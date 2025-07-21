# Core ライブラリモジュール

このフォルダには、他のプロジェクトでも再利用可能な汎用ライブラリモジュールが含まれています。

## 📦 モジュール一覧

### 1. **azure_universal_auth.py** - Azure汎用認証基盤
- 複数のAzureサービスに対応した統一認証システム
- az login、Service Principal、Managed Identityなど複数認証方式対応
- 詳細: [Azure認証モジュール仕様書](./azure_universal_auth_spec.md)

### 2. **azure_auth.py** - Azure OpenAI基本認証
- Azure OpenAI (o3-pro) 専用の認証・接続管理
- APIキー認証とAzure AD認証の両方に対応
- 詳細: [Azure OpenAI認証モジュール仕様書](./azure_auth_spec.md)

### 3. **error_handler.py** - エラーハンドリング
- 統一エラー処理とレスポンス生成
- リトライ機能付きエラーハンドラー
- 詳細: [エラーハンドラー仕様書](./error_handler_spec.md)

### 4. **chat_history.py** - チャット履歴管理（削除予定）
- **注意**: chat_history/local_history.py に移行済み
- このファイルは後方互換性のために残されています

## 🚀 使用方法

### インストール
```python
# プロジェクトルートからの相対インポート
from core.azure_universal_auth import AzureAuthManager, quick_auth
from core.azure_auth import O3ProConfig, O3ProClient
from core.error_handler import create_safe_response, retry_with_exponential_backoff
```

### クイックスタート

#### Azure汎用認証
```python
# 1行で認証
from core.azure_universal_auth import get_azure_token
token = get_azure_token("cognitive_services")

# 詳細制御
from core.azure_universal_auth import AzureAuthManager
auth_manager = AzureAuthManager()
result = auth_manager.authenticate("storage")
```

#### Azure OpenAI接続
```python
from core.azure_auth import O3ProConfig, O3ProClient

config = O3ProConfig()
client = O3ProClient(config)

if client.is_ready():
    # OpenAIクライアントを使用
    openai_client = client.client
```

## 📋 依存関係

- `azure-identity>=1.15.0`
- `openai>=1.5.0`
- `python-dotenv>=1.0.0`

## 🔧 設定

環境変数（.envファイル）で設定:

```bash
# Azure OpenAI設定
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment

# Azure AD認証（オプション）
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

## 📄 ライセンス

内部使用のみ。再配布時は要相談。