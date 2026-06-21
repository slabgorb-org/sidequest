---
story_id: "153-26"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-26: [DUNGEON-CURATE-TIMEOUT] keep dungeon room curate within the 25s wall-clock cap (precurate/stream) so authored room content and encounters are not dropped to the degraded deterministic manifest

## Story Details
- **ID:** 153-26
- **Jira Key:** (Jira integration disabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T15:54:05Z
**Round-Trip Count:** 1
**Repos:** server
**Branch:** feat/153-26-dungeon-curate-timeout

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T14:12:29Z | - | - |
| red | 2026-06-21T14:12:29Z | 2026-06-21T14:40:26Z | 27m 57s |
| green | 2026-06-21T14:40:26Z | 2026-06-21T14:54:17Z | 13m 51s |
| review | 2026-06-21T14:54:17Z | 2026-06-21T15:06:35Z | 12m 18s (REJECTED → rework) |
| green | 2026-06-21T15:06:35Z | 2026-06-21T15:30:19Z | 23m 44s |
| review | 2026-06-21T15:30:19Z | 2026-06-21T15:42:10Z | 11m 51s |
| green | 2026-06-21T15:42:10Z | 2026-06-21T15:47:50Z | 5m 40s |
| review | 2026-06-21T15:47:50Z | 2026-06-21T15:54:05Z | 6m 15s |
| finish | 2026-06-21T15:54:05Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Argus Panoptes) for RED.**

- **Story:** 153-26 `[DUNGEON-CURATE-TIMEOUT]` — p1, 3pts, tdd. Claimed `in_progress` (assigned keith, started 2026-06-21).
- **Repo / branch:** sidequest-server, `feat/153-26-dungeon-curate-timeout` (off `develop`).
- **Workflow:** tdd (phased) → next phase **red**, owner **TEA**.

**Read the context doc first — it is the authoritative contract:** `sprint/context/context-story-153-26.md` (188 lines). It carries exact `materializer.py` line refs, the real degrade log (`elapsed_ms=30337` vs the 25.0s cap), a perf+correctness root-cause split, the full Key-Code-Areas map, and **5 precise ACs**. Write the failing tests FROM those 5 ACs — do not re-derive scope.

**Heads-up (doc provenance):** that context doc was clobbered to a thin placeholder by sm-setup's `pf context create` and restored verbatim from `d0723d2` (commit `2871821`). It is now correct and authoritative; the story YAML deliberately keeps `acceptance_criteria: []` (the ACs live in the context doc).

**Two-part bug** (both must be covered by RED tests):
1. **Perf** — curate blows the 25.0s wall-clock cap on a multi-region expansion (one whole-expansion prompt; deadline scales with band size). Fix direction: pre-curate ahead of arrival (`dungeon/lookahead_worker.py`), per-region chunk, and/or an honest per-region budget. Extend the ladder, don't replace it.
2. **Correctness** — the Layer-2 degraded path (`_degrade_region` / `_creatures_from_manifest`) never reads authored `rooms/*.yaml`, so it silently drops authored `encounter_creatures` (e.g. `entrance` → `gnaw_swarm`). Even when curate degrades, authored content must still surface via the LLM-free `resolve_room_creatures`.

**Key test seam (for the AC5 wiring/integration test):** `CURATE_DEADLINE_S` (`materializer.py:191`) is module-level and **injectable** — set it tiny to force a real degrade through the materialize path, then assert (a) the authored `encounter_creatures` still ships and (b) both `dungeon.curate.degraded` AND the authored-content-preserved span (`monster_manual.room_bound`) fired. Loudness contract (ADR-106 Amendment A: `curated=false` + ERROR log) must be preserved — this story reduces how often degrade fires and stops it eating authored content; it does NOT silence it.

**Notes for TEA:** reuse-first — `assemble_region`, the `_degrade_region` Layer-2 ladder, and `resolve_room_creatures` all already exist. Out of scope: the 153-23 room-population wiring and 153-27 procedural-region zone/cast eligibility (reference only).

## Tea Assessment

**RED complete — 4 failing/guard tests committed. Routing to Dev (Hephaestus) for GREEN.**

- **Test file:** `sidequest-server/tests/dungeon/test_153_26_curate_authored_content.py` (commit `66045953` on `feat/153-26-dungeon-curate-timeout`).
- **Verified RED via testing-runner** (run_id `153-26-tea-red`): `3 failed, 1 passed` — each failure matches the AC contract; no collection errors; lint clean.

| Test | AC | Outcome (develop) | Why it fails / what GREEN must do |
|------|----|-------------------|-----------------------------------|
| `test_degraded_region_surfaces_authored_encounter_creatures` | AC2+AC4 | FAIL (`pytest.fail`: no `pack`) | Thread a genre `pack` into `_stage_curate`; on Layer-2 degrade, call `resolve_room_creatures(pack, request.world_slug, region_id)` and add the authored creatures to `region_creatures[rid]` (built as `CuratedCreature`s with an `HpPool` from the bestiary entry). `monster_manual.room_bound` then fires for free (it's emitted inside `resolve_room_creatures`). |
| `test_one_slow_region_degrades_alone_not_the_whole_band` | AC1 | FAIL (both regions degrade) | Make the curate wall-clock cap **per-region** (chunk the one whole-band `complete_with_tools` call into per-region calls under per-region timeouts, and/or an honest per-region budget). The deadline must not scale with band size. |
| `test_forced_deadline_degrade_stays_loud` | AC3 | **PASS** (guard) | Regression guard — keep the degrade LOUD (`curated=False`, `uncurated_regions`, ERROR log, `dungeon.curate.degraded` span). Do NOT silence while fixing AC2. |
| `test_materialize_degrade_preserves_authored_content_end_to_end` | AC5 | FAIL (`pytest.fail`: no `pack`) | Add/thread `pack` through `materialize(...)` → `_stage_curate` so the behavior holds through the real five-stage pipeline (uses the `migrated_db` Postgres fixture — pg confirmed up). |

**Hard contract for the `pack` parameter (don't break the existing suite):** `pack` MUST be **optional (default `None`)**. The large existing `_stage_curate`/`materialize` test suites do not pass it, and a packless degrade must keep working (current behavior, minus authored-content preservation). Make `pack` resolution loud only where a pack IS supplied.

**Test-design choices (read before implementing):**
- The authored-content ACs are driven at the **`materialize()` boundary (AC5)** and the **`_stage_curate` boundary (AC2)** rather than grepping source — per the server CLAUDE.md "No Source-Text Wiring Tests" rule. AC2/AC5 use a duck-typed `_authored_pack` fixture (`source_dir` + `effective_bestiary`) writing a real `rooms/<id>.yaml`; assertions are on emitted spans + the returned `CuratedCreature` names. The two `inspect.signature(...).parameters` guards are the **blessed reflection-based tripwire** (CLAUDE.md exception), not source-text matching.
- AC1 (`_slow_for_region_sdk_client`) sleeps only when the slow region is in the curate call's INPUT, so it cleanly separates "one whole-band call" (RED: both degrade) from "per-region calls" (GREEN: fast sibling curated). This intentionally requires the **structural** fix (per-region isolation), not just a bigger `CURATE_DEADLINE_S` or pre-curate-alone — see the Design Deviation note.

### Rule Coverage (`.pennyfarthing/gates/lang-review/python.md`)

| Rule | Covered by |
|------|-----------|
| #1 Silent exception swallowing / No Silent Fallbacks | AC3 asserts the degrade still logs at ERROR and routes `dungeon.curate.degraded`; a fix that swallows the timeout fails AC3. |
| #4 Logging coverage + correctness | AC3 asserts the ERROR-level "dungeon curate degraded" log fires. |
| #6 Test quality | Self-checked — no vacuous assertions; every test asserts concrete state (span presence, `CuratedCreature` names, `uncurated_regions` membership), not bare truthiness. |
| #9 Async/await pitfalls | All four tests drive the real `await _stage_curate` / `await materialize` async path under an injected `asyncio.timeout`; a blocking-sleep or wrong-timeout-scope regression in the per-region fix surfaces in AC1. |
| #8 Unsafe deserialization | The authored binding is read via `resolve_room_creatures` → `yaml.safe_load` (existing, safe); the fix reuses it rather than re-parsing. |

Other checklist rules (#2 mutable defaults, #3 type annotations, #5 path handling, #7 resource leaks, #10–#13) are Dev self-review concerns at GREEN — flagged for Hephaestus, not separately tested at RED.

## Dev Assessment

**GREEN complete — all 4 tests pass, 139/139 across the curate suite + callers, zero regressions. Routing to Reviewer (Hermes).**

- **Impl commit:** `6979b4c3` on `feat/153-26-dungeon-curate-timeout` (4 files, +143/−35).
- **Verified GREEN via testing-runner** (run_id `153-26-dev-green`): `139 passed, 0 failed`; ran the new file + `test_materializer.py` + `test_materializer_wiring.py` + `test_materializer_room_yaml.py` + `test_lookahead_worker.py` + `test_session_integration.py` + `test_setpiece_attach.py`. No collection errors, no OTEL deadlock. Existing curate/degrade tests (deadline, llm_error, per_region_partial, truncated, missing_cr) all still green.

**What I changed (`sidequest/dungeon/`):**
1. **Honest per-region budget (AC1)** — `materializer.py::_stage_curate`: the band timeout is now `asyncio.timeout(CURATE_DEADLINE_S * max(1, len(manifests)))`. `CURATE_DEADLINE_S` is the per-region budget; the band gets N× it. One whole-band call kept → **no curate call-count/cost change** (per Keith's chosen approach). Only the timeout value scales, so the existing whole-band `_per_region_partial` test is untouched.
2. **Authored content survives degrade (AC2/AC4/AC5)** — new `materializer.py::_append_authored_creatures` consults the LLM-free `resolve_room_creatures` on the Layer-2 degrade path (it emits `monster_manual.room_bound`), building `CuratedCreature`s from the bestiary entry via `hp_pool_from_hp`. Threaded an **optional** `pack` (default `None`) through `materialize()` → `_stage_curate` → `_degrade_region`. Packless degrade keeps its prior loud shape (existing suite unaffected).
3. **Production wiring** — both `materialize()` callers now pass the genre pack: `session_integration.py` (`pack=genre_pack`) and `lookahead_worker.py` (`pack=self.pack_tropes`). This closes the wiring Delivery Finding (the fix is live in prod, not just tests).

**Loudness preserved (AC3):** `curated=false`, `uncurated_regions`, the ERROR log, and the `dungeon.curate.degraded` span are all unchanged. A bad authored binding still fails loud inside `resolve_room_creatures` (authoring error, surfaced even on degrade).

**Self-review (python.md):** immutable defaults (`pack=None`/`world_slug=""`); no swallowed exceptions; local import of `resolve_room_creatures` (cycle-avoidance, commented); `Any` justified for the duck-typed pack; async timeout correct. Clean.

**For Reviewer:** the one judgment call worth a look is letting `RoomCreatureBindingError` propagate on the degrade path (an authoring error fails loud rather than being swallowed into a graceful degrade) — consistent with the existing `monster_manual_inject` caller and No-Silent-Fallbacks. The production binding (`gnaw_swarm`) is valid, so it won't fire in practice.

---

### Dev Rework Assessment (review round 2 — REJECTED → re-GREEN)

**Rework complete — all 3 required findings fixed, TDD'd, 151 passed / 0 failed across the dungeon group + room-binding suite, telemetry 417 passed, ruff + pyright clean.**

The Reviewer's central correction stands: the round-1 "let it fail loud by **crashing**" judgment call was an *over-correction* of No-Silent-Fallbacks on the very path ADR-106 Amendment A designed to be crash-free. The degrade must be loud-**but-graceful** (log + span + proceed), not loud-by-crash. All three findings were verified against the code before implementing (None-bestiary `AttributeError` reproduced at `room_creature_binding.py:76`; unbounded `band_deadline_s` confirmed; silent `entry is None` `continue` confirmed).

**What I changed (rework):**
1. **[HIGH] Loud-but-graceful broken binding on degrade.**
   - `room_creature_binding.py::resolve_room_creatures` now raises `RoomCreatureBindingError` (not a raw `AttributeError`) when `effective_bestiary` returns `None` for a *declared* binding — same typed authoring-error signal as a dangling ref.
   - `materializer.py::_append_authored_creatures` now **catches** `RoomCreatureBindingError` → ERROR log + new `dungeon.curate.authored_bind_failed` OTEL span (stays LOUD) → returns creatures unchanged so the degrade **proceeds with procedural coal** instead of crashing the player-facing bootstrap `await materialize()` at connect.
   - New span `SPAN_DUNGEON_CURATE_AUTHORED_BIND_FAILED` declared + routed in `telemetry/spans/dungeon_materialize.py` (the GM-panel lie-detector for a dropped authored binding).
   - New degrade-path test (`test_degrade_with_bad_authored_binding_stays_loud_but_graceful`) + a `None`-bestiary unit test (`test_resolve_raises_binding_error_not_attribute_error_on_none_bestiary`).
2. **[MEDIUM] Bounded freeze ceiling.** New module constant `MAX_BAND_DEADLINE_S = 120.0`; `band_deadline_s = min(CURATE_DEADLINE_S * max(1, len(manifests)), MAX_BAND_DEADLINE_S)` — refines (does not reverse) Keith's honest-budget cap-scaling so a 6-region bootstrap band can never hold the connect open for minutes. New test `test_band_deadline_is_bounded_by_max_ceiling`.
3. **[LOW] Observable `entry is None`.** Split the lumped `continue`: a divergent-bestiary-read miss now logs at ERROR (kept the name-match `continue` silent — that is the expected "procedural manifest already shipped it" case).

**Also fixed (test-isolation — see Deviation + Delivery Finding):** the pre-existing AC5 test drove the real `materialize()` with `genre_slug="caverns_and_claudes"`, so `_resolve_world_dir` resolved the **real** content pack and the commit stage deposited (gitignored) `worlds/test_world/rooms/*.yaml` into it — breaking sibling `load_genre_pack` tests run in the same session (this masqueraded as 4 "failures" in the round-1-vs-now group run). Redirected the AC5 room-emit to a tmp dir via `monkeypatch.setattr(_mat, "_resolve_world_dir", ...)`; the suite is now hermetic (verified: zero real-content pollution after a full group run).

**Files changed (rework):**
- `sidequest/dungeon/materializer.py` — catch + loud-graceful span; `entry is None` ERROR log; `MAX_BAND_DEADLINE_S` ceiling.
- `sidequest/server/dispatch/room_creature_binding.py` — `None`-bestiary → `RoomCreatureBindingError`.
- `sidequest/telemetry/spans/dungeon_materialize.py` — new `dungeon.curate.authored_bind_failed` span (constant + route + helper + `__all__`).
- `tests/dungeon/test_153_26_curate_authored_content.py` — 2 new tests + AC5 isolation fix.
- `tests/server/dispatch/test_room_creature_binding_107_2.py` — 1 new `None`-bestiary test.

**Verification:** `uv run pytest -n0` over the new file + `test_room_creature_binding_107_2.py` + `test_materializer.py` + `_wiring` + `_room_yaml` + `test_lookahead_worker.py` + `test_session_integration.py` + `test_setpiece_attach.py` → **151 passed, 0 failed**; `tests/telemetry/` → **417 passed**; `ruff check` + `ruff format --check` + `pyright` → clean on all touched files.

**Handoff:** To Reviewer (Hermes Psychopompos) for re-review.

---

### Dev Rework Assessment (review round 3 — round-2 REJECTED → re-GREEN)

**Rework complete — the round-2 blocking HIGH is fixed, TDD'd, 153 passed / 0 failed + happy-path caller regression-checked (54 passed). Routing back to Reviewer.**

The round-2 Reviewer (my own adversarial pass) confirmed a real gap: `_append_authored_creatures`' `except RoomCreatureBindingError` was too narrow — a **malformed or unreadable `rooms/<id>.yaml`** raises `yaml.YAMLError`/`OSError` from `resolve_room_creatures`' `yaml.safe_load`, which escaped the catch and crashed the player-facing bootstrap connect on degrade (the round-1 crash class via a sibling exception). Verified RED first (the `ParserError` propagated out of `_stage_curate`), then fixed.

**What I changed (round 3 — 1 source file, 2 tests):**
1. **[HIGH fix] Typed read/parse errors.** `room_creature_binding.py:67` — the room-file read+parse is now wrapped in `try/except (yaml.YAMLError, OSError) → raise RoomCreatureBindingError(...) from exc`. A malformed/unreadable room file is now the **same typed authoring-error** as a dangling ref, so the existing `_append_authored_creatures` catch covers it: the degrade stays LOUD (ERROR log + `dungeon.curate.authored_bind_failed` span) and proceeds with procedural coal — no connect crash.
2. **Two new tests:** `test_resolve_raises_binding_error_not_yaml_error_on_malformed_room_yaml` (unit) and `test_degrade_with_malformed_room_yaml_stays_loud_but_graceful` (degrade-path, loud + graceful + proceeds).

**Why this scope (see Deviation):** I took the "re-raise in `resolve_room_creatures`" branch of the Reviewer's "and/or". The folded edges #2 (second `effective_bestiary` call) and #6 (non-bestiary `pack`) are **production-impossible** per the Reviewer's own VERIFIED notes (real `GenrePack.effective_bestiary` is pure; `pack_tropes` IS the full pack). Adding a speculative `hasattr` no-op would itself be a silent fallback (rule #1), so I deliberately did not.

**No happy-path regression (verified):** `monster_manual_inject.py:529` (the happy-path caller) does NOT catch `RoomCreatureBindingError`, so a malformed YAML still fails loud there (typed error instead of `YAMLError`). `tests/server/dispatch/` monster_manual/room_creature suite → **54 passed**.

**Files changed (round 3):**
- `sidequest/server/dispatch/room_creature_binding.py` — typed re-raise of `yaml.YAMLError`/`OSError`.
- `tests/server/dispatch/test_room_creature_binding_107_2.py` — +1 malformed-YAML unit test.
- `tests/dungeon/test_153_26_curate_authored_content.py` — +1 malformed-YAML degrade-path test (+ helper).

**Verification:** dungeon group + binding → **153 passed, 0 failed**; `tests/telemetry/` → **417 passed**; happy-path `monster_manual`/`room_creature` → **54 passed**; `ruff check` + `ruff format --check` + `pyright` → clean; no real-content pollution.

**Handoff:** To Reviewer (Hermes Psychopompos) for re-review.

## Subagent Results (round 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (66 passed/0 failed, lint clean) | 1 nominal | confirmed 0; the `pack=self.pack_tropes` "same object two slots" note → VERIFIED intentional |
| 2 | reviewer-edge-hunter | Yes | findings | 5 | confirmed 3 (1 HIGH = #1+#2 unified, 1 MEDIUM = #3, 1 LOW = #5), folded 1 (#4 → into the HIGH fix), dismissed 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — covered by me + security |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — covered by me |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — covered by me |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — covered by me (#4 type note) |
| 7 | reviewer-security | Yes | clean | none | N/A — region_id server-minted, path not attacker-reachable, yaml.safe_load + encoding present |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — covered by me (#5 redundant call) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — Rule Compliance done by me below |

**All received:** Yes (3 enabled returned: preflight clean/green, security clean, edge-hunter 5 findings; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (1 HIGH, 1 MEDIUM, 1 LOW), 1 folded, 0 dismissed

## Reviewer Assessment (round 1 — REJECTED, superseded by rework)

**VERDICT: REJECTED** — one HIGH (blocking) finding. The change is well-targeted and correct on the happy path (139 green, wiring verified, security clean, loudness preserved), but it adds a NEW way for a degrade to crash, on the very path ADR-106 Amendment A designed to be crash-free. Small, well-defined rework.

### Observations
1. **[HIGH][EDGE] New uncaught crash path on the Layer-2 degrade.** `_append_authored_creatures` (materializer.py:1035) calls `resolve_room_creatures`, which raises `RoomCreatureBindingError` on an unknown bestiary id — and `AttributeError` on a `None` bestiary (room_creature_binding.py:76 dereferences `bestiary.entries` with no guard). Nothing in `_degrade_region` / `_stage_curate` / `materialize` catches it. On the bootstrap path (`session_integration.attach_dungeon_to_session` → `await materialize()` at connect, `connect.py:1170`) the exception propagates and **crashes session start** — and **no validator catches a mistyped room binding at load** (confirmed: grep found none). So a single content typo can intermittently brick a world's sessions (only when curate degrades — non-deterministic). This contradicts the ADR-106 Amendment A degrade contract ("LOUD degrade, the turn proceeds, no table freeze") that `_degrade_region`'s own docstring states. **Fix:** `_append_authored_creatures` must catch `RoomCreatureBindingError` (and resolve_room_creatures must raise that, not `AttributeError`, on a `None` bestiary) → log ERROR + emit an OTEL span (stays LOUD) + return creatures unchanged (degrade proceeds with procedural coal). Add a test for the bad-binding degrade path.
2. **[MEDIUM][EDGE] Unbounded freeze ceiling.** `band_deadline_s = CURATE_DEADLINE_S * max(1, len(manifests))` (materializer.py:1320) has no upper bound. `len(manifests)` = `len(expansion.new_nodes)`, drawn from `JaquaysConfig.new_regions_per_expansion` (lo=3, hi=6) → up to `6 * 25 = 150s`. The bootstrap `materialize` is `await`ed on the connect handler, so a stuck curate can hold the connect open ~150s — removing the documented "no multi-minute freeze" guarantee (the old fixed 25s cap). **Fix:** `band_deadline_s = min(CURATE_DEADLINE_S * max(1, len(manifests)), MAX_BAND_DEADLINE_S)` with a sane ceiling (e.g. 120s). This refines Keith's chosen cap-scaling (an honest budget should still be bounded), not reverses it.
3. **[LOW][EDGE] Silent `continue` on `entry is None`.** materializer.py:1049 — after a redundant *second* `effective_bestiary` call, an id `resolve_room_creatures` already validated could miss `by_id` (if the call ever diverged) and be dropped with no log. Production `effective_bestiary` is pure, so low risk; add a one-line ERROR log on that branch for observability.
4. **[VERIFIED] pack wiring correct (no half-wiring).** Both production call sites pass the full `GenrePack`: `session_integration.py:193` `pack=genre_pack`, and `lookahead_worker.py:385` `pack=self.pack_tropes` where `self.pack_tropes` is set from `register_lookahead_worker(pack_tropes=genre_pack)` (session_integration.py:223). `GenrePack` defines `source_dir` (pack.py:490) + `effective_bestiary` (pack.py:540), the two attrs `resolve_room_creatures` needs. Confirmed by preflight.
5. **[VERIFIED] Loudness preserved (AC3).** `_degrade_region` retains the ERROR log + `dungeon.curate.degraded` span (materializer.py:1085-1103); `test_forced_deadline_degrade_stays_loud` green; reviewer-security confirmed no silencing.
6. **[VERIFIED][SEC] No security exposure.** `region_id` is server-minted `exp{id:03d}.r{i}` (generator.py:76), `world_slug` session-bound, `source_dir` from startup — path not attacker-reachable; `yaml.safe_load` + `encoding="utf-8"` present (room_creature_binding.py:67). reviewer-security returned CLEAN (0 findings) — path-traversal, unsafe-deserialization, and info-leakage all checked and cleared.
7. **[VERIFIED] Existing curate suite preserved.** Packless degrade (existing tests pass `world_slug=""`) no-ops `_append_authored_creatures`; single-region timeout (`n=1`) is unchanged; `_per_region_partial` untouched (only the timeout *value* scaled, not the call structure). 139/139 green.

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`)
- **#1 No Silent Fallbacks** — VIOLATION-adjacent: the HIGH finding is actually an *over-correction* of #1 — the code fails loud by **crashing** the bootstrap, where the degrade contract wants loud-**but-graceful** (log + span + proceed). The fix keeps it loud without the crash. The `pack=None`/blank-`world_slug` no-op is a documented absent-binding, not a silent fallback — compliant.
- **#2 Mutable defaults** — compliant (`pack=None`, `world_slug=""`).
- **#4 Logging** — degrade ERROR log preserved; the HIGH fix must ADD an ERROR log on the caught binding error.
- **#6 Test quality** — new tests are non-vacuous; **gap:** no test covers the bad-binding/None-bestiary degrade path (the HIGH fix must add one).
- **#9 Async** — timeout scaling is async-correct; no blocking calls introduced.
- **#3/#5/#7/#8/#10–#13** — no relevant surface in the diff.

### Devil's Advocate
Assume this is broken. A world author fat-fingers a room binding (`gnaw_swarm` → `gnaw_swrm`). Content loads clean — nothing validates room `encounter_creatures` against the bestiary (verified). Sessions run fine for days. Then curate degrades on that region — which is *more* likely now, since this very story exists because curate degrades — and `resolve_room_creatures` finds the dangling id and raises. On bootstrap that propagates out of `await materialize()` at connect and the session never starts; the failure is **intermittent** (only on degrade) and gives the author no clear signal. Worse, a world with room bindings but *no* bestiary at all hits a raw `AttributeError` at room_creature_binding.py:76 — an uglier crash with a worse message. Now layer the freeze ceiling: a 6-region bootstrap band behind a hung LLM holds the connect ~150s *before* the degrade (and its crash) even fires — a 2.5-minute hang then a crash. So a change whose entire purpose is to make degrades survive better has introduced two new ways for a degrade to behave *worse*: a hard crash and a multi-minute freeze, both on the player-facing connect path. A malicious actor can't reach it (inputs are server-minted), but a *confused author* — exactly the person ADR-140/Jade's homebrew path is built for — can brick their own world and not know why. The fixes are small (a try/except that logs+proceeds; a `min()` ceiling) and restore both load-bearing guarantees the degrade path is supposed to keep.

### Deviation Audit
- **TEA deviation (AC1 chunking/isolation):** → ✓ ACCEPTED as SUPERSEDED — correctly retired by the Dev deviation after Keith chose honest-budget; no action.
- **Dev deviation (AC1 honest per-region budget, test retuned):** → ✓ ACCEPTED by Reviewer — user-directed, sound, and the retuned test genuinely exercises the band-proportional property. (The MEDIUM ceiling finding refines this deviation; it does not reverse it.)

### Required for re-approval
1. **[HIGH]** Catch `RoomCreatureBindingError` in `_append_authored_creatures` → loud (ERROR + span) but graceful (return creatures unchanged); fix `resolve_room_creatures` `None`-bestiary to raise `RoomCreatureBindingError` not `AttributeError`; add a degrade-path test for a bad/absent binding.
2. **[MEDIUM]** Bound `band_deadline_s` with a `MAX_BAND_DEADLINE_S` ceiling.
3. **[LOW]** Log on the `entry is None` branch.

## Subagent Results (round 2)

Round 2 re-review of the rework (commit `27064ea7`). Enabled subagents (toggles unchanged: preflight, edge_hunter, security on; 6 disabled).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (568 passed/0 failed; ruff + pyright clean; new span routed) | confirmed 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 1 HIGH (#1 yaml/OS uncaught), folded 2 into it (#2 2nd-bestiary, #6 pack_tropes), 3 LOW non-blocking (#3 src_dir, #5 ceiling-obs, #7 AC5 round-trip), 1 dismissed (#4 empty-band span — incorrect) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (path-traversal, unsafe-deser, info-leak all CLEAN) | confirmed 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned: preflight clean/green, security clean, edge-hunter 7 findings; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed HIGH (2 folded in), 3 deferred LOW (non-blocking), 1 dismissed

## Reviewer Assessment (round 2 — REJECTED, superseded by rework)

**VERDICT: REJECTED** — one HIGH (blocking) finding. The three round-1 required fixes are all correctly implemented and verified GREEN (None-bestiary→typed raise, `MAX_BAND_DEADLINE_S` ceiling, `entry is None` ERROR log; 568 passed, ruff/pyright clean, security CLEAN, new span routed). But the rework only domesticated **one** of the ways an authored room binding can be broken on the crash-free degrade path — the very gap the round-1 HIGH was about reopens through a **sibling exception**. Small, tightly-scoped rework (≈3 lines + a test).

### Observations

1. **[HIGH][EDGE] Uncaught `yaml.YAMLError` / `OSError` from `resolve_room_creatures` still crashes the player-facing connect on degrade.** `_append_authored_creatures` (materializer.py:1054) catches **only** `RoomCreatureBindingError`. But `resolve_room_creatures` reads + parses the room YAML at `room_creature_binding.py:67` (`yaml.safe_load(room_path.read_text(encoding="utf-8"))`) — a **malformed `rooms/<id>.yaml`** raises `yaml.YAMLError`, an unreadable file raises `OSError`/`PermissionError`. Neither is a `RoomCreatureBindingError`, so both propagate through `_append_authored_creatures` → `_degrade_region` → `_stage_curate` (no outer catch) → out of the bootstrap `await materialize()` at connect (`connect.py`), crashing session start. This is the **exact** failure mode the round-1 HIGH rejected ("a single content typo can intermittently brick a world's sessions … only when curate degrades … contradicts the ADR-106 Amendment A degrade contract"), reached through a different exception class. A malformed room YAML is precisely the homebrew-authoring error ADR-140/Jade's path must survive. **Fix:** in `resolve_room_creatures`, wrap the read+parse (line 67) in `try/except (yaml.YAMLError, OSError) as exc: raise RoomCreatureBindingError(...) from exc` — this keeps the typed-error contract so the existing materializer catch covers it, stays LOUD (the catch already logs ERROR + emits `dungeon.curate.authored_bind_failed`), and the degrade proceeds with procedural coal. Add a degrade-path test for a malformed room YAML. **Verified no happy-path regression:** the happy-path caller `monster_manual_inject.py:529` does NOT catch `RoomCreatureBindingError`, so a malformed YAML still fails loud there (typed error instead of `YAMLError`) — no new silent fallback.
   - **[Folded] #2 — the second `pack.effective_bestiary(world_slug)` (materializer.py:1085) is unguarded.** Pure dict-lookup on the real `GenrePack` (cannot raise — VERIFIED below), but `pack: Any`. Address defensively *as part of the same fix* by guarding the `_append_authored_creatures` authored-read block so any read/lookup failure routes to the loud-but-graceful path, not just `RoomCreatureBindingError`.
   - **[Folded] #6 — `lookahead_worker.py:385` passes `pack=self.pack_tropes`.** In production `pack_tropes` IS the full `genre_pack` (round-1 VERIFIED #4, re-confirmed), so `effective_bestiary`/`source_dir` exist; a future trope-only pack would raise `AttributeError` uncaught. Lower risk than #1; the same defensive guard closes it.
2. **[LOW][EDGE] `source_dir` set-but-invalid → silent `[]` (room_creature_binding.py:54/60).** A non-`None` but nonexistent `source_dir` makes `room_path.is_file()` False → returns `[]` (authored binding silently dropped). **Pre-existing** (unchanged by the rework); `source_dir` is operator startup config (fail-loud at load). Non-blocking; noted as a Delivery Finding.
3. **[LOW][EDGE] Ceiling-bite observability gap (materializer.py:1377).** When `MAX_BAND_DEADLINE_S` clamps, effective per-region budget drops below `CURATE_DEADLINE_S` (e.g. 5 regions → 24s/region at defaults), but the degrade reason/span don't surface the *effective* per-region cap. Non-blocking enhancement; not required for re-approval.
4. **[LOW][EDGE] AC5 `_resolve_world_dir` monkeypatch (test).** Redirecting the commit-stage emit to a separate tmp dir from the degrade-read `source_dir` means AC5 does not exercise a commit→curate round-trip — but it never did (the original AC5 wrote commit-emit to *real content* while reading from tmp; the dirs were always disjoint). The isolation fix preserves AC5's span-based intent. Non-blocking; the durable fix (shared tmp content root / conftest fixture) is captured as a Delivery Finding.
5. **[DISMISSED] #4 empty-band spurious degrade span.** Incorrect: with `len(manifests)==0` the `if verdict is None:` branch's `for region_id, manifest in manifests.items()` iterates **zero** times, so **no** `dungeon.curate.degraded` span is emitted. No spurious signal. (Also pre-existing; `max(1, …)` only affects the deadline value.)
6. **[VERIFIED] Round-1 HIGH part A — None-bestiary now typed.** `room_creature_binding.py:76` guards `bestiary is None` and raises `RoomCreatureBindingError` (evidence: line 76-87); `test_resolve_raises_binding_error_not_attribute_error_on_none_bestiary` green. Complies with No-Silent-Fallbacks (typed loud raise).
7. **[VERIFIED] Round-1 HIGH part B — loud-but-graceful catch.** `_append_authored_creatures` catches `RoomCreatureBindingError`, logs ERROR (materializer.py:1056-1066), emits `dungeon.curate.authored_bind_failed` (new span, routed in dungeon_materialize.py, `__all__`-exported, routing-completeness test green), returns creatures unchanged. Degrade proceeds. `test_degrade_with_bad_authored_binding_stays_loud_but_graceful` green.
8. **[VERIFIED] Round-1 MEDIUM — bounded deadline.** `band_deadline_s = min(CURATE_DEADLINE_S * max(1, len(manifests)), MAX_BAND_DEADLINE_S)` (materializer.py:1377; `MAX_BAND_DEADLINE_S=120.0` injectable); `test_band_deadline_is_bounded_by_max_ceiling` green and deterministic (ceiling vs unbounded budget).
9. **[VERIFIED] Round-1 LOW — `entry is None` logs LOUD.** Split out of the name-match `continue`; ERROR log at materializer.py:1095-1101. Name-match `continue` stays silent (correct — "procedural manifest already shipped it").
10. **[VERIFIED][SEC] No security regression.** reviewer-security CLEAN: path components server-minted (no CWE-22), `yaml.safe_load` only (no CWE-502), ERROR-log + span attributes carry only content-pack ids/slugs (no PII/secrets), GM-panel-only routing.
11. **[VERIFIED] Loudness preserved (AC3).** `test_forced_deadline_degrade_stays_loud` green; the new catch adds a span+log, never silences the existing degrade.

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`)
- **#1 Silent exception swallowing** — the confirmed HIGH is the inverse risk: the catch is *too narrow*, letting `yaml.YAMLError`/`OSError` escape into a crash. The fix re-raises them as the typed `RoomCreatureBindingError` (still loud), not a broad swallow. The existing `except RoomCreatureBindingError` is correctly specific (not bare/`except Exception`).
- **#4 Logging** — caught-binding ERROR log + the `entry is None` ERROR log both use lazy `%s` args; severity correct (content/server error → ERROR).
- **#6 Test quality** — new tests non-vacuous (assert span presence, `curated is False`, `uncurated_regions`, creature names); **gap:** no test covers the malformed-YAML degrade path (the HIGH fix must add one). #13 meta-check: the round-1 fix's added `except` was too narrow — exactly the "adding error handling but catching too broadly/narrowly" regression class.
- **#8 Unsafe deserialization** — `yaml.safe_load` (compliant). **#5 Path** — server-minted components, `encoding="utf-8"` present (compliant; resolve() absent but not attacker-reachable). **#9 Async** — timeout scaling async-correct, no blocking calls. **#10 Imports** — new span added to `__all__`; lazy import keeps the cycle broken. **#2/#3/#7/#11/#12** — no relevant surface or compliant.

### Devil's Advocate
Assume this is broken. Jade is extending `perseus_cloud`/`beneath_sunden` homebrew and hand-edits a `rooms/exp001.r2.yaml` to add an encounter, leaving a tab in the indentation or an unclosed quote. Content loads — nothing validates room YAML *syntax* at load (the binding-id validator only runs once the YAML parses). Sessions run for days. Then exp001.r2's curate degrades (more likely now — this story exists *because* curate degrades), `_append_authored_creatures` calls `resolve_room_creatures`, `yaml.safe_load` raises `yaml.YAMLError`, the `except RoomCreatureBindingError` doesn't match, and the exception rides out of the awaited bootstrap `materialize()` — the session never starts, intermittently, with a raw YAML stack trace and no author-friendly signal. That is bit-for-bit the round-1 HIGH ("a single content typo can intermittently brick a world's sessions") with `YAMLError` swapped for `AttributeError`. The round-1 fix taught the degrade to survive a *dangling id* and a *missing bestiary* but not a *malformed file* or a *permissions error* — the file-read failure modes are arguably the **more** common homebrew mistake. Worse, a sysadmin `chmod` slip or an NFS hiccup on the content mount produces an `OSError` with the same fatal result. The blast radius is the player-facing connect, the trigger is non-deterministic, and the person who hits it is exactly the homebrew author the degrade contract exists to protect. The fix is the same shape as the one already applied (re-raise as the typed error so the existing catch lands) and is ≈3 lines plus one test — small, but load-bearing for the "no table freeze, the turn proceeds" guarantee the whole story is about.

### Deviation Audit
See `### Reviewer (audit)` under Design Deviations — round-2 Dev deviation (AC5 isolation) ACCEPTED.

### Required for re-approval
1. **[HIGH]** Make the degrade-path authored read survive **all** content/read failures, not just `RoomCreatureBindingError`: re-raise `yaml.YAMLError`/`OSError` from `resolve_room_creatures` as `RoomCreatureBindingError` (keeps the typed contract; happy path stays loud — verified), and/or broaden the `_append_authored_creatures` guard so the second `effective_bestiary` lookup and a non-bestiary `pack` also route to loud-but-graceful (folds in edge #2/#6). Add a malformed-room-YAML degrade-path test (loud + graceful + degrade proceeds).

### Non-blocking (Delivery Findings — do not gate re-approval)
- Ceiling-bite effective-per-region observability (#3); `source_dir` set-but-invalid silent `[]` (#2); a durable materialize test-isolation fixture for `_resolve_world_dir` (#7/AC5).

## Subagent Results

Round 3 re-review of the round-2 fix (commit `783ac570` — the typed re-raise of `yaml.YAMLError`/`OSError`). Toggles unchanged (preflight, edge_hunter, security on; 6 disabled).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (139 passed inc. 54 happy-path; ruff + pyright clean; 0 smells) | confirmed 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 4 (all LOW/MEDIUM-conf) | confirmed 0 blocking; 2 LOW non-blocking (duck-typed-pack `Path()`/`effective_bestiary` — production-impossible, pre-existing = #2/#6 already adjudicated), 1 LOW non-blocking (happy-path type-change unverified-by-test; no up-stack `except yaml.YAMLError` found), 1 dismissed (#4 lookahead async swallow — incorrect: the error is caught at materializer.py:1065 inside `_append_authored_creatures` and never escapes `materialize`, so it never reaches the async done-callback) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (LOW, CWE-209) | confirmed 1 LOW non-blocking (OSError `str(exc)` embeds the server content path in the ERROR log + GM-panel span — operator-only, not PII/credential; common YAMLError case is path-clean) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned: preflight clean/green, edge-hunter 4 LOW/dismissed, security 1 LOW; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking; 3 confirmed LOW (non-blocking, captured as Delivery Findings); 1 dismissed

## Reviewer Assessment

**VERDICT: APPROVED** — the round-2 blocking HIGH is fully closed and no new blocker is introduced. The fix is minimal and principled: `resolve_room_creatures` now re-raises `yaml.YAMLError`/`OSError` from its room-file read+parse as the typed `RoomCreatureBindingError`, so a malformed or unreadable `rooms/<id>.yaml` on the Layer-2 degrade path is caught by `_append_authored_creatures` (loud — ERROR log + `dungeon.curate.authored_bind_failed` span — but graceful — degrade proceeds with procedural coal), instead of crashing the player-facing bootstrap connect. 139 green (incl. the happy-path caller regression suite), ruff/pyright clean, security one LOW non-blocking.

### Observations
1. **[VERIFIED] Round-2 HIGH closed — malformed/unreadable room YAML degrades loud-but-graceful.** `room_creature_binding.py:67-79` wraps the read+parse in `try/except (yaml.YAMLError, OSError) → raise RoomCreatureBindingError(...) from exc`. The existing `_append_authored_creatures` catch (materializer.py:1065) now covers it — evidence: `test_degrade_with_malformed_room_yaml_stays_loud_but_graceful` drives the real `_stage_curate` degrade and asserts `curated is False`, `uncurated_regions`, the `dungeon.curate.authored_bind_failed` span, an ERROR log, and that procedural coal still ships; `test_resolve_raises_binding_error_not_yaml_error_on_malformed_room_yaml` pins the unit-level typed raise. Both non-vacuous (edge-hunter Q4 confirmed).
2. **[EDGE][VERIFIED] The catch is tight, not over-broad.** `yaml.YAMLError` + `OSError` are exactly the two families the wrapped ops (`read_text` → OSError, `safe_load` → yaml.YAMLError) raise; neither subsumes a programming-error class (`TypeError`/`AttributeError`), so no logic bug is masked. `raise ... from exc` preserves the chain — nothing silently swallowed (edge-hunter Q3, security #3).
3. **[EDGE][VERIFIED] Error caught deep — lookahead async boundary unaffected.** `RoomCreatureBindingError` is caught at materializer.py:1065 inside `_append_authored_creatures`, which returns rather than re-raising (evidence: only two `RoomCreatureBindingError` references in materializer.py, both in the catch block; none in lookahead_worker.py). So it never propagates out of `materialize()` to the lookahead `drain()` done-callback — edge-hunter #4 (async `return_exceptions=True` swallow) is moot. DISMISSED.
4. **[EDGE][LOW][non-blocking] Happy-path type change is loud-to-loud, untested.** `monster_manual_inject.py:529` (the happy-path caller) doesn't wrap `resolve_room_creatures`; a malformed YAML now propagates `RoomCreatureBindingError` instead of `yaml.YAMLError`. Edge-hunter searched for an up-stack `except yaml.YAMLError` that would now miss it and found **none** — so it stays loud. No test pins the happy-path propagation under the new type; captured as a non-blocking Delivery Finding.
5. **[EDGE][LOW][non-blocking] Duck-typed-pack edges remain (`Path(source_dir)` TypeError; `pack.effective_bestiary` AttributeError).** Production-impossible — the live `GenrePack` has a `Path` `source_dir` and a pure `effective_bestiary` (re-affirmed; same #2/#6 adjudicated round 2). Pre-existing (not introduced by round-3). Not blocking.
6. **[SEC][LOW][non-blocking] CWE-209 info-leak in the OSError message.** `str(exc)` of an `OSError`/`PermissionError` embeds the full absolute server content path; it lands in the ERROR log + the `dungeon.curate.authored_bind_failed` span `error` attr (→ GM-panel watcher, operator-only — not the player socket). Downgraded to LOW (per the project rule, the leaked datum is a server content path, **not** a password/token/key/PII), not dismissed — captured as a Delivery Finding with the `exc.strerror` fix. The common `yaml.YAMLError` case is path-clean.
7. **[SILENT] No swallowed errors introduced** — the only new `except` re-raises (loud); the degrade-path catch logs ERROR + emits a span (verified round 2). **[TEST]** new tests substantive (per #1). **[DOC]** the new `except` carries an explanatory comment tying it to the 153-26 degrade contract; no stale docs. **[TYPE]** typed `RoomCreatureBindingError` replaces untyped leakage (improvement). **[SIMPLE]** minimal — one `try/except`, no over-engineering. **[RULE]** see Rule Compliance.

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`)
- **#1 Silent exception swallowing** — compliant: the new `except (yaml.YAMLError, OSError)` is specific and re-raises (loud); the degrade-path catch logs + spans. No bare/broad except.
- **#8 Unsafe deserialization** — `yaml.safe_load` unchanged (compliant). **#5 Path** — `encoding="utf-8"` present; components server-minted (no CWE-22). **#4 Logging** — error string reaches an ERROR log (correct level); the CWE-209 nit (#6 above) is the only blemish, LOW. **#6 Test quality** — new tests non-vacuous, assert concrete state. **#13 meta-check** — the round-2 fix's `except` was re-scanned: specific, typed, chained (`from exc`); no new broad-catch regression.

### Devil's Advocate
Assume still broken. After the round-3 fix, what content/IO failure can a homebrew author trigger that still crashes the degrade connect? Walking `resolve_room_creatures` line by line: `getattr(source_dir)` can't raise; `source_dir is None` → typed raise; `Path(source_dir)` → TypeError only if `source_dir` is a non-path type — impossible for the real `GenrePack` (it's a `Path`); `is_file()` → returns False on a missing dir (no raise); `read_text` → OSError now typed; `safe_load` → YAMLError now typed; `effective_bestiary` → AttributeError only on a pack lacking the method — impossible for the real `GenrePack`; `None` bestiary → typed raise; dangling id → typed raise. So **every** authoring/content failure mode a real homebrew pack can produce is now a `RoomCreatureBindingError` the degrade catch absorbs. The only residual raises are the two duck-typed-pack TypeError/AttributeError edges, which require an object that is *not* a `GenrePack` and that *also* carries a valid `source_dir` and a matching room file — a shape no production path constructs. A malicious actor still can't reach the call (server-minted inputs; security CLEAN). The worst remaining real-world consequence is the LOW info-leak: a `chmod` slip on a content file produces a `PermissionError` whose full path lands in the operator-only GM panel — not a player, not a credential. That is a follow-up, not a blocker. The fix holds.

### Deviation Audit
See `### Reviewer (audit)` under Design Deviations — round-3 Dev deviation (scope: re-raise branch, not the production-impossible #2/#6) ACCEPTED.

### Handoff
To SM (Themis the Just) for finish-story. **Do NOT** weaken the degrade contract in follow-ups; the three non-blocking Delivery Findings (happy-path type-change test, CWE-209 OSError message, ceiling effective-per-region observability) are improvements, not regressions.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[Gap / non-blocking] (TEA)** Production wiring obligation for GREEN: AC5 proves `materialize()` *consumes* a `pack` end-to-end, but the **production caller** that invokes `materialize()` (the dungeon expansion/lookahead path in the server handlers) must actually be wired to **pass the real genre pack** — otherwise `pack=None` in production and the bug is "fixed in tests, dead in prod" (the classic half-wired failure CLAUDE.md warns about). Dev: verify the live caller passes the loaded pack, and confirm via a real-path span (`monster_manual.room_bound` should appear in a live beneath_sunden degrade, not just the test). Same for `_stage_curate`'s pack arg if curate is also invoked off the lookahead worker.

### Dev (implementation) — rework round 2

- **Improvement** (non-blocking): Pre-existing test-isolation hazard. Any test that drives the real `materialize()` with a real `genre_slug` + a synthetic `world_slug` causes `materializer.py::_resolve_world_dir` to resolve the **real** content pack and the commit stage to deposit `worlds/<world_slug>/rooms/*.yaml` into it (gitignored, but on disk) — which then breaks sibling `load_genre_pack` tests run in the same pytest session (observed: 153-26 AC5 polluting `caverns_and_claudes/worlds/test_world/`, breaking `test_session_integration.py` ×3 + `test_room_creature_binding_107_2.py`'s real-content test). Worked around in the 153-26 AC5 test (redirect the emit to tmp), but the durable fix belongs in the materializer's test-friendliness or a shared conftest fixture that points `_resolve_world_dir` at a tmp content root for any materialize-driving test. Affects `sidequest/dungeon/materializer.py` (`_resolve_world_dir`) and `tests/dungeon/conftest.py` (could host a fixture). *Found by Dev during rework.*

### Reviewer (code review) — round 2

- **Gap** (blocking): The degrade-path authored read only survives `RoomCreatureBindingError`, not `yaml.YAMLError`/`OSError` from `resolve_room_creatures` (malformed/unreadable `rooms/<id>.yaml`) — so a malformed room YAML still crashes the player-facing connect on degrade. Affects `sidequest/server/dispatch/room_creature_binding.py:67` (re-raise read/parse errors as `RoomCreatureBindingError`) and `sidequest/dungeon/materializer.py::_append_authored_creatures` (the catch then covers them). *Found by Reviewer during code review.* (Drives the REJECT — see Reviewer Assessment #1.)
- **Improvement** (non-blocking): When `MAX_BAND_DEADLINE_S` clamps the band budget, the effective per-region cap (`band_deadline_s / len(manifests)`) silently drops below `CURATE_DEADLINE_S`; the degrade reason/curate span don't surface it. Affects `sidequest/dungeon/materializer.py:1377` (add `effective_per_region_s` to the degrade reason + span attrs). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `resolve_room_creatures` returns `[]` (silently drops an authored binding) when `source_dir` is set-but-invalid (missing dir) rather than failing loud. Affects `sidequest/server/dispatch/room_creature_binding.py:54-60`. Pre-existing; low risk (`source_dir` is startup config). *Found by Reviewer during code review.*

### Dev (implementation) — rework round 3

- No new upstream findings. The round-2 blocking HIGH (yaml/OS uncaught on degrade) is fixed in this branch; the non-blocking Reviewer improvements above (ceiling effective-per-region observability, set-but-invalid `source_dir`) remain open follow-ups, not regressions introduced here.

### Reviewer (code review) — round 3 (APPROVED)

- **Improvement** (non-blocking): CWE-209 info-leak — `str(exc)` of an `OSError`/`PermissionError` in the `RoomCreatureBindingError` message embeds the full absolute server content path, which reaches the ERROR log + the `dungeon.curate.authored_bind_failed` span (GM-panel/operator-only, not the player socket). Affects `sidequest/server/dispatch/room_creature_binding.py:76-79` — use `exc.strerror` for `OSError` (the basename is already in the message) instead of the full `str(exc)`. Low (server content path, not PII/credential). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No test pins the happy-path caller (`monster_manual_inject.py:529`) propagating `RoomCreatureBindingError` (rather than the old `yaml.YAMLError`) on a malformed room YAML. The change is loud-to-loud (no up-stack `except yaml.YAMLError` interceptor found), but a regression test would lock the contract. Affects `tests/server/dispatch/test_room_creature_binding_107_2.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): When `MAX_BAND_DEADLINE_S` clamps the band budget, the effective per-region cap silently drops below `CURATE_DEADLINE_S`; surface `effective_per_region_s` on the degrade reason/curate span. Affects `sidequest/dungeon/materializer.py:1377` (carried forward from round 2). *Found by Reviewer during code review.*

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 test requires per-region isolation, not just a larger cap or pre-curate-alone**
  - Spec source: context-story-153-26.md, AC-1 ("pre-curating ahead of arrival, per-region chunking, and/or an honest (per-region) budget")
  - What the test pins: `test_one_slow_region_degrades_alone_not_the_whole_band` asserts a fast sibling stays curated when one region is slow — i.e. the wall-clock cap is **per-region**. This is satisfied by per-region chunking or an honest per-region budget, but NOT by (a) merely raising `CURATE_DEADLINE_S`, nor (b) "pre-curate ahead of arrival" that keeps a single whole-band cap.
  - Why: the root cause is "deadline scales with band size" (context-story §Root Cause #1). A bigger fixed number or a relocation that preserves the single-cap-per-band shape would re-surface the real-world 30s-vs-25s failure on a larger band. The test deliberately requires the structural fix the context doc's primary levers describe. If Dev chooses a pre-curate approach, the per-region property must still hold (or raise it back to TEA).
  - Status: intentional, ratified by the context-doc AC wording — not a silent narrowing.

### Dev (implementation)
- **AC1 approach: honest per-region budget (cap-scaling), NOT per-region chunking — and the AC1 test was retuned to match**
  - Spec source: context-story-153-26.md AC-1 (lists "per-region chunking, and/or an honest (per-region) budget" as co-equal options) + Keith's explicit 2026-06-21 decision (AskUserQuestion: "Honest per-region budget").
  - What changed vs the RED test: the original RED test (`test_one_slow_region_degrades_alone_not_the_whole_band`) asserted single-region *isolation*, which only chunking delivers. Keith chose the lighter cap-scaling fix (one whole-band call, cap = `CURATE_DEADLINE_S * region_count`), which fixes the observed band-size-timeout bug without changing curate call count or disturbing the existing `_per_region_partial` whole-band test. I replaced that test with `test_band_curate_budget_scales_with_region_count` (asserts a normal-latency N-region band does not mass-degrade under the scaled budget).
  - Why: the lighter fix "extends the pipeline, doesn't replace it" (SOUL), fixes the real 30s-vs-25s playtest failure, and avoids an N× curate-call cost increase on the dungeon hot path. The trade-off accepted: a single pathologically-slow region still degrades the band (not the observed failure mode).
  - This supersedes the TEA deviation above (which assumed the chunking/isolation interpretation).
  - Status: directed by the user; recorded here, retuned test committed in `6979b4c3`.

- **Rework round 2: AC5 test isolation fix beyond the Reviewer's 3 required findings**
  - Spec source: Reviewer Assessment (round 1), "Required for re-approval" — listed exactly 3 fixes (HIGH catch+span+test, MEDIUM ceiling, LOW log). The AC5 isolation fix was NOT requested.
  - Spec text: "1. [HIGH] … 2. [MEDIUM] … 3. [LOW] …" (no test-hermeticity item).
  - Implementation: also added `monkeypatch.setattr(_mat, "_resolve_world_dir", …)` to `test_materialize_degrade_preserves_authored_content_end_to_end` so the commit-stage room-emit writes to tmp, not the real `caverns_and_claudes` content pack.
  - Rationale: required to make the GREEN gate reliably pass — without it the full dungeon suite fails 4 sibling tests via real-content pollution (a pre-existing AC5 defect, not introduced by my src changes, but surfaced when verifying the rework). The fix touches only WHERE an incidental emit lands; AC5 asserts on spans, not emitted YAMLs, so its intent is preserved.
  - Severity: minor
  - Forward impact: minor — captured as a non-blocking Delivery Finding (durable fix belongs in materializer test-friendliness / a shared conftest fixture). No sibling-story assumption changes.

- **Rework round 3: fixed the blocking edge #1 (yaml/OS re-raise) but NOT the folded #2/#6**
  - Spec source: Reviewer Assessment (round 2), "Required for re-approval" #1 — "re-raise yaml.YAMLError/OSError … **and/or** broaden the _append_authored_creatures guard so the second effective_bestiary lookup and a non-bestiary pack also route to loud-but-graceful (folds in edge #2/#6)".
  - Implementation: took the "re-raise in resolve_room_creatures" branch of the "and/or" — wrapped the read+parse (room_creature_binding.py:67) in `try/except (yaml.YAMLError, OSError) → raise RoomCreatureBindingError`. Did NOT add a guard around the second `pack.effective_bestiary` call (#2) or a `hasattr(pack, "effective_bestiary")` no-op (#6).
  - Rationale: the re-raise fully closes the blocking crash path (a malformed/unreadable room YAML now degrades loud-but-graceful — verified). #2/#6 are production-impossible per the Reviewer's own VERIFIED notes (the real `GenrePack.effective_bestiary` is a pure dict lookup that cannot raise; `pack_tropes` IS the full `genre_pack`). Adding a speculative `hasattr` no-op for #6 would be a **silent fallback** (a misconfigured pack silently drops authored bindings — a rule-#1 violation), and a broad `except` around the second lookup would swallow real bugs. The minimal typed-re-raise is the principled fix; the existing `if bestiary else []` guard already defends the second lookup against a None return without masking a raise.
  - Severity: minor
  - Forward impact: none — production paths unaffected; #2/#6 cannot fire with the live `GenrePack`.

### Reviewer (audit)
- **TEA deviation (AC1 chunking/isolation)** → ✓ ACCEPTED as SUPERSEDED (re-affirmed round 2): correctly retired by the Dev honest-budget deviation; no action.
- **Dev deviation (AC1 honest per-region budget, retuned test)** → ✓ ACCEPTED (re-affirmed round 2): user-directed, sound; the round-2 `MAX_BAND_DEADLINE_S` ceiling refines (does not reverse) it.
- **Dev deviation round 2 (AC5 `_resolve_world_dir` test-isolation fix beyond the 3 required findings)** → ✓ ACCEPTED by Reviewer: necessary and correctly scoped. Without it the full dungeon suite pollutes the real content pack and fails 4 sibling `load_genre_pack` tests; the monkeypatch only redirects WHERE an incidental commit-stage emit lands and AC5 asserts on spans (not emitted YAMLs), so the test's intent is preserved. The durable fix (a shared fixture) is logged as a non-blocking Delivery Finding — appropriate.
- **Dev deviation round 3 (fixed blocking edge #1 via the re-raise branch, NOT the production-impossible #2/#6)** → ✓ ACCEPTED by Reviewer (round 3): the correct branch of the Reviewer's "and/or". The re-raise fully closes the malformed/unreadable-YAML crash path; #2/#6 are production-impossible (live `GenrePack.effective_bestiary` is pure, `pack_tropes` IS the full pack), and a speculative `hasattr` no-op would be a silent fallback (rule #1). Minimal and principled — declining the speculative hardening was the right call.