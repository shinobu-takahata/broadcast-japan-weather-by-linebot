# タスクリスト: 天気API切り替え（OpenWeatherMap → WeatherAPI）

## タスク一覧

### 1. WeatherAPI クライアント新規作成
- [x] `app/infrastructure/weatherapi/__init__.py` を作成
- [x] `app/infrastructure/weatherapi/client.py` を作成
  - `WeatherApiClient` クラス実装
  - `get_hourly_weather(lat, lon)` メソッド実装
  - リトライ（3回、指数バックオフ）適用
  - レスポンスを `{"time": str, "temp": float}` 形式に正規化

### 2. WeatherCalculator のロジック変更
- [x] `app/domain/services/weather_calculator.py` を変更
  - 気温フィルタリングを Unix timestamp → `time` 文字列パースに変更
  - UTC→JST 変換ロジックを削除

### 3. ユースケース・ハンドラの依存関係変更
- [x] `app/usecases/broadcast_weather.py` の import・型ヒントを変更
- [x] `app/handlers/broadcast.py` の import・環境変数名・クライアント生成を変更

### 4. 例外クラスの更新
- [x] `app/infrastructure/exceptions.py` の `WeatherAPIException` docstring を更新

### 5. 旧 OpenWeatherMap 関連ファイルの削除
- [x] `app/infrastructure/openweathermap/client.py` を削除
- [x] `app/infrastructure/openweathermap/__init__.py` を削除

### 6. テストの更新
- [x] `app/tests/infrastructure/test_weatherapi_client.py` を新規作成
- [x] `app/tests/infrastructure/test_openweathermap_client.py` を削除
- [x] `app/tests/domain/test_weather_calculator.py` のテストデータ形式を変更

### 7. CDK スタックの変更
- [x] `cdk/lib/weather-broadcast-stack.ts` を変更
  - Secret 名を `weatherapi-api-key` に変更
  - 環境変数名を `WEATHERAPI_API_KEY_NAME` に変更

### 8. ドキュメント更新
- [x] `docs/functional-design/api_design.md` の OpenWeatherMap 記述を WeatherAPI に更新

### 9. テスト実行・動作確認
- [x] 全テストがパスすることを確認
