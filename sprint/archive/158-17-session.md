---
story_id: "158-17"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-17: big_bad signature resolution for per-expansion quests — collect defeated-NPC names at the turn handshake and guarantee seeded big_bad name matches the minted encounter-actor name

## Story Details
- **ID:** 158-17
- **Jira Key:** (not in use)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-24T09:43:48Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-24T09:03:15.036460+00:00 | 2026-06-24T09:19:11Z | 15m 55s |
| green | 2026-06-24T09:19:11Z | 2026-06-24T09:23:59Z | 4m 48s |
| review | 2026-06-24T09:23:59Z | 2026-06-24T09:34:04Z | 10m 5s |
| green | 2026-06-24T09:34:04Z | 2026-06-24T09:37:42Z | 3m 38s |
| review | 2026-06-24T09:37:42Z | 2026-06-24T09:43:48Z | 6m 6s |
| finish | 2026-06-24T09:43:48Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): the turn-handshake call site `defeated_npc_names=set()` (`websocket_session_handler.py` ~line 1569) is hardcoded empty, so no test can drive it without spinning the full WebSocket handler — and CLAUDE.md "No Source-Text Wiring Tests" forbids a `read_text()` grep assertion on it. GREEN MUST edit that call site to pass `collect_defeated_npc_names(snapshot)` (the new collector my tests pin). The composition test `test_big_bad_quest_resolves_when_defeated_name_collected` is the behavioral guarantee that collector→resolver works; the one-line call-site swap is verified by Dev + Reviewer, not by a unit test. Affects `sidequest/server/websocket_session_handler.py` (swap the empty set for the collector at the existing `resolve_expansion_quests(...)` call). *Found by TEA during test design.*
- **Question** (non-blocking): the SECOND dead call site is the frontier observer `make_expansion_quest_observer._observer` (`expansion_quest.py` ~line 370), which also passes `defeated_npc_names=set()`. Region transitions don't defeat NPCs, so leaving it empty is arguably correct — but GREEN should make an explicit, code-commented decision (wire it or document why it stays empty) rather than leave the divergence silent. Affects `sidequest/dungeon/expansion_quest.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the `dungeon.quest.resolved` SpanRoute `extract` in `telemetry/spans/dungeon_quest.py` does not surface `ref_id`. Adding `ref_id` to `quest_resolved_span` alone satisfies the test, but the SpanRoute `extract` should also emit it so the GM panel's routed view carries the antagonist id, not just the raw span. Affects `sidequest/telemetry/spans/dungeon_quest.py`. *Found by TEA during test design.*

### Dev (implementation)
- All three TEA findings resolved in-scope: blocking handshake call-site swapped; the frontier-observer site wired (not left empty) with a code comment; the resolved-span SpanRoute `extract` now emits `ref_id`. No new upstream findings during implementation.
- **Rework (round 1):** resolved the Reviewer's asymmetric-sanitization finding by normalizing in `collect_defeated_npc_names`. **Improvement** (non-blocking): the root-cause inject-side gap remains — `_npc_patches_for_region_population` / `_npc_patches_for_room_binding` append to `all_patches` after `_sanitize_patch_names`, so other readers of `snapshot.npcs` still see raw procedural names. A future hardening could run `_sanitize_patch_names` on those branches. Affects `sidequest/server/dispatch/monster_manual_inject.py:742-753`. *Found by Dev during rework.*

### Reviewer (code review)
- **Gap** (blocking): `collect_defeated_npc_names` reads `npc.core.name` raw, but the procedural big_bad mint path (`_npc_patches_for_region_population` / `_npc_patches_for_room_binding` in `monster_manual_inject.py:742-753`) appends patches to `all_patches` AFTER `_sanitize_patch_names` ran, so those names enter `snapshot.npcs` UNSANITIZED. `select_signature` now binds the quest ref_id to the *sanitized* form — an asymmetry this diff introduces. A cache-sourced bracket-named big_bad minted via region_population (beneath_sunden's own path) → ref_id `"Gormath the Drowned"` vs minted `"Gormath the Drowned (boss)"` → `ref in defeated_npc_names` is False → quest silently never resolves after the kill. Affects `sidequest/dungeon/expansion_quest.py` (`collect_defeated_npc_names` must normalize via `sanitize_display_name`, OR the region_pop/room_binding inject branches must run `_sanitize_patch_names`). *Found by Reviewer during code review.* → **RESOLVED in rework (collector now sanitizes); re-review APPROVED.**
- **Improvement** (non-blocking, deferred): `sanitize_display_name` is a lossy bracket-strip, so two NPC names sharing a base but differing only in bracket suffix (`"Gormath (boss)"`/`"Gormath (undead)"`) collapse to one key — a degenerate path to a *false-positive* quest resolution if both co-reside in `snapshot.npcs` with one being the big_bad. Not a regression and not a silent failure (the quest resolves, noisily). A robust future fix would key the big_bad by a stable id rather than display name. Affects `sidequest/dungeon/expansion_quest.py` (`collect_defeated_npc_names` / `select_signature` ref_id strategy). *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Collector seam named/located by the test, not the spec**
  - Rationale: the AC names a behavior, not an API; TDD requires a concrete contract. Co-locating with the consumer keeps `session.py` from growing and matches the module's existing ownership of quest resolution. GREEN may relocate/rename ONLY by keeping the behavior and updating the import — but the `hp.current == 0` defeat definition and the set-of-names return are load-bearing for resolution.
  - Severity: minor
  - Forward impact: Dev must add this exact (or behavior-equivalent) seam and wire it at the handshake call site; Reviewer verifies the call-site swap.
- **Call-site wiring proven by composition + Dev/Reviewer, not a unit test**
  - Rationale: no light handshake harness exists to drive `_execute_narration_turn`, and CLAUDE.md "No Source-Text Wiring Tests" explicitly forbids the deprecated `handler_path.read_text()` grep the sibling `test_setpiece_attach_wiring.py` used. Honest behavioral proof + a loud finding beats a fragile/forbidden grep.
  - Severity: minor
  - Forward impact: Reviewer must confirm the call-site edit landed.
- **Wired the collector at BOTH call sites, not just the blocking handshake one**
  - Rationale: leaving one dead `set()` behind while fixing the other is the "half-wired feature" anti-pattern (CLAUDE.md). The collector is cheap and `snapshot.npcs` is available at both sites; a big_bad killed in a region the party then leaves resolves on the move too.
  - Severity: minor
  - Forward impact: none — idempotent ledger resolution; both sites consult the same durable 0-HP signal.
- **Rework (round 1): fixed in the collector, not the inject branches**
  - Rationale: the collector fix is localized to this story's module, makes the `ref in defeated` comparison robust regardless of which mint path produced the NPC, and is idempotent on already-clean names (no behavior change for the common path). Sanitizing the inject branches has a wider blast radius (other consumers read `snapshot.npcs`) and is a separate, pre-existing concern — left as a noted follow-up rather than widened into this story.
  - Severity: minor
  - Forward impact: the inject-side unsanitized branches remain (other readers still see raw names there); see the follow-up Delivery Finding.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Collector seam named/located by the test, not the spec**
  - Spec source: session AC1 ("Defeated-NPC names are collected at the turn handshake ... with a non-test consumer wiring test")
  - Spec text: "collected at the turn handshake and passed into resolve_expansion_quests"
  - Implementation: tests pin a concrete seam `collect_defeated_npc_names(snapshot) -> set[str]` in `sidequest/dungeon/expansion_quest.py` (co-located with `resolve_expansion_quests` / `make_expansion_quest_observer`), defining "defeated" as `npc.core.hp.current == 0` in `snapshot.npcs`.
  - Rationale: the AC names a behavior, not an API; TDD requires a concrete contract. Co-locating with the consumer keeps `session.py` from growing and matches the module's existing ownership of quest resolution. GREEN may relocate/rename ONLY by keeping the behavior and updating the import — but the `hp.current == 0` defeat definition and the set-of-names return are load-bearing for resolution.
  - Severity: minor
  - Forward impact: Dev must add this exact (or behavior-equivalent) seam and wire it at the handshake call site; Reviewer verifies the call-site swap.
- **Call-site wiring proven by composition + Dev/Reviewer, not a unit test**
  - Spec source: session AC1 + CLAUDE.md "Every Test Suite Needs a Wiring Test"
  - Spec text: "proven via a non-test consumer (the websocket session handler turn path) — wiring test required"
  - Implementation: the wiring is proven by the real-store composition test (collector→resolver→completed + OTEL span) plus a blocking Delivery Finding directing the one-line handshake swap; there is NO source-text assertion on the handler.
  - Rationale: no light handshake harness exists to drive `_execute_narration_turn`, and CLAUDE.md "No Source-Text Wiring Tests" explicitly forbids the deprecated `handler_path.read_text()` grep the sibling `test_setpiece_attach_wiring.py` used. Honest behavioral proof + a loud finding beats a fragile/forbidden grep.
  - Severity: minor
  - Forward impact: Reviewer must confirm the call-site edit landed.

### Dev (implementation)
- **Wired the collector at BOTH call sites, not just the blocking handshake one**
  - Spec source: session AC1 + TEA Delivery Finding (non-blocking, Question)
  - Spec text: "GREEN should make an explicit, code-commented decision (wire it or document why it stays empty)" for the frontier-observer call site
  - Implementation: replaced `defeated_npc_names=set()` with `collect_defeated_npc_names(snapshot)` at the handshake (`websocket_session_handler.py`) AND the frontier observer (`expansion_quest.py make_expansion_quest_observer`), with a code comment noting resolution is idempotent so the two sites cannot double-resolve.
  - Rationale: leaving one dead `set()` behind while fixing the other is the "half-wired feature" anti-pattern (CLAUDE.md). The collector is cheap and `snapshot.npcs` is available at both sites; a big_bad killed in a region the party then leaves resolves on the move too.
  - Severity: minor
  - Forward impact: none — idempotent ledger resolution; both sites consult the same durable 0-HP signal.
- **Rework (round 1): fixed in the collector, not the inject branches**
  - Spec source: Reviewer blocking finding (asymmetric sanitization) + session AC2
  - Spec text: "guarantee seeded big_bad name matches the minted encounter-actor name"
  - Implementation: normalized via `sanitize_display_name` inside `collect_defeated_npc_names` (the read side), rather than running `_sanitize_patch_names` on the `region_population`/`room_binding` inject branches in `monster_manual_inject.py` (the write side, the Reviewer's alternative).
  - Rationale: the collector fix is localized to this story's module, makes the `ref in defeated` comparison robust regardless of which mint path produced the NPC, and is idempotent on already-clean names (no behavior change for the common path). Sanitizing the inject branches has a wider blast radius (other consumers read `snapshot.npcs`) and is a separate, pre-existing concern — left as a noted follow-up rather than widened into this story.
  - Severity: minor
  - Forward impact: the inject-side unsanitized branches remain (other readers still see raw names there); see the follow-up Delivery Finding.

### Reviewer (audit)
- **TEA — "Collector seam named/located by the test"** → ✓ ACCEPTED by Reviewer: defining `collect_defeated_npc_names(snapshot) -> set[str]` with the `hp.current == 0` defeat definition is a sound, minimal contract; co-location with the resolver matches module ownership. (Verified the implementation honors it; husk-reaper at `encounter_lifecycle.py:165` only reaps *ephemeral* stubs, so a bound big_bad survives at 0 HP for the collector.)
- **TEA — "Call-site wiring proven by composition + Dev/Reviewer, not a unit test"** → ✓ ACCEPTED by Reviewer: no light handshake harness exists and CLAUDE.md forbids `read_text()` source-grep; the real-store composition test plus my own call-site verification (the `set()`→collector swap IS present in the diff at `websocket_session_handler.py`) is the correct proof. Call-site swap CONFIRMED present.
- **Dev — "Wired the collector at BOTH call sites"** → ✓ ACCEPTED by Reviewer: wiring the frontier observer too (not leaving a dead `set()`) is correct per CLAUDE.md "no half-wired features"; idempotent resolution means no double-resolve. Good call.
- **Reviewer (audit, undocumented):** the diff sanitizes the *seed* side (`select_signature`) but NOT the *read* side (`collect_defeated_npc_names`), while the procedural mint path is unsanitized — an asymmetric-sanitization divergence neither TEA nor Dev logged. Spec said (AC2) "guarantee seeded name matches minted name"; code guarantees it only when the mint path happens to sanitize. Severity: M. Filed as the blocking Delivery Finding above; drives this REJECT.
- **Dev (rework) — "fixed in the collector, not the inject branches"** → ✓ ACCEPTED by Reviewer (re-review): normalizing in the collector is the correct localized fix — symmetric with the ref_id, idempotent on clean names, and avoids widening the blast radius of the pre-existing inject-side gap (which is logged as a non-blocking follow-up). The new regression test pins it.

## Technical Approach

### Root Cause Summary
Per the 2026-06-23 beneath_sunden playtest, the big_bad-signature quest resolution path is wired dead:

1. **Wiring Gap:** `resolve_expansion_quests(...)` is called from websocket_session_handler.py:1569 with `defeated_npc_names=set()` — a hardcoded empty set. The resolver checks `if kind == "big_bad" and ref in defeated_npc_names`, which can never be true with an always-empty set. Nobody collects defeated-NPC names at the turn handshake.

2. **Name-Match Gap:** The quest seeds `ref_id` from the region manifest at quest-seed time. The actual NPC actor minted into the encounter may carry a different name. The two names must be guaranteed identical for the comparison to work.

### Implementation Plan

1. **Collect defeated-NPC names:** At the turn handshake in websocket_session_handler.py, extract defeated NPC names from the current encounter/NPC-defeat state (not a hardcoded empty set). Pass this set into `resolve_expansion_quests`.

2. **Guarantee name matching:** Ensure the seeded big_bad name (quest ref_id) matches the name of the minted encounter actor, so defeating the big_bad makes the comparison true.

3. **OTEL observability:** Add `dungeon.quest.resolved` span emissions with ref_id and resolving-event name so the GM panel can verify resolution actually engaged (per ADR principle: the GM panel is the lie detector).

4. **Testing:** Wiring test verifying the non-test consumer (websocket session handler turn path) calls resolve_expansion_quests with non-empty defeated_npc_names; end-to-end test showing big_bad-signature quest completes when the big_bad is defeated.

### Key Files
- sidequest-server/sidequest/dungeon/expansion_quest.py (select_signature, _fill, resolve_expansion_quests)
- sidequest-server/sidequest/server/websocket_session_handler.py:~1561-1569 (dead call site)
- sidequest-server/sidequest/telemetry/spans/dungeon_quest.py (quest_resolved_span)

## Acceptance Criteria

- [x] Defeated-NPC names are collected at the turn handshake and passed into resolve_expansion_quests with a non-test consumer wiring test
- [x] The seeded big_bad name matches the minted encounter-actor name
- [x] Big_bad-signature per-expansion quests complete end-to-end when the big_bad is defeated
- [x] OTEL: dungeon.quest.resolved span fires with ref_id and resolving-event name
- [x] No regression to reach_deep / set_piece resolution paths

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral change to the quest-resolution engine (a previously-dead signature kind goes live).

**Test File:**
- `sidequest-server/tests/dungeon/test_expansion_quest_big_bad.py` — big_bad signature resolution (7 tests).

**Tests Written:** 7 tests covering 5 ACs.
**Status:** RED (5 failing — feature missing; 2 passing guards). Verified via `uv run pytest -n0` directly (testing-runner is unreliable per project memory — fabricates GREEN, clobbers session).

### AC → Test map

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 collect defeated names at handshake | `test_collect_defeated_npc_names_returns_only_zero_hp_npcs`, `test_collect_defeated_npc_names_empty_when_all_alive` | failing (ImportError — collector missing) |
| AC1+AC3 composed collect→resolve completes quest | `test_big_bad_quest_resolves_when_defeated_name_collected` | failing (ImportError) |
| AC2 seeded name == minted (sanitized) name | `test_big_bad_ref_id_matches_mint_sanitized_name` | failing (ref_id keeps bracket junk) |
| AC4 resolved span carries ref_id | `test_big_bad_resolved_span_carries_ref_id` | failing (span ref_id=None) |
| AC5 no over-resolve | `test_big_bad_does_not_resolve_when_other_npc_defeated` | **passing guard** (must stay green) |
| AC5 reach_deep unaffected | `test_reach_deep_unaffected_by_populated_defeated_names` | **passing guard** (must stay green) |

### Rule Coverage (python lang-review checklist)

| Rule | Coverage | Status |
|------|----------|--------|
| #6 Test quality (no vacuous asserts) | every test asserts a specific value (set equality, exact ref_id, span attrs) — no `assert result`/`assert True`; self-checked | pass |
| #3 Type annotations at boundaries | the pinned `collect_defeated_npc_names(snapshot) -> set[str]` contract is fully typed; Dev must annotate | enforced via contract |
| OTEL Observability Principle | `test_big_bad_resolved_span_carries_ref_id` forces the `dungeon.quest.resolved` span to carry the antagonist `ref_id` — the GM-panel lie-detector signal for this fix | failing (drives the emit) |
| Verify Wiring (non-test consumer) | composition test drives the REAL DungeonStore + collector + resolver; call-site swap flagged as a blocking Delivery Finding (see Decisions) | see finding |

**Rules checked:** 6 python lang-review checks reviewed; #6/#3 + the OTEL + Verify-Wiring doctrines are directly test-enforced. The remaining checks (#1 silent-except, #2 mutable-defaults, #4 logging, #5 path, #7 resource-leaks, #8 deserialization, #9 async, #10 imports, #11 input-validation, #12 deps, #13 fix-regressions) are Dev production-code concerns with no boundary in this test surface.
**Self-check:** 0 vacuous tests found.

### Key design decisions for Dev (Agent Smith)
1. **Add `collect_defeated_npc_names(snapshot) -> set[str]`** in `sidequest/dungeon/expansion_quest.py` — returns `{npc.core.name for npc in snapshot.npcs if npc.core.hp.current == 0}` (or behavior-equivalent). Minimal — no new ledger needed; 0-HP in `snapshot.npcs` is the durable defeat signal (the BUG-2b note in `session.py` keeps a slain NPC pinned at 0/N).
2. **Swap the dead call site:** `websocket_session_handler.py` ~line 1569, replace `defeated_npc_names=set()` with `defeated_npc_names=collect_defeated_npc_names(snapshot)`. (Decide explicitly on the frontier-observer site at `expansion_quest.py` ~370 — see Delivery Findings.)
3. **Name parity (AC2):** apply `sanitize_display_name` (from `sidequest.genre.names.generator`) to the big_bad name in `select_signature` so the seeded `ref_id` equals the name the Monster-Manual inject mints into `snapshot.npcs`.
4. **AC4:** add `ref_id` to `quest_resolved_span` (and its SpanRoute `extract`), and pass `ref_id=thread.payload["ref_id"]` from `resolve_expansion_quests`.

**Handoff:** To Agent Smith (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/dungeon/expansion_quest.py` — new `collect_defeated_npc_names(snapshot)` collector (0-HP NPCs); `select_signature` sanitizes the big_bad name via `sanitize_display_name` so the seeded `ref_id` matches the minted actor name; `resolve_expansion_quests` passes `ref_id` to the resolved span; the frontier observer now feeds the live collector instead of `set()`.
- `sidequest-server/sidequest/telemetry/spans/dungeon_quest.py` — `quest_resolved_span` accepts `ref_id` and its `SPAN_QUEST_RESOLVED` SpanRoute `extract` surfaces it for the GM panel.
- `sidequest-server/sidequest/server/websocket_session_handler.py` — turn-handshake call site swaps the dead `defeated_npc_names=set()` for `collect_defeated_npc_names(snapshot)`.

**AC status:** AC1 ✅ (collector + both call sites wired) · AC2 ✅ (sanitized ref_id parity) · AC3 ✅ (composition test completes the quest) · AC4 ✅ (resolved span + route carry ref_id) · AC5 ✅ (reach_deep/set_piece unchanged; over-resolve guard green).

**Tests:** new file 7/7 passing; full dungeon + telemetry suites **943 passed**. Verified with `uv run pytest` directly (testing-runner unreliable per project memory). Ruff clean on all changed files; pyright 0 errors on the two changed source modules.

**Branch:** `feat/158-17-big-bad-quest-resolution` (pushed to origin).

**Handoff:** To The Merovingian (Reviewer).

### Rework Round 1 (post-REJECT)

**Reviewer finding addressed:** asymmetric sanitization — `collect_defeated_npc_names` read `npc.core.name` raw while `select_signature` bound the ref_id to the sanitized form, so a bracket-named big_bad minted via the unsanitized `region_population` path would silently fail to resolve.

**Change:** `collect_defeated_npc_names` now returns `{sanitize_display_name(npc.core.name) for npc in snapshot.npcs if npc.core.hp.current == 0}` — symmetric with the ref_id, robust regardless of mint path, idempotent on clean names.

**Test added:** `test_big_bad_resolves_when_minted_name_is_unsanitized` — mints a raw `"Gormath the Drowned (boss)"` at 0 HP against a sanitized ref_id thread; RED before the fix (collector returned the raw name), GREEN after.

**Files changed (rework):** `sidequest/dungeon/expansion_quest.py`, `tests/dungeon/test_expansion_quest_big_bad.py` (commit `fe4cbbe5`, pushed).

**Tests:** big_bad file 8/8; full dungeon + telemetry **944 passed**; ruff clean; pyright 0 errors.

**Handoff:** Back to The Merovingian (Reviewer) for re-review.

## Subagent Results (Round 1 — REJECTED, superseded by re-review below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (943 pass, ruff/pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (husk-reaper, HP clamp, name=None) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (silent non-resolution → the blocking finding) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (tests non-vacuous, but miss the region_pop bracket case) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (comments accurate) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (fully typed) |
| 7 | reviewer-security | Yes | findings | 1 (low confidence, pre-existing) | confirmed 1 (upgraded to blocking on AC2/No-Silent-Fallbacks grounds) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (minimal, no over-engineering) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (lang-review #1-13 below) |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`, assessed by Reviewer directly)
**Total findings:** 1 confirmed (blocking), 0 dismissed, 0 deferred

## Reviewer Assessment (Round 1 — REJECTED; resolved by rework, see re-review below)

**Verdict:** REJECTED

### Findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM][SEC][SILENT][RULE] | Asymmetric sanitization: `collect_defeated_npc_names` reads `npc.core.name` raw, but the procedural big_bad mint path bypasses `_sanitize_patch_names`, while `select_signature` now binds the ref_id to the *sanitized* form. A cache-sourced bracket-named big_bad minted via region_population (beneath_sunden's path) → ref_id≠minted-name → quest **silently never resolves** after the kill. AC2 says "guarantee"; this is conditional. Violates No-Silent-Fallbacks. | `expansion_quest.py:332` (`collect_defeated_npc_names`); root at `monster_manual_inject.py:742-753` | Normalize collected names via `sanitize_display_name` inside `collect_defeated_npc_names` (symmetric with the ref_id) — OR run `_sanitize_patch_names` on the region_pop/room_binding inject branches. Add a regression test: minted NPC name carries bracket junk, sanitized ref_id, assert resolution still fires. |

### Observations (8+, tagged)

- [VERIFIED] Husk-reaper spares bound big_bads — `encounter_lifecycle.py:160-167` reaps only `npc.ephemeral and name in opponent_names`; Monster-Manual/region_pop creatures are bound (`ephemeral=False`, `creature_id` set), so a slain big_bad survives in `snapshot.npcs` at 0 HP for the collector. The collector's premise holds.
- [VERIFIED] HP can't go negative — `creature_core.py:43-44` clamps `current = max(0, min(max, raw))`, so `== 0` in the collector is exactly equivalent to `<= 0`. No off-by-one.
- [VERIFIED] Data flow — combat HP patches apply during narration (before the post-narration handshake block, comment at `websocket_session_handler.py:1526` "post-recompute snapshot"); the resolve call at ~1571 reads a snapshot where this turn's defeat is already at 0 HP. Same-turn resolution works.
- [VERIFIED][TYPE] Types — `collect_defeated_npc_names(snapshot: GameSnapshot) -> set[str]` and `ref_id: str = ""` are fully annotated; pyright 0 errors. lang-review #3 compliant.
- [VERIFIED][DOC] Comments accurate — new docstrings correctly cite BUG-2b, `monster_manual_inject` sanitization, and 158-17; the observer docstring update truthfully reflects the new wiring. No stale comments.
- [VERIFIED][SIMPLE] Minimal — `collect_defeated_npc_names` is a one-line comprehension; span change is additive/backward-compatible (`ref_id` default ""); no dead code, no over-engineering. lang-review confirms 0 smells.
- [SEC][SILENT][RULE] The blocking finding above — asymmetric sanitization → silent quest non-resolution on the procedural path.
- [LOW] Pre-existing: `bb.get("name", "")` returns `None` (not `""`) if the key exists with value `None` → `str(None)` = `"None"` ref_id. Unchanged by this diff (original `.strip()` had the same shape); out of scope, noted for awareness.
- [EDGE] `sanitize_display_name(name) or "the master of this place"` — a pure-bracket big_bad name sanitizes to `""` → fallback string, but the minted NPC would be dropped by `_sanitize_patch_names` (unsalvageable) on the manual path → unresolvable. Degenerate, pre-existing fallback; not introduced here.

### Rule Compliance (python lang-review)

- **#1 silent exception swallowing** — none in the diff. PASS. (But the *behavioral* silent failure in the blocking finding violates the sibling No-Silent-Fallbacks doctrine.)
- **#2 mutable defaults** — none (`ref_id=""` is immutable). PASS.
- **#3 type annotations at boundaries** — collector + span param fully typed. PASS.
- **#4 logging** — no new error paths; the collector cannot fail. PASS.
- **#6 test quality** — new tests assert specific values (set equality, exact ref_id, span attrs); 0 vacuous. PASS — but coverage GAP: no test exercises a bracket-named NPC minted via the unsanitized region_pop path (the blocking finding).
- **#8 unsafe deserialization** — none. PASS.
- **#10 import hygiene** — `sanitize_display_name` top-level import, no cycle (verified `genre.names.generator` doesn't import dungeon); local `# noqa: PLC0415` imports at handshake match existing style. PASS.
- **OTEL Observability Principle** — `dungeon.quest.resolved` span + SpanRoute now carry `ref_id`; the GM panel can attribute the close. PASS.
- **Verify Wiring** — collector called from two real non-test consumers (handshake + observer); call-site swap CONFIRMED present in diff. PASS.

### Devil's Advocate

Assume this code is broken. The headline attack: a player fights their way to the bottom of beneath_sunden, corners the named horror the quest told them to end, and kills it — and the quest stays "active" forever. No error, no log, no span anomaly; the GM panel shows the kill but the quest never flips. That is the single worst outcome for this story, because it is *indistinguishable from "the boss isn't dead yet"* — the exact silent-failure class the project's OTEL "lie detector" doctrine exists to prevent. How does it happen? The big_bad for a procedural region is frozen into the `region_population` mutation at materialize time, and its name can originate from the Monster-Manual cache, which (per `sanitize_display_name`'s own docstring and the 2026-06-10 "Vesper (version)" playtest) can hold bracket-annotated names minted by older code. That name is injected into `snapshot.npcs` **raw** (the region_pop branch bypasses `_sanitize_patch_names`), while the quest ref_id is now bound to the **sanitized** name. `"Gormath (boss)" != "Gormath"`, so `ref in defeated_npc_names` is permanently False. The diff didn't create the unsanitized mint path, but it *did* introduce the asymmetry by sanitizing only one side — and it's the side that doesn't match the world this story names. A confused author would reasonably believe AC2 ("guarantee … matches") is satisfied because the unit tests pass — but the tests only exercise the seed↔select symmetry, never a name that the mint path leaves dirty. What about a clean-named boss? Works fine — which is *why this is dangerous*: it passes every test, every playtest with a clean name, and only bites when a cached bracket name resurfaces months later, with no breadcrumb pointing here. A stressed reviewer would rubber-stamp it (green tests, clean lint). The fix is one `sanitize_display_name` call to make the comparison symmetric, plus a test that mints a dirty name. Cheap insurance against a silent, hard-to-diagnose regression of the very bug the story exists to kill.

**Handoff:** Back to Agent Smith (Dev) — `recovery_config.reviewer-verdict.target_phase: green` is authoritative (rework routes to green/Dev, not red/TEA). Dev must add BOTH: (1) the symmetric-sanitize fix — apply `sanitize_display_name` inside `collect_defeated_npc_names` so the collected names match the canonical form `select_signature` binds the ref_id to (closes the region_population/room_binding unsanitized-mint gap), and (2) a regression test that mints an NPC whose `core.name` carries bracket junk (e.g. `"Gormath the Drowned (boss)"`) at 0 HP with a sanitized ref_id thread, asserting the big_bad quest still resolves.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (944 pass, 8/8 big_bad, ruff/pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (collision/empty-string edges below) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — round-1 silent-failure finding now RESOLVED |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — regression test added, covers the prior gap |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — collector docstring updated, accurate |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — still fully typed |
| 7 | reviewer-security | Yes | findings | 1 (low, pre-existing structural) | confirmed resolved (prior finding); 1 new LOW deferred (lossy-transform collision) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — fix is a 1-line set-comprehension change |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — lang-review re-checked below |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`, assessed by Reviewer directly)
**Total findings:** 0 blocking (the round-1 blocker is resolved), 1 LOW deferred (non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED (re-review, round-trip 1)

The round-1 blocking finding (asymmetric sanitization → silent quest non-resolution) is **RESOLVED**: `collect_defeated_npc_names` now normalizes via `sanitize_display_name` (`expansion_quest.py:340-344`), symmetric with `select_signature`'s ref_id binding (`:87`), backed by a new regression test `test_big_bad_resolves_when_minted_name_is_unsanitized` (RED→GREEN). Preflight GREEN (944), ruff/pyright clean.

### Findings

| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [SEC][SILENT][RULE] (resolved) | Round-1 asymmetric sanitization — now fixed symmetrically; regression-tested. | `expansion_quest.py:340` | RESOLVED — verified in diff + test green |
| [LOW][SEC][EDGE] (deferred) | `sanitize_display_name` is lossy: two bracket-variant NPC names sharing a base (`"Gormath (boss)"`/`"Gormath (undead)"`) collapse to one key, so a non-big_bad kill could *falsely* resolve a quest. Requires both variants co-resident in `snapshot.npcs` with one being the big_bad; `select_signature` takes only the deepest big_bad per expansion, so the trigger is degenerate. NOT a regression, NOT a silent failure (quest resolves, noisily). | `expansion_quest.py:340` | DEFERRED — non-blocking; captured as a Delivery Finding for awareness |

### Observations (re-review, tagged)

- [VERIFIED][SILENT] Prior blocker resolved — collector sanitizes (`expansion_quest.py:341`); `ref in defeated_npc_names` is now symmetric regardless of mint path. The silent-non-resolution path is closed.
- [VERIFIED][TEST] Regression test `test_big_bad_resolves_when_minted_name_is_unsanitized` mints a raw `"Gormath the Drowned (boss)"` at 0 HP against a sanitized ref_id thread; confirmed RED before the fix, GREEN after. Non-vacuous (asserts membership + resolution count + completed status + thread closed).
- [VERIFIED][SIMPLE] Fix is minimal — a one-line set-comprehension change wrapping `sanitize_display_name`; idempotent on clean names, so no behavior change on the common path.
- [VERIFIED][DOC] The collector docstring now documents the lossy-normalize rationale and the inject-side asymmetry it compensates for. Accurate.
- [VERIFIED][TYPE] Signature unchanged (`-> set[str]`); pyright 0 errors.
- [SEC][EDGE] New LOW collision observation (deferred above) + empty-string edge: a pure-bracket name → `""` in the collected set, but ref_id never sanitizes to `""` (falls back), so no false match. Harmless.
- [RULE] lang-review re-check: #1/#2/#3/#4/#6/#8/#10 still PASS; OTEL principle PASS (ref_id on resolved span); Verify-Wiring PASS (collector consumed at handshake + observer). The round-1 #6 coverage gap is now closed by the regression test.
- [DOC] No stale comments introduced by the rework.

### Devil's Advocate (re-review)

Can I still break it? The original silent-failure path is gone — a raw bracket-named big_bad now normalizes on both sides, so the kill resolves. The remaining attack is the *inverse*: force a FALSE resolution. To do that I need two NPCs whose names differ only inside brackets, both alive in `snapshot.npcs`, one being the quest's big_bad, and I must defeat the *other* one — then its sanitized name collapses onto the big_bad's ref_id and closes the quest without killing the real boss. But `select_signature` binds exactly one big_bad per expansion (the deepest-region candidate), names are generated to be distinct, and bracket-variant collisions of the same base name are a degenerate generator artifact. Even if it happened, the failure is *noisy* (a quest visibly completes) — the opposite of the silent class the project fights hardest. It does not violate No-Silent-Fallbacks. The cost to fully eliminate it (track the big_bad by a stable id rather than display name) is disproportionate to a degenerate trigger; deferring with a logged Delivery Finding is the right call. Nothing else in the one-line delta moves the needle: it's idempotent on clean names, fully typed, regression-tested, and GM-panel-observable via the `ref_id` span. Approving.

**Handoff:** To Morpheus (SM) for finish-story.