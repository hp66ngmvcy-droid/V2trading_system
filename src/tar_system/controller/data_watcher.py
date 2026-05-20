"""Detect changed local raw CSV files and queue research jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from tar_system.controller.job_queue import active_job_keys, add_job, count_active_jobs, make_active_job_key
from tar_system.dashboard.runtime_control import has_tested_data
from tar_system.data.csv_importer import hash_csv_file, load_csv
from tar_system.strategies.registry import RESEARCH_REGISTRY


def scan_raw_data(
    raw_dir: str | Path = "data/raw",
    force: bool = False,
    broker: str = "current_broker_demo",
    research_stage: str = "full",
    window_months: int = 6,
    skip_walk_forward: bool | None = None,
    skip_forward_test: bool | None = None,
    max_walk_forward_splits: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    max_jobs: int | None = None,
    no_live: bool = True,
    no_mt5_promotion: bool = True,
    require_walk_forward: bool = True,
    require_min_trades: bool = False,
    min_trades: int = 30,
) -> list[dict[str, Any]]:
    queued: list[dict[str, Any]] = []
    active_count = count_active_jobs()
    active_keys = active_job_keys()
    for path in sorted(Path(raw_dir).glob("*.csv")):
        parsed = parse_asset_file(path.name)
        if parsed is None:
            continue
        symbol, timeframe = parsed
        data_hash = hash_csv_file(path)
        job_from_date, job_to_date = (from_date, to_date) if from_date and to_date else _stage_window(path, symbol, timeframe, research_stage, window_months)
        stage_skip_walk_forward = False if skip_walk_forward is None else skip_walk_forward
        stage_skip_forward_test = research_stage == "smoke" if skip_forward_test is None else skip_forward_test
        stage_max_splits = 10 if research_stage == "smoke" else 100
        if max_walk_forward_splits is not None:
            stage_max_splits = max_walk_forward_splits
        stage_priority = 10 if research_stage == "smoke" else 100
        for strategy in RESEARCH_REGISTRY:
            if max_jobs is not None and active_count + len(queued) >= max_jobs:
                return queued
            if not force and has_tested_data(strategy, symbol, timeframe, data_hash, "full_pipeline", job_from_date, job_to_date):
                continue
            key = make_active_job_key(strategy, symbol, timeframe, str(path), data_hash=data_hash, from_date=job_from_date, to_date=job_to_date, research_stage=research_stage)
            if key in active_keys:
                continue
            queued.append(
                add_job(
                    strategy,
                    symbol,
                    timeframe,
                    str(path),
                    broker,
                    priority=stage_priority,
                    data_hash=data_hash,
                    from_date=job_from_date,
                    to_date=job_to_date,
                    skip_walk_forward=stage_skip_walk_forward,
                    skip_forward_test=stage_skip_forward_test,
                    max_walk_forward_splits=stage_max_splits,
                    research_stage=research_stage,
                    no_live=no_live,
                    no_mt5_promotion=no_mt5_promotion,
                    require_walk_forward=require_walk_forward,
                    require_min_trades=require_min_trades,
                    min_trades=min_trades,
                )
            )
            active_keys.add(key)
    return queued


def parse_asset_file(filename: str) -> tuple[str, str] | None:
    stem = Path(filename).stem
    parts = stem.split("_")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0].upper(), parts[1].upper()


def _stage_window(path: Path, symbol: str, timeframe: str, research_stage: str, window_months: int) -> tuple[str | None, str | None]:
    if research_stage != "smoke":
        return None, None
    try:
        df = load_csv(path, symbol, timeframe)
    except Exception:
        return None, None
    timestamps = pd.to_datetime(df.get("timestamp"), errors="coerce").dropna()
    if timestamps.empty:
        return None, None
    latest = timestamps.max()
    start = latest - pd.DateOffset(months=max(1, window_months))
    return start.strftime("%Y-%m-%d"), latest.strftime("%Y-%m-%d")
