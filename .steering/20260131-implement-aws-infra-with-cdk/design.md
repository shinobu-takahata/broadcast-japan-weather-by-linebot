# 設計書

## 1. 実装アプローチ

### 1.1 基本方針
- AWS CDK v2をTypeScriptで実装
- 単一スタック構成（`WeatherBroadcastStack`）
- リソース名はハードコーディングせず、論理IDから自動生成またはプレフィックス付与
- 環境変数は`cdk.json`のcontextで管理
- Lambda関数コードは本タスクではダミー実装（`app/`ディレクトリの実装は別タスク）

### 1.2 デプロイ戦略
- 初回デプロイ前に`cdk bootstrap`を実行
- リージョンは`ap-northeast-1`（東京）
- AWSアカウントIDとリージョンは環境変数またはCDK Contextから取得

## 2. 変更するコンポーネント

本タスクで作成・変更するファイル：

```
cdk/
├── bin/
│   └── app.ts                    # 新規作成: CDKアプリケーションエントリポイント
├── lib/
│   └── weather-broadcast-stack.ts # 新規作成: メインスタック定義
├── cdk.json                      # 既存ファイル修正: Context設定追加
└── package.json                  # 既存ファイル確認: 必要な依存関係の確認
```

## 3. AWSリソース設計

### 3.1 DynamoDB テーブル

#### テーブル名
- 論理ID: `UsersTable`
- 物理名: `WeatherBroadcast-Users`（プレフィックス付与）

#### キー設計
| キー種別 | 属性名 | 型 |
|---------|--------|-----|
| Partition Key | userId | String |

#### 属性定義
テーブル作成時に定義する属性（キー属性のみ）：
- `userId` (String): LINE User ID

その他の属性（スキーマレス）：
- `lat` (Number): 緯度
- `lon` (Number): 経度
- `cityName` (String): 市区町村名
- `createdAt` (String): 登録日時（ISO 8601形式）
- `updatedAt` (String): 更新日時（ISO 8601形式）

#### キャパシティ設定
| パラメータ | 値 |
|-----------|-----|
| Billing Mode | PAY_PER_REQUEST（オンデマンド） |
| Read Capacity Units | 自動スケーリング |
| Write Capacity Units | 自動スケーリング |

#### バックアップ・復旧設定
| パラメータ | 値 |
|-----------|-----|
| Point-in-Time Recovery (PITR) | 有効 |
| Deletion Protection | 無効（開発段階のため） |

#### その他設定
| パラメータ | 値 |
|-----------|-----|
| Encryption | AWS管理のキー（デフォルト） |
| Table Class | Standard |
| Stream | 無効 |

### 3.2 Lambda 関数（Webhook処理）

#### 基本設定
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `LineWebhookHandler` |
| 関数名 | `weather-broadcast-line-webhook-handler` |
| ランタイム | Python 3.12 |
| ハンドラー | `webhook.handler`（ダミー実装） |
| タイムアウト | 30秒 |
| メモリ | 256 MB |
| アーキテクチャ | x86_64 |

#### コード設定
| パラメータ | 値 |
|-----------|-----|
| コードソース | インラインダミーコード（本タスクでは動作確認用の最小実装） |
| 実際のコードパス | `app/handlers/webhook.py`（別タスクで実装） |

#### 環境変数
| 変数名 | 値 | 説明 |
|--------|-----|------|
| TABLE_NAME | DynamoDBテーブル名（参照） | Usersテーブル名 |
| LINE_CHANNEL_SECRET_NAME | `line-channel-secret` | Secrets Manager シークレット名 |
| LINE_CHANNEL_ACCESS_TOKEN_NAME | `line-channel-access-token` | Secrets Manager シークレット名 |
| OPENWEATHERMAP_API_KEY_NAME | `openweathermap-api-key` | Secrets Manager シークレット名 |

#### IAMロール権限
必要な権限：
- DynamoDB: `GetItem`, `PutItem`（Usersテーブルのみ）
- Secrets Manager: `GetSecretValue`（3つのシークレットのみ）
- CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`

#### トリガー
- API Gateway（REST API）の`POST /webhook`エンドポイント

#### その他設定
| パラメータ | 値 |
|-----------|-----|
| Reserved Concurrency | 未設定（デフォルト） |
| Provisioned Concurrency | 未設定 |
| Ephemeral Storage | 512 MB（デフォルト） |

### 3.3 Lambda 関数（天気配信処理）

#### 基本設定
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `WeatherBroadcastHandler` |
| 関数名 | `weather-broadcast-weather-broadcast-handler` |
| ランタイム | Python 3.12 |
| ハンドラー | `broadcast.handler`（ダミー実装） |
| タイムアウト | 300秒（5分） |
| メモリ | 512 MB |
| アーキテクチャ | x86_64 |

#### コード設定
| パラメータ | 値 |
|-----------|-----|
| コードソース | インラインダミーコード（本タスクでは動作確認用の最小実装） |
| 実際のコードパス | `app/handlers/broadcast.py`（別タスクで実装） |

#### 環境変数
| 変数名 | 値 | 説明 |
|--------|-----|------|
| TABLE_NAME | DynamoDBテーブル名（参照） | Usersテーブル名 |
| LINE_CHANNEL_ACCESS_TOKEN_NAME | `line-channel-access-token` | Secrets Manager シークレット名 |
| OPENWEATHERMAP_API_KEY_NAME | `openweathermap-api-key` | Secrets Manager シークレット名 |

#### IAMロール権限
必要な権限：
- DynamoDB: `Scan`（Usersテーブルのみ）
- Secrets Manager: `GetSecretValue`（2つのシークレットのみ）
- CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`

#### トリガー
- EventBridgeスケジュールルール

#### その他設定
| パラメータ | 値 |
|-----------|-----|
| Reserved Concurrency | 未設定（デフォルト） |
| Provisioned Concurrency | 未設定 |
| Ephemeral Storage | 512 MB（デフォルト） |

### 3.4 API Gateway

#### API設定
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `WebhookApi` |
| API名 | `weather-broadcast-webhook-api` |
| タイプ | REST API |
| エンドポイントタイプ | Regional |
| Deploy | 自動デプロイ（prodステージ） |

#### リソース・メソッド設定
| パス | メソッド | 統合タイプ | 統合先 |
|------|---------|-----------|--------|
| /webhook | POST | Lambda Proxy統合 | `LineWebhookHandler` Lambda |

#### CORS設定
| パラメータ | 値 |
|-----------|-----|
| CORS | 無効（LINE Platformからのみアクセス） |

#### レスポンス設定
- Lambda Proxy統合のため、Lambdaが全てのレスポンスを制御

#### その他設定
| パラメータ | 値 |
|-----------|-----|
| API Key Required | 無効（LINE署名検証を使用） |
| Throttling | デフォルト設定 |
| CloudWatch Logging | エラーログのみ |

### 3.5 EventBridge スケジュールルール

#### ルール設定
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `WeatherBroadcastSchedule` |
| ルール名 | `weather-broadcast-schedule` |
| 説明 | `Trigger weather broadcast at 9:00 JST daily` |
| スケジュール式 | `cron(0 0 * * ? *)` |
| タイムゾーン | UTC（cron式がUTC 0:00 = JST 9:00） |
| 状態 | ENABLED |

#### ターゲット設定
| パラメータ | 値 |
|-----------|-----|
| ターゲット | `WeatherBroadcastHandler` Lambda |
| Input | デフォルト（イベント情報をそのまま渡す） |
| Retry Policy | デフォルト（最大2回リトライ） |

### 3.6 Secrets Manager

#### シークレット1: LINE Channel Secret
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `LineChannelSecret` |
| シークレット名 | `line-channel-secret` |
| 説明 | `LINE Channel Secret for webhook verification` |
| シークレット値 | 空文字列（手動で設定） |
| 自動ローテーション | 無効 |

#### シークレット2: LINE Channel Access Token
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `LineChannelAccessToken` |
| シークレット名 | `line-channel-access-token` |
| 説明 | `LINE Channel Access Token for messaging API` |
| シークレット値 | 空文字列（手動で設定） |
| 自動ローテーション | 無効 |

#### シークレット3: OpenWeatherMap API Key
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `OpenWeatherMapApiKey` |
| シークレット名 | `openweathermap-api-key` |
| 説明 | `OpenWeatherMap API Key for weather data` |
| シークレット値 | 空文字列（手動で設定） |
| 自動ローテーション | 無効 |

#### 共通設定
| パラメータ | 値 |
|-----------|-----|
| KMS暗号化 | AWS管理のキー |
| Deletion Protection | 30日の復旧期間 |

### 3.7 CloudWatch Logs

#### ロググループ設定（Webhook Lambda）
| パラメータ | 値 |
|-----------|-----|
| ロググループ名 | `/aws/lambda/weather-broadcast-line-webhook-handler` |
| 保持期間 | 30日 |
| KMS暗号化 | 無効 |

#### ロググループ設定（配信 Lambda）
| パラメータ | 値 |
|-----------|-----|
| ロググループ名 | `/aws/lambda/weather-broadcast-weather-broadcast-handler` |
| 保持期間 | 30日 |
| KMS暗号化 | 無効 |

### 3.8 IAM Role

#### Webhook Lambda 実行ロール
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `LineWebhookHandlerRole` |
| Trust Policy | Lambda Service Principal |
| Managed Policy | AWSLambdaBasicExecutionRole |
| Inline Policy | DynamoDB GetItem/PutItem (Usersテーブルのみ)<br>Secrets Manager GetSecretValue (3シークレットのみ) |

#### 配信 Lambda 実行ロール
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `WeatherBroadcastHandlerRole` |
| Trust Policy | Lambda Service Principal |
| Managed Policy | AWSLambdaBasicExecutionRole |
| Inline Policy | DynamoDB Scan (Usersテーブルのみ)<br>Secrets Manager GetSecretValue (2シークレットのみ) |

#### EventBridge実行ロール
| パラメータ | 値 |
|-----------|-----|
| 論理ID | `EventBridgeInvokeLambdaRole` |
| Trust Policy | Events Service Principal |
| Inline Policy | Lambda InvokeFunction (配信Lambdaのみ) |

## 4. データ構造の変更

本タスクではデータ構造の変更はありません。DynamoDBテーブルのスキーマは`docs/infra-design/table.md`で定義された通りに実装します。

## 5. 影響範囲の分析

### 5.1 新規作成されるリソース
- DynamoDB Usersテーブル
- Lambda関数 × 2（Webhook処理、天気配信処理）
- API Gateway REST API
- EventBridgeスケジュールルール
- Secrets Manager シークレット × 3
- CloudWatch Logsロググループ × 2
- IAM Role × 3

### 5.2 既存リソースへの影響
本タスクは新規インフラ構築のため、既存リソースへの影響はありません。

### 5.3 アプリケーションコードへの影響
- Lambda関数のビジネスロジック実装は別タスク
- 本タスクではダミーハンドラーを実装し、インフラの動作確認のみ実施
- 実際のコードは`app/`ディレクトリに別途実装される

### 5.4 CI/CDへの影響
- GitHub Actions ワークフローは別タスクで実装
- 本タスクでは手動デプロイのみ実施

### 5.5 コストへの影響

#### 想定月額コスト（ユーザー数100人、毎日配信の場合）

| サービス | 想定使用量 | 月額コスト（概算） |
|---------|-----------|------------------|
| DynamoDB | オンデマンド（100ユーザー、日次更新） | $1〜2 |
| Lambda | Webhook: 100回/日、配信: 1回/日 | $0.20以下 |
| API Gateway | 100リクエスト/日 | $0.01以下 |
| EventBridge | 30回/月 | 無料枠内 |
| Secrets Manager | 3シークレット | $1.20 |
| CloudWatch Logs | 1GB/月 | $0.50 |
| **合計** | | **約$3〜4/月** |

### 5.6 セキュリティへの影響
- Secrets Managerにより認証情報を安全に保管
- IAMロールは最小権限の原則に従う
- API GatewayエンドポイントはHTTPSのみ
- LINE Webhook署名検証は別タスクで実装

### 5.7 運用への影響
- CloudWatch Logsによるログ監視が可能
- DynamoDB PITRにより最大35日前の時点に復元可能
- CDKによりインフラの再現性が確保される

## 6. デプロイ手順

### 6.1 初回デプロイ前の準備
1. AWS CLIの認証情報設定
2. `cdk bootstrap`の実行（未実施の場合）
3. Secrets Managerへの実際の値の手動設定（デプロイ後）

### 6.2 デプロイコマンド
```bash
cd cdk
npm install
npx cdk synth    # CloudFormationテンプレート生成確認
npx cdk deploy   # デプロイ実行
```

### 6.3 デプロイ後の確認事項
- DynamoDBテーブルが作成されていること
- Lambda関数が作成されていること
- API Gatewayエンドポイントが作成されていること
- EventBridgeルールが有効化されていること
- Secrets Managerシークレットが作成されていること（値は空）

### 6.4 デプロイ後の手動設定
Secrets Managerの各シークレットに実際の値を設定：
- `line-channel-secret`: LINE Developersコンソールから取得
- `line-channel-access-token`: LINE Developersコンソールから取得
- `openweathermap-api-key`: OpenWeatherMapから取得

## 7. 検証計画

### 7.1 インフラ構築の検証
- `cdk synth`が成功すること
- `cdk deploy`が成功すること
- 全てのAWSリソースが正しく作成されていること

### 7.2 Lambda関数の検証
- ダミーハンドラーが正常に実行されること（テストイベント使用）
- CloudWatch Logsにログが出力されること

### 7.3 API Gatewayの検証
- `/webhook`エンドポイントにPOSTリクエストを送信できること
- Lambda Proxy統合が正しく動作していること

### 7.4 EventBridgeの検証
- スケジュールルールが有効化されていること
- テストイベントでLambda関数が起動すること

### 7.5 権限の検証
- 各Lambda関数が必要なリソースにアクセスできること
- 不要なリソースにはアクセスできないこと
