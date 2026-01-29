# テーブル設計

## 1. テーブル一覧

| テーブル名 | 用途 |
|-----------|------|
| Users | ユーザー情報・地域設定を保存 |

## 2. Usersテーブル

### 2.1 概要

ユーザーのLINE IDと設定した地域の緯度経度を管理するテーブル。

### 2.2 テーブル定義

| 属性名 | 型 | 必須 | 説明 |
|--------|-----|------|------|
| userId | String | Yes | LINE User ID（Primary Key） |
| lat | Number | Yes | 緯度（OpenWeatherMap API用） |
| lon | Number | Yes | 経度（OpenWeatherMap API用） |
| cityName | String | Yes | 市区町村名（表示用） |
| createdAt | String | Yes | 登録日時（ISO 8601形式） |
| updatedAt | String | Yes | 更新日時（ISO 8601形式） |

### 2.3 キー設計

| キー種別 | 属性 |
|----------|------|
| Partition Key | userId |

### 2.4 サンプルデータ

```json
{
  "userId": "U1234567890abcdef",
  "lat": 35.6619,
  "lon": 139.7041,
  "cityName": "渋谷区",
  "createdAt": "2025-01-29T10:00:00Z",
  "updatedAt": "2025-01-29T10:00:00Z"
}
```

### 2.5 アクセスパターン

| 操作 | パターン | 使用キー |
|------|----------|----------|
| ユーザー情報取得 | GetItem | userId |
| ユーザー情報登録/更新 | PutItem | userId |
| 全ユーザー取得 | Scan | - |

### 2.6 キャパシティ設計

| 項目 | 設定 |
|------|------|
| 読み込みキャパシティ | オンデマンド |
| 書き込みキャパシティ | オンデマンド |

**理由**: ユーザー数が少ない初期段階ではオンデマンドが費用対効果が高い。
