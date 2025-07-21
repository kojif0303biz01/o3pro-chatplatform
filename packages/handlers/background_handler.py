"""
バックグラウンド処理ハンドラー

長時間タスク、ポーリング、ステータス管理機能
Azure API仕様に基づいたbackground=True対応

使用方法:
    from handlers.background_handler import BackgroundHandler
    from core.azure_auth import O3ProClient, O3ProConfig
    
    config = O3ProConfig()
    client = O3ProClient(config)
    handler = BackgroundHandler(client)
    
    # バックグラウンド処理開始
    job_id = handler.start_background_task("複雑な分析タスク", effort="high")
    
    # ステータス確認
    status = handler.check_status(job_id)
    
    # 結果取得
    result = handler.get_result(job_id)

作成日: 2025-07-19（Azure API仕様に基づく実装）
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from core.azure_auth import O3ProClient


class BackgroundHandler:
    """バックグラウンド処理ハンドラークラス"""
    
    def __init__(self, client: O3ProClient):
        """
        ハンドラー初期化
        
        Args:
            client: 認証済みのO3ProClientインスタンス
        """
        self.client = client
        self.deployment = client.config.deployment
        self.active_jobs = {}  # ジョブID -> ジョブ情報のマッピング
    
    def start_background_task(
        self, 
        question: str, 
        effort: str = "high",
        max_completion_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        バックグラウンドタスクを開始
        
        Args:
            question: 質問・タスク内容
            effort: 推論努力レベル ("low", "medium", "high")
            max_completion_tokens: 最大完了トークン数
            
        Returns:
            ジョブ開始結果辞書
        """
        if not self.client.is_ready():
            return {
                "success": False,
                "error": "クライアントが初期化されていません"
            }
        
        try:
            # バックグラウンド処理リクエスト作成
            request_params = {
                "model": self.deployment,
                "input": question,
                "reasoning": {"effort": effort},
                "background": True  # バックグラウンド処理指定
            }
            
            if max_completion_tokens:
                request_params["max_completion_tokens"] = max_completion_tokens
            
            start_time = time.time()
            response = self.client.client.responses.create(**request_params)
            
            # ジョブ情報を保存
            job_info = {
                "id": response.id,
                "question": question,
                "effort": effort,
                "status": "running",
                "started_at": start_time,
                "response_object": response
            }
            
            self.active_jobs[response.id] = job_info
            
            return {
                "success": True,
                "job_id": response.id,
                "status": "running",
                "question": question,
                "effort": effort,
                "started_at": start_time
            }
            
        except Exception as e:
            error_msg = f"バックグラウンドタスク開始失敗: {e}"
            return {
                "success": False,
                "error": error_msg,
                "question": question,
                "effort": effort
            }
    
    def check_status(self, job_id: str) -> Dict[str, Any]:
        """
        ジョブステータスを確認
        
        Args:
            job_id: ジョブID
            
        Returns:
            ステータス辞書
        """
        if job_id not in self.active_jobs:
            return {
                "success": False,
                "error": f"ジョブID {job_id} が見つかりません"
            }
        
        try:
            # ステータス取得（Azure API仕様に基づく）
            status_response = self.client.client.responses.retrieve(job_id)
            
            job_info = self.active_jobs[job_id]
            current_time = time.time()
            elapsed_time = current_time - job_info["started_at"]
            
            # ステータス更新
            job_info["status"] = status_response.status
            job_info["last_checked"] = current_time
            
            status_result = {
                "success": True,
                "job_id": job_id,
                "status": status_response.status,
                "elapsed_time": elapsed_time,
                "question": job_info["question"],
                "effort": job_info["effort"]
            }
            
            # 進捗情報があれば追加
            if hasattr(status_response, 'progress'):
                status_result["progress"] = status_response.progress
            
            # エラー情報があれば追加
            if hasattr(status_response, 'error') and status_response.error:
                status_result["error"] = status_response.error
            
            return status_result
            
        except Exception as e:
            error_msg = f"ステータス確認失敗: {e}"
            return {
                "success": False,
                "error": error_msg,
                "job_id": job_id
            }
    
    def get_result(self, job_id: str) -> Dict[str, Any]:
        """
        ジョブ結果を取得
        
        Args:
            job_id: ジョブID
            
        Returns:
            結果辞書
        """
        # まずステータス確認
        status = self.check_status(job_id)
        
        if not status["success"]:
            return status
        
        if status["status"] != "completed":
            return {
                "success": False,
                "error": f"ジョブがまだ完了していません（現在のステータス: {status['status']}）",
                "status": status["status"],
                "job_id": job_id
            }
        
        try:
            # 結果取得
            result_response = self.client.client.responses.retrieve(job_id)
            
            job_info = self.active_jobs[job_id]
            total_time = time.time() - job_info["started_at"]
            
            result = {
                "success": True,
                "job_id": job_id,
                "response": result_response.output_text,
                "total_time": total_time,
                "question": job_info["question"],
                "effort": job_info["effort"],
                "status": "completed"
            }
            
            # 推論情報があれば追加
            if hasattr(result_response, 'reasoning'):
                result["reasoning"] = result_response.reasoning
            
            return result
            
        except Exception as e:
            error_msg = f"結果取得失敗: {e}"
            return {
                "success": False,
                "error": error_msg,
                "job_id": job_id
            }
    
    async def wait_for_completion(
        self, 
        job_id: str, 
        polling_interval: float = 10.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        ジョブ完了まで待機（非同期）
        
        Args:
            job_id: ジョブID
            polling_interval: ポーリング間隔（秒）
            timeout: タイムアウト時間（秒）
            
        Returns:
            最終結果辞書
        """
        start_time = time.time()
        
        print(f"ジョブ {job_id} の完了を待機中（タイムアウト: {timeout}秒）...")
        
        while True:
            # タイムアウトチェック
            if time.time() - start_time > timeout:
                return {
                    "success": False,
                    "error": f"タイムアウト（{timeout}秒）",
                    "job_id": job_id
                }
            
            # ステータス確認
            status = self.check_status(job_id)
            
            if not status["success"]:
                return status
            
            if status["status"] == "completed":
                return self.get_result(job_id)
            elif status["status"] == "failed":
                return {
                    "success": False,
                    "error": "ジョブが失敗しました",
                    "status": status["status"],
                    "job_id": job_id
                }
            
            # 待機
            await asyncio.sleep(polling_interval)
    
    def list_active_jobs(self) -> List[Dict[str, Any]]:
        """アクティブなジョブ一覧を取得"""
        jobs = []
        for job_id, job_info in self.active_jobs.items():
            status = self.check_status(job_id)
            jobs.append({
                "job_id": job_id,
                "question": job_info["question"],
                "effort": job_info["effort"],
                "status": status.get("status", "unknown"),
                "elapsed_time": status.get("elapsed_time", 0)
            })
        return jobs
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """ジョブをキャンセル（APIがサポートしている場合）"""
        try:
            # 注意: この機能はAzure APIでサポートされていない可能性があります
            # 実際の実装では、APIの仕様を確認してください
            
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            return {
                "success": True,
                "job_id": job_id,
                "message": "ジョブをローカル管理から削除しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"ジョブキャンセル失敗: {e}",
                "job_id": job_id
            }
    
    def quick_test(self) -> bool:
        """クイックテスト実行"""
        print("\n=== バックグラウンドハンドラークイックテスト ===")
        
        # 短いタスクでテスト
        result = self.start_background_task("2+2は何ですか？", effort="low")
        
        if not result["success"]:
            print(f"NG バックグラウンドタスク開始失敗: {result.get('error')}")
            return False
        
        job_id = result["job_id"]
        
        # ステータス確認
        max_attempts = 30  # 最大30回（5分）
        for attempt in range(max_attempts):
            time.sleep(10)  # 10秒待機
            
            status = self.check_status(job_id)
            if not status["success"]:
                print(f"NG ステータス確認失敗: {status.get('error')}")
                return False
            
            if status["status"] == "completed":
                # 結果取得
                final_result = self.get_result(job_id)
                if final_result["success"]:
                    print("OK バックグラウンドハンドラーテスト成功")
                    return True
                else:
                    print(f"NG 結果取得失敗: {final_result.get('error')}")
                    return False
            elif status["status"] == "failed":
                print(f"NG ジョブが失敗: {status.get('error', '原因不明')}")
                return False
            
            print(f"待機中... ({attempt + 1}/{max_attempts})")
        
        print("NG タイムアウト")
        return False


# 使用例とテスト関数
def test_background_handler():
    """バックグラウンドハンドラーのテスト"""
    from pathlib import Path
    from core.azure_auth import O3ProConfig, O3ProClient
    
    print("バックグラウンドハンドラーテスト開始...")
    
    # 設定とクライアント初期化
    env_path = Path(__file__).parent.parent / ".env"
    config = O3ProConfig(str(env_path))
    
    if not config.validate():
        print("ERROR 設定が不正です")
        return False
    
    client = O3ProClient(config)
    
    if not client.is_ready():
        print("ERROR クライアント初期化失敗")
        return False
    
    # バックグラウンドハンドラーテスト
    handler = BackgroundHandler(client)
    
    return handler.quick_test()


if __name__ == "__main__":
    test_background_handler()