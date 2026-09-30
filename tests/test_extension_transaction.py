import json
import pandas as pd
import pytest
from scripts import extend_m15_data as ext


def test_append_saves_matching_pair_and_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(ext, 'ROOT', tmp_path)
    raw = tmp_path / 'data/raw/BTCUSD_M15.csv'
    validated = tmp_path / 'data/validated/BTCUSD_M15.parquet'
    raw.parent.mkdir(parents=True)
    validated.parent.mkdir(parents=True)
    first = dict(datetime='2026-01-01 00:00:00', open='100', high='102', low='99', close='101')
    raw.write_text('<DATE>\t<TIME>\n' + ext._format_btcusd_row(first) + '\n')
    pd.DataFrame([dict(timestamp=pd.Timestamp(first['datetime']), open=100., high=102., low=99., close=101.)]).to_parquet(validated)
    second = {**first, 'datetime': '2026-01-01T01:15:00+01:00'}
    ext.append_to_validated_parquet('BTCUSD', [second], False)
    df = pd.read_parquet(validated)
    assert len(df) == 2 and df.timestamp.max() == pd.Timestamp('2026-01-01 00:15:00')
    assert '00:15:00' in raw.read_text()
    receipt = json.loads(next((tmp_path / 'data/source_evidence').glob('*.json')).read_text())
    assert receipt['source_status'] == 'UNVERIFIED_CALLER_INPUT'
    assert receipt['parquet_sha256'] == ext.sha(validated.read_bytes())
    assert receipt['raw_sha256'] == ext.sha(raw.read_bytes())


def test_api_evidence_excludes_request_key(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'meta': {'symbol':'BTC/USD','interval':'15min'}, 'values':[
                dict(datetime='2026-01-01 00:00:00', open='100', high='102', low='99', close='101')]}
    monkeypatch.setattr(ext.httpx, 'get', lambda *a, **kw: Response())
    evidence = []
    now = ext.datetime(2026,1,1,tzinfo=ext.timezone.utc)
    ext._fetch_batch('BTC/USD', now, now, 'TEST_SECRET', evidence)
    assert 'TEST_SECRET' not in json.dumps(evidence)
    assert evidence[0]['request']['timezone'] == 'UTC'
    with pytest.raises(ValueError, match='identity'):
        ext._fetch_batch('XAU/USD', now, now, 'TEST_SECRET', [])
