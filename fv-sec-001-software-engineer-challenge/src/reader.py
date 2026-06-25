from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)

_SCHEMA = {
    "campaign_id": pl.String,
    "date": pl.String,
    "impressions": pl.Int64,
    "clicks": pl.Int64,
    "spend": pl.Float64,
    "conversions": pl.Int64,
}

_REQUIRED = ["campaign_id", "impressions", "clicks", "spend", "conversions"]


def scan_ad_data(input_path: str | Path) -> pl.LazyFrame:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    lf = pl.scan_csv(path, schema=_SCHEMA, ignore_errors=True)
    # Rows where numeric parsing failed become null — drop them
    return lf.drop_nulls(subset=_REQUIRED)
