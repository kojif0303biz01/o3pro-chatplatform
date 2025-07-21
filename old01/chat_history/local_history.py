"""
ローカル履歴管理モジュール

JSONファイルベースのチャット履歴管理機能
既存のJSONファイル処理パターンを活用

作成日: 2025-07-19
"""

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ChatHistoryManager:
    """チャット履歴管理クラス"""
    
    def __init__(self, history_dir: str = "chat_history"):
        """
        履歴管理初期化
        
        Args:
            history_dir: 履歴保存ディレクトリ
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        
        # セッション一覧ファイル
        self.sessions_file = self.history_dir / "sessions.json"
        self.sessions = self._load_sessions()
    
    def _load_sessions(self) -> Dict[str, Any]:
        """セッション一覧を読み込み"""
        if not self.sessions_file.exists():
            return {}
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"セッション読み込みエラー: {e}")
            return {}
    
    def _save_sessions(self):
        """セッション一覧を保存"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"セッション保存エラー: {e}")
    
    def start_new_session(self, mode: str = "reasoning", title: str = "") -> str:
        """
        新しいセッションを開始
        
        Args:
            mode: 処理モード
            title: セッションタイトル
            
        Returns:
            セッションID
        """
        session_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        if not title:
            title = f"チャット ({mode}) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session_info = {
            "id": session_id,
            "title": title,
            "mode": mode,
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0
        }
        
        self.sessions[session_id] = session_info
        self._save_sessions()
        
        # セッションファイル作成
        session_file = self.history_dir / f"{session_id}.json"
        session_data = {
            "session_info": session_info,
            "messages": []
        }
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"セッションファイル作成エラー: {e}")
            return None
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        メッセージを追加
        
        Args:
            session_id: セッションID
            role: メッセージロール (user/assistant)
            content: メッセージ内容
            metadata: メタデータ（モード、実行時間など）
            
        Returns:
            成功/失敗
        """
        if session_id not in self.sessions:
            print(f"セッション {session_id} が見つかりません")
            return False
        
        session_file = self.history_dir / f"{session_id}.json"
        if not session_file.exists():
            print(f"セッションファイル {session_file} が見つかりません")
            return False
        
        try:
            # セッションデータ読み込み
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # メッセージ追加
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            session_data["messages"].append(message)
            
            # セッション情報更新
            session_data["session_info"]["message_count"] = len(session_data["messages"])
            session_data["session_info"]["updated_at"] = datetime.now().isoformat()
            
            # ファイル保存
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # セッション一覧更新
            self.sessions[session_id] = session_data["session_info"]
            self._save_sessions()
            
            return True
            
        except Exception as e:
            print(f"メッセージ追加エラー: {e}")
            return False
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """セッションのメッセージ一覧を取得"""
        session_file = self.history_dir / f"{session_id}.json"
        if not session_file.exists():
            return []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return session_data.get("messages", [])
        except Exception:
            return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """セッション情報を取得"""
        return self.sessions.get(session_id)
    
    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """セッション一覧を取得（最新順）"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_sessions = len(self.sessions)
        total_messages = sum(s.get("message_count", 0) for s in self.sessions.values())
        
        mode_stats = {}
        for session in self.sessions.values():
            mode = session.get("mode", "unknown")
            mode_stats[mode] = mode_stats.get(mode, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "mode_statistics": mode_stats
        }


def test_history_manager():
    """履歴管理のテスト"""
    print("=== 履歴管理テスト開始 ===")
    
    # テスト用ディレクトリ
    test_dir = "test_history"
    manager = ChatHistoryManager(test_dir)
    
    # 新セッション作成
    session_id = manager.start_new_session("reasoning", "テストセッション")
    print(f"✓ セッション作成: {session_id}")
    
    # メッセージ追加
    success1 = manager.add_message(session_id, "user", "こんにちは")
    success2 = manager.add_message(
        session_id, 
        "assistant", 
        "こんにちは！何かお手伝いできることはありますか？",
        {"mode": "reasoning", "effort": "low", "duration": 1.2}
    )
    
    if success1 and success2:
        print("✓ メッセージ追加成功")
    else:
        print("✗ メッセージ追加失敗")
        return False
    
    # メッセージ取得
    messages = manager.get_session_messages(session_id)
    print(f"✓ メッセージ取得: {len(messages)}件")
    
    # セッション一覧
    sessions = manager.list_sessions()
    print(f"✓ セッション一覧: {len(sessions)}件")
    
    # 統計
    stats = manager.get_statistics()
    print(f"✓ 統計: {stats}")
    
    print("=== 履歴管理テスト完了 ===")
    return True


if __name__ == "__main__":
    test_history_manager()