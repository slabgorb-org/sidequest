---
parent: context-epic-53.md
workflow: tdd
---

# Story 53-4: OTEL spans: rig_pool delta + rig_crash_event per ADR-031

## Business Context

The rig is the Road Warrior's diamond — the rider plus the vessel. Stories 53-1/2/3 made the pool model, materializer, and crash handler real. Without watcher visibility, the GM panel can't see whether the rig subsystem is actually engaged during play; per CLAUDE.md's OTEL Observability Principle, Claude can write convincing narration about a rig taking damage even when no `RigComposurePool` exists or no delta has been applied. That is the failure mode this story prevents: the spans are the lie detector. The audience is Keith-the-GM and Sebastien-the-mechanics-player (see CLAUDE.md "Who This Is For") — both need the dashboard to surface the rig delta + crash decisions to validate that the road_warrior genre is mechanically alive.

ADR-031 defines the Game Watcher three-layer model; ADR-090 documented the post-port restoration that introduced `WatcherSpanProcessor` (sidequest-server/sidequest/server/watcher.py) and the `watcher_hub` fan-out (sidequest-server/sidequest/telemetry/watcher_hub.py). The rig subsystem must hook into both — Layer 2 (`tracing` spans on decision points) and the watcher dispatch path that the GM panel reads.

## Technical Guardrails

### Span constants and registration (already in place — 53-1/53-3)
- `sidequest-server/sidequest/telemetry/spans/rig.py` defines `SPAN_RIG_POOL_CREATED`, `SPAN_RIG_POOL_DELTA`, `SPAN_RIG_POOL_ZERO_CROSSING`, `SPAN_RIG_POOL_CRASH_EVENT` and registers all four in `FLAT_ONLY_SPANS`.
- Emit sites: `rig_composure_pool.py::model_post_init` (created), `apply_delta` (delta + zero_crossing), and `rig_crash.py::handle_rig_crash` (crash_event).
- Use the same `Span.open(...)` context-manager pattern other rig spans use; do not introduce a parallel emission mechanism (memory `[[one_mechanism_per_problem]]`).

### What the story must finish

**1. Watcher-publish wiring for the four rig spans.** Today the `Span.open(...)` block emits to the OTEL tracer pipeline only. The `magic.working` span (see `tests/magic/test_magic_span.py`) is the precedent: alongside the tracer span, the emission code calls a `_watcher_publish(...)` helper (or routes via `SPAN_ROUTES`) so the watcher_hub fans the event to connected GM-panel subscribers without depending on a tracer provider being installed. The four `rig_pool.*` spans currently appear in `FLAT_ONLY_SPANS`, so they bypass `SPAN_ROUTES`; the GM panel sees nothing unless a tracer with the WatcherSpanProcessor is installed in test/runtime. Pick **one** approach for the wiring — either a direct watcher publish at each emit site (magic precedent) or a `SPAN_ROUTES` registration removing them from FLAT_ONLY_SPANS — and apply it consistently. Do not ship "both paths just in case."

**2. `rig_pool.crash_event` attribute completeness per ADR-031 Layer-2 contract.** ADR-031 specifies that Layer-2 spans capture "what was decided and why." The crash event currently emits `character_id, chassis_id, location, attacker` — the *inputs* — but not the *decisions*: Edge delta applied (`-1` per `DRIVER_EDGE_HIT`), injury status added, dismount status added, post-crash Edge value. The GM panel cannot show "this crash caused dismount" from the current attrs; the operator has to cross-reference narration. The crash_event span MUST include the three consequence outcomes as attributes so the dashboard renders the crash deterministically.

**3. `rig_pool.delta` outcome attrs are sufficient as-is.** `character_id, chassis_id, delta, old_current, new_current` is the complete decision record — no expansion needed.

### Constraints
- **No content-coupled tests.** Use fixture pools and synthetic `CreatureCore` instances (memory `[[no_content_coupled_tests]]`). The road_warrior pack is not a test dependency.
- **No silent fallbacks.** If `watcher_hub.publish_event` is not bound (e.g., no event loop), the emit must either propagate the error or be a documented no-op on a single, explicit code path — never two paths that "try one then the other" (memory `[[no_fallbacks_hard]]`, `[[one_mechanism_per_problem]]`).
- **Wiring test mandatory.** Per CLAUDE.md "Every Test Suite Needs a Wiring Test," at least one test must drive a span through the real watcher pipeline (`watcher_hub.subscribe(_Sock())` then drive the rig flow and assert the sock receives the event) — not just monkeypatched capture. The magic suite's `tests/magic/test_state.py::test_*` family is the precedent.
- **No source-text wiring tests.** Per `sidequest-server/CLAUDE.md` "No Source-Text Wiring Tests": never grep production source as a wiring assertion. Behavior tests only — drive the flow, assert the span fired / event published.
- **Two OTEL streams — pick the right one.** Per memory `[[sdk_migration_otel_two_streams]]`: ADR-031 game-watcher spans (this story) are the `Span.open` → tracer-provider + `WatcherSpanProcessor` → `watcher_hub` → `/ws/watcher` path. NOT the ADR-058 Claude-subprocess HTTP/JSON `playtest_otlp` path; NOT the ADR-103 server-tracer→gRPC→Jaeger narrator-turn path. If a test reaches for `playtest_otlp.*` or the narrator gRPC harness, it's the wrong layer.

### Reference paths
- Span helpers + registry: `sidequest-server/sidequest/telemetry/spans/_core.py`, `spans/__init__.py`
- Watcher fan-out: `sidequest-server/sidequest/telemetry/watcher_hub.py`
- Watcher processor: `sidequest-server/sidequest/server/watcher.py` (`WatcherSpanProcessor`)
- Existing rig emits: `sidequest-server/sidequest/game/rig_composure_pool.py`, `sidequest-server/sidequest/game/rig_crash.py`
- Span definitions: `sidequest-server/sidequest/telemetry/spans/rig.py`
- Existing unit tests: `sidequest-server/tests/game/test_rig_composure_pool.py`, `tests/game/test_rig_crash_handler.py`, `tests/game/test_rig_pool_binding.py`
- Precedent watcher-test: `sidequest-server/tests/magic/test_magic_span.py`, `tests/magic/test_state.py` (real subscribe path)
- Precedent SpanRoute: `sidequest-server/sidequest/telemetry/spans/_core.py::SPAN_ROUTES`

## Scope Boundaries

**In scope:**
- Watcher wiring for the four `rig_pool.*` spans (created, delta, zero_crossing, crash_event), via the same mechanism used by an existing precedent (magic.working or another SpanRoute-registered span).
- `rig_pool.crash_event` attribute expansion to include the three consequence outcomes (edge_delta, edge_after, injury_status_text, dismounted_status_text — or equivalent canonical names the schema validators already use).
- Unit tests confirming the new attrs land on the span.
- Integration test that drives a rig crash through the real `watcher_hub.subscribe` path and asserts the subscriber receives the event with the consequence attrs (the canonical wiring test for this story).
- Updates to `tests/game/test_rig_composure_pool.py` and/or `tests/game/test_rig_crash_handler.py` for the new attribute shape if the existing assertions break against the expanded contract — fit tests to new shape, do not revert features (memory `[[dont_revert_features]]`).

**Out of scope:**
- New `rig.*` span types beyond the four named. The taxonomy lists ten more (bond_event, voice_register_change, confrontation_outcome — already present; subsystem install/remove, damage_resolution, ancillary_loss, etc.) — those ship with their producing subsystems, not here.
- GM panel React rendering of the new attrs (story 53-5 owns UI surface for Rig + injury tags).
- Cross-character rig events (multi-PC crash chains, dogfight rig telemetry). Single-character, single-crash here.
- Refactoring the magic.working watcher-publish path. Use it as precedent; don't change it.
- Migrating the existing `rig.bond_event` / `rig.voice_register_change` / `rig.confrontation_outcome` spans to the new wiring (those are pre-53-4 and pre-existing; keep their current shape unless the wiring approach you pick forces a uniform migration — if so, log a Design Deviation).
- ADR-090 dashboard restoration or `/ws/watcher` endpoint changes — that infrastructure exists.
- New telemetry for the materializer or other non-emit-site touches.

## AC Context

There are no explicit ACs on the sprint YAML — the title is the spec. The story title decomposes into the following testable acceptance criteria:

### AC1 — `rig_pool.delta` emits via the watcher path with damage-and-repair semantics

For each of (a) damage delta on a healthy pool, (b) repair delta from a non-destroyed pool, the watcher subscriber receives a `rig_pool.delta` event whose payload includes `character_id`, `chassis_id`, the signed `delta`, `old_current`, `new_current`. The test must subscribe via `watcher_hub.subscribe` (not by monkeypatching `_watcher_publish`), prove the event arrives, and parse the payload — proving end-to-end wiring, not just emit-site invocation. Edge cases:
- A no-op delta (`apply_delta(0)`) still publishes (the contract is "every apply_delta call publishes").
- Repeated damage on a wrecked rig (current already 0, delta=-3) publishes a delta with `new_current=0` and does NOT re-publish a `zero_crossing` event.

### AC2 — `rig_pool.zero_crossing` publishes exactly once per downward crossing

A pool with `current=3` taking `apply_delta(-3)` publishes one `rig_pool.zero_crossing` event. A subsequent `apply_delta(-1)` (still at 0) publishes zero additional crossing events. Healing back to 1 and damaging to 0 again publishes the crossing event a second time. Negative case: a `rig_pool.delta` that lands above 0 publishes NO `zero_crossing` event.

### AC3 — `rig_pool.crash_event` carries the three consequence outcomes

When `handle_rig_crash` fires, the published `rig_pool.crash_event` payload includes (in addition to the existing `character_id, chassis_id, location, attacker`):
- `edge_delta` — the Edge change applied (`DRIVER_EDGE_HIT`, currently `-1`)
- `edge_after` — the character's Edge value after the crash
- `injury_status_text` — the injury status text appended (`INJURY_STATUS_TEXT`)
- `dismounted_status_text` — the dismount status text appended (`DISMOUNTED_STATUS_TEXT`)

Attribute names should match existing schema conventions if a schema validator exists for watcher events; if there's no canonical name yet, the test pins one and Dev implements it. Negative cases:
- `handle_rig_crash` returning `None` (no pool / not destroyed / already dismounted) publishes NO crash_event.
- A pool zero-crossing where the crash handler isn't invoked still publishes `rig_pool.zero_crossing` but NOT `rig_pool.crash_event` (these are independent gates).

### AC4 — `rig_pool.created` publishes via the watcher path

Constructing a `RigComposurePool` publishes a `rig_pool.created` event with `character_id, chassis_id, current, max`. Both direct construction and round-trip `model_validate_json` paths publish (per the existing emit-site comment that round-trip loads fire so the GM panel sees every pool instance). A `model_construct(...)` (validation-bypass) path also fires, OR explicitly does not — pin the contract.

### AC5 — Integration / wiring test

A single test that uses the real `watcher_hub` async subscribe path (same shape as `tests/magic/test_state.py` lines 342–438):
1. Bind the loop.
2. Subscribe a fake socket / list-recording sendable.
3. Drive a rig sequence: construct pool → damage to crash → call `handle_rig_crash`.
4. Assert the subscriber received, in order, a `rig_pool.created`, one or more `rig_pool.delta`, exactly one `rig_pool.zero_crossing`, and one `rig_pool.crash_event` with the AC3 consequence attrs.

This is the canonical wiring test for the story.

### AC6 — Single emission mechanism

All four spans use the same emission shape (e.g., all via SpanRoute, OR all via direct `watcher_hub.publish_event` next to the `Span.open` block). No parallel paths (memory `[[one_mechanism_per_problem]]`). A test that introspects the rig.py emit functions or routing registration enforces this — preferred shape: assert the four span constants are registered in `SPAN_ROUTES` and removed from `FLAT_ONLY_SPANS` (if the chosen approach is SpanRoute), OR assert no SpanRoute entry exists for them and the four emit sites all call the same publish helper (if the chosen approach is direct publish). The test pins the choice.

## Assumptions

- **Watcher hub publish path is the canonical wiring.** Per ADR-090 the `WatcherSpanProcessor` → `watcher_hub` → `/ws/watcher` is the live restored Layer-2/Layer-3 surface. If Dev finds the path is degraded or pending another story, log a Design Deviation immediately rather than working around it.
- **`DRIVER_EDGE_HIT` is `-1` and the two crash statuses (`INJURY_STATUS_TEXT`, `DISMOUNTED_STATUS_TEXT`) are stable constants in `rig_crash.py`.** If those move during this story, fit tests to the new constants. Don't hardcode the literal text in test assertions — import the constants.
- **`SpanRoute` mechanism is the documented extension point and is preferred over a parallel publish helper if the precedent is unclear.** If both magic.working and another span use direct `watcher_hub.publish_event`, follow that; otherwise default to SpanRoute. Log the choice as a Design Deviation noting the precedent that decided it.
- **No new ADR is required.** This is an implementation of ADR-031, not an amendment to it. If the attribute schema feels load-bearing enough to need an ADR, log a Question finding rather than writing one in-flight.
- **Schema validation for watcher events.** If `watcher_hub.publish_event` enforces a typed schema (e.g., known event_type set, known field set), the new attrs may need to be added to that schema. Check before testing — a test that asserts the publish succeeds proves the schema accepts the new fields.
- **The story is 2 points.** If watcher-publish wiring + attribute expansion + wiring test grows past ~250 lines of test code or requires touching more than the four files named in Technical Guardrails, log a finding and split the story rather than ship a bloated 2-pointer.
