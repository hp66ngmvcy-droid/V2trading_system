#!/usr/bin/env python3
"""One-shot queue reconciliation: sync _state.yaml pending tasks → state.db.

Run once from project root. Safe to re-run (INSERT OR IGNORE).

Usage:
    venv/bin/python scripts/reconcile_queue.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "collab" / "_state.yaml"
DB_PATH = ROOT / "collab" / "state.db"
PROJECT = "V2trading_system"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              TEXT PRIMARY KEY,
            project         TEXT NOT NULL DEFAULT '',
            owner           TEXT NOT NULL DEFAULT 'codex',
            status          TEXT NOT NULL DEFAULT 'PENDING',
            priority        INTEGER DEFAULT 99,
            summary         TEXT DEFAULT '',
            note_path       TEXT DEFAULT '',
            done_note_path  TEXT DEFAULT '',
            next_action     TEXT DEFAULT '',
            created         TEXT,
            updated         TEXT
        );
    """)
    conn.commit()


def existing_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT id FROM tasks").fetchall()
    return {r["id"] for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = yaml.safe_load(YAML_PATH.read_text())
    pending = data.get("pending_tasks", [])

    conn = get_conn(DB_PATH)
    init_db(conn)
    existing = existing_ids(conn)

    inserted = []
    skipped = []

    for task in pending:
        tid = task["id"]
        if tid in existing:
            skipped.append(tid)
            continue
        owner = task.get("owner", "claude")
        priority = int(task.get("priority", 99))
        summary = task.get("summary", "")[:500]  # truncate for db
        ts = now_utc()
        if not args.dry_run:
            conn.execute(
                "INSERT OR IGNORE INTO tasks "
                "(id, project, owner, status, priority, summary, created, updated) "
                "VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?)",
                (tid, PROJECT, owner, priority, summary, ts, ts),
            )
        inserted.append(tid)

    # Mark queue-reconciliation as DONE in db
    if "queue-reconciliation" in existing or "queue-reconciliation" in [t["id"] for t in pending]:
        if not args.dry_run:
            conn.execute(
                "UPDATE tasks SET status='DONE', updated=? WHERE id='queue-reconciliation'",
                (now_utc(),),
            )

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f"{'DRY RUN — ' if args.dry_run else ''}Queue reconciliation complete")
    print(f"  Inserted : {len(inserted)}")
    print(f"  Skipped  : {len(skipped)} (already in db)")
    if inserted:
        print(f"  New IDs  : {', '.join(inserted)}")


if __name__ == "__main__":
    main()
