from __future__ import annotations

import tempfile
from pathlib import Path

import polars as pl

from src.writer import write_results


def _make_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "campaign_id": ["CMP001"],
            "total_impressions": [30000],
            "total_clicks": [1300],
            "total_spend": [300.0],
            "total_conversions": [30],
            "CTR": [1300 / 30000],
            "CPA": [10.0],
        }
    )


def test_output_files_are_created():
    df = _make_df()
    with tempfile.TemporaryDirectory() as tmp:
        write_results(df, df, tmp)
        assert (Path(tmp) / "top10_ctr.csv").exists()
        assert (Path(tmp) / "top10_cpa.csv").exists()


def test_output_dir_is_created_if_missing():
    df = _make_df()
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "nested" / "output"
        write_results(df, df, nested)
        assert (nested / "top10_ctr.csv").exists()


def test_csv_content_is_correct():
    df = _make_df()
    with tempfile.TemporaryDirectory() as tmp:
        write_results(df, df, tmp)
        result = pl.read_csv(Path(tmp) / "top10_ctr.csv")
        assert result["campaign_id"][0] == "CMP001"
        assert result["total_impressions"][0] == 30000


def test_output_columns_use_fixed_decimals():
    df = _make_df()
    with tempfile.TemporaryDirectory() as tmp:
        write_results(df, df, tmp)
        # Read raw text so we can assert exact formatting (trailing zeros preserved)
        lines = (Path(tmp) / "top10_ctr.csv").read_text().splitlines()
        header, row = lines[0].split(","), lines[1].split(",")
        cells = dict(zip(header, row))
        assert cells["CTR"] == "0.0433"      # 1300/30000 -> 4 dp
        assert cells["CPA"] == "10.00"       # 2 dp, trailing zeros kept
        assert cells["total_spend"] == "300.00"


def test_null_cpa_renders_as_empty():
    df = _make_df().with_columns(pl.lit(None, dtype=pl.Float64).alias("CPA"))
    with tempfile.TemporaryDirectory() as tmp:
        write_results(df, df, tmp)
        lines = (Path(tmp) / "top10_ctr.csv").read_text().splitlines()
        cells = dict(zip(lines[0].split(","), lines[1].split(",")))
        assert cells["CPA"] == ""
