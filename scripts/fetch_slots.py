#!/usr/bin/env python3
"""
irodas の予約枠を取得して data/slots.json を更新するスクリプト（雛形）。

現状:
- 環境変数 IRODAS_URL が未設定なら、何も壊さず note だけを更新して終了する。
- 対象ページの構造（ログイン要否・HTML/API）が確定したら、parse_slots() を実装する。

禁止事項:
- ID/パスワード/Cookie をコードに直接書かない。必ず環境変数（GitHub Secrets）から読む。
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "slots.json"


def main() -> int:
    url = os.environ.get("IRODAS_URL", "").strip()
    now = datetime.now(timezone.utc).isoformat()

    if not url:
        data = {
            "updated_at": None,
            "source": "irodas",
            "slots": [],
            "note": "IRODAS_URL が未設定です。GitHub Secrets に取得対象 URL を登録してください。",
        }
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("IRODAS_URL not set; wrote placeholder slots.json")
        return 0

    # TODO: ここに対象ページに合わせた取得処理を実装する
    # - ログイン不要な公開ページか、認証が必要かを確認してから実装すること
    # - 取得は標準ライブラリ (urllib) を基本とし、必要時のみ依存を追加する
    print(f"Target URL configured ({url}) but parser is not implemented yet.", file=sys.stderr)
    print("Confirm the irodas page structure first, then implement parse_slots().", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
