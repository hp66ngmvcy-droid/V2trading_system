#!/usr/bin/env python3
"""Day-by-day paper game simulation.

For each brief + M15 data day:
  1. Validate R:R of all brief setups (validator logic)
  2. For passing setups, check if price entered the entry zone
  3. If zone hit, track whether T1 or stop was hit first
  4. Report day-by-day outcome table

This is a zone-entry model (not wick-filtered) to show raw directional edge.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BRIEFS_DIR = ROOT / "data" / "daily_briefs"
XAU_PARQUET = ROOT / "data" / "validated" / "XAUUSD_M15.parquet"
BTC_PARQUET = ROOT / "data" / "validated" / "BTCUSD_M15.parquet"

# XAU: 1 std lot = ~$100/pt (100 oz * $1/pt). BTC: 1 lot = 1 BTC.
CONTRACT = {"XAUUSD": 100.0, "BTCUSD": 1.0}
RISK_USD = 100.0
SESSION_END_UTC = {"XAUUSD": "17:00", "BTCUSD": None}  # inclusive day window


def _rr(entry: float, stop: float, target: float) -> float:
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return reward / risk if risk > 0 else 0.0


def load_brief_setups(brief_path: Path, min_rr: float = 1.0) -> list[dict]:
    """Return list of valid setups from a brief, applying R:R gate."""
    data = json.loads(brief_path.read_text())
    date = data["date"]
    # Bug 4: carry brief issuance time so callers can gate entries.
    # ISSUED_AT_UNKNOWN = brief pre-dates the issued_at field; availability unverifiable.
    issued_at = data.get("issued_at", "ISSUED_AT_UNKNOWN")
    setups = []

    for sym in ("XAUUSD", "BTCUSD"):
        sym_data = data.get(sym)
        if not sym_data:
            continue
        kl = sym_data.get("key_levels", {})
        # Prefer direction-specific targets (new format); fallback to top_scenario_targets
        sell_tgts = sym_data.get("sell_targets") or sym_data.get("top_scenario_targets", [])
        buy_tgts  = sym_data.get("buy_targets")  or sym_data.get("top_scenario_targets", [])

        # SELL setup
        szl = kl.get("sell_zone_low")
        szh = kl.get("sell_zone_high")
        stop_sell = kl.get("bearish_invalidation")
        t1_sell = float(sell_tgts[0]) if sell_tgts else None
        t2_sell = float(sell_tgts[1]) if len(sell_tgts) > 1 else None
        if szl and szh and stop_sell and t1_sell:
            entry = float(szl)
            rr = _rr(entry, float(stop_sell), float(t1_sell))
            if rr >= min_rr:
                setups.append({
                    "date": date, "symbol": sym, "side": "SELL",
                    "entry_zone_low": float(szl), "entry_zone_high": float(szh),
                    "stop": float(stop_sell), "t1": float(t1_sell),
                    "t2": t2_sell,
                    "rr_t1": round(rr, 2),
                    "confidence": sym_data.get("sell_confidence", 0),
                    "issued_at": issued_at,
                })

        # BUY setup
        bzl = kl.get("buy_zone_low")
        bzh = kl.get("buy_zone_high")
        stop_buy = kl.get("breakdown_trigger") or kl.get("bullish_invalidation")
        t1_buy = float(buy_tgts[0]) if buy_tgts else None
        t2_buy = float(buy_tgts[1]) if len(buy_tgts) > 1 else None
        if bzl and bzh and stop_buy and t1_buy:
            entry = float(bzh)
            # T1 must be ABOVE entry for a BUY
            if t1_buy <= entry:
                continue
            rr = _rr(entry, float(stop_buy), t1_buy)
            if rr >= min_rr:
                setups.append({
                    "date": date, "symbol": sym, "side": "BUY",
                    "entry_zone_low": float(bzl), "entry_zone_high": float(bzh),
                    "stop": float(stop_buy), "t1": t1_buy,
                    "t2": t2_buy,
                    "rr_t1": round(rr, 2),
                    "confidence": sym_data.get("buy_confidence", 0),
                    "issued_at": issued_at,
                })

    return setups


def simulate_setup_legacy(setup: dict, bars: pd.DataFrame) -> dict:
    """Given a setup and day's M15 bars, simulate zone-entry outcome."""
    side = setup["side"]
    ezl = setup["entry_zone_low"]
    ezh = setup["entry_zone_high"]
    stop = setup["stop"]
    t1 = setup["t1"]
    t2 = setup["t2"]

    # Validate T2 direction — old briefs sometimes store wrong-direction T2
    if t2 is not None:
        if side == "SELL" and t2 >= t1:
            t2 = None
        elif side == "BUY" and t2 <= t1:
            t2 = None

    # Fixed spread costs per side (points): BTC ~$20/contract, XAU ~$0.30/oz
    SPREAD_COST = {"XAUUSD": 0.30, "BTCUSD": 20.0}
    spread = SPREAD_COST.get(setup.get("symbol", ""), 0.0)

    result = {**setup, "zone_hit": False, "outcome": "NO_ENTRY",
              "pnl_pts": 0.0, "r_multiple": 0.0, "r_multiple_net": 0.0,
              "entry_price": None}

    if bars.empty:
        return result

    # Find first bar that enters the zone
    for _, bar in bars.iterrows():
        hi, lo = float(bar["high"]), float(bar["low"])

        zone_entered = (side == "SELL" and hi >= ezl) or (side == "BUY" and lo <= ezh)
        if not zone_entered:
            continue

        # Zone touched — mark hit regardless of fill validity
        result["zone_hit"] = True

        # Fill validity: fill price must be within the bar's traded range.
        # SELL fills at ezl (zone bottom): valid only if lo <= ezl (bar traded down to ezl).
        #   zone_entered guarantees hi >= ezl, but if lo > ezl the bar never reached ezl.
        # BUY  fills at ezh (zone top):    valid only if hi >= ezh (bar traded up to ezh).
        #   zone_entered guarantees lo <= ezh, but if hi < ezh the bar never reached ezh.
        entry_price = ezl if side == "SELL" else ezh
        if side == "SELL" and lo > ezl:
            result["outcome"] = "INVALID_FILL"
            return result
        if side == "BUY" and hi < ezh:
            result["outcome"] = "INVALID_FILL"
            return result

        result["entry_price"] = entry_price
        risk = abs(entry_price - stop)
        if risk == 0:
            return result

        # From this bar onward, find first: T1 or stop (T1-only primary model)
        future = bars.loc[bar.name:]
        for _, fbar in future.iterrows():
            fhi, flo = float(fbar["high"]), float(fbar["low"])
            if side == "SELL":
                stop_hit = fhi >= stop
                t1_hit   = flo <= t1
            else:
                stop_hit = flo <= stop
                t1_hit   = fhi >= t1

            if stop_hit and t1_hit:
                # Simultaneous touch — SL wins (conservative); r_multiple = -1.0
                result["outcome"]        = "SL"
                result["pnl_pts"]        = -risk
                result["r_multiple"]     = -1.0
                result["r_multiple_net"] = round((-risk - spread) / risk, 2)
                break
            elif t1_hit:
                reward = abs(t1 - entry_price)
                result["outcome"]        = "TP_T1"
                result["pnl_pts"]        = reward
                result["r_multiple"]     = round(reward / risk, 2)
                result["r_multiple_net"] = round((reward - spread) / risk, 2)
                # Bug 3 fix: T2 is a separate tracking field — never overwrites T1 result.
                # Record whether T2 was later reached (with no intervening stop) for
                # secondary-arm analysis only.
                t2_reached = False
                if t2:
                    for _, tbar in future.loc[fbar.name:].iterrows():
                        thi2, tlo2 = float(tbar["high"]), float(tbar["low"])
                        if side == "SELL":
                            if thi2 >= stop:
                                break
                            if tlo2 <= t2:
                                t2_reached = True
                                break
                        else:
                            if tlo2 <= stop:
                                break
                            if thi2 >= t2:
                                t2_reached = True
                                break
                result["t2_reached"] = t2_reached
                break
            elif stop_hit:
                result["outcome"]        = "SL"
                result["pnl_pts"]        = -risk
                result["r_multiple"]     = -1.0
                result["r_multiple_net"] = round((-risk - spread) / risk, 2)
                break
        else:
            result["outcome"] = "OPEN_EOD"
        break

    return result


try:
    from scripts.zone_touch_v2 import simulate_setup
    from scripts.market_data_io import read_frame
except ModuleNotFoundError:
    from zone_touch_v2 import simulate_setup
    from market_data_io import read_frame


def main():
    print('DIAGNOSTIC_ONLY: boundary_touch_v2; no validated edge or promotion approval.')
    xau_df = read_frame(ROOT, 'XAUUSD')
    btc_df = read_frame(ROOT, 'BTCUSD')
    data_map = {"XAUUSD": xau_df, "BTCUSD": btc_df}
    gold_source_blocked = bool((pd.to_datetime(xau_df.timestamp, utc=True).dt.dayofweek == 5).any())

    brief_files = sorted(BRIEFS_DIR.glob("*_levels.json"))
    all_results = []

    for bf in brief_files:
        setups = load_brief_setups(bf, min_rr=1.0)
        for setup in setups:
            date = setup["date"]
            sym = setup["symbol"]
            df = data_map[sym]
            day_bars = df[df["timestamp"].dt.date.astype(str) == date].copy()
            day_bars = day_bars.sort_values("timestamp").reset_index(drop=True)

            # Apply session end filter for XAU
            end_utc = SESSION_END_UTC.get(sym)
            if end_utc:
                h, m = end_utc.split(":")
                cutoff_min = int(h) * 60 + int(m)
                day_bars = day_bars[
                    day_bars["timestamp"].dt.hour * 60 + day_bars["timestamp"].dt.minute < cutoff_min
                ]

            result = simulate_setup(setup, day_bars.iloc[:0] if sym == 'XAUUSD' and gold_source_blocked else day_bars)
            if sym == 'XAUUSD' and gold_source_blocked:
                result['outcome'] = 'SOURCE_REVIEW_REQUIRED'
            all_results.append(result)

    if not all_results:
        print("No valid setups found with M15 data.")
        return

    # Print summary table
    print(f"\n{'DATE':<12} {'SYM':<8} {'SIDE':<5} {'RR':>5} {'CONF':>5} "
          f"{'ZONE':>5} {'OUTCOME':<10} {'PNL_PTS':>9} {'R_MULT':>7}")
    print("-" * 80)

    total_r = 0.0
    trade_count = 0
    wins = 0

    for r in all_results:
        zone = "YES" if r["zone_hit"] else "NO"
        outcome = r["outcome"]
        pnl = r["pnl_pts"]
        rmult = r["r_multiple"]

        if outcome in ("SL", "TP_T1"):
            trade_count += 1
            r_val = rmult
            total_r += r_val
            if outcome.startswith("TP"):
                wins += 1

        r_multiple = r["r_multiple"]
        entry_str = f"{r['entry_price']:.1f}" if r.get("entry_price") else "—"
        print(f"{r['date']:<12} {r['symbol']:<8} {r['side']:<5} "
              f"{r['rr_t1']:>5.2f} {r['confidence']:>5.2f} "
              f"{zone:>5} {outcome:<10} {pnl:>9.1f} {rmult:>7.2f}  entry={entry_str}")

    print("-" * 80)
    print(f"\nValid setups: {len(all_results)}")
    print(f"Zone entries: {sum(1 for r in all_results if r['zone_hit'])}")
    print(f"Completed trades: {trade_count}")
    if trade_count > 0:
        wr = wins / trade_count
        print(f"Win rate: {wins}/{trade_count} = {wr:.1%}")
        print(f"Total R: {total_r:+.2f}R")
        avg_r = total_r / trade_count
        print(f"Avg R/trade: {avg_r:+.2f}R")
        print(f"Expectancy (at 1R risk=$100): ${avg_r * 100:+.0f}/trade")


if __name__ == "__main__":
    main()
