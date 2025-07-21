# Cosmos History モジュール 設定ガイド

このガイドでは、Cosmos History モジュールの設定方法について説明します。

## 🚀 クイックスタート

### 1. 必須環境変数の設定

最低限必要な設定は以下の通りです：

```bash
# .env ファイルを作成
cp .env.example .env

# 必須設定を編集
COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_API_KEY=your-cosmos-api-key
```

### 2. 設定診断の実行

設定が正しく構成されているかチェックします：

```bash
python cosmos_history/cli_config.py diagnostics
```

## 📋 設定項目の詳細

### Azure Cosmos DB設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `COSMOS_DB_ENDPOINT` | ✅ | - | Cosmos DBエンドポイントURL |
| `COSMOS_DB_API_KEY` | ⚠️ | - | API Key（Azure AD認証を使わない場合は必須） |
| `COSMOS_DB_DATABASE_NAME` | | `chat_history_db` | データベース名 |
| `COSMOS_DB_CONVERSATIONS_CONTAINER` | | `conversations` | 会話コンテナー名 |
| `COSMOS_DB_MESSAGES_CONTAINER` | | `messages` | メッセージコンテナー名 |
| `COSMOS_DB_THROUGHPUT_MODE` | | `serverless` | スループットモード (`serverless`/`provisioned`) |
| `COSMOS_DB_MAX_THROUGHPUT` | | `4000` | 最大スループット (RU/s) |
| `ENABLE_COSMOS_CACHE` | | `true` | キャッシュ有効化 |

### Azure認証設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `AZURE_CLIENT_ID` | ⚠️ | - | Service Principal クライアントID |
| `AZURE_CLIENT_SECRET` | ⚠️ | - | Service Principal クライアントシークレット |
| `AZURE_TENANT_ID` | ⚠️ | - | Azure テナントID |
| `AZURE_SUBSCRIPTION_ID` | | - | Azure サブスクリプションID |
| `AZURE_AUTH_METHOD` | | `auto` | 認証方式 (`auto`/`apikey`/`azuread`/`cli`/`msi`) |
| `AZURE_PREFER_CLI` | | `false` | Azure CLI認証を優先するか |

⚠️ Azure AD認証を使用する場合は必須

### チャット履歴設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `LOCAL_CHAT_HISTORY_DIR` | | `chat_history` | ローカル履歴ディレクトリ |
| `DEFAULT_TENANT_ID` | | `default_tenant` | デフォルトテナントID |
| `DEFAULT_USER_ID` | | `default_user` | デフォルトユーザーID |
| `CHAT_HISTORY_RETENTION_DAYS` | | `365` | 履歴保持日数 |
| `MAX_MESSAGES_PER_CONVERSATION` | | `1000` | 会話あたりの最大メッセージ数 |
| `ENABLE_MESSAGE_SEARCH` | | `true` | メッセージ検索機能有効化 |

### 移行設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `MIGRATION_BATCH_SIZE` | | `100` | 移行バッチサイズ |
| `MIGRATION_DRY_RUN_DEFAULT` | | `true` | デフォルトでドライラン実行 |
| `MIGRATION_BACKUP_ENABLED` | | `true` | バックアップ有効化 |
| `MIGRATION_VERIFICATION_ENABLED` | | `true` | 移行検証有効化 |

### ログ・デバッグ設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `LOG_LEVEL` | | `INFO` | ログレベル (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `COSMOS_LOG_LEVEL` | | `WARNING` | Cosmos DBログレベル |
| `AZURE_SDK_LOG_LEVEL` | | `WARNING` | Azure SDKログレベル |
| `DEBUG_MODE` | | `false` | デバッグモード |
| `ENABLE_DETAILED_LOGGING` | | `false` | 詳細ログ有効化 |
| `LOG_AZURE_REQUESTS` | | `false` | Azure HTTPリクエストログ |

### パフォーマンス設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `SEARCH_CACHE_TTL_SECONDS` | | `300` | 検索キャッシュTTL（秒） |
| `SEARCH_MAX_CACHE_SIZE` | | `100` | 検索キャッシュ最大サイズ |
| `SEARCH_DEFAULT_PAGE_SIZE` | | `20` | 検索デフォルトページサイズ |
| `SEARCH_MAX_PAGE_SIZE` | | `100` | 検索最大ページサイズ |
| `API_RATE_LIMIT_ENABLED` | | `false` | API制限有効化 |
| `API_MAX_REQUESTS_PER_MINUTE` | | `60` | 1分あたりの最大リクエスト数 |

### 開発・テスト設定

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|-------------|------|
| `DEVELOPMENT_MODE` | | `false` | 開発モード |
| `ENABLE_TEST_DATA` | | `false` | テストデータ有効化 |
| `MOCK_COSMOS_DB` | | `false` | Cosmos DBモック使用 |
| `TEST_TENANT_ID` | | `test_tenant` | テスト用テナントID |
| `TEST_USER_ID` | | `test_user` | テスト用ユーザーID |
| `TEST_DATABASE_NAME` | | `test_chat_history_db` | テスト用データベース名 |

## 🛠️ CLI設定ツール

便利な設定管理コマンドが利用できます：

### 設定診断（推奨）
```bash
python cosmos_history/cli_config.py diagnostics
```

### 設定表示
```bash
# 秘密情報をマスクして表示
python cosmos_history/cli_config.py show

# 秘密情報も含めて表示
python cosmos_history/cli_config.py show --show-secrets
```

### 設定検証のみ
```bash
python cosmos_history/cli_config.py validate
```

### 必須設定チェックのみ
```bash
python cosmos_history/cli_config.py check-required
```

### 設定をJSONファイルに出力
```bash
python cosmos_history/cli_config.py export config.json
```

### 推奨.env設定を表示
```bash
python cosmos_history/cli_config.py suggest-env
```

## 🔐 認証方式

### 1. API Key認証（推奨・簡単）

```bash
COSMOS_DB_API_KEY=your-cosmos-api-key
```

### 2. Azure AD認証（Service Principal）

```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_AUTH_METHOD=azuread
```

### 3. Azure CLI認証

```bash
# Azure CLIでログイン
az login

# 設定
AZURE_AUTH_METHOD=cli
AZURE_PREFER_CLI=true
```

### 4. Managed Identity認証

```bash
AZURE_AUTH_METHOD=msi
```

## 🚨 トラブルシューティング

### よくあるエラー

#### 1. `COSMOS_DB_ENDPOINT is required`
- `.env`ファイルに`COSMOS_DB_ENDPOINT`を設定してください
- エンドポイントは`https://`で始まる必要があります

#### 2. `Authentication failed`
- API Keyまたは Azure AD認証情報を確認してください
- Azure AD の場合、Service Principal に適切な権限があることを確認してください

#### 3. `Database/Container not found`
- Cosmos DBアカウントにデータベース・コンテナーが作成されていることを確認してください
- 自動作成されない場合は、手動で作成するか Azure環境セットアップガイドを参照してください

### 設定診断の実行

問題がある場合は、まず設定診断を実行してください：

```bash
python cosmos_history/cli_config.py diagnostics
```

診断結果に基づいて、不足している設定や間違った設定を修正してください。

## 📚 関連ドキュメント

- [Azure環境セットアップガイド](AZURE_SETUP_GUIDE.md)（次のタスクで作成予定）
- [API仕様書](API_SPECIFICATION.md)（後のタスクで作成予定）
- [.env.example](.env.example) - 設定例ファイル

## 🔍 設定例

### 最小構成（API Key認証）
```bash
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_API_KEY=your-api-key
```

### 本格運用構成（Azure AD認証）
```bash
# Cosmos DB
COSMOS_DB_ENDPOINT=https://prod-cosmos.documents.azure.com:443/
COSMOS_DB_DATABASE_NAME=production_chat_db
COSMOS_DB_THROUGHPUT_MODE=provisioned
COSMOS_DB_MAX_THROUGHPUT=1000

# Azure AD認証
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_SECRET=your-secret
AZURE_TENANT_ID=87654321-4321-4321-4321-210987654321
AZURE_AUTH_METHOD=azuread

# パフォーマンス最適化
SEARCH_CACHE_TTL_SECONDS=600
SEARCH_MAX_CACHE_SIZE=200
API_RATE_LIMIT_ENABLED=true

# ログ
LOG_LEVEL=WARNING
ENABLE_DETAILED_LOGGING=false
```

### 開発環境構成
```bash
# 基本設定
COSMOS_DB_ENDPOINT=https://dev-cosmos.documents.azure.com:443/
COSMOS_DB_API_KEY=dev-api-key
COSMOS_DB_DATABASE_NAME=dev_chat_db

# 開発設定
DEVELOPMENT_MODE=true
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_DETAILED_LOGGING=true
MOCK_COSMOS_DB=false

# テストデータ
ENABLE_TEST_DATA=true
```