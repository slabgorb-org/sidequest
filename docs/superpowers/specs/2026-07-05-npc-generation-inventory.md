# NPC / Creature Generation — Full-System Inventory and Conflict Map

**Date:** 2026-07-05 · **Author:** Architect (survey: 4 parallel read-only crews — server, rulesets, content, doctrine — plus live-cache/log forensics) · **Status:** Survey complete; design decisions pending Keith review
**Prompt:** "Inventory all the ways NPCs can be done — pre-authored, generated on the fly, Monster Manual, bestiary, creatures.yaml — and get them squared away. The beneath_sunden system is fighting against the Fate system; NPC spawning is still a problem."

---

## 1. Executive summary — the reframe

**There is no Fate-vs-WWN fight.** `ruleset` is genre-scoped and session-fixed (`RulesConfig.ruleset`, `genre/models/rules.py:1277`; the `World` model has no ruleset field; one module resolved per session at `server/session.py:99`). Every Fate code path is gated on `pack.rules.ruleset == "fate"` and is unreachable in a caverns_and_claudes session. What *presents* as two rulesets fighting is:

1. **Seven production paths** appending NPCs/creatures into `snapshot.npcs`/`npc_pool` with **no precedence arbiter** (the doctrine layer confirms no ADR establishes one — the closest is epic-157's faction-zone eligibility predicate);
2. A **six-strategy opponent-seating fallback stack** that guesses when sources disagree (patched in 108-2, 150-2, 153-9/10, 158-1/30/34 — each patch evidence of guessing);
3. A **shared mutable Monster Manual cache** (`~/.sidequest/manuals/{genre}_{world}.json`) written by **four clones** (oq-1..oq-4) with divergent content checkouts, currently sitting at **0 NPCs / 0 encounters for beneath_sunden** while `flickering_reach` holds 310 and `glenross` 1,153 (unbounded accumulation at the other extreme);
4. **Name-only, per-seam-divergent dedup** as the sole identity reconciliation between all of the above.

beneath_sunden is the perfect storm: procedural world + SRD-curated 192-entry bestiary + empty MM pool + seam crossings — so its WN rounds routinely fall through the whole stack to **ephemeral stub minting** ("Hold-Dead, HP 10, creature_id=None" vs the narrator's "Molgrath the Eyeless"), the two-names-one-enemy symptom.

---

## 2. Where NPC/creature state lives

| Store | Type | Role |
|---|---|---|
| `snapshot.npcs` | `list[Npc]` (`game/session.py`) | **Primary canonical** — materialized, stateful (HP, disposition, beliefs, last_seen). Everything converges here. |
| `snapshot.npc_pool` | `list[NpcPoolMember]` (`game/npc_pool.py:27`) | Identity-only staging ("known, not yet mechanical"). Promoted → `npcs` on engagement (ADR-138). |
| `snapshot.encounter.actors` | `list[EncounterActor]` | Combat seating; references NPCs **by name**. |
| `snapshot.scenario_state.npc_roles` | dict | Belief-graph roles (ADR-053), not entities. |
| `sd.monster_manual` | `MonsterManual`, off-snapshot | ADR-059 available pool; persisted to `~/.sidequest/manuals/`; injects into `snapshot.npcs` every turn. |
| dungeon `region_population` mutations | `RegionCreature` via Postgres | Frozen procedural roster (ADR-106 Amdt C); injected per-room. |

**Friction:** pool→npcs promotion happens in 3+ places with divergent name matching (exact / casefold / comma-inverted / `invented_from` alias). Disposition defaults are set in 3 different seams. `EncounterActor` references by name only.

---

## 3. The complete creation-path inventory

### 3a. Server paths into `snapshot.npcs` / `npc_pool` (all verified wired)

| # | Path | Trigger | Source | Produces |
|---|---|---|---|---|
| 1 | **MM injection** — `monster_manual_inject.ensure_loaded`+`inject` (`websocket_session_handler.py:835-865`, every turn pre-narrator) with **4 patch builders**: available-humans (L274), encounters (L412→`_creature_patch_from_enemy` L488), room-binding (L623→`_creature_patch_from_bestiary_entry` L540, story 107-2), region-population (L582→L565) | per turn | MM pool (namegen+encountergen pregen + authored backfill), room YAML `encounter_creatures`→bestiary, frozen procedural roster | `NpcPatch`→`Npc` |
| 2 | **Narrator mentions** — `_apply_npc_mentions` (`narration_apply.py:2480`): match npcs → match pool → **mint** `NpcPoolMember(drawn_from="narrator_invented")` (L3173); person names via ADR-091 Markov (`_generate_invented_name` L3103) | post-narration | narrator structured output | pool member |
| 3 | **Prose extraction** — `_auto_mint_prose_only_npcs` (`session_helpers.py:2080`): honorific/role regex over narration, `observation_pending=True`; ratification gate promotes or purges (ADR-138) | post-narration | narration regex | pool member |
| 4 | **Opponent-seater fabrication** — `_seed_combat_hp_depletion_to_npcs` (`encounter_lifecycle.py:317`; promote pool antagonist L395 OR mint `Npc(ephemeral=True)` L428, reaped post-fight) / `_seed_fate_opponents` (L536, Fate packs, FateSheet) | confrontation instantiation | pool promotion or `opponent_default_stats` | `Npc` (possibly ephemeral) |
| 5 | **Session-start cast** — `preload_authored_npcs` (`world_materialization.py:824`) + `WorldBuilder._apply_npc` (L482, history chapters) | chargen/bind | `npcs.yaml` (`authored_npcs`), `history.yaml` | `Npc` |
| 6 | **Zone-cast staging** — `stage_region_cast` (`region_cast_staging.py:48`), observer on region transition | region entry | cartography `entities[]` `binding.kind=="npc"` | pool member (`world_authored`) |
| 7 | **Procedural population** — materializer `_stage_curate` (deterministic since ADR-106 Amdt C) → `_stage_commit` persists `record_mutation(region_id,"region_population",...)` (`materializer.py:1881-1887`) → `load_region_population` → path #1's region builder | dungeon materialization + room entry | cookbook/CR tables + authored room bindings | `RegionCreature`→`Npc` |

Narrator has **no tool** to mint NPCs directly (`generate_encounter` tool is an unwired fatal stub; `apply_world_patch` allowlist is scalar-only). Two narration-minting paths (#2, #3) overlap by design and compete.

### 3b. Doctrine's 12 sanctioned creation modes (survey-doctrine, with sanctioning ADR)

1. World-authored cartography NPCs (ADR-109/140, enter ratified per ADR-138) · 2. Archetype/funnel resolution (ADR-121/016/007 — **dual-use**: chargen AND NPC-gen; `archetype_constraints.yaml` says so explicitly) · 3. Monster Manual pre-gen (ADR-059) · 4. Bestiary-sampled encountergen (ADR-155 + 059 addendum; bestiary is single source of truth) · 5. Procedural megadungeon population (ADR-106) · 6. Namegen culture-corpus (ADR-091; `named_individual` excluded from random spawn; real-Earth worlds use `names_file:` direct sampling) · 7. Opponent-seater (ADR-116/139) · 8. Prose-minted walk-ons + Yes-And ratification (ADR-138/109/014) · 9. Pool→Npc promotion (ADR-138/128 ladder) · 10. Scenario-role seeding (ADR-053 — roles on existing NPCs, creates none) · 11. Companion seat (2026-06-25/27 specs — full mechanical PC) · 12. ~~Guest NPC players~~ (ADR-029 — historical, not building).

### 3c. Content-side sources (survey-content; 11 packs, 22 worlds)

- **World bestiaries:** 24 files (192 entries beneath_sunden → 4 blackthorn_moor), consistent SRD/WN stat shape (`level/hp/armor_class/attack_bonus/damage/morale`). **No Fate-shaped bestiary exists anywhere** — even Fate-genre worlds carry WN-shaped entries. Genre-root bestiaries: only 2 (mutant_wasteland 14, neon_dystopia 15).
- **creatures.yaml:** only 2 remain. beneath_sunden = clean post-158-52 render-only override (`name_is_secret`). **flickering_reach = still a full parallel stat block that diverges from its bestiary** (see §5).
- **npcs.yaml:** 18 files, 149 standard + 38 mystery-suspect entries (`AuthoredNpc`: OCEAN, `initial_disposition`, `location_tags`, `history_seeds`; suspect shape adds truth/secret/cover_story tied to clue graphs). Authoring an NPC **reserves** its canonical name from auto-generation. No `faction` field exists on any NPC.
- **Faction blocks:** `lore.yaml factions:` in 19 worlds — named leaders live in *description prose only* (e.g. coyote_star's Prefect Ilara Vaskov is in no npcs.yaml) — an **unstructured NPC source** the narrator materializes with zero mechanical backing.
- **Encounter tables:** `encounter_tables.yaml` (flickering_reach, seaboard) + per-room `encounter_creatures:` (beneath_sunden entrance + 30 rooms).
- **SRD curation:** `tools/bestiary_curator` (corpus/monsters.yaml + world_register.yaml → gate → CR→level ladder) in 6 WWN worlds; presence of the corpus ≠ SRD-derived (burning_peace/shattered_accord/barsoom are setting-authored).
- **Render contract (post-158-52):** `scripts/generate_creature_images.py` derives from bestiary, creatures.yaml overrides per-field, `name_is_secret` swaps name→role.

---

## 4. Conflict ledger (ranked)

1. **N-source convergence without an arbiter.** Four+ sources feed `snapshot.npcs` for one scene (MM humans, MM encounters, room-binding, region-population, narrator mentions, authored preload); dedup is by-name with authored-wins ordering (`monster_manual_inject.py:802-806`). A bestiary creature, its procedural counterpart, and a narrator invention with slightly different names coexist. Doctrine confirms no precedence ADR exists (contradiction #5 in survey-doctrine).
2. **The six-strategy seating stack** (`instantiate_encounter_from_trigger`, `encounter_lifecycle.py:1492`): roster-resolve (L1114) → zone-reconcile (L1028) → location-fallback (L932) → friendly-fallback (L1250) → frame-default (L1806) → mint-ephemeral-stub (L428, lie-detector span fires). Roster reconciliation **declines under Fate and non-combat**, so those categories skip straight to weaker strategies. Heuristic tiebreaks (most-recent/highest-threat/name) seat ambient mobs over intended antagonists (playtest 150-14).
3. **Shared mutable MM cache, multi-writer.** Genre+world-keyed JSON under `~/.sidequest/manuals/` is read/written by four clones with divergent content. Observed: `total_authored` for beneath_sunden oscillates 0↔4 across 64 loads in 30 days of logs; `purge_foreign_bestiary_encounters` fired **14×** (11 on 2026-06-27 across 5 launches, 3 on 2026-07-02), each purging exactly 2 encounters — a purge/reseed cycle between divergent writers. Two repair purges (ruleset-incoherence from playtest 150-20; foreign-bestiary from 158-33) exist *because* the cache goes stale — they are tourniquets, not a lifecycle.
4. **Pool-size extremes from the same subsystem:** beneath_sunden 0/0 (starved) vs flickering_reach 310 / glenross 1,153 NPCs (unbounded accumulation — no cap or dedup on pregen re-seeding). Also: manuals keyed with **empty world slug** (`caverns_and_claudes_.json`, `heavy_metal_.json` w/ 12 encounters — sessions bound pre-world-resolution) and a stale `victoria_glenross.json` (pre-rename genre).
5. **MM injection vs encounter authority (ADR-139 clash):** injection re-fires every combat turn and historically clobbered damaged HP back up; 139's carve-out ("the encounter is the authority on current HP") is the patch, not a design.
6. **Soft-fallback seed failure:** `ensure_loaded`'s `except Exception` swallows non-`EncounterSeedError` failures as "transient" (`monster_manual.seed_failed`) — can bind a WN world to an empty pool with only a log line. Shape-identical to the 87-4 failure its own comment forbids.
7. **Identity is a name everywhere.** Purge membership = `enemy.name.lower()` vs bestiary names; seater matching, MM dedup, pool promotion, `EncounterActor` refs — all name-string keyed, each with different normalization. The narrator's prose renames ("Molgrath the Eyeless" over creature_id `Thief`) then split identity (`encounter_lifecycle.py:1130` documents the split). `npc_pool[].invented_from` (server #738) is the only provenance breadcrumb.
8. **Content drift, flickering_reach (both findings hard):** (a) `encounter_tables.yaml` references **18/20 phantom creature ids** (authored against an abandoned form-name scheme; only `silo_eye`, `glass_touched_mount` resolve) — ~90% of authored encounters unspawnable; (b) creatures.yaml duplicates all 10 bestiary ids with **divergent stats** (`silo_eye`: L8/hp36/ac16/2d6 vs tier[3,4]/hp30/ac14/1d8+2) — the one world where creatures.yaml still looks like a runtime stat source, in violation of ADR-155. (seaboard_of_saints resolves 100% — clean.)
9. **space_opera bestiary triplication:** aureate_span/coyote_star/perseus_cloud carry **byte-identical** 12-entry "pack bestiary (story 90-1)" files — genre floor stored per-world because no genre-root file exists; zero world-flavored creatures in any of the three. Three different `effective_bestiary` merge behaviors coexist across packs (world-REPLACES / genre-floor+adds / floor-with-precedence).
10. **Unstructured faction leaders** (§3c) — named NPCs with no stat/OCEAN backing, materialized from prose.

---

## 5. beneath_sunden case file (evidence chain)

1. On-disk manual `caverns_and_claudes_beneath_sunden.json`: **0 NPCs / 0 encounters** (nearly unique among live worlds).
2. Logs (30-day retention): `foreign_encounter_purged purged=2` ×14; `stale_encounter_purged purged=2` ×1; `authored_npcs_seeded` 64 loads — `total_authored` oscillates 0 (25×) ↔ 4 (35×), `inserted=4` on 4 loads; **yet disk shows npcs=0 now**; 1 `monster_manual.load_failed` event.
3. Purge logic (`monster_manual.py:417-456`): drops `class=="creature"` enemies whose name is absent from the session's `effective_bestiary(world)`; conservative on `None`. Encountergen stamps `name=entry.name` verbatim (`encountergen.py:356-423` — no personalization; "Molgrath the Eyeless" is the *narrator's* prose name).
4. `effective_bestiary` (`pack.py:540`): world-REPLACES-genre; caverns_and_claudes has **no genre-root bestiary**, so a load where beneath_sunden is absent from `pack.worlds` resolves `(None, "genre")` → purges nothing, seeds nothing meaningful, `total_authored=0`. A load with current content resolves the 192-entry bestiary and purges anything seeded against older rosters.
5. Consequence at runtime: empty MM pool → seater strategies 1-2 find no bound roster → stub minting (the 108-2 two-names-one-enemy report) → "random things happening."

**Root-cause candidates (verification items below):** (a) multi-clone shared cache with divergent content states re-seeding/purging each other; (b) seeding branch not firing on some path (`needs_seeding() and source_dir is not None` — loader sets `source_dir` at `loader.py:2884`, but per-world attribution of the 45 `seed_manual_complete` events needs context tracing since that line carries no world field); (c) the single `load_failed` reset wiping inserted authored NPCs.

---

## 6. Corrections to the written record (completed 2026-07-05)

Tech Writer pass done (docs/meta only, verify-before-write; all edits uncommitted in working tree): (1) architect-gotchas "curate stage is DEAD OUTPUT" corrected — wiring landed; nuance: the named accessors `creatures_for_region`/`big_bad_for_region` still have zero callers, only the direct-dict pipeline is wired; (2) co-location seating gotcha **confirmed FIXED** via 158-1 (`_co_located` region-aware + `_reconcile_surfaced_adversary`); (3) the stale ADR-059 claims lived in the ADR's own "Implementation status (2026-05-02)" prose (DRIFT.md is generated and never listed 059) — corrected in-body; **loadoutgen verified genuinely still a dead 1-line stub**; (4) JARGONFILE +7 terms; (5) new dated learnings appended to architect sidecars. Second pass (done): `docs/feature-inventory.md` CLI table + ADR-087 Dark/Partial roster rows corrected (namegen/encountergen live; loadoutgen reconfirmed dead; pregen-dispatch gap struck from the closing summary). Third pass (done): `docs/adr/087-post-port-subsystem-restoration-plan.md` corrected in-body per its own maintenance pattern (line item + table rows + rollups + a new "Sweep changes through 2026-07-05" log entry) — pregen dispatch row RESTORE/P0 → VERIFIED-partial/P3; encountergen RESTORED (the "empty stub" verdict only ever described `__init__.py`, not the real 836-line `encountergen.py`); namegen confirmed live in-process (and the "22K LOC" figure corrected to 764 lines — a chars-vs-LOC units mix-up); loadoutgen stays RESTORE/P0, reconfirmed dead; P0 rollup renumbered 5→2. Frontmatter untouched (its `implementation-status: live` describes the tracker doc itself), so index regeneration was correctly skipped.

## 7. Open verification items

- **V1:** Attribute the 45 `seed_manual_complete` events per-world (grep with context around each `authored_npcs_seeded`); confirm whether beneath_sunden's encounter seeding ever fires on current code.
- **V2:** Identify which clone/content-state produced the 13 foreign purges (correlate launch timestamps with each clone's content git log for 2026-06-27); confirm the multi-writer hypothesis.
- **V3:** What deleted beneath_sunden's 4 inserted authored NPCs (the `load_failed` reset, or a writer with `total_authored=0`)?
- **V4:** Whether flickering_reach's runtime resolves creatures.yaml stats anywhere (native-path encountergen `_collect_creatures_from_yaml`, `encountergen.py:231`) — if yes, its divergent stat block is live ammunition, not just dead content.
- **V5:** `resolve_encounter_from_trope` (`encounter_lifecycle.py:2331`) claims no callers — confirm and delete or wire.
- **V6:** `generate_name` tool's `ctx.name_generators` population ("Phase E") — no live construction site found.

## 8. Design questions for Keith (the "squared away" part)

- **D1 — One arbiter.** Write the missing precedence ADR: a single **NPC Origin Registry** ordering (authored > room-bound > region-population > MM pool > narrator mint), with every path stamping typed provenance (`origin`, `creature_id`/`authored_id`, `content_version`) instead of converging on bare names. Reuse-first: `invented_from`, `pool_origin`, `manual_origin` already exist as partial provenance — unify, don't add a new system.
- **D2 — Identity by id, not name.** Dedup/purge/seating keyed on `creature_id`/authored id where one exists; prose names become display-layer aliases (the narrator can call it "Molgrath the Eyeless" without forking identity).
- **D3 — MM cache lifecycle.** The shared mutable JSON under `~/.sidequest/manuals/` predates 4-clone development. Options: key by content-version/git-sha (stale = discard, never repair); move per-session into the existing PG substrate (ADR-115); or per-clone cache dirs. The two purge functions become unnecessary the moment staleness is impossible.
- **D4 — Cap + dedup pregen accumulation** (310/1,153-NPC pools) and fail loud on empty-world-slug manual keys.
- **D5 — Content fixes (file as stories):** flickering_reach encounter-table reconciliation (18 phantoms) + creatures.yaml stat-block demotion to ADR-155 render-only; space_opera genre-root bestiary de-triplication; decide whether faction leaders get structured `npcs.yaml` entries or stay prose-only by design.
- **D6 — Seating stack diet.** With D1-D3 in place, strategies 2/5/6 (zone-reconcile, frame-default, stub-mint) should become assertion failures on non-degenerate paths, not fallbacks — per No Silent Fallbacks.
