---
story_id: "104-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 104-1: M-A — Server multi-system flag from systems/ presence (retire region-count cluster heuristic)

## Story Details
- **ID:** 104-1
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p2
- **Branch Strategy:** gitflow (feat/104-1-server-multi-system-flag)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-11T09:56:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-11T09:27:13Z | 2026-06-11T09:30:05Z | 2m 52s |
| red | 2026-06-11T09:30:05Z | 2026-06-11T09:43:01Z | 12m 56s |
| green | 2026-06-11T09:43:01Z | 2026-06-11T09:48:41Z | 5m 40s |
| review | 2026-06-11T09:48:41Z | 2026-06-11T09:56:00Z | 7m 19s |
| finish | 2026-06-11T09:56:00Z | - | - |

## Technical Approach

### Overview
This story implements an explicit boolean flag (`is_cluster` or `multi_system`) on the server-side cartography and reference-projection payloads. The flag is true when a world has a `systems/` directory or a sector graph, false otherwise. This replaces the client-side heuristic `regionCount > 1` which incorrectly classified single-system worlds (like `coyote_star` and `aureate_span`) as clusters.

### Context
- **Spec Reference:** 2026-06-11-space-opera-map-playtest-addendum.md §5 Story M-A
- **Problem:** The existing heuristic treats multi-region worlds (like 8-region `coyote_star`) as clusters because they have multiple entries in cartography—but `coyote_star` is a single system with 8 orbital bodies, not a multi-system cluster. Only `perseus_cloud` has a `systems/` directory.
- **Load-bearing fact:** Story 104-2 (UI) depends on this flag being set and accurate; 104-2 cannot proceed until the server emits the flag.

### Implementation Scope
1. **Cartography Payload:** Add `is_cluster` / `multi_system` boolean to the cartography response (worldstate projection).
2. **Reference Projection:** Add the same flag to `build_lore_map_section` output in `reference_projection.py` (around line 527).
3. **Signal Detection:** Check for `systems/` directory in the loaded world's genre pack structure, or check for a sector graph.
4. **OTEL Instrumentation:** Emit a span during the flag decision with fields: world name, signal source (systems/ present?), result.
5. **No Silent Fallback:** Absence of `systems/` is a definite single-system signal, not an unknown—no guessing.

### Files to Modify
- **Server core:** Cartography builder, worldstate projections
- **Server reference:** `reference_projection.py` (build_lore_map_section)
- **Telemetry:** Add OTEL span for cluster detection decision
- **Tests:** Unit test the flag detection logic; integration test cartography/reference payloads include the flag

### Acceptance Criteria
1. **AC1:** Server sets an explicit boolean (named `is_cluster` or `multi_system`) on the cartography payload and the reference projection's map section, true iff the world has a `systems/` dir or sector graph. `perseus_cloud` → true; `coyote_star`, `aureate_span` → false.
2. **AC2:** OTEL span on the decision logs: world, signal source (`systems/` present?), and result.
3. **AC3:** The flag is authoritative and supersedes the client `regionCount > 1` heuristic (story 104-2 will read only this flag).
4. **AC4:** No silent fallback—absence of `systems/` is a definite single-system, never an "unknown."

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The operator's unified model (2026-06-11) wants coyote_star and aureate_span each given a one-entry `systems/` file so every space-opera world has the same structure ("treat everything the same"; adding a 2nd entry later flips a world to cluster with zero code change). This is a CONTENT change in a separate story (104-1 is server-only). It does NOT change today's flag truth — both worlds read `is_cluster=False` before and after — so the server flag is correct without it. Affects `sidequest-content/genre_packs/space_opera/worlds/{coyote_star,aureate_span}/systems/` (add one-entry system file each). *Found by TEA during test design.*
- **Improvement** (non-blocking): The real-world truth table (perseus_cloud→cluster, coyote_star/aureate_span→single) is a CONTENT invariant — per project rule it belongs in the pack validator, not a unit test. Recommend a validator check asserting each space-opera world's detected `is_cluster` matches its intended topology. Affects the content pack validator. *Found by TEA during test design.*
- **Question** (non-blocking): perseus_cloud's `systems/` dir holds only `yula.yaml` (other systems are Diamonds-and-Coal, regenerable from `perseus_cloud.sector.json`). The tests pin that the system COUNT comes from the sector graph's `system` node dict when present, falling back to `systems/*.yaml` file count, else 1. Confirm Dev wires detection to read the sector graph `*.sector.json` (not just `systems/` file count) — the paranoid test `test_cluster_count_comes_from_sector_graph_not_systems_file_count` enforces this. *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): Detection exceptions (`ValueError` on a malformed `system` dict; unguarded `OSError`/`json.JSONDecodeError` from reading `*.sector.json`) propagate untyped through `_load_subdirectories:396`, breaking the loader's pervasive `GenreLoadError` contract. Loud, not silent; no current content triggers it (only perseus's well-formed sector.json exists). Affects `sidequest/genre/cluster_detection.py` (guard `read_text`/`json.loads`) + `sidequest/genre/loader.py:1570` (wrap `detect_is_cluster` in `GenreLoadError`, per the stocks-block precedent at 1558-1563). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Loader→`World.is_cluster` caching link is not directly asserted by a test (in-game payload tests stub `World` via `SimpleNamespace`). Affects `sidequest-server/tests/server/test_multi_system_cluster_flag.py` (add a loader test asserting `World.is_cluster` from a fixture world dir with a 2-node sector graph). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `world_dir` reaches the glob without `Path.resolve()` + a content-root containment check (CWE-59 symlink traversal); URL slug is regex-guarded so the only vector is an operator-planted symlink (self-attack, personal project). Affects `sidequest/server/reference_routes.py:67` / `sidequest/genre/cluster_detection.py:57`. *Found by Reviewer during code review.*

### Dev (implementation)
- Resolved TEA's Question: detection reads the sector graph first (`_sector_graph_system_count` counts the `*.sector.json` `system` node dict), then `systems/` entries, then a definite single — `test_cluster_count_comes_from_sector_graph_not_systems_file_count` is green. No new upstream findings. TEA's content-sibling Improvements still stand as follow-ups (one-entry `systems/` files + validator truth-table check) — not blockers; today's flag is correct without them. *Found by Dev during implementation.*

## Design Deviations

No deviations at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Detection signal is system COUNT, not `systems/` dir presence**
  - Spec source: 2026-06-11-space-opera-map-playtest-addendum.md §5 Story M-A, AC1
  - Spec text: "Server sets an explicit boolean … **true iff** the world has a `systems/` dir (or a sector graph)."
  - Implementation: Tests pin `is_cluster := system_count > 1`. Count precedence: sector-graph `system` nodes if a `*.sector.json` is present, else `systems/*.yaml` entry count, else 1.
  - Rationale: Operator design call (2026-06-11, this conversation): give coyote_star/aureate_span a one-entry `systems/` file so every world has the same structure. Under that model *every* world has a `systems/` dir, so mere presence can no longer distinguish single from cluster — count must. This also fixes a latent bug: perseus_cloud's `systems/` dir is sparse (only `yula.yaml`), so a presence/file-count signal would misread it.
  - Severity: minor
  - Forward impact: 104-2 (UI) reads `is_cluster` and is unaffected by how the server derives it. The wire field name is locked as `is_cluster` (matches `MapWidget.tsx:97`). Content sibling story (one-entry `systems/` files) is logged under Delivery Findings.

### Reviewer (audit)
- **Detection signal is system COUNT, not `systems/` dir presence** → ✓ ACCEPTED by Reviewer: sound operator design call. Count-based detection is strictly more correct than the spec's literal "presence" rule — I verified perseus_cloud's `systems/` dir is sparse (only `yula.yaml`) while its sector graph declares 34 systems, so a presence/file-count signal *would* have misread perseus. Count from the sector graph (authoritative when present) is the right precedence. The wire field name `is_cluster` is correctly locked for 104-2. No undocumented deviations found.

## Sm Assessment

Setup complete and ready for RED phase. Story 104-1 is well-scoped, server-only, 3 points, no blocking dependencies (`depends_on: null`). The technical approach is grounded directly in the spec (2026-06-11-space-opera-map-playtest-addendum.md §5 Story M-A) and the four ACs map cleanly onto the spec's requirements.

**Routing decision:** Hand off to TEA (O'Brien) for the RED phase. This is a backend mechanical-decision story — exactly the kind that demands OTEL coverage per the project's observability principle, and the spec already calls for an OTEL span on the cluster decision (AC2). TEA must write failing tests that pin all four ACs:
1. Flag-true for `perseus_cloud` (has `systems/`), flag-false for `coyote_star` and `aureate_span` (no `systems/`) — on **both** the cartography payload and the reference projection's map section.
2. OTEL span asserts world + signal-source + result fields.
3. No silent fallback — absence of `systems/` resolves to a definite single-system, never "unknown."

**Watch-out for downstream agents:** This blocks 104-2 (UI cluster detection). The flag name and payload shape are a contract — 104-2 reads only this flag, retiring the `regionCount > 1` heuristic. Lock the field name (`is_cluster` vs `multi_system`) in the RED phase so the UI story has a stable target.

**Coordination note:** Session file was created under `sprint/.session/` by setup and relocated to repo-root `.session/` where the handoff CLI reads it.
## TEA Assessment

**Tests Required:** Yes
**Reason:** Server behavior change with an observable contract (two payloads + OTEL span) — exactly what TDD pins.

**Test Files:**
- `sidequest-server/tests/server/test_multi_system_cluster_flag.py` — 10 tests across all 4 ACs.

**Tests Written:** 10 tests covering 4 ACs
**Status:** RED (all 10 failing, no collection/import errors — verified via testing-runner, run `104-1-tea-red`)

### Contract pinned (the seam Dev implements)

- **`is_cluster := system_count > 1`** (bool). Count precedence: sector-graph `system` nodes (`*.sector.json`) → else `systems/*.yaml` entry count → else 1.
- Wire field name **`is_cluster`** on BOTH payloads (locked for 104-2):
  - in-game MAP_UPDATE `cartography` dict (`_build_cartography_map_message`, `session_helpers.py`) — read from a loader-cached `World.is_cluster`.
  - reference lore `map` section (`build_lore_map_section` gains an `is_cluster=` kwarg; `build_lore_projection` detects on disk via `world_dir` and passes it).
- **Decision span** `sidequest.cartography.cluster_detected` with attrs `world`, `signal_source` (`sector_graph`|`systems_dir`|`none`), `system_count`, `is_cluster`. Fires on BOTH the cluster and single decisions (no silent skip on the common case).
- Recommended seam: one `detect_is_cluster(world_dir: Path) -> bool` helper (emits the span); the loader calls it (caches `World.is_cluster` for the in-game path), the session-free reference projection calls it directly.

### AC → test map

| AC | Test(s) |
|----|---------|
| AC1 flag true/false on payloads, keyed on count | `test_cluster_flag_true_for_multi_system_sector_graph`, `test_cluster_flag_false_for_single_entry_systems_dir`, `test_build_lore_map_section_carries_is_cluster_directly`, `test_ingame_cartography_payload_carries_is_cluster_true`, `test_ingame_cartography_payload_carries_is_cluster_false` |
| AC2 OTEL decision span (world, signal source, result) | `test_cluster_decision_emits_otel_span`, `test_cluster_decision_span_records_single_system` |
| AC3 supersedes `regionCount>1` (flag on in-game payload) | `test_ingame_cartography_payload_carries_is_cluster_true/false` |
| AC4 no silent fallback (definite single, never unknown) | `test_cluster_flag_false_when_no_systems_and_no_sector`, `test_ingame_payload_is_cluster_is_always_a_bool_never_missing` |
| Paranoid (perseus trap: count from sector graph, not file count) | `test_cluster_count_comes_from_sector_graph_not_systems_file_count` |

### Rule Coverage (.pennyfarthing/gates/lang-review/python.md)

| Rule | Coverage | Status |
|------|----------|--------|
| #1 silent exception swallowing | AC4 tests enforce explicit `False`, never None/missing/unknown — the behavioral analog of no-silent-swallow | failing (RED) |
| #3 type annotations at boundaries | Dev must annotate `detect_is_cluster(world_dir: Path) -> bool` and the new kwarg — not unit-testable; flagged for Dev | n/a |
| #5 path handling | Dev reads `*.sector.json` / `systems/` via `pathlib` + `encoding=` — flagged for Dev; fixtures already write with `encoding="utf-8"` | n/a |
| #6 test quality | Self-checked: every test asserts a specific value (`is True/False`, `== 3`, `in`, `isinstance`); no `assert True`, no bare-truthy-on-wrong-value, no skips | clean |
| #8 unsafe deserialization | Dev: count `systems/` files (no parse needed); parse `*.sector.json` with `json` (safe). If any YAML is loaded, SafeLoader only | n/a (flagged) |

**Rules checked:** 5 of 9 applicable lang-review rules considered; #1/#6 have behavioral coverage, #3/#5/#8 flagged for Dev (implementation-shape, not behaviorally testable here).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Julia) for GREEN.
### Dev (implementation)
- No deviations from spec. Implemented exactly to TEA's pinned contract (the count-vs-presence detection refinement is already logged above under `### TEA (test design)`; I followed it, did not introduce a new deviation).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/genre/cluster_detection.py` (NEW) — `detect_is_cluster(world_dir)` + `detect_system_count`; count precedence sector-graph → systems/ → definite-single; emits the decision span.
- `sidequest/telemetry/spans/cartography_map.py` — new `SPAN_CARTOGRAPHY_CLUSTER_DETECTED` (`sidequest.cartography.cluster_detected`), routed in `SPAN_ROUTES`, + `cluster_detected_span` ctx manager.
- `sidequest/genre/models/pack.py` — `World.is_cluster: bool = False` field.
- `sidequest/genre/loader.py` — computes `is_cluster=detect_is_cluster(world_path)` at load, passes to `World(...)`.
- `sidequest/server/session_helpers.py` — in-game MAP_UPDATE `cartography` dict carries `is_cluster` (from the loader-cached World flag).
- `sidequest/server/reference_projection.py` — `build_lore_map_section` gains `is_cluster=` kwarg; `build_lore_projection` detects on disk via `world_dir` and passes it.

**Tests:** 22/22 passing (GREEN) — 10 new (`test_multi_system_cluster_flag.py`) + 12 regression (routing-completeness, cartography_map_emit, reference_projection). Also `tests/genre/ -k "load or world"`: 290 passed, 0 failed (loader hot-path safe). Ruff clean on all changed files.

**Wiring:** End-to-end on both surfaces — loader → `World.is_cluster` → in-game MAP_UPDATE payload; `build_lore_projection` → disk detection → reference map section. Decision span routed to the GM panel (routing-completeness test green).

**Branch:** feat/104-1-server-multi-system-flag (pushed)

**Handoff:** To Reviewer (The Thought Police) for code review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells, 22/22 green | N/A (confirmed clean) |
| 2 | reviewer-edge-hunter | Yes | findings | 9 | confirmed 4 (1 H→downgraded M, 3 M/L), dismissed 3, deferred 2 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer (see Devil's Advocate) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer (see Rule Compliance #6 + test-wiring finding) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer read all docstrings; accurate, no stale comments |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer (see Rule Compliance #3) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 (LOW) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — Reviewer: clean detect_system_count/detect_is_cluster split, no over-engineering |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Reviewer ran the lang-review enumeration manually (see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, assessed by Reviewer)
**Total findings:** 2 confirmed-Medium, 2 confirmed-Low, 3 dismissed, 2 deferred — 0 Critical/High

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md + CLAUDE.md)

- **#1 silent exception swallowing** — COMPLIANT. No bare `except`, no `except: pass`. Every failure path raises loud: `_sector_graph_system_count` raises `ValueError` on a missing `system` dict; `detect_system_count` returns an explicit `(1, "none")` for the no-signal case (documented, not swallowed). Note: error *type* consistency gap recorded as [EDGE] M-1 (untyped vs `GenreLoadError`) — loud, not silent.
- **#3 type annotations at boundaries** — COMPLIANT. `detect_is_cluster(world_dir: Path) -> bool`, `detect_system_count(world_dir: Path) -> tuple[int, str]`, `_sector_graph_system_count(...) -> int | None`, `_systems_dir_entry_count(...) -> int | None`, `cluster_detected_span(*, world: str, signal_source: str, system_count: int, is_cluster: bool)`, `build_lore_map_section(..., is_cluster: bool = False)`, `World.is_cluster: bool`. All annotated. pyright clean (preflight).
- **#5 path handling** — MOSTLY COMPLIANT. `pathlib.Path` throughout; `read_text(encoding="utf-8")` present (no bare `open`). One gap: no `Path.resolve()` + containment before glob ([SEC] L-1, CWE-59, self-attack only).
- **#6 test quality** — COMPLIANT. All 10 new tests assert specific values (`is True/False`, `== 3`, `in`, `isinstance`); no `assert True`, no vacuous truthy, no skips. Gap: loader→`World.is_cluster` link not directly asserted (in-game tests stub `World` via SimpleNamespace) — [TEST] M-2, non-blocking.
- **#8 unsafe deserialization** — COMPLIANT. `json.loads` (not `yaml.load`) on the trusted, author-controlled content repo; structure validated (`isinstance(systems, dict)` or raise). `systems/` counted via glob, not parsed.
- **CLAUDE.md No Silent Fallbacks** — COMPLIANT (loud on every failure path).
- **CLAUDE.md OTEL principle** — COMPLIANT. `sidequest.cartography.cluster_detected` span fires on every decision (cluster AND single), routed in `SPAN_ROUTES`, routing-completeness test green.
- **CLAUDE.md No Source-Text Wiring Tests** — COMPLIANT. Tests drive real builders/projection + assert span via `otel_capture`; no `read_text()` source-grep assertions.

### Devil's Advocate

Argue the code is broken. **Loader hot path.** `detect_is_cluster(world_path)` now runs on EVERY world load of EVERY pack — it globs `*.sector.json` and, when one exists, parses the whole file (perseus's is 195 KB) just to `len(data["system"])`. A truncated write, a bad-permission file, or non-UTF-8 bytes raises `OSError`/`json.JSONDecodeError` — neither is `ValueError`, neither is wrapped in `GenreLoadError`, and `_load_subdirectories:396` calls the world loader with no try/except. So one corrupt sector graph crashes the entire pack load with a raw traceback instead of the structured diagnostic every other loader failure produces. A malicious or careless author who commits `system: {}` gets `is_cluster=False` (0 > 1) — a *present, authoritative* sector graph silently classified single, the exact "looks single but isn't" bug this story set out to kill, reincarnated one layer down. Two `*.sector.json` files → first-wins silently, no warning on the span. A symlink under `worlds/` is followed without `.resolve()` (CWE-59), though the URL slug is regex-guarded so only the operator can plant one. **What a confused user misunderstands:** an author adds `systems/README.yaml` and tips a single-system world's count; or authors perseus's other 33 orrery files into `systems/` and is surprised the count still comes from the sector graph (precedence is documented but not obvious). **Mitigations that hold:** I verified the *only* sector.json in all content (perseus, 34 systems) is well-formed → no crash today; both detection call sites run only AFTER their caller has already read files from `world_dir` (cartography loaded; a dozen world files loaded), so the "nonexistent world_dir" path is unreachable; `is_cluster` is a bool, no info leak; the json source is the trusted content repo, not user upload. Net: the failure modes are real but (a) loud, (b) untriggerable by current content, (c) refinements to error-*type* and robustness, not correctness or silent-fallback violations. None rises to High.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** world directory on disk → `detect_is_cluster(world_dir)` (count: sector-graph `system` nodes → `systems/*.yaml` count → definite 1) → `is_cluster: bool`. Two destinations: (1) loader caches it on `World.is_cluster` → in-game `_build_cartography_map_message` `cartography.is_cluster` → MAP_UPDATE wire; (2) session-free `build_lore_projection` re-detects on disk → reference lore `map` section `is_cluster`. Both supersede the UI `regionCount > 1` heuristic (104-2/M-B reads this flag). Safe: bool only, trusted content source, decision span on every path.

**Findings (all non-blocking — 0 Critical/High):**

| Severity | Tag | Issue | Location | Recommendation |
|----------|-----|-------|----------|----------------|
| [MEDIUM] | [EDGE] | Detection exceptions (`ValueError` on bad `system` dict; unguarded `OSError`/`JSONDecodeError` from `read_text`/`json.loads`) propagate untyped through `_load_subdirectories:396`, breaking the loader's pervasive `GenreLoadError` contract. Loud, not silent; no current content triggers it (only perseus's sector.json exists, well-formed). | `cluster_detection.py:63,69`; `loader.py:1570` | Wrap the `detect_is_cluster(world_path)` call (and the `read_text`/`json.loads`) in `GenreLoadError`, matching the stocks-block precedent at `loader.py:1558-1563`. |
| [MEDIUM] | [TEST] | Loader→`World.is_cluster` caching link not directly asserted — in-game payload tests stub `World` via `SimpleNamespace`, so deleting `is_cluster=is_cluster` at `loader.py` would not fail any test. Reference path IS wired end-to-end (disk→projection→section). | `tests/server/test_multi_system_cluster_flag.py` | Add a loader test: build a fixture world dir with a 2-node sector graph, load it, assert `World.is_cluster is True`. |
| [LOW] | [SEC] | `world_dir` reaches `glob` without `Path.resolve()` + containment check (CWE-59 symlink traversal). URL slug is regex-guarded (`_SAFE_SLUG`); only an operator-planted filesystem symlink could exploit it — self-attack on a single-operator personal project. | `reference_routes.py:67`, `cluster_detection.py:57` | `resolve()` + assert under content root, or document the fail-loud intent. |
| [LOW] | [EDGE] | A present sector graph with `system: {}` → count 0 → `is_cluster=False` (single), silently — a present authoritative source mapping to single without a loud signal. No content triggers it. | `cluster_detection.py:71` | Optional: raise on count 0 from a present sector graph, or document 0→single. |

**Dismissed:** (1) nonexistent `world_dir` → `(1,"none")` — unreachable: both call sites run only after their caller has read files from that dir. (2) `systems/*.yaml` broad glob counting `README.yaml` — content convention, the pack-validator's job per CLAUDE.md, not a code bug. (3) span-not-emitted-on-detection-error — minor; the error itself is loud.

**Deferred:** multiple `*.sector.json` first-wins warning, and the count==0 guard — both fold naturally into the [EDGE] M-1 error-handling fast-follow.

**Subagent tags:** [EDGE] confirmed (4); [SEC] confirmed (1, low); [TEST] Reviewer-assessed (subagent disabled); [SILENT] Reviewer-assessed — no silent fallbacks, all paths loud; [DOC] Reviewer-assessed — docstrings accurate, no stale comments; [TYPE] Reviewer-assessed — all boundaries annotated (Rule #3); [SIMPLE] Reviewer-assessed — clean count/detect split, no over-engineering; [RULE] Reviewer-assessed — lang-review enumeration in Rule Compliance, compliant.

**Pattern observed:** shared low-layer helper in `genre/` called by both the loader (caches on `World`) and the session-free reference projection (detects on disk) — correct DRY, honors the layering (server→genre). Deferred imports match the loader's established style (`loader.py:857+`).

**Error handling:** fail-loud on every path (`cluster_detection.py:72` raises on malformed graph); explicit single classification on no-signal (`:107`), never silent/unknown — satisfies spec AC4. The error-*type* refinement is [EDGE] M-1.

**Verdict rationale:** All 4 ACs met and tested (22/22 green), OTEL decision span wired and routed, No-Silent-Fallbacks honored. The two Medium findings are robustness/contract refinements with no reachable trigger in current content; per the severity table, Medium/Low do not block. Unblocks 104-2 (M-B). Recommend the [EDGE] M-1 `GenreLoadError` wrap + [TEST] M-2 loader test as a fast-follow.

**Handoff:** To SM for finish-story.