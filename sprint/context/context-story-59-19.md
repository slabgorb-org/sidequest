---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-19: Dogfight smoke fails to resolve through production path

## ⚠️ Staleness Check — TEST PASSES, STORY IS STALE

**Recommendation: close 59-19 without code work. The cited test is GREEN.**

The story title names an exact failing test as its anchor:
`tests/integration/test_dogfight_playtest_smoke.py::test_three_turn_dogfight_resolves_through_production_path`.
Run on 2026-05-28 against `develop` (env: `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS` set):

```
tests/integration/test_dogfight_playtest_smoke.py::test_three_turn_dogfight_resolves_through_production_path PASSED [100%]
======================== 1 passed, 6 warnings in 0.41s =========================
```

This is the same staleness pattern flagged across Epic 59's backlog (see project memory
`project_epic59_61_stale_premises`): the bug was overtaken by faster-landing sibling work
before it reached the front of the queue. Two commits closed the hole this story describes:

- **`4bb71a20` `fix(59-17): dogfight instantiation via production path (#475)`** — the
  directly-related sibling (DONE, archived at `sprint/archive/59-17-session.md`, epic YAML
  `status: done`). 59-17 fixed the instantiation half: confrontation engagement is now
  router-driven (ADR-113 / 59-4) and the narrator-initiated instantiation block was removed
  from `_apply_narration_result_to_snapshot`, which is what left `snap.encounter == None`.
- **`3016177f` `feat(dogfight): SWN shot resolution layered onto the maneuver cross-product (#478)`**
  — the resolution half the smoke test exercises across three turns.

The smoke fixture itself was rewritten as part of 59-17 to drive the live primitive — see
`tests/fixtures/dogfight_playtest_encounter.py:145-170` ("Story 59-17: instantiate through
the LIVE production primitive… the old `confrontation=DOGFIGHT_TYPE` call no longer seats an
encounter (that was the 59-17 repro)"). With the fixture re-pointed at
`instantiate_encounter_from_trigger` and dispatch driven through
`_apply_narration_result_to_snapshot`, the three-turn smoke resolves cleanly and all
`dogfight.*` OTEL spans fire.

**Before any RED-phase work:** re-run the cited test. If it still passes (it does as of
2026-05-28), reconcile the tracker (mark 59-19 `done`/closed, note "overtaken by 59-17 #475
+ #478") rather than re-running the TDD pipeline on an already-green target. The sections
below describe the intended behavior the test pins, in case the story is reopened to add
*new* coverage rather than fix a regression.

## Business Context

Dogfight is the ADR-077 sealed-letter "Ace of Aces" subsystem, the space_opera mechanical
confrontation that Sebastien and Jade (the playgroup's two mechanics-first players) most
want to see fire with real crunch behind it. The SOUL "Illusionism" failure mode — convincing
narration with zero mechanical backing — is exactly what kills a dogfight: the narrator
describes a kill-shot the engine never resolved. Epic 59's whole thesis is that the engine
must run *before* the narrator, and OTEL spans are the GM-panel lie detector proving it did.

59-19's anchor test is the **wiring/smoke test** for that guarantee on the dogfight path:
it drives three maneuver pairs end-to-end through the production dispatch (instantiation →
commit → resolver → state mutation) and asserts the `dogfight.*` spans fired each turn. Its
sibling 59-17 fixed instantiation; 59-19 was filed to guarantee the *whole* three-turn loop
resolves through production code, not just the first seat. As of 2026-05-28 that guarantee
already holds — the test is green — so the remaining value here is tracker reconciliation,
not a fix.

## Technical Guardrails

**The anchor test and its fixture (read these first):**
- `sidequest-server/tests/integration/test_dogfight_playtest_smoke.py` — the cited test.
  Drives `drive_dogfight_turn` three times: T1 `(straight, straight)`, T2 `(loop,
  kill_rotation)`, T3 `(bank, bank)`. Asserts per-actor-state mutation, single-entry
  `narrator_hints` (T5 replace-not-accumulate), distinct cell names, and the OTEL span
  counts in `_assert_dogfight_otel_spans_fired`.
- `sidequest-server/tests/fixtures/dogfight_playtest_encounter.py` — the reusable scaffold.
  `make_dogfight_playtest_state` (line 61) loads real `space_opera` content and instantiates
  via `instantiate_encounter_from_trigger` (line 157). `drive_dogfight_turn` (line 185) routes
  a `NarrationTurnResult` with red+blue `BeatSelection`s through
  `_apply_narration_result_to_snapshot` and returns the `SealedLetterOutcome`.

**Production path the test exercises (do NOT bypass — the point is to catch wiring breaks):**
- `sidequest/server/dispatch/encounter_lifecycle.py` — `instantiate_encounter_from_trigger`,
  the live instantiation primitive 59-17 re-pointed the fixture at.
- `sidequest/server/narration_apply.py` — `_apply_narration_result_to_snapshot`, the
  dispatch entrypoint; it returns `apply_outcome.sealed_letter`.
- `sidequest/server/dispatch/sealed_letter.py` — `SealedLetterOutcome` + the resolver.
- `sidequest/server/dispatch/confrontation.py` — `find_confrontation_def`.

**OTEL spans the test gates on (the lie detector, per CLAUDE.md OTEL Observability Principle):**
Per `_assert_dogfight_otel_spans_fired`, each resolved turn must emit exactly:
`dogfight.confrontation_started` ×1, `dogfight.maneuver_committed` ×2 (red + blue),
`dogfight.cell_resolved` ×1. Any new work must preserve these names and per-turn counts —
they are how the GM panel proves the engine engaged rather than the narrator improvising.

**Env (project memory `reference_testing_runner_database_url`):** the server suite needs
`SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` and
`SIDEQUEST_GENRE_PACKS` pointed at `sidequest-content/genre_packs`. Without them you get ~33
phantom `MissingDatabaseUrlError` and a content-gated SKIP on this test (it `skipif`s when
`DEFAULT_CONTENT_ROOT` is absent) — that is the env tell, not a regression.

## Scope Boundaries

**In scope (only if the story is reopened for NEW coverage):**
- Strengthening the three-turn smoke assertions on the production dogfight resolution loop.
- Any genuinely-uncovered span/state assertion the existing test misses.

**Out of scope:**
- Re-fixing dogfight instantiation — that was 59-17 (#475), DONE.
- The SWN shot-resolution layer — that was #478, DONE.
- Confrontation engagement routing / `begin_confrontation` retirement — 59-4 (ADR-113), DONE.
- Editing the fixture's instantiation strategy — 59-17 deliberately set it to the live
  primitive; do not revert to the narrator-sidecar `confrontation=DOGFIGHT_TYPE` path.
- Any change that renames or drops the `dogfight.*` span names the smoke test depends on.
- **Net-new code at all if the test still passes** — reconcile the tracker instead.

## AC Context

**AC1 — Three-turn dogfight resolves through the production path:** the cited test drives
three maneuver pairs via `drive_dogfight_turn` (NOT by calling the resolver directly), proving
instantiation → commit → dispatch → resolver → state mutation all run through production code.
After each turn both actors' `per_actor_state` is non-empty (engine moved the world); T2's
mutual gunline sets `gun_solution=True` on both; `narrator_hints` holds exactly one entry that
matches the latest outcome (T5 replace semantics); the three cell names are ≥2 distinct.
**Status 2026-05-28: PASSES.**

**AC2 — Engagement OTEL spans fire each turn:** `_assert_dogfight_otel_spans_fired` confirms
exactly one turn's worth of `dogfight.confrontation_started` (×1),
`dogfight.maneuver_committed` (×2), and `dogfight.cell_resolved` (×1) after each of the three
turns. This is the GM-panel lie-detector assertion — it is what distinguishes a real engine
run from narrator improvisation. **Status 2026-05-28: PASSES.**

Both ACs are satisfied by `develop` as of 2026-05-28. If they still pass at pickup time, the
correct action is closing the story, not a RED/GREEN cycle.

## Assumptions

- 59-17 (#475) and #478 are merged to `develop` and remain merged — both confirmed in
  `git log` and 59-17's `status: done` in `sprint/epic-59.yaml` (archived session present).
- The `space_opera` genre pack is checked out at `sidequest-content/genre_packs/space_opera`;
  otherwise the test SKIPs (not fails) via its content-root `skipif`.
- The Postgres test DB and `SIDEQUEST_GENRE_PACKS` are set per the env note above; the
  PASSED result was produced with both set.
- This is a personal project — no Jira; tracker reconciliation happens in the sprint YAML
  via `pf sprint` commands, not a ticket system.
