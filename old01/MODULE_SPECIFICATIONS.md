# モジュール仕様書

## 📋 概要

Azure OpenAI o3-proチャットボットプロジェクトで開発されたモジュール群の詳細仕様書です。各モジュールは独立して動作し、他のプロジェクトでも再利用可能な設計となっています。

---

## 🏗️ core/ - コアモジュール群

### core/azure_auth.py - Azure認証・設定管理

#### 📁 ファイル概要
Azure OpenAI接続に必要な認証と設定管理を担当

#### 🔧 提供クラス

##### O3ProConfig
設定管理クラス

**初期化**
```python
from core.azure_auth import O3ProConfig

config = O3ProConfig(env_path=".env")  # env_pathは省略可
```

**主要メソッド**
- `validate() -> bool`: 設定妥当性チェック
- `print_config()`: 設定情報表示（機密情報マスク）

**設定項目**
- `endpoint`: Azure OpenAIエンドポイント
- `api_key`: APIキー
- `deployment`: デプロイメント名（デフォルト: "O3-pro"）
- `api_version`: APIバージョン（固定: "2025-04-01-preview"）
- `client_id`, `client_secret`, `tenant_id`: Azure AD認証用

##### O3ProClient
Azure OpenAIクライアント管理クラス

**初期化**
```python
from core.azure_auth import O3ProClient

client = O3ProClient(config, auth_method="api_key")  # "api_key" | "azure_ad" | "auto"
```

**主要メソッド**
- `is_ready() -> bool`: クライアント初期化状態確認
- `get_client()`: OpenAIクライアントインスタンス取得

#### 💡 使用例
```python
from core.azure_auth import O3ProConfig, O3ProClient

# 設定初期化
config = O3ProConfig()
if not config.validate():
    print("設定エラー")
    exit(1)

# クライアント初期化
client = O3ProClient(config, auth_method="api_key")
if client.is_ready():
    print("認証成功")
```

---

### core/error_handler.py - エラーハンドリング

#### 📁 ファイル概要
API呼び出しエラーの分類、自動修正、リトライ機能を提供

#### 🔧 提供クラス・関数

##### ErrorHandler
エラーハンドリングクラス

**初期化**
```python
from core.error_handler import ErrorHandler

handler = ErrorHandler(max_retries=3, base_delay=1.0)
```

**主要メソッド**
- `handle_api_call(client, **kwargs)`: API呼び出しのエラーハンドリング
- `classify_error(error)`: エラータイプ分類
- `get_user_friendly_message(error, error_type)`: ユーザー向けエラーメッセージ生成

##### safe_api_call
簡易API呼び出し関数

**使用方法**
```python
from core.error_handler import safe_api_call

result = safe_api_call(
    client,
    model="O3-pro",
    input="質問内容",
    reasoning={"effort": "low"}
)
```

#### 🚨 エラータイプ
- `REASONING_SUMMARY`: reasoning.summaryエラー（自動修正）
- `RATE_LIMIT`: API利用制限
- `TIMEOUT`: タイムアウト
- `AUTH_ERROR`: 認証エラー
- `NETWORK_ERROR`: ネットワークエラー
- `UNKNOWN`: その他

#### 💡 使用例
```python
from core.error_handler import ErrorHandler

handler = ErrorHandler()
result = handler.handle_api_call(
    client.client,
    model="O3-pro",
    input="テスト質問",
    reasoning={"effort": "low"}
)

if hasattr(result, 'output_text'):
    print(f"成功: {result.output_text}")
else:
    print(f"エラー: {result['error']}")
```

---

### core/chat_history.py - チャット履歴管理

#### 📁 ファイル概要
JSONベースのチャット履歴管理システム

#### 🔧 提供クラス

##### ChatHistoryManager
履歴管理クラス

**初期化**
```python
from core.chat_history import ChatHistoryManager

history = ChatHistoryManager(history_dir="chat_history")
```

**主要メソッド**
- `start_new_session(mode, title)`: 新セッション開始
- `add_message(session_id, role, content, metadata)`: メッセージ追加
- `get_session_messages(session_id)`: セッションメッセージ取得
- `list_sessions(limit)`: セッション一覧取得
- `search_messages(query, session_id)`: メッセージ検索
- `get_statistics()`: 統計情報取得

#### 📊 データ構造

**セッションデータ**
```json
{
  "session_id": "abc12345",
  "title": "テストセッション",
  "mode": "reasoning",
  "created_at": "2025-07-19T12:00:00",
  "last_updated": "2025-07-19T12:05:00",
  "message_count": 4,
  "messages": [...]
}
```

**メッセージデータ**
```json
{
  "timestamp": "2025-07-19T12:01:00",
  "role": "user",
  "content": "質問内容",
  "metadata": {
    "mode": "reasoning",
    "effort": "low",
    "duration": 3.2
  }
}
```

#### 💡 使用例
```python
from core.chat_history import ChatHistoryManager

history = ChatHistoryManager()

# セッション開始
session_id = history.start_new_session("reasoning", "テストチャット")

# メッセージ追加
history.add_message(session_id, "user", "2+2は？")
history.add_message(session_id, "assistant", "4です", {
    "duration": 3.2, "mode": "reasoning"
})

# メッセージ取得
messages = history.get_session_messages(session_id)
```

---

## 🎛️ handlers/ - 処理モードハンドラー群

### handlers/reasoning_handler.py - 基本推論処理

#### 📁 ファイル概要
o3-proの基本推論機能（low/medium/high effort対応）

#### 🔧 提供クラス

##### ReasoningHandler
基本推論ハンドラークラス

**初期化**
```python
from handlers.reasoning_handler import ReasoningHandler

handler = ReasoningHandler(client)  # O3ProClientインスタンス
```

**主要メソッド**
- `basic_reasoning(question, effort)`: 基本推論実行
- `test_all_levels(question)`: 全effortレベルテスト
- `quick_test()`: クイックテスト

#### 💡 使用例
```python
from handlers.reasoning_handler import ReasoningHandler

handler = ReasoningHandler(client)
result = handler.basic_reasoning("2+2は？", effort="low")

if result["success"]:
    print(f"回答: {result['response']}")
    print(f"実行時間: {result['duration']:.1f}秒")
```

---

### handlers/streaming_handler.py - ストリーミング処理

#### 📁 ファイル概要
リアルタイムストリーミング応答処理

#### 🔧 提供クラス

##### StreamingHandler
ストリーミング処理ハンドラークラス

**主要メソッド**
- `stream_response(question, effort)`: ストリーミング実行
- `stream_with_callback(question, callback, effort)`: コールバック付きストリーミング
- `stream_generator(question, effort)`: ジェネレータ形式ストリーミング

#### 💡 使用例
```python
from handlers.streaming_handler import StreamingHandler

handler = StreamingHandler(client)

# 基本ストリーミング
result = handler.stream_response("説明してください", effort="low")

# コールバック付き
def on_chunk(chunk_text):
    print(chunk_text, end='', flush=True)

result = handler.stream_with_callback("質問", on_chunk, effort="low")

# ジェネレータ形式
for chunk in handler.stream_generator("質問", effort="low"):
    print(chunk, end='')
```

---

### handlers/background_handler.py - バックグラウンド処理

#### 📁 ファイル概要
長時間タスクのバックグラウンド処理・ポーリング機能

#### 🔧 提供クラス

##### BackgroundHandler
バックグラウンド処理ハンドラークラス

**主要メソッド**
- `start_background_task(question, effort)`: バックグラウンドタスク開始
- `check_status(job_id)`: ジョブステータス確認
- `get_result(job_id)`: ジョブ結果取得
- `wait_for_completion(job_id, polling_interval, timeout)`: 完了待機（非同期）
- `list_active_jobs()`: アクティブジョブ一覧

#### 💡 使用例
```python
from handlers.background_handler import BackgroundHandler

handler = BackgroundHandler(client)

# バックグラウンドタスク開始
result = handler.start_background_task("複雑な分析", effort="high")
job_id = result["job_id"]

# ステータス確認
while True:
    status = handler.check_status(job_id)
    if status["status"] == "completed":
        final_result = handler.get_result(job_id)
        break
    time.sleep(10)
```

---

## 🧪 テストファイル群

### test_modules.py - モジュール単体テスト

#### 📁 ファイル概要
全モジュールの構造・インポートテスト

**実行方法**
```bash
python test_modules.py
```

**テスト項目**
- 進捗管理システム
- 認証モジュール
- エラーハンドリング
- ハンドラーモジュール群
- モジュール間連携

---

### api_connection_test.py - API接続テスト

#### 📁 ファイル概要
実際のAzure OpenAI接続テスト

**実行方法**
```bash
python api_connection_test.py
```

**テスト項目**
- 設定・クライアント初期化
- 基本推論テスト
- エラーハンドリング機能
- ストリーミングテスト
- safe_api_call関数テスト

---

### test_chat_history_integration.py - 履歴統合テスト

#### 📁 ファイル概要
API呼び出しと履歴管理の統合テスト

**実行方法**
```bash
python test_chat_history_integration.py
```

**テスト項目**
- API + 履歴管理統合
- 質問・回答サイクル
- 履歴検証・検索
- セッション情報・統計

---

## 🚀 統合使用例

### 完全なチャットセッション例

```python
from core import O3ProConfig, O3ProClient, ChatHistoryManager
from handlers import ReasoningHandler, StreamingHandler

# 初期化
config = O3ProConfig()
client = O3ProClient(config, auth_method="api_key")
history = ChatHistoryManager()

# セッション開始
session_id = history.start_new_session("reasoning", "数学の質問")

# 推論ハンドラー
reasoning_handler = ReasoningHandler(client)

# チャットループ
while True:
    question = input("質問: ")
    if question.lower() in ['quit', 'exit']:
        break
    
    # ユーザーメッセージ記録
    history.add_message(session_id, "user", question)
    
    # API呼び出し
    result = reasoning_handler.basic_reasoning(question, effort="low")
    
    if result["success"]:
        print(f"回答: {result['response']}")
        
        # アシスタントメッセージ記録
        metadata = {
            "mode": "reasoning",
            "effort": "low", 
            "duration": result["duration"]
        }
        history.add_message(session_id, "assistant", result["response"], metadata)
    else:
        print(f"エラー: {result['error']}")

# セッション情報表示
session_info = history.get_session_info(session_id)
print(f"セッション終了: {session_info['message_count']}メッセージ")
```

---

## 📝 注意事項

### 環境変数設定
モジュール使用前に以下の環境変数が必要：
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=O3-pro
```

### エラーハンドリング
- 全ての公開メソッドは例外安全
- reasoning.summaryエラーは自動修正
- リトライ機能は指数バックオフ実装

### パフォーマンス
- API呼び出し時間: 3-6秒程度（effortレベルにより変動）
- ストリーミング: チャンク毎のリアルタイム配信
- 履歴管理: JSONファイルベース（大量データ時はAzure DB推奨）

---

**更新日**: 2025-07-19  
**版**: v1.0  
**対応API**: Azure OpenAI 2025-04-01-preview