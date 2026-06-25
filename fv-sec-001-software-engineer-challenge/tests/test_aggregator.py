from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.aggregator import aggregate_by_campaign
from src.reader import scan_ad_data

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def aggregated():
    lf = scan_ad_data(FIXTURES / "sample.csv")
    return aggregate_by_campaign(lf)


def _row(df: pl.DataFrame, campaign_id: str) -> dict:
    return df.filter(pl.col("campaign_id") == campaign_id).to_dicts()[0]


def test_campaign_count(aggregated):
    assert len(aggregated) == 5


def test_totals_cmp001(aggregated):
    row = _row(aggregated, "CMP001")
    assert row["total_impressions"] == 30000
    assert row["total_clicks"] == 1300
    assert row["total_spend"] == pytest.approx(300.00)
    assert row["total_conversions"] == 30


def test_ctr_cmp001(aggregated):
    row = _row(aggregated, "CMP001")
    assert row["CTR"] == pytest.approx(1300 / 30000)


def test_cpa_cmp001(aggregated):
    row = _row(aggregated, "CMP001")
    assert row["CPA"] == pytest.approx(300.00 / 30)


def test_cpa_null_when_zero_conversions(aggregated):
    row = _row(aggregated, "CMP002")
    assert row["CPA"] is None


def test_ctr_highest_is_cmp003(aggregated):
    # CMP003: 100/1000 = 0.10 — highest in fixture
    row = _row(aggregated, "CMP003")
    assert row["CTR"] == pytest.approx(0.10)


def test_ctr_zero_impressions_is_null():
    import polars as pl
    from src.aggregator import aggregate_by_campaign

    lf = pl.LazyFrame(
        {"campaign_id": ["CMP_ZERO"], "date": ["2025-01-01"],
         "impressions": [0], "clicks": [0], "spend": [0.0], "conversions": [0]}
    )
    df = aggregate_by_campaign(lf)
    assert df["CTR"][0] is None
