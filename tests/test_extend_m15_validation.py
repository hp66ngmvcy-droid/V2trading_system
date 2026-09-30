import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('extend', Path(__file__).resolve().parents[1] / 'scripts/extend_m15_data.py')
extend = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extend)
NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)


def bar(**changes):
    return dict(datetime='2026-09-25 12:00:00', open='100', high='102', low='99', close='101', **changes)


def test_valid_closed_bar():
    extend.validate_batch('XAUUSD', [bar()], NOW)


@pytest.mark.parametrize('field,value', [('high', 'NaN'), ('low', '103'), ('open', '-1'), ('volume', '-2'), ('datetime', '2026-09-25 12:01:00'), ('datetime', '2026-09-27 00:00:00')])
def test_bad_bar_rejected(field, value):
    row = bar()
    row[field] = value
    with pytest.raises(ValueError):
        extend.validate_batch('BTCUSD', [row], NOW)


def test_duplicate_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        extend.validate_batch('BTCUSD', [bar(), bar()], NOW)


def test_saturday_is_instrument_specific():
    row = bar()
    row['datetime'] = '2026-09-26 12:00:00'
    extend.validate_batch('BTCUSD', [row], NOW)
    with pytest.raises(ValueError, match='Saturday'):
        extend.validate_batch('XAUUSD', [row], NOW)


def test_invalid_append_does_not_touch_files(tmp_path, monkeypatch):
    monkeypatch.setattr(extend, 'ROOT', tmp_path)
    with pytest.raises(ValueError):
        extend.append_to_validated_parquet('XAUUSD', [{'datetime': 'bad'}], False)
    assert list(tmp_path.iterdir()) == []
