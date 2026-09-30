"""
day_review.py — Interactive CLI: review daily price action, label human bias.
Storage: data/research/human_bias_labels.json

Usage:
  venv/bin/python scripts/day_review.py --date 2026-09-24 --symbol BTCUSD
  venv/bin/python scripts/day_review.py --date 2026-09-24
  venv/bin/python scripts/day_review.py --recent 10
"""
import argparse, calendar, fcntl, hashlib, json, os
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

BASE   = Path(__file__).parent.parent
DATA_V = BASE / "data/validated"
BRIEFS = BASE / "data/daily_briefs"
LABELS = BASE / "data/research/human_bias_labels.json"
AUTO_R = BASE / "data/research/auto_bias_results.json"
SYMBOLS = ["BTCUSD", "XAUUSD"]
RENDERER_VERSION = "v1"
MIN_ATR_SESSIONS = 14  # prior complete sessions required for valid ATR


def load_df(sym):
    df = pd.read_parquet(DATA_V / f"{sym}_M15.parquet")
    df["ts"] = pd.to_datetime(df["date"].str.replace(".", "-", regex=False) + " " + df["time"])
    return df.sort_values("ts").set_index("ts")

def load_labels():
    return json.loads(LABELS.read_text()) if LABELS.exists() else {}

def save_labels(data):
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    tmp = LABELS.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, LABELS)


def _locked_upsert(sym: str, date_str: str, new_record: dict) -> None:
    """Under exclusive lock: reload labels, build append-only history from on-disk record,
    merge new record, write atomically. History is assembled from disk, not caller-supplied
    state, so concurrent writers on the same date cannot lose each other's revisions."""
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    lock_path = LABELS.with_suffix(".lock")
    with open(lock_path, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            current = json.loads(LABELS.read_text()) if LABELS.exists() else {}
            # Build history from the record currently on disk (not caller state)
            old = current.get(sym, {}).get(date_str)
            if old:
                if "provenance" not in old:
                    old["provenance"] = "RETROSPECTIVE_CONTAMINATED"
                existing_history = old.pop("history", [])
                new_record = {**new_record, "history": existing_history + [old]}
            current.setdefault(sym, {})[date_str] = new_record
            tmp = LABELS.with_suffix(".tmp")
            tmp.write_text(json.dumps(current, indent=2))
            os.replace(tmp, LABELS)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def _validate_as_of(as_of: str) -> tuple[int, int]:
    """Parse and validate HH:MM cutoff. Raises ValueError with reason if invalid."""
    try:
        parts = as_of.split(":")
        h, m = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise ValueError(f"Cutoff {as_of!r} not HH:MM format")
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Cutoff {as_of!r} out of range (hours 0–23, minutes 0–59)")
    return h, m


def _evidence_hash(visible_df: pd.DataFrame, atr, prior_summary,
                   date_str: str, sym: str, as_of: str) -> str:
    """Hash the complete blind evidence: visible bars + prior context + metadata.
    Changes when any part of the displayed context changes."""
    manifest = {
        "date": date_str,
        "symbol": sym,
        "as_of": as_of,
        "renderer": RENDERER_VERSION,
        "atr": None if (atr is None or np.isnan(atr)) else round(float(atr), 4),
        "prior": prior_summary,
        "bars": [{"ts": ts.isoformat(), "o": float(r["open"]), "h": float(r["high"]),
                  "l": float(r["low"]), "c": float(r["close"])}
                 for ts, r in visible_df.iterrows()],
    }
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:16]

def load_brief(date_str):
    p = BRIEFS / f"{date_str}_levels.json"
    return json.loads(p.read_text()) if p.exists() else {}

def load_auto(sym, date_str):
    if not AUTO_R.exists(): return None
    return json.loads(AUTO_R.read_text()).get(sym, {}).get(date_str)

def daily_bars(df):
    return df.resample("D").agg(
        open=("open","first"), high=("high","max"),
        low=("low","min"), close=("close","last")).dropna(subset=["open"])

def atr14(df, date_str):
    d = daily_bars(df)
    if len(d) < 2: return np.nan
    pc = d["close"].shift(1)
    tr = pd.concat([(d["high"]-d["low"]), (d["high"]-pc).abs(), (d["low"]-pc).abs()], axis=1).max(axis=1)
    a = tr.rolling(14, min_periods=1).mean()
    dt = pd.Timestamp(date_str)
    return float(a.loc[dt]) if dt in a.index else float(a.iloc[-1])

def session_ohlc(day_df, start, end, atr_val):
    s = day_df.between_time(start, end)
    if s.empty: return None
    h, l = s["high"].max(), s["low"].min()
    rng = h - l
    return {"O": s["open"].iloc[0], "H": h, "L": l, "C": s["close"].iloc[-1],
            "Range": rng, "va": rng/atr_val if atr_val > 0 else np.nan}

def print_day(sym, date_str, df, blind_df=None, hide_auto=False, hide_brief=False,
              _blind_atr=None, _blind_n_prior=None):
    dt = pd.Timestamp(date_str)
    # H1 fix + warm-up: in blind mode caller supplies precomputed ATR (gated on MIN_ATR_SESSIONS)
    if blind_df is not None:
        atr = _blind_atr if _blind_atr is not None else np.nan
    else:
        atr = atr14(df, date_str)
    # H2 fix: don't load hidden sources at all in blind mode
    brief = {} if hide_brief else load_brief(date_str)
    auto  = None if hide_auto else load_auto(sym, date_str)
    day_df = blind_df if blind_df is not None else df[df.index.date == dt.date()]

    blind_tag = f"  [BLIND as-of {blind_df.index[-1].strftime('%H:%M') if blind_df is not None and not blind_df.empty else '?'} UTC]" if blind_df is not None else ""
    atr_status = ""
    if blind_df is not None and (atr is None or np.isnan(atr)):
        n = _blind_n_prior or 0
        atr_status = f"  ATR: INSUFFICIENT_HISTORY ({n} prior sessions, need {MIN_ATR_SESSIONS})"
    print(f"\n=== DAY REVIEW: {sym} — {date_str} ({dt.strftime('%A')}){blind_tag} ===")
    if atr_status:
        print(atr_status)

    # Sessions
    if not day_df.empty:
        print("\nSESSION BREAKDOWN")
        for name, lbl, t0, t1 in [("Asia","00–08 UTC","00:00","07:45"),
                                    ("London","08–16 UTC","08:00","15:59"),
                                    ("NY","13–21 UTC","13:00","20:59")]:
            s = session_ohlc(day_df, t0, t1, atr)
            if s:
                va = f"{s['va']:.2f}×" if not np.isnan(s['va']) else "N/A"
                print(f"  {name:<8} ({lbl})  O={s['O']:.0f}  H={s['H']:.0f}  L={s['L']:.0f}  C={s['C']:.0f}  Range={s['Range']:.0f}  vs ATR: {va}")

    # Prior day context
    d = daily_bars(df)
    if dt in d.index:
        loc = d.index.get_loc(dt)
        if loc > 0:
            prev, today = d.iloc[loc-1], d.iloc[loc]
            gap = today["open"] - prev["close"]
            gap_pct = 100*gap/prev["close"] if prev["close"] else 0
            pr = prev["high"] - prev["low"]
            ra = f"{pr/atr:.1f}×" if atr > 0 else "N/A"
            sign = "+" if gap >= 0 else ""
            dirn = "UP" if prev["close"] >= prev["open"] else "DOWN"
            print(f"\nPRIOR DAY CONTEXT")
            print(f"  {d.index[loc-1].strftime('%b-%d')} close: {prev['close']:.0f} | {date_str} open: {today['open']:.0f} | Gap: {sign}{gap:.0f} ({sign}{gap_pct:.1f}%)")
            print(f"  Prior day direction: {dirn} | Prior day range/ATR: {ra}")
            # Key levels
            dh, dl = day_df["high"].max(), day_df["low"].min()
            tol = pr * 0.005
            kl = []
            if abs(dh - prev["high"]) <= tol or dh >= prev["high"]:
                kl.append(f"  Prior high {prev['high']:.0f} → tested")
            if dl <= prev["low"]:
                kl.append(f"  Prior low  {prev['low']:.0f} → new low (breakdown)")
            elif abs(dl - prev["low"]) <= tol:
                kl.append(f"  Prior low  {prev['low']:.0f} → tested")
            if kl:
                print("\nKEY LEVELS TOUCHED")
                for k in kl: print(k)

    # Auto signals
    if hide_auto:
        print("\nAUTO SIGNALS  [hidden in blind mode]")
    elif auto:
        slbl = {1:"BUY", 0:"NEUTRAL", -1:"SELL"}
        print("\nAUTO SIGNALS")
        for n, v in zip(["Range position","Session momentum","Prior day follow"], auto["signals"]):
            print(f"  {n}: {slbl[v]}")
        print(f"  AUTO BIAS → {auto['auto_bias']} ({auto['agreement']}/3 signals)")
    else:
        print("\nAUTO SIGNALS  (run backfill_auto_bias.py first)")

    # Pattern flags
    flags = []
    lf = max(d for d in range(calendar.monthrange(dt.year,dt.month)[1],0,-1)
             if pd.Timestamp(dt.year,dt.month,d).weekday()==4)
    nd = dt + pd.Timedelta(days=1)
    if nd.day == lf and nd.month == dt.month:
        flags.append("  OPTIONS_EXPIRY_VOLATILITY_FADE: tomorrow is last Friday of month")
    us10y = brief.get("macro",{}).get("us10y_yield")
    if us10y and float(us10y) > 5.0:
        flags.append(f"  YIELD_COMPRESSION_EXHAUSTION: 10Y at {us10y}% (above 5.0% threshold)")
    if auto and auto.get("auto_bias") == "NEUTRAL":
        flags.append("  NEUTRAL_BIAS_SKIP: auto_bias is NEUTRAL — low-conviction day")
    note = brief.get("macro",{}).get("note","")
    if "etf" in note.lower() or "flow" in note.lower():
        flags.append("  FLOW_DIVERGENCE: ETF flow context present — review manually")
    if flags:
        print("\nPATTERN FLAGS")
        for f in flags: print(f)

    # Existing brief
    if not hide_brief:
        sb = brief.get(sym, {})
        if sb:
            kl = sb.get("key_levels", {})
            zones = []
            if "sell_zone_high" in kl: zones.append(f"SELL {kl['sell_zone_low']}–{kl['sell_zone_high']}")
            if "buy_zone_high"  in kl: zones.append(f"BUY {kl['buy_zone_low']}–{kl['buy_zone_high']}")
            print(f"\nEXISTING BRIEF\n  daily_bias: {sb.get('daily_bias','N/A')} | zones: {' / '.join(zones) or 'N/A'}")
    else:
        print("\nEXISTING BRIEF  [hidden in blind mode]")


def prompt_label(sym, date_str, df, labels, blind=False, as_of="07:45"):
    prior_exposed = False
    ev_hash = None
    n_prior = None

    if blind:
        try:
            h, m = _validate_as_of(as_of)
        except ValueError as e:
            print(f"\n  BLOCKED: {e}")
            return False

        dt = pd.Timestamp(date_str)
        cutoff_mins = h * 60 + m
        day_df_full = df[df.index.date == dt.date()].copy()
        bar_mins = day_df_full.index.hour * 60 + day_df_full.index.minute
        visible_df = day_df_full[bar_mins + 15 <= cutoff_mins]
        if visible_df.empty:
            print(f"\n  BLOCKED: no bars before {as_of} UTC for {date_str}.")
            return False

        # ATR gated on warm-up: require MIN_ATR_SESSIONS prior complete sessions
        prior_df = df[df.index.date < dt.date()]
        prior_d = daily_bars(prior_df)
        n_prior = len(prior_d)
        blind_atr = atr14(prior_df, date_str) if n_prior >= MIN_ATR_SESSIONS else float("nan")

        # Prior summary for evidence hash — full OHLC so prior-open direction changes affect hash
        prior_summary = None
        if not prior_d.empty:
            prev = prior_d.iloc[-1]
            prior_summary = {
                "date": prior_d.index[-1].strftime("%Y-%m-%d"),
                "open": round(float(prev["open"]), 4),
                "high": round(float(prev["high"]), 4),
                "low":  round(float(prev["low"]),  4),
                "close": round(float(prev["close"]), 4),
            }

        ev_hash = _evidence_hash(visible_df, blind_atr, prior_summary,
                                 date_str, sym, as_of)
        print_day(sym, date_str, df, blind_df=visible_df, hide_auto=True, hide_brief=True,
                  _blind_atr=blind_atr, _blind_n_prior=n_prior)
    else:
        print_day(sym, date_str, df)

    ex = labels.get(sym, {}).get(date_str)
    if ex:
        prov = ex.get("provenance", "RETROSPECTIVE_CONTAMINATED")
        if blind:
            prior_exposed = True
            print(f"\n  (Prior label exists [{prov}] — answer hidden to preserve blind integrity)")
        else:
            print(f"\n  (Already labelled: {ex['human_bias']} [{prov}])")
    val = input("\nYour bias classification [BUY/SELL/NEUTRAL/skip]: ").strip().upper()
    if val in ("SKIP","") or val not in ("BUY","SELL","NEUTRAL"):
        if val not in ("SKIP","","BUY","SELL","NEUTRAL"): print("  Invalid — skipping")
        return False
    note = input("Optional note (press enter to skip): ").strip()
    auto = load_auto(sym, date_str)

    new_record = {
        "human_bias": val,
        "note": note or None,
        "auto_bias": auto["auto_bias"] if auto else None,
        "labelled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance": "RETROSPECTIVE_BLINDED" if blind else "RETROSPECTIVE",
    }
    if blind:
        new_record["as_of_cutoff"] = as_of
        new_record["evidence_hash"] = ev_hash
        new_record["n_prior_sessions"] = n_prior
        if prior_exposed:
            new_record["prior_label_exposed"] = True

    # History assembly happens inside _locked_upsert (reads from disk under lock)
    _locked_upsert(sym, date_str, new_record)
    print(f"  Saved: {sym} {date_str} → {val} [{new_record['provenance']}]")
    return True


def unlabelled_days(df, sym, labels, n):
    existing = set(labels.get(sym,{}).keys())
    days = sorted({ts.date().isoformat() for ts in df.index}, reverse=True)
    return list(reversed([d for d in days if d not in existing][:n]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--symbol"); ap.add_argument("--recent", type=int)
    ap.add_argument("--blind", action="store_true",
                    help="Blind mode: hide bars after --as-of, hide auto signals and brief")
    ap.add_argument("--as-of", default="07:45", dest="as_of",
                    help="Cutoff HH:MM UTC for blind mode (default 07:45)")
    args = ap.parse_args()
    labels = load_labels()
    syms = [args.symbol] if args.symbol else SYMBOLS

    if args.recent:
        for sym in syms:
            df = load_df(sym)
            days = unlabelled_days(df, sym, labels, args.recent)
            if not days: print(f"{sym}: no unlabelled days"); continue
            print(f"\n{sym}: {len(days)} unlabelled days to review")
            for d in days:
                prompt_label(sym, d, df, labels, blind=args.blind, as_of=args.as_of)
                if input("[c]ontinue / [q]uit: ").strip().lower() == "q": break
    elif args.date:
        for sym in syms:
            prompt_label(sym, args.date, load_df(sym), labels, blind=args.blind, as_of=args.as_of)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
