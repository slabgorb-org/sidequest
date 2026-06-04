---
story_id: "59-32"
jira_key: ""
epic: "59"
workflow: "tdd"
---
# Story 59-32: Shared is_player_victory() classifier — opponent_yielded/surrender/rout inherit player_victory rewards

## Story Details
- **ID:** 59-32
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Priority:** p3
- **Type:** refactor

## Story Context

**Predecessor:** Story 59-31 (DONE) implemented the opponent-yield outcome signal with deterministic engine-checked confirmation (opponent_yield_outcome() → player_victory when all opponent-side actors are withdrawn/surrendered). The three resolution paths are:

1. **dial_threshold_outcome()** — player achieves a dial threshold → player_victory
2. **opponent_yield_outcome()** — opponent yields/surrenders → player_victory
3. **location_change_without_threshold()** — party leaves with no threshold met and no opponent yield → abandoned_on_location_change

**The Refactor:** Story 59-31 established outcome='opponent_yielded' resolves AS player_victory for reward/credit purposes, treating it identically to beat/dial player_victory. However, the reward logic (award_turn_xp, any future victory-keyed advancement) currently checks `outcome == 'player_victory'` explicitly, requiring three separate code paths to emit player_victory:

- from dial_threshold_outcome()
- from opponent_yield_outcome()
- from location-change edge case (if threshold met on location change, per PR #576)

Additionally, the broader semantics are:
- player_victory (the outcome label)
- opponent_yielded → resolves player_victory (the mapping)
- opponent_victory (inverse, not in scope here)
- abandoned (genuine walk-away)
- yielded (player-side only, loss)

**This story extracts a shared is_player_victory() classifier that consolidates these outcome-resolution mappings into ONE place.** All three mechanical paths (dial, opponent_yield, location/threshold) set enc.outcome to their mechanical-truth label (player_victory / opponent_yielded / opponent_victory), then the classifier maps those labels to True/False for reward consumption. This is a refactoring that unifies outcome interpretation — no behavior change, only code clarity and DRY.

## Technical Approach

1. **Extract is_player_victory(outcome: str) → bool classifier** into StructuredEncounter or a standalone module (game/encounter_classifier.py per project decomposition pattern).
   - Maps outcome → boolean: player_victory | opponent_yielded | (any future victory equiv) → True
   - Maps outcome → boolean: abandoned | yielded | opponent_victory | (non-victory states) → False
   - Single source of truth for victory logic

2. **Wire the classifier into reward/advancement paths** (dispatch/encounter_lifecycle.py award_turn_xp and any future victory-keyed mechanics):
   - Replace `if outcome == 'player_victory':` with `if is_player_victory(outcome):`
   - Ensures opponent_yielded gets the same advancement credit as dial-threshold player_victory (parity contract from 59-31 XP decision)

3. **Update three mechanical outcome-emission sites** to use the classifier conceptually:
   - dial_threshold_outcome() → emits 'player_victory' (highest priority)
   - opponent_yield_outcome() → emits 'opponent_yielded' (maps to victory via classifier)
   - location-change boundary → emits 'abandoned' or 'player_victory' or 'opponent_yielded' (already uses the classifier's logic, tighten the mapping)

4. **No OTEL changes** — the existing outcome OTEL spans remain unchanged (resolution_label='opponent_yielded' et al are still emitted correctly).

5. **Test coverage:**
   - Unit test: is_player_victory() maps all documented outcomes correctly
   - Wiring test: a fixture encounter with outcome='opponent_yielded' rewards the same XP as outcome='player_victory' (regression on the 59-31 parity contract)
   - Existing 59-31 tests remain passing

## Acceptance Criteria

- is_player_victory(outcome: str) → bool classifier is defined and exported from a canonical module (either StructuredEncounter or game/encounter_classifier.py); contains definitive logic for "does this outcome count as a player victory for reward/advancement purposes?"

- Classifier maps the victory outcomes correctly:
  - outcome='player_victory' → True
  - outcome='opponent_yielded' → True
  - outcome='opponent_victory' → False
  - outcome='abandoned_on_location_change' → False
  - outcome='yielded' (player-side loss) → False
  - Any other unrecognized outcome → False (fail-safe default)

- All reward/advancement call sites that were checking `outcome == 'player_victory'` now call is_player_victory(outcome) instead (at least award_turn_xp in dispatch/encounter_lifecycle.py; document any other sites found); behavior is identical, code is centralized.

- Unit test in tests/game/ or tests/server/ (or adjacent to the classifier definition) verifies the mapping for all documented outcomes.

- **Wiring test (per CLAUDE.md "Every Test Suite Needs a Wiring Test"):** A behavioral test constructs two synthetic encounters — one with outcome='player_victory' from dial threshold, one with outcome='opponent_yielded' from yield — and asserts both award the same XP delta via the live award_turn_xp path (verifying the parity contract from 59-31 AC5). Does NOT grep source code; uses a real harness with the classifier wired into the reward path.

- Existing 59-31 tests remain passing; no regression in outcome labeling or OTEL emission.

- Tree green (all tests pass, ruff/pyright clean).

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-04

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04 | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design — PREP, pre-RED)
- **Conflict** (blocking): The story premise + wiring AC + wiring test assume `award_turn_xp` (`dispatch/encounter_lifecycle.py:1299`) checks `outcome == 'player_victory'`. **It does not.** `award_turn_xp` awards a flat per-turn tick (25 if `in_combat` else 10) to seated PCs, gated ONLY on `in_combat_now` (a live unresolved combat-category encounter — `websocket_session_handler.py:1231`), and never reads `enc.outcome`. The ONLY `outcome == 'player_victory'` check in the tree is `websocket_session_handler.py:195`, which computes `defeated_side` for the dramatic-kill spike tracker (a CONSUMER, not a reward; gated to `enc.outcome in ("player_victory","opponent_victory")` so `opponent_yielded` never even reaches it). **Consequences:** (a) the classifier has no existing reward call site to replace; (b) the specced wiring test ("player_victory and opponent_yielded award the same XP via `award_turn_xp`") is **vacuous** — `award_turn_xp` ignores outcome, so XP is already identical regardless of outcome, before any refactor. Needs ruling: identify the REAL victory-keyed reward/advancement site the classifier should gate, or reframe the wiring AC (e.g. the `defeated_side` consumer, or a new victory-keyed reward this story introduces). Affects `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`, `.../websocket_session_handler.py`. *Found by TEA during prep.*
- **Gap** (blocking): The AC victory-mapping set is **incomplete vs. live `enc.outcome` strings.** Live opponent morale-break sets `encounter.outcome = "surrender"` / `"rout"` (`narration_apply.py:540,546`, alongside `opponents_disposition = "surrendered"/"routed"`) — these are opponent-side yields = **player victories** and MUST map True. The AC only lists `player_victory`/`opponent_yielded`→True. A routed/surrendered opponent yielding no victory credit is the exact cry-wolf the epic fights. (Team-lead's brief named surrender/rout; confirming exact sites.) Full live `enc.outcome` set: `player_victory`, `opponent_yielded`, `surrender`, `rout`, `opponent_victory`, `abandoned_on_location_change`, `yielded`, plus dynamic `resolution_beat:<beat_id>`. Affects the classifier's victory set. *Found by TEA during prep.*
- **Question** (blocking — ambiguous outcome): `resolution_beat:<beat_id>` is a DYNAMIC `enc.outcome` value (`beat_kinds.py:1054`), absent from the AC set. The fail-safe default (unrecognized→False) would DENY victory credit to a beat-resolved encounter — but a resolution beat can resolve in the player's favor. Ruling needed: does `resolution_beat:*` (or some subset) count as a victory, or is the beat path always paired with a separate `player_victory`/`opponent_victory` terminal label (making False safe)? Affects the classifier's prefix/membership handling. *Found by TEA during prep.*
- **Question** (non-blocking): `mutual_destruction` (`hp_depletion.py:24,62`) — confirm whether it propagates to `enc.outcome` (it's an `HpResult.outcome` dataclass field today). If it can land on `enc.outcome`, classify → False (not a player victory). *Found by TEA during prep.*
- **Improvement** (non-blocking): The SAME conceptual event (opponent yields) lands as THREE different `enc.outcome` strings by path — `encounter.opponent_yield_outcome()` returns the string `"player_victory"` (`encounter.py:301`), `_resolve_opponent_yield` sets `"opponent_yielded"` (`narration_apply.py:4560`), morale sets `"surrender"/"rout"`. The classifier must map all True. Story step 3 (change `opponent_yield_outcome()` to return `"opponent_yielded"`) is **consumer-safe** — verified its only two consumers (`narration_apply.py:2824`, `:4615`) check `is None` only, never the string value. Note for Dev. Also: outcome is stringly-typed (no enum); a frozenset of victory labels as the classifier's single source of truth is the clean shape. Affects `sidequest-server/sidequest/game/encounter.py` + classifier module. *Found by TEA during prep.*

### Architect (design — rulings on TEA's prep + SM's 3 questions)
I concur with TEA's blocking findings (premise error: `award_turn_xp` is a flat per-turn tick, not victory-gated; the specced XP-parity wiring test is vacuous; the only live `== "player_victory"` site is `session_handler:195` kill-tracking). I verified the open questions in code and **rule** as follows:

- **Victory True-set (FINAL):** `player_victory`, `opponent_yielded`, `surrender`, `rout` → **True**. Everything else → **False**: `opponent_victory`, `yielded`, `abandoned_on_location_change`, `mutual_destruction`, and the dynamic `resolution_beat:*`, `composure_break:*`, `table_winner:*`, `resolved_by_trope:*`, plus unknown. Rationale verified:
  - `surrender`/`rout` (`narration_apply.py:540,546`) set `opponents_disposition="surrendered"/"routed"` — opponent-side yields = player victory → **True** (confirms TEA's Gap).
  - `resolution_beat:*` (`beat_kinds.py:1054`) is the **fallthrough `elif`** — it fires ONLY when player_victory / opponent_victory / composure_break / hp_depletion did **not** already resolve. By construction a bare resolution beat means *no victory condition was met* → **False is correct and safe** (answers TEA's blocking Question — it is NOT a missed victory; a real win would have set `player_victory` first).
  - `mutual_destruction` (`hp_depletion.py:62`) **does** land on `enc.outcome` → **False** (both sides down) (confirms TEA's Question).
  - `composure_break:{name}` embeds the broken **name**, not side — `:{opponent}` is a win, `:{player}` a loss, indistinguishable from the string alone → **False under the narrow "earns-credit" fail-safe.** Granting credit for opponent-composure-break needs name→side resolution = a richer predicate, out of scope for this extraction. Flagged for a follow-up if desired.

- **SM Q1 (string set):** above. **SM Q2 (call sites):** there is **no** reward call site to migrate. Do **not** touch `award_turn_xp` (no-op) and do **not** migrate `session_handler:195` (it needs *kill*-semantics where `opponent_yielded`/`surrender`/`rout` must stay non-victory — keep its own `("player_victory","opponent_victory")` set). The classifier's **legitimate live consumer** is the credit-victory collapse currently **hardcoded** in the resolution OTEL emits (`_resolve_opponent_yield` emits `"outcome":"player_victory"` beside `"resolution_label":"opponent_yielded"`, `narration_apply.py:4574-75`; the surrender/rout and location-change branches do the same implicitly). Wire `is_player_victory(enc.outcome)` to back that collapse — that gives it a real reader (not a stub) and removes the scattered hardcoding.

- **RULING — should the dramatic-kill spike tracker (`session_handler:195`) be the consumer (i.e., should a yield count as "player won" there)? NO.** That tracker's payload is `killed=<actor name who went down>`, feeding kill-keyed pacing/intensity. A yield/surrender/rout produces **no corpse** — the opponent is alive. Making it treat those as victory would fabricate a death that didn't happen — textbook Illusionism, the exact thing OTEL exists to catch. It is genuinely **kill-keyed, not victory-keyed**; leave it alone. If Keith wants yields to drive a pacing spike, that's a *separate* enhancement (have the tracker `observe` a distinct "resolved-in-player-favor, no kill" signal), NOT a victory-predicate swap — and it's its own story.

- **RESCOPE READ (the most important answer): there is no real victory-keyed reward today, so don't build a predicate that gates nothing (No Stubbing).** Three honest paths for SM/Keith:
  1. **Modest-but-real (recommended if the DRY is wanted):** ship `is_player_victory` as the single source of truth for the *credit-victory label mapping*, wired into the OTEL credit-attr emit sites that currently hardcode `"outcome":"player_victory"`. Real consumer, real DRY, ~1–2pts. Non-vacuous wiring test: a surrender/rout/opponent_yielded encounter's emitted **credit-outcome attr** is derived from the classifier (not a literal).
  2. **Defer/close:** if the OTEL collapse isn't worth a story on its own, close 59-32 as "premise invalid — XP parity already holds; no victory-keyed reward exists" and let the classifier be born *with* its first real reward consumer when that reward actually lands. Cleanest per No Stubbing.
  3. **Expand (only if Keith actually wants it):** introduce a genuine victory-keyed reward (e.g., a confrontation-win XP/advancement bonus distinct from the flat per-turn tick). That's a real feature, >2pts, its own story; 59-32's classifier becomes step 1 of it. Pick this only if the reward is genuinely on the roadmap — otherwise it's speculative.
  My lean: **Option 1** (it has a real reader and removes live hardcoding) or **Option 2** (if even that's not wanted). Avoid Option 3 unless the reward is real. Either way the unit mapping-table test is valid and TEA can write it now; the *wiring* target is the decision Keith must make.

- **SM Q3 (is one predicate safe?): NO.** Two divergent semantics — **credit-victory** (yield/surrender/rout → True) vs **defeated/killed-side** (`session_handler:195`, where they must be False because nobody was killed). Keep them separate. Name/scope the classifier as *"earns player-victory credit"*, NOT *"is a player win in general"* (the open label space means it is deliberately incomplete: surrender-by-name, table_winner, composure_break can be wins it doesn't claim).

- **Story step 3** (change `opponent_yield_outcome()` to return `"opponent_yielded"`): **endorse** — TEA verified both callers (`narration_apply.py:2824,4615`) check `is None` only, so it's consumer-safe, and it removes the confusing dual-string (method returns collapsed `"player_victory"` while persisted `enc.outcome` is `"opponent_yielded"`). Optional but a clarity win; include it.

- **Test direction:** drop the vacuous `award_turn_xp` parity test. Keep the trivial unit mapping-table test (label→bool, all of the above). Add a **behavioral wiring test** asserting a surrender/rout/opponent_yielded encounter's **credit-outcome OTEL attr** is derived from `is_player_victory()` (real consumer), per CLAUDE.md "wiring test, not source-grep."

**Net verdict for SM:** the classifier is a sound small extraction once **reframed** from "fix XP rewards" (already free) to "single source of truth for the credit-victory label mapping, backing the OTEL credit-outcome collapse." With that reframing + the True-set above, it's ~2pts and TEA can write RED. Recommend a 1-line confirmation from Keith that the credit-mapping (not XP) is the intent before RED.

### Dev (implementation)
- **Improvement** (non-blocking, forward to whoever lands the first victory-keyed reward): `is_player_victory` is now the single source of truth for credit-victory labels, but its ONLY live consumer is the `_resolve_opponent_yield` OTEL credit-outcome emit. The surrender/rout and dial-threshold/location-change resolution emits still set their credit `outcome` directly (not all route through the classifier yet) — a future reward consumer (Architect's Option 3) should route ALL credit-outcome derivations through `is_player_victory` to complete the DRY. Affects `sidequest-server/sidequest/server/narration_apply.py` (other resolution emits). *Found by Dev during implementation.*
- **Note** (non-blocking): the Architect's `composure_break:{name}` observation stands — the classifier deliberately returns False for it (name≠side from the string alone). If opponent-composure-break should earn credit, that needs name→side resolution, a richer predicate out of this extraction's scope. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Step 3 normalizes `opponent_yield_outcome()` return → breaks 4 existing 59-31 tests**
  - Spec source: SM RED brief (test #3) + story §52-55; AC "Existing 59-31 tests remain passing".
  - Spec text: "Cover step 3: opponent_yield_outcome() normalized return to 'opponent_yielded' (consumer-safe)" vs. "Existing 59-31 tests remain passing."
  - Implementation: New test `test_opponent_yield_outcome_returns_mechanical_truth_label` asserts the method returns `"opponent_yielded"`. This contradicts 4 existing assertions in `tests/server/test_opponent_yield_resolution.py` (lines 140,148,153,198) that assert `== "player_victory"`.
  - Rationale: "consumer-safe" is true for PRODUCTION (both consumers None-check), but the 4 TESTS pin the old return string. A deliberate contract change requires updating the tests that encode the old contract. **SM ruled Option (a) — step 3 stands.** Updated + renamed the 4 tests (`tests/server/test_opponent_yield_resolution.py`) to expect `"opponent_yielded"`: `test_all_opponents_withdrawn_returns_opponent_yielded`, `test_opponents_disposition_surrendered_returns_opponent_yielded`, `test_opponents_disposition_routed_returns_opponent_yielded`, and the assertion in `test_opponent_yield_outcome_is_win_condition_agnostic`. The 4 tests pinned an advisory mechanical-truth label now corrected to the truth (the opponent yielded — it was never a "player_victory" kill); credit still flows via the classifier. Deliberate, consumer-safe contract change, not a regression mask — the more-honest mechanical signal per the epic-59 lie-detector ethos.
  - Severity: minor (resolved per SM ruling)
  - Forward impact: production None-check consumers (`narration_apply.py:2824,4615`) unaffected; the 4 updated tests go GREEN when Dev lands step 3.
- **Wiring producer-proof patches `narration_apply.is_player_victory` (module-level import seam)**
  - Spec source: SM RED brief, wiring test #2 ("classifier is the ACTUAL producer ... derives the credit label THROUGH is_player_victory()").
  - Spec text: "derives its player_victory/credit label THROUGH is_player_victory(), replacing the hardcoded mapping."
  - Implementation: `test_credit_label_derives_through_classifier_not_hardcoded` monkeypatches `narration_apply.is_player_victory` and asserts the emit flips — which requires Dev to import the classifier into `narration_apply`'s namespace (module-level `from ...encounter_classifier import is_player_victory`) and call the bound name.
  - Rationale: a non-vacuous producer proof needs a patchable seam; module-level import into the using module is the standard one (mirrors 59-4 wiring-test convention). Behavioral, not source-grep.
  - Severity: trivial
  - Forward impact: if Dev calls it module-qualified instead, update the patch target + note here.

### Dev (implementation)
- No deviations from spec. Implemented exactly to TEA's pinned contract:
  - `is_player_victory` lives in the preferred module `sidequest/game/encounter_classifier.py` (TEA's shim prefers it); TRUE set = {`player_victory`, `opponent_yielded`, `surrender`, `rout`}, exact case-sensitive membership, fail-safe `False` for everything else (real `bool` via `in frozenset`).
  - Wired into `_resolve_opponent_yield` via a MODULE-LEVEL `from sidequest.game.encounter_classifier import is_player_victory` in `narration_apply.py` and the BOUND name `is_player_victory(...)` (not module-qualified) — so the wiring test's `monkeypatch.setattr(narration_apply, "is_player_victory", ...)` seam works as TEA expected. **No patch-target update needed.**
  - Credit derivation: `credit_outcome = "player_victory" if is_player_victory(enc.outcome) else enc.outcome` — derives THROUGH the classifier from the mechanical-truth label (`enc.outcome == "opponent_yielded"`); patching the classifier to `False` flips the emit away from `player_victory` (proves non-hardcoded), and the `else enc.outcome` fallback emits the honest mechanical label rather than a second hardcode.
  - Step 3: `StructuredEncounter.opponent_yield_outcome()` returns `"opponent_yielded"`. Verified both production consumers (`narration_apply.py:2825` `elif ... is not None`, `:4623` `is None`) are None-check-only — consumer-safe, no `== "player_victory"` equality anywhere in production.
  - Did NOT touch the kill/defeated-side tracker (`websocket_session_handler.py:195`) — out of scope per the SM brief (a yield is not a kill).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/game/encounter_classifier.py` — NEW. `is_player_victory(outcome) -> bool`: exact, case-sensitive membership against `frozenset{player_victory, opponent_yielded, surrender, rout}`; fail-safe `False` for everything else (dynamic prefixes, near-misses, case variants, `""`, unknown). Single source of truth for the credit-victory label mapping.
- `sidequest/game/encounter.py` — `StructuredEncounter.opponent_yield_outcome()` returns the mechanical-truth label `"opponent_yielded"` (was the credit label `"player_victory"`); docstring updated. Consumer-safe (both production consumers None-check only).
- `sidequest/server/narration_apply.py` — module-level `from sidequest.game.encounter_classifier import is_player_victory`; `_resolve_opponent_yield` now DERIVES the credit `outcome` attr via `credit_outcome = "player_victory" if is_player_victory(enc.outcome) else enc.outcome` (was hardcoded `"player_victory"`). Bound module-level name preserves the wiring test's monkeypatch seam.

**Out of scope (untouched, per SM brief):** the kill/defeated-side tracker at `websocket_session_handler.py:195` — a yield is not a kill; treating it as one would fabricate a death (Illusionism).

**Tests:** The 28 TEA RED tests → GREEN. Story set: 41/41 across `test_59_32_is_player_victory.py` (21), `test_59_32_classifier_wiring.py` (6), `test_opponent_yield_resolution.py` (14, incl. TEA's 4 normalized + the producer-proof + real-telemetry wiring test). Regression: **444/444** across 74 encounter/confrontation/resolution/morale/narration_apply/telemetry test files via testing-runner — zero regressions. Full suite: **20 failed / 8959 passed / 72 errors** — the 20 failures + 72 errors are **identical to the pre-existing clean-tree baseline** (DB/embedding/reference-page env failures; verified the full FAILED list contains ZERO 59-32/encounter/confrontation/resolution tests). **Zero new failures.** Ruff check clean.

**Branch:** `feat/59-32-shared-is-player-victory-classifier` (sidequest-server) — pushed.

**Handoff:** To review (The Queen of Hearts).
