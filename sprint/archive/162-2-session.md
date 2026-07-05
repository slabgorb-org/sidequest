---
story_id: "162-2"
jira_key: ""
epic: "162"
workflow: "tdd"
---
# Story 162-2: Identity by id, not name: unify invented_from/pool_origin/manual_origin/creature_id into one typed Origin; dedup/purge/seating key on creature_id/authored id; narrator prose names recorded as aliases (alias ledger) — kills two-names-one-enemy identity forks

## Story Details
- **ID:** 162-2
- **Title:** Identity by id, not name: unify invented_from/pool_origin/manual_origin/creature_id into one typed Origin; dedup/purge/seating key on creature_id/authored id; narrator prose names recorded as aliases (alias ledger) — kills two-names-one-enemy identity forks
- **Points:** 3
- **Priority:** p1
- **Type:** refactor
- **Repos:** server
- **Workflow:** tdd
- **Stack Parent:** none

## Branch Information
- **Branch Strategy:** gitflow (feat/162-2-identity-by-id-typed-origin)
- **Repository:** sidequest-server
- **Base:** origin/develop

## Context
- sprint/context/context-story-162-2.md
- sprint/context/context-epic-162.md

## Acceptance Criteria
1. All NPC/creature identity consolidated under a single typed Origin model (unifying invented_from/pool_origin/manual_origin/creature_id)
2. Dedup/purge/seating operations key on creature_id or authored id (not name strings)
3. Narrator prose names recorded in an alias ledger; aliases do not affect identity
4. Two-names-one-enemy identity forks eliminated (verified by integration tests)
5. OTEL spans on identity derivation and alias recording (lie-detector)

**Phase:** finish
**Phase Started:** 2026-07-05T18:38:34Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-05T17:09:02Z | 2026-07-05T17:11:59Z | 2m 57s |
| red | 2026-07-05T17:11:59Z | 2026-07-05T17:31:25Z | 19m 26s |
| green | 2026-07-05T17:31:25Z | 2026-07-05T17:51:29Z | 20m 4s |
| review | 2026-07-05T17:51:29Z | 2026-07-05T18:07:28Z | 15m 59s |
| red | 2026-07-05T18:07:28Z | 2026-07-05T18:12:55Z | 5m 27s |
| green | 2026-07-05T18:12:55Z | 2026-07-05T18:22:08Z | 9m 13s |
| review | 2026-07-05T18:22:08Z | 2026-07-05T18:38:34Z | 16m 26s |
| finish | 2026-07-05T18:38:34Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)

- **Gap** (non-blocking): `SPAN_IDENTITY_RESOLVED` needs a `SpanRoute` registration (component routing) in addition to the constant the tests pin — the tests assert the name and emission, not GM-panel routing.
  Affects `sidequest/telemetry/spans/` (add constant + SPAN_ROUTES entry, npc.py family).
  *Found by TEA during test design.*
- **Gap** (non-blocking): the narrator-mention seams (`_apply_npc_mentions` exact/casefold/comma-inverted/invented_from legs) and the seeder's pool-member lookup (`m.name == actor.name`, exact) should adopt the unified resolver too; RED pins the Npc-roster seams (seeder, roster-resolve, inject dedup) but not the mention path or the `NpcPoolMember` leg.
  Affects `sidequest/server/narration_apply.py` and `sidequest/server/dispatch/encounter_lifecycle.py` (wire `resolve_roster_npc` / a pool sibling; reviewer should verify).
  *Found by TEA during test design.*
- **Question** (non-blocking): `identity_key` literal format is unpinned — tests assert equality properties only (same creature_id ⇒ same key; authored dominates; None-origin ≡ id-less origin). Dev owns the encoding.
  Affects `sidequest/game/origin.py` (net-new).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): AC2's "purge" term has no remaining name-keyed target — 162-1 replaced the two name-matching purge tourniquets with `reconcile_content` keyed on `content_sha`, which is already id-shaped. No purge test written; nothing left to key by name.
  Affects nothing (documenting the AC-term drift for the reviewer).
  *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (non-blocking): two more exact-match `by_name` dicts remain in `encounter_lifecycle.py` — the Fate seeder `_seed_fate_opponents` (~L595) and `_publish_combat_edge_to_npcs` (~L808). Only the hp_depletion seeder was cut over to `resolve_roster_npc` (the seam with failing tests). Same one-line cutover applies; candidates for the epic's follow-up story alongside TEA's mention-path/pool-member gaps.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py` (adopt `resolve_roster_npc`).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): the testing-runner helper applied a production fix during GREEN verification (the inject dedup name-leg, see Dev deviation #1) instead of only reporting. Fix was reviewed, comment corrected, and kept — but the helper's report-only lane should be tightened.
  Affects `.pennyfarthing` testing-runner agent definition (out of this story's repo scope).
  *Found by Dev during implementation.*

### Reviewer (code review)

- **Gap** (blocking): alias/case-variant-seated `EncounterActor.name` is unresolvable by `find_creature_core` — opponent drops from HP bars, WN attack returns not_found; the seeder's own documented reachability invariant is broken. Fix: canonicalize the seat name on resolver hit; test reachability, not just roster size.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py` (seeder :375 area + head check :1168) and `tests/server/test_162_2_identity_fork_seating.py` (add reachability assertions).
  *Found by Reviewer during code review.*
- **Gap** (blocking): `normalize_name` lacks diacritic folding — reuse `sidequest/foundation/slug_fold.py:fold_to_ascii` (the primitive alias_resolution.py already uses for this exact bug class).
  Affects `sidequest/game/origin.py:65` (compose fold_to_ascii; add diacritic tests).
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): `identity.resolved`'s SPAN_ROUTES extract lambda has no `WatcherSpanProcessor.on_end` typed-event test (every sibling npc.* route has one in tests/server/test_watcher_events.py).
  Affects `tests/server/test_watcher_events.py` (add the on_end test).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the id-leg dedup negative guard doesn't isolate the id mechanism (names also differ); ambiguous-alias collision resolves by accidental roster order untested; `pool_origin` exclusion from Origin undocumented (see Reviewer audit).
  Affects `tests/server/test_162_2_identity_fork_seating.py`, `sidequest/game/origin.py`, docstrings per the [LOW][DOC] finding bundle.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, round 2 — the 162-epic follow-up bundle): (a) decoy-roster hardening for the three canonicalization tests (mutation-confirmed single-entry-roster blindspot); (b) `participant.joined`/init-span names compute pre-rename on the npcs_present path (stale alias in one GM-panel event, reproduced); (c) two comment lines overclaim (case-variant rebind emits no span; "edge publish" uses its own by-name dict); (d) NpcMention rebind should use `dataclasses.replace` to stop dropping flags; (e) diacritic-leg integration test at a seat seam; (f) `ruff format` one test file at merge. Bundle these with the already-filed mention-path / pool-member / Fate-seeder resolver adoptions.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py`, `tests/server/test_162_2_identity_fork_seating.py`.
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

No design deviations (setup phase)

### TEA (test design)
- **Origin precedence arbiter excluded from test scope**
  - Spec source: docs/superpowers/specs/2026-07-05-npc-generation-inventory.md, §8 D1
  - Spec text: "a single NPC Origin Registry ordering (authored > room-bound > region-population > MM pool > narrator mint)"
  - Implementation: Tests pin the typed Origin, id-keyed identity, and alias ledger (D2 + the provenance half of D1); no precedence-arbiter tests
  - Rationale: The epic sequence (context-epic-162) makes the precedence ADR the THIRD story; 162-2's ACs are identity-only. `identity_key`'s authored-dominates-creature rule is a keying rule, not the arbiter.
  - Severity: minor
  - Forward impact: 162-3+ (Green Room precedence ADR) tests the ordering; Origin.kind is designed as its input.
- **Narrator-mention path covered by resolver units, not an integration test**
  - Spec source: session AC4
  - Spec text: "Two-names-one-enemy identity forks eliminated (verified by integration tests)"
  - Implementation: Integration tests drive the seater seams (`_seed_combat_hp_depletion_to_npcs`, `instantiate_encounter_from_trigger` conscription, `inject` dedup) — the seams where the playtest-observed fork actually manifests. The `_apply_npc_mentions` mention path gets resolver unit coverage only.
  - Rationale: The mention path requires the full narration-apply harness for one additional leg of the same resolver; the seater is where "Hold-Dead vs Molgrath" forked in production (survey §5). Logged as a Delivery Finding so Dev wires the mention seams through the same resolver.
  - Severity: minor
  - Forward impact: Reviewer should verify mention-path adoption; a follow-up integration test can land with GREEN if Dev's wiring touches narration_apply.

### Dev (implementation)
- **Inject dedup keys on identity_key AND normalized name, not identity_key alone**
  - Spec source: tests/server/test_162_2_identity_fork_seating.py docstring, item 4
  - Spec text: "``inject``'s authored-vs-procedural dedup keys on ``identity_key`` (the creature_id), not the display name"
  - Implementation: The region-population filter excludes a patch when EITHER its identity_key OR its normalized display name matches an authored patch
  - Rationale: id-only dedup regressed the existing `test_inject_region_population_authored_name_wins_dedup` — same-name/different-id pairs both landed, then collided at the materializer's name-keyed merge with region-pop fields clobbering the authored patch. The name leg preserves pre-162-2 same-name dominance; the id leg adds drift protection. Both TEA dedup tests still pass.
  - Severity: minor
  - Forward impact: none — strictly a superset of the pinned behavior; documented in the dedup comment.
- **Seam cutover limited to the hp_depletion seeder + roster conscription + inject dedup**
  - Spec source: session AC2
  - Spec text: "Dedup/purge/seating operations key on creature_id or authored id (not name strings)"
  - Implementation: `resolve_roster_npc` wired into `_seed_combat_hp_depletion_to_npcs` and `_resolve_opponent_from_roster`; the Fate seeder and `_publish_combat_edge_to_npcs` still use exact-name dicts
  - Rationale: minimalist GREEN — those seams have no failing test and no observed fork; blanket cutover risks unreviewed behavior change in Fate seating (153-9 territory). Logged as a Delivery Finding for the follow-up.
  - Severity: minor
  - Forward impact: the 162 epic's later stories (arbiter) should adopt the resolver at the remaining seams; finding filed.

### Reviewer (audit)
- **TEA: Origin precedence arbiter excluded from test scope** → ✓ ACCEPTED by Reviewer: epic sequencing is sound; identity_key's authored-dominates rule is keying, not arbitration.
- **TEA: Narrator-mention path covered by resolver units, not an integration test** → ✓ ACCEPTED by Reviewer: the seater is the production fork site; findings filed for the mention leg. (Note: the review found the seater integration tests themselves under-pin reachability — see [HIGH] — which is a separate defect, not a fault of this scoping decision.)
- **Dev: Inject dedup keys on identity_key AND normalized name** → ✓ ACCEPTED by Reviewer: the existing `test_inject_region_population_authored_name_wins_dedup` proves the name leg is load-bearing (materializer merges by name downstream); strictly a superset of the pinned behavior.
- **Dev: Seam cutover limited to hp_depletion seeder + roster conscription + inject dedup** → ✓ ACCEPTED by Reviewer: minimalist GREEN with findings filed is the right call; blanket Fate-seeter cutover unreviewed would have been worse. The [HIGH] is about the seams that WERE cut over, not the ones deferred.
- **UNDOCUMENTED (Reviewer audit) — pool_origin is not represented in the typed Origin:** Story title and AC1 say "unify invented_from/**pool_origin**/manual_origin/creature_id into one typed Origin"; the shipped `Origin` has no pool_origin field and `derive_origin` never reads it (it only influences derivation implicitly by falling through to NARRATOR_INVENTED). Neither TEA (whose RED contract omitted it) nor Dev logged this as a deviation. Severity: M (as an undocumented scope cut; the docstrings additionally overclaim it — see [LOW][DOC] finding). Rework must either wire pool_origin into the typed view or document the exclusion explicitly as a decision.
  → ✓ RESOLVED by Reviewer (round 2): Dev took the documented-exclusion option — both docstrings now state pool_origin is promotion lineage, deliberately outside the typed view; verified accurate against the code.

### Reviewer (audit — round 2)
- **TEA rework round 1: "No new deviations"** → ✓ ACCEPTED by Reviewer: the rework tests map one-to-one onto the round-1 findings; the two declined suggestions (creature_type-falsy, second-stamp merge) are documented with defensible rationale in the TEA rework assessment.
- **Dev rework round 1 (no deviations logged)** → ✓ ACCEPTED by Reviewer: the two-seam fix matches the finding's fix-required text; the second seam (head-check rebind) was forced by the failing test, not invented scope.

## Sm Assessment

Setup phase complete; all pre-handoff checklist items verified:

- **Session file:** Created at `.session/162-2-session.md` with story fields, ACs, and phase tracking.
- **Jira:** Explicitly skipped — story 162-2 has no Jira key in sprint YAML (local-only tracking).
- **Story context:** Validated at `sprint/context/context-story-162-2.md`; epic context created at `sprint/context/context-epic-162.md`. Context includes technical approach and the five acceptance criteria (typed Origin unification, id-keyed dedup/purge/seating, alias ledger, identity-fork elimination via integration tests, OTEL spans on identity derivation).
- **Branch:** `feat/162-2-identity-by-id-typed-origin` created in sidequest-server off `origin/develop` per repos.yaml gitflow strategy.
- **Sprint YAML:** Story marked `in_progress` (started 2026-07-05) via pf CLI.
- **Workflow routing:** `tdd` is phased (setup → red → green → review → finish); next agent is **tea** for the RED phase.

No blockers. Ready for handoff to tea.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-point p1 refactor of identity semantics across four production seams; tdd workflow.

**Test Files:**
- `sidequest-server/tests/game/test_162_2_origin_model.py` — AC1/AC2: `OriginKind` (six creation families), `Origin` model shape (kind required, extra=forbid), `normalize_name` (the ONE normalization), `identity_key` equality properties (id-keyed where an id exists, normalized-name floor, authored dominates), `derive_origin` legacy mapping (derive-don't-migrate; stamped wins), `Npc.origin`/`NpcPatch.origin` storage + JSON round-trip + legacy-save load, materializer carry-through + monotonic merge, and four creation-path stamping wiring tests (authored preload, encounter/room-bound/region-population patch builders).
- `sidequest-server/tests/game/test_162_2_identity_resolution.py` — AC2/AC3/AC5: `resolve_roster_npc` (canonical > alias > invented_from, one normalization, canonical outranks another entity's alias, blank/miss → None), `SPAN_IDENTITY_RESOLVED` = "identity.resolved" pinned + emitted on alias/invented_from hits only (attrs query/canonical/via), alias-ledger invariant (accretion via existing `accrete_npc_aliases` leaves `identity_key` bit-identical).
- `sidequest-server/tests/server/test_162_2_identity_fork_seating.py` — AC2/AC3/AC4/AC5 integration on the REAL production seams: alias-named actor seats the canonical creature with no stub (and keeps its own statted HP per the 108-2 rule), casefold variant doesn't mint a twin, 108-2 conscription RECORDS the router name in the creature's alias ledger (+ `entity.alias_accreted` span) and the recorded alias resolves + re-seats with no second identity (the two-turn fork-kill), the genuinely-novel stub still mints loud + ephemeral and is stamped `EPHEMERAL_STUB`, and `inject`'s authored-vs-procedural dedup keys on creature_id under display-name drift (with an over-merge negative guard).

**Tests Written:** 53 tests covering 5 ACs (2 commits: 3bc47c37, 6763f134)
**Status:** RED (verified by testing-runner: 52 failed / 1 intentional pass; full suite still collects, 14,922 tests)

**RED-state notes for Dev (Naomi):**
- 45 failures are `ModuleNotFoundError: sidequest.game.origin` (net-new module) + `origin` field rejections on `Npc`/`NpcPatch` (extra=forbid) — the contract surface.
- 7 failures are behavioral asserts on the live seams (stub minted beside the alias-named creature, case-fork twin, dropped router name, name-keyed inject dedup).
- `test_span_name_pinned` fails with ImportError on `SPAN_IDENTITY_RESOLVED` — that IS the RED signal for the AC5 constant (imported inside the test; collection survives). Not suite breakage.
- `test_distinct_creature_ids_both_materialize` PASSES by design — it is the over-merge paranoia negative guard and must keep passing after GREEN.
- The full contract (module surface, derivation table, resolution order, span semantics) is spelled out in each file's docstring — the test IS the spec.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 no silent fallbacks/swallowing | `test_origin_requires_kind` (no default provenance), `test_minted_stub_...` (lie-detector span must keep firing) | failing (RED) |
| #3 type annotations at boundaries | Contract pins typed signatures (`Origin`, `resolve_roster_npc`); all test fns annotated | failing (RED) |
| #6 test quality | Phase-C self-check done: no vacuous assertions; one pass-in-RED strengthened (6763f134); negative guard labeled | done |
| #8 deserialization trusts schema | `test_legacy_npc_json_without_origin_key_loads_as_none`, `test_origin_rejects_undeclared_fields` (model_validate, extra=forbid) | failing (RED) |
| #10 import hygiene | Net-new symbols imported inside tests (collection survives); no star imports | done |

**Rules checked:** 5 of 13 lang-review rules applicable to test-design scope have coverage; the rest (#2,4,5,7,9,11,12,13) target implementation code and bind on Dev's diff.
**Self-check:** 1 vacuous-in-RED test found and strengthened (commit 6763f134); 0 removed.

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement `sidequest.game.origin`, stamp the creation paths, wire the seater/inject/resolver seams, add `SPAN_IDENTITY_RESOLVED` (+ SpanRoute), and see the two non-blocking Gaps in Delivery Findings (mention-path + pool-member legs).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/origin.py` — NET-NEW: `OriginKind` (StrEnum, six creation families), `Origin` (pydantic, kind required, extra=forbid), `normalize_name`, `identity_key`, `derive_origin` (stamped wins; legacy derive-don't-migrate), `resolve_roster_npc` (canonical > alias > invented_from; emits `identity.resolved` on alias/invented_from hits with query/canonical/via/identity_key attrs)
- `sidequest/game/session.py` — `Npc.origin` + `NpcPatch.origin` fields (None default, lossless legacy load); `_npc_from_patch` carries the stamp; `_merge_npc_patch` is monotonic (first stamp wins, origin-less patch never clears)
- `sidequest/game/world_materialization.py` — authored preload stamps `AUTHORED` + `AuthoredNpc.id`
- `sidequest/server/dispatch/monster_manual_inject.py` — four builders stamp (`MANUAL_POOL` ×2, `ROOM_BOUND`, `REGION_POPULATION`); `_patch_identity_key` helper; inject dedup keys on identity_key AND normalized name (see Dev deviation #1)
- `sidequest/server/dispatch/encounter_lifecycle.py` — hp_depletion seeder seats via `resolve_roster_npc` (live per actor); 108-2 conscription records the router name via `accrete_npc_aliases` (fork closed durably); fabricated stub stamped `EPHEMERAL_STUB`
- `sidequest/telemetry/spans/npc.py` — `SPAN_IDENTITY_RESOLVED` = "identity.resolved" + SpanRoute (component npc_registry, op identity_resolved) — closes TEA's routing Gap

**Tests:** 53/53 story tests passing; full suite 14,582 passed / 0 failed / 341 skipped (testing-runner run 162-2-dev-green); post-polish re-verify 171 tests (story + touched seams) 0 failures. Ruff clean + formatted on story files; pyright adds 0 new errors vs baseline (19 pre-existing on touched files, stash-compared).
**Branch:** feat/162-2-identity-by-id-typed-origin (pushed; commits 3bc47c37, 6763f134, d9022f86)

**Note for Chrisjen (review):** the testing-runner helper applied one production hunk during verification (the dedup name-leg) — reviewed, comment corrected, kept; flagged in Delivery Findings. TEA's `SPAN_IDENTITY_RESOLVED` routing Gap is closed in this diff; the mention-path/pool-member/Fate-seeder resolver adoptions are deliberately deferred (findings + deviations logged).

**Handoff:** To review phase (Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by reviewer's own trace (found the [HIGH] actor-name resolvability break) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain self-covered: found the silent HP-bar drop at websocket_session_handler.py:202 on unresolvable actor names |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 3, deferred 2, dismissed 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 4, dismissed 1 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain self-covered: Origin model typing sound (required kind, extra=forbid, StrEnum); no stringly regressions found |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain self-covered: no boundary input, no injection surface, no tenant concept in this codebase (personal project, N/A) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain self-covered: no over-engineering found; one narrow-footprint observation (derive_origin) folded into findings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 2, deferred 1 |

**All received:** Yes (4 enabled returned; 5 disabled via settings, domains self-covered)
**Total findings:** 9 confirmed, 3 dismissed (with rationale), 3 deferred

**Dismissals (rationale):**
- [TEST] span-name pin test redundant (low) — dismissed: harmless one-line rename guard, costs nothing, matches the 84-2 precedent (`test_span_name_pinned` in test_alias_accretion.py).
- [TEST] second-different-stamp merge case (low) — dismissed as blocking material: the monotonic guard `if npc.origin is None` provably cannot overwrite (session.py:1957); logged as optional hardening in findings for TEA.
- [DOC] legacy-field cross-references (low) — dismissed as blocking material: nice-to-have doc polish, folded into the doc-fix bundle below.

**Deferrals:**
- [TEST] unicode/diacritic distinctness tests — deferred INTO the [RULE] normalize_name finding (same root cause; one fix).
- [TEST] creature_type-falsy stamping branch — deferred to TEA's discretion in rework (low).
- [RULE] `_patch_identity_key` speculative MANUAL_POOL fabrication — deferred: documented, functionally inert for the dedup decision (identity_key ignores .kind), exercised by tests; noted as a forward landmine in findings.

## Rule Compliance

Rule-checker ran all 13 lang-review checks + 6 CLAUDE.md principles exhaustively over every changed function/class/field (61 instances): checks #1–#13 all pass (verified by execution: ruff clean, pyright error-set byte-identical to develop, 53/53 story + 1168/1168 related tests). CLAUDE.md principles: No Silent Fallbacks — pass (Origin.kind required, no default; merge monotonicity documented); No Stubbing — pass (all six symbols fully implemented); Verify Wiring — pass with one observation (all new symbols have production callers; `derive_origin`'s only production caller is the resolver's span attribute — acceptable now, the 162-3 arbiter is its intended consumer); OTEL Principle — pass (SPAN_IDENTITY_RESOLVED registered + routed, fires on derivations only); No Source-Text Wiring Tests — pass (real seams + span capture only). **One violation confirmed:** Don't Reinvent — `normalize_name` duplicates `sidequest/foundation/slug_fold.py:fold_to_ascii` with less capability (no diacritic folding), see [RULE] finding.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [EDGE] | Alias/case-variant seating leaves `EncounterActor.name` unresolvable: the seeder resolves the npc via `resolve_roster_npc` but never canonicalizes the seat name, breaking its own documented invariant ("the opponent core is reachable via `snapshot.find_creature_core(name)`", encounter_lifecycle.py:340-345). Pre-162-2 this invariant ALWAYS held (exact match or stub named exactly actor.name). Consequences: opponent silently vanishes from HP bars (websocket_session_handler.py:202 filter), `query_encounter`/payload core resolution misses (query_encounter.py:126), WN attack on the seat name returns not_found (wn_tools.py:236-237). The `_resolve_opponent_from_roster` head-check change (encounter_lifecycle.py:1168) makes it worse: an alias of a co-located creature previously went through conscription and got seated CANONICALLY; now it early-returns None and seats the dangling alias. All three new seeder tests pin the half-behavior (roster size) without pinning core reachability. | sidequest/server/dispatch/encounter_lifecycle.py:375, :1168 | On a resolver hit where `npc.core.name != actor.name`, rewrite the seat to the canonical name (`actor.name = npc.core.name`), mirroring 108-2 conscription; the alias stays in the ledger for prose. Failing test first: seat by alias, assert `snapshot.find_creature_core(actor.name) is not None` (and the HP-bar predicate at websocket_session_handler.py:202 keeps the actor). Cover the head-check path too. |
| [MEDIUM] [RULE] | `normalize_name` reinvents the existing shared normalization with LESS capability: `fold_to_ascii` (sidequest/foundation/slug_fold.py) already exists and is used by the ADJACENT alias seam (`alias_resolution.py`) precisely to close the diacritic split-brain. An ADR-091 culture name ("Veyra Solnë") won't resolve against an ASCII prose reference ("Veyra Solne") — the exact bug class this story exists to kill, reintroduced in the module claiming to be "THE single normalization." Don't Reinvent violation — cannot be dismissed. | sidequest/game/origin.py:65-69 | Compose `fold_to_ascii` into `normalize_name` (fold + casefold + whitespace collapse); add diacritic resolution + distinctness tests. |
| [MEDIUM] [TEST] | `identity.resolved`'s SPAN_ROUTES extract lambda is untested: every sibling npc.* route has a `test_on_end_emits_typed_event_for_*` test in tests/server/test_watcher_events.py driving WatcherSpanProcessor.on_end; this one has none — a key typo in the extract would ship silently and blind the GM panel (OTEL lie-detector principle). | sidequest/telemetry/spans/npc.py:56-67 | Add the on_end typed-event test per the established pattern (component=npc_registry, op=identity_resolved, query/canonical/via/identity_key round-trip). |
| [MEDIUM] [TEST] | The id-leg negative guard is vacuous for its stated purpose: `test_distinct_creature_ids_both_materialize` uses patches whose display names ALSO differ, so reverting the entire id-keyed dedup still passes it — it re-proves pre-existing name dedup, not the new mechanism. | tests/server/test_162_2_identity_fork_seating.py:397 | Unit-test `_patch_identity_key` distinctness for distinct creature_ids directly, and/or annotate the integration test honestly. |
| [MEDIUM] [TEST] | Ambiguous-alias collision undefined and untested: two npcs carrying the SAME alias (or invented_from) resolve by accidental roster order with no signal — the story's failure mode shifted one level, not closed. | sidequest/game/origin.py:150-158 | Pin deterministic first-in-roster-order resolution in a test; consider a collision attribute on the identity.resolved span. |
| [LOW] [DOC] | Docstring overclaims: (a) `Npc.origin`/origin.py module docstring claim `pool_origin` is unified — `derive_origin` never reads it and `Origin` has no field for it (see Reviewer deviation audit); (b) "Three seams consume this module today" — actual count is four (world_materialization omitted); (c) "the 162-1 derive-don't-migrate pattern" — 162-1's coined term is "derive-don't-cache"; (d) `content_version` docstring implies a live mechanism but no path stamps it. | sidequest/game/origin.py:6-14,62; sidequest/game/session.py:266 | Correct all four in the rework commit; state explicitly that pool_origin remains a separate promotion-tracking field and content_version is reserved. |
| [LOW] [SIMPLE] | `derive_origin`'s only production caller is the resolver's own span attribute — narrower footprint than the module docstring advertises. Acceptable: the 162-3 arbiter is its intended consumer; do not expand scope now. | sidequest/game/origin.py:170 | Docstring nuance only (optional). |
| [LOW] [SILENT] | `_patch_identity_key` fabricates `Origin(kind=MANUAL_POOL)` for unstamped creature patches — documented and functionally inert today (identity_key ignores kind; all four builders stamp), but a future fifth builder that forgets to stamp would be silently papered over rather than failing loud. | sidequest/server/dispatch/monster_manual_inject.py:82-89 | Optional hardening note for 162-3; no change required now. |

**Verified good (evidence + rule compatibility):**
- [VERIFIED] [TYPE] `Origin` model: `kind` is required with no default (origin.py:53; `test_origin_requires_kind` proves ValidationError) and `extra="forbid"` (origin.py:51) — complies with No Silent Fallbacks; StrEnum kinds serialize as plain strings for the ADR-115 JSON blob (round-trip test passes).
- [VERIFIED] [TYPE] The origin.py↔session.py cycle is broken correctly: `Npc` imported under TYPE_CHECKING only (origin.py:25-29), same sanctioned pattern as npc_pool.py; runtime import graph is acyclic (smoke-imported).
- [VERIFIED] [SEC] No security surface: no new boundary input, no SQL/eval/exec/subprocess, in-process name strings only (rule-checker #8/#11 pass, 61 instances). Tenant isolation N/A — no tenant concept in this single-operator codebase.
- [VERIFIED] [SILENT] Conscription alias recording fails loud paths preserved: the minted-stub lie-detector span still fires (test_minted_stub_is_stamped_ephemeral_stub_origin drives the real seam), and the 153-9/150-2 decline spans are untouched (118 seam tests pass).
- [VERIFIED] [SIMPLE] Reuse-first held at the ledger: conscription records via the EXISTING `accrete_npc_aliases` (encounter_lifecycle.py:1263-1271) with its idempotent casefold dedup + `entity.alias_accreted` span — no parallel alias system was invented.
- [VERIFIED] [DOC] The "RED today" test docstrings match repo convention (~50 merged GREEN suites keep TDD narrative; sibling test_opponent_roster_resolution.py checked) — not stale.
- [VERIFIED] [EDGE] Merge monotonicity: `_merge_npc_patch` cannot clear or overwrite a stamp (session.py:1953-1958 guard `npc.origin is None and patch.origin is not None`); mirrors the story-72-3 manual_origin OR-merge one line above.

**Data flow traced:** router `threat_name` → `_resolve_opponent_from_roster` (resolver head check → conscription + alias record) → `EncounterActor` seat → `_seed_combat_hp_depletion_to_npcs` (resolver lookup → HP seed on canonical npc) → combat resolution reads core via `snapshot.find_creature_core(actor.name)` — **the trace breaks at the last hop on alias-named seats**, which is the [HIGH].
**Pattern observed:** good — TYPE_CHECKING cycle-break + derive-don't-migrate mirrors npc_pool.py and 162-1 (origin.py:25-29); bad — seat-name canonicalization done in one path (conscription) but not the other (direct seeder resolution).
**Error handling:** `Origin()` without kind raises (validated); blank/unknown resolver queries return None with no span spam; no new swallowed exceptions (rule-checker #1: zero).

### Devil's Advocate

Assume this diff is broken and I'm the one who has to run Sunday's session on it. The party recorded "The Pale King" as the Vellum Ghast's alias last week. Tonight Keith types "I attack the Pale King." The router names the threat, the head check resolves the alias, seats it directly, and the seeder dutifully finds the ghast and tops up its HP — and then the encounter panel shows a fight with no opponent HP bar, because the overlay filter resolves `actor.name` ("The Pale King") through `find_creature_core` exact-match and silently drops it. The narrator's attack tool returns "unknown target." From the table this looks like the pre-162-2 bug got WORSE: before, at least a hollow stub fought back. The story that promised "two names, one enemy" shipped "one name, zero enemies" on its own showcase path — and every test passed, because the tests measured roster arithmetic, not reachability. Second angle: Jade's perseus world mints "Veyra Solnë" via the culture namer; the player types "Veyra Solne." casefold doesn't fold diacritics; the resolver misses; the seater mints a stub twin — the exact double-mint this module's own docstring cites as its origin story, alive and well one seam over from where `fold_to_ascii` was built to kill it. Third angle: two different cultists both nicknamed "the Butcher" — the resolver binds whichever entered the roster first, silently, and the GM panel span happily asserts the binding as truth. The lie-detector can now confidently report a lie. All three of these came out of this section and all three are in the findings table — the first two are why this is a rejection, not an approval with notes.

**Handoff:** Back through the rework loop — findings are testable (logic bug + missing edge cases) → red rework → Amos (tea) writes the failing tests, Naomi (dev) fixes.

## TEA Assessment (rework round 1)

**Tests Required:** Yes — reviewer REJECTED with testable findings.
**Reason:** [HIGH] seat-name reachability + [MEDIUM] diacritic folding are logic bugs; three more [MEDIUM]s are coverage gaps.

**Rework tests (commit d8196eda; RED verified by testing-runner run 162-2-tea-red-rework1 — 5 failed / 58 passed, originals clean):**
- `tests/server/test_162_2_identity_fork_seating.py::TestSeatNameCanonicalization` (3 RED) — alias seat, case-variant seat, and instantiate-with-recorded-alias-threat must all leave the `EncounterActor` named canonically with `snapshot.find_creature_core(actor.name)` reachable (the HP-bar predicate asserted verbatim). Fix-agnostic: passes whether Dev canonicalizes in the seeder, the head check, or both — but the direct-seeder tests force at least the seeder-level rewrite.
- `tests/game/test_162_2_origin_model.py::test_diacritics_fold_to_ascii_base` (RED) + `test_diacritic_fold_preserves_distinctness` (guard) and `tests/game/test_162_2_identity_resolution.py::test_resolves_diacritic_name_from_ascii_query` (RED) — normalize_name composes `foundation.slug_fold.fold_to_ascii`.
- Labeled green-on-arrival CONTRACT GUARDS (must stay green): `TestPatchIdentityKeyUnit` (2 — id-leg isolation the integration negative couldn't provide), `test_shared_alias_resolves_first_in_roster_order` (deterministic tiebreak pinned both directions), `test_on_end_emits_typed_event_for_identity_resolved_span` (SPAN_ROUTES extract lambda driven through WatcherSpanProcessor.on_end).

**Not tested, Dev-owned per review:** the [LOW] doc-fix bundle (pool_origin overclaim + explicit exclusion decision, seam count, 162-1 term, content_version note) — docstrings, no test surface. Reviewer's `creature_type`-falsy and second-different-stamp suggestions assessed and skipped: both are guarded by existing behavior proofs (identity_key ignores kind; merge guard provably can't overwrite) — declining per minimal-suite discipline, noted here for transparency.

**Deviations:** No new deviations in rework round 1.
**Handoff:** To Dev (Naomi) — make the 5 RED green, keep the guards green, land the doc fixes.

## Dev Assessment (rework round 1)

**Implementation Complete:** Yes
**Files Changed (commit a29486b4):**
- `sidequest/server/dispatch/encounter_lifecycle.py` — seat canonicalization at BOTH seams: the hp_depletion seeder rewrites `actor.name` to the canonical core name on a resolver hit, and `instantiate_encounter_from_trigger` canonicalizes `materialized_threat` through `resolve_roster_npc` before conscription. The two-seam fix was forced by the tests: the fixture pack's combat is a dial confrontation, so the head-check test proved the seeder-level rewrite alone can't cover non-hp_depletion paths. Rebinds are observable via the resolver's `identity.resolved` span.
- `sidequest/game/origin.py` — `normalize_name` composes `foundation.slug_fold.fold_to_ascii` (fold → casefold → whitespace collapse); module docstring corrected (pool_origin documented as deliberate exclusion per reviewer audit, four seams, derive-don't-cache attribution, content_version marked RESERVED).
- `sidequest/game/session.py` — `Npc.origin` docstring corrected (no pool_origin overclaim; explicit exclusion note).

**Tests:** 83/83 story + watcher tests passing; full suite **14,592 passed / 0 failed / 341 skipped** (testing-runner run 162-2-dev-green-rework1). All rework contract guards green. Ruff clean.
**Branch:** feat/162-2-identity-by-id-typed-origin (pushed; rework commits d8196eda, a29486b4)

**Review-finding disposition:** [HIGH] fixed (both seams + reachability tests); [MEDIUM] normalize_name fixed (fold_to_ascii reuse); [MEDIUM] on_end routing test added (green); [MEDIUM] id-leg guard + alias-ambiguity determinism pinned; [LOW] doc bundle landed. pool_origin: documented-exclusion option taken (per reviewer's either/or), stated in both docstrings.

**Handoff:** Back to review (Chrisjen) for re-verdict.

## Subagent Results

*(Review round 2 — rework delta d9022f86..a29486b4)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 | confirmed 1 (format-only nit; its "maintainer preference" framing dismissed — it is plain unformatted code, verified by ruff format --diff) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain self-covered: re-traced both canonicalization seams; NpcMention field-drop chased and refuted (ship-scale filter runs pre-rebind) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — rule-checker's reproduction covered the domain (participant.joined pre-rename telemetry gap, confirmed) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 2, deferred 1, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — no type-surface changes in the delta beyond docstrings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — no boundary input in the delta |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — delta is minimal; no over-engineering observed |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 2 (1 with empirical reproduction) |

**All received:** Yes (4 enabled returned; 5 disabled via settings, domains self-covered)
**Total findings:** 7 confirmed, 2 dismissed (with rationale), 1 deferred

**Dismissals:** preflight's "maintainer formatting preference" framing (it is ordinary unformatted code — confirmed via ruff format --diff; the underlying nit is CONFIRMED as [LOW]); test-analyzer's diacritic-distinctness weak-pair note (low, the exact-value strengthening folds into the follow-up bundle).
**Deferrals:** case-variant head-check coverage (low — the seeder-side case test + shared resolver make an isolated regression at the second call site unlikely; bundled in follow-up).
**Reviewer self-correction:** my own [LOW] on the NpcMention field-drop was REFUTED by two independent traces (test-analyzer + rule-checker: no consumer reads the dropped flags downstream of the rebind; ship-scale filter runs before it) — downgraded to the latent-pattern note the rule-checker logged.

## Rule Compliance

*(Round 2, delta-scoped)* Rule-checker ran all 13 checks over 27 instances: #1–#12 pass (typed signatures on all 10 new test methods; None-sentinel defaults; correct monkeypatch targets; no new logging/path/resource/deserialization/async surface; fold_to_ascii import is cycle-free; the local NpcMention re-import matches the file's established convention). #13 (fix-introduced regressions): one confirmed telemetry-ordering finding — `participant.joined` and the init-span `combatant_names` compute BEFORE the seeder rename on the explicit-`npcs_present` path, so they log the stale alias with missing stamp attrs; game state, final actors, and reachability verified correct by reproduction (`enc.actors` canonical; `identity.resolved` + `npc.edge_published` correct). CLAUDE.md principles: Don't Reinvent — CLOSED (fold_to_ascii genuinely reused, 4th consumer); Verify Wiring — pass (both canonicalization sites production-reachable via confrontation.py:156 / dogfight.py:144); OTEL — pass with the noted ordering gap; the case-variant no-span behavior is a documented design distinction (normalization ≠ derivation), not a silent fallback.

## Reviewer Assessment

*(Round 2 verdict)*

**Verdict:** APPROVED

**Round-1 finding closure — all verified:**
- [EDGE] [HIGH → CLOSED] Seat canonicalization landed at BOTH seams (seeder actor.name rewrite encounter_lifecycle.py:408; head-check rebind :1796) — verified by the three reachability tests, by rule-checker's independent reproduction (final `enc.actors` canonical, `find_creature_core` reachable, correct `identity.resolved` + `npc.edge_published` spans), and by the full suite (14,592 passed / 0 failed).
- [RULE] [MEDIUM → CLOSED] `normalize_name` now composes `fold_to_ascii` — genuine reuse confirmed (4th consumer of the shared primitive), diacritic tests pass, distinctness preserved.
- [TEST] [MEDIUM → CLOSED] `identity.resolved` routing pinned through a real `WatcherSpanProcessor.on_end` drive; id-leg isolation unit-pinned (same-name/different-id keys apart — only the id leg can produce that); shared-alias roster-order determinism pinned both directions. Test-analyzer verified the contract guards genuinely passed at the pre-fix commit — honest guards, not theater.
- [DOC] [LOW → CLOSED] pool_origin documented as deliberate exclusion (both docstrings, matching the reviewer-audit either/or); four-seam count accurate (spot-checked); derive-don't-cache attribution corrected; content_version marked RESERVED and verified unstamped everywhere.

**New findings this round (none blocking — Medium/Low per severity doctrine):**
| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [MEDIUM] [TEST] | Mutation-confirmed: all three canonicalization tests use a single-entry roster, so "canonicalize to the npc the resolver matched" vs "canonicalize to whatever is in the roster" are indistinguishable — a wrong-npc rename would pass. Add a decoy npc per test and assert the SPECIFIC creature. | tests/server/test_162_2_identity_fork_seating.py:435+ | Non-blocking; filed as delivery finding for the epic follow-up bundle (production behavior verified correct by reproduction; this hardens the regression net). |
| [LOW] [RULE] [SILENT] | `participant.joined` + init-span `combatant_names` compute pre-rename on the explicit-npcs_present path — GM panel sees the stale alias for one event while later spans show canonical (reproduced). Game state correct; presence re-stamped by the seeder. | encounter_lifecycle.py:2075-2124 | Non-blocking observability polish; filed as delivery finding. |
| [LOW] [DOC] | New head-check comment overclaims: the case-variant rebind emits NO `identity.resolved` span (canonical-leg hits don't span by design); and "edge publish" resolves via its own by-name dict, not `find_creature_core`. Two comment lines. | encounter_lifecycle.py:1791-1793 | Non-blocking; follow-up bundle. |
| [LOW] [SIMPLE] | Format-only: one test file collapses under `ruff format` (3 call sites) — run the formatter before/at merge so the next story's diff stays clean (today's 49-file sweep is the cautionary tale). | tests/server/test_162_2_identity_fork_seating.py:442,492,502 | Non-blocking; flagged to Drummer for the finish flow. |
| [LOW] [TYPE] | NpcMention manual field-copy in the rebind drops is_new/is_creature/disengaged/is_place — INERT today (verified by two independent traces; ship-scale filter runs pre-rebind) but a latent trap; `dataclasses.replace(...)` is the robust form. | encounter_lifecycle.py:1800-1805 | Non-blocking; follow-up bundle. |

**Verified good:** [VERIFIED] [SEC] no new boundary surface in the delta (rule-checker #8/#11: zero instances). [VERIFIED] [TEST] no vacuous assertions in the 10 new tests (#6 clean, every assert value-specific). [VERIFIED] [SILENT] no new swallowed exceptions (#1: zero); the case-variant no-span path is documented design, not silence.

**Data flow traced (round 2):** alias-named threat → head-check rebind (canonical NpcMention) → conscription head sees canonical → seat → seeder resolver (already canonical, no-op rename) → HP seed → `find_creature_core(actor.name)` resolves → HP bars/WN attack/query_encounter all reachable. The round-1 break is closed at both entry points.
**Pattern observed:** good — both fixes reuse `resolve_roster_npc` (one resolution semantics everywhere) rather than adding a third matching dialect; the fix-forced-by-fixture moment (dial-path pack exposing the seeder-only fix as insufficient) is TDD working as intended.
**Error handling:** unchanged surface; `Origin` validation and blank-query guards intact.

### Devil's Advocate

*(Round 2 — argue the rework is still broken.)* Try to break it: seat two enemies where one's alias equals the other's canonical name — the resolver's whole-roster canonical-first pass answers deterministically, and the ambiguity tiebreak is now a pinned contract, so the GM panel at least never sees a random flip. Try the mutation the tests can't see: rename-to-wrong-npc — the suite passes, which is exactly why the decoy-roster finding is filed; what keeps it from being a blocker is that three independent verifications (my trace, the rule-checker's span-level reproduction, 14,592-test regression) agree today's code resolves to the RIGHT npc, so the gap is in the net, not the fish. Try telemetry: watch the GM panel during an alias-named npcs_present combat — `participant.joined` briefly lies about the name before `identity.resolved` corrects the record; annoying, reproducible, filed — but the lie-detector family itself (minted_stub, alias_accreted, identity.resolved, edge_published) now tells a coherent canonical story where round 1 shipped an unreachable opponent. Try Unicode: "Straße"/"strasse" casefold-collides and NFKD won't split them — a German-named NPC pair could merge; ADR-091 corpora are Latin-diacritic-heavy, `ł/ø/þ` pass through unfolded (slug_fold documents this), so the residual collision surface is narrow and now shared with the alias seam rather than unique to this module. The honest verdict: the blocking defects are demonstrably closed, the residue is hardening, and the residue is written down where the next story can't lose it.

**Handoff:** To Drummer (SM) for finish — run `ruff format tests/server/test_162_2_identity_fork_seating.py` as part of branch preparation (format-only, no re-review needed), create the PR, merge, finish ceremony.