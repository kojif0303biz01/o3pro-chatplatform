# Azure環境セットアップガイド

このガイドでは、Cosmos History モジュールを使用するためのAzure環境構築手順を説明します。

## 📋 前提条件

- Azureアカウント（無料試用版でも可）
- Azure CLI または Azure PowerShell
- 適切なAzureサブスクリプションの権限

## 🚀 クイックセットアップ

### Option A: Azure CLI での自動セットアップ（推奨）

```bash
# 1. Azure CLIでログイン
az login

# 2. リソースグループ作成
az group create --name rg-cosmos-chat --location japaneast

# 3. Cosmos DBアカウント作成
az cosmosdb create \
  --resource-group rg-cosmos-chat \
  --name cosmos-chat-$(date +%s) \
  --kind GlobalDocumentDB \
  --locations regionName=japaneast failoverPriority=0 isZoneRedundant=False \
  --default-consistency-level Session \
  --enable-automatic-failover false \
  --enable-multiple-write-locations false \
  --enable-serverless

# 4. データベース作成
az cosmosdb sql database create \
  --resource-group rg-cosmos-chat \
  --account-name YOUR_COSMOS_ACCOUNT_NAME \
  --name chat_history_db

# 5. コンテナー作成
az cosmosdb sql container create \
  --resource-group rg-cosmos-chat \
  --account-name YOUR_COSMOS_ACCOUNT_NAME \
  --database-name chat_history_db \
  --name conversations \
  --partition-key-path "/tenantId"

az cosmosdb sql container create \
  --resource-group rg-cosmos-chat \
  --account-name YOUR_COSMOS_ACCOUNT_NAME \
  --database-name chat_history_db \
  --name messages \
  --partition-key-path "/conversationId"

# 6. 接続文字列取得
az cosmosdb keys list \
  --resource-group rg-cosmos-chat \
  --name YOUR_COSMOS_ACCOUNT_NAME \
  --type connection-strings
```

### Option B: Azure ポータルでの手動セットアップ

#### 1. Cosmos DBアカウント作成

1. [Azure ポータル](https://portal.azure.com) にログイン
2. 「リソースの作成」→ 「Azure Cosmos DB」を選択
3. 以下の設定で作成：
   - **サブスクリプション**: 使用するサブスクリプション
   - **リソースグループ**: 新規作成 `rg-cosmos-chat`
   - **アカウント名**: `cosmos-chat-yourname`（グローバルで一意）
   - **API**: `Core (SQL)`
   - **場所**: `Japan East` または `Japan West`
   - **容量モード**: `サーバーレス`（開発用）または `プロビジョニング済みスループット`（本番用）

#### 2. データベース・コンテナー作成

1. 作成したCosmos DBアカウントを開く
2. 「データエクスプローラー」を選択
3. 「新しいデータベース」をクリック
   - **データベースID**: `chat_history_db`
4. 「新しいコンテナー」で以下を作成：

**会話コンテナー**:
- **データベースID**: `chat_history_db`
- **コンテナーID**: `conversations`
- **パーティションキー**: `/tenantId`

**メッセージコンテナー**:
- **データベースID**: `chat_history_db`
- **コンテナーID**: `messages`
- **パーティションキー**: `/conversationId`

## 🔐 認証設定

### Option 1: API Key認証（簡単・推奨）

```bash
# 接続情報取得
az cosmosdb show \
  --resource-group rg-cosmos-chat \
  --name YOUR_COSMOS_ACCOUNT_NAME \
  --query documentEndpoint

az cosmosdb keys list \
  --resource-group rg-cosmos-chat \
  --name YOUR_COSMOS_ACCOUNT_NAME \
  --query primaryMasterKey
```

環境変数設定：
```bash
COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_API_KEY=your-primary-key
```

### Option 2: Azure AD認証（推奨・本番環境）

#### Service Principal作成

```bash
# 1. Service Principal作成
az ad sp create-for-rbac \
  --name "cosmos-chat-sp" \
  --role "Cosmos DB Account Reader Writer" \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/rg-cosmos-chat

# 2. Cosmos DB組み込みロール割り当て
az cosmosdb sql role assignment create \
  --resource-group rg-cosmos-chat \
  --account-name YOUR_COSMOS_ACCOUNT_NAME \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id YOUR_SERVICE_PRINCIPAL_OBJECT_ID \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/rg-cosmos-chat/providers/Microsoft.DocumentDB/databaseAccounts/YOUR_COSMOS_ACCOUNT_NAME
```

環境変数設定：
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_AUTH_METHOD=azuread
```

## 📊 自動化デプロイ

### Option A: ARMテンプレート使用（推奨）

```bash
# 1. azure_templates ディレクトリに移動
cd azure_templates

# 2. 自動デプロイ実行
./deploy.sh

# 3. 生成された環境変数ファイルを確認
cat .env.generated
```

### Option B: Bicepテンプレート使用（モダン）

```bash
# 1. Bicep ディレクトリに移動
cd azure_templates/bicep

# 2. Bicepデプロイ実行
./deploy-bicep.sh

# 3. 生成された環境変数ファイルを確認
cat .env.bicep
```

### Option C: 手動Azure CLI（カスタマイズ重視）

```bash
# リソース変数設定
RESOURCE_GROUP="rg-cosmos-chat"
COSMOS_ACCOUNT="cosmos-chat-$(date +%s)"
LOCATION="japaneast"

# 1. リソースグループ作成
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Cosmos DBアカウント作成
az cosmosdb create \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_ACCOUNT \
  --kind GlobalDocumentDB \
  --locations regionName=$LOCATION failoverPriority=0 \
  --default-consistency-level Session \
  --enable-serverless

# 3. データベース・コンテナー作成
az cosmosdb sql database create \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --name chat_history_db

az cosmosdb sql container create \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --database-name chat_history_db \
  --name conversations \
  --partition-key-path "/tenantId"

az cosmosdb sql container create \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --database-name chat_history_db \
  --name messages \
  --partition-key-path "/conversationId"

# 4. 接続情報取得
az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query documentEndpoint
az cosmosdb keys list --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query primaryMasterKey
```

## 🛠️ 高度な設定

### インデックスポリシーの最適化

本格運用時には、以下のインデックスポリシーを適用してください：

#### 会話コンテナー最適化
```bash
# 複合インデックス追加（検索性能向上）
az cosmosdb sql container replace \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --database-name chat_history_db \
  --name conversations \
  --indexing-policy '{
    "indexingMode": "consistent",
    "includedPaths": [
      {"path": "/tenantId/?"},
      {"path": "/title/?"},
      {"path": "/participants/*/userId/?"},
      {"path": "/categories/*/categoryId/?"},
      {"path": "/timeline/lastMessageAt/?"}
    ],
    "compositeIndexes": [
      [
        {"path": "/tenantId", "order": "ascending"},
        {"path": "/timeline/lastMessageAt", "order": "descending"}
      ]
    ]
  }'
```

### パフォーマンス設定

#### サーバーレス vs プロビジョニング済み

**サーバーレス（推奨・開発/小規模）**:
- 使用量に応じた課金
- 最大40万RU/s
- 設定不要

**プロビジョニング済み（本番環境）**:
- 固定スループット
- 予測可能なコスト
- 高いスループット要件に対応

```bash
# プロビジョニング済みに変更
az cosmosdb create \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_ACCOUNT \
  --throughput 400 \
  --kind GlobalDocumentDB
```

### セキュリティ強化

#### ネットワークアクセス制限
```bash
# 特定のIPアドレスからのみアクセス許可
az cosmosdb update \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_ACCOUNT \
  --ip-range-filter "192.168.1.0/24,10.0.0.0/8"
```

#### プライベートエンドポイント設定
```bash
# Virtual Network作成
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name vnet-cosmos \
  --address-prefix 10.0.0.0/16

# サブネット作成
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name vnet-cosmos \
  --name subnet-cosmos \
  --address-prefix 10.0.1.0/24

# プライベートエンドポイント作成
az network private-endpoint create \
  --resource-group $RESOURCE_GROUP \
  --name pe-cosmos \
  --vnet-name vnet-cosmos \
  --subnet subnet-cosmos \
  --private-connection-resource-id $(az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query id -o tsv) \
  --connection-name cosmos-connection \
  --group-id Sql
```

### バックアップとディザスタリカバリ

#### 自動バックアップ設定
```bash
# 継続的バックアップ有効化
az cosmosdb update \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_ACCOUNT \
  --backup-policy-type Continuous
```

#### マルチリージョン設定
```bash
# セカンダリリージョン追加
az cosmosdb update \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_ACCOUNT \
  --locations regionName=japaneast failoverPriority=0 \
              regionName=japanwest failoverPriority=1 \
  --enable-automatic-failover
```

## 📊 モニタリングとアラート

### Azure Monitor設定

```bash
# アラートルール作成（高RU使用量）
az monitor metrics alert create \
  --resource-group $RESOURCE_GROUP \
  --name "CosmosDB-HighRU" \
  --scopes $(az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query id -o tsv) \
  --condition "avg TotalRequestUnits > 1000" \
  --description "Cosmos DB RU usage is high"
```

### ログ分析設定

```bash
# Log Analytics Workspace作成
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name law-cosmos-chat

# 診断設定追加
az monitor diagnostic-settings create \
  --name cosmos-diagnostics \
  --resource $(az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query id -o tsv) \
  --workspace $(az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name law-cosmos-chat --query id -o tsv) \
  --logs '[{"category":"DataPlaneRequests","enabled":true}]' \
  --metrics '[{"category":"Requests","enabled":true}]'
```

## 🧪 デプロイ後の検証

### 接続テスト

```bash
# 設定診断実行
python cosmos_history/cli_config.py diagnostics

# テストデータ投入
python -c "
import sys
sys.path.append('.')
from cosmos_history.cosmos_client import test_cosmos_connection
test_cosmos_connection()
"
```

### パフォーマンステスト

```bash
# 基本的な読み書きテスト
python -c "
import sys
sys.path.append('.')
from cosmos_history.cosmos_history_manager import test_cosmos_history_manager
import asyncio
asyncio.run(test_cosmos_history_manager())
"
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. 認証エラー
```bash
# API Key確認
az cosmosdb keys list --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT

# Service Principal権限確認
az role assignment list --assignee $AZURE_CLIENT_ID --scope $(az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query id -o tsv)
```

#### 2. 接続エラー
```bash
# エンドポイント確認
az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query documentEndpoint

# ファイアウォール設定確認
az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query ipRules
```

#### 3. パフォーマンス問題
```bash
# メトリクス確認
az monitor metrics list \
  --resource $(az cosmosdb show --resource-group $RESOURCE_GROUP --name $COSMOS_ACCOUNT --query id -o tsv) \
  --metric "TotalRequestUnits"

# インデックス使用状況確認
az cosmosdb sql container show \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --database-name chat_history_db \
  --name conversations \
  --query "resource.indexingPolicy"
```

## 💰 コスト最適化

### 費用監視

```bash
# 現在の使用量確認
az consumption usage list \
  --start-date $(date -d '1 month ago' '+%Y-%m-%d') \
  --end-date $(date '+%Y-%m-%d') \
  --query "[?contains(instanceName, 'cosmos')]"
```

### 最適化のヒント

1. **サーバーレス使用**: 開発・テスト環境では必ずサーバーレスを選択
2. **TTL設定**: 古いデータの自動削除
3. **インデックス最適化**: 不要なインデックスの削除
4. **クエリ最適化**: 効率的なクエリパターンの使用

```bash
# TTL設定例（メッセージの自動削除）
az cosmosdb sql container update \
  --resource-group $RESOURCE_GROUP \
  --account-name $COSMOS_ACCOUNT \
  --database-name chat_history_db \
  --name messages \
  --ttl 2592000  # 30日後に自動削除
```

## 📚 参考資料

- [Azure Cosmos DB公式ドキュメント](https://docs.microsoft.com/azure/cosmos-db/)
- [Cosmos DB価格計算ツール](https://cosmos.azure.com/capacitycalculator/)
- [ARMテンプレートリファレンス](https://docs.microsoft.com/azure/templates/microsoft.documentdb/databaseaccounts)
- [Bicepドキュメント](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)

## ✅ セットアップチェックリスト

- [ ] Azure CLI インストール・ログイン
- [ ] リソースグループ作成
- [ ] Cosmos DB アカウント作成
- [ ] データベース・コンテナー作成
- [ ] 認証設定（API Key または Azure AD）
- [ ] 環境変数設定（.env ファイル）
- [ ] 設定診断実行
- [ ] 接続テスト
- [ ] インデックス最適化（本番環境）
- [ ] モニタリング設定
- [ ] バックアップ設定
- [ ] セキュリティ設定
