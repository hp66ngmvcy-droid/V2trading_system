Repository: freqtrade
URL: https://github.com/freqtrade/freqtrade/tree/develop

Primary focus for review:
- Strategy plugin architecture and separation of exchange layer
- Backtest reproducibility and parameter search patterns
- Position sizing and risk models
- Queueing/automation hooks (cron / bot loop) for batch runs

Questions for reviewer:
- How does their strategy interface compare to TAR's `STRATEGIES` registry?
- Any lessons for deduplication or job orchestration?

Notes: Do not clone or build; read docs, README, and key files only.