#!/usr/bin/env python3
"""Queue and optionally process all local CSV data across canonical strategies.

This is paper-only orchestration. It uses the local DuckDB job queue, local CSV
files under data/raw, and local reports/results. It does not use cloud services,
broker APIs, or live trading.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.controller.data_watcher import parse_asset_file
from tar_system.controller.job_queue import (
    active_job_keys,
    add_job,
    make_active_job_key,
    queue_stats,
)
from tar_system.controller.worker import run_worker
from tar_system.dashboard.runtime_control import has_tested_data
from tar_system.data.csv_importer import hash_csv_file


CANONICAL_STRATEGIES = [
    "gold_v2",
    "rsi_reversion_v1",
    "goldv2_v2",
    "rsi_only_v3",
    "ema_volume_v3",
    "atr_breakout_v3",
    "momentum_crossover_v3",
    "multi_timeframe_v3",
    "ema_volume_fixed",
    "atr_breakout_fixed",
    "liquidity_sweep_v1",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all local data through all canonical paper strategies.")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--broker", default="current_broker_demo")
    parser.add_argument("--stage", default="continuous_all_strategies")
    parser.add_argument("--force", action="store_true", help="Queue even if this data hash was already tested.")
    parser.add_argument("--run", action="store_true", help="Process queued jobs after queueing.")
    parser.add_argument("--limit", type=int, default=100000, help="Maximum worker jobs to process when --run is used.")
    parser.add_argument("--skip-walk-forward", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--skip-forward-test", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-walk-forward-splits", type=int, default=10)
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--summary-path", default=None)
    args = parser.parse_args()

    queued = queue_all_jobs(args)
    worker_result = run_worker(args.limit) if args.run else None
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "raw_dir": args.raw_dir,
        "strategy_count": len(CANONICAL_STRATEGIES),
        "strategies": CANONICAL_STRATEGIES,
        "queued": queued,
        "worker": worker_result.__dict__ if worker_result else None,
        "queue_stats": queue_stats(),
    }
    path = write_summary(summary, args.summary_path)
    print(json.dumps({"summary_path": str(path), "queue_stats": summary["queue_stats"], "worker": summary["worker"]}, indent=2, default=str))
    return 0


def queue_all_jobs(args: argparse.Namespace) -> dict[str, Any]:
    raw_files = sorted(Path(args.raw_dir).glob("*_*.csv"))
    active = active_job_keys()
    queued_jobs: list[dict[str, Any]] = []
    skipped_active = 0
    skipped_tested = 0
    skipped_unparsed = 0

    for path in raw_files:
        parsed = parse_asset_file(path.name)
        if parsed is None:
            skipped_unparsed += 1
            continue
        symbol, timeframe = parsed
        data_hash = hash_csv_file(path)
        for strategy in CANONICAL_STRATEGIES:
            if (
                not args.force
                and has_tested_data(strategy, symbol, timeframe, data_hash, "full_pipeline", args.from_date, args.to_date)
            ):
                skipped_tested += 1
                continue
            key = make_active_job_key(
                strategy,
                symbol,
                timeframe,
                str(path),
                data_hash=data_hash,
                from_date=args.from_date,
                to_date=args.to_date,
                research_stage=args.stage,
            )
            if key in active:
                skipped_active += 1
                continue
            queued_jobs.append(
                add_job(
                    strategy,
                    symbol,
                    timeframe,
                    str(path),
                    args.broker,
                    priority=200,
                    data_hash=data_hash,
                    from_date=args.from_date,
                    to_date=args.to_date,
                    skip_walk_forward=args.skip_walk_forward,
                    skip_forward_test=args.skip_forward_test,
                    max_walk_forward_splits=args.max_walk_forward_splits,
                    research_stage=args.stage,
                )
            )
            active.add(key)

    return {
        "raw_files": len(raw_files),
        "new_jobs": len(queued_jobs),
        "skipped_active": skipped_active,
        "skipped_already_tested": skipped_tested,
        "skipped_unparsed": skipped_unparsed,
    }


def write_summary(summary: dict[str, Any], summary_path: str | None) -> Path:
    path = Path(summary_path) if summary_path else Path("reports") / "continuous_all_strategies_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
