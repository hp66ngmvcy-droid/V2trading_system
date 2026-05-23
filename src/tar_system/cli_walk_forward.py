"""Walk-Forward CLI - Phase 2"""
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from tar_system.strategies.registry import get_strategy
from tar_system.validation.walk_forward import run_walk_forward as _run_wf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = typer.Typer()

@app.command()
def run_walk_forward(strategy: str = typer.Option("gold_v2"), symbol: str = typer.Option("XAUUSD"), timeframe: str = typer.Option("M15"), train_window: int = typer.Option(200), test_window: int = typer.Option(50), start_date: Optional[str] = typer.Option(None), end_date: Optional[str] = typer.Option(None), output: str = typer.Option("reports/walk_forward_results.json")):
    try:
        data = _load_data(symbol, timeframe, start_date, end_date)
        if data is None:
            typer.echo("No data")
            raise typer.Exit(1)
        strategy_instance = get_strategy(strategy)
        result = _run_wf(data, strategy_instance, train_window, test_window)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)
        typer.echo(f"Results saved to: {output}")
        typer.echo(json.dumps(asdict(result), indent=2, default=str))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

def _load_data(symbol, timeframe, start_date, end_date):
    path = Path(f"data/validated/{symbol}_{timeframe}.parquet")
    if path.exists():
        data = pd.read_parquet(path)
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
        return data
    return None

if __name__ == "__main__":
    app()
