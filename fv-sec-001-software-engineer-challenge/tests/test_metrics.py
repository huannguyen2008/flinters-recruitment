from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.aggregator import aggregate_by_campaign
from src.metrics import top10_by_ctr, top10_by_cpa
from src.reader import scan_ad_data

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def aggregated():
    lf = scan_ad_data(FIXTURES / "sample.csv")
    return aggregate_by_campaign(lf)


def test_top10_ctr_first_row_is_highest(aggregated):
    result = top10_by_ctr(aggregated)
    assert result["campaign_id"][0] == "CMP003"  # CTR = 0.10


def test_top10_ctr_descending_order(aggregated):
    result = top10_by_ctr(aggregated)
    ctrs = result["CTR"].to_list()
    assert ctrs == sorted(ctrs, reverse=True)


def test_top10_ctr_returns_at_most_10():
    rows = [{"campaign_id": f"C{i}", "date": "2025-01-01",
              "impressions": 1000, "clicks": i, "spend": float(i), "conversions": 1}
             for i in range(1, 20)]
    lf = pl.LazyFrame(rows)
    df = aggregate_by_campaign(lf)
    result = top10_by_ctr(df)
    assert len(result) <= 10


def test_top10_ctr_columns(aggregated):
    result = top10_by_ctr(aggregated)
    assert list(result.columns) == [
        "campaign_id", "total_impressions", "total_clicks",
        "total_spend", "total_conversions", "CTR", "CPA",
    ]


def test_top10_cpa_excludes_zero_conversions(aggregated):
    result = top10_by_cpa(aggregated)
    assert all(v > 0 for v in result["total_conversions"].to_list())


def test_top10_cpa_ascending_order(aggregated):
    result = top10_by_cpa(aggregated)
    cpas = result["CPA"].to_list()
    assert cpas == sorted(cpas)


def test_top10_cpa_returns_at_most_10(aggregated):
    result = top10_by_cpa(aggregated)
    assert len(result) <= 10


def test_top10_cpa_campaign_ids(aggregated):
    # Only CMP001, CMP003, CMP004 have conversions > 0
    result = top10_by_cpa(aggregated)
    ids = set(result["campaign_id"].to_list())
    assert ids == {"CMP001", "CMP003", "CMP004"}
