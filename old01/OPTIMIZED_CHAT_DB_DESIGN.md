# チャットDB最適化設計書 - 検索重視アーキテクチャ

## 🎯 設計方針

### チャットDBとしてのベストプラクティス重視
1. **検索ファーストデザイン**: 検索パフォーマンスを最優先
2. **ユーザー体験重視**: 直感的な検索・分類機能
3. **スケーラビリティ**: 数百万メッセージ対応
4. **AI活用**: 自動カテゴリー分類・要約生成

## 📊 検索パターン分析

### 実際のチャット検索ニーズ
```
1. 人による検索 (30%)
   - "田中さんとの会話"
   - "サポートチームとのやり取り"
   
2. カテゴリー・トピック検索 (25%)
   - "プログラミング関連"
   - "会議の議事録"
   - "技術サポート"
   
3. 内容・キーワード検索 (20%)
   - "Azure Cosmos DB"
   - "エラー解決方法"
   
4. 時期・期間検索 (15%)
   - "先月の会話"
   - "プロジェクト開始前後"
   
5. 複合検索 (10%)
   - "田中さんとの先月のプログラミング関連会話"
```

## 🏗️ 最適化データモデル設計

### 1. コンテナ設計（検索最適化）

#### 主要コンテナ構成
```json
{
  "database": "optimized_chat_db",
  "containers": [
    {
      "name": "conversations",
      "partitionKey": "/tenantId",
      "description": "会話スレッド管理（検索メイン）"
    },
    {
      "name": "messages",
      "partitionKey": "/conversationId", 
      "description": "個別メッセージ（内容検索）"
    },
    {
      "name": "participants",
      "partitionKey": "/tenantId",
      "description": "参加者マスタ（人検索）"
    },
    {
      "name": "categories",
      "partitionKey": "/tenantId",
      "description": "カテゴリーマスタ（分類検索）"
    },
    {
      "name": "search_index",
      "partitionKey": "/indexType",
      "description": "検索インデックス（高速検索）"
    }
  ]
}
```

### 2. 会話（Conversation）モデル

```json
{
  "id": "conv_20250720_001",
  "tenantId": "tenant_company_a",
  "conversationId": "20250720_001",
  
  "title": "Azure Cosmos DB 実装相談",
  "summary": "チャット履歴をCosmos DBに移行する際の設計相談と実装方針の検討",
  
  "participants": [
    {
      "userId": "user_koji",
      "displayName": "Koji",
      "role": "developer",
      "joinedAt": "2025-07-20T01:00:00Z"
    },
    {
      "userId": "assistant_o3pro",
      "displayName": "O3-Pro Assistant",
      "role": "ai_assistant",
      "joinedAt": "2025-07-20T01:00:00Z"
    }
  ],
  
  "categories": [
    {
      "categoryId": "tech_database",
      "categoryName": "技術/データベース",
      "confidence": 0.95,
      "source": "ai_classification"
    },
    {
      "categoryId": "project_development", 
      "categoryName": "プロジェクト/開発",
      "confidence": 0.85,
      "source": "ai_classification"
    }
  ],
  
  "tags": [
    "azure", "cosmos_db", "python", "チャット履歴", "設計相談"
  ],
  
  "metrics": {
    "messageCount": 12,
    "participantCount": 2,
    "totalTokens": 3500,
    "avgResponseTime": 4.2,
    "conversationDuration": 1800
  },
  
  "timeline": {
    "createdAt": "2025-07-20T01:00:00Z",
    "updatedAt": "2025-07-20T01:30:00Z",
    "lastMessageAt": "2025-07-20T01:30:00Z",
    "firstMessagePreview": "次のプロジェクトでは、Cosmos DBを使いたいと思います",
    "lastMessagePreview": "ありがとうございます。設計方針が明確になりました"
  },
  
  "searchableText": "azure cosmos db 実装 相談 チャット 履歴 移行 設計 python データベース",
  
  "status": "active",
  "privacy": "private",
  "archived": false,
  "bookmarked": false,
  
  "ai_metadata": {
    "sentiment": "positive",
    "complexity": "medium",
    "resolution_status": "resolved",
    "key_topics": ["database_design", "azure_services", "python_implementation"],
    "related_conversations": ["conv_20250715_003", "conv_20250718_001"]
  }
}
```

### 3. メッセージ（Message）モデル

```json
{
  "id": "msg_20250720_001_001",
  "conversationId": "20250720_001",
  "tenantId": "tenant_company_a",
  
  "sender": {
    "userId": "user_koji",
    "displayName": "Koji",
    "role": "developer"
  },
  
  "content": {
    "text": "次のプロジェクトでは、現在のJSONファイルベースのチャット履歴をAzure Cosmos DBに移行したいと考えています。",
    "originalText": "次のプロジェクトでは、現在のJSONファイルベースのチャット履歴をAzure Cosmos DBに移行したいと考えています。",
    "searchableText": "次 プロジェクト 現在 json ファイル ベース チャット 履歴 azure cosmos db 移行 考え",
    "type": "text",
    "language": "ja"
  },
  
  "timestamp": "2025-07-20T01:00:15Z",
  "sequenceNumber": 1,
  
  "technical_metadata": {
    "mode": "reasoning",
    "effort": "medium",
    "duration": 5.2,
    "tokens": 45,
    "model": "o3-pro",
    "temperature": 0.7
  },
  
  "extracted_entities": [
    {
      "type": "technology",
      "value": "Azure Cosmos DB",
      "confidence": 0.95
    },
    {
      "type": "format",
      "value": "JSON",
      "confidence": 0.90
    },
    {
      "type": "action",
      "value": "移行",
      "confidence": 0.85
    }
  ],
  
  "thread_info": {
    "parentMessageId": null,
    "replyToMessageId": null,
    "threadDepth": 0,
    "hasReplies": false
  },
  
  "reactions": [],
  "attachments": [],
  
  "ai_analysis": {
    "intent": "request_consultation",
    "sentiment": "neutral",
    "urgency": "medium",
    "topics": ["database_migration", "azure_services"],
    "action_items": ["design_review", "implementation_plan"]
  }
}
```

### 4. 参加者（Participant）マスタ

```json
{
  "id": "participant_user_koji",
  "tenantId": "tenant_company_a",
  "userId": "user_koji",
  
  "profile": {
    "displayName": "Koji",
    "email": "koji@company.com",
    "department": "Engineering",
    "role": "Senior Developer",
    "timezone": "Asia/Tokyo"
  },
  
  "chat_statistics": {
    "totalConversations": 156,
    "totalMessages": 2340,
    "avgMessagesPerConversation": 15,
    "mostActiveCategories": ["tech_database", "project_development"],
    "preferredLanguage": "ja",
    "avgResponseTime": 300
  },
  
  "activity_pattern": {
    "mostActiveHours": [9, 10, 14, 15, 16],
    "mostActiveDays": ["Monday", "Tuesday", "Wednesday"],
    "lastActiveAt": "2025-07-20T01:30:00Z",
    "currentStatus": "online"
  },
  
  "preferences": {
    "searchHistory": ["Azure", "Cosmos DB", "Python", "設計"],
    "bookmarkedCategories": ["tech_database", "architecture"],
    "notificationSettings": {
      "mentions": true,
      "keywords": ["urgent", "エラー", "障害"]
    }
  }
}
```

### 5. カテゴリーマスタ

```json
{
  "id": "category_tech_database",
  "tenantId": "tenant_company_a",
  "categoryId": "tech_database",
  
  "hierarchy": {
    "level": 2,
    "parentId": "tech",
    "parentName": "技術",
    "fullPath": "技術/データベース",
    "children": ["tech_database_sql", "tech_database_nosql", "tech_database_design"]
  },
  
  "display": {
    "name": "データベース",
    "description": "データベース設計、運用、パフォーマンスに関する話題",
    "color": "#2196F3",
    "icon": "database",
    "emoji": "🗄️"
  },
  
  "ai_classification": {
    "keywords": ["database", "データベース", "DB", "SQL", "NoSQL", "cosmos", "mongodb"],
    "patterns": [
      ".*データベース.*設計.*",
      ".*DB.*パフォーマンス.*",
      ".*クエリ.*最適化.*"
    ],
    "excludePatterns": [".*database.*password.*"]
  },
  
  "statistics": {
    "conversationCount": 45,
    "messageCount": 680,
    "avgConversationLength": 15,
    "topParticipants": ["user_koji", "user_tanaka"],
    "trendingTopics": ["Azure Cosmos DB", "パフォーマンス最適化", "スキーマ設計"]
  },
  
  "settings": {
    "autoClassify": true,
    "confidenceThreshold": 0.8,
    "requireManualReview": false,
    "enableTrending": true
  }
}
```

## 🔍 検索インデックス設計

### 1. マルチレベル検索戦略

#### Level 1: 高速フィルタリング（Cosmos DB インデックス）
```json
{
  "conversations_index": {
    "includedPaths": [
      {"path": "/tenantId/?"},
      {"path": "/participants/*/userId/?"},
      {"path": "/categories/*/categoryId/?"},
      {"path": "/tags/*"},
      {"path": "/timeline/lastMessageAt/?"},
      {"path": "/timeline/createdAt/?"},
      {"path": "/searchableText/?"},
      {"path": "/status/?"},
      {"path": "/archived/?"}
    ],
    "compositeIndexes": [
      [
        {"path": "/tenantId", "order": "ascending"},
        {"path": "/timeline/lastMessageAt", "order": "descending"}
      ],
      [
        {"path": "/tenantId", "order": "ascending"},
        {"path": "/participants/0/userId", "order": "ascending"},
        {"path": "/timeline/lastMessageAt", "order": "descending"}
      ],
      [
        {"path": "/tenantId", "order": "ascending"},
        {"path": "/categories/0/categoryId", "order": "ascending"},
        {"path": "/timeline/lastMessageAt", "order": "descending"}
      ]
    ]
  }
}
```

#### Level 2: 全文検索（Azure Cognitive Search 統合）
```json
{
  "search_service_config": {
    "index_name": "chat-conversations",
    "fields": [
      {
        "name": "id",
        "type": "Edm.String",
        "key": true
      },
      {
        "name": "title",
        "type": "Edm.String",
        "searchable": true,
        "analyzer": "ja.lucene"
      },
      {
        "name": "summary", 
        "type": "Edm.String",
        "searchable": true,
        "analyzer": "ja.lucene"
      },
      {
        "name": "searchableText",
        "type": "Edm.String", 
        "searchable": true,
        "analyzer": "ja.lucene"
      },
      {
        "name": "participants",
        "type": "Collection(Edm.String)",
        "searchable": true,
        "filterable": true
      },
      {
        "name": "categories",
        "type": "Collection(Edm.String)",
        "filterable": true,
        "facetable": true
      },
      {
        "name": "tags",
        "type": "Collection(Edm.String)",
        "filterable": true,
        "facetable": true
      },
      {
        "name": "lastMessageAt",
        "type": "Edm.DateTimeOffset",
        "filterable": true,
        "sortable": true
      }
    ],
    "suggesters": [
      {
        "name": "conversation-suggester",
        "searchMode": "analyzingInfixMatching",
        "sourceFields": ["title", "tags", "participants"]
      }
    ]
  }
}
```

### 2. 検索API設計

#### 統合検索エンドポイント
```python
class OptimizedSearchService:
    """最適化検索サービス"""
    
    async def search_conversations(self, search_request: SearchRequest) -> SearchResponse:
        """統合会話検索"""
        
        # Phase 1: 高速フィルタリング（Cosmos DB）
        cosmos_filter = self._build_cosmos_filter(search_request)
        candidate_conversations = await self._cosmos_pre_filter(cosmos_filter)
        
        # Phase 2: 全文検索（Azure Cognitive Search） 
        if search_request.has_text_query():
            search_results = await self._cognitive_search(
                search_request, 
                candidate_conversations
            )
        else:
            search_results = candidate_conversations
        
        # Phase 3: AI強化検索（オプション）
        if search_request.enable_ai_search:
            search_results = await self._ai_enhance_results(
                search_request,
                search_results
            )
        
        # Phase 4: ランキング・ソート
        ranked_results = self._rank_and_sort(search_results, search_request)
        
        return SearchResponse(
            results=ranked_results,
            total_count=len(ranked_results),
            facets=self._extract_facets(search_results),
            suggestions=await self._get_suggestions(search_request),
            search_time_ms=self._get_search_time()
        )

@dataclass
class SearchRequest:
    """検索リクエスト"""
    
    # 基本検索
    query: Optional[str] = None  # 自由テキスト検索
    
    # 人検索
    participants: Optional[List[str]] = None
    participant_roles: Optional[List[str]] = None
    
    # カテゴリー検索
    categories: Optional[List[str]] = None
    category_confidence_min: float = 0.8
    
    # 時期検索
    date_range: Optional[DateRange] = None
    time_of_day: Optional[TimeRange] = None
    
    # メタデータ検索
    tags: Optional[List[str]] = None
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    resolution_status: Optional[str] = None
    
    # 検索オプション
    enable_ai_search: bool = False
    include_archived: bool = False
    search_mode: str = "all"  # all, any, exact
    
    # ソート・ページング
    sort_by: str = "relevance"  # relevance, date, activity
    page_size: int = 20
    page_number: int = 1
```

## 🤖 AI活用機能

### 1. 自動カテゴリー分類

```python
class AICategorizationService:
    """AI自動分類サービス"""
    
    async def classify_conversation(self, conversation: dict) -> List[CategoryPrediction]:
        """会話の自動分類"""
        
        # 会話内容の特徴抽出
        features = self._extract_features(conversation)
        
        # 多層分類モデル
        predictions = []
        
        # Level 1: 大分類（技術/ビジネス/個人など）
        major_category = await self._classify_major_category(features)
        predictions.append(major_category)
        
        # Level 2: 中分類（技術→データベース/フロントエンドなど）
        if major_category.confidence > 0.8:
            minor_category = await self._classify_minor_category(
                features, 
                major_category.category_id
            )
            predictions.append(minor_category)
        
        # Level 3: 詳細分類（データベース→設計/性能など）
        if len(predictions) > 1 and predictions[-1].confidence > 0.75:
            detail_category = await self._classify_detail_category(
                features,
                predictions[-1].category_id
            )
            predictions.append(detail_category)
        
        return predictions
    
    def _extract_features(self, conversation: dict) -> dict:
        """特徴量抽出"""
        
        # テキスト特徴
        all_text = " ".join([
            conversation.get("title", ""),
            conversation.get("summary", ""),
            " ".join([p.get("displayName", "") for p in conversation.get("participants", [])])
        ])
        
        # キーワード特徴
        keywords = self._extract_keywords(all_text)
        
        # 技術用語特徴
        tech_terms = self._extract_tech_terms(all_text)
        
        # 参加者特徴
        participant_features = self._analyze_participants(conversation.get("participants", []))
        
        # 時間特徴
        temporal_features = self._analyze_temporal_patterns(conversation)
        
        return {
            "text_features": all_text,
            "keywords": keywords,
            "tech_terms": tech_terms,
            "participant_features": participant_features,
            "temporal_features": temporal_features,
            "message_count": conversation.get("metrics", {}).get("messageCount", 0),
            "avg_response_time": conversation.get("metrics", {}).get("avgResponseTime", 0)
        }
```

### 2. スマート検索候補

```python
class SmartSuggestionService:
    """スマート検索候補サービス"""
    
    async def get_search_suggestions(
        self, 
        user_id: str, 
        partial_query: str,
        context: dict = None
    ) -> List[SearchSuggestion]:
        """スマート検索候補取得"""
        
        suggestions = []
        
        # 1. 履歴ベース候補
        history_suggestions = await self._get_history_suggestions(user_id, partial_query)
        suggestions.extend(history_suggestions)
        
        # 2. カテゴリーベース候補
        category_suggestions = await self._get_category_suggestions(partial_query)
        suggestions.extend(category_suggestions)
        
        # 3. 人ベース候補
        people_suggestions = await self._get_people_suggestions(user_id, partial_query)
        suggestions.extend(people_suggestions)
        
        # 4. AI強化候補
        if len(partial_query) >= 3:
            ai_suggestions = await self._get_ai_suggestions(
                user_id, 
                partial_query, 
                context
            )
            suggestions.extend(ai_suggestions)
        
        # 5. トレンド候補
        trending_suggestions = await self._get_trending_suggestions(partial_query)
        suggestions.extend(trending_suggestions)
        
        # ランキング・重複排除
        ranked_suggestions = self._rank_suggestions(suggestions, partial_query)
        return ranked_suggestions[:10]  # 上位10件
```

## 📈 パフォーマンス最適化戦略

### 1. 階層キャッシュ戦略

```python
class HierarchicalCacheService:
    """階層キャッシュサービス"""
    
    def __init__(self):
        # L1: アプリケーションメモリキャッシュ
        self.memory_cache = {}  # 1分TTL
        
        # L2: Redis分散キャッシュ  
        self.redis_cache = redis.Redis()  # 5分TTL
        
        # L3: Cosmos DB変更フィード
        self.change_feed_cache = {}  # リアルタイム更新
    
    async def get_search_results(self, search_key: str) -> Optional[dict]:
        """階層キャッシュから検索結果取得"""
        
        # L1: メモリキャッシュ確認
        result = self.memory_cache.get(search_key)
        if result and not self._is_expired(result, 60):  # 1分
            return result["data"]
        
        # L2: Redis確認
        result = await self.redis_cache.get(search_key)
        if result:
            data = json.loads(result)
            # L1にプロモート
            self.memory_cache[search_key] = {
                "data": data,
                "timestamp": time.time()
            }
            return data
        
        return None
    
    async def cache_search_results(self, search_key: str, data: dict):
        """検索結果キャッシュ"""
        
        # L1: メモリキャッシュ
        self.memory_cache[search_key] = {
            "data": data,
            "timestamp": time.time()
        }
        
        # L2: Redis
        await self.redis_cache.setex(
            search_key, 
            300,  # 5分
            json.dumps(data)
        )
```

### 2. パーティション最適化戦略

```python
class PartitionOptimizer:
    """パーティション最適化"""
    
    def get_optimal_partition_key(self, query_pattern: str) -> str:
        """クエリパターンに基づく最適パーティションキー決定"""
        
        if query_pattern == "user_conversations":
            # ユーザー別会話一覧 → tenantId + userId
            return "/tenantId"
        
        elif query_pattern == "category_browse":
            # カテゴリー別ブラウジング → tenantId + categoryId
            return "/tenantId"
        
        elif query_pattern == "time_range_search":
            # 時期別検索 → tenantId + dateSharding
            return "/tenantId"
        
        elif query_pattern == "conversation_messages":
            # 会話内メッセージ → conversationId
            return "/conversationId"
        
        else:
            # デフォルト → tenantId
            return "/tenantId"
    
    def create_synthetic_partition_key(self, data: dict, pattern: str) -> str:
        """合成パーティションキー作成"""
        
        if pattern == "tenant_user":
            return f"{data['tenantId']}#{data['userId']}"
        
        elif pattern == "tenant_date":
            date_shard = data['createdAt'][:7]  # YYYY-MM
            return f"{data['tenantId']}#{date_shard}"
        
        elif pattern == "tenant_category":
            main_category = data['categories'][0]['categoryId'] if data['categories'] else 'general'
            return f"{data['tenantId']}#{main_category}"
        
        else:
            return data['tenantId']
```

## 🔧 実装ロードマップ

### Phase 1: 基盤構築（2週間）
```
Week 1:
- ✅ 最適化データモデル実装
- ✅ Cosmos DB コンテナ・インデックス設計
- ✅ 基本CRUD操作

Week 2:  
- ✅ 参加者・カテゴリーマスタ実装
- ✅ 基本検索API（Cosmos DBのみ）
- ✅ ユニットテスト
```

### Phase 2: 検索強化（2週間）
```
Week 3:
- ✅ Azure Cognitive Search統合
- ✅ 全文検索機能
- ✅ ファセット検索

Week 4:
- ✅ 検索候補機能
- ✅ パフォーマンス最適化
- ✅ キャッシュ機能
```

### Phase 3: AI機能（2週間）
```
Week 5:
- ✅ 自動カテゴリー分類
- ✅ 要約生成
- ✅ エンティティ抽出

Week 6:
- ✅ スマート検索候補
- ✅ 関連会話推薦
- ✅ 性能調整
```

### Phase 4: 統合・移行（1週間）
```
Week 7:
- ✅ 既存システム統合
- ✅ データ移行ツール
- ✅ E2Eテスト
- ✅ 本番展開
```

## 💡 検索UX設計

### 1. 統一検索インターフェース

```python
class UnifiedSearchInterface:
    """統一検索インターフェース"""
    
    def __init__(self):
        self.search_modes = {
            "simple": SimpleSearchMode(),
            "advanced": AdvancedSearchMode(), 
            "ai_assisted": AIAssistedSearchMode()
        }
    
    async def search(self, mode: str, query: dict) -> SearchResult:
        """モード別検索実行"""
        
        search_mode = self.search_modes.get(mode, self.search_modes["simple"])
        return await search_mode.execute(query)

class SimpleSearchMode:
    """シンプル検索（Google風）"""
    
    async def execute(self, query: dict) -> SearchResult:
        """
        入力例: "田中さん Azure 先月"
        自動解析: 
        - 参加者: 田中さん
        - キーワード: Azure
        - 時期: 先月
        """
        
        parsed_query = self._parse_natural_query(query["text"])
        
        search_request = SearchRequest(
            query=parsed_query.get("keywords"),
            participants=parsed_query.get("participants"),
            date_range=parsed_query.get("date_range"),
            enable_ai_search=True
        )
        
        return await self.search_service.search_conversations(search_request)

class AdvancedSearchMode:
    """高度検索（フィールド指定）"""
    
    async def execute(self, query: dict) -> SearchResult:
        """
        フィールド別検索:
        - 参加者: [田中, 佐藤]
        - カテゴリー: [技術/データベース]
        - 期間: 2025-07-01 ～ 2025-07-31
        - キーワード: "Azure Cosmos DB"
        """
        
        search_request = SearchRequest(**query)
        return await self.search_service.search_conversations(search_request)

class AIAssistedSearchMode:
    """AI支援検索"""
    
    async def execute(self, query: dict) -> SearchResult:
        """
        AI理解例:
        - "Azureの設定でつまづいた時の会話を見つけて"
        - "先月のプロジェクト会議の要点を教えて"
        - "類似の技術相談があったか確認して"
        """
        
        # AI意図理解
        intent = await self.ai_service.understand_intent(query["text"])
        
        # 検索クエリ生成
        search_request = await self.ai_service.generate_search_query(intent)
        
        # 検索実行
        results = await self.search_service.search_conversations(search_request)
        
        # AI強化レスポンス
        enhanced_results = await self.ai_service.enhance_results(
            results, 
            intent
        )
        
        return enhanced_results
```

### 2. 検索結果表示最適化

```python
class SearchResultPresenter:
    """検索結果プレゼンター"""
    
    def format_results(self, results: SearchResult, view_mode: str) -> dict:
        """ビューモード別結果フォーマット"""
        
        if view_mode == "list":
            return self._format_list_view(results)
        elif view_mode == "timeline":
            return self._format_timeline_view(results)
        elif view_mode == "category":
            return self._format_category_view(results)
        elif view_mode == "participants":
            return self._format_participants_view(results)
        else:
            return self._format_default_view(results)
    
    def _format_list_view(self, results: SearchResult) -> dict:
        """リスト表示"""
        return {
            "view_type": "list",
            "items": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "summary": conv.summary[:100] + "...",
                    "participants": [p["displayName"] for p in conv.participants],
                    "categories": [c["categoryName"] for c in conv.categories],
                    "lastMessageAt": conv.timeline["lastMessageAt"],
                    "messageCount": conv.metrics["messageCount"],
                    "relevance_score": conv.relevance_score
                }
                for conv in results.conversations
            ],
            "facets": results.facets,
            "suggestions": results.suggestions
        }
    
    def _format_timeline_view(self, results: SearchResult) -> dict:
        """タイムライン表示"""
        
        # 日付別グループ化
        grouped_by_date = {}
        for conv in results.conversations:
            date_key = conv.timeline["lastMessageAt"][:10]  # YYYY-MM-DD
            if date_key not in grouped_by_date:
                grouped_by_date[date_key] = []
            grouped_by_date[date_key].append(conv)
        
        timeline_items = []
        for date, conversations in sorted(grouped_by_date.items(), reverse=True):
            timeline_items.append({
                "date": date,
                "conversations": conversations,
                "count": len(conversations)
            })
        
        return {
            "view_type": "timeline",
            "timeline": timeline_items,
            "facets": results.facets
        }
```

## 📊 分析・レポート機能

### 1. チャット分析ダッシュボード

```python
class ChatAnalyticsService:
    """チャット分析サービス"""
    
    async def generate_usage_report(self, tenant_id: str, period: str) -> dict:
        """利用状況レポート"""
        
        analytics = await self._aggregate_conversation_metrics(tenant_id, period)
        
        return {
            "period": period,
            "summary": {
                "total_conversations": analytics["conversation_count"],
                "total_messages": analytics["message_count"],
                "active_participants": analytics["participant_count"],
                "avg_conversation_length": analytics["avg_length"],
                "most_active_categories": analytics["top_categories"]
            },
            "trends": {
                "daily_activity": analytics["daily_trend"],
                "hourly_pattern": analytics["hourly_pattern"],
                "category_growth": analytics["category_trend"]
            },
            "insights": await self._generate_ai_insights(analytics)
        }
    
    async def _generate_ai_insights(self, analytics: dict) -> List[str]:
        """AI洞察生成"""
        insights = []
        
        # 活動パターン分析
        if analytics["peak_hour"] in [9, 10, 14, 15]:
            insights.append("業務時間中の技術相談が活発です")
        
        # カテゴリー偏向分析
        top_category_ratio = analytics["top_categories"][0]["ratio"]
        if top_category_ratio > 0.4:
            insights.append(f"特定分野（{analytics['top_categories'][0]['name']}）への集中度が高いです")
        
        # 応答時間分析
        if analytics["avg_response_time"] > 300:  # 5分
            insights.append("応答時間が長い傾向があります。リアルタイム通知の活用を検討してください")
        
        return insights
```

---

この最適化設計により、チャットDBとしての実用性を大幅に向上させることができます。検索ファーストのアプローチにより、ユーザーは直感的かつ高速に過去の会話を見つけることができるようになります。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Azure Cosmos DB\u6280\u8853\u8abf\u67fb: Context7\u3068Web\u3067Cosmos DB\u306e\u6a5f\u80fd\u3001Python SDK\u3001\u6599\u91d1\u4f53\u7cfb\u3092\u8abf\u67fb", "status": "completed", "priority": "high", "id": "27"}, {"content": "\u73fe\u5728\u306e\u5c65\u6b74\u7ba1\u7406\u5206\u6790: local_history.py\u306e\u6a5f\u80fd\u3068\u30c7\u30fc\u30bf\u69cb\u9020\u3092\u5206\u6790\u3057\u3001Cosmos DB\u79fb\u884c\u8a08\u753b\u3092\u7acb\u6848", "status": "completed", "priority": "high", "id": "28"}, {"content": "\u691c\u7d22\u6a5f\u80fd\u8a2d\u8a08: Cosmos DB\u3067\u306e\u30c1\u30e3\u30c3\u30c8\u5c65\u6b74\u691c\u7d22\u30fb\u30d5\u30a3\u30eb\u30bf\u30ea\u30f3\u30b0\u6a5f\u80fd\u306e\u8a73\u7d30\u8a2d\u8a08", "status": "completed", "priority": "high", "id": "29"}, {"content": "\u8a8d\u8a3c\u7d71\u5408\u8a2d\u8a08: \u65e2\u5b58\u306eAzure\u8a8d\u8a3c\u57fa\u76e4\u3068Cosmos DB\u63a5\u7d9a\u306e\u7d71\u5408\u8a2d\u8a08", "status": "completed", "priority": "medium", "id": "30"}, {"content": "\u30c7\u30fc\u30bf\u30e2\u30c7\u30eb\u8a2d\u8a08: \u30c1\u30e3\u30c3\u30c8\u5c65\u6b74\u306eCosmos DB\u30b3\u30f3\u30c6\u30ca\u30fb\u30d1\u30fc\u30c6\u30a3\u30b7\u30e7\u30f3\u8a2d\u8a08", "status": "completed", "priority": "high", "id": "31"}, {"content": "\u30d1\u30d5\u30a9\u30fc\u30de\u30f3\u30b9\u8a2d\u8a08: \u5927\u91cf\u30c7\u30fc\u30bf\u3067\u306e\u691c\u7d22\u30d1\u30d5\u30a9\u30fc\u30de\u30f3\u30b9\u6700\u9069\u5316\u8a2d\u8a08", "status": "completed", "priority": "medium", "id": "32"}, {"content": "\u79fb\u884c\u6226\u7565\u8a2d\u8a08: \u30ed\u30fc\u30ab\u30eb\u5c65\u6b74\u304b\u3089Cosmos DB\u3078\u306e\u79fb\u884c\u624b\u9806\u3068\u30c7\u30fc\u30bf\u79fb\u884c", "status": "completed", "priority": "medium", "id": "33"}, {"content": "\u8a2d\u8a08\u69cb\u60f3\u66f8\u4f5c\u6210: \u5168\u4f53\u30a2\u30fc\u30ad\u30c6\u30af\u30c1\u30e3\u3068\u6280\u8853\u9078\u629e\u306e\u69cb\u60f3\u66f8\u4f5c\u6210", "status": "completed", "priority": "high", "id": "34"}, {"content": "\u8a73\u7d30\u4ed5\u69d8\u66f8\u4f5c\u6210: \u5b9f\u88c5\u30ec\u30d9\u30eb\u306e\u8a73\u7d30\u4ed5\u69d8\u66f8\u4f5c\u6210", "status": "completed", "priority": "high", "id": "35"}, {"content": "\u30c1\u30e3\u30c3\u30c8DB\u30d9\u30b9\u30c8\u30d7\u30e9\u30af\u30c6\u30a3\u30b9\u518d\u8a2d\u8a08: \u691c\u7d22\u6700\u9069\u5316\u3001\u30ab\u30c6\u30b4\u30ea\u30fc\u5206\u985e\u3001\u30e6\u30fc\u30b6\u30fc\u7ba1\u7406\u3092\u8003\u616e\u3057\u305f\u8a2d\u8a08\u306e\u518d\u691c\u8a0e", "status": "completed", "priority": "high", "id": "36"}]