# 設計書

## 1. 実装アプローチ

### 1.1 全体方針

CDKの`Code.fromAsset`に`bundling`オプションを追加し、デプロイ時にDockerコンテナ内で依存関係をインストールする方式に変更する。

**変更前（現状）:**
```typescript
const appCode = lambda.Code.fromAsset(
  path.join(__dirname, "../../app"),
  {
    exclude: [/* ... */]
  }
);
```

**変更後:**
```typescript
const appCode = lambda.Code.fromAsset(
  path.join(__dirname, "../../app"),
  {
    bundling: {
      image: lambda.Runtime.PYTHON_3_12.bundlingImage,
      command: [/* pip install コマンド */]
    },
    exclude: [/* ... */]
  }
);
```

### 1.2 bundlingコマンドの設計

Dockerコンテナ内で以下の処理を実行:

1. `requirements.txt`をもとに依存関係を `/asset-output` ディレクトリにインストール
2. アプリケーションコードを `/asset-output` にコピー

```bash
bash -c "
  pip install -r requirements.txt -t /asset-output &&
  cp -au . /asset-output
"
```

**ポイント:**
- `-r requirements.txt`: requirements.txtに定義された依存関係をインストール
- `-t /asset-output`: 指定ディレクトリにパッケージをインストール（フラット構造）
- `cp -au`: アプリケーションコードをコピー（`-a`はアーカイブモード、`-u`は更新のみ）

### 1.3 依存関係の管理方針

`pyproject.toml`を唯一の情報源とし、`requirements.txt`はデプロイ時に自動生成する。

- `app/pyproject.toml`で依存関係を一元管理
- CI/CDのDeployワークフローで`uv pip compile pyproject.toml -o requirements.txt`を実行して自動生成
- ローカルデプロイ時は手動で`uv pip compile pyproject.toml -o requirements.txt`を実行
- `app/requirements.txt`は`.gitignore`に追加し、リポジトリにはコミットしない

## 2. 変更するコンポーネント

### 2.1 CDKスタック定義

**ファイル:** `cdk/lib/weather-broadcast-stack.ts`

**変更箇所:**
- `appCode` 変数の定義（69-83行目）

**変更内容:**
- `bundling`オプションを追加
- `exclude`オプションは維持

### 2.2 CI/CDドキュメント

**ファイル:** `docs/infra-design/cicd.md`

**変更箇所:**
- 6.2 CDK Deploy セクション（223-226行目）

**変更内容:**
- `Install Python dependencies for Lambda` ステップを削除

### 2.3 GitHub Actions ワークフロー（該当する場合）

**ファイル:** `.github/workflows/deploy.yml`（存在する場合）

**変更内容:**
- `uv pip install --target .deps` ステップを削除

### 2.4 .gitignore

**ファイル:** `.gitignore`

**変更内容:**
- `.deps/` エントリを削除

## 3. データ構造の変更

なし。Lambda関数の環境変数、DynamoDBテーブル構造、API構造に変更はない。

## 4. 影響範囲の分析

### 4.1 Lambda関数への影響

**Webhook Handler:**
- デプロイパッケージに`requests`ライブラリが含まれるようになる
- `handlers.webhook`から`import requests`が成功する
- ハンドラーパスは変更なし: `handlers.webhook.handler`

**Broadcast Handler:**
- 同様に`requests`ライブラリが利用可能になる
- ハンドラーパスは変更なし: `handlers.broadcast.handler`

### 4.2 CDKデプロイプロセスへの影響

**デプロイ時間:**
- bundling処理により初回デプロイ時間が増加（1-2分程度）
- 2回目以降はキャッシュが効くため、変更がない限り高速

**Docker要件:**
- ローカルデプロイ時にDocker環境が必要
- GitHub ActionsのランナーにはDockerがデフォルトで利用可能

**cdk synth:**
- bundling処理が実行される
- 出力される`cdk.out/`ディレクトリにバンドルされたアセットが生成される

### 4.3 開発環境への影響

**ローカル開発:**
- `app/.venv`は引き続き開発用として使用
- bundlingは開発環境には影響しない（デプロイ時のみ実行）

**テスト実行:**
- 影響なし（ローカルの`.venv`を使用）

### 4.4 CI/CDパイプラインへの影響

**GitHub Actions:**
- `deploy.yml`から手動の依存関係インストールステップを削除できる
- ワークフローがシンプルになる
- デプロイ時間はbundling分だけ増加

**必要なランナー要件:**
- Docker（既に利用可能）
- Node.js（既に利用可能）
- AWS認証情報（既に設定済み）

### 4.5 既存の.steering/20260131-fix-lambda-dependency-bundlingとの関係

旧ステアリング（20260131）は手動で`.deps/`にインストールするアプローチでしたが、今回の変更により:
- `.deps/`ディレクトリは不要になる
- 手動のビルドステップは不要になる
- CDKの自動bundlingに置き換わる

## 5. 実装の詳細設計

### 5.1 bundlingオプションの完全な設定

```typescript
const appCode = lambda.Code.fromAsset(
  path.join(__dirname, "../../app"),
  {
    bundling: {
      image: lambda.Runtime.PYTHON_3_12.bundlingImage,
      command: [
        "bash",
        "-c",
        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
      ],
    },
    exclude: [
      ".venv",
      "__pycache__",
      "tests",
      ".devcontainer",
      "*.pyc",
      "pyproject.toml",
      "uv.lock",
      "Dockerfile",
    ],
  }
);
```

**処理の流れ:**
1. CDKが`app/`ディレクトリを読み込む
2. `exclude`リストに該当するファイル・ディレクトリを除外
3. Dockerコンテナ（`public.ecr.aws/sam/build-python3.12`）を起動
4. コンテナ内で`pip install`を実行し、パッケージを`/asset-output`にインストール
5. アプリケーションコードを`/asset-output`にコピー
6. `/asset-output`の内容をzip化してLambda関数としてデプロイ

### 5.2 デプロイされるディレクトリ構造

```
/var/task/  (Lambda実行環境)
├── requests/                    # pip installでインストール
│   └── ...
├── urllib3/                     # requestsの依存関係
│   └── ...
├── certifi/                     # requestsの依存関係
│   └── ...
├── charset_normalizer/          # requestsの依存関係
│   └── ...
├── idna/                        # requestsの依存関係
│   └── ...
├── handlers/                    # アプリケーションコード
│   ├── webhook.py
│   └── broadcast.py
├── usecases/
├── domain/
└── infrastructure/
```

### 5.3 除外されるファイル

以下は`exclude`オプションでデプロイから除外される:
- `.venv/` - ローカルの仮想環境
- `__pycache__/` - Pythonキャッシュ
- `tests/` - テストコード
- `.devcontainer/` - 開発コンテナ設定
- `*.pyc` - コンパイル済みPythonファイル
- `pyproject.toml` - プロジェクト設定（本番環境不要）
- `uv.lock` - ロックファイル（本番環境不要）
- `Dockerfile` - 開発用Dockerfile（本番環境不要）

## 6. docs/への影響

### 6.1 更新が必要なドキュメント

**`docs/infra-design/cicd.md`**

**変更箇所:** 6.2 CDK Deploy セクション

**変更前:**
```yaml
- name: Install Python dependencies for Lambda
  working-directory: app
  run: uv pip install -r pyproject.toml --target .deps

- name: CDK Deploy
  working-directory: cdk
  run: npx cdk deploy --require-approval never
```

**変更後:**
```yaml
- name: CDK Deploy
  working-directory: cdk
  run: npx cdk deploy --require-approval never
```

### 6.2 更新が不要なドキュメント

以下のドキュメントは変更の影響を受けない:
- `docs/product-requirements.md` - プロダクト要求は変更なし
- `docs/functional-design/layered_architecture.md` - アーキテクチャは変更なし
- `docs/functional-design/workflow.md` - 処理フローは変更なし
- `docs/functional-design/api_design.md` - API設計は変更なし
- `docs/infra-design/table.md` - テーブル設計は変更なし
- `docs/infra-design/aws_infra.md` - AWS構成は変更なし（デプロイ方法のみ変更）
- `docs/structure/architecture.md` - 技術スタックは変更なし
- `docs/structure/repository-structure.md` - リポジトリ構造は変更なし

## 7. リスクと対策

### 7.1 リスク: bundlingの失敗

**内容:** Dockerコンテナ内でpip installが失敗する可能性

**対策:**
- デプロイ前にローカルで`cdk synth`を実行し、bundlingが成功することを確認
- エラーが発生した場合、コマンドの構文やパッケージ名を確認

### 7.2 リスク: デプロイ時間の増加

**内容:** bundling処理により初回デプロイ時間が増加

**対策:**
- CDKは自動的にbundlingをキャッシュする
- コードやbundling設定に変更がない場合、キャッシュが使用される

### 7.3 リスク: Docker環境の不備

**内容:** ローカルやCI環境でDockerが利用できない

**対策:**
- GitHub ActionsのランナーにはDockerがデフォルトで利用可能
- ローカル開発ではDocker Desktopのインストールを推奨

### 7.4 リスク: ローカルデプロイ時のrequirements.txt生成忘れ

**内容:** ローカルで`cdk deploy`する前に`uv pip compile`を実行し忘れる

**対策:**
- `requirements.txt`が存在しない場合、bundlingがエラーになるので気づける
- CI/CDでは自動生成されるため、本番デプロイへの影響はない

## 8. テスト方針

### 8.1 ローカルテスト

1. `cdk synth`を実行し、bundlingが成功することを確認
2. 生成された`cdk.out/`ディレクトリに、bundleされたアセットが含まれることを確認

### 8.2 デプロイテスト

1. `cdk deploy`を実行し、デプロイが成功することを確認
2. デプロイされたLambda関数のコンソールでコードを確認し、`requests`ライブラリが含まれていることを確認

### 8.3 動作確認

1. LINE BOTに地域設定メッセージを送信し、正常に処理されることを確認
2. Lambda関数のCloudWatchログでimportエラーが発生していないことを確認

## 9. ロールバック計画

もしbundling後に問題が発生した場合:

1. CDKスタックの`bundling`オプションを削除
2. 手動で依存関係をインストールする方式に戻す（旧方式）
3. `cdk deploy`で再デプロイ

ただし、今回の変更はデプロイプロセスのみの変更であり、アプリケーションロジックには影響しないため、ロールバックのリスクは低い。
