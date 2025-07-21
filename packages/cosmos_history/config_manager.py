"""
設定管理ユーティリティ

設定の検証、表示、更新を管理
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from .config import AppConfig, load_config_from_env, validate_config, get_config


logger = logging.getLogger(__name__)


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
    
    def display_config(self, mask_secrets: bool = True) -> None:
        """設定表示"""
        print("=" * 60)
        print("📋 Cosmos History 設定")
        print("=" * 60)
        
        self._display_cosmos_db_config(mask_secrets)
        self._display_azure_auth_config(mask_secrets)
        self._display_chat_history_config()
        self._display_migration_config()
        self._display_logging_config()
        self._display_performance_config()
        self._display_development_config()
        
        print("=" * 60)
    
    def _display_cosmos_db_config(self, mask_secrets: bool = True):
        """Cosmos DB設定表示"""
        print("\n🗄️  Cosmos DB設定:")
        
        endpoint = self.config.cosmos_db.endpoint
        if mask_secrets and endpoint:
            # エンドポイントをマスク
            endpoint = f"{endpoint[:30]}...{endpoint[-15:]}" if len(endpoint) > 45 else endpoint
        
        api_key = self.config.cosmos_db.api_key
        if mask_secrets and api_key:
            api_key = f"{api_key[:8]}..." if len(api_key) > 8 else "***"
        
        print(f"  Endpoint: {endpoint}")
        print(f"  API Key: {api_key or '未設定'}")
        print(f"  Database: {self.config.cosmos_db.database_name}")
        print(f"  Conversations Container: {self.config.cosmos_db.conversations_container}")
        print(f"  Messages Container: {self.config.cosmos_db.messages_container}")
        print(f"  Throughput Mode: {self.config.cosmos_db.throughput_mode.value}")
        print(f"  Max Throughput: {self.config.cosmos_db.max_throughput}")
        print(f"  Cache Enabled: {self.config.cosmos_db.enable_cache}")
    
    def _display_azure_auth_config(self, mask_secrets: bool = True):
        """Azure認証設定表示"""
        print("\n🔐 Azure認証設定:")
        
        client_id = self.config.azure_auth.client_id
        if mask_secrets and client_id:
            client_id = f"{client_id[:8]}..." if len(client_id) > 8 else "***"
        
        client_secret = self.config.azure_auth.client_secret
        if mask_secrets and client_secret:
            client_secret = "***" if client_secret else "未設定"
        
        print(f"  Client ID: {client_id or '未設定'}")
        print(f"  Client Secret: {client_secret or '未設定'}")
        print(f"  Tenant ID: {self.config.azure_auth.tenant_id or '未設定'}")
        print(f"  Subscription ID: {self.config.azure_auth.subscription_id or '未設定'}")
        print(f"  Auth Method: {self.config.azure_auth.auth_method.value}")
        print(f"  Prefer CLI: {self.config.azure_auth.prefer_cli}")
        print(f"  Service Principal Available: {self.config.azure_auth.has_service_principal()}")
    
    def _display_chat_history_config(self):
        """チャット履歴設定表示"""
        print("\n💬 チャット履歴設定:")
        print(f"  Local History Dir: {self.config.chat_history.local_history_dir}")
        print(f"  Default Tenant ID: {self.config.chat_history.default_tenant_id}")
        print(f"  Default User ID: {self.config.chat_history.default_user_id}")
        print(f"  Retention Days: {self.config.chat_history.retention_days}")
        print(f"  Max Messages per Conversation: {self.config.chat_history.max_messages_per_conversation}")
        print(f"  Enable Message Search: {self.config.chat_history.enable_message_search}")
    
    def _display_migration_config(self):
        """移行設定表示"""
        print("\n🔄 移行設定:")
        print(f"  Batch Size: {self.config.migration.batch_size}")
        print(f"  Dry Run Default: {self.config.migration.dry_run_default}")
        print(f"  Backup Enabled: {self.config.migration.backup_enabled}")
        print(f"  Verification Enabled: {self.config.migration.verification_enabled}")
    
    def _display_logging_config(self):
        """ログ設定表示"""
        print("\n📝 ログ設定:")
        print(f"  Log Level: {self.config.logging.log_level.value}")
        print(f"  Cosmos Log Level: {self.config.logging.cosmos_log_level.value}")
        print(f"  Azure SDK Log Level: {self.config.logging.azure_sdk_log_level.value}")
        print(f"  Debug Mode: {self.config.logging.debug_mode}")
        print(f"  Detailed Logging: {self.config.logging.enable_detailed_logging}")
        print(f"  Log Azure Requests: {self.config.logging.log_azure_requests}")
    
    def _display_performance_config(self):
        """パフォーマンス設定表示"""
        print("\n⚡ パフォーマンス設定:")
        print(f"  Search Cache TTL: {self.config.performance.search_cache_ttl_seconds}秒")
        print(f"  Search Max Cache Size: {self.config.performance.search_max_cache_size}")
        print(f"  Search Default Page Size: {self.config.performance.search_default_page_size}")
        print(f"  Search Max Page Size: {self.config.performance.search_max_page_size}")
        print(f"  API Rate Limit Enabled: {self.config.performance.api_rate_limit_enabled}")
        print(f"  API Max Requests/min: {self.config.performance.api_max_requests_per_minute}")
    
    def _display_development_config(self):
        """開発設定表示"""
        print("\n🔧 開発・テスト設定:")
        print(f"  Development Mode: {self.config.development.development_mode}")
        print(f"  Enable Test Data: {self.config.development.enable_test_data}")
        print(f"  Mock Cosmos DB: {self.config.development.mock_cosmos_db}")
        print(f"  Test Tenant ID: {self.config.development.test_tenant_id}")
        print(f"  Test User ID: {self.config.development.test_user_id}")
        print(f"  Test Database Name: {self.config.development.test_database_name}")
    
    def validate_config(self) -> Dict[str, Any]:
        """設定検証実行"""
        valid, errors = self.config.validate_all()
        
        validation_result = {
            "valid": valid,
            "errors": errors,
            "summary": self._create_validation_summary(valid, errors)
        }
        
        return validation_result
    
    def _create_validation_summary(self, valid: bool, errors: Dict[str, List[str]]) -> str:
        """検証結果サマリー作成"""
        if valid:
            return "✅ 全ての設定が有効です"
        
        error_count = sum(len(section_errors) for section_errors in errors.values())
        sections_with_errors = len(errors)
        
        return f"❌ {sections_with_errors}セクションで{error_count}個のエラーが見つかりました"
    
    def print_validation_result(self) -> bool:
        """検証結果表示"""
        result = self.validate_config()
        
        print("\n" + "=" * 60)
        print("🔍 設定検証結果")
        print("=" * 60)
        print(result["summary"])
        
        if not result["valid"]:
            print("\n詳細エラー:")
            for section, section_errors in result["errors"].items():
                print(f"\n  {section}:")
                for error in section_errors:
                    print(f"    ❌ {error}")
        
        print("=" * 60)
        
        return result["valid"]
    
    def export_config(self, file_path: str, include_secrets: bool = False) -> None:
        """設定をファイルに出力"""
        config_dict = self.config.to_dict()
        
        if not include_secrets:
            # 秘密情報をマスク
            config_dict = self._mask_secrets(config_dict)
        
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 設定を {file_path} に出力しました")
    
    def _mask_secrets(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """秘密情報マスク"""
        masked_config = config_dict.copy()
        
        # Cosmos DB API Key
        if masked_config.get("cosmos_db", {}).get("api_key"):
            masked_config["cosmos_db"]["api_key"] = "***"
        
        # Azure認証情報
        azure_auth = masked_config.get("azure_auth", {})
        if azure_auth.get("client_secret"):
            azure_auth["client_secret"] = "***"
        
        return masked_config
    
    def check_required_settings(self) -> Dict[str, Any]:
        """必須設定チェック"""
        required_checks = {
            "cosmos_db_endpoint": bool(self.config.cosmos_db.endpoint),
            "cosmos_db_auth": bool(
                self.config.cosmos_db.api_key or 
                self.config.azure_auth.has_service_principal()
            ),
            "database_name": bool(self.config.cosmos_db.database_name),
            "containers_configured": bool(
                self.config.cosmos_db.conversations_container and 
                self.config.cosmos_db.messages_container
            )
        }
        
        all_required = all(required_checks.values())
        missing_settings = [
            setting for setting, configured in required_checks.items() 
            if not configured
        ]
        
        return {
            "all_required_configured": all_required,
            "missing_settings": missing_settings,
            "required_checks": required_checks
        }
    
    def print_required_settings_check(self) -> bool:
        """必須設定チェック結果表示"""
        result = self.check_required_settings()
        
        print("\n" + "=" * 60)
        print("🔍 必須設定チェック")
        print("=" * 60)
        
        if result["all_required_configured"]:
            print("✅ 全ての必須設定が構成されています")
        else:
            print("❌ 必須設定が不足しています:")
            for setting in result["missing_settings"]:
                print(f"    - {setting}")
        
        print("\n詳細チェック結果:")
        for setting, configured in result["required_checks"].items():
            status = "✅" if configured else "❌"
            print(f"  {status} {setting}")
        
        if not result["all_required_configured"]:
            print("\n💡 推奨アクション:")
            print("  1. .env ファイルを作成し、必要な環境変数を設定してください")
            print("  2. .env.example を参考にしてください")
            print("  3. Azure ポータルで Cosmos DB アカウントを作成してください")
        
        print("=" * 60)
        
        return result["all_required_configured"]
    
    def suggest_env_file_content(self) -> str:
        """環境ファイル内容提案"""
        suggestions = []
        
        if not self.config.cosmos_db.endpoint:
            suggestions.append("COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/")
        
        if not self.config.cosmos_db.api_key and not self.config.azure_auth.has_service_principal():
            suggestions.append("COSMOS_DB_API_KEY=your-cosmos-api-key")
            suggestions.append("# または Azure AD認証:")
            suggestions.append("# AZURE_CLIENT_ID=your-client-id")
            suggestions.append("# AZURE_CLIENT_SECRET=your-client-secret")
            suggestions.append("# AZURE_TENANT_ID=your-tenant-id")
        
        if suggestions:
            suggestions.insert(0, "# 必須設定:")
            suggestions.append("")
            suggestions.append("# その他のオプション設定については .env.example を参照してください")
        
        return "\n".join(suggestions)


def create_config_manager(config: Optional[AppConfig] = None) -> ConfigManager:
    """設定管理インスタンス作成"""
    return ConfigManager(config)


def run_config_diagnostics():
    """設定診断実行"""
    print("🔧 Cosmos History 設定診断")
    print("=" * 60)
    
    try:
        # 検証を回避して設定を直接読み込み
        config = load_config_from_env()
        manager = ConfigManager(config)
        
        # 設定表示
        manager.display_config()
        
        # 検証実行
        validation_success = manager.print_validation_result()
        
        # 必須設定チェック
        required_success = manager.print_required_settings_check()
        
        # 総合判定
        overall_success = validation_success and required_success
        
        print(f"\n🎯 総合結果: {'✅ 設定OK' if overall_success else '❌ 設定に問題があります'}")
        
        if not overall_success:
            suggestions = manager.suggest_env_file_content()
            if suggestions:
                print("\n📝 推奨 .env 設定:")
                print(suggestions)
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 設定診断エラー: {e}")
        logger.exception("Config diagnostics failed")
        return False


if __name__ == "__main__":
    # 設定診断実行
    success = run_config_diagnostics()
    exit(0 if success else 1)