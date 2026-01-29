# API設計書

## 1. エンドポイント一覧

### 1.1 内部API（API Gateway）

| メソッド | パス | 説明 |
|----------|------|------|
| POST | /webhook | LINE Webhook受信 |

### 1.2 外部API

| API | 用途 |
|-----|------|
| OpenWeatherMap Geocoding API | 市区町村名 → 緯度経度変換 |
| OpenWeatherMap One Call API 3.0 | 時間ごとの天気情報取得 |
| LINE Messaging API | メッセージ送受信 |

## 2. OpenWeatherMap Geocoding API

市区町村名から緯度経度を取得する。

**エンドポイント**:
```
GET https://api.openweathermap.org/geo/1.0/direct?q={city},JP&limit=1&appid={API_KEY}
```

**レスポンス例**:
```json
[
  {
    "name": "Shibuya",
    "local_names": { "ja": "渋谷区" },
    "lat": 35.6619,
    "lon": 139.7041,
    "country": "JP"
  }
]
```

## 3. OpenWeatherMap One Call API 3.0

緯度経度を指定して、1時間ごとの天気情報（48時間分）を取得する。

**エンドポイント**:
```
GET https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,alerts&units=metric&lang=ja&appid={API_KEY}
```

**レスポンス例**:
```json
{
  "hourly": [
    {
      "dt": 1706497200,
      "temp": 8.5,
      "pop": 0.2
    }
  ]
}
```

**使用フィールド**:

| フィールド | 説明 |
|-----------|------|
| hourly[].dt | Unix timestamp（UTC） |
| hourly[].temp | 気温（摂氏） |
| hourly[].pop | 降水確率（0〜1） |

**実質天気の算出**:
- hourly配列から9:00〜23:00（JST）のデータを抽出
- 実質最高気温 = 抽出データのtempの最大値
- 実質最低気温 = 抽出データのtempの最小値
- 実質降水確率 = 抽出データのpopの最大値 × 100

## 4. LINE Messaging API

### 4.1 Webhook

**リクエストヘッダ**:

| ヘッダ | 説明 |
|--------|------|
| X-Line-Signature | リクエストボディの署名（検証必須） |

**リクエストボディ例**:
```json
{
  "events": [
    {
      "type": "message",
      "replyToken": "xxx",
      "source": { "userId": "U1234..." },
      "message": { "type": "text", "text": "渋谷区" }
    }
  ]
}
```

### 4.2 Reply Message API

Webhookへの応答としてメッセージを送信。

```
POST https://api.line.me/v2/bot/message/reply
Authorization: Bearer {Channel Access Token}
```

### 4.3 Push Message API

任意のタイミングでユーザーにメッセージを送信。

```
POST https://api.line.me/v2/bot/message/push
Authorization: Bearer {Channel Access Token}
```

## 5. API呼び出し制限

| API | 無料枠 |
|-----|--------|
| OpenWeatherMap | 1,000回/日 |
| LINE Messaging（フリープラン） | 200通/月 |
| LINE Messaging（ライトプラン） | 5,000通/月 |
