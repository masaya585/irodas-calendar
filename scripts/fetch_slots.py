#!/usr/bin/env python3
"""Read irodas' public pre-registration availability list.

Only fill the school and faculty fields. Never register, send personal data,
authenticate, or book an appointment. The browser-based parsing uses the
accessible roles and visible text observed in the Muse investigation on
2026-11-14; successful live execution still requires verification.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "slots.json"
JST = timezone(timedelta(hours=9))
DEFAULT_URL = "https://form.irodas.com/member/partner-call?dai_marketing=ds&chu_marketing=tre"
SCHOOL = os.environ.get("IRODAS_SCHOOL", "駒澤大学").strip()
FACULTY = os.environ.get("IRODAS_FACULTY", "経済学部").strip()

MONTH_HEADER = re.compile(r"(20\d{2})年\s*(1[0-2]|[1-9])月")
DATE_LINE = re.compile(r"^(1[0-2]|[1-9])月([1-9]|[12]\d|3[01])日\s*[\(（]([月火水木金土日])[\)）]$")
TIME_RANGE = re.compile(
    r"^([01]?\d|2[0-3]):([0-5]\d)\s*[〜～~]\s*([01]?\d|2[0-3]):([0-5]\d)$"
)
WEEKDAYS = "月火水木金土日"
MAX_SLOTS = 500


def parse_public_list(body_text: str, visible_terms: list[str], today: date | None = None) -> list[tuple[str, str]]:
    """Parse only date-labelled 60-minute slots from the pre-registration list.

    The widget's header supplies year/month; term-role dates anchor each group.
    Reject incomplete/ambiguous data instead of publishing a misleading update.
    """
    today = today or datetime.now(JST).date()
    before, marker, after = body_text.partition("60分の面談")
    if not marker:
        raise ValueError("Expected heading '60分の面談' was not found")
    months = MONTH_HEADER.findall(before)
    if not months:
        raise ValueError("Calendar year/month heading was not found")
    year, month = map(int, months[-1])

    term_labels = [re.sub(r"\s+", "", text) for text in visible_terms]
    if not term_labels or any(not DATE_LINE.fullmatch(t) for t in term_labels):
        raise ValueError("The visible date terms are missing or unexpected")
    if len(term_labels) != len(set(term_labels)):
        raise ValueError("Duplicate visible date terms")

    seen_days: set[str] = set()
    slots: set[tuple[str, str]] = set()
    current_day: date | None = None
    saw_calendar = False

    for original in after.splitlines():
        line = re.sub(r"\s+", " ", original).strip()
        if not line:
            continue
        day_match = DATE_LINE.fullmatch(re.sub(r"\s+", "", line))
        if day_match:
            m, d = int(day_match.group(1)), int(day_match.group(2))
            if m != month:
                raise ValueError(f"Unexpected month {m} inside {year}-{month} calendar")
            try:
                day = date(year, m, d)
            except ValueError as exc:
                raise ValueError("Invalid calendar date") from exc
            if WEEKDAYS[day.weekday()] != day_match.group(3):
                raise ValueError("Calendar weekday does not match date")
            seen_days.add(re.sub(r"\s+", "", line))
            current_day = day
            saw_calendar = True
            continue
        time_match = TIME_RANGE.fullmatch(line)
        if time_match and current_day is not None:
            h1, m1, h2, m2 = map(int, time_match.groups())
            start_minutes = h1 * 60 + m1
            end_minutes = h2 * 60 + m2
            if end_minutes - start_minutes != 60:
                raise ValueError(f"Unexpected meeting duration: {line}")
            if today <= current_day <= today + timedelta(days=90):
                slots.add((current_day.isoformat(), f"{h1:02d}:{m1:02d}"))
            continue
        if saw_calendar:
            # Unknown text can indicate we've left the public calendar.
            # Date headings and time ranges may still appear below; fail on
            # unexpected content instead of silently consuming other sections.
            if DATE_LINE.search(line) or TIME_RANGE.search(line):
                raise ValueError(f"Ambiguous calendar entry: {line[:80]}")
            if any(keyword in line for keyword in ("プライバシーポリシー", "個人情報", "©", "お問い合わせ")):
                break

    if set(term_labels) != seen_days:
        raise ValueError("Not all visible date headings were parsed")
    if not slots:
        raise ValueError("No future available time slots found; preserving previous snapshot")
    if len(slots) > MAX_SLOTS:
        raise ValueError("Implausibly many availability entries")
    return sorted(slots)


async def fetch_public_list(url: str) -> tuple[str, list[str]]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(locale="ja-JP", timezone_id="Asia/Tokyo")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            school = page.get_by_role("combobox", name="学校名", exact=True)
            faculty = page.get_by_role("combobox", name="学部名", exact=True)
            if await school.count() != 1 or await faculty.count() != 1:
                raise RuntimeError("Could not uniquely locate school/faculty comboboxes")
            # School first: editing school may clear faculty.
            await school.fill(SCHOOL)
            await faculty.fill(FACULTY)
            # The public date terms appear only after both fields are filled.
            await page.get_by_role("term").first.wait_for(state="visible", timeout=30000)
            # Give the dynamically rendered date rows a moment to settle.
            await page.wait_for_timeout(800)
            terms = await page.get_by_role("term").all_text_contents()
            body = await page.locator("body").inner_text(timeout=15000)
            return body, terms
        finally:
            await browser.close()


def main() -> int:
    url = os.environ.get("IRODAS_URL", DEFAULT_URL).strip()
    parsed_url = urlparse(url)
    if (parsed_url.scheme != "https" or parsed_url.hostname != "form.irodas.com"
            or parsed_url.path != "/member/partner-call" or parsed_url.username
            or parsed_url.password):
        print("Unsupported IRODAS_URL; expected official partner-call page", file=sys.stderr)
        return 2

    try:
        body_text, terms = asyncio.run(fetch_public_list(url))
        slots = parse_public_list(body_text, terms)
        now = datetime.now(JST)
        snapshot = {
            "updated_at": now.isoformat(),
            "source": "irodas",
            "slots": [
                {
                    "date": day,
                    "time": start,
                    "title": "就活サポート面談",
                    "available": True,
                    "url": url,
                }
                for day, start in slots
            ],
            "note": (
                "登録前の空き状況を駒澤大学・経済学部で取得しています。"
                "取得後に変更される場合があります。予約は必ず公式ページで確認してください。"
            ),
        }
        # Only publish after a validated parse. Atomic replace is important
        # when the script runs locally as well as in GitHub Actions.
        tmp = OUT.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(OUT)
        print(f"Validated public availability: {len(slots)} slots, {len(terms)} dates")
        return 0
    except Exception as exc:
        print(f"Public availability fetch failed; snapshot preserved: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
