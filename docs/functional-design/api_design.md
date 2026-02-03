# API設計書

## 1. エンドポイント一覧

### 1.1 内部API（API Gateway）

| メソッド | パス | 説明 |
|----------|------|------|
| POST | /webhook | LINE Webhook受信 |

### 1.2 外部API

| API | 用途 |
|-----|------|
| 国土地理院 Geocoding API | 市区町村名 → 緯度経度変換 |
| WeatherAPI Forecast API | 時間ごとの天気情報取得（気温） |
| 気象庁予報API | 降水確率取得 |
| LINE Messaging API | メッセージ送受信 |

## 2. 国土地理院 Geocoding API

市区町村名から緯度経度を取得する。

**エンドポイント**:
```
GET https://msearch.gsi.go.jp/address-search/AddressSearch?q={city}
```

**レスポンス例**:
```json
[
  {
    "geometry": { "coordinates": [139.7041, 35.6619] },
    "properties": { "title": "東京都渋谷区" }
  }
]
```

## 3. WeatherAPI Forecast API

緯度経度を指定して、1時間ごとの天気情報を取得する。

**エンドポイント**:
```
GET https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={lat},{lon}&days=1&lang=ja&aqi=no&alerts=no
```

**レスポンス例**:
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

**使用フィールド**:

| フィールド | 説明 |
|-----------|------|
| forecast.forecastday[0].hour[].time | ローカル時刻文字列（YYYY-MM-DD HH:MM） |
| forecast.forecastday[0].hour[].temp_c | 気温（摂氏） |

**気温の算出**:
- forecastday[0].hour配列から9:00〜23:00のデータを抽出
- 実質最高気温 = 抽出データのtemp_cの最大値
- 実質最低気温 = 抽出データのtemp_cの最小値

## 4. 気象庁予報API

降水確率を取得する。

**エンドポイント**:
```
GET https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json
```

**降水確率の算出**:
- 6時間ブロック（06:00, 12:00, 18:00）から9:00〜23:00に該当するものの最大値を使用

## 5. LINE Messaging API

### 5.1 Webhook

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

### 5.2 Reply Message API

Webhookへの応答としてメッセージを送信。

```
POST https://api.line.me/v2/bot/message/reply
Authorization: Bearer {Channel Access Token}
```

### 5.3 Push Message API

任意のタイミングでユーザーにメッセージを送信。

```
POST https://api.line.me/v2/bot/message/push
Authorization: Bearer {Channel Access Token}
```

## 6. API呼び出し制限

| API | 無料枠 |
|-----|--------|
| WeatherAPI | 1,000,000回/月 |
| LINE Messaging（フリープラン） | 200通/月 |
| LINE Messaging（ライトプラン） | 5,000通/月 |
