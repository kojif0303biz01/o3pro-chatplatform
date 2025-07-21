# Design Document - O3-Pro Chat Platform

## 1. システムアーキテクチャ

### 1.1 Phase 2完了構成（開発環境）

```
┌─────────────────────────────────────────────────────────┐
│  開発環境 (localhost)                              │
│                                                       │
│  ┌────────────────────┐    ┌───────────────────┐  │
│  │ Frontend (React+TS) │◄──►│ FastAPI Backend  │  │
│  │ Vite Dev Server     │    │ + Socket.IO      │  │
│  │ (localhost:5174)    │    │ (localhost:8000) │  │
│  └────────────────────┘    └─────────┬─────────┘  │
└─────────────────────────────────────────────────┼────┘
                                              │
             ┌──────────────────────────────────────┼───────────────────┐
             │                                  ▼                  │
        ┌────────────┐         ┌─────────────────┐         ┌──────────────┐
        │ Cosmos DB  │         │  Azure OpenAI   │         │  ローカル環境  │
        │ (履歴管理)  │         │    o3-pro       │         │  (.envファイル) │
        └────────────┘         └─────────────────┘         └──────────────┘
```

### 1.2 Phase 3ターゲット構成（Azure Container Apps）

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                      Azure Container Apps Environment                    │
│                            (env-poc-apps)                               │
│                                                                         │
│  ┌─────────────────────────┐   ┌──────────────────────────────────────────┐  │
│  │      Static Web App       │   │         Container Apps                    │  │
│  │                         │   │                                          │  │
│  │  React + TypeScript     │◄─►│  FastAPI Backend                       │  │
│  │  + Tailwind CSS         │   │  + Azure Functions Integration         │  │
│  │  (Build Optimized)      │   │  + WebSocket (Socket.IO)               │  │
│  │                         │   │  + Background Processing               │  │
│  └─────────────────────────┘   │  + KEDA Autoscaling                    │  │
│                              │  + Dapr Integration                    │  │
│  ┌─────────────────────────┐   │  + Container Image (ACR)               │  │
│  │   CI/CD Pipeline        │   └────────────────┬───────────────────────┘  │
│  │                         │                    │                               │
│  │  GitHub Actions         │                    │                               │
│  │  + Auto Build & Deploy  │                    │                               │
│  │  + Environment Mgmt     │                    │                               │
│  └─────────────────────────┘                    │                               │
└─────────────────────────────────────────────────┼───────────────────────────────┘
                                                            │
      ┌──────────────────────────────────────────────────┼──────────────────────────────┐
      │                                              ▼                          │
 ┌────────────────────────────────────────────────────────────────────────────────────┐
 │                           Azure Support Services                          │
 │                                                                        │
 │ ┌─────────────┐ ┌──────────────────┐ ┌─────────────────────┐ │
 │ │ Cosmos DB    │ │ Azure OpenAI o3  │ │ Container Registry     │ │
 │ │ (履歴管理)    │ │ (チャット処理)      │ │ (ACR)                  │ │
 │ └─────────────┘ └──────────────────┘ └─────────────────────┘ │
 │                                                                        │
 │ ┌────────────────────┐ ┌─────────────────────────────────┐ │
 │ │ Key Vault            │ │ Application Insights + Logs       │ │
 │ │ (機密管理)           │ │ (監視・アラート・分析)            │ │
 │ └────────────────────┘ └─────────────────────────────────┘ │
 └────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 プロジェクト構造（現在からPhase 3ターゲット）

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

## 4. Phase 3: Azure Container Apps展開設計

### 4.1 コンテナ化戦略

#### 4.1.1 FastAPIコンテナ設計

```dockerfile
# Dockerfileサンプル
FROM python:3.12-slim

# メタデータ
LABEL maintainer="o3pro-chatplatform" \
      version="1.0.0" \
      description="FastAPI Backend for Container Apps"

# ワーキングディレクトリ
WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポート公開
EXPOSE 8000

# 実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4.1.2 Reactスタティックビルド戦略

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["anonymous"]
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html"
  },
  "mimeTypes": {
    ".js": "text/javascript",
    ".json": "application/json"
  }
}
```

### 4.2 Azure Container Apps設定

#### 4.2.1 Container App定義サンプル

```yaml
# container-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: o3pro-chatbot-api
  namespace: env-poc-apps
spec:
  replicas: 2
  selector:
    matchLabels:
      app: o3pro-chatbot-api
  template:
    metadata:
      labels:
        app: o3pro-chatbot-api
    spec:
      containers:
      - name: api
        image: acrpocapps.azurecr.io/o3pro-chatbot-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 4.2.2 スケーリング設定

```yaml
# KEDAスケーリング設定
scale:
  minReplicas: 1
  maxReplicas: 10
  rules:
  - name: "http-scaler"
    type: "http"
    metadata:
      concurrentRequests: "30"
  - name: "cpu-scaler"
    type: "cpu"
    metadata:
      targetAverageUtilization: "70"
```

### 4.3 Azure Functions 統合設計

#### 4.3.1 Functions on Container Apps

```python
# Azure Functions 統合サンプル
import azure.functions as func
from apps.api.services.chat_service import ChatService

app = func.FunctionApp()

@app.route(route="background_process", auth_level=func.AuthLevel.FUNCTION)
async def background_process(req: func.HttpRequest) -> func.HttpResponse:
    """バックグラウンド処理用Function"""
    
    try:
        # 非同期ジョブ処理
        job_id = req.params.get('job_id')
        chat_service = ChatService()
        result = await chat_service.process_background_job(job_id)
        
        return func.HttpResponse(
            f"Job {job_id} completed: {result}",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer")
async def job_monitor(timer: func.TimerRequest) -> None:
    """ジョブステータス監視"""
    # 定期的なジョブ状態チェック
    pass
```

### 4.4 CI/CDパイプライン設計

#### 4.4.1 GitHub Actionsワークフロー

```yaml
# .github/workflows/deploy-container-apps.yml
name: Deploy to Azure Container Apps

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: acrpocapps.azurecr.io
  IMAGE_NAME: o3pro-chatbot-api

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./apps/api
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Deploy to Container Apps
      uses: azure/container-apps-deploy-action@v1
      with:
        imageToDeploy: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        containerAppName: o3pro-chatbot-api
        resourceGroup: rg-poc-apps
        containerAppEnvironment: env-poc-apps
```

### 4.5 セキュリティ強化設計

#### 4.5.1 Managed Identity + Key Vault

```python
# 機密管理強化
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class SecureConfigManager:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.vault_url = "https://kv-poc-apps.vault.azure.net/"
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
    
    async def get_secret(self, secret_name: str) -> str:
        """機密情報安全取得"""
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise
```

### 4.6 監視・運用設計

#### 4.6.1 Application Insights統合

```python
# アプリケーション監視
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

class MonitoringService:
    def __init__(self):
        # Application Insights接続キー
        self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        
        # ログ設定
        logger = logging.getLogger(__name__)
        logger.addHandler(AzureLogHandler(connection_string=self.connection_string))
        
        # トレーシング設定
        config_integration.trace_integrations(['requests', 'sqlalchemy'])
        self.tracer = Tracer(
            exporter=AzureExporter(connection_string=self.connection_string),
            sampler=ProbabilitySampler(1.0)
        )
    
    def track_dependency(self, name: str, data: dict):
        """依存関係追跡"""
        with self.tracer.span(name=name) as span:
            span.add_attribute("dependency.type", data.get("type", "unknown"))
            span.add_attribute("dependency.data", str(data))
```

### 4.7 Phase 3 実装ロードマップ

#### フェーズ3-1: インフラ構築 (1-2週間)

**Week 1: 基盤環境構築**
- Azure Container Apps Environment作成 (env-poc-apps)
- Container Registry設定・Private Endpoint構成
- Key Vault + Managed Identity設定
- VNet統合・Network Security Group設定

**Week 2: アプリケーションコンテナ化**
- FastAPI Dockerfile最適化・マルチステージビルド
- Reactビルドパイプライン構築
- 環境変数管理のContainer Apps統合
- ヘルスチェック・ロードバランシング実装

#### フェーズ3-2: デプロイメント自動化 (1週間)

**デプロイメントパイプライン構築**
- GitHub Actionsワークフロー作成
- Container Appsデプロイ自動化
- Static Web Appsデプロイ統合
- 環境別設定 (dev/staging/prod)

#### フェーズ3-3: 監視・運用 (1週間)

**監視システム構築**
- Application Insights統合・カスタムメトリクス
- Log Analytics Workspace設定・クエリ作成
- アラートルール設定・通知構成
- パフォーマンスダッシュボード作成

#### フェーズ3-4: Azure Functions統合 (2-3週間)

**Functions on Container Apps**
- Container Apps環境でのFunctionsホスティング
- Event-driven処理・KEDAスケーリング
- Dapr統合・マイクロサービス連携
- バックグラウンドジョブ処理フレームワーク

#### 将来フェーズ (Phase 4以降)
- WebSocketストリーミング機能
- ユーザー認証システム (Azure AD B2C)
- マルチユーザー対応・権限管理
- ファイルアップロード機能

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

### 8.2 Phase 3: Azure Container Apps展開戦略

**即座に着手（優先度：最高）**
1. Azure Container Apps Environment構築 - env-poc-apps環境作成
2. アプリケーションコンテナ化 - FastAPI + ReactのBuild最適化
3. CI/CDパイプライン構築 - GitHub Actions自動デプロイ
4. セキュリティ強化 - Key Vault + Managed Identity

**数週間内（優先度：高）**
5. 監視システム統合 - Application Insights + Log Analytics
6. Azure Functions統合 - Container Apps上でのサーバーレス処理
7. スケーリング最適化 - KEDA + 自動スケール設定

**将来的（Phase 4以降）**
8. WebSocketストリーミング機能実装
9. ユーザー認証システム (Azure AD B2C)
10. マルチユーザー対応・権限管理

## Phase 3 設計指針・原則

### アーキテクチャ原則

1. **Cloud Native First** - Kubernetesベース・12 Factor App準拠
2. **セキュリティバイデザイン** - Zero Trust・最小権限の原則
3. **可観測性重視** - ログ・メトリクス・トレーシング統合
4. **Infrastructure as Code** - 再現可能・バージョン管理
5. **漸進的移行** - ゼロダウンタイム・フェーズ別展開

### 技術的決定事項

1. **Container Runtime**: containerd (Container Appsデフォルト)
2. **Service Mesh**: Dapr (Container Appsネイティブ)
3. **Autoscaling**: KEDA (Event-driven + HTTP/CPUスケーリング)
4. **Image Registry**: Azure Container Registry (Private + Geo-replication)
5. **Secret Management**: Key Vault + Managed Identity
6. **Monitoring**: Application Insights + Azure Monitor
7. **CI/CD**: GitHub Actions (Azure公式サポート)

### パフォーマンスターゲット

- **コールドスタート**: < 5秒 (Consumptionプラン)
- **レスポンスタイム**: < 100ms (P50), < 500ms (P95)
- **スケールアウト**: 0から100インスタンス (30秒以内)
- **可用性**: 99.95% (Container Apps SLA)
- **コスト効率**: 現行比 +15%以内

### セキュリティフレームワーク

1. **Identity & Access**
   - Managed Identity (System-assigned + User-assigned)
   - Azure ADロールベースアクセス制御
   - Key Vault機密管理統合

2. **Network Security**
   - VNet統合 (Private Endpoint使用)
   - Application Gateway + WAF
   - Network Security Groupルール

3. **Application Security**
   - Container Image Scanning (Defender for Containers)
   - Secretsのruntime注入
   - HTTPS Only + TLS 1.2+

## 更新履歴

- **2025-07-21**: Phase 3 Azure Container Apps展開設計に大幅更新
  - Container Apps + Functions統合設計詳細化
  - CI/CDパイプライン・コンテナ化戦略
  - セキュリティフレームワーク・監視設計
  - アーキテクチャ決定・パフォーマンスターゲット
- **2025-07-21**: Phase 2完了版に大幅更新
  - 全実装済み機能の詳細化
  - 解決済み技術的課題の記録
  - 実際のコード例とファイル構造の反映
- **2025-01-21**: 初版作成