---
parent: context-epic-72.md
workflow: trivial
---

# Story 72-14: Replace source-text wiring test with OTEL-span/behavior assertion

## Business Context

Epic 72 (NPC Identity Hardening) proves the combat-edge handshake actually
publishes `current/max` edge onto the opponent NPC at encounter start. The wiring
is verified — but one of the tests proves it the *wrong way*: it reads the
production module's **source text** and counts substring occurrences. A source-
text count is brittle (renames, refactors, or a helper moving files break it
without any behavior change) and it proves nothing about runtime — it only proves
the string appears twice in a file. This violates the project's OTEL doctrine:
the GM panel is the lie detector, so wiring should be proven by a span emitted on
the real path, not by grepping the source.

## Technical Guardrails

**The offending test (sidequest-server):**
- `tests/server/test_npc_registry_combat_stats.py::test_helper_is_called_from_production_handshake_path`
  (lines ~290–307). It does:
  ```python
  src = Path(encounter_lifecycle.__file__).read_text(...)
  assert "_publish_combat_edge_to_npcs(" in src
  assert src.count("_publish_combat_edge_to_npcs(") >= 2
  ```
  Replace this body with a behavior/OTEL assertion that proves the **production
  encounter-init path** calls the helper.

**The wiring already proven correctly — reuse these patterns:**
- `test_otel_span_emitted_on_npc_edge_publish` (same file, line ~238) already
  drives `trigger_encounter(snap, pack, "combat", ...)` (the real production path)
  and asserts on the emitted span (`source == "encounter_handshake"`). The
  replacement should assert the same span fires — proving the helper ran in prod,
  not that its name appears in a file.
- `tests/_helpers.trigger_encounter` is the production-path driver; `otel_capture`
  is the span-capture fixture already imported in this file.
- Production symbol lives in `sidequest/server/dispatch/encounter_lifecycle.py`
  (`_publish_combat_edge_to_npcs`); the span is defined in
  `sidequest/telemetry/spans/` (NPC edge-publish span, `source=encounter_handshake`).

**Do not** delete the *behavior* coverage — only replace the source-counting
assertion. If the OTEL-span test (line 238) already fully covers "the helper ran
on the prod path," the source-text test is redundant and can be removed outright
rather than rewritten; pick whichever leaves clean, non-overlapping coverage and
note the choice as a deviation.

## Scope Boundaries

**In scope:**
- Replace/remove `test_helper_is_called_from_production_handshake_path` in
  `test_npc_registry_combat_stats.py` with a span/behavior assertion.
- One repo: `sidequest-server`.

**Out of scope:**
- Any change to production code (`encounter_lifecycle.py`, span definitions).
- The other `_publish_combat_edge_to_npcs` callers/tests in `tests/integration/`
  and `tests/server/dispatch/` (72-8, 72-12) — leave them alone.

## Acceptance Criteria

1. `test_npc_registry_combat_stats.py` no longer asserts on source-text
   occurrence counts (`src.count(...)`, `read_text` of a prod module).
2. The wiring guarantee ("the helper runs on the real encounter-init path") is
   proven by an OTEL-span assertion (or behavior assertion via `trigger_encounter`)
   instead.
3. `just server-test` for this file passes; no other tests regress.
