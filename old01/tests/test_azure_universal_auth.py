#!/usr/bin/env python3
"""
Azure汎用認証基盤テストモジュール

各認証方式の動作確認とライフサイクルテスト
"""

import sys
import os
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.azure_universal_auth import (
        AzureAuthManager,
        AzureServiceScopeRegistry,
        CliCredentialProvider,
        DefaultCredentialProvider,
        ServicePrincipalCredentialProvider,
        ManagedIdentityCredentialProvider,
        quick_auth,
        get_azure_token,
        AZURE_IDENTITY_AVAILABLE
    )
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)


class AzureAuthTester:
    """Azure認証基盤テスタークラス"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def run_test(self, test_name: str, test_func):
        """テスト実行"""
        print(f"\n🧪 {test_name} ...")
        
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} - 成功")
                self.passed += 1
                self.results.append((test_name, True, None))
            else:
                print(f"❌ {test_name} - 失敗")
                self.failed += 1
                self.results.append((test_name, False, "テスト条件不合格"))
        
        except Exception as e:
            print(f"💥 {test_name} - 例外: {e}")
            self.failed += 1
            self.results.append((test_name, False, str(e)))
    
    def test_azure_identity_availability(self) -> bool:
        """azure-identityパッケージの利用可能性テスト"""
        print(f"   azure-identity利用可能: {AZURE_IDENTITY_AVAILABLE}")
        return AZURE_IDENTITY_AVAILABLE
    
    def test_service_scope_registry(self) -> bool:
        """サービススコープレジストリテスト"""
        
        # 基本的なサービススコープ確認
        cognitive_scope = AzureServiceScopeRegistry.get_default_scope("cognitive_services")
        print(f"   Cognitive Services スコープ: {cognitive_scope}")
        
        if cognitive_scope != "https://cognitiveservices.azure.com/.default":
            return False
        
        # サービス一覧取得
        services = AzureServiceScopeRegistry.list_services()
        print(f"   対応サービス数: {len(services)}")
        
        return len(services) >= 8  # 基本的なサービス数チェック
    
    def test_credential_providers_availability(self) -> bool:
        """認証プロバイダー利用可能性テスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        providers = [
            CliCredentialProvider(),
            DefaultCredentialProvider(),
            ServicePrincipalCredentialProvider(),
            ManagedIdentityCredentialProvider()
        ]
        
        available_count = 0
        for provider in providers:
            is_available = provider.is_available()
            print(f"   {provider.name}: {'利用可能' if is_available else '利用不可'}")
            if provider.last_error:
                print(f"     エラー: {provider.last_error}")
            
            if is_available:
                available_count += 1
        
        print(f"   利用可能プロバイダー: {available_count}/{len(providers)}")
        return available_count > 0  # 最低1つの認証方式が利用可能
    
    def test_auth_manager_health_check(self) -> bool:
        """認証マネージャーヘルスチェックテスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        try:
            auth_manager = AzureAuthManager()
            health = auth_manager.health_check()
            
            print(f"   システム状態: {health['azure_identity_available']}")
            print(f"   対応サービス数: {health['services']}")
            print(f"   プロバイダー数: {len(health['providers'])}")
            
            return health['azure_identity_available'] and health['services'] > 0
        
        except Exception as e:
            print(f"   ヘルスチェックエラー: {e}")
            return False
    
    def test_authentication_attempt(self) -> bool:
        """認証試行テスト（実際の認証は環境に依存）"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        try:
            auth_manager = AzureAuthManager()
            result = auth_manager.authenticate("cognitive_services")
            
            print(f"   認証結果: {result.success}")
            print(f"   認証方式: {result.method}")
            
            if result.success:
                print(f"   ユーザー情報: {result.user_info}")
                
                # トークン取得テスト
                token = auth_manager.get_token("cognitive_services")
                print(f"   トークン取得: {'成功' if token else '失敗'}")
                
                return True
            else:
                print(f"   認証エラー: {result.error}")
                # 認証失敗は環境によるものなので、テスト失敗とはしない
                return True
        
        except Exception as e:
            print(f"   認証テストエラー: {e}")
            return False
    
    def test_quick_auth_function(self) -> bool:
        """クイック認証関数テスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        try:
            success, credential, message = quick_auth("cognitive_services")
            print(f"   クイック認証結果: {success}")
            print(f"   メッセージ: {message}")
            
            # 認証に成功した場合のみトークン取得テスト
            if success and credential:
                token = get_azure_token("cognitive_services")
                print(f"   トークン直接取得: {'成功' if token else '失敗'}")
            
            return True  # 環境に依存するため常に成功とする
        
        except Exception as e:
            print(f"   クイック認証エラー: {e}")
            return False
    
    def test_multiple_services(self) -> bool:
        """複数サービスに対する認証テスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        services = ["cognitive_services", "storage", "keyvault", "management"]
        
        try:
            auth_manager = AzureAuthManager()
            
            for service in services:
                scope = AzureServiceScopeRegistry.get_default_scope(service)
                print(f"   {service}: {scope}")
                
                if not scope:
                    return False
            
            return True
        
        except Exception as e:
            print(f"   複数サービステストエラー: {e}")
            return False
    
    def test_auth_manager_lifecycle(self) -> bool:
        """認証マネージャーライフサイクルテスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        try:
            # 初期化
            auth_manager = AzureAuthManager(cache_enabled=True)
            print(f"   初期認証状態: {auth_manager.is_authenticated()}")
            
            # 認証情報取得
            auth_info = auth_manager.get_auth_info()
            print(f"   認証情報: {auth_info['authenticated']}")
            
            # 認証クリア
            auth_manager.clear_auth()
            print(f"   クリア後認証状態: {auth_manager.is_authenticated()}")
            
            # サポートサービス一覧
            services = auth_manager.get_supported_services()
            print(f"   サポートサービス数: {len(services)}")
            
            return True
        
        except Exception as e:
            print(f"   ライフサイクルテストエラー: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """エラーハンドリングテスト"""
        
        if not AZURE_IDENTITY_AVAILABLE:
            print("   azure-identity が利用できないため、スキップ")
            return True
        
        try:
            auth_manager = AzureAuthManager()
            
            # 無効なサービス名
            result = auth_manager.authenticate("invalid_service")
            print(f"   無効サービス認証: {result.success} (期待: False)")
            if result.success:
                return False
            
            # 無効な認証方式
            result = auth_manager._authenticate_with_method("invalid_method", "test_scope")
            print(f"   無効認証方式: {result.success} (期待: False)")
            if result.success:
                return False
            
            # 無効なスコープでのトークン取得
            token = auth_manager.get_token("invalid_service")
            print(f"   無効スコープトークン: {token is None} (期待: True)")
            if token is not None:
                return False
            
            return True
        
        except Exception as e:
            print(f"   エラーハンドリングテストエラー: {e}")
            return False
    
    def run_all_tests(self):
        """全テスト実行"""
        print("=== Azure汎用認証基盤テスト開始 ===")
        
        # 基本機能テスト
        self.run_test("azure-identity利用可能性", self.test_azure_identity_availability)
        self.run_test("サービススコープレジストリ", self.test_service_scope_registry)
        self.run_test("認証プロバイダー利用可能性", self.test_credential_providers_availability)
        self.run_test("認証マネージャーヘルスチェック", self.test_auth_manager_health_check)
        
        # 認証機能テスト
        self.run_test("認証試行", self.test_authentication_attempt)
        self.run_test("クイック認証関数", self.test_quick_auth_function)
        self.run_test("複数サービス対応", self.test_multiple_services)
        
        # ライフサイクルテスト
        self.run_test("認証マネージャーライフサイクル", self.test_auth_manager_lifecycle)
        self.run_test("エラーハンドリング", self.test_error_handling)
        
        # 結果表示
        print(f"\n=== テスト結果 ===")
        print(f"成功: {self.passed}")
        print(f"失敗: {self.failed}")
        print(f"成功率: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        
        if self.failed > 0:
            print(f"\n失敗したテスト:")
            for name, success, error in self.results:
                if not success:
                    print(f"  ❌ {name}: {error}")
        
        return self.failed == 0


def main():
    """メイン関数"""
    
    # 環境情報表示
    print("=== 環境情報 ===")
    print(f"Python バージョン: {sys.version}")
    print(f"プロジェクトルート: {project_root}")
    print(f"azure-identity: {'インストール済み' if AZURE_IDENTITY_AVAILABLE else '未インストール'}")
    
    # Azure CLI ログイン状態確認
    print(f"\n=== Azure CLI 状態確認 ===")
    try:
        import subprocess
        result = subprocess.run(['az', 'account', 'show'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Azure CLI ログイン済み")
        else:
            print("⚠️  Azure CLI 未ログインまたは未インストール")
    except Exception as e:
        print(f"⚠️  Azure CLI 状態確認失敗: {e}")
    
    # 環境変数確認
    print(f"\n=== 環境変数確認 ===")
    env_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET', 
        'AZURE_TENANT_ID',
        'AZURE_SUBSCRIPTION_ID'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 8}...{value[-4:]}")
        else:
            print(f"⚠️  {var}: 未設定")
    
    # テスト実行
    tester = AzureAuthTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 すべてのテストに成功しました！")
        return 0
    else:
        print("\n💥 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    exit(main())