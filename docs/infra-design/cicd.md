# CI/CD設計書

## 1. 概要

GitHub Actionsを使用したCI/CDパイプラインの設計。

## 2. ブランチ戦略

### 2.1 ブランチ構成

| ブランチ | 用途 | デプロイ先 |
|---------|------|-----------|
| main | 本番環境用 | Production |
| feature/* | 機能開発用 | - |
| fix/* | バグ修正用 | - |

### 2.2 マージフロー

```
feature/* → main
fix/*     → main
```

## 3. ワークフロー設計

### 3.1 ワークフロー一覧

| ワークフロー | トリガー | 内容 |
|-------------|---------|------|
| CI | PR作成時、pushイベント | Lint、型チェック、テスト |
| Deploy | mainへのマージ | Production環境へデプロイ |

### 3.2 CI ワークフロー

**トリガー:**
- Pull Request作成・更新時
- mainへのpush時

**ジョブ:**

```yaml
jobs:
  lint-python:
    # Ruffによるlint

  typecheck-python:
    # mypyによる型チェック

  test-python:
    # pytestによるテスト

  lint-cdk:
    # ESLintによるlint

  cdk-synth:
    # CDK synthによる合成確認
```

### 3.3 Deploy ワークフロー

**トリガー:** mainブランチへのpush

**ジョブ:**

```yaml
jobs:
  deploy:
    steps:
      - checkout
      - setup-python
      - setup-node
      - install-dependencies
      - cdk-deploy
```

## 4. 環境設定

### 4.1 GitHub Environments

| 環境名 | 用途 | 保護ルール |
|-------|------|-----------|
| production | 本番環境 | 必須レビュー |

### 4.2 GitHub Secrets

| シークレット名 | 用途 |
|---------------|------|
| AWS_ACCOUNT_ID | AWSアカウントID |

### 4.3 環境変数

| 変数名 | 値 |
|--------|-----|
| AWS_REGION | ap-northeast-1 |

## 5. ワークフローファイル構成

```
.github/
└── workflows/
    ├── ci.yml           # CI（lint、テスト）
    └── deploy.yml       # Productionデプロイ
```

## 6. CI詳細設計

### 6.1 Python CI

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .

  typecheck-python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run mypy .

  test-python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest

  lint-cdk:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cdk
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: cdk/package-lock.json
      - run: npm ci
      - run: npm run lint

  cdk-synth:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cdk
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: cdk/package-lock.json
      - run: npm ci
      - run: npx cdk synth
```

### 6.2 CDK Deploy

```yaml
name: Deploy

on:
  push:
    branches: [main]

env:
  AWS_REGION: ap-northeast-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-role
          aws-region: ${{ env.AWS_REGION }}

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: cdk/package-lock.json

      - uses: astral-sh/setup-uv@v4

      - name: Generate requirements.txt from pyproject.toml
        working-directory: app
        run: uv pip compile pyproject.toml -o requirements.txt

      - name: Install CDK dependencies
        working-directory: cdk
        run: npm ci

      - name: CDK Deploy
        working-directory: cdk
        run: npx cdk deploy --require-approval never
```

## 7. AWS認証

### 7.1 OIDC連携（推奨）

GitHub ActionsとAWSをOIDC連携し、長期的なアクセスキーを使用しない。

**必要なAWSリソース:**
- IAM OIDC Provider（GitHub用）
- IAM Role（GitHub Actions用）

**Trust Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:OWNER/REPO:*"
        }
      }
    }
  ]
}
```

## 8. セキュリティ考慮事項

### 8.1 シークレット管理

- OIDC連携により長期的なアクセスキーを排除
- AWS_ACCOUNT_IDのみGitHub Secretsで管理

### 8.2 デプロイ保護

- Production環境は必須レビューを設定
- mainブランチへの直接pushを禁止
- PRマージにはCIパス必須
