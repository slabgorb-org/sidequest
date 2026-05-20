# Epic 24: Procedural World-Grounding Systems

## Overview

Anti-mode-collapse infrastructure: weather, demographics, NPC schedules, economy, establishments, calendar — following Monster Manual pattern (ADR-059; note drift, successor pointer ADR-087 — implementer reads both). Phase 1: schemas + tea_and_murder/glenross proof of concept.

## Architecture

- **Backend:** Python (ADR-082 retired Rust backend); lives in `sidequest-server`
- **Content:** YAML schemas + authored packs live in `sidequest-content/genre_packs/<pack>/` alongside existing top-level pack files
- **NOT a system/milieu split:** ADR-072 (system/milieu split) is retired (historical 2026-05-02). Packs remain monolithic; grounding data goes alongside existing pack YAML.
- **Genre fit (tea_and_murder):** Cozy mystery benefits hard from grounding — Scottish-village weather/seasons drive scene framing, glenross demographics give the narrator a stable cast for "who is in the post office today", calendar gates festivals and tea-room hours.

## Story Hierarchy

1. **24-1** (done) — Define YAML schemas for weather, demographics, calendar, economy, establishments, quest shapes, NPC schedules
2. **24-2** (done) — Author tea_and_murder/glenross weather rules
3. **24-3** (done) — Author tea_and_murder/glenross demographics
4. **24-4** (backlog) — Author tea_and_murder/glenross calendar
5. **24-5** (done) — Weather generator in Python (climate YAML + RNG seed → typed weather state)
6. **24-6** (in progress) — Narrator tool call for weather + demographics + calendar grounding (ADR-102/103)
7. **24-7** (backlog) — OTEL spans for weather/demographics (ADR-031 observability)
8. **24-8** (backlog) — Playtest validation in tea_and_murder/glenross

## Key Design Decisions

- **Tool-based, not always-on injection:** 24-6 (this story) uses narrator-callable tools (ADR-102) instead of always-on VALLEY-zone prompt injection. Narrator invokes when needed → saves tokens, makes use observable.
- **OTEL-observable:** Tool invocation emits spans per ADR-103 (tool registry spans are free). Story 24-7 will wire additional observability for weather generation itself (proposed vs used).
- **Playtest-driven:** Story 24-8 validates during tea_and_murder/glenross playtest with actual players. This is the success criterion.

## Related ADRs

- **ADR-059** — Monster Manual (server-side pre-generation via game-state injection; this epic follows the pattern)
- **ADR-082** — Port to Python (backend is now Python, not Rust)
- **ADR-087** — Post-port subsystem restoration (restoration plan context)
- **ADR-102** — Tool-use protocol for structured output (narrator tool architecture)
- **ADR-103** — OTEL via tool registry (observability architecture)
- **ADR-009** — VALLEY zone (was considered for 24-6, rejected in favor of tools; kept for context)

## Content Status

- **Schemas (24-1):** Defined; lives at `sidequest-content/genre_packs/{pack}/grounding/` (weather.yaml, demographics.yaml, calendar.yaml, etc.)
- **Glenross weather (24-2):** Authored (climate zones, seasonal conditions, special events)
- **Glenross demographics (24-3):** Authored (13-strong recurring cast, settlement profiles, services)
- **Glenross calendar (24-4):** Pending (months, days, moons, festivals, time precision)

## Implementation Status

- **Weather generator (24-5):** Implemented in `sidequest-server/sidequest/game/weather_generator.py`; materializer wired; CLI tested.
- **Narrator tool (24-6):** This story. Acceptance: tool in registry, returns weather/demographics/calendar, narrator invokes during playtest, OTEL span emitted.
- **OTEL instrumentation (24-7):** Pending. Will add weather_proposed vs weather_used spans, demographics_injection span.
- **Playtest validation (24-8):** Pending. Run glenross session, verify narrator uses grounding data in narration.
