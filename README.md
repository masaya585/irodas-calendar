# irodas-calendar

irodas の予約枠を定期的に確認し、GitHub Pages のカレンダーに反映するための土台です。月額 0 円運用を想定しています。

- **GitHub Actions**: 1時間ごとに取得スクリプトを実行（無料枠内を想定。定期実行は遅延・欠落することがあります）
- **GitHub Pages**: `index.html` + `data/slots.json` を無料公開
- **取得スクリプト**: `scripts/fetch_slots.py`（対象ページが確定したらセレクタを合わせます）

## 絶対に守ること
- GitHub のログイン情報・irodas の ID / パスワード・Cookie を、コードや公開ページに書かない
- 認証が必要な場合は GitHub の **Settings → Secrets and variables → Actions** にだけ登録する
- irodas 側が自動アクセス / ログイン後情報の外部公開を許可しているかは、対象ページが確定した時点で確認する

## セットアップ手順
詳しくは `SETUP.md` を参照。

1. GitHub で Public リポジトリ `irodas-calendar` を作成
2. このフォルダの中身をそのリポジトリに push
3. Settings → Pages → Branch: `main` / `(root)` を選んで Save
4. 必要なら Secrets に `IRODAS_URL` などを登録
5. Actions タブで `Update slots` を手動実行して初回確認

## 現在の状態
- サイトとワークフローの土台は作成済み
- 取得先の irodas ページ（どの企業・イベントの予約枠か、URL、ログイン要否）が未確定のため、スクリプトはプレースホルダです。確定後に実ページに合わせて実装します。
