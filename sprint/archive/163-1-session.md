---
story_id: "163-1"
jira_key: ""
epic: "163"
workflow: "spdd"
---
# Story 163-1: Server: map.yaml treatment layer — models, loader, protocol block, emission + OTEL (plan tasks 1,3–7)

## Story Details
- **ID:** 163-1
- **Jira Key:** (none — sprint-tracked)
- **Workflow:** spdd
- **Stack Parent:** none
- **Epic:** 163 — Mapping Track A — genre-true main-map treatments

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-08T23:59:09Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-08T23:03:10+00:00 | 2026-07-08T23:05:20Z | 2m 10s |
| red | 2026-07-08T23:05:20Z | 2026-07-08T23:17:25Z | 12m 5s |
| green | 2026-07-08T23:17:25Z | 2026-07-08T23:48:27Z | 31m 2s |
| review | 2026-07-08T23:48:27Z | 2026-07-08T23:59:09Z | 10m 42s |
| finish | 2026-07-08T23:59:09Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (red phase).**

- **Story:** 163-1 — Server: map.yaml treatment layer (models, loader, protocol block, emission + OTEL). Lead server story of Epic 163 (Mapping Track A). 5pts, p1, server repo only. No Jira (sprint-tracked); Jira steps explicitly skipped.
- **Workflow:** `spdd` (phased). The YAML tag "superpowers" is an alias for spdd. Phase flow: setup → red → green → review → finish (setup=sm, red=tea, green=dev, review=reviewer, finish=sm).
- **Branch:** `feat/track-a-main-map-treatments` on sidequest-server (base: develop).
- **Authoritative sources for the next agents:**
  - Spec: `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md` §2
  - Plan: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` — this story = tasks **1, 3, 4, 5, 6, 7** (task 2 shipped as 163-2, done).
  - Story context: `sprint/context/context-story-163-1.md` (ACs derived from the plan tasks).
- **Scope for TEA's red phase:** failing tests covering MapTreatmentConfig/MapProvenance models + strict validation (task 3), map.yaml → World.map_treatment loader (task 4), CartographyTreatmentWire protocol + payload.treatment field (task 5), payload population from World.map_treatment (task 6), and the `map.treatment_emitted` OTEL watcher span (task 7). Per the OTEL Observability Principle and CLAUDE.md's wiring rules, include a wiring/integration test proving the treatment block is emitted end-to-end over the WebSocket path and the OTEL span fires — not just unit coverage of the models.
- **Judgment checks:** Jira — skipped (no-jira story). Context — written with technical approach + ACs. Merge gate — clear (state came back NEW_WORK_STATE).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the plan's task-4 loader test block covers only absent + present-valid map.yaml; the story-context AC (task 4) additionally requires "malformed → raises (no silent fallback)". Added `test_malformed_map_yaml_raises_no_silent_fallback` to close that gap. Affects `sidequest-server/tests/genre/test_map_treatment_loader.py` (Dev must ensure `_load_map_treatment` calls `MapTreatmentConfig.model_validate` unguarded so a bad kind raises — do NOT wrap in try/except). *Found by TEA during test design.*
- **Question** (non-blocking): RED is a task-ordered cascade — all five files currently collection-error on `MapProvenance` (task 3) since the models are the shared dependency. As Dev implements in plan order (3→4→5→6→7) each file's collection unblocks and then fails on its own missing behavior (`genre_slug` param, absent span, treatment=None). This is intended; Dev should implement strictly in task order and re-run each file `-n0` per task. Affects `sidequest-server/tests/{genre,protocol,server}/` (sequencing only). *Found by TEA during test design.*
- **Gap** (non-blocking): the task-7 DB-readback wiring test requires a running PG test DB (`migrated_db` fixture). Verified up locally (`:5432 accepting connections`); if Dev's env lacks it, run `just pg-up` before the green run. Affects `sidequest-server/tests/server/test_map_treatment_span.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `_build_cartography_map_message` has TWO production callers — the per-turn producer (`map_emit._maybe_emit_cartography_map`, plan task 6) AND the connect/resume bootstrap (`connect.py:2012`). The plan only named the map_emit call site; a pre-handoff code review caught the connect caller missing `genre_slug`, which would emit a `genre_packs//worlds/...` double-slash image URL (404) on the FIRST connect/resume frame for a raster world. Fixed both. Affects `sidequest-server/sidequest/handlers/connect.py` (now passes `genre_slug=row.genre_slug`). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the connect/resume cartography producer has no dedicated integration test, which is why the missing `genre_slug` slipped past the RED suite (both new build/span tests exercise only the map_emit producer). A fixture-driven connect-bootstrap test asserting a raster treatment's `image_url` has no double-slash should be added when a real `map.yaml` world lands (story 163-4). Affects `sidequest-server/tests/server/` (new connect-producer test). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the `map.treatment_emitted` OTEL span lives in `_maybe_emit_cartography_map` (per-turn), so the connect/resume bootstrap ships the treatment block without firing the span — the GM panel sees it on the first turn, not on resume. This mirrors the existing `cartography.map_emitted` span, which is also per-turn-only (the connect bootstrap has never emitted these location spans), so it is consistent rather than a new regression; noted for a future pass that unifies bootstrap/per-turn location telemetry. Affects `sidequest-server/sidequest/handlers/connect.py` + `websocket_handlers/map_emit.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `MapTreatmentConfig.image` is a bare `str` embedded unsanitized into an asset URL (`session_helpers.py:1691`); a `../..`-laden value re-points the map image within the public CDN object space (not a filesystem/cross-host escape). Add a shared `_validate_asset_filename` field-validator rejecting `/`, `\`, `..`, and leading `/`, and apply it to the pre-existing `resolve_player_portrait_url` (`asset_urls.py:76`) which has the same shape. Matches lang-review #11. Affects `sidequest-server/sidequest/genre/models/world.py` + `sidequest/foundation/asset_urls.py`. *Found by Reviewer during code review (converged: [SEC]+[EDGE]).*
- **Improvement** (non-blocking): the `genre_slug: str = ""` default on `_build_cartography_map_message` is a footgun — a future third caller that forgets to pass it silently ships a double-slash 404 image URL. Add an internal guard (`if mt.image and not genre_slug: skip image_url / raise`) so the function defends itself rather than trusting every caller. Affects `sidequest-server/sidequest/server/session_helpers.py`. *Found by Reviewer during code review ([EDGE]).*
- **Gap** (non-blocking): story 163-3's pack validator MUST enforce the raster content-completeness the model deliberately omits — raster requires `image` + `provenance`, `node_anchors` values must be exactly `[x, y]` (len==2), and every cartography region must have an anchor. Until 163-3 lands, a `raster` map.yaml with no image loads silently (partly mitigated: the `map.treatment_emitted` span exposes `has_image=false` to the GM panel). Affects `sidequest-server/sidequest/cli/validate/pack.py` (story 163-3). *Found by Reviewer during code review ([EDGE]).*
- **Improvement** (non-blocking): the sidequest-ui RasterMap consumer (story 163-5) must treat `style_hints`/`node_anchors` as untrusted author content — never interpolate into `dangerouslySetInnerHTML` or unescaped inline CSS. Affects `sidequest-ui` (story 163-5). *Found by Reviewer during code review ([SEC]).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **`raising=False` on the `resolve_asset_url` monkeypatches**
  - Spec source: plan 2026-07-08-mapping-track-a-main-map-treatments.md, tasks 6 & 7 (literal test code)
  - Spec text: `monkeypatch.setattr(sh, "resolve_asset_url", lambda p, **k: ...)` (default `raising=True`)
  - Implementation: added `raising=False` to the resolve_asset_url patches in `test_cartography_treatment_build.py` and `test_map_treatment_span.py`
  - Rationale: `resolve_asset_url` is imported into `session_helpers` by task 6, so in RED the name is absent; with `raising=True` the patch itself throws AttributeError and masks the real missing behavior. `raising=False` makes RED fail on the genuine gap (missing `genre_slug` param / absent span) and is a no-op-then-real-patch in green.
  - Severity: minor
  - Forward impact: none (identical behavior once the import lands in green)
- **Task-7 DB-readback test uses an inline `repo_and_sink`-style fixture, not `store_bound_to_hub`**
  - Spec source: plan task 7 ("Use the `store_bound_to_hub` fixture from tests/server/conftest.py if present; else replicate the `repo_and_sink` + `bind_event_store(sink)` pattern")
  - Spec text: prefer `store_bound_to_hub`
  - Implementation: authored an inline `bound_pg_sink` fixture modeled on `tests/game/test_mechanical_census_contract.py::repo_and_sink`
  - Rationale: `store_bound_to_hub` yields a dial-pack + StructuredEncounter shaped for combat census tests; it does not model a region-mode world with a `map_treatment`. The census-contract `repo_and_sink` (bare PG session + `PgTelemetrySink` + `bind_event_store`) is the exact shape this out-of-frame `publish_event` readback needs. The plan explicitly sanctions this fallback.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Threaded `genre_slug` through a second call site the plan did not enumerate**
  - Spec source: plan 2026-07-08-mapping-track-a-main-map-treatments.md, task 6
  - Spec text: "Call site in map_emit.py passes genre_slug param" (names ONLY the map_emit producer)
  - Implementation: also added `genre_slug=row.genre_slug` to the connect/resume producer at `sidequest/handlers/connect.py:2012`
  - Rationale: `_build_cartography_map_message` builds the treatment block unconditionally when `world.map_treatment` is set, so the connect caller — omitted from the plan — would have shipped a broken (double-slash) raster image URL on the bootstrap frame. Wiring BOTH producers is required by the "no half-wired features / verify wiring" rule; caught by pre-handoff code review.
  - Severity: minor
  - Forward impact: none — closes the gap; no sibling story depends on the connect path.
- No other deviations from spec — models, loader, protocol, emission, and OTEL span implemented exactly per plan tasks 3–7.

### Reviewer (audit)
- **TEA: `raising=False` on the resolve_asset_url monkeypatches** → ✓ ACCEPTED by Reviewer: correct idiom for patching a name the code-under-test introduces later; makes RED fail on real behavior, no-op-then-real in green. Verified identical behavior in the green run (17/17 pass).
- **TEA: task-7 DB-readback uses inline `repo_and_sink`-style fixture, not `store_bound_to_hub`** → ✓ ACCEPTED by Reviewer: `store_bound_to_hub` is dial-pack/encounter-shaped and wrong for a region-mode map_treatment scenario; the census-contract `repo_and_sink` pattern is the right minimal fixture and the plan explicitly sanctions the fallback. The resulting test is a genuine production-reachability wiring test.
- **Dev: threaded `genre_slug` through the connect/resume producer (connect.py:2012), a call site the plan did not enumerate** → ✓ ACCEPTED by Reviewer: this is the correct fix for a real wiring gap (double-slash image URL on the bootstrap frame); wiring BOTH producers is mandated by the "no half-wired features" rule. `row.genre_slug` is `TEXT NOT NULL` and validated upstream, so the threaded value is sound. Note: the residual `genre_slug: str = ""` default remains a footgun for future callers — captured as a non-blocking delivery finding (recommend an internal guard).

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt feature story (models, loader, protocol, emission, OTEL) — full RED coverage per plan tasks 3–7.

**Test Files:**
- `tests/genre/test_map_treatment_model.py` — MapTreatmentConfig/MapProvenance structure + fail-loud (task 3)
- `tests/genre/test_map_treatment_loader.py` — `_load_map_treatment` absent→None / valid / malformed→raises (task 4)
- `tests/protocol/test_cartography_treatment_wire.py` — CartographyTreatmentWire + payload.treatment serialize/default (task 5)
- `tests/server/test_cartography_treatment_build.py` — `_build_cartography_map_message` treatment population + asset-url resolve (task 6)
- `tests/server/test_map_treatment_span.py` — `map.treatment_emitted` capture tests + **DB-readback wiring test** (task 7)

**Tests Written:** 16 tests covering 5 ACs (plan tasks 3–7). Task 1 (baseline) verified green, not re-implemented.
**Status:** RED — all five files collection-error on the missing symbols (`MapProvenance`/`_load_map_treatment`/`CartographyTreatmentWire`), the correct feature-missing reason. Task-1 baseline `test_course_router_summary_wiring.py` confirmed GREEN (5 passed — 158-50 fold complete).

### Rule Coverage

| Rule (lang-review python.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| #11/#8 boundary validation — fail loud on malformed input | `test_unknown_treatment_kind_fails_loud`, `test_extra_key_fails_loud`, `test_provenance_forbids_extra_keys` | RED |
| No Silent Fallbacks (SOUL) — malformed map.yaml raises, absent→None by design | `test_malformed_map_yaml_raises_no_silent_fallback`, `test_absent_map_yaml_returns_none` | RED |
| #2 mutable defaults — per-instance collections not shared | `test_default_collections_are_not_shared_between_instances` | RED |
| Required-field integrity | `test_provenance_requires_all_four_fields` | RED |
| OTEL Observability Principle — span reaches turn_telemetry via publish_event (not Span.open) | `test_treatment_span_reaches_turn_telemetry` (DB-readback wiring) | RED |
| Every Test Suite Needs a Wiring Test (CLAUDE.md) | `test_treatment_span_reaches_turn_telemetry` drives the real `_maybe_emit_cartography_map` | RED |

**Rules checked:** 5 of the applicable lang-review/SOUL rules have test coverage (the story surface — model validation, loader, protocol, emission, OTEL — does not touch async/resource-leak/dependency rules).
**Self-check:** 0 vacuous assertions — every test asserts a specific value or a raised exception; no `assert True`, no `let _ =`, no truthy-only checks. The wiring test drives production code (`_maybe_emit_cartography_map`), not a reimplementation, and reads the authoritative PG store.

**Handoff:** To Dev (Hephaestus) for GREEN — implement plan tasks 3→4→5→6→7 in order.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (7 source):**
- `sidequest/genre/models/world.py` — `MapProvenance` + `MapTreatmentConfig` models (task 3)
- `sidequest/genre/models/__init__.py` — export both (task 3)
- `sidequest/genre/loader.py` — `_load_map_treatment` + leaf-loader wiring + `World(map_treatment=…)` (task 4)
- `sidequest/genre/models/pack.py` — `World.map_treatment` field (task 4)
- `sidequest/protocol/messages.py` — `CartographyTreatmentWire` + `payload.treatment` (task 5)
- `sidequest/server/session_helpers.py` — `genre_slug` param + treatment build + `resolve_asset_url` (task 6)
- `sidequest/server/websocket_handlers/map_emit.py` — pass `genre_slug` + `map.treatment_emitted` OTEL span (tasks 6, 7)
- `sidequest/handlers/connect.py` — thread `genre_slug` through the connect/resume producer (review fix; see Deviations)

**Tests:** 17/17 story tests GREEN (`-n0`), incl. the DB-readback wiring test `test_treatment_span_reaches_turn_telemetry` (proves the span reaches `turn_telemetry` via `publish_event`). Task-1 baseline (158-50) GREEN.

**Regression:** touched-module suite (`tests/genre tests/protocol` + 4 cartography server files) shows the IDENTICAL 46 failures with and without this change (diff empty both directions) → **0 new failures**. The 46 are pre-existing content/ruleset-migration drift (`162_*` bestiary detriplication, `neon` CWN, `space_opera` SWN, `elemental_harmony` WWN), matching the documented "WWN content breaks server fixtures."

**Lint:** ruff check clean on all touched files; format applied to branch-touched files only.

**Wiring verified:** real-pack load of `tea_and_murder` initializes `World.map_treatment=None` cleanly; both production producers of `_build_cartography_map_message` (per-turn + connect/resume) now thread `genre_slug`.

**Branch:** `feat/track-a-main-map-treatments` — pushed (commits: RED tests, GREEN impl, review fix). No PR (SM creates it in finish).

**Handoff:** To Reviewer (Hermes Psychopompos) for the review phase.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-08T23:16:21Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-08T23:47:04Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-08T23:47:04Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-08T23:47:04Z"/>
</skills-invoked>

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | 17/17 tests pass, lint clean, 0 new type errors, wiring complete — N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 4 (2 med, 2 low) | confirmed 4, dismissed 0, deferred 0 (all non-blocking) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed manually (see [SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — assessed manually (see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — assessed manually (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed manually (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (1 low-med, 1 low) | confirmed 2, dismissed 0, deferred 0 (all non-blocking) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed manually (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — assessed manually (see Rule Compliance + [RULE]) |

**All received:** Yes (3 enabled subagents returned: preflight, edge-hunter, security; 6 disabled via `workflow.reviewer_subagents` and assessed manually)
**Total findings:** 6 confirmed (all Medium/Low, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The implementation matches plan tasks 3–7 and its ACs exactly, is comprehensively tested (17/17 including a real DB-readback wiring test that proves `map.treatment_emitted` reaches `turn_telemetry` via `publish_event`), introduces **zero** new regressions (Dev's stash-diff proof: identical 46 pre-existing failures with/without the change), and is lint/type clean. The Dev's own pre-handoff review already caught and fixed the one real wiring bug (the connect/resume producer's missing `genre_slug`). My three subagents surfaced 6 further findings — all Medium/Low, none reaching the Critical/High blocking bar, and the content-completeness ones are by the plan's explicit design the domain of story 163-3 (the pack validator). Routed to delivery findings.

**Data flow traced:** author `map.yaml` → `_load_yaml_raw` (`yaml.safe_load`, fails loud on parse error) → `_load_map_treatment` (absent→None, malformed→`ValidationError`) → `World.map_treatment` → `_build_cartography_map_message` (builds `CartographyTreatmentWire`, resolves `image` via `resolve_asset_url` → client URL string) → `CartographyMapPayload.treatment` on the `MAP_UPDATE` frame → both producers (per-turn `map_emit` + connect/resume bootstrap) → `map.treatment_emitted` OTEL span (per-turn) → `turn_telemetry`. Safe: no server-side filesystem read of the author-controlled `image`; safe YAML; typed additive wire field.

**Pattern observed:** additive-optional field + fail-loud pydantic model + per-turn OTEL span — mirrors the existing `cartography.map_emitted` seam at `map_emit.py:1226`. Consistent with codebase convention (`resolve_player_portrait_url` uses the same `resolve_asset_url` composition at `asset_urls.py:76`).

### Rule Compliance (lang-review python.md #1–#13 + SOUL)

Enumerated every new type/function against each applicable rule (rule-checker was disabled; this is my manual backstop):

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | `_load_map_treatment`, treatment-build block, span block — no try/except in new code; `model_validate` raises upward | COMPLIANT |
| #2 mutable defaults | `MapTreatmentConfig.node_anchors`/`style_hints`, `CartographyTreatmentWire.node_anchors`/`style_hints` — all `Field(default_factory=dict)` | COMPLIANT (test-enforced) |
| #3 type annotations | `_load_map_treatment(world_path: Path) -> MapTreatmentConfig \| None`; `genre_slug: str = ""`; all model fields typed | COMPLIANT |
| #4 logging | no new error paths that swallow; span logs counts/enums | COMPLIANT |
| #5 path handling | `world_path / "map.yaml"` (pathlib); `read_text(encoding="utf-8")`; `mt.image`→URL string (not FS) — see [SEC] note on hardening | COMPLIANT (Low hardening note) |
| #6 test quality | 17 tests, all meaningful asserts; DB-readback wiring; 0 vacuous | COMPLIANT |
| #7 resource leaks | DB test uses `with pool.connection()`; fixture try/finally unbinds + closes pool | COMPLIANT |
| #8 unsafe deserialization | `yaml.safe_load` only | COMPLIANT |
| #9 async pitfalls | no async in new code | N/A |
| #10 import hygiene | no star imports; `__all__` updated for both new models | COMPLIANT |
| #11 input validation | `extra="forbid"` + `Literal` enum validate map.yaml at the boundary; `image` string not path-validated — see [SEC]/[EDGE] | COMPLIANT for structure; `image` path-hardening deferred (Medium) |
| #12 dependency hygiene | no dependency changes | N/A |
| #13 fix regressions | connect.py fix introduces no new issue class (verified) | COMPLIANT |

### Observations (subagent findings incorporated, tagged by source)

1. `[EDGE][SEC] [MEDIUM]` **Unsanitized `genre_slug`/`mt.image` f-string** at `session_helpers.py:1690-1693`. Two specialists converge here. (a) An empty `genre_slug` yields a `genre_packs//worlds/...` double-slash URL that silently 404s; not reachable via the two current production callers (both thread a validated `genre_slug` — `connect.py`'s is `TEXT NOT NULL` + validated upstream at `connect.py:582`), but the function's `genre_slug: str = ""` default leaves no internal defense against a future caller. (b) A `map.yaml` author could set `image: "../.."` to re-point the rendered map image to another object within the already-public CDN root — **not** a filesystem read (Starlette StaticFiles containment blocks local mode; CDN is object storage) and **not** cross-host. Matches lang-review #11; mirrors the pre-existing `resolve_player_portrait_url` pattern. → Confirmed, non-blocking; recommend a shared `_validate_asset_filename` field-validator (delivery finding).
2. `[EDGE] [MEDIUM]` **`raster` treatment with no image loads silently** (`loader.py`/model). The model defers raster-requires-image to 163-3 by explicit design (docstring `world.py:271`). Partially mitigated *today* by the OTEL span: a raster with `has_image=false` is visible to the GM panel (`map_emit.py` span field `has_image`). → Confirmed, non-blocking; the completeness gate is story 163-3 (delivery finding).
3. `[EDGE] [LOW]` **`node_anchors: dict[str, list[float]]` has no len==2 constraint** (`world.py:283`) — `[10]` or `[10,20,30]` passes to the wire. Content-shape, 163-3 validator territory. → Confirmed, non-blocking.
4. `[EDGE] [LOW]` **Empty/blank `map.yaml` == absent** (`loader.py`): `yaml.safe_load("")` → None → treated as absent (dag fallback). Explicitly matches the pre-existing `_load_yaml_raw_optional` convention (edge-hunter agrees it is *not* a deviation introduced here). → Confirmed, non-blocking.
5. `[SEC] [LOW]` **`style_hints`/`node_anchors` forwarded verbatim to the UI** (`messages.py` `CartographyTreatmentWire`). No unsafe server sink; the span logs only counts/enums (no raw content). Forward note for the sidequest-ui story (avoid `dangerouslySetInnerHTML`/unescaped CSS). → Confirmed, non-blocking.
6. `[SIMPLE] [LOW]` **Incidental ruff-format reflows** at `map_emit.py:271/365` (Track B `_maybe_build_runtime_cavern_payload`/`_maybe_emit_tactical_grid`) and `loader.py:1452` — pure whitespace/line-wrap, no logic change; minor diff noise near the Track B boundary. → Confirmed, non-blocking, cosmetic.
7. `[VERIFIED]` **YAML load is safe** — `_load_yaml_raw` uses `yaml.safe_load` at `loader.py:204`, wraps parse errors in `GenreLoadError`. Complies with lang-review #8.
8. `[VERIFIED]` **No silent fallback in the loader** — `_load_map_treatment` (`loader.py:1079`) returns None only for an absent file; malformed → `model_validate` raises (`ValidationError`). Test-proven (`test_malformed_map_yaml_raises_no_silent_fallback`). Complies with SOUL No-Silent-Fallbacks.
9. `[VERIFIED]` **Span None-safety** — `len(msg.payload.cartography.get("regions", {})) if msg.payload.cartography else 0` (`map_emit.py:1254`): edge-hunter confirmed `cartography` is structurally never None on this path (the builder's only non-None return populates it as a literal dict alongside `treatment`). No KeyError/AttributeError.
10. `[SILENT][TEST][DOC][TYPE][RULE]` **(disabled-subagent domains, assessed manually — 6 of 9 subagents off via settings)** — [SILENT]: no swallowed errors in new code — the loader raises `ValidationError`/`GenreLoadError` upward (no bare except, no `pass`), and the one nearby `except Exception` at `map_emit.py:271` is pre-existing and logs at warning level (see obs 8). [TEST]: preflight confirms 17/17 pass; assertions meaningful; DB-readback wiring present; TEA self-checked 0 vacuous. [DOC]: docstrings on both new models + `_load_map_treatment` + `CartographyTreatmentWire` are accurate and thorough; no stale comments introduced. [TYPE]: pyright reports 0 new errors on the 7 touched files; `Literal` enum + `Optional` + `default_factory` are sound; the anchor-len concern is captured under [EDGE] #3. [RULE]: I performed the exhaustive rule enumeration myself (Rule Compliance table above, lang-review #1–#13 + SOUL) — one Medium hardening note on #11 (`image` path validation), everything else compliant.

### Devil's Advocate

Assume this code is broken. Where would it bite?

A malicious *player* cannot reach any of this — `map.yaml` is loaded once at pack-load from disk, not from any player input; nothing on the WebSocket turn path lets a player inject a treatment. The only actor with influence is a **content author** writing `map.yaml`, and CLAUDE.md deliberately widens that role beyond Keith (Jade is the first non-Keith author, "wizards to follow" — the human-PR-review bar may loosen). So the adversary I must fear is a careless or hostile author. What can they do? (1) A `../..` in `image` — but I traced this: it produces a URL string, not a server read; Starlette StaticFiles' `realpath`+`commonpath` containment blocks local-mode traversal, and CDN mode is object storage with a fixed host, so the worst case is re-pointing one world's map image at another *already-public* asset. No confidentiality or integrity breach, no cross-host. Real, but Low-Medium, and the identical shape already ships unguarded in `resolve_player_portrait_url`. (2) A `raster` with no `image` — ships `image_url=None`; but the plan's UI contract is an explicit RasterMap error state (never a silent dag fallback), and the OTEL span already flags `has_image=false` to the GM panel, so it is not truly silent. (3) A malformed `map.yaml` — fails loud at pack load (`ValidationError`/`GenreLoadError`), which halts the pack, exactly as intended. (4) A confused author writing an *empty* `map.yaml` — treated as absent (dag fallback); mildly surprising but harmless and consistent with every other optional loader. (5) A stressed filesystem — `read_text` raises `OSError`→`GenreLoadError` (fails loud). (6) Unexpected keys — `extra="forbid"` rejects them. (7) A future engineer adding a third caller of `_build_cartography_map_message` who forgets `genre_slug` — reintroduces the double-slash URL; the `genre_slug: str = ""` default is a genuine footgun (the strongest argument for the recommended internal guard). None of these rise to data loss, crash-on-turn, security breach, or a broken *current* production path. The residual risks are hardening/robustness improvements whose correct home is story 163-3's validator plus a small defensive guard — recorded as delivery findings. Verdict stands: **APPROVED**.

**Handoff:** To SM (Themis the Just) for finish-story.