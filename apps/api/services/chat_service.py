"""
チャットサービス
ビジネスロジックの実装
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from loguru import logger

from core.azure_auth import O3ProClient
from handlers import ReasoningHandler, StreamingHandler, BackgroundHandler
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager
from cosmos_history.config import load_config_from_env


class ChatService:
    """チャットサービス"""
    
    def __init__(self, client: O3ProClient):
        self.client = client
        self.reasoning_handler = ReasoningHandler(client)
        self.streaming_handler = StreamingHandler(client)
        self.background_handler = BackgroundHandler(client)
        self.history_manager = None
        self.sessions: Dict[str, Dict] = {}  # メモリ内セッション管理
    
    async def initialize(self):
        """非同期初期化"""
        try:
            # Cosmos DB初期化を試みる
            cosmos_config = load_config_from_env()
            if cosmos_config.cosmos_db.endpoint:
                cosmos_client = CosmosDBClient(cosmos_config.cosmos_db)
                self.history_manager = CosmosHistoryManager(
                    cosmos_client, 
                    "default_tenant", 
                    cosmos_config
                )
                logger.info("Cosmos DB履歴管理初期化完了")
            else:
                logger.warning("Cosmos DB設定が見つかりません。履歴管理は無効です。")
        except Exception as e:
            logger.error(f"Cosmos DB初期化エラー: {e}")
            logger.warning("履歴管理は無効になります")
    
    async def create_session(
        self, 
        title: str = None, 
        user_id: str = "default", 
        mode: str = "reasoning", 
        effort: str = "low"
    ) -> Dict:
        """新規セッション作成"""
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "title": title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "mode": mode,
            "effort": effort,
            "message_count": 0
        }
        
        self.sessions[session_id] = session
        
        # Cosmos DBに会話を作成
        if self.history_manager:
            try:
                conversation = await self.history_manager.create_conversation(
                    title=session["title"],
                    creator_user_id=user_id
                )
                session["cosmos_conversation_id"] = conversation.conversation_id
            except Exception as e:
                logger.error(f"Cosmos DB会話作成エラー: {e}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """セッション取得"""
        return self.sessions.get(session_id)
    
    async def update_session_mode(self, session_id: str, mode: str, effort: str = "low") -> bool:
        """セッションモード更新"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        valid_modes = ["reasoning", "streaming", "background"]
        valid_efforts = ["low", "medium", "high"]
        
        if mode not in valid_modes or effort not in valid_efforts:
            return False
        
        session["mode"] = mode
        session["effort"] = effort
        session["updated_at"] = datetime.now().isoformat()
        
        return True
    
    async def send_message(self, session_id: str, message: str) -> Dict:
        """メッセージ送信（通常モード）"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        mode = session["mode"]
        effort = session["effort"]
        
        # メッセージ処理
        if mode == "reasoning":
            result = self.reasoning_handler.basic_reasoning(message, effort=effort)
        elif mode == "background":
            result = self.background_handler.start_background_task(message, effort=effort)
        else:
            raise ValueError(f"Unsupported mode for sync processing: {mode}")
        
        # 履歴保存
        if self.history_manager and "cosmos_conversation_id" in session:
            try:
                # ユーザーメッセージ
                await self.history_manager.add_message(
                    conversation_id=session["cosmos_conversation_id"],
                    sender_user_id=session["user_id"],
                    sender_display_name="User",
                    content=message
                )
                
                # アシスタント応答（backgroundモード以外）
                if mode != "background" and result["success"]:
                    await self.history_manager.add_message(
                        conversation_id=session["cosmos_conversation_id"],
                        sender_user_id="assistant",
                        sender_display_name="O3-Pro",
                        content=result["response"]
                    )
            except Exception as e:
                logger.error(f"履歴保存エラー: {e}")
        
        # セッション更新
        session["message_count"] += 1
        session["updated_at"] = datetime.now().isoformat()
        
        return result
    
    async def stream_message(self, session_id: str, message: str, callback):
        """ストリーミングメッセージ処理"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        effort = session["effort"]
        
        # ストリーミング処理
        result = self.streaming_handler.stream_with_callback(
            message, 
            callback, 
            effort=effort
        )
        
        # 履歴保存
        if self.history_manager and "cosmos_conversation_id" in session and result["success"]:
            try:
                # ユーザーメッセージ
                await self.history_manager.add_message(
                    conversation_id=session["cosmos_conversation_id"],
                    sender_user_id=session["user_id"],
                    sender_display_name="User",
                    content=message
                )
                
                # アシスタント応答
                await self.history_manager.add_message(
                    conversation_id=session["cosmos_conversation_id"],
                    sender_user_id="assistant",
                    sender_display_name="O3-Pro",
                    content=result["response"]
                )
            except Exception as e:
                logger.error(f"履歴保存エラー: {e}")
        
        # セッション更新
        session["message_count"] += 1
        session["updated_at"] = datetime.now().isoformat()
        
        return result
    
    async def get_job_status(self, job_id: str) -> Dict:
        """バックグラウンドジョブステータス取得"""
        return self.background_handler.check_status(job_id)
    
    async def get_job_result(self, job_id: str) -> Dict:
        """バックグラウンドジョブ結果取得"""
        return self.background_handler.get_result(job_id)
    
    async def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """履歴取得"""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        if self.history_manager and "cosmos_conversation_id" in session:
            try:
                messages = await self.history_manager.get_conversation_messages(
                    session["cosmos_conversation_id"],
                    limit=limit
                )
                
                # フォーマット変換
                formatted = []
                for msg in messages:
                    formatted.append({
                        "id": msg.message_id,
                        "role": "user" if msg.sender.user_id == session["user_id"] else "assistant",
                        "content": msg.content.text or msg.content.display_text,
                        "timestamp": msg.timestamp.isoformat(),
                        "sender": msg.sender.display_name
                    })
                
                return formatted
            except Exception as e:
                logger.error(f"履歴取得エラー: {e}")
        
        return []