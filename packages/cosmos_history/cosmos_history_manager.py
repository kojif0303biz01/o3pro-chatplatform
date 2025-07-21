"""
Cosmos DB チャット履歴管理メインクラス

会話とメッセージの統合管理を提供
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError

from .cosmos_client import CosmosDBClient
from .models.conversation import ChatConversation
from .models.message import ChatMessage
from core.azure_universal_auth import AzureAuthManager

logger = logging.getLogger(__name__)


class CosmosHistoryManager:
    """Cosmos DB チャット履歴管理メインクラス"""
    
    def __init__(self, cosmos_client: CosmosDBClient, tenant_id: str, config: 'AppConfig' = None):
        """
        初期化
        
        Args:
            cosmos_client: Cosmos DBクライアント
            tenant_id: テナントID（マルチテナント対応）
            config: アプリケーション設定
        """
        self.cosmos_client = cosmos_client
        self.tenant_id = tenant_id
        self.config = config or self._load_default_config()
        
        if not cosmos_client.is_ready():
            raise ValueError("Cosmos DB client is not ready")
        
        self.conversations_container = cosmos_client.get_conversations_container()
        self.messages_container = cosmos_client.get_messages_container()
        
        logger.info(f"CosmosHistoryManager initialized for tenant: {tenant_id}")
    
    def _load_default_config(self):
        """デフォルト設定読み込み"""
        from .config import load_config_from_env
        return load_config_from_env()
    
    # ==================== 会話管理 ====================
    
    async def create_conversation(
        self,
        title: str,
        creator_user_id: str,
        creator_display_name: str = "",
        initial_category: Optional[str] = None
    ) -> ChatConversation:
        """新規会話作成"""
        
        try:
            # 会話オブジェクト作成
            conversation = ChatConversation.create_new(
                tenant_id=self.tenant_id,
                title=title,
                creator_user_id=creator_user_id,
                creator_display_name=creator_display_name,
                initial_category=initial_category
            )
            
            # Cosmos DBに保存
            cosmos_dict = conversation.to_cosmos_dict()
            
            # TTL設定（環境変数ベース）
            development_mode = self.config.development.development_mode
            ttl_value = self.config.chat_history.get_conversation_ttl(development_mode)
            cosmos_dict['ttl'] = ttl_value
            
            created_item = self.conversations_container.create_item(cosmos_dict)
            
            logger.info(f"Conversation created: {conversation.conversation_id}")
            return ChatConversation.from_cosmos_dict(created_item)
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to create conversation: {e}")
            raise Exception(f"会話作成エラー: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """会話取得"""
        
        try:
            # Cosmos DBから取得
            item_id = f"conv_{conversation_id}"
            item = self.conversations_container.read_item(
                item=item_id,
                partition_key=self.tenant_id
            )
            
            return ChatConversation.from_cosmos_dict(item)
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise
    
    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        include_archived: bool = False
    ) -> List[ChatConversation]:
        """会話一覧取得"""
        
        try:
            # クエリ構築
            query = "SELECT * FROM c WHERE c.tenantId = @tenantId"
            parameters = [{"name": "@tenantId", "value": self.tenant_id}]
            
            # ユーザーフィルター
            if user_id:
                query += " AND ARRAY_CONTAINS(c.participants, {'userId': @userId}, true)"
                parameters.append({"name": "@userId", "value": user_id})
            
            # アーカイブフィルター
            if not include_archived:
                query += " AND (c.archived = false OR NOT IS_DEFINED(c.archived))"
            
            # ソート・ページング
            query += " ORDER BY c.timeline.lastMessageAt DESC"
            
            # クエリ実行
            items = list(self.conversations_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=limit
            ))
            
            # オフセット適用（簡易実装）
            if offset > 0:
                items = items[offset:]
            
            return [ChatConversation.from_cosmos_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            raise
    
    async def update_conversation(self, conversation: ChatConversation) -> ChatConversation:
        """会話更新"""
        
        try:
            # 検索用テキスト更新
            conversation.update_searchable_text()
            
            # Cosmos DBで更新
            cosmos_dict = conversation.to_cosmos_dict()
            updated_item = self.conversations_container.replace_item(
                item=conversation.id,
                body=cosmos_dict
            )
            
            logger.info(f"Conversation updated: {conversation.conversation_id}")
            return ChatConversation.from_cosmos_dict(updated_item)
            
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation.conversation_id}: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """会話削除（論理削除）"""
        
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            # 論理削除
            conversation.status = "deleted"
            conversation.archived = True
            
            await self.update_conversation(conversation)
            
            logger.info(f"Conversation deleted: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise
    
    # ==================== メッセージ管理 ====================
    
    async def add_message(
        self,
        conversation_id: str,
        sender_user_id: str,
        sender_display_name: str,
        content: str,
        sender_role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """メッセージ追加"""
        
        try:
            # 会話存在確認
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"会話が見つかりません: {conversation_id}")
            
            # シーケンス番号取得
            sequence_number = await self._get_next_sequence_number(conversation_id)
            
            # メッセージ作成
            message = ChatMessage.create_new(
                conversation_id=conversation_id,
                tenant_id=self.tenant_id,
                sender_user_id=sender_user_id,
                sender_display_name=sender_display_name,
                content_text=content,
                sender_role=sender_role,
                sequence_number=sequence_number,
                metadata=metadata or {}
            )
            
            # Cosmos DBに保存
            cosmos_dict = message.to_cosmos_dict()
            
            # TTL設定（環境変数ベース）
            development_mode = self.config.development.development_mode
            ttl_value = self.config.chat_history.get_message_ttl(development_mode)
            cosmos_dict['ttl'] = ttl_value
            
            created_item = self.messages_container.create_item(cosmos_dict)
            
            # 会話情報更新
            await self._update_conversation_from_message(conversation, message, is_first_message=(sequence_number == 1))
            
            logger.info(f"Message added: {message.id}")
            return ChatMessage.from_cosmos_dict(created_item)
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
        ascending: bool = True
    ) -> List[ChatMessage]:
        """会話内メッセージ一覧取得"""
        
        try:
            # ソート順
            order = "ASC" if ascending else "DESC"
            
            query = f"""
                SELECT * FROM m 
                WHERE m.conversationId = @conversationId 
                ORDER BY m.sequenceNumber {order}
            """
            
            parameters = [{"name": "@conversationId", "value": conversation_id}]
            
            # クエリ実行
            items = list(self.messages_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=conversation_id,
                max_item_count=limit
            ))
            
            # オフセット適用
            if offset > 0:
                items = items[offset:]
            
            return [ChatMessage.from_cosmos_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_message(self, message_id: str, conversation_id: str) -> Optional[ChatMessage]:
        """個別メッセージ取得"""
        
        try:
            item = self.messages_container.read_item(
                item=message_id,
                partition_key=conversation_id
            )
            
            return ChatMessage.from_cosmos_dict(item)
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Message not found: {message_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            raise
    
    async def update_message(self, message: ChatMessage) -> ChatMessage:
        """メッセージ更新"""
        
        try:
            # 検索テキスト更新
            message.update_search_text()
            
            # Cosmos DBで更新
            cosmos_dict = message.to_cosmos_dict()
            updated_item = self.messages_container.replace_item(
                item=message.id,
                body=cosmos_dict
            )
            
            logger.info(f"Message updated: {message.id}")
            return ChatMessage.from_cosmos_dict(updated_item)
            
        except Exception as e:
            logger.error(f"Failed to update message {message.id}: {e}")
            raise
    
    async def delete_message(self, message_id: str, conversation_id: str) -> bool:
        """メッセージ削除（物理削除）"""
        
        try:
            self.messages_container.delete_item(
                item=message_id,
                partition_key=conversation_id
            )
            
            logger.info(f"Message deleted: {message_id}")
            return True
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Message not found for deletion: {message_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    # ==================== ヘルパーメソッド ====================
    
    async def _get_next_sequence_number(self, conversation_id: str) -> int:
        """次のシーケンス番号取得"""
        
        try:
            query = """
                SELECT VALUE MAX(m.sequenceNumber) 
                FROM m WHERE m.conversationId = @conversationId
            """
            
            parameters = [{"name": "@conversationId", "value": conversation_id}]
            
            items = list(self.messages_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=conversation_id
            ))
            
            max_sequence = items[0] if items and items[0] is not None else 0
            return max_sequence + 1
            
        except Exception as e:
            logger.warning(f"Failed to get sequence number, using default: {e}")
            return 1
    
    async def _update_conversation_from_message(
        self,
        conversation: ChatConversation,
        message: ChatMessage,
        is_first_message: bool = False
    ):
        """メッセージから会話情報を更新"""
        
        try:
            # メッセージカウント更新
            conversation.metrics.message_count += 1
            
            # タイムライン更新
            conversation.update_from_message(message.content.text, is_first_message)
            
            # 参加者追加（新規の場合）
            if not conversation.is_participant(message.sender.user_id):
                conversation.add_participant(
                    message.sender.user_id,
                    message.sender.display_name,
                    message.sender.role
                )
            
            # 会話更新
            await self.update_conversation(conversation)
            
        except Exception as e:
            logger.warning(f"Failed to update conversation from message: {e}")
            # メッセージ追加は成功させる
    
    # ==================== 統計・分析 ====================
    
    async def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """会話統計取得"""
        
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return {"error": "会話が見つかりません"}
            
            # メッセージ統計
            messages = await self.get_conversation_messages(conversation_id, limit=1000)
            
            stats = {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "message_count": len(messages),
                "participant_count": len(conversation.participants),
                "created_at": conversation.timeline.created_at,
                "last_message_at": conversation.timeline.last_message_at,
                "categories": [c.category_name for c in conversation.categories],
                "tags": conversation.tags
            }
            
            # メッセージ分析
            if messages:
                user_messages = [m for m in messages if m.sender.role == "user"]
                assistant_messages = [m for m in messages if m.sender.role == "assistant"]
                
                stats.update({
                    "user_message_count": len(user_messages),
                    "assistant_message_count": len(assistant_messages),
                    "avg_message_length": sum(len(m.content.text) for m in messages) / len(messages),
                    "total_tokens": sum(m.metadata.tokens for m in messages if m.metadata.tokens > 0),
                    "avg_response_time": sum(m.metadata.duration for m in assistant_messages if m.metadata.duration > 0) / max(len(assistant_messages), 1)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {"error": str(e)}
    
    async def get_tenant_stats(self) -> Dict[str, Any]:
        """テナント統計取得"""
        
        try:
            # 会話統計
            conversations = await self.list_conversations(limit=1000)
            
            stats = {
                "tenant_id": self.tenant_id,
                "total_conversations": len(conversations),
                "active_conversations": len([c for c in conversations if c.status == "active"]),
                "archived_conversations": len([c for c in conversations if c.archived]),
            }
            
            if conversations:
                # カテゴリー統計
                all_categories = []
                for conv in conversations:
                    all_categories.extend([c.category_name for c in conv.categories])
                
                category_counts = {}
                for cat in all_categories:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                stats["top_categories"] = sorted(
                    category_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                # 時系列統計
                recent_conversations = [
                    c for c in conversations
                    if c.timeline.last_message_at and 
                    (datetime.now() - datetime.fromisoformat(c.timeline.last_message_at.replace('Z', '+00:00'))).days <= 30
                ]
                
                stats["recent_activity"] = {
                    "last_30_days": len(recent_conversations),
                    "most_active_participants": self._get_most_active_participants(conversations)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            return {"error": str(e)}
    
    def _get_most_active_participants(self, conversations: List[ChatConversation]) -> List[Dict[str, Any]]:
        """最もアクティブな参加者取得"""
        
        participant_counts = {}
        
        for conv in conversations:
            for participant in conv.participants:
                user_id = participant.user_id
                if user_id not in participant_counts:
                    participant_counts[user_id] = {
                        "user_id": user_id,
                        "display_name": participant.display_name,
                        "conversation_count": 0
                    }
                participant_counts[user_id]["conversation_count"] += 1
        
        return sorted(
            participant_counts.values(),
            key=lambda x: x["conversation_count"],
            reverse=True
        )[:10]


# ==================== ファクトリー関数 ====================

def create_cosmos_history_manager(
    tenant_id: str,
    auth_manager: Optional[AzureAuthManager] = None
) -> CosmosHistoryManager:
    """Cosmos DB履歴管理マネージャー作成"""
    
    from .cosmos_client import CosmosDBClient
    
    cosmos_client = CosmosDBClient(auth_manager)
    return CosmosHistoryManager(cosmos_client, tenant_id)


# ==================== テスト関数 ====================

async def test_cosmos_history_manager():
    """Cosmos DB履歴管理テスト"""
    
    print("=== Cosmos DB履歴管理テスト ===")
    
    try:
        # マネージャー作成
        manager = create_cosmos_history_manager("test_tenant")
        print("✅ マネージャー作成成功")
        
        # 会話作成
        conversation = await manager.create_conversation(
            title="テスト会話",
            creator_user_id="test_user",
            creator_display_name="テストユーザー"
        )
        print(f"✅ 会話作成: {conversation.conversation_id}")
        
        # メッセージ追加
        message1 = await manager.add_message(
            conversation.conversation_id,
            "test_user",
            "テストユーザー",
            "こんにちは！"
        )
        print(f"✅ メッセージ追加: {message1.id}")
        
        message2 = await manager.add_message(
            conversation.conversation_id,
            "assistant",
            "アシスタント",
            "こんにちは！何かお手伝いできることはありますか？",
            sender_role="assistant",
            metadata={"duration": 2.5, "tokens": 15}
        )
        print(f"✅ アシスタントメッセージ追加: {message2.id}")
        
        # メッセージ一覧取得
        messages = await manager.get_conversation_messages(conversation.conversation_id)
        print(f"✅ メッセージ一覧取得: {len(messages)}件")
        
        # 統計取得
        stats = await manager.get_conversation_stats(conversation.conversation_id)
        print(f"✅ 統計取得: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cosmos_history_manager())