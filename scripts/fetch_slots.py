#!/usr/bin/env python3
"""Retrieve public pre-registration irodas availability using a browser.

Only the public *reference list* (before registration) is in scope. This
extractor is deliberately conservative: it never writes an empty or uncertain
result, and it never submits personal details or books an appointment.

The actual target DOM has not yet been inspected with DevTools. Selectors and
date parsing MUST be verified against the live page before relying on automation.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "slots.json"
JST = timezone(timedelta(hours=9))
DEFAULT_URL = "https://form.irodas.com/member/partner-call?dai_marketing=ds&chu_marketing=tre"

# Strictly limit extracted data to dated times, not durations or the embedded
# appointment widget. These are fallback patterns, not confirmed DOM selectors.
DATE_PATTERN = re.compile(r"(?<!\d)(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})日?(?!\d)")
MONTH_DAY_PATTERN = re.compile(r"(?<!\d)(\d{1,2})[/月](\d{1,2})日?(?!\d)")
TIME_PATTERN = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
MAX_DAYS_AHEAD = 90
MAX_SLOTS = 500
MIN_SLOTS = 3


def _date(year: int, month: int, day: int, today) -> str | None:
    try:
        value = datetime(year, month, day, tzinfo=JST).date()
    except ValueError:
        return None
    if today <= value <= today + timedelta(days=MAX_DAYS_AHEAD):
        return value.isoformat()
    return None


def extract_from_lines(lines: list[str], today=None) -> list[tuple[str, str]]:
    """Strict parser for a date-header + subsequent times public availability list.

    Works only if each day heading is on its own short line and time choices
    follow it. It must not be applied to arbitrary page text including the
    booking widget. Verify against real DOM before enabling production use.
    """
    today = today or datetime.now(JST).date()
    active_date = None
    found: set[tuple[str, str]] = set()
    for raw in lines:
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        full = DATE_PATTERN.search(line)
        partial = MONTH_DAY_PATTERN.search(line) if full is None else None
        if full and len(line) <= 55:
            active_date = _date(*(int(x) for x in full.groups()), today=today)
        elif partial and len(line) <= 35:
            m, d = (int(x) for x in partial.groups())
            year = today.year + (m < today.month - 1)
            active_date = _date(year, m, d, today)
        elif re.match(r"^(?:日程|ご希望|学校名|学部名|氏名|メール|電話|同意|登録)", line) and len(line) > 40:
            active_date = None

        if active_date and len(line) <= 100:
            for hh, mm in TIME_PATTERN.findall(line):
                found.add((active_date, f"{int(hh):02d}:{mm}"))
        if len(found) > MAX_SLOTS:
            raise ValueError("Too many matches: refusing ambiguous extraction")
    return sorted(found)


async def _fill_school(page, field_name: str, value: str) -> None:
    """Try common label/placeholder based input controls without registration."""
    import re as _re
    candidate = page.get_by_role("combobox", name=_re.compile(field_name))
    if await candidate.count() == 0:
        candidate = page.get_by_role("textbox", name=_re.compile(field_name))
    if await candidate.count() == 0:
        candidate = page.get_by_placeholder(_re.compile(field_name))
    if await candidate.count() != 1:
        raise RuntimeError(f"Could not uniquely identify {field_name} field; DOM inspection required")
    field = candidate.first
    await field.fill(value)
    # Some forms require selecting the suggestion, not only typing text.
    await page.wait_for_timeout(900)
    option = page.get_by_role("option", name=_re.compile(re.escape(value)))
    if await option.count() == 1:
        await option.click()
        return
    button = page.get_by_role("button", name=_re.compile(re.escape(value)))
    if await button.count() == 1:
        await button.click()
        return
    await field.press("Tab")


async def fetch_lines(url: str) -> list[str]:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = await browser.new_page(locale="ja-JP", timezone_id="Asia/Tokyo")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await _fill_school(page, "学校名", os.environ.get("IRODAS_SCHOOL", "駒澤大学"))
            await _fill_school(page, "学部名", os.environ.get("IRODAS_FACULTY", "経済学部"))
            # Wait until the public availability prompt has finished loading.
            await page.get_by_text("空き状況を確認しています", exact=False).wait_for(
                state="hidden", timeout=20000
            )
            # Only inspect the public reference list, never the registration
            # screen or appointment iframe. The DOM selector must be confirmed.
            selector = os.environ.get("IRODAS_LIST_SELECTOR", "").strip()
            if not selector:
                raise RuntimeError(
                    "IRODAS_LIST_SELECTOR not configured. Ask Muse for the exact "
                    "DOM selector of the pre-registration reference list."
                )
            region = page.locator(selector)
            if await region.count() != 1:
                raise RuntimeError("List selector does not match exactly one element")
            text = await region.inner_text(timeout=15000)
            return text.splitlines()
        finally:
            await browser.close()


def main() -> int:
    url = os.environ.get("IRODAS_URL", DEFAULT_URL).strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "form.irodas.com":
        print("IRODAS_URL must point to https://form.irodas.com", file=sys.stderr)
        return 2
    try:
        import asyncio
        rows = asyncio.run(fetch_lines(url))
        pairs = extract_from_lines(rows)
        if len(pairs) < MIN_SLOTS:
            raise RuntimeError(
                f"Only {len(pairs)} date/time pairs extracted; refusing to replace stored data"
            )
        data = {
            "updated_at": datetime.now(JST).isoformat(),
            "source": "irodas",
            "slots": [
                {
                    "date": date, "time": time,
                    "title": "就活サポート面談",
                    "available": True, "url": url,
                }
                for date, time in pairs
            ],
            "note": (
                "登録前の参照一覧から自動取得した空き枠です（駒澤大学・経済学部）。"
                "予約時点の空き状況は公式サイトでご確認ください。"
            ),
        }
        # Atomic replacement only after extraction and validation succeed.
        temp = OUT.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(OUT)
        print(f"Successfully extracted {len(pairs)} available slots")
        return 0
    except Exception as exc:
        # Do not fabricate a successful timestamp, or erase the last snapshot.
        print(f"Could not safely fetch availability: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
