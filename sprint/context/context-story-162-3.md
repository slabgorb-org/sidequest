---
parent: context-epic-162.md
---

# Story 162-3: Bestiary generics section replaces ephemeral stub minting

## Business Context

This story addresses the "No Silent Fallbacks" principle from CLAUDE.md. Currently, when creature generation cannot find a suitable source (authored creature, pool, or room-bound), the system silently fabricates a stub NPC. This masks configuration problems and makes it impossible to debug which worlds need bestiary entries.

The goal is to make creatures sources explicit and loud:
1. **Authored generics**: Each world's bestiary gains a `generics` section with hand-authored generic creatures (goblin, orc, familiar, etc.) per world and genre context
2. **Last-resort fallback**: Authored generic rows become the sanctioned, explicit fallback when other sources don't apply
3. **Loud failure**: Stub fabrication (creating NPCs without a legitimate source) becomes a loud failure (error/exception) on non-degenerate paths rather than silent fallback

This cascades from epic 162-1 (derive-don't-cache Monster Manual) and 162-2 (id-keyed identity) — the new bestiary structure gives each world an explicit, authored baseline roster.

## Technical Guardrails

- **Bestiary schema**: Add optional `generics:` section to `bestiary.yaml` (world-level YAML)
  - Format: list of creature rows (same structure as other bestiary entries)
  - Per-world authored fallbacks when no other source applies
  - Inherit from genre default if not overridden

- **Origin-precedence path**: Integrate with the Green Room materializer (162-4 ADR)
  - Authored > room-bound > region-population > MM pool > **generics** > ~~narrator stub~~ (error)
  - Generics are the last _legitimate_ source before failure

- **Failure contract**: 
  - Log a blocking Finding (not warning) when stub fabrication is attempted
  - Raise an exception in non-degenerate paths (gameplay sessions)
  - Degenerate paths (e.g., test fixtures, one-off scenario generation) may emit a WARNING + synthetic creature
  - All paths must OTEL span the attempt + reason

- **No silent fallbacks**: Every NPC generation attempt must have an explicit origin (Origin enum) traceable to a bestiary source or a deliberate fallback reason

## Scope Boundaries

**In scope:**
- Add `generics:` section schema to bestiary YAML per world/genre
- Populate representative generics for 2–3 worlds (recommend high-traffic worlds: caverns_and_claudes, space_opera, neon_dystopia)
- Integrate generics into the Origin-precedence materializer (162-4 follow-up or pre-wiring)
- Replace stub-fabrication silent paths with loud error/warning + OTEL spans
- Wiring test: verify generics are used as fallback when no other source applies
- Verify no existing sessions regress (generics don't break seated encounters)

**Out of scope:**
- Authoring generics for all 22 worlds (post-story content work)
- Changing existing encounter tables or creature references
- Altering bestiary-load or schema validation (that's 162-1)
- Narrator-side "make one up" fallback (only MM/generics/authored paths)

## AC Context

| AC | Detail |
|----|--------|
| Bestiary `generics` schema defined | `generics:` section accepted in world bestiary YAML; schema validated |
| Generics integrated into materializer | Precedence path includes generics as last _legitimate_ source before error |
| Stub creation is loud | Stale stub-fabrication paths raise an exception (or loud WARNING in degenerate tests) |
| Generics fallback verified | Test: encounter-gen with no pool/room/region source falls back to bestiary generics (if available) |
| No regressions | Existing sessions with MM-derived creatures still work; no breakage on seated NPCs |
| OTEL spans on all paths | Every NPC-gen attempt logs origin (authored/room/region/MM/generic) and any fallback reason |

---

_Derived from `pf context create story 162-3` on 2026-07-05._
