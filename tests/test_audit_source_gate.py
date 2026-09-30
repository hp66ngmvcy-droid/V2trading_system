import json
import pandas as pd
from scripts.four_month_baseline_audit import audit


def test_suspect_gold_month_is_not_simulated(tmp_path):
    validated = tmp_path / 'data/validated'
    briefs = tmp_path / 'data/daily_briefs'
    validated.mkdir(parents=True)
    briefs.mkdir(parents=True)
    frame = pd.DataFrame(dict(timestamp=pd.to_datetime(['2026-09-05 12:00', '2026-09-07 12:00']),
                              open=[102.,102.], high=[107.,107.], low=[101.,101.], close=[106.,106.]))
    for symbol in ('BTCUSD','XAUUSD'):
        frame.to_parquet(validated / f'{symbol}_M15.parquet')
    brief = {'date':'2026-09-07', 'issued_at':'2026-09-07T00:00:00Z',
             'XAUUSD': {'daily_bias':'BUY', 'buy_targets':[106.], 'key_levels':{
                 'buy_zone_low':100., 'buy_zone_high':102., 'breakdown_trigger':98.}}}
    (briefs / '2026-09-07_levels.json').write_text(json.dumps(brief))
    report = audit(tmp_path, '2026-09-01', '2026-09-08')
    assert report['promotion_eligible'] is False
    assert report['records'][0]['outcome'] == 'SOURCE_REVIEW_REQUIRED'
    assert report['monthly'][1]['completed'] == 0
