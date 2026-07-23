"""Safety-net unit tests untuk fungsi parsing murni di preprocessor.py.

Dijalankan sebelum & sesudah refactor Clean Code (naming/docstring/type
hint/extract-constant) untuk memastikan behavior tidak berubah.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessor import (  # noqa: E402
    _is_dash,
    end_of_month,
    latest_nav_date,
    parse_date,
    parse_fee_pct,
    parse_float,
    parse_int,
    parse_str_or_none,
)


class TestIsDash:
    def test_none_is_dash(self):
        assert _is_dash(None) is True

    def test_single_dash_is_dash(self):
        assert _is_dash("-") is True

    def test_dash_with_whitespace_is_dash(self):
        assert _is_dash("  -  ") is True

    def test_real_value_is_not_dash(self):
        assert _is_dash("Jakarta") is False


class TestParseStrOrNone:
    def test_dash_becomes_none(self):
        assert parse_str_or_none("-") is None

    def test_none_stays_none(self):
        assert parse_str_or_none(None) is None

    def test_whitespace_only_becomes_none(self):
        assert parse_str_or_none("   ") is None

    def test_trims_value(self):
        assert parse_str_or_none("  Jakarta  ") == "Jakarta"

    def test_dash_null_false_keeps_dash(self):
        assert parse_str_or_none("-", dash_null=False) == "-"


class TestParseInt:
    def test_none_is_none(self):
        assert parse_int(None) is None

    def test_plain_int(self):
        assert parse_int(5000) == 5000

    def test_float_truncated(self):
        assert parse_int(5000.7) == 5000

    def test_rp_thousands_separator(self):
        assert parse_int("Rp 1.000.000") == 1000000

    def test_bare_dash_is_none(self):
        assert parse_int("-") is None

    def test_empty_string_is_none(self):
        assert parse_int("") is None

    def test_negative_value(self):
        assert parse_int("-500") == -500


class TestParseFloat:
    def test_none_is_none(self):
        assert parse_float(None) is None

    def test_plain_float(self):
        assert parse_float(12.5) == 12.5

    def test_int_becomes_float(self):
        assert parse_float(12) == 12.0

    def test_european_decimal_comma(self):
        assert parse_float("2,00%") == 2.0

    def test_dash_is_none(self):
        assert parse_float("-") is None


class TestParseFeePct:
    def test_none_is_none(self):
        assert parse_fee_pct(None) is None

    def test_text_prefixed_fee(self):
        assert parse_fee_pct("Maks 0,30%") == 0.30

    def test_plain_percent(self):
        assert parse_fee_pct("2,000%") == 2.000

    def test_unparseable_is_none(self):
        assert parse_fee_pct("n/a") is None


class TestParseDate:
    def test_falsy_is_none(self):
        assert parse_date(None) is None
        assert parse_date("") is None

    def test_iso_datetime_truncated(self):
        assert parse_date("2005-05-25T00:00:00") == "2005-05-25"

    def test_ddmmyyyy_converted_to_iso(self):
        assert parse_date("18-08-2023") == "2023-08-18"

    def test_unknown_format_kept_as_is(self):
        assert parse_date("not-a-date") == "not-a-date"


class TestEndOfMonth:
    def test_30_day_month(self):
        assert end_of_month("2026-06-05") == "2026-06-30"

    def test_31_day_month(self):
        assert end_of_month("2026-07-01") == "2026-07-31"

    def test_february_leap_year(self):
        assert end_of_month("2024-02-10") == "2024-02-29"

    def test_february_non_leap_year(self):
        assert end_of_month("2026-02-10") == "2026-02-28"


class TestLatestNavDate:
    def test_no_nav_values_is_none(self):
        assert latest_nav_date({"NetAssetValues": []}) is None

    def test_missing_key_is_none(self):
        assert latest_nav_date({}) is None

    def test_picks_max_date(self):
        snap = {"NetAssetValues": [
            {"Date": "2026-01-10"},
            {"Date": "2026-03-05"},
            {"Date": "2026-02-20"},
        ]}
        assert latest_nav_date(snap) == "2026-03-05"
