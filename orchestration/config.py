"""Per-project orchestration config for V2trading_system."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH      = PROJECT_ROOT / "orchestration" / "db.sqlite"
KB_DIR       = PROJECT_ROOT / "knowledge-base"
CHROMA_PATH  = PROJECT_ROOT / "orchestration" / "chroma_db"
AGENTS       = ["analysis"]   # no autonomous execution — analysis only

# NO heartbeat or Telegram for this project — tasks run manually only
# python ~/Dev/shared/orchestration/database.py --project ~/Dev/V2trading_system --tasks
