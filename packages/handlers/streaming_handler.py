"""
ストリーミング処理ハンドラー

既存のO3ProTesterクラスから抽出した動作確認済みのストリーミング機能
リアルタイムレスポンス、チャンク処理、プログレス表示対応

使用方法:
    from handlers.streaming_handler import StreamingHandler
    from core.azure_auth import O3ProClient, O3ProConfig
    
    config = O3ProConfig()
    client = O3ProClient(config)
    handler = StreamingHandler(client)
    
    # ストリーミング実行
    result = handler.stream_response("質問内容")
    
    # コールバック付きストリーミング
    def on_chunk(chunk_text):
        print(chunk_text, end='', flush=True)
    
    result = handler.stream_with_callback("質問内容", on_chunk)

作成日: 2025-07-19（o3_pro_complete_toolkit.pyから抽出）
"""

import time
from typing import Dict, Any, Optional, Callable, Iterator
from core.azure_auth import O3ProClient


class StreamingHandler:
    """ストリーミング処理ハンドラークラス（動作確認済み）"""
    
    def __init__(self, client: O3ProClient):
        """
        ハンドラー初期化
        
        Args:
            client: 認証済みのO3ProClientインスタンス
        """
        self.client = client
        self.deployment = client.config.deployment
    
    def stream_response(self, question: str, effort: str = "low") -> Dict[str, Any]:
        """
        ストリーミング応答実行（デバッグ済み）
        
        Args:
            question: 質問内容
            effort: 推論努力レベル ("low", "medium", "high")
            
        Returns:
            ストリーミング結果辞書
        """
        if not self.client.is_ready():
            return {
                "success": False,
                "error": "クライアントが初期化されていません"
            }
        
        try:
            print(f"\n=== ストリーミング応答開始 ({effort}レベル) ===")
            print(f"質問: {question}")
            print("ストリーミング開始...")
            
            start_time = time.time()
            
            stream = self.client.client.responses.create(
                model=self.deployment,
                input=question,
                reasoning={"effort": effort},
                stream=True
            )
            
            full_response = ""
            chunk_count = 0
            
            for event in stream:
                chunk_count += 1
                # o3-proのストリーミングAPIはイベントベース
                if event.type == "response.output_text.delta":
                    if hasattr(event, 'delta'):
                        chunk_text = event.delta
                        print(chunk_text, end='', flush=True)
                        full_response += chunk_text
            
            duration = time.time() - start_time
            
            print()  # 改行
            print(f"OK ストリーミング成功（チャンク数: {chunk_count}、実行時間: {duration:.1f}秒）")
            
            return {
                "success": True,
                "response": full_response,
                "chunk_count": chunk_count,
                "duration": duration,
                "effort": effort,
                "question": question
            }
            
        except Exception as e:
            error_msg = f"ストリーミング失敗: {e}"
            print(f"NG {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "effort": effort,
                "question": question
            }
    
    def stream_with_callback(
        self, 
        question: str, 
        on_chunk: Callable[[str], None],
        effort: str = "low"
    ) -> Dict[str, Any]:
        """
        コールバック付きストリーミング応答
        
        Args:
            question: 質問内容
            on_chunk: チャンク受信時のコールバック関数
            effort: 推論努力レベル
            
        Returns:
            ストリーミング結果辞書
        """
        if not self.client.is_ready():
            return {
                "success": False,
                "error": "クライアントが初期化されていません"
            }
        
        try:
            start_time = time.time()
            
            stream = self.client.client.responses.create(
                model=self.deployment,
                input=question,
                reasoning={"effort": effort},
                stream=True
            )
            
            full_response = ""
            chunk_count = 0
            
            for event in stream:
                chunk_count += 1
                # o3-proのストリーミングAPIはイベントベース
                if event.type == "response.output_text.delta":
                    if hasattr(event, 'delta'):
                        chunk_text = event.delta
                        full_response += chunk_text
                        
                        # コールバック実行
                        try:
                            on_chunk(chunk_text)
                        except Exception as callback_error:
                            print(f"\nWARN コールバックエラー: {callback_error}")
            
            duration = time.time() - start_time
            
            return {
                "success": True,
                "response": full_response,
                "chunk_count": chunk_count,
                "duration": duration,
                "effort": effort,
                "question": question
            }
            
        except Exception as e:
            error_msg = f"コールバック付きストリーミング失敗: {e}"
            return {
                "success": False,
                "error": error_msg,
                "effort": effort,
                "question": question
            }
    
    def stream_generator(self, question: str, effort: str = "low") -> Iterator[str]:
        """
        ジェネレータ形式でのストリーミング
        
        Args:
            question: 質問内容
            effort: 推論努力レベル
            
        Yields:
            チャンクテキスト
        """
        if not self.client.is_ready():
            yield f"ERROR: クライアントが初期化されていません"
            return
        
        try:
            stream = self.client.client.responses.create(
                model=self.deployment,
                input=question,
                reasoning={"effort": effort},
                stream=True
            )
            
            for event in stream:
                # o3-proのストリーミングAPIはイベントベース
                if event.type == "response.output_text.delta":
                    if hasattr(event, 'delta'):
                        yield event.delta
                    
        except Exception as e:
            yield f"ERROR: ストリーミング失敗: {e}"
    
    def quick_test(self) -> bool:
        """クイックテスト実行"""
        print("\n=== ストリーミングハンドラークイックテスト ===")
        
        result = self.stream_response("日本の首都について簡潔に教えてください", effort="low")
        
        if result["success"]:
            print("OK ストリーミングハンドラーテスト成功")
            return True
        else:
            print(f"NG ストリーミングハンドラーテスト失敗: {result.get('error')}")
            return False
    
    def test_all_modes(self) -> Dict[str, Any]:
        """全ストリーミングモードのテスト"""
        print("\n=== 全ストリーミングモードテスト ===")
        
        question = "Python プログラミングについて説明してください"
        results = {}
        
        # 基本ストリーミング
        print("\n1. 基本ストリーミングテスト:")
        results["basic"] = self.stream_response(question, effort="low")
        
        # コールバック付きストリーミング
        print("\n2. コールバック付きストリーミングテスト:")
        callback_output = []
        
        def collect_chunks(chunk):
            callback_output.append(chunk)
        
        results["callback"] = self.stream_with_callback(question, collect_chunks, effort="low")
        results["callback"]["callback_chunks"] = len(callback_output)
        
        # ジェネレータストリーミング
        print("\n3. ジェネレータストリーミングテスト:")
        generator_chunks = []
        try:
            for chunk in self.stream_generator(question, effort="low"):
                generator_chunks.append(chunk)
                print(chunk, end='', flush=True)
            
            print()
            results["generator"] = {
                "success": True,
                "chunk_count": len(generator_chunks),
                "total_length": sum(len(chunk) for chunk in generator_chunks)
            }
            print("OK ジェネレータストリーミング成功")
            
        except Exception as e:
            results["generator"] = {
                "success": False,
                "error": str(e)
            }
            print(f"NG ジェネレータストリーミング失敗: {e}")
        
        # サマリー
        success_count = sum(1 for r in results.values() if r.get("success", False))
        results["summary"] = {
            "total_tests": len(results) - 1,  # summaryを除く
            "successful_tests": success_count,
            "success_rate": (success_count / (len(results) - 1) * 100)
        }
        
        return results


# 使用例とテスト関数
def test_streaming_handler():
    """ストリーミングハンドラーのテスト"""
    from pathlib import Path
    from core.azure_auth import O3ProConfig, O3ProClient
    
    print("ストリーミングハンドラーテスト開始...")
    
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
    
    # ストリーミングハンドラーテスト
    handler = StreamingHandler(client)
    
    # クイックテスト
    if not handler.quick_test():
        return False
    
    # 全モードテスト
    results = handler.test_all_modes()
    
    summary = results["summary"]
    print(f"\n=== テスト結果サマリー ===")
    print(f"成功率: {summary['success_rate']:.1f}%")
    
    return summary["success_rate"] == 100


if __name__ == "__main__":
    test_streaming_handler()