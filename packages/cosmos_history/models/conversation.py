"""
会話（Conversation）データモデル

検索最適化されたチャット会話管理
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ConversationParticipant:
    """会話参加者"""
    user_id: str
    display_name: str
    role: str = "user"  # user, assistant, admin
    joined_at: Optional[str] = None
    
    def __post_init__(self):
        if self.joined_at is None:
            self.joined_at = datetime.now().isoformat()


@dataclass_json
@dataclass
class ConversationCategory:
    """会話カテゴリー"""
    category_id: str
    category_name: str
    confidence: float = 0.0
    source: str = "manual"  # manual, ai_classification
    
    def is_high_confidence(self) -> bool:
        """高信頼度分類かどうか"""
        return self.confidence >= 0.8


@dataclass_json
@dataclass
class ConversationMetrics:
    """会話メトリクス"""
    message_count: int = 0
    participant_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    conversation_duration: float = 0.0
    
    def update_from_messages(self, messages: List[Dict[str, Any]]):
        """メッセージリストからメトリクス更新"""
        self.message_count = len(messages)
        
        total_duration = 0.0
        response_times = []
        total_tokens = 0
        
        for msg in messages:
            metadata = msg.get("metadata", {})
            total_duration += metadata.get("duration", 0.0)
            total_tokens += metadata.get("tokens", 0)
            
            if msg.get("role") == "assistant" and metadata.get("duration"):
                response_times.append(metadata["duration"])
        
        self.total_tokens = total_tokens
        self.conversation_duration = total_duration
        self.avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0


@dataclass_json
@dataclass
class ConversationTimeline:
    """会話タイムライン"""
    created_at: str
    updated_at: str
    last_message_at: str
    first_message_preview: str = ""
    last_message_preview: str = ""
    
    def update_message_preview(self, content: str, is_first: bool = False):
        """メッセージプレビュー更新"""
        preview = content[:100] + "..." if len(content) > 100 else content
        
        if is_first:
            self.first_message_preview = preview
        
        self.last_message_preview = preview
        self.last_message_at = datetime.now().isoformat()
        self.updated_at = self.last_message_at


@dataclass_json
@dataclass
class ChatConversation:
    """チャット会話モデル（検索最適化）"""
    
    # 必須フィールド
    id: str
    tenant_id: str  # マルチテナント対応
    conversation_id: str
    title: str
    
    # 参加者・カテゴリー（検索重要）
    participants: List[ConversationParticipant] = field(default_factory=list)
    categories: List[ConversationCategory] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # 要約・検索用テキスト
    summary: str = ""
    searchable_text: str = ""
    
    # メトリクス・タイムライン
    metrics: ConversationMetrics = field(default_factory=ConversationMetrics)
    timeline: ConversationTimeline = field(default_factory=lambda: ConversationTimeline(
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        last_message_at=datetime.now().isoformat()
    ))
    
    # ステータス
    status: str = "active"  # active, archived, deleted
    privacy: str = "private"  # private, shared, public
    archived: bool = False
    bookmarked: bool = False
    
    # TTL（オプション）
    ttl: Optional[int] = None
    
    @classmethod
    def create_new(
        cls,
        tenant_id: str,
        title: str,
        creator_user_id: str,
        creator_display_name: str = "",
        initial_category: Optional[str] = None
    ) -> "ChatConversation":
        """新規会話作成"""
        
        conversation_id = str(uuid.uuid4())[:12]  # 短縮ID
        timestamp = datetime.now().isoformat()
        
        # 作成者を参加者に追加
        creator = ConversationParticipant(
            user_id=creator_user_id,
            display_name=creator_display_name or creator_user_id,
            role="user",
            joined_at=timestamp
        )
        
        conversation = cls(
            id=f"conv_{conversation_id}",
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            title=title,
            participants=[creator]
        )
        
        # 初期カテゴリー設定
        if initial_category:
            conversation.add_category(initial_category, initial_category, 1.0, "manual")
        
        # 検索用テキスト生成
        conversation.update_searchable_text()
        
        return conversation
    
    def add_participant(self, user_id: str, display_name: str, role: str = "user"):
        """参加者追加"""
        # 重複チェック
        if any(p.user_id == user_id for p in self.participants):
            return
        
        participant = ConversationParticipant(
            user_id=user_id,
            display_name=display_name,
            role=role
        )
        
        self.participants.append(participant)
        self.metrics.participant_count = len(self.participants)
        self.update_searchable_text()
    
    def add_category(self, category_id: str, category_name: str, confidence: float = 0.0, source: str = "manual"):
        """カテゴリー追加"""
        # 重複チェック
        if any(c.category_id == category_id for c in self.categories):
            return
        
        category = ConversationCategory(
            category_id=category_id,
            category_name=category_name,
            confidence=confidence,
            source=source
        )
        
        self.categories.append(category)
        self.update_searchable_text()
    
    def add_tag(self, tag: str):
        """タグ追加"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_searchable_text()
    
    def update_searchable_text(self):
        """検索用テキスト更新"""
        text_parts = [
            str(self.title) if self.title else "",
            str(self.summary) if self.summary else "",
            " ".join([str(p.display_name) for p in self.participants if p.display_name]),
            " ".join([str(c.category_name) for c in self.categories if c.category_name]),
            " ".join([str(tag) for tag in self.tags if tag])
        ]
        
        # 日本語対応の正規化
        full_text = " ".join(filter(None, text_parts))
        self.searchable_text = self._normalize_search_text(full_text)
    
    def _normalize_search_text(self, text: str) -> str:
        """検索用テキスト正規化"""
        # 小文字化
        text = text.lower()
        
        # 特殊文字除去（日本語文字は保持）
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', text)
        
        # 連続空白を単一空白に
        text = ' '.join(text.split())
        
        return text
    
    def update_from_message(self, message_content: str, is_first_message: bool = False):
        """メッセージからの情報更新"""
        
        # タイムライン更新
        self.timeline.update_message_preview(message_content, is_first_message)
        
        # 検索用テキスト更新（メッセージ内容は含めない - 別途message検索で対応）
        self.update_searchable_text()
    
    def get_participant_names(self) -> List[str]:
        """参加者名一覧取得"""
        return [p.display_name for p in self.participants]
    
    def get_category_names(self) -> List[str]:
        """カテゴリー名一覧取得"""
        return [c.category_name for c in self.categories]
    
    def is_participant(self, user_id: str) -> bool:
        """指定ユーザーが参加者かどうか"""
        return any(p.user_id == user_id for p in self.participants)
    
    def has_category(self, category_id: str) -> bool:
        """指定カテゴリーが設定されているかどうか"""
        return any(c.category_id == category_id for c in self.categories)
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Cosmos DB用辞書変換"""
        data = self.to_dict()
        
        # パーティションキー確認
        data["tenantId"] = self.tenant_id
        
        # Cosmos DB用フィールド変換
        data["conversationId"] = self.conversation_id
        
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: Dict[str, Any]) -> "ChatConversation":
        """Cosmos DB辞書からオブジェクト作成"""
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"ChatConversation(id={self.id}, title='{self.title}', participants={len(self.participants)})"