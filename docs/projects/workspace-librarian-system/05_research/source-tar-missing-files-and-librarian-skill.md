# TAR Missing Files and Local Librarian Skill Proposal

## Purpose

This file covers two additions to review before adding them into the TAR system:

1. Missing sealed live-trading interface files
2. A local Librarian Skill for organising project data, files, reports and Obsidian notes

The goal is to design the structure now without adding unsafe live trading or overcomplicating the build.

---

# Part 1: Missing Live Interface Files

## Recommended Position

Add the live-trading interface structure now, but keep it permanently disabled until the system has passed:

- paper trading validation
- risk engine validation
- security review
- human approval workflow
- audit log review
- broker integration review

Do not add real live trading yet.

---

## Files to Add

```text
src/tar_system/live/
├── __init__.py
├── live_adapter_base.py
├── live_guard.py
├── broker_interface.py
└── disabled_live_adapter.py
```

---

## File: live_adapter_base.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LiveOrderRequest:
    symbol: str
    side: str
    quantity: float
    order_type: str
    strategy_name: str
    reason_code: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class LiveOrderResult:
    accepted: bool
    blocked: bool
    message: str
    reason_code: str
    metadata: dict[str, Any]


class LiveAdapterBase(ABC):
    """Base interface for any future live broker adapter.

    This interface exists so the TAR execution layer can be designed cleanly.
    Real live execution must not be implemented yet.
    """

    @abstractmethod
    def place_order(self, request: LiveOrderRequest) -> LiveOrderResult:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> LiveOrderResult:
        raise NotImplementedError

    @abstractmethod
    def get_account_state(self) -> dict[str, Any]:
        raise NotImplementedError
```

---

## File: live_guard.py

```python
from dataclasses import dataclass
from typing import Any


LIVE_TRADING_ENABLED = False


@dataclass(frozen=True)
class LiveGuardDecision:
    allowed: bool
    reason_code: str
    message: str
    metadata: dict[str, Any]


class LiveGuard:
    """Hard safety guard for live execution.

    Live trading cannot be enabled by config alone.
    A future live deployment must require code-level policy change,
    security review and human approval.
    """

    def check_live_allowed(self, metadata: dict[str, Any] | None = None) -> LiveGuardDecision:
        metadata = metadata or {}

        if not LIVE_TRADING_ENABLED:
            return LiveGuardDecision(
                allowed=False,
                reason_code="LIVE_TRADING_DISABLED_BY_POLICY",
                message="Live trading is disabled by system policy.",
                metadata=metadata,
            )

        return LiveGuardDecision(
            allowed=False,
            reason_code="LIVE_TRADING_NOT_APPROVED",
            message="Live trading requires explicit security and human approval.",
            metadata=metadata,
        )
```

---

## File: disabled_live_adapter.py

```python
from typing import Any

from tar_system.live.live_adapter_base import (
    LiveAdapterBase,
    LiveOrderRequest,
    LiveOrderResult,
)
from tar_system.live.live_guard import LiveGuard


class DisabledLiveAdapter(LiveAdapterBase):
    """Live adapter placeholder that blocks all real execution."""

    def __init__(self, guard: LiveGuard | None = None):
        self.guard = guard or LiveGuard()

    def place_order(self, request: LiveOrderRequest) -> LiveOrderResult:
        decision = self.guard.check_live_allowed(request.metadata)

        return LiveOrderResult(
            accepted=False,
            blocked=True,
            message=decision.message,
            reason_code=decision.reason_code,
            metadata={
                **request.metadata,
                "symbol": request.symbol,
                "side": request.side,
                "quantity": request.quantity,
                "strategy_name": request.strategy_name,
            },
        )

    def cancel_order(self, order_id: str) -> LiveOrderResult:
        decision = self.guard.check_live_allowed({"order_id": order_id})

        return LiveOrderResult(
            accepted=False,
            blocked=True,
            message=decision.message,
            reason_code=decision.reason_code,
            metadata={"order_id": order_id},
        )

    def get_account_state(self) -> dict[str, Any]:
        return {
            "live_trading_enabled": False,
            "status": "DISABLED",
            "reason_code": "LIVE_TRADING_DISABLED_BY_POLICY",
        }
```

---

## File: broker_interface.py

```python
from typing import Protocol, Any

from tar_system.live.live_adapter_base import LiveOrderRequest, LiveOrderResult


class BrokerInterface(Protocol):
    """Future broker interface.

    No implementation should connect to a real broker at this stage.
    """

    def place_order(self, request: LiveOrderRequest) -> LiveOrderResult:
        ...

    def cancel_order(self, order_id: str) -> LiveOrderResult:
        ...

    def get_account_state(self) -> dict[str, Any]:
        ...
```

---

## File: __init__.py

```python
from tar_system.live.disabled_live_adapter import DisabledLiveAdapter
from tar_system.live.live_adapter_base import LiveAdapterBase, LiveOrderRequest, LiveOrderResult
from tar_system.live.live_guard import LiveGuard

__all__ = [
    "DisabledLiveAdapter",
    "LiveAdapterBase",
    "LiveOrderRequest",
    "LiveOrderResult",
    "LiveGuard",
]
```

---

## Tests to Add

```text
tests/live/
├── test_live_guard.py
└── test_disabled_live_adapter.py
```

---

## File: test_live_guard.py

```python
from tar_system.live.live_guard import LiveGuard


def test_live_guard_blocks_by_default():
    guard = LiveGuard()
    decision = guard.check_live_allowed()

    assert decision.allowed is False
    assert decision.reason_code == "LIVE_TRADING_DISABLED_BY_POLICY"
```

---

## File: test_disabled_live_adapter.py

```python
from tar_system.live.disabled_live_adapter import DisabledLiveAdapter
from tar_system.live.live_adapter_base import LiveOrderRequest


def test_disabled_live_adapter_blocks_order():
    adapter = DisabledLiveAdapter()

    request = LiveOrderRequest(
        symbol="XAUUSD",
        side="BUY",
        quantity=0.01,
        order_type="MARKET",
        strategy_name="gold_v2",
        reason_code="TEST_ORDER",
        metadata={"test": True},
    )

    result = adapter.place_order(request)

    assert result.accepted is False
    assert result.blocked is True
    assert result.reason_code == "LIVE_TRADING_DISABLED_BY_POLICY"
```

---

# Part 2: Local Librarian Skill

## Purpose

Build a local Librarian Skill that organises files, data, reports, prompts, code notes and research into a structured local knowledge system.

It should work with:

- local project folders
- TAR trading system files
- downloaded GitHub review reports
- Markdown notes
- Obsidian vaults
- CSV / JSON / Parquet metadata
- audit logs
- strategy reports

The Librarian should not move or delete files without approval.

---

## Recommended Position

Yes, build this skill.

It should be a local organisation and knowledge-indexing layer, not an AI agent that randomly edits files.

The first version should:

- scan local folders
- classify files
- generate metadata
- create index notes
- write Obsidian-compatible Markdown
- link related files
- produce review queues
- never delete originals
- never overwrite without backup

---

## Why This Helps TAR

The TAR system will create many files:

```text
data/raw/
data/validated/
data/features/
reports/
logs/audit/
configs/
external_repos/
docs/
strategy_memory/
backtest_results/
```

Without a Librarian, these become difficult to track.

The Librarian adds:

- file discovery
- project indexing
- duplicate detection
- report summaries
- Obsidian dashboards
- strategy knowledge pages
- GitHub repo review library
- local file audit trail

---

## Obsidian Integration Method

Use Obsidian as a Markdown knowledge layer.

The Librarian should write `.md` files into an Obsidian vault.

Recommended vault structure:

```text
ObsidianVault/
├── 00_Inbox/
├── 01_TAR_System/
│   ├── Strategies/
│   ├── Backtests/
│   ├── Risk/
│   ├── GitHub_Reviews/
│   ├── Architecture/
│   └── Audit/
├── 02_Business_Automation/
├── 03_Print_Production/
├── 04_Research/
├── 90_Index/
└── 99_Archive/
```

---

## Obsidian Note Format

Each generated note should use YAML properties:

```markdown
---
type: tar_report
source_path: /Users/yourname/Dev/V2trading_system/reports/example.md
created: 2026-05-06
system: TAR
tags:
  - tar
  - backtest
  - review
status: review
---

# Report Title

## Summary

Short summary here.

## Linked Files

- Source: `local path here`

## Next Action

- Review
- Keep
- Revise
- Archive
```

---

## Librarian Folder Structure

Create:

```text
src/tar_system/librarian/
├── __init__.py
├── scanner.py
├── classifier.py
├── metadata.py
├── obsidian_writer.py
├── index_builder.py
├── duplicate_checker.py
├── safety.py
└── librarian_agent.py
```

---

## Librarian Responsibilities

## 1. Scanner

Scans local project folders and records:

- file path
- file name
- extension
- modified date
- size
- hash
- folder
- project tag

Target file:

```text
src/tar_system/librarian/scanner.py
```

---

## 2. Classifier

Classifies files as:

```text
raw_data
validated_data
feature_data
backtest_result
audit_log
strategy_report
github_review
configuration
prompt
code
document
unknown
```

Target file:

```text
src/tar_system/librarian/classifier.py
```

---

## 3. Metadata Writer

Creates structured metadata records.

Suggested storage:

```text
data/librarian/file_index.duckdb
data/librarian/file_index.jsonl
```

Target file:

```text
src/tar_system/librarian/metadata.py
```

---

## 4. Obsidian Writer

Writes Markdown notes into the Obsidian vault.

Target file:

```text
src/tar_system/librarian/obsidian_writer.py
```

---

## 5. Index Builder

Creates dashboard index notes:

```text
90_Index/TAR System Index.md
90_Index/Strategy Review Index.md
90_Index/GitHub Repo Review Index.md
90_Index/Audit Log Index.md
```

Target file:

```text
src/tar_system/librarian/index_builder.py
```

---

## 6. Duplicate Checker

Checks duplicate files by hash.

It should report duplicates but not delete them.

Target file:

```text
src/tar_system/librarian/duplicate_checker.py
```

---

## 7. Safety Layer

Rules:

- no delete by default
- no overwrite without backup
- no moving source files in v1
- no scanning `.env`
- no exposing secrets
- no indexing private credentials
- no importing external code into active source automatically

Target file:

```text
src/tar_system/librarian/safety.py
```

---

# Codex Prompt: Build Missing Files and Librarian Skill

```text
TASK: Add TAR missing live-interface files and local Librarian Skill.

Part A: Sealed Live Interface

Create:
src/tar_system/live/__init__.py
src/tar_system/live/live_adapter_base.py
src/tar_system/live/live_guard.py
src/tar_system/live/broker_interface.py
src/tar_system/live/disabled_live_adapter.py

Create tests:
tests/live/test_live_guard.py
tests/live/test_disabled_live_adapter.py

Rules:
- Live trading must be permanently disabled.
- Do not connect brokers.
- Do not read credentials.
- Do not place real orders.
- Do not add API execution.
- Any attempted live order must be blocked.
- Dashboard should show LIVE TRADING: DISABLED.

Part B: Librarian Skill

Create:
src/tar_system/librarian/__init__.py
src/tar_system/librarian/scanner.py
src/tar_system/librarian/classifier.py
src/tar_system/librarian/metadata.py
src/tar_system/librarian/obsidian_writer.py
src/tar_system/librarian/index_builder.py
src/tar_system/librarian/duplicate_checker.py
src/tar_system/librarian/safety.py
src/tar_system/librarian/librarian_agent.py

Purpose:
Build a local file organisation and knowledge-indexing tool for TAR and wider business files.

The Librarian should:
- scan local folders
- classify files
- create metadata
- write JSONL and DuckDB indexes
- generate Obsidian-compatible Markdown notes
- create index pages
- detect duplicate files
- produce review queues
- never delete files automatically
- never move files automatically in v1
- never scan secrets or .env files
- never import external repo code into active source automatically

Obsidian integration:
- Write Markdown notes directly into the Obsidian vault.
- Use YAML frontmatter/properties.
- Use tags, status, source_path and type fields.
- Create index notes in 90_Index.
- Use relative links where possible.

Add CLI commands:
python -m tar_system.cli librarian-scan --path /Users/whs1/Dev/V2trading_system
python -m tar_system.cli librarian-index --vault /Users/whs1/Obsidian/TAR
python -m tar_system.cli librarian-duplicates --path /Users/whs1/Dev/V2trading_system

Add tests:
tests/librarian/test_classifier.py
tests/librarian/test_safety.py
tests/librarian/test_obsidian_writer.py

Acceptance criteria:
- Running librarian-scan creates a file index.
- Running librarian-index creates Obsidian Markdown notes.
- Duplicate checker reports duplicates only.
- Safety layer blocks .env and secret files.
- No source files are moved or deleted.
```

---

# Suggested Build Order

1. Add sealed live files
2. Add live tests
3. Add librarian folder structure
4. Add safety rules
5. Add scanner
6. Add classifier
7. Add metadata writer
8. Add Obsidian writer
9. Add index builder
10. Add CLI commands
11. Add tests
12. Add dashboard page later

---

# Final Recommendation

Add the Librarian Skill.

It is a strong fit because your system will produce many files, reports, repo reviews and strategy outputs.

Keep v1 simple:

- scan
- classify
- index
- write notes
- report duplicates
- do not move or delete files

Later v2 can add:

- approved file moves
- archive workflow
- Obsidian URI opening
- Dataview dashboards
- scheduled scans
- business document indexing
- print production file tracking
