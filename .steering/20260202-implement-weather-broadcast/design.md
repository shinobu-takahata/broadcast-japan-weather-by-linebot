# 設計書 - 天気配信機能の実装

## 1. 実装アプローチ

### 1.1 アーキテクチャ概要

レイヤードアーキテクチャに従い、以下の構成で実装する。

```
EventBridge
   │
   ▼
┌─────────────────────────────────────┐
│   Presentation Layer                │
│   handlers/broadcast.py             │
│   - EventBridgeイベント受信         │
│   - エラーハンドリング               │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│   Application Layer                 │
│   usecases/broadcast_weather.py     │
│   - ユーザー取得                     │
│   - 緯度経度グルーピング             │
│   - 天気情報取得                     │
│   - メッセージ配信                   │
└─────────────────────────────────────┘
   │
   ├─────────────────┬─────────────────┐
   ▼                 ▼                 ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Domain Layer │ │Domain Layer │ │Domain Layer │
│services/    │ │entities/    │ │value_objects│
│weather_     │ │user.py      │ │weather.py   │
│calculator.py│ │             │ │location.py  │
└─────────────┘ └─────────────┘ └─────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│   Infrastructure Layer              │
│   - dynamodb/user_repository.py     │
│   - openweathermap/client.py        │
│   - line/messaging_client.py        │
└─────────────────────────────────────┘
```

### 1.2 処理フロー

1. **EventBridge → Lambda起動**
   - cron式: `cron(0 0 * * ? *)` (UTC 0:00 = JST 9:00)
   - Lambda関数: `weather-broadcast-handler`

2. **全ユーザー取得**
   - `UserRepository.get_all_users()` を呼び出し
   - DynamoDB Scan操作で全ユーザーを取得

3. **緯度経度グルーピング**
   - `(lat, lon)` をキーとして辞書でグルーピング
   - 同じ緯度経度のユーザーをリストにまとめる

4. **天気情報取得と算出**
   - グループごとに OpenWeatherMap API を呼び出し
   - `WeatherCalculator.calculate_practical_weather()` で実質天気を算出

5. **メッセージ配信**
   - 各ユーザーに LINE Push Message を送信
   - エラー時は個別にスキップしてログ出力

## 2. 変更するコンポーネント

### 2.1 新規作成

#### Presentation Layer
| ファイル | 説明 |
|---------|------|
| `app/handlers/broadcast.py` | EventBridge トリガーによる配信処理のエントリポイント |

#### Application Layer
| ファイル | 説明 |
|---------|------|
| `app/usecases/broadcast_weather.py` | 天気配信ユースケース |

#### Domain Layer
| ファイル | 説明 |
|---------|------|
| `app/domain/services/weather_calculator.py` | 実質天気算出ロジック |
| `app/domain/value_objects/weather.py` | 天気情報Value Object |

#### Infrastructure Layer
| ファイル | 説明 |
|---------|------|
| `app/infrastructure/openweathermap/client.py` | OpenWeatherMap API クライアント（One Call API 3.0） |
| `app/infrastructure/line/messaging_client.py` | LINE Messaging API クライアント（Push Message） |

### 2.2 既存コンポーネント修正

#### Domain Layer
| ファイル | 変更内容 |
|---------|---------|
| `app/domain/repositories/user_repository.py` | `get_all_users()` メソッドを追加（インターフェース） |

#### Infrastructure Layer
| ファイル | 変更内容 |
|---------|---------|
| `app/infrastructure/dynamodb/user_repository.py` | `get_all_users()` メソッドを実装 |

### 2.3 IaC（CDK）修正

| ファイル | 変更内容 |
|---------|---------|
| `cdk/lib/stack.ts` | EventBridge Rule追加、Lambda関数追加、IAMポリシー追加 |

## 3. データ構造の変更

### 3.1 新規Value Object: Weather

天気情報を表すValue Object。

```python
@dataclass(frozen=True)
class Weather:
    """実質天気情報"""
    max_temp: float      # 最高気温（℃）
    min_temp: float      # 最低気温（℃）
    pop: int             # 降水確率（%）
```

### 3.2 既存Entity: User（変更なし）

ユーザー情報を表すEntity（既存）。

```python
@dataclass
class User:
    user_id: str
    location: Location
    city_name: str
    created_at: datetime
    updated_at: datetime
```

### 3.3 既存Value Object: Location（変更なし）

位置情報を表すValue Object（既存）。

```python
@dataclass(frozen=True)
class Location:
    lat: float
    lon: float
```

## 4. 影響範囲の分析

### 4.1 新規追加されるAWSリソース

| リソース | 詳細 |
|---------|------|
| Lambda関数 | `weather-broadcast-handler`（タイムアウト: 300秒、メモリ: 512MB） |
| EventBridge Rule | cron式で毎日UTC 0:00にトリガー |
| IAMポリシー | DynamoDB Scan権限、Secrets Manager読み取り権限 |
| CloudWatch Logs | Lambda関数のログ出力先 |

### 4.2 既存リソースへの影響

| リソース | 影響内容 |
|---------|---------|
| DynamoDB（Users テーブル） | Scan操作が追加される（読み取りキャパシティに影響） |
| Secrets Manager | OpenWeatherMap API Key、LINE Channel Access Token の読み取りが追加 |

### 4.3 外部APIへの影響

| API | 影響内容 |
|-----|---------|
| OpenWeatherMap API | One Call API 3.0の呼び出しが追加（1日1回 × ユニークな緯度経度数） |
| LINE Messaging API | Push Message APIの呼び出しが追加（1日1回 × ユーザー数） |

## 5. 主要コンポーネント設計

### 5.1 handlers/broadcast.py

**責務**: EventBridgeイベントを受け取り、配信ユースケースを実行する。

**主要処理**:
- イベント受信
- ユースケースの初期化と実行
- エラーハンドリング（全体のtry-catch）
- ログ出力（開始・終了・エラー）

### 5.2 usecases/broadcast_weather.py

**責務**: 天気配信のユースケースを実行する。

**主要処理**:
- DynamoDBから全ユーザーを取得
- 緯度経度でグルーピング
- 各グループごとに天気情報を取得
- WeatherCalculatorで実質天気を算出
- 各ユーザーにメッセージを配信
- 配信結果の集計とログ出力

**依存**:
- `UserRepository` (インターフェース)
- `OpenWeatherMapClient` (インターフェース)
- `LineMessagingClient` (インターフェース)
- `WeatherCalculator` (Domain Service)

### 5.3 domain/services/weather_calculator.py

**責務**: OpenWeatherMap APIのhourlyデータから実質天気を算出する。

**主要処理**:
- hourlyデータからJST 9:00〜23:00の範囲を抽出
- UTC → JST 変換
- 最高気温・最低気温・降水確率の算出
- Weatherオブジェクトの生成

**入力**: hourlyデータのリスト（dt、temp、pop）
**出力**: Weatherオブジェクト

### 5.4 infrastructure/openweathermap/client.py

**責務**: OpenWeatherMap One Call API 3.0を呼び出す。

**主要処理**:
- One Call API 3.0のエンドポイント呼び出し
- リトライ処理（3回、指数バックオフ）
- エラーハンドリング
- レスポンスのパース

**メソッド**:
- `get_hourly_weather(lat: float, lon: float) -> list[dict]`

### 5.5 infrastructure/line/messaging_client.py

**責務**: LINE Messaging APIを呼び出してPush Messageを送信する。

**主要処理**:
- Push Message APIのエンドポイント呼び出し
- メッセージフォーマット作成
- リトライ処理（3回、指数バックオフ）
- エラーハンドリング

**メソッド**:
- `push_message(user_id: str, message: str) -> None`

## 6. エラーハンドリング設計

### 6.1 エラー種別と対応

| エラー種別 | 対応 |
|-----------|------|
| DynamoDB Scanエラー | リトライ後、失敗時は処理中断してログ出力 |
| OpenWeatherMap APIエラー | リトライ後、失敗時は該当グループをスキップしてログ出力 |
| LINE APIエラー | リトライ後、失敗時は該当ユーザーをスキップしてログ出力 |
| 計算エラー | 該当ユーザーをスキップしてログ出力 |

### 6.2 リトライ戦略

**指数バックオフ**:
- 1回目のリトライ: 1秒待機
- 2回目のリトライ: 2秒待機
- 3回目のリトライ: 4秒待機
- 3回失敗したら諦めてログ出力

**適用対象**:
- OpenWeatherMap API呼び出し
- LINE API呼び出し
- DynamoDB操作

## 7. ログ出力設計

### 7.1 ログレベル

| レベル | 用途 |
|-------|------|
| INFO | 処理開始・終了、配信成功、件数情報 |
| WARNING | リトライ実行、ユーザースキップ |
| ERROR | API呼び出し失敗、処理中断 |

### 7.2 ログ出力項目

**処理開始時**:
- タイムスタンプ
- 処理開始メッセージ

**ユーザー取得後**:
- 取得したユーザー数
- ユニークな緯度経度数

**グループごとの処理**:
- 緯度経度
- 対象ユーザー数
- API呼び出し結果

**配信完了後**:
- 配信成功件数
- 配信失敗件数
- 処理終了時刻

**エラー発生時**:
- エラーメッセージ
- スタックトレース
- 対象ユーザーID

## 8. 設定値

### 8.1 Lambda関数設定

| 項目 | 値 |
|------|-----|
| 関数名 | weather-broadcast-handler |
| ランタイム | Python 3.12 |
| タイムアウト | 300秒 |
| メモリ | 512MB |
| 環境変数 | USERS_TABLE_NAME, SECRETS_ARN |

### 8.2 EventBridge設定

| 項目 | 値 |
|------|-----|
| ルール名 | weather-broadcast-schedule |
| cron式 | cron(0 0 * * ? *) |
| タイムゾーン | UTC |
| ターゲット | Lambda (weather-broadcast-handler) |

### 8.3 Secrets Manager

| シークレット名 | 格納内容 |
|--------------|---------|
| line-channel-access-token | LINE Channel Access Token |
| openweathermap-api-key | OpenWeatherMap API Key |

## 9. テスト方針

### 9.1 ユニットテスト

| コンポーネント | テスト内容 |
|--------------|-----------|
| WeatherCalculator | 実質天気算出ロジックの正確性 |
| OpenWeatherMapClient | API呼び出しとレスポンスパース（モック使用） |
| LineMessagingClient | メッセージ送信（モック使用） |
| BroadcastWeatherUseCase | ユースケース全体のフロー（モック使用） |

### 9.2 統合テスト

| テスト内容 | 確認項目 |
|-----------|---------|
| DynamoDB連携 | 全ユーザー取得の動作確認 |
| OpenWeatherMap API連携 | 実際のAPIレスポンスの処理確認 |
| LINE API連携 | Push Messageの送信確認 |

### 9.3 手動テスト

| テスト内容 | 確認項目 |
|-----------|---------|
| EventBridge手動実行 | スケジュール通りの実行確認 |
| エラーハンドリング | リトライ・スキップ動作の確認 |
| ログ出力 | CloudWatch Logsの内容確認 |

## 10. デプロイ計画

### 10.1 デプロイ順序

1. `cdk/lib/stack.ts` 修正（EventBridge、Lambda追加）
2. Pythonコード実装
3. ユニットテスト実装と実行
4. CDK deploy実行
5. 手動テスト実行（EventBridge手動トリガー）
6. 本番稼働確認

### 10.2 ロールバック計画

- CDK deployが失敗した場合、CloudFormationが自動ロールバック
- デプロイ後に問題が発生した場合、EventBridge Ruleを無効化
- 前のバージョンに戻す場合、Gitで前のコミットに戻してCDK deploy

## 11. docs/ への影響確認

### 11.1 影響のあるドキュメント

以下のドキュメントに今回の実装内容が既に記載されているため、更新は不要。

| ドキュメント | 既存記載内容 |
|------------|-------------|
| `docs/product-requirements.md` | F-002 天気配信機能が定義済み |
| `docs/functional-design/workflow.md` | 3. 天気配信フローが設計済み |
| `docs/functional-design/layered_architecture.md` | レイヤー構成が定義済み |
| `docs/functional-design/api_design.md` | One Call API 3.0、LINE Push Message APIが定義済み |
| `docs/infra-design/aws_infra.md` | Lambda関数、EventBridgeが設計済み |
| `docs/structure/repository-structure.md` | ディレクトリ構造が定義済み |

### 11.2 更新不要の理由

今回の実装は、既に `docs/` で定義されている設計に従って実装するため、永続的ドキュメントの更新は不要。
