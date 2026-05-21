# Red Team Post-Mortem

Use this skill after strategy runs, system reviews, or automation changes.

## Purpose

- Challenge attractive results before they become decisions.
- Separate working evidence from unstable assumptions.
- Identify failure modes, hidden coupling, and operational risk.
- Produce action items that improve safety, repeatability, and auditability.

## Review Order

1. Confirm what actually ran.
2. Check whether tests passed or only focused checks passed.
3. Inspect data scope, date range, row caps, and selection bias.
4. Identify code blockers that could invalidate automation.
5. Identify repo/state risks that could make recovery hard.
6. Separate immediate fixes from later research.

## Required Sections

- Executive verdict
- What worked
- Red-team concerns
- Post-mortem timeline
- Evidence reviewed
- Action list
- Decision gate

## Rules

- Do not promote a strategy from bounded smoke alone.
- Do not write strategy memory from partial or blocked runs.
- Never imply live-readiness.
- Always call out zero-trade assets and small sample sizes.
- Prefer local reproducible commands over narrative confidence.
- Keep the report concise enough to read in one sitting.
