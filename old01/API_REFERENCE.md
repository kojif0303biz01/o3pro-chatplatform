# API リファレンス

**o3-pro Azure OpenAI チャットボット + Cosmos DB履歴管理システム**

---

## 📋 概要

このシステムは、Azure OpenAIのo3-proモデルを使用したチャットボットと、Azure Cosmos DBを使用した履歴管理機能を提供します。

### 主要機能
- ✅ o3-pro推論モード（low/medium/high effort）
- ✅ ストリーミング応答
- ✅ Azure Cosmos DB履歴保存
- ✅ チャット履歴検索
- ✅ TTL（自動削除）設定
- ✅ マルチテナント対応

---

## 🚀 クイックスタート

### 1. 環境設定

```bash
# 1. Python仮想環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. 依存関係インストール
pip install -r requirements.txt

# 3. 環境変数設定
cp .env.cosmos .env  # Cosmos DB設定をコピー
# .envファイルを編集してAzure認証情報を設定
```

### 2. Azure環境構築

```bash
# Cosmos DBデプロイ
cd azure_templates
./deploy.sh

# 生成された設定を確認
cat .env.generated
```

### 3. チャットボット起動

```bash
# メインチャットボット
python simple_chatbot.py

# 履歴検索ツール
python cosmos_search.py --conversations
```

---

## 🔧 コアAPI

### Azure認証 (`core/azure_auth.py`)

#### O3ProConfig
Azure OpenAI接続設定管理クラス

```python
from core.azure_auth import O3ProConfig

config = O3ProConfig()
is_valid = config.validate()  # bool: 設定検証
```

**環境変数**:
- `AZURE_OPENAI_API_KEY` - APIキー
- `AZURE_OPENAI_ENDPOINT` - エンドポイントURL
- `AZURE_OPENAI_DEPLOYMENT_NAME` - デプロイメント名

#### O3ProClient
Azure OpenAI クライアント

```python
from core.azure_auth import O3ProClient

client = O3ProClient(config)
is_ready = client.is_ready()  # bool: 接続確認

# 基本推論
response = client.basic_reasoning(
    messages=[{"role": "user", "content": "質問"}],
    effort="low"  # "low", "medium", "high"
)

# ストリーミング
for chunk in client.streaming_chat(messages):
    print(chunk.choices[0].delta.content, end="")
```

### 履歴管理 (`cosmos_history/`)

#### CosmosHistoryManager
Cosmos DB履歴管理メインクラス

```python
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

# 初期化
config = load_config_from_env()
cosmos_client = CosmosDBClient(config.cosmos_db)
manager = CosmosHistoryManager(cosmos_client, "tenant_id", config)

# 会話作成
conversation = await manager.create_conversation(
    title="新しい会話",
    creator_user_id="user123"
)

# メッセージ追加
message = await manager.add_message(
    conversation_id=conversation.conversation_id,
    sender_user_id="user123",
    sender_display_name="ユーザー",
    content="こんにちは"
)

# 会話取得
conversation = await manager.get_conversation(conversation_id)

# 会話一覧
conversations = await manager.list_conversations(limit=20)

# メッセージ取得
messages = await manager.get_conversation_messages(conversation_id)

# 検索
results = await manager.search_conversations(
    tenant_id="tenant_id",
    query="キーワード",
    limit=10
)
```

### データモデル (`cosmos_history/models/`)

#### ChatConversation
会話データモデル

```python
from cosmos_history.models.conversation import ChatConversation

conversation = ChatConversation(
    id="conv_001",
    tenant_id="tenant_001", 
    conversation_id="conv_001",
    title="会話タイトル",
    # ... その他のフィールド
)

# 辞書変換
dict_data = conversation.to_dict()
cosmos_dict = conversation.to_cosmos_dict()

# 復元
conversation = ChatConversation.from_dict(dict_data)
conversation = ChatConversation.from_cosmos_dict(cosmos_dict)
```

#### ChatMessage
メッセージデータモデル

```python
from cosmos_history.models.message import ChatMessage

message = ChatMessage(
    id="msg_001",
    conversation_id="conv_001",
    tenant_id="tenant_001",
    sender=MessageSender(
        user_id="user123",
        display_name="ユーザー",
        role="user"
    ),
    content=MessageContent(
        text="メッセージ内容",
        content_type="text"
    ),
    timestamp="2025-07-20T12:00:00.000Z"
)
```

---

## 🔍 検索API

### コマンドライン検索 (`cosmos_search.py`)

```bash
# 会話一覧
python cosmos_search.py --conversations

# キーワード検索
python cosmos_search.py --search "検索語"

# メッセージ内容検索
python cosmos_search.py --message-search "内容"

# 特定会話のメッセージ表示
python cosmos_search.py --messages "conversation_id"

# 表示件数制限
python cosmos_search.py --limit 50
```

### プログラム内検索

```python
# 検索サービス
from cosmos_history.search_service import SearchService

search = SearchService(cosmos_client, config)

# 会話検索
results = await search.search_conversations(
    tenant_id="tenant_001",
    query="検索語",
    filters={"status": "active"},
    limit=20
)

# メッセージ検索
messages = await search.search_messages(
    tenant_id="tenant_001", 
    query="内容検索",
    conversation_id="conv_001"  # オプション
)
```

---

## ⚙️ 設定管理

### 環境変数設定 (`.env.cosmos`)

```bash
# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_API_KEY=your-primary-key
COSMOS_DB_DATABASE_NAME=chat_history_db
COSMOS_DB_CONVERSATIONS_CONTAINER=conversations
COSMOS_DB_MESSAGES_CONTAINER=messages

# TTL設定
ENABLE_TTL=true
CONVERSATION_TTL_SECONDS=-1        # -1 = 永続保存
MESSAGE_TTL_SECONDS=-1             # -1 = 永続保存
DEVELOPMENT_TTL_SECONDS=-1         # 開発環境用

# 基本設定
DEFAULT_TENANT_ID=default_tenant
DEFAULT_USER_ID=default_user
DEVELOPMENT_MODE=true

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=o3-pro
```

### プログラム設定

```python
from cosmos_history.config import load_config_from_env, AppConfig

# 環境変数から設定読み込み
config = load_config_from_env()

# 設定検証
is_valid, errors = config.validate_all()

# TTL設定取得
conversation_ttl = config.chat_history.get_conversation_ttl(
    development_mode=config.development.development_mode
)
```

---

## 🎮 ハンドラーAPI

### 推論ハンドラー (`handlers/reasoning_handler.py`)

```python
from handlers import ReasoningHandler

handler = ReasoningHandler(client)

result = handler.process_with_reasoning(
    user_input="質問内容",
    effort_level="medium",  # "low", "medium", "high"
    context_messages=[]     # 過去の会話履歴
)

print(f"回答: {result['content']}")
print(f"実行時間: {result['execution_time']}")
```

### ストリーミングハンドラー (`handlers/streaming_handler.py`)

```python
from handlers import StreamingHandler

handler = StreamingHandler(client)

# ストリーミング応答
for chunk in handler.stream_response(
    user_input="質問内容",
    context_messages=[]
):
    print(chunk, end="", flush=True)
```

### バックグラウンドハンドラー (`handlers/background_handler.py`)

```python
from handlers import BackgroundHandler

handler = BackgroundHandler(client)

# バックグラウンド処理開始
job_id = handler.start_background_job(
    user_input="時間のかかる質問",
    effort_level="high"
)

# 進捗確認
status = handler.get_job_status(job_id)
if status["status"] == "completed":
    result = handler.get_job_result(job_id)
```

---

## 🧪 テストAPI

### テスト実行

```bash
# 全テスト実行
python cosmos_history/tests/test_runner.py

# 個別テスト
python -m pytest cosmos_history/tests/test_models.py
python -m pytest cosmos_history/tests/test_cosmos_client.py
```

### プログラムテスト

```python
# 設定診断
from cosmos_history.cli_config import run_diagnostics
await run_diagnostics()

# 接続テスト
from cosmos_history.cosmos_client import test_cosmos_connection
await test_cosmos_connection()
```

---

## 🚨 エラーハンドリング

### 共通エラー処理 (`core/error_handler.py`)

```python
from core.error_handler import handle_api_error, CosmosDBError

try:
    # Cosmos DB操作
    result = await manager.create_conversation(...)
except CosmosDBError as e:
    handle_api_error(e, context="conversation_creation")
```

### カスタム例外

```python
# Cosmos DB関連
from cosmos_history.cosmos_client import CosmosDBError, ConnectionError

# Azure認証関連
from core.azure_auth import AuthenticationError, ConfigurationError
```

---

## 📊 データ移行

### JSONからCosmos DBへの移行

```python
from cosmos_history.migration_service import MigrationService

migration = MigrationService(cosmos_client, config)

# 移行実行
result = await migration.migrate_from_json(
    json_file_path="chat_history/sessions.json",
    tenant_id="default_tenant",
    dry_run=False  # True: 移行予行演習
)

print(f"移行完了: {result.migrated_count}件")
```

---

## 🔒 セキュリティ

### 認証方式

1. **API Key認証** (推奨・簡単)
2. **Azure AD認証** (Enterprise)
3. **Managed Identity** (Azure環境)

### TTL（自動削除）

```python
# TTL設定例
CONVERSATION_TTL_SECONDS=2592000  # 30日後削除
MESSAGE_TTL_SECONDS=7776000       # 90日後削除
DEVELOPMENT_TTL_SECONDS=-1        # 開発環境は永続保存
```

### データプライバシー

- テナント分離でマルチテナント対応
- ユーザーID別アクセス制御
- 検索可能フィールドの制限

---

## 📈 パフォーマンス

### インデックス最適化

```sql
-- Cosmos DB SQL API
SELECT * FROM c 
WHERE c.tenantId = "tenant_001" 
AND c.timeline.lastMessageAt > "2025-01-01"
ORDER BY c.timeline.lastMessageAt DESC
```

### バッチ処理

```python
# 大量データ処理
batch_size = 100
for batch in migration.get_batches(data, batch_size):
    await migration.process_batch(batch)
```

---

## 🛠️ トラブルシューティング

### よくある問題

1. **接続エラー**
   ```bash
   python cosmos_history/cli_config.py diagnostics
   ```

2. **TTLエラー** 
   - TTL値を -1 または正の整数に設定

3. **認証エラー**
   - API Keyとエンドポイントを確認

4. **Bicepデプロイエラー**
   - ARMテンプレートを使用 (`azure_templates/deploy.sh`)

### ログ確認

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Cosmos DBログ
cosmos_logger = logging.getLogger('azure.cosmos')
cosmos_logger.setLevel(logging.INFO)
```

---

## 📚 関連ドキュメント

- [Azure環境セットアップガイド](AZURE_SETUP_GUIDE.md)
- [設定ガイド](CONFIG_SETUP_GUIDE.md)
- [Cosmos DB設計仕様](COSMOS_DB_DESIGN_SPECIFICATION.md)
- [モジュール仕様書](MODULE_SPECIFICATIONS.md)
- [ファイル状況ガイド](FILE_STATUS_GUIDE.md)

---

**このAPIリファレンスは動作確認済みの機能のみを記載しています。**