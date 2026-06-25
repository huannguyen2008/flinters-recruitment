from __future__ import annotations

import pytest
from pathlib import Path

from src.reader import scan_ad_data

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_returns_lazy_frame():
    lf = scan_ad_data(FIXTURES / "sample.csv")
    import polars as pl
    assert isinstance(lf, pl.LazyFrame)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        scan_ad_data("/nonexistent/path/data.csv")


def test_malformed_rows_are_dropped():
    # malformed.csv has 4 data rows: 1 with non-numeric impressions, 1 with empty campaign_id
    # Only CMP001 and CMP002 rows are valid → 2 rows
    lf = scan_ad_data(FIXTURES / "malformed.csv")
    df = lf.collect()
    assert len(df) == 2
    assert set(df["campaign_id"].to_list()) == {"CMP001", "CMP002"}


def test_all_valid_rows_are_loaded():
    lf = scan_ad_data(FIXTURES / "sample.csv")
    df = lf.collect()
    assert len(df) == 7
