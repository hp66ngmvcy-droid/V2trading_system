# TAR V2 Research UI

This folder contains the installed UI design handoff for the local TAR V2
trading research system.

## Installed Bundle

- `research-ui-prototype/` - Claude Design HTML/CSS/JS prototype exported from
  `/Users/whs1/Downloads/ui-for-trading/project`.

The primary design source is:

- `research-ui-prototype/TAR Trading UI.html`

The split source files mirror the same UI:

- `app.jsx`
- `data.jsx`
- `components.jsx`
- `page-dashboard.jsx`
- `page-explorer.jsx`
- `page-detail.jsx`
- `tar-styles.css`
- `tweaks-panel.jsx`

## System Link Points

The prototype should be wired to the existing local read/write surfaces rather
than duplicating trading logic.

Read-only UI data:

- `runtime/dashboard_run_status.json`
- `runtime/latest_paper_signal.json`
- `runtime/strategy_health_status.json`
- `runtime/strategy_filter_plan.json`
- `runtime/ai_review_packet.json`
- `runtime/research_committee_*.json`
- `runtime/research_committee_*.md`
- `data/results/*_metrics.json`
- `data/results/*_walk_forward.json`
- `data/results/*_forward_test.json`
- `data/results/*_equity.json`
- `reports/*.md`
- `logs/audit/*.jsonl`

Write actions should stay narrow and paper-only:

- queue jobs through `tar_system.controller.job_queue.add_job`
- read queue status through `tar_system.controller.job_queue.read_jobs`
- use runtime status helpers in `tar_system.dashboard.runtime_control`

The browser UI must not execute trading logic directly, edit parameters, delete
raw data, edit JSONL history, or expose live-trading actions.

## Giffery

No `giffery` package/tool is referenced in this repository or in the installed
UI handoff. It is not needed for this UI. The design is a static React-style
prototype with Chart.js-style equity charting and local JSON/JSONL data targets.

Keep the install dependency-light unless a real production frontend build step
is added later.

## Audit Notes

`research-ui-prototype/TAR Trading UI.html` is a design artifact and references
external CDN assets for fonts, React, Babel, and Chart.js. Do not serve that file
as the production local-only dashboard without replacing those references with
repo-local bundled assets or a proper frontend build.
