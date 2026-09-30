# AlphaInsider Skill Scout: V2 Suitability Audit

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Interpreting as: inspect all three skills and bundled runtime helpers as untrusted source material, identify useful V2 improvements, and recommend adoption boundaries without installing or activating anything.

## Scope and reproducibility

Repository tree inspected at commit `50f9c0f847d05cca6576d822164f78a689a56bcc`; both GitHub skills identify version 1.0.4. This is a pinned repository snapshot, not a claim that a release tag or ZIP was independently verified. Inventory was complete (`truncated: false`).

Read in full: router SKILL.md and catalog; Strategy Creator SKILL.md, all four bundled reference documents, both Python scripts; pyproject.toml and MIT licence; separately hosted API skill. No external Python imported or executed. No credentials accessed, authentication attempted, account mutated or dependency installed.

Inactive downloaded copies: `/private/tmp/alphainsider-scout-50f9c0f/`. This is temporary audit storage, NOT a discoverable installed skill directory. Nothing is enabled for future conversations.

Hosted API skill SHA-256: `d9b2298c6fc5efb13f01fe4c8a5ee54b5583a3cf98ad93296eff5c46342d5141`. Its retrieval succeeded using plain-text curl, superseding the earlier browser content-type failure. It is hosted independently, not pinned by the Git commit. All linked API endpoint pages, platform-scheduler documentation, CI workflows and release archives were not audited. This is a static suitability/security review, not a full penetration test or API integration certification.

## Findings

### HIGH: activation and repair authority exceed V2 defaults

`references/workflow-contracts.md:127` enables schedules during agreed setup without separate activation confirmation. `references/run-and-recover.md:39` allows any implementation issue to be self-repaired when enabled, with no fixed component boundary; successful recovery may resume the scheduler. These are documented behaviours, not hidden backdoors, but importing them unchanged would conflict with V2's explicit activation and review gates.

Decision: no unattended repair of strategy, risk, execution or eligibility rules. Any later local adaptation must default to inactive schedules and require explicit approval for activation/resumption after code changes.

### HIGH: credential/publication workflow conflicts

`references/credentials.md` requests newly supplied credentials in chat and stores them in a project .env. Strategy Creator SKILL.md:93 recommends public strategies. Restricted file permissions and secret redaction help, but do not satisfy V2's Keychain/local-private requirements or remove chat retention exposure.

Decision: no upstream credential workflow, no public upload. No API key is needed to reuse the planning ideas locally.

### HIGH: setup helper is not a read-only boundary

`scripts/alphainsider_setup_request.py:34-36` permits create/update/delete strategy POSTs. The CLI sends an allowed request by default unless --dry-run is supplied; it does not independently verify human approval. It excludes order endpoints, but that does not make it non-mutating.

Decision: do not give this helper to V2 as a general scout tool. A future approved integration needs separate read-only and mutation capabilities, least-privilege credentials, explicit approval and reconciliation tests.

### MEDIUM: reproducibility and test coverage gaps

The router can load release packages or live hosted instructions. A pinned router alone therefore does not freeze the complete instruction dependency chain. Snapshot all adopted references, record hashes, and review updates rather than trusting a floating latest URL.

The returned Git tree has no tests directory despite pyproject.toml naming one. This does not prove the authors never test, but no repository test suite was supplied in this snapshot. Runtime assertions about redaction, mutation blocking, normalised sizing and retries need independent fixtures before integration.

### MEDIUM: secret writer atomicity is not concurrency safety

`set_env_value.py` reads the full file, builds a replacement and uses os.replace. Replacement is atomic, but there is no lock around the read-modify-write transaction; concurrent updates could lose another writer's change. It also reads file content internally, although instructions correctly distinguish program access from exposing values to the agent. Not recommended for V2 in any case because V2 uses a different secret store.

### Compatibility: not a turnkey BTCUSD/XAUUSD engine

The API skill handles AlphaInsider-specific normalised portfolios and distinguishes simulated strategies from broker-connected bots. The setup helper accepts stock/cryptocurrency strategy types. Exact V2 spot/CFD instruments, prices, calendars and execution semantics have not been verified against the service. Do not substitute gold ETFs, futures or another BTC venue silently.

## Positive controls observed

- API helper uses a fixed HTTPS origin, blocks redirects, validates endpoint/method allowlists, bounds request/response size and checks success envelopes.
- It redacts known secret values and credential-named fields; rejects credential query arguments; supports non-sending dry runs. This is useful defence, not proof that every possible secret encoding is covered.
- Secret writer validates inputs, rejects direct symlink .env paths, uses mode 0600 and atomic replacement. It uses standard-library modules, as does the API helper; no eval/exec/subprocess execution was found in these two scripts.
- Runtime guidance recognises uncertain outcomes, duplicate triggers, cross-entry-point exclusion and preservation of later user pauses.
- API instructions explicitly distinguish accepted orders from fills and virtual strategies from real broker bots. They do not themselves grant trading permission.

No obvious malicious payload or hidden external destination was found in the inspected helpers. This limited finding is not a guarantee of security or a certification of future versions.

## Which skills help?

| Skill | V2 value | Recommendation |
| --- | --- | --- |
| alphainsider | Primarily routes to vendor specialists | Do not install; little benefit without choosing their service |
| alphainsider-api | Useful API units, operation semantics and reconciliation guidance | Reference only; defer integration pending an actual service requirement |
| alphainsider-strategy-creator | Strong planning, feasibility and run-state practices | Adapt selected concepts locally; do not install unchanged |

Repository files are MIT-licensed; retain notices for any copied substantial material. Hosted API documentation is separately served: do not assume the repository licence automatically covers it. Publicly reading instructions does not require a paid subscription; API use, data rights and account entitlements remain separate. No service entitlement was authenticated in this scout.

## Prioritised local improvements

1. **Backtest feasibility record:** per feature, capture source, instrument, bar convention, availability, coverage and whether the evidence is prospective, retrospective or a proxy. Integrate with existing `src/tar_system/reviewer/stage0_validator.py` and `tests/test_reviewer_stage0.py`; inspect their contracts before extending them. Do not introduce a competing schema merely because upstream uses plan.md.
2. **Single concise resume record:** link the approved specification, code/data hashes, last complete evidence, blockers and next authorised step from collab. Keep proposals distinct from approvals and mark old results superseded when their implementation changes.
3. **Outcome and retry discipline:** use stable run/candidate identities and explicit UNKNOWN outcomes. Reconcile existing records before repeating a run; distinguish successful WAIT from a runtime error. Reuse `scripts/log_outcome.py` where compatible rather than creating a second ledger.
4. **Technically inert dry runs:** prove no raw brief, strategy state, risk setting or external resource can mutate; test this boundary rather than relying on a prompt. Preserve separate derived research output paths.
5. **Recovery specification:** incident records and a stop-new-work state are useful. Code repair stays reviewed and manual; a crash or an unresolved previous action cannot implicitly resume trading research jobs.

These are operational-quality improvements, not evidence of higher trading returns. The skill contains no validated BTC/gold alpha to import. Existing simulator, availability and classifier prefix-invariance blockers still take priority over adding features.

## Collab handoff

Recommended verdict: ADAPT WORKFLOW CONCEPTS; DO NOT INSTALL UPSTREAM SKILLS UNCHANGED.

Claude review requested: identify which five improvements already exist, nominate the smallest missing change with exact files/tests, and challenge any proposed duplication. Reply at `collab/claude_notes/2026-09-26_alphainsider-scout-response.md`. No code changes, integrations, account creation, scheduler changes or publication are authorised by this audit.

Sources:
- https://github.com/AlphaInsider/skills/tree/50f9c0f847d05cca6576d822164f78a689a56bcc
- https://api.alphainsider.com/skill.md
- https://api.alphainsider.com/resources/agent-skill

Verification: source downloads succeeded; static reading and inventory checks completed; hosted snapshot hashed. Foreign scripts and API operations were not run. Saved-note contents compared after delivery. Claude has not been invoked or notified automatically.
