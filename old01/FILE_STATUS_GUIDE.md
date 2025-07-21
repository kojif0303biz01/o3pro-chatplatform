# プロジェクトファイル状況ガイド

**最終更新**: 2025-07-20

このドキュメントでは、プロジェクト内のファイルの動作状況を明確に分類しています。

## 🟢 動作確認済み（本番使用可能）

### メインプログラム
- ✅ **simple_chatbot.py** - o3-proチャットボット（Cosmos DB統合済み）
- ✅ **cosmos_search.py** - Cosmos DB履歴検索ツール

### コアライブラリ（core/）
- ✅ **azure_auth.py** - Azure OpenAI認証（O3ProConfig, O3ProClient）
- ✅ **azure_universal_auth.py** - 汎用Azure認証（8サービス対応）
- ✅ **error_handler.py** - エラーハンドリング

### ハンドラー（handlers/）
- ✅ **reasoning_handler.py** - 推論モードハンドラー（low/medium/high effort）
- ✅ **streaming_handler.py** - ストリーミング応答ハンドラー
- ✅ **background_handler.py** - バックグラウンド処理ハンドラー

### Cosmos DB履歴管理（cosmos_history/）
- ✅ **config.py** - 統合設定管理（TTL対応）
- ✅ **cosmos_client.py** - Cosmos DBクライアント
- ✅ **cosmos_history_manager.py** - 履歴管理メインクラス
- ✅ **migration_service.py** - データ移行サービス
- ✅ **search_service.py** - 検索サービス
- ✅ **models/conversation.py** - 会話データモデル
- ✅ **models/message.py** - メッセージデータモデル
- ✅ **cli_config.py** - CLI設定ツール
- ✅ **tests/*** - 全テストファイル（100%成功）

### Azure デプロイ（azure_templates/）
- ✅ **cosmos-chat-template.json** - ARM テンプレート（動作確認済み）
- ✅ **deploy.sh** - ARM デプロイスクリプト
- ✅ **parameters.json** - ARM パラメーター
- ✅ **cleanup.sh** - クリーンアップスクリプト

### ローカル履歴管理（chat_history/）
- ✅ **local_history.py** - ローカル履歴管理（フォールバック用）
- ✅ **sessions.json, sessions_index.json** - セッション管理ファイル
- ✅ **各JSONファイル** - 履歴データファイル

### 設定ファイル
- ✅ **.env.cosmos** - Cosmos DB設定（動作確認済み）
- ✅ **requirements.txt** - Python依存関係

## 🟡 部分的動作（制限あり）

### Azure デプロイ（Bicep）
- ⚠️ **azure_templates/bicep/main.bicep** - Bicep テンプレート（コンパイルエラー）
- ⚠️ **azure_templates/bicep/deploy-bicep.sh** - Bicep デプロイスクリプト（エラー）

**問題**: Bicep CLIでのコンパイルエラー（URI関連）
**回避策**: ARM テンプレートを使用（動作確認済み）

## 🔴 非推奨・移行済み（old/）

### 旧バージョンファイル
- ❌ **old/o3_pro_complete_toolkit.py** - 旧統合ツールキット（分割済み）
- ❌ **old/api_connection_test.py** - 旧接続テスト（core/に移行）
- ❌ **old/azure_auth_troubleshoot.py** - 旧認証トラブルシューティング
- ❌ **old/chatbot_core.py** - 旧チャットボットコア
- ❌ **old/simple_o3_test.py** - 旧簡易テスト

**注意**: oldディレクトリ内のファイルは参考用のみ。本番環境では使用しない。

## 📋 ドキュメント

### 技術仕様書（動作確認済み）
- ✅ **AZURE_SETUP_GUIDE.md** - Azure環境構築ガイド
- ✅ **CONFIG_SETUP_GUIDE.md** - 設定ガイド
- ✅ **COSMOS_DB_DESIGN_SPECIFICATION.md** - Cosmos DB設計仕様
- ✅ **COSMOS_DB_IMPLEMENTATION_SPECIFICATION.md** - Cosmos DB実装仕様
- ✅ **MODULE_SPECIFICATIONS.md** - モジュール仕様書
- ✅ **LIBRARY_GUIDE.md** - ライブラリ利用ガイド

### プロジェクト管理
- ✅ **CLAUDE.md** - プロジェクト概要・開発方針
- ✅ **README.md** - プロジェクト説明
- ✅ **core/README.md** - コアライブラリ説明
- ✅ **handlers/README.md** - ハンドラー説明

### 参考資料
- ✅ **docs/azure_v1_api_o3_pro_guide.md** - Azure o3-pro API ガイド
- ✅ **docs/azure_llm_methods_comprehensive.md** - Azure LLM 包括ガイド

## 🎯 推奨使用方法

### 本番環境での起動
```bash
# メインチャットボット起動
python simple_chatbot.py

# 履歴検索
python cosmos_search.py --conversations
python cosmos_search.py --search "キーワード"
```

### 開発・テスト
```bash
# 全テスト実行
python cosmos_history/tests/test_runner.py

# 設定診断
python cosmos_history/cli_config.py diagnostics
```

### Azure環境構築
```bash
# ARM テンプレートでデプロイ（推奨）
cd azure_templates
./deploy.sh

# Bicep は現在エラーのため非推奨
# cd azure_templates/bicep
# ./deploy-bicep.sh  # ❌ エラー
```

## ⚠️ 既知の問題・制限事項

1. **Bicep デプロイエラー**: URI解決の問題でコンパイル失敗
2. **Azure Portal アクセス**: データエクスプローラーでの直接確認が必要な場合あり
3. **非同期処理**: 一部の処理で同期ラッパーを使用

## 🔧 今後の改善予定

1. **パフォーマンス最適化**: インデックス調整、クエリ最適化
2. **Bicep エラー修正**: コンパイル問題の解決
3. **監視・ログ**: より詳細な運用監視機能

---

**このガイドに従って、動作確認済みファイルのみを本番環境で使用してください。**