# タスクリスト - Lambda依存関係バンドリング修正

## タスク一覧

- [x] 1. `app/pyproject.toml` にプロダクション依存関係 `requests` を追加
- [x] 2. `app/.gitignore` に `.deps/` を追加
- [x] 3. `cdk/lib/weather-broadcast-stack.ts` を修正（fromAssetの変更、Broadcast Handlerのコードパス統一）
- [x] 4. `docs/infra-design/cicd.md` のdeployワークフローに依存関係インストールステップを追加
- [x] 5. CDK synthで合成確認
- [x] 6. 動作確認（CDK deploy）
