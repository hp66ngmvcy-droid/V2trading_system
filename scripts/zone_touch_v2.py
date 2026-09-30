"""Boundary-touch replay v2: unresolved ordering is never a win or loss."""
import math

import pandas as pd

MODEL = 'boundary_touch_v2'


def simulate_setup(setup, bars):
    result = {**setup, 'model': MODEL, 'evidence_status': 'DIAGNOSTIC_ONLY',
              'promotion_eligible': False, 'zone_hit': False, 'outcome': 'NO_ENTRY',
              'pnl_pts': 0.0, 'r_multiple': 0.0, 'r_multiple_net': 0.0,
              'entry_price': None, 'exit_price': None, 't2_reached': None,
              'entry_bar': None, 'exit_bar': None}

    def unresolved(reason):
        result['outcome'] = reason
        return result

    try:
        issued = pd.Timestamp(setup.get('issued_at'))
        if pd.isna(issued) or issued.tzinfo is None:
            return unresolved('AVAILABILITY_UNKNOWN')
    except (TypeError, ValueError):
        return unresolved('AVAILABILITY_UNKNOWN')
    side = setup.get('side')
    if side not in ('BUY', 'SELL'):
        return unresolved('INVALID_GEOMETRY')
    low, high, stop, target = [setup[k] for k in ('entry_zone_low', 'entry_zone_high', 'stop', 't1')]
    if not all(math.isfinite(v) for v in (low, high, stop, target)) or low > high:
        return unresolved('INVALID_GEOMETRY')
    entry = high if side == 'BUY' else low
    direction = 1 if side == 'BUY' else -1
    risk = direction * (entry - stop)
    if risk <= 0 or direction * (target - entry) <= 0:
        return unresolved('INVALID_GEOMETRY')
    if bars.empty:
        return unresolved('NO_POST_ISSUANCE_DATA')
    work = bars.copy()
    work['timestamp'] = pd.to_datetime(work.timestamp, utc=True, errors='coerce')
    if work.timestamp.isna().any() or work.timestamp.duplicated().any():
        return unresolved('INVALID_DATA')
    work = work[work.timestamp >= issued.tz_convert('UTC')].sort_values('timestamp')
    if work.empty:
        return unresolved('NO_POST_ISSUANCE_DATA')
    active = False
    previous = None
    cost = {'BTCUSD': 20.0, 'XAUUSD': 0.30}.get(setup.get('symbol'))
    if cost is None:
        return unresolved('UNKNOWN_COST_MODEL')

    def finish(outcome, price, timestamp):
        pnl = direction * (price - entry)
        result.update(outcome=outcome, exit_price=price, exit_bar=timestamp.isoformat(),
                      pnl_pts=pnl, r_multiple=pnl / risk, r_multiple_net=(pnl - cost) / risk)
        return result

    for row in work.itertuples():
        o, h, l, c = row.open, row.high, row.low, row.close
        if not all(math.isfinite(v) and v > 0 for v in (o, h, l, c)) or not l <= min(o, c) <= max(o, c) <= h:
            return unresolved('INVALID_DATA')
        # Missing intervals cannot establish whether a barrier was hit first.
        if active and row.timestamp - previous != pd.Timedelta(minutes=15):
            return unresolved('DATA_GAP')
        previous = row.timestamp
        stop_hit = l <= stop if direction == 1 else h >= stop
        target_hit = h >= target if direction == 1 else l <= target
        if not active:
            # This is a boundary-touch experiment, not a resting limit-order model.
            if not l <= entry <= h:
                continue
            active = True
            result.update(zone_hit=True, entry_price=entry, entry_bar=row.timestamp.isoformat())
            if o != entry and (stop_hit or target_hit):
                return unresolved('AMBIGUOUS_ENTRY_BAR')
        else:
            if direction * (o - stop) <= 0:
                return finish('SL', o, row.timestamp)
            if direction * (o - target) >= 0:
                return finish('TP_T1', target, row.timestamp)
        if stop_hit and target_hit:
            return unresolved('AMBIGUOUS_BARRIERS')
        if stop_hit:
            return finish('SL', stop, row.timestamp)
        if target_hit:
            return finish('TP_T1', target, row.timestamp)
    return unresolved('OPEN_EOD' if active else 'NO_ENTRY')
