# Post-import learning review design

Interpreting as: explain and record how successful daily data imports can trigger a repeatable review and evidence-led learning cycle.

Date: 2026-09-08
Status: DESIGN_RECORDED — not scheduled or built.

Read import_csv, import_all_assets.sh, run_daily_forward_test.sh, nightly_strategy_review.sh and the Cortex learning boundary. Confirmed source-level integration opportunities and pitfalls: existing-Parquet skip, no explicit failing batch exit, date-only review lock and dry-run side effects. Installed scheduler state was not inspected or changed.

Saved [the concrete design and daily prompt](../../docs/prompts/V2_POST_IMPORT_LEARNING_REVIEW_PLAN.md). It specifies readiness manifests, duplicate protection, retry recovery, observation lineage, findings/trial records and separate daily/checkpoint/weekly cadences. The existing learning skill keeps proposed findings distinct from approved instructions; no automatic parameter or gate changes are proposed.

Documentation verification: read back the design and checked linked local files exist. No execution of the import/nightly scripts, no installations, no scheduler or model calls. Next implementation slice is an isolated synthetic manifest-to-report path before activation.
