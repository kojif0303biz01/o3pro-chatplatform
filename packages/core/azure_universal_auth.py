#!/usr/bin/env python3
"""
Azure汎用認証基盤 - Universal Azure Authentication Framework

他のAzureサービスでも使用可能な汎用認証システム
- 複数認証方式の統一インターフェース
- サービス別スコープ管理
- 自動フォールバック機能
- トークンキャッシュ・検証

作成日: 2025-07-20
"""

import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

try:
    from azure.identity import (
        DefaultAzureCredential,
        AzureCliCredential, 
        ClientSecretCredential,
        ManagedIdentityCredential,
        InteractiveBrowserCredential
    )
    from azure.core.credentials import TokenCredential
    from azure.core.exceptions import ClientAuthenticationError
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    TokenCredential = None


@dataclass
class AuthResult:
    """認証結果"""
    success: bool
    credential: Optional[TokenCredential] = None
    method: str = ""
    user_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass 
class ServiceScope:
    """Azureサービス別スコープ定義"""
    service_name: str
    default_scope: str
    description: str
    additional_scopes: Optional[List[str]] = None


class AzureServiceScopeRegistry:
    """Azureサービススコープレジストリ"""
    
    SCOPES = {
        "cognitive_services": ServiceScope(
            service_name="Cognitive Services",
            default_scope="https://cognitiveservices.azure.com/.default",
            description="Azure Cognitive Services (OpenAI, Speech, Vision など)",
            additional_scopes=["https://cognitiveservices.azure.com/read"]
        ),
        "storage": ServiceScope(
            service_name="Storage",
            default_scope="https://storage.azure.com/.default", 
            description="Azure Storage (Blob, Queue, Table など)",
            additional_scopes=["https://storage.azure.com/user_impersonation"]
        ),
        "keyvault": ServiceScope(
            service_name="Key Vault",
            default_scope="https://vault.azure.net/.default",
            description="Azure Key Vault (シークレット、キー、証明書)",
            additional_scopes=["https://vault.azure.net/user_impersonation"]
        ),
        "management": ServiceScope(
            service_name="Resource Management", 
            default_scope="https://management.azure.com/.default",
            description="Azure Resource Manager API",
            additional_scopes=["https://management.azure.com/user_impersonation"]
        ),
        "graph": ServiceScope(
            service_name="Microsoft Graph",
            default_scope="https://graph.microsoft.com/.default",
            description="Microsoft Graph API (ユーザー、グループなど)",
            additional_scopes=[
                "https://graph.microsoft.com/User.Read",
                "https://graph.microsoft.com/Directory.Read.All"
            ]
        ),
        "sql": ServiceScope(
            service_name="SQL Database",
            default_scope="https://database.windows.net/.default",
            description="Azure SQL Database",
            additional_scopes=["https://database.windows.net/user_impersonation"]
        ),
        "servicebus": ServiceScope(
            service_name="Service Bus",
            default_scope="https://servicebus.azure.net/.default", 
            description="Azure Service Bus",
            additional_scopes=["https://servicebus.azure.net/user_impersonation"]
        ),
        "eventhub": ServiceScope(
            service_name="Event Hub",
            default_scope="https://eventhubs.azure.net/.default",
            description="Azure Event Hub", 
            additional_scopes=["https://eventhubs.azure.net/user_impersonation"]
        )
    }
    
    @classmethod
    def get_scope(cls, service_key: str) -> Optional[ServiceScope]:
        """サービスキーからスコープ情報を取得"""
        return cls.SCOPES.get(service_key.lower())
    
    @classmethod
    def get_default_scope(cls, service_key: str) -> Optional[str]:
        """デフォルトスコープを取得"""
        scope_info = cls.get_scope(service_key)
        return scope_info.default_scope if scope_info else None
    
    @classmethod
    def list_services(cls) -> List[Tuple[str, str]]:
        """利用可能なサービス一覧を取得"""
        return [(key, scope.service_name) for key, scope in cls.SCOPES.items()]


class CredentialProvider(ABC):
    """認証プロバイダーの抽象基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_error: Optional[str] = None
    
    @abstractmethod
    def create_credential(self, **kwargs) -> Optional[TokenCredential]:
        """認証クレデンシャルを作成"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """認証方式が利用可能かチェック"""
        pass
    
    @abstractmethod
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool:
        """認証クレデンシャルの有効性を検証"""
        pass
    
    def get_priority(self) -> int:
        """認証プロバイダーの優先度（低い値が高優先度）"""
        return 100


class CliCredentialProvider(CredentialProvider):
    """Azure CLI認証プロバイダー"""
    
    def __init__(self):
        super().__init__("Azure CLI")
    
    def create_credential(self, **kwargs) -> Optional[TokenCredential]:
        try:
            return AzureCliCredential()
        except Exception as e:
            self.last_error = f"Azure CLI認証の作成に失敗: {e}"
            return None
    
    def is_available(self) -> bool:
        """Azure CLIがインストールされ、ログイン済みかチェック"""
        if not AZURE_IDENTITY_AVAILABLE:
            return False
        
        try:
            # Azure CLIの認証状態をチェック
            credential = AzureCliCredential()
            # トークン取得を試行（軽量なスコープでテスト）
            token = credential.get_token("https://management.azure.com/.default")
            return token is not None
        except Exception as e:
            self.last_error = f"Azure CLI認証チェック失敗: {e}"
            return False
    
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool:
        try:
            token = credential.get_token(scope)
            return token is not None and token.token
        except Exception as e:
            self.last_error = f"認証検証失敗: {e}"
            return False
    
    def get_priority(self) -> int:
        return 10  # 高優先度


class DefaultCredentialProvider(CredentialProvider):
    """デフォルト認証プロバイダー（自動検出）"""
    
    def __init__(self):
        super().__init__("Default Azure Credential")
    
    def create_credential(self, **kwargs) -> Optional[TokenCredential]:
        try:
            exclude_cli = kwargs.get('exclude_cli', False)
            exclude_browser = kwargs.get('exclude_browser', True)
            
            return DefaultAzureCredential(
                exclude_cli_credential=exclude_cli,
                exclude_interactive_browser_credential=exclude_browser
            )
        except Exception as e:
            self.last_error = f"DefaultAzureCredential作成失敗: {e}"
            return None
    
    def is_available(self) -> bool:
        if not AZURE_IDENTITY_AVAILABLE:
            return False
        
        try:
            credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
            token = credential.get_token("https://management.azure.com/.default")
            return token is not None
        except Exception as e:
            self.last_error = f"DefaultAzureCredential利用不可: {e}"
            return False
    
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool:
        try:
            token = credential.get_token(scope)
            return token is not None and token.token
        except Exception as e:
            self.last_error = f"認証検証失敗: {e}"
            return False
    
    def get_priority(self) -> int:
        return 20  # 中優先度


class ServicePrincipalCredentialProvider(CredentialProvider):
    """サービスプリンシパル認証プロバイダー"""
    
    def __init__(self):
        super().__init__("Service Principal")
    
    def create_credential(self, **kwargs) -> Optional[TokenCredential]:
        try:
            client_id = kwargs.get('client_id') or os.getenv('AZURE_CLIENT_ID')
            client_secret = kwargs.get('client_secret') or os.getenv('AZURE_CLIENT_SECRET')
            tenant_id = kwargs.get('tenant_id') or os.getenv('AZURE_TENANT_ID')
            
            if not all([client_id, client_secret, tenant_id]):
                self.last_error = "サービスプリンシパルの必要な情報が不足"
                return None
            
            return ClientSecretCredential(tenant_id, client_id, client_secret)
        except Exception as e:
            self.last_error = f"サービスプリンシパル認証作成失敗: {e}"
            return None
    
    def is_available(self) -> bool:
        if not AZURE_IDENTITY_AVAILABLE:
            return False
        
        required_vars = ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID']
        return all(os.getenv(var) for var in required_vars)
    
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool:
        try:
            token = credential.get_token(scope)
            return token is not None and token.token
        except Exception as e:
            self.last_error = f"認証検証失敗: {e}"
            return False
    
    def get_priority(self) -> int:
        return 30  # 低優先度


class ManagedIdentityCredentialProvider(CredentialProvider):
    """マネージドアイデンティティ認証プロバイダー"""
    
    def __init__(self):
        super().__init__("Managed Identity")
    
    def create_credential(self, **kwargs) -> Optional[TokenCredential]:
        try:
            client_id = kwargs.get('client_id')
            return ManagedIdentityCredential(client_id=client_id)
        except Exception as e:
            self.last_error = f"マネージドアイデンティティ認証作成失敗: {e}"
            return None
    
    def is_available(self) -> bool:
        if not AZURE_IDENTITY_AVAILABLE:
            return False
        
        try:
            # IMDS エンドポイントの存在確認（簡易チェック）
            import socket
            socket.setdefaulttimeout(1)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('169.254.169.254', 80))
            return True
        except:
            return False
    
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool:
        try:
            token = credential.get_token(scope)
            return token is not None and token.token
        except Exception as e:
            self.last_error = f"認証検証失敗: {e}"
            return False
    
    def get_priority(self) -> int:
        return 25  # 中〜低優先度


class TokenCacheManager:
    """トークンキャッシュ管理"""
    
    def __init__(self, cache_dir: str = ".azure_auth_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, method: str, service: str, user_id: str = "default") -> str:
        """キャッシュキーを生成"""
        return f"{method}_{service}_{user_id}"
    
    def save_token_info(self, cache_key: str, token_info: Dict[str, Any]):
        """トークン情報をキャッシュに保存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(token_info, f, default=str)
        except Exception as e:
            print(f"WARN: トークンキャッシュ保存失敗: {e}")
    
    def load_token_info(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュからトークン情報を読み込み"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"WARN: トークンキャッシュ読み込み失敗: {e}")
        return None
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """キャッシュをクリア"""
        try:
            if cache_key:
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
            else:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
        except Exception as e:
            print(f"WARN: キャッシュクリア失敗: {e}")


class AzureAuthManager:
    """Azure汎用認証管理クラス"""
    
    def __init__(self, 
                 cache_enabled: bool = True,
                 prefer_cli: bool = True,
                 auto_fallback: bool = True):
        
        if not AZURE_IDENTITY_AVAILABLE:
            raise ImportError("azure-identity パッケージがインストールされていません")
        
        self.cache_enabled = cache_enabled
        self.prefer_cli = prefer_cli
        self.auto_fallback = auto_fallback
        
        # プロバイダー初期化
        self.providers: List[CredentialProvider] = [
            CliCredentialProvider(),
            DefaultCredentialProvider(), 
            ServicePrincipalCredentialProvider(),
            ManagedIdentityCredentialProvider()
        ]
        
        # 優先度でソート
        self.providers.sort(key=lambda p: p.get_priority())
        
        # キャッシュマネージャー
        self.cache_manager = TokenCacheManager() if cache_enabled else None
        
        # 現在の認証状態
        self.current_auth: Optional[AuthResult] = None
    
    def authenticate(self, 
                    service: str = "cognitive_services",
                    method: Optional[str] = None,
                    **kwargs) -> AuthResult:
        """認証を実行"""
        
        # サービススコープ取得
        scope = AzureServiceScopeRegistry.get_default_scope(service)
        if not scope:
            return AuthResult(
                success=False,
                error=f"未対応サービス: {service}"
            )
        
        # 特定の認証方式が指定された場合
        if method:
            return self._authenticate_with_method(method, scope, **kwargs)
        
        # 自動認証（プロバイダーを優先度順に試行）
        return self._authenticate_auto(scope, **kwargs)
    
    def _authenticate_with_method(self, method: str, scope: str, **kwargs) -> AuthResult:
        """指定された認証方式で認証"""
        
        provider_map = {
            "cli": CliCredentialProvider(),
            "default": DefaultCredentialProvider(),
            "service_principal": ServicePrincipalCredentialProvider(),
            "managed_identity": ManagedIdentityCredentialProvider()
        }
        
        provider = provider_map.get(method.lower())
        if not provider:
            return AuthResult(
                success=False,
                error=f"未対応認証方式: {method}"
            )
        
        return self._try_authenticate(provider, scope, **kwargs)
    
    def _authenticate_auto(self, scope: str, **kwargs) -> AuthResult:
        """自動認証（フォールバック付き）"""
        
        last_error = ""
        
        for provider in self.providers:
            if not provider.is_available():
                continue
            
            result = self._try_authenticate(provider, scope, **kwargs)
            
            if result.success:
                self.current_auth = result
                return result
            
            last_error = result.error or f"{provider.name}認証失敗"
            
            if not self.auto_fallback:
                break
        
        return AuthResult(
            success=False,
            error=f"すべての認証方式が失敗: {last_error}"
        )
    
    def _try_authenticate(self, provider: CredentialProvider, scope: str, **kwargs) -> AuthResult:
        """プロバイダーで認証を試行"""
        
        try:
            # 認証クレデンシャル作成
            credential = provider.create_credential(**kwargs)
            if not credential:
                return AuthResult(
                    success=False,
                    method=provider.name,
                    error=provider.last_error or "クレデンシャル作成失敗"
                )
            
            # 認証検証
            if not provider.validate_credential(credential, scope):
                return AuthResult(
                    success=False,
                    method=provider.name,
                    error=provider.last_error or "認証検証失敗"
                )
            
            # ユーザー情報取得（可能な場合）
            user_info = self._get_user_info(credential)
            
            # 成功結果
            return AuthResult(
                success=True,
                credential=credential,
                method=provider.name,
                user_info=user_info,
                expires_at=datetime.now() + timedelta(hours=1)  # 概算有効期限
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                method=provider.name,
                error=f"認証エラー: {e}"
            )
    
    def _get_user_info(self, credential: TokenCredential) -> Optional[Dict[str, Any]]:
        """ユーザー情報を取得（可能な場合）"""
        try:
            # Microsoft Graphからユーザー情報取得を試行
            graph_scope = "https://graph.microsoft.com/.default"
            token = credential.get_token(graph_scope)
            
            if token:
                # 実際のGraph API呼び出しは省略（必要に応じて実装）
                return {
                    "authenticated": True,
                    "method": "azure_ad",
                    "token_expires": token.expires_on
                }
        except:
            pass
        
        return {"authenticated": True}
    
    def get_token(self, service: str = "cognitive_services") -> Optional[str]:
        """指定サービス用のアクセストークンを取得"""
        
        if not self.current_auth or not self.current_auth.success:
            auth_result = self.authenticate(service)
            if not auth_result.success:
                return None
        
        scope = AzureServiceScopeRegistry.get_default_scope(service)
        if not scope:
            return None
        
        try:
            token = self.current_auth.credential.get_token(scope)
            return token.token if token else None
        except Exception as e:
            print(f"WARN: トークン取得失敗: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """認証状態をチェック"""
        return (self.current_auth is not None and 
                self.current_auth.success and
                self.current_auth.credential is not None)
    
    def get_auth_info(self) -> Dict[str, Any]:
        """現在の認証情報を取得"""
        if not self.current_auth:
            return {"authenticated": False}
        
        return {
            "authenticated": self.current_auth.success,
            "method": self.current_auth.method,
            "user_info": self.current_auth.user_info,
            "expires_at": self.current_auth.expires_at,
            "error": self.current_auth.error
        }
    
    def clear_auth(self):
        """認証状態をクリア"""
        self.current_auth = None
        if self.cache_manager:
            self.cache_manager.clear_cache()
    
    def get_supported_services(self) -> List[Tuple[str, str]]:
        """サポートされているAzureサービス一覧"""
        return AzureServiceScopeRegistry.list_services()
    
    def health_check(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        result = {
            "azure_identity_available": AZURE_IDENTITY_AVAILABLE,
            "providers": {},
            "services": len(AzureServiceScopeRegistry.SCOPES),
            "authenticated": self.is_authenticated()
        }
        
        for provider in self.providers:
            result["providers"][provider.name] = {
                "available": provider.is_available(),
                "priority": provider.get_priority(),
                "last_error": provider.last_error
            }
        
        return result


# 便利な関数

def quick_auth(service: str = "cognitive_services", 
               method: Optional[str] = None) -> Tuple[bool, Optional[TokenCredential], str]:
    """クイック認証 - 簡単にAzure認証を行う"""
    
    try:
        auth_manager = AzureAuthManager()
        result = auth_manager.authenticate(service=service, method=method)
        
        if result.success:
            return True, result.credential, f"認証成功: {result.method}"
        else:
            return False, None, result.error or "認証失敗"
    
    except Exception as e:
        return False, None, f"認証エラー: {e}"


def get_azure_token(service: str = "cognitive_services") -> Optional[str]:
    """アクセストークンを直接取得"""
    
    success, credential, message = quick_auth(service)
    if not success or not credential:
        return None
    
    scope = AzureServiceScopeRegistry.get_default_scope(service)
    if not scope:
        return None
    
    try:
        token = credential.get_token(scope)
        return token.token if token else None
    except:
        return None


if __name__ == "__main__":
    # テスト実行
    print("=== Azure汎用認証基盤テスト ===")
    
    auth_manager = AzureAuthManager()
    
    # ヘルスチェック
    health = auth_manager.health_check()
    print(f"システム状態: {health}")
    
    # 認証テスト
    result = auth_manager.authenticate("cognitive_services")
    print(f"認証結果: {result}")
    
    if result.success:
        token = auth_manager.get_token("cognitive_services")
        print(f"トークン取得: {'OK' if token else 'NG'}")