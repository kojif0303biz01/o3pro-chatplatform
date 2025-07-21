# O3-Pro Chat Platform - Phase 2

Azure OpenAI o3-proを使用したWebベースチャットプラットフォーム

## 🎯 Phase 2の概要

React + FastAPI + Azure Cosmos DBを使用したフル機能チャットアプリケーション。Azure OpenAI o3-proの3つのモード（reasoning/streaming/background）をサポート。

## 🏗️ アーキテクチャ

- **フロントエンド**: React + TypeScript + Vite + Zustand
- **バックエンド**: FastAPI + Socket.IO
- **データベース**: Azure Cosmos DB
- **AI**: Azure OpenAI o3-pro
- **認証**: APIキー（POC段階）

## 📁 プロジェクト構造

```
conect01/
├── apps/
│   ├── api/              # FastAPI バックエンド
│   └── web/              # React フロントエンド
├── packages/
│   ├── core/             # Azure認証・共通機能
│   ├── cosmos_history/   # Cosmos DB履歴管理
│   └── handlers/         # o3-pro各モードハンドラー
├── infrastructure/       # デプロイ設定
├── history&tips.md       # 開発履歴・トラブルシューティング
└── old01/               # 旧バージョン・未使用ファイル
```

## 🚀 クイックスタート

### 前提条件
- Python 3.12+
- Node.js 18+
- Azure CLI & Azure subscription

### バックエンド起動
```bash
cd apps/api
source venv/bin/activate
python main.py
```

### フロントエンド起動
```bash
cd apps/web
npm run dev
```

### アクセス
- **Web UI**: http://localhost:5174
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## ✅ Phase 2 完了機能

- **基本チャット機能** - REST API経由での安定した通信
- **セッション管理** - 作成・切り替え・履歴表示
- **Azure OpenAI o3-pro連携** - reasoning/streaming/backgroundモード対応
- **Cosmos DB履歴保存** - 永続化されたチャット履歴
- **レスポンシブUI** - Tailwind CSS使用のモダンUI
- **状態管理** - Zustand使用による効率的な状態管理
- **CORS問題解決** - フロントエンド・バックエンド完全連携
- **エラーハンドリング** - 統一されたエラー処理とユーザーフィードバック

## 🔄 実装予定機能（Phase 3）

- **WebSocketリアルタイムストリーミング** - ライブチャット機能
- **バックグラウンドジョブステータス表示** - 長時間処理の進捗表示
- **ユーザー認証システム** - Azure AD B2C連携
- **マルチユーザー対応** - ユーザー管理・権限制御

## 🛠️ 開発環境セットアップ

### 環境変数設定
ルートの`.env`ファイルに以下を設定：

```bash
# Azure OpenAI設定
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=O3-pro

# Cosmos DB設定
COSMOS_DB_ENDPOINT=your-cosmos-endpoint
COSMOS_DB_API_KEY=your-cosmos-key

# API認証（POC用）
API_KEY=test-api-key-123
```

### 開発コマンド

```bash
# バックエンド
cd apps/api && python main.py

# フロントエンド
cd apps/web && npm run dev

# API接続テスト
curl -X POST "http://localhost:8000/api/v1/sessions/" \
  -H "X-API-Key: test-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}'
```

## 📚 ドキュメント

- **開発履歴**: `history&tips.md` - 技術的課題と解決方法
- **アーキテクチャ設計**: packages/各ライブラリのREADME
- **API仕様**: http://localhost:8000/docs （Swagger UI）

## 🔧 技術的ハイライト

### 解決した主要課題
1. **CORS問題** - OPTIONSエンドポイント実装で完全解決
2. **API認証** - ミドルウェア方式による統一認証
3. **WebSocket表示問題** - 未実装機能の適切な非表示化
4. **環境変数管理** - コメント付き設定の安全な解析

### アーキテクチャ決定
- **状態管理**: Zustand（軽量・TypeScript最適）  
- **通信方式**: REST API（安定性重視）+ WebSocket（将来実装）
- **データベース**: Cosmos DB（スケーラビリティ対応）
- **認証**: APIキー（POC） → Azure AD（将来）

## 🛡️ トラブルシューティング

問題が発生した場合：

1. `history&tips.md`の「トラブルシューティングTips」を確認
2. API接続テスト実行
3. 環境変数設定確認
4. ログファイル確認

## 📊 プロジェクト状況

**Phase 2**: ✅ **完了**（2025年7月21日）
- 基本チャット機能完全動作
- フロントエンド・バックエンド統合完了
- Cosmos DB履歴管理実装完了

**Next Phase**: Phase 3 開発準備中
- WebSocketストリーミング機能
- ユーザー認証システム

---

**最終更新**: 2025年7月21日  
**開発ステータス**: Phase 2 完了 → Phase 3 準備中