# タスクリスト - 開発環境セットアップ

## タスク一覧

### 1. Python開発環境

- [ ] `app/pyproject.toml` を作成（uv、Ruff、mypy設定を含む）

### 2. CDK開発環境

- [ ] `cdk/package.json` を作成（AWS CDK、TypeScript依存関係）
- [ ] `cdk/tsconfig.json` を作成（TypeScriptコンパイラ設定）
- [ ] `cdk/cdk.json` を作成（CDKアプリケーション設定）

### 3. 既存ファイル修正

- [ ] `cdk/Dockerfile` のAWS CLIインストールをARM64対応に修正

### 4. 動作確認

- [ ] app側devcontainerのビルド確認
- [ ] cdk側devcontainerのビルド確認

## 完了条件

- 全ての設定ファイルが作成されていること
- devcontainerが正常にビルドできること
