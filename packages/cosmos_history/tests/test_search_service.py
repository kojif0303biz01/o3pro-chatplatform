"""
検索サービステスト

CosmosSearchService の基本動作テスト（モック使用）
"""

import pytest
from unittest.mock import Mock, patch
from cosmos_history.search_service import (
    CosmosSearchService, SearchQuery, SearchResult, DateRange,
    SearchSortField, SearchSortOrder, create_search_service
)


class TestSearchQuery:
    """SearchQuery テスト"""
    
    def test_search_query_creation(self):
        """検索クエリ作成テスト"""
        query = SearchQuery(
            keyword="Python",
            tenant_id="test_tenant",
            participant_user_ids=["user1", "user2"],
            category_ids=["tech"],
            tags=["プログラミング"],
            page_size=10
        )
        
        assert query.keyword == "Python"
        assert query.tenant_id == "test_tenant"
        assert query.participant_user_ids == ["user1", "user2"]
        assert query.category_ids == ["tech"]
        assert query.tags == ["プログラミング"]
        assert query.page_size == 10
        assert query.sort_field == SearchSortField.UPDATED_AT
        assert query.sort_order == SearchSortOrder.DESC
    
    def test_search_query_defaults(self):
        """検索クエリデフォルト値テスト"""
        query = SearchQuery()
        
        assert query.keyword is None
        assert query.tenant_id is None
        assert query.participant_user_ids is None
        assert query.category_ids is None
        assert query.tags is None
        assert query.page_size == 20
        assert query.sort_field == SearchSortField.UPDATED_AT
        assert query.sort_order == SearchSortOrder.DESC
        assert not query.include_archived
        assert not query.high_confidence_only


class TestDateRange:
    """DateRange テスト"""
    
    def test_date_range_valid(self):
        """有効な日時範囲テスト"""
        date_range = DateRange(
            start_date="2023-01-01T00:00:00Z",
            end_date="2023-12-31T23:59:59Z"
        )
        
        assert date_range.is_valid()
    
    def test_date_range_invalid(self):
        """無効な日時範囲テスト"""
        date_range = DateRange(
            start_date="2023-12-31T23:59:59Z",
            end_date="2023-01-01T00:00:00Z"
        )
        
        assert not date_range.is_valid()
    
    def test_date_range_single_date(self):
        """単一日時範囲テスト"""
        date_range = DateRange(start_date="2023-01-01T00:00:00Z")
        assert date_range.is_valid()
        
        date_range = DateRange(end_date="2023-12-31T23:59:59Z")
        assert date_range.is_valid()
    
    def test_date_range_empty(self):
        """空の日時範囲テスト"""
        date_range = DateRange()
        assert date_range.is_valid()


class TestSearchResult:
    """SearchResult テスト"""
    
    def test_search_result_creation(self):
        """検索結果作成テスト"""
        items = [{"id": "1", "title": "テスト1"}, {"id": "2", "title": "テスト2"}]
        result = SearchResult(
            items=items,
            total_count=100,
            continuation_token="token123",
            has_more=True,
            search_time_ms=150.5
        )
        
        assert len(result.items) == 2
        assert result.total_count == 100
        assert result.continuation_token == "token123"
        assert result.has_more is True
        assert result.search_time_ms == 150.5
    
    def test_search_result_to_dict(self):
        """検索結果の辞書変換テスト"""
        items = [{"id": "1", "title": "テスト1"}]
        result = SearchResult(items=items, total_count=1)
        
        result_dict = result.to_dict()
        
        assert "items" in result_dict
        assert "total_count" in result_dict
        assert "continuation_token" in result_dict
        assert "has_more" in result_dict
        assert "search_time_ms" in result_dict
        assert result_dict["total_count"] == 1


class TestCosmosSearchService:
    """CosmosSearchService テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_conversations_container = Mock()
        self.mock_messages_container = Mock()
        
        self.search_service = CosmosSearchService(
            self.mock_conversations_container,
            self.mock_messages_container
        )
    
    @pytest.mark.asyncio
    async def test_search_conversations_basic(self):
        """基本的な会話検索テスト"""
        # モック設定
        mock_items = [
            {"id": "conv_1", "title": "テスト会話1", "tenantId": "test_tenant"},
            {"id": "conv_2", "title": "テスト会話2", "tenantId": "test_tenant"}
        ]
        
        mock_iterator = Mock()
        mock_iterator.__iter__ = Mock(return_value=iter(mock_items))
        mock_iterator.response_headers = {}
        
        self.mock_conversations_container.query_items.return_value = mock_iterator
        
        # 検索実行
        query = SearchQuery(
            keyword="テスト",
            tenant_id="test_tenant",
            page_size=10
        )
        
        with patch('cosmos_history.models.conversation.ChatConversation.from_cosmos_dict') as mock_from_dict:
            mock_from_dict.side_effect = lambda x: Mock(**x)
            
            result = await self.search_service.search_conversations(query)
        
        # 検証
        assert isinstance(result, SearchResult)
        assert len(result.items) == 2
        assert result.search_time_ms > 0
        self.mock_conversations_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_conversations_with_filters(self):
        """フィルター付き会話検索テスト"""
        # モック設定
        self.mock_conversations_container.query_items.return_value = []
        
        # フィルター付き検索
        query = SearchQuery(
            keyword="Python",
            tenant_id="test_tenant",
            participant_user_ids=["user1"],
            category_ids=["tech"],
            tags=["プログラミング"],
            include_archived=False,
            high_confidence_only=True
        )
        
        result = await self.search_service.search_conversations(query)
        
        # クエリが正しく構築されたことを確認
        call_args = self.mock_conversations_container.query_items.call_args
        query_str = call_args[1]["query"]
        parameters = call_args[1]["parameters"]
        
        # フィルター条件がクエリに含まれていることを確認
        assert "CONTAINS" in query_str  # キーワード検索
        assert "ARRAY_CONTAINS" in query_str  # 参加者・カテゴリー・タグ検索
        assert "archived" in query_str  # アーカイブフィルター
        assert "confidence" in query_str  # 高信頼度フィルター
        
        # パラメーターが正しく設定されていることを確認
        param_names = [p["name"] for p in parameters]
        assert "@tenantId" in param_names
        assert "@keyword" in param_names
    
    @pytest.mark.asyncio
    async def test_search_conversations_with_date_range(self):
        """日時範囲付き会話検索テスト"""
        # モック設定
        self.mock_conversations_container.query_items.return_value = []
        
        # 日時範囲付き検索
        date_range = DateRange(
            start_date="2023-01-01T00:00:00Z",
            end_date="2023-12-31T23:59:59Z"
        )
        query = SearchQuery(
            tenant_id="test_tenant",
            date_range=date_range
        )
        
        result = await self.search_service.search_conversations(query)
        
        # 日時範囲条件がクエリに含まれていることを確認
        call_args = self.mock_conversations_container.query_items.call_args
        query_str = call_args[1]["query"]
        parameters = call_args[1]["parameters"]
        
        assert "lastMessageAt >=" in query_str
        assert "lastMessageAt <=" in query_str
        
        param_names = [p["name"] for p in parameters]
        assert "@startDate" in param_names
        assert "@endDate" in param_names
    
    @pytest.mark.asyncio
    async def test_search_messages_basic(self):
        """基本的なメッセージ検索テスト"""
        # モック設定
        mock_items = [
            {"id": "msg_1", "content": {"text": "テストメッセージ1"}, "tenantId": "test_tenant"},
            {"id": "msg_2", "content": {"text": "テストメッセージ2"}, "tenantId": "test_tenant"}
        ]
        
        mock_iterator = Mock()
        mock_iterator.__iter__ = Mock(return_value=iter(mock_items))
        mock_iterator.response_headers = {}
        
        self.mock_messages_container.query_items.return_value = mock_iterator
        
        # 検索実行
        query = SearchQuery(
            keyword="テスト",
            tenant_id="test_tenant",
            page_size=10
        )
        
        with patch('cosmos_history.models.message.ChatMessage.from_cosmos_dict') as mock_from_dict:
            mock_from_dict.side_effect = lambda x: Mock(**x)
            
            result = await self.search_service.search_messages(query)
        
        # 検証
        assert isinstance(result, SearchResult)
        assert len(result.items) == 2
        assert result.search_time_ms > 0
        self.mock_messages_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_messages_with_sender_filters(self):
        """送信者フィルター付きメッセージ検索テスト"""
        # モック設定
        self.mock_messages_container.query_items.return_value = []
        
        # 送信者フィルター付き検索
        query = SearchQuery(
            tenant_id="test_tenant",
            participant_user_ids=["user1", "user2"],
            participant_names=["テストユーザー"],
            sender_roles=["user", "assistant"]
        )
        
        result = await self.search_service.search_messages(query)
        
        # フィルター条件がクエリに含まれていることを確認
        call_args = self.mock_messages_container.query_items.call_args
        query_str = call_args[1]["query"]
        parameters = call_args[1]["parameters"]
        
        # 送信者ID、名前、ロールフィルターが含まれることを確認
        assert "sender.userId" in query_str
        assert "sender.displayName" in query_str
        assert "sender.role" in query_str
        
        # パラメーターが正しく設定されていることを確認
        param_names = [p["name"] for p in parameters]
        assert any("senderId" in name for name in param_names)
        assert any("senderName" in name for name in param_names)
        assert any("role" in name for name in param_names)
    
    @pytest.mark.asyncio
    async def test_search_combined(self):
        """統合検索テスト"""
        # モック設定
        self.mock_conversations_container.query_items.return_value = []
        self.mock_messages_container.query_items.return_value = []
        
        # 統合検索実行
        query = SearchQuery(keyword="テスト", tenant_id="test_tenant")
        
        with patch('cosmos_history.models.conversation.ChatConversation.from_cosmos_dict'), \
             patch('cosmos_history.models.message.ChatMessage.from_cosmos_dict'):
            
            result = await self.search_service.search_combined(query)
        
        # 検証
        assert "conversations" in result
        assert "messages" in result
        assert "combined_time_ms" in result
        assert isinstance(result["conversations"], SearchResult)
        assert isinstance(result["messages"], SearchResult)
    
    @pytest.mark.asyncio
    async def test_search_combined_with_error(self):
        """エラー発生時の統合検索テスト"""
        # モック設定（エラー発生）
        self.mock_conversations_container.query_items.side_effect = Exception("Connection error")
        self.mock_messages_container.query_items.return_value = []
        
        # 統合検索実行
        query = SearchQuery(keyword="テスト", tenant_id="test_tenant")
        
        with patch('cosmos_history.models.message.ChatMessage.from_cosmos_dict'):
            result = await self.search_service.search_combined(query)
        
        # エラーハンドリングの確認
        assert "conversations" in result
        assert "messages" in result
        assert len(result["conversations"].items) == 0  # エラー時は空の結果
        assert len(result["messages"].items) == 0
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self):
        """検索候補取得テスト"""
        # モック設定
        mock_suggestions = [
            {"title": "Python学習ガイド"},
            {"title": "Python開発環境"},
            {"title": "Pythonライブラリ"}
        ]
        self.mock_conversations_container.query_items.return_value = mock_suggestions
        
        # 検索候補取得
        suggestions = await self.search_service.get_search_suggestions(
            tenant_id="test_tenant",
            partial_query="Python",
            limit=5
        )
        
        # 検証
        assert len(suggestions) == 3
        assert all("Python" in title for title in suggestions)
        self.mock_conversations_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions_short_query(self):
        """短いクエリでの検索候補取得テスト"""
        # 短いクエリ（2文字未満）
        suggestions = await self.search_service.get_search_suggestions(
            tenant_id="test_tenant",
            partial_query="P",
            limit=5
        )
        
        # 短すぎるクエリでは候補を返さない
        assert len(suggestions) == 0
        self.mock_conversations_container.query_items.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_search_facets(self):
        """検索ファセット取得テスト"""
        # モック設定
        mock_categories = [
            {"categoryName": "技術", "categoryId": "tech"},
            {"categoryName": "一般", "categoryId": "general"}
        ]
        mock_participants = [
            {"displayName": "テストユーザー", "userId": "user1"},
            {"displayName": "アシスタント", "userId": "assistant"}
        ]
        
        # query_itemsの呼び出し順序でモック結果を返す
        call_count = 0
        def mock_query_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_categories
            elif call_count == 2:
                return mock_participants
            return []
        
        self.mock_conversations_container.query_items.side_effect = mock_query_side_effect
        
        # ファセット取得
        facets = await self.search_service.get_search_facets("test_tenant")
        
        # 検証
        assert "categories" in facets
        assert "participants" in facets
        assert "tags" in facets
        assert len(facets["categories"]) == 2
        assert len(facets["participants"]) == 2
        
        # カテゴリーファセットの内容確認
        tech_category = next((c for c in facets["categories"] if c["id"] == "tech"), None)
        assert tech_category is not None
        assert tech_category["name"] == "技術"
    
    def test_cache_functionality(self):
        """キャッシュ機能テスト"""
        # キャッシュキー生成テスト
        query = SearchQuery(keyword="テスト", tenant_id="test_tenant")
        cache_key = self.search_service._generate_cache_key("conversations", query)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5ハッシュの長さ
        
        # キャッシュ保存・取得テスト
        test_result = SearchResult(items=[{"test": "data"}])
        self.search_service._cache_result(cache_key, test_result)
        
        cached_result = self.search_service._get_cached_result(cache_key)
        assert cached_result is test_result
        
        # キャッシュクリアテスト
        self.search_service.clear_cache()
        cached_result = self.search_service._get_cached_result(cache_key)
        assert cached_result is None


class TestFactoryFunction:
    """ファクトリー関数テスト"""
    
    def test_create_search_service(self):
        """検索サービス作成テスト"""
        # モッククライアント作成
        mock_cosmos_client = Mock()
        mock_conversations_container = Mock()
        mock_messages_container = Mock()
        
        mock_cosmos_client.get_conversations_container.return_value = mock_conversations_container
        mock_cosmos_client.get_messages_container.return_value = mock_messages_container
        
        # 検索サービス作成
        search_service = create_search_service(mock_cosmos_client)
        
        # 検証
        assert isinstance(search_service, CosmosSearchService)
        assert search_service.conversations_container is mock_conversations_container
        assert search_service.messages_container is mock_messages_container


# テスト実行関数
def run_search_service_tests():
    """検索サービステスト実行"""
    print("=== 検索サービステスト実行 ===")
    
    try:
        # SearchQuery テスト
        print("🔍 SearchQuery テスト...")
        test_query = TestSearchQuery()
        test_query.test_search_query_creation()
        test_query.test_search_query_defaults()
        print("✅ SearchQuery テスト完了")
        
        # DateRange テスト
        print("🔍 DateRange テスト...")
        test_date_range = TestDateRange()
        test_date_range.test_date_range_valid()
        test_date_range.test_date_range_invalid()
        test_date_range.test_date_range_single_date()
        test_date_range.test_date_range_empty()
        print("✅ DateRange テスト完了")
        
        # SearchResult テスト
        print("🔍 SearchResult テスト...")
        test_result = TestSearchResult()
        test_result.test_search_result_creation()
        test_result.test_search_result_to_dict()
        print("✅ SearchResult テスト完了")
        
        # CosmosSearchService テスト
        print("🔍 CosmosSearchService テスト...")
        test_service = TestCosmosSearchService()
        test_service.setup_method()
        test_service.test_cache_functionality()
        print("✅ CosmosSearchService テスト完了")
        
        # ファクトリー関数テスト
        print("🔍 ファクトリー関数テスト...")
        test_factory = TestFactoryFunction()
        test_factory.test_create_search_service()
        print("✅ ファクトリー関数テスト完了")
        
        print("🎉 全検索サービステスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 検索サービステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_search_service_tests()