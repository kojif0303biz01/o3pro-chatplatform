#!/usr/bin/env python3
"""
O3-Pro Chat Platform API
FastAPIベースのバックエンドAPI
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# パッケージのパスを追加
packages_path = project_root / "packages"
sys.path.insert(0, str(packages_path))

from routers import chat, sessions, websocket
from middleware.auth import APIKeyMiddleware
from middleware.error_handler import error_handler_middleware
from services.startup import initialize_services


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    print("🚀 O3-Pro Chat API 起動中...")
    await initialize_services()
    print("✅ サービス初期化完了")
    
    yield
    
    # シャットダウン時の処理
    print("👋 O3-Pro Chat API シャットダウン中...")


# FastAPIアプリケーション作成
app = FastAPI(
    title="O3-Pro Chat Platform API",
    description="Azure OpenAI o3-proを使用したチャットプラットフォームAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カスタムミドルウェア
app.middleware("http")(error_handler_middleware)
app.add_middleware(APIKeyMiddleware)

# ルーター登録
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "O3-Pro Chat Platform API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": "O3-Pro Chat API",
        "timestamp": os.popen('date').read().strip()
    }


@app.get("/api/v1/info")
async def api_info():
    """API情報エンドポイント"""
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "features": {
            "chat": True,
            "streaming": True,
            "background_jobs": True,
            "cosmos_db": True
        }
    }


if __name__ == "__main__":
    # 開発サーバー起動
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )