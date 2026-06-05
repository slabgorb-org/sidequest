---
story_id: "77-6"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 77-6: Author wry_whimsy seed_tropes deck (ADR-128) — active_seeds carve-out

## Story Details
- **ID:** 77-6
- **Jira Key:** (none — Jira integration is not configured for this project)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** implement
**Phase Started:** 2026-06-04T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T00:00:00Z | - | - |
| implement | 2026-06-04T00:00:00Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The "active_seeds carve-out" has no YAML field — it is an engine-runtime concept (`_DEFAULT_INITIAL_HAND=3` in `seed_tick.py` dealing into the live `active_seeds` list). Neither tea_and_murder nor wry_whimsy declare it in YAML; the deck is just a flat list. Future ADR-128 docs/stories should avoid implying authors set `active_seeds` in pack YAML. *Found by Dev during implementation.*
- **Gap** (non-blocking): `pack.yaml`'s `extensions` list is purely declarative metadata (`PackMeta.extensions`) — the loader reads `seed_tropes.yaml` unconditionally regardless of whether `seed_tropes` is listed. tea_and_murder lists it; wry_whimsy did not until this story. Worth a loader assertion that listed extensions have backing files (and vice-versa) to keep the declaration honest. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

## Branch Strategy
**Branch Strategy:** gitflow (feat/77-6-wry-whimsy-seed-tropes-deck)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `genre_packs/wry_whimsy/pack.yaml` - added `seed_tropes` to the `extensions` list to mirror tea_and_murder's declaration
- `genre_packs/wry_whimsy/seed_tropes.yaml` - 14-seed deck (authored at session setup; verified against the `SeedTrope` `extra="forbid"` schema, no changes needed)

**Tests:** N/A (trivial content workflow — no test suite). Validated by real loader + deck simulation (GREEN).
**Branch:** feat/77-6-wry-whimsy-seed-tropes-deck (NOT pushed — SM handles git per instructions)

**Validation:**
- `load_genre_pack(wry_whimsy)` → all 14 seeds pass `SeedTrope.model_validate` (`extra="forbid"`)
- `SeedDeck(...).draw()` x `_DEFAULT_INITIAL_HAND` (3) → deterministic, unique initial active-seeds hand; reproducible across reload

**Handoff:** To review phase

## Implementation Notes

**Task:** Author wry_whimsy genre pack seed_tropes deck per ADR-128.

The tea_and_murder genre pack has a reference implementation at
`genre_packs/tea_and_murder/seed_tropes.yaml` with 20 tropes in a cosy murder-mystery
register. The wry_whimsy pack (portal-fairytale: oz + wonderland + gulliver)
currently has no seed_tropes deck.

**Acceptance Criteria:**
1. wry_whimsy pack has a seed_tropes deck mirroring the tea_and_murder structure
2. Genre-appropriate to portal-fairytale tone (whimsy with teeth, absurd authority, nonsense-logic antagonist)
3. Active seeds carve-out per ADR-128 mechanism (initial active_seeds drawn at session start)
4. Pack still loads/validates (run the pack validator if one exists)
5. Tropes are flavored to wry_whimsy; NOT copied from tea_and_murder

**Technical Notes:**
- Seed tropes are short-arc narrative hooks (ADR-128)
- Each seed: id, name, description, flavor_tags, lifespan_turns, delivery_hints[], narrative_hint
- Reference: ADR-128 (Trope Temporal Governor, Seed-Trope Deck, and NPC Development Ladder)
- Initial hand size per ADR-128: 3 seeds (`ensure_initial_draw` draws _DEFAULT_INITIAL_HAND=3)
- Flavor should reflect the light-to-savage gradient: oz (lightest), wonderland (mid), gulliver (most savage)
- Update genre_packs/wry_whimsy/pack.yaml to add seed_tropes to extensions list
