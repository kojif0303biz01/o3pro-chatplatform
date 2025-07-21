"""
メッセージ（Message）データモデル

検索最適化されたチャットメッセージ管理
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MessageSender:
    """メッセージ送信者"""
    user_id: str
    display_name: str
    role: str = "user"  # user, assistant, system


@dataclass_json
@dataclass
class MessageContent:
    """メッセージ内容"""
    text: str
    original_text: str = ""
    searchable_text: str = ""
    content_type: str = "text"  # text, image, file, code
    language: str = "ja"
    
    def __post_init__(self):
        if not self.original_text:
            self.original_text = self.text
        if not self.searchable_text:
            self.searchable_text = self._create_searchable_text(self.text)
    
    def _create_searchable_text(self, text: str) -> str:
        """検索用テキスト生成"""
        # 小文字化
        search_text = text.lower()
        
        # 特殊文字除去（日本語文字は保持）
        search_text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', search_text)
        
        # 連続空白を単一空白に
        search_text = ' '.join(search_text.split())
        
        return search_text


@dataclass_json
@dataclass
class MessageMetadata:
    """メッセージメタデータ"""
    # 技術情報
    mode: str = ""
    effort: str = ""
    duration: float = 0.0
    tokens: int = 0
    model: str = ""
    temperature: float = 0.0
    
    # 分析情報
    intent: str = ""
    sentiment: str = "neutral"  # positive, negative, neutral
    urgency: str = "normal"  # low, normal, high, urgent
    
    # 抽出情報
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)


@dataclass_json
@dataclass
class ThreadInfo:
    """スレッド情報"""
    parent_message_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    thread_depth: int = 0
    has_replies: bool = False


@dataclass_json
@dataclass
class ChatMessage:
    """チャットメッセージモデル（検索最適化）"""
    
    # 必須フィールド
    id: str
    conversation_id: str
    tenant_id: str
    
    # 送信者・内容
    sender: MessageSender
    content: MessageContent
    
    # タイムスタンプ・順序
    timestamp: str
    sequence_number: int = 0
    
    # メタデータ
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    thread_info: ThreadInfo = field(default_factory=ThreadInfo)
    
    # 添付・リアクション
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    
    # TTL（オプション）
    ttl: Optional[int] = None
    
    @classmethod
    def create_new(
        cls,
        conversation_id: str,
        tenant_id: str,
        sender_user_id: str,
        sender_display_name: str,
        content_text: str,
        sender_role: str = "user",
        sequence_number: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ChatMessage":
        """新規メッセージ作成"""
        
        message_id = f"msg_{uuid.uuid4()}"
        timestamp = datetime.now().isoformat()
        
        # 送信者情報
        sender = MessageSender(
            user_id=sender_user_id,
            display_name=sender_display_name,
            role=sender_role
        )
        
        # メッセージ内容
        content = MessageContent(text=content_text)
        
        # メタデータ
        msg_metadata = MessageMetadata()
        if metadata:
            msg_metadata = MessageMetadata.from_dict(metadata)
        
        return cls(
            id=message_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            sender=sender,
            content=content,
            timestamp=timestamp,
            sequence_number=sequence_number,
            metadata=msg_metadata
        )
    
    def add_entity(self, entity_type: str, value: str, confidence: float = 0.0):
        """エンティティ追加"""
        entity = {
            "type": entity_type,
            "value": value,
            "confidence": confidence
        }
        self.metadata.extracted_entities.append(entity)
    
    def add_topic(self, topic: str):
        """トピック追加"""
        if topic not in self.metadata.topics:
            self.metadata.topics.append(topic)
    
    def add_action_item(self, action: str):
        """アクション項目追加"""
        if action not in self.metadata.action_items:
            self.metadata.action_items.append(action)
    
    def add_reaction(self, user_id: str, reaction_type: str, display_name: str = ""):
        """リアクション追加"""
        reaction = {
            "user_id": user_id,
            "display_name": display_name,
            "type": reaction_type,  # like, dislike, helpful, etc.
            "timestamp": datetime.now().isoformat()
        }
        
        # 既存リアクション更新 or 新規追加
        existing_reaction = next(
            (r for r in self.reactions if r["user_id"] == user_id),
            None
        )
        
        if existing_reaction:
            existing_reaction.update(reaction)
        else:
            self.reactions.append(reaction)
    
    def set_as_reply(self, parent_message_id: str, thread_depth: int = 1):
        """返信設定"""
        self.thread_info.parent_message_id = parent_message_id
        self.thread_info.thread_depth = thread_depth
    
    def mark_has_replies(self):
        """返信ありマーク"""
        self.thread_info.has_replies = True
    
    def update_search_text(self):
        """検索テキスト再生成"""
        self.content.searchable_text = self.content._create_searchable_text(self.content.text)
    
    def get_search_keywords(self) -> List[str]:
        """検索キーワード抽出"""
        keywords = []
        
        # 内容から抽出
        words = self.content.searchable_text.split()
        keywords.extend([w for w in words if len(w) >= 2])
        
        # エンティティから抽出
        for entity in self.metadata.extracted_entities:
            if entity["confidence"] > 0.7:  # 高信頼度のみ
                keywords.append(entity["value"].lower())
        
        # トピックから抽出
        keywords.extend([t.lower() for t in self.metadata.topics])
        
        return list(set(keywords))  # 重複除去
    
    def is_from_user(self, user_id: str) -> bool:
        """指定ユーザーからのメッセージかどうか"""
        return self.sender.user_id == user_id
    
    def is_assistant_message(self) -> bool:
        """AIアシスタントからのメッセージかどうか"""
        return self.sender.role == "assistant"
    
    def is_recent(self, hours: int = 24) -> bool:
        """最近のメッセージかどうか"""
        from datetime import datetime, timedelta
        
        message_time = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return message_time > cutoff_time
    
    def has_high_confidence_entities(self, min_confidence: float = 0.8) -> bool:
        """高信頼度エンティティを含むかどうか"""
        return any(
            entity["confidence"] >= min_confidence 
            for entity in self.metadata.extracted_entities
        )
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Cosmos DB用辞書変換"""
        data = self.to_dict()
        
        # パーティションキー確認
        data["conversationId"] = self.conversation_id
        data["tenantId"] = self.tenant_id
        
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Cosmos DB辞書からオブジェクト作成"""
        return cls.from_dict(data)
    
    def to_display_dict(self) -> Dict[str, Any]:
        """表示用辞書（簡略化）"""
        return {
            "id": self.id,
            "sender": {
                "display_name": self.sender.display_name,
                "role": self.sender.role
            },
            "content": self.content.text,
            "timestamp": self.timestamp,
            "metadata": {
                "duration": self.metadata.duration,
                "tokens": self.metadata.tokens
            } if self.metadata.duration > 0 or self.metadata.tokens > 0 else None
        }
    
    def __str__(self) -> str:
        preview = self.content.text[:50] + "..." if len(self.content.text) > 50 else self.content.text
        return f"ChatMessage(id={self.id}, sender={self.sender.display_name}, content='{preview}')"