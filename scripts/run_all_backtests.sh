#!/usr/bin/env bash
set +e

REPO="/Users/whs1/Dev/V2trading_system"
STRATEGIES=("gold_v2" "rsi_reversion_v1")
SYMBOLS=("XAUUSD" "EURUSD" "GBPUSD" "BTCUSD")
TIMEFRAMES=("M15" "H1")

cd "$REPO" || exit 1
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

has_validated_parquet() {
  local symbol="$1"
  local timeframe="$2"
  [ -f "data/validated/${symbol}_${timeframe}.parquet" ]
}

raw_csv_path() {
  local symbol="$1"
  local timeframe="$2"
  local file="data/raw/${symbol}_${timeframe}.csv"
  if [ -f "$file" ]; then
    printf "%s\n" "$file"
  fi
}

run_combo() {
  local strategy="$1"
  local symbol="$2"
  local timeframe="$3"
  local file
  local output
  file="$(raw_csv_path "$symbol" "$timeframe")"
  if [ -z "$file" ] || ! has_validated_parquet "$symbol" "$timeframe"; then
    echo "SKIPPED $strategy $symbol $timeframe"
    return 2
  fi
  output="$(PYTHONPATH=src python -m tar_system.cli run-full-pipeline \
    --strategy "$strategy" \
    --symbol "$symbol" \
    --timeframe "$timeframe" \
    --file "$file" \
    --broker current_broker_demo \
    --skip-walk-forward \
    --force 2>&1)"
  status=$?
  printf "%s\n" "$output"
  if [ "$status" -ne 0 ] && printf "%s\n" "$output" | grep -q "Pipeline stopped safely"; then
    return 3
  fi
  return "$status"
}

if [ "${BASH_SOURCE[0]}" != "$0" ]; then
  return 0
fi

ran=0
failed=0
skipped=0
safe_stopped=0
for strategy in "${STRATEGIES[@]}"; do
  for symbol in "${SYMBOLS[@]}"; do
    for timeframe in "${TIMEFRAMES[@]}"; do
      run_combo "$strategy" "$symbol" "$timeframe"
      status=$?
      if [ "$status" -eq 0 ]; then
        ran=$((ran + 1))
      elif [ "$status" -eq 2 ]; then
        skipped=$((skipped + 1))
      elif [ "$status" -eq 3 ]; then
        safe_stopped=$((safe_stopped + 1))
      else
        failed=$((failed + 1))
      fi
    done
  done
done

echo "RAN: $ran  SAFE_STOPPED: $safe_stopped  FAILED: $failed  SKIPPED: $skipped"
exit 0
