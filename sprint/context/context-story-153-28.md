# Story 153-28 Context: [BENEATH_SUNDEN-AUTHOR-CAMP-CAST] Author the Surface-Camp Cast

## Story Summary

Author `genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` with the Ropefoot surface-camp cast — Brecca Half-Hand (winch-keeper / camp boss) and the rope-keepers (a short roster of those who keep the rope and those who have stopped going down).

**Type:** chore  
**Points:** 2  
**Workflow:** trivial

## Acceptance Criteria

1. `npcs.yaml` file exists and loads without validator errors
2. Brecca Half-Hand is authored with canon-consistent traits:
   - Role: winch-keeper / camp boss
   - Appearance: missing three fingers from left hand; old sweat
   - Voice: grave, economical, speaking in ledger/cargo-cult procedural language
   - Located at ropefoot region
3. Rope-keepers roster authored (short, no invented strangers per lore)
4. Initial dispositions set (warm cast defaults 15–30 per ADR-020)
5. All history_seeds contain voice/mannerism prose for narrator extraction
6. Location tags set to ["ropefoot"] for placement awareness
7. `pregen.authored_npcs_seeded` for beneath_sunden shows `total_authored > 0` when the world loads

## Canon / Lore Context

### Beneath Sünden World Identity
- Moria-as-tragedy: an honest, working dwarfhold that dug past where digging stops and did not survive
- One descent, no hub, no second mouth, no walking to a different dungeon
- The deep is generated and unbounded; the surface is fixed, small, known to the inch
- The board of the unreturned is the regional memory; the count is the campaign
- Ropefoot are the ones who came after, not the hold's heirs — no rescue is possible

### Ropefoot Camp (region: ropefoot)
- Bootworn camp at the lip of the only shaft
- Landmarks: the winch-house (over the drum), the kept fire (never let go out), the board of the unreturned (names burned in with iron), rigging benches (worn pale in the middle)
- The people: the ones who keep the rope and the ones who have stopped going down and have not yet left
- Courteous in the spare way of a place that knows a fraction of its dead by name and the rest by the length of time the rope stayed slack

### Brecca Half-Hand (Chargen Canon)
- Winch-keeper; missing three fingers from left hand; old sweat
- Frames the chargen and the ledger
- Counts the bones, arranges the trades, dips the quill for the tally ("For the tally, in case the rope does not come back"), hands out the gear
- Voice: grave, economical, speaking in procedural ledger language; no winking, no gloss
- Never explains; counts; writes; reaches

### Rope-Keepers Context
- "Ropefoot is a SHORT roster (a winch-keeper, a few who will not go down again); it cannot afford invented strangers"
- Per ADR-020: initial_disposition is the player's starting standing with this NPC
- No townsfolk-tone NPCs — humanoids appear as grave rope-keepers or those who have stopped going down

## Schema / Implementation Notes

### AuthoredNpc Fields
- **id:** unique slug identifier
- **name:** display name
- **pronouns:** he/him, she/her, they/them, etc.
- **role:** occupation or title (required for seeding; passed to narrator)
- **ocean:** dict[str, float] with O, C, E, A, N (0.0–1.0) per ADR-042; optional
- **appearance:** visual description (becomes ocean_summary in seeding if present)
- **age:** age descriptor (e.g., "mid-fifties", "indeterminate, perhaps seventy")
- **distinguishing_features:** list of physical/behavioral marks
- **history_seeds:** list of prose snippets for voice/mannerisms/background; narrator extracts verbal tics
- **initial_disposition:** int (-100 to 100); warm cast defaults 15–30
- **location_tags:** list of lowercase substrings anchoring placement (e.g., ["ropefoot"])

### pregen._seed_authored_npcs Contract
- Reads `pack.worlds[world].authored_npcs` from the loaded World object
- Uses exact (case-insensitive) name match for dedup — an authored NPC must never be shadowed by a generated walk-on
- Carries location_tags through to ManualNpc so placement-aware selection surfaces the NPC as "nearby (not yet met)" before narration
- Returns count of inserted + tag-refreshed; logs outcome on every successful read

### YAML Structure (from glenross/npcs.yaml template)
```yaml
version: "0.1.0"
world: beneath_sunden

npcs:
  - id: brecca_half_hand
    name: "Brecca Half-Hand"
    pronouns: "she/her"
    role: "Winch-keeper, camp boss of Ropefoot"
    ocean: { O: 0.7, C: 0.8, E: 0.4, A: 0.6, N: 0.5 }
    appearance: >-
      [visual description: missing three fingers from left hand, old sweat, etc.]
    age: "[age descriptor]"
    distinguishing_features:
      - "[feature 1]"
      - "[feature 2]"
    history_seeds:
      - >[prose: voice/mannerism 1]
      - >[prose: voice/mannerism 2]
    initial_disposition: 20
    location_tags: ["ropefoot"]
```

## Related Materials

- **Within-world:** `lore.yaml` (world identity, themes, Ropefoot description), `cartography.yaml` (ropefoot region details, landmarks, entities), `seed_tropes.yaml` (Ropefoot roster constraint, tone register)
- **Chargen:** `openings.yaml` (Brecca framing in the UI flow)
- **Server:** `sidequest-server/sidequest/genre/models/authored_npc.py` (schema), `sidequest/server/dispatch/pregen.py::_seed_authored_npcs` (seeding contract)
- **Template:** `genre_packs/tea_and_murder/worlds/glenross/npcs.yaml` (12-NPC warm cast example with full voice and history)

## Notes for the Implementer

1. **Voice register:** beneath_sunden is grave, lethal, Moria-as-tragedy. Never wink. Never explain or gloss. Ropefoot speaks in the economical, procedural language of the ledger and the rope — no tavern-keeper warmth, no bard chatter.

2. **Brecca is the diamond:** she is the one NPC the party will see every session, the one who dips the quill, the one who counts. Her voice is the camp's voice. Every line should reinforce the ledger, the count, the fire, the rope.

3. **Short roster, no invented strangers:** the rope-keepers should be few (2–4 others). They are the ones who keep the rope or the ones who stopped going down. No tavern keeper, no merchant, no bard. Every NPC earns their place by being tied to the rope or the decision not to descend.

4. **Location tags:** set all camp NPCs to `["ropefoot"]` so the Manual can surface them as nearby before narration. Per ADR-042 notes, the tag is optional but recommended for placement awareness.

5. **History seeds as voice:** the narrator extracts and uses voice mannerisms from history_seeds. Write Brecca's tics, Brecca's pauses, Brecca's way of speaking the ledger. Write the rope-keepers' reasons for staying or stopping.

6. **No OCEAN invention:** OCEAN is optional but recommended (per ADR-042). If you author it, make it canon-consistent with beneath_sunden's grave tone and the NPC's role. Brecca should feel competent, conscientious, emotionally reserved, somewhat disagreeable (the ledger is not kind), stable (she is the one constant at Ropefoot).

7. **Accept the acceptance criteria:** the story is done when pregen shows `total_authored > 0` for beneath_sunden and the validator passes.
