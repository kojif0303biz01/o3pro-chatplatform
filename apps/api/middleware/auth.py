"""
認証ミドルウェア
POC段階ではシンプルなAPIキー認証を実装
"""

import os
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    """APIキー認証ミドルウェア"""
    
    def __init__(self, app, dispatch=None):
        super().__init__(app, dispatch)
        self.api_key = os.getenv("API_KEY")
        # デバッグ用
        print(f"🔑 APIキーミドルウェア初期化: {self.api_key[:8] if self.api_key else 'None'}...")
        self.excluded_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """リクエスト処理"""
        # 除外パスはスキップ
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # WebSocketは別途処理
        if request.url.path.startswith("/ws"):
            return await call_next(request)
        
        # OPTIONSリクエスト（プリフライト）は認証をスキップ
        if request.method == "OPTIONS":
            print(f"⚡ OPTIONSリクエストをスキップ: {request.url.path}")
            return await call_next(request)
        
        # APIキー検証
        api_key = request.headers.get("X-API-Key")
        
        # デバッグ用
        print(f"🔍 リクエスト: {request.url.path}")
        print(f"🔑 受信APIキー: '{api_key}'" if api_key else "🔑 受信APIキー: None")
        print(f"🔑 期待APIキー: '{self.api_key}'" if self.api_key else "🔑 期待APIキー: None")
        print(f"🔑 一致判定: {api_key == self.api_key}")
        
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key missing"}
            )
        
        if api_key != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"}
            )
        
        # 認証成功
        print(f"✅ 認証成功: {request.url.path}")
        response = await call_next(request)
        print(f"📤 レスポンス: {response.status_code}")
        return response


# FastAPI用のAPIキーヘッダー定義
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = None) -> bool:
    """APIキー検証関数"""
    if not api_key:
        return False
    
    expected_key = os.getenv("API_KEY")
    return api_key == expected_key


async def get_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """APIキー取得（依存性注入用）"""
    if not api_key or not await verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key