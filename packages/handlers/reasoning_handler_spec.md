# 推論ハンドラー モジュール仕様書

## 概要
`reasoning_handler.py`は、Azure OpenAI o3-proの基本推論機能を処理するハンドラーです。low/medium/highの3つのeffortレベルに対応しています。

## クラス: ReasoningHandler

### コンストラクタ
```python
ReasoningHandler(client: O3ProClient)
```

#### パラメータ
- `client`: 初期化済みのO3ProClientインスタンス

### メソッド

#### basic_reasoning
基本推論を実行

```python
def basic_reasoning(
    question: str, 
    effort: str = "low"
) -> Dict[str, Any]
```

##### パラメータ
- `question` (str): 推論対象の質問やプロンプト
- `effort` (str): 推論努力レベル ("low", "medium", "high")

##### 戻り値
```python
{
    "success": bool,          # 処理成功/失敗
    "response": str,          # 推論結果（成功時）
    "error": str,             # エラーメッセージ（失敗時）
    "effort": str,            # 使用したeffortレベル
    "duration": float,        # 処理時間（秒）
    "question": str           # 元の質問
}
```

#### reasoning_with_context
コンテキスト付き推論（将来実装予定）

```python
def reasoning_with_context(
    question: str,
    context: List[Dict[str, str]],
    effort: str = "low"
) -> Dict[str, Any]
```

## 使用例

### 基本的な使用方法
```python
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler

# クライアント初期化
config = O3ProConfig()
client = O3ProClient(config)

# ハンドラー作成
handler = ReasoningHandler(client)

# 低努力レベルで推論
result = handler.basic_reasoning(
    "Pythonでフィボナッチ数列を生成する関数を書いてください",
    effort="low"
)

if result["success"]:
    print(f"推論結果: {result['response']}")
    print(f"処理時間: {result['duration']:.2f}秒")
else:
    print(f"エラー: {result['error']}")
```

### effortレベル別の使用
```python
# 高精度推論（時間がかかる）
result = handler.basic_reasoning(
    "量子コンピューティングの基本原理を説明してください",
    effort="high"
)

# 中程度の推論
result = handler.basic_reasoning(
    "機械学習とディープラーニングの違いは何ですか？",
    effort="medium"
)
```

### エラーハンドリング付き使用
```python
questions = [
    "質問1",
    "質問2",
    "質問3"
]

for question in questions:
    result = handler.basic_reasoning(question, effort="low")
    
    if result["success"]:
        print(f"Q: {question}")
        print(f"A: {result['response'][:100]}...")
        print(f"時間: {result['duration']:.1f}秒\n")
    else:
        print(f"質問「{question}」でエラー: {result['error']}\n")
```

## effortレベルの特徴

### low (低)
- **処理時間**: 通常5-10秒
- **用途**: 簡単な質問、基本的なコード生成
- **精度**: 基本的な精度
- **トークン消費**: 少ない

### medium (中)
- **処理時間**: 通常10-30秒
- **用途**: 複雑な質問、詳細な説明
- **精度**: より高い精度
- **トークン消費**: 中程度

### high (高)
- **処理時間**: 30秒以上
- **用途**: 高度な推論、複雑な問題解決
- **精度**: 最高精度
- **トークン消費**: 多い

## エラー処理

### 一般的なエラー
```python
# クライアント未初期化
{
    "success": False,
    "error": "クライアントが初期化されていません"
}

# API呼び出しエラー
{
    "success": False,
    "error": "API Error: [詳細メッセージ]"
}

# タイムアウト
{
    "success": False,
    "error": "Request timeout"
}
```

### リトライ機能
内部で`reasoning.summary`エラーに対する自動リトライを実装:
- 最大3回リトライ
- 指数バックオフ（2秒、4秒、8秒）

## パフォーマンス考慮事項

1. **effortレベルの選択**: 
   - 簡単な質問には`low`を使用
   - 精度が必要な場合のみ`high`を使用

2. **並列処理**: 
   - 複数質問がある場合は非同期処理を検討
   - BackgroundHandlerとの組み合わせ

3. **キャッシュ**: 
   - 同じ質問の再実行を避ける
   - 結果をローカルに保存

## 注意事項

1. **応答形式**: o3-proの応答は`output_text`フィールドに格納
2. **エラー時**: `error`フィールドに詳細が格納される
3. **処理時間**: effortレベルにより大きく変動
4. **同期処理**: このハンドラーは同期的に動作

## 動作確認済み機能

- ✅ 全effortレベル（low/medium/high）での推論
- ✅ エラーハンドリング
- ✅ reasoning.summaryエラーの自動リトライ
- ✅ 処理時間測定
- ✅ 日本語・英語での質問対応