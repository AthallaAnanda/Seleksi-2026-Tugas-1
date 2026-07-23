"""Safety-net unit tests untuk fungsi murni (tanpa koneksi DB) di load_data.py.

Fixture di bawah meniru kasus nyata yang didokumentasikan di komentar
BUG 1-7 pada load_data.py, supaya refactor (ekstrak blok inline jadi
fungsi bernama) tidak diam-diam mengubah behavior.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from load_data import (  # noqa: E402
    aggregate_duplicates,
    dedupe_isin_code,
    filter_sentinel_zero_rankings,
    fix_negative_min_next_subscription,
    fix_policy_pct_range,
    fix_treynor_outlier,
    fix_unreasonable_fees,
    resolve_snapshot_rows,
)


class TestAggregateDuplicates:
    def test_sums_value_pct_for_shared_key(self):
        # BUG 7: fund 1717 @2026-06-30, category_id=0 muncul dua kali.
        rows = [
            {"snapshot_ref": (1717, "2026-06-30"), "category_id": 0, "value_pct": 69.9},
            {"snapshot_ref": (1717, "2026-06-30"), "category_id": 0, "value_pct": 21.8},
        ]
        result = aggregate_duplicates(rows, "category_id")
        assert len(result) == 1
        assert result[0]["value_pct"] == 91.7

    def test_no_duplicates_passthrough(self):
        rows = [
            {"snapshot_ref": (1, "2026-01-01"), "category_id": 0, "value_pct": 50.0},
            {"snapshot_ref": (1, "2026-01-01"), "category_id": 1, "value_pct": 50.0},
        ]
        result = aggregate_duplicates(rows, "category_id")
        assert len(result) == 2


class TestResolveSnapshotRows:
    def test_resolves_known_snapshot_ref(self):
        snap_map = {(1, "2026-01-01"): 42}
        rows = [{"snapshot_ref": (1, "2026-01-01"), "category_id": 0, "value_pct": 100.0}]
        result = resolve_snapshot_rows(rows, snap_map)
        assert result == [{"snapshot_ref": (1, "2026-01-01"), "category_id": 0,
                            "value_pct": 100.0, "snapshot_id": 42}]

    def test_missing_snapshot_ref_is_dropped(self):
        rows = [{"snapshot_ref": (999, "2026-01-01"), "category_id": 0, "value_pct": 100.0}]
        result = resolve_snapshot_rows(rows, {})
        assert result == []


class TestFixNegativeMinNextSubscription:
    def test_negative_sentinel_becomes_none(self):
        # BUG 2: fund_id=4374 min_next_subscription=-1
        funds = [{"fund_id": 4374, "min_next_subscription": -1}]
        fix_negative_min_next_subscription(funds)
        assert funds[0]["min_next_subscription"] is None

    def test_positive_value_untouched(self):
        funds = [{"fund_id": 1, "min_next_subscription": 100000}]
        fix_negative_min_next_subscription(funds)
        assert funds[0]["min_next_subscription"] == 100000

    def test_none_value_untouched(self):
        funds = [{"fund_id": 1, "min_next_subscription": None}]
        fix_negative_min_next_subscription(funds)
        assert funds[0]["min_next_subscription"] is None


class TestFixUnreasonableFees:
    FEE_FIELDS = ["sub_fee_max_pct", "red_fee_max_pct"]

    def test_fee_over_100_becomes_none(self):
        # BUG 3: fund_id=1281 red_fee_max_pct=200.0
        funds = [{"fund_id": 1281, "sub_fee_max_pct": 1.0, "red_fee_max_pct": 200.0}]
        fix_unreasonable_fees(funds, self.FEE_FIELDS)
        assert funds[0]["red_fee_max_pct"] is None
        assert funds[0]["sub_fee_max_pct"] == 1.0

    def test_fee_exactly_100_is_nulled(self):
        funds = [{"fund_id": 1, "sub_fee_max_pct": 100.0, "red_fee_max_pct": 3.0}]
        fix_unreasonable_fees(funds, self.FEE_FIELDS)
        assert funds[0]["sub_fee_max_pct"] is None


class TestDedupeIsinCode:
    def test_first_occurrence_kept_second_nulled(self):
        # BUG 4: dua kelas berbagi isin_code sama persis.
        funds = [
            {"fund_id": 5591, "isin_code": "IDN000123456"},
            {"fund_id": 5592, "isin_code": "IDN000123456"},
        ]
        dedupe_isin_code(funds)
        assert funds[0]["isin_code"] == "IDN000123456"
        assert funds[1]["isin_code"] is None

    def test_none_isin_untouched(self):
        funds = [{"fund_id": 1, "isin_code": None}]
        dedupe_isin_code(funds)
        assert funds[0]["isin_code"] is None


class TestFixPolicyPctRange:
    POLICY_FIELDS = ["policy_bond_pct", "policy_equity_pct", "policy_money_market_pct"]

    def test_out_of_range_field_nulled(self):
        # BUG 5: fund 2113 equity=102.52 & money_market=-2.52
        funds = [{"fund_id": 2113, "policy_bond_pct": 0.0,
                  "policy_equity_pct": 102.52, "policy_money_market_pct": -2.52}]
        fix_policy_pct_range(funds, self.POLICY_FIELDS)
        assert funds[0]["policy_equity_pct"] is None
        assert funds[0]["policy_money_market_pct"] is None
        assert funds[0]["policy_bond_pct"] == 0.0

    def test_in_range_values_untouched(self):
        funds = [{"fund_id": 1, "policy_bond_pct": 40.0,
                  "policy_equity_pct": 60.0, "policy_money_market_pct": 0.0}]
        fix_policy_pct_range(funds, self.POLICY_FIELDS)
        assert funds[0]["policy_equity_pct"] == 60.0


class TestFixTreynorOutlier:
    def test_extreme_ratio_becomes_none(self):
        # BUG 6: treynor_ratio meledak jadi ribuan saat beta~0.
        performances = [{"fund_id": 1, "treynor_ratio": -30098.0}]
        fix_treynor_outlier(performances)
        assert performances[0]["treynor_ratio"] is None

    def test_normal_ratio_untouched(self):
        performances = [{"fund_id": 1, "treynor_ratio": 12.5}]
        fix_treynor_outlier(performances)
        assert performances[0]["treynor_ratio"] == 12.5

    def test_none_ratio_untouched(self):
        performances = [{"fund_id": 1, "treynor_ratio": None}]
        fix_treynor_outlier(performances)
        assert performances[0]["treynor_ratio"] is None


class TestFilterSentinelZeroRankings:
    ZERO_FIELDS = ["risk_rank", "rating_rank", "all_risk_rank",
                   "pasardana_rating", "risk_rating", "all_risk_rating"]

    def test_all_zero_row_is_skipped(self):
        # BUG 1: 302 baris sentinel "belum ada ranking periode ini".
        rankings = [{f: 0 for f in self.ZERO_FIELDS} | {"fund_id": 1}]
        result = filter_sentinel_zero_rankings(rankings, self.ZERO_FIELDS)
        assert result == []

    def test_row_with_real_data_kept(self):
        row = {f: 0 for f in self.ZERO_FIELDS} | {"fund_id": 1, "risk_rank": 3}
        result = filter_sentinel_zero_rankings([row], self.ZERO_FIELDS)
        assert result == [row]
