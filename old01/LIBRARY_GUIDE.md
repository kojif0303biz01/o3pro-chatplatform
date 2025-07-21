# Azure o3-pro ライブラリ使用ガイド

このドキュメントでは、本プロジェクトのライブラリモジュールを他のプロジェクトで使用する方法を説明します。

## 🚀 インストール

### 方法1: 直接コピー
必要なモジュールをプロジェクトにコピー：

```bash
# coreとhandlersフォルダをコピー
cp -r path/to/conect01/core your_project/
cp -r path/to/conect01/handlers your_project/
```

### 方法2: Gitサブモジュール（推奨）
```bash
git submodule add https://github.com/your-repo/conect01.git lib/conect01
```

## 📚 基本的な使用例

### 1. Azure汎用認証

```python
from core.azure_universal_auth import AzureAuthManager, quick_auth, get_azure_token

# 方法1: 簡単なトークン取得
token = get_azure_token("cognitive_services")

# 方法2: 詳細な認証管理
auth_manager = AzureAuthManager()
result = auth_manager.authenticate("cognitive_services")
if result.success:
    print(f"認証成功: {result.method}")
    token = auth_manager.get_token("cognitive_services")

# 方法3: クイック認証
success, credential, message = quick_auth("storage")
```

### 2. o3-pro基本操作

```python
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler

# 設定と認証
config = O3ProConfig()  # .envから自動読み込み
client = O3ProClient(config)

# 推論実行
handler = ReasoningHandler(client)
result = handler.basic_reasoning("質問内容", effort="low")

if result["success"]:
    print(result["response"])
```

### 3. ストリーミング処理

```python
from handlers import StreamingHandler

handler = StreamingHandler(client)

# コンソール出力
def print_chunk(chunk):
    print(chunk, end='', flush=True)

result = handler.stream_with_callback(
    "長い説明をお願いします",
    print_chunk,
    effort="medium"
)
```

### 4. バックグラウンド処理

```python
from handlers import BackgroundHandler
import time

handler = BackgroundHandler(client)

# ジョブ開始
result = handler.start_background_task("複雑な分析", effort="high")
job_id = result["job_id"]

# ステータス確認
while True:
    status = handler.check_status(job_id)
    if status["status"] == "completed":
        break
    time.sleep(5)

# 結果取得
result = handler.get_result(job_id)
print(result["response"])
```

## 🔧 高度な使用例

### Azure AD認証との統合

```python
from core.azure_universal_auth import AzureAuthManager
import openai

# Azure AD認証でOpenAIクライアント作成
auth_manager = AzureAuthManager()
result = auth_manager.authenticate("cognitive_services")

if result.success:
    config = O3ProConfig()
    token = result.credential.get_token("https://cognitiveservices.azure.com/.default")
    
    # トークンベース認証
    client = openai.AzureOpenAI(
        azure_endpoint=config.endpoint,
        api_version=config.api_version,
        azure_ad_token=token.token
    )
```

### エラーハンドリング

```python
from core.error_handler import create_safe_response, retry_with_exponential_backoff

@retry_with_exponential_backoff(max_retries=3)
def call_api(prompt):
    try:
        result = handler.basic_reasoning(prompt)
        return create_safe_response(
            success=True,
            data=result
        )
    except Exception as e:
        return create_safe_response(
            success=False,
            error=str(e),
            error_type="API_ERROR"
        )
```

### 複数サービスの認証

```python
# 複数のAzureサービスを使用
auth_manager = AzureAuthManager()

# Cognitive Services用トークン
cog_token = auth_manager.get_token("cognitive_services")

# Storage用トークン
auth_manager.authenticate("storage")
storage_token = auth_manager.get_token("storage")

# Key Vault用トークン
auth_manager.authenticate("keyvault")
kv_token = auth_manager.get_token("keyvault")
```

## 🎯 ユースケース別ガイド

### Webアプリケーションでの使用

```python
from flask import Flask, request, jsonify
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler

app = Flask(__name__)

# 起動時に初期化
config = O3ProConfig()
client = O3ProClient(config)
handler = ReasoningHandler(client)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    result = handler.basic_reasoning(
        data['message'],
        effort=data.get('effort', 'low')
    )
    return jsonify(result)
```

### バッチ処理での使用

```python
import csv
from concurrent.futures import ThreadPoolExecutor

def process_question(question):
    return handler.basic_reasoning(question, effort="low")

# CSVから質問を読み込んで並列処理
with open('questions.csv', 'r') as f:
    questions = [row[0] for row in csv.reader(f)]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_question, questions))
```

### CLIツールでの使用

```python
import argparse
from core.azure_auth import O3ProConfig, O3ProClient
from handlers import ReasoningHandler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question', help='質問内容')
    parser.add_argument('--effort', default='low', choices=['low', 'medium', 'high'])
    args = parser.parse_args()
    
    config = O3ProConfig()
    client = O3ProClient(config)
    handler = ReasoningHandler(client)
    
    result = handler.basic_reasoning(args.question, args.effort)
    if result["success"]:
        print(result["response"])
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
```

## 📋 環境変数設定

プロジェクトルートに`.env`ファイルを作成：

```bash
# 必須設定
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=O3-pro

# Azure AD認証（オプション）
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

## 🔍 トラブルシューティング

### 認証エラー

```python
# デバッグ情報を表示
config = O3ProConfig()
config.display_config(masked=True)

# 認証状態確認
auth_manager = AzureAuthManager()
health = auth_manager.health_check()
print(health)
```

### パフォーマンス最適化

```python
# キャッシュ有効化
auth_manager = AzureAuthManager(cache_enabled=True)

# 低effortレベルで高速化
result = handler.basic_reasoning(question, effort="low")

# バックグラウンド処理で非ブロッキング
handler.start_background_task(question)
```

## 📄 API リファレンス

詳細なAPIドキュメントは各モジュールの仕様書を参照：

- [Azure汎用認証基盤](core/azure_universal_auth_spec.md)
- [Azure OpenAI認証](core/azure_auth_spec.md)
- [エラーハンドラー](core/error_handler_spec.md)
- [推論ハンドラー](handlers/reasoning_handler_spec.md)
- [ストリーミングハンドラー](handlers/streaming_handler_spec.md)
- [バックグラウンドハンドラー](handlers/background_handler_spec.md)