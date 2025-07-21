"""
エラーハンドリングモジュール

既存のo3_pro_complete_toolkit.pyから抽出した動作確認済みのエラー処理機能
create_safe_response関数とリトライロジック、ユーザーフレンドリーメッセージ対応

使用方法:
    from core.error_handler import safe_api_call, ErrorHandler
    
    # 安全なAPI呼び出し
    result = safe_api_call(client, model="o3-pro", input="質問")
    
    # エラーハンドラークラス使用
    handler = ErrorHandler()
    result = handler.handle_api_call(client, **kwargs)

作成日: 2025-07-19（o3_pro_complete_toolkit.pyから抽出）
"""

import time
import functools
from typing import Any, Dict, Optional, Callable
from enum import Enum


class ErrorType(Enum):
    """エラータイプ分類"""
    REASONING_SUMMARY = "reasoning_summary"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class ErrorHandler:
    """エラーハンドリングクラス"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        エラーハンドラー初期化
        
        Args:
            max_retries: 最大リトライ回数
            base_delay: 基本待機時間（秒）
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def classify_error(self, error: Exception) -> ErrorType:
        """エラーを分類"""
        error_str = str(error).lower()
        
        if "reasoning.summary" in error_str:
            return ErrorType.REASONING_SUMMARY
        elif "rate limit" in error_str or "too many requests" in error_str:
            return ErrorType.RATE_LIMIT
        elif "timeout" in error_str:
            return ErrorType.TIMEOUT
        elif "auth" in error_str or "unauthorized" in error_str:
            return ErrorType.AUTH_ERROR
        elif "network" in error_str or "connection" in error_str:
            return ErrorType.NETWORK_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def get_user_friendly_message(self, error: Exception, error_type: ErrorType) -> str:
        """ユーザーフレンドリーなエラーメッセージを生成"""
        messages = {
            ErrorType.REASONING_SUMMARY: "推論プロセスの表示に問題がありました。暗号化されたコンテンツで再試行しています。",
            ErrorType.RATE_LIMIT: "API利用制限に達しました。しばらく待ってから再試行してください。",
            ErrorType.TIMEOUT: "処理に時間がかかりすぎました。ネットワーク接続を確認してください。",
            ErrorType.AUTH_ERROR: "認証に問題があります。API設定を確認してください。",
            ErrorType.NETWORK_ERROR: "ネットワーク接続に問題があります。接続を確認してください。",
            ErrorType.UNKNOWN: f"予期しないエラーが発生しました: {str(error)}"
        }
        
        return messages.get(error_type, messages[ErrorType.UNKNOWN])
    
    def handle_reasoning_summary_error(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """reasoning.summaryエラーの自動修正（デバッグ済み）"""
        print("reasoning.summaryエラーを検出、encrypted_contentに変更してリトライ...")
        
        # 既存のincludeパラメータを削除/修正
        modified_kwargs = kwargs.copy()
        modified_kwargs['include'] = ["reasoning.encrypted_content"]
        modified_kwargs['store'] = False
        
        return modified_kwargs
    
    def calculate_retry_delay(self, attempt: int, error_type: ErrorType) -> float:
        """リトライ待機時間を計算"""
        if error_type == ErrorType.RATE_LIMIT:
            # レート制限の場合は長めに待機
            return self.base_delay * (2 ** attempt) + 10
        else:
            # 指数バックオフ
            return self.base_delay * (2 ** attempt)
    
    def handle_api_call(self, client, **kwargs) -> Any:
        """
        API呼び出しのエラーハンドリング
        
        Args:
            client: APIクライアント
            **kwargs: API呼び出しパラメータ
            
        Returns:
            APIレスポンスまたはエラー辞書
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # API呼び出し実行
                return client.responses.create(**kwargs)
                
            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                user_message = self.get_user_friendly_message(e, error_type)
                
                print(f"試行 {attempt + 1}/{self.max_retries + 1} 失敗: {user_message}")
                
                # reasoning.summaryエラーの特別処理
                if error_type == ErrorType.REASONING_SUMMARY and attempt == 0:
                    kwargs = self.handle_reasoning_summary_error(kwargs)
                    continue
                
                # 最後の試行でない場合は待機
                if attempt < self.max_retries:
                    delay = self.calculate_retry_delay(attempt, error_type)
                    print(f"{delay:.1f}秒待機してリトライします...")
                    time.sleep(delay)
                else:
                    # 最後の試行も失敗
                    print(f"NG 全ての試行が失敗しました: {user_message}")
        
        # 全ての試行が失敗した場合
        return {
            "success": False,
            "error": self.get_user_friendly_message(last_error, self.classify_error(last_error)),
            "error_type": self.classify_error(last_error).value,
            "raw_error": str(last_error)
        }


def safe_api_call(client, **kwargs) -> Any:
    """
    安全なAPI呼び出し関数（動作確認済み）
    
    既存のcreate_safe_response関数をベースにした改良版
    
    Args:
        client: APIクライアント
        **kwargs: API呼び出しパラメータ
        
    Returns:
        APIレスポンスまたはエラー辞書
    """
    try:
        return client.responses.create(**kwargs)
    except Exception as e:
        error_str = str(e)
        
        # reasoning.summary エラーの自動修正（デバッグ済み）
        if "reasoning.summary" in error_str:
            print("reasoning.summaryエラーを検出、encrypted_contentに変更してリトライ...")
            kwargs['include'] = ["reasoning.encrypted_content"]
            kwargs['store'] = False
            return client.responses.create(**kwargs)
        
        # その他のエラーは再発生
        raise e


def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    指数バックオフでのリトライデコレータ
    
    Args:
        max_retries: 最大リトライ回数
        base_delay: 基本待機時間（秒）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(max_retries, base_delay)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    
                    error_type = handler.classify_error(e)
                    delay = handler.calculate_retry_delay(attempt, error_type)
                    
                    print(f"試行 {attempt + 1} 失敗、{delay:.1f}秒後にリトライ: {e}")
                    time.sleep(delay)
            
        return wrapper
    return decorator


# 使用例とテスト関数
def test_error_handler():
    """エラーハンドラーのテスト"""
    print("エラーハンドラーテスト開始...")
    
    # エラータイプ分類テスト
    handler = ErrorHandler()
    
    test_errors = [
        (Exception("reasoning.summary is not supported"), ErrorType.REASONING_SUMMARY),
        (Exception("Rate limit exceeded"), ErrorType.RATE_LIMIT),
        (Exception("Connection timeout"), ErrorType.TIMEOUT),
        (Exception("Authentication failed"), ErrorType.AUTH_ERROR),
        (Exception("Network connection error"), ErrorType.NETWORK_ERROR),
        (Exception("Some unknown error"), ErrorType.UNKNOWN)
    ]
    
    print("=== エラー分類テスト ===")
    all_passed = True
    
    for error, expected_type in test_errors:
        classified_type = handler.classify_error(error)
        message = handler.get_user_friendly_message(error, classified_type)
        
        if classified_type == expected_type:
            print(f"OK {error} → {classified_type.value}")
            print(f"   メッセージ: {message}")
        else:
            print(f"NG {error} → 期待: {expected_type.value}, 実際: {classified_type.value}")
            all_passed = False
    
    # リトライ待機時間テスト
    print("\n=== リトライ待機時間テスト ===")
    for attempt in range(3):
        delay_normal = handler.calculate_retry_delay(attempt, ErrorType.UNKNOWN)
        delay_rate_limit = handler.calculate_retry_delay(attempt, ErrorType.RATE_LIMIT)
        print(f"試行 {attempt + 1}: 通常 {delay_normal:.1f}秒, レート制限 {delay_rate_limit:.1f}秒")
    
    if all_passed:
        print("\nOK エラーハンドラーテスト成功")
        return True
    else:
        print("\nNG エラーハンドラーテスト失敗")
        return False


if __name__ == "__main__":
    test_error_handler()