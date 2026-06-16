---
story_id: "122-3"
jira_key: ""
epic: "122"
workflow: "trivial"
---
# Story 122-3: Lift interior HTTP endpoint to server/rest.py; leave interior/ pure (no FastAPI imports)

## Story Details
- **ID:** 122-3
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T04:50:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T04:31:53+00:00 | 2026-06-16T04:33:45Z | 1m 52s |
| implement | 2026-06-16T04:33:45Z | 2026-06-16T04:44:04Z | 10m 19s |
| review | 2026-06-16T04:44:04Z | 2026-06-16T04:50:41Z | 6m 37s |
| finish | 2026-06-16T04:50:41Z | - | - |

## Sm Assessment

**Story:** 122-3 — Lift the interior HTTP endpoint to `server/rest.py`; leave `interior/` pure (no FastAPI imports). 2pt, p3, trivial workflow, server repo only.

**Context:** Epic 122 (Honest Layering, ADR-147) corrects layering-inversion edges where low-level domain code imports UP into `sidequest/server`. The import-direction law is `foundation <- {game,genre,orbital,magic,interior} <- server`. The `interior/` subsystem currently owns a FastAPI HTTP endpoint — an upward edge that violates the law. Prior steps 122-1 (asset_urls/slug_fold/reference_anchors) and 122-2 (pure combat-rules helpers) are done and approved.

**Scope (behavior-preserving, no library extraction):**
- Move the interior HTTP endpoint definition from `sidequest/interior/` to `sidequest/server/rest.py`.
- Strip all FastAPI imports out of `sidequest/interior/`, leaving it pure interior/room state logic.
- Keep the endpoint's external behavior (route, method, payload, response) identical — pure relocation, no contract change.

**Routing:** trivial (phased) workflow → next agent is **dev** (Hephaestus the Smith). setup → implement → review → finish.

**Reference:** docs/adr/147-honest-layering-pure-logic-below-server.md

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Endpoint registered on the existing REST router instead of a standalone APIRouter**
  - Rationale: rest.py's idiom is one router built in `create_rest_router()`; folding the route in matches the surrounding code, drops a redundant `include_router`, and preserves the exact route path/method/response. Same external behavior, one fewer router object.
  - Severity: trivial
  - Forward impact: none — route path `GET /api/chassis/{instance_id}/interior`, payload, and `image/svg+xml` response are unchanged; 122-5's import-direction guard sees interior/ with zero FastAPI imports either way.
- **Kept non-cached `load_genre_pack` in the lifted helper**
  - Rationale: Switching to the cached loader would change caching behavior; a pure relocation must not. Preserved the original call exactly.
  - Severity: trivial
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Endpoint registered on the existing REST router instead of a standalone APIRouter**
  - Spec source: .session/122-3-session.md, Sm Assessment ("Move the interior HTTP endpoint definition from `sidequest/interior/` to `sidequest/server/rest.py`")
  - Spec text: "Move the interior HTTP endpoint definition ... to sidequest/server/rest.py"
  - Implementation: Registered `get_chassis_interior` inside `create_rest_router()` (the existing rest router, already `app.include_router`'d) and removed the separate `interior_router`/`app.include_router(interior_router)` wiring in app.py, rather than relocating the standalone `interior_router = APIRouter()` to rest.py.
  - Rationale: rest.py's idiom is one router built in `create_rest_router()`; folding the route in matches the surrounding code, drops a redundant `include_router`, and preserves the exact route path/method/response. Same external behavior, one fewer router object.
  - Severity: trivial
  - Forward impact: none — route path `GET /api/chassis/{instance_id}/interior`, payload, and `image/svg+xml` response are unchanged; 122-5's import-direction guard sees interior/ with zero FastAPI imports either way.
- **Kept non-cached `load_genre_pack` in the lifted helper**
  - Spec source: behavior-preserving-refactor constraint (Sm Assessment, "no contract change")
  - Spec text: "Keep the endpoint's external behavior ... identical — pure relocation"
  - Implementation: Imported `load_genre_pack` (non-cached) into rest.py for `_find_chassis_instance`, matching the original dispatch.py, even though rest.py already imports `load_genre_pack_cached`.
  - Rationale: Switching to the cached loader would change caching behavior; a pure relocation must not. Preserved the original call exactly.
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **Endpoint registered on the existing REST router instead of a standalone APIRouter** → ✓ ACCEPTED by Reviewer: sound and idiomatic. Verified the route is registered exactly once on `create_rest_router()` (rest.py:~950), `rest_router` is included at app.py:297, and the old `interior_router` include is fully removed (no double/missing registration). Same route path, method, and `image/svg+xml` response — behavior preserved, one fewer router object.
- **Kept non-cached `load_genre_pack` in the lifted helper** → ✓ ACCEPTED by Reviewer: correct call for a behavior-preserving move. Verified `_find_chassis_instance` still calls `load_genre_pack` (non-cached) at rest.py:~157; the added `load_genre_pack_cached` import serves only pre-existing routes. No caching-semantics drift.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/rest.py` — Lifted `get_chassis_interior` (GET /api/chassis/{instance_id}/interior) + helpers `_find_chassis_instance` and `_EmptySnapshot` here; registered the route inside `create_rest_router()`. Added `Response` to the fastapi import, `load_genre_pack` to the genre.loader import, and imports of `render_interior_svg` / `emit_interior_render`.
- `sidequest/server/app.py` — Removed `from sidequest.interior.dispatch import interior_router` and `app.include_router(interior_router)`; replaced with a comment noting the endpoint now lives on the REST router (ADR-147 / 122-3).
- `sidequest/interior/dispatch.py` — **Deleted.** It was the only FastAPI-bearing module in `interior/`, and it reached UP into `sidequest.server.rest` for `DEFAULT_GENRE_PACK_SEARCH_PATHS` (the exact layering inversion ADR-147 targets).

**Result:** `interior/` is now FastAPI-free (`grep -rn "fastapi\|APIRouter\|HTTPException" sidequest/interior/` → clean). The upward edge interior→server is gone; the server tier owns the HTTP surface and imports the pure renderer downward (`interior.render`).

**Tests:** interior 18/18 GREEN, server/test_rest.py 20/20 GREEN, `create_app`/`create_rest_router` import sanity OK. The 177 failures in the full parallel server run are pre-existing and unrelated (OTEL/Anthropic-SDK mock + WWN-content drift per project memory) — not a regression from this change. Behavior-preserving: route path, method, payload, and `image/svg+xml` response are identical.

**Branch:** feat/122-3-lift-interior-http-endpoint (pushed)

**Handoff:** To review phase — Hermes Psychopompos (reviewer).
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (38/38 green, lint/format clean, no stragglers, interior FastAPI-free) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 0, dismissed 1, deferred 2 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 0, dismissed 1, deferred 2 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via workflow.reviewer_subagents)
**Total findings:** 0 confirmed-blocking, 2 dismissed (with rationale), 4 deferred (all pre-existing, captured as Delivery Findings)

### Finding dispositions
- **[EDGE] Misleading 404 when chassis_class_id is dangling** (rest.py:~173, medium) → **DEFERRED.** Real, but identical to deleted dispatch.py — pre-existing, not introduced by this behavior-preserving relocation. Filed as Delivery Finding. Fixing it would change the endpoint's response contract, violating the story's "pure relocation, no contract change" scope.
- **[SEC] No Silent Fallbacks: `except Exception` swallows pack-load failures** (rest.py:~157, medium) → **DEFERRED.** Matches a project rule (No Silent Fallbacks) so NOT dismissed — confirmed as a real pre-existing violation, carried over verbatim from dispatch.py. Out of scope for a relocation (surfacing the failure changes behavior). Filed as Delivery Finding for a follow-on.
- **[SEC] Reflected `instance_id` in 404 JSON without length/charset validation** (rest.py:~183, low) → **DEFERRED.** Pre-existing; response is application/json (not HTML), so no XSS. Filed as Delivery Finding (hygiene).
- **[EDGE/SEC] `_EmptySnapshot` mutable class-level list attributes** (rest.py:~185, low) → **DISMISSED.** Not exploitable: `snapshot.npcs` is overwritten per-instance before use and the renderer only *reads* `characters`/`npcs` via `getattr` (confirmed by security subagent reading interior/render.py). Pre-existing, carried verbatim.
- **[SEC] Latent SVG XSS when live session snapshot is later wired** (interior/render.py, low) → **DISMISSED for this story.** Not present in current code (all SVG text comes from server-authored YAML, never from the URL param). It is a future advisory for the live-wiring follow-on, not a defect in this diff.
- **[EDGE] `_find_chassis_instance` now module-level in rest.py (wider import scope)** (rest.py:~146, low) → **DEFERRED (noted).** Not a correctness edge; same module-level visibility it had in dispatch.py. No action.

## Reviewer Review

### Observations
- **[VERIFIED] Relocation is byte-faithful** — the added block in rest.py (`_find_chassis_instance`, `_EmptySnapshot`, `get_chassis_interior`) is logically identical to the removed dispatch.py block; only the decorator (`@interior_router.get` → `@router.get`), indentation (now nested in `create_rest_router`), and import sites changed. Confirmed by edge-hunter diff comparison.
- **[VERIFIED] Endpoint registered exactly once** — `GET /api/chassis/{instance_id}/interior` is declared only inside `create_rest_router()` (rest.py:~950); `app.include_router(rest_router)` at app.py:297 is the single registration. The old `app.include_router(interior_router)` is removed with no replacement, so no double- or missing-registration. Evidence: edge-hunter route enumeration + interior endpoint test hitting `/api/chassis/kestrel/interior` → 200.
- **[VERIFIED] `DEFAULT_GENRE_PACK_SEARCH_PATHS` is the same object** — dispatch.py imported it from `sidequest.server.rest`; rest.py imports it from `sidequest.genre.loader` (the true origin). Edge-hunter confirmed runtime `same object: True` — no default-value drift.
- **[VERIFIED] Non-cached loader preserved** — the moved `_find_chassis_instance` still calls `load_genre_pack(genre_dir)` (rest.py:~157), not `load_genre_pack_cached`. The newly-imported `load_genre_pack_cached` is used only by pre-existing portrait/pack routes. No caching-behavior change. Matches Dev's logged deviation #2.
- **[VERIFIED] `interior/` is now FastAPI-free** — `grep -rn "fastapi|APIRouter|HTTPException|Response" sidequest/interior/` returns zero hits; the upward edge `interior → server.rest` (for DEFAULT_GENRE_PACK_SEARCH_PATHS) is eliminated. This is exactly the ADR-147 import-direction outcome the story required.
- **[VERIFIED] No path traversal** — `instance_id` (URL path param) is used only in equality comparison (`inst_cfg.id == instance_id`) and the 404 detail (`{instance_id!r}`); it never constructs a filesystem path. Confirmed by security subagent trace.
- **[MEDIUM/pre-existing] Two carried-over correctness/rule smells** (misleading 404 detail; No-Silent-Fallbacks `except Exception`) — both deferred as Delivery Findings; neither is introduced by this change and neither blocks (Medium, and out of scope for a relocation).

### Rule Compliance
- **ADR-147 import-direction law (foundation <- {…,interior} <- server):** COMPLIANT. interior/ no longer imports up into server; server imports the pure renderer (`interior.render`) downward. The specific inversion the story names (interior/dispatch importing `sidequest.server.rest.DEFAULT_GENRE_PACK_SEARCH_PATHS`) is gone.
- **No Stubbing / No half-wired features:** COMPLIANT. dispatch.py fully deleted, route fully wired on rest_router, tests green end-to-end via create_app. No empty shells left.
- **OTEL Observability Principle:** COMPLIANT (preserved). `emit_interior_render(...)` is carried over unchanged on the success path. No new subsystem decision was added (cosmetic relocation), so no new span required.
- **No Silent Fallbacks:** ONE pre-existing violation present (`except Exception` per-pack skip in `_find_chassis_instance`) — confirmed, not dismissed, deferred as a Delivery Finding because surfacing it changes behavior and is out of scope for a pure relocation. No NEW silent fallback introduced by the diff.
- **Python lang-review — path handling (rule 5):** COMPLIANT. URL param never enters a filesystem path.
- **Python lang-review — mutable class attribute (rule 2):** `_EmptySnapshot` carries class-level `list` defaults — pre-existing, not exploitable (per-instance overwrite + read-only renderer). No new instance introduced.

### Devil's Advocate
Argue this is broken: the most dangerous thing about a "pure relocation" is the claim itself — reviewers rubber-stamp moves and miss the one line that drifted. So I attacked the equivalence. Could the route have silently vanished? If `create_rest_router()` weren't actually `include_router`'d, the endpoint would 404 everywhere and the only test covering it might be a stale unit test that never hits create_app. Refuted: app.py:297 includes rest_router, and `tests/interior/test_endpoint_wired.py` drives a real `create_app(...)` TestClient and asserts 200 + `data-actor="kestrel_captain"` in the body — a genuine end-to-end hit, not a shape assertion. Could the route be registered twice (old + new), causing FastAPI to shadow one with a 405/duplicate? Refuted: the old `interior_router` include is deleted and `grep` finds no surviving `interior_router`/`interior.dispatch` reference except a provenance comment. Could `DEFAULT_GENRE_PACK_SEARCH_PATHS` now resolve to a different default (rest.py re-exported a different value than genre.loader)? Refuted: it was always genre.loader's symbol; rest.py merely re-exported it, and runtime identity is the same object. Could the loader have silently switched to the cached variant, changing freshness semantics mid-session? Refuted: the moved code still calls `load_genre_pack` (non-cached); the cached import serves only pre-existing routes. What would a malicious user do? Feed a huge/Unicode `instance_id` — it reflects in a JSON 404 (no XSS), never touches the filesystem (no traversal). What about a stressed filesystem — a pack that fails to load mid-walk? The `except Exception` swallows it and the user sees a possibly-wrong 404; that is a real pre-existing rule violation, but it is unchanged by this diff and out of scope for a behavior-preserving move. Nothing the devil surfaced is a NEW defect in this change.


## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A faithful, behavior-preserving relocation per ADR-147 / story 122-3. The chassis-interior HTTP endpoint moved verbatim from `sidequest/interior/dispatch.py` (deleted) into `sidequest/server/rest.py`'s `create_rest_router()`, and the redundant `app.include_router(interior_router)` wiring was removed. `interior/` is now FastAPI-free, eliminating the `interior → server.rest` upward edge the story targeted.

**Data flow traced:** URL path param `instance_id` → `_find_chassis_instance` equality match against pack-authored chassis IDs → render `image/svg+xml` (success) or `HTTPException(404)` (miss). `instance_id` never reaches a filesystem path (no traversal) and is reflected only into a JSON 404 (no XSS).

**Pattern observed:** route folded into the existing single-router factory (rest.py:~950), matching rest.py's idiom; registered once, included once (app.py:297).

**Error handling:** 404-on-miss preserved. One pre-existing `except Exception` per-pack skip (No-Silent-Fallbacks) carried over unchanged — deferred as a Delivery Finding, out of scope for a pure relocation.

**Tests:** interior 18/18 + rest 20/20 = 38/38 GREEN via real `create_app` TestClient; lint/format clean; no straggler references.

**Findings:** 0 blocking (no Critical/High). 4 deferred + 2 dismissed — every finding explicitly pre-existing and not introduced by this diff.
- `[EDGE]` Misleading 404 when `chassis_class_id` is dangling (rest.py:~173, medium) → deferred (pre-existing, out of scope for a pure relocation).
- `[EDGE]` `_EmptySnapshot` mutable class-level list attributes (rest.py:~185, low) → dismissed (not exploitable: per-instance overwrite + read-only renderer).
- `[EDGE]` `_find_chassis_instance` now module-level in rest.py (low) → noted, no action (same visibility as in dispatch.py).
- `[SEC]` No-Silent-Fallbacks `except Exception` swallows pack-load failures (rest.py:~157, medium) → deferred (matches project rule, NOT dismissed; pre-existing, surfacing it changes behavior).
- `[SEC]` Reflected `instance_id` in 404 JSON without length/charset validation (rest.py:~183, low) → deferred (application/json, no XSS; hygiene).
- `[SEC]` Latent SVG-XSS when live snapshot is later wired (interior/render.py, low) → dismissed for this story (not present today; future-wiring advisory).
- `[SEC]` Path traversal → confirmed NOT present: `instance_id` never enters a filesystem path.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings (Reviewer)
<!-- appended by Reviewer; append-only -->

### Reviewer (code review)
- **Improvement** (non-blocking): `_find_chassis_instance` swallows per-pack `load_genre_pack` failures via `except Exception` + warning-log + continue, so a masked pack-load error is indistinguishable from a genuine 404 (No Silent Fallbacks rule). Affects `sidequest/server/rest.py` (`_find_chassis_instance` — accumulate load-failure count and surface it in the 404 detail / a summary log). Pre-existing (carried verbatim from the deleted dispatch.py); out of scope for the 122-3 behavior-preserving move. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The 404 detail returns a misleading "not found in any genre pack" message even when the instance exists but its `chassis_class_id` is dangling. Affects `sidequest/server/rest.py` (distinguish "instance not found" vs "instance found, class_id unresolvable"). Pre-existing. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `instance_id` is reflected into the 404 JSON without length/charset validation; harmless today (application/json, not HTML) but a slug-validation guard at the route entry is cheap hygiene. Affects `sidequest/server/rest.py` (`get_chassis_interior`). Pre-existing. *Found by Reviewer during code review.*
- **Gap** (non-blocking): Latent SVG-XSS risk — when the endpoint is later wired to live session snapshots, player-authored NPC names will flow into SVG `<text>` nodes; address sanitization / `Content-Security-Policy: default-src 'none'` at that wiring point. Affects `sidequest/interior/render.py` + the future live-snapshot wiring story. Not present today (all SVG text is server-authored YAML). *Found by Reviewer during code review.*