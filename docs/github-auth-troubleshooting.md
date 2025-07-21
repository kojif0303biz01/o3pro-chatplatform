# GitHub Actions Azure認証トラブルシューティングガイド

## 問題履歴と解決策

### 発生した問題
GitHub ActionsでAzure認証が失敗する: "Using auth-type: SERVICE_PRINCIPAL. Not all values are present"

### 調査結果
1. **初期の問題**: サービスプリンシパル設定とGitHub Secretsの設定に関する疑い
2. **デバッグ情報追加**: 詳細なログ出力機能を実装
3. **根本原因判明**: ワークフロー内の環境変数参照エラー
   - `${{ env.RESOURCE_GROUP }}` が存在しない環境変数を参照
   - 結果として、Azure CLIコマンドが正しい値を取得できない状態

### 修正内容
- 環境変数参照を `${{ env.RESOURCE_GROUP }}` から `rg-poc-apps` に修正
- デバッグ機能を追加して問題の特定を容易化

### Issue追跡
- この問題はGitHubリポジトリのIssueとして記録
- 継続的な監視とテストが必要

## 解決手順

### 1. サービスプリンシパルの再作成（正しいスコープで）

```bash
# 現在のサブスクリプションIDを取得
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# 既存のサービスプリンシパルを削除（存在する場合）
az ad sp delete --id $(az ad sp list --display-name "sp-pocapp-github" --query "[0].id" -o tsv) 2>/dev/null || true

# 新しいサービスプリンシパルを正しいスコープで作成
az ad sp create-for-rbac \
  --name "sp-pocapp-github" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-poc-apps" \
  --output json > sp-credentials.json

# 結果を表示
cat sp-credentials.json
```

### 2. GitHub Secretsの設定確認

以下の4つのSecretがGitHubリポジトリに正しく設定されているか確認：

1. **AZURE_CLIENT_ID**: `appId` の値
2. **AZURE_CLIENT_SECRET**: `password` の値  
3. **AZURE_TENANT_ID**: `tenant` の値
4. **AZURE_SUBSCRIPTION_ID**: `subscription` の値

### 3. サービスプリンシパルの権限確認

```bash
# サービスプリンシパルの権限を確認
az role assignment list \
  --assignee $(az ad sp list --display-name "sp-pocapp-github" --query "[0].appId" -o tsv) \
  --resource-group rg-poc-apps \
  --output table
```

### 4. Container Registry用の追加権限設定

```bash
# ACRへの権限追加
az role assignment create \
  --assignee $(az ad sp list --display-name "sp-pocapp-github" --query "[0].appId" -o tsv) \
  --role "AcrPush" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-poc-apps/providers/Microsoft.ContainerRegistry/registries/acrpocapps"

az role assignment create \
  --assignee $(az ad sp list --display-name "sp-pocapp-github" --query "[0].appId" -o tsv) \
  --role "AcrPull" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-poc-apps/providers/Microsoft.ContainerRegistry/registries/acrpocapps"
```

### 5. サービスプリンシパルのテスト

```bash
# サービスプリンシパルでログインテスト
az login --service-principal \
  --username $(cat sp-credentials.json | jq -r .appId) \
  --password $(cat sp-credentials.json | jq -r .password) \
  --tenant $(cat sp-credentials.json | jq -r .tenant)

# リソースグループへのアクセステスト
az group show --name rg-poc-apps

# ログアウト
az logout
```

### 6. 代替案: OIDC認証の使用

サービスプリンシパル認証が解決しない場合、OIDC認証を試す：

```bash
# OIDC用のアプリケーション登録
az ad app create \
  --display-name "github-oidc-o3pro" \
  --web-redirect-uris "https://token.actions.githubusercontent.com"

# Federated Credentialの作成
APP_ID=$(az ad app list --display-name "github-oidc-o3pro" --query "[0].appId" -o tsv)

az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-actions",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:kojif0303biz01/o3pro-chatplatform:ref:refs/heads/containerization",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### 7. ワークフローでのOIDC認証

```yaml
- name: Azure Login (OIDC)
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

## デバッグ情報

現在のワークフローにデバッグステップが追加されています：

- GitHub Secretsの存在確認
- 値の長さ確認
- Azure CLI バージョン確認

## チェックリスト

- [ ] サービスプリンシパルが正しいスコープで作成されている
- [ ] GitHub Secretsが4つすべて設定されている
- [ ] シークレットの値にスペースや改行が含まれていない
- [ ] サービスプリンシパルが有効期限内である
- [ ] 必要な権限（Contributor, AcrPush, AcrPull）が付与されている

## 次のステップ

1. 上記手順でサービスプリンシパルを再作成
2. GitHub Secretsを正しく設定
3. デバッグ情報付きでワークフローを実行
4. 失敗する場合はOIDC認証に切り替え