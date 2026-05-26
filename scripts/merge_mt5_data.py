#!/usr/bin/env python3
"""Merge two MT5 CSV exports, dedup, sort chronologically.

Original raw files are never overwritten — output goes to a separate path.

Usage:
    python scripts/merge_mt5_data.py \
        --base data/raw/XAUUSD_M15.csv \
        --new  "data/raw/XAUUSD_M15_New 26.csv" \
        --out  data/raw/XAUUSD_M15_merged.csv
"""

import argparse
import csv
import sys
from pathlib import Path


HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"


def parse_rows(path: Path) -> dict[tuple[str, str], str]:
    rows: dict[tuple[str, str], str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("<DATE>"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            key = (parts[0], parts[1])
            rows[key] = line
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base_path = Path(args.base)
    new_path = Path(args.new)
    out_path = Path(args.out)

    if not base_path.exists():
        sys.exit(f"Base file not found: {base_path}")
    if not new_path.exists():
        sys.exit(f"New file not found: {new_path}")
    if out_path.exists():
        sys.exit(f"Output already exists: {out_path}  — delete it first to prevent accidental overwrite")

    base_rows = parse_rows(base_path)
    new_rows = parse_rows(new_path)

    added = len(set(new_rows) - set(base_rows))
    merged = {**base_rows, **new_rows}

    sorted_keys = sorted(merged.keys())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(HEADER + "\n")
        for key in sorted_keys:
            f.write(merged[key] + "\n")

    print(f"Base rows  : {len(base_rows)}")
    print(f"New rows   : {len(new_rows)}")
    print(f"Added (net): {added}")
    print(f"Total      : {len(merged)}")
    print(f"Written to : {out_path}")
    print()
    print("Next — run import-csv to validate the merged file:")
    print(f"  PYTHONPATH=src venv/bin/python -m tar_system.cli import-csv --file {out_path} --symbol XAUUSD --timeframe M15")


if __name__ == "__main__":
    main()
