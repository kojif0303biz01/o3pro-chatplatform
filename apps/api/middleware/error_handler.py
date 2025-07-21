"""
エラーハンドリングミドルウェア
"""

import sys
import traceback
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger


async def error_handler_middleware(request: Request, call_next):
    """グローバルエラーハンドラー"""
    try:
        response = await call_next(request)
        return response
    
    except HTTPException as e:
        # HTTPExceptionはそのまま返す
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "message": e.detail,
                    "type": "http_error",
                    "status_code": e.status_code
                }
            }
        )
    
    except ValueError as e:
        # バリデーションエラー
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": str(e),
                    "type": "validation_error"
                }
            }
        )
    
    except Exception as e:
        # 予期しないエラー
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 開発環境では詳細を返す
        if os.getenv("ENVIRONMENT", "development") == "development":
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": traceback.format_exc().split('\n')
                    }
                }
            )
        else:
            # 本番環境では詳細を隠す
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "type": "internal_error"
                    }
                }
            )


class ChatError(Exception):
    """チャット関連のカスタムエラー"""
    def __init__(self, message: str, error_type: str = "chat_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class SessionError(Exception):
    """セッション関連のカスタムエラー"""
    def __init__(self, message: str, error_type: str = "session_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


import os