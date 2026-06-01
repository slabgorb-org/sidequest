---
story_id: "65-8"
jira_key: ""
epic: "65"
workflow: "tdd"
---
# Story 65-8: Lore POI gallery — feed geography renderer from history.yaml, manifest-gated images

## Story Details
- **ID:** 65-8
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 65 — Content Infrastructure — R2 asset tracking and audit
- **Points:** 3
- **Type:** feature
- **Repo:** sidequest-server

## Story Context

Epic 65 replaces git-LFS pointer tracking for the dual-repo (OQ-1/OQ-2) workflow. This story wires the POI image gallery into the lore reference pages, feeding the existing `present_lore_geography` card renderer from `history.yaml:points_of_interest` entries and gating image display on manifest presence.

### Background: What Already Exists

The infrastructure is **95% complete** — this is a **wire-up, not a build** (per the design spec ADR-135 §2):

- **POI card renderer:** `_poi_image_html()` + `present_lore_geography()` in `reference_presenters.py` are fully implemented and emit POI cards with image tags, OTEL watcher spans, and theme-accent styling. The renderer is proven and wired into the live game engine.
- **POI slug source:** `history.yaml:points_of_interest[].slug` is authored in every world. The exact shape (`name / slug / region / type / description / environment`) matches what the presenter consumes.
- **R2 manifest oracle:** Story 65-7 (DONE) populated and committed `sidequest-content/r2_manifest.json` with 1743 entries covering all live R2 assets. The manifest schema is `{key, md5, size_bytes, uploaded_at, source}`.
- **Manifest loader:** `scripts/r2_manifest.py:load_manifest()` exists and is battle-tested by the audit tools. The server will need a Python equivalent (or reuse).

### The Problem

The lore reference page (`GET /reference/lore/{pack}/{world}`) is image-poor:

1. **POI images never appear.** The `_poi_image_html()` emitter only runs inside `present_lore_geography()`, which expects a **list of location dicts**. But in the live worlds (glenross, blackthorn_moor), `lore.yaml:geography` is authored as a **prose string**, not a structured list. So the POI list is never passed to the renderer, and the images go unused.

2. **No existence gate.** The renderer would naively emit `<img src=...>` tags without checking whether the asset exists on R2. This creates broken images (glenross has 13 NPCs in `portrait_manifest.yaml` but **zero** portraits in R2, so naive rendering = 13 broken images). The manifest-gated approach (D2 of ADR-135) requires the asset's R2 key to be present in the manifest before emitting the tag.

3. **POI slug manifest unused.** The slug manifest (`load_poi_image_slugs()`, keyed by `history.yaml:points_of_interest[].slug`) is built correctly by the lore loader but never fed to the image renderer.

### The Solution

Per ADR-135 (decision D3), add a thin "Points of Interest" section presenter that:

1. **Feeds the existing card renderer** from `history.yaml:points_of_interest` — a **presenter-level change**, not a lore model change.
2. **Manifest-gates the `<img>` emitter** on `slug ∈ poi_image_slugs AND slug_key ∈ r2_manifest_keys` — no broken images.
3. **Reuses proven infrastructure** — no new card markup, no new geography logic, just a presenter that bridges history.yaml POIs to the existing card renderer.

### Data Flow (Post-Implementation)

```
GET /reference/lore/{pack}/{world}
    │
    ├─ load r2_manifest.json (cached) → set of live R2 keys, prefix-filtered to this world
    │
assemble_lore_page(pack, world, manifest_keys)
    ├─ hero (world_name)                         [existing]
    ├─ § Points of Interest  ← history.yaml POIs → present_lore_geography
    │        └─ <img> iff slug-key ∈ manifest_keys              [NEW: this story]
    ├─ § Cast                ← npcs.yaml public projection      [65-9]
    │        └─ portrait <img> iff portrait-key ∈ manifest_keys [65-9]
    ├─ § History / Cosmology / Factions / …      [existing]
    └─ TOC wraps sections by corrected PACK_TOC  [65-10]
```

## Acceptance Criteria

### AC1 — Manifest loading and caching
- The lore renderer loads `r2_manifest.json` from the SIDEQUEST_GENRE_PACKS mount point.
- Manifest is loaded once per process and cached (static between deploys).
- Failure to load the manifest (file absent, JSON malformed) aborts loudly with an informative error — no silent fallback to "render imageless."

### AC2 — POI section presenter
- A new presenter (or extension to existing) feeds `history.yaml:points_of_interest` entries to the existing `present_lore_geography()` card renderer.
- The POI list is independent of the prose `lore.yaml:geography` field (both may render, or only the prose may exist, or both are absent — no coupling).
- Entries must carry the exact shape the renderer expects: `{name, slug, region, type, description, environment}`.

### AC3 — Manifest-gated image emission
- POI image `<img>` tags are only emitted when the expected R2 key (`.../worlds/{world}/assets/poi/{slug}.png`) is present in the loaded manifest.
- Emits an `<img>` tag with the resolved CDN URL from `resolve_asset_url()` (existing seam).
- Logs `SKIP (not in manifest)` as an OTEL `reference_poi_image_*` span (reusing existing span family) for audit trail.

### AC4 — TOC registration
- A "Points of Interest" section is registered in the page's table of contents (via `PACK_TOC` / `TOC_TO_FILES` or the rendering engine's section tracking).
- The section is only shown when POI entries exist in history.yaml.
- The TOC entry does not appear for worlds with no POIs (e.g., if a world has no `history.yaml:points_of_interest`, the section is omitted).

### AC5 — Two-reader presentation principle
- POI type (e.g., "tavern", "monument", "hideout") is surfaced as a **visible chip/badge** alongside the description, not buried in prose — per ADR-135 D7 (the mechanical reader, Sebastien/Jade, should see the gears).
- Region and environment are rendered legibly (not as raw YAML keys).

### AC6 — OTEL observability
- Every manifest load emits a `reference_manifest_loaded` span with: path, entry count, world prefix filter result.
- Each POI image decision (resolved | not-in-manifest | slug missing from poi_image_slugs) emits a `reference_poi_image_*` span reusing the existing span family.

### AC7 — Wiring proof
- Integration test: render the reference page for a pilot world (`blackthorn_moor`, which has both live POI images and non-zero history.yaml POIs), assert the POI section renders with at least one image tag and no broken `<img>` tags.
- Negative test: render for a zero-portrait world (glenross), assert POI section renders (if POIs exist in history.yaml) with **zero `<img>` tags** (not broken images).
- No visual regressions in existing sections (history, cosmology, factions, etc.) — the POI section is prepended/appended without disrupting the layout.

## Technical Approach

### 1. Manifest Loading
- Load `r2_manifest.json` from the SIDEQUEST_GENRE_PACKS root at server startup or on first lore-page access.
- Parse as `dict[str, {key, md5, size_bytes, uploaded_at, source}]`.
- Cache as a module-level or request-scoped singleton (verify no cache-invalidation bugs if manifest is updated live; static-between-deploys assumption is OK for now).
- Fail loud if the file is absent or malformed.

**Candidate approach:** Add a `load_manifest()` function in `reference_renderer.py` or a new `reference_manifest.py` module (mirrors `scripts/r2_manifest.py` design pattern). Call it from `assemble_lore_page()` or the route handler, cache the result.

### 2. POI Section Presenter
- Extend `reference_presenters.py` with a new presenter (or enhance an existing one) that:
  - Takes `history.yaml:points_of_interest` entries (a list of dicts).
  - Calls `present_lore_geography(locations=poi_list, ...)` with the POI entries as the location list.
  - Returns the rendered section HTML.
- Wire this presenter into `assemble_lore_page()` as a new section (or extend the `geography` section to include both prose and POI entries, if the lore loader already handles both).

**Implementation location:** `reference_presenters.py`, new function e.g. `present_lore_poi_gallery(...)` or extend `present_lore_geography` to be called twice (once for prose, once for history POIs).

### 3. Manifest-Gated Image Emission
- The existing `_poi_image_html()` function already calls `resolve_asset_url()` to emit image tags. Gate the emission by checking the resolved key against the loaded manifest **before** emitting the `<img>` tag.
- If the key is not in the manifest, skip the `<img>` tag but emit an OTEL span for audit.
- If the key is in the manifest, emit the tag and an OTEL span.

**Implementation:** In the POI presenter or in `_poi_image_html()`, add a manifest-check parameter or a context variable. Only emit `<img>` when `manifest.get(expected_key) is not None`.

### 4. TOC Registration and Conditional Rendering
- Add a "Points of Interest" entry to `PACK_TOC` and `TOC_TO_FILES` for packs that have POI-bearing worlds.
- The section only appears in the rendered output if `history.yaml:points_of_interest` is non-empty for that world.
- Use the existing TOC rendering logic (no new markup).

### 5. OTEL Spans
- Add `reference_manifest_loaded` span (fired once per route) with metadata: manifest path, entry count, world-specific key count.
- Reuse `reference_poi_image_resolved` and `reference_poi_image_not_in_manifest` spans (existing span family from ADR-031/090) for each POI image decision.

### 6. Test Structure (TDD: RED phase)
- **Unit test:** manifest loading — file present/absent, valid/malformed JSON, key lookup.
- **Unit test:** POI list presenter — feeds correct shape to the geography renderer.
- **Unit test:** manifest-gated `<img>` emission — verify `<img>` tag appears iff key in manifest.
- **Integration test:** full lore-page render for `blackthorn_moor` (POIs + images), assert POI section present with correct image count.
- **Negative test:** `glenross` (POIs but no images), assert section renders with zero `<img>` tags.
- **Regression test:** existing sections (history, cosmology, factions) render unchanged.

## Pilot / Verification World

**blackthorn_moor** — the only world with **both** live POI images and live NPCs in R2. Proves both image paths end-to-end.
**glenross** — negative test: POIs yes, portraits no. The manifest gate must suppress missing portraits cleanly (zero broken images).

## Dependencies

- **Story 65-7** (DONE) — manifest must be populated and committed before this story starts (not just the code, but the actual artifact).
- No blocking runtime dependencies. The infrastructure (manifest schema, R2 keys, existing presenters) is complete.

## Out of Scope

- Portrait rendering / Cast section (story 65-9).
- TOC data repair for tea_and_murder beyond registering the new section (story 65-10).
- Map view or timeline (stories 65-11, 65-12 — follow-on slices).
- Markdown-in-YAML rendering, cross-pack search, or inline authoring.

## Design Notes

**Public Projection Only:** The reference pages render the **public** projection (ADR-135). POI type, region, and environment are public mechanical facts (no secrets here); description is public prose. No `?audience` parameter, no GM mode, no toggles.

**Reuse, Don't Rebuild:** The `present_lore_geography()` renderer, the `_poi_image_html()` emitter, the `resolve_asset_url()` seam, and the OTEL span families already exist. The load-bearing work is **integration**, not new code.

---

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-01T20:10:42Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-01T00:00:00Z | 2026-06-01T15:04:05Z | 15h 4m |
| red | 2026-06-01T15:04:05Z | 2026-06-01T19:42:00Z | 4h 37m |
| green | 2026-06-01T19:42:00Z | 2026-06-01T19:50:17Z | 8m 17s |
| spec-check | 2026-06-01T19:50:17Z | 2026-06-01T19:52:27Z | 2m 10s |
| verify | 2026-06-01T19:52:27Z | 2026-06-01T19:59:33Z | 7m 6s |
| review | 2026-06-01T19:59:33Z | 2026-06-01T20:09:05Z | 9m 32s |
| spec-reconcile | 2026-06-01T20:09:05Z | 2026-06-01T20:10:42Z | 1m 37s |
| finish | 2026-06-01T20:10:42Z | - | - |

## Sm Assessment

Selected 65-8 as the next thread in epic 65 — highest priority (p1), unblocked (no `depends_on`), board clear (0 in progress, 0 in review). Its twin 65-9 (Lore Cast section) is the natural follow-on; both share the manifest-gated-image pattern established by 65-7 (DONE, the R2 manifest oracle).

This is a **wire-up, not a build**: the POI card renderer (`present_lore_geography` / `_poi_image_html`), the slug source (`history.yaml:points_of_interest`), and the committed manifest oracle (`r2_manifest.json`, 1743 entries) all exist. The work is connecting the prose-vs-list geography gap and gating image emission on manifest presence so glenross (POIs but no R2 images) renders zero broken `<img>` tags while blackthorn_moor (live images) renders the gallery.

Scope is single-repo (sidequest-server), 3 pts, phased TDD. Seven ACs authored, including AC6 (OTEL: reuse `reference_poi_image_*` span family + new `reference_manifest_loaded` span) honoring the OTEL Observability Principle, and AC7 (wiring proof — non-test consumer reachable from the live `/reference/lore/{pack}/{world}` path). Manifest-gating directly serves Genre-Truth presentation: no broken images leaking into a player-facing surface.

Handing off to TEA (Hamlet) for the RED phase. Routing only — implementation belongs to the next agents.

## Delivery Findings

No upstream findings at setup time.

<!-- TEA findings below this marker; append-only -->

### TEA (test design)

- **Conflict** (non-blocking): The 65-8 session "Problem" narrative describes a pre-63-8 world — its problems #1 ("POI images never appear") and #3 ("POI slug manifest unused") were already solved by story **63-8**, which is merged and green (12 tests pass). The renderer already threads `history.yaml` POI slugs into `present_lore_geography` and emits an `<img>` per *authored* POI. The genuine net-new core of 65-8 is the **R2-manifest existence gate** only. Re-scoped with the boss's approval (see deviation below). Affects the story framing, not code.
- **Improvement** (non-blocking): AC5 (POI **type** as a visible chip) is **already delivered** by 63-8 — the live card markup renders `<span class="ref-chip">Ruin</span>` / region chips (confirmed in the RED failure output for `sunken-vault`). No new work needed for AC5. Affects `reference_presenters.py` (no change required).
- **Gap** (blocking for Dev/GREEN): AC1's fail-loud-on-absent makes `r2_manifest.json` a **hard dependency of lore rendering**. Any lore-page test path that renders without a manifest at `pack_dir.parent.parent/r2_manifest.json` will 500 once the gate lands. The fixture manifest `tests/fixtures/r2_manifest.json` covers the `reference_v2_fixture` root (includes the 63-8 `vaskov-centrum` key so that suite stays green), but Dev must audit every other lore-rendering test/fixture for a manifest and decide the contract for *content roots that legitimately lack one*. Affects `assemble_lore_page` + any lore-render fixtures (`tests/fixtures/**`, tmp-pack lore tests).
- **Question** (non-blocking): AC4 (a *separate* "Points of Interest" TOC section) is ambiguous — 63-8 folds POI images **into** existing geography/location cards rather than a distinct TOC section. The re-scope drops AC4 from RED. If a standalone POI TOC section is actually wanted, it is a separate slice (closer to 65-11's map view). Affects TOC registration in `reference_renderer.py`; deferred, no test written.

### Reviewer (review)

- **Gap** (non-blocking): No **end-to-end** loud-fail test — a POI-bearing world with an absent `r2_manifest.json` should 500 at `GET /reference/lore/...`, not render imageless. Behavior is correct (FileNotFoundError propagates) and unit-tested, but the route-level No-Silent-Fallback proof is missing. Affects `tests/server/test_reference_poi_manifest_gate.py` (add a route test with a manifest-less content root). *Found by Reviewer during code review.*
- **Gap** (non-blocking): The second loud-fail branch — a manifest list entry that is a dict **missing `key`** — is uncovered. Affects `tests/server/test_reference_poi_manifest_gate.py` (add `test_load_manifest_entry_missing_key_raises_loudly`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_lore_render_fires_manifest_loaded_span_once` asserts `entry_count >= 1`; tighten to `== 2` (exact fixture count) so it also proves the gate read the fixture manifest, not the prod one — guarding the `pack_dir.parent.parent` resolution. Affects the same test file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Three docstring fixes — `_gate_poi_slugs_on_manifest` "one span per render" (false for POI-less worlds), `load_r2_manifest_keys` "once per process" (imprecise vs lru_cache), and `poi_image_key` (document raw-key-vs-resolved-URL). Affects `reference_renderer.py`, `reference_presenters.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Two test-file type annotations — `_entry -> dict[str, object]`, `gated_client -> Iterator[TestClient]`. *Found by Reviewer during code review.*
- **Gap** (non-blocking, operational): `load_r2_manifest_keys` is `@lru_cache`'d with no mtime/TTL — a manifest regenerated after an asset upload is not picked up until server restart (safe-failing: text-only, never broken). Needs a runbook note, or a future mtime-keyed cache. Affects `reference_renderer.py` + asset-gen runbook. *Found by Reviewer during code review.*

**Recommendation:** all of the above are best folded into **65-9** (Cast portraits), which will reuse this exact manifest-gate pattern. None block this PR.

### Dev (implementation)

- **Resolved** the TEA blocking Gap (manifest hard-dependency / blast radius): scoped the loud-fail manifest load to POI-bearing worlds only (see Dev deviation). Full server suite re-run clean — **9524 passed, 362 skipped, 0 failed** — so no lore-render fixture needed a manifest backfill. Affects `assemble_lore_page` (`_gate_poi_slugs_on_manifest` early-return).
- **Improvement** (non-blocking): 65-9 (Cast portraits) faces the identical "authored-but-not-on-R2 → broken image" problem and should reuse `load_r2_manifest_keys` + the `pack_dir.parent.parent/r2_manifest.json` discovery rule + the gate-only-when-present shape. The `_poi_image_key` helper has a direct `_portrait_key` analog. Affects future `reference_presenters.py`/`reference_renderer.py` Cast work. *Found by Dev during implementation.*
- **Gap** (non-blocking): the real `sidequest-content/r2_manifest.json` (415 KB, committed by 65-7) is the production oracle; if it goes stale relative to actual R2 (e.g. a POI image is uploaded but the manifest isn't regenerated), that POI silently renders text-only. That's the safe failure (no broken image), but operators should regenerate the manifest after asset uploads. No code change needed; flagged for the asset-gen runbook. *Found by Dev during implementation.*

## Design Deviations

<!-- Each agent appends under its own subsection. Append-only. -->

### TEA (test design)

- **Re-scoped 65-8 from the full 7-AC frame to the R2-manifest existence gate**
  - Spec source: `.session/65-8-session.md` (Acceptance Criteria AC1–AC7) vs. implemented reality (story 63-8, merged/green)
  - Spec text: AC2 "feed `history.yaml:points_of_interest` to the existing `present_lore_geography()` renderer"; AC5 "POI type surfaced as a visible chip/badge"
  - Implementation: RED tests written ONLY for AC1 (manifest loader), AC3 (manifest existence gate), AC6 (`manifest_loaded` span), AC7 (gated-world wiring). No tests written for AC2 (covered green by 63-8's `test_reference_poi_images.py`), AC5 (chip already live), or AC4 (separate POI TOC section — ambiguous/deferred). Writing duplicate tests for already-green 63-8 behavior would be vacuous per python-review check #6 (test quality) and not true RED.
  - Rationale: The boss explicitly chose "Re-scope to manifest gate" when presented the 63-8 overlap. The net-new, player-facing value is exclusively "stop emitting broken `<img>` for authored-but-not-on-R2 POIs."
  - Severity: major
  - Forward impact: GREEN-phase Dev should implement only the manifest loader + gate + span; the presenter/TOC/chip surfaces are untouched. Reviewer should NOT expect AC2/AC4/AC5 code in this PR. If a standalone POI TOC section is later wanted, file a follow-on slice.
- **Pinned the manifest-discovery path and loader contract as a TEA design decision**
  - Spec source: `context-story-65-8.md` (Technical Guardrails) + session AC1/AC3
  - Spec text: "loads `r2_manifest.json` from the SIDEQUEST_GENRE_PACKS mount point"; "expected R2 key … `.../worlds/{world}/assets/poi/{slug}.png`"
  - Implementation: Tests pin (a) the loader as `sidequest.server.reference_renderer.load_r2_manifest_keys(Path) -> frozenset[str]`, and (b) manifest discovery at `pack_dir.parent.parent / "r2_manifest.json"` (prod → `sidequest-content/r2_manifest.json`; fixture → `tests/fixtures/r2_manifest.json`). The session left the module home and discovery rule unspecified.
  - Rationale: Route/integration tests need a deterministic, plumbing-stable contract; `pack_dir.parent.parent` is the single rule that resolves correctly in both prod and fixture layouts.
  - Severity: minor
  - Forward impact: Dev may relocate the loader to a new module (e.g. `reference_manifest.py`) but must keep the import path importable or update the three loader-test imports; the discovery rule is load-bearing for the route tests and should not change without updating the fixture manifest location.

### Dev (implementation)

- **Manifest is required only when a world authors POIs — not a hard dependency of every lore render**
  - Spec source: `.session/65-8-session.md` AC1 + TEA Delivery Finding (Gap, blocking): "fail-loud-on-absent makes `r2_manifest.json` a hard dependency of lore rendering … 500 once the gate lands."
  - Spec text: AC1 "Failure to load the manifest (file absent, JSON malformed) aborts loudly … no silent fallback to 'render imageless.'"
  - Implementation: `_gate_poi_slugs_on_manifest` returns early (`frozenset()`) when the world authors **no** POIs, *before* discovering or loading the manifest. The loud-fail manifest load fires only for POI-bearing worlds (the only ones that could emit a broken image). POI-less lore pages never consult the manifest.
  - Rationale: Kept No-Silent-Fallbacks exactly where it matters (a POI-bearing world with a missing manifest still aborts loud) while avoiding a ~15-file blast radius (every existing lore-render test/tmp-pack/real-content path that renders a POI-less world would otherwise 500). This *resolves* the TEA blocking Gap finding without auditing/adding a manifest to every lore fixture.
  - Severity: minor
  - Forward impact: A world that authors POIs but legitimately has no manifest at its content root will 500 (intended, loud). 65-9 (Cast portraits) should reuse this same "gate the resource only when the feature is present" shape. No sibling-story assumption is broken.

### Reviewer (audit)

All logged deviations reviewed; every one stamped below. No undocumented spec deviations found in the diff.

- **TEA: Re-scoped 65-8 from the 7-AC frame to the R2-manifest existence gate** → ✓ **ACCEPTED**: the boss explicitly approved the narrowing; the dropped ACs (AC2/AC5 already shipped by green 63-8; AC4 ambiguous/deferred) left no footprint in the diff, and the surviving core (AC1/AC3/AC6/AC7) is faithfully implemented and tested. Re-scope is sound and traceable.
- **TEA: Pinned the manifest-discovery path (`pack_dir.parent.parent`) and loader contract** → ✓ **ACCEPTED**: resolves correctly in both prod (`sidequest-content/r2_manifest.json`) and fixture layouts; consistent with how `reference_routes` already resolves pack/world dirs. Positional fragility noted in Devil's Advocate but acceptable for the established layout — not a blocker.
- **Dev: Manifest required only when a world authors POIs** → ✓ **ACCEPTED**: the strongest design call in the PR — preserves No-Silent-Fallbacks exactly where a broken image could occur (POI-bearing world → loud-fail) without coupling every lore render to the manifest. Verified the full suite stays green with no fixture backfill. Endorsed; 65-9 should reuse it.

### Architect (reconcile)

Reviewed all prior deviation entries (TEA ×2, Dev ×1) against the diff and the live code — spec sources exist, quoted text is accurate, and each "Implementation" line matches the shipped code (`if not authored_slugs:` at `reference_renderer.py:1180`; `pack_dir.parent.parent / "r2_manifest.json"` at :1182). No correction notes needed. Two spec divergences were identified at spec-check but never recorded in the 6-field deviation manifest — formalized here so the audit is complete from the session file alone.

- **AC6 `manifest_loaded` span fires once per *render*, not once per *manifest load***
  - Spec source: `.session/65-8-session.md`, AC6
  - Spec text: "Every manifest load emits a `reference_manifest_loaded` span with: path, entry count, world prefix filter result."
  - Implementation: `load_r2_manifest_keys` is `@lru_cache`'d, so the physical file *load* happens at most once per process per path; the span is emitted in `_gate_poi_slugs_on_manifest` on **every POI-bearing render** (`reference_renderer.py:1186`), reporting the (possibly cached) key set used by that render.
  - Rationale: A cache-miss-only span would go dark after the first render, defeating per-render GM-panel observability. Per-render emission is the correct granularity and a strict improvement over the literal spec; ratified at spec-check (Option A).
  - Severity: minor
  - Forward impact: none. 65-9's portrait-manifest gate should emit its span the same way (per-render, not per-load).
- **AC6/AC3 image-decision observability uses the existing `poi_image_not_found` span, not a distinct `not_in_manifest` span**
  - Spec source: `.session/65-8-session.md`, AC6 (and AC3's "Logs `SKIP (not in manifest)`")
  - Spec text: AC6 "Each POI image decision (resolved | not-in-manifest | slug missing from poi_image_slugs) emits a `reference_poi_image_*` span"; AC3 "Logs `SKIP (not in manifest)` as an OTEL `reference_poi_image_*` span."
  - Implementation: The gate **excludes** authored-but-absent slugs from `gated_poi_slugs`, so the presenter's existing `reference_poi_image_not_found_span` (Story 63-8) fires for them — the same span as a genuinely un-imaged location. No new `not_in_manifest` span was added; the three-way decision is observable as two spans (resolved / not_found) plus the per-render `manifest_loaded` span (which carries `world_key_count`).
  - Rationale: Honors the boss-approved re-scope directive to *reuse the existing span family* rather than expand it; `poi_image_not_found` truthfully means "this card has no image," which holds for both the not-authored and authored-but-not-on-R2 sub-cases. A distinct span is additive polish, deferred.
  - Severity: minor
  - Forward impact: A GM cannot, from spans alone, distinguish "POI not authored" from "POI authored but not on R2." If that distinction is later wanted (e.g. an authoring-completeness dashboard), add a `reference_poi_image_not_in_manifest` span — tracked in Delivery Findings as a 65-9 fast-follow candidate.

**AC deferral verification (re-scope):** AC2 and AC5 are **DESCOPED — already delivered by merged/green Story 63-8** (presenter wiring; `ref-chip` type/region badges), confirmed against the live diff and the green 63-8 suite. AC4 (a standalone "Points of Interest" TOC section) is **DEFERRED** to a future slice (63-8 folds POI images into existing geography cards; a separate TOC section is closer to 65-11's map view). All three deferrals trace to the boss-approved TEA re-scope and are not invalidated by any Reviewer finding. The delivered core (AC1/AC3/AC6/AC7) is complete and tested.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Net-new behavior (manifest loader, existence gate, new OTEL span) — genuine RED.

**Test Files:**
- `sidequest-server/tests/server/test_reference_poi_manifest_gate.py` — 11 tests (10 net-new RED + 1 green regression guard)
- Fixtures: `tests/fixtures/r2_manifest.json`, `tests/fixtures/packs/reference_v2_fixture/worlds/poi_gated_fixture/{world,locations,history}.yaml`

**Tests Written:** 11 tests covering the re-scoped core (AC1, AC3, AC6, AC7)
**Status:** RED — 10 fail for intended reasons; 1 regression guard passes. Existing 63-8 suite + full reference suite stay green (400 passed, 2 skipped).

**RED breakdown (verified inline, `-n0`):**
| Test | AC | RED reason |
|------|----|-----------|
| `test_load_manifest_keys_returns_key_set` | AC1 | ImportError: `load_r2_manifest_keys` absent |
| `test_load_manifest_absent_file_raises_loudly` | AC1 | ImportError (loader absent) |
| `test_load_manifest_malformed_json_raises_loudly` | AC1 | ImportError (loader absent) |
| `test_load_manifest_wrong_shape_raises_loudly` | AC1 | ImportError (loader absent) |
| `test_load_manifest_is_cached_per_path` | AC1 | ImportError (loader absent) |
| `test_manifest_loaded_span_name_constant` | AC6 | ImportError: `SPAN_REFERENCE_MANIFEST_LOADED` absent |
| `test_manifest_loaded_span_helper_emits_attrs` | AC6 | ImportError: `reference_manifest_loaded_span` absent |
| `test_manifest_loaded_span_registered_flat_only` | AC6 | ImportError: span constant absent |
| `test_authored_but_absent_poi_renders_textonly` | AC3/AC7 | AssertionError: current authorship-gate emits broken `<img src=.../sunken-vault.png>` — **the exact bug** |
| `test_lore_render_fires_manifest_loaded_span_once` | AC6/AC7 | AssertionError: 0 spans (span not emitted yet) |
| `test_manifest_present_poi_gets_image` | AC3 | **Passes** (regression guard: gate must not over-suppress in-manifest art) |

### Rule Coverage

Project rules: `.pennyfarthing/gates/lang-review/python.md` (13 checks). Server CLAUDE.md adds the **No Source-Text Wiring Tests** rule and **No Silent Fallbacks**.

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent-exception / No Silent Fallbacks | `test_load_manifest_absent_file_raises_loudly`, `test_load_manifest_malformed_json_raises_loudly`, `test_load_manifest_wrong_shape_raises_loudly` (absent/malformed/wrong-shape all raise, never silently-empty) | failing (RED) |
| #6 test-quality (no vacuous asserts) | Self-checked — every test asserts a specific value; the absent-POI test asserts on rendered HTML, not a truthy check; no duplication of green 63-8 behavior | n/a (self-applied) |
| #8 unsafe-deserialization | manifest parsed as JSON (not pickle/eval); `test_load_manifest_wrong_shape_raises_loudly` pins structure validation rather than trusting shape | failing (RED) |
| Server: No Source-Text Wiring Tests | Wiring proven via the real `/reference/lore/{pack}/{world}` route (TestClient) + an OTEL `manifest_loaded` span assertion — never `read_text()` greps on source | failing (RED) |
| OTEL Observability Principle (every subsystem decision emits a span) | `test_manifest_loaded_span_*` + `test_lore_render_fires_manifest_loaded_span_once` | failing (RED) |

**Rules checked:** 5 of 13 lang-review checks apply to this test-only RED change (the rest target implementation Dev will write — #2 mutable-defaults, #3 type-annotations, #5 path-handling/`open(encoding=)`, etc. — and become live targets in GREEN).
**Self-check:** 0 vacuous tests. No `assert True`, no bare truthy asserts, no `let _`. The one green-on-arrival test is a deliberate, labeled regression guard, not a vacuous pass.

### Contract handed to Dev (GREEN)

1. `load_r2_manifest_keys(manifest_path: Path) -> frozenset[str]` in `sidequest.server.reference_renderer` — returns `{entry["key"]}`; raises `FileNotFoundError` (absent) / `ValueError` (malformed or non-list shape); cached per path. Mind python-review #5 (`open(..., encoding="utf-8")`, `pathlib`) and #3 (annotate the public signature).
2. `assemble_lore_page` discovers the manifest at `pack_dir.parent.parent / "r2_manifest.json"`, intersects authored POI slugs with manifest presence (`genre_packs/{pack}/worlds/{world}/assets/poi/{slug}.png`), and fires `reference_manifest_loaded_span(path=..., entry_count=..., world_key_count=...)` once per render. The cleanest localization is making `load_poi_image_slugs` (or its caller) manifest-aware so its docstring claim ("slugs that *have* a generated image") becomes true.
3. New span in `sidequest/telemetry/spans/reference.py`: `SPAN_REFERENCE_MANIFEST_LOADED = "sidequest.reference.manifest_loaded"`, helper `reference_manifest_loaded_span(*, path, entry_count, world_key_count, _tracer=None)` via `Span.open`, attrs `reference.manifest_path` / `reference.manifest_entry_count` / `reference.world_key_count`, added to `FLAT_ONLY_SPANS`.
4. **Blast radius (blocking):** the fail-loud manifest makes `r2_manifest.json` mandatory for lore rendering — audit all lore-render fixtures/tests for a manifest before declaring GREEN (see Delivery Findings → Gap).

**Handoff:** To Dev (Puck) for GREEN implementation.
## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/telemetry/spans/reference.py` — new `SPAN_REFERENCE_MANIFEST_LOADED` constant + flat-only registration + `reference_manifest_loaded_span` helper (mirrors the existing POI span helpers).
- `sidequest-server/sidequest/server/reference_renderer.py` — `load_r2_manifest_keys(Path) -> frozenset[str]` (cached, loud-fail); `_poi_image_key()`; `_gate_poi_slugs_on_manifest()`; wired into `assemble_lore_page` (gate authored slugs before threading into the presenter).
- Test assets (from RED): `tests/server/test_reference_poi_manifest_gate.py`, `tests/fixtures/r2_manifest.json`, `tests/fixtures/packs/reference_v2_fixture/worlds/poi_gated_fixture/{world,locations,history}.yaml`.

**Tests:** 11/11 story tests passing (GREEN). Full server suite **9524 passed, 362 skipped, 0 failed**. Reference subset 410 passed, 2 skipped. `ruff check` clean, `ruff format` applied, `pyright` 0 errors on changed files.

**Branch:** `feat/65-8-lore-poi-gallery` (pushed to origin).

**AC coverage (re-scoped core):**
| AC | Status | Where |
|----|--------|-------|
| AC1 manifest loader (loud-fail, cached) | ✅ | `load_r2_manifest_keys` + 5 loader tests |
| AC3 manifest-gated `<img>` | ✅ | `_gate_poi_slugs_on_manifest` + route gate tests |
| AC6 `manifest_loaded` span | ✅ | new span helper + 3 span tests + fires-once route test |
| AC7 wiring (in-manifest shows / authored-absent suppressed) | ✅ | `poi_gated_fixture` through the real `/reference/lore` route |
| AC2 / AC4 / AC5 | n/a | AC2 + AC5 already live (63-8); AC4 deferred (see deviations) |

**Self-review:**
- [x] Wired end-to-end — the gate runs inside `assemble_lore_page`, reachable from the live `GET /reference/lore/{pack}/{world}` route (proven by the route tests, not source greps).
- [x] OTEL observability — `manifest_loaded` span fires per POI-bearing render (the GM-panel lie detector for the gate).
- [x] No Silent Fallbacks — absent/malformed manifest raises; gate suppresses only the image, never the card.
- [x] Minimal blast radius — manifest required only for POI-bearing worlds; full suite green with no fixture backfill.
- [x] Follows project patterns — span helper mirrors siblings; loader mirrors `load_poi_image_slugs` style; `open(encoding="utf-8")` + `pathlib`.

**Handoff:** To verify phase (Hamlet/TEA) — simplify + quality-pass.
## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (re-scoped core faithfully implemented; no drift requiring action)
**Mismatches Found:** 2 minor interpretation deltas (both accepted, logged for traceability — no hand-back)

Reviewed the diff (`git diff develop...HEAD -- sidequest/`) against the **re-scoped** AC set (AC1/AC3/AC6/AC7; AC2/AC5 pre-delivered by 63-8, AC4 deferred — per the boss-approved TEA re-scope).

- **Span fires per render, not per cached file-load** (Ambiguous spec — Behavioral, Minor)
  - Spec: AC6 "Every manifest *load* emits a `reference_manifest_loaded` span."
  - Code: `load_r2_manifest_keys` is `@lru_cache`'d (file read once per process); the span fires inside `_gate_poi_slugs_on_manifest` **per POI-bearing render**.
  - Recommendation: **A (accept; spec improves to match)** — per-render is the correct observability granularity for the GM panel (a cache-miss-only span would go dark after the first render). The span reports the set actually used by *this* render.
- **"Not-in-manifest" folded into existing `poi_image_not_found` span** (Different behavior — Behavioral, Minor)
  - Spec: AC6 envisioned a three-way image decision (resolved | not-in-manifest | slug-missing).
  - Code: The gate excludes authored-but-absent slugs from `gated_poi_slugs`, so the existing 63-8 `poi_image_not_found` span fires for them — same span as a genuinely un-imaged location. No distinct `not_in_manifest` span was added.
  - Recommendation: **C (accept; clarify spec)** — consistent with the re-scope's "reuse the existing span family" directive; `poi_image_not_found` truthfully means "this rendered card has no image," which holds for both sub-cases. A distinct span would be additive polish, not correctness; defer unless the GM panel needs to separate the two.

**Architectural notes (no action):**
- **Reuse posture is strong** — extends `load_poi_image_slugs`, reuses the presenter's existing `poi_image_slugs` gate and the `reference_poi_image_*` span family, adds exactly one loader + one span. No new infrastructure invented (Reuse-First satisfied).
- **`pack_dir.parent.parent` manifest discovery** is sound and consistent with how `reference_routes` already resolves pack/world dirs; resolves correctly in prod (`sidequest-content/r2_manifest.json`) and fixture layouts. No need to thread a content-root through app.state for this scope.
- **Manifest-only-for-POI-worlds** (Dev's minimal-blast deviation) correctly preserves No-Silent-Fallbacks where a broken image could occur (POI-bearing world → loud-fail) without coupling every lore render to the manifest. Endorsed.
- **`@lru_cache(maxsize=8)` process-lifetime cache** matches AC1's "static between deploys." The staleness-after-upload risk (Dev's non-blocking Gap) is safe-failing (text-only, never a broken image) and out of scope — runbook note, not a code change.

**Decision:** Proceed to verify (Hamlet/TEA). No hand-back to Dev.
## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed — full server suite **9525 passed, 361 skipped, 0 failed**; ruff + pyright clean.

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`reference_renderer.py`, `telemetry/spans/reference.py`, `test_reference_poi_manifest_gate.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | 1 dismissed (cross-repo import impossible), 1 **applied** (key dedup), 2 noted (test-only / non-finding) |
| simplify-quality | 5 findings | 1 **applied** (docstring accuracy), 1 dismissed (false: `:func:` is house style), 3 cosmetic/non-findings |
| simplify-efficiency | 1 finding | 1 declined-with-rationale (cold-path micro-opt) |

**Applied (2):**
- **Single source of truth for the POI image key** (reuse, *upgraded* from medium): the gate and the presenter's `<img src>` both built `genre_packs/{pack}/worlds/{world}/assets/poi/{slug}.png` as independent f-strings. Extracted `poi_image_key()` into `reference_presenters.py` (already imported by `reference_renderer.py` → no circular dep) and used it in both sites. **This is correctness-protecting, not cosmetic** — divergent key formats would let the gate pass on a key the src never requests (or vice versa), silently breaking image emission.
- **Span-helper docstring accuracy** (quality, medium): `reference_manifest_loaded_span` said "fired once per lore render" — but the once-per-render invariant is the *caller's* (`_gate_poi_slugs_on_manifest` calls it once), not the helper's. Softened to "fired when a lore render consults r2_manifest.json."

**Dismissed with verified rationale (2 high-confidence agent claims, both wrong):**
- reuse "import `scripts/r2_manifest.py::load_manifest` instead of reimplementing" — **impossible**: `scripts/r2_manifest.py` lives in the **orchestrator** repo (`../scripts/`), not the server package; it is not importable. Its contract also differs (`list[dict]` vs `frozenset[str]`). Not actionable.
- quality "`:func:` Sphinx role is inconsistent with peers" — **false**: `:func:` appears 105× in the server package; it IS the house style. Changing it would *introduce* inconsistency.

**Declined with rationale (1):**
- efficiency "cache `world_key_count` instead of recomputing per render" (high-confidence): technically a redundant O(manifest) walk, but the lore reference page is a **cold path** (browsed on demand, not per game-turn), the walk is sub-millisecond on a 1743-entry frozenset, and the suggested fix *adds* a per-world cache — increasing complexity during a pass whose purpose is to reduce it. Net-negative trade; declined. If the reference page ever becomes hot, compute the count at manifest-load time.

**Overall:** simplify: applied 2 fixes (1 correctness-protecting), regression-clean.

### Rule re-check (post-simplify)
- python #6 test-quality: no tests modified; story tests still 11/11 green.
- Server "No Source-Text Wiring Tests": unaffected — wiring still proven via route + OTEL span.
- python #3 type-annotations / #5 path-handling: `poi_image_key` fully annotated; loader still `open(encoding="utf-8")`.

**Handoff:** To Reviewer (Portia) for code review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (11/11 story tests, full suite 9525 pass, ruff+pyright clean, 0 smells) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 4, dismissed 1, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 2 (LOW, test annotations), dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled-skipped)
**Total findings:** 9 confirmed, 1 dismissed (with rationale), 0 deferred — **0 Critical, 0 High; all LOW/MEDIUM**

### Confirmed findings (none blocking)

- `[DOC]` **LOW** — `_gate_poi_slugs_on_manifest` docstring says "Emits one span per render," but POI-less worlds early-return and emit none. The nearby `reference.py` comment is correct; the function docstring dropped the qualifier. (renderer:~1177)
- `[DOC]` **LOW** — `load_r2_manifest_keys` "loaded once per process" is imprecise vs. `@lru_cache(maxsize=8)` (per-path, evictable; effectively once-per-deploy for the single prod path). (renderer:~1136)
- `[DOC]` **MEDIUM** — `poi_image_key` should document that it returns a **raw R2 key** (no scheme/leading slash): the gate compares it directly against manifest keys, while the presenter must wrap it in `resolve_asset_url`. The raw-vs-resolved distinction is load-bearing. (presenters:193)
- `[TEST]` **MEDIUM** — no test for the second loud-fail branch: a JSON list whose entry is a dict **missing `key`**. The branch is correct but uncovered. (test:~110)
- `[TEST]` **MEDIUM** — no **end-to-end** loud-fail test: a POI-bearing world whose `r2_manifest.json` is absent at `pack_dir.parent.parent` should 500 (not silently render imageless). Unit-tested in isolation; the route-level No-Silent-Fallback proof is missing. *(Independently flagged by me before subagents returned.)* (test:~503)
- `[TEST]` **LOW** — `test_lore_render_fires_manifest_loaded_span_once` asserts `entry_count >= 1`; `== 2` (exact fixture count) would also prove the gate read the **fixture** manifest, not the prod one — catching a `pack_dir.parent.parent` resolution bug. (test:~528)
- `[TEST]` **LOW** — `load_r2_manifest_keys.cache_clear()` is never called between tests; currently harmless (read-only fixture, unique tmp_paths) but a latent ordering fragility. An autouse teardown fixture would harden it. (test:~418)
- `[RULE]` **LOW** — `_entry(key) -> dict` should be `-> dict[str, object]` (rule #3; test helper, borderline-exempt). (test:52)
- `[RULE]` **LOW** — `gated_client()` fixture lacks a `-> Iterator[TestClient]` return annotation (rule #3; pytest fixtures are commonly unannotated in this codebase). (test:188)

### Dismissed (with rationale)

- `[TEST]` `test_manifest_loaded_span_name_constant` "tautological" (test-analyzer, high confidence) — **DISMISSED**: it mirrors the established 63-8 `test_poi_span_name_constants` convention and guards the OTEL **wire-format string** (`sidequest.reference.manifest_loaded`), which GM-panel/dashboard queries depend on. It catches an accidental constant-value rename — not vacuous.

### Rule Compliance (13 lang-review checks × new code)

Cross-referenced with reviewer-rule-checker (47 instances enumerated). **Production code: 0 violations across all 13 checks.**

- **#1 silent-exceptions** — `[VERIFIED]` `load_r2_manifest_keys` (renderer:1144) has no try/except; `FileNotFoundError` (absent), `JSONDecodeError`/`ValueError` (malformed), and explicit `ValueError` (non-list / missing-key) all propagate. Complies with No Silent Fallbacks.
- **#3 type-annotations** — `[VERIFIED]` all four new production functions fully annotated (`load_r2_manifest_keys -> frozenset[str]`, `poi_image_key -> str`, `_gate_poi_slugs_on_manifest -> frozenset[str]`, span helper `-> Iterator[trace.Span]`). Only gaps are 2 test-file helpers (LOW, confirmed above).
- **#5 path-handling** — `[VERIFIED]` `manifest_path.open(encoding="utf-8")` (renderer:1144); `pack_dir.parent.parent / "r2_manifest.json"` uses the `/` operator. The f-string keys are **R2 object keys** (logical, forward-slash by R2 convention), not filesystem paths.
- **#6 test-quality** — `[VERIFIED]` 11 tests, each with specific-value assertions; no `assert True`, no bare truthy checks; OTEL-span/route assertions, **no source-text greps** (complies with "No Source-Text Wiring Tests").
- **#7 resource-leaks** — `[VERIFIED]` file handle and span both via `with`.
- **#8 unsafe-deserialization** — `[VERIFIED]` `json.load` (not pickle/eval) on a first-party committed artifact, with `isinstance` shape validation.
- **#11 input-validation/security** — `[VERIFIED]` the manifest path is built from trusted `pack_dir`, not from the `pack`/`world` route strings; `pack`/`world` are `_SAFE_SLUG`-validated in `reference_routes._resolve_pack_dir/_resolve_world_dir`, so `../` cannot reach `world_prefix`.
- **#2/#4/#9/#10/#12/#13** — `[VERIFIED]` no mutable defaults; error path is loud-raise (OTEL is the success-path observability, per the OTEL Principle); sync code (no async pitfalls); explicit imports, no star/circular (renderer→presenters is one-directional); no new deps (`functools` is stdlib); meta re-scan clean (`lru_cache` does NOT cache exceptions → absent-then-present re-reads correctly).

### Observations (≥5)

1. `[VERIFIED]` **Wired end-to-end** — `_gate_poi_slugs_on_manifest` ← `assemble_lore_page` (renderer:1214) ← route `lore_page` (reference_routes.py:124). Reachable from `GET /reference/lore/{pack}/{world}`; proven by 3 route tests.
2. `[VERIFIED]` **Drift-proofed key** — both the gate's manifest-check and the presenter's `<img src>` now call the single `poi_image_key` (presenters:193). The pre-verify two-f-string drift hazard is gone.
3. `[VERIFIED]` **Loud-fail correct** — absent → `FileNotFoundError`, malformed/non-list/missing-key → `ValueError`; none caught by `lore_page`'s `except (ValueError, MissingThemeFieldError)` for FileNotFoundError → still a 500 (loud), never a silent text-only render.
4. `[VERIFIED]` **Observable** — `reference_manifest_loaded` span (flat-only registered) fires per POI-bearing render with path/entry_count/world_key_count — the GM-panel lie detector for the gate.
5. `[MEDIUM]` **Data flow traced** — route `pack`/`world` (`_SAFE_SLUG`-validated) → `pack_dir` → `pack_dir.parent.parent/r2_manifest.json` → cached key set → intersect authored slugs → presenter gate. Safe: user input never reaches the manifest path or filesystem traversal.
6. `[LOW]` **Empty-manifest edge** — a structurally-valid empty `[]` manifest returns an empty key set → all POIs render text-only with no error. Defensible (the oracle says "nothing on R2"), but an accidentally-empty manifest silently hides every image. Operational, not a defect.

### Devil's Advocate

Assume this is broken. The most plausible real-world failure is **cache staleness in a long-running server**: `load_r2_manifest_keys` is `@lru_cache`'d with no TTL or mtime check, so once a manifest is read it is pinned for the process lifetime. An operator who renders a new POI image, uploads it to R2, and regenerates `r2_manifest.json` on disk will see the running server *continue to suppress that image* until restart — a confusing "I added the art, why won't it show?" footgun. It is safe-failing (text-only, never a broken image), so it doesn't violate the story's contract, but it is a genuine operational trap worth a runbook note (Dev already flagged a milder version). A second angle: an **accidentally-empty or truncated-but-valid manifest** (`[]`) silently blanks every POI image with no error — the loud-fail only covers absent/malformed, not "valid but empty," so a botched manifest-regeneration that writes `[]` degrades the whole lore gallery quietly. Third, a **casing/slug-normalization mismatch** between the authored history.yaml slug and the actual uploaded R2 object key would make the gate miss a real image (exact string match, case-sensitive R2 keys) — slugify mitigates this but cross-tool casing drift could still bite. Fourth, the **`pack_dir.parent.parent` discovery is positionally fragile**: it hard-codes the assumption that the genre-pack search root is exactly one level below the content root; a future deployment that points `SIDEQUEST_GENRE_PACKS` directly at a content root (no `genre_packs/` layer) would resolve the manifest one directory too high and 500 every POI-bearing lore page. A confused operator misreading the loud-fail (a bare FileNotFoundError 500, since `lore_page` doesn't catch it for a friendly message) might not immediately connect it to a missing manifest. None of these are *current* bugs — the code is correct, wired, observable, and rule-clean — but they are the seams where it could fracture, and the missing e2e loud-fail test (`[TEST]` MEDIUM above) is the one I'd most want closed before this gate pattern is copied into 65-9.

## Reviewer Assessment

**Verdict:** APPROVED
**Data flow traced:** `GET /reference/lore/{pack}/{world}` → `_SAFE_SLUG`-validated `pack`/`world` → `pack_dir` → `pack_dir.parent.parent/r2_manifest.json` (cached, loud-fail) → authored slugs ∩ manifest keys → presenter `<img>` gate. Safe: user input never reaches a filesystem path; the manifest path derives from trusted `pack_dir`.
**Pattern observed:** Manifest-existence gate scoped to only-POI-bearing worlds (`_gate_poi_slugs_on_manifest`, renderer:1196) — preserves No-Silent-Fallbacks where a broken image could occur without coupling every render to the manifest. Single `poi_image_key` eliminates gate/presenter key drift.
**Error handling:** Loud on absent/malformed manifest (FileNotFoundError / ValueError propagate to a 500); not-in-manifest slugs are excluded and the existing `poi_image_not_found` span fires — observable, never silent. Verified `lru_cache` does not cache exceptions.
**Why APPROVED:** 0 Critical, 0 High across 4 subagents + my own pass + 13-rule enumeration. Production code is correct, wired end-to-end, observable, and rule-clean. All 9 confirmed findings are LOW/MEDIUM test-coverage, test-annotation, or docstring-precision items — none block under the severity policy, and the `<critical>` wiring-test requirement is met (the gate is proven through the live route).
**Findings incorporated (tagged by specialist):**
- `[TEST]` MEDIUM — no e2e loud-fail route test (POI-bearing world + absent manifest → 500); `[TEST]` MEDIUM — missing-`key` loud-fail branch uncovered; `[TEST]` LOW — tighten `entry_count >= 1` to `== 2`; `[TEST]` LOW — `lru_cache` not cleared between tests. (1 `[TEST]` dismissed: the constant-equality test guards the OTEL wire-format string — not vacuous.)
- `[DOC]` LOW — `_gate_poi_slugs_on_manifest` "one span per render" (false for POI-less worlds); `[DOC]` LOW — `load_r2_manifest_keys` "once per process" imprecise vs lru_cache; `[DOC]` MEDIUM — `poi_image_key` should document raw-key-vs-resolved-URL.
- `[RULE]` LOW — `_entry -> dict[str, object]`; `[RULE]` LOW — `gated_client -> Iterator[TestClient]`. (Production code: 0 rule violations across all 13 checks.)
**Recommended fast-follow (non-blocking):** the e2e loud-fail test (No-Silent-Fallback proof), the missing-`key`-branch test, the `== 2` assertion tightening, the 3 docstring fixes, and the 2 test annotations — best folded into 65-9 (Cast portraits), which will reuse this exact gate pattern. Plus a runbook note on the manifest-cache-staleness footgun.
**Handoff:** To SM (Prospero) for finish-story.