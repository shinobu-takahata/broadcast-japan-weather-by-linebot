# 要求定義書

## 1. 変更・追加する機能の説明

AWS CDKを使用して、日本全国の天気配信LINE BOTのインフラストラクチャをコードとして実装する。

### 1.1 背景
`docs/infra-design/`配下に定義されているAWS構成設計書、CI/CD設計書、テーブル設計書に基づき、実際のAWSリソースをCDKで構築する。これにより、インフラストラクチャのバージョン管理、再現性の確保、変更の追跡が可能になる。

### 1.2 実装対象のAWSリソース
以下のAWSリソースをCDKで定義・デプロイする：

- **DynamoDB**: Usersテーブル（ユーザー情報・地域設定を保存）
- **Lambda関数**:
  - `line-webhook-handler`: LINE Webhook処理（地域設定・設定確認）
  - `weather-broadcast-handler`: 天気配信処理
- **API Gateway**: LINE Webhookリクエストを受信するREST APIエンドポイント
- **EventBridge**: 毎日9:00（JST）に天気配信Lambdaをトリガーするスケジュールルール
- **Secrets Manager**: LINE Channel Secret、LINE Channel Access Token、OpenWeatherMap API Keyを安全に保管
- **CloudWatch Logs**: Lambda関数のログ出力先
- **IAM Role**: Lambda実行ロール（最小権限の原則に基づく）

## 2. 受け入れ条件

### AC-001: DynamoDBテーブル
- [ ] テーブル名は`Users`
- [ ] Partition Keyは`userId`（String型）
- [ ] 属性として`lat`（Number）、`lon`（Number）、`cityName`（String）、`createdAt`（String）、`updatedAt`（String）を保持
- [ ] オンデマンドキャパシティモードを使用
- [ ] ポイントインタイムリカバリ（PITR）が有効

### AC-002: Lambda関数（Webhook処理）
- [ ] 関数名は`line-webhook-handler`
- [ ] ランタイムはPython 3.12
- [ ] タイムアウトは30秒
- [ ] メモリは256MB
- [ ] API Gatewayからトリガーされる
- [ ] DynamoDBへの読み書き権限を持つ
- [ ] Secrets Managerへの読み取り権限を持つ
- [ ] CloudWatch Logsへの書き込み権限を持つ

### AC-003: Lambda関数（天気配信処理）
- [ ] 関数名は`weather-broadcast-handler`
- [ ] ランタイムはPython 3.12
- [ ] タイムアウトは300秒（5分）
- [ ] メモリは512MB
- [ ] EventBridgeからトリガーされる
- [ ] DynamoDBへの読み取り権限を持つ
- [ ] Secrets Managerへの読み取り権限を持つ
- [ ] CloudWatch Logsへの書き込み権限を持つ

### AC-004: API Gateway
- [ ] REST API形式
- [ ] エンドポイントは`POST /webhook`
- [ ] `line-webhook-handler` Lambdaと統合
- [ ] CORS設定なし（LINE Platformからのみアクセス）
- [ ] パブリックエンドポイント

### AC-005: EventBridge
- [ ] スケジュールルール名は`weather-broadcast-schedule`
- [ ] Cron式は`cron(0 0 * * ? *)`（UTC 0:00 = JST 9:00）
- [ ] ターゲットは`weather-broadcast-handler` Lambda

### AC-006: Secrets Manager
- [ ] 以下3つのシークレットを定義：
  - `line-channel-secret`
  - `line-channel-access-token`
  - `openweathermap-api-key`
- [ ] Lambda関数から読み取り可能
- [ ] 自動ローテーション設定なし（初期実装では手動管理）

### AC-007: IAMロール
- [ ] Lambda実行ロールは最小権限の原則に従う
- [ ] Webhook Lambdaは必要なリソースのみアクセス可能
- [ ] 配信Lambdaは必要なリソースのみアクセス可能

### AC-008: CDKコード品質
- [ ] TypeScriptで実装
- [ ] ESLintによるlintエラーなし
- [ ] `cdk synth`が正常に実行できる
- [ ] スタック名は`WeatherBroadcastStack`

## 3. 制約事項

### 3.1 技術的制約
- AWS CDK v2を使用
- TypeScript 5.xで実装
- Node.js 20.x LTS環境で動作
- Lambda関数のコードは`app/`ディレクトリを参照（本タスクではダミーハンドラーを使用）
- リージョンは`ap-northeast-1`（東京）

### 3.2 セキュリティ制約
- Secrets Managerのシークレット値は空で作成（実際の値は手動で設定）
- Lambda実行ロールは最小権限の原則に従う
- API GatewayエンドポイントはHTTPSのみ

### 3.3 コスト制約
- DynamoDBはオンデマンドキャパシティモード（初期段階のため）
- Lambda関数は必要最小限のメモリ設定
- CloudWatch Logsのログ保持期間は30日

### 3.4 運用制約
- シークレットの値は手動でAWSコンソールまたはCLIから設定
- 初回デプロイ時は`cdk bootstrap`が必要
- Lambda関数コードの実装は別タスク（本タスクではインフラのみ）

## 4. 対象外（スコープ外）

以下は本タスクの対象外とする：

- Lambda関数の実際のビジネスロジック実装（ダミーハンドラーのみ作成）
- GitHub Actions CI/CDワークフローの実装
- カスタムドメイン設定
- WAF設定
- 複数環境（dev/staging/production）の分離
- Lambda Layersの実装
- X-Rayトレーシングの有効化
- DynamoDB Global Tablesの設定
