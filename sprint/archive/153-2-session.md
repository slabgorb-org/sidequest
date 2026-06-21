---
story_id: "153-2"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-2: [SWN-OPENING-ESTABLISHING-NARRATION-DROPPED] emit authored establishing_narration verbatim at cold-open

## Story Details
- **ID:** 153-2
- **Jira Key:** (none — jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p2

## Background & Root-Cause Direction

**Finding (from sq-playtest ping-pong board):** In the SWN space_opera worlds (aureate_span / coyote_star / perseus_cloud), the world's authored `establishing_narration` (a field on the unified Opening schema) is being DROPPED at cold-open instead of being emitted verbatim. Players start without the authored scene-setting prose.

**Root-cause direction:** The server's opening-emission path is not surfacing the authored `establishing_narration` verbatim at session cold-open for these worlds. Fix lives server-side in the opening/cold-open emission code path.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T12:37:05Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T11:54:23Z | 2026-06-21T11:54:23Z | - |
| red | 2026-06-21T11:54:23Z | 2026-06-21T12:22:05Z | 27m 42s |
| green | 2026-06-21T12:22:05Z | 2026-06-21T12:29:29Z | 7m 24s |
| review | 2026-06-21T12:29:29Z | 2026-06-21T12:37:05Z | 7m 36s |
| finish | 2026-06-21T12:37:05Z | - | - |

## Delivery Findings

<!-- agents append below; never edit another agent's entries -->

### TEA (test design)
- **Gap** (non-blocking): once `establishing_narration` is emitted verbatim, the narrator must STOP re-narrating it or the player reads the scene twice. The directive still says "ESTABLISHING NARRATION (play this scene):". Affects `sidequest/server/dispatch/opening.py` (`_render_directive_location` / `_render_directive_chassis`) — change the directive to "already shown verbatim; narrate forward from it", mirroring the existing `opening_seed_shown` mechanism for the invitation. *Found by TEA during test design.*
- **Question** (non-blocking): MP parity — the verbatim establishing frame should ride the same `_cold_open_author` / `visibility_sidecar` rules as the existing seed cold-open frame in `_run_opening_turn_narration` (solo → private author-anchored sidecar; MP → broadcast), and respect the MP-joiner suppression. The RED tests cover the SOLO path only. Affects `sidequest/server/websocket_session_handler.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): test-isolation leak — a dungeon materializer writes `worlds/beneath_sunden/rooms/exp001.r*.yaml` into the SHARED `tests/fixtures/packs/test_genre/` tree, which makes `test_genre` fail to load (missing `beneath_sunden/world.yaml`) and breaks both these RED tests and `test_lore_seeding_dispatch.py`. TEA removed the untracked cruft to reach RED; it will recur on any full-suite run that exercises that dungeon test. Affects fixture isolation (materializer should write to tmp, not the fixture source tree). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the test-isolation leak TEA flagged (Finding 3) is real and confirmed — a dungeon materializer writes `worlds/beneath_sunden/rooms/exp001.r*.yaml` into the SHARED `tests/fixtures/packs/test_genre/` source tree, breaking `test_genre` pack load. It is OUT OF SCOPE for this server story (the leak lives in the materializer's output-dir resolution, not the opening path). Dev re-removed the untracked cruft; it will recur on any full-suite run that exercises that dungeon test. Affects `sidequest/dungeon/materializer.py` (should write to a session/tmp dir, not the genre-pack source tree). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): the directive text now ships `"Story 153-2: ..."` inside the narrator-facing prompt string in `sidequest/server/dispatch/opening.py` (both render paths). A story-ID is internal tracking and is noise in a permanent runtime prompt the LLM reads every cold-open — drop the `Story 153-2: ` prefix (keep the instruction). Trivial follow-up. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `Opening.establishing_narration` (and `first_turn_invitation`) have no non-blank validator (`genre/models/narrative.py` — only `_no_placeholder_text`). A blank-string authoring mistake would silently drop at the cold-open truthiness gate (or, if whitespace-only, raise at `NonBlankString`). Pre-existing model gap that the existing `opening_seed` path shares; add a non-blank validator so a hollow opening fails loud at pack-load. Affects `sidequest/genre/models/narrative.py`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- No deviations from spec. The sprint YAML carried no description or ACs (spec = the story title); ACs were defined during the RED phase as the tdd workflow requires. The `establishing_narration_emitted` watcher-event name + `establishing_len` field + `severity="info"` (AC3) are TEA-defined contracts, chosen to mirror the existing `cold_open_emitted` event. AC4 is a green-by-design forward-guard (no establishing is emitted pre-fix, so it passes today) — it locks the no-opening negative path so the fix can't leak a stray/empty establishing frame.

### Dev (implementation)
- No deviations from spec. Implemented exactly per TEA's contract; additionally addressed the two non-blocking TEA findings (Finding 1 directive no-re-narration; Finding 2 MP parity) as part of completing the fix coherently — establishing rides the same `cold_open_messages` list as the seed, so it inherits the seed's `_cold_open_author`/`visibility_sidecar` MP rules and the MP-joiner suppression for free.

### Reviewer (audit)
- **TEA "No deviations from spec"** → ✓ ACCEPTED by Reviewer: the YAML carried no ACs; defining them at RED is the workflow's intent. The `establishing_narration_emitted` / `establishing_len` / `severity=info` contract is sound and mirrors `cold_open_emitted`.
- **Dev "No deviations from spec"** → ✓ ACCEPTED by Reviewer: implementation matches TEA's contract exactly; addressing the two non-blocking findings (no-re-narration directive, MP parity) is completing the fix, not a deviation. Verified MP parity independently (emission loop applies one sidecar/author to all `cold_open_messages`).
- No undocumented deviations found.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 minor smells | confirmed 1 (LOW story-id prompt noise), dismissed 1 (dual-site directive — pre-existing symmetric pattern) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium) | confirmed 1 as LOW (missing non-blank validator — pre-existing model gap, matches seed pattern, not introduced here) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A — verified perception-firewall/MP-suppression/injection all clean |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via settings, pre-filled as Skipped)
**Total findings:** 2 confirmed (both LOW, non-blocking), 1 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The change is surgical, pattern-consistent, fully tested, and MP-safe. It fixes the bug ([SWN-OPENING-ESTABLISHING-NARRATION-DROPPED]) by emitting the authored `establishing_narration` verbatim at cold-open instead of relying on the narrator (which dropped it), and addresses the two coherence findings TEA raised. No Critical/High issues. The two confirmed findings are both LOW/non-blocking cleanups recorded as Delivery Findings.

**Observations (≥5):**
- [VERIFIED] MP perception firewall (ADR-104/105) holds — `websocket_session_handler.py:3114-3123` applies one `_cold_open_sidecar`/`_cold_open_author` to ALL `cold_open_messages`, so the new establishing frame inherits the seed's per-recipient visibility (solo: `visible_to=[author]`, `pov_strategy=private`; MP: broadcast). Independently confirmed + `[SEC]` clean.
- [VERIFIED] MP-joiner suppression — `opening_establishing_narration` is cleared in the consume-time suppression block (`websocket_session_handler.py:2908`) and the field defaults to `None` for a joiner's `_SessionData`; a suppressed joiner cannot receive the host's authored scene. `[SEC]` confirmed two independent gates.
- [VERIFIED] Wiring — AC1 drives the real `_populate_opening_directive_on_chargen_complete` → `_run_opening_turn_narration` path end-to-end; `[PREFLIGHT]` tests 4/4 GREEN, ruff check + format clean.
- [VERIFIED] OTEL — `establishing_narration_emitted` (component `opening_hook`, severity `info`, `establishing_len`) mirrors `cold_open_emitted`, satisfying the CLAUDE.md OTEL Observability Principle (GM-panel lie-detector).
- [VERIFIED] Ordering — establishing is prepended to `cold_open_messages` before the seed, so the player reads the scene-set then the invitation (AC2). Emission order preserved by the list comprehension.
- [LOW][SIMPLE] `dispatch/opening.py` bakes `"Story 153-2: "` into the narrator-facing directive prompt (both render paths) — internal tracking noise in a permanent runtime prompt. `[PREFLIGHT]` smell confirmed. Non-blocking; recorded as Delivery Finding.
- [LOW][SILENT] `Opening.establishing_narration` has no non-blank validator — an empty-string authoring mistake silently drops (whitespace-only would raise at `NonBlankString`). Pre-existing model gap shared by the `opening_seed` path; not introduced here. Non-blocking; recorded as Delivery Finding.
- [TEST] Test quality verified by Reviewer (analyzer disabled): assertions check specific marker substrings / ordering indices / event name + `establishing_len` + `severity`; watcher spy patches `websocket_session_handler._watcher_publish` (where used); AC4 is an honest green forward-guard. No vacuous assertions.
- [DOC] Comments verified by Reviewer (analyzer disabled): new comments are accurate and reference the story + the bug; the only doc issue is the story-id in the runtime prompt (above).
- [TYPE] Type design verified by Reviewer (type-design disabled): `opening_establishing_narration: str | None = None` mirrors `opening_seed`/`opening_directive` exactly — consistent, no stringly-typed regression.
- [RULE] lang-review compliance verified by Reviewer (rule-checker disabled): #4 log-level — success event is `info` (correct); no mutable defaults, no bare excepts, no unsafe deserialization, no path issues in the diff.

### Rule Compliance

- **No Silent Fallbacks (CLAUDE.md):** the cold-open `if sd.opening_establishing_narration:` gate is a correct None-guard (no opening resolved → silent by design, no fabricated frame). The one gap (blank-string authoring) is a pre-existing model-validation hole, not a new silent fallback in the emit path — downgraded to LOW, recorded. COMPLIANT (with noted hardening follow-up).
- **No Stubbing:** no placeholder/skeleton code — the field, stash, emit, and clears are all live and wired. COMPLIANT.
- **OTEL Observability Principle:** every new subsystem decision emits a span/watcher event (`establishing_narration_emitted`). COMPLIANT.
- **Perception firewall (ADR-104/105):** new player-facing NARRATION frame inherits per-recipient projection. COMPLIANT.
- **lang-review #4 (log-level):** success = info. COMPLIANT. **#6 (test quality):** meaningful assertions, correct patch target. COMPLIANT.

### Devil's Advocate

Argue this is broken. First attack: the verbatim emit could double the scene — the establishing prose is shown to the player AND still handed to the narrator in the directive, so the narrator might re-narrate it and the player reads it twice. Rebuttal: Dev changed both directive renderers (`opening.py`) to tell the narrator the scene is ALREADY shown verbatim and to continue forward — exactly to prevent this. The narrator mock can't prove the LLM obeys, but the directive is now correct; residual risk is LLM disobedience, which is a tuning concern, not a code defect. Second attack: a malicious/careless world author writes `establishing_narration: "   "` (whitespace) — `if sd.opening_establishing_narration:` is truthy, `NonBlankString("   ")` raises, and the cold-open turn crashes mid-chargen-commit. Rebuttal: real, but (a) the identical risk already exists in the seed path (`first_turn_invitation`), so this PR doesn't widen it, and (b) it fails LOUD (raises), not silently — the worse outcome (silent drop) only happens for empty-string, which produces no scene but no crash. Recorded as a LOW hardening finding. Third attack: MP race — two players commit chargen near-simultaneously; could a joiner get the host's private establishing prose? Rebuttal: the security subagent traced two independent gates (consume-time clear + populate idempotency + None default) and the emission sidecar marks solo frames `visible_to=[author]`; the joiner is excluded by both the pack VisibilityTagRule and the structural NARRATION list-gate. Fourth attack: the field leaks into a later turn (not cleared). Rebuttal: cleared in both the suppression block and the consume block, symmetric with `opening_seed`/`opening_directive`; `_SessionData` is in-memory (no resume leak). Conclusion: no defect rises above LOW.

**Data flow traced:** world YAML `establishing_narration` → `Opening` (Pydantic, validated) → `_populate_opening_directive_on_chargen_complete` stash → `sd.opening_establishing_narration` → `cold_open_messages` (prepended) → `_emit_event("NARRATION", …, sidecar, author)` → player. Safe: per-recipient projection applied; cleared on consume/suppression.
**Pattern observed:** mirrors the existing `opening_seed` cold-open emission + `cold_open_emitted` watcher — `websocket_session_handler.py:3003-3018` vs the new block at `:3009`.
**Error handling:** None-gated (correct); `NonBlankString` guards blank on emit (matches seed). No new swallow.
**Handoff:** To SM (Vizzini) for finish-story.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/session_state.py` — new `_SessionData.opening_establishing_narration: str | None` field.
- `sidequest-server/sidequest/server/websocket_handlers/opening_helpers.py` — populator stashes `opening.establishing_narration` onto session_data alongside the seed/directive.
- `sidequest-server/sidequest/server/websocket_session_handler.py` — `_run_opening_turn_narration` emits the establishing prose VERBATIM as a NARRATION cold-open frame BEFORE the seed (same `cold_open_messages` MP author/sidecar path) and publishes `establishing_narration_emitted` (component `opening_hook`, severity `info`, `establishing_len`); cleared on MP-joiner suppression and on consume.
- `sidequest-server/sidequest/server/dispatch/opening.py` — both directive renderers now tell the narrator the establishing scene is ALREADY shown verbatim (continue forward, do not repeat) so the player never reads it twice.

**Tests:** 4/4 GREEN (`tests/server/test_153_2_establishing_narration_verbatim.py`).
**Regression (blast radius):** opening/chargen/session surface — all pass except pre-existing failures confirmed on the clean tree (`test_chargen_quest_seed_wiring`, `test_scenario_bind` ×2 — all fail with my changes stashed, so not introduced here).
**Quality:** `ruff check` clean, `ruff format --check` clean, `pyright` adds 0 new errors (3 pre-existing in untouched `opening_helpers.py` lines 127/198/559, same on clean tree).
**Branch:** `feat/153-2-swn-establishing-narration` (pushed to `slabgorb-org/sidequest-server`).

**Handoff:** To Reviewer (Westley) for code review.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Server-side behavior bug — the authored `establishing_narration` is never emitted verbatim to the player; it is only handed to the narrator LLM as a directive (and the SWN narrator dropped it).

**Test Files:**
- `sidequest-server/tests/server/test_153_2_establishing_narration_verbatim.py` — 4 tests driving the REAL chargen → cold-open path against the hermetic `test_genre/flickering_reach` fixture pack, forcing a synthetic location-anchored `Opening` (aureate_span shape) whose `establishing_narration` is a unique marker.

**Tests Written:** 4 tests covering 4 ACs.
**Status:** RED — 3 fail (AC1/AC2/AC3) for the intended reason, AC4 is a green forward-guard.

Verified RED reason (not a harness error):
- AC1 emitted narration = `['AUREATE-SEED-… (the invitation/seed, emitted verbatim)', 'The world takes shape… (narrator mock)']` — the establishing marker is **absent**.
- AC3 watcher events seen include `cold_open_emitted` but **not** `establishing_narration_emitted`.

Run:
```
SIDEQUEST_TEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test \
  uv run pytest -n0 sidequest-server/tests/server/test_153_2_establishing_narration_verbatim.py
```

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------------------|---------|--------|
| #4 log-level classification (success = info, not error) | AC3 asserts the establishing emit event fires at `severity="info"` | failing (RED) |
| #6 test quality — meaningful assertions, patch where used | all 4 tests assert specific values; watcher spy patches `websocket_session_handler._watcher_publish` (where used) | n/a (self-check) |
| Wiring (CLAUDE.md "Verify Wiring, Not Just Existence") | AC1 drives the real `_populate_opening_directive_on_chargen_complete` → `_run_opening_turn_narration` path | failing (RED) |

**Rules checked:** lang-review #4 + #6 are the applicable rules for this surface; #6 enforced via self-check (no vacuous assertions, correct patch target).
**Self-check:** 0 vacuous tests. Every assertion checks a specific value (marker substring, ordering index, event name + `establishing_len` > 0 + `severity`).

### Implementation contract (for Dev — Inigo)
Server-only (`sidequest-server`). Suggested fix:
1. `opening_helpers.py::_populate_opening_directive_on_chargen_complete` — stash `opening.establishing_narration` onto `session_data` (new field, e.g. `opening_establishing_narration`) alongside `opening_seed`/`opening_directive`; add the field to `_SessionData` in `session_state.py`.
2. `websocket_session_handler.py::_run_opening_turn_narration` (~line 2999, the `if sd.opening_seed:` cold-open block) — emit the stashed establishing prose verbatim as a `NARRATION` cold-open frame **before** the seed frame, through the same `_emit_event("NARRATION", …)` path the seed uses (same author/visibility-sidecar rules), and publish `establishing_narration_emitted` (component `opening_hook`, severity `info`, `establishing_len`). Clear the field on consume alongside `opening_seed`/`opening_directive`.
3. Address the two Delivery Findings above (narrator no-redundant-narration directive change; MP parity).

**Handoff:** To Dev (Inigo Montoya) for GREEN implementation.