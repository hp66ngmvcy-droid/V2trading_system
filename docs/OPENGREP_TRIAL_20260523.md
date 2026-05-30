# OpenGrep Static Analysis Trial

Date started: 2026-05-23
Review date: 2026-05-28

## Decision

Trial OpenGrep first for scan-only static analysis. If it is noisy, unavailable, or awkward to integrate by the review date, switch the static-analysis input to Semgrep.

## Rules

- Scan-only mode only.
- Findings are evidence for review, not automatic fixes.
- Findings must feed `export-ai-review-packet`.
- No strategy promotion, live trading, or MT5 automation can depend on AI-only findings.
- Gate logic remains authoritative in `src/tar_system/scoring/gates.py`.

## Local Commands

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-static-analysis-scan --tool opengrep --target src --output runtime/static_analysis/opengrep.json
PYTHONPATH=src venv/bin/python -m tar_system.cli export-ai-review-packet --output runtime/ai_review_packet.md --limit 10
```

For construction-time local checks, use the combined command:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-local-construction-audit --fail-on-findings
```

Or the repo wrapper:

```bash
scripts/local_construction_audit.sh
```

## Review Questions

- Did OpenGrep run reliably in the local environment?
- Were findings useful enough to improve adversarial review quality?
- Did JSON/SARIF ingestion stay stable?
- Was false-positive noise manageable?
- Should the fallback switch to Semgrep?
