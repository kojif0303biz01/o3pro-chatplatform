#!/usr/bin/env python3
"""
o3-pro シンプルチャットボット

モード切り替え対応の基本的なチャットボット
- 基本推論（low/medium/high effort）  
- ストリーミング応答
- チャット履歴保存

使用方法:
    python simple_chatbot.py

作成日: 2025-07-19
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler, StreamingHandler, BackgroundHandler
from chat_history.local_history import ChatHistoryManager

# Cosmos DB統合
try:
    from cosmos_history.config import load_config_from_env
    from cosmos_history.cosmos_client import CosmosDBClient
    from cosmos_history.cosmos_history_manager import CosmosHistoryManager
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False


class HistoryManagerWrapper:
    """Cosmos DB と ローカル履歴管理の統一インターフェース"""
    
    def __init__(self, manager, is_cosmos=False):
        self.manager = manager
        self.is_cosmos = is_cosmos
        self.session_mapping = {}  # Cosmos DB用のセッションID変換
    
    def start_new_session(self, mode: str, title: str):
        """新セッション開始"""
        if self.is_cosmos:
            import asyncio
            import uuid
            
            # 会話を作成
            conversation_title = f"{title} ({mode})"
            
            # 非同期関数を同期実行
            async def create_conv():
                return await self.manager.create_conversation(
                    title=conversation_title,
                    creator_user_id="chatbot_user"
                )
            
            try:
                conversation = asyncio.run(create_conv())
                session_id = str(uuid.uuid4())
                self.session_mapping[session_id] = conversation.conversation_id
                return session_id
            except Exception as e:
                print(f"⚠️ Cosmos DB会話作成エラー: {e}")
                return None
        else:
            return self.manager.start_new_session(mode, title)
    
    def add_message(self, session_id: str, role: str, content: str, metadata=None):
        """メッセージ追加"""
        if self.is_cosmos:
            import asyncio
            
            # セッションIDから会話IDを取得
            conversation_id = self.session_mapping.get(session_id)
            if not conversation_id:
                print(f"⚠️ セッションID {session_id} が見つかりません")
                return
            
            # 非同期関数を同期実行
            async def add_msg():
                if role == "user":
                    return await self.manager.add_message(
                        conversation_id=conversation_id,
                        sender_user_id="chatbot_user",
                        sender_display_name="ユーザー",
                        content=content
                    )
                else:  # assistant
                    return await self.manager.add_message(
                        conversation_id=conversation_id,
                        sender_user_id="assistant",
                        sender_display_name="o3-pro",
                        content=content
                    )
            
            try:
                asyncio.run(add_msg())
            except Exception as e:
                print(f"⚠️ Cosmos DBメッセージ追加エラー: {e}")
        else:
            self.manager.add_message(session_id, role, content, metadata)
    
    def get_session_info(self, session_id: str):
        """セッション情報取得"""
        if self.is_cosmos:
            import asyncio
            
            conversation_id = self.session_mapping.get(session_id)
            if not conversation_id:
                return None
            
            async def get_conv():
                return await self.manager.get_conversation(conversation_id)
            
            try:
                conversation = asyncio.run(get_conv())
                if conversation:
                    return {
                        'title': conversation.title,
                        'message_count': len(conversation.participants)  # 簡易表示
                    }
            except Exception as e:
                print(f"⚠️ Cosmos DB会話情報取得エラー: {e}")
            return None
        else:
            return self.manager.get_session_info(session_id)
    
    def get_session_messages(self, session_id: str):
        """セッションメッセージ取得"""
        if self.is_cosmos:
            import asyncio
            
            conversation_id = self.session_mapping.get(session_id)
            if not conversation_id:
                return []
            
            async def get_msgs():
                return await self.manager.get_conversation_messages(conversation_id)
            
            try:
                messages = asyncio.run(get_msgs())
                # ローカル形式に変換
                converted = []
                for msg in messages:
                    converted.append({
                        'role': 'user' if msg.sender.user_id == 'chatbot_user' else 'assistant',
                        'content': msg.content.text or msg.content.display_text,
                        'timestamp': msg.timestamp
                    })
                return converted
            except Exception as e:
                print(f"⚠️ Cosmos DBメッセージ取得エラー: {e}")
            return []
        else:
            return self.manager.get_session_messages(session_id)


class SimpleO3ProChatBot:
    """シンプルo3-proチャットボット"""
    
    def __init__(self):
        self.config = None
        self.client = None
        self.reasoning_handler = None
        self.streaming_handler = None
        self.background_handler = None
        self.history_manager = None
        self.current_session_id = None
        self.current_mode = "reasoning"
        self.current_effort = "low"
    
    def initialize(self) -> bool:
        """システム初期化"""
        try:
            print("🚀 o3-proチャットボット初期化中...")
            
            # 設定・認証
            self.config = O3ProConfig()
            if not self.config.validate():
                print("❌ 設定エラー: .envファイルを確認してください")
                return False
            
            self.client = O3ProClient(self.config)
            if not self.client.is_ready():
                print("❌ Azure OpenAI接続失敗")
                return False
            
            print("✅ Azure OpenAI接続成功")
            
            # ハンドラー初期化
            self.reasoning_handler = ReasoningHandler(self.client)
            self.streaming_handler = StreamingHandler(self.client)
            self.background_handler = BackgroundHandler(self.client)
            print("✅ 処理ハンドラー初期化完了")
            
            # 履歴管理初期化
            self.history_manager = self._initialize_history_manager()
            if self.history_manager:
                self.current_session_id = self.history_manager.start_new_session(
                    self.current_mode, 
                    f"チャットセッション"
                )
            else:
                print("⚠️ 履歴管理が無効です")
            print("✅ 履歴管理初期化完了")
            
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False
    
    def process_message(self, user_input: str) -> dict:
        """メッセージ処理"""
        try:
            # ユーザーメッセージを履歴に保存
            self.history_manager.add_message(
                self.current_session_id, 
                "user", 
                user_input
            )
            
            # モード別処理
            if self.current_mode == "reasoning":
                result = self.reasoning_handler.basic_reasoning(
                    user_input, 
                    effort=self.current_effort
                )
            elif self.current_mode == "streaming":
                print("🤖 ", end='', flush=True)  # ストリーミング開始時のアイコン
                
                def stream_callback(chunk_text):
                    print(chunk_text, end='', flush=True)
                
                result = self.streaming_handler.stream_with_callback(
                    user_input,
                    stream_callback,
                    effort=self.current_effort
                )
                print()  # ストリーミング終了後の改行
            elif self.current_mode == "background":
                print("🔄 バックグラウンド処理を開始...")
                result = self.background_handler.start_background_task(
                    user_input,
                    effort=self.current_effort
                )
                if result["success"]:
                    print(f"✅ ジョブ開始成功 (ID: {result['job_id']})")
                    print("📋 ジョブステータス確認: /job status <job_id>")
                    print("📋 結果取得: /job result <job_id>")
            else:
                result = {
                    "success": False,
                    "error": f"未対応モード: {self.current_mode}"
                }
            
            # アシスタント応答を履歴に保存（backgroundモード以外）
            if result["success"] and self.current_mode != "background":
                metadata = {
                    "mode": self.current_mode,
                    "effort": self.current_effort,
                    "duration": result.get("duration", 0)
                }
                
                self.history_manager.add_message(
                    self.current_session_id,
                    "assistant", 
                    result["response"],
                    metadata
                )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"処理エラー: {e}"
            }
    
    def set_mode(self, mode: str, effort: str = "low") -> bool:
        """モード変更"""
        valid_modes = ["reasoning", "streaming", "background"]
        valid_efforts = ["low", "medium", "high"]
        
        if mode not in valid_modes:
            print(f"❌ 無効なモード: {mode}. 有効: {valid_modes}")
            return False
        
        if effort not in valid_efforts:
            print(f"❌ 無効なeffort: {effort}. 有効: {valid_efforts}")
            return False
        
        self.current_mode = mode
        self.current_effort = effort
        
        print(f"✅ モード変更: {mode} (effort: {effort})")
        return True
    
    def _initialize_history_manager(self):
        """履歴管理初期化（Cosmos DB優先、フォールバック対応）"""
        # Cosmos DB環境変数チェック
        import os
        cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        
        if COSMOS_AVAILABLE and cosmos_endpoint:
            try:
                print("🔍 Cosmos DB履歴管理を初期化中...")
                from dotenv import load_dotenv
                
                # .env.cosmosファイルを読み込み
                if Path(".env.cosmos").exists():
                    load_dotenv(".env.cosmos")
                    print("✅ .env.cosmos設定読み込み完了")
                
                # Cosmos DB設定
                cosmos_config = load_config_from_env()
                cosmos_client = CosmosDBClient(cosmos_config.cosmos_db)
                
                # 非同期チェックは省略し、直接作成
                cosmos_manager = CosmosHistoryManager(cosmos_client, "default_tenant", cosmos_config)
                wrapper = HistoryManagerWrapper(cosmos_manager, is_cosmos=True)
                print("✅ Cosmos DB履歴管理初期化完了")
                return wrapper
                
            except Exception as e:
                print(f"⚠️ Cosmos DB初期化失敗: {e}")
                print("📂 ローカル履歴管理にフォールバック")
        
        # ローカル履歴管理にフォールバック
        try:
            local_manager = ChatHistoryManager()
            wrapper = HistoryManagerWrapper(local_manager, is_cosmos=False)
            print("✅ ローカル履歴管理初期化完了")
            return wrapper
        except Exception as e:
            print(f"❌ ローカル履歴管理初期化失敗: {e}")
            return None
    
    def show_help(self):
        """ヘルプ表示"""
        help_text = """
=== o3-proチャットボット コマンド ===

基本:
  /help           - ヘルプ表示
  /quit, /exit    - 終了
  /status         - 現在の設定表示
  
モード切り替え:
  /mode reasoning [effort]  - 基本推論モード (effort: low/medium/high)
  /mode streaming [effort]  - ストリーミングモード
  /mode background [effort] - バックグラウンド処理モード
  
セッション:
  /new [タイトル]  - 新セッション開始
  /history        - 履歴表示
  
バックグラウンドジョブ:
  /job list       - アクティブジョブ一覧
  /job status <id> - ジョブステータス確認
  /job result <id> - ジョブ結果取得
  /job cancel <id> - ジョブキャンセル

使用例:
  /mode reasoning high     - 高精度推論モード
  /new 数学の質問          - 新セッション開始
  こんにちは               - 通常の質問
        """
        print(help_text)
    
    def show_status(self):
        """ステータス表示"""
        print(f"\n=== 現在のステータス ===")
        print(f"モード: {self.current_mode}")
        print(f"Effort: {self.current_effort}")
        print(f"セッションID: {self.current_session_id}")
        
        if self.current_session_id:
            session_info = self.history_manager.get_session_info(self.current_session_id)
            if session_info:
                print(f"メッセージ数: {session_info['message_count']}")
        print()
    
    def show_history(self):
        """履歴表示"""
        if not self.current_session_id:
            print("セッションがありません")
            return
        
        messages = self.history_manager.get_session_messages(self.current_session_id)
        if not messages:
            print("メッセージがありません")
            return
        
        print(f"\n=== セッション履歴 (最新5件) ===")
        for msg in messages[-5:]:  # 最新5件のみ表示
            role = "👤" if msg["role"] == "user" else "🤖"
            content = msg["content"]
            # 確実に文字制限を適用
            content = content.replace('\n', ' ')  # 改行を除去
            if len(content) > 60:
                content = content[:60] + "..."
            
            timestamp = msg["timestamp"][:19]
            print(f"{role} [{timestamp}] {content}")
        print()
    
    def start_new_session(self, title: str = ""):
        """新セッション開始"""
        if not title:
            title = f"チャットセッション ({self.current_mode})"
        
        self.current_session_id = self.history_manager.start_new_session(
            self.current_mode, 
            title
        )
        print(f"✅ 新セッション開始: {title}")
    
    def show_jobs(self):
        """アクティブジョブ一覧表示"""
        if not self.background_handler:
            print("❌ バックグラウンドハンドラーが初期化されていません")
            return
        
        jobs = self.background_handler.list_active_jobs()
        if not jobs:
            print("📋 アクティブなジョブはありません")
            return
        
        print(f"\n=== アクティブジョブ一覧 ({len(jobs)}件) ===")
        for job in jobs:
            print(f"🔄 {job['job_id'][:8]}... | {job['status']} | {job['effort']} | {job['elapsed_time']:.1f}s")
            print(f"   質問: {job['question'][:60]}...")
        print()
    
    def show_job_status(self, job_id: str):
        """ジョブステータス表示"""
        if not self.background_handler:
            print("❌ バックグラウンドハンドラーが初期化されていません")
            return
        
        print(f"🔍 ジョブステータス確認中: {job_id}")
        status = self.background_handler.check_status(job_id)
        
        if status["success"]:
            print(f"📊 ステータス: {status['status']}")
            print(f"⏱️  経過時間: {status['elapsed_time']:.1f}秒")
            print(f"🎯 Effort: {status['effort']}")
            print(f"❓ 質問: {status['question']}")
        else:
            print(f"❌ エラー: {status['error']}")
    
    def get_job_result(self, job_id: str):
        """ジョブ結果取得"""
        if not self.background_handler:
            print("❌ バックグラウンドハンドラーが初期化されていません")
            return
        
        print(f"📥 ジョブ結果取得中: {job_id}")
        result = self.background_handler.get_result(job_id)
        
        if result["success"]:
            print(f"🤖 {result['response']}")
            print(f"\n⏱️  総実行時間: {result['total_time']:.1f}秒")
            
            # 履歴に保存
            if self.current_session_id:
                metadata = {
                    "mode": "background",
                    "effort": result["effort"],
                    "duration": result["total_time"],
                    "job_id": job_id
                }
                
                self.history_manager.add_message(
                    self.current_session_id,
                    "user", 
                    result["question"]
                )
                self.history_manager.add_message(
                    self.current_session_id,
                    "assistant", 
                    result["response"],
                    metadata
                )
        else:
            print(f"❌ エラー: {result['error']}")
    
    def cancel_job(self, job_id: str):
        """ジョブキャンセル"""
        if not self.background_handler:
            print("❌ バックグラウンドハンドラーが初期化されていません")
            return
        
        print(f"🚫 ジョブキャンセル中: {job_id}")
        result = self.background_handler.cancel_job(job_id)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ エラー: {result['error']}")


def main():
    """メイン関数"""
    chatbot = SimpleO3ProChatBot()
    
    if not chatbot.initialize():
        print("初期化に失敗しました")
        return
    
    print("\n💡 /help でコマンド一覧を表示")
    print("💬 チャットを開始してください。終了するには /quit\n")
    
    while True:
        try:
            # プロンプト表示
            mode_indicator = f"[{chatbot.current_mode}/{chatbot.current_effort}]"
            
            try:
                user_input = input(f"{mode_indicator} > ").strip()
            except EOFError:
                print("\n👋 終了します")
                break
            
            if not user_input:
                continue
            
            # コマンド処理
            if user_input.startswith('/'):
                parts = user_input[1:].split()
                command = parts[0].lower()
                
                if command in ['quit', 'exit']:
                    print("👋 終了します")
                    break
                elif command == 'help':
                    chatbot.show_help()
                elif command == 'status':
                    chatbot.show_status()
                elif command == 'history':
                    chatbot.show_history()
                elif command == 'new':
                    title = ' '.join(parts[1:]) if len(parts) > 1 else ""
                    chatbot.start_new_session(title)
                elif command == 'mode':
                    if len(parts) >= 2:
                        mode = parts[1]
                        effort = parts[2] if len(parts) >= 3 else "low"
                        chatbot.set_mode(mode, effort)
                    else:
                        print("使用方法: /mode <reasoning|streaming|background> [effort]")
                elif command == 'job':
                    if len(parts) >= 2:
                        sub_command = parts[1]
                        if sub_command == 'list':
                            chatbot.show_jobs()
                        elif sub_command == 'status' and len(parts) >= 3:
                            job_id = parts[2]
                            chatbot.show_job_status(job_id)
                        elif sub_command == 'result' and len(parts) >= 3:
                            job_id = parts[2]
                            chatbot.get_job_result(job_id)
                        elif sub_command == 'cancel' and len(parts) >= 3:
                            job_id = parts[2]
                            chatbot.cancel_job(job_id)
                        else:
                            print("使用方法: /job <list|status|result|cancel> [job_id]")
                    else:
                        print("使用方法: /job <list|status|result|cancel> [job_id]")
                else:
                    print(f"未知のコマンド: {command}. /help で確認してください")
                
                continue
            
            # 通常メッセージ処理
            print()  # 改行
            
            result = chatbot.process_message(user_input)
            
            if result["success"]:
                # ストリーミングとバックグラウンド以外は結果表示
                if chatbot.current_mode not in ["streaming", "background"]:
                    print(f"🤖 {result['response']}")
                
                # backgroundモード以外は実行時間表示
                if chatbot.current_mode != "background":
                    duration = result.get("duration", 0)
                    print(f"\n⏱️  実行時間: {duration:.1f}秒")
            else:
                print(f"❌ エラー: {result['error']}")
            
            print()  # 間隔
            
        except KeyboardInterrupt:
            print("\n\n👋 終了します")
            break
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            continue


if __name__ == "__main__":
    main()