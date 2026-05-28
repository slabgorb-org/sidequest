---
parent: context-epic-59.md
workflow: trivial
---

# Story 59-15: Engagement e2e validation — beneath_sunden + road_warrior (OTEL span proof)

## ⚠️ Staleness Check

**This story DEPENDS on three sibling stories that are all still `backlog` as of 2026-05-28.** Run `pf sprint story show 59-11 / 59-12 / 59-14` and re-confirm before starting — this validation cannot fully pass until they land:

| Sibling | Status (2026-05-28) | What it blocks for 59-15 |
|---------|---------------------|--------------------------|
| **59-11** — retire redundant 2nd `run_dispatch_bank` run | `backlog` | The orchestrator currently fires `run_dispatch_bank` TWICE per turn (canonical pass at `server/intent_router_pass.py:161`, then a crippled directive-collection re-run at `agents/orchestrator.py:2562` with no snapshot/pack/player_name). The 2nd run raises `TypeError` (missing kw-only args) for every stateful subsystem and pollutes the GM-panel Subsystems tab with spurious error rows. PR #448 made it non-fatal, but **a clean Subsystems tab — `dispatch_bank` + `intent_router.subsystem` spans firing exactly ONCE per turn — is 59-11's acceptance signal, and is also what 59-15 must observe to call the run clean.** If 59-11 is not done, expect duplicate/erroring subsystem spans and do NOT score that as a 59-15 pass. |
| **59-12** — movement surface→deep bind / double-dispatch | `backlog` (parked, needs repro) | beneath_sunden movement validation (the `frontier.region_transition` + `movement.resolved` leg) is exactly the surface that 59-12 is repairing. Note 59-12's own description flags that Movement Phase 1/2/3 already landed (commits `fbe28ce`, `407294a`) so the bug **may already be fixed** — confirm whether beneath_sunden movement resolves cleanly today before declaring this leg blocked. |
| **59-14** — load `magic_state` for worlds with caster classes | `backlog` | The magic_working handler (`agents/subsystems/magic_working.py:54`) bails when `snapshot.magic_state is None` ("no magic config loaded"). For a caverns_and_claudes Mage in beneath_sunden, if `magic_state` isn't loaded, casting is a **legitimate no-op** and `magic.working` will not fire — that is 59-14's bug, not a 59-15 failure. The magic leg of beneath_sunden validation is gated on 59-14. |

**The validation work does NOT appear to have been performed yet** — there is no `scenarios/beneath_sunden_*.yaml` or `scenarios/road_warrior_*.yaml`, and no integration test named for this story. Proceed as fresh work, but treat each leg's pass/fail honestly against the sibling-dependency table above: a leg that fails because its blocking sibling hasn't landed is a **deferred** leg, not a 59-15 regression. Per memory `feedback_measure_dont_assert`, run the scenario and read the real spans before claiming any leg green.

## Business Context

Epic 59's entire premise is that mechanical engines must **fire for real before the narrator runs**, never be improvised in prose — and that the only proof is OTEL spans on the GM panel (CLAUDE.md "OTEL Observability Principle"; the GM panel is the lie detector). Stories 59-2 through 59-7 built and wired the IntentRouter spine and per-subsystem handlers; the per-engine handler stories shipped against synthetic fixtures and tea_and_murder/Glenross. 59-8 was the tea_and_murder confrontation playtest.

59-15 is the **cross-pack e2e capstone**: prove the spine engages confrontation, movement, and magic in two structurally different live packs — **beneath_sunden** (a dungeon-crawl world under the `caverns_and_claudes` pack, with caster classes and procedurally-generated deep movement) and **road_warrior** (a vehicular-combat pack, all-non-magical classes). The two packs are chosen precisely because they exercise different corners of the spine: beneath_sunden has caster classes (magic should fire) and a runtime-procedural dungeon (movement is dynamic, ADR-106), while road_warrior has `magic_access: null` on every class (magic should correctly NOT fire — a legitimate non-engagement, not a miss). This guards against the SOUL "Illusionism" failure for Keith-as-player: when a Mage in beneath_sunden casts, the engine must move, and the GM panel must show it moved.

## Technical Guardrails

This is a **trivial-workflow validation story** — a playtest-driver run + span inspection, not TDD code. Do not write engine code. Output is a span-evidence writeup (archive session), optionally a committed `scenarios/*.yaml` per pack to make the run reproducible.

**Packs / worlds under test:**
- **beneath_sunden** — world under `caverns_and_claudes` (`sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/`). genre=`caverns_and_claudes`, world=`beneath_sunden`. Has caster classes (`classes.yaml`) → magic-relevant. The deep is procedurally generated (Sünden Deep engine, ADR-106 partial) — per memory `project_beneath_sunden_unmapped_deep`, movement there is dynamic / improv-on-descent BY DESIGN; an empty authored map is not a bug.
- **road_warrior** — pack `road_warrior`, world `the_circuit` (`genre_packs/road_warrior/worlds/the_circuit/`). All six classes are non-magical (`classes.yaml`: `magic_access: null`); `magic.yaml` models item/folkloric "magic," not caster spellcasting. **Expect magic_working to legitimately NOT dispatch here** — that asymmetry is the point.

**How to run (playtest driver + span capture):**
- `just playtest-scenario <name>` → `scripts/playtest.py --scenario scenarios/<name>.yaml` against a running server (`just up`). Scenario YAML shape: `name`, `genre`, `world`, `character.strategy: auto`, `actions: [ ... short action strings ... ]` (see `scenarios/combat_otel.yaml`). Keep player actions short per memory `feedback_playtest_short_actions` (1-2 sentences), each aimed at the target subsystem.
- **Span capture:** `scripts/playtest.py --span-jsonl /tmp/<pack>.spans.jsonl` dumps every span the run produced (pulled from Jaeger's HTTP query API). Server must be up with OTEL→Jaeger export enabled. This jsonl is the primary evidence artifact. The GM dashboard (`just otel`) is the human-readable cross-check.
- Per memory `reference_testing_runner_database_url` + the full-suite gotcha: a live run needs `SIDEQUEST_GENRE_PACKS` pointing at `sidequest-content/genre_packs` and `SIDEQUEST_DATABASE_URL` set, or packs won't load / saves won't persist.

**Exact OTEL spans (the proof — all names verified in tree):**
- IntentRouter producer: `intent_router.decompose` (`telemetry/spans/intent_router.py:44`), `intent_router.dispatch_bank` (`:71`), `intent_router.subsystem` (`:82`, one per dispatched subsystem, `event_type=subsystem_exercise_summary`), `intent_router.failed` (`:59`, ERROR — must be ABSENT on clean turns).
- Confrontation engaged: `encounter.confrontation_initiated` (`telemetry/spans/encounter.py:65`) — the handler at `agents/subsystems/confrontation.py` routes through `instantiate_encounter_from_trigger`, which emits this. (NOTE: the epic spec's `encounter.created` is aspirational shorthand; the real span is `encounter.confrontation_initiated`.)
- Movement resolved: `movement.resolved` (`telemetry/spans/movement.py`, PER-PC, carries `from_region`/`to_region`/`resolved_via`); on a deep transition also `frontier.region_transition` (`telemetry/spans/dungeon_materialize.py:42`). Fail-loud counterpart `movement.unresolved` (ERROR) must be ABSENT.
- Magic engaged: `magic.working` (`telemetry/spans/magic.py:29`), emitted by `apply_magic_working` which the handler at `agents/subsystems/magic_working.py:58` delegates to.
- Lie-detector (must be ZERO across the whole run): `dispatch_engagement.{subsystem}.mismatch` (`telemetry/spans/dispatch_engagement.py:31-36`; `confrontation`, `magic_working`, `scenario_clue`, `npc_agency`, `distinctive_detail_hint`, `reflect_absence`) — emitted by `agents/dispatch_engagement_watcher.py:run_dispatch_engagement_watcher`, wired at `server/websocket_session_handler.py:867`. A mismatch means the router dispatched a subsystem but the engine did not engage on the post-turn snapshot — the exact failure 59-15 exists to rule out.

**What NOT to do:** no engine edits; no source-text wiring assertions (CLAUDE.md "No Source-Text Wiring Tests" — drive the flow, read the span); no Jira (personal project); don't grade road_warrior on magic firing.

## Scope Boundaries

**In scope:**
- One playtest run per pack (beneath_sunden, road_warrior) with `--span-jsonl` capture.
- Per-pack span-evidence writeup confirming confrontation / movement / magic dispatched + the matching engine span fired (or legitimately did not, with reason), and that `dispatch_engagement.*.mismatch` count is zero.
- Confirm `intent_router.subsystem` + `dispatch_bank` spans fire exactly once per turn (the 59-11 cleanliness signal).
- Optional but recommended: commit `scenarios/beneath_sunden_engagement.yaml` and `scenarios/road_warrior_engagement.yaml` so the validation is reproducible.
- Capture findings + any narrative misses in `sprint/archive/59-15-session.md`.

**Out of scope:**
- Any fix to confrontation/movement/magic engines — those belong to their owning stories (59-11/59-12/59-14 and earlier). If a leg fails, file/route the failure to the owning story; do not patch in 59-15.
- tea_and_murder Glenross (that was 59-8).
- scenario_clue / npc_agency / distinctive_detail / reflect_absence beyond noting their mismatch spans stay zero.
- Latency benchmarking (that was 59-8 AC5).
- Multiplayer fan-out / perception-firewall validation.

## AC Context

Each leg = run the pack scenario, capture spans, assert the named span(s). A leg passes only when the dispatch span AND its engine span both appear, in order, before the narrator turn, with zero mismatch spans.

### Pack A — beneath_sunden (genre=caverns_and_claudes, world=beneath_sunden)

**AC-A1 Confrontation fires:** Player action that starts a fight (e.g. "I block the goblin's path and ready my blade"). Proof span chain: `intent_router.decompose` → `intent_router.dispatch_bank` → `intent_router.subsystem`(subsystem=`confrontation`) → `encounter.confrontation_initiated`. The encounter must exist on the snapshot before the narrator runs. Zero `dispatch_engagement.confrontation.mismatch`.

**AC-A2 Movement fires:** Player action that descends/moves between regions (e.g. "I head down the passage to the east"). Proof: `intent_router.subsystem`(subsystem=`movement`) → `movement.resolved` (carrying `from_region`/`to_region`); on a surface→deep procedural transition also `frontier.region_transition`. Zero `movement.unresolved` (ERROR). **Gated on 59-12** — if a real surface→deep entry bypasses `seed_pc_regions` and `movement.unresolved` fires, that is the 59-12 repro, not a 59-15 pass; record it and route to 59-12.

**AC-A3 Magic fires:** Run with a caster character (Mage/caster class from caverns_and_claudes `classes.yaml`); cast something (e.g. "I cast a light ward on the doorway"). Proof: `intent_router.subsystem`(subsystem=`magic_working`) → `magic.working`. Zero `dispatch_engagement.magic_working.mismatch`. **Gated on 59-14** — if `magic.working` is absent because `snapshot.magic_state is None`, that is 59-14's "Mage casting is a no-op" bug, not a 59-15 failure; record and route to 59-14.

### Pack B — road_warrior (genre=road_warrior, world=the_circuit)

**AC-B1 Confrontation fires:** Vehicular/combat-start action (e.g. "I gun the Interceptor and ram the raider's buggy"). Proof: `intent_router.subsystem`(subsystem=`confrontation`) → `encounter.confrontation_initiated`. Zero `dispatch_engagement.confrontation.mismatch`. (Cross-check `project_opposed_check_wiring_trap`: drive a real combat-start against the live pack, not a synthetic fixture.)

**AC-B2 Movement fires:** Travel/road action (e.g. "I floor it down the wasteland highway toward the refinery"). Proof: `intent_router.subsystem`(subsystem=`movement`) → `movement.resolved`. Zero `movement.unresolved`. road_warrior is not a procedural-dungeon world, so `frontier.region_transition` is not expected — only `movement.resolved` on an authored adjacency.

**AC-B3 Magic correctly does NOT fire (negative leg):** All road_warrior classes are `magic_access: null` (`genre_packs/road_warrior/classes.yaml`). A casting-shaped action should produce **no** `magic_working` dispatch and **no** `magic.working` span — AND critically **no** `dispatch_engagement.magic_working.mismatch` (the router not dispatching is correct intended non-engagement, per epic §"Confidence below threshold = correct non-engagement, NOT a fallback"). This leg proves the spine doesn't hallucinate magic in a magic-less pack.

### Cross-cutting (both packs)

**AC-X1 No lie-detector mismatches:** Across both full runs, total `dispatch_engagement.*.mismatch` span count = 0. Any non-zero count is a real engagement gap — record the offending turn + subsystem and route to the owning engine story.

**AC-X2 Clean Subsystems tab (59-11 signal):** `intent_router.dispatch_bank` and `intent_router.subsystem` spans fire exactly once per turn per dispatched subsystem, with no `TypeError`/error rows from a redundant second `run_dispatch_bank`. If duplicate/erroring subsystem spans appear, 59-11 has not landed — note it and do not score AC-X2 green.

## Assumptions

- The IntentRouter live path (59-2/59-4) and per-subsystem handlers (confrontation/movement/magic) are merged on develop and engage from `server/intent_router_pass.py`.
- Jaeger + OTEL export is running so `--span-jsonl` capture works; otherwise fall back to GM-panel (`just otel`) visual inspection and screenshot the Subsystems tab.
- beneath_sunden loads cleanly under caverns_and_claudes with `SIDEQUEST_GENRE_PACKS` set; road_warrior/the_circuit loads (road_warrior is a live, wired pack).
- Per memory `feedback_playtest_is_dev_cycle`: if a leg surfaces a bomb, the finding routes to the owning engine story — 59-15 reports, it does not fix.
