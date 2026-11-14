# SETUP（岩島向け・最短手順）

## 1. リポジトリ作成
GitHub（アカウント: masaya585）で New repository
- Repository name: `irodas-calendar`
- Public を選択
- README / .gitignore / license は追加しない（このフォルダ側に用意済み）

## 2. push
このフォルダで:
```bash
git init
git add .
git commit -m "Initial calendar site + hourly Actions"
git branch -M main
git remote add origin https://github.com/masaya585/irodas-calendar.git
git push -u origin main
```
※ Muse 側の環境は GitHub にログインしていないため、この push は
  (a) 岩島がブラウザでログインして Muse のブラウザ作業に渡す、または
  (b) GitHub CLI の認証をこの環境で済ませる
のどちらかが必要です。ChatGPT 側の GitHub 連携は Muse 側には引き継がれません。

## 3. GitHub Pages を有効化
リポジトリ Settings → Pages
- Source: Deploy from a branch
- Branch: `main` / `(root)` → Save
- 公開 URL の目安: https://masaya585.github.io/irodas-calendar/

## 4. Actions の権限
Settings → Actions → General → Workflow permissions
- `Read and write permissions` を選択（slots.json の自動コミットに必要）

## 5. Secrets（必要な場合のみ）
Settings → Secrets and variables → Actions → New repository secret
- `IRODAS_URL` : 取得対象ページの URL
- 認証情報が必要な場合は、名前と受け渡し方法を決めてから登録する。パスワードを README やコードに書かない。

## 6. 初回テスト
Actions タブ → `Update slots` → Run workflow
- 成功し、`data/slots.json` の `updated_at` が更新されるか確認
- Pages の URL を開いてカレンダーが表示されるか確認
