"""
データモデルテスト

ChatConversation と ChatMessage モデルの基本動作テスト
"""

import pytest
from datetime import datetime
from cosmos_history.models.conversation import (
    ChatConversation, ConversationParticipant, ConversationCategory,
    ConversationMetrics, ConversationTimeline
)
from cosmos_history.models.message import (
    ChatMessage, MessageSender, MessageContent, MessageMetadata, ThreadInfo
)


class TestChatConversation:
    """ChatConversation モデルテスト"""
    
    def test_create_new_conversation(self):
        """新規会話作成テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user123",
            creator_display_name="テストユーザー"
        )
        
        assert conversation.tenant_id == "test_tenant"
        assert conversation.title == "テスト会話"
        assert conversation.id.startswith("conv_")
        assert conversation.conversation_id is not None
        assert conversation.status == "active"
        assert not conversation.archived
        assert len(conversation.participants) == 1
        assert conversation.participants[0].user_id == "user123"
    
    def test_add_participant(self):
        """参加者追加テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="ユーザー1"
        )
        
        # 参加者追加
        conversation.add_participant("user2", "ユーザー2", "guest")
        
        assert len(conversation.participants) == 2
        assert conversation.is_participant("user2")
        assert conversation.participants[1].role == "guest"
    
    def test_add_category(self):
        """カテゴリー追加テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="ユーザー1"
        )
        
        # カテゴリー追加
        conversation.add_category("tech", "技術", 0.95, "ai_classification")
        
        assert len(conversation.categories) == 1
        assert conversation.categories[0].category_id == "tech"
        assert conversation.categories[0].confidence == 0.95
    
    def test_add_tag(self):
        """タグ追加テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="ユーザー1"
        )
        
        # タグ追加
        conversation.add_tag("重要")
        conversation.add_tag("技術質問")
        conversation.add_tag("重要")  # 重複追加
        
        assert len(conversation.tags) == 2
        assert "重要" in conversation.tags
        assert "技術質問" in conversation.tags
    
    def test_update_from_message(self):
        """メッセージからの更新テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="テスト会話",
            creator_user_id="user1",
            creator_display_name="ユーザー1"
        )
        
        # 最初のメッセージ
        conversation.update_from_message("最初のメッセージです", is_first_message=True)
        
        assert conversation.timeline.first_message_preview == "最初のメッセージです"
        assert conversation.timeline.last_message_preview == "最初のメッセージです"
        
        # 2番目のメッセージ
        conversation.update_from_message("2番目のメッセージです", is_first_message=False)
        
        assert conversation.timeline.first_message_preview == "最初のメッセージです"
        assert conversation.timeline.last_message_preview == "2番目のメッセージです"
    
    def test_update_searchable_text(self):
        """検索可能テキスト更新テスト"""
        conversation = ChatConversation.create_new(
            tenant_id="test_tenant",
            title="プログラミング質問",
            creator_user_id="user1",
            creator_display_name="開発者"
        )
        
        conversation.summary = "Pythonに関する質問です"
        conversation.add_tag("Python")
        conversation.add_tag("プログラミング")
        
        conversation.update_searchable_text()
        
        searchable = conversation.searchable_text
        assert "プログラミング質問" in searchable
        assert "python" in searchable
        assert "開発者" in searchable


class TestChatMessage:
    """ChatMessage モデルテスト"""
    
    def test_create_new_message(self):
        """新規メッセージ作成テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージです",
            sender_role="user",
            sequence_number=1
        )
        
        assert message.conversation_id == "conv_123"
        assert message.tenant_id == "test_tenant"
        assert message.sender.user_id == "user1"
        assert message.sender.display_name == "テストユーザー"
        assert message.content.text == "テストメッセージです"
        assert message.sequence_number == 1
        assert message.id.startswith("msg_")
    
    def test_content_searchable_text(self):
        """検索可能テキスト生成テスト"""
        content = MessageContent("プログラミングの質問です！どう思いますか？")
        
        # 検索用テキストは小文字化・特殊文字除去済み
        assert "プログラミング" in content.searchable_text
        assert "質問" in content.searchable_text
        assert "どう思いますか" in content.searchable_text
        # 特殊文字は除去される
        assert "！" not in content.searchable_text
        assert "？" not in content.searchable_text
    
    def test_add_entity(self):
        """エンティティ追加テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="Pythonについて教えてください"
        )
        
        message.add_entity("technology", "Python", 0.95)
        
        assert len(message.metadata.extracted_entities) == 1
        entity = message.metadata.extracted_entities[0]
        assert entity["type"] == "technology"
        assert entity["value"] == "Python"
        assert entity["confidence"] == 0.95
    
    def test_add_topic(self):
        """トピック追加テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ"
        )
        
        message.add_topic("プログラミング")
        message.add_topic("技術質問")
        message.add_topic("プログラミング")  # 重複
        
        assert len(message.metadata.topics) == 2
        assert "プログラミング" in message.metadata.topics
        assert "技術質問" in message.metadata.topics
    
    def test_add_reaction(self):
        """リアクション追加テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ"
        )
        
        message.add_reaction("user2", "like", "ユーザー2")
        
        assert len(message.reactions) == 1
        reaction = message.reactions[0]
        assert reaction["user_id"] == "user2"
        assert reaction["type"] == "like"
        assert reaction["display_name"] == "ユーザー2"
        
        # 同じユーザーからの異なるリアクション（更新）
        message.add_reaction("user2", "love", "ユーザー2")
        
        assert len(message.reactions) == 1  # 更新されるため数は変わらない
        assert message.reactions[0]["type"] == "love"
    
    def test_set_as_reply(self):
        """返信設定テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="返信メッセージ"
        )
        
        message.set_as_reply("msg_parent_123", thread_depth=2)
        
        assert message.thread_info.parent_message_id == "msg_parent_123"
        assert message.thread_info.thread_depth == 2
    
    def test_get_search_keywords(self):
        """検索キーワード抽出テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="Pythonでデータ分析をしたいです"
        )
        
        message.add_entity("technology", "Python", 0.9)
        message.add_topic("データ分析")
        
        keywords = message.get_search_keywords()
        
        assert "python" in keywords
        assert "データ分析" in keywords
        assert "pythonでデータ分析をしたいです" in keywords or "データ" in keywords
    
    def test_is_from_user(self):
        """ユーザー判定テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ"
        )
        
        assert message.is_from_user("user1")
        assert not message.is_from_user("user2")
    
    def test_is_assistant_message(self):
        """アシスタントメッセージ判定テスト"""
        user_message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="質問です",
            sender_role="user"
        )
        
        assistant_message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="assistant",
            sender_display_name="アシスタント",
            content_text="回答です",
            sender_role="assistant"
        )
        
        assert not user_message.is_assistant_message()
        assert assistant_message.is_assistant_message()
    
    def test_has_high_confidence_entities(self):
        """高信頼度エンティティ判定テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ"
        )
        
        message.add_entity("tech", "Python", 0.6)  # 低信頼度
        assert not message.has_high_confidence_entities(0.8)
        
        message.add_entity("tech", "JavaScript", 0.9)  # 高信頼度
        assert message.has_high_confidence_entities(0.8)
    
    def test_to_cosmos_dict(self):
        """Cosmos DB辞書変換テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ"
        )
        
        cosmos_dict = message.to_cosmos_dict()
        
        assert cosmos_dict["conversationId"] == "conv_123"
        assert cosmos_dict["tenantId"] == "test_tenant"
        assert "id" in cosmos_dict
        assert "sender" in cosmos_dict
        assert "content" in cosmos_dict
    
    def test_to_display_dict(self):
        """表示用辞書変換テスト"""
        message = ChatMessage.create_new(
            conversation_id="conv_123",
            tenant_id="test_tenant",
            sender_user_id="user1",
            sender_display_name="テストユーザー",
            content_text="テストメッセージ",
            metadata={"duration": 2.5, "tokens": 10}
        )
        
        display_dict = message.to_display_dict()
        
        assert display_dict["id"] == message.id
        assert display_dict["sender"]["display_name"] == "テストユーザー"
        assert display_dict["content"] == "テストメッセージ"
        assert display_dict["metadata"]["duration"] == 2.5
        assert display_dict["metadata"]["tokens"] == 10


class TestConversationParticipant:
    """ConversationParticipant テスト"""
    
    def test_create_participant(self):
        """参加者作成テスト"""
        participant = ConversationParticipant(
            user_id="user123",
            display_name="テストユーザー",
            role="admin"
        )
        
        assert participant.user_id == "user123"
        assert participant.display_name == "テストユーザー"
        assert participant.role == "admin"
        assert participant.joined_at is not None


class TestConversationCategory:
    """ConversationCategory テスト"""
    
    def test_create_category(self):
        """カテゴリー作成テスト"""
        category = ConversationCategory(
            category_id="tech",
            category_name="技術",
            confidence=0.95,
            source="ai_classification"
        )
        
        assert category.category_id == "tech"
        assert category.category_name == "技術"
        assert category.confidence == 0.95
        assert category.source == "ai_classification"
        assert category.is_high_confidence() is True


# テスト実行関数
def run_model_tests():
    """モデルテスト実行"""
    print("=== データモデルテスト実行 ===")
    
    try:
        # ChatConversation テスト
        print("🔍 ChatConversation テスト...")
        test_conv = TestChatConversation()
        test_conv.test_create_new_conversation()
        test_conv.test_add_participant()
        test_conv.test_add_category()
        test_conv.test_add_tag()
        test_conv.test_update_from_message()
        test_conv.test_update_searchable_text()
        print("✅ ChatConversation テスト完了")
        
        # ChatMessage テスト
        print("🔍 ChatMessage テスト...")
        test_msg = TestChatMessage()
        test_msg.test_create_new_message()
        test_msg.test_content_searchable_text()
        test_msg.test_add_entity()
        test_msg.test_add_topic()
        test_msg.test_add_reaction()
        test_msg.test_set_as_reply()
        test_msg.test_get_search_keywords()
        test_msg.test_is_from_user()
        test_msg.test_is_assistant_message()
        test_msg.test_has_high_confidence_entities()
        test_msg.test_to_cosmos_dict()
        test_msg.test_to_display_dict()
        print("✅ ChatMessage テスト完了")
        
        # 関連クラステスト
        print("🔍 関連クラステスト...")
        test_participant = TestConversationParticipant()
        test_participant.test_create_participant()
        test_category = TestConversationCategory()
        test_category.test_create_category()
        print("✅ 関連クラステスト完了")
        
        print("🎉 全モデルテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ モデルテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_model_tests()