from __future__ import annotations

import polars as pl


def aggregate_by_campaign(lf: pl.LazyFrame, engine: str = "streaming") -> pl.DataFrame:
    return (
        lf.group_by("campaign_id")
        .agg(
            pl.col("impressions").sum().alias("total_impressions"),
            pl.col("clicks").sum().alias("total_clicks"),
            pl.col("spend").sum().alias("total_spend"),
            pl.col("conversions").sum().alias("total_conversions"),
        )
        .with_columns(
            # Guard against zero impressions to avoid inf/NaN
            pl.when(pl.col("total_impressions") > 0)
            .then(pl.col("total_clicks") / pl.col("total_impressions"))
            .otherwise(None)
            .alias("CTR"),
            pl.when(pl.col("total_conversions") > 0)
            .then(pl.col("total_spend") / pl.col("total_conversions"))
            .otherwise(None)
            .alias("CPA"),
        )
        # The streaming engine (default) processes the file in chunks, keeping peak
        # memory well below the full file size instead of materializing it all at once.
        .collect(engine=engine)
    )
