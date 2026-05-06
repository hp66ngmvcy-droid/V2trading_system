"""Plain-language optimisation rules."""

OPTIMISATION_RULES = [
    "Do not optimise by win rate alone.",
    "Penalise low trade count.",
    "Penalise high drawdown.",
    "Penalise unstable walk-forward.",
    "Penalise fragile parameters.",
    "Penalise high cost sensitivity.",
    "Penalise poor out-of-sample performance.",
    "Penalise strategies that only work in one short date range.",
    "Prefer balanced strategies with stable results across regimes.",
    "Prefer lower drawdown over maximum return.",
    "Require human approval for promotion.",
]


def list_rules() -> list[str]:
    return list(OPTIMISATION_RULES)
