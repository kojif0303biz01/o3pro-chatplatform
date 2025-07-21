# Design Document - O3-Pro Chat Platform Phase 2

## 1. システムアーキテクチャ（Phase 2完了）

### 1.1 実装済み全体構成

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │  • Chat UI Components (完全実装済み)              │   │
│  │  • Zustand状態管理                               │   │
│  │  • REST API Client (完全動作)                    │   │
│  │  • WebSocket Client (基盤準備済み)               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTPS REST API (CORS完全対応)
┌─────────────────┴───────────────────────────────────────┐
│  Backend API (FastAPI + Socket.IO)                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  • REST Endpoints (完全実装)                     │   │
│  │  • APIキー認証 (ミドルウェア)                     │   │
│  │  • WebSocket準備 (Socket.IO基盤)                 │   │
│  │  • Core Module統合 (完全連携)                    │   │
│  └─────────────────────────────────────────────────┘   │
└────────┬────────────────┬─────────────────────────────────┘
         │                │
         │                │
┌────────┴──────┐  ┌──────┴────────────────────────────────┐
│ Azure OpenAI  │  │  Azure Cosmos DB                      │
│ o3-pro        │  │  • 履歴管理 (完全動作)                 │
│ (完全連携)     │  │  • セッション管理                     │
└───────────────┘  └───────────────────────────────────────┘
```

### 1.2 Phase 2完了時のプロジェクト構造

```
conect01/
├── apps/                      # アプリケーション層
│   ├── web/                   # ✅ React + TypeScript + Vite
│   │   ├── src/
│   │   │   ├── components/    # ✅ 完全実装 (Chat/Layout)
│   │   │   │   ├── Chat/     # チャットUI完全実装
│   │   │   │   └── Layout/   # レイアウト管理
│   │   │   ├── hooks/        # ✅ WebSocket基盤
│   │   │   ├── stores/       # ✅ Zustand状態管理
│   │   │   └── services/     # ✅ API通信
│   │   ├── public/
│   │   └── package.json
│   └── api/                   # ✅ FastAPI完全実装
│       ├── main.py           # FastAPIアプリ + CORS設定
│       ├── routers/          # ✅ 全エンドポイント実装済み
│       │   ├── chat.py       # チャットメッセージ処理
│       │   ├── sessions.py   # セッションCRUD + OPTIONS対応
│       │   └── websocket.py  # Socket.IO WebSocket準備
│       ├── middleware/       # ✅ 認証・エラー処理完全実装
│       │   ├── auth.py       # APIキー認証ミドルウェア
│       │   └── error_handler.py # グローバルエラーハンドラー
│       ├── services/         # ✅ ビジネスロジック完全実装
│       │   ├── startup.py    # サービス初期化管理
│       │   └── chat_service.py # チャット処理 + 履歴管理
│       ├── models/           # ✅ Pydanticモデル完全実装
│       │   ├── request.py    # API リクエストモデル
│       │   └── response.py   # API レスポンスモデル
│       └── venv/             # 仮想環境
├── packages/                  # ✅ 共通ライブラリ
│   ├── core/                 # ✅ Azure認証・共通機能
│   ├── cosmos_history/       # ✅ Cosmos DB履歴管理
│   └── handlers/             # ✅ o3-proモードハンドラー
├── infrastructure/           # ✅ Infrastructure as Code準備
│   ├── bicep/
│   └── scripts/
├── history&tips.md           # ✅ 開発履歴・トラブルシューティング
├── requirements.md           # ✅ 要件定義（Phase 2完了版）
├── design.md                 # 本ドキュメント
├── todolist.md               # ✅ 開発進捗管理
└── old01/                    # 旧バージョン・未使用ファイル
```

## 2. 実装済みコンポーネント設計

### 2.1 Frontend（完全実装済み）

#### 技術スタック
- **Framework**: React 18 + TypeScript ✅
- **ビルドツール**: Vite ✅ 
- **スタイリング**: Tailwind CSS ✅
- **状態管理**: Zustand ✅
- **通信**: Fetch API (REST) ✅ + Socket.IO準備
- **開発体験**: Hot Reload + TypeScript完全サポート ✅

#### 実装済みコンポーネント構造

```typescript
src/
├── components/           # ✅ 完全実装
│   ├── Chat/            # チャットUIコンポーネント群
│   │   ├── ChatContainer.tsx    # メインチャットコンテナ
│   │   ├── MessageList.tsx      # メッセージ表示リスト
│   │   ├── MessageInput.tsx     # メッセージ入力フォーム
│   │   ├── ModeSelector.tsx     # o3-proモード選択
│   │   └── index.ts
│   ├── Layout/          # レイアウトコンポーネント
│   │   ├── Header.tsx           # アプリヘッダー
│   │   ├── MainLayout.tsx       # メインレイアウト
│   │   └── index.ts
│   └── common/          # 共通コンポーネント（準備）
├── hooks/               # ✅ カスタムフック
│   └── useWebSocket.ts         # WebSocket管理フック
├── stores/              # ✅ Zustand状態管理
│   └── chatStore.ts            # チャット状態管理ストア
├── App.tsx              # ✅ ルートコンポーネント
└── main.tsx             # ✅ エントリーポイント
```

### 2.2 Backend API（完全実装済み）

#### 技術スタック
- **Framework**: FastAPI ✅
- **WebSocket**: Socket.IO (python-socketio) ✅
- **非同期処理**: asyncio ✅
- **認証**: APIキーミドルウェア ✅
- **バリデーション**: Pydantic ✅
- **ログ**: Loguru ✅

#### 実装済みAPI設計

```python
# 完全実装済みエンドポイント
/                         # ✅ ルートエンドポイント
/health                   # ✅ ヘルスチェック
/api/v1/info             # ✅ API情報エンドポイント

/api/v1/chat/
├── POST /message         # ✅ メッセージ送信 (3モード対応)
└── GET /history/{id}     # ✅ チャット履歴取得

/api/v1/sessions/
├── OPTIONS /             # ✅ CORS プリフライト対応
├── POST /                # ✅ セッション作成
├── GET /{id}             # ✅ セッション詳細取得
├── PUT /{id}/mode        # ✅ モード変更
└── GET /                 # ✅ セッション一覧取得

/ws/chat                  # ✅ WebSocketエンドポイント（基盤準備）
```

#### 実装済みディレクトリ構造

```python
apps/api/
├── main.py              # ✅ FastAPIアプリ + ライフサイクル + CORS
├── routers/             # ✅ 完全実装
│   ├── __init__.py
│   ├── chat.py         # チャット関連エンドポイント実装
│   ├── sessions.py     # セッション管理 + OPTIONS対応
│   └── websocket.py    # Socket.IO WebSocketハンドラー準備
├── services/            # ✅ ビジネスロジック完全実装
│   ├── __init__.py
│   ├── startup.py      # サービス初期化 + 環境変数処理
│   └── chat_service.py # チャット処理 + Cosmos DB統合
├── middleware/          # ✅ 完全実装
│   ├── __init__.py
│   ├── auth.py         # APIキー認証 + OPTIONS処理
│   └── error_handler.py# 統一エラーハンドリング
├── models/              # ✅ Pydanticモデル完全実装
│   ├── __init__.py
│   ├── request.py      # API リクエストモデル
│   └── response.py     # API レスポンスモデル
└── requirements.txt     # 依存関係管理
```

### 2.3 データモデル（実装済み）

#### メッセージ構造

```typescript
// Frontend TypeScript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: 'reasoning' | 'streaming' | 'background';
  effort?: 'low' | 'medium' | 'high';
}
```

```python
# Backend Pydantic
class CreateMessageRequest(BaseModel):
    message: str = Field(..., description="送信するメッセージ")
    session_id: str = Field(..., description="セッションID")

class MessageResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    job_id: Optional[str] = None
    duration: Optional[float] = None
```

#### セッション構造

```python
class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, description="セッションタイトル")
    user_id: str = Field("default", description="ユーザーID")
    mode: Optional[Literal["reasoning", "streaming", "background"]] = Field("reasoning")
    effort: Optional[Literal["low", "medium", "high"]] = Field("low")

class SessionResponse(BaseModel):
    id: str
    title: str
    user_id: str
    created_at: str
    updated_at: str
    mode: str
    effort: str
    message_count: int
```

## 3. Phase 2で解決した技術的課題

### 3.1 CORS問題の完全解決 ✅

**問題**: フロントエンド（localhost:5174）からのAPIリクエストが400 Bad Request

**解決策**:
```python
# main.py - CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", ...],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# sessions.py - 専用OPTIONSエンドポイント
@router.options("/")
async def options_sessions():
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })
```

### 3.2 API認証の統合 ✅

**問題**: 二重認証（ミドルウェア + 依存性注入）によるエラー

**解決策**:
```python
# middleware/auth.py - ミドルウェアのみで認証
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # OPTIONSリクエストはスキップ
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # APIキー検証のみ実装（二重認証を防ぐ）
        api_key = request.headers.get("X-API-Key")
        if api_key != self.api_key:
            return JSONResponse(status_code=401, ...)
```

### 3.3 環境変数管理 ✅

**問題**: LOG_LEVELエラー、コメント付き環境変数の解析失敗

**解決策**:
```python
# services/startup.py - 安全な環境変数解析
log_level = os.getenv("LOG_LEVEL", "INFO").strip().split('#')[0].strip()
```

### 3.4 WebSocket表示問題 ✅

**問題**: WebSocketサーバー未実装なのに接続エラーが常時表示

**解決策**:
```typescript
// ChatContainer.tsx - 適切な条件分岐
{error && !error.includes('接続に失敗しました') && (
    <div className="error-display">
        <p>{error}</p>
    </div>
)}

// useWebSocket.ts - 自動接続を無効化
useEffect(() => {
    // WebSocketサーバーが稼働していないため接続を無効化
    // ストリーミングチャット実装時に有効化
    // if (currentSessionId) {
    //   connect();
    // }
}, [currentSessionId]);
```

## 4. Phase 3実装計画

### 4.1 WebSocketストリーミング実装

```python
# 実装予定のWebSocketイベント
class WebSocketEvents:
    # Server -> Client (ストリーミング)
    STREAM_START = "stream_start"
    MESSAGE_CHUNK = "message_chunk"  
    MESSAGE_COMPLETE = "message_complete"
    
    # バックグラウンドジョブ
    JOB_STARTED = "job_started"
    JOB_STATUS = "job_status"
    JOB_COMPLETED = "job_completed"
```

### 4.2 ユーザー認証システム

```python
# Azure AD B2C統合予定
class AzureADAuth:
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
    
    async def verify_token(self, token: str) -> User:
        # JWT Token検証
        # ユーザー情報取得
        pass
```

### 4.3 予定される追加機能

1. **リアルタイムストリーミング** - WebSocket基盤活用
2. **バックグラウンドジョブ管理** - 進捗表示UI
3. **ファイルアップロード** - マルチパート対応
4. **マルチユーザー対応** - セッション分離

## 5. セキュリティ設計（Phase 2実装済み）

### 5.1 現在の認証方式

```python
# APIキー認証（POC段階）
class APIKeyMiddleware:
    def __init__(self, app, dispatch=None):
        super().__init__(app, dispatch)
        self.api_key = os.getenv("API_KEY")  # test-api-key-123
        
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-Key")
        if api_key != self.api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
```

### 5.2 環境変数管理

```bash
# 現在の環境変数構成
# Azure OpenAI
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=<endpoint>
AZURE_OPENAI_DEPLOYMENT_NAME=O3-pro

# Cosmos DB
COSMOS_DB_ENDPOINT=<endpoint>
COSMOS_DB_API_KEY=<key>
COSMOS_DB_DATABASE_NAME=chat_history_db

# API認証
API_KEY=test-api-key-123

# ログレベル
LOG_LEVEL=INFO
```

## 6. テンプレート化戦略（Phase 2で確立）

### 6.1 再利用可能な構造

1. **Frontend テンプレート** ✅
   - React + TypeScript + Vite構成
   - Zustand状態管理パターン
   - Tailwind CSS設定
   - API通信抽象化

2. **Backend テンプレート** ✅
   - FastAPI + プロジェクト構造
   - 認証ミドルウェア
   - CORS設定
   - Pydanticモデル構造

3. **共通ライブラリ** ✅
   - packages/core: Azure認証
   - packages/handlers: o3-proハンドラー
   - packages/cosmos_history: DB管理

### 6.2 設定外部化

```typescript
// 実装済み設定管理
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key-123';
```

## 7. 開発ガイドライン（Phase 2確立）

### 7.1 実装済みコーディング規約

- **Python**: PEP 8 + 型ヒント完全使用 ✅
- **TypeScript**: 厳格な型チェック ✅
- **API設計**: OpenAPI仕様準拠 ✅
- **エラーハンドリング**: 統一されたエラー形式 ✅

### 7.2 テスト戦略（準備完了）

```python
# 予定されるテスト構造
tests/
├── unit/
│   ├── test_chat_service.py
│   ├── test_auth_middleware.py
│   └── test_session_management.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_websocket_events.py
└── e2e/
    └── test_chat_flow.py
```

## 8. Phase 2の成果と次のステップ

### 8.1 Phase 2達成事項

- ✅ **完全動作するWebチャットアプリケーション**
- ✅ **React + FastAPI + Cosmos DB統合**
- ✅ **CORS問題完全解決**
- ✅ **API認証実装**
- ✅ **o3-pro 3モード完全対応**
- ✅ **セッション管理・履歴保存**
- ✅ **モダンUI（Tailwind CSS）**
- ✅ **型安全性（TypeScript）**

### 8.2 Phase 3への移行計画

**即座に着手（優先度：高）**
1. WebSocketストリーミング機能実装
2. バックグラウンドジョブUI

**数週間内（優先度：中）**
3. Azure AD B2C認証システム
4. マルチユーザー対応

**将来的（優先度：低）**
5. ファイルアップロード機能
6. 分析ダッシュボード

## 更新履歴

- **2025-07-21**: Phase 2完了版に大幅更新
  - 全実装済み機能の詳細化
  - 解決済み技術的課題の記録
  - Phase 3実装計画の追加
  - 実際のコード例とファイル構造の反映
- **2025-01-21**: 初版作成