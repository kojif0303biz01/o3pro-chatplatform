#!/bin/bash

# 設定
RESOURCE_GROUP="rg-poc-apps"
ACR_NAME="acrpocapps"
LOCATION="japaneast"

echo "🚀 Azure Container Registry セットアップを開始します..."

# リソースグループの存在確認
echo "📋 リソースグループの確認: $RESOURCE_GROUP"
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "❌ リソースグループが見つかりません: $RESOURCE_GROUP"
    exit 1
fi

# ACRの作成または確認
echo "📦 Azure Container Registry の確認: $ACR_NAME"
if ! az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "🔨 ACRを作成しています..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --location $LOCATION \
        --sku Basic \
        --admin-enabled true
    
    if [ $? -eq 0 ]; then
        echo "✅ ACRが正常に作成されました"
    else
        echo "❌ ACR作成に失敗しました"
        exit 1
    fi
else
    echo "✅ ACRは既に存在します"
fi

# ACR情報の取得
echo "🔍 ACR情報を取得しています..."
LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

echo ""
echo "📌 ACR接続情報:"
echo "   Login Server: $LOGIN_SERVER"
echo "   Username: $USERNAME"
echo ""
echo "🔐 以下の値をGitHub Secretsに設定してください:"
echo "   REGISTRY_NAME: $ACR_NAME"
echo "   ACR_USERNAME: $USERNAME"
echo "   ACR_PASSWORD: [表示されません - Azure Portalで確認]"
echo ""

# Container Apps環境でのACR統合
echo "🔗 Container Apps環境との統合を設定しています..."
az containerapp env dapr-component create \
    --name acr-component \
    --environment env-poc-apps \
    --resource-group $RESOURCE_GROUP \
    --yaml @- <<EOF
componentType: secretstores.azure.keyvault
version: v1
metadata:
  - name: vaultName
    value: "kv-poc-apps"
  - name: azureEnvironment
    value: "AZUREPUBLICCLOUD"
secrets:
  - name: acr-password
    value: "$PASSWORD"
scopes:
  - o3pro-api
  - o3pro-functions
EOF

echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "📝 次のステップ:"
echo "1. GitHub Secretsに上記の値を設定"
echo "2. docker login $LOGIN_SERVER でローカルからACRにログイン"
echo "3. GitHub Actionsワークフローを実行してデプロイ"