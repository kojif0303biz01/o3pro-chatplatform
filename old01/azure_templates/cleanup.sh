#!/bin/bash

# 失敗したデプロイメントのクリーンアップスクリプト

set -e

RESOURCE_GROUP_NAME="rg-cosmos-chat"

log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# リソースグループの内容を確認
check_resources() {
    log_info "リソースグループ内のリソースを確認中..."
    
    resources=$(az resource list --resource-group $RESOURCE_GROUP_NAME --query "[].{name:name, type:type, provisioningState:properties.provisioningState}" -o table)
    
    if [ -z "$resources" ] || [ "$resources" = "[]" ]; then
        log_info "リソースグループにリソースがありません"
    else
        echo "$resources"
    fi
}

# 失敗したCosmos DBアカウントを削除
cleanup_cosmos_account() {
    log_info "失敗したCosmos DBアカウントを確認中..."
    
    cosmos_accounts=$(az cosmosdb list --resource-group $RESOURCE_GROUP_NAME --query "[].name" -o tsv)
    
    if [ -n "$cosmos_accounts" ]; then
        for account in $cosmos_accounts; do
            log_warn "Cosmos DBアカウントを削除中: $account"
            az cosmosdb delete --resource-group $RESOURCE_GROUP_NAME --name $account --yes
            log_info "削除完了: $account"
        done
    else
        log_info "削除対象のCosmos DBアカウントはありません"
    fi
}

# リソースグループ全体を削除する選択肢
delete_resource_group() {
    log_warn "リソースグループ全体を削除します: $RESOURCE_GROUP_NAME"
    
    read -p "本当にリソースグループ全体を削除しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        az group delete --name $RESOURCE_GROUP_NAME --yes --no-wait
        log_info "リソースグループの削除を開始しました（非同期）"
        log_info "削除完了まで数分かかる場合があります"
    else
        log_info "リソースグループの削除をキャンセルしました"
    fi
}

# メイン処理
main() {
    echo "=========================================="
    echo "🧹 失敗したデプロイメントのクリーンアップ"
    echo "=========================================="
    
    # Azure CLI ログイン確認
    if ! az account show &> /dev/null; then
        log_error "Azure CLI にログインしていません"
        exit 1
    fi
    
    # リソース確認
    check_resources
    
    echo
    echo "クリーンアップオプション:"
    echo "1. 失敗したCosmos DBアカウントのみ削除"
    echo "2. リソースグループ全体を削除"
    echo "3. 何もしない"
    
    read -p "選択してください (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            cleanup_cosmos_account
            log_info "個別リソース削除完了"
            ;;
        2)
            delete_resource_group
            ;;
        3)
            log_info "クリーンアップをキャンセルしました"
            ;;
        *)
            log_error "無効な選択です"
            exit 1
            ;;
    esac
    
    echo
    log_info "クリーンアップ処理完了"
    log_info "修正済みのARMテンプレートで再デプロイしてください:"
    log_info "  ./deploy.sh"
}

main "$@"