---
parent: context-epic-64.md
workflow: tdd
---

# Story 64-6: Fix circular import — WebSocketSessionHandler back-compat re-export cycle

## Business Context

A pre-existing import cycle makes a dungeon test unrunnable in isolation:
`tests/dungeon/test_region_projection_wiring.py::test_dungeon_map_frame_is_emitted_to_ui`
fails with `ImportError: cannot import name 'WebSocketSessionHandler' from
partially initialized module 'sidequest.server.websocket_session_handler'
(most likely due to a circular import)`. Surfaced during epic 64 review (it is
unrelated to content). Beyond the one red test, the cycle is a latent hazard
for anything that imports the server graph in a fresh interpreter — including
64-4's content-validation pass, which pulls in `genre.loader` and can
transitively reach these modules. Fixing it unblocks isolated test runs and
removes a landmine on the validator's import path.

## Technical Guardrails

**The cycle:**
- `sidequest/server/session_handler.py:640` re-exports
  `WebSocketSessionHandler` and `_populate_opening_directive_on_chargen_complete`
  *from* `websocket_session_handler.py` (a back-compat re-export, `# noqa:
  E402`).
- `sidequest/server/websocket_session_handler.py:144` imports `_SessionData`,
  `_State`, `_build_pc_descriptor`, `_hash_snapshot`,
  `_shared_world_delta_to_state_delta`, `_AUDIO_INTERPRETER` *back from*
  `session_handler.py`.
- Whichever module the interpreter imports first can observe the other
  half-initialized.

**Approaches (pick the smallest that breaks the cycle):**
- Move the shared leaf types/helpers (`_SessionData`, `_State`,
  `_build_pc_descriptor`, `_hash_snapshot`, `_shared_world_delta_to_state_delta`,
  `_AUDIO_INTERPRETER`) into a leaf module that both import, so neither depends
  on the other at import time. Preferred — turns the diamond into a tree.
- Or, if the `session_handler.py:640` re-export of `WebSocketSessionHandler`
  has no remaining importers, drop it (and update any consumers). Verify with a
  repo-wide grep for `from sidequest.server.session_handler import
  WebSocketSessionHandler` before deleting — per the dead-code rule, remove it
  fully in this PR rather than leaving a shim.

**Constraints:**
- This is a server refactor, not a behavior change — no new functionality.
- Do not paper over with a function-local import unless it is genuinely the
  cleanest break; prefer relocating the shared types.
- Verify the fix structurally: import each module *first* in a fresh
  interpreter and confirm both succeed.

## Scope Boundaries

**In scope:**
- Break the `session_handler` ↔ `websocket_session_handler` import cycle.
- Make the failing dungeon test pass in isolation.
- Update any import sites touched by relocating the shared symbols.

**Out of scope:**
- The validator content-validation work (64-4/64-5) — this only removes the
  import hazard those stories sit behind.
- Any change to WebSocket behavior, session semantics, or the dungeon
  map-frame emission logic the test exercises.
- Broader server import-graph cleanup beyond what this one cycle requires.

## AC Context

1. **`test_region_projection_wiring.py::test_dungeon_map_frame_is_emitted_to_ui`
   passes in isolation.** Test: `uv run pytest
   tests/dungeon/test_region_projection_wiring.py::test_dungeon_map_frame_is_emitted_to_ui`
   in a clean process → PASS (currently ImportError at session_handler.py:640).
2. **No import cycle between the two modules.** Verify structurally: in a fresh
   interpreter, `python -c "import
   sidequest.server.websocket_session_handler"` and, separately, `python -c
   "import sidequest.server.session_handler"` both succeed regardless of order.
   A small test importing each first is acceptable (this is a runtime-type /
   import check, not a banned source-text grep).
3. **Full dungeon suite green; no server regression.** Test: `uv run pytest
   tests/dungeon/` green, and the wider server suite shows no new failures
   attributable to the symbol relocation.

## Assumptions

- The cycle is exactly the two-module back-compat edge described; if a third
  module participates, widen the leaf-extraction accordingly and log a
  deviation.
- The shared symbols (`_SessionData`, `_State`, etc.) can be relocated without
  dragging their own heavy imports back into the cycle — confirm the chosen
  leaf module stays a leaf.
- The `WebSocketSessionHandler` re-export at `session_handler.py:640` exists for
  back-compat; check for live importers before deciding relocate-vs-delete.
