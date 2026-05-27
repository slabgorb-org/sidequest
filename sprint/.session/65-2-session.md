---
story_id: "65-2"
jira_key: null
epic: "65"
workflow: "tdd"
---
# Story 65-2: Per-session asset ledger — track runtime-generated images per save file

## Story Details
- **ID:** 65-2
- **Jira Key:** TBD (will be assigned when claimed)
- **Epic:** 65 — Content Infrastructure — R2 asset tracking and audit
- **Workflow:** tdd
- **Repos:** server, content
- **Points:** 3
- **Priority:** P1
- **Type:** feature
- **Stack Parent:** none

## Problem Statement

Runtime-generated images (portraits, scene illustrations, POI renders triggered during play) are uploaded to R2 by the daemon but never recorded against the save file that caused them. When a player resumes a session, those images are orphaned — the UI can't find them because nothing links the save to its R2 keys.

## Acceptance Criteria

### Server: SQLite schema and asset_ledger table
- [ ] Add `asset_ledger` table to `SqliteStore` schema migration with columns:
  - `r2_key` (TEXT, PRIMARY KEY) — full R2 path (e.g., `genre_packs/caverns_and_claudes/images/portraits/slug.png`)
  - `asset_type` (TEXT, NOT NULL) — enum: portrait | illustration | poi
  - `entity_ref` (TEXT, NOT NULL) — NPC slug, scene ID, or POI slug (the thing the asset represents)
  - `created_turn` (INTEGER, NOT NULL) — turn number when asset was generated
  - `md5` (TEXT, NOT NULL) — MD5 hash from r2_manifest.json
  - `size_bytes` (INTEGER, NOT NULL) — file size from r2_manifest.json

### Server: daemon_client asset ledger writes
- [ ] `daemon_client.upload_complete()` receives R2 upload result (r2_key, asset_type, entity_ref, turn, md5, size_bytes) and writes asset_ledger row
- [ ] Ledger write is idempotent (upsert on r2_key)
- [ ] Respects durable-retention-by-default: never reap save-referenced R2 assets on a timer

### Server: REST API
- [ ] `GET /api/session/{slug}/assets` returns full asset_ledger for the save (JSON array of ledger rows)
- [ ] Endpoint is available during session resume and accessible to the UI on reconnect

### UI: ImageBus ledger read on reconnect
- [ ] `ImageBus` reads `/api/session/{slug}/assets` on reconnect (when WebSocket reconnects after a player returns to a saved session)
- [ ] Preloads CDN URLs for portraits and illustrations from previous turns — no re-rendering needed
- [ ] Maps asset_type + entity_ref to the correct UI component slots (portrait gallery, scene context, POI backgrounds)

### Audit: r2_audit.py cross-references asset_ledger
- [ ] `r2_audit.py` (from story 65-1) cross-references asset_ledger tables across all saves in `~/.sidequest/saves/*.db`
- [ ] Detects orphaned R2 keys: uploaded to R2 but no save references them (in r2_manifest but missing from all asset_ledgers)
- [ ] Detects dangling ledger rows: save references an R2 key that no longer exists (in asset_ledger but missing from r2_manifest)
- [ ] Reports both categories with path, MD5, and affected save files

## Technical Notes

**Dependencies:** Completes the loop started in story 65-1 (r2_manifest.json). The manifest provides the durable record; the asset_ledger links saves to their assets.

**Durable retention:** Never apply reaping logic to save-referenced assets. If a save's asset_ledger references an R2 key, that key must remain in R2 indefinitely. Orphaned keys (in manifest but unrefenced) are fair game for eventual cleanup, but save-referenced keys are permanent.

**Entity refs:** Store the canonical reference (NPC slug, scene ID, POI slug) so the UI can map back to the right component. The audit then uses these refs to validate that YAML entities still exist.

**No re-render on resume:** The whole point — when a player loads a save, the UI should find the portraits and illustrations in the ledger and load from CDN without triggering new daemon renders. This requires ledger writes to be *eager* and *complete* on each upload.

## Sm Assessment

**Disposition:** Ready for RED. Story is fully scoped — six AC clusters spanning server (SQLite `asset_ledger` schema, `daemon_client` upsert writes, `GET /api/session/{slug}/assets`), UI (`ImageBus` reconnect read + CDN preload), and audit (`r2_audit.py` cross-reference). Direct continuation of 65-1, which landed `r2_manifest.json` and `r2_audit.py`; this story closes the loop by linking saves to their R2 keys.

**Technical approach for TEA/Dev:**
- Schema migration adds `asset_ledger` keyed on `r2_key` (upsert/idempotent); columns enumerated in AC.
- Write path hangs off `daemon_client.upload_complete()` — verify the daemon already returns r2_key/md5/size_bytes (65-1's manifest plumbing) so this is wiring, not reinvention.
- REST endpoint must be reachable on resume/reconnect; `ImageBus` consumes it to preload portraits/illustrations without re-rendering.
- Audit reuses 65-1's `r2_audit.py` — extend, don't fork — to flag orphans (manifest∖ledgers) and dangling rows (ledger∖manifest).

**Durable-retention invariant:** save-referenced R2 keys are permanent — never reaped on a timer. RED tests must pin this.

**Wiring gate:** per project rules, RED must include an integration test proving the ledger write fires from the production upload path and the endpoint is hit by `ImageBus` on reconnect — not just unit coverage of the table.

**Risks:** cross-repo (server + content + ui touched by ACs though `repos: server,content` — UI ACs may spill into sidequest-ui; flag if so). No blockers; 65-1 merged.

## Workflow Tracking

**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-05-27T15:44:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | 2026-05-27T15:44:33Z | 15h 44m |
| red | 2026-05-27T15:44:33Z | - | - |

## Delivery Findings

No upstream findings (setup phase).

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): The ledger `md5` column has no runtime source. The runtime
  artifact uploader computes **sha256** (`hashlib.sha256(content_bytes).hexdigest()`) and
  embeds it in the key; no md5 is computed anywhere on the render path. Affects
  `sidequest-daemon/sidequest_daemon/media/r2_writer.py:91` and the ledger schema
  (`asset_ledger.md5`) — column should reuse the existing sha256, not compute a second
  hash. *Found by TEA during test design.*
- **Conflict** (blocking): Runtime renders and authored pack assets occupy **disjoint R2
  namespaces** — runtime → `artifacts/{world}/{session}/{kind}/{sha}.{ext}`; manifest/pack
  → `genre_packs/...` (the pack uploader *requires* the `genre_packs/` prefix). Affects
  `sidequest-daemon/.../r2_writer.py:196` and **AC6** (`scripts/r2_audit.py` ledger
  cross-reference): comparing ledger keys against the manifest compares disjoint sets, so
  every ledger row is spuriously "dangling" and orphan detection is meaningless as
  specified. AC6 needs redefinition (e.g. cross-ref against the `artifacts/` R2 listing,
  not the manifest) before it can be tested. *Found by TEA during test design.*
- **Gap** (blocking): The daemon image render result is mid-refactor —
  `sidequest-daemon/.../media/daemon.py` `dispatch_request` raises `NotImplementedError`
  for the image tier ("inline in `_handle_client` until Task 12"). Adding md5/size to the
  image render result (AC2) lands in code explicitly in flux; the wiring target is
  unstable. *Found by TEA during test design.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Architect (reconcile)
- **Drop `md5`/`size_bytes`; daemon out of scope**
  - Spec source: context-story-65-2.md, AC2 (prior rev) + Doctor decision 2026-05-27 "expand scope to daemon"
  - Spec text: "the daemon owns the bytes at R2-upload time, so it computes and returns `md5` + `size_bytes` in the image render result … ledger columns are therefore NOT NULL"
  - Implementation: ledger stores neither column; content sha256 is already embedded in `r2_key` (`artifacts/<world>/<session>/<kind>/<sha256>.<ext>`, `r2_writer.py:91`), so it is persisted for free via the PK; `size_bytes` has no resume consumer
  - Rationale: avoids a redundant second hash and an unnecessary change to in-flux image-tier daemon code (`dispatch_request` NotImplementedError, "Task 12"); reuse-first
  - Severity: major (reverses a Doctor decision on new evidence — flagged for veto)
  - Forward impact: `sidequest-daemon` exits scope; `size_bytes` re-addable in the AC6 follow-up if a consumer appears
- **AC6 (ledger↔manifest audit) deferred to a follow-up**
  - Spec source: context-story-65-2.md, AC6 (prior rev)
  - Spec text: "extends `audit()`/`AuditResult`: detects orphans (in manifest/R2…) and dangling rows (ledger row whose `r2_key` is absent from the manifest)"
  - Implementation: AC6 removed from 65-2; no RED test written for it; filed as "Runtime-artifact R2 audit" follow-up
  - Rationale: ledger keys (`artifacts/…`) and manifest keys (`genre_packs/…`) are disjoint namespaces (`r2_writer.py:196`), so the diff is all-noise; a real audit needs an R2-listing capability that does not exist + an undesigned retention policy
  - Severity: major (removes an AC cluster)
  - Forward impact: `scripts/` + `sidequest-content` exit scope; follow-up story owns runtime-artifact retention + R2 listing
- **Repos reduced to server + ui**
  - Spec source: epic-65.yaml 65-2 `repos: server,content,daemon,ui`
  - Spec text: "repos: server,content,daemon,ui"
  - Implementation: effective scope is `server, ui`; SM to update the field and retire the unused `feat/65-2-*` branches in `sidequest-daemon` and `sidequest-content`
  - Rationale: consequence of the two deviations above
  - Severity: minor
  - Forward impact: fewer branches to finish/merge at story close

### TEA (test design)
- **AC6 has no RED test (descoped)**
  - Spec source: context-story-65-2.md, AC6 (current rev)
  - Spec text: "AC6 — DEFERRED, not in this story. … No RED test is written for AC6 here; it moves to a follow-up story"
  - Implementation: no test authored for the ledger↔manifest audit; tracked as a DESCOPED AC, not a coverage gap
  - Rationale: the audit is incoherent against disjoint R2 namespaces and depends on a non-existent R2-listing capability (see Architect reconcile)
  - Severity: minor
  - Forward impact: follow-up story "Runtime-artifact R2 audit" owns it
- **Two RED tests pass vacuously (non-discriminating until GREEN)**
  - Spec source: context-story-65-2.md, AC3 + AC4
  - Spec text: "Unknown slug → 404 (loud)" / "The legacy local-tmpdir branch (`r2_key` falsy) writes no ledger row"
  - Implementation: `test_get_assets_404_for_unknown_slug` passes in RED because the route is absent (all paths 404); `test_render_without_r2_key_writes_no_ledger_row` passes because the hook is absent (MagicMock `.called` is False). Both remain valid, meaningful assertions once GREEN lands.
  - Rationale: kept deliberately — they guard the GREEN behavior; a RED-only failure isn't required for every assertion
  - Severity: trivial
  - Forward impact: none
## TEA Assessment

**Tests Required:** Yes
**Phase:** red — RED confirmed (failing, ready for Dev)

**Earlier blocking findings:** RESOLVED by the Architect reconciliation (2026-05-27) —
md5/sha256, disjoint-namespace AC6, and the daemon mid-refactor are all dispositioned in
the context + Design Deviations. RED was written against the reconciled context (scope:
server + ui).

**Test Files:**
- `sidequest-server/tests/persistence/test_pg_asset_ledger.py` — AC1 (table shape via
  migration; no md5/size; r2_key PK; FK) + AC2 (`PgAssetLedgerStore` upsert, isolation,
  injection-safety)
- `sidequest-server/tests/server/test_rest_session_assets.py` — AC4
  (`GET /api/sessions/{slug}/assets` round-trip, 404-on-unknown-slug, empty-list)
- `sidequest-server/tests/server/test_asset_ledger_write_wiring.py` — AC3 (mandatory
  wiring: ledger write fires from `_run_render_inner` on an r2_key reply + OTEL watcher
  event; local-only render writes nothing)
- `sidequest-ui/src/hooks/__tests__/useAssetPreload.test.ts` — AC5 (reconnect-edge fetch
  of the asset endpoint → preload callback; no fetch w/o slug; no double-fetch)

**Tests Written:** 20 (15 server + 5 ui) covering AC1–AC5. AC6 descoped (deferred).
**Status:** RED — 9 failed, 5 errors (missing-module fixtures), 2 vacuous-pass (noted as
deviations), UI collection error (missing hook). All trace to missing implementation.
**Env note:** the pg suite requires `SIDEQUEST_TEST_DATABASE_URL` (e.g.
`postgresql://$USER@localhost:5432/sidequest_test`, provisioned by `just pg-up`) — same
precondition as every existing `tests/persistence/*` test.

### Rule Coverage (lang-review)

| Rule (python.md / ts) | Test(s) | Status |
|------|---------|--------|
| #6 test quality — meaningful assertions | all assert specific values; 2 non-discriminating-in-RED flagged as deviations | satisfied |
| #11 parameterized SQL (no f-string injection) | `test_injection_safe_entity_ref_roundtrips_literally` | failing (RED) |
| #11 boundary validation — unknown input loud | `test_get_assets_404_for_unknown_slug` (404, not silent-empty) | green-vacuous in RED |
| #1 no silent fallback — local render writes nothing | `test_render_without_r2_key_writes_no_ledger_row` | green-vacuous in RED |
| OTEL principle — subsystem decision emits span | `test_render_ledger_write_emits_watcher_event` | failing (RED) |
| Wiring (CLAUDE.md) — fires from production path, no source-grep | `test_render_with_r2_key_writes_asset_ledger` (drives `_run_render_inner`) | failing (RED) |
| FK / PK integrity | `test_r2_key_is_primary_key`, `test_dangling_session_id_rejected` | failing (RED) |
| cross-session isolation | `test_cross_session_isolation` | error (missing module) |

**Rules checked:** Python #1, #6, #11 + OTEL + wiring + integrity have coverage.
**Self-check:** no `assert True` / `let _ =` / always-None assertions; the two
non-discriminating-in-RED tests are intentional GREEN guards, logged as trivial deviations.

### Contract defined for Dev (GREEN)
- `sidequest.game.pg.asset_ledger.PgAssetLedgerStore(pool, *, session_id)` with
  `.append(r2_key, asset_type, entity_ref, created_turn)` (upsert on r2_key) and
  `.list_assets()`.
- `PgSaveRepository.append_asset_ledger(...)` composing the store (mirrors
  `append_scrapbook_entry`).
- New Alembic revision (down_revision `0001`) creating `asset_ledger`.
- `GET /api/sessions/{slug}/assets` in `rest.py` (resolve slug→session_id; 404 on miss).
- Ledger write + `state_transition field=asset_ledger op=write` watcher event in
  `_run_render_inner` when the reply carries `r2_key`.
- `sidequest-ui` `@/hooks/useAssetPreload` ({slug, connected, onAssets}) fetching the
  endpoint on the (re)connect edge.

### Delivery Findings (red phase)
- No new upstream findings during test design (the three blocking findings were resolved
  pre-RED by the Architect reconciliation).

**Handoff:** To Dev for implementation.
