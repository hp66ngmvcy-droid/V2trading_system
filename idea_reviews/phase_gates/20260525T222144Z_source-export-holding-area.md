# Phase Gate Report

- Phase: source export holding area
- Generated: 2026-05-25T22:21:44+00:00
- Passed: True

## Commands

| Step | Passed | Return | Command |
| --- | --- | ---: | --- |
| compile | True | 0 | `/Users/whs1/Dev/V2trading_system/venv/bin/python -m compileall src/tar_system` |
| tests | True | 0 | `/Users/whs1/Dev/V2trading_system/venv/bin/python -m pytest tests/test_raw_data_inventory.py tests/test_data_readiness.py tests/test_phase_gate.py` |
| pip_check | True | 0 | `/Users/whs1/Dev/V2trading_system/venv/bin/python -m pip check` |
| security_check | True | 0 | `/Users/whs1/Dev/V2trading_system/venv/bin/python -m tar_system.cli security-check` |
| construction_audit | True | 0 | `/Users/whs1/Dev/V2trading_system/venv/bin/python -m tar_system.cli run-local-construction-audit --fail-on-findings` |

## Guardrails

- Review this report before moving to the next phase.
- Do not promote candidates if any gate fails.
