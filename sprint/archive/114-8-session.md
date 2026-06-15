---
story_id: "114-8"
jira_key: ""
epic: "114"
workflow: "tdd"
---
# Story 114-8: mutant_wasteland — re-stat inventory against the AWN schema (trauma die/shock), fix genre scrap_armor mitigation

## Story Details
- **ID:** 114-8
- **Jira Key:** (none — SideQuest is personal)
- **Workflow:** tdd
- **Stack Parent:** 114-1 (status: done)
- **Repos:** server, content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T08:08:38Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T05:42:53Z | - | - |
| red | - | 2026-06-15T07:47:44Z | unknown |
| green | 2026-06-15T07:47:44Z | 2026-06-15T08:00:14Z | 12m 30s |
| review | 2026-06-15T08:00:14Z | 2026-06-15T08:08:38Z | 8m 24s |
| finish | 2026-06-15T08:08:38Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

- **[SM · Conflict · blocking]** Wiring-tier conflict to resolve before authoring: SM memory says world `inventory.yaml` is engine-unwired (crunch loads genre-tier only), but the 2026-06-14 audit says mutant_wasteland's *world* catalog "replaces genre wholesale" and dropped `power_glove` from chargen. Both cannot be true. TEA: write a wiring test proving which tier the chargen/resolution path actually loads for mutant_wasteland BEFORE editing any catalog — a world-tier edit may silently no-op. See `sprint/context/context-story-114-8.md` → "Wiring tension".
- **[SM · Constraint · blocking]** AWN free edition has NO open license — **derive/re-stat against the AWN schema, do NOT copy AWN tables verbatim** (ADR-145 SWN/AWN lane). Item names/flavor must be SideQuest-original.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **[Conflict · resolved]** RESOLVES the SM "wiring-tier conflict" finding above. Both SM facts were stale. `sidequest/server/dispatch/inventory_resolve.py:resolve_inventory(pack, world_slug)` does an ADR-145 D3 **non-droppable by-id merge** (landed in 114-11): the genre baseline survives; the world catalog merges *over* it (not wholesale-replace). The "REPLACES wholesale" comment atop `seaboard_of_saints/inventory.yaml` predates 114-11 and is stale. `power_glove` is present in BOTH tiers (114-2 added it to the world) and survives the merge — proven by the passing `tests/server/test_114_8_power_glove_nondroppable.py`. Dev: edit at the **genre tier** for baseline gear; world-tier edits merge over it.
- **[Conflict · CORRECTS SM finding]** The SM "AWN has no open license — derive, do NOT copy verbatim" finding is **superseded by ADR-145 D4** (and Keith's 2026-06-15 direction to source from the real Sine Nomine SRD docs). ALL four WN SRDs — incl. **AWN** — are reproduce-**verbatim** under Sine Nomine's free-use terms. Gear is `mode=verbatim, srd=awn, license=wn-free, srd_ref`. The `ItemProvenance` validator structurally enforces verbatim⇒wn-free. Source: `/Users/slabgorb/Documents/DriveThruRPG/Sine Nomine Publishing/Ashes Without Number_ Free Edition/AshesWithoutNumber_FreeVersion_071025.pdf` (Equipment chapter pp.76-78; `pdftotext` extract at `/tmp/awn_full.txt` lines ~4317 armor, ~4406 ranged weapons). D4a: factual sourcing only — NO implied Sine Nomine / Kevin Crawford endorsement. D4b: source the SRD only, never a commercial book.
- **[Improvement · non-blocking]** Stale premise: the `power_glove` broken-ref regression named in the title/ADR-145 is **already fixed** (114-2 added it to the seaboard world catalog; 114-11 made the merge non-droppable). File-3 tests pass as regression guards. Remaining 114-8 work is the AWN verbatim re-stat + provenance + the `scrap_armor` AC defect — NOT power_glove.
- **[Question · blocking-for-Dev]** Genre-baseline SHAPE fork Dev must pick at GREEN. **Model A** (like elemental_harmony/114-4): raw `awn_*` SRD ids at the genre tier, wasteland flavor as world-tier reskins — but this renames `scrap_armor`/`sawed_off`/etc. and breaks `starting_equipment` id refs (rewire needed). **Model B** (ADR-145 D1 explicitly permits): keep the flavorful genre ids, stamp each `mode=verbatim` with `srd_ref` to the AWN item it reproduces (a genre-tier reskin). My tests are id-agnostic EXCEPT `test_scrap_armor_is_the_awn_scrap_mail_reskin`, which pins `scrap_armor` at the genre tier (the title's named target ⇒ Model B for that item). Recommendation: **Model B** — it satisfies the title's named `scrap_armor`/genre-tier deliverable, avoids the starting_equipment rewire, and is ADR-145-D1-compliant. If Dev chooses Model A, reconcile the renamed scrap_armor and log a deviation.
- **[Question · non-blocking]** Artifact placement (ADR-145 D1/D3). The 5 pre-war chargen artifacts (`power_glove`, `datapad`, `growth_wand`, `purifier`, `mystery_compass`) are NOT AWN SRD gear → legitimately `provenance.mode=bespoke`. ADR-145 says bespoke is a **world-tier** privilege and genre-tier bespoke is a D4 "hard error" (NOT currently enforced by the loader). I deliberately did NOT write a hard "no genre-tier bespoke" test (would balloon scope to move 5 artifacts across both worlds + rewire chargen). Stamping them `mode=bespoke` at the genre tier satisfies `test_every_genre_catalog_item_carries_provenance`. Keith/Dev to decide: move-to-world-tier vs. documented genre-bespoke exception.
- **[Gap · non-blocking]** "shock" (in the title): AWN melee weapons carry Shock (WN "Shock X/AC Y"; `DamageSpec` enforces `shock>0 ⇒ shock_ac`). I assert Trauma Die/Rating universally on weapons but do NOT hard-assert `shock` presence (can't generically tell which genre weapons are melee). Dev: source `shock`/`shock_ac` faithfully for melee weapons from the AWN SRD melee table.

### Dev (implementation)
- **[Improvement · non-blocking]** Chose TEA's recommended **Model B** (genre-tier verbatim reskin): kept the flavorful genre ids (`scrap_armor`, `sawed_off`, etc.), stamped each `mode=verbatim` with `srd_ref`. No `starting_equipment` rewire needed; `scrap_armor` stays the title's named target. The AWN melee `shock` IS sourced (Spear 2/AC13, Club 1/AC18).
- **[Gap · non-blocking → server]** **No AWN extraction tool exists** (only `wwn_equip_extract` + `cwn_equip_extract`; the AWN tool tests SKIP). I sourced the ~5 standard items by hand from the AWN SRD — fine at this catalog size, but a full AWN baseline (≈200 items) would want an `awn_equip_extract` CLI. Candidate follow-on (parallels 114-12's WN-extraction-CLI hardening). Affects `sidequest-server/sidequest/cli/` (no AWN extractor).
- **[Question · non-blocking]** Bound item `value` to the AWN SRD's printed costs (Spear 5, Shotgun 100, Scrap Mail 100) per ADR-145 D1 (cost is part of the verbatim envelope). The wasteland's `starting_gold` is Salvage-scale (Scavenger 8) and unchanged (world-kit, ADR-145 D3). Same currency-unit caveat the WWN packs carry — flagged in the file header. If the Salvage economy should diverge from AWN credit costs, that's a separate economy-tuning call (Keith).
- **[Question · non-blocking]** `range_band`/`magazine` set on the two ranged weapons (bow `20/100` mag 1, shotgun `10/30` mag 2, matching road_warrior's CWN convention); intentionally NOT set on the melee weapons (Spear/Club have an AWN thrown range `10/20`, but they're melee-tagged — adding range_band risks the engine treating them as ranged). Reviewer: confirm that's the right call.

### Reviewer (code review)
- **[Improvement · non-blocking]** `tests/genre/test_114_8_mutant_wasteland_awn_inventory.py::test_every_combat_weapon_carries_awn_trauma_fields` fails on `trauma_rating <= 1`, which is slightly over-strict: AWN does have x1 multipliers (e.g. Unarmed). No current catalog weapon is x1 (all x2+), so it passes today — but a future AWN x1 catalog weapon would falsely fail. Affects that test (consider `trauma_die is None` as the condition if an x1 weapon is ever added). Confirmed range_band-on-melee omission is the right call (melee-tagged weapons shouldn't advertise a ranged band). *Found by Reviewer during code review.*
- **[Improvement · non-blocking]** `range_band` is stored as the SRD's `"normal/long"` string (e.g. `"20/100"`) per the road_warrior/CWN convention — fine, but the `CatalogItem.range_band` docstring suggests a band *category* (`"thrown"|"pistol"|"rifle"`). The two conventions coexist across packs; a future pass could reconcile the field's intended vocabulary. Affects `sidequest-server/sidequest/genre/models/inventory.py` (range_band doc vs usage). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests assert verbatim AWN sourcing, not "derive against the schema"**
  - Spec source: story title "114-8" + `sprint/context/context-story-114-8.md` (Licensing constraint, SM-authored from the 2026-06-14 audit)
  - Spec text: "re-stat inventory against the AWN **schema**" / "AWN free edition carries NO open license — derive/re-stat … do NOT reproduce AWN tables verbatim"
  - Implementation: RED tests assert `provenance.mode == "verbatim"`, `srd == "awn"`, `license == "wn-free"` (not `derived`), and the `scrap_armor`/weapon mechanics are the AWN SRD's own values carried unchanged.
  - Rationale: ADR-145 D4 (the design output of this story's dependency 114-1) explicitly supersedes the audit's licensing read — all four WN SRDs incl. AWN are verbatim-reproducible under Sine Nomine's free-use terms. Keith confirmed on 2026-06-15 by directing me to source from the real Sine Nomine SRD documents. The `ItemProvenance` model structurally enforces verbatim⇒wn-free, so "derived" would be the wrong contract.
  - Severity: minor (the title's "re-stat against the AWN schema" is satisfied by verbatim AWN items; only the licensing *mode* changed, and ADR-145 + Keith settle it)
  - Forward impact: Dev sources gear verbatim from the AWN SRD (provenance-stamped), not hand-derived/paraphrased. Item names/flavor remain freely reskinnable (ADR-145 D1), so SideQuest-original names are still fine — but they ride verbatim AWN *mechanics*.

### Dev (implementation)
- **Bespoke items stamped at the GENRE tier (not relocated to world tier)**
  - Spec source: ADR-145 D1/D3 + `context-story-114-8.md` (Scope) + TEA finding "Artifact placement"
  - Spec text: "bespoke is a world-tier privilege, not a baseline shortcut … a bespoke item in a genre baseline is a hard error" (ADR-145 D3/D4)
  - Implementation: the 7 non-AWN wasteland items (5 chargen artifacts + `ancient_artifact` + 6 survival consumables/tools) are stamped `provenance.mode=bespoke` and left in the genre `inventory.yaml`, rather than moved to both worlds' catalogs.
  - Rationale: relocating them across `seaboard_of_saints` + `flickering_reach` and rewiring the chargen `item_hint`/`starting_equipment` refs is a much larger change than this story's defect scope (AWN re-stat + scrap_armor AC). The genre-tier-bespoke "hard error" is NOT enforced by the loader today (the pack loads + all tests pass), so this is a documented holding state, mirroring ADR-145 D5's "Fate packs keep bespoke records until their migration" pattern.
  - Severity: minor
  - Forward impact: a future story (or a 114-x follow-on) should relocate genre-tier bespoke items to the world tier once/if the loader enforces the D3 rule. Flagged in Delivery Findings for Keith.

### Reviewer (audit)
- **TEA "verbatim AWN sourcing, not derive"** → ✓ ACCEPTED by Reviewer: sound. ADR-145 D4 (the dependency 114-1's design output) explicitly supersedes the audit's derive-only read; Keith's 2026-06-15 direction confirms. The `ItemProvenance` validator structurally enforces verbatim⇒wn-free, so verbatim is the correct contract. Security subagent confirmed all 5 verbatim items carry `license: wn-free`.
- **Dev "bespoke items stamped at the GENRE tier (not relocated to world)"** → ✓ ACCEPTED by Reviewer: sound holding state. The genre-tier-bespoke "hard error" is not loader-enforced today (pack loads + all tests green), the 12 items are genuinely non-AWN wasteland flavor, and the deferral mirrors ADR-145 D5's "keep bespoke records until migration" pattern. Relocation correctly deferred to a follow-on with a Delivery Finding. Not a blocker.
- **Dev verbatim mechanical re-stat (dice/cost/encumbrance bound to AWN)** → ✓ ACCEPTED (covered by the TEA verbatim deviation): pipe_wrench 1d6→1d4 (AWN Club) and crossbow_salvage 1d8→1d6 (AWN Primitive Bow) are correct verbatim binds, not regressions — "Bind the Ruleset, Don't Balance It." Cross-checked against the AWN SRD (`/tmp/awn_full.txt`): Scrap Mail AC 15, Spear/Club/Bow/Shotgun trauma dice all match. Combat-dispatch + calibration regression suite stayed green.
- No undocumented deviations found.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED confirmed — 7 fail / 4 pass (guards), 0 skip, 0 error (run against the real pack with `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL` set).

**Test Files:**
- `tests/genre/test_114_8_mutant_wasteland_awn_inventory.py` — content-assertion: every genre-tier item is provenance-stamped; catalog is AWN-verbatim-sourced; every non-bespoke weapon carries Trauma Die/Rating; every non-bespoke armor declares `armor_class`; `scrap_armor` reproduces AWN Scrap Mail (AC 15) verbatim.
- `tests/server/test_114_8_scrap_armor_ac_wiring.py` — behavior + OTEL: equipping `scrap_armor` through the real `equip_starting_armor` seam derives `core.armor_class = 15` and fires `chargen.armor_equipped` (not the `chargen.armor_unresolved` gap span).
- `tests/server/test_114_8_power_glove_nondroppable.py` — regression guard: `power_glove` survives the non-droppable genre↔world merge into `seaboard_of_saints` (passes today — locks 114-2 + 114-11).

**Tests Written:** 11 tests. RED drivers (must fail until Dev implements): provenance-on-all-items, catalog-is-AWN-sourced, weapon-trauma-fields, armor-has-armor_class, scrap_armor-is-Scrap-Mail-AC15, scrap_armor-AC-derives-15, scrap_armor-fires-equipped-span.

**RED evidence (testing-runner, RUN_ID 114-8-tea-red):**
- 17/17 catalog items unstamped (no provenance) → provenance + AWN-sourced tests FAIL.
- 0 weapons carry `trauma_die` → trauma test FAILS.
- `scrap_armor.armor_class is None` → armor + Scrap-Mail tests FAIL; equipping it logs `chargen.armor_unresolved reason=catalog_armor_class_missing` and leaves AC 10 → both wiring tests FAIL for the right reason.
- `power_glove` present in resolved seaboard catalog → both guards PASS.

### Rule Coverage

Mapped to the project rubric (SOUL.md + sidequest-server/CLAUDE.md — the load-bearing rules for this content+server story):

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (armor with no AC must fail loud, not silently AC 10) | `test_scrap_armor_fires_equipped_span_not_unresolved` (RED proves the loud `chargen.armor_unresolved` gap span currently fires) | failing |
| Verify Wiring, Not Just Existence (not just YAML presence) | `test_equipping_scrap_armor_derives_awn_ac_15` drives the real `equip_starting_armor` derivation | failing |
| Every Test Suite Needs a Wiring Test | File 2 (chargen AC derivation) + File 3 (resolver merge) exercise production paths | failing / passing |
| OTEL Observability (GM-panel lie-detector) | `test_scrap_armor_fires_equipped_span_not_unresolved` asserts `chargen.armor_equipped` attrs | failing |
| No Source-Text Wiring Tests | behavior + OTEL span assertions used; zero `read_text()`/source-grep tests | n/a (compliant) |
| Bind the Ruleset, Don't Balance It (verbatim AWN mechanics, no hand-tuning) | `test_catalog_is_actually_awn_sourced`, `test_scrap_armor_is_the_awn_scrap_mail_reskin`, `test_verbatim_items_are_awn_wn_free_with_srd_ref` | failing / guard |
| Tests must not point at live content (anti-pattern) | N/A — these ARE content-compliance tests; the real pack is the subject under test (the legit "production wiring test" case, matching `test_mutant_wasteland_awn_binding.py`) | compliant |

**Rules checked:** 6 of 6 applicable project rules have test coverage.
**Self-check (vacuous assertions):** 1 noted — `test_verbatim_items_are_awn_wn_free_with_srd_ref` passes vacuously today (no verbatim items yet) but is an intentional correctness contract that activates once Dev stamps items; it is not a bad-vacuous (`assert True`/always-None) test. No `let _ =` / `assert True` / always-None assertions present. Kept.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Read the Delivery Findings first — especially the **Model A vs B** baseline-shape decision (recommend Model B), the **already-fixed power_glove** (don't redo it), and the **verbatim-not-derive** correction. AWN source data is at `/tmp/awn_full.txt` (armor ~line 4317, ranged weapons ~line 4406); the canonical source PDF is in the Sine Nomine Publishing dir. Honor D4a (no implied endorsement) + D4b (SRD only, never the commercial book) in every provenance string and comment.

## Dev Assessment

**Implementation Complete:** Yes (Model B — genre-tier verbatim reskin, per TEA recommendation)

**Files Changed:**
- `sidequest-content/genre_packs/mutant_wasteland/inventory.yaml` — re-sourced the genre catalog: 4 standard weapons + scrap_armor now carry verbatim AWN SRD mechanics + `provenance{mode=verbatim,srd=awn,license=wn-free,srd_ref}`; the 7 non-AWN wasteland items stamped `mode=bespoke`. AWN mappings: sharpened_rebar=Spear (1d6, Trauma 1d8×3, Shock 2/AC13), pipe_wrench=Club (1d4, Trauma 1d6×2, Shock 1/AC18), crossbow_salvage=Primitive Bow (1d6, Trauma 1d8×3, mag 1, range 20/100), sawed_off=Shotgun (3d4, Trauma 1d10×3, mag 2, range 10/30), scrap_armor=Scrap Mail (**armor_class 15**). Costs/encumbrance/TL bound to SRD.
- `sidequest-server/` — **no production code change**. The schema (`provenance`/`armor_class`/trauma fields) + the `equip_starting_armor` AC-derivation wiring already existed (114-3 + 106-1 + 114-11). The server-repo deliverable is the test suite (3 files committed in RED, `76bc5ece`). "Wire up what exists," not reinvent.

**Tests:** 11/11 new tests GREEN. Regression sweep clean — 66/66 targeted (mutant_wasteland binding + combat dispatch + inventory_resolve + union_merge + equip_starting_armor) and 152/152 broad (`-k "mutant_wasteland or awn or calibration or COMBAT_PACKS or dual_dial"`), 0 failures (8 pre-existing skips: absent AWN extraction tool + COMBAT_PACKS metadata). The scrap_armor fix verified end-to-end: equipping it derives `core.armor_class=15` and fires `chargen.armor_equipped` (the `chargen.armor_unresolved` gap span no longer fires).

**Branches (pushed, github-flow → develop; SM opens PRs at finish):**
- content: `feature/114-8-mutant-wasteland-awn-inventory-restat` @ `c266bc5`
- server: `feature/114-8-mutant-wasteland-awn-inventory-restat` @ `76bc5ece`

**Note for verify/review:** regression sweep was scoped to the content change's blast radius (single-pack catalog); the full server suite runs at the verify/check gate. Reviewer: see the 4 Dev Delivery Findings — genre-tier-bespoke holding state (deviation logged), no AWN extraction tool, value-bound-to-AWN-cost vs Salvage economy, and range_band-on-melee omission.

**Handoff:** To verify phase (TEA — simplify + quality-pass), then Reviewer.

## Subagent Results

Enabled subagents (per `workflow.reviewer_subagents`): preflight, silent_failure_hunter, security. The other six are disabled via settings — Reviewer self-assessed those domains (see Reviewer Assessment tags).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (ruff format reflow, LOW) | confirmed 1 (fixed by reviewer reflow commit 2ffd9daa); tests 11/11 green, ruff check clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 med, 2 low) | dismissed 1 (in-place mutation proven), verified 1 (narrow catch), deferred 1 (trauma_rating<=1, LOW non-blocking) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed [TYPE]) |
| 7 | reviewer-security | Yes | clean | 0 | N/A — D4a/D4b/D4 all compliant, no secrets/unsafe-deser |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (self-assessed [RULE] — see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled per settings)
**Total findings:** 1 confirmed-and-fixed (format reflow), 2 dismissed/verified, 2 deferred LOW (non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. The one actionable finding (ruff-format reflow on the AC-wiring test, LOW) was fixed in-place by the reviewer (commit `2ffd9daa`, pure whitespace, 11/11 re-verified green). Two LOW improvements deferred as non-blocking. The change is content-only (one genre `inventory.yaml`) plus the new test suite; no production code changed.

**Observations (tagged by domain):**
1. `[SEC] [VERIFIED]` ADR-145 D4a/D4b/D4 compliance — `inventory.yaml` header (lines 12-16) is a *disclaimer* that negates Sine Nomine/Kevin Crawford endorsement (the highest-stakes check); all 5 `srd_ref` strings cite "AWN SRD Equipment —", never a commercial book (D4b); all 5 `mode: verbatim` items carry `license: wn-free` and all 12 `mode: bespoke` carry no false srd/license (D4). Security subagent: 17 items checked, 0 violations.
2. `[SILENT] [VERIFIED]` `equip_starting_armor` mutates `core.armor_class` in place — `sidequest/server/dispatch/chargen_loadout.py:409` `core.armor_class = ac_after`; the existing `test_106_1_equip_starting_armor.py:172` asserts the same post-condition and passes. The silent-failure-hunter's medium "could pass vacuously" concern is **dismissed**: the RED→GREEN transition (AC 10→15, unresolved→equipped span) is only possible because the function mutates and the assertion reads the mutated value.
3. `[SILENT] [VERIFIED]` No Silent Fallbacks — `scrap_armor` now carries `armor_class: 15` (no silent AC-10 fallback; the `chargen.armor_unresolved` gap span no longer fires); the two ranged weapons correctly omit `shock` (default 0, no ceiling needed); melee weapons set `shock`+`shock_ac` together (`DamageSpec._shock_requires_ceiling` would reject otherwise). The `PackNotFound` skip catches a narrow `FileNotFoundError` subclass — any loader `ValidationError` propagates as a real failure.
4. `[RULE] [VERIFIED]` "Bind the Ruleset, Don't Balance It" (SOUL.md) — gear mechanics are AWN SRD verbatim, cross-checked against `/tmp/awn_full.txt`: Scrap Mail AC 15 (p.77 / line 4321), Spear 1d6 Shock2/AC13 Trauma 1d8×3 (line 4460), Club 1d4 Shock1/AC18 Trauma 1d6×2 (line 4459), Primitive Bow 1d6 Trauma 1d8×3 (line 4409), Shotgun 3d4 Trauma 1d10×3 mag2 (line 4414). pipe_wrench 1d6→1d4 and crossbow 1d8→1d6 are correct verbatim binds (not nerfs to "balance"), exactly the doctrine.
5. `[TEST] [LOW]` `test_every_combat_weapon_carries_awn_trauma_fields` uses `trauma_rating <= 1` as the failure predicate — slightly over-strict (AWN has x1 multipliers); passes today (all catalog weapons x2+), but a future x1 catalog weapon would falsely fail. Non-blocking; logged as a Delivery Finding.
6. `[SIMPLE] [VERIFIED]` Content is minimal and consistent — verbatim items carry only the SRD envelope + provenance; bespoke items carry only `mode: bespoke`. No over-engineering, no dead fields. The one format reflow was the only simplicity nit and is fixed.
7. `[DOC] [VERIFIED]` Comments are accurate — the file header documents the AWN sourcing + the bespoke-deferral; per-item comments name the exact AWN source row. The stale "REPLACES wholesale" comment lives in the *world* `seaboard_of_saints/inventory.yaml` (NOT touched by this diff; already flagged by TEA) — no new stale comments introduced here.
8. `[TYPE] [VERIFIED]` Types are sound — the content is validated by the strict (`extra="forbid"`) pydantic `CatalogItem`/`ItemProvenance`/`DamageSpec`; the verbatim⇒wn-free invariant and shock⇒shock_ac invariant are enforced structurally at load. No new types; no stringly-typed surface introduced.
9. `[EDGE] [VERIFIED]` Edge coverage — the bespoke-exemption branch in the tests is exercised (power_glove is a bespoke weapon with no trauma → correctly exempt); the non-droppable merge edge (genre-only id surviving a world that ships its own inventory) is covered by the power_glove guard; armor-with-no-AC (the pre-fix gap) is the RED state the wiring test pinned.

**Rule Compliance (Python lang-review checklist — enumerated, since rule_checker is disabled):**
- #1 Silent exceptions: PASS — only `except PackNotFound` (narrow) → `pytest.skip`; no bare/broad except.
- #2 Mutable defaults: PASS — no function in the diff uses a mutable default.
- #3 Type annotations at boundaries: PASS — these are test helpers (exempt); `_scrap_armor_item() -> dict` is annotated.
- #4 Logging: N/A — no logging added (tests + YAML).
- #5 Path handling: PASS — no path manipulation; `find_pack_path` is the project helper.
- #6 Test quality: PASS — no `assert True`, no assertion-free tests; skips are env-gated with a reason; `otel_capture` fixture confirmed in `tests/server/conftest.py`. One over-strict predicate noted (#5 observation, LOW).
- #7 Resource leaks: N/A — no file/socket/lock handles opened.
- #8 Unsafe deserialization: PASS — uses `load_genre_pack` (safe loader); no `yaml.load`/`eval`/`exec`.
- #9 Async: N/A — no async code.
- #10 Import hygiene: PASS — explicit imports, no star imports; in-function imports of `Character`/`equip_starting_armor` are the established lazy-import test pattern.
- #11 Input validation: N/A — no external input; content validated by pydantic at load.
- #12 Dependency hygiene: N/A — no dependency changes.
- #13 Fix-introduced regressions: PASS — regression sweep (66 targeted + 152 broad) stayed green.

**Data flow traced:** player equips `scrap_armor` → `equip_starting_armor` (`chargen_loadout.py`) looks the item up in the resolved catalog → reads `catalog_item.armor_class` (15, sourced from the AWN SRD content, not a constant) → sets `core.armor_class = 15` → WN/AWN attack rolls target AC 15 → emits `chargen.armor_equipped` OTEL span (GM-panel lie-detector). Safe: the AC value originates in provenance-stamped content and is verified end-to-end by `test_equipping_scrap_armor_derives_awn_ac_15` + the OTEL-span test.

### Devil's Advocate
Argue the change is broken. **Licensing landmine:** this content reproduces a third party's equipment statistics; if the "verbatim" framing or a stray comment implied Sine Nomine endorsement, that is the project's single most damaging defect (ADR-145 D4a, "treat an endorsement-implying string as a hard defect"). I hunted for it specifically — every comment, every `srd_ref`, the header, the test docstrings — and the only Sine Nomine/Crawford mention is the *disclaimer that negates* endorsement. Clean, but it is the thing most likely to rot later: a future author copying this file as a template could weaken the disclaimer. **Balance creep:** a skeptic says binding AWN dropped pipe_wrench from 1d6 to 1d4 — a "nerf" players will notice. But that is precisely the doctrine (bind, don't balance); the prior 1d6 was the unsanctioned hand-tune, and the combat/calibration suite stayed green, so no balance assumption silently broke. **Vacuous green:** the most insidious failure mode for a test that flips RED→GREEN via content is that the assertion never actually executes the asserted path. I verified `equip_starting_armor` mutates in place (line 409) and that the existing 106-1 test asserts the identical post-condition and passes — so the GREEN is real, not a no-op. **Economy mismatch:** binding `value` to AWN credit costs (Shotgun 100) against a Salvage economy where a Scavenger starts with 8 could make starting purchasing nonsensical — but starting_gold is unchanged and world-owned (ADR-145 D3), and AWN's economy is internally balanced; Dev flagged it for Keith. **The genuinely soft spot:** the 12 bespoke items sit at the genre tier, which ADR-145 D3 calls a "hard error." Today the loader does not enforce it, so nothing breaks — but if a later story turns on that enforcement, this pack will fail to load until the artifacts are relocated. That is a real future tripwire, correctly logged as a deferred Delivery Finding rather than hidden. None of these rises to Critical/High for *this* change; the licensing check (the one that could truly hurt) is clean.

**Verdict:** APPROVED — content faithfully binds the AWN SRD with machine-readable provenance, the named `scrap_armor` mitigation defect is fixed and wired end-to-end (with OTEL proof), no regressions, and the licensing guardrails (D4a/D4b/D4) hold. Two LOW improvements deferred; one format reflow fixed in-review.

**Handoff:** To SM (Vizzini) for finish-story.