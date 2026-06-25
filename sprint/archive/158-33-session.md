---
story_id: "158-33"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-33: Monster Manual cross-world bestiary bleed — MM injection seeds sibling-world creatures (long_foundry into barsoom); scope pre-gen to the current world's bestiary

## Story Details
- **ID:** 158-33
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/158-33-mm-bestiary-world-scope)
- **Repos:** server, content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T19:30:50Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T18:58:16.975340Z | 2026-06-25T19:01:32Z | 3m 15s |
| red | 2026-06-25T19:01:32Z | 2026-06-25T19:14:21Z | 12m 49s |
| green | 2026-06-25T19:14:21Z | 2026-06-25T19:23:18Z | 8m 57s |
| review | 2026-06-25T19:23:18Z | 2026-06-25T19:30:50Z | 7m 32s |
| finish | 2026-06-25T19:30:50Z | - | - |

## Sm Assessment

**Story:** 158-33 — Monster Manual cross-world bestiary bleed. p2, 2 pts, tdd, repos server + content.

**Setup verdict:** Ready for RED. Session + context written, status `in_progress`, branches `feat/158-33-mm-bestiary-world-scope` created in both sidequest-server and sidequest-content (base `develop`). No Jira (skipped per empty key). Merge gate clear — the only open PR is Dependabot server #1063, not a sprint-story PR.

**Routing rationale:** Phased `tdd` → next owner is TEA (Argus Panoptes) for the RED phase. This is a scoping bug with a concrete, reproducible signature (named sibling-world creatures in barsoom's MM; `monster_manual.injected world=barsoom patches=7`), so it is well-suited to a failing-test-first approach. I enriched the context with the server seam (`monster_manual.py` seeding, `pregen.py` `_seed_authored_npcs`, `loader.py` genre-tier vs world-tier `effective_bestiary` merge) and draft ACs so TEA has a strong target — TEA owns confirming/replacing them.

**Risk flags handed to TEA/Dev:**
- *Don't empty the pool.* The fix scopes the source; AC-2 guards against regressing to the 87-4 silently-empty-pool failure mode.
- *Test-pollution trap.* Synthetic fixture packs only; monkeypatch real-content resolvers to tmp (the `materialize()`-pollutes-real-content hazard).
- *Content invariants belong in the pack validator, not unit tests* — world-ownership of the heavy_metal bestiaries (AC-5) goes to the validator.
- *OTEL is the lie-detector.* Per the project principle, surface world-scoping in `monster_manual.injected` so the GM panel proves the fix engaged.
- *Cross-check 158-21..25* (WWN bestiary curation) before assuming this is longstanding — they may have changed MM source scoping.

**Two-repo note:** server holds the scoping logic (the fix); content holds the world-ownership verification (likely validator-only). Both branches exist; Dev/TEA decide where the change lands.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): The CONTENT repo needs no change — this is a pure server-side stale-cache bug. barsoom's `genre_packs/heavy_metal/worlds/barsoom/bestiary.yaml` is already correct (owns Banth/White Ape/Apt/Calot/Thern Zealot/Plant-Man/Kaldane/Sith; does NOT contain the long_foundry creatures), and `pack.effective_bestiary("barsoom")` already returns it (source=`world`). Affects nothing in `sidequest-content` (the `content` branch may end up empty — Dev/Reviewer should decide whether to keep it). *Found by TEA during test design.*
- **Gap** (non-blocking): The real failing path is a STALE PERSISTED MANUAL, not live seeding. The foreign creatures sit in `~/.sidequest/manuals/heavy_metal_barsoom.json` as two encounter blocks (`enemies=[Foundry Automaton×2]` and `[Knight of the Ashen Banner, Grave Knight]`), seeded under the pre-ADR-120 genre-tier bestiary and never re-validated after creatures moved to per-world bestiaries. Affects `sidequest/server/dispatch/monster_manual_inject.py::ensure_loaded` (needs a foreign-bestiary purge alongside the existing `purge_ruleset_incoherent_encounters`) and `sidequest/game/monster_manual.py` (needs the new `purge_foreign_bestiary_encounters` method). *Found by TEA during test design.*
- **Improvement** (non-blocking): Consider a pack-validator check that no world's `bestiary.yaml` names a creature owned solely by a sibling world (a content-side tripwire for future bleed). Out of scope for this 2-pt cache fix; belongs in the content validator per "content invariants go in the validator, not unit tests." Affects `sidequest-content` pack validator. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking): Confirmed TEA's finding — the `sidequest-content` branch `feat/158-33-mm-bestiary-world-scope` has ZERO changes (the fix is entirely server-side; barsoom's bestiary was already correct). SM/Reviewer should close that content branch without a PR rather than open an empty one. Affects the finish flow (one repo to merge, not two). *Found by Dev during implementation.*
- **Improvement** (non-blocking): A stray `~/.sidequest/manuals/heavy_metal_.json` (empty world-slug key) exists on the dev machine — a pre-chargen/no-world seed, NOT part of this bug (its `effective_bestiary("")` resolves to the genre tier, which heavy_metal lacks, so it cannot hold foreign creatures). Left as-is; flagging only so it isn't mistaken for bleed in future forensics. Affects nothing in code. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Add an `else: logger.warning(...)` (or OTEL span) when `getattr(pack, "effective_bestiary", None)` is absent so a non-`GenrePack` pack reaching `ensure_loaded` fails loud instead of silently skipping the cross-world purge. Affects `sidequest/server/dispatch/monster_manual_inject.py:182` (the silent-skip guard). Not production-reachable today (`_SessionData.genre_pack` is typed `GenrePack`); harden only if a partial/shim pack type is introduced. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The encounter↔bestiary join is name-verbatim (shared with `purge_ruleset_incoherent_encounters` and `pregen._encounter_factions`). If a future encountergen change ever decorates enemy names (suffixes/pluralization), all three name-keyed paths would misfire (over-purge or mis-tag). Affects `sidequest/cli/encountergen/encountergen.py::generate_enemy_from_bestiary` (keep names verbatim, or introduce a stable `creature_id`). Pre-existing systemic assumption, not introduced here. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): When both the ruleset-incoherent purge and the foreign purge fire in one `ensure_loaded`, `manual.save()` is called twice (`monster_manual_inject.py:149` and `:186`). Harmless (idempotent JSON write); optional `needs_save`-flag consolidation. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Fix mechanism is purge-on-load, not seeding-source scoping**
  - Rationale: The story's invariant (no sibling-world creatures in a world's MM) is preserved; only the failing seam differs. Fixing the seed source alone would leave the existing `heavy_metal_barsoom.json` (and any peer manual seeded in that era) corrupt forever — the reported bug would persist on Keith's machine.
  - Severity: minor
  - Forward impact: Dev implements a model purge method + `ensure_loaded` wiring + a `monster_manual.foreign_purged` OTEL span; the `content` repo branch is likely unused (see Delivery Findings). AC-4 (OTEL) and AC-2 (don't-empty-the-pool) are unchanged and fully covered.
- **Scope narrowed to encounter enemies (not NPCs)**
  - Rationale: Purging the encounter source removes the injected creature-NPCs downstream; a separate NPC purge would be dead code against a path that cannot bleed.
  - Severity: minor
  - Forward impact: If a future forensic shows a genuinely foreign Manual NPC entry, a sibling NPC purge can be added; not needed for this finding.
- **Defensive `getattr` guard on `effective_bestiary` at the wiring seam**
  - Rationale: Keeps the 4 pre-existing `ensure_loaded` backfill/combat tests green without forcing every minimal stub to grow an `effective_bestiary` it never exercises. Not a silent fallback in production — the only packs without the method are test doubles.
  - Severity: trivial
  - Forward impact: none — a real pack always purges; if a future malformed real pack lacked `effective_bestiary`, loader validation would already have failed it before `ensure_loaded`.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Fix mechanism is purge-on-load, not seeding-source scoping**
  - Spec source: context-story-158-33.md, "Technical Approach" + AC-1/AC-3 (SM draft)
  - Spec text: "scope MM pre-gen NPC/encounter seeding to the current world's `effective_bestiary` so sibling-world creatures never enter another world's MM"
  - Implementation: Tests target a new `MonsterManual.purge_foreign_bestiary_encounters(bestiary)` wired into `ensure_loaded` (purge-on-load), NOT a change to `pregen.seed_manual`/`encountergen` source selection. Investigation showed live seeding is ALREADY scoped (`encountergen` main + `pregen.seed_manual` both call `pack.effective_bestiary(world)`, which replaces world-over-genre); the bleed is a stale persisted manual from the pre-ADR-120 genre-tier-bestiary era. Scoping the seed would not remove already-persisted foreign encounters.
  - Rationale: The story's invariant (no sibling-world creatures in a world's MM) is preserved; only the failing seam differs. Fixing the seed source alone would leave the existing `heavy_metal_barsoom.json` (and any peer manual seeded in that era) corrupt forever — the reported bug would persist on Keith's machine.
  - Severity: minor
  - Forward impact: Dev implements a model purge method + `ensure_loaded` wiring + a `monster_manual.foreign_purged` OTEL span; the `content` repo branch is likely unused (see Delivery Findings). AC-4 (OTEL) and AC-2 (don't-empty-the-pool) are unchanged and fully covered.
- **Scope narrowed to encounter enemies (not NPCs)**
  - Spec source: context-story-158-33.md, AC-1
  - Spec text: "none of the long_foundry-only creatures … appear in barsoom's Manual `npcs[]`/`encounters[]`"
  - Implementation: The purge (and its tests) target `encounters[]` only. Forensics showed the bled creatures are encounter `enemies`, not `npcs[]` entries (the snapshot `npcs[]` are materialized FROM encounter enemies at injection time, per the gaslighting-doctrine deviation). Manual NPCs are namegen-minted per the world's `effective_cultures` (already world-scoped) or authored/world-owned, so they cannot bleed cross-world the way a stale genre-tier encounter can.
  - Rationale: Purging the encounter source removes the injected creature-NPCs downstream; a separate NPC purge would be dead code against a path that cannot bleed.
  - Severity: minor
  - Forward impact: If a future forensic shows a genuinely foreign Manual NPC entry, a sibling NPC purge can be added; not needed for this finding.

### Dev (implementation)
- **Defensive `getattr` guard on `effective_bestiary` at the wiring seam**
  - Spec source: TEA implementation contract (session), step 2 + the inject suite's `_FakeSessionData` stub doctrine
  - Spec text: "resolve `bestiary, _src = pack.effective_bestiary(sd.world_slug or "")`, call the purge"
  - Implementation: Wrapped the resolve in `effective_bestiary = getattr(pack, "effective_bestiary", None); if callable(effective_bestiary): ...`. A real `GenrePack` always exposes `effective_bestiary`, so production always runs the purge; the guard only no-ops for the inject suite's minimal pack stubs (`_pack_with_authored`, `_pack_with_combat`) that intentionally omit it. This mirrors the existing `getattr(getattr(pack, "rules", None), "ruleset", None)` defensive shape three lines above in the same function.
  - Rationale: Keeps the 4 pre-existing `ensure_loaded` backfill/combat tests green without forcing every minimal stub to grow an `effective_bestiary` it never exercises. Not a silent fallback in production — the only packs without the method are test doubles.
  - Severity: trivial
  - Forward impact: none — a real pack always purges; if a future malformed real pack lacked `effective_bestiary`, loader validation would already have failed it before `ensure_loaded`.

### Reviewer (audit)
- **TEA: "Fix mechanism is purge-on-load, not seeding-source scoping"** → ✓ ACCEPTED by Reviewer: I independently confirmed both `encountergen.main` (`:812`) and `pregen.seed_manual` (`:494`) already call `pack.effective_bestiary(world)`, so live seeding is scoped; the bleed is a persisted-cache artifact. Purge-on-load is the only mechanism that removes already-persisted foreign encounters. Sound — and it preserves the story's invariant.
- **TEA: "Scope narrowed to encounter enemies (not NPCs)"** → ✓ ACCEPTED by Reviewer: forensics confirmed the bled creatures are encounter `enemies` (the snapshot `npcs[]` are materialized from them at injection), and Manual NPCs are namegen-minted per `effective_cultures` (already world-scoped) or authored/world-owned. An NPC-level purge would be dead code. Correct scoping.
- **Dev: "Defensive `getattr` guard on `effective_bestiary`"** → ✓ ACCEPTED by Reviewer (with a non-blocking note): the guard is consistent with the pre-existing sibling guard `getattr(getattr(pack, "rules", None), "ruleset", None)` (`monster_manual_inject.py:145`) and `_SessionData.genre_pack` is typed `GenrePack`, so the skip is not production-reachable. Accepted; I additionally recorded a LOW non-blocking hardening Improvement ([SEC]) to add an `else: logger.warning` should a non-GenrePack pack type ever be introduced.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a (clear, reproducible behavioral invariant)

**Test Files:**
- `sidequest-server/tests/game/test_monster_manual_foreign_purge.py` (NEW) — 10 unit tests for the pure `MonsterManual.purge_foreign_bestiary_encounters(bestiary)` model method.
- `sidequest-server/tests/server/dispatch/test_monster_manual_inject.py` (MODIFIED) — 4 wiring/OTEL tests driving the real `ensure_loaded` seam (2 RED behavioral, 2 over-purge guards).

**Tests Written:** 14 tests (10 model + 4 wiring) covering AC-1..AC-4.
**Status:** RED — verified via `testing-runner` (-n0, serial per the OTEL-deadlock note):
- 10 model tests FAIL `AttributeError: 'MonsterManual' object has no attribute 'purge_foreign_bestiary_encounters'` (method not implemented).
- `test_ensure_loaded_purges_foreign_bestiary_encounter` FAILS `AssertionError: 'foreign' not in {'canon','foreign'}` (purge not wired into `ensure_loaded`).
- `test_ensure_loaded_foreign_purge_emits_span` FAILS `AssertionError: assert 0 == 1` (the `monster_manual.foreign_purged` span does not fire yet).
- 2 over-purge guards (`test_ensure_loaded_keeps_pure_in_world_manual_untouched`, `..._no_foreign_purge_span_when_clean`) PASS now and must stay green after the fix.
- All 44 pre-existing `test_monster_manual_inject.py` tests still PASS; clean collection.

### AC → test map
| AC | Tests |
|----|-------|
| AC-1/AC-3 sibling creature purged | `test_purges_encounter_with_sibling_world_creature`, `test_purges_encounter_when_any_enemy_is_foreign`, `test_mixed_cache_purges_only_the_foreign_encounters`, `test_ensure_loaded_purges_foreign_bestiary_encounter` (wiring) |
| AC-2 don't empty the pool | `test_keeps_encounter_with_in_world_creature`, `test_match_is_case_insensitive`, `test_returns_empty_when_all_in_world`, `test_none_bestiary_purges_nothing`, `test_ignores_native_class_enemies`, `test_does_not_purge_missing_class_name_or_empty_enemies`, `test_ensure_loaded_keeps_pure_in_world_manual_untouched` |
| AC-4 OTEL legibility | `test_ensure_loaded_foreign_purge_emits_span`, `test_ensure_loaded_no_foreign_purge_span_when_clean` |
| AC-5 content world-ownership | Re-scoped to a Delivery Findings Improvement (content already correct — no fix; validator tripwire optional). Content invariants belong in the pack validator, not unit tests. |

### Rule Coverage
| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle (span on every subsystem decision) | `test_ensure_loaded_foreign_purge_emits_span` (fires w/ genre/world/purged), `..._no_foreign_purge_span_when_clean` (no empty spans) | failing (driver) |
| No Silent Fallbacks (never silently empty the pool) | `test_none_bestiary_purges_nothing`, `test_does_not_purge_missing_class_name_or_empty_enemies` | failing (driver) |
| Every Test Suite Needs a Wiring Test | `test_ensure_loaded_purges_foreign_bestiary_encounter` (real `ensure_loaded` invocation + on-disk persistence assert) | failing (driver) |
| SOUL: Crunch in the Genre, Flavor in the World | all cross-world purge tests | failing (driver) |
| python.md #6 Test quality (no vacuous assertions) | self-check: every test asserts specific values (labels/sets/span attrs), no `assert True`/truthy-only | pass |

**Rules checked:** 5 applicable rules have test coverage (the OTEL principle is the load-bearing one — the GM-panel lie-detector for the purge).
**Self-check:** 0 vacuous tests found.

### Implementation contract for Dev (Hephaestus)
1. Add pure method `MonsterManual.purge_foreign_bestiary_encounters(self, bestiary: Bestiary | None) -> list[ManualEncounter]` in `sidequest/game/monster_manual.py` — sibling of `purge_ruleset_incoherent_encounters`. Drop encounters that field a `class="creature"` enemy whose name (case-insensitive) is absent from `bestiary.entries` names. Conservative: `bestiary is None` → return `[]` (never empty the pool); ignore non-`creature`-class enemies (the native-class purge's domain); ignore missing class/name/empty enemies. Pure — caller persists + emits the span.
2. Wire it into `ensure_loaded` (`monster_manual_inject.py`) right after the existing `purge_ruleset_incoherent_encounters` block: resolve `bestiary, _src = pack.effective_bestiary(sd.world_slug or "")`, call the purge, and on a non-empty result `manual.save()` + open a `monster_manual.foreign_purged` span with `{genre, world, ruleset?, purged, remaining_encounters}`. Add the span constant `SPAN_MONSTER_MANUAL_FOREIGN_PURGED = "monster_manual.foreign_purged"` to `sidequest/telemetry/spans/monster_manual.py`.
3. The span name string `"monster_manual.foreign_purged"` and method name are pinned by the tests — keep them (or update both the constant and the tests together, but the span name is the GM-panel contract).
4. No content change required (see Delivery Findings); if you keep the `content` branch, leave it empty or add only the optional validator tripwire.

**Handoff:** To Dev (Hephaestus the Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/game/monster_manual.py` — added pure `MonsterManual.purge_foreign_bestiary_encounters(bestiary)` + module helper `_encounter_has_foreign_creature(enc, allowed_names)` (sibling of `_encounter_has_native_class_enemy`); `TYPE_CHECKING` import of `Bestiary`.
- `sidequest/server/dispatch/monster_manual_inject.py` — wired the foreign purge into `ensure_loaded` immediately after the existing ruleset-incoherent purge: resolve `pack.effective_bestiary(world)`, purge, `manual.save()`, emit `monster_manual.foreign_purged` span.
- `sidequest/telemetry/spans/monster_manual.py` — added `SPAN_MONSTER_MANUAL_FOREIGN_PURGED = "monster_manual.foreign_purged"` + registered in `FLAT_ONLY_SPANS`.
- `tests/server/dispatch/test_monster_manual_inject.py` — ruff-format rewrap only (no test logic change; TEA authored the tests).

**Content repo:** No change (branch is empty — see Delivery Findings).

**Tests:** GREEN — 979/979 passing across the monster-manual / dispatch / pregen / telemetry sweep (testing-runner, `-n0`). All 14 story tests pass; 2 over-purge guards stayed green; zero regressions (telemetry span-count/registry suites all pass). Re-confirmed 64/64 on the two story files after ruff-format.

**Lint/format:** `ruff check` clean on all touched files; `ruff format` applied to touched files only.

**Branch:** `feat/158-33-mm-bestiary-world-scope` (server) — pushed to origin.

**ACs:** AC-1/AC-3 (sibling creature purged), AC-2 (don't empty the pool), AC-4 (OTEL span) all met; AC-5 re-scoped to a non-blocking content-validator Improvement per TEA (content already correct).

**Handoff:** To Reviewer (Hermes Psychopompos) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (492 tests pass, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 1 (LOW), dismissed 2 (with rationale) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed manually below ([SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — assessed manually below ([TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — assessed manually below ([DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed manually below ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 (LOW, non-blocking — rule-aligned, not dismissed) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed manually below ([SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — assessed manually below ([RULE]) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and assessed manually)
**Total findings:** 2 confirmed (both LOW, non-blocking), 2 dismissed (with rationale), 0 deferred

### Rule Compliance (python.md lang-review + SOUL.md/CLAUDE.md)

Exhaustive enumeration over the changed code (new method, helper, wiring, span):

| # python.md rule | Instances checked | Verdict |
|---|---|---|
| #1 silent exception swallowing | 0 new try/except introduced | compliant |
| #2 mutable default arguments | `purge_foreign_bestiary_encounters(self, bestiary)` (no default), `_encounter_has_foreign_creature(enc, allowed_names)` (no default) | compliant |
| #3 type annotations at boundaries | method `-> list[ManualEncounter]` with `bestiary: Bestiary \| None`; helper `(enc: ManualEncounter, allowed_names: set[str]) -> bool` | compliant |
| #4 logging coverage/correctness | `logger.warning` for the purge decision (data-coherence event, matches sibling STALE_PURGED level), `%s` lazy args, no sensitive data | compliant |
| #5 path handling | no new path manipulation (reuses existing `_file_path`) | compliant |
| #6 test quality | 14 tests, every one asserts specific values (labels/sets/span attrs); no `assert True`, no truthy-only | compliant |
| #7 resource leaks | none introduced | compliant |
| #8 unsafe deserialization | reads `enemy.get("class"/"name")` from pydantic-validated, locally-owned cache JSON; only `.lower()` + set membership; no eval/pickle/subprocess | compliant |
| #10 import hygiene | `TYPE_CHECKING` import of `Bestiary` (breaks the cycle, matches `pregen.py`); span import added in alpha order | compliant |
| #11 input validation | defensive `isinstance` guards on every dict access in the helper | compliant |
| SOUL: Crunch in Genre, Flavor in World | the entire purge enforces this (sibling-world creatures removed) | compliant |
| SOUL/CLAUDE: No Silent Fallbacks | `bestiary is None → []` is documented "don't empty the pool" (compliant); the `getattr(effective_bestiary)` silent-skip → see [SEC]/[SILENT] finding (LOW, not production-reachable) | mostly compliant; 1 LOW note |
| CLAUDE: OTEL Observability | `monster_manual.foreign_purged` registered in FLAT_ONLY_SPANS, emitted on every purge decision, no empty spans | compliant |

### Observations (≥5)

- [VERIFIED] `_encounter_has_foreign_creature` handles every enemy-block shape conservatively — evidence: `monster_manual.py:86-99`. Non-dict `data`, non-list `enemies`, non-dict enemy, `class != "creature"`, missing/non-str/empty/whitespace name all fall through to "not foreign". Complies with python.md #11 (input validation) and the sibling helper's conservatism.
- [VERIFIED] Case-folding is symmetric — evidence: `allowed_names = {entry.name.lower() ...}` (`monster_manual.py` purge method) and `name.lower() not in allowed_names` (`monster_manual.py:97`). Both sides lowered; `BestiaryEntry.name` is a validated non-empty str, so `.lower()` is always safe.
- [VERIFIED] `save()` only fires on a real mutation — evidence: `monster_manual_inject.py:185-186` — `foreign = purge(...)`; `if foreign: manual.save()`. The purge only mutates `self.encounters` when `foreign` is non-empty, so there is no mutate-without-persist path. Span/log gated identically (no empty spans).
- [VERIFIED] Self-heal does not re-introduce foreigners — evidence: after the purge, `needs_seeding()` (`monster_manual.py:344`) re-fires only if the pool is empty, and the downstream `seed_manual` re-resolves `effective_bestiary(world)` (world-scoped) — so a re-seed draws only world-true hostiles. The barsoom case purges the two long_foundry encounters; the canon Banth-style encounters (or a fresh world-scoped re-seed) remain.
- [VERIFIED] OTEL parity with the sibling purge — evidence: `monster_manual_inject.py` foreign block mirrors the `STALE_PURGED` block (`genre/world/ruleset/purged/remaining_encounters`), and `telemetry/spans/monster_manual.py:61` registers it in `FLAT_ONLY_SPANS`. Complies with the OTEL Observability Principle.
- [SEC]/[SILENT] [LOW] Silent skip when `pack` lacks `effective_bestiary` — `monster_manual_inject.py:182-183`. `getattr(pack, "effective_bestiary", None)` + `if callable(...)` skips the purge with no log/span if the attribute is absent. CONFIRMED (matches No Silent Fallbacks), but judged LOW + non-blocking: `_SessionData.genre_pack` is typed `GenrePack` (`session_state.py:198`) which always exposes `effective_bestiary`, so the skip is not production-reachable; and the guard is consistent with the pre-existing sibling defensive guard `getattr(getattr(pack, "rules", None), "ruleset", None)` (`monster_manual_inject.py:145`) three lines above, which also silently tolerates absence. Recorded as a non-blocking hardening Improvement (add an `else: logger.warning` only if a non-GenrePack pack type is ever introduced).
- [EDGE] [LOW] Double `manual.save()` when both purges fire in one `ensure_loaded` — `monster_manual_inject.py:149` then `:186`. CONFIRMED but harmless: `save()` is an idempotent JSON file write; final state correct. Non-blocking; optional `needs_save`-flag consolidation.
- [EDGE] [dismissed] `world_slug=None → effective_bestiary("")` returns genre-tier scope (edge-hunter F3). Dismissed: a world-unbound session loads the distinct `{genre}_.json` cache (seeded against that same genre-tier scope), so the purge is a consistent no-op there and can never reach a world-bound manual like `heavy_metal_barsoom.json` (different cache key).
- [EDGE] [dismissed] source="genre" fallback can't flag a sibling creature that's also in the genre pool (edge-hunter F5). Dismissed as correct-by-design: when a world inherits the genre pool (`effective_bestiary` REPLACES world-over-genre — a world with its own `bestiary.yaml` returns source="world"), that pool *is* the world's effective roster, so a creature in it is not foreign. The suggested `source=="world"` gate would *reduce* correctness — it would stop purging a creature genuinely absent from the genre pool.
- [TEST] (subagent disabled — assessed manually) Test quality strong: 14 tests, each asserts specific values; covers foreign/in-world/mixed/case/None-bestiary/native-class/partial-data/pure + wiring + span-fires + no-empty-span + over-purge-guard. No vacuous assertions. Synthetic fixtures only (no real-content pollution). Minor: no explicit test of the double-save or the re-seed-after-purge self-heal, both acceptable scoping choices.
- [DOC] (subagent disabled — assessed manually) Docstrings are excellent — the new method/helper/span each carry a precise, dated rationale tracing the bug to ADR-120 and the sibling-purge distinction. No stale or misleading comments; the inline `ensure_loaded` comment correctly explains the getattr guard.
- [TYPE] (subagent disabled — assessed manually) Types are sound: `Bestiary | None` is the honest signature; `allowed_names: set[str]` is the right structure for O(1) membership; `list[ManualEncounter]` return matches the sibling. No stringly-typed regressions.
- [SIMPLE] (subagent disabled — assessed manually) No over-engineering — the implementation is the minimal sibling of `purge_ruleset_incoherent_encounters`, reusing the same id()-identity removal idiom. No dead code, no speculative abstraction.
- [RULE] (subagent disabled — assessed manually) See the Rule Compliance table above — every applicable python.md rule + SOUL/CLAUDE principle enumerated; all compliant except the one LOW No-Silent-Fallbacks note already captured under [SEC].

### Devil's Advocate

Suppose I want this code to fail. The purge hinges on a name-equality join between the encounter's `enemy["name"]` and `BestiaryEntry.name`. What if the encountergen path does NOT copy `entry.name` verbatim — say it appends a tier suffix ("Banth (tier 2)") or pluralizes ("Banths")? Then a *legitimate* in-world creature would not match `allowed_names` and would be wrongly purged — an over-purge that empties a healthy pool. I checked: `pregen._encounter_factions` and the existing `purge_ruleset_incoherent_encounters` both rely on the same name-verbatim assumption (`generate_enemy_from_bestiary` copies `entry.name` exactly, no suffix), and the docstring states it. So the join key is consistent with the established code — but it is a shared fragility: if a future encountergen change decorates enemy names, BOTH purges silently misfire. That is a pre-existing systemic risk this story inherits, not introduces; worth a note, not a block.

Next: a malicious or corrupt on-disk manual. An attacker who can write `~/.sidequest/manuals/*.json` already owns the server's home dir — out of scope — but a *corrupt* file (truncated, wrong types) is realistic. The helper's `isinstance` guards mean a garbage enemy block is simply treated as "not foreign" (left in place) rather than crashing — graceful. A `Bestiary` with zero entries cannot exist (pydantic validator), so `allowed_names` is never empty when `bestiary is not None`; the only "empty scope" is `None`, which returns `[]`. Good — no accidental mass-purge.

What about a confused operator? If a world legitimately renames a creature in its `bestiary.yaml` between sessions, the old name in a persisted manual encounter becomes "foreign" and is purged on next load — then re-seeded under the new name. That is the *desired* self-heal, not a bug. What if config has unexpected fields? `model_config = {"extra": "forbid"}` on the models means a stray field fails loudly at load — fine.

The one genuine soft spot the devil finds: the `getattr(effective_bestiary)` silent skip (already captured as [SEC]). If some future refactor passes a non-`GenrePack` (e.g., a lazily-bound shim) into `ensure_loaded`, the entire cross-world purge vanishes with no signal — the exact silent regression this story exists to kill. Today it is unreachable (typed `GenrePack`), so LOW; but it is the right thing to harden later. Nothing here rises to Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

**Dispatch tags:** [EDGE] 3 findings (1 LOW confirmed double-save, 2 dismissed correct-by-design) · [SILENT] disabled, assessed manually — the one silent-skip path is the [SEC] LOW below, no swallowed errors elsewhere · [TEST] disabled, assessed manually — 14 meaningful tests, synthetic fixtures, no vacuous asserts · [DOC] disabled, assessed manually — precise dated docstrings, no stale comments · [TYPE] disabled, assessed manually — `Bestiary | None`/`set[str]`/`list[ManualEncounter]` all sound · [SEC] 1 LOW non-blocking (getattr silent-skip, not production-reachable, rule-aligned, recorded as hardening Improvement) · [SIMPLE] disabled, assessed manually — minimal sibling impl, no over-engineering · [RULE] disabled, assessed manually — full python.md + SOUL/CLAUDE enumeration, all compliant bar the one LOW note.

**Data flow traced:** stale `~/.sidequest/manuals/heavy_metal_barsoom.json` → `MonsterManual.load` → `ensure_loaded` → `pack.effective_bestiary("barsoom")` returns barsoom's world bestiary (source="world") → `purge_foreign_bestiary_encounters` builds `allowed_names={banth,...}` → the long_foundry "Knight of the Ashen Banner"/"Foundry Automaton"/"Grave Knight" encounters (class="creature", not in allowed) are removed → `save()` + `monster_manual.foreign_purged` span → the foreign creature never reaches `inject` / the narrator snapshot. Safe — the genre/world-truth break is closed at the cache-load boundary.

**Pattern observed:** clean reuse of the established stale-purge pattern — pure model method returning purged items + caller persists + emits an OTEL span (`monster_manual.py:417` mirrors `:348`; wiring at `monster_manual_inject.py:182` mirrors `:143`). The new helper is a faithful sibling of `_encounter_has_native_class_enemy`.

**Error handling:** defensive `isinstance` guards throughout the helper (corrupt/partial cache data → treated as not-foreign, never crashes); `None` bestiary → `[]` (no empty-pool); pydantic `extra="forbid"` + `BestiaryEntry` validators make malformed input fail loud at load. The only silent path is the typed-unreachable getattr guard (LOW, recorded).

**Verdict rationale:** No Critical or High issues. Two LOW non-blocking findings recorded for optional hardening; two edge findings dismissed with rationale; all project rules compliant. Tests GREEN (979 full sweep / 492 preflight), lint clean, content branch correctly empty.

**Handoff:** To SM (Themis the Just) for finish-story.