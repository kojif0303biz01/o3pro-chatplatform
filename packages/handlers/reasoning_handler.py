"""
基本推論処理ハンドラー

既存のO3ProTesterクラスから抽出した動作確認済みの基本推論機能
low/medium/high推論レベル対応

使用方法:
    from handlers.reasoning_handler import ReasoningHandler
    from core.azure_auth import O3ProClient, O3ProConfig
    
    config = O3ProConfig()
    client = O3ProClient(config) 
    handler = ReasoningHandler(client)
    
    result = handler.basic_reasoning("質問", effort="medium")
    results = handler.test_all_levels("複雑な質問")

作成日: 2025-07-19（o3_pro_complete_toolkit.pyから抽出）
"""

import time
from typing import Dict, Any, Optional
from core.azure_auth import O3ProClient


class ReasoningHandler:
    """基本推論処理ハンドラークラス（動作確認済み）"""
    
    def __init__(self, client: O3ProClient):
        """
        ハンドラー初期化
        
        Args:
            client: 認証済みのO3ProClientインスタンス
        """
        self.client = client
        self.deployment = client.config.deployment
    
    def basic_reasoning(self, question: str, effort: str = "low") -> Dict[str, Any]:
        """
        基本推論実行（デバッグ済み）
        
        Args:
            question: 質問内容
            effort: 推論努力レベル ("low", "medium", "high")
            
        Returns:
            推論結果辞書
        """
        if not self.client.is_ready():
            return {
                "success": False,
                "error": "クライアントが初期化されていません"
            }
        
        try:
            start_time = time.time()
            
            response = self.client.client.responses.create(
                model=self.deployment,
                input=question,
                reasoning={"effort": effort}
            )
            
            duration = time.time() - start_time
            result_text = response.output_text
            
            return {
                "success": True,
                "response": result_text,
                "effort": effort,
                "duration": duration,
                "question": question
            }
            
        except Exception as e:
            error_msg = f"基本推論失敗: {e}"
            return {
                "success": False,
                "error": error_msg,
                "effort": effort,
                "question": question
            }
    
    def test_all_levels(self, question: str) -> Dict[str, Any]:
        """
        全推論レベルでのテスト実行（デバッグ済み）
        
        Args:
            question: テスト質問
            
        Returns:
            全レベルの結果辞書
        """
        print("\n=== 推論レベル別テスト ===")
        print(f"質問: {question}")
        
        levels = ["low", "medium", "high"]
        results = {}
        
        for level in levels:
            try:
                print(f"\n{level.upper()}レベルテスト中...")
                start_time = time.time()
                
                response = self.client.client.responses.create(
                    model=self.deployment,
                    input=question,
                    reasoning={"effort": level}
                )
                
                duration = time.time() - start_time
                result_text = response.output_text
                
                results[level] = {
                    "success": True,
                    "response": result_text,
                    "duration": duration
                }
                
                print(f"OK {level.upper()}レベル成功（{duration:.1f}秒）")
                print(f"回答: {result_text[:100]}...")
                
            except Exception as e:
                print(f"NG {level.upper()}レベル失敗: {e}")
                results[level] = {
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
        
        return {
            "question": question,
            "levels": results,
            "summary": self._generate_summary(results)
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """結果サマリーを生成"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get("success", False))
        
        # 実行時間の統計
        durations = [r.get("duration", 0) for r in results.values() if r.get("success", False)]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "average_duration": avg_duration,
            "fastest_level": min(results.keys(), key=lambda k: results[k].get("duration", float('inf'))) if durations else None,
            "slowest_level": max(results.keys(), key=lambda k: results[k].get("duration", 0)) if durations else None
        }
    
    def quick_test(self) -> bool:
        """クイックテスト実行"""
        print("\n=== 推論ハンドラークイックテスト ===")
        
        result = self.basic_reasoning("1+1は何ですか？", effort="low")
        
        if result["success"]:
            print("OK 推論ハンドラーテスト成功")
            return True
        else:
            print(f"NG 推論ハンドラーテスト失敗: {result.get('error')}")
            return False


# 使用例とテスト関数
def test_reasoning_handler():
    """推論ハンドラーのテスト"""
    from pathlib import Path
    from core.azure_auth import O3ProConfig, O3ProClient
    
    print("推論ハンドラーテスト開始...")
    
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
    
    # 推論ハンドラーテスト
    handler = ReasoningHandler(client)
    
    # クイックテスト
    if not handler.quick_test():
        return False
    
    # 全レベルテスト
    test_question = "97は素数ですか？理由も教えてください。"
    results = handler.test_all_levels(test_question)
    
    summary = results["summary"]
    print(f"\n=== テスト結果サマリー ===")
    print(f"成功率: {summary['success_rate']:.1f}%")
    print(f"平均実行時間: {summary['average_duration']:.1f}秒")
    
    return summary["success_rate"] == 100


if __name__ == "__main__":
    test_reasoning_handler()