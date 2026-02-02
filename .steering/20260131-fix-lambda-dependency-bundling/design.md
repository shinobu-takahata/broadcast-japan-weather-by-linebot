# 設計 - Lambda依存関係バンドリング修正

## 1. 実装アプローチ

CDKデプロイの前に `uv pip install --target` で依存関係をディレクトリに出力し、`Code.fromAsset` でアプリコードと一緒にパッケージングする。

CDKのbundling機能やDockerは使用しない。

## 2. デプロイ手順

```bash
# 1. 依存関係インストール
cd app && uv pip install -r pyproject.toml --target .deps

# 2. デプロイ
cd cdk && npx cdk deploy
```

手動でもCI/CDでもこの2ステップのみ。

## 3. 変更コンポーネント

### 3.1 `app/pyproject.toml`

`dependencies` に `requests` を追加する。

### 3.2 `app/.gitignore`

`.deps/` を追加する（ビルド成果物のためGit管理対象外）。

### 3.3 `cdk/lib/weather-broadcast-stack.ts`

#### Webhook Handler Lambda

`Code.fromAsset` でアプリコードと `.deps` を合わせてパッケージングする。

```typescript
const appCode = lambda.Code.fromAsset(path.join(__dirname, "../../app"), {
  exclude: [".venv", "__pycache__", "tests", ".devcontainer", "*.pyc", "pyproject.toml", "uv.lock"],
});
```

`.deps/` 内のライブラリはapp/直下に展開されるため、Lambdaランタイムから直接importできる。

#### Broadcast Handler Lambda

- コードパスを存在しない `cdk/lambda/broadcast` から上記 `appCode` に変更
- handler名を `handlers.broadcast.handler` に変更

### 3.4 `docs/infra-design/cicd.md`

deploy.ymlに依存関係インストールステップを追加。

```yaml
- name: Install Python dependencies for Lambda
  working-directory: app
  run: uv pip install -r pyproject.toml --target .deps
```

## 4. 影響範囲

- ローカル開発フロー: 変更なし（.depsはデプロイ時のみ使用）
- CI/CD: deployワークフローに1ステップ追加のみ
- 既存のDynamoDB、API Gateway、EventBridge設定: 変更なし
