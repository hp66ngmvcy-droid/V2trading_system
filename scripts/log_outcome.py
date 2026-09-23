#!/usr/bin/env python3
"""Append one outcome record to data/outcomes/brief_outcomes.jsonl."""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

ROOT = Path(__file__).parent.parent
SCHEMA_PATH = ROOT / "data/schemas/human_outcome_record.json"
OUTPUT_PATH = ROOT / "data/outcomes/brief_outcomes.jsonl"


def _nullable(val, cast):
    return None if val is None or val.lower() == "null" else cast(val)


def _bool_null(val):
    if val is None or val.lower() == "null": return None
    if val.lower() == "true": return True
    if val.lower() == "false": return False
    raise argparse.ArgumentTypeError(f"Expected true/false/null, got: {val}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brief-date", required=True)
    p.add_argument("--symbol", required=True, choices=["XAUUSD", "BTCUSD"])
    p.add_argument("--side", required=True, choices=["BUY", "SELL"])
    p.add_argument("--result", required=True,
                   choices=["TP", "SL", "AMBIGUOUS", "NO_SIGNAL", "PENDING"])
    p.add_argument("--hit-target", required=True, help="true/false/null")
    p.add_argument("--hit-stop", required=True, help="true/false/null")
    p.add_argument("--entry-actual", required=True, help="float or null")
    p.add_argument("--exit-price", required=True, help="float or null")
    p.add_argument("--exit-utc", default=None)
    p.add_argument("--bars-held", default=None)
    p.add_argument("--brief-confidence", default=None)
    p.add_argument("--note", default=None)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    rec = {
        "brief_date": a.brief_date,
        "symbol": a.symbol,
        "side": a.side,
        "result": a.result,
        "hit_target": _bool_null(a.hit_target),
        "hit_stop": _bool_null(a.hit_stop),
        "entry_actual": _nullable(a.entry_actual, float),
        "exit_price": _nullable(a.exit_price, float),
        "logged_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if a.exit_utc is not None: rec["exit_utc"] = a.exit_utc
    if a.bars_held is not None: rec["bars_held"] = _nullable(a.bars_held, int)
    if a.brief_confidence is not None:
        rec["brief_confidence"] = _nullable(a.brief_confidence, float)
    if a.note is not None: rec["note"] = a.note

    schema = json.loads(SCHEMA_PATH.read_text())
    try:
        jsonschema.validate(rec, schema)
    except jsonschema.ValidationError as exc:
        print(f"Validation error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    line = json.dumps(rec, separators=(",", ":"))
    if a.dry_run:
        print("[dry-run] Record valid:")
        print(line)
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("a") as fh:
        fh.write(line + "\n")
    print(f"Appended to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
