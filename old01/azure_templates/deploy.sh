#!/bin/bash

# Cosmos History モジュール用 Azure インフラストラクチャ デプロイスクリプト

set -e

# 設定
RESOURCE_GROUP_NAME="rg-cosmos-chat"
LOCATION="japaneast"
TEMPLATE_FILE="cosmos-chat-template.json"
PARAMETERS_FILE="parameters.json"

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
        log_info "インストール手順: https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Azure CLI ログイン確認
    if ! az account show &> /dev/null; then
        log_error "Azure CLI にログインしていません"
        log_info "以下のコマンドでログインしてください: az login"
        exit 1
    fi
    
    # テンプレートファイル存在確認
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "ARMテンプレートファイルが見つかりません: $TEMPLATE_FILE"
        exit 1
    fi
    
    if [ ! -f "$PARAMETERS_FILE" ]; then
        log_error "パラメーターファイルが見つかりません: $PARAMETERS_FILE"
        exit 1
    fi
    
    log_info "前提条件チェック完了"
}

# 現在のサブスクリプション表示
show_subscription() {
    local subscription_info=$(az account show --query '{name:name, id:id, tenantId:tenantId}' -o json)
    log_info "現在のサブスクリプション:"
    echo "$subscription_info" | jq .
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

# テンプレートデプロイ
deploy_template() {
    log_info "ARMテンプレートをデプロイ中..."
    
    local deployment_name="cosmos-chat-deploy-$(date +%Y%m%d-%H%M%S)"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$deployment_name" \
        --template-file "$TEMPLATE_FILE" \
        --parameters "@$PARAMETERS_FILE" \
        --query '{provisioningState:properties.provisioningState, outputs:properties.outputs}' \
        --output json > deployment_output.json
    
    if [ $? -eq 0 ]; then
        log_info "デプロイ完了"
    else
        log_error "デプロイに失敗しました"
        exit 1
    fi
}

# デプロイ結果表示
show_deployment_results() {
    log_info "デプロイ結果:"
    
    if [ -f "deployment_output.json" ]; then
        local outputs=$(cat deployment_output.json | jq -r '.outputs')
        
        echo "=========================================="
        echo "🎉 Cosmos DB インフラストラクチャ構築完了"
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
        
        echo
        echo "📝 次のステップ:"
        echo "  1. 上記の環境変数を .env ファイルに設定してください"
        echo "  2. 設定診断を実行してください:"
        echo "     python cosmos_history/cli_config.py diagnostics"
        echo "  3. テストデータで動作確認を行ってください"
        echo "=========================================="
        
        # .env.generated ファイル作成
        cat > .env.generated << EOF
# Cosmos History モジュール用環境変数（自動生成）
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
        
        log_info ".env.generated ファイルを作成しました"
        
    else
        log_error "デプロイ出力ファイルが見つかりません"
    fi
}

# クリーンアップ
cleanup() {
    log_info "一時ファイルをクリーンアップ中..."
    
    if [ -f "deployment_output.json" ]; then
        rm deployment_output.json
    fi
}

# メイン処理
main() {
    echo "=========================================="
    echo "🚀 Cosmos History Azure デプロイ開始"
    echo "=========================================="
    
    check_prerequisites
    show_subscription
    
    # ユーザー確認
    echo
    read -p "続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "デプロイをキャンセルしました"
        exit 0
    fi
    
    create_resource_group
    deploy_template
    show_deployment_results
    
    log_info "デプロイプロセス完了"
}

# エラー時のクリーンアップ
trap cleanup EXIT

# スクリプト実行
main "$@"