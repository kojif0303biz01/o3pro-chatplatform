"""
WebSocketエンドポイント
"""

import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from services.startup import get_chat_service
from middleware.auth import verify_api_key


router = APIRouter()


class ConnectionManager:
    """WebSocket接続管理"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_json(self, client_id: str, data: Dict[str, Any]):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    api_key: str = Query(...),
    session_id: str = Query(...)
):
    """WebSocketチャットエンドポイント"""
    
    # API Key検証
    if not await verify_api_key(api_key):
        await websocket.close(code=1008, reason="Invalid API key")
        return
    
    client_id = f"{session_id}_{id(websocket)}"
    
    try:
        # 接続受け入れ
        await manager.connect(websocket, client_id)
        
        chat_service = get_chat_service()
        
        # セッション確認
        session = await chat_service.get_session(session_id)
        if not session:
            await websocket.close(code=1008, reason="Session not found")
            return
        
        # 接続成功通知
        await manager.send_json(client_id, {
            "type": "connected",
            "session_id": session_id,
            "mode": session["mode"],
            "effort": session["effort"]
        })
        
        # メッセージループ
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            if event_type == "send_message":
                await handle_send_message(client_id, session_id, data)
            
            elif event_type == "change_mode":
                await handle_change_mode(client_id, session_id, data)
            
            elif event_type == "get_job_status":
                await handle_get_job_status(client_id, data)
            
            elif event_type == "ping":
                await manager.send_json(client_id, {"type": "pong"})
            
            else:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": f"Unknown event type: {event_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(client_id)


async def handle_send_message(client_id: str, session_id: str, data: Dict[str, Any]):
    """メッセージ送信処理"""
    try:
        chat_service = get_chat_service()
        session = await chat_service.get_session(session_id)
        
        message = data.get("message", "")
        if not message:
            await manager.send_json(client_id, {
                "type": "error",
                "message": "Message is required"
            })
            return
        
        # ストリーミングモードの場合
        if session["mode"] == "streaming":
            # ストリーミング開始通知
            await manager.send_json(client_id, {
                "type": "stream_start"
            })
            
            # コールバック関数
            async def stream_callback(chunk: str):
                await manager.send_json(client_id, {
                    "type": "message_chunk",
                    "chunk": chunk
                })
            
            # ストリーミング処理
            result = await chat_service.stream_message(
                session_id=session_id,
                message=message,
                callback=stream_callback
            )
            
            # 完了通知
            await manager.send_json(client_id, {
                "type": "message_complete",
                "duration": result.get("duration", 0)
            })
        
        else:
            # 通常処理
            result = await chat_service.send_message(
                session_id=session_id,
                message=message
            )
            
            if session["mode"] == "background":
                # バックグラウンドジョブ開始通知
                await manager.send_json(client_id, {
                    "type": "job_started",
                    "job_id": result.get("job_id"),
                    "message": "Background processing started"
                })
            else:
                # 通常レスポンス
                await manager.send_json(client_id, {
                    "type": "message_complete",
                    "response": result.get("response"),
                    "duration": result.get("duration", 0)
                })
    
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": str(e)
        })


async def handle_change_mode(client_id: str, session_id: str, data: Dict[str, Any]):
    """モード変更処理"""
    try:
        chat_service = get_chat_service()
        
        mode = data.get("mode")
        effort = data.get("effort", "low")
        
        success = await chat_service.update_session_mode(
            session_id=session_id,
            mode=mode,
            effort=effort
        )
        
        if success:
            await manager.send_json(client_id, {
                "type": "mode_changed",
                "mode": mode,
                "effort": effort
            })
        else:
            await manager.send_json(client_id, {
                "type": "error",
                "message": "Failed to change mode"
            })
    
    except Exception as e:
        logger.error(f"Mode change error: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": str(e)
        })


async def handle_get_job_status(client_id: str, data: Dict[str, Any]):
    """ジョブステータス取得処理"""
    try:
        chat_service = get_chat_service()
        
        job_id = data.get("job_id")
        if not job_id:
            await manager.send_json(client_id, {
                "type": "error",
                "message": "Job ID is required"
            })
            return
        
        status = await chat_service.get_job_status(job_id)
        
        if status["success"] and status["status"] == "completed":
            # 完了している場合は結果も取得
            result = await chat_service.get_job_result(job_id)
            await manager.send_json(client_id, {
                "type": "job_completed",
                "job_id": job_id,
                "response": result.get("response"),
                "total_time": result.get("total_time")
            })
        else:
            # ステータスのみ返す
            await manager.send_json(client_id, {
                "type": "job_status",
                "job_id": job_id,
                "status": status.get("status"),
                "elapsed_time": status.get("elapsed_time")
            })
    
    except Exception as e:
        logger.error(f"Job status error: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": str(e)
        })