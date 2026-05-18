---
story_id: "50-26"
jira_key: null
epic: null
workflow: tdd
---
# Story 50-26: Harden ADR-106 curate stage against truncated JSON — no frozen turn, loud degrade-to-uncurated

## Story Details
- **ID:** 50-26
- **Jira Key:** None (SideQuest is a personal project, no Jira)
- **Workflow:** tdd (phased)
- **Stack Parent:** none

## Bug Context
**Source:** /Users/slabgorb/Projects/sq-playtest-pingpong.md, the "[BS-BUG] Dungeon curation pass returns truncated/unterminated JSON -> materializer raises CurationError, freezing the turn (~9-min table dead-air on the R3 descent)" headline (GM/Architect OQ-1, 2026-05-17).

**Deterministic failure mode:** The curate-stage LLM (claude -p curate, ADR-106 materializer) emits a large wandering_table JSON that is cut mid-string (token cap / streaming cut); `_parse_curation_verdict` does a strict `json.loads` with NO repair / retry-with-continuation / bounded-timeout-then-degrade, so the JSONDecodeError becomes `sidequest.dungeon.materializer.CurationError` (raised materializer.py:914 `_stage_curate` -> :749/:747 `_parse_curation_verdict`, observed shapes: 'Unterminated string starting at: line 452 column 17', 'Expecting value: line 429 column 25', head `{"exp001.r0":{"race":"undead","cr_band":"shallow","wandering_table":[{"name":"Skeleton",...}`) which propagates unhandled and freezes the narration turn — a multi-minute submit-and-wait dead-air with zero player feedback, the worst MP failure mode for the Alex/whole-table pacing axis, and a No-Silent-Fallbacks gap in the ADR-106 curate stage.

**Read full Root-cause and Honest-caveat bullets** in sq-playtest-pingpong.md before touching code.

## Workflow Tracking
**Workflow:** tdd (phased)
**Phase:** finish (SM/Pierce — Reviewer APPROVED, spec-reconcile manifest complete; all gates green. Finish: land the orchestrator-side ADR-106 Amendment A + `sprint/epic-50.yaml` into the story git flow [the load-bearing post-merge risk flagged by Dev/Architect/Reviewer], PR+merge `feat/50-26-harden-curate-truncated-json` → develop, `pf sprint story finish 50-26`, then mark the pingpong dungeon-CurationError entry `fixed`)

**GATING PRECONDITION (CRITICAL — pingpong explicitly routes this):** Do NOT blind-patch the parser. The policy choice — JSON repair vs retry-with-continuation vs degrade-to-uncurated-room — is an Architect contract decision under ADR-106 and MUST be recorded (ADR-106 amendment or a design note referenced by the implementation) BEFORE GREEN. The implemented behaviour must be exactly the recorded policy.

**Phase Started:** 2026-05-18T14:16:58Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-18 | 2026-05-18T13:30:28Z | 13h 30m |
| red | 2026-05-18T13:30:28Z | 2026-05-18T13:43:43Z | 13m 15s |
| green | 2026-05-18T13:43:43Z | 2026-05-18T13:58:56Z | 15m 13s |
| spec-check | 2026-05-18T13:58:56Z | 2026-05-18T14:01:25Z | 2m 29s |
| verify | 2026-05-18T14:01:25Z | 2026-05-18T14:07:29Z | 6m 4s |
| review | 2026-05-18T14:07:29Z | 2026-05-18T14:12:58Z | 5m 29s |
| finish | 2026-05-18T14:12:58Z | - | - |

## Acceptance Criteria

**AC-1 (Architect contract decision recorded, GATING — precedes GREEN):** The repair-vs-retry-with-continuation-vs-degrade-to-uncurated policy is decided by the Architect under ADR-106 and written down (ADR-106 amendment or a session design note the implementation references). Verifiable: the recorded decision exists and the shipped behaviour matches it exactly; a reviewer can point at the policy doc and the code path that implements it.

**AC-2 (no frozen turn):** A truncated/unterminated curate-stage JSON response no longer produces an unhandled CurationError that propagates and blocks the narration turn. Verifiable (RED first): a test feeds `_stage_curate` / `_parse_curation_verdict` the exact pingpong failure shapes (Unterminated string at line 452 col 17; Expecting value line 429 col 25; the `{exp001.r0:{race:undead,cr_band:shallow,wandering_table:[{name:Skeleton...}` truncated head) and asserts the materialize resolves within a bounded time budget per the AC-1 policy (repaired parse, or a degraded uncurated room) — the exception does NOT escape `_stage_curate`.

**AC-3 (loud + observable — No-Silent-Fallbacks + OTEL mandate):** Every curate-parse failure AND every degrade-to-uncurated fallback emits a routed OTEL span / watcher event (e.g. `dungeon.curate.parse_failed` / `dungeon.curate.degraded`) carrying `region_id`, `failure_kind`, and `retry_count`, GM-panel visible. A degraded room is explicitly flagged uncurated in the materialized state, never silently swapped for a curated one. Verifiable: the span fires in the AC-2 test and the degraded region carries the uncurated marker.

**AC-4 (bounded, non-looping):** If the AC-1 policy includes retry-with-continuation, it is capped by an explicit budget (max attempts AND wall-clock) that provably cannot loop; budget exhaustion deterministically falls through to the degrade path. Verifiable: a test forces repeated truncated responses and asserts the attempt count is capped and the degrade path is taken (no unbounded loop, no second freeze).

**AC-5 (wiring — not a parser unit test in isolation):** The robustness path is exercised end-to-end through the real `dungeon/materializer.py` `materialize` -> `_stage_curate` -> `_parse_curation_verdict` chain (ADR-106 production path), proving it is reachable from a real expansion materialize (the exp001.r0-style first-descent expansion), per CLAUDE.md "every test suite needs a wiring test".

## Sm Assessment

**Story setup: COMPLETE. Setup-exit gate: passing. Routing to RED (TEA / Radar).**

**Origin & scoping.** Surfaced in the 2026-05-17 beneath_sunden MP playtest pingpong as a `[BS-BUG]` (status: open) — a ~9-minute table dead-air freeze on the R3 descent when the ADR-106 curate stage hit a truncated/unterminated JSON verdict. Scoped as story `50-26` (epic 50; p1; 5pts; type bug; workflow tdd; repos sidequest-server) with a full description + 5 ACs derived verbatim from the pingpong, copied above. Pingpong remains the source of truth for the bug; this story is the tracked vehicle for the fix.

**Workflow decision (user-chosen, Option B).** The pingpong explicitly routes the policy choice (repair vs retry vs degrade) to the Architect under ADR-106. Two viable shapes were presented to the user: (A) `bdd` with a design phase, or (B) `tdd` + an Architect pre-step that records the contract as a first-class artifact before RED — matching the proven `50-24` precedent. **User selected B.** Rationale: keeps the ADR decision a recorded, auditable artifact rather than burying it in a workflow phase, and reuses the pattern that already worked on the sibling story. Phase sequence: setup → (Architect pre-step) → red → green → review → finish.

**Architect pre-step: DONE.** Houlihan recorded the contract as **`docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → Amendment A** and updated this session's `## Design Deviations`. Policy = layered bounded (Layer 0 keep `max_tokens=16384` already-on-develop; Layer 1 one bounded whole-call retry, ADR-098-compatible, NOT JSON repair; Layer 1 wall-clock cap; Layer 2 LOUD degrade-to-uncurated stamped `curated=false` + span + marker; `CurationError` retained + per-region isolation). AC-1 is satisfied by that amendment. Material forensic finding: the playtest's specific truncation sub-case is *already mitigated on develop* by `b846544` (max_tokens 4096→16384, landed 2026-05-17 19:22 — after the freeze window); 50-26's real contribution is the bounded-latency + loud-degrade contract for the *residual* unparseable paths.

**Setup defect noted (process learning).** `sm-setup` MODE=setup wrote the session to `sidequest-server/.session/50-26-session.md`; the handoff CLI and the archive convention (sibling `50-24` archived at orchestrator `sprint/archive/`) require the orchestrator path `.session/50-26-session.md`. Houlihan relocated it (content intact). The SM post-setup verification also checked the server path and missed this. **Process fix for sm-setup:** for repo-scoped stories, the session file belongs at the orchestrator `.session/`, and the post-setup `ls` check must verify that path — not the target repo's `.session/`. Flagging for retro / sm-setup correction; not blocking this story (file is now correctly placed).

**Branch:** `feat/50-26-harden-curate-truncated-json` cut off `develop` in sidequest-server (per repos.yaml — sidequest-server targets develop). Story `in_progress` since 2026-05-18. No Jira (personal project).

**Handoff to TEA (Radar):** write RED against ADR-106 Amendment A (the normative spec). RED targets are enumerated at the end of the `## Design Deviations` Architect entry — feed the pingpong failure shapes through the real `materialize → _stage_curate → _parse_curation_verdict` chain; assert no escaped `CurationError`, Layer-2 `curated=false` + `uncurated` marker, `dungeon.curate.degraded` span, attempts capped at 2, per-region isolation. Do not implement (that is Winchester's GREEN); watch the tests fail first.

## TEA Assessment

**RED phase: COMPLETE. State verified RED. Handing to Dev (Winchester) for GREEN.**

**Tests written** — all in `sidequest-server/tests/dungeon/test_materializer.py`, branch `feat/50-26-harden-curate-truncated-json`, commits `57513f5` (main RED batch) + `04caf36` (rule-enforcement). New class `TestStageCurateRobustness` (10 tests) + one rewritten superseded test. Reuses the existing curate harness (`_real_cookbook_bundle`, `_curate_inputs`, `_setup_otel_task3`, `dungeon_materialize_curate_span`) — new SDK fakes added module-level beside `_failing_sdk_client` (no fixture duplication).

**RED verified** (testing-runner, RUN_ID `50-26-tea-red`): collection clean (no import/syntax/harness errors); **9/10 robustness tests + the rewritten test + the rule test FAIL on the contract** (CurationError raised; `AttributeError: RegionCuration has no 'uncurated_regions'`; no `dungeon.curate.degraded`/`parse_failed` spans; no `CURATE_DEADLINE_S`; no ERROR log). The single early-PASS is `test_missing_cr_still_raises_curation_error_retained_carveout` — the **retained-`CurationError` regression guard** (carve-out ii); PASS is correct and it MUST stay green after GREEN.

**AC → test map:**
- **AC-2** (no frozen turn) → `test_truncated_verdict_does_not_escape_stage_curate`, `..._completes_through_real_materialize_chain`
- **AC-3** (loud + observable) → `..._degrades_loud_curated_false_with_content`, `test_degrade_emits_routed_dungeon_curate_degraded_span` (asserts routed in `SPAN_ROUTES`), `test_degrade_logs_at_error_level_not_swallowed_silently`
- **AC-4** (bounded, non-looping) → `test_retry_is_bounded_exactly_one_retry_then_degrade` (call count == 2; parse_failed attempt 1,2), `test_wall_clock_cap_degrades_with_deadline_failure_kind`
- **AC-5** (wiring) → `test_truncated_verdict_completes_through_real_materialize_chain` (real `materialize` chain, mandatory wiring test per CLAUDE.md)
- **Per-region isolation** → `test_per_region_isolation_one_bad_region_siblings_curated`
- **Retry recovers (anti-vacuous)** → `test_retry_recovers_no_degrade_when_second_attempt_valid`
- **Forbidden silent fallback** → `curated is not True` asserted in the two degrade tests
- **AC-1** is the recorded ADR-106 Amendment A (Architect) — not a code test; the suite pins behaviour *exactly* to that amendment.

**Rule Coverage (lang-review/python.md):**
- **#1 Silent exception swallowing** (the story's core, == CLAUDE.md No-Silent-Fallbacks) → enforced by `test_degrade_logs_at_error_level_not_swallowed_silently` (ERROR-level `caplog` assertion) + every degrade test requiring the `dungeon.curate.degraded` span. A Dev implementing Layer-2 as `except Exception: pass` fails these.
- **#42 Logging discipline / error paths must log error/warning** → same ERROR-log test (Layer-2 is an error path).
- **#60–63 Test quality** → self-checked: no `assert True`/vacuous truthy; the no-escape test asserts `isinstance(result, RegionCuration)` (not a bare call); `test_retry_recovers...` is the explicit anti-vacuous control proving retry is not an always-degrade stub.
- **#33–36 Type annotations** / **#3 broad except** → not TEA-testable cleanly; flagged for Reviewer (Potter) — Dev's new degrade/retry code must be fully annotated and must catch `json.JSONDecodeError` / the specific `LlmClientError`, never bare `except`.

**Test-pinned API the GREEN must satisfy (Architect spec-check may rename; behaviour is fixed):**
1. `RegionCuration.uncurated_regions: frozenset[str]` (default empty); `RegionCuration.curated` becomes the expansion rollup (False iff any region degraded — a degraded region is NEVER stamped True).
2. Span names `dungeon.curate.parse_failed` (per attempt; attrs `region_id`, `failure_kind`∈{truncated,malformed,llm_error,deadline}, `attempt`) and `dungeon.curate.degraded` (attrs `region_id`, `failure_kind`, `attempts`, `elapsed_ms`), **both registered in `SPAN_ROUTES`** (clause-12 GM-visible).
3. An injectable wall-clock cap `materializer.CURATE_DEADLINE_S` so AC-4's deadline is verifiable without a 25 s test.
4. Layer-2 emits an ERROR-level log naming the curate degrade.

**Contract supersession (flag for Architect spec-check + Dev):** the pre-existing `test_curation_subprocess_failure_raises_and_records_curated_false` asserted `LlmClientError → raise CurationError`. ADR-106 Amendment A makes `llm_error` an enumerated degrade `failure_kind` and it is NOT one of the two retained carve-outs → it must degrade, not raise. The test is **rewritten** (`test_curation_llm_failure_degrades_loudly_not_raises_amendment_a`) to the new contract, retaining the stage-span `curated=False` lie-detector assertion. This is a deliberate contract change recorded as a deviation below — not test vandalism.

**Handoff to Dev (Winchester):** make GREEN by implementing ADR-106 Amendment A exactly — Layer-1 one bounded whole-call retry (2 attempts, no JSON repair), Layer-1 `CURATE_DEADLINE_S` wall-clock cap, Layer-2 loud degrade (ship `assemble_region` manifest, `curated=False`, `uncurated_regions` marker, ERROR log, routed `dungeon.curate.{parse_failed,degraded}` spans), per-region isolation, `CurationError` retained for the two carve-outs. Do NOT weaken the retained-raise guard (`test_missing_cr_*`) or the anti-vacuous retry-recovers test. New code must be type-annotated and catch specific exceptions (no bare/broad except). ADR-106 Amendment A is the spec; no improvisation past it.

## Dev Assessment

**Implementation Complete:** Yes — ADR-106 Amendment A implemented exactly to contract, no improvisation.

**Files Changed (sidequest-server, branch `feat/50-26-harden-curate-truncated-json`, pushed):**
- `sidequest/dungeon/materializer.py` — `_stage_curate` rewritten: Layer-0 `max_tokens=16384` retained; Layer-1 bounded whole-call retry (exactly 2 attempts, each an independent one-shot — ADR-098, NOT JSON repair) wrapped in `async with asyncio.timeout(CURATE_DEADLINE_S)`; Layer-2 loud per-region degrade. New module constant `CURATE_DEADLINE_S = 25.0` (injectable for AC-4). New `RegionCuration.uncurated_regions: frozenset[str]`; `curated` is now the expansion rollup (False iff any region degraded). New helpers `_classify_parse_failure`, `_creatures_from_manifest` (carve-out i raise), `_degrade_region` (ERROR log + degraded span + manifest content). Per-region isolation in the parsed-verdict branch; carve-out (ii) row-missing-`cr` still raises `CurationError`. Specific excepts only (`LlmClientError`, `CurationError`, `TimeoutError`) — no bare/broad except.
- `sidequest/telemetry/spans/dungeon_materialize.py` — `SPAN_DUNGEON_CURATE_PARSE_FAILED` / `SPAN_DUNGEON_CURATE_DEGRADED` constants, two `SPAN_ROUTES` registrations (clause-12 routed/GM-visible), two contextmanager helpers, `__all__`.
- `tests/dungeon/test_lookahead_worker.py` — superseded-test retarget (see Dev deviation #1): `_failing_sdk_client` → `_missing_cr_sdk_client` (carve-out ii still hard-raises), docstring/comments updated. No assertion weakened.

**Tests:** Story suite **14/14 GREEN** (`TestStageCurateRobustness` 11 incl. the rule-enforcement + retained-raise guard; `TestStageCurate` 4 incl. the rewritten `llm_error` degrade test + the 3 pre-existing curated-path tests). Regression envelope (`test_materializer.py` + `test_materializer_wiring.py` + `test_lookahead_worker.py` + `tests/telemetry/`) **291 passed / 0 failed / 0 errors**. `ruff check` clean on all changed files.

**Branch:** `feat/50-26-harden-curate-truncated-json` — commits `57513f5`+`04caf36` (RED, TEA) → `e2dbc87` (GREEN, Dev), pushed to origin.

**Scope discipline:** minimal helpers, every one required by a test or a spec-mandated carve-out; no abstractions beyond the contract; the retry budget/deadline/marker/spans/carve-outs are exactly Amendment A. Two deviations logged (superseded lookahead test retarget; carve-out (i) implemented-but-not-RED-covered) + two non-blocking findings (orchestrator-side ADR/sprint artifacts need committing by SM/finish; carve-out (i) test follow-up).

**Handoff:** To verify/review per the tdd workflow.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

I authored ADR-106 Amendment A; this spec-check verifies the shipped code (`e2dbc87`) against it clause-by-clause and AC-by-AC.

**Clause conformance (all ✓):**
- Layer 0 — `max_tokens=16384` retained (`# Layer 0 (retained)`).
- Layer 1 — `for attempt in range(1, 3)` = exactly 1 retry / 2 attempts; each `_one_attempt()` is an independent one-shot (`complete_with_tools` → `_parse_curation_verdict`, no `--resume`/continuation, NOT JSON repair). ADR-098-compatible.
- Layer 1 deadline — `async with asyncio.timeout(CURATE_DEADLINE_S)` wraps the whole retry loop; `except TimeoutError` → `failure_kind="deadline"`. `CURATE_DEADLINE_S=25.0` module-level/injectable.
- Layer 2 — `_degrade_region` emits `logger.error(...)` (loud) + routed `dungeon.curate.degraded` span + ships `_creatures_from_manifest` (the deterministic assemble_region content); `uncurated.add(region_id)`.
- Forbidden invariant — `curated = len(uncurated) == 0`; a degraded expansion returns `curated=False` + populated `uncurated_regions`. Never stamped True. ✓
- CurationError retained — carve-out (i) `_creatures_from_manifest` raises on an invalid assembled manifest; carve-out (ii) parsed row missing `cr` raises. Both still hard-raise. ✓
- Per-region isolation — parsed-verdict branch degrades only the structurally-invalid region (`continue`); siblings stay curated; expansion never aborts. ✓
- Span taxonomy — `dungeon.curate.parse_failed` per failed attempt (region_id/failure_kind/attempt) + `dungeon.curate.degraded` (region_id/failure_kind/attempts/elapsed_ms); both registered in `SPAN_ROUTES` (clause-12 GM-visible). ✓

**AC conformance:** AC-1 ✓ (Amendment A exists; code references it by name — a reviewer can point at the doc and `_stage_curate`). AC-2 ✓ (deadline + Layer-2 guarantee; no escaped `CurationError` on the truncated path; tests green). AC-3 ✓ (spans + ERROR log + `uncurated_regions` marker). AC-4 ✓ (`range(1,3)` hard cap AND wall-clock cap, deterministic degrade — provably non-looping). AC-5 ✓ (wiring test through the real `materialize` chain green).

**Adjudication of the two flagged supersessions (both are consequences of MY Amendment A — I am the authority):**

1. **TEA's `llm_error` raise→degrade test rewrite — CONFIRMED INTENDED (Resolution A — spec already mandates it; the test now matches the spec).** Amendment A's `failure_kind` enum explicitly lists `llm_error`, and the no-freeze principle is universal. An `LlmClientError` is neither carve-out (i) nor (ii). Therefore by the contract it MUST Layer-2 degrade, not raise. The old test pinned pre-Amendment behaviour. No spec change, no code hand-back.
2. **Dev's lookahead-worker test retarget (`_failing_sdk_client`→`_missing_cr_sdk_client`) — CONFIRMED INTENDED (Resolution A).** Same root: a generic curate failure no longer aborts the look-ahead worker (it degrades, expansion commits uncurated). Retargeting to carve-out (ii) — the path my contract explicitly *retains* as still-aborting — preserves the test's central-constraint intent (a prefetch failure must not abort the party's crossing) against a still-valid hard failure. Correct, minimal, no coverage lost.

**Confirmed interpretation (pre-empt a Reviewer false-flag):** the code retries once on BOTH `CurationError` (unparseable) AND `LlmClientError` before degrading. Amendment A's Layer-1 text says "on an unparseable verdict" but the `failure_kind` enum includes `llm_error` and Layer-2's trigger is "retry-exhaustion OR deadline". Retrying a transient API blip once within the same 1-retry budget before the loud degrade is the intended reading and does not violate the bounded contract (still exactly 1 retry, still degrades). Aligned, not drift.

**Carve-out (i) coverage gap (Dev finding) — no spec/code mismatch; Resolution D (defer).** The code matches the spec (Amendment A mandates carve-out (i); `_creatures_from_manifest` implements it). It is RED-uncovered only because the real cookbook never yields an invalid assembled manifest in-test. Deferred to TEA-verify as a suggested follow-up (inject an invalid manifest to lock carve-out (i)); not blocking — the path is spec-mandated, code-reviewed, and exists to prevent over-degradation.

**Escalation (not a spec-check mismatch — a delivery/integration risk for SM/finish):** Amendment A lives in the **orchestrator** repo (`docs/adr/106-...md`), currently uncommitted on `main`; the code on `feat/50-26-...` references it by name. AC-1 ("a reviewer can point at the policy doc") breaks post-merge if the amendment never lands on develop. The orchestrator-side ADR amendment + `sprint/epic-50.yaml` MUST be committed into the story's git flow by SM/finish. Flagged loudly here so it is not lost.

**Decision:** Proceed to review (TEA verify → Reviewer). No mismatches; both supersessions confirmed intended; one deferred coverage note; one integration risk escalated to finish.

## TEA Assessment (verify)

**Verify phase: COMPLETE. Quality-pass GREEN. Routing to Reviewer (Potter).**

**Simplify fan-out** (3 parallel teammates — reuse / quality / efficiency — over the 4 changed files vs `develop`). Fan-in + confidence triage:

- **APPLIED — 1 fix** (simplify-quality, high, in-scope): `test_dungeon_materialize_spans_registered_and_routed` asserted 7 dungeon spans but not the two ADR-106 Amendment A additions — a genuine clause-12 / OTEL-lie-detector wiring-completeness gap I introduced in RED. Added `SPAN_DUNGEON_CURATE_PARSE_FAILED` + `SPAN_DUNGEON_CURATE_DEGRADED` to the gate + corrected the docstring. Commit `a0ccddd` (pushed). Re-verified: **240 passed / 0 failed**, `test_dungeon_materialize_spans_registered_and_routed` + all 10 `TestStageCurateRobustness` + `tests/telemetry/` green. Ruff clean.
- **DISMISSED with rationale:**
  - simplify-efficiency E1 (inline `_one_attempt`, high): the closure is a deliberate readability boundary delineating "the retried unit"; no reuse claimed → not premature abstraction. Inlining 8+ lines into a contract-critical retry loop obscures control flow. Net-negative.
  - simplify-efficiency E2 (inline `region_ids_repr`, high): the named var documents the whole-document parse-failed span scope; inlining recomputes in a 2-iteration loop and removes the documenting name. No improvement.
  - simplify-efficiency E3 (on-demand `degrade_kind`/`reason`, med): the defaults are defensive against an UnboundLocal on the `verdict is None`/no-classification edge — correctness, not complexity.
  - simplify-quality Q2 (`lookahead_worker.py:213` broad except, med): PRE-EXISTING code not touched by 50-26 (only the test client was swapped); the noqa + central-constraint justification is the existing architectural decision. Out of scope.
  - simplify-quality Q3/Q4/Q5, simplify-reuse R2/R4 (low): cosmetic / self-dismissed / pre-existing parallelism. No value.
  - Houlihan's spec-check already validated this exact structure as Aligned — I will not churn GREEN, contract-critical code for stylistic deltas.
- **DEFERRED as findings** (recorded below — scope discipline, NOT bundled into a p1 fix mid-pipeline):
  - simplify-reuse R3 (high): `_otel_in_memory()` duplicated in `test_materializer.py:45` + `test_lookahead_worker.py:67` — **pre-existing**, neither introduced by 50-26. Moving to `conftest.py` touches shared dungeon test infra across the suite — a separate refactor story, not curate-robustness.
  - simplify-reuse R1 (med): big_bad CR→Edge resolution mirrored between `_creatures_from_manifest` (Layer-2/carve-out i) and the `_stage_curate` verdict loop (Layer-1). Intentional per the in-code comment; the two sites carry *different* carve-out error semantics. A `_resolve_big_bad_cr` extraction is reasonable but entangling the carve-out paths mid-pipeline on a p1 fix is unjustified risk. Future cleanup.

**Bottom line:** RED→GREEN→spec-check→verify all green; story suite 14/14; regression 291/291; routing-completeness now covers the Amendment A spans. Ready for Potter.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (639 passed/0 failed, 0 lint, 0 type, 0 smells, tree clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered manually (Devil's Advocate + Rule 9 enumeration) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain covered manually (Rule 1 enumeration) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain covered manually (Rule 6 + deviation audit) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain covered manually |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain covered manually (Rule 3 enumeration) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain covered manually (Rule 11 — no boundary/input/secret surface in diff) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by the verify-phase simplify trio (TEA Assessment (verify)) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain covered manually (Rule Compliance section below) |

**All received:** Yes (1 enabled returned clean; 8 disabled via `workflow.reviewer_subagents`, domains covered manually per the review-checklist)
**Total findings:** 0 confirmed Critical/High, 0 dismissed, 3 deferred (pre-existing/contingent — see Delivery Findings)

## Reviewer Assessment

**Verdict:** APPROVED

**Verdict basis:** No Critical/High. ADR-106 Amendment A is implemented exactly to contract (Houlihan's spec-check independently verified Aligned/no-mismatch); preflight 639/0; the two superseded tests were retargeted to the new contract (not weakened); the verify-phase simplify trio + this adversarial pass surface only pre-existing/contingent low-severity items, all deferred with rationale.

### Observations (≥5, dispatch-tagged; subagents 2–9 disabled → I cover their domains)

- `[SILENT]` **[VERIFIED]** No silent swallow — `materializer.py:1054` catches `(LlmClientError, CurationError)` and `:1063` `TimeoutError` (specific, never bare/broad); the degrade path is LOUD (`_degrade_region` → `logger.error(...)` + routed `dungeon.curate.degraded` span); carve-outs (i)/(ii) `raise CurationError` out (not swallowed). Complies with lang-review #1.
- `[EDGE]` **[VERIFIED]** Bounded/non-looping — `for attempt in range(1, 3)` (hard 2-attempt cap) inside `async with asyncio.timeout(CURATE_DEADLINE_S)` (wall-clock cap); `attempts or 1` guards the timeout-before-iteration edge; `verdict is None` ⇒ deterministic Layer-2 degrade. No unbounded loop, no second freeze. Evidence: `materializer.py:1048-1066`.
- `[TYPE]` **[VERIFIED]** Full annotations — `verdict: dict[str, Any] | None`, `uncurated: set[str]`, `CURATE_DEADLINE_S: float`, `RegionCuration.uncurated_regions: frozenset[str]`, all 3 new helpers fully typed; pyright clean (preflight). `frozenset()` default is immutable (no lang-review #2 mutable-default bug). Complies with #3.
- `[SEC]` **[VERIFIED]** No new security surface — the curate verdict is an internal `claude -p` artifact, not user input; no auth/secrets/tenant/path/deserialization introduced (lang-review #11/#8/#5 N/A to this diff). `json.loads` on a bounded (~16 KB) internal string.
- `[EDGE]` **[VERIFIED]** Per-region carve-out asymmetry is intentional — structurally-invalid region ⇒ `_degrade_region`+`continue` (siblings stay curated); a parsed row missing `cr` ⇒ `raise CurationError` (carve-out ii, aborts by design — degrading would corrupt CR→Edge). Checked against Amendment A: this is the explicit retained carve-out, NOT a per-region-isolation violation. Houlihan's spec-check ACCEPTED.
- `[SIMPLE]` **[VERIFIED]** No over-engineering introduced — the verify-phase simplify trio already triaged; `_one_attempt`/`region_ids_repr` are readability boundaries, not abstractions-for-reuse; helpers are each test- or spec-mandated. Concur with TEA's triage.
- `[DOC]` **[VERIFIED]** Comments accurate — the Amendment-A block comment in `_stage_curate`, the carve-out docstrings, and the corrected routing-test docstring match behaviour; no stale/misleading comments in the diff. New spans documented in `dungeon_materialize.py` SpanRoute blocks.
- `[RULE]` **[VERIFIED]** Async correctness (#9) — `verdict = await _one_attempt()` (no missing await); no `asyncio.gather`; `time.monotonic()` non-blocking; the only sync CPU in the timeout window is `json.loads` on a bounded string (µs — not a freeze). Import hygiene (#10) — `asyncio`/`logging`/`time` added cleanly, span helpers alphabetised into the existing import block, `__all__` updated, no star/circular imports.
- `[TEST]` `[LOW]` carve-out (i) (`_creatures_from_manifest` raising on an invalid assembled manifest) has no direct test — spec-mandated, code-reviewed, prevents over-degradation. Already a Dev/TEA finding; deferred, non-blocking.
- `[EDGE]` `[LOW]` (Devil's-Advocate-surfaced) the no-freeze guarantee is contingent on `complete_with_tools` yielding at an `await`; a future synchronous/blocking backend would defeat `asyncio.timeout` and re-introduce the freeze. Not a defect in this diff (the SDK one-shot is awaitable per ADR-098); recorded as a Question for the Architect/future maintainers.

### Rule Compliance (lang-review/python.md — manual, rule-checker disabled)

- **#1 Silent exception swallowing:** COMPLIANT. Only specific excepts (`(LlmClientError, CurationError)`, `TimeoutError`); degrade path is loud (ERROR log + span); carve-out raises propagate. Enumerated every `except` in the diff — no bare/broad/`pass`-swallow.
- **#2 Mutable default args:** COMPLIANT. `uncurated_regions: frozenset[str] = field(default=frozenset())` — immutable. No `[]`/`{}`/`set()` defaults in new signatures.
- **#3 Type annotations at boundaries:** COMPLIANT. All new fns/constants/fields annotated; pyright clean.
- **#4 Logging coverage+correctness:** COMPLIANT. The new error path (`_degrade_region`) logs at ERROR (not debug); `%`-style args, no sensitive data.
- **#6 Test quality:** COMPLIANT. RED suite has meaningful assertions (verified during TEA phase); the two retargeted tests strengthened (not weakened); a deliberate anti-vacuous retry-recovers control exists.
- **#9 Async pitfalls:** COMPLIANT (see `[RULE]` above).
- **#10 Import hygiene:** COMPLIANT (see `[RULE]` above).
- **#13 Fix-introduced regressions:** COMPLIANT. Preflight 639/0; retargeted tests adjudicated intended by Architect spec-check.
- **#14 State-cleanup ordering:** N/A — no consume-then-clear queue/buffer in the diff.
- **#5/#7/#8/#11/#12:** N/A — no path handling, resource handles, deserialization, external-input boundary, or dependency changes in this diff.

### Devil's Advocate

Assume this is broken. Where? **(1) The wall-clock guarantee is a promise the diff cannot fully keep alone.** `asyncio.timeout` only interrupts at an `await`. The entire no-freeze contract — the load-bearing reason this p1 story exists — rests on `complete_with_tools` actually suspending at an awaitable I/O point. The current SDK client does; ADR-098 mandates the one-shot SDK path. But nothing in *this diff* enforces that a future/alternate backend stays awaitable, and `_parse_curation_verdict`'s `json.loads` runs synchronously inside the timeout window — on a pathologically large (multi-MB) verdict it is uninterruptible CPU. At the contractual ≤16 KB it is microseconds, so not a live freeze, but the guarantee is *contingent*, not *absolute*. Recorded as a non-blocking Question. **(2) A confused curator that returns valid JSON with thousands of phantom region keys?** Harmless — the loop iterates `manifests.items()` (bounded by `expansion.new_nodes`/burst); extra verdict keys are ignored. **(3) Concurrency:** multiple look-ahead workers in `_stage_curate` concurrently — all state (`verdict`/`attempts`/`uncurated`/spans) is function-local; `CURATE_DEADLINE_S` is read-only at runtime (tests monkeypatch, prod constant). No shared-mutable race. **(4) Stressed filesystem / partial writes:** `_stage_curate` does no I/O itself; persistence is downstream (commit), unchanged by this diff. **(5) The retry double-charges latency:** two failed ~10–20 s curate calls before degrade ≈ up to ~40 s — but the wall-clock cap (`CURATE_DEADLINE_S=25`) bounds it; the cap, not the retry count, is the real ceiling. Correct. **(6) `attempts or 1`** could mislabel a 0-attempt timeout as 1 attempt in the span — cosmetic telemetry only, not a correctness bug. Conclusion: the one substantive devil's-advocate point (contingent awaitability) is recorded as a Question; nothing rises to blocking.

### Deviation Audit

- **Architect (pre-RED contract decision) — Amendment A recorded** → ✓ ACCEPTED by Reviewer: the gating contract; code conforms clause-by-clause; Houlihan's own spec-check independently verified Aligned.
- **TEA (test design) — `llm_error` raise-test rewritten to degrade** → ✓ ACCEPTED by Reviewer: direct, intended consequence of Amendment A's `failure_kind` enum + universal no-freeze principle; assertions strengthened, lie-detector stage-span check retained; Architect spec-check confirmed intended.
- **Dev (implementation) — lookahead worker test retargeted to carve-out (ii)** → ✓ ACCEPTED by Reviewer: preserves the test's central-constraint intent against a still-aborting failure mode; the carve-out is exactly the path Amendment A retains; no coverage lost.
- **Dev (implementation) — carve-out (i) implemented but not RED-covered** → ✓ ACCEPTED by Reviewer: spec-mandated; the absent test is a deferred non-blocking follow-up, not a deviation from the contract.

No undocumented deviations found.

**Data flow traced:** curator LLM verdict (`claude -p`, internal) → `_one_attempt` → `_parse_curation_verdict` (strict `json.loads`) → on failure: bounded retry → Layer-2 `_degrade_region` (deterministic `assemble_region` manifest, `curated=False`, `uncurated_regions`, ERROR log, routed span) → `RegionCuration` → attach/commit. Safe: no user input on this path; failure terminates in a bounded loud degrade, never an unbounded freeze or a silent stamped-curated lie.

**Pattern observed:** loud graceful degradation with a per-region isolation boundary + retained hard-fail carve-outs — `materializer.py::_stage_curate`/`_degrade_region`. Good pattern; matches ADR-006 + No-Silent-Fallbacks.

**Error handling:** every failure path is bounded and observable — retry-exhaustion/deadline → `dungeon.curate.degraded` span + ERROR log (`materializer.py:_degrade_region`); per-attempt → `dungeon.curate.parse_failed` span; carve-outs → loud `CurationError` with stage-span `curated=False`+reason.

**Handoff:** To SM for finish-story.

No upstream findings at this time.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### SM handoff → Architect (Houlihan), 2026-05-18 — pre-RED contract decision (user-chosen Option B)

**Your job, and only your job, this step:** make and RECORD the ADR-106 contract decision that gates this story. The user explicitly chose the "Architect-first, then straight tdd" path (Option B), matching the proven 50-24 precedent where the Architect resolution was a first-class recorded artifact *before* RED/GREEN ran.

**Decide and record:** for a truncated/unterminated curate-stage JSON response (deterministic failure: strict `json.loads` at `materializer.py` `_parse_curation_verdict` → `CurationError` → unhandled → frozen turn), what is the policy — **JSON repair** vs **retry-with-continuation** vs **degrade-to-uncurated-room** (or a defined combination, e.g. bounded-retry-then-degrade)? Record it as an **ADR-106 amendment** (preferred — `docs/adr/`) **or** a design note the implementation references. That recorded decision IS gating **AC-1**; the TEA RED tests and Dev GREEN must implement exactly the recorded policy, no improvisation.

**Constraints to honor in the decision:** No-Silent-Fallbacks (degrade must be loud — OTEL span + uncurated marker, never a swallowed except); the OTEL lie-detector mandate (CLAUDE.md lists dungeon subsystem decisions as must-emit); bounded + non-looping if retry is in the policy (AC-4); `claude -p` curate is the producer (per server CLAUDE.md, curate is still a `claude -p` job, not the SDK path). Read the pingpong Root-cause and Honest-caveat bullets in full first. Do NOT write implementation code — you produce the recorded contract, then hand to TEA for RED.

**Where this pre-step ENDS:** once the ADR-106 decision is recorded and this session's Design Deviations section is updated with the chosen policy + the doc reference, advance the workflow to RED (TEA / Radar). Do not run RED yourself.

**Branch:** `feat/50-26-harden-curate-truncated-json` (already cut off `develop` in sidequest-server). Story is `in_progress`. No Jira (personal project). Do not stash; do not test on a prior commit; no fixture may point at a live world/pack slug.

### Architect (Houlihan) → SM (Pierce), 2026-05-18 — pre-RED contract DONE; handing back to close setup gate

**Contract deliverable COMPLETE (AC-1 satisfied).** Recorded in two places: (1) normative spec — `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → **Amendment A — Curate-stage robustness contract (story 50-26)**; (2) the chosen policy + doc pointer is in this session's **## Design Deviations → ### Architect (pre-RED contract decision)**. Policy = layered bounded: keep `max_tokens=16384` (Layer 0, already on develop via b846544/PR#317) + 1-retry whole-call (Layer 1, ADR-098-compatible, NOT JSON repair) + wall-clock cap → **loud** degrade-to-uncurated stamped `curated=false` (Layer 2, ADR-006 graceful degradation). `CurationError` retained for genuinely-unrecoverable + per-region isolation. Spans `dungeon.curate.parse_failed`/`degraded`. Forensic note: the playtest's truncation sub-case is *already mitigated on develop* (b846544 landed 2026-05-17 19:22, after the ~16:51–17:00 freeze) — 50-26's real contribution is the bounded-latency + loud-degrade contract for the *residual* unparseable paths, not the truncation bump itself.

**TWO setup-mechanics defects found and one corrected — SM/process please note:**
1. **Session written to the wrong directory.** `sm-setup` created the session at `sidequest-server/.session/50-26-session.md`, but the handoff CLI and the archive convention (sibling `50-24` archived at orchestrator `sprint/archive/50-24-session.md`; story repos=sidequest-server identically) require the orchestrator path `.session/50-26-session.md`. **I relocated it** (`mv`, mechanical, content unchanged — the contract decision moved with it). Process fix: `sm-setup` MODE=setup must write to the orchestrator `.session/`, not the target repo's `.session/`, for repo-scoped stories. The SM's post-setup `ls` verification also looked at the server path and so did not catch this — verification should check the orchestrator `.session/`.
2. **`setup→red` gate blocked: no `## Sm Assessment`.** `pf handoff complete-phase 50-26 tdd setup red sm_setup_exit` fails with `No assessment found in session file. ... Add a '## Sm Assessment' heading`. That section is the SM's artifact for the `sm_setup_exit` gate; per agent-lane discipline the Architect does not write the Scrum Master's assessment. The Option-B insertion (Architect pre-step before tdd-setup-exit) means the SM relayed to Architect *before* completing its own setup-exit gate — that gate is still owed.

**Action for SM (Pierce):** the contract pre-step is done and recorded; nothing architectural remains. Please (a) note the session-location process defect above; (b) write the `## Sm Assessment` and run the setup-exit (`pf handoff complete-phase 50-26 tdd setup red sm_setup_exit` → `pf handoff marker tea`), routing to **Radar (TEA)** for RED against ADR-106 Amendment A. TEA's RED targets are enumerated at the end of the Design Deviations Architect entry.

### Dev (implementation) — 2026-05-18, C. E. Winchester III

- **Improvement** (non-blocking): The ADR-106 Amendment A document and `sprint/epic-50.yaml` are modified in the **orchestrator** repo (currently on `main`), NOT on the sidequest-server feature branch. Amendment A is the normative spec the shipped code references by name; it MUST travel with the story to develop on merge. Affects `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` + `sprint/epic-50.yaml` (the orchestrator-side story artifacts need committing into the story's git flow by SM/finish — the server code branch alone does not carry the spec). *Found by Dev during implementation.*
- **Question** (non-blocking): RED covers retained carve-out (ii) (`test_missing_cr_*`) but not carve-out (i) (assembled manifest itself invalid). Implemented per Amendment A regardless. Affects `tests/dungeon/test_materializer.py` (a future test injecting an invalid assembled manifest would lock carve-out (i)); flagged for TEA-verify / Reviewer, not blocking. *Found by Dev during implementation.*

### TEA (verify) — 2026-05-18, Radar O'Reilly

- **Improvement** (non-blocking): `_otel_in_memory()` is duplicated verbatim in `tests/dungeon/test_materializer.py:45` and `tests/dungeon/test_lookahead_worker.py:67` — **pre-existing**, not introduced by 50-26. Affects both files (extract to `tests/dungeon/conftest.py` as a shared helper). Deliberately NOT bundled into 50-26 (scope discipline — touches shared dungeon test infra for a curate-robustness story); recommend a standalone test-hygiene cleanup. *Found by TEA during verify (simplify-reuse, confidence high).*
- **Improvement** (non-blocking): big_bad CR→Edge resolution is mirrored between `materializer.py::_creatures_from_manifest` (Layer-2 / carve-out i) and the `_stage_curate` verdict loop (Layer-1) — intentional per the in-code comment; the two sites carry different carve-out error semantics. Affects `sidequest/dungeon/materializer.py` (a `_resolve_big_bad_cr` extraction would DRY ~14 lines). Deferred — entangling the carve-out error paths mid-pipeline on a p1 fix is unjustified risk; recommend a follow-up refactor with its own tests. *Found by TEA during verify (simplify-reuse, confidence medium).*

### Reviewer (code review) — 2026-05-18, S. Potter

- **Question** (non-blocking): the no-freeze guarantee is *contingent* on `complete_with_tools` yielding at an `await` so `asyncio.timeout` can cancel it; a future synchronous/blocking curate backend, or a pathologically large verdict making `_parse_curation_verdict`'s `json.loads` an uninterruptible sync block, would defeat the wall-clock cap and re-introduce the freeze. Affects `sidequest/dungeon/materializer.py::_stage_curate` (not a defect in this diff — the ADR-098 SDK one-shot is awaitable and the contractual verdict is ≤~16 KB; flagged so the Architect/future maintainers keep curate backends awaitable and consider a size guard if verdicts ever grow). *Found by Reviewer during code review (Devil's Advocate).*
- **Conflict** (blocking-at-finish, NOT blocking-this-PR): ADR-106 Amendment A — the normative spec the shipped code references *by name* (AC-1) — and `sprint/epic-50.yaml` are uncommitted in the **orchestrator** repo on `main`, outside the sidequest-server feature branch. Affects `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` + `sprint/epic-50.yaml` (SM/finish MUST land these into the story's git flow; if the code merges to develop and the amendment never lands, AC-1 "a reviewer can point at the policy doc" breaks post-merge). Re-raising Dev's + Architect's escalation with reviewer weight — this is the single highest post-merge risk. *Found by Reviewer during code review.*
- **Conflict / process-defect** (non-blocking; retro item): the **Reviewer agent definition's `<exit>` hardcodes `complete-phase {WORKFLOW} review finish approval`**, but the live `tdd` workflow is `setup→red→green→spec-check→verify→review→spec-reconcile→finish` (`pf workflow show tdd`). Following the hardcode, I ran `complete-phase 50-26 tdd review finish approval`, which **skipped the Architect `spec-reconcile` phase** (the definitive deviation-manifest audit). `resolve-gate review` had correctly returned `next_phase: spec-reconcile / next_agent: architect` — the workflow-routing principle ("never hardcode workflow→agent; resolve-gate is authoritative") was violated by the agent-def itself. **Recovery applied:** corrected the Phase line back to `spec-reconcile` and relayed to the Architect (not SM) so the `### Architect (reconcile)` manifest is produced before finish; the `spec-reconcile` gate is `status: ready` and `spec_reconcile`-gated, so no work is lost — only re-sequenced. Affects `pennyfarthing-dist/agents/reviewer.md` `<exit>` (APPROVED branch must be `complete-phase review spec-reconcile approval` → handoff architect, not `review finish`). *Found by Reviewer during exit (workflow-vs-agent-def drift).*

## Design Deviations

The Architect pre-step (contract decision under ADR-106, precursor to RED) is required before implementation begins. This design note will be updated with the recorded policy choice.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Architect (pre-RED contract decision) — 2026-05-18, M. Houlihan

**Status: RECORDED. AC-1 satisfied. Pre-step COMPLETE — workflow advances to RED (TEA / Radar).**

**Recorded contract:** `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → **Amendment A — Curate-stage robustness contract (story 50-26)**. That amendment is the normative spec; TEA writes RED against it, Dev makes it GREEN, no improvisation beyond it.

**Policy chosen (layered, bounded — NOT repair-vs-retry-vs-degrade as alternatives):**
- **Layer 0 (retained):** keep `max_tokens=16384` (already on develop via `b846544`/PR #317 — landed 2026-05-17 19:22, *after* the recorded freeze window, so the playtest's truncation sub-case is already mitigated on develop; this is design context, not the contract).
- **Layer 1:** bounded whole-call retry — **exactly 1 retry (2 attempts total)**, each an independent one-shot (ADR-098-compatible; NO `--resume`, NO mid-gen tools, NO continuation). **NOT JSON repair** — never invent the truncated tail (silent CR→Edge corruption risk).
- **Layer 1 deadline:** explicit wall-clock cap on the whole curate stage (**recommended ≤ 25 s**); deadline OR retry-exhaustion → Layer 2. This cap is the load-bearing no-freeze guarantee.
- **Layer 2:** loud degrade-to-uncurated — ship the deterministic pre-curation `assemble_region` manifest (valid+complete per ADR-106 clause 9) stamped `curated=false`, visible `uncurated` region marker, ERROR log, routed `dungeon.curate.degraded` span. Transaction completes; turn proceeds.
- **Forbidden (retained):** raw manifest stamped `curated=true` (the silent fallback the prior architect correctly rejected). Layer 2 stamps `curated=false` — the inverse.
- **`CurationError` retained**, reserved for: (i) the assembled manifest itself invalid; (ii) post-parse structural violations that would corrupt mechanics (e.g. row missing `cr`). Degradation is **per-region** — one bad region degrades loudly, never aborts the whole expansion.
- **Spans (clause 12):** `dungeon.curate.parse_failed` (per attempt; `region_id`, `failure_kind`∈{truncated,malformed,llm_error,deadline}, `attempt`) + `dungeon.curate.degraded` (Layer 2 fired; `region_id`, `failure_kind`, `attempts`, `elapsed_ms`).

**Scope guard honored:** whether the live R3 9-min gap was *this* exact `CurationError` is OQ-1's clock-binding verification concern — not adjudicated here; the contract makes the table-freeze impossible regardless of which unparseable path fires.

**Next:** TEA (Radar) — RED against ADR-106 Amendment A. Suggested first failing tests: feed `_stage_curate`/`_parse_curation_verdict` the pingpong failure shapes ("Unterminated string ... line 452 col 17"; "Expecting value line 429 col 25"; the `{exp001.r0:{race:undead,...wandering_table:[{name:Skeleton...}` truncated head); assert (a) no escaped `CurationError`, (b) Layer-2 region ships `curated=false` + `uncurated` marker, (c) `dungeon.curate.degraded` span fires, (d) attempts capped at 2, (e) exercised through the real `materialize` chain (AC-5 wiring), (f) per-region isolation (one bad region, siblings stay curated).

### TEA (test design) — 2026-05-18, Radar O'Reilly

**Deviation: a pre-existing test was rewritten because ADR-106 Amendment A supersedes its contract.**

- **Spec source:** `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → Amendment A. Quoted: *"`CurationError` is retained, not deleted. It is reserved for genuinely unrecoverable cases: (i) the assembled manifest itself structurally invalid …; (ii) post-parse structural violations where degrading would corrupt mechanics …"* and span taxonomy *"`failure_kind` ∈ {`truncated`, `malformed`, `llm_error`, `deadline`}"*.
- **Old contract (superseded):** `tests/dungeon/test_materializer.py::TestStageCurate::test_curation_subprocess_failure_raises_and_records_curated_false` asserted an `LlmClientError` curate failure **raises `CurationError`** and aborts the materialization.
- **Why it changed:** `llm_error` is an enumerated *degrade* `failure_kind` and is NEITHER retained carve-out (i) nor (ii). A raised/aborted turn on `llm_error` is exactly the frozen-turn failure mode Amendment A exists to eliminate (the no-freeze guarantee is universal across `failure_kind`). Leaving the old test green would make GREEN impossible (Dev cannot both raise and degrade on `llm_error`).
- **Implementation (test):** rewritten as `test_curation_llm_failure_degrades_loudly_not_raises_amendment_a` — asserts Layer-2 loud degrade (`curated=False`, `uncurated_regions` marker, `dungeon.curate.degraded` span `failure_kind="llm_error"`), **retaining** the original lie-detector assertion that the `dungeon.materialize.curate` stage span still surfaces `curated=False` to the GM panel. No assertion was weakened; the raise→degrade flip is the contract change itself.
- **Forward impact:** none on sibling stories. Dev GREEN must implement `llm_error` as a degrade path (retry then Layer-2), not a raise. Architect spec-check: confirm this supersession is intended (it is the direct consequence of the Amendment A `failure_kind` enum + universal no-freeze principle); if the Architect intends `llm_error` to still raise, the amendment's `failure_kind` enum must drop `llm_error` and this test reverts — flag at spec-check.
- **Test-pinned API note (not a deviation, a forward contract):** RED pins `RegionCuration.uncurated_regions: frozenset[str]`, span names `dungeon.curate.{parse_failed,degraded}` registered in `SPAN_ROUTES`, and an injectable `materializer.CURATE_DEADLINE_S`. These realize the amendment's mandated marker/spans/bounded-cap; Architect/Dev may rename at spec-check but the observable behaviour is fixed by the amendment.

### Dev (implementation) — 2026-05-18, C. E. Winchester III

- **Second superseded test retargeted: the look-ahead worker abort test**
  - Spec source: `docs/adr/106-...md` Amendment A; `tests/dungeon/test_lookahead_worker.py::test_worker_failure_loud_on_span_and_does_not_abort_transition`
  - Spec text: *"`CurationError` is retained, not deleted. It is reserved for genuinely unrecoverable cases: (i) … (ii) post-parse structural violations … (e.g. a curated row missing `cr`)."* — i.e. a *generic* curate failure (`LlmClientError`/unparseable) no longer raises; it Layer-2-degrades.
  - Implementation: the test forced the failure with `_failing_sdk_client()` (LlmClientError) and asserted (a) no expansion committed + (b) a loud `frontier.lookahead` error span. Post-Amendment-A, `LlmClientError` degrades and the expansion commits uncurated, so both assertions are stale. Retargeted the test to `_missing_cr_sdk_client()` — the RETAINED carve-out (ii), which *still* hard-raises — preserving the test's exact central-constraint intent (a prefetch failure must not re-raise synchronously / must not abort the party's region crossing) against a failure mode that genuinely still aborts. No assertion weakened; only the failure-injection client + docstring changed.
  - Rationale: same supersession class TEA already logged for the `llm_error` raise-test — discovered in the GREEN regression envelope, not anticipated by RED. Using the carve-out keeps a valuable regression guard for the still-aborting path rather than deleting coverage.
  - Severity: minor (test-only; the implementation is correct per Amendment A)
  - Forward impact: none on sibling stories. Architect spec-check: same confirmation as the TEA note — if `llm_error` is intended to still raise, both this and the TEA-rewritten test revert and the amendment's `failure_kind` enum must drop `llm_error`.
- **Retained carve-out (i) implemented per spec but not directly RED-covered**
  - Spec source: `docs/adr/106-...md` Amendment A
  - Spec text: *"reserved for genuinely unrecoverable cases: (i) the assembled manifest itself structurally invalid (a real upstream bug — fail loud, never degrade a corrupt input into content)"*
  - Implementation: `_creatures_from_manifest` raises `CurationError` when a degrade-sourced manifest row has no `cr` or a big_bad's `cr_band` is absent from `affinities.cr_bands`. RED covered only carve-out (ii) (`test_missing_cr_*`), not (i).
  - Rationale: Amendment A explicitly mandates carve-out (i); omitting it would silently degrade a corrupt assembled manifest (the exact No-Silent-Fallbacks trap). Implemented as spec requires even though no RED test forces it (the real cookbook never produces an invalid manifest in-test).
  - Severity: minor
  - Forward impact: TEA verify / Reviewer — consider a follow-up test that injects an invalid assembled manifest to lock carve-out (i); not blocking (the path is spec-mandated and code-reviewed, and over-degradation is the failure it prevents).

### Architect (reconcile) — 2026-05-18, M. Houlihan

**Definitive deviation manifest for story 50-26 (the boss's audit artifact). I authored ADR-106 Amendment A and ran spec-check; this reconcile is the final, self-contained record.**

**Existing entries reviewed — all VERIFIED ACCURATE (annotated, not altered):**
- *Architect (pre-RED contract decision):* the recorded gating contract = `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → "Amendment A — Curate-stage robustness contract (story 50-26)". Path exists; the layered policy (Layer 0 retain `max_tokens=16384` / Layer 1 one bounded whole-call retry, no JSON repair / Layer 1 wall-clock cap / Layer 2 loud degrade-to-uncurated `curated=false` + `uncurated_regions` + ERROR log + routed `dungeon.curate.degraded` / `CurationError` retained for carve-outs (i) assembled-manifest-invalid and (ii) parsed-row-missing-`cr` / per-region isolation) is implemented exactly (spec-check verified Aligned, clause-by-clause). 6 fields substantive. ✓ ACCURATE.
- *TEA (test design) — `llm_error` raise→degrade test rewrite:* spec source path valid; Amendment A text quoted accurately (*"`CurationError` is retained … reserved for genuinely unrecoverable cases: (i) … (ii) …"*; `failure_kind ∈ {truncated, malformed, llm_error, deadline}`); implementation (`test_curation_llm_failure_degrades_loudly_not_raises_amendment_a`) matches shipped code; forward impact accurate. 6 fields present. ✓ ACCURATE.
- *Dev (implementation) — lookahead test retarget + carve-out (i) note:* both entries 6-field complete; spec text accurately quoted; `test_worker_failure_loud_on_span_and_does_not_abort_transition` now drives `_missing_cr_sdk_client()` (carve-out ii, still hard-raises) preserving the central-constraint intent; carve-out (i) is spec-mandated and implemented in `_creatures_from_manifest`. ✓ ACCURATE.

**Missed deviation ADDED (spec-ambiguity resolution — Resolution C, definitively closed here):**
- **Layer-1 retry trigger is broader than the Amendment A prose literally stated.** Spec source: `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md` → Amendment A. Spec text (Layer 1): *"on an unparseable verdict, re-issue the one-shot curate call. Budget: exactly 1 retry (2 attempts total)."* — the prose names only *"unparseable verdict"*, but the same amendment's span taxonomy enumerates `failure_kind ∈ {truncated, malformed, llm_error, deadline}` and Layer 2's trigger is *"retry-exhaustion OR deadline"*. Implementation: `materializer.py:_stage_curate` retries on `(LlmClientError, CurationError)` — i.e. an `llm_error` (transient API failure) gets the same single bounded retry before Layer-2 degrade, not just an unparseable-JSON verdict. Rationale: this is the intended reading and is hereby **definitively confirmed by the contract author** — the universal no-freeze principle + the `llm_error` enum member make retrying-then-degrading an `llm_error` correct; raising on it would be the exact frozen/aborted turn the amendment eliminates. This **closes the open conditional** that both the TEA and Dev entries flagged ("if the Architect intends `llm_error` to still raise, the enum must drop it and the tests revert"): `llm_error` is intended to **degrade, not raise**; the tests stand; nothing reverts. Severity: trivial (interpretation, not a behaviour change — code already correct). Forward impact: a follow-up doc-only touch-up to Amendment A should tighten the Layer-1 prose to *"on any curate-attempt failure (unparseable verdict OR `LlmClientError`), re-issue …"* so prose and enum agree; non-blocking, no code/test change implied.

**AC deferral verification:** No ACs were deferred. AC-1 (Amendment A recorded) ✓, AC-2 (no frozen turn) ✓, AC-3 (loud+observable spans+marker) ✓, AC-4 (bounded non-looping retry + wall-clock) ✓, AC-5 (real-chain wiring) ✓ — all DONE and test-backed (story 14/14, regression/preflight 639/0). The carve-out (i) "no direct RED test" item is a deferred *follow-up test*, NOT a deferred AC (no AC requires a carve-out-(i) test; AC-2's no-freeze is fully covered). Nothing in the ac-completion accountability set is DEFERRED/DESCOPED.

**Process note (for the boss's complete audit — not a code/spec deviation):** the Reviewer's `<exit>` agent-def hardcodes `complete-phase review finish`, but the live `tdd` workflow is `review → spec-reconcile → finish`. The Reviewer initially transitioned review→finish (skipping this phase), detected the drift against `resolve-gate`'s authoritative `next_phase: spec-reconcile`, self-corrected the Phase line, and routed here. This spec-reconcile ran in full; no code/spec/test work was lost — only re-sequenced. The agent-def fix is logged as a non-blocking retro item in Delivery Findings (`pennyfarthing-dist/agents/reviewer.md` `<exit>` APPROVED branch). The story's substantive audit trail is intact and complete.

**Reconcile verdict:** every spec deviation is now explicitly accounted for and accurate; one ambiguity definitively resolved by the contract author; no undocumented deviations remain. Ready for SM finish.