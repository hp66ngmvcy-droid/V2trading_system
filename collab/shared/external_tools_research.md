# External Tools Research — 2026-05-21

Status: Researched. NOT installed. Pending security review per CLAUDE.md gate.

## 1. agency-agents (msitarzewski/agency-agents) — MIT, 98.5k stars

Copy `.md` agent files to `~/.claude/agents/`. Activate by name in Claude Code.

### TAR-relevant agents (copy first):
- `finance/finance-investment-researcher.md` — validates trading signals with fundamentals
- `finance/finance-financial-analyst.md` — scenario modeling for positions
- `finance/finance-fpa-analyst.md` — portfolio performance vs plan
- `finance/finance-tax-strategist.md` — tax optimization, loss harvesting
- `support/support-analytics-reporter.md` — KPI dashboards
- `project-management/project-management-experiment-tracker.md` — A/B testing strategies
- `testing/testing-reality-checker.md` — verifies assumptions before committing capital

### Business OS agents (copy second):
- finance-finance-tracker, support-infrastructure-maintainer, sales-outreach, content-creator,
  ppc-strategist, tracking-specialist, ui-designer, backend-architect, analytics-reporter,
  outbound-strategist (10 files)

**Install after security review:**
```bash
git clone https://github.com/msitarzewski/agency-agents.git
mkdir -p ~/.claude/agents
cp agency-agents/finance/*.md ~/.claude/agents/
# etc. per AGENTS_QUICK_REFERENCE notes
```

---

## 2. spec-kit (github/spec-kit) — MIT, 103k stars, v0.8.12

Spec-driven development: idea → spec → plan → tasks → implement with quality gates.
Works with Claude Code, Copilot, Cursor, Codex, Gemini CLI.

**7 commands:** `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`

**Install after security review:**
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
specify init . --integration copilot
```

**Use for V2trading:** Run `/speckit.specify` before implementing new features to prevent scope creep. Especially useful for wiring multi_agent_scorer into main pipeline.

---

## Security Gate Reminder

Before cloning or running either repo:
1. Read-only inspection of key files (`install.sh`, setup scripts, any `.py` files with `exec`/`eval`)
2. Check for `trust_remote_code` or shell-injection patterns
3. Report findings before proceeding
