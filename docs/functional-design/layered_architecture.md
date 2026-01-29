# レイヤードアーキテクチャ構成設計書

## 1. アーキテクチャ概要

本システムは、関心の分離と保守性を重視したレイヤードアーキテクチャを採用する。

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│                    (Lambda Handlers)                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                      (Use Cases)                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Domain Layer                         │
│                  (Business Logic)                        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                    │
│                    (External I/O)                        │
└─────────────────────────────────────────────────────────┘
```

## 2. 各レイヤーの責務

### 2.1 Presentation Layer

| 項目 | 内容 |
|------|------|
| 責務 | 外部からのリクエスト受付とレスポンス返却 |
| コンポーネント | `line-webhook-handler`<br>`weather-broadcast-handler` |
| 依存 | Application Layer |

### 2.2 Application Layer

| 項目 | 内容 |
|------|------|
| 責務 | ユースケースの実行 |
| コンポーネント | `RegisterRegionUseCase`<br>`GetUserSettingsUseCase`<br>`BroadcastWeatherUseCase` |
| 依存 | Domain Layer, Infrastructure Layer（インターフェース経由） |

### 2.3 Domain Layer

| 項目 | 内容 |
|------|------|
| 責務 | ビジネスロジックの実装 |
| コンポーネント | `User` Entity<br>`Location` Value Object<br>`Weather` Value Object<br>`WeatherCalculator` |
| 依存 | なし（最も内側のレイヤー） |

### 2.4 Infrastructure Layer

| 項目 | 内容 |
|------|------|
| 責務 | 外部システムとの通信 |
| コンポーネント | `DynamoDBUserRepository`<br>`OpenWeatherMapClient`<br>`LineMessagingClient` |
| 依存 | 外部サービス |

## 3. 依存関係のルール

1. **内側への依存のみ許可**: 外側のレイヤーは内側のレイヤーにのみ依存できる
2. **インターフェースによる抽象化**: Infrastructure LayerはDomain Layerで定義されたインターフェースを実装
3. **依存性逆転の原則（DIP）**: Application LayerはInfrastructure Layerの具象クラスではなく、インターフェースに依存
