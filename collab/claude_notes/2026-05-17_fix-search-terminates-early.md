# Fix: Search Terminates After Generation 0 When Seeds Score Poorly

**Date:** 2026-05-17  
**Author:** Claude  
**Status:** DONE

## Bug

`next_generation()` in `continuous_parameter_search.py` selected survivors using:
```python
tested = [c for c in completed if float(c.score or 0.0) >= min_score]  # 35.0
```

When all generation-0 candidates scored below 35.0 (which happens when default
parameters produce high-drawdown strategies), `tested` was empty → `children = []`
→ the `main()` loop hit `if not new_candidates: break` and terminated.

**Real evidence:** The existing search summary shows 3 completed candidates with
scores of 5.1, 4.94, and 1.43 — all KILLed for HIGH_DRAWDOWN. All below the
35.0 threshold. The search ran one generation and stopped with zero mutations.

## Fix

Added fallback in `next_generation`: when nothing meets `min_score`, select the
best available non-KILL candidates instead. If all candidates are KILL, use all
of them. REVIEW candidates are preferred over KILL in the fallback.

Normal path (candidates above threshold) is unchanged — the fallback only
activates when the threshold produces an empty set.

## Tests

3 tests added to `test_continuous_parameter_search.py`:
- `test_next_generation_falls_back_when_all_below_min_score`
- `test_next_generation_prefers_review_over_kill_in_fallback`  
- `test_next_generation_normal_path_unchanged`

Full suite: **235 passed**.
