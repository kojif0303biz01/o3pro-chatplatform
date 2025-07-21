// Cosmos History モジュール用 Bicep テンプレート
// より簡潔で読みやすいAzureリソース定義

@description('Cosmos DB アカウント名（グローバルで一意）')
param cosmosAccountName string = 'cosmos-chat-${uniqueString(resourceGroup().id)}'

@description('リソースの場所')
param location string = resourceGroup().location

@description('データベース名')
param databaseName string = 'chat_history_db'

@description('会話コンテナー名')
param conversationsContainerName string = 'conversations'

@description('メッセージコンテナー名')
param messagesContainerName string = 'messages'

@description('容量モード')
@allowed(['Serverless', 'Provisioned'])
param capacityMode string = 'Serverless'

@description('プロビジョニング済みスループット（RU/s）')
@minValue(400)
@maxValue(1000000)
param throughput int = 400

@description('マルチリージョン書き込み有効化')
param enableMultipleWriteLocations bool = false

@description('自動フェールオーバー有効化')
param enableAutomaticFailover bool = false

@description('一貫性レベル')
@allowed(['Strong', 'Session', 'BoundedStaleness', 'ConsistentPrefix', 'Eventual'])
param consistencyLevel string = 'Session'

@description('境界のある陳腐化の最大プレフィックス')
param maxStalenessPrefix int = 100000

@description('境界のある陳腐化の最大間隔（秒）')
param maxIntervalInSeconds int = 300

// 一貫性ポリシー設定
var consistencyPolicies = {
  Strong: {
    defaultConsistencyLevel: 'Strong'
  }
  Session: {
    defaultConsistencyLevel: 'Session'
  }
  BoundedStaleness: {
    defaultConsistencyLevel: 'BoundedStaleness'
    maxStalenessPrefix: maxStalenessPrefix
    maxIntervalInSeconds: maxIntervalInSeconds
  }
  ConsistentPrefix: {
    defaultConsistencyLevel: 'ConsistentPrefix'
  }
  Eventual: {
    defaultConsistencyLevel: 'Eventual'
  }
}

// ロケーション設定
var locations = [
  {
    locationName: location
    failoverPriority: 0
    isZoneRedundant: false
  }
]

// Cosmos DB アカウント
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: consistencyPolicies[consistencyLevel]
    locations: locations
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: enableAutomaticFailover
    enableMultipleWriteLocations: enableMultipleWriteLocations
    capabilities: capacityMode == 'Serverless' ? [
      {
        name: 'EnableServerless'
      }
    ] : []
  }
}

// データベース
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    options: capacityMode == 'Provisioned' ? {
      throughput: throughput
    } : {}
  }
}

// 会話コンテナー
resource conversationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: conversationsContainerName
  properties: {
    resource: {
      id: conversationsContainerName
      partitionKey: {
        paths: ['/tenantId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          { path: '/tenantId/?' }
          { path: '/title/?' }
          { path: '/summary/?' }
          { path: '/participants/*/userId/?' }
          { path: '/participants/*/displayName/?' }
          { path: '/categories/*/categoryId/?' }
          { path: '/categories/*/categoryName/?' }
          { path: '/tags/*' }
          { path: '/timeline/lastMessageAt/?' }
          { path: '/timeline/createdAt/?' }
          { path: '/searchableText/?' }
          { path: '/status/?' }
          { path: '/archived/?' }
        ]
        excludedPaths: [
          { path: '/metrics/*' }
          { path: '/_etag/?' }
        ]
        compositeIndexes: [
          [
            { path: '/tenantId', order: 'ascending' }
            { path: '/timeline/lastMessageAt', order: 'descending' }
          ]
          [
            { path: '/tenantId', order: 'ascending' }
            { path: '/participants/0/userId', order: 'ascending' }
            { path: '/timeline/lastMessageAt', order: 'descending' }
          ]
          [
            { path: '/tenantId', order: 'ascending' }
            { path: '/categories/0/categoryId', order: 'ascending' }
            { path: '/timeline/lastMessageAt', order: 'descending' }
          ]
        ]
      }
    }
    options: capacityMode == 'Provisioned' ? {
      throughput: throughput / 2
    } : {}
  }
}

// メッセージコンテナー
resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: messagesContainerName
  properties: {
    resource: {
      id: messagesContainerName
      partitionKey: {
        paths: ['/conversationId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          { path: '/conversationId/?' }
          { path: '/tenantId/?' }
          { path: '/sender/userId/?' }
          { path: '/sender/role/?' }
          { path: '/timestamp/?' }
          { path: '/content/searchableText/?' }
          { path: '/metadata/mode/?' }
          { path: '/metadata/topics/*' }
          { path: '/sequenceNumber/?' }
        ]
        excludedPaths: [
          { path: '/content/originalText/?' }
          { path: '/metadata/duration/?' }
          { path: '/metadata/tokens/?' }
          { path: '/metadata/extractedEntities/*' }
        ]
        compositeIndexes: [
          [
            { path: '/conversationId', order: 'ascending' }
            { path: '/sequenceNumber', order: 'ascending' }
          ]
          [
            { path: '/conversationId', order: 'ascending' }
            { path: '/timestamp', order: 'ascending' }
          ]
          [
            { path: '/tenantId', order: 'ascending' }
            { path: '/timestamp', order: 'descending' }
          ]
        ]
      }
    }
    options: capacityMode == 'Provisioned' ? {
      throughput: throughput / 2
    } : {}
  }
}

// 出力
@description('Cosmos DB アカウント名')
output cosmosAccountName string = cosmosAccount.name

@description('Cosmos DB アカウントID')
output cosmosAccountId string = cosmosAccount.id

@description('Cosmos DB エンドポイント')
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint

@description('データベース名')
output databaseName string = database.name

@description('会話コンテナー名')
output conversationsContainerName string = conversationsContainer.name

@description('メッセージコンテナー名')
output messagesContainerName string = messagesContainer.name

@description('プライマリキー')
@secure()
output primaryKey string = cosmosAccount.listKeys().primaryMasterKey

@description('接続文字列')
@secure()
output connectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString