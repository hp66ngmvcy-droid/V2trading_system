#!/usr/bin/env bash
set -uo pipefail

parse_asset_file() {
  local file_name="$1"
  local base="${file_name%.csv}"
  if [[ "$file_name" != *.csv ]]; then
    return 1
  fi
  if [[ "$base" =~ ^([A-Z0-9]+)_([A-Z0-9]+)$ ]]; then
    printf '%s %s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

import_status_for_file() {
  local file_name="$1"
  local parsed
  if ! parsed="$(parse_asset_file "$file_name")"; then
    echo "SKIPPED_UNRECOGNISED"
    return 0
  fi
  local symbol timeframe
  read -r symbol timeframe <<< "$parsed"
  if [[ -f "data/validated/${symbol}_${timeframe}.parquet" && "${FORCE:-0}" != "1" ]]; then
    echo "ALREADY_IMPORTED"
  else
    echo "IMPORT"
  fi
}

main() {
  cd /Users/whs1/Dev/V2trading_system || exit 1
  if [[ -f venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
  fi

  local imported=0
  local already=0
  local failed=0
  local skipped=0

  shopt -s nullglob
  for path in data/raw/*.csv; do
    local name
    name="$(basename "$path")"
    local parsed
    if ! parsed="$(parse_asset_file "$name")"; then
      echo "$name SKIPPED_UNRECOGNISED"
      skipped=$((skipped + 1))
      continue
    fi
    local symbol timeframe
    read -r symbol timeframe <<< "$parsed"
    local parquet="data/validated/${symbol}_${timeframe}.parquet"
    if [[ "$(import_status_for_file "$name")" == "ALREADY_IMPORTED" ]]; then
      echo "$name ALREADY_IMPORTED"
      already=$((already + 1))
      continue
    fi
    echo "$name IMPORTING symbol=${symbol} timeframe=${timeframe}"
    if PYTHONPATH=src python -m tar_system.cli import-csv --file "$path" --symbol "$symbol" --timeframe "$timeframe" \
      && PYTHONPATH=src python -m tar_system.cli build-features --symbol "$symbol" --timeframe "$timeframe"; then
      echo "$name IMPORTED"
      imported=$((imported + 1))
    else
      echo "$name FAILED"
      failed=$((failed + 1))
    fi
  done

  echo "IMPORTED: ${imported}  ALREADY_IMPORTED: ${already}  FAILED: ${failed}  SKIPPED: ${skipped}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
