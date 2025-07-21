"""
Cosmos DB 検索サービス

高度な検索・フィルタリング・ソート機能を提供
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import CosmosHttpResponseError

from .models.conversation import ChatConversation
from .models.message import ChatMessage

logger = logging.getLogger(__name__)


class SearchSortOrder(Enum):
    """ソート順序"""
    ASC = "ascending"
    DESC = "descending"


class SearchSortField(Enum):
    """ソートフィールド"""
    TIMESTAMP = "timestamp"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"
    MESSAGE_COUNT = "messageCount"
    RELEVANCE = "relevance"
    TITLE = "title"


@dataclass
class DateRange:
    """日時範囲"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    def is_valid(self) -> bool:
        """有効な範囲かどうか"""
        if not self.start_date and not self.end_date:
            return True
        
        try:
            if self.start_date and self.end_date:
                start = datetime.fromisoformat(self.start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(self.end_date.replace('Z', '+00:00'))
                return start <= end
            return True
        except:
            return False


@dataclass
class SearchQuery:
    """検索クエリ"""
    # 基本検索
    keyword: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # 人検索
    participant_user_ids: Optional[List[str]] = None
    participant_names: Optional[List[str]] = None
    
    # カテゴリー・タグ検索
    category_ids: Optional[List[str]] = None
    category_names: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    # 日時範囲
    date_range: Optional[DateRange] = None
    
    # メッセージ特有フィルター
    sender_roles: Optional[List[str]] = None  # user, assistant, system
    
    # ソート
    sort_field: SearchSortField = SearchSortField.UPDATED_AT
    sort_order: SearchSortOrder = SearchSortOrder.DESC
    
    # ページング
    page_size: int = 20
    continuation_token: Optional[str] = None
    
    # フラグ
    include_archived: bool = False
    high_confidence_only: bool = False  # カテゴリー分類の信頼度


@dataclass
class SearchResult:
    """検索結果"""
    items: List[Any]
    total_count: Optional[int] = None
    continuation_token: Optional[str] = None
    has_more: bool = False
    search_time_ms: float = 0.0
    query_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [
                item.to_dict() if hasattr(item, 'to_dict') else item 
                for item in self.items
            ],
            "total_count": self.total_count,
            "continuation_token": self.continuation_token,
            "has_more": self.has_more,
            "search_time_ms": self.search_time_ms,
            "query_info": self.query_info
        }


class CosmosSearchService:
    """Cosmos DB検索サービス"""
    
    def __init__(self, conversations_container: ContainerProxy, messages_container: ContainerProxy):
        self.conversations_container = conversations_container
        self.messages_container = messages_container
        
        # 簡易キャッシュ
        self.query_cache = {}
        self.cache_ttl = 300  # 5分
        
        logger.info("CosmosSearchService initialized")
    
    # ==================== 会話検索 ====================
    
    async def search_conversations(self, query: SearchQuery) -> SearchResult:
        """会話検索"""
        start_time = time.time()
        
        try:
            # キャッシュ確認
            cache_key = self._generate_cache_key("conversations", query)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # クエリ構築
            sql_query, parameters = self._build_conversations_query(query)
            
            # 実行
            query_options = {
                "enable_cross_partition_query": True,
                "max_item_count": query.page_size
            }
            
            if query.continuation_token:
                query_options["continuation"] = query.continuation_token
            
            logger.debug(f"Executing conversation search: {sql_query}")
            
            result_iterator = self.conversations_container.query_items(
                query=sql_query,
                parameters=parameters,
                **query_options
            )
            
            items = []
            continuation_token = None
            
            # 結果取得
            for item in result_iterator:
                items.append(ChatConversation.from_cosmos_dict(item))
            
            # 継続トークン取得（実装依存）
            try:
                if hasattr(result_iterator, 'response_headers'):
                    continuation_token = result_iterator.response_headers.get("x-ms-continuation")
            except:
                pass
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = SearchResult(
                items=items,
                continuation_token=continuation_token,
                has_more=bool(continuation_token),
                search_time_ms=search_time_ms,
                query_info={
                    "sql_query": sql_query,
                    "parameters": parameters,
                    "total_results": len(items)
                }
            )
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            
            logger.info(f"Conversation search completed: {len(items)} results in {search_time_ms:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Conversation search failed: {e}")
            raise Exception(f"会話検索エラー: {str(e)}")
    
    def _build_conversations_query(self, query: SearchQuery) -> Tuple[str, List[Dict[str, Any]]]:
        """会話検索クエリ構築"""
        conditions = []
        parameters = []
        
        # テナントID（必須）
        if query.tenant_id:
            conditions.append("c.tenantId = @tenantId")
            parameters.append({"name": "@tenantId", "value": query.tenant_id})
        
        # キーワード検索（タイトル、要約、検索用テキスト）
        if query.keyword:
            conditions.append("(CONTAINS(c.title, @keyword) OR CONTAINS(c.summary, @keyword) OR CONTAINS(c.searchableText, @keyword))")
            parameters.append({"name": "@keyword", "value": query.keyword.lower()})
        
        # 参加者検索（ユーザーID）
        if query.participant_user_ids:
            participant_conditions = []
            for i, user_id in enumerate(query.participant_user_ids):
                param_name = f"@userId{i}"
                participant_conditions.append(f"ARRAY_CONTAINS(c.participants, {{'userId': {param_name}}}, true)")
                parameters.append({"name": param_name, "value": user_id})
            conditions.append(f"({' OR '.join(participant_conditions)})")
        
        # 参加者検索（表示名）
        if query.participant_names:
            name_conditions = []
            for i, name in enumerate(query.participant_names):
                param_name = f"@participantName{i}"
                name_conditions.append(f"ARRAY_CONTAINS(c.participants, {{'displayName': {param_name}}}, true)")
                parameters.append({"name": param_name, "value": name})
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        # カテゴリー検索（ID）
        if query.category_ids:
            category_conditions = []
            for i, cat_id in enumerate(query.category_ids):
                param_name = f"@categoryId{i}"
                category_conditions.append(f"ARRAY_CONTAINS(c.categories, {{'categoryId': {param_name}}}, true)")
                parameters.append({"name": param_name, "value": cat_id})
            conditions.append(f"({' OR '.join(category_conditions)})")
        
        # カテゴリー検索（名前）
        if query.category_names:
            category_name_conditions = []
            for i, cat_name in enumerate(query.category_names):
                param_name = f"@categoryName{i}"
                category_name_conditions.append(f"ARRAY_CONTAINS(c.categories, {{'categoryName': {param_name}}}, true)")
                parameters.append({"name": param_name, "value": cat_name})
            conditions.append(f"({' OR '.join(category_name_conditions)})")
        
        # タグ検索
        if query.tags:
            tag_conditions = []
            for i, tag in enumerate(query.tags):
                param_name = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
                parameters.append({"name": param_name, "value": tag})
            conditions.append(f"({' OR '.join(tag_conditions)})")
        
        # 日時範囲
        if query.date_range and query.date_range.is_valid():
            if query.date_range.start_date:
                conditions.append("c.timeline.lastMessageAt >= @startDate")
                parameters.append({"name": "@startDate", "value": query.date_range.start_date})
            
            if query.date_range.end_date:
                conditions.append("c.timeline.lastMessageAt <= @endDate")
                parameters.append({"name": "@endDate", "value": query.date_range.end_date})
        
        # アーカイブフィルター
        if not query.include_archived:
            conditions.append("(c.archived = false OR NOT IS_DEFINED(c.archived))")
        
        # 高信頼度カテゴリーのみ
        if query.high_confidence_only:
            conditions.append("EXISTS(SELECT VALUE cat FROM cat IN c.categories WHERE cat.confidence >= 0.8)")
        
        # WHERE句構築
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # ORDER BY句
        sort_field = "c.timeline.lastMessageAt"
        if query.sort_field == SearchSortField.CREATED_AT:
            sort_field = "c.timeline.createdAt"
        elif query.sort_field == SearchSortField.MESSAGE_COUNT:
            sort_field = "c.metrics.messageCount"
        elif query.sort_field == SearchSortField.TITLE:
            sort_field = "c.title"
        
        sort_order = "DESC" if query.sort_order == SearchSortOrder.DESC else "ASC"
        order_clause = f"ORDER BY {sort_field} {sort_order}"
        
        sql_query = f"SELECT * FROM conversations c {where_clause} {order_clause}"
        
        return sql_query, parameters
    
    # ==================== メッセージ検索 ====================
    
    async def search_messages(self, query: SearchQuery) -> SearchResult:
        """メッセージ検索"""
        start_time = time.time()
        
        try:
            # キャッシュ確認
            cache_key = self._generate_cache_key("messages", query)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # クエリ構築
            sql_query, parameters = self._build_messages_query(query)
            
            # 実行
            query_options = {
                "enable_cross_partition_query": True,
                "max_item_count": query.page_size
            }
            
            if query.continuation_token:
                query_options["continuation"] = query.continuation_token
            
            logger.debug(f"Executing message search: {sql_query}")
            
            result_iterator = self.messages_container.query_items(
                query=sql_query,
                parameters=parameters,
                **query_options
            )
            
            items = []
            continuation_token = None
            
            # 結果取得
            for item in result_iterator:
                items.append(ChatMessage.from_cosmos_dict(item))
            
            # 継続トークン取得
            try:
                if hasattr(result_iterator, 'response_headers'):
                    continuation_token = result_iterator.response_headers.get("x-ms-continuation")
            except:
                pass
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = SearchResult(
                items=items,
                continuation_token=continuation_token,
                has_more=bool(continuation_token),
                search_time_ms=search_time_ms,
                query_info={
                    "sql_query": sql_query,
                    "parameters": parameters,
                    "total_results": len(items)
                }
            )
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            
            logger.info(f"Message search completed: {len(items)} results in {search_time_ms:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Message search failed: {e}")
            raise Exception(f"メッセージ検索エラー: {str(e)}")
    
    def _build_messages_query(self, query: SearchQuery) -> Tuple[str, List[Dict[str, Any]]]:
        """メッセージ検索クエリ構築"""
        conditions = []
        parameters = []
        
        # テナントID
        if query.tenant_id:
            conditions.append("m.tenantId = @tenantId")
            parameters.append({"name": "@tenantId", "value": query.tenant_id})
        
        # キーワード検索（検索用テキスト）
        if query.keyword:
            conditions.append("CONTAINS(m.content.searchableText, @keyword)")
            parameters.append({"name": "@keyword", "value": query.keyword.lower()})
        
        # 送信者検索
        if query.participant_user_ids:
            sender_conditions = []
            for i, user_id in enumerate(query.participant_user_ids):
                param_name = f"@senderId{i}"
                sender_conditions.append(f"m.sender.userId = {param_name}")
                parameters.append({"name": param_name, "value": user_id})
            conditions.append(f"({' OR '.join(sender_conditions)})")
        
        # 送信者名検索
        if query.participant_names:
            name_conditions = []
            for i, name in enumerate(query.participant_names):
                param_name = f"@senderName{i}"
                name_conditions.append(f"CONTAINS(m.sender.displayName, {param_name})")
                parameters.append({"name": param_name, "value": name})
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        # ロールフィルター
        if query.sender_roles:
            role_conditions = []
            for i, role in enumerate(query.sender_roles):
                param_name = f"@role{i}"
                role_conditions.append(f"m.sender.role = {param_name}")
                parameters.append({"name": param_name, "value": role})
            conditions.append(f"({' OR '.join(role_conditions)})")
        
        # 日時範囲
        if query.date_range and query.date_range.is_valid():
            if query.date_range.start_date:
                conditions.append("m.timestamp >= @startDate")
                parameters.append({"name": "@startDate", "value": query.date_range.start_date})
            
            if query.date_range.end_date:
                conditions.append("m.timestamp <= @endDate")
                parameters.append({"name": "@endDate", "value": query.date_range.end_date})
        
        # トピック検索
        if query.tags:  # タグをトピックとして使用
            topic_conditions = []
            for i, topic in enumerate(query.tags):
                param_name = f"@topic{i}"
                topic_conditions.append(f"ARRAY_CONTAINS(m.metadata.topics, {param_name})")
                parameters.append({"name": param_name, "value": topic})
            conditions.append(f"({' OR '.join(topic_conditions)})")
        
        # WHERE句構築
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # ORDER BY句
        sort_field = "m.timestamp"
        if query.sort_field == SearchSortField.TIMESTAMP:
            sort_field = "m.timestamp"
        
        sort_order = "DESC" if query.sort_order == SearchSortOrder.DESC else "ASC"
        order_clause = f"ORDER BY {sort_field} {sort_order}"
        
        sql_query = f"SELECT * FROM messages m {where_clause} {order_clause}"
        
        return sql_query, parameters
    
    # ==================== 複合検索 ====================
    
    async def search_combined(self, query: SearchQuery) -> Dict[str, SearchResult]:
        """会話とメッセージの統合検索"""
        
        try:
            # 並行実行
            import asyncio
            
            conversation_task = asyncio.create_task(self.search_conversations(query))
            message_task = asyncio.create_task(self.search_messages(query))
            
            conversation_result, message_result = await asyncio.gather(
                conversation_task, message_task, return_exceptions=True
            )
            
            # エラーハンドリング
            if isinstance(conversation_result, Exception):
                logger.error(f"Conversation search failed: {conversation_result}")
                conversation_result = SearchResult(items=[])
            
            if isinstance(message_result, Exception):
                logger.error(f"Message search failed: {message_result}")
                message_result = SearchResult(items=[])
            
            return {
                "conversations": conversation_result,
                "messages": message_result,
                "combined_time_ms": max(
                    conversation_result.search_time_ms,
                    message_result.search_time_ms
                )
            }
            
        except Exception as e:
            logger.error(f"Combined search failed: {e}")
            return {
                "conversations": SearchResult(items=[]),
                "messages": SearchResult(items=[]),
                "error": str(e)
            }
    
    # ==================== 検索候補・統計 ====================
    
    async def get_search_suggestions(
        self,
        tenant_id: str,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """検索候補取得"""
        
        try:
            suggestions = []
            
            # 会話タイトルから候補
            if len(partial_query) >= 2:
                title_query = f"""
                    SELECT DISTINCT c.title 
                    FROM conversations c 
                    WHERE c.tenantId = @tenantId 
                    AND CONTAINS(c.title, @partial)
                    ORDER BY c.timeline.lastMessageAt DESC
                """
                
                parameters = [
                    {"name": "@tenantId", "value": tenant_id},
                    {"name": "@partial", "value": partial_query}
                ]
                
                items = list(self.conversations_container.query_items(
                    query=title_query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=limit
                ))
                
                suggestions.extend([item["title"] for item in items])
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.warning(f"Failed to get search suggestions: {e}")
            return []
    
    async def get_search_facets(self, tenant_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """検索ファセット（分類）取得"""
        
        try:
            facets = {
                "categories": [],
                "participants": [],
                "tags": []
            }
            
            # カテゴリーファセット
            category_query = f"""
                SELECT DISTINCT cat.categoryName, cat.categoryId
                FROM conversations c
                JOIN cat IN c.categories
                WHERE c.tenantId = @tenantId
                ORDER BY cat.categoryName
            """
            
            parameters = [{"name": "@tenantId", "value": tenant_id}]
            
            category_items = list(self.conversations_container.query_items(
                query=category_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            facets["categories"] = [
                {"name": item["categoryName"], "id": item["categoryId"]}
                for item in category_items
            ]
            
            # 参加者ファセット（簡易版）
            participant_query = f"""
                SELECT DISTINCT p.displayName, p.userId
                FROM conversations c
                JOIN p IN c.participants
                WHERE c.tenantId = @tenantId
                ORDER BY p.displayName
            """
            
            participant_items = list(self.conversations_container.query_items(
                query=participant_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            facets["participants"] = [
                {"name": item["displayName"], "id": item["userId"]}
                for item in participant_items
            ]
            
            return facets
            
        except Exception as e:
            logger.warning(f"Failed to get search facets: {e}")
            return {"categories": [], "participants": [], "tags": []}
    
    # ==================== キャッシュ管理 ====================
    
    def _generate_cache_key(self, collection: str, query: SearchQuery) -> str:
        """キャッシュキー生成"""
        import hashlib
        query_str = f"{collection}_{query.__dict__}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[SearchResult]:
        """キャッシュ結果取得"""
        if cache_key in self.query_cache:
            cached_item = self.query_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_item["result"]
            else:
                # 期限切れキャッシュ削除
                del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: SearchResult):
        """結果キャッシュ"""
        self.query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        # キャッシュサイズ制限（100件まで）
        if len(self.query_cache) > 100:
            # 最古のキャッシュを削除
            oldest_key = min(
                self.query_cache.keys(), 
                key=lambda k: self.query_cache[k]["timestamp"]
            )
            del self.query_cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key}")
    
    def clear_cache(self):
        """キャッシュクリア"""
        self.query_cache.clear()
        logger.info("Search cache cleared")


# ==================== ファクトリー関数 ====================

def create_search_service(cosmos_client) -> CosmosSearchService:
    """検索サービス作成"""
    return CosmosSearchService(
        cosmos_client.get_conversations_container(),
        cosmos_client.get_messages_container()
    )


# ==================== テスト関数 ====================

async def test_search_service():
    """検索サービステスト"""
    
    print("=== 検索サービステスト ===")
    
    try:
        from .cosmos_client import create_cosmos_client
        
        # クライアント作成
        cosmos_client = create_cosmos_client()
        search_service = create_search_service(cosmos_client)
        print("✅ 検索サービス初期化成功")
        
        # 基本検索テスト
        query = SearchQuery(
            tenant_id="test_tenant",
            keyword="テスト",
            page_size=5
        )
        
        result = await search_service.search_conversations(query)
        print(f"✅ 会話検索: {len(result.items)}件, {result.search_time_ms:.1f}ms")
        
        # メッセージ検索テスト
        message_result = await search_service.search_messages(query)
        print(f"✅ メッセージ検索: {len(message_result.items)}件, {message_result.search_time_ms:.1f}ms")
        
        # ファセット取得テスト
        facets = await search_service.get_search_facets("test_tenant")
        print(f"✅ ファセット取得: {len(facets.get('categories', []))}カテゴリー")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_service())