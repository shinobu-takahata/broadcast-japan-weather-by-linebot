# 設計書

## 1. 実装アプローチ

レイヤードアーキテクチャに従い、関心の分離を徹底する。各レイヤーの責務を明確にし、依存関係のルール（内側への依存のみ）を遵守する。

### 1.1 アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│                  webhook.py (handler)                    │
│  - LINE Webhook受信                                      │
│  - 署名検証                                               │
│  - UseCaseの呼び出し                                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│              register_region.py (UseCase)                │
│  - 地域設定ユースケースの実行                              │
│  - トランザクション制御                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Domain Layer                         │
│  - User Entity (user.py)                                │
│  - Location Value Object (location.py)                  │
│  - UserRepository Interface (user_repository.py)        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                    │
│  - DynamoDBUserRepository (dynamodb/user_repository.py) │
│  - GeocodingClient (openweathermap/geocoding_client.py) │
│  - LineMessagingClient (line/messaging_client.py)       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 依存性逆転の原則（DIP）

Application LayerはInfrastructure Layerの具象クラスに直接依存せず、Domain Layerで定義されたインターフェースに依存する。

## 2. 変更するコンポーネント

### 2.1 新規作成ファイル

#### Presentation Layer
| ファイルパス | 役割 |
|------------|------|
| `app/handlers/webhook.py` | LINE Webhookハンドラー |

#### Application Layer
| ファイルパス | 役割 |
|------------|------|
| `app/usecases/register_region.py` | 地域設定ユースケース |

#### Domain Layer
| ファイルパス | 役割 |
|------------|------|
| `app/domain/entities/user.py` | Userエンティティ |
| `app/domain/value_objects/location.py` | Location値オブジェクト |
| `app/domain/repositories/user_repository.py` | UserRepositoryインターフェース |

#### Infrastructure Layer
| ファイルパス | 役割 |
|------------|------|
| `app/infrastructure/dynamodb/user_repository.py` | DynamoDB実装 |
| `app/infrastructure/openweathermap/geocoding_client.py` | Geocoding APIクライアント |
| `app/infrastructure/line/messaging_client.py` | LINE Messaging APIクライアント |

#### 共通ユーティリティ
| ファイルパス | 役割 |
|------------|------|
| `app/utils/logger.py` | ロガー設定 |
| `app/utils/retry.py` | リトライデコレーター |

### 2.2 既存ファイルの変更

なし（初回実装のため）

## 3. データ構造の変更

### 3.1 Domain Layer

#### User Entity
```python
@dataclass
class User:
    """ユーザーエンティティ"""
    user_id: str
    location: Location
    created_at: datetime
    updated_at: datetime
```

#### Location Value Object
```python
@dataclass(frozen=True)
class Location:
    """地域情報の値オブジェクト"""
    city_name: str
    latitude: float
    longitude: float

    def __post_init__(self):
        # バリデーション
        if not -90 <= self.latitude <= 90:
            raise ValueError("緯度は-90〜90の範囲である必要があります")
        if not -180 <= self.longitude <= 180:
            raise ValueError("経度は-180〜180の範囲である必要があります")
```

### 3.2 Infrastructure Layer

#### DynamoDB Item構造
```python
{
    "userId": "U1234567890abcdef",  # String (Partition Key)
    "lat": 35.6619,                  # Number
    "lon": 139.7041,                 # Number
    "cityName": "渋谷区",            # String
    "createdAt": "2026-01-31T10:00:00Z",  # String (ISO 8601)
    "updatedAt": "2026-01-31T10:00:00Z"   # String (ISO 8601)
}
```

## 4. コンポーネント詳細設計

### 4.1 Presentation Layer

#### webhook.py

**責務**: LINE Webhookリクエストの受信と署名検証

```python
def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda関数エントリポイント

    処理フロー:
    1. リクエストボディと署名を取得
    2. 署名検証
    3. イベントタイプの判定
    4. メッセージタイプが"text"の場合、RegisterRegionUseCaseを実行
    5. レスポンス返却
    """
```

**主要メソッド**:
- `verify_signature(body: str, signature: str) -> bool`: 署名検証
- `handle_message_event(event: dict) -> None`: メッセージイベント処理

### 4.2 Application Layer

#### register_region.py

**責務**: 地域設定ユースケースの実行

```python
class RegisterRegionUseCase:
    """地域設定ユースケース"""

    def __init__(
        self,
        user_repository: UserRepository,
        geocoding_client: GeocodingClient,
        messaging_client: LineMessagingClient,
    ):
        self.user_repository = user_repository
        self.geocoding_client = geocoding_client
        self.messaging_client = messaging_client

    def execute(self, user_id: str, city_name: str, reply_token: str) -> None:
        """
        地域設定を実行

        処理フロー:
        1. Geocoding APIで緯度経度を取得
        2. Location値オブジェクトを生成
        3. Userエンティティを生成
        4. UserRepositoryで保存
        5. 成功メッセージを返信

        例外:
        - GeocodingNotFoundException: 地名が見つからない
        - RepositoryException: データベースエラー
        - MessagingException: メッセージ送信エラー
        """
```

### 4.3 Domain Layer

#### entities/user.py

**責務**: ユーザーの状態とビジネスルールを保持

```python
@dataclass
class User:
    """ユーザーエンティティ"""
    user_id: str
    location: Location
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(user_id: str, location: Location) -> 'User':
        """新規ユーザーを作成"""
        now = datetime.now(timezone.utc)
        return User(
            user_id=user_id,
            location=location,
            created_at=now,
            updated_at=now,
        )

    def update_location(self, location: Location) -> None:
        """地域を更新"""
        self.location = location
        self.updated_at = datetime.now(timezone.utc)
```

#### value_objects/location.py

**責務**: 地域情報の不変な値オブジェクト

```python
@dataclass(frozen=True)
class Location:
    """地域情報の値オブジェクト"""
    city_name: str
    latitude: float
    longitude: float

    def __post_init__(self):
        if not self.city_name:
            raise ValueError("市区町村名は必須です")
        if not -90 <= self.latitude <= 90:
            raise ValueError("緯度は-90〜90の範囲である必要があります")
        if not -180 <= self.longitude <= 180:
            raise ValueError("経度は-180〜180の範囲である必要があります")
```

#### repositories/user_repository.py

**責務**: UserRepositoryのインターフェース定義

```python
from abc import ABC, abstractmethod
from typing import Optional

class UserRepository(ABC):
    """ユーザーリポジトリのインターフェース"""

    @abstractmethod
    def save(self, user: User) -> None:
        """ユーザーを保存"""
        pass

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザーを取得"""
        pass
```

### 4.4 Infrastructure Layer

#### dynamodb/user_repository.py

**責務**: DynamoDBへのユーザーデータ永続化

```python
class DynamoDBUserRepository(UserRepository):
    """DynamoDB実装のUserRepository"""

    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def save(self, user: User) -> None:
        """
        ユーザーを保存（上書き）

        例外:
        - ClientError: DynamoDBエラー
        """
        item = {
            'userId': user.user_id,
            'lat': Decimal(str(user.location.latitude)),
            'lon': Decimal(str(user.location.longitude)),
            'cityName': user.location.city_name,
            'createdAt': user.created_at.isoformat(),
            'updatedAt': user.updated_at.isoformat(),
        }
        self.table.put_item(Item=item)

    def find_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザーを取得"""
        response = self.table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            return None
        return self._to_entity(response['Item'])
```

#### openweathermap/geocoding_client.py

**責務**: OpenWeatherMap Geocoding APIとの通信

```python
class GeocodingClient:
    """Geocoding APIクライアント"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/geo/1.0"

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_coordinates(self, city_name: str) -> tuple[float, float, str]:
        """
        市区町村名から緯度経度を取得

        戻り値:
            (latitude, longitude, city_name_en)

        例外:
            GeocodingNotFoundException: 地名が見つからない
            GeocodingAPIException: APIエラー
        """
        url = f"{self.base_url}/direct"
        params = {
            'q': f'{city_name},JP',
            'limit': 1,
            'appid': self.api_key,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            raise GeocodingNotFoundException(f"地名が見つかりません: {city_name}")

        location = data[0]
        return (location['lat'], location['lon'], location.get('name', city_name))
```

#### line/messaging_client.py

**責務**: LINE Messaging APIとの通信

```python
class LineMessagingClient:
    """LINE Messaging APIクライアント"""

    def __init__(self, channel_access_token: str):
        self.channel_access_token = channel_access_token
        self.base_url = "https://api.line.me/v2/bot/message"

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def reply_message(self, reply_token: str, text: str) -> None:
        """
        返信メッセージを送信

        例外:
            MessagingException: メッセージ送信エラー
        """
        url = f"{self.base_url}/reply"
        headers = {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json',
        }
        data = {
            'replyToken': reply_token,
            'messages': [{'type': 'text', 'text': text}],
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
```

### 4.5 ユーティリティ

#### utils/retry.py

**責務**: リトライ処理の共通化

```python
def retry(max_attempts: int = 3, backoff: list[int] = None):
    """
    リトライデコレーター

    Args:
        max_attempts: 最大試行回数
        backoff: リトライ間隔（秒）のリスト
    """
    if backoff is None:
        backoff = [1, 2, 4]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    sleep_time = backoff[min(attempt, len(backoff) - 1)]
                    logger.warning(f"Retry {attempt + 1}/{max_attempts} after {sleep_time}s: {e}")
                    time.sleep(sleep_time)
        return wrapper
    return decorator
```

#### utils/logger.py

**責務**: ロガーの設定

```python
import logging
import json

def get_logger(name: str) -> logging.Logger:
    """構造化ログを出力するロガーを取得"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def log_info(logger: logging.Logger, message: str, **kwargs):
    """構造化ログを出力（INFO）"""
    log_data = {'level': 'INFO', 'message': message, **kwargs}
    logger.info(json.dumps(log_data, ensure_ascii=False))

def log_error(logger: logging.Logger, message: str, **kwargs):
    """構造化ログを出力（ERROR）"""
    log_data = {'level': 'ERROR', 'message': message, **kwargs}
    logger.error(json.dumps(log_data, ensure_ascii=False))
```

## 5. 影響範囲の分析

### 5.1 新規作成されるコンポーネント

以下のコンポーネントが新規に作成される:
- Presentation Layer: webhook.py
- Application Layer: register_region.py
- Domain Layer: user.py, location.py, user_repository.py
- Infrastructure Layer: user_repository.py（DynamoDB実装）, geocoding_client.py, messaging_client.py
- ユーティリティ: logger.py, retry.py

### 5.2 依存する外部サービス

| サービス | 影響 |
|---------|------|
| OpenWeatherMap Geocoding API | API呼び出し回数が増加（1回/地域設定） |
| LINE Messaging API | メッセージ送信回数が増加（1回/地域設定） |
| DynamoDB | 書き込みリクエストが増加（1回/地域設定） |

### 5.3 インフラストラクチャへの影響

| リソース | 変更内容 |
|---------|---------|
| Lambda関数（line-webhook-handler） | 新規作成 |
| API Gateway | 新規エンドポイント `/webhook` を追加 |
| DynamoDB（Users テーブル） | 既に作成済み（影響なし） |
| Secrets Manager | 既存のシークレットを使用（影響なし） |

### 5.4 docs/への影響

今回の実装はdocs/の設計に基づいて行われるため、永続的ドキュメントへの変更は不要。

ただし、実装完了後に以下を確認することを推奨:
- レイヤードアーキテクチャ構成が設計通りか
- エラーハンドリングが設計通りか
- リトライ戦略が設計通りか

## 6. セキュリティ考慮事項

### 6.1 署名検証

LINE Webhookの署名検証は必須:
```python
def verify_signature(body: str, signature: str, channel_secret: str) -> bool:
    """X-Line-Signatureヘッダを検証"""
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)
```

### 6.2 シークレット管理

以下のシークレットはAWS Secrets Managerから取得:
- LINE Channel Secret
- LINE Channel Access Token
- OpenWeatherMap API Key

### 6.3 入力バリデーション

- 市区町村名の長さ制限（最大100文字）
- 緯度経度の範囲チェック（Location値オブジェクトで実施）

## 7. テスト戦略

### 7.1 ユニットテスト

各レイヤーごとにユニットテストを作成:
- Domain Layer: User, Locationの振る舞いテスト
- Application Layer: RegisterRegionUseCaseのテスト（モック使用）
- Infrastructure Layer: 各クライアントのテスト（モック使用）

### 7.2 統合テスト

- Webhook → UseCase → Repository の連携テスト
- 実際のDynamoDB LocalまたはAWS環境でのテスト

### 7.3 テストカバレッジ目標

- 全体: 80%以上
- Domain Layer: 100%
- Application Layer: 90%以上

## 8. パフォーマンス考慮事項

### 8.1 レスポンスタイム目標

- 地域設定処理全体: 3秒以内
  - Geocoding API呼び出し: 1秒以内
  - DynamoDB保存: 0.5秒以内
  - LINE Reply Message送信: 1秒以内

### 8.2 最適化ポイント

- Geocoding APIレスポンスのキャッシュは行わない（地域設定は低頻度のため）
- DynamoDBはオンデマンドキャパシティで十分
- Lambda関数のメモリは256MBで開始し、必要に応じて調整
