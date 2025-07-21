# Azure OpenAI認証モジュール 仕様書

## 概要
`azure_auth.py`は、Azure OpenAI (o3-pro)専用の認証・接続管理モジュールです。APIキー認証とAzure AD認証の両方に対応しています。

## 主要クラス

### 1. O3ProConfig
設定管理クラス

#### コンストラクタ
```python
O3ProConfig(env_path: Optional[str] = None)
```

#### プロパティ
```python
api_key: str           # Azure OpenAI APIキー
endpoint: str          # エンドポイントURL
deployment: str        # デプロイメント名（デフォルト: "O3-pro"）
api_version: str       # APIバージョン（固定: "2025-04-01-preview"）
client_id: str         # Azure AD クライアントID
client_secret: str     # Azure AD クライアントシークレット
tenant_id: str         # Azure AD テナントID
```

#### メソッド
```python
# 設定検証
validate() -> bool

# Azure AD設定の有無確認
has_azure_ad_config() -> bool

# 設定情報表示（デバッグ用）
display_config(masked: bool = True)
```

### 2. O3ProClient
OpenAIクライアント管理クラス

#### コンストラクタ
```python
O3ProClient(config: O3ProConfig, use_azure_ad: bool = False)
```

#### プロパティ
```python
client: openai.AzureOpenAI  # OpenAIクライアントインスタンス
auth_method: str            # 使用中の認証方式（"api_key" or "azure_ad"）
```

#### メソッド
```python
# クライアント準備状態確認
is_ready() -> bool

# OpenAIクライアント取得（エイリアス）
get_client() -> openai.AzureOpenAI
```

## 使用例

### 基本的な使用方法（APIキー認証）
```python
from core.azure_auth import O3ProConfig, O3ProClient

# 設定読み込み（.envファイルから）
config = O3ProConfig()

# クライアント作成
client = O3ProClient(config)

if client.is_ready():
    # OpenAIクライアントを使用
    openai_client = client.client
    
    # o3-pro推論実行
    response = openai_client.responses.create(
        model=config.deployment,
        input="質問内容",
        reasoning={"effort": "low"}
    )
```

### Azure AD認証を使用
```python
# Azure AD認証を有効化
client = O3ProClient(config, use_azure_ad=True)

if client.is_ready():
    print(f"認証方式: {client.auth_method}")  # "azure_ad"
```

### カスタム設定ファイルを使用
```python
# 特定の.envファイルを指定
config = O3ProConfig("custom.env")

# 設定確認
config.display_config(masked=True)
```

## 環境変数

### 必須設定
```bash
# エンドポイント（必須）
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 認証情報（いずれか必須）
## APIキー認証
AZURE_OPENAI_API_KEY=your-api-key

## Azure AD認証
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

### オプション設定
```bash
# デプロイメント名（デフォルト: O3-pro）
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

## エラーハンドリング

### 設定検証
```python
config = O3ProConfig()
if not config.validate():
    # エラーメッセージが自動的に表示される
    exit(1)
```

### クライアント初期化エラー
```python
try:
    client = O3ProClient(config)
    if not client.is_ready():
        print("クライアント初期化失敗")
except Exception as e:
    print(f"エラー: {e}")
```

## Azure AD認証との統合

`azure_universal_auth.py`と組み合わせて使用する場合:

```python
from core.azure_universal_auth import quick_auth
from core.azure_auth import O3ProConfig
import openai

# Azure AD認証でトークン取得
success, credential, message = quick_auth("cognitive_services")

if success:
    config = O3ProConfig()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    # トークンベース認証でクライアント作成
    client = openai.AzureOpenAI(
        azure_endpoint=config.endpoint,
        api_version=config.api_version,
        azure_ad_token=token.token
    )
```

## 注意事項

1. **APIバージョン**: o3-pro用に`2025-04-01-preview`で固定
2. **認証優先順位**: APIキー → Azure AD（明示的に指定した場合）
3. **エンドポイント形式**: 末尾のスラッシュは自動処理
4. **デバッグ出力**: `display_config()`でマスク付き表示可能

## 動作確認済み機能

- ✅ APIキー認証での接続
- ✅ o3-pro推論（reasoning）実行
- ✅ ストリーミング応答
- ✅ バックグラウンド処理
- ✅ エラーハンドリング
- ⚠️ Azure AD認証（azure_universal_authとの統合で動作確認済み）