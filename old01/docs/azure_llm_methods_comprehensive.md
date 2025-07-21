# Azure LLMモデル呼び出し方法 - 包括的ガイド

## 概要

Azure OpenAI Serviceは、OpenAIの強力な言語モデルへのREST APIアクセスを提供し、エンタープライズレベルのセキュリティとスケーラビリティを実現します。本ガイドでは、各種の呼び出し方法、対応モデル、APIバージョンについて詳細に解説します。

## 1. API呼び出し方法の分類

### 1.1 REST API（直接呼び出し）

#### Chat Completions API
**エンドポイント：**
```
POST https://{endpoint}/openai/deployments/{deployment-id}/chat/completions?api-version={api-version}
```

**最新APIバージョン：**
- **GA版**: `2024-10-21` （最新安定版）
- **Preview版**: `2025-04-01-preview` （最新機能含む）

**対応モデル：**
- GPT-4o, GPT-4o mini
- GPT-4.1, GPT-4.1-nano
- GPT-4 Turbo with Vision
- GPT-3.5 Turbo
- o3, o3-mini, o1, o1-mini（推論モデル）

#### Completions API（レガシー）
**エンドポイント：**
```
POST https://{endpoint}/openai/deployments/{deployment-id}/completions?api-version={api-version}
```

**対応モデル：**
- GPT-3.5 Turbo Instruct
- レガシーGPT-3モデル（Ada, Babbage, Curie, Davinci）

#### Responses API（新機能）
**エンドポイント：**
```
POST https://{endpoint}/openai/v1/responses
```

**特徴：**
- Chat CompletionsとAssistants APIの統合
- ステートフルAPI
- Computer-use-preview モデル対応
- MCP (Model Context Protocol) ツール対応

### 1.2 SDKベースの呼び出し

#### Python SDK
```python
# Azure OpenAI専用SDK（旧）
from azure.openai import AzureOpenAI

# OpenAI SDK（推奨）
from openai import AzureOpenAI
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# キーベース認証
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Microsoft Entra ID認証（推奨）
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), 
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = client.chat.completions.create(
    model="gpt-4o",  # デプロイメント名
    messages=[
        {"role": "system", "content": "あなたは役立つアシスタントです。"},
        {"role": "user", "content": "Azure OpenAIについて教えてください。"}
    ]
)
```

#### JavaScript/TypeScript SDK
```javascript
// npm install openai @azure/identity
import { AzureOpenAI } from "openai";
import { DefaultAzureCredential, getBearerTokenProvider } from "@azure/identity";

const credential = new DefaultAzureCredential();
const scope = "https://cognitiveservices.azure.com/.default";
const azureADTokenProvider = getBearerTokenProvider(credential, scope);

const client = new AzureOpenAI({
    azureADTokenProvider,
    apiVersion: "2024-10-21",
    endpoint: process.env.AZURE_OPENAI_ENDPOINT,
});

const result = await client.chat.completions.create({
    model: "gpt-4o",
    messages: [
        { role: "system", content: "あなたは役立つアシスタントです。" },
        { role: "user", content: "Azure OpenAIについて教えてください。" }
    ],
});
```

#### C# SDK
```csharp
using Azure;
using Azure.AI.OpenAI;
using Azure.Identity;

var credential = new DefaultAzureCredential();
var client = new AzureOpenAIClient(
    new Uri("https://your-resource.openai.azure.com/"),
    credential);

var chatClient = client.GetChatClient("gpt-4o");

var completion = await chatClient.CompleteChatAsync(
    [
        new SystemChatMessage("あなたは役立つアシスタントです。"),
        new UserChatMessage("Azure OpenAIについて教えてください。")
    ]);

Console.WriteLine(completion.Value.Content[0].Text);
```

#### Java SDK
```java
import com.azure.ai.openai.OpenAIClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.*;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.identity.DefaultAzureCredentialBuilder;

OpenAIClient client = new OpenAIClientBuilder()
    .endpoint("https://your-resource.openai.azure.com/")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();

List<ChatRequestMessage> chatMessages = Arrays.asList(
    new ChatRequestSystemMessage("あなたは役立つアシスタントです。"),
    new ChatRequestUserMessage("Azure OpenAIについて教えてください。")
);

ChatCompletions chatCompletions = client.getChatCompletions("gpt-4o", 
    new ChatCompletionsOptions(chatMessages));
```

### 1.3 Prompt Flow Integration
```yaml
# LLMツールでのAzure OpenAI接続
type: llm
inputs:
  deployment_name: gpt-4o
  temperature: 0.7
  max_tokens: 1000
  messages:
    - role: system
      content: "あなたは役立つアシスタントです。"
    - role: user
      content: "${inputs.question}"
connection: azure_openai_connection
api: chat
```

### 1.4 LangChain Integration
```python
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2024-10-21",
    temperature=0.7,
    max_tokens=800,
)

messages = [
    ("system", "あなたは役立つアシスタントです。"),
    ("human", "Azure OpenAIについて教えてください。"),
]

response = llm.invoke(messages)
print(response.content)
```

## 2. 対応モデル一覧

### 2.1 最新推論モデル（o-シリーズ）

| モデル名 | 用途 | コンテキスト長 | API |
|---------|------|-------------|-----|
| o3 | 高度な推論・問題解決 | 200K | Chat Completions, Responses |
| o3-mini | 効率的な推論 | 128K | Chat Completions, Responses |
| o1 | 推論タスク | 128K | Chat Completions |
| o1-mini | 軽量推論 | 128K | Chat Completions |

### 2.2 GPT-4シリーズ

| モデル名 | 用途 | コンテキスト長 | マルチモーダル | API |
|---------|------|-------------|-------------|-----|
| GPT-4.1 | 最新汎用モデル | 1M | ✓ | Chat Completions, Responses |
| GPT-4.1-nano | 軽量版 | 128K | ✓ | Chat Completions |
| GPT-4o | 最適化版 | 128K | ✓ | Chat Completions, Audio |
| GPT-4o mini | 効率版 | 128K | ✓ | Chat Completions |
| GPT-4 Turbo | 高性能版 | 128K | ✓（Vision） | Chat Completions |

### 2.3 GPT-3.5シリーズ

| モデル名 | 用途 | コンテキスト長 | API |
|---------|------|-------------|-----|
| GPT-3.5 Turbo | 汎用チャット | 16K | Chat Completions |
| GPT-3.5 Turbo Instruct | 指示特化 | 4K | Completions |

### 2.4 特殊モデル

| モデル名 | 用途 | API | 制限 |
|---------|------|-----|-----|
| Model Router | 自動モデル選択 | Chat Completions | - |
| computer-use-preview | コンピューター操作 | Responses | 限定アクセス |
| GPT-image-1 | 画像生成 | Images | 限定アクセス |
| Sora | 動画生成 | Video | プレビュー |

### 2.5 音声モデル

| モデル名 | 用途 | API |
|---------|------|-----|
| gpt-4o-transcribe | 音声認識 | Audio |
| gpt-4o-mini-transcribe | 軽量音声認識 | Audio |
| gpt-4o-mini-realtime | リアルタイム音声 | Realtime |

## 3. APIバージョン詳細

### 3.1 安定版（GA）
- **2024-10-21**: 現在の最新GA版
- **2024-06-01**: 前GA版（廃止予定）

### 3.2 プレビュー版
- **2025-04-01-preview**: 最新機能を含む
- **2024-12-01-preview**: 旧プレビュー版

### 3.3 次世代v1 API（2025年5月開始）
- **OpenAI互換**: 最小限のコード変更でOpenAI↔Azure間移行可能
- **自動更新**: 毎月のAPIバージョン更新不要
- **エンドポイント**: `/openai/v1/` プレフィックス

## 4. 認証方法

### 4.1 APIキー認証
```bash
# ヘッダー設定
api-key: YOUR_API_KEY
```

### 4.2 Microsoft Entra ID認証（推奨）
```bash
# ヘッダー設定
Authorization: Bearer YOUR_AZURE_AD_TOKEN
```

**必要なロール:**
- `Cognitive Services OpenAI User`
- `Cognitive Services OpenAI Contributor`

### 4.3 マネージドアイデンティティ
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
```

## 5. 実装ベストプラクティス

### 5.1 エラーハンドリング
```python
import openai
from azure.core.exceptions import ClientAuthenticationError

try:
    response = client.chat.completions.create(...)
except ClientAuthenticationError:
    print("認証エラー: API キーまたは認証情報を確認してください")
except openai.RateLimitError:
    print("レート制限エラー: リクエスト頻度を調整してください")
except Exception as e:
    print(f"予期しないエラー: {e}")
```

### 5.2 トークン管理
```python
import tiktoken

def count_tokens(text, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# コンテキスト長制限を考慮した実装
max_tokens = 128000  # GPT-4oの場合
current_tokens = count_tokens(conversation_history)

if current_tokens > max_tokens:
    # 古い会話履歴を削除または要約
    pass
```

### 5.3 ストリーミング対応
```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

## 6. 料金・デプロイメント戦略

### 6.1 デプロイメント種類
- **Standard**: 従量課金制
- **Provisioned (PTU)**: 専用容量予約
- **Batch**: バッチ処理専用（低コスト）

### 6.2 リージョン別対応状況
**Standard デプロイメント対応リージョン:**
- East US, West US 2, West US 3
- North Central US, South Central US
- Canada East, Brazil South
- UK South, France Central
- Sweden Central, Switzerland North
- Australia East, Japan East
- Korea Central

## 7. トラブルシューティング

### 7.1 よくある問題
1. **認証エラー**: API キーまたはエンドポイントの確認
2. **モデル未デプロイ**: Azure AI Studio でのモデルデプロイが必要
3. **リージョン制限**: モデルがデプロイ予定リージョンで利用可能か確認
4. **クォータ制限**: TPM（Token Per Minute）制限の確認

### 7.2 デバッグ手順
```python
# ログ有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# 接続テスト
try:
    models = client.models.list()
    print("利用可能なモデル:", [model.id for model in models])
except Exception as e:
    print(f"接続エラー: {e}")
```

## 8. 今後の展望

### 8.1 2025年注目機能
- **v1 API**: OpenAI完全互換API
- **Responses API**: 統合ステートフルAPI
- **Computer Use**: コンピューター操作自動化
- **MCP対応**: Model Context Protocol

### 8.2 推奨アップグレードパス
1. 現在のAPIバージョンを最新GA版（2024-10-21）に更新
2. Microsoft Entra ID認証への移行
3. 新しいOpenAI SDKの採用
4. v1 APIへの段階的移行準備

---

## まとめ

Azure OpenAIは多様な呼び出し方法を提供し、エンタープライズニーズに対応した堅牢なLLMサービスです。REST API、各種SDK、統合フレームワークを通じて、最新の推論モデルから特殊用途モデルまで幅広く活用できます。セキュリティと可用性を重視したアーキテクチャにより、本格的なプロダクション環境での運用が可能です。