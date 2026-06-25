#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
import time

from src.aggregator import aggregate_by_campaign
from src.metrics import top10_by_ctr, top10_by_cpa
from src.reader import scan_ad_data
from src.writer import write_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ad Performance Aggregator — processes a large ad-data CSV and outputs top-10 reports."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file (e.g. ad_data.csv)")
    parser.add_argument("--output", required=True, help="Path to output directory (e.g. results/)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    try:
        t0 = time.perf_counter()

        logger.info("Scanning %s", args.input)
        lf = scan_ad_data(args.input)

        logger.info("Aggregating by campaign_id")
        aggregated = aggregate_by_campaign(lf)
        logger.info("Unique campaigns: %d", len(aggregated))

        logger.info("Computing top-10 CTR and top-10 CPA")
        ctr_df = top10_by_ctr(aggregated)
        cpa_df = top10_by_cpa(aggregated)

        logger.info("Writing results to %s", args.output)
        write_results(ctr_df, cpa_df, args.output)

        elapsed = time.perf_counter() - t0
        logger.info("Done in %.2fs", elapsed)

    except FileNotFoundError as exc:
        logging.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
