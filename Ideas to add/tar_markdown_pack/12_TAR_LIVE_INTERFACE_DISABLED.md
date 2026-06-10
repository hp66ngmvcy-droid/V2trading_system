# TAR Disabled Live Interface

## Recommendation

Include the live-trading interface now, but keep it hard-wired off.

Do not add real live execution.

---

## Files

```text
src/tar_system/live/
├── __init__.py
├── live_adapter_base.py
├── live_guard.py
├── broker_interface.py
└── disabled_live_adapter.py
```

---

## Hard Disable

```python
LIVE_TRADING_ENABLED = False
```

---

## Disabled Adapter

```python
class DisabledLiveAdapter:
    def place_order(self, *args, **kwargs):
        raise RuntimeError("Live trading is disabled by system policy.")
```

---

## Rules

- no broker connections
- no credentials
- no live API calls
- no real order placement
- dashboard must show LIVE TRADING: DISABLED
- attempted live order must be blocked and logged
- cannot be enabled by config alone

---

## Tests

```text
tests/live/test_live_guard.py
tests/live/test_disabled_live_adapter.py
```

---

## Final Position

Build the doorway now.

Keep it locked.
