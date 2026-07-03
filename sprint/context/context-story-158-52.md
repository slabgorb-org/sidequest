# Story 158-52 Context

## Title
Creature portraits derive from bestiary.yaml — demote per-world creatures.yaml to an optional naming-override

## Metadata
- **Story ID:** 158-52
- **Type:** refactor
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** orchestrator,server,content
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
Creature portraits currently render only for 2 of 22 WN-bound worlds (beneath_sunden, flickering_reach) because `scripts/generate_creature_images.py::collect_creatures` hard-rglobs `creatures.yaml` and never reads `bestiary.yaml`. For WN packs the RUNTIME roster is `bestiary.yaml` (encountergen samples it; `creatures.yaml` is NOT a runtime source on the WN path), so a per-world `creatures.yaml` is now almost pure duplication: `compose_prompt` needs only name/description/threat_level/id, and the bestiary already carries name, description, and level (level->threat is a trivial map). The ONE thing `creatures.yaml` adds is a NON-PROPER-NOUN `name` for the CLIP prompt — load-bearing only for worlds with a "nothing is named" conceit (beneath_sunden), where Z-Image would otherwise paint "Constrictor Snake" as a caption. Style already auto-layers from each world's `visual_style.yaml positive_suffix` (which already carries the no-text/no-caption clause).

DECISION (Keith, 2026-07-01): "Something is missing" — do NOT hand-author per-world image manifests (~900 plates across 22 worlds does not scale). Make the BESTIARY the single source of truth for creature-image production; the render pipeline DERIVES the prompt from it. Demote `creatures.yaml` to an OPTIONAL per-world override, needed only where a world overrides the derived name (naming conceits) or wants a bespoke marquee plate.

DESIGN (for Architect/ADR then Dev):
- `generate_creature_images.py` / `render_common.py`: add `bestiary.yaml` as a creature source. For each bestiary entry derive {id, name, description, threat_level<-level, tags}. Where a world ships a `creatures.yaml` override for an id, the override wins (per-field merge, ADR-121 flavor); otherwise render straight from bestiary.
- For "nothing is named" worlds (beneath_sunden), the derived CLIP name must be de-proper-noun'd — either via a per-world `name_is_secret: true` flag that suppresses/rewrites the CLIP name, or by keeping ONLY the naming override in `creatures.yaml` (drop the duplicated descriptions). Do not paint proper nouns.
- Update the invariant test `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`: `test_every_low_tagged_bestiary_entry_is_renderable` currently asserts the OLD per-world-manifest model (every low-tagged id must be in `creatures.yaml`). Under the new design "renderable" = "resolvable to a render prompt" = "in bestiary with a non-empty description (+ naming handled)". Retune the assertion to the derived-source model; keep the beneath_sunden non-proper-noun guard for the 6 bespoke shaft ids.

RELATED 107-2 DEBT (currently also red, scope alongside or split): `test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` — only `entrance.yaml` declares `encounter_creatures`; needs >=2 distinct per-room bindings + the server-side resolver/OTEL (`tests/server/dispatch/test_room_creature_binding_107_2.py`). This is beneath_sunden content+wiring, independent of the render-source architecture above.

PROVENANCE: surfaced 2026-07-01 while scoping the 160-4 full-suite-green push (option C). These two beneath_sunden tests are pre-existing story-107-2 debt, unrelated to 160-4; 160-4 lands without them. Full render-path trace, field-by-field, in the 160-4 session Delivery Findings.

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- generate_creature_images.py collects creatures from bestiary.yaml (deriving name/description/threat_level<-level/id/tags); a world creatures.yaml entry for the same id acts as a per-field OVERRIDE, not a precondition
- A world with a naming conceit (beneath_sunden 'nothing is named') never emits a proper-noun CLIP name — via a per-world secret-name flag or a naming-only override; verified by a render dry-run showing no bestiary proper noun in the CLIP
- test_beneath_sunden_creature_images_107_2.py invariant retuned to the derived-source model: every low-tagged bestiary entry is renderable because it resolves to a prompt (bestiary description present + naming handled), not because it appears in creatures.yaml
- Wiring test: a render dry-run for at least one previously-manifest-less WN world (e.g. space_opera/coyote_star) produces non-empty creature prompts from bestiary alone — proving portraits now scale past the 2 hand-authored worlds
- ADR (or amendment to ADR-059/086/127) records: bestiary.yaml is the single source of truth for creature-image production; creatures.yaml is an optional per-world override

---
_Generated by `pf context create story 158-52` from the sprint YAML._
