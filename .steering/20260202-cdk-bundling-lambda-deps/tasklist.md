# タスクリスト

## 1. 実装タスク

### Phase 0: requirements.txtの作成

- [x] **Task 0.1: app/requirements.txtを生成**
  - 作業内容:
    - appコンテナで`uv pip compile pyproject.toml -o requirements.txt`を実行
    - CI/CDでも同様に自動生成する（`docs/infra-design/cicd.md`に反映済み）
    - `app/requirements.txt`は`.gitignore`に追加（リポジトリにはコミットしない）
  - 完了条件: `app/requirements.txt`が生成され、依存関係がピン留めされている

### Phase 1: CDKスタックの変更

- [x] **Task 1.1: CDKスタックにbundlingオプションを追加**
  - ファイル: `cdk/lib/weather-broadcast-stack.ts`
  - 変更箇所: `appCode` 変数の定義（69-83行目）
  - 作業内容:
    - `lambda.Code.fromAsset`に`bundling`オプションを追加
    - `image: lambda.Runtime.PYTHON_3_12.bundlingImage`を設定
    - `command`に`pip install -r requirements.txt -t /asset-output && cp -au . /asset-output`を設定
    - 既存の`exclude`オプションは維持
  - 完了条件: TypeScriptのコンパイルエラーがない

### Phase 2: ローカルでの動作確認

- [x] **Task 2.1: cdk synthの実行**
  - 作業内容:
    - `cdk/`ディレクトリで`npx cdk synth`を実行
    - bundlingが成功することを確認
    - `cdk.out/`ディレクトリにバンドルされたアセットが生成されることを確認
  - 完了条件: synthが成功し、エラーが発生しない

- [x] **Task 2.2: バンドルされたアセットの確認**
  - 作業内容:
    - `cdk.out/`ディレクトリ内のアセットzipを解凍
    - `requests`ライブラリが含まれていることを確認
    - アプリケーションコード（`handlers/`, `usecases/`など）が含まれていることを確認
    - 除外設定（`.venv`, `tests`など）が正しく動作していることを確認
  - 完了条件: 必要なファイルが含まれ、不要なファイルが除外されている

### Phase 3: ドキュメントの更新

- [x] **Task 3.1: cicd.mdの更新**
  - ファイル: `docs/infra-design/cicd.md`
  - 変更箇所: 6.2 CDK Deploy セクション（223-226行目）
  - 作業内容:
    - `Install Python dependencies for Lambda`ステップを削除
    - Deployワークフローのステップを更新
  - 完了条件: 手動の依存関係インストールステップが削除されている

### Phase 4: 不要な設定のクリーンアップ

- [x] **Task 4.1: .gitignoreの更新**
  - ファイル: `.gitignore`
  - 作業内容:
    - `.deps/`エントリを削除
  - 完了条件: `.deps/`エントリが存在しない

- [x] **Task 4.2: 既存の.deps/ディレクトリの削除（存在する場合）**
  - 作業内容:
    - `app/.deps/`ディレクトリが存在するか確認
    - 存在する場合、削除
  - 完了条件: `.deps/`ディレクトリが存在しない

- [x] **Task 4.3: GitHub Actionsワークフローの確認**
  - ファイル: `.github/workflows/deploy.yml`（存在する場合）
  - 作業内容:
    - `uv pip install --target .deps`ステップが存在するか確認
    - 存在する場合、削除
  - 完了条件: 手動の依存関係インストールステップが存在しない

### Phase 5: デプロイテスト

- [x] **Task 5.1: CDK deployの実行**
  - 作業内容:
    - `cdk/`ディレクトリで`npx cdk deploy`を実行
    - デプロイが成功することを確認
  - 完了条件: デプロイが正常に完了する

- [ ] **Task 5.2: Lambda関数コードの確認**
  - 作業内容:
    - AWSコンソールでLambda関数を開く
    - コードタブで`requests`ライブラリが含まれていることを確認
    - アプリケーションコード（`handlers/`など）が正しく配置されていることを確認
  - 完了条件: 依存関係とアプリケーションコードが正しくデプロイされている

### Phase 6: 動作確認

- [ ] **Task 6.1: Webhook Handlerの動作確認**
  - 作業内容:
    - LINE BOTに地域設定メッセージを送信（例: 「渋谷区」）
    - CloudWatchログでimportエラーが発生していないことを確認
    - 正常に応答が返ってくることを確認
  - 完了条件: importエラーが発生せず、正常に動作する

- [ ] **Task 6.2: Broadcast Handlerの動作確認**
  - 作業内容:
    - 手動でBroadcast Lambda関数をテスト実行（AWSコンソールまたはCLI）
    - CloudWatchログでimportエラーが発生していないことを確認
    - 依存関係が正常にインポートされていることを確認
  - 完了条件: importエラーが発生せず、正常に動作する

### Phase 7: CI/CDパイプラインの確認

- [ ] **Task 7.1: mainブランチへのマージ**
  - 作業内容:
    - 変更をcommitしてPRを作成
    - CIが成功することを確認
    - mainブランチにマージ
  - 完了条件: CIが成功する

- [ ] **Task 7.2: GitHub Actionsでの自動デプロイ確認**
  - 作業内容:
    - mainブランチへのマージでDeployワークフローが起動することを確認
    - bundlingが自動実行されることを確認
    - デプロイが成功することを確認
  - 完了条件: GitHub Actionsでのデプロイが成功する

## 2. タスクの依存関係

```
Task 1.1 (CDKスタック変更)
  ↓
Task 2.1 (cdk synth実行)
  ↓
Task 2.2 (アセット確認)
  ↓
Task 3.1 (cicd.md更新) + Task 4.1 (gitignore更新) + Task 4.2 (.deps削除) + Task 4.3 (workflow確認)
  ↓
Task 5.1 (cdk deploy実行)
  ↓
Task 5.2 (Lambda確認)
  ↓
Task 6.1 (Webhook動作確認) + Task 6.2 (Broadcast動作確認)
  ↓
Task 7.1 (mainマージ)
  ↓
Task 7.2 (自動デプロイ確認)
```

## 3. 完了条件

### 3.1 機能完了条件

- [ ] CDKのbundlingオプションが正しく設定されている
- [ ] `cdk synth`が成功する
- [ ] `cdk deploy`が成功する
- [ ] Lambda関数に`requests`ライブラリが含まれている
- [ ] Webhook HandlerとBroadcast Handlerが正常に動作する
- [ ] importエラーが発生しない

### 3.2 ドキュメント完了条件

- [ ] `docs/infra-design/cicd.md`から手動の依存関係インストールステップが削除されている
- [ ] `.gitignore`から`.deps/`エントリが削除されている

### 3.3 クリーンアップ完了条件

- [ ] `.deps/`ディレクトリが存在しない
- [ ] `.github/workflows/deploy.yml`に手動インストールステップが存在しない（ファイルが存在する場合）

### 3.4 CI/CD完了条件

- [ ] GitHub ActionsのDeployワークフローが成功する
- [ ] bundlingが自動実行される
- [ ] 手動のビルドステップが不要になっている

## 4. 検証チェックリスト

実装完了後、以下を確認してください:

- [ ] Lambda関数で`import requests`が成功する
- [ ] LINE BOTの地域設定機能が正常に動作する
- [ ] CloudWatchログにimportエラーが記録されていない
- [ ] CDKのbundlingキャッシュが正しく動作する（2回目のdeployが高速）
- [ ] 除外設定が正しく動作している（`.venv`, `tests`などがデプロイされていない）
- [ ] デプロイパッケージのサイズが適切（不要なファイルが含まれていない）
- [ ] GitHub ActionsでDockerが利用可能である
- [ ] ドキュメントが最新の状態に更新されている

## 5. 注意事項

### 5.1 Docker環境について

- ローカルで`cdk synth`や`cdk deploy`を実行する場合、Docker Desktopが起動している必要があります
- GitHub ActionsのランナーにはDockerがデフォルトで利用可能です

### 5.2 初回デプロイ時間について

- bundling処理により、初回デプロイ時間が1-2分程度増加します
- 2回目以降はキャッシュが効くため、変更がない限り高速です

### 5.3 依存関係の追加について

- `pyproject.toml`の`dependencies`を更新した場合、`requirements.txt`を再生成する必要があります
- ローカル: `docker compose run --rm app uv pip compile pyproject.toml -o requirements.txt`
- CI/CD: Deployワークフローで自動生成されます

### 5.4 トラブルシューティング

**問題: bundlingが失敗する**
- Dockerが起動しているか確認
- インターネット接続が正常か確認（pipがパッケージをダウンロードするため）
- `pip install`のパッケージ名やバージョン指定が正しいか確認

**問題: デプロイ後もimportエラーが発生する**
- AWSコンソールでLambda関数のコードを確認し、`requests`ライブラリが含まれているか確認
- CloudWatchログで詳細なエラーメッセージを確認

**問題: cdk synthが遅い**
- bundlingのキャッシュが効いていない可能性があります
- `cdk.out/`ディレクトリを削除して再実行してみてください
