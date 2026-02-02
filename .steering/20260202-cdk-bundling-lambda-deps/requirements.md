# 要求定義書

## 1. 変更・追加する機能の説明

### 背景
現在のデプロイ方式では、Lambda関数に必要な依存関係（`requests`など）が含まれず、実行時にimportエラーが発生している。

現状の問題点:
- `cdk/lib/weather-broadcast-stack.ts` で `lambda.Code.fromAsset` を使用し、`app/` ディレクトリをそのままデプロイしている
- `app/pyproject.toml` に定義された依存関係（`requests>=2.31.0`）がLambdaレイヤーに含まれていない
- GitHub Actionsの `deploy.yml` で手動の `uv pip install --target .deps` ステップを実行しているが、CDKが `.deps/` を参照していないため効果がない
- `.gitignore` に `.deps/` が定義されているが、実際には使用されていない

### 変更内容
CDKの `bundling` オプションを使用して、デプロイ時にDockerコンテナ内で依存関係を自動的にインストールし、フラットな構造でパッケージングする。

これにより:
- 手動のビルドステップが不要になる
- デプロイの信頼性が向上する
- ローカル環境の差異による問題を防げる
- CI/CD パイプラインがシンプルになる

## 2. 受け入れ条件

### AC-001: Lambda依存関係の自動バンドリング
- [ ] CDKの `bundling` オプションを使用して、デプロイ時にDockerコンテナ内で `pip install` を実行する
- [ ] `app/pyproject.toml` の `dependencies` セクションに定義されたパッケージがインストールされる
- [ ] インストールされた依存関係がLambda関数のルートディレクトリにフラットに配置される
- [ ] Lambda関数から `import requests` が成功する

### AC-002: 手動ビルドステップの削除
- [ ] `docs/infra-design/cicd.md` の Deploy ワークフローから `uv pip install --target .deps` ステップを削除する
- [ ] `.github/workflows/deploy.yml` に該当するステップがある場合、削除する
- [ ] デプロイ時にCDKのbundlingが自動実行される

### AC-003: 不要な設定のクリーンアップ
- [ ] `.gitignore` から `.deps/` エントリを削除する
- [ ] 既存の `.deps/` ディレクトリが存在する場合、削除する

### AC-004: 既存の除外設定の維持
- [ ] CDKの `fromAsset` の `exclude` オプションで、開発用ファイル（`.venv`, `__pycache__`, `tests`, `.devcontainer`, `*.pyc`, `pyproject.toml`, `uv.lock`, `Dockerfile`）が除外される
- [ ] 本番環境に不要なファイルがデプロイされない

### AC-005: デプロイの成功確認
- [ ] CDK synthが成功する
- [ ] CDK deployが成功する
- [ ] デプロイされたLambda関数で依存関係が正常にインポートできる

## 3. 制約事項

### 3.1 技術的制約
- AWS CDK 2.x の `bundling` オプションを使用する
- Python 3.12 のDockerイメージを使用する
- `pip install` は `requirements.txt` 形式で実行する（pyproject.tomlから変換が必要）

### 3.2 運用上の制約
- bundlingはデプロイ時にDockerコンテナで実行されるため、Docker環境が必要
- GitHub ActionsのランナーにはDockerが利用可能
- bundlingによりデプロイ時間がわずかに増加する可能性がある

### 3.3 既存機能への影響
- Lambda関数のhandlerパス（`handlers.webhook.handler`, `handlers.broadcast.handler`）は変更しない
- 環境変数の設定は変更しない
- IAM権限の設定は変更しない

## 4. 参考情報

### 4.1 AWS CDK bundling の仕組み
CDKの`Code.fromAsset`に`bundling`オプションを指定すると、デプロイ時にDockerコンテナ内でコマンドを実行し、その結果をLambda関数としてパッケージングできる。

```typescript
lambda.Code.fromAsset(path, {
  bundling: {
    image: lambda.Runtime.PYTHON_3_12.bundlingImage,
    command: [
      'bash', '-c',
      'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
    ]
  }
})
```

### 4.2 pyproject.toml から requirements.txt への変換
`pyproject.toml` の `dependencies` を `requirements.txt` 形式に変換する必要がある。
これはbundlingコマンド内で `pip install` の引数として直接指定することも可能。
