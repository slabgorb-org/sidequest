---
story_id: "153-27"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-27: [DUNGEON-ZONE-ELIGIBILITY-UNKNOWN-REGION] teach zone/cast-eligibility to recognize procedural dungeon region ids (entrance/expNNN.rN) so cast staging stops skipping every generated room

## Story Details
- **ID:** 153-27
- **Jira Key:** (none — personal project, no Jira)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T20:17:09Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T16:51:41Z | 2026-06-22T16:53:51Z | 2m 10s |
| red | 2026-06-22T16:53:51Z | 2026-06-22T20:00:16Z | 3h 6m |
| green | 2026-06-22T20:00:16Z | 2026-06-22T20:10:41Z | 10m 25s |
| review | 2026-06-22T20:10:41Z | 2026-06-22T20:17:09Z | 6m 28s |
| finish | 2026-06-22T20:17:09Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the Seam-2 cast-staging frontier observer (`stage_region_cast`) fires on *every* region transition with no world-applicability gate, so it runs on `navigation_mode: region` / procedural-dungeon worlds it was never designed for. 153-27 recognizes procedural ids at the consumer; a cleaner long-term shape is an applicability gate that skips the observer entirely for procedural-dungeon worlds. Affects `sidequest/game/region_cast_staging.py` (add a world-mode gate at registration or entry). *Found by TEA during test design.*
- **Improvement** (non-blocking): other `cartography.regions.get(region_id)` consumers — `intent_router_pass.py`, `narration_apply.py:3774`, `map_emit.py:430`, `dispatch/entity_sync.py:152` — also treat a procedural id as a cartography miss. They degrade silently (permissive), so no current harm, but the new shared `is_procedural_region_id()` recognizer should be evaluated at those seams to avoid the same class of misclassification recurring. Affects those files. *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): the procedural region-id format lives in two places — the minter `region_graph.generator` (`f"exp{expansion_id:03d}.r{i}"`) and the recognizer regex `_EXPANSION_REGION_RE` — with no test pinning them together, so a future change to the generator's format would silently stale the recognizer and revive the `unknown_region` warning-spam. Affects `sidequest/dungeon/seed_bootstrap.py` + `sidequest/dungeon/region_graph/generator.py` (add a coupling test that derives a sample id from the generator and asserts `is_procedural_region_id` accepts it). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `is_procedural_region_id` is world-agnostic, so the `entrance` literal would suppress a `unknown_region` warning in *any* world (not just procedural-dungeon worlds) on a cartography miss — corroborates TEA's world-applicability-gate finding above. Affects `sidequest/game/region_cast_staging.py`. *Found by Reviewer during code review.*

### Dev (implementation)
- **Gap** (non-blocking): 3 tests fail on `develop` **independent of 153-27** — proven by re-running them with my changes stashed (they fail identically on the base). None touch the recognizer/span/branch: (1) `tests/genre/test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` — beneath_sunden binds a creature in only `entrance.yaml` (`{'entrance': ['gnaw_swarm']}`), so there is 1 distinct room→creature binding where the test wants ≥2 (a content gap; relates to 153-28's cast-authoring and the depth-graduated bestiary not being placed); (2) `tests/agents/test_59_30_witnesses.py::test_witnesses_count_is_nine_and_docstring_not_stale`; (3) `tests/agents/subsystems/test_movement_dispatch.py::test_move_toward_uncommitted_edge_sync_materializes`. Affects those test files / their subsystems (pre-existing develop breakage to triage separately). *Found by Dev during implementation.*

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned the recognition span name `zone_eligibility.procedural_region`**
  - Spec source: context-story-153-27.md, AC-4 + session `## Architect Assessment (design decision)`
  - Spec text: "reuse the existing `zone_eligibility` span family (e.g. a `reason="procedural_region"` on a skip span) … unless a dedicated `*.procedural_region_recognized` reads cleaner — Dev's call, but it MUST fire and carry the region id"
  - Implementation: tests require a concrete constant `SPAN_ZONE_ELIGIBILITY_PROCEDURAL_REGION = "zone_eligibility.procedural_region"` in `spans/zone_eligibility.py`, flat-only-registered like its siblings
  - Rationale: a test must assert one concrete span name; chose the zone_eligibility family per the decision. Dev/Reviewer may rename within the family if they update the test constant.
  - Severity: minor
  - Forward impact: none (single new span; GM-panel/forensics consume it by name)
- **Pinned the recognizer public import at `sidequest.dungeon.is_procedural_region_id`**
  - Spec source: session `## Architect Assessment (design decision)`
  - Spec text: "Add one shared `is_procedural_region_id(region_id)` recognizer co-located with the id minter … the internal home is Dev's choice"
  - Implementation: tests import `from sidequest.dungeon import is_procedural_region_id`; Dev re-exports it from `dungeon/__init__.py`, internal home co-located with the minter
  - Rationale: tests need a stable import surface; `sidequest.dungeon` is already `region_cast_staging`'s dependency (no new coupling). Internal module placement stays unconstrained.
  - Severity: minor
  - Forward impact: none
- **153-27 RED tests are a self-contained story file duplicating ~40 lines of builder scaffolding from `test_region_cast_staging.py`**
  - Spec source: CLAUDE.md "Don't Reinvent — Wire Up What Exists" / lang-review reuse
  - Spec text: "Before building anything new, check if the infrastructure already exists"
  - Implementation: `tests/game/test_153_27_procedural_region_recognition.py` replicates `_pack`/`_region`/`_snapshot`/`otel_capture`/`_restore_frontier_observers` rather than importing the other file's underscore-private helpers or extracting a shared conftest
  - Rationale: deliberate — keeps the story RED set discoverable + attributable (the dominant `test_153_NN_*` convention) and avoids importing module-private helpers across test files or editing the 157-3 file during RED. Reviewer may consolidate into a shared conftest if preferred.
  - Severity: trivial
  - Forward impact: none

### Dev (implementation)
- No deviations from spec. Implemented exactly to the corrected ACs + Architect guidance: `is_procedural_region_id` placed in `seed_bootstrap.py` (next to `ENTRANCE_ID`, internal home per the decision's "Dev's choice") and re-exported from `sidequest.dungeon`; the span constant is exactly TEA's pinned `zone_eligibility.procedural_region` (flat-only); the recognition branch skips quietly + emits the span on a procedural cartography-miss and preserves the `unknown_region` warning otherwise. (The span carries an extra `reason="procedural_region"` attribute beyond the test's `region` assertion — Neo's suggested payload, additive, not a spec deviation.)

### Reviewer (audit)
- TEA deviation "Pinned the recognition span name `zone_eligibility.procedural_region`" → ✓ ACCEPTED by Reviewer: stays within the `zone_eligibility.*` family per the Architect decision; flat-only registration matches its `filtered`/`cast_staged` siblings. Sound.
- TEA deviation "Pinned the recognizer public import at `sidequest.dungeon.is_procedural_region_id`" → ✓ ACCEPTED by Reviewer: re-export verified in `dungeon/__init__.py`; `sidequest.dungeon` is already the consumer's dependency, so no new coupling. Sound.
- TEA deviation "self-contained story file duplicating ~40 lines of builders" → ✓ ACCEPTED by Reviewer: deliberate test-scaffolding duplication for story-file self-containment; matches the `test_153_NN_*` convention; not production duplication. Acceptable; optional conftest consolidation noted but not required.
- Dev "No deviations from spec" → ✓ ACCEPTED by Reviewer: confirmed against the diff — the implementation matches the corrected ACs and Architect guidance exactly; no undocumented divergence found.

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** the Seam-2 cast-staging frontier observer (`stage_region_cast`) fires on *every* region transition with no world-applicability gate, so it runs on `navigation_mode: region` / procedural-dungeon worlds it was never designed for. 153-27 recognizes procedural ids at the consumer; a cleaner long-term shape is an applicability gate that skips the observer entirely for procedural-dungeon worlds. Affects `sidequest/game/region_cast_staging.py`.

### Downstream Effects

- **`sidequest/game`** — 1 finding

## Sm Assessment

**Story:** 153-27 — [DUNGEON-ZONE-ELIGIBILITY-UNKNOWN-REGION]. Playtest follow-up bug (Sprint 2626).

**The defect (one sentence):** The procedural Jaquaysed megadungeon (ADR-106) mints region ids shaped like `entrance` and `expNNN.rN`, but the zone / cast-eligibility predicate only recognizes authored cartography regions — so cast staging finds no matching region and silently skips *every* procedurally-generated room, leaving generated dungeon rooms permanently NPC-less.

**Setup decisions:**
- **Workflow:** tdd (phased) → next agent is TEA for the RED phase. This is a real behavioral bug with a clear regression target, so TDD is correct over trivial.
- **Repo/branch:** sidequest-server only; branch `feat/153-27-dungeon-zone-region-eligibility` off origin/develop (server trunk is `develop`, not main).
- **Jira:** explicitly skipped — Jira integration is not configured locally; the story id is the key.
- **Parallel-clone check:** setup fetched origin/develop and confirmed 153-27 is not already merged elsewhere.
- **Research landed in context doc** (`sprint/context/context-story-153-27.md`): root cause located at `region_cast_staging.py` and `zone_eligibility.py`; technical approach (recognize `entrance` + `expNNN.rN` procedural shapes / short-circuit the cartography lookup) and 4 acceptance criteria recorded.

**Routing note for TEA (The Architect):** Honor the OTEL Observability Principle — this subsystem decision (region recognized → staging eligible) must emit a watcher event so the GM panel can verify cast actually stages into a generated room. The regression test must prove a generated-region room is no longer skipped (not just that the predicate returns true in isolation — wire it end-to-end per the project's wiring-test rule).

**Verdict:** Setup complete and verified — session file, context doc, branch, and in_progress status all confirmed. Ready for RED.

## Architect Assessment (design decision)

**Decision (Neo, 2026-06-22):** 153-27 = **recognize procedural region ids + suppress the
false `unknown_region` warning + emit an OTEL recognition span.** Do **NOT** extend Seam 2
cast-staging to source NPC cast from the dungeon room-content pipeline. The original
context-doc ACs ("authored NPC cast stages into a procedural room") are architecturally
wrong and are superseded by the rewritten ACs in `context-story-153-27.md`.

**Why — two deliberately separate content pipelines (the load-bearing finding):**

| | Pipeline 1 — room content | Pipeline 2 — cartography cast (Seam 2) |
|---|---|---|
| Owns | per-room creatures + location features | authored-cartography **NPC** cast |
| Source | `rooms/<region_id>.yaml` | `cartography.regions[id].entities` (kind=npc) |
| Driver | curate → materializer → `monster_manual.room_bound` (**fixed by 153-26 / #1022**) | `stage_region_cast` frontier observer (#1006, epic-157) |
| Built for | the procedural deep (ADR-106) | multi-region authored worlds (gulliver/oz) |

Evidence the deep has no Seam-2 cast by design:
- `beneath_sunden/cartography.yaml` authors ONLY `ropefoot` + `the_dropmouth` (static
  surface) and states verbatim: *"The deep is GENERATED, not authored here — no dungeon
  region exists below the_dropmouth by design."*
- All 17 `beneath_sunden/rooms/*.yaml` carry **0 `kind: npc`** bindings (28
  `location_feature`, 1 `encounter_creatures: [gnaw_swarm]`). The creatures path is
  Pipeline 1 and already works post-153-26.
- The original finding's "narrator improvises rooms/creatures" harm traced to the curate
  timeout (153-26, fixed) + the movement-crossing miss (#1042, landed) — NOT to Seam 2.

So Seam 2's only real defect: its frontier observer fires on every transition and
misreads a legitimate procedural id as a *misconfigured cartography id*
(`region_cast_staging.py:77-88` → `unknown_region` warning on every generated room).

**Implementation guidance for Dev (Agent Smith):**
- Add one shared `is_procedural_region_id(region_id)` recognizer **co-located with the id
  minter** (`dungeon/seed_bootstrap.py` `ENTRANCE_ID` / `region_graph/generator.py`
  `f"exp{expansion_id:03d}.r{i}"`) so the pattern cannot drift from its producer. Match
  `entrance` literal + `^exp\d{3}\.r\d+$`. **No second copy of the regex** in the consumer.
- `region_cast_staging.stage_region_cast`: on a cartography miss, branch on the recognizer
  — procedural → quiet skip + OTEL recognition span; non-procedural → keep `unknown_region`.
- `zone_eligibility._faction_for_region` already degrades gracefully (returns None →
  permissive) on a miss, so it needs **no** change for correctness; reuse the shared
  recognizer there only if it improves clarity, not as a required deliverable.
- OTEL: reuse the existing `zone_eligibility` span family (e.g. a `reason="procedural_region"`
  on a skip span) rather than minting a brand-new span namespace, unless a dedicated
  `*.procedural_region_recognized` reads cleaner on the GM panel — Dev's call, but it MUST
  fire and carry the region id (lie-detector principle).

**Deferred (out of scope, documented for traceability):** authored NPCs *in* procedural
rooms — if ever wanted — belong in Pipeline 1 (author a cast/`kind: npc` block in
`rooms/<id>.yaml`; surface via curate), never bolted onto Seam 2. A separate
content-driven story + a design-spec amendment to
`2026-06-20-faction-zone-content-eligibility-design.md`.

**Routing:** No new ADR required — this is a scoped correction within ADR-059/epic-157's
existing seam, consistent with the cartography design intent. Handing back to TEA (The
Architect) to write the RED tests against the rewritten ACs.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Real behavioral bug with a clear regression target (the false `unknown_region`
warning on every procedural room). TDD against the corrected ACs.

**Test Files:**
- `sidequest-server/tests/game/test_153_27_procedural_region_recognition.py` — the 153-27 RED set.

**Tests Written:** 9 test functions / 28 cases (2 parametrized: 6 accept + 15 reject predicate cases) covering all 6 ACs.
**Status:** RED — **confirmed** via `uv run pytest -n0` on the file. Manifests as a collection `ImportError` on the intended-missing symbols (`sidequest.dungeon.is_procedural_region_id`, then `SPAN_ZONE_ELIGIBILITY_PROCEDURAL_REGION`); the recognition branch in `stage_region_cast` is the third missing piece. This is the established repo RED pattern (mirrors the 157-3 file's own "symbol not defined yet" RED). Fixtures are copied verbatim from the live, green 157-3 test file, so the RED is on the missing symbols/behavior, not a fixture defect.

### AC → Test map
| AC | Test(s) |
|----|---------|
| AC1 — no `unknown_region` warning on procedural entry | `test_procedural_room_entry_suppresses_unknown_region_warning`, `test_entrance_region_entry_suppresses_unknown_region_warning` |
| AC2 — recognizer accepts minted shapes / rejects the rest | `test_is_procedural_region_id_accepts_generated_ids` (6), `test_is_procedural_region_id_rejects_non_procedural_ids` (15) |
| AC3 — misconfiguration guard preserved (non-procedural unknown still warns) | `test_non_procedural_unknown_region_still_warns` |
| AC4 — recognition span fires + flat-only routing | `test_procedural_room_entry_emits_recognition_span`, `test_procedural_region_span_is_flat_only_registered` |
| AC5 — no Seam-2 regression (authored cast still stages, no false recognition) | `test_authored_cartography_region_still_stages_cast_without_procedural_span` |
| AC6 — wiring through the real frontier dispatch | `test_real_frontier_transition_into_procedural_region_is_recognized` |

### Rule Coverage
| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #11 input validation / ReDoS-robustness on the recognizer | `test_is_procedural_region_id_rejects_non_procedural_ids` (empty, whitespace-only, junk, substring traps `entranceway`/`entrance.r0`, case `EXP001.R0`) | failing (RED) |
| #6 test quality (meaningful assertions) | self-check — every test asserts a specific value/membership; no `assert True`, no truthy-only, no assertion-free calls | pass (self-check) |

**Rules checked:** 2 of 13 lang-review rules are materially applicable to a pure-predicate + branch + span change; the rest (async, deserialization, resource leaks, mutable defaults, path-handling, deps) do not apply to this surface — noted rather than padded.
**Self-check:** 0 vacuous tests found.

**Wiring test:** `test_real_frontier_transition_into_procedural_region_is_recognized` drives the real `frontier_hook.notify_region_transition` → registered-observer path (not the predicate in isolation), satisfying CLAUDE.md "Every Test Suite Needs a Wiring Test" + "No Source-Text Wiring Tests" (behavior + OTEL span, no source grep).

**Handoff:** To Dev (Agent Smith) for GREEN. Implement: (1) `is_procedural_region_id` co-located with the id minter, re-exported from `sidequest.dungeon`; (2) `SPAN_ZONE_ELIGIBILITY_PROCEDURAL_REGION` (flat-only, zone_eligibility family); (3) the recognition branch in `stage_region_cast` — procedural cartography-miss → quiet skip + recognition span (carry `region`), non-procedural miss → keep the `unknown_region` warning. Do NOT stage cast into the deep and do NOT touch the curate/monster_manual pipeline.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/dungeon/seed_bootstrap.py` — added `is_procedural_region_id()` + the `_EXPANSION_REGION_RE` (`^exp\d{3,}\.r\d+$`) recognizer, next to `ENTRANCE_ID`; added to `__all__`.
- `sidequest/dungeon/__init__.py` — re-export `is_procedural_region_id` (public surface `sidequest.dungeon.is_procedural_region_id`).
- `sidequest/telemetry/spans/zone_eligibility.py` — added `SPAN_ZONE_ELIGIBILITY_PROCEDURAL_REGION = "zone_eligibility.procedural_region"`, registered flat-only.
- `sidequest/game/region_cast_staging.py` — on a cartography miss, branch: procedural id → `debug` log + recognition span + return; non-procedural id → existing `unknown_region` warning.

**Tests:** 153-27 set 28/28 GREEN; sibling `test_region_cast_staging.py` 10/10 (no regression); `tests/dungeon` 488/488. Full server suite: 14020 passed, 340 skipped, **3 failed**. The 3 failures are **pre-existing on develop** — proven by re-running them with my changes git-stashed (they fail identically on the base); see Delivery Findings → Dev. None touch the recognizer/span/branch.

**Branch:** `feat/153-27-dungeon-zone-region-eligibility` (commit `ccdff90c`; RED `fdda69d3`). Not yet pushed.

### AC coverage
| AC | Status | Implementation |
|----|--------|----------------|
| AC1 — no `unknown_region` warning on procedural entry | DONE | recognition branch returns before the warning for `entrance`/`expNNN.rN` |
| AC2 — recognizer accepts minted shapes / rejects the rest | DONE | `is_procedural_region_id` = `== ENTRANCE_ID or _EXPANSION_REGION_RE.match`; `\d{3,}` honors `:03d` min-width; empty/junk → False |
| AC3 — misconfiguration guard preserved | DONE | non-procedural cartography-miss still hits the `unknown_region` warning unchanged |
| AC4 — recognition span + flat-only routing | DONE | `SPAN_ZONE_ELIGIBILITY_PROCEDURAL_REGION` fires with `region` (+`reason`); added to `FLAT_ONLY_SPANS` |
| AC5 — no Seam-2 regression | DONE | authored-cartography path untouched; `test_region_cast_staging.py` 10/10 |
| AC6 — wiring through real frontier dispatch | DONE | recognition reached via `frontier_hook.notify_region_transition` → registered observer (wiring test green) |

**Self-review:** wired (the recognizer has a non-test consumer — `stage_region_cast`; the observer is registered at startup); follows project patterns (mirrors the sibling `cast_staged` span + the existing skip/return shape); no debug/leftover code; OTEL emitted per the Observability Principle. lint + format + pyright clean on all 4 changed files.

**Handoff:** To next phase (spec-check / verify).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (38/38 GREEN, ruff+pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-covered below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (self-covered below) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (self-covered below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (ReDoS-safe regex; regex gate sanitizes span attr; ADR-047 N/A; no silent fallback) | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled subagents returned, both clean; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 from subagents; 2 self-found (1 MEDIUM non-blocking, 1 LOW nit); 0 dismissed; 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `to_region` (from `frontier_hook.notify_region_transition`, fed by the engine seam or a narrator WorldStatePatch) → `stage_region_cast` → `cartography.regions.get(to_region)` MISS → `is_procedural_region_id(to_region)` → recognition branch (debug log + `zone_eligibility.procedural_region` span + return). Safe: the recognizer is a pure predicate and the span attribute is constrained to `^exp\d{3,}\.r\d+$` (or the `entrance` literal) before emission — no unsanitized free-text reaches a persisted attribute, and ADR-047's narrator-prompt surface is not on this path. End-to-end reachability proven by the wiring test (`test_real_frontier_transition_into_procedural_region_is_recognized`).

**Pattern observed:** the new branch mirrors the existing skip/return + `Span.open(...)` shape in the same function and the sibling `cast_staged` span registration — idiomatic, no new pattern introduced. `region_cast_staging.py:80-99`.

### Rule Compliance (python.md lang-review checklist, enumerated vs the diff)
| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | recognizer (no try/except); recognition branch (no swallow) | compliant |
| #3 type annotations at boundaries | `is_procedural_region_id(region_id: str) -> bool` (public) annotated | compliant |
| #4 logging level correctness | recognition = `logger.debug` (expected/by-design, not an error); the misconfiguration path keeps `logger.warning` — correct severity split | compliant |
| #6 test quality | RED tests assert specific values (region equality, membership, warning text, span count); no vacuous assertions; real wiring test | compliant |
| #10 import hygiene | explicit imports, no star, no circular (fresh-interpreter import + full suite verified), `__all__` updated in both modules | compliant |
| #11 input validation / ReDoS | `^exp\d{3,}\.r\d+$` fully anchored, single-class repeats, no alternation/backref → linear; empty/None → False guard | compliant |
| #2/#5/#7/#8/#9/#12 | not applicable to this surface (no mutable defaults, paths, resources, deserialization, async, deps) | N/A |

### Observations (≥5)
1. **[VERIFIED]** Branch ordering is correct — the recognition branch runs ONLY on a cartography miss (`region_cast_staging.py:81` `if region is None:`), so a world that *authored* a region literally named `entrance`/`expNNN.rN` would be a cartography HIT and stage normally; no collision. Evidence: the `cartography.regions.get(to_region)` lookup precedes the new branch.
2. **[VERIFIED]** No-regression on the authored path — the Seam-2 staging body is untouched; `test_region_cast_staging.py` 10/10 green; `test_authored_cartography_region_still_stages_cast_without_procedural_span` confirms a real cartography region stages cast AND fires no procedural span.
3. **[PRE]** Preflight GREEN — story 28/28 + sibling 10/10 + dungeon 488/488; ruff + pyright clean on all 4 production files; 0 code smells.
4. **[SEC]** Security clean — regex is ReDoS-safe (anchored, no nested quantifiers); the regex gate constrains `to_region` to digits+literals before it reaches the persisted span attribute; no new silent fallback (the skip emits a span → observable).
5. **[SILENT]** (self-covered — subagent disabled) No swallowed errors introduced; the procedural skip is *observable* via `logger.debug` + the flat-only span, satisfying No Silent Fallbacks — it is a recognized decision, not a silent drop.
6. **[EDGE]** (self-covered — subagent disabled) **[MEDIUM, non-blocking]** Recognizer↔generator format-drift coupling: `_EXPANSION_REGION_RE` is a hand-maintained second copy of the minter's `f"exp{expansion_id:03d}.r{i}"` format. No test pins the recognizer against an id actually produced by `region_graph.generator` — if the generator's format ever changes, the recognizer (and the literal-based tests) would silently go stale and the warning-spam bug would return. The source-of-truth comment mitigates but does not enforce. Filed as a non-blocking Improvement (add a coupling test). Not a current bug; the region-id format is save-stable/frozen.
7. **[EDGE]** (self-covered) **[LOW, nit]** The regex uses `$`, which in Python matches before a trailing `\n`, so `"exp001.r0\n"` would be recognized as procedural. `\Z` would be strict. Non-blocking: engine-minted ids are clean, and a newline-bearing id would break graph navigation elsewhere long before this matters.
8. **[VERIFIED]** `exp000.r0` matches the regex though expansion-0 is the `entrance` anchor (never minted as `exp000.*`) — harmless: same shape, treated as procedural; no path depends on rejecting it.

### Devil's Advocate
Argue this is broken. **(1) The `entrance` literal is world-agnostic.** `is_procedural_region_id` recognizes the bare string `entrance` regardless of world or `navigation_mode`. A *non*-dungeon world whose narrator names a missing region `entrance` would now have its `unknown_region` warning silently suppressed — the operator loses a misconfiguration signal. Counter: this is the documented TEA finding (the observer has no world-applicability gate); the practical surface is near-zero (what non-dungeon world emits a missing-`entrance` transition?), and it is a follow-up improvement, not a regression introduced here. **(2) Format drift.** The recognizer duplicates the generator's id format as a regex; a future change to `region_graph.generator` would not propagate, silently reviving the original warning-spam (Observation 6). This is the most real long-term risk — but it surfaces *loudly* (the warning returns), is not a silent data-corruption, and the format is frozen for save-stability. Filed non-blocking. **(3) Trailing-newline `$`.** A crafted `"exp001.r0\n"` slips through the regex (Observation 7) — but it breaks navigation elsewhere regardless, so the recognizer is not the weak link. **(4) Untrusted span attribute.** `to_region` originates from LLM-authored patches; but by the time it reaches the span it has passed the anchored regex (digits + literals only), so there is no injection/leak vector — security confirmed this. **(5) Does it even fix the bug?** Yes: the warning was the entire reported symptom; the recognition branch returns before it, and a span now makes the recognition GM-panel-visible. Conclusion: the failure modes are either documented non-blocking follow-ups or contrived edges with louder downstream guards. Nothing rises to Critical/High.

**Error handling:** null/empty `region_id` → `False` (`seed_bootstrap.py` `if not region_id`); non-procedural miss → preserved `unknown_region` warning (`region_cast_staging.py:99`); no exception paths introduced.

**Handoff:** To SM for finish-story. Two non-blocking follow-ups recorded in Delivery Findings (format-drift coupling test; world-applicability gate — the latter already raised by TEA).