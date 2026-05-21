import json
import os

print("="*70)
print("WALK-FORWARD RESULTS AUDIT")
print("="*70)

results_dir = 'data/results'
files = [f for f in os.listdir(results_dir) if 'walk_forward' in f and '.json' in f]
print(f"\nFound {len(files)} files:\n")

for f in sorted(files):
    try:
        with open(f'{results_dir}/{f}') as file:
            data = json.load(file)
            m = data['stitched_metrics']
            s = data['parameter_stability']['stability_score']
            
            trades = int(m['total_trades'])
            wr = m['win_rate']
            dd = m['max_drawdown']
            pf = m['profit_factor']
            exp = m['expectancy']
            
            print(f"{f}")
            print(f"  Trades: {trades} | WR: {wr:.1%} | DD: {dd:.2%} | PF: {pf:.2f} | Exp: {exp:.2f} | Stability: {s:.0f}%\n")
    except Exception as e:
        print(f"Error: {f} - {e}\n")

print("="*70)
