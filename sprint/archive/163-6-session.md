---
story_id: "163-6"
jira_key: null
epic: "163"
workflow: "spdd"
---
# Story 163-6: Weather zones: Region.weather_zone, region-aware selection, re-gen on region change + Glenross content (plan tasks 16–17,19–20)

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T15:25:05Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T15:59:58Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T15:59:58Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T15:59:58Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-10T16:30:39Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T16:37:49Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T16:37:49Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T16:37:49Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-10T19:28:04Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T19:29:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T19:29:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T19:29:00Z"/>
</skills-invoked>

## Dev Assessment (Rework Round 2)

**Complete.** r2 fixes committed `4361a9d6` (pushed): [HIGH #2] connect-seam test asserts `weather_generator`/`weather_season` populate; [MED] game_slug ValueError contained in the emit helper as `weather.zone_change_skipped` (reason=`no_game_slug`) + test; [LOW] `sd:Any` comment corrected to layering, emit cadence docstring corrected, `pytest.raises(ValueError)` tightened. **[HIGH #1]** on-move call-site harness split to follow-up **163-8** per Keith. 30 story+regression tests green; ruff clean. **Handoff:** To Reviewer (approve per Keith's override).

## Keith Decision (2026-07-10, re-review round 1)

**Merge 163-6 now, split the on-move integration harness to a follow-up.** Reviewer re-review r1 raised two HIGH wiring gaps; #2 (connect cache-field population) is guarded now (extended connect-seam test). #1 (the on-move call site `websocket_session_handler.py:2581`) requires a full-turn integration harness that does **not exist** for ANY region-change-block helper (`_maybe_emit_location_description`, `_maybe_emit_dungeon_map`, `_maybe_emit_relationships` are all equally unguarded at their call sites). Building it is a shared infra task larger than this feature. **Keith's call:** accept #1 as a documented HIGH finding + follow-up story **163-8** (region-change-block integration harness, covers all siblings); override the reviewer bar for this one finding; merge 163-6. Also landed in r2: game_slug containment (Medium) + comment fixes (Low). Rework commit `4361a9d6`.

## Story Details
- **ID:** 163-6
- **Jira Key:** null
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T19:30:44Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T15:03:36Z | 2026-07-10T15:10:42Z | 7m 6s |
| red | 2026-07-10T15:10:42Z | 2026-07-10T15:27:52Z | 17m 10s |
| green | 2026-07-10T15:27:52Z | 2026-07-10T16:01:42Z | 33m 50s |
| review | 2026-07-10T16:01:42Z | 2026-07-10T16:21:27Z | 19m 45s |
| red | 2026-07-10T16:21:27Z | 2026-07-10T16:32:26Z | 10m 59s |
| green | 2026-07-10T16:32:26Z | 2026-07-10T16:39:08Z | 6m 42s |
| review | 2026-07-10T16:39:08Z | 2026-07-10T16:58:22Z | 19m 14s |
| red | 2026-07-10T16:58:22Z | 2026-07-10T19:28:44Z | 2h 30m |
| green | 2026-07-10T19:28:44Z | 2026-07-10T19:30:05Z | 1m 21s |
| review | 2026-07-10T19:30:05Z | 2026-07-10T19:30:44Z | 39s |
| finish | 2026-07-10T19:30:44Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

- **Improvement (non-blocking):** sm-setup wrote the session `workflow` field as the authoring alias `superpowers` verbatim; the handoff/gate CLI only accepts the canonical name `spdd`, so `resolve-gate` errored. SM corrected the session file to `spdd` (matching all archived sibling sessions 163-1..5, 164-1..5). Root cause: sm-setup should normalize the `superpowers`→`spdd` alias when writing the session. The story YAML legitimately keeps `superpowers` (that's the authoring value across all epics).

### TEA (test design)
- **Improvement** (non-blocking): The plan's Task 16 RED test (`assert r.weather_zone == "highland_pass"`) would PASS immediately under pydantic v2 `extra="allow"` — a false-RED, since the extras bag already exposes the attribute. Affects `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` (the Task 16 test snippet should assert `"weather_zone" in Region.model_fields` and omitted-→-`None`, not just the value round-trip). *Found by TEA during test design.*
- No blocking upstream findings during test design. Task 18's validator (`_validate_weather_zones`) confirmed already shipped, so Task 20's content will be checked live — no gap.
- **(Rework round 1) Improvement** (non-blocking): the reviewer's Low findings that are NOT testable remain for Dev in green — `load_world_grounding(cartography: Any)` → concrete `CartographyConfig | None`; a justifying comment on `regenerate_weather_for_region(sd: Any)`; the two stale docstrings (`world_grounding_bootstrap.py` module scope + `WorldGroundingBootstrap` "three values"); optional `logger.warning` parity in the except block. Affects `sidequest-server/sidequest/game/world_grounding_bootstrap.py` + `map_emit.py`. *Found by Reviewer, carried by TEA into the rework handoff.* → **RESOLVED by Dev in green round 1 (all four).**
- No new upstream findings during rework implementation (Dev, green round 1).

### Dev (implementation)
- **Gap** (non-blocking): On session RESUME, `load_world_grounding` (connect.py ~L668) runs BEFORE the saved snapshot is restored (~L737), so bootstrap weather always binds to `cartography.starting_region`, never the party's persisted `current_region`. A session resumed in `castle_ross` boots with `glen_floor` weather (and the `world_grounding_loaded` OTEL span reports that wrong zone) until the party next changes region, when Task 19's on-move re-sample corrects it. Affects `sidequest-server/sidequest/handlers/connect.py` (a resume-time re-sample from the restored `current_region` would close it). Out of Task 17's explicit "starting region" scope — flagging for a follow-up, not fixed here. *Found by Dev during implementation.*
- **Gap** (non-blocking): `_validate_weather_zones` (task 18) checks a region's `weather_zone` is a real climate zone, but NOT that the zone defines the session's bootstrap season. A world whose reachable zones don't share a common season would have re-samples skip (now contained + observable via `weather.zone_change_skipped` after the pre-review fix) rather than produce weather. Affects `sidequest-server/sidequest/cli/validate/pack.py` (a cross-zone common-season check would catch it at authoring time). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the sanctioned bootstrap-wiring suite's fixture pack (`tests/fixtures/packs/test_genre`) declares no `weather_zone` on any region, so it can only ever exercise the no-op branch of any region-override bootstrap wire — every future weather-zone story inherits this blind spot. Affects `sidequest-server/tests/fixtures/packs/test_genre/**/cartography.yaml` + `tests/server/test_session_bootstrap_world_grounding.py` (add a `weather_zone`-bearing fixture world so the positive override path is reachable). *Found by Reviewer during code review.*
- **Gap** (non-blocking): the region-driven *bootstrap* weather selection is invisible to the GM panel — only the resulting zone rides the generic `weather_proposed` span, with no record of whether the region override or the genre default chose it. Affects `sidequest-server/sidequest/game/world_grounding_bootstrap.py` (`_select_zone_for_region` should emit a strategy span, matching the region-change path). *Found by Reviewer during code review.* (Also in the rework severity table.) → **RESOLVED in green round 1.**
- **(Re-review round 1) Gap** (blocking): the Task-19 on-move re-sample is mutation-proven-unguarded at TWO seams — the handler call site (`websocket_session_handler.py:2581`) and the connect cache-field population (`connect.py:1205-1206`); each can be deleted with all 14,935 tests green. Needs an integration test through `WebSocketSessionHandler.handle_message` + a cache-field assertion. *Found by Reviewer during re-review.* (Rework severity table.)
- **(Re-review round 1) Improvement** (non-blocking): the `game_slug` `ValueError` can tear down the whole WS connection (past the emit helper's narrow catch), inconsistent with the file's "must not crash a turn" convention; unreachable today. Contain it in the emit helper. Plus two comment-accuracy nits (`sd: Any` "cycle" reason; "same region-change block" cadence). *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Task 16 RED assertion strengthened — the plan's round-trip check is a false-RED under `extra="allow"`**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Task 16
  - Spec text: "Run it, SEE it fail … EXPECT fail (attribute absent; `extra="allow"` keeps it in `__pydantic_extra__`, not as `.weather_zone`)"
  - Implementation: added `assert "weather_zone" in Region.model_fields` and an omitted-→-`None` assertion as the RED drivers; kept the plan's value round-trip as an AC companion (it passes today)
  - Rationale: verified empirically — pydantic v2 with `extra="allow"` DOES expose `.weather_zone` via `__getattr__` (returns `'highland_pass'` today), so the plan's `r.weather_zone == "…"` passes before the field exists. `model_fields` distinguishes a *declared* typed field from an extras-bag entry; that is the real thing Task 16 adds.
  - Severity: minor
  - Forward impact: none — Dev adds the same typed field; the suite is simply a valid RED now
- **Task 19 emit targeted as an extracted `map_emit` helper, not inline in `websocket_session_handler`**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Task 19
  - Spec text: "In `websocket_session_handler.py`, inside `if _region_changed:` … call the helper and publish … `_watcher_publish("weather.zone_changed", …)`"
  - Implementation: tests target an extracted `map_emit._maybe_regenerate_weather_on_region_change(handler, *, sd, snapshot)` (plus the pure `regenerate_weather_for_region`), driven with `SimpleNamespace` fixtures + monkeypatched `_watcher_publish` + a `PgTelemetrySink` DB-readback
  - Rationale: the inline emit is not unit-drivable without the full ~2600-line handler method. The established house pattern is an extracted `_maybe_emit_*` helper in `map_emit.py` (siblings `_maybe_emit_cartography_map` / `_maybe_emit_location_description`, and the sibling test `tests/server/test_map_treatment_span.py`). This satisfies CLAUDE.md "No Source-Text Wiring Tests" with a behavior-driven capture + durable-sink readback.
  - Severity: minor
  - Forward impact: Dev implements the helper in `map_emit.py` and calls it from the region-change block (right where `_maybe_emit_cartography_map` is invoked, ~L2567), not as a raw inline block
- **Rework (round 1): two new contracts beyond the plan, mandated by RED tests responding to the review**
  - Spec source: Reviewer Assessment (this session) — OTEL Observability + No Silent Fallbacks findings
  - Spec text: "the bootstrap zone-selection decision emits no dedicated span"; "`game_slug` (str|None) unguarded in the seed → silent `"None:region"` degrade"
  - Implementation: `test_select_zone_for_region_emits_bootstrap_span` demands `weather.bootstrap_zone_selected` (`component="location"`, `{zone, strategy}`) from `_select_zone_for_region`; `test_regenerate_weather_requires_game_slug` demands `regenerate_weather_for_region` RAISE on a `None` game_slug
  - Rationale: the plan specified neither bootstrap observability nor the game_slug precondition; these close the reviewer's two doctrine-matching findings. The game_slug guard belongs in the pure helper (it owns the seed precondition) and is a tripwire — regenerate is only called on the active-session region-change path where game_slug is always set, so it won't crash normal turns.
  - Severity: minor
  - Forward impact: Dev adds the span emit + the guard in green (2 RED → GREEN)

### Dev (implementation)
- **Retagged `the_kirk_of_st_maelrubha` `glen_floor`, not the plan's `highland_pass`**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Task 20
  - Spec text: "Add `weather_zone: highland_pass` to `castle_ross`, `the_long_pass`, and `the_kirk_of_st_maelrubha` (upland)"
  - Implementation: tagged `the_kirk_of_st_maelrubha` `glen_floor`; `highland_pass` = `castle_ross` + `the_long_pass` only
  - Rationale: the authored region is "a low mound at the village" (`terrain: building`), adjacent only to glen_floor village regions and never touching the genuine uplands — `highland_pass` would flip a blizzard on a pub→kirk stroll (genre truth). Confirmed by the pre-handoff review.
  - Severity: minor
  - Forward impact: none — no consumer depends on the kirk being highland; the two real uplands are correctly tagged
- **Contained the region-change re-sample instead of the plan's raw `generate` call**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Task 19
  - Spec text: "call the helper and publish … `_watcher_publish("weather.zone_changed", …)`" (raw `sd.weather_generator.generate(zone, sd.weather_season, seed)`)
  - Implementation: wrapped the re-sample in `try/except (UnknownWeatherZone, UnknownWeatherSeason)` → emit `weather.zone_change_skipped` (component `location`, `reason`) and return; added `condition` to the `weather.zone_changed` span
  - Rationale: the raw call raises `UnknownWeatherSeason` (uncaught → whole-turn crash, per the pre-review Critical) for any world whose entered zone doesn't define the bootstrap season; the task-18 validator can't catch it. Contained loudly (No Silent Fallbacks) without crashing the turn.
  - Severity: minor
  - Forward impact: none for glenross (both zones define all four seasons); future worlds get an observable skip span instead of a turn crash
- **Rework (round 1): No new deviations from spec.** Implemented exactly the two contracts TEA's rework RED tests mandated (`weather.bootstrap_zone_selected` span + `game_slug` fail-loud guard) plus the reviewer's Low cleanups; no divergence from those contracts.

### Reviewer (audit)
- **TEA — Task 16 RED assertion strengthened (`model_fields`)** → ✓ ACCEPTED by Reviewer: verified independently — pydantic v2 `extra="allow"` exposes the attribute, so the plan's round-trip check is a genuine false-RED; `model_fields` membership is the correct declared-field distinguisher (and a sanctioned reflection tripwire).
- **TEA — Task 19 emit as an extracted `map_emit` helper, not inline** → ✓ ACCEPTED by Reviewer: matches the established `_maybe_emit_*` house pattern and the sibling `test_map_treatment_span.py`; enabled the (present) DB-readback wiring test. Sound.
- **Dev — retagged `the_kirk_of_st_maelrubha` `glen_floor`, not the plan's `highland_pass`** → ✓ ACCEPTED by Reviewer: the authored region ("low mound at the village", adjacent only to glen-floor regions) contradicts the plan's "upland" label; retag is genre-truth-correct and validator-clean. Good catch.
- **Dev — contained the region-change re-sample (`weather.zone_change_skipped`) instead of the plan's raw `generate`** → ✓ ACCEPTED by Reviewer: prevents a real whole-turn crash for future non-season-sharing worlds; the catch is specific and loud (not a swallow). Sound. (Note: the *bootstrap* selection still lacks a span — tracked as a separate Medium finding, not a deviation flag.)

No deviations flagged. All four are accepted; none contributed to the REJECT.

**(Re-review round 1 audit):**
- **TEA rework — bootstrap span + game_slug guard contracts** → ✓ ACCEPTED by Reviewer: both are sound responses to round-0 findings and are implemented. Caveat: the game_slug guard's *placement* (raise past a narrow catch) is flagged as a Medium finding (contain it) — the contract is right, the containment needs tightening; not a deviation reversal.
- **Dev rework — "No new deviations"** → ✓ ACCEPTED by Reviewer: implementation matches the mandated contracts; the residual issues are wiring-test coverage + comment accuracy, not spec deviations.

## Sm Assessment

**Setup complete — routing to TEA (red phase).**

- **Story:** 163-6 — Weather zones (spec §2 **A2**): bind climate to geography. 5 pts, p1, repos **server + content**. Epic 163 (Mapping Track A). No Jira (sprint-YAML tracked; Jira steps skipped, same as all epic-163 siblings).
- **Workflow:** `spdd` (phased) — setup(sm) → red(tea) → green(dev) → review(reviewer) → finish(sm). The sprint-YAML tag `superpowers` is the established alias for spdd on epics 163/164/165 per Keith's settled 2026-07-08 decision (`.pennyfarthing/sidecars/sm-decisions.md`). **Decision is settled — do not re-ask.**
- **Branches:** `feat/163-6-weather-zones-region-selection` created in **sidequest-server** and **sidequest-content**, both off `develop` (per repos.yaml both subrepos are gitflow → develop, not main). Working trees clean, synced to origin/develop.
- **Authoritative source for the next agents:**
  - Plan: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` — this story = tasks **16, 17, 19, 20** (Task 18 excluded — already shipped, see scope note). Each task is fully specified: files, interfaces, failing-test-first code, exact `-n0` pytest commands, commit messages. Follow in task order.
  - Spec: three-tier-mapping design §2 A2 ("bind weather to geography").
  - Story context: `sprint/context/context-story-163-6.md` (stub — ACs to be defined by TEA in RED, matching sibling pattern).
- **Scope for TEA's red phase (tasks 16, 17, 19, 20):**
  - **Task 16 (server):** add `weather_zone: str | None = None` to `Region` (`genre/models/world.py`, after `controlled_by`). Failing test: `tests/genre/test_region_weather_zone.py`. (Verified NOT yet present.)
  - **Task 17 (server):** `_select_zone_for_region(...)` in `world_grounding_bootstrap.py` prefers the STARTING region's `weather_zone` over the genre hardcode; declared-but-invalid zone **fails loud**. Thread `cartography` through `load_world_grounding` + `connect.py`. Failing test: `tests/game/test_weather_region_zone_selection.py`.
  - **Task 19 (server):** cache `weather_generator`/`weather_season` on `_SessionData`; re-sample `sd.weather_state` on region change when the new region's zone differs (deterministic seed `crc32(game_slug:region_id)`); emit `weather.zone_changed` OTEL span (`component="location"` → `turn_telemetry`). Failing test: `tests/server/test_weather_zone_change.py` (reflection tripwire + capture span test + **DB-readback wiring test** binding `PgTelemetrySink`).
  - **Task 20 (content):** annotate all 14 glenross `cartography.yaml` regions — `highland_pass` for castle_ross / the_long_pass / the_kirk_of_st_maelrubha (upland), `glen_floor` for the other 11.
- **Scope note — Task 18 already shipped:** validator `_validate_weather_zones` already exists in `sidequest-server/sidequest/cli/validate/pack.py` (L1102, wired at L1311). That's why the range skips 18. Consequence: Task 20's content **will** be checked by the live validator — the plan's `just content-validate tea_and_murder` gate is real. Author zones exactly per Task 20 or validation fails loud.
- **Doctrine flags:**
  - **No Silent Fallbacks** — Task 17's declared-but-unknown `weather_zone` must raise, never fall back (test `test_declared_but_invalid_region_zone_fails_loud`).
  - **OTEL Observability** — Task 19's `weather.zone_changed` span is mandatory; it's the GM-panel lie-detector for weather. Needs the DB-readback wiring test, not just a capture test.
  - **Every suite needs a wiring test** — Task 16 exercised by a real pack load; Task 19 via `PgTelemetrySink` readback (per CLAUDE.md wiring rules).
- **Judgment checks:** Jira — skipped (no-jira sprint story). Context — story + epic context written & validated. Merge gate — CLEAR (no open PRs in server/content; the lone open PR is the unrelated understudy draft #19, non-blocking).

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt feature story (spec §2 A2) — new model field, selection logic, on-move re-generation, and a mandatory OTEL span. No chore bypass conceivable.

**Test Files:**
- `tests/genre/test_region_weather_zone.py` — Task 16: `Region.weather_zone` typed field (3 tests)
- `tests/game/test_weather_region_zone_selection.py` — Task 17: `_select_zone_for_region` bootstrap selection (4 tests)
- `tests/server/test_weather_zone_change.py` — Task 19: `_SessionData` cache fields + `regenerate_weather_for_region` + extracted `map_emit._maybe_regenerate_weather_on_region_change` emit (9 tests)

**Tests Written:** 16 tests covering tasks 16 / 17 / 19. Task 20 is content authoring (glenross `cartography.yaml` `weather_zone` annotations), validated by the already-shipped `_validate_weather_zones` (task 18) — no separate test file; Dev runs `just content-validate tea_and_murder`.
**Status:** RED — 15 failing (all feature-missing), 1 AC-companion pass. Verified by testing-runner (`163-6-tea-red`): 0 collection errors, 0 fixture errors; the `PgTelemetrySink` DB-readback provisioned Postgres + migrated cleanly and failed only on the missing helper. Commit `545d5808`.

### Rule Coverage

| Rule / doctrine | Test(s) | Status |
|---|---|---|
| No Silent Fallbacks — invalid zone raises, no default drift | `test_declared_but_invalid_region_zone_fails_loud` | RED |
| OTEL Observability — subsystem decision emits a span | `test_zone_change_emits_weather_zone_changed` | RED |
| Every suite needs a wiring test — durable-sink readback | `test_weather_zone_changed_reaches_turn_telemetry` (PgTelemetrySink → `turn_telemetry`) | RED |
| No Source-Text Wiring Tests — reflection tripwire, not grep | `test_session_data_has_weather_cache_fields` (`__dataclass_fields__`) | RED |
| Determinism — region-seeded, reproducible weather | `test_regenerate_weather_is_deterministic_by_region` | RED |
| No-op on absent config — no silent default weather | `test_regenerate_weather_noops_without_generator`, `test_no_emit_when_region_has_no_weather_zone` | RED |

**Rules checked:** 6 doctrine checks (Python has no numbered lang-review list for these; mapped to SOUL/CLAUDE.md doctrine) have failing test coverage.
**Self-check:** 0 vacuous tests. Every test asserts a concrete value or behavior; the single passing test (`test_region_accepts_weather_zone`) asserts a real value round-trip, not `is_some`/`is_none`/`True`.

**GREEN scope for Dev (Naomi Nagata):**
1. **Task 16 (server):** `weather_zone: str | None = None` on `Region` (`genre/models/world.py`, after `controlled_by`).
2. **Task 17 (server):** `_select_zone_for_region(rules, cartography, genre_slug)` in `world_grounding_bootstrap.py`; thread `cartography` through `load_world_grounding` (add `cartography: Any | None = None` kwarg) and pass it from `connect.py`. Declared-but-invalid zone raises.
3. **Task 19 (server):** two cache fields on `_SessionData` (populated in `connect.py`); pure `regenerate_weather_for_region(sd, region_id, zone)` in `world_grounding_bootstrap.py` (seed `crc32(f"{sd.game_slug}:{region_id}")`); extracted `_maybe_regenerate_weather_on_region_change(handler, *, sd, snapshot)` in `websocket_handlers/map_emit.py`, **called from the region-change block** (~L2567, beside `_maybe_emit_cartography_map`) — emits `weather.zone_changed` (component `location`, fields `world`/`region`/`from_zone`/`to_zone`).
4. **Task 20 (content):** annotate all 14 glenross regions — `highland_pass` for `castle_ross` / `the_long_pass` / `the_kirk_of_st_maelrubha`, `glen_floor` for the rest; verify with `just content-validate tea_and_murder`.

**Note for Dev:** my fake `sd` in the Task 19 tests reads `sd.game_slug` for the seed and `sd.weather_generator` / `sd.weather_season` for regeneration — match those attribute names.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/genre/models/world.py` — Task 16: `Region.weather_zone: str | None` typed field.
- `sidequest-server/sidequest/game/world_grounding_bootstrap.py` — Task 17/19: `_select_zone_for_region` (region zone wins, fails loud on unknown), `regenerate_weather_for_region` (deterministic per-region re-sample), extended `WorldGroundingBootstrap` (generator + season), `load_world_grounding` gains optional `cartography=` and geography-driven zone.
- `sidequest-server/sidequest/server/session_state.py` — Task 19: `weather_generator` / `weather_season` cache fields on `_SessionData`.
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — Task 19: `_maybe_regenerate_weather_on_region_change` emit helper (fires `weather.zone_changed`; contained skip → `weather.zone_change_skipped` when the zone lacks the season; `condition` in the span).
- `sidequest-server/sidequest/server/websocket_session_handler.py` — Task 19 wiring: calls the helper from the region-change block.
- `sidequest-server/sidequest/handlers/connect.py` — Task 17/19 wiring: passes `cartography` to `load_world_grounding`, stamps the two cache fields at bootstrap.
- `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` — Task 20: 14 regions annotated (`highland_pass` = castle_ross + the_long_pass; `glen_floor` = the other 12).

**Tests:** 17/17 story tests GREEN (`test_region_weather_zone.py` 3, `test_weather_region_zone_selection.py` 4, `test_weather_zone_change.py` 10 incl. the new containment test). Regression: 88 targeted + 47 blast-radius (region-transition, cartography projection, intent-router region exits, connect, location-description emit, map-treatment sibling) — **zero regressions**. ruff clean; content validator PASS (0 errors); full import chain verified.

**Branches (pushed):**
- server `feat/163-6-weather-zones-region-selection` @ `9cd9812a` (green `7c0bd2a8` + review-fix `9cd9812a`)
- content `feat/163-6-weather-zones-region-selection` @ `866bbe0` (green `edba291` + kirk-fix `866bbe0`)

**Pre-handoff review (self, via `requesting-code-review`):** dispatched an adversarial reviewer over the diff. Acted on it with `receiving-code-review` discipline (verified each claim):
- **FIXED (Critical):** unguarded season-mismatch re-sample could crash a whole turn for a future world whose zones don't share the bootstrap season → now contained + observable (`weather.zone_change_skipped`).
- **FIXED (Important):** the plan's Task-20 kirk tag (`highland_pass`) contradicted the authored village-floor region → retagged `glen_floor`.
- **RECORDED as findings (not fixed — out of scope):** resume binds weather to `starting_region` not the persisted `current_region` (Task 17 is explicitly starting-region-scoped; Task 19 corrects on next move); the task-18 validator doesn't enforce cross-zone common-season.
- **Pushed back (Minor):** the helper's world re-lookup is intentional — it keeps the helper independently unit-drivable with `SimpleNamespace` fixtures (matches the sibling `_maybe_emit_cartography_map`); a one-`dict.get` cost, not fixed.

**Self-review:** wired end-to-end (helper called from the real region-change block; connect.py stamps the cache); follows the `_maybe_emit_*` house pattern; ACs met; error handling loud + contained.

**Handoff:** To Reviewer (Chrisjen Avasarala) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (17 tests green, ruff clean, validator PASS, no new smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — reviewer assessed edge cases (game_slug None, empty zone, weather_state None) directly |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — reviewer assessed silent-failure domain (see [RULE #1] + [RULE #14]) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (2 high, 1 med, 1 low) | confirmed 4, dismissed 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (high-confidence, Low severity) | confirmed 2 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type domain covered by rule-checker check #3 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — reviewer assessed: `yaml.safe_load` throughout, input validated in `_select_zone_for_region` — clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — reviewer assessed: helper world re-lookup intentional (matches sibling `_maybe_emit_cartography_map`) |
| 9 | reviewer-rule-checker | Yes | findings | 6 (checks #3×2, #4, #14, #16, #17) | confirmed 6, dismissed 0 |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per `workflow.reviewer_subagents`)
**Total findings:** 12 confirmed (1 High / 5 Medium / 6 Low), 0 dismissed, 0 deferred. **Convergence:** test-analyzer #2 and rule-checker #17 independently flagged the same connect-time wiring-test gap.

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md (4 additional), every changed symbol:

| Rule | Instances | Verdict |
|---|---|---|
| #1 Silent exception swallowing | `_maybe_regenerate_weather_on_region_change` except; `connect.py` grounding except | COMPLIANT — both catch specific/handled + emit loud (span/logger.error), never swallow |
| #2 Mutable defaults | 27 defs | COMPLIANT — only `None`/immutable-str defaults |
| #3 Type annotations at boundaries | `regenerate_weather_for_region(sd: Any)`, `load_world_grounding(cartography: Any)`, `_select_zone_for_region` (private, exempt), emit helper (typed) | **2 VIOLATIONS** — `sd: Any` (cycle excuse unstated) + `cartography: Any` (concrete `CartographyConfig` importable, no cycle) |
| #4 Logging coverage/correctness | except block emits watcher span only, no `logger.warning` | **1 VIOLATION (textual)** — convention-consistent with sibling skip paths; Low |
| #5 Path handling | none new | COMPLIANT |
| #6 Test quality | 17 tests | COMPLIANT (specific-value asserts, correct patch target); coverage gaps tracked under #17/[TEST] |
| #7 Resource leaks | `with pool.connection()` | COMPLIANT |
| #8 Unsafe deserialization | `yaml.safe_load` | COMPLIANT |
| #9 Async pitfalls | none | COMPLIANT |
| #10 Import hygiene | 2 new `map_emit` imports | COMPLIANT — no cycle (game never imports server; AST-verified), explicit named imports |
| #11 Input validation | `_select_zone_for_region` validates region zone vs rules | COMPLIANT (raises loud) |
| #12 Dependency hygiene | none | COMPLIANT |
| #13 Fix-introduced regressions | fix commit `9cd9812a` | COMPLIANT — specific except, no new bug class |
| [+] No Silent Fallbacks | 4 sites | **1 VIOLATION** — `game_slug` (str\|None) interpolated into seed unguarded (silent "None:region" degrade) |
| [+] No Source-Text Wiring Tests | 3 reflection tripwires | COMPLIANT — `__dataclass_fields__` / `model_fields`, sanctioned |
| [+] OTEL Observability | 4 decisions | **1 VIOLATION** — bootstrap `_select_zone_for_region` region-vs-default decision emits no dedicated span (region-*change* path does) |
| [+] Every Test Suite Needs a Wiring Test | 2 subsystems | **1 VIOLATION** — Task-19 emit path wired-tested (DB-readback ✓); Task-17 bootstrap cartography wire has NO positive-case test |

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is correct and the code is genuinely wired — but the **Task-17 bootstrap region-override path is both untested and, for the only shipped world, currently unobservable**, and that gap is mutation-proven and matches two stated project rules. That is blocking under this project's wiring doctrine. The fixes are small (mostly tests + one OTEL span + type tidy-ups).

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]``[RULE]` | Connect-time cartography wire (`genre_pack.worlds.get(...).cartography` → `load_world_grounding(cartography=)` → `_select_zone_for_region`) has **no positive-case wiring test**. Mutation-proven: hardcoding `cartography=None` left all 309 connect/grounding tests green. The sanctioned wiring suite `test_session_bootstrap_world_grounding.py` uses a fixture pack whose cartography declares no `weather_zone`, so it only exercises the no-op branch. Matches "Verify Wiring, Not Just Existence" + "Every Test Suite Needs a Wiring Test". | `sidequest-server/sidequest/handlers/connect.py:662`; suite gap | Add a test through the real `ConnectHandler`/`load_world_grounding` seam with a world whose `starting_region.weather_zone` **differs** from the genre default, asserting `session._session_data.weather_state.zone` reflects the region (not the hardcode). Same-value fixtures cannot catch a severed wire. |
| [MEDIUM] `[TEST]` | `test_regenerate_weather_is_deterministic_by_region` samples the **same** region twice → region-derived seeding unproven. Mutation-proven: dropping `region_id` from the seed still passes. | `sidequest-server/tests/server/test_weather_zone_change.py:102` | Sample two **different** regions bound to the same zone; assert their `WeatherState`/`seed` differ. |
| [MEDIUM] `[RULE]` `[SILENT]` | `_select_zone_for_region`'s region-vs-genre-default decision emits **no OTEL span** — only the resulting zone rides the generic `weather_proposed` span. The GM panel can't verify Task-17 fired vs. fell back. The parallel region-change path got a full span. | `sidequest-server/sidequest/game/world_grounding_bootstrap.py:96` | Emit a bootstrap span (e.g. `weather.bootstrap_zone_selected` with `strategy: region\|genre_default`, `zone`). |
| [MEDIUM] `[RULE]` `[SILENT]` | `seed = crc32(f"{sd.game_slug}:{region_id}")` with `game_slug: str \| None` — a `None` slug silently yields a `"None:<region>"` seed instead of failing loud. No guard, no test. | `sidequest-server/sidequest/game/world_grounding_bootstrap.py:127` | Guard/assert `game_slug` non-None (or document + test the invariant that it's always set before a region change). |
| [MEDIUM] `[TEST]` | The `reason == "unknown_zone"` skip branch is untested; only `zone_missing_season` is covered. | `sidequest-server/sidequest/server/websocket_handlers/map_emit.py:1383` | Add a case where a non-starting region binds a non-existent climate zone; assert `reason == "unknown_zone"`. |
| [LOW] `[TYPE]` `[RULE]` | `load_world_grounding(cartography: Any \| None)` — the concrete `CartographyConfig` is importable into `sidequest.game` with no cycle; `Any` is lazy. | `world_grounding_bootstrap.py:132` | Type as `CartographyConfig \| None` (or add a justifying comment). |
| [LOW] `[TYPE]` `[RULE]` | `regenerate_weather_for_region(sd: Any)` — `Any` used at a public boundary with no comment (real reason: avoid game→server import cycle). | `world_grounding_bootstrap.py:118` | Add a one-line comment explaining the cycle-avoidance `Any`. |
| [LOW] `[RULE]` | except block emits watcher span only, no `logger.warning()` — convention-consistent with sibling `_maybe_emit_cartography_map` skip paths. | `map_emit.py:1381` | Optional: add `logger.warning(...)` for stdlib-log parity. |
| [LOW] `[DOC]` | Module docstring lists "location-graph zone selection … OUT of scope" — this story added exactly that. | `world_grounding_bootstrap.py:8` | Update the Scope paragraph. |
| [LOW] `[DOC]` | `WorldGroundingBootstrap` docstring says "three world-grounding values" — now five fields. | `world_grounding_bootstrap.py:49` | Update the count/enumeration. |
| [LOW] `[TEST]` | `test_weather_zone_change_helper_is_importable` is a callable-only check (passes for a no-op stub). | `test_weather_zone_change.py:159` | Fold into a behavior test or drop. |
| [LOW] `[SIMPLE]` | Helper re-looks-up the world the caller already resolved. | `map_emit.py:1374` | Accept — intentional for independent unit-drivability; matches sibling. (VERIFIED, not a defect.) |

**Observations (≥5):**
- `[VERIFIED]` Wiring call site is real — helper imported (`websocket_session_handler.py:244`) + called inside `if _region_changed:` (`:2581`), a genuine non-test production consumer. Complies with wiring *existence*; the *test* of the Task-17 sibling wire is the [HIGH] gap.
- `[VERIFIED]` No-Silent-Fallbacks on the unknown-zone bootstrap path — `_select_zone_for_region` raises `ValueError` with the zone + available list (`world_grounding_bootstrap.py:109-113`); the emit helper catches the two SPECIFIC weather exceptions and emits a loud `weather.zone_change_skipped` span (`map_emit.py:1383-1404`). Complies with check #1. (The `game_slug` None edge is the one exception — see Medium.)
- `[VERIFIED]` `yaml.safe_load` on every weather/grounding load (`weather.py:215`, `world_grounding_loader.py:58/95`) — check #8 clean; no pickle/eval/exec.
- `[VERIFIED]` Content genre-truth — highland_pass now = `castle_ross` ("on the rise — Highland baronial") + `the_long_pass` ("drove road north up the glen"); the kirk ("low mound at the village") correctly retagged glen_floor. Validator PASS.
- `[VERIFIED]` Import hygiene — `map_emit`'s new `sidequest.game.*` imports create no cycle (game never imports server; AST-verified by rule-checker); explicit named imports.
- `[TEST]``[RULE]` The connect-wire test gap (HIGH) is the load-bearing finding — confirmed independently by two subagents and mutation-proven.
- `[SEC]` Security domain (disabled subagent, reviewer-assessed): the only external input is authored `weather_zone` content, validated loud at bootstrap AND by the pack validator. No injection/deserialization surface. Clean.

### Devil's Advocate

Assume this ships broken. The most damning line of attack: **Task 17 does nothing observable and nobody would notice.** For glenross — the only world with `weather_zone` annotations — the starting region `the_glenross_arms` is `glen_floor`, which is verbatim the `tea_and_murder` entry in `_BOOTSTRAP_SELECTION`. So whether the cartography wire works, is severed (`cartography=None`), or is deleted entirely, bootstrap weather is `glen_floor` either way. The entire "starting region's zone wins over the genre hardcode" feature is a no-op for the shipped content, and no test drives a world where the two differ — so a typo in the `_world_obj` extraction (wrong key, inverted `is not None`) ships green and silent. A future author who adds a world starting in a highland pass would find the override mysteriously ignored, with nothing in the GM panel to explain it — because the bootstrap selection emits no span (only the resulting zone rides `weather_proposed`, indistinguishable from the default). Second attack: a confused player resumes a save taken in `castle_ross`; the weather boots as `glen_floor` (bootstrap always binds `starting_region`), contradicting the map, until they wander to a new region — the resume-ordering gap the Dev flagged but did not fix. Third: a stressed content author binds a region to a real climate zone that lacks the session's season; the turn no longer crashes (good, the pre-review fix), but weather silently freezes on the old zone with only a `warning`-level span — is that discoverable in practice, or does it read as "weather is just broken"? Fourth: `game_slug` is `None` on some legacy non-slug session, and every region in every such session shares the `"None:<region>"` seed space — deterministic, but not what "per-session reproducible" promised. None of these crash; all of them are the *quiet wrongness* the wiring/OTEL/No-Silent-Fallbacks rules exist to prevent. The code is competent; the **evidence that it works end-to-end is missing**, and for the one world we ship, the headline behavior is untestable by construction.

**Handoff:** Back to TEA (Amos Burton) for rework — the blocking finding and most of the Mediums are missing tests (red phase); the OTEL span, type tidy-ups, and docstrings follow in green.

## TEA Assessment (Rework Round 1)

**Tests Required:** Yes — addressed every reviewer finding in the TEA/red lane.

**Test Files (changed this round):**
- `tests/server/test_session_bootstrap_world_grounding.py` — **[HIGH]** new `region_override_pack` fixture + `test_bootstrap_region_weather_zone_overrides_genre_default`: drives the REAL `ConnectHandler` with a world whose starting region binds `highland_pass` (glenross's 2nd zone) while the genre default is `glen_floor` (1st). Wire intact → `highland_pass`; severed (`cartography=None`) → `glen_floor` → fails. Closes the mutation-proven connect-seam gap.
- `tests/server/test_weather_zone_change.py` — `test_regenerate_weather_seed_varies_by_region` (two regions → different seeds; the same-region determinism test alone was mutation-blind); `test_zone_change_skips_with_unknown_zone_reason` (the `UnknownWeatherZone` catch branch, `reason="unknown_zone"`); **RED** `test_regenerate_weather_requires_game_slug`; dropped the near-vacuous `_helper_is_importable`.
- `tests/game/test_weather_region_zone_selection.py` — **RED** `test_select_zone_for_region_emits_bootstrap_span` (demands `weather.bootstrap_zone_selected`).

**Status:** 19 pass (coverage guards + wiring) + **2 RED** (drive Dev green): the bootstrap OTEL span and the game_slug fail-loud guard. Both fail feature-missing (verified). ruff clean. Commit `67ebb542` (pushed).

### Finding → disposition map (Reviewer severity table)
| Reviewer finding | Sev | TEA action |
|---|---|---|
| Connect-seam bootstrap wiring test | HIGH | ✅ added (passes; discriminating) |
| Determinism doesn't pin region-seeding | MED | ✅ added seed-varies test |
| Bootstrap zone-selection has no OTEL span | MED | ✅ RED test → Dev adds span |
| `game_slug` None silent seed degrade | MED | ✅ RED test → Dev adds guard |
| `unknown_zone` branch untested | MED | ✅ added |
| `cartography: Any` / `sd: Any` boundary types | LOW×2 | → Dev (green; not testable) |
| 2 stale docstrings | LOW×2 | → Dev (green; not testable) |
| `logger.warning` parity | LOW | → Dev (green; optional) |
| near-vacuous importable test | LOW | ✅ dropped |

**GREEN scope for Dev (Naomi):** (1) emit `weather.bootstrap_zone_selected` (`component="location"`, `{zone, strategy: region\|genre_default}`) from `_select_zone_for_region` — import `publish_event as _watcher_publish` in `world_grounding_bootstrap.py`; (2) guard `regenerate_weather_for_region` to raise on `sd.game_slug is None`; (3) the 4 Low cleanups above. Then the full story suite + regression must be green.

**Handoff:** To Dev (Naomi Nagata) for GREEN (rework round 1).

## Dev Assessment (Rework Round 1)

**Implementation Complete:** Yes — the 2 rework RED tests are GREEN and all 6 reviewer findings in the code lane are resolved.

**Files Changed (this round):**
- `sidequest-server/sidequest/game/world_grounding_bootstrap.py` — `_select_zone_for_region` now emits `weather.bootstrap_zone_selected` (`component="location"`, `{zone, strategy: region|genre_default, region}`); `regenerate_weather_for_region` raises `ValueError` on `sd.game_slug is None` (No Silent Fallbacks tripwire); `load_world_grounding(cartography: CartographyConfig | None)` (TYPE_CHECKING import, no cycle); `sd: Any` documented; module + `WorldGroundingBootstrap` docstrings de-staled.
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — `logger.warning` parity on the `weather.zone_change_skipped` path (check #4).

**Finding → resolution (all confirmed reviewer findings):**
| Reviewer finding | Sev | Resolution |
|---|---|---|
| Connect-seam bootstrap wiring test | HIGH | TEA added (green) — verified passing |
| Determinism / region-seed | MED | TEA added (green) |
| No bootstrap OTEL span | MED | ✅ emit `weather.bootstrap_zone_selected` — test green |
| `game_slug` None silent seed | MED | ✅ raise on None — test green; sole caller is the region-change path (game_slug always set) |
| `unknown_zone` branch untested | MED | TEA added (green) |
| `cartography: Any` | LOW | ✅ typed `CartographyConfig | None` |
| `sd: Any` uncommented | LOW | ✅ comment added (cycle-avoidance) |
| module docstring stale | LOW | ✅ updated |
| `WorldGroundingBootstrap` "three values" | LOW | ✅ updated |
| `logger.warning` parity | LOW | ✅ added |

**Verification (fresh):** 21/21 story tests GREEN (incl. the 2 previously-RED bootstrap-span + game_slug-guard); **78 regression GREEN** (full bootstrap wiring suite, `load_world_grounding` callers `test_genre_flavor_world_tier`, weather subsystem, `map_treatment_span` sibling, region-transition) — **zero regressions**. ruff clean; import chain verified (no `game`→`server`/`telemetry` cycle); sole-caller check confirms the guard + span are tripwires with one call site each.

**Self-review (via `requesting-code-review`):** the round-0 adversarial dispatch drove these findings; this rework is their direct resolution. Meta-check #13 (fix-introduced regressions): the new `watcher_hub` import is module-level + cycle-verified; the game_slug `ValueError` propagates past the emit helper's `(UnknownWeatherZone, UnknownWeatherSeason)` catch, but its only caller passes a real `sd` with `game_slug` set, so it never fires on a normal turn (tripwire). No new bug class introduced.

**Branches (pushed):** server `feat/163-6-weather-zones-region-selection` @ `e1ac1dd0`; content unchanged @ `866bbe0`.

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review (round 1).

## Subagent Results (Re-Review Round 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (98 tests green, ruff clean, no cycle, validator pass) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 new HIGH (mutation-proven) + 5 round-0 RESOLVED | confirmed 2, dismissed 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (DOC) + 2 round-0 RESOLVED | confirmed 2 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings; reviewer-assessed clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 new (game_slug crash) + all 6 round-0 RESOLVED | confirmed 1 |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled)
**Total findings:** 5 confirmed (2 High / 1 Medium / 2 Low). All round-0 findings verified RESOLVED (test-analyzer + rule-checker + comment-analyzer each mutation- or import-verified their own).

## Reviewer Assessment (Re-Review Round 1)

**Verdict:** REJECTED

The round-0 rework is genuine — every prior finding is mutation-/import-verified fixed (the bootstrap wire, the OTEL span, the guard, the type, the docstrings). **But full-suite mutation testing found the same Pattern-1 wiring gap recurring at the Task-19 on-move seams — the headline behavior (weather changes as the party moves) has no end-to-end test and is mutation-proven-unguarded.** That is blocking under this project's wiring doctrine, and it's the identical class I rejected round-0 for, one seam over.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]``[RULE]` | The Task-19 on-move re-sample **call site** is unguarded: commenting out `_maybe_regenerate_weather_on_region_change(...)` at `websocket_session_handler.py:2581` produces **0 failures across all 14,935 tests**. Every emit test calls the helper directly with `SimpleNamespace` doubles; the DB-readback proves the mechanism, not that the handler invokes it. Matches "Verify Wiring, Not Just Existence" + "Every Test Suite Needs a Wiring Test". | `websocket_session_handler.py:2581` (untested) | Add an integration test driving a real region change through `WebSocketSessionHandler.handle_message` (fixture world with two regions binding different `weather_zone`s), asserting `sd.weather_state.zone` flips after the move. |
| [HIGH] `[TEST]``[RULE]` | The **cache-field population** is unguarded: commenting out `session._session_data.weather_generator/weather_season = ...` at `connect.py:1205-1206` produces **0 failures**. The reflection tripwire only proves the fields are *declared*; the connect-seam test asserts `weather_state.zone` (a different field). Drop this wire and on-move re-sampling no-ops forever, silently — the whole feature goes dark, all 8 tests green. | `connect.py:1205-1206` (untested) | Extend the connect-seam wiring test to also assert `sd.weather_generator is not None` and `sd.weather_season` after the real bootstrap. |
| [MEDIUM] `[RULE]``[SILENT]` | The `game_slug` `ValueError` (world_grounding_bootstrap.py:161) is not caught by the emit helper's `except (UnknownWeatherZone, UnknownWeatherSeason)`; it propagates to the top-level WS loop and tears down the **whole connection**, inconsistent with this file's sibling `except Exception: # must not crash a turn` convention (ADR-006 graceful degradation). Unreachable today (`game_slug` always truthy at the sole `_SessionData` construction site) but a real hazard for future paths (companion-seat variants). | `map_emit.py:1383` | Add `ValueError` to the emit helper's catch (skip loudly via `weather.zone_change_skipped`, reason `no_game_slug`) so a broken invariant degrades to a contained turn-skip, not a connection drop. Keep the pure-helper raise (its test stays green). |
| [LOW] `[DOC]` | `regenerate_weather_for_region`'s `sd: Any` comment says "to avoid a `game`→`server` import cycle" — empirically there is NO cycle (`session_state` is a leaf); the real reason is layering discipline / heavy transitive import. | `world_grounding_bootstrap.py:150` | Reword to the accurate reason (or use a `TYPE_CHECKING` `_SessionData` import like `CartographyConfig`). |
| [LOW] `[DOC]` | `_maybe_regenerate_weather_on_region_change` docstring calls itself the "sibling … called from the same region-change block" as `_maybe_emit_cartography_map`, which actually fires **every** turn (unconditional), while this is gated on `_region_changed`. | `map_emit.py:1371` | Reword the cadence claim. |

**Observations:**
- `[VERIFIED]` All 6 round-0 findings resolved — rule-checker mutation/import-verified each (cartography typed, sd comment, logger.warning, game_slug guard, bootstrap span both strategies, connect-seam wiring test); comment-analyzer verified both docstrings; test-analyzer mutation-killed each round-0 test to confirm it discriminates.
- `[VERIFIED]` No import cycle — AST-walk of `watcher_hub` + the `spans/` package + standalone import (`sidequest.game`→`sidequest.telemetry`).
- `[TEST]``[RULE]` The two new HIGH gaps are the load-bearing blockers — mutation-proven against the full 14,935-test suite.
- `[RULE]``[SILENT]` game_slug connection-crash: compliant with No-Silent-Fallbacks' letter, inconsistent with graceful-degradation; unreachable today but bundled into the rework because the fix is 2 lines.
- `[SEC]` (disabled subagent, reviewer-assessed): only external input is authored `weather_zone`, validated loud + by the pack validator; parameterized SQL in the DB-readback test. Clean.

### Devil's Advocate

Assume it ships broken. The strongest attack is the same one that survived round 0: **the feature that gives the story its name — weather that shifts as the party crosses from glen to pass — has no test that a live session ever triggers it.** Two independent wires (the handler call at line 2581, the cache population at connect.py:1205) can each be deleted with all 14,935 tests staying green; a careless merge, a refactor of the region-change block, or the companion-seat work reconstructing `_SessionData` would silently kill on-move weather and the GM panel's only signal (`weather.zone_changed`) would simply never fire — indistinguishable from "the party never changed climate zones." The DB-readback test that everyone (including my own round-0 note) treated as the Task-19 wiring proof is a mechanism test: it calls the helper by hand. A second attack: a future companion-seat `_SessionData` without `game_slug` turns a cosmetic "no weather this turn" into a full WebSocket disconnect, because the guard I asked for raises past a catch that only knows about weather exceptions. None of these are reachable in *today's* single-construction-site, glen_floor-start world — which is exactly why they're dangerous: the suite is green, the demo works, and the wiring rots on the next refactor. The rule exists for precisely this.

**Handoff:** Back to TEA (Amos Burton) for rework — the two HIGH blockers are missing integration tests (red); the game_slug containment + comment fixes follow in green.