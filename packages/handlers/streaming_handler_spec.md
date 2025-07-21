# ストリーミングハンドラー モジュール仕様書

## 概要
`streaming_handler.py`は、Azure OpenAI o3-proのストリーミング応答を処理するハンドラーです。リアルタイムでチャンク単位の応答を処理できます。

## クラス: StreamingHandler

### コンストラクタ
```python
StreamingHandler(client: O3ProClient)
```

#### パラメータ
- `client`: 初期化済みのO3ProClientインスタンス

### メソッド

#### stream_with_callback
コールバック関数を使用してストリーミング応答を処理

```python
def stream_with_callback(
    question: str,
    on_chunk: Callable[[str], None],
    effort: str = "low"
) -> Dict[str, Any]
```

##### パラメータ
- `question` (str): 推論対象の質問やプロンプト
- `on_chunk` (Callable): チャンク受信時のコールバック関数
- `effort` (str): 推論努力レベル ("low", "medium", "high")

##### 戻り値
```python
{
    "success": bool,           # 処理成功/失敗
    "response": str,           # 完全な応答テキスト（成功時）
    "error": str,              # エラーメッセージ（失敗時）
    "effort": str,             # 使用したeffortレベル
    "duration": float,         # 総処理時間（秒）
    "chunk_count": int,        # 受信したチャンク数
    "first_chunk_time": float, # 最初のチャンクまでの時間（秒）
    "question": str            # 元の質問
}
```

#### stream_to_list
応答をリストとして収集（デバッグ用）

```python
def stream_to_list(
    question: str,
    effort: str = "low"
) -> Dict[str, Any]
```

## 使用例

### 基本的な使用方法
```python
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import StreamingHandler

# クライアント初期化
config = O3ProConfig()
client = O3ProClient(config)

# ハンドラー作成
handler = StreamingHandler(client)

# コンソールに直接出力
def print_chunk(chunk):
    print(chunk, end='', flush=True)

result = handler.stream_with_callback(
    "Pythonの基本的なデータ型を説明してください",
    print_chunk,
    effort="low"
)

if result["success"]:
    print(f"\n\n処理時間: {result['duration']:.2f}秒")
    print(f"チャンク数: {result['chunk_count']}")
```

### UIへの統合例
```python
# Tkinterの例
import tkinter as tk

class ChatUI:
    def __init__(self):
        self.text_widget = tk.Text()
        self.handler = StreamingHandler(client)
    
    def stream_response(self, question):
        # UIにチャンクを追加
        def update_ui(chunk):
            self.text_widget.insert(tk.END, chunk)
            self.text_widget.update()
        
        result = self.handler.stream_with_callback(
            question,
            update_ui,
            effort="low"
        )
```

### プログレス表示付き
```python
import sys

class StreamProgress:
    def __init__(self):
        self.char_count = 0
    
    def on_chunk(self, chunk):
        self.char_count += len(chunk)
        sys.stdout.write(f"\r文字数: {self.char_count} ")
        sys.stdout.flush()

progress = StreamProgress()
result = handler.stream_with_callback(
    "長い説明を要する質問",
    progress.on_chunk,
    effort="medium"
)
```

### エラーハンドリング
```python
def safe_stream(question):
    chunks = []
    
    def collect_chunk(chunk):
        chunks.append(chunk)
        print(chunk, end='', flush=True)
    
    result = handler.stream_with_callback(
        question,
        collect_chunk,
        effort="low"
    )
    
    if result["success"]:
        # 完全な応答も利用可能
        full_response = result["response"]
        # または収集したチャンクを使用
        collected = ''.join(chunks)
    else:
        print(f"\nストリーミングエラー: {result['error']}")
```

## ストリーミングの特徴

### イベントベースAPI
o3-proのストリーミングはイベントベース:
```python
# 内部処理
for event in stream:
    if event.type == "response.output_text.delta":
        chunk_text = event.delta
        on_chunk(chunk_text)
```

### パフォーマンス指標
- **最初のチャンクまでの時間**: `first_chunk_time`で測定
- **総処理時間**: `duration`で測定
- **チャンク数**: ストリーミングの粒度を示す

## コールバック関数の要件

### 基本要件
```python
def callback(chunk: str) -> None:
    # チャンクテキストを処理
    pass
```

### エラーハンドリング付き
```python
def safe_callback(chunk: str) -> None:
    try:
        # UI更新など
        update_display(chunk)
    except Exception as e:
        # エラーをログに記録
        logger.error(f"Callback error: {e}")
```

## 注意事項

1. **コールバックエラー**: コールバック内のエラーは警告として表示されるが、ストリーミングは継続
2. **バッファリング**: 出力にはflush=Trueを使用してリアルタイム表示
3. **完全な応答**: `response`フィールドには全チャンクを結合した完全なテキストが格納
4. **同期処理**: このハンドラーは同期的に動作（非同期版は別途実装可能）

## エラー処理

### 一般的なエラー
```python
# ストリーミング未対応
{
    "success": False,
    "error": "Streaming not supported for this model"
}

# ネットワークエラー
{
    "success": False,
    "error": "Connection lost during streaming"
}

# コールバックエラー（警告のみ）
# WARN コールバックエラー: [詳細]
```

## ベストプラクティス

1. **UI更新**: UIスレッドでの更新に注意
2. **バッファサイズ**: 大量のテキストの場合はバッファ管理を検討
3. **キャンセル機能**: 長時間のストリーミングにはキャンセル機能を実装
4. **エラー回復**: ネットワークエラー時の再接続ロジック

## 動作確認済み機能

- ✅ リアルタイムストリーミング表示
- ✅ 全effortレベル対応
- ✅ チャンク数とタイミング測定
- ✅ コールバックエラーの適切な処理
- ✅ 完全な応答テキストの収集
- ✅ 日本語・英語のストリーミング