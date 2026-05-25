---
story_id: "51-4"
jira_key: "none"
epic: "51"
workflow: "tdd"
---
# Story 51-4: Remove DEV_SCENES gate + add fixture picker to connect screen

## Story Details
- **ID:** 51-4
- **Jira Key:** none
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 51 — Scenario Fixture Library Wave 1 — Retarget Caverns Fixtures to beneath_sunden

## Branches
- **Orchestrator:** main (no changes needed)
- **Server:** feat/51-4-scene-fixture-picker
- **UI:** feat/51-4-scene-fixture-picker

## Acceptance Criteria

### Server
- Remove the `if DEV_SCENES == "1"` conditional in create_app()
- Always register create_scene_harness_router()
- Add GET /dev/scenes listing endpoint returning [{name, description, genre, world}] for each YAML in fixtures/
- Drop SIDEQUEST_FIXTURES_DIR env var indirection

### UI
- Add "Scene Library" section to ConnectScreen
- Fetch GET /dev/scenes on mount
- Display fixture cards (name + description + genre badge)
- Click loads ?scene={name} and connects

### Cleanup
- Update playtest-cookbook.md to remove DEV_SCENES references
- Update justfile recipes that set DEV_SCENES

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-25T09:47:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-25T00:00:00Z | 2026-05-25T09:15:47Z | 9h 15m |
| red | 2026-05-25T09:15:47Z | 2026-05-25T09:29:59Z | 14m 12s |
| green | 2026-05-25T09:29:59Z | 2026-05-25T09:37:09Z | 7m 10s |
| spec-check | 2026-05-25T09:37:09Z | 2026-05-25T09:38:52Z | 1m 43s |
| verify | 2026-05-25T09:38:52Z | 2026-05-25T09:42:26Z | 3m 34s |
| review | 2026-05-25T09:42:26Z | 2026-05-25T09:46:44Z | 4m 18s |
| spec-reconcile | 2026-05-25T09:46:44Z | 2026-05-25T09:47:30Z | 46s |
| finish | 2026-05-25T09:47:30Z | - | - |

## Sm Assessment

Story is well-scoped: remove an unnecessary env-var gate (Cloudflare tunnel handles access), expose a listing endpoint, and wire a picker into the ConnectScreen. Three-pointer, TDD workflow, server+ui repos. Branches created in both subrepos. No Jira key (per project policy). No blockers.

**Routing:** TDD phased → RED phase → Radar (TEA).

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No undocumented deviations found. TEA and Dev both logged "no deviations" — confirmed accurate after reviewing all 11 ACs against the diff.

### Architect (reconcile)
- No additional deviations found. TEA, Dev, and Reviewer subsections are complete and accurate. All 11 ACs implemented as specified. No AC deferrals to verify.

## Delivery Findings

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- **Improvement** (non-blocking): AC-11 is a no-op — `docs/playtest-cookbook.md` contains no DEV_SCENES references. Affects `docs/playtest-cookbook.md` (nothing to change). *Found by Dev during implementation.*

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer (code review)
- **Improvement** (non-blocking): Pre-existing CWE-209 in POST /dev/scene/{name} — raw user-supplied `name` reflected in 404 detail payload before router-level validation. Blocked by `hydrate_fixture()` internally but the reflection exists. Affects `sidequest-server/sidequest/server/scene_harness_router.py` (add `_FIXTURE_NAME_RE.match(name)` guard at top of `load_scene`). *Found by Reviewer during code review.*

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 5 | confirmed 0, dismissed 4 (pre-existing/low), deferred 1 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 returned, 7 disabled via settings)
**Total findings:** 0 confirmed blocking, 4 dismissed (low-severity/pre-existing), 1 deferred (pre-existing CWE-209 logged as delivery finding)

### Security Finding Disposition

1. **CWE-209 reflected input in POST /dev/scene/{name}** (medium) — Dismissed from blocking: pre-existing code, story spec says "do not touch POST handler". Deferred as delivery finding for future story.
2. **OTEL fixtures_dir path leak** (low) — Dismissed: GM panel is Keith-only dev tool; `fixtures_dir` is operational debug signal, not sensitive. Pre-existing pattern in intent.load span.
3. **OTEL save_path leak** (low) — Dismissed: same as above, pre-existing in persist.ok span.
4. **navigate() missing encodeURIComponent** (low) — Dismissed: server `_FIXTURE_NAME_RE` guarantees `[A-Za-z0-9_-]` only. No actual XSS vector. Defense-in-depth gap noted.
5. **Relative fixtures_dir default** (low) — Dismissed: matches pre-existing behavior; `just server` runs from orchestrator root.

## Reviewer Assessment

**Verdict:** APPROVED

[EDGE] No edge cases found in new code — `list_scenes` handles empty dir, invalid YAML, non-matching filenames gracefully. Skipped subagent confirmed disabled.
[SILENT] No silent failure paths — invalid YAML logged at WARNING, OTEL span always fires regardless of scan results. `scene_harness_router.py:192,200-203`.
[TEST] 45/45 tests GREEN — 13 new listing tests + 24 existing harness tests + 8 UI tests. Good AC coverage (21 tests across 8 ACs).
[DOC] Module docstring updated from "Dev-gated" to "Always registered" — accurate. Comment analyzer disabled.
[TYPE] Return type `list[dict[str, str | None]]` on `list_scenes` is annotated. `fixtures_dir: Path | None` on `create_app` follows existing param pattern. Type design subagent disabled.
[SEC] Security scan found 0 blocking issues. 5 findings all low/pre-existing. See disposition above.
[SIMPLE] No over-engineering — listing endpoint is ~25 lines of straightforward scan logic. Simplifier disabled.
[RULE] Python #3 (type annotations): `list_scenes` has return type. `create_app` has `fixtures_dir` typed. Python #5 (pathlib): Path used throughout, no string concatenation. Python #6 (test quality): all assertions meaningful per TEA self-check. Rule checker disabled.

**Data flow traced:** User clicks fixture card → `navigate("/?scene=combat_brawl_wasteland")` → App picks up `?scene` param → existing `POST /dev/scene/{name}` fires → hydrate → persist → slug returned → game loads. Safe because `scene.name` is server-validated via `_FIXTURE_NAME_RE` before reaching the client.

**Pattern observed:** The `list_scenes` handler follows the exact same request-scoped `request.app.state.fixtures_dir` pattern as the existing `load_scene` handler at `scene_harness_router.py:69-70`.

**Error handling:** Fetch failure in UI → empty catch → section stays empty (non-fatal per `ConnectScreen.tsx:105`). Server invalid YAML → `continue` with WARNING log (`scene_harness_router.py:191-192`). Both appropriate for a listing endpoint.

### Devil's Advocate

What if this code is broken? The most plausible attack surface: removing the DEV_SCENES gate exposes scene harness endpoints to anyone who reaches the origin server. But the origin is behind Cloudflare Zero Trust — the tunnel config at `~/.cloudflared/config.yml` gates the hostname, and only the playgroup email allowlist gets in. Without the tunnel, `127.0.0.1:8765` is localhost-only. So the gate removal is genuinely safe given the deployment architecture.

What about a confused user? The Scene Library section renders fixture names as raw slugs (`combat_brawl_wasteland`) rather than pretty names (`Combat — Wasteland Brawl`). The YAML files have a `name:` field with the pretty name, but the listing endpoint returns the file stem as `name`, not the YAML's `name:` field. This means the UI shows `combat_brawl_wasteland` instead of `Combat — Wasteland Brawl`. This is a cosmetic choice, not a bug — the fixture stem is what you need to pass to `?scene=`, so showing it is operationally useful for Keith's iteration workflow. The pretty name from YAML is not surfaced. Could confuse a non-Keith user but the audience IS Keith.

What if the filesystem is stressed? `fixtures_dir.glob("*.yaml")` + `yaml.safe_load` on each file is synchronous I/O in an async handler. With 12 fixture files (current count), each under 2KB, the total blocking time is negligible. At 1000+ fixtures it would be a problem, but that's far beyond the current scale and the endpoint is not polled — it's fetched once on mount. If a fixture YAML is somehow huge (multi-MB), `yaml.safe_load` would block the event loop during parsing. Extremely unlikely given the current fixture authoring workflow.

What about config with unexpected fields? The listing endpoint only reads `genre`, `world`, `description` from each YAML — extra fields are ignored by `raw.get()`. If `genre` or `world` is missing, the fixture is skipped (`scene_harness_router.py:193-194`). If they're present but non-string (e.g. `genre: 42`), they'll be serialized as JSON numbers in the response — the UI would render `42` as the genre badge text. Harmless but ugly. Not worth blocking for.

The devil's advocate found nothing the review missed. The code is clean.

**Handoff:** To Hawkeye (SM) for finish-story

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | All pre-existing code, not introduced by story 51-4 |
| simplify-quality | clean | No quality issues |
| simplify-efficiency | clean | No over-engineering |

**Applied:** 0 high-confidence fixes (all 4 reuse findings target pre-existing code — out of scope)
**Flagged for Review:** 0 medium-confidence findings applicable to this story
**Noted:** 4 observations on pre-existing patterns (localStorage duplication, prettify extraction, error handler extraction, disambiguate promotion)
**Reverted:** 0

**Overall:** simplify: clean (for this story's changes)

**Quality Checks:** Server ruff — 7 pre-existing import errors (none in story files); UI tsc — clean
**Handoff:** To Colonel Potter (Reviewer) for code review

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/app.py` — removed DEV_SCENES gate, added `fixtures_dir` constructor arg
- `sidequest-server/sidequest/server/scene_harness_router.py` — added `GET /dev/scenes` listing endpoint with YAML scan, regex validation, OTEL span
- `sidequest-server/tests/server/test_scene_harness.py` — removed obsolete gate-absent tests, updated helper to use constructor arg
- `sidequest-server/tests/server/test_scene_listing.py` — updated helper to use new API
- `sidequest-ui/src/screens/ConnectScreen.tsx` — added Scene Library section with fetch, cards, click-to-navigate
- `justfile` — removed DEV_SCENES and SIDEQUEST_FIXTURES_DIR env vars

**Tests:** 45/45 passing (GREEN) — 37 server (13 new + 24 existing) + 8 UI
**Branches:** feat/51-4-scene-fixture-picker (server + UI, both pushed)

**Handoff:** To verify phase

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

AC-by-AC verification against context-story-51-4.md:

| AC | Spec | Code | Status |
|----|------|------|--------|
| AC-1 | Remove `if DEV_SCENES == "1"` conditional | Conditional removed from `app.py:275-291` | Aligned |
| AC-2 | Always register scene harness router | `create_scene_harness_router()` called unconditionally | Aligned |
| AC-3 | `GET /dev/scenes` returns `[{name, description, genre, world}]` | `list_scenes()` scans YAML, validates regex, returns fields | Aligned |
| AC-4 | Drop `SIDEQUEST_FIXTURES_DIR` env var | `fixtures_dir` is now a constructor arg with `Path("scenarios/fixtures")` default | Aligned |
| AC-5 | Scene Library section on ConnectScreen | `<section>` with `<h2>Scene Library</h2>` added | Aligned |
| AC-6 | Fetch `GET /dev/scenes` on mount | `useEffect` with `fetch("/dev/scenes")` and `[]` deps | Aligned |
| AC-7 | Cards with name + description + genre badge | Cards render name, `prettify(genre)` badge, description | Aligned |
| AC-8 | Click loads `?scene={name}` | `navigate(\`/?scene=${scene.name}\`)` | Aligned |
| AC-9 | Remove DEV_SCENES/FIXTURES_DIR from justfile | Both lines removed from `_server-cmd` | Aligned |
| AC-10 | Update `serve` comment | Comment updated to remove DEV_SCENES reference | Aligned |
| AC-11 | Remove DEV_SCENES from cookbook | No-op — file has no references (confirmed by Dev) | Aligned |

**Observations (non-blocking):**
- `_FIXTURE_NAME_RE` is duplicated between `scene_harness_router.py` and `scene_harness.py`. Trivial — both use the same pattern, and importing from `scene_harness.py` would add a cross-module dependency for a 1-line regex. Leave as-is.
- Navigate pattern `/?scene={name}` chosen over POST-then-navigate. Both were spec-valid options. The `?scene=` approach is simpler and avoids an extra server round-trip.

**Decision:** Proceed to verify

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story introduces new server endpoint (GET /dev/scenes), removes env var gate, and adds UI section — all need test coverage.

**Test Files:**
- `sidequest-server/tests/server/test_scene_listing.py` — Server: gate removal (AC-1/AC-2), listing endpoint (AC-3), fixtures_dir constructor arg (AC-4)
- `sidequest-ui/src/__tests__/scene-library-wiring.test.tsx` — UI: Scene Library section rendering, fetch, cards, navigation (AC-5 through AC-8)

**Tests Written:** 21 tests covering 8 ACs

| AC | Tests | Repo |
|----|-------|------|
| AC-1/AC-2 (always register route) | 2 | server |
| AC-3 (GET /dev/scenes listing) | 9 | server |
| AC-4 (fixtures_dir constructor arg) | 2 | server |
| AC-5 (Scene Library section) | 1 + 2 edge cases | ui |
| AC-6 (fetch on mount) | 1 | ui |
| AC-7 (fixture cards) | 3 | ui |
| AC-8 (click navigates) | 1 | ui |

**Status:** RED (all 21 failing — ready for Dev)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Python #3 type annotations at boundaries | Covered by listing endpoint return type assertions | failing |
| Python #5 path handling (pathlib) | test_create_app_accepts_fixtures_dir_kwarg asserts Path type | failing |
| Python #6 test quality | Self-checked: all tests have meaningful assertions, no vacuous patterns | verified |
| TS #4 null handling | test_listing_includes_fixtures_without_description (null description) | failing |
| TS #6 React useEffect deps | test fetches /dev/scenes on mount (exercises hook correctness) | failing |
| OTEL observability | test_listing_emits_otel_span | failing |
| Wiring test (CLAUDE.md) | test_listing_returns_canonical_fixtures_from_real_dir (real filesystem) | failing |
| No silent fallbacks | test_listing_excludes_invalid_yaml_gracefully (bad YAML excluded, not 500) | failing |

**Rules checked:** 8 applicable rules have test coverage
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Major Winchester) for implementation