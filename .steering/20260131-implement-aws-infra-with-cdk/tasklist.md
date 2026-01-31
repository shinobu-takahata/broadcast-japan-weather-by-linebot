# タスクリスト

## 1. 事前準備タスク

### T-001: CDKプロジェクトの初期設定確認
- [x] `cdk/package.json`に必要な依存関係が含まれているか確認
- [x] 不足している依存関係があれば追加
  - `source-map-support`を追加
  - CDK v2では`aws-cdk-lib`に全モジュールが含まれるため個別パッケージは不要
- [x] `cdk.json`の設定を確認
- [x] TypeScriptコンパイラ設定（`tsconfig.json`）を確認

**完了条件**:
- `npm install`が成功すること
- 必要なCDKライブラリがインストールされていること

---

## 2. Lambda関数ダミーコード作成

### T-002: Webhook処理Lambda用ダミーハンドラー作成
- [x] `cdk/lambda/webhook/`ディレクトリを作成
- [x] `cdk/lambda/webhook/index.py`を作成
  - 最小限のハンドラー関数を実装（ログ出力のみ）
  - イベントとコンテキストを受け取る
  - 200ステータスコードを返す
- [x] ダミーハンドラーが正しい構文であることを確認

**完了条件**:
- Pythonファイルが作成されていること
- 構文エラーがないこと

### T-003: 天気配信処理Lambda用ダミーハンドラー作成
- [x] `cdk/lambda/broadcast/`ディレクトリを作成
- [x] `cdk/lambda/broadcast/index.py`を作成
  - 最小限のハンドラー関数を実装（ログ出力のみ）
  - イベントとコンテキストを受け取る
  - 成功レスポンスを返す
- [x] ダミーハンドラーが正しい構文であることを確認

**完了条件**:
- Pythonファイルが作成されていること
- 構文エラーがないこと

---

## 3. CDKスタック実装

### T-004: CDKアプリケーションエントリポイント作成
- [x] `cdk/bin/app.ts`を作成
- [x] CDK Appインスタンスを初期化
- [x] `WeatherBroadcastStack`をインスタンス化
- [x] 環境設定（リージョン: ap-northeast-1）を指定
- [x] スタック名を`WeatherBroadcastStack`に設定

**完了条件**:
- `app.ts`が作成されていること
- TypeScriptコンパイルエラーがないこと

### T-005: DynamoDB Usersテーブルの実装
- [x] `cdk/lib/weather-broadcast-stack.ts`を作成
- [x] DynamoDB Tableリソースを定義
  - テーブル名: `WeatherBroadcast-Users`
  - Partition Key: `userId` (String)
  - Billing Mode: PAY_PER_REQUEST
  - Point-in-Time Recovery: 有効
  - Removal Policy: RETAIN（本番では削除保護）
- [x] テーブル参照を後続のリソースで使用できるよう変数に格納

**完了条件**:
- DynamoDBテーブルが定義されていること
- 設計書通りのパラメータが設定されていること

### T-006: Secrets Manager シークレットの実装
- [x] LINE Channel Secret用シークレットを定義
  - シークレット名: `line-channel-secret`
  - 説明: LINE Channel Secret for webhook verification
  - 初期値: 空のプレースホルダー
- [x] LINE Channel Access Token用シークレットを定義
  - シークレット名: `line-channel-access-token`
  - 説明: LINE Channel Access Token for messaging API
  - 初期値: 空のプレースホルダー
- [x] OpenWeatherMap API Key用シークレットを定義
  - シークレット名: `openweathermap-api-key`
  - 説明: OpenWeatherMap API Key for weather data
  - 初期値: 空のプレースホルダー
- [x] 各シークレットの参照を後続のリソースで使用できるよう変数に格納

**完了条件**:
- 3つのシークレットが定義されていること
- 設計書通りの名前と説明が設定されていること

### T-007: Webhook処理Lambda関数の実装
- [x] Lambda Functionリソースを定義
  - 関数名: `weather-broadcast-line-webhook-handler`
  - ランタイム: Python 3.12
  - ハンドラー: `index.handler`
  - コードパス: `cdk/lambda/webhook/`
  - タイムアウト: 30秒
  - メモリ: 256 MB
- [x] 環境変数を設定
  - `TABLE_NAME`: DynamoDBテーブル名
  - `LINE_CHANNEL_SECRET_NAME`: シークレット名
  - `LINE_CHANNEL_ACCESS_TOKEN_NAME`: シークレット名
  - `OPENWEATHERMAP_API_KEY_NAME`: シークレット名
- [x] IAM権限を付与
  - DynamoDB: ReadWriteData（Usersテーブルのみ）
  - Secrets Manager: GetSecretValue（3シークレットのみ）
- [x] CloudWatch Logsロググループを定義
  - ロググループ名: `/aws/lambda/weather-broadcast-line-webhook-handler`
  - 保持期間: 30日

**完了条件**:
- Lambda関数が定義されていること
- 設計書通りのパラメータが設定されていること
- 必要な権限が付与されていること

### T-008: 天気配信処理Lambda関数の実装
- [x] Lambda Functionリソースを定義
  - 関数名: `weather-broadcast-weather-broadcast-handler`
  - ランタイム: Python 3.12
  - ハンドラー: `index.handler`
  - コードパス: `cdk/lambda/broadcast/`
  - タイムアウト: 300秒
  - メモリ: 512 MB
- [x] 環境変数を設定
  - `TABLE_NAME`: DynamoDBテーブル名
  - `LINE_CHANNEL_ACCESS_TOKEN_NAME`: シークレット名
  - `OPENWEATHERMAP_API_KEY_NAME`: シークレット名
- [x] IAM権限を付与
  - DynamoDB: ReadData（Usersテーブルのみ）
  - Secrets Manager: GetSecretValue（2シークレットのみ）
- [x] CloudWatch Logsロググループを定義
  - ロググループ名: `/aws/lambda/weather-broadcast-weather-broadcast-handler`
  - 保持期間: 30日

**完了条件**:
- Lambda関数が定義されていること
- 設計書通りのパラメータが設定されていること
- 必要な権限が付与されていること

### T-009: API Gateway REST APIの実装
- [x] REST APIリソースを定義
  - API名: `weather-broadcast-webhook-api`
  - エンドポイントタイプ: Regional
  - デプロイステージ: prod
- [x] `/webhook`リソースを作成
- [x] POSTメソッドを追加
  - 統合タイプ: Lambda Proxy
  - 統合先: Webhook処理Lambda
- [x] Lambda呼び出し権限をAPI Gatewayに付与

**完了条件**:
- API Gatewayが定義されていること
- `/webhook`エンドポイントが作成されていること
- Lambda Proxy統合が設定されていること

### T-010: EventBridgeスケジュールルールの実装
- [x] EventBridge Ruleリソースを定義
  - ルール名: `weather-broadcast-schedule`
  - 説明: Trigger weather broadcast at 9:00 JST daily
  - スケジュール式: `cron(0 0 * * ? *)`
  - 状態: ENABLED
- [x] ターゲットを設定
  - ターゲット: 天気配信処理Lambda
- [x] Lambda呼び出し権限をEventBridgeに付与

**完了条件**:
- EventBridgeルールが定義されていること
- 設計書通りのcron式が設定されていること
- Lambda関数がターゲットに設定されていること

### T-011: スタック出力の定義
- [x] API GatewayエンドポイントURLを出力
  - 出力名: `WebhookApiUrl`
  - 説明: LINE Webhook URL
- [x] DynamoDBテーブル名を出力
  - 出力名: `UsersTableName`
  - 説明: Users table name

**完了条件**:
- スタック出力が定義されていること
- デプロイ後に必要な情報が表示されること

---

## 4. コード品質チェック

### T-012: Biomeによるlint・formatチェック
- [x] `cdk/`ディレクトリにBiomeを導入
- [x] `npx biome check`を実行
- [x] エラーがある場合は修正

**完了条件**:
- `npx biome check`がエラーなく完了すること

### T-013: TypeScriptコンパイルチェック
- [x] `cdk/`ディレクトリで`npm run build`を実行
- [x] コンパイルエラーがある場合は修正
- [x] 全てのコンパイルエラーが解消されていることを確認

**完了条件**:
- `npm run build`がエラーなく完了すること

### T-014: CDK Synthチェック
- [x] `npx cdk synth`を実行
- [x] CloudFormationテンプレートが正常に生成されることを確認
- [x] 生成されたテンプレートに全てのリソースが含まれていることを確認
  - DynamoDB Usersテーブル
  - Lambda関数 × 2
  - API Gateway
  - EventBridgeルール
  - Secrets Manager シークレット × 3
  - IAM Role × 2（Lambda用）
  - CloudWatch Logsロググループ × 2

**完了条件**:
- `cdk synth`がエラーなく完了すること
- 全てのリソースがテンプレートに含まれていること

---

## 5. デプロイと検証

### T-015: CDK Bootstrapの実行（初回のみ）
- [x] AWSアカウントとリージョンでCDK Bootstrapが実行済みか確認
- [x] 未実行の場合は`cdk bootstrap`を実行
- [x] Bootstrap Stackが正常に作成されたことを確認

**完了条件**:
- CDK Bootstrap Stackが存在すること
- S3バケット（CDK Asset用）が作成されていること

### T-016: スタックのデプロイ
- [x] `npx cdk deploy`を実行
- [x] デプロイ確認プロンプトで`y`を入力
- [x] デプロイが正常に完了することを確認
- [x] スタック出力からAPI GatewayエンドポイントURLを記録
  - `https://sgekf19vcd.execute-api.ap-northeast-1.amazonaws.com/prod/webhook`

**完了条件**:
- CloudFormation Stackが正常に作成されていること
- 全てのリソースがCREATE_COMPLETE状態であること

### T-017: DynamoDBテーブルの検証
- [x] AWSコンソールまたはCLIでUsersテーブルが作成されていることを確認
- [x] Partition Key（userId）が正しく設定されていることを確認
- [x] Billing ModeがPAY_PER_REQUESTであることを確認
- [x] Point-in-Time Recoveryが有効であることを確認

**完了条件**:
- DynamoDBテーブルが設計書通りに作成されていること

### T-018: Lambda関数の検証
- [x] AWSコンソールまたはCLIで2つのLambda関数が作成されていることを確認
- [x] Webhook処理Lambda:
  - ランタイムがPython 3.12であることを確認
  - タイムアウトが30秒であることを確認
  - メモリが256 MBであることを確認
  - 環境変数が正しく設定されていることを確認
- [x] 天気配信処理Lambda:
  - ランタイムがPython 3.12であることを確認
  - タイムアウトが300秒であることを確認
  - メモリが512 MBであることを確認
  - 環境変数が正しく設定されていることを確認
- [x] 各Lambda関数でテストイベントを実行し、正常に動作することを確認

**完了条件**:
- 2つのLambda関数が設計書通りに作成されていること
- テストイベントでダミーハンドラーが正常に実行されること

### T-019: API Gatewayの検証
- [x] AWSコンソールでREST APIが作成されていることを確認
- [x] `/webhook`リソースが存在することを確認
- [x] POSTメソッドが存在することを確認
- [x] Lambda Proxy統合が設定されていることを確認
- [ ] curlまたはPostmanで`POST /webhook`エンドポイントにテストリクエストを送信
- [ ] Lambda関数が呼び出され、レスポンスが返ってくることを確認

**完了条件**:
- API Gatewayが設計書通りに作成されていること
- テストリクエストで正常にレスポンスが返ること

### T-020: EventBridgeの検証
- [x] AWSコンソールでスケジュールルールが作成されていることを確認
- [x] cron式が`cron(0 0 * * ? *)`であることを確認
- [x] ルールが有効（ENABLED）であることを確認
- [x] ターゲットが天気配信処理Lambda関数であることを確認
- [ ] （オプション）テストイベントを手動で送信し、Lambda関数が起動することを確認

**完了条件**:
- EventBridgeルールが設計書通りに作成されていること
- Lambda関数がターゲットに正しく設定されていること

### T-021: Secrets Managerの検証
- [x] AWSコンソールで3つのシークレットが作成されていることを確認
  - `line-channel-secret`
  - `line-channel-access-token`
  - `openweathermap-api-key`
- [x] 各シークレットの説明が正しく設定されていることを確認
- [x] シークレット値を設定済み

**完了条件**:
- 3つのシークレットが作成されていること

### T-022: IAM権限の検証
- [x] Webhook処理Lambda関数のIAMロールを確認
  - DynamoDB ReadWriteData権限がUsersテーブルに対してのみ付与されていること
  - Secrets Manager GetSecretValue権限が3シークレットに対してのみ付与されていること
  - CloudWatch Logs書き込み権限が付与されていること（AWSLambdaBasicExecutionRole）
- [x] 天気配信処理Lambda関数のIAMロールを確認
  - DynamoDB ReadData権限がUsersテーブルに対してのみ付与されていること
  - Secrets Manager GetSecretValue権限が2シークレットに対してのみ付与されていること
  - CloudWatch Logs書き込み権限が付与されていること（AWSLambdaBasicExecutionRole）

**完了条件**:
- 各Lambda関数が必要最小限の権限のみを持っていること

### T-023: CloudWatch Logsの検証
- [x] AWSコンソールで2つのロググループが作成されていることを確認
  - `/aws/lambda/weather-broadcast-line-webhook-handler`
  - `/aws/lambda/weather-broadcast-weather-broadcast-handler`
- [x] 保持期間が30日に設定されていることを確認
- [x] テストイベント実行後、ログが出力されていることを確認

**完了条件**:
- 2つのロググループが作成されていること
- ログが正常に出力されていること

---

## 6. ドキュメント更新

### T-024: デプロイ結果の記録
- [x] スタック出力（API GatewayエンドポイントURL等）を記録
  - Webhook URL: `https://sgekf19vcd.execute-api.ap-northeast-1.amazonaws.com/prod/webhook`
  - Users Table: `WeatherBroadcast-Users`
- [x] デプロイ日時を記録: 2026-01-31
- [x] 使用したCDKバージョンを記録: AWS CDK v2

**完了条件**:
- デプロイ情報が記録されていること

### T-025: 次のステップの確認
- [x] Secrets Managerへの実際の値の設定が必要であることを確認 → 設定済み
- [x] Lambda関数の実際のビジネスロジック実装が別タスクであることを確認
- [x] LINE Webhook URLをLINE Developersコンソールに設定する必要があることを確認 → 設定済み

**完了条件**:
- 次に実施すべき作業が明確になっていること

---

## 完了条件（全体）

- [x] 全てのAWSリソースが設計書通りに作成されている
- [x] `cdk synth`がエラーなく実行できる
- [x] `cdk deploy`が正常に完了している
- [x] Biomeによるlint・formatエラーがない
- [x] 各Lambda関数のテストイベントが正常に実行できる
- [ ] API Gatewayエンドポイントにリクエストを送信できる（ビジネスロジック実装後に検証）
- [x] EventBridgeルールが有効化されている
- [x] Secrets Managerシークレットが作成されている（値も設定済み）
- [x] IAM権限が最小権限の原則に従っている
- [x] CloudWatch Logsにログが出力されている

---

## 備考

### Lambda関数のビジネスロジック実装について
本タスクではダミーハンドラーのみを実装します。実際のビジネスロジック（地域設定処理、天気情報取得、LINE API連携など）は別タスクで実装します。

### Secrets Managerの値設定について
デプロイ後、以下のコマンドまたはAWSコンソールで実際の値を設定してください：

```bash
# LINE Channel Secret
aws secretsmanager put-secret-value \
  --secret-id line-channel-secret \
  --secret-string "YOUR_CHANNEL_SECRET"

# LINE Channel Access Token
aws secretsmanager put-secret-value \
  --secret-id line-channel-access-token \
  --secret-string "YOUR_CHANNEL_ACCESS_TOKEN"

# OpenWeatherMap API Key
aws secretsmanager put-secret-value \
  --secret-id openweathermap-api-key \
  --secret-string "YOUR_API_KEY"
```

### LINE Webhook URL設定について
デプロイ後、スタック出力に表示されるAPI GatewayエンドポイントURLをLINE Developersコンソールに設定してください：

1. LINE Developersコンソールにログイン
2. 対象のチャネルを選択
3. Messaging API設定タブを開く
4. Webhook URLに`{API_GATEWAY_URL}/webhook`を設定
5. Webhookの利用を有効化
