"""
セッション管理エンドポイント
"""

from typing import List

from fastapi import APIRouter, HTTPException, Request, Response
from loguru import logger

from models.request import CreateSessionRequest, UpdateSessionModeRequest
from models.response import SessionResponse
from services.startup import get_chat_service


router = APIRouter()


@router.options("/")
async def options_sessions():
    """OPTIONSリクエスト用エンドポイント"""
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest
):
    """新規セッション作成"""
    try:
        chat_service = get_chat_service()
        
        session = await chat_service.create_session(
            title=request.title,
            user_id=request.user_id,
            mode=request.mode,
            effort=request.effort
        )
        
        return SessionResponse(**session)
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str
):
    """セッション情報取得"""
    try:
        chat_service = get_chat_service()
        
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{session_id}/mode", response_model=SessionResponse)
async def update_session_mode(
    session_id: str,
    request: UpdateSessionModeRequest
):
    """セッションモード更新"""
    try:
        chat_service = get_chat_service()
        
        # モード更新
        success = await chat_service.update_session_mode(
            session_id=session_id,
            mode=request.mode,
            effort=request.effort
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update session mode")
        
        # 更新後のセッション取得
        session = await chat_service.get_session(session_id)
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session mode update error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    user_id: str = "default"
):
    """セッション一覧取得"""
    try:
        chat_service = get_chat_service()
        
        # 簡易実装：メモリ内の全セッションから該当ユーザーのものを取得
        sessions = []
        for session in chat_service.sessions.values():
            if session.get("user_id") == user_id:
                sessions.append(SessionResponse(**session))
        
        return sessions
        
    except Exception as e:
        logger.error(f"Session listing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")