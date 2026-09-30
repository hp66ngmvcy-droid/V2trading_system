"""Read-only input audit and retrospective zone-touch diagnostics, not optimisation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def eligible_bars(frame, issued_at):
    try:
        issued = pd.Timestamp(issued_at)
        if pd.isna(issued) or issued.tzinfo is None:
            return frame.iloc[:0], 'AVAILABILITY_UNKNOWN'
    except (ValueError, TypeError):
        return frame.iloc[:0], 'AVAILABILITY_UNKNOWN'
    result = frame[frame.timestamp >= issued.tz_convert('UTC')]
    return result, None if len(result) else 'NO_POST_ISSUANCE_DATA'


def valid_geometry(s):
    vals = [s[k] for k in ('entry_zone_low', 'entry_zone_high', 'stop', 't1')]
    if not all(np.isfinite(v) for v in vals) or vals[0] > vals[1]:
        return False
    return (s['stop'] < vals[1] < s['t1'] if s['side'] == 'BUY'
            else s['t1'] < vals[0] < s['stop'])


def summarise(records):
    completed = [r for r in records if r['outcome'] in ('SL', 'TP_T1')]
    return {
        'candidates': len(records),
        'outcomes': dict(Counter(r['outcome'] for r in records)),
        'completed': len(completed),
        'gross_R': sum(r['r_multiple'] for r in completed),
        'assumed_cost_net_R': sum(r['r_multiple_net'] for r in completed),
        'win_rate': (sum(r['outcome'] == 'TP_T1' for r in completed) / len(completed)
                     if completed else None),
    }


def audit(root, start, end):
    sys.path.insert(0, str(root))
    from scripts.paper_game_sim import load_brief_setups, simulate_setup
    from scripts.market_data_io import data_lock

    start, end = pd.Timestamp(start, tz='UTC'), pd.Timestamp(end, tz='UTC')
    if start >= end or end.normalize() != end or start.normalize() != start:
        raise ValueError('Use increasing midnight dates; end is exclusive')
    sources, records, coverage = {}, [], []
    for symbol in ('BTCUSD', 'XAUUSD'):
        path = root / 'data/validated' / f'{symbol}_M15.parquet'
        with data_lock(root, symbol):
            sources[str(path.relative_to(root))] = digest(path)
            frame = pd.read_parquet(path, columns=['timestamp', 'open', 'high', 'low', 'close'])
        # Existing local convention; report that naive timestamps are assumed UTC.
        frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True)
        frame = frame[(frame.timestamp >= start) & (frame.timestamp < end)].sort_values('timestamp')
        ohlc = frame[['open', 'high', 'low', 'close']]
        invalid = (~np.isfinite(ohlc).all(axis=1) | (frame.low > frame[['open', 'close']].min(axis=1))
                   | (frame.high < frame[['open', 'close']].max(axis=1)) | (frame.low > frame.high))
        bad_dates = set(frame.loc[invalid | frame.timestamp.duplicated(keep=False), 'timestamp'].dt.date)
        for month in pd.period_range(start.tz_localize(None), (end - pd.Timedelta(days=1)).tz_localize(None), freq='M'):
            monthly = frame[frame.timestamp.dt.strftime('%Y-%m') == str(month)]
            source_blocked = symbol == 'XAUUSD' and (monthly.timestamp.dt.dayofweek == 5).any()
            brief_days = 0
            for date, day in monthly.groupby(monthly.timestamp.dt.date):
                brief = root / 'data/daily_briefs' / f'{date}_levels.json'
                if not brief.exists():
                    continue
                sources[str(brief.relative_to(root))] = digest(brief)
                raw = json.loads(brief.read_text())
                if symbol not in raw:
                    continue
                brief_days += 1
                setups = [s for s in load_brief_setups(brief, min_rr=1.0) if s['symbol'] == symbol]
                for setup in setups:
                    identity = json.dumps({'brief_hash': sources[str(brief.relative_to(root))],
                                           'date': str(date), 'symbol': symbol, 'side': setup['side']}, sort_keys=True)
                    base = {'candidate_id': hashlib.sha256(identity.encode()).hexdigest(),
                            'month': str(month), 'date': str(date), 'symbol': symbol, 'side': setup['side'],
                            'bias': raw[symbol].get('daily_bias', 'UNKNOWN')}
                    window = day
                    if symbol == 'XAUUSD':
                        window = window[window.timestamp.dt.hour < 17]
                    window, reason = eligible_bars(window, raw.get('issued_at'))
                    if raw.get('date') != str(date):
                        reason = 'BRIEF_DATE_MISMATCH'
                    elif source_blocked:
                        reason = 'SOURCE_REVIEW_REQUIRED'
                    elif date in bad_dates:
                        reason = 'INVALID_DATA'
                    elif not valid_geometry(setup):
                        reason = 'INVALID_GEOMETRY'
                    if reason:
                        records.append({**base, 'outcome': reason})
                    else:
                        result = simulate_setup(setup, window.reset_index(drop=True))
                        records.append({**base, 'outcome': result['outcome'],
                                        'r_multiple': result['r_multiple'],
                                        'r_multiple_net': result['r_multiple_net']})
            selected = [r for r in records if r['symbol'] == symbol and r['month'] == str(month)]
            coverage.append({'symbol': symbol, 'month': str(month), 'bars': len(monthly),
                             'weekend_bars_UTC': int((monthly.timestamp.dt.dayofweek >= 5).sum()),
                             'calendar_review_required': bool(symbol == 'XAUUSD' and (monthly.timestamp.dt.dayofweek == 5).any()),
                             'observed_days': monthly.timestamp.dt.date.nunique(), 'brief_days': brief_days,
                             'invalid_data_days': sum(d in bad_dates for d in set(monthly.timestamp.dt.date)),
                             'status': 'NO_BARS' if monthly.empty else 'NO_BRIEFS' if not brief_days else 'RETROSPECTIVE_DIAGNOSTIC',
                             **summarise(selected)})
    for name in ('scripts/paper_game_sim.py', 'scripts/zone_touch_v2.py', 'scripts/four_month_baseline_audit.py'):
        path = root / name
        if path.exists():
            sources[name] = digest(path)
    return {'model': 'boundary_touch_v2_NOT_key_level_sweep',
            'evidence_status': 'DIAGNOSTIC_ONLY', 'promotion_eligible': False,
            'start_inclusive': str(start), 'end_exclusive': str(end),
            'includes_neutral_bias': True, 'parameter_searches': 0,
            'limitations': ['Not a validated performance backtest or untouched holdout.',
                            'Naive bar timestamps assumed UTC; provider convention not verified.',
                            'Issued_at syntax is checked, not historical authenticity of brief availability.',
                            'Ambiguous bar ordering and data gaps are unresolved, excluded from completed-only R.',
                            'Net R uses unverified fixed point costs: BTC 20, XAU 0.30.',
                            'Observed days are not a verified complete exchange-session calendar.',
                            'XAU Saturday bars require feed provenance review before performance use; bars are not silently removed.',
                            'Missing brief months cannot test this strategy; no briefs fabricated.',
                            'Completed-only statistics exclude unresolved outcomes shown separately.'],
            'source_hashes': sources, 'monthly': coverage, 'records': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new path to preserve earlier evidence')
    report = audit(args.root, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(report['monthly'], indent=2))


if __name__ == '__main__':
    main()
