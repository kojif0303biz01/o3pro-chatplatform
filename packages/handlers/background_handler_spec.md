# バックグラウンドハンドラー モジュール仕様書

## 概要
`background_handler.py`は、Azure OpenAI o3-proのバックグラウンド（非同期）処理を管理するハンドラーです。長時間実行される推論タスクをジョブとして管理します。

## クラス: BackgroundHandler

### コンストラクタ
```python
BackgroundHandler(client: O3ProClient)
```

#### パラメータ
- `client`: 初期化済みのO3ProClientインスタンス

### プロパティ
```python
jobs: Dict[str, Dict[str, Any]]  # アクティブなジョブの辞書
```

### メソッド

#### start_background_task
バックグラウンドタスクを開始

```python
def start_background_task(
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
    "success": bool,        # タスク開始成功/失敗
    "job_id": str,          # ジョブID（成功時）
    "error": str,           # エラーメッセージ（失敗時）
    "status": str,          # 初期ステータス ("started")
    "question": str,        # 元の質問
    "effort": str           # 使用effortレベル
}
```

#### check_status
ジョブのステータスを確認

```python
def check_status(job_id: str) -> Dict[str, Any]
```

##### 戻り値
```python
{
    "success": bool,         # 照会成功/失敗
    "status": str,           # ジョブステータス
    "elapsed_time": float,   # 経過時間（秒）
    "error": str,            # エラーメッセージ（失敗時）
    "question": str,         # 元の質問
    "effort": str            # 使用effortレベル
}
```

#### get_result
完了したジョブの結果を取得

```python
def get_result(job_id: str) -> Dict[str, Any]
```

##### 戻り値
```python
{
    "success": bool,         # 結果取得成功/失敗
    "response": str,         # 推論結果（成功時）
    "error": str,            # エラーメッセージ（失敗時）
    "status": str,           # 最終ステータス
    "total_time": float,     # 総実行時間（秒）
    "question": str,         # 元の質問
    "effort": str            # 使用effortレベル
}
```

#### list_active_jobs
アクティブなジョブ一覧を取得

```python
def list_active_jobs() -> List[Dict[str, Any]]
```

##### 戻り値
```python
[
    {
        "job_id": str,
        "status": str,
        "question": str,
        "effort": str,
        "elapsed_time": float
    },
    ...
]
```

#### cancel_job
実行中のジョブをキャンセル

```python
def cancel_job(job_id: str) -> Dict[str, Any]
```

## 使用例

### 基本的な使用方法
```python
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import BackgroundHandler
import time

# クライアント初期化
config = O3ProConfig()
client = O3ProClient(config)

# ハンドラー作成
handler = BackgroundHandler(client)

# バックグラウンドタスク開始
result = handler.start_background_task(
    "複雑なアルゴリズムの実装方法を詳しく説明してください",
    effort="high"
)

if result["success"]:
    job_id = result["job_id"]
    print(f"ジョブ開始: {job_id}")
    
    # ステータス確認ループ
    while True:
        status = handler.check_status(job_id)
        print(f"ステータス: {status['status']} ({status['elapsed_time']:.1f}秒)")
        
        if status["status"] in ["completed", "failed"]:
            break
        
        time.sleep(5)  # 5秒待機
    
    # 結果取得
    result = handler.get_result(job_id)
    if result["success"]:
        print(f"結果: {result['response']}")
```

### 複数ジョブの並列実行
```python
# 複数の質問を並列処理
questions = [
    ("質問1", "low"),
    ("質問2", "medium"),
    ("質問3", "high")
]

job_ids = []

# すべてのジョブを開始
for question, effort in questions:
    result = handler.start_background_task(question, effort)
    if result["success"]:
        job_ids.append(result["job_id"])
        print(f"ジョブ {result['job_id']} 開始")

# すべてのジョブの完了を待機
completed = set()
while len(completed) < len(job_ids):
    for job_id in job_ids:
        if job_id in completed:
            continue
        
        status = handler.check_status(job_id)
        if status["status"] == "completed":
            result = handler.get_result(job_id)
            print(f"ジョブ {job_id} 完了: {result['response'][:50]}...")
            completed.add(job_id)
    
    time.sleep(2)
```

### ジョブ管理UI例
```python
class JobManager:
    def __init__(self, handler):
        self.handler = handler
    
    def submit_job(self, question, effort="low"):
        result = self.handler.start_background_task(question, effort)
        if result["success"]:
            return result["job_id"]
        return None
    
    def show_active_jobs(self):
        jobs = self.handler.list_active_jobs()
        print(f"\nアクティブジョブ: {len(jobs)}件")
        for job in jobs:
            print(f"- {job['job_id'][:8]}... | {job['status']} | {job['elapsed_time']:.1f}秒")
    
    def get_completed_jobs(self):
        jobs = self.handler.list_active_jobs()
        completed = []
        for job in jobs:
            if job["status"] == "completed":
                result = self.handler.get_result(job["job_id"])
                completed.append(result)
        return completed
```

## ジョブステータス

### ステータスの種類
- `started`: ジョブ開始直後
- `running`: 実行中
- `completed`: 正常完了
- `failed`: エラーで失敗
- `cancelled`: ユーザーによりキャンセル

### ステータス遷移
```
started → running → completed
   ↓         ↓         
cancelled  failed    
```

## エラー処理

### 一般的なエラー
```python
# ジョブが見つからない
{
    "success": False,
    "error": "ジョブが見つかりません: [job_id]"
}

# まだ完了していない
{
    "success": False,
    "error": "ジョブはまだ完了していません",
    "status": "running"
}

# 実行中のエラー
{
    "success": False,
    "error": "API Error: [詳細]",
    "status": "failed"
}
```

## パフォーマンス考慮事項

1. **ポーリング間隔**: 
   - 短いジョブ: 2-5秒
   - 長いジョブ: 10-30秒

2. **メモリ管理**: 
   - 完了したジョブは明示的に削除
   - 大量のジョブには注意

3. **同時実行数**: 
   - API制限に注意
   - 適切な並列数を設定

## 注意事項

1. **メモリ内管理**: ジョブ情報はメモリ内に保持（永続化なし）
2. **プロセス終了**: プロセス終了時にジョブ情報は失われる
3. **スレッドセーフ**: 内部でスレッドロックを使用
4. **自動クリーンアップ**: 完了ジョブは手動で削除が必要

## ベストプラクティス

1. **定期的なステータス確認**: 適切な間隔でポーリング
2. **タイムアウト設定**: 長時間実行ジョブにはタイムアウトを設定
3. **エラーハンドリング**: ジョブ失敗時の適切な処理
4. **リソース管理**: 完了ジョブの定期的なクリーンアップ

## 動作確認済み機能

- ✅ バックグラウンドジョブの開始・管理
- ✅ 複数ジョブの並列実行
- ✅ ジョブステータスの追跡
- ✅ 結果の非同期取得
- ✅ ジョブキャンセル機能
- ✅ スレッドセーフな実装