"""Strategy scoring."""

from tar_system.scoring.gates import GateResult, run_gates
from tar_system.scoring.scorer import ScoreResult, score_strategy

__all__ = ["GateResult", "ScoreResult", "run_gates", "score_strategy"]
