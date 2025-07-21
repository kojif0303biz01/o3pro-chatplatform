"""
統合設定管理

環境変数からの設定読み込みと検証を統合管理
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ThroughputMode(Enum):
    """スループットモード"""
    SERVERLESS = "serverless"
    PROVISIONED = "provisioned"


class AuthMethod(Enum):
    """認証方式"""
    AUTO = "auto"
    API_KEY = "apikey"
    AZURE_AD = "azuread"
    CLI = "cli"
    MSI = "msi"


class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class CosmosDBSettings:
    """Cosmos DB設定"""
    # 接続設定
    endpoint: str
    api_key: Optional[str] = None
    database_name: str = "chat_history_db"
    conversations_container: str = "conversations"
    messages_container: str = "messages"
    
    # パフォーマンス設定
    throughput_mode: ThroughputMode = ThroughputMode.SERVERLESS
    max_throughput: int = 4000
    enable_cache: bool = True
    
    def validate(self) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []
        
        if not self.endpoint:
            errors.append("COSMOS_DB_ENDPOINT is required")
        elif not self.endpoint.startswith("https://"):
            errors.append("COSMOS_DB_ENDPOINT must start with https://")
        
        if not self.database_name:
            errors.append("Database name cannot be empty")
        
        if not self.conversations_container:
            errors.append("Conversations container name cannot be empty")
        
        if not self.messages_container:
            errors.append("Messages container name cannot be empty")
        
        if self.max_throughput < 400 or self.max_throughput > 1000000:
            errors.append("Max throughput must be between 400 and 1,000,000")
        
        return len(errors) == 0, errors


@dataclass
class AzureAuthSettings:
    """Azure認証設定"""
    # Service Principal設定
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    subscription_id: Optional[str] = None
    
    # 認証方式設定
    auth_method: AuthMethod = AuthMethod.AUTO
    prefer_cli: bool = False
    
    def has_service_principal(self) -> bool:
        """Service Principal認証情報があるかどうか"""
        return bool(self.client_id and self.client_secret and self.tenant_id)
    
    def validate(self) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []
        
        if self.auth_method == AuthMethod.AZURE_AD and not self.has_service_principal():
            errors.append("Azure AD authentication requires client_id, client_secret, and tenant_id")
        
        return len(errors) == 0, errors


@dataclass
class ChatHistorySettings:
    """チャット履歴設定"""
    # ディレクトリ設定
    local_history_dir: str = "chat_history"
    
    # デフォルト設定
    default_tenant_id: str = "default_tenant"
    default_user_id: str = "default_user"
    
    # 保持設定
    retention_days: int = 365
    max_messages_per_conversation: int = 1000
    enable_message_search: bool = True
    
    # TTL設定
    enable_ttl: bool = True
    conversation_ttl_seconds: int = -1  # -1 = 永続保存
    message_ttl_seconds: int = -1       # -1 = 永続保存
    development_ttl_seconds: int = -1   # 開発環境用
    
    def validate(self) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []
        
        if self.retention_days < 1:
            errors.append("Retention days must be positive")
        
        if self.max_messages_per_conversation < 1:
            errors.append("Max messages per conversation must be positive")
        
        if not self.default_tenant_id:
            errors.append("Default tenant ID cannot be empty")
        
        if not self.default_user_id:
            errors.append("Default user ID cannot be empty")
        
        return len(errors) == 0, errors
    
    def get_conversation_ttl(self, development_mode: bool = False) -> int:
        """会話のTTL値取得"""
        if not self.enable_ttl:
            return -1
        
        if development_mode:
            return self.development_ttl_seconds
        
        return self.conversation_ttl_seconds
    
    def get_message_ttl(self, development_mode: bool = False) -> int:
        """メッセージのTTL値取得"""
        if not self.enable_ttl:
            return -1
        
        if development_mode:
            return self.development_ttl_seconds
        
        return self.message_ttl_seconds


@dataclass
class MigrationSettings:
    """移行設定"""
    batch_size: int = 100
    dry_run_default: bool = True
    backup_enabled: bool = True
    verification_enabled: bool = True
    
    def validate(self) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []
        
        if self.batch_size < 1 or self.batch_size > 1000:
            errors.append("Batch size must be between 1 and 1000")
        
        return len(errors) == 0, errors


@dataclass
class LoggingSettings:
    """ログ設定"""
    log_level: LogLevel = LogLevel.INFO
    cosmos_log_level: LogLevel = LogLevel.WARNING
    azure_sdk_log_level: LogLevel = LogLevel.WARNING
    
    debug_mode: bool = False
    enable_detailed_logging: bool = False
    log_azure_requests: bool = False
    
    def apply_logging_config(self):
        """ログ設定適用"""
        # ルートロガー設定
        logging.basicConfig(
            level=getattr(logging, self.log_level.value),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Cosmos DBログレベル設定
        cosmos_logger = logging.getLogger('azure.cosmos')
        cosmos_logger.setLevel(getattr(logging, self.cosmos_log_level.value))
        
        # Azure SDKログレベル設定
        azure_logger = logging.getLogger('azure')
        azure_logger.setLevel(getattr(logging, self.azure_sdk_log_level.value))
        
        # HTTPトラフィックログ設定
        if self.log_azure_requests:
            http_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
            http_logger.setLevel(logging.DEBUG)


@dataclass
class PerformanceSettings:
    """パフォーマンス設定"""
    # 検索・キャッシュ設定
    search_cache_ttl_seconds: int = 300
    search_max_cache_size: int = 100
    search_default_page_size: int = 20
    search_max_page_size: int = 100
    
    # API制限設定
    api_rate_limit_enabled: bool = False
    api_max_requests_per_minute: int = 60
    
    def validate(self) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []
        
        if self.search_cache_ttl_seconds < 0:
            errors.append("Search cache TTL must be non-negative")
        
        if self.search_max_cache_size < 0:
            errors.append("Search max cache size must be non-negative")
        
        if self.search_default_page_size < 1 or self.search_default_page_size > 1000:
            errors.append("Search default page size must be between 1 and 1000")
        
        if self.search_max_page_size < self.search_default_page_size:
            errors.append("Search max page size must be >= default page size")
        
        if self.api_max_requests_per_minute < 1:
            errors.append("API max requests per minute must be positive")
        
        return len(errors) == 0, errors


@dataclass
class DevelopmentSettings:
    """開発・テスト設定"""
    development_mode: bool = False
    enable_test_data: bool = False
    mock_cosmos_db: bool = False
    
    # テスト設定
    test_tenant_id: str = "test_tenant"
    test_user_id: str = "test_user"
    test_database_name: str = "test_chat_history_db"


@dataclass
class AppConfig:
    """統合アプリケーション設定"""
    cosmos_db: CosmosDBSettings
    azure_auth: AzureAuthSettings
    chat_history: ChatHistorySettings
    migration: MigrationSettings
    logging: LoggingSettings
    performance: PerformanceSettings
    development: DevelopmentSettings
    
    def validate_all(self) -> tuple[bool, Dict[str, List[str]]]:
        """全設定検証"""
        all_errors = {}
        all_valid = True
        
        settings_map = {
            "cosmos_db": self.cosmos_db,
            "azure_auth": self.azure_auth,
            "chat_history": self.chat_history,
            "migration": self.migration,
            "performance": self.performance
        }
        
        for name, settings in settings_map.items():
            valid, errors = settings.validate()
            if not valid:
                all_errors[name] = errors
                all_valid = False
        
        return all_valid, all_errors
    
    def apply_logging(self):
        """ログ設定適用"""
        self.logging.apply_logging_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書変換"""
        def convert_to_serializable(obj):
            """JSON serializable形式に変換"""
            if hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    if hasattr(value, 'value'):  # Enum
                        result[key] = value.value
                    else:
                        result[key] = value
                return result
            return obj
        
        return {
            "cosmos_db": convert_to_serializable(self.cosmos_db),
            "azure_auth": convert_to_serializable(self.azure_auth),
            "chat_history": convert_to_serializable(self.chat_history),
            "migration": convert_to_serializable(self.migration),
            "logging": convert_to_serializable(self.logging),
            "performance": convert_to_serializable(self.performance),
            "development": convert_to_serializable(self.development)
        }


def load_config_from_env() -> AppConfig:
    """環境変数から設定読み込み"""
    
    # Cosmos DB設定
    cosmos_db = CosmosDBSettings(
        endpoint=os.getenv("COSMOS_DB_ENDPOINT", ""),
        api_key=os.getenv("COSMOS_DB_API_KEY"),
        database_name=os.getenv("COSMOS_DB_DATABASE_NAME", "chat_history_db"),
        conversations_container=os.getenv("COSMOS_DB_CONVERSATIONS_CONTAINER", "conversations"),
        messages_container=os.getenv("COSMOS_DB_MESSAGES_CONTAINER", "messages"),
        throughput_mode=ThroughputMode(os.getenv("COSMOS_DB_THROUGHPUT_MODE", "serverless")),
        max_throughput=int(os.getenv("COSMOS_DB_MAX_THROUGHPUT", "4000")),
        enable_cache=os.getenv("ENABLE_COSMOS_CACHE", "true").lower() == "true"
    )
    
    # Azure認証設定
    azure_auth = AzureAuthSettings(
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
        auth_method=AuthMethod(os.getenv("AZURE_AUTH_METHOD", "auto")),
        prefer_cli=os.getenv("AZURE_PREFER_CLI", "false").lower() == "true"
    )
    
    # チャット履歴設定
    chat_history = ChatHistorySettings(
        local_history_dir=os.getenv("LOCAL_CHAT_HISTORY_DIR", "chat_history"),
        default_tenant_id=os.getenv("DEFAULT_TENANT_ID", "default_tenant"),
        default_user_id=os.getenv("DEFAULT_USER_ID", "default_user"),
        retention_days=int(os.getenv("CHAT_HISTORY_RETENTION_DAYS", "365")),
        max_messages_per_conversation=int(os.getenv("MAX_MESSAGES_PER_CONVERSATION", "1000")),
        enable_message_search=os.getenv("ENABLE_MESSAGE_SEARCH", "true").lower() == "true",
        # TTL設定
        enable_ttl=os.getenv("ENABLE_TTL", "true").lower() == "true",
        conversation_ttl_seconds=int(os.getenv("CONVERSATION_TTL_SECONDS", "-1")),
        message_ttl_seconds=int(os.getenv("MESSAGE_TTL_SECONDS", "-1")),
        development_ttl_seconds=int(os.getenv("DEVELOPMENT_TTL_SECONDS", "-1"))
    )
    
    # 移行設定
    migration = MigrationSettings(
        batch_size=int(os.getenv("MIGRATION_BATCH_SIZE", "100")),
        dry_run_default=os.getenv("MIGRATION_DRY_RUN_DEFAULT", "true").lower() == "true",
        backup_enabled=os.getenv("MIGRATION_BACKUP_ENABLED", "true").lower() == "true",
        verification_enabled=os.getenv("MIGRATION_VERIFICATION_ENABLED", "true").lower() == "true"
    )
    
    # ログ設定
    logging_settings = LoggingSettings(
        log_level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
        cosmos_log_level=LogLevel(os.getenv("COSMOS_LOG_LEVEL", "WARNING")),
        azure_sdk_log_level=LogLevel(os.getenv("AZURE_SDK_LOG_LEVEL", "WARNING")),
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
        enable_detailed_logging=os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true",
        log_azure_requests=os.getenv("LOG_AZURE_REQUESTS", "false").lower() == "true"
    )
    
    # パフォーマンス設定
    performance = PerformanceSettings(
        search_cache_ttl_seconds=int(os.getenv("SEARCH_CACHE_TTL_SECONDS", "300")),
        search_max_cache_size=int(os.getenv("SEARCH_MAX_CACHE_SIZE", "100")),
        search_default_page_size=int(os.getenv("SEARCH_DEFAULT_PAGE_SIZE", "20")),
        search_max_page_size=int(os.getenv("SEARCH_MAX_PAGE_SIZE", "100")),
        api_rate_limit_enabled=os.getenv("API_RATE_LIMIT_ENABLED", "false").lower() == "true",
        api_max_requests_per_minute=int(os.getenv("API_MAX_REQUESTS_PER_MINUTE", "60"))
    )
    
    # 開発設定
    development = DevelopmentSettings(
        development_mode=os.getenv("DEVELOPMENT_MODE", "false").lower() == "true",
        enable_test_data=os.getenv("ENABLE_TEST_DATA", "false").lower() == "true",
        mock_cosmos_db=os.getenv("MOCK_COSMOS_DB", "false").lower() == "true",
        test_tenant_id=os.getenv("TEST_TENANT_ID", "test_tenant"),
        test_user_id=os.getenv("TEST_USER_ID", "test_user"),
        test_database_name=os.getenv("TEST_DATABASE_NAME", "test_chat_history_db")
    )
    
    return AppConfig(
        cosmos_db=cosmos_db,
        azure_auth=azure_auth,
        chat_history=chat_history,
        migration=migration,
        logging=logging_settings,
        performance=performance,
        development=development
    )


def validate_config(config: AppConfig) -> None:
    """設定検証（エラー時は例外発生）"""
    valid, errors = config.validate_all()
    
    if not valid:
        error_msg = "Configuration validation failed:\n"
        for section, section_errors in errors.items():
            error_msg += f"\n{section}:\n"
            for error in section_errors:
                error_msg += f"  - {error}\n"
        
        raise ValueError(error_msg)


# グローバル設定インスタンス（遅延読み込み）
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """グローバル設定取得"""
    global _config
    
    if _config is None:
        _config = load_config_from_env()
        validate_config(_config)
        _config.apply_logging()
    
    return _config


def reload_config() -> AppConfig:
    """設定再読み込み"""
    global _config
    _config = None
    return get_config()


# テスト用設定作成
def create_test_config() -> AppConfig:
    """テスト用設定作成"""
    return AppConfig(
        cosmos_db=CosmosDBSettings(
            endpoint="https://test-cosmos.documents.azure.com:443/",
            api_key="test-key",
            database_name="test_db"
        ),
        azure_auth=AzureAuthSettings(),
        chat_history=ChatHistorySettings(),
        migration=MigrationSettings(),
        logging=LoggingSettings(),
        performance=PerformanceSettings(),
        development=DevelopmentSettings(
            development_mode=True,
            mock_cosmos_db=True
        )
    )


if __name__ == "__main__":
    # 設定テスト実行
    print("=== 設定テスト ===")
    
    try:
        config = load_config_from_env()
        print("✅ 設定読み込み成功")
        
        valid, errors = config.validate_all()
        if valid:
            print("✅ 設定検証成功")
        else:
            print("❌ 設定検証失敗:")
            for section, section_errors in errors.items():
                print(f"  {section}: {section_errors}")
        
        print("\n📋 現在の設定:")
        import json
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 設定エラー: {e}")