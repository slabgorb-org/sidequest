---
story_id: "102-3"
jira_key: ""
epic: "102"
workflow: "tdd"
---
# Story 102-3: Explicit free-play cast classified as magic_working

## Story Details
- **ID:** 102-3
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T17:24:38Z
**Round-Trip Count:** 1
**Repos:** server
**Branch:** feat/102-3-freeplay-cast-magic-working
**Jira:** (none — Jira not enabled)

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T16:04:41Z | 2026-06-10T16:06:03Z | 1m 22s |
| red | 2026-06-10T16:06:03Z | 2026-06-10T16:18:51Z | 12m 48s |
| green | 2026-06-10T16:18:51Z | 2026-06-10T17:05:24Z | 46m 33s |
| review | 2026-06-10T17:05:24Z | 2026-06-10T17:14:43Z | 9m 19s |
| red | 2026-06-10T17:14:43Z | 2026-06-10T17:18:42Z | 3m 59s |
| green | 2026-06-10T17:18:42Z | 2026-06-10T17:22:27Z | 3m 45s |
| review | 2026-06-10T17:22:27Z | 2026-06-10T17:24:38Z | 2m 11s |
| finish | 2026-06-10T17:24:38Z | - | - |

## Sm Assessment

Story 102-3 set up for TDD. p1 bug, 5 points, server repo only. The intent router
(sidequest-server/sidequest/agents/intent_router.py) never classifies an explicit
named free-play cast (e.g. "I cast foundation_of_flame") as `magic_working`, so
`resolve_spellcast` is never dispatched from a world opening — the narrator improvises
the working with no mechanical backing (no `wwn.spell.cast` span, `casts_remaining`
unchanged, no `dispatch_engagement.magic_working.mismatch`). This is the AC5b
"from a world opening" blocker (gap #3 in epic 102's FIXER investigation).

Acceptance shape: dispatch_engagement lie-detector assertion — a named cast in free
play must route to resolve_spellcast and fire `wwn.spell.cast`. Story context with
technical approach and ACs: sprint/context/context-story-102-3.md. Feature branch
feat/102-3-freeplay-cast-magic-working created in sidequest-server off develop
(verified 102-3 not already merged on origin/develop). Jira not enabled — skipped.
Next agent: TEA (red phase).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The post-turn watcher witness `_check_magic_working_engaged` reads
  only `magic_state.working_log` (ADR-126 shape) — it has no way to observe WN engagement.
  Affects `sidequest-server/sidequest/agents/dispatch_engagement_watcher.py:140` (needs a
  snapshot-readable WN engagement record; the turn-scoped-ledger pattern from 59-30's
  movement/witnessed_act witnesses is the precedent). *Found by TEA during test design.*
- **Gap** (non-blocking): The router system prompt describes `magic_working` params only as
  "a MagicWorking-shaped object" — Haiku is never told to emit the named spell. Affects
  `sidequest-server/sidequest/agents/intent_router.py:145` (prompt must instruct the router
  to carry the typed spell name, per the params["spell"] contract the RED suite pins; the
  env-gated live test `test_live_router_classifies_explicit_named_cast_as_magic_working`
  verifies this). *Found by TEA during test design.*
- **Improvement** (non-blocking): Existing test
  `test_router_pass_gates_magic_working_so_bank_raises_no_parse_error` and the fixture
  comment block (tests/agents/test_dispatch_precondition_gate.py:197-209) document the
  "gate it out and let the beat path narrate" rationale that 102-3 partially retires. The
  test stays valid post-change (its snapshot has NO characters → still no cast surface),
  but the comment block should be updated when the gate predicate changes. *Found by TEA
  during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The server suite silently depends on shell-level DB env vars —
  ~22 tests ERROR with `MissingDatabaseUrlError` instead of the conftest's loud-skip when
  `SIDEQUEST_DATABASE_URL`/`SIDEQUEST_TEST_DATABASE_URL` are unset, because they reach
  `db_config.py` without the `migrated_db` fixture's skip guard. Affects
  `sidequest-server/tests/` (route DB-touching app/forensics/lore tests through the same
  env-gated skip, or document the exports in CLAUDE.md's build commands). *Found by Dev
  during implementation.*
- **Conflict** (non-blocking): Orchestrator commit a731ec5 ("wip: preserve gap-audit
  working-tree changes", 2026-06-09) deleted `docs/api-contract.md` while CLAUDE.md and a
  server test still reference it — restored on local orchestrator main this session.
  Affects `docs/api-contract.md` (operator: verify the deletion wasn't intentional before
  pushing; if intentional, the server test `test_api_contract_aside` and CLAUDE.md must
  follow). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `road_warrior` Matatu Crews corpus `swahili.txt` is
  THIN (260 < 1000 words) across 4 slots — warns in every audit run but doesn't gate.
  Affects `sidequest-content/corpus/shared/swahili.txt` (conlang expansion pass when
  convenient). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): Cross-seat actor spoofing — `params["actor"]` is LLM-copied
  from player text and never checked against the submitting seat, so in MP a player can
  spend another character's casts (the pact-working path shares the shape). Affects
  `sidequest-server/sidequest/agents/subsystems/magic_working.py` (add a
  `player_seats`-consistency guard per the 59-30 movement pattern; consider a shared fix
  across actor-keyed subsystems). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The hermeticity tripod in `tests/server/conftest.py`
  makes env-gated LIVE opt-in tests silently impossible in that tree — R1 failed against
  a stub. Affects `sidequest-server/tests/server/conftest.py` (consider a loud guard:
  the router-factory stub could `pytest.fail` when `SIDEQUEST_VERIFY_*_LIVE` env vars
  are set, so future live tests placed there fail with a diagnosis instead of a stub
  result). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `available_ids` in the unknown-spell `data` dict and
  the existing `wwn.cast_spell_unknown` watcher payload both enumerate the full spell
  catalog server-side — fine today, but a spoiler-protected world (CLAUDE.md spoiler
  policy) would leak its catalog if either channel ever reaches a client. Affects
  `sidequest-server/sidequest/agents/subsystems/magic_working.py` (count, not IDs, if
  client exposure ever planned). *Found by Reviewer during code review.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-server, feat/102-3-freeplay-cast-magic-working):**
- `sidequest/agents/dispatch_precondition_gate.py` — WN-aware magic_working predicate
  (inert only when neither magic_state nor any PC core.spellcasting exists); gated
  magic_working also emits `dispatch_engagement.magic_working.mismatch` (AC2);
  GatedDispatch gains `dispatched_type`
- `sidequest/agents/subsystems/magic_working.py` — WN free-play cast branch: typed-name
  → catalog resolution (id or display name, fold whitespace/underscores) →
  `WwnRulesetModule.resolve_spellcast` (no target in free play) → cast receipt + narrator
  directive; unknown spell = failed-premise output, no spend; ADR-126 path untouched
- `sidequest/agents/dispatch_engagement_watcher.py` — magic_working witness accepts
  turn-scoped WN cast receipts (cast AND refused) alongside working_log
- `sidequest/game/wwn_magic.py` — `WwnCastLogEntry` model
- `sidequest/game/session.py` — `wwn_spell_cast_log` snapshot ledger
- `sidequest/server/snapshot_slimming.py` — ledger categorized `_PHASE_B_DROP_FIELDS`
  (governance gate)
- `sidequest/agents/intent_router.py` — router prompt: named casts carry
  `{actor, spell}` params, confidence HIGH

**Tests:** 9/9 story tests passing + 1 env-gated live skip (GREEN). Full server suite:
**11367 passed, 0 failed, 349 skipped** (verified twice with
SIDEQUEST_DATABASE_URL/SIDEQUEST_TEST_DATABASE_URL set, direct `uv run pytest`).
**Branch:** feat/102-3-freeplay-cast-magic-working (pushed; commits b528a54a + test-infra
fix + aa2f7db4 RED)

**Operator-directed suite repair (mid-phase scope addition):** of ~29 full-suite
failures, ~22 were environmental (DB env vars unset in the invoking shell — both
Postgres DBs exist and run; export `SIDEQUEST_DATABASE_URL` and
`SIDEQUEST_TEST_DATABASE_URL` per `just pg-up`). The 7 real ones, all fixed, zero skips:
1. `swn_test_pack` fixture lacked `bestiary.yaml` → 90-5 fail-loud pregen gate broke the
   dogfight roundtrip test (server, fixed on story branch)
2. Orphan-actors AST gate vs the ADR-092 scene harness (90-7 fixture `actors:` support)
   → scene_harness.py exempted with rationale (server, story branch)
3. `docs/api-contract.md` deleted by accident in orchestrator commit a731ec5 (wip sweep,
   2026-06-09) → restored verbatim; committed on orchestrator main —
   **operator must push** (classifier blocks)
4. `corpus/shared/evropi_sest.txt` 97 words < 200 FAIL floor → conlang agent expanded to
   1072 within attested phonotactics → **content PR #411 awaiting operator merge**
   (local content checkout left on `fix/evropi-sest-corpus-expansion` so the audit gate
   stays green until merge)

**Handoff:** To The Merovingian (Reviewer) for code review.

## TEA Assessment

**Tests Required:** Yes
**Reason:** p1 bug with span-shaped ACs — the lie-detector assertion IS the deliverable.

**Test Files:**
- `sidequest-server/tests/server/test_102_3_freeplay_cast_magic_working.py` — full RED
  suite across four seams: precondition gate, dispatch bank → WN cast spine, real
  pre-narrator pass wiring + post-turn watcher, and live router classification.

**Tests Written:** 10 tests covering 4 ACs
**Status:** RED (6 failing on the exact production gaps, 3 deliberate pinning guards
passing, 1 env-gated live test skipping) — commit `aa2f7db4` on
`feat/102-3-freeplay-cast-magic-working`. Verified with direct
`uv run pytest -n0` (per project memory: testing-runner fabricates per-test prose;
counts cross-checked by hand).

**The two production gaps the failures name:**
1. `gate_inert_dispatches` drops `magic_working` whenever `snapshot.magic_state is None`
   (every WN world) — `intent_router.dispatch.gated` fires, nothing reaches any engine.
2. Even ungated, `run_magic_working_dispatch` → `apply_magic_working` raises
   `MagicWorkingParseError`; there is no route to `WwnRulesetModule.resolve_spellcast`.

**RED→GREEN map for Agent Smith (Dev):**
| Test | Production gap it forces |
|------|--------------------------|
| `test_gate_keeps_magic_working_for_wn_caster_with_spellcasting` | Gate predicate: a PC with `core.spellcasting` is a live WN cast surface — not inert |
| `test_freeplay_named_cast_fires_wwn_spell_cast_and_spends_cast` | Bank handler WN branch: catalog resolve (`resolve_wwn_spell_catalog`) + `resolve_spellcast` + spend + narrator directive |
| `test_freeplay_cast_resolves_display_name` | Typed-name → spell_id resolution (id and display name) |
| `test_unknown_spell_name_no_spend_and_loud_evidence` | Failed premise: no spend + refused span OR mismatch span (passes today via legacy witness; guards the new path) |
| `test_zero_casts_remaining_surfaces_mechanical_refusal` | Refusal is engagement: `refused=True` span, directive, NO mismatch cry-wolf |
| `test_pass_routes_wn_freeplay_cast_to_spell_cast_span` | End-to-end wiring through the REAL pass (real gates, real bank) |
| `test_classified_but_unengageable_emits_mismatch_span` | AC2: gated-closed classification must emit `dispatch_engagement.magic_working.mismatch` with evidence |
| `test_native_genre_cast_does_not_crash_or_emit_wwn_spans` | AC3 pinning: native genre safety |
| `test_live_router_classifies_explicit_named_cast_as_magic_working` | AC4 live half: router prompt extension (opt-in: `SIDEQUEST_VERIFY_FREEPLAY_CAST_LIVE=1`) |

Param contract pinned for the WN cast dispatch: `params={"actor": <caster>, "spell":
<as the player typed it>}` — see Design Deviations. Watcher witness needs WN-readable
engagement evidence — see Delivery Findings (59-30 turn-scoped-ledger precedent).

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions (fail-loud paths) | `test_unknown_spell_name_no_spend_and_loud_evidence`, `test_classified_but_unengageable_emits_mismatch_span` | failing (by design) |
| #6 test quality (no vacuous asserts) | self-check below | pass |
| #9 async pitfalls (awaited coroutines) | all bank/pass tests use `pytest.mark.asyncio` + awaited calls | pass |
| CLAUDE.md wiring test | `test_pass_routes_wn_freeplay_cast_to_spell_cast_span` (integration marker) | failing (by design) |
| CLAUDE.md no source-text wiring | entire suite span/state-asserted | pass |
| Heavy-e2e timeout (project memory) | live test carries `@pytest.mark.timeout(120)` | pass |

**Rules checked:** 3 of 13 lang-review rules applicable to test-only changes have coverage;
the remainder (mutable defaults, resource leaks, deserialization, etc.) apply to Dev's
GREEN diff and are enforced at review.
**Self-check:** 0 vacuous tests — every test asserts specific span names, span attribute
values (`refused`, `spell_id`, `actor`, `evidence`), and exact `casts_remaining` values.

**Handoff:** To Agent Smith (Dev) for GREEN implementation.

### Red Rework (round-trip 1, Reviewer R1 + D1)

**R1 [HIGH][TEST] fixed:** the AC4 live test moved from tests/server/ (hermetic — the
autouse tripod stubs the router factory and refuses real SDK) to
`tests/agents/test_102_3_live_router_classification.py`, self-contained fixtures, plus an
isinstance tripwire that fails loud with a diagnosis if a factory stub ever intercepts it
again. A pointer comment marks the old site so it is not re-added there.

**LIVE VERIFICATION RUN (this rework):** `SIDEQUEST_VERIFY_FREEPLAY_CAST_LIVE=1
uv run pytest tests/agents/test_102_3_live_router_classification.py -n0` → **1 passed in
5.19s** — a real Haiku round-trip. Live Haiku classified "I cast foundation_of_flame at
the rust-wight blocking the gate." as `magic_working` with the spell name in params and
confidence ≥ the engagement threshold. AC4's live half is now actually verified, not
aspirational.

**D1 [LOW][DOC] fixed:** the stale magic_working fixture comment block
(test_dispatch_precondition_gate.py) rewritten to describe the post-102-3 two-surface
predicate and the gate-side mismatch emission.

Deterministic suites re-verified green (29 passed / 1 env-gated skip across the story +
gate files). Commit ce6cf360, pushed. S1/S3 (optional hardening) left for Dev's green
pass per the Reviewer's note.

### Green Rework (round-trip 1, Dev)

Applied the Reviewer's sanctioned optional hardening (commit 450a6fbe, pushed):
- **S1**: `_MAX_SPELL_REF_CHARS = 256` cap on the LLM-copied spell reference before the
  normalizer/catalog scan — over-cap returns a `spell_ref_too_long` failed premise
  (no spend, loud, no raw text echoed).
- **S3**: the `unknown_spell` directive payload no longer interpolates the player-typed
  reference (ADR-047 lane); the identity stays in `data` (never reaches the prompt —
  orchestrator forwards directives only), alongside `available_ids` for forensics.

**Tests:** seam suites 57 passed / 0 failed; FULL suite 11367 passed / 0 failed / 349
skipped (DB env set). Lint + format clean. S2 (cross-seat actor guard) remains a
recorded non-blocking delivery finding for a follow-up story, per the Reviewer's
disposition.

**Handoff:** Back to The Merovingian (Reviewer) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (81 passed/0 failed, lint+format PASS, 0 smells; 1 env-gated skip judged legitimate) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [EDGE] notes) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [SILENT] notes) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [TEST] finding R1) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [DOC] note) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [TYPE] note) |
| 7 | reviewer-security | Yes | findings | 5 (1 medium, 4 low) | confirmed 2, dismissed 2 (with rationale), deferred 1 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [SIMPLE] note) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — rule sweep self-assessed (see Rule Compliance) |

**All received:** Yes (2 enabled returned; 7 disabled via settings, domains self-assessed)
**Total findings:** 3 confirmed, 2 dismissed (with rationale), 1 deferred

## Reviewer Assessment

**Verdict:** APPROVED (round 2 re-review, 2026-06-10 — round 1 verdict REJECTED is
preserved below for the record; every blocking finding is now fixed and independently
re-verified)

### Round 2 re-review (rework delta ce6cf360 + 450a6fbe)

- **R1 [TEST] FIXED & INDEPENDENTLY VERIFIED:** live AC4 test relocated to
  `tests/agents/test_102_3_live_router_classification.py` with an isinstance tripwire
  against future factory stubs and a pointer comment at the old site. I re-ran it myself
  with the opt-in env: **1 passed in 4.50s against real Haiku** (separate from TEA's
  5.19s run — two independent live confirmations of the router-prompt contract).
- **D1 [DOC] FIXED:** the magic_working fixture comment block now describes the
  two-surface predicate and the gate-side mismatch emission (verified in delta diff).
- **S1 [SEC] FIXED per prescription:** `_MAX_SPELL_REF_CHARS = 256` cap before
  normalize/scan; over-cap is a loud `spell_ref_too_long` failed premise, no raw echo.
- **S3 [SEC] FIXED per prescription:** unknown-spell directive payload no longer
  interpolates the player-typed reference; identity rides in `data` only (verified:
  orchestrator forwards directives, not data).
- **Residual [LOW] noted, non-blocking:** the `missing_spell` / `spell_ref_too_long` /
  `no_spellcasting` payloads interpolate `actor` before it is validated against the
  roster — the same class S3 closed for spell_ref, mitigated by the same baseline (the
  raw action already enters the prompt). Fold into the S2 cross-seat follow-up, which
  reworks actor handling anyway.
- Deterministic seam suites re-verified: 57 passed / 1 env-gated skip. Full suite was
  11367/0 at Dev's green exit; no production code changed since except the reviewed
  S1/S3 delta.

### Round 1 record (original verdict: REJECTED)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [TEST] R1 — the AC4 live-classification test is structurally unrunnable | `tests/server/test_102_3_freeplay_cast_magic_working.py::test_live_router_classifies_explicit_named_cast_as_magic_working` | tests/server/conftest.py's autouse hermeticity tripod stubs `build_intent_router_for_session` (returns an EMPTY DispatchPackage) and refuses `build_async_anthropic`. With `SIDEQUEST_VERIFY_FREEPLAY_CAST_LIVE=1` + a real key the test FAILS against the stub in 0.19s (verified this review) — and a stub that emitted dispatches would false-PASS. Move the test to `tests/agents/` (the 91-3 live opt-in pattern lives there; its conftest carries no router/SDK stubs) and re-verify it reaches live Haiku. |
| [MEDIUM] [SEC] S2 — cross-seat actor spoofing | `sidequest/agents/subsystems/magic_working.py` (`_run_wn_freeplay_cast`, actor resolution) | Non-blocking (recorded as delivery finding): `params["actor"]` is LLM-copied from player text; in MP, player A's action can name player B's character and spend B's casts. Movement solved this in 59-30 by trusting `player_seats`, not the LLM field. Recommend a seat-consistency guard in a follow-up story (shared with the pact-working path, which has the same shape). |
| [LOW] [SEC] S1 — no length cap on `spell_ref` | `magic_working.py` (spell param validation) | Non-blocking: LLM-derived string flows into regex-normalize + catalog scan with no cap; O(n) only (regex verified non-backtracking), but a 256-char cap after the isinstance check is cheap hardening. May fold into rework if convenient. |
| [LOW] [SEC] S3 — raw `spell_ref!r` in narrator directive payload | `magic_working.py` (unknown_spell failed-premise payload) | Deferred: the player's raw action text already enters the narrator prompt verbatim every turn, so the repr'd substring adds little new surface — but it bypasses the ADR-047 sanitization lane. Recommend a generic payload with the identity kept in `data` (which never reaches the prompt — verified orchestrator.py:2782-2789 only forwards directives). |
| [LOW] [DOC] D1 — stale rationale comment block | `tests/agents/test_dispatch_precondition_gate.py:197-209` | Non-blocking: the burning_peace "gate it out, narrate via beat path" comment now describes retired doctrine for WN-caster worlds. TEA flagged it in red; Dev did not update. Fold into rework. |

**Dismissed (with rationale):**
- [SEC] S4 `available_ids` in failed-premise `data` — DISMISSED: `SubsystemOutput.data`
  never reaches the narrator prompt or the client (orchestrator.py:2782-2789 forwards
  only visibility-filtered directives), and the existing beat-path miss event
  (`wwn.cast_spell_unknown`, narration_apply.py:311-321) already carries `available_ids`
  server-side — same precedent, same audience (GM/dev). Spoiler-world caveat recorded as
  a non-blocking delivery finding.
- [SEC] S5 unbounded `wwn_spell_cast_log` — DISMISSED: deliberately mirrors the uncapped
  `region_transitions` ledger (the model comment cites it); growth is one row per cast at
  human play rate, and the prompt is protected by the Phase-B drop. A rolling cap across
  BOTH ledgers is a future improvement, not a 102-3 defect.

**Verified good (with evidence and rule cross-check):**
- [VERIFIED] Receipt-turn vs watcher-turn ordering is correct: the watcher runs at
  websocket_session_handler.py:1113, `record_interaction()` bumps at :1224 — receipt
  (stamped pre-narrator at interaction=N) and witness read (also N) are on the same side
  of the bump, exactly like the witnessed_act/movement witnesses. Complies with the
  59-30 turn-scoped-ledger pattern. (I suspected a cry-wolf here; the code refutes it.)
- [VERIFIED] [TYPE] `isinstance(module, WwnRulesetModule)` scopes the cast spine to wwn
  only: class hierarchy is Wwn(Swn), Cwn(Swn), Awn(Cwn) — swn/cwn/awn packs fall through
  to the loud legacy path. Complies with ADR-117 capability-binding ("isinstance against
  module classes, never genre slug") and keeps psionics for 102-6.
- [VERIFIED] [SILENT] No silent fallbacks in the new paths: every failed premise returns
  an error-coded output WITH a must_narrate directive (magic_working.py `_failed_premise`),
  the no-WN/no-magic_state fallthrough still raises `MagicWorkingParseError`, and a
  wwn-pack-without-wwn-config crashes loudly into the bank's error span
  (`resolve_spellcast` cfg guard, wwn.py:496-497). Complies with CLAUDE.md No Silent
  Fallbacks.
- [VERIFIED] [EDGE] Boundary sweep: 0 casts → refused-no-spend (engine answers, no
  mismatch — test-pinned); unprepared-but-cataloged spell → spine refusal "not prepared"
  (wwn.py:527); display-name and id both resolve via `_norm_spell_name` (character-class
  regex, non-backtracking); no-encounter free play passes `target_core=None` which the
  spine's no-target contract spends correctly (wwn.py:494 docstring); coyote_star
  (magic_state populated) keeps the ADR-126 path (handler branches on magic_state first);
  no-surface worlds stay gated (pinned by both old and new gate tests).
- [VERIFIED] [SIMPLE] No dead code introduced; `_GATE_DISPATCHED_TYPE_KEY` carries
  scenario_clue/witnessed_act entries whose dispatched_type is currently only consumed
  for magic_working spans — populated-but-cheap, acceptable forward generality, not
  over-engineering.
- [VERIFIED] MP perception: the handler's directives carry `dispatch.visibility` and the
  orchestrator filters on `redact_from_narrator_canonical` (orchestrator.py:2782-2787) —
  complies with ADR-105 broadcast-layer firewall.

**Data flow traced:** player free text "I cast foundation_of_flame" → WS →
`execute_intent_router_pre_narrator_pass` → Haiku decompose (UNTRUSTED params) →
unregistered gate (registered: passes) → precondition gate (WN surface: passes) →
`run_dispatch_bank` → `run_magic_working_dispatch` WN branch → catalog resolve
(world-first, genre fallback) → `resolve_spellcast` (validates prepared/casts/level
BEFORE spending; spends exactly one) → turn-stamped receipt → visibility-filtered
directive → narrator prompt. Post-narration watcher reads the same package + snapshot →
receipt found → silent; no receipt → mismatch span. Safe because every params read is
isinstance-guarded, the spend is gated behind the spine's own validation, and both miss
shapes emit GM-panel spans.

**Pattern observed:** reuse-first done right — the third entry point into the SAME
`resolve_spellcast` spine (after apply_beat and 102-2's dice path), zero new cast
implementation (magic_working.py:188-196 calls the existing module method).

**Error handling:** unknown spell / missing actor / no catalog / no spellcasting each
produce an explicit failed-premise directive + error-coded data (magic_working.py
`_failed_premise`), and bank-level exceptions land in `result.errors` + error span
(subsystems/__init__.py:345-352). Nothing swallowed.

### Rule Compliance

Python lang-review checklist (.pennyfarthing/gates/lang-review/python.md) against every
changed production file (magic_working.py, dispatch_precondition_gate.py,
dispatch_engagement_watcher.py, intent_router.py, session.py, wwn_magic.py,
snapshot_slimming.py):

| # | Rule | Result |
|---|------|--------|
| 1 | Silent exceptions | COMPLIANT — no new try/except; failed premises are explicit returns; legacy raise preserved |
| 2 | Mutable defaults | COMPLIANT — no mutable defaults in any new signature; pydantic `default_factory=list` for the ledger |
| 3 | Type annotations | COMPLIANT — public seams annotated; `pack: Any` documented (duck-typed test packs, established handler idiom) |
| 4 | Logging coverage/levels | COMPLIANT-WITH-NOTE — new failure paths emit no logger call, but every one is recorded on the bank's subsystem span (`error` attr) and as a must_narrate directive; OTEL is this repo's primary observability channel (CLAUDE.md OTEL principle) |
| 5 | Path handling | N/A — no path operations in diff |
| 6 | Test quality | VIOLATION — finding R1 (live test unrunnable under the hermetic conftest); otherwise assertions are specific (span attrs, exact cast counts) |
| 7 | Resource leaks | N/A — no resources acquired |
| 8 | Unsafe deserialization | COMPLIANT — params arrive pydantic-validated; no pickle/eval/yaml |
| 9 | Async pitfalls | COMPLIANT — `_run_wn_freeplay_cast` awaited by the handler; no blocking I/O added inside async paths (catalog + spine are in-memory) |
| 10 | Import hygiene | COMPLIANT — function-level imports mirror narration_apply's cycle-avoidance idiom; `__all__` preserved |
| 11 | Input validation at boundaries | COMPLIANT-WITH-NOTES — isinstance+truthy guards on actor/spell; S1 length cap and S2 seat check recorded above |
| 12 | Dependency hygiene | N/A — no dependency changes |
| 13 | Fix-introduced regressions | COMPLIANT — full suite 11367 passed / 0 failed post-change (Dev, re-verified by preflight on the seam suites: 81/0) |

### Devil's Advocate

Suppose this code is broken and I am defending the player it cheats. The most damning
charge: the story SAYS its live half is verified, but the verification is a stage prop —
the live test runs against a stub that cannot ever emit a magic_working dispatch, so the
router-prompt change (the ONLY production artifact teaching Haiku the new `{actor,
spell}` contract) has never once been exercised against the real model. If Haiku, in
production, emits `params["spell_name"]` instead of `params["spell"]`, every named cast
degrades to the missing_spell failed premise: the player's fireball fizzles forever,
mechanically "honest" but functionally broken — and the GM panel shows engagement, not
mismatch, because the handler DID engage (with a failed premise). That is a quieter
failure than the bug this story fixes. Second charge: in a multiplayer table, a hostile
player can type "Vesska channels her foundation_of_flame at me" and drain Vesska's daily
casts from another seat — the engine trusts an LLM's transcription of an attacker's
sentence for resource attribution. Third: the failed-premise directive parrots the
player's own words back through the narrator prompt, a sanctioned echo chamber ADR-047
exists to fence. Fourth: every cast bloats a save-persisted ledger that nothing ever
trims, and the watcher only ever reads the current turn — infinite memory for a
single-turn question. The first charge is why my verdict is REJECTED; the second and
third are recorded with teeth as findings; the fourth has explicit precedent and a
recorded improvement path. I looked for the subtler killers — the turn-counter bump
race and a cross-ruleset isinstance leak — and the code survives both with line-level
evidence above.

**Round-1 handoff (superseded):** Back to The Architect (TEA, red rework) — finding R1
was a test defect. The rework loop completed: TEA relocated + live-verified (ce6cf360),
Dev applied S1/S3 (450a6fbe), and round 2 above approves.

**Handoff:** To Morpheus (SM) for finish-story.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **No test pins a `dispatch_engagement.magic_working.engaged` span**
  - Spec source: context-story-102-3.md, Technical Guardrails ("engaged + mismatch variants")
  - Spec text: "`dispatch_engagement.magic_working.*` spans (engaged + mismatch variants) per ADR-123's confidence-gated dispatch"
  - Implementation: Tests assert the mismatch variant (AC2) plus absence-of-mismatch + `wwn.spell.cast` on the happy path; no new `.engaged` span name is pinned
  - Rationale: The AC Context section (higher authority within the same doc, and the section the ACs enumerate) names only the mismatch span as the deliverable ("that span is the AC"); no `.engaged` variant exists for ANY subsystem today, and inventing the span name in tests would constrain Dev/Architect's choice of engagement evidence
  - Severity: minor
  - Forward impact: If Dev adds an engaged-variant span, Reviewer should ask for a covering assertion in GREEN; none of the RED tests will conflict with it
- **Param contract pinned as `params={"actor", "spell"}` for WN casts**
  - Spec source: context-story-102-3.md, Technical Guardrails (spell-name resolution)
  - Spec text: "the typed name ('foundation_of_flame', 'Foundation of Flame') must resolve against the caster's prepared/known spells" — no param key named
  - Implementation: RED suite fixes the dispatch param contract to `params["actor"]` + `params["spell"]` (the spell as the player typed it)
  - Rationale: The router prompt's existing "MagicWorking-shaped object" has no spell field; a concrete key is required for tests to be writable, and `actor` mirrors the existing watcher's `_DISPATCHED_TYPE_KEY["magic_working"]`
  - Severity: minor
  - Forward impact: Dev's router-prompt extension and handler must read these keys (or Dev renegotiates the contract by amending the RED tests with a logged deviation)

### Dev (implementation)
- **AC2 mismatch span emitted from the gate wrapper, not the watcher**
  - Spec source: context-story-102-3.md, AC-2
  - Spec text: "If classification succeeds but dispatch cannot engage (precondition/unregistered gate), `dispatch_engagement.magic_working.mismatch` is emitted with reason attributes"
  - Implementation: `run_dispatch_precondition_gate` emits the mismatch span alongside `intent_router.dispatch.gated` when it drops a magic_working dispatch (the gate strips the dispatch from the package, so the post-turn watcher can never see it); scoped to magic_working only — scenario_clue keeps the 59-8 Glenross quiet-gate contract
  - Rationale: The two miss shapes (gated-pre-bank vs dispatched-but-unengaged) need one GM-panel signal; emitting at the gate is the only site that still has the dispatch. TEA's test asserts the span across the whole pass+watcher flow, implementation-agnostic
  - Severity: minor
  - Forward impact: none — 90-8 (typed GM-panel feed) consumes the same span name from either emit site
- **WN engagement receipt is a new snapshot field (`wwn_spell_cast_log`), not a turn-context artifact**
  - Spec source: context-story-102-3.md, Technical Guardrails (lie-detector deliverable)
  - Spec text: spec names the spans but not the watcher's evidence mechanism
  - Implementation: turn-stamped `WwnCastLogEntry` ledger on GameSnapshot (mirrors 59-30 `region_transitions`), stamped on every `resolve_spellcast` call (cast AND refused); categorized `_PHASE_B_DROP_FIELDS` (prompt-payload drop, persists in save)
  - Rationale: the witness only receives `(dispatch, snapshot, player_id)`; snapshot-readable turn-scoped evidence is the established pattern (movement, witnessed_act); refusals must count as engagement or the lie-detector cries wolf on honest fizzles
  - Severity: minor
  - Forward impact: ADR-124 forensics gains a per-cast receipt for free; saves grow one row per cast
- **Out-of-story test-suite repair (operator-directed)**
  - Spec source: operator instruction mid-green ("fix or skip the broken ones")
  - Spec text: n/a — scope addition by the operator
  - Implementation: fixed 7 genuinely-broken pre-existing tests across three repos (see Dev Assessment); ~22 further failures diagnosed as environmental (DB env vars unset), zero skips added
  - Rationale: operator directive; every fix is root-cause (fixture gap, stale gate allowlist, accidental doc deletion, under-sized corpus), no test weakened
  - Severity: minor
  - Forward impact: orchestrator commit needs operator push; content PR #411 needs operator merge

### Reviewer (audit)
- **TEA: no engaged-span test** → ✓ ACCEPTED by Reviewer: the AC Context names the
  mismatch span as the deliverable ("that span is the AC"); no `.engaged` variant exists
  for any subsystem today, and pinning a new span name in RED would have constrained the
  engagement-evidence design without spec backing.
- **TEA: param contract `{actor, spell}`** → ✓ ACCEPTED by Reviewer: `actor` mirrors the
  watcher's existing `_DISPATCHED_TYPE_KEY["magic_working"]`; `spell` is the minimal
  carrier for the typed name; the router-prompt extension teaches Haiku the same keys.
- **Dev: AC2 mismatch from the gate wrapper** → ✓ ACCEPTED by Reviewer: the gate is the
  only site that still holds the dispatch after stripping it from the package; span name
  is identical for 90-8 consumers; scoping to magic_working preserves the 59-8
  scenario_clue quiet-gate contract (verified `_keep`/wrapper diff — scenario_clue and
  witnessed_act drops emit only `intent_router.dispatch.gated`).
- **Dev: snapshot ledger `wwn_spell_cast_log`** → ✓ ACCEPTED by Reviewer: 59-30
  `region_transitions` precedent verified (same shape, same Phase-B drop categorization,
  `extra: ignore` for forward-compat); refusal-counts-as-engagement is the correct
  cry-wolf prevention.
- **Dev: out-of-story suite repair** → ✓ ACCEPTED by Reviewer: operator-directed; each
  fix verified root-cause (fixture bestiary, AST-gate exemption with rationale, doc
  restore from `a731ec5^`, corpus expansion via conlang lane); zero `@pytest.mark.skip`
  added anywhere in the diff.