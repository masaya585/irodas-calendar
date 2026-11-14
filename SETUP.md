# 設定・確認手順

リポジトリ: `masaya585/irodas-calendar`

1. GitHub → Settings → Secrets and variables → Actions → New repository secret
2. `IRODAS_SCHOOL`: 取得時に入力する学校名
3. `IRODAS_FACULTY`: 取得時に入力する学部名
4. 必要なら `IRODAS_URL`: 対象ページURL（URLは公開ページのみに制限）
5. Actions → Update slots → Run workflow から手動実行
6. 取得成功を確認してから、フォームの受信テストを行う

注意: 取得スクリプトのLive動作は未検証。コードやGitHub Pagesに個人情報・ログイン情報を記録しないこと。GitHub Secretsの値も過去コミット履歴からは削除されないため、既に公開した情報を機密として扱う場合は履歴の点検が必要。
