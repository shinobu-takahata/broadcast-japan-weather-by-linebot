# リポジトリ構造定義書

## 1. 全体構成

```
/
├── cdk/                     # AWS CDKプロジェクト
│   └── .devcontainer/       # CDK用devcontainer
├── app/                     # Pythonアプリケーション
│   └── .devcontainer/       # Python用devcontainer
├── docs/                    # 永続的ドキュメント
└── .steering/               # 作業単位のドキュメント
```

## 2. ディレクトリの役割

### 2.1 cdk/

AWS CDKによるインフラ定義。VS Codeで`cdk/`を開いてdevcontainerを起動。

```
cdk/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── Dockerfile
│   └── docker-compose.yml
├── bin/
│   └── app.ts           # CDKアプリケーションエントリポイント
├── lib/
│   └── stack.ts         # スタック定義
├── cdk.json
├── package.json
└── tsconfig.json
```

### 2.2 app/

Pythonアプリケーション（Lambda関数）。VS Codeで`app/`を開いてdevcontainerを起動。

```
app/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── Dockerfile
│   └── docker-compose.yml
├── handlers/                # Presentation Layer
│   ├── webhook.py           # LINE Webhook処理
│   └── broadcast.py         # 天気配信処理
├── usecases/                # Application Layer
│   ├── register_region.py
│   ├── get_user_settings.py
│   └── broadcast_weather.py
├── domain/                  # Domain Layer
│   ├── entities/
│   │   └── user.py
│   ├── value_objects/
│   │   ├── location.py
│   │   └── weather.py
│   ├── services/
│   │   └── weather_calculator.py
│   └── repositories/
│       └── user_repository.py   # インターフェース
├── infrastructure/          # Infrastructure Layer
│   ├── dynamodb/
│   │   └── user_repository.py   # 実装
│   ├── openweathermap/
│   │   └── client.py
│   └── line/
│       └── messaging_client.py
├── requirements.txt
└── pyproject.toml
```

### 2.3 docs/

永続的ドキュメント。

```
docs/
├── product-requirements.md
├── functional-design/
│   ├── aws_infra.md
│   ├── layered_architecture.md
│   ├── workflow.md
│   ├── api_design.md
│   └── table.md
├── architecture.md
└── repository-structure.md
```

### 2.4 .steering/

作業単位のドキュメント。

```
.steering/
└── [YYYYMMDD]-[開発タイトル]/
    ├── requirements.md
    ├── design.md
    └── tasklist.md
```

## 3. ファイル配置ルール

### 3.1 Pythonソースコード

| ファイル種別 | 配置先 |
|-------------|--------|
| Lambda handler | `app/handlers/` |
| UseCase | `app/usecases/` |
| Entity | `app/domain/entities/` |
| Value Object | `app/domain/value_objects/` |
| Domain Service | `app/domain/services/` |
| Repository Interface | `app/domain/repositories/` |
| Repository Implementation | `app/infrastructure/` |
| 外部APIクライアント | `app/infrastructure/` |

### 3.2 テスト

| テスト種別 | 配置先 |
|-----------|--------|
| ユニットテスト | `app/tests/` |

### 3.3 設定ファイル

| ファイル | 配置先 |
|----------|--------|
| Python依存関係 | `app/requirements.txt` |
| Python設定 | `app/pyproject.toml` |
| CDK依存関係 | `cdk/package.json` |
| CDK設定 | `cdk/cdk.json` |

## 4. devcontainer使用方法

### 4.1 CDK開発

1. VS Codeで`cdk/`ディレクトリを開く
2. 「Reopen in Container」を実行
3. CDKコマンドを実行
   ```bash
   cdk synth
   cdk deploy
   ```

### 4.2 Python開発

1. VS Codeで`app/`ディレクトリを開く
2. 「Reopen in Container」を実行
3. Python開発を行う
   ```bash
   python -m pytest
   ```
