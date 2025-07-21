# エラーハンドラーモジュール 仕様書

## 概要
`error_handler.py`は、統一的なエラー処理とレスポンス生成を提供するモジュールです。エラーの安全な処理とリトライ機能を提供します。

## 主要関数

### 1. create_safe_response
エラー情報を含む安全なレスポンス辞書を生成

#### シグネチャ
```python
def create_safe_response(
    success: bool,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    error_type: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]
```

#### パラメータ
- `success` (bool): 処理の成功/失敗
- `data` (dict, optional): 成功時のデータ
- `error` (str, optional): エラーメッセージ
- `error_type` (str, optional): エラーの種類
- `**kwargs`: 追加のフィールド

#### 戻り値
```python
{
    "success": bool,
    "data": dict or None,
    "error": str or None,
    "error_type": str or None,
    "timestamp": str,
    # その他のkwargsで指定したフィールド
}
```

### 2. retry_with_exponential_backoff
指数バックオフ付きリトライデコレーター

#### シグネチャ
```python
def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable
```

#### パラメータ
- `max_retries` (int): 最大リトライ回数（デフォルト: 3）
- `initial_delay` (float): 初回リトライ待機時間（秒）（デフォルト: 1.0）
- `max_delay` (float): 最大待機時間（秒）（デフォルト: 60.0）
- `exponential_base` (float): 指数基数（デフォルト: 2.0）
- `exceptions` (tuple): リトライ対象の例外タプル

### 3. format_error_message
エラーメッセージのフォーマット

#### シグネチャ
```python
def format_error_message(
    error: Exception,
    context: Optional[str] = None
) -> str
```

### 4. is_retryable_error
リトライ可能なエラーかチェック

#### シグネチャ
```python
def is_retryable_error(error: Exception) -> bool
```

## 使用例

### 基本的なエラーレスポンス生成
```python
from core.error_handler import create_safe_response

# 成功レスポンス
response = create_safe_response(
    success=True,
    data={"result": "処理完了", "count": 10}
)

# エラーレスポンス
response = create_safe_response(
    success=False,
    error="接続に失敗しました",
    error_type="CONNECTION_ERROR",
    retry_after=30
)
```

### リトライデコレーターの使用
```python
from core.error_handler import retry_with_exponential_backoff
import requests

@retry_with_exponential_backoff(
    max_retries=5,
    initial_delay=2.0,
    exceptions=(requests.RequestException,)
)
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# 自動的にリトライされる
data = fetch_data("https://api.example.com/data")
```

### エラーメッセージのフォーマット
```python
from core.error_handler import format_error_message

try:
    # 何か処理
    result = risky_operation()
except Exception as e:
    formatted_msg = format_error_message(e, context="データ処理中")
    print(formatted_msg)
```

### リトライ可能エラーの判定
```python
from core.error_handler import is_retryable_error
import openai

try:
    response = client.chat.completions.create(...)
except Exception as e:
    if is_retryable_error(e):
        print("リトライ可能なエラーです")
    else:
        print("リトライ不可能なエラーです")
```

## エラータイプ

定義済みエラータイプ:
- `CONNECTION_ERROR`: 接続エラー
- `TIMEOUT_ERROR`: タイムアウト
- `AUTHENTICATION_ERROR`: 認証エラー
- `VALIDATION_ERROR`: 検証エラー
- `RATE_LIMIT_ERROR`: レート制限
- `UNKNOWN_ERROR`: 不明なエラー

## 統合例

### Azure OpenAIとの統合
```python
from core.error_handler import create_safe_response, retry_with_exponential_backoff
from core.azure_auth import O3ProClient

@retry_with_exponential_backoff(max_retries=3)
def call_o3_pro(client, prompt):
    try:
        response = client.client.responses.create(
            model="o3-pro",
            input=prompt,
            reasoning={"effort": "low"}
        )
        return create_safe_response(
            success=True,
            data={"response": response.output_text}
        )
    except Exception as e:
        return create_safe_response(
            success=False,
            error=str(e),
            error_type="API_ERROR"
        )
```

## 注意事項

1. **タイムスタンプ**: すべてのレスポンスにISO形式のタイムスタンプが自動付与
2. **エラー詳細**: エラー時は`error`と`error_type`の両方を設定することを推奨
3. **リトライ対象**: ネットワークエラーや一時的なエラーのみリトライ対象
4. **最大遅延**: リトライ間隔は最大60秒に制限

## リトライ可能なエラー

以下のエラーは自動的にリトライ対象と判定:
- `ConnectionError`
- `TimeoutError`
- `requests.RequestException`
- `openai.APIError` (429, 500, 502, 503, 504)
- `aiohttp.ClientError`

## ベストプラクティス

1. **一貫性**: アプリケーション全体で`create_safe_response`を使用
2. **コンテキスト**: エラー時は`context`パラメータで詳細情報を提供
3. **適切なリトライ**: API呼び出しには適切なリトライ設定を使用
4. **ログ記録**: エラーレスポンスは必ずログに記録