# Story 90-1 Context

## Title
Encountergen ruleset-awareness — emit WWN/CWN/SWN-aligned enemy stat blocks via the RulesetModule seam so pregen.seed_manual populates the Monster Manual encounters pool for ruleset-module packs (replaces native allowed_classes/class_hp_bases dependency)

## Metadata
- **Story ID:** 90-1
- **Type:** story
- **Points:** 8
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server,content
- **Epic:** 90 — Ruleset-Module Worlds: Live Combat & Magic Verification Enablement

## Problem
`encountergen` is **native-dial-only**: it requires `rules.yaml allowed_classes`
(and `class_hp_bases`) to build enemy stat blocks. For a **RulesetModule** pack
(ADR-117 — `ruleset: wwn|cwn|swn`, which deliberately drops the native
`allowed_classes` block), it hard-fails with `genre <pack> has no allowed_classes`.
Consequently `pregen.seed_manual`'s encountergen call returns `None` and the
**Monster Manual `encounters` pool stays empty** (87-4 finding: evropi 49 NPCs / **0
encounters**; long_foundry 39 / **0**).

That gap matters for **free-play reachability** — a fight-seeking player has no
named/located/varied hostiles to run into (the "basic bestiary floor"). It is *not*
about whether a *triggered* Other is mechanically capable — WWN already seats the
Other from `opponent_default_stats` at trigger time (87-4 finding (1)). This story
supplies reachable hostile *presence/variety* for live play; it does not change how a
triggered confrontation seats its Other.

This is the **root dependency of epic 90**: 90-3 (live free-play OTEL proof) needs
statted, reachable hostiles, and epic 89 (Barsoom) depends on this too.

## Technical Approach
_Hints for TEA/Dev — refine during RED/green; the architect may want a design pass on
the seam shape before tests are locked._

- **Seam:** route encountergen's enemy-stat generation through the **`RulesetModule`**
  ABC (`sidequest-server/sidequest/game/ruleset/` — `base.py`, `registry.py`,
  `native.py`, `swn.py`) instead of reading `allowed_classes`/`class_hp_bases` directly.
  The native path becomes one `RulesetModule` implementation; `wwn`/`cwn`/`swn` provide
  their own enemy-stat-block emission aligned to each SRD.
- **Detection:** read the pack's `ruleset:` (already resolved at load via the registry;
  unknown → `UnknownRulesetError`, fail loud — preserve that). Native-dial packs (no
  `ruleset:` or `ruleset: native`) keep today's behavior exactly (regression guard).
- **Touch points:** `sidequest-server/sidequest/cli/encountergen/` (generation),
  `pregen.seed_manual` (the caller that currently gets `None`). Content side: the
  ruleset-module packs (heavy_metal evropi/long_foundry) whose Monster Manual pools
  this populates.
- **OTEL (mandatory per the Observability Principle):** emit a span on the seeding
  decision — which ruleset path fired, how many encounters were generated, per pack —
  so the GM panel can verify the pool was populated (not silently empty).
- **No silent fallback:** a ruleset-module pack must NOT silently fall back to the
  native path or to an empty pool — emit ruleset-aware blocks or fail loud.

## Scope
- **In scope:** make `encountergen` + `pregen.seed_manual` ruleset-aware via the
  RulesetModule seam; emit WWN/CWN/SWN-aligned enemy stat blocks; populate the Monster
  Manual `encounters` pool for ruleset-module packs; OTEL on the seeding path; preserve
  native-dial behavior.
- **Out of scope:** the live free-play OTEL proof (90-3); the magic-plugin session-bind
  fix (90-2); scene-harness hydrator spellcasting/encounter seeding (90-4); any change
  to how a *triggered* confrontation seats its Other (`opponent_default_stats` is
  untouched); authoring per-world bespoke bestiaries beyond the basic SRD-aligned floor.

## Acceptance Criteria (DRAFT — TEA to encode/refine as RED tests)
1. **No hard-fail on ruleset-module packs.** `encountergen` on a `ruleset: wwn` pack
   (heavy_metal) no longer raises `... has no allowed_classes`; it routes through the
   RulesetModule seam. Test: drive encountergen on heavy_metal, assert no raise + a
   result.
2. **WWN-aligned stat blocks.** Generated enemies for a `wwn` pack carry WWN-shaped
   combat numbers (hp / armor_class / attack-channel) sourced via the RulesetModule, not
   native dial metrics. Test: assert the emitted block shape/fields match the wwn module.
3. **Monster Manual pool populated.** `pregen.seed_manual` yields a **non-empty**
   `encounters` pool for evropi and long_foundry (was 0/0), with named + located +
   varied hostiles. Test: seed → assert pool size > 0 and entries are well-formed.
4. **OTEL seeding span.** The seeding path emits a span recording the ruleset used and
   the encounter count per pack (GM-panel lie-detector). Test: drive seeding, assert the
   span fired with the ruleset + count attributes.
5. **Native-dial regression intact.** A native pack (e.g. caverns_and_claudes) seeds
   exactly as before via `allowed_classes`/`class_hp_bases`. Test: native seed unchanged.
6. **Generality.** The seam is ruleset-generic (wwn/cwn/swn dispatch via the registry),
   not a wwn-only special-case. Test: at least the wwn path proven; cwn/swn reachable via
   the same dispatch (no native-only assumption).

## References
- Epic context: `sprint/context/context-epic-90.md`
- ADRs: 059 (Monster Manual server-side pregen), 117 (pluggable RulesetModule), 114
  (ablative HP), 116/139 (confrontation seating invariants)
- Code: `sidequest-server/sidequest/cli/encountergen/`, `pregen.seed_manual`,
  `sidequest-server/sidequest/game/ruleset/{base,registry,native,swn}.py`
- 87-4 origin: `docs/superpowers/specs/2026-06-05-ac5-otel-combat-verification-design.md`
  (D1 — the decision that filed this work to epic 90)

---
_Seeded from epic-90 scope + 87-4 findings (SM, story start). ACs are DRAFT — TEA owns
the final RED encoding; architect may design-pass the RulesetModule seam shape first._
