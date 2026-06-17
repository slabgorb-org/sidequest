---
story_id: "122-8"
jira_key: ""
epic: "122"
workflow: "tdd"
---
# Story 122-8: Relocate _KIND_TO_MESSAGE_CLS from server/session_handler to protocol tier; delete the validator.py grandfathered edge + its GRANDFATHERED guard entry (ADR-147 honesty — kills the last upward edge the guard grandfathers)

## Story Details
- **ID:** 122-8
- **Jira Key:** (none — YAML-based sprint)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T07:17:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T06:45:46Z | 2026-06-17T06:48:37Z | 2m 51s |
| red | 2026-06-17T06:48:37Z | 2026-06-17T06:58:23Z | 9m 46s |
| green | 2026-06-17T06:58:23Z | 2026-06-17T07:12:00Z | 13m 37s |
| review | 2026-06-17T07:12:00Z | 2026-06-17T07:17:10Z | 5m 10s |
| finish | 2026-06-17T07:17:10Z | - | - |

## Technical Approach

### Context
ADR-147 ("Honest Layering") establishes one import-direction law: imports flow downward only — `foundation <- {game, genre, orbital, magic, interior} <- server`. The layering guard (`tests/infrastructure/test_import_direction_guard.py`) currently grandfathers exactly one upward edge:

```python
GRANDFATHERED: dict[str, frozenset[str]] = {
    "game/projection/validator.py": frozenset({
        "sidequest.server.session_handler",
        "sidequest.server.session_handler._KIND_TO_MESSAGE_CLS",
    }),
}
```

This edge — validator.py reaching up into session_handler for `_KIND_TO_MESSAGE_CLS` — must be eliminated by relocating the dict to the protocol tier (which sits *below* all domain packages in the import hierarchy). Once relocated, the grandfather exception can be deleted, tightening the guard to enforce the layering law fully.

### Implementation Steps

1. **Create kind-to-message registry in protocol tier:**
   - Add `_KIND_TO_MESSAGE_CLS` dict to `sidequest/protocol/messages.py` or a new `sidequest/protocol/registry.py`
   - Dict must be module-level and immutable (module-level dict, or frozen after construction)
   - Export via `sidequest/protocol/__init__.py`

2. **Update imports in server/session_handler.py:**
   - Change `_KIND_TO_MESSAGE_CLS: dict[str, type] = { ... }` definition to remove the dict
   - Import from protocol tier instead
   - Preserve all call sites (lines 202, 226 in current code)

3. **Update imports in game/projection/validator.py:**
   - Remove the two lazy in-method imports of `_KIND_TO_MESSAGE_CLS` from `sidequest.server.session_handler`
   - Replace with import from protocol tier
   - Both call sites (`_filter_reachable_kinds` and `_schema_fields_for_kind`) can now use a direct import

4. **Delete grandfathered exception:**
   - Remove the entire `"game/projection/validator.py"` entry from `GRANDFATHERED` dict in `tests/infrastructure/test_import_direction_guard.py`
   - Remove the self-expiry test block (lines 267–281) that checks validator.py is still importing the pinned targets
   - Simplify the module docstring to reflect the deletion (lines 35–56)

5. **Verify layering guard passes:**
   - Run `uv run pytest tests/infrastructure/test_import_direction_guard.py -v`
   - All upward-import tests must pass
   - Grandfathered-exception self-expiry test must be gone (or updated to match the new GRANDFATHERED set)

### Acceptance Criteria

- [ ] `_KIND_TO_MESSAGE_CLS` dict relocated to protocol tier (immutable, module-level, exported)
- [ ] server/session_handler.py imports the dict from protocol tier; all call sites unchanged
- [ ] game/projection/validator.py imports from protocol tier (no upward edges to server)
- [ ] Layering guard: GRANDFATHERED exception for validator.py fully deleted
- [ ] Layering guard: self-expiry test block removed or simplified
- [ ] `uv run pytest tests/infrastructure/test_import_direction_guard.py -v` passes green
- [ ] `uv run pytest -v` full suite passes (TDD: add integration test verifying protocol registry is wired and reachable)
- [ ] Story completed: no dangling branches, PR merged to develop

## Sm Assessment

Story selected by Operator from the p2 backlog. Setup verified clean: session at orchestrator root, branch `feat/122-8-kind-to-message-cls-protocol-tier` off `origin/develop` (sidequest-server is gitflow, base `develop` not `main`), context written, ISO-8601 phase timestamp.

Scope is a focused ADR-147 "Honest Layering" cleanup, server-only, 2 pts. It eliminates the **last** grandfathered upward import edge (`game/projection/validator.py` → `sidequest.server.session_handler._KIND_TO_MESSAGE_CLS`) by relocating the dict to the protocol tier (which sits below all domain packages), then deletes the GRANDFATHERED guard entry + its self-expiry test.

Routing → **TEA (RED phase)**. Notes for The Architect:
- This is a pure relocation/refactor — behavior must not change. The wiring test (a known project rule: "Every Test Suite Needs a Wiring Test") should assert the relocated `_KIND_TO_MESSAGE_CLS` is reachable through the **production** path — i.e. session_handler and validator both resolve the same registry object, not a duplicated copy. Watch for accidental fork-into-two-dicts.
- The deliverable also includes tightening the layering guard itself (`tests/infrastructure/test_import_direction_guard.py`): the GRANDFATHERED entry and the self-expiry block must be gone, and the guard must still go green with zero remaining upward edges. A RED test that asserts "no grandfathered entry for validator.py" is the natural failing-first test.
- No Jira on this project (YAML sprint); no Jira transitions needed.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Pure relocation/refactor, but it changes a load-bearing import boundary (ADR-147 layering law) with ~12 production/test consumers — needs failing tests pinning the end-state contract before Dev moves anything.

**Test Files:**
- `tests/protocol/test_kind_to_message_cls_relocation.py` (new) — 6 tests

**Tests Written:** 6 tests covering all 5 ACs + the "no circular imports" constraint.
**Status:** RED (5 failing as designed, ready for Dev). 1 standing regression guard is GREEN (see below).

Verified directly (`uv run pytest ... -n0`, not via testing-runner which clobbers the session + hallucinates GREEN on this project): **5 failed, 9 passed** — the 5 relocation-driving tests fail for the right reasons (`protocol._KIND_TO_MESSAGE_CLS` absent; `GRANDFATHERED` still holds the validator edge; validator still imports up into `sidequest.server`); the 9 passing = my green guard (`test_protocol_tier_does_not_import_up_into_server`) + the 8 existing layering-guard tests still green.

| Test | AC | RED now? |
|------|----|----------|
| `test_kind_to_message_cls_exported_from_protocol_tier` | AC1 (relocation + exact mapping, no drift) | RED |
| `test_session_handler_reexports_the_same_registry_object` | AC2 + back-compat (identity, no fork) | RED |
| `test_validator_reads_the_relocated_registry` | AC2/AC4 wiring (production-path, single source of truth) | RED |
| `test_grandfathered_edge_for_validator_is_removed` | AC3 (`GRANDFATHERED == {}`, last edge) | RED |
| `test_validator_no_longer_imports_up_into_server` | AC2/AC3 (zero upward edges) | RED |
| `test_protocol_tier_does_not_import_up_into_server` | "no circular imports" constraint | GREEN (standing guard) |

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #10 Import hygiene — circular imports | `test_protocol_tier_does_not_import_up_into_server` | green guard |
| #10 Import hygiene — no upward edges | `test_validator_no_longer_imports_up_into_server` | RED |
| #6 Test quality — meaningful assertions, patch-where-used | self-check below; `test_validator_reads_the_relocated_registry` patches the registry where validator *reads* it | pass |
| #13 Fix-introduced regressions (meta) — don't break the ~12 existing importers | `test_session_handler_reexports_the_same_registry_object` + full-suite AC4 | RED + suite |

**Rules checked:** 3 of 13 applicable (the rest — silent except #1, mutable defaults #2, type gaps #3, logging #4, paths #5, resource leaks #7, deserialization #8, async #9, input validation #11, deps #12 — are N/A to a pure dict relocation: no exceptions, I/O, async, user input, or new deps).
**Self-check (Phase C):** 0 vacuous tests. Every test asserts a specific value (exact `dict(reg) ==`, object identity `is`, post-mutation membership, `GRANDFATHERED == {}`). No `assert True`, no bare-truthy, no always-None.

**Notes for Agent Smith (Dev / GREEN):**
- Natural home: `sidequest/protocol/messages.py` (all 7 message classes are defined there at lines 1085+, so place the dict *after* the class defs — or in a new `protocol/registry.py` importing them). Either way export it from `protocol/__init__.py` so `sidequest.protocol._KIND_TO_MESSAGE_CLS` resolves.
- **Keep the name `_KIND_TO_MESSAGE_CLS`** and have `session_handler` re-import it (`from sidequest.protocol... import _KIND_TO_MESSAGE_CLS`) so `session_handler._KIND_TO_MESSAGE_CLS` stays valid — ~10 test modules and `server/emitters.py:367` import it from there. The identity test enforces this.
- `validator.py` (`_filter_reachable_kinds` L37, `_schema_fields_for_kind` L108): swap the two lazy `from sidequest.server.session_handler import` lines to import from the protocol tier. They can become top-level imports (protocol is below game, no circular risk).
- `emitters.py:367` is server→server — not a layering violation; you may leave it importing from `session_handler` (resolves to the same object) or repoint to protocol. No test forces either.
- Then delete the `game/projection/validator.py` entry from `GRANDFATHERED` and delete the now-empty-parametrize `test_grandfathered_exceptions_are_still_live` block (lines 260–281 + the §self-expiry docstring) in `tests/infrastructure/test_import_direction_guard.py`. Trim the module docstring's GRANDFATHERED section.
- **Do NOT freeze the dict to MappingProxyType** — see the deviation below; it breaks ~13 `monkeypatch.setitem` sites and AC4.

**Handoff:** To Dev (Agent Smith) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/protocol/messages.py` — `_KIND_TO_MESSAGE_CLS` defined here (module-level, at EOF after the 7 message classes it maps); load-bearing comments (RELATIONSHIPS/LOCATION_DESCRIPTION deliberately-absent warning, TACTICAL_GRID/DUNGEON_MAP non-event-sourced notes) carried over verbatim.
- `sidequest/protocol/__init__.py` — import + `__all__` entry so `sidequest.protocol._KIND_TO_MESSAGE_CLS` resolves.
- `sidequest/server/session_handler.py` — dict definition removed; now imports `_KIND_TO_MESSAGE_CLS` from `protocol.messages` (still used by the replay path `_build_message_for_kind`, and re-exported for back-compat). Dropped the 7 now-unused message-class imports (verified used only by the dict), kept the 4 payloads the replay path needs.
- `sidequest/game/projection/validator.py` — two lazy upward imports replaced with one top-level `from sidequest.protocol.messages import _KIND_TO_MESSAGE_CLS` (circular-safe: protocol is below game). Stale "deferred to avoid circular import" docstrings updated.
- `tests/infrastructure/test_import_direction_guard.py` — `GRANDFATHERED` emptied (`= {}`), obsolete `test_grandfathered_exceptions_are_still_live` self-expiry test removed, module docstring's grandfather section rewritten to "zero exceptions."

**Implementation choice:** Registry lives in `protocol/messages.py` (not a new `registry.py`) — zero new imports, the 7 classes are co-located, simplest layer-honest home. Single source of truth: `protocol.messages._KIND_TO_MESSAGE_CLS` IS the object re-exported by `session_handler` and imported by `validator`/`emitters` (object identity, verified by the wiring test). Kept it a plain mutable dict — see deviation below.

**Tests:** Story suite + guard **13/13 passing** (6 relocation tests GREEN incl. the wiring test; 7 guard tests GREEN). All ~10 affected importer/monkeypatch files: **61 passed, 9 skipped, 0 regressions**.
**Full suite:** 87 failed / 12967 passed — **proven baseline**: base (impl stashed) = 92 failed / 12963 passed; the delta is exactly my 5 RED→GREEN tests + 1 removed obsolete test. **Zero new failures**; the 87 are pre-existing (in-flight WWN combat per ADR-114/143 + an xdist-ordering flake in `test_watcher_events::test_publish_event_shape`, which passes in isolation).
**Branch:** `feat/122-8-kind-to-message-cls-protocol-tier` (pushed).
**Lint/format:** ruff check + format clean (scoped to changed files).

**Handoff:** To verify (The Architect / simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN 41/0/5; ruff check + format clean on all 6 files; 0 code smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer manually (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — covered manually (see [SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered manually (see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered manually (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered manually (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none (7 rules checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered manually (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered manually (see [RULE] + Rule Compliance) |

**All received:** Yes (2 enabled subagents returned, both clean; 7 disabled via `workflow.reviewer_subagents` settings — their domains assessed manually below)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 deferred (LOW — registry/reconstructor cross-file coupling, non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED

A textbook ADR-147 relocation. I traced every cause to its effect — the registry moves down a tier, the upward edge dies, and nothing else changes. Both enabled subagents (preflight, security) returned clean, and I independently confirmed the load-bearing claim (object identity across the re-export chain) in a fresh interpreter.

**Data flow traced:** A persisted event row → `_build_message_for_kind(kind, ...)` (`session_handler.py:169`) → `_KIND_TO_MESSAGE_CLS.get(kind)`. Post-relocation, that name resolves to `sidequest.protocol.messages._KIND_TO_MESSAGE_CLS` via a plain re-import — I verified in a fresh interpreter that `session_handler._KIND_TO_MESSAGE_CLS is protocol._KIND_TO_MESSAGE_CLS` is `True` and `emitters` chains to the same object. Unknown kind → `ValueError` (fail-loud) is preserved. Validator's `_filter_reachable_kinds()` derives from the same object (confirmed: `== frozenset(protocol_dict)`).

**Observations (8):**
- `[VERIFIED]` **Single source of truth, no fork** — `sidequest/protocol/messages.py:1852` defines the dict; `session_handler.py:33` and `validator.py:9` import it; fresh-interpreter check confirms one shared object (identity `is True`). Complies with the SM's explicit anti-fork concern and ADR-147.
- `[SEC]` **clean** (subagent + manual): no new attack surface, registry mutated only by trusted test monkeypatch, `json.loads` in the replay path reads server-written DB rows (unchanged), no player free-text touches this dict (ADR-047 N/A). Emptying `GRANDFATHERED` *tightens* the guard.
- `[SILENT]` **No silent fallback introduced** — `session_handler.py:169-171` still `raise ValueError` on unknown kind; no try/except added or modified. Complies with No-Silent-Fallbacks (CLAUDE.md).
- `[EDGE]` **Boundary paths intact** — the three consumers (`_build_message_for_kind`, `_filter_reachable_kinds`, `_schema_fields_for_kind`) read the same dict with unchanged logic; the empty-`GRANDFATHERED` edge is handled (the law test now iterates an empty allow-set, correctly flagging any upward edge). Verified the now-empty `GRANDFATHERED` doesn't break `test_no_upward_imports_beyond_grandfathered` (`.get(rel_path, frozenset())` default).
- `[TEST]` **Test quality high** — `tests/protocol/test_kind_to_message_cls_relocation.py`: exact `dict(reg) ==` (anti-drift), object-identity `is`, monkeypatch-propagation wiring (behavioral, production-path — not a source-text grep, complies with CLAUDE.md "No Source-Text Wiring Tests"), `GRANDFATHERED == {}`. No vacuous assertions.
- `[TYPE]` **Type design preserved** — `_KIND_TO_MESSAGE_CLS: dict[str, type]` annotation carried over verbatim; no stringly-typed regression, no unsafe cast.
- `[SIMPLE]` **Net simplification** — validator's two lazy in-method imports + `# noqa: PLC0415` suppressions collapse to one top-level import; the deferred-import workaround and its explanatory docstrings are gone. No over-engineering, no dead code.
- `[DOC]` **Comments accurate** — load-bearing registry comments (RELATIONSHIPS/LOCATION_DESCRIPTION deliberately-absent, TACTICAL_GRID/DUNGEON_MAP non-event-sourced) carried over verbatim; guard module docstring rewritten correctly to "zero exceptions"; stale "deferred to avoid circular import" docstrings in validator removed. One minor coupling note — see deferred finding.

### Rule Compliance (lang-review/python.md, exhaustive over the diff)
- **#1 Silent exceptions** — COMPLIANT. No try/except added; `_build_message_for_kind` fail-loud preserved.
- **#2 Mutable defaults** — COMPLIANT. No function signatures changed; the module-level dict is intentional shared registry state, not a default arg.
- **#3 Type annotations** — COMPLIANT. `dict[str, type]` on the registry; validator helpers retain their annotations.
- **#4 Logging** — N/A. No logging touched.
- **#5 Path handling** — COMPLIANT. New test uses `pathlib` (`SIDEQUEST_PKG / "protocol"`, `rglob`); no string path concat.
- **#6 Test quality** — COMPLIANT (see [TEST]).
- **#7 Resource leaks** — N/A. No file/socket/lock handles.
- **#8 Unsafe deserialization** — COMPLIANT. `json.loads` on server-written DB rows, unchanged; no pickle/yaml/eval/exec.
- **#9 Async** — N/A. No async code.
- **#10 Import hygiene** — COMPLIANT, and the *subject* of the story: no star imports, no circular import (protocol is leaf — verified `import sidequest.protocol` succeeds and pulls no server/game), the upward edge is eliminated. The `_KIND_TO_MESSAGE_CLS` entry in `protocol/__init__.__all__` is explicit (not `*`).
- **#11 Input validation** — N/A. Registry maps hardcoded trusted constants.
- **#12 Dependency hygiene** — N/A. No dependency changes.
- **#13 Fix-introduced regressions (meta)** — COMPLIANT. Dev proved the baseline (92 fail on base → 87 on branch; delta = exactly the 5 RED→GREEN tests + 1 removed obsolete test). Zero new failures; I cross-checked the math and it reconciles.

### Devil's Advocate
Let me argue this is broken. **Cross-file coupling rot:** the registry now lives in `protocol/messages.py`, but its *replay reconstructor* — the per-kind `if kind == "X": ... Payload(**data)` ladder — stays in `server/session_handler._build_message_for_kind`. Before this change they were adjacent in one file, so a dev adding a new event-kind saw both at once. Now a dev who adds `"FOO": FooMessage` to the protocol dict, far from the reconstructor, can ship a kind that has no payload branch. On reconnect-replay of a persisted FOO event, `_build_message_for_kind` would fall through to its terminal `raise ValueError("no payload constructor")`. Is that a latent crash? It is — but it is a *loud* one (ValueError, not silent corruption), and `tests/server/test_replay_kind_coverage.py` already asserts the required kinds are present and that the dict and `_REPLAY_SKIP_KINDS` don't overlap. So the blast radius is bounded by fail-loud + an existing coverage test. I'll log it as a non-blocking improvement (a one-line cross-reference comment), not a blocker. **Star-import leak:** could the underscore name in `__all__` leak via `from sidequest.protocol import *`? I grepped — there are zero star-imports of protocol in the tree, and even if one appeared, exporting a dict is harmless. **Circular import under odd import order:** could `validator` (in `game/`) importing `protocol.messages` at module load deadlock? No — `protocol/messages.py` imports nothing from `game`/`server` (grep-confirmed: only docstring `:func:` references), and a fresh `import sidequest.protocol` + `validator` succeeds. **Confused deputy via re-export:** does `emitters` reaching the dict through `session_handler`'s re-export risk binding a stale/copied object? No — Python's module cache guarantees a plain `from X import name` binds the one object; the AC2 `is` test pins it permanently. The change survives every line of attack I can mount. The only real residue is the coupling note above.

**Pattern observed:** Layer-honest relocation to the lowest tier that owns the dependencies (`protocol/messages.py` already defines all 7 message classes) — `sidequest/protocol/messages.py:1844-1852`. Exemplary ADR-147 execution.
**Error handling:** fail-loud `ValueError` on unknown kind preserved at `session_handler.py:169-171`.
**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

### TEA (test design)
- **Improvement** (non-blocking): The protocol tier is not in the layering guard's `GUARDED_TIERS` (only `foundation, game, genre, orbital, magic, interior`). Once `_KIND_TO_MESSAGE_CLS` lives in `protocol/`, an accidental upward `protocol → server` import would slip past the guard. Affects `tests/infrastructure/test_import_direction_guard.py` (`GUARDED_TIERS`). My `test_protocol_tier_does_not_import_up_into_server` covers the relocation target as a stopgap; a follow-up could add `protocol` to `GUARDED_TIERS` wholesale. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): TEA's `GUARDED_TIERS` finding is now concretely actionable — `protocol/` (and arguably `mutation/`, `dungeon/`, `agents/`, `corpus/`, `renderer/`, `daemon_client/`) sit below `server` but aren't guarded. Adding `protocol` to `GUARDED_TIERS` is a clean ~1-line follow-up that would supersede my stopgap `test_protocol_tier_does_not_import_up_into_server`. Affects `tests/infrastructure/test_import_direction_guard.py`. *Found by Dev during implementation.*
- Otherwise no upstream findings — the relocation matched TEA's notes exactly (back-compat re-export needed, mutable dict, messages.py home all confirmed by the suite).

### Reviewer (code review)
- **Improvement** (non-blocking, deferred LOW): The kind→class registry (`protocol/messages.py`) and its replay reconstructor (`session_handler._build_message_for_kind`) now live in different files/tiers. A dev adding a new kind to the dict without adding a payload branch ships a fail-loud `ValueError` on replay of that kind. Mitigated by fail-loud + `tests/server/test_replay_kind_coverage.py`, but a one-line cross-reference comment on the relocated dict ("adding a kind here also needs a reconstructor branch in server/session_handler._build_message_for_kind") would restore the visual coupling the co-location used to provide. Affects `sidequest/protocol/messages.py`. *Found by Reviewer during code review.*
- Endorse the TEA/Dev `GUARDED_TIERS` finding — adding `protocol` to the guard's `GUARDED_TIERS` is the right follow-up and would supersede the stopgap `test_protocol_tier_does_not_import_up_into_server`.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Registry pinned mutable, not frozen — "immutable" half of AC1 relaxed**
  - Rationale: ~13 existing sites do `monkeypatch.setitem(session_handler._KIND_TO_MESSAGE_CLS, ...)` (test_narration_pov_emission/_regression, test_perception_rewriter_wiring, test_merged_mp_emitter_projection). A `MappingProxyType` raises `TypeError` on `setitem`, breaking all of them — and AC4 requires the full suite to pass. AC1 and AC4 are same-authority (both story context) and conflict; I preserve the larger contract (the suite) and keep the "module-level, constructed-once, single-source-of-truth" spirit of AC1.
  - Severity: minor
  - Forward impact: True runtime immutability would require first migrating those monkeypatch sites onto a registration helper — out of scope for this 2pt story; file as future work if desired.
- **Relocated registry implemented as a plain mutable module-level dict, not frozen**
  - Rationale: Implemented per TEA's tests and deviation. Freezing it raises `TypeError` on the ~13 existing `monkeypatch.setitem(_KIND_TO_MESSAGE_CLS, ...)` sites and breaks AC4 (full suite passes). Object identity across protocol/session_handler/validator gives the "single source of truth" the AC's intent targets; the "frozen" half is the only part relaxed.
  - Severity: minor
  - Forward impact: A future true-immutability pass must first migrate the monkeypatch sites onto a registration helper (e.g. a `register_kind()` fixture). No consumer today relies on immutability.

## Design Deviations

### TEA (test design)
- **Registry pinned mutable, not frozen — "immutable" half of AC1 relaxed**
  - Spec source: context-story-122-8.md, AC1 ("Immutable module-level definition") + Key Constraints ("the dict must be module-level and immutable ... constructed once and frozen")
  - Spec text: "The dict must be module-level and immutable (a frozenset of kinds, or constructed once and frozen)"
  - Implementation: Tests pin a single canonical module-level dict (one source of truth) and require it to stay mutable (`test_validator_reads_the_relocated_registry` does `monkeypatch.setitem` through the registry); no test asserts `MappingProxyType`/frozen.
  - Rationale: ~13 existing sites do `monkeypatch.setitem(session_handler._KIND_TO_MESSAGE_CLS, ...)` (test_narration_pov_emission/_regression, test_perception_rewriter_wiring, test_merged_mp_emitter_projection). A `MappingProxyType` raises `TypeError` on `setitem`, breaking all of them — and AC4 requires the full suite to pass. AC1 and AC4 are same-authority (both story context) and conflict; I preserve the larger contract (the suite) and keep the "module-level, constructed-once, single-source-of-truth" spirit of AC1.
  - Severity: minor
  - Forward impact: True runtime immutability would require first migrating those monkeypatch sites onto a registration helper — out of scope for this 2pt story; file as future work if desired.

### Dev (implementation)
- **Relocated registry implemented as a plain mutable module-level dict, not frozen**
  - Spec source: context-story-122-8.md, AC1 + Key Constraints ("immutable ... constructed once and frozen")
  - Spec text: "The dict must be module-level and immutable (a frozenset of kinds, or constructed once and frozen)"
  - Implementation: `_KIND_TO_MESSAGE_CLS: dict[str, type] = {...}` at module level in `protocol/messages.py` — a single canonical, constructed-once definition, but a plain `dict` (not `MappingProxyType`/frozen).
  - Rationale: Implemented per TEA's tests and deviation. Freezing it raises `TypeError` on the ~13 existing `monkeypatch.setitem(_KIND_TO_MESSAGE_CLS, ...)` sites and breaks AC4 (full suite passes). Object identity across protocol/session_handler/validator gives the "single source of truth" the AC's intent targets; the "frozen" half is the only part relaxed.
  - Severity: minor
  - Forward impact: A future true-immutability pass must first migrate the monkeypatch sites onto a registration helper (e.g. a `register_kind()` fixture). No consumer today relies on immutability.

### Reviewer (audit)
- **TEA deviation (registry pinned mutable, not frozen)** → ✓ ACCEPTED by Reviewer: sound. AC1 ("immutable") and AC4 ("full suite passes") are same-authority and genuinely conflict — ~13 `monkeypatch.setitem` sites would break under `MappingProxyType`. Relaxing only the "frozen" half while preserving "module-level, constructed-once, single source of truth" (enforced by the `is`-identity test) is the correct resolution for a 2pt relocation. The intent of AC1 — one canonical registry, no drift — is fully met.
- **Dev deviation (plain mutable module-level dict)** → ✓ ACCEPTED by Reviewer: identical rationale; implementation matches the tests and the TEA deviation exactly. Verified the dict is `dict[str, type]` at `protocol/messages.py:1852` and that object identity holds across the re-export chain.
- No undocumented deviations found. The relocation preserved the exact mapping (anti-drift test) and all comments; nothing diverged from spec beyond the two logged immutability entries.