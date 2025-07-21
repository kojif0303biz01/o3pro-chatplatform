"""
チャット履歴データモデル
"""

from .conversation import ChatConversation, ConversationParticipant, ConversationCategory
from .message import ChatMessage, MessageMetadata

__all__ = [
    "ChatConversation", 
    "ConversationParticipant", 
    "ConversationCategory",
    "ChatMessage", 
    "MessageMetadata"
]