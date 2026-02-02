# 要求内容 - Lambda依存関係バンドリング修正

## 1. 背景・課題

現在、Lambda関数のデプロイ時にPythonライブラリの依存関係が解決されず、ランタイムエラーが発生する。

### 原因

- `lambda.Code.fromAsset()` でapp/ディレクトリをそのままZip化しているだけで、外部ライブラリがバンドルされていない
- `pyproject.toml` の `dependencies` が空（`dependencies = []`）
- アプリケーションコードは `boto3`、`requests` を使用しているが、これらがLambdaパッケージに含まれていない

### 補足

- `boto3` はLambdaランタイムにプリインストールされているが、バージョン固定の観点から明示的にバンドルすることが望ましい
- `requests` はLambdaランタイムに含まれないため、必ずバンドルが必要

## 2. 要求内容

CDKの `Code.fromAsset()` の `bundling` オプションを使い、Dockerコンテナ内で `uv` を用いて依存関係をインストール・バンドルする仕組みを構築する。

### 変更対象

1. **`app/pyproject.toml`** - 本番用依存関係（`boto3`、`requests`）を追加
2. **`cdk/lib/weather-broadcast-stack.ts`** - Webhook Handler Lambda の `Code.fromAsset()` に `bundling` オプションを追加
3. **Broadcast Handler Lambda** - 同様に `bundling` を適用（現在 `cdk/lambda/broadcast` を参照しているが、app/に統一するか検討）

## 3. 受け入れ条件

- [ ] `pyproject.toml` に本番用依存関係（`requests`）が定義されている
- [ ] CDKデプロイ時にDockerコンテナ内で `uv` を使って依存関係がインストールされる
- [ ] Lambda関数が依存ライブラリのインポートエラーなく実行できる
- [ ] CI/CDパイプライン（GitHub Actions）でのデプロイも正常に動作する
- [ ] 既存のローカル開発環境（docker-compose）に影響がない

## 4. 制約事項

- パッケージマネージャーは `uv` を使用する（技術仕様書の方針に準拠）
- CDKの `bundling` オプション + Dockerコンテナ方式で実装する
- Lambda Layerや `@aws-cdk/aws-lambda-python-alpha` は使用しない
