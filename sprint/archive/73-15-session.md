---
story_id: "73-15"
jira_key: ""
epic: "73"
workflow: "tdd"
---
# Story 73-15: Filter narrator tool_definitions by bound ruleset — WWN/CWN-only tools exposed on every pack (ADR-117 tightening)

## Story Details
- **ID:** 73-15
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Repo:** sidequest-server
- **Branch Strategy:** gitflow (feat/73-15-filter-narrator-tools-by-ruleset)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T17:02:40Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T00:00:00Z | 2026-06-05T16:38:21Z | 16h 38m |
| red | 2026-06-05T16:38:21Z | 2026-06-05T16:47:55Z | 9m 34s |
| green | 2026-06-05T16:47:55Z | 2026-06-05T16:54:51Z | 6m 56s |
| review | 2026-06-05T16:54:51Z | 2026-06-05T17:02:40Z | 7m 49s |
| finish | 2026-06-05T17:02:40Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → TEA (RED phase) next. 2-pt p3 server-only tightening.

**Scope (single repo, sidequest-server):** Filter the narrator's `tool_definitions()`
so only tools compatible with the pack's bound ruleset are exposed. Today
`orchestrator.py` (~3844/3992) hands the narrator `default_registry.tool_definitions()`
— the *entire* registry — so WWN-only tools (`commit_effort`, `long_rest`,
`veterans_luck`) and CWN-only tools (`adjust_system_strain`,
`stabilize_mortal_injury`) appear on every pack, including native.

**Not a correctness bug — a tightening.** The gated tools self-guard fail-loud
(description says "WWN-only…"; handler raises `ValueError` when
`pack.rules.ruleset` ≠ required slug, e.g. `commit_effort.py:96`). No silent
fallback exists today, so RED must NOT assert on silent-fallback behavior. The
win is tool-budget + mis-attempt avoidance: the narrator should not see tools it
can only fail to use.

**Suggested test seams for TEA (RED):**
- Assembly-time filter: given a pack bound to `native`, the tool list handed to
  the narrator excludes `commit_effort`/`adjust_system_strain`/etc.; given a
  `wwn` pack, WWN tools are present and CWN tools absent (and vice-versa).
- Wiring test (mandatory): prove the *production* assembly path in
  `orchestrator.py` calls the filtered set, not just a unit on the registry.
- Regression guard: ruleset-agnostic tools remain present on all packs.

**ADR:** ADR-117 (Pluggable Ruleset Module System) — this is the routing
tightening flagged in the 2026-06-04 ruleset-routing dig.

**No Jira** (null in YAML) — Jira claim explicitly skipped.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral tightening with clear ACs — registry filtering + production
narration wiring both need coverage.

**Test Files:**
- `tests/agents/test_73_15_ruleset_tool_filter.py` — 14 tests (12 new-behavior
  RED, 2 intentional regression guards that pass now and must stay green).

**Tests Written:** 14 tests covering 4 ACs
**Status:** RED (12 failing — ready for Dev; 2 guards green by design)

**Verified RED reasons (ran `uv run pytest … -n0`, not testing-runner):**
- Registry/unit: `TypeError: tool() got an unexpected keyword argument 'ruleset'`
  and `Registry.tool_definitions() got an unexpected keyword argument 'ruleset'`
  — the filtering seam does not exist yet.
- Wiring: `AssertionError: native narration leaked gated tools: {all 5}` — the
  test drives the **real** `run_narration_turn` path (fake-SDK harness mirroring
  `test_narrator_uses_sdk_client.py`) and captures the actual `tools=` array, so
  it proves production wiring, not just a registry unit.
- OTEL: `narrator.tools.ruleset_filter` span not emitted yet.

### Intended GREEN shape (for Dev — Agent Smith)

1. `@tool` decorator + `_RegisteredTool` + `Registry.register` gain
   `ruleset: str | None = None`.
2. `Registry.tool_definitions(ruleset: str | None = None)` filters: include a
   tool iff `t.ruleset is None or t.ruleset == ruleset`. **`ruleset=None` →
   return ALL** (back-compat — the diagnostic call site, pack-less/legacy paths,
   and the self-guard backstop keep the full catalog).
3. The 5 gated tools declare `ruleset="wwn"` (commit_effort, long_rest,
   veterans_luck) / `ruleset="cwn"` (adjust_system_strain,
   stabilize_mortal_injury). **Declaration-driven, NOT a hardcoded name allowlist**
   (AC-4 is pinned by `test_filter_is_declaration_driven_not_a_name_allowlist`).
4. Both `orchestrator.py` call sites (~3904 diagnostic + ~4103 the real `tools=`)
   pass `context.pack.rules.ruleset` — but **only when `context.pack` is not
   None**; when it is None (legacy/fixture), pass `ruleset=None` (unfiltered) so
   the existing `test_narrator_uses_sdk_client.py::test_orchestrator_routes_
   narration_through_sdk` (pack=None → 35 tools) stays green.
5. Emit a `narrator.tools.ruleset_filter` OTEL span at the assembly site with
   attributes `tools.bound_ruleset`, `tools.advertised_count`,
   `tools.excluded_count` (the test asserts native → bound=native, excluded=5,
   advertised = full − 5). Satisfies the OTEL Observability Principle.

### Rule Coverage

| Rule (server CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| Wiring test (non-test consumer / reachable from prod) | `test_native_pack_narration_excludes_gated_tools_from_sdk_array`, `test_wwn_pack_narration_includes_wwn_excludes_cwn` (drive real `run_narration_turn`) | failing |
| OTEL on every subsystem decision | `test_narration_emits_ruleset_filter_otel_span` | failing |
| No Silent Fallbacks (self-guard backstop preserved) | `test_commit_effort_self_guard_still_raises_on_native_pack` | passing (guard) |
| No source-text wiring tests | behavior + OTEL assertions only — no `read_text()`/grep | n/a |
| Meaningful assertions (no vacuous) | self-checked — every test asserts concrete set membership / counts / error content | ok |

**Rules checked:** 5 of 5 applicable. **Self-check:** 0 vacuous tests.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/tool_registry.py` — `_RegisteredTool`, `Registry.register`,
  and the `@tool` decorator gain `ruleset: str | None = None`;
  `Registry.tool_definitions(ruleset=None)` filters (agnostic OR matching slug;
  None = full catalog, back-compat).
- `sidequest/agents/tools/commit_effort.py`, `long_rest.py`, `veterans_luck.py`
  — declare `ruleset="wwn"`.
- `sidequest/agents/tools/adjust_system_strain.py`,
  `stabilize_mortal_injury.py` — declare `ruleset="cwn"`.
- `sidequest/agents/orchestrator.py` — derive `bound_ruleset` from
  `context.pack.rules.ruleset` (None when pack absent), compute the filtered
  set once, reuse it for both the token-estimate diagnostic and the real
  `tools=` array, and emit the `narrator.tools.ruleset_filter` OTEL span.

**Tests:** 14/14 story tests passing (GREEN). Wider regression: full
`tests/agents/` + `tests/agents/tools/` = 1750 passed / 1 skipped;
`tests/game/ruleset/` + `tests/genre/` = 1062 passed / 49 skipped. The existing
`test_narrator_uses_sdk_client.py::test_orchestrator_routes_narration_through_sdk`
(pack=None → 35 tools) still green — back-compat confirmed. Ran directly via
`uv run pytest … -n0`, not testing-runner.

**Lint/format:** ruff check + format clean on all 7 changed files.

**TEA findings addressed:**
- *Improvement (dedup the two call sites):* done — both sites now use one
  `advertised_tool_defs` computed once; the OTEL span fires once per turn.
- *Question (swn packs):* confirmed correct — an `swn`-bound pack has no gated
  tools, so it simply receives the agnostic set; no swn-only tool is dropped
  (none declare `ruleset="swn"`).

**Branch:** feat/73-15-filter-narrator-tools-by-ruleset (pushed)

**Handoff:** To verify (TEA) / review (Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 4 obs (tests GREEN, lint clean) | confirmed 1 ([PRE] awn gap), noted 3 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edges covered by reviewer |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-failure covered by reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality covered by reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — docs covered by reviewer ([DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type design covered by reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 3 (1 med, 2 low) + 1 OTEL obs | confirmed 1 med (awn) non-blocking, 2 low downgraded/noted |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity covered by reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rules covered by reviewer ([RULE]) |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 Medium + 3 Low confirmed (all non-blocking), 0 dismissed outright, 0 deferred

## Impact Summary

### Delivery Findings Compilation

**Finding Count:** 3 discrete findings logged (1 TEA improvement + 1 TEA question + 2 Reviewer improvements)  
**Blocking Issues:** 0  
**Non-Blocking Issues:** 3

#### Summary by Phase

**TEA (Test Design):**
- Improvement: Dedup the two `tool_definitions()` call sites (duplication eliminated in GREEN)
- Question: Confirm swn packs don't silently drop tools (confirmed correct)

**Dev (Implementation):**
- No upstream findings; GREEN shape held exactly; both TEA pre-flagged findings resolved in-story

**Reviewer (Code Review):**
- Improvement (awn subclass family-mismatch): Exact-string filter vs. isinstance check on dispatch self-guards create an advertise/dispatch divergence for awn ruleset. Zero live impact (no pack binds awn); documented for fast-follow before awn pack ships.
- Improvement (getattr guard): `getattr(_pack, "rules", None)` masks non-None pack with rules=None into unfiltered path. Structurally impossible via real GenrePack model; recommended distinguishing pack=None (legitimate) from pack+rules=None (fail loud) for strict compliance. Low severity.

#### Technical Exposure

- **Filter Correctness:** Verified against all 11 live packs (native, swn, cwn×2, wwn×2, others). All map correctly.
- **Back-Compat:** Pack=None path (legacy narration tests) preserved; existing `test_orchestrator_routes_narration_through_sdk` still green.
- **Operability:** Single computation site (dedup), reused for both token-estimate diagnostic and SDK `tools=` array. OTEL span `narrator.tools.ruleset_filter` emits decision once per turn.

#### Risk Assessment

- **Severity:** No blocking issues. Both improvements are non-blocking and documented for follow-up.
- **Deployment Readiness:** Code is approved, all tests pass, no regressions. Safe to merge.
- **Future Work:** Recommend ruleset-family-aware filter (match module class vs. exact string) + awn test coverage before any awn-bound pack ships.

## Reviewer Assessment

**Verdict:** APPROVED

All four stated ACs are met and **every live pack maps correctly** (verified against
sidequest-content: native/swn → agnostic-only; cwn ×2 road_warrior+neon_dystopia →
CWN tools; wwn ×2 heavy_metal+elemental_harmony → WWN tools). No Critical/High issues.
Confirmed findings are Medium/Low and non-blocking; the standout (awn) has **zero live
impact** (no pack binds awn).

**Data flow traced:** player turn → `Orchestrator.run_narration_turn` →
`context.pack.rules.ruleset` (bound slug) → `default_registry.tool_definitions(slug)`
→ `advertised_tool_defs` → both the token-estimate diagnostic and the SDK `tools=`
array (one computation, reused). Safe: filtering only narrows the model's advertised
capability surface; it carries no per-session player data, and the dispatch-side
`perception_filter.filter_result` is unchanged.

**Observations (≥5):**
- `[VERIFIED]` Filter predicate correct — `tool_registry.py:225` `ruleset is None or
  t.ruleset is None or t.ruleset == ruleset`: no-slug→all (back-compat), agnostic→always,
  gated→exact match. Complies with AC-1/AC-2/AC-4 (declaration-driven, no name allowlist).
- `[VERIFIED]` AC-3 self-guard intact — the 5 handlers keep their fail-loud guards;
  `dispatch()` is unchanged, so the advertised filter is primary and the self-guard is
  the backstop (defense-in-depth, as the story requires).
- `[VERIFIED]` Single narrator tool-bearing call site — `orchestrator.py:4133` now uses
  `advertised_tool_defs`; the only other `complete_with_tools` (`dungeon/materializer.py:1208`)
  passes `tools=[]`, out of scope. No unfiltered path remains.
- `[SEC]` `[MEDIUM]` **awn family-mismatch** at `tool_registry.py:225` / the two CWN tool
  decorations — `adjust_system_strain` & `stabilize_mortal_injury` are tagged
  `ruleset="cwn"` and filtered by exact string match, but their dispatch self-guards admit
  the **awn** subclass via `isinstance(module, CwnRulesetModule)`. An awn-bound pack would
  have these tools suppressed from the narrator surface while dispatch would still accept
  them — an advertise/dispatch inconsistency. **Non-blocking:** no pack binds awn today
  (verified in content), and all stated ACs cover only native/wwn/cwn. Recommend a
  fast-follow making the filter ruleset-family-aware (match the module class, mirroring the
  handler `isinstance` check) + awn test coverage. Corroborated independently by
  reviewer-preflight (obs 2).
- `[SILENT]` `[LOW]` `getattr(_pack, "rules", None)` at `orchestrator.py:3908` collapses a
  *non-None pack with a None `rules`* into the unfiltered path. Matches the No Silent
  Fallbacks rule, so **not dismissed** — but downgraded to Low: `GenrePack.rules` is
  non-optional (the masked input is structurally impossible via the real model), the
  self-guard backstop catches any misuse, and `pack=None` is the legitimate documented
  fixture path. Recommend distinguishing `pack=None` (unfiltered, fine) from
  `pack present + rules=None` (fail loud) for strict compliance.
- `[SEC]` `[LOW]` `bound_ruleset or "none"` at `orchestrator.py:3921` conflates a None pack
  with a (loader-impossible) empty ruleset and could collide with a future "none" slug.
  Cosmetic for the GM panel; the underlying counts are correct.
- `[TYPE]` `[VERIFIED]` `ruleset: str | None = None` is a clean optional declaration on
  `_RegisteredTool`/`register`/`@tool`/`tool_definitions`; no stringly-typed API regression
  beyond the pre-existing slug convention shared with `pack.rules.ruleset`.
- `[SIMPLE]` `[VERIFIED]` Computed once, reused at both sites — addresses TEA's dedup
  finding; net registry iterations per turn unchanged vs. before. No over-engineering.
- `[TEST]` `[VERIFIED]` Tests are non-vacuous and pin behavior at the production seam
  (fake-SDK `tools=` capture + OTEL span). Gap: no `ruleset="awn"` coverage (ties to the
  Medium finding); `swn` is covered. Acceptable given awn is unbound.
- `[DOC]` `[VERIFIED]` Comments are accurate and the `tool_definitions` docstring states the
  back-compat contract precisely; the diagnostic comment was correctly updated to note the
  payload now reflects the filtered set.
- `[RULE]` `[LOW]` OTEL span is a `with _ToolFilterSpan.open(...): pass` event marker — both
  subagents agree this is the established point-in-time event-span pattern (mirrors
  `tool.unknown.*`, ADR-132 ephemeral events); recorded as intentional, not a defect.
  Minor `[PRE]` style nit: the inline `from sidequest.telemetry.spans.span import Span`
  reaches the submodule rather than the package surface — consistent with the file's
  existing `_GuardrailSpan` import; no behavioral risk.

### Rule Compliance

- **No Silent Fallbacks** (CLAUDE.md, critical): the `ruleset=None → full catalog` contract
  is explicit, documented, and tested (legitimate pack-less path). The one soft spot is the
  `getattr(..., None)` rules guard — confirmed as a Low finding above (not dismissed).
- **No Stubbing:** no stubs/skeletons. ✓
- **Don't Reinvent / Wire Up What Exists:** reuses `tool_definitions`, the `@tool` seam, and
  the `Span.open` helper. ✓
- **Every Test Suite Needs a Wiring Test:** the fake-SDK narration tests drive the real
  `run_narration_turn` and assert the advertised array + OTEL span. ✓
- **No Source-Text Wiring Tests:** wiring proven via behavior + OTEL, not `read_text()`/grep. ✓
- **OTEL Observability:** `narrator.tools.ruleset_filter` span emits the decision. ✓
- **Crunch in the Genre:** filtering is keyed on the bound ruleset (genre-tier mechanic),
  flavor untouched. ✓

### Devil's Advocate

Argue the code is broken. The sharpest attack succeeds and is the awn case: this story's
entire reason to exist is *correct* tool↔ruleset mapping, and it ships a *wrong* mapping for
the awn ruleset — an exact-string filter (`== "cwn"`) over a class that the dispatch layer
treats polymorphically (`isinstance CwnRulesetModule`). Before this diff, an awn narrator
saw `adjust_system_strain`/`stabilize_mortal_injury` and the self-guard let them work; after
it, they vanish. So the diff is, narrowly, a capability *regression* for awn — the precise
advertise/dispatch divergence the change was meant to eliminate. The only thing saving it is
that no awn pack is wired today; if Jade or Keith binds `ruleset: awn` tomorrow, the narrator
silently loses two combat tools and nobody gets a failure — it just won't reach for them.
That is the genie's-paw shape SOUL warns about, in miniature.

Second attack: a confused author writes `ruleset: cwm` (typo) in a pack. The loader fails
loud (`UnknownRulesetError`) before the orchestrator, so the typo never reaches the filter —
good, that path is safe. Third: a stressed/partial loader yields a pack with `rules=None`;
the `getattr` swallows it and over-advertises — but the self-guards still fire on misuse, so
no wrong-ruleset state mutation occurs; worst case is wasted tool-budget, exactly the thing
the story set out to reduce, ironically reappearing on a degraded pack. Fourth: malicious
`pack.rules.ruleset` = arbitrary string → empty advertised set (all gated tools hidden) +
agnostic tools retained → narrator still functions, fails safe. None of these escalate beyond
Medium, and the live-pack matrix is correct, so the verdict holds: APPROVED with a documented
awn fast-follow.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The two `tool_definitions()` call sites in
  `orchestrator.py` (~3904 diagnostic token-estimate + ~4103 the real `tools=`)
  duplicate the assembly. Affects `sidequest/agents/orchestrator.py` — Dev should
  route both through one filtered call (compute the filtered list once per turn
  and reuse) so the diagnostic size reflects the advertised size and the OTEL
  span fires once. *Found by TEA during test design.*
- **Question** (non-blocking): `context.pack.rules.ruleset` is the bound slug, but
  `swn`-bound packs (space_opera) have no gated tools today — under the proposed
  contract an `swn` pack simply gets agnostic tools only (correct). No action
  needed; flagging so Dev confirms no swn-only tool is silently dropped.
  Affects `sidequest/agents/tool_registry.py`. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. The GREEN shape TEA specified held
  exactly; both pre-flagged findings were resolved in-story (single filtered
  call reused at both sites; swn packs confirmed correct).

### Reviewer (code review)
- **Improvement** (non-blocking): the CWN-family tools (`adjust_system_strain`,
  `stabilize_mortal_injury`) are tagged `ruleset="cwn"` and filtered by exact
  string match, but their dispatch self-guards admit the **awn** subclass
  (`isinstance(module, CwnRulesetModule)`). An awn-bound pack would have these
  tools suppressed from the narrator surface despite dispatch accepting them.
  Affects `sidequest/agents/tool_registry.py` (`tool_definitions` filter) and
  the two CWN tool decorations — make the filter ruleset-family-aware (match the
  module class, mirroring the handler `isinstance`) and add `ruleset="awn"` test
  coverage. **Zero live impact today** (no pack binds awn); do before any awn
  pack ships. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(_pack, "rules", None)` at
  `orchestrator.py:3908` collapses a non-None pack with `rules=None` into the
  unfiltered path. `GenrePack.rules` is non-optional so this is structurally
  impossible via the real model, but for strict No-Silent-Fallbacks compliance
  distinguish `pack=None` (unfiltered, legitimate) from `pack present + rules
  None` (fail loud). Affects `sidequest/agents/orchestrator.py`. *Found by
  Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. Test strategy covers all four ACs directly; the
  back-compat contract for `ruleset=None` (unfiltered) is an additive
  clarification of AC-1/AC-2, not a deviation — it preserves the pack-less
  legacy/fixture paths and the existing narrator-SDK wiring test.
  → ✓ ACCEPTED by Reviewer: the `ruleset=None` back-compat contract is sound and
  is what keeps the existing pack-less narrator wiring test green; agrees with
  author reasoning.

### Dev (implementation)
- No deviations from spec. Implemented the TEA GREEN shape verbatim: declaration-
  driven `ruleset` on `@tool`/registry, `tool_definitions(ruleset=None)` =
  full-catalog back-compat, the 5 gated tools tagged wwn/cwn, orchestrator
  derives the slug from `context.pack` and emits the
  `narrator.tools.ruleset_filter` span.
  → ✓ ACCEPTED by Reviewer: implementation matches the spec'd shape; all four
  ACs met and all live packs map correctly.

### Reviewer (audit)
- **Undocumented divergence (awn subclass):** Spec/ACs cover native/wwn/cwn; the
  code tags CWN-family tools by exact slug `"cwn"`, which diverges from the
  dispatch self-guards' `isinstance(CwnRulesetModule)` (admits awn). Not logged by
  TEA/Dev because awn is outside the stated ACs and unbound by any pack. Severity:
  M (latent, zero live impact). Captured as a non-blocking delivery finding for a
  family-aware fast-follow — does not block this story.