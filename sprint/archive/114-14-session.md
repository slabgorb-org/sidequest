---
story_id: "114-14"
jira_key: ""
epic: null
workflow: "tdd"
---
# Story 114-14: Relocate mutant_wasteland genre-tier bespoke to world tier; enforce ADR-145 D3 genre-baseline-verbatim

## Story Details
- **ID:** 114-14
- **Jira Key:** (none)
- **Workflow:** tdd
- **Repos:** content, server
- **Stack Parent:** 114-8

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T11:09:45Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T09:46:51Z | 2026-06-15T09:50:23Z | 3m 32s |
| red | 2026-06-15T09:50:23Z | 2026-06-15T10:31:53Z | 41m 30s |
| green | 2026-06-15T10:31:53Z | 2026-06-15T11:01:16Z | 29m 23s |
| review | 2026-06-15T11:01:16Z | 2026-06-15T11:09:45Z | 8m 29s |
| finish | 2026-06-15T11:09:45Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[SM · Gap · blocking]** sm-setup emitted a hollow story-context template (no
  problem/approach/ACs). I enriched `sprint/context/context-story-114-14.md` from
  the Architect's measured design spec. **TEA: read `sprint/planning/114-14-design.md`
  FIRST**, then the enriched story context — both carry the verified ground truth,
  the decision, the validator design, and the RED test plan.
- **[SM · Improvement · non-blocking]** D3 validator = **EXTEND** the existing 114-3
  provenance validator (it already enforces genre-tier provenance *presence*; add a
  `mode ∈ {verbatim, derived}` branch — never `bespoke`), do NOT build a new
  validator. "Wire Up What Exists." Seam: `sidequest/genre/loader.py` (~:1623) /
  `models/pack.py`; `ItemProvenance` at `models/inventory.py:152`.
- **[SM · Question · non-blocking]** Decision (B) (AWN-source the 6 survival/tool
  items at the genre tier) assumes AWN has analogs for canteen/rad-meds/medkit/
  light/toolkit/rad-detector. Dev/TEA: verify each against the AWN SRD equipment
  chapter. An item with **truly no AWN analog** moves to BOTH worlds (not genre).
  Confirm-with-Keith only if a survival item has no analog AND moving it to both
  worlds feels wrong.
- **[SM · Gap · non-blocking]** Measured: `seaboard_of_saints/inventory.yaml` has
  ZERO provenance stamps across its ENTIRE catalog (not just the 5 artifacts).
  Scope = stamp the 5 chargen artifacts + add `ancient_artifact`. World-tier
  provenance is *optional during migration* (ADR-145 D3), so stamping seaboard's own
  whaling gear is OUT of scope unless the new validator's scope reaches the world
  tier (it should NOT — world-tier bespoke is legal).
- **[SM · Improvement · non-blocking]** Stale-tree caution: this is oq-2; the
  content and server trees lag `develop` independently. Verify both are current
  before treating any "still bespoke / still broken" as a finding (per the
  pull-don't-just-restart rule).

### TEA (test design)
- **[Conflict · resolved by Keith]** SCOPE GREW then NARROWED. Measuring the real
  tree (not the `mode: bespoke` grep) showed the defect is "not `mode: verbatim`"
  → **79 non-verbatim genre items across 4 SRD-bound packs**, not 23 across 3:
  mutant_wasteland 12 (bespoke), neon_dystopia 6 (bespoke), road_warrior 30 (5
  bespoke + **25 UNPROVENANCED**), caverns_and_claudes 31 (UNPROVENANCED).
  elemental_harmony + heavy_metal are already 100% verbatim (target). Keith ruled
  **"narrow this story, file the rest as epic"** → 114-14 = validator + the **23
  declared-bespoke** items (3 packs); the 56 unprovenanced → **epic 119** (filed).
- **[Improvement · CORRECTS the SM finding]** The validator is **net-new**, not an
  extension of 114-3. ADR-145 says 114-3 enforces genre-tier provenance *presence*,
  but it does NOT — pulp_noir loads with 0 provenance; the swn fixture has none.
  Presence is a test-level contract only. So the D3 check is a new loader validator.
- **[Improvement · non-blocking]** The validator rule is **"no genre-tier
  `mode: bespoke`"**, NOT "verbatim-only" — and it is **gated to the WN family**
  (`awn/cwn/wwn/swn`). NATIVE packs are EXEMPT (authored content, no SRD; protects
  homebrew/Jade authoring). The narrow rule lets caverns (31) + road_warrior (25)
  unprovenanced items keep loading → no breakage; epic 119 upgrades to verbatim-only.
- **[Gap · blocking-for-Dev]** ⚠ **world-replaces-genre kit trap.**
  `resolve_inventory` takes `starting_equipment`/`starting_gold`/`currency` from a
  world's inventory.yaml WHOLESALE. The instant Dev creates
  `worlds/flickering_reach|franchise_nations|the_circuit/inventory.yaml`, that world
  STOPS inheriting genre kits → empty loadouts unless the new file copies the genre
  kits/gold/currency. seaboard already ships its own (safe). Tests
  `test_world_starting_equipment_resolves` (both new server files) catch this.
- **[Improvement · non-blocking]** Fixture landmine for Dev/Reviewer: the
  `spaghetti_western`/`low_fantasy`/`test_genre` fixtures all carry lethality
  `genre_key: test_genre`, so they only load from a dir named `test_genre`
  (`lethality_policy_loader.py:47`). The native-exempt test copies `test_genre`
  (ruleset defaults to native) to `tmp/test_genre` for this reason.

### Dev (implementation)
- **[Improvement · non-blocking]** mutant_wasteland: only **4 of 6** survival items
  had clean AWN analogs — Water jug (2/1), First aid kit (25/1), Flashlight (10/1),
  Toolkit (50/3) — sourced verbatim at the genre tier. `rad_pills` + `geiger_clicker`
  have NO AWN equipment entry (AWN handles radiation via saves; "Therapeutic" is a
  Major-Injury drug, not anti-rad; there is no Geiger/dosimeter in the gear tables —
  verified against `/tmp/awn_full.txt` Survival Gear p.85 + Modern Drugs p.87), so
  they moved to `worlds/flickering_reach` as bespoke alongside the relics.
- **[Gap · non-blocking → epic 119]** road_warrior genre still carries 25
  UNPROVENANCED items (rig parts, mount weapons, survival, rig-tier vessels);
  caverns_and_claudes 31. The narrow validator passes them (not `mode: bespoke`).
  Epic 119 verbatim-only sweep.
- **[Conflict · resolved]** `test_road_warrior_combat_dispatch.py` asserted the
  personal-weapon invariant against the GENRE tier (`pack.inventory`). The weapons
  moved to the world tier (D3), so I updated 2 tests to resolve against
  `the_circuit` (the live play tier). Same invariant, correct tier — not a
  weakening (the resolved catalog is what a player actually sees).
- **[Improvement · non-blocking]** Fixed 2 stale "world inventory REPLACES genre
  wholesale" comments in `seaboard_of_saints/inventory.yaml` (the 114-8 Reviewer
  flagged one) — `item_catalog` is a non-droppable MERGE since 114-11; only
  starting_equipment/gold/currency are world-replaces.
- **[Improvement · non-blocking]** Full server suite: **30 pre-existing failures
  remain** (caverns/elemental chargen + e2e + websocket + narrator-SDK + snapshot
  governance) — NONE touch mutant/neon/road or inventory. caverns/elemental/
  heavy_metal/space_opera all load clean under the new validator; the caverns
  chargen failures root in "Warrior not in choices: [None×6]" (chargen-scene/
  namegen, unrelated). Matches the known ~90 oq-2-tree pre-existing failures.

### Reviewer (code review)
- **[Improvement · non-blocking → future story]** `chargen_loadout._item_dict_minimal`
  (chargen_loadout.py:110) silently mints a `category: equipment` stub when a
  starting_equipment kit id isn't in the resolved catalog — there is no PER-ITEM
  OTEL span (only the class-level `chargen.starting_equipment_missing` fires when a
  class has NO kit). Pre-existing; the genre-kit route into it is now closed by the
  reviewer fix (genre kits reference only genre-catalog ids), but the stub path is
  still observability-blind. A future story should emit a span naming pack/world/
  class/item_id. Affects `sidequest-server/sidequest/server/dispatch/chargen_loadout.py`.
- **[Gap · non-blocking → epic 119]** Reaffirmed: caverns_and_claudes (31) +
  road_warrior (25) UNPROVENANCED genre items remain (not bespoke → validator passes);
  the verbatim-only sweep + validator upgrade is epic 119 (filed).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Story scope expanded 5pt→13pt and from 1 pack to 3 packs + a global validator**
  - Spec source: context-story-114-14.md (original Scope: mutant_wasteland only) +
    Keith's two rulings 2026-06-15.
  - Spec text: original story title/context scoped to "relocate mutant_wasteland
    genre-tier bespoke items to the WORLD tier."
  - Implementation: tests + plan now cover the **D3 loader validator** (WN-family,
    fail-loud on genre-tier `mode: bespoke`) AND **neon_dystopia + road_warrior**
    (their declared-bespoke items move to their single worlds), not just
    mutant_wasteland. The unprovenanced verbatim-only sweep (caverns + road_warrior
    25) is split out to **epic 119**.
  - Rationale: the validator runs for every pack at load; shipping it while
    neon_dystopia (6) and road_warrior (5) still carried genre-tier bespoke would
    fail their load (conflict with "full suite green"). Keith ruled validator + all
    declared-bespoke packs now ("no split brain, No Silent Fallbacks"), rest as epic.
  - Severity: major (scope + points change)
  - Forward impact: epic 119 carries the verbatim-only upgrade (validator → reject
    unprovenanced genre items) + caverns/road_warrior provenance sweep.
- **Validator rejects only `mode: bespoke`, not all non-verbatim (deferred to 119)**
  - Spec source: ADR-145 D3 ("genre baseline = verbatim-only") + Keith "narrow".
  - Spec text: ADR-145 D3 says the genre baseline is SRD-verbatim only.
  - Implementation: this story's validator rejects genre-tier `mode == "bespoke"`
    for WN-family packs; it does NOT reject unprovenanced (no-provenance) genre items.
  - Rationale: enforcing full verbatim-only now breaks caverns_and_claudes (31) +
    road_warrior (25), which Keith deferred to epic 119. The narrow rule is the
    bounded, self-consistent step (every WN pack ends with 0 declared-bespoke).
  - Severity: minor (a deliberately bounded enforcement; documented + epic-tracked)
  - Forward impact: epic 119 upgrades the rule to verbatim-only and migrates the
    unprovenanced items.

### Dev (implementation)
- **mutant_wasteland rad_pills + geiger_clicker moved to the world tier (not AWN-sourced at genre)**
  - Spec source: `sprint/planning/114-14-design.md` (mutant_wasteland decision) + AC8.
  - Spec text: "AWN-source the 6 survival/tool items verbatim AT the genre tier … Only if an item truly has no AWN analog does it move to the world tier."
  - Implementation: 4 of 6 survival items AWN-sourced at genre; `rad_pills` and `geiger_clicker` moved to `worlds/flickering_reach/inventory.yaml` as bespoke.
  - Rationale: the AWN SRD has no anti-radiation drug and no radiation-detector equipment entry (verified against the SRD extract). Forcing a verbatim bind onto an unrelated AWN item would be a false provenance claim — worse than an honest world-tier bespoke. AC8's test explicitly permits a genre-absent survival item.
  - Severity: minor
  - Forward impact: none — flickering_reach (which copies the genre kits, incl. Pureblood→rad_pills) carries both; seaboard uses its own Saints gear and references neither.
- **road_warrior personal weapons moved to the world tier (not re-sourced from CWN)**
  - Spec source: `sprint/planning/114-14-design.md` (road_warrior) + Keith "narrow".
  - Spec text: "These were deliberately authored bespoke ('iconic improvised' weapons) — MOVE them, don't re-source (preserve identity)."
  - Implementation: the 5 declared-bespoke personal weapons moved verbatim to `worlds/the_circuit/inventory.yaml`; CWN baseline weapons stay at genre.
  - Rationale: they were intentionally marked bespoke; re-sourcing would change their identity. Single-world pack → no duplication.
  - Severity: minor
  - Forward impact: epic 119 may revisit whether the genre's CWN baseline duplicates any of them.

### Reviewer (audit)
- **TEA "scope expanded 5pt→13pt, 3 packs + validator"** → ✓ ACCEPTED: sound and
  Keith-ruled. Filing epic 119 for the deferred verbatim-only sweep is the correct
  split; the narrow validator (reject `mode: bespoke`, WN-gated) does not break the
  unprovenanced packs. Verified all 6 WN packs load clean.
- **TEA "validator rejects only mode:bespoke, not all non-verbatim"** → ✓ ACCEPTED:
  the bounded enforcement is self-consistent (every WN pack ends with 0 declared
  bespoke) and avoids breaking caverns/road_warrior; epic 119 tracks the upgrade.
- **Dev "rad_pills + geiger_clicker moved to world (no AWN analog)"** → ✓ ACCEPTED:
  verified against the AWN SRD extract — no anti-rad drug and no radiation-detector
  equipment entry exist; an honest world-tier bespoke beats a false verbatim claim.
  AC8's test permits genre-absent survival items. (Reviewer note: also drove the
  reviewer fix removing the now-dangling rad_pills ref from the genre Pureblood kit.)
- **Dev "road_warrior personal weapons moved, not re-sourced"** → ✓ ACCEPTED:
  they were deliberately authored bespoke ("iconic improvised"); single-world pack →
  no duplication. Preserving identity over a forced CWN bind is correct.
- No undocumented deviations found.

## Sm Assessment

**Setup complete — ready for RED.**

- **Workflow:** tdd (phased). **Repos:** content, server (orchestrator carries only
  sprint/planning/context artifacts — no orchestrator code).
- **Branches created** (off `develop`, github-flow per repos.yaml):
  - sidequest-content: `feature/114-14-mutant-wasteland-bespoke-to-world-d3`
  - sidequest-server: `feature/114-14-mutant-wasteland-bespoke-to-world-d3`
- **Context:** sm-setup's template was hollow; enriched
  `sprint/context/context-story-114-14.md` from the Architect's measured spec
  (`sprint/planning/114-14-design.md`). Both are TEA's required reads.
- **Design authority:** The Man in Black (Architect) verified every load-bearing
  claim against the real tree before this story was filed (12 genre-tier bespoke
  items confirmed; flickering_reach has no inventory.yaml; seaboard unstamped;
  resolver + ItemProvenance seams located; D3 enforcement = extend the 114-3
  validator). No open architectural question — Keith ruled the placement 2026-06-15.
- **Jira:** disabled (personal project) — skipped by design.
- **Merge gate:** clear at setup (no open PRs in content or server).
- **Routing:** next phase `red`, owner **TEA (Fezzik)**.

**Handoff:** To TEA (Fezzik) for the RED phase. Write the failing tests per the 7
ACs — headline: no genre-tier item is `mode: bespoke`; per-world relic resolution;
chargen-artifact category resolution; starting_equipment resolution; the new D3
validator (synthetic bespoke-genre pack fails loud, world-tier bespoke does not).
Run against the real pack with `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL`
set; record the pre-existing baseline-fail list before claiming RED.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED confirmed — **5 fail / 15 pass (guards)**, 0 error (run with
`SIDEQUEST_DATABASE_URL` set; `find_pack_path` resolves real packs without
`SIDEQUEST_GENRE_PACKS`).

**Test Files (4):**
- `tests/server/test_114_14_genre_baseline_no_bespoke_validator.py` — the D3 loader
  validator, via real `load_genre_pack` on tmp-copied fixtures: WN-family genre-tier
  bespoke RAISES (names the id) [RED]; genre verbatim OK, world-tier bespoke OK,
  native-pack genre bespoke OK (WN-gated) [guards].
- `tests/genre/test_114_14_srd_packs_genre_baseline_no_bespoke.py` — real packs: no
  genre-tier `mode: bespoke` in mutant_wasteland/neon_dystopia/road_warrior [RED ×3];
  elemental_harmony/heavy_metal stay clean [guards]; mutant_wasteland survival gear
  kept at genre is AWN-verbatim [RED].
- `tests/server/test_114_14_mutant_wasteland_relic_world_resolution.py` — relics
  resolve in both worlds; chargen item_hint artifacts upgrade to catalog category
  (datapad→tool, power_glove→weapon) via real `apply_starting_loadout`;
  starting_equipment resolves per world (world-replaces trap) [guards].
- `tests/server/test_114_14_neon_road_world_migration.py` — neon/road moved-bespoke
  ids resolve for their single world; starting_equipment resolves (world-replaces
  trap) [guards].

**RED drivers (must go green when Dev implements):**
1. WN-family genre-tier bespoke raises at load (validator does not exist today).
2/3/4. mutant_wasteland(12)/neon_dystopia(6)/road_warrior(5) carry genre-tier bespoke.
5. mutant_wasteland survival gear is bespoke (must become AWN-verbatim or move).

**Guards (green today, lock the migration):** verbatim-allowed, world-tier-bespoke-
allowed, native-exempt, already-clean WWN packs, and all relic/artifact/kit
resolution incl. the world-replaces-genre `starting_equipment` trap.

### Rule Coverage

| Rule (SOUL/claude.md/lang-review) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (validator fails loud, names id; no allow-list) | `test_wn_family_genre_tier_bespoke_is_rejected` | failing (RED) |
| Verify Wiring, Not Just Existence (real `resolve_inventory`/`apply_starting_loadout`) | relic/artifact/kit resolution tests | passing (guards) |
| Every Test Suite Needs a Wiring Test | validator via real `load_genre_pack`; chargen via real seam | failing/passing |
| No Source-Text Wiring Tests | all behavior/load-driven; zero `read_text()` source asserts | compliant |
| Crunch in the Genre / homebrew authoring protected (native exempt) | `test_native_pack_genre_tier_bespoke_is_exempt` | passing (guard) |
| Tests must not point at live content (anti-pattern) | N/A — these ARE content-compliance tests (the legit case); validator uses fixtures | compliant |
| lang-review #8 unsafe deser | `yaml.safe_load` only | compliant |

**Rules checked:** 7 of 7 applicable. **Self-check (vacuous):** none — every test
asserts specific ids/categories/membership; `pytest.raises` asserts the id is named.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Read `sprint/planning/114-14-design.md`
(the implementation map) + the TEA Delivery Findings — especially the ⚠
**world-replaces-genre kit trap** (any new world inventory.yaml MUST copy genre
`starting_equipment`/`starting_gold`/`currency`) and the **narrow validator rule**
(WN-family, reject `mode: bespoke` only; native exempt; verbatim-only deferred to
epic 119). Re-run the 4 files with `SIDEQUEST_DATABASE_URL` set; then the FULL suite
(`SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL`) for the regression baseline.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/genre/loader.py` — new `_validate_genre_baseline_no_bespoke(ruleset, inventory)` (reuses `_is_without_number`, raises `PackError` naming offending ids; native packs exempt), called from `load_genre_pack` in the validator cluster.
- `sidequest-server/tests/server/test_road_warrior_combat_dispatch.py` — 2 tests now assert the personal-weapon invariant against the resolved `the_circuit` catalog (the weapons moved to the world tier).
- `sidequest-content/genre_packs/mutant_wasteland/inventory.yaml` — genre now 9 items, 100% AWN-verbatim (4 survival AWN-sourced; 6 relics + rad_pills + geiger removed).
- `sidequest-content/genre_packs/mutant_wasteland/worlds/flickering_reach/inventory.yaml` — NEW: 8 bespoke + copied genre kits/gold/currency.
- `sidequest-content/genre_packs/mutant_wasteland/worlds/seaboard_of_saints/inventory.yaml` — 5 artifacts stamped bespoke + `ancient_artifact` added; stale comments fixed.
- `sidequest-content/genre_packs/neon_dystopia/inventory.yaml` — 6 bespoke removed (pointer comment).
- `sidequest-content/genre_packs/neon_dystopia/worlds/franchise_nations/inventory.yaml` — NEW: 6 bespoke + copied kits/gold/currency.
- `sidequest-content/genre_packs/road_warrior/inventory.yaml` — 5 declared-bespoke removed (pointer comment).
- `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/inventory.yaml` — NEW: 5 bespoke + copied kits/gold/currency.

**AC accountability:**
| AC | Status | Evidence |
|----|--------|----------|
| 1 validator exists + fails loud (names id) | DONE | `test_wn_family_genre_tier_bespoke_is_rejected` green |
| 2 world-tier bespoke legal | DONE | `test_wn_family_world_tier_bespoke_is_allowed` green |
| 3 native packs exempt | DONE | `test_native_pack_genre_tier_bespoke_is_exempt` green |
| 4 no genre-tier bespoke (3 packs) | DONE | `test_fixed_pack_has_no_genre_tier_bespoke[*]` green |
| 5 mutant relics resolve per world | DONE | `test_all_relics_resolve_for_world[*]` green |
| 6 chargen artifacts upgrade category | DONE | `test_chargen_artifacts_upgrade_to_catalog_category[*]` green |
| 7 starting_equipment resolves per world (trap) | DONE | `test_world_starting_equipment_resolves[*]` (mutant + neon/road) green |
| 8 survival AWN-sourced (or moved if no analog) | DONE | `test_mutant_wasteland_survival_gear_is_awn_verbatim_at_genre` green (4 sourced; rad_pills/geiger moved — deviation logged) |
| 9 full regression green | DONE | 11402 passed; 30 failures all pre-existing & unrelated (caverns/elemental chargen, websocket, narrator-SDK, snapshot) — verified caverns/elemental/heavy_metal/space_opera load clean |

**Tests:** 20/20 new 114-14 tests green; 2 road_warrior tests fixed for the tier
move. Blast-radius regression (470 targeted) clean. Full suite: 11402 passed,
30 pre-existing failures (none in mutant/neon/road or inventory). ruff check +
format clean.

**Handoff:** To verify (TEA simplify + quality-pass), then Reviewer (Westley). Note
the two logged deviations (rad_pills/geiger moved for lack of an AWN analog;
road_warrior weapons moved not re-sourced) and the 25/31 unprovenanced items
deferred to **epic 119**.

## Subagent Results

Enabled subagents (per `workflow.reviewer_subagents`): preflight,
silent_failure_hunter, security. The other six are disabled via settings —
self-assessed below (Reviewer Assessment domain tags).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 0 (smells) | tests GREEN 25/0; ruff check+format clean; all 6 WN packs load clean; 3 env-gated skips (ok) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (2 low, 2 med) | confirmed+FIXED 1 (genre Pureblood kit rad_pills); noted 2 low (correct/intentional); deferred 1 (pre-existing chargen stub OTEL gap) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed [TYPE]) |
| 7 | reviewer-security | Yes | clean | 0 | N/A — D4/D4a/D4b all compliant (44 instances), no unsafe deser/secrets |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (self-assessed [RULE]) |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled per settings)
**Total findings:** 1 confirmed-and-fixed (genre Pureblood kit), 2 low noted
(correct/intentional), 1 deferred (pre-existing observability gap)

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. The one actionable finding (a [SILENT] medium: the
genre `starting_equipment.Pureblood` kit referenced `rad_pills`, a world-tier id
absent from the genre catalog — a latent `_item_dict_minimal` stub trap for a
future world) was **fixed in-review** (content commit on the feature branch): the
genre Pureblood kit now references only genre-catalog ids; flickering_reach retains
rad_pills in its own world kit. 22/22 114-14 tests re-verified green after the fix.

**Data flow traced:** `load_genre_pack(path)` parses `inventory.yaml` →
`InventoryConfig` (pydantic, `extra=forbid`) → `_validate_genre_baseline_no_bespoke(
rules.ruleset, inventory)` → for a WN-family ruleset, raises `PackError` naming any
genre-tier `provenance.mode=="bespoke"` id; native packs early-return. At play time,
`resolve_inventory(pack, world)` unions the genre baseline with the world catalog
(non-droppable) and takes kits/gold/currency from the world wholesale — so the
relocated bespoke items resolve for each world. Verified end-to-end by the new tests.

**Observations (tagged by domain):**
1. `[SILENT] [CONFIRMED→FIXED]` genre mutant_wasteland Pureblood kit referenced
   world-tier `rad_pills` → fixed in-review (genre kits reference genre-catalog ids
   only). The other 3 silent-failure findings: loader `inventory is None` early
   return is correct (not a silent failure); the `provenance is None` pass-through is
   the intentional epic-119 deferral (documented); the `_item_dict_minimal` per-item
   observability gap is pre-existing and logged as a Delivery Finding.
2. `[SEC] [VERIFIED]` ADR-145 D4/D4a/D4b clean — security subagent checked 44
   instances, 0 violations: the only Sine Nomine mention in changed files is the
   anti-endorsement disclaimer (`mutant_wasteland/inventory.yaml`); all 4 AWN-sourced
   survival items carry `verbatim/awn/wn-free` + an `AWN SRD …` srd_ref; all moved
   bespoke items carry no false srd/license. `yaml.safe_load` only; no secrets.
3. `[VERIFIED]` validator correctness — `loader.py:723`: WN-gated via the existing
   `_is_without_number`, fails loud naming sorted offender ids (No Silent Fallbacks,
   no allow-list — honors Keith's ruling). Native packs exempt (protects homebrew
   authoring). Confirmed 0 genre-tier bespoke across all 3 fixed packs; caverns/
   elemental/heavy_metal/space_opera load clean.
4. `[VERIFIED]` world-replaces-genre trap handled — all 3 new world inventories
   (flickering_reach/franchise_nations/the_circuit) carry currency + starting_equipment
   + starting_gold; `test_world_starting_equipment_resolves[*]` green.
5. `[TEST] [VERIFIED]` (self-assessed, analyzer disabled) — tests drive real seams
   (`load_genre_pack`, `resolve_inventory`, `apply_starting_loadout`); no source-grep
   wiring tests; `pytest.raises` asserts the offending id is named (not vacuous);
   parametrized cases cover distinct packs/worlds. The road_warrior tests were
   correctly re-pointed to the world tier (same invariant, correct tier).
6. `[SIMPLE] [VERIFIED]` (self-assessed) — the validator reuses `_is_without_number`
   and `PackError` rather than adding new machinery; content edits are data-only with
   pointer comments. No over-engineering. Stale "REPLACES wholesale" comments removed.
7. `[DOC] [VERIFIED]` (self-assessed) — new comments are accurate; the seaboard stale
   comments (flagged by the 114-8 reviewer) are fixed; world headers document the
   world-replaces trap and the bespoke-is-world-tier rationale.
8. `[TYPE] [VERIFIED]` (self-assessed) — no new types; the validator's typed
   `InventoryConfig | None` signature is sound; content validated by the strict
   `CatalogItem`/`ItemProvenance` pydantic models (verbatim⇒wn-free enforced).
9. `[EDGE] [VERIFIED]` (self-assessed) — validator edges covered: inventory None
   (early return), native ruleset (early return), empty catalog (no offenders),
   verbatim/derived (allowed), world-tier bespoke (allowed), genre bespoke (raises).
10. `[RULE] [VERIFIED]` (self-assessed, rule_checker disabled) — Python lang-review:
    no bare except, no mutable defaults, annotated boundary, `yaml.safe_load` only,
    no resource leaks, no star imports; test quality clean (no `assert True`/vacuous).

### Devil's Advocate
Argue this is broken. **Licensing landmine:** reproducing third-party stats is the
single most damaging possible defect (ADR-145 D4a). I hunted every new comment,
srd_ref, and header — the only Sine Nomine string in the diff is the disclaimer that
*negates* endorsement, and every verbatim item cites the SRD, never a commercial
book. Clean, but the perennial rot risk is a future author copying a world file and
weakening the disclaimer. **Silent kit breakage:** the strongest real concern — a
genre kit referencing a world-tier id (`rad_pills`) that falls through to a
category=equipment stub. That was live in the first GREEN cut; the reviewer fix
closes the genre-kit route, and the remaining `_item_dict_minimal` blindness is
pre-existing and logged. **Duplication creep:** rad_pills/geiger now live only in
flickering_reach, the relics in both mutant worlds, neon/road bespoke in their single
worlds — minimal, justified duplication (genuinely bespoke, no SRD analog), and the
universal survival gear is AWN-sourced once at genre (the anti-duplication win).
**Validator over-reach:** could it wrongly reject a legitimate pack? It is WN-gated
and bespoke-only — native packs and verbatim/derived items pass; verified all live
WN packs load. **The genuine soft spot:** caverns (31) + road_warrior (25) still
carry unprovenanced genre items — not bespoke, so the validator passes them, but they
violate the *spirit* of D3. That is the explicit, Keith-ruled epic-119 deferral, not
a hidden gap. None rises to Critical/High; the licensing check (the one that could
truly hurt) is clean.

**Verdict:** APPROVED — the validator faithfully enforces ADR-145 D3 (fail-loud,
WN-gated, native-exempt, no allow-list), all 3 packs' genre baselines are bespoke-
free, the bespoke items resolve correctly per world with kits intact, licensing
guardrails hold, and the one latent kit trap was fixed in-review. The unprovenanced
sweep is correctly deferred to epic 119.

**Handoff:** To SM (Vizzini) for finish-story.