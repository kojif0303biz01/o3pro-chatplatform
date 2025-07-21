# Bicep デプロイメント - 既知の問題

⚠️ **注意**: このディレクトリのBicepファイルには現在解決されていない問題があります。

## 🔴 現在の問題

### エラー内容
```
ERROR: Unhandled exception. System.InvalidOperationException: The URI is not a local file path.
   at Bicep.IO.Abstraction.IOUri.GetLocalFilePath()
```

### 発生状況
- **日時**: 2025-07-20
- **環境**: WSL2 Linux環境
- **Bicep CLI**: v0.36.177
- **実行コマンド**: `az deployment group create --template-file main.bicep`

### 影響範囲
- `main.bicep` - Cosmos DB リソース定義
- `deploy-bicep.sh` - Bicep デプロイスクリプト

## ✅ 回避策（使用推奨）

**ARM テンプレートを使用してください:**

```bash
# 成功確認済みの方法
cd ../
./deploy.sh
```

ARM テンプレート (`cosmos-chat-template.json`) は完全に動作し、同じリソースをデプロイできます。

## 🔍 原因分析

1. **URI解決問題**: Bicep CLIがファイルパス解決に失敗
2. **WSL環境固有**: Windows-Linux間のパス変換問題の可能性
3. **Bicep CLI バグ**: 特定バージョンでの既知の問題

## 🚧 修正状況

- **優先度**: 低（ARM テンプレートで代替可能）
- **ステータス**: 調査中
- **代替手段**: ARM テンプレート（動作確認済み）

## 📋 Bicep vs ARM 比較

| 項目 | Bicep | ARM Template |
|------|-------|--------------|
| **構文** | 簡潔 | 詳細 |
| **動作状況** | ❌ エラー | ✅ 動作確認済み |
| **保守性** | 高 | 中 |
| **デプロイ速度** | - | 2-3分 |
| **推奨度** | 将来的 | **現在推奨** |

## 💡 推奨アクション

1. **本番環境**: ARM テンプレートを使用
2. **開発環境**: ARM テンプレートで統一
3. **Bicep修正**: 将来のタスクとして保留

---

**現在は `../deploy.sh` を使用してください。**