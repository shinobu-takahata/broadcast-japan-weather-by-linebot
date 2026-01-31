# タスクリスト: アプリケーションディレクトリ骨組み作成

## 概要
`docs/functional-design/layered_architecture.md` および `docs/structure/repository-structure.md` に基づき、`app/` 配下にレイヤードアーキテクチャのディレクトリ構造と空ファイルを作成する。ビジネスロジックの実装は含まない。

## タスク一覧

### 1. Presentation Layer ディレクトリ作成
- [x] `app/handlers/` ディレクトリを作成
- [x] `app/handlers/__init__.py` を作成（空ファイル）
- [x] `app/handlers/webhook.py` を作成（空ファイル）
- [x] `app/handlers/broadcast.py` を作成（空ファイル）

### 2. Application Layer ディレクトリ作成
- [x] `app/usecases/` ディレクトリを作成
- [x] `app/usecases/__init__.py` を作成（空ファイル）
- [x] `app/usecases/register_region.py` を作成（空ファイル）
- [x] `app/usecases/get_user_settings.py` を作成（空ファイル）
- [x] `app/usecases/broadcast_weather.py` を作成（空ファイル）

### 3. Domain Layer ディレクトリ作成
- [x] `app/domain/` ディレクトリを作成
- [x] `app/domain/__init__.py` を作成（空ファイル）
- [x] `app/domain/entities/` ディレクトリを作成
- [x] `app/domain/entities/__init__.py` を作成（空ファイル）
- [x] `app/domain/entities/user.py` を作成（空ファイル）
- [x] `app/domain/value_objects/` ディレクトリを作成
- [x] `app/domain/value_objects/__init__.py` を作成（空ファイル）
- [x] `app/domain/value_objects/location.py` を作成（空ファイル）
- [x] `app/domain/value_objects/weather.py` を作成（空ファイル）
- [x] `app/domain/services/` ディレクトリを作成
- [x] `app/domain/services/__init__.py` を作成（空ファイル）
- [x] `app/domain/services/weather_calculator.py` を作成（空ファイル）
- [x] `app/domain/repositories/` ディレクトリを作成
- [x] `app/domain/repositories/__init__.py` を作成（空ファイル）
- [x] `app/domain/repositories/user_repository.py` を作成（空ファイル）

### 4. Infrastructure Layer ディレクトリ作成
- [x] `app/infrastructure/` ディレクトリを作成
- [x] `app/infrastructure/__init__.py` を作成（空ファイル）
- [x] `app/infrastructure/dynamodb/` ディレクトリを作成
- [x] `app/infrastructure/dynamodb/__init__.py` を作成（空ファイル）
- [x] `app/infrastructure/dynamodb/user_repository.py` を作成（空ファイル）
- [x] `app/infrastructure/openweathermap/` ディレクトリを作成
- [x] `app/infrastructure/openweathermap/__init__.py` を作成（空ファイル）
- [x] `app/infrastructure/openweathermap/client.py` を作成（空ファイル）
- [x] `app/infrastructure/line/` ディレクトリを作成
- [x] `app/infrastructure/line/__init__.py` を作成（空ファイル）
- [x] `app/infrastructure/line/messaging_client.py` を作成（空ファイル）

### 5. テストディレクトリ作成
- [x] `app/tests/` ディレクトリを作成
- [x] `app/tests/__init__.py` を作成（空ファイル）

## 完了条件
- `app/` 配下に4レイヤー（handlers, usecases, domain, infrastructure）＋ tests のディレクトリ構造が存在すること
- 各ディレクトリに `__init__.py` が配置されていること
- `repository-structure.md` に記載のファイルが全て存在すること（中身は空で可）
