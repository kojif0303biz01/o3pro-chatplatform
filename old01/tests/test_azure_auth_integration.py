#!/usr/bin/env python3
"""
Azure認証基盤とo3-pro統合テスト

Azure AD認証を使用してo3-proに接続し、基本機能をテスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.azure_universal_auth import AzureAuthManager, quick_auth
    from core.azure_auth import O3ProConfig, O3ProClient
    import openai
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)


class AzureO3ProIntegrationTester:
    """Azure AD認証 + o3-pro統合テスター"""
    
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
    
    def test_azure_ad_token_acquisition(self) -> bool:
        """Azure AD認証でCognitive Services用トークン取得テスト"""
        
        # Azure認証マネージャーで認証
        auth_manager = AzureAuthManager()
        result = auth_manager.authenticate("cognitive_services")
        
        if not result.success:
            print(f"   認証失敗: {result.error}")
            return False
        
        print(f"   認証方式: {result.method}")
        
        # Cognitive Services用トークン取得
        token = auth_manager.get_token("cognitive_services")
        
        if not token:
            print("   トークン取得失敗")
            return False
        
        print(f"   トークン取得成功: {token[:20]}...")
        return True
    
    def test_openai_client_with_azure_ad(self) -> bool:
        """Azure AD認証を使用したOpenAIクライアント接続テスト"""
        
        # 設定読み込み
        config = O3ProConfig()
        
        if not config.endpoint:
            print("   Azure OpenAI エンドポイントが設定されていません")
            return False
        
        # Azure AD認証でトークン取得
        success, credential, message = quick_auth("cognitive_services")
        
        if not success:
            print(f"   認証失敗: {message}")
            return False
        
        print(f"   認証成功: {message}")
        
        # Azure AD認証でOpenAIクライアント作成
        scope = "https://cognitiveservices.azure.com/.default"
        token = credential.get_token(scope)
        
        if not token:
            print("   トークン取得失敗")
            return False
        
        try:
            # OpenAIクライアント作成（トークンベース認証）
            client = openai.AzureOpenAI(
                azure_endpoint=config.endpoint,
                api_version=config.api_version,
                azure_ad_token=token.token
            )
            
            print(f"   OpenAIクライアント作成成功")
            return True
        
        except Exception as e:
            print(f"   OpenAIクライアント作成失敗: {e}")
            return False
    
    def test_o3_pro_reasoning_with_azure_ad(self) -> bool:
        """Azure AD認証を使用したo3-pro基本推論テスト"""
        
        # 設定読み込み
        config = O3ProConfig()
        
        if not all([config.endpoint, config.deployment]):
            print("   Azure OpenAI設定が不完全です")
            return False
        
        # Azure AD認証でトークン取得
        success, credential, message = quick_auth("cognitive_services")
        
        if not success:
            print(f"   認証失敗: {message}")
            return False
        
        try:
            # Azure AD認証でOpenAIクライアント作成
            scope = "https://cognitiveservices.azure.com/.default"
            token = credential.get_token(scope)
            
            client = openai.AzureOpenAI(
                azure_endpoint=config.endpoint,
                api_version=config.api_version,
                azure_ad_token=token.token
            )
            
            print(f"   OpenAIクライアント作成成功")
            
            # o3-pro推論テスト
            print(f"   o3-pro推論テスト実行中...")
            
            response = client.responses.create(
                model=config.deployment,
                input="1+1は何ですか？簡潔に答えてください。",
                reasoning={"effort": "low"}
            )
            
            if hasattr(response, 'output_text') and response.output_text:
                print(f"   推論結果: {response.output_text[:50]}...")
                return True
            else:
                print("   推論結果が取得できませんでした")
                return False
        
        except Exception as e:
            print(f"   o3-pro推論テスト失敗: {e}")
            return False
    
    def test_token_refresh_capability(self) -> bool:
        """トークンリフレッシュ機能テスト"""
        
        try:
            # 複数回のトークン取得で自動リフレッシュをテスト
            auth_manager = AzureAuthManager()
            
            # 初回認証
            result1 = auth_manager.authenticate("cognitive_services")
            if not result1.success:
                print(f"   初回認証失敗: {result1.error}")
                return False
            
            token1 = auth_manager.get_token("cognitive_services")
            print(f"   初回トークン: {token1[:20] if token1 else 'None'}...")
            
            # 再度トークン取得（キャッシュまたはリフレッシュ）
            token2 = auth_manager.get_token("cognitive_services")
            print(f"   2回目トークン: {token2[:20] if token2 else 'None'}...")
            
            return token1 and token2
        
        except Exception as e:
            print(f"   トークンリフレッシュテスト失敗: {e}")
            return False
    
    def test_multiple_service_authentication(self) -> bool:
        """複数Azureサービス認証テスト"""
        
        auth_manager = AzureAuthManager()
        
        # テスト対象サービス
        services = ["cognitive_services", "storage", "keyvault"]
        
        success_count = 0
        
        for service in services:
            try:
                result = auth_manager.authenticate(service)
                if result.success:
                    token = auth_manager.get_token(service)
                    if token:
                        print(f"   {service}: 認証・トークン取得成功")
                        success_count += 1
                    else:
                        print(f"   {service}: 認証成功、トークン取得失敗")
                else:
                    print(f"   {service}: 認証失敗 - {result.error}")
            
            except Exception as e:
                print(f"   {service}: 例外 - {e}")
        
        print(f"   成功サービス: {success_count}/{len(services)}")
        return success_count >= 1  # 最低1つのサービスで成功
    
    def test_fallback_to_api_key(self) -> bool:
        """Azure AD認証失敗時のAPIキーフォールバックテスト"""
        
        try:
            # 既存のO3ProClientでフォールバック動作を確認
            config = O3ProConfig()
            
            # APIキー設定の確認
            if not config.api_key:
                print("   APIキーが設定されていないため、フォールバックテストをスキップ")
                return True
            
            # 従来のAPIキー認証でクライアント作成
            client = O3ProClient(config)
            
            if client.is_ready():
                print("   APIキー認証でOpenAIクライアント作成成功")
                return True
            else:
                print("   APIキー認証でクライアント作成失敗")
                return False
        
        except Exception as e:
            print(f"   APIキーフォールバックテスト失敗: {e}")
            return False
    
    def run_all_tests(self):
        """全統合テスト実行"""
        print("=== Azure AD認証 + o3-pro統合テスト開始 ===")
        
        # 基本認証テスト
        self.run_test("Azure AD認証トークン取得", self.test_azure_ad_token_acquisition)
        self.run_test("OpenAIクライアント統合", self.test_openai_client_with_azure_ad)
        
        # o3-pro機能テスト
        self.run_test("o3-pro推論テスト", self.test_o3_pro_reasoning_with_azure_ad)
        
        # 高度な機能テスト
        self.run_test("トークンリフレッシュ", self.test_token_refresh_capability)
        self.run_test("複数サービス認証", self.test_multiple_service_authentication)
        
        # フォールバック機能テスト
        self.run_test("APIキーフォールバック", self.test_fallback_to_api_key)
        
        # 結果表示
        print(f"\n=== 統合テスト結果 ===")
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
    print("=== Azure AD + o3-pro統合テスト環境 ===")
    
    # 設定確認
    config = O3ProConfig()
    print(f"Azure OpenAI エンドポイント: {'設定済み' if config.endpoint else '未設定'}")
    print(f"デプロイメント名: {'設定済み' if config.deployment else '未設定'}")
    print(f"APIキー: {'設定済み' if config.api_key else '未設定'}")
    
    # Azure認証状態確認
    try:
        auth_manager = AzureAuthManager()
        health = auth_manager.health_check()
        print(f"Azure認証システム: {'正常' if health['azure_identity_available'] else '異常'}")
        
        available_providers = sum(1 for p in health['providers'].values() if p['available'])
        print(f"利用可能認証方式: {available_providers}個")
    
    except Exception as e:
        print(f"Azure認証システム確認失敗: {e}")
        return 1
    
    # 統合テスト実行
    tester = AzureO3ProIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 すべての統合テストに成功しました！")
        print("\n💡 Azure AD認証基盤は本格運用準備完了です")
        return 0
    else:
        print("\n💥 一部の統合テストが失敗しました")
        print("\n🔧 設定やAzure環境を確認してください")
        return 1


if __name__ == "__main__":
    exit(main())