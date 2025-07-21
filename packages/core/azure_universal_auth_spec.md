# Azure汎用認証基盤 モジュール仕様書

## 概要
`azure_universal_auth.py`は、複数のAzureサービスに対応した汎用認証基盤です。Azure CLIのaz login、Service Principal、Managed Identityなど複数の認証方式を統一的に扱えます。

## 主要クラス

### 1. AzureAuthManager
メインの認証管理クラス

#### コンストラクタ
```python
AzureAuthManager(
    cache_enabled: bool = True,      # トークンキャッシュ有効化
    prefer_cli: bool = True,         # Azure CLI認証を優先
    auto_fallback: bool = True       # 認証失敗時の自動フォールバック
)
```

#### 主要メソッド
```python
# 認証実行
authenticate(
    service: str = "cognitive_services",  # 対象サービス
    method: Optional[str] = None,         # 認証方式（None=自動）
    **kwargs
) -> AuthResult

# トークン取得
get_token(service: str = "cognitive_services") -> Optional[str]

# 認証状態確認
is_authenticated() -> bool

# 認証情報取得
get_auth_info() -> Dict[str, Any]

# ヘルスチェック
health_check() -> Dict[str, Any]

# サポートサービス一覧
get_supported_services() -> List[Tuple[str, str]]
```

### 2. AuthResult (dataclass)
認証結果を格納するデータクラス

```python
@dataclass
class AuthResult:
    success: bool                                    # 認証成功/失敗
    credential: Optional[TokenCredential] = None     # 認証クレデンシャル
    method: str = ""                                # 使用された認証方式
    user_info: Optional[Dict[str, Any]] = None     # ユーザー情報
    error: Optional[str] = None                     # エラーメッセージ
    expires_at: Optional[datetime] = None           # トークン有効期限
```

### 3. AzureServiceScopeRegistry
Azureサービスのスコープ管理

#### 対応サービス
- `cognitive_services`: Azure OpenAI, Speech, Vision等
- `storage`: Blob, Queue, Table Storage
- `keyvault`: Key Vault (シークレット、キー、証明書)
- `management`: Resource Manager API
- `graph`: Microsoft Graph API
- `sql`: Azure SQL Database
- `servicebus`: Azure Service Bus
- `eventhub`: Azure Event Hub

### 4. 認証プロバイダー
#### 基底クラス: CredentialProvider
```python
class CredentialProvider(ABC):
    @abstractmethod
    def create_credential(self, **kwargs) -> Optional[TokenCredential]
    
    @abstractmethod
    def is_available(self) -> bool
    
    @abstractmethod
    def validate_credential(self, credential: TokenCredential, scope: str) -> bool
    
    def get_priority(self) -> int
```

#### 実装クラス
- `CliCredentialProvider`: Azure CLI (az login) 認証
- `DefaultCredentialProvider`: 自動検出認証
- `ServicePrincipalCredentialProvider`: サービスプリンシパル認証
- `ManagedIdentityCredentialProvider`: マネージドID認証

## 便利な関数

### quick_auth
簡単に認証を行うヘルパー関数

```python
def quick_auth(
    service: str = "cognitive_services",
    method: Optional[str] = None
) -> Tuple[bool, Optional[TokenCredential], str]
```

### get_azure_token
トークンを直接取得

```python
def get_azure_token(service: str = "cognitive_services") -> Optional[str]
```

## 使用例

### 基本的な使用方法
```python
from core.azure_universal_auth import AzureAuthManager

# 認証マネージャー作成
auth_manager = AzureAuthManager()

# Cognitive Services認証
result = auth_manager.authenticate("cognitive_services")
if result.success:
    token = auth_manager.get_token("cognitive_services")
    print(f"認証成功: {result.method}")
```

### クイック認証
```python
from core.azure_universal_auth import quick_auth, get_azure_token

# 1行で認証
success, credential, message = quick_auth("storage")

# トークン直接取得
token = get_azure_token("keyvault")
```

### 特定の認証方式を指定
```python
# Azure CLI認証を明示的に使用
result = auth_manager.authenticate("cognitive_services", method="cli")

# Service Principal認証を使用
result = auth_manager.authenticate(
    "management",
    method="service_principal",
    client_id="xxx",
    client_secret="xxx",
    tenant_id="xxx"
)
```

## エラーハンドリング

認証失敗時は`AuthResult`の`error`フィールドに詳細メッセージが格納されます。

```python
result = auth_manager.authenticate("cognitive_services")
if not result.success:
    print(f"認証失敗: {result.error}")
```

## 環境変数

### Azure AD認証用
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret  
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id  # 一部サービスで必要
```

### Azure CLI認証
```bash
# az loginコマンドで事前にログインが必要
az login
```

## 注意事項

1. **認証優先順位**: デフォルトでは Azure CLI → Default → Service Principal → Managed Identity の順で試行
2. **トークンキャッシュ**: デフォルトで有効（`.azure_auth_cache`フォルダに保存）
3. **スコープ**: 各Azureサービスごとに適切なスコープが自動設定される
4. **エラー処理**: 認証失敗時は自動的に次の認証方式にフォールバック

## 動作確認済み環境

- ✅ Azure CLI認証: 完全動作確認
- ✅ Cognitive Services: トークン取得・API呼び出し成功
- ✅ Storage, Key Vault: トークン取得成功
- ⚠️ Service Principal: 環境設定のみ確認
- ⚠️ Managed Identity: Azure環境が必要