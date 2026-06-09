---
story_id: "100-3"
jira_key: ""
epic: "100"
workflow: "tdd"
---
# Story 100-3: Phase 1 — Lore Cast section JSON projection (is_projectable gate, R2 portrait resolved server-side)

## Story Details
- **ID:** 100-3
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-08T23:08:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-08T22:40:15Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Story context (`context-story-100-3.md`) had no problem statement and no acceptance criteria — TEA derived the contract from the story title, the spec reference, and the already-shipped HTML path (`present_lore_cast`, `_cast_entry_is_projectable`, `_gate_cast_slugs_on_manifest` in `reference_renderer.py`). Affects `sprint/context/context-story-100-3.md` (ACs should be backfilled from the RED contract). *Found by TEA during test design.*
- **Gap** (non-blocking): The migration spec `docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md` is referenced by the epic/story but is NOT present in this `oq-1` clone (only in `sidequest-server/docs/`, where the React-migration spec also could not be located). TEA proceeded from the existing code as the source of truth for the Cast data shape and the two firewalls. *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

## TEA Assessment

**Tests Required:** Yes
**Reason:** New projection behavior (Cast section JSON) with two load-bearing security firewalls — not a chore.

**Test Files:**
- `sidequest-server/tests/server/test_reference_cast_projection.py` — RED-phase contract for the Cast section JSON projection (`build_cast_section`) and its wiring into `build_lore_projection`.

**Tests Written:** 22 tests across 6 groups covering the 5 required ACs:
- AC "NPCs passing is_projectable appear": `test_ratified_npc_appears_in_output`, `test_entry_without_name_is_skipped`
- AC "NPCs failing is_projectable excluded": `test_unratified_npc_is_excluded`, `test_quoted_string_observation_pending_still_withholds`, `test_all_unratified_projects_to_none`, plus reuse guard `test_is_projectable_is_the_gate_not_a_reimplementation`
- AC "R2 portrait URL resolved (not raw path)": `test_portrait_url_resolved_when_on_r2`, `test_portrait_url_is_null_when_not_on_r2`, `test_client_never_sees_raw_r2_key_or_path`, `test_portrait_slug_uses_explicit_id_when_present`
- AC "keeper fields excluded (security)": `test_keeper_npc_fields_never_cross_the_boundary`, `test_cast_member_carries_only_allowlisted_keys`
- AC "Cast appears in build_lore_projection output" (wiring): `test_lore_projection_includes_cast_section`, `test_lore_projection_cast_withholds_unratified`, `test_lore_projection_omits_cast_when_no_manifest`, plus OTEL wiring (`test_resolved_portrait_fires_resolved_span`, `test_missing_portrait_fires_not_found_span`, `test_lore_projection_cast_fires_unratified_skipped_span`)

**Status:** RED — collection fails with `ImportError: cannot import name 'build_cast_section'`. All other imports (build_lore_projection, the three reference spans, the conftest span helper) resolve, so the failure is precisely the not-yet-implemented contract.

**Contract pinned (Dev implements):**
- `build_cast_section(entries, *, pack, world, portrait_on_r2_slugs) -> dict | None` — mirrors `build_lore_map_section` (pre-gated R2 slug set passed in; does not load the manifest itself). Section shape `{"id": "cast", "label": "Cast", "members": [{"slug", "name", "role", "appearance", "portrait_url"}]}`. Returns `None` when no projectable member survives.
- `build_lore_projection` appends a `cast` section built from `load_cast_entries` + the `is_projectable` ratification gate + the R2 portrait gate (`_gate_cast_slugs_on_manifest`).
- Reuse, do not reimplement: ratification via `sidequest.game.npc_pool.is_projectable` (the shape assertions are reconcilable; the firewall/reuse/server-side-URL assertions are non-negotiable).

**Handoff:** To Dev for implementation (`.session/100-3-handoff-red.md`)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/reference_projection.py` — implemented `build_cast_section(entries, *, pack, world, portrait_on_r2_slugs) -> dict | None` (ratification gate via `_cast_entry_is_projectable`, server-side R2 portrait resolution via `resolve_asset_url(portrait_image_key(...))`, allowlisted member keys, per-member resolved/not-found spans, `None` when empty) and wired it into `build_lore_projection()` after the map section (loads `load_cast_entries`, fires `reference_npc_unratified_skipped_span` with the withheld count, gates slugs on the R2 manifest).
- `sidequest/server/reference_renderer.py` — routed `_cast_entry_is_projectable` through `npc_pool.is_projectable` (module attribute) so the single-source ratification gate is reused, not reimplemented, and the reuse spy test lands.
- `tests/server/test_reference_cast_projection.py` — TEA-owned; fixture helper `_world_dir_with_cast` seeds an empty `r2_manifest.json` at the gate's discovery path (the gate fails loud without it — No Silent Fallbacks).

**Tests:** 19/19 passing in `test_reference_cast_projection.py` (GREEN). 23/23 sibling projection tests pass (no regression). Pre-existing DB-dependent `TestClient` reference tests (`SIDEQUEST_DATABASE_URL` unset) fail/error on the clean RED checkout too — unrelated to this story.
**Branch:** feat/100-3-lore-cast-section-projection (pushed)

**Handoff:** To review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 26/26 tests GREEN, lint clean post-fix | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | N | Skipped | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | N | Skipped | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 2 [MEDIUM], dismissed 0, deferred 3 [LOW] |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1 [MEDIUM], dismissed 0, deferred 2 [LOW] |
| 6 | reviewer-type-design | N | Skipped | N/A | Disabled via settings |
| 7 | reviewer-security | N | Skipped | N/A | Disabled via settings |
| 8 | reviewer-simplifier | N | Skipped | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 1 [MEDIUM], dismissed 1 [pre-existing, not this diff], deferred 1 [LOW] |

**All received:** Yes (4 enabled subagents returned; 5 disabled per settings)
**Total findings:** 4 confirmed (0 High, 4 Medium/Low), 1 dismissed, 3 deferred as Low

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)
No TEA or Dev deviations were logged. Implementation matches the TEA contract exactly (shape, firewall, reuse). No undocumented spec deviations detected during review.

## Reviewer Assessment

**Verdict:** APPROVED

### Checklist

- [x] Subagent completion gate passed: all 4 enabled subagents received, table filled
- [x] Rule-by-rule enumeration: 18 rules checked (13 lang-review + 5 additional), 47 instances
- [x] Found 5+ observations (5 confirmed + 3 deferred Low)
- [x] Data flow traced: `portrait_manifest.yaml` → `load_cast_entries()` → `_cast_entry_is_projectable` ratification gate → `_gate_cast_slugs_on_manifest` R2 gate → `build_cast_section()` allowlist projection → `resolve_asset_url(portrait_image_key(...))` CDN URL → returned in JSON dict. Client never sees raw R2 key. Safe.
- [x] Wiring: `build_lore_projection` → `build_cast_section` wired and tested via wiring test (Group 6). `sections.append(cast_section)` at reference_projection.py:310.
- [x] Pattern: allowlist projection (not denylist) at reference_projection.py:143-151 — GOOD pattern. Future keeper fields can be added to `portrait_manifest.yaml` without leaking.
- [x] Error handling: `load_cast_entries` fails loud on malformed YAML and non-list `characters:`. `load_r2_manifest_keys` fails loud on absent/malformed manifest. `build_cast_section` returns `None` (not raises) on empty result — correct contract for a projection builder.
- [x] Security: keeper firewall is allowlist (5 explicit keys), not denylist. `_cast_entry_is_projectable` routes through `npc_pool.is_projectable` (pydantic coercion of quoted strings). Server-side URL resolution via `resolve_asset_url`. No user input reaches SQL or HTML.
- [x] Tenant isolation audit: N/A — this is a public reference projection with no tenant-scoped data.
- [x] Devil's Advocate: completed (see above). No new findings emerged that weren't already captured.

### Observations

**[DOC] [MEDIUM] Stale `build_lore_projection` docstring** at `reference_projection.py:258-259`. Says "This slice emits the map section only; Cast/POI/Timeline/generic-YAML sections land in later slices." Now emits map + Cast + generic-YAML. Actively misleading. Not blocking but should be fixed in the next story that touches this function.

**[TEST] [MEDIUM] Weak disjunctive assertion** at `test_reference_cast_projection.py:152`. `assert section is None or all(m["name"] != "Phantom" ...)` accepts a non-None empty section, which would pass if the contract changed from `None` to `{}`. The `test_all_unratified_projects_to_none` test provides coverage but this specific test should assert `None` directly. Non-blocking — covered elsewhere.

**[TEST] [MEDIUM] xdist cache pollution risk** at `test_reference_cast_projection.py:441`. `load_r2_manifest_keys.cache_clear()` is process-global — evicts all cached manifest entries in the worker, not just the test's tmp_path entry. Under xdist, a subsequent test in the same worker that relied on a cached manifest path from a prior test gets a re-read on a potentially cleaned-up path. Low actual risk (pytest doesn't eagerly clean tmp_path during runs), but the pattern is fragile. Non-blocking.

**[RULE] [LOW] Private symbol cross-module import** at `reference_projection.py:14`. `_cast_entry_is_projectable` (underscore-prefixed, private) imported from `reference_renderer`. This is a new import introduced by this story. The pattern is pre-established in this module pair (`_gate_cast_slugs_on_manifest`, `_humanize_label`, `_is_devnote` already cross this boundary). Consistent with codebase convention; not a stated project rule. Low severity.

**[RULE] [LOW] `_gate_cast_slugs_on_manifest` private import** at `reference_projection.py:15`. Pre-existing (not introduced by this diff) — dismissed from blocking scope. Same coupling concern as `_cast_entry_is_projectable` above.

**[DOC] [LOW] `build_cast_section` double-gate contract ambiguity**. Caller (`build_lore_projection`) pre-filters to ratified entries, then passes them to `build_cast_section` which re-gates internally. Defense-in-depth is intentional, but the docstring says "project the RATIFIED NPC cast" (implying caller pre-gates) while the body also gates. The contract is ambiguous for future callers. Non-blocking.

**[DOC] [LOW] RED-phase framing stale** in `test_reference_cast_projection.py` module docstring. Says "these symbols do not exist yet" — they now exist. Future readers will be confused. Non-blocking cosmetic issue.

**[VERIFIED] Keeper firewall** — allowlist projection at reference_projection.py:143-151. Exactly 5 keys: `slug`, `name`, `role`, `appearance`, `portrait_url`. No `**entry` splat. `test_keeper_npc_fields_never_cross_the_boundary` and `test_cast_member_carries_only_allowlisted_keys` both pass. Complies with CLAUDE.md SOUL principle (no keeper content crosses the public boundary).

**[VERIFIED] `npc_pool.is_projectable` reuse** — `reference_renderer.py:1359` calls `npc_pool.is_projectable(member)` (module-attribute style). Monkeypatch on `npc_pool.is_projectable` fires correctly. `test_is_projectable_is_the_gate_not_a_reimplementation` passes. The import change in reference_renderer.py (module import instead of direct name import) is the minimal correct change to enable the spy.

**[VERIFIED] OTEL wiring** — three spans fire: `reference_portrait_resolved_span` per on-R2 slug (reference_projection.py:134), `reference_portrait_not_found_span` per missing slug (reference_projection.py:138), `reference_npc_unratified_skipped_span` once per cast-bearing world carrying the withheld count (reference_projection.py:287-292). All tested in Groups 5-6. CLAUDE.md OTEL Observability Principle satisfied.

**[VERIFIED] Server-side URL resolution** — `resolve_asset_url(portrait_image_key(pack, world, slug))` at reference_projection.py:136 returns absolute CDN URL. Client never receives raw R2 key or manifest path. `test_portrait_url_resolved_when_on_r2` asserts `startswith("http")` and key segment in URL.

**[VERIFIED] No Silent Fallbacks** — `load_r2_manifest_keys` raises `FileNotFoundError` on absent manifest and `ValueError` on malformed JSON/wrong shape. `_world_dir_with_cast` seeds empty `r2_manifest.json` to trigger the gate without the loud failure. `test_lore_projection_omits_cast_when_no_manifest` verifies the no-manifest path correctly skips the R2 gate entirely.

### Devil's Advocate
The double-gating contract is a maintenance time-bomb: `build_lore_projection` pre-filters to `ratified_entries`, then `build_cast_section` re-runs `_cast_entry_is_projectable`. A future developer who reads the function's internal gate might remove the pre-filter from `build_lore_projection`; another who reads the "RATIFIED NPC cast" docstring might remove the internal gate. The ping-pong is silent — no test enforces which side owns the gate. `test_quoted_string_observation_pending_still_withholds` uses a disjunctive assertion that would pass on an empty-but-non-None section, allowing a contract change to slip. The `cache_clear()` in `_world_dir_with_cast` is process-global and could evict cached manifest paths from other tests in the same xdist worker, triggering FileNotFoundError on re-read. The `_KEEPER_NPC_FIELDS` set omits `observation_pending: True` — the most critical keeper visibility flag — so the keeper-firewall test doesn't verify this specific sentinel can't leak. The stale docstring actively misdirects future developers about the function's scope. After all of this adversarial analysis: none rise above Medium. The double-gate is defense-in-depth (the correct behavior fires regardless of which gate owns it). The weak assertion is compensated by `test_all_unratified_projects_to_none`. Cache risk is low (pytest doesn't clean tmp_path mid-run). The keeper fields gap is closed by the allowlist test. The stale docstring is documentation rot, not runtime failure.

**Data flow traced:** `portrait_manifest.yaml` on disk → `load_cast_entries(world_dir)` (yaml.safe_load, characters list) → `_cast_entry_is_projectable(e)` (pydantic coercion of `observation_pending`) → `_gate_cast_slugs_on_manifest(authored_slugs, pack_dir=...)` (R2 manifest read, fail-loud on absent) → `build_cast_section(ratified_entries, portrait_on_r2_slugs=gated_slugs)` → allowlist projection with `resolve_asset_url(portrait_image_key(pack, world, slug))` CDN URL → `sections.append(cast_section)` → JSON dict returned to caller. Client receives finished URL string or `null`. No raw R2 key ever leaves the server.

**Pattern observed:** Allowlist projection (not denylist) at `reference_projection.py:143-151`. Only 5 explicit keys (`slug`, `name`, `role`, `appearance`, `portrait_url`) are written to the member dict. Future keeper fields added to `portrait_manifest.yaml` are automatically blocked without any code changes — the firewall is additive-safe.

**Error handling:** `load_cast_entries` raises `ValueError` on malformed YAML and non-list characters; `load_r2_manifest_keys` raises `FileNotFoundError`/`ValueError` on absent/malformed manifest; `build_cast_section` returns `None` on empty result (not raises) — correct for a projection builder. The No Silent Fallbacks principle holds throughout.

**Handoff:** To The Announcer (SM) for finish-story.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Improvement** (non-blocking): `build_lore_projection` docstring (`reference_projection.py:258`) says "This slice emits the map section only" — stale since story 100-2 added generic-YAML and this story adds Cast. Should be updated to reflect all three emitted section types. Affects `sidequest/server/reference_projection.py` (docstring update only). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_quoted_string_observation_pending_still_withholds` at `test_reference_cast_projection.py:152` uses a disjunctive assertion that accepts non-None empty sections. Should assert `section is None` directly. Affects `tests/server/test_reference_cast_projection.py`. *Found by Reviewer during code review.*