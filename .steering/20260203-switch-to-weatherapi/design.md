# 設計書: 天気API切り替え（OpenWeatherMap → WeatherAPI）

## 1. 実装アプローチ

OpenWeatherMap クライアントを WeatherAPI クライアントに置き換える。
WeatherAPI は1時間ごとの予報データを返すため、09:00〜23:00 のフィルタリングと気温算出に適している。

降水確率は JMA API を継続使用するため、WeatherCalculator の JMA 降水確率ロジックは変更しない。

## 2. 変更するコンポーネント

### 2.1 インフラ層: WeatherAPI クライアント（新規作成）

**ファイル**: `app/infrastructure/weatherapi/client.py`（新規）

OpenWeatherMap クライアントを削除し、WeatherAPI クライアントを新規作成する。

**WeatherAPI Forecast API 仕様**:
- エンドポイント: `GET https://api.weatherapi.com/v1/forecast.json`
- パラメータ:
  - `key`: APIキー
  - `q`: 緯度経度（`"{lat},{lon}"` 形式）
  - `days`: 予報日数（`1`）
  - `lang`: `ja`
  - `aqi`: `no`
  - `alerts`: `no`

**レスポンス構造**（使用するフィールドのみ）:
```json
{
  "forecast": {
    "forecastday": [
      {
        "hour": [
          {
            "time": "2026-02-03 09:00",
            "temp_c": 8.5
          }
        ]
      }
    ]
  }
}
```

**クライアントの責務**:
- WeatherAPI を呼び出し、`forecastday[0].hour` 配列を取得
- 各 hour エントリから `time`（ローカル時刻文字列）と `temp_c` を抽出
- WeatherCalculator が期待する形式 `{"time": str, "temp": float}` に正規化して返す

**クラス設計**:
```
class WeatherApiClient:
    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    def __init__(self, api_key: str) -> None

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_hourly_weather(self, lat: float, lon: float) -> list[dict]
```

**メソッドの戻り値形式**:
```python
[
    {"time": "2026-02-03 09:00", "temp": 8.5},
    {"time": "2026-02-03 10:00", "temp": 9.2},
    ...
]
```

### 2.2 ドメイン層: WeatherCalculator の変更

**ファイル**: `app/domain/services/weather_calculator.py`

**変更内容**: 気温フィルタリングのロジックを変更する。

- **現在**: Unix timestamp（`dt`）を UTC→JST 変換してフィルタリング
- **変更後**: WeatherAPI の `time` 文字列（`"YYYY-MM-DD HH:MM"` 形式）から時刻を抽出してフィルタリング

```
変更前: entry["dt"] → datetime.fromtimestamp(UTC) → JST変換 → hour抽出
変更後: entry["time"] → datetime.strptime → hour抽出
```

WeatherAPI の `time` フィールドはリクエスト地点のローカル時刻（日本の座標なので JST）が返されるため、UTC→JST 変換が不要になりシンプルになる。

降水確率の JMA ロジック部分は一切変更しない。

### 2.3 ユースケース層: BroadcastWeatherUseCase の変更

**ファイル**: `app/usecases/broadcast_weather.py`

**変更内容**:
- import を `OpenWeatherMapClient` → `WeatherApiClient` に変更
- コンストラクタの型ヒントを変更
- メソッド呼び出しのインターフェースは `get_hourly_weather(lat, lon)` で同一のため、呼び出し部分の変更は不要

### 2.4 プレゼンテーション層: ハンドラの変更

**ファイル**: `app/handlers/broadcast.py`

**変更内容**:
- import を `OpenWeatherMapClient` → `WeatherApiClient` に変更
- 環境変数名を `OPENWEATHERMAP_API_KEY_NAME` → `WEATHERAPI_API_KEY_NAME` に変更
- クライアント生成を `OpenWeatherMapClient(api_key)` → `WeatherApiClient(api_key)` に変更

### 2.5 インフラ: CDK スタックの変更

**ファイル**: `cdk/lib/weather-broadcast-stack.ts`

**変更内容**:
- Secrets Manager のリソース名を `openweathermap-api-key` → `weatherapi-api-key` に変更
- 変数名を `openWeatherMapApiKey` → `weatherApiKey` に変更
- Lambda 環境変数名を `OPENWEATHERMAP_API_KEY_NAME` → `WEATHERAPI_API_KEY_NAME` に変更

### 2.6 例外クラスの更新

**ファイル**: `app/infrastructure/exceptions.py`

**変更内容**:
- `WeatherAPIException` のdocstringを「OpenWeatherMap APIのエラー」から「WeatherAPI のエラー」に更新
- クラス名は汎用的なので変更不要

### 2.7 旧ファイルの削除

- `app/infrastructure/openweathermap/client.py` → 削除
- `app/infrastructure/openweathermap/__init__.py` → 削除
- `app/tests/infrastructure/test_openweathermap_client.py` → 削除

## 3. データ構造の変更

### WeatherCalculator の入力データ形式

| 項目 | 変更前（OpenWeatherMap） | 変更後（WeatherAPI） |
|------|------------------------|---------------------|
| 時刻 | `{"dt": 1706497200}` (Unix timestamp, UTC) | `{"time": "2026-02-03 09:00"}` (ローカル時刻文字列) |
| 気温 | `{"temp": 8.5}` | `{"temp": 8.5}` |
| フィルタ方式 | UTC→JST変換後にhour比較 | 文字列から直接hour抽出 |

### Weather バリューオブジェクト（変更なし）

`Weather(max_temp, min_temp, pop)` の構造は維持する。

## 4. 影響範囲の分析

| レイヤー | ファイル | 変更種別 |
|---------|---------|---------|
| インフラ | `infrastructure/weatherapi/client.py` | 新規作成 |
| インフラ | `infrastructure/weatherapi/__init__.py` | 新規作成 |
| インフラ | `infrastructure/openweathermap/` | 削除 |
| インフラ | `infrastructure/exceptions.py` | docstring修正 |
| ドメイン | `domain/services/weather_calculator.py` | ロジック変更 |
| ユースケース | `usecases/broadcast_weather.py` | import変更 |
| プレゼンテーション | `handlers/broadcast.py` | import・環境変数変更 |
| インフラ(CDK) | `cdk/lib/weather-broadcast-stack.ts` | Secret名・環境変数変更 |
| テスト | `tests/infrastructure/test_weatherapi_client.py` | 新規作成 |
| テスト | `tests/infrastructure/test_openweathermap_client.py` | 削除 |
| テスト | `tests/domain/test_weather_calculator.py` | テストデータ形式変更 |
| ドキュメント | `docs/functional-design/api_design.md` | API仕様更新 |

## 5. 影響しない範囲

- JMA 関連（`JmaForecastClient`, `JmaAreaMapper`）: 変更なし
- LINE Messaging 関連: 変更なし
- Weather バリューオブジェクト: 変更なし
- Location バリューオブジェクト: 変更なし
- User エンティティ・リポジトリ: 変更なし
- Geocoding クライアント: 変更なし
- メッセージテンプレート: 変更なし
