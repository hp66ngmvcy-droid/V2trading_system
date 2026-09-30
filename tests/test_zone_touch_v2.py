import pandas as pd
import pytest
from scripts.zone_touch_v2 import simulate_setup


def run(rows, side='BUY', **extra):
    setup = dict(symbol='BTCUSD', side=side, entry_zone_low=100., entry_zone_high=102.,
                 stop=98. if side == 'BUY' else 104., t1=106. if side == 'BUY' else 96.,
                 issued_at='2026-09-01T00:00:00Z')
    setup.update(extra)
    frame = pd.DataFrame(rows, columns=['open', 'high', 'low', 'close'])
    frame['timestamp'] = pd.date_range('2026-09-01', periods=len(frame), freq='15min')
    return simulate_setup(setup, frame)


@pytest.mark.parametrize('issued', [None, 'bad', '08:00', '2026-09-01'])
def test_unknown_availability(issued):
    assert run([(102, 103, 101, 102)], issued_at=issued)['outcome'] == 'AVAILABILITY_UNKNOWN'


def test_no_pre_issuance_entry():
    assert run([(102, 107, 101, 106)], issued_at='2026-09-01T00:01:00Z')['outcome'] == 'NO_POST_ISSUANCE_DATA'


def test_initial_unfillable_bar_does_not_end_search():
    r = run([(100, 101, 99, 100), (102, 103, 101, 102), (103, 107, 103, 106)])
    assert r['outcome'] == 'TP_T1' and r['r_multiple'] == 1
    assert not r['promotion_eligible']


@pytest.mark.parametrize('side,rows,expected', [
    ('BUY', [(102,103,101,102),(95,97,94,96)], -1.75),
    ('SELL', [(100,101,99,100),(108,109,107,108)], -2.),
])
def test_gap_stop_uses_open(side, rows, expected):
    r = run(rows, side)
    assert r['outcome'] == 'SL' and r['r_multiple'] == expected


def test_entry_bar_order_unknown():
    assert run([(103,107,100,104)])['outcome'] == 'AMBIGUOUS_ENTRY_BAR'


def test_later_double_touch_unknown():
    assert run([(102,103,101,102),(102,107,97,101)])['outcome'] == 'AMBIGUOUS_BARRIERS'


def test_bad_geometry():
    assert run([(102,103,101,102)], stop=104.)['outcome'] == 'INVALID_GEOMETRY'


def test_missing_bar_censors_open_trade():
    setup = dict(symbol='BTCUSD', side='BUY', entry_zone_low=100., entry_zone_high=102., stop=98., t1=106., issued_at='2026-09-01T00:00:00Z')
    df = pd.DataFrame(dict(timestamp=pd.to_datetime(['2026-09-01 00:00', '2026-09-01 00:30']), open=[102,103], high=[103,107], low=[101,102], close=[102,106]))
    assert simulate_setup(setup, df)['outcome'] == 'DATA_GAP'
