# タスクリスト - 天気配信機能の実装

## 1. Domain Layer実装

### 1.1 Weather Value Object作成
- [ ] `app/domain/value_objects/weather.py` を作成
  - Weather dataclassを定義（max_temp, min_temp, pop）
  - frozen=Trueでイミュータブルにする
  - 型ヒントを適切に設定

### 1.2 WeatherCalculator Domain Service作成
- [ ] `app/domain/services/weather_calculator.py` を作成
  - `calculate_practical_weather()` メソッドを実装
  - hourlyデータからJST 9:00〜23:00を抽出
  - UTC → JST変換処理を実装
  - 最高気温・最低気温・降水確率を算出
  - Weatherオブジェクトを返却

### 1.3 UserRepository インターフェース拡張
- [ ] `app/domain/repositories/user_repository.py` に `get_all_users()` メソッドを追加
  - 戻り値の型: `list[User]`
  - docstringを記載

## 2. Infrastructure Layer実装

### 2.1 UserRepository実装拡張
- [ ] `app/infrastructure/dynamodb/user_repository.py` に `get_all_users()` メソッドを実装
  - DynamoDB Scan操作で全ユーザーを取得
  - Userエンティティのリストに変換
  - エラーハンドリングを実装

### 2.2 OpenWeatherMapClient作成
- [ ] `app/infrastructure/openweathermap/client.py` を作成
  - `get_hourly_weather(lat, lon)` メソッドを実装
  - One Call API 3.0エンドポイントを呼び出し
  - API Keyは環境変数またはSecrets Managerから取得
  - リトライ処理を実装（3回、指数バックオフ: 1秒、2秒、4秒）
  - エラーハンドリングを実装
  - レスポンスをパースしてhourlyデータを返却

### 2.3 LineMessagingClient作成
- [ ] `app/infrastructure/line/messaging_client.py` を作成
  - `push_message(user_id, message)` メソッドを実装
  - Push Message APIエンドポイントを呼び出し
  - Channel Access Tokenは環境変数またはSecrets Managerから取得
  - リトライ処理を実装（3回、指数バックオフ: 1秒、2秒、4秒）
  - エラーハンドリングを実装

## 3. Application Layer実装

### 3.1 BroadcastWeatherUseCase作成
- [ ] `app/usecases/broadcast_weather.py` を作成
  - クラス初期化（依存性注入: UserRepository, OpenWeatherMapClient, LineMessagingClient, WeatherCalculator）
  - `execute()` メソッドを実装:
    - 全ユーザーをDynamoDBから取得
    - 緯度経度でグルーピング（辞書: `{(lat, lon): [User, ...]}`）
    - グループごとに処理:
      - OpenWeatherMap APIで天気情報を取得
      - WeatherCalculatorで実質天気を算出
      - 該当ユーザー全員にメッセージを配信
    - 配信成功・失敗件数を集計
    - ログ出力（INFO: 開始・終了・件数、ERROR: 失敗）
  - エラーハンドリング（個別スキップ）を実装

## 4. Presentation Layer実装

### 4.1 Broadcast Handler作成
- [ ] `app/handlers/broadcast.py` を作成
  - `lambda_handler(event, context)` 関数を実装
  - 依存オブジェクトの初期化:
    - UserRepository
    - OpenWeatherMapClient
    - LineMessagingClient
    - WeatherCalculator
    - BroadcastWeatherUseCase
  - UseCaseの`execute()`を呼び出し
  - 全体のtry-catchでエラーハンドリング
  - ログ出力（開始・終了・エラー）

## 5. ユニットテスト実装

### 5.1 WeatherCalculator テスト
- [ ] `app/tests/domain/services/test_weather_calculator.py` を作成
  - 正常系: 9:00〜23:00のデータから正しく実質天気を算出
  - 境界値: 9:00ちょうど、23:00ちょうどのデータを含む
  - 異常系: データが空の場合のエラーハンドリング

### 5.2 OpenWeatherMapClient テスト
- [ ] `app/tests/infrastructure/openweathermap/test_client.py` を作成
  - モックを使用してAPI呼び出しをテスト
  - 正常系: レスポンスを正しくパース
  - 異常系: リトライ動作の確認
  - 異常系: エラー時の例外発生確認

### 5.3 LineMessagingClient テスト
- [ ] `app/tests/infrastructure/line/test_messaging_client.py` を作成
  - モックを使用してPush Message APIをテスト
  - 正常系: メッセージを正しく送信
  - 異常系: リトライ動作の確認
  - 異常系: エラー時の例外発生確認

### 5.4 BroadcastWeatherUseCase テスト
- [ ] `app/tests/usecases/test_broadcast_weather.py` を作成
  - モックを使用してユースケース全体をテスト
  - 正常系: 全ユーザーへの配信フロー
  - 正常系: 緯度経度グルーピングの動作確認
  - 異常系: 一部ユーザーのスキップ動作確認

### 5.5 Broadcast Handler テスト
- [ ] `app/tests/handlers/test_broadcast.py` を作成
  - モックを使用してハンドラをテスト
  - 正常系: EventBridgeイベントを受け取りユースケースを実行
  - 異常系: エラー発生時のハンドリング

## 6. Infrastructure (CDK) 実装

### 6.1 Lambda関数追加
- [ ] `cdk/lib/stack.ts` を修正
  - `weather-broadcast-handler` Lambda関数を追加
  - ランタイム: Python 3.12
  - タイムアウト: 300秒
  - メモリ: 512MB
  - 環境変数: USERS_TABLE_NAME, SECRETS_ARN
  - ハンドラ: `handlers/broadcast.lambda_handler`

### 6.2 EventBridge Rule追加
- [ ] `cdk/lib/stack.ts` を修正
  - EventBridge Ruleを追加
  - ルール名: weather-broadcast-schedule
  - cron式: `cron(0 0 * * ? *)`（UTC 0:00 = JST 9:00）
  - ターゲット: weather-broadcast-handler Lambda

### 6.3 IAMポリシー追加
- [ ] `cdk/lib/stack.ts` を修正
  - DynamoDB Scan権限を追加
  - Secrets Manager読み取り権限を追加
  - CloudWatch Logs書き込み権限を追加（自動付与されるが確認）

### 6.4 Secrets Manager設定確認
- [ ] 既存のSecrets Managerリソースを確認
  - LINE Channel Access Tokenが設定済みか確認
  - OpenWeatherMap API Keyが設定済みか確認
  - 未設定の場合は手動でSecretsを作成

## 7. 統合テスト

### 7.1 ローカルテスト（オプション）
- [ ] Lambda関数をローカルで実行してテスト
  - テスト用のEventBridgeイベントJSONを作成
  - AWS SAM CLIまたは直接Python実行でテスト
  - DynamoDBはローカルDBまたは実際のAWSリソースを使用

### 7.2 CDK Deploy
- [ ] CDKスタックをデプロイ
  - `cd cdk && npx cdk synth` でテンプレート確認
  - `npx cdk deploy` でデプロイ実行
  - デプロイ完了を確認

### 7.3 手動テスト
- [ ] EventBridgeルールを手動トリガーして動作確認
  - AWS ConsoleまたはCLIでルールを手動実行
  - CloudWatch Logsでログを確認
  - LINE通知が正しく送信されるか確認
  - エラーが発生していないか確認

### 7.4 スケジュール実行確認
- [ ] 翌日9:00に自動実行されるか確認
  - 9:00以降にCloudWatch Logsを確認
  - 配信成功件数・失敗件数を確認
  - ユーザーがLINEで通知を受信したか確認

## 8. ドキュメント更新

### 8.1 docs/ 影響確認
- [ ] 永続的ドキュメントへの影響を再確認
  - 今回の実装で既存設計との矛盾がないか確認
  - 必要に応じて`docs/`を更新（通常は不要）

### 8.2 .steering/ 更新
- [ ] `tasklist.md` のチェックボックスを更新
  - 完了したタスクにチェックを入れる
  - 進捗状況を記録

## 9. CI/CD確認

### 9.1 CI パイプライン確認
- [ ] Pull Request作成時にCIが実行されるか確認
  - lint-python（Ruff）
  - typecheck-python（mypy）
  - test-python（pytest）
  - lint-cdk（ESLint）
  - cdk-synth

### 9.2 Deploy パイプライン確認
- [ ] mainブランチマージ時にデプロイが実行されるか確認
  - GitHub Actionsのログを確認
  - CDK deployが成功したか確認

## 10. 完了条件

### 10.1 機能要件
- [ ] EventBridgeにより毎日9:00（JST）に自動実行される
- [ ] DynamoDBから全ユーザーが取得される
- [ ] 緯度経度でグルーピングされ、API呼び出しが最適化される
- [ ] OpenWeatherMap One Call API 3.0で天気情報が取得される
- [ ] 9:00〜23:00の実質天気が正しく算出される
- [ ] 各ユーザーにLINE Push Messageが配信される
- [ ] 配信メッセージが指定フォーマットで表示される

### 10.2 非機能要件
- [ ] 全ユーザーへの配信が9:30までに完了する
- [ ] エラー発生時に適切にリトライされる
- [ ] エラー時に個別スキップして処理が継続される
- [ ] CloudWatch Logsに詳細なログが出力される
- [ ] 配信成功・失敗件数が正しく集計される

### 10.3 品質要件
- [ ] 全ユニットテストがパスする
- [ ] 型チェック（mypy）がエラーなしでパスする
- [ ] Linter（Ruff）がエラーなしでパスする
- [ ] 手動テストで正常動作が確認される
- [ ] CI/CDパイプラインが正常に動作する

## タスク進捗

- **総タスク数**: 48
- **完了**: 0
- **残り**: 48
- **進捗率**: 0%
