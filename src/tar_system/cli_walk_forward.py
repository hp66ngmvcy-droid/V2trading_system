"""Walk-Forward CLI - Phase 2"""
import typer
import logging
import pandas as pd
from typing import Optional
from pathlib import Path
from tar_system.validation.window_splitter import RollingWindowSplitter
from tar_system.validation.blind_tester import BlindOOSTester
from tar_system.validation.equity_stitcher import EquityCurveStitcher
from tar_system.validation.oos_metrics import OOSMetricsAggregator
from tar_system.validation.failed_window_logger import FailedWindowLogger
from tar_system.validation.walk_forward_orchestrator import WalkForwardOrchestrator
from tar_system.backtest.engine import BacktestEngine
from tar_system.strategies.base import GoldV2EMAStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = typer.Typer()

@app.command()
def run_walk_forward(strategy: str = typer.Option("gold_v2"), symbol: str = typer.Option("XAUUSD"), timeframe: str = typer.Option("M15"), train_months: int = typer.Option(12), test_months: int = typer.Option(3), start_date: Optional[str] = typer.Option(None), end_date: Optional[str] = typer.Option(None), output: str = typer.Option("reports/walk_forward_results.json")):
    try:
        data = _load_data(symbol, timeframe, start_date, end_date)
        if data is None:
            typer.echo("No data")
            raise typer.Exit(1)
        strategy_class = _get_strategy_class(strategy)
        backtest_engine = BacktestEngine(initial_capital=10000)
        window_splitter = RollingWindowSplitter(data, train_months, test_months)
        blind_tester = BlindOOSTester(strategy_class, backtest_engine)
        equity_stitcher = EquityCurveStitcher(initial_capital=10000)
        oos_metrics = OOSMetricsAggregator()
        failed_window_logger = FailedWindowLogger("logs/failed_windows.jsonl")
        orchestrator = WalkForwardOrchestrator(strategy_class, backtest_engine, window_splitter, blind_tester, equity_stitcher, oos_metrics, failed_window_logger, 10000)
        results = orchestrator.run(data)
        orchestrator.export_results(output)
        typer.echo(orchestrator.get_results_summary())
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

def _get_strategy_class(name):
    strategies = {'gold_v2': GoldV2EMAStrategy, 'ema_12_26': GoldV2EMAStrategy}
    s = strategies.get(name.lower())
    if not s:
        raise ValueError(f"Strategy '{name}' not found")
    return s

if __name__ == "__main__":
    app()
