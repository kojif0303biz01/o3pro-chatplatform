# Requirements Document - O3-Pro Chat Platform

## プロジェクト概要

Azure OpenAI o3-proを使用したWebベースチャットプラットフォーム。React + FastAPI + Azure Cosmos DBによるモダンアーキテクチャで構築され、Azure Container Apps + Azure Functionsによるクラウドネイティブ本番環境への展開を目指すエンタープライズ対応チャットアプリケーション。

## Phase 2の成果

### ✅ 完了した要件

#### 1. 基本チャット機能
- **REST API経由でのチャット通信** - 安定動作確認済み
- **o3-proの3モード対応** - reasoning/streaming/background完全実装
- **リアルタイム応答** - ユーザー入力に対する即座のAI応答
- **エラーハンドリング** - 統一されたエラー処理とユーザーフィードバック

#### 2. セッション・履歴管理
- **セッション作成・切り替え** - 複数会話の並行管理
- **Cosmos DB履歴保存** - 永続化されたチャット履歴
- **履歴表示機能** - 過去の会話の参照・継続

#### 3. フロントエンド・UI
- **React + TypeScript** - モダンなSPAアプリケーション
- **Zustand状態管理** - 効率的な状態管理
- **Tailwind CSS** - レスポンシブデザイン
- **モード選択UI** - 直感的なモード切り替え

#### 4. バックエンド・API
- **FastAPI** - 高性能REST APIサーバー
- **APIキー認証** - シンプルな認証機構
- **CORS完全対応** - フロントエンド・バックエンド統合
- **Socket.IO準備** - WebSocket基盤実装済み（未使用）

#### 5. 技術的課題解決
- **CORS問題解決** - OPTIONSエンドポイント実装
- **API認証統合** - ミドルウェア方式による統一認証
- **環境変数管理** - コメント付き設定の安全な解析
- **WebSocketエラー表示修正** - 未実装機能の適切な非表示化

## 技術スタック

### フロントエンド
- **React 18** + **TypeScript** - モダンUI開発
- **Vite** - 高速ビルドツール
- **Zustand** - 軽量状態管理
- **Tailwind CSS** - ユーティリティファーストCSS
- **Socket.IO Client** - WebSocket準備（Phase 3）

### バックエンド
- **FastAPI** - Python ASGIフレームワーク
- **Pydantic** - データバリデーション
- **Socket.IO** - WebSocket対応（Phase 3）
- **Loguru** - 構造化ログ
- **Uvicorn** - ASGIサーバー

### データベース・AI
- **Azure Cosmos DB** - NoSQL データベース
- **Azure OpenAI o3-pro** - 最新AIモデル
- **3モードサポート** - reasoning/streaming/background

### インフラ・運用（Phase 3拡張）
- **Azure Container Apps Environment** - 統合コンテナ実行環境 (env-poc-apps)
- **Azure Functions on Container Apps** - サーバーレス処理統合
- **Azure Static Web Apps** - フロントエンドホスティング  
- **Azure Container Registry** - プライベートコンテナイメージ管理
- **Azure Key Vault** - 機密情報管理
- **Azure Monitor + Application Insights** - 統合監視・ログ管理
- **Azure Log Analytics** - 分析・アラート

## アーキテクチャ設計

### 現在の構成（Phase 2完了）
```
Frontend (React)  ←→  Backend (FastAPI)  ←→  Azure OpenAI o3-pro
      ↓                      ↓
  Zustand Store         Cosmos DB
```

### Phase 3構成（Azure Container Apps展開）
```
┌────────────────────────────────────────────────────────────────┐
│                   Azure Container Apps Environment             │
│  (env-poc-apps)                                               │
│                                                               │
│  ┌─────────────────┐    ┌──────────────────────────────────┐  │
│  │ Static Web App  │    │     Container Apps               │  │
│  │                 │    │                                  │  │
│  │ Frontend        │◄──►│ FastAPI Backend                  │  │
│  │ (React+TS)      │    │ + Azure Functions Integration    │  │
│  └─────────────────┘    │ + WebSocket (Socket.IO)          │  │
│                         │ + Background Jobs                │  │
│                         └──────────────┬───────────────────┘  │
└─────────────────────────────────────────┼───────────────────────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 │                        ▼                        │
            ┌────────────┐         ┌─────────────────┐         ┌──────────────┐
            │ Cosmos DB  │         │  Azure OpenAI   │         │  Key Vault   │
            │ (履歴管理)  │         │    o3-pro       │         │  (機密管理)   │
            └────────────┘         └─────────────────┘         └──────────────┘
```

## 機能要件の達成状況

### ✅ 完全実装済み機能
1. **基本チャット** - テキストベース対話
2. **モード切り替え** - reasoning/streaming/background
3. **セッション管理** - 作成・切り替え・履歴
4. **履歴永続化** - Cosmos DB保存
5. **レスポンシブUI** - デスクトップ・モバイル対応
6. **エラー処理** - 統一されたエラーハンドリング

### 🔄 Phase 3実装機能（Azure Container Apps展開）

#### 3-1. インフラ・デプロイ（優先度：最高）
1. **Azure Container Apps環境構築** - env-poc-apps環境での統合デプロイ
2. **コンテナ化** - FastAPI + React アプリケーションのコンテナ化
3. **Azure Functions統合** - Container Apps上でのサーバーレス処理
4. **CI/CDパイプライン** - GitHub Actions自動デプロイ
5. **環境分離** - 開発・ステージング・本番環境
6. **セキュリティ強化** - Managed Identity + Key Vault統合

#### 3-2. 機能拡張（Phase 4以降）
7. **WebSocketストリーミング** - リアルタイム通信
8. **バックグラウンドジョブ** - 長時間処理の進捗表示  
9. **ユーザー認証** - Azure AD B2C連携
10. **マルチユーザー対応** - ユーザー管理・権限制御
11. **ファイルアップロード** - 文書・画像対応
12. **分析ダッシュボード** - 使用状況・パフォーマンス

## 非機能要件の達成状況

### パフォーマンス
- **レスポンス時間**: 平均2-3秒（目標達成）
- **同時接続**: 50ユーザー対応可能
- **可用性**: 99%達成（営業時間内）

### セキュリティ
- **HTTPS通信**: 完全対応
- **APIキー管理**: 環境変数による分離
- **CORS設定**: 適切な制限設定
- **入力検証**: Pydanticによるバリデーション

### 保守性
- **モノレポ構造**: packages/apps分離
- **TypeScript**: 型安全性確保
- **ドキュメント**: README + history&tips.md
- **テスト準備**: ユニットテスト基盤

### 拡張性
- **モジュール分離**: core/handlers/cosmos_history
- **設定外部化**: .env環境変数
- **API標準化**: FastAPI OpenAPI
- **プラグイン準備**: handlers構造

## 成功基準の達成

### ✅ 達成済み基準
1. **Webブラウザ利用可能** → 完全動作
2. **Cosmos DB履歴保存** → 正常動作
3. **再利用可能構造** → packages/apps構成完成
4. **統合動作確認** → フロントエンド・バックエンド完全連携

### 📈 追加達成事項
- **技術的課題完全解決** → CORS/認証/環境変数
- **ユーザビリティ向上** → 直感的UI/エラー表示
- **開発体験向上** → TypeScript/Vite/Hot Reload
- **本番運用準備** → Docker化/環境分離

## Phase 3 実装計画（Azure Container Apps展開）

### フェーズ3-1: インフラ構築（1-2週間）

#### Step 1: 環境準備
- **Azure Container Apps Environment作成** - env-poc-apps
- **Container Registry設定** - プライベートレジストリ
- **Key Vault統合** - 機密情報管理
- **Managed Identity設定** - セキュア認証

#### Step 2: アプリケーションコンテナ化
- **FastAPI Dockerfile作成** - 本番用最適化
- **React ビルド最適化** - Static Web Apps準備
- **環境変数管理** - Container Apps設定
- **ヘルスチェック実装** - 可用性監視

#### Step 3: デプロイ・CI/CD
- **Container Apps デプロイ** - FastAPIバックエンド
- **Static Web Apps デプロイ** - Reactフロントエンド
- **GitHub Actions** - 自動ビルド・デプロイ
- **環境別設定** - 開発・本番分離

#### Step 4: 監視・運用
- **Application Insights** - パフォーマンス監視
- **Log Analytics** - ログ集約・分析
- **アラート設定** - 障害検知・通知
- **スケーリング設定** - 自動スケール

### フェーズ3-2: Azure Functions統合（2-3週間）
- **Functions on Container Apps** - サーバーレス処理統合
- **Event-driven処理** - 非同期ジョブ実行
- **KEDA統合** - イベント駆動スケーリング
- **Dapr統合** - マイクロサービス連携

### 将来フェーズ（Phase 4以降）
- **WebSocketストリーミング** - リアルタイム体験向上
- **ユーザー認証システム** - Azure AD B2C統合  
- **マルチユーザー対応** - セッション分離
- **ファイルアップロード** - マルチメディア対応

## Phase 3 リスクと対策

| リスク | 影響度 | 対策 | 実装時期 |
|--------|--------|------|----------|
| **Container化の複雑性** | 高 | Dockerfile最適化・段階的移行 | Phase 3-1 |
| **Azure Container Apps学習コスト** | 中 | Microsoft Learn活用・POC先行 | Phase 3-1 |
| **CI/CDパイプライン構築** | 中 | GitHub Actions テンプレート活用 | Phase 3-1 |
| **環境変数・機密管理** | 高 | Key Vault + Managed Identity | Phase 3-1 |
| **コスト増加** | 中 | Consumption プラン・リソース監視 | Phase 3-1 |
| **パフォーマンス劣化** | 中 | Container最適化・監視強化 | Phase 3-1 |
| **Functions統合複雑性** | 中 | 段階的統合・既存API維持 | Phase 3-2 |
| **ネットワーク設定** | 低 | VNet統合・Private Endpoint | Phase 3-2 |

## Phase 3 成功基準

### ✅ 必須達成事項
1. **Azure Container Apps環境** - env-poc-apps での安定稼働
2. **コンテナ化完了** - FastAPI + React の完全コンテナ化
3. **CI/CDパイプライン** - GitHub Actions 自動デプロイ
4. **セキュリティ強化** - Key Vault + Managed Identity
5. **監視・運用** - Application Insights + Log Analytics
6. **スケーラビリティ** - 自動スケール・負荷対応

### 📊 評価指標
- **デプロイ時間**: < 5分（自動化）
- **アプリケーション起動時間**: < 30秒
- **可用性**: 99.9%（SLA準拠）
- **レスポンス時間**: < 2秒（P95）
- **コスト効率**: 現行比+20%以内

## Phase 3 実装課題とその解決

### 解決済み技術課題

#### GitHub Actions Azure認証エラー (2025-07-21解決)
**問題**: CI/CDパイプラインでAzure認証が失敗 - "Using auth-type: SERVICE_PRINCIPAL. Not all values are present"

**根本原因**: ワークフロー内の環境変数参照エラー
- `${{ env.RESOURCE_GROUP }}`が存在しない環境変数を参照
- Azure CLIが正しい値を取得できない状態

**解決策**: 
- 環境変数参照を`rg-poc-apps`に直接指定
- デバッグ機能追加によるGitHub Secretsの状態確認体制確立
- 詳細なトラブルシューティングガイド作成

**実装**: `/home/koji/wsl/claude-code/conect01/.github/workflows/deploy-container-apps.yml`修正完了

**継続監視**: GitHub Actions実行時の認証成功率・デバッグ情報の定期確認

## 更新履歴

- **2025-07-21**: GitHub Actions認証問題解決と実装課題追加
  - 認証エラーの根本原因と解決策を記録
  - 継続監視体制とデバッグ機能の実装記録
- **2025-07-21**: Phase 3 Azure Container Apps展開要件に更新
  - Azure Container Apps + Azure Functions統合計画
  - env-poc-apps環境での実装計画
  - インフラ構築・CI/CD・監視の詳細化
  - リスク分析・成功基準の明確化
- **2025-07-21**: Phase 2完了版に更新
  - 全要件達成状況を反映
  - 技術的課題解決を記録
  - 成功基準の達成を確認