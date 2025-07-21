#!/usr/bin/env python3
"""
Cosmos DB チャット履歴検索ツール

使用方法:
    python cosmos_search.py                    # 全履歴表示
    python cosmos_search.py --search "キーワード"  # キーワード検索
    python cosmos_search.py --conversations    # 会話一覧のみ
    python cosmos_search.py --messages conv_id # 特定会話のメッセージ
"""

import asyncio
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager


class CosmosHistorySearcher:
    """Cosmos DB 履歴検索クラス"""
    
    def __init__(self):
        self.config = None
        self.manager = None
    
    async def initialize(self):
        """初期化"""
        try:
            # .env.cosmos ファイル読み込み
            if Path(".env.cosmos").exists():
                load_dotenv(".env.cosmos")
                print("✅ .env.cosmos設定読み込み完了")
            
            # Cosmos DB設定
            self.config = load_config_from_env()
            cosmos_client = CosmosDBClient(self.config.cosmos_db)
            self.manager = CosmosHistoryManager(cosmos_client, "default_tenant", self.config)
            
            print("✅ Cosmos DB接続完了")
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False
    
    async def list_conversations(self, limit=20):
        """会話一覧表示"""
        try:
            conversations = await self.manager.list_conversations(limit=limit)
            
            if not conversations:
                print("📭 会話履歴がありません")
                return
            
            print(f"🗂️  会話一覧 (最新{len(conversations)}件)")
            print("=" * 80)
            
            for i, conv in enumerate(conversations, 1):
                created_time = self._format_datetime(conv.timeline.created_at)
                print(f"{i:2d}. {conv.title}")
                print(f"    ID: {conv.conversation_id}")
                print(f"    作成: {created_time}")
                print(f"    参加者: {len(conv.participants)}名")
                print()
                
        except Exception as e:
            print(f"❌ 会話一覧取得エラー: {e}")
    
    async def search_conversations(self, keyword):
        """会話検索"""
        try:
            # タイトル検索
            results = await self.manager.search_conversations(
                tenant_id="default_tenant",
                query=keyword,
                limit=20
            )
            
            if not results:
                print(f"🔍 「{keyword}」に関する会話が見つかりませんでした")
                return
            
            print(f"🔍 検索結果: 「{keyword}」({len(results)}件)")
            print("=" * 80)
            
            for i, conv in enumerate(results, 1):
                created_time = self._format_datetime(conv.timeline.created_at)
                print(f"{i:2d}. {conv.title}")
                print(f"    ID: {conv.conversation_id}")
                print(f"    作成: {created_time}")
                
                # 検索可能テキストの一部を表示
                if hasattr(conv, 'searchable_text') and conv.searchable_text:
                    preview = conv.searchable_text[:100] + "..." if len(conv.searchable_text) > 100 else conv.searchable_text
                    print(f"    内容: {preview}")
                print()
                
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
    
    async def show_conversation_messages(self, conversation_id):
        """特定会話のメッセージ表示"""
        try:
            # 会話情報取得
            conversation = await self.manager.get_conversation(conversation_id)
            if not conversation:
                print(f"❌ 会話ID「{conversation_id}」が見つかりません")
                return
            
            # メッセージ取得
            messages = await self.manager.get_conversation_messages(conversation_id)
            
            print(f"💬 会話: {conversation.title}")
            print(f"📅 作成: {self._format_datetime(conversation.timeline.created_at)}")
            print("=" * 80)
            
            if not messages:
                print("📭 メッセージがありません")
                return
            
            for i, msg in enumerate(messages, 1):
                sender_name = msg.sender.display_name or msg.sender.user_id
                timestamp = self._format_datetime(msg.timestamp)
                content = msg.content.text or msg.content.display_text or "[内容なし]"
                
                print(f"[{i:2d}] {sender_name} ({timestamp})")
                print(f"     {content}")
                print()
                
        except Exception as e:
            print(f"❌ メッセージ取得エラー: {e}")
    
    async def search_messages(self, keyword, limit=20):
        """メッセージ内容検索"""
        try:
            # 全会話を取得して内容検索（簡易実装）
            conversations = await self.manager.list_conversations(limit=100)
            found_messages = []
            
            print(f"🔍 メッセージ検索中: 「{keyword}」...")
            
            for conv in conversations:
                messages = await self.manager.get_conversation_messages(conv.conversation_id)
                for msg in messages:
                    content = msg.content.text or msg.content.display_text or ""
                    if keyword.lower() in content.lower():
                        found_messages.append({
                            'conversation': conv,
                            'message': msg,
                            'content': content
                        })
            
            if not found_messages:
                print(f"🔍 「{keyword}」を含むメッセージが見つかりませんでした")
                return
            
            print(f"🔍 メッセージ検索結果: 「{keyword}」({len(found_messages)}件)")
            print("=" * 80)
            
            for i, item in enumerate(found_messages[:limit], 1):
                conv = item['conversation']
                msg = item['message']
                content = item['content']
                
                timestamp = self._format_datetime(msg.timestamp)
                sender = msg.sender.display_name or msg.sender.user_id
                
                print(f"{i:2d}. 会話: {conv.title}")
                print(f"    送信者: {sender} ({timestamp})")
                print(f"    内容: {content[:200]}{'...' if len(content) > 200 else ''}")
                print(f"    会話ID: {conv.conversation_id}")
                print()
                
        except Exception as e:
            print(f"❌ メッセージ検索エラー: {e}")
    
    def _format_datetime(self, iso_string):
        """日時フォーマット"""
        try:
            if 'T' in iso_string:
                dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return iso_string
        except:
            return iso_string


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Cosmos DB チャット履歴検索ツール')
    parser.add_argument('--search', '-s', help='キーワード検索')
    parser.add_argument('--conversations', '-c', action='store_true', help='会話一覧のみ表示')
    parser.add_argument('--messages', '-m', help='特定会話のメッセージ表示（会話ID指定）')
    parser.add_argument('--message-search', '-ms', help='メッセージ内容検索')
    parser.add_argument('--limit', '-l', type=int, default=20, help='表示件数制限')
    
    args = parser.parse_args()
    
    print("🔍 Cosmos DB チャット履歴検索ツール")
    print("=" * 50)
    
    # 初期化
    searcher = CosmosHistorySearcher()
    if not await searcher.initialize():
        return
    
    # 処理分岐
    if args.conversations:
        await searcher.list_conversations(args.limit)
    elif args.search:
        await searcher.search_conversations(args.search)
    elif args.messages:
        await searcher.show_conversation_messages(args.messages)
    elif args.message_search:
        await searcher.search_messages(args.message_search, args.limit)
    else:
        # デフォルト: 会話一覧表示
        await searcher.list_conversations(args.limit)


if __name__ == "__main__":
    asyncio.run(main())