---
story_id: "158-50"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-50: ADR-130 orbital course/story-clock inert in play

## Story Details
- **ID:** 158-50
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-02T12:50:29Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-02T11:51:43Z | 2026-07-02T11:53:22Z | 1m 39s |
| red | 2026-07-02T11:53:22Z | 2026-07-02T12:14:33Z | 21m 11s |
| green | 2026-07-02T12:14:33Z | 2026-07-02T12:38:26Z | 23m 53s |
| review | 2026-07-02T12:38:26Z | 2026-07-02T12:50:29Z | 12m 3s |
| finish | 2026-07-02T12:50:29Z | - | - |

## Sm Assessment

**Story:** 158-50 — ADR-130 orbital course/story-clock inert in play (3 pts, p2, tdd/phased, repo: sidequest-server).

**Problem (root cause already pinned):** The course subsystem is fully implemented and registered — `run_course_dispatch` at `agents/subsystems/__init__.py:213`, orbital_content threaded into the bank context, and a dispatch-engagement lie-detector for "course" all exist — but the IntentRouter can never produce its trigger. The router's prompt gates course emission on a `<courses>` block being present in the state summary (`intent_router.py:287-300`), yet `compute_courses` / `format_courses_block` are only called for the NARRATOR prompt (`orchestrator.py:2817-2849`, `narration_apply.py`) and never in `intent_router_pass.py`. So the router never sees a `<courses>` block, never classifies travel, and `run_course_dispatch` is never invoked → `plotted_course` stays `None`, `clock_t_hours` never advances, the orrery STARDATE freezes at 0.0. This is the CLAUDE.md half-wired-trigger anti-pattern: registered subsystem, unreachable trigger.

**Fix direction (Dev's call):** Assemble a `<courses>`/orbital-tier block into the router's state summary in `intent_router_pass.py`, reusing `compute_courses` + `format_courses_block` (Don't Reinvent), gated on `session.orbital_content` present. Alternatively relax the router gating to detect the orbital tier from a field already in its summary. Beware the `actor_location_unresolved` red herring — per the code comment at `intent_router_pass.py:436-437` an unresolved location makes the projection pass through, it does NOT drop a courses block; the block simply isn't assembled for the router at all.

**Wiring test (mandatory, per CLAUDE.md + story):** A NL travel-to-named-body action in an orbital world must produce a course dispatch + non-None `plotted_course` + advanced `clock_t_hours`, asserted via OTEL span (not source-grep). This is the acceptance spine — RED must fail because no course dispatch fires today.

**Scope discipline:** course/clock only. The dogfight half is story **158-49** — do NOT touch it. Ground/personal SWN combat is already green and out of scope.

**Routing:** Phased TDD → handing off to TEA (Fezzik) for RED. Then DEV → REVIEWER → SM. No Jira integration (no key, Jira not enabled). Branch `feat/158-50-adr130-course-dispatch` created from main.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Bug fix with an explicit mandatory wiring test (OTEL span assertion). The seam 158-50 fixes is precisely the one the green 153-5 suite *stubbed past*.

**Test File:**
- `sidequest-server/tests/agents/subsystems/test_course_router_summary_wiring.py` — 5 tests. Drives the REAL production pre-pass (`execute_intent_router_pre_narrator_pass`), not a hand-built bank context, so it exercises the exact seam the fix touches (the summary the real router consumes). Wiring proven by OTEL spans + behavior, never a source-text grep (CLAUDE.md "No Source-Text Wiring Tests").

**The seam (why 153-5 didn't catch this):** 153-5 wired `course` end-to-end *below* the router and is fully green — but every one of its tests injects the `course` `SubsystemDispatch` directly, because "the router's classification *is* the input to this layer." 158-50 is that input: the real router can never emit `course` because its state summary never carries a `<courses>` block. `compute_courses`/`format_courses_block` are built only for the NARRATOR prompt (`orchestrator.py`), never in `intent_router_pass.py::_build_state_summary`. Verified empirically — the router summary today is `{"genre_slug":"space_opera","world_slug":"coyote_star","clock_t_hours":100.0,"party_body_id":"turning_hub","quest_anchors":["red_prospect"]}` with no `<courses>` block.

**RED discriminator (leak-proof):** the literal `<courses>` marker (what `intent_router.py:292`'s gate keys on and what `format_courses_block` emits). A quest_anchor serializes as a plain `["red_prospect"]` list and never mints that tag — so a naive "destination name present" check would false-green (the name *is* in the summary via quest_anchors); the marker is the honest signal.

**On the router doubles (no live LLM, per `feedback_no_content_coupled_tests` + 153-5 precedent):**
- `_recording_router` captures the `state_summary` the pass hands the router (Test 1 asserts on it directly).
- `_courses_gated_router` is a *contract* double, not a content stub — it encodes the exact rule `intent_router.py:292` encodes (emit `course` iff a `<courses>` block is present), so its emission tracks the one thing 158-50 changes. Today: no block → emits nothing → no span → RED. After fix: block present → emits `course` → the green engine fires the spans → GREEN.

**AC coverage matrix:**

| AC | Test | State |
|----|------|-------|
| AC-1 (RED wiring, `course.plot` span fires) | `test_orbital_travel_action_dispatches_course_and_ticks_clock` | **RED** |
| AC-2 (router summary carries `<courses>` block) | `test_router_state_summary_carries_courses_block_for_orbital_world` | **RED** |
| AC-3 (`plotted_course` non-None + clock advances by ETA) | `test_orbital_travel_action_dispatches_course_and_ticks_clock` | **RED** |
| AC-4 (loud reject `no_orbital_tier` / `no_party_anchor`) | `test_course_rejects_loud_when_world_has_no_orbital_tier`, `test_course_rejects_loud_when_party_has_no_anchor` | GREEN guard |
| AC-5 (`dispatch_engagement.course.mismatch` lie-detector) | already green in `test_course_clock_dispatch_wiring.py` (witness registered + mismatch detection) — not re-tested | GREEN (existing) |
| AC-6 (regression: non-orbital worlds unaffected) | `test_non_orbital_world_gets_no_courses_block_and_no_dispatch` | GREEN guard |

**Tests Written:** 5 (2 RED fix-targets, 3 GREEN guards) covering 6 ACs
**Status:** RED — the 2 fix-target tests fail on the intended assertions (`<courses>` marker absent; `course.plot` span never fires). 657 neighboring tests (agents/subsystems + orbital) stay green; 153-5 sibling suite 9/9 green — no collateral damage.

### Rule Coverage

This is a **test-only** RED change; the Python lang-review checklist governs the *production* code Dev writes in GREEN. The one check that applies directly to a test file is enforced:

| Rule (python.md) | Coverage | Status |
|------|---------|--------|
| #6 Test quality | Every test asserts specific values with diagnostic messages; router doubles are real `async def` assigned to `router.decompose` (mock target correct — no `mock.patch` on the wrong symbol); no `assert True`/truthy-only/assertion-free tests; no skips | pass |

**Rules Dev must satisfy in GREEN (flagged for the fix):** #1 silent exceptions (the block must be *gated*, not silently defaulted — No Silent Fallbacks), #3 type annotations at the summary-builder boundary, #4 logging on the gate decision, #13 fix-introduced regressions.
**Self-check:** 0 vacuous tests found (the `<courses>` marker discriminator was chosen specifically to avoid the quest_anchors false-green).

**Handoff:** To Dev (Inigo Montoya) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**The fix (mirrors the narrator — Don't Reinvent):** `_build_state_summary` (`sidequest/server/intent_router_pass.py`) now assembles the SAME `<courses>` block the narrator builds (`orchestrator.py` ~2814: `_bodies_in_scope` + `compute_courses` + `format_courses_block`), gated exactly like the narrator — an orbital tier (`orbital_content`) AND a party body anchor. The block string lands under `summary["courses"]`, so when `decompose` serializes the summary to JSON the `<courses>` marker is in game_state and the router's own gate (`intent_router.py:292`) can finally fire. A `course.compute` span is emitted for GM-panel evidence the router saw the block (previously nothing fired — the SWN-ORBITAL-COURSE-INERT blind spot).

**Threaded the full narrator inputs, not just `orbital_content` (avoids a half-fix):** `compute_courses` needs `in_scope_body_ids` + `recent_body_mentions` + `quest_anchors`. Only `quest_anchors` is on the snapshot; `orbital_scope` and `recent_body_mentions` live on the Session. Added `orbital_scope` + `recent_body_mentions` kwargs to `execute_intent_router_pre_narrator_pass` and threaded `_session.orbital_scope` + `list(_session.recent_body_mentions)` from the caller (`websocket_session_handler.py`, right where `orbital_content` is already threaded). Without this, the router block would carry only quest-anchored bodies and travel to an in-scope-but-not-quest body (the actual playtest case, "The Horn") would stay inert.

**Files Changed:**
- `sidequest/server/intent_router_pass.py` — courses block in `_build_state_summary`; `orbital_scope`/`recent_body_mentions` params on the pre-pass, threaded into the builder.
- `sidequest/server/websocket_session_handler.py` — thread the Session's `orbital_scope` + `recent_body_mentions` into the pre-pass.
- `tests/agents/subsystems/test_movement_dispatch.py` — stale `_build_state_summary` monkeypatch stub now accepts `**kwargs` (its fixed-signature lambda broke on the added params; it re-breaks on every param addition — `**kwargs` future-proofs it).

**Tests:** All 5 story tests GREEN (2 former RED fix-targets now pass, 3 guards hold). Sibling 153-5 suite 9/9 green; full movement-dispatch file green. `intent_router_pass.py` pyright: 0 errors; `websocket_session_handler.py` added 0 new pyright errors (28 pre-existing, none in the edit region). ruff check/format clean.

**Full-suite regression:** `9 failed, 13039 passed, 1709 skipped`. Verified via `git stash` of my source changes that 8 of the 9 are PRE-EXISTING on `develop` (7 fail identically without my change; the 8th, `test_pregen_bestiary_90_1[evropi]`, was an xdist worker-crash flake that passes in isolation) — all unrelated to 158-50 (dogfight content 158-49, wwn cast 158-53, mutant_wasteland mutations, beneath_sunden content, sealed-letter frame-default debt). The 9th (`test_movement_dispatch::test_wiring_intent_router_pass_threads_context`) was the ONLY real regression from my change (stale mock) and is fixed.

**Branch:** `feat/158-50-adr130-course-dispatch` (pushed)

**Handoff:** To Reviewer (Westley) — or verify phase per workflow.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — ruff/format clean, 443 tests pass, pyright 0 errors on intent_router_pass.py |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge domain assessed by Reviewer (see Rule Compliance + Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (both medium) | confirmed 2 (both LOW after severity assessment), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality assessed by Reviewer (see observations [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — comments assessed by Reviewer (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — types assessed by Reviewer (see [TYPE] rule #3) |
| 7 | reviewer-security | Yes | clean | none | N/A — injection refuted (allowlist gate + hardcoded label_hint), bounded (cap 12), counts-only telemetry |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — full lang-review checklist walked by Reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, domains covered by Reviewer)
**Total findings:** 2 confirmed (both LOW, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A focused, correct fix for SWN-ORBITAL-COURSE-INERT. It assembles the `<courses>` block into the IntentRouter state summary by reusing the narrator's exact recipe (`_bodies_in_scope` + `compute_courses` + `format_courses_block`), gated identically (`orbital_content is not None and party_body_id`), and threads the two missing Session inputs (`orbital_scope`, `recent_body_mentions`) so the router block equals the narrator block — not a quest-anchors-only half-fix. No Critical/High issues. Two LOW No-Silent-Fallbacks observations, both non-blocking (one unreachable in production by construction, one following the pre-existing 153-5 pattern).

**Data flow traced:** player action "burn for the Red Prospect" → `websocket_session_handler._execute_narration_turn` threads `_session.orbital_content/orbital_scope/recent_body_mentions` (ws_handler.py:1010-1017) → `execute_intent_router_pre_narrator_pass` → `_build_state_summary` builds `summary["courses"]` (intent_router_pass.py:702-745) → `decompose` serializes it into the Haiku prompt → router sees `<courses>` marker → classifies travel → `course` dispatch → `run_course_dispatch` → `plotted_course` + `clock_t_hours` advance. Wired end-to-end through the real production turn path (safe: body ids/labels are authored world content, allowlist-gated — [SEC] confirmed no player text reaches the prompt).

**Pattern observed:** faithful narrator-mirror (Don't Reinvent) at intent_router_pass.py:702-745 — same helpers, same double-gate, same unconditional `emit_course_compute` before the `if block_text` guard as orchestrator.py:2814-2854. Correct application of the existing conditional-vocabulary pattern (`confrontation_types`/`fate`/`witnessed_act`).

### Observations (Reviewer, adversarial pass)

- **[VERIFIED] End-to-end wiring is real, not a test-only seam** — the change lives in `_execute_narration_turn`, the production per-turn path; the pre-pass call at ws_handler.py:1021 threads all three Session inputs. Evidence: ws_handler.py:1010-1034. Complies with CLAUDE.md "Verify Wiring, Not Just Existence."
- **[SILENT] LOW — scope default `else Scope.system_root()`** at intent_router_pass.py:724 (silent-failure-hunter #1). Confirmed as a No-Silent-Fallbacks footgun: a caller threading `orbital_content` without `orbital_scope` silently gets a different in-scope body set. **Severity LOW / non-blocking because it is unreachable in production BY CONSTRUCTION:** the caller derives `_orbital_scope` and `_orbital_content` from the same `_session is not None` guard, and `Session.orbital_scope` (session.py:119-121) never returns None (`or Scope.system_root()`). So whenever the block builds (`orbital_content is not None` ⟹ `_session is not None`), `orbital_scope` is guaranteed non-None; the `else` branch fires only for test/future callers. It also reproduces the Session's OWN blessed default. Cannot dismiss (matches the doctrine) → confirmed LOW + Delivery Finding recommending a hardening fast-follow.
- **[SILENT] LOW — `_session is None` cascade** at ws_handler.py:1010-1017 (silent-failure-hunter #2). Collapses "no session/room" into the same None as "no orbital tier," whereas ws_handler.py:1209-1214 raises `RuntimeError` for an unexpectedly-None `sd._room`. Confirmed, but **non-blocking: this is the pre-existing Story 153-5 pattern** (the `_orbital_content` line directly above mine has the identical cascade); my change consistently extends it to two more fields rather than introducing it. Hardening (fail loud on unexpected `_session is None`) is a 153-5-scoped concern affecting `_orbital_content` too → Delivery Finding.
- **[TYPE] LOW — `orbital_scope: Any | None` uses `Any` without an explanatory comment** at intent_router_pass.py:365,929 (lang-review rule #3: "Any is acceptable only with a comment explaining why"). Rationale for `Any` is circular-import avoidance (Scope is a lazy import), mirroring TurnContext.orbital_scope:Any (orchestrator.py:973). Cleaner: annotate `Scope | None` with a `TYPE_CHECKING` import (as `OrbitalContent` already is at line 39). Non-blocking; Delivery Finding.
- **[TEST] VERIFIED — tests are honest and non-vacuous.** The `<courses>` marker discriminator is leak-proof (the destination name reaches the summary via `quest_anchors`, but the marker does not — proven empirically by the RED run showing the name present without the tag). Test 1 asserts the real summary contains the block; Test 2 chains block→dispatch→span via a router double faithful to the prompt gate; AC-4 guards call `run_course_dispatch` directly for the two previously-uncovered rejection reasons. No `assert True`/truthy-only/skips. Evidence: test_course_router_summary_wiring.py + preflight 443-green.
- **[DOC] VERIFIED — comments are accurate and cite exact seams** (intent_router_pass.py:702-714 block comment; ws_handler.py:1005-1009). The movement-test stub comment was updated to explain the `**kwargs` future-proofing. No stale/misleading docs.
- **[SIMPLE] VERIFIED — no over-engineering.** Minimal reuse of existing helpers; the only "extra" is threading two Session inputs, which is required by `compute_courses`'s signature (not gold-plating — a quest-anchors-only block would be the half-fix). One incidental ruff-format collapse at intent_router_pass.py:269 (unrelated dogfight-verb line, 99 chars < 100 limit) — benign, formatter-mandated; reverting it would fail `ruff format --check`. Accepted.
- **[EDGE] VERIFIED — boundary paths handled.** party_body_id not in orbits.bodies → `compute_courses` returns `{}` → empty block, no `summary["courses"]`, `emit_course_compute(0)` fires (loud); recent_body_mentions/quest_anchors None → `or []` safe; body count > 12 → capped (COURSES_HARD_CAP). No new mutable-default args (all None-defaulted). Evidence: orbital/course.py:144, 185.
- **[RULE] Observation — `emit_course_compute` fires twice per orbital turn now** (router pre-pass + narrator), with no phase/source attribute to distinguish them; and `dropped_by_cap=0` is hardcoded (both mirror the pre-existing narrator call). Observability-precision nit, not a correctness bug. Delivery Finding.
- **[SEC] VERIFIED — security-neutral.** No player-controlled string reaches the router prompt (allowlist gate on `orbits.bodies`, `label_hint=None`); bounded size; counts-only telemetry. Byte-for-byte reuse of the narrator block already shown to the player. Evidence: security subagent trace of `compute_courses`/`format_courses_block`.

### Rule Compliance (python.md lang-review checklist — Reviewer walked all 13 since rule_checker disabled)

| # | Rule | Verdict |
|---|------|---------|
| 1 | Silent exception swallowing | PASS (no try/except added). Two `[SILENT]` default observations above are LOW/non-blocking, not swallowed exceptions. |
| 2 | Mutable default arguments | PASS — new params default to `None`, never `[]`/`{}`; `or []` inside. |
| 3 | Type annotations at boundaries | LOW violation — `orbital_scope: Any | None` lacks the required "why Any" comment. Non-blocking (see [TYPE]). |
| 4 | Logging coverage/correctness | PASS — observability via `emit_course_compute` span; no error path added. |
| 5 | Path handling | N/A (no paths). |
| 6 | Test quality | PASS (see [TEST]). |
| 7 | Resource leaks | N/A (no files/connections). |
| 8 | Unsafe deserialization | N/A. |
| 9 | Async pitfalls | PASS — new code is sync param-passing inside the async pre-pass; no blocking calls, no missing awaits. |
| 10 | Import hygiene | PASS — lazy in-function imports (mirror narrator, avoid circular); no star imports; pyright 0 errors. `_bodies_in_scope` underscore cross-module import has precedent (orchestrator.py:2816). |
| 11 | Input validation at boundaries | PASS — [SEC] confirmed authored-content-only, allowlist-gated. |
| 12 | Dependency hygiene | N/A (no deps changed). |
| 13 | Fix-introduced regressions | PASS — the one regression (stale movement mock) was caught by full-suite run and fixed; verified 8 other failures pre-existing via stash. |

### Devil's Advocate

Let me argue this code is broken. **Attack 1 — the scope footgun is a real inert-path regression.** The story exists because a subsystem was silently unreachable; my strongest case is that the `else Scope.system_root()` default reintroduces exactly that. A future dev adds a scene/opening that calls `execute_intent_router_pre_narrator_pass(orbital_content=world, ...)` and forgets `orbital_scope`. Now the router sees the wrong in-scope set, a drilled-in local body is missing from `<courses>`, the router (told "Do NOT invent course_ids") declines a legitimate "take us to the inner moon," and the burn goes back to narrator improv — the exact SWN-ORBITAL-COURSE-INERT symptom, silent, no span field flagging the defaulted scope. **Rebuttal:** unreachable via the sole production caller by construction (proven: orbital_scope None ⟹ orbital_content None ⟹ block gated off), and it reproduces the Session's own default — so it is a latent maintainability footgun (LOW), not a live bug; I've routed a hardening Delivery Finding rather than let it slip undocumented. **Attack 2 — a confused caller passes a genre snapshot with `party_body_id` set but no orbital tier.** Then `orbital_content is None` → block skipped → correct. No break. **Attack 3 — a malicious world author stuffs a prompt-injection payload into a body id/label.** Refuted by [SEC]: `label_hint` is hardcoded None and only allowlist-validated `orbits.bodies` keys render; a crafted id that isn't an authored key is dropped. **Attack 4 — the double course.compute emit corrupts the GM panel.** No — two honest emits (one per prompt assembly that includes the block); worst case is a counting ambiguity, not corruption. **Attack 5 — huge world balloons the prompt.** Capped at 12 entries. **Conclusion:** the only substantive attack (the scope footgun) is unreachable in production; nothing here ships a broken player experience. The doctrine concern is real, documented, and routed as a fast-follow, not dismissed.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `_build_state_summary` (`sidequest/server/intent_router_pass.py:361`) does not receive `orbital_content` — its signature is `(snapshot, *, pack, dungeon_store, palette, acting_player)`. The pre-pass already accepts `orbital_content` (line 882) and threads it into the bank context (line 1139) but does NOT pass it to the summary builder (call site line 917). Affects `sidequest/server/intent_router_pass.py` (the GREEN fix must thread `orbital_content` into `_build_state_summary`, or assemble the `<courses>` block in the pre-pass between the builder call and `decompose`, reusing `compute_courses` + `format_courses_block`). *Found by TEA during test design.*
- **Question** (non-blocking): the story flags a possible *separate* `actor_location_unresolved` / unresolved `party_location` issue at the coyote_star cockpit ("worth a glance … not what starves the course trigger"). Confirmed the pre-pass logs `projection_skipped reason=actor_location_unresolved` for a party-anchored-but-roomless snapshot (expected pass-through per `intent_router_pass.py:436-437`, not a courses-block starve). Not in 158-50 scope; noting so Dev/Reviewer don't conflate the two. Affects `sidequest/server/intent_router_pass.py` (no change required for 158-50). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `develop` currently carries ~8 pre-existing test failures unrelated to 158-50 (verified by stashing this story's changes and re-running). They belong to other stories/debt: dogfight content loading (`test_dogfight_has_dual_track_metrics`, `test_dogfight_beats_cover_every_consumed_maneuver` — 158-49), `test_sealed_letter_empty_npcs_present_raises_without_consuming_fallback` (158-34 frame-default debt), `test_wwn_scene_harness_fixture_proof` cast charges (158-53), `test_102_7_mutant_wasteland_mutations_live`, and two `beneath_sunden` content tests (`creature_images`/`room_binding`, 107-2). Affects those stories' scopes (not this one) — flagging so the base-branch red isn't mistaken for a 158-50 regression. *Found by Dev during implementation.*
- **Improvement** (non-blocking): monkeypatched `_build_state_summary` stubs with fixed signatures re-break on every added param (bit `acting_player` @153-22, then this story's three). Fixed the one in `test_movement_dispatch.py` to `**kwargs`; other call sites should follow the same pattern. Affects `tests/**` (grep `monkeypatch.setattr(..., "_build_state_summary"`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the `else Scope.system_root()` scope default (`intent_router_pass.py:724`) is unreachable in production today but a latent No-Silent-Fallbacks footgun for any future/test caller that threads `orbital_content` without `orbital_scope`. Harden by failing loud (assert/raise `orbital_scope is not None` when `orbital_content is not None`) AND threading `orbital_scope` in `test_course_router_summary_wiring.py`'s `_snap()` fixture to gain real scope-propagation coverage (currently zero). Affects `sidequest/server/intent_router_pass.py` + the story's test file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `_session is None` cascade (`websocket_session_handler.py:1010-1017`) silently collapses "no room/session" into "no orbital tier," whereas `ws_handler.py:1209-1214` raises `RuntimeError` for the analogous unexpectedly-None `sd._room`. Pre-existing from Story 153-5 (`_orbital_content` line); consider failing loud consistently. Affects `sidequest/server/websocket_session_handler.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `orbital_scope: Any | None` should be `Scope | None` under a `TYPE_CHECKING` import (as `OrbitalContent` already is) to satisfy python.md rule #3 and drop the bare `Any`. Affects `sidequest/server/intent_router_pass.py`. *Found by Reviewer during code review.*
- **Question** (non-blocking): `Session.note_body_mentioned()` (`session.py:146`, the only writer of `_recent_body_mentions`) is never called in production (repo-wide grep, per the security subagent) — so the `recent_body_mentions` course-source is dead for BOTH the narrator and this new router path; only in-scope + quest-anchor bodies surface. Not a 158-50 regression, but worth wiring if "recently mentioned" is meant to weight travel vocabulary. Affects `sidequest/server/session.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `emit_course_compute` now fires twice per orbital turn (router pre-pass + narrator) with no phase/source attribute to distinguish them, and `dropped_by_cap=0` is hardcoded at both sites. Consider a `source`/`phase` span attribute and a real dropped-by-cap count. Affects `sidequest/telemetry/spans/course.py` + both call sites. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 0 Conflict, 1 Question, 1 Improvement)
**Blocking:** None

- **Gap:** `_build_state_summary` (`sidequest/server/intent_router_pass.py:361`) does not receive `orbital_content` — its signature is `(snapshot, *, pack, dungeon_store, palette, acting_player)`. The pre-pass already accepts `orbital_content` (line 882) and threads it into the bank context (line 1139) but does NOT pass it to the summary builder (call site line 917). Affects `sidequest/server/intent_router_pass.py`.
- **Question:** the story flags a possible *separate* `actor_location_unresolved` / unresolved `party_location` issue at the coyote_star cockpit ("worth a glance … not what starves the course trigger"). Confirmed the pre-pass logs `projection_skipped reason=actor_location_unresolved` for a party-anchored-but-roomless snapshot (expected pass-through per `intent_router_pass.py:436-437`, not a courses-block starve). Not in 158-50 scope; noting so Dev/Reviewer don't conflate the two. Affects `sidequest/server/intent_router_pass.py`.
- **Improvement:** monkeypatched `_build_state_summary` stubs with fixed signatures re-break on every added param (bit `acting_player` @153-22, then this story's three). Fixed the one in `test_movement_dispatch.py` to `**kwargs`; other call sites should follow the same pattern. Affects `tests/**`.

### Downstream Effects

Cross-module impact: 3 findings across 2 modules

- **`sidequest/server`** — 2 findings
- **`tests`** — 1 finding

### Deviation Justifications

4 deviations

- **AC-5 covered by existing green tests, not re-tested**
  - Rationale: 158-50 does not change the watcher; duplicating existing green coverage adds maintenance cost without new signal (avoid the redundant-parametrized-path smell in python.md #6).
  - Severity: minor
  - Forward impact: none (Reviewer can confirm the witness is unchanged)
- **Router classification modeled by a contract double, not a live LLM**
  - Rationale: A live intent-router pass is flaky/content-coupled (`feedback_no_content_coupled_tests`); this is the same STUBBED-router discipline the green 153-5 suite established. The double faithfully encodes the production gate, so it flips red→green on exactly the summary-block fix. The OTEL span assertion (not a source grep) still satisfies the AC's wiring-proof requirement.
  - Severity: minor
- **Threaded two extra Session inputs beyond the `orbital_content` the story named**
  - Rationale: The story says "reuse compute_courses" — which REQUIRES `in_scope_body_ids` + `recent_body_mentions` + `quest_anchors` as inputs. Only `quest_anchors` is on the snapshot; the other two are Session-scoped (like `orbital_content`). Omitting them yields a quest-anchors-only block that leaves in-scope travel (the actual "burn for The Horn" playtest case) inert — a half-fix (server CLAUDE.md "No half-wired features"). This makes the router block === the narrator block.
  - Severity: minor
  - Forward impact: none — additive keyword-only params with defaults; 153-5's reflection check on the pre-pass signature stays green.
- **Modified a sibling test's monkeypatch stub**
  - Rationale: My added `_build_state_summary` params made the pre-pass pass kwargs the fixed-signature stub rejected (TypeError). The stub only bypasses pack-touching logic and returns a placeholder; `**kwargs` keeps it in sync without weakening any assertion (still asserts the PC moved + `movement.resolved` span).
  - Severity: minor

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-5 covered by existing green tests, not re-tested**
  - Spec source: context-story-158-50.md, AC-5
  - Spec text: "The dispatch_engagement.course.mismatch lie-detector fires when the narrator prose claims a transit but no course dispatch backed it"
  - Implementation: No new test written for AC-5; the `course` engagement witness is already registered and its mismatch/no-mismatch behavior is green in `test_course_clock_dispatch_wiring.py` (`test_course_witness_registered`, `test_watcher_flags_course_dispatch_that_did_not_plot`, `test_watcher_silent_when_course_committed`) plus `tests/agents/test_dispatch_engagement_watcher.py`.
  - Rationale: 158-50 does not change the watcher; duplicating existing green coverage adds maintenance cost without new signal (avoid the redundant-parametrized-path smell in python.md #6).
  - Severity: minor
  - Forward impact: none (Reviewer can confirm the witness is unchanged)
- **Router classification modeled by a contract double, not a live LLM**
  - Spec source: context-story-158-50.md, AC-1
  - Spec text: "a natural-language travel-to-named-body action in an orbital world produces a 'course' SubsystemDispatch and run_course_dispatch fires — assert a course.plot span emits"
  - Implementation: The router's emit decision is driven by `_courses_gated_router`, a double that emits `course` iff the summary it is handed contains a `<courses>` block — the exact rule `intent_router.py:292` encodes — rather than invoking the live Haiku router on the NL string.
  - Rationale: A live intent-router pass is flaky/content-coupled (`feedback_no_content_coupled_tests`); this is the same STUBBED-router discipline the green 153-5 suite established. The double faithfully encodes the production gate, so it flips red→green on exactly the summary-block fix. The OTEL span assertion (not a source grep) still satisfies the AC's wiring-proof requirement.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Threaded two extra Session inputs beyond the `orbital_content` the story named**
  - Spec source: context-story-158-50.md, Fix Direction
  - Spec text: "assemble a `<courses>`/orbital-tier block into the router's state summary in intent_router_pass.py … gated on the world having an orbital tier (session.orbital_content present)"
  - Implementation: Also added `orbital_scope` + `recent_body_mentions` kwargs to `execute_intent_router_pre_narrator_pass` (threaded from the Session) and into `_build_state_summary`, not just `orbital_content`.
  - Rationale: The story says "reuse compute_courses" — which REQUIRES `in_scope_body_ids` + `recent_body_mentions` + `quest_anchors` as inputs. Only `quest_anchors` is on the snapshot; the other two are Session-scoped (like `orbital_content`). Omitting them yields a quest-anchors-only block that leaves in-scope travel (the actual "burn for The Horn" playtest case) inert — a half-fix (server CLAUDE.md "No half-wired features"). This makes the router block === the narrator block.
  - Severity: minor
  - Forward impact: none — additive keyword-only params with defaults; 153-5's reflection check on the pre-pass signature stays green.
- **Modified a sibling test's monkeypatch stub**
  - Spec source: the tests TEA wrote + existing suite
  - Spec text: (implicit) production changes must not break green tests
  - Implementation: Changed `test_movement_dispatch.py::test_wiring_intent_router_pass_threads_context`'s `_build_state_summary` stub from a fixed-signature lambda to `lambda snapshot, **kwargs: "summary"`.
  - Rationale: My added `_build_state_summary` params made the pre-pass pass kwargs the fixed-signature stub rejected (TypeError). The stub only bypasses pack-touching logic and returns a placeholder; `**kwargs` keeps it in sync without weakening any assertion (still asserts the PC moved + `movement.resolved` span).
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: AC-5 covered by existing green tests, not re-tested** → ✓ ACCEPTED by Reviewer: 158-50 does not touch the engagement watcher; the `course` witness + mismatch behavior are already green in `test_course_clock_dispatch_wiring.py` (verified those three tests exist and pass in the preflight run). Re-testing unchanged behavior would be the redundant-path smell. Sound.
- **TEA: Router classification modeled by a contract double, not a live LLM** → ✓ ACCEPTED by Reviewer: mandatory — a live Haiku pass is non-deterministic/content-coupled (`feedback_no_content_coupled_tests`), the same discipline the green 153-5 suite established. The `_courses_gated_router` double faithfully encodes `intent_router.py:292`'s own gate, so it flips red→green on exactly the summary-block fix; the OTEL span assertion (not a source grep) satisfies the wiring-proof requirement. The one gap this leaves (no coverage of *correct scope propagation*) is captured in my Delivery Finding on the scope default.
- **Dev: Threaded two extra Session inputs beyond the `orbital_content` the story named** → ✓ ACCEPTED by Reviewer: correct and required, not scope creep. "Reuse compute_courses" mandates supplying its `in_scope_body_ids`/`recent_body_mentions`/`quest_anchors` inputs; a quest-anchors-only block would leave in-scope travel (the reported "The Horn" case) inert — the half-fix the server CLAUDE.md forbids. The additive keyword-only params keep 153-5's signature-reflection check green. Makes the router block === the narrator block.
- **Dev: Modified a sibling test's monkeypatch stub** → ✓ ACCEPTED by Reviewer: the fixed-signature stub legitimately broke on the new params (a real TypeError, caught by the full-suite run); `lambda snapshot, **kwargs: "summary"` is the correct future-proof sync and weakens no assertion (the test still asserts `pc_regions["Rux"] == "b"` + the `movement.resolved` span). This is a mock-sync fix, not a spec deviation of substance.
- **UNDOCUMENTED (Reviewer-spotted):** the diff includes an incidental `ruff format` collapse of an unrelated 3-line list-comp to one line at `intent_router_pass.py:269` (`force_dispatch_dogfight_on_verb_miss`) — outside 158-50's scope. Severity: LOW. ACCEPTED: the collapsed form is 99 chars (< the 100 line-length limit), i.e. formatter-mandated; develop carried stale formatting there. Reverting it would fail `ruff format --check`, so keeping it is correct. Noted for diff-hygiene awareness only.