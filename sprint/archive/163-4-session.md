---
story_id: "163-4"
jira_key: ""
epic: "163"
workflow: "trivial"
---
# Story 163-4: Content: Glenross OS-sheet, Années Folles Baedeker, the_circuit highway map.yaml + authoring checklists (plan tasks 9–11)

## Story Details
- **ID:** 163-4
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/163-4-raster-map-yaml-content in sidequest-content subrepo)
- **Branch:** feat/163-4-raster-map-yaml-content (sidequest-content)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-07-09T10:46:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T10:31:21.989462Z | 2026-07-09T10:33:12Z | 1m 50s |
| implement | 2026-07-09T10:33:12Z | 2026-07-09T10:38:15Z | 5m 3s |
| review | 2026-07-09T10:38:15Z | 2026-07-09T10:46:41Z | 8m 26s |
| finish | 2026-07-09T10:46:41Z | - | - |

## Sm Assessment

**Story:** 163-4 — content-only authoring of raster `map.yaml` treatments for three worlds (glenross, annees_folles, the_circuit), plus per-world `assets/maps/README.md` sourcing checklists + `.gitkeep`. Epic 163, Mapping Track A.

**Workflow decision — `trivial`, not the epic's tagged `superpowers`/spdd:** Keith explicitly chose `trivial` (setup → implement → review → finish). Siblings 163-1/2/3 ran full spdd because they were *server* stories with real failing tests. 163-4 is pure content YAML transcription with no honest RED — content invariants live in the pack validator (project doctrine), and that validator already shipped in 163-3. Forcing spdd would produce a vacuous RED phase. Story YAML `workflow` field updated to `trivial` via `pf sprint story update` (not hand-edited).

**Authoritative spec is the PLAN, not the story YAML** (which has no description/ACs): `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Tasks 9 (L728–794), 10 (L798–842), 11 (L846–894). Each task ships the exact `map.yaml` body, README checklist text, and verify command. Dev should transcribe near-verbatim, then verify region-id coverage against each world's `cartography.yaml`.

**Dependency:** 163-1 (server map.yaml treatment layer/loader) and 163-3 (validator anchor+provenance gates) are both DONE + merged to develop. This story is the content that those gates now police — no code dependency beyond the validator being present.

**Branching:** content-only story. Working branch `feat/163-4-raster-map-yaml-content` created in the `sidequest-content` subrepo from `origin/develop` (subrepo targets develop, not main). No orchestrator branch for the code work. Dev's PR targets `develop` in sidequest-content.

**Verification gate (Reviewer must confirm):** `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/<pack>` for each of tea_and_murder, pulp_noir, road_warrior — EXPECT no map.yaml errors. A missing image FILE is fine (validator checks the `image:` field is declared, not that the file exists; real scans arrive later via the R2 checklist in each README).

**Acceptance criteria:** see `sprint/context/context-story-163-4.md` (AC1–AC4: all-anchors coverage, the_circuit style_hints, README+.gitkeep per world, validator clean on all 3 packs).

**Handoff:** To Hephaestus the Smith (Dev) for the implement phase.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings

### Dev (implementation)
- **Improvement** (non-blocking): `map.yaml` `image:` is a bare filename (e.g. `os_one_inch_glenross.jpg`) while the authoring checklist says to save the scan *in* `assets/maps/`. The resolution base for that filename is not pinned by this story — the UI RasterMap story must decide whether the image key resolves relative to the world root, `assets/maps/`, or the R2 manifest key. Affects `sidequest-ui` RasterMap (163-5, plan tasks 12–15) — needs an explicit image-path resolution rule. *Found by Dev during implementation.*
- **Note** (non-blocking): Anchors are placeholder pixel coordinates on a 1024×768 canvas (per plan). Real calibration against the sourced PD scans is a manual Keith step documented in each world's `assets/maps/README.md`; the scans + R2 upload are out of scope for this story (validator checks the `image:` field is declared, not that the file exists). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): annees_folles' placeholder anchors are on a ~1024×768 scale, but its pre-existing `cartography.yaml` declares `map_resolution: [1920, 1080]` (glenross is `null`, the_circuit has none). `map_resolution` is currently an **inert** model field — defined at `world.py:227` but read nowhere in the server — so this is latent, not a live defect. Affects `sidequest-ui` RasterMap (163-5) + the real-scan calibration step: reconcile the anchor coordinate space with the declared/real resolution when the annees_folles scan is sourced. *Found by Reviewer (edge-hunter) during code review.*
- **Improvement** (non-blocking): PD-basis wording is imprecise on two worlds. the_circuit claims `"US government work — public domain"` for a **state** highway map (federal §105 PD does not extend to state works); annees_folles applies the US "pre-1929 ⇒ PD" rule to a German-published Baedeker (foreign works want a source-country/URAA check). Text is transcribed **verbatim from the plan** (Tasks 10–11) and is placeholder provenance for scans not yet sourced — real legal vetting is checklist step 1 — so this is an upstream plan-wording refinement, not an implementation defect. Affects the two `map.yaml` + README pairs; tighten the `pd_basis`/checklist language when the real scans are sourced. *Found by Reviewer (security) during code review.*
- **Note** (non-blocking): the_circuit and annees_folles `map.yaml` lack the explicit "1024×768 canvas" comment that glenross carries; adding it would make the placeholder coordinate frame self-describing. Cosmetic. *Found by Reviewer (edge-hunter) during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. All three `map.yaml` bodies transcribed verbatim from plan Tasks 9–11; the annees_folles and the_circuit READMEs follow the plan's explicit "same checklist shape as Task 9, but source = X / filename = Y" instruction (adaptation is the spec, not a deviation). Region-id coverage verified against each world's live `cartography.yaml` (14 / 11 / 13) before writing.

### Reviewer (audit)
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: independently confirmed. The three `map.yaml` bodies match the plan's Task 9–11 YAML verbatim; the two adapted READMEs follow the plan's explicit "same shape, source=X" instruction (that IS the spec). Region-id correspondence verified in both directions (no missing, no extra).
- No **undocumented** deviations found. The PD-wording imprecision and the annees_folles map_resolution mismatch (see Delivery Findings) are not deviations from *this story's* spec — the PD text is verbatim-from-plan and the map_resolution field is pre-existing content untouched by this diff. Recorded as forward-looking delivery findings, not deviations.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (all new, `sidequest-content`):**
- `genre_packs/tea_and_murder/worlds/glenross/map.yaml` — raster treatment, OS one-inch sheet provenance, 14 node_anchors
- `genre_packs/tea_and_murder/worlds/glenross/assets/maps/README.md` + `.gitkeep` — sourcing checklist
- `genre_packs/pulp_noir/worlds/annees_folles/map.yaml` — raster treatment, Baedeker Paris plan provenance, 11 node_anchors
- `genre_packs/pulp_noir/worlds/annees_folles/assets/maps/README.md` + `.gitkeep`
- `genre_packs/road_warrior/worlds/the_circuit/map.yaml` — raster treatment, state-highway-map provenance, 13 node_anchors, `style_hints: {faction_layer: wasteland_defacement, routes: highway_tracing}`
- `genre_packs/road_warrior/worlds/the_circuit/assets/maps/README.md` + `.gitkeep`

**Verification (this IS the gate — trivial workflow, no unit tests):**
- Pack validator clean on all 3 packs: `tea_and_murder PASS (0 errors)`, `pulp_noir PASS (0 errors)`, `road_warrior PASS (0 errors)` via `uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/<pack>`.
- **Gate proven live (not silently skipped):** negative test — removed the `bromsviken` anchor from the_circuit → validator produced `ERROR: world 'the_circuit': raster map.yaml has no node_anchor for region 'bromsviken'`; restored → PASS. Confirms 163-3's anchor-coverage gate actually policed my content.

**ACs:** AC1 (all anchors + complete provenance) ✓ · AC2 (the_circuit style_hints) ✓ · AC3 (README + .gitkeep per world) ✓ · AC4 (validator clean on 3 packs) ✓.

**Branch:** `feat/163-4-raster-map-yaml-content` (sidequest-content, pushed → origin, 3 commits). Targets `develop`. No orchestrator changes.

**Handoff:** To Hermes Psychopompos (Reviewer) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (0 blockers) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 3 (all non-blocking/forward), dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 4 (2 distinct issues × 2 files) | confirmed 4 (LOW, non-blocking), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled subagents ran, 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 7 confirmed (all non-blocking — 1 MEDIUM, 6 LOW), 0 dismissed, 0 deferred

## Rule Compliance

Rules enumerated from `sidequest-content/CLAUDE.md` (Asset Hosting, Quality Rules), SOUL.md, and the map-treatment model contract (163-1). The diff is pure content YAML + markdown — no Python/TypeScript, so the lang-review/python & lang-review/typescript checklists are N/A (no governed types/functions in the diff).

- **Provenance PD claims must be accurate** — 3 raster treatments checked. glenross (`map.yaml:10`, "Crown copyright expired, >50 yrs", 1900 OS map) → **compliant** (matches UK Crown 50-yr rule). the_circuit (`map.yaml:10`, "US government work" for a *state* map) → **VIOLATION, confirmed** (state ≠ federal §105). annees_folles (`map.yaml:8`, US "pre-1929" rule on a German Baedeker) → **VIOLATION, confirmed**. Both downgraded to LOW/non-blocking with rationale (verbatim-from-plan placeholder text; legal vetting is checklist step 1) — **not dismissed** (recorded as delivery findings for the sourcing step).
- **No secrets/credentials in content** — 6 files checked (3 map.yaml + 3 README) → **0 violations**.
- **No path traversal / absolute path in `image:`** — 3 fields checked (`os_one_inch_glenross.jpg`, `baedeker_paris_plan.jpg`, `state_highway_map.jpg`) → all bare filenames, **compliant**.
- **R2 is canonical; sync + manifest are separate manual steps** (Asset Hosting) — 3 READMEs checked → all correctly instruct `r2_sync_packs.py` then `r2_manifest_from_bucket.py` as separate manual steps and name R2 canonical → **compliant**.
- **No binary image/LFS assets committed** — diff adds only YAML/md/empty `.gitkeep`; referenced JPGs correctly absent → **compliant**.
- **`MapTreatmentConfig` model contract (`extra="forbid"`, 163-1)** — all 3 map.yaml instantiate valid models via the real loader `_load_map_treatment` (no forbidden/typo'd keys) → **compliant** (proven, see [VERIFIED] below).
- **Anchor coverage (validator rule, 163-3)** — every cartography region has an anchor in all 3 worlds → **compliant**.

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. The mechanical deliverable is correct and complete — the story asked for three validator-clean raster `map.yaml` treatments with full anchor coverage, complete provenance, and the_circuit's defacement `style_hints`, plus per-world sourcing checklists. All four ACs are met and independently verified. Every confirmed finding is non-blocking and forward-looking (163-5 UI + Keith's real-scan calibration/sourcing).

**Observations (evidence-backed):**
- `[VERIFIED]` Anchor↔region correspondence exact in **both** directions — evidence: independent `set`-diff of `node_anchors` keys vs `cartography.yaml` `regions` keys → glenross 14/14, annees_folles 11/11, the_circuit 13/13; 0 missing, 0 extra/typo'd. Stronger than the validator (coverage-only).
- `[VERIFIED]` All 3 `map.yaml` load through the **real runtime loader** `_load_map_treatment` into valid `MapTreatmentConfig` objects — evidence: loader returned `treatment=raster`, correct image + anchor counts + provenance + style_hints for each; `extra="forbid"` accepted every field (proves no server-crash-at-load path a validator PASS would miss, since the validator reads raw YAML and skips the model).
- `[VERIFIED]` All anchors within the 1024×768 canvas; no duplicate coordinate pairs — evidence: bounds/dupe scan across all 38 anchors.
- `[VERIFIED]` AC2 met — the_circuit `map.yaml:11-12` carries `style_hints: {faction_layer: wasteland_defacement, routes: highway_tracing}`; glenross/annees_folles correctly `default`/`default`.
- `[EDGE]` `[MEDIUM]` annees_folles anchors (~1024×768 scale) vs pre-existing `cartography.yaml` `map_resolution: [1920, 1080]` mismatch — confirmed; **non-blocking** because `map_resolution` is an inert unconsumed field (`world.py:227`, read nowhere) and anchors are placeholders. Delivery finding for 163-5/calibration.
- `[SEC]` `[LOW]` PD-basis imprecision on the_circuit (state-vs-federal) and annees_folles (foreign-work) — confirmed (project-rule match, **not dismissed**); non-blocking (verbatim-from-plan placeholder; vetting deferred to sourcing step). Delivery findings.
- `[EDGE]` `[LOW]` the_circuit/annees_folles lack glenross's explicit canvas-size comment — cosmetic self-documentation nit.
- `[EDGE]` `[LOW]` referenced JPGs absent from working tree + R2 — by-design, disclosed via the sibling README sourcing checklists (corroborates Dev's finding).
- `[DOC]` Comment/README quality checked manually (comment-analyzer disabled): READMEs are clear, consistent, R2-doctrine-correct; only nit is the missing canvas comment above.
- `[SILENT]` / `[TEST]` / `[TYPE]` / `[SIMPLE]` / `[RULE]` — N/A: these subagents are disabled via `workflow.reviewer_subagents`, and a pure content-YAML diff has no swallowed-error paths, no test code, no governed types, no complexity/dead-code surface, and no lang-review-checklist-governed symbols for them to assess. Rule compliance was performed manually (see `## Rule Compliance`).

**Data flow traced:** `map.yaml` (on disk) → `_load_map_treatment(world_path)` → `MapTreatmentConfig` (extra="forbid") → `World.map_treatment` (`pack.py:199`) → served to the UI RasterMap (163-5, not yet built). Safe because the model parse succeeds for all 3 files and the pack validator independently enforces anchor coverage + provenance; the only downstream unknown (image resolution base, canvas scale) is explicitly deferred to 163-5 and captured as delivery findings.

**Pattern observed:** Faithful plan transcription with independent region-id verification against live cartography — the correct pattern for validator-gated content authoring (`glenross/map.yaml:14-27`).

**Error handling:** N/A for static content; the failure surface is the pack validator (163-3), which I re-confirmed fires on this content via Dev's negative test (missing-anchor → FAIL) and re-validated clean (all 3 packs PASS, 0 errors).

### Devil's Advocate

Argue this is broken. **The pins are fiction.** Every anchor is a made-up coordinate with no relation to any real map — because no map exists (the three JPGs are absent from the tree and from `r2_manifest.json`). If 163-5 ships a RasterMap before Keith sources and calibrates the scans, a player opening the Map tab gets pins scattered over a blank/broken image tile — a visibly broken feature. **The scale is a landmine.** annees_folles declares `map_resolution: [1920, 1080]` in cartography but the anchors are ~1024×768; a RasterMap that naively scales anchors by `map_resolution` would cram every annees_folles pin into the top-left ~53% of the canvas. **The license claims could bite.** If Keith trusts the_circuit's README ("state highway department official road map… these are US government works — public domain") he could source a still-copyrighted state map under a false federal-PD theory and ship an infringing asset — a real-world takedown risk, and exactly the kind of thing the "provenance must be accurate" rule exists to prevent. A confused author is actively mis-guided by the doc. **Dead redundancy:** each `assets/maps/` holds both a `.gitkeep` and a `README.md` — the `.gitkeep` is pointless once a README keeps the dir. **Rename fragility:** if any cartography region id is later renamed, its anchor silently orphans and the new id has no anchor. Now the counter-argument, which is why the verdict holds: none of these are live today. Images are absent *by design* and disclosed; `map_resolution` is provably unconsumed (grep: defined, never read), so the scale mismatch cannot mis-render anything until 163-5 wires it — and it's now a tracked delivery finding for that story; the PD text is placeholder, verbatim from the approved plan, with legal vetting mandated as checklist step 1 before any asset is sourced; the `.gitkeep` is harmless; and the rename case is precisely what the 163-3 validator gate catches loudly (proven). The mechanical contract this story owns — validator-clean, model-loadable raster map.yaml with full anchor coverage — holds under every check I ran. The brokenness is entirely latent and forward, correctly captured, not shipped. Verdict stands.

**Handoff:** To Themis the Just (SM) for finish-story.