---
story_id: "87-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 87-4: Content sweep + calibration + OTEL playtest

## Story Details
- **ID:** 87-4
- **Jira Key:** (none — Jira disabled for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/87-4-heavy-metal-content-sweep-otel-playtest (sidequest-content, sidequest-server)
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T17:16:44Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T11:52:50Z | 2026-06-05T11:55:03Z | 2m 13s |
| red | 2026-06-05T11:55:03Z | 2026-06-05T12:00:00Z | 4m 57s |
| green | 2026-06-05T12:00:00Z | 2026-06-05T16:40:21Z | 4h 40m |
| review | 2026-06-05T16:40:21Z | 2026-06-05T16:56:57Z | 16m 36s |
| green | 2026-06-05T16:56:57Z | 2026-06-05T17:11:23Z | 14m 26s |
| review | 2026-06-05T17:11:23Z | 2026-06-05T17:16:44Z | 5m 21s |
| finish | 2026-06-05T17:16:44Z | - | - |

## Sm Assessment

**Story:** 87-4 — final integration gate for epic 87 (heavy_metal → WWN faithful port).
**Workflow:** tdd (phased) → routes to TEA (RED) → Dev (green) → Reviewer → SM finish.
**Repos:** sidequest-content (the sweep + confrontation retirement) + sidequest-server (calibration test migration + OTEL playtest verification). Both feature branches created: `feat/87-4-heavy-metal-content-sweep-otel-playtest`.
**Jira:** none ([no jira]) — claim skipped.

**Context written and validated:** `sprint/context/context-story-87-4.md` (parent `context-epic-87.md`). It is ground-truthed against the live pack — exact line numbers for the four retirement targets (`rules.yaml:11–16` custom_rules, `:255` pact_working, `:309` debt_collection, `prompts.yaml:72` pact-cost prompt) and a three-category sweep doctrine (dead mechanical refs → remove; prose flavor → keep; world freeform races → keep).

**Load-bearing routing notes for TEA:**
- **87-3 was canceled, scope folded into 87-2** (content PR #358). `spells_wwn.yaml` + `cast_spell` beat already live — nothing upstream missing. PR #358 deliberately "left Story-4 baggage untouched."
- **Two false-alarm traps** the tests must respect: (1) the `hp_depletion` calibration regression is BY DESIGN (record baseline first); (2) evropi/long_foundry freeform races (kobold/antman/half-orc/gnome) are world features wired through `allows_freeform`, NOT 5e baggage — tests must not assert them away.
- **The OTEL playtest is the epic's lie-detector** — AC 5 requires span evidence on BOTH worlds (evropi + long_foundry), combat + magic, asserting spans not source text (server CLAUDE.md "No Source-Text Wiring Tests").
- **Zero engine changes** is the epic premise — server work is test-only.

**Decision:** Setup complete, gate ready. Handoff to TEA (Mr. Praline) for RED.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[Question, non-blocking] long_foundry magic-plugin class ids vs WWN Callings.** `worlds/long_foundry/magic.yaml:248` declares `available_classes: [warlock, pact_priest, soul_trader, crossroads_walker]` under a world magic-plugin block — names that do NOT exist in the live WWN class set (`classes.yaml`: warrior/expert/necromancer/elementalist/pact_born). Two readings: (a) these are dead mechanical class-ids a chargen/narrator path could bind to → category-1 baggage AC2 must sweep/remap; or (b) they are a legitimate separate magic-plugin taxonomy (ADR-126) that is world-flavor and stays. **Dev/GM must adjudicate during the sweep** — check whether anything in the engine resolves a *character class* from `magic.yaml available_classes`, or whether it's purely magic-system content. If (a), the long_foundry OTEL playtest (AC5) is where it surfaces. I did not encode a test either way — the right answer depends on the engine reading, not on my guess.
- **[Improvement, non-blocking]** `prompts.yaml:72` carries the one *mechanical* pact-cost claim ("casts twice → pays twice") amid otherwise-preserved prose; flagged in the TEA assessment for re-homing to Effort/Strain truth.
- **[Gap, blocking-for-AC5] The evropi OTEL scenario cannot demonstrate WWN combat/magic via free narration — no Other ever seated.** Live run (2026-06-05, `2026-06-05-evropi`, fresh chargen, $0.39, span dump `~/.sidequest/logs/87-4-playtest/evropi-spans.jsonl`): 7 narration.turn, **zero** `wwn.spell.cast` / confrontation-seat / confrontation-resolve / HP-ablation spans anywhere in the capture. The lie-detector fired correctly instead: `confrontation.intent_mismatch ×3` (combat tokens "strike"/"spell" with no declared confrontation), `dispatch_engagement.movement.mismatch` (PC never relocated toward a fight), and `intent_router.dispatch.gated ×3` on subsystem `magic_working` with reason "snapshot.magic_state is None (world ships no ADR-126 pact-working magic plugin)". **Root cause:** the narrator kept the PC in evropi's social town-hall opening; no hostile Other was seated, so no WWN combat confrontation started, and the WWN `cast_spell` beat (which only fires *inside* a confrontation) never triggered — the spell fell through to the absent pact-working plugin and gated. Engine behaved correctly (ADR-116/139 no-toothless-Other; honest lie-detector). This is **not** an engine bug (epic premise = zero engine changes) — it's an AC5 test-design gap: free-form narration from a social opening doesn't deterministically produce combat. Fix path = drive AC5 via the ADR-092 scene-harness `--fixture` (deterministic hydrated combat scene with a seated Other), which the story context explicitly permits ("authoring a minimal one is in scope for AC5"). **Affects** `scenarios/heavy_metal_evropi_otel.yaml` + `scenarios/heavy_metal_long_foundry_otel.yaml` (rework to fixture-based seating) — and possibly a `/dev/scene` fixture for heavy_metal. *Found by Dev during AC5 playtest.*
- **[Improvement, non-blocking] playtest `--span-jsonl` capture is not trace-scoped.** The evropi capture (8,876 spans) pulled in spans from an unrelated concurrent session (`watcher.magic.init_skipped` with `world_slug=grimvault`, `actor=Sebastien`). Our run's spans are isolatable by idempotency-key / slug, but raw span counts are polluted by other Jaeger traffic. Affects `scripts/playtest.py` span-capture query scoping (should filter to the run's trace_ids). *Found by Dev during AC5 playtest.*

### Reviewer (code review)

- **Gap (blocking, AC3/AC6): prompts.yaml pact-ledger sweep incomplete.** `genre_packs/heavy_metal/prompts.yaml` `ritual:` (L178) names the retired `pact_working` confrontation and frames the ledger as a live mechanic; `debt_collection:` (L200) is a prompt key named after the other retired confrontation. Affects `genre_packs/heavy_metal/prompts.yaml` (re-home both to Effort/Strain like the `combat:` block, or remove — both `Prompts.ritual`/`debt_collection` are unconsumed dead fields). *Found by Reviewer during code review.*
- **Improvement (non-blocking): dead prompt fields.** `Prompts.ritual` / `Prompts.debt_collection` (`sidequest-server/.../genre/models/narrative.py:40-41`) are declared but never read by any server path (the `combat` prompt is consumed via `gp.combat` at `orchestrator.py:1818`; no `gp.ritual`/`gp.debt_collection` equivalent exists). Affects `narrative.py` + any pack populating these keys — candidate for removal as dead surface. *Found by Reviewer during code review.*
- **Improvement (non-blocking): retirement-guard suite has no wiring test.** `tests/genre/test_heavy_metal_pact_ledger_retired_87_4.py` asserts only content shape; no test proves the `wwn` ruleset binding loads without `UnknownRulesetError` via a production path. Mechanical wiring IS covered by the sibling integration suites (`test_wwn_heavy_metal_combat.py`/`_dispatch.py`), so this is a suite-completeness gap, not a coverage hole. Affects the test file. *Found by Reviewer during code review.*

## Tea Assessment (RED)

**Phase:** finish complete. Tests written, confirmed failing for the right reason.

**RED tests added** — `sidequest-server/tests/genre/test_heavy_metal_pact_ledger_retired_87_4.py` (5 tests, all FAIL now against the un-swept pack; assertion failures, not errors):
1. `test_pact_working_confrontation_is_retired`
2. `test_debt_collection_confrontation_is_retired`
3. `test_ledger_custom_rules_are_retired` (`ledger_tracking` + `pact_cost_attribution`)
4. `test_no_retired_confrontation_types_remain`
5. `test_surviving_confrontations_are_exactly_the_ported_set` — pins BOTH directions: bespoke pair gone AND combat/negotiation/chase survive (guards against over-reach deleting the generic dials)

Run: `cd sidequest-server && SIDEQUEST_GENRE_PACKS=<content>/genre_packs uv run pytest tests/genre/test_heavy_metal_pact_ledger_retired_87_4.py -v` → 5 failed.

**What I deliberately did NOT test (and why — Dev/Reviewer must verify by judgment, not by my asserting it):**
- **AC2 5e sweep (prose):** I did not write a `grep`-style sweep test. The story's three-category doctrine makes a naive grep actively *wrong* — "sorcerer/wizard/cleric" as prose words and evropi/long_foundry freeform races (kobold/antman/half-orc/gnome) are FEATURES, not baggage. Asserting them away would gut the pack. Sweep correctness = Dev judgment + the OTEL playtest, not a unit test.
- **AC3 prompt voice:** `prompts.yaml` uses "ledger" ~10× as the doom-cost METAPHOR (blood-and-years, candle match-cuts) — D5 PRESERVES that voice. The one mechanical claim to retire is `prompts.yaml:72` ("a sorcerer who casts twice in one combat pays twice, and the second cost…") which implies a ledger *rule* that no longer exists. Re-home it to WWN Effort/Strain truth. This is a prose edit best reviewed by eye, not pinned by a brittle string assert.
- **AC5 OTEL playtest (both worlds):** the existing `tests/integration/test_wwn_heavy_metal_combat.py` already proves `wwn.*` combat spans fire + HP ablates (world-agnostic `test_world`). AC5's "both worlds" ask is a **headless OTEL playtest** (`just playtest` on evropi + long_foundry), whose evidence (span lists) attaches to this session — a verification gate, not a unit test. I did not duplicate the heavy combat harness per-world; that adds brittleness without new signal. **Dev/playtest owns producing the span evidence.**

**Green-phase guidance for Bicycle Repair Man:**
- Retire the two confrontations (`rules.yaml` ~L255 `pact_working`, ~L309 `debt_collection`) and the two `custom_rules` keys (~L15–16). My 5 tests go green.
- Update the now-stale docstring in `tests/genre/test_pack_load.py::test_heavy_metal_pack_loads_with_dual_dial_schema` — it names "pact_working, debt_collection" as surviving dial confrontations. Test still passes (filters to dial_threshold; negotiation/chase remain) but the comment lies after retirement.
- Record the full-suite BASELINE failure list BEFORE changes (the `hp_depletion` calibration regression is by-design per 87-1 — do not chase it).

## GM Assessment (green — content)

**Content green DONE and verified** (sidequest-content commit `7e8bd9c` on the feature branch):
- `rules.yaml` — cut `pact_working` + `debt_collection` confrontations; dropped `ledger_tracking` + `pact_cost_attribution` custom_rules. Surviving confrontations: **combat (hp_depletion) + negotiation + chase** (exactly the ported set).
- `prompts.yaml` — re-homed the one mechanical pact-cost claim ("casts twice → pays twice") to WWN truth (Effort committed + System Strain on the body). The doom-cost ledger *metaphor* is preserved per D5.
- `openings.yaml` — "paladin-style" → "clean righteous-knight" in an `avoid:` list (drop the 5e class noun; identical narrator steer).

**TEA finding adjudicated (long_foundry `available_classes`):** resolved to reading **(b) — legitimate ADR-126 magic-plugin taxonomy, NOT 5e baggage.** `magic.yaml`'s `available_classes` (warlock/pact_priest/soul_trader/crossroads_walker) is **not read by any server code** (`grep available_classes sidequest-server` → empty); it's the world magic-plugin instantiation layer (bargained_for_v1 etc.), and "warlock" is heavy_metal's own pact-guild term ("Coil and Brand journeyman-sorcerer"), genre-true to a blood-pact city. **Left untouched** — sweeping it would delete legitimate magic-system flavor. No chargen/narrator path binds a character class from it.

**Verification run (env: SIDEQUEST_GENRE_PACKS set):**
- 5 RED retirement tests → **GREEN**.
- Supporting genre suite (pack_load, wwn_classes, class_id_consistency, calibration, win_condition, resolution_mode) → **61 passed**.
- heavy_metal WWN integration (combat HP-ablation, no-toothless-Other, opponent reprisal, cast_spell routing, caster Effort seeding) → **9 passed**.
- Both worlds' genre loads clean; ruleset `wwn`; confrontations `[chase, combat, negotiation]`.

**Still TODO this story:**
- **AC5 OTEL playtest, BOTH worlds (evropi + long_foundry)** — scenarios authored (`scenarios/heavy_metal_evropi_otel.yaml`, `scenarios/heavy_metal_long_foundry_otel.yaml`; caster Callings so combat + `wwn.spell.cast` both fire). **Live narrator runs pending a go/no-go (real API spend — ADR-134).** Stack is currently UP (server :8765 HTTP 200).
- **AC4 full-suite calibration** with `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS` — record baseline first; the `hp_depletion` dial regression is by-design (do not chase).
- **Dev (code):** update the now-stale docstring in `tests/genre/test_pack_load.py::test_heavy_metal_pack_loads_with_dual_dial_schema` — it still names `pact_working, debt_collection` as surviving dial confrontations (test passes; the comment lies).

## Dev Assessment (green — code + AC4)

**Dev (code) item DONE:** `tests/genre/test_pack_load.py::test_heavy_metal_pack_loads_with_dual_dial_schema` docstring fixed — dropped `pact_working, debt_collection` from the "surviving dial confrontations" list (now `negotiation, chase`). Cosmetic; no OTEL.

**AC4 full-suite calibration — DONE and baseline-grounded.** Ran the full server suite with `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_TEST_DATABASE_URL` set: **10,720 passed / 20 failed / 343 skipped** (xdist `-n auto`, 93s). Established the true baseline by diffing the failing set against pre-sweep content (`b3534ee`) and re-running the suspect tests serially (`-n0`):
- **15 reproducible failures** (output-byte-budget 61-12, MessageType enum count, 6× npc_invented_namegen mocks, 5–6× narration_clue_discovery MagicMock-progression, apply_world_patch active_stakes path, yield_handler_outbound) — present **identically pre- and post-sweep**, all in subsystems orthogonal to heavy_metal content. **Pre-existing baseline debt, NOT 87-4 fallout.**
- **5 "worker-crash" failures** in the xdist run (pertinence_wiring, chargen_complete_no_hp_leak, **culture_context test_connect_to_evropi**, lore_rag_wiring, retrieval_orchestration) **all PASS serially (`-n0`) both pre- and post-sweep** → xdist worker-death collateral, not real failures. The evropi one was the only plausibly-sweep-related node; it passes clean → sweep did not break evropi world context.
- **Zero failures are the by-design `hp_depletion` regression** — the sweep produced no confrontation-removal fallout at all. AC4 "no fallout after removal" bar is met; the 15 pre-existing failures are separate baseline debt to route outside this story.

**Content cleanup (beyond the defined retirement targets, per Keith 2026-06-05):** `audio.yaml` — removed the two **dead** mood aliases `pact: ritual` / `working: ritual` (no engine emits `pact`/`working` moods; the engine vocabulary is combat/exploration/rest/ritual/sorrow/tension). Track titles ("Working the Rite", "The Collector Approaches") kept as genre-true doom-ritual flavor (category-2). Pack re-validates clean (0 errors).

**Asset audit (Keith request, same session):** R2-verified both worlds. evropi portraits were the lone real gap (0/4 in R2 despite docs saying "complete"); **rendered + uploaded 4/4** (rux, hant, prot_thokk, pumblestone_sweedlewit), re-scan confirms 4/4 in R2. long_foundry portraits already 7/7 in R2; music complete (41 .ogg). CLAUDE.md asset-status lines (orchestrator + content) were reversed vs R2 truth — corrected to "both asset-complete".

**AC5 OTEL playtest:** RAN both worlds live (evropi + long_foundry) — both confirm the same result: **no `wwn.*` combat, no `wwn.spell.cast`, no HP ablation; the lie-detector fired correctly** (`confrontation.intent_mismatch`, `dispatch.gated`, `movement.mismatch`). Root cause = no hostile Other seated from a social opening → no confrontation → cast_spell beat never triggers. Engine is honest; the **verification approach** is what needs rethinking, not the engine. **AC5 is blocked-pending-design.** Brainstorming handoff written: `docs/superpowers/notes/2026-06-05-ac5-otel-combat-engagement-brainstorm-handoff.md`. Span evidence: `~/.sidequest/logs/87-4-playtest/{evropi,long_foundry}-spans.jsonl`.

**AC5 RESOLVED via D1 (2026-06-05, architect brainstorm).** Re-scoped: WWN combat+magic mechanics proven by tests/integration/test_wwn_heavy_metal_combat.py (see the "AC5 Resolution (D1)" section below for the run). Live narrator-in-the-loop proof deferred to epic 90 (90-1 encountergen ruleset-awareness; 90-2 magic-plugin session-bind; 90-3 AC5b free-play proof evropi+long_foundry+barsoom; 90-4 hydrator spellcasting/hp_depletion seeding for a deterministic fixture). Design: docs/superpowers/specs/2026-06-05-ac5-otel-combat-verification-design.md. No server code changed — epic 87 zero-engine-changes premise preserved.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)

TEA/Dev logged no deviations in this section, but three were carried in prose elsewhere
in the file and are recorded here for the audit, plus one undocumented deviation I found:

- **AC5 re-scoped from live-playtest proof → integration-test proof (D1).** Spec
  (context AC5, original): "OTEL playtest, both worlds … combat fires `wwn.*` + ablates
  HP; a caster fires the spell-cast span." Implementation: AC5 now leans on
  `tests/integration/test_wwn_heavy_metal_combat.py` (3 passing) for the mechanical proof;
  live narrator-in-the-loop proof deferred to epic 90. → ✓ ACCEPTED by Reviewer: the live
  lie-detector fired correctly (engine is honest), the integration test drives the
  production seating + dice seams, and the live proof is correctly filed as epic 90.
- **Scope add: playtest `--keep`→`--fresh` default inversion (a333988).** Not in the AC
  list; landed during 87-4. → ✓ ACCEPTED by Reviewer: documented end-to-end (help, usage
  docstring, cookbook); rule-checker found no stale `--keep` refs; reuse default matches
  the UI client's existing `force_new=False`.
- **Scope add: `audio.yaml` dead-mood-alias removal (`pact:`/`working:`).** → ✓ ACCEPTED
  by Reviewer: the engine emits no `pact`/`working` moods; correct dead-alias cleanup.

- **UNDOCUMENTED (Reviewer-found, this is the REJECT cause): prompts.yaml pact-ledger
  sweep is incomplete — `ritual:` and `debt_collection:` blocks survive.** Spec (context
  AC3): "Narrator prompts tell the WWN truth. No prompt text implies pact-ledger mechanics;
  doom-cost voice carried by Effort/Strain framing." Code: `genre_packs/heavy_metal/
  prompts.yaml:178` (`ritual:`) still reads *"When a character performs a **pact_working** …
  what is being **withdrawn from the ledger** … what the **ledger** now reads"* — naming the
  retired `pact_working` confrontation type and framing the ledger as a live mechanic; and
  `prompts.yaml:200` (`debt_collection:`) is a prompt key named after the other retired
  confrontation type. The Dev correctly re-homed the `combat:` block (TEA flagged only
  `prompts.yaml:72`) to Effort/Strain but missed these two. ✗ FLAGGED by Reviewer:
  unmet AC3 on the epic's final integration gate. Reachability is nil today (both
  `Prompts.ritual`/`debt_collection` are unconsumed by any server path — caps live risk)
  but that does not satisfy AC3's prompts-review axis or AC6 ("no dual-truth content
  remaining"). See Reviewer Assessment for severity + fix.
  → ✓ RESOLVED (round 2, rework `bcce10c`): the Dev ported `ritual:`/`debt_collection:`
  — and, beyond the named findings, the every-turn `narrator:` block (Keith's directive
  "replace ALL THIS with faithful port") — to WWN Effort/System Strain grounding;
  `pact_working` is gone (0 matches pack-wide), the ledger survives only as metaphor.
  Re-review preflight + comment-analyzer both CLEAN; pack PASS (0 err); suite 5/5.
  The scope-extension to `narrator:` and the deferral of the four non-blocking `[TEST]`
  findings to a TEA follow-up are both ✓ ACCEPTED by Reviewer (sound — narrator: carried
  the same latent dual-truth in the consumed prompt; test-design is TEA's lane).

## AC5 Resolution (D1)

**Date:** 2026-06-05
**Approach:** Span-asserting integration test (ADR-092 scene-harness fixture), not free-narration playtest.

**Test run:**
```
sidequest-server/tests/integration/test_wwn_heavy_metal_combat.py
```

**Exact pytest summary line:**
```
3 passed, 96 warnings in 2.99s
```

**Tests (all PASSED):**
1. `test_heavy_metal_combat_is_wwn_bound_and_ablates_hp` — asserts `pack.rules.ruleset == "wwn"`, Other seated with `hp`/`armor_class` from `opponent_default_stats`, strike ablates Other HP, `state_patch.hp` span fires.
2. `test_heavy_metal_combat_seats_no_toothless_opponent` — asserts `encounter.opponent_toothless` span is **absent** (no-toothless-Other invariant holds).
3. `test_heavy_metal_opponent_reprisal_ablates_player_hp` — asserts `encounter.opponent_attack_resolved` span fires (opponent-reprisal invariant holds).

**Asserted span names (AC5 evidence):**
- `state_patch.hp` — HP ablation fires on a successful strike
- `encounter.opponent_toothless` — ABSENT (invariant: toothless Other cannot be seated)
- `encounter.opponent_attack_resolved` — opponent reprisal resolves and ablates player HP

**Run command:**
```bash
cd sidequest-server && \
SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs \
uv run pytest tests/integration/test_wwn_heavy_metal_combat.py -v
```

This is the mechanical evidence for AC5 under D1 (the closure plan's substitute for free-narration playtests that cannot deterministically seat a hostile Other from a social opening). See `docs/superpowers/plans/2026-06-05-ac5-d1-closure.md`.

## Subagent Results

Review scope: 3 repos — sidequest-content `feat/87-4` (`rules.yaml` −116: retire `pact_working`/`debt_collection` confrontations + `ledger_tracking`/`pact_cost_attribution` custom_rules; `prompts.yaml`/`openings.yaml` prose), sidequest-server `feat/87-4` (new `test_heavy_metal_pact_ledger_retired_87_4.py`), orchestrator `main` (docs + `scripts/playtest.py` `--keep`→`--fresh`). Settings `workflow.reviewer_subagents`: 4 enabled, 5 disabled.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (5/5 tests GREEN, pack validates 0 err, lint clean, no rules.yaml dangles) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (guard/loader skip-mismatch, 3 redundant tests, no wiring test) | confirmed 3 (all non-blocking), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (ritual: pact_working ref, debt_collection: orphan key, stale "FAIL until" docstring) | confirmed 3 (1 → blocking, 2 minor), dismissed 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (ws:Any no-comment, no wiring test ×2 [rule 6 + A3]) | confirmed 1 (Low), corroborated wiring-gap, dismissed 0 |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per settings)
**Total findings:** 1 confirmed blocking (HIGH), 5 confirmed non-blocking (Medium/Low), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

The mechanical core of this story is clean and well-built — but the pact-ledger sweep (AC2/AC3) is **incomplete**: two narrator-prompt blocks in `prompts.yaml` still carry the retired framing, including the name of a deleted confrontation type. On the epic's *final integration gate* (AC6: "no dual-truth content remaining"), that is a blocking gap. The fix is small and in-scope.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `ritual:` prompt names retired `pact_working` confrontation + frames the ledger as a live mechanic — unmet AC3 ("no prompt text implies pact-ledger mechanics") on the final gate. Dev re-homed `combat:` but missed this. | `sidequest-content/genre_packs/heavy_metal/prompts.yaml:178-188` | Re-home to Effort/Strain + `cast_spell` (mirror the `combat:` block), OR remove the block — `Prompts.ritual` is unconsumed dead surface. Drop the `pact_working` name either way. |
| [MEDIUM] | `debt_collection:` prompt key named after the other retired confrontation; cost-payment prose ("years, memory, a name, a piece of the body") is the retired pact-cost framing. | `prompts.yaml:200-214` | Rename to a non-mechanical Collector-flavor key + strip pact-cost mechanics, OR remove (also unconsumed). |
| [MEDIUM] | Test guard/loader skip mismatch: `_has_real_content()` checks `GENRE_PACKS_DIR/heavy_metal` directly while `_load_heavy_metal()` uses `find_pack_path()` (which has a `genre_workshopping` fallback). If the pack moves, all 5 tests silently skip. `[TEST]` | `tests/genre/test_heavy_metal_pact_ledger_retired_87_4.py:52-57` | Use the `try find_pack_path / except PackNotFound → pytest.skip` idiom from `test_wwn_heavy_metal_combat.py`. (Non-blocking — `genre_workshopping` was retired 2026-06-03, so the fallback is largely moot.) |
| [MEDIUM] | Retirement-guard suite has no wiring test (rule 6 + A3): asserts content shape only; nothing proves the `wwn` binding loads without `UnknownRulesetError` via a production path. `[RULE][TEST]` | same file | Add one test asserting `load_genre_pack` does not raise on the `wwn` ruleset (sibling integration suites already cover the dispatch wiring). |
| [LOW] | 3 of 5 tests (`test_pact_working…`, `test_debt_collection…`, `test_no_retired…`) are subsumed by `test_surviving_confrontations_are_exactly_the_ported_set`. `[TEST]` | same file | Acceptable belt-and-braces; optional to trim to the exact-set + custom_rules tests. |
| [LOW] | Module docstring "These tests FAIL until that retirement happens … are present in the live pack" is stale now that the tests are GREEN. `[DOC]` | same file:18-21 | Flip to past tense ("retirement applied 2026-06-05; tests now PASS"). |
| [LOW] | `Playtest._send` / `_send_next_action` type `ws: Any` without the rule-3 explanatory comment (pre-existing in the changed file). `[RULE]` | `scripts/playtest.py:666,822` | Add `# websockets connection type varies by version` comment. Non-blocking, pre-existing. |

### Rule Compliance

Enumerated against the Python lang-review checklist (13 checks) + server CLAUDE.md additionals, across the two changed `.py` files and the content YAML:

- **Silent exceptions / No Silent Fallbacks** — `[SILENT]` (specialist disabled, checked by rule-checker + me): COMPLIANT. playtest.py raises `ScenarioError`/`SpanCaptureEmpty`/`HTTPError` loudly; the `--fresh=False` reuse default is a *documented, intentional* default (help text + docstring + cookbook), not a silent fallback. The test file has no except blocks.
- **Type design / annotations** — `[TYPE]` (specialist disabled): one Low finding — `ws: Any` without comment (pre-existing). Test helpers fully annotated (`-> bool`, `-> GenrePack`, `-> set[str]`). `Prompts` model uses `extra="forbid"` (good — misspelled keys fail loud at load).
- **Test quality** — `[TEST]`: assertions are specific (set membership/equality with diagnostic messages), no `assert True`, every `skipif` has a reason. Gaps: no wiring test; guard/loader mismatch; redundancy (above).
- **Security** — `[SEC]` (specialist disabled): no surface — content YAML + a dev-only headless CLI; `yaml.safe_load` used; no injection/secret/auth paths. COMPLIANT.
- **Simplicity** — `[SIMPLE]` (specialist disabled): only the 3-redundant-tests Low note; no over-engineering.
- **Edge cases** — `[EDGE]` (specialist disabled): the relevant edge — pack-not-on-disk — is handled (skipif), though via the mismatched guard noted above.
- **Wiring (CLAUDE.md)** — `[RULE]`: the suite lacks its own wiring test; mechanical wiring is covered by sibling integration suites. No source-text/grep wiring tests present (A4 compliant — runtime model-attribute access only).
- **rules.yaml deletions** — COMPLIANT: surgical removal of exactly the 2 custom_rules + 2 confrontations; the generic `combat`/`negotiation`/`chase` dials are untouched (verified vs the RED tests + pack validation).

### Observations

- `[VERIFIED]` Retirement is surgical — `rules.yaml` removes exactly `ledger_tracking`/`pact_cost_attribution` + `pact_working`/`debt_collection`; surviving set is exactly `{combat, negotiation, chase}` — evidence: preflight `test_surviving_confrontations_are_exactly_the_ported_set` GREEN + `validate pack heavy_metal` PASS (0 errors).
- `[VERIFIED]` `combat:` prompt correctly re-homed — `prompts.yaml:67-78` now frames the cost as "Effort … System Strain … the body pays in blood, breath, and years" (metaphor kept, mechanic corrected). Evidence: the diff.
- `[HIGH][DOC]` But `ritual:` (`prompts.yaml:178`) and `debt_collection:` (`:200`) were missed — they still name retired confrontation types and present the ledger as mechanism. This is the REJECT cause (AC3/AC6).
- `[VERIFIED]` Both stragglers are *unreachable* dead surface — `Prompts.ritual`/`debt_collection` have zero server consumers (grep: only `narrative.py:40-41` declaration; `combat` is read via `gp.combat` at `orchestrator.py:1818`, no `gp.ritual` analogue). This caps the live narration risk to nil but does not satisfy AC3's prompts-review axis.
- `[TEST]` Suite is a content-shape guard with a guard/loader skip mismatch and no wiring test (corroborated by test-analyzer + rule-checker).
- `[VERIFIED]` `--keep`→`--fresh` rename is complete and self-consistent — no stale `--keep` in justfile/scenarios/docs (rule-checker grep); reuse default matches the UI client's `force_new=False`.
- `[SIMPLE]` 3 of 5 retirement tests are redundant with the exact-set test (Low).

### Devil's Advocate

Argue this story is broken. The most dangerous reading: this is the epic's *final* gate, and it ships a "faithful WWN pack" whose narrator prompts still tell the narrator to run a `pact_working` and describe debts "withdrawn from the ledger." I called those blocks unreachable — but how confident am I? My evidence is a grep that found no `gp.ritual` consumer. Genre prompt dispatch is not always static attribute access; if any code path does `getattr(prompts, scene_mood)` or iterates `model_dump()`, then `ritual`/`debt_collection` would resurrect the moment a scene's mood string matched the field name — and the `ritual` mood string *does* exist in the audio layer. I grepped for `getattr(.*prompt` and `model_dump` and found nothing, and `combat` is reached by explicit `gp.combat`, so the pattern is static — but a confused future author who wires `Prompts.ritual` (the field is *right there*, inviting it) would instantly create live dual-truth: the narrator instructed to perform a confrontation type the engine deleted, describing ledger mechanics the engine doesn't run. That is precisely the "winging it" the OTEL lie-detector exists to catch — except prompt-authored dual-truth precedes the lie-detector; it *manufactures* the lie. A career-GM playtester (Keith, Jade) who triggered a ritual scene would get pact/ledger narration with zero mechanical backing and no span trail, because the engine never engaged. For a stressed content author six months from now, the orphaned `debt_collection:` key is a landmine: it looks live (it has a model field), it reads like flavor, and re-wiring it would reintroduce the exact mechanic this epic spent four stories removing. The test suite would not catch any of this — it asserts only `rules.yaml`, never `prompts.yaml`, and TEA explicitly (and correctly) refused a grep test, which means the *only* backstop for prompt-level dual-truth is this review. If I approve, that backstop fails silently. The redundant tests and the guard/loader skip-mismatch compound the risk: if the pack ever moves roots, all five guards skip green, and a reintroduced confrontation type sails through CI. None of this is a crash or data-loss, so it is not Critical — but "no dual-truth content remaining" is the literal acceptance text of AC6, and dead-but-present dual-truth content fails it. The honest verdict is REJECT, and the fix is 20 minutes of content work the Dev has already modeled on the `combat:` block.

**Handoff:** Back to Dev (green rework) — the blocking fix is a content-prose edit (re-home or remove the `ritual:`/`debt_collection:` prompt blocks), not a logic/test-design change. The non-blocking `[TEST]` findings (wiring test, guard/loader idiom, redundancy trim) can be addressed opportunistically in the same pass since they touch the same new test file.

## Dev Assessment (green rework — AC3/AC6 prompts faithful-WWN port)

**Round-trip 1 — blocking finding RESOLVED.** Directed by Keith (2026-06-05): "we are REPLACING ALL THIS WITH the new SRD rules. This is flavor that got into rules. Replace it with faithful port." So the bespoke pact/ledger framing in the prompts is **ported to faithful WWN**, not merely re-homed.

**What changed (content-only — zero server code, epic-87 premise preserved):** `genre_packs/heavy_metal/prompts.yaml`, three prompt blocks where the bespoke ledger was presented as the cost *mechanism*:
- **`ritual:`** (drafted by `writer` subagent, verified by me) — removed the literal retired confrontation-type name `pact_working`; reframed the scene as a WWN High Magic *working* (committing Effort / invoking a High Art / the live `cast_spell` beat). Cost grounded in **Effort committed + System Strain accrued** ("the body is the book"), mirroring the already-fixed `combat:` block. `<rules>` (agency, cost-is-visible) + the YAML key preserved (key is a `extra="forbid"` `Prompts` model field; renaming would need a server change epic 87 forbids).
- **`debt_collection:`** (writer + me) — reframed from a debt being mechanically collected to a **social/narrative** Collector scene: "not a mechanical account being zeroed … the debt itself is a thing that lives in the story, not in a system," resolved through the surviving `negotiation` confrontation or pure narration. Collector voice/atmosphere preserved verbatim.
- **`narrator:`** (me) — the main, **every-turn-consumed** prompt still framed magic-cost as a bare "withdrawal from a ledger" with no WWN grounding (missed by the original review; caught by my post-edit grep). Applied the same light, voice-preserving port: cost now "spends Effort the caster cannot reclaim until they rest and leaves System Strain graven in the body that gated it — a toll the genre keeps like a ledger." All imagery + ornate voice intact.

**Scope judgment (the category-2 line — deliberately NOT swept):** the ledger/debt/account/book idiom is the pack's **core identity** and saturates `char_creation.yaml`, `axes.yaml`, `classes.yaml` ("Read the Ledger", Necromancer "read a living thing's account"), `inventory.yaml` (`ledger_knife`), and the `transition_hints`/`town`/`chargen` prompts as PROSE METAPHOR / scene props. The pack's own doctrine endorses this: `spells_wwn.yaml` header ("the doom-cost feeling re-homes into prose + System Strain, not a bespoke ledger subsystem") and `classes.yaml:297` ("cost is carried in narration and System Strain, not a bespoke ledger"). Per TEA's standing warning (a naive `grep ledger` sweep "would gut the pack's voice"), I ported ONLY the three places that presented the ledger as the literal cost-MECHANISM; the metaphor survives everywhere else. Net rule: *every cost-mechanism statement is now grounded in Effort/System Strain; the ledger/debt imagery survives as flavor.*

**Verification (evidence):**
- `validate pack heavy_metal` → **PASS (0 errors, 7 pre-existing warnings)** — YAML well-formed, `Prompts` `extra="forbid"` satisfied (keys preserved).
- `test_heavy_metal_pact_ledger_retired_87_4.py` → **5 passed** (retirement guards stay GREEN).
- Audit grep: **0** occurrences of `pact_working` / "withdrawal from a ledger" / "ledger now reads" / "what the ledger" in `prompts.yaml`; all three cost-mechanism prompts (`narrator:` L3, `combat:` L72, `ritual:` L181) now name Effort + System Strain.

**AC status after rework:** AC3 ("no prompt text implies pact-ledger mechanics; doom-cost carried by Effort/Strain") — now **MET** (prompts-review axis closed). AC6 ("no dual-truth content remaining") — **MET**. AC1/AC2/AC4 unchanged (done). AC5 resolved via D1 (unchanged).

**Non-blocking Reviewer findings — acknowledged, deferred (not done this pass):** the `[TEST]` findings (no wiring test; `_has_real_content` vs `find_pack_path` guard/loader skip-mismatch; 3 redundant tests; stale "FAIL until" docstring) are test-DESIGN concerns owned by TEA, and the Reviewer marked all four **non-blocking**. I kept the rework tight to the blocking content fix per minimalist-dev discipline + TDD phase ownership (test files are TEA's). They remain captured under `### Reviewer (code review)` for a TEA follow-up; none blocks approval.

## Subagent Results (re-review — round 2)

Re-review scope: rework commit `bcce10c` (sidequest-content `feat/87-4`) — content-only: `prompts.yaml` (3 prompt blocks ported to faithful WWN), `audio.yaml` (dead mood-alias removal), `CLAUDE.md` (asset-status line). **No Python or test files changed this round.**

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 — pack PASS (0 err), retirement suite 5/5 GREEN, `pact_working` 0 matches pack-wide, Effort/Strain present, no audio regression; remaining ledger refs are preserved metaphor (axes/transition_hints) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | no-change | rework diff has 0 `.py`/test files — round-1 findings (guard/loader mismatch, 3 redundant tests, no wiring test) unchanged, all non-blocking | confirmed 0 new, round-1 carried (non-blocking) |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 — all 3 ported blocks RESOLVED (`narrator:`/`ritual:`/`debt_collection:`), cross-block cost model consistent (Effort+Strain), no new stale content | confirmed 0, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | no-change | rework diff has 0 `.py` files — round-1 `ws: Any` (Low, pre-existing) + wiring-test (non-blocking) findings unchanged | confirmed 0 new, round-1 carried (non-blocking) |

**All received:** Yes (2 relevant specialists re-ran on the content diff and returned clean; test/rule specialists have no in-scope changes — round-1 findings stand, all non-blocking; 5 disabled per settings)
**Total findings:** 0 new; the blocking round-1 finding is RESOLVED; 5 round-1 non-blocking findings carried for a TEA follow-up

## Reviewer Assessment (re-review — round 2)

**Verdict:** APPROVED

The round-1 blocking finding (AC3/AC6: `prompts.yaml` presented the retired bespoke ledger as the cost mechanism + named the retired `pact_working` confrontation) is **mechanically resolved** by rework `bcce10c`. Two independent specialists confirm; I verified the diff myself.

**Data flow traced:** narrator turn → `gp.combat`/`gp.narrator` prompt injection (orchestrator.py:1818) → narration. The three cost-mechanism prompts (`narrator:`, `combat:`, `ritual:`) now uniformly ground magic-cost in WWN **Effort + System Strain**; no prompt instructs a bespoke ledger/`pact_working` mechanic. Safe because the narrator can no longer be told to perform a confrontation type the engine deleted.

**Pattern observed:** faithful-port done right — `genre_packs/heavy_metal/prompts.yaml:181` (`ritual:`) mirrors the proven `combat:` template (`:75`): cost named as Effort/Strain, ledger kept only as explicit metaphor ("the body is the book").

**Error handling / invariants:** pack loads under `Prompts` `extra="forbid"` (keys preserved — no server change; epic-87 zero-engine premise intact); `validate pack heavy_metal` = PASS (0 errors); retirement guard suite 5/5 GREEN.

### Rule Compliance (round 2)
Content-YAML-only diff; the Python lang-review checklist has no in-scope Python this round.
- `[SILENT]` / No-Silent-Fallbacks (disabled specialist; checked by me): N/A — no control flow added; the rework is prose.
- `[TYPE]` (disabled): N/A — no type surface changed; `Prompts` model untouched, `extra="forbid"` still satisfied.
- `[SEC]` (disabled): N/A — narrator-prompt prose, no input/auth/secret surface.
- `[SIMPLE]` (disabled): the rework removed dual-truth without adding complexity; prose only.
- `[EDGE]` (disabled): N/A — no branching logic.
- `[TEST]` (re-ran, no-change): round-1 test-design findings (guard/loader skip-mismatch, redundancy, no wiring test) carried — all non-blocking, TEA's lane.
- `[DOC]` (comment-analyzer, clean): the ported prose is internally consistent; round-1 stale "FAIL until" test docstring is a separate non-blocking carry.
- `[RULE]` (re-ran, no-change): round-1 `ws: Any`-without-comment (playtest.py, pre-existing, Low) carried.
- Genre/content rule (ADR-120 "mechanics-in-genre, flavor-in-world" + the pack's own doctrine `spells_wwn.yaml`/`classes.yaml:297`): COMPLIANT — cost-mechanism is Effort/Strain; the ledger idiom is preserved flavor.

### Observations (round 2)
- `[VERIFIED]` `ritual:` retired-type name removed — evidence: preflight grep `pact_working` → 0 matches pack-wide; the block now opens "committing Effort to a casting … invoking a High Art" (prompts.yaml:181).
- `[VERIFIED]` ledger is metaphor not mechanism — evidence: prompts.yaml:191 "The ledger the genre speaks of is kept in Effort committed and Strain accrued — the body is the book"; mirrors `combat:` (`:75`). `[DOC]` comment-analyzer concurs (clean).
- `[VERIFIED]` `debt_collection:` de-mechanized — evidence: prompts.yaml:210 "not about a mechanical account being zeroed … the debt itself is a thing that lives in the story, not in a system"; resolves via the surviving `negotiation` dial.
- `[VERIFIED]` consumed `narrator:` prompt grounded — evidence: prompts.yaml:3 "spends Effort the caster cannot reclaim until they rest and leaves System Strain graven in the body … a toll the genre keeps like a ledger" (simile, not mechanism). This was beyond the round-1 named findings — a correct scope-extension per Keith's directive.
- `[VERIFIED]` no regression — evidence: pack PASS (0 err) incl. the bundled `audio.yaml` change; retirement suite 5/5 GREEN.
- `[TEST]`/`[RULE]` round-1 non-blocking findings carried (no `.py`/test changes this round) — documented for a TEA follow-up.
- `[SIMPLE]` the idiom was preserved pack-wide (no over-sweep) exactly as TEA mandated ("don't gut the voice").

### Devil's Advocate (round 2)
Argue the approval is premature. The rework is prose, and prose is where a narrator "wings it" — did the port merely *relocate* the dual-truth rather than remove it? The strongest attack: the `narrator:` block still contains the words "ledger," "creditors," "the bill," and the ritual: block still says "the body is the book." If a downstream reader (or a future content author) treats "a toll the genre keeps like a ledger" as license to invent a ledger sub-mechanic, haven't we just re-seeded the problem? I pushed on this: the difference is that every cost CLAUSE now names the real WWN mechanic (Effort committed, System Strain accrued) as the operative thing, and the ledger appears only in explicit simile ("like a ledger," "the body is the book") — the same construction the already-approved `combat:` block uses. A narrator following these prompts is told to spend Effort and accrue Strain and *describe* it as a ledger; it is never told to consult or zero a ledger object, and it is never given the name of a confrontation type the engine would reject. Second attack: the `debt_collection:` and `ritual:` prompt fields are still UNCONSUMED dead surface (round-1 finding) — so I approved a story that ships clean-but-dead prompt slots. True, but that is a non-blocking improvement explicitly deferred (removing the fields needs a server change outside epic 87's zero-engine premise, and Keith chose "port" over "remove"); dead-but-correct beats dead-and-wrong, and AC2/AC3/AC6 are about *content presence*, which is now WWN-faithful. Third attack: I only re-ran 2 of 4 enabled specialists. But the rework diff contains zero `.py`/test files — the test-analyzer and rule-checker have literally nothing new to analyze; re-running them would re-surface the same non-blocking round-1 findings, which I have carried explicitly rather than dropped. Fourth: the prompt fields are unreachable, so does AC3 even "fire" in play? It fires on the *prompts-review* axis (the AC's own stated test), and the consumed `narrator:` block — which IS reachable every turn — was the real exposure, and it is now grounded. The honest conclusion: the dual-truth is removed, not relocated; the residue is non-blocking and documented. APPROVE.

**Handoff:** To SM for finish-story (this is the epic-87 final gate — closing 87-4 completes epic 87). DO NOT merge — SM owns PR creation/merge in finish.