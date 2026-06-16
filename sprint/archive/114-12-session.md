---
story_id: "114-12"
jira_key: ""
epic: "114"
workflow: "trivial"
---
# Story 114-12: RECONCILIATION — rebase the stale feat/114-12 branches onto current develop, recover the missing deliverable, re-review, merge

## Story Details
- **ID:** 114-12
- **Jira Key:** (none — personal project, Jira skipped)
- **Workflow:** trivial (reconciliation — NO new tests; the existing 114-12 tests are the spec, the "implement" phase is the rebase)
- **Repos:** server, content
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish

## Why this story is reopened

114-12 was archived as `done`, but its two PRs were **never merged** — they were left as DRAFTs and the story was archived prematurely. The headline deliverable is genuinely **missing from develop**:
- `sidequest/cli/wn_equip_extract_core.py` (the DRY shared WN-extraction core) — **not in develop**, present only on the branch.
- `tests/cli/test_wn_equip_core.py` — **not in develop**, present only on the branch.

The branches cannot be merged as-is: they are 9 develop commits behind their merge-base (`2aad4dfa`, 2026-06-15 19:03 → develop HEAD `1c414152`), and those 9 commits include high-impact work the branches predate (see hotspots below). A blind merge would regress develop. This story rebases them current, re-reviews, and merges.

## Reconciliation plan (for Dev)

### Branches (already exist — do NOT create new ones)
- server: `feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction` (PR #893, DRAFT) — the REAL work
- content: `feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction` (PR #469, DRAFT) — a "tracking stub — no content changes"

### Server (#893) — the substantive rebase
1. `git fetch origin`, then rebase the branch onto `origin/develop`.
2. **Conflict hotspots (the 9 intervening commits):**
   - **ADR-147 honest-layering reparent (122-x):** develop MOVED `sidequest/foundation/{reference_anchors,reference_slug,slug_fold}.py` → `sidequest/server/`. The branch still has the OLD `foundation/` paths. Resolve by taking develop's reparented locations and re-applying any 114-12 edits there — do NOT resurrect `sidequest/foundation/` files.
   - **114-15 dogfight (#895):** develop added `sidequest/telemetry/spans/dogfight.py` + `ship_weapons:` in inventory. Do NOT drop these.
   - **Inventory model:** 114-14 / 120-x touched `sidequest/genre/models/inventory.py` and inventory.yaml — reconcile 114-12's CatalogItem field-population against develop's current model.
3. **PRESERVE through the rebase (114-12's actual deliverable):**
   - `sidequest/cli/wn_equip_extract_core.py` (DRY shared core)
   - parser wiring that populates `CatalogItem` dual-AC/soak + trauma-target + ranged `+N` damage bonus
   - `Path.resolve()` / argparse-choices hardening in both wwn + cwn extract tools
   - `tests/cli/test_wn_equip_core.py`
4. After rebase: run the FULL server suite via testing-runner — must be green on current develop. Force-push (`--force-with-lease`). Mark PR #893 **ready for review** (`gh pr ready 893`).

### Content (#469) — verify, likely close
1. The branch's only commit is "tracking stub — no content changes." Rebase onto `origin/develop`.
2. If after the rebase it carries **no real content changes** (only a `.session/` note), it has nothing to merge → recommend **CLOSING #469** (never merge a `.session` note into develop) and note it as a delivery finding. If it DOES carry real content, rebase + keep + mark ready.
3. Guard: the rebase must NOT revert develop's space_opera de-triplication (#466), 114-15 `ship_weapons`, or road_warrior 120-2 inventory work.

### Definition of Done
- Server branch rebased onto current develop, conflicts resolved, full server suite GREEN, force-pushed, PR #893 marked ready.
- No `sidequest/foundation/` files resurrected; no 114-15 dogfight/`ship_weapons` work dropped.
- Content #469 either rebased-and-ready (if real changes) or recommended-for-close (if stub-only), with the call documented.
- `wn_equip_extract_core.py` + `test_wn_equip_core.py` present and green on the rebased branch.

## Delivery Findings

No upstream findings yet.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (blocking — for DEVELOP'S health, not for 114-12): `origin/develop` is RED — **272 pre-existing test failures** from a hermeticity gap. New narrator paths (e.g. `build_unseeded_objective_classifier_llm` via `run_unseeded_objective_classifier_watcher`) construct the **real Anthropic SDK** (`build_async_anthropic()`) in tests that don't install the conftest fake. **Verified on untouched `origin/develop` (030f9afb)** — `tests/server/test_45_20_trope_resolution_wire.py` fails 10/10 there with zero 114-12 present. NOT caused by this rebase (HEAD differs from develop in only 5 `sidequest/cli/` files). With a developer `ANTHROPIC_API_KEY` set, these tests could **silently bill live API calls**. Needs its own fix story. Affects `tests/server/*` (install the SDK fake on the affected narrator-path tests, or extend `tests/server/conftest.py::_no_real_anthropic_sdk` to cover the new path). *Found by Dev during 114-12 reconciliation.*
- **Note** (non-blocking): content PR #469 closed as a no-op — its only diff was a `.session/` tracking note; all 114-12 work is server-side (#893). Content stub branch deleted. *Found by Dev during 114-12 reconciliation.*

### Reviewer (code review)
- **Improvement** (non-blocking — bundle into ONE follow-up, do NOT chain per-finding): the recovered 114-12 code carries a batch of LOW/MEDIUM polish, none correctness bugs:
  - [DOC][LOW] `tests/cli/test_wn_equip_core.py` still has RED-phase framing ("RED until 114-12 lands…" module docstring + "(→ RED.)" inline markers ~`:184`/`:224`). Story is done/green — same stale-RED class as 120-5/120-6. Refresh to GREEN.
  - [TEST][MEDIUM] `wwn_main`'s `Path.resolve()` error-message hardening (`wwn_equip_extract.py:105`) is untested at the assertion level — only `cwn_main` is covered; the pre-existing wwn test asserts only `rc != 0`. Add a parallel wwn test (or parametrize over `[cwn_main, wwn_main]`).
  - [TYPE][LOW] `sidequest/cli/wn_equip_extract_core.py:73` `slugify()` missing `-> str` return annotation (every sibling public fn has one).
  - [DOC][LOW] new public module `wn_equip_extract_core.py` has no `__all__` (16 public names; private regex constants would leak under `import *`).
  - [DOC][LOW] `data_rows` docstring says "Yield" but returns a `list` (`wn_equip_extract_core.py:89`).
  - [DOC][LOW] `wwn_equip_extract.py:44` TOOL_VERSION comment misattributes its pinning test (copy-paste from cwn; wwn is pinned by `tests/cli/test_wwn_equip_extract.py`).
  - [TEST][LOW] CLI stdout round-trip omits a `trauma_rating` spot-check (covered by the model_dump `==` test); WWN `bonus` has no subprocess-level round-trip; the positive argparse guard only covers `cwn_build_parser`.
  *Found by Reviewer during code review.*
- **Gap** (BLOCKING for DEVELOP'S health — reiterating Dev's finding as the team's #1 priority): develop is RED with **272 pre-existing failures** — real Anthropic SDK constructed in narrator-path tests without the conftest fake. **Independently reproduced by Reviewer:** `tests/server/test_45_20_trope_resolution_wire.py` fails 10/10 on untouched `origin/develop` (030f9afb). A dev with `ANTHROPIC_API_KEY` set could bill live API calls from the suite. Unrelated to 114-12, but a fire needing its own urgent fix story. *Confirmed by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **DoD "full server suite GREEN" cannot be literally satisfied — but for a reason external to 114-12**
  - Rationale: The rebase changes only 5 `sidequest/cli/` files (none touch the narrator/SDK/conftest); it is structurally impossible for it to have caused narrator-SDK failures, and direct verification on develop confirms they predate it. Blocking 114-12 on develop's own redness would be wrong.
  - Severity: minor (for 114-12) / the underlying develop redness is its own blocking finding
  - Forward impact: Reviewer should scope the green-check to 114-12's 5 files + the 57 deliverable tests, not the full suite; the develop-wide failure is tracked separately.

## Design Deviations

No design deviations yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **DoD "full server suite GREEN" cannot be literally satisfied — but for a reason external to 114-12**
  - Spec source: .session/114-12-session.md, Definition of Done
  - Spec text: "full server suite GREEN"
  - Implementation: 114-12's own deliverable is green (57/57 CLI extraction tests + ruff clean); the full suite shows 272 failures that are **pre-existing on develop** (hermeticity gap — see Delivery Findings), verified on untouched `origin/develop`.
  - Rationale: The rebase changes only 5 `sidequest/cli/` files (none touch the narrator/SDK/conftest); it is structurally impossible for it to have caused narrator-SDK failures, and direct verification on develop confirms they predate it. Blocking 114-12 on develop's own redness would be wrong.
  - Severity: minor (for 114-12) / the underlying develop redness is its own blocking finding
  - Forward impact: Reviewer should scope the green-check to 114-12's 5 files + the 57 deliverable tests, not the full suite; the develop-wide failure is tracked separately.

### Reviewer (audit)
- **Dev deviation — DoD "full server suite GREEN" not literally met (develop is pre-existing red)** → ✓ ACCEPTED by Reviewer: independently verified. HEAD differs from `origin/develop` in exactly 5 `sidequest/cli/` files (none touch narrator/SDK), and `tests/server/test_45_20_trope_resolution_wire.py` fails 10/10 on untouched `origin/develop` (030f9afb) — so the 272 failures are develop's, not 114-12's. Scoping the green-check to the 5-file diff + 57 deliverable tests is correct. No undocumented deviations in the diff.

## Sm Assessment

**Routing:** trivial workflow (phased) → handoff to **dev (Naomi)** for the `implement` phase, which here is a RECONCILIATION rebase, not new code.

**Why reopened (per Bossmang's "merge all the PRs" → option A):** 114-12 was archived `done` but its PRs #893 (server) / #469 (content) were never merged — both still DRAFT. Confirmed the deliverable is genuinely missing from develop: `sidequest/cli/wn_equip_extract_core.py` and `tests/cli/test_wn_equip_core.py` exist only on the branch. The branches are 9 develop-commits stale and would regress develop if merged blind, so they must be rebased current first.

**The danger Dev must respect (do NOT regress develop):**
- The ADR-147 honest-layering reparent moved `sidequest/foundation/* → sidequest/server/*`. The branch predates it and holds the OLD `foundation/` paths. Take develop's reparented locations; never resurrect `foundation/`.
- 114-15 added `dogfight.py` spans + `ship_weapons:`; do not drop them.
- content #469 is a "no content changes" stub — likely a clean CLOSE after rebase (don't merge a `.session` note), but Dev verifies.

**This is risky merge-reconciliation work, not a trivial edit** — the "trivial" workflow is only the phase shape (no new tests needed; existing 114-12 tests are the spec). Reviewer must scrutinize the rebased diff hard for resurrection/regression of the reparent and 114-15 work.

**Branches already exist** in both repos (`feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction`) — Dev rebases them, does NOT cut new ones.

**Jira:** none. **DoD:** see the reconciliation plan above. **No new blockers** beyond the rebase conflicts themselves.

## Dev Assessment

**Implementation Complete:** Yes (reconciliation rebase)

**What happened:**
- **Server #893 — rebased clean onto current develop.** The branch's 2 commits replayed with **0 conflicts**. Why it was painless despite the scary `develop..branch` diff: 114-12's *real* changeset is only 5 files (`sidequest/cli/wn_equip_extract_core.py` [NEW], the cwn/wwn extract CLIs refactored onto the core, `tests/cli/test_wn_equip_core.py` [NEW], one fixture) — and **none** of those 5 were touched by develop's 9 intervening commits. The huge prior diff was all develop's drift (honest-layering `server/→foundation/` reparent, 114-15 dogfight) on files 114-12 never touches. Post-rebase, `git diff origin/develop..HEAD` = **exactly those 5 files** — no `foundation/` resurrection, no dropped dogfight/`ship_weapons`, confirmed.
- **Deliverable recovered:** `sidequest/cli/wn_equip_extract_core.py` + `tests/cli/test_wn_equip_core.py` are now on a develop-current branch.
- **Force-pushed** (`--force-with-lease`, `d05f5738 → a0c665d4`); **PR #893 marked ready** (no longer draft).
- **Content #469 — closed** as a no-op (only a `.session/` note; commit literally "no content changes"). Stub remote+local branches deleted.

**Files Changed (server #893 vs develop):**
- `sidequest/cli/wn_equip_extract_core.py` (NEW — DRY shared WN-extraction core)
- `sidequest/cli/cwn_equip_extract/cwn_equip_extract.py`, `sidequest/cli/wwn_equip_extract/wwn_equip_extract.py` (refactored onto the core; argparse/Path.resolve hardening)
- `tests/cli/test_wn_equip_core.py` (NEW)
- `tests/fixtures/cwn_srd/equipment_chapter.txt` (fixture)

**Tests:** 114-12 deliverable **57/57 GREEN** (`test_wn_equip_core` + `test_wwn_equip_extract` + `test_cwn_equip_extract`); ruff clean on all changed files. Full suite is red (272) but that is **pre-existing develop debt**, verified on untouched develop — see Delivery Findings + Design Deviations.

**Branch:** feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction (server, base develop, rebased+pushed). PR #893 ready.

**Handoff:** To review (Chrisjen Avasarala / Reviewer). Reviewer: scope the green-check to the 5-file 114-12 diff + 57 deliverable tests; the full-suite redness is develop's, tracked as a separate blocking finding.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 57/57 GREEN, lint+format clean, 0 smells (its "11 files" was stale *local* develop; authoritative vs origin/develop = 5) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (1 med, 3 low) | all confirmed non-blocking → bundled follow-up |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 ([DOC], high-conf / low-sev) | all confirmed non-blocking → bundled follow-up |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (slugify annot, missing __all__, wwn test gap — low/med) | all confirmed non-blocking → bundled follow-up |

**All received:** Yes (4 enabled returned, 5 disabled skipped)
**Total findings:** 0 blocking for 114-12; 1 BLOCKING for develop-health (separate fire, reiterated); ~8 distinct non-blocking polish items (bundled into one recommended follow-up); 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

A reconciliation that recovers a genuinely-lost deliverable (`wn_equip_extract_core.py` + tests) cleanly onto current develop. The rebase is surgical, the deliverable is green, and every code finding is Low/Medium polish — none Critical/High. The one blocking-severity finding (272 develop failures) is **develop's pre-existing debt, not 114-12's**, independently verified, and is tracked as a separate fire.

**Rebase integrity (my own verification):** `git diff --name-only origin/develop..HEAD` = **exactly the 5 deliverable files**; `--diff-filter=D` shows **zero** develop files dropped; the ADR-147 reparented `foundation/` files are identical on HEAD and develop (3=3). No resurrection, no regression. The scary pre-rebase `+1491/-3278` diff was entirely develop's drift on files 114-12 never touches.

**Data flow traced:** SRD chapter text → `extract_catalog()` (the new DRY core) → `CatalogItem`/`DamageSpec` with verbatim dual-AC/soak + trauma-target + ranged `+N` bonus → `model_dump()` → JSON stdout. Round-trip verified by `test_new_field_items_survive_model_dump_roundtrip` (pydantic `==` over every item) + the CWN subprocess JSON round-trip. Safe — fail-loud on malformed rows (`row_context` re-raises with context), no silent fallbacks.

### Observations

- [VERIFIED] Rebase landed exactly the deliverable — evidence: `origin/develop..HEAD` = 5 files, 0 deletions, `foundation/` identical to develop. The reconciliation's core goal (recover the lost `wn_equip_extract_core.py` without regressing develop) is met.
- [VERIFIED] Develop-red is pre-existing, not 114-12 — evidence: I ran `tests/server/test_45_20_trope_resolution_wire.py` on detached `origin/develop` (030f9afb, zero 114-12) → 10/10 FAIL. Confirms Dev's attribution; the deductive argument (5 CLI-only files can't touch narrator/SDK) holds empirically.
- [TEST] reviewer-test-analyzer + [RULE] reviewer-rule-checker both flag the **wwn `Path.resolve()` hardening is untested at assertion level** (`wwn_equip_extract.py:105` shipped; only `cwn_main` covered) — [MEDIUM], confirmed, non-blocking (the code is present and mirrors the tested cwn path; it's a coverage asymmetry, not a defect). Bundled.
- [DOC] reviewer-comment-analyzer: **stale RED-phase framing in `test_wn_equip_core.py`** (module docstring + `(→ RED.)` markers) — [DOC][LOW], the exact class fixed in 120-5/120-6. Plus a "Yield"→returns-list docstring and a copy-paste TOOL_VERSION misattribution. Confirmed, non-blocking, bundled.
- [TYPE] reviewer-rule-checker: `slugify()` missing `-> str` and the new public module missing `__all__` — [LOW] hygiene. Confirmed, bundled.
- [RULE] Path handling (#5) and input validation (#11) — the story's actual security hardening — PASS: `Path(args.srd_path).resolve()` is called BEFORE `is_file()` (CWE-59), `read_text(encoding="utf-8")` (no bare open, CWE-838), argparse `choices=` on `--srd`/`--license`. Verified by rule-checker with line cites.
- [SILENT] No silent fallbacks: malformed SRD rows raise `ValueError` with row context (`row_context`), CLI boundary re-raises to stderr + `return 1`. The deliberate `noqa:BLE001` is the legitimate CLI-surface boundary pattern, not buried swallowing.
- [SEC] / [SIMPLE] / [EDGE] — specialists disabled via settings. Self-assessed: the CLIs read local SRD files (operator-supplied, not a network/tenant boundary); no injection/secret/tenant surface; the DRY refactor *reduces* duplication (the whole point) — no over-engineering.

### Rule Compliance

Python lang-review (13) + project rules, against the 5-file diff (rule-checker corroborated, 3 low/med findings, 0 blocking):
- **#5 Path handling** — PASS: `Path(...).resolve()` before `is_file()` in both CLIs (`cwn:183`/`wwn:105`); `read_text(encoding="utf-8")`. The story's headline hardening, verified correct.
- **#11 Input validation** — PASS: argparse `required=True`, `choices=WN_SRD_CHOICES`/`WN_LICENSE_CHOICES` on both parsers; negative tests assert rejection.
- **#7 Resource leaks** — PASS: `Path.read_text()` (context-managed), no bare `open()`.
- **#1 Silent exceptions** — PASS: `row_context` re-raises `from e`; CLI boundary surfaces to stderr.
- **#8 Unsafe deserialization** — PASS: `json.dumps` (serialize) only; `json.loads` is test-only on controlled subprocess stdout.
- **#3 Type annotations** — 1 LOW gap (`slugify` missing `-> str`); all other public fns annotated. Non-blocking, bundled.
- **#10 Import hygiene** — 1 LOW gap (no `__all__` on the new public module). No star/circular imports. Non-blocking, bundled.
- **#6 Test quality** — strong (field-level round-trip via pydantic `==`, fail-loud negatives, parametrized over both CLIs); 1 MEDIUM coverage asymmetry (wwn Path.resolve untested). Non-blocking, bundled.
- **#13 Fix-regressions** — PASS: the fixture's added Soak/Trauma columns preserve value/weight positions; pre-existing cwn/wwn tests' count/provenance assertions still hold (rule-checker verified). TOOL_VERSION pins unchanged.
- #2,#4,#9,#12 — no applicable surface (no mutable defaults, offline CLI = no runtime logging subsystem, no async, no dep changes). PASS.

### Devil's Advocate

The dangerous failure mode for a reconciliation is a *silent regression* — the rebase quietly drops or reverts develop's newer work while looking clean. So I attacked that first and hardest. Could the rebase have reverted the ADR-147 honest-layering reparent (the branch predates it and held the old `sidequest/server/` copies of pure-logic modules)? No: `git ls-tree` shows HEAD has the reparented files at `foundation/` exactly as develop does (3=3), `--diff-filter=D` shows zero deletions vs develop, and the authoritative `origin/develop..HEAD` is exactly 5 `sidequest/cli/` files. A branch that touches only the equipment-extraction CLI subsystem cannot, by construction, revert reference-slug reparenting or drop dogfight spans — and the file-level diff proves it didn't. The "preflight saw 11 files" scare resolved to a stale *local* `develop` ref, not a real extra-file problem.

Second attack: is the green I'm trusting actually meaningful, or vacuous? The 57 deliverable tests aren't structure-only — the round-trip test reconstructs every item via `CatalogItem(**dump)` and asserts pydantic `==`, which catches a dropped or defaulted `trauma_rating` even though the CLI spot-check omits it. The negative tests have concrete fail conditions (malformed bonus → ValueError with row name; bad `--srd` → SystemExit). This is honest coverage.

Third, the uncomfortable one: am I rubber-stamping a story just because it was "approved before"? No — I re-derived every claim. But I also have to be honest that I'm shipping a [MEDIUM] coverage gap (wwn Path.resolve untested) and a fresh batch of stale-RED markers into develop. Are those really non-blocking? By the severity rubric and my own consistent 120-5/6 precedent, yes: stale RED markers are [DOC][LOW], an untested-but-present mirror of a tested path is [MEDIUM]. Neither is a correctness defect. The right disposition is approve-and-bundle, not block-the-recovery — but I'm logging them loudly enough that they can't hide, and recommending a *single* follow-up so we don't spawn a per-finding chain.

The real fire isn't in this diff at all: **develop is red, 272 tests, with a hermeticity hole that can bill live API calls.** That deserves more urgency than 114-12's polish. I've reproduced it independently and flagged it blocking for the team. Approving 114-12 doesn't worsen it (114-12's 5 files are green); merging recovers a lost deliverable. Approved.

**Handoff:** To SM (Camina Drummer) for finish-story.