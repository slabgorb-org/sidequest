---
story_id: "158-2"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-2: IntentRouter routes literary/described attacks to combat, not only blunt 'attacks X with Y'

## Story Details
- **ID:** 158-2
- **Jira Key:** (none — Jira not enabled)
- **Epic:** 158 (Playtest sweep follow-ups)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repo:** sidequest-server
- **Branch:** feat/158-2-intentrouter-literary-attack-routing

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T02:00:57Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T01:21:08Z | - | - |
| red | 2026-06-23T01:21:08Z | 2026-06-23T01:34:28Z | 13m 20s |
| green | 2026-06-23T01:34:28Z | 2026-06-23T01:41:57Z | 7m 29s |
| review | 2026-06-23T01:41:57Z | 2026-06-23T01:51:18Z | 9m 21s |
| green | 2026-06-23T01:51:18Z | 2026-06-23T01:55:12Z | 3m 54s |
| review | 2026-06-23T01:55:12Z | 2026-06-23T02:00:57Z | 5m 45s |
| finish | 2026-06-23T02:00:57Z | - | - |

## Repro & Root Cause

### Repro (2026-06-22 beneath_sunden playtest, session 697cbc14, turns 5 vs 6)

**T5 (literary attack, NOT routed to combat):**
```
"…draws his short sword, splashes two quick steps through the black water, 
and drives the point hard at the crouched thing along the northeast wall…"
```
- NO confrontation dispatched
- OTEL: intent_router/mechanical/confrontation consulted but 0 encounter events, total_beats_fired=0
- Narrator free-narrated the fight

**T6 (blunt attack, ROUTED to combat):**
```
"Groucho attacks the Pale Thing with his short sword."
```
- ENCOUNTER_STARTED, opponent seated

### Root Cause

The router's combat-verb classification keys on plain attack phrasing. A narrated/literary action with the verb buried ("drives the point hard at…") falls under the confidence/verb gate and isn't dispatched. The diagnostic signal `confrontation_verb_unrouted` was downgraded to DEBUG in commit de4b6e50 (#950), so at INFO there is no trace of the miss — it silently doesn't fight.

### Player Impact

Squarely on narrative-first seats (CLAUDE.md audience: James/Alex describe actions in prose, not blunt verbs). This is a real player-experience failure for the primary audience.

## Acceptance Criteria (for TEA RED phase)

1. **Literary attack routing:** A literary/described attack against a present, live creature (verb buried in prose, e.g., "drives the point hard at the crouched thing") routes to a confrontation and dispatches (ENCOUNTER_STARTED / confrontation seated), same as blunt "attacks X with Y"

2. **No regression:** The blunt "attacks X with Y" form continues to route correctly

3. **OTEL visibility:** When a combat verb is seen but NOT routed, a loud OTEL signal is emitted at INFO (re-raise `confrontation_verb_unrouted` or an equivalent "combat verb seen but not routed" span) so the miss is observable in the GM panel
   - Per CLAUDE.md OTEL Observability Principle: every backend fix touching a subsystem must add/restore OTEL watcher events

4. **No false positives:** Non-combat described actions (movement, talking, examining) must NOT be mis-routed to combat (guard against over-widening)

## Technical Context

### Relevant Systems
- **ADR-113:** Intent Router — mechanical-engagement spine
- **ADR-123:** Mechanical-Engagement Pipeline — confidence-gated dispatch bank
- Combat is supposed to resolve pre-narrator in the IntentRouter + dispatch bank

### Known Implementation Hints (for Dev reference; not prescriptive)
- (a) Widen verb extraction to catch the attack verb inside a described action, and/or
- (b) Re-raise `confrontation_verb_unrouted` to INFO (or emit a loud OTEL span) so this is visible per the OTEL lie-detector principle

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The headline routing fix (a literary/described attack must actually START combat — AC1) is a Haiku LLM decision made in `IntentRouter.decompose`, steered by `CONFRONTATION_TRIGGER_CORE`. The pre-narrator-pass test harness STUBS the router (`_StubRouter`), so no RED unit can prove the routing changed — a stub-router "routing" test would pass today and after, i.e. vacuous. The real fix is prompt steering for described attacks, validated by replaying the T5/T6 beneath_sunden repro (and/or the router eval corpus), NOT by these units. Affects `sidequest/agents/narrator_guardrails.py` (`CONFRONTATION_TRIGGER_CORE` — needs literary/described-attack steering) and requires a playtest gate. *Found by TEA during test design.*
- **Improvement** (non-blocking): `_confrontation_verb_hits` (`sidequest/server/intent_router_pass.py:185`) matches raw `intent_verbs` with `\bverb\b` and does NOT stem, so inflected combat verbs ("hacks", "striking", "stabbed") are lexically invisible → the exact zero-telemetry hole the playtest hit on T5. Widen it to the shared suffix-stripped `tokenize()` (already used by the pack loader and `confrontation_intent_validator`) so described attacks become observable. Pinned by `test_described_attack_with_inflected_verb_is_detected`. *Found by TEA during test design.*
- **Question** (non-blocking): AC3 endorses INFO, but the `intent_router.confrontation_classified` span (emitted=0 + verb_hits) ALREADY carries the decline to the GM panel. Confirm whether re-raising the log DEBUG→INFO satisfies AC3, or whether a dedicated "combat verb seen but not routed" span is also wanted. The RED tests accept `>= INFO` to leave Dev latitude. Affects `intent_router_pass.py:885`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (blocking): TEA's blocking Gap is partly resolved — the headline AC1 routing fix DID land as a `CONFRONTATION_TRIGGER_CORE` clause that treats a described/literary attack against a present target as a strike (with the T5 "drives the point at the crouched thing" phrasing as a concrete example, and explicit handling of a leading preparation clause). BUT its effect on the live Haiku router is NOT unit-testable. Before the story is truly closed it must be validated by replaying the beneath_sunden T5 repro against the live router (a `/sq-playtest` descent, or the router eval corpus in `sidequest/corpus/router_corpus.py`). Reviewer/SM: the 61 green units do NOT prove the literary attack now routes. Affects `sidequest/agents/narrator_guardrails.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Resolved TEA's INFO-vs-span Question by re-raising the existing `confrontation_verb_unrouted` log to INFO and NOT adding a new span — the `intent_router.confrontation_classified` span (emitted=0 + verb_hits) already carries the structured signal to the GM panel, so a second span would be redundant (minimalist). *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): [SEC] The `confrontation_verb_unrouted` log now emits at INFO and includes `action[:120]` — raw player text (CWE-532 / python lang-review rule #4 "never log PII"). The rest of the codebase logs `action_len` (an integer), never raw text; raising this from DEBUG→INFO pushes raw player input into prod logs (`~/.sidequest/logs`). Affects `sidequest/server/intent_router_pass.py` (the `logger.info` block ~line 898 — drop `action_preview=%r`/`action[:120]`, keep `verb_hits`, or log `action_len`). *Found by Reviewer during code review.*
- **Gap** (blocking): The now-INFO unrouted-verb log fires during ACTIVE combat (verified empirically: an active unresolved encounter + "I strike the orc again" emits `confrontation_verb_unrouted` at INFO, because once seated the router uses beat_selections so `conf_types` is empty). That is expected suppression, not a miss — logging it loudly every combat turn dilutes the exact AC3 signal this story raised it to surface. Affects `sidequest/server/intent_router_pass.py` (gate the unrouted log on `snapshot.encounter is None or resolved`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): [DOC] The module-level docstring of `tests/server/test_intent_router_confrontation_classified.py:13` still says "a DEBUG log — Story 126-6 downgraded it" though the test now asserts INFO. Update it. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): [SILENT] An all-stopword authored `intent_verb` tokenizes to `frozenset()` and is silently skipped by the `if verb_tokens and ...` guard in `_confrontation_verb_hits`. Pathological (no live pack writes a stopword-only verb) and the runtime guard is correct defensive code; consider a loud load-time warn in `ConfrontationDef` post-init. Not required for this story. *Found by Reviewer during code review.*
- **Gap** (blocking — POST-MERGE acceptance, not a code blocker): AC1's literary-attack routing fix is a `CONFRONTATION_TRIGGER_CORE` prompt change whose efficacy cannot be unit-proven (the harness stubs the LLM). The code is APPROVED, but the ping-pong finding is NOT closed until a live `/sq-playtest` re-runs the beneath_sunden T5 repro ("…drives the point hard at the crouched thing…") and confirms `ENCOUNTER_STARTED`. SM/Keith: this is the real acceptance probe; merge unblocks it. Affects `sidequest/agents/narrator_guardrails.py` + `~/Projects/sq-playtest-pingpong.md` (mark 158-2 resolved only after the playtest passes). *Found by Reviewer during code review (re-review round-trip 1).*
- **Improvement** (non-blocking): [SEC-LOW] `test_active_encounter_suppresses_unrouted_log` uses a hand-rolled `_ActiveEncounter` stub rather than the real `StructuredEncounter`. Faithful today (duck-typed `getattr(_enc, "resolved", False)`; real field is `bool=False`), but if `encounter` becomes a richer model add a real-type wiring test. Affects `tests/server/test_158_2_literary_attack_routing.py`. *Found by Reviewer during code review (re-review).*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 1 Conflict, 0 Question, 0 Improvement)
**Blocking:** 2 BLOCKING items — see below

**BLOCKING:**
- **Conflict:** [SEC] The `confrontation_verb_unrouted` log now emits at INFO and includes `action[:120]` — raw player text (CWE-532 / python lang-review rule #4 "never log PII"). The rest of the codebase logs `action_len` (an integer), never raw text; raising this from DEBUG→INFO pushes raw player input into prod logs (`~/.sidequest/logs`). Affects `sidequest/server/intent_router_pass.py`.
- **Gap:** The now-INFO unrouted-verb log fires during ACTIVE combat (verified empirically: an active unresolved encounter + "I strike the orc again" emits `confrontation_verb_unrouted` at INFO, because once seated the router uses beat_selections so `conf_types` is empty). That is expected suppression, not a miss — logging it loudly every combat turn dilutes the exact AC3 signal this story raised it to surface. Affects `sidequest/server/intent_router_pass.py`.


### Downstream Effects

- **`sidequest/server`** — 2 findings

### Deviation Justifications

4 deviations

- **AC1/AC2/AC4 LLM-routing halves are validated by playtest, not deterministic units**
  - Rationale: Pinning an LLM decision through a stubbed router is vacuous (passes before and after the fix), and grepping the prompt is a forbidden source-text wiring test. Deterministic units cover what can be honestly pinned.
  - Severity: major
  - Forward impact: Dev MUST do the `CONFRONTATION_TRIGGER_CORE` prompt fix and validate against the beneath_sunden T5/T6 repro; green units are NOT proof the headline routing is fixed (see blocking Delivery Finding).
- **Modified an existing test to the new INFO contract (supersedes Story 126-6)**
  - Rationale: That test pinned the exact behavior 158-2 changes; leaving it untouched would create two contradictory tests. Honest reconciliation beats a silent contradiction.
  - Severity: minor
  - Forward impact: Dev's DEBUG→INFO change turns both this test and the new INFO tests green at once.
- **Edited the load-bearing CONFRONTATION_TRIGGER_CORE prompt with no failing unit driving it**
  - Rationale: AC1 is the story's headline; the OTEL/detector changes alone do not make a literary attack START combat. The fingerprint guards (test_57_4, test_61_18) still pass — the clause is additive, no fingerprint removed.
  - Severity: major
  - Forward impact: Requires playtest validation (see blocking Delivery Finding). Adds ~0.6KB to the cached system prompt; the oversized-prompt canary (test_61_3) still passes.
- **Widened the detector via tokenize() rather than adding a second span**
  - Rationale: The `confrontation_classified` span already carries the signal; AC3's "or" lets me pick the cheaper, non-duplicative path.
  - Severity: minor
  - Forward impact: none — `verb_hits` string format (`type:verb`) is unchanged, so the existing span-attribute tests are unaffected.

## Design Deviations

No deviations logged at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1/AC2/AC4 LLM-routing halves are validated by playtest, not deterministic units**
  - Spec source: context-story-158-2.md, AC1 + AC2 + AC4
  - Spec text: "A literary/described attack ... routes to a confrontation and dispatches (ENCOUNTER_STARTED / confrontation seated)" / "The blunt 'attacks X with Y' form continues to route correctly" / "Non-combat described actions ... must NOT be mis-routed to combat"
  - Implementation: RED tests target only the deterministic OBSERVABILITY layer (detector widening + log re-raise). The actual route/no-route decision is the Haiku `IntentRouter.decompose` pass, which the harness stubs; the routing behavior is delegated to the T5/T6 playtest repro + router eval corpus.
  - Rationale: Pinning an LLM decision through a stubbed router is vacuous (passes before and after the fix), and grepping the prompt is a forbidden source-text wiring test. Deterministic units cover what can be honestly pinned.
  - Severity: major
  - Forward impact: Dev MUST do the `CONFRONTATION_TRIGGER_CORE` prompt fix and validate against the beneath_sunden T5/T6 repro; green units are NOT proof the headline routing is fixed (see blocking Delivery Finding).
- **Modified an existing test to the new INFO contract (supersedes Story 126-6)**
  - Spec source: context-story-158-2.md, AC3
  - Spec text: "a loud OTEL signal is emitted at INFO (re-raise `confrontation_verb_unrouted` ...)"
  - Implementation: Renamed `test_intent_router_confrontation_classified.py::test_verb_hit_with_no_dispatch_logs_at_debug_not_warning` → `::test_verb_hit_with_no_dispatch_logs_at_info` and changed the assertion from `levelno == DEBUG` to `levelno >= INFO`, with a supersession note.
  - Rationale: That test pinned the exact behavior 158-2 changes; leaving it untouched would create two contradictory tests. Honest reconciliation beats a silent contradiction.
  - Severity: minor
  - Forward impact: Dev's DEBUG→INFO change turns both this test and the new INFO tests green at once.

### Dev (implementation)
- **Edited the load-bearing CONFRONTATION_TRIGGER_CORE prompt with no failing unit driving it**
  - Spec source: context-story-158-2.md, AC1
  - Spec text: "A literary/described attack against a present, live creature (verb buried in prose ...) routes to a confrontation and dispatches"
  - Implementation: Added a "described/literary attack" clause to `CONFRONTATION_TRIGGER_CORE` (narrator_guardrails.py) — the LLM steering surface the IntentRouter system prompt composes. No RED unit covers it (per TEA's deviation, LLM routing is not deterministically testable); I implemented it anyway because shipping only the observability half would leave the headline player bug unfixed (CLAUDE.md "No half-wired features").
  - Rationale: AC1 is the story's headline; the OTEL/detector changes alone do not make a literary attack START combat. The fingerprint guards (test_57_4, test_61_18) still pass — the clause is additive, no fingerprint removed.
  - Severity: major
  - Forward impact: Requires playtest validation (see blocking Delivery Finding). Adds ~0.6KB to the cached system prompt; the oversized-prompt canary (test_61_3) still passes.
- **Widened the detector via tokenize() rather than adding a second span**
  - Spec source: context-story-158-2.md, AC3 + TEA Improvement finding
  - Spec text: "re-raise `confrontation_verb_unrouted` or an equivalent 'combat verb seen but not routed' span"
  - Implementation: `_confrontation_verb_hits` now matches on the shared `tokenize()` (subset-of-action-tokens) instead of raw `\bverb\b`; log re-raised to INFO. No new OTEL span added.
  - Rationale: The `confrontation_classified` span already carries the signal; AC3's "or" lets me pick the cheaper, non-duplicative path.
  - Severity: minor
  - Forward impact: none — `verb_hits` string format (`type:verb`) is unchanged, so the existing span-attribute tests are unaffected.

### Reviewer (audit)
- **TEA — AC1/AC2/AC4 LLM-routing validated by playtest, not units** → ✓ ACCEPTED by Reviewer: correct call. The route/no-route decision is a Haiku LLM judgment; a stub-router unit would be vacuous and grepping the prompt is a forbidden source-text wiring test. The playtest gate is carried forward as a blocking finding.
- **TEA — Modified existing test to INFO (supersedes Story 126-6)** → ✓ ACCEPTED by Reviewer: honest reconciliation of a directly-contradicted test; the supersession is documented in the test body. (Note: the *module docstring* was missed — flagged as a non-blocking DOC finding.)
- **Dev — Edited CONFRONTATION_TRIGGER_CORE with no failing unit** → ✓ ACCEPTED by Reviewer: implementing AC1's headline is correct, not scope creep; shipping observability-only would be a half-wired feature. Fingerprints (test_57_4, test_61_18) and the oversized canary (test_61_3) all still pass — verified.
- **Dev — Widened detector via tokenize() rather than a new span** → ✓ ACCEPTED by Reviewer (with caveat): the minimalist choice is sound and the `type:verb` format is preserved. BUT re-raising the *existing* log to INFO without an encounter-gate is what surfaced the combat-noise regression — see the blocking Gap finding. The deviation itself is accepted; the side effect is a separate finding.
- **Round-trip 1 (re-review):** No NEW deviations introduced by the rework — the fixes (encounter gate + `action_len`) implement the Reviewer's round-trip-0 findings and do not diverge from spec. All prior deviations remain ACCEPTED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a

**Test Files:**
- `tests/server/test_158_2_literary_attack_routing.py` (new) — 6 tests: 2 RED (inflected-verb detection; unrouted log at INFO), 4 green guards (span carries verb; described movement stays silent; stemmed near-miss "withdraw"≠"draw"; blunt-verb detection regression).
- `tests/server/test_intent_router_confrontation_classified.py` (modified) — 1 test re-pinned DEBUG→INFO (RED).

**Tests Written:** 3 RED + 6 green-guard, covering the deterministic (observability) slices of ACs 1, 3, 4. AC2's detector half is guarded; the AC1/AC2/AC4 LLM-routing halves are delegated to playtest (see deviation + blocking finding).
**Status:** RED (verified by testing-runner, RUN_ID 158-2-tea-red — 3 fail, 6 pass, 0 collection errors)

**Wiring:** All tests drive the real production entry point `execute_intent_router_pre_narrator_pass` (called from `websocket_session_handler.py` before the narrator), so they are behavior/wiring tests, not isolated units.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| python.md L17/L41-43 — observability/error events must not be logged at DEBUG | `test_unrouted_combat_verb_logs_at_info_not_debug`, `test_verb_hit_with_no_dispatch_logs_at_info` | failing |
| python.md L60-63 — no vacuous assertions | self-check: every test asserts a concrete value (span count, attr value, `levelno`); no `assert True`, no truthy-on-always-None | n/a |
| No source-text wiring tests (server CLAUDE.md) | tests assert OTEL spans + caplog via the real pass, never grep prod source | passing |

**Rules checked:** 3 of 3 applicable lang-review rules have coverage.
**Self-check:** 0 vacuous tests found.

**RED expectations confirmed:**
- `test_described_attack_with_inflected_verb_is_detected` — span 0, expected 1 (detector blind to "hacks").
- `test_unrouted_combat_verb_logs_at_info_not_debug` — logged at DEBUG, expected ≥ INFO.
- `test_verb_hit_with_no_dispatch_logs_at_info` — logged at DEBUG, expected ≥ INFO.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Two deterministic deliverables: (1) widen `_confrontation_verb_hits` to stem via the shared `tokenize()`; (2) re-raise the `confrontation_verb_unrouted` log to INFO. PLUS the non-unit-testable headline fix: steer `CONFRONTATION_TRIGGER_CORE` to recognize described attacks, and validate against the T5/T6 beneath_sunden repro (the green units do NOT cover this).

---
## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/agents/narrator_guardrails.py` — added a "described/literary attack" clause to `CONFRONTATION_TRIGGER_CORE` (the IntentRouter steering surface): a buried-verb attack against a present, named target is a strike even when the literal word "attack" never appears and even when the action opens with a preparation clause. This is the headline AC1 routing fix.
- `sidequest/server/intent_router_pass.py` — `_confrontation_verb_hits` now matches on the shared suffix-stripping `tokenize()` (subset-of-action-tokens) instead of raw `\bverb\b`, so inflected combat verbs ("hacks", "striking", "stabbed") are no longer lexically invisible; still word-level ("withdraw" ≠ "draw"). Re-raised the `confrontation_verb_unrouted` log DEBUG→INFO (supersedes Story 126-6).

**Tests:** 61/61 passing (GREEN). The 3 previously-RED tests now pass; the fingerprint guards (test_57_4, test_61_18), the oversized-prompt canary (test_61_3), the router corpus, and the intent-router telemetry/vocabulary siblings all still pass. (RUN_ID 158-2-dev-green.)
**Branch:** feat/158-2-intentrouter-literary-attack-routing (pushed)

**AC coverage:**
- AC1 (literary attack routes): prompt steering landed; effect is LLM-driven → playtest validation outstanding (blocking Delivery Finding).
- AC2 (no regression on blunt): detector-side guarded green; routing is LLM (same playtest gate).
- AC3 (OTEL visibility): log re-raised to INFO; existing `confrontation_classified` span retained — both unit-pinned green.
- AC4 (no false positives): detector false-positive guards green ("withdraw"≠"draw", described movement silent).

**Self-review:** Wired (changes are on the live pre-narrator pass + the IntentRouter system prompt, both production paths). Follows project patterns (shared `tokenize`, OTEL-first). Error handling n/a (pure detector + prompt + log-level). Lint clean (`ruff check`).

**Handoff:** To Reviewer (Westley) for review. Key thing to scrutinize: AC1's routing fix is a prompt change with NO unit gate — the green suite does NOT prove a literary attack now routes; that needs the beneath_sunden T5 playtest. See the blocking Delivery Finding.

---
## Subagent Results (round-trip 0 — superseded by re-review below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (doc) | confirmed 1 (LOW doc), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (low) | confirmed 1 (LOW, non-blocking), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (medium) | confirmed 1 (MEDIUM, rule #4 match — cannot dismiss) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed blocking (1 SEC + 1 own/verified), 2 confirmed non-blocking (DOC, SILENT), 0 dismissed

## Reviewer Assessment (round-trip 0 — REJECTED, superseded by re-review below)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM][SEC] | Raw player text (`action[:120]`) logged at INFO — CWE-532 / python rule #4 "never log PII". Codebase pattern is `action_len`. DEBUG→INFO (this diff) pushes it into prod logs. | `sidequest/server/intent_router_pass.py` unrouted log block (~L898) | Drop `action_preview=%r` + `action[:120]`; keep `verb_hits` (or log `action_len`). |
| [MEDIUM] | unrouted-verb INFO log fires during ACTIVE combat (verified empirically) — expected suppression logged loudly every combat turn dilutes the AC3 signal. | `sidequest/server/intent_router_pass.py` unrouted log block (~L889) | Gate the log on `snapshot.encounter is None or resolved`. |
| [LOW][DOC] | Module docstring still says "a DEBUG log" though the test asserts INFO. | `tests/server/test_intent_router_confrontation_classified.py:13` | Update docstring to INFO. |
| [LOW][SILENT] | All-stopword `intent_verb` silently skipped (pathological; runtime guard correct). | `_confrontation_verb_hits` | Optional: loud load-time warn in `ConfrontationDef`. Not required for this story. |

**Why REJECT on two MEDIUMs:** The [SEC] finding matches a stated project rule (#4 — never log PII) and per reviewer doctrine a rule-matching finding is CONFIRMED, not dismissable. The diff *elevated* that exposure (DEBUG→INFO → prod-captured). The second MEDIUM is an empirically-verified regression that undermines this very story's AC3 (OTEL signal clarity). Both land on the *same newly-changed log statement* and the fix is small. An adversarial reviewer should not ship a confirmed rule-#4 PII issue plus an AC3-undermining noise regression when the fix is a few lines on the line this story just touched.

**Subagent dispatch coverage (all 8 tags):**
- [EDGE] — subagent disabled; I enumerated edge cases myself: empty action (`tokenize`→empty, guarded early-return ✓), all-punctuation/10k-char action (linear `[^a-z0-9]+` split, no ReDoS — security-confirmed ✓), inflected verb ("hacks"→"hack" ✓), stemmed near-miss ("withdraw"≠"draw" ✓), all-stopword verb (silently skipped — LOW finding).
- [SILENT] — confirmed 1 LOW (all-stopword verb skip). No swallowed errors; the new code adds no try/except.
- [TEST] — subagent disabled; I assessed myself: tests drive the real `execute_intent_router_pre_narrator_pass` (no source-text wiring tests ✓), assert concrete values (span count, attr, `levelno`) — no vacuous assertions; the fake faithfully mirrors `intent_verb_set`. The combat-active edge case is NOT covered by a test (→ part of the rework: TEA should add an encounter-active suppression test + a no-raw-text-in-log test).
- [DOC] — confirmed 1 LOW (stale module docstring).
- [TYPE] — subagent disabled; I checked: `_confrontation_verb_hits` keeps its `-> list[str]` signature; `tokenize` returns `frozenset[str]`; subset op is type-correct. No stringly-typed regressions.
- [SEC] — confirmed 1 MEDIUM (raw-text-at-INFO, above). ReDoS/injection/deserialization all clean (security-confirmed).
- [SIMPLE] — subagent disabled; I checked: the change is minimal and non-duplicative (reuses shared `tokenize`); no over-engineering.
- [RULE] — subagent disabled; rule-checker domain covered by my Rule Compliance section below + the [SEC] rule-#4 hit.

### Rule Compliance (python lang-review enumerated against the diff)
- **#1 Silent exception swallowing:** No new try/except introduced. PASS.
- **#3 Type annotations at boundaries:** `_confrontation_verb_hits(action: str, pack: GenrePack | None) -> list[str]` fully annotated. PASS.
- **#4 Logging coverage AND correctness:** Lazy `%s`/`%r` used (good); BUT logs raw player text (PII) — **VIOLATION** (see [SEC]). Level-classification of the unrouted signal as INFO is otherwise reasonable.
- **#6 Test quality:** New tests assert concrete values, no `assert True`, no vacuous truthy, no unexplained skips. PASS (gap: combat-active case untested — addressed in rework).
- **#8 Unsafe deserialization / #9 Async pitfalls:** `tokenize` is pure regex/string ops; the pass is async and adds no blocking calls. PASS.

### Data flow traced
Player `action` (untrusted) → `execute_intent_router_pre_narrator_pass` → `_confrontation_verb_hits(action, pack)` → `tokenize(action)` (pure, no LLM, no I/O) → `frozenset` subset check vs authored `intent_verbs` → `verb_hits` list → OTEL span attr + **INFO log containing `action[:120]`** (← the PII leak point) . The `action`→LLM path (`IntentRouter.decompose`) is unchanged by this diff (ADR-047 unaffected). Safe except the log payload.

### Devil's Advocate
Assume this code is broken. A malicious or careless player types a 4,000-character action with a credit-card number in the first sentence and the word "strike" later: `tokenize` handles the length fine (linear split, security-verified), but the INFO log now persists "strike"-triggered `action_preview` with the first 120 chars — potentially the card number — to a plaintext local log. That is the realistic harm (rule #4). A confused author writing a multi-word `intent_verb` like "open fire" would get looser non-contiguous subset matching ("open … fire" anywhere) than the old contiguous regex — but I verified *every* current pack uses single-word verbs, so no live impact; it is a future-author footgun only (LOW). A stressed combat session is the worst case for the noise regression: the player hammers "I strike / I hack / I stab" each round, and every round emits an INFO `confrontation_verb_unrouted` even though combat is correctly seated — the GM panel's signal-to-noise for *genuine* unrouted misses drops exactly when the table is busiest. What about an empty/whitespace action? Guarded (`if not action_tokens: return []`). What about a pack with zero confrontations? Guarded (`if not confrontations: return []`). The prompt clause: a static constant, no interpolation, no injection vector, fingerprints intact. Net: the logic is correct; the two MEDIUM issues are both on the log statement and both worth fixing before merge. Nothing rises to Critical/High — but the combination clears my bar for a quick rework.

### Observations (≥5)
1. [VERIFIED] `_confrontation_verb_hits` token-subset matching is correct and reuses the shared `tokenize` — evidence: intent_router_pass.py:211-219; 36/36 targeted tests green incl. inflected-verb detection.
2. [VERIFIED] Fingerprints preserved — evidence: test_57_4 + test_61_18 pass; `"Do NOT defer it to the"`, `"exactly as mechanically binding as a weapon drawn"`, `"fire the pre-combat type at the FIRST show of force"` all still in the constant.
3. [VERIFIED] No ReDoS — `_TOKEN_SPLIT = r"[^a-z0-9]+"` is a linear char-class split; security subagent measured 10k-char input at 0.07ms.
4. [MEDIUM][SEC] Raw player text logged at INFO (CWE-532 / rule #4) — intent_router_pass.py unrouted log block.
5. [MEDIUM] unrouted INFO log fires during active combat (verified empirically) — intent_router_pass.py unrouted log block.
6. [LOW][DOC] Stale module docstring — test_intent_router_confrontation_classified.py:13.
7. [LOW][SILENT] All-stopword verb silently skipped — _confrontation_verb_hits.
8. [NOTE] AC1's routing fix (the prompt clause) is correct in approach but NOT unit-verifiable; the beneath_sunden T5 playtest gate (Dev's blocking finding) remains the real acceptance probe — this is sound and accepted, not a reject reason.

**Handoff:** Back to TEA (Fezzik) for red rework — both blocking findings are testable behaviors (encounter-active suppression; no-raw-text-in-log). Add the failing tests, then Dev implements the small log-statement fix.

---
## Dev Assessment (round-trip 1 rework)

**Implementation Complete:** Yes
**Both blocking Reviewer findings addressed** (commit `839dcceb`):
- [SEC / CWE-532] The unrouted-verb log no longer echoes raw player text — `action[:120]`/`action_preview=%r` replaced with `action_len=%d`, matching the codebase's no-PII-in-logs convention. (`sidequest/server/intent_router_pass.py`)
- [noise/AC3] The unrouted-verb INFO log is now gated on no-active-confrontation (`_enc is not None and not resolved` → suppressed). During active combat a described attack routes to a beat, so the verb-hit-without-dispatch there is expected and no longer logged — only genuine no-encounter misses surface. (`sidequest/server/intent_router_pass.py`)

**Non-blocking findings:**
- [DOC] Fixed: the stale module docstring in `tests/server/test_intent_router_confrontation_classified.py` now reflects the INFO + no-encounter contract.
- [SILENT] Not actioned (Reviewer marked "not required for this story"; pathological — no live pack writes a stopword-only verb, and the runtime guard is correct defensive code).

**New guard tests:** `test_active_encounter_suppresses_unrouted_log`, `test_unrouted_log_omits_raw_action_text` — both pin the fixes.
**Tests:** 43/43 passing (GREEN), incl. the two new guards; fingerprints (test_57_4, test_61_18) still green. (RUN_ID 158-2-dev-green-rework.) Lint clean.
**Branch:** feat/158-2-intentrouter-literary-attack-routing (pushed, `839dcceb`).

**Handoff:** Back to Reviewer (Westley) for re-review. The AC1 prompt-fix playtest gate (Dev's earlier blocking finding) is unchanged and still outstanding for story-close.

---
## Subagent Results

(Re-review — round-trip 1. Re-ran the 3 enabled subagents on the rework diff `839dcceb`.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (31/31 green, lint clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A — verified gate has no swallow path |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (low) | prior MEDIUM RESOLVED; 1 new LOW deferred |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 blocking, 1 new non-blocking LOW (deferred). Both prior blocking findings RESOLVED.

## Reviewer Assessment

**Verdict:** APPROVED

**Both round-trip-0 blocking findings RESOLVED (verified, not just claimed):**
- [SEC/CWE-532] PII fix — `intent_router_pass.py:909-914` now logs `action_len=%d`/`len(action)`; the `action[:120]`/`action_preview=%r` raw player text is gone. Confirmed by me (read), the security subagent (rule-#4 violations now 0), and the regression guard `test_unrouted_log_omits_raw_action_text` (injects a fake secret, asserts no token leaks).
- [noise/AC3] Encounter gate — `intent_router_pass.py:895-897` adds `_encounter_active = _enc is not None and not getattr(_enc, "resolved", False)` and only logs when `not _encounter_active`. Mirrors the established `_beat_invocations_outside_confrontation` pattern. Confirmed by `test_active_encounter_suppresses_unrouted_log` (verified empirically by me in round-trip 0 that it fired before; now suppressed).
- [DOC] Stale module docstring fixed.

**Subagent dispatch coverage (all 8 tags):**
- [EDGE] — disabled; I re-enumerated the gate's truth table myself (None→fires, resolved=True→fires, resolved=False→suppressed, empty action→guarded). All correct.
- [SILENT] — re-ran: CLEAN. Gate has no swallow path; `getattr(_enc, "resolved", False)` default is the conservative direction (a fieldless fake → treated active → suppress, never a false miss). Subagent confirmed `StructuredEncounter.resolved` is a real `bool = False` field (encounter.py:371), so the real type works.
- [TEST] — disabled; I assessed: 2 new guard tests pin both fixes; 43→ now 31/31 in the re-review subset all green; no vacuous assertions.
- [DOC] — fixed this round (docstring).
- [TYPE] — disabled; signatures unchanged; the gate is plain bool logic. No issues.
- [SEC] — re-ran: prior MEDIUM RESOLVED; 1 new LOW (test uses a hand-rolled `_ActiveEncounter` stub rather than the real type — defense-in-depth, "no immediate action required"; the duck-typed getattr makes the stub faithful and the silent-failure subagent confirmed the real field exists). Deferred.
- [SIMPLE] — disabled; the rework is minimal (one gate + one format change). No over-engineering.
- [RULE] — disabled; rule #4 (no PII in logs) now COMPLIANT (was the round-trip-0 violation). All other applicable python rules pass.

### Rule Compliance (delta from round-trip 0)
- **#4 Logging — never log PII:** was VIOLATION (raw `action[:120]`), now **PASS** (`action_len` only). The level-classification (INFO for a genuine no-encounter miss) is correct and now properly scoped.
- All other rules unchanged from round-trip 0 (PASS).

### Data flow re-traced
Player `action` → `_confrontation_verb_hits` (pure) → `verb_hits` → INFO log **now emits only `verb_hits` + `action_len`** (no raw text) **and only when no confrontation is active**. The PII leak point identified in round-trip 0 is closed.

### Devil's Advocate (re-review)
Could the gate suppress a REAL miss? Only if `snapshot.encounter` is non-None and `resolved=False` — i.e., combat is genuinely active — in which case a described attack is correctly a beat, not a missed new confrontation, so suppression is right. A resolved encounter (post-combat) still fires the log (correct — a literary attack after combat ends is a fresh potential miss). Could a malicious 4000-char action with a card number leak now? No — only `len(action)` (an int) is logged. Could the new stub mask a real-type incompatibility? The silent-failure subagent confirmed `StructuredEncounter.resolved` exists as `bool=False`, and the getattr default is conservative, so no. Nothing rises to a finding.

### Observations (≥5)
1. [VERIFIED] PII removed — intent_router_pass.py:909-914 logs `action_len`; guard test asserts no secret tokens leak.
2. [VERIFIED] Encounter gate correct — intent_router_pass.py:895-897; truth table re-enumerated; guard test pins active-combat suppression.
3. [VERIFIED] Real `resolved` field exists (`bool=False`, encounter.py:371) — duck-typed getattr is faithful; conservative default.
4. [VERIFIED] Lint clean + 31/31 (re-review subset) / fingerprints (test_57_4, test_61_18) green.
5. [LOW][SEC] Test stub fidelity — deferred defense-in-depth note; no action required for this story.
6. [NOTE] AC1 prompt-fix playtest gate still outstanding — a post-merge acceptance step in the epic's ping-pong loop, NOT a code-review blocker (see delivery finding).

**Data flow traced:** player `action` → `_confrontation_verb_hits` → `verb_hits` → gated INFO log (`verb_hits` + `action_len` only). Safe.
**Pattern observed:** encounter-state gating mirrors `_beat_invocations_outside_confrontation` at intent_router_pass.py:236-237 — consistent.
**Error handling:** pure detector + bool gate + log; no new failure paths (silent-failure subagent: clean).
**Handoff:** To SM for finish-story.