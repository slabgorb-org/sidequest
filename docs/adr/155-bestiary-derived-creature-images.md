---
id: 155
title: "Bestiary-Derived Creature Images — bestiary.yaml Is the Single Source of Truth for Creature-Image Production; creatures.yaml Demotes to an Optional Per-World Override"
status: accepted
date: 2026-07-03
deciders: ["Keith Avery"]
supersedes: []
superseded-by: null
related: [59, 86, 121, 124, 127]
tags: [media-audio]
implementation-status: live
implementation-pointer: "scripts/generate_creature_images.py::collect_creatures"
---

# ADR-155: Bestiary-Derived Creature Images — bestiary.yaml Is the Single Source of Truth for Creature-Image Production; creatures.yaml Demotes to an Optional Per-World Override

## Context

Creature portraits rendered for only 2 of 22 WN-bound worlds (beneath_sunden,
flickering_reach) because `scripts/generate_creature_images.py::collect_creatures`
hard-rglobbed `creatures.yaml` and never read `bestiary.yaml`. On the
Without-Number path the RUNTIME roster is `bestiary.yaml` — the encountergen
samples it; `creatures.yaml` is not a runtime source — so a per-world
`creatures.yaml` had become almost pure duplication: `compose_prompt` needs only
`{id, name, description, threat_level}`, and the bestiary already carries name,
description, and level. The one thing `creatures.yaml` added was a
NON-PROPER-NOUN `name` for the CLIP prompt, load-bearing only for worlds with a
"nothing is named" conceit (beneath_sunden), where Z-Image would otherwise paint
the roster name as a caption.

Hand-authoring per-world image manifests does not scale: ~900 plates across 22
worlds (Keith, 2026-07-01: "something is missing" — the missing piece was the
derivation, not more authoring).

## Decision

1. **The bestiary is the single source of truth for creature-image
   production.** `collect_creatures` walks every `bestiary.yaml` (top-level
   `entries:`) per world (genre-root files map to world `default`) and derives
   a render item per entry: `{id, name, description, tags}` verbatim,
   `threat_level <- max(1, ceil(level / 2))` — level 1-2 spot, 3-4 quarter,
   5-6 half, 7+ full page, matching the low/mid/deep band tagging.
2. **`creatures.yaml` is demoted to an optional per-world override manifest.**
   An entry with a bestiary id overrides PER-FIELD (ADR-121 flavor): declared
   fields win, omitted fields fall through to the derived value. Entries with
   no bestiary id pass through verbatim (bespoke marquee plates). One render
   item per (world, id).
3. **Naming conceits declare `name_is_secret: true`** at the top level of the
   world's `creatures.yaml`. Under the flag, every bestiary-derived render
   name is replaced with the entry's `role` line (SRD-convention descriptive
   prose — already non-proper), so the roster proper noun never reaches
   subject or CLIP. A per-id override name still wins. An entry with no
   `role` under the flag is loud-skipped.
4. **Unrenderable entries loud-skip** (ADR-124 fold pattern): missing/empty
   `description` or non-int `level` logs a warning naming the id and is
   excluded — never a silent drop, never a batch-killing crash.
5. **Visual style resolves per world, not per genre.** A world-level
   `positive_suffix` REPLACES the genre suffix (it is where beneath_sunden's
   no-text/no-caption clause lives), so the batch loop loads
   `load_visual_style(genre_dir, world, tier="portrait")` per world.

## Consequences

- Creature plates scale to all 22 worlds from content that already exists;
  a new world gets portraits by authoring its bestiary, nothing else.
- The per-world authoring burden drops to naming conceits and bespoke plates.
  beneath_sunden keeps its 13 bespoke specs; its other 179 entries render
  derived.
- The invariant test `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`
  is retuned to the derived-source model: "renderable" = non-empty bestiary
  description + naming handled (flag or non-proper override), not "present in
  creatures.yaml".
- ADR-059's monster-manual image intent gets its content pipeline back without
  hand-kept manifests; ADR-086/127 composition layers are unchanged — this ADR
  only moves WHERE the subject/name come from.
- Contract pinned by `tests/scripts/test_creature_bestiary_source_158_52.py`
  (orchestrator) — derivation, per-field merge, conceit flag, loud-skip, and
  CLI dry-run wiring for a previously manifest-less world (coyote_star).
