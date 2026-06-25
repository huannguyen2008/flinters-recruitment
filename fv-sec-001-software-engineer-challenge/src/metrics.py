from __future__ import annotations

import polars as pl

_COLUMNS = [
    "campaign_id",
    "total_impressions",
    "total_clicks",
    "total_spend",
    "total_conversions",
    "CTR",
    "CPA",
]


def top10_by_ctr(df: pl.DataFrame) -> pl.DataFrame:
    return df.sort("CTR", descending=True).head(10).select(_COLUMNS)


def top10_by_cpa(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.filter(pl.col("total_conversions") > 0)
        .sort("CPA", descending=False)
        .head(10)
        .select(_COLUMNS)
    )
