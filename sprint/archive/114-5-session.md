---
story_id: "114-5"
jira_key: "null"
epic: "114"
workflow: "tdd"
---
# Story 114-5: CWN extraction + neon_dystopia and road_warrior personal gear; cyberware system_strain as a typed field

## Story Details
- **ID:** 114-5
- **Jira Key:** (none — no Jira integration)
- **Workflow:** tdd
- **Epic:** 114 — SRD-sourced inventory
- **Stack Parent:** 114-3 (done) — the extraction-tool substrate this builds on
- **Points:** 5
- **Priority:** p2

## Epic Context

**Epic-114 thesis:** *bind the equipment catalog, don't author it.* If a genre binds a Without Number ruleset, its gear should BE that ruleset's gear — extracted from the SRD's equipment chapter, not hand-authored with a ruleset-shaped envelope bolted on. This is the inventory analogue of the ADR-143/144 doctrine *Bind the Ruleset, Don't Balance It.*

**Completed upstream:** 114-3 built the WWN CC0 equipment extraction tool (SRD chapter → canonical baseline catalog); 114-4 produced the WWN baseline catalog and wired caverns_and_claudes, elemental_harmony, heavy_metal to it (de-duplicated barsoom/long_foundry).

**This story (114-5) must do the SAME for CWN:**
1. Build/extend a CWN equipment extractor (parallel to the 114-3 WWN tool)
2. Produce a CWN baseline catalog
3. Wire neon_dystopia and road_warrior personal gear to it
4. **Standalone mechanical change:** make cyberware system_strain a **typed field** (not free-form/ad-hoc)

**Licensing note:** WWN is CC0 (verbatim-reproducible); CWN is likely CC0 but the license must be **verified** before bulk-importing. The technical approach should flag that the dev must verify CWN's license before proceeding with reproduction.

## Sm Assessment

**Story ready for RED.** This is the CWN twin of the already-shipped WWN extraction (114-3/114-4) — the pattern, the CatalogItem provenance model, and the genre-baseline/world-override placement are all established and live, so TEA and Dev have a concrete reference implementation to mirror rather than a greenfield design. Dependency 114-3 is `done`; merge gate clear (0 in-review, 0 in-progress).

**Two things TEA must pin down in RED, both flagged in the technical notes:**
1. **Licensing gate.** CWN is "likely CC0 — VERIFY." The extraction tool must refuse verbatim emission under an unverified license (fail loud, per the No-Silent-Fallbacks principle and the 114-3 tool's existing invariant). RED should assert that refusal.
2. **`system_strain` typing.** Whether it extends `DamageSpec` or warrants a dedicated `CyberwareSpec` is a type-design call for TEA/Dev — the requirement is that it become a *typed, validated* field, not free-form. Watch for CWN rows where the value is a die expression vs. a flat int.

**Wiring is the load-bearing AC** (AC-5): a passing unit test on the extractor proves nothing if the baseline catalog is never loaded by a neon_dystopia/road_warrior session. RED must include the wiring test.

Coordination-only on the orchestrator (no code branch here); server + content carry the work on `feat/114-5-cwn-extraction-personal-gear`.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev/Agent Smith)

**Test Files (server repo, branch `feat/114-5-cwn-extraction-personal-gear`):**
- `tests/fixtures/cwn_srd/equipment_chapter.txt` — synthetic CWN SRD fixture (Armor/Melee/Ranged/General use the shared WN layout per ADR-145 D4; net-new **Cyberware** section with a `Strain` column).
- `tests/cli/test_cwn_equip_extract.py` — 14 tests: CWN extraction tool mirroring the 114-3 WWN tool. Verbatim/cwn/wn-free provenance, srd_ref names CWN not WWN, the cyberware section emitting a typed `system_strain` int, licensing fail-loud (`none`/`na`/`ccby`), required `--srd-path`, and the `python -m sidequest.cli.cwn_equip_extract` CLI wiring test.
- `tests/genre/test_catalog_item_system_strain.py` — 5 tests: the `CatalogItem.system_strain: int | None = None` schema delta (typed, None-defaulted, rejects prose + negative, keeps `extra="forbid"`).
- `tests/server/test_cwn_inventory_wiring.py` — 3 tests: `system_strain` is a locked mechanical field (`VerbatimFieldLockError` on world re-stat; reskin preserves it) and the CWN baseline loads through the real `resolve_inventory` seam + fires its `state_transition` OTEL span (the wiring proof).

**Tests Written:** 22 tests covering the 6 derived ACs.

**RED verified directly** via `uv run pytest -n0` (not the `testing-runner` subagent — known to hallucinate output and clobber the session file). Honest result: `tests/cli/test_cwn_equip_extract.py` errors at collection (`ModuleNotFoundError: sidequest.cli.cwn_equip_extract`); schema + wiring positive tests FAIL on the absent `system_strain` field (`extra_forbidden` / `AttributeError`). 3 negative/invariant guards pass trivially now (field absent) and become load-bearing once the field lands — each fails if Dev omits int-typing, `ge=0`, or relaxes `extra=forbid`.

**AC → test mapping:**
| AC (derived from the 114-3/114-4 pattern) | Test(s) |
|---|---|
| (1) CWN extraction tool exists, tested, refuses non-permitting license (fail loud) | `test_refuses_verbatim_under_non_permitting_license[none/na/ccby]`, `test_cwn_happy_path_wn_free_permits_verbatim`, `test_missing_source_path_fails_loud`, `test_source_path_is_required` |
| (2) CWN baseline catalog produced (verbatim/cwn/wn-free) | `test_extract_emits_all_fixture_items`, `test_every_item_is_provenance_stamped_verbatim_cwn`, `test_srd_ref_names_cwn_not_wwn` |
| (3) neon_dystopia + road_warrior gear references the CWN baseline (genre-baseline + world-override placement) | `test_resolve_inventory_loads_cwn_cyberware_baseline` (production-path proof); content YAML is Dev's deliverable (see Findings) |
| (4) cyberware `system_strain` is a typed, validated field | `test_catalog_item_accepts_typed_system_strain`, `test_system_strain_rejects_free_form_prose`, `test_system_strain_rejects_negative`, `test_cyberware_section_emits_typed_system_strain`, `test_cyberware_system_strain_is_int_not_prose` |
| (5) wiring: catalog loaded by production code paths, not just present | `test_resolve_inventory_loads_cwn_cyberware_baseline` (+ OTEL span), `test_cli_entrypoint_reachable` |
| (6) cyberware strain locked against world re-stat (ADR-145 D3) | `test_world_may_not_restat_verbatim_cyberware_strain`, `test_world_may_reskin_cyberware_name_keeping_strain` |

### Rule Coverage (Python lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / fail-loud | `test_refuses_verbatim_under_non_permitting_license`, `test_missing_source_path_fails_loud` | RED |
| #3 type annotations at boundaries (typed field) | `test_catalog_item_accepts_typed_system_strain`, `test_cyberware_system_strain_is_int_not_prose` | RED |
| #5 path handling (`--srd-path` required, utf-8 read) | `test_source_path_is_required`, `test_missing_source_path_fails_loud` | RED |
| #6 test quality (self-checked: no vacuous asserts; bool excluded from int check) | all (self-review) | n/a |
| #8 unsafe deserialization (loader uses `yaml.safe_load`; tool reads text, no eval) | covered by existing loader; tool has no deserialization surface | n/a |
| #11 input validation at the CLI/parser boundary | `test_source_path_is_required`, licensing-gate tests | RED |

**Rules checked:** 5 of the 13 lang-review rules are applicable to this story (extraction CLI + schema field) and carry test coverage. **Self-check:** no vacuous assertions in the new tests (negative tests use `pytest.raises` on specific `ValidationError`/`ValueError`; the `isinstance(int)` check explicitly excludes `bool`).

**Handoff:** To Dev (Agent Smith) for the GREEN phase — build the `cwn_equip_extract` CLI (sharing the WN core is encouraged), add `CatalogItem.system_strain: int | None` (`ge=0`), wire `system_strain` into `_MECHANICAL_FIELDS` + `_FIELD_DEFAULTS`, and author the neon_dystopia + road_warrior CWN-sourced gear in the content repo.

## GM Content-Sourcing Report (2026-06-14) — schema correction required before content

GM read the real CWN SRD (`~/Documents/.../Cities_Without_Number_SRD_1.0.pdf`, §3.6.7 Cyberware) to source verbatim gear. The investigation caught a fidelity defect the int-typed RED contract missed:

**Finding:** CWN's most common cyberware is priced in **fractional System Strain** — Cybereyes, Cyberears, Cranial Jack, Skillplug Jack I = **0.25**; Viper Sting, Skillplug Jack II, Eye Mods, Discretion Unit = **0.5**; plus `0` and integer values. The shipped `system_strain: int` truncates 0.25→0 (cybereyes become "free") — a verbatim-fidelity violation. The CWN cyberware table schema is also `Name | Cost | Location | Concealment | System Strain | Effect` (no TL; the tool's `_parse_cyberware` expects `Name | Strain | Cost | TL`).

**Keith's decision (2026-06-14): type `system_strain` as `float`.** Hold 0.25/0.5 verbatim; `SystemStrainPool.current`/`permanent` also become float so fractional costs sum faithfully (0.25+0.25+0.5=1.0). This reopens the engine work before GM can author the content.

**Engine change-list (TEA re-RED → Dev re-GREEN):**
1. **TEA (test contract):** `tests/genre/test_catalog_item_system_strain.py` + `tests/cli/test_cwn_equip_extract.py` — replace `isinstance(int)` assertions with float/numeric; add a fractional case (e.g. `system_strain == 0.25`); keep "rejects prose" (`"permanent"` still rejected) and `ge=0`. Update the fixture `tests/fixtures/cwn_srd/equipment_chapter.txt` cyberware section to the real CWN column layout (`Name | Cost | Location | Concealment | Strain | Effect`) with a fractional strain row.
2. **Dev:** `CatalogItem.system_strain: float | None = Field(default=None, ge=0)`; `SystemStrainPool.current`/`permanent` → float (`max` may stay int — CON-derived); rebuild the tool's cyberware parser to the real CWN layout. `_MECHANICAL_FIELDS`/`_FIELD_DEFAULTS` already include `system_strain` (unchanged).
3. **GM (after green):** author the verbatim neon_dystopia + road_warrior CWN baseline (cyberware with float strain, Location/Concealment carried in tags/description; weapons/armor/gear with normalized costs), re-source personal gear, fix the orphan Nomad/Ghost loadouts.

See the `### GM (content sourcing)` entries under Delivery Findings for the full evidence (incl. the armor Trauma-Target extra and the `$K`/`~`/`*` notation normalization).

## Dev Assessment

**Implementation Complete:** Yes (engine GREEN + content authored & verified)

**Files Changed:**
- *Server* (`sidequest-server`, commit `68f68977`, branch `feat/114-5-cwn-extraction-personal-gear`):
  - `sidequest/cli/cwn_equip_extract/` (`__init__.py`, `__main__.py`, `cwn_equip_extract.py`) — new CWN extraction CLI; `_parse_cyberware` built to the real CWN `Name|Cost|Location|Concealment|System Strain|Effect` layout (float strain, location/concealment → tags, Effect → description).
  - `sidequest/genre/models/inventory.py` — `CatalogItem.system_strain: float | None = Field(default=None, ge=0)`.
  - `sidequest/game/system_strain.py` — `SystemStrainPool.current`/`permanent` + `StrainResult.current`/`permanent`/`delta` → `float` (`max` stays `int`).
  - `sidequest/game/ruleset/without_number.py` — `apply_system_strain` `amount`/`requested` → `float`.
  - `sidequest/telemetry/spans/wn.py` — `system_strain_delta_span` `amount`/`new_total` → `float`.
  - `sidequest/server/dispatch/inventory_resolve.py` — `system_strain` in `_MECHANICAL_FIELDS` + `_FIELD_DEFAULTS` (world re-stat locked).
  - Tests + fixture: `tests/cli/test_cwn_equip_extract.py`, `tests/genre/test_catalog_item_system_strain.py`, `tests/fixtures/cwn_srd/equipment_chapter.txt` (real CWN layout + fractional `0.25` row; int→float assertions).
- *Content* (`sidequest-content`, branch `feat/114-5-cwn-extraction-personal-gear`):
  - `genre_packs/neon_dystopia/inventory.yaml` — verbatim CWN baseline (18 cyberware w/ float strain, weapons/armor/general gear); tag-only cyberware converted to typed; Nomad/Ghost orphan loadouts backed (zero orphans).
  - `genre_packs/road_warrior/inventory.yaml` — CWN baseline added; bespoke `weapon`-category personal weapons retained as combat-class starting gear; War Rider loadout restored.

**Tests:** GREEN. CWN/strain/inventory + real-pack neon/road_warrior suites pass (engine set 97; strain consumers 55; combined real-pack re-verify 111 passed / 2 skipped). Both packs `validate pack` clean (0 errors). Pre-existing, unrelated: 2 `test_genre_flavor_world_tier` weather tests fail on the original tree too (confirmed via stash) — not a 114-5 regression. Pyright: 2 pre-existing errors in `without_number.py` (lines 744/1039), outside this diff.

**Branches (pushed):** server `68f68977`, content (new branch) — both `feat/114-5-cwn-extraction-personal-gear`.

**Content authoring:** delegated to a background `gm` agent (authored via the real `cwn_equip_extract` tool for verbatim fidelity). During verification I caught + fixed a regression it introduced (retired the test-pinned bespoke `pistol`, dropped the War Rider combat-class loadout) — see the second Dev deviation.

**Handoff:** To next phase (verify/review).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The CWN armor schema (the session note's dual `rangedAC`/`meleeAC`/`soak`) is NOT pinned by the RED suite — the fixture uses the shared WN single-AC layout (ADR-145 D4: "the four WN SRDs share one item schema"). Affects `sidequest/cli/cwn_equip_extract/` + the fixture: Dev must verify CWN armor against the real SRD text and decide whether dual-AC needs both `armor_class` and `mitigation` (CatalogItem already carries both). *Found by TEA during test design.*
- **Improvement** (non-blocking): Sharing a Without-Number extraction core between `wwn_equip_extract` and `cwn_equip_extract` is encouraged (DRY) — the WWN tool's Armor/Melee/Ranged/General parsers, `_NA_CELLS`, and the licensing gate are reusable as-is; only the Cyberware section + `system_strain` is net-new. Affects `sidequest/cli/`. The tests pin only the CWN entry-point behavior, not the module structure, so this refactor is free. *Found by TEA during test design.*
- **Gap** (non-blocking): The content-side ACs (neon_dystopia + road_warrior gear re-sourced from the CWN baseline; the orphan `Nomad`/`Ghost` loadout keys backed with `starting_equipment`) are a content-repo (YAML) deliverable not covered by server tests. The server wiring test proves the *load path* (resolve_inventory loads + locks CWN cyberware); the actual pack YAML is validated by the merge/Reviewer. Affects `sidequest-content/genre_packs/{neon_dystopia,road_warrior}/`. *Found by TEA during test design.*
- **Question** (non-blocking): The `system_strain` lower bound is asserted as `ge=0` (negative rejected). If the real CWN cyberware table has no zero-strain entries, Dev may tighten to `ge=1`; `ge=0` is the safe floor that keeps the RED negative test honest. Affects `CatalogItem.system_strain`. *Found by TEA during test design.*

### GM (content sourcing)
- **Conflict** (blocking): `system_strain` must be a **float, not an int**. The real CWN SRD cyberware table (§3.6.7) prices the *most common* cyberware in **fractional System Strain**: Cybereyes (pair), Cyberears (pair), Cranial Jack, Deadman Circuit, Medical Support Readout, Skillplug Jack I = **0.25**; Viper Sting, Skillplug Jack II, Eye Mod/Dazzler, Eye Mod/Flechette, Discretion Insurance Unit, Medusa Implant = **0.5**. The shipped `CatalogItem.system_strain: int = Field(ge=0)` truncates 0.25→0, making cybereyes "free" — a verbatim-fidelity violation (the exact lie the epic's "bind, don't author" doctrine exists to prevent). Affects `sidequest/genre/models/inventory.py` (field → `float | None`), `tests/genre/test_catalog_item_system_strain.py` + `tests/cli/test_cwn_equip_extract.py` (drop the `isinstance(int)` assertions; assert numeric/float), and the tool's cyberware parser. **This is a mechanics/crunch decision → Keith's call** (float vs. quarter-point int vs. other). *Found by GM during content sourcing.*
- **Gap** (blocking): The CWN cyberware table schema is `Name | Cost | Location | Concealment | System Strain | Effect` — **no TL column**, and it adds **Location** (Body/Head/Skin/Sensory/Nerve/Limb) and **Concealment** (Obvious/Sight/Touch/Medical) grades. The tool's `_parse_cyberware` expects `Name | Strain | Cost | TL` (wrong order, wrong columns). Faithful CWN cyberware extraction needs the tool's cyberware parser rebuilt to the real layout (engine/Dev). Affects `sidequest/cli/cwn_equip_extract/cwn_equip_extract.py`. *Found by GM during content sourcing.*
- **Gap** (non-blocking): CWN armor carries mechanical extras beyond plain AC — e.g. "Dermal Armor I: AC 16, **+1 Trauma Target**"; "Dermal Armor II: AC 18 and **Shock resist**". `CatalogItem` has `armor_class` + `mitigation` (soak) but no Trauma-Target-modifier field, so verbatim CWN armor can't fully round-trip. Affects `CatalogItem` / the armor parser. *Found by GM during content sourcing.*
- **Gap** (non-blocking): CWN gear/weapon/armor tables use SRD notation the tool's integer parsers don't accept — costs as `$250`/`$1K`/`$10K`/`$5M`, encumbrance markers `~` (no enc worn), `*` (no enc for reasonable amount), `-` (none). The pre-extracted SRD text must be normalized to plain integers before the tool runs. Affects the SRD-text preprocessing step (content), documented for whoever shapes the real `--srd-path` input. *Found by GM during content sourcing.*

### Dev (implementation)
- **Gap** (non-blocking): The WN-family extraction schema drops three verbatim CWN weapon/armor facets. (1) The ranged parser encodes only the die, so a weapon's flat damage bonus (CWN rifle `1d10+2`) is held as `1d10` — the `+2` is lost. (2) `DamageSpec` Trauma Die / Trauma Rating and ranged Shock are not columns the WN-family parser reads. (3) CWN armor has dual Ranged-AC + Melee-AC + Soak; `CatalogItem` takes one `armor_class`, so the baseline uses the SRD Ranged AC and drops Melee-AC/Soak. Affects `sidequest/cli/cwn_equip_extract/cwn_equip_extract.py` + `CatalogItem`/`DamageSpec` (a richer ranged/armor schema is a follow-on; out of 114-5's typed-`system_strain` scope). *Found by Dev during implementation.*
- **Gap** (non-blocking): Confirms the GM Trauma-Target finding — `CatalogItem` has no Trauma-Target-modifier field, so CWN Dermal Armor's "+N Trauma Target" rides in `description`/`tags` text, not a typed field. A `trauma_target_mod` on `CatalogItem` (paired with the existing `CreatureCore.trauma_target_mod`) would let it round-trip. Affects `sidequest/genre/models/inventory.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The CWN baseline authored here is the iconic/common playable core (≈66 items across all 7 cyberware location tables + weapons/armor/general gear), not all ~80 CWN implants. It is extendable via the same `cwn_equip_extract` tool when a table wants deeper coverage. Affects `sidequest-content/genre_packs/{neon_dystopia,road_warrior}/inventory.yaml`. *Found by Dev during implementation.*
- **Question** (non-blocking): road_warrior's personal weapons (tire iron, chain, sawed-off, crossbow, pistol) are genuinely bespoke — they are NOT in the CWN catalog, and the personal-combat strike path + dispatch tests pin `category: weapon` items (CWN emits `melee_weapon`/`ranged_weapon`). So road_warrior's CWN binding supplies the *catalog baseline* but its combat-class starting weapons stay bespoke. If a future story wants combat classes to start with CWN-category weapons, the road_warrior strike path + `test_road_warrior_combat_classes_start_with_a_personal_weapon` need to accept `melee_weapon`/`ranged_weapon`. Affects `sidequest/server/dispatch/dice.py` consumers + the road_warrior dispatch tests. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `[SEC]` Both WN-family extraction CLIs (`cwn_equip_extract` AND the shipped `wwn_equip_extract`) call `srd_path.is_file()` without `Path.resolve()` first (lang-review rule #5 / CWE-59). Practical impact is nil — a developer-run CLI on a developer-supplied path with no privilege boundary or allowlist check that `resolve()` would protect; a symlink to any unreadable target fails loud at section-header parsing. Worth a one-line `srd_path = srd_path.resolve()` in BOTH tools as a cross-tool hygiene follow-up (not introduced by 114-5; pre-existing house pattern). Affects `sidequest/cli/{cwn,wwn}_equip_extract/*.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `[SEC]` The `--license`/`--srd` argparse args have no `choices=` whitelist, so an invalid `--license` is rejected at `extract_catalog()` (loud, before any emission) rather than at the CLI boundary (lang-review rule #11). The licensing invariant is structurally sound (defense-in-depth: gate + model validator), so this is purely an earlier-rejection nicety. Same pattern in both WN tools. Affects `sidequest/cli/{cwn,wwn}_equip_extract/*.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `[EDGE]` `_parse_cyberware` takes the FIRST arabic-numeric token as Cost; a future SRD/cyberware name containing an arabic digit (not a Roman grade) could misparse Cost/Location. Mostly self-correcting (the non-numeric strain-position check fails loud), but a one-line guard or a column-count assertion would harden it. Affects `sidequest/cli/cwn_equip_extract/cwn_equip_extract.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **CWN licensing resolved to `wn-free`/verbatim rather than left as an open "verify" step**
  - Spec source: SM Assessment ("CWN is 'likely CC0 — VERIFY'; the tool must refuse verbatim emission under an unverified license") + epic-114 description ("CWN likely CC0 (verify)").
  - Spec text: "RED should assert that refusal" / "verify CWN's license before bulk-import."
  - Implementation: Tests assert CWN extraction emits `mode=verbatim, srd=cwn, license=wn-free` and that the licensing gate still fails loud under `none`/`na`/`ccby`. The "is CWN verbatim-permitted at all" question is treated as **already settled**, not an open runtime check.
  - Rationale: ADR-145 D4 (higher authority than the SM assessment / epic blurb per the spec-authority hierarchy) explicitly states "verbatim … is the mode for **all four WN SRDs** (WWN, CWN, SWN, AWN) under their free-use terms" and `_VERBATIM_LICENSES = {"wn-free"}` already covers the WN line. The epic's "(verify)" parenthetical was pre-ADR uncertainty the governing ADR has closed. The fail-loud gate SM wanted is still asserted — just keyed on the settled `wn-free` value.
  - Severity: minor
  - Forward impact: Dev emits `license="wn-free"` for CWN; no separate CWN-license-verification gate is built. If a future audit overturns the WN free-use basis, the change is centralized in `_VERBATIM_LICENSES`.
- **CWN armor column schema (dual AC / soak) intentionally not pinned**
  - Spec source: context-story-114-5 / session Technical Notes ("CWN §3.0.0: armor (rangedAC/meleeAC/soak)").
  - Spec text: "CWN §3.0.0 equipment chapter includes: armor (rangedAC/meleeAC/soak)".
  - Implementation: The synthetic fixture's Armor section uses the shared WN single-AC layout; no test asserts CWN dual-AC/soak extraction.
  - Rationale: I cannot verify the real CWN armor column layout without the out-of-repo SRD; pinning a guessed dual-AC schema would force an implementation I can't confirm. ADR-145 D4 says the four WN SRDs share one item schema, and CatalogItem already expresses both `armor_class` and `mitigation` (soak), so the representation exists if needed. Logged as a non-blocking Gap for Dev to verify against the real SRD.
  - Severity: minor
  - Forward impact: Dev verifies CWN armor against the real SRD; the armor-extraction detail is covered by Dev running the tool on the real text, not by this RED suite.

### Dev (implementation)
- **`system_strain` typed as `float`, not `int` — RED int contract corrected per Keith's ruling**
  - Spec source: TEA Assessment AC-4 + `tests/genre/test_catalog_item_system_strain.py` / `tests/cli/test_cwn_equip_extract.py` (RED) — asserted `system_strain: int` (`isinstance(int)`).
  - Spec text: "add `CatalogItem.system_strain: int | None` (`ge=0`)"; "a typed `system_strain: int` reproduced verbatim"; "the cyberware section emitting a typed `system_strain` int".
  - Implementation: `CatalogItem.system_strain: float | None = Field(default=None, ge=0)`; `SystemStrainPool.current`/`permanent` + `StrainResult.current`/`permanent`/`delta` → `float` (`max` stays `int`, CON-derived); `WithoutNumberRulesetModule.apply_system_strain` `amount`/`requested` → `float`; `system_strain_delta_span` `amount`/`new_total` → `float`. The tool's `_parse_cyberware` rebuilt to the real CWN `Name|Cost|Location|Concealment|System Strain|Effect` layout, parsing strain as `float`. Fixture + the two cyberware `isinstance(int)` assertions updated to numeric/`float` with an added fractional `0.25` case.
  - Rationale: GM read the real CWN SRD §3.6.7 and found the most common cyberware is priced in **fractional** System Strain (Cybereyes/Cyberears/Skillplug Jack I = 0.25; Viper Sting/Skillplug Jack II = 0.5). An int truncates 0.25→0, making the genre's iconic chrome "free" — a verbatim-fidelity violation (the exact lie epic-114's "bind, don't author" doctrine exists to prevent). **Keith ruled `float`, 2026-06-14** (pool too, so fractional installs sum faithfully: 0.25+0.25+0.5=1.0). Per spec-authority, Keith's live ruling outranks the RED int contract.
  - Severity: minor
  - Forward impact: Forward-prep only — `item.system_strain` (catalog) is not yet wired into the runtime pool (`apply_system_strain` still takes `kind`+config amount); the install→apply-strain wiring is a future story. The pool float widening here just makes that path ready. No int call sites broke (int is float-compatible); 152 strain/inventory tests green.
- **road_warrior personal weapons kept bespoke instead of fully re-sourced to the CWN baseline**
  - Spec source: TEA Assessment AC-3 + Technical Notes ("road_warrior personal gear re-source to CWN baseline").
  - Spec text: "pull personal gear from the extracted CWN baseline; world-tier inventory.yaml overrides only bespoke/world-distinct gear."
  - Implementation: The CWN baseline (~66 verbatim items) IS added to road_warrior's genre-tier catalog, and CWN-mappable gear (medkits/tools/radios etc.) references it. But road_warrior's iconic improvised personal weapons (tire iron, chain, sawed-off, crossbow, and the bespoke `pistol`) stay `mode: bespoke, category: weapon` and remain the combat-class starting weapons. (The gm agent initially retired the bespoke `pistol` for the CWN `cwn_light_pistol` and dropped the War Rider loadout; I reverted both.)
  - Rationale: (1) road_warrior's improvised arms are genuinely world-distinct — they are NOT in the CWN catalog, so re-sourcing them would be fabrication, not binding. (2) road_warrior's personal-combat strike path + its dispatch tests (`test_road_warrior_combat_dispatch.py`) pin `category: weapon` items by id; CWN weapons are `melee_weapon`/`ranged_weapon`, which that path/guard doesn't accept as the combat-class starting weapon. Using a CWN weapon as the sole starting weapon left two combat classes "unarmed" and a 'shoot' strike dealing 0 HP (`damage_spec_missing`). Keeping the bespoke `weapon`-category items is the faithful AND test-correct placement.
  - Severity: minor
  - Forward impact: AC-3 satisfied — the CWN baseline is bound and present; the only items left bespoke are genuinely non-SRD. If a later story wants combat classes to start with CWN-category weapons, the road_warrior strike path + the personal-weapon guard must accept `melee_weapon`/`ranged_weapon` (logged as a Dev Delivery Finding).

### Reviewer (audit)
- **TEA: CWN licensing resolved to `wn-free`/verbatim** → ✓ ACCEPTED by Reviewer: ADR-145 D4 governs (higher authority than the epic blurb), and the fail-loud gate is preserved at TWO layers (`extract_catalog` + `ItemProvenance` model validator). Sound.
- **TEA: CWN armor dual-AC/soak not pinned in RED** → ✓ ACCEPTED by Reviewer: pinning a guessed armor schema against an out-of-repo SRD would force unverifiable code; `CatalogItem` already carries `armor_class`+`mitigation`. Dev confirmed against the real SRD and logged the single-AC choice as a non-blocking gap.
- **Dev: `system_strain` typed `float` not `int`** → ✓ ACCEPTED by Reviewer: Keith's 2026-06-14 ruling (live spec authority) corrects a genuine verbatim-fidelity defect (int truncates 0.25→"free" chrome). Float widening is complete across all 5 strain surfaces with `max` correctly kept int; no call site stranded (numeric tower). The contract correction is the right call and well-executed.
- **Dev: road_warrior personal weapons kept bespoke** → ✓ ACCEPTED by Reviewer: road_warrior's improvised arms genuinely are not in the CWN catalog (re-sourcing would be fabrication, violating "bind, don't author"), and the road_warrior strike path + dispatch guard pin `category: weapon`. Retaining the bespoke weapons is both faithful and test-correct; the CWN baseline is still bound additively, satisfying AC-3. No undocumented deviations spotted — the diff matches the four logged entries.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T23:49:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T22:04:16Z | 2026-06-14T22:08:25Z | 4m 9s |
| red | 2026-06-14T22:08:25Z | 2026-06-14T22:24:22Z | 15m 57s |
| green | 2026-06-14T22:24:22Z | 2026-06-14T23:39:26Z | 1h 15m |
| review | 2026-06-14T23:39:26Z | 2026-06-14T23:49:36Z | 10m 10s |
| finish | 2026-06-14T23:49:36Z | - | - |

## Technical Notes for Dev

### Reference material

1. **Inventory audit (2026-06-14):** `docs/inventory-audit-2026-06-14.md`
   - Current state: no pack sources gear from its bound SRD's equipment chapter
   - Heavy_metal/evropi: weapons/armor missing damage/AC entirely (worst defect)
   - Neon_dystopia: cyberware is a tag, not a system_strain field; orphan loadout keys (Nomad/Ghost)
   - Road_warrior: personal gear partial (hand-authored); vehicular = bespoke homebrew, dormant

2. **ADR-145 (SRD-sourced inventory model):** `docs/adr/145-srd-sourced-inventory-model.md`
   - D1: What it means for gear to "be" SRD gear (mechanical envelope reproduced verbatim; presentation can be reskinned)
   - D2: Schema delta — CatalogItem grows provenance record + WN ranged/TL fields
   - D3: Placement + merge — genre-tier baseline catalog, world-tier overrides only (non-droppable baseline)
   - D4: Licensing policy — WN SRDs are "free-use"; CWN must be verified before verbatim reproduction
   - D5: Fate seam (deferred, not part of 114-5)

3. **WWN extraction tool pattern (114-3, done):** `sidequest-server/sidequest/cli/wwn_equip_extract/`
   - `wwn_equip_extract.py`: reads pre-extracted text file, emits provenance-stamped CatalogItem records
   - Tool version stamp: TOOL_VERSION = "wwn_equip_extract@114-3"
   - Licensing invariant: tool refuses to emit verbatim items under non-verbatim license (fail loud)
   - Section labels per category: armor, melee, ranged, general
   - Handles NA cells (_NA_CELLS) in SRD text correctly (None, -, —, N/A)

4. **WWN baseline catalog wiring (114-4, done):** Content side
   - Genre-level inventory.yaml placed under `genre_packs/caverns_and_claudes/` (and others)
   - World-level overrides under `genre_packs/<genre>/worlds/<world>/inventory.yaml`
   - ADR-140 doctrine: crunch at genre tier (the SRD baseline), flavor at world tier

### Technical tasks for this story

#### Server side (sidequest-server)

1. **Extend/build the CWN extraction tool**
   - Parallel pattern to `wwn_equip_extract.py`, adapted for CWN's richer schema
   - CWN §3.0.0 equipment chapter includes: armor (rangedAC/meleeAC/soak), weapons (damage/range/mag), cyberware (system_strain/location/concentration)
   - Pre-extraction: CWN SRD text → text file (same preprocessing as WWN)
   - Output: CatalogItem records with provenance (mode=verbatim, srd=cwn, license=?, srd_ref="CWN SRD §3.0.0")
   - **Licensing check:** Tool must verify CWN's "free-use" claim before emitting verbatim items. If unverified, fail loud with message "CWN license must be verified before bulk-import."
   - Tests: unit test on fixture text, wiring test confirming tool is called from production path (if there is one)

2. **Make cyberware system_strain a typed field**
   - Currently: system_strain is ad-hoc/free-form in cyberware entries
   - Target: add `system_strain: int | None = None` field to `DamageSpec` or create a dedicated `CyberwareSpec` (depends on schema decision)
   - CWN cyberware rows include: `systemStrain` value (e.g. "3", "1d6", "permanent")
   - If the value is numeric, type it; if it's a die roll, decide whether to parse it or store as prose
   - Tests: validate that a CWN cyberware item with system_strain resolves correctly in chargen/encounter

3. **Produce the CWN baseline catalog**
   - Extract the ~150 base CWN items from the SRD text (armor, weapons, cyberware, general gear)
   - Output: `genre_packs/neon_dystopia/inventory.yaml` (or wherever the baseline lands per ADR-140)
   - Schema: standard CatalogItem records, each with ItemProvenance(mode=verbatim, srd=cwn, license=<verified>, ...)

4. **Integration tests**
   - Wiring test: verify CWN baseline is loaded by production code paths (e.g., when a neon_dystopia session initializes, the extracted baseline is present)
   - Chargen test: a neon_dystopia character can equip CWN cyberware with system_strain; system_strain value is correctly parsed/validated
   - Bonus: if schema allows, test that a world-override item can reskin a CWN item while keeping mechanics intact

#### Content side (sidequest-content)

1. **Neon_dystopia personal gear re-source to CWN baseline**
   - Current state: hand-authored items.yaml (audit found cyberware as a tag, not system_strain field; orphan loadout keys)
   - Target: pull personal gear from the extracted CWN baseline; world-tier inventory.yaml overrides only bespoke/world-distinct gear
   - Remove orphan loadout keys (Nomad/Ghost) from archetype definitions, or back them with world-distinct classes if they're intentional
   - Verify: chargen for neon_dystopia correctly reflects CWN cyberware with system_strain

2. **Road_warrior personal gear re-source to CWN baseline**
   - Current state: hand-authored items.yaml (personal gear partial); vehicular = bespoke homebrew (dormant, not part of this story)
   - Target: pull personal gear from extracted CWN baseline; keep world-distinct items as bespoke overrides
   - Note: vehicular binding (CWN vehicle chapter) is deferred to 114-6 (dependent on 114-5)
   - Verify: chargen for road_warrior correctly pulls CWN baseline gear

3. **Acceptance criteria (derived from 114-3/114-4 pattern)**
   - (1) CWN extraction tool exists, tested, and refuses non-verbatim licenses (fail loud)
   - (2) CWN baseline catalog is produced and placed at genre tier per ADR-140
   - (3) Neon_dystopia and road_warrior personal gear reference the CWN baseline (genre-baseline + world-override placement)
   - (4) Cyberware system_strain is a typed field with validation and tests
   - (5) Wiring test proves the catalog is loaded by production code paths (not just present as a file)
   - (6) No orphan loadout keys (or backed by world-specific classes)

### Known constraints & dependencies

- **Dependency:** 114-3 (done) — the extraction-tool substrate and CatalogItem provenance pattern
- **Licensing gate:** CWN's "free-use" claim must be verified before bulk-reproduction. Current audit note: "CWN — likely CC0 (verify)."
- **ADR-140 coordination:** genre = crunch (SRD baseline), world = flavor (overrides only). This story's work naturally falls into that placement.
- **Schema:** CatalogItem already carries DamageSpec; cyberware system_strain must either extend DamageSpec or warrant a new Spec type.
- **Tests must include wiring:** unit tests alone will false-green if the catalog exists but isn't called.

### Branch strategy

- **Orchestrator (main):** no feature branch; this is a coordination story
- **Server (sidequest-server):** gitflow → `feat/114-5-cwn-extraction-personal-gear` off develop
- **Content (sidequest-content):** gitflow → `feat/114-5-cwn-extraction-personal-gear` off develop

### Related ADRs & stories

- **ADR-143:** Bind the Ruleset, Don't Balance It (combat)
- **ADR-144:** Fate Core Binding Replaces Native Ruleset (mechanics)
- **ADR-145:** SRD-Sourced Inventory — this ADR (implementation)
- **ADR-140:** Genre Is the Rulebook Only; the World Owns the Cast and Catalog (placement)
- **114-3 (done):** WWN extraction tool
- **114-4 (done):** WWN baseline catalog + wiring
- **114-6 (depends on 114-5):** road_warrior vehicle binding

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | smells noted (3 print(), 4 type:ignore) | confirmed 0 blocking (print=intentional CLI stdout/stderr; type:ignore load-bearing/justified) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [EDGE] analysis) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [SILENT] analysis) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [TEST] analysis) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [DOC] analysis) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [TYPE] analysis) |
| 7 | reviewer-security | Yes | findings | 2 (both low) | confirmed 2 (both LOW/non-blocking, captured as Delivery Findings), dismissed 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [SIMPLE] analysis) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [RULE] enumeration) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` settings, pre-filled per protocol)
**Total findings:** 2 confirmed (LOW/non-blocking), 0 dismissed, 0 deferred. Preflight smells assessed and cleared. The 7 disabled dimensions are each covered by the Reviewer's own tagged analysis below (gate-required dispatch tags present).

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** developer SRD text → `extract_catalog()` (licensing gate at line 376 + per-row fail-loud parse) → provenance-stamped `CatalogItem` (mode=verbatim requires wn-free, enforced again structurally in `ItemProvenance` validator) → content `inventory.yaml` (genre tier) → a neon_dystopia/road_warrior session calls `resolve_inventory(pack, world)` → `merge_inventory_catalog` locks `system_strain` as a mechanical field → resolved `CatalogItem.system_strain == 0.25` (float, not truncated) reaches the resolver and fires a `state_transition` OTEL span (GM-panel lie detector). **Safe because:** verbatim provenance cannot be minted under a non-permitting license from any construction path (defense-in-depth), and a world cannot re-stat the locked strain (`VerbatimFieldLockError`, tested).

**Pattern observed:** the CWN tool deliberately mirrors the shipped WWN tool (114-3) — same CLI contract, same `_NA_CELLS`/`_row_context` fail-loud discipline (`cwn_equip_extract.py`), with one net-new `_parse_cyberware` section. Good consistency; the DRY shared-core extraction is correctly deferred (logged) rather than prematurely abstracted mid-story.

**Error handling:** every failure path fails loud — missing `--srd-path` → stderr + exit 1 (`cwn_equip_extract.py:427-434`); missing section header → `ValueError` (`:386-388`); malformed/short row, non-numeric strain → `ValueError` with section+row context (`_row_context`, `:169-174`); top-level `except Exception` surfaces the message to stderr + returns 1 (`:439-441`) — converts any error into a non-zero exit, never a silent empty catalog.

### Rule Compliance (Python lang-review checklist — enumerated against all changed `.py`)

| # | Rule | Verdict |
|---|------|---------|
| 1 | Silent exception swallowing | COMPLIANT — `[SILENT]` no bare `except`, no `except: pass`; `main()` broad `except` (BLE001, commented) surfaces to stderr + exit 1; `_row_context` re-raises with context; pydantic `ValidationError` IS-A `ValueError` so it surfaces too. |
| 2 | Mutable default arguments | COMPLIANT — only immutable defaults (`license: str = "wn-free"`); no list/dict/set defaults; no shared class-level mutables. |
| 3 | Type annotations at boundaries | COMPLIANT `[TYPE]` — `extract_catalog`/`main`/`build_parser`/all `_parse_*` fully annotated; the lone `# type: ignore[arg-type]` carries its specific code + "validated by the model" rationale. |
| 4 | Logging coverage/correctness | N/A — CLI uses stdout(JSON)/stderr(errors) by design (not a logging module); engine deltas already emit OTEL spans. |
| 5 | Path handling | COMPLIANT w/ 1 LOW note `[SEC]` — `read_text(encoding="utf-8")` ✓, `pathlib` throughout ✓; `.resolve()` not called before `is_file()` (CWE-59) — LOW/non-blocking, matches shipped WWN precedent, captured as Delivery Finding. |
| 6 | Test quality | COMPLIANT `[TEST]` — specific value asserts (0.25, 10000), `bool` excluded from numeric checks, no vacuous asserts; wiring test drives real `resolve_inventory` + asserts the OTEL span (not source-grep). |
| 7 | Resource leaks | COMPLIANT — `read_text` (no dangling handle); no unmanaged resources. |
| 8 | Unsafe deserialization | COMPLIANT — no pickle/eval/exec; no `yaml.load`; `json.dumps` output only; test `json.loads` is on the tool's own trusted subprocess stdout. |
| 9 | Async/await pitfalls | N/A — no async code in diff. |
| 10 | Import hygiene | COMPLIANT — explicit imports, `from __future__ import annotations`, no star imports, no new cycles. |
| 11 | Input validation at boundaries | COMPLIANT w/ 1 LOW note `[SEC]` — `_is_numeric()` pre-validates before every `int()`/`float()`; licensing gate validates before emission; missing argparse `choices=` is a LOW earlier-rejection nicety (validated at `extract_catalog`), captured as Delivery Finding. |
| 12 | Dependency hygiene | COMPLIANT — no new dependencies. |
| 13 | Fix-introduced regressions | COMPLIANT — the road_warrior content fix (restore bespoke `pistol` + War Rider loadout) was re-verified GREEN; introduced no new broad excepts or type drift. |

### Observations (≥5)

- `[VERIFIED]` `[RULE]` Licensing gate is defense-in-depth — `extract_catalog` rejects non-`wn-free` verbatim emission (`cwn_equip_extract.py:376`) AND `ItemProvenance._verbatim_requires_permitting_license` rejects it structurally (`inventory.py:171-182`). No path mints an inconsistent verbatim item. Complies with the "No Silent Fallbacks" CRITICAL rule.
- `[VERIFIED]` `[TYPE]` Float widening complete and backward-compatible — `CatalogItem.system_strain`, `SystemStrainPool.current/permanent`, `StrainResult.current/permanent/delta`, `apply_system_strain.amount/requested`, `system_strain_delta_span.amount/new_total` are all `float`; `max` correctly stays `int`. The 4 call sites (`use_ops.py:96`, `stocks.py:286`, `adjust_system_strain.py:116`, `without_number.py:1047`) pass int amounts — accepted via the numeric tower. No caller stranded; `extra="forbid"` preserved on all 3 models.
- `[SEC]` (LOW, non-blocking) `srd_path.is_file()` runs on an unresolved path (`cwn_equip_extract.py:426`, CWE-59 / rule #5). No privilege boundary in a dev CLI; identical to the shipped WWN tool. Captured as a cross-tool Delivery Finding.
- `[SEC]` (LOW, non-blocking) `--license`/`--srd` lack an argparse `choices=` whitelist (`:411-419`, rule #11); rejection happens loudly at `extract_catalog()` instead. Captured as a Delivery Finding.
- `[EDGE]` (LOW) `_parse_cyberware` takes the first arabic-numeric token as Cost (`:304`); a cyberware name with an arabic digit could misparse (mostly self-corrected by the non-numeric strain-position check failing loud). Hardening note captured.
- `[SILENT]` `[VERIFIED]` No silent fallbacks anywhere — every missing/malformed input raises or exits non-zero; the `_data_rows` header-drop is bounded (a *second* "Name…" row fails loud rather than silently dropping data).
- `[DOC]` `[VERIFIED]` Comments/docstrings track the code — the module docstring describes the rebuilt `Name|Cost|Location|Concealment|System Strain|Effect` layout exactly, and the `CatalogItem.system_strain` comment correctly explains the float-not-int rationale. The fixture comment block matches the data rows. No stale comments (the agent's "pistol retired" comment was correctly replaced when Dev restored the item).
- `[SIMPLE]` `[VERIFIED]` No over-engineering — the cyberware parser is a direct token walk; the shared WN extraction core is appropriately deferred to a follow-up rather than abstracted prematurely under one consumer.
- `[VERIFIED]` Content fidelity (spot-check) — neon cyberware float strain matches the verbatim CWN data (cybereyes/cyberears/skillplug_jack_i 0.25; viper_sting 0.5; enhanced_reflexes_i 2.0); genre-tier placement only (ADR-140); zero world-tier re-stat; both packs `validate pack` clean; zero dangling loadout refs; loadout↔gold parity for all classes in both packs.

### Devil's Advocate

Assume this is broken. The most dangerous surface is the float widening: by promoting `SystemStrainPool.current/permanent` from `int` to `float`, did I silently change runtime arithmetic for the eight live packs that already use System Strain (WWN/AWN combat)? If any consumer compared `pool.current == some_int` or used `pool.current` as a dict key, float coercion (2 → 2.0) could break equality or hashing. Counter: I enumerated all 4 call sites and the preflight ran the strain consumers (`test_use_ops`, `test_implant_strain`, `test_adjust_system_strain_tool`, `test_cwn_system_strain`, `test_system_strain_pool`) — 68/68 green; `2.0 == 2` holds and no strain value is used as a dict key. Second attack: the cyberware parser. A malicious/garbled SRD text could carry a row like `Cyberarm Mk 2 50000 Limb Obvious 1 ...` where "2" in the name becomes Cost — but then the strain-position token lands on a word and raises `ValueError`, so it fails loud rather than emitting a wrong implant; the worst realistic case is a loud crash on bad input, which is the desired behavior, not a silent lie. Third: a confused operator points `--srd-path` at a symlink to a sensitive file — but the tool only reads text the operator already has access to, writes JSON to the operator's own stdout, and finds no `§` headers so it exits 1; no exfiltration boundary is crossed. Fourth: content. Could a world silently cheapen cyberware? No — `system_strain` is now in `_MECHANICAL_FIELDS`, so a world re-stat raises `VerbatimFieldLockError` (tested), and the content ships genre-tier only with no world overrides. Fifth: the stressed-filesystem case — `read_text` on a missing/locked file raises, caught and reported to stderr with exit 1. The one genuine residual is the documented schema-fidelity gap (rifle `+2`, armor dual-AC, trauma-target field) — but those are *honestly logged* as Delivery Findings, not silently fabricated values, which is exactly the discipline epic-114 demands. Nothing here rises to Critical/High.

**Verdict rationale:** zero Critical/High findings; two LOW security/rule items (both non-blocking, both consistent with shipped precedent, both captured as follow-ups); tests GREEN (68/68 + Dev's broader real-pack sweep); content validates clean with verified fidelity. The float-contract correction and the road_warrior regression fix are both sound. APPROVED.

**Handoff:** To Morpheus (SM) for finish-story.