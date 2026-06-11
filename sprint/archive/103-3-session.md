---
story_id: "103-3"
jira_key: ""
epic: "103"
workflow: "tdd"
---
# Story 103-3: Roll the Bones alt-attribute mode — 3d6-in-order + 2-stat reroll budget

## Story Details
- **ID:** 103-3
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server, ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-11T06:40:46Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-11T05:46:38Z | 2026-06-11T05:48:10Z | 1m 32s |
| red | 2026-06-11T05:48:10Z | 2026-06-11T06:07:13Z | 19m 3s |
| green | 2026-06-11T06:07:13Z | 2026-06-11T06:22:39Z | 15m 26s |
| review | 2026-06-11T06:22:39Z | 2026-06-11T06:28:37Z | 5m 58s |
| red | 2026-06-11T06:28:37Z | 2026-06-11T06:31:15Z | 2m 38s |
| green | 2026-06-11T06:31:15Z | 2026-06-11T06:36:46Z | 5m 31s |
| review | 2026-06-11T06:36:46Z | 2026-06-11T06:40:46Z | 4m |
| finish | 2026-06-11T06:40:46Z | - | - |

## Branches created
- **sidequest-server:** `feature/103-3-roll-the-bones` (from develop)
- **sidequest-ui:** `feature/103-3-roll-the-bones` (from develop)

**Branch Strategy:** gitflow (feature/103-3-roll-the-bones)

## Delivery Findings

No upstream findings at setup. Story context exists at sprint/context/context-story-103-3.md; workflow type verified as phased; tdd routes to red phase (DEV/TDD agent). Both repos (server, ui) in sync with origin/develop; both feature branches created cleanly.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): content adoption of the genre-tier flag is out of this story's repos (server, ui) — mutant_wasteland's real `char_creation.yaml` gains the wager/bones scenes in a later content pass (103-8 or a world story). RED tests run against synthetic packs (`minimal_pack_factory`) through the production loader/dispatch, so engine wiring is fully proven without touching content.
  Affects `sidequest-content/genre_packs/mutant_wasteland/char_creation.yaml` (authoring follow-up, not engine work).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): `RolledStat` carries `{name, value}` totals only; per-die faces reach the player exclusively via the pinned `DiceResultMessage` broadcasts. If the UI later wants faces inside the chargen frame itself, that's an additive payload field — do not widen `RolledStat`.
  Affects `sidequest-server/sidequest/protocol/messages.py` (only if a future story wants in-frame faces).
  *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the chargen DiceResult broadcasts (faces, totals, `chargen.bones.<STAT>` request ids) reach the client but the 3D dice overlay does not yet animate them — the bones step renders numbers. Wiring the existing DiceOverlay replay to these broadcasts is a pure-UI follow-up (103-9/103-10 or a UX pass).
  Affects `sidequest-ui/src/dice/` (subscribe the overlay to chargen-context DiceResult messages).
  *Found by Dev during implementation.*
- **Question** (non-blocking): 23 server tests fail in a bare local shell with no `SIDEQUEST_DATABASE_URL` exported (test_app lifecycle, forensics routes, lore RAG wiring, use_mutation_tool, etc.) — verified IDENTICAL with the 103-3 diff stashed, so pre-existing and environmental, not story regressions. They pass in the properly-configured dev/CI environment per 103-2's preflight (11712 GREEN).
  Affects `sidequest-server/tests/` (no change needed; noted so the Reviewer doesn't re-derive the baseline).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): client-facing chargen errors use `exc!r`, leaking Python exception class names to the wire — systemic house pattern across every arrange/story handler in the file, not bones-specific; a hygiene pass should swap to `str(exc)` (or a normalising helper) file-wide rather than patching two lines inconsistently.
  Affects `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (all `_error_msg(f"...{exc!r}")` call sites).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): should Back-navigation out of an adopted Roll the Bones be narratively acknowledged (the wager scene re-presents with the dice already cast)? Content authors may want wager narration that acknowledges a returning player. Pure authoring consideration once the [HIGH]/[MEDIUM] fixes land.
  Affects `sidequest-content` wager-scene authoring (103-8 or world pass).
  *Found by Reviewer during code review.*

### Reviewer (re-review)
- **Improvement** (non-blocking): replace the two-field idempotency guard in `_enter_roll_the_bones` with a single `_bones_initialized` flag — desync-proof against future partial-init refactors of the bones state block.
  Affects `sidequest-server/sidequest/game/builder.py` (one-flag cleanup; bundle into 103-10's wiring pass).
  *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): add a load-time validation rejecting any scene that carries BOTH `requires_stat_generation` and `mechanical_effects.stat_generation` — the redundant authoring would make confirm→Back orphan the adoption (mode reset by the wrong ledger pop). Loud at load beats subtle at runtime.
  Affects `sidequest-server/sidequest/genre/loader.py` (scene validation; land with 103-8's real content or 103-10).
  *Found by Reviewer during re-review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implementation follows TEA's pinned contract exactly (choice-level adoption + eager roll, requires_stat_generation FILTER gate, replacement-semantics reroll with loud rejections, DiceResult broadcasts via a builder drain queue, SceneResult ledger entry on bones confirm per the 103-2 doctrine).

### TEA (test design)
- **ADR-074 dice path pinned as server-rolled DiceResult broadcasts, not a Request→Throw→Result round-trip**
  - Spec source: context-story-103-3.md, Technical Guardrails + AC-4
  - Spec text: "route through the ADR-074 dice protocol so the rolls are visible/honest, not server-silent. Reuse the existing dice-throw payloads; no new protocol message types."
  - Implementation: tests pin one existing `DiceResultMessage` per stat roll/reroll (3×d6 faces, total == stat, `request_id == "chargen.bones.<STAT>"`), plus `SPAN_CHARGEN_STAT_ROLL` per roll — no `DiceRequest`/`DiceThrow` gesture loop during chargen
  - Rationale: the full ADR-074 loop demands a player throw-gesture per roll; six blocking throws would fight the Alex-paced chargen flow, and ADR-074's interactive loop is confrontation-scoped. The guardrail's intent — visible faces on the wire, mechanically honest, existing payloads only — is fully satisfied by result broadcasts + OTEL
  - Severity: minor
  - Forward impact: 103-10 e2e can tighten to the interactive loop if Keith wants throw-gestures in chargen; UI dice overlay can animate from the same broadcasts
- **Mode selection pinned as a choice scene + gated rolling scene, not a toggle on an existing attribute step**
  - Spec source: context-story-103-3.md, Technical Guardrails + Assumptions
  - Spec text: "the existing attribute step gains a mode toggle" / "if attribute generation is currently UI-implicit, the server becomes authoritative for this mode (log deviation if that shifts behavior)"
  - Implementation: no discrete attribute step exists today (stats generate implicitly at build() per pack default). Tests pin: a chargen choice carrying `stat_generation: "roll_the_bones"` adopts the mode + rolls eagerly; a scene tagged `requires_stat_generation` (mirror of 103-2's `requires_stock`) is the reroll/confirm surface, skip-walked on the default path
  - Rationale: this is the contingency the context itself anticipated; the server becomes authoritative for rolled stats, reusing the 103-2 branching machinery instead of inventing a parallel toggle surface
  - Severity: minor
  - Forward impact: the bones scene is authored data — any pack/world can place or omit it (homebrew-expressible per the Jade requirement)
- **ADR-128 SHA-256 deterministic rolls not pinned**
  - Spec source: context-story-103-3.md, Technical Guardrails
  - Spec text: "Deterministic/resume-safe randomness per ADR-128 conventions if the chargen roll path persists seeds"
  - Implementation: tests pin the builder's existing injectable-RNG convention (seeded `random.Random`) for determinism; no SHA-256 `deterministic_roll()` requirement
  - Rationale: the guardrail is explicitly conditional and chargen does not persist seeds today (the arrange flow has the same property). Pinning ADR-128 here would force a resume-safety layer the live chargen substrate doesn't have
  - Severity: minor
  - Forward impact: if chargen ever becomes mid-flow resumable, rolls should migrate to `sidequest/mutation/rolls.py::deterministic_roll` — flag in that story

### Reviewer (audit)
- **TEA: ADR-074 dice path as DiceResult broadcasts (no gesture loop)** → ✓ ACCEPTED by Reviewer: faces are on the wire via existing payloads + spans; the guardrail's visibility/honesty intent is met, and six blocking throw-gestures would fight the Alex pacing requirement. 103-10 may tighten.
- **TEA: mode selection as choice scene + gated rolling scene** → ✓ ACCEPTED by Reviewer: the context's own contingency clause anticipated server-authoritative generation; reusing the 103-2 FILTER machinery is the right shape. NOTE: the *implementation* of the adoption broke ledger coherence (see [HIGH]) — the design is accepted, the state-anchoring bug is not.
- **TEA: ADR-128 SHA-256 rolls not pinned** → ✓ ACCEPTED by Reviewer: the guardrail is explicitly conditional on seed persistence, which chargen does not have; injectable-RNG determinism matches the arrange-flow precedent.
- **Dev: "No deviations from spec"** → ✗ FLAGGED by Reviewer: the implementation deviates from the pinned contract's *intent* in three repro-confirmed ways the tests didn't pin — stale mode across back-nav (AC-1 violation, [HIGH]), unlocked post-confirm rerolls (contradicts apply_bones_confirm's own "Lock" docstring, [MEDIUM]), and budget-resetting re-adoption ([MEDIUM]). Not logged because the tests passed; the ledger doctrine (103-2) applied regardless. See severity table. → **RESOLVED in rework fb3a1291** — all three fixed and pinned; flag closed at re-review.

### Reviewer (audit — rework deviations, re-review 2026-06-11)
- **TEA rework: no deviations** → ✓ ACCEPTED by Reviewer: the 10 pins land verbatim on the four findings, behavior-pinned not mechanism-pinned.
- **Dev rework: original reroll-fixture updated (bones scene added, confirm before name entry)** → ✓ ACCEPTED by Reviewer: the old fixture rerolled from the name scene, which the review's scene-gate contract makes illegal — maintaining the fixture to the superseding contract is correct, and the rework suite independently pins the gate so the change cannot mask a regression.

## Subagent Results (re-review, 2026-06-11)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 55/55 bones tests (41 builder + 8 dispatch + 6 UI), ruff clean, 0 smells, both repos in sync (fb3a1291 / 84bee47), trees clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — lead re-ran all four repro scripts + two new probes (P4 confirm→back reroll window, P5 double-back ledger undo): all correct |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — security agent enumerated the 3 undo/guard paths under No Silent Fallbacks: compliant |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — 10 rework pins land exactly on the four findings; fixture maintenance audited below |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — lead verified apply_bones_confirm's "Lock" docstring is now TRUE (scene gate enforces it) and reroll_stat/budget docstrings updated |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — no type surface changed in rework beyond a docstring'd property |
| 7 | reviewer-security | Yes | findings | 2 (both low confidence) | deferred 2 with rationale (future-hardening, not present-day defects — recorded as delivery findings) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — rework is 59 net lines, all prescribed |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — lead re-checked the affected rules (No Silent Fallbacks, server-authoritative budget, input validation, error-message scope): compliant |

**All received:** Yes (2 enabled returned; 7 disabled via settings)
**Total findings:** 0 confirmed blocking, 2 deferred (with rationale below), 0 dismissed

## Reviewer Assessment (re-review, 2026-06-11)

**Verdict:** APPROVED

All four prior findings verified fixed in fb3a1291 — each by my own live repro AND the pinned tests:
- [VERIFIED] [EDGE] [HIGH→fixed] Bones→Back→Default now lands on the name scene, budget surface reads None, and build() point-buys (repro R1; pinned by 3 builder tests + 1 wire test). Fix is ledger-driven as prescribed: `_undo_popped_effects` (builder.py, called from both `go_back` and `revert`) keys off `popped.effects_applied.stat_generation` — the same provenance doctrine as 103-2's `scene_index`.
- [VERIFIED] [EDGE] [MEDIUM→fixed] Confirmed arrays lock: reroll off the bones scene raises loud RuntimeError in every probed phase (post-confirm name scene, Confirmation summary, AwaitingFollowup — security agent enumerated all). The over-correction guard passes (rerolls still flow ON the bones scene).
- [VERIFIED] [EDGE] [MEDIUM→fixed] Re-adoption is idempotent: array/budget/once-each ledger survive Back+re-pick, zero new spans/broadcasts (repro R3 + span-capture test). Confirm→Back legitimately reopens the reroll window with the SAME budget (probe P4: 1→0 then RerollBudgetExhaustedError) — coherent, budget never refreshes.
- [VERIFIED] [SEC] [LOW→fixed] Unknown-stat error names the offender only; ability-list oracle gone (security agent confirmed at the new ValueError site).
- [VERIFIED] [SILENT] [RULE] No new silent paths: undo helper is a no-op only for non-bones pops (correct by ledger semantics, not a fallback); all guards raise loud. [TEST] 10 rework pins + fixture maintenance verified discriminating. [DOC] "Lock the array" docstring now true. [TYPE] [SIMPLE] No type or complexity regressions in the 59-line delta.

Deferred (recorded as delivery findings; both low-confidence future-hardening, not present-day defects):
| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [LOW] [SEC] | Idempotency guard is a two-field conjunction (`_bones_budget`/`_rolled_stats`); a future partial-init refactor could bypass it and refresh the budget. A single `_bones_initialized` flag would be desync-proof | builder.py `_enter_roll_the_bones` | Defer — fields initialize atomically today; fold into 103-10's wiring pass |
| [LOW] [SEC] | A pack author who redundantly puts `stat_generation: "roll_the_bones"` on the gated bones scene itself would make confirm→Back reset the mode (orphaned adoption). Engine can't stop the authoring; a loud load-time validation should | genre loader / CharCreationScene validation | Defer — add a load-time rejection (gated scene must not also carry stat_generation) in 103-8/103-10 when the real content lands |

**Data flow traced (delta):** Back click → go_back → pop wager result → `_undo_popped_effects` reads the popped ledger entry's own effects (no re-derivation) → mode restored to `rules.stat_generation` → skip-walk and `generate_stats` both read the restored mode → default pick walks clean. Safe.
**Pattern observed:** good — the fix reads provenance off the popped SceneResult exactly like 103-2's scene_index fix; the builder now has a single undo seam for future apply-time state mutations.
**Error handling:** every rework rejection loud and specific; nothing swallowed (security enumeration).
**Handoff:** To Morpheus (SM) for finish-story.

## Dev Assessment (rework green, 2026-06-11)

**Implementation Complete:** Yes — all four review findings fixed in server commit fb3a1291 (pushed; UI untouched in rework).

**Files Changed:**
- `sidequest/game/builder.py` — (1) [HIGH] `_undo_popped_effects` called from both `go_back` and `revert`: popping a result whose `effects_applied.stat_generation == "roll_the_bones"` restores the pack-default `_stat_generation` — ledger-driven undo as prescribed; (2) [MEDIUM] `reroll_stat` gains the scene gate (phase `InProgress` AND current scene `requires_stat_generation` set) — confirmed arrays lock, pre-adoption/post-confirm/summary rerolls all raise loud; (3) [MEDIUM] `_enter_roll_the_bones` idempotent: existing array/budget/rerolled-set survive re-adoption, zero new rolls/spans/broadcasts; (4) [LOW] unknown-stat ValueError names the offender only; plus `reroll_budget_remaining` made mode-aware (None whenever bones mode inactive — required to satisfy both the [HIGH] surface pin and idempotent preservation).
- `tests/game/test_roll_the_bones_reroll.py` — fixture maintenance: the original two-scene fixture rerolled from the name scene, which the new scene-gate correctly rejects; added the gated bones scene + `apply_bones_confirm()` before name entry in the built-character test. Contract superseded by the review; noted as a rework deviation below.

**Tests:** 49/49 story tests GREEN (41 builder incl. all 10 rework pins + 8 dispatch incl. the wire-level [HIGH] pin). Full server suite: 11741 passed / 21 failed — all within the documented pre-existing environmental family (was 23; xdist variance), zero new failures. Ruff clean.

**Rework deviation (Dev):** updated TEA's original reroll-fixture rather than leaving contradictory pins — the review's scene-gate contract supersedes the phase-1 "reroll anywhere in mode" behavior the old fixture incidentally encoded. No production-behavior deviation from the Reviewer's prescription.

**Branch:** feature/103-3-roll-the-bones @ fb3a1291 (server), 84bee47 (ui) — both pushed.

**Handoff:** To The Merovingian (Reviewer) for re-review.

## TEA Assessment (rework red, 2026-06-11)

**Tests Required:** Yes — pin all four review findings verbatim.

**Test Files (rework):**
- `sidequest-server/tests/game/test_roll_the_bones_review_rework.py` — 10 tests: [HIGH] go_back→default clears bones mode (scene skip + point-buy build + budget None, plus the `revert()` alias); [MEDIUM] reroll locked off the bones scene (post-confirm AND post-summary, array untouched) with an over-correction guard (reroll on the bones scene still works — the one intentional baseline pass); [MEDIUM] idempotent re-adoption (array+budget+rerolled-set survive Back+re-pick, zero new spans/broadcasts, once-each ledger survives); [LOW] unknown-stat error names the offender only
- `sidequest-server/tests/server/test_chargen_roll_the_bones_dispatch.py` — +1 wire test: back action then default choice → no bones frame, no DiceResult broadcasts

**Status:** RED verified by direct run — 9/10 builder-level failing + wire test failing, all on the unfixed bugs (the 1 pass is the over-correction guard, by design). Ruff clean. Committed 13ae3615, pushed.

**Rework deviations:** none — tests pin exactly the Reviewer's prescribed behaviors; the [HIGH] fix mechanism (ledger-driven undo keyed on `popped.effects_applied.stat_generation`) is pinned by behavior, not implementation.

**Handoff:** To Agent Smith (Dev) — fix prescription is in the Reviewer's severity table; note the interplay: undo-on-pop resets `_stat_generation` to the rules default but PRESERVES the bones array/budget so idempotent re-adoption can re-arm it without new rolls.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — mechanical state green (43/43 story tests, ruff/eslint clean, 0 smells, both branches in sync at 55a4dd56 / 84bee47, trees clean) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by lead's own repro-driven edge pass (3 confirmed findings below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — lead enumerated all 6 new error paths under No Silent Fallbacks (Rule Compliance §1) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — lead audited the 43 tests; gap identified: no back-nav re-pick coverage (became the [HIGH]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — lead spot-checked: apply_bones_confirm docstring says "Lock the array" but nothing locks (matches [MEDIUM] #2) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — lead reviewed: additive optional fields, two domain error types subclassing BuilderError, no stringly-typed regressions |
| 7 | reviewer-security | Yes | findings | 3 (all low confidence) | confirmed 1 (as [LOW], folded into rework), deferred 2 (systemic `exc!r` pattern — delivery finding, out of story scope) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — lead reviewed: no dead code, no over-engineering; drain-queue is the minimal broadcast mechanism |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — lead performed the rule-by-rule enumeration (Rule Compliance below) |

**All received:** Yes (2 enabled returned; 7 disabled via settings)
**Total findings:** 5 confirmed (1 my own [HIGH], 2 my own [MEDIUM], 1 my own [MEDIUM]→merged, 1 [LOW] from security), 0 dismissed without rationale, 2 deferred (with rationale)

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [EDGE] | **Stale bones mode survives back-navigation.** Repro (live, seeded): pick Roll the Bones → `go_back()` → pick the DEFAULT choice → builder still has `_stat_generation == "roll_the_bones"`, the gated bones scene is PRESENTED on the default path, and `generate_stats` will use the stale rolled array instead of point-buy. AC-1 ("default unchanged when not selected") is violated on every back-nav path. Root cause: `_enter_roll_the_bones` mutates builder state directly; unlike `chosen_stock_id` (derived from the results ledger), the mode is never undone when the adopting SceneResult is popped. This is the 103-2 regression class — state not anchored to the ledger | builder.py `apply_choice`/`_enter_roll_the_bones`/`go_back`/`revert` | In `go_back`/`revert`, when `popped.effects_applied.stat_generation == "roll_the_bones"`, reset `_stat_generation` to the rules default (snapshot it at construction). Ledger-driven undo, mirroring the scene_index provenance pattern |
| [MEDIUM] [EDGE] | **Reroll accepted off the bones scene.** Repro: after `apply_bones_confirm()` (scene advanced to the name scene — and equally after the confirmation summary renders), `reroll_stat("STR")` still succeeds with leftover budget: 18 → rerolled post-"lock". A raw-WS client can reroll after seeing the summary's derived projections. The docstring says "Lock the Roll the Bones array" — nothing locks it | builder.py `reroll_stat` | Gate `reroll_stat` on phase `InProgress` AND `current_scene().requires_stat_generation is not None`; raise loud RuntimeError otherwise |
| [MEDIUM] [EDGE] | **Full-array reroll fishing via Back + re-pick.** Repro: pick bones → `go_back()` → pick bones again → entire array re-rolled, budget reset to 2. Infinite full-array rerolls make the 2-stat budget decorative and gut the "hopeless characters allowed" register (AC-3/AC-5 spirit). C&C's unlimited `reject_arrangement` is an *authored* escape valve; this one is an accident | builder.py `_enter_roll_the_bones` | Make re-adoption idempotent: roll fresh ONLY when no bones array exists on the builder; otherwise re-arm the mode with the existing array/budget/rerolled-set (no new rolls, no new broadcasts). Combined with the [HIGH] fix, default-revert stays correct and fishing dies |
| [LOW] [SEC] | Unknown-stat `ValueError` embeds the full `ability_score_names` list — a free configuration oracle on invalid probes; for homebrew packs with custom score names that's disclosure beyond need (the valid set is already visible in the bones frame the player owns) | builder.py `reroll_stat` (~line 3047) | Drop the list from the message: `unknown stat '{stat_name}'` suffices |

**Routing:** findings are testable logic bugs → rework via red (TEA pins them, Dev fixes).

### Observations (beyond the findings table)

1. [VERIFIED] [SILENT] No Silent Fallbacks — all six new failure paths are loud and specific: `_render_bones_message` raises on missing state (builder.py diff @1769-1779) rather than re-rolling; `generate_stats` `roll_the_bones` branch raises on missing array instead of defensively re-rolling (contrast: the legacy `roll_3d6_strict` branch keeps a documented defensive re-roll); `reroll_stat` has four distinct loud rejections; `bones_reroll` dispatch returns explicit ErrorMessage on missing stat field. Complies with CLAUDE.md No Silent Fallbacks.
2. [VERIFIED] [SEC] Server-authoritative budget — the 2-cap is enforced in `reroll_stat` before any rng consumption; the UI `disabled` attribute is convenience only; `stat` input is whitelist-validated against pack `ability_score_names` before any state mutation. Security agent confirmed no injection/spoofing vector; DiceResult `seed=0`/zero throw_params are cosmetic replay fields, values authoritative from `_rng`.
3. [VERIFIED] [RULE] OTEL lie-detector — every initial roll AND every reroll fires `SPAN_CHARGEN_STAT_ROLL` with faces+total (`_bones_roll_one` is the single roll site; both call paths route through it), and per-roll DiceResult broadcasts put the faces on the wire. The GM panel can prove every die. Complies with the OTEL Observability Principle.
4. [VERIFIED] [TEST] The 43 tests assert concrete values (seeded replays, scripted RNG faces, exact budget counts) — no vacuous assertions found on my read. The gap is coverage, not quality: no test walks `go_back` around the wager scene, which is precisely where the [HIGH] lives. TEA's rework must pin all three repros.
5. [VERIFIED] [TYPE] Two new domain errors subclass `BuilderError` so the existing dispatch `except BuilderError` taxonomy catches them; payload additions are optional fields (wire-compatible); no stringly-typed regressions. `requires_stat_generation` mirrors `requires_stock`'s shape exactly.
6. [DOC] `apply_bones_confirm` docstring claims "Lock the Roll the Bones array" but no lock exists (see [MEDIUM] #2) — stale-by-construction documentation; the rework fix makes the docstring true. (Folded into [MEDIUM] #2's fix.)
7. [VERIFIED] [SIMPLE] No over-engineering: the broadcast drain-queue is the minimal mechanism for the dispatch fan-out; no dead code introduced; UI branch follows the established input_type-router pattern (CharacterCreation.tsx:283+, mirrors stock/arrange branches).
8. [SEC] (deferred) The `exc!r` → client ErrorMessage pattern leaks Python exception class names. It is the established file-wide house pattern (every arrange/story handler uses it identically), so changing only the bones lines would be inconsistent and changing the file is out of story scope — recorded as a non-blocking delivery finding for a hygiene pass.

### Rule Compliance

| Rule | Instances enumerated | Verdict |
|------|---------------------|---------|
| No Silent Fallbacks (CLAUDE.md) | 6 new error paths (`_render_bones_message`, `apply_bones_confirm` ×2 guards, `generate_stats` bones branch, `reroll_stat` ×4 rejections, `bones_reroll`/`bones_confirm` dispatch) | Compliant — all loud, all specific. The [HIGH] is a *state-coherence* bug, not a silent fallback |
| OTEL Observability Principle | Roll sites: `_bones_roll_one` (sole roller, span per roll); dispatch events `character_creation.bones_reroll`/`bones_confirm`; DiceResult broadcasts | Compliant |
| Every Test Suite Needs a Wiring Test | `test_loader_accepts_roll_the_bones_flags` (production loader) + 6 dispatch tests (production handler chain) + UI wiring via component router test | Compliant |
| python.md #1 silent exceptions | 3 new `except` sites in chargen_mixin — explicit tuples, no bare except, no swallowing | Compliant |
| python.md #2 mutable defaults | All new functions/methods checked — none | Compliant |
| python.md #3 type annotations | All new public methods annotated (`reroll_stat`, `apply_bones_confirm`, `consume_bones_broadcasts`, `_bones_dice_messages`) | Compliant |
| python.md #6 test quality | 43 tests, concrete assertions, `_ScriptedRng` fails loud on exhaustion | Compliant (coverage gap noted in finding table) |
| python.md #8 unsafe deserialization | No pickle/eval/yaml.load in diff; player input via pydantic models | Compliant |
| python.md #11 input validation | `bones_reroll.stat`: None-check at dispatch + whitelist in builder | Compliant (see [LOW] for error-message verbosity) |
| typescript: server-driven UI, no client authority | UI sends ops only; budget/values rendered from payload; disabled-state cosmetic | Compliant |
| SOUL Agency/The Test | UI never auto-commits; hopeless array confirmable without coercion | Compliant |
| Zork Problem (no verb-set reduction) | Chargen is the sanctioned menu surface (103-2 precedent); no play-time NL gated | Compliant |

**Data flow traced:** player clicks "Reroll DEX" → `{phase:"bones_reroll", stat:"DEX"}` → handlers/character_creation.py:105 → `_chargen_bones_reroll` (None-check, span event) → `builder.reroll_stat("DEX")` (mode gate → whitelist → once-each → budget → `_bones_roll_one` rolls/spans/queues) → `_next_message` drains queue → one DiceResultMessage (faces, total, `chargen.bones.DEX`) + refreshed bones frame (new value, decremented budget). Safe except for the scene-gating gap in [MEDIUM] #2.

**Pattern observed:** good — `requires_stat_generation` reuses the 103-2 FILTER skip-walk and `apply_bones_confirm` records a ledger SceneResult with `scene_index` provenance (builder.py diff @2266+). Bad — the *mode adoption itself* broke the same ledger doctrine the confirm honored: `_stat_generation` is mutated state with no ledger anchor, which is exactly how the [HIGH] got in.

**Error handling:** all new paths loud (see Rule Compliance §1); client-facing `exc!r` verbosity deferred as systemic.

### Devil's Advocate

Assume this code is broken and the table is full of Sebastiens. What does a mechanics-first player with a WebSocket inspector do? First, they probe `bones_reroll` with garbage — the whitelist holds, but the error answer recites the entire ability-score configuration, which on a homebrew pack is information the author may not have surfaced yet ([LOW], confirmed). Second, they notice "Go Back" exists on every scene. They pick Roll the Bones, see a mediocre array, hit Back, and pick it again — fresh array, fresh budget, forever. The 2-reroll budget that the story exists to enforce is now a suggestion; Gamma World's "hopeless character" covenant is dead on arrival ([MEDIUM] #3, repro-confirmed). Third, the confused-user case: a cautious player picks Roll the Bones just to *look*, recoils, hits Back, and chooses the Measured Path — and the engine quietly keeps them in bones mode, marches them into the bones scene, and builds their character from dice they explicitly walked away from. That is not a hypothetical: my seeded repro prints `after DEFAULT pick: the_bones gen= roll_the_bones`. It is the single worst outcome this feature could produce, because it violates the player's explicit choice — SOUL's The Test fails ([HIGH], blocking). Fourth, the post-confirm window: confirm the bones, read the confirmation summary's derived projections, then spend leftover budget from the name scene via raw WS ([MEDIUM] #2, repro-confirmed). What about double-confirm replay? Guarded — the second confirm lands on a non-bones scene and raises. Race conditions? The session handler is single-threaded per connection; the drain-queue cannot double-broadcast because `consume_bones_broadcasts` swaps the list atomically within that model. Huge inputs? `stat` is whitelist-checked before use. The devil found three real things; they are all in the findings table.

**Handoff:** Back through red — The Architect (TEA) pins the three repros as failing tests, Agent Smith (Dev) fixes. Prescribed fixes are in the table; the [HIGH] fix must be ledger-driven (undo on pop), not a special-case flag.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server, `feature/103-3-roll-the-bones` @ 55a4dd56, pushed):**
- `sidequest/genre/models/character.py` — `CharCreationScene.requires_stat_generation` (FILTER gate field, mirrors `requires_stock`)
- `sidequest/game/builder.py` — `RerollBudgetExhaustedError`/`StatAlreadyRerolledError`; bones state (`_bones_budget`, `_bones_rerolled`, broadcast queue); `_bones_roll_one`/`_enter_roll_the_bones`/`reroll_stat`/`reroll_budget_remaining`/`consume_bones_broadcasts`; choice-level adoption hook in `apply_choice`; `roll_the_bones` branch in `generate_stats` (loud on missing rolls, no clamping); gen-gate in `_advance_scene` skip-walk; `_render_bones_message` frame; `apply_bones_confirm` with SceneResult ledger entry
- `sidequest/protocol/messages.py` — `CharacterCreationPayload.reroll_budget_remaining`
- `sidequest/handlers/character_creation.py` — `bones_reroll`/`bones_confirm` phase dispatch
- `sidequest/server/websocket_handlers/chargen_mixin.py` — `_chargen_bones_reroll`/`_chargen_bones_confirm`; `_bones_dice_messages` ADR-074 DiceResult fan-out drained in `_next_message`

**Files Changed (ui, `feature/103-3-roll-the-bones` @ 84bee47, pushed):**
- `src/components/CharacterCreation/CharacterCreation.tsx` — `roll_the_bones` branch: six stat rows in payload order, per-stat reroll buttons (disabled at 0 budget), budget counter, explicit "Keep These Bones" confirm
- `src/types/payloads.ts` — `reroll_budget_remaining` on the chargen payload type

**Tests:** 43/43 story tests passing (31 builder + 7 dispatch + 6 UI). Full suites: UI 2077/2077 + `npm run build` clean; server 11728 passed / 23 failed — the 23 verified pre-existing environmental (identical with the diff stashed; bare shell lacks `SIDEQUEST_DATABASE_URL`, see Delivery Findings). Ruff clean + formatted on all changed files. Dispatch tests run against throwaway Postgres via the suite-standard `_pg_isolation`/`migrated_db` fixtures (`SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest_test`).

**Branch:** feature/103-3-roll-the-bones (pushed in server + ui)

**Handoff:** To The Architect (TEA) for verify (simplify + quality-pass).

## TEA Assessment

**Tests Required:** Yes
**Reason:** New chargen mechanic across server + UI; five ACs, all mechanically observable.

**Test Files:**
- `sidequest-server/tests/game/test_builder_roll_the_bones.py` — mode adoption, 3d6-in-order seeded correctness, 3–18 range, hopeless-array no-clamp, stat-bonus additivity, `requires_stat_generation` skip-walk + go_back ledger (the 103-2 [HIGH] regression class), SPAN_CHARGEN_STAT_ROLL per stat (12 param cases + 9 tests)
- `sidequest-server/tests/game/test_roll_the_bones_reroll.py` — replacement semantics (lower roll stands), 2→1→0 budget, third-stat/same-stat/unknown-stat/out-of-mode loud rejections, rerolled values reach build(), reroll span (9 tests)
- `sidequest-server/tests/server/test_chargen_roll_the_bones_dispatch.py` — WIRING: production loader accepts the new flags from a synthetic pack; full dispatch path (connect → choice → bones frame `input_type="roll_the_bones"` + `reroll_budget_remaining` → `bones_reroll`/`bones_confirm` ops → DiceResultMessage visibility per AC-4 → ErrorMessage on budget exhaustion) (7 tests)
- `sidequest-ui/src/components/CharacterCreation/__tests__/CharacterCreation.roll-the-bones.test.tsx` — six stats in order with values (Sebastien/Jade legibility), per-stat reroll buttons, budget display, explicit confirm (Alex pacing), disabled rerolls at 0 budget, hopeless array confirmable (6 tests)

**Tests Written:** 43 covering 5 ACs (+ wiring + ledger regression pins)
**Status:** RED verified by direct run — server: 36 failed / 2 passed (`-n0`; the 2 passes are intentional baseline pins: default point-buy untouched, UnknownStatGenerationError stays loud), UI: 6/6 failed. Failure reasons spot-checked: pydantic `extra_forbidden` on `requires_stat_generation` (schema gap), `AttributeError: reroll_budget_remaining` (API gap), eager-roll assertion (behavior gap) — all fail on the missing feature, none on fixtures. Ruff clean (new files formatted). Note for Agent Smith: ran pytest/vitest directly per standing memory (testing-runner clobbers the session file and fabricates per-test prose); session backup at /tmp/103-3-session.backup.md.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (#1 silent exceptions) | `test_third_distinct_stat_rejected`, `test_same_stat_twice_rejected_and_burns_no_budget`, `test_unknown_stat_rejected_loudly`, `test_reroll_outside_bones_mode_rejected`, `test_third_reroll_rejected_over_wire`, `test_unknown_stat_generation_still_raises` | failing (except the last — baseline pin, passing) |
| Wiring test mandate | `test_loader_accepts_roll_the_bones_flags` + all 6 dispatch tests (production loader → handler → builder) | failing |
| OTEL Observability Principle | `test_roll_fires_stat_roll_span_per_stat`, `test_reroll_fires_stat_roll_span`, dice-broadcast assertions | failing |
| #6 test quality (no vacuous asserts) | self-checked: every test asserts concrete values; `_ScriptedRng` explodes on exhaustion; no `assert True`/bare truthy | n/a |
| The Test / Agency (SOUL) | `test_hopeless_array_stands`, UI hopeless-confirm test — system never "helps" uninvited | failing |
| Zork Problem guard | chargen is the sanctioned menu surface (103-2 precedent); no play-time verbs gated | n/a |

**Rules checked:** 13-point python checklist reviewed; checks without new-surface relevance (deps, async, paths) have no applicable code in test-only diff
**Self-check:** 0 vacuous tests found

**Handoff:** To Agent Smith (Dev) for GREEN. The contract is fully specified in the three docstring headers; mirror `requires_stock`/`arrange_*` precedents. Key construction sites: `MechanicalEffects.stat_generation` adoption in `apply_choice` (builder.py:1805), `_advance_scene` gate (builder.py:3060), `to_scene_message` frame upgrade, `chargen_mixin` ops, `CharacterCreationPayload.reroll_budget_remaining`, UI `input_type === "roll_the_bones"` branch.

## Sm Assessment

**Setup complete.** Story 103-3 is a small, independent chargen feature (Roll the Bones alt-attribute mode: 3d6-in-order, 2-stat reroll budget, UI affordance). Story context validates; workflow tdd is phased; Jira integration skipped per empty jira_key. Both repos (server, ui) on sync'd develop; feature branches created. Ready for red phase (dev/TDD agent).