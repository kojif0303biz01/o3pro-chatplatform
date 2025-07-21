#!/bin/bash

# Cosmos History モジュール用 Bicep デプロイスクリプト

set -e

# 設定
RESOURCE_GROUP_NAME="rg-cosmos-chat"
LOCATION="japaneast"
BICEP_FILE="main.bicep"

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # Azure CLI インストール確認
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI がインストールされていません"
        exit 1
    fi
    
    # Bicep CLI インストール確認
    if ! az bicep version &> /dev/null; then
        log_warn "Bicep CLI がインストールされていません。インストール中..."
        az bicep install
    fi
    
    # Azure CLI ログイン確認
    if ! az account show &> /dev/null; then
        log_error "Azure CLI にログインしていません"
        log_info "以下のコマンドでログインしてください: az login"
        exit 1
    fi
    
    # Bicepファイル存在確認
    if [ ! -f "$BICEP_FILE" ]; then
        log_error "Bicepファイルが見つかりません: $BICEP_FILE"
        exit 1
    fi
    
    log_info "前提条件チェック完了"
}

# リソースグループ作成
create_resource_group() {
    log_info "リソースグループ作成中: $RESOURCE_GROUP_NAME"
    
    if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        log_warn "リソースグループ '$RESOURCE_GROUP_NAME' は既に存在します"
    else
        az group create \
            --name "$RESOURCE_GROUP_NAME" \
            --location "$LOCATION"
        log_info "リソースグループ作成完了"
    fi
}

# Bicepデプロイ
deploy_bicep() {
    log_info "Bicepテンプレートをデプロイ中..."
    
    local deployment_name="cosmos-chat-bicep-$(date +%Y%m%d-%H%M%S)"
    
    # パラメーターを対話的に設定するか、デフォルト値を使用
    local cosmos_account_name="cosmos-chat-$(date +%s)"
    
    echo "デプロイパラメーター:"
    echo "  Cosmos Account Name: $cosmos_account_name"
    echo "  Location: $LOCATION"
    echo "  Capacity Mode: Serverless"
    echo ""
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$deployment_name" \
        --template-file "$BICEP_FILE" \
        --parameters cosmosAccountName="$cosmos_account_name" \
                    location="$LOCATION" \
                    capacityMode="Serverless" \
        --query '{provisioningState:properties.provisioningState, outputs:properties.outputs}' \
        --output json > bicep_deployment_output.json
    
    if [ $? -eq 0 ]; then
        log_info "Bicepデプロイ完了"
    else
        log_error "Bicepデプロイに失敗しました"
        exit 1
    fi
}

# デプロイ結果表示
show_bicep_results() {
    log_info "Bicepデプロイ結果:"
    
    if [ -f "bicep_deployment_output.json" ]; then
        local outputs=$(cat bicep_deployment_output.json | jq -r '.outputs')
        
        echo "=========================================="
        echo "🎉 Bicep Cosmos DB デプロイ完了"
        echo "=========================================="
        
        echo
        echo "📊 リソース情報:"
        echo "  アカウント名: $(echo "$outputs" | jq -r '.cosmosAccountName.value')"
        echo "  エンドポイント: $(echo "$outputs" | jq -r '.cosmosEndpoint.value')"
        echo "  データベース名: $(echo "$outputs" | jq -r '.databaseName.value')"
        echo "  会話コンテナー: $(echo "$outputs" | jq -r '.conversationsContainerName.value')"
        echo "  メッセージコンテナー: $(echo "$outputs" | jq -r '.messagesContainerName.value')"
        
        echo
        echo "🔐 接続情報（.env ファイル用）:"
        echo "  COSMOS_DB_ENDPOINT=$(echo "$outputs" | jq -r '.cosmosEndpoint.value')"
        echo "  COSMOS_DB_API_KEY=$(echo "$outputs" | jq -r '.primaryKey.value')"
        echo "  COSMOS_DB_DATABASE_NAME=$(echo "$outputs" | jq -r '.databaseName.value')"
        echo "  COSMOS_DB_CONVERSATIONS_CONTAINER=$(echo "$outputs" | jq -r '.conversationsContainerName.value')"
        echo "  COSMOS_DB_MESSAGES_CONTAINER=$(echo "$outputs" | jq -r '.messagesContainerName.value')"
        
        # .env.bicep ファイル作成
        cat > .env.bicep << EOF
# Cosmos History モジュール用環境変数（Bicep自動生成）
# $(date)

# Azure Cosmos DB設定
COSMOS_DB_ENDPOINT=$(echo "$outputs" | jq -r '.cosmosEndpoint.value')
COSMOS_DB_API_KEY=$(echo "$outputs" | jq -r '.primaryKey.value')
COSMOS_DB_DATABASE_NAME=$(echo "$outputs" | jq -r '.databaseName.value')
COSMOS_DB_CONVERSATIONS_CONTAINER=$(echo "$outputs" | jq -r '.conversationsContainerName.value')
COSMOS_DB_MESSAGES_CONTAINER=$(echo "$outputs" | jq -r '.messagesContainerName.value')

# 基本設定
DEFAULT_TENANT_ID=default_tenant
DEFAULT_USER_ID=default_user
LOG_LEVEL=INFO

# 開発設定
DEVELOPMENT_MODE=true
DEBUG_MODE=false
EOF
        
        log_info ".env.bicep ファイルを作成しました"
        
    else
        log_error "Bicepデプロイ出力ファイルが見つかりません"
    fi
}

# メイン処理
main() {
    echo "=========================================="
    echo "🚀 Bicep Cosmos History デプロイ開始"
    echo "=========================================="
    
    check_prerequisites
    
    # ユーザー確認
    echo
    read -p "Bicepデプロイを続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Bicepデプロイをキャンセルしました"
        exit 0
    fi
    
    create_resource_group
    deploy_bicep
    show_bicep_results
    
    log_info "Bicepデプロイプロセス完了"
}

# スクリプト実行
main "$@"