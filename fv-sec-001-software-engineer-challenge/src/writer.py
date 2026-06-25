from __future__ import annotations

from pathlib import Path

import polars as pl

# Fixed decimal places per output column, matching the README's "Expected output
# format" (CTR -> 4 dp, CPA & total_spend -> 2 dp). Formatting is applied only at
# write time so ranking/sorting still uses full-precision values.
_DECIMALS = {"total_spend": 2, "CTR": 4, "CPA": 2}


def _format_for_output(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col(col)
        .map_elements(
            lambda v, d=decimals: "" if v is None else f"{v:.{d}f}",
            return_dtype=pl.String,
        )
        .alias(col)
        for col, decimals in _DECIMALS.items()
    )


def write_results(
    ctr_df: pl.DataFrame,
    cpa_df: pl.DataFrame,
    output_dir: str | Path,
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    _format_for_output(ctr_df).write_csv(out / "top10_ctr.csv")
    _format_for_output(cpa_df).write_csv(out / "top10_cpa.csv")
