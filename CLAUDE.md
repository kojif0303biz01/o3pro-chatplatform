# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際のClaude Code (claude.ai/code)へのガイダンスを提供します。

## プロジェクト概要

- プロジェクトの主な目的と機能

- phase1
AzureのLLMモデルを使用するための、接続部分を作成し、基本的な部分や、モデルの使用方法を確認する。
o3-proの各モードを切り替えて使えるチャットボットを作成する。
チャット履歴も保存できるようにする。
次のPJで、チャット履歴は、AzureのDBに保存する。

- phase2
 チャットをStatic Web Appで作成する。
 azure container app+azure functionで作成し、チャット履歴は、conmosDBに保存する。

- phase3（進行中）
 Phase2で作成したチャットプラットフォームをAzure Container Apps環境（env-poc-apps）にデプロイする。
 FastAPI + Azure Functions統合によるマイクロサービス構成。
 CI/CDパイプライン（GitHub Actions）とコンテナ化による自動デプロイ体制確立。



- 主要なアーキテクチャの決定事項とパターン
AzureのLLMモデル、OpenAI,Azure Foundry,Azure project、Hubなど

- 重要な依存関係とその目的
python,static web app, azure functionなど

## 開発基本方針
- システムの効率的な開発、運用を重視する。
- オブジェクト＆機能モジュールは、出来るだけ汎用的に使えるようにし、ライブラリー化し再利用する。
- 運用する汎用モジュール、ライブラリーの管理も効率的に行えるように文書化、フォルダー配置を考慮する。
- AIやクラウドの最先端の技術を活用するが、汎用安定に稼働するものを使用する。
- アプリを構築する時、既存の作成した汎用モジュールを使い効率的に行う。
- アプリを構築する時、他のアプリに活用する可能性の強い機能は、汎用的なモジュールとして分離して構築する。
- coreフォルダーには、汎用モジュールを配置する。
- coreフォルダーの既存ファイルを変更する場合、そのファイルを使用しているファイルを確認し、事前に確認する事。

## 開発コマンド

### Container Apps デプロイ関連
- **GitHub Actions**: `git push origin containerization` でCI/CDパイプライン実行
- **サービスプリンシパル作成**: `./scripts/create-service-principal.sh`
- **ACRセットアップ**: `./infrastructure/scripts/setup-acr.sh`

### 開発環境
- ビルドコマンド: `docker-compose build`
- テストコマンド: （追加予定）
- リントコマンド: （追加予定）
- 実行/起動コマンド: `docker-compose up -d`

### 監視・デバッグ
- Container Appsログ: `az containerapp logs show --name o3pro-api --resource-group rg-poc-apps --follow`
- GitHub Actions認証デバッグ: ワークフローに組み込み済み

## プロジェクト構造

プロジェクト構造が発展するにつれて記載してください。すべてのファイルをリストするのではなく、高レベルの構成に焦点を当ててください。

## 主要なアーキテクチャの決定事項

### Phase 3: Container Apps移行の主要決定
1. **Azure Container Apps + Azure Functions統合アーキテクチャ採用**
   - コスト効率とスケーラビリティのバランス
   - マイクロサービス構成による保守性向上

2. **CI/CD戦略**
   - GitHub Actionsによる自動デプロイパイプライン
   - マルチステージDockerビルドによるイメージ最適化
   - デバッグ機能組み込みによる問題解決効率化

3. **セキュリティ設計**
   - 非rootユーザーでのコンテナ実行
   - Key Vault統合によるシークレット管理
   - 最小権限の原則（POC: min 0, max 1 replicas）

### 解決済み技術課題
- **GitHub Actions認証問題**: 環境変数参照エラーの修正
- **コンテナ化戦略**: マルチステージビルドとヘルスチェック実装
- **スケーリング設定**: POC環境向け最適化（0-1 replicas）

### 継続監視項目
- GitHub Actions認証安定性
- Container Apps パフォーマンス
- コスト効率の追跡