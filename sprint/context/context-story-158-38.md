# Story 158-38 Context

## Title
Pronoun/POV localizer residuals after 158-8/14 — verb-agreement stays 3rd-person-singular after name->you swap (does you / grips); solo resume/replay still drops the POV swap entirely

## Description
Two residual defects surfaced in playtests after stories 158-8 and 158-14 (which built the _apply_pov_swap / pronoun-localizer infrastructure). Both involve the POV localization not being applied in all cases:

1. **VERB-AGREEMENT defect (pingpong 2026-06-23, MP beneath_sunden):** When the name->you swap is applied, the subject pronoun is correctly swapped but the governing verb stays 3rd-person-singular. Examples:
   - "Which way does you mean to go" (should be "do you")
   - "You check the anchor then grips the rope and swing" (should be "grip")
   The localizer swaps the name/pronoun but fails to re-conjugate all verb positions that depend on the swapped subject.

2. **SOLO RESUME/REPLAY defect (pingpong 2026-06-24):** When a player reconnects and resumes a session, stored prose is re-emitted without the POV swap applied to the resuming player. The prose re-emits in 3rd-person (stored form) instead of 2nd-person (per recipient's POV). Example:
   - Live narration: "You touch flame"
   - Resume/replay: "Zeppo touches flame" (acting player's own PC still in 3rd person)
   
   This is because _apply_pov_swap runs only at live-emit time (in emit_event when building per-recipient payloads). During resume/replay (ADR-133 full-replay mirror), stored narration events are reconstructed and re-emitted from the event log, but the POV swap is not re-applied to the replayed prose.

Both are cosmetic but immersion-breaking on the acting player's own screen.

## Technical Context

### Current POV Swap Implementation

**File:** `sidequest-server/sidequest/agents/pov_swap.py`

The **_apply_pov_swap** function (sidequest/server/emitters.py:274) handles 2nd-person localization:
- Called from `emit_event` to rewrite narration prose for each recipient
- Takes the anchor PC's prose and swaps target references (names, pronouns) based on the **recipient**'s PC
- Uses the `swap_to_second_person` function from pov_swap.py which:
  - Performs **multiple passes** to swap PC name → "you"
  - Applies **clause-local pronoun gating** to avoid NPC-bleed (ADR-153-29)
  - Conjugates verbs that follow the swapped subject
  - Preserves dialogue unchanged

**Verb conjugation:** `_conjugate()` converts 3rd-person-singular verbs to their 2nd-person forms:
- Irregular verbs handled explicitly (has→have, does→do, is→are, was→were, etc.)
- Regular suffixes (-s, -es, -ies) removed algorithmically
- The `_looks_like_verb()` heuristic identifies which words need conjugation
- Verb agreement is handled at conjugation time, not after

**AC-related from 158-14 hardening:**
- Non-canonical pronouns are projected to a canonical set (she→she/her, they→they/them, custom→they/them)
- Empty/invalid pronouns result in skipped swap with an OTEL span
- Character.pronouns can be freeform (chargen permits it); the localizer receives a canonical projection

### Resume/Replay Path (ADR-133)

**File:** `sidequest-server/sidequest/handlers/connect.py:1476-1620`

When a player reconnects:
1. Projection cache reads cached event payloads (if available)
2. Fallback: event log is read and ProjectionFilter applied live
3. Messages are rebuilt from the cached/filtered payloads via `_build_message_for_kind()`
4. The rebuilt messages are sent to the reconnecting player as a replay
5. **POV swap is NOT applied** — the prose is replayed byte-identical to what the cache stored

The issue: replay reconstruction happens in the connect handler, not in emit_event. The POV swap (which decorates payloads per-recipient in emit_event) is not part of the replay path. The narrative_log is empty on resume per ADR-133 (full-replay uses stored turn events, not the narrative_log); the stored prose carries the original 3rd-person form written by the narrator.

## Acceptance Criteria

1. **Verb-agreement fix:** After a name→you swap, all verbs conjugated to 2nd-person form, not just the immediate verb following the subject. Specifically:
   - Coordinated verbs after "and" or "," are re-conjugated (story example: "grips"→"grip")
   - The existing `_looks_like_verb()` / `_conjugate()` logic must cover these secondary positions
   - No over-conjugation of non-verbs (nouns, adjectives, possessives remain unchanged)
   - Lie-detector OTEL: narration.second_person_swap span includes a count of distinct substitutions per clause

2. **Resume/replay POV swap:** Replayed narration events apply _apply_pov_swap on reconnect, preserving per-recipient POV:
   - When a NARRATION message is rebuilt from cache/storage during connect replay, apply POV localization per recipient before sending
   - The recipient_player_id must be available at replay-build time
   - Canonical prose (3rd-person, as stored) is swapped to 2nd-person only for the acting player's own PC
   - Other recipients get the unswapped prose (3rd-person narrator voice for the anchored PC)
   - Lie-detector OTEL: log narration.pov_swap_skipped/narration.second_person_swap spans on replay path with origin='replay' marker

3. **No regression:** Existing tests pass (158-8 and 158-14 test suites); the verb-agreement pass does not over-apply to dialogue or NPC names; the replay path does not double-swap or corrupt narrative already-localized during live emit.

## Design Decisions

- **Verb-agreement:** The existing conjugation machinery is sound; the issue is likely incomplete pattern matching on secondary verbs in coordinated clauses. Extend the verb-agreement passes to capture more syntactic positions.
  
- **Resume/replay POV swap:** Add POV localization to the replay path in connect.py. The swap must be guarded the same way as live emit (pronouns validation, recipient in snapshot check) and must emit the same OTEL spans so the GM panel sees replay vs. live consistency.

- **Avoid cosmetic-only tooling:** The two defects are immersion-breaking for the player but do not affect game state or mechanical resolution. Both are pure narration-layer concerns. Fix them cleanly without altering the game/event log/ruleset substrate.

## Metadata
- **Story ID:** 158-38
- **Epic ID:** 158
- **Type:** bug
- **Repos:** server
- **Workflow:** tdd (red-green-refactor; tests first, then implementation)
- **Points:** 3 (p3 priority)

---
_Generated by sm-setup from sprint YAML and upstream story research._
