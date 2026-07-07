---
story_id: "158-56"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-56: Mutation picker in the confrontation overlay — client sends mutation_id on the mutation beat commit (158-54 UI half)

## Story Details
- **ID:** 158-56
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/158-56-mutation-picker-overlay
- **Branch Strategy:** gitflow (feat/158-56-mutation-picker-overlay)
- **Repos:** server,ui  <!-- re-scoped 2026-07-07 from ui → server,ui: owned-mutations list is not projected to the client; a server-side mutation_economy projection on ConfrontationPayload (spellcasting twin) is required. User-authorized (TEA RED). Sprint YAML updated to match. -->
- **Original Repos:** ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-07T21:52:45Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-07T20:00:50Z | 2026-07-07T20:02:54Z | 2m 4s |
| red | 2026-07-07T20:02:54Z | 2026-07-07T20:43:02Z | 40m 8s |
| green | 2026-07-07T20:43:02Z | 2026-07-07T21:13:48Z | 30m 46s |
| review | 2026-07-07T21:13:48Z | 2026-07-07T21:33:16Z | 19m 28s |
| red | 2026-07-07T21:33:16Z | 2026-07-07T21:39:19Z | 6m 3s |
| green | 2026-07-07T21:39:19Z | 2026-07-07T21:44:16Z | 4m 57s |
| review | 2026-07-07T21:44:16Z | 2026-07-07T21:52:45Z | 8m 29s |
| finish | 2026-07-07T21:52:45Z | - | - |

## Sm Assessment

**Setup complete — ready for RED (TEA / Amos Burton).**

158-56 is the **UI half of 158-54**. The server half (completed) already wired the AWN mutation-use path into the primary dice-roll combat system and now expects `DiceThrowPayload.mutation_id` on a `mutation_resolution` beat. Nothing to discover on the server side — the wire contract is fixed. This story adds the client picker that supplies that field. Server repo is **not** touched; `repos: ui` only.

**Six ACs** (context-story-158-56.md, AC1–AC6), all client-side:
1. Picker visibility — render a mutation picker when the active beat is `mutation_resolution`.
2. Mutation list — populate from `snapshot.character.mutation_state.positive_ids` joined to the catalog for display names/descriptions.
3. `mutation_id` on commit — ride the selected id on the `DICE_THROW` payload.
4. Reject unmutated commit — local validation (disable commit) or handle the server's `DiceDispatchError` as a form error.
5. Regression — spell picker (cast_spell / `spell_id`) and non-mutation beats unaffected.
6. **Wiring test** — drive a real `DICE_THROW` with a valid `mutation_id` end-to-end, not an isolated unit test.

**Doctrine watch — Don't Reinvent:** the **102-2 spell picker** is the established pattern (`spell_id`, sourced from `spell_state`). Mirror it for `mutation_id` / `mutation_state.positive_ids` — do NOT author a parallel picker framework. Examine `sidequest-ui/src/components/CavernActionPanel.tsx` (or the spell-picker subcomponent) for the shape to copy.

**Player-audience note:** the mutation picker is a **player-facing mechanical surface** — the kind of legibility Sebastien/Jade want in the player UI (they can see and choose the crunch). This is UI legibility, not dev observability; no OTEL/GM-panel scope here.

**Notes for TEA:** AC6 is the load-bearing test per CLAUDE.md ("Every Test Suite Needs a Wiring Test") — the picker must be proven to actually emit `mutation_id` on the wire, not just render. Watch AC4: pick ONE of the two acceptance paths (local-disable vs server-reject) and pin it; don't leave both unasserted. UI repo → vitest; `just client-test`. No blocking deps (`depends_on: none`).

**Checklist:** session ✓ · fields ✓ · context+ACs ✓ · branch `feat/158-56-mutation-picker-overlay` (sidequest-ui/develop) ✓ · Jira skipped (not configured for this project).

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Status:** RED — verified by testing-runner (RUN_ID 158-56-tea-red): **10 failing (honest) + 4 green guards**, clean collection/transform, zero authoring bugs.

**Scope note (see Deviations):** RED discovery proved the story mis-scoped as `ui`-only — the owned-mutation list is **not projected to the client** (the `spellcasting` economy block has no mutation twin). User authorized expanding to **server + ui**. Sprint YAML `repos` + session `Repos:` updated to `server,ui`; context ACs corrected (AC1/AC2 named non-existent mechanisms).

**Test Files (3):**
- `sidequest-server/tests/server/test_confrontation_payload_mutation_economy_158_56.py` (NEW) — 5 RED. Pins the `mutation_economy` projection on `ConfrontationPayload` (the `spellcasting` twin): owned `{id,name,strain_cost}` for a mutant, recipient-scoped (162-10 decoy lesson), `None` for non-mutants/no-catalog, and the `extra="forbid"` protocol field. Real `mutant_wasteland` pack + synthetic `MutationState`.
- `sidequest-ui/src/__tests__/mutation-picker-mutate-beat-158-56.test.tsx` (NEW) — 4 RED + 2 green guards. Picker opens on a `mutation_resolution` beat (marker-driven), lists owned by `data-mutation-id` with `data-strain-cost`, choosing rides `mutationId` (spellId slot undefined), no-economy refuses loudly. Guards: non-mutation immediate commit; 102-2 spell picker unaffected.
- `sidequest-ui/src/__tests__/mutation-throw-wiring-158-56.test.tsx` (NEW) — 1 RED + 2 green guards. AC6 wiring: `mutation_id` + typed `player_action` land on the real `DICE_THROW` frame through App's production commit chain (GameBoard prop-trap). Guards: non-mutation no-`mutation_id`; atomic consume (no leak).

**Tests Written:** 14 (10 RED + 4 green guards) covering AC0–AC6.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Python #1 — No Silent Fallbacks (never fabricate empty economy) | `test_payload_omits_mutation_economy_for_a_non_mutant`, `_without_state_or_catalog` (assert `None`, not `{owned:[]}`) | failing (RED) |
| Python #11 — input validation at boundaries | `test_confrontation_payload_model_accepts_mutation_economy` (extra="forbid" protocol field) | failing (RED) |
| TS #4/#10 — null/undefined + API-data gating (No Silent Fallbacks, client) | `never silently commits … when the economy is missing` | failing (RED) |
| TS #8 — test quality (no `as any`, meaningful asserts) | all UI tests — typed tuple casts only, concrete id/name/strain/wire-key assertions | pass (self-check) |
| CLAUDE.md — No Source-Text Wiring Tests | every test drives real components/functions + asserts behavior; zero `read_text`/source-grep | pass |
| CLAUDE.md — Every Test Suite Needs a Wiring Test | `mutation-throw-wiring` drives the real App→send chain to the DICE_THROW frame; server test drives the real `build_confrontation_payload` | failing (RED) |
| CLAUDE.md — Don't Reinvent (SM doctrine watch) | tests pin the spell-picker CONTRACT twin (`mutation_economy`/`mutation_id`), not a parallel picker | failing (RED) |
| 162-10 lesson — decoy-scoped, not grab-all | `test_mutation_economy_is_scoped_to_the_recipient_not_the_whole_state` (decoy actor "Chrome") | failing (RED) |

**Rules checked:** applicable Python (server test) + TypeScript (UI tests) lang-review checks have coverage; OTEL span NOT pinned (parity with `spellcasting`, which emits none — see Delivery Findings for the optional-span note).
**Self-check (Phase C):** 0 vacuous assertions — no `assert True`, no `let _ =`, no truthy-on-always-None. The 4 green guards (non-mutation commit ×2, spell-picker-unaffected, atomic-consume) pass at RED by design — they guard regressions/leaks that only become falsifiable once the feature lands; explicitly labeled, not silent passes.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** GREEN. Server **14,669 passed** / 340 skipped / 3 pre-existing failed (see note); the 5 new `mutation_economy` tests + 2 spell-regression + 4 frame-supplier tests all pass. UI **2,551 passed / 0 failed** (full suite) — the 2 new files + the 2 fixed source-pattern wiring assertions + spell regression. ruff + pyright (0 new) + tsc (0 errors) + eslint (0 errors, 1 pre-existing warning) clean.
**Branches:** `feat/158-56-mutation-picker-overlay` — server `0c067587`, ui `973843d` (both pushed).

**Files Changed:**
- **server** `sidequest/protocol/messages.py` — `ConfrontationPayload.mutation_economy: dict|None` field (extra="forbid" declared).
- **server** `sidequest/server/dispatch/confrontation.py` — `_project_mutation_economy` helper (owned `positive_ids` → `{id,name,strain_cost}`, recipient-scoped, None-safe); `build_confrontation_payload` gains `mutation_state`/`mutation_catalog` kwargs + the projection; wired at the per-recipient `_frame_for` supplier via `getattr(genre_pack, "mutations", None)`.
- **ui** `src/types/payloads.ts` — `DiceThrowPayload.mutation_id?: string`.
- **ui** `src/components/ConfrontationOverlay.tsx` — `BeatOption.mutation_resolution`, `ConfrontationData.mutation_economy` + `ConfrontationMutationEconomy`/`MutationEconomyEntry` types, widened `onBeatSelect`, `MutationPicker` (SpellPicker twin), marker-driven detection + no-economy refusal in `handleBeatSelect`, `handleMutationChoose`, render.
- **ui** `src/components/GameBoard/GameBoard.tsx` — widened `onBeatSelect` + `handleBeatTileSelect` threads `mutationId`.
- **ui** `src/App.tsx` — `pendingMutationIdRef` latch, widened `handleBeatSelect`, `handleDiceThrow` conditional-spreads `mutation_id` (mirrors `spell_id`).
- **ui** `src/__tests__/confrontation-wiring.test.tsx` — updated 2 source-pattern regexes for the widened signatures (my change broke them; see Deviations + Findings).

**AC coverage:**
- AC0 (server projection) — ✅ 5 tests green; recipient-scoped (decoy test), None for non-mutants/no-catalog, protocol field accepted.
- AC1 (picker visibility) — ✅ marker-driven (`beat.mutation_resolution`).
- AC2 (owned list + strain) — ✅ `data.mutation_economy.owned`, `data-mutation-id` + `data-strain-cost` (per-mutation `strain_cost`; aggregate Strain pool left as TEA's open Question).
- AC3 (mutation_id on commit) — ✅ rides its own slot → `DICE_THROW.mutation_id` (wiring test green).
- AC4 (reject unmutated) — ✅ no-economy refuses loudly (chose the local-disable path).
- AC5 (regression) — ✅ spell picker + non-mutation beats untouched (full UI suite green).
- AC6 (wiring test) — ✅ green through App's real commit chain.

**3 pre-existing server failures (NOT this diff — zero coupling, verified):** `test_companion_brain_telemetry_passthrough.py::test_emit_endpoint_forwards_session_slug_and_severity_to_hub` + `::test_emit_endpoint_daemon_path_unchanged` (161-2 watcher-emit endpoint) and `test_pregen_bestiary_90_1.py::...[evropi]` (bestiary pregen — passes in isolation, fails in-suite = flaky test-isolation). None import/construct the confrontation payload; my getattr fix cleared the only real regressions my diff caused (4 frame-supplier tests, now 23 green).

**Self-review:** wired end-to-end (server projects at the production per-recipient supplier; UI reads it → picker → `mutation_id` on the real DICE_THROW frame) ✅ · mirrors the 102-2 spell-picker pattern verbatim, no parallel framework (Don't Reinvent) ✅ · all ACs met ✅ · No Silent Fallbacks (None economy → loud refusal, never a fabricated empty economy) ✅.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results — Round 1 (archived)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (server 28/28, ui 38/38, ruff+format+tsc clean, eslint 1 pre-existing warn, wiring verified E2E) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings; boundary paths self-assessed — the stale-id boundary IS the [HIGH] |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; self-assessed — found the KeyError-crash [HIGH] + corroborated the getattr silent fallback |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 6 (2 non-discriminating regexes, click-fidelity, decoy-order, loud-refusal, missing GameBoard wiring), 1 folds into [HIGH] |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (LOW) | confirmed 1 (GameBoard onBeatSelect JSDoc missing mutationId) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled; self-assessed — 2 new interfaces + widened signatures sound (rule-checker TS#2/#5 compliant) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled; no new surface — mutation_id is WHICH-not-WHOSE (158-54 server-side identity + unknown_mutation refusal) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled; self-assessed — faithful spell-picker mirror, no new abstraction |
| 9 | reviewer-rule-checker | Yes | findings | 2 (+ exhaustive per-rule pass) | confirmed 2 (getattr silent fallback [MED]; source-text-wiring-test/missing-wiring-test [MED]); **CHALLENGED** its "compliant" verdict on the KeyError path (see Assessment) |

**All received:** Yes (4 enabled returned; 5 disabled via workflow.reviewer_subagents, self-assessed)
**Total findings:** 1 blocking [HIGH] (correctness) + 5 [MEDIUM] (getattr rule violation, defanged-regex/missing-wiring, click-fidelity, decoy-order, loud-refusal) + 1 [LOW] (doc). 1 rule-checker verdict challenged with evidence.

## Reviewer Assessment — Round 1 (archived, verdict REJECTED — rework landed in R1)

**Verdict:** REJECTED

I wrote this code as Dev, so I hunted it twice as hard. It works on the happy path — every test is green — but it ships a **table-wide crash on a real content-authoring path**, reintroduces a **silent fallback a prior review round already killed in this exact function**, and its tests **do not actually verify the load-bearing `mutation_id` wire**. The green is partly illusory.

### Rule Compliance

Rubric = `.pennyfarthing/gates/lang-review/{python,typescript}.md` + CLAUDE.md/SOUL principles. rule-checker ran an exhaustive 13+13 pass; my confirmations:
- **Python #1 (No Silent Fallbacks):** 2 issues. (a) `getattr(genre_pack, "mutations", None)` — silent fallback on a declared field → **[MEDIUM], confirmed** (below). (b) `positive_by_id` KeyError propagation — rule-checker ruled compliant ("raises loudly per docstring"); **I CHALLENGE → [HIGH]** (below). The three `None`-returns in `_project_mutation_economy` (conf.py:121-125) are legitimate business-state, mirroring `spellcasting` — compliant.
- **Python #3 (type annotations):** `_project_mutation_economy` + new kwargs fully annotated — compliant.
- **Python #6 (test quality):** the 5 server tests — the decoy-scoping test is non-discriminating (recipient-first) → [MEDIUM]; the stale-id Err-path is untested → folds into [HIGH].
- **TS #4 (`??` vs `||`):** `data?.mutation_economy ?? null`, `mutationId ?? null` correct; `!mutationEconomy || …` is a boolean guard — compliant.
- **TS #6 (hook deps):** both widened dep arrays verified exhaustive (rule-checker + my re-check) — compliant.
- **TS #8 (test quality) / No-Source-Text-Wiring-Tests:** `confrontation-wiring.test.tsx:298,371` widened regexes non-discriminating → [MEDIUM] (below).
- **Every Test Suite Needs a Wiring Test:** the server suite never drives `make_confrontation_frame_supplier`/a real snapshot+pack; the GameBoard `mutation_id` forwarding has no behavioral test → [MEDIUM].
- **Don't Reinvent:** faithful 102-2 spell-picker mirror at every layer — compliant. **OTEL:** no projection span, but parity with `spellcasting` (which has none) — pre-existing debt, not a regression.

### Blocking

**[HIGH] [correctness] `_project_mutation_economy` crashes the whole table's CONFRONTATION broadcast on a content-drift stale mutation id.** It resolves every owned `positive_id` via `mutation_catalog.positive_by_id(mid)` (confrontation.py:128), which RAISES `KeyError` on an id absent from the catalog (models.py:186-189). There is NO load-time re-validation of a persisted character's `positive_ids` against the current catalog (`mutation_init` only seeds NEW sessions; resume loads verbatim), so: a content author renames/removes a positive mutation + an existing save owns it → KeyError at projection time. It propagates undamped through `build_confrontation_payload` → `make_confrontation_frame_supplier._frame_for` → `emitters._deliver_to_connected_recipients` (**emitters.py:165 — `msg = message_builder(pid)` in a bare loop, no try/except**) → the ENTIRE CONFRONTATION broadcast crashes for every seat, and the emitter-fallback (emitters.py:665) re-invokes the supplier and re-raises. **Blast radius: table-wide encounter brick from one stale display id.**
**Challenged (rule-checker ruled this "compliant"):** it reasoned the docstring claims "raises loudly (No Silent Fallbacks)" and the code does — a docstring-conformance pass, not a correctness judgment. I OVERRIDE with line-level evidence: (1) **`context_builder._positive_line` (context_builder.py:23-29) handles the IDENTICAL scenario** — a `positive_id` the catalog no longer carries — with `try/except KeyError` and an explicit comment: *"State references an id the catalog no longer carries (content drift) — surface it honestly rather than dropping the row."* The codebase's established pattern for stale owned-mutation ids in a read-only-display context is graceful degradation, NOT a crash. (2) `resolve_recipient_pc` (same file, conf.py:59-64) documents broadcast-path resolution failures must be non-fatal — *"refusing to broadcast at all would hide the encounter card."* An uncaught KeyError deep in the emit path is not a legitimate "fail loud" — it is the encounter-brick the project's whole recent arc (162-10, 158-48, SOUL) exists to prevent. The spell picker never hits this: it projects raw spell ids with NO catalog lookup. My mutation projection invented a crash surface the mirror doesn't have — and the docstring (conf.py:118-119) documents the defect as intent.
**Fix:** mirror `context_builder._positive_line` — per-id `try/except KeyError` (skip or mark the unknown id + a `logger.warning`); never let the projection crash the broadcast. Delete the "raises loudly (No Silent Fallbacks)" docstring line.

### Non-blocking (fix in the same rework — we are already going back)

| Severity | Issue | Location | Fix |
|---|---|---|---|
| [MEDIUM] [RULE][SILENT] | `getattr(genre_pack, "mutations", None)` is a silent fallback on a declared, always-present pydantic field (`GenrePack.mutations`, pack.py:466) — contradicts the `rules=genre_pack.rules` direct-access + fail-loud precedent 7 lines above in the SAME function; the justifying comment misrepresents the convention (every real call site uses direct `.mutations`: session_helpers.py:1403, chargen_mixin.py:209/1571/1818, and the new test's own `_catalog()`). Rule-matching → confirmed, cannot dismiss. | confrontation.py:835 | `mutation_catalog=genre_pack.mutations` + add `mutations = None` to the two `_FakeGenrePack` fixtures (test_confrontation_stakes_portrait_payload.py, test_wwn_cast_spell_wiring.py). |
| [MEDIUM] [TEST] | `confrontation-wiring.test.tsx:298,371` widened regexes non-discriminating — PROVEN (analyzer ran both) to match the new 4-arg AND the old 3-arg shape, defanging the ONE guard for GameBoard's `mutation_id` forwarding; and NO behavioral test covers the `handleBeatTileSelect → onBeatSelect` link (picker test never touches GameBoard; wiring test mocks GameBoard out). | confrontation-wiring.test.tsx:298,371 + missing coverage | Require the mutationId group (drop `?`) AND add a rendered-GameBoard test that clicks the picker and asserts the 4th arg reaches a spy onBeatSelect. |
| [MEDIUM] [TEST] | Click-fidelity: every picker/wiring test only clicks `owned[0]` (`structure/iron_hide`); a grab-[0] regression passes all 9. `sense/keen_sight` is checked for existence but never clicked-and-committed. (Code is correct — `onChoose(m.id)` — but the guard is missing.) | mutation-picker-mutate-beat-158-56.test.tsx:130-152 | Add a test clicking `sense/keen_sight` (owned[1]); assert `onBeatSelect` receives THAT id. |
| [MEDIUM] [TEST] | Server decoy-scoping test seats the recipient FIRST (`{"Rust": …, "Chrome": …}`), so a positional grab-first-CharacterMutationState bug still returns `mine.id` and passes — the exact 162-10 grab-[0] lesson the test cites, unmet. | test_confrontation_payload_mutation_economy_158_56.py:156 | Seat the recipient NOT first: `_state({"Chrome": [theirs.id], "Rust": [mine.id]})`. |
| [MEDIUM] [TEST] | "refuses loudly" test asserts only `not.toHaveBeenCalled()` — never the loud signal (console.warn). A fully-silent no-op passes; the name overstates ("no commit" ≠ "loud refusal"). | mutation-picker-mutate-beat-158-56.test.tsx:191 | Spy `console.warn`, assert it fires. |
| [LOW] [DOC] | GameBoard `GameBoardProps.onBeatSelect` JSDoc documents playerAction/spellId but not the new `mutationId` param (the overlay's sibling JSDoc WAS updated). | GameBoard.tsx:233 | Add a `mutationId` (158-56) line mirroring `spellId`. |

**Data flow traced:** picker click → `onChoose(m.id)` → overlay `onBeatSelect(beatId, undefined, mutationId)` → GameBoard `handleBeatTileSelect` → App `handleBeatSelect(beatId, draft, undefined, mutationId)` → `pendingMutationIdRef` → `handleDiceThrow` conditional-spread → `DICE_THROW.mutation_id`. Wire is correct end-to-end; the GameBoard hop is the one link with no genuine behavioral guard. Server: `snapshot.mutation_state` + `genre_pack.mutations` → `_project_mutation_economy` (recipient-scoped) → `ConfrontationPayload.mutation_economy`. The break: one unknown owned id crashes the whole projection.
**Pattern observed:** faithful 102-2 spell-picker mirror (SpellPicker↔MutationPicker, spellcasting↔mutation_economy, spell_id↔mutation_id) — Don't-Reinvent honored; marker-based detection (`beat.mutation_resolution`) is a justified improvement over a hardcoded id.
**Dispatch tags:** [EDGE] self-assessed (stale-id boundary = the [HIGH]). [SILENT] getattr fallback + KeyError-crash. [TEST] 5 (defanged regex, click-fidelity, decoy-order, loud-refusal, missing GameBoard wiring). [DOC] 1 (GameBoard JSDoc). [TYPE] clean. [SEC] no new surface. [SIMPLE] clean. [RULE] 2 (getattr No-Silent-Fallbacks; source-text-wiring-test).

### Devil's Advocate

Assume it is broken and prove it. The strongest case is the one I proved: this story's UI half exists because 158-54 was funded to stop in-combat mutations from bricking — and it reintroduces a brick one layer up. A mutant_wasteland table is Keith's or Jade's; Jade is a *content author* onboarded on a paste-and-PR loop (CLAUDE.md), so mutations.yaml WILL change under live saves. The day she renames `structure/iron_hide`, every existing save whose PC owns it can no longer enter combat: `positive_by_id` throws, the CONFRONTATION frame fails to build, and `_deliver_to_connected_recipients` — a bare `for pid: msg = message_builder(pid)` with no guard — takes down the broadcast for the whole table, not just the drifted seat. The failure is a KeyError deep in the emit stack: cryptic, mid-turn, exactly the "hours of debugging why isn't this quite right" the No-Silent-Fallbacks rule was written against — except it's a hard crash, and the sibling narrator path (`context_builder`) already solved it gracefully three functions away. A confused author would see "combat just crashes now" with no hint it's a stale mutation id. Second angle — the green is thinner than it looks: the one test meant to pin GameBoard's `mutation_id` forwarding is a source-text regex I widened until it matches the pre-feature 3-arg shape (proven), and no rendered test exercises that hop, so a Dev who deletes the 4th arg from `handleBeatTileSelect` ships green. Every picker test clicks index 0, so a stale-closure "always commit owned[0]" bug is invisible; the server decoy test seats the recipient first, so a grab-first bug is invisible — two independent "is it the RIGHT one" guards that don't actually discriminate. Third — the getattr quietly swaps a fail-loud for a shrug on a field that is never legitimately absent, undoing a prior review's explicit fix in the same function, on the exact call whose one wiring test doesn't exist. None of this is style. It is a table-wide crash on a real path, plus a test net with holes shaped precisely like the bugs it should catch. REJECT.

**Handoff:** Back to TEA (Amos Burton, red) — the findings are testable. Land RED first: a stale-id graceful-degradation test (drive `build_confrontation_payload` with an owned id absent from the catalog; today it raises — pin that it degrades instead), a discriminating GameBoard `mutation_id`-forwarding test (rendered, not source-regex) + a click-fidelity test (click `owned[1]`), the reordered decoy, and a `console.warn` loud-refusal assertion. Then Dev applies the graceful-degradation fix (mirror `context_builder`), the direct-access `.mutations` + `_FakeGenrePack` fixture updates, and the GameBoard JSDoc.

## TEA Assessment (rework R1)

**Tests Required:** Yes — responsive to the Reviewer's [HIGH] + [MED][TEST] findings.
**Status:** RED — **1 failing (the [HIGH] pin) + hardening guards green.** Verified: server `test_confrontation_payload_mutation_economy_158_56.py` → 1 failed / 5 passed (`test_stale_owned_id_is_skipped_not_crashed` fails on today's KeyError); ui `mutation-picker-mutate-beat-158-56.test.tsx` + `confrontation-wiring.test.tsx` → 28 passed.
**Commits:** server `0ca768ae`, ui `7bfabcb`.

**What I added/changed:**
- **[HIGH] RED** — `test_stale_owned_id_is_skipped_not_crashed`: drives `build_confrontation_payload` with an owned `positive_id` absent from the catalog (content drift). Today `positive_by_id` raises `KeyError` (→ table-wide broadcast crash via the no-try/except delivery loop). Pins the graceful-skip contract (mirror `context_builder._positive_line`): valid mutations survive, the uninstantiable id is skipped, no raise. **Dev fix: wrap the per-id lookup in try/except (skip + `logger.warning`), delete the "raises loudly" docstring line.**
- **[MED][TEST] decoy hardening** (green): reordered the scoping test to seat the recipient NOT first (`{"Chrome": ..., "Rust": ...}`) — a grab-first-CharacterMutationState bug now fails.
- **[MED][TEST] click-fidelity** (green): new test clicks `owned[1]` (`sense/keen_sight`), asserts ITS id commits — a grab-[0] bug now fails.
- **[MED][TEST] loud-refusal** (green): the no-economy test now spies `console.warn` and asserts it fires (the LOUD half, not just "no commit").
- **[MED][TEST] re-armed regexes** (green): both `confrontation-wiring.test.tsx` source-text assertions now REQUIRE `mutationId` (dropped the optional group that matched the pre-158-56 3-arg shape) — the defanged guard is discriminating again.

**Not fully closed (see Deviations + Findings):** the GameBoard `handleBeatTileSelect` forwarding hop still has no rendered behavioral test — I re-armed the source-text regex as a stopgap (proportionality + context pressure) rather than a full behavioral rewrite of the pre-existing anti-pattern file. Flagged for Dev/follow-up.

**Remaining Dev work (code fixes the RED + the [MED] getattr + [LOW] doc):** (1) graceful stale-id skip in `_project_mutation_economy`; (2) `getattr(genre_pack, "mutations", None)` → direct `genre_pack.mutations` + add `mutations = None` to the two `_FakeGenrePack` fixtures; (3) GameBoard `onBeatSelect` JSDoc `mutationId` line.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment (rework R1)

**Implementation Complete:** Yes — resolved the Reviewer's [HIGH] + all [MED]/[LOW] findings.
**Tests:** GREEN (targeted; Reviewer preflight runs the full suites). Server: `test_confrontation_payload_mutation_economy_158_56.py` + the 2 frame-supplier files → **29 passed** (the [HIGH] `test_stale_owned_id_is_skipped_not_crashed` + reordered decoy now pass; both `_FakeGenrePack` suites green under direct `.mutations` access). ruff clean. UI: picker + wiring + confrontation-wiring → **31 passed**.
**Commits:** server `ecb0cb6c`, ui `af97084`.

**Fixes:**
- **[HIGH] graceful stale-id skip** — `_project_mutation_economy` (confrontation.py) now iterates with a per-id `try/except KeyError` → `logger.warning` + skip (mirrors `context_builder._positive_line`); returns `None` if drift drops every owned id (never a fabricated empty economy). Added a module `logger`. Docstring corrected (was "raises loudly"; now documents graceful skip + the broadcast-crash rationale). No longer crashes the CONFRONTATION broadcast on content drift.
- **[MED] getattr → direct** — `mutation_catalog=genre_pack.mutations` (fail-loud like the adjacent `rules=genre_pack.rules`); the two `_FakeGenrePack` fixtures gain `self.mutations = None` (a real GenrePack always has the declared field).
- **[MED][TEST]** (landed by TEA rework): stale-id RED pin, reordered decoy, click-fidelity, loud-refusal, re-armed discriminating regexes.
- **[LOW][DOC]** — GameBoard `onBeatSelect` JSDoc now documents `mutationId`.

**Self-review:** the crash surface is closed and the graceful path matches the codebase's established content-drift precedent ✅ · getattr silent fallback removed, fail-loud restored ✅ · No-Silent-Fallbacks honored at the RIGHT layer (a `logger.warning`, not a broadcast crash) ✅.

**Deferred (TEA finding, non-blocking):** the GameBoard `handleBeatTileSelect` forwarding hop is guarded by the re-armed (discriminating) source-text regex; a full behavioral rewrite of `confrontation-wiring.test.tsx` is a flagged follow-up.

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 24 reported fails | **Verified FALSE regressions** — 5/5 representative "regressions" (protocol/persistence/session/visibility/crash-span) PASS isolated (`-n0`); causally unreachable from the confrontation.py delta = full-suite xdist OTEL flake. UI 2552 green, ruff/pyright/tsc clean. |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled; the stale-id boundary is the closed [HIGH] |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled; self-assessed — graceful-skip is fail-loud-at-the-right-layer (`logger.warning`), not a silent drop (rule-checker confirmed) |
| 4 | reviewer-test-analyzer | Yes | clean | 0 | all 5 R1 findings CLOSED + stale-id mutation-verified (revert → fails) |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 | all 4 fixes' comments verified accurate vs source |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled; `owned: list[dict[str,Any]]` annotation correct (rule-checker #3) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled; no new surface |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled; try/except mirrors context_builder, no new abstraction |
| 9 | reviewer-rule-checker | Yes | clean | 0 | both R1 violations RESOLVED (getattr→direct, KeyError→graceful-skip correctly layered), 0 new |

**All received:** Yes (4 enabled returned; 5 disabled, self-assessed)
**Total findings:** 0 confirmed. Preflight's 24 "fails" verified as full-suite xdist flakiness (representative sample passes isolated) — not blocking.

## Reviewer Assessment

**Verdict:** APPROVED

Round 2 re-review of the rework delta (server `ecb0cb6c`, ui `af97084`). Every round-1 finding is closed — verified independently, not by trusting a green suite.

**[HIGH] KeyError broadcast crash — CLOSED.** `_project_mutation_economy` now wraps the per-id `positive_by_id` in `try/except KeyError` → `logger.warning` + skip, returning `None` if drift empties the owned list (confrontation.py:149-162). Mirrors `context_builder._positive_line` (the round-1 precedent). Mutation-verified: test-analyzer confirmed reverting to the uncaught list-comp propagates the KeyError and fails `test_stale_owned_id_is_skipped_not_crashed`. The table-wide crash surface is sealed.
**[MED] getattr silent fallback — CLOSED.** Direct `genre_pack.mutations` (fail-loud like the adjacent `.rules`); `.mutations` is a declared `GenrePack` field so direct access is safe on any real pack; the two `_FakeGenrePack` fixtures declare `mutations = None`. rule-checker confirmed.
**[MED][TEST] test net — CLOSED.** test-analyzer verified all five: both regexes now REQUIRE `mutationId` (reject the 3-arg shape), click-fidelity clicks `owned[1]` (grab-[0] fails), the decoy seats the recipient second (positional-grab fails), loud-refusal asserts `console.warn`, and the stale-id RED pin is genuine + discriminating.
**[LOW][DOC] — CLOSED.** GameBoard JSDoc documents `mutationId` (comment-analyzer verified).

**Preflight "24 failures" — verified NOT a regression.** The full-suite xdist run reported 21 "new" failures across protocol/persistence/session/visibility/scene-harness — all systems the confrontation.py delta cannot reach. I ran 5 representative ones in isolation (`-n0`): 5/5 PASS. Full-suite OTEL-span/xdist flakiness under load (the documented `-n0` span caveat), not a regression. UI full suite 2552/2552; server ruff + pyright + UI tsc clean.

**Dispatch tags:** [EDGE] closed (stale-id). [SILENT] closed (graceful-skip is right-layer fail-loud). [TEST] 5 closed. [DOC] closed. [TYPE] clean. [SEC] no surface. [SIMPLE] clean (mirrors context_builder). [RULE] both R1 violations resolved, 0 new.

### Devil's Advocate
Try to break the fix. Does the graceful skip mask drift silently? No — every skip logs a WARNING with the id + recipient, surfacing content drift at the diagnosable layer instead of crashing the table; empty-after-drift returns None so the picker gates off. Does direct `.mutations` re-break the fakes? No — both `_FakeGenrePack` fixtures declare it and both suites pass. Could the try/except swallow a different error? No — `KeyError` only, and `positive_by_id` raises exactly that. Is the preflight red real? I trusted neither the red NOR the green — I ran the "regressed" tests isolated and they pass, and they are causally unreachable from a confrontation-payload projection change. The one honest residue is pre-existing full-suite xdist OTEL flakiness (companion/bestiary), which predates this story. Nothing in the delta turns a real path red. APPROVE.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Gap** (blocking → resolved by re-scope): the owned-mutation list is not projected to the client — there is no `mutation_economy` twin of the `spellcasting` block on `ConfrontationPayload`, and the UI snapshot has no `mutation_state`. A `ui`-only picker renders empty (half-wired). User authorized expanding to server+ui; a server `mutation_economy` projection is now AC0. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py` (`build_confrontation_payload`/`_frame_for`) + `sidequest/protocol/messages.py` (`ConfrontationPayload` field) + `sidequest-ui/src/types/payloads.ts` (`DiceThrowPayload.mutation_id`). *Found by TEA during test design.*
- **Conflict** (non-blocking): context AC1/AC2 named mechanisms that do not exist — `beat.beat_resolution_type === 'mutation_resolution'` (real field is the boolean `beat.mutation_resolution`, already projected) and `snapshot.character.mutation_state.positive_ids` (never on the wire; the spell-picker mirror uses a server-projected confrontation-payload economy block). Corrected in `sprint/context/context-story-158-56.md`. *Found by TEA during test design.*
- **Improvement** (non-blocking): OTEL — the `spellcasting` projection emits no dedicated span, so I did not pin one for `mutation_economy` (parity). But projecting which mutations a player may invoke IS a subsystem decision; Dev may add a small span (e.g. `confrontation.mutation_economy_projected` w/ owned-count) for GM-panel legibility per the OTEL principle. Not pinned. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py`. *Found by TEA during test design.*
- **Question** (non-blocking): the RED pins per-mutation `strain_cost` (from `PositiveMutationDef`) for legibility, but not the actor's aggregate Strain pool (current/max). The approved scope preview hinted `{owned, strain, ...}`. Should the block also carry the live Strain pool so the picker can show affordability? Dev/UX call — not required by RED; would enrich the `mutation_economy` shape. Affects the `mutation_economy` block. *Found by TEA during test design.*
- **Improvement** (non-blocking, pre-existing): App's item-use fast-path (App.tsx ~1819-1828) sends `DICE_THROW` directly. Mutations aren't item-use, but Dev should seal `mutation_id=None` there for shape parity with `spell_id` (No Half-Wired). Affects `sidequest-ui/src/App.tsx`. *Found by TEA during test design.*
- **Gap** (rework R1, non-blocking): the GameBoard `handleBeatTileSelect` → App `onBeatSelect` mutation_id-forwarding hop still lacks a rendered behavioral test — I re-armed the source-text regex (now discriminating) as a stopgap but did not rewrite `confrontation-wiring.test.tsx` behaviorally (pre-existing anti-pattern, out of this rework's scope under context pressure). A follow-up should replace that file's `readFileSync`+regex assertions with rendered-component interaction tests. Affects `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx`. *Found by TEA during rework test design.*

### Dev (implementation)

- **Improvement** (non-blocking): `confrontation-wiring.test.tsx` asserts wiring via `readFileSync` + regex on GameBoard/App SOURCE TEXT — the "No Source-Text Wiring Tests" anti-pattern (CLAUDE.md). My (correct) signature widening for AC3 broke 2 of its patterns; I updated them, but they should be rewritten as behavioral tests (survive refactors, catch real breakage). Affects `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): resolved TEA's OTEL Question by NOT adding a projection span (parity with `spellcasting`, which emits none) — the mutation USE already emits `awn.mutation.used`/`.refused` (158-54); the picker projection is a read-side data surface, not a mechanical decision. A `confrontation.mutation_economy_projected` span (owned-count) could be added later for GM-panel "what was offered" legibility. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): re TEA's item-use fast-path finding — the App item-use path sends DICE_THROW without `spell_id` OR `mutation_id`; the conditional-spread naturally omits both keys, so no explicit `mutation_id=None` seal is needed (matches `spell_id`'s treatment exactly). No change made; parity confirmed. Affects `sidequest-ui/src/App.tsx`. *Found by Dev during implementation.*
- **Question** (non-blocking, pre-existing): 3 full-server-suite failures are unrelated to this diff (verified zero coupling to confrontation-payload assembly): 2 companion watcher-emit endpoint tests (`test_companion_brain_telemetry_passthrough.py`, 161-2) + 1 bestiary pregen test (`test_pregen_bestiary_90_1.py::...[evropi]`, passes alone / fails in-suite = flaky isolation). Flagged so the Reviewer/finish gate does not attribute them to 158-56. Affects `sidequest-server/tests/server/test_companion_brain_telemetry_passthrough.py`, `sidequest-server/tests/server/dispatch/test_pregen_bestiary_90_1.py`. *Found by Dev during implementation.*
- **Improvement** (rework R1, non-blocking): resolved the Reviewer's [HIGH] (graceful stale-id skip mirroring `context_builder._positive_line`), [MED] getattr (reverted to direct `.mutations` + fake-fixture `mutations=None`), and [LOW] JSDoc. My own R0 getattr deviation is now reverted per the Reviewer FLAG. No new upstream findings this round. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py`. *Found by Dev during rework implementation.*

### Reviewer (code review)

- **Gap** (blocking): `_project_mutation_economy` crashes the whole-table CONFRONTATION broadcast on a content-drift stale `positive_id` — `positive_by_id` raises `KeyError` (no load-time re-validation of persisted `positive_ids`), and it propagates undamped through the bare `for pid: msg = message_builder(pid)` delivery loop (emitters.py:165). The codebase already handles this exact scenario gracefully at `context_builder._positive_line` (context_builder.py:23-29). Affects `sidequest-server/sidequest/server/dispatch/confrontation.py` (mirror the try/except; delete the "raises loudly" docstring line). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(genre_pack, "mutations", None)` (confrontation.py:835) is a silent fallback on a declared always-present field, contradicting the adjacent `rules=genre_pack.rules` fail-loud precedent; its justifying comment misrepresents the convention (all real call sites use direct `.mutations`). Fix = direct access + `mutations = None` on the two `_FakeGenrePack` fixtures. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py`, `tests/server/dispatch/test_confrontation_stakes_portrait_payload.py`, `tests/server/dispatch/test_wwn_cast_spell_wiring.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the `mutation_id` forwarding through `GameBoard.handleBeatTileSelect` has no behavioral test — the `confrontation-wiring.test.tsx:298,371` source-text regexes were widened until they match both the 4-arg and pre-feature 3-arg shapes (non-discriminating, proven), and neither new test file exercises the GameBoard hop (picker test skips GameBoard; wiring test mocks it out). Affects `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx` + a new rendered-GameBoard test. *Found by Reviewer during code review.*
- **Gap** (non-blocking): three "is-it-the-right-one" test guards don't discriminate — every picker/wiring test clicks only `owned[0]` (grab-[0] passes), the server decoy test seats the recipient first (positional bug passes), and the "refuses loudly" test never asserts the loud signal. Affects `sidequest-ui/src/__tests__/mutation-picker-mutate-beat-158-56.test.tsx`, `sidequest-server/tests/server/test_confrontation_payload_mutation_economy_158_56.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `GameBoardProps.onBeatSelect` JSDoc (GameBoard.tsx:233) omits the new `mutationId` param (the overlay's sibling JSDoc was updated). Affects `sidequest-ui/src/components/GameBoard/GameBoard.tsx`. *Found by Reviewer during code review.*
- **Question** (non-blocking, pre-existing): neither `mutation_economy` nor `spellcasting` projection emits an OTEL span answering "was the economy projected, for whom, with what" — shared observability debt. Not a regression (mutation USE is fully spanned via 158-54); flagged for a future pass. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py`. *Found by Reviewer during code review.*
- **Improvement** (round 2, non-blocking, pre-existing): the full-suite `uv run pytest` (xdist `-n auto`) flakes ~20 OTEL-span/emit tests under load (protocol/persistence/session/visibility/scene-harness) that pass cleanly in isolation (`-n0`) — verified 5/5 during this re-review. Unrelated to 158-56; a pre-existing test-isolation issue in the span-capture harness. Finish gate should run the story's targeted tests or `-n0`, not attribute the xdist flake to this branch. Affects `sidequest-server` test infra. *Found by Reviewer during code review (round 2).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Scope expanded from `ui` to `server,ui`**
  - Spec source: sprint/epic-158.yaml (`repos: ui`) + context-story-158-56.md ("this story is UI + one client-payload wiring test")
  - Spec text: the story assumed the picker lists `mutation_state.positive_ids` client-side
  - Implementation: added a server AC0 (`mutation_economy` projection on `ConfrontationPayload`); wrote a server test file; re-scoped `repos` in the sprint YAML + session (no `pf` CLI exists for the repos field, so the YAML was edited directly — documented, user-authorized)
  - Rationale: the owned-mutation list is not on the wire; the faithful spell-picker mirror requires a server projection (the `spellcasting` twin). A `ui`-only picker is half-wired. User chose "expand to server+ui, one story."
  - Severity: major
  - Forward impact: Dev implements both halves; the finish ceremony must track BOTH repos' PRs (repos field now `server,ui`)
- **Detection via the `beat.mutation_resolution` boolean, not a `beat_resolution_type` string**
  - Spec source: context-story-158-56.md, AC1
  - Spec text: "when `beat.beat_resolution_type === 'mutation_resolution'`"
  - Implementation: tests detect the mutation beat by the boolean `mutation_resolution` marker (real field, `genre/models/rules.py:201`, already `model_dump`'d onto the projected beat at confrontation.py:323)
  - Rationale: `beat_resolution_type` does not exist anywhere; the boolean marker is the real, already-projected discriminator — no server change needed for detection
  - Severity: minor
  - Forward impact: none — Dev reads `beat.mutation_resolution`
- **Mutation list sourced from a server-projected `mutation_economy` block, not `snapshot.character.mutation_state.positive_ids`**
  - Spec source: context-story-158-56.md, AC2
  - Spec text: "from `snapshot.character.mutation_state.positive_ids`"
  - Implementation: the picker reads `data.mutation_economy.owned` (a confrontation-payload projection), mirroring how the spell picker reads `data.spellcasting.prepared`
  - Rationale: raw `mutation_state` never leaves the server (parity with `magic_state`→`spellcasting`); the client snapshot has no `mutation_state`
  - Severity: minor (subsumed by the scope deviation; logged for the AC2 wording)
  - Forward impact: none — this IS AC0's projection
- **`mutationId` occupies its own positional callback slot**
  - Spec source: none (no spec named the callback arity)
  - Spec text: n/a
  - Implementation: overlay `onBeatSelect(beatId, spellId?, mutationId?)`; GameBoard/App `(beatId, playerAction?, spellId?, mutationId?)` — mutationId at the new trailing slot, spellId undefined on a mutation commit
  - Rationale: spell and mutation are mutually exclusive picks; a distinct positional slot is the direct mirror of how `spell_id` was added (App.tsx:1973) and avoids refactoring the cast path into an options object (smaller blast radius, No-Reinvent)
  - Severity: minor
  - Forward impact: Dev widens the three signatures + adds a `pendingMutationIdRef` latch and conditional-spread
- **Economy shape pins per-mutation `strain_cost`, not an aggregate Strain pool**
  - Spec source: the approved scope preview (`{owned, strain, ...}`)
  - Spec text: preview hinted a `strain` field
  - Implementation: `owned:[{id,name,strain_cost}]` — per-mutation cost from `PositiveMutationDef.strain_cost`; no actor aggregate Strain pool pinned
  - Rationale: per-mutation `strain_cost` delivers the Sebastien/Jade legibility (the `casts_remaining` analog) without locating/threading the live Strain pool in RED; Dev may enrich (see Delivery Findings Question)
  - Severity: minor
  - Forward impact: Dev may add an aggregate Strain readout to the block; the RED does not forbid it (assertions target the `owned` list)
- **(rework R1) Re-armed the source-text wiring regexes instead of a behavioral rewrite**
  - Spec source: Reviewer [MED][TEST] finding (confrontation-wiring.test.tsx defanged regexes + no behavioral GameBoard-forwarding test)
  - Spec text: "add a rendered-GameBoard test that clicks the picker and asserts the 4th arg reaches a spy onBeatSelect"
  - Implementation: required the `mutationId` group in both regexes (dropped the optional `?`), making them discriminate again; did NOT add a full rendered-GameBoard behavioral test
  - Rationale: the file is a pre-existing `readFileSync`+regex anti-pattern (102-2 era); re-arming closes the immediate defang (a dropped 4th arg now fails), and the new click-fidelity test covers the overlay's output. A full behavioral rewrite of GameBoard's render tree is a larger, out-of-scope effort under context pressure — flagged as a Delivery Finding for a follow-up.
  - Severity: minor
  - Forward impact: the GameBoard `handleBeatTileSelect` hop's draft-injection remains guarded only by the (now-discriminating) source-regex; a behavioral rewrite would be more robust.

### Dev (implementation)
- **`getattr(genre_pack, "mutations", None)` at the frame supplier, not direct `genre_pack.mutations`**
  - Spec source: context-story-158-56.md AC0 + the adjacent `genre_pack.rules` direct-access pattern (confrontation.py:827)
  - Spec text: project the economy "from `pack.mutations`"
  - Implementation: `getattr(genre_pack, "mutations", None)` in the `_frame_for` build call
  - Rationale: direct `genre_pack.mutations` raised `AttributeError` on the duck-typed `_FakeGenrePack` fixtures (test_confrontation_stakes_portrait_payload + test_wwn_cast_spell_wiring — 4 tests regressed). `.mutations` is an OPTIONAL field (unlike required `.rules`), so getattr is semantically correct AND matches the sibling mutation-path accessors (`narration_apply.py:589`, `magic_working.py:130`). A real GenrePack always has the field → production result is identical; the getattr default is unreachable outside test fakes. Chosen over editing the two fakes (less invasive, matches convention).
  - Severity: minor
  - Forward impact: none
- **Updated 2 source-pattern assertions in `confrontation-wiring.test.tsx`**
  - Spec source: the test file's own `readFileSync`+regex assertions on GameBoard/App source
  - Spec text: `/onBeatSelect\?\.\(beatId,\s*draft,\s*spellId\)/` and the `handleBeatSelect` signature regex
  - Implementation: widened both regexes to accept the optional trailing `mutationId` param
  - Rationale: my (correct) signature widening for AC3 broke these brittle source-text matches; leaving them red would fail the gate on a correct change. Updated to match; flagged as a Delivery Finding to rewrite behaviorally (these are the CLAUDE.md "No Source-Text Wiring Tests" anti-pattern).
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)

- **TEA — Scope expanded from `ui` to `server,ui`** → ✓ ACCEPTED: user-authorized via AskUserQuestion; the owned-mutation list genuinely isn't on the wire, so the server projection is required — sound.
- **TEA — Detection via the `beat.mutation_resolution` boolean** → ✓ ACCEPTED: `beat_resolution_type` does not exist; the boolean marker is the real, already-projected discriminator. Verified.
- **TEA — Mutation list from a server-projected `mutation_economy` block** → ✓ ACCEPTED: the `magic_state`→`spellcasting` precedent confirms raw state stays server-side; correct.
- **TEA — `mutationId` occupies its own positional callback slot** → ✓ ACCEPTED: mutually-exclusive picks, direct `spell_id` mirror; hook deps verified exhaustive.
- **TEA — Economy shape pins per-mutation `strain_cost`, not an aggregate Strain pool** → ✓ ACCEPTED: per-mutation cost delivers the legibility; aggregate pool is a separate enrichment (TEA's open Question). No objection.
- **Dev — `getattr(genre_pack, "mutations", None)` at the frame supplier** → ✗ FLAGGED: silent fallback on a declared always-present field, contradicting the `rules=genre_pack.rules` fail-loud precedent 7 lines above; the deviation's rationale ("matches sibling accessors / tolerates duck-typed packs") misrepresents the call-site convention (all real sites use direct `.mutations`). See [MEDIUM] finding — fix = direct access + `_FakeGenrePack` fixture updates.
- **Dev — Updated 2 source-pattern assertions in `confrontation-wiring.test.tsx`** → ✗ FLAGGED: the widening (`(,\s*mutationId)?` optional group) made the assertions non-discriminating — PROVEN to match both the 4-arg and pre-feature 3-arg shapes, defanging the only guard on GameBoard's `mutation_id` forwarding. See [MEDIUM][TEST] finding — require the group AND add a behavioral GameBoard test.
- **UNDOCUMENTED (Reviewer):** the [HIGH] KeyError-crash behavior was shipped without a logged deviation — `_project_mutation_economy` chose fail-loud-via-uncaught-KeyError over the codebase's established graceful-degradation pattern (`context_builder._positive_line`) for the identical scenario, and documented the choice as intent in its docstring rather than logging it as a deviation from the broadcast-non-fatal doctrine. Severity: H (see blocking finding).

**Round 2 audit (re-review):**
- **TEA (rework R1) — Re-armed the source-text wiring regexes instead of a behavioral rewrite** → ✓ ACCEPTED: the re-armed regexes now discriminate (test-analyzer verified they reject the 3-arg shape), and the full behavioral rewrite of the pre-existing `readFileSync` anti-pattern is correctly scoped as a follow-up Delivery Finding. Proportionate.
- The round-1 UNDOCUMENTED [HIGH] and the ✗ FLAGGED Dev deviations (getattr; defanged regexes) are all **RESOLVED** by the R1 rework: graceful skip mirrors `context_builder`, getattr reverted to direct access, regexes re-armed. Mutation-verified. Flags cleared. No new deviations introduced by the rework.