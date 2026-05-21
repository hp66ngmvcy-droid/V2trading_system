# Directional Mutation — Parameter Search Improvement

**Date:** 2026-05-17  
**Author:** Claude  
**Status:** DONE

## Problem

`continuous_parameter_search.py` mutated parameters symmetrically (±step) with no memory. Every REVIEW-verdict near-winner discarded its directional signal, so the search could not build momentum toward better regions of parameter space.

## Change

Three surgical edits to `scripts/continuous_parameter_search.py`:

1. **`_compute_direction_hints(candidate, by_id)`** — new function. Compares a survivor's score to its parent's score. For each parameter that changed, returns `+1.0` (keep going) if score improved, `-1.0` (reverse) if it declined.

2. **`mutate_parameters(parameters, direction_hints=None)`** — when a hint is present for a parameter, adds a **momentum variant** (2× step in the winning direction) alongside the normal ±step variants. Without hints, behaviour is identical to before.

3. **`next_generation`** — builds a `by_id` lookup of all candidates, computes direction hints per survivor, passes hints into `mutate_parameters`.

## Effect

- Generation 0→1: no hints (no parent history), normal ±step mutation as before.
- Generation 1→2+: survivors with improving scores get a third momentum variant per parameter, biasing the search toward the improving direction.
- Survivors with declining scores get the reverse direction emphasised.
- Diversity is preserved — normal ±step variants are always included.

## Tests

6 new tests added to `tests/test_continuous_parameter_search.py`. Full suite: **222 passed**.
