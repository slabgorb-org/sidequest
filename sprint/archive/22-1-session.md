---
story_id: "22-1"
jira_key: ""
epic: "22"
workflow: "tdd"
---
# Story 22-1: Seed trope schema + deck engine — lifespan, flavor tags, draw-without-replacement, ghost retention

## Story Details
- **ID:** 22-1
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p1

## Acceptance Criteria

From Epic 22 description: Expand the trope engine with short-arc 'seed' tropes — deliberately vague narrative events randomly dealt each session from a per-genre deck. Seeds inject as background context; the LLM narrator retroactively connects them to macro-trope escalations, creating emergent foreshadowing. Expired seeds linger as ghosts for cross-session callbacks.

**AC1: SeedTrope schema**
- New Pydantic model `SeedTrope` parallel to `TropeDefinition` in `sidequest/genre/models/tropes.py`
- Fields: `id`, `name`, `description`, `flavor_tags` (list[str]), `lifespan_turns` (int), `delivery_hints` (list[str]), `narrative_hint` (str)
- Lives in `sidequest/genre/models/tropes.py` alongside TropeDefinition

**AC2: Deck engine**
- New class `SeedDeck` in `sidequest/game/` (new module or extend existing trope module)
- Constructor takes `genre_id`, `world_id`, loads seeds from YAML via genre loader
- Method `draw() -> SeedTrope | None` — removes seed from deck (without-replacement); returns None when deck exhausted
- Deck state is keyed per (genre, world, session_id) — survives save/reload via ADR-023 JSON column

**AC3: Ghost retention**
- New `SeedGhost` model: `id`, `name`, `expired_at_turn`, `delivery_hints`
- Field on `GameSnapshot`: `seed_ghosts: list[SeedGhost]`; expires seeds migrate here when lifespan elapses
- `SeedGhost` is immutable — record-only, no resolution mechanics in this story (22-3)

**AC4: Active seed tracking**
- Field on `GameSnapshot`: `active_seeds: list[SeedState]`
- `SeedState` model: `id`, `name`, `activated_at_turn`, `flavor_tags`, `lifespan_turns`, `delivery_hints`
- SeedState is round-trippable JSON (no side effects on load)

**AC5: Persist via ADR-023**
- Deck state, active_seeds, and seed_ghosts all persist in `game_state.snapshot_json` (existing column)
- No schema migration required; round-trip JSON serialization
- Seed deck re-instantiates on session load: verify seeds already drawn don't return to deck

## Technical Approach

**Phase 1: Schema (Red)**
- Add `SeedTrope`, `SeedState`, `SeedGhost` models to `sidequest/genre/models/tropes.py`
- Verify Pydantic serialization round-trips correctly
- Test fixtures: minimal seed YAML fixtures for testing (caverns_and_claudes or tea_and_murder)

**Phase 2: Deck Engine (Green)**
- Create `sidequest/game/seed_deck.py` with `SeedDeck` class
- Load seeds from genre pack YAML (location: `genre_packs/{genre}/worlds/{world}/seeds.yaml` or per-genre `tropes.yaml` with `seed_tropes:` section)
- Deck state: `drawn_ids: set[str]` (tracks already-drawn seeds per session)
- `draw()` method uses Python's `random.Random` seeded by `session_id` for reproducibility
- Unit tests: draw order, without-replacement contract, deck exhaustion

**Phase 3: Ghost Lifecycle (Green → Refactor)**
- Add `active_seeds` and `seed_ghosts` fields to `GameSnapshot`
- Test: load saved state with seeds, verify they persist
- Test: serialization round-trip (JSON dump → load)

**Phase 4: Integration (Yellow/Red)**
- Wiring story 22-2 (narrator injection): will consume SeedDeck + active_seeds
- Wiring story 22-3 (narrator context): will reference active_seeds and seed_ghosts in narrator prompt

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-21T13:23:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-21 | 2026-05-21T12:32:15Z | 12h 32m |
| red | 2026-05-21T12:32:15Z | 2026-05-21T12:44:35Z | 12m 20s |
| green | 2026-05-21T12:44:35Z | 2026-05-21T12:55:40Z | 11m 5s |
| spec-check | 2026-05-21T12:55:40Z | 2026-05-21T12:59:45Z | 4m 5s |
| verify | 2026-05-21T12:59:45Z | 2026-05-21T13:13:50Z | 14m 5s |
| review | 2026-05-21T13:13:50Z | 2026-05-21T13:23:51Z | 10m 1s |
| finish | 2026-05-21T13:23:51Z | - | - |

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with two endorsed deviations)
**Mismatches Found:** 2 (both Minor, both pre-logged by TEA/Dev — I endorse both)

Reviewed all 5 ACs against the committed code (`SeedTrope` in `genre/models/tropes.py`, `SeedState`/`SeedGhost` + `GameSnapshot.active_seeds`/`seed_ghosts` in `game/session.py`, `SeedDeck` in `game/seed_deck.py`). AC1/AC3/AC4 are exactly aligned. Verified AC5 persistence empirically: `SqliteStore.save()` serializes the whole snapshot via `model_dump_json()`, so the two new list fields round-trip with **no migration** — confirmed. Confirmed no production consumers exist outside the three new modules (the engine ships intentionally unwired; wiring is 22-2/22-3).

- **Deck constructor takes injected `seeds`, not a YAML-loading constructor** (Different behavior — Architectural, Minor)
  - Spec: AC2 "Constructor takes `genre_id`, `world_id`, loads seeds from YAML via genre loader"
  - Code: `SeedDeck(genre_id, world_id, session_id, seeds, drawn_ids=None)` — caller injects the seed list; the deck never touches YAML.
  - Recommendation: **A — Update spec.** Dependency injection is the correct call: it keeps the engine pure/testable and honors the no-content-coupled-tests rule. "Loads from YAML via genre loader" is rightly the *caller's* responsibility, deferred to the 22-2/22-3 wiring. Spec wording should bless the injected-seeds contract.

- **`drawn_ids` derived from `active_seeds ∪ seed_ghosts`, not a dedicated persisted deck-state field** (Different behavior — Architectural, Minor)
  - Spec: AC5 "Deck state, active_seeds, and seed_ghosts all persist in `snapshot_json`"
  - Code: no separate `seed_deck`/`drawn_ids` column; the reload test reconstructs the drawn set as the union of the two persisted lists.
  - Recommendation: **A — Update spec.** This is *better* than a dedicated field: every drawn seed is by construction either currently active or already a ghost, so the union is a complete, non-lossy record of "what's been drawn." A separate `drawn_ids` field would be denormalized state that can drift. Single source of truth wins. AC5's "deck state persists" is satisfied because deck state is fully *recoverable* from the two persisted lists.

**Forward-looking note (for 22-3 wiring, non-blocking — deferred):** The production consumer must append a freshly-drawn seed to `active_seeds` within the *same* persisted turn as the `draw()`. If a draw isn't recorded before save, the derived reconstruction will (correctly, fail-safe) redeal it — but the wiring story should make draw→record atomic to avoid surprise. Recommend 22-3 add a `SeedDeck.from_snapshot(snapshot, seeds)` classmethod that centralizes the `{active}∪{ghosts}` derivation so callers don't reinvent it. Logged in Delivery Findings (Dev) already; flagged here for the 22-3 architect.

**Decision:** Proceed to review (TEA verify). No hand-back to Dev — implementation is correct and the two deviations are improvements, not drift.

## Sm Assessment

Setup complete. Story 22-1 is the foundation story for Epic 22 (seed trope engine): pure schema + deck-engine work, no narrator wiring (deferred to 22-2/22-3). Five ACs are well-bounded and self-contained within `sidequest-server`.

**Handoff to TEA (red phase):**
- AC1–AC4 are schema + engine contracts ideal for TDD: `SeedTrope`/`SeedState`/`SeedGhost` Pydantic models, `SeedDeck` draw-without-replacement, ghost retention, active-seed tracking.
- AC2 deck draw must be reproducible (`random.Random` seeded by `session_id`) — test draw order determinism and without-replacement contract.
- AC5 persistence is JSON round-trip via existing `game_state.snapshot_json` (ADR-023) — no schema migration. Test that drawn seeds don't return to the deck after reload.
- **Test data discipline (memory):** use minimal seed YAML *fixtures* for unit tests; do NOT load live `genre_packs/*` and assert properties. Live-pack seed content is a content-team deliverable surfaced by a validator, not a server unit test.
- Single repo: `sidequest-server`, branch `feat/22-1-seed-trope-engine` (created, checked out).
- No Jira (this project never uses Jira).

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** New schema + engine code (SeedTrope/SeedState/SeedGhost models, SeedDeck draw engine, GameSnapshot persistence) — pure TDD surface.

**Test Files:**
- `tests/game/test_seed_trope_models.py` — AC1 (SeedTrope), AC3 (SeedGhost), AC4 (SeedState): fields, defaults, round-trip, extra-field policy, immutability, expiry mapping.
- `tests/game/test_seed_deck.py` — AC2 (SeedDeck): draw/remove, exhaustion→None, without-replacement, reproducible-by-session_id, empty/single-seed edges, drawn_ids reconstruction.
- `tests/game/test_seed_persistence.py` — AC5: GameSnapshot seed-field defaults + JSON round-trip, **SqliteStore save/load wiring**, and the load-bearing "drawn seeds don't return after reload" assertion.

**Tests Written:** 26 tests covering 5 ACs
**Status:** RED (failing — all three modules error at import on missing `SeedTrope`; confirmed by testing-runner as proper RED, no test-authoring bugs)

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #2 mutable defaults | `test_seed_trope_list_fields_default_empty_not_shared`, `test_constructor_drawn_ids_defaults_to_empty_not_shared` | failing (RED) |
| #6 test quality (no vacuous asserts) | all — every test asserts a specific value, not bare truthiness | n/a (self-check) |
| #8 unsafe deserialization / extra-field policy | `test_seed_trope_rejects_unknown_field` (forbid), `test_seed_state_ignores_unknown_fields_for_forward_compat` (ignore) | failing (RED) |
| Wiring (server CLAUDE.md — behavior not source-grep) | `test_snapshot_persists_seeds_through_sqlite_store`, `test_drawn_seeds_do_not_return_after_reload` | failing (RED) |
| Immutability invariant (AC3) | `test_seed_ghost_is_immutable` | failing (RED) |

**Rules checked:** 3 of the directly-applicable lang-review rules (#2 mutable defaults, #6 test quality, #8 deserialization/extra-field policy) have explicit test coverage. Most other checks (#1 silent exceptions, #5 path handling, #7 resource leaks, #9 async, #11 input validation) do not apply to pure-Pydantic schema + an in-memory deck engine with no I/O, network, or user-input boundary. Resource handling for the DB is owned by the existing `SqliteStore` context-manager code, not new in this story.
**Self-check:** 0 vacuous tests — every test asserts a concrete value or membership; no `assert True`, no bare-truthy `assert result`, no assertion-free calls.

**Handoff:** To Dev for implementation (GREEN). Implement `SeedTrope` in `sidequest/genre/models/tropes.py` (mirror `TropeDefinition` `extra="forbid"`), `SeedState`/`SeedGhost` in `sidequest/game/session.py` (`extra="ignore"` like `TropeState`; `SeedGhost` frozen), `SeedDeck` in new `sidequest/game/seed_deck.py`, and add `active_seeds`/`seed_ghosts` fields to `GameSnapshot`. See Design Deviations for the injected-seeds and derived-drawn_ids contracts.

### Verify Phase (simplify + quality-pass)

**Phase:** finish
**Status:** GREEN confirmed (27/27 story tests passing)

#### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 6 (3 source, 3 test)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | 0 — confirmed SeedTrope/TropeDefinition and SeedState/TropeState sibling overlap is intentional, not extractable duplication |
| simplify-quality | clean | 0 — naming/type-safety/conventions all sound; "unwired" code correctly recognized as intentional 22-1 scope |
| simplify-efficiency | 3 findings | All 3 on **pre-existing untouched code** in `session.py` (`party_location()` L920 medium; region-discovery L1129 medium / L1197 low) — outside this story's diff |

**Applied:** 0 high-confidence fixes (none found within story scope)
**Flagged for Review:** 0 (the 3 efficiency findings are out-of-scope — they target pre-existing `party_location`/region-discovery code I did not touch; my diff adds only the seed classes ~L417 and two `GameSnapshot` fields L625-626)
**Noted:** 3 (out-of-scope efficiency observations on pre-existing code — see Delivery Findings)
**Reverted:** 0

**Overall:** simplify: clean (for the story diff; no changes applied)

#### Quality Checks

- **ruff check** (6 changed files): All checks passed.
- **pyright** (3 source files): `seed_deck.py` and `tropes.py` are type-clean (0 errors). 2 errors reported in `session.py` are at L870 and L1371 — pre-existing code (float conversion / `Disposition` literal) unrelated to my additions; not introduced by this story.
- **Story tests:** 27/27 passing (serial `-n0 --timeout=30`, confirmed by testing-runner).

**Deviations (verify):** No new deviations — no simplify changes were applied, so no implementation drift introduced during verify.

**Handoff:** To Reviewer for code review.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/genre/models/tropes.py` — added `SeedTrope` model (sibling to `TropeDefinition`, `extra="forbid"`, required `id`).
- `sidequest/game/session.py` — added `SeedGhost` (frozen, record-only) and `SeedState` (with `is_expired()` + `to_ghost()`); added `active_seeds` and `seed_ghosts` fields to `GameSnapshot`.
- `sidequest/game/seed_deck.py` — new `SeedDeck` draw-without-replacement engine, sha256-derived reproducible shuffle, `drawn_ids` reconstruction.
- `tests/game/test_seed_deck.py` — fixed an infinite-loop authoring bug in two reproducibility tests (see Design Deviations).

**Tests:** 27/27 passing (GREEN, serial `-n0 --timeout=30`). No regressions — the source changes are additive (new classes + defaulted optional fields) and the full `tests/game` suite was already green on these changes apart from pre-existing FileNotFoundError content-coupled failures unrelated to this story.
**Branch:** feat/22-1-seed-trope-engine (pushed)

**Handoff:** To next phase (spec-check / architect).

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Gap** (non-blocking): Story context (`context-story-22-1.md`) and epic context (`context-epic-22.md`) did not exist when RED began — `sm-setup` created the session file but not the context docs the `sm_setup_exit` gate's `create_context` recovery is meant to produce. Created both via `/pf-context` before writing tests. Affects the SM setup flow (context-creation step should run during setup, not be discovered missing at RED). *Found by TEA during test design.*
- **Question** (non-blocking): AC2 says the deck "loads seeds from YAML via genre loader" but no seed-loading exists in `genre/loader.py` yet (only `tropes.yaml` → `TropeDefinition`). Where do seed decks live — a `seed_tropes:` section in `tropes.yaml`, or a separate `seeds.yaml`? Affects `sidequest/genre/loader.py` (needs a seed-loading path) and 22-2 content authoring. Deferred out of 22-1 per scope, but the loader wiring needs an owner. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `SeedDeck` is implemented but has no production consumer yet — nothing in dispatch/handlers constructs a deck, draws, or migrates expired `active_seeds` → `seed_ghosts`. This is by design (22-1 is schema+engine; wiring is 22-2/22-3), but the engine ships unwired. The active→ghost expiry transition (`SeedState.is_expired()` / `to_ghost()`) likewise has no turn-loop caller yet. Affects future `sidequest/handlers/` + narrator dispatch (22-3). *Found by Dev during implementation.*
- **Improvement** (non-blocking): The seed-loading path in `genre/loader.py` (TEA's open question) will need to decide `seed_tropes:` in `tropes.yaml` vs a separate `seeds.yaml`, and pass the loaded `list[SeedTrope]` into `SeedDeck(seeds=...)`. Recommend resolving at spec-check so 22-2 content authors have a target schema. Affects `sidequest/genre/loader.py` and `sidequest/genre/models/pack.py`. *Found by Dev during implementation.*

### TEA (test verification)
- **Improvement** (non-blocking): simplify-efficiency flagged two consolidation opportunities in pre-existing `session.py` code outside this story's diff — `party_location()` emits near-identical OTEL spans across 4 branches (L920, medium confidence), and `discovered_regions`/`discover_regions` share near-identical validate/canonicalize/dedup loops (L1129, medium). Not touched here (out of scope); recorded for a future cleanup story. Affects `sidequest/game/session.py`. *Found by TEA during test verification.*
- **Improvement** (non-blocking): pyright reports 2 pre-existing type errors in `session.py` (L870 `object`→`ConvertibleToFloat`; L1371 `Literal[-20,0]`→`Disposition`) unrelated to this story's additions (my new code is type-clean). Worth a typing-debt sweep. Affects `sidequest/game/session.py`. *Found by TEA during test verification.*

## Design Deviations

### TEA (test design)
- **Deck constructor takes injected seeds, not a YAML-loading constructor**
  - Spec source: context-story-22-1.md, AC2 / epic AC2
  - Spec text: "Constructor takes `genre_id`, `world_id`, loads seeds from YAML via genre loader"
  - Implementation: Tests construct `SeedDeck(genre_id, world_id, session_id, seeds=[...], drawn_ids=...)` with an explicitly injected seed list. "Loads from YAML via genre loader" is treated as the *caller's* responsibility in the (later) wiring story; the deck itself stays pure.
  - Rationale: feedback_no_content_coupled_tests — unit tests must not load live `genre_packs/*` and assert on their content. An injected-seed contract keeps the deck testable with fixtures and decoupled from content authoring (22-2). The genre-loader→deck wiring is a content/integration concern surfaced later, not a 22-1 server unit test.
  - Severity: minor
  - Forward impact: Dev should accept an explicit `seeds` list (and optional `drawn_ids`) on the constructor; whoever wires production loads the list from the GenrePack/World and passes it in. Architect to confirm at spec-check.
- **drawn_ids reconstructed from active_seeds ∪ seed_ghosts in the reload test, not asserted as a dedicated persisted field**
  - Spec source: context-story-22-1.md, AC5
  - Spec text: "Deck state, active_seeds, and seed_ghosts all persist in `snapshot_json`"
  - Implementation: `test_drawn_seeds_do_not_return_after_reload` derives the drawn set as `{active}∪{ghosts}` and feeds it to a rebuilt deck, asserting drawn seeds aren't redealt — rather than asserting a third `seed_deck`/`drawn_ids` field on `GameSnapshot`.
  - Rationale: Every drawn seed is, by definition, either still active or already a ghost, so the union IS the drawn set. Testing the *behavior* ("drawn seeds don't return") avoids over-prescribing a storage shape the Dev/Architect may reasonably choose differently (derived vs. stored).
  - Severity: minor
  - Forward impact: If Dev adds an explicit persisted deck-state field instead of deriving, the behavioral test still passes — no rework. Architect to decide derived-vs-stored at spec-check.

### Dev (implementation)
- **Fixed an infinite-loop bug in two TEA reproducibility tests**
  - Spec source: tests/game/test_seed_deck.py (TEA red-phase tests), AC2
  - Spec text: `order_a = [s.id for s in iter(lambda: _make_deck(...).draw(), None)]`
  - Implementation: Replaced the `iter(lambda: ...)` form (which built a *fresh* deck on every call, so `draw()` never returned `None` → infinite hang) with a `_draw_all(deck)` helper that constructs the deck once and drains it. Assertions and the reproducibility contract are unchanged.
  - Rationale: The test could never pass as written — it was a mechanical authoring bug, not a contract disagreement. Fixing the loop preserves the exact intent (same session_id → same order; different → different). Surfaced as an xdist worker crash / 30s-timeout hang.
  - Severity: minor
  - Forward impact: none — assertions identical; pure test-harness correctness fix.
- **SeedDeck derives an integer PRNG seed via sha256 instead of passing the session_id string to `random.Random`**
  - Spec source: context-story-22-1.md, AC2 / Technical Approach
  - Spec text: "`draw()` method uses Python's `random.Random` seeded by `session_id` for reproducibility"
  - Implementation: `random.Random(_seed_int(session_id))` where `_seed_int` is `int.from_bytes(sha256(session_id))`. Still seeded by `session_id`, just hashed to an int first.
  - Rationale: A hashed int seed is reproducible across processes and Python versions and is independent of `PYTHONHASHSEED` (unlike builtin `hash()`), which matters because the deck is re-instantiated on session reload and must deal the identical order.
  - Severity: minor
  - Forward impact: none — reproducibility contract is satisfied; transparent to callers.

## Branch

- **Repository:** sidequest-server
- **Branch:** feat/22-1-seed-trope-engine
- **Started:** 2026-05-21

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (27/27 green, lint clean, 2 pre-existing pyright errors, 0 new) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 8 | confirmed 5 (as non-blocking/deferred), dismissed 2, deferred 1 (wiring=in-spec) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 3 (non-blocking), dismissed 2 (extra=ignore intentional; draw()=None documented) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 4 (non-blocking nits), dismissed 4 (low/duplicate of others) |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 (LOW — comment rot), dismissed 0 |
| 6 | reviewer-type-design | Yes | findings | 8 | confirmed 3 (non-blocking), downgraded 4 (TropeState convention), dismissed 1 |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0 — domain genuinely clean (verified 7 rule classes) |
| 8 | reviewer-simplifier | Yes | findings | 4 | confirmed 1 (LOW), dismissed 3 (spec-keying / Dev-deviation / harmless) |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 1 (non-blocking: empty session_id), deferred 1 (OTEL→22-2), confirmed 1 (LOW: probabilistic test) |

**All received:** Yes (9 returned, 6 with findings)
**Total findings:** 6 confirmed actionable (all non-blocking or blocking-for-22-2), 12 dismissed/downgraded (with rationale), 2 deferred to 22-2 (wiring + OTEL, both in-spec)

### Cross-subagent convergence (the signal)

Four independent specialists converged on one cluster — **missing input-validity guards on the pure engine/schema**:
- **`lifespan_turns` 0/negative** → always-expired / expired-before-activation: flagged by edge-hunter (high), silent-failure (high), type-design (high), test-analyzer (medium). 4-way convergence.
- **Duplicate seed `id` in injected list** → second seed silently undealt forever: edge-hunter (high), silent-failure (high), test-analyzer (medium). 3-way.
- **Empty `session_id`** → degenerate (identical) shuffle, silently accepted: rule-checker (high). 1-way but valid.
- **`id=""` defaults on SeedState/SeedGhost**: edge (medium), silent-failure (medium), type-design (high) — **downgraded** (see Rule Compliance: TropeState convention, Architect-endorsed).

## Rule Compliance

Exhaustive enumeration against python lang-review (14 checks) + CLAUDE.md/SOUL.md additional rules. Every changed type/function/field judged.

### Python lang-review checklist

- **#1 Silent exceptions** — COMPLIANT. No try/except anywhere in the diff (`_seed_int`, `SeedDeck.__init__`, `draw`, `is_expired`, `to_ghost` all exception-free). 5 instances clean.
- **#2 Mutable defaults** — COMPLIANT (12 instances). All list fields use `Field(default_factory=list)`; `drawn_ids` uses `None` sentinel + `set(...)` copy; `_ordered = list(seeds)` is a fresh copy per instance; test helpers use `None`/string-literal defaults. No shared mutable state.
- **#3 Type annotations at boundaries** — COMPLIANT for production (all 8 public fns/methods fully annotated incl. return types). One LOW violation: `_make_deck` test helper `seeds` param unannotated (test_seed_deck.py:199) — test-internal, non-blocking.
- **#4 Logging coverage/correctness** — N/A for pure predicates/transforms. `draw()` emits no OTEL span; deferred to 22-2 wiring (see A6).
- **#5 Path handling** — COMPLIANT. Zero file I/O in the diff.
- **#6 Test quality** — COMPLIANT (23 tests, 0 vacuous, 0 assertion-free, 0 unexplained skips). Two LOW nits: `test_seed_trope_lifespan_turns_is_int` is tautological (subsumed by the field-value test); `test_different_session_id_produces_different_draw_order` is probabilistic (~1/3.6M false-fail). Both non-blocking.
- **#7 Resource leaks** — COMPLIANT. No open/connect/Lock outside existing `SqliteStore` context management.
- **#8 Unsafe deserialization** — COMPLIANT. Pydantic `model_validate`/`model_dump_json` only; no pickle/eval/yaml.load/subprocess.
- **#9 Async pitfalls** — COMPLIANT. All new code synchronous; no blocking calls in async context.
- **#10 Import hygiene** — COMPLIANT. No star imports; `genre.models.tropes` is a downward dependency (no cycle); `__all__` absence consistent with adjacent modules.
- **#11 Input validation at boundaries** — One CONFIRMED gap: empty `session_id` silently accepted (seed_deck.py:36). Non-blocking in 22-1 (no production caller); blocking-for-22-2 (loader boundary). See Delivery Findings.
- **#12 Dependency hygiene** — COMPLIANT. No new deps (hashlib/random stdlib; pydantic already present).
- **#13 Fix-introduced regressions** — COMPLIANT. New `GameSnapshot` fields default to `[]` + `extra="ignore"` → old saves load clean both directions.
- **#14 State cleanup ordering** — COMPLIANT. `draw()` adds to `drawn_ids` BEFORE returning; no fallible side effect after mutation.

### Additional rules (CLAUDE.md / SOUL.md)

- **No Silent Fallbacks** (`<critical>`) — Enumerated every default/guard. Three patterns are technically loud-worthy (empty session_id, duplicate id, 0/negative lifespan) but **none is reachable in 22-1's shipped surface** — only test fixtures construct these objects, all with valid inputs. The correct validation home is the 22-2 loader boundary (where authored YAML enters). Recorded as **blocking-for-22-2** delivery findings so they cannot silently ship. `extra="ignore"` on SeedState/SeedGhost is an intentional forward-compat choice mirroring `TropeState`, NOT a silent fallback.
- **No Stubbing** — COMPLIANT (6 instances). All classes fully implemented; "no resolution mechanics (22-3)" is a documented scope limit, not a skeleton.
- **Don't Reinvent** — COMPLIANT. Uses stdlib `random.Random` and existing `SqliteStore.open_in_memory()`.
- **Verify Wiring / non-test consumers** — IN-SPEC. `SeedDeck`/`SeedTrope` have no production consumer by design (Architect spec-check confirmed wiring deferred to 22-2/22-3). `GameSnapshot.active_seeds`/`seed_ghosts` ARE wired into the real persistence path and tested.
- **Every Test Suite Needs a Wiring Test** — COMPLIANT. `test_snapshot_persists_seeds_through_sqlite_store` + `test_drawn_seeds_do_not_return_after_reload` drive real `SqliteStore` I/O (not in-memory model copies). Verified genuine by test-analyzer and rule-checker.
- **No Source-Text Wiring Tests** — COMPLIANT. No `read_text()`/regex-on-source assertions. Wiring proven behaviorally via persistence round-trip.
- **OTEL Observability** (A6) — `SeedDeck.draw()` is the seed trope-engine activation point and emits no span. Acceptably deferred (no production call site in 22-1) but the obligation MUST transfer to 22-2 — recorded as blocking-for-22-2.

### The `id=""` / bare-int downgrade (rule-matching finding, NOT dismissed — downgraded with cited contradicting convention)

type-design/edge/silent-failure flagged `SeedState.id=""`, `SeedGhost.id=""`, and bare-`int` turn fields (no `ge=0`) as broken invariants (up to HIGH). Per my rules I may not *dismiss* a rule-matching finding, but I may downgrade citing a contradicting convention: **`TropeState` (session.py:409) has the identical `id: str = ""` default and bare-`int` `beats_fired`**, and the Architect's spec-check explicitly endorsed "`SeedState`/`SeedGhost` mirror `TropeState`." These are the established codebase convention for save-round-trippable state models (lenient defaults for forward-compat). Hardening them would *diverge* SeedState from its sibling. Downgraded to LOW/informational. Note the deliberate, correct split: the *authored* model `SeedTrope` is strict (`id`/`name` required, `extra="forbid"`); the *save-state* models are lenient — exactly right.

## Devil's Advocate

Argue this code is broken. A career GM authoring a `tea_and_murder` seed deck in YAML fat-fingers `lifespan_turns: 0` (or omits it — `extra="forbid"` catches extra keys but never a *missing* defaulted field). The seed deals, activates at turn N, and `is_expired(N)` returns `True` on the same turn — the seed is a ghost before the narrator ever sees it. Worse, `lifespan_turns: -3` makes `is_expired` return `True` for turns *before* activation: a seed that is retroactively dead. Neither raises. Now imagine the author duplicates an entry id (copy-paste in a 30-seed YAML): `draw()` deals the first, marks the id, and the duplicate is silently unreachable for the entire campaign — the deck under-counts its own capacity with no error and no log. The GM panel (Sebastien's mechanical-visibility feature) shows nothing because `draw()` emits no OTEL span — the lie-detector is blind to seed deals. A confused caller in 22-2 passes `session_id=""` (uninitialized session) and *every* such deck deals the identical order — reproducibility becomes accidental collision. A malicious or corrupt save omits a ghost's `id`; `extra="ignore"` swallows it and the ghost loads as `id=""`, and two such ghosts collapse to a single empty-string entry in `drawn_ids`, potentially blocking a real future seed whose id is also accidentally empty. A stressed filesystem mid-write truncates the snapshot JSON — but here Pydantic + `extra="ignore"` + defaults degrade gracefully to empty lists rather than crashing, which is arguably *too* graceful (it masks corruption).

**What this uncovers:** every one of these is real — but every one requires a *producer* that does not exist in 22-1. The shipped surface constructs these objects only in tests, with valid inputs. The diff is a pure schema + pure engine + persistence fields: green, lint-clean, no new type errors, security-clean, convention-following, with a genuine persistence wiring test. The Devil's Advocate scenarios are all reachable *only* once 22-2 wires a YAML loader and a turn-loop caller — which is precisely why the validity guards (lifespan `ge`, duplicate-id uniqueness, non-empty session_id) and the `draw()` OTEL span belong at that boundary, and why I record them as **blocking-for-22-2** rather than rejecting a correct foundation story. The validation's home is where untrusted/authored data enters the system, not bolted speculatively onto a model with no caller.

## Reviewer Assessment

**Verdict:** APPROVED

Story 22-1 ships a pure seed-trope schema (`SeedTrope`), two save-state models (`SeedState`, `SeedGhost`), a draw-without-replacement engine (`SeedDeck`), and two persisted `GameSnapshot` fields. Foundation story, intentionally unwired (Architect-confirmed; wiring is 22-2/22-3). 27/27 tests green, ruff clean, 0 new pyright errors (2 pre-existing in `session.py` unrelated), security clean.

**Data flow traced:** authored `SeedTrope` (injected list) → `SeedDeck.shuffle(seeded by session_id)` → `draw()` skips `drawn_ids` → drawn seed becomes `SeedState` on `GameSnapshot.active_seeds` → `model_dump_json()` → `SqliteStore` `snapshot_json` column → reload via `model_validate` → `drawn_ids` reconstructed as `{active}∪{ghosts}` → rebuilt deck never redeals. Safe because the reconstruction is provably complete (every drawn seed is either active or a ghost) and persistence is migration-free (round-trips through existing column). Verified end-to-end by `test_drawn_seeds_do_not_return_after_reload`.

**Pattern observed:** deliberate strict/lenient model split — `SeedTrope` authored-strict (`extra="forbid"`, required `id`/`name`) vs `SeedState`/`SeedGhost` save-lenient (`extra="ignore"`, full defaults, mirroring `TropeState` at session.py:409). Correct and convention-consistent.

**Error handling:** `draw()` returns documented `None` sentinel on exhaustion (seed_deck.py:62); `extra="ignore"` degrades old/partial saves to defaults rather than crashing (session.py:439, 84). The convergent guard-gaps (validity of authored values) are deferred to the loader boundary.

**Confirmed findings (tagged by source):**
- `[EDGE]`/`[SILENT]`/`[TYPE]`/`[TEST]` `lifespan_turns` 0/negative → always-expired/expired-before-activation (tropes.py:79, session.py:445). MEDIUM, blocking-for-22-2.
- `[EDGE]`/`[SILENT]`/`[TEST]` duplicate seed `id` silently undealt (seed_deck.py:58). MEDIUM, blocking-for-22-2.
- `[RULE]` empty `session_id` → degenerate shuffle, silently accepted (seed_deck.py:36). MEDIUM, blocking-for-22-2.
- `[RULE]`/`[SILENT]` `draw()` emits no OTEL span (seed_deck.py:62). Deferred-to-22-2 (OTEL obligation transfers to call site).
- `[TYPE]` `narrative_hint: str = ""` vs sibling `description: str | None = None` nullability inconsistency (tropes.py:81). LOW, non-blocking.
- `[DOC]` `Epic 22`/`(22-3)` tracker-label rot in docstrings (seed_deck.py:7, session.py:418/433, tropes.py:148). LOW, non-blocking.

**Downgraded (rule-matching, contradicting convention cited):**
- `[TYPE]`/`[EDGE]`/`[SILENT]` `id=""` + bare-`int` defaults on `SeedState`/`SeedGhost` → matches `TropeState` convention (session.py:409), Architect-endorsed. Downgraded HIGH→LOW.

**Dismissed (with rationale):**
- `[SIMPLE]` sha256 `_seed_int` "over-engineering" — DISMISSED: Dev's logged deviation justifies it (cross-process/cross-version + PYTHONHASHSEED independence); rationale sound, transparent to callers.
- `[SIMPLE]` `genre_id`/`world_id` stored-but-unused — DISMISSED: AC2 mandates the deck be "keyed per (genre, world, session_id)"; storing the key components is spec-required even if engine logic only reads `session_id`.
- `[SIMPLE]` defensive `list(self.delivery_hints)` in `to_ghost` — DISMISSED: harmless (Pydantic copies on construction anyway); not a defect.
- `[EDGE]`/`[TYPE]` `drawn_ids` falsy-check vs `is not None` (seed_deck.py:47) — DISMISSED as defect (result is identical: empty set ≡ None both yield `set()`); noted as cosmetic in Delivery Findings.
- `[SEC]` — nothing to dismiss; domain verified clean.

**Handoff:** To SM for finish-story.

### Deviation Audit (Reviewer)

All four logged deviations reviewed:

- **TEA: Deck takes injected `seeds`, not a YAML-loading constructor** → ✓ ACCEPTED by Reviewer: dependency injection keeps the engine pure and honors no-content-coupled-tests; Architect already endorsed (Recommendation A). Agrees with author reasoning.
- **TEA: `drawn_ids` reconstructed from `active_seeds ∪ seed_ghosts`, not a dedicated field** → ✓ ACCEPTED by Reviewer: the union is provably the complete drawn set (every drawn seed is active or ghost); single source of truth beats a denormalized field that can drift. Verified via `test_drawn_seeds_do_not_return_after_reload`.
- **Dev: Fixed infinite-loop bug in two TEA reproducibility tests** → ✓ ACCEPTED by Reviewer: the `iter(lambda: _make_deck(...).draw(), None)` form rebuilt a fresh deck per call → never exhausts → hang. `_draw_all` fix preserves identical assertions/contract. Pure harness correctness.
- **Dev: sha256-derived int PRNG seed instead of raw string to `random.Random`** → ✓ ACCEPTED by Reviewer: reproducible across processes/versions and PYTHONHASHSEED-independent; reproducibility contract satisfied. (Simplifier's counter-proposal dismissed above — Dev's rationale is the stronger call for a reload-dependent shuffle.)

#### Reviewer (audit)
- No undocumented spec deviations found. AC1/AC3/AC4 exactly aligned; AC2/AC5 satisfied via the two Architect-endorsed deviations above.

## Delivery Findings

<!-- Append-only below. Never edit/remove other agents' entries. -->

### Reviewer (code review)
- **Gap** (blocking): `SeedTrope.lifespan_turns` / `SeedState.lifespan_turns` accept `0` and negative values, producing seeds that expire on (or before) activation. No validator; `extra="forbid"` does not catch a missing/zero defaulted field. Affects `sidequest/genre/models/tropes.py` (add `Field(ge=1)` or validate at the 22-2 loader boundary). Validity belongs where authored YAML enters the system. *Found by Reviewer during code review.*
- **Gap** (blocking): `SeedDeck` silently drops a seed when the injected list contains duplicate `id`s (second occurrence never dealt). Affects `sidequest/game/seed_deck.py` + the 22-2 loader (add an id-uniqueness guard that raises, per No Silent Fallbacks — most naturally at the loader/pack-model boundary). *Found by Reviewer during code review.*
- **Gap** (blocking): `SeedDeck.__init__` accepts an empty `session_id` silently, yielding an identical (degenerate) shuffle across all such decks. Affects `sidequest/game/seed_deck.py` (raise on empty `session_id`, or guarantee non-empty at the 22-2 caller). *Found by Reviewer during code review.*
- **Gap** (blocking): `SeedDeck.draw()` emits no OTEL span despite being the seed trope-engine activation point (CLAUDE.md OTEL principle: "Trope engine — activations"). The GM panel (Sebastien's mechanical-visibility feature) will be blind to seed deals unless 22-2/22-3 adds a span at the wiring call site. Affects the 22-2/22-3 turn-loop integration. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `SeedTrope.narrative_hint: str = ""` uses empty-string-as-absent while the same model's `description: str | None = None` uses true optional — callers must check both forms. Consider `narrative_hint: str | None = None` for consistency. Affects `sidequest/genre/models/tropes.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `SeedDeck.__init__` `drawn_ids` guard `if drawn_ids else set()` treats an explicit empty set identically to `None` (harmless — same result — but signals the wrong mental model). `set(drawn_ids) if drawn_ids is not None else set()` is clearer. Affects `sidequest/game/seed_deck.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Two test-quality nits — `test_seed_trope_lifespan_turns_is_int` is tautological (subsumed); `test_different_session_id_produces_different_draw_order` is probabilistic (~1/3.6M false-fail). Consider pinning the latter to a known-different first element. Affects `tests/game/test_seed_deck.py`, `tests/game/test_seed_trope_models.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Docstrings carry `(Epic 22)` / `(22-3)` tracker labels that will rot. Prefer the design rationale over the ticket pointer. Affects `sidequest/game/seed_deck.py`, `sidequest/game/session.py`, `sidequest/genre/models/tropes.py`. *Found by Reviewer during code review.*