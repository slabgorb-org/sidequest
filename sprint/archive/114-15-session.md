---
story_id: "114-15"
jira_key: "none"
epic: "none"
workflow: "tdd"
---
# Story 114-15: space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home

## Story Details
- **ID:** 114-15
- **Jira Key:** none
- **Workflow:** tdd
- **Repos:** content,server
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T01:19:13Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T23:38:33Z | 2026-06-15T23:40:46Z | 2m 13s |
| red | 2026-06-15T23:40:46Z | 2026-06-15T23:53:47Z | 13m 1s |
| green | 2026-06-15T23:53:47Z | 2026-06-16T01:10:53Z | 1h 17m |
| review | 2026-06-16T01:10:53Z | 2026-06-16T01:19:13Z | 8m 20s |
| finish | 2026-06-16T01:19:13Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): the dogfight weapon_lookup is an inline nested comprehension at `sidequest/server/narration_apply.py:5385` resolving against `item_catalog`. Affects `narration_apply.py` (extract into `build_dogfight_weapon_lookup` and repoint to `ship_weapons`). *Found by TEA during test design.*
- **Gap** (non-blocking): the comment at `sidequest/server/narration_apply.py:5372-5374` ("genre tier is None … lookup hits the world-tier item_catalog") goes STALE after this story — the genre tier now ships `ship_weapons` and the lookup must hit it. Affects `narration_apply.py` (update the comment when repointing the lambda). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the session-handler-layer dogfight tests (`tests/server/test_dogfight_player_throw_roundtrip.py`, `tests/integration/test_dogfight_swn_production_wiring.py`) die on a PRE-EXISTING LLM-hermeticity guard (`build_async_anthropic()` refusal at `websocket_session_handler.py:1197`, the unstubbed objective-classifier pass) BEFORE reaching the dogfight weapon lookup, so they do not exercise the new genre-tier resolution at that layer. The apply-level `tests/server/test_dogfight_shot_wiring.py` does exercise it and passes (3/3). Affects those tests (stub `build_unseeded_objective_classifier_llm`); not introduced by this story. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): on the world-merge path, when `pack.inventory is None` (a future pack that ships a world `inventory.yaml` but no genre baseline), `resolve_inventory` carries `ship_weapons=[]` and the dogfight then fails with `_resolve_weapon`'s generic "weapon id … not found / has no damage spec" rather than naming the missing genre inventory as root cause. Affects `sidequest/server/dispatch/inventory_resolve.py:214` (a loud guard naming the world slug + missing-genre-inventory would beat the misleading downstream message). Loud-fails today (not silent) and follows the resolver's existing `pack.inventory is None → []` convention; no current pack hits it. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `ship_weapons` is genre-tier-only in v1, but `InventoryConfig` is the shared genre/world model, so a world author (e.g. Jade's homebrew) who writes `ship_weapons:` in a world `inventory.yaml` has it silently overwritten by the genre collection on the merge path (no error, no span). Affects `sidequest/server/dispatch/inventory_resolve.py:215` (a v1.1 either merges world ship_weapons or loud-fails on a world-authored one). Documented as a v1 limitation in the model comment; no current content authors it. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No deviations from spec during setup.

### TEA (test design)
- **Extracted a named `build_dogfight_weapon_lookup` helper (test prescribes the seam)**
  - Spec source: context-story-114-15.md, Technical Approach step 3 + AC2
  - Spec text: "Dogfight `weapon_lookup` … resolves player_weapon/opponent_weapon ids against `ship_weapons` ONLY — reuse existing fail-loud ValueError on missing id."
  - Implementation: tests require the inline narration_apply lambda (narration_apply.py:5385) to be extracted into `sidequest.game.dogfight_shot.build_dogfight_weapon_lookup(resolved_inventory) -> Callable[[str], CatalogItem | None]`, resolving from `ship_weapons` only and returning None on miss.
  - Rationale: a named seam is unit-testable and houses the AC5 span; satisfies the server "No Source-Text Wiring Tests" rule (drive behavior + assert a span, never grep source).
  - Severity: minor
  - Forward impact: none beyond this story — the helper is dogfight-internal; sibling 114-13 (road_warrior personal-weapon guard) is unaffected.
- **Specified a new typed span `dogfight.weapon_resolved` (test prescribes shape)**
  - Spec source: context-story-114-15.md, AC5
  - Spec text: "OTEL span/event for dogfight weapon resolution carries source=ship_weapons + weapon id + armor_piercing value."
  - Implementation: tests require a NEW typed span `SPAN_DOGFIGHT_WEAPON_RESOLVED = "dogfight.weapon_resolved"` in `sidequest/telemetry/spans/dogfight.py` (+ a `SPAN_ROUTES` entry, component="dogfight", event_type="state_transition", and a `dogfight_weapon_resolved_span(*, source, weapon_id, armor_piercing, dice)` context manager), emitted by `build_dogfight_weapon_lookup` on each successful resolution.
  - Rationale: consistent with the existing dogfight span family (shot_attempted/shot_damage); routed (not flat-only) so the GM panel renders it.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Mirrored the ship-weapon move into the `swn_test_pack` fixture (new genre-tier `inventory.yaml`) and de-duplicated the world fixture**
  - Spec source: context-story-114-15.md, Technical Approach (CONTENT steps 6–8 enumerate only the live space_opera pack)
  - Spec text: "Add `ship_weapons:` block to genre_packs/space_opera/inventory.yaml … Delete triplicated `multifocal_laser` from … worlds/{aureate_span,coyote_star,perseus_cloud}/inventory.yaml"
  - Implementation: also created `tests/fixtures/packs/swn_test_pack/inventory.yaml` (genre-tier `ship_weapons` with multifocal_laser) and removed the laser from `tests/fixtures/packs/swn_test_pack/worlds/test_world/inventory.yaml`, so the fixture mirrors the production resolution path the dogfight server/integration tests drive.
  - Rationale: the dogfight now resolves the weapon from genre-tier `ship_weapons` only; leaving it world-tier in the fixture would break the fixture-driven dogfight wiring tests. The fixture must track the production shape.
  - Severity: minor
  - Forward impact: none — fixture-only; no production behavior depends on it.
- **Retargeted two pre-existing 114-7 regression tests to the new genre-tier home**
  - Spec source: context-story-114-15.md, Title ("114-7 review follow-up … supersedes the 114-7 world-tier triplication")
  - Spec text: the story title states it supersedes the 114-7 per-world copies.
  - Implementation: in `tests/genre/test_114_7_space_opera_swn_inventory.py`, `test_confrontation_weapon_ids_resolve_in_every_world` and `test_multifocal_laser_stays_a_ship_weapon_with_armor_piercing` now resolve via `build_dogfight_weapon_lookup` and assert the laser is ABSENT from the personal item_catalog (was: asserted present in the world item_catalog). Same invariant (AP 20 resolves per world), new home.
  - Rationale: those tests pinned the now-superseded world-triplication; leaving them unchanged would red the suite on correct behavior.
  - Severity: minor
  - Forward impact: none — they now pin the 114-15 invariant.
- **Corrected three stale location-describing comments my change falsified (doc-only)**
  - Spec source: CLAUDE.md "No Source-Text Wiring Tests" + reviewer comment-hygiene
  - Spec text: comments must not mislead about where a thing lives.
  - Implementation: updated docstrings/comments in `tests/server/test_dogfight_shot_wiring.py`, `tests/_helpers/fixture_packs.py`, and `tests/fixtures/packs/swn_test_pack/worlds/test_world/world.yaml` that described `multifocal_laser` as "world-tier" — now genre-tier `ship_weapons`. (Left the separate, pre-existing "REPLACE path" staleness alone — not caused by this story.)
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
All five logged deviations (2 TEA, 3 Dev) reviewed; none reversed:
- **TEA — `build_dogfight_weapon_lookup` named seam** → ✓ ACCEPTED: the only way to unit-test resolution + house the AC5 span; satisfies the server "No Source-Text Wiring Tests" rule; production consumer wired at narration_apply.py:5388.
- **TEA — new `dogfight.weapon_resolved` span** → ✓ ACCEPTED: consistent with the dogfight span family, routed (not flat-only), extractor projects all panel fields; verified registered+routed by test.
- **Dev — mirror the move into the swn_test_pack fixture** → ✓ ACCEPTED: the fixture MUST track the production resolution shape or the apply-level dogfight wiring test breaks; fixture-only, no production impact.
- **Dev — retarget two 114-7 regression tests** → ✓ ACCEPTED: those tests pinned the now-superseded world-triplication; the retarget preserves the same invariant (AP 20 resolves per world) against the new genre-tier home — correct per the story title (supersedes 114-7).
- **Dev — correct three stale "world-tier" comments** → ✓ ACCEPTED: the move falsified them; doc-only and accurate now; confirmed no behavioral change.

No UNDOCUMENTED deviations found: the content move is byte-identical (no stat drift on damage/AP/value/weight), and the diff scope matches the spec plus the logged fixture/test consequences.

## Branch Strategy

**Orchestrator:** trunk-based (branching skipped — work happens on main)
**content & server:** gitflow (feat/114-15-dogfight-ship-weapon-home)

## Sm Assessment

**Setup complete — ready for RED (TEA).**

- **Story:** 114-15 (5pts, p3, epic 114 — SRD-sourced inventory). Repos: content,server. Workflow: tdd (phased). Jira: none (personal project — Jira correctly skipped).
- **Design status: DECIDED, not open.** The Architect (The Man in Black) completed the design and Keith approved it before setup. The story YAML's stated "preferred" (bind a VERBATIM SWN starship weapon) is **REJECTED** — ship-scale 3d4 vs the native dogfight's personal-scale hp:8 would either silently rebalance the duel or falsify provenance (SOUL "Bind the Ruleset, Don't Balance It"). TEA must NOT re-open the verbatim option in RED.
- **Chosen approach (in context):** option 2b — a genre-tier `ship_weapons: list[CatalogItem]` collection on `InventoryConfig`, carried through `resolve_inventory` un-merged, resolved by the dogfight `weapon_lookup` / `dogfight_shot._resolve_weapon` only (fail-loud on miss). Content: hoist the one `multifocal_laser` to genre `ship_weapons:`, delete the 3 world copies, repoint the inventory.yaml:89-93 comment.
- **ACs:** AC1–AC5 written in context-story-114-15.md. **AC3 is the load-bearing one** — a space_opera world that ships NO `multifocal_laser` entry must still resolve the dogfight weapon with `armor_piercing == 20` from the genre source. That's the only test that actually proves de-duplication; TEA should write it first.
- **Watch-outs for TEA/Dev:** (1) `armor_piercing: 20` is load-bearing (dogfight applies `effective_armor_after_ap(armor=5, ap=20)`) — assert it survives, not just that the id resolves. (2) provenance.mode must be `bespoke` (⇒ srd:None); credit the SWN lineage in a YAML comment, not the struct. (3) `_validate_genre_baseline_no_bespoke` stays unchanged (scans item_catalog only) — ship_weapons is exempt by design. (4) OTEL span on weapon resolution per AC5. (5) Lighter fallback (2a inline cdef weapon spec) allowed only if 2b proves heavier than expected.
- **Merge gate:** clear (no open non-draft PRs on server/content).

**Decision:** Hand off to TEA (Fezzik) for the RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New behavior (genre-tier `ship_weapons` collection + dogfight resolution + OTEL span) — a real feature slice across model, resolver, dogfight, and telemetry. Not a chore.

**Test Files:**
- `sidequest-server/tests/server/dispatch/test_ship_weapons_resolve.py` — synthetic mechanism: `InventoryConfig.ship_weapons` field, `resolve_inventory` threading the genre collection through the **world-merge path** (the load-bearing AC3 guard), and the D3-validator exemption (AC1 substrate, AC3, AC4).
- `sidequest-server/tests/game/test_dogfight_weapon_lookup.py` — `build_dogfight_weapon_lookup`: resolves from `ship_weapons` ONLY, returns None on miss + on item_catalog-only ids (exclusivity), tolerates None inventory, emits the OTEL span (AC2, AC4, AC5).
- `sidequest-server/tests/telemetry/spans/test_dogfight_weapon_resolved_span.py` — the `dogfight.weapon_resolved` typed span: routed under component=dogfight, carries source/weapon_id/armor_piercing, extractor projects panel fields (AC5).
- `sidequest-server/tests/genre/test_space_opera_ship_weapons.py` — **the wiring test**: loads the real space_opera pack and proves de-duplication end-to-end (weapon lives once in genre `ship_weapons`, zero copies in the 3 worlds, every world resolves AP 20 from the single source) (AC1, AC2, AC3, AC4).

**Tests Written:** 26 test cases covering all 5 ACs.
**Status:** RED (verified) — 7 failed + 3 collection errors, every one for the expected feature-missing reason (no `ship_weapons` field / no `build_dogfight_weapon_lookup` / no `SPAN_DOGFIGHT_WEAPON_RESOLVED`). No test bugs. Commit `a77973b7` on `feat/114-15-dogfight-ship-weapon-home` (server).

### AC → Test Coverage

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 (defined once at genre `ship_weapons`, zero world copies) | `test_multifocal_laser_lives_once_in_genre_ship_weapons`, `test_multifocal_laser_not_in_genre_item_catalog`, `test_world_item_catalog_has_no_ship_weapon_copy[×3]`, `test_worlds_keep_their_distinct_gear` | RED |
| AC2 (dogfight resolves AP 20, all 3 worlds) | `test_resolves_ship_weapon_with_armor_piercing_intact`, `test_dogfight_weapon_resolves_with_ap_from_genre[×3]`, `test_dogfight_cdef_weapon_ids_resolve` | RED |
| AC3 (de-dup proof — world with no copy still resolves) | `test_genre_ship_weapons_survive_world_merge_path`, `test_dogfight_weapon_resolves_with_ap_from_genre[×3]` | RED |
| AC4 (load OK; D3 still fails loud; unknown id fails loud) | `test_bespoke_ship_weapon_is_exempt_from_d3`, `test_bespoke_item_catalog_item_still_fails_loud`, `test_unknown_id_returns_none`, real-pack fixture load | RED |
| AC5 (OTEL span: source/id/AP) | `test_emits_weapon_resolved_span_on_hit`, `test_no_span_on_miss`, `test_weapon_resolved_span_is_routed`, `test_weapon_resolved_span_carries_source_id_and_ap`, `test_weapon_resolved_route_extract_projects_panel_fields` | RED |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| SOUL **No Silent Fallbacks** | `test_unknown_id_returns_none`, `test_does_not_resolve_from_personal_item_catalog`, `test_no_span_on_miss` | RED |
| CLAUDE.md **OTEL Observability** (subsystem decision emits a span) | `test_emits_weapon_resolved_span_on_hit`, span routing + attribute tests | RED |
| CLAUDE.md **No Source-Text Wiring Tests** | wiring proven via OTEL span + real-pack behavior (`test_space_opera_ship_weapons.py`); zero `read_text()`/source-grep | pass (design) |
| python lang-review #6 **test-quality** | all tests assert specific values; 1 vacuous no-raise test found and hardened with provenance/precondition assertions | pass (self-check) |
| python lang-review #3 **type-annotations** | typed helpers + fixtures across all four files | pass |
| python lang-review #2/#4/#5/#7–#12 | N/A — pure model/lookup/telemetry tests; no I/O, async, untrusted input, deps, or path handling | n/a |

**Rules checked:** all 13 lang-review checks reviewed; 2 applicable + 3 project rules have direct test coverage, remainder N/A to this change class.
**Self-check:** 1 vacuous assertion found (`test_bespoke_ship_weapon_is_exempt_from_d3` was a bare no-raise call) and fixed.

**Implementation pointers for Dev (Inigo):**
- `InventoryConfig.ship_weapons: list[CatalogItem] = Field(default_factory=list)` (genre-tier only).
- `resolve_inventory`: in the **merge path** (`world_inv.model_copy(...)`), also set `ship_weapons` from `pack.inventory.ship_weapons` — the world copy would otherwise drop it (this is the AC3 trap).
- Extract `build_dogfight_weapon_lookup(resolved_inventory)` into `sidequest/game/dogfight_shot.py`; repoint the inline lambda at `narration_apply.py:5385` to use it and update the stale comment at `narration_apply.py:5372-5374`.
- Add `SPAN_DOGFIGHT_WEAPON_RESOLVED` + `SPAN_ROUTES` entry + `dogfight_weapon_resolved_span` to `sidequest/telemetry/spans/dogfight.py`; emit from the lookup on each hit.
- Content (sidequest-content branch `feat/114-15-dogfight-ship-weapon-home`): add `ship_weapons:` block to genre `space_opera/inventory.yaml` (multifocal_laser, 1d4/AP20, provenance bespoke); delete the laser from the 3 worlds; repoint the comment at `inventory.yaml:89-93`.

**Handoff:** To Dev (Inigo Montoya) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**

_server (`feat/114-15-dogfight-ship-weapon-home`, commit 485ed91e):_
- `sidequest/genre/models/inventory.py` — `InventoryConfig.ship_weapons: list[CatalogItem] = Field(default_factory=list)` (genre-tier-only, off item_catalog).
- `sidequest/server/dispatch/inventory_resolve.py` — `resolve_inventory` carries genre `ship_weapons` through the world-merge `model_copy(update=…)` so a world that ships its own inventory.yaml still inherits the dogfight weapon (the AC3 trap).
- `sidequest/game/dogfight_shot.py` — new `build_dogfight_weapon_lookup(resolved_inventory)`: resolves from `ship_weapons` ONLY, `None` on miss (fail-loud preserved in `_resolve_weapon`), emits `dogfight.weapon_resolved` on each hit.
- `sidequest/server/narration_apply.py` — dogfight branch uses `build_dogfight_weapon_lookup`; stale `:5372-5374` comment corrected (resolves TEA's noted Gap).
- `sidequest/telemetry/spans/dogfight.py` — `SPAN_DOGFIGHT_WEAPON_RESOLVED` + `SPAN_ROUTES` entry (component=dogfight, state_transition) + `dogfight_weapon_resolved_span` context manager.
- Tests/fixtures: new `tests/fixtures/packs/swn_test_pack/inventory.yaml`; `worlds/test_world/inventory.yaml` + `world.yaml`; `tests/_helpers/fixture_packs.py`; `tests/server/test_dogfight_shot_wiring.py`; `tests/genre/test_114_7_space_opera_swn_inventory.py` (see Design Deviations → Dev).

_content (`feat/114-15-dogfight-ship-weapon-home`, commit dc1662e):_
- `genre_packs/space_opera/inventory.yaml` — new genre-tier `ship_weapons:` block (multifocal_laser, 1d4/AP20, provenance bespoke); explanatory comment repointed.
- `genre_packs/space_opera/worlds/{aureate_span,coyote_star,perseus_cloud}/inventory.yaml` — triplicated multifocal_laser deleted (de-duplicated; each world keeps its 2 distinct items).

**Tests:** 43/43 passing GREEN — the 26 story cases (40 with parametrization) across the four story files + the 3 `test_dogfight_shot_wiring` apply-level cases. AC1–AC5 all covered (the real-pack wiring test `test_space_opera_ship_weapons.py` proves load-success + de-dup end-to-end). Verified the new `swn_test_pack` genre fixture resolves the weapon (AP 20) through the production `resolve_inventory → build_dogfight_weapon_lookup` path.

**Regression check:** Full server suite run twice (with/without the content env). 258–269 PRE-EXISTING failures, dominated by an LLM-hermeticity guard (`build_async_anthropic()` refusal, 522 line-mentions) plus the known EH/HM/CAC loader baselines. Read the traceback of every failure inside this change's blast radius (the only one, `test_dogfight_player_throw_roundtrip`, dies upstream at the objective-classifier LLM construction, never reaching the weapon lookup). **Zero regressions attributable to this story.** Lint + format clean on all changed files.

**Branch:** feat/114-15-dogfight-ship-weapon-home (server + content, both pushed to origin)

**Handoff:** To next phase (review).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (43/43 GREEN, lint+format PASS, both trees clean, branches on origin) | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | disabled → reviewed manually | Disabled via settings; edges enumerated in assessment [EDGE] |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium-confidence) | confirmed 1 (downgraded to non-blocking Improvement), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | clean | disabled → reviewed manually | Disabled via settings; test quality assessed manually [TEST] |
| 5 | reviewer-comment-analyzer | Yes | clean | disabled → reviewed manually | Disabled via settings; comments assessed manually [DOC] |
| 6 | reviewer-type-design | Yes | clean | disabled → reviewed manually | Disabled via settings; type design assessed manually [TYPE] |
| 7 | reviewer-security | Yes | clean | 0 | N/A |
| 8 | reviewer-simplifier | Yes | clean | disabled → reviewed manually | Disabled via settings; no over-engineering found [SIMPLE] |
| 9 | reviewer-rule-checker | Yes | clean | disabled → reviewed manually | Disabled via settings; Rule Compliance done manually [RULE] |

**All received:** Yes (3 enabled returned: preflight clean, security clean, silent-failure-hunter 1 finding; 6 disabled via `workflow.reviewer_subagents`, each reviewed manually)
**Total findings:** 1 confirmed (non-blocking Improvement), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A clean, tightly-scoped slice. The bespoke dogfight ship weapon moves from per-world `item_catalog` triplication into a single genre-tier `ship_weapons` collection; the dogfight resolves from it via a named, span-emitting lookup; the ADR-145 D3 validator exemption is structurally scoped (by omission) and proven by a control test. 43/43 GREEN, ruff check + format clean, both trees clean and pushed. No Critical/High issues.

**Observations:**
- [VERIFIED] D3 exemption scoped by omission — `_validate_genre_baseline_no_bespoke` iterates `inventory.item_catalog` only (loader.py:739), never `ship_weapons`; control test `test_bespoke_item_catalog_item_still_fails_loud` proves a bespoke `item_catalog` item STILL raises `PackError`. Validator is unchanged (not in the diff). Complies with ADR-145 D3.
- [VERIFIED] Production wiring is real, not just unit-tested — `build_dogfight_weapon_lookup` is consumed at `narration_apply.py:5388`, and the apply-level `test_dogfight_shot_wiring.py` (3/3) drives the real dogfight branch against the fixture (NPC frame HP ablates, spans fire). Satisfies "Verify Wiring, Not Just Existence" + "Every Test Suite Needs a Wiring Test."
- [VERIFIED] AC3 carry-through correct — `resolve_inventory` threads genre `ship_weapons` through the world-merge `model_copy` (inventory_resolve.py:215); `test_genre_ship_weapons_survive_world_merge_path` + 3 real-world parametrized cases prove a world that ships its own inventory still resolves AP 20 from the single genre source.
- [SEC] reviewer-security: clean — YAML via `yaml.safe_load` (loader.py:159/192/282/361/…) + pydantic `extra=forbid`; OTEL span carries only authored content values (no PII/tokens/paths); `provenance bespoke+na` cannot be confused for verbatim (the `_verbatim_requires_permitting_license` validator only fires on `mode=verbatim`).
- [SILENT] reviewer-silent-failure-hunter: 1 finding → confirmed as a non-blocking Improvement. When `pack.inventory is None` on the merge path, `ship_weapons=[]` and the failure surfaces as `_resolve_weapon`'s generic "weapon not found" rather than naming the missing genre inventory. It fails LOUD (not silent), follows the resolver's existing `pack.inventory is None → []` convention, and no current pack hits it. Logged as a delivery finding for future hardening; does not block.
- [EDGE] edge-hunter disabled — manual: all branches covered (hit / miss / None-inventory / item_catalog-exclusivity / empty-world-ship_weapons / pure-genre-path each have a test). Two uncovered edges, both non-blocking: (a) a `damage=None` ship weapon emits a `weapon_resolved` span (ap=0) before `_resolve_weapon` rejects it — content always carries damage; (b) a world authoring non-empty `ship_weapons` is silently overwritten by the genre's (v1-documented; logged as a delivery finding).
- [TEST] test-analyzer disabled — manual: assertions are specific (AP==20, source=="ship_weapons", exact id-sets), not vacuous; `test_bespoke_ship_weapon_is_exempt_from_d3` carries precondition assertions so the no-raise is meaningful; the real-pack wiring test skips cleanly when content is absent; `test_worlds_keep_their_distinct_gear` guards over-deletion; mock target patches `spans_module.tracer` (where used). Strong.
- [DOC] comment-analyzer disabled — manual: the three stale "world-tier multifocal_laser" comments (test_dogfight_shot_wiring docstring, fixture_packs helper, world.yaml description) were correctly retargeted to genre-tier; the model/resolver/narration_apply comments are accurate. No stale documentation remains in the diff.
- [TYPE] type-design disabled — manual: `build_dogfight_weapon_lookup(InventoryConfig | None) -> Callable[[str], CatalogItem | None]` fully typed; reusing `CatalogItem` for `ship_weapons` is the deliberately-approved option 2b (not a new newtype), consistent with the spec; `Field(default_factory=list)` is the correct pydantic empty-collection pattern.
- [SIMPLE] simplifier disabled — manual: no over-engineering, no dead code; the inline lambda was DELETED and replaced by the named helper (net simplification at the call site); `list(genre_ship_weapons)` is intentional anti-aliasing.
- [RULE] rule-checker disabled — manual: see `### Rule Compliance` — all 13 python.md checks pass.

### Rule Compliance
Checked every changed `.py` against the 13 `python.md` lang-review checks:
1. Silent exceptions — PASS: no try/except added; failures propagate as `ValueError`.
2. Mutable defaults — PASS: `Field(default_factory=list)` (pydantic) and a closure capture of a list; no mutable default ARG.
3. Type annotations — PASS: helper, inner `_lookup`, and the span context manager are fully annotated.
4. Logging — N/A: the subsystem decision emits an OTEL span (the prescribed mechanism); no logger in the diff.
5. Path handling — N/A: no path manipulation; new YAML is data loaded by the existing safe loader.
6. Test quality — PASS: specific assertions, preconditioned no-raise test, correct mock target.
7. Resource leaks — PASS: span context managers use `with`.
8. Unsafe deserialization — PASS: `yaml.safe_load` + pydantic `extra=forbid` (security subagent corroborated).
9. Async pitfalls — N/A: synchronous code.
10. Import hygiene — PASS: explicit imports; no star/circular (`genre.models.inventory` does not import `dogfight_shot`).
11. Input validation — PASS: content validated by `CatalogItem`/`DamageSpec` pydantic validators at load.
12. Dependency hygiene — N/A: no dependency changes.
13. Fix-introduced regressions — N/A: no fix-on-fix.
Also checked SOUL "Bind the Ruleset, Don't Balance It": the ship weapon is honestly `bespoke` (damage-scaled 1d4, NOT a verbatim SWN starship weapon), so it does not try to balance a native subsystem against a bound SRD weapon — compliant with the doctrine and the approved design rationale.

### Devil's Advocate
Suppose I want this broken. The richest target is the resolver's tolerance of missing inventory. `resolve_inventory` sets `genre_ship_weapons = pack.inventory.ship_weapons if pack.inventory is not None else []`. A careless future pack that wires a `dogfight` (player_weapon=multifocal_laser) but ships NO genre `inventory.yaml` — only a world one — gets `ship_weapons=[]`, and the dogfight dies with "weapon id 'multifocal_laser' not found / has no damage spec." A developer reads that and hunts in content for a typo'd id, never realizing the genre inventory file is simply absent. A real diagnostic trap (the silent-failure-hunter caught it) — but it fails LOUDLY, it follows the resolver's pre-existing `pack.inventory is None → []` convention (this story did not invent it), and no shipping pack hits it. Non-blocking.

Second attack: a confused world author (Jade, per CLAUDE.md — homebrew is the goal) adds `ship_weapons:` to a world `inventory.yaml`, expecting a new fighter weapon. The merge-path `model_copy(update={"ship_weapons": list(genre_ship_weapons)})` overwrites it with the genre's collection — her weapon vanishes with no error and no span. The model comment documents "genre-tier-only in v1," but a homebrew author won't read server source. This is the strongest design smell, yet it is an explicit v1 scope decision, not a bug; logged for v1.1.

Third: a `damage=None` ship weapon would emit a `weapon_resolved` span (a faint "lie") before `_resolve_weapon` rejects it — but content damage is pydantic-shaped in practice and the dogfight cdef weapons all carry damage. Fourth: races — none; the closure captures an effectively-immutable list, no shared mutable state, fully synchronous. Fifth: huge inputs — `ship_weapons` is one item; `next()` is trivially bounded. None rise above non-blocking. The de-dup is byte-identical (no stat drift), AP 20 survives end-to-end for all three worlds, and the GM-panel span makes the resolution auditable. The code holds.

**Data flow traced:** `cdef.player_weapon`/`opponent_weapon` (authored YAML id) → `resolve_inventory(pack, world)` → `build_dogfight_weapon_lookup` → match in `ship_weapons` → `DamageSpec(AP 20)` → `effective_armor_after_ap` in the dogfight shot. Safe because an unknown id returns `None` → `_resolve_weapon` raises (no silent substitution), and the genre collection is the single source for every world.
**Pattern observed:** span-emitting resolver callable — telemetry emitted at the resolution decision (OTEL Observability Principle) at dogfight_shot.py:43-49.
**Error handling:** miss → `None` → loud `ValueError` in `_resolve_weapon` (dogfight_shot.py:282); `None` inventory tolerated (returns `None`), no `AttributeError`.
**Handoff:** To SM (Vizzini) for finish-story.