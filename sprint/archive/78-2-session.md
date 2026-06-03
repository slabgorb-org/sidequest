---
story_id: "78-2"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 78-2: Daemon dead-export sweep — NullRenderer/Renderer ABC, dead genre/models.py stubs, half-extracted dispatch_request image branch

## Story Details
- **ID:** 78-2
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-03T14:25:17Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T00:00:00Z | 2026-06-03T14:15:23Z | 14h 15m |
| implement | 2026-06-03T14:15:23Z | 2026-06-03T14:21:22Z | 5m 59s |
| review | 2026-06-03T14:21:22Z | 2026-06-03T14:25:17Z | 3m 55s |
| finish | 2026-06-03T14:25:17Z | - | - |

## Story Context

### Technical Background
This is a **wiring-audit finding** from `sq-wire-it` (2026-06-02), performed against `sidequest-daemon` at `origin/develop`. The daemon has pure dead exports that exist but have zero non-test consumers. The story is to **delete (1) and (2), and resolve the NotImplementedError trap in (3)**.

### Target 1: NullRenderer + Renderer ABC (sidequest_daemon/renderer/null.py)
- **Location:** `sidequest_daemon/renderer/null.py`
- **Status:** Completely unused — no importers anywhere (including tests)
- **Action:** DELETE the entire file
- **Verification:** Confirm zero references via grep before deletion
  ```bash
  grep -r "NullRenderer\|renderer.base.Renderer" sidequest_daemon/ tests/
  ```

### Target 2: Dead genre/models.py Stubs (sidequest_daemon/genre/models.py)
- **Dead symbols:**
  - `VisualStyle`
  - `AudioConfig`
  - `MixerSettings`
  - `AIGenerationConfig`
  - `ThemeFamily`
  - `MoodTrack`
  - `Variation`
  - `PackMeta`
- **Rationale:** The daemon uses `StyleCatalog` and YAML directly; these models are never instantiated
- **Exception:** `GenrePack` is retained — it's referenced under `TYPE_CHECKING` (type hints only)
- **Verification:** Confirm zero non-definition references for each symbol:
  ```bash
  grep -r "VisualStyle\|AudioConfig\|MixerSettings\|AIGenerationConfig\|ThemeFamily\|MoodTrack\|Variation\|PackMeta" sidequest_daemon/ tests/ --include="*.py"
  ```
  (Exclude genre/models.py definition lines)
- **Action:** Delete the dead symbol definitions, keep GenrePack definition and its TYPE_CHECKING usage

### Target 3: dispatch_request Image-Tier NotImplementedError Trap (sidequest_daemon/media/daemon.py:246)
- **Location:** `sidequest_daemon/media/daemon.py`, `dispatch_request()` function
- **Current state:** Music tier is fully wired; image tier raises `NotImplementedError`
- **Decision paths:**
  1. **Finish extraction:** Complete the image-tier wiring (inspect the spec, wire the handler, add tests)
  2. **Collapse branch:** Remove the image-tier branch entirely so the NotImplementedError trap doesn't trap future callers
- **Recommendation:** Collapse to remove the trap — the music tier is sufficient for current use
- **Action:** Remove the image-tier `elif` clause from dispatch_request; either handle it in the main flow or document that image requests are not yet routed

## Acceptance Criteria (from story YAML)
1. ✓ NullRenderer + Renderer ABC removed (confirmed zero importers first)
2. ✓ Confirmed-dead genre/models.py stubs removed; GenrePack retained if still TYPE_CHECKING-referenced
3. ✓ dispatch_request image-tier NotImplementedError trap resolved (extraction finished OR branch removed)
4. ✓ daemon-test + daemon-lint green after removals; no dangling imports

## Implementation Notes

### Pre-Deletion Verification Checklist
Before each deletion, run the grep command to confirm zero consumers:
- [ ] NullRenderer/Renderer ABC: `grep -r "NullRenderer\|from.*renderer.base import\|import.*renderer.base" sidequest_daemon tests`
- [ ] Each dead genre/models symbol: `grep -r "{symbol}" sidequest_daemon tests` (excluding definition lines)
- [ ] dispatch_request callers: `grep -r "dispatch_request" sidequest_daemon tests` (understand the call pattern)

### Testing Gate
After removals:
1. Run daemon test suite: `just daemon-test` or `cd sidequest-daemon && pytest`
2. Run linter: `just daemon-lint` or `cd sidequest-daemon && ruff check .`
3. Verify no import errors: `python -c "from sidequest_daemon import *"`

### Branch
- **Repo:** sidequest-daemon
- **Base:** origin/develop
- **Branch name:** feat/78-2-daemon-dead-export-sweep

## Sm Assessment

**Setup complete — routing to dev (implement phase).**

- **Scope is bounded and well-specified.** Three independent dead-export targets in `sidequest-daemon` only, sourced from a 2026-06-02 `sq-wire-it` audit. No cross-repo coupling, no engine/UI surface.
- **Trivial workflow is correct.** 3 pts, p3, mechanical deletion + one trap resolution. No design ambiguity that warrants TDD ceremony — the verify-before-delete grep checklist *is* the discipline here.
- **Dev's load-bearing obligation:** confirm zero consumers (including tests) *immediately before* each deletion — the audit is a day old and the tree can drift. Retain `GenrePack` (only TYPE_CHECKING-referenced). For target 3, the recommended path is collapsing the image-tier branch to remove the `NotImplementedError` trap rather than finishing an unscoped extraction.
- **Exit gate for implement:** `daemon-test` + `daemon-lint` green, no dangling imports.
- **No Jira key** — claim skipped intentionally (story has `jira: null`).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest_daemon/renderer/null.py` — DELETED (NullRenderer; zero importers incl. tests)
- `sidequest_daemon/renderer/base.py` — DELETED (Renderer ABC; only consumer was null.py)
- `sidequest_daemon/genre/models.py` — slimmed to `GenrePack`-only; removed the 8 dead sub-models
- `sidequest_daemon/media/daemon.py` — removed the `dispatch_request` image-tier `NotImplementedError` trap (lines ~246–251) + updated its docstring

**Verification before each deletion:**
- NullRenderer/Renderer ABC: only self-reference in null.py; the sole external mention of `Renderer` is a docstring word in `scene_interpreter.py`. Safe.
- 8 stub symbols: zero references outside `genre/models.py`. `GenrePack` is the only externally-referenced symbol — imported under `TYPE_CHECKING` in `scene_interpreter.py` (line 19) and used as the annotation `genre_pack: GenrePack | None` (line 331). `self._genre_pack` is assigned (line 336) but never read → no field access, so a minimal stub is sufficient.
- dispatch_request image branch: unreachable in production — `_handle_client` (line 513) only routes `tier in MUSIC_TIERS` to `dispatch_request`; image tiers are dispatched inline afterward. `IMAGE_TIERS` itself stays (5 other uses).

**Tests:** 371/371 passing (GREEN); ruff clean
**Branch:** feat/78-2-daemon-dead-export-sweep (pushed)

**Handoff:** To review (The Merovingian)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 371 pass, ruff clean, imports resolve, no dangling refs |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 0, dismissed 0, deferred 2 (both pre-existing, outside diff scope) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 0 dismissed, 2 deferred (both in unchanged code, recorded as non-blocking delivery findings)

## Reviewer Assessment

**Verdict:** APPROVED

A textbook dead-export sweep. Every deletion was justified by zero-consumer evidence, the tree was verified clean after each cut, and the result is 371 green tests + ruff clean + resolving imports. Cause traced to effect on every removed symbol.

**Data flow traced:** socket `render` request → `dispatch_request` → `tier=music` reaches `music_pipeline.generate()`; any non-music/non-image tier now raises `ValueError("Unknown tier")` loudly. The removed image-tier `NotImplementedError` branch was unreachable — `_handle_client` (daemon.py:513) only routes `tier in MUSIC_TIERS` here; image tiers dispatch inline. Removing it changes an unreachable `NotImplementedError` into the same loud `ValueError` fall-through. No silent fallback introduced (SOUL: No Silent Fallbacks — upheld).

**Pattern observed:** Tombstone docstring in `genre/models.py:1-9` names the removed sub-models — good institutional memory, the only residual mention of the deleted symbols and intentionally not code.

**Error handling:** `dispatch_request` still rejects non-`render` methods (`NotImplementedError`) and unknown tiers (`ValueError`) — both loud. Verified against test `test_dispatch_unknown_tier_still_raises_loudly`.

### Observations
- [VERIFIED] `renderer/null.py` + `renderer/base.py` deletion is safe — evidence: only `Renderer` mention outside the deleted files is a docstring word in `scene_interpreter.py:4`; zero imports of `renderer.base`/`NullRenderer` anywhere incl. tests (preflight grep + my own grep agree). Complies with No-Stubbing (removes dead code).
- [VERIFIED] `GenrePack` slim is safe — evidence: imported only under `TYPE_CHECKING` (scene_interpreter.py:19), annotated at line 331, stored at line 336 as `self._genre_pack` and never read. No field access exists, so a zero-field stub satisfies the lone consumer. Import smoke test passes (no NameError from removed default-value references).
- [VERIFIED] `IMAGE_TIERS` correctly retained — evidence: still used at daemon.py:383, 410, 630, 693; only the unreachable branch at the old line 246 was removed.
- [SEC] Pre-existing path-handling in the music branch (`daemon.py` music read of `params["json_params_path"]`) — **not introduced by this diff** (diff only touches the docstring + image branch; read line unchanged per `git diff`). Deferred as a non-blocking delivery finding for a future hardening story. Not a blocker for a dead-code sweep.
- [SEC] `GenrePack(extra="allow")` low-confidence deserialization note — `extra="allow"` was on the original `GenrePack` (develop:19) and is **preserved, not introduced**; the model is never instantiated (TYPE_CHECKING-only). Deferred as non-blocking; a `forbid`/`ignore` change is out of scope for this story and arguable either way.
- [EDGE] Specialist disabled via settings — no boundary-condition findings to incorporate.
- [SILENT] Specialist disabled via settings — but I independently verified no swallowed errors: both `dispatch_request` reject paths raise loudly.
- [TEST] Specialist disabled via settings — preflight confirms the existing suite (incl. `test_music_dispatch.py`) stays green; no test was deleted or weakened by this diff.
- [DOC] Specialist disabled via settings — I checked the touched docstrings myself: `models.py` and `dispatch_request` docstrings were both updated to match the new reality (no stale references).
- [TYPE] Specialist disabled via settings — I checked the one type-surface change: the `GenrePack` annotation in `scene_interpreter.py` still resolves under TYPE_CHECKING.
- [SIMPLE] Specialist disabled via settings — the diff *is* a simplification (195 deletions / 16 insertions); nothing added.
- [RULE] Specialist disabled via settings — I enumerated the applicable rules myself; see Rule Compliance below.

### Rule Compliance
- **No Silent Fallbacks:** `dispatch_request` — non-render → `NotImplementedError`; music → handled; unknown/image tier → `ValueError`. All loud. COMPLIANT.
- **No Stubbing (dead code is worse than no code):** The sweep *removes* dead code. The remaining `GenrePack` is not a dead-code shell — it is a live TYPE_CHECKING annotation target with a real consumer. COMPLIANT.
- **Verify Wiring, Not Just Existence:** Confirmed the remaining `GenrePack` has a real (type-level) consumer; confirmed deleted symbols had none. COMPLIANT.
- **Personal-project / no Jira:** No Jira references introduced. COMPLIANT.

### Devil's Advocate
Let me try to break this. Argument one: deleting the `Renderer` ABC removes the contract that future renderer backends were meant to implement — a maintainability regression disguised as cleanup. Rebuttal: the ABC had exactly one implementer (`NullRenderer`), which itself had zero consumers; the live image worker (`zimage_mlx_worker.py`) does not inherit from it. There is no production renderer that depended on this contract, so nothing structural is lost — if a backend interface is wanted later it can be reintroduced deliberately. Argument two: the `GenrePack` slim is a time bomb — some future caller will instantiate it expecting `.meta`/`.audio`/`.visual_style`/`.name` and get `AttributeError`. Rebuttal: that is true of *any* stub, and the docstring explicitly warns the model is annotation-only and never instantiated; the failure would be loud (`AttributeError`) and immediate, not silent corruption. The deviation is logged. Argument three: removing the image-tier `NotImplementedError` weakens a guardrail — a future dev who wires image dispatch through `dispatch_request` loses the explicit "not done yet" signal and gets a generic "Unknown tier" instead. This is the most credible concern. Rebuttal: the branch was a half-extraction trap (the story's explicit target), the `ValueError` is still loud and names the offending tier, and `IMAGE_TIERS` remains defined so a future dev re-adding the branch has the constant ready. The signal moves from "NotImplementedError with a stale Task-12 reference" to "Unknown tier" — arguably a wash, and the stale plan reference is correctly retired. Argument four: a malicious socket client sends `tier=music` with a traversal path. Real — but pre-existing and untouched by this diff; recorded as a follow-up. Nothing the devil raised blocks this sweep.

## Delivery Findings

No upstream findings at setup time.

### Dev (implementation)
- No upstream findings.

### Reviewer (code review)
- **Improvement** (non-blocking): The music-tier dispatch reads `params["json_params_path"]` and opens it before any allowlist/containment check (`daemon.py` music branch; `MusicPipeline.generate`). A socket client could supply an arbitrary filesystem path. Affects `sidequest_daemon/media/daemon.py` + `sidequest_daemon/media/music_pipeline.py` (validate the path is under `SIDEQUEST_GENRE_PACKS` before `read_text()`). Pre-existing — not introduced by 78-2; surfaced by reviewer-security. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `GenrePack(extra="allow")` is preserved from the original model but the slimmed stub is annotation-only; if it is ever instantiated with live data, `extra="forbid"` would align better with No Silent Fallbacks. Affects `sidequest_daemon/genre/models.py` (reconsider `extra=` policy when/if real fields return). Low confidence, pre-existing config. *Found by Reviewer during code review.*

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

### Dev (implementation)
- **Slimmed `GenrePack`'s body, not just the 8 sibling stubs**
  - Spec source: session Story Context, Target 2 ("Delete the dead symbol definitions, keep GenrePack definition and its TYPE_CHECKING usage")
  - Spec text: "keep GenrePack definition and its TYPE_CHECKING usage"
  - Implementation: Reduced `GenrePack` to `class GenrePack(BaseModel): model_config = ConfigDict(extra="allow")` — removed its `meta`/`audio`/`visual_style` fields and the `name` property
  - Rationale: `GenrePack`'s field annotations and *default values* instantiate `PackMeta()`/`AudioConfig()`/`VisualStyle()`, which transitively pull in all 8 stubs. Deleting the stubs while leaving `GenrePack` intact would raise `NameError` at class-definition (import) time. `GenrePack` is referenced only as a `TYPE_CHECKING` annotation and is never instantiated nor are its fields read (`self._genre_pack` is assigned but never accessed), so a minimal `extra="allow"` stub fully satisfies the lone consumer. The class name — the thing the spec says to keep — is preserved.
  - Severity: minor
  - Forward impact: minor — any future code that instantiates `GenrePack` and reads `.meta`/`.audio`/`.visual_style`/`.name` would need those fields reintroduced; none exists today.
  - → ✓ ACCEPTED by Reviewer: agrees with author reasoning. Deleting the 8 stubs forces the slim — `GenrePack`'s defaults instantiate them, so keeping the class name (what the spec actually requires) while dropping its now-orphaned fields is the only coherent way to honor "keep GenrePack." The class is TYPE_CHECKING-only and never instantiated; any future regression would fail loudly. Forward impact correctly bounded.

### Reviewer (audit)
- No undocumented deviations found. The only spec divergence (GenrePack slim) was logged by Dev and is accepted above. The image-tier branch removal and the two file deletions match the session Story Context targets exactly.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->