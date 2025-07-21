"""
Azure Cosmos DB チャット履歴管理システム

検索最適化されたチャット履歴管理ライブラリ
"""

__version__ = "1.0.0"
__author__ = "Azure o3-pro Toolkit Team"

from .models.conversation import ChatConversation
from .models.message import ChatMessage

__all__ = ["ChatConversation", "ChatMessage"]