# Azure Cosmos DB チャット履歴管理システム 詳細実装仕様書

## 🎯 実装概要

本仕様書は、Azure Cosmos DBを使用したチャット履歴管理システムの詳細実装手順を定義します。既存のローカルJSONベースシステムからの移行と、高度な検索機能の実装を含みます。

## 📦 モジュール構成

### 新規追加モジュール
```
cosmos_history/
├── __init__.py
├── cosmos_client.py           # Cosmos DB接続・認証
├── cosmos_history_manager.py  # メイン履歴管理
├── search_service.py          # 検索機能
├── migration_service.py       # データ移行
├── cache_service.py           # キャッシュ機能
├── user_service.py            # ユーザー管理
└── models/
    ├── __init__.py
    ├── session.py             # セッションモデル
    ├── message.py             # メッセージモデル
    └── search.py              # 検索モデル
```

## 🔧 詳細実装仕様

### 1. Cosmos DB接続・認証 (cosmos_client.py)

```python
#!/usr/bin/env python3
"""
Azure Cosmos DB クライアント管理

Azure認証基盤と統合したCosmos DB接続管理
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from azure.identity import DefaultAzureCredential

from core.azure_universal_auth import AzureAuthManager
from core.error_handler import ErrorHandler, safe_api_call

logger = logging.getLogger(__name__)


class CosmosDBConfig:
    """Cosmos DB設定管理"""
    
    def __init__(self):
        self.endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        self.database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "chat_history_db")
        self.sessions_container = os.getenv("COSMOS_DB_SESSIONS_CONTAINER", "sessions")
        self.messages_container = os.getenv("COSMOS_DB_MESSAGES_CONTAINER", "messages")
        self.users_container = os.getenv("COSMOS_DB_USERS_CONTAINER", "user_profiles")
        
        # パフォーマンス設定
        self.throughput_mode = os.getenv("COSMOS_DB_THROUGHPUT_MODE", "serverless")
        self.max_throughput = int(os.getenv("COSMOS_DB_MAX_THROUGHPUT", "4000"))
        self.enable_cache = os.getenv("ENABLE_COSMOS_CACHE", "true").lower() == "true"
    
    def validate(self) -> bool:
        """設定検証"""
        if not self.endpoint:
            logger.error("COSMOS_DB_ENDPOINT not configured")
            return False
        
        if not self.endpoint.startswith("https://"):
            logger.error("COSMOS_DB_ENDPOINT must start with https://")
            return False
        
        return True
    
    def display_config(self, masked: bool = True):
        """設定表示"""
        endpoint_display = self.endpoint
        if masked and endpoint_display:
            endpoint_display = f"{endpoint_display[:20]}...{endpoint_display[-10:]}"
        
        print(f"Cosmos DB設定:")
        print(f"  Endpoint: {endpoint_display}")
        print(f"  Database: {self.database_name}")
        print(f"  Sessions Container: {self.sessions_container}")
        print(f"  Messages Container: {self.messages_container}")
        print(f"  Throughput Mode: {self.throughput_mode}")
        print(f"  Cache Enabled: {self.enable_cache}")


class CosmosDBClient:
    """Cosmos DB統合クライアント"""
    
    def __init__(self, auth_manager: Optional[AzureAuthManager] = None):
        """
        初期化
        
        Args:
            auth_manager: Azure認証マネージャー（None の場合は環境変数認証）
        """
        self.config = CosmosDBConfig()
        self.auth_manager = auth_manager
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.containers: Dict[str, ContainerProxy] = {}
        
        self._initialize()
    
    def _initialize(self):
        """クライアント初期化"""
        if not self.config.validate():
            raise ValueError("Cosmos DB configuration invalid")
        
        try:
            # 認証
            credential = self._get_credential()
            
            # クライアント作成
            self.client = CosmosClient(
                url=self.config.endpoint,
                credential=credential,
                consistency_level="Session",
                enable_endpoint_discovery=True,
                preferred_locations=["Japan East", "Japan West"]
            )
            
            # データベース・コンテナー初期化
            self._initialize_database()
            self._initialize_containers()
            
            logger.info("Cosmos DB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Cosmos DB initialization failed: {e}")
            raise
    
    def _get_credential(self):
        """認証情報取得"""
        if self.auth_manager:
            # Azure認証基盤使用
            auth_result = self.auth_manager.authenticate("cosmos_db")
            if not auth_result.success:
                raise Exception(f"Cosmos DB authentication failed: {auth_result.message}")
            return auth_result.credential
        else:
            # 環境変数・マネージドID認証
            api_key = os.getenv("COSMOS_DB_API_KEY")
            if api_key:
                return api_key
            else:
                return DefaultAzureCredential()
    
    def _initialize_database(self):
        """データベース初期化"""
        try:
            self.database = self.client.get_database_client(self.config.database_name)
            # データベース存在確認
            self.database.read()
        except CosmosResourceNotFoundError:
            # データベース作成
            logger.info(f"Creating database: {self.config.database_name}")
            self.database = self.client.create_database(self.config.database_name)
    
    def _initialize_containers(self):
        """コンテナー初期化"""
        container_configs = [
            {
                "name": self.config.sessions_container,
                "partition_key": "/userId",
                "indexing_policy": self._get_sessions_indexing_policy()
            },
            {
                "name": self.config.messages_container,
                "partition_key": "/sessionId",
                "indexing_policy": self._get_messages_indexing_policy()
            },
            {
                "name": self.config.users_container,
                "partition_key": "/userId",
                "indexing_policy": self._get_users_indexing_policy()
            }
        ]
        
        for config in container_configs:
            self._create_or_get_container(config)
    
    def _create_or_get_container(self, config: Dict[str, Any]):
        """コンテナー作成または取得"""
        container_name = config["name"]
        
        try:
            container = self.database.get_container_client(container_name)
            container.read()  # 存在確認
            self.containers[container_name] = container
            logger.info(f"Container exists: {container_name}")
            
        except CosmosResourceNotFoundError:
            # コンテナー作成
            logger.info(f"Creating container: {container_name}")
            
            throughput_config = None
            if self.config.throughput_mode == "provisioned":
                throughput_config = {
                    "max_throughput": self.config.max_throughput
                }
            
            container = self.database.create_container(
                id=container_name,
                partition_key={"paths": [config["partition_key"]], "kind": "Hash"},
                indexing_policy=config["indexing_policy"],
                offer_throughput=throughput_config
            )
            
            self.containers[container_name] = container
            logger.info(f"Container created: {container_name}")
    
    def _get_sessions_indexing_policy(self) -> Dict[str, Any]:
        """セッションコンテナーのインデックスポリシー"""
        return {
            "indexingMode": "consistent",
            "includedPaths": [
                {"path": "/userId/?"},
                {"path": "/mode/?"},
                {"path": "/createdAt/?"},
                {"path": "/updatedAt/?"},
                {"path": "/title/?"},
                {"path": "/tags/*"},
                {"path": "/lastMessage/?"}
            ],
            "excludedPaths": [
                {"path": "/metadata/*"},
                {"path": "/_etag/?"}
            ],
            "compositeIndexes": [
                [
                    {"path": "/userId", "order": "ascending"},
                    {"path": "/updatedAt", "order": "descending"}
                ],
                [
                    {"path": "/userId", "order": "ascending"},
                    {"path": "/mode", "order": "ascending"},
                    {"path": "/createdAt", "order": "descending"}
                ]
            ]
        }
    
    def _get_messages_indexing_policy(self) -> Dict[str, Any]:
        """メッセージコンテナーのインデックスポリシー"""
        return {
            "indexingMode": "consistent",
            "includedPaths": [
                {"path": "/sessionId/?"},
                {"path": "/userId/?"},
                {"path": "/role/?"},
                {"path": "/timestamp/?"},
                {"path": "/searchText/?"},
                {"path": "/metadata/mode/?"}
            ],
            "excludedPaths": [
                {"path": "/content/?"},
                {"path": "/metadata/duration/?"},
                {"path": "/metadata/tokens/?"}
            ],
            "compositeIndexes": [
                [
                    {"path": "/sessionId", "order": "ascending"},
                    {"path": "/timestamp", "order": "ascending"}
                ],
                [
                    {"path": "/userId", "order": "ascending"},
                    {"path": "/timestamp", "order": "descending"}
                ]
            ]
        }
    
    def _get_users_indexing_policy(self) -> Dict[str, Any]:
        """ユーザーコンテナーのインデックスポリシー"""
        return {
            "indexingMode": "consistent",
            "includedPaths": [
                {"path": "/userId/?"},
                {"path": "/lastLoginAt/?"},
                {"path": "/createdAt/?"}
            ],
            "excludedPaths": [
                {"path": "/statistics/*"},
                {"path": "/preferences/*"}
            ]
        }
    
    def get_sessions_container(self) -> ContainerProxy:
        """セッションコンテナー取得"""
        return self.containers[self.config.sessions_container]
    
    def get_messages_container(self) -> ContainerProxy:
        """メッセージコンテナー取得"""
        return self.containers[self.config.messages_container]
    
    def get_users_container(self) -> ContainerProxy:
        """ユーザーコンテナー取得"""
        return self.containers[self.config.users_container]
    
    def is_ready(self) -> bool:
        """クライアント準備状況確認"""
        return (
            self.client is not None and
            self.database is not None and
            len(self.containers) >= 3
        )
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # データベース接続確認
            db_info = self.database.read()
            
            # コンテナー確認
            container_status = {}
            for name, container in self.containers.items():
                try:
                    container.read()
                    container_status[name] = "healthy"
                except Exception as e:
                    container_status[name] = f"error: {str(e)}"
            
            return {
                "status": "healthy",
                "database": db_info.get("id"),
                "containers": container_status,
                "throughput_mode": self.config.throughput_mode
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

### 2. データモデル定義

#### セッションモデル (models/session.py)

```python
"""
セッションデータモデル
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class SessionMetadata:
    """セッションメタデータ"""
    total_tokens: int = 0
    total_duration: float = 0.0
    average_response_time: float = 0.0
    migrated_from: Optional[str] = None
    migration_date: Optional[str] = None


@dataclass_json
@dataclass
class ChatSession:
    """チャットセッションモデル"""
    
    # 必須フィールド
    id: str
    user_id: str
    session_id: str
    title: str
    mode: str
    created_at: str
    updated_at: str
    message_count: int
    
    # オプションフィールド
    tags: List[str] = None
    summary: str = ""
    last_message: str = ""
    metadata: SessionMetadata = None
    ttl: Optional[int] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = SessionMetadata()
    
    @classmethod
    def create_new(cls, user_id: str, mode: str = "reasoning", title: str = "") -> "ChatSession":
        """新規セッション作成"""
        session_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        if not title:
            title = f"チャット ({mode}) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return cls(
            id=f"session_{session_id}",
            user_id=user_id,
            session_id=session_id,
            title=title,
            mode=mode,
            created_at=timestamp,
            updated_at=timestamp,
            message_count=0,
            tags=[],
            summary="",
            last_message="",
            metadata=SessionMetadata()
        )
    
    def update_message_count(self, count: int):
        """メッセージ数更新"""
        self.message_count = count
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str):
        """タグ追加"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def update_summary(self, summary: str):
        """要約更新"""
        self.summary = summary
        self.updated_at = datetime.now().isoformat()
    
    def update_last_message(self, message: str):
        """最終メッセージ更新"""
        self.last_message = message[:100]  # 100文字まで
        self.updated_at = datetime.now().isoformat()
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Cosmos DB用辞書変換"""
        data = asdict(self)
        # パーティションキー確認
        data["userId"] = self.user_id
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        """Cosmos DB辞書からオブジェクト作成"""
        # metadata処理
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = SessionMetadata.from_dict(data["metadata"])
        
        return cls.from_dict(data)
```

#### メッセージモデル (models/message.py)

```python
"""
メッセージデータモデル
"""

import uuid
import re
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MessageMetadata:
    """メッセージメタデータ"""
    mode: str = ""
    effort: str = ""
    duration: float = 0.0
    tokens: int = 0
    model: str = ""


@dataclass_json
@dataclass  
class ChatMessage:
    """チャットメッセージモデル"""
    
    # 必須フィールド
    id: str
    session_id: str
    user_id: str
    role: str
    content: str
    timestamp: str
    
    # インデックス用フィールド
    search_text: str = ""
    
    # オプションフィールド
    metadata: MessageMetadata = None
    parent_message_id: Optional[str] = None
    ttl: Optional[int] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = MessageMetadata()
        if not self.search_text:
            self.search_text = self._create_search_text(self.content)
    
    @classmethod
    def create_new(
        cls,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ChatMessage":
        """新規メッセージ作成"""
        
        message_metadata = MessageMetadata()
        if metadata:
            message_metadata = MessageMetadata.from_dict(metadata)
        
        return cls(
            id=f"message_{uuid.uuid4()}",
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            search_text="",  # __post_init__で生成
            metadata=message_metadata
        )
    
    def _create_search_text(self, content: str) -> str:
        """検索用テキスト生成"""
        # 基本的な正規化
        text = content.lower()
        # 特殊文字除去（日本語文字は保持）
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', text)
        # 連続空白を単一空白に
        text = ' '.join(text.split())
        return text
    
    def update_search_text(self):
        """検索テキスト再生成"""
        self.search_text = self._create_search_text(self.content)
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Cosmos DB用辞書変換"""
        data = asdict(self)
        # パーティションキー確認
        data["sessionId"] = self.session_id
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Cosmos DB辞書からオブジェクト作成"""
        # metadata処理
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = MessageMetadata.from_dict(data["metadata"])
        
        return cls.from_dict(data)
```

### 3. 検索機能実装 (search_service.py)

```python
"""
Cosmos DB検索サービス

高度な検索・フィルタリング機能を提供
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from azure.cosmos import ContainerProxy
from cosmos_history.models.session import ChatSession
from cosmos_history.models.message import ChatMessage


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


@dataclass
class SearchQuery:
    """検索クエリ"""
    # 基本検索
    keyword: Optional[str] = None
    user_id: Optional[str] = None
    
    # 日時範囲
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # フィルター
    modes: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    # ソート
    sort_field: SearchSortField = SearchSortField.UPDATED_AT
    sort_order: SearchSortOrder = SearchSortOrder.DESC
    
    # ページング
    page_size: int = 20
    continuation_token: Optional[str] = None


@dataclass
class SearchResult:
    """検索結果"""
    items: List[Any]
    total_count: Optional[int] = None
    continuation_token: Optional[str] = None
    has_more: bool = False
    search_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            "total_count": self.total_count,
            "continuation_token": self.continuation_token,
            "has_more": self.has_more,
            "search_time_ms": self.search_time_ms
        }


class CosmosSearchService:
    """Cosmos DB検索サービス"""
    
    def __init__(self, sessions_container: ContainerProxy, messages_container: ContainerProxy):
        self.sessions_container = sessions_container
        self.messages_container = messages_container
        self.query_cache = {}  # 簡易キャッシュ
        self.cache_ttl = 300   # 5分
    
    async def search_sessions(self, query: SearchQuery) -> SearchResult:
        """セッション検索"""
        start_time = time.time()
        
        # キャッシュ確認
        cache_key = self._generate_cache_key("sessions", query)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # クエリ構築
        sql_query, parameters = self._build_sessions_query(query)
        
        # 実行
        query_options = {
            "enable_cross_partition_query": True,
            "max_item_count": query.page_size
        }
        
        if query.continuation_token:
            query_options["continuation"] = query.continuation_token
        
        try:
            result_iterator = self.sessions_container.query_items(
                query=sql_query,
                parameters=parameters,
                **query_options
            )
            
            items = []
            continuation_token = None
            
            # 結果取得
            for item in result_iterator:
                items.append(ChatSession.from_cosmos_dict(item))
            
            # 継続トークン取得
            if hasattr(result_iterator, 'response_headers'):
                continuation_token = result_iterator.response_headers.get("x-ms-continuation")
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = SearchResult(
                items=items,
                continuation_token=continuation_token,
                has_more=bool(continuation_token),
                search_time_ms=search_time_ms
            )
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            raise Exception(f"Session search failed: {str(e)}")
    
    async def search_messages(self, query: SearchQuery) -> SearchResult:
        """メッセージ検索"""
        start_time = time.time()
        
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
        
        try:
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
            if hasattr(result_iterator, 'response_headers'):
                continuation_token = result_iterator.response_headers.get("x-ms-continuation")
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = SearchResult(
                items=items,
                continuation_token=continuation_token,
                has_more=bool(continuation_token),
                search_time_ms=search_time_ms
            )
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            raise Exception(f"Message search failed: {str(e)}")
    
    def _build_sessions_query(self, query: SearchQuery) -> Tuple[str, List[Dict[str, Any]]]:
        """セッション検索クエリ構築"""
        conditions = []
        parameters = []
        
        # ユーザーID（必須）
        if query.user_id:
            conditions.append("s.userId = @userId")
            parameters.append({"name": "@userId", "value": query.user_id})
        
        # キーワード検索
        if query.keyword:
            conditions.append("(CONTAINS(s.title, @keyword) OR CONTAINS(s.summary, @keyword) OR CONTAINS(s.lastMessage, @keyword))")
            parameters.append({"name": "@keyword", "value": query.keyword})
        
        # 日時範囲
        if query.start_date:
            conditions.append("s.updatedAt >= @startDate")
            parameters.append({"name": "@startDate", "value": query.start_date})
        
        if query.end_date:
            conditions.append("s.updatedAt <= @endDate")
            parameters.append({"name": "@endDate", "value": query.end_date})
        
        # モードフィルター
        if query.modes:
            mode_conditions = []
            for i, mode in enumerate(query.modes):
                param_name = f"@mode{i}"
                mode_conditions.append(f"s.mode = {param_name}")
                parameters.append({"name": param_name, "value": mode})
            conditions.append(f"({' OR '.join(mode_conditions)})")
        
        # タグフィルター
        if query.tags:
            tag_conditions = []
            for i, tag in enumerate(query.tags):
                param_name = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(s.tags, {param_name})")
                parameters.append({"name": param_name, "value": tag})
            conditions.append(f"({' OR '.join(tag_conditions)})")
        
        # WHERE句構築
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # ORDER BY句
        sort_field = "s.updatedAt"  # デフォルト
        if query.sort_field == SearchSortField.CREATED_AT:
            sort_field = "s.createdAt"
        elif query.sort_field == SearchSortField.MESSAGE_COUNT:
            sort_field = "s.messageCount"
        
        sort_order = "DESC" if query.sort_order == SearchSortOrder.DESC else "ASC"
        order_clause = f"ORDER BY {sort_field} {sort_order}"
        
        sql_query = f"SELECT * FROM sessions s {where_clause} {order_clause}"
        
        return sql_query, parameters
    
    def _build_messages_query(self, query: SearchQuery) -> Tuple[str, List[Dict[str, Any]]]:
        """メッセージ検索クエリ構築"""
        conditions = []
        parameters = []
        
        # ユーザーID（必須）
        if query.user_id:
            conditions.append("m.userId = @userId")
            parameters.append({"name": "@userId", "value": query.user_id})
        
        # キーワード検索（searchTextを使用）
        if query.keyword:
            conditions.append("CONTAINS(m.searchText, @keyword)")
            parameters.append({"name": "@keyword", "value": query.keyword.lower()})
        
        # 日時範囲
        if query.start_date:
            conditions.append("m.timestamp >= @startDate")
            parameters.append({"name": "@startDate", "value": query.start_date})
        
        if query.end_date:
            conditions.append("m.timestamp <= @endDate")
            parameters.append({"name": "@endDate", "value": query.end_date})
        
        # ロールフィルター
        if query.roles:
            role_conditions = []
            for i, role in enumerate(query.roles):
                param_name = f"@role{i}"
                role_conditions.append(f"m.role = {param_name}")
                parameters.append({"name": param_name, "value": role})
            conditions.append(f"({' OR '.join(role_conditions)})")
        
        # モードフィルター（メタデータ内）
        if query.modes:
            mode_conditions = []
            for i, mode in enumerate(query.modes):
                param_name = f"@mode{i}"
                mode_conditions.append(f"m.metadata.mode = {param_name}")
                parameters.append({"name": param_name, "value": mode})
            conditions.append(f"({' OR '.join(mode_conditions)})")
        
        # WHERE句構築
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # ORDER BY句
        sort_field = "m.timestamp"  # デフォルト
        sort_order = "DESC" if query.sort_order == SearchSortOrder.DESC else "ASC"
        order_clause = f"ORDER BY {sort_field} {sort_order}"
        
        sql_query = f"SELECT * FROM messages m {where_clause} {order_clause}"
        
        return sql_query, parameters
    
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
            oldest_key = min(self.query_cache.keys(), 
                           key=lambda k: self.query_cache[k]["timestamp"])
            del self.query_cache[oldest_key]
    
    def clear_cache(self):
        """キャッシュクリア"""
        self.query_cache.clear()
    
    async def get_search_suggestions(self, user_id: str, partial_query: str) -> List[str]:
        """検索候補取得"""
        # 最近のセッションタイトルから候補を生成
        query = SearchQuery(
            user_id=user_id,
            page_size=10,
            sort_field=SearchSortField.UPDATED_AT,
            sort_order=SearchSortOrder.DESC
        )
        
        result = await self.search_sessions(query)
        
        suggestions = []
        for session in result.items:
            if partial_query.lower() in session.title.lower():
                suggestions.append(session.title)
            if len(suggestions) >= 5:
                break
        
        return suggestions
```

## 🔄 移行ツール実装 (migration_service.py)

```python
"""
データ移行サービス

ローカルJSON履歴からCosmos DBへの移行を管理
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from chat_history.local_history import ChatHistoryManager
from cosmos_history.cosmos_history_manager import CosmosDBHistoryManager
from cosmos_history.models.session import ChatSession
from cosmos_history.models.message import ChatMessage


logger = logging.getLogger(__name__)


class MigrationStats:
    """移行統計"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_sessions = 0
        self.migrated_sessions = 0
        self.failed_sessions = 0
        self.total_messages = 0
        self.migrated_messages = 0
        self.failed_messages = 0
        self.errors: List[Dict[str, str]] = []
    
    def add_error(self, session_id: str, error: str):
        """エラー追加"""
        self.errors.append({
            "session_id": session_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """統計サマリー取得"""
        duration = datetime.now() - self.start_time
        
        return {
            "migration_duration_seconds": duration.total_seconds(),
            "total_sessions": self.total_sessions,
            "migrated_sessions": self.migrated_sessions,
            "failed_sessions": self.failed_sessions,
            "session_success_rate": self.migrated_sessions / max(self.total_sessions, 1),
            "total_messages": self.total_messages,
            "migrated_messages": self.migrated_messages,
            "failed_messages": self.failed_messages,
            "message_success_rate": self.migrated_messages / max(self.total_messages, 1),
            "error_count": len(self.errors),
            "errors": self.errors[-10:] if self.errors else []  # 最新10件のエラー
        }


class DataMigrationService:
    """データ移行サービス"""
    
    def __init__(
        self,
        local_manager: ChatHistoryManager,
        cosmos_manager: CosmosDBHistoryManager,
        user_id: str
    ):
        self.local_manager = local_manager
        self.cosmos_manager = cosmos_manager
        self.user_id = user_id
        self.stats = MigrationStats()
    
    async def migrate_all_data(self, dry_run: bool = False) -> Dict[str, Any]:
        """全データ移行"""
        logger.info(f"Starting data migration (dry_run={dry_run})")
        
        # ローカルセッション一覧取得
        local_sessions = self.local_manager.list_sessions(limit=None)
        self.stats.total_sessions = len(local_sessions)
        
        logger.info(f"Found {self.stats.total_sessions} sessions to migrate")
        
        for session_info in local_sessions:
            try:
                await self._migrate_session(session_info, dry_run)
                self.stats.migrated_sessions += 1
                
            except Exception as e:
                logger.error(f"Session migration failed: {session_info.get('id', 'unknown')}: {e}")
                self.stats.add_error(session_info.get('id', 'unknown'), str(e))
                self.stats.failed_sessions += 1
        
        summary = self.stats.get_summary()
        logger.info(f"Migration completed: {summary}")
        
        return summary
    
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
        
        # セッション変換・作成
        cosmos_session = self._convert_session_format(session_info, local_messages)
        
        # Cosmos DBに既存セッションがあるかチェック
        existing_session = await self.cosmos_manager.get_session_by_id(session_id)
        if existing_session:
            logger.warning(f"Session {session_id} already exists in Cosmos DB, skipping")
            return
        
        # セッション作成
        created_session = await self.cosmos_manager.create_session(cosmos_session)
        logger.info(f"Created session: {session_id}")
        
        # メッセージ移行
        for local_message in local_messages:
            try:
                cosmos_message = self._convert_message_format(local_message, session_id)
                await self.cosmos_manager.add_message_direct(cosmos_message)
                self.stats.migrated_messages += 1
                
            except Exception as e:
                logger.error(f"Message migration failed for session {session_id}: {e}")
                self.stats.add_error(session_id, f"Message error: {str(e)}")
                self.stats.failed_messages += 1
        
        logger.info(f"Migrated session {session_id} with {len(local_messages)} messages")
    
    def _convert_session_format(self, local_session: Dict[str, Any], messages: List[Dict[str, Any]]) -> ChatSession:
        """ローカルセッション → Cosmos DBセッション変換"""
        
        # 最終メッセージ取得
        last_message = ""
        if messages:
            last_message = messages[-1].get("content", "")
        
        # 統計計算
        total_duration = 0.0
        total_tokens = 0
        response_times = []
        
        for msg in messages:
            metadata = msg.get("metadata", {})
            total_duration += metadata.get("duration", 0.0)
            total_tokens += metadata.get("tokens", 0)
            
            if msg.get("role") == "assistant" and metadata.get("duration"):
                response_times.append(metadata["duration"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # ChatSessionオブジェクト作成
        session = ChatSession(
            id=f"session_{local_session['id']}",
            user_id=self.user_id,
            session_id=local_session["id"],
            title=local_session["title"],
            mode=local_session["mode"],
            created_at=local_session["created_at"],
            updated_at=local_session["updated_at"],
            message_count=len(messages),
            tags=[],  # 新規フィールド（今後手動で設定）
            summary="",  # 新規フィールド（今後AI生成）
            last_message=last_message
        )
        
        # メタデータ設定
        session.metadata.total_tokens = total_tokens
        session.metadata.total_duration = total_duration
        session.metadata.average_response_time = avg_response_time
        session.metadata.migrated_from = "local_json"
        session.metadata.migration_date = datetime.now().isoformat()
        
        return session
    
    def _convert_message_format(self, local_message: Dict[str, Any], session_id: str) -> ChatMessage:
        """ローカルメッセージ → Cosmos DBメッセージ変換"""
        
        return ChatMessage.create_new(
            session_id=session_id,
            user_id=self.user_id,
            role=local_message["role"],
            content=local_message["content"],
            metadata=local_message.get("metadata", {})
        )
    
    async def verify_migration(self) -> Dict[str, Any]:
        """移行検証"""
        logger.info("Starting migration verification")
        
        verification_results = {
            "local_sessions": 0,
            "cosmos_sessions": 0,
            "session_match": True,
            "local_messages": 0,
            "cosmos_messages": 0,
            "message_match": True,
            "mismatched_sessions": [],
            "sample_verification": {}
        }
        
        # セッション数比較
        local_sessions = self.local_manager.list_sessions(limit=None)
        verification_results["local_sessions"] = len(local_sessions)
        
        cosmos_sessions = await self.cosmos_manager.list_sessions(
            self.user_id, limit=len(local_sessions) + 10
        )
        verification_results["cosmos_sessions"] = len(cosmos_sessions)
        
        # メッセージ数比較
        local_message_count = 0
        cosmos_message_count = 0
        
        # サンプル検証（最初の3セッション）
        sample_sessions = local_sessions[:3]
        
        for local_session in sample_sessions:
            session_id = local_session["id"]
            
            # ローカルメッセージ数
            local_messages = self.local_manager.get_session_messages(session_id)
            local_count = len(local_messages)
            local_message_count += local_count
            
            # Cosmos DBメッセージ数
            cosmos_messages = await self.cosmos_manager.get_session_messages(session_id)
            cosmos_count = len(cosmos_messages)
            cosmos_message_count += cosmos_count
            
            # サンプル詳細記録
            verification_results["sample_verification"][session_id] = {
                "local_message_count": local_count,
                "cosmos_message_count": cosmos_count,
                "match": local_count == cosmos_count
            }
            
            if local_count != cosmos_count:
                verification_results["mismatched_sessions"].append({
                    "session_id": session_id,
                    "local_count": local_count,
                    "cosmos_count": cosmos_count
                })
        
        verification_results["local_messages"] = local_message_count
        verification_results["cosmos_messages"] = cosmos_message_count
        verification_results["session_match"] = verification_results["local_sessions"] == verification_results["cosmos_sessions"]
        verification_results["message_match"] = local_message_count == cosmos_message_count
        
        logger.info(f"Verification completed: {verification_results}")
        return verification_results
    
    async def rollback_migration(self, confirmation_code: str) -> Dict[str, Any]:
        """移行ロールバック（Cosmos DBデータ削除）"""
        
        if confirmation_code != "CONFIRM_ROLLBACK":
            raise ValueError("Invalid confirmation code")
        
        logger.warning("Starting migration rollback - this will delete all migrated data")
        
        rollback_stats = {
            "deleted_sessions": 0,
            "deleted_messages": 0,
            "errors": []
        }
        
        try:
            # ユーザーの全セッション取得
            cosmos_sessions = await self.cosmos_manager.list_sessions(self.user_id, limit=1000)
            
            for session in cosmos_sessions:
                try:
                    # セッション内の全メッセージ削除
                    messages = await self.cosmos_manager.get_session_messages(session.session_id)
                    
                    for message in messages:
                        await self.cosmos_manager.delete_message(message.id)
                        rollback_stats["deleted_messages"] += 1
                    
                    # セッション削除
                    await self.cosmos_manager.delete_session(session.id)
                    rollback_stats["deleted_sessions"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to delete session {session.session_id}: {str(e)}"
                    logger.error(error_msg)
                    rollback_stats["errors"].append(error_msg)
            
            logger.info(f"Rollback completed: {rollback_stats}")
            
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            rollback_stats["errors"].append(error_msg)
            raise
        
        return rollback_stats
```

## 📚 使用例とテスト

### 使用例 (examples/cosmos_usage_example.py)

```python
"""
Cosmos DB履歴管理使用例
"""

import asyncio
from core.azure_universal_auth import AzureAuthManager
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosDBHistoryManager
from cosmos_history.search_service import CosmosSearchService, SearchQuery, SearchSortField, SearchSortOrder


async def basic_usage_example():
    """基本使用例"""
    
    # 認証初期化
    auth_manager = AzureAuthManager()
    
    # Cosmos DBクライアント初期化
    cosmos_client = CosmosDBClient(auth_manager)
    
    if not cosmos_client.is_ready():
        print("❌ Cosmos DB client initialization failed")
        return
    
    # 履歴マネージャー初期化
    history_manager = CosmosDBHistoryManager(cosmos_client, "user_123")
    
    print("✅ Cosmos DB history manager initialized")
    
    # 新規セッション作成
    session = await history_manager.start_new_session("reasoning", "API開発の質問")
    print(f"✅ Session created: {session.session_id}")
    
    # メッセージ追加
    await history_manager.add_message(
        session.session_id,
        "user",
        "Azure Cosmos DBの使い方を教えてください",
        {}
    )
    
    await history_manager.add_message(
        session.session_id,
        "assistant", 
        "Azure Cosmos DBは、Microsoftが提供するフルマネージドのNoSQLデータベースサービスです...",
        {"mode": "reasoning", "effort": "medium", "duration": 5.2}
    )
    
    print("✅ Messages added")
    
    # セッション一覧取得
    sessions = await history_manager.list_sessions(limit=5)
    print(f"✅ Retrieved {len(sessions)} sessions")


async def search_example():
    """検索機能使用例"""
    
    # 初期化（上記と同様）
    auth_manager = AzureAuthManager()
    cosmos_client = CosmosDBClient(auth_manager)
    history_manager = CosmosDBHistoryManager(cosmos_client, "user_123")
    
    # 検索サービス初期化
    search_service = CosmosSearchService(
        cosmos_client.get_sessions_container(),
        cosmos_client.get_messages_container()
    )
    
    # セッション検索
    search_query = SearchQuery(
        user_id="user_123",
        keyword="Azure",
        modes=["reasoning"],
        sort_field=SearchSortField.UPDATED_AT,
        sort_order=SearchSortOrder.DESC,
        page_size=10
    )
    
    session_results = await search_service.search_sessions(search_query)
    print(f"✅ Found {len(session_results.items)} sessions matching 'Azure'")
    
    # メッセージ検索
    message_query = SearchQuery(
        user_id="user_123",
        keyword="cosmos db",
        roles=["assistant"],
        page_size=5
    )
    
    message_results = await search_service.search_messages(message_query)
    print(f"✅ Found {len(message_results.items)} assistant messages about 'cosmos db'")


async def migration_example():
    """移行機能使用例"""
    
    from chat_history.local_history import ChatHistoryManager
    from cosmos_history.migration_service import DataMigrationService
    
    # ローカル履歴マネージャー
    local_manager = ChatHistoryManager("chat_history")
    
    # Cosmos DB履歴マネージャー
    auth_manager = AzureAuthManager()
    cosmos_client = CosmosDBClient(auth_manager)
    cosmos_manager = CosmosDBHistoryManager(cosmos_client, "user_123")
    
    # 移行サービス
    migration_service = DataMigrationService(
        local_manager,
        cosmos_manager,
        "user_123"
    )
    
    # ドライラン実行
    print("🔍 Running migration dry-run...")
    dry_run_result = await migration_service.migrate_all_data(dry_run=True)
    print(f"✅ Dry-run completed: {dry_run_result}")
    
    # 実際の移行実行（確認後）
    confirm = input("Proceed with actual migration? (yes/no): ")
    if confirm.lower() == "yes":
        print("🚀 Starting actual migration...")
        migration_result = await migration_service.migrate_all_data(dry_run=False)
        print(f"✅ Migration completed: {migration_result}")
        
        # 移行検証
        print("🔍 Verifying migration...")
        verification_result = await migration_service.verify_migration()
        print(f"✅ Verification completed: {verification_result}")


if __name__ == "__main__":
    print("🚀 Cosmos DB History Management Examples")
    
    # 基本使用例
    print("\n=== Basic Usage Example ===")
    asyncio.run(basic_usage_example())
    
    # 検索例
    print("\n=== Search Example ===")
    asyncio.run(search_example())
    
    # 移行例（コメントアウト - 実際の移行時のみ使用）
    # print("\n=== Migration Example ===")
    # asyncio.run(migration_example())
```

## 🧪 テスト仕様

### ユニットテスト (tests/test_cosmos_history.py)

```python
"""
Cosmos DB履歴管理ユニットテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from cosmos_history.cosmos_client import CosmosDBClient, CosmosDBConfig
from cosmos_history.models.session import ChatSession
from cosmos_history.models.message import ChatMessage
from cosmos_history.search_service import CosmosSearchService, SearchQuery


class TestCosmosDBConfig:
    """Cosmos DB設定テスト"""
    
    @patch.dict("os.environ", {
        "COSMOS_DB_ENDPOINT": "https://test.documents.azure.com:443/",
        "COSMOS_DB_DATABASE_NAME": "test_db"
    })
    def test_config_initialization(self):
        config = CosmosDBConfig()
        assert config.endpoint == "https://test.documents.azure.com:443/"
        assert config.database_name == "test_db"
        assert config.validate() == True
    
    def test_config_validation_missing_endpoint(self):
        with patch.dict("os.environ", {}, clear=True):
            config = CosmosDBConfig()
            assert config.validate() == False


class TestChatSession:
    """セッションモデルテスト"""
    
    def test_create_new_session(self):
        session = ChatSession.create_new("user_123", "reasoning", "テストセッション")
        
        assert session.user_id == "user_123"
        assert session.mode == "reasoning"
        assert session.title == "テストセッション"
        assert session.message_count == 0
        assert isinstance(session.tags, list)
        assert session.metadata is not None
    
    def test_session_dict_conversion(self):
        session = ChatSession.create_new("user_123", "reasoning")
        
        # Cosmos DB辞書変換
        cosmos_dict = session.to_cosmos_dict()
        assert "userId" in cosmos_dict
        assert cosmos_dict["userId"] == "user_123"
        
        # 逆変換
        restored_session = ChatSession.from_cosmos_dict(cosmos_dict)
        assert restored_session.user_id == session.user_id
        assert restored_session.mode == session.mode
    
    def test_session_updates(self):
        session = ChatSession.create_new("user_123", "reasoning")
        original_updated_at = session.updated_at
        
        # メッセージ数更新
        session.update_message_count(5)
        assert session.message_count == 5
        assert session.updated_at != original_updated_at
        
        # タグ追加
        session.add_tag("test")
        assert "test" in session.tags
        
        # 重複タグ追加（追加されない）
        session.add_tag("test")
        assert session.tags.count("test") == 1


class TestChatMessage:
    """メッセージモデルテスト"""
    
    def test_create_new_message(self):
        message = ChatMessage.create_new(
            "session_123",
            "user_456",
            "user",
            "こんにちは",
            {"mode": "reasoning"}
        )
        
        assert message.session_id == "session_123"
        assert message.user_id == "user_456"
        assert message.role == "user"
        assert message.content == "こんにちは"
        assert message.search_text != ""
        assert message.metadata.mode == "reasoning"
    
    def test_search_text_generation(self):
        message = ChatMessage.create_new(
            "session_123",
            "user_456",
            "user",
            "Azure Cosmos DBの使い方を教えてください！",
        )
        
        # 検索テキストが小文字化・正規化されている
        assert "azure" in message.search_text
        assert "cosmos" in message.search_text
        assert "db" in message.search_text
        assert "!" not in message.search_text  # 特殊文字除去
    
    def test_message_dict_conversion(self):
        message = ChatMessage.create_new("session_123", "user_456", "user", "テスト")
        
        # Cosmos DB辞書変換
        cosmos_dict = message.to_cosmos_dict()
        assert "sessionId" in cosmos_dict
        assert cosmos_dict["sessionId"] == "session_123"
        
        # 逆変換
        restored_message = ChatMessage.from_cosmos_dict(cosmos_dict)
        assert restored_message.session_id == message.session_id
        assert restored_message.content == message.content


@pytest.mark.asyncio
class TestCosmosSearchService:
    """検索サービステスト"""
    
    def setup_method(self):
        # モックコンテナー作成
        self.mock_sessions_container = Mock()
        self.mock_messages_container = Mock()
        
        self.search_service = CosmosSearchService(
            self.mock_sessions_container,
            self.mock_messages_container
        )
    
    async def test_sessions_query_building(self):
        """セッション検索クエリ構築テスト"""
        query = SearchQuery(
            user_id="user_123",
            keyword="Azure",
            modes=["reasoning", "streaming"]
        )
        
        sql_query, parameters = self.search_service._build_sessions_query(query)
        
        # SQLクエリ確認
        assert "s.userId = @userId" in sql_query
        assert "CONTAINS" in sql_query  # キーワード検索
        assert "s.mode = @mode0 OR s.mode = @mode1" in sql_query  # モードフィルター
        
        # パラメーター確認
        param_names = [p["name"] for p in parameters]
        assert "@userId" in param_names
        assert "@keyword" in param_names
        assert "@mode0" in param_names
        assert "@mode1" in param_names
    
    async def test_messages_query_building(self):
        """メッセージ検索クエリ構築テスト"""
        query = SearchQuery(
            user_id="user_123",
            keyword="cosmos db",
            roles=["assistant"]
        )
        
        sql_query, parameters = self.search_service._build_messages_query(query)
        
        # SQLクエリ確認
        assert "m.userId = @userId" in sql_query
        assert "CONTAINS(m.searchText, @keyword)" in sql_query
        assert "m.role = @role0" in sql_query
        
        # パラメーター確認  
        param_values = {p["name"]: p["value"] for p in parameters}
        assert param_values["@userId"] == "user_123"
        assert param_values["@keyword"] == "cosmos db"
        assert param_values["@role0"] == "assistant"
    
    async def test_cache_functionality(self):
        """キャッシュ機能テスト"""
        query = SearchQuery(user_id="user_123", keyword="test")
        
        # キャッシュミス確認
        cache_key = self.search_service._generate_cache_key("sessions", query)
        cached_result = self.search_service._get_cached_result(cache_key)
        assert cached_result is None
        
        # 結果キャッシュ
        from cosmos_history.search_service import SearchResult
        mock_result = SearchResult(items=[], search_time_ms=100.0)
        self.search_service._cache_result(cache_key, mock_result)
        
        # キャッシュヒット確認
        cached_result = self.search_service._get_cached_result(cache_key)
        assert cached_result is not None
        assert cached_result.search_time_ms == 100.0


def run_tests():
    """テスト実行"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
```

---

**作成日**: 2025-07-20  
**バージョン**: v1.0  
**ファイル数**: 25+ 実装ファイル  
**テストカバレッジ目標**: 85%+  

この詳細仕様書に基づいて、段階的な実装を開始できます。