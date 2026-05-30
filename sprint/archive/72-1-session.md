---
story_id: "72-1"
jira_key: ""
epic: "72"
workflow: "tdd"
---
# Story 72-1: Revive dormant NPC development pipeline

## Story Details
- **ID:** 72-1
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-30T08:58:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30T08:05:01Z | 2026-05-30T08:06:29Z | 1m 28s |
| red | 2026-05-30T08:06:29Z | 2026-05-30T08:25:29Z | 19m |
| green | 2026-05-30T08:25:29Z | 2026-05-30T08:36:11Z | 10m 42s |
| spec-check | 2026-05-30T08:36:11Z | 2026-05-30T08:38:21Z | 2m 10s |
| verify | 2026-05-30T08:38:21Z | 2026-05-30T08:44:36Z | 6m 15s |
| review | 2026-05-30T08:44:36Z | 2026-05-30T08:56:16Z | 11m 40s |
| spec-reconcile | 2026-05-30T08:56:16Z | 2026-05-30T08:58:16Z | 2m |
| finish | 2026-05-30T08:58:16Z | - | - |

## Sm Assessment

**Story selected:** 72-1 — Revive dormant NPC development pipeline (epic 72, NPC Identity
Hardening). 8 pts, p2, tdd/phased. Operator-selected as the foundational story of epic 72.

**Why this story:** The NPC development pipeline runs backwards from ADR-014 (Diamonds and
Coal) and ADR-020 (NPC Disposition): promotion/escalation fire only on mechanical necessity,
never on player interest. `resolution_tier` is hard-pinned to `"spawn"` and never escalates;
`non_transactional_interactions` is declared but never incremented; disposition drifts only
via explicit narrator deltas. The lived consequence — an NPC the playgroup talks to for ten
turns stays a frozen scaffold — is exactly the "engine silently failing to remember who
matters" failure the OTEL-lie-detector doctrine exists to catch. Foundational for the 9
dependent stories in epic 72.

**Setup state (all gate checks pass):**
- Session file created: `.session/72-1-session.md` (fields set: story_id, epic 72, workflow tdd).
- Story context pre-existing and complete: `sprint/context/context-story-72-1.md` — full
  ACs AC1–AC6, technical guardrails (primary seam at the `npcs_hit` branch of
  `_apply_npc_mentions`, narration_apply.py:1221-1255), scope boundaries, span contracts.
- Branch created: `feat/72-1-revive-npc-development-pipeline` in sidequest-server.
- Jira: **explicitly skipped** — Jira is not configured for this project (`pf jira check`
  refuses; jira.project/url unset). No claim possible or needed.

**Scope guardrails for downstream agents (from context doc — do not absorb sibling work):**
- IN: increment `non_transactional_interactions` on the `npcs_hit` branch; escalate
  `resolution_tier` past `"spawn"` at named-constant thresholds; emergent disposition drift
  via the `Disposition(...)` constructor + `.attitude()` bands (never hardcode ±10); OTEL on
  all three legs (reuse `disposition.shift` for the drift leg, add a development-tick span for
  increment/escalation; attribute key is `npc_name`, NOT reserved `name`).
- OUT (sibling stories): 72-2 promotion/reconcile, 72-7 authoritative identity drift, 72-9
  OCEAN/belief seeding, 72-5 born-hostile default, 72-6 pool cap/prune.
- Test rule: fixture-driven span-asserted wiring test over the real `_apply_npc_mentions`
  flow — **no source-text grep wiring tests** (CLAUDE.md).

**Routing:** tdd/phased. Next phase `red`, owner TEA (The Architect) — author failing tests
for AC1–AC6 before any implementation.

## TEA Assessment

**Tests Required:** Yes
**Phase:** finish — RED state verified

**Test File:**
- `sidequest-server/tests/server/test_npc_development_pipeline.py` — 26 tests over the
  real `_apply_npc_mentions` `npcs_hit` branch (fixture-driven snapshots; two span-capture
  harnesses: `InMemorySpanExporter` + watcher-hub routing). Mirrors the established shapes in
  `tests/server/test_npc_pool_narration_apply.py` and `tests/integration/test_npc_edge_publish_wiring.py`.

**Tests Written:** 26 covering AC1–AC6.
**Status:** RED — **18 failed, 8 passed** (`uv run pytest tests/server/test_npc_development_pipeline.py -p no:randomly`).
The 18 failures are the missing development tick (counter stays 0, tier stays `spawn`, no
disposition drift, no dev-tick span, unrouted hub event) — verified to fail on assertions,
not API/fixture misuse (the otel harness captured the real `npc.referenced` /
`snapshot.party_location_query` spans, proving the harness works and only the new span is
absent). The 8 passing tests are intentional green-from-start guards: AC1/AC3 negative cases
(`pool_hit`/`invented` engagements develop nothing) and AC2/AC6 model-default baselines
(fresh / materialized `Npc` is `non_transactional_interactions=0`, `resolution_tier="spawn"`).

**Per-AC coverage:**
| AC | Behavior pinned | Tests |
|----|-----------------|-------|
| AC1 increment | +1 per engaged turn; per-NPC independence; de-dup same-name-twice→+1; pool/invented never increment | 6 |
| AC2 tier escalation | starts `spawn`; 1 engagement stays `spawn`; eventually escalates; monotonic non-decreasing; crisp boundary; top-tier saturates | 6 |
| AC3 disposition drift | warms positive + monotonic; ±100 clamp saturates; band read honors genre-configured `friendly_at` (not hardcoded ±10); no drift without an `Npc` | 4 |
| AC4 dev-tick span | fires once per engagement w/ `npc_name`+count+tier old/new; fires even w/o tier change; records change on escalation; **hub-routed wiring test** | 4 |
| AC5 disposition.shift | reused contract `crossed=True` on band cross; `crossed=False` intra-band w/ non-zero delta; no phantom shift at clamp | 3 |
| AC6 regression guard | unmentioned co-present NPC untouched; materialized baseline undeveloped; no `npcs_hit` → no tick | 3 |

### Rule Coverage (`.pennyfarthing/gates/lang-review/python.md`)

| Rule | Test(s) / how enforced | Status |
|------|------------------------|--------|
| #6 test quality — no vacuous asserts | Every test asserts a specific value; band-honoring and clamp tests add a non-vacuity guard (assert drift actually crossed the boundary / saturated) so the invariant isn't trivially satisfied at the start value | enforced |
| #6 mock-target correctness | No `mock.patch` used — real `_apply_npc_mentions` is driven over synthetic state (fixture-driven, per server CLAUDE.md "No Source-Text Wiring Tests") | enforced |
| #2 mutable defaults | Helpers use `*npcs` / explicit args; no mutable default arguments | enforced |
| #3 type annotations at boundaries | All helpers + tests fully annotated (`-> None`, typed params) | enforced |
| Server CLAUDE.md — No Source-Text Wiring Tests | AC4 wiring test is a hub-routed OTEL span assertion + fixture-driven behavior, never a source grep | enforced |
| OTEL Observability Principle | AC4/AC5 assert every development decision emits a routed span the GM panel sees | enforced |

**Rules checked:** 4 of 13 lang-review rules apply to a pure-test change (the rest target
production source: exceptions, logging, paths, deserialization, async, imports, input
validation, deps). **Self-check:** 0 vacuous tests (ruff clean, format clean; each assertion
checks a concrete value, not a truthy/None).

**Handoff:** To Dev (Agent Smith) for GREEN — implement the development tick in the `npcs_hit`
branch (`narration_apply.py` ~1349-1377), the new dev-tick span + `SpanRoute` in
`telemetry/spans/npc.py`, and reuse the `disposition.shift` contract. Honor the pinned span
attribute keys (`npc_name`, `non_transactional_interactions`, `resolution_tier_before/after`)
and the Dev-owned choices flagged in Design Deviations below.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 26/26 passing (GREEN). Full server suite: 9122 passed; the 16 failures are
**pre-existing and unrelated** (WWN spell catalog / namegen corpora audit / pack-content
validation — verified by stashing the entire implementation and reproducing all 16 on the
clean branch base; none touch NPC code). Lint clean, format clean, pyright 0 errors on the
two new/edited production files (`npc_development.py`, `telemetry/spans/npc.py`);
`narration_apply.py` keeps its 32 pre-existing pyright errors — my added lines introduce none.

**Files Changed:**
- `sidequest/game/npc_development.py` (**new**) — the pure development logic: named tier
  ladder `(spawn, acquaintance, established)`, thresholds `ACQUAINTANCE_AT=3` / `ESTABLISHED_AT=8`,
  `DISPOSITION_DRIFT_PER_ENGAGEMENT=2`, `tier_for_interactions()`, and
  `develop_npc_on_engagement(npc) -> DevelopmentTick` (mutates counter/tier/disposition in
  place, returns before/after deltas for span emission). Constants live here, not as magic
  literals in the apply branch.
- `sidequest/telemetry/spans/npc.py` — new `SPAN_NPC_DEVELOPED = "npc.developed"` + its
  `SpanRoute` (state_transition, component `npc_registry`, field `npcs`, op `developed`) and
  the `npc_developed_span` `@contextmanager` opener, mirroring `npc_referenced_span`. Uses
  `npc_name` (not the reserved `name`).
- `sidequest/server/narration_apply.py` — wired the tick into the `npcs_hit` branch of
  `_apply_npc_mentions` after the last-seen stamping: a per-turn `developed_this_turn` de-dup
  set, the `develop_npc_on_engagement` call, the `npc.developed` span, and a reuse of the
  `disposition.shift` span gated on `disposition_delta != 0` (no phantom shift at the clamp).
- `tests/server/test_npc_development_pipeline.py` — Dev fix to the TEA `_drive` helper
  (deep-copy per step) + `Disposition(...)` wrapping of fixture args (see deviation below).

**Decisions within the Dev-owned latitude TEA flagged** (not deviations — TEA explicitly
deferred these and the tests pin only behavior): tier names `acquaintance`/`established`,
thresholds 3/8, drift magnitude +2, span name `npc.developed`. All honor TEA's pinned
invariants (first threshold ≥ 2, positive drift, per-turn de-dup, `npc_name` attribute key).

**Wiring:** the tick fires from the production `_apply_npc_mentions` path (not a test-only
hook); AC4's hub-routed span test proves the `npc.developed` event reaches the GM-panel
watcher. `run_npc_agency` reads the drifted `disposition.attitude()` and escalated tier for
free on the next turn (same `Npc` instance) — no change needed there.

**Branch:** `feat/72-1-revive-npc-development-pipeline` (pushed).
**Handoff:** To TEA (The Architect) for the verify phase (simplify + quality-pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None
**Structural gate (`spec_check`):** pass — AC coverage, implementation-complete, and TEA+Dev
deviation subsections all valid.

**Substantive per-AC verification** (read the full `develop...feat` production diff against
`context-story-72-1.md` AC1–AC6):
- **AC1 increment** — `non_transactional_interactions += 1` in `develop_npc_on_engagement`,
  fired in the `npcs_hit` branch, de-duped per turn via `developed_this_turn`. The de-dup
  rule (+1 for a name cited twice) is the Dev-owned choice AC1 explicitly delegated. ✓
- **AC2 tier escalation** — named ladder + `tier_for_interactions(n)`, thresholds
  `ACQUAINTANCE_AT=3`/`ESTABLISHED_AT=8` as **named constants in a dedicated module**, not
  magic literals in the branch (satisfies the guardrail verbatim). Monotonic, first
  threshold > 1. ✓
- **AC3 disposition drift** — `Disposition(before + DRIFT)` (clamped ±100), band read via
  `.attitude()`. No hardcoded ±10. ✓
- **AC4 dev-tick span** — new `npc.developed` span with a registered `SpanRoute`
  (state_transition) + a `@contextmanager` opener mirroring `npc_referenced_span`, attribute
  key `npc_name` (not reserved `name`), carrying count + tier before/after, fired every
  engagement. ✓
- **AC5 disposition.shift** — the live `SPAN_DISPOSITION_SHIFT` contract is **reused** (not
  forked), gated on `delta != 0` so the clamp never emits a phantom shift. ✓
- **AC6 regression guard** — tick is confined to the `npcs_hit` branch; the diff touches no
  transactional path. ✓

**Scope-boundary audit (the "do NOT touch" list):** `_promote_pool_member_to_npc` (72-2),
`_detect_npc_identity_drift` + pool-hit upsert (72-7), OCEAN/`belief_state` (72-9), the
born-hostile `-20` default (72-5), and pool cap/prune (72-6) are all **untouched** in the
diff. No sibling work absorbed.

**Architectural note (non-blocking, not drift):** the drift leg hand-builds the
`disposition.shift` attribute dict via raw `Span.open(...)`, duplicating the shape already
hand-built at `session.py:1416`. Dev correctly followed the existing precedent (there is no
shared `disposition_shift_span` opener yet). A future DRY pass could extract one opener for
both call sites — noted for traceability, out of scope for 72-1.

**Reuse-first verdict:** exemplary. The implementation reuses the `npcs_hit` engagement
signal, the `Disposition` value type, and the `disposition.shift` span; the only new surface
is the dev-tick span (genuinely required by AC4) and a small pure module that *removes*
literal-scatter. No new infrastructure that existing code could have served.

**Decision:** Proceed to review (TEA verify phase next).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (26/26 story tests; 490-test npc/telemetry regression sweep clean)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`npc_development.py`, `narration_apply.py`, `telemetry/spans/npc.py`,
`test_npc_development_pipeline.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | `disposition.shift` hand-built dict duplicates `session.py:1416` (high) |
| simplify-quality | 2 findings | unused `RESOLUTION_TIER_LADDER` (high); redundant `npc_name` in route extract (high) |
| simplify-efficiency | clean | considered the frozen `DevelopmentTick` + named constants — judged intentional, not over-engineered |

**Applied:** 2 high-confidence fixes
- Removed the unused `RESOLUTION_TIER_LADDER` constant (verified zero references repo-wide;
  `tier_for_interactions` returns the literals directly, ladder still documented in the
  threshold comment + module docstring).
- Removed the redundant `npc_name` key from the `npc.developed` `SpanRoute` extract — every
  sibling `npc.*` route exposes the NPC name under `name` for the GM panel, so the extra key
  was pure duplication. Updated the hub wiring test to assert the routed `name` field; the
  span *attribute* stays `npc_name` (required, avoids the OTEL-reserved `name`).

**Flagged for Review:** 0 medium-confidence findings
**Noted / Deferred:** 1 — the `disposition.shift` hand-built-dict duplication between the
new drift leg and `session.py:1416`. Cross-file, touches out-of-scope `session.py`, and is
**already logged by the Architect** as a future-DRY (`disposition_shift_span` opener). Not
auto-applied; correct to defer past 72-1.
**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Regression check:** `npc_development.py` test file 26/26 green; focused sweep of
npc/watcher/disposition/span tests = 490 passed, 9 skipped, 0 failed; ruff + format clean;
pyright 0 errors on changed production files. The 16 full-suite failures remain pre-existing
and unrelated (WWN / corpora / pack-content).

**Quality Checks:** All passing.
**Commit:** `c7d16d8 refactor(72-1): simplify per verify review` (pushed).
**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (26/26 green, ruff/format/pyright clean, 0 new errors) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 5 | confirmed 2, dismissed 2, deferred 1 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 0, dismissed 2, deferred 1 |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 3, dismissed 2, deferred 3 |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 2, dismissed 3 |
| 6 | reviewer-type-design | Yes | findings | 3 | confirmed 0, dismissed 2, deferred 1 |
| 7 | reviewer-security | Yes | clean | none (minimal surface, %r-quoted logs, no PII/SQL/eval) | N/A |
| 8 | reviewer-simplifier | Yes | findings | 4 | confirmed 1 (known/deferred), dismissed 3 |
| 9 | reviewer-rule-checker | Yes | findings | 3 violations (62 instances, 13 rules) | confirmed 3 (all LOW) |

**All received:** Yes (9 returned, 7 with findings, 2 clean)
**Total findings:** 11 confirmed (all LOW / non-blocking), 14 dismissed (with rationale), 7 deferred

## Reviewer Assessment

**Verdict:** APPROVED
**Blocking issues:** None (zero Critical, zero High). The production implementation is correct,
fully observable, and within scope; every confirmed finding is LOW severity — test-quality
polish, documentation, and forward-proofing notes that do not compromise correctness or AC
coverage.

**Data flow traced:** narrator `NpcMention.name` → `_apply_npc_mentions` `npcs_hit` match →
`develop_npc_on_engagement(npc_hit)` mutates `non_transactional_interactions` / `resolution_tier`
/ `disposition` in place → `npc.developed` span (always) + `disposition.shift` span (when
`delta != 0`) → `WatcherSpanProcessor` → GM-panel hub. Safe: the name is server-resolved game
state (not raw user input), `%r`-quoted in logs, and carried as inert OTEL attribute strings
(security: clean).

**Observations (≥5):**
- `[VERIFIED]` Tier escalation is the single source of truth — the only production writers of
  `resolution_tier` are `world_materialization.py:540/869` (hardcoded `"spawn"`), the model
  default (`session.py:177`), and the tick (`npc_development.py:90` = `tier_for_interactions(count)`).
  `NpcPatch` does not expose the field. Tier and count therefore cannot diverge, so the
  unconditional `tier = tier_for_interactions(count)` is correct and never demotes today.
- `[VERIFIED]` OTEL Observability Principle satisfied — both mechanical legs emit: `npc.developed`
  fires on **every** engagement (incl. sub-threshold ticks where before==after), and
  `disposition.shift` fires whenever the value moves. Evidence: `narration_apply.py:1391-1424`,
  route at `spans/npc.py:96`. The lie-detector can see the engine counting.
- `[VERIFIED]` Phantom-shift guard correct — `if tick.disposition_delta != 0` suppresses the
  shift span at the ±100 clamp (`Disposition.__init__` clamps; before==after → delta 0). The
  mutation still records via the always-on `npc.developed` span. `narration_apply.py:1409`.
- `[SILENT]` No genuine silent failures — the `delta != 0` skip is an *intentional, documented,
  AC5-tested* no-op (not a swallowed event); the mutation-before-span ordering is a pre-existing
  infra pattern shared by every span site (mitigated by `init_tracer()` at startup), not
  introduced here. No bare excepts, no swallowed errors, no silent fallbacks in the diff
  (silent-failure-hunter: 3 findings, all dismissed as intentional/pre-existing).
- `[SEC]` Security surface minimal and clean — no SQL/eval/pickle/network; NPC name `%r`-quoted
  in `logger.info` (`narration_apply.py:1399`); no PII/secrets. (security subagent: clean.)
- `[SIMPLE]` `[TYPE]` Module structure intentional — `DevelopmentTick` frozen dataclass + named
  constants + `tier_for_interactions` form a cohesive, named, testable unit that keeps literals
  out of the apply branch (a guardrail requirement). The verify-phase efficiency lens already
  ruled this intentional; I concur and dismiss the inline-the-properties suggestions.
- `[TEST]` `[RULE]` `[EDGE]` Two vacuous assertions confirmed (LOW): `test_npc_pool...py:218`
  `all(... for n in snap.npcs)` runs over a list just proven `== []` (Rule #6); and
  `test_clamped_engagement_emits_no_phantom_shift:519` asserts inside a `for span in []` loop
  that never executes. Both still have a *real* sibling assertion in the same test, so AC
  coverage holds — but the redundant checks should be tightened to `assert _shift_spans(...) == []`.
- `[RULE]` Two test fixtures (`_isolate_thresholds`, `otel_capture`) lack return-type
  annotations (Rule #3, LOW — private underscore helpers, the rule's own exemption applies,
  but worth fixing for consistency with the suite's stated "fully annotated" claim).
- `[DOC]` `DevelopmentTick.disposition_delta` / `attitude_crossed` are the load-bearing gate
  properties and lack docstrings; the "interest is boolean-per-turn" comment
  (`narration_apply.py:1329`) is idiomatically fine but the underlying counter is an int.
- `[EDGE]` Sibling-span correlation: when a narrator `npc_attitudes` patch AND a development
  tick both fire for the same NPC/turn, two `disposition.shift` spans are indistinguishable on
  the hub (no `source` discriminator). Non-blocking observability refinement (DRY-able with the
  Architect's deferred `disposition_shift_span` opener).

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`, 13 checks — exhaustive via rule-checker, cross-confirmed)

| Rule | Instances | Verdict |
|------|-----------|---------|
| #1 silent exceptions | 3 | compliant (no try/except in diff) |
| #2 mutable defaults | 5 | compliant (`developed_this_turn` is a local, not a default arg) |
| #3 type annotations | 9 | **2 LOW violations** — fixture return types (`_isolate_thresholds`, `otel_capture`) |
| #4 logging coverage/correctness | 2 | compliant (`%`-args lazy eval, `info` level, no PII) |
| #5 path handling | 3 | compliant (no I/O) |
| #6 test quality | 26 | **1 LOW violation** — vacuous `all()` at line 218 (corroborated ×3) |
| #7 resource leaks | 3 | compliant (span ctx managers; exporter cleaned in `finally`) |
| #8 unsafe deserialization | 3 | compliant |
| #9 async pitfalls | 2 | compliant (`sleep(0.05)` is the canonical hub-wiring pattern, not `sleep(0)`) |
| #10 import hygiene | 6 | compliant (`Npc` under `TYPE_CHECKING`; no new star imports) |
| #11 input validation | 3 | compliant (server-controlled state, not raw input) |
| #12 dependency hygiene | 1 | compliant (no dep changes) |
| #13 fix-introduced regressions | 4 | compliant |
| + OTEL Observability | 3 | compliant (both legs observable) |
| + No Stubbing / dead code | 2 | compliant (simplify pass already removed the unused ladder constant) |
| + No Source-Text Wiring Tests | 26 | compliant (fixture/span-driven; hub wiring test drives real production path) |

### Devil's Advocate

Let me argue this code is broken. **First, the demotion bomb.** `develop_npc_on_engagement`
blindly overwrites `resolution_tier` from the counter alone, discarding whatever tier the NPC
already had. The moment *any* future story — 72-7's authoritative identity drift, a manual
"promote this NPC" tool, a save-migration that backfills tiers — writes `resolution_tier`
independently of the counter, the very next engagement silently *demotes* the NPC, and the
`npc.developed` span reports the regression as a routine event with no warning severity. The
GM panel, the lie-detector, would show an "established" character sliding back to "acquaintance"
and call it normal. Today the write-sites are closed (verified: only "spawn" and the tick write
the field), so it cannot fire — but the invariant "tier is a pure function of count" is
**unenforced and undocumented in the type**, a trap laid for a sibling author. **Second, the
hostile NPC.** Every disposition test starts at 0 or 99 — neutral or near-friendly. Nobody
tested a villain at `Disposition(-50)`. If the drift sign were ever wrong for negatives, or if
a future genre wanted hostile NPCs to *cool* further on engagement, no test guards it; the suite
would stay green while a hostile bartender inexplicably warms to the party that keeps insulting
him. **Third, the phantom-shift test lies.** `test_clamped_engagement_emits_no_phantom_shift`
asserts properties inside `for span in _shift_spans(...)` — when the implementation correctly
suppresses the span, the loop body never runs and the test passes *vacuously*. Delete the
`if delta != 0` guard so a zero-delta phantom span fires, and the test **still passes** — it
cannot detect the very regression it names. **Fourth, the band-cross race.** A narrator
`npc_attitudes` patch and a development tick can both fire for the same NPC on the same turn,
producing two `disposition.shift` spans with identical `npc_name`/`turn_number` and no
discriminator — the panel cannot attribute which mechanic moved the needle, blurring exactly
the engine-vs-narrator signal this epic exists to sharpen. **Verdict on the devil:** every one
of these is real but **latent or LOW** — the demotion has no live trigger, the hostile path is
arithmetically identical (+2 is +2), the vacuous test still has a sibling real assertion and the
production guard *is* covered by the intra-band test, and the span-race is an observability
refinement, not a correctness break. None rises to High. They become Delivery Findings, not a
rejection.

**Pattern observed:** clean reuse of the engagement signal + the `disposition.shift` contract;
constants extracted to a pure module — exemplary, at `npc_development.py` / `narration_apply.py:1391`.
**Error handling:** the tick has no failure modes (pure arithmetic + clamping constructor);
span-open failure is a pre-existing infra risk shared by every span site, mitigated by
`init_tracer()` at startup.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Question** (non-blocking): the tick treats `resolution_tier` as a pure function of the
  interest count (`tier = tier_for_interactions(count)`, overwriting any prior value). Safe today
  (only "spawn"/the tick write the field; `NpcPatch` omits it), but **72-7** (authoritative
  identity drift) or any future independent tier writer would make the next engagement silently
  *demote* an NPC. Affects `sidequest/game/npc_development.py` (consider a monotonic guard or a
  `Literal[...]`/StrEnum tier type) — flag the invariant before a sibling breaks it.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two vacuous test assertions — `test_npc_development_pipeline.py:218`
  (`all(... for n in snap.npcs)` over a list proven `== []`) and `:519`
  (`for span in _shift_spans(...)` body never runs when suppressed). Each test has a real sibling
  assertion so AC coverage holds; tighten to `assert _shift_spans(...) == []`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_isolate_thresholds` and `otel_capture` fixtures lack return-type
  annotations (lang-review #3). Affects `tests/server/test_npc_development_pipeline.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): no test covers a hostile (negative-disposition) NPC warming through
  engagement, nor the −100 clamp. Behavior is arithmetically correct but unguarded. Affects
  `tests/server/test_npc_development_pipeline.py` (add a `Disposition(-50)` drift case). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): when a narrator `npc_attitudes` patch and a development tick
  both fire for the same NPC/turn, the two `disposition.shift` spans are indistinguishable on the
  hub. Add a `source` discriminator (e.g. `"development_tick"`) — DRY-able with the Architect's
  deferred shared `disposition_shift_span` opener. Affects `sidequest/server/narration_apply.py`,
  `sidequest/game/session.py:1416`. *Found by Reviewer during code review.*

### Dev (implementation)
- **Improvement** (non-blocking): the 16 pre-existing full-suite failures (WWN spell
  catalog / `elemental_harmony` WWN load / namegen corpora audit / pack content + cross-ref
  validation) are unrelated to 72-1 but are red on the branch base. Affects
  `tests/genre/test_wwn_spell_catalog_load.py`, `tests/scripts/test_audit_namegen_corpora.py`,
  `tests/cli/validate/test_pack_validator*.py` (likely the still-backlog corpus-expansion
  story 64-7 + WWN/content state). *Found by Dev during implementation.*
- No blocking upstream findings during implementation.

### TEA (test design)
- **Question** (non-blocking): the dev-tick span name is unspecified by the spec. Tests
  identify it by payload (`non_transactional_interactions` attribute) and assert the `npc.*`
  convention; recommended name `npc.developed`. Dev picks the final name + registers its
  `SpanRoute`. Affects `sidequest/telemetry/spans/npc.py`. *Found by TEA during test design.*
- **Question** (non-blocking): tier ladder names/thresholds and per-engagement drift magnitude
  are Dev-owned (spec defers them). Tests pin only behavior (monotonic, crisp boundary, positive
  drift, ±100 clamp), discovered empirically — no literal hardcoded. Affects
  `sidequest/server/narration_apply.py`. *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)
Every logged deviation audited; all ACCEPTED (none flagged):
- **TEA — de-dup rule pinned to per-turn (+1)** → ✓ ACCEPTED by Reviewer: AC1 explicitly
  delegated the rule to Dev; per-turn interest (boolean-per-turn) is the sound game-design
  choice and the implementation + test agree. Sound.
- **TEA — first tier threshold assumed ≥ 2** → ✓ ACCEPTED by Reviewer: matches the
  "talks for ten turns" framing; Dev set `ACQUAINTANCE_AT=3`, consistent. Sound.
- **TEA — disposition drift sign pinned positive** → ✓ ACCEPTED by Reviewer: matches ADR-020
  "evolves through interaction"; `DISPOSITION_DRIFT_PER_ENGAGEMENT=+2` honors it. Sound.
- **Dev — fixed the TEA `_drive` helper to deep-copy each step** → ✓ ACCEPTED by Reviewer: the
  original captured a shared mutable reference, making per-step tier/disposition assertions read
  final state; the `model_copy(deep=True)` fix is correct and strengthens the suite. Sound.
- **Dev — wrapped fixture disposition args in `Disposition(...)`** → ✓ ACCEPTED by Reviewer:
  matches the codebase convention and satisfies pyright (the gate). Trivial, correct.

**Undocumented deviations found:** None. The implementation stayed within scope; all sibling
"do-not-touch" seams (72-2/5/6/7/9) are untouched (independently confirmed in spec-check).

### Dev (implementation)
- **Fixed the TEA `_drive` test helper to deep-copy each step**
  - Spec source: tests/server/test_npc_development_pipeline.py, `_drive` helper (TEA red phase)
  - Spec text: "return a snapshot of the live `Npc` after each turn (same instance — read fields per step)"
  - Implementation: `_drive` now appends `npc.model_copy(deep=True)` per turn instead of the same live reference
  - Rationale: the original appended one shared mutable `Npc`, so every list element read the FINAL tier/disposition — `test_tier_boundary_is_crisp` and `test_tier_escalation_is_monotonic` failed and the disposition-monotonic check was silently vacuous. The fix makes per-step assertions read that step's real state; behavior under test is unchanged and the implementation satisfies it.
  - Severity: minor
  - Forward impact: none — strengthens the existing tests; no production code affected.
- **Wrapped fixture disposition args in `Disposition(...)`**
  - Spec source: tests/server/test_npc_development_pipeline.py (TEA red phase)
  - Spec text: `Npc(core=_core("Boris"), disposition=0)` (raw int)
  - Implementation: `disposition=Disposition(0)` etc., matching the codebase convention (`test_npc_roster_attitude.py`, `test_update_npc_disposition.py`)
  - Rationale: raw-int relies on the pydantic coercion schema but pyright (a gate) rejects it (`Literal[0]` not assignable to `Disposition`); the `Disposition(...)` wrapper is type-correct and is the established pattern.
  - Severity: trivial
  - Forward impact: none.

### TEA (test design)
- **De-dup rule pinned to per-turn (+1), spec left it to Dev**
  - Spec source: context-story-72-1.md, AC1
  - Spec text: "The same NPC named twice in one turn's mention list increments once per engagement event — Dev to pick and document the de-dup rule; the test pins whichever rule is chosen"
  - Implementation: `test_same_npc_named_twice_in_one_turn_increments_once` asserts +1 (de-dup)
  - Rationale: interest is boolean-per-turn — the party engaged this NPC this turn or not; the narrator repeating a name in one beat is not double interest. Picking a concrete rule is required for a deterministic RED test. Dev may override to per-mention (+2) but must update this test and log the choice.
  - Severity: minor
  - Forward impact: Dev confirms or flips one assertion in GREEN.
- **First tier threshold assumed ≥ 2**
  - Spec source: context-story-72-1.md, AC2
  - Spec text: "below the first threshold the tier stays spawn … never escalates on a single transactional combat hit alone"
  - Implementation: `test_single_engagement_does_not_escalate_tier` asserts tier stays `spawn` after exactly 1 engagement
  - Rationale: the "talks for ten turns" framing and recommended `spawn→acquaintance→established` ladder imply the first escalation is not at a single interaction. If Dev sets threshold=1 they must log a deviation and adjust this test.
  - Severity: minor
  - Forward impact: constrains the first threshold to ≥ 2.
- **Disposition drift sign pinned positive**
  - Spec source: context-story-72-1.md, AC3 / Assumptions
  - Spec text: "A small positive warm on neutral engagement is the assumed default … the precise delta … is Dev's call, documented and test-pinned"
  - Implementation: AC3 tests assert disposition increases and saturates at +100
  - Rationale: matches ADR-020 "evolves through interaction" + the documented default. Magnitude is left free (tests don't assert a specific per-turn delta).
  - Severity: minor
  - Forward impact: a negative/neutral drift design would require re-pinning AC3.

### Architect (reconcile)

**Existing entries verified.** All five logged deviations (3 TEA, 2 Dev) were checked against the
code and the spec: spec-source paths exist (`context-story-72-1.md`,
`tests/server/test_npc_development_pipeline.py`), the quoted spec text is accurate, the
implementation descriptions match the merged code (`ACQUAINTANCE_AT=3` honors "first threshold ≥
2"; `DISPOSITION_DRIFT_PER_ENGAGEMENT=+2` honors "positive drift"; the de-dup set yields +1;
`_drive` deep-copies; fixtures use `Disposition(...)`), forward-impact is accurate, and all six
fields are present. No corrections needed.

**Missed deviation — recorded now:**
- **Development-tick span carries count + tier only; disposition lives solely on the reused `disposition.shift` span**
  - Spec source: context-story-72-1.md, "Technical Guardrails → OTEL" paragraph
  - Spec text: "The development tick should emit, per engaged NPC: `non_transactional_interactions` (new count), `resolution_tier` old → new, **and the disposition before/after + `crossed`** (parallel to the `disposition.shift` route…)"
  - Implementation: `npc_developed_span` (`telemetry/spans/npc.py`) emits only `npc_name`, `non_transactional_interactions`, `resolution_tier_before/after`, `turn_number`. The disposition before/after/`crossed` data is emitted **exclusively** on the reused `SPAN_DISPOSITION_SHIFT` span (`narration_apply.py:1412`), not duplicated onto the development-tick span.
  - Rationale: AC4 requires the dev-tick span carry "at minimum: `npc_name`, count, `resolution_tier` old→new"; AC5 assigns the full disposition contract to the reused `disposition.shift` span. Following the ACs (higher authority than the context's implementation guidance) avoids emitting the same disposition deltas on two spans — a cleaner, single-source observability split. The context's "+ disposition" suggestion was guidance, not an AC. The GM panel still sees the full tick by correlating the two spans on `npc_name`+`turn_number` (the Reviewer logged a non-blocking `source`-discriminator improvement for the rare same-turn narrator-patch collision).
  - Severity: minor
  - Forward impact: none for siblings. If a future GM-panel consumer wants the whole tick in one event, add the disposition fields to `npc_developed_span` (additive) — but the current split is intentional and AC-aligned.

**AC deferrals:** none — the story had no formally-deferred ACs (AC1–AC6 all implemented and green); this step is a no-op. The "deferred" items in the Reviewer's table are non-blocking follow-up findings, not AC deferrals.