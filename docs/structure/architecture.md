# 技術仕様書（Architecture Document）

## 1. テクノロジースタック

### 1.1 アプリケーション（Lambda）

| 項目 | 技術 | バージョン |
|------|------|-----------|
| 言語 | Python | 3.12 |
| パッケージマネージャー | uv | - |
| フォーマッター/リンター | Ruff | - |
| 静的型チェッカー | mypy | - |

### 1.2 IaC（Infrastructure as Code）

| 項目 | 技術 | バージョン |
|------|------|-----------|
| IaCツール | AWS CDK | 2.x |
| 言語 | TypeScript | 5.x |
| ランタイム | Node.js | 20.x LTS |

### 1.3 AWSサービス

| サービス | 用途 |
|----------|------|
| Lambda | ビジネスロジック実行 |
| API Gateway | REST API エンドポイント |
| DynamoDB | データストア |
| EventBridge | スケジュール実行 |
| Secrets Manager | シークレット管理 |
| CloudWatch | ログ・監視 |

### 1.4 外部サービス

| サービス | 用途 |
|----------|------|
| LINE Messaging API | メッセージ送受信 |
| OpenWeatherMap API | 天気情報取得 |

## 2. 開発環境

### 2.1 devcontainer構成

CDK用とPythonアプリケーション用で分離。

| 環境 | ディレクトリ | 用途 |
|------|-------------|------|
| CDK | `cdk/.devcontainer/` | インフラ構築・デプロイ |
| Python | `app/.devcontainer/` | Lambda開発 |

### 2.2 CDK環境

| 項目 | 内容 |
|------|------|
| ベースイメージ | node:20-slim |
| AWS CLI | v2 |
| AWS CDK | グローバルインストール |
| VS Code拡張 | ESLint, Prettier, AWS Toolkit |

### 2.3 Python環境

| 項目 | 内容 |
|------|------|
| ベースイメージ | python:3.12-slim |
| パッケージマネージャー | uv |
| フォーマッター/リンター | Ruff |
| 静的型チェッカー | mypy |
| VS Code拡張 | Python, Pylance, Ruff, mypy Type Checker |

## 3. 非機能要件達成のためのコンポーネント設計

### 3.1 エラーハンドリング

#### リトライ戦略

| 処理 | リトライ回数 | 間隔 |
|------|-------------|------|
| OpenWeatherMap API | 3回 | 指数バックオフ（1秒、2秒、4秒） |
| LINE API | 3回 | 指数バックオフ（1秒、2秒、4秒） |
| DynamoDB | 3回 | 指数バックオフ |

#### エラー種別と対応

| エラー種別 | 対応 |
|-----------|------|
| Geocoding APIエラー | ユーザーにエラーメッセージを返信 |
| One Call APIエラー | リトライ後、失敗時はスキップしログ出力 |
| LINE APIエラー | リトライ後、失敗時はログ出力 |
| DynamoDBエラー | リトライ後、失敗時はアラート発報 |

### 3.2 セキュリティ

#### 認証・認可

| 項目 | 実装 |
|------|------|
| LINE Webhook検証 | X-Line-Signatureヘッダの署名検証 |
| API Gateway | パブリックエンドポイント（LINE専用） |

#### シークレット管理

| シークレット | 保管先 |
|-------------|--------|
| LINE Channel Secret | AWS Secrets Manager |
| LINE Channel Access Token | AWS Secrets Manager |
| OpenWeatherMap API Key | AWS Secrets Manager |

#### 通信セキュリティ

- 全通信はHTTPS
- Lambda実行ロールは最小権限の原則

### 3.3 監視・ログ

#### CloudWatch Logs

| Lambda | ログ内容 |
|--------|---------|
| line-webhook-handler | リクエスト受信、地域設定結果、エラー |
| weather-broadcast-handler | 配信開始/完了、配信件数、エラー |

#### アラート

| 条件 | アクション |
|------|----------|
| Lambda エラー率 > 5% | CloudWatch Alarm |
| 天気配信の失敗 | ログ出力 |
