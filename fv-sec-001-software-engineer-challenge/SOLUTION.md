# Solution — Ad Performance Aggregator

## Quick Start (Docker — no local Python needed)

The only requirement is **Docker** (with Compose, which ships with Docker Desktop).
You do **not** need Python or any packages installed locally.

```bash
# 1. Unzip the dataset (produces ad_data.csv in this folder)
unzip ad_data.csv.zip

# 2. Run the aggregator — builds the image on first run
docker compose run --rm aggregator
```

The project folder is mounted into the container, so:
- the unzipped `ad_data.csv` is picked up automatically, and
- the results are written back to `./results/` on your machine:
  - `results/top10_ctr.csv` — top 10 campaigns by highest CTR (descending)
  - `results/top10_cpa.csv` — top 10 campaigns by lowest CPA (ascending, zero-conversion campaigns excluded)

### Run the tests (also in Docker)

```bash
docker compose run --rm test
```

### Custom input/output paths

`aggregator` is the default command; override the arguments to point elsewhere:

```bash
docker compose run --rm aggregator --input some_other.csv --output results/
```

---

## Alternative: run locally without Docker

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
unzip ad_data.csv.zip
python aggregator.py --input ad_data.csv --output results/

# Tests
pytest tests/ -v
```

## Libraries Used

| Library | Version | Purpose |
|---------|---------|---------|
| [polars](https://pola.rs/) | ≥ 0.20 | Lazy CSV scanning and aggregation |
| [pytest](https://pytest.org/) | ≥ 7.4 | Unit testing |

## Design Decisions

### Why Polars?

Polars' `scan_csv()` builds a lazy query plan instead of loading the file. The entire pipeline (scan → group_by → aggregate → with_columns) is then executed with `.collect(engine="streaming")`, which processes the file in chunks using multi-threading and predicate pushdown. This keeps peak memory well below the full file size — measured at ~1.3 GB for the ~1 GB / 26.8M-row dataset, versus ~2.8 GB with the default eager engine (a ~54% reduction).

Alternatives considered:
- **pandas** — loads the full file into memory by default; chunking requires manual bookkeeping
- **Python `csv` module** — zero dependencies but requires manual aggregation with `defaultdict` and is single-threaded

### Error handling for malformed rows

Rows where a numeric column cannot be parsed (e.g. corrupted values) are converted to `null` by Polars (`ignore_errors=True`) and then dropped via `drop_nulls`. This makes the program resilient to partially corrupted files without aborting the entire run.

### CPA null for zero conversions

The spec says "ignore or return null for CPA" when `conversions = 0`. We store `null` in the `CPA` column and exclude those campaigns from `top10_cpa.csv` entirely, matching the expected output format.

### Zero-impression guard

If a campaign somehow has `total_impressions = 0`, CTR is set to `null` rather than producing `inf` or `NaN`, which would break CSV output and downstream tooling.

### Output number formatting

The README's result tables are labelled *"Expected output **format**"* and contain
illustrative (fabricated) campaign values, so they show the intended column layout and
rounding rather than the actual answers for this dataset. To match that format, the output
CSVs render **CTR to 4 decimals** and **CPA / total_spend to 2 decimals**, with trailing
zeros preserved (e.g. `0.0275`, `19.35`, `395992597.40`). Formatting is applied only at
write time, so ranking and tie-breaking still use full-precision values. A `null` CPA
(zero-conversion campaign) is written as an empty field.

## Performance

Measured on the real dataset (`ad_data.csv`: 995 MB, 26,843,544 rows, 50 campaigns),
running inside the Docker container (`python:3.11-slim`, Polars 1.42, 12 cores) on an
Apple Silicon MacBook Pro. Full output is captured in [`docs/benchmark.log`](docs/benchmark.log).

| Metric | Streaming engine (default) | In-memory engine (comparison) |
|--------|----------------------------|-------------------------------|
| Aggregation time (best of 3) | ~0.9 s | ~1.0 s |
| Throughput | ~1.1 GB/s | ~1.0 GB/s |
| Peak RSS | **~1.8 GB** | ~2.8 GB |
| End-to-end CLI run (scan + aggregate + write) | ~1.0–1.6 s | — |

The streaming engine delivers the same speed at **~35% lower peak memory**, which is the
relevant win for the ~1 GB input. Memory was measured via
`resource.getrusage(RUSAGE_SELF).ru_maxrss`; numbers vary with hardware and core count.

### Reproduce the benchmark

```bash
docker compose run --rm benchmark --input ad_data.csv --engine streaming --trials 3
docker compose run --rm benchmark --input ad_data.csv --engine in-memory --trials 3
```

## Project Structure

```
aggregator.py          # CLI entry point (argparse)
benchmark.py           # time + peak-memory benchmark harness
src/
  reader.py            # scan_csv() with schema enforcement and error filtering
  aggregator.py        # group_by + metric computation (single collect pass)
  metrics.py           # top-10 ranking logic
  writer.py            # CSV output (fixed-decimal formatting)
tests/
  fixtures/
    sample.csv         # 7-row known-value fixture
    malformed.csv      # fixture with intentionally bad rows
  test_reader.py
  test_aggregator.py
  test_metrics.py
  test_writer.py
docs/
  architecture.svg     # architecture/plan diagram
  benchmark.log        # captured benchmark output
results/               # output directory (gitignored except .gitkeep)
requirements.txt
Dockerfile
docker-compose.yml
PROMPTS.md
```
