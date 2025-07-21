<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Azureで「必要な時だけ動作する」サーバーレスWebサイトを作る方法

「必要な時だけ動作するWebサイト」をAzureで構築したい場合、サーバーレスアーキテクチャが最適です。Azureには複数のサーバーレスサービスがありますが、代表的なのは **Azure Functions** と **Azure Static Web Apps** です。それぞれの特徴と、要件に応じた最適な構成を提案します。

---

### サーバーレスの基本とメリット

- **リソースは必要な時だけ自動的に起動・停止**されるため、常時稼働のサーバーコストが不要
- **イベント駆動型**（HTTPリクエスト、スケジュール、キューなど）で、必要な時だけ処理が実行される
- **従量課金**なので、アクセスが少ない場合はコストを大幅に抑えられる
- **インフラ管理不要**で、開発に集中できる[^1_10][^1_11][^1_13]

---

## 主要な選択肢

### 1. Azure Static Web Apps

- **静的Webサイト（HTML, CSS, JS）＋サーバーレスAPI**を一体でデプロイ可能
- バックエンドAPIは**Azure Functions（マネージド関数）**として自動的に連携
- **グローバルCDN**による高速配信、オートスケール対応
- GitHubやAzure DevOps連携、CLIによるローカル開発・デプロイも可能[^1_3][^1_6][^1_9]


#### こんな場合に最適

- SPA（React, Vue, Angular等）や静的サイト＋APIで構成したい
- フロントとAPIを一体でサーバーレスに管理したい
- 必要な時だけAPIが起動し、コストを抑えたい


#### デプロイ手順（例）

1. ローカルでアプリ・API開発
2. `npx swa build` でビルド
3. `npx swa deploy --env production` でAzureにデプロイ
4. Azure PortalでURL確認、即公開[^1_3][^1_9]

---

### 2. Azure Functions

- **必要な時だけ関数（APIやバッチ）が起動**するサーバーレス実行環境
- HTTPリクエスト、スケジュール、キュー、Blobなど多様なトリガーに対応
- C\#, JavaScript, Pythonなど複数言語サポート
- バックエンドAPIやバッチ処理、Webhook受信などに最適[^1_4][^1_5][^1_10][^1_11]


#### こんな場合に最適

- APIやバッチ処理のみをサーバーレスで運用したい
- Webフロントは別途用意（例：Blob Storage＋CDNやApp Service）


#### デプロイ手順（例）

1. Azure PortalでFunction Appリソース作成
2. VSCodeやCLIからデプロイ（`Azure Functions: Deploy to Function App...`）[^1_2]
3. HTTPトリガー関数を作成し、Web APIとして公開

---

### 3. Azure App Service（サーバーレスプラン）

- PaaS型Webアプリサービスだが、**App Serviceプランの「従量課金（Consumption）」**や「Premium」プランを選択することで、インスタンスを必要な時だけ起動できる
- .NETやJavaなどのWebアプリをサーバーレス的に運用可能[^1_12]

---

## 要件別おすすめ構成

| 要件 | おすすめサービス | 理由 |
| :-- | :-- | :-- |
| 静的サイト＋API | Azure Static Web Apps | フロント・API一体型、サーバーレス、CDN、高速、コスト最適 |
| API/バッチのみ | Azure Functions | 必要な時だけ起動、従量課金、イベント駆動 |
| ASP.NET等のWebアプリ | App Service（従量課金プラン） | サーバーレス運用、PaaSの拡張性 |


---

## さらに一歩進んだ提案

- **Azure Static Web Apps＋マネージド関数**で、Webフロント・APIを完全サーバーレス化し、CDNで高速配信＆グローバル対応
- **Azure Functions**のDurable Functions拡張で、複雑なワークフローやバッチもサーバーレスで実現
- **Azure MonitorやApplication Insights**で、サーバーレスWebサイトのパフォーマンスや障害も自動監視

---

## 注意点とTips

- サーバーレスは**コールドスタート**（初回起動時の遅延）が発生する場合あり。頻繁なアクセスが想定される場合はPremiumプランの検討も[^1_11]
- 長時間処理や特殊な要件がある場合は、プラン選択や設計に注意
- ストレージや認証など他サービスとの連携も容易だが、設計時にベストプラクティスを確認すること[^1_7][^1_11]

---

## まとめ

Azureのサーバーレスサービスを活用すれば、「必要な時だけ動作するWebサイト」を簡単かつ低コストで構築できます。
特に**Azure Static Web Apps**は、静的サイト＋APIを一体でサーバーレス運用したい場合に最適です。
要件に応じて、Azure FunctionsやApp Serviceのサーバーレスプランも検討しましょう。

---

**ご要望や今後の拡張性を踏まえ、最適なアーキテクチャ設計もご提案できますので、ぜひご相談ください。**

<div style="text-align: center">⁂</div>

[^1_1]: https://learn.microsoft.com/ja-jp/azure/architecture/web-apps/serverless/architectures/web-app

[^1_2]: https://zenn.dev/headwaters/articles/f343dbf79c8de9

[^1_3]: https://qiita.com/s-nagumo/items/f09b3c567050fc042634

[^1_4]: https://zenn.dev/falcode/books/f842a997cc4ae0/viewer/f4ddad

[^1_5]: https://jp.linkedin.com/learning/azure-functions-essential-training/2841228

[^1_6]: https://www.issoh.co.jp/tech/details/3175/

[^1_7]: https://qiita.com/TsuyoshiUshio@github/items/200abbd218c800136773

[^1_8]: https://zenn.dev/yamaday/articles/azure-static-web-apps-clarity

[^1_9]: https://learn.microsoft.com/ja-jp/azure/developer/javascript/how-to/with-web-app/static-web-app-with-swa-cli/introduction

[^1_10]: https://www.cloud-for-all.com/azure/blog/what-are-azure-functions

[^1_11]: https://esg.teldevice.co.jp/iot/azure/column/column37.html

[^1_12]: https://www.zead.co.jp/column/azure-app-service/

[^1_13]: https://ic-solution.jp/blog/serverless-appropriate

[^1_14]: https://learn.microsoft.com/ja-jp/azure/azure-functions/deployment-zip-push

[^1_15]: https://docs.github.com/ja/actions/use-cases-and-examples/deploying/deploying-to-azure-static-web-app

[^1_16]: https://www.cresco.co.jp/blog/entry/23364.html

[^1_17]: https://qiita.com/gsy0911/items/61198607476ac686ce6f

[^1_18]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/get-started-portal

[^1_19]: https://licensecounter.jp/azure/blog/ai/azureappservice-webapps.html

[^1_20]: https://zenn.dev/headwaters/articles/fd819f69c60270

[^1_21]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/getting-started

[^1_22]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/add-api

[^1_23]: https://licensecounter.jp/azure/blog/azure-basic-knowledge/azure-functions.html

[^1_24]: https://qiita.com/NovanMondon/items/b25ba54e0b7533e02219

[^1_25]: https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-deployment-technologies

[^1_26]: https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-bindings-event-hubs-trigger

[^1_27]: https://learn.microsoft.com/ja-jp/azure/app-service/manage-automatic-scaling

[^1_28]: https://www.rworks.jp/cloud/azure/azure-column/azure-entry/24384/

[^1_29]: https://qiita.com/komiyasa/items/c9c18e36d64d773276c3

[^1_30]: https://azure.microsoft.com/ja-jp/products/app-service/static

[^1_31]: https://www.techfirm.co.jp/blog/serverlessarchitecture

[^1_32]: https://azure.github.io/jpazpaas/2024/02/22/Azure-functions-trigger-and-binding-series-eventhubs.html

[^1_33]: https://learn.microsoft.com/ja-jp/shows/learn-tv-static-web-apps-code-to-scale/

[^1_34]: https://zenn.dev/ncdc/articles/20f9e92441b9e8

[^1_35]: https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-bindings-event-grid-trigger

[^1_36]: https://www.idaten.ne.jp/portal/page/out/secolumn/multicloud/column044.html

[^1_37]: https://qiita.com/yuhattor/items/f7b2aec5211951dd7622

[^1_38]: https://tech-blog.cloud-config.jp/2021-09-07-azure-functions-tips

[^1_39]: https://qiita.com/ussvgr/items/b5c827f9dc7ec145895f

[^1_40]: https://en-ambi.com/itcontents/entry/2019/11/19/103000/

[^1_41]: https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-best-practices

[^1_42]: https://qiita.com/hiro10149084/items/7300a2e74abd0083973e

[^1_43]: https://www.sigmact.com/updated/azure/security/

[^1_44]: https://zenn.dev/sakojun/articles/20210529-azure-functions

[^1_45]: https://withwonder.co.jp/blog/azure-static-web-apps-entra-id/

[^1_46]: https://qiita.com/takanorig/items/3a3a0b43b5be5b4a124f

[^1_47]: https://learn.microsoft.com/ja-jp/azure/azure-functions/storage-considerations

[^1_48]: https://www.rworks.jp/cloud/azure/azure-column/azure-entry/28706/

[^1_49]: https://payproglobal.com/ja/回答トピック/サーバーレスコンピューティング/

[^1_50]: https://www.rworks.jp/cloud/azure/azure-column/azure-entry/27492/

[^1_51]: https://business.ntt-east.co.jp/content/cloudsolution/column-414.html

[^1_52]: https://azure.microsoft.com/ja-jp/solutions/serverless

[^1_53]: https://learn.microsoft.com/ja-jp/azure/architecture/web-apps/

[^1_54]: https://learn.microsoft.com/ja-jp/azure/synapse-analytics/sql/best-practices-serverless-sql-pool


---

# さらに一歩進んだ提案内容も含んだ事例を詳細に教えてください。プログラムコード、Azureの設定手順なども含めて。実例となるサンプルコードがあると良いです。

AzureでサーバーレスWebアプリケーションを構築する高度な事例として、**Durable Functionsを活用した注文処理ワークフロー**と**Application Insightsによる監視**を統合したソリューションを紹介します。以下の実装例では、複雑なビジネスプロセスをサーバーレスで実現し、監視機能を組み込んだ包括的なアーキテクチャを示します。

### 高度なアーキテクチャ例

```
Azure Static Web Apps (Reactフロントエンド)
│
├── Azure Functions (API層)
│   └── Durable Functions Orchestrator
│       ├── ValidateOrderActivity
│       ├── CheckInventoryActivity
│       ├── ChargePaymentActivity
│       └── ShipOrderActivity
│
├── Azure Cosmos DB (注文データ永続化)
├── Service Bus (非同期メッセージング)
└── Application Insights (監視・トレーシング)
```


### 実装手順（C\# .NET 8）

#### 1. Durable Functionsプロジェクトの初期化

```bash
func init OrderProcessing --worker-runtime dotnet --model V3
cd OrderProcessing
func extensions install --package Microsoft.Azure.Functions.Extensions.DurableTask --version 2.9.6
```


#### 2. オーケストレーター関数の実装

```csharp
[FunctionName("OrderProcessingOrchestrator")]
public static async Task<OrderResult> RunOrchestrator(
    [OrchestrationTrigger] IDurableOrchestrationContext context)
{
    var order = context.GetInput<OrderDetails>();
    
    try
    {
        // 注文バリデーション
        order = await context.CallActivityWithRetryAsync<OrderDetails>(
            "ValidateOrderActivity",
            new RetryOptions(TimeSpan.FromSeconds(5), 3),
            order);

        // 在庫チェック
        var inventoryAvailable = await context.CallActivityAsync<bool>(
            "CheckInventoryActivity",
            order);

        if (!inventoryAvailable)
        {
            await context.CallActivityAsync("NotifyInventoryShortage", order);
            throw new InventoryException("在庫不足");
        }

        // 支払い処理
        var paymentSuccess = await context.CallActivityWithRetryAsync<bool>(
            "ChargePaymentActivity",
            new RetryOptions(TimeSpan.FromSeconds(10), 2),
            order);

        if (!paymentSuccess)
        {
            await context.CallActivityAsync("NotifyPaymentFailure", order);
            throw new PaymentException("支払い失敗");
        }

        // 出荷処理
        var trackingNumber = await context.CallActivityAsync<string>(
            "ShipOrderActivity",
            order);

        return new OrderResult
        {
            OrderId = order.OrderId,
            Status = "Completed",
            TrackingNumber = trackingNumber,
            Timestamp = context.CurrentUtcDateTime
        };
    }
    catch (Exception ex)
    {
        await context.CallActivityAsync("CompensateTransaction", order);
        throw;
    }
}
```


#### 3. Activity関数の実装例（在庫チェック）

```csharp
[FunctionName("CheckInventoryActivity")]
public static async Task<bool> CheckInventory(
    [ActivityTrigger] OrderDetails order,
    [CosmosDB(
        databaseName: "InventoryDB",
        collectionName: "Items",
        ConnectionStringSetting = "CosmosDBConnection")] CosmosClient client,
    ILogger log)
{
    var container = client.GetContainer("InventoryDB", "Items");
    var query = new QueryDefinition(
        "SELECT * FROM Items i WHERE i.productId = @productId")
        .WithParameter("@productId", order.ProductId);

    var iterator = container.GetItemQueryIterator<InventoryItem>(query);
    var result = await iterator.ReadNextAsync();

    return result.FirstOrDefault()?.Stock >= order.Quantity;
}
```


### Azureリソースのデプロイ（Bicepテンプレート）

```bicep
param location string = resourceGroup().location

// Application Insightsの作成
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'order-monitoring'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

// Azure Functionsの作成
resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: 'order-processing-func'
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AzureWebJobsStorage'
          value: storageAccount.properties.primaryEndpoints.blob
        }
      ]
    }
  }
}

// Static Web Appsの構成
resource staticWebApp 'Microsoft.Web/staticSites@2021-02-01' = {
  name: 'order-frontend'
  location: location
  properties: {
    repositoryUrl: 'https://github.com/contoso/order-frontend'
    branch: 'main'
    buildProperties: {
      appLocation: 'src'
      apiLocation: 'api'
    }
  }
}
```


### 監視設定（Application Insights Kustoクエリ）

```kusto
// 直近24時間のオーケストレーション実行状況
requests
| where timestamp > ago(24h)
| where operation_Name == "OrderProcessingOrchestrator"
| summarize 
    Total = count(),
    Success = countif(success == true),
    Failed = countif(success == false)
    by bin(timestamp, 1h)
| render timechart
```


### 高度なエラーハンドリングパターン

**補償トランザクションの実装**

```csharp
[FunctionName("CompensateTransaction")]
public static async Task Compensate(
    [ActivityTrigger] OrderDetails order,
    [ServiceBus("compensation-queue", Connection = "ServiceBusConnection")] IAsyncCollector<string> messages,
    ILogger log)
{
    // 支払いの返金処理
    if (order.PaymentProcessed)
    {
        await messages.AddAsync(JsonConvert.SerializeObject(new
        {
            OrderId = order.OrderId,
            Action = "RefundPayment",
            Amount = order.TotalAmount
        }));
    }

    // 在庫の返品処理
    if (order.InventoryReserved)
    {
        await messages.AddAsync(JsonConvert.SerializeObject(new
        {
            OrderId = order.OrderId,
            Action = "RestockInventory",
            ProductId = order.ProductId,
            Quantity = order.Quantity
        }));
    }
}
```

**タイムアウト処理の実装**

```csharp
var timeout = TimeSpan.FromMinutes(30);
var deadline = context.CurrentUtcDateTime.Add(timeout);

using (var cts = new CancellationTokenSource())
{
    var paymentTask = context.CallActivityAsync<bool>("ProcessPayment", order);
    var timeoutTask = context.CreateTimer(deadline, cts.Token);

    var winner = await Task.WhenAny(paymentTask, timeoutTask);
    if (winner == timeoutTask)
    {
        await context.CallActivityAsync("HandlePaymentTimeout", order);
        throw new TimeoutException("支払い処理がタイムアウトしました");
    }
    else
    {
        cts.Cancel();
        if (!await paymentTask)
        {
            throw new PaymentException("支払い処理に失敗しました");
        }
    }
}
```


### デプロイパイプライン（GitHub Actions）

```yaml
name: Deploy Order Processing

on:
  push:
    branches: [ main ]

jobs:
  deploy_frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_SWA_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          app_location: "src"
          api_location: "api"

  deploy_functions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: Azure/functions-action@v1
        with:
          app-name: 'order-processing-func'
          package: './OrderProcessing'
          publish-profile: ${{ secrets.AZURE_FUNCTION_PUBLISH_PROFILE }}
```

この構成により、以下の高度な機能を実現します：

1. **回復力のあるワークフロー**：自動リトライと補償トランザクション
2. **リアルタイム監視**：Application Insightsによるパフォーマンス追跡
3. **動的スケーリング**：需要に応じた自動スケーリング
4. **コスト最適化**：実際の使用量に基づく課金
5. **DevOps統合**：GitHub Actionsを使ったCI/CD

特に、Durable Functionsの**チェックポイント/リスタート機能**により、長時間実行プロセス中の障害発生時でも最後の正常な状態から処理を再開できます。Application Insightsとの統合で、オーケストレーションの各ステップの実行時間やリソース使用状況を詳細に分析可能です。

<div style="text-align: center">⁂</div>

[^2_1]: https://learn.microsoft.com/en-us/azure/static-web-apps/getting-started

[^2_2]: https://www.cmarix.com/blog/how-to-build-a-serverless-web-app-in-azure/

[^2_3]: https://learn.microsoft.com/en-us/azure/static-web-apps/functions-bring-your-own

[^2_4]: https://learn.microsoft.com/en-us/samples/azure-samples/durable-functions-order-processing/durable-func-order-processing/

[^2_5]: https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview

[^2_6]: https://johnnyreilly.com/application-insights-bicep-azure-static-web-apps

[^2_7]: https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview

[^2_8]: https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/durable-functions-overview

[^2_9]: https://blog.nashtechglobal.com/orchestrating-workflows-with-net-8-durable-functions/

[^2_10]: https://pisquare.fr/how-to-build-your-first-serverless-web-application-on-azure/

[^2_11]: https://learn.microsoft.com/en-us/azure/static-web-apps/add-api

[^2_12]: https://www.youtube.com/watch?v=MQdIiJh6AGc

[^2_13]: https://github.com/Azure-Samples/serverless-web-application

[^2_14]: https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions

[^2_15]: https://github.com/Azure-Samples/azure-search-static-web-app

[^2_16]: https://nordicapis.com/how-to-build-a-serverless-web-app-with-azure-functions-and-rapidapi/

[^2_17]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/add-api

[^2_18]: https://help.qlik.com/talend/en-US/api-portal-deployment-guide/Cloud/azure-static-web-apps-deployment

[^2_19]: https://www.tatvasoft.com/blog/serverless-web-application-in-azure/

[^2_20]: https://qiita.com/y__saito/items/7c78893eaf2af6ecd301

[^2_21]: https://www.youtube.com/watch?v=iE7HuRX_Da8

[^2_22]: https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/

[^2_23]: https://blog.xeynergy.com/mastering-workflows-with-azure-durable-functions-a-guide-to-simplicity-4ce097dbfd9b

[^2_24]: https://dev.to/azure/durable-functions-stateful-long-running-functions-in-serverless-part-i-5bm

[^2_25]: https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/durable-functions-isolated-create-first-csharp

[^2_26]: https://www.youtube.com/watch?v=-zsWfa4LfVY

[^2_27]: https://learn.microsoft.com/en-us/azure/azure-functions/durable/

[^2_28]: https://dev.to/florianlenz/azure-durable-task-scheduler-advantages-for-durable-functions-2944

[^2_29]: https://www.youtube.com/live/ttfSvYiS83A

[^2_30]: https://gotocph.com/2024/sessions/3234/azure-durable-functions-for-developers-developing-and-solving-complex-event-driven-workflows

[^2_31]: https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/azure-functions/monitor-functions.md

[^2_32]: https://learn.microsoft.com/en-us/azure/static-web-apps/monitor

[^2_33]: https://www.youtube.com/watch?v=-9unw5kfx_o

[^2_34]: https://www.site24x7.com/help/azure/functions.html

[^2_35]: https://www.isjw.uk/post/azure/static-webapp-monitoring/

[^2_36]: https://learn.microsoft.com/en-us/azure/azure-monitor/app/usage

[^2_37]: https://learn.microsoft.com/ja-jp/azure/azure-functions/configure-monitoring

[^2_38]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/monitor

[^2_39]: https://learn.microsoft.com/ja-jp/azure/azure-monitor/app/monitor-functions

[^2_40]: http://www.kentsu.website/ja/posts/2023/hugo_appinsights/

[^2_41]: https://docs.azure.cn/en-us/azure-functions/monitor-functions

[^2_42]: https://johnnyreilly.com/bicep-link-azure-application-insights-to-static-web-apps

[^2_43]: https://learn.microsoft.com/en-us/azure/static-web-apps/get-started-portal

[^2_44]: https://learn.microsoft.com/en-us/azure/static-web-apps/configuration

[^2_45]: https://github.com/microsoft/static-web-apps-examples

[^2_46]: https://learn.microsoft.com/en-us/azure/static-web-apps/build-configuration

[^2_47]: https://dev.to/jeptoo/building-your-first-static-web-app-on-azure-a-step-by-step-guide-35d3

[^2_48]: https://github.com/jochenvw/azure-durable-functions-examples

[^2_49]: https://github.com/sonusathyadas/azure-durable-functions-tutorial

[^2_50]: https://www.youtube.com/watch?v=dZsp18GZ16w

[^2_51]: https://techcommunity.microsoft.com/blog/appsonazureblog/azure-durable-functions-faas-for-stateful-logic-and-complex-workflows/4238858

[^2_52]: https://learn.microsoft.com/en-us/azure/app-service/monitor-app-service

[^2_53]: https://azure.microsoft.com/ja-jp/blog/optimize-your-apps-for-your-business-with-azure-application-insights/

[^2_54]: https://docs.datadoghq.com/serverless/azure_app_services/

[^2_55]: https://www.youtube.com/watch?v=A0jAeGf2zUQ

[^2_56]: https://turbo360.com/blog/azure-functions-monitoring

[^2_57]: https://turbo360.com/blog/how-to-configure-monitoring-and-alerts-for-azure-app-service


---

# 必要な時に使用できる、ツールを登録したWebサーバーをAzure StaticWebAppsに作成します。その環境構築の手順を、実例（コード）も有りで、詳細に統括的にわかりやすく整理して、まとめてください

Azure Static Web Appsを使用して「必要な時だけ動作するツール登録Webサーバー」を構築する手順を、実践的なコード例と共に詳細に解説します。以下の構成では、Reactフロントエンド＋Azure Functions API＋Cosmos DBの組み合わせで、完全サーバーレスな環境を実現します。

---

## 全体アーキテクチャ

```
Azure Static Web Apps (Reactフロントエンド)
│
├── Azure Functions (ツール登録API)
│   ├── HTTPトリガー関数
│   └── Cosmos DBバインディング
│
├── Azure Cosmos DB (ツールデータ保存)
└── Application Insights (監視)
```


---

## 環境構築手順

### 1. プロジェクト構造の初期化

```bash
# フロントエンド（React）の作成
npx create-react-app tool-registry-frontend --template typescript
cd tool-registry-frontend

# APIディレクトリの作成
mkdir api && cd api
func init --worker-runtime node --model V4
npm install @azure/cosmos
```


---

### 2. Azure Functions APIの実装（api/src/functions/tools.js）

```javascript
const { app } = require('@azure/functions');
const { CosmosClient } = require('@azure/cosmos');

const client = new CosmosClient(process.env.CosmosDB_connectionString);
const database = client.database('ToolDB');
const container = database.container('Tools');

app.http('tools', {
    methods: ['GET', 'POST'],
    authLevel: 'anonymous',
    handler: async (request, context) => {
        switch (request.method) {
            case 'GET':
                const { resources } = await container.items.readAll().fetchAll();
                return { jsonBody: resources };
                
            case 'POST':
                const tool = await request.json();
                const { resource } = await container.items.create(tool);
                return { 
                    status: 201,
                    jsonBody: resource 
                };
        }
    }
});
```


---

### 3. ローカル開発環境の設定（swa-cli.config.json）

```json
{
  "$schema": "https://aka.ms/azure/static-web-apps-cli/schema",
  "configurations": {
    "tool-registry": {
      "appLocation": "build",
      "apiLocation": "api",
      "outputLocation": "dist",
      "appBuildCommand": "npm run build",
      "apiBuildCommand": "npm run build --if-present",
      "appDevserverUrl": "http://localhost:3000",
      "env": {
        "CosmosDB_connectionString": "@CosmosDBConnection"
      }
    }
  }
}
```


---

### 4. フロントエンドからAPIを呼び出す実装（src/App.tsx）

```typescript
import { useEffect, useState } from 'react';

interface Tool {
  id: string;
  name: string;
  description: string;
}

function App() {
  const [tools, setTools] = useState<Tool[]>([]);

  useEffect(() => {
    fetch('/api/tools')
      .then(res => res.json())
      .then(data => setTools(data));
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    
    fetch('/api/tools', {
      method: 'POST',
      body: JSON.stringify({
        name: formData.get('name'),
        description: formData.get('description')
      })
    });
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input name="name" placeholder="Tool Name" />
        <textarea name="description" placeholder="Description" />
        <button type="submit">Register</button>
      </form>

      <div>
        {tools.map(tool => (
          <div key={tool.id}>
            <h3>{tool.name}</h3>
            <p>{tool.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```


---

## Azureリソースのデプロイ手順

### 1. リソースの作成（Azure CLI）

```bash
# リソースグループの作成
az group create --name ToolRegistry --location japaneast

# Cosmos DBのデプロイ
az cosmosdb create --name tool-db-$(date +%s) --resource-group ToolRegistry

# Static Web Appsのデプロイ
az staticwebapp create \
  --name tool-registry-app \
  --resource-group ToolRegistry \
  --source https://github.com/<your-repo> \
  --location japaneast \
  --branch main \
  --app-location "build" \
  --api-location "api"
```


---

### 2. 環境変数の設定

```bash
# Cosmos DB接続文字列の取得
COSMOS_CONNECTION=$(az cosmosdb keys list --name tool-db-123 --resource-group ToolRegistry --query primaryMasterKey -o tsv)

# Static Web Appsに設定
az staticwebapp appsettings set \
  --name tool-registry-app \
  --setting-names CosmosDB_connectionString=$COSMOS_CONNECTION
```


---

## 高度な構成

### 自動スケーリングの設定

```json
{
  "version": "2.0",
  "extensions": {
    "http": {
      "routePrefix": "api",
      "maxConcurrentRequests": 100,
      "dynamicThrottlesEnabled": true
    }
  }
}
```


### 監視設定（Application Insights）

```bash
# Application Insightsの作成
az monitor app-insights component create \
  --app tool-registry-insights \
  --location japaneast \
  --resource-group ToolRegistry

# インストルメンテーションキーの設定
az staticwebapp appsettings set \
  --name tool-registry-app \
  --setting-names APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=<your-key>"
```


---

## デプロイ自動化（GitHub Actions）

```yaml
name: Azure Static Web Apps CI/CD

on:
  push:
    branches: [main]

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build
          
      - name: Build API
        run: |
          cd api
          npm install
          npm run build
          
      - name: Deploy to Azure
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_SWA_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          app_location: "frontend/build"
          api_location: "api"
```


---

## 運用監視のためのKustoクエリ例

```kusto
requests
| where timestamp > ago(24h)
| where operation_Name == "tools"
| summarize 
    TotalRequests = count(),
    AverageDuration = avg(duration),
    ErrorCount = countif(success == false)
    by bin(timestamp, 1h)
| render timechart
```

この構成により、以下の特徴を実現できます：

- **完全サーバーレス**: アクセス時にのみリソースが起動
- **自動スケーリング**: トラフィックに応じた自動拡張
- **統合監視**: Application Insightsによるリアルタイム分析
- **CI/CD自動化**: GitHub Actionsを使用した継続的デプロイ

開発から本番環境までのフローをシームレスに構築でき、初期コストを抑えつつ大規模なスケーリングにも対応可能です。実際の運用では、Azure AD B2Cを統合した認証機能の追加や、Durable Functionsを活用したバッチ処理の実装など、要件に応じた拡張が可能です。

<div style="text-align: center">⁂</div>

[^3_1]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/getting-started

[^3_2]: https://qiita.com/i-chini-techoes/items/f94b2fc0dd0e5928a006

[^3_3]: https://learn.microsoft.com/en-us/azure/static-web-apps/get-started-portal

[^3_4]: https://learn.microsoft.com/en-us/azure/static-web-apps/add-api

[^3_5]: https://dev.to/gkarwchan/deploy-a-single-page-application-to-azure-static-website-using-cicd-and-cli-3o7b

[^3_6]: https://qiita.com/s-nagumo/items/f09b3c567050fc042634

[^3_7]: https://learn.microsoft.com/en-us/azure/static-web-apps/getting-started

[^3_8]: https://zenn.dev/supino0017/articles/3210acbb22544a

[^3_9]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/add-api

[^3_10]: https://learn.microsoft.com/en-us/azure/static-web-apps/getting-started

[^3_11]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/overview

[^3_12]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/configuration

[^3_13]: https://learn.microsoft.com/ja-jp/azure/developer/javascript/how-to/with-web-app/static-web-app-with-swa-cli/introduction

[^3_14]: https://learn.microsoft.com/en-us/azure/static-web-apps/get-started-portal

[^3_15]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/deploy-web-framework

[^3_16]: https://www.idaten.ne.jp/portal/page/out/secolumn/multicloud/column044.html

[^3_17]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/custom-domain

[^3_18]: https://learn.microsoft.com/en-us/azure/static-web-apps/configuration

[^3_19]: https://zenn.dev/drumath2237/articles/232753174cb952

[^3_20]: https://neon.tech/guides/azure-todo-static-web-app

[^3_21]: https://learn.microsoft.com/ja-jp/training/modules/publish-static-web-app-api-preview-url/

[^3_22]: https://qreat.tech/2895/

[^3_23]: https://docs.commercetools.com/merchant-center-customizations/deployment/azure-static-web-apps

[^3_24]: https://dev.to/jeptoo/building-your-first-static-web-app-on-azure-a-step-by-step-guide-35d3

[^3_25]: https://zenn.dev/tk_hamaguchi/articles/83ee81a896f401

[^3_26]: https://learn.microsoft.com/en-us/azure/static-web-apps/publish-bicep

[^3_27]: https://www.youtube.com/watch?v=jnwRpEM6GR8

[^3_28]: https://github.com/gbaeke/az-static-web-app

[^3_29]: https://qiita.com/s-nagumo/items/3eea64da5fdac0df7038

[^3_30]: https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/create-static-web-app

[^3_31]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/get-started-portal

[^3_32]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/local-development

[^3_33]: https://b3id.jp/portal/page/out/secolumn/multicloud/column041.html

[^3_34]: https://docs.github.com/en/enterprise-server@3.13/actions/use-cases-and-examples/deploying/deploying-to-azure-static-web-app

[^3_35]: https://github.com/microsoft/static-web-apps-examples

[^3_36]: https://learn.microsoft.com/en-us/azure/static-web-apps/deploy-web-framework

[^3_37]: https://github.com/bbachi/react-azure-static-web-app


---

## Azure Static Web AppsでCosmos DBを選択する主な理由

Azure Static Web AppsとCosmos DBの組み合わせが推奨される理由を、技術的観点から詳細に解説します。

---

### 1. **サーバーレスアーキテクチャの完全統合**

- **自動スケーリング**: Cosmos DBのサーバーレス容量モード（400 RU/s無料枠[^4_3][^4_7]）とStatic Web Appsのイベント駆動型スケーリングが連動
- **コールドスタート対策**: Cosmos DBの予約容量オプション（Autoscale）で初期遅延を最小化[^4_4][^4_8]
- **統合課金モデル**: 両サービスの従量課金が単一サブスクリプションで管理可能[^4_7][^4_8]

```bash
# Cosmos DBサーバーレスモード有効化（Azure CLI）
az cosmosdb update \
  --name <account-name> \
  --resource-group <resource-group> \
  --capabilities EnableServerless
```


---

### 2. **データ操作の効率化**

- **Schema-less設計**: 動的なデータ構造変更に対応（例：ツールメタデータの柔軟な拡張）[^4_3][^4_9]
- **多APIサポート**: MongoDB API（Mongoose連携[^4_1]）やSQL APIなど開発者のスキルに応じた選択
- **データAPIビルダー**: バックエンドコード不要でREST/GraphQLエンドポイント自動生成[^4_2][^4_9]

```javascript
// Mongooseスキーマ定義例（Cosmos DB連携）
const toolSchema = new mongoose.Schema({
  name: { type: String, required: true },
  category: { type: String, index: true },
  metadata: mongoose.Schema.Types.Mixed
});
```


---

### 3. **パフォーマンス最適化**

- **グローバル分散**: マルチリージョン配置で待ち時間5ms以下を実現[^4_4][^4_8]
- **自動インデックス管理**: クエリパターンに応じたインデックス自動生成[^4_4][^4_8]
- **統合CDNキャッシュ**: Static Web AppsのCDNとCosmos DBのグローバル分散が連動[^4_3][^4_6]

```kusto
// Application Insightsでのパフォーマンス分析
requests
| where cloud_RoleName == "tool-registry-api"
| summarize avg(duration) by name
| render barchart
```


---

### 4. **セキュリティ構成**

- **マネージドID認証**: Keyベース認証ではなくAzure AD統合認証[^4_9]
- **IPフィルタリング**: Static Web Apps専用ネットワークグループの自動許可[^4_2][^4_9]
- **RBAC統合**: ロールベースのデータアクセス制御（例：管理者/一般ユーザー権限分離）[^4_8][^4_9]

```json
// staticwebapp.database.config.json のセキュリティ設定例
{
  "entities": {
    "Tools": {
      "permissions": [
        {
          "role": "admin",
          "actions": ["*"]
        },
        {
          "role": "user",
          "actions": ["read"]
        }
      ]
    }
  }
}
```


---

### 5. **開発者体験の向上**

- **ローカルエミュレータ**: Cosmos DBエミュレータとStatic Web Apps CLIの連携[^4_2][^4_10]
- **CI/CD統合**: GitHub Actionsでのデプロイパイプライン自動構成[^4_6][^4_9]
- **スキーマ管理**: GraphQLスキーマファイル（.gql）によるデータモデル定義[^4_9][^4_10]

```yaml
# GitHub Actionsデプロイ設定例
- name: Configure Cosmos DB
  uses: azure/cli@v1
  with:
    inlineScript: |
      az cosmosdb sql container update \
        --account-name ${{ vars.COSMOS_ACCOUNT }} \
        --database-name ToolDB \
        --name Tools \
        --idx @indexing-policy.json
```


---

### 6. **コスト最適化戦略**

- **RU（Request Unit）管理**: クエリのコスト予測ツールと自動チューニング[^4_4][^4_8]
- **階層化ストレージ**: アクセス頻度に応じたホット/コールドデータ分割[^4_4][^4_8]
- **予約容量割引**: 継続利用時の最大65%コスト削減[^4_4][^4_8]

```bash
# クエリコスト分析（Cosmos DB Metrics）
az cosmosdb sql query throughput show \
  --account-name <account-name> \
  --database-name <database> \
  --container-name <container>
```


---

## 総合評価

| 評価項目 | Cosmos DB | 代替DB |
| :-- | :-- | :-- |
| スケーラビリティ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 開発速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| グローバル対応 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| コスト効率 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 監視機能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

Azure Static Web AppsとCosmos DBの組み合わせは、特に以下のケースで強みを発揮します：

- 予測不能なトラフィック変動があるアプリケーション
- マルチリージョン展開が必要なグローバルサービス
- 急速なプロトタイピングと頻繁なスキーマ変更が発生する開発プロジェクト

これらを実現する技術的基盤として、Cosmos DBのサーバーレスアーキテクチャとStatic Web Appsのイベント駆動モデルが緊密に連携しています[^4_1][^4_3][^4_7][^4_8]。

<div style="text-align: center">⁂</div>

[^4_1]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/add-mongoose

[^4_2]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/database-azure-cosmos-db

[^4_3]: https://jamstack.jp/blog/azure_payjp/

[^4_4]: https://tech-lab.sios.jp/archives/44424

[^4_5]: https://www.issoh.co.jp/tech/details/3175/

[^4_6]: https://github.com/zengeeks/b2c-swa-handson/blob/main/docs/setup-cosmos-db.md

[^4_7]: https://zenn.dev/ncdc/articles/20f9e92441b9e8

[^4_8]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/database-overview

[^4_9]: https://learn.microsoft.com/ja-jp/azure/static-web-apps/database-configuration

[^4_10]: https://qiita.com/s-nagumo/items/aad108e607be2297ad87

[^4_11]: https://qiita.com/takatoshiinaoka/items/fd7c0a4a53b4badd7c4f


---

# Cosmos DBの無料枠の特徴は

Azure Cosmos DBの無料枠（Free Tier）の主な特徴は以下の通りです。

---

### Cosmos DB無料枠の特徴

- **無期限で利用可能**
Free Tierは一時的な試用ではなく、アカウントの有効期間中ずっと無料枠が適用されます[^5_6]。
- **サブスクリプションごとに1アカウント**
無料枠はAzureサブスクリプションにつき1つのCosmos DBアカウントにのみ適用できます[^5_5]。
- **スループットとストレージの無料枠**
    - 400 RU/s（リクエストユニット/秒）または1000 RU/sのスループット（最新情報では1000 RU/sまで拡大されています）[^5_4][^5_8]。
    - 5GBまたは25GBのストレージ（最新情報では25GBまで拡大）[^5_4][^5_8]。
- **有償版と同等の機能**
無料枠内でも有償版と同じ機能・性能（SLA、グローバル分散、無制限ストレージ、API互換性など）を利用できます[^5_5]。
- **超過分のみ課金**
無料枠を超えた分だけ課金されます。枠内であれば完全無料です[^5_5]。
- **用途**
小規模な本番アプリや開発・検証用途、PoC（概念実証）などに最適です[^5_5][^5_6]。

---

### 最新の無料枠仕様（2025年4月時点）

| 項目 | 無料枠の内容 |
| :-- | :-- |
| スループット | 1000 RU/秒（以前は400 RU/秒） |
| ストレージ | 25GB（以前は5GBや50GBの場合も） |
| 利用可能数 | サブスクリプションごとに1アカウント |
| 利用期間 | 無期限 |
| 超過時 | 超過分のみ課金 |


---

### 注意点

- 無料枠は**最初に作成したCosmos DBアカウント**にのみ適用されるため、設計時に注意が必要です[^5_5][^5_1]。
- 無料枠の内容や適用条件は今後変更される可能性があるため、公式ドキュメントの最新情報を確認してください[^5_8]。

---

**まとめ**
Cosmos DBの無料枠は、サブスクリプションごとに1アカウント、1000 RU/s・25GBまで無期限で使える強力な特典です。小規模アプリや開発・テスト用途、本番利用でも十分活用できます[^5_5][^5_8][^5_4]。

<div style="text-align: center">⁂</div>

[^5_1]: https://qiita.com/ymasaoka/items/ffc3a44eef75bda5a502

[^5_2]: https://tech-blog.cloud-config.jp/2020-03-18-azure-cosmos-db-free-tier/

[^5_3]: https://www.ai-souken.com/article/azure-cosmos-db-overview

[^5_4]: https://qiita.com/i-chini-techoes/items/bf8a16b420571e825149

[^5_5]: https://k-miyake.github.io/blog/cosmos-free-tier-usecase/

[^5_6]: https://www.fenet.jp/infla/column/server/cosmos-dbって何？その特徴6つや他dbとの違いを解説/

[^5_7]: https://ascii.jp/elem/000/004/007/4007713/

[^5_8]: https://learn.microsoft.com/ja-jp/azure/cosmos-db/introduction

[^5_9]: https://www.kuix.co.jp/da-sys/?p=1529


---

# Kustoクエリとは？

Kustoクエリ（KQL: Kusto Query Language）とは、Azureの各種サービス（Azure Data Explorer、Azure Monitor、Log Analytics、Microsoft Sentinelなど）で利用される**データ分析専用のクエリ言語**です。
KQLは、構造化・半構造化・非構造化データに対して、**検索・集計・分析・パターン検出・異常検知**などを高速かつ柔軟に行うために設計されています[^6_1][^6_5][^6_2]。

---

## 主な特徴

- **読み取り専用**のクエリで、データの検索・分析・可視化に特化
- SQLに似た**テーブル・列・演算子**を使う直感的な構文
- **パイプ（|）演算子**で処理を連結し、データフロー型でクエリを記述
- **集計・フィルタ・時系列処理・文字列操作・グラフ化**など多彩な演算子・関数をサポート
- Azure Log AnalyticsやApplication Insightsなど、多くのAzureサービスで標準採用

---

## 基本的なクエリ例

```kusto
StormEvents
| where StartTime between (datetime(2007-11-01) .. datetime(2007-12-01))
| where State == "FLORIDA"
| count
```

この例では、`StormEvents`テーブルからフロリダ州で2007年11月〜12月に発生したイベントの件数を集計しています[^6_1][^6_5][^6_7]。

---

## 利用シーン

- システムやアプリの**ログ分析**
- **メトリックやテレメトリ**の可視化・異常検知
- **セキュリティイベント**の探索やパターン分析
- 大量データの**ダッシュボード化**

---

## まとめ

Kustoクエリは、Azureの各種データ分析サービスで標準的に使われる、**高速・高機能・直感的なクエリ言語**です。SQLに近い感覚で扱える一方、パイプライン型のデータ処理や高度な集計・分析も得意としています[^6_1][^6_2][^6_5]。

<div style="text-align: center">⁂</div>

[^6_1]: https://learn.microsoft.com/ja-jp/kusto/query/?view=microsoft-fabric

[^6_2]: https://qiita.com/YoshiakiOi/items/f2cb2b5626c2f7f71dba

[^6_3]: https://zenn.dev/e99h2121/articles/azure-kusto-first

[^6_4]: https://learn.microsoft.com/ja-jp/kusto/query/tutorials/learn-common-operators?view=microsoft-fabric

[^6_5]: https://learn.microsoft.com/ja-jp/azure/sentinel/kusto-overview

[^6_6]: https://learn.microsoft.com/ja-jp/training/modules/write-first-query-kusto-query-language/

[^6_7]: https://qiita.com/wf-kenji-ikeda/items/16345dfb37d1c296fcf4

[^6_8]: https://zenn.dev/choeurtap/articles/8f66691e51306f

[^6_9]: https://learn.microsoft.com/ja-jp/training/modules/explore-fundamentals-kql/

[^6_10]: https://learn.microsoft.com/ja-jp/kusto/query/datatypes-string-operators?view=microsoft-fabric

