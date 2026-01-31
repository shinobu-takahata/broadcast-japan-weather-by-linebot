# broadcast-japan-weather-by-linebot

日本全国の天気（09:00〜23:00までの最高気温、最低気温、降水確率）をLINEでお知らせするアプリケーション。

## 手動デプロイ手順

### 前提条件

- Docker / Docker Compose がインストール済み
- `~/.aws/credentials` にAWSプロファイルが設定済み

### 1. コンテナ起動

```bash
docker compose up -d cdk
```

### 2. 依存関係のインストール

```bash
docker compose exec -e AWS_PROFILE=takahata cdk npm install
```

### 3. CDK Bootstrap（初回のみ）

```bash
docker compose exec -e AWS_PROFILE=takahata cdk npx cdk bootstrap
```

### 4. デプロイ

```bash
docker compose exec -e AWS_PROFILE=takahata cdk npx cdk synth    # テンプレート生成確認
docker compose exec -e AWS_PROFILE=takahata cdk npx cdk deploy   # デプロイ実行
```

デプロイ完了後、スタック出力に `WebhookApiUrl` と `UsersTableName` が表示されます。

### 5. スタック削除（必要な場合）

```bash
docker compose exec -e AWS_PROFILE=takahata cdk npx cdk destroy
```

---

## Secrets Manager の設定手順

デプロイ後、以下の3つのシークレットに実際の値を設定する必要があります。

### 1. 各シークレットの値の取得先

| シークレット名 | 取得先 |
|---|---|
| `line-channel-secret` | [LINE Developers](https://developers.line.biz/) > 対象チャネル > チャネル基本設定 > チャネルシークレット |
| `line-channel-access-token` | [LINE Developers](https://developers.line.biz/) > 対象チャネル > Messaging API設定 > チャネルアクセストークン（長期） |
| `openweathermap-api-key` | [OpenWeatherMap](https://openweathermap.org/api) > My API Keys |

### 2. AWS CLI で設定

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

### 3. LINE Webhook URL の設定

1. [LINE Developers](https://developers.line.biz/) にログイン
2. 対象のチャネルを選択
3. Messaging API設定タブを開く
4. Webhook URLに `{デプロイ後に出力されるWebhookApiUrl}` を設定
5. Webhookの利用を有効化
