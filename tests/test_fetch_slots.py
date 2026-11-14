"""Offline parser checks using the 2026-11-14 observed page wording."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_slots import parse_public_list


class AvailabilityParserTests(unittest.TestCase):
    def test_observed_japanese_text(self):
        text = """学校名
サンプル大学
学部名
サンプル学部
面談の空き状況
空き状況の参照のみです。
日本時間で表示しています。
前の月
2026年11月
次の月
60分の面談
11月16日(月)
14:00〜15:00
16:00〜17:00
17:00〜18:00
11月17日(火)
10:00〜11:00
11:00〜12:00
"""
        result = parse_public_list(text, ["11月16日(月)", "11月17日(火)"], today=date(2026, 11, 14))
        self.assertEqual(result, [
            ("2026-11-16", "14:00"), ("2026-11-16", "16:00"),
            ("2026-11-16", "17:00"), ("2026-11-17", "10:00"),
            ("2026-11-17", "11:00"),
        ])

    def test_rejects_mismatched_term_count(self):
        text = "2026年11月\n60分の面談\n11月16日(月)\n14:00〜15:00"
        with self.assertRaises(ValueError):
            parse_public_list(text, ["11月16日(月)", "11月17日(火)"], today=date(2026, 11, 14))

    def test_rejects_bad_weekday(self):
        text = "2026年11月\n60分の面談\n11月16日(火)\n14:00〜15:00"
        with self.assertRaises(ValueError):
            parse_public_list(text, ["11月16日(火)"], today=date(2026, 11, 14))

    def test_rejects_zero_future_slots(self):
        text = "2026年11月\n60分の面談\n11月16日(月)\n14:00〜15:00"
        with self.assertRaises(ValueError):
            parse_public_list(text, ["11月16日(月)"], today=date(2026, 11, 20))


if __name__ == "__main__":
    unittest.main()
