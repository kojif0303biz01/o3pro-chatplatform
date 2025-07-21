#!/bin/bash

# Azure Service Principal作成スクリプト
# GitHub Actions認証用

set -e

echo "🚀 Azure Service Principal作成を開始します..."

# 設定
RESOURCE_GROUP="rg-poc-apps"
SP_NAME="sp-pocapp-github"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "📋 設定情報:"
echo "  リソースグループ: $RESOURCE_GROUP"
echo "  サービスプリンシパル名: $SP_NAME"
echo "  サブスクリプション: $SUBSCRIPTION_ID"
echo ""

# 既存のサービスプリンシパルがあれば削除
echo "🔍 既存のサービスプリンシパルを確認中..."
EXISTING_SP=$(az ad sp list --display-name "$SP_NAME" --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ ! -z "$EXISTING_SP" ]; then
    echo "⚠️  既存のサービスプリンシパルが見つかりました。削除します..."
    az ad sp delete --id "$EXISTING_SP"
    echo "✅ 削除完了"
fi

# 新しいサービスプリンシパルを作成
echo "🔨 新しいサービスプリンシパルを作成中..."
SP_JSON=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role "Contributor" \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --output json)

echo "✅ サービスプリンシパル作成完了"
echo ""

# 結果をパース
CLIENT_ID=$(echo $SP_JSON | jq -r .appId)
CLIENT_SECRET=$(echo $SP_JSON | jq -r .password)
TENANT_ID=$(echo $SP_JSON | jq -r .tenant)

echo "📌 GitHub Secretsに設定する値:"
echo "================================="
echo "Secret Name: AZURE_CLIENT_ID"
echo "Value: $CLIENT_ID"
echo ""
echo "Secret Name: AZURE_CLIENT_SECRET"
echo "Value: $CLIENT_SECRET"
echo ""
echo "Secret Name: AZURE_TENANT_ID"
echo "Value: $TENANT_ID"
echo ""
echo "Secret Name: AZURE_SUBSCRIPTION_ID"
echo "Value: $SUBSCRIPTION_ID"
echo "================================="
echo ""

# ACR用の追加権限を設定
echo "🔐 ACR用権限を追加中..."
az role assignment create \
    --assignee "$CLIENT_ID" \
    --role "AcrPush" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/acrpocapps" \
    2>/dev/null || echo "⚠️  ACR権限追加をスキップ (ACRが存在しない可能性)"

# 権限確認
echo "🔍 権限を確認中..."
az role assignment list \
    --assignee "$CLIENT_ID" \
    --resource-group "$RESOURCE_GROUP" \
    --output table

echo ""
echo "✅ セットアップ完了!"
echo ""
echo "📝 次のステップ:"
echo "1. GitHub リポジトリの Settings > Secrets and variables > Actions に移動"
echo "2. 上記の4つのSecretを追加"
echo "3. 値をコピー&ペーストする際は、前後の空白文字に注意"
echo "4. GitHub Actionsワークフローを再実行"
echo ""

# テスト用コマンドを出力
echo "🧪 ローカルテスト用コマンド:"
echo "az login --service-principal --username $CLIENT_ID --password '$CLIENT_SECRET' --tenant $TENANT_ID"
echo "az group show --name $RESOURCE_GROUP"