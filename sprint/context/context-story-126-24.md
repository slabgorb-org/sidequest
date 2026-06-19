# Story 126-24 Context

## Title
[FATE/CHARGEN] Narrative chargen seeds the Fate pyramid + aspects as editable defaults (genre translation table + world overrides)

## Metadata
- **Story ID:** 126-24
- **Type:** story
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** content,server,ui
- **Epic:** Fate Core playtest follow-ups — annees_folles eval (2026-06-16/17)

## Problem
Source: sq-playtest-pingpong 2026-06-19 [GAP] (Keith flagged in play). The narrative chargen wizard for pulp_noir/annees_folles (Fate Core, ADR-144) collects rich answers (Origin=The Service, Signature=I Find Things Out, Connection=A Ghost, Drive=Answers) but DISCARDS them at the Fate steps: fate_aspects renders empty (generic placeholders) and fate_pyramid is fully blank (Great 0/1, Good 0/2, Fair 0/3, Average 0/4) — the player must hand-rank all 10 skills. Narrative chargen is meant to be the friendly on-ramp (esp. for Alex, slow typist); instead it bait-and-switches to a blank Fate sheet.

ROOT CAUSE (validated across 3 repos this playtest):
- CONTENT (genre_packs/pulp_noir/char_creation.yaml): narrative steps (origins/crucible/connection/drive) emit NATIVE-model mechanical_effects (class_hint=Detective, background=Veteran, rpg_role_hint, jungian_hint, personality_trait, relationship, goals) — authored before the Fate binding. The Fate steps (fate_aspects/fate_pyramid/fate_stunts) are a parallel track: choices:[] + fate_chargen_step: markers, no consumption of the earlier hints.
- SERVER (server/websocket_handlers/chargen_mixin.py): _chargen_fate_aspects_confirm / _chargen_fate_pyramid_confirm only RECORD the submitted UI payload. The native hints ARE accumulated (acc.class_hint/race_hint/rpg_role_hint exist, used today for portrait/lore/quest-spine seeding) but are NEVER consumed into a Fate seed when the step is PRESENTED. game/ruleset/fate_chargen.py builds+validates a FateSheet from explicit post-edit choices; validate_fate_sheet/pyramid_violations is the single legality authority.
- UI (ui/.../CharacterCreation/FateChargenPanel.tsx): SEAM ALREADY EXISTS — FateSkillPyramidPanel initializes local state from currentAllocation; FateAspectsPanel slots carry value (pre-fill, editable) + suggestion (placeholder). So the server only has to SEND a seeded currentAllocation + slot.value; expected to need little/no UI code, but verify end-to-end (no regression to the no-silent-default behavior for HC/Trouble).

DESIGN DECISION (Keith, 2026-06-19): genre-tier translation table WITH world overrides. Base narrative-hint -> Fate skill+aspect-seed map lives in pulp_noir genre config (skills like Investigate/Shoot are genre rulebook per ADR-140); individual worlds (annees_folles) may override/extend per-hint via ADR-121 layered per-field resolution. NOT per-choice fate_*_seed blocks (rejected: duplicative across choices/worlds, staples Fate crunch onto the world-flavor on-ramp). Seed is always an EDITABLE DEFAULT — override always allowed.

Affected: content genre_packs/pulp_noir/ (new genre-tier seed table + optional annees_folles world override) ; server chargen_mixin.py present-time seed computation + fate_chargen.py helper ; ui FateChargenPanel.tsx (verify-only expected). Does NOT block 150-1 mechanical AC verification.

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- Genre-tier translation table maps accumulated narrative hints (class_hint/background/rpg_role_hint) to a Fate skill-pyramid allocation + aspect-text seeds; the table lives in pulp_noir genre config (genre is the rulebook, ADR-140).
- World override: annees_folles (or any Fate world) can override/extend the genre seed table per-hint via ADR-121 layered per-field resolution; a unit test proves a world override replaces the genre default for a given hint.
- Server computes the seed from accumulated chargen mechanical_effects when PRESENTING fate_pyramid/fate_aspects (not only on confirm), and sends pyramid via currentAllocation + aspects via slot.value.
- The seeded pyramid is LEGAL: passes pyramid_violations/validate_fate_sheet for the pack chargen_pyramid + chargen_apex_rating (every rung at exact budget; no rung over/under).
- Seed is an EDITABLE DEFAULT: player can override every skill rating and every aspect; the override always wins; HC/Trouble keep the no-silent-default invariant (must be non-empty on confirm).
- OTEL span on seed computation (hints-in -> skills+aspects-out, world_override_applied bool) so the GM panel can confirm the seed engaged and the narrator/UI didn't improvise (lie-detector parity, CLAUDE.md OTEL principle).
- End-to-end repro retired: walking The Service / I Find Things Out / A Ghost / Answers presents a pre-ranked pyramid (Investigate seeded high) + pre-filled aspects, all overridable — no blank sheet. UI renders the seed with no code change OR the minimal change is wired and tested (wiring test, not source-grep).
- Chargen confirmation prose renders the Fate High Concept, not the native {race} {class} template (char_creation.yaml 'confirmation' step) — no 'a Military I Find Things Out' under a Fate binding.
- Pack default signature gear compiles onto the sheet at chargen via the NARRATIVE-WIZARD path (folded from the pingpong [BUG]): pulp_noir/rules.yaml declares a gear: list (noir_trench_coat, noir_pi_license→'Licensed Private Investigator', noir_service_revolver→'A Piece I'd Rather Not Use', noir_little_black_book→'A Contact for Every Occasion') compiled via the EXISTING fate_gear.compile_gear_onto_sheet seam. The narrative-wizard chargen currently bypasses it (stored save shows only HC+Trouble+player aspects, all source_gear=null). Wire the seam into the narrative-wizard path; resulting sheet carries the pack's gear-derived aspects in addition to player + seeded aspects.

---
_Generated by `pf context create story 126-24` from the sprint YAML._
