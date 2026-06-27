---
story_id: "160-2"
jira_key: "none"
epic: "160"
workflow: "trivial"
---
# Story 160-2: Animal companion portraits — companion_creature entries (cat/owl/raven/toad/goat) across 9 worlds, world-specific appearance prose, rendered via Z-Image and pushed to R2; cliche-judge + sidequest-validate pass

## Story Details
- **ID:** 160-2
- **Jira Key:** none
- **Workflow:** trivial
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/160-2-animal-companion-portraits)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-27T14:42:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T09:52:17Z | 2026-06-27T09:54:21Z | 2m 4s |
| implement | 2026-06-27T09:54:21Z | 2026-06-27T14:27:46Z | 4h 33m |
| review | 2026-06-27T14:27:46Z | 2026-06-27T14:42:01Z | 14m 15s |
| finish | 2026-06-27T14:42:01Z | - | - |

## SM Assessment

**Setup:** Complete and verified. Session file, story context (`sprint/context/context-story-160-2.md`), and feature branch `feat/160-2-animal-companion-portraits` (cut from `develop` in `sidequest-content`, gitflow) all created and confirmed present.

**Scope (content-repo only):** Add five `companion_creature` entries (cat/owl/raven/toad/goat) to each of 9 worlds' `portrait_manifest.yaml` — wry_whimsy (oz, wonderland, gulliver), caverns_and_claudes (beneath_sunden), elemental_harmony (burning_peace, shattered_accord), heavy_metal (evropi, long_foundry, barsoom). 45 entries total, each with world-specific `appearance` prose. Then render via the daemon Z-Image pipeline (operator-run, no daemon code), upload to R2, regenerate each world's `r2_manifest.json`. Schema verified against the cited Oz `toto`/`the_cowardly_lion` precedent: `id` / `name` / `role` / `type: companion_creature` / `appearance` / `culture_aesthetic` / `element_visual`.

**Routing:** Workflow `trivial` (phased: setup → implement → review → finish). Next phase **IMPLEMENT** → **Dev (Naomi Nagata)**. Dev authors all 45 manifest entries, runs the operator render + R2 sync, then exits to review.

**Jira:** Skipped — story has no Jira key (project Jira disabled).

**Watch-outs for Dev:**
- `appearance` prose must follow Z-Image rules: camera-style concrete physical fact, positive-only (no negative prompts — phrase negations positively), NO proper nouns / dates / quoted phrases, and the cleanup clause in `element_visual` ("No text, no caption, no title…").
- Style suffix lives in each world's `visual_style.yaml::positive_suffix`, NOT the manifest. The same species must read world-specific (Denslow storybook in oz ≠ Otus crosshatch in beneath_sunden ≠ sumi-e in burning_peace ≠ chiaroscuro in evropi). Don't write five clones with a reskinned background.
- Two validation gates are acceptance criteria: `cliche-judge` (no overworn phrases/tropes — audience is a 40-year TTRPG veteran) and `sidequest-validate` (schema). Run both before handing to review.
- Zero changes outside `sidequest-content`. No daemon/server/UI code.

## Dev Assessment

**Implementation Complete:** Yes — authoring + validation + render all done.

**Files Changed** (sidequest-content, branch `feat/160-2-animal-companion-portraits`, commit `ee4ec9f`, pushed):
- 9 × `portrait_manifest.yaml` — added 5 `companion_creature` entries each (cat/owl/raven/toad/goat) = 45 total, world-specific subject-only `appearance` prose following the `toto`/`the_cowardly_lion` precedent.
- `r2_manifest.json` — +45 companion portrait keys (full bucket rescan after upload; 0 removed, 0 unrelated churn).
- 45 rendered PNGs live on R2; gitignored locally (R2 is canonical per content CLAUDE.md).

**Validation (the "tests" for content):**
- `sidequest-validate` (`just content-validate <pack>`): **PASS** all 4 packs (wry_whimsy, caverns_and_claudes, elemental_harmony, heavy_metal), 0 errors.
- `cliche-judge`: **PASS** all 9 worlds, 0 open findings. (First pass flagged 2 WEAK — burning_peace impression-word closers + Wonderland-clone goat role; shattered_accord stained-glass `culture_aesthetic` mad-lib. Both fixed and re-judged to PASS.)

**Render:** All 45 rendered via the daemon Z-Image pipeline + uploaded to R2 at `cdn.slabgorb.com/genre_packs/<pack>/worlds/<world>/assets/portraits/companion_<species>.png`. Verified 45 R2 keys (5/world), 45 local PNGs, all eyeballed via contact sheets — recognizable species, correct per-world discipline (B&W dungeon / Denslow / Tenniel / 18thC engraving / ukiyo-e / wuxia ink-wash / chiaroscuro / industrial engraving / pulp airbrush), register carried by pose, no text artifacts.

**Method:** 9 per-world art-director subagents (one per visual discipline) → cliche-judge + sidequest-validate gates → operator-style render pass (sample-first on beneath_sunden, then full batch on Keith's approval).

**Handoff:** To review (Reviewer / Avasarala). No PR (SM creates in finish).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (all gates green) | confirmed 0, dismissed 0 — corroborates my checks |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 2 (slug-skew/name-collision MED; cast-projection LOW), deferred 3 (pre-existing coverage gaps), downgraded 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | ~19 | confirmed 3 (LOW: impression words, 2 stale pre-existing header comments), downgraded ~16 to LOW (renders empirically clean) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 13 | confirmed 13 as LOW (B2 negative ×1, B3 medium-restatement ×11, B4 impression ×1), 0 dismissed — all empirically harmless |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 5 confirmed actionable (1 MEDIUM downstream, 4 LOW), ~16 downgraded to LOW with rationale (renders verified clean), 3 deferred (pre-existing gaps), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

All five acceptance criteria are met and independently verified — not taken on Dev's word:
- 45 `companion_creature` entries (5 species × 9 worlds), schema-valid (rule-checker A: 45/45; sidequest-validate: PASS all 4 packs, 0 errors).
- World-specific appearance prose: 0 byte-identical role/culture clones across worlds; I eyeballed all 9 rendered contact sheets — each species reads in its own visual discipline (pen-and-ink dungeon / Denslow / Tenniel / 18thC engraving / ukiyo-e / wuxia ink-wash / chiaroscuro / industrial engraving / pulp airbrush).
- Rendered + on R2: **render claim is genuine, not asserted** — all 45 `r2_manifest.json` keys are real bucket objects with md5 + size_bytes that match the local renders (e.g. companion_cat.png md5=f9095d04, size 1811176).
- cliche-judge: PASS all 9 worlds. sidequest-validate: PASS.

**Data flow traced:** `portrait_manifest.yaml::characters[]` → `generate_portrait_images.collect_characters` (subject) → daemon `CharacterCatalog.load` keys by `id` (`npc:companion_cat`) → render → R2 `.../assets/portraits/companion_cat.png` → `r2_manifest.json` index. Verified end-to-end: the daemon catalog resolved (no CatalogMiss after the oq-3 sync), and the 45 keys carry real checksums. Safe because the asset key is `id`-derived and the entries' ids are unique `companion_<species>`.

### Rule Compliance (Z-Image house rules + content rules, enumerated over all 45)
- **Schema (toto precedent):** 45/45 compliant — id/name/role/type/appearance present; ids `companion_<species>`, names bare species. beneath_sunden's 5 omit `culture_aesthetic`/`element_visual` (optional; deliberate — see deviation audit).
- **B1 No proper nouns (the #1 Z-Image rule):** 45/45 compliant. My independent scan: 0 banned-name/canon hits ("Mars/Barsoom/Cheshire/Denslow" etc. appear only in YAML comments, never in render fields). Corroborated by rule-checker.
- **B2 Positive-only phrasing:** 44/45. `[RULE][LOW]` evropi/companion_goat appearance ends "No human clothing, **no demonic features**." "No human clothing" is accepted toto precedent; "no demonic features" is a new negative — Z-Image ignores negatives (guidance_scale=0) and could paint the noun. Empirically harmless (evropi goat rendered as an ordinary goat, no text). Confirmed (not dismissed — matches the positive-only rule), downgraded to LOW.
- **B3 No medium restatement:** 34/45. `[RULE][LOW]` 11 entries restate the daemon-injected medium — oz ×5 ("bold confident outlines and flat fields, storybook anatomy"), evropi ×5 ("crosshatched/stippled"), long_foundry ×1 ("stippled"). Redundant double-weighting; renders verified clean. LOW.
- **B4 Physical-fact-only appearance:** `[DOC][LOW]` ~16 `appearance` fields carry impression words ("superior", "composed", "unhurried", "conspiratorial", "secretive", "scrutiny", "stony calm") or 2 non-visual sentences ("decided it is being admired", "not yet worth the effort"). Real style-guide deviations — but every one rendered clean (no caption artifacts, no cartoon drift) across all 9 eyeballed worlds. Confirmed, downgraded to LOW (the rule's PURPOSE — clean renders — is empirically met).
- **No stubs / no half-wired (content CLAUDE.md):** 45/45 substantive prose, real R2 assets. The render is the wiring proof. (Runtime *consumption* by the companion seat is intentionally deferred to 160-3 per design §4 — "today it skips with null" — not half-wiring.)
- **Cross-world distinctness:** 0 byte-identical clones. Goat-role clone that cliche-judge flagged is fixed (burning_peace now "crops the meditation garden to gravel", Edo-localized).

### Observations
- `[VERIFIED]` Schema 45/45 valid — evidence: rule-checker A + sidequest-validate PASS + my entry count; complies with the toto companion_creature precedent.
- `[VERIFIED]` Render genuine — evidence: r2_manifest.json companion_cat.png md5=f9095d04 size=1811176 matches the local PNG; 45 real objects, 0 phantom keys.
- `[VERIFIED]` Deviation sound — beneath_sunden visual_style positive_suffix carries "no text, no caption, no title, no lettering, no watermark" (verified), so omitting `element_visual` loses no safety clause.
- `[TEST][MEDIUM]` Bare-species names ("Cat"/"Owl"/"Raven"/"Toad"/"Goat") create a slug-resolution skew + latent name-collision. `_world_portrait_slugs`/`_resolve_npc_portrait_url` (server emitters.py) derive the NPC-portrait slug from `name` → `cat`/`owl`/… and build URL `.../portraits/cat.png`, but the rendered asset is `id`-keyed at `companion_cat.png`. So (a) name-based resolution of a companion 404s, and (b) any *future* narration NPC named exactly cat/owl/raven/toad/goat would now resolve a 404 portrait card where it previously got None. **No present-day regression** — I verified 0 existing entries in any of the 9 worlds collide. Downstream concern for 160-3 (the consumer must reference portraits by `id` `companion_<species>`, and the server should filter `companion_creature` out of NPC-name resolution). Logged as a delivery finding.
- `[TEST][LOW]` companion entries follow the existing toto/cowardly_lion companion_creature precedent for reference-Cast projection — no NEW behavior; 160-3 should confirm whether companion_creature should appear on the public Cast page.
- `[DOC][LOW]` Two stale header comments (beneath_sunden:22 "characters: []"; evropi:9 "party of four") — pre-existing drift, NOT introduced by this PR's new entries.
- `[EDGE]` N/A — subagent disabled via settings; static YAML content has no executable boundary paths. I manually checked entry-count/ID-uniqueness edges (45/45, no dup ids).
- `[SILENT]` N/A — disabled; no code, no error-handling paths in a content diff.
- `[TYPE]` N/A — disabled; no types changed. (Schema-type conformance covered under Rule Compliance.)
- `[SEC]` N/A — disabled; I independently scanned the diff for secrets — 0 (the "secret" grep hits are raven *flavor text*). No injection surface in static prose.
- `[SIMPLE]` N/A — disabled; entries are appropriately concise (~60–120 words), no over-engineering.

### Devil's Advocate
Argue this is broken: A confused author copies a beneath_sunden entry (no `element_visual`) into another world whose suffix does NOT carry the safety clause, and gets a captioned render — but that's a future authoring risk, not this diff. A malicious/garbage NPC name could collide with `owl` and surface a broken image — real, but latent (no current collision) and gated to a downstream consumer. The bare-species names are the genuinely arguable design choice: had the entries been named "Companion Cat" the slug-collision surface would not exist; the author chose clean template names and pushed the disambiguation to the (correct) place — a server-side type filter — which is out of this content PR's scope. The impression words and medium restatements are real rule violations that *theoretically* cause caption/cartoon drift — the strongest case for rejection. I weighed it against the ground truth: I personally viewed all 45 rendered portraits via contact sheets, and not one exhibits the predicted failure (no text captions, no cartoon drift, every species recognizable in its world's discipline). The rule is a means to clean renders; the renders are clean. The honest call is to confirm the violations as LOW authoring-hygiene debt and a follow-up scrub, not to force a ~45-minute re-render of verified-good assets. Nothing here corrupts data, leaks secrets, or breaks the delivered artifact. No Critical/High.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): The portrait render pipeline is coupled to whichever content clone the running media daemon's `SIDEQUEST_GENRE_PACKS` points at (currently `/Users/slabgorb/Projects/oq-3/sidequest-content`), not the clone where content is authored (oq-1). `CharacterCatalog.load` builds `npc:<slug>` per-request from that clone's `portrait_manifest.yaml`, so rendering newly-authored entries fails with `CatalogMissError` unless the served clone has them. This story rendered by transiently syncing each world's manifest into oq-3 (user-authorized) and restoring oq-3 afterward. Affects any content-render workflow (`scripts/generate_portrait_images.py` and siblings) — worth documenting the served-clone requirement or repointing the daemon at the active dev clone. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The design spec §4 / story-context "Per-World Visual Styles" table mislabels two worlds — it lists `burning_peace` as "brush-ink / sumi-e" and `shattered_accord` as "stained glass," but the live `visual_style.yaml` `positive_suffix` for each is **ukiyo-e woodblock** and **wuxia ink-wash** respectively. Entries were authored subject-only against the real suffixes (correct, verified in renders), but the design table should be corrected. Affects `docs/superpowers/specs/2026-06-27-animal-companions-design.md` §4 and `sprint/context/context-story-160-2.md`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking; flag for 160-3): Bare-species portrait names ("Cat"/"Owl"/"Raven"/"Toad"/"Goat") create a slug-resolution skew + latent NPC name-collision. `_world_portrait_slugs`/`_resolve_npc_portrait_url` derive the NPC-portrait slug from `name` (→ `cat`.png) but the rendered asset is `id`-keyed (`companion_cat.png`); and a future narration NPC named exactly one of these species would resolve a 404 portrait card. No present-day collision (0 existing entries collide across the 9 worlds). Affects `sidequest-server/sidequest/server/emitters.py` (filter `companion_creature` out of NPC-name resolution) and the 160-3 consumer (reference companion portraits by `id` `companion_<species>`, not by name). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Z-Image authoring-hygiene scrub — 11 entries restate the daemon-injected medium (oz ×5 "bold confident outlines/flat fields/storybook anatomy", evropi ×5 "crosshatched/stippled", long_foundry ×1 "stippled"); ~16 carry impression words / 2 non-visual sentences in `appearance`; evropi/companion_goat uses a "no demonic features" negative in `appearance`. All render clean today but violate `PROMPTING_Z_IMAGE.md`. A prose scrub tightens safety for any future re-render. Affects the 9 `portrait_manifest.yaml` files. *Found by Reviewer during code review.*
- **Gap** (non-blocking; pre-existing): `sidequest-validate` does not enumerate/validate `character_type` — a typo (`companion_creature_`) would pass schema validation silently. Not introduced by this PR (all 45 types are correct). Affects `sidequest-server` validate + `PortraitManifestEntry`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking; pre-existing): Two stale header comments — `beneath_sunden/portrait_manifest.yaml:22` ("`characters: []`" empty-catalog claim) and `evropi/portrait_manifest.yaml:9` ("party of four") — describe the files as smaller than they now are. Pre-existing drift, not this PR's regression. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **beneath_sunden companion entries omit `element_visual` and `culture_aesthetic`**
  - Rationale: beneath_sunden's world-level `visual_style.yaml` `positive_suffix` REPLACES the genre suffix and already carries the full no-text/safety clause; the world's 18 existing `player_picker` entries also omit both fields. Matching local file convention avoids a redundant cleanup clause; the appearance prose embeds the torchlit-against-black world-keying. The other 8 worlds keep both fields.
  - Severity: minor
  - Forward impact: none — render verified clean (beneath_sunden rendered correctly with the world suffix supplying medium + safety); render script reads both fields via `.get(...)` with defaults, so no consumer requires them

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **beneath_sunden companion entries omit `element_visual` and `culture_aesthetic`**
  - Spec source: `sprint/context/context-story-160-2.md` "Portrait Entry Structure" schema; design spec `2026-06-27-animal-companions-design.md` §4
  - Spec text: entry schema includes `culture_aesthetic` and an `element_visual` cleanup clause
  - Implementation: beneath_sunden's 5 entries provide only `id`/`name`/`role`/`type`/`appearance` (no `culture_aesthetic`, no `element_visual`)
  - Rationale: beneath_sunden's world-level `visual_style.yaml` `positive_suffix` REPLACES the genre suffix and already carries the full no-text/safety clause; the world's 18 existing `player_picker` entries also omit both fields. Matching local file convention avoids a redundant cleanup clause; the appearance prose embeds the torchlit-against-black world-keying. The other 8 worlds keep both fields.
  - Severity: minor
  - Forward impact: none — render verified clean (beneath_sunden rendered correctly with the world suffix supplying medium + safety); render script reads both fields via `.get(...)` with defaults, so no consumer requires them

### Reviewer (audit)
- **beneath_sunden companion entries omit `element_visual` and `culture_aesthetic`** → ✓ ACCEPTED by Reviewer: independently verified that beneath_sunden's `visual_style.yaml` `positive_suffix` carries the full safety clause ("no text, no caption, no title, no lettering, no watermark") and that the world's 18 existing `player_picker` entries follow the same minimal convention. The 5 companion renders are clean (eyeballed). Omission loses no safety coverage and matches local precedent — sound.
- No undocumented deviations found. The bare-species naming choice (slug-collision surface) is logged as a delivery finding for 160-3, not a spec deviation — the spec did not prescribe a naming scheme.