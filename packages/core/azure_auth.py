"""
Azure認証モジュール

既存のo3_pro_complete_toolkit.pyから抽出した動作確認済みの認証機能
O3ProConfig, O3ProClientクラスを提供

使用方法:
    from core.azure_auth import O3ProConfig, O3ProClient
    
    config = O3ProConfig()
    client = O3ProClient(config)
    
作成日: 2025-07-19（o3_pro_complete_toolkit.pyから抽出）
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class O3ProConfig:
    """o3-pro設定管理クラス（動作確認済み）"""
    
    def __init__(self, env_path: Optional[str] = None):
        """設定を初期化"""
        if env_path:
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=True)
        
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "O3-pro")
        self.api_version = "2025-04-01-preview"
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
    
    def validate(self) -> bool:
        """設定の妥当性をチェック（デバッグ済み）"""
        if not self.endpoint:
            print("NG AZURE_OPENAI_ENDPOINT が設定されていません")
            return False
        
        if not self.api_key and not self.has_azure_ad_config():
            print("NG API Key または Azure AD 設定が必要です")
            return False
        
        return True
    
    def has_azure_ad_config(self) -> bool:
        """Azure AD設定があるかチェック（デバッグ済み）"""
        return bool(self.client_id and self.client_secret and self.tenant_id)
    
    def print_config(self):
        """設定情報を表示（機密情報は伏せる）"""
        print("=== 設定情報 ===")
        print(f"エンドポイント: {self.endpoint}")
        print(f"デプロイメント: {self.deployment}")
        print(f"API バージョン: {self.api_version}")
        print(f"API Key: {'設定済み' if self.api_key else '未設定'}")
        print(f"Azure AD: {'設定済み' if self.has_azure_ad_config() else '未設定'}")


class O3ProClient:
    """o3-pro専用クライアントクラス（動作確認済み）"""
    
    def __init__(self, config: O3ProConfig, auth_method: str = "auto"):
        """
        クライアント初期化
        
        Args:
            config: 設定オブジェクト
            auth_method: 認証方法 ("api_key", "azure_ad", "auto")
        """
        self.config = config
        self.client = None
        self.auth_method = auth_method
        self._initialize_client()
    
    def _initialize_client(self):
        """クライアントを初期化（デバッグ済み）"""
        try:
            from openai import AzureOpenAI
            
            if self.auth_method == "api_key" or (
                self.auth_method == "auto" and self.config.api_key
            ):
                print("API Key認証でクライアント初期化中...")
                self.client = AzureOpenAI(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.endpoint,
                    api_version=self.config.api_version
                )
                print("OK API Key認証成功")
                
            elif self.auth_method == "azure_ad" or (
                self.auth_method == "auto" and self.config.has_azure_ad_config()
            ):
                print("Azure AD認証でクライアント初期化中...")
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default"
                )
                
                self.client = AzureOpenAI(
                    azure_endpoint=self.config.endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version=self.config.api_version
                )
                print("OK Azure AD認証成功")
                
            else:
                raise ValueError("有効な認証方法が設定されていません")
                
        except Exception as e:
            print(f"NG クライアント初期化失敗: {e}")
            self.client = None
    
    def is_ready(self) -> bool:
        """クライアントが使用可能かチェック"""
        return self.client is not None
    
    def test_connection(self) -> bool:
        """接続テスト（デバッグ済み）"""
        if not self.is_ready():
            return False
        
        try:
            print("接続テスト中...")
            models = self.client.models.list()
            print(f"OK 接続成功（モデル数: {len(models.data)}）")
            return True
        except Exception as e:
            print(f"NG 接続失敗: {e}")
            return False


# 使用例とテスト関数
def test_auth_module():
    """認証モジュールのテスト"""
    print("Azure認証モジュールテスト開始...")
    
    # 設定初期化
    env_path = Path(__file__).parent.parent / ".env"
    config = O3ProConfig(str(env_path))
    config.print_config()
    
    if not config.validate():
        print("ERROR 設定が不正です")
        return False
    
    # クライアント初期化
    client = O3ProClient(config)
    
    if not client.is_ready():
        print("ERROR クライアント初期化失敗")
        return False
    
    # 接続テスト
    return client.test_connection()


if __name__ == "__main__":
    test_auth_module()