"""
Cosmos DB履歴管理テスト

CosmosHistoryManager の基本動作テスト（モック使用）
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from cosmos_history.cosmos_history_manager import CosmosHistoryManager, create_cosmos_history_manager
from cosmos_history.models.conversation import ChatConversation
from cosmos_history.models.message import ChatMessage


class TestCosmosHistoryManager:
    """CosmosHistoryManager テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        # モッククライアント作成
        self.mock_cosmos_client = Mock()
        self.mock_cosmos_client.is_ready.return_value = True
        
        self.mock_conversations_container = Mock()
        self.mock_messages_container = Mock()
        
        self.mock_cosmos_client.get_conversations_container.return_value = self.mock_conversations_container
        self.mock_cosmos_client.get_messages_container.return_value = self.mock_messages_container
        
        # マネージャー作成
        self.manager = CosmosHistoryManager(self.mock_cosmos_client, "test_tenant")
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.manager.cosmos_client is self.mock_cosmos_client
        assert self.manager.tenant_id == "test_tenant"
        assert self.manager.conversations_container is self.mock_conversations_container
        assert self.manager.messages_container is self.mock_messages_container
    
    def test_initialization_not_ready(self):
        """準備未完了クライアントでの初期化テスト"""
        mock_client = Mock()
        mock_client.is_ready.return_value = False
        
        with pytest.raises(ValueError, match="Cosmos DB client is not ready"):
            CosmosHistoryManager(mock_client, "test_tenant")
    
    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """会話作成テスト"""
        # モック設定
        created_item = {
            "id": "conv_123",
            "conversationId": "conv_123",
            "tenantId": "test_tenant",
            "title": "テスト会話",
            "participants": [{"userId": "user1", "displayName": "テストユーザー"}]
        }
        self.mock_conversations_container.create_item.return_value = created_item
        
        # 会話作成
        conversation = await self.manager.create_conversation(
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="テストユーザー"
        )
        
        # 検証
        assert isinstance(conversation, ChatConversation)
        self.mock_conversations_container.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_found(self):
        """会話取得テスト（存在する場合）"""
        # モック設定
        conversation_data = {
            "id": "conv_test123",
            "conversationId": "test123",
            "tenantId": "test_tenant",
            "title": "テスト会話"
        }
        self.mock_conversations_container.read_item.return_value = conversation_data
        
        # 会話取得
        conversation = await self.manager.get_conversation("test123")
        
        # 検証
        assert conversation is not None
        assert isinstance(conversation, ChatConversation)
        self.mock_conversations_container.read_item.assert_called_once_with(
            item="conv_test123",
            partition_key="test_tenant"
        )
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self):
        """会話取得テスト（存在しない場合）"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_conversations_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # 会話取得
        conversation = await self.manager.get_conversation("nonexistent")
        
        # 検証
        assert conversation is None
    
    @pytest.mark.asyncio
    async def test_list_conversations(self):
        """会話一覧取得テスト"""
        # モック設定
        mock_conversations = [
            {"id": "conv_1", "title": "会話1", "tenantId": "test_tenant"},
            {"id": "conv_2", "title": "会話2", "tenantId": "test_tenant"}
        ]
        self.mock_conversations_container.query_items.return_value = mock_conversations
        
        # 会話一覧取得
        conversations = await self.manager.list_conversations(limit=10)
        
        # 検証
        assert len(conversations) == 2
        assert all(isinstance(conv, ChatConversation) for conv in conversations)
        self.mock_conversations_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_user_filter(self):
        """ユーザーフィルター付き会話一覧取得テスト"""
        # モック設定
        self.mock_conversations_container.query_items.return_value = []
        
        # ユーザーフィルター付きで会話一覧取得
        await self.manager.list_conversations(user_id="user1", limit=10)
        
        # クエリにユーザーフィルターが含まれることを確認
        call_args = self.mock_conversations_container.query_items.call_args
        query = call_args[1]["query"]
        parameters = call_args[1]["parameters"]
        
        assert "ARRAY_CONTAINS" in query
        assert any(param["name"] == "@userId" and param["value"] == "user1" for param in parameters)
    
    @pytest.mark.asyncio
    async def test_update_conversation(self):
        """会話更新テスト"""
        # テスト用会話作成
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="テストユーザー"
        )
        conversation.summary = "更新されたサマリー"
        
        # モック設定
        updated_item = conversation.to_cosmos_dict()
        self.mock_conversations_container.replace_item.return_value = updated_item
        
        # 会話更新
        updated_conversation = await self.manager.update_conversation(conversation)
        
        # 検証
        assert isinstance(updated_conversation, ChatConversation)
        self.mock_conversations_container.replace_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """会話削除テスト"""
        # テスト用会話データ
        conversation_data = {
            "id": "conv_test123",
            "conversationId": "test123",
            "tenantId": "test_tenant",
            "title": "削除対象会話",
            "status": "active",
            "archived": False
        }
        
        # モック設定
        self.mock_conversations_container.read_item.return_value = conversation_data
        updated_item = conversation_data.copy()
        updated_item.update({"status": "deleted", "archived": True})
        self.mock_conversations_container.replace_item.return_value = updated_item
        
        # 会話削除
        result = await self.manager.delete_conversation("test123")
        
        # 検証
        assert result is True
        self.mock_conversations_container.read_item.assert_called_once()
        self.mock_conversations_container.replace_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self):
        """存在しない会話の削除テスト"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_conversations_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # 会話削除
        result = await self.manager.delete_conversation("nonexistent")
        
        # 検証
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_message(self):
        """メッセージ追加テスト"""
        # テスト用会話データ
        conversation_data = {
            "id": "conv_test123",
            "conversationId": "test123",
            "tenantId": "test_tenant",
            "title": "テスト会話"
        }
        
        # モック設定
        self.mock_conversations_container.read_item.return_value = conversation_data
        
        # シーケンス番号クエリのモック
        self.mock_messages_container.query_items.return_value = [0]  # MAX結果
        
        # メッセージ作成のモック
        created_message = {
            "id": "msg_123",
            "conversationId": "test123",
            "tenantId": "test_tenant",
            "content": {"text": "テストメッセージ"},
            "sender": {"userId": "user1", "displayName": "テストユーザー"}
        }
        self.mock_messages_container.create_item.return_value = created_message
        
        # 会話更新のモック
        self.mock_conversations_container.replace_item.return_value = conversation_data
        
        # メッセージ追加
        message = await self.manager.add_message(
            conversation_id="test123",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content="テストメッセージ"
        )
        
        # 検証
        assert isinstance(message, ChatMessage)
        self.mock_conversations_container.read_item.assert_called_once()
        self.mock_messages_container.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_message_conversation_not_found(self):
        """存在しない会話へのメッセージ追加テスト"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_conversations_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # メッセージ追加（エラーが発生することを確認）
        with pytest.raises(ValueError, match="会話が見つかりません"):
            await self.manager.add_message(
                conversation_id="nonexistent",
                sender_user_id="user1",
                sender_display_name="テストユーザー",
                content="テストメッセージ"
            )
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages(self):
        """会話内メッセージ一覧取得テスト"""
        # モック設定
        mock_messages = [
            {"id": "msg_1", "conversationId": "test123", "content": {"text": "メッセージ1"}},
            {"id": "msg_2", "conversationId": "test123", "content": {"text": "メッセージ2"}}
        ]
        self.mock_messages_container.query_items.return_value = mock_messages
        
        # メッセージ一覧取得
        messages = await self.manager.get_conversation_messages("test123")
        
        # 検証
        assert len(messages) == 2
        assert all(isinstance(msg, ChatMessage) for msg in messages)
        self.mock_messages_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_message_found(self):
        """個別メッセージ取得テスト（存在する場合）"""
        # モック設定
        message_data = {
            "id": "msg_123",
            "conversationId": "test123",
            "content": {"text": "テストメッセージ"}
        }
        self.mock_messages_container.read_item.return_value = message_data
        
        # メッセージ取得
        message = await self.manager.get_message("msg_123", "test123")
        
        # 検証
        assert message is not None
        assert isinstance(message, ChatMessage)
        self.mock_messages_container.read_item.assert_called_once_with(
            item="msg_123",
            partition_key="test123"
        )
    
    @pytest.mark.asyncio
    async def test_get_message_not_found(self):
        """個別メッセージ取得テスト（存在しない場合）"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_messages_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # メッセージ取得
        message = await self.manager.get_message("nonexistent", "test123")
        
        # 検証
        assert message is None
    
    @pytest.mark.asyncio
    async def test_update_message(self):
        """メッセージ更新テスト"""
        # テスト用メッセージ作成
        message = ChatMessage.create_new(
            conversation_id="test123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="更新されたメッセージ"
        )
        
        # モック設定
        updated_item = message.to_cosmos_dict()
        self.mock_messages_container.replace_item.return_value = updated_item
        
        # メッセージ更新
        updated_message = await self.manager.update_message(message)
        
        # 検証
        assert isinstance(updated_message, ChatMessage)
        self.mock_messages_container.replace_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_message(self):
        """メッセージ削除テスト"""
        # メッセージ削除
        result = await self.manager.delete_message("msg_123", "test123")
        
        # 検証
        assert result is True
        self.mock_messages_container.delete_item.assert_called_once_with(
            item="msg_123",
            partition_key="test123"
        )
    
    @pytest.mark.asyncio
    async def test_delete_message_not_found(self):
        """存在しないメッセージの削除テスト"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_messages_container.delete_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # メッセージ削除
        result = await self.manager.delete_message("nonexistent", "test123")
        
        # 検証
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_conversation_stats(self):
        """会話統計取得テスト"""
        # テスト用会話データ
        conversation_data = {
            "id": "conv_test123",
            "conversationId": "test123",
            "tenantId": "test_tenant",
            "title": "統計テスト会話",
            "participants": [{"userId": "user1", "displayName": "テストユーザー"}],
            "categories": [{"categoryName": "テスト"}],
            "tags": ["tag1", "tag2"],
            "timeline": {"createdAt": "2023-01-01T00:00:00Z", "lastMessageAt": "2023-01-01T12:00:00Z"}
        }
        
        # モック設定
        self.mock_conversations_container.read_item.return_value = conversation_data
        
        mock_messages = [
            {"id": "msg_1", "sender": {"role": "user"}, "content": {"text": "ユーザーメッセージ"}, "metadata": {"tokens": 10, "duration": 1.0}},
            {"id": "msg_2", "sender": {"role": "assistant"}, "content": {"text": "アシスタントメッセージ"}, "metadata": {"tokens": 20, "duration": 2.0}}
        ]
        self.mock_messages_container.query_items.return_value = mock_messages
        
        # 統計取得
        stats = await self.manager.get_conversation_stats("test123")
        
        # 検証
        assert stats["conversation_id"] == "test123"
        assert stats["title"] == "統計テスト会話"
        assert stats["message_count"] == 2
        assert stats["participant_count"] == 1
        assert "user_message_count" in stats
        assert "assistant_message_count" in stats
    
    @pytest.mark.asyncio
    async def test_get_conversation_stats_not_found(self):
        """存在しない会話の統計取得テスト"""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        # モック設定
        self.mock_conversations_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )
        
        # 統計取得
        stats = await self.manager.get_conversation_stats("nonexistent")
        
        # 検証
        assert "error" in stats
    
    @pytest.mark.asyncio
    async def test_get_tenant_stats(self):
        """テナント統計取得テスト"""
        # モック設定
        mock_conversations = [
            {"id": "conv_1", "status": "active", "archived": False, "categories": [{"categoryName": "tech"}]},
            {"id": "conv_2", "status": "active", "archived": True, "categories": [{"categoryName": "general"}]},
            {"id": "conv_3", "status": "deleted", "archived": True, "categories": [{"categoryName": "tech"}]}
        ]
        self.mock_conversations_container.query_items.return_value = mock_conversations
        
        # 統計取得
        stats = await self.manager.get_tenant_stats()
        
        # 検証
        assert stats["tenant_id"] == "test_tenant"
        assert stats["total_conversations"] == 3
        assert stats["active_conversations"] == 2
        assert stats["archived_conversations"] == 2
        assert "top_categories" in stats


class TestFactoryFunction:
    """ファクトリー関数テスト"""
    
    @patch('cosmos_history.cosmos_history_manager.CosmosDBClient')
    def test_create_cosmos_history_manager(self, mock_cosmos_client_class):
        """Cosmos DB履歴管理マネージャー作成テスト"""
        # モック設定
        mock_client_instance = Mock()
        mock_client_instance.is_ready.return_value = True
        mock_client_instance.get_conversations_container.return_value = Mock()
        mock_client_instance.get_messages_container.return_value = Mock()
        mock_cosmos_client_class.return_value = mock_client_instance
        
        # マネージャー作成
        manager = create_cosmos_history_manager("test_tenant")
        
        # 検証
        assert isinstance(manager, CosmosHistoryManager)
        assert manager.tenant_id == "test_tenant"
        mock_cosmos_client_class.assert_called_once_with(None)


# テスト実行関数
def run_history_manager_tests():
    """履歴管理テスト実行"""
    print("=== Cosmos DB履歴管理テスト実行 ===")
    
    try:
        # CosmosHistoryManager テスト
        print("🔍 CosmosHistoryManager テスト...")
        test_manager = TestCosmosHistoryManager()
        test_manager.setup_method()
        test_manager.test_initialization()
        test_manager.test_initialization_not_ready()
        print("✅ CosmosHistoryManager テスト完了")
        
        # ファクトリー関数テスト
        print("🔍 ファクトリー関数テスト...")
        test_factory = TestFactoryFunction()
        print("✅ ファクトリー関数テスト完了")
        
        print("🎉 全履歴管理テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 履歴管理テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_history_manager_tests()