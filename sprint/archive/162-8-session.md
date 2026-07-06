---
story_id: "162-8"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 162-8: Dead spawn-path cleanup: resolve_encounter_from_trope (no callers) deleted or wired; generate_name tool ctx.name_generators Phase-E wiring resolved or the stub removed (No Stubbing)

## Story Details
- **ID:** 162-8
- **Jira Key:** (none)
- **Workflow:** tdd
- **Priority:** p3
- **Type:** chore
- **Points:** 1
- **Stack Parent:** none

## Context: NPC Origin Consolidation (Epic 162)

This cleanup story addresses dead code paths identified in the NPC generation inventory. Epic 162 consolidates seven NPC/creature spawn paths into a single, identity-preserving pipeline per the origin-precedence model (Green Room / ADR-TBD).

**Related completed stories:**
- 162-1: Derive-don't-cache Monster Manual
- 162-2: Identity by id, not name (unify Origin types)
- 162-3: Bestiary generics section
- 162-4: Origin-precedence ADR (Green Room)
- 162-5: flickering_reach content reconciliation
- 162-6: space_opera bestiary de-triplication
- 162-7: All-sources-one-scene wiring test + understudy identity-split hunt

## Acceptance Criteria

### Task 1: `resolve_encounter_from_trope` Dead Code Path
**Requirement:** Either delete the function or wire it into the narrator prompt pipeline.

**Investigation:**
- Locate `resolve_encounter_from_trope` in the codebase (likely in `sidequest/game/encounter.py` or `sidequest/game/npc.py`)
- Search for all callers using `grep -r "resolve_encounter_from_trope"` across `sidequest/`
- If zero callers found (expected): apply No Silent Fallbacks principle
  - **Option A (Preferred):** Delete the function and any associated test stubs
  - **Option B:** Wire it as a fallback in the Green Room precedence materializer (ADR-TBD, if there's a legitimate use case in the narrator pipeline)
- If caller(s) found: verify they follow the origin-precedence model; if not, rework caller to use the new Origin/Identity system

**Acceptance Criteria 1a:**
- [ ] Zero orphaned function definitions after resolution
- [ ] If deleted: CHANGELOG or commit message justifies removal (dead code per no-callers sweep)
- [ ] If wired: caller(s) verified in production code paths (not test-only); OTEL span added to track usage
- [ ] Integration test added (or existing test updated) asserting function is reachable or explicitly unreachable

### Task 2: `generate_name` Tool `ctx.name_generators` Phase-E Wiring
**Requirement:** Either complete the Phase-E wiring or remove the stub per the No Stubbing principle.

**Investigation:**
- Locate the `generate_name` tool definition (likely `sidequest/game/tools/generate_name.py` or `sidequest/game/narrator_tools.py`)
- Search for references to `ctx.name_generators` and any Phase-E conditional logic
- Determine whether Phase-E (late narrator pass, post-narration name regeneration) is still in scope:
  - If **Phase-E is active:** wire `ctx.name_generators` to receive the current NPC roster at turn time, add OTEL span tracking, write integration test
  - If **Phase-E is dormant/deferred:** remove the stub field and any dead conditional logic; leave a comment referencing the deferral decision (ADR or DRIFT.md)

**Acceptance Criteria 2a:**
- [ ] No stub fields in tool context (either wired end-to-end or removed entirely)
- [ ] If wired: `ctx.name_generators` populated with current session NPC roster; OTEL span verifies lookup at turn time
- [ ] If removed: clear comment in code explaining deferral rationale (link to ADR or DRIFT.md); test stubs updated to reflect removal
- [ ] No dead conditional branches left behind
- [ ] Ruff/Pyright clean; no unused imports or dead assignments

## Sm Assessment

**Ready for RED.** 1-point cleanup, two disjoint targets in `sidequest-server`, both governed by the No Stubbing / No Silent Fallbacks doctrine.

**Routing rationale:** Story is tagged `tdd` explicitly (not the 1-2pt chore→trivial fallback). Honoring the tag — a delete-or-wire decision needs a test that pins the outcome, not a blind edit. TEA writes the failing test(s) that assert the resolved state; Dev makes green.

**Scope guidance for TEA (Amos):**
- Task 1 (`resolve_encounter_from_trope`): the no-callers sweep is the first move. If zero callers (expected), the test asserts the symbol is gone (import/grep-level reachability assertion) — that's a legitimate RED for a deletion. If wired instead, the test must exercise a production path, not test-only.
- Task 2 (`generate_name` / `ctx.name_generators` Phase-E): decision hinges on whether Phase-E is live or dormant. Test the resolved state — either the wiring fires (OTEL span + roster populated) or the stub is fully excised (no dead conditional).
- Both tasks: prefer deletion when there's no live consumer. Dead code is worse than no code. Don't wire something into existence just to satisfy a test.

**Epic context:** Closing story in the Epic 162 NPC-origin consolidation sweep (162-1 through 162-7 complete). This is debt cleanup, not new capability. No Jira (local sprint story).

**Owner from here:** TEA → Dev → Reviewer. Not mine to solve.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T14:40:55Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T14:00:30.198345Z | 2026-07-06T14:03:43Z | 3m 12s |
| red | 2026-07-06T14:03:43Z | 2026-07-06T14:14:03Z | 10m 20s |
| green | 2026-07-06T14:14:03Z | 2026-07-06T14:30:35Z | 16m 32s |
| review | 2026-07-06T14:30:35Z | 2026-07-06T14:40:55Z | 10m 20s |
| finish | 2026-07-06T14:40:55Z | - | - |

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Not a chore bypass. This is dead-code *removal* — the existing coverage tests the dead code and gets deleted with it, so the *end state* (code absent) has zero coverage without new tests. Server CLAUDE.md requires a reachability/unreachability assertion; the session AC asks for it explicitly.

**Investigation → Decision (both targets: REMOVE):**

Both targets are unwired stubs the live engine routed around. Evidence pinned removal (not wiring) for each:

- **Target 1 — `resolve_encounter_from_trope`** (`server/dispatch/encounter_lifecycle.py:2546`): self-described IOU helper — docstring admits "no Python caller as of this commit ... hook this at the completion site when the trope tick/resolve path lands." That path **has** landed (`game/trope_tick.py`) and deliberately does **not** resolve encounters this way — the resolved-trope handshake is chapter-promotion (`_handshake_resolved_tropes`, Story 45-20). The helper is the sole non-test caller of `Encounter.resolve_from_trope`. The future it waited for arrived and went elsewhere → **delete**.
- **Target 2 — `generate_name` tool + `ToolContext.name_generators`** (`agents/tools/generate_name.py`, `agents/tool_registry.py:132`): the **one** Phase-E `ToolContext` seam never wired at the production call site. `orchestrator.py:4525` wires every sibling seam (`lore_store`, `monster_manual`, `genre_pack`, `weather_state`, …) but never `name_generators` → `ctx.name_generators` is permanently `None` → the tool always returns `[]`. The **live** namer is `narration_apply.py:2007/2035`'s `build_from_culture` route (Story 83-2, actively maintained). The tool is a redundant, permanently-empty parallel path → **remove tool + field**. Wiring it would *add* a second naming path, cutting against Epic 162's consolidation grain (162-6 was de-triplication).

Cross-repo sweep: server-only — no UI/understudy/content/daemon references. `name_generators_wired` lives only in the tool's internal ToolResult (narrator-facing), not the UI.

**Test Files:**
- `tests/server/test_dead_spawn_path_cleanup_162_8.py` — 4 reflection-based absence assertions (module namespace / dataclass fields / registry state — never source-text grep, per the server "No Source-Text Wiring Tests" rule).

**Tests Written:** 4 tests covering both removal targets (AC-1a + AC-2a)
**Status:** RED (all 4 fail cleanly with assertion failures — verified via testing-runner, no import/collection errors; each detects the still-present dead code)

| # | Test | Target |
|---|------|--------|
| 1 | `test_resolve_encounter_from_trope_helper_deleted` | AC-1a: helper gone from dispatch namespace |
| 2 | `test_generate_name_tool_unregistered` | AC-2a: tool de-registered (narrator surface) |
| 3 | `test_generate_name_module_deleted` | AC-2a: adapter module gone (no dead shell) |
| 4 | `test_toolcontext_has_no_name_generators_field` | AC-2a: dangling field excised, not just the tool |

### Rule Coverage

| Rule (lang-review/python.md) | Applies? | Coverage |
|------|------|------|
| #3 Type annotation gaps | Yes | All 4 test signatures `-> None`, no untyped params |
| #6 Test quality | Yes | Every test asserts a specific absence condition with a message — no `assert True`, no truthy-only checks, no skips, no assertion-free calls |
| #1/#2/#4/#5/#7/#8/#9 | N/A | Removal chore — no new exception handling, defaults, logging, paths, resources, deserialization, or async introduced by the tests |

**Rules checked:** 2 of 2 applicable lang-review rules have test coverage (removal chore — the remainder target new behavior, not absence assertions).
**Self-check:** 0 vacuous tests. All four assert real absence with explanatory messages.

**GREEN scope for Dev (what "make it pass" requires):**
- Delete `resolve_encounter_from_trope` (`encounter_lifecycle.py:2546-2584`).
- Delete `tests/server/test_encounter_trope_resolution.py` (whole 58-line file — all 3 tests hit the helper) and remove the 3 duplicate helper tests at `tests/server/test_encounter_lifecycle.py:265-309`. **Keep** `tests/game/test_encounter.py:860-879` — those test the surviving `Encounter.resolve_from_trope` *method*, not the helper.
- Delete `agents/tools/generate_name.py`; remove `generate_name,` from `agents/tools/__init__.py`; remove the `name_generators` field (`tool_registry.py:132`), its Phase-C-Task-24 comment block (123-131), and the now-unused `NameGenerator` TYPE_CHECKING import (`tool_registry.py:37`); delete `tests/agents/tools/test_generate_name.py`.
- Verify `ruff` / `pyright` clean (no orphaned imports) and the full suite is green.

**Handoff:** To Dev for implementation.

## Dev Assessment

**Implementation Complete:** Yes — both targets removed (matched TEA's REMOVE decision; the evidence was decisive, no reason to invert).

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — deleted `resolve_encounter_from_trope` (the no-caller IOU helper) + its now-orphaned `encounter_resolved_span` import (it was the sole user in this file).
- `sidequest/agents/tools/generate_name.py` — **deleted** (redundant, permanently-empty tool).
- `sidequest/agents/tools/__init__.py` — removed the `generate_name` barrel export.
- `sidequest/agents/tool_registry.py` — removed the `ToolContext.name_generators` field, its Phase-C-Task-24 comment block, and the now-unused `NameGenerator` TYPE_CHECKING import.
- `tests/server/test_encounter_trope_resolution.py` — **deleted** (whole file; all 3 tests exercised the deleted helper).
- `tests/server/test_encounter_lifecycle.py` — removed the 3 duplicate helper tests (kept everything else).
- `tests/agents/tools/test_generate_name.py` — **deleted** (24 tests of the removed tool).
- `tests/agents/test_narrator_uses_sdk_client.py` — updated the narrator tool-count assertion `41 → 40` (a count-coupled wiring test that correctly caught the tool removal; documented inline).

**Kept intentionally:** `Encounter.resolve_from_trope` method + `tests/game/test_encounter.py:860-879` — the method survives; only the helper died (per TEA scope + story wording).

**AC verification:**
- AC-1a — helper gone (0 orphaned defs), commit message justifies the dead-code removal, `test_resolve_encounter_from_trope_helper_deleted` asserts it's explicitly unreachable. ✓
- AC-2a — no stub field left (`name_generators` excised), no dead conditional branches (whole tool gone), ruff clean, no unused imports. ✓

**Tests:** Full server suite **14651 passed, 0 failed, 341 skipped** (GREEN). The 4 new absence tests all pass.
**Lint/Type:** `ruff check` clean on all changed files. `pyright` neutral — `encounter_lifecycle.py` carries 14 pre-existing Optional-access errors (verified identical on the base via stash); my change introduced none and touched none of those lines. Fixing them is out of scope for a 1-pt removal.
**Branch:** `feat/162-8-dead-spawn-path-cleanup` (pushed).

**Handoff:** To Reviewer for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | none | N/A (empirically verified RED→GREEN in a worktree) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (17 rules / 27 instances, 0 violations) | N/A |

**All received:** Yes (4 enabled returned clean; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed from subagents, 0 dismissed, 0 deferred. One Low doc-drift item found by the Reviewer directly (below).

## Reviewer Assessment

**Verdict:** APPROVED

A textbook dead-code removal: 713 deletions, 85 insertions (the new absence-test file + one count fix). Two self-documented stubs — one whose own docstring admitted "no Python caller," one whose own deleted test file called itself "an intentional duplicate ... named artifact ... when the trope engine port lands" — plus the one Phase-E `ToolContext` seam that never got wired while all its siblings did. Every enabled subagent returned clean, my own independent sweep confirms the removal is complete, and the tests empirically flip RED→GREEN. No Critical/High. One Low doc-drift item, non-blocking.

**Data flow traced:** player action → narrator turn → `orchestrator.py:4525` builds `ToolContext` and advertises `default_registry.list_names()` as the SDK `allowed_tools` → `generate_name` no longer in the registry → the narrator is never offered it. Safe because the tool surface is *derived from the registry*, not a hardcoded list (verified: no `generate_name` literal in `orchestrator.py`/`anthropic_sdk_client.py`). The deleted `resolve_encounter_from_trope` was on zero dispatch paths (no callers), so its removal changes no runtime behavior — the live trope-completion path (`trope_tick.py` → `_handshake_resolved_tropes`) never touched it.

**Observations:**
- [VERIFIED][RULE] Removal is complete — repo-wide grep for `resolve_encounter_from_trope`, `name_generators`, and the `generate_name` tool returns zero hits outside the new RED test. Evidence: my own sweep + rule-checker rule 17 (checked ~65 `ToolContext(...)` sites) + preflight dead-reference sweep. Three independent confirmations.
- [VERIFIED] `encounter_resolved_span` import removal correctly scoped — it was the sole user *in `encounter_lifecycle.py`*; the span function itself stays defined and used at `narration_apply.py`, `dispatch/dice.py`, `dispatch/fate_contest.py`, `game/hp_depletion.py`. Not a wiring break. Evidence: rule-checker rule 10 + comment-analyzer.
- [VERIFIED] `ToolContext` remains a valid `@dataclass(frozen=True, slots=True)` after the field removal — 14 fields, `name_generators` absent, no default-ordering violation (all remaining fields keep defaults). Evidence: my runtime `dataclasses.fields()` introspection.
- [VERIFIED][TEST] The 4 new tests are genuine, non-vacuous RED→GREEN — test-analyzer checked out the pre-removal commit in a worktree and confirmed all 4 *fail* there and pass at HEAD. Reflection-based (hasattr / registry membership / ModuleNotFoundError / dataclass fields) per the sanctioned "No Source-Text Wiring Tests" exception. Evidence: test-analyzer empirical run.
- [VERIFIED] No unique coverage dropped — `Encounter.resolve_from_trope` (the surviving *method*) keeps direct tests in `tests/game/test_encounter.py`; the `NameGenerator`/`build_from_culture` engine keeps coverage in `tests/genre/test_namegen_*` + `tests/server/test_npc_*namegen*`. Only dead wrapper/duplicate tests were removed. Evidence: test-analyzer + rule-checker.
- [VERIFIED][DOC] The 41→40 count change and its inline changelog comment are accurate — `default_registry.list_names()` returns exactly 40 at runtime with `generate_name` absent. Evidence: comment-analyzer + rule-checker both ran the count.
- [LOW][DOC] **Stale doc-drift:** `tests/agents/test_narrator_uses_sdk_client.py:7` ("Advertise the full **41-tool** array") and `:35` ("Importing the tools package wires the **41 adapters**") still say 41 after the count dropped to 40. The assertion (`:191`) and its changelog comment (`:187`) are correct; only these two prose references lag. Non-blocking (Low — documentation, no correctness impact), but ironic in a stale-reference-cleanup story. Logged as a non-blocking finding.

### Rule Compliance

Mapped to `.pennyfarthing/gates/lang-review/python.md` + the four load-bearing CLAUDE.md doctrines. reviewer-rule-checker enumerated 17 rules / 27 instances exhaustively; I cross-checked the load-bearing ones:
- **No Stubbing (complete removal):** both stubs fully excised — no half-removed field, no orphaned import, no dangling barrel export. Verified by reflection (field/tool/module all absent). ✓
- **No Source-Text Wiring Tests:** all 4 new tests use the sanctioned reflection form (dataclass/registry/import introspection), never `read_text()` source grep. ✓
- **#10 Import hygiene:** `NameGenerator` TYPE_CHECKING import + `generate_name` barrel export + `encounter_resolved_span` import all removed with their symbols; ruff clean; alphabetical order preserved. ✓
- **#3 Type annotations / #6 Test quality:** all 4 test signatures `-> None`; every assertion checks a specific value with an explanatory message — no vacuous truthy checks. ✓
- **#1 Silent exception swallowing / #15 No Silent Fallbacks:** N/A — the diff *removes* the tool's `name_generators is None` graceful-degrade path; it adds no new exception/fallback logic. ✓

### Disabled-dimension coverage (subagents off via settings)

- **[EDGE]** edge-hunter disabled — assessed directly: a pure-deletion diff introduces no new branches/boundaries; the only logic touched is *removed*. No edge surface. N/A.
- **[SILENT]** silent-failure-hunter disabled — assessed directly: no `try/except`, no swallowed errors added; the removed code's silent-empty-return is being deleted, not introduced. N/A.
- **[TYPE]** type-design disabled — assessed directly: no new types; `ToolContext` field removal verified type-consistent (frozen/slots intact). N/A.
- **[SEC]** security disabled — assessed directly: no auth/input/tenant surface touched; removing an unreachable tool reduces attack surface. N/A.
- **[SIMPLE]** simplifier disabled — assessed directly: this diff *is* the simplification (−628 net lines of dead code). No over-engineering added. N/A.

### Devil's Advocate

Assume this removal is broken. Where would it bite? First: could the narrator have depended on `generate_name` at runtime? No — `ctx.name_generators` was permanently `None`, so every call returned `{names: [], name_generators_wired: False}`. A tool that has only ever returned nothing cannot be load-bearing; the live naming is `narration_apply.build_from_culture` (Story 83-2), which is untouched and independently tested. Removing a no-op narrows the tool menu but changes no player-visible behavior. Second: could a genre-pack YAML or prompt template force `generate_name` by literal name, now dangling? The tool catalog and descriptions are *generated from the registry*, and grep finds no hardcoded `generate_name` in the orchestrator or SDK client — so a removed tool simply stops being advertised; no prompt references a ghost. Third: could `resolve_encounter_from_trope` be reached by dynamic dispatch (getattr) that grep misses? No — it was a plain module-level function referenced only by direct import in tests, no `getattr(encounter_lifecycle, ...)` pattern exists, and its docstring itself declared zero callers. Fourth: does deleting it lose a needed future hook? The trope engine already resolves via a *different* path (`_handshake_resolved_tropes`); if a future story needs this exact helper it lives in git history — keeping dead code "just in case" is precisely the No-Stubbing anti-pattern this story exists to kill. Fifth, and the one real bite: the stale "41" comments at lines 7/35 will mislead the next reader who trusts the docstring over the assertion. That is a genuine (if Low) defect and is the one thing the devil's advocate legitimately surfaces — captured as a finding. Nothing else survives scrutiny: the removal is complete, scoped, and behavior-neutral.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Once `resolve_encounter_from_trope` is deleted, `Encounter.resolve_from_trope` (`sidequest/game/encounter.py:475`) has only test callers (`tests/game/test_encounter.py:860-879`) and no production caller. Affects `sidequest/game/encounter.py` (evaluate whether the method is also dead once the helper is gone — the resolved-trope handshake at `_handshake_resolved_tropes` may or may not need it). Deliberately **out of scope** for this 1-pt story (story names the helper, not the method; the method has its own direct unit tests). Flag for a follow-up dead-method sweep. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The narrator's advertised tool count is pinned by a hardcoded literal in `tests/agents/test_narrator_uses_sdk_client.py::test_orchestrator_routes_narration_through_sdk` (`== 40`). Affects `tests/agents/test_narrator_uses_sdk_client.py` — every tool add/remove must hand-edit this number, which is brittle (this story hit it). Consider asserting only `len(allowed) == len(default_registry.list_names())` and dropping the magic constant, or deriving the expected count from a category census. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Stale doc-drift — `tests/agents/test_narrator_uses_sdk_client.py:7` ("Advertise the full 41-tool array") and `:35` ("Importing the tools package wires the 41 adapters") still cite 41 after the removal dropped the count to 40. Affects `tests/agents/test_narrator_uses_sdk_client.py` (update both prose references to 40; the assertion at :191 and changelog comment at :187 are already correct). Low severity — documentation only, no correctness impact — so not a blocker, but worth folding into the finish commit or a quick follow-up given this is itself a stale-reference-cleanup story. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Chose "remove" over "wire" for both delete-or-wire targets**
  - Spec source: context-story-162-8.md (title) + session AC Task 1/Task 2 ("deleted or wired" / "wiring resolved or the stub removed")
  - Spec text: "resolve_encounter_from_trope (no callers) deleted or wired; generate_name tool ctx.name_generators Phase-E wiring resolved or the stub removed"
  - Implementation: RED tests pin **removal** of both, foreclosing the "wire" branch the spec left open
  - Rationale: Both are unwired stubs the live engine already routed around (trope engine landed without the helper; `narration_apply.build_from_culture` is the live namer while `name_generators` stayed `None`). Wiring would add redundant parallel paths against Epic 162's consolidation grain. Matches SM's lean ("prefer deletion when there's no live consumer") and No Stubbing.
  - Severity: minor
  - Forward impact: Dev must remove code + obsolete tests (not add wiring). If Reviewer disagrees and prefers wiring, the RED tests must be inverted — flagged here so that decision is explicit, not silent.

### Dev (implementation)
- **Edited a file beyond TEA's stated removal surface**
  - Spec source: TEA Assessment "GREEN scope for Dev" (session file)
  - Spec text: enumerated 3 source files + 3 test files to change; did not list `tests/agents/test_narrator_uses_sdk_client.py`
  - Implementation: also updated the narrator tool-count assertion there `41 → 40`
  - Rationale: removing the `generate_name` tool drops the registry count by one, and that test asserts `len(allowed) == len(default_registry.list_names()) == 41`. It failed on the removal (correctly — it's a real wiring test) and had to be updated to stay GREEN. Not scope creep: it's a direct, mechanical consequence of the sanctioned removal.
  - Severity: trivial
  - Forward impact: none (documented inline with a Story 162-8 comment; flagged as a brittleness Improvement in Delivery Findings).

### Reviewer (audit)
- **TEA deviation "Chose remove over wire"** → ✓ ACCEPTED by Reviewer: the evidence is decisive — both targets are unwired seams the live engine routed around (`narration_apply.build_from_culture` is the live namer; the trope engine resolves via `_handshake_resolved_tropes`). Wiring would *add* redundant parallel paths, directly against Epic 162's consolidation intent. Removal is the correct reading of the "deleted or wired" branch.
- **Dev deviation "Edited a file beyond TEA's stated surface"** → ✓ ACCEPTED by Reviewer: mechanically necessary, not scope creep. `test_narrator_uses_sdk_client.py`'s `len(allowed) == len(default_registry.list_names()) == 41` is a genuine wiring assertion that *correctly* broke on the tool removal; updating it to 40 is the only honest way to keep it green. Confirmed 40 is the true runtime count.
- **No undocumented deviations found.** The only spec gap is the stale "41" prose left in that same file (lines 7, 35) — captured as a non-blocking Reviewer finding above, not a deviation (it's an incomplete edit, not a divergence from spec).