---
parent: context-epic-71.md
workflow: tdd
---

# Story 71-28: OTEL-coverage split — encounter beats land in events table but emit no watcher spans (live GM panel half-blind)

> Recovered during TEA red-phase gate (sm-setup did not produce a separate
> context file; full context was inline in the session). Same recovery shape
> as 71-... / 61-19. Material drawn from the session file, epic-71 context,
> and a live code investigation of the OTEL span-routing subsystem
> (2026-05-30).

## Business Context

The GM panel is the project's **lie-detector** — the only mechanism that
distinguishes a subsystem actually firing from the narrator improvising
convincing prose with zero mechanical backing (CLAUDE.md OTEL Observability
Principle; ADR-031 / ADR-090 / ADR-103). Every subsystem *decision* must emit a
typed watcher event so the dashboard's `state_transition` tab can show it live.

Advancing an encounter beat — moving a confrontation from one phase to the next
— is exactly such a decision. The `advance_encounter_beat` WRITE tool fires, the
beat counter mutates, the change persists, and the dispatch span carries the
before/after beat numbers. **But there is no routing decision for that span**,
so the watcher translator emits only a bare `agent_span_close`; the typed
`state_transition` the GM panel listens for never arrives. The GM cannot tell
whether beats are advancing or stuck. This is precisely the half-blindness the
OTEL principle exists to prevent — and it sits at the seam Sebastien & Jade care
about most (the confrontation/beat engine they ran a 140-turn game around).

Note: this is a **Keith/dev observability** concern (GM panel + OTEL), not a
player-facing surface. It serves the developer's ability to verify the engine
works, per the CLAUDE.md caution against attaching player names to backend OTEL.

## Technical Guardrails

**Verified live in code, 2026-05-30:**

1. **The tool** — `sidequest/agents/tools/advance_encounter_beat.py`. Loads the
   snapshot, mutates `encounter.beat` (auto +1, or to an explicit `to_beat`),
   saves, and sets three OTEL attributes on `ctx.otel_span`:
   `tool.encounter.beat_from`, `tool.encounter.beat_to`, `tool.encounter.reason`.
   It does **not** currently set `tool.encounter.encounter_type` (though
   `encounter.encounter_type` is in scope — it is returned in the tool payload).

2. **The dispatch span** — `Registry.dispatch` (`tool_registry.py:196`) opens
   `tool_dispatch_span(name="advance_encounter_beat", category=WRITE)`, which
   produces the span name **`tool.write.advance_encounter_beat`** and swaps it
   into the handler's `ToolContext.otel_span` via `dataclasses.replace`. The
   tool's attribute writes land on this span.

3. **The routing registry** — `sidequest/telemetry/spans/_core.py`:
   `SPAN_ROUTES: dict[str, SpanRoute]` keyed by span name. `SpanRoute` is a
   frozen dataclass `(event_type: str, component: str, extract: Callable[[span], dict])`.
   Existing encounter routes live in `sidequest/telemetry/spans/encounter.py`
   (`SPAN_ENCOUNTER_PHASE_TRANSITION`, `SPAN_ENCOUNTER_BEAT_APPLIED`, …) — copy
   that pattern.

4. **The watcher path** — `WatcherSpanProcessor.on_end(span)`
   (`sidequest/server/watcher.py`) looks up `SPAN_ROUTES.get(span.name)`; if
   present, calls `route.extract(span)` and `hub.publish({component, event_type,
   fields, …})`. `PgTelemetrySink` persists published events to the `events`
   table. **No `turn_telemetry` hop is involved** in the typed-event path.

5. **Why the gap was invisible** — `tests/telemetry/test_routing_completeness.py`
   enforces a routing decision for every module-level `SPAN_*` *constant*. The
   dispatch span name is **constructed dynamically** (`tool.{cat}.{name}`), so it
   is not a `SPAN_*` constant and the static lint never required a decision for
   it. Any fix that introduces a `SPAN_*` constant for it will *also* be policed
   by that lint going forward.

**Test harness:** `tests/integration/test_combat_otel_wiring.py` is the canonical
end-to-end pattern — local `TracerProvider` + `WatcherSpanProcessor`, monkeypatch
`spans_module.tracer` (the dispatch span resolves its tracer via `Span.open` →
`spans.tracer()`, so the monkeypatch intercepts it), subscribe a fake socket,
drive the real path, assert the typed event. **No source-text wiring tests**
(CLAUDE.md): drive the flow and assert the span/event, never grep source.

## Scope Boundaries

**In scope (sidequest-server only):**
- Register a `SPAN_ROUTES` entry for `tool.write.advance_encounter_beat`
  (`event_type=state_transition`, `component=encounter`) extracting the beat
  transition into typed fields.
- Set `tool.encounter.encounter_type` on the dispatch span in the tool so the
  route can surface encounter context (the value is already in scope).
- Wiring test proving the full path; keep existing unit tests green.

**Out of scope:**
- GM-panel reader / dashboard UI changes (sidequest-ui) — if the reader needs
  downstream work, file a follow-up; do not expand this story into the UI.
- Reworking `SPAN_ENCOUNTER_BEAT_APPLIED` (a *different*, engine-side span with a
  live route) — leave it alone.
- Any change to beat-advance *mechanics* (counter logic, encounter resolution).
  This story is observability only.

## AC Context

1. **Route defined** — `SPAN_ROUTES` entry for the dispatch span maps
   `tool.encounter.*` attributes to watcher event fields.
2. **Consistency** — span/extraction consistent with existing beat-related
   encounter routes (mirror `SPAN_ENCOUNTER_PHASE_TRANSITION` /
   `SPAN_ENCOUNTER_BEAT_APPLIED`).
3. **Wiring test (load-bearing)** — exercises tool call → dispatch span →
   `WatcherSpanProcessor` → `SPAN_ROUTES` extraction → hub publish; asserts the
   typed event is a `state_transition` carrying non-null `beat_from`, `beat_to`,
   and `encounter_type`.
4. **No regressions** — existing `advance_encounter_beat` unit tests and
   encounter telemetry tests stay green.
5. **Attribute/extraction alignment** — the tool's `ctx.otel_span` attributes
   match the route's extraction keys (adding `encounter_type` is required to
   satisfy AC3).
6. **Decision documented** — session-file note on whether `SPAN_ROUTES` was the
   right seam or whether the GM-panel reader needs additional downstream wiring.
