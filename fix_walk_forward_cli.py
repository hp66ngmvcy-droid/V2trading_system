import json
from pathlib import Path

# Read the CLI file
cli_path = Path("src/tar_system/cli.py")
content = cli_path.read_text()

# Find and replace the run_walk_forward_cmd function
old_cmd = '''def run_walk_forward_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from tar_system.data.store import load_feature_data
    from tar_system.strategies.registry import get_strategy
    from tar_system.validation.walk_forward import run_walk_forward

    features = load_feature_data(args.symbol, args.timeframe)
    strategy = get_strategy(args.strategy)
    result = run_walk_forward(features, strategy, args.train_window, args.test_window)
    print(json.dumps(asdict(result), indent=2, default=str))'''

new_cmd = '''def run_walk_forward_cmd(args: argparse.Namespace) -> None:
    from dataclasses import asdict
    from pathlib import Path

    from tar_system.data.store import load_feature_data
    from tar_system.strategie    from tar_system.strarat    from tar_system.strategie    fromlk   rward imp    from tar_system.st    features = load_feat    from tar_system.strategie    from t   strategy = get_strategy(args.st    from tar_system.strategie    from tar_system.srat    from tar_system.strategie    from tar_system.strarat    from tar_syts    from tar_system.strategie    ")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{args.strategy}_{args.symbol}_{args.timeframe}_w    path = output / f"{args.strategy}_{args.symbol}_{args.timefram(as    path = output / f"{args.strategy}_{args.symbol}_{args.tik-    path = output / f"{args.strategy}_ print(json.dumps(asdict(result), indent=2, default=str))'''

if old_cmd in content:
    con    con    con    con    con    con    con    con    con    coxt(content)
    print("✅ Fixed run_walk_forward_cmd - now saves results to    print("✅ Fixed run_walk_for"❌ Could not find the exact fu    print("✅ Fixed run_walk_forward_cmd - now savese the new_cmd above")
