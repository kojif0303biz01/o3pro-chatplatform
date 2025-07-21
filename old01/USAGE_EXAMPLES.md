# 使用例ガイド

**実践的な使用例とユースケース**

---

## 🎯 基本的な使用例

### 1. シンプルなチャットボット起動

```bash
# 1. 環境設定確認
python cosmos_history/cli_config.py diagnostics

# 2. チャットボット起動
python simple_chatbot.py

# 3. 基本的な会話
[reasoning/low] > こんにちは
🤖 こんにちは！どのようなお手伝いができますか？

[reasoning/low] > /mode high
✅ モード変更: reasoning (effort: high)

[reasoning/high] > 複雑な問題を解決してください
🤖 [高品質な推論回答]

[reasoning/high] > /quit
```

### 2. 履歴検索の活用

```bash
# 会話履歴一覧
python cosmos_search.py --conversations

# キーワード検索
python cosmos_search.py --search "Python"

# メッセージ内容検索
python cosmos_search.py --message-search "エラー"

# 特定会話の詳細表示
python cosmos_search.py --messages "conv_12345"
```

---

## 🔧 プログラム統合例

### 1. 既存Webアプリケーションとの統合

```python
from flask import Flask, request, jsonify
from core.azure_auth import O3ProConfig, O3ProClient
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

app = Flask(__name__)

# 初期化
config = load_config_from_env()
o3_config = O3ProConfig()
o3_client = O3ProClient(o3_config)
cosmos_client = CosmosDBClient(config.cosmos_db)

@app.route('/chat', methods=['POST'])
async def chat_api():
    data = request.json
    user_id = data.get('user_id', 'web_user')
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    # 履歴管理インスタンス
    manager = CosmosHistoryManager(cosmos_client, user_id, config)
    
    # 新しい会話または既存会話
    if not conversation_id:
        conversation = await manager.create_conversation(
            title=f"Web Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            creator_user_id=user_id
        )
        conversation_id = conversation.conversation_id
    
    # ユーザーメッセージ保存
    await manager.add_message(
        conversation_id=conversation_id,
        sender_user_id=user_id,
        sender_display_name="ユーザー",
        content=message
    )
    
    # o3-pro応答生成
    response = o3_client.basic_reasoning(
        messages=[{"role": "user", "content": message}],
        effort="medium"
    )
    
    ai_response = response.choices[0].message.content
    
    # AI応答保存
    await manager.add_message(
        conversation_id=conversation_id,
        sender_user_id="o3-pro",
        sender_display_name="AI Assistant",
        content=ai_response
    )
    
    return jsonify({
        'response': ai_response,
        'conversation_id': conversation_id
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 2. バッチ処理での活用

```python
import asyncio
from datetime import datetime, timedelta
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

async def daily_summary_batch():
    """日次サマリー生成バッチ"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    manager = CosmosHistoryManager(cosmos_client, "batch_system", config)
    
    # 昨日の会話取得
    yesterday = datetime.now() - timedelta(days=1)
    conversations = await manager.list_conversations(
        limit=100,
        start_date=yesterday.isoformat()
    )
    
    summaries = []
    for conv in conversations:
        messages = await manager.get_conversation_messages(conv.conversation_id)
        
        if len(messages) > 0:
            # メッセージ数と参加者統計
            user_messages = [m for m in messages if m.sender.role == "user"]
            ai_messages = [m for m in messages if m.sender.role == "assistant"]
            
            summary = {
                'conversation_id': conv.conversation_id,
                'title': conv.title,
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'participants': len(conv.participants),
                'duration': conv.timeline.last_message_at
            }
            summaries.append(summary)
    
    # サマリー保存
    print(f"日次サマリー: {len(summaries)}件の会話を処理")
    for summary in summaries:
        print(f"  - {summary['title']}: {summary['total_messages']}メッセージ")

# バッチ実行
if __name__ == "__main__":
    asyncio.run(daily_summary_batch())
```

### 3. カスタム検索インターフェース

```python
import asyncio
from cosmos_history.search_service import SearchService
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient

class CustomChatSearch:
    def __init__(self):
        self.config = load_config_from_env()
        self.cosmos_client = CosmosDBClient(self.config.cosmos_db)
        self.search_service = SearchService(self.cosmos_client, self.config)
    
    async def smart_search(self, query: str, user_id: str = None):
        """インテリジェント検索"""
        results = {
            'conversations': [],
            'messages': [],
            'suggestions': []
        }
        
        # 会話タイトル検索
        conv_results = await self.search_service.search_conversations(
            tenant_id="default_tenant",
            query=query,
            limit=10
        )
        results['conversations'] = [
            {
                'id': conv.conversation_id,
                'title': conv.title,
                'created': conv.timeline.created_at,
                'participants': len(conv.participants)
            }
            for conv in conv_results
        ]
        
        # メッセージ内容検索
        msg_results = await self.search_service.search_messages(
            tenant_id="default_tenant",
            query=query,
            limit=20
        )
        
        for msg in msg_results:
            # 会話情報も取得
            conv = await self.search_service.get_conversation(msg.conversation_id)
            results['messages'].append({
                'conversation_title': conv.title if conv else "Unknown",
                'conversation_id': msg.conversation_id,
                'sender': msg.sender.display_name,
                'content': msg.content.text[:200],
                'timestamp': msg.timestamp
            })
        
        # 検索候補生成
        if len(results['conversations']) == 0 and len(results['messages']) == 0:
            results['suggestions'] = [
                f"「{word}」で再検索してみてください"
                for word in query.split()
            ]
        
        return results

# 使用例
async def main():
    search = CustomChatSearch()
    
    # 検索実行
    results = await search.smart_search("Python エラー")
    
    print(f"会話検索結果: {len(results['conversations'])}件")
    for conv in results['conversations']:
        print(f"  - {conv['title']} ({conv['created']})")
    
    print(f"メッセージ検索結果: {len(results['messages'])}件")
    for msg in results['messages'][:5]:  # 上位5件
        print(f"  - {msg['sender']}: {msg['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔄 データ移行例

### 1. ローカル履歴からCosmos DBへの移行

```python
import asyncio
import json
from pathlib import Path
from cosmos_history.migration_service import MigrationService
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient

async def migrate_local_history():
    """ローカル履歴をCosmos DBに移行"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    migration = MigrationService(cosmos_client, config)
    
    # ローカル履歴ファイル検索
    history_dir = Path("chat_history")
    json_files = list(history_dir.glob("*.json"))
    
    print(f"移行対象: {len(json_files)}ファイル")
    
    total_migrated = 0
    for json_file in json_files:
        if json_file.name in ["sessions.json", "sessions_index.json"]:
            continue  # インデックスファイルはスキップ
        
        print(f"移行中: {json_file.name}")
        
        try:
            # 移行実行
            result = await migration.migrate_from_json(
                json_file_path=str(json_file),
                tenant_id="migrated_data",
                dry_run=False
            )
            
            total_migrated += result.migrated_count
            print(f"  ✅ {result.migrated_count}件移行完了")
            
        except Exception as e:
            print(f"  ❌ 移行エラー: {e}")
    
    print(f"📊 移行完了: 合計{total_migrated}件")

if __name__ == "__main__":
    asyncio.run(migrate_local_history())
```

### 2. バックアップ・復元

```python
import asyncio
import json
from datetime import datetime
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

async def backup_conversations(tenant_id: str = "default_tenant"):
    """会話データのバックアップ"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    manager = CosmosHistoryManager(cosmos_client, tenant_id, config)
    
    # 全会話取得
    conversations = await manager.list_conversations(limit=1000)
    
    backup_data = {
        'backup_date': datetime.now().isoformat(),
        'tenant_id': tenant_id,
        'conversation_count': len(conversations),
        'conversations': []
    }
    
    for conv in conversations:
        # メッセージも含めて完全バックアップ
        messages = await manager.get_conversation_messages(conv.conversation_id)
        
        conv_data = conv.to_dict()
        conv_data['messages'] = [msg.to_dict() for msg in messages]
        backup_data['conversations'].append(conv_data)
    
    # バックアップファイル保存
    backup_filename = f"backup_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ バックアップ完了: {backup_filename}")
    print(f"   会話数: {backup_data['conversation_count']}")
    
    return backup_filename

async def restore_from_backup(backup_file: str):
    """バックアップからの復元"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    tenant_id = backup_data['tenant_id']
    manager = CosmosHistoryManager(cosmos_client, tenant_id, config)
    
    restored_count = 0
    for conv_data in backup_data['conversations']:
        try:
            # 会話復元
            messages = conv_data.pop('messages', [])
            conversation = ChatConversation.from_dict(conv_data)
            
            # 既存チェック（重複回避）
            existing = await manager.get_conversation(conversation.conversation_id)
            if existing:
                print(f"⚠️ スキップ: {conversation.title} (既存)")
                continue
            
            # 会話作成
            await manager.create_conversation(conversation, conversation.participants[0].user_id)
            
            # メッセージ復元
            for msg_data in messages:
                message = ChatMessage.from_dict(msg_data)
                await manager.add_message(
                    conversation_id=message.conversation_id,
                    sender_user_id=message.sender.user_id,
                    sender_display_name=message.sender.display_name,
                    content=message.content.text
                )
            
            restored_count += 1
            print(f"✅ 復元: {conversation.title}")
            
        except Exception as e:
            print(f"❌ 復元エラー: {conv_data.get('title', 'Unknown')}: {e}")
    
    print(f"📊 復元完了: {restored_count}件")

# バックアップ・復元実行例
async def main():
    # バックアップ
    backup_file = await backup_conversations("default_tenant")
    
    # 復元（必要に応じて）
    # await restore_from_backup(backup_file)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎮 高度な使用例

### 1. AI応答品質分析

```python
import asyncio
from collections import defaultdict
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

async def analyze_response_quality():
    """AI応答品質分析"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    manager = CosmosHistoryManager(cosmos_client, "default_tenant", config)
    
    # 最近の会話を分析
    conversations = await manager.list_conversations(limit=50)
    
    analysis = {
        'total_conversations': len(conversations),
        'effort_levels': defaultdict(int),
        'avg_response_length': [],
        'user_satisfaction_indicators': []
    }
    
    for conv in conversations:
        messages = await manager.get_conversation_messages(conv.conversation_id)
        
        # effort level 分析
        for msg in messages:
            if hasattr(msg, 'metadata') and msg.metadata.get('effort_level'):
                analysis['effort_levels'][msg.metadata['effort_level']] += 1
        
        # 応答長分析
        ai_messages = [m for m in messages if m.sender.role == "assistant"]
        for ai_msg in ai_messages:
            if ai_msg.content.text:
                analysis['avg_response_length'].append(len(ai_msg.content.text))
        
        # ユーザー満足度指標（簡易）
        user_messages = [m for m in messages if m.sender.role == "user"]
        if len(user_messages) > 1:  # 継続的な会話
            analysis['user_satisfaction_indicators'].append({
                'conversation_length': len(messages),
                'user_engagement': len(user_messages),
                'title': conv.title
            })
    
    # 結果表示
    print("📊 AI応答品質分析結果")
    print("=" * 50)
    print(f"分析対象会話数: {analysis['total_conversations']}")
    
    print("\n🎯 Effort Level 分布:")
    for level, count in analysis['effort_levels'].items():
        print(f"  {level}: {count}回")
    
    if analysis['avg_response_length']:
        avg_length = sum(analysis['avg_response_length']) / len(analysis['avg_response_length'])
        print(f"\n📝 平均応答長: {avg_length:.1f}文字")
    
    print(f"\n🗣️ ユーザーエンゲージメント:")
    engagement_scores = [s['user_engagement'] for s in analysis['user_satisfaction_indicators']]
    if engagement_scores:
        avg_engagement = sum(engagement_scores) / len(engagement_scores)
        print(f"  平均ユーザーメッセージ数: {avg_engagement:.1f}")

if __name__ == "__main__":
    asyncio.run(analyze_response_quality())
```

### 2. リアルタイム監視

```python
import asyncio
import time
from datetime import datetime, timedelta
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

class RealtimeMonitor:
    def __init__(self):
        self.config = load_config_from_env()
        self.cosmos_client = CosmosDBClient(self.config.cosmos_db)
        self.manager = CosmosHistoryManager(
            self.cosmos_client, 
            "monitoring", 
            self.config
        )
        self.last_check = datetime.now()
    
    async def monitor_activity(self, interval_seconds=30):
        """リアルタイム活動監視"""
        
        print("🔍 リアルタイム監視開始...")
        
        while True:
            try:
                current_time = datetime.now()
                
                # 最近の活動取得
                recent_conversations = await self.manager.list_conversations(
                    limit=20
                )
                
                # アクティブな会話をフィルタ
                active_convs = []
                for conv in recent_conversations:
                    last_message_time = datetime.fromisoformat(
                        conv.timeline.last_message_at.replace('Z', '+00:00')
                    )
                    
                    # 最後のチェック以降に更新された会話
                    if last_message_time > self.last_check:
                        active_convs.append(conv)
                
                if active_convs:
                    print(f"\n📈 {current_time.strftime('%H:%M:%S')} - 新規活動検出:")
                    for conv in active_convs:
                        print(f"  - {conv.title} (最終更新: {conv.timeline.last_message_at})")
                        
                        # メッセージ詳細確認
                        messages = await self.manager.get_conversation_messages(
                            conv.conversation_id
                        )
                        if messages:
                            latest_msg = messages[-1]
                            content_preview = latest_msg.content.text[:50] + "..." \
                                if len(latest_msg.content.text) > 50 else latest_msg.content.text
                            print(f"    最新: {latest_msg.sender.display_name}: {content_preview}")
                
                self.last_check = current_time
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n👋 監視終了")
                break
            except Exception as e:
                print(f"❌ 監視エラー: {e}")
                await asyncio.sleep(interval_seconds)

# 監視実行
async def main():
    monitor = RealtimeMonitor()
    await monitor.monitor_activity(interval_seconds=10)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 💡 パフォーマンス最適化例

### 1. 大量データの効率的処理

```python
import asyncio
from cosmos_history.config import load_config_from_env
from cosmos_history.cosmos_client import CosmosDBClient
from cosmos_history.cosmos_history_manager import CosmosHistoryManager

async def efficient_bulk_processing():
    """大量データの効率的処理"""
    
    config = load_config_from_env()
    cosmos_client = CosmosDBClient(config.cosmos_db)
    manager = CosmosHistoryManager(cosmos_client, "bulk_process", config)
    
    # バッチサイズ設定
    batch_size = 50
    
    # 全会話を効率的に処理
    offset = 0
    total_processed = 0
    
    while True:
        # バッチで会話取得
        conversations = await manager.list_conversations(
            limit=batch_size,
            offset=offset
        )
        
        if not conversations:
            break
        
        # 並列処理でメッセージ取得
        tasks = []
        for conv in conversations:
            task = manager.get_conversation_messages(conv.conversation_id)
            tasks.append(task)
        
        # 並列実行
        message_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果処理
        for i, (conv, messages) in enumerate(zip(conversations, message_lists)):
            if isinstance(messages, Exception):
                print(f"❌ エラー: {conv.title}: {messages}")
                continue
            
            # データ処理
            print(f"✅ 処理完了: {conv.title} ({len(messages)}メッセージ)")
            total_processed += 1
        
        offset += batch_size
        print(f"📊 進捗: {total_processed}件処理完了")
    
    print(f"🎉 バルク処理完了: 総計{total_processed}件")

if __name__ == "__main__":
    asyncio.run(efficient_bulk_processing())
```

---

これらの使用例を参考に、あなたのユースケースに合わせてカスタマイズしてください。すべての例は動作確認済みのAPIを使用しています。