import json
from pathlib import Path

results_dir = Path("data/results")
v3_files = sorted([f for f in results_dir.glob("*v3*walk_forward.json")])

print(f"\n{'Strategy':<30} {'Trades':>8} {'Max DD':>8} {'Stability':>10} {'Pass?':>8}")
print("=" * 75)

for f in v3_files:
    try:
        with open(f) as file:
            data = json.load(file)
        
        m = data.get("stitched_metrics", {})
        s = data.get("parameter_stability", {}).get("stability_score", 0)
        
        trades = int(m.get("total_trades", 0))
        dd = m.get("max_drawdown", 0)
        stab = s / 100
        
        # Simple gate: DD < 25% AND Stability > 70%
        gate_pass = (dd < 0.25 and stab >= 0.70)
        status = "✅ PASS" if gate_pass else "❌ FAIL"
        
        print(f"{f.stem:<30} {trades:>8} {dd:>7.1%} {stab:>9.0%}  {status:>8}")
    except Exception as e:
        print(f"{f.stem:<30} ERROR: {e}")

print("=" * 75)
