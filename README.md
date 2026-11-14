# 空き時間カレンダー

希望日時を選んだ後に必要情報を入力できる、非公式の面談空き時間カレンダー。

- GitHub Pages: 公開サイト `index.html`
- GitHub Actions: 1時間ごとに公開されている予約枠を取得（動作検証中）
- Formspree: 予約希望受付フォーム（受信内容は公開リポジトリに保存しない）
- データ形式: `data/slots.json` は固定

## 公開情報と認証情報

大学名・学部名は公開コードに書かず、GitHub ActionsのRepository secretsに `IRODAS_SCHOOL` と `IRODAS_FACULTY` を設定する。
`IRODAS_URL` は必要な場合のみSecretsで設定する。
ログイン情報、Cookie、トークン、応募者の個人情報は公開リポジトリに保存しない。

このカレンダーは公式の予約システムではない。日時の選択やフォーム送信で予約は確定しない。取得の失敗や空き枠の変動を考慮し、正確性を保証しない。

## 初回動作確認

1. 必要なSecretsをGitHubで設定する
2. Actions → Update slots → Run workflow
3. `data/slots.json` の `updated_at` とWorkflowログを確認する
4. メール送信は自分の情報でフォームテストをする（正式な面談予約は行わない）

GitHubのPublicリポジトリの過去コミットは閲覧できるため、公開済み情報が本当に機密である場合、履歴を含む対応が別途必要。
