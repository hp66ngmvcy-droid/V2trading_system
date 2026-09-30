#!/usr/bin/env python3
"""Generate LLM blind agent bias labels for brief dates.

For each date/symbol, shows only pre-07:45 UTC Asia session bars to
claude-haiku and records its BUY/SELL/NEUTRAL classification.

Run via secrets_run_trading (needs ANTHROPIC_API_KEY):
    source ~/Dev/shared/automations/secrets.sh
    secrets_run_trading -- venv/bin/python scripts/llm_blind_agent_labels.py
    secrets_run_trading -- venv/bin/python scripts/llm_blind_agent_labels.py --date 2026-09-07
    secrets_run_trading -- venv/bin/python scripts/llm_blind_agent_labels.py --dry-run

Provenance: LLM_BLIND_AGENT — machine classifier, NOT human labels.
Do not mix with data/research/human_bias_labels.json.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_V  = ROOT / "data" / "validated"
BRIEFS  = ROOT / "data" / "daily_briefs"
OUTPUT  = ROOT / "data" / "research" / "llm_bias_labels.json"
SYMBOLS = ["BTCUSD", "XAUUSD"]
AS_OF   = "07:45"
MODEL   = "claude-haiku-4-5-20251001"
PROMPT_VERSION = "v1"

SYSTEM_PROMPT = (
    "You are analysing early session price action. "
    "Based only on the data provided, classify the likely directional bias "
    "for the remainder of the trading day. "
    "Respond with exactly one word on the first line: BUY, SELL, or NEUTRAL. "
    "No explanation."
)


def _call_claude(user_text: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — run via secrets_run_trading")
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 10,
        "temperature": 0,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_text}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = json.loads(resp.read())["content"][0]["text"].strip()
    # Take first word only, normalise
    word = text.split()[0].upper() if text else ""
    if word not in ("BUY", "SELL", "NEUTRAL"):
        raise ValueError(f"Unexpected response: {text!r}")
    return word


def _load_df(sym: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA_V / f"{sym}_M15.parquet")
    df["ts"] = pd.to_datetime(df["date"].str.replace(".", "-", regex=False) + " " + df["time"])
    return df.sort_values("ts").set_index("ts")


def _daily_bars(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("D").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last")
    ).dropna(subset=["open"])


def _prior_atr(df: pd.DataFrame, date_str: str) -> float:
    prior = df[df.index.date < pd.Timestamp(date_str).date()]
    d = _daily_bars(prior)
    if len(d) < 2:
        return float("nan")
    pc = d["close"].shift(1)
    tr = pd.concat([(d["high"] - d["low"]),
                    (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14, min_periods=1).mean().iloc[-1])


def _visible_hash(visible_df: pd.DataFrame) -> str:
    rows = [{"ts": ts.isoformat(), "o": float(r["open"]), "h": float(r["high"]),
             "l": float(r["low"]), "c": float(r["close"])}
            for ts, r in visible_df.iterrows()]
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]


def _build_prompt(sym: str, date_str: str, df: pd.DataFrame) -> tuple[str, str]:
    """Return (prompt_text, visible_hash). Raises if no visible bars."""
    dt = pd.Timestamp(date_str)
    h, m = int(AS_OF.split(":")[0]), int(AS_OF.split(":")[1])
    cutoff = h * 60 + m

    day = df[df.index.date == dt.date()].copy()
    bm = day.index.hour * 60 + day.index.minute
    visible = day[bm + 15 <= cutoff]

    if visible.empty:
        raise ValueError(f"No bars before {AS_OF} UTC on {date_str}")

    atr = _prior_atr(df, date_str)
    atr_str = f"{(visible['high'].max() - visible['low'].min()) / atr:.2f}×" \
              if not np.isnan(atr) and atr > 0 else "N/A"

    # Prior day context — uses only completed prior sessions
    d = _daily_bars(df[df.index.date < dt.date()])
    prior_line = ""
    if not d.empty:
        prev = d.iloc[-1]
        today_open = visible["open"].iloc[0]
        gap = today_open - prev["close"]
        dirn = "UP" if prev["close"] >= prev["open"] else "DOWN"
        pr = prev["high"] - prev["low"]
        pr_atr = f"{pr / atr:.1f}×" if not np.isnan(atr) and atr > 0 else "N/A"
        prior_line = (
            f"\nPRIOR DAY: close={prev['close']:.0f}  open_today={today_open:.0f}  "
            f"gap={gap:+.0f}  direction={dirn}  range/ATR={pr_atr}"
        )

    prompt = (
        f"ASIA SESSION ({date_str}, 00:00–{AS_OF} UTC):\n"
        f"  O={visible['open'].iloc[0]:.0f}  "
        f"H={visible['high'].max():.0f}  "
        f"L={visible['low'].min():.0f}  "
        f"C={visible['close'].iloc[-1]:.0f}  "
        f"Range/ATR={atr_str}"
        f"{prior_line}"
    )
    return prompt, _visible_hash(visible)


def load_existing() -> dict:
    return json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}


def save_labels(data: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, OUTPUT)


def run(dates: list[str] | None, dry_run: bool, force: bool) -> None:
    brief_dates = sorted(p.stem.replace("_levels", "") for p in BRIEFS.glob("*_levels.json"))
    if dates:
        brief_dates = [d for d in brief_dates if d in dates]

    labels = load_existing()
    dfs = {sym: _load_df(sym) for sym in SYMBOLS}

    for date_str in brief_dates:
        for sym in SYMBOLS:
            existing = labels.get(sym, {}).get(date_str)
            if existing and not force:
                print(f"  SKIP {sym} {date_str} (already labelled)")
                continue

            try:
                prompt, snap_hash = _build_prompt(sym, date_str, dfs[sym])
            except ValueError as e:
                print(f"  SKIP {sym} {date_str}: {e}")
                continue

            if dry_run:
                print(f"  DRY  {sym} {date_str}")
                print(f"       {prompt[:120]}...")
                continue

            bias = _call_claude(prompt)
            record = {
                "llm_bias": bias,
                "model": MODEL,
                "prompt_version": PROMPT_VERSION,
                "as_of_cutoff": AS_OF,
                "visible_snapshot_hash": snap_hash,
                "labelled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "provenance": "LLM_BLIND_AGENT",
            }
            labels.setdefault(sym, {})[date_str] = record
            save_labels(labels)
            print(f"  DONE {sym} {date_str} → {bias}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="Single date YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true", help="Show prompts, no API calls")
    ap.add_argument("--force", action="store_true", help="Overwrite existing labels")
    args = ap.parse_args()
    dates = [args.date] if args.date else None
    run(dates=dates, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
