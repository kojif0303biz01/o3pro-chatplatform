# コンテナ化ガイド - O3-Pro Chat Platform

## 概要

このドキュメントでは、O3-Pro Chat PlatformのAzure Container Appsへのデプロイ手順を説明します。

## アーキテクチャ

```
Azure Container Apps Environment (env-poc-apps)
├── o3pro-api (FastAPI Backend)
│   ├── REST API エンドポイント
│   ├── WebSocket サポート
│   └── Azure OpenAI / Cosmos DB 連携
└── o3pro-functions (Azure Functions)
    ├── バックグラウンドジョブ処理
    ├── 定期タスク実行
    └── イベント駆動処理
```

## 前提条件

- Azure CLI インストール済み
- Docker Desktop インストール済み
- GitHub アカウントとリポジトリ
- Azure サブスクリプション

## セットアップ手順

### 1. ACR (Azure Container Registry) の作成

```bash
# ACRセットアップスクリプトの実行
./infrastructure/scripts/setup-acr.sh
```

### 2. ローカルでのビルドとテスト

```bash
# Dockerイメージのビルド
docker-compose build

# ローカルテスト
docker-compose up -d

# 動作確認
curl http://localhost:8000/health
```

### 3. サービスプリンシパルの作成とGitHub Secrets設定

#### サービスプリンシパル作成
```bash
# サービスプリンシパル作成
az ad sp create-for-rbac \
  --name "sp-o3pro-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-poc-apps \
  --json-auth
```

#### GitHub Secretsの設定
以下の1つのシークレットをGitHubリポジトリに設定：

- **Name**: `AZURE_CREDENTIALS`
- **Value**: サービスプリンシパル作成コマンドの出力JSON全体

例：
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", 
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 4. デプロイの実行

```bash
# containerizationブランチにプッシュ
git add .
git commit -m "feat: コンテナ化設定完了"
git push origin containerization

# GitHub Actionsが自動的にデプロイを実行
```

## 環境変数の管理

### 開発環境 (.env)
```env
API_KEY=test-api-key-123
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
COSMOS_DB_ENDPOINT=https://xxx.documents.azure.com:443/
COSMOS_DB_API_KEY=xxx
```

### 本番環境 (Container Apps)
環境変数はContainer Apps設定またはKey Vaultから注入されます。

## スケーリング設定（POC/開発環境）

### API (o3pro-api)
- 最小レプリカ: 0（コスト削減のため）
- 最大レプリカ: 1（POCなので1インスタンスで十分）
- HTTPリクエスト: 100同時接続でスケール（1インスタンス想定）

### Functions (o3pro-functions)
- 最小レプリカ: 0（イベント駆動）
- 最大レプリカ: 2（POCなので最小限）
- キュー長: 5メッセージでスケール
- HTTPリクエスト: 10同時接続でスケール

**注意**: 本番環境では要件に応じてスケール設定を調整してください。

## 監視とログ

### Application Insights
- パフォーマンスメトリクス
- エラートラッキング
- カスタムイベント

### Container Apps ログ
```bash
# ログの確認
az containerapp logs show \
  --name o3pro-api \
  --resource-group rg-poc-apps \
  --follow
```

## トラブルシューティング

### GitHub Actions認証エラー (解決済み)
**問題**: "Using auth-type: SERVICE_PRINCIPAL. Not all values are present"

**原因**: ワークフロー内の環境変数参照エラー
- `${{ env.RESOURCE_GROUP }}`が存在しない環境変数を参照していた

**解決方法**: 
```yaml
# 修正前（エラー）
RESOURCE_GROUP: ${{ env.RESOURCE_GROUP }}

# 修正後（正常）
RESOURCE_GROUP: rg-poc-apps
```

**対策**: 
- デバッグ機能を追加してGitHub Secretsの状態確認
- 環境変数参照の正確性検証
- 詳細なトラブルシューティングガイド作成

### イメージプルエラー
```bash
# ACR認証情報の確認
az acr credential show --name acrpocapps
```

### ヘルスチェック失敗
```bash
# コンテナの状態確認
az containerapp revision list \
  --name o3pro-api \
  --resource-group rg-poc-apps
```

### 環境変数の問題
```bash
# 環境変数の確認
az containerapp show \
  --name o3pro-api \
  --resource-group rg-poc-apps \
  --query properties.template.containers[0].env
```

## セキュリティベストプラクティス

1. **非rootユーザー実行**: Dockerfileで`appuser`を使用
2. **マルチステージビルド**: 最小限のランタイムイメージ
3. **ヘルスチェック**: 定期的な生存確認
4. **シークレット管理**: Key Vault統合
5. **ネットワーク分離**: VNet統合（将来実装）

## 次のステップ

1. Key Vault統合によるシークレット管理
2. Application Insights設定
3. Static Web Apps (React Frontend) デプロイ
4. HTTPS/TLS証明書設定
5. カスタムドメイン設定