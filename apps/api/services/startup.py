"""
スタートアップサービス
アプリケーション起動時の初期化処理
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# 環境変数読み込み
load_dotenv()
load_dotenv(".env.cosmos")

# インポートパス設定
project_root = Path(__file__).parent.parent.parent.parent
packages_path = project_root / "packages"
sys.path.insert(0, str(packages_path))

from core.azure_auth import O3ProConfig, O3ProClient
from services.chat_service import ChatService


# グローバルインスタンス
chat_service: ChatService = None


async def initialize_services():
    """サービス初期化"""
    global chat_service
    
    try:
        # ログ設定
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().split('#')[0].strip()
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level
        )
        
        logger.info("サービス初期化開始...")
        
        # Azure OpenAI初期化
        config = O3ProConfig()
        if not config.validate():
            raise ValueError("Azure OpenAI設定が無効です")
        
        client = O3ProClient(config)
        if not client.is_ready():
            raise ValueError("Azure OpenAI接続に失敗しました")
        
        logger.info("Azure OpenAI接続成功")
        
        # チャットサービス初期化
        chat_service = ChatService(client)
        await chat_service.initialize()
        
        logger.info("チャットサービス初期化完了")
        
    except Exception as e:
        logger.error(f"サービス初期化エラー: {e}")
        raise


def get_chat_service() -> ChatService:
    """チャットサービス取得"""
    if not chat_service:
        raise RuntimeError("チャットサービスが初期化されていません")
    return chat_service