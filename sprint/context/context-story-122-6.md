# Story 122-6 Context

## Title
Rename asset_url OTEL span `server.asset_url.resolved` → `foundation.asset_url.resolved` to match emitting tier

## Overview
This is an ADR-147 honesty follow-up. The OTEL span for asset-URL resolution is currently named `server.asset_url.resolved`, but the function that emits it lives in the `foundation` tier (`sidequest/foundation/asset_urls.py`), not the `server` tier. Rename the span to accurately reflect its source tier, and update the two tests in `tests/server/test_asset_urls.py` that assert on this span name.

## Metadata
- **Story ID:** 122-6
- **Epic:** 122 (Honest Layering)
- **Points:** 1
- **Workflow:** trivial
- **Repo:** server
- **Priority:** p3

## Technical Details

### Current State
- Span name: `server.asset_url.resolved` (line 14 of `sidequest/telemetry/spans/asset_url.py`)
- Emitting function: `resolve_asset_url` in `sidequest/foundation/asset_urls.py` (line 71)
- The foundation tier is below the server tier per ADR-147 layering; the span name should reflect this

### Acceptance Criteria
1. Rename `SPAN_ASSET_URL_RESOLVED` constant in `sidequest/telemetry/spans/asset_url.py` from `"server.asset_url.resolved"` to `"foundation.asset_url.resolved"`
2. Update test assertions in `tests/server/test_asset_urls.py` that explicitly check for the span name (lines 118–147):
   - `test_resolve_asset_url_defaults_scope_pack` (line 126)
   - `test_resolve_asset_url_accepts_shared_scope` (line 145)
3. All tests pass; no functional change to the asset URL resolution logic itself
4. `just server-check` passes (ruff + pytest + pyright)

## Files to Change
- `sidequest-server/sidequest/telemetry/spans/asset_url.py` (rename constant, 1 line change)
- `sidequest-server/tests/server/test_asset_urls.py` (update 2 test assertions, search string in span_attrs_by_name calls)

---
_Generated from sprint YAML for 122-6._
