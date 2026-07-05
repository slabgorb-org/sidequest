---
story_id: "162-1"
jira_key: "162-1"
epic: "162"
workflow: "tdd"
---
# Story 162-1: Derive-don't-cache Monster Manual

## Story Details
- **ID:** 162-1
- **Jira Key:** 162-1
- **Workflow:** tdd
- **Stack Parent:** none

## Branch Information
**Branch Strategy:** gitflow (feat/162-1-derive-dont-cache-monster-manual)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-05T16:41:45Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-05T13:14:13.992402Z | 2026-07-05T13:17:17Z | 3m 3s |
| red | 2026-07-05T13:17:17Z | 2026-07-05T13:34:59Z | 17m 42s |
| green | 2026-07-05T13:34:59Z | 2026-07-05T15:30:31Z | 1h 55m |
| review | 2026-07-05T15:30:31Z | 2026-07-05T15:51:15Z | 20m 44s |
| green | 2026-07-05T15:51:15Z | 2026-07-05T16:08:08Z | 16m 53s |
| review | 2026-07-05T16:08:08Z | 2026-07-05T16:41:45Z | 33m 37s |
| finish | 2026-07-05T16:41:45Z | - | - |

## Sm Assessment

**Story:** 162-1 — Derive-don't-cache Monster Manual. First implementation story of
epic 162 (NPC origin consolidation). Server repo, tdd workflow, p1, 3 pts.

**Readiness:** Ready for RED. The story title is a detailed behavioral spec and the
authoritative source is `docs/superpowers/specs/2026-07-05-npc-generation-inventory.md`
(Monster Manual section). The Green Room origin-precedence ADR (162-4) is already DONE
and establishes where the MM pool sits in the precedence ladder. ADR-059 is the
subsystem being reworked.

**Scope for TEA (Amos):** Write failing tests for — content-sha + session-seed keyed
pool; discard-on-mismatch replacing purge-repair; accumulation cap; fail-loud on empty
world-slug keys (No Silent Fallbacks); forensics V1–V3 (per-world seed attribution,
multi-clone writer detection, authored-NPC deletion); and a seed/purge idempotence test.
See `sprint/context/context-story-162-1.md` for the enriched pointers.

**Risks / watch-items:**
- Shared-mutable-cache concurrency across ~4 process clones — tests must exercise the
  multi-writer path, not just single-process behavior.
- OTEL: MM derive/discard/cap decisions must emit watcher events (project observability
  principle) so the GM panel can verify the fix is engaged.
- No Silent Fallbacks: empty world-slug keys must fail loud, never default to "".

**Jira:** Skipped — integration disabled for this project (no jira.project/url).

**Routing:** Phased workflow → hand off to TEA for RED phase.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** p1 architectural refactor with an explicit multi-part behavioral contract in the story title (D3+D4 of the NPC-generation inventory spec).

**Test Files:**
- `tests/game/test_monster_manual_derive.py` — model contract (16 tests): content_sha/session_seed fields, `reconcile_content` discard-on-mismatch, session-seed re-derive, full-match preservation, authored-deletion count (V3), idempotence/no-livelock, accumulation cap (npcs + encounters + authored-not-evicted), fail-loud blank world/genre on `_file_path`/`load`/`save`.
- `tests/server/test_monster_manual_derive_wiring.py` — production-seam wiring (4 tests): `ensure_loaded` skips cleanly on unresolved world (no `<genre>_.json` written), calls `reconcile_content` and emits `monster_manual.pool_discarded` on discard, no span on match, threads content_sha + session_seed.

**Tests Written:** 20 tests covering the 6 named behaviors (keying, discard-replaces-purge, cap, fail-loud keys, V1–V3 forensics via the discard span, idempotence).
**Status:** RED — 19 failing for the right reasons (pydantic `ValidationError` for missing fields, `AttributeError` for `reconcile_content`, `AssertionError` for missing `MAX_MANUAL_*` constants, `ValueError`-not-raised for fail-loud keys, spy-not-called for wiring), 1 negative-case span test passes trivially (`spans == []`) and stays meaningful in GREEN. Verified by testing-runner: no collection/import errors, `otel_capture` resolves.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------------------|---------|--------|
| #1 silent exception / silent fallback | `test_file_path_rejects_blank_world`/`_genre`, `test_load_rejects_blank_world`, `test_save_rejects_blank_world` (silent `<genre>_.json` fallback → loud `ValueError`) | failing |
| #6 test quality | all tests assert specific values (no `assert True`, no truthy-only); parametrized cases test distinct inputs | self-checked ✓ |
| OTEL Observability Principle | `test_ensure_loaded_reconciles_content_and_emits_discard_span` (V1–V3 forensic span) | failing |

**Rules checked:** #1 and #6 have direct test coverage; OTEL observability enforced via the discard-span wiring test.
**Self-check:** 0 vacuous assertions. The single RED-passing test has a real `spans == []` assertion, not a tautology.

**Dev responsibilities NOT test-gated here (Reviewer to enforce):** #3 type annotations on the new public `reconcile_content` + fields; #4 the accumulation-cap drop must be loud (WARNING/span, not a silent drop) — I asserted the *bound* but left the log message unpinned to avoid brittleness.

**Handoff:** To Dev (Naomi) for implementation.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (blocking): The `session_seed` source is unresolved in the codebase — no `session_seed`/`campaign_seed` field on `_SessionData` or the snapshot (grep came up empty; `dungeon/` has a dungeon-scoped `campaign_seed`). Dev must decide where `ensure_loaded` sources the session seed it threads into `reconcile_content` (session_slug? dungeon campaign_seed? a new field?). Affects `sidequest/server/dispatch/monster_manual_inject.py` (`ensure_loaded`). *Found by TEA during test design.*
- **Gap** (blocking): `reconcile_content` REPLACES `purge_ruleset_incoherent_encounters` + `purge_foreign_bestiary_encounters` — these two methods and their three test files (`tests/game/test_monster_manual_stale_purge.py`, `tests/game/test_monster_manual_foreign_purge.py`, `tests/server/test_monster_manual_stale_purge_wiring.py`) must be DELETED in GREEN, and the two purge-call blocks removed from `ensure_loaded` (`monster_manual_inject.py:144-205`). Leaving them is dead code (No Stubbing). Affects `sidequest/game/monster_manual.py` + `monster_manual_inject.py`. *Found by TEA during test design.*
- **Question** (non-blocking): The content_sha derivation is deliberately unpinned by the tests (spec D3 left it open: git-sha vs effective-bestiary hash; codebase precedent is `hashlib.sha256`/`blake2b` across `dungeon/`). Dev owns the choice, but per No Silent Fallbacks it must be a real non-empty value and fail loud if underivable — the wiring test asserts threading, not non-emptiness. Affects `monster_manual_inject.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `ManualNpc` needs an `authored` marker for the cap-eviction + V3 authored-deletion count. 162-2 unifies this into a typed `Origin`; 162-1 needs only the boolean now — Dev should shape it so 162-2 can absorb it without churn. Affects `sidequest/game/monster_manual.py` (`ManualNpc`, `add_npc`). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, fixed in this story): 9 chargen full-turn tests had a latent isolation dependency — they bind the synthetic `caverns_and_claudes/flickering_reach` combo (no bestiary) and only passed when stale populated manuals in the global `~/.sidequest/manuals/` made `needs_seeding()` False; they fail on a clean checkout of main. Fixed portably by the `_isolate_monster_manuals` autouse fixture. Affects `tests/conftest.py` (fixture added). *Found by Dev during implementation.*
- **Gap** (non-blocking, fixed in this story): tests that attach a dungeon session without calling `detach_dungeon_from_session` leak their expansion-quest observer in the process-global `frontier_hook._OBSERVERS`; once a later module's fixture runs `db_pool.close_pool()`, the leaked observer holds a dead pool and any subsequent region transition on that xdist worker dies with `PoolClosed("the pool 'sidequest-save' is already closed")` — the shifting-victim seam/region flake (victims move as test files change worker distribution). Fixed generically by the `_isolate_frontier_observers` snapshot/restore fixture. Affects `tests/conftest.py` (fixture added); a root-cause cleanup would make the leaking tests detach. *Found by Dev during implementation.*
- **Gap** (non-blocking, OPEN): `tests/server/dispatch/test_pregen_bestiary_90_1.py` (real end-to-end seeding of heavy_metal/evropi) flaked in 2 of 4 full-suite parallel runs during GREEN verification — once as a hard xdist worker crash (`worker 'gw10' crashed while running ...test_seed_manual_span_reports_nonzero_encounters`), once as a failure of `test_seed_manual_populates_encounters_for_wwn_world[evropi]` (mode unrecoverable). Passes in isolation and in the final two full runs; no fork/subprocess in the seeding path, so the crash mechanism is unidentified. Affects `tests/server/dispatch/test_pregen_bestiary_90_1.py` (needs a crash-mode investigation if it recurs in CI). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the RED contract exercised `add_npc(authored=True)` only directly — no production caller passed it, so the V3 forensic and cap protection were dead letters until the backfill producer was wired during GREEN. For 162-2: derive the typed `Origin` from the now-live producer seam (`_seed_authored_npcs`), and consider a wiring-style test that asserts the flag from the production path, not just the model API. Affects `sidequest/server/dispatch/pregen.py` (`_seed_authored_npcs`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `needs_seeding()` is cap-blind — a pool at MAX_MANUAL_NPCS with <4 AVAILABLE entries (normal long-campaign promotion) keeps `needs_seeding()` True forever, so EVERY session bind runs the full namegen/encountergen pipeline and the cap drops everything generated: unbounded repeated wasted work + warning spam with no convergence (reproduced live: `npcs delta = 0`, `needs_seeding still True`). The story's own bug class, relocated from storage to compute. Affects `sidequest/game/monster_manual.py` (`needs_seeding` or the `ensure_loaded` seeding gate needs cap-awareness). *Found by Reviewer during code review.*
- **Gap** (blocking): the story's core mechanism has zero real-execution coverage — `_content_sha_for` is called by no test, all three non-trivial wiring tests monkeypatch `reconcile_content` with a hand-written fake (`test_monster_manual_derive_wiring.py:106,144,176`), and the threading test asserts only `isinstance(..., str)` (`:194-195`); the `sd._room.slug` branch of `_session_seed_for` is likewise never exercised. A wrong-fields/ordering/constant-output regression in the hash would pass the entire suite. Affects `tests/server/test_monster_manual_derive_wiring.py` (add a real-deriver + real-reconcile seam test with a realistic bestiary stub, and a room-slug value assertion). *Found by Reviewer during code review.*
- **Gap** (blocking): cap drop/evict decisions emit no OTEL span (log-only) and no test pins any loudness — violates the OTEL Observability Principle ("inventory mutations — items added/removed, with source"); the sibling `pool_discarded` decision in this same diff got the span. `add_npc`/`add_encounter` return nothing, so callers have no signal to hang a span on — follow the `ContentDiscard` pure-model-returns-data/caller-emits-span pattern. Affects `sidequest/game/monster_manual.py` + `sidequest/server/dispatch/monster_manual_inject.py` + `sidequest/telemetry/spans/monster_manual.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `_content_sha_for` conflates "bestiary UNRESOLVABLE" with "bestiary empty" — both hash to the empty-roster digest, so a stamped pool reconciled during a transiently-broken content state is wholesale-discarded (authored included), where the removed purge refused to act on a None bestiary. Skip reconcile on no-evidence (mirror the pack-None gate). Affects `sidequest/server/dispatch/monster_manual_inject.py` (`_content_sha_for`/`ensure_loaded`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): `reconcile_content` absorbs a blank `content_sha` — discards a stamped pool, then re-stamps `""` so the NEXT reconcile silently adopts; `""` is the reserved never-stamped sentinel and should be rejected fail-loud, exactly as `_file_path` rejects blank slugs in this same diff. Affects `sidequest/game/monster_manual.py` (`reconcile_content`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): reconcile ADOPTS legacy over-cap pools untrimmed — spec D4 cites the 310/1,153-NPC pools as the motivation, but a legacy pool with unchanged content is grandfathered at its runaway size until a content change discards it; the caps only gate new adds. Trim-on-adopt (oldest generated first, authored preserved) closes the migration gap. Affects `sidequest/game/monster_manual.py` (`reconcile_content`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): three docstrings still describe the pre-reclassification design ("a new session ... re-derives") contradicting the implementation, its own method docstring, and a passing test — `monster_manual.py` `session_seed` field docstring, `monster_manual_inject.py` `_session_seed_for` docstring, and the `ensure_loaded` call-site comment; plus the `MonsterManual` class docstring still says "Grows over play sessions — every generated entry persists." Fix all four together. Affects `sidequest/game/monster_manual.py` + `sidequest/server/dispatch/monster_manual_inject.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): five now-inert `mock.patch.object(Path, "home", ...)` wrappers remain in `tests/server/dispatch/test_pregen.py` — dead setup since the autouse manuals isolation; misleading, cleanup in rework. Affects `tests/server/dispatch/test_pregen.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_file_path` now validates blankness but not slug shape — a world slug containing path separators reaches it (connect deliberately tolerates unknown world slugs via genre-tier fallback); writes fail loudly today, but rejecting separators alongside the blank-guard is cheap defense-in-depth. Affects `sidequest/game/monster_manual.py` (`_file_path`). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 9 findings (5 Gap, 0 Conflict, 1 Question, 3 Improvement)
**Blocking:** 3 BLOCKING items — see below

**BLOCKING:**
- **Question:** The `session_seed` source is unresolved in the codebase — no `session_seed`/`campaign_seed` field on `_SessionData` or the snapshot (grep came up empty; `dungeon/` has a dungeon-scoped `campaign_seed`). Dev must decide where `ensure_loaded` sources the session seed it threads into `reconcile_content` (session_slug? dungeon campaign_seed? a new field?). Affects `sidequest/server/dispatch/monster_manual_inject.py`.
- **Gap:** `needs_seeding()` is cap-blind — a pool at MAX_MANUAL_NPCS with <4 AVAILABLE entries (normal long-campaign promotion) keeps `needs_seeding()` True forever, so EVERY session bind runs the full namegen/encountergen pipeline and the cap drops everything generated: unbounded repeated wasted work + warning spam with no convergence (reproduced live: `npcs delta = 0`, `needs_seeding still True`). The story's own bug class, relocated from storage to compute. Affects `sidequest/game/monster_manual.py`.
- **Gap:** the story's core mechanism has zero real-execution coverage — `_content_sha_for` is called by no test, all three non-trivial wiring tests monkeypatch `reconcile_content` with a hand-written fake (`test_monster_manual_derive_wiring.py:106,144,176`), and the threading test asserts only `isinstance(..., str)` (`:194-195`); the `sd._room.slug` branch of `_session_seed_for` is likewise never exercised. A wrong-fields/ordering/constant-output regression in the hash would pass the entire suite. Affects `tests/server/test_monster_manual_derive_wiring.py`.

- **Improvement:** `ManualNpc` needs an `authored` marker for the cap-eviction + V3 authored-deletion count. 162-2 unifies this into a typed `Origin`; 162-1 needs only the boolean now — Dev should shape it so 162-2 can absorb it without churn. Affects `sidequest/game/monster_manual.py`.
- **Improvement:** the RED contract exercised `add_npc(authored=True)` only directly — no production caller passed it, so the V3 forensic and cap protection were dead letters until the backfill producer was wired during GREEN. For 162-2: derive the typed `Origin` from the now-live producer seam (`_seed_authored_npcs`), and consider a wiring-style test that asserts the flag from the production path, not just the model API. Affects `sidequest/server/dispatch/pregen.py`.
- **Gap:** `_content_sha_for` conflates "bestiary UNRESOLVABLE" with "bestiary empty" — both hash to the empty-roster digest, so a stamped pool reconciled during a transiently-broken content state is wholesale-discarded (authored included), where the removed purge refused to act on a None bestiary. Skip reconcile on no-evidence (mirror the pack-None gate). Affects `sidequest/server/dispatch/monster_manual_inject.py`.
- **Gap:** `reconcile_content` absorbs a blank `content_sha` — discards a stamped pool, then re-stamps `""` so the NEXT reconcile silently adopts; `""` is the reserved never-stamped sentinel and should be rejected fail-loud, exactly as `_file_path` rejects blank slugs in this same diff. Affects `sidequest/game/monster_manual.py`.
- **Gap:** reconcile ADOPTS legacy over-cap pools untrimmed — spec D4 cites the 310/1,153-NPC pools as the motivation, but a legacy pool with unchanged content is grandfathered at its runaway size until a content change discards it; the caps only gate new adds. Trim-on-adopt (oldest generated first, authored preserved) closes the migration gap. Affects `sidequest/game/monster_manual.py`.
- **Improvement:** `_file_path` now validates blankness but not slug shape — a world slug containing path separators reaches it (connect deliberately tolerates unknown world slugs via genre-tier fallback); writes fail loudly today, but rejecting separators alongside the blank-guard is cheap defense-in-depth. Affects `sidequest/game/monster_manual.py`.

### Downstream Effects

Cross-module impact: 9 findings across 3 modules

- **`sidequest/game`** — 5 findings
- **`sidequest/server/dispatch`** — 3 findings
- **`tests/server`** — 1 finding

### Deviation Justifications

9 deviations

- **content_sha derivation left unpinned by the wiring test**
  - Rationale: Spec D3 explicitly lists the deriver as an open option; pinning it in a test would over-constrain Dev. Discard *semantics* are fully pinned at the model layer where values are controlled.
  - Severity: minor
  - Forward impact: Reviewer must confirm the derived content_sha is real/non-empty and fails loud if underivable (No Silent Fallbacks).
- **Accumulation-cap loudness asserted as a bound, not a log message**
  - Rationale: The exact log/span shape for a routine cap-drop is a Dev decision; asserting a message string would be brittle. The *bound* and *authored-preservation* are the load-bearing invariants.
  - Severity: minor
  - Forward impact: Reviewer to confirm over-cap drops are observable (not silent) per No Silent Fallbacks.
- **V1 (per-world seed attribution) folded into the discard span, not a separate seed-time span**
  - Rationale: One forensic span at the discard decision covers multi-clone-writer detection (V2), per-world+seed attribution (V1), and authored deletion (V3) with minimal new instrumentation; the existing `pregen.seed_manual` span already carries world.
  - Severity: minor
  - Forward impact: If Reviewer wants seed-time (not just discard-time) per-world attribution, that's a follow-up on `pregen.seed_manual`.
- **session_seed reclassified: attribution-only, never a discard key**
  - Rationale: Integration evidence — per-session discard empties a valid pool on EVERY new session: 9 chargen full-turn regressions in the full suite, plus a costly production reseed each session bind. Content is the real staleness axis (multi-clone divergent checkouts); accumulation is bounded by the D4 caps, not by nuking the pool.
  - Severity: moderate
  - Forward impact: 162-2 alias/Origin work must know `session_seed` is attribution metadata, not a discard key. The `pool_discarded` span still carries it for V1 attribution.
- **content_sha deriver = sha256 of the effective bestiary roster (name:hp:level:armor_class per entry, sorted, 16-hex)**
  - Rationale: The bestiary is the axis clones actually diverge on (barsoom foreign-bleed, roster churn); a git-sha would discard on every unrelated content commit. Only identity fields are hashed — an abilities/prose-only bestiary edit does not discard.
  - Severity: minor
  - Forward impact: If deeper bestiary edits (abilities/weaknesses) must also invalidate pools, widen the per-entry hash fields.
- **Reconcile gated on pack presence (no evidence, no discard)**
  - Rationale: Without a pack the effective bestiary is unreadable — the empty-roster digest would masquerade as a content change and nuke a validly-stamped pool on a transient packless load. Mirrors the removed purges' None-bestiary conservatism.
  - Severity: minor
  - Forward impact: None expected; the live turn path always has a pack by injection time.
- **Cap eviction prefers AVAILABLE walk-ons over in-play (ACTIVE/DORMANT) ones**
  - Rationale: An ACTIVE walk-on is anchored to a location and projected into narration — naive evict-oldest could vanish an NPC mid-scene (Diamonds and Coal: engaged walk-ons are diamonds in the making).
  - Severity: minor
  - Forward impact: None for 162-2; eviction order among generated entries is otherwise insertion order.
- **`authored=True` wired at the backfill producer + legacy upsert (beyond the RED contract)**
  - Rationale: TEA's tests exercised `authored=` only via direct `add_npc` calls — no production caller passed True, so the V3 forensic would always report 0 and an authored insert at cap would be REFUSED (the exact V3 failure). Found during the hotspot review; a flag without a producer is a half-wired feature.
  - Severity: moderate
  - Forward impact: 162-2's typed `Origin` should absorb the flag from this live producer; legacy on-disk manuals self-heal on first backfill.
- **Suite-hygiene autouse fixtures added to tests/conftest.py (out of minimal-GREEN scope)**
  - Rationale: This story's correct behavior (empty pools re-derive) unmasked two pre-existing suite bugs: chargen tests passing only via `~/.sidequest` cruft, and leaked frontier observers holding dead DB pools (`PoolClosed` shifting-victim flake). Without the fixtures the full suite cannot go green on a clean machine.
  - Severity: minor
  - Forward impact: No test may rely on a pre-populated global manuals dir; tests attaching dungeon sessions no longer leak observers across tests.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **content_sha derivation left unpinned by the wiring test**
  - Spec source: story-162-1 title / spec §D3 ("key by content-version/git-sha")
  - Spec text: "content-sha + session-seed keyed pool"
  - Implementation: Wiring test spies `reconcile_content` and asserts content_sha is threaded as a string kwarg, but does NOT assert its value or pin the deriver (git-sha vs bestiary hash).
  - Rationale: Spec D3 explicitly lists the deriver as an open option; pinning it in a test would over-constrain Dev. Discard *semantics* are fully pinned at the model layer where values are controlled.
  - Severity: minor
  - Forward impact: Reviewer must confirm the derived content_sha is real/non-empty and fails loud if underivable (No Silent Fallbacks).
- **Accumulation-cap loudness asserted as a bound, not a log message**
  - Spec source: story-162-1 title / spec §D4; SOUL No Silent Fallbacks
  - Spec text: "accumulation cap ... fail loud"
  - Implementation: Tests assert `len(pool) <= MAX_MANUAL_*` and that authored NPCs are never evicted, but do NOT assert a specific WARNING/span on over-cap drop.
  - Rationale: The exact log/span shape for a routine cap-drop is a Dev decision; asserting a message string would be brittle. The *bound* and *authored-preservation* are the load-bearing invariants.
  - Severity: minor
  - Forward impact: Reviewer to confirm over-cap drops are observable (not silent) per No Silent Fallbacks.
- **V1 (per-world seed attribution) folded into the discard span, not a separate seed-time span**
  - Spec source: spec §7 V1 / story-162-1 "forensics V1-V3"
  - Spec text: "Attribute the ... seed events per-world"
  - Implementation: V1/V2/V3 are carried as attributes on the one `monster_manual.pool_discarded` span (world + session_seed + discard counts incl. authored), rather than instrumenting `pregen.seed_manual` separately.
  - Rationale: One forensic span at the discard decision covers multi-clone-writer detection (V2), per-world+seed attribution (V1), and authored deletion (V3) with minimal new instrumentation; the existing `pregen.seed_manual` span already carries world.
  - Severity: minor
  - Forward impact: If Reviewer wants seed-time (not just discard-time) per-world attribution, that's a follow-up on `pregen.seed_manual`.
### Dev (implementation)
- **session_seed reclassified: attribution-only, never a discard key**
  - Spec source: story-162-1 title / spec §D3; TEA RED contract (`test_reconcile_content_discards_on_session_seed_mismatch`)
  - Spec text: "content-sha + session-seed keyed pool ... a NEW session (new seed) re-derives from scratch"
  - Implementation: `reconcile_content` refreshes `session_seed` on every call but discards ONLY on a `content_sha` mismatch of a previously-stamped pool. The TEA model test was renamed/inverted to `test_reconcile_content_does_not_discard_on_session_seed_change_alone`.
  - Rationale: Integration evidence — per-session discard empties a valid pool on EVERY new session: 9 chargen full-turn regressions in the full suite, plus a costly production reseed each session bind. Content is the real staleness axis (multi-clone divergent checkouts); accumulation is bounded by the D4 caps, not by nuking the pool.
  - Severity: moderate
  - Forward impact: 162-2 alias/Origin work must know `session_seed` is attribution metadata, not a discard key. The `pool_discarded` span still carries it for V1 attribution.
- **content_sha deriver = sha256 of the effective bestiary roster (name:hp:level:armor_class per entry, sorted, 16-hex)**
  - Spec source: spec §D3 (deriver explicitly left open: git-sha vs content hash)
  - Spec text: "key by content-version/git-sha"
  - Implementation: `_content_sha_for` hashes the world's `effective_bestiary` — the roster the pool is seeded from. Empty/absent roster hashes to the stable empty-payload digest (never a blank key).
  - Rationale: The bestiary is the axis clones actually diverge on (barsoom foreign-bleed, roster churn); a git-sha would discard on every unrelated content commit. Only identity fields are hashed — an abilities/prose-only bestiary edit does not discard.
  - Severity: minor
  - Forward impact: If deeper bestiary edits (abilities/weaknesses) must also invalidate pools, widen the per-entry hash fields.
- **Reconcile gated on pack presence (no evidence, no discard)**
  - Spec source: spec §D3; TEA wiring tests (stub packs only)
  - Spec text: (silent on packless loads)
  - Implementation: `ensure_loaded` runs `reconcile_content` only when `sd.genre_pack` is not None; a packless load leaves the pool and stamp untouched.
  - Rationale: Without a pack the effective bestiary is unreadable — the empty-roster digest would masquerade as a content change and nuke a validly-stamped pool on a transient packless load. Mirrors the removed purges' None-bestiary conservatism.
  - Severity: minor
  - Forward impact: None expected; the live turn path always has a pack by injection time.
- **Cap eviction prefers AVAILABLE walk-ons over in-play (ACTIVE/DORMANT) ones**
  - Spec source: spec §D4/V3 (says "evict a generated walk-on", silent on which)
  - Spec text: "authored insert at cap evicts a generated walk-on rather than being refused"
  - Implementation: `_make_room_for_npc` evicts the oldest AVAILABLE generated entry; falls back to the oldest generated entry of any state only when every generated entry is in play. Test added (`test_accumulation_cap_eviction_prefers_available_over_active`).
  - Rationale: An ACTIVE walk-on is anchored to a location and projected into narration — naive evict-oldest could vanish an NPC mid-scene (Diamonds and Coal: engaged walk-ons are diamonds in the making).
  - Severity: minor
  - Forward impact: None for 162-2; eviction order among generated entries is otherwise insertion order.
- **`authored=True` wired at the backfill producer + legacy upsert (beyond the RED contract)**
  - Spec source: spec §V3; TEA Improvement finding (authored marker)
  - Spec text: "how many authored NPCs a discard dropped"
  - Implementation: `_seed_authored_npcs` passes `authored=True` on insert AND upserts the flag on an exact-name legacy entry (counted as a refresh once; idempotent thereafter). Tests added in `test_pregen_authored_placement.py`.
  - Rationale: TEA's tests exercised `authored=` only via direct `add_npc` calls — no production caller passed True, so the V3 forensic would always report 0 and an authored insert at cap would be REFUSED (the exact V3 failure). Found during the hotspot review; a flag without a producer is a half-wired feature.
  - Severity: moderate
  - Forward impact: 162-2's typed `Origin` should absorb the flag from this live producer; legacy on-disk manuals self-heal on first backfill.
- **Suite-hygiene autouse fixtures added to tests/conftest.py (out of minimal-GREEN scope)**
  - Spec source: dev minimalist discipline (no code beyond what tests demand)
  - Spec text: n/a
  - Implementation: (1) `_isolate_monster_manuals` — per-test tmp manuals dir + `pregen.seed_manual` wrapped to tolerate `EncounterSeedError` (real seeding still runs; direct-import callers and self-mocking tests are structurally unaffected, so the 90-5 fail-loud assertions still bite). (2) `_isolate_frontier_observers` — snapshot/restore of `frontier_hook._OBSERVERS` + `session_integration._ATTACHED_SAVES`. Three legacy tests converted from `Path.home()` mocks to the `_manuals_dir` convention.
  - Rationale: This story's correct behavior (empty pools re-derive) unmasked two pre-existing suite bugs: chargen tests passing only via `~/.sidequest` cruft, and leaked frontier observers holding dead DB pools (`PoolClosed` shifting-victim flake). Without the fixtures the full suite cannot go green on a clean machine.
  - Severity: minor
  - Forward impact: No test may rely on a pre-populated global manuals dir; tests attaching dungeon sessions no longer leak observers across tests.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/monster_manual.py` - content_sha/session_seed fields; `reconcile_content` (content-sha-only wholesale discard, unstamped-pool adoption, `ContentDiscard` counts); MAX_MANUAL_NPCS=200 / MAX_MANUAL_ENCOUNTERS=100 with loud drops; `authored` flag on ManualNpc; cap eviction prefers AVAILABLE walk-ons; `_file_path`/`save` fail loud on blank genre/world; both `purge_*` methods and their 2 module helpers removed
- `sidequest/server/dispatch/monster_manual_inject.py` - early return on unresolved world; `_content_sha_for` (sha256 of effective-bestiary roster) + `_session_seed_for` (SessionRoom slug, world fallback); reconcile gated on pack presence; `pool_discarded` warning + OTEL span; both purge blocks removed
- `sidequest/server/dispatch/pregen.py` - `_seed_authored_npcs` passes `authored=True` on insert and upserts the flag on legacy entries (idempotent)
- `sidequest/telemetry/spans/monster_manual.py` - `SPAN_MONSTER_MANUAL_POOL_DISCARDED` replaces STALE_PURGED + FOREIGN_PURGED
- `tests/conftest.py` - autouse `_isolate_monster_manuals` (per-test manuals dir + tolerant seed) and `_isolate_frontier_observers` (registry snapshot/restore) fixtures
- `tests/game/test_monster_manual_derive.py` - session-seed test inverted to the content-only contract; fixed-width cap names; eviction-preference test added
- `tests/server/dispatch/test_pregen_authored_placement.py` - authored-flag insert + legacy-upsert tests added
- `tests/game/test_monster_manual.py`, `tests/server/dispatch/test_pregen.py` - 3 tests converted from `Path.home()` mocks to the `_manuals_dir` convention
- `tests/server/conftest.py` - stale purge-era comment updated
- Deleted: `tests/game/test_monster_manual_stale_purge.py`, `tests/game/test_monster_manual_foreign_purge.py`, `tests/server/test_monster_manual_stale_purge_wiring.py`, the 4 foreign-purge tests + 3 helpers in `tests/server/dispatch/test_monster_manual_inject.py`

**Tests:** Full suite 14509 passed / 0 failed / 341 skipped (102.9s, parallel). Targeted MM/pregen/seam surface 155/155. TEA's 20 RED tests GREEN (1 renamed/inverted per the session_seed deviation — see Design Deviations). ruff + pyright clean on all changed source (pyright noise in tests/conftest.py is pre-existing PG-fixture typing).
**Branch:** feat/162-1-derive-dont-cache-monster-manual (pushed, af03e9b6 on top of RED d7e4d7c9)

**Handoff:** To Reviewer (Chrisjen). Hotspot notes for review focus: `reconcile_content` discard semantics (content-only; session_seed attribution), the pack-None reconcile gate, cap-eviction ordering, and the authored-flag producer wiring in `_seed_authored_npcs`.
### Reviewer (audit)

Stamps for every deviation above, in order:

**TEA entries:**
- **content_sha derivation left unpinned by the wiring test** → ✓ ACCEPTED by Reviewer: legitimate scope choice at RED time — but the review found its shadow: NO test anywhere executes the real `_content_sha_for` (wiring tests fake `reconcile_content` at lines 106/144; model tests hand-pick shas). The rework must add a real-deriver + real-reconcile seam test ([TEST] finding #1).
- **Accumulation-cap loudness asserted as a bound, not a log message** → ✗ FLAGGED by Reviewer: the entry itself deferred loudness enforcement to review ("Reviewer to enforce") — enforcing now. Cap drop/evict decisions are log-only with no OTEL span and no test pins ANY loudness (log or span). Violates the CLAUDE.md OTEL Observability Principle ("inventory mutations — items added/removed, with source"); the sibling decision in this same diff (`pool_discarded`) got the span treatment. Finding [RULE]/[TEST], rework required.
- **V1 (per-world seed attribution) folded into the discard span** → ✓ ACCEPTED by Reviewer: one forensic span at the discard decision carries world + session_seed + counts; consistent with spec §7 forensics and the existing `pregen.seed_manual` span already carries per-world attribution at seed time.

**Dev entries:**
- **session_seed reclassified: attribution-only, never a discard key** → ✓ ACCEPTED by Reviewer: spec §D3's own text keys staleness by "content-version/git-sha (stale = discard, never repair)" — session-seed-as-discard-key was a RED-contract interpretation, not spec text. The integration evidence (9 chargen regressions + per-session reseed cost) is decisive; the inverted test pins a real contract. Surfaced prominently in the Reviewer Assessment for Keith's sign-off at merge, per [TEST] finding #4's process point. CAVEAT the docs must match: three docstrings still claim session-mismatch discards ([DOC] findings, rework).
- **content_sha deriver = sha256 of the effective bestiary roster** → ✗ FLAGGED by Reviewer: the deriver conflates "bestiary UNRESOLVABLE" (no evidence) with "bestiary empty" (real state) — both hash to the empty-roster digest, so a stamped pool seen during a transiently-broken content state is wholesale-discarded (NPCs and authored included), where the removed purge explicitly refused to act on a None bestiary (87-4 conservatism). Mitigated by reseed+backfill recovery, but the discard-on-no-evidence is a conservatism regression ([TEST] finding #5). Rework: skip reconcile when the bestiary is unresolvable (mirror the pack-None gate), keep the stable digest for a genuinely empty roster.
- **Reconcile gated on pack presence (no evidence, no discard)** → ✓ ACCEPTED by Reviewer: correct conservatism, and the exact pattern the flagged deriver case above should extend to the None-bestiary state.
- **Cap eviction prefers AVAILABLE walk-ons over in-play ones** → ✓ ACCEPTED by Reviewer: sound Diamonds-and-Coal rationale; pinned by a behavioral test asserting survivor/evictee identities, not implementation shape.
- **`authored=True` wired at the backfill producer + legacy upsert** → ✓ ACCEPTED by Reviewer: fixed a dead-letter flag (V3 forensic and cap protection had zero production producers); insert + legacy-upsert + idempotence all test-pinned.
- **Suite-hygiene autouse fixtures** → ✓ ACCEPTED by Reviewer: the can't-mask argument for the tolerant seed wrapper is verified (fail-loud unit tests bind `seed_manual` via module-scope direct import; the re-raise wiring test installs its own raising fake); the frontier-observer leak is test-only (production detaches at `websocket_session_handler.py:567-570`). Residual risk documented, not flagged: the tolerance is suite-wide, so incidental integration coverage of production `EncounterSeedError` regressions is thinner ([TEST] finding #6) — the canonical guards (direct-import unit tests + re-raise wiring test) remain intact.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | No | error — no response after status ping (spawned first, never reported) | none | Domain self-assessed per gate rule 4 with direct evidence: full suite 14509 passed / 0 failed / 341 skipped (own captured run, exit 0); ruff clean on every changed file (3 pre-existing E402 in untouched `tests/dungeon/conftest.py` — develop baseline); diff smell-scan clean (no TODO/FIXME/debugger/print/.only added) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4 (#1 no-real-deriver coverage, #2 session-seed branch/type-only assert, #3 cap loudness untested, #5 no-evidence discard), addressed-via-deviation-audit 1 (#4 session_seed sign-off — stamped ACCEPTED with spec citation, surfaced in assessment), deferred 1 (#6 tolerance blast radius — disclosed residual, canonical fail-loud guards verified intact) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 4 (#1-3 session-seed docstring contradiction ×3 as one class, #4 forever-cache class docstring), deferred 1 (#5 historical plan-doc anchor — completed plan doc, out of diff scope) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (own-domain pass done: slug-shape traversal noted [LOW], single-user deployment, writes fail loudly today) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 + 6 wiring PASSes | confirmed 4 (#1 cap-blind needs_seeding HIGH w/ live repro, #2 cap decisions span-less, #3 blank-sha absorption, #4 inert home-mocks); all 6 wiring/dead-code checks PASS with evidence |

**All received:** Yes (3 of 4 spawned returned with findings; preflight errored and its mechanical domain is self-assessed with direct evidence per rule 4; 5 subagents disabled via settings)
**Total findings:** 12 raw → 9 deduped confirmed, 2 dismissed/deferred (with rationale), 1 addressed via deviation audit

### Rule Compliance

Python lang-review checklist (13 checks) applied to every changed `.py` file — full enumeration by rule-checker, cross-checked by me:
- #1 silent exceptions: PASS — sole new try/except (`_tolerant_seed_manual`, tests/conftest.py) catches the specific `EncounterSeedError`, warns with context; test-only. The blank-sha absorption in `reconcile_content` is flagged as the No-Silent-Fallbacks-adjacent gap ([RULE] finding 5), not an except-block violation.
- #2 mutable defaults: PASS — `authored: bool = False`, `ContentDiscard` scalars; enumerated all new signatures.
- #3 annotations: PASS — `reconcile_content`, `_make_room_for_npc`, `_content_sha_for`, `_session_seed_for`, both fixtures all fully annotated; the one `Any` carries the required explanatory comment.
- #4 logging: PASS — all new warnings lazy `%`-style, severity consistent with file conventions, no sensitive data.
- #5 path handling: PASS on pathlib/encoding; slug-shape guard gap noted [LOW].
- #6 test quality: FAIL — type-only assertion `isinstance(captured["session_seed"], str)` (wiring test :194-195) and cap tests assert bound only, never loudness (findings 2, 3).
- #7 resources / #8 deserialization / #9 async / #12 dependencies: PASS or N/A — nothing introduced.
- #10 imports: PASS — TYPE_CHECKING Bestiary import removed with its consumers; hashlib/dataclass used.
- #11 boundary validation: PASS on the new blank-key guards (the story's point); `reconcile_content` blank-sha boundary flagged (finding 5).
- #13 fix-regressions: hotspot fixes re-scanned — the pack-None gate judged acceptable conservatism (mirrors removed purges' None-bestiary posture), the unresolvable-bestiary sibling case flagged (finding 4).
- CLAUDE.md No Stubbing / dead code: PASS — zero live references to removed purge machinery (repo-wide grep; the derive-test docstring names them as history, intentional).
- CLAUDE.md Verify Wiring: PASS for production callers (`reconcile_content` ← `ensure_loaded` ← `websocket_session_handler.py:837`; `authored=True` ← `pregen.py:311`; span ← `monster_manual_inject.py:216-227`); FAIL for test-side wiring of the deriver (finding 2).
- CLAUDE.md OTEL Observability Principle: FAIL for cap decisions (finding 3); PASS for discard (`pool_discarded` span, asserted via otel_capture).
- Tenant isolation audit: N/A — single-user personal game server, no tenant-scoped types in the diff; nearest analogue (world-scoped cache keys) is the story's own fail-loud work, verified.

### Devil's Advocate

Assume this diff is broken. Where does it bleed? First, the multi-clone thrash: two clones with divergent checkouts binding the same world now alternate wholesale discards — every bind nukes the other's pool and reseeds. I tried to make this a finding and failed: each session gets a pool correct for ITS content, the discard is loud (span + warning with session_seed attribution — the V2 forensic), and the spec's own words are "stale = discard, never repair." The thrash is bounded reseed cost, not corruption. Second, version skew: `extra="forbid"` on the pydantic models means a manual written by a NEWER clone (extra field) fails load on an older one → `load_failed` → empty manual → rederive → save strips the field — degradation is loud and self-healing, but note the newer clone then silently loses its extra field's data; 162-2's Origin field addition will hit exactly this on mixed-version clones — worth a migration note there. Third, mid-campaign content pull: a bestiary edit discards the pool including ACTIVE walk-on anchors and faction origin-stamps; promoted NPCs persist in `snapshot.npcs` (the durable record), so the loss is pool-state — acceptable, V3-visible. Fourth, what would a stressed machine do? The reseed storm (finding 1) is the answer I could NOT argue away: at cap, every bind pays full namegen/encountergen for zero gain, forever — on the Mac mini running four clones plus MLX, that is real thermal/latency money, and it lands precisely on the most-played worlds. Fifth, the epic's spec issue #6 (broad `except Exception` still swallows non-EncounterSeedError seed failures into a log line) survives untouched in this diff — out of 162-1's scope but the DA notes the empty-pool-with-a-log-line shape remains reachable via that path until its sibling story lands. Sixth, the confused-user angle: a homebrew author (Jade) editing bestiary.yaml sees her pool rebuild — correct, but nothing tells her WHY her manual reset; the pool_discarded span serves the dev, and that is the right audience for now.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [RULE] | Cap-blind `needs_seeding()` → per-session-bind reseed storm at cap (live repro: `npcs delta = 0`, `needs_seeding` stays True) | `sidequest/game/monster_manual.py:397` + `monster_manual_inject.py:230` | Cap-aware seeding gate (e.g. NPC-side seeding condition includes `len(npcs) < MAX_MANUAL_NPCS`); RED test |
| [HIGH] [TEST] | Story's core mechanism never executed by tests: `_content_sha_for` uncovered, wiring tests fake `reconcile_content`, threading test asserts `isinstance` only, `_room.slug` branch unexercised | `tests/server/test_monster_manual_derive_wiring.py:106,144,176,194-195` | Real-deriver + real-reconcile seam test (realistic bestiary stub; sha changes on roster change, stable otherwise; real discard+persist); room-slug value assertion |
| [HIGH→MEDIUM-HIGH] [RULE][TEST] | Cap drop/evict decisions log-only — no OTEL span, no loudness test; violates OTEL Observability Principle (rule-matching, not dismissable) | `monster_manual.py` `_make_room_for_npc` + `add_encounter` | Pure-model-returns-event / caller-emits-span (the `ContentDiscard` pattern); span constant + wiring test |
| [MEDIUM] [EDGE] | No-evidence discard: unresolvable bestiary hashes to empty-roster digest → wholesale discard of a stamped pool on transiently-broken content | `monster_manual_inject.py:113-138` | Skip reconcile when bestiary is unresolvable (mirror pack-None gate); keep stable digest for genuinely-empty roster; test |
| [MEDIUM] [SILENT] | `reconcile_content` absorbs blank `content_sha`: discards then re-stamps `""` → next reconcile silently adopts | `monster_manual.py` `reconcile_content` | Fail-loud ValueError on blank sha (mirror `_file_path` guards); test |
| [MEDIUM] [EDGE] | Legacy over-cap pools (the spec-cited 310/1,153) adopted untrimmed — caps gate only new adds | `monster_manual.py` `reconcile_content` | Trim-on-adopt: oldest generated first, authored preserved; test |
| [MEDIUM] [DOC] | Session-seed-discard misconception ×3 docstrings + forever-cache class docstring — contradicts impl + passing test; will misdirect 162-2 | `monster_manual.py:176-178,205-211`; `monster_manual_inject.py:141-145,190-193` | Rewrite all four in one pass to the content-only contract |
| [LOW] [SIMPLE] | Five inert `Path.home` mocks left in sibling tests | `tests/server/dispatch/test_pregen.py` | Remove dead setup |
| [LOW] [SEC] | `_file_path` slug-shape: path separators in a world slug reach the key builder (connect tolerates unknown slugs by design) | `monster_manual.py` `_file_path` | Reject separators alongside blank-guard; test |

No findings from the [TYPE] domain (annotations/invariants clean — `ContentDiscard` frozen dataclass, full annotations). [EDGE]/[SILENT]/[SEC]/[SIMPLE] tags above are my own-domain observations; those specialist subagents were disabled via settings.

**Data flow traced:** client connect (world slug, deliberately tolerant of unknown slugs) → `websocket_session_handler.py:837` `ensure_loaded(sd)` → fail-loud blank-key `MonsterManual.load` (early-return None pre-world-resolution — the `<genre>_.json` bug is dead) → pack-gated `reconcile_content` (content-sha-only discard; adopt unstamped) → discard path saves + emits `pool_discarded` span → `needs_seeding` → `seed_manual` (fail-loud 90-5 preserved) → authored backfill (`authored=True` now wired) → per-turn `inject` into `snapshot.npcs`. Safe except the two HIGH gaps above.

**Pattern observed (good):** pure-model-returns-data / caller-emits-span (`ContentDiscard` → `SPAN_MONSTER_MANUAL_POOL_DISCARDED`, `monster_manual_inject.py:205-227`) — the correct OTEL seam pattern; the cap path must adopt it.

**Error handling:** blank keys raise `ValueError` pre-write (`monster_manual.py` `_file_path`/`save` — verified by 4 tests); corrupt manual load degrades loudly to empty + rederive; save mkdir failure warns and skips (ADR-006, pre-existing).

**Verified good (evidence):**
- [VERIFIED] `reconcile_content` production wiring — `monster_manual_inject.py:205` called from `ensure_loaded`, reached from `websocket_session_handler.py:837`; complies with Verify Wiring rule.
- [VERIFIED] `authored=True` producer — `pregen.py:311` in `_seed_authored_npcs` + legacy upsert with idempotence test; complies with Verify Wiring rule.
- [VERIFIED] zero dead purge references — repo-wide grep of both symbol families and both span constants: no live hits; complies with No Stubbing.
- [VERIFIED] tolerant-seed fixture cannot mask 90-5 fail-loud — `test_pregen_fail_loud_90_5.py:46` binds `seed_manual` by module-scope direct import (patch-invisible); re-raise wiring test installs its own raising fake (`test_monster_manual_inject.py:210`); complies with No Silent Fallbacks at the production seam (raise preserved in `ensure_loaded`).
- [VERIFIED] frontier-observer fixture masks no production leak — production detaches at `websocket_session_handler.py:567-570`; leak is test-only.
- [VERIFIED] `_session_seed_for` reads a real field — `_SessionData._room: SessionRoom | None` (`session_state.py:208`), Optional by design for pre-slug-connect paths.

**Session-seed reclassification — flag for Keith at merge:** the shipped contract is derive-per-CONTENT-version, not per-session; spec §D3's own text supports it ("key by content-version/git-sha; stale = discard, never repair") and the per-session variant demonstrably empties valid pools every bind — but the story title says "derive-don't-cache" and TEA's original RED contract read it as per-session, so the human owner should see this explicitly. Deviation stamped ACCEPTED in the audit with this caveat.

**Handoff:** Back to TEA (Amos) — findings are testable behaviors (red rework): cap-aware seeding gate, cap-event span, blank-sha fail-loud, no-evidence skip, trim-on-adopt, real-deriver seam coverage, room-slug value assertion. Doc rewrites + mock cleanup + slug-shape guard ride the same round on the Dev side.
## Dev Assessment — Rework Round (post-review)

**Implementation Complete:** Yes — all 9 review findings addressed, RED-first.

**Blocking findings fixed:**
- **Cap-blind reseed storm** — `needs_seeding()` is now cap-aware per side (`npcs_starved and len < MAX`, same for encounters): a saturated pool no longer triggers a futile full seed on every session bind. Tests: `test_needs_seeding_false_at_npc_cap_with_no_available`, `..._at_encounter_cap...`, plus the below-cap guard-the-guard case.
- **Real-execution coverage** — `tests/server/test_monster_manual_derive_wiring.py` rewritten: realistic bestiary-bearing pack stubs, the REAL `_content_sha_for` (stability under roster reorder, change on edit, empty-vs-unresolvable distinction) and the REAL `reconcile_content` through `ensure_loaded`, including the persisted discard cycle re-loaded from disk and idempotence. `session_seed` room-slug branch asserted BY VALUE (`sunday-table-42`) plus the world-slug fallback.
- **Cap decisions GM-panel visible** — new `monster_manual.cap_enforced` span (constant + FLAT_ONLY registered). `add_npc`/`add_encounter` now return a `CapEvent` (`npc_dropped` / `npc_evicted` / `npc_dropped_all_authored` / `encounter_dropped`) — pure-model-returns-data / caller-emits-span, exactly the `ContentDiscard` pattern; `pregen._note_cap_event` emits at all four insert sites. Wiring tests: seed-path drop span (`test_pregen.py`) + authored-eviction span (`test_pregen_authored_placement.py`).

**Non-blocking findings fixed:**
- **No-evidence discard** — `_content_sha_for` returns `None` when the bestiary is UNRESOLVABLE (no pack / no accessor / None bestiary); `ensure_loaded` skips reconcile entirely on None (debug log), subsuming the old pack-None gate. An empty-but-present roster keeps its stable digest — the two states are never conflated. Test: stamped pool + unresolvable bestiary → pool and stamp untouched, no span.
- **Blank content_sha** — `reconcile_content` raises `ValueError` on blank (the `""` never-stamped sentinel can't be smuggled as a content version); pool untouched by the refused call. Parametrized tests.
- **Legacy over-cap adoption** — new `trim_to_caps()` (oldest generated first, authored NEVER dropped, oldest encounters beyond cap); `ensure_loaded` calls it after reconcile, persists, and emits `cap_enforced` kind="trim" with counts. Model tests + wiring test (220-NPC legacy pool → 200 on disk, span with npcs_trimmed=20).
- **Docstring contradictions ×4** — `session_seed` field, `_session_seed_for`, the `ensure_loaded` call-site comment, and the `MonsterManual` class docstring all rewritten to the content-only contract (attribution-only session_seed; derived pool, not forever-cache).
- **Inert `Path.home` mocks** — all six `with mock.patch.object(Path, "home", ...)` wrappers in `test_pregen.py` removed (bodies de-indented, explanatory comment left), `mock` import dropped.
- **Slug-shape guard** — `_file_path` rejects `/`, `\`, and `..` in either slug (loud ValueError); parametrized tests.

**Tests:** rework surface 158/158 green (derive model + MM legacy + wiring + pregen + authored placement + inject + fail-loud-90-5); ruff + pyright clean on all changed files; full suite run in flight at handoff-write time — result recorded below before exit.

### Design Deviations addendum

### Dev (rework)
- **Trim seam is `trim_to_caps()` called from `ensure_loaded`, not inside `reconcile_content`**
  - Spec source: Reviewer finding ("Trim-on-adopt ... Affects `reconcile_content`")
  - Spec text: "Trim-on-adopt (oldest generated first, authored preserved)"
  - Implementation: a separate public `MonsterManual.trim_to_caps() -> PoolTrim | None`, invoked by `ensure_loaded` immediately after `reconcile_content`, which persists and emits the span.
  - Rationale: keeps the model pure and the OTEL seam consistent (pure-model-returns-data / caller-emits-span, identical to `ContentDiscard`); `ensure_loaded` is the only production reconcile caller, so adopt-time trimming is preserved in behavior.
  - Severity: minor
  - Forward impact: any future non-`ensure_loaded` reconcile caller must also call `trim_to_caps` (documented in both docstrings).
- **Reconcile-skip on unresolvable bestiary logs at DEBUG, no span**
  - Spec source: Reviewer finding (no-evidence skip); OTEL Observability Principle
  - Spec text: "skip reconcile when the bestiary is unresolvable (mirror the pack-None gate)"
  - Implementation: `logger.debug("monster_manual.reconcile_skipped_no_bestiary ...")`, no OTEL span.
  - Rationale: for packs with no bestiary at all this fires on EVERY session bind as a static condition — a per-bind span would be steady-state noise, not a decision signal; the debug line keeps it forensically reachable.
  - Severity: minor
  - Forward impact: if a bestiary-less pack ever needs a content axis (e.g. Fate packs keying on something else), this seam is where it lands.

**Final verification (rework):** Full suite on the settled tree: **14,529 passed / 0 failed / 341 skipped** (102.6s, exit 0). ruff + pyright clean on all changed files; repo-wide `ruff format --check` drift (45 files) verified as pre-existing develop baseline with ZERO overlap with this branch's changed files.

**Preflight resolution note:** the review-phase `reviewer-preflight` subagent reported 40 minutes late claiming 107 failures across unrelated subsystems. Root-caused as an artifact: its ~101s suite run raced the rework's live working-tree edits (RED tests without implementations mid-write). The same suite on the settled tree passes 14,529/0. Its clean smell/lint findings match my own; its failure claim is disregarded with this evidence.

**Branch:** feat/162-1-derive-dont-cache-monster-manual (pushed, dc214a44 on top of af03e9b6 + RED d7e4d7c9)
**Handoff:** Back to Reviewer (Chrisjen) for re-review of the rework round.
## Re-Review (rework round) — Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight (round 2) | No | still running at operator approval | none | Domain covered by direct evidence: settled-tree full suite 14,529 passed / 0 failed / 341 skipped (exit 0, run window verified against a stable tree at dc214a44); ruff + pyright clean on changed files; format drift (45 files) verified pre-existing with zero overlap with the branch. Round-1 preflight's 107-failure report was root-caused as an artifact of racing live working-tree edits. |
| 2-3, 6-8 | edge-hunter / silent-failure / type-design / security / simplifier | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer (round 2) | Yes | findings | 4 | confirmed 4: trim gated on content evidence (real bug, repro'd: 220-NPC pool unbounded under no-bestiary pack); npc_dropped_all_authored kind untested; encounter-side trim untested; encounter_dropped never driven through seed_manual. Also verified all 3 prior test findings genuinely fixed, with mutation-testing evidence (deleted save() calls → tests caught both). |
| 5 | reviewer-comment-analyzer (round 2) | Yes | findings | 4 | confirmed 4: 3 leftover session-discard claims (derive-file module docstring, pool_discarded span comment, ContentDiscard docstring) + class docstring "bounded on reconcile" overstates (reconcile_content never calls trim_to_caps). New docstrings + all 6 mock-removal comments verified accurate. |
| 9 | reviewer-rule-checker (round 2) | Yes | findings | 3 | confirmed 3: trim-gating (corroborates test-analyzer), zero-trim WARNING re-logged every load in the authored-over-cap state, stale session_fixture comment in tests/server/conftest.py (the (None,"") pin now means unresolvable → reconcile+trim skipped for ~20 shared-fixture tests). All 5 prior-blocker verify items PASS with reproductions; CapEvent caller enumeration exhaustive (4/4 sites wired). |

**All received:** Yes (3 of 4 returned; preflight2 domain covered by direct settled-tree evidence per rule 4)
**Total findings:** 11 raw → 9 deduped confirmed (1 code defect + 3 coverage gaps + 5 doc corrections), 0 dismissed

### Design Deviations — Reviewer audit addendum (rework round)

- **Trim seam is `trim_to_caps()` called from `ensure_loaded`, not inside `reconcile_content`** → ✓ ACCEPTED by Reviewer (pattern) with a materialized cost: placing the call inside the `content_sha is not None` branch gated a pure size-bound operation on content evidence — the confirmed defect below. The pattern stands; the placement needs the follow-up fix.
- **Reconcile-skip on unresolvable bestiary logs at DEBUG, no span** → ✓ ACCEPTED by Reviewer: proportionate for a static per-world condition; forensically reachable.

## Reviewer Assessment — Re-Review (rework round)

**Verdict:** APPROVED — operator decision (Keith, 2026-07-05: "stop and approve here"), and defensible on the merits: zero Critical/High against live production. All 9 prior findings verified resolved (with reproductions and mutation-testing evidence). The one confirmed code defect found this round is masked in production today — rule-checker2 verified all 11 live packs bind ruleset-modules with REQUIRED bestiaries, so the trim path is live for every real world; the gap only opens for a hypothetical bestiary-less pack.

**Outstanding items — logged below as non-blocking Delivery Findings for a follow-up story:**
1. (code) `trim_to_caps()` runs only inside `ensure_loaded`'s `content_sha is not None` branch — a pure size-bound op gated on content evidence; a bestiary-less world's legacy over-cap pool is never trimmed (repro'd: 220 NPCs stay 220). Move the trim outside the gate + regression test.
2. (code, trivial) zero-trim WARNING re-logs every load when authored alone exceed the cap — guard on actual counts.
3. (tests) 3 coverage gaps: `npc_dropped_all_authored`, encounter-side trim, `encounter_dropped` through `seed_manual`.
4. (docs) 5 corrections: 3 leftover session-discard claims (derive module docstring, span comment, ContentDiscard), class-docstring "bounded on reconcile" wording, stale `session_fixture` comment in tests/server/conftest.py.

**Verified this round:** cap-aware `needs_seeding` both sides (repro'd both directions) · CapEvent contract wired at all 4 production insert sites (exhaustive grep) · None-sha structurally cannot reach `reconcile_content` · real-deriver + real-reconcile end-to-end coverage incl. persist-reread (mutation-tested) · room-slug session_seed by value · slug guard validated against all real content world slugs · full suite 14,529/0/341 on the settled tree.

**Handoff:** To SM (Camina Drummer) for finish (PR + merge) — on operator's go.

### Delivery Findings addendum

### Reviewer (re-review)
- **Gap** (non-blocking): `trim_to_caps()` is gated on content evidence — runs only in `ensure_loaded`'s `content_sha is not None` branch, so a bestiary-less world's legacy over-cap pool is never bounded (repro: 220-NPC pool unchanged under a no-bestiary pack; masked today — all 11 live packs have required bestiaries). Affects `sidequest/server/dispatch/monster_manual_inject.py` (move trim outside the sha gate + regression test). *Found by Reviewer during re-review.*
- **Gap** (non-blocking): `trim_to_caps` logs "dropped 0 oldest generated NPCs" on every load when authored entries alone exceed the cap — log guard checks the over-cap condition, not the trim count. Affects `sidequest/game/monster_manual.py` (guard the warning on npcs_trimmed > 0). *Found by Reviewer during re-review.*
- **Gap** (non-blocking): coverage gaps — `CapEvent(kind="npc_dropped_all_authored")` untested; `trim_to_caps` encounter-side untested; `encounter_dropped` never driven through `seed_manual`. Affects `tests/game/test_monster_manual_derive.py` + `tests/server/dispatch/test_pregen.py`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): 5 doc corrections — session-discard claims persist in `tests/game/test_monster_manual_derive.py` module docstring, the `pool_discarded` span comment, and the `ContentDiscard` docstring; `MonsterManual` class docstring says "bounded on reconcile" (trim is an `ensure_loaded` step, not part of `reconcile_content`); `tests/server/conftest.py` `session_fixture` comment still describes the pre-rework `(None,"")` → stable-digest behavior (now means unresolvable → reconcile skipped). Affects those five files. *Found by Reviewer during re-review.*