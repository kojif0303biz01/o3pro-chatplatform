# Azure Cosmos DB チャット履歴管理システム 設計構想書

## 📋 プロジェクト概要

### 目的
現在のローカルJSONファイルベースのチャット履歴管理を、Azure Cosmos DBベースのクラウド管理システムに移行し、検索・読み出し機能を強化する。

### 主要目標
1. **スケーラビリティ**: 大量のチャット履歴に対応
2. **高速検索**: 内容・日時・モードでの複合検索
3. **高可用性**: グローバル分散対応
4. **認証統合**: 既存Azure認証基盤の活用
5. **シームレス移行**: 既存データとAPIの互換性維持

## 🏗️ 全体アーキテクチャ

### システム構成図
```
┌─────────────────────────────────────────────────────────────────┐
│ Application Layer                                               │
├─────────────────────────────────────────────────────────────────┤
│ Simple Chatbot (既存)                                           │
│ ├─ Chat History Interface (新規・既存互換)                        │
│ ├─ Search & Filter Functions (新規)                            │
│ └─ Migration Tools (新規)                                       │
├─────────────────────────────────────────────────────────────────┤
│ Service Layer                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Chat History Services                                           │
│ ├─ CosmosDBHistoryManager (新規メイン)                           │
│ ├─ LocalHistoryManager (既存・後方互換)                          │
│ ├─ SearchService (新規)                                         │
│ ├─ MigrationService (新規)                                      │
│ └─ CacheService (新規・オプション)                               │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure Layer                                            │
├─────────────────────────────────────────────────────────────────┤
│ Azure Services                                                  │
│ ├─ Azure Cosmos DB (NoSQL)                                     │
│ ├─ Azure Authentication (既存)                                  │
│ ├─ Azure Monitor (ログ・メトリクス)                              │
│ └─ Azure Storage (バックアップ・移行用)                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 データモデル設計

### 1. Cosmos DB コンテナ設計

#### コンテナ構成
```json
{
  "database": "chat_history_db",
  "containers": [
    {
      "name": "sessions",
      "partitionKey": "/userId",
      "description": "チャットセッション管理"
    },
    {
      "name": "messages", 
      "partitionKey": "/sessionId",
      "description": "メッセージ詳細管理"
    },
    {
      "name": "user_profiles",
      "partitionKey": "/userId", 
      "description": "ユーザー設定・統計"
    }
  ]
}
```

#### セッションドキュメント構造
```json
{
  "id": "session_uuid",
  "userId": "user_identifier", 
  "sessionId": "79f13509",
  "title": "チャット (reasoning) - 2025-07-20 01:10",
  "mode": "reasoning",
  "createdAt": "2025-07-20T01:10:37.826804Z",
  "updatedAt": "2025-07-20T01:10:44.755908Z", 
  "messageCount": 2,
  "tags": ["work", "development"],
  "summary": "o3-proでの開発質問",
  "lastMessage": "こんにちは！今日はどのようなお手伝いをしましょうか？",
  "metadata": {
    "totalTokens": 150,
    "totalDuration": 8.5,
    "averageResponseTime": 4.25
  },
  "ttl": null,
  "_ts": 1737396644
}
```

#### メッセージドキュメント構造
```json
{
  "id": "message_uuid",
  "sessionId": "79f13509",
  "userId": "user_identifier",
  "role": "assistant",
  "content": "こんにちは！今日はどのようなお手伝いをしましょうか？",
  "timestamp": "2025-07-20T01:10:44.755908Z",
  "metadata": {
    "mode": "reasoning", 
    "effort": "low",
    "duration": 6.928,
    "tokens": 75,
    "model": "o3-pro"
  },
  "searchText": "こんにちは 今日 どのような お手伝い しましょうか",
  "parentMessageId": null,
  "ttl": null,
  "_ts": 1737396644
}
```

### 2. パーティション戦略

#### セッションコンテナ
- **パーティションキー**: `/userId`
- **理由**: ユーザーごとのセッション一覧取得が最も頻繁
- **スケーリング**: ユーザー数に比例して自然分散

#### メッセージコンテナ  
- **パーティションキー**: `/sessionId`
- **理由**: セッション内メッセージの取得が最も頻繁
- **スケーリング**: セッション単位での分散

### 3. インデックス設計

#### セッション検索用インデックス
```json
{
  "indexingPolicy": {
    "indexingMode": "consistent",
    "includedPaths": [
      {"path": "/userId/?"},
      {"path": "/mode/?"},
      {"path": "/createdAt/?"},
      {"path": "/updatedAt/?"},
      {"path": "/title/?"},
      {"path": "/tags/*"},
      {"path": "/lastMessage/?"}
    ],
    "excludedPaths": [
      {"path": "/metadata/*"},
      {"path": "/_etag/?"}
    ],
    "compositeIndexes": [
      [
        {"path": "/userId", "order": "ascending"},
        {"path": "/updatedAt", "order": "descending"}
      ],
      [
        {"path": "/userId", "order": "ascending"}, 
        {"path": "/mode", "order": "ascending"},
        {"path": "/createdAt", "order": "descending"}
      ]
    ]
  }
}
```

#### メッセージ検索用インデックス
```json
{
  "indexingPolicy": {
    "indexingMode": "consistent", 
    "includedPaths": [
      {"path": "/sessionId/?"},
      {"path": "/userId/?"},
      {"path": "/role/?"},
      {"path": "/timestamp/?"},
      {"path": "/searchText/?"},
      {"path": "/metadata/mode/?"}
    ],
    "excludedPaths": [
      {"path": "/content/?"},
      {"path": "/metadata/duration/?"},
      {"path": "/metadata/tokens/?"}
    ],
    "compositeIndexes": [
      [
        {"path": "/sessionId", "order": "ascending"},
        {"path": "/timestamp", "order": "ascending"}
      ],
      [
        {"path": "/userId", "order": "ascending"},
        {"path": "/timestamp", "order": "descending"}
      ]
    ]
  }
}
```

## 🔍 検索機能設計

### 1. 検索タイプ

#### 基本検索
- **キーワード検索**: メッセージ内容での全文検索
- **日時範囲検索**: 作成日・更新日での範囲指定
- **モード検索**: reasoning/streaming/background
- **セッション検索**: タイトル・タグでの検索

#### 高度検索
- **複合条件検索**: 複数条件のAND/OR組み合わせ
- **ファセット検索**: モード・日付・タグでのドリルダウン
- **類似セッション検索**: 内容の類似性ベース
- **ユーザー活動検索**: 特定期間の活動パターン

### 2. 検索クエリ例

#### セッション検索
```sql
-- 最近のreasoningセッション
SELECT * FROM sessions s 
WHERE s.userId = @userId 
  AND s.mode = 'reasoning'
  AND s.updatedAt >= @startDate
ORDER BY s.updatedAt DESC

-- タグベース検索
SELECT * FROM sessions s
WHERE s.userId = @userId
  AND ARRAY_CONTAINS(s.tags, @tag)
ORDER BY s.updatedAt DESC

-- キーワード検索（タイトル・要約）
SELECT * FROM sessions s
WHERE s.userId = @userId
  AND (CONTAINS(s.title, @keyword) OR CONTAINS(s.summary, @keyword))
```

#### メッセージ検索
```sql
-- 内容検索
SELECT * FROM messages m
WHERE m.userId = @userId
  AND CONTAINS(m.searchText, @keyword)
  AND m.timestamp >= @startDate
ORDER BY m.timestamp DESC

-- セッション内検索
SELECT * FROM messages m
WHERE m.sessionId = @sessionId
  AND m.role = @role
ORDER BY m.timestamp ASC

-- 複合検索
SELECT * FROM messages m
WHERE m.userId = @userId
  AND m.metadata.mode = @mode
  AND m.timestamp BETWEEN @startDate AND @endDate
  AND CONTAINS(m.content, @keyword)
```

### 3. 検索パフォーマンス最適化

#### キャッシュ戦略
- **セッション一覧**: Redis/Memory Cache (5分TTL)
- **頻繁検索**: クエリ結果キャッシュ (1分TTL)
- **統計情報**: 日次集計キャッシュ (1時間TTL)

#### ページング戦略
```python
# Cosmos DB継続トークンベースページング
def search_messages(query_params, page_size=20, continuation_token=None):
    query = build_search_query(query_params)
    
    options = {
        "enable_cross_partition_query": True,
        "max_item_count": page_size
    }
    
    if continuation_token:
        options["continuation"] = continuation_token
    
    result = container.query_items(
        query=query,
        parameters=query_params,
        **options
    )
    
    return {
        "items": list(result),
        "continuation_token": result.response_headers.get("x-ms-continuation"),
        "has_more": bool(result.response_headers.get("x-ms-continuation"))
    }
```

## 🔐 認証統合設計

### 1. 既存認証基盤との統合

#### Azure認証フロー
```python
# azure_universal_auth.pyとの統合
from core.azure_universal_auth import AzureAuthManager

class CosmosDBHistoryManager:
    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager
        self.cosmos_client = self._initialize_cosmos_client()
    
    def _initialize_cosmos_client(self):
        # Cosmos DB認証
        auth_result = self.auth_manager.authenticate("cosmos_db")
        if not auth_result.success:
            raise Exception("Cosmos DB認証失敗")
        
        return CosmosClient(
            url=os.getenv("COSMOS_DB_ENDPOINT"),
            credential=auth_result.credential
        )
```

#### ユーザーIDマッピング
```python
class UserIdentityService:
    def get_user_id(self, auth_context) -> str:
        """認証コンテキストからユーザーIDを取得"""
        if auth_context.method == "azure_cli":
            # Azure CLI: subscription + user email
            return f"azurecli_{auth_context.user_email}"
        elif auth_context.method == "service_principal":
            # SP: tenant + client_id  
            return f"sp_{auth_context.tenant_id}_{auth_context.client_id}"
        elif auth_context.method == "api_key":
            # APIキー: 固定ユーザー（開発用）
            return "apikey_default_user"
        else:
            return f"unknown_{uuid.uuid4()}"
```

### 2. アクセス制御

#### データアクセス権限
- **自分のデータのみ**: userId によるフィルタリング
- **管理者アクセス**: 特権ユーザーは全データアクセス可
- **匿名化データ**: 統計・分析用の匿名化ビュー

#### API権限レベル
```python
class PermissionLevel(Enum):
    READ_OWN = "read_own"           # 自分のデータ読み取り
    WRITE_OWN = "write_own"         # 自分のデータ書き込み  
    READ_ALL = "read_all"           # 全データ読み取り
    WRITE_ALL = "write_all"         # 全データ書き込み
    ADMIN = "admin"                 # システム管理
```

## 🚀 移行戦略設計

### 1. 段階的移行アプローチ

#### Phase 1: 並行運用 (4週間)
```python
class HybridHistoryManager:
    def __init__(self):
        self.local_manager = ChatHistoryManager()      # 既存
        self.cosmos_manager = CosmosDBHistoryManager() # 新規
        self.write_both = True  # 両方に書き込み
        self.read_source = "cosmos"  # 読み取りソース
    
    def add_message(self, session_id, role, content, metadata=None):
        # Cosmos DBに書き込み
        cosmos_success = self.cosmos_manager.add_message(session_id, role, content, metadata)
        
        if self.write_both:
            # ローカルにもバックアップ書き込み
            local_success = self.local_manager.add_message(session_id, role, content, metadata)
        
        return cosmos_success
```

#### Phase 2: データ移行 (2週間)
```python
class MigrationService:
    def migrate_all_data(self):
        """全ローカルデータをCosmos DBに移行"""
        
        # セッション一覧取得
        local_sessions = self.local_manager.list_sessions(limit=None)
        
        migration_stats = {
            "total_sessions": len(local_sessions),
            "migrated_sessions": 0,
            "total_messages": 0,
            "migrated_messages": 0,
            "errors": []
        }
        
        for session in local_sessions:
            try:
                # セッション移行
                cosmos_session = self._convert_session_format(session)
                self.cosmos_manager.create_session(cosmos_session)
                
                # メッセージ移行
                messages = self.local_manager.get_session_messages(session["id"])
                for message in messages:
                    cosmos_message = self._convert_message_format(message, session["id"])
                    self.cosmos_manager.add_message_direct(cosmos_message)
                
                migration_stats["migrated_sessions"] += 1
                migration_stats["migrated_messages"] += len(messages)
                
            except Exception as e:
                migration_stats["errors"].append({
                    "session_id": session["id"],
                    "error": str(e)
                })
        
        return migration_stats
```

#### Phase 3: Cosmos DB完全移行 (1週間)
- ローカル読み書き停止
- Cosmos DBのみで動作
- パフォーマンス監視

### 2. データ形式変換

#### セッション変換
```python
def _convert_session_format(self, local_session):
    """ローカルセッション → Cosmos DBセッション"""
    return {
        "id": f"session_{local_session['id']}",
        "userId": self._get_current_user_id(),
        "sessionId": local_session["id"],
        "title": local_session["title"],
        "mode": local_session["mode"],
        "createdAt": local_session["created_at"],
        "updatedAt": local_session["updated_at"],
        "messageCount": local_session["message_count"],
        "tags": [],  # 新規フィールド
        "summary": "",  # 新規フィールド（後で生成）
        "lastMessage": "",  # 新規フィールド（後で設定）
        "metadata": {
            "migrated_from": "local_json",
            "migration_date": datetime.now().isoformat()
        }
    }
```

#### メッセージ変換
```python
def _convert_message_format(self, local_message, session_id):
    """ローカルメッセージ → Cosmos DBメッセージ"""
    
    # 検索用テキスト生成
    search_text = self._create_search_text(local_message["content"])
    
    return {
        "id": f"message_{uuid.uuid4()}",
        "sessionId": session_id,
        "userId": self._get_current_user_id(),
        "role": local_message["role"],
        "content": local_message["content"],
        "timestamp": local_message["timestamp"],
        "metadata": local_message.get("metadata", {}),
        "searchText": search_text,
        "parentMessageId": None
    }

def _create_search_text(self, content):
    """検索用テキスト生成（形態素解析・正規化）"""
    import re
    
    # 基本的な正規化
    text = content.lower()
    text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', text)
    text = ' '.join(text.split())
    
    return text
```

## 💰 コスト設計

### 1. 料金モデル選択

#### 開発・テスト環境
- **Serverlessモード**: 変動的な負荷に対応
- **推定コスト**: 月額 $10-50
- **利点**: 使用量ベース、自動スケーリング

#### 本番環境
- **Provisioned Throughputモード**: 予測可能なパフォーマンス
- **Auto-scaleモード**: 400-4000 RU/s
- **推定コスト**: 月額 $100-500
- **利点**: 安定したレスポンス時間

### 2. コスト最適化戦略

#### スループット最適化
```python
class ThroughputOptimizer:
    def __init__(self):
        self.base_throughput = 400  # RU/s
        self.max_throughput = 4000  # RU/s
        self.scale_factor = 1.5
    
    def adjust_throughput(self, current_usage):
        """使用量ベースでスループット調整"""
        if current_usage > 0.8:  # 80%使用率
            new_throughput = min(
                int(self.base_throughput * self.scale_factor),
                self.max_throughput
            )
            return new_throughput
        elif current_usage < 0.3:  # 30%使用率
            new_throughput = max(
                int(self.base_throughput / self.scale_factor),
                400  # 最小スループット
            )
            return new_throughput
        
        return self.base_throughput
```

#### データ保持ポリシー
```python
class DataRetentionPolicy:
    def __init__(self):
        self.retention_periods = {
            "active_sessions": None,        # 無制限
            "old_sessions": 365 * 24 * 3600,  # 1年 (TTL秒)
            "temp_messages": 30 * 24 * 3600,   # 30日
            "debug_logs": 7 * 24 * 3600        # 7日
        }
    
    def set_ttl_for_message(self, message, session_age_days):
        """メッセージのTTL設定"""
        if session_age_days > 365:
            message["ttl"] = self.retention_periods["old_sessions"]
        elif message.get("metadata", {}).get("debug"):
            message["ttl"] = self.retention_periods["debug_logs"]
        else:
            message["ttl"] = None  # 無制限
        
        return message
```

### 3. コスト監視

#### 予算アラート設定
```python
class CostMonitor:
    def __init__(self):
        self.monthly_budget = 500  # USD
        self.alert_thresholds = [0.5, 0.8, 0.9]  # 50%, 80%, 90%
    
    def check_usage(self, current_month_cost):
        """月次予算使用率チェック"""
        usage_rate = current_month_cost / self.monthly_budget
        
        for threshold in self.alert_thresholds:
            if usage_rate >= threshold and not self._alert_sent(threshold):
                self._send_budget_alert(usage_rate, threshold)
                self._mark_alert_sent(threshold)
        
        return usage_rate < 1.0  # 予算内かどうか
```

## 📈 パフォーマンス設計

### 1. レスポンス時間目標

#### 基本操作
- **メッセージ追加**: < 100ms (P95)
- **セッション一覧取得**: < 200ms (P95)
- **メッセージ検索**: < 500ms (P95)
- **複合検索**: < 1000ms (P95)

#### 最適化手法
```python
class PerformanceOptimizer:
    def __init__(self):
        self.query_cache = {}
        self.cache_ttl = 300  # 5分
    
    async def search_with_cache(self, query, params):
        """キャッシュ付き検索"""
        cache_key = self._generate_cache_key(query, params)
        
        # キャッシュ確認
        cached_result = self.query_cache.get(cache_key)
        if cached_result and not self._is_cache_expired(cached_result):
            return cached_result["data"]
        
        # Cosmos DB検索実行
        result = await self._execute_search(query, params)
        
        # キャッシュ保存
        self.query_cache[cache_key] = {
            "data": result,
            "timestamp": time.time()
        }
        
        return result
```

### 2. スケーラビリティ設計

#### 水平スケーリング戦略
- **パーティション分散**: ユーザーID/セッションIDベース
- **地理的分散**: マルチリージョン対応
- **レプリケーション**: 読み取り専用レプリカ

#### 負荷テスト計画
```python
class LoadTestScenario:
    def __init__(self):
        self.scenarios = {
            "normal_usage": {
                "concurrent_users": 10,
                "operations_per_minute": 100,
                "read_write_ratio": 7,  # 読み取り:書き込み = 7:3
            },
            "peak_usage": {
                "concurrent_users": 50,
                "operations_per_minute": 500,
                "read_write_ratio": 8,
            },
            "stress_test": {
                "concurrent_users": 100,
                "operations_per_minute": 1000,
                "read_write_ratio": 9,
            }
        }
```

## 🔧 実装計画

### 1. 開発フェーズ

#### Phase 1: 基盤実装 (2週間)
- [ ] Cosmos DB接続・認証モジュール
- [ ] 基本CRUD操作
- [ ] データモデル実装
- [ ] ユニットテスト

#### Phase 2: 検索機能 (2週間)  
- [ ] 基本検索API
- [ ] 高度検索クエリ
- [ ] パフォーマンス最適化
- [ ] 検索UI統合

#### Phase 3: 移行ツール (1週間)
- [ ] データ移行スクリプト
- [ ] 形式変換ロジック
- [ ] 移行検証ツール
- [ ] ロールバック機能

#### Phase 4: 統合・テスト (1週間)
- [ ] simple_chatbot.py統合
- [ ] E2Eテスト
- [ ] パフォーマンステスト
- [ ] ドキュメント作成

### 2. 技術スタック

#### 必要な追加パッケージ
```bash
# Azure Cosmos DB
pip install azure-cosmos>=4.5.0

# キャッシュ（オプション）
pip install redis>=4.0.0

# 検索・解析（オプション）
pip install azure-search-documents>=11.4.0
pip install mecab-python3>=1.0.0  # 日本語形態素解析
```

#### 設定管理
```python
# .env追加設定
COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_DATABASE_NAME=chat_history_db
COSMOS_DB_SESSIONS_CONTAINER=sessions
COSMOS_DB_MESSAGES_CONTAINER=messages

# オプション設定
COSMOS_DB_THROUGHPUT_MODE=serverless  # or provisioned
COSMOS_DB_MAX_THROUGHPUT=4000
ENABLE_COSMOS_CACHE=true
ENABLE_MIGRATION_MODE=true
```

## 📚 参考情報

### 関連ドキュメント
- [Azure Cosmos DB Python SDK Best Practices](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/best-practice-python)
- [Chat History Implementation Guide](https://devblogs.microsoft.com/cosmosdb/implementing-chat-history-for-ai-applications-using-azure-cosmos-db-go-sdk/)
- [Azure Cosmos DB Pricing](https://azure.microsoft.com/en-us/pricing/details/cosmos-db/)

### 既存プロジェクト資産
- `core/azure_universal_auth.py`: Azure認証基盤
- `chat_history/local_history.py`: 既存履歴管理
- `simple_chatbot.py`: チャットボットアプリケーション

---

**作成日**: 2025-07-20  
**バージョン**: v1.0  
**作成者**: Azure o3-pro Toolkit Development Team