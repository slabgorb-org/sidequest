---
story_id: "126-14"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-14: [FATE] Reconcile concede-at-defend — wire defend-concession end-to-end

## Story Details
- **ID:** 126-14
- **Title:** [FATE] Reconcile concede-at-defend: AC-4 (server records concession) vs AC-6 (no wire) — add a defend-concession protocol field or remove the dead conceded branches
- **Points:** 3
- **Jira Key:** none (not configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server
- **Branch:** feat/126-14-fate-defend-concession
- **Scope note (2026-06-19, Architect):** RE-SCOPED to server-only. The UI concede affordance + the whole missing Fate defend-throw UI surface moved to new story **126-17** (p1). Story YAML `repos:` still reads `server,ui` (the `pf sprint story update` CLI has no `--repos` flag) — **this `Repos: server` line is authoritative** (see Design Deviations).

## Context Summary

Story 126-8 introduced player defense 4dF determinism (physics-is-the-roll) but left a design split unresolved: AC-4 states "server records concession" while AC-6 says "no wire". The review found dead code branches for conceding attacks:

- `dispatch_fate_defense(conceded=...)` parameter exists but has no caller
- `_resolve_attack` concede branch in fate_conflict.py is untouched
- `ledger_full ... or p.conceded` clause in pending-defense accumulation is dead
- `FatePendingDefense.conceded` field is defined but never set in production

Keith's decision (2026-06-19): **WIRE the concession end-to-end**. This honors Fate's signature concession agency (the player may concede when facing an incoming attack, forfeiting defense in exchange for narrative control) and the project's "wire it, don't delete" doctrine. The story adds:

1. A `concede` signal field on the FATE_THROW message (action='defend', concede=True/False or null)
2. Handler plumbing to mark the entry conceded and fire the `_resolve_attack` concede branch (no roll_4df on the player path when conceding)
3. UI defense tray affordance (Concede button) that sends the message without a dice throw
4. Authorization guard: only the entry's own defender may concede (mirrors the ADR-119 spoof-rejection added in 126-8)
5. Resume-safety: a conceded entry in snapshot.encounter survives restart; RESUME never re-rolls
6. OTEL watcher events so the GM panel records the concession was a real choice, not improv

This story completes ADR-148/149's DEFEND barrier coverage and fulfills the no-half-wired-features invariant.

## Acceptance Criteria (SERVER-ONLY — re-scoped 2026-06-19; UI moved to 126-17)

1. FateThrowPayload(action='defend') gains a 'concede' signal field; when conceding, NO 4dF faces are required (no roll_4df, faces optional/ignored on the concede path). A non-concede defend throw still validates its four faces (defense in depth unchanged).

2. _handle_defend reads the concede signal and passes conceded=True to dispatch_fate_defense, marking the matching pending_defenses entry conceded and filling the ledger via the already-built _resolve_attack concede branch (fate_conflict.py:612) and the 'ledger_full ... or p.conceded' clause (fate_conflict.py:1231). After this story NO 'conceded' code path remains unwired (No half-wired features / dead-code doctrine).

3. Authorization holds: only the entry's own defender may concede it — the existing entry.defender==actor_name check (fate_conflict.py:1188, ADR-119) must guard the concede path too. A concede aimed at another defender's request_id is rejected loudly (FateConflictError) and that defender's entry stays unfilled (and unconceded).

4. Resume-safety (ADR-128): a conceded pending_defenses entry rides snapshot.encounter and survives a server restart; RESUME reads the recorded concession and never re-rolls; NPC dice locked at REVEAL are untouched.

5. OTEL (lie detector): the fate.defend_phase span records conceded=True for the answered entry, and NO fate.action_resolved roll span is emitted for a conceded defense (nothing was rolled). The GM panel can confirm a concession was a real player choice.

6. Wiring (mandatory, server e2e): a test drives NPC-attacks-PC -> FATE_DEFEND_REQUEST -> player CONCEDES through the real FateThrowHandler/registry/exchange on a fixture snapshot -> ledger fills -> RESUME -> narrate-once, asserting the concede span fired and no player 4dF was rolled. Span capture over grepping production source.

> **Dropped from this story (moved to 126-17):** the UI concede affordance — there is no Fate defend UI surface to host it (verified 2026-06-19). 126-17 builds the whole defend tray + concede button.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T10:05:14Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T08:29:23Z | - | - |
| red | 2026-06-19T08:29:23Z | 2026-06-19T09:17:14Z | 47m 51s |
| green | 2026-06-19T09:17:14Z | 2026-06-19T09:28:48Z | 11m 34s |
| review | 2026-06-19T09:28:48Z | 2026-06-19T09:37:24Z | 8m 36s |
| green | 2026-06-19T09:37:24Z | 2026-06-19T09:51:56Z | 14m 32s |
| review | 2026-06-19T09:51:56Z | 2026-06-19T10:05:14Z | 13m 18s |
| finish | 2026-06-19T10:05:14Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### Architect (scope re-verification)
- **Gap (blocking — FILED as 126-17):** 126-8's DEFEND barrier is unreachable from the UI. The server broadcasts `FATE_DEFEND_REQUEST` and block-and-waits with no auto-roll (`sidequest/handlers/fate_throw.py:161-173`), but the UI has no `FATE_DEFEND_REQUEST` handler, no `"defend"` action (`payloads.ts:614`), and no defend tray (verified 2026-06-19 via exhaustive grep + server contract trace). So a Fate conflict where an NPC attacks a PC **parks forever**. 126-8 was marked done as `repos=server,ui` but its UI half (defense-throw tray) was deferred to spec §8 and never filed. New story **126-17** (p1) builds the surface. *Found by Architect during 126-14 RED re-verification.*

### TEA (test design)
- **Gap (non-blocking):** AC-1 must NOT make `face` unconditionally optional. `FateThrowPayload`'s docstring and `test_fate_throw_non_concede_defend_still_requires_faces` pin the anti-backdoor invariant — a NON-concede defend throw still requires four valid dF faces. Dev: add `concede: bool = False`, make `face` optional (`tuple[int,int,int,int] | None = None`), and extend the `_validate_faces` model_validator to require valid faces when `not self.concede`. Affects `sidequest/protocol/fate.py` (`FateThrowPayload`). *Found by TEA during test design.*
- **Gap (non-blocking):** `_handle_defend` currently always passes `thrown_faces=payload.face`; on a concession `face` is None. Dev must branch — when `payload.concede`, call `dispatch_fate_defense(..., conceded=True)` and do NOT pass/require faces (the dispatch concede branch at fate_conflict.py:1207 ignores `thrown_faces`). Affects `sidequest/handlers/fate_throw.py:260-268`. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. The concede ENGINE pre-existed from 126-8; this story added only the protocol field + handler wire (+ `dispatch_fate_defense` faces-optional). The UI defend-surface gap is already filed as **126-17**.
- No upstream findings during rework. The reviewer's HIGH concede+faces finding was a contained protocol-boundary gap, fixed with the specified one-line guard + RED test; no spec gaps, conflicts, or questions surfaced.

### Reviewer (code review)
- **Improvement** (non-blocking): `FateConflictError` text is returned verbatim to the client; on a cross-player concede/defend it leaks the owning defender's PC name and the `def:{round}:{attacker}->{target}` request_id format (CWE-209). Pre-existing from the 126-8 defend path (NOT introduced by this diff); acceptable under this project's trusted single-table threat model (ADR-036 peer-visibility; request_id already broadcast). Affects `sidequest/server/dispatch/fate_conflict.py` (return a generic client message, log detail server-side) — a future hardening pass, not a 126-14 blocker. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `dispatch_fate_defense` has no fail-loud guard against `conceded=True` + non-None `thrown_faces` — it ignores faces on the concede branch. This is AC-1-sanctioned ("faces optional/ignored on the concede path") and unreachable from the wire (the protocol guard closes it), so it is NOT a violation; but the dispatch function is internal-public and the AC-4 net test exercises the inert combo (`thrown_faces=(0,0,0,0)`). Affects `sidequest/server/dispatch/fate_conflict.py` / `tests/server/test_fate_concede_wire.py` (optional defense-in-depth guard + pass `None` in the test) — a clarity nicety, not required. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): a concede `FateThrowPayload` accepts `skill`/`target`/`difficulty` that are ignored on the fold path. Distinct from faces (faces are the roll → a direct contradiction; intent metadata has harmless defaults and creates no narration-vs-mechanics divergence). Out of AC-1 scope for 126-14. Affects `sidequest/protocol/fate.py` (could reject or document) — future hardening. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### Architect (scope re-verification)
- **126-14 re-scoped server-only; UI concede + defend surface split to 126-17**
  - Spec source: sprint/epic-126.yaml 126-14 AC-6; session Repos: server,ui
  - Spec text: "UI (sidequest-ui): the defense tray surfaces a Concede affordance alongside the defend throw..."
  - Implementation: 126-14 narrowed to server-only (concede protocol field + handler + OTEL + auth + resume + e2e); AC-6 removed; new story 126-17 (p1, repos ui) builds the entire Fate defend-throw UI surface + concede affordance.
  - Rationale: verification 2026-06-19 found NO Fate defend UI surface exists — no tray to host a concede button, and concede-alone would be half-wired. Keith approved the split 2026-06-19.
  - Severity: major
  - Forward impact: 126-17 (UI defend surface; concede affordance soft-depends on this story's server concede field); 126-15 (DEFEND-barrier ADR should document the UI-reachability gap).
- **Story YAML repos field stale (server,ui); session Repos line authoritative (server)**
  - Spec source: sprint/epic-126.yaml 126-14 repos: server,ui
  - Spec text: "repos: server,ui"
  - Implementation: session Repos set to "server"; YAML repos left unchanged (the `pf sprint story update` CLI exposes no `--repos` flag and hand-editing sprint YAML is prohibited).
  - Rationale: CLI limitation; the session Repos line is the authoritative scope per project convention.
  - Severity: minor
  - Forward impact: SM finish creates ONLY the server PR for 126-14 (ignore the stale ui entry); the orphaned ui branch feat/126-14-fate-defend-concession is deleted as part of this re-scope.

### TEA (test design)
- **Wire tests placed in tests/server/, not tests/handlers/**
  - Spec source: context-story-126-14.md AC-6
  - Spec text: "a test drives ... through the real handler/registry/exchange on a fixture snapshot"
  - Implementation: the handler-driven concede wire tests live in `tests/server/test_fate_concede_wire.py` (co-located with the 126-8 e2e `test_fate_defend_barrier_wiring.py`), not `tests/handlers/`, because `tests/handlers/conftest.py` has an autouse `_pg_isolation` fixture that SKIPS without a live test DB — the DB-free session-double harness must live in `tests/server/` so the RED tests actually RUN in the standard unit suite.
  - Rationale: keep the wire tests executable in the normal (no-DB) suite, matching where the analogous 126-8 e2e test lives.
  - Severity: trivial
  - Forward impact: none.
- **AC-4 covered by a green safety-net, not a RED driver**
  - Spec source: context-story-126-14.md AC-4
  - Spec text: "a conceded pending_defenses entry rides snapshot.encounter and survives a server restart; RESUME reads the recorded concession and never re-rolls"
  - Implementation: `test_conceded_entry_survives_reload_and_resume_folds_defender` passes GREEN today — the persistence + resume-fold engine pre-exists from 126-8; only the player-side WIRE is new (covered RED by the handler tests). The test is a characterization net pinning the concede path across a model round-trip.
  - Rationale: AC-4's engine behavior shipped in 126-8; this story adds only the wire. Documented so a reviewer doesn't read the green as missing-RED.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Corrected a TEA test with a wrong invariant**
  - Spec source: tests/server/test_fate_concede_wire.py (TEA RED test `test_concede_through_handler_never_rolls_a_player_defense`)
  - Spec text: "assert calls['roll'] == 0" — no 4dF rolled on the concede turn
  - Implementation: renamed to `..._never_resolves_a_player_defense`; spies `FateRulesetModule.resolve_action_from_faces` (asserts 0) instead of counting `roll_4df`. The original premise was WRONG: at RESUME the conceding PC's own proactive attack still resolves, so the NPC legitimately server-rolls ITS defense via `resolve_action` (a different path) — `roll_4df` is non-zero. Production is correct; only the test invariant was wrong.
  - Rationale: assert the true invariant (the PLAYER-defense resolver never runs on concede), not "zero rolls anywhere".
  - Severity: minor
  - Forward impact: none.
- **`concede` restricted to `action="defend"` (beyond AC-1's literal text)**
  - Spec source: context-story-126-14.md AC-1
  - Spec text: "when conceding, NO 4dF faces are required ... A non-concede defend throw still validates its four faces"
  - Implementation: `_validate_faces` also rejects `concede=True` on a non-defend action. Because `face` is now optional, a proactive throw could otherwise omit faces via `concede=True` and bypass the faces requirement; this guard keeps the anti-backdoor invariant closed for ALL non-defend throws.
  - Rationale: faithful to AC-1's intent ("optional ONLY on the concede path"); closes a backdoor the literal text didn't enumerate.
  - Severity: minor
  - Forward impact: none (126-17 only sets `concede` on defend throws).
- **Dev authored the rework RED test (workflow routed review→green, not review→TEA→green)**
  - Spec source: Reviewer Assessment (REJECTED) handoff — "Back to TEA for a RED test on the concede+faces rejection, then Dev for the one-line validator guard."
  - Spec text: "Back to TEA for a RED test ... then Dev for the one-line validator guard."
  - Implementation: the tdd workflow routed the reject straight to the green phase (dev), with no red (TEA) phase inserted (Phase History: review→green at 2026-06-19T09:37:24Z). I (Dev) authored the RED test `test_fate_throw_defend_concede_rejects_faces` in `tests/protocol/test_fate_defend_protocol.py`, watched it fail for the right reason (`DID NOT RAISE ValidationError`), then added the one-line validator guard to make it pass — preserving TDD red-before-green within the single green phase.
  - Rationale: I am the green-phase owner per `pf workflow phase-check tdd green`; the reviewer's "Back to TEA" was a process suggestion the workflow did not honor, and blocking to re-route would have been wasteful for a one-test/one-line rework. TDD discipline (failing test first) was kept.
  - Severity: minor
  - Forward impact: none.
- **concede+faces contradiction now rejected loud (rework — closes the HIGH finding)**
  - Spec source: Reviewer Assessment (REJECTED) — HIGH `[SILENT]` `[RULE]` finding; AC-1
  - Spec text: "In `_validate_faces`, reject the contradiction: `if self.concede and self.face is not None: raise ValueError(\"a concede throw carries no dice faces\")`. Add a RED test `test_fate_throw_defend_concede_rejects_faces`."
  - Implementation: implemented verbatim — added the guard to `FateThrowPayload._validate_faces` (after the concede-on-non-defend guard) plus the RED test. A concede that carries faces now fails loud at the protocol boundary instead of being silently dropped downstream.
  - Rationale: No Silent Fallbacks (CLAUDE.md `<critical>`, lang-review #1/#11) — the validator now fails loud on the one remaining contradiction, closing the narration-vs-mechanics divergence vector the reviewer flagged.
  - Severity: minor (faithful rework; no scope change)
  - Forward impact: none — 126-17's concede affordance sends `concede=True` with no faces, which the guard permits.

### Reviewer (audit) — re-review (Round 2, 2026-06-19)
- Architect / TEA / Dev (original) deviations → ✓ all re-affirmed ACCEPTED (Round-1 audit stands; nothing in the rework alters them).
- Dev (rework) "Dev authored the rework RED test (workflow routed review→green, not review→TEA→green)" → ✓ ACCEPTED: verified the Phase History shows review→green at 2026-06-19T09:37:24Z with no red(TEA) phase, and `pf workflow phase-check tdd green` returns `dev`. Dev preserved RED-before-green within the single green phase (RED verified `DID NOT RAISE ValidationError`, then GREEN). A separate TEA cycle for a one-line guard would have been wasteful; TDD discipline was kept. Sound.
- Dev (rework) "concede+faces contradiction now rejected loud (closes the HIGH finding)" → ✓ ACCEPTED: implemented verbatim to the Round-1 fix spec (`fate.py:112-116`); independently confirmed closed by reviewer-silent-failure-hunter (high) and reviewer-security (compliant). The reconciliation is exactly as prescribed — the PROTOCOL boundary rejects a concede that carries faces, while the ENGINE ignores faces on concede per AC-1.
- **Reviewer (audit) — no new undocumented deviations.** The rework is confined to the one guard + one test; no spec divergence introduced.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-server/tests/protocol/test_fate_defend_protocol.py` (+3) — concede payload contract (AC-1)
- `sidequest-server/tests/server/test_fate_concede_wire.py` (new, 5) — concede through the REAL FateThrowHandler (AC-2/3/5/6) + the AC-4 resume net

**Tests Written:** 8 (6 RED + 2 documented green nets) covering all 6 server ACs
**Status:** RED — verified by targeted run (`-n0`): **6 failed for the right reason** (no `concede` field on `FateThrowPayload`; `_handle_defend` never forwards `conceded`), 8 passed (6 pre-existing 126-8 protocol tests = no regression, + 2 green nets). 126-8 dispatch + barrier-wiring suites still green (9 passed, no regression). The entire concede ENGINE (dispatch concede branch, `fate.defend_phase` conceded span, ledger fill, `_resolve_attack` fold, resume) already exists from 126-8 — the RED surface is purely **protocol field + handler wire**, so these tests drive the real handler and do not duplicate the green dispatch-layer concede/auth tests.

### Rule Coverage
| Rule / AC | Test(s) | Status |
|-----------|---------|--------|
| AC-1 concede field / faces-optional-on-concede | `test_fate_throw_defend_concede_valid_without_faces`, `_field_defaults_false` | RED |
| AC-1 anti-backdoor (lang-review #11 input-validation; No Silent Fallbacks #1) | `test_fate_throw_non_concede_defend_still_requires_faces` | green guard |
| AC-2 handler plumbs conceded; dead branch goes live | `test_concede_through_handler_fills_ledger_and_resumes` | RED |
| AC-1/2 no player 4dF on concede (ADR-148) | `test_concede_through_handler_never_rolls_a_player_defense` | RED |
| AC-3 defender authorization (No Silent Fallbacks #1; lang-review #11) | `test_concede_for_another_defenders_request_is_rejected` | RED |
| AC-5 OTEL lie-detector (project OTEL principle) | `test_concede_through_handler_emits_conceded_defend_phase_and_no_player_roll_span` | RED |
| AC-4 resume-safety (ADR-128) | `test_conceded_entry_survives_reload_and_resume_folds_defender` | green net |
| AC-6 wiring e2e through real handler (project wiring rule) | `test_concede_through_handler_fills_ledger_and_resumes` | RED |
| Test quality (lang-review #6) | all | self-checked |

**Rules checked:** lang-review #6 (test quality), #11 (input validation at boundary), #1 (fail-loud / No Silent Fallbacks), plus the project OTEL / determinism (ADR-148) / resume-safety (ADR-128) / wiring principles. The remaining lang-review checks (#2 mutable defaults, #3/#4 annotations/logging, #5 paths, #7 leaks, #8 deserialization, #9 async, #10 imports, #12 deps, #13 fix-regressions) are Dev-side GREEN self-review concerns, not new-AC test surface.
**Self-check:** 0 vacuous tests — every test asserts a specific value/identity (`entry.conceded`/`withdrawn`, `pending_defenses == []`, `orchestrator.calls == 1`, span attributes, `calls['roll'] == 0`); the 2 always-green tests are a documented anti-backdoor guard + an AC-4 characterization net, not accidental passes.

**Handoff:** To Dev (Inigo Montoya) for GREEN — add `concede` to `FateThrowPayload` (faces optional only on the concede path; keep the four-faces requirement for a real defend), and wire `_handle_defend` to forward `conceded=True` to `dispatch_fate_defense` without requiring faces. No engine changes needed — the dispatch concede machinery already exists from 126-8.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/protocol/fate.py` — `FateThrowPayload`: add `concede: bool = False`; `face` now `tuple | None = None`; `_validate_faces` requires four dF faces unless conceding and restricts `concede` to `action="defend"`; docstrings updated for the concede path.
- `sidequest-server/sidequest/handlers/fate_throw.py` — `_handle_defend` forwards `conceded=payload.concede` to `dispatch_fate_defense` (faces `None` on the fold).
- `sidequest-server/sidequest/server/dispatch/fate_conflict.py` — `dispatch_fate_defense.thrown_faces` now optional with a fail-loud guard on the non-concede path; docstring updated.
- `sidequest-server/tests/server/test_fate_concede_wire.py` — corrected one test's invariant (see Dev deviation).

**Tests:** GREEN — focused suite 37/37; fate-scoped regression canary **397 passed, 0 failed** (`tests/server tests/protocol tests/game/ruleset tests/handlers -k fate`). Lint + format clean on all touched files.
**Branch:** feat/126-14-fate-defend-concession (pushed → origin)

**Minimalism note:** no engine logic added — the concede branch, `fate.defend_phase` conceded span, ledger fill, `_resolve_attack` fold, and resume all pre-existed from 126-8. This story is purely the player-side wire (protocol field + handler forward + dispatch faces-optional), which is exactly what made the 126-8 dead `conceded` branches live.

**Handoff:** To next phase (verify / review).

### Dev Assessment — Rework (Round-Trip 2, 2026-06-19)

**Trigger:** Reviewer REJECTED on a HIGH `[SILENT]` `[RULE]` finding — `FateThrowPayload._validate_faces` accepted `concede=True` WITH a non-None `face` tuple; the faces were then silently discarded by the dispatch concede branch (No Silent Fallbacks violation + narration-vs-mechanics divergence vector).

**Fix (minimal, exactly as specified):**
- `sidequest/protocol/fate.py` — `FateThrowPayload._validate_faces`: added one guard `if self.concede and self.face is not None: raise ValueError("a concede throw carries no dice faces")` (placed after the existing concede-on-non-defend guard). A concede that carries faces now fails loud at the protocol boundary.
- `tests/protocol/test_fate_defend_protocol.py` — added RED test `test_fate_throw_defend_concede_rejects_faces` (constructs `action="defend", concede=True, face=(1,1,1,1)`, expects `ValidationError`). Verified RED first (`DID NOT RAISE ValidationError`), then GREEN.

**Tests:** GREEN — `tests/protocol/test_fate_defend_protocol.py tests/server/test_fate_concede_wire.py` = 15/15 passing (incl. the new test); fate-scoped regression canary **396 passed, 2 skipped, 0 failed** (`tests/server tests/protocol tests/game/ruleset tests/handlers -k fate`). Ruff lint + format clean on both touched files. No existing test constructs concede+faces (verified by grep), so the new guard breaks nothing.

**Branch:** feat/126-14-fate-defend-concession (pushed → origin)

**Handoff:** Back to review (Westley).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
_(Round 2 / re-review of the rework — same enabled set as Round 1.)_

| 1 | reviewer-preflight | Yes | clean | none (411 pass / 0 fail / 2 pre-existing skip; ruff + format clean; 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered personally — see [EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 high = closure-confirmation, 1 medium, 1 low) | prior HIGH CONFIRMED CLOSED; medium dismissed (AC-1-sanctioned, see [SILENT]); low → non-blocking delivery finding |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (covered personally — see [TEST] below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (covered personally — see [DOC] below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered personally — see [TYPE] below) |
| 7 | reviewer-security | Yes | findings | 3 (1 medium pre-existing CWE-209, 2 low) | 0 auth/backdoor violations; all 3 non-blocking (pre-existing / project threat model — see [SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered personally — see [SIMPLE] below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (covered personally — see [RULE] / Rule Compliance below) |

**All received:** Yes (3 enabled returned and assessed; 6 disabled pre-filled and covered personally per the 90-1 disabled-subagent rule)
**Total findings:** 0 confirmed-blocking — the prior HIGH is verified CLOSED. Remaining items are all medium/low and non-blocking (2 dismissed with rationale: dispatch defense-in-depth is AC-1-sanctioned, the concede-on-non-defend message is informational; 3 captured as non-blocking delivery findings: CWE-209 leak, dispatch guard nicety, concede extra-fields).

## Reviewer Assessment

**Verdict:** APPROVED

_Round 2 — re-review of the rework that closed the Round-1 HIGH finding. The full Round-1 (REJECTED) assessment is preserved below under "Prior Review — Round 1" for history._

**Data flow traced:** A hostile/buggy `FATE_THROW(action="defend", concede=True, face=(1,1,1,1))` now dies at `FateThrowPayload` construction — `_validate_faces` (`fate.py:112-116`) raises `ValueError("a concede throw carries no dice faces")` before the payload can exist, so the contradiction never reaches the handler. A *valid* concede (`concede=True`, no `face`) → `FateThrowHandler.handle` → `_handle_defend` → `dispatch_fate_defense(conceded=True, thrown_faces=None)` → auth check `entry.defender == actor_name` (runs BEFORE the concede mutation) → concede branch sets `entry.conceded=True`, `outcome=None` → `fate.defend_phase(conceded=True)` span → `ledger_full` → `_finish_defense` resume → narrate once. The El Dorado lie (client animates a roll while the server folds) is now structurally impossible: a single payload can no longer carry both a concession and dice faces.

**Pattern observed:** fail-loud-at-the-boundary with defense-in-depth — `_validate_faces` (`fate.py:101-124`) rejects all four contradictory input combinations at the wire, and the dispatch layer adds a second loud guard for the non-concede-without-faces case (`fate_conflict.py:1211-1214`). Good, consistent pattern.

**Error handling:** `_handle_defend`'s `except FateConflictError` (`fate_throw.py`) logs a warning (client-error → warning level, lang-review #4 correct) and surfaces the error to the client rather than swallowing it.

**Observations (≥5):**
- `[SILENT]` `[RULE]` `[VERIFIED]` **Prior HIGH CLOSED at the boundary.** `_validate_faces` (`fate.py:112-116`) raises `ValueError("a concede throw carries no dice faces")` for `concede=True, face is not None`. Independently confirmed by reviewer-silent-failure-hunter (high confidence) and reviewer-security (compliant). All four contradictions fail loud: concede+non-defend (`:110-111`), concede+faces (`:112-116`), non-concede+no-faces (`:117-119`), out-of-range face (`:121-123`).
- `[SILENT]` dispatch defense-in-depth (DISMISSED, non-blocking): silent-failure-hunter flagged (medium) that `dispatch_fate_defense(conceded=True, thrown_faces != None)` ignores the faces. DISMISSED — AC-1 explicitly states "faces optional/**ignored** on the concede path", so the ENGINE ignoring faces IS the spec; the combination is unreachable from the wire (the protocol guard precedes it). Captured as a non-blocking delivery finding for an optional dispatch-layer guard + a test-clarity tweak.
- `[SEC]` `[VERIFIED]` cross-defender concede is rejected — `entry.defender != actor_name` (`fate_conflict.py:1197`) runs BEFORE the concede mutation (`:1208`), so a concede aimed at another PC's `request_id` raises `FateConflictError` and leaves that entry untouched. reviewer-security: 0 auth violations. Pinned by `test_concede_for_another_defenders_request_is_rejected`.
- `[SEC]` CWE-209 info leak (non-blocking, pre-existing): `FateConflictError` text is returned verbatim to the client; on a cross-player concede it leaks the owning defender's PC name + the `def:{round}:{attacker}->{target}` request_id format. PRE-EXISTING from the 126-8 defend path (not introduced by this diff); acceptable under this project's trusted single-table threat model (ADR-036 peer-visibility; request_id already broadcast). Recorded as a non-blocking delivery finding.
- `[VERIFIED]` backdoor closed — non-concede + `face=None` fails loud at BOTH the protocol validator (`fate.py:117-119`) and the dispatch guard (`fate_conflict.py:1211-1214`). No `roll_4df`-for-the-player path survives.
- `[TYPE]` `[VERIFIED]` `face: tuple[int, int, int, int] | None = None` and `thrown_faces: tuple | None = None` are correctly annotated Optionals; the tuple shape still enforces exactly-4 faces when present; `concede: bool = False` is a typed, immutable default.
- `[DOC]` `[VERIFIED]` the `FateThrowPayload` / `dispatch_fate_defense` docstrings, the new test comment, and the inline `# None on a concession (no roll)` at `fate_throw.py:267` all match the implemented behavior. (reviewer-comment-analyzer disabled — checked personally.)
- `[SIMPLE]` `[VERIFIED]` the rework is exactly 5 lines of guard + 1 test; no engine logic added, no dead code, no over-engineering. reviewer-preflight: 0 smells.
- `[TEST]` `[VERIFIED]` `test_fate_throw_defend_concede_rejects_faces` asserts the specific contradiction (`concede=True` + `face` → `ValidationError`); Dev verified RED (`DID NOT RAISE`) then GREEN. Non-blocking nit: the AC-4 net `test_conceded_entry_survives_reload_and_resume_folds_defender` passes `thrown_faces=(0,0,0,0)` to the dispatch layer with `conceded=True` — now a production-impossible combo, but inert (AC-1-sanctioned ignore) and outside the rework delta. (reviewer-test-analyzer disabled — checked personally.)
- `[EDGE]` `[VERIFIED]` the guard ordering (concede-on-non-defend → concede+faces → no-faces → range) correctly resolves all eight input combinations; unknown / already-filled `request_id` on concede fails loud (`fate_conflict.py`).

### Rule Compliance (lang-review/python + SOUL) — Round 2
- **#1 Silent exception/fallback swallowing — COMPLIANT (was the Round-1 VIOLATION, now fixed):** `_validate_faces` fails loud on the concede+faces contradiction. The dispatch layer ignoring faces on concede is AC-1-sanctioned ("faces ignored on the concede path"), not a swallow. Every error path raises (`ValueError` / `FateConflictError`).
- **#11 Input validation at boundaries — COMPLIANT:** the wire payload now rejects all four contradictory combinations.
- **#6 Test quality — COMPLIANT:** specific value/identity assertions; the new RED test is non-vacuous and was RED-verified.
- **#3 Type annotations — COMPLIANT:** `concede: bool`, `face: tuple|None`, `thrown_faces: tuple|None` annotated at the boundaries.
- **#4 Logging — COMPLIANT:** `_handle_defend`'s `except FateConflictError` logs at warning (client error), the correct severity.
- **SOUL "No Silent Fallbacks" — COMPLIANT** (the boundary fix). **SOUL "Bind the ruleset" — N/A** (no ladder math touched).
- **#2/#5/#7/#8/#9/#10/#12 — N/A** to this diff (no mutable defaults, paths, resources, deserialization, async, imports, or deps changes).

### Devil's Advocate
Assume it is still broken. The sharpest remaining angle is the dispatch layer: `dispatch_fate_defense` still silently ignores `thrown_faces` on the concede branch, and the AC-4 net test proves it by passing `(0,0,0,0)` with `conceded=True`. A future refactor that adds a second internal caller — or a resume path that reconstructs the dispatch call from a persisted snapshot — could smuggle faces past the now-guarded wire and reintroduce the divergence the protocol guard was meant to kill. But trace it: the only production caller is `_handle_defend`, which sources both `conceded` and `thrown_faces` from a `FateThrowPayload` the validator has already vetted, so production always passes `thrown_faces=None` on a concede; there is no other production caller (grep). The resume path (`resume_fate_exchange`) reads the persisted `entry.conceded` boolean and never reconstructs `thrown_faces`, so a reloaded snapshot cannot smuggle faces. The next angle is the info-leak: a malicious table member spams cross-player concedes to enumerate live request_ids and defender names — but the request_id is already broadcast to every seat (ADR-036 peer visibility), the auth guard rejects the concede before any mutation, and the wrong player learns nothing they could not already see and cannot fold another PC's defense. The Round-1 race vector (client animates a 4dF tumble while the server records a fold) is now structurally impossible: a payload carrying faces cannot also concede, and a concede payload carries no faces, so there is nothing to animate against the fold. Config/filesystem/timeout/async vectors are N/A — this is pure in-memory, synchronous pydantic validation. I tried to break it and the one real Round-1 defect is closed; the residue is pre-existing or AC-1-sanctioned, none of it blocking.

**Handoff:** To SM (Vizzini) for finish-story.

---

## Prior Review — Round 1 (REJECTED — superseded by the APPROVED assessment above)

**Round-1 Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[SILENT]` `[RULE]` | `_validate_faces` accepts a payload with BOTH `concede=True` and a non-None `face` tuple; the faces then reach `dispatch_fate_defense` and are silently discarded by the concede branch (which sets `outcome=None` and never reads `thrown_faces`). Contradictory input is accepted and partially dropped with no error — a No Silent Fallbacks violation (CLAUDE.md `<critical>`) in the very validator this story hardens, and a narration-vs-mechanics divergence risk (a client could animate a thrown roll while the server records a fold — the El Dorado lie). The validator already fails loud on every other contradiction (missing faces, out-of-range faces, concede-on-non-defend); this is the one inconsistent gap. | `sidequest/protocol/fate.py` `FateThrowPayload._validate_faces` | In `_validate_faces`, reject the contradiction: `if self.concede and self.face is not None: raise ValueError("a concede throw carries no dice faces")`. Add a RED test `test_fate_throw_defend_concede_rejects_faces`. (This reconciles AC-1 "faces optional/ignored on the concede path" — the ENGINE ignores faces during resolution — with No Silent Fallbacks at the PROTOCOL boundary: a concede that *carries* faces is contradictory and must fail loud.) |

**Data flow traced:** `FATE_THROW(action="defend", concede=True)` → `FateThrowHandler.handle` (auth/seat resolution, `fate_throw.py:69-122`) → `_handle_defend` → `dispatch_fate_defense(conceded=True, thrown_faces=None)` → auth check (`entry.defender==actor_name`, 1196) → concede branch (`entry.conceded=True`, 1207) → `fate_defend_phase_span(conceded=True)` → `ledger_full` → `_finish_defense` resume → narrate once. Safe EXCEPT the concede+faces contradiction above.

**Observations (≥5):**
- `[HIGH]` `[SILENT]` `[RULE]` concede+faces silently dropped — see severity table. Confirmed from reviewer-silent-failure-hunter (high) and my own #1/#11 rule analysis.
- `[SEC]` `[VERIFIED]` cross-defender concede is rejected — the `entry.defender != actor_name` auth check (`fate_conflict.py:1196`) runs BEFORE the concede branch (`:1207`), so a concede aimed at another PC's `request_id` raises `FateConflictError` and leaves that entry untouched. reviewer-security: 0 violations. Test: `test_concede_for_another_defenders_request_is_rejected`.
- `[VERIFIED]` `[SEC]` concede-on-non-defend cannot reach a server-roll backdoor — `_validate_faces` raises "concede is only valid on a defend throw" at construction; the proactive handler branch (`fate_throw.py:113`) is unreachable with `concede`. Anti-backdoor invariant held.
- `[DOC]` `[VERIFIED]` docstrings are accurate — `FateThrowPayload` and `dispatch_fate_defense` docstrings now describe the concede path (faces omitted on concede, fail-loud otherwise) and match the code.
- `[TYPE]` `[VERIFIED]` `thrown_faces: tuple | None` mirrors `dispatch_fate_action`'s pre-existing Optional signature; the non-concede branch's `if thrown_faces is None: raise` (`fate_conflict.py:~1212`) is a correct fail-loud narrow.
- `[SIMPLE]` `[VERIFIED]` minimal change — no engine logic added; the concede branch/span/ledger/fold are reused from 126-8. No over-engineering, no dead code.
- `[EDGE]` `[VERIFIED]` unknown / already-filled `request_id` on concede → fail loud (`fate_conflict.py:1183`, `:1202`); both tested at the dispatch layer (126-8) and reachable via the wire.
- `[TEST]` the concede+faces contradiction is currently UNTESTED — the rework RED test closes it. The corrected `test_concede_through_handler_never_resolves_a_player_defense` (spies `resolve_action_from_faces`) is sound; the AC-4 green net is documented.

### Rule Compliance (lang-review/python + SOUL)
- **#1 Silent exception/fallback swallowing — VIOLATION:** `_validate_faces` silently accepts+drops `concede=True` + faces (the finding). All other error paths fail loud (`FateConflictError` / `ValueError`).
- **#11 Input validation at boundaries — VIOLATION (same instance):** the protocol boundary accepts a contradictory payload instead of rejecting it.
- **#6 Test quality — compliant:** specific value/identity assertions; no vacuous tests; one test's wrong premise corrected by Dev.
- **#3 Type annotations — compliant:** `concede: bool`, `face: tuple|None`, `thrown_faces: tuple|None` all annotated at the boundaries.
- **SOUL "No Silent Fallbacks" — VIOLATION (same instance).** SOUL "Bind the ruleset" — N/A (no ladder math touched). 
- **#2/#4/#5/#7/#8/#9/#10/#12 — N/A** to this diff (no mutable defaults, logging is warning-on-reject, no paths/resources/deserialization/async/imports/deps changes).

### Devil's Advocate
Assume this is broken. The sharpest break is the concede+faces vector: nothing stops a client (buggy, racing, or hostile) from sending `FATE_THROW(action="defend", concede=True, face=(1,1,1,1))`. The validator waves it through; `dispatch_fate_defense` folds the defender and throws the faces away. On the client, the player may have *already watched the 4dF tumble and land* before the concede message won the race — so their screen shows a defense roll while the server recorded a surrender. That is precisely the narration-vs-mechanics divergence the OTEL lie-detector architecture exists to expose, and here it would pass *silently* with a clean `fate.defend_phase(conceded=True)` span and no contradiction logged. A career GM watching the GM panel would see "Rux conceded" while Rux's player swears they rolled — and nothing in the trace explains the discrepancy. Beyond that vector I tried to break it and could not: an unknown `request_id` fails loud; an already-conceded/filled entry fails loud; a concede from the wrong seat fails loud (auth precedes the concede branch); a concede on a proactive verb is rejected at construction; `face=None` on a real defend fails loud at both the validator and the dispatch guard; the conceding defender's `defense_roll` is `None` and `_finish_defense` guards that before broadcasting. Multi-defender rounds (PC-A concedes, PC-B rolls) rely on the 126-8 `ledger_full` logic, which is unit-tested at the dispatch layer — not e2e through the handler, but that is acceptable existing coverage, not a regression. Config/filesystem/timeout angles are N/A (pure in-memory state). Conclusion: one real defect (the silent concede+faces drop), everything else holds.

#### Round-1 audit (history — canonical audit lives in `## Design Deviations → ### Reviewer (audit) — re-review`)
- Architect (scope re-verification) — both entries (server-only re-scope → 126-17; stale YAML `repos` vs authoritative session line) → ✓ ACCEPTED: verified independently — the UI truly has no defend surface and the `pf` CLI has no `--repos` flag; the split is sound.
- TEA (test design) — "wire tests in tests/server/ not tests/handlers/" and "AC-4 covered by a green net" → ✓ ACCEPTED: confirmed `tests/handlers/` autouse `_pg_isolation` would skip without a DB; the AC-4 net is correctly labelled (engine pre-exists from 126-8).
- Dev (implementation) — "corrected a TEA test with a wrong invariant" → ✓ ACCEPTED: verified the `roll_4df` premise was wrong (NPC legitimately rolls at RESUME) and the `resolve_action_from_faces` spy is the correct invariant. "concede restricted to action=defend" → ✓ ACCEPTED: a correct, necessary backdoor-closure within AC-1's intent.
- **Reviewer (audit) — UNDOCUMENTED deviation found:** the concede+faces silent-drop (the HIGH finding) is an undocumented gap between AC-1's "faces optional/ignored" and the No-Silent-Fallbacks boundary requirement. Severity: HIGH. Routed to rework.

**Handoff:** Back to TEA for a RED test on the concede+faces rejection, then Dev for the one-line validator guard.

#### Round-1 code-review finding (RESOLVED in Round 2 — history)
- **Gap (was blocking, now RESOLVED):** `FateThrowPayload._validate_faces` accepted `concede=True` with a non-None `face` and the faces were silently discarded downstream. Fixed by the `fate.py:112-116` guard + the `test_fate_throw_defend_concede_rejects_faces` RED test. *Found by Reviewer (Round 1); closed by Dev rework.*