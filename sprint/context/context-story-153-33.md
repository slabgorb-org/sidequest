# Story Context: 153-33 — SWN Chargen Backgrounds & Foci Authoring

## Story Metadata
- **Story ID:** 153-33
- **Epic:** 153 (Playtest follow-ups — open findings)
- **Type:** Bug
- **Points:** 3
- **Workflow:** TDD
- **Repository:** sidequest-content
- **Priority:** P2

## Problem Statement

Story 153-4 fixed the SWN narrative character generation attribute spread (applying the WN 14-to-7 differentiated array instead of flat point-buy), but deferred the skills/foci granting portion as a content-authoring task: **space_opera defines NO backgrounds.yaml or foci.yaml files**, so `contribute_background_skills()` and `contribute_foci()` in the ruleset run with empty inputs on every chargen.

The server-side wiring (ADR-142/143 ruleset-owned chargen) is ready and fully tested (153-4 proofs); the content gap is the blocker. Chargen must grant skills and foci per the WWN SRD §1.3 (backgrounds → free_skill + quick_skills at level 0) and §1.5 (foci → first level of each chosen focus).

## Acceptance Criteria

1. **Space Opera backgrounds.yaml authored:**
   - Define 4–6 background origins (flavor anchored to the space_opera narrative canon: starship crews, political houses, frontier colonies, corporate servitude, etc.)
   - Each background carries a `free_skill` (trained at level 0) and `quick_skills[]` (all taken at level 0)
   - All skill names resolve to entries in a space_opera-specific `skills.yaml`
   - Backgrounds integrate with the existing `char_creation.yaml` chargen scenes (the `origins` scene references background IDs)

2. **Space Opera foci.yaml authored:**
   - Define 6–10 foci (specialized training/expertise tied to the genre: pilot tricks, diplomat's network, soldier's weapon mastery, technician's systems knowledge, etc.)
   - Each focus has at least a level-1 entry with one or two skills and a signature ability (mechanical_effect per ADR-095)
   - Foci integrate with the existing chargen scene (the `archetype` scene references focus IDs)
   - Abilities must be mechanically sound and genre-appropriate, not overlapping with class signature abilities

3. **Space Opera skills.yaml authored:**
   - Define the full SWN skill list adapted to the space_opera setting
   - Map the WWN canonical skill names (Administer, Connect, Convince, Craft, Exert, Heal, Know, Lead, Magic, Notice, Perform, Pray, Punch, Ride, Sail, Shoot, Sneak, Stab, Survive, Trade, Work) to space_opera flavor where applicable
   - Include any pack-specific extensions (e.g., Pilot, Engineer, Hack for space-tech flavor)

4. **Wiring test proves chargen integration:**
   - Integration test drives the real space_opera pack through the full narrative chargen flow
   - Assert that the character's final skill snapshot includes contributions from backgrounds + foci
   - Verify OTEL spans fire for background_skills and foci_applied

5. **Acceptance criteria from 153-4 remain satisfied:**
   - SWN narrative chargen still applies the WN 14-to-7 differentiated attribute spread
   - OTEL spans for attributes, background skills, and foci are all visible on the GM panel

## Key Code Areas

**Content authoring (main work):**
- `sidequest-content/genre_packs/space_opera/backgrounds.yaml` — **to be authored**
- `sidequest-content/genre_packs/space_opera/foci.yaml` — **to be authored**
- `sidequest-content/genre_packs/space_opera/skills.yaml` — **to be authored**

**Chargen scene definitions (already exist):**
- `sidequest-content/genre_packs/space_opera/worlds/*/char_creation.yaml` — references background/focus IDs

**Server-side wiring (already live from 153-4):**
- `sidequest-server/sidequest/game/builder.py` — invokes `contribute_background_skills()` and `contribute_foci()`
- `sidequest-server/sidequest/game/ruleset/without_number.py` — the SWN ruleset subclass that grants skills/foci
- Tests in `tests/game/ruleset/test_153_4_swn_shaped_spread.py` and integration tests prove the wiring

## Technical Notes

- **WWN SRD § 1.3:** background grants are one `free_skill` (trained at level 0) + multiple `quick_skills` (all level 0). The builder merges using max-semantics (takes the highest grant level per skill) across scene origins, background, and foci.
- **WWN SRD § 1.5:** focus grants are the skills + abilities for the *first level only* (not multi-level progression). A character picks 1–3 foci during chargen; each contributes its level-1 skills and signature ability.
- **SWN flavor vs. WWN base:** SWN (Stars Without Number) is the space-opera variant of the Without Number ruleset family. The skill names follow WWN canon (the 20-skill set above), but flavor is "crew roles on a starship, interstellar politics, salvage, trading, dogfighting" instead of "feudal magic, pacts, and inherited debts."
- **Skill names are not invented; they come from the SWN SRD.** Do not create new skills to fill gaps — instead, adapt the existing SWN skills to the space_opera flavor or pick the closest fit from the standard list.
- **ADR-091 (culture-corpus Markov naming):** if space_opera defines its own background flavor, consider tying background descriptions to the existing culture corpus so character names and origins coordinate (optional enhancement, not required for AC).

## Story Scope

This story completes the deferred AC-2 from story 153-4. It is **content authoring only** — no server changes, no mechanical additions beyond what SWN already defines. The server-side wiring is proven live; this story provides the content that makes it visible.

## Constraints

- **Use only WWN/SWN SRD skill names and mechanics.** Do not invent new skills or homebrew abilities.
- **Skills must exist in `skills.yaml` before a background or focus references them.** Silent mismatches are forbidden (CLAUDE.md No Silent Fallbacks).
- **Backgrounds and foci must not duplicate class signature abilities** (ADR-095 — one per class, per-class differentiation). The class mechanical surface is distinct from focus abilities.
- **Do not author per-world overrides yet.** The three worlds (aureate_span, coyote_star, perseus_cloud) may later author world-specific backgrounds/foci that replace the genre set; this story authors only the genre-tier defaults.

## References

- **Story 153-4 session:** `sprint/archive/153-4-session.md` (see Delivery Findings section for the content gap)
- **ADR-142:** Without Number Core Extraction (attribute spread, SWN chargen flow)
- **ADR-143:** WN Combat Owns the WN Round (ruleset-owned chargen seam)
- **ADR-095:** Class Mechanical Surface — One Signature Ability Per Non-Magical Class
- **ADR-091:** Culture-Corpus + Markov Naming
- **WWN SRD §1.3–§1.5:** Background and Focus rules (referenced in server code)

---

## Development Notes

1. Start by reviewing the heavy_metal pack's backgrounds.yaml and foci.yaml to understand the structure and flavor depth expected
2. Draft 5–6 space_opera-specific backgrounds anchored to the core genre themes (starship roles, political factions, frontier origins)
3. Draft 8–10 foci reflecting specializations available to any class (pilot expertise, diplomatic training, tech skills, etc.)
4. Author `skills.yaml` with the full SWN skill list + space_opera flavor re-descriptions
5. Write integration tests that drive the full chargen path and assert background/foci contributions appear in the final character
6. Verify OTEL spans fire for chargen attributes, background_skills, and foci_applied on the GM panel
