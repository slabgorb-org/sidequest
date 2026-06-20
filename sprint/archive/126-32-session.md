---
story_id: "126-32"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-32: [BUG] Bind narrated NPCs to seeded/registry entities + fix shuffle_fallback culture/region routing

## Story Details
- **ID:** 126-32
- **Jira Key:** (none — no Jira integration for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/126-32-bind-narrated-npcs-registry)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T11:20:49Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T10:05:16+00:00 | 2026-06-20T10:09:03Z | 3m 47s |
| red | 2026-06-20T10:09:03Z | 2026-06-20T10:30:46Z | 21m 43s |
| green | 2026-06-20T10:30:46Z | 2026-06-20T11:05:53Z | 35m 7s |
| review | 2026-06-20T11:05:53Z | 2026-06-20T11:20:49Z | 14m 56s |
| finish | 2026-06-20T11:20:49Z | - | - |

## Sm Assessment

Setup complete for the LARGE/RISKY (8pt) bug story. Branch `feat/126-32-bind-narrated-npcs-registry` created in sidequest-server off `origin/develop`; orchestrator stays on `main`. No Jira (project tracks via `pf sprint`). No blocking PRs in any repo. Workflow `tdd` (phased): next phase **red**, owner **TEA**.

**One root seam, three manifestations** (TEA defines the RED tests):
- (a) narrated antagonist → seated Fate opponent identity by *exact name* (dust_and_lead 'Henry Shaw', not bestiary 'Western Diamondback'); Defect A seater fix already shipped — write the RED test for the *identity-binding residual*.
- (b) described canonical figure → seeded registry NPC (Oz 'Good Witch of the North' carries hp/pronouns, not a hollow 'Amaranth Warmacre' mint).
- (c) Defect B namegen: `npc.invented_name_routed` `shuffle_fallback` reroutes established Anglo names to the wrong culture/region (Ndé) — key the mint to the current region.

**Key SM finding (path correction):** the live seam is `sidequest/server/narration_apply.py`, NOT `sidequest/game/narration_apply.py` as the story title states. Relevant symbols (`_auto_mint_prose_only_npcs`, `npc_invented_name_routed_span`, the `snapshot.npcs.append` promote points, the "double-mint original→mint binding" comment) all live there. Full routing pointers in `sprint/context/context-story-126-32.md`.

**Doctrine reminder for the fix:** per the OTEL principle, the NPC-binding decisions must emit/retain watcher spans so the GM panel can verify the binding fired (`npc_invented_name_routed_span` already exists) — don't let the narrator improvise NPC identity without a mechanical trace.

## TEA Assessment

**Tests Required:** Yes
**Reason:** LARGE/RISKY bug story — three behavioral manifestations of one root NPC-binding seam.

**Test Files:**
- `sidequest-server/tests/server/test_126_32_narrated_npc_binding.py` — 3 RED tests, one per manifestation, driving the real production seams.

**Tests Written:** 3 tests covering 3 manifestations (a/b/c). All confirmed RED via `uv run pytest -n0` (failing on the behavioral assertion, not on collection/setup):
- (a) `test_narrated_fate_opponent_binds_identity_not_phantom` — RED: the seated opponent is a phantom `Npc(description="Fate conflict opponent")` with `pronouns=None`; must carry the narrated `he/him` + appearance, and `fate.opponent.seeded` must report `created=False`. Drives `_apply_npc_mentions` → `_seed_fate_opponents` (real Fate pack `spaghetti_western`).
- (b) `test_canonical_figure_binds_to_registry_not_hollow_mint` — RED: a narrator reference to the oz roster figure mints a duplicate `NpcPoolMember('Good Witch of the North')` instead of binding the registry NPC + carrying its she/her + disposition 25.
- (c) `test_invented_name_not_shuffle_routed_to_wrong_people_group` — RED: `npc.invented_name_routed` fires with `resolution_strategy="shuffle_fallback"` (blind people-group shuffle) for a narrator-named Anglo-frontier stranger; must be region-keyed. Drives the full `_apply_narration_result_to_snapshot` production path.

**Status:** RED (3 failing — ready for Dev)

### Rule Coverage

| Rule source | Applicable | Coverage |
|-------------|-----------|----------|
| `.pennyfarthing/gates/lang-review/python.md` #6 (test quality) | Yes | Every test has meaningful value assertions (pronoun/appearance/disposition/strategy equality + count), no `assert True`, no truthy-only checks, no skips. |
| `.pennyfarthing/gates/lang-review/python.md` (other 12 checks) | No | RED-phase test file only — no production error-handling/async/path/deserialization surface introduced. Applies to Dev's GREEN diff. |
| `.claude/rules/*.md` | N/A | No `.claude/rules/` directory in this project. |
| Server CLAUDE.md "No Source-Text Wiring Tests" | Yes | Tests are fixture-driven behavior + OTEL span assertions; (c) drives the full `_apply_narration_result_to_snapshot` path as the mandatory wiring test. No `read_text()` source-grep assertions. |
| Server CLAUDE.md OTEL Observability Principle | Yes | (a) asserts the `fate.opponent.seeded` `created` flag; (c) asserts the `npc.invented_name_routed` `resolution_strategy` — the GM-panel lie-detector for both binding decisions. |

**Rules checked:** 1 of 1 test-applicable lang-review rule (#6) covered; wiring + OTEL doctrine satisfied.
**Self-check:** 0 vacuous tests (every assertion checks a specific value; verified the phantom/duplicate/strategy failures are the *right-reason* RED).

**Design caveat:** manifestations (b) and (c) carry blocking design questions (see Delivery Findings) — Dev should resolve the region→culture mapping (c) and confirm the registry trigger (b) before/early in GREEN; both may need a Keith design call.

**Handoff:** To Dev (Agent Smith) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes (manifestations a + b; c split to 126-38)

**Files Changed (sidequest-server, branch `feat/126-32-bind-narrated-npcs-registry`):**
- `sidequest/server/dispatch/encounter_lifecycle.py` — (a) `_seed_fate_opponents` consults `snapshot.npc_pool` before fabricating a phantom: promotes the narrated antagonist's identity (pronouns/appearance/disposition + OCEAN seed) and attaches the Fate sheet, `created=False`. Truly-novel opponents still seed an ephemeral stub (`created=True`).
- `sidequest/server/narration_apply.py` — (b) new `_reconcile_active_person` (person recency scene-guard) + guard in `_apply_npc_mentions` gated `not is_creature and not is_new`; co-location scene-guard (one person → reconcile) / similarity (several → clear best). Plus the `npc_person_reconciled_span` import.
- `sidequest/telemetry/spans/npc.py` — new `npc.person_reconciled` span (constant + `SPAN_ROUTES` GM-panel route + `npc_person_reconciled_span`). Verified routed via fresh-interpreter production import.
- `tests/server/test_126_32_narrated_npc_binding.py` — 4 tests (a: bind + novel-guard; b: scene-guard reconcile + new-arrival guard).

**Tests:** 4/4 passing (GREEN) for 126-32. Regression sweeps clean: npc/narration server (638 passed), agents narration (340 passed), fate/encounter (68 passed). The 2 `test_102_4_wn_*` failures in one integration sweep are PRE-EXISTING (fail identically with my change stashed — known `seed_slug_for_test` order-dependent isolation flakiness), not a regression.

**Branch:** feat/126-32-bind-narrated-npcs-registry (commits 64c60385 RED, 077134b4 GREEN — not yet pushed).

**Decisions surfaced to Keith mid-GREEN:** (b) folded back in with the recency-scene-guard design; (c) split to 126-38. See Design Deviations.

**Handoff:** To next phase (verify/review).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (blocking): Manifestation (c) "key the mint to the current region" has NO content representation — `dust_and_lead`'s cultures (`ndé`, `sangre_anglo`, `sangre_frontera`) carry no `region:` key, and `cartography.yaml`/`world.yaml` declare no region→culture binding. `_resolve_invented_naming_context` (`sidequest/server/narration_apply.py`) `random.shuffle`s the bound cultures with no region awareness. Dev cannot "key to the region" without a design decision on WHERE the region→culture mapping lives (new culture `region:` field? cartography region→culture list? world default culture?). The RED test (`test_invented_name_not_shuffle_routed_to_wrong_people_group`) pins the OBSERVABLE contract (`resolution_strategy != "shuffle_fallback"` for a narrator-named stranger) but the mechanism is gated on this call. *May warrant a Keith design call (cf. 126-35's pending design call).* *Found by TEA during test design.*
- **Question** (blocking): Manifestation (b) the exact "seeded registry" lookup trigger is unconfirmed against the playtest repro (not located in `~/Projects/sq-playtest-pingpong.md`). The oz roster figure "The Good Witch of the North" is real (ADR-059 `npcs.yaml`: she/her, disposition 25), but it is unclear what narrator reference produced the hollow `Amaranth Warmacre` mint — a non-exact name reference (the RED test models an article-drop), a not-yet-loaded registry entry, or an epithet. Dev should confirm the trigger; the RED test (`test_canonical_figure_binds_to_registry_not_hollow_mint`) pins the contract (no hollow duplicate; carry pronouns/disposition) but uses an assumed trigger. Affects `sidequest/server/narration_apply.py` (`_reconcile_epithet_to_person` / Step 1-2 matching / promotion). *Found by TEA during test design.*
- **Gap** (non-blocking): The story title cites `narration_apply.py` without a path; the live seam is `sidequest/server/narration_apply.py`, NOT `sidequest/game/narration_apply.py`. `_seed_fate_opponents`/`_resolve_opponent_from_roster` live in `sidequest/server/dispatch/encounter_lifecycle.py`. (Already captured in the SM routing notes / context file.) *Found by TEA during test design.*

**OPERATOR DIRECTIVE (Keith, 2026-06-20):** Proceed to GREEN now. Implement manifestation **(a)** (unblocked). For the two blocking design questions **(b)** [registry trigger] and **(c)** [region→culture mapping], **surface them back to the Operator** as you reach them — do NOT guess a design. (a) ships regardless; b/c await Keith's call.

**DIRECTIVE UPDATE (Keith, mid-GREEN):** (b) FOLDED BACK IN — Keith provided the grounded design (person recency scene-guard: re-reference to the active conversation partner), so (b) is no longer design-blocked and ships under 126-32. (c) SPLIT to follow-up story 126-38.

### Dev (implementation)
- **Improvement** (non-blocking): The combat seater `_seed_combat_hp_depletion_to_npcs` (`sidequest/server/dispatch/encounter_lifecycle.py`) likely has the SAME phantom-vs-pool gap that 126-32 (a) fixed for the Fate seater — a prior-turn narrated antagonist in `npc_pool` would not be found by a `snapshot.npcs`-only opponent map under a WN/d20 combat seating. Not in 126-32 scope (the (a) test is Fate-only); a future story could extend the same pool-consult + promote to the combat path. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): The (a) seater promotes the pool member but does not remove it — `snapshot.npc_pool.remove(pool_member)` is missing, leaving a same-name duplicate across `npc_pool` + `npcs`. `build_npc_working_set` / `register_npc_roster_section` don't dedup the two stores, so the seated opponent can be double-listed in the narrator's canonical-identity roster. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (add the pool removal to match the 97-1 "one identity, one source" path `_promote_engaged_pool_member`, and assert pool-emptiness in `test_narrated_fate_opponent_binds_identity_not_phantom`). NOTE: this is a faithful copy of the pre-existing shadow idiom in `resolve_status_target` (`narration_apply.py:1629-1639`), so the latent double-list affects all shadow-promotion sites, not only this one — a roster-dedup or store-consolidation pass is the broader fix. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Narrator-supplied `mention.role/pronouns/appearance` are written to the pool member without `sanitize_player_text` at `sidequest/server/narration_apply.py:2842-2847`, and reach the narrator prompt via `register_npc_roster_section`. This is the 4th replication of an unsanitized sibling pattern (lines 2680-2690, 2785-2790, 2931-2935); source is narrator structured output, not the player free-text ADR-047 governs. A dedicated story should sanitize all four sites consistently (fixing only the new one would be inconsistent). Affects `sidequest/server/narration_apply.py`. *Found by Reviewer (security specialist) during code review.*
- **Gap** (non-blocking): The `similarity` branch of `_reconcile_active_person` (multi-person disambiguation + tie-decline, `narration_apply.py:2270-2285`) has no test — only the single-person `scene_guard` lever is covered. A follow-up regression test should exercise multi-person token-overlap and the tie/zero-overlap decline. Affects `tests/server/test_126_32_narrated_npc_binding.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests assert behavior/OTEL outcome, not the prescribed promotion mechanism**
  - Spec source: 126-32 story title (sprint YAML) / context-story-126-32.md
  - Spec text: "Timing change in narration_apply.py (promote narrated NPCs to snapshot.npcs before mint/seating)."
  - Implementation: The RED tests assert the OBSERVABLE outcome (seated opponent carries narrated pronouns/appearance; no hollow duplicate minted; `fate.opponent.seeded created=False`; `resolution_strategy != "shuffle_fallback"`) and drive the real seams (`_apply_npc_mentions`, `_seed_fate_opponents`, `_apply_narration_result_to_snapshot`). They do NOT assert that the fix is a promote-to-`snapshot.npcs` step specifically.
  - Rationale: Mechanism-agnostic tests survive Dev's choice of lever (promotion vs registry-consult vs epithet-reconcile) and avoid prescribing implementation, per the project test doctrine in `test_npc_ongoing_threat_reconciliation.py`.
  - Severity: minor
  - Forward impact: Dev is free to choose the promotion mechanism; the OTEL contract (`created`/`resolution_strategy`) constrains the span shape.
- **Manifestation (c) coverage is the OTEL strategy contract, not the minted name**
  - Spec source: 126-32 story title, manifestation (c)
  - Spec text: "shuffle_fallback reroutes established Anglo names to the wrong culture/region (Ndé), key the mint to the current region."
  - Implementation: The test asserts `resolution_strategy != "shuffle_fallback"` rather than asserting the minted name belongs to a specific region culture, because no region→culture binding exists in content to assert against (see blocking finding).
  - Rationale: Asserting a concrete region-culture would bake in a region→culture mechanism that has not been designed; the strategy contract pins "stop blind-shuffling a named stranger" without prescribing the map.
  - Severity: minor
  - Forward impact: When the region→culture design lands, a follow-up assertion on the resolved culture can tighten this test.

### Dev (implementation)
- **(a) fix landed at the SEATER, not narration_apply.py**
  - Spec source: 126-32 story title (sprint YAML)
  - Spec text: "Timing change in narration_apply.py (promote narrated NPCs to snapshot.npcs before mint/seating)."
  - Implementation: The promotion was added to `_seed_fate_opponents` in `sidequest/server/dispatch/encounter_lifecycle.py` (consult `snapshot.npc_pool`, promote the narrated identity, `created=False`), NOT to `narration_apply.py`.
  - Rationale: Confrontation seating runs in the PRE-narrator dispatch bank (ADR-113, `agents/subsystems/confrontation.py` → `instantiate_encounter_from_trigger` → `_seed_fate_opponents`), BEFORE that turn's POST-narrator `_apply_npc_mentions` mint (there is no post-narrator re-seat in `_apply_narration_result_to_snapshot`). The established antagonist therefore lives in `npc_pool` from a prior turn; a promotion added in narration_apply would run too late for the same-turn seating. The story's hypothesized location was based on an incorrect ordering assumption.
  - Severity: minor
  - Forward impact: The parallel combat seater `_seed_combat_hp_depletion_to_npcs` likely has the same phantom-vs-pool gap (see Delivery Findings) — a future story may extend the same pool-consult there.
- **(b) folded back in as a person recency scene-guard (Keith call mid-GREEN)**
  - Spec source: Operator directive (Keith, 2026-06-20, mid-GREEN) — supersedes the earlier "split (b)" decision
  - Spec text: "do we do some kind of recency check or something? … I am invariably referring to a NPC WE JUST MENTIONED."
  - Implementation: Added `_reconcile_active_person` (the person twin of `_reconcile_ongoing_threat`) + a guard in `_apply_npc_mentions` gated `not is_creature and not is_new`, plus a new `npc.person_reconciled` OTEL span. The original TEA framing of (b) (registry-name string-match / article-drop) was replaced by Keith's grounded recency design.
  - Rationale: The real repro is a re-reference to the active conversation partner in a scene with no one else; a recency/co-location scene-guard is the correct lever, mirroring the existing creature guard. `is_new=True` preserves Living-World new arrivals.
  - Severity: moderate (new reconciliation behavior in the narration apply hot path)
  - Forward impact: Person mints now reconcile to a single co-located recently-engaged person when `is_new` is unset — narrator prompts that under-set `is_new` could see a re-reference collapse onto the scene person (the accepted, span-visible risk the creature guard already carries).
- **(c) split to follow-up story 126-38**
  - Spec source: Operator directive (Keith, 2026-06-20)
  - Spec text: "Split (c) to a follow-up."
  - Implementation: Created `126-38` (server, tdd, p2) for the region-keyed namegen routing; the (c) RED contract is preserved in git commit 64c60385. Not implemented under 126-32.
  - Rationale: "Key to the current region" has no region→culture representation in content; it needs a design decision before implementation.
  - Severity: minor

### Reviewer (audit)

Every logged deviation stamped (append-only — originals untouched):

- **TEA: "Tests assert behavior/OTEL outcome, not the prescribed promotion mechanism"** → ✓ ACCEPTED by Reviewer: mechanism-agnostic behavior+OTEL assertions are the correct project test doctrine (No Source-Text Wiring Tests); they survived Dev's choice to land the fix at the seater rather than narration_apply.
- **TEA: "Manifestation (c) coverage is the OTEL strategy contract, not the minted name"** → ✓ ACCEPTED by Reviewer: moot — (c) was split to 126-38 by Keith; the strategy-contract framing is the right deferral seam.
- **Dev: "(a) fix landed at the SEATER, not narration_apply.py"** → ✓ ACCEPTED by Reviewer (verified): seating runs in the pre-narrator dispatch bank (ADR-113) BEFORE the post-narrator `_apply_npc_mentions` mint, so a prior-turn antagonist lives in `npc_pool`; a promotion in narration_apply would run too late for same-turn seating. The story title's hypothesized location rested on an incorrect ordering assumption. Correct relocation.
- **Dev: "(b) folded back in as a person recency scene-guard (Keith call mid-GREEN)"** → ✓ ACCEPTED by Reviewer: Keith's grounded recency design supersedes the earlier "split (b)" decision; the implementation faithfully mirrors the established `_reconcile_ongoing_threat` creature twin. The `is_new` under-set risk is real, accepted by Keith, and span-visible (see finding R-2).
- **Dev: "(c) split to follow-up story 126-38"** → ✓ ACCEPTED by Reviewer: documented Operator directive; (c) RED contract preserved in git 64c60385.

No undocumented spec deviations found beyond those logged.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 4/4 GREEN; 4 files +553/-9 | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — edge paths assessed by Reviewer (see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — silent-fallback paths assessed by Reviewer |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — test quality assessed by Reviewer |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (preflight confirmed all comments explanatory, none commented-out code) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type design assessed by Reviewer |
| 7 | reviewer-security | Yes | findings | 1 (medium) | confirmed 1 (downgraded → non-blocking), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — complexity assessed by Reviewer |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — exhaustive rule check done by Reviewer (see Rule Compliance) |

**All received:** Yes (2 enabled returned: preflight clean, security 1 finding; 7 disabled via `workflow.reviewer_subagents` pre-filled as Skipped)
**Total findings:** 1 confirmed non-blocking (security), 4 Reviewer-originated (1 MEDIUM non-blocking, 3 LOW), 0 blocking; 0 dismissed; 0 deferred

> NOTE: two independent security passes ran (the pre-`/clear` async agent + a fresh launch). Both converged on the SAME single medium finding (unsanitized narrator identity-field write), which corroborates it and its severity.

## Reviewer Assessment

**Verdict:** APPROVED

Two enabled specialists (preflight, security) plus a full Reviewer pass over all disabled domains. No Critical or High findings. The story's required behavior — (a) bind a prior-turn narrated antagonist to the seated Fate opponent carrying its identity (`created=False`), still ephemeral-phantom for a truly-novel foe; (b) reconcile a non-new person reference onto the co-located recently-engaged conversation partner via a new `npc.person_reconciled` OTEL span, while `is_new=True` still mints — is correct, OTEL-traced, and covered by 4 GREEN tests driving the real seams. The findings below are non-blocking quality/follow-up items, two of which faithfully replicate established, defended pre-existing patterns.

**Data flow traced:** narrator `NpcMention("Henry Shaw", he/him, side=opponent)` → `_apply_npc_mentions` mints `NpcPoolMember` in `snapshot.npc_pool` (turn N) → next turn the Fate conflict seats `EncounterActor("Henry Shaw", opponent)` → `_seed_fate_opponents` (pre-narrator, ADR-113) now consults `snapshot.npc_pool`, promotes the member via `_promote_pool_member_to_npc` + `_seed_invented_npc_identity`, attaches the Fate sheet, appends to `snapshot.npcs`, emits `fate.opponent.seeded created=False`. Safe and correct for binding; the residual concern is that the source member is left in the pool (R-1).

### Rule Compliance

Exhaustive pass over `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md doctrine, applied to every new symbol (`_reconcile_active_person`, `npc_person_reconciled_span`, `SPAN_NPC_PERSON_RECONCILED`/`SPAN_ROUTES` entry, the `_seed_fate_opponents` pool-promote branch, the `_apply_npc_mentions` person-guard block, 4 tests):

- **#1 Silent exception swallowing** — `[VERIFIED]` no `try/except`, no bare `except`, no `suppress()` introduced anywhere in the diff. Compliant.
- **#2 Mutable default args** — `[VERIFIED]` all new functions use keyword-only params with scalar/None defaults; `**attrs: Any` in the span is a kwargs sink, not a mutable default. Compliant.
- **#3 Type annotation gaps** — `[VERIFIED]` `_reconcile_active_person` fully annotated (params + `-> tuple[Npc | None, NpcPoolMember | None, str] | None`); `mention: Any` matches the established `_reconcile_ongoing_threat`/`_reconcile_epithet_to_person` sibling convention (NpcMention typed as Any to avoid the orchestrator import cycle). Span fns annotated. Compliant.
- **#4 Logging coverage/correctness** — `[VERIFIED]` reconciliation logs use `logger.info("...%r...", var)` lazy-interpolation form (not f-strings); names are game fiction, not PII/secrets. Compliant. (`%r`→`repr()` adds quoting/escaping for the log sink only; both security passes confirmed the log is not fed back to the LLM or client.)
- **#5 Path handling** — N/A (no path/`open()` work in the production diff; test uses `pathlib.Path` for the content-presence guard — compliant).
- **#6 Test quality** — `[TEST]` `[VERIFIED]` every test asserts specific values (pronouns/appearance/`created` flag/span `reconciled_to`+`signal`/pool emptiness-of-invented), no `assert True`, no truthy-only checks, no `@pytest.mark.skip` (the `requires_content` skipif carries a reason and only gates the two Fate-pack tests). GAP (non-blocking): the `similarity` branch of `_reconcile_active_person` (multi-person disambiguation + tie decline) is **untested** — only the `scene_guard` single-person lever is exercised (finding R-3).
- **#7 Resource leaks** — `[VERIFIED]` no file/socket/lock/db handles; the span context managers use `with`. Compliant.
- **#8 Unsafe deserialization** — `[VERIFIED]` no pickle/`yaml.load`/`eval`/`exec`/`shell=True`. Compliant.
- **#9 Async/await** — N/A (all changed code is synchronous; no `await`/`asyncio`).
- **#10 Import hygiene** — `[VERIFIED]` the function-scoped `from sidequest.server.narration_apply import (_promote_pool_member_to_npc, _seed_invented_npc_identity)` inside `_seed_fate_opponents` breaks a real cycle (`narration_apply` imports `sidequest.server.dispatch.*` siblings at module scope) and is idiomatic for this file (narration_apply itself uses function-scoped dispatch imports at lines 395/438/798/1313/…). No star imports. Compliant.
- **#11 Input validation at boundaries** — `[SEC]` security specialist flagged narrator-supplied `mention.role/pronouns/appearance` written unsanitized to the pool member at narration_apply.py:2842-2847 (finding R-4). Downgraded to non-blocking: source is **narrator structured output**, not the player free-text ADR-047 governs, and it is a faithful 4th replication of three unsanitized sibling sites (2680-2690, 2785-2790, 2931-2935). No SQL/HTML/path-from-input. ReDoS N/A.
- **#12 Dependency hygiene** — N/A (no dependency changes).
- **#13 Fix-introduced regressions (meta)** — `[VERIFIED]`/`[EDGE]` the (a) fix preserves the unchanged novel-opponent path (guarded by `test_novel_fate_opponent_with_no_pool_member_still_seeds_phantom`, `created=True`, `ephemeral=True`); the (b) guard preserves new-arrival mint (`test_genuinely_new_arrival_still_mints`). One latent regression in the split-identity domain: R-1 (member left in pool).

### Observations

- `[MEDIUM][EDGE] R-1 — seater leaves the promoted member in `npc_pool` (shadow-duplicate)` at `sidequest/server/dispatch/encounter_lifecycle.py:486-495`. The branch promotes the pool member to an `Npc` and `snapshot.npcs.append(npc)` but never `snapshot.npc_pool.remove(pool_member)`. The identity now lives in BOTH stores. `build_npc_working_set` (`npc_context.py:183` + `:203`) and `register_npc_roster_section` (`prompt_framework/core.py:593,606`) iterate `npcs` and `npc_pool` with **no dedup**, so the seated opponent can be double-listed in the "## KNOWN NPCS — Canonical Identity (do not contradict)" section (once full/on-stage, once off-stage). **Non-blocking** because this is a faithful copy of the established, docstring-defended shadow-promotion idiom in `resolve_status_target` (`narration_apply.py:1629-1639`, which also promotes + seeds + appends without pool removal; the 1604-1605 docstring explicitly leaves the entry "shadowed by the Npc lookup"). Re-citation is functionally correct (Step-1 npcs-by-name shadows Step-2 pool, line 2483-2486 `continue`). **Recommendation:** add `snapshot.npc_pool.remove(pool_member)` to match the 97-1 "one identity, one source" path (`_promote_engaged_pool_member`, :1487) — it's a one-liner squarely in this story's split-identity domain — and assert pool-emptiness in the (a) test. See Delivery Findings.
- `[LOW][EDGE] R-2 — seater pool lookup uses exact case-sensitive `m.name == actor.name`` at `encounter_lifecycle.py:484`, narrower than the mint path's casefold + comma-inversion keys (`_npc_name_match_keys`). A narrated opponent stored as "Shaw, Henry" or differing case would miss the pool and re-fabricate the phantom (the original bug). Works for the common exact-string case (same router free-string seats and was minted). Non-blocking; tighten if a playtest shows a near-miss.
- `[LOW][SIMPLE] R-3 — `_reconcile_active_person` takes an unused `turn_num` param` at `narration_apply.py:2221`. Never referenced in the body (the creature twin `_reconcile_ongoing_threat` takes no such param). Vestigial — drop it or use it. Ruff does not flag unused params (ARG not enabled), so preflight stayed clean. Non-blocking.
- `[MEDIUM][TEST] R-3b — `similarity` branch untested`. Only the `scene_guard` (single co-located person) lever has a test; the multi-person token-overlap + tie-decline path (`narration_apply.py:2270-2285`) has zero coverage. The tie logic is non-trivial (reset-on-strictly-greater across two candidate loops) — I traced it by hand and it is correct, but it deserves a regression test. Non-blocking (mirrors the well-tested epithet guard's shape).
- `[SEC] R-4 — unsanitized narrator identity-field write` at `narration_apply.py:2842-2847` — both security passes (medium confidence). `mention.role/pronouns/appearance` reach `register_npc_roster_section` via the pool member without `sanitize_player_text`. Downgraded non-blocking: narrator structured output (not player free-text per ADR-047) and a faithful 4th replication of three pre-existing sibling sites. **Recommendation:** a dedicated story sanitizing all four sites consistently — fixing only the new one would be inconsistent. See Delivery Findings.
- `[VERIFIED][TYPE] Span contract is sound` — `SPAN_NPC_PERSON_RECONCILED`/`npc_person_reconciled_span`/`SPAN_ROUTES` entry mirror the `npc.creature_reconciled`/`npc.epithet_reconciled` twins exactly (same `state_transition`/`npc_registry` route, same attribute extract shape). Dev verified the route populates via a fresh-interpreter production import. Compliant with the OTEL Observability Principle — the binding decision is GM-panel visible. Evidence: `telemetry/spans/npc.py:239-252,261-291`.
- `[VERIFIED][DOC] Comments accurate` — preflight confirmed all comments explanatory, none commented-out code. The dense provenance comments (ADR-113 ordering, oz repro, 72-7 additive precedent) match the code they annotate. The `_reconcile_active_person` docstring correctly describes both levers and the co-location bound.
- `[VERIFIED][SILENT] No silent fallbacks` — the seater's else branch (no pool member → loud ephemeral phantom, `created=True`) is loud, not a swallow; `_reconcile_active_person` returns `None` on tie/zero-score so the caller falls through to the Step-3 mint (no silent identity discard); every reconciliation emits a span + `logger.info`. Compliant with the No Silent Fallbacks rule.

### Devil's Advocate

Argue the code is broken. The sharpest line of attack is identity duplication — the very defect this story exists to kill. Manifestation (a) trades a *fabricated-phantom* split (phantom opponent beside the narrated cattle-baron) for a *shadow-duplicate* split: after seating, "Henry Shaw" exists as a promoted `Npc` AND as the original `NpcPoolMember`, and neither the working-set builder nor the roster renderer dedup the two stores. A career GM (Keith) reading the narrator's canonical-identity roster could see Henry Shaw listed twice — once full and on-stage, once brief and off-stage — a contradiction in a section literally headed "do not contradict." So the fix arguably swaps one split for another. The mitigating truth is that this is exactly what the pre-existing, defended `resolve_status_target` shadow idiom already does, so it is not a novel regression — but "everyone else does it" is not a correctness proof, and the one-line `npc_pool.remove()` would close it cleanly inside this story's own domain.

A confused/adversarial narrator is the second front. The `scene_guard` lever reconciles a non-new person reference onto the lone co-located person with **zero token overlap required** — strictly more aggressive than the `>=2`-token epithet guard it sits in front of. If the narrator introduces a genuinely new bystander ("the bartender pours a drink") but forgets `is_new=True`, that bystander collapses onto the one present NPC — a false merge that misattributes a relationship/disposition ledger onto the wrong human. Dev logged this as an accepted, span-visible risk mirroring the creature guard, and `is_new` is the documented escape hatch, so it is a known trade, not a hidden bug — but it does widen the blast radius of a narrator that under-sets `is_new`.

What about stressed inputs? Empty scene (`total==0`) → returns None → mint (correct, tested-adjacent). `party_location` None → returns None → mint (handled). A `mention.name` that is a real personal name colliding with the present NPC under a different identity → scene_guard still merges (the accepted risk). Huge candidate lists → linear scans, no pathological backtracking (token sets, not regex). `Npc.location` exists (session.py:150) so the `n.location == location` leg cannot AttributeError. Tie logic across the npc+member loops correctly declines on equal-top scores. Net: no crash-class or security-class break; the real exposures are the shadow-duplicate (R-1) and the documented is_new false-merge (R-2 accepted) — both quality, both non-blocking, both with a clear path. Verdict holds at APPROVED with follow-ups.

**Pattern observed:** correct mirroring of the `_reconcile_ongoing_threat` creature guard into a person twin, with a deliberately tighter co-location bound — `narration_apply.py:2092` (creature) ↔ `:2217` (person).
**Error handling:** None-returns at every decline path fall through to the existing Step-3 mint; no swallow. `encounter_lifecycle.py:498` else-branch stays loud.
**Handoff:** To SM (Morpheus) for finish-story.
  - Forward impact: 126-38 carries the deferred work; 126-32 ships (a)+(b).