# Handlers ライブラリモジュール

このフォルダには、Azure OpenAI o3-proの各処理モード用ハンドラーが含まれています。

## 📦 モジュール一覧

### 1. **reasoning_handler.py** - 推論モードハンドラー
- o3-proの基本推論機能を処理
- low/medium/high effortレベル対応
- 詳細: [推論ハンドラー仕様書](./reasoning_handler_spec.md)

### 2. **streaming_handler.py** - ストリーミングモードハンドラー  
- リアルタイムストリーミング応答処理
- チャンク単位のコールバック対応
- 詳細: [ストリーミングハンドラー仕様書](./streaming_handler_spec.md)

### 3. **background_handler.py** - バックグラウンドモードハンドラー
- 非同期バックグラウンド処理
- ジョブ管理とステータス追跡
- 詳細: [バックグラウンドハンドラー仕様書](./background_handler_spec.md)

## 🚀 使用方法

### 基本的な使用例

```python
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler, StreamingHandler, BackgroundHandler

# クライアント初期化
config = O3ProConfig()
client = O3ProClient(config)

# 各ハンドラーの作成
reasoning = ReasoningHandler(client)
streaming = StreamingHandler(client)
background = BackgroundHandler(client)

# 推論実行
result = reasoning.basic_reasoning("質問内容", effort="low")

# ストリーミング実行
def on_chunk(text):
    print(text, end='', flush=True)

result = streaming.stream_with_callback("質問内容", on_chunk)

# バックグラウンド実行
result = background.start_background_task("質問内容")
```

## 📋 共通インターフェース

すべてのハンドラーは以下の共通パターンに従います:

### レスポンス形式
```python
{
    "success": bool,           # 処理成功/失敗
    "response": str,          # 応答テキスト（成功時）
    "error": str,             # エラーメッセージ（失敗時）
    "duration": float,        # 処理時間（秒）
    "effort": str,            # 使用したeffortレベル
    # その他モード固有のフィールド
}
```

### エラーハンドリング
- すべてのハンドラーは`core.error_handler`を使用
- 例外は捕捉され、統一形式のエラーレスポンスを返す

## 🔧 拡張方法

新しいハンドラーを追加する場合:

1. 基本クラスを継承（必須ではないが推奨）
2. `__init__`でO3ProClientを受け取る
3. 処理メソッドは統一レスポンス形式を返す
4. エラーハンドリングは`create_safe_response`を使用

例:
```python
from typing import Dict, Any
from core.azure_auth import O3ProClient
from core.error_handler import create_safe_response

class CustomHandler:
    def __init__(self, client: O3ProClient):
        self.client = client
        self.deployment = client.config.deployment
    
    def process(self, input_text: str, **kwargs) -> Dict[str, Any]:
        try:
            # 処理実装
            result = self._do_something(input_text)
            
            return {
                "success": True,
                "response": result,
                "duration": elapsed_time
            }
        except Exception as e:
            return create_safe_response(
                success=False,
                error=str(e)
            )
```

## 📄 ライセンス

内部使用のみ。再配布時は要相談。