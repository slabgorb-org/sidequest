---
story_id: "118-9"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 118-9: ADR-119/ADR-047 hardening: audit dice_throw seat-auth (mirrors the 118-8 spoof pattern) + sanitize target/aspect_text at the Fate seal site

## Story Details
- **ID:** 118-9
- **Jira Key:** (none — Jira not in use)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p2
- **Repo:** server
- **Branch:** feat/118-9-dice-throw-seat-auth-hardening
- **Branch Strategy:** gitflow (feat/118-9-dice-throw-seat-auth-hardening)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T04:20:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T03:35:56Z | 2026-06-17T03:37:32Z | 1m 36s |
| red | 2026-06-17T03:37:32Z | 2026-06-17T03:50:08Z | 12m 36s |
| green | 2026-06-17T03:50:08Z | 2026-06-17T04:05:02Z | 14m 54s |
| review | 2026-06-17T04:05:02Z | 2026-06-17T04:20:46Z | 15m 44s |
| finish | 2026-06-17T04:20:46Z | - | - |

## Sm Assessment

**Routing:** Selected from backlog as the lead p2 — the only available story carrying a latent **security exposure** rather than pure tech debt. tdd phased workflow → handing to TEA for RED.

**Scope — three bundled ADR-119/ADR-047 findings, server repo only:**

1. **AC1 — dice_throw seat-auth audit (potential HIGH).** `DiceThrowHandler` (`sidequest/handlers/dice_throw.py`) is the explicit handler `FateActionHandler` was modeled on ("mirrors DiceThrowHandler" docstring). The 118-8 review confirmed `FateActionHandler` carried a seat-spoof via the auth-trust idiom `getattr(msg, "player_id", "") or sd.player_id`. **Audit dice_throw for the same idiom; if present, mirror the 118-8 fix.** This is the load-bearing item — same class as the p1 118-8 fix.

2. **AC2 — fate_conflict `target` sanitization (MEDIUM).** In `sidequest/server/dispatch/fate_conflict.py`, `payload.target` is sealed RAW onto `FateSealedCommit` beside the now-sanitized `skill`. Active exploit path is narrow (`_resolve_attack` raises at `find_creature_core(commit.target)` before the narrator hint at ~:521-547), but apply `sanitize_player_text` at the seal site for consistency.

3. **AC3 — fate_conflict `aspect_text` sanitization (LOW/latent).** Same file. Already sanitized at the hint producer (`_resolve_create_advantage` 590/606) and prompt projection (`fate_projection.py:65`); raw survives only on the F3a display-only projection. Apply `sanitize_player_text` at the seal site — defense-in-depth parity with the 118-8 skill fix.

**Reference pattern:** The 118-8 fix is the model for both the auth idiom and the `sanitize_player_text` application. TEA should write the auth-audit test first (it determines whether AC1 is a real HIGH or a confirmed-clean no-op) before the two sanitization tests.

**Jira:** Not configured for this project — explicitly skipped, not an oversight.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (verified — 5 fail on assertions, 6 regression guards green, 0 collection errors)

**Audit verdict (AC1):** CONFIRMED. `dice_throw.py:78` carries the exact 118-8 spoof idiom and `rolling_player_id` drives the seat-map lookup — a real HIGH, same class as the p1 118-8 fix. AC1 is an implement, NOT a document-and-close.

**Test Files:**
- `tests/server/test_dice_throw_auth_bypass_118_9.py` — AC1 dice_throw seat-auth net (6 tests). Drives the REAL `DiceThrowHandler`; `dispatch_dice_throw` is monkeypatched to capture its `rolling_player_id`/`character_name` kwargs (the seat-resolution boundary) and short-circuit before narration.
- `tests/server/test_fate_seal_sanitization_118_9.py` — AC2/AC3 Fate seal-site sanitization net (5 tests). Drives the REAL `FateActionHandler`; barrier held open with a second un-acting PC so the sealed commit persists for inspection.

**Tests Written:** 11 tests covering 3 ACs.

| # | Test | Maps to | Today |
|---|------|---------|-------|
| 1 | dice: spoofed id rolls as authenticated PC, not victim | AC1 | RED |
| 2 | dice: spoofed id never rolls as victim (invariant) | AC1 | RED |
| 3 | dice: spoofed id emits fate_action-style spoof watcher event | AC1 (OTEL) | RED |
| 4 | dice: authenticated player rolls as own seat (not characters[0]) | AC1 regression | green |
| 5 | dice: empty inbound id → authenticated seat | AC1 regression | green |
| 6 | dice: matching inbound id emits NO spoof event | AC1 regression | green |
| 7 | fate: malicious attack target sanitized at seal site | AC2 | RED |
| 8 | fate: clean attack target preserved unmangled (lookup-key integrity) | AC2 regression | green |
| 9 | fate: passive action preserves None target (None→"" tripwire) | AC2 regression | green |
| 10 | fate: malicious aspect_text sanitized at seal site | AC3 | RED |
| 11 | fate: clean aspect_text preserved unmangled | AC3 regression | green |

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #11 input validation at boundaries — seat auth | tests 1–3 | failing (RED) |
| #11 input validation at boundaries — injection sanitization | tests 7, 10 | failing (RED) |
| #11 None-handling at the sanitize boundary | test 9 (tripwire) | passing |
| #6 test quality — anti-vacuous oracle | `assert expected != malicious` guards (tests 7, 10) | self-check pass |

**Rules checked:** #11 (input validation at boundaries) is the load-bearing rule for this security story — covered by both the auth net and the sanitization net. #6 test-quality self-check ran clean.
**Self-check:** 0 vacuous assertions found (grep-verified: no `assert True`, no truthy-only oracles, both injection tests guard against a no-op sanitizer).

**Handoff:** To Dev (Naomi Nagata) for implementation. Mirror `fate_action.py:69-91` for AC1 (drive seat from `sd.player_id` sole-source + emit the spoof event); apply `sanitize_player_text` at the Fate seal site for AC2/AC3, guarding the None case (see Delivery Findings).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/handlers/dice_throw.py` — AC1: seat resolution now driven by `sd.player_id` (the Cf-Access authenticated identity) as the SOLE source; a disagreeing non-empty inbound `msg.player_id` emits a `dice_throw_player_id_spoof_rejected` watcher event (warning, component=session) and the roll proceeds as the authenticated PC. Mirrors `fate_action.py:69-91`.
- `sidequest/server/dispatch/fate_conflict.py` — AC2/AC3: `payload.target` (None-guarded) and `payload.aspect_text` sanitized via `sanitize_player_text` at the seal site, joining the 118-8 `skill` sanitization — one consistent posture across all three sealed player-text fields. Hint-time + projection-time aspect sanitization kept as defense-in-depth.

**Tests:** 11/11 new 118-9 tests GREEN; 33/33 touched-handler regression tests GREEN (including the 118-8 sibling `test_fate_action_auth_bypass.py`). Both changed files lint clean (ruff). Full-suite regression check via stash-comparison: 90 failed with my fix reverted → 85 with it applied — the 5-test delta is exactly my RED→GREEN tests, so **zero regressions**. The ~85 remaining failures are pre-existing (WWN ruleset integration + llm_factory monkeypatching), independent of these two files.

**Branch:** feat/118-9-dice-throw-seat-auth-hardening (pushed)

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (17/17 tests pass, ruff clean, 1 pre-existing pyright err outside changed region) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — edge domain assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — silent-failure domain assessed by Reviewer |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (all low) | confirmed 0, dismissed 0, deferred 3 (non-blocking coverage suggestions) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 2 (LOW DOC), dismissed 0, deferred 1 (pre-existing docstring, out of scope) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type domain assessed by Reviewer |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — **security domain assessed by Reviewer directly** (security story) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — simplicity assessed by Reviewer |
| 9 | reviewer-rule-checker | Yes | findings | 2 (both high-confidence) | confirmed 0, **dismissed 2 with evidence**, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled; disabled domains assessed by Reviewer)
**Total findings:** 2 confirmed (both LOW DOC), 2 dismissed with evidence, 4 deferred (non-blocking suggestions)

## Reviewer Assessment

**Verdict:** APPROVED

Three bundled ADR-119/ADR-047 findings, all fixed correctly and minimally. The code is sound, tested (11 new + 33 regression green), and lint-clean. No Critical/High issues. The confirmed findings are LOW (comment precision) and the dismissed ones were rule-checker false positives debunked empirically. The **security** subagent was disabled on a security story, so I assessed the security/edge/type/silent-failure/simplicity domains myself.

**Data flow traced:** inbound `msg.player_id` (client-controlled) → previously drove `snapshot.player_seats.get(...)` seat lookup → another seat's PC. Now: inbound id is quarantined to a read-only spoof comparison; `rolling_player_id = sd.player_id` (server-authenticated) is the sole driver of seat resolution and all downstream attribution. Safe.

### Observations

- **[SEC][VERIFIED] AC1 closes the seat-spoof at the sole source** — `dice_throw.py:91` sets `rolling_player_id = sd.player_id` unconditionally; inbound id is only read for the `!=` comparison (line 93), never assigned to seat-driving state. Every downstream use (seat lookup ~127, `DiceResultPayload.rolling_player_id` ~177, dispatch kwarg ~305) now flows from the authenticated id. Complies with ADR-119. Mirrors the approved 118-8 `fate_action.py:69-91` exactly (same event field shape; channel-specific `op`/`source`).
- **[SEC][VERIFIED] AC2/AC3 complete the seal-site sanitization** — all three free-text fields on `FateSealedCommit` (skill/target/aspect_text) are now `sanitize_player_text`-cleaned at the seal site (`fate_conflict.py:895/907/911`). `actor` is server-resolved, `action` is a validated Literal, the rest are ints — so the player-text attack surface on the commit is fully covered. Complies with ADR-047.
- **[SILENT][VERIFIED] No silent fallback in the spoof path** — a detected spoof emits `logger.warning` + a `dice_throw_player_id_spoof_rejected` watcher event (warning, component=session) and proceeds as the authenticated PC. The proceed-as-authenticated choice is loud (GM-panel visible), mirrors the approved 118-8 precedent, and is the gentler UX for a misconfigured client. Satisfies No Silent Fallbacks + the OTEL Observability Principle.
- **[EDGE][VERIFIED] None-target guard is correct and the averted bug is worse than the comment says** — `target=(sanitize_player_text(payload.target) if payload.target is not None else None)` preserves the passive-action sentinel. Without the guard, a passive action's `None` would coerce to `""` and `_opposition_total` would call `_roll_defense("")` → `find_creature_core("")` → None → `rating=0` → a **silent 0-rated defense roll** (not a raise), i.e. a silent wrong-mechanics result — exactly what No Silent Fallbacks forbids. The guard is even more justified than its comment claims. `test_passive_action_preserves_none_target` pins it.
- **[EDGE][VERIFIED] target-sanitization does not break legitimate attack resolution** — `commit.target` is the `find_creature_core` lookup key in `_resolve_attack`. `sanitize_player_text` is idempotent on clean names (no tags, no double-spaces) so legitimate targets resolve unchanged; a malicious name is neutralized and the attack raises loud at the no-Fate-sheet check (`fate_conflict.py:503-504`) — defense-in-depth, no injection reaches the LLM.
- **[TYPE][VERIFIED] conditional expression is type-correct** — the `str | None` result matches `seal_fate_commit(target: str | None = None)`. No new stringly-typed surface; no unsafe cast.
- **[SIMPLE][VERIFIED] minimal, pattern-faithful** — both fixes mirror existing approved code (118-8 auth block; the 118-8 skill sanitization). No new abstractions, no scope creep. 40 lines total.
- **[DOC][LOW] `fate_conflict.py` comment overstates the averted failure as "→ raises"** (comment-analyzer, high confidence on inaccuracy). For the passive path the coercion produces a silent 0-rated defense roll, not a raise (the raise only occurs on the attack path). CONFIRMED — non-blocking; recommend tightening the comment. The code is correct.
- **[DOC][LOW] `fate_conflict.py` comment presents `sanitize_player_text(None) → ""` as a contract** (comment-analyzer). The function is typed `str → str`; the `""` is a falsy short-circuit, not a documented guarantee. Could mislead a future reader to drop the guard. CONFIRMED — non-blocking; recommend rephrasing to "guard None explicitly because the function is typed str→str."
- **[TEST][LOW] coverage suggestions** (test-analyzer, all low): (a) dogfight sub-branch spoof attribution untested — but the spoof check fires before that branch and dogfight attribution comes from a prior-turn stash, not the current spoofable msg, so no new vector; (b) clean-target test uses `"Mook"` not a seated `"Rival"`; (c) no non-existent-seat (`"p99"`) spoof test. All deferred as non-blocking — the security invariant is already pinned by the seated-spoof tests.
- **[RULE][DISMISSED] missing `# noqa: PLC0415` on the function-local import** (rule-checker, high confidence) — DISMISSED: `ruff check` passes clean (exit 0); PLC0415 is **not** in this project's selected ruleset (`["E","F","I","UP","B","SIM"]`); the reference `fate_action.py` does the identical local import with no noqa and passes lint. False positive.
- **[RULE][DISMISSED] `Iterator[...]` fixture annotation will fail pyright** (rule-checker, high confidence) — DISMISSED: pyright did NOT flag the fixture annotation; the 12 test-file pyright errors are the SimpleNamespace + concrete-message handler-test-double idiom, **identical to the merged/approved 118-8 sibling test** (12 errors there too). The project type-checks production files only. False positive; pattern is established.

### Rule Compliance (lang-review/python.md, applied to the changed code)

| Rule | Applies to | Verdict |
|------|-----------|---------|
| #1 silent exceptions | spoof branch, seal site | PASS — no try/except, spoof surfaced loudly |
| #3 type annotations | conditional expr, handler sig | PASS — `str\|None` matches signature |
| #4 logging coverage/level | spoof `logger.warning` | PASS — warning (client-input event), lazy `%s`, no secrets |
| #6 test quality | 11 new tests | PASS — anti-vacuous guards, behavioral assertions, no skips |
| #10 import hygiene | function-local `publish_event` import | PASS — consistent with file convention; ruff clean (PLC0415 not selected) |
| #11 input validation at boundaries | both fixes | PASS — this IS the fix (auth identity + sanitization) |
| ADR-119 (auth identity drives seat) | dice_throw.py | PASS — sole-source `sd.player_id`, inbound quarantined |
| ADR-047 (sanitize player text) | fate_conflict.py | PASS — all three free-text seal fields sanitized |
| OTEL Observability | spoof path | PASS — `dice_throw_player_id_spoof_rejected` watcher event emitted |
| No Source-Text Wiring Tests | 11 new tests | PASS — drive real registered HANDLERs, assert behavior/spans |

### Devil's Advocate

Let me argue this code is broken. **First attack: can a client still spoof a seat?** The inbound id is read at line 93 only for the `!=` comparison — but what if `sd.player_id` itself is attacker-influenced? No: `sd.player_id` is the Cf-Access identity bound at connect (ADR-119), not derived from any per-message field, so the sole source is trustworthy. **Second: the dogfight sub-branch.** It attributes the `DiceResultPayload` via `pending_df.player_actor_name`, not the freshly-resolved seat — could an attacker authenticated as p1 consume p2's pending shot? The pending stash is per-`sd` and the shot resolution is keyed on shooter roles, not player identity; this is pre-existing behavior untouched by 118-9 and not a seat-spoof of the *roll attribution* the story scopes. Worth a future hardening note, not a blocker. **Third: sanitizing the target breaks a real fight.** If a legitimate creature were named with a literal `<system>` tag or double-spaces, `sanitize_player_text` would mangle the lookup key and the attack would raise. But genre/world content does not name actors with prompt-injection tokens (and if it did, that content is itself the bug); clean names are idempotent. **Fourth: the None guard is wrong.** If `payload.target` arrived as `""` (empty string, not None) from a malformed client, the guard's `is not None` lets `""` through to `sanitize_player_text("")` → `""` → sealed as `""` — which `_opposition_total` then treats as a real (0-rated) defender. But that is a pre-existing wire-shape concern (the client UI sends `None` for passive actions, not `""`), identical to the pre-fix behavior, and out of 118-9 scope. **Fifth: a confused user.** A legitimately reconnecting client that re-sends a stale `player_id` matching its own seat triggers no event (the `inbound == authenticated` path is silent); a mismatch only ever downgrades to the authenticated seat plus a warning — never escalates privilege. Nothing the devil found rises above LOW. The fix holds.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): AC1's "if the audit finds it already safe, document why and close that AC" branch does NOT apply — the audit CONFIRMED the spoof. `dice_throw.py:78` carries the live idiom `getattr(msg, "player_id", "") or sd.player_id` and `rolling_player_id` drives the seat-map lookup at `:92-93`, so a spoofed inbound id resolves another seat's PC. Affects `sidequest/handlers/dice_throw.py` (Dev must IMPLEMENT the fix mirroring `fate_action.py:69-91`, not close AC1 as already-safe). *Found by TEA during test design.*
- **Improvement** (non-blocking): `sanitize_player_text(None)` returns `""` (not None), so a naive `sanitize_player_text(payload.target)` at the Fate seal site would coerce a passive action's `target=None` into `""`, flipping it into a broken active action (`_opposition_total` treats a non-None target as a real defender → `find_creature_core("")` raises). Affects `sidequest/server/dispatch/fate_conflict.py` (Dev must guard None, e.g. `sanitize_player_text(payload.target) if payload.target is not None else None`). The `test_passive_action_preserves_none_target` tripwire guards it. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved (AC1 audit):** the seat-spoof was confirmed and fixed in `dice_throw.py` (TEA's blocking Conflict — done, not closed-as-safe). The None-coercion landmine (TEA's Improvement) was guarded with `sanitize_player_text(payload.target) if payload.target is not None else None`; `test_passive_action_preserves_none_target` is green. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the full server suite carries ~85 pre-existing failures unrelated to this story (WWN ruleset integration + llm_factory monkeypatching). Confirmed independent of the 118-9 change via stash-comparison (they persist with my fix reverted). Flagging so the full-suite count doesn't read as a 118-9 regression. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): two comments in `fate_conflict.py` (the new 118-9 seal-site block) are imprecise — "→ raises" overstates the averted passive-path failure (it is a *silent* 0-rated defense roll, not a raise), and "`sanitize_player_text(None)` returns ''" reads as a contract when the function is typed `str → str`. Affects `sidequest/server/dispatch/fate_conflict.py` (tighten the two comment lines; code is correct). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): handler test-doubles (SimpleNamespace + concrete message types passed to `msg: GameMessage`) generate ~10-12 pyright errors per file — an established codebase pattern (identical on the merged 118-8 sibling), not specific to 118-9. Affects `tests/server/` broadly; a typed test-double base or `cast()` helper would clean it up project-wide if ever desired. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `DiceThrowHandler` class docstring claims "Returns []" but error paths return non-empty lists — PRE-EXISTING, not touched by this diff. Affects `sidequest/handlers/dice_throw.py:25` (docstring accuracy, opportunistic cleanup). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (0 Gap, 1 Conflict, 0 Question, 2 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Conflict:** AC1's "if the audit finds it already safe, document why and close that AC" branch does NOT apply — the audit CONFIRMED the spoof. `dice_throw.py:78` carries the live idiom `getattr(msg, "player_id", "") or sd.player_id` and `rolling_player_id` drives the seat-map lookup at `:92-93`, so a spoofed inbound id resolves another seat's PC. Affects `sidequest/handlers/dice_throw.py`.

- **Improvement:** two comments in `fate_conflict.py` (the new 118-9 seal-site block) are imprecise — "→ raises" overstates the averted passive-path failure (it is a *silent* 0-rated defense roll, not a raise), and "`sanitize_player_text(None)` returns ''" reads as a contract when the function is typed `str → str`. Affects `sidequest/server/dispatch/fate_conflict.py`.
- **Improvement:** the `DiceThrowHandler` class docstring claims "Returns []" but error paths return non-empty lists — PRE-EXISTING, not touched by this diff. Affects `sidequest/handlers/dice_throw.py:25`.

### Downstream Effects

Cross-module impact: 3 findings across 2 modules

- **`sidequest/handlers`** — 2 findings
- **`sidequest/server/dispatch`** — 1 finding

### Deviation Justifications

1 deviation

- **AC2 target-sanitization tested at the seal site only**
  - Rationale: The story title and SM assessment both direct the seal-site fix; spec-authority places story scope above the context AC's parenthetical alternative. Seal-site also matches the 118-8 `skill` fix this story mirrors (one consistent defensive posture across all three sealed fields).
  - Severity: minor
  - Forward impact: If Dev implements the hint-site alternative instead, `test_malicious_attack_target_is_sanitized_at_seal_site` fails. Dev must implement at the seal site (the directed choice) or log a counter-deviation.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC2 target-sanitization tested at the seal site only**
  - Spec source: context-story-118-9.md, AC2
  - Spec text: "sanitize payload.target via sanitize_player_text at the seal site in dispatch_fate_action (or commit.target at the _resolve_attack hint sites)"
  - Implementation: Tests assert the STORED `commit.target` is sanitized (the seal-site choice); the hint-site alternative is not exercised.
  - Rationale: The story title and SM assessment both direct the seal-site fix; spec-authority places story scope above the context AC's parenthetical alternative. Seal-site also matches the 118-8 `skill` fix this story mirrors (one consistent defensive posture across all three sealed fields).
  - Severity: minor
  - Forward impact: If Dev implements the hint-site alternative instead, `test_malicious_attack_target_is_sanitized_at_seal_site` fails. Dev must implement at the seal site (the directed choice) or log a counter-deviation.

### Dev (implementation)
- No deviations from spec. Implemented exactly as the story title, SM assessment, and TEA's tests directed: AC1 mirrors `fate_action.py:69-91` (`sd.player_id` sole-source + spoof watcher event); AC2/AC3 sanitize at the Fate seal site (the directed choice — confirms TEA's seal-site deviation rather than taking the hint-site alternative), with the `None` guard on `target`.

### Reviewer (audit)
- **TEA — "AC2 target-sanitization tested at the seal site only"** → ✓ ACCEPTED by Reviewer: the story title and SM assessment both direct the seal-site fix; spec-authority correctly places story scope above the context AC's parenthetical hint-site alternative. Dev implemented the seal-site choice, so the test and implementation agree. Sound.
- **Dev — "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed against the diff — AC1 mirrors the approved 118-8 pattern, AC2/AC3 sanitize at the directed seal site with the None guard. No undocumented divergence found.
- No undocumented deviations spotted during review.