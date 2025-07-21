"""
Azure Cosmos DB クライアント管理

既存のAzure認証基盤と統合したCosmos DB接続管理
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
        self.api_key = os.getenv("COSMOS_DB_API_KEY")
        self.database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "chat_history_db")
        self.conversations_container = os.getenv("COSMOS_DB_CONVERSATIONS_CONTAINER", "conversations")
        self.messages_container = os.getenv("COSMOS_DB_MESSAGES_CONTAINER", "messages")
        
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
        
        # API KeyまたはAzure AD認証のどちらかが必要
        if not self.api_key and not os.getenv("AZURE_CLIENT_ID"):
            logger.warning("Neither API key nor Azure AD credentials configured")
        
        return True
    
    def display_config(self, masked: bool = True):
        """設定表示"""
        endpoint_display = self.endpoint
        if masked and endpoint_display:
            endpoint_display = f"{endpoint_display[:30]}...{endpoint_display[-10:]}"
        
        print(f"Cosmos DB設定:")
        print(f"  Endpoint: {endpoint_display}")
        print(f"  Database: {self.database_name}")
        print(f"  Conversations Container: {self.conversations_container}")
        print(f"  Messages Container: {self.messages_container}")
        print(f"  Throughput Mode: {self.throughput_mode}")
        print(f"  Cache Enabled: {self.enable_cache}")
        print(f"  API Key: {'設定済み' if self.api_key else '未設定'}")


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
        # 1. API Keyを優先
        if self.config.api_key:
            logger.info("Using API Key authentication")
            return self.config.api_key
        
        # 2. Azure認証基盤使用
        if self.auth_manager:
            logger.info("Using Azure Universal Auth authentication")
            auth_result = self.auth_manager.authenticate("cosmos_db")
            if not auth_result.success:
                raise Exception(f"Cosmos DB authentication failed: {auth_result.message}")
            return auth_result.credential
        
        # 3. デフォルト認証（環境変数・マネージドID）
        logger.info("Using DefaultAzureCredential authentication")
        return DefaultAzureCredential()
    
    def _initialize_database(self):
        """データベース初期化"""
        try:
            self.database = self.client.get_database_client(self.config.database_name)
            # データベース存在確認
            self.database.read()
            logger.info(f"Connected to existing database: {self.config.database_name}")
        except CosmosResourceNotFoundError:
            # データベース作成
            logger.info(f"Creating database: {self.config.database_name}")
            self.database = self.client.create_database(self.config.database_name)
    
    def _initialize_containers(self):
        """コンテナー初期化"""
        container_configs = [
            {
                "name": self.config.conversations_container,
                "partition_key": "/tenantId",
                "indexing_policy": self._get_conversations_indexing_policy()
            },
            {
                "name": self.config.messages_container,
                "partition_key": "/conversationId",
                "indexing_policy": self._get_messages_indexing_policy()
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
            logger.info(f"Connected to existing container: {container_name}")
            
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
    
    def _get_conversations_indexing_policy(self) -> Dict[str, Any]:
        """会話コンテナーのインデックスポリシー"""
        return {
            "indexingMode": "consistent",
            "includedPaths": [
                {"path": "/tenantId/?"},
                {"path": "/title/?"},
                {"path": "/summary/?"},
                {"path": "/participants/*/userId/?"},
                {"path": "/participants/*/displayName/?"},
                {"path": "/categories/*/categoryId/?"},
                {"path": "/categories/*/categoryName/?"},
                {"path": "/tags/*"},
                {"path": "/timeline/lastMessageAt/?"},
                {"path": "/timeline/createdAt/?"},
                {"path": "/searchableText/?"},
                {"path": "/status/?"},
                {"path": "/archived/?"}
            ],
            "excludedPaths": [
                {"path": "/metrics/*"},
                {"path": "/_etag/?"}
            ],
            "compositeIndexes": [
                [
                    {"path": "/tenantId", "order": "ascending"},
                    {"path": "/timeline/lastMessageAt", "order": "descending"}
                ],
                [
                    {"path": "/tenantId", "order": "ascending"},
                    {"path": "/participants/0/userId", "order": "ascending"},
                    {"path": "/timeline/lastMessageAt", "order": "descending"}
                ],
                [
                    {"path": "/tenantId", "order": "ascending"},
                    {"path": "/categories/0/categoryId", "order": "ascending"},
                    {"path": "/timeline/lastMessageAt", "order": "descending"}
                ]
            ]
        }
    
    def _get_messages_indexing_policy(self) -> Dict[str, Any]:
        """メッセージコンテナーのインデックスポリシー"""
        return {
            "indexingMode": "consistent",
            "includedPaths": [
                {"path": "/conversationId/?"},
                {"path": "/tenantId/?"},
                {"path": "/sender/userId/?"},
                {"path": "/sender/role/?"},
                {"path": "/timestamp/?"},
                {"path": "/content/searchableText/?"},
                {"path": "/metadata/mode/?"},
                {"path": "/metadata/topics/*"},
                {"path": "/sequenceNumber/?"}
            ],
            "excludedPaths": [
                {"path": "/content/originalText/?"},
                {"path": "/metadata/duration/?"},
                {"path": "/metadata/tokens/?"},
                {"path": "/metadata/extractedEntities/*"}
            ],
            "compositeIndexes": [
                [
                    {"path": "/conversationId", "order": "ascending"},
                    {"path": "/sequenceNumber", "order": "ascending"}
                ],
                [
                    {"path": "/conversationId", "order": "ascending"},
                    {"path": "/timestamp", "order": "ascending"}
                ],
                [
                    {"path": "/tenantId", "order": "ascending"},
                    {"path": "/timestamp", "order": "descending"}
                ]
            ]
        }
    
    def get_conversations_container(self) -> ContainerProxy:
        """会話コンテナー取得"""
        return self.containers[self.config.conversations_container]
    
    def get_messages_container(self) -> ContainerProxy:
        """メッセージコンテナー取得"""
        return self.containers[self.config.messages_container]
    
    def is_ready(self) -> bool:
        """クライアント準備状況確認"""
        return (
            self.client is not None and
            self.database is not None and
            len(self.containers) >= 2
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
                "throughput_mode": self.config.throughput_mode,
                "endpoint": self.config.endpoint[:50] + "..." if len(self.config.endpoint) > 50 else self.config.endpoint
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_container_stats(self) -> Dict[str, Any]:
        """コンテナー統計情報取得"""
        stats = {}
        
        for name, container in self.containers.items():
            try:
                # 簡易統計（サンプルクエリ）
                count_query = "SELECT VALUE COUNT(1) FROM c"
                items = list(container.query_items(
                    query=count_query,
                    enable_cross_partition_query=True
                ))
                
                stats[name] = {
                    "estimated_count": items[0] if items else 0,
                    "status": "active"
                }
                
            except Exception as e:
                stats[name] = {
                    "estimated_count": -1,
                    "status": f"error: {str(e)}"
                }
        
        return stats


def create_cosmos_client(auth_manager: Optional[AzureAuthManager] = None) -> CosmosDBClient:
    """Cosmos DBクライアント作成ヘルパー"""
    try:
        client = CosmosDBClient(auth_manager)
        if client.is_ready():
            return client
        else:
            raise Exception("Cosmos DB client initialization failed")
    except Exception as e:
        logger.error(f"Failed to create Cosmos DB client: {e}")
        raise


def test_cosmos_connection():
    """Cosmos DB接続テスト"""
    print("=== Cosmos DB接続テスト ===")
    
    try:
        # 設定表示
        config = CosmosDBConfig()
        config.display_config()
        
        if not config.validate():
            print("❌ 設定が無効です")
            return False
        
        # クライアント作成
        print("\n🔄 Cosmos DBクライアント初期化中...")
        client = create_cosmos_client()
        
        if client.is_ready():
            print("✅ Cosmos DBクライアント初期化成功")
            
            # ヘルスチェック
            health = client.health_check()
            print(f"✅ ヘルスチェック: {health}")
            
            # 統計情報
            stats = client.get_container_stats()
            print(f"📊 コンテナー統計: {stats}")
            
            return True
        else:
            print("❌ Cosmos DBクライアント初期化失敗")
            return False
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False


if __name__ == "__main__":
    test_cosmos_connection()