import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location('audit', Path(__file__).resolve().parents[1] / 'scripts/four_month_baseline_audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


@pytest.mark.parametrize('issued', [None, '', 'bad', '2026-09-01T08:00:00'])
def test_unknown_availability(issued):
    df = pd.DataFrame({'timestamp': pd.to_datetime(['2026-09-01T08:00:00Z'])})
    got, reason = audit.eligible_bars(df, issued)
    assert got.empty and reason == 'AVAILABILITY_UNKNOWN'


def test_intrabar_issuance_waits_for_next_open():
    df = pd.DataFrame({'timestamp': pd.to_datetime(['2026-09-01T08:00:00Z', '2026-09-01T08:15:00Z'])})
    got, reason = audit.eligible_bars(df, '2026-09-01T09:01:00+01:00')
    assert reason is None and len(got) == 1
    assert got.iloc[0].timestamp.minute == 15


@pytest.mark.parametrize('side,stop,target,expected', [('BUY',98,104,True), ('BUY',104,98,False), ('SELL',104,98,True), ('SELL',98,104,False)])
def test_geometry(side, stop, target, expected):
    assert audit.valid_geometry(dict(side=side, entry_zone_low=100, entry_zone_high=102, stop=stop, t1=target)) == expected


def test_neutral_and_unresolved_are_accounted_separately():
    rows = [dict(bias='NEUTRAL', outcome='SL', r_multiple=-1, r_multiple_net=-1.1), dict(outcome='OPEN_EOD')]
    got = audit.summarise(rows)
    assert got['candidates'] == 2 and got['completed'] == 1
    assert got['gross_R'] == -1 and got['outcomes']['OPEN_EOD'] == 1


def test_empty_is_not_zero_win_rate():
    assert audit.summarise([])['win_rate'] is None
