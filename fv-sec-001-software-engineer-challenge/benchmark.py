#!/usr/bin/env python3
"""Benchmark the aggregation pipeline: wall-clock time over N trials and peak RSS.

Run a single engine in a fresh process so the reported peak memory is attributable
to that engine only:

    python benchmark.py --input ad_data.csv --engine streaming --trials 3
    python benchmark.py --input ad_data.csv --engine in-memory --trials 3
"""
from __future__ import annotations

import argparse
import os
import platform
import resource
import statistics
import sys
import time

import polars as pl

from src.aggregator import aggregate_by_campaign
from src.reader import scan_ad_data


def _peak_rss_mb() -> float:
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if platform.system() == "Darwin" else peak / 1024


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the ad aggregation pipeline.")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument(
        "--engine",
        default="streaming",
        choices=["streaming", "in-memory"],
        help="Polars collect engine to benchmark (default: streaming)",
    )
    parser.add_argument("--trials", type=int, default=3, help="Number of timed trials")
    args = parser.parse_args()

    size_mb = os.path.getsize(args.input) / (1024 * 1024)

    print("=" * 60)
    print("Ad Performance Aggregator — Benchmark")
    print("=" * 60)
    print(f"Timestamp     : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform      : {platform.platform()}")
    print(f"Python        : {platform.python_version()}")
    print(f"Polars        : {pl.__version__}")
    print(f"CPU cores      : {os.cpu_count()}")
    print(f"Input file    : {args.input} ({size_mb:.0f} MB)")
    print(f"Engine        : {args.engine}")
    print(f"Trials        : {args.trials}")
    print("-" * 60)

    times: list[float] = []
    n_campaigns = 0
    for i in range(args.trials):
        lf = scan_ad_data(args.input)
        start = time.perf_counter()
        df = aggregate_by_campaign(lf, engine=args.engine)
        elapsed = time.perf_counter() - start
        n_campaigns = len(df)
        times.append(elapsed)
        print(f"  trial {i + 1}: {elapsed:6.3f} s")

    print("-" * 60)
    print(f"Campaigns     : {n_campaigns}")
    print(f"Min time      : {min(times):.3f} s")
    print(f"Mean time     : {statistics.mean(times):.3f} s")
    if len(times) > 1:
        print(f"Stdev         : {statistics.stdev(times):.3f} s")
    print(f"Throughput    : {size_mb / min(times):.0f} MB/s (best trial)")
    print(f"Peak RSS      : {_peak_rss_mb():.0f} MB")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
