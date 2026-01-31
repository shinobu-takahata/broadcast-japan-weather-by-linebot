# 設計書 - 開発環境セットアップ

## 1. 現状分析

以下のファイルは既に作成済みです。

| ファイル | 状態 |
|---------|------|
| `docker-compose.yml` | 作成済み |
| `app/Dockerfile` | 作成済み |
| `app/.devcontainer/devcontainer.json` | 作成済み |
| `cdk/Dockerfile` | 作成済み |
| `cdk/.devcontainer/devcontainer.json` | 作成済み |

以下のファイルが未作成です。

| ファイル | 状態 |
|---------|------|
| `app/pyproject.toml` | 未作成 |
| `cdk/package.json` | 未作成 |
| `cdk/tsconfig.json` | 未作成 |
| `cdk/cdk.json` | 未作成 |

## 2. 実装アプローチ

### 2.1 Python開発環境（app/）

#### pyproject.toml
uvによるパッケージ管理の設定ファイルを作成します。

```toml
[project]
name = "broadcast-japan-weather"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv]
dev-dependencies = [
    "pytest",
    "ruff",
    "mypy",
]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
```

- `uv sync`でdev-dependenciesも含めてインストールされる
- Ruffのルールはpyproject.toml内で管理
- mypyはstrict modeで運用

### 2.2 CDK開発環境（cdk/）

#### package.json
AWS CDKプロジェクトの依存関係を定義します。

```json
{
  "name": "broadcast-japan-weather-cdk",
  "version": "0.1.0",
  "bin": {
    "app": "bin/app.js"
  },
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "cdk": "cdk"
  },
  "devDependencies": {
    "typescript": "~5.7",
    "@types/node": "^20",
    "aws-cdk": "^2"
  },
  "dependencies": {
    "aws-cdk-lib": "^2",
    "constructs": "^10"
  }
}
```

#### tsconfig.json
TypeScriptコンパイラ設定。CDK標準の設定を使用します。

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["es2022"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "outDir": "./build",
    "rootDir": "./"
  },
  "exclude": ["node_modules", "build"]
}
```

#### cdk.json
CDKアプリケーション設定。

```json
{
  "app": "npx ts-node bin/app.ts",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "node_modules",
      "build",
      "cdk.out",
      "**/*.js",
      "**/*.d.ts"
    ]
  },
  "context": {
    "@aws-cdk/core:stackRelativeExports": true
  }
}
```

## 3. 既存ファイルの修正

### 3.1 cdk/Dockerfile - ARM64対応
現在のDockerfileはx86_64向けのAWS CLIインストールURLを使用しています。マルチアーキテクチャ対応を検討します。

```dockerfile
# 現在: x86_64固定
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" ...

# 修正: アーキテクチャ自動判定
RUN ARCH=$(uname -m) && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" ...
```

これにより、Apple Silicon (M1/M2/M3) Macでも正常にビルドできます。

### 3.2 docker-compose.yml - platform指定不要
docker-compose.ymlにはplatform指定を追加しません。Dockerfileのマルチアーキテクチャ対応で解決します。

## 4. 変更するコンポーネント

| コンポーネント | 変更内容 |
|--------------|---------|
| `app/pyproject.toml` | 新規作成 |
| `cdk/package.json` | 新規作成 |
| `cdk/tsconfig.json` | 新規作成 |
| `cdk/cdk.json` | 新規作成 |
| `cdk/Dockerfile` | ARM64対応の修正 |

## 5. 影響範囲の分析

- 既存のdevcontainer.jsonファイルへの変更は不要
- docker-compose.ymlへの変更は不要
- app/Dockerfileへの変更は不要
- 新規ファイル追加のみのため、既存環境への影響なし
- cdk/DockerfileのARM64対応は機能追加であり、x86_64環境でも動作に影響なし
