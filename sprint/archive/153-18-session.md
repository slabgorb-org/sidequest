---
story_id: "153-18"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-18: [EVROPI-MISSING-PORTRAITS] render+sync 5 missing evropi picker portraits to R2 or drop from the manifest

## Story Details
- **ID:** 153-18
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** trivial
- **Stack Parent:** none
- **Type:** chore
- **Points:** 2
- **Priority:** p3
- **Repos:** content

## Story Context Reference

Full story context available at: `sprint/context/context-story-153-18.md`

The context document contains:
- Problem statement: 5 of 32 character-picker portraits on the `evropi` world (heavy_metal, WWN) return 404
- Broken portrait slugs and paths
- Fix directions: Option A (render+sync) or Option B (drop from manifest)
- Acceptance criteria and scope notes

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-22T14:37:35Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T13:51:10+00:00 | 2026-06-22T13:56:12Z | 5m 2s |
| implement | 2026-06-22T13:56:12Z | 2026-06-22T14:27:41Z | 31m 29s |
| review | 2026-06-22T14:27:41Z | 2026-06-22T14:37:35Z | 9m 54s |
| finish | 2026-06-22T14:37:35Z | - | - |
| implement | - | 2026-06-22T14:27:41Z | unknown |
| review | 2026-06-22T14:27:41Z | 2026-06-22T14:37:35Z | 9m 54s |
| finish | 2026-06-22T14:37:35Z | - | - |

## Sm Assessment

**Setup summary.** Story 153-18 is a content-only chore (2pts, p3, `trivial` workflow, `sidequest-content` only). A complete story context already exists at `sprint/context/context-story-153-18.md` (problem statement, the 5 broken slugs, the A/B fix tree, ACs, scope notes) — it was NOT regenerated. Branch `chore/153-18-evropi-missing-portraits` created in the content subrepo off `develop` (gitflow). No Jira (project has no Jira key).

**Routing.** `pf workflow type trivial` = **phased** (setup → implement[dev] → review[reviewer] → finish[sm]). Handing off to **dev** (Inigo Montoya) for the implement phase. Although asset rendering touches the art-director/world-builder domain, the work here is running documented scripts + a manifest edit, well within the implement phase; the context doc gives precise commands. If the Dev hits a hard render-pipeline dependency, fall back to Option B or raise it.

**Technical approach (from context doc — do not re-derive).** Two paths, no silent fallback:
- **Option A (preferred):** render the 5 missing portraits and sync to R2, then regenerate/verify the R2 manifest. Render/publish scripts (`render_batch`, `r2_sync_packs`, `r2_manifest_from_bucket`) live at the **orchestrator root** and run under the root venv (`uv run --project .`) — boto3 is there, not in sidequest-server.
- **Option B (fallback):** drop the 5 entries from `portrait_manifest.yaml` so the picker shows only the 27 resolvable portraits.

**Key gotchas for the Dev:**
- The 5 missing slugs: `picker_vaermm_copyist_f01`, `picker_zked_daggereye_f01`, `picker_gnome_tunnelwise_f01`, `picker_half_orc_minehand_m01`, `picker_antman_scoutdrone_m01` (path `genre_packs/heavy_metal/worlds/evropi/assets/portraits/<slug>.png`).
- **Verify slugs against a live bucket scan** (`r2_manifest_from_bucket` / `aws s3 ls`), NOT by assuming the manifest slug == on-disk filename — `render_common` keeps non-ASCII in slugs while `slugify_player_name` drops them; slug-rule divergence is a known mis-keying source.
- Confirm which clone the daemon launched from (`SIDEQUEST_GENRE_PACKS`) before rendering — author in the same clone.
- AC2 requires diffing manifest entries against the live bucket; AC3 requires no `naturalWidth==0` tiles in the evropi picker. Every manifest entry must resolve on R2 (200) or be removed.

**Setup deviations (corrected).** The `sm-setup` subagent (haiku) (1) mislabeled the workflow as "stepped" — it is `phased` per `pf workflow type trivial`; and (2) wrote an invalid `**Workflow:** trivial (stepped)` line and pre-set `**Phase:** finish Both corrected: `**Workflow:** trivial`, `**Phase:** finish so the documented setup→implement handoff records cleanly.

## Dev Assessment

**Implementation Complete:** Yes (Option A — render + sync, plus the root-cause content fix the finding didn't anticipate)

**Root cause (differs from the finding's hypothesis).** The finding guessed "render-local-not-synced-to-R2 drift." The actual cause: all 5 missing pickers carried a `backdrop_poi` that referenced the slugified *display name* of a POI rather than that POI's explicit `slug:` override, so the daemon's `PlaceCatalog.get("where:evropi/<bad>")` raised `CatalogMissError` and composition failed (`COMPOSE_FAILED`). They had never rendered — there was nothing local to sync. Mapping:
- `the_vaermm_hold_of_uteininnk` → `vaermm_hold_of_uteininnk`
- `the_daggereyes_forest_camp` → `daggereyes_camp`
- `the_deep_shaft` → `ingurdios_deep_shaft` (×3: gnome_tunnelwise, half_orc_minehand, antman_scoutdrone — the antman sibling `scentbearer_f01` already uses this exact key)

**Files Changed:**
- `genre_packs/heavy_metal/worlds/evropi/portrait_manifest.yaml` — 5 `backdrop_poi` remaps to real catalog slugs (the fix).
- `r2_manifest.json` — rebuilt from the live bucket after upload (+5 entries; 2694 → 2699).
- (Rendered PNGs are canonical in R2, gitignored locally — not committed, per content asset-hosting policy.)

**Verification:**
- Rendered 5/5 via the live daemon (≈170s each, 0 failures); each `R2 PUT` succeeded; manifest auto-rebuilt.
- **AC1** ✓ — all 5 CDN URLs return `200 image/png` (1.77–2.04 MB each).
- **AC2** ✓ — manifest-vs-`r2_manifest.json` diff: 49/49 resolve, MISSING=NONE, ORPHAN=NONE (32 pickers + 17 named NPCs).
- **AC3** ✓ — all 5 are valid non-zero PNGs returning 200; `naturalWidth==0` only arises from 404/corrupt bytes, neither present.

**Branch:** chore/153-18-evropi-missing-portraits (pushed to origin)

**Handoff:** To review (Reviewer / Westley).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 0 blocking (5 observations) | confirmed 0, dismissed 1 (bladtrablo mislist), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (pre-existing validator) | confirmed 0, dismissed 0, deferred 2 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 1 dismissed (with rationale), 2 deferred (pre-existing, out of scope)

## Reviewer Assessment

**Verdict:** APPROVED

Content-only change: 5 `backdrop_poi` remaps in `evropi/portrait_manifest.yaml` + the regenerated `r2_manifest.json` index. I read the diff, re-derived the root cause, and independently re-verified every claim in the Dev Assessment. The fix is correct, minimal, and complete. No Critical/High issues.

**Data flow traced:** picker `backdrop_poi` (manifest, oq-2) → render script passes `background=where:evropi/<slug>` → daemon `PlaceCatalog.get` (oq-1 catalog) → compose → render → R2 PUT → `r2_manifest.json` → CDN `<key>.png` → UI picker `<img>`. The break was at `PlaceCatalog.get` (CatalogMissError on the slugified-name refs); the remap to the POIs' explicit `slug:` keys closes it. Verified the new refs resolve and the CDN serves 200.

**Observations (≥5):**
- [VERIFIED] All 5 remapped backdrops resolve in `PlaceCatalog.load(heavy_metal, evropi)` — re-ran the daemon loader: `vaermm_hold_of_uteininnk`, `daggereyes_camp`, `ingurdios_deep_shaft` all present as keys. Evidence: catalogs.py:170-230 reads `history.yaml` POI `slug:`; the 3 slugs exist there. Rule check: complies with **No Silent Fallbacks** — the fail-loud `CatalogMissError` path (catalogs.py:265) is preserved, no fallback added.
- [VERIFIED] Semantic correctness — each target slug IS the POI the author named: `ingurdios_deep_shaft`=="The Deep Shaft", `vaermm_hold_of_uteininnk`=="The Vaermm Hold of Uteininnk", `daggereyes_camp`=="The Daggereyes' Forest Camp". The old values were merely slugified *names*; this is a precise correction, not a substitution. Evidence: evropi/history.yaml POI `name`/`slug` pairs. Rule check: no applicable project rule (this is an authorial-intent/correctness verification, not a type/security-governed item).
- [VERIFIED] No remaining dangling `backdrop_poi` in evropi after the fix — scanned all 49 manifest entries against the catalog: 0 dangling. Evidence: my Reviewer loader scan. Rule check: complies with **No half-wired features** (every manifest backdrop now resolves end-to-end).
- [VERIFIED] `r2_manifest.json` delta is exactly +5 keys (the 5 fixed pickers), 0 removals, no spurious mutation. Evidence: `git diff develop...HEAD -- r2_manifest.json` added-key grep + `--numstat` 35/0. Rule check: complies with content **"assets canonical in R2, spec/index in git"** — the index of record is updated to match the bucket; PNGs themselves stay out of git.
- [VERIFIED] AC1 — all 5 portraits return `200 image/png` on the CDN. Evidence: independent `curl` of all 5 URLs (Reviewer re-check, not trusting Dev). Rule check: no applicable project rule beyond the story ACs (verification of AC1).
- [VERIFIED] AC2/AC3 — manifest↔bucket diff 49/49 (0 missing, 0 orphan); all 5 are valid multi-MB PNGs → no `naturalWidth==0`. Evidence: Reviewer diff + CDN content-type/size. Rule check: no applicable project rule beyond the story ACs (verification of AC2/AC3).
- [PREFLIGHT] GREEN: pack-load canary 13/13, valid YAML/JSON, working tree clean, pack validator 0 errors (28 pre-existing field-shadow pydantic warnings, unrelated). Challenged: preflight mislisted the 5th new R2 key as `bladtrablo_raidcaptain_m01`; my direct `git diff` shows it is `zked_daggereye_f01` and that `bladtrablo_raidcaptain_m01` already existed on develop — dismissed the subagent's entry on direct evidence.

**Subagent dispatch tags:**
- [EDGE] — edge-hunter disabled via settings; content data change has no executable boundary paths. Assessed by Reviewer: the only "boundary" (catalog miss) is the very thing fixed; fail-loud preserved.
- [SILENT] — silent-failure-hunter returned 2 findings, both **pre-existing structural gaps in `sidequest-server/sidequest/cli/validate/pack.py` (NOT in this diff, NOT caused by it)**: (1) a dangling `backdrop_poi` is a validator *warning* not an *error* (pack.py:325) so it loads anyway and only fails loud at render time; (2) `_collect_poi_slugs` swallows a malformed-`history.yaml` read error (pack.py:247, low). Both **deferred** — out of scope for a content-only fix; #1 corroborates the Dev's Improvement finding and is re-captured below. The subagent confirms the diff introduces no new silent path.
- [TEST] — test-analyzer disabled; no tests in scope (content validated via pack-load canary, which is GREEN).
- [DOC] — comment-analyzer disabled; no code comments/docs in a YAML value remap.
- [TYPE] — type-design disabled; no type surface (string-valued YAML field, schema unchanged).
- [SEC] — security returned **clean**: no secrets/credentials in either file; `r2_manifest.json` adds only public-CDN key/md5/size/timestamp (matches existing schema); no spoiler/PII/info leakage; no injection surface.
- [SIMPLE] — simplifier disabled; the change is already minimal (5-line remap + regenerated index), nothing to simplify.
- [RULE] — rule-checker disabled. Assessed by Reviewer in Rule Compliance below.

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md/SOUL.md):** COMPLIANT. The fix preserves the loud `CatalogMissError` (catalogs.py:265); it does not add a fallback. (The validator's warning-not-error gap is pre-existing server code, flagged as a finding, not introduced here.)
- **Crunch in the Genre, Flavor in the World:** COMPLIANT. Backdrop POIs are world flavor; the change stays entirely in the world tier (`worlds/evropi/`).
- **Assets canonical in R2, spec in git (content CLAUDE.md):** COMPLIANT. Only the spec (`portrait_manifest.yaml`) + index of record (`r2_manifest.json`) are committed; rendered PNGs are gitignored and live in R2.
- **No half-wired features:** COMPLIANT. All 5 render, upload, index, and serve (200) end-to-end; all 32 picker options preserved (Option A, not the drop fallback).
- **OTEL on subsystem fixes:** N/A — no backend subsystem decision logic changed (content/asset spec only); the render pipeline already logs R2 PUTs + the manifest scan.
- **Spoiler protection:** COMPLIANT (security subagent) — evropi backdrops are cosmetic picker scenery, not plot secrets.

### Devil's Advocate
Suppose this is broken. The most dangerous illusion here is "it rendered, therefore it's right" — a render succeeding only proves the daemon *found a backdrop*, not the *correct* one. Could the remap point at a plausible-but-wrong POI? I checked the strongest version of this: each target slug's authored `name` in history.yaml is literally the string the old ref slugified ("The Deep Shaft" → `the_deep_shaft` vs explicit slug `ingurdios_deep_shaft`), so the remap recovers the author's exact intent rather than guessing — and the antman picker now matches its own sibling's backdrop. So that attack fails. Next: three pickers now share `ingurdios_deep_shaft` — does that read as lazy copy-paste? No; they are three distinct species (gnome/half-orc/antman) all "Refuser of the Long Mine," and a shared mine backdrop is the intended through-line; sharing a POI backdrop is already the norm (multiple working pickers share `the_drowned_ampitheatre`, `the_klas_horse_market`). Next: the `r2_manifest.json` commit is a 658KB generated file — a confused future author could hand-edit it or hit a merge conflict; but it's regenerated from the live bucket by `r2_manifest_from_bucket.py` (the documented index-of-record), so drift self-heals on the next rebuild — non-blocking. Next: what would a stressed filesystem / cross-clone setup produce? The daemon composes from oq-1's catalog while the script ran in oq-2 — a real split — but I and the Dev both verified the two manifests are identical and oq-1's catalog has all 3 target keys, and the PNGs landed on the *shared* R2 with canonical keys, so the server (oq-3) serves them via CDN regardless. Finally, a malicious/garbage `backdrop_poi`: still fail-loud at render (CatalogMissError); the pre-existing validator-warning gap means it wouldn't be caught at authoring time, which is exactly the deferred finding — but that is not a regression this diff introduces. Nothing here rises to blocking.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.

### Dev (implementation)
- **Gap** (non-blocking): The same dangling-`backdrop_poi` class of bug affects `heavy_metal/long_foundry` — `picker_kragmoor_thaumaturge_m01` → `the_coil_and_brand_guild_hall` and `picker_astran_feed_keeper_f01` → `the_keepers_of_the_hour_temple` both miss the PlaceCatalog (these are the "2 errored long_foundry pickers" noted in `docs/genre-pack-status.md`). Out of scope for this evropi-only story; warrants a sibling story fixed the same way (remap to the POI's explicit `slug:`, then render+sync). Affects `genre_packs/heavy_metal/worlds/long_foundry/portrait_manifest.yaml`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): No loader/validator catches a `backdrop_poi` that doesn't resolve in the world's PlaceCatalog — the failure only surfaces at render time as `COMPOSE_FAILED`. A pack-load or `validate` check that diffs every `backdrop_poi` against `PlaceCatalog.load(...)` keys would catch this authoring trap (slugified-name vs explicit `slug:`) before render. Affects the content validator / `scripts` render preflight. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Corroborates the Dev's validator-gap finding and pins the exact location — `_validate_portrait_manifest` routes a dangling `backdrop_poi` into `waiver_warnings`, not `content_errors`, at `sidequest-server/sidequest/cli/validate/pack.py:325`, so the pack loads despite a broken ref and the failure only surfaces at render as `CatalogMissError`. Promoting it to a hard `content_error` would catch the slugified-name-vs-explicit-`slug` trap at authoring time. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, low): `_collect_poi_slugs` (`pack.py:247`) returns an empty set on a malformed `history.yaml` and discards the read error, which would yield spurious "unknown POI slug" warnings instead of surfacing the real parse failure. Pre-existing; not exercised by this diff. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Fixed dangling backdrop_poi refs in addition to render+sync**
  - Rationale: The finding's stated cause was wrong; the true cause was dangling backdrop refs. Per "Fix it right / No silent fallbacks," fixing the references (keeping all 32 picker options) is correct and stays within the content repo and story scope (evropi picker portraits resolving). Option B (drop entries) was the fallback, not needed.
  - Severity: minor
  - Forward impact: none for this story; the sibling long_foundry gap is logged as a Delivery Finding for a follow-up.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

None recorded at setup.

### Dev (implementation)
- **Fixed dangling backdrop_poi refs in addition to render+sync**
  - Spec source: context-story-153-18.md, "Fix Direction" / Problem Statement
  - Spec text: "The likely cause is render-local-but-not-synced-to-R2 drift" → fix = "Render the 5 missing portraits and sync them to R2" (Option A), with no mention of editing the manifest's `backdrop_poi` fields.
  - Implementation: Edited 5 `backdrop_poi` values in `portrait_manifest.yaml` to the POIs' real catalog slugs, THEN rendered + synced. Pure render+sync was impossible — the renders had never succeeded (CatalogMissError on the bad backdrop refs), so there was no local PNG to sync.
  - Rationale: The finding's stated cause was wrong; the true cause was dangling backdrop refs. Per "Fix it right / No silent fallbacks," fixing the references (keeping all 32 picker options) is correct and stays within the content repo and story scope (evropi picker portraits resolving). Option B (drop entries) was the fallback, not needed.
  - Severity: minor
  - Forward impact: none for this story; the sibling long_foundry gap is logged as a Delivery Finding for a follow-up.

### Reviewer (audit)
- **Fixed dangling backdrop_poi refs in addition to render+sync** → ✓ ACCEPTED by Reviewer: necessary and correct. Pure render+sync was impossible (the renders had never succeeded — CatalogMissError on the bad refs), so there was nothing local to sync; the finding's "render-local-not-synced" premise was wrong. The remap targets each POI's exact authored `slug:` (verified: target slug == authored POI name), stays in-scope (content/world tier, evropi pickers resolving), preserves all 32 options, and keeps the fail-loud catalog contract. Option B (drop) was correctly avoided.
- No undocumented spec deviations found — the diff is exactly the 5 backdrop remaps + the regenerated R2 index; nothing diverged silently.

## Branch & Repos
- **Branch:** chore/153-18-evropi-missing-portraits
- **Branch Strategy:** gitflow (content repo targets develop)
- **Repos:** sidequest-content (content subrepo)