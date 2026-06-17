# Story 122-8 — Relocate _KIND_TO_MESSAGE_CLS to Protocol Tier

**Epic:** 122 — Honest Layering

**Type:** Refactor

**Points:** 2

**Workflow:** tdd

**Repository:** server (sidequest-server)

## Purpose

Eliminate the last grandfathered upward-import edge that violates ADR-147's layering law. The dict `_KIND_TO_MESSAGE_CLS` currently lives in `sidequest/server/session_handler.py` but is reached from `sidequest/game/projection/validator.py` via lazy imports. Moving it to the protocol tier (which sits below all domain packages) allows the layering guard to enforce the law fully.

## Problem Statement

ADR-147 establishes one import-direction law:

```
foundation <- {game, genre, orbital, magic, interior} <- server
```

The layering guard (`tests/infrastructure/test_import_direction_guard.py`) currently grandfathers exactly one violation: `game/projection/validator.py` importing `_KIND_TO_MESSAGE_CLS` from `sidequest.server.session_handler`. This is a temporary exception pending the design work to relocate the dict.

## Solution

Relocate `_KIND_TO_MESSAGE_CLS` from `sidequest/server/session_handler.py` to `sidequest/protocol/messages.py` (or a new `sidequest/protocol/registry.py` if preferred). The protocol tier imports-downward-only, so this move eliminates the upward edge and allows the grandfather exception to be deleted.

### Key Constraints

- **Immutability:** The dict must be module-level and immutable (a frozenset of kinds, or constructed once and frozen)
- **Wiring:** Both call sites (session_handler and validator.py) must import from the new location
- **No circular imports:** protocol tier must remain import-safe for server/ and game/
- **Test coverage:** Integration test must verify the registry is wired and reachable from production code paths

## Acceptance Criteria

1. **Relocation:**
   - `_KIND_TO_MESSAGE_CLS` dict moved to protocol tier
   - Exported via `sidequest/protocol/__init__.py`
   - Immutable module-level definition

2. **Imports Updated:**
   - `server/session_handler.py` imports from protocol tier
   - `game/projection/validator.py` imports from protocol tier (no upward edges to server)
   - All call sites preserve their behavior

3. **Layering Guard Tightened:**
   - Grandfather exception for `game/projection/validator.py` deleted from `GRANDFATHERED` dict
   - Self-expiry test block removed or simplified
   - Guard passes: `uv run pytest tests/infrastructure/test_import_direction_guard.py -v`

4. **Test Coverage:**
   - Full test suite passes: `uv run pytest -v`
   - Integration test added verifying protocol registry is wired and reachable

5. **PR Merged:**
   - Feature branch merged to develop
   - Story marked done

## Technical Context

- **_KIND_TO_MESSAGE_CLS location:** `sidequest/server/session_handler.py` lines 66–90
- **Current consumers:**
  - `server/session_handler.py` — line 202 (`_build_message_for_kind`), line 226
  - `server/emitters.py` — re-exported from session_handler (back-compat)
  - `game/projection/validator.py` — lazy imports in `_filter_reachable_kinds` and `_schema_fields_for_kind`
- **Guard location:** `tests/infrastructure/test_import_direction_guard.py` lines 87–95 (GRANDFATHERED dict) + lines 267–281 (self-expiry test)
- **Related ADR:** ADR-147 ("Honest Layering — Pure Logic & Utilities Below the Server Tier")

## Notes

- This is a pure refactoring; no behavioral change
- The dict contents do not change, only the location
- Lazy imports in validator.py can become direct imports once the dict is in the protocol tier
