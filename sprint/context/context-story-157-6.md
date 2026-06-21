# Story 157-6 Context

## Title
[CONTENT] Faction-tag fan-out: oz, wonderland, the_circuit

## Metadata
- **Story ID:** 157-6
- **Type:** chore
- **Points:** 5
- **Priority:** p2
- **Workflow:** trivial (setup → implement[Dev] → review → finish — **no TEA RED phase**)
- **Repo:** content (sidequest-content, base branch `develop`, branch `feat/157-6-faction-tag-fanout`)
- **Epic:** 157 — Faction/zone-scoped content eligibility
- **Depends on:** 157-5 (DONE — gulliver proof world, content PR #483 / commit `db55af9`)

## Problem
Multi-region worlds leak content across zones (epic-157 / ADR-059 amendment): the
Monster Manual seeds creatures with no `location_tags`, and `format_area_creatures`
does zero location filtering — so a 4th-voyage Yahoo could surface on the 1st-voyage
Lilliput shore. The engine seams that scope content per region by **faction** are DONE
(157-2/3/4), and the content pattern is **proven** on one world (157-5, gulliver). This
story fans that same content pattern out to the next three multi-region worlds so their
pooled content stops bleeding across regions:
- **oz** — 4 countries + Emerald City + open country (7 region-factions)
- **wonderland** — region groups under a few faction banners
- **road_warrior/the_circuit** — subculture territories

This is the last content prerequisite before 157-7 (the strict fail-loud zone-tagging
load validator), which depends on this story.

## Technical Approach (where to look — Dev owns the tagging calls)
**Replicate the 157-5 gulliver pattern exactly.** Read the proof commit first for the
exact YAML shape:
```
git -C sidequest-content show db55af9
```
That commit added a `factions:` list to every **pooled, home-less** content item across
three files in `genre_packs/wry_whimsy/worlds/gulliver/`:
- `bestiary.yaml` — creatures, one (or more) region-faction each
- `tropes.yaml` — region-scoped tropes get their faction; world-global "spine" tropes get `"*"`
- `seed_tropes.yaml` — seeds, region-anchored

**Faction value = the region's `controlled_by:<faction>`** — never invent a faction. The
authoritative source per world is its `cartography.yaml` `controlled_by:` field. Confirmed
faction sets (read cartography.yaml for the full region→faction mapping before tagging):

| World | Faction values present in cartography.yaml `controlled_by:` |
|-------|-----------------------------------------------------------|
| `genre_packs/wry_whimsy/worlds/oz` | `munchkins`, `open_country`, `the_wizard`, `witch_of_the_west`, `glinda`, `gillikin_hedge_witches`, `no_one` |
| `genre_packs/wry_whimsy/worlds/wonderland` | `the_queens_terror`, `the_rigged_game`, `no_one` (many regions map onto these few banners — grouping is coarser than oz/the_circuit) |
| `genre_packs/road_warrior/worlds/the_circuit` | `bosozoku`, `cafe_racers`, `tuk_tuk`, `lowriders`, `dekotora`, `one_percenters`, `mods`, `rockers`, `matatu`, `raggare` |

All three worlds already have `bestiary.yaml`, `tropes.yaml`, `seed_tropes.yaml`,
`world.yaml`, and `cartography.yaml` present. Note: oz already declares
`setting.region_id` on all four openings (content PR #482, commit `1efacf8`) — relevant prep.

Use `"*"` for genuinely world-global items that should be eligible in every region
(mirror gulliver's 3 world-global spine tropes). Don't over-globalize — the whole point
is region scoping.

**Reference material to read before tagging:**
- Design spec: `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md`
- Epic direction (Keith, 2026-06-20): `sprint/epic-157.yaml` description
- ADR-059 (Monster Manual) + its 157-1 amendment for the eligibility model
- No-bleed verification template (gulliver): `sidequest-server/tests/genre/test_157_5_gulliver_no_bleed.py`

## Scope
- **In scope:** add `factions:` lists to pooled/home-less content items in `bestiary.yaml`,
  `tropes.yaml`, and `seed_tropes.yaml` for **oz, wonderland, and the_circuit** only.
- **Out of scope:** engine changes (seams are done in 157-2/3/4); the strict load
  validator (that is 157-7); any other world; re-tagging gulliver (done in 157-5);
  inventing new factions or editing cartography `controlled_by` values.

## Acceptance Criteria
1. Every pooled / home-less content item in oz, wonderland, and the_circuit
   (`bestiary.yaml`, `tropes.yaml`, `seed_tropes.yaml`) carries a `factions:` list.
2. Every faction value is either a real `controlled_by:` faction from that world's
   `cartography.yaml`, or `"*"` for a deliberately world-global item. No invented factions.
3. No content bleed: region-scoped creatures/tropes/seeds cannot surface in a region
   they don't belong to — verified the way 157-5 proved it for gulliver (mirror
   `test_157_5_gulliver_no_bleed.py`; a no-bleed test/verification covering the three
   new worlds is the wiring proof, not just the YAML edits).
4. YAML stays valid and the genre-pack loader loads all three worlds cleanly (no
   pydantic `ValidationError`, no loader error).

---
_Enriched by SM (Camina Drummer) at setup — trivial workflow has no TEA RED phase, so
the context carries the full intent for Dev. Pointers + AC only; tagging calls are Dev's._
