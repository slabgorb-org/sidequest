# Story 24-6: Narrator tool call for weather + demographics + calendar grounding

## Story Brief

Add a narrator-callable tool that returns weather + demographics + calendar grounding on demand. Aligns with ADR-102 (native tool-use) and ADR-103 (OTEL via tool registry). Replaces the original always-on VALLEY-zone injection design. **User revision (2026-05-20):** tool-based approach saves tokens and makes use observable.

## Acceptance Criteria

1. **Tool registered:** Tool appears in narrator tool registry (extending ADR-102 patterns); docstring + input/output schema defined
2. **Tool returns grounding data:**
   - Current weather (from story 24-5 generator: climate + RNG seed → WeatherState)
   - Glenross calendar (from story 24-4: months, days, moons, festivals)
   - Pack demographics (from story 24-3: settlement profiles, recurring cast, services)
3. **Narrator invokes:** During tea_and_murder/glenross playtest (story 24-8), narrator calls the tool when scene needs grounding
4. **OTEL instrumented:** Tool invocation automatically emits span per ADR-103 (tool registry span binding is free)

## Out of Scope

- Forcing narrator to call the tool (we trust model behavior + good tool description)
- Always-on injection or VALLEY-zone prompt manipulation

## Implementation Pointers

### Tool Registry (ADR-102)

File: `sidequest-server/sidequest/agents/tool_registry.py`

Define tool schema:
```python
@dataclass
class GroundingToolInput(BaseModel):
    world_slug: str          # e.g., "glenross"
    pack_slug: str           # e.g., "tea_and_murder"
    narrative_timestamp: float  # seconds since session start (optional, for calendar context)

@dataclass
class GroundingToolOutput(BaseModel):
    weather: WeatherState  # from 24-5 generator
    demographics: dict     # from 24-3 content YAML
    calendar: dict         # from 24-4 content YAML
    narrative_context: str # narrator-friendly summary ("High noon on a Tuesday in October, mild and overcast. The post office is staffed by Margaret and Thomas today. The village's autumn festival begins next week.")
```

Register in narrator tool registry with ADR-102 pattern:
```python
tool_registry.register(
    name="get_scene_grounding",
    description="Get current weather, calendar, and settlement demographics for narrative grounding. Call this when establishing a scene location or time.",
    input_schema=GroundingToolInput,
    output_schema=GroundingToolOutput,
    handler=ground_scene,  # implementation function
)
```

### Data Sources

1. **Weather (24-5 generator):** `sidequest/game/weather_generator.py::generate_weather(climate_yaml, rng_seed) → WeatherState`
2. **Demographics (24-3 content):** `sidequest-content/genre_packs/tea_and_murder/grounding/demographics.yaml` (13-strong recurring cast, settlement profiles, services list)
3. **Calendar (24-4 content):** `sidequest-content/genre_packs/tea_and_murder/grounding/calendar.yaml` (months, days, moons, festivals, time precision)

### OTEL Integration (ADR-103)

Tool registry automatically emits span on invocation. No extra code required if tool is properly registered. Span name will be `tool_call.get_scene_grounding`.

Story 24-7 will add deeper observability (weather_proposed vs weather_used, demographics_injection frequency, etc.).

## Related Stories

- **24-5** (done) — Weather generator produces typed WeatherState
- **24-4** (backlog) — Glenross calendar YAML; needed for tool to return calendar data
- **24-3** (done) — Glenross demographics YAML; already available
- **24-7** (backlog) — OTEL spans for weather/demographics (uses this tool's spans as baseline)
- **24-8** (backlog) — Playtest validation; verifies narrator calls tool during tea_and_murder/glenross session

## Design Notes

- **Token efficiency:** Narrator requests weather/demographics only when narrating a scene or state change, not every turn. Saves tokens vs. always-on injection.
- **Observability:** Tool invocation is observable in OTEL dashboard (ADR-031 GM panel). Each call generates span with input/output payload.
- **Trust the model:** Tool description + schema are sufficient; we don't force calls or add prompt zones. Narrator will naturally call when needed if description is clear.

## Branch

- Feature branch: `feat/24-6-narrator-grounding-tool` (in `sidequest-server`)
- Story is personal project (SideQuest, no Jira)
- Sprint: TO Sprint 2621

## Workflow

- **Type:** tdd (phased: red → green → spec-check → verify → review → spec-reconcile → finish)
- **Assignee:** slabgorb
- **Points:** 3
- **Priority:** p0
