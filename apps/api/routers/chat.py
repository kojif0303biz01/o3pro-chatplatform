"""
チャット関連エンドポイント
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from models.request import SendMessageRequest, GetHistoryRequest
from models.response import MessageResponse, HistoryResponse
from middleware.auth import get_api_key
from services.startup import get_chat_service


router = APIRouter()


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    api_key: str = Depends(get_api_key)
):
    """メッセージ送信エンドポイント"""
    try:
        chat_service = get_chat_service()
        
        # セッション確認
        session = await chat_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # メッセージ処理
        result = await chat_service.send_message(
            session_id=request.session_id,
            message=request.message
        )
        
        return MessageResponse(**result)
        
    except ValueError as e:
        logger.error(f"Message processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(
    session_id: str,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """履歴取得エンドポイント"""
    try:
        chat_service = get_chat_service()
        
        # セッション確認
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 履歴取得
        messages = await chat_service.get_history(session_id, limit=limit)
        
        return HistoryResponse(
            session_id=session_id,
            messages=messages,
            total_count=session.get("message_count", 0)
        )
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")