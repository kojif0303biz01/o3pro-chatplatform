# Azure OpenAI o3-pro チャットボット 設計仕様書

## 📋 プロジェクト概要

### 目的
既存の`o3_pro_complete_toolkit.py`をモジュール化し、再利用可能なコンポーネント群を構築してチャットボットシステムを開発

### スコープ
- Azure OpenAI o3-proモデルの3つの処理モード対応
- チャット履歴管理（JSON、将来Azure DB）
- 認証・エラーハンドリングの統合
- 段階的テスト・検証による品質保証

---

## 🏗️ システムアーキテクチャ

### 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI Client    │  Chat Bot Core  │    Web Interface       │
│                │                 │    (Future)            │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                Application Service Layer                   │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Reasoning      │   Streaming     │    Background          │
│  Handler        │   Handler       │    Handler             │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Core Service Layer                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Azure Auth     │  Error Handler  │   Chat History         │
│  Manager        │                │   Manager              │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                  External Service Layer                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Azure OpenAI   │   File System   │    Azure Database      │
│   o3-pro API   │   (JSON)        │    (Future)            │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### データフロー図

```
User Input
    │
    ▼
┌─────────────────┐
│  Chat Interface │
│   (CLI/Web)     │
└─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐
│ Chat History    │◄───┤  Session Mgmt   │
│   Manager       │    │                │
└─────────────────┘    └─────────────────┘
    │                           │
    ▼                           ▼
┌─────────────────┐    ┌─────────────────┐
│  Mode Handler   │    │  Azure Auth     │
│ (Reasoning/     │◄───┤   Manager       │
│  Streaming/     │    │                │
│  Background)    │    └─────────────────┘
└─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐
│  Error Handler  │◄───┤  Azure OpenAI   │
│                │    │   o3-pro API   │
└─────────────────┘    └─────────────────┘
    │
    ▼
┌─────────────────┐
│   Response      │
│  Processing     │
└─────────────────┘
    │
    ▼
User Output
```

---

## 📚 モジュール設計詳細

### Core Modules (core/)

#### azure_auth.py
**責務**: Azure OpenAI接続の認証・設定管理

**設計パターン**: Configuration Object Pattern
```python
class O3ProConfig:
    # 設定値の検証とカプセル化
    
class O3ProClient:
    # クライアント接続の抽象化
```

**設計決定**:
- 環境変数からの設定読み込み
- API Key/Azure AD両対応
- 設定妥当性の事前検証
- 機密情報のマスク表示

#### error_handler.py
**責務**: API呼び出しエラーの分類・修正・リトライ

**設計パターン**: Strategy Pattern + Decorator Pattern
```python
class ErrorHandler:
    # エラー分類とリトライ戦略
    
def safe_api_call():
    # 簡易ラッパー関数
```

**設計決定**:
- reasoning.summary自動修正
- 指数バックオフリトライ
- エラータイプ別戦略
- ユーザーフレンドリーメッセージ

#### chat_history.py
**責務**: チャット履歴の永続化・検索・管理

**設計パターン**: Repository Pattern
```python
class ChatHistoryManager:
    # 履歴データの CRUD 操作
```

**設計決定**:
- JSONファイルベース（移行容易性考慮）
- セッション単位の管理
- メタデータ付きメッセージ
- 検索・統計機能

### Handler Modules (handlers/)

#### reasoning_handler.py
**責務**: o3-pro基本推論処理

**設計パターン**: Command Pattern
```python
class ReasoningHandler:
    def basic_reasoning(self, question: str, effort: str) -> Dict[str, Any]
```

**設計決定**:
- low/medium/high effortレベル対応
- 同期処理
- 実行時間測定
- 結果の構造化

#### streaming_handler.py
**責務**: リアルタイムストリーミング応答

**設計パターン**: Observer Pattern + Iterator Pattern
```python
class StreamingHandler:
    def stream_response(self, question: str, effort: str) -> Dict[str, Any]
    def stream_with_callback(self, question: str, callback: Callable, effort: str) -> Dict[str, Any]
    def stream_generator(self, question: str, effort: str) -> Iterator[str]
```

**設計決定**:
- 複数のストリーミング形式対応
- コールバック機能
- ジェネレータ対応
- チャンク数計測

#### background_handler.py
**責務**: 長時間タスクのバックグラウンド処理

**設計パターン**: Async Command Pattern + Polling Pattern
```python
class BackgroundHandler:
    def start_background_task(self, question: str, effort: str) -> Dict[str, Any]
    def check_status(self, job_id: str) -> Dict[str, Any]
    def get_result(self, job_id: str) -> Dict[str, Any]
```

**設計決定**:
- ジョブID管理
- ポーリングベース監視
- 非同期待機対応
- ジョブ状態管理

---

## 🗄️ データモデル設計

### 設定データモデル
```python
@dataclass
class O3ProConfig:
    endpoint: str
    api_key: Optional[str]
    deployment: str
    api_version: str
    client_id: Optional[str]
    client_secret: Optional[str] 
    tenant_id: Optional[str]
```

### セッションデータモデル
```json
{
  "session_id": "string",
  "title": "string", 
  "mode": "reasoning|streaming|background|general",
  "created_at": "ISO8601",
  "last_updated": "ISO8601",
  "message_count": "number",
  "messages": [
    {
      "timestamp": "ISO8601",
      "role": "user|assistant|system",
      "content": "string",
      "metadata": {
        "mode": "string",
        "effort": "low|medium|high",
        "duration": "number",
        "job_id": "string",
        "chunk_count": "number"
      }
    }
  ]
}
```

### APIレスポンスモデル
```python
# 成功レスポンス
{
    "success": True,
    "response": "string",
    "duration": "number",
    "effort": "string",
    "metadata": {}
}

# エラーレスポンス  
{
    "success": False,
    "error": "string",
    "error_type": "string",
    "raw_error": "string"
}
```

---

## 🔄 API設計

### Core API

#### O3ProClient
```python
class O3ProClient:
    def __init__(config: O3ProConfig, auth_method: str)
    def is_ready() -> bool
    def get_client() -> OpenAI
```

#### ErrorHandler
```python
class ErrorHandler:
    def handle_api_call(client, **kwargs) -> Any
    def classify_error(error: Exception) -> ErrorType
    def get_user_friendly_message(error: Exception, error_type: ErrorType) -> str
```

#### ChatHistoryManager
```python
class ChatHistoryManager:
    def start_new_session(mode: str, title: str) -> str
    def add_message(session_id: str, role: str, content: str, metadata: Dict) -> bool
    def get_session_messages(session_id: str) -> List[Dict]
    def search_messages(query: str, session_id: Optional[str]) -> List[Dict]
    def get_statistics() -> Dict
```

### Handler API

#### 統一インターフェース設計
```python
class BaseHandler:
    def __init__(client: O3ProClient)
    def quick_test() -> bool
```

各ハンドラーは統一された初期化とテスト機能を提供

---

## 🛡️ セキュリティ設計

### 認証情報管理
- 環境変数での機密情報管理
- 設定表示時のマスク処理
- メモリ上での機密情報最小化

### API通信セキュリティ
- HTTPS強制
- タイムアウト設定
- リトライ制限

### データ保護
- ローカルJSON暗号化（将来拡張）
- ログからの機密情報除外
- 一時ファイルの安全削除

---

## 🔧 エラーハンドリング戦略

### エラー分類
```python
class ErrorType(Enum):
    REASONING_SUMMARY = "reasoning_summary"    # 自動修正対象
    RATE_LIMIT = "rate_limit"                 # 長時間待機
    TIMEOUT = "timeout"                       # 短時間リトライ  
    AUTH_ERROR = "auth_error"                 # 即座に中断
    NETWORK_ERROR = "network_error"           # 短時間リトライ
    UNKNOWN = "unknown"                       # 標準リトライ
```

### リトライ戦略
- **reasoning.summary**: 自動修正後リトライ
- **rate_limit**: 指数バックオフ + 長時間待機
- **timeout/network**: 標準指数バックオフ
- **auth**: リトライなし
- **unknown**: 標準指数バックオフ

### ユーザー体験
- 技術的エラーの平易な説明
- 進捗表示（リトライ中）
- 適切な待機時間表示

---

## 📊 パフォーマンス設計

### レスポンス時間目標
- **基本推論**: 3-6秒（effortレベル依存）
- **ストリーミング開始**: 1秒以内
- **履歴操作**: 100ms以内

### スケーラビリティ考慮
- セッションファイル分割による大量履歴対応
- バックグラウンド処理による長時間タスク対応
- 将来のAzure DB移行設計

### リソース管理
- メモリ使用量最小化
- ファイルハンドル適切管理
- 不要オブジェクトの即座解放

---

## 🧪 テスト戦略

### テストピラミッド
```
┌─────────────────┐
│  Integration    │  ← API + 履歴管理統合テスト
│     Tests       │
├─────────────────┤
│   Service       │  ← 各ハンドラー単体テスト  
│    Tests        │
├─────────────────┤
│    Unit         │  ← コアモジュール単体テスト
│    Tests        │
└─────────────────┘
```

### テスト種別

#### 単体テスト (test_modules.py)
- モジュールインポート確認
- クラス初期化テスト
- 設定妥当性テスト
- エラーハンドリングロジック

#### API接続テスト (api_connection_test.py)
- 実Azure OpenAI接続
- 各処理モード動作確認
- エラーハンドリング実動作
- パフォーマンス測定

#### 統合テスト (test_chat_history_integration.py)
- API + 履歴管理統合
- エンドツーエンドフロー
- データ整合性確認
- 実用性検証

### テスト自動化
- 依存関係チェック
- 環境設定検証
- 自動クリーンアップ
- 結果レポート生成

---

## 🚀 展開・運用設計

### 環境分離
```
Development → Testing → Staging → Production
     ↓           ↓        ↓          ↓
  Local Test   CI/CD    Azure      Azure
  Environment  Pipeline  Test Env   Prod Env
```

### 設定管理
- 環境別.envファイル
- Azure Key Vault連携（将来）
- 設定妥当性事前チェック

### 監視・ログ
- API呼び出し統計
- エラー発生率監視
- レスポンス時間監視
- 履歴容量監視

### バックアップ・災害復旧
- 履歴データ定期バックアップ
- 設定ファイルバージョン管理
- Azure DB移行パス確保

---

## 📈 将来拡張設計

### 短期拡張 (3ヶ月)
- CLIチャットボット完成
- Webインターフェース追加
- リアルタイム履歴同期

### 中期拡張 (6ヶ月)
- Azure Database移行
- マルチユーザー対応
- 認証・認可システム

### 長期拡張 (1年)
- 他LLMモデル対応
- プラグインシステム
- エンタープライズ機能

---

## 📝 技術的制約・前提

### Azure OpenAI制約
- API version: 2025-04-01-preview固定
- o3-proデプロイメント必須
- レート制限: TPM/RPMに依存

### 開発環境制約
- Python 3.12以上
- 依存ライブラリサイズ考慮
- クロスプラットフォーム対応

### 運用制約
- JSONファイルサイズ制限（将来解決）
- ネットワーク接続必須
- Azure リージョン依存

---

**更新日**: 2025-07-19  
**版**: v1.0  
**承認**: 設計完了・実装開始済み