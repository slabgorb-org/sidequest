---
parent: context-epic-65.md
workflow: tdd
---

# Story 65-12: Lore world timeline — world-historical spine from legends, honest conditional sort

## Business Context

Epic 65 spent a checked-in R2 manifest (`sidequest-content/r2_manifest.json`,
committed by 65-7) on a run of player-facing payoffs on the lore reference page
(`GET /reference/lore/{pack}/{world}`, the **ADR-135** public table tool): 65-8
lit up **Points of Interest** images, 65-9 added the manifest-gated **Cast**
section, 65-11 added the server-rendered **Map** (node-link graph). The 2026-06-01
design spec (`docs/superpowers/specs/2026-06-01-lore-reference-images-and-audience-split-design.md`
§6, line 234) names this story as the final follow-on slice: a unified **world
timeline**. This is the **timeline** slice.

The timeline gives the table the world's *past* as a single legible spine — the
deep history a good DM holds in their head and doles out in fragments. It serves
both ADR-135 readers exactly as the rest of the lore page does. The **narrative
reader** (James/Keith) gets the world's legends laid out as a chronicle —
Diamonds-and-Coal across time, the Cataclysm and the Armistice and the night the
Mesh launched, each with its flavor. The **mechanical/legibility reader**
(Sebastien/Jade) gets the **`era`/`period` value surfaced verbatim as a chip**
beside each entry — the temporal fact made explicit instead of buried in prose.
For a mechanics-first author like Jade extending `perseus_cloud`, seeing her
authored legend eras rendered as an ordered spine is direct feedback that the lore
she wrote loads and reads the way she intended.

The hard fact that shapes the whole story — and the reason it needed an architect
pass before TDD, exactly as 65-11 did against `cartography.yaml`: **the three
sources the spec names do not share a sortable temporal axis, and two of them are
not even on the same axis.** Legend time is free-text and bespoke per world
(absolute years `1855`; relative `"15 years ago"`/`"three centuries ago"`; fantasy
calendar `"-11540"`/`"early Second Rising"`; or no field at all, dates embedded in
prose) — and the field name itself is `era:` in most packs but `period:` in
heavy_metal. `history.yaml:chapters[].session_range` is **campaign/play time**, an
axis orthogonal to world-historical time, and those chapters carry
`tropes: status: dormant` escalation seeds that **ADR-135 D1 forbids surfacing**.
**POI founding has no structured field anywhere** — it lives only in prose.

The Operator decided the resolution (2026-06-03): **a world-historical spine with
an honest conditional sort.** Build the timeline on the world-historical axis only
— legends — order it as authored by default, apply a numeric sort *only* when every
entry in a world exposes a uniformly-parseable key, and record which mode fired in
OTEL so the page never claims a chronology it could not compute. Campaign chapters
are excluded (wrong axis + spoiler seeds); POI founding is deferred to 74-3 (it has
no field to read, and writing a reader for a field no world authors is dead code —
"No Stubbing").

## Technical Guardrails

**This REUSES the 65-8/65-9/65-11 reference-page machinery — it is mostly a
wire-up plus one small new ordering helper, not a new build** (CLAUDE.md: "Don't
Reinvent — Wire Up What Exists"). The route, the synthesized-section + TOC
registration, the legend model, the OTEL span family, and the test fixtures all
exist. Author a divergent manifest path, a second legend parser, a universal
temporal-date parser, or a parallel span vocabulary and you have failed the story.

**Repo / branch:** `sidequest-server` only, on a `feat/65-12-*` branch off
`develop` (per repos.yaml — NOT main). Server is Python/FastAPI, uv-managed. Run
tests via the `testing-runner` subagent, never directly. (Epic 65's header reads
`repos: content`, but this slice is server-side per the spec decomposition, like
65-8/65-9/65-11.)

**As-built seams to reuse (verified by Architect scan, cite `develop`):**
- **Route + assembler:** `server/reference_routes.py:lore_page()` (~120) →
  `server/reference_renderer.py:assemble_lore_page(pack, world, pack_dir,
  world_dir)` (~1297). The timeline section is produced inside the lore assembler
  and concatenated into the page body — it is NOT a new route.
- **Synthesized-section + TOC append (the exact pattern to follow):** the 65-9
  **Cast** append (`reference_renderer.py` ~1334-1361) and the 65-11 **Map** append
  (~1363-1391): render the section HTML, `body += html`, then append a
  `{"num": _int_to_roman(len(kept_toc)+1), "id": "timeline", "label": "Timeline"}`
  entry to `kept_toc` *after* `_wrap_sections_by_toc()` returns (~1332). Timeline is
  a synthesized section (not a YAML file stem), so it registers a TOC entry directly
  — do NOT add it to `TOC_TO_FILES`/`LORE_WORLD_FILES`.
- **Legend model (reuse, do not re-model):** `genre/models/legends.py:Legend`
  (~39-79): `name: str`, `summary: str`, `era: str = ""`, `cultural_impact: str`,
  `monuments: list[str]`, `terrain_scars: list[TerrainScar]`, and the
  heavy_metal pass-through `period: str | None = None`. **Temporal value = `era` if
  non-empty else `period`.** Both are free-text; treat them as opaque display
  strings (see AC3).
- **Legend loading (reuse the existing flexible loader):** legends load via
  `genre/loader.py:_load_legends_flexible` (~327) which already handles both the
  per-file `worlds/<slug>/legends/` directory and the flat `legends.yaml` map form.
  **Do NOT hand-roll a third legends parser.** See the reachability Gap in
  Assumptions — `assemble_lore_page` currently walks files and does not hold a typed
  `World`; getting the typed `Legend` list to the presenter is *wiring*, not
  reimplementation.
- **Optional preamble source:** `genre/models/lore.py:WorldLore.history`
  (`str | None`) — the world's history prose, reachable as `world.lore.history`.
  Rendered as section framing only, never decomposed into entries (AC5).
- **OTEL spans:** `telemetry/spans/reference.py` holds the reference span family
  and the `FLAT_ONLY_SPANS` registry; mirror `reference_map_rendered_span`
  (~436-458). Add a `reference`-namespaced `reference_timeline_rendered` span
  (register the constant in `FLAT_ONLY_SPANS`). Do NOT invent a parallel
  vocabulary.
- **Manifest gate (only if images are emitted):** legends carry no images, so the
  timeline is **text + chips**; the D2 manifest gate (`load_r2_manifest_keys`,
  `_gate_poi_slugs_on_manifest`) is **not** needed unless a future entry emits an
  `<img>`. v1 emits none — note it, do not wire an unused gate.

**Test seams to reuse:** `tests/server/test_reference_*` modules; the reference
integration `client()` fixture (`tests/server/test_reference_integration.py` ~44,
`TestClient` over the `reference_v2_fixture` pack at
`tests/fixtures/packs/reference_v2_fixture/`, which already has a
`worlds/long_fixture/legends.yaml`); `otel_capture`/`otel_exporter` and the
`span_attrs_by_name(exporter, name)` helper (`tests/server/conftest.py`
~1177-1295). **No source-text wiring tests** (server CLAUDE.md): assert on rendered
HTML, emitted spans, or fixture-driven behavior — never `read_text()` of production
source. The wiring proof is an integration test through the real `/reference/lore/`
route.

**Determinism is a correctness requirement, not a nicety.** Same legend set →
byte-identical Timeline HTML. That rules out `set`/`dict` iteration order leaking
into output, and wall-clock or randomness in element ids. Authored order is the
legends' load order; the conditional sort (AC4) is a stable sort with ties broken
by authored order.

## Scope Boundaries

**In scope:**
- A public **Timeline** section on the lore reference page: world-historical
  entries built from the world's `Legend` list, each rendering `name` + a
  **verbatim** `era`/`period` chip + `summary` (and existing public flavor:
  `cultural_impact`, `monuments`, `terrain_scars`), with a TOC entry registered
  when the world has at least one legend.
- An **honest conditional sort** (the one genuinely new helper): default authored
  order; apply an ascending numeric sort *only* when every temporal entry in the
  world exposes a uniformly-parseable comparable key; otherwise keep authored
  order. Legends with no temporal value render in an explicit "undated" tail —
  never dropped.
- An optional **history preamble**: `world.lore.history` prose rendered as section
  framing, not decomposed into entries.
- OTEL: a `reference_timeline_rendered` span carrying `entry_count`,
  `undated_count`, and `sort_mode` (`sorted` | `authored_order`).
- An integration test through the real route, a regression check that existing
  sections render unchanged, and a chrome-wiring fixture extension covering the new
  timeline CSS classes.

**Out of scope (record the first two as Design Deviations against spec line 234):**
- **POI founding as timeline entries.** No structured founding field exists in any
  world (`Region.origin` is nullable freeform prose; `points_of_interest[]` carry
  no date). Building a reader for an unauthored field is dead code (No Stubbing);
  POI founding is **deferred to 74-3** (content adds a field first). Spec
  reinterpretation — log it.
- **`history.yaml:chapters[]` / `session_range` in the spine.** Campaign/play-time
  axis, not world-historical; and the chapters carry `tropes: status: dormant`
  escalation seeds ADR-135 D1 forbids surfacing. Excluded. Spec reinterpretation —
  log it.
- A **universal temporal-date parser** that normalizes `"15 years ago"` /
  `"-11540"` / `"early Second Rising"` into one scale. Explicitly rejected — the
  conditional sort detects *uniform parseability* and otherwise preserves authored
  order; it does not attempt cross-dialect normalization. Pursuing one pushes past
  3 points — log a Design Deviation.
- Any schema or content change (adding `year`/`founded` fields) — that is 74-3.
- The in-game live surfaces; client-side React; image generation; writes to R2 or
  the asset ledger. This is the static, server-rendered lore-page projection.
- The public/secret projection decision — ADR-135 already governs it; this story
  consumes the public projection, it does not create the split.

## AC Context

**AC1 — Timeline section registered + rendered.** The lore page gains a "Timeline"
section with a TOC entry via the 65-9 Cast / 65-11 Map synthesized-section append
pattern (append to `kept_toc` after `_wrap_sections_by_toc`, NOT via
`TOC_TO_FILES`). *Pass:* a world WITH at least one legend → response contains the
Timeline section. *Edge (graceful):* a world with NO legends → HTTP 200, page
unchanged, no Timeline section, no error. *Loud:* malformed `legends.yaml` → HTTP
500 (No Silent Fallbacks). Assert on the rendered HTML.

**AC2 — Entries from legends; nothing dropped.** Every `Legend` renders as exactly
one timeline entry. A legend whose temporal value (`era` else `period`) is
non-empty is a dated entry; a legend with neither renders in an explicit "undated"
group. Entry count == legend count (dated + undated). *Test:* a fixture world with
legends covering all three cases (an `era`, a `period`-only, a neither) → assert
each appears exactly once and the undated one is in the undated group. Pins the
"silently dropped a legend" bug.

**AC3 — Verbatim temporal chip, never normalized.** The `era`/`period` value
renders **verbatim** as a chip beside the entry (ADR-135 D7 — mechanical fact
beside flavor). `"-11540"`, `"15 years ago"`, `"early Second Rising"`, and
`"shot February 25, 1855, ..."` must each appear in the chip markup **exactly as
authored** — never reformatted, parsed-into-a-date, or truncated. *Test:* a fixture
whose legends use all four dialects → assert each raw string is present verbatim in
the rendered chip. This is the No-Silent-Fallback-honesty AC for display.

**AC4 — Honest conditional sort with recorded mode.** Default order is authored
(legend load) order. An ascending numeric sort is applied **iff** every dated entry
in the world exposes a uniformly-parseable comparable key (e.g. all clean ≤4-digit
years, or all `"N <unit> ago"` with one unit family); a single non-conforming entry
forces authored order for the whole world. The sort is **stable**, ties broken by
authored order; the "undated" group always sorts to the tail in authored order.
*Tests:* (a) a uniform-year fixture (`1855`, `1862`, `1878`) → entries ascending;
(b) a mixed-dialect fixture (`1855` + `"15 years ago"` + `"early Second Rising"`) →
entries in authored order, unchanged. The mode is asserted via the AC6 span, so the
test distinguishes a real sort from an accidental one.

**AC5 — Optional history preamble, no decomposition.** If `world.lore.history`
prose is present, render it as the Timeline section's framing preamble, visually
distinct from the entry list; it is **not** parsed into entries. *Test:* a fixture
with `lore.history` → preamble present and entries still render; a fixture without
→ entries-only, no error, no empty preamble node.

**AC6 — OTEL on the render decision (mandatory per CLAUDE.md).** The renderer emits
`reference_timeline_rendered` **once per render** carrying `entry_count`,
`undated_count`, and `sort_mode` (`"sorted"` | `"authored_order"`). Reuse the
`telemetry/spans/reference.py` family + `FLAT_ONLY_SPANS`; mirror
`reference_map_rendered_span`. *Test:* `span_attrs_by_name`/`otel_capture` with a
**complement assertion** — the uniform-year fixture reports `sort_mode == "sorted"`
AND the mixed-dialect fixture reports `sort_mode == "authored_order"`, so the span
alone proves the conditional gate engaged rather than the renderer improvising an
order. The GM panel is the lie detector: this span is how we confirm the honest
sort fired, not a convincing-but-fabricated chronology.

**AC7 — Public projection only (ADR-135 D1).** No `?audience` param, no GM mode.
Only public legend fields render (name, era/period, summary, cultural_impact,
monuments, terrain_scars). `history.yaml:chapters[]`, any `tropes` /
`status: dormant` / escalation-seed data, and ADR-053 belief/clue data **never**
appear in the Timeline section. *Test:* a fixture whose `history.yaml` has
dormant-trope chapters → assert no chapter/trope/seed tokens appear in the Timeline
section, and assert no query param changes the output.

**AC8 — Wiring + regression (no source-text wiring tests).** At least one
integration test hits the **real** `/reference/lore/{pack}/{world}` route via the
reference `client` fixture and asserts the Timeline section + at least one entry +
a verbatim chip end-to-end (behavior/OTEL/fixture-driven, never a grep of source).
Existing lore sections (geography/POI, cast, map, history, factions) render
**unchanged** (regression). The chrome-wiring fixture
(`test_reference_chrome_wiring.py` seed world) is extended so the new timeline CSS
classes are actually rendered and validated — closes the chrome blind spot rather
than reopening it.

## Assumptions

- **Legend reachability is the one blocking Gap to confirm in RED.**
  `assemble_lore_page` currently *walks files* and does not hold a typed `World`,
  so `world.legends` may not be in scope at the assembler. Getting the typed
  `Legend` list to the timeline presenter must reuse the existing
  `_load_legends_flexible` loader (parse `world_dir`'s legends), **not** a new
  parser. If reachability requires loading the world object in the assembler, that
  is the story's wiring; if it needs a new helper, log a Design Deviation. Confirm
  against the `reference_v2_fixture/worlds/long_fixture/legends.yaml` shape before
  pinning tests.
- **Temporal value precedence is `era` (if non-empty) else `period`.** Confirm
  against fixtures; heavy_metal is the `period`-only world (manual verify).
- **The conditional-sort helper stays minimal and deterministic** — detect uniform
  parseability for a small, closed set of forms (clean year, `"N <unit> ago"`); any
  ambiguity → authored order. It is NOT a general date parser. Log a Design
  Deviation if a richer parser is pursued (that is past 3 points).
- **Determinism is achievable** — authored order is the legend load order; the sort
  is stable. No dict/set ordering may leak into output.
- **Fixture worlds, not live content, anchor the tests.** Build frozen fixtures: a
  uniform-year world (sorted mode), a mixed-dialect world (authored-order mode), a
  no-legends world (graceful skip), and a dormant-trope-bearing world (spoiler
  scrub). Live candidates for **manual** verification only:
  `spaghetti_western/five_points` (clean years → sorted), `heavy_metal/evropi`
  (`period`, fantasy calendar → authored-order fallback),
  `neon_dystopia/franchise_nations` (`"N years ago"`).

If any assumption proves wrong during implementation, log a Design Deviation and
notify SM — wrong assumptions are the top source of scope creep.

---
_Authored 2026-06-03 by Architect (the White Queen) as the AC-authoring + context
step the Operator requested before TDD setup (65-12 entered the sprint as a
title-only story). Composed from ADR-135, the 2026-06-01 lore-reference design spec
(§6 line 234), the 65-11 sibling context, and an **as-built** reuse-surface scan of
`develop` (`reference_routes.lore_page`, `reference_renderer.assemble_lore_page` /
`_wrap_sections_by_toc` / the Cast+Map synthesized-section append, `Legend` /
`WorldLore` models, `genre/loader._load_legends_flexible`,
`telemetry/spans/reference` / `FLAT_ONLY_SPANS` / `reference_map_rendered_span`, and
the reference `client` / `otel_capture` / `span_attrs_by_name` fixtures). The
Operator chose the world-historical-spine + honest-conditional-sort resolution;
POI-founding and campaign-chapter inclusion are logged here as deferred spec
reinterpretations (74-3 + ADR-135 D1). Schema-compliant per context-schema.yaml._
