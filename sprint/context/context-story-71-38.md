# Story 71-38 Context

## Title
POI lore-gate slug normalization — decouple R2-object-key slug (verbatim) from HTML-anchor slug (slugify)

## Metadata
- **Story ID:** 71-38
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Epic:** Playtest bugfix — uncovered findings (coyote_star MP, 2026-05-27)

## Problem
ROOT CAUSE (confirmed on develop HEAD 2026-06-04, repro test test_reference_renderable_landscapes.py): the lore-page 'Renderable Landscapes' POI gate emits 0 <img> for EVERY underscore-slug world (oz: 12 munchkin_country-style POIs on R2, all suppressed). load_poi_image_slugs (reference_renderer.py:~1150) runs the authored POI slug from history.yaml points_of_interest[].slug — authored underscore, e.g. munchkin_country — through slugify(), producing munchkin-country (hyphen). That hyphenated slug feeds _gate_poi_slugs_on_manifest -> poi_image_key(pack, world, 'munchkin-country') (reference_renderer.py:~1228) -> genre_packs/.../poi/munchkin-country.png. But the real R2 object key is .../poi/munchkin_country.png (underscore: render_common.py writes <slug>.png from the authored slug verbatim). Hyphen-key vs underscore-manifest -> never matches -> gated_poi_slugs empty. One slugify-normalised slug does DOUBLE DUTY: (1) match the location-{slug} HTML card id / deep-link anchor (hyphen — correct, conventional, blast radius via reference_url_for_region, Story 63-6); (2) build the R2 object key via poi_image_key (must be underscore). The load_poi_image_slugs docstring encodes the wrong assumption verbatim: 'the authored POI slug (often underscore-style) and the card slug (hyphenated) both pass through slugify' — true for the anchor, the BUG for the R2 key.

ARCHITECTURAL DECISION (Architect / White Queen, 2026-06-04): DECOUPLE the two slug forms. Do NOT rename R2 assets. (A) R2 object key = authored POI slug VERBATIM (underscore). (B) HTML anchor / deep-link = slugify(authored slug) (hyphen). This is exactly the rule the already-shipped Location-tab fix (server #643, map_emit.py:585) uses — it builds poi_image_url from region_id VERBATIM — so decoupling makes the lore gate AGREE with the Location tab. Rejected alternative (rename all R2 POI assets to hyphen): forks the asset key away from the content identifier every OTHER consumer uses verbatim (render scripts, Location tab #643, rest.py/app.py POI readers), requires re-uploading every world's POIs, and still needs the render scripts changed — strictly more blast radius, pointing toward the presentation-only anchor convention instead of the stable content identifier.

IMPLEMENTATION NOTE (carry BOTH forms): load_poi_image_slugs returns frozenset[str] of slugified slugs, and gated_poi_slugs flows into _file_renders_by_stem(poi_image_slugs=...) where the card is keyed on the slugified anchor. The decouple must keep BOTH: feed poi_image_key the VERBATIM slug for the R2-key/gate comparison, while the card render / location-{slug} anchor keep using slugify. Carry a {verbatim -> slugified} mapping (or the verbatim slugs + slugify at the anchor site). Surgical — only the R2-key/gate comparison switches to verbatim; reference_url_for_region and the card ids are UNTOUCHED.

SCOPE: server only. Corrects the (now-archived) epic-65 65-8 gate doctrine — no new pattern, no ADR. Was filed as 65-17 before epic 65 archived; re-homed here. The #642 'Renderable Landscapes' section is correct and lights up the moment this lands; the Location tab (#643) already works for oz/gulliver regardless. Sibling: 71-39 (wonderland content article mismatch). Test against oz (assets present on R2).

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- DECOUPLE the slug forms: the R2-object-key/gate comparison feeds poi_image_key the AUTHORED POI slug VERBATIM (underscore, as authored in history.yaml points_of_interest[].slug); the HTML card anchor / location-{slug} id / reference_url_for_region deep-link continue to use slugify() (hyphen). poi_image_key is never fed a slugified value. Both forms are carried out of load_poi_image_slugs (verbatim for the gate, slugified for the anchor) so neither side is lost.
- LOAD-BEARING REPRO (extends test_reference_renderable_landscapes.py): an underscore-slug world whose r2_manifest.json contains .../poi/<underscore_slug>.png now yields a NON-EMPTY gated_poi_slugs and emits the POI <img>. Pin oz: its 12 munchkin_country-style keys -> 12 landscape cards render where today there are 0. Assert behaviorally (img emitted / gated set non-empty), not by source grep.
- DEEP-LINK REGRESSION GUARD (blast radius): reference_url_for_region and the location-{slug} card ids STILL resolve via the hyphen (slugify) form — an existing region-header deep-link does not break. Pin BOTH forms in one test (R2 key = underscore, anchor = hyphen, for the same authored slug) so the decouple can never silently re-couple.
- Fix the now-wrong load_poi_image_slugs docstring that claims the authored slug and the card slug 'both pass through slugify' — that conflation IS the bug. Document the two distinct forms: R2 object key = verbatim authored slug; HTML anchor = slugify(authored slug).
- No new OTEL span family (slug/keying correction is cosmetic-class per CLAUDE.md 'Not needed for: cosmetic'). The existing reference_manifest_loaded span (world_key_count) already proves the gate read the manifest; the verifiable signal is gated_poi_slugs becoming non-empty (POI imgs emit) — assert that, per No-Source-Text-Wiring-Tests.

---
_Generated by `pf context create story 71-38` from the sprint YAML._
