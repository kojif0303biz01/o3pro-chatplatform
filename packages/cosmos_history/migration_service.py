"""
データ移行サービス

ローカルJSON履歴からCosmos DBへの安全な移行を管理
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from chat_history.local_history import ChatHistoryManager
from .cosmos_history_manager import CosmosHistoryManager
from .models.conversation import ChatConversation
from .models.message import ChatMessage

logger = logging.getLogger(__name__)


class MigrationStats:
    """移行統計"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_sessions = 0
        self.migrated_conversations = 0
        self.failed_conversations = 0
        self.total_messages = 0
        self.migrated_messages = 0
        self.failed_messages = 0
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
    
    def add_error(self, session_id: str, error: str):
        """エラー追加"""
        self.errors.append({
            "session_id": session_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        logger.error(f"Migration error for {session_id}: {error}")
    
    def add_warning(self, session_id: str, warning: str):
        """警告追加"""
        self.warnings.append({
            "session_id": session_id,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })
        logger.warning(f"Migration warning for {session_id}: {warning}")
    
    def get_summary(self) -> Dict[str, Any]:
        """統計サマリー取得"""
        duration = datetime.now() - self.start_time
        
        return {
            "migration_started_at": self.start_time.isoformat(),
            "migration_duration_seconds": duration.total_seconds(),
            "total_sessions": self.total_sessions,
            "migrated_conversations": self.migrated_conversations,
            "failed_conversations": self.failed_conversations,
            "conversation_success_rate": self.migrated_conversations / max(self.total_sessions, 1),
            "total_messages": self.total_messages,
            "migrated_messages": self.migrated_messages,
            "failed_messages": self.failed_messages,
            "message_success_rate": self.migrated_messages / max(self.total_messages, 1),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors[-5:] if self.errors else [],  # 最新5件のエラー
            "warnings": self.warnings[-5:] if self.warnings else []  # 最新5件の警告
        }


class DataMigrationService:
    """データ移行サービス"""
    
    def __init__(
        self,
        local_manager: ChatHistoryManager,
        cosmos_manager: CosmosHistoryManager,
        default_user_id: str = "migrated_user"
    ):
        self.local_manager = local_manager
        self.cosmos_manager = cosmos_manager
        self.default_user_id = default_user_id
        self.stats = MigrationStats()
    
    async def migrate_all_data(self, dry_run: bool = False) -> Dict[str, Any]:
        """全データ移行"""
        logger.info(f"Starting data migration (dry_run={dry_run})")
        
        try:
            # ローカルセッション一覧取得
            local_sessions = self.local_manager.list_sessions(limit=None)
            self.stats.total_sessions = len(local_sessions)
            
            logger.info(f"Found {self.stats.total_sessions} sessions to migrate")
            
            if self.stats.total_sessions == 0:
                logger.warning("No sessions found to migrate")
                return self.stats.get_summary()
            
            # セッションごとに移行
            for i, session_info in enumerate(local_sessions, 1):
                session_id = session_info.get("id", f"unknown_{i}")
                
                try:
                    logger.info(f"Migrating session {i}/{self.stats.total_sessions}: {session_id}")
                    await self._migrate_session(session_info, dry_run)
                    self.stats.migrated_conversations += 1
                    
                except Exception as e:
                    self.stats.add_error(session_id, str(e))
                    self.stats.failed_conversations += 1
            
            summary = self.stats.get_summary()
            logger.info(f"Migration completed: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.stats.add_error("global", str(e))
            return self.stats.get_summary()
    
    async def _migrate_session(self, session_info: Dict[str, Any], dry_run: bool):
        """個別セッション移行"""
        session_id = session_info["id"]
        
        # ローカルメッセージ取得
        local_messages = self.local_manager.get_session_messages(session_id)
        self.stats.total_messages += len(local_messages)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate session {session_id} with {len(local_messages)} messages")
            self.stats.migrated_messages += len(local_messages)
            return
        
        # 重複チェック
        existing_conversation = await self.cosmos_manager.get_conversation(session_id)
        if existing_conversation:
            self.stats.add_warning(session_id, "Session already exists in Cosmos DB, skipping")
            return
        
        # 会話変換・作成
        cosmos_conversation = self._convert_session_to_conversation(session_info, local_messages)
        
        try:
            # Cosmos DBに会話作成
            created_conversation = await self.cosmos_manager.create_conversation(
                title=cosmos_conversation.title,
                creator_user_id=self.default_user_id,
                creator_display_name="移行ユーザー"
            )
            
            # 作成された会話のIDを使用
            conversation_id = created_conversation.conversation_id
            
            logger.info(f"Created conversation: {conversation_id}")
            
            # メッセージ移行
            migrated_count = 0
            for i, local_message in enumerate(local_messages):
                try:
                    cosmos_message = self._convert_message_format(
                        local_message, 
                        conversation_id
                    )
                    
                    await self.cosmos_manager.add_message(
                        conversation_id,
                        cosmos_message.sender.user_id,
                        cosmos_message.sender.display_name,
                        cosmos_message.content.text,
                        cosmos_message.sender.role,
                        cosmos_message.metadata.to_dict() if cosmos_message.metadata else {}
                    )
                    
                    migrated_count += 1
                    self.stats.migrated_messages += 1
                    
                except Exception as e:
                    self.stats.add_error(
                        session_id, 
                        f"Message {i+1} migration failed: {str(e)}"
                    )
                    self.stats.failed_messages += 1
            
            # 会話メタデータ更新
            await self._update_conversation_metadata(
                created_conversation, 
                local_messages,
                migrated_count
            )
            
            logger.info(f"Migrated session {session_id}: {migrated_count}/{len(local_messages)} messages")
            
        except Exception as e:
            # 会話作成エラーの場合は全体を失敗とする
            self.stats.failed_messages += len(local_messages)
            raise Exception(f"Conversation creation failed: {str(e)}")
    
    def _convert_session_to_conversation(
        self, 
        local_session: Dict[str, Any], 
        messages: List[Dict[str, Any]]
    ) -> ChatConversation:
        """ローカルセッション → Cosmos DB会話変換"""
        
        # 基本情報
        title = local_session.get("title", f"移行会話 - {local_session.get('id', 'unknown')}")
        mode = local_session.get("mode", "reasoning")
        
        # カテゴリー推定
        category_id = f"migrated_{mode}"
        category_name = f"移行済み ({mode})"
        
        # 参加者分析
        participants = self._analyze_participants(messages)
        
        # 統計計算
        metrics = self._calculate_message_metrics(messages)
        
        # タイムライン情報
        created_at = local_session.get("created_at", datetime.now().isoformat())
        updated_at = local_session.get("updated_at", datetime.now().isoformat())
        
        # 会話オブジェクト作成（仮）
        conversation = ChatConversation.create_new(
            tenant_id=self.cosmos_manager.tenant_id,
            title=title,
            creator_user_id=self.default_user_id,
            creator_display_name="移行ユーザー",
            initial_category=category_id
        )
        
        # メタデータ設定
        conversation.timeline.created_at = created_at
        conversation.timeline.updated_at = updated_at
        
        if messages:
            conversation.timeline.first_message_preview = messages[0].get("content", "")[:100]
            conversation.timeline.last_message_preview = messages[-1].get("content", "")[:100]
            conversation.timeline.last_message_at = messages[-1].get("timestamp", updated_at)
        
        # カテゴリー追加
        conversation.add_category(category_id, category_name, 1.0, "migration")
        
        # タグ追加
        conversation.add_tag("移行済み")
        conversation.add_tag(mode)
        
        # 統計更新
        conversation.metrics.message_count = len(messages)
        conversation.metrics.total_tokens = metrics["total_tokens"]
        conversation.metrics.total_duration = metrics["total_duration"]
        conversation.metrics.avg_response_time = metrics["avg_response_time"]
        
        return conversation
    
    def _analyze_participants(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """メッセージから参加者分析"""
        participants = {}
        
        for msg in messages:
            role = msg.get("role", "user")
            
            if role == "user":
                user_id = self.default_user_id
                display_name = "ユーザー"
            elif role == "assistant":
                user_id = "assistant"
                display_name = "アシスタント"
            else:
                user_id = f"{role}_user"
                display_name = role.capitalize()
            
            if user_id not in participants:
                participants[user_id] = {
                    "user_id": user_id,
                    "display_name": display_name,
                    "role": role
                }
        
        return list(participants.values())
    
    def _calculate_message_metrics(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """メッセージメトリクス計算"""
        total_duration = 0.0
        total_tokens = 0
        response_times = []
        
        for msg in messages:
            metadata = msg.get("metadata", {})
            
            # 継続時間
            duration = metadata.get("duration", 0.0)
            if isinstance(duration, (int, float)):
                total_duration += duration
                
                # アシスタントの応答時間
                if msg.get("role") == "assistant" and duration > 0:
                    response_times.append(duration)
            
            # トークン数
            tokens = metadata.get("tokens", 0)
            if isinstance(tokens, int):
                total_tokens += tokens
        
        avg_response_time = (
            sum(response_times) / len(response_times) 
            if response_times else 0.0
        )
        
        return {
            "total_duration": total_duration,
            "total_tokens": total_tokens,
            "avg_response_time": avg_response_time
        }
    
    def _convert_message_format(
        self, 
        local_message: Dict[str, Any], 
        conversation_id: str
    ) -> ChatMessage:
        """ローカルメッセージ → Cosmos DBメッセージ変換"""
        
        # 基本情報
        role = local_message.get("role", "user")
        content = local_message.get("content", "")
        timestamp = local_message.get("timestamp", datetime.now().isoformat())
        
        # 送信者情報
        if role == "user":
            sender_user_id = self.default_user_id
            sender_display_name = "ユーザー"
        elif role == "assistant":
            sender_user_id = "assistant"
            sender_display_name = "アシスタント"
        else:
            sender_user_id = f"{role}_user"
            sender_display_name = role.capitalize()
        
        # メタデータ変換
        local_metadata = local_message.get("metadata", {})
        cosmos_metadata = {
            "mode": local_metadata.get("mode", ""),
            "effort": local_metadata.get("effort", ""),
            "duration": local_metadata.get("duration", 0.0),
            "tokens": local_metadata.get("tokens", 0),
            "model": local_metadata.get("model", ""),
            "source": "migration"
        }
        
        # メッセージ作成
        message = ChatMessage.create_new(
            conversation_id=conversation_id,
            tenant_id=self.cosmos_manager.tenant_id,
            sender_user_id=sender_user_id,
            sender_display_name=sender_display_name,
            content_text=content,
            sender_role=role,
            metadata=cosmos_metadata
        )
        
        # タイムスタンプ上書き
        message.timestamp = timestamp
        
        return message
    
    async def _update_conversation_metadata(
        self,
        conversation: ChatConversation,
        local_messages: List[Dict[str, Any]],
        migrated_count: int
    ):
        """会話メタデータ更新"""
        
        try:
            # 移行情報追加
            conversation.add_tag(f"移行完了_{migrated_count}件")
            
            if migrated_count < len(local_messages):
                conversation.add_tag(f"一部移行失敗_{len(local_messages) - migrated_count}件")
            
            # 会話更新
            await self.cosmos_manager.update_conversation(conversation)
            
        except Exception as e:
            logger.warning(f"Failed to update conversation metadata: {e}")
    
    async def verify_migration(self) -> Dict[str, Any]:
        """移行検証"""
        logger.info("Starting migration verification")
        
        verification_results = {
            "local_sessions": 0,
            "cosmos_conversations": 0,
            "session_match": True,
            "local_messages": 0,
            "cosmos_messages": 0,
            "message_match": True,
            "mismatched_sessions": [],
            "sample_verification": {},
            "verification_time": datetime.now().isoformat()
        }
        
        try:
            # セッション数比較
            local_sessions = self.local_manager.list_sessions(limit=None)
            verification_results["local_sessions"] = len(local_sessions)
            
            cosmos_conversations = await self.cosmos_manager.list_conversations(
                limit=len(local_sessions) + 10
            )
            verification_results["cosmos_conversations"] = len(cosmos_conversations)
            
            # サンプル検証（最初の3セッション）
            sample_sessions = local_sessions[:3]
            
            for local_session in sample_sessions:
                session_id = local_session["id"]
                
                # ローカルメッセージ数
                local_messages = self.local_manager.get_session_messages(session_id)
                local_count = len(local_messages)
                verification_results["local_messages"] += local_count
                
                # Cosmos DBメッセージ数
                cosmos_conversation = await self.cosmos_manager.get_conversation(session_id)
                if cosmos_conversation:
                    cosmos_messages = await self.cosmos_manager.get_conversation_messages(
                        cosmos_conversation.conversation_id
                    )
                    cosmos_count = len(cosmos_messages)
                else:
                    cosmos_count = 0
                
                verification_results["cosmos_messages"] += cosmos_count
                
                # サンプル詳細記録
                verification_results["sample_verification"][session_id] = {
                    "local_message_count": local_count,
                    "cosmos_message_count": cosmos_count,
                    "match": local_count == cosmos_count,
                    "conversation_exists": cosmos_conversation is not None
                }
                
                if local_count != cosmos_count:
                    verification_results["mismatched_sessions"].append({
                        "session_id": session_id,
                        "local_count": local_count,
                        "cosmos_count": cosmos_count
                    })
            
            verification_results["session_match"] = (
                verification_results["local_sessions"] == verification_results["cosmos_conversations"]
            )
            verification_results["message_match"] = (
                verification_results["local_messages"] == verification_results["cosmos_messages"]
            )
            
            logger.info(f"Verification completed: {verification_results}")
            return verification_results
            
        except Exception as e:
            verification_results["error"] = str(e)
            logger.error(f"Verification failed: {e}")
            return verification_results
    
    async def rollback_migration(self, confirmation_code: str) -> Dict[str, Any]:
        """移行ロールバック（Cosmos DBデータ削除）"""
        
        if confirmation_code != "CONFIRM_ROLLBACK_DELETE_ALL":
            raise ValueError("Invalid confirmation code")
        
        logger.warning("Starting migration rollback - this will delete all migrated data")
        
        rollback_stats = {
            "deleted_conversations": 0,
            "deleted_messages": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # 全会話取得
            cosmos_conversations = await self.cosmos_manager.list_conversations(limit=1000)
            
            for conversation in cosmos_conversations:
                try:
                    # 会話内の全メッセージ削除
                    messages = await self.cosmos_manager.get_conversation_messages(
                        conversation.conversation_id,
                        limit=1000
                    )
                    
                    for message in messages:
                        await self.cosmos_manager.delete_message(
                            message.id, 
                            message.conversation_id
                        )
                        rollback_stats["deleted_messages"] += 1
                    
                    # 会話削除
                    await self.cosmos_manager.delete_conversation(conversation.conversation_id)
                    rollback_stats["deleted_conversations"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to delete conversation {conversation.conversation_id}: {str(e)}"
                    logger.error(error_msg)
                    rollback_stats["errors"].append(error_msg)
            
            rollback_stats["end_time"] = datetime.now().isoformat()
            logger.info(f"Rollback completed: {rollback_stats}")
            
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            rollback_stats["errors"].append(error_msg)
            rollback_stats["end_time"] = datetime.now().isoformat()
            raise
        
        return rollback_stats


# ==================== ファクトリー関数 ====================

def create_migration_service(
    local_history_dir: str,
    cosmos_manager: CosmosHistoryManager,
    default_user_id: str = "migrated_user"
) -> DataMigrationService:
    """移行サービス作成"""
    
    local_manager = ChatHistoryManager(local_history_dir)
    return DataMigrationService(local_manager, cosmos_manager, default_user_id)


# ==================== テスト関数 ====================

async def test_migration_service():
    """移行サービステスト"""
    
    print("=== 移行サービステスト ===")
    
    try:
        from .cosmos_history_manager import create_cosmos_history_manager
        
        # マネージャー作成
        cosmos_manager = create_cosmos_history_manager("test_tenant")
        migration_service = create_migration_service(
            "chat_history",  # ローカル履歴ディレクトリ
            cosmos_manager,
            "test_migration_user"
        )
        print("✅ 移行サービス初期化成功")
        
        # ドライラン実行
        print("🔍 Running migration dry-run...")
        dry_run_result = await migration_service.migrate_all_data(dry_run=True)
        print(f"✅ Dry-run completed: {dry_run_result}")
        
        # 検証テスト
        print("🔍 Running verification...")
        verification_result = await migration_service.verify_migration()
        print(f"✅ Verification completed: {verification_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_migration_service())