"""Controlled candidate mutations."""

from __future__ import annotations

from dataclasses import replace

from tar_system.discovery.strategy_blueprint import StrategyBlueprint
from tar_system.validation.parameter_sensitivity import neighbouring_parameters


def mutate_blueprint(blueprint: StrategyBlueprint) -> list[StrategyBlueprint]:
    mutations: list[StrategyBlueprint] = []
    for index, parameters in enumerate(neighbouring_parameters(blueprint.parameters or {"risk_reward": 2.0})):
        mutations.append(replace(blueprint, strategy_name=f"{blueprint.strategy_name}_param_{index}", parameters=parameters))
    for filter_name in blueprint.filters:
        filters = [item for item in blueprint.filters if item != filter_name]
        mutations.append(replace(blueprint, strategy_name=f"{blueprint.strategy_name}_no_{filter_name}", filters=filters))
    for reward in (1.5, 2.0, 3.0):
        parameters = dict(blueprint.parameters)
        parameters["reward_risk"] = reward
        mutations.append(replace(blueprint, strategy_name=f"{blueprint.strategy_name}_rr_{str(reward).replace('.', '_')}", parameters=parameters))
    for timeframe in ("M15", "H1", "H4"):
        mutations.append(replace(blueprint, strategy_name=f"{blueprint.strategy_name}_{timeframe.lower()}", timeframe=timeframe))
    return mutations
