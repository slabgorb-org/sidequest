# Story 158-12: Remove the LLM from dungeon curate — deterministic materialization, narrator owns creature prose

## Title

[DUNGEON-CURATE-DETERMINISTIC] Remove the Haiku LLM call from the dungeon materializer's Stage-3 curate pass. Make region materialization pure-deterministic end-to-end (`assemble_region → _creatures_from_manifest → _append_authored_creatures`) and let the live narrator render creature prose at narration time. Retire the Amendment-A retry/deadline/degrade ladder that exists only to survive the LLM call.

## Metadata

- **Story ID:** 158-12
- **Type:** refactor
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 158 — Playtest sweep follow-ups (open findings from the 2026-06-22 full-stack /sq-playtest sweep)
- **Design authority:** ADR-106 **Amendment C** (2026-06-23) — `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md`. Written, currently **uncommitted** on this orchestrator clone. The amendment is the locked contract; this story implements it. The ADR commit lands on orchestrator `main`; the code lands on `sidequest-server` → `develop`.

## Problem Statement

The dungeon materializer's Stage-3 curate pass (`sidequest/dungeon/materializer.py::_stage_curate`, `:1200`) issues **one LLM call per expansion** to `claude_client.complete_with_tools(...)` (`:1386`) — model `CallType.SCRATCH` = `claude-haiku-4-5-20251001` (`agents/model_routing.py:62`), `max_tokens=16384`, covering the whole region band in a single JSON round-trip.

**What that call actually does (and is forbidden from doing).** The prompt (`_build_curation_prompt`, `:921`) asks Haiku for exactly two **cosmetic** things and bars it from touching anything mechanical:
- *PASS 1 (content):* drop wandering-table rows that "read as noise" (a taste filter).
- *PASS 2 (creatures):* rewrite each kept row's telegraph to "one grave, specific sentence."
- **"Preserve every kept row's name/cr/xp/type verbatim … it does not invent stats."**

Every load-bearing mechanic — which creatures, CR→HP (`_hp_from_cr` = CR×8), threat band, `big_bad`, loot, specials, room prose — is produced **deterministically** by `assemble_region` (`game/cookbook/assemble.py:279`, a pure seeded function) *before* curate runs.

**Why it is wrong — three findings:**

1. **Mis-shaped task.** To perform two cosmetic edits, the contract forces the model to **re-emit the entire manifest as strict JSON**, copying `name/cr/xp/type/weight/count` verbatim for every row of every region. Output is dominated by structural echo — the worst possible job to hand a small model under a token cap.

2. **Named, structural flakiness.** That echo under a token/wall-clock cap makes mid-JSON truncation a *routine, named* failure: `_classify_parse_failure` (`:984`) has a dedicated `truncated` kind keyed on `"Unterminated string"`. Large bands blow the cap (the recorded `30337ms-vs-25000ms` failure on `exp001.r2..r5`), both attempts fail, the region degrades. A region therefore materializes its **curated** roster or its **raw** roster *non-deterministically* depending on whether Haiku finished in time. **This is the flakiness: the engine intermittently does or doesn't apply a cosmetic pass, unpredictably — and it is a per-turn, latency-bound LLM call on the dungeon-generation hot path.**

3. **Batching buys nothing.** The prompt curates each region **independently** against its own look/CR band — there is no cross-region coherence instruction. The single all-regions call carries all of the truncation cost and none of the only benefit (holistic dungeon context) that could justify an LLM here.

**The deterministic path already exists and is proven shippable.** Amendment A's Layer-2 degrade (`_degrade_region`, `:1153`) already ships exactly `_creatures_from_manifest(manifest, bundle) + _append_authored_creatures(...)` with no LLM, and ADR-106 clause 9 certifies the `assemble_region` manifest as "valid, complete, and seed-reproducible."

**The narrator already does the prose job.** Seated creatures flow `region_population` mutation → `RegionCreature` (`server/dispatch/region_population.py`) → Monster-Manual `inject` → `snapshot.npcs` → the live narrator, which renders them as world truth with the full genre/world prompt. The Haiku telegraph rewrite was a strictly-worse pre-bake of the narrator's own job (SOUL: *Crunch in the Genre, Flavor in the World* — prose belongs to the narrator at the moment the creature surfaces).

## Root Cause Direction

An LLM was bolted onto the **critical materialization path** to do cosmetic taste-and-prose work, under a token/wall-clock cap, in a verbatim-JSON-echo shape that makes truncation routine — producing intermittent, non-deterministic region materialization with no coherence upside.

**Fix:** delete the LLM from the curate stage. Promote the already-existing deterministic path (`assemble_region → _creatures_from_manifest → _append_authored_creatures`) to the **only** path. Let the narrator render creature prose at narration time (no new narrator code — it already does). Retire the Amendment-A retry/deadline/degrade ladder, which exists solely to survive the now-removed LLM call.

## Acceptance Criteria

Verify by **OTEL spans and behavior, not source-text grep** (server CLAUDE.md § No Source-Text Wiring Tests).

1. **No LLM in the curate path.** `_stage_curate` no longer accepts a `claude_client`, and no `complete_with_tools` (or Ollama `send_with_session`) call is reachable from `sidequest/dungeon/`. The `build_llm_client(purpose="tool")` construction in `session_integration.py` (`:153`) that exists only to feed curate is removed, along with the `claude_client=` argument threaded through `materialize` and `register_lookahead_worker`.

2. **Deterministic materialization.** Same seed ⇒ identical rosters. A fixture-driven test materializes one expansion band twice from one `campaign_seed` and asserts the committed `region_population` mutations (creatures + `big_bad`, including HP and threat) are byte-identical. The `RegionCuration` docstring note that curation "deliberately breaks byte-reproducibility" (`materializer.py:514`) is reversed in code and comment.

3. **Curate span is always clean.** Driving a real materialize emits one `dungeon.materialize.curate` span per region with `curated=true`, and **zero** `dungeon.curate.parse_failed` / `dungeon.curate.degraded` spans are reachable on any path. (The two failure spans + their `materializer.py` usages are removed; coordinate with any telemetry span-registry count test.)

4. **Authored bindings still survive.** A region with an authored `rooms/<id>.yaml` `encounter_creatures` binding (e.g. `entrance` → `gnaw_swarm`) still surfaces that creature under its authored name via `_append_authored_creatures`. Verified through the real materialize → commit → `region_population` path.

5. **`CurationError` carve-out (i) retained.** A structurally-invalid *assembled* manifest (a wandering row missing `cr`, or an unknown `cr_band`) still raises `CurationError` and fails loud — a real upstream content bug is never degraded into shipped content. (Carve-out (ii), the curated-row-dropped-`cr` case, disappears with the verdict.)

6. **No regression on seating + narration.** Procedural region creatures still seat into `snapshot.npcs` with correct HP/threat and the narrator renders them. The existing wiring test (`notify_region_transition → observer → materialize`, `tests/dungeon/test_materializer_wiring.py`) stays green.

7. **Sync collapse (recommended, in-scope).** `_stage_curate` becomes synchronous (no `await`). The `materialize` coordinator and the lookahead worker collapse to synchronous calls; the ~3 `await materialize(...)` sites (`session_integration.py`, `lookahead_worker.py`, tests) are updated. If Dev finds the ripple larger than scoped, this AC may be split to a fast-follow — but the LLM removal (AC 1–6) ships regardless.

## Technical Approach

**Files (sidequest-server, branch off `develop`):**

1. **`sidequest/dungeon/materializer.py`** (the core change)
   - **Rewrite `_stage_curate` as sync + deterministic.** Keep the existing None-guards and the per-region `assemble_region` assembly loop. Then, per region: `creatures, big_bad = _creatures_from_manifest(manifest, bundle)`; `creatures = _append_authored_creatures(creatures, region_id=node.id, pack=pack, world_slug=request.world_slug)`. Accumulate into `region_creatures` / `region_big_bad`. Set the curate span `curated=true` + region/creature counts. Return `RegionCuration(..., uncurated_regions=set())`.
   - **Delete:** `_build_curation_prompt`, `_parse_curation_verdict`, `_classify_parse_failure`, the inline `_one_attempt` LLM/Ollama body, the `asyncio.timeout` retry block, `_degrade_region` (its body is now the main path), and the constants `CURATE_DEADLINE_S` / `MAX_BAND_DEADLINE_S` / the curate `max_tokens=16384` ceiling.
   - **Keep:** `_creatures_from_manifest`, `_append_authored_creatures`, `_hp_from_cr`, `_threat_from_band`, `_curated_to_payload`, and `CurationError` (carve-out i only).
   - **`materialize`:** drop the `claude_client` parameter, its `None`-guard, and `curation_client`; the `_stage_curate` call no longer passes a client and is not awaited.

2. **`sidequest/dungeon/session_integration.py`** — delete `claude_client = build_llm_client(purpose="tool")` (`:153`) and the `claude_client=` args to `materialize` (`:182`) and `register_lookahead_worker` (`:223`); drop the now-unused import.

3. **`sidequest/dungeon/lookahead_worker.py`** — drop `claude_client` from `register_lookahead_worker`, the worker handle, and the `materialize(..., claude_client=self.claude_client)` call (`:381`).

4. **`sidequest/telemetry/spans/dungeon_materialize.py`** — remove the two now-unreachable curate-failure spans (`dungeon_curate_parse_failed_span` `:435`, `dungeon_curate_degraded_span` `:460`); coordinate with any span-registry count test.

5. **`tests/dungeon/`** — remove the curate-LLM fake (`ToolingLlmClient`-shaped) injection; **add the seed-determinism test** (AC 2); keep the wiring test (AC 6).

**TDD order (TEA → Dev):** RED with (a) the seed-determinism test, (b) an OTEL assertion that `dungeon.materialize.curate` fires `curated=true` and the failure spans never fire, (c) the authored-binding survival test. GREEN by the deletion above. The implemented behavior must match Amendment C exactly — no improvisation past what is written there.

## Scope

**In scope:** Remove the LLM from the curate stage; deterministic `_stage_curate`; `claude_client` cleanup across the dungeon wiring; retire the Amendment-A ladder + its two failure spans; sync collapse (AC 7); the determinism + OTEL + authored-binding tests.

**Out of scope (explicit):**
- **The lookahead-race a/b fix** (block-on-arrival vs. deeper prefetch). This story *enables* it — once materialization is microsecond-scale deterministic compute, both options become cheap — but the a/b re-scope is a separate follow-on story to be written on top of Amendment C.
- **Cookbook affinity-weight re-tuning.** Only pursue if a deterministic wandering table actually reads as noisy in play; the fix then is the data (`build_wandering_table` weights), never a runtime trim. Out of scope here.
- **The Map UI gap** (region graph never drawn) — separate, `sidequest-ui`.
- **Narrator changes.** None required: the narrator already renders seated creatures from `snapshot.npcs`. "Narrator owns the prose" is achieved by *removing* the pre-bake, not by adding narrator code.

## Story Scope Clarification

This is a **deletion-led refactor** that fixes an intermittent correctness defect (non-deterministic region materialization). The "type: refactor" classification reflects the dominant action (removing the LLM + collapsing to the deterministic path); the motivating defect is the playtest-observed flakiness. The win is threefold: (1) the dungeon stops being flaky, (2) materialization becomes seed-reproducible, and (3) the expensive per-expansion Haiku call leaves the hot path — which is the precondition that makes the lookahead-race fix tractable.
