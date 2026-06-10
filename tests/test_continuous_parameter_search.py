from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


def _load_search_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "continuous_parameter_search.py"
    spec = importlib.util.spec_from_file_location("continuous_parameter_search", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fresh_reset_clears_queue_and_tested_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    module = _load_search_module()
    queue = Path("runtime/optimizer_candidate_queue.jsonl")
    registry = Path("runtime/tested_data_registry.json")
    queue.parent.mkdir(parents=True)
    queue.write_text('{"candidate_id": "old"}\n', encoding="utf-8")
    registry.write_text("{}", encoding="utf-8")

    module.reset_runtime_state(clear_tested_registry=True)

    assert not queue.exists()
    assert not registry.exists()
    assert list(Path("runtime").glob("optimizer_candidate_queue.*.bak"))
    assert list(Path("runtime").glob("tested_data_registry.*.bak"))


def test_preflight_skips_zero_trade_candidate(monkeypatch) -> None:
    module = _load_search_module()
    candidate = module.Candidate(
        candidate_id="abc",
        parent_id=None,
        generation=0,
        strategy="gold_v2",
        symbol="XAUUSD",
        timeframe="M15",
        parameters={},
    )
    features = pd.DataFrame({"timestamp": pd.date_range("2026-01-01", periods=600, freq="15min")})
    monkeypatch.setattr(module, "run_backtest", lambda *_args, **_kwargs: SimpleNamespace(trades=0))

    result = module.preflight_candidate(candidate, features, object(), rows=500)

    assert result["skip"] is True
    assert result["trades"] == 0
    assert result["rows"] == 500


def test_preflight_can_be_disabled() -> None:
    module = _load_search_module()
    candidate = module.Candidate("abc", None, 0, "gold_v2", "XAUUSD", "M15", {})
    features = pd.DataFrame({"timestamp": pd.date_range("2026-01-01", periods=10, freq="15min")})

    result = module.preflight_candidate(candidate, features, object(), rows=0)

    assert result["skip"] is False


def test_compute_direction_hints_improving_score() -> None:
    module = _load_search_module()
    grandparent = module.Candidate("gp", None, 0, "gold_v2", "XAUUSD", "M15", {"rsi_period": 14}, score=40.0)
    parent = module.Candidate("p", "gp", 1, "gold_v2", "XAUUSD", "M15", {"rsi_period": 17}, score=55.0)
    by_id = {"gp": grandparent, "p": parent}

    hints = module._compute_direction_hints(parent, by_id)

    # Score improved (55 > 40) and rsi_period went up (17 > 14), so direction should be +1
    assert hints.get("rsi_period") == 1.0


def test_compute_direction_hints_declining_score() -> None:
    module = _load_search_module()
    grandparent = module.Candidate("gp", None, 0, "gold_v2", "XAUUSD", "M15", {"rsi_period": 14}, score=60.0)
    parent = module.Candidate("p", "gp", 1, "gold_v2", "XAUUSD", "M15", {"rsi_period": 17}, score=45.0)
    by_id = {"gp": grandparent, "p": parent}

    hints = module._compute_direction_hints(parent, by_id)

    # Score declined (45 < 60), so direction should be -1 (reverse)
    assert hints.get("rsi_period") == -1.0


def test_compute_direction_hints_no_parent() -> None:
    module = _load_search_module()
    candidate = module.Candidate("c", None, 0, "gold_v2", "XAUUSD", "M15", {"rsi_period": 14}, score=50.0)

    hints = module._compute_direction_hints(candidate, {})

    assert hints == {}


def test_mutate_parameters_adds_momentum_on_positive_hint() -> None:
    module = _load_search_module()
    params = {"rsi_period": 14}
    hints = {"rsi_period": 1.0}

    variants = module.mutate_parameters(params, hints)
    values = [v["rsi_period"] for v in variants]

    # Normal steps: [14-step, 14+step]; momentum: 14 + 2*step
    assert len(values) == 3
    assert max(values) > 14 + max(1, int(round(14 * 0.2)))  # momentum exceeds normal upper step


def test_mutate_parameters_adds_momentum_on_negative_hint() -> None:
    module = _load_search_module()
    params = {"rsi_period": 20}
    hints = {"rsi_period": -1.0}

    variants = module.mutate_parameters(params, hints)
    values = [v["rsi_period"] for v in variants]

    # Momentum goes further down than normal lower step
    step = max(1, int(round(20 * 0.2)))
    assert min(values) < 20 - step


def test_mutate_parameters_without_hints_unchanged() -> None:
    module = _load_search_module()
    params = {"rsi_period": 14}

    variants_no_hints = module.mutate_parameters(params)
    variants_empty_hints = module.mutate_parameters(params, {})

    assert len(variants_no_hints) == len(variants_empty_hints) == 2


def test_next_generation_falls_back_when_all_below_min_score() -> None:
    module = _load_search_module()
    # All completed candidates score below min_score_to_mutate — search would
    # previously terminate immediately. Now it should fall back to best available.
    low_scorer = module.Candidate(
        "aaa", None, 0, "gold_v2", "XAUUSD", "M15",
        {"rsi_buy_threshold": 55.0, "atr_multiplier": 1.5},
        status="COMPLETED", score=5.0, verdict="KILL",
    )
    children = module.next_generation([low_scorer], generation=0, survivors=3, min_score=35.0)

    # Should still produce children despite score < min_score
    assert len(children) > 0
    assert all(c.generation == 1 for c in children)
    assert all(c.parent_id == "aaa" for c in children)


def test_next_generation_excludes_kill_candidates_in_fallback() -> None:
    module = _load_search_module()
    kill_candidate = module.Candidate(
        "k1", None, 0, "gold_v2", "XAUUSD", "M15",
        {"rsi_buy_threshold": 55.0, "atr_multiplier": 1.5},
        status="COMPLETED", score=8.0, verdict="KILL",
    )
    review_candidate = module.Candidate(
        "r1", None, 0, "gold_v2", "XAUUSD", "M15",
        {"rsi_buy_threshold": 50.0, "atr_multiplier": 1.2},
        status="COMPLETED", score=5.0, verdict="REVIEW",
    )
    children = module.next_generation(
        [kill_candidate, review_candidate], generation=0, survivors=1, min_score=35.0
    )

    # REVIEW candidate preferred over higher-scoring KILL in fallback
    assert all(c.parent_id == "r1" for c in children)


def test_next_generation_normal_path_unchanged() -> None:
    module = _load_search_module()
    good = module.Candidate(
        "g1", None, 0, "gold_v2", "XAUUSD", "M15",
        {"rsi_buy_threshold": 55.0, "atr_multiplier": 1.5},
        status="COMPLETED", score=60.0, verdict="REVIEW",
    )
    bad = module.Candidate(
        "b1", None, 0, "gold_v2", "XAUUSD", "M15",
        {"rsi_buy_threshold": 50.0, "atr_multiplier": 1.0},
        status="COMPLETED", score=5.0, verdict="KILL",
    )
    children = module.next_generation([good, bad], generation=0, survivors=5, min_score=35.0)

    # Normal path: only the good candidate (score >= 35) generates children
    assert all(c.parent_id == "g1" for c in children)


def test_seed_candidates_applies_asset_overrides(monkeypatch) -> None:
    module = _load_search_module()

    # Patch asset_seed_overrides to return a known override for atr_breakout_v3 / EURUSD
    import tar_system.strategies.asset_variants as av
    original = av.asset_seed_overrides

    def fake_overrides(strategy, symbol, timeframe="M15"):
        if strategy == "atr_breakout_v3" and symbol == "EURUSD":
            return {"atr_multiplier": 1.5}
        return original(strategy, symbol, timeframe)

    monkeypatch.setattr(module, "asset_seed_overrides", fake_overrides)

    candidates = module.seed_candidates(["atr_breakout_v3"], ["EURUSD", "XAUUSD"], ["M15"])

    eurusd = next(c for c in candidates if c.symbol == "EURUSD")
    xauusd = next(c for c in candidates if c.symbol == "XAUUSD")

    assert eurusd.parameters["atr_multiplier"] == 1.5
    # XAUUSD gets no override from fake_overrides, so uses class default (2.0)
    assert xauusd.parameters["atr_multiplier"] == 2.0
