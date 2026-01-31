# タスクリスト

## 1. タスク概要

地域設定フローのビジネスロジック実装を以下の順序で進める。依存関係を考慮し、内側のレイヤー（Domain Layer）から外側のレイヤー（Presentation Layer）へと実装していく。

## 2. 実装タスク

### フェーズ1: 環境準備

#### T-001: ディレクトリ構造の作成 ✅
- [x] `app/handlers/` ディレクトリを作成
- [x] `app/usecases/` ディレクトリを作成
- [x] `app/domain/entities/` ディレクトリを作成
- [x] `app/domain/value_objects/` ディレクトリを作成
- [x] `app/domain/repositories/` ディレクトリを作成
- [x] `app/infrastructure/dynamodb/` ディレクトリを作成
- [x] `app/infrastructure/openweathermap/` ディレクトリを作成
- [x] `app/infrastructure/line/` ディレクトリを作成
- [x] `app/utils/` ディレクトリを作成
- [x] 各ディレクトリに `__init__.py` を作成

**完了条件**: 全ディレクトリが存在し、Pythonパッケージとして認識される

---

#### T-002: 依存関係のインストール
- [ ] `app/requirements.txt` を作成
  - boto3（DynamoDB用）
  - requests（HTTP通信用）
  - python-dotenv（環境変数管理用、開発時のみ）
- [ ] `app/pyproject.toml` を作成（Ruff, mypy設定）
- [ ] `uv` で依存関係をインストール

**完了条件**: 必要なライブラリがインストールされている

---

### フェーズ2: Domain Layer実装

#### T-003: Location値オブジェクトの実装 ✅
- [x] `app/domain/value_objects/location.py` を作成
- [x] `Location` クラスを実装
  - `city_name: str`
  - `latitude: float`
  - `longitude: float`
- [x] `__post_init__` でバリデーション実装
  - 市区町村名が空でないこと
  - 緯度が -90〜90 の範囲内
  - 経度が -180〜180 の範囲内
- [x] frozen=True（イミュータブル）を設定

**完了条件**: Location値オブジェクトが正しくバリデーションされる

---

#### T-004: Userエンティティの実装 ✅
- [x] `app/domain/entities/user.py` を作成
- [x] `User` クラスを実装
  - `user_id: str`
  - `location: Location`
  - `created_at: datetime`
  - `updated_at: datetime`
- [x] `create()` 静的メソッドを実装（新規ユーザー作成）
- [x] `update_location()` メソッドを実装（地域更新）

**完了条件**: Userエンティティが正しく生成・更新できる

---

#### T-005: UserRepositoryインターフェースの実装 ✅
- [x] `app/domain/repositories/user_repository.py` を作成
- [x] `UserRepository` 抽象クラスを実装
  - `save(user: User) -> None` 抽象メソッド
  - `find_by_id(user_id: str) -> Optional[User]` 抽象メソッド

**完了条件**: インターフェースが定義されている

---

### フェーズ3: Infrastructure Layer実装

#### T-006: ユーティリティの実装

##### T-006-1: リトライデコレーターの実装 ✅
- [x] `app/utils/retry.py` を作成
- [x] `retry()` デコレーターを実装
  - max_attempts: 最大試行回数
  - backoff: リトライ間隔のリスト
  - 指数バックオフの実装
  - 最終試行で失敗時は例外をそのまま送出

**完了条件**: リトライデコレーターが正しく動作する

---

##### T-006-2: ロガーの実装 ✅
- [x] `app/utils/logger.py` を作成
- [x] `get_logger()` 関数を実装
- [x] `log_info()` 関数を実装（構造化ログ: JSON形式）
- [x] `log_error()` 関数を実装（構造化ログ: JSON形式）

**完了条件**: ロガーが構造化ログを出力できる

---

#### T-007: カスタム例外クラスの実装 ✅
- [x] `app/infrastructure/exceptions.py` を作成
- [x] `GeocodingNotFoundException` クラスを実装
- [x] `GeocodingAPIException` クラスを実装
- [x] `MessagingException` クラスを実装
- [x] `RepositoryException` クラスを実装

**完了条件**: カスタム例外が定義されている

---

#### T-008: GeocodingClientの実装 ✅
- [x] `app/infrastructure/openweathermap/client.py` に実装
- [x] `GeocodingClient` クラスを実装
  - `__init__(api_key: str)` コンストラクタ
  - `get_coordinates(city_name: str) -> tuple[float, float, str]` メソッド
- [x] Geocoding API呼び出し処理を実装
  - エンドポイント: `https://api.openweathermap.org/geo/1.0/direct`
  - パラメータ: `q={city_name},JP&limit=1&appid={api_key}`
- [x] `@retry` デコレーターを適用（3回、1秒/2秒/4秒）
- [x] エラーハンドリングを実装
  - レスポンスが空の場合: `GeocodingNotFoundException`
  - HTTPエラーの場合: `GeocodingAPIException`

**完了条件**: Geocoding APIから緯度経度を取得できる

---

#### T-009: LineMessagingClientの実装 ✅
- [x] `app/infrastructure/line/messaging_client.py` を作成
- [x] `LineMessagingClient` クラスを実装
  - `__init__(channel_access_token: str)` コンストラクタ
  - `reply_message(reply_token: str, text: str) -> None` メソッド
- [x] Reply Message API呼び出し処理を実装
  - エンドポイント: `https://api.line.me/v2/bot/message/reply`
  - ヘッダー: `Authorization: Bearer {channel_access_token}`
  - ボディ: `{"replyToken": "...", "messages": [{"type": "text", "text": "..."}]}`
- [x] `@retry` デコレーターを適用（3回、1秒/2秒/4秒）
- [x] エラーハンドリングを実装
  - HTTPエラーの場合: `MessagingException`

**完了条件**: LINE Reply Messageを送信できる

---

#### T-010: DynamoDBUserRepositoryの実装 ✅
- [x] `app/infrastructure/dynamodb/user_repository.py` を作成
- [x] `DynamoDBUserRepository` クラスを実装（UserRepositoryを継承）
  - `__init__(table_name: str)` コンストラクタ
  - `save(user: User) -> None` メソッド
  - `find_by_id(user_id: str) -> Optional[User]` メソッド
- [x] `save()` メソッドの実装
  - User → DynamoDB Item 変換
  - Decimal型への変換（lat, lon）
  - ISO 8601形式の日時文字列（createdAt, updatedAt）
  - `put_item()` で保存
  - `@retry` デコレーターを適用
- [x] `find_by_id()` メソッドの実装
  - `get_item()` でアイテム取得
  - DynamoDB Item → User変換
  - アイテムが存在しない場合は None を返す
- [x] `_to_entity()` プライベートメソッドの実装（Item → User変換）

**完了条件**: DynamoDBにユーザーデータを保存・取得できる

---

### フェーズ4: Application Layer実装

#### T-011: RegisterRegionUseCaseの実装 ✅
- [x] `app/usecases/register_region.py` を作成
- [x] `RegisterRegionUseCase` クラスを実装
  - `__init__(user_repository, geocoding_client, messaging_client)` コンストラクタ
  - `execute(user_id: str, city_name: str, reply_token: str) -> None` メソッド
- [x] `execute()` メソッドの処理フロー実装
  1. Geocoding APIで緯度経度を取得
  2. Location値オブジェクトを生成
  3. 既存ユーザーを取得（find_by_id）
  4. 既存ユーザーがいる場合: `update_location()`、いない場合: `User.create()`
  5. UserRepositoryで保存
  6. 成功メッセージを返信: `{city_name}の天気をお届けします`
- [x] エラーハンドリングを実装
  - `GeocodingNotFoundException`: 「申し訳ございません。{city_name}が見つかりませんでした。\n\n正しい市区町村名を入力してください。\n例: 渋谷区、新宿区、横浜市」
  - その他の例外: 「エラーが発生しました。しばらくしてからもう一度お試しください。」
- [x] ログ出力を実装
  - 処理開始時: user_id, city_name
  - 成功時: user_id, city_name, lat, lon
  - エラー時: user_id, city_name, error_message

**完了条件**: 地域設定ユースケースが正しく実行される

---

### フェーズ5: Presentation Layer実装

#### T-012: Webhook署名検証の実装 ✅
- [x] `app/handlers/webhook.py` を作成
- [x] `verify_signature(body: str, signature: str, channel_secret: str) -> bool` 関数を実装
  - HMAC-SHA256でハッシュ計算
  - Base64エンコード
  - 署名比較（timing-safe comparison）

**完了条件**: 署名検証が正しく動作する

---

#### T-013: Webhookハンドラーの実装 ✅
- [x] `handler(event: dict, context: Any) -> dict` 関数を実装
- [x] リクエストボディと署名の取得
  - `event['body']` からボディを取得
  - `event['headers']['x-line-signature']` から署名を取得
- [x] 環境変数からシークレット名取得 → Secrets Managerから値取得
  - `LINE_CHANNEL_SECRET_NAME`
  - `LINE_CHANNEL_ACCESS_TOKEN_NAME`
  - `OPENWEATHERMAP_API_KEY_NAME`
  - `TABLE_NAME`
- [x] 署名検証の実行
  - 失敗時: `{"statusCode": 401, "body": "Unauthorized"}` を返す
- [x] Webhookイベントのパース
  - JSON形式でパース
  - `events` 配列を取得
- [x] メッセージイベントの処理
  - イベントタイプが `message` かつメッセージタイプが `text` の場合
  - user_id, text, reply_token を抽出
  - RegisterRegionUseCaseを実行
- [x] レスポンス返却
  - `{"statusCode": 200, "body": "OK"}`
- [x] エラーハンドリング
  - 全ての例外をキャッチしてログ出力
  - `{"statusCode": 500, "body": "Internal Server Error"}` を返す

**完了条件**: Webhookハンドラーが正しく動作する

---

### フェーズ6: テスト実装

#### T-014: Domain Layerのユニットテスト ✅
- [x] `app/tests/domain/test_location.py` を作成
  - 正常系: 有効な緯度経度で生成
  - 異常系: 無効な緯度・経度でValueError
- [x] `app/tests/domain/test_user.py` を作成
  - 正常系: User.create()で新規ユーザー生成
  - 正常系: update_location()で地域更新

**完了条件**: Domain Layerのテストが通る

---

#### T-015: Application Layerのユニットテスト ✅
- [x] `app/tests/usecases/test_register_region.py` を作成
  - 正常系: 新規ユーザーの地域設定
  - 正常系: 既存ユーザーの地域更新
  - 異常系: 地名が見つからない場合
  - 異常系: 予期しないエラーの場合
- [x] モックを使用してRepository, GeocodingClient, MessagingClientをモック化

**完了条件**: Application Layerのテストが通る

---

#### T-016: Infrastructure Layerのユニットテスト ✅
- [x] `app/tests/infrastructure/test_geocoding_client.py` を作成
  - 正常系: 有効な地名で緯度経度取得
  - 正常系: local_namesがない場合のフォールバック
  - 異常系: 無効な地名でGeocodingNotFoundException
  - 異常系: HTTPエラーでGeocodingAPIException
  - モック: requestsライブラリをモック化
- [x] `app/tests/infrastructure/test_line_messaging_client.py` を作成
  - 正常系: Reply Message送信成功
  - 異常系: HTTPエラーでMessagingException
  - モック: requestsライブラリをモック化
- [x] `app/tests/infrastructure/test_dynamodb_user_repository.py` を作成
  - 正常系: save()でユーザー保存
  - 正常系: find_by_id()でユーザー取得
  - 異常系: find_by_id()でユーザーが存在しない場合はNone
  - モック: boto3をモック化

**完了条件**: Infrastructure Layerのテストが通る

---

#### T-017: Presentation Layerのユニットテスト ✅
- [x] `app/tests/handlers/test_webhook.py` を作成
  - 正常系: 有効な署名でWebhook処理（メッセージイベント）
  - 異常系: 無効な署名で401
  - モック: RegisterRegionUseCase, Secrets Manager等をモック化

**完了条件**: Presentation Layerのテストが通る


---

#### T-019: Lintと型チェック
- [ ] Ruffでコードフォーマット実行
  ```bash
  ruff format app/
  ```
- [ ] Ruffでlint実行
  ```bash
  ruff check app/
  ```
- [ ] mypyで型チェック実行
  ```bash
  mypy app/
  ```
- [ ] 全てのエラー・警告を修正

**完了条件**: Lint・型チェックがクリーンに通る

---

### フェーズ7: デプロイ準備

#### T-020: CDKスタックへの統合
- [ ] `cdk/lib/stack.ts` を確認
- [ ] Lambda関数（line-webhook-handler）が定義されているか確認
- [ ] 環境変数が正しく設定されているか確認
  - LINE_CHANNEL_SECRET（Secrets Manager）
  - LINE_CHANNEL_ACCESS_TOKEN（Secrets Manager）
  - OPENWEATHERMAP_API_KEY（Secrets Manager）
  - DYNAMODB_TABLE_NAME
- [ ] Lambda関数のIAMロールを確認
  - DynamoDB: GetItem, PutItem権限
  - Secrets Manager: GetSecretValue権限
  - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents権限

**完了条件**: CDKスタックが正しく設定されている

---

#### T-021: デプロイ
- [ ] CDKでデプロイ実行
  ```bash
  cd cdk
  cdk deploy
  ```
- [ ] デプロイ成功を確認
- [ ] API Gateway エンドポイントURLを取得
- [ ] LINE DevelopersコンソールでWebhook URLを設定

**完了条件**: AWSにデプロイされ、Webhook URLが設定されている

---


---

#### T-023: パフォーマンステスト
- [ ] CloudWatch Metricsでレスポンスタイムを確認
  - Lambda実行時間が3秒以内か
- [ ] CloudWatch Logsで各処理の所要時間を確認
  - Geocoding API呼び出し時間
  - DynamoDB保存時間
  - LINE Reply Message送信時間

**完了条件**: パフォーマンス目標（3秒以内）を達成している

---

#### T-024: エラー処理の検証
- [ ] Geocoding APIエラー時の動作確認（APIキーを一時的に無効化）
  - リトライが3回実行されるか
  - エラーメッセージが返信されるか
  - ログにエラーが出力されるか
- [ ] DynamoDBエラー時の動作確認（権限を一時的に削除）
  - リトライが3回実行されるか
  - エラーメッセージが返信されるか
  - ログにエラーが出力されるか

**完了条件**: エラーハンドリングが正しく動作する

---

## 3. タスクの依存関係

```
T-001 → T-002 → T-003 → T-004 → T-005
                   ↓       ↓       ↓
              T-006-1  T-006-2  T-007
                   ↓       ↓       ↓
              T-008   T-009   T-010
                   ↓       ↓       ↓
                      T-011
                        ↓
                   T-012 → T-013
                        ↓
              T-014 → T-015 → T-016 → T-017
                        ↓
                      T-018
                        ↓
                      T-019
                        ↓
                      T-020
                        ↓
                      T-021
                        ↓
                T-022 → T-023
```

## 4. 完了定義

### 全タスク完了条件
- [ ] 全てのタスクのチェックボックスが完了している
- [ ] 全てのユニットテストが通る
- [ ] Lint・型チェックがクリーンに通る
- [ ] ローカル統合テストが成功する
- [ ] 本番環境でE2Eテストが成功する
- [ ] パフォーマンス目標を達成している
- [ ] エラーハンドリングが正しく動作している
- [ ] CloudWatch Logsに構造化ログが出力されている

### 品質基準
- [ ] テストカバレッジ80%以上
- [ ] Domain Layerのテストカバレッジ100%
- [ ] レスポンスタイム3秒以内
- [ ] 署名検証が正しく動作
- [ ] リトライ処理が正しく動作

## 5. 推定工数

| フェーズ | 工数（時間） |
|---------|------------|
| フェーズ1: 環境準備 | 0.5 |
| フェーズ2: Domain Layer実装 | 2 |
| フェーズ3: Infrastructure Layer実装 | 4 |
| フェーズ4: Application Layer実装 | 2 |
| フェーズ5: Presentation Layer実装 | 2 |
| フェーズ6: テスト実装 | 4 |
| フェーズ7: デプロイ準備 | 1 |
| **合計** | **19.5時間** |
