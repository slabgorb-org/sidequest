---
story_id: "71-38"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 71-38: POI lore-gate slug normalization — decouple R2-object-key slug (verbatim) from HTML-anchor slug (slugify)

## Story Details
- **ID:** 71-38
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-04T14:44:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T14:17:44Z | 2026-06-04T14:19:49Z | 2m 5s |
| red | 2026-06-04T14:19:49Z | 2026-06-04T14:31:48Z | 11m 59s |
| green | 2026-06-04T14:31:48Z | 2026-06-04T14:38:12Z | 6m 24s |
| review | 2026-06-04T14:38:12Z | 2026-06-04T14:44:20Z | 6m 8s |
| finish | 2026-06-04T14:44:20Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → next agent **tea** (RED phase).

**Scope:** Server-only. Decouple the two slug forms in `reference_renderer.py`:
- R2 object key = authored POI slug **verbatim** (underscore) via `poi_image_key`
- HTML anchor / deep-link = `slugify(authored slug)` (hyphen) — UNTOUCHED

**Root cause (per Architect, 2026-06-04):** one slugify'd slug does double duty — the hyphen form is correct for the `location-{slug}` card anchor but wrong for the R2 object key (which is written verbatim/underscore by render scripts). `load_poi_image_slugs` → `_gate_poi_slugs_on_manifest` → `poi_image_key` builds a hyphen key that never matches the underscore R2 key, so every underscore-slug world emits 0 `<img>` on the "Renderable Landscapes" lore page (oz: 12 POIs suppressed).

**Decision:** DECOUPLE, do not rename R2 assets. Makes the lore gate agree with the already-shipped Location-tab fix (server #643), which builds `poi_image_url` from `region_id` verbatim.

**TEA notes:**
- Named repro test exists: `test_reference_renderable_landscapes.py` — start there.
- Surgical: only the R2-key/gate comparison switches to verbatim. `reference_url_for_region` and card ids stay on slugify. Carry BOTH forms (a {verbatim → slugified} mapping).
- Test against **oz** (assets present on R2).
- Sibling 71-39 (wonderland content article mismatch) is OUT of scope.
- No new ADR/pattern — corrects archived 65-8 gate doctrine.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug with a clear repro; AC explicitly demands behavioral (not source-grep) assertions.

**Test Files:**
- `tests/server/test_reference_renderable_landscapes.py` — 3 new tests + 1 reframed existing test (Story 71-38 block at the bottom).
- `tests/fixtures/packs/reference_v2_fixture/worlds/poi_underscore_fixture/{world,history}.yaml` — NEW underscore-slug fixture world (mirrors oz/`munchkin_country`).
- `tests/fixtures/r2_manifest.json` — +1 entry: the verbatim underscore R2 key `.../poi_underscore_fixture/assets/poi/munchkin_country.png`.

**Tests Written:** 3 new + 1 reframed, covering AC1/AC2/AC3 behaviorally.
**Status:** RED — exactly one new test fails (the load-bearing repro); guards are green-now-and-must-stay-green.

| Test | AC | State now | Pins |
|------|----|-----------|------|
| `test_underscore_slug_world_renders_poi_with_verbatim_r2_src` | AC1, AC2, AC3 | **RED** | section present + card id `landscape-munchkin-country` (hyphen) + `<img src>` = verbatim `munchkin_country.png` (underscore) + hyphen src ABSENT. Both forms in one test → can't silently re-couple. |
| `test_underscore_world_omits_poi_not_on_r2` | AC2 | green (stays) | `emerald_void` (authored, not on R2) → no card. Guards against "render everything" instead of decouple. |
| `test_underscore_region_deep_link_still_resolves_via_hyphen_anchor` | AC3 | green (stays) | the REAL prod consumer path (`map_emit.py:554` → `load_poi_image_slugs` → `reference_url_for_region`) keeps the hyphen anchor. A naive "make `load_poi_image_slugs` return underscore" fix turns this RED. |
| `test_presenter_keys_cards_on_the_slugify_anchor_form` (reframed) | — | green (stays) | presenter contract (anchor = slugify) is intentionally UNTOUCHED by 71-38. Was `test_underscore_slug_is_hyphenated_by_the_gate_membership_check`, whose docstring said "revisit when fixed upstream" — done. |

### Rule Coverage (`.pennyfarthing/gates/lang-review/python.md`)

| Rule | Test(s) | Status |
|------|---------|--------|
| Test quality — meaningful assertions (no truthy-only) | all 4 assert specific HTML ids / src URLs / deep-link fragments | enforced |
| Test quality — distinct code paths (not all same path) | render-present / render-omit / deep-link-resolve are 3 distinct paths | enforced |
| Wiring test present | the route test drives the real `/reference/lore/{pack}/{world}` FastAPI route end-to-end | enforced |
| No source-text wiring tests | behavioral HTTP + public-function assertions only; zero `read_text()`/source-grep | enforced |

**Rules checked:** 4 of 4 applicable. **Self-check:** 0 vacuous tests (every assert checks a specific value, not `is_some`/`assert True`).

**Verified RED for the right reason:** route returns 200 and renders the world (`data-world="poi_underscore_fixture"`), but the "Renderable Landscapes" section is suppressed because the gate set is empty — the slugify-vs-underscore mismatch, not a fixture error.

**Handoff:** To Dev (Agent Smith) for GREEN. ⚠️ Read the blocking Delivery Finding below first.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/reference_renderer.py` — new `load_poi_slug_map()` returns `{anchor_slug: verbatim_slug}`; `load_poi_image_slugs()` is now its anchor-only projection (frozenset of slugify keys — `map_emit`/`reference_url_for_region` contract UNCHANGED); `_gate_poi_slugs_on_manifest()` takes the map, feeds `poi_image_key` the **verbatim** slug, returns surviving **anchor** slugs; call site passes the map; corrected the `load_poi_image_slugs` docstring (AC4).
- `sidequest/server/reference_presenters.py` — `_poi_image_html()` gains optional `image_slug` (verbatim) for the R2 `src`, defaulting to `slug` (legacy geography path untouched); `present_renderable_landscapes()` passes the verbatim authored slug so the `<img src>` addresses the real underscore R2 key while the card id stays the slugify anchor.

**Design (both TEA blocking findings addressed):**
- Img `src` now built from the verbatim slug (Finding #1) — the presenter already had it as `raw_slug`.
- `load_poi_image_slugs` kept slugified for the `map_emit` deep-link consumer (Finding #2) — the verbatim form is introduced only via `load_poi_slug_map` at the renderer's gate call.

**Tests:** Story file 11/11 GREEN (was 1 RED). Broader `reference/manifest/poi/lore/landscape/map_emit/location` suite: 725 passed, 13 skipped, 0 failed. `ruff` + `pyright` clean on both changed files.

**Pre-existing unrelated reds:** full-suite run surfaced 7 failures in `tests/agents/` + `tests/server/test_narration_clue_discovery_wiring.py` — **proven pre-existing** (identical failures with my source stashed; disjoint domain — narration/agents, not reference rendering). Tracked below + matches backlog 76-10. Not introduced by 71-38.

**Branch:** `feat/71-38-poi-lore-gate-slug-normalization` (pushed)

**Handoff:** To The Architect (TEA) for verify (simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | tests GREEN (11/11 story, 725 reference suite), 7 reds proven pre-existing on develop, ruff+pyright clean, 0 smells | N/A (mechanical) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — reviewer self-assessed edges (collision, empty-map, strip asymmetry) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — reviewer self-assessed (no swallowed errors; manifest fails loud) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — reviewer self-assessed (assertions specific, not vacuous) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — reviewer self-assessed docstrings (AC4 correction verified) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — reviewer self-assessed (dict/frozenset, pyright clean) |
| 7 | reviewer-security | Yes | findings | 2 (both LOW, latent) | confirmed 2 (LOW, non-blocking) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — reviewer self-assessed (no over-engineering) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — reviewer self-assessed Rule Compliance below |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (2 [SEC] LOW + 1 reviewer-found LOW strip-asymmetry), 0 dismissed, 0 deferred — none blocking.

## Reviewer Assessment

**Verdict:** APPROVED

**Cause and effect, traced.** The diff decouples two slug forms that one `slugify()` call previously conflated. I traced the full causality:

- **Data flow (input → DOM):** `history.yaml points_of_interest[].slug` → `load_poi_slug_map` stores `{slugify(slug): verbatim}` → `_gate_poi_slugs_on_manifest` keeps an **anchor** iff `poi_image_key(pack, world, verbatim)` is an EXACT member of `r2_manifest.json` keys → gated anchor set flows to `present_renderable_landscapes` → membership re-checked on the anchor (`slug not in poi_image_slugs: continue`) → `_poi_image_html(slug=anchor, image_slug=verbatim)` → `src = escape(resolve_asset_url(poi_image_key(..., verbatim)))`. The verbatim slug reaches the `<img src>` only after passing the manifest exact-match gate **twice** (presenter continue-guard + `_poi_image_html` membership check), and is HTML-escaped on emit.

**Observations (8):**
- `[VERIFIED]` The fix is correct end-to-end — `reference_renderer.py:1262-1265` feeds `poi_image_key` the **verbatim** slug for the manifest match and returns the **anchor** form; `reference_presenters.py:377` builds the `<img src>` from `raw_slug` (verbatim) while the card id stays `landscape-{slug}` (anchor, `:366`). Both TEA blocking findings are resolved. Evidence: the previously-RED `test_underscore_slug_world_renders_poi_with_verbatim_r2_src` is GREEN.
- `[VERIFIED]` map_emit deep-link consumer untouched — `load_poi_image_slugs` still returns the anchor frozenset (`reference_renderer.py:1181`), so `map_emit.py:554 → reference_url_for_region` (`slugify(region_id) in set`) keeps matching. Evidence: `test_underscore_region_deep_link_still_resolves_via_hyphen_anchor` GREEN; `map_emit` not in the diff.
- `[VERIFIED]` Legacy geography path byte-identical — `_poi_image_html`'s new `image_slug` defaults to `None → slug`, and `present_lore_geography` (`reference_presenters.py:295`) omits it. No behavior change on that path.
- `[VERIFIED]` No Silent Fallbacks honored — ungated POI is skipped before `_poi_image_html` (`:363`); manifest load still fails loud via `load_r2_manifest_keys`. Evidence: `test_underscore_world_omits_poi_not_on_r2` GREEN.
- `[VERIFIED]` OTEL unchanged — the `reference_manifest_loaded` span logic is outside the diff; AC5 (no new span family, slug-keying is cosmetic-class) respected. The verifiable signal (gated set non-empty → img emits) is asserted behaviorally.
- `[SEC][LOW]` CWE-113 (latent): `html.escape()` does not strip ASCII control chars, so a newline in a verbatim slug could inject an attribute — but only if `r2_manifest.json` itself held a newline key (a project-controlled artifact). Non-exploitable today; hardening recommended at `load_poi_slug_map` (`reference_renderer.py:1164`).
- `[SEC][LOW]` CWE-22 (latent): the verbatim slug is not path-validated before `poi_image_key`; the manifest exact-match gate fully contains it under the first-party-author model, but the charset reaching the URL builder widened from slugified (safe) to verbatim. Same one-line fix location.
- `[LOW]` (reviewer-found) `.strip()` asymmetry — the gate computes `verbatim = str(raw)` (no strip, `:1164`) while the presenter computes `raw_slug = str(...).strip()` (`:360`). Identical for clean slugs; for a whitespace-padded slug the gate key carries spaces and (in all realistic cases) safe-fails to exclusion. Worth aligning: strip in `load_poi_slug_map` too. This single change also closes both [SEC] findings.

### Rule Compliance (rule-checker disabled — reviewer-enumerated)

| Rule (source) | Instances in diff | Verdict |
|---|---|---|
| No Silent Fallbacks (CLAUDE.md) | gate exclusion (`:363`), manifest load (loud) | compliant — ungated → text-only, never broken img |
| OTEL: not needed for cosmetic (CLAUDE.md) | slug-keying correction | compliant — AC5 explicitly classes this cosmetic; existing `reference_manifest_loaded` span retained |
| No Source-Text Wiring Tests (CLAUDE.md) | all 3 new tests | compliant — behavioral HTTP + public-fn assertions, zero `read_text()`/grep |
| HTML output escaped, CWE-79 (python.md) | `src`, `name`, `accent` (`:260-263`) | compliant — all `escape()`d |
| File paths validated, CWE-22 (python.md) | `poi_image_key(verbatim)` | LOW finding — gated by manifest exact-match; rule's "user input" trigger is first-party content today |
| Type annotations (python.md) | `load_poi_slug_map → dict[str,str]`, `image_slug: str \| None` | compliant — pyright 0 errors |
| Test quality: meaningful assertions (python.md) | 4 tests | compliant — specific ids/src/fragments, no truthy-only |

### Devil's Advocate

Assume this code is broken. The most dangerous change here is the charset widening: before, every value reaching `poi_image_key` had passed `slugify()`, a natural sanitizer that guarantees `[a-z0-9-]`. After this diff, the **verbatim** authored slug — arbitrary bytes from a YAML file — flows into a URL builder (`f"{base}/{rel}"`, `resolve_asset_url`) and into an HTML attribute. A malicious or careless author who writes `slug: "../../portraits/secret"` produces the R2 key `.../poi/../../portraits/secret.png`; a `slug` containing a newline plus `data-onerror=...` could, post-escape, smuggle a second attribute into the `<img>` tag. What stops this today? Exactly one thing: the manifest exact-match gate. The verbatim slug must produce a `poi_image_key` string that is byte-identical to a key in `r2_manifest.json`. That file is generated by the render pipeline from the same authored slugs and is operator-controlled — so to weaponize either vector, an attacker must control BOTH `history.yaml` AND the manifest. Under the current first-party-author invariant that is not a realistic threat, and the security subagent rated both LOW. But the code's own comment (`reference_presenters.py:256`) acknowledges "the creator-authoring roadmap makes pack content less-trusted" — so the trust boundary is explicitly moving toward where these become real. A confused author is the more likely failure: a slug with a stray trailing space renders text-only with no diagnostic (the `.strip()` asymmetry), and they will not know why their landscape vanished. None of these rise to High: no path reaches the DOM without the double manifest gate, every interpolation is escaped, and the regression is confined to a first-party content surface. But the cheap, correct hardening — strip + reject control-chars/`/`/`..` in `load_poi_slug_map` — restores the safety `slugify()` used to provide for the key path and closes all three findings at once. I record it as a tracked non-blocking finding rather than block a fully-functional, AC-complete fix on first-party content.

**Deviation audit:** 4 deviations (2 TEA, 2 Dev) — all ACCEPTED (see Design Deviations).
**Pre-existing reds:** 7 confirmed identical on develop (narration/agents domain) — not introduced by 71-38; tracked under backlog 76-10.
**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The story's "surgical — only the R2-key/gate comparison switches to verbatim; the card render is UNTOUCHED" framing is *incomplete* for end-to-end correctness. The `<img src>` itself is built by `_poi_image_html` → `poi_image_key(ctx.pack, ctx.world, slug)` where `slug = slugify(raw_slug)` (hyphen). So even if the GATE is fixed to be non-empty, a gate-only change leaves the emitted `src` pointing at `.../poi/munchkin-country.png` (hyphen) — a 404 against the real underscore R2 asset. The fix MUST also propagate the VERBATIM slug into the src-building path so the emitted img addresses the asset that exists. Affects `sidequest/server/reference_presenters.py` (`present_renderable_landscapes` / `_poi_image_html` must build `src` from the verbatim slug while keeping `id="landscape-{slugify}"`) and `sidequest/server/reference_renderer.py` (`load_poi_image_slugs` / `_gate_poi_slugs_on_manifest` must carry the verbatim form through to the presenter, not just the gate comparison). *Found by TEA during test design.*
- **Gap** (blocking): The decouple CANNOT simply change `load_poi_image_slugs` to return verbatim (underscore) slugs. `map_emit.py:554` feeds its return straight into `reference_url_for_region(known_location_slugs=...)`, which matches `slugify(region_id)` (hyphen) against that set — so a verbatim-only return silently breaks every region-header deep-link. Either keep `load_poi_image_slugs` returning the slugified set (and introduce the verbatim form only inside the renderer's gate call at `reference_renderer.py:1414`) or carry a `{verbatim → slugified}` mapping and give each consumer the form it needs. `test_underscore_region_deep_link_still_resolves_via_hyphen_anchor` is the tripwire. Affects `sidequest/server/reference_renderer.py` + `sidequest/server/websocket_handlers/map_emit.py` (consumer). *Found by TEA during test design.*
- **Improvement** (non-blocking): AC4 (fix the now-wrong `load_poi_image_slugs` docstring claiming the authored slug and card slug "both pass through slugify") is a documentation change with no behavioral test — verifiable only by Reviewer reading, not by a test (per No-Source-Text-Wiring-Tests). Dev must do it; Reviewer must confirm it. Affects `sidequest/server/reference_renderer.py:1138-1146`. *Found by TEA during test design.*
- **Improvement** (non-blocking): Server test deps live in `[project.optional-dependencies] dev` (pytest, pyright, ruff); a bare `uv sync` does NOT install them and `uv run pytest` falls through to a global `~/.local/bin/pytest` on the wrong interpreter (missing opentelemetry). Run `uv sync --extra dev` then `uv run python -m pytest ...`. Affects local dev/CI bootstrap only. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 7 pre-existing test failures on the server suite are UNRELATED to 71-38 and were not introduced here (proven: identical failures with my source changes stashed). They are `tests/agents/test_61_12_output_format_compaction.py::test_output_only_prose_under_byte_budget`, `tests/agents/tools/test_apply_world_patch.py::test_active_stakes_path_applies`, and all 5 in `tests/server/test_narration_clue_discovery_wiring.py`. Affects the narration/agents domain (not reference rendering). Matches backlog story 76-10 ("clear pre-existing sidequest-server red tests"). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Defensive hardening for the widened slug charset. This diff changes the value reaching `poi_image_key` from the `slugify()`'d slug (safe `[a-z0-9-]`) to the **verbatim** authored slug (arbitrary bytes), relying solely on the `r2_manifest.json` exact-match gate for containment. Add a single guard in `load_poi_slug_map` (`sidequest/server/reference_renderer.py:1162-1165`) that `.strip()`s the verbatim AND rejects control chars / path separators before storing it (e.g. `if not verbatim or any(c < " " for c in verbatim) or "/" in verbatim: continue`). This closes three LOW findings at once: [SEC] CWE-113 newline-attribute-injection, [SEC] CWE-22 path-traversal (both latent under the first-party-author model but on the explicit trust-reduction roadmap per the `reference_presenters.py:256` comment), and the reviewer-found `.strip()` asymmetry between the gate (`:1164`, no strip) and the presenter (`reference_presenters.py:360`, stripped). Non-blocking: no path reaches the DOM without the double manifest gate, every interpolation is HTML-escaped, and content is first-party today. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tested the img `src` form, beyond the AC's "card render untouched" framing**
  - Spec source: context-story-71-38.md, AC1 ("only the R2-key/gate comparison switches to verbatim; ... the card ids are UNTOUCHED")
  - Spec text: "Surgical — only the R2-key/gate comparison switches to verbatim; reference_url_for_region and the card ids are UNTOUCHED."
  - Implementation: the RED test additionally asserts the emitted `<img src>` uses the verbatim underscore key (and that the hyphen src is absent), which forces a change to the src-building path the AC calls "untouched."
  - Rationale: a gate-only fix leaves the img `src` pointing at a 404 hyphen key — the feature would not actually work (AC2 demands "emits the POI <img>", i.e. a working image). Card *id* stays slugify (untouched, as the AC requires); only the *src* form is the extra pin. See the blocking Delivery Finding.
  - Severity: minor
  - Forward impact: Dev's GREEN must touch `reference_presenters.py` (src-building), not only the gate.
- **Reframed an existing test instead of deleting it**
  - Spec source: pre-existing `test_underscore_slug_is_hyphenated_by_the_gate_membership_check` docstring ("When the slug-normalization is fixed upstream this test should be revisited")
  - Spec text: the test asserted `html == ""` as "the load-bearing reason oz renders 0 POI images."
  - Implementation: renamed to `test_presenter_keys_cards_on_the_slugify_anchor_form`; kept the assertion but reframed the docstring to a presenter-level invariant (anchor = slugify), since 71-38 fixes the mismatch UPSTREAM so the presenter no longer receives a form-mismatched set in production.
  - Rationale: the assertion is still true and useful (presenter keying rule), but its old framing becomes misleading once the upstream gate is fixed.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Built the `<img src>` from the verbatim slug — touched the path the AC called "untouched"**
  - Spec source: context-story-71-38.md, AC1
  - Spec text: "Surgical — only the R2-key/gate comparison switches to verbatim; reference_url_for_region and the card ids are UNTOUCHED."
  - Implementation: added an optional `image_slug` to `_poi_image_html` and pass the verbatim authored slug from `present_renderable_landscapes`, so the `<img src>` addresses the verbatim underscore R2 key. The card *id* (`landscape-{slugify}`) and `reference_url_for_region` are genuinely untouched, as the AC requires.
  - Rationale: a gate-only fix leaves the `src` as a 404 hyphen key — AC2 ("emits the POI <img>") demands a *working* image. Confirmed by TEA's blocking Finding #1 and the RED test, which asserts the verbatim src. The "untouched" clause holds for the anchor/card-id, not the src.
  - Severity: minor
  - Forward impact: none — `image_slug` defaults to `slug`, so every other `_poi_image_html` caller (legacy geography path) is byte-identical.
- **Carried a `{anchor: verbatim}` map rather than changing `load_poi_image_slugs`'s return type**
  - Spec source: context-story-71-38.md, IMPLEMENTATION NOTE
  - Spec text: "Carry a {verbatim -> slugified} mapping (or the verbatim slugs + slugify at the anchor site)."
  - Implementation: new `load_poi_slug_map()` returns `{anchor: verbatim}`; `load_poi_image_slugs()` becomes its anchor-only projection (unchanged frozenset contract). The gate consumes the map; the `map_emit` deep-link consumer keeps the anchor frozenset.
  - Rationale: keeps the `map_emit` → `reference_url_for_region` consumer (TEA Finding #2) byte-identical while giving the gate the verbatim form. Map keyed `{anchor: verbatim}` (not `{verbatim: anchor}`) because consumers look up by the anchor.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: "Tested the img `src` form, beyond the AC's untouched framing"** → ✓ ACCEPTED by Reviewer: correct call — AC2 demands a *working* `<img>`, which requires the verbatim src; the card id stays slugify as the AC requires. The "untouched" clause holds for the anchor only.
- **TEA: "Reframed an existing test instead of deleting it"** → ✓ ACCEPTED by Reviewer: the renamed `test_presenter_keys_cards_on_the_slugify_anchor_form` pins a real presenter invariant (anchor = slugify) and stays GREEN; reframing the now-stale docstring is preferable to deletion.
- **Dev: "Built the `<img src>` from the verbatim slug"** → ✓ ACCEPTED by Reviewer: implements TEA's blocking finding correctly; `image_slug` defaults to `slug` so the legacy geography path is byte-identical (verified — `present_lore_geography` omits the arg).
- **Dev: "Carried a `{anchor: verbatim}` map rather than changing `load_poi_image_slugs`'s return type"** → ✓ ACCEPTED by Reviewer: the cleanest way to satisfy both consumers — the gate gets verbatim, `map_emit`'s deep-link consumer keeps the anchor frozenset unchanged. `{anchor: verbatim}` keying is the right direction (lookups are by anchor).
- No undocumented deviations found — the diff matches the logged deviations exactly.