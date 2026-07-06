---
story_id: "162-9"
jira_key: ""
epic: "162"
workflow: "trivial"
---
# Story 162-9: 162-1 follow-up: un-gate trim_to_caps from content evidence + zero-trim WARNING guard

## Story Details
- **ID:** 162-9
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Type:** chore
- **Points:** 2

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-07-06T17:25:04Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T15:52:23Z | 2026-07-06T15:54:40Z | 2m 17s |
| implement | 2026-07-06T15:54:40Z | 2026-07-06T16:59:08Z | 1h 4m |
| review | 2026-07-06T16:59:08Z | 2026-07-06T17:13:48Z | 14m 40s |
| implement | 2026-07-06T17:13:48Z | 2026-07-06T17:18:27Z | 4m 39s |
| review | 2026-07-06T17:18:27Z | 2026-07-06T17:25:04Z | 6m 37s |
| finish | 2026-07-06T17:25:04Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### Dev (implementation)
- **Improvement** (non-blocking): `tests/server/test_space_opera_swn_combat_e2e.py::test_firefight_resolves_on_hp_depletion_vs_content_ac` is flaky under xdist parallelism — fails ~1/3 full-suite runs ("opponent HP must reach 0", HpPool.current==1), passes consistently in isolation (`-n0`, verified 1 passed). Pre-existing race on shared Postgres fixtures, unrelated to this story (it touches combat/HP/dice, not the monster-manual pool). Affects `tests/server/test_space_opera_swn_combat_e2e.py` (+ likely `tests/server/dispatch/test_pregen_bestiary_90_1.py`) — wants per-test pool/fixture isolation. *Found by Dev during full-suite regression run.*

### Reviewer (code review)
- **Gap** (non-blocking): `test_websocket_session_handler_wires_monster_manual_inject` is a source-text wiring test — it `read_text()`s `websocket_session_handler.py` and asserts literal call-site strings, exactly the pattern CLAUDE.md's "No Source-Text Wiring Tests" forbids (passes on the literal being present even if wiring is broken; brittle to refactor). UNMODIFIED by 162-9 (out of scope), so not a blocker here. Affects `tests/server/dispatch/test_monster_manual_inject.py:~1072` (convert to a fixture-driven / OTEL-span behavior wiring test). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): a permanently authored-over-cap NPC pool (authored alone exceed `MAX_MANUAL_NPCS`) now emits neither a log nor an OTEL span in steady state — the pre-162-9 "dropped 0" warning is gone, correctly, but not replaced with a correctly-worded signal. Consistent with `reconcile_content`'s no-op-returns-None convention, so not a defect; noted in case the GM panel later wants visibility into a saturated authored roster. Affects `sidequest/game/monster_manual.py::trim_to_caps` (optional debug-level note or dedicated span). *Found by Reviewer during code review.*

### Reviewer (re-review, round 2)
- No new upstream findings. The round-1 blocking Medium is resolved; the two prior non-blocking Reviewer findings above (source-text wiring test; authored-over-cap steady-state visibility) still stand as future cleanup and were correctly left out of this trivial chore's scope. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### Dev (implementation)
- No deviations from spec. The story context YAML was title-only, so the exact scope (the 5 doc-correction locations + the precise "guard on actual trim count" framing of the zero-trim WARNING) was reconstructed from the authoritative source: the 162-1 session archive Delivery-Findings addendum (`sprint/archive/162-1-session.md`, PR #1110). All four buckets implemented exactly as the reviewer enumerated them.
- **Rework round 2 — conscious deferral of 2 Low reviewer recommendations.** Spec source: Reviewer Assessment "Non-blocking (deferred)". Reviewer marked these "recommended, not required for approval." (1) The resolvable-bestiary + over-cap combined-path test — deferred: requires constructing a real `Bestiary` stub; the no-double-save property it would cover is already proven by inspection (post-discard the pool is emptied) and confirmed by rule-checker #1/#13, so it is net-new coverage rather than a fix. (2) Changing the zero-trim caplog assertion from substring to `len(records)==0` — deferred: the reviewer verified the current substring assertion DOES fail against pre-fix code (sound today), and a hard `==0` risks flakiness if any unrelated WARNING enters the capture. Both logged here so they are visible for a future cleanup, not silently dropped. Severity: minor.

### Reviewer (audit)
- **"No deviations from spec" (Dev)** → ✓ ACCEPTED by Reviewer: Dev correctly sourced the exact scope from the 162-1 addendum, and the behavioral change + the 5 enumerated doc corrections match that spec precisely. Reconstructing scope from the parent's archived Delivery-Findings is the right move for a title-only follow-up.
- **UNDOCUMENTED (incomplete execution of bucket 4):** Spec bucket 4 is "correct the stale session-discard / 'bounded on reconcile' claims." The five *enumerated* locations were all fixed accurately, but the same class of stale claim survives at `sidequest/telemetry/spans/monster_manual.py:49-54` (the `CAP_ENFORCED` span comment) — a location the reviewer addendum did not itemize but which falls squarely within the bucket's stated intent, and which the diff itself edited 9 lines above. Not a design *deviation* so much as an incomplete sweep; captured as the blocking [MEDIUM] `[DOC]` finding. Severity: M. → **RESOLVED in round 2** (commit `9da83403`): the `CAP_ENFORCED` comment now reads "bounded unconditionally in ensure_loaded ... independent of reconcile"; comment-analyzer re-grep confirms no stale claim remains. ✓
- **Round-2 deferral of 2 Low reviewer recommendations (Dev)** → ✓ ACCEPTED by Reviewer: both were explicitly marked "recommended, not required for approval" in the round-1 assessment; deferring net-new coverage (resolvable-bestiary combined test) and a flakiness-risk assertion change (caplog substring→count) is sound, and both are logged for future cleanup rather than silently dropped. No re-review concern.

## Sm Assessment

**Routing:** New Work → trivial (phased) → implement phase → Dev (Naomi Nagata).

**What this story is:** A 2-pt follow-up to completed 162-1, scoped to `sidequest-server`. Three buckets of work:

1. **Un-gate `trim_to_caps` from content evidence** — the core fix. Over-cap pools that have *no bestiary* currently escape trimming because the trim path is gated on content evidence. Un-gate it so bestiary-less over-cap pools get trimmed too. Add a **zero-trim WARNING guard** so a trim pass that removes nothing is loud (per No-Silent-Fallbacks doctrine).
2. **Close coverage gaps** — tests for `npc_dropped_all_authored`, encounter-side trim, and `encounter_dropped` via `seed_manual`.
3. **5 doc corrections** — stale session-discard claims, class-docstring wording, conftest `session_fixture` comment.

**Why trivial workflow fits:** Chore, 2 pts, single repo, mostly targeted un-gating + guard + tests + doc text. No new subsystem, no ADR. Reference specs already identified (npc-generation-inventory seven-spawn-paths, ADR-059, ADR-121).

**Guardrails for Dev to honor:**
- The zero-trim guard must WARN loudly, not silently pass — this is the whole point of the OTEL/No-Silent-Fallback doctrine. Prefer a watcher/OTEL emit on the trim decision so the GM panel can confirm trimming engaged.
- Coverage gaps are real test debt — each new test must actually exercise the un-gated path, not restate what 162-1 already covered.
- Doc corrections are text-only; keep them scoped, don't refactor the code they describe.

**Merge gate:** Clear — no open PRs on server. Jira disabled for this sprint (jira_key empty), so no claim step.

## Branch Strategy
**Branch Strategy:** gitflow (feat/162-9-trim-caps-ungate-coverage)

## Dev Assessment

**Implementation Complete:** Yes

**Source of truth:** The 162-1 reviewer logged this exact follow-up in `sprint/archive/162-1-session.md` (PR #1110). Four buckets, all done:

**1. Un-gate `trim_to_caps` from content evidence (+ regression test)**
- `sidequest/server/dispatch/monster_manual_inject.py` — moved the `trim_to_caps()` call OUT of `ensure_loaded`'s `content_sha is not None` branch so it runs unconditionally. `reconcile_content` stays content-gated (it judges staleness against a roster it must read); trimming is a pure size-bound op that needs no bestiary. Fixes the bestiary-less over-cap pool never being bounded (repro: 220-NPC pool stayed 220). The `cap_enforced` (kind="trim") span still fires; still persists on trim.

**2. Zero-trim WARNING guard**
- `sidequest/game/monster_manual.py` `trim_to_caps` — guarded the "pool_trimmed — dropped N oldest generated NPCs" warning on `npcs_trimmed > 0`. An all-authored over-cap pool has nothing trimmable, so the old code re-logged "dropped 0" on every load (guarded on the over-cap condition, not the trim count). Now silent when nothing was dropped.

**3. Coverage gaps closed (4 new tests)**
- `tests/game/test_monster_manual_derive.py`: `test_add_npc_all_authored_at_cap_returns_drop_all_authored_event` (the untested 4th CapEvent kind), `test_trim_to_caps_bounds_encounters_oldest_first` (encounter-side trim), `test_trim_to_caps_all_authored_over_cap_is_silent_noop` (zero-trim guard behavior).
- `tests/server/dispatch/test_pregen.py`: `test_seed_manual_emits_cap_enforced_span_for_encounter_drop` (`encounter_dropped` driven through `seed_manual`).
- `tests/server/dispatch/test_monster_manual_inject.py`: `test_ensure_loaded_trims_over_cap_pool_without_bestiary` — the un-gate regression test (would fail without bucket 1; also the seam wiring test).

**4. Five doc corrections**
- `sidequest/game/monster_manual.py` — `MonsterManual` class docstring ("bounded on reconcile" → unconditional `ensure_loaded` step); `ContentDiscard` docstring ("content/seed mismatch" → content_sha only).
- `sidequest/telemetry/spans/monster_manual.py` — `pool_discarded` span comment ("(content_sha, session_seed) key ... or a new session" → content_sha only, session_seed attribution-only).
- `tests/game/test_monster_manual_derive.py` — module docstring ("either key changed ... or a new session" → content_sha-only discard).
- `tests/server/conftest.py` — `session_fixture` comment (`(None,"")` → stable-digest → now unresolvable → reconcile skipped).

**Files Changed:**
- `sidequest/game/monster_manual.py` — zero-trim guard + 2 docstrings
- `sidequest/server/dispatch/monster_manual_inject.py` — un-gate trim
- `sidequest/telemetry/spans/monster_manual.py` — span comment
- `tests/game/test_monster_manual_derive.py` — 3 tests + module docstring
- `tests/server/dispatch/test_pregen.py` — 1 test
- `tests/server/dispatch/test_monster_manual_inject.py` — 1 test
- `tests/server/conftest.py` — fixture comment

**Tests:** Targeted files 113/113 GREEN. Full suite 14655 passed / 341 skipped / 1 pre-existing xdist-flaky failure (unrelated SWN combat e2e — verified passes `-n0` in isolation; logged as a Delivery Finding).

**Branch:** feat/162-9-trim-caps-ungate-coverage (sidequest-server)

**Handoff:** To review phase (Reviewer — Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 113 pass, ruff/format/pyright clean, no smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (all low) | confirmed 0 blocking, 3 deferred (bundled recommendations) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (1 high, 1 medium) | confirmed 2 (both blocking the doc-correction deliverable) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 (17 rules / 26 instances / 0 violations) | N/A |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed blocking (Medium), 4 confirmed non-blocking/deferred (1 Low doc + 3 Low test), 0 dismissed

## Reviewer Assessment

**Verdict:** REJECTED (narrow — one doc-correction miss in the story's own deliverable)

The behavioral change is *correct and well-verified*. The reason for rejection is scoped entirely to the story's fourth bucket (doc corrections): this doc-fix story left a stale comment of the exact type it was chartered to remove, in a file it already edited, producing an internal contradiction shipped in the same PR.

### Severity Table

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] `[DOC]` | `SPAN_MONSTER_MANUAL_CAP_ENFORCED` comment still says a legacy over-cap pool is "bounded **on reconcile** (kind='trim')" and lists the call site as "ensure_loaded's **reconcile**". This directly contradicts the docstrings THIS STORY corrected (monster_manual.py:~221 now says trim is "an unconditional ensure_loaded step, not part of reconcile_content (which never trims)"). Post-un-gate the trim span fires even when reconcile is *skipped* (content_sha None). Same "bounded on reconcile" phrasing the story removed elsewhere — 9 lines below the `pool_discarded` comment the story DID fix in this same file. | `sidequest/telemetry/spans/monster_manual.py:49-50, 54` | Reword to "a legacy over-cap pool bounded unconditionally in ensure_loaded (kind='trim', ...)" and change the call-site list from "ensure_loaded's reconcile" to "ensure_loaded's unconditional trim step". |
| [LOW] `[DOC]` (bundle in same touch) | Within the reconcile-content explainer block, the trim mention is framed inside the reconcile paragraph ("...bounded via trim_to_caps below"). "below" is literally still true, but the framing predates the un-gate and reads as if trim is scoped to a resolved-content path — the new comment at 258-266 exists specifically to correct this framing. | `sidequest/server/dispatch/monster_manual_inject.py:218` | Split the trim mention out or add "— unconditionally, independent of this reconcile step (see the comment at the trim call)". |

### Non-blocking (deferred — recommended, not required for approval)

- [LOW] `[TEST]` The zero-trim guard test asserts absence via a `"pool_trimmed" in message` substring; a harmless log rename could make it pass vacuously. Optional hardening: assert `len(caplog.records) == 0` at WARNING. (test-analyzer verified it DOES fail against pre-fix code today, so it is sound now.) `tests/game/test_monster_manual_derive.py:~430`
- [LOW] `[TEST]` No test exercises the *resolvable*-bestiary + over-cap combination (reconcile runs AND the now-unconditional trim runs in one `ensure_loaded`) — the new test only covers the content_sha-None branch. `tests/server/dispatch/test_monster_manual_inject.py`
- [LOW] `[TEST]` The encounter-drop seed test asserts encounter spans fired but not the *absence* of NPC-side spans its docstring claims. `tests/server/dispatch/test_pregen.py:~354`

### Subagent Dispatch Tags

- `[EDGE]` — edge-hunter DISABLED via settings; boundary analysis performed manually (see Devil's Advocate). No edge defects found.
- `[SILENT]` — silent-failure-hunter DISABLED via settings; verified manually + by rule-checker #1/#14: moving trim out of the `else` introduces no silent-skip (it REMOVES a prior silent grandfathering); no swallowed errors added.
- `[TEST]` — test-analyzer: 3 LOW deferred findings (above). Revert-experiment confirmed both regression tests genuinely fail against pre-fix code (non-vacuous).
- `[DOC]` — comment-analyzer: 1 MEDIUM (blocking) + 1 LOW confirmed (above); all 6 authored doc corrections verified accurate.
- `[TYPE]` — type-design DISABLED via settings; signatures unchanged (`trim_to_caps(self) -> PoolTrim | None`, `ensure_loaded(sd: _SessionData) -> MonsterManual | None`), pyright clean. No type defects.
- `[SEC]` — security DISABLED via settings; diff has zero auth/input/deserialization/path surface (pure in-memory pool bookkeeping + comments + tests). No security surface.
- `[SIMPLE]` — simplifier DISABLED via settings; change is minimal (un-nest a block + guard one warning). No over-engineering.
- `[RULE]` — rule-checker: CLEAN, 17 rules / 26 instances / 0 violations. Confirmed correct logging level/lazy-interp, no double-save, sanctioned OTEL-span wiring test.

### Rule Compliance (enumerated)

- **No Silent Fallbacks (SOUL/CLAUDE.md):** The un-gate is itself a No-Silent-Fallback FIX — a bestiary-less over-cap pool was silently grandfathered; it now trims loudly. The zero-trim guard removes a *misleading* log ("dropped 0"), and authored-over-cap is the documented authored-preservation contract, not a hidden fallback. ✓ (rule-checker #14). Minor observation (not a violation): a permanently-authored-over-cap pool now emits neither log nor span in steady state — consistent with `reconcile_content`'s own no-op-returns-None convention; noted for possible future GM-panel visibility, NOT required here.
- **No Stubbing:** No placeholder/skeleton code. ✓
- **Every test suite needs a WIRING test / no source-text wiring tests:** `test_ensure_loaded_trims_over_cap_pool_without_bestiary` is the sanctioned fixture-driven + OTEL-span-assertion wiring test for the moved trim call. No `read_text()`/regex-on-source in any new test. ✓ (The pre-existing `test_websocket_session_handler_wires_monster_manual_inject` source-grep test violates this rule but is UNMODIFIED by this story — out of scope, logged as a Delivery Finding.)
- **OTEL Observability Principle:** `cap_enforced` (kind="trim") still fires whenever `trim_to_caps()` returns a PoolTrim, regardless of the log guard; `pool_discarded` still fires only on a real discard, and the new test asserts its absence when reconcile is skipped. ✓
- **Logging correctness (python.md #4):** WARNING level correct for the anomalous legacy-pool event; %s/%d lazy interpolation; no sensitive data. ✓
- **Mutable defaults / type annotations / resource leaks / async / deserialization / input validation (python.md #2,3,7,8,9,11):** N/A or clean — no such surface in the diff. ✓

### Observations (≥5)

1. [VERIFIED] Un-gate is correct — trim moved to function-body scope in `ensure_loaded`; uses only `sd.*`/`trim.*`, never `session_seed` (which stays in the `else`), so no out-of-scope reference. Evidence: `monster_manual_inject.py:258-280`, pyright clean.
2. [VERIFIED] No double-save regression — when `reconcile_content` returns a discard it sets `self.npcs=[]/self.encounters=[]` (`monster_manual.py:528-529`), so the now-unconditional `trim_to_caps()` sees an empty pool and returns None → no second `save()`. Confirmed independently by rule-checker #1/#13.
3. [VERIFIED] Zero-trim guard is behaviorally proven — `if npcs_trimmed:` suppresses only the "dropped 0" log; return value and span emission are unchanged. test-analyzer's revert experiment confirms the new caplog test fails against pre-fix code. Evidence: `monster_manual.py:564-579`.
4. [VERIFIED] Regression test bites — reverting only the production hunks makes `test_ensure_loaded_trims_over_cap_pool_without_bestiary` fail `assert 220 == 200`. Genuine, non-vacuous. Evidence: test-analyzer revert experiment.
5. [MEDIUM] `[DOC]` Stale `CAP_ENFORCED` span comment (blocking — see severity table) at `telemetry/spans/monster_manual.py:49-54`.
6. [VERIFIED] All 6 authored doc corrections are accurate to the code (comment-analyzer cross-checked each against `reconcile_content`, `_content_sha_for`, and the un-gated trim). Evidence: comment-analyzer confirmations.

### Devil's Advocate

Argue the code is broken. **Performance:** trim now runs on EVERY `ensure_loaded` — but it's a single O(n) pass over a ≤200-entry list; negligible, and it early-returns None under cap. **A malicious/confused pack author** ships a world with 300 authored NPCs: the pool stays at 300 (authored never dropped), trim returns None, and — post-fix — nothing is logged. Is that a silent failure? No: authored-preservation is the *documented contract* (a named cast member is never crowded out), and it mirrors `reconcile_content`'s own no-op-returns-None convention. The rule-checker flagged this as an observation, not a violation; I concur — it's a steady-state design property, not a hidden error, though a future story could add a debug-level "authored roster exceeds cap" note for GM-panel visibility. **Ordering:** does trimming before seeding matter? Seeding's `add_npc` enforces the cap itself, so order is safe. **Double reconcile+trim:** covered above — empty pool after discard. **The stressed filesystem:** `manual.save()` on trim can raise — but that's pre-existing behavior identical to the discard-save path and out of scope. **What a confused *reader* misunderstands:** THIS is where the real defect lives — a developer reading `telemetry/spans/monster_manual.py:49` learns trim happens "on reconcile," then reads `monster_manual.py:221` and learns it's "not part of reconcile_content." Two files in the same PR teach opposite things about the same operation. For a story whose entire fourth bucket is "make these docs accurate," that contradiction is the deliverable failing its own test. That is the confirmed blocking finding; everything else is verified-good or Low.

**Handoff:** Back to Dev (Naomi Nagata) — green/rework. Required: fix the `CAP_ENFORCED` span comment (blocking Medium). Recommended in the same touch: reframe `monster_manual_inject.py:218` (Low) and optionally harden the three Low test observations. The behavioral code and all 5 new tests are approved as-is — do NOT change them beyond the optional test hardening.

## Dev Assessment — Rework (round 2)

**Rework Complete:** Yes — addressed the blocking Medium + bundled Low, per the Reviewer's scoped guidance.

**Fixed:**
- **[BLOCKING Medium `[DOC]`]** `sidequest/telemetry/spans/monster_manual.py` — the `CAP_ENFORCED` span comment now reads "a legacy over-cap pool bounded **unconditionally in `ensure_loaded`** ... the trim step runs independently of reconcile (story 162-9), so this span can fire even when content_sha is None and reconcile was skipped", and the call-site list changed from "ensure_loaded's reconcile" → "ensure_loaded's unconditional trim step". Now consistent with the `MonsterManual` class docstring and `ContentDiscard` docstring. The in-PR contradiction is resolved.
- **[Low `[DOC]`]** `sidequest/server/dispatch/monster_manual_inject.py:~217` — the trim mention in the reconcile explainer paragraph now says bounded "**UNCONDITIONALLY and independent of this reconcile step** (see the comment at the trim call)".
- **[Low `[TEST]`]** `tests/server/dispatch/test_pregen.py` — `test_seed_manual_emits_cap_enforced_span_for_encounter_drop` now asserts no `npc_`-kind cap span fires, making its "only encounter-side spans" docstring claim a real assertion.

**Deferred (reviewer-sanctioned Low, non-blocking — logged as Design Deviation round 2):** the resolvable-bestiary+over-cap combined-path test and the zero-trim caplog substring→count change.

**Behavioral code + the 5 new tests:** untouched, exactly as the Reviewer instructed ("do NOT change them beyond the optional test hardening").

**Tests:** targeted suites 113/113 GREEN (incl. the newly-hardened encounter-drop test). ruff check + format clean on all changed files.

**Branch:** feat/162-9-trim-caps-ungate-coverage (pushed — commit `9da83403`).

**Handoff:** Back to review phase (Reviewer — Chrisjen Avasarala).

## Subagent Results

_(Round 2 — re-review of the narrow rework diff: 2 comment edits + 1 test-assertion.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 113 pass, ruff/format clean, no smells; hardened test passes) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | 0 (mutation-verified the new npc-absence assertion is non-vacuous: forced MAX_MANUAL_NPCS=0 → test fails) | N/A |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 (blocking comment resolved; grepped both files — no stale "on reconcile" claims remain, no new inaccuracy) | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 (17 rules / 0 violations; refactor behaviorally identical, no fix-introduced regression) | N/A |

**All received:** Yes (4 enabled returned CLEAN, 5 disabled pre-filled)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred — the round-1 blocking Medium is resolved and no new findings surfaced.

## Reviewer Assessment

**Verdict:** APPROVED (round 2)

The round-1 blocking [MEDIUM] `[DOC]` finding is fully resolved: the `CAP_ENFORCED` span comment now reads "bounded unconditionally in `ensure_loaded` ... the trim step runs independently of reconcile (story 162-9), so this span can fire even when content_sha is None and reconcile was skipped", with the call-site list corrected to "ensure_loaded's unconditional trim step". comment-analyzer re-grepped both files (plus `monster_manual.py`) and confirms zero remaining "on reconcile" claims and no new inaccuracy — the in-PR contradiction is gone. The bundled Low reframe (`monster_manual_inject.py:214-222`) and the Low test hardening (npc-span-absence assertion) both landed cleanly. The two consciously-deferred Low items (resolvable-bestiary combined test; caplog substring→count) are reviewer-sanctioned non-blocking and logged as Design Deviations.

**Data flow traced:** a bestiary-less over-cap Manual pool → `ensure_loaded` (content_sha None → reconcile skipped) → unconditional `trim_to_caps()` → bounded to cap + `cap_enforced`(kind="trim") span + `manual.save()`. Safe: verified in round 1 (revert experiment) and unchanged in round 2.
**Pattern observed:** documentation now internally consistent across all three files describing the trim/reconcile relationship (`monster_manual.py` class + `trim_to_caps` docstrings, `telemetry/spans/monster_manual.py` CAP_ENFORCED comment, `monster_manual_inject.py` reconcile explainer + trim-call comment).
**Error handling:** unchanged; no runtime surface touched in the rework (comments + 1 test assertion).

### Subagent Dispatch Tags (round 2)

- `[EDGE]` — DISABLED via settings; rework has no new control-flow surface (comments + test assertion). No edge risk.
- `[SILENT]` — DISABLED via settings; no exception/fallback code touched. Rule-checker #1 clean.
- `[TEST]` — test-analyzer CLEAN; mutation-verified the new assertion catches a real NPC-cap regression; refactor behaviorally identical.
- `[DOC]` — comment-analyzer CLEAN; blocking comment resolved, no stale/new inaccuracy anywhere in the two files.
- `[TYPE]` — DISABLED via settings; no signatures changed. N/A.
- `[SEC]` — DISABLED via settings; zero security surface (comments + test). N/A.
- `[SIMPLE]` — DISABLED via settings; rework is minimal and additive. No over-engineering.
- `[RULE]` — rule-checker CLEAN; 17 rules / 0 violations; #6 (test quality) and #13 (fix-introduced regression) both clean.

### Observations (round 2)

1. [VERIFIED] Blocking finding resolved — `telemetry/spans/monster_manual.py:46-56` no longer says "bounded on reconcile"; now "bounded unconditionally in ensure_loaded". Consistent with `monster_manual.py:220-223`. Evidence: round-2 diff + comment-analyzer grep of both files (clean).
2. [VERIFIED] No new stale claim introduced — comment-analyzer grepped `"on reconcile"`/`"bounded via"`/`"trim_to_caps"` across all three files; every remaining hit is consistent with the corrected model.
3. [VERIFIED] New test assertion is non-vacuous — test-analyzer forced `MAX_MANUAL_NPCS=0` and the assertion FAILED as expected, then restored. It targets the stable `CapEvent.kind` taxonomy (the 3 npc_ kinds), and `seed_manual` structurally cannot emit a `trim` span, so no false-negative. Evidence: test-analyzer mutation test.
4. [VERIFIED] Refactor is behaviorally identical — `enc_spans` is now filtered from an intermediate `cap_spans` list with the same predicate; original non-empty + genre assertions preserved. Evidence: rule-checker + test-analyzer, both confirmed by run (113 pass).
5. [VERIFIED] Green everywhere — ruff check + format clean on all 3 touched files; 113/113 in the affected suites. Evidence: preflight.
6. [VERIFIED] Behavioral code + the 5 original tests untouched in the rework (round-2 diff is comments + 1 assertion only), so round-1's verified-good behavioral verdict stands. Evidence: round-2 diff stat (3 files, +16/-10, no logic).

### Devil's Advocate (round 2)

Could the rework be wrong? The only executable change is the added assertion `assert not [s for s in cap_spans if kind.startswith("npc_")]`. Could it pass vacuously (making the test weaker)? test-analyzer's mutation experiment answers no: force an NPC cap and it fails. Could it over-match and cause flakiness? The `npc_` prefix matches exactly the three NPC `CapEvent.kind` values and never `encounter_dropped`/`trim`; `otel_capture` is function-scoped so no cross-test span pollution; `seed_manual` never reaches `trim_to_caps`. Could the comment edits misstate behavior? Both were re-verified against the real `ensure_loaded` body — trim sits AFTER/outside the content_sha branch, so "unconditional, independent of reconcile" is literally the control flow. The remaining risk surface is nil: no production logic moved. Approve.

**Handoff:** To SM (Camina Drummer) for finish (PR + merge).