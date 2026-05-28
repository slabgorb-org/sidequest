# Story 65-5 Context

## Title
Asset generators skip files already on R2 (live-listing existence check)

## Metadata
- **Story ID:** 65-5
- **Type:** chore
- **Points:** 2
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** orchestrator (`.`) — base branch `main`
- **Epic:** Content Infrastructure — R2 asset tracking and audit

## Problem
The asset-generation scripts decide whether to (re)generate by checking **local
disk only**. In `scripts/render_common.py:502-504`:

```python
# Skip if already generated (unless --force)
if out_path.exists() and not force and not dry_run:
    log.info("[%d/%d] SKIP %s/%s (already exists)", ...)
```

Generated PNGs are gitignored (they live on R2 / cdn.slabgorb.com, not in git).
So on any clone that did not generate the images locally — e.g. the OQ-2 clone,
or a fresh checkout — `out_path.exists()` is `False` for everything, the gate
fires "missing", and the script regenerates assets **that are already on R2**.
This burns GPU time, wall-clock, and (for any paid render path) money, and it is
the concrete pain that motivated all of epic 65's "what's done vs. what needs
doing" framing.

`scripts/generate_poi_images.py:167` is the worst offender — it hardcodes
`force=True` ("POIs don't have --force flag, always regenerate"), so POIs are
**unconditionally** regenerated regardless of local OR remote state.

## Technical Approach
Make generation **idempotent against R2** — the standard "skip what already
exists in the remote store" pattern. All code is in the **orchestrator**
`scripts/` tree; this does **not** touch the runtime `asset_ledger` (that is
65-2's per-session runtime-image concern and a different namespace).

1. **Live R2 listing helper.** Add a function (in `render_common.py`, or a small
   shared helper it imports) that lists the live bucket under a given
   `genre_packs/<...>` prefix using boto3 `list_objects_v2` with a paginator,
   returning a `set[str]` of existing keys. **Reuse `_build_client()` from
   `scripts/r2_sync_packs.py:72`** — do not introduce a second client.
2. **Expected-key mapping.** Map each render item to its expected R2 key using
   the same 1:1 relative-path convention `r2_sync_packs` uploads with
   (`key = path.relative_to(content_root).as_posix()`, i.e. `genre_packs/...`),
   so the existence check compares like-for-like with what is actually on R2.
3. **Extend the skip gate** at `render_common.py:502-504`: skip the item when
   `out_path.exists()` **OR** its expected R2 key is in the existing-set —
   unless `--force` or `dry_run`. Log the remote-skip distinctly
   (`SKIP (on R2)`).
4. **Fix the POI generator.** Remove the `force=True` hardcode in
   `generate_poi_images.py:167`; add a `--force` flag mirroring
   `generate_portrait_images.py` so POIs get the same skip-by-default + explicit
   override behavior.
5. **Loud failure, no silent fallback.** If R2 listing fails (missing
   `R2_S3_ENDPOINT`/creds, or a `ClientError`), abort with a clear error rather
   than silently falling back to "regenerate everything" — per CLAUDE.md
   No-Silent-Fallbacks. (An explicit offline escape hatch may be added if
   wanted, but the *default* must be loud failure, not silent mass-regen.)

## Scope
- **In scope:** `scripts/render_common.py` (R2 listing helper + skip gate),
  `scripts/generate_poi_images.py` (drop `force=True`, add `--force`). Aligning
  any sibling generator (`generate_portrait_images.py`,
  `generate_creature_images.py`) that routes through `render_common` so they
  inherit the new skip behavior consistently.
- **Out of scope:** the runtime `asset_ledger` (PG, 65-2); ledger↔R2
  reconciliation; any retention/reaping/deletion of R2 objects; the
  `artifacts/` runtime namespace. This story is read-only against R2 (LIST
  only — never PUT/DELETE).

## Acceptance Criteria
1. `render_common` builds a set of existing R2 keys via a single paginated
   `list_objects_v2` over the target `genre_packs/` prefix at run start, reusing
   the boto3 client from `scripts/r2_sync_packs._build_client()`.
2. The skip gate in `render_common` skips any render item whose expected R2 key
   is in the existing-set, even when the local file is absent (logs
   `SKIP (on R2)`); unless `--force`/`dry_run`.
3. `--force` overrides the R2 skip and regenerates regardless, preserving
   existing `--force` semantics.
4. `generate_poi_images.py` no longer hardcodes `force=True`; POIs honor the
   same R2 skip and gain a `--force` flag matching
   `generate_portrait_images.py`.
5. Expected-key mapping uses the `r2_sync` 1:1 relative-path convention
   (`genre_packs/...`) so keys align with what `r2_sync_packs` actually uploads.
6. R2 listing failure (missing creds/endpoint or `ClientError`) aborts loudly
   with a clear error — no silent fallback to "regenerate everything" (per
   CLAUDE.md No-Silent-Fallbacks).

## Test Strategy Notes (for TEA)
- The R2 client is injectable: `r2_sync_packs._build_client()` is the seam, and
  the codebase already uses the `patch.object(..., "_client", ...)` idiom for
  boto3 in tests (see daemon `r2_writer` tests and `scripts/tests/`). Inject a
  fake S3 client whose paginator returns canned `Contents` pages — no live R2.
- **Core behavioral test:** given a fake listing that contains an item's
  expected key but with the local file ABSENT, assert the generator SKIPs it.
  This is the regression that pins the bug. Pair with the inverse (key absent →
  generates) and `--force` (key present → still generates).
- **Loud-failure test:** make the listing raise / creds missing → assert the run
  aborts (raises / non-zero), not "regenerate everything".
- Existing test conventions live in `scripts/tests/` (`test_r2_audit.py`,
  `test_r2_sync_packs.py`) — match their style and the orchestrator
  `pyproject.toml` pytest setup.

## History
Replaces the original 65-5 framing ("Runtime-artifact R2 audit — ledger vs
artifacts/ R2 listing + retention policy"), which was the descoped AC6 from
65-2. That framing solved the wrong problem: it audited *runtime* images
(`artifacts/{world}/{session}/...`) and proposed a retention policy, none of
which answers "stop regenerating authored pack assets already on R2." Reframed
2026-05-28 by the Architect after the boss identified the real pain (gitignored
PNGs → non-idempotent generation). The runtime-ledger reconciliation, if ever
needed, can be re-filed separately.

---
_Reframed 2026-05-28. Supersedes the auto-generated stub._
