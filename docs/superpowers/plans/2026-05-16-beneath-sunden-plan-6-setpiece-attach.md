# Beneath Sünden — Plan 6: Set-Piece Attach + Trope/Quest-at-Attach + Complication Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Plan 4's set-piece *templates* live. At attach (during materialization), roll each `SetPiece`'s component slots from the seed, **start** its trope components (resolved against the world's `tropes.yaml` — register into the live trope engine so escalation begins *before* the party reaches the room), **seed** its quest components (resolved against scenario state), and write every started-but-unresolved thread into the **open-complication ledger** with origin region + status. Then wire the resolution side: when players close/finish/fail/kill/seal/flee a thread, flip its ledger status and emit the resolution span. This is spec §6 + §7.1 — the *dramatic* half of the bursty feel and the Tomb-of-Horrors escalation spine. `setpieces.py`'s own module docstring names this plan as the owner: *"Plan 6 rolls set-pieces / starts trope+quest components / writes the ledger."*

**Architecture:** One new module `sidequest/dungeon/setpiece_attach.py` exposing a single deterministic public entry point that **Plan 7's attach stage invokes inside the `dungeon.materialize.attach` span** (Plan 7 owns the span + ordering; Plan 6 owns the thread logic and emits `setpiece.attach`/`trope.start`/`quest.seed`/`ledger.add` as children; `ledger.resolve` is emitted from the gameplay resolution path). Slot rolls are a **pure deterministic function** of `(campaign_seed, expansion_id, region_id, setpiece_id, slot_id)` — Plan 7's commit freezes the result into the save; the save is source of truth and rolls are never recomputed (spec §7). The number of set-pieces/components lit per expansion is bounded by `threads_lit_per_expansion` driven from `burst_magnitude` (spec §7.1 — the dramatic burst paired with Plan 2's structural `connection_burst`). Three bindings are **reconcile-at-execution seams** declared against their contracts, the established Plan 2/3/4 honest-deferral stance: (1) **Plan 5's complication-ledger storage** (in flight, oq-1 — spec §7.1 contract); (2) the **trope engine** (`snap.active_tropes` / `TropeState`, ADR-018, *live* — a real binding, low risk); (3) **scenario/quest seeding** (`ScenarioState`, **ADR-053 `partial`** — a stated dependency risk, handled like Plan 7's ADR-055 note: bind to the real surface, stop-and-report if incomplete, never stub).

## Execution Preamble (read before Task 0)

**This plan executes after Plan 5 (persistence/ledger storage) is merged. It does NOT depend on Plan 7** — Plan 7 depends on *this*. Critical-path position: Plan 5 (in flight, oq-1) → **Plan 6 (this — next executable)** → Plan 7 (keystone, gated on 5+6). Writing it now is an Architect design artifact in parallel with oq-1's Plan 5; it is not a directive to begin coding.

### Cross-workspace ownership

oq-2 authors/pushes/opens PRs; **oq-1 owns Plan 5, git-sync, merge, verify.** This plan's *design* is oq-2/Architect; *execution* is gated on Plan 5 and coordinated with oq-1. Do not begin Task 1 while Plan 5's ledger API is unmerged — designing the ledger writes against a moving target produces rot. The contract bound here is **spec §7.1's ledger description**, not in-flight Plan 5 code; bind to the real Plan 5 API at execution and reconcile (Self-Review).

### Scope boundaries (deliberate — NOT omissions; logged so review does not flag them)

- **No persistence schema authored here.** The complication-ledger *storage* (first-class persisted structure, spec §7) is Plan 5. This plan defines *what is added at attach* and *the resolve transition*; it calls Plan 5's ledger primitive. It does not define save tables.
- **No pipeline orchestration / no async worker / no frontier here.** That is Plan 7. This plan's entry point is *called by* Plan 7's attach stage; it does not run the pipeline.
- **No new trope engine and no new scenario engine.** Trope components register into the **existing** ADR-018 trope engine (`snap.active_tropes`); quest components seed into the **existing** ADR-053 `ScenarioState`. ⚠️ **SUPERSEDED — see "Architect Task-0 Reconciliation (2026-05-16)" below: the quest-component host is Plan 5's `ComplicationThread(kind="quest")`, NOT `ScenarioState`.** Plan 6 does cross-resolution (id → real trope/quest) and wiring, not a reimplementation. Reuse-first (ADR-106 / pragmatic-restraint).
- **Set-pieces ≠ cookbook special rooms.** `DungeonTheme.set_pieces` (Plan 4 templates) is this plan's source library. The manifest's `special_rooms` are *curated content rows* placed by Plan 7's curate/attach — a different axis. Slot options that reference creatures/loot resolve against the manifest's `wandering_table`/`loot_table` (the join point, Task 3). Do not conflate the two; this boundary is stated so review does not flag the absence of special-room handling here.
- **No CR→Edge translation here.** That seam is Plan 7 Task 4 (owned, end-to-end). Plan 6 consumes already-translated creature refs from the manifest.

## §6 / §7.1 / §12 decisions baked in here (tunable — reversible)

| Decision | Default | Knob | Rationale |
|----------|---------|------|-----------|
| Threads lit per expansion | derived from `burst_magnitude` (the dramatic half) | `threads_lit_per_expansion` | Spec §7.1 — paired with Plan 2's `connection_burst`; "how big a spike feels fun" is empirical, playtest-tuned. |
| Slot-roll seed | `(campaign_seed, expansion_id, region_id, setpiece_id, slot_id)` | — | Deterministic-given-inputs; frozen by Plan 7 commit (spec §7). Not a knob — a contract. |
| Trope start | append `TropeState` to `snap.active_tropes`, `status="progressing"` | — | Reuses ADR-018 escalation (`trope_tick.tick_tropes`) so a started trope counts down before room entry (spec §6 `priest_demands_a_sacrifice`). |
| Unresolved-thread persistence | every started trope/quest → one ledger entry (origin region + status) | — | Spec §7.1 — first-class, fully legible, no hidden math. |
| Resolution | ledger entry clears **only** on player resolution (close/finish/fail/kill/seal/flee) | — | Spec §7.1 — threads shrink only on resolution; detection lives in the existing trope/scenario systems, Plan 6 subscribes the ledger to them. |

## File Structure

### sidequest-server

| Path | Action | Responsibility |
|------|--------|----------------|
| `sidequest/dungeon/setpiece_attach.py` | Create | Slot roll + trope-start + quest-seed + ledger-add; `AttachReport.as_dict()` span contract; the public entry point Plan 7 calls |
| `sidequest/dungeon/__init__.py` | Edit | Export the Plan 6 public surface |
| the gameplay resolution path (trope-resolve / scenario-resolve sites) | Edit | Subscribe the ledger: thread resolved → `ledger.resolve` + status flip |
| `tests/dungeon/test_setpiece_attach.py` | Create | Roll determinism, trope-start, quest-seed, ledger-add, burst bounding |
| `tests/dungeon/test_setpiece_attach_wiring.py` | Create | **Mandatory wiring test** — entry point reachable from the real Plan-7-attach call shape; resolve subscription fires from the real trope/scenario resolution path |

### sidequest-content

None. Set-piece templates + theme libraries shipped in Plan 4; `tropes.yaml`/scenario content is existing world content.

## Task 0: Branch setup + dependency gate

- [x] **Hard gate:** confirm Plan 5 (persistence/ledger storage) is **merged**. If not, stop. Record merged-base SHA. → **MERGED. PR #303 `feat/beneath-sunden-persistence`, merged-base SHA `cfd4aa1`.**
- [x] Read the **real merged** Plan 5 ledger API. Every "spec §7.1 contract" seam below binds to it at execution; log divergence in Self-Review (do not silently adapt). → **Done — see reconciliation below.**
- [x] Read the live `tropes.yaml` shape (world content) and the real `ScenarioState` seeding surface. **If the scenario/quest-seeding surface is too partial (ADR-053 `partial`) to seed a quest component, stop and report it** as the stated dependency risk — do not stub a fake seed (No Stubbing / No Silent Fallbacks; `feedback_no_burying_bombs`). → **Probed. Reported below — seam redirected, not stubbed.**
- [x] Branch in `sidequest-server` per `repos.yaml` base. → **`feat/beneath-sunden-plan-6-setpiece-attach` off `develop` (server) + off `main` (orchestrator, for plan/spec docs).**

## Architect Task-0 Reconciliation (2026-05-16)

Task 0's three investigative checkboxes are discharged here against **merged** Plan 5 (`cfd4aa1`), not spec §7.1 prose. Dev: bind to these findings; do not re-derive. Log any further divergence in Self-Review per the plan's honest-deferral discipline.

**Seam (1) — Plan 5 complication-ledger storage → GREEN (one favorable divergence).**
Merged API in `sidequest/dungeon/persistence.py`:
- `ComplicationThread(thread_id, origin_region_id, kind, status, started_at_depth_score, payload)` — `kind ∈ {"trope","quest"}`. This is the dataclass Task 4 binds to. `to_dict`/`from_dict` present.
- `DungeonStore.open_thread(thread: ComplicationThread)` — the ledger-add primitive (Task 4). Raises loudly on duplicate `thread_id` (no silent fallback). **It already wraps `ledger_add_span` internally.**
- `DungeonStore.resolve_thread(thread_id)` — the resolve primitive (Task 5). Wraps `ledger_resolve_span`.
- `DungeonStore.get_thread(thread_id)` — raises `NotFoundError` if absent.
- Span constants `ledger.add` / `ledger.resolve` are **owned by Plan 5** in `sidequest/telemetry/spans/dungeon_persist.py`.

**Divergence to carry into Self-Review:** Plan 6 does **NOT** emit `ledger.add` / `ledger.resolve` itself — Plan 5 owns those spans inside `open_thread()` / `resolve_thread()`. The line-7 architecture statement ("Plan 6 ... emits `ledger.add` as children") is superseded: Plan 6 emits only `setpiece.attach` / `trope.start` / `quest.seed` and **calls** the Plan 5 primitive for the ledger row + its span. This is favorable — less surface for Plan 6 to own, span contract centralized.

**Seam (2) — ADR-018 trope engine → GREEN (as the plan predicted, low-risk).**
`snapshot.active_tropes: list[TropeState]` is live on the session snapshot (`sidequest/game/session.py:587`); `trope_tick.tick_tropes` mutates it in place. Trope-start = append a `TropeState(status="progressing")` to `snapshot.active_tropes` (Task 2/3). No new engine. Binding confirmed real.

**Seam (3) — quest-component host → REDIRECTED (the ADR-053 bomb, defused on paper).**
`ScenarioState` (`sidequest/game/scenario_state.py`) is a **whodunit** model: clue graph, `guilty_npc`, suspect roles, gossip adjacency, "binding surface only, between-turn processing deferred." It has **no surface to seed a dungeon quest thread and never will — that is not its axis.** Plan 6 scope bullet "quest components seed into ADR-053 `ScenarioState`" was written against spec prose *before Plan 5 merged* and is **stale**.

**Architect decision (supersedes scope line 21):** A dungeon quest component is a `ComplicationThread(kind="quest")` written via Plan 5's `open_thread()` and cleared via `resolve_thread()` — **the same primitive as a trope thread, different `kind`**. Plan 5 already shipped the quest-thread host. `ScenarioState` is explicitly **out of Plan 6's path** (different subsystem, ADR-053 murder-mystery axis; conflating it is exactly the line-22 axis error). This is a **seam redirect, not a descope and not a stub**: every quest component still produces a real, persisted, legible ledger thread — it just lands in the ledger where Plan 5 put the `kind="quest"` slot, not in a whodunit clue graph.

**Net:** all three seams resolved. Task 1 is unblocked. Branch `feat/beneath-sunden-plan-6-setpiece-attach` off `develop` in `sidequest-server` (empirical: every merged Sünden server PR #295–#303 used `feat/beneath-sunden-*` → `develop`).

## Task 1: Slot roll — pure deterministic component selection

**TDD intent:** for a `SetPiece`, roll each `ComponentSlot` to exactly one `SlotOption` using a `random.Random` seeded by `(campaign_seed, expansion_id, region_id, setpiece_id, slot_id)` (blake2b-mixed, **not** XOR — pre-empt the Plan 2 `seed ^ 0x5EED` fixed-point gotcha at this layer too). Pure function: identical inputs → identical rolled set-piece. No I/O, no engine mutation.

- [ ] Test: identical inputs → byte-identical rolled result across repeated calls and process restarts (frozen-into-save contract; spec §7).
- [ ] Test: distinct `(region_id|setpiece_id|slot_id)` tuples do not collude (different rolls — no accidental shared sub-stream).
- [ ] Test: a `ComponentSlot` with one option rolls that option; an empty options list was already rejected by Plan 4's validator — assert that guard holds, do not re-validate.

## Task 2: Trope-component start → live trope engine (ADR-018 seam)

**TDD intent:** for each `TropeComponent` on the rolled set-piece, resolve `trope_id` against the world's `tropes.yaml` (loud failure if the id is unknown — a content authoring bug, not a silent skip), and **start** it: append a `TropeState` (`status="progressing"`, origin region recorded, `params` carried) to `snap.active_tropes` so `trope_tick.tick_tropes` escalates it from the next tick — before the party reaches the room (spec §6). Emit `trope.start` per component.

- [ ] Test: a started trope appears in `snap.active_tropes` with `status="progressing"` and origin region; a subsequent `tick_tropes` advances its progress (proves it is *live*, not inert — lie detector).
- [ ] Test: unknown `trope_id` raises loudly (content bug surfaced, not swallowed); the failure path still emits a `trope.start` span carrying the failure.
- [ ] Test: `threads_lit_per_expansion` bounds the count — with burst N, at most N trope+quest components across the expansion are lit; the selection of *which* is deterministic from the seed.

## Task 3: Quest-component seed → ScenarioState (ADR-053 `partial` seam)

**TDD intent:** for each `QuestComponent`, resolve `quest_id` and **seed** it into the existing `ScenarioState` (clue graph / belief seeding per ADR-053). Slot options referencing creatures/loot resolve against the manifest's `wandering_table` / `loot_table` (the set-piece↔cookbook join point — set-pieces consume curated content, they do not author it). Emit `quest.seed` per component.

- [ ] Test: a seeded quest is present in `ScenarioState` and discoverable through the real scenario surface (proves wiring, not just a struct write).
- [ ] Test: a slot option referencing a creature id absent from the manifest's tables raises loudly (curation/authoring mismatch surfaced — No Silent Fallbacks), span records the failure.
- [ ] Test (ADR-053 risk): if the scenario seeding surface cannot accept a quest seed, the test asserts the loud stop-and-report path — **not** a stubbed success.

## Task 4: Ledger add — every started thread persisted (Plan 5 seam)

**TDD intent:** every started trope and seeded quest produces one open-complication-ledger entry: thread id, kind (trope|quest), origin region, status `open`, the `setpiece.attach` linkage. Written via **Plan 5's ledger primitive** (binds at execution to the real merged API; spec §7.1 contract here). Emit `ledger.add` per entry and one `setpiece.attach` per attached set-piece. The accumulation is emergent and fully legible (spec §7.1) — no hidden counters.

- [ ] Test: N started threads → N ledger entries, each with origin region + `open` status; the count equals the trope+quest spans emitted (cross-check, lie detector).
- [ ] Test: ledger add is part of the materialization transaction — if Plan 7's commit aborts, no orphan ledger rows (binds to Plan 5 transaction; assert no partial state).
- [ ] Test: `AttachReport.as_dict()` is a byte-pinned span contract (mirrors `GenerationReport.as_dict()` / `DepthReport.as_dict()` precedent) — key-set locked so Plan 7's `attach` span and the GM panel stay stable.

## Task 5: Resolution wiring — `ledger.resolve` from the real gameplay path

**TDD intent:** threads shrink **only** on player resolution (spec §7.1: close set-piece / finish/fail quest / kill / seal / flee). Resolution *detection* already lives in the trope engine (TropeState terminal status) and scenario state (quest finish/fail). Subscribe the ledger to those existing resolution events: on resolution, flip the ledger entry to `resolved` and emit `ledger.resolve`. Do not invent a new resolution mechanic — wire the existing ones (reuse-first).

- [ ] Test: driving a trope to a terminal status through the **real** trope path flips its ledger entry to `resolved` and emits `ledger.resolve` (origin region carried).
- [ ] Test: an unresolved thread stays `open` across subsequent expansions (accumulation spine — it does not silently age out; spec §7.1 "no arbitrary clock").
- [ ] **MANDATORY WIRING TEST** (`test_setpiece_attach_wiring.py`, CLAUDE.md): (a) the attach entry point is invoked with the real Plan-7 attach call shape; (b) the resolve subscription fires from the **real** trope/scenario resolution path, not a test-only call. If the existing resolution surface cannot host the subscription, stop and report it as the stated Task-5 dependency risk — do not stub.

## Task 6: Full-suite gate + honest-deferral / as-built docs

- [ ] Full server suite green; ruff + pyright clean on `setpiece_attach.py` and both test files.
- [ ] Module docstring states: this is the runtime owner `setpieces.py` deferred to; the three seams (Plan 5 ledger / ADR-018 trope engine / ADR-053 scenario) and their contracts; the `AttachReport.as_dict()` byte-pinned span contract; the deterministic-roll / save-is-truth / resolution-only-shrinks contracts.
- [ ] **Post-Implementation Corrections** appended (code authoritative): record divergence between the spec §7.1 contract written against and the real merged Plan 5 ledger + ADR-053 scenario APIs.
- [ ] Update spec §10 decomposition item 6 status (the live tracker — not ADR-106's body).

## Self-Review

- [ ] No silent fallback: unknown trope/quest id, missing manifest creature ref, scenario-seed-impossible, ledger-write-fail all raise loudly with an OTEL trail.
- [ ] No stub: if Plan 5 unmerged or the ADR-053 surface can't seed, the plan did not run / stopped-and-reported — not faked.
- [ ] Set-pieces vs cookbook special rooms boundary respected (Task 3 join point only).
- [ ] Determinism: slot rolls pure + seed-stable across restarts; Plan 7 commit freezes them; never recomputed.
- [ ] Threads shrink only on player resolution; no arbitrary clock; accumulation observable in ledger + spans.
- [ ] All five Plan-6 spans present (`setpiece.attach`/`trope.start`/`quest.seed`/`ledger.add`/`ledger.resolve`); the first four emit inside Plan 7's `attach` span, `ledger.resolve` from the gameplay path.

## Execution Handoff

Designed by Architect (oq-2) on 2026-05-16, in parallel with oq-1's in-flight Plan 5. **Executes after Plan 5 merge; does not depend on Plan 7** (Plan 7 depends on this). Next executable plan after Plan 5. Coordinated with oq-1 (Plan 5 + git-sync/merge/verify owner). Do not begin Task 1 before the Task 0 gate passes.

## Post-Implementation Corrections (as-built — CODE IS AUTHORITATIVE)

### Task 2 corrections (2026-05-16, implementer: Claude Opus 4.7)

**Decision A — origin_region & params do NOT go on `TropeState`.**
Spec §6 says "origin region recorded, params carried" on the TropeState append. But
`TropeState` has `model_config = {"extra": "ignore"}` — any extra kwargs passed to it
are silently dropped, which is exactly the silent fallback the GM panel exists to catch.
Therefore:
- `start_trope_components` appends a minimal `TropeState(id=<trope_id>, status="progressing", progress=0.0)` only.
- Origin region and `params` are carried in `TropeStartResult.pending` as
  `list[tuple[TropeComponent, str]]` (component, origin_region_id pairs) for Task 4 to
  write into the ledger (`ComplicationThread.origin_region_id` + payload). Task 2 does
  NOT attempt to stash them on `TropeState`.
- Code authority: `sidequest/dungeon/setpiece_attach.py::TropeStartResult` and
  `start_trope_components`.

**Decision B — `threads_lit_per_expansion` is an explicit required parameter, no config module.**
The plan references `threads_lit_per_expansion` derived from `burst_magnitude` (spec §7.1).
There is no `threads_lit_per_expansion` knob in the dungeon subsystem (only Plan 2's
`region_graph/config.py::connection_burst`, a distinct structural axis). Plan 6's File
Structure forbids creating a config module. Therefore:
- `start_trope_components` takes `threads_lit_per_expansion: int` and `threads_already_lit: int`
  as explicit required keyword arguments — no silent default.
- Plan 7's pipeline owns the value (derived from `burst_magnitude`, playtest-tuned, spec §7.1)
  and threads it across set-pieces.
- The budget is shared across trope AND quest components (Task 3 continues the same counter
  via the returned `TropeStartResult.tropes_started` value accumulated into `threads_already_lit`).
- When components exceed remaining budget, the selection is deterministic from the seed via
  the existing `_slot_seed` / blake2b family (no second seed scheme, no XOR).
- Code authority: `sidequest/dungeon/setpiece_attach.py::start_trope_components` signature.

**Atomicity (post-review correctness fix, not a spec divergence).**
`start_trope_components` validates EVERY component's `trope_id` against the pack
(two-pass: validate-all → budget-select → append) BEFORE any
`snapshot.active_tropes.append`. A bad `trope_id` rejects the whole set-piece's
trope-start with zero snapshot mutation — no orphan `TropeState` left in a live
snapshot when the `ValueError` propagates (Task 5 wires this into a live snapshot;
the orphan-on-raise would otherwise surface there). The failure span is still
emitted with `failed=True`. Pinned by
`tests/dungeon/test_setpiece_attach.py::test_unknown_trope_id_is_atomic_no_partial_mutation`.

### Task 3 investigation (2026-05-16, implementer: Claude Sonnet 4.6) — NEEDS_CONTEXT: creature/loot-ref convention undefined

**Seam (3) continuation — ScenarioState supersession confirmed.**
The Architect Task-0 Reconciliation already discharged this: `ScenarioState` is a whodunit
model with no dungeon-quest-seeding surface. A quest component's host is
`ComplicationThread(kind="quest")` via Plan 5's `open_thread()`. This is confirmed by reading
`sidequest/dungeon/persistence.py::ComplicationThread` (thread_id, origin_region_id, kind,
status, started_at_depth_score, payload) and `DungeonStore.open_thread()`. The ScenarioState
path is explicitly not touched — no ScenarioState import, no whodunit surface. Task 3's primary
job (carry quest_id + params + origin_region as a pending ComplicationThread for Task 4) is
fully implementable.

**Decision C — symmetric API + shared budget (implementable).**
`seed_quest_components(*, campaign_seed, expansion_id, region_id, setpiece_id,
components: list[QuestComponent], manifest, threads_lit_per_expansion: int,
threads_already_lit: int) -> QuestSeedResult` and
`QuestSeedResult(quests_seeded: int, pending: list[tuple[QuestComponent, str]])` are well-defined
and symmetric with Task 2's `start_trope_components` / `TropeStartResult`. The manifest is
duck-typed on `.wandering_table` / `.loot_table` (mirror Task 2's `pack_tropes: Any` precedent).
Budget sharing: Task 4 passes `threads_already_lit = trope_result.tropes_started` so quests
consume what remains after tropes. Budget determinism via `_slot_seed` family.

**Decision D — atomicity (implementable).**
All-or-nothing on content bug: validate ALL components before producing any result or emitting
success spans. On first missing ref: open that component's `quest.seed` span, set
`failed=True`, raise loudly — symmetric with Task 2.

**Decision E — creature/loot-ref convention: UNDEFINED in shipped Plan 4 code → STOP.**
Investigation of the real shipped code and templates:

1. `QuestComponent` (`sidequest/dungeon/setpieces.py:95`) has `quest_id: str` and
   `params: dict` (free-form, no schema). No typed creature/loot ref fields.

2. `ComponentSlot.name` is a free string (validated non-blank only). Slot names in shipped
   YAML are `"features"`, `"creatures"`, `"loot"`, `"layout"` — but the `SlotOption.value`
   for these is a FREE narrative string, not a manifest entry key.

3. Shipped `sunless_temple.yaml` set-piece `the_altar_that_waits`:
   - `slots[creatures].options = [{value: waking_acolytes, weight: 2.0},
     {value: the_thing_the_temple_feeds, weight: 1.0}]` — these are NARRATIVE descriptions,
     not manifest creature names
   - `quest_components[0].params = {irreversible: true}` — a game-mechanical flag,
     NOT a creature/loot ref

4. Shipped `bone_crypt.yaml` set-piece `the_false_floor`:
   - `slots[loot].options = [{value: prior_victims_effects, weight: 1.0}]` — narrative
     description, not a manifest loot item name

5. `build_wandering_table()` (`sidequest/game/cookbook/assemble.py:92`) produces rows with
   keys `name`, `cr`, `xp`, `type`, `weight`, `count`, `telegraph`. The `name` values are
   canonical D&D monster names from the corpus (`"Zombie"`, `"Shadow"`, etc.).

6. `build_loot_table()` produces rows with keys `name`, `item_type`, `rarity`. The `name`
   values are canonical item names from the corpus.

7. The `DungeonTheme.creature_table[*].ref` values (`temple_acolyte_shade`, `altar_horror`,
   `bone_drake`, `crypt_warden`) are theme-internal identifiers that appear NEITHER in the
   manifest's `wandering_table` (corpus names) NOR in `QuestComponent.params`.

**Finding:** There is NO convention in shipped Plan 4 code, YAML templates, or any other
source that defines how a `QuestComponent`'s params or a set-piece's slot option values
reference manifest `wandering_table` / `loot_table` entries. The task's "test 2" (missing
creature/loot ref raises loudly) cannot be implemented without inventing a convention — which
is explicitly forbidden (No Silent Fallbacks means the test must bind to a REAL convention,
not an invented one).

**What is blocked:**
- Test 2: a slot option referencing a creature id absent from the manifest raises loudly
- The creature/loot ref cross-resolution logic in `seed_quest_components`

**What is NOT blocked (implementable without this convention):**
- `QuestSeedResult` dataclass (quests_seeded, pending)
- `seed_quest_components` signature + budget sharing + pending production
- `quest.seed` span in `dungeon_setpiece.py`
- Test 1 (pending quest is a real pending ledger thread for Task 4)
- Test 3 reframe (no ScenarioState, no stub — real pending thread)
- Budget cap / deterministic selection test
- No-silent-default test

**Resolution needed from Architect before Task 3 can complete:**
Define the convention by which a set-piece references manifest creature/loot entries.
Options (do NOT select one here — that's the Architect's call):
  A. Define `creatures`/`loot` slot values as corpus `name` references (would require
     changing shipped YAML to use corpus names instead of narrative descriptions).
  B. Define a separate typed field on `QuestComponent` for creature/loot refs (would require
     a Plan 4 schema extension and new YAML convention).
  C. Defer creature/loot ref cross-resolution entirely to Plan 7's materializer
     (making Task 3's "test 2" Plan 7 scope, not Plan 6 scope).
  D. Explicitly exclude creature/loot ref resolution from Task 3 (the `params` dict is
     narration-facing, not manifest-resolution-facing; the manifest join happens in Plan 7).

The implementation can proceed on the non-ref-resolution subtasks immediately once the
Architect confirms the scope reduction (option C/D) or the new convention (option A/B).

### Task 3 as-built (2026-05-16, implementer: Claude Opus 4.7 — Architect decision applied)

**Architect decision (2026-05-16): Option C/D merged — defer the creature/loot manifest-join
to Plan 7.** Rationale (logged spec-reconciliation, same pattern as Task-0/Task-2 — NOT a stub,
NOT a silent fallback):
- The plan's scope line 22 ("the join point, Task 3") was an Architect assumption that Plan 4
  would ship a slot/param→creature/loot-ref convention. The Decision-E investigation above
  proves Plan 4 shipped **no such convention**. The assumption was wrong.
- Option A (YAML changes) is forbidden — Plan 6 authors no content (scope line 47-49).
  Option B (extend Plan 4 schema) is forbidden — Plan 4 schema is shipped/frozen; extending it
  from Plan 6 is scope-violating.
- Plan 7 **owns the manifest, curation/attach, and CR→Edge translation end-to-end** (scope
  line 23: "Plan 6 consumes already-translated creature refs from the manifest"). The
  set-piece↔cookbook content-existence join is therefore Plan 7's by ownership, not Plan 6's.

> **PLAN 7 OWNS** (deferred from reduced Task 3 by Architect decision, flagged loudly — NOT
> silently dropped): creature/loot ref resolution of set-piece quest/slot content against the
> manifest's `wandering_table` / `loot_table`. Plan 6 deferred this because **Plan 4 shipped no
> binding convention** (see Decision-E investigation above). The dropped Task-3 "test 2"
> (missing creature/loot ref raises loudly) and its behavior are **reassigned to Plan 7**, which
> owns the manifest + CR→Edge end-to-end. Plan 7's execution must implement this join and its
> loud-failure path. This is a Plan 7 dependency/TODO.

**(a) ScenarioState supersession — continuation of reconciliation Seam 3 (confirmed in code).**
`seed_quest_components` does NOT import, construct, or mutate `ScenarioState`. A quest component
is carried forward as a pending `ComplicationThread(kind="quest")` for Task 4 to write via
Plan 5's `DungeonStore.open_thread()`. Pinned by
`tests/dungeon/test_setpiece_attach.py::test_quest_seed_does_not_touch_scenario_state` (AST
import + symbol scan — not a docstring substring scan, since the module docstring legitimately
*names* ScenarioState to document the supersession). The genuine lie-detector,
`test_seeded_quest_is_a_real_pending_ledger_thread`, persists the pending entry through the
**real** `DungeonStore.open_thread()` and reads it back via `get_thread()` — proving the
pending shape is end-to-end-consumable by Task 4, not an inert struct write.

**(b) Decision-E finding (verbatim above) — Plan 4 ships no creature/loot-ref convention.**
Recorded in full in the "Task 3 investigation" section above. Unchanged by the Architect
decision; the decision is the *resolution* of that finding (defer to Plan 7), not a refutation.

**(c) Decision C — symmetric API, shared budget, manifest-as-parameter (Plan-7-supplied).**
Implemented as:
```
seed_quest_components(*, campaign_seed: int, expansion_id: int, region_id: str,
    setpiece_id: str, components: list[QuestComponent], manifest: Any,
    threads_lit_per_expansion: int, threads_already_lit: int) -> QuestSeedResult
QuestSeedResult(quests_seeded: int, pending: list[tuple[QuestComponent, str]])
```
Symmetric to `start_trope_components` / `TropeStartResult`. `manifest` is REQUIRED (duck-typed
`Any`, mirroring Task 2's `pack_tropes: Any` precedent) so Plan 7's call shape is ready, but
reduced Task 3 does NOT resolve refs against it (Plan 7 owns that join — see PLAN 7 OWNS
callout). Over-budget selection is deterministic via the shared `_slot_seed` / blake2b family
with a `"quest_order|<idx>"` discriminator (keeps quest selection independent of trope
selection; no second seed scheme, no XOR). **Shared expansion budget:** Task 4's caller passes
`threads_already_lit = trope_result.tropes_started` so quests consume what remains after
tropes. `QuestSeedResult.quests_seeded` accumulates into the running total exactly as
`TropeStartResult.tropes_started` does.

**(d) Decision D — atomicity: structurally symmetric, no trigger by design.**
`start_trope_components` runs a validate-all PASS 1 before mutating because an unknown
`trope_id` is a content bug that must reject the whole set-piece atomically. Reduced Task 3
has **no such trigger** — there is no quest registry to resolve `quest_id` against, and the
manifest-join that could surface a content bug is Plan 7's. So there is intentionally **no
PASS 1 validate-all** here: inventing a check just to mirror the shape would be dead code, and
fabricating a failure mode just to have a failure-path test would be **testing theater (the
inverse of stubbing)**. The structural shape (budget gate → deterministic select → emit span)
is preserved for symmetry/robustness; the absence of a failure path is documented in the
module docstring and the function's `Raises:` section ("Nothing by design"). If Plan 7 ever
pushes ref-resolution back into Plan 6, a PASS 1 validate-all must be reinstated here (same
two-pass discipline as `start_trope_components`).

**`quest.seed` span (informational/success only).** Added to
`sidequest/telemetry/spans/dungeon_setpiece.py` as `SPAN_QUEST_SEED = "quest.seed"` +
`quest_seed_span(...)` ctxmgr + a `SPAN_ROUTES` registration (`component="dungeon"`,
`event_type="state_transition"`, `field="complication_ledger"`, `op="quest_seed"`). Mirrors
`trope_start_span` EXCEPT there is **no `failed` attribute** — reduced Task 3 has no failure
path (see (d)), so a `failed` key would be testing theater. One span per seeded component for
the GM-panel per-quest trail. Routing-completeness lint passes
(`tests/telemetry/test_routing_completeness.py`). `setpiece.attach` remains deferred (Task 4 —
no stub).

**Test inventory (9 new, all green; 17 prior Task 1/2 unchanged & green):**
`test_seeded_quest_is_a_real_pending_ledger_thread` (lie-detector via real `DungeonStore`),
`test_quest_seed_does_not_touch_scenario_state` (AST coupling check — supersession pin),
`test_quest_budget_caps_seeded_and_is_deterministic`,
`test_quest_shared_budget_accumulator_with_tropes` (shared-budget threading),
`test_quest_zero_budget_seeds_nothing`, `test_quest_budget_exhausted_seeds_nothing`,
`test_quest_budget_no_silent_default`,
`test_quest_seed_span_emitted_per_component_and_routed` (span + SPAN_ROUTES),
`test_quest_seed_manifest_parameter_accepted_unchanged` (manifest accepted, refs NOT
resolved — pins the Plan 7 deferral).

**No Task-3-owned failure path — by design.** Reviewers: the absence of a "missing
creature/loot ref raises loudly" test is **intentional and Architect-decided**, not a gap.
That behavior is reassigned to Plan 7 (see PLAN 7 OWNS callout). Manufacturing a fake failure
mode to satisfy a "needs a failure test" heuristic would be testing theater.

**Pre-existing pyright note (not introduced here):** `tests/dungeon/test_setpiece_attach.py`'s
pre-existing `test_identical_inputs_produce_identical_result` (Task 1, byte-identical to base
`ffc2663`) trips 10 `reportArgumentType` errors from its `kwargs = dict(...)` then
`roll_set_piece(**kwargs)` splat pattern (the heterogeneous dict literal loses per-key types).
Confirmed pre-existing by type-checking the base-commit copy of the file. Out of Task 3 scope
(another task's code); not "fixed" here to avoid cross-task scope creep. All Task 3 code
(`setpiece_attach.py`, `dungeon_setpiece.py`, all 9 new test functions) is pyright-clean.

### Task 4 as-built (2026-05-16, implementer: Claude Sonnet 4.6)

**BASE_SHA (before Task 4 commit):** `571060d95569683b0326c64c94e311690e484c96`
**Task 4 server commit SHA:** `c76a482`

**(a) `ledger.add` supersession — Plan 6 does NOT emit `ledger.add`.**
Plan 5's `DungeonStore.open_thread()` ALREADY emits `ledger.add` internally (wraps
`ledger_add_span`). Plan 6's `attach_set_piece` emits ONLY `setpiece.attach` and calls
`open_thread()` (which emits `ledger.add` itself). This supersedes the plan's line-7
architecture "Plan 6 ... emits `ledger.add` as children". The Task 4 test
`test_attach_set_piece_n_threads_produce_n_ledger_entries_lie_detector`'s cross-check
counts `trope.start + quest.seed` spans (emitted by Tasks 2/3) against ledger rows —
NOT `ledger.add` spans — per the Architect Task-0 reconciliation.

**(b) Decision H — collision-safe, frozen-into-save thread_id derivation.**
`thread_id` is derived deterministically via `_thread_id_seed(campaign_seed, expansion_id,
region_id, setpiece_id, kind, component_index)` using blake2b over the pipe-delimited
discriminator string (same family as `_slot_seed`). `component_index` is the component's
stable position in the deterministically-ordered pending list returned by
`start_trope_components` and `seed_quest_components`. The `kind` field (`"trope"` vs
`"quest"`) ensures the two pending lists' component_index=0 entries get distinct thread_ids
even if their payloads are otherwise similar. Thread_id format:
`"thread|{kind}|{campaign_seed}|{expansion_id}|{region_id}|{setpiece_id}|{component_index}|{hex_val}"`.
A genuine re-attach of the same set-piece at the same position produces the same thread_id —
correctly tripping Plan 5's `open_thread` duplicate loud raise (freeze-violation signal).

**(c) `attach_set_piece` signature — the Plan-7 contract (Task 5 must bind to this).**
```python
attach_set_piece(
    *,
    campaign_seed: int,
    expansion_id: int,
    region_id: str,
    setpiece_id: str,
    set_piece: SetPiece,
    trope_components: list[TropeComponent],
    quest_components: list[QuestComponent],
    pack_tropes: Any,
    snapshot: GameSnapshot,
    manifest: Any,
    store: DungeonStore,          # concrete Plan 5 type — NOT Any (Decision J)
    threads_lit_per_expansion: int,
    threads_already_lit: int,
    started_at_depth_score: float,  # REQUIRED, no default (Decision I)
) -> AttachReport
```
Code authority: `sidequest/dungeon/setpiece_attach.py::attach_set_piece`.

**(d) `AttachReport.as_dict()` locked key set (Decision K).**
```python
{"setpiece_id", "region_id", "tropes_started", "quests_seeded", "threads_written"}
```
`threads_written = tropes_started + quests_seeded` (count of `ComplicationThread`s opened).
Byte-pinned by `test_attach_report_as_dict_key_set_locked`. Any addition or removal breaks
Plan 7's `attach` span and the GM panel lie-detector.

**(e) `ComplicationThread.payload` shape (Decision L).**
```python
{"setpiece_id": setpiece_id, "component_index": component_index, "ref_id": <trope_id|quest_id>, "params": component.params}
```
Legible, flat, no hidden math. `component_index` is the stable pending-list position (same
discriminator used for thread_id — cross-referencing is possible). `ref_id` is `trope_id`
for trope threads and `quest_id` for quest threads. Pinned by
`test_attach_set_piece_payload_is_legible`.

**(f) `setpiece.attach` span added to `dungeon_setpiece.py`.**
`SPAN_SETPIECE_ATTACH = "setpiece.attach"` with `SPAN_ROUTES` registration
(`component="dungeon"`, `event_type="state_transition"`, `field="complication_ledger"`,
`op="setpiece_attach"`). Context manager `setpiece_attach_span(...)` carries the locked
`AttachReport.as_dict()` key set as span attributes. Added to `__all__`. Routing-completeness
test (`test_routing_completeness.py`) passes. `ledger.add` and `ledger.resolve` are Plan 5's
(`dungeon_persist.py`) — not added here.

**Test inventory (10 new Task 4 tests, all green; 29 prior Task 1/2/3 unchanged & green):**
- `test_attach_set_piece_n_threads_produce_n_ledger_entries_lie_detector` (checkbox 1: N threads → N rows, cross-check against trope.start+quest.seed spans, one setpiece.attach span)
- `test_attach_set_piece_no_orphan_rows_on_caller_rollback` (checkbox 2: caller-owns-txn, no orphan rows after `conn.rollback()`)
- `test_attach_report_as_dict_key_set_locked` (checkbox 3: locked key set, byte-pinned values)
- `test_attach_report_as_dict_matches_fields` (as_dict keys == dataclass fields, spec §7.1 legibility)
- `test_attach_set_piece_thread_ids_are_deterministic` (frozen-into-save, Decision H)
- `test_attach_set_piece_duplicate_trope_id_produces_distinct_thread_ids` (per-component discriminator, Decision H)
- `test_attach_set_piece_tropes_consume_budget_before_quests` (shared budget, tropes first, Decision C)
- `test_attach_set_piece_payload_is_legible` (Decision L payload shape)
- `test_attach_set_piece_started_at_depth_score_required_no_default` (Decision I, No Silent Fallbacks)
- `test_attach_set_piece_setpiece_attach_span_routed` (SPAN_ROUTES routing-completeness)

**pyright:** 0 errors, 0 warnings on `setpiece_attach.py`, `dungeon_setpiece.py`, `test_setpiece_attach.py`
**ruff:** all checks passed, all files formatted.
**routing completeness:** 2/2 passed (`test_routing_completeness.py`).
**pre-existing test-ordering sensitivity in `test_persistence.py::test_commit_and_ledger_emit_spans`:** passes in isolation; flaky in the large `-k dungeon` run due to OTEL tracer monkeypatching contamination from prior tests. Pre-existing — NOT introduced by Task 4. Confirmed by running the test alone. **RESOLVED in the Task 4 review-fix pass — see "Task 4 review fixes" below.**

### Task 4 review fixes (2026-05-16, implementer: Claude Opus 4.7 — two-stage review follow-up)

**Server review-fix commit SHA:** `3beb9d1` (base for this pass: `c76a482`).

Two-stage review of Task 4: spec compliance PASSED; code quality "No — with fixes" (four items). All applied on the same feature branch, re-verified, committed.

**ITEM 1 — re-attach `PersistError` test added (spec-verification gap, code was already correct).**
Spec verification required both the code path AND a test that calling `attach_set_piece` twice with identical inputs on the same `store` lets Plan 5's `PersistError` propagate (the frozen-into-save freeze-violation signal, spec §7). The code was already correct (no `except PersistError` anywhere) but untested. Added `test_attach_set_piece_re_attach_raises_persist_error`: first attach + `conn.commit()`, then a re-attach asserting `pytest.raises(PersistError)` (specifically `PersistError` from `sidequest.dungeon.persistence`, not generic `Exception`), then `conn.rollback()` and asserts the committed-row count is unchanged — proving the raise lands on the FIRST duplicate `open_thread` (trope `component_index` 0) BEFORE any new rows land, so no partial write occurs and **no validate-all-first pass is needed** (Decision J — caller owns the txn — is sufficient; reviewer-confirmed). Added a `Raises:` docstring line on `attach_set_piece` stating this.

**ITEM 2 — deterministic OTEL test-isolation blocker fixed IN THIS BRANCH (Architect-ordered).**
`tests/dungeon/test_persistence.py::test_commit_and_ledger_emit_spans` failed 100% deterministically in the full filtered suite: it calls `trace.set_tracer_provider(provider)` without resetting OTEL's once-only guard (`_TRACER_PROVIDER_SET_ONCE`), so when an earlier conftest's `init_tracer()` already won that guard the test's `_Capture` exporter never installs → empty `captured` → assertions fail. **Pre-existing and unrelated to Task 4's product code** (neither file is Task 4's), but it WILL block Task 6's "full server suite green" gate and the root cause is certain, so the Architect ordered the one-helper fix here rather than burning a Task 6 cycle discovering it cold. **Test-infra only — it does NOT mask a product bug**: production `init_tracer()` is correct (the single legitimate runtime `set_tracer_provider` caller); the test passes in isolation. Fix: added `tests/dungeon/conftest.py::reset_otel_provider()` (resets `trace._TRACER_PROVIDER` to `None` and clears the `Once._done` guard — mirrors the established private-API helper at `tests/telemetry/test_spans.py:_reset_otel_provider`; **duplicated, not cross-imported** — the underscore-prefixed test-module helper is intentionally module-private and must not be reached across test modules), called immediately before the test's `set_tracer_provider`. Full filtered suite (`uv run pytest tests/ -k "trope or quest or scenario or dungeon" -q`) is now FULLY green: **644 passed, 0 failed** (was 641 passed + 1 fail before this pass; +2 new Task-4 tests + this unblocked test = 644).

**ITEM 3 — `AttachReport.rolled` exposed; `RolledSetPiece` no longer discarded (Architect design decision).**
`attach_set_piece` previously called `roll_set_piece(...)` and discarded the `RolledSetPiece`. That is a real bug, not cosmetic: **spec §7 requires Plan 7 to FREEZE the exact rolled result into the save and NEVER recompute it** — discarding it makes Plan 7 unable to freeze it. Fix (minimal, single-return, span-contract-locked):
- `AttachReport` gains a `rolled: RolledSetPiece` field (`field(default_factory=RolledSetPiece)` — mirrors the `DepthReport`/`GenerationReport` plain-dataclass-with-defaults precedent; `attach_set_piece` ALWAYS supplies the real value so production never relies on the empty default — a data-carrier construction convenience, NOT a silent fallback in any live path).
- `AttachReport.as_dict()` stays **byte-identical and key-locked to the existing 5 scalar keys** (`setpiece_id, region_id, tropes_started, quests_seeded, threads_written`). `rolled` is NOT in `as_dict()`: a nested `RolledSetPiece` is not a flat OTEL span attribute, and including it would pollute the locked `setpiece.attach`/Plan-7-`attach`-span contract and break the GM panel. `as_dict()` remains the frozen span contract, mirroring `DepthReport.as_dict()` precisely.
- **`test_attach_report_as_dict_key_set_locked` passes UNCHANGED** (byte-unchanged — verified via `git diff`; works because `rolled` has a `default_factory` so the test's `AttachReport(...)` construction without `rolled` still succeeds and the locked-5-key assertion is intact).
- `test_attach_report_as_dict_matches_fields` was **rewritten** (renamed `test_attach_report_as_dict_is_the_scalar_fields_minus_rolled`) — its old invariant (`as_dict().keys() == all dataclass fields`) is now wrong *by design*, since `rolled` is deliberately a field NOT in `as_dict()`. The rewrite pins the two-surface design: every SCALAR field IS in `as_dict()`; the one structured field (`rolled`) is NOT, and `"rolled" not in report.as_dict()` is asserted.
- New `test_attach_report_rolled_is_the_deterministic_rolled_set_piece` asserts `report.rolled` equals a direct `roll_set_piece(...)` for the same inputs using Task 1's pinned determinism expectations (`campaign_seed=42, expansion_id=3, region_id="exp003.r7", setpiece_id="false_floor"` over `_MULTI_OPTION_SET_PIECE` → `{layout: corridor, loot: gold_coins}`) and that `"rolled" not in report.as_dict()`.

> **PLAN 7 HANDOFF (ITEM 3 + ITEM 6):** Plan 7's attach stage reads the deterministic roll to freeze into the save off **`AttachReport.rolled`** (the `RolledSetPiece`), NOT off the `setpiece.attach` span (the span is the locked 5-scalar-key flat OTEL contract; `rolled` is intentionally absent from it). Likewise, **`started_at_depth_score` is intentionally NOT in `as_dict()`** (correct by Decision K — locked key set): Plan 7 reads each thread's depth from the persisted **`ComplicationThread.started_at_depth_score` ledger row**, not from the span. The span carries only the 5 scalar summary attributes for the GM panel lie-detector.

**ITEM 4 — factually-wrong comment rewritten (code was correct).**
`setpiece_attach.py`'s quest-loop comment claimed `component_index` is "offset past the trope count". It is not — the quest loop is `enumerate(quest_result.pending)` from 0; trope/quest `thread_id` uniqueness at the same list index comes from the `kind` discriminator (`"trope"` vs `"quest"`) mixed into `_thread_id_seed`'s blake2b input, NOT a numeric offset. Comment rewritten to state the mechanism accurately. No code change (the code was already correct).

**ITEM 5 (empty-body `setpiece_attach_span`) — reviewer adjudicated mechanically-correct; LEFT AS-IS** (all `open_thread` work + any `PersistError` happens before the span opens; the span's sole job is to carry the report attributes for the GM panel). No change.

**ITEM 6 (`started_at_depth_score` not in `as_dict()`) — correct by Decision K; no code change.** Documented in the PLAN 7 HANDOFF callout above (Plan 7 reads depth from the thread rows, not the span).

**Re-verification (review-fix pass, Task 4):**
- `uv run pytest tests/dungeon/test_setpiece_attach.py -v` → **41 passed** (39 prior, with `test_attach_report_as_dict_matches_fields` rewritten to `test_attach_report_as_dict_is_the_scalar_fields_minus_rolled` keeping the count, + 2 new: re-attach PersistError, rolled determinism).
- `uv run pytest tests/ -k "trope or quest or scenario or dungeon" -q` → **644 passed, 3 skipped, 0 failed** (ITEM 2 unblocked `test_commit_and_ledger_emit_spans`).
- `uv run pytest tests/telemetry/test_routing_completeness.py -q` → **2 passed**.
- `uv run ruff check` / `format` clean on all changed files (`setpiece_attach.py`, `test_setpiece_attach.py`, `conftest.py`, the `test_persistence.py` addition). The `test_persistence.py` whole-file `ruff format` would also reformat several **pre-existing** style deviations in functions Task 4 never touched (lines 77/89/264 — multi-line `conn.execute` / `ComplicationThread(...)` calls); these are out of Task-4-review scope and were left untouched to avoid cross-scope Plan-5-test churn. The 9-line Task-4 addition itself is correctly formatted.
- `uv run pyright` → **0 errors, 0 warnings** on `setpiece_attach.py`, `dungeon_setpiece.py`, `test_setpiece_attach.py`, AND `tests/dungeon/conftest.py`.

---

### Task 5 Post-Implementation Corrections (2026-05-16)

Server commit: `cb6ac94` on branch `feat/beneath-sunden-plan-6-setpiece-attach`.

**Seam 1 supersession (ledger.resolve) — continuation, Task 5:**
Plan 5's `DungeonStore.resolve_thread(thread_id)` emits `ledger.resolve` internally (inside `persistence.py:419`). Task 5 calls `store.resolve_thread(thread_id)` from `resolve_complications_for_resolved_tropes`; Plan 5 emits the span. Plan 6 does NOT add a second `ledger.resolve` emit in `setpiece_attach.py`. This is the continuation of the Seam 1 supersession documented under Task 4 — Plan 5 owns both `ledger.add` and `ledger.resolve`; Plan 6 only calls the primitives.

**Decision M — resolution function + wiring:**
`resolve_complications_for_resolved_tropes(*, resolved_trope_ids: list[str], store: DungeonStore) -> None` is the Plan 6 public resolution function, added at the bottom of `sidequest/dungeon/setpiece_attach.py`. It is wired at the REAL Story 45-20 handshake site in `sidequest/server/websocket_session_handler.py`, immediately after the existing `_handshake_resolved_tropes(...)` call (approximately line 2786). The call consumes the resolved-trope diff computed by the 45-20 handshake: a list comprehension over `snapshot.active_tropes` selecting tropes whose `status == "resolved"` and whose baseline status was not already `"resolved"` — the exact diff the handshake site already computes. This is the "reuse-first, subscribe to the existing event" mandate from the plan. The function fetches all open threads once, filters `kind="trope"` threads by `payload["ref_id"]`, and calls `store.resolve_thread(thread_id)` for each match.

**Decision N — STOP-AND-REPORT (store-source seam):**
`_SessionData` has NO `dungeon_store` attribute — confirmed by inspecting `sidequest/server/session_handler.py:427–580`. Plan 7 owns the session→DungeonStore wiring. The handler-site call uses `getattr(sd, "dungeon_store", None)` to reference the Plan 7–designated attribute name without blowing up pre-Plan 7. The guard is NOT a silent no-op: when `dungeon_store` is `None` (pre-Plan 7), the handler emits a `logger.warning("dungeon.ledger_resolve.skipped — sd.dungeon_store is not set...")` visible in the server log and GM panel. Plan 7 adds `dungeon_store: DungeonStore | None = None` to `_SessionData` and populates it at session-construction time to activate the path. The mandatory wiring test (`test_mandatory_wiring_decision_n_handler_site_present_and_seam_declared`) asserts: (a) the function name is in the handler file, (b) the string `"dungeon_store"` is in the handler file, (c) `_SessionData` does NOT yet have `dungeon_store` (the honest-deferral finding), (d) the handler uses `getattr`. This test will need updating when Plan 7 lands.

**Decision O — quest-thread resolution is Plan 7's:**
`resolve_complications_for_resolved_tropes` resolves ONLY `kind="trope"` threads. Quest threads (`kind="quest"`) remain `open` — Plan 6 has no quest-resolution detector (the ScenarioState finish/fail mechanic and the resolve call are Plan 7's). Task 5 Test 2 and the mandatory wiring test both assert the quest thread stays `open` after the trope resolves, proving the accumulation spine works correctly and Decision O is honored.

> **PLAN 7 HANDOFF (TASK 5):** Plan 7 must:
> 1. Add `dungeon_store: DungeonStore | None = None` to `_SessionData` in `session_handler.py`.
> 2. Populate `sd.dungeon_store` at session-construction time (connect / chargen-confirmation path) so the handler-site WARNING disappears and `resolve_complications_for_resolved_tropes` actually fires from the live turn path.
> 3. Own quest-thread resolution: when a quest finishes/fails via the scenario mechanic, call `store.resolve_thread(thread_id)` for the matching `kind="quest"` threads. Plan 6's resolution function ONLY handles tropes.
> 4. Update `test_mandatory_wiring_decision_n_handler_site_present_and_seam_declared` — invert the `"dungeon_store" not in sd_fields` assertion once Plan 7 wires the seam.

**Re-verification (Task 5):**
- `uv run pytest tests/dungeon/test_setpiece_attach.py tests/dungeon/test_setpiece_attach_wiring.py -v` → **47 passed** (43 prior Task-4 + 2 Task-5 tests in `test_setpiece_attach.py` + 4 mandatory wiring tests in `test_setpiece_attach_wiring.py`).
- `uv run pytest tests/ -k "trope or quest or scenario or dungeon" -q` → **650 passed, 3 skipped, 0 failed**.
- `uv run pytest tests/telemetry/test_routing_completeness.py -q` → **2 passed**.
- `uv run ruff check` / `format` clean on all changed files.
- `uv run pyright sidequest/dungeon/setpiece_attach.py` → **0 errors, 0 warnings**. `websocket_session_handler.py` has 23 pre-existing pyright errors (none on the Task-5 additions at lines ~2786–2825); new lines introduce zero errors.
