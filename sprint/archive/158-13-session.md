---
story_id: "158-13"
jira_key: ""
epic: "158"
workflow: "trivial"
---
# Story 158-13: 158-7 follow-up: harden party-advance tests (surface_ascent + lateral coverage, OTEL party_advance/anchor_pc span assertions) + cleanups (drain_calls counter, dogfight witness-key, telemetry comment)

## Story Details
- **ID:** 158-13
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-23T21:29:03Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T23:59:59Z | 2026-06-23T21:15:07Z | -9892s |
| implement | 2026-06-23T21:15:07Z | 2026-06-23T21:23:45Z | 8m 38s |
| review | 2026-06-23T21:23:45Z | 2026-06-23T21:29:03Z | 5m 18s |
| finish | 2026-06-23T21:29:03Z | - | - |

## Sm Assessment

**Story:** 158-13 — a 158-7 FOLLOW-UP cleanup (server-only, 2pt, trivial/refactor). It captures the non-blocking Reviewer "Improvement" findings recorded in `sprint/archive/158-7-session.md` (Reviewer section, lines ~114-118). **No new production behavior** — test hardening + one comment-precision fix.

**Routing:** trivial workflow (setup → implement → review → finish), phased. Next agent: **Dev** (implement phase). This is pure test/comment work, so trivial is correct — no RED phase needed.

**Scope (6 items, all in sidequest-server):**
1. `tests/agents/subsystems/test_movement_party_split_158_7.py` — add `test_colocated_party_ascends_together` (covers the untested `surface_ascent` reverse-seam advance site).
2. Same file — add a lateral-cartography-move variant (covers the untested lateral advance site). These two are 2 of 6 `_advance_colocated_peers` call sites with no co-located-party test.
3. Same file — strengthen `test_party_advance_emits_per_pc_movement_span` to assert the per-peer spans carry `party_advance=True` and `anchor_pc` OTEL attributes (the AC-4 lie-detector; attributes are already emitted, just unasserted).
4. `tests/agents/subsystems/test_movement_dispatch.py` — `_FakeHandle.drain()` increments a `drain_calls` counter no test asserts (dead instrumentation). Either drop it (plain `pass`) or assert `handle.drain_calls == 1` in the in-dungeon materialize test.
5. `tests/agents/test_59_30_witnesses.py` — witness-count test asserts `len(_WITNESSES) == 11` but not which key is new. Add `assert "dogfight" in _WITNESSES` (mirror the existing `movement`/`course` checks).
6. `sidequest/telemetry/spans/movement.py` — guard comment cites "a dropped sampling decision" as a NonRecordingSpan cause, but prod `init_tracer` uses `ParentBased(ALWAYS_ON)` with no remote parent → sampling can't drop a movement span absent an external `OTEL_TRACES_SAMPLER`. Tighten the comment; the guard itself is correct.

**Verification:** run the three touched test files green. `_advance_colocated_peers` (movement.py) emits the OTEL attrs the new assertions pin — Dev should confirm against the live emitter, not assume.

**Caveats for Dev:**
- Branch `feat/158-13-harden-party-advance-tests` is off `origin/develop` in sidequest-server (subrepo targets `develop`, not main).
- Scope ruff to changed files only — do NOT `ruff format .` the whole repo.

## Dev Assessment

**Implementation Complete:** Yes

All 6 SM-scoped items shipped. No production behavior change — 4 test-file edits + 1 comment-precision fix.

**Files Changed:**
- `tests/agents/subsystems/test_movement_party_split_158_7.py` — added `test_colocated_party_ascends_together` (the `surface_ascent` reverse-seam advance site: both PCs at `entrance`, non-`deeper` intent → both ascend to the seam owner `the_dropmouth`) and `test_colocated_party_moves_laterally_together` (the lateral cartography-adjacency site, via a new seam-free `_lateral_cartography()` fixture: both PCs at `market_square` → both hop to adjacent `temple_row`, `resolved_via="region_lateral"`). These cover the 2 of 6 `_advance_colocated_peers` call sites the 158-7 suite never exercised. Also strengthened `test_party_advance_emits_per_pc_movement_span` to assert the fanned-out PEER span (Harpo) carries `party_advance=True` and `anchor_pc="Groucho"` — the AC-4 OTEL lie-detector (the acting PC's span comes from the seam resolver and does NOT carry these; only `_advance_colocated_peers` stamps them).
- `tests/agents/subsystems/test_movement_dispatch.py` — assert `handle.drain_calls == 1` in `test_move_toward_uncommitted_edge_sync_materializes` (the in-dungeon materialize test, which passes a `_FakeHandle`; production awaits the onward-ring drain at movement.py:858). Chose to make the counter live instrumentation (it proves the affordance-race generation-before-narrate drain engaged) rather than delete it.
- `tests/agents/test_59_30_witnesses.py` — assert `"dogfight" in _WITNESSES` in `test_witnesses_count_is_eleven_and_docstring_not_stale`, so a different 11th registration can't pass the count check silently (mirrors the explicit `movement`/`course` key checks elsewhere).
- `sidequest/telemetry/spans/movement.py` — tightened the `_mirror_movement_span_to_sink` NonRecordingSpan guard comment: verified `init_tracer` (telemetry/setup.py:41) leaves the SDK default sampler (`ParentBased(ALWAYS_ON)`) in place and movement spans are roots with no remote parent, so a sampling drop is NOT a realistic cause — only a never-initialized tracer (or an external `OTEL_TRACES_SAMPLER` override) yields a non-recording span. Guard logic unchanged.

**Tests:** 76/76 passing across the three touched files (`-n0`). The 5 new/changed tests verified GREEN both via testing-runner and a direct targeted run. Ruff check + format clean on all 4 changed files (scoped).

**Branch:** `feat/158-13-harden-party-advance-tests` (pushed to origin).

**Handoff:** To Reviewer (The Merovingian) for code review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings. Every item was a self-contained test/comment improvement already root-caused in the 158-7 review; the production helper `_advance_colocated_peers` already emitted the `party_advance`/`anchor_pc` attributes the new assertions pin and the drain was already awaited at the asserted site — the tests just weren't checking them. *Found by Dev during implementation.*

### Reviewer (code review)
- No upstream findings during code review. The change set closes the 158-7 non-blocking test-coverage gaps exactly as scoped; the production paths it pins (surface_ascent, lateral cartography, peer-span attrs, onward-ring drain, dogfight witness) all already existed and were verified live. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implemented all 6 SM-scoped items exactly as described. For the two "either drop or assert" cleanups (drain_calls counter, witness-key), chose the ASSERT option in both cases — it converts dead/weak instrumentation into live behavioral coverage rather than removing it, which is the higher-value reading of the Reviewer findings and consistent with the OTEL lie-detector doctrine.

### Reviewer (audit)
- **Dev: chose ASSERT over DROP for both "either/or" cleanups (drain_calls counter, dogfight witness-key)** → ✓ ACCEPTED by Reviewer: both SM-scope items explicitly offered "drop OR assert"; choosing ASSERT is the strictly stronger reading — it turns dead/weak instrumentation into live behavioral coverage (drain awaited exactly once; the specific 11th witness key pinned) rather than deleting the signal. Verified non-vacuous: `_FakeHandle.drain_calls` is initialized to 0 (test_movement_dispatch.py:96) and incremented in `drain()` (:106), so `== 1` exercises the production drain at movement.py:858; `"dogfight" in _WITNESSES` pins the exact key the count check alone would miss. Consistent with the OTEL lie-detector doctrine. No spec conflict.
- **No undocumented deviations found.** The diff matches the logged scope exactly: 4 test-file edits (2 new party-split tests + 1 strengthened OTEL assertion + 1 drain assertion + 1 witness-key assertion) and 1 comment-only edit in `telemetry/spans/movement.py`. No production logic changed (`git diff` confirms the only non-test hunk is a comment block; guard logic byte-identical).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 0 (6 advisory observations) | confirmed 0, dismissed 0, deferred 0 — all 6 observations are verification prompts, each independently confirmed below |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (boundary analysis done by Reviewer — see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (the only error-path touched is the unchanged telemetry guard; assessed by Reviewer `[SILENT]`) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (test quality / vacuity assessed by Reviewer `[TEST]`) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (the comment-only edit assessed by Reviewer `[DOC]`) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (no type surface changed — test fixtures only; Reviewer `[TYPE]`) |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 (rules_checked: No-Silent-Fallbacks, ADR-047, no-secrets, no-PII — all compliant) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (change is minimal/additive; Reviewer `[SIMPLE]`) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (rule enumeration done by Reviewer — see Rule Compliance, `[RULE]`) |

**All received:** Yes (2 enabled returned clean; 7 disabled pre-filled)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A test-hardening + comment-precision change set (158-7 follow-up). Both enabled subagents returned clean; my independent trace of all four files confirms every new assertion is non-vacuous and pins real, pre-existing production behavior. No production logic changed.

**Data flow traced:** A co-located MP party submits a shared move → `run_movement_dispatch(player_name, additional_player_names=[peer])` resolves the acting PC's hop → `_advance_colocated_peers` fans the destination to every peer whose `pc_regions[peer] == from_region`, each emitting its own `movement.resolved` span with `party_advance=True`/`anchor_pc`. The two new tests drive the two `_advance_colocated_peers` call sites that 158-7 left uncovered (`surface_ascent` at movement.py:524, lateral cartography at :592), asserting both acting PC AND co-located peer land on the same node. Safe/non-vacuous because the peer assertion (`Harpo`/`temple_row` resp. `the_dropmouth`) is reachable ONLY through the fan-out, and `resolved_via` pins the exact production path so a wrong route fails loudly.

**Observations (8+):**
- `[VERIFIED]` `test_colocated_party_ascends_together` exercises the real `surface_ascent` path, not narration string-matching — evidence: routing is gated on `direction != "deeper"` (movement.py:493) + `surface_owner_for_entrance(cart)` (registry.py:81), and the test asserts `resolved_via == "surface_ascent"`. The free-text `"back up the rope"` is exit_descriptor flavor only; `direction="toward_exit"` drives the branch. Non-vacuous: `Harpo` reaches `the_dropmouth` only via `_advance_colocated_peers`.
- `[VERIFIED]` `test_colocated_party_moves_laterally_together` reaches the lateral block (not a silent skip on `dungeon_store=None`) — evidence: `_lateral_cartography()` has `routes=[]`, so `seam_route_for`/`seam_route_via_adjacency` return None, the entrance/ascent guard is skipped (`from_region="market_square"`), and `_in_dungeon` is False (store None) → the lateral resolver runs (movement.py:565) and stamps `resolved_via="region_lateral"`. The test pins that label + the peer landing on `temple_row`.
- `[VERIFIED]` The strengthened OTEL assertion isolates the PEER span correctly — evidence: it filters `pc_name == "Harpo"` and asserts `party_advance is True` + `anchor_pc == "Groucho"`; those attrs are stamped ONLY by `_advance_colocated_peers` (movement.py:324-325), never by the acting PC's seam-resolver span (deep_descent.py:55-69), so the assertion cannot false-pass on the anchor's span.
- `[VERIFIED]` `handle.drain_calls == 1` is real behavioral coverage — evidence: `_FakeHandle.drain_calls` init 0 (test_movement_dispatch.py:96), `drain()` increments (:106); production awaits `lookahead_handle.drain()` exactly once at movement.py:858 when a handle is present, which this test supplies. Would catch a regression that drops the affordance-race drain.
- `[VERIFIED]` `assert "dogfight" in _WITNESSES` pins the specific 11th key — evidence: the count check (`== 11`) alone would pass on any 11-key set; the membership assert mirrors the existing `movement`/`course` key checks (test_dogfight_dispatch_wiring.py:412, test_course_clock_dispatch_wiring.py:359).
- `[TEST]` (subagent disabled) Reviewer check: no vacuity in the new/changed assertions — each lands on a value that is only produced by the path under test (peer region, span attrs, drain count, registry key). The two new tests also follow the file's content-free fixture convention (synthetic `CartographyConfig`, in-memory store doubles, monkeypatched in-memory exporter). No implementation coupling beyond the established `additional_player_names` contract.
- `[DOC]` (subagent disabled) Reviewer check: the comment-only edit in `telemetry/spans/movement.py` is accurate — verified `init_tracer` (telemetry/setup.py:41) constructs `TracerProvider(resource=...)` with no explicit sampler, so the SDK default `ParentBased(ALWAYS_ON)` applies; a root movement span cannot be sampled out absent an external `OTEL_TRACES_SAMPLER`. The rewrite corrects the prior overstated "dropped sampling decision" cause. Cosmetic; no OTEL span required (CLAUDE.md exempts label/comment tweaks).
- `[SILENT]` (subagent disabled) Reviewer check: the `if not hasattr(span, "attributes"): return` guard is byte-identical (only its comment changed). It is not a silent fallback — it short-circuits a telemetry side-channel on a structurally-unrecordable span with no alternative path masked. Confirmed unchanged via `git diff`.
- `[TYPE]` (subagent disabled) Reviewer check: no type surface changed — the new `_lateral_cartography()` returns a real `CartographyConfig` built from `Region`/`Route` models (same as the existing `_hybrid_cartography()`); no new public API, no annotations weakened.
- `[SIMPLE]` (subagent disabled) Reviewer check: the new fixture and tests reuse existing helpers (`_party_snapshot`, `_pack_with_cartography`, `_movement`, `capture_spans`); no duplication, no over-engineering. Minimal additive change.
- `[SEC]` Confirmed clean (security subagent): test-only synthetic data — no secrets, no injection sink reached, `raw_action` never crosses the ADR-047 narrator boundary in tests, OTEL attrs carry only fixture region IDs / fictional names.
- `[EDGE]` (subagent disabled) Reviewer boundary check: the two new tests ARE the edge coverage the story exists for (the 2 untested fan-out sites). The non-co-located Agency guard (`test_non_colocated_peer_is_not_dragged`) and empty/None peer handling remain covered by the pre-existing suite. No new boundaries introduced.
- `[RULE]` (subagent disabled) Reviewer rule enumeration — see Rule Compliance below.

### Rule Compliance (CLAUDE.md / SOUL — applicable subset)
- **Every Test Suite Needs a Wiring Test:** Compliant. The suite retains `test_party_advance_wired_through_dispatch_bank` (real `run_dispatch_bank` path); the new tests drive the real `run_movement_dispatch`, not a private helper.
- **No Source-Text Wiring Tests:** Compliant. New assertions are OTEL span-attribute checks (in-memory exporter) and runtime registry-dict membership (`_WITNESSES`), never `read_text()`/source-grep.
- **OTEL Observability Principle:** Compliant/strengthened. The change tightens the OTEL lie-detector (peer-span `party_advance`/`anchor_pc` now pinned). The comment edit is cosmetic → no span required per the explicit exemption.
- **No Silent Fallbacks:** Compliant. No new error-swallowing; the unchanged telemetry guard is a structural skip, not a masked alternative path.
- **No Stubbing / No half-wired:** Compliant. No stubs; tests pin already-wired production paths.

### Devil's Advocate
Let me try to break this. **First angle — false GREEN via path bypass.** The most dangerous failure for a test-hardening story is a test that passes without exercising the path it claims. I attacked both new tests on this. For `test_colocated_party_moves_laterally_together` the suspicion is real: `dungeon_store=None` could send the handler down a `no_dungeon_store` or `region_mode_deferred` branch that never touches `_advance_colocated_peers`, leaving Harpo at `market_square` — but then `to_region == "temple_row"` AND `Harpo == "temple_row"` would both fail, so a bypass cannot produce a green. The test additionally pins `resolved_via == "region_lateral"`, which only the lateral resolver emits. Bypass refuted. For `test_colocated_party_ascends_together`, a bypass to `region_mode_deferred` would fail `resolved_via == "surface_ascent"`. Refuted. **Second angle — the peer assertion riding the anchor's span.** Could `test_party_advance_emits_per_pc_movement_span` pass by reading the acting PC's span instead of the peer's? No — it filters `pc_name == "Harpo"` and asserts exactly one such span, and `party_advance`/`anchor_pc` are stamped only in `_advance_colocated_peers`; the anchor's seam-resolver span omits them, so a regression that stopped fanning out would yield zero Harpo spans → `len(peer_spans) == 1` fails. **Third angle — the drain counter.** Could `drain_calls == 1` pass spuriously? Only if production stopped awaiting drain AND the fake still counted — but the fake only increments inside `drain()`, which production must call; drop the await and the count is 0 → fails. **Fourth angle — comment drift.** The comment now asserts a specific sampler fact; if `init_tracer` later adds an explicit non-ALWAYS_ON sampler the comment goes stale. That is a latent doc-rot risk, but it is strictly more accurate than what it replaced and the guard remains correct regardless; not worth blocking. **Fifth angle — fixture realism.** `_lateral_cartography` invents `market_square`/`temple_row` rather than reusing beneath_sunden regions; could that mask a real-world adjacency quirk? No — the lateral resolver is content-agnostic (operates on any `CartographyConfig.regions[*].adjacent`), and the isolation is deliberate to avoid the seam interference that real beneath_sunden adjacency would introduce. No finding survives. The change is sound.

**Handoff:** To SM (Morpheus) for finish-story.