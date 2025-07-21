"""
移行サービステスト

DataMigrationService の基本動作テスト（モック使用）
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from cosmos_history.migration_service import (
    DataMigrationService, MigrationStats, create_migration_service
)


class TestMigrationStats:
    """MigrationStats テスト"""
    
    def test_migration_stats_initialization(self):
        """移行統計初期化テスト"""
        stats = MigrationStats()
        
        assert stats.total_sessions == 0
        assert stats.migrated_conversations == 0
        assert stats.failed_conversations == 0
        assert stats.total_messages == 0
        assert stats.migrated_messages == 0
        assert stats.failed_messages == 0
        assert len(stats.errors) == 0
        assert len(stats.warnings) == 0
        assert isinstance(stats.start_time, datetime)
    
    def test_add_error(self):
        """エラー追加テスト"""
        stats = MigrationStats()
        
        stats.add_error("session_123", "テストエラー")
        
        assert len(stats.errors) == 1
        error = stats.errors[0]
        assert error["session_id"] == "session_123"
        assert error["error"] == "テストエラー"
        assert "timestamp" in error
    
    def test_add_warning(self):
        """警告追加テスト"""
        stats = MigrationStats()
        
        stats.add_warning("session_123", "テスト警告")
        
        assert len(stats.warnings) == 1
        warning = stats.warnings[0]
        assert warning["session_id"] == "session_123"
        assert warning["warning"] == "テスト警告"
        assert "timestamp" in warning
    
    def test_get_summary(self):
        """統計サマリー取得テスト"""
        stats = MigrationStats()
        stats.total_sessions = 10
        stats.migrated_conversations = 8
        stats.failed_conversations = 2
        stats.total_messages = 50
        stats.migrated_messages = 45
        stats.failed_messages = 5
        
        summary = stats.get_summary()
        
        assert summary["total_sessions"] == 10
        assert summary["migrated_conversations"] == 8
        assert summary["failed_conversations"] == 2
        assert summary["conversation_success_rate"] == 0.8
        assert summary["total_messages"] == 50
        assert summary["migrated_messages"] == 45
        assert summary["failed_messages"] == 5
        assert summary["message_success_rate"] == 0.9
        assert "migration_started_at" in summary
        assert "migration_duration_seconds" in summary


class TestDataMigrationService:
    """DataMigrationService テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        # モックマネージャー作成
        self.mock_local_manager = Mock()
        self.mock_cosmos_manager = Mock()
        self.mock_cosmos_manager.tenant_id = "test_tenant"
        
        # 移行サービス作成
        self.migration_service = DataMigrationService(
            self.mock_local_manager,
            self.mock_cosmos_manager,
            "test_user"
        )
    
    @pytest.mark.asyncio
    async def test_migrate_all_data_no_sessions(self):
        """セッションが存在しない場合の移行テスト"""
        # モック設定
        self.mock_local_manager.list_sessions.return_value = []
        
        # 移行実行
        result = await self.migration_service.migrate_all_data(dry_run=False)
        
        # 検証
        assert result["total_sessions"] == 0
        assert result["migrated_conversations"] == 0
        assert result["failed_conversations"] == 0
        self.mock_local_manager.list_sessions.assert_called_once_with(limit=None)
    
    @pytest.mark.asyncio
    async def test_migrate_all_data_dry_run(self):
        """ドライラン移行テスト"""
        # モック設定
        mock_sessions = [
            {"id": "session_1", "title": "テストセッション1"},
            {"id": "session_2", "title": "テストセッション2"}
        ]
        self.mock_local_manager.list_sessions.return_value = mock_sessions
        self.mock_local_manager.get_session_messages.return_value = [
            {"role": "user", "content": "テストメッセージ1"},
            {"role": "assistant", "content": "テストメッセージ2"}
        ]
        
        # ドライラン実行
        result = await self.migration_service.migrate_all_data(dry_run=True)
        
        # 検証
        assert result["total_sessions"] == 2
        assert result["migrated_conversations"] == 2
        assert result["total_messages"] == 4  # 2セッション × 2メッセージ
        assert result["migrated_messages"] == 4
        assert result["failed_conversations"] == 0
        
        # 実際のCosmos DB操作は実行されないことを確認
        self.mock_cosmos_manager.get_conversation.assert_not_called()
        self.mock_cosmos_manager.create_conversation.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_migrate_session_already_exists(self):
        """既存セッションの移行スキップテスト"""
        # モック設定
        session_info = {"id": "session_1", "title": "既存セッション"}
        
        # 既存会話を返すモック
        existing_conversation = Mock()
        self.mock_cosmos_manager.get_conversation = AsyncMock(return_value=existing_conversation)
        
        self.mock_local_manager.get_session_messages.return_value = [
            {"role": "user", "content": "テストメッセージ"}
        ]
        
        # セッション移行
        await self.migration_service._migrate_session(session_info, dry_run=False)
        
        # 検証
        assert len(self.migration_service.stats.warnings) == 1
        warning = self.migration_service.stats.warnings[0]
        assert "already exists" in warning["warning"]
        
        # 会話作成は実行されないことを確認
        self.mock_cosmos_manager.create_conversation.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_migrate_session_success(self):
        """セッション移行成功テスト"""
        # モック設定
        session_info = {
            "id": "session_1",
            "title": "新規セッション",
            "mode": "reasoning",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        local_messages = [
            {
                "role": "user",
                "content": "こんにちは",
                "timestamp": "2023-01-01T00:01:00Z",
                "metadata": {"duration": 0.5, "tokens": 5}
            },
            {
                "role": "assistant",
                "content": "こんにちは！何かお手伝いできることはありますか？",
                "timestamp": "2023-01-01T00:02:00Z",
                "metadata": {"duration": 2.0, "tokens": 15}
            }
        ]
        
        # 会話が存在しない
        self.mock_cosmos_manager.get_conversation = AsyncMock(return_value=None)
        
        # 会話作成をモック
        created_conversation = Mock()
        created_conversation.conversation_id = "conv_new_123"
        self.mock_cosmos_manager.create_conversation = AsyncMock(return_value=created_conversation)
        
        # メッセージ追加をモック
        self.mock_cosmos_manager.add_message = AsyncMock()
        
        # 会話更新をモック
        self.mock_cosmos_manager.update_conversation = AsyncMock()
        
        self.mock_local_manager.get_session_messages.return_value = local_messages
        
        # セッション移行
        await self.migration_service._migrate_session(session_info, dry_run=False)
        
        # 検証
        self.mock_cosmos_manager.create_conversation.assert_called_once()
        assert self.mock_cosmos_manager.add_message.call_count == 2
        self.mock_cosmos_manager.update_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_migrate_session_message_error(self):
        """メッセージ移行エラーテスト"""
        # モック設定
        session_info = {"id": "session_1", "title": "エラーセッション"}
        local_messages = [
            {"role": "user", "content": "テストメッセージ1"},
            {"role": "assistant", "content": "テストメッセージ2"}
        ]
        
        # 会話作成は成功
        self.mock_cosmos_manager.get_conversation = AsyncMock(return_value=None)
        created_conversation = Mock()
        created_conversation.conversation_id = "conv_123"
        self.mock_cosmos_manager.create_conversation = AsyncMock(return_value=created_conversation)
        
        # 最初のメッセージは成功、2番目のメッセージでエラー
        def mock_add_message_side_effect(*args, **kwargs):
            if self.mock_cosmos_manager.add_message.call_count == 1:
                return AsyncMock()  # 成功
            else:
                raise Exception("メッセージ追加エラー")  # エラー
        
        self.mock_cosmos_manager.add_message = AsyncMock(side_effect=mock_add_message_side_effect)
        self.mock_cosmos_manager.update_conversation = AsyncMock()
        self.mock_local_manager.get_session_messages.return_value = local_messages
        
        # セッション移行
        await self.migration_service._migrate_session(session_info, dry_run=False)
        
        # 検証
        assert self.migration_service.stats.migrated_messages == 1
        assert self.migration_service.stats.failed_messages == 1
        assert len(self.migration_service.stats.errors) == 1
    
    def test_convert_session_to_conversation(self):
        """セッション→会話変換テスト"""
        # テストデータ
        local_session = {
            "id": "session_123",
            "title": "変換テスト",
            "mode": "streaming",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        messages = [
            {"role": "user", "content": "質問です", "metadata": {"duration": 1.0, "tokens": 5}},
            {"role": "assistant", "content": "回答です", "metadata": {"duration": 2.0, "tokens": 10}}
        ]
        
        # 変換実行
        conversation = self.migration_service._convert_session_to_conversation(
            local_session, messages
        )
        
        # 検証
        from cosmos_history.models.conversation import ChatConversation
        assert isinstance(conversation, ChatConversation)
        assert conversation.title == "変換テスト"
        assert len(conversation.participants) > 0
        assert len(conversation.categories) > 0
        assert "移行済み" in conversation.tags
        assert "streaming" in conversation.tags
        assert conversation.metrics.message_count == 2
    
    def test_analyze_participants(self):
        """参加者分析テスト"""
        messages = [
            {"role": "user", "content": "ユーザーメッセージ"},
            {"role": "assistant", "content": "アシスタントメッセージ"},
            {"role": "system", "content": "システムメッセージ"}
        ]
        
        participants = self.migration_service._analyze_participants(messages)
        
        # 検証
        assert len(participants) == 3
        
        user_participant = next((p for p in participants if p["role"] == "user"), None)
        assert user_participant is not None
        assert user_participant["user_id"] == "test_user"
        assert user_participant["display_name"] == "ユーザー"
        
        assistant_participant = next((p for p in participants if p["role"] == "assistant"), None)
        assert assistant_participant is not None
        assert assistant_participant["user_id"] == "assistant"
        assert assistant_participant["display_name"] == "アシスタント"
    
    def test_calculate_message_metrics(self):
        """メッセージメトリクス計算テスト"""
        messages = [
            {
                "role": "user",
                "metadata": {"duration": 1.0, "tokens": 10}
            },
            {
                "role": "assistant",
                "metadata": {"duration": 2.5, "tokens": 20}
            },
            {
                "role": "assistant",
                "metadata": {"duration": 1.5, "tokens": 15}
            }
        ]
        
        metrics = self.migration_service._calculate_message_metrics(messages)
        
        # 検証
        assert metrics["total_duration"] == 5.0
        assert metrics["total_tokens"] == 45
        assert metrics["avg_response_time"] == 2.0  # (2.5 + 1.5) / 2
    
    def test_convert_message_format(self):
        """メッセージフォーマット変換テスト"""
        local_message = {
            "role": "user",
            "content": "テストメッセージ",
            "timestamp": "2023-01-01T00:00:00Z",
            "metadata": {
                "mode": "reasoning",
                "effort": "medium",
                "duration": 1.5,
                "tokens": 10,
                "model": "gpt-4"
            }
        }
        
        conversation_id = "conv_123"
        
        # 変換実行
        message = self.migration_service._convert_message_format(local_message, conversation_id)
        
        # 検証
        from cosmos_history.models.message import ChatMessage
        assert isinstance(message, ChatMessage)
        assert message.conversation_id == conversation_id
        assert message.sender.user_id == "test_user"
        assert message.sender.role == "user"
        assert message.content.text == "テストメッセージ"
        assert message.timestamp == "2023-01-01T00:00:00Z"
        assert message.metadata.mode == "reasoning"
        assert message.metadata.duration == 1.5
        assert message.metadata.tokens == 10
    
    @pytest.mark.asyncio
    async def test_verify_migration(self):
        """移行検証テスト"""
        # モック設定
        local_sessions = [
            {"id": "session_1"},
            {"id": "session_2"},
            {"id": "session_3"}
        ]
        self.mock_local_manager.list_sessions.return_value = local_sessions
        
        cosmos_conversations = [
            Mock(), Mock(), Mock()  # 3つの会話
        ]
        self.mock_cosmos_manager.list_conversations = AsyncMock(return_value=cosmos_conversations)
        
        # サンプル検証用のモック
        self.mock_local_manager.get_session_messages.return_value = [Mock(), Mock()]  # 2メッセージ
        
        sample_conversation = Mock()
        sample_conversation.conversation_id = "conv_sample"
        self.mock_cosmos_manager.get_conversation = AsyncMock(return_value=sample_conversation)
        self.mock_cosmos_manager.get_conversation_messages = AsyncMock(return_value=[Mock(), Mock()])  # 2メッセージ
        
        # 検証実行
        verification = await self.migration_service.verify_migration()
        
        # 検証結果確認
        assert verification["local_sessions"] == 3
        assert verification["cosmos_conversations"] == 3
        assert verification["session_match"] is True
        assert verification["message_match"] is True
        assert "sample_verification" in verification
    
    @pytest.mark.asyncio
    async def test_rollback_migration_invalid_confirmation(self):
        """無効な確認コードでのロールバックテスト"""
        with pytest.raises(ValueError, match="Invalid confirmation code"):
            await self.migration_service.rollback_migration("WRONG_CODE")
    
    @pytest.mark.asyncio
    async def test_rollback_migration_success(self):
        """ロールバック成功テスト"""
        # モック設定
        mock_conversations = [
            Mock(conversation_id="conv_1"),
            Mock(conversation_id="conv_2")
        ]
        self.mock_cosmos_manager.list_conversations = AsyncMock(return_value=mock_conversations)
        
        mock_messages = [Mock(id="msg_1", conversation_id="conv_1")]
        self.mock_cosmos_manager.get_conversation_messages = AsyncMock(return_value=mock_messages)
        self.mock_cosmos_manager.delete_message = AsyncMock()
        self.mock_cosmos_manager.delete_conversation = AsyncMock()
        
        # ロールバック実行
        result = await self.migration_service.rollback_migration("CONFIRM_ROLLBACK_DELETE_ALL")
        
        # 検証
        assert result["deleted_conversations"] == 2
        assert result["deleted_messages"] >= 1
        assert len(result["errors"]) == 0
        assert "start_time" in result
        assert "end_time" in result


class TestFactoryFunction:
    """ファクトリー関数テスト"""
    
    @patch('cosmos_history.migration_service.ChatHistoryManager')
    def test_create_migration_service(self, mock_history_manager_class):
        """移行サービス作成テスト"""
        # モック設定
        mock_local_manager = Mock()
        mock_history_manager_class.return_value = mock_local_manager
        
        mock_cosmos_manager = Mock()
        
        # サービス作成
        service = create_migration_service(
            local_history_dir="test_dir",
            cosmos_manager=mock_cosmos_manager,
            default_user_id="test_user"
        )
        
        # 検証
        assert isinstance(service, DataMigrationService)
        assert service.cosmos_manager is mock_cosmos_manager
        assert service.default_user_id == "test_user"
        mock_history_manager_class.assert_called_once_with("test_dir")


# テスト実行関数
def run_migration_service_tests():
    """移行サービステスト実行"""
    print("=== 移行サービステスト実行 ===")
    
    try:
        # MigrationStats テスト
        print("🔍 MigrationStats テスト...")
        test_stats = TestMigrationStats()
        test_stats.test_migration_stats_initialization()
        test_stats.test_add_error()
        test_stats.test_add_warning()
        test_stats.test_get_summary()
        print("✅ MigrationStats テスト完了")
        
        # DataMigrationService テスト
        print("🔍 DataMigrationService テスト...")
        test_service = TestDataMigrationService()
        test_service.setup_method()
        test_service.test_convert_session_to_conversation()
        test_service.test_analyze_participants()
        test_service.test_calculate_message_metrics()
        test_service.test_convert_message_format()
        print("✅ DataMigrationService テスト完了")
        
        # ファクトリー関数テスト
        print("🔍 ファクトリー関数テスト...")
        test_factory = TestFactoryFunction()
        print("✅ ファクトリー関数テスト完了")
        
        print("🎉 全移行サービステスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 移行サービステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_migration_service_tests()