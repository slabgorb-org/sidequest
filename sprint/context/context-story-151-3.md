---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-3: action_rewrite → IntentRouter pre-pass

## Business Context

`action_rewrite` (`you`/`named`/`intent`) is a mechanical transform of the player's
*own submitted action* — it needs nothing from the narrator's prose. Today it's
emitted as a sidecar field by the narrator, then its `.named`/`.intent` *feed*
visibility classification that runs *after* the narrator — an ordering hazard (the
turn that emits the field is the one whose visibility it's meant to gate). Moving it
to the pre-narration `IntentRouter` (which already reads the action and resolves
referents) closes that hazard and removes one field from the narrator's load. This
story is independent of the extractor (151-2) and can run in parallel.

## Technical Guardrails

- **Emit from** `sidequest/agents/intent_router.py` — produce `action_rewrite`
  (you/named/intent) from the player action it already reads.
- **Rewire** `sidequest/server/visibility_classifier.py` (`:124-129`) to read the
  pre-pass `action_rewrite` instead of the post-narration sidecar value.
- **Retire** the field from `output_only.md` PART 2 and from
  `NarrationTurnResult`/`_extract_game_patch_json` parsing. Add a retirement guard.
- **Atomic:** retire the sidecar emission in the same change that lights the pre-pass
  emission — never two producers for one field (*one mechanism per problem*).
- **OTEL:** `intent_router.action_rewrite` (emitted/derived).
- Keep the existing default fallback (omitted → `"unspecified"`) as the loud net
  during transition.

## Scope Boundaries

**In scope:**
- IntentRouter emits `action_rewrite`; `visibility_classifier` rewired; sidecar field
  retired; retirement guard test; `intent_router.action_rewrite` span.

**Out of scope:**
- All other sidecar fields and the post-extractor (151-2/4/5).

## AC Context

1. **Pre-pass emits:** `IntentRouter` outputs `action_rewrite` with you/named/intent
   derived from the player's raw action.
2. **Consumer rewired:** `visibility_classifier` reads the pre-pass value; visibility
   classification still routes correctly (the ordering hazard is closed — assert that
   classification no longer depends on the post-narration sidecar).
3. **Span:** `intent_router.action_rewrite` fires.
4. **Retired:** `output_only.md` no longer instructs the narrator to emit
   `action_rewrite`; `NarrationTurnResult` no longer parses it from `game_patch`
   (retirement guard asserts this).
5. Full suite (with content) green.

## Assumptions

- The `IntentRouter` has the player action and referent resolution available
  pre-narrator (it does today).
- `visibility_classifier`'s only dependency on `action_rewrite` is `.named`/`.intent`.
