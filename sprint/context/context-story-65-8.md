---
parent: context-epic-65.md
workflow: tdd
---

# Story 65-8: Lore POI gallery — feed geography renderer from history.yaml, manifest-gated images

## Business Context

Epic 65 replaces git-LFS pointer tracking with a checked-in R2 manifest so the
dual-clone (OQ-1/OQ-2) workflow can answer "what's actually rendered vs. what
still needs doing" without hitting the network. Story 65-7 (DONE) populated and
committed `sidequest-content/r2_manifest.json` — 1743 entries, the existence
oracle. This story spends that oracle for the first **player-facing** payoff: the
lore reference page.

The lore reference page (`GET /reference/lore/{pack}/{world}`) is a public
table tool (ADR-135) — a single fixed projection any player can open to see a
world's points of interest, history, and factions. Today it is image-poor: the
POI card renderer and the POI image emitter both exist and are wired into the
live engine, but the images **never appear**, because the geography section is
authored as a prose string in `lore.yaml` and the structured POI list from
`history.yaml` is never handed to the renderer. The work here is integration,
not new capability.

Two readers are served. The narrative reader sees a richer, illustrated world
page (Diamonds-and-Coal: the worlds with real art finally show it). The
mechanical reader (Sebastien/Jade) gets POI **type/region/environment** surfaced
as legible chips rather than buried in prose — the gears made visible in a
player surface, per ADR-135 D7. The manifest gate is what makes this safe:
glenross has POIs but zero portrait/POI images on R2, so a naive renderer would
emit broken `<img>` tags into a player's face. Gating emission on manifest
presence is Genre-Truth presentation hygiene — show what exists, silently omit
what doesn't, never ship a broken image.

## Technical Guardrails

**This is a wire-up, not a build.** The load-bearing infrastructure already
exists and is proven in the live engine. Reuse it; do not reimplement it
(CLAUDE.md: "Don't Reinvent — Wire Up What Exists").

**Repo / branch:** `sidequest-server` only. Server is Python/FastAPI, uv-managed.
Run tests via the `testing-runner` subagent, not directly.

**Key files / seams to use:**
- `reference_presenters.py` — `present_lore_geography()` (the card renderer,
  expects a **list of location dicts**) and `_poi_image_html()` (the `<img>`
  emitter that already calls `resolve_asset_url()`). Extend with a thin POI
  presenter, e.g. `present_lore_poi_gallery(...)`, or call
  `present_lore_geography` a second time with the history POI list.
- `reference_renderer.py` / `assemble_lore_page()` — the page assembler and route
  path. New "Points of Interest" section wires in here.
- `resolve_asset_url()` — existing CDN-URL seam. Do not hand-build URLs.
- `scripts/r2_manifest.py:load_manifest()` — the battle-tested manifest loader
  pattern. Mirror it (or import it) for the server-side
  `load_manifest()`; do not author a second, divergent parser.
- `history.yaml:points_of_interest[]` — source list, shape
  `{name, slug, region, type, description, environment}`. This is exactly what
  the presenter consumes — no lore-model change required.
- `load_poi_image_slugs()` — already built by the lore loader, keyed by POI
  slug; currently unused by the image path. Feed it in.
- OTEL span family `reference_poi_image_*` (ADR-031/090) — **reuse**, don't
  invent. Add one new span: `reference_manifest_loaded`.

**Expected R2 key convention:** POI image key is
`.../worlds/{world}/assets/poi/{slug}.png` — must match what the manifest
actually contains (the same 1:1 relative-path convention the sync uploads with).
Compare like-for-like against manifest keys.

**No Silent Fallbacks (CLAUDE.md, critical):** manifest absent or malformed must
**fail loud** — never silently degrade to "render imageless." The *image gate*
(key-not-in-manifest → skip tag) is a deliberate, OTEL-logged decision, not a
silent fallback — log every skip as a `reference_poi_image_*` span.

**OTEL Observability Principle (CLAUDE.md, important):** every manifest-gating
decision must emit a span so the GM panel can verify the gate is engaged and the
narrator/renderer isn't "winging it." Manifest load → `reference_manifest_loaded`
(path, entry count, world-prefix count). Each image decision →
`reference_poi_image_resolved` | `reference_poi_image_not_in_manifest` |
slug-missing variant. (These are **dev/GM observability** spans, not a
"Sebastien feature" — keep that framing straight.)

**Public projection only (ADR-135):** no `?audience` param, no GM mode, no
toggles. POI type/region/environment/description are all public facts.

**What NOT to touch:** the lore data model (`lore.yaml` schema), the runtime
`asset_ledger` (65-2's namespace), R2 itself (read the manifest only — never
LIST/PUT/DELETE at request time), and the Cast/portrait path (65-9).

## Scope Boundaries

**In scope:**
- Server-side `load_manifest()` for `r2_manifest.json` (load-once, cached,
  loud-fail on absent/malformed).
- A POI section presenter that feeds `history.yaml:points_of_interest` to the
  existing `present_lore_geography()` card renderer.
- Manifest-gated `<img>` emission: emit only when the expected R2 key is present
  in the loaded manifest; otherwise omit cleanly and log an OTEL span.
- TOC registration of a "Points of Interest" section, shown only when the world
  has POI entries.
- POI **type** surfaced as a visible chip/badge; region and environment rendered
  legibly (not raw YAML keys).
- OTEL: `reference_manifest_loaded` span + reuse of the `reference_poi_image_*`
  family per decision.
- A wiring/integration test that renders the live `/reference/lore/{pack}/{world}`
  path for a pilot world.

**Out of scope:**
- Cast section / NPC portraits (65-9).
- TOC data repair beyond registering this one section (65-10).
- POI map view / SVG (65-11) and world timeline (65-12).
- Markdown-in-YAML rendering, cross-pack search, inline authoring.
- Any write to R2 or to the runtime asset ledger.

## AC Context

**AC1 — Manifest loading and caching.** The renderer loads `r2_manifest.json`
from the `SIDEQUEST_GENRE_PACKS` mount, parses to a key→entry map, loads once per
process and caches. *Pass test:* a second render does not re-read the file (cache
hit). *Edge/negative — the load-bearing one:* file absent → raises an informative
error; malformed JSON → raises. **No silent fallback to imageless render.** Assert
the raised error type/message, not just `is_none()`.

**AC2 — POI section presenter.** A presenter feeds
`history.yaml:points_of_interest` entries to `present_lore_geography()`. *Pass
test:* given a POI list, the presenter calls the geography renderer with that
list and returns section HTML. *Edge:* POI list and the prose
`lore.yaml:geography` are independent — both present, only prose, only POIs, or
neither, with no coupling (test each combination renders without error). *Shape
guard:* entries missing required keys (`slug`, `name`, …) are handled
predictably — assert the chosen behavior (skip-with-span vs. raise), don't leave
it implicit.

**AC3 — Manifest-gated image emission.** An `<img>` is emitted **iff** the
expected key `.../worlds/{world}/assets/poi/{slug}.png` is in the loaded
manifest. *Pass test:* key present → exactly one `<img>` with the
`resolve_asset_url()` CDN URL. *Negative — pins the bug:* key absent → **zero**
`<img>` tags (not a broken tag) and a `reference_poi_image_not_in_manifest` (or
equivalent) span logged. Assert on the rendered HTML string for presence/absence
of `<img`, not just span counts.

**AC4 — TOC registration.** "Points of Interest" appears in the page TOC when the
world has POI entries, and is **omitted** when it does not. *Pass test:* world
with POIs → TOC contains the entry. *Negative:* world with empty/absent
`history.yaml:points_of_interest` → no TOC entry **and** no empty section body.

**AC5 — Two-reader presentation.** POI **type** renders as a visible chip/badge
alongside the description (not buried in prose); region and environment render
legibly. *Test:* assert the type value appears wrapped in the chip markup
(class/element), and that raw YAML key strings (e.g. literal `environment:`) do
**not** leak into output.

**AC6 — OTEL observability.** Every manifest load emits `reference_manifest_loaded`
with path, entry count, and world-prefix-filtered count. Each POI image decision
emits a `reference_poi_image_*` span (resolved / not-in-manifest /
slug-missing-from-poi_image_slugs). *Test:* capture emitted spans (existing
watcher test harness) and assert the manifest-load span fires once per render and
one image-decision span fires per POI. Assert span **attributes**, not just that
a span exists.

**AC7 — Wiring proof (mandatory integration test).** Render the live reference
page for **blackthorn_moor** (has both `history.yaml` POIs and live POI images on
R2): assert the POI section renders with ≥1 `<img>` and zero broken tags.
**Negative wiring test:** render **glenross** (POIs yes, images no): assert the
POI section renders (POIs exist) with **zero** `<img>` tags. **Regression:**
existing sections (history, cosmology, factions) render unchanged — assert their
markers still present and the page assembles without error. This AC is the
non-test-consumer proof required by CLAUDE.md "Verify Wiring, Not Just
Existence": the presenter must be reachable from the real route, not just unit
tests.

## Assumptions

- **Manifest artifact is present.** 65-7 committed `r2_manifest.json` with 1743
  entries; this story assumes the artifact (not just the code) is on disk at the
  `SIDEQUEST_GENRE_PACKS` mount. If absent at runtime, AC1's loud-fail path is
  the correct behavior — do not work around it.
- **blackthorn_moor R2 images exist** for at least one POI slug, and
  **glenross has zero** POI images on R2. These are the pilot/negative fixtures;
  if R2 state has drifted since setup, the integration test fixtures may need a
  manifest stub rather than live R2 (tests must not hit live R2 — inject a fake
  manifest map). Verify against the committed manifest, not the network.
- **`history.yaml:points_of_interest` shape is stable** as
  `{name, slug, region, type, description, environment}` across the pilot worlds
  — the presenter consumes it directly. A world authoring a divergent shape is a
  data bug, not a renderer concern.
- **`present_lore_geography()` / `_poi_image_html()` signatures are reusable**
  as-is (possibly with one added manifest-gate parameter). If a signature change
  ripples beyond a single optional parameter, log a Design Deviation before
  proceeding — that would mean this is no longer a pure wire-up.

If any assumption proves wrong during implementation, log a Design Deviation and
notify SM — wrong assumptions are the top source of scope creep.

---
_Authored 2026-06-01 to backfill the setup gap (sm-setup produced the session
file but not this story-context doc). Composed solo from the session brief and
epic-65 context per the context skill's graceful-degradation path; the session
file already carried architect-grade technical detail. Schema-compliant per
context-schema.yaml v1.0.0._
