---
story_id: "159-3"
jira_key: ""
epic: "159"
workflow: "tdd"
---
# Story 159-3: Server companion bond + perception seam

## Story Details
- **ID:** 159-3
- **Jira Key:** (not enabled)
- **Workflow:** tdd
- **Stack Parent:** none (independent story)
- **Branch Strategy:** gitflow (feat/159-3-server-companion-bond-perception-seam)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T22:09:52Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T20:57:04Z | 2026-06-25T20:59:18Z | 2m 14s |
| red | 2026-06-25T20:59:18Z | 2026-06-25T21:14:37Z | 15m 19s |
| green | 2026-06-25T21:14:37Z | 2026-06-25T21:25:27Z | 10m 50s |
| review | 2026-06-25T21:25:27Z | 2026-06-25T21:42:11Z | 16m 44s |
| green | 2026-06-25T21:42:11Z | 2026-06-25T21:59:12Z | 17m 1s |
| review | 2026-06-25T21:59:12Z | 2026-06-25T22:09:52Z | 10m 40s |
| finish | 2026-06-25T22:09:52Z | - | - |

## Story Context

**Points:** 3  
**Type:** Feature  
**Epic:** 159 — Companion Seat — full-PC AI companion over WS  
**Repo:** sidequest-server  

### User Story
As a player, I want the server to recognize a seat as a companion bonded to me and scope its perception by type, so that a bonded pet shares my private view while a hireling sees only what's observable.

### Acceptance Criteria
- **Given** the SESSION_EVENT connect handshake can carry companion metadata
- **When** the bond registry, connect-handler registration, and fan-out pet-widening are added per Plan B
- **Then** a pet receives owner-private NARRATION_SEGMENT/SECRET_NOTE and a hireling does not, unknown relationships fail closed, and `companion.bond_resolved` + `companion.routed_as_pet` OTEL spans fire — proven by a firewall wiring test.

### Key Technical Anchors
- **Implementation plan:** docs/superpowers/plans/2026-06-25-companion-B-server-bond-seam.md (the authoritative task list — bond registry, connect-handler registration, fan-out pet-widening)
- **Design spec:** docs/superpowers/specs/2026-06-25-companion-seat-design.md
- **Epic breakdown:** docs/superpowers/plans/2026-06-25-companion-epic-breakdown.md (Story 1.3 section)
- **Existing infra to wire into (do NOT reimplement):** the engine's perception firewall / broadcast-layer perception (ADR-104 Perception Filtering at the Tool Layer, ADR-105 Broadcast-Layer Perception Firewall), MP item attribution (ADR-108), and the disposition/OCEAN machinery (ADR-020, ADR-042).

### Critical Project Rules to Surface
- **No Silent Fallbacks:** unknown relationships MUST fail closed (loud), never silently widen perception.
- **OTEL Observability Principle:** this subsystem MUST emit `companion.bond_resolved` and `companion.routed_as_pet` spans so the GM panel can verify the seam is engaged — the firewall wiring test asserts this.
- **Every Test Suite Needs a Wiring Test:** the AC explicitly demands a firewall wiring test proving end-to-end perception scoping, not just unit coverage.

## Sm Assessment

**Readiness:** Ready for RED phase. Story is fully specified in the epic breakdown (Story 1.3) and has a dedicated authoritative implementation plan (Plan B). No blocking dependencies — 159-3 is explicitly independent of 1.1/1.4/1.5, so it can be built in isolation. Merge gate clear (only open PR is an unrelated dependabot bump).

**Scope (server-only):** Three seams from Plan B — (1) a companion **bond registry** resolving seat→owner relationships, (2) **connect-handler registration** so the SESSION_EVENT handshake carries and records companion metadata, (3) **fan-out pet-widening** in the broadcast layer so a `pet` inherits its owner's private view (NARRATION_SEGMENT/SECRET_NOTE) while a `hireling` does not.

**What TEA (Amos) must drive in RED — write failing tests that pin:**
- Pet inherits owner-private NARRATION_SEGMENT/SECRET_NOTE; hireling is denied the same.
- **Fail-closed invariant** (No Silent Fallbacks): an unknown/unresolvable relationship must raise loudly and widen *nothing* — assert the loud failure, not a silent default.
- **OTEL spans** `companion.bond_resolved` and `companion.routed_as_pet` are emitted on the resolution/fan-out paths.
- **Firewall wiring test** (mandatory per AC + project rule): proves the seam is reachable end-to-end through the real broadcast/perception path — not just unit-level. This is the load-bearing test; do not let it degrade into a mock-only unit.

**Wire, don't reinvent:** Bind into the existing perception firewall (ADR-104/105), item attribution (ADR-108), and disposition/OCEAN machinery (ADR-020/042). Flag in Delivery Findings if any of those seams aren't where the plan expects them.

**Routing:** Phased TDD → next agent **tea** (Amos Burton) for RED.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `emitters.py` has no module-level `_watcher_publish` — it imports it function-locally from `session_handler` (lines 65/468) to avoid an emitters↔session_handler import cycle. The `expand_visibility_for_companions` helper must emit `companion.routed_as_pet` via that **same function-local** `from sidequest.server.session_handler import _watcher_publish` pattern (NOT a module-level import — cycle risk). Affects `sidequest/server/emitters.py` (helper's span emit). The RED tests patch the alias on both `emitters` and `session_handler` with `raising=False`, so either resolution works — but the function-local form is the in-repo convention. *Found by TEA during test design.*
- **Gap** (non-blocking): the helper also needs `json` resolvable in its scope; `json` is currently a function-local import in `emit_event` (line 421), not module-level. A module-level `import json` in `emitters.py` is cycle-safe. Affects `sidequest/server/emitters.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the widening helper must key on `VISIBILITY_GATED_KINDS` membership (covers both `NARRATION_SEGMENT` AND `SECRET_NOTE`, per the AC) — do not hardcode `NARRATION_SEGMENT`. RED tests pin SECRET_NOTE explicitly (registry-level and through the real firewall). Affects `sidequest/server/emitters.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): Plan B's sample test code constructs `SessionRoom()` and `view=GameStateView()`, both of which `TypeError` against the live API (`SessionRoom` requires `slug`+`mode`; `GameStateView` is a `typing.Protocol`). RED tests use `SessionRoom(slug=..., mode=GameMode.SOLO)` and `SessionGameStateView()`. Dev/Reviewer: keep these forms; do not "simplify" back to the plan's sketch. Affects test scaffolding only; production interfaces unchanged. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): the full server suite has a pre-existing baseline of ~10 failures unrelated to this story — all die at `sidequest/game/monster_manual_inject.py:184` (`effective_bestiary(sd.world_slug or "")` → `ValueError: not enough values to unpack`) in the pre-narration monster-injection path. Independently confirmed orthogonal to the companion change (the emit fan-out helper is never reached in those tests). Affects `sidequest/game/monster_manual_inject.py` (bestiary resolution returns 0 values for some world slugs). Not in this story's blast radius. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `pyright` reports ~76 pre-existing strictness errors across `connect.py`/`emitters.py`/`session_room.py` (possibly-unbound `view`/`_snapshot_for_swap`, `str | None`→`str` arg mismatches). Verified none fall in the lines this story added — the companion code is pyright-clean. Affects those three files (latent type-strictness debt). *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): `companion.bond_resolved` publishes the owner's Cf-Access email (`owner_identity`) into persisted+broadcast telemetry, contradicting `bind_player_identity`'s no-PII convention and lang-review #4. Affects `sidequest/handlers/connect.py:294` (drop the identity value from the span). *Found by Reviewer during code review.*
- **Gap** (blocking): no test guards the production wiring — the labeled wiring test bypasses `emit_event`, so the AC's "proven by a firewall wiring test" is unmet at the call site. Affects `tests/server/test_companion_perception_wiring.py` (add a fixture-driven `emit_event`/`_project_frames` test). *Found by Reviewer during code review.*
- **Gap** (non-blocking): identity-spoofing is out-of-scope per spec ("cooperative-local v1; owner-consent deferred", spec:67/359) — a future v2 story MUST add owner-consent/bond-authority before `companion_of` can be trusted in multi-human sessions, since an attacker-controlled `companion_of` would widen them into a victim's private view. Affects the companion connect path (v2 owner-consent gate). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): pet-widening is live-only; a reconnecting pet replays canonical (un-widened) visibility and won't re-receive owner-private history. Affects `sidequest/server/emitters.py` (v2 reconnect parity). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_companion_bonds` is not cleaned on companion disconnect (unlike `_player_identities`), leaving stale pet bonds that produce phantom recipients. Affects `sidequest/server/session_room.py:538` disconnect path. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, re-review): the Layer-2 production-path wiring test asserts the pet is included but not that the owner remains included; add `assert decides.get("p_owner") is True` to catch a hypothetical replace-instead-of-extend regression (current code copies-then-appends, so not a defect). Affects `tests/server/test_companion_perception_wiring.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, re-review): the bound-rejection tests assert the over-limit failure but not the valid-boundary (254/32) pass; and the SECRET_NOTE composition test checks 3 seats vs the narration test's 5. Affects `tests/protocol/test_session_event_companion_fields.py` + `tests/server/test_companion_perception_wiring.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, re-review): `bind_companion_bond` docstring "behaves as a non-widening hireling" conflates the no-widen outcome with registry state (an unknown relationship is unregistered + resolved=False, unlike a registered hireling). Affects `sidequest/handlers/connect.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 1 Conflict, 0 Question, 1 Improvement)
**Blocking:** 2 BLOCKING items — see below

**BLOCKING:**
- **Conflict:** `companion.bond_resolved` publishes the owner's Cf-Access email (`owner_identity`) into persisted+broadcast telemetry, contradicting `bind_player_identity`'s no-PII convention and lang-review #4. Affects `sidequest/handlers/connect.py:294`.
- **Gap:** no test guards the production wiring — the labeled wiring test bypasses `emit_event`, so the AC's "proven by a firewall wiring test" is unmet at the call site. Affects `tests/server/test_companion_perception_wiring.py`.

- **Improvement:** pet-widening is live-only; a reconnecting pet replays canonical (un-widened) visibility and won't re-receive owner-private history. Affects `sidequest/server/emitters.py`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`sidequest/handlers`** — 1 finding
- **`sidequest/server`** — 1 finding
- **`tests/server`** — 1 finding

### Deviation Justifications

6 deviations

- **Corrected Plan B's sample test-harness constructions against the live API**
  - Rationale: the plan's forms raise TypeError/AttributeError against the real code (SessionRoom requires slug+mode; GameStateView is a Protocol; emitters._watcher_publish is function-local) — RED must fail only on the missing feature, not on harness bugs
  - Severity: minor
  - Forward impact: none — production interfaces unchanged; corrections are confined to test scaffolding
- **Expanded coverage beyond the plan's sample tests (SECRET_NOTE, PEER, span fields, fail-safes)**
  - Rationale: Plan B's samples exercised only NARRATION_SEGMENT and the PET/HIRELING split; the AC explicitly names SECRET_NOTE, PEER is a third role whose non-widening is a fail-closed invariant, and span-name-only assertions don't prove the GM panel can attribute the routing
  - Severity: minor
  - Forward impact: none — additive coverage; constrains the helper to widen by VISIBILITY_GATED_KINDS membership (which Plan B's helper already does)
- **emitters helper uses function-local imports + TYPE_CHECKING annotations, not Plan B's bare module-level names**
  - Rationale: `emitters.py` has no module-level `_watcher_publish`/`json`/`MessageEnvelope` — they're function-local everywhere to avoid the emitters↔session_handler import cycle. Bare module-level names would NameError. Honors TEA's Delivery Finding and keeps the OTEL-span monkeypatch contract intact.
  - Severity: minor
  - Forward impact: none — behavior identical; import placement only
- **Registry methods are lock-guarded; `parse_companion_relationship` rejects empty string explicitly**
  - Rationale: `_companion_bonds` is written on the connect thread and read at fan-out; locking matches the class's existing identity-dict convention. `if not raw` makes the empty-string case fail closed explicitly (behaviorally identical — `CompanionRelationship("")` would have raised → None anyway — but clearer and asserted by `parse_companion_relationship("") is None`).
  - Severity: minor
- **(Rework) logger.warning() added at the handler, not in the pure parser**
  - Rationale: the parser is a pure, reusable utility — its `None` return is a documented contract value, not an error, and the caller owns the decision to log. The rejection EVENT is logged once, at the boundary, where context exists. Double-logging the same rejection would be noise.
  - Severity: minor
- **(Rework) owner_identity dropped from the bond span entirely (not hashed)**
  - Rationale: minimal fix matching the `bind_player_identity` precedent (source-only, no value). Owner correlation already rides `companion.routed_as_pet` (server-minted player_ids, no PII); a hash would be unused complexity now.
  - Severity: minor
  - Forward impact: none — a future GM-panel grouping need can add a salted token then.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Corrected Plan B's sample test-harness constructions against the live API**
  - Spec source: docs/superpowers/plans/2026-06-25-companion-B-server-bond-seam.md, Tasks 1/3/4/5 sample test code
  - Spec text: "room = SessionRoom()", "view=GameStateView()", and `monkeypatch.setattr("sidequest.server.emitters._watcher_publish", ...)`
  - Implementation: tests use `SessionRoom(slug=..., mode=GameMode.SOLO)`, `SessionGameStateView()`, and patch `_watcher_publish` on both `emitters` and `session_handler` (`raising=False`)
  - Rationale: the plan's forms raise TypeError/AttributeError against the real code (SessionRoom requires slug+mode; GameStateView is a Protocol; emitters._watcher_publish is function-local) — RED must fail only on the missing feature, not on harness bugs
  - Severity: minor
  - Forward impact: none — production interfaces unchanged; corrections are confined to test scaffolding
- **Expanded coverage beyond the plan's sample tests (SECRET_NOTE, PEER, span fields, fail-safes)**
  - Spec source: context-story-159-3.md Acceptance Criteria; SOUL.md "No Silent Fallbacks"
  - Spec text: "a pet receives owner-private NARRATION_SEGMENT/SECRET_NOTE and a hireling does not, unknown relationships fail closed"
  - Implementation: added SECRET_NOTE widening + firewall-wiring tests; PEER-does-not-widen tests (registry/connect/expand/wiring); `companion.routed_as_pet` field assertions (pet_player_id/owner_player_id/kind); a pet-without-resolved-owner-identity fail-safe; empty/blank-relationship fail-closed tests; a no-duplicate-recipient test
  - Rationale: Plan B's samples exercised only NARRATION_SEGMENT and the PET/HIRELING split; the AC explicitly names SECRET_NOTE, PEER is a third role whose non-widening is a fail-closed invariant, and span-name-only assertions don't prove the GM panel can attribute the routing
  - Severity: minor
  - Forward impact: none — additive coverage; constrains the helper to widen by VISIBILITY_GATED_KINDS membership (which Plan B's helper already does)

### Dev (implementation)
- **emitters helper uses function-local imports + TYPE_CHECKING annotations, not Plan B's bare module-level names**
  - Spec source: docs/superpowers/plans/2026-06-25-companion-B-server-bond-seam.md, Task 4 Step 3; session Delivery Findings (TEA)
  - Spec text: helper calls bare `_watcher_publish(...)` and `json.loads(...)` and notes "no top-level import change is required beyond the existing json import"
  - Implementation: `expand_visibility_for_companions` imports `json`, `MessageEnvelope` (as `_Envelope`), `VISIBILITY_GATED_KINDS`, and `_watcher_publish` **inside the function body**; `SessionRoom`/`MessageEnvelope` added to the `TYPE_CHECKING` block for the signature
  - Rationale: `emitters.py` has no module-level `_watcher_publish`/`json`/`MessageEnvelope` — they're function-local everywhere to avoid the emitters↔session_handler import cycle. Bare module-level names would NameError. Honors TEA's Delivery Finding and keeps the OTEL-span monkeypatch contract intact.
  - Severity: minor
  - Forward impact: none — behavior identical; import placement only
- **Registry methods are lock-guarded; `parse_companion_relationship` rejects empty string explicitly**
  - Spec source: docs/superpowers/plans/2026-06-25-companion-B-server-bond-seam.md, Task 1 Steps 4/6
  - Spec text: lock-free `register_companion_bond`/`companion_owner_identity`/`pets_of`; parser guards `if raw is None`
  - Implementation: the three registry methods wrap dict access in `with self._lock:` (matching `set_player_identity`/`get_player_identity`); the parser guards `if not raw` (covers `None` and `""`)
  - Rationale: `_companion_bonds` is written on the connect thread and read at fan-out; locking matches the class's existing identity-dict convention. `if not raw` makes the empty-string case fail closed explicitly (behaviorally identical — `CompanionRelationship("")` would have raised → None anyway — but clearer and asserted by `parse_companion_relationship("") is None`).
  - Severity: minor
  - Forward impact: none
- **(Rework) logger.warning() added at the handler, not in the pure parser**
  - Spec source: Reviewer finding [MEDIUM][RULE] (lang-review #4) — flagged both `parse_companion_relationship` (session_room.py:137) and `bind_companion_bond` (connect.py:294)
  - Spec text: "add logger.warning() on the two fail-closed paths"
  - Implementation: added `logger.warning(...)` only in `bind_companion_bond`'s resolved=False branch (with player_id + relationship context); left `parse_companion_relationship` log-free
  - Rationale: the parser is a pure, reusable utility — its `None` return is a documented contract value, not an error, and the caller owns the decision to log. The rejection EVENT is logged once, at the boundary, where context exists. Double-logging the same rejection would be noise.
  - Severity: minor
  - Forward impact: none
- **(Rework) owner_identity dropped from the bond span entirely (not hashed)**
  - Spec source: Reviewer finding [HIGH][SEC]
  - Spec text: "publish player_id + resolved + a non-PII indicator"
  - Implementation: removed `owner_identity` from the `companion.bond_resolved` fields; did not substitute a hashed token
  - Rationale: minimal fix matching the `bind_player_identity` precedent (source-only, no value). Owner correlation already rides `companion.routed_as_pet` (server-minted player_ids, no PII); a hash would be unused complexity now.
  - Severity: minor
  - Forward impact: none — a future GM-panel grouping need can add a salted token then.

### Reviewer (audit)
- **TEA — "Corrected Plan B's sample test-harness constructions"** → ✓ ACCEPTED: correct against the live API (`SessionRoom` requires slug+mode; `GameStateView` is a Protocol). Pre-empted real TypeErrors. Sound.
- **TEA — "Expanded coverage (SECRET_NOTE, PEER, span fields, fail-safes)"** → ✓ ACCEPTED for the coverage expansion (SECRET_NOTE/PEER are genuinely valuable). → ✗ FLAGGED sub-decision: the dual-patch (`emitters` + `session_handler` `_watcher_publish`, raising=False) bakes in a permanent dead no-op patch on `emitters` — the docstring's "robust to whichever import site" is false. See [MEDIUM][TEST] dead-patch finding; fix in rework.
- **Dev — "emitters helper uses function-local imports + TYPE_CHECKING annotations"** → ✓ ACCEPTED: correct emitters↔session_handler cycle avoidance; matches the established in-file convention.
- **Dev — "Registry methods lock-guarded; `parse_companion_relationship` rejects empty string"** → ✓ ACCEPTED: lock matches the class's identity-dict convention; `if not raw` is behaviorally equivalent and clearer.
- **UNDOCUMENTED (Reviewer-spotted):** (1) `owner_identity` (PII) published into the `companion.bond_resolved` telemetry event — not logged as a deviation; it contradicts the `bind_player_identity` no-PII convention. See [HIGH][SEC]. (2) Pet-widening is live-fan-out-only — the EventLog persists canonical (un-widened) visibility (emitters.py:556), so reconnect-replay does not re-widen to pets. Reasonable for a transient companion but undocumented; flagged Low + v2 Delivery Finding.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — a 3-pt feature story with a behavioral AC and two mandated OTEL spans.

**Test Files:** (all in `sidequest-server`, committed `1b1b9f04`)
- `tests/server/test_companion_bond_registry.py` — bond registry: PET resolves owner+pets, HIRELING/PEER do not widen, fail-safe on unresolved owner identity, exact-match-or-None parse (Task 1)
- `tests/protocol/test_session_event_companion_fields.py` — `SessionEventPayload.companion_of`/`relationship` fields; unknown relationship is transport-opaque (Task 2)
- `tests/handlers/test_companion_bond_connect.py` — `bind_companion_bond` registers a pet + emits `companion.bond_resolved` (resolved=True); unknown/empty relationship fails closed (resolved=False) but still emits; PEER registered-but-no-view; non-companion / blank `companion_of` no-op (Task 3)
- `tests/server/test_companion_visibility_expand.py` — `expand_visibility_for_companions`: widens NARRATION_SEGMENT **and** SECRET_NOTE to bonded pets + emits `companion.routed_as_pet` with pet/owner/kind fields; hireling/peer/unresolved-owner not widened; "all" sentinel & non-gated kinds & None room untouched; no duplicate recipient (Task 4)
- `tests/server/test_companion_perception_wiring.py` — **load-bearing wiring test**: pet receives owner-private NARRATION_SEGMENT and SECRET_NOTE through the REAL `ComposedFilter`→`CoreInvariantStage` pipeline; hireling/peer/stranger excluded; span observable (Task 5)

**Tests Written:** 27 tests covering the compound AC's 7 sub-clauses (pet sees NARRATION_SEGMENT+SECRET_NOTE · hireling doesn't · unknown fails closed · `companion.bond_resolved` fires · `companion.routed_as_pet` fires · firewall wiring test · SESSION_EVENT carries metadata).
**Status:** RED — verified by testing-runner: 4 ImportError-at-collection (missing `CompanionRelationship`/`bind_companion_bond`/`expand_visibility_for_companions`) + 3 protocol failures (extra-forbid ValidationError / AttributeError on `companion_of`). **No harness bugs** — none of Plan B's three ctor/patch traps fired.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks — unknown relationship fails CLOSED + LOUD | `test_unknown_relationship_fails_closed_and_emits_span`, `test_empty_relationship_fails_closed_and_emits_span`, `test_parse_relationship_exact_match_or_none` | failing |
| No Silent Fallbacks — non-PET roles never widen | `test_peer_is_not_widened`, `test_hireling_is_not_widened`, `test_pet_with_unresolved_owner_identity_is_not_widened` | failing |
| OTEL Observability — `companion.bond_resolved` fires w/ relationship+resolved | `test_pet_bond_registered_and_span_emitted`, `test_peer_bond_registered_but_grants_no_owner_view` | failing |
| OTEL Observability — `companion.routed_as_pet` fires w/ pet/owner/kind | `test_pet_added_to_owner_private_narration_segment`, `test_pet_added_to_owner_private_secret_note` | failing |
| Every Test Suite Needs a Wiring Test (real pipeline) | `test_pet_receives_owner_private_narration_through_real_firewall`, `test_pet_receives_owner_private_secret_note_through_real_firewall` | failing |
| No Source-Text Wiring Tests (fixture+OTEL, no source grep) | wiring file uses real `ComposedFilter` + span assertion | satisfied |

**Rules checked:** 6 of 6 applicable rules (the story's load-bearing rules are No Silent Fallbacks + OTEL + wiring; lang-review #1 silent-swallow and #6 test-quality are the relevant Python-checklist items) have test coverage.
**Self-check:** 0 vacuous tests — every assertion checks a specific value (`is True/False`, exact `set(...)`, field equality, identity `is env`); no `assert True`, no bare truthy `assert result`.

**Handoff:** To Dev (Naomi Nagata) for implementation — make these RED tests GREEN per Plan B, honoring the Delivery Findings (function-local `_watcher_publish`/`json` in the emitters helper; widen by `VISIBILITY_GATED_KINDS` membership; keep the corrected `SessionRoom`/`SessionGameStateView` test forms).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:** (all `sidequest-server`, committed + pushed)
- `sidequest/server/session_room.py` — `CompanionRelationship` enum + `parse_companion_relationship` (fail-closed); `_companion_bonds` field; lock-guarded `register_companion_bond` / `companion_owner_identity` / `pets_of` (PET-only widening)
- `sidequest/protocol/messages.py` — `SessionEventPayload.companion_of` + `.relationship` (connect-handshake metadata)
- `sidequest/handlers/connect.py` — `bind_companion_bond` (registers the bond + emits `companion.bond_resolved`; resolved=False+warning on unknown relationship), wired into `ConnectHandler.handle` after `room.connect`
- `sidequest/server/emitters.py` — `expand_visibility_for_companions` (widens owner-private NARRATION_SEGMENT/SECRET_NOTE `visible_to` to bonded pets + emits `companion.routed_as_pet`; firewall untouched), wired into `emit_event` at envelope-build time

**Tests:** 27/27 passing (GREEN) — `test_companion_bond_registry` (6), `test_session_event_companion_fields` (3), `test_companion_bond_connect` (6), `test_companion_visibility_expand` (9), `test_companion_perception_wiring` (3 incl. SECRET_NOTE).
**Quality:** ruff clean; pyright clean on the new code (the ~76 baseline errors verified outside the added line ranges). Regression sweep `-k "projection or emit or invariant or session_room or session_event"`: 1454 passed; the only 10 failures are the pre-existing `monster_manual_inject.py:184` baseline (unrelated — see Delivery Findings).
**Branch:** `feat/159-3-server-companion-bond-perception-seam` (pushed, tracking origin).

**AC verification:** pet receives owner-private NARRATION_SEGMENT+SECRET_NOTE ✓ · hireling does not ✓ · unknown relationships fail closed (No Silent Fallbacks) ✓ · `companion.bond_resolved` + `companion.routed_as_pet` spans fire ✓ · proven by the real-pipeline firewall wiring test ✓ · SESSION_EVENT carries companion metadata ✓.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (orphan method) + smells clean | confirmed 1 (orphan), dismissed 1 (function-local json — documented pattern) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge/boundary analysis done by Reviewer |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — fail-closed/silent analysis done by Reviewer (see Rule Compliance #1/#14) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 5, downgraded 1 (wiring-gap → Medium after adjudicating vs rule-checker) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 (both Low/doc) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type analysis done by Reviewer (annotations clean, see Rule Compliance #3) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — SECURITY analysis done by Reviewer (PII + input-bound + spoofing-scope; this is a perception-security story) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity done by Reviewer (orphan method) |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 3 (logger #4 ×2 → Medium w/ OTEL mitigation, companion_of bound #11 → Medium) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled as Skipped)
**Total findings:** 8 confirmed blocking-or-fix (1 High, 7 Medium), 6 Low, 2 dismissed/downgraded

## Reviewer Findings & Observations

- **[HIGH][SEC] PII leaked into telemetry** — `bind_companion_bond` publishes `owner_identity` (a Cf-Access email) into the `companion.bond_resolved` watcher event at `connect.py:294`. That event is broadcast to the GM dashboard AND persisted via `publish_event`→`_persist_turn_telemetry`. The sibling `bind_player_identity` (connect.py:258-259) deliberately emits "the SOURCE only — never the identity value (no PII in telemetry)." Violates that explicit convention + lang-review #4 ("Never log sensitive data: PII"). Impact is low in v1 cooperative-local (owner_identity = operator's own Host) but real in any MP/Cf-Access session. **Blocking.** Fix: drop `owner_identity` from the span (publish player_id + resolved + a non-PII indicator). Test-safe — no test asserts `owner_identity` is in the span.
- **[MEDIUM][TEST] The "wiring test" does not guard the production wiring.** `tests/server/test_companion_perception_wiring.py` calls `expand_visibility_for_companions(...)` and `ComposedFilter.project(...)` directly; it never drives `emit_event`. Delete the production call at `emitters.py:658` and all 27 tests stay green. The AC says "proven by a firewall wiring test," and CLAUDE.md requires the test verify the component is "reachable from production code paths." (Adjudicated against rule-checker, which marked it compliant for being a real-component behavioral test — it is a real *composition* test, but not a *call-site* wiring test.) Fix: a fixture-driven test that drives `emit_event`/`_project_frames` with a pet-bonded room and asserts the pet's outbound queue received the owner-private frame (precedent: `test_confrontation_single_delivery.py`). [TEST, test-analyzer, high]
- **[MEDIUM][TEST] Dead monkeypatch target.** `monkeypatch.setattr("sidequest.server.emitters._watcher_publish", sink, raising=False)` in `test_companion_visibility_expand.py:23` and `test_companion_perception_wiring.py:26` patches a non-existent attribute (emitters imports `_watcher_publish` function-locally). `raising=False` silently no-ops it; only the `session_handler` patch fires. The module docstring's "robust to whichever import site" is false — there is one site. Remove the emitters patch, keep `session_handler`. [TEST + DOC, corroborated by test-analyzer + comment-analyzer, high]
- **[MEDIUM][TEST] `_capture_spans` discards the `severity` kwarg.** The fail-closed tests (`test_unknown_relationship_fails_closed`, `test_empty_relationship_fails_closed`) assert `resolved is False` but cannot assert `severity == "warning"` — the loud-signal that distinguishes a rejected bond from a normal grant. A regression emitting `severity="info"` for rejections passes. Capture and assert it. [TEST, test-analyzer, medium]
- **[MEDIUM][TEST] Missing hireling case in the connect dispatch test** and **tautological exclusion tests.** `bind_companion_bond` is tested for pet/peer/unknown but not hireling (registered, resolved=True, no view). And `test_hireling_is_not_widened`/`test_peer_is_not_widened` assert `out.payload_json == env.payload_json`, satisfiable by a no-op widener with no span assertion. Add the hireling dispatch test + a "no `routed_as_pet` span" assertion. [TEST, test-analyzer, medium]
- **[MEDIUM][RULE] No `logger.warning()` on the two fail-closed paths** — `parse_companion_relationship` ValueError branch (session_room.py:137) and `bind_companion_bond` resolved=False (connect.py:294). Both modules import logging; lang-review #4 wants an error-path logger line. Mitigated (the OTEL warning span IS the loud signal per the project's OTEL mandate), so Medium not High — but add the logger lines for log-aggregator visibility. [RULE, rule-checker, high→medium w/ mitigation]
- **[MEDIUM][SEC/RULE] `companion_of` is unbounded at the connect API boundary** (messages.py:364) — no `Field(max_length=...)`, stored verbatim in `room._companion_bonds` and published to telemetry. lang-review #11 (validate input at boundaries); the codebase bounds Fate aspects (`Field(max_length=200)`, messages.py:576). Partially mitigated (sibling fields player_name/genre/world are also unbounded). Bound it (e.g. `max_length=254`, RFC-5321 email). [RULE, rule-checker, high→medium] `relationship` is fine — enum-gated before storage.
- **[MEDIUM][SIMPLE] `companion_owner_identity` is an orphan** (session_room.py:748) — zero non-test consumers (verified across docs/understudy/server); the fan-out uses `pets_of`. Violates "Verify Wiring, Not Just Existence / non-test consumers." Remove it (the connect tests use it as the registration observable — switch them to `pets_of`), or name a same-epic consumer. [SIMPLE, preflight + Reviewer, low→medium]
- **[LOW] Live-only widening.** The EventLog persists the *canonical* (un-widened) `payload_json` at append (emitters.py:556) before widening; the pet-widening affects the live frame only. A reconnecting pet replays canonical visibility and won't re-receive owner-private history. Correct-by-design for a transient companion, but a latent gap for v2 reconnect. [EDGE, Reviewer]
- **[LOW] Stale bonds on disconnect.** `_player_identities` is popped on the owner's last-socket close (session_room.py:572) but `_companion_bonds` is never cleaned. A disconnected pet's bond lingers → `pets_of` returns a stale pet_pid → a phantom recipient that triggers `_emit_recipient_dropped` warnings. Ephemeral room (process lifetime) bounds it; not a security issue. [EDGE, Reviewer]
- **[LOW][DOC] Two comment nits** (comment-analyzer): the test docstring over-claims "both patches"; `bind_companion_bond`'s "behaves as a non-widening hireling" is imprecise (an unknown relationship is NOT registered, unlike a real hireling bond which IS). [DOC]
- **[VERIFIED][SILENT] Fail-closed is correct and loud, not silent** — every non-pet path refuses to widen: `parse_companion_relationship` returns None for unknown/empty/None (session_room.py:133-138) → no bond registered; `pets_of` returns [] for no-identity/non-PET (session_room.py:756-767); `expand_visibility` returns the envelope unchanged for `room is None` / non-gated kind / non-list `visible_to` (emitters.py:103-108). The unknown path emits a `companion.bond_resolved` span at `severity="warning"` — observable, per No Silent Fallbacks. Evidence traced end-to-end. [SILENT — Reviewer, security subagent disabled]
- **[VERIFIED][TYPE] Annotations and types are clean** — all six new functions/fields fully annotated; `CompanionRelationship(StrEnum)` is the right newtype (exact-match parse, not stringly-typed); `_companion_bonds: dict[str, tuple[str, CompanionRelationship]]` is precise; pyright clean on new code (verified line ranges). [TYPE — Reviewer, type-design subagent disabled]
- **[VERIFIED][SEC] Identity-spoofing is OUT OF SCOPE by documented design** — an attacker connecting with `companion_of="victim@email"` + `relationship="pet"` WOULD be widened into the victim's private view, but the spec explicitly defers owner-consent: "No owner-consent/multi-tenant bond authority in v1 (cooperative local use)" (spec:67), "Trust model: cooperative-local only in v1" (spec:359). Not a finding against this story; captured as a v2 Delivery Finding. [SEC — Reviewer]

### Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md/SOUL.md (corroborated by rule-checker over 58 instances):

| Rule | Verdict | Evidence |
|------|---------|----------|
| #1 Silent exception swallowing | PASS | `parse_companion_relationship` catches `ValueError` specifically + documented fail-closed + caller emits warning span (session_room.py:135-138) |
| #2 Mutable default args | PASS | all 6 symbols use no defaults / `field(default_factory)` / Pydantic None |
| #3 Type annotations at boundaries | PASS | all new functions + fields fully annotated |
| #4 Logging coverage | **FAIL (Medium)** | no `logger.warning()` on the two fail-closed paths (session_room.py:137, connect.py:294) — OTEL-mitigated. **PII: `owner_identity` (email) in span = FAIL (High).** |
| #5 Path handling | N/A | no path ops |
| #6 Test quality | PARTIAL | assertions are specific (no vacuous), BUT dead patch + dropped severity + tautological hireling/peer tests (see findings) |
| #7 Resource leaks | PASS | `with self._lock:` used throughout |
| #8 Unsafe deserialization | PASS | `json.loads(payload_json)` is server-generated event data, guarded by isinstance checks (emitters.py:105-108) |
| #9 Async pitfalls | PASS | all new code synchronous; no blocking I/O in async handler |
| #10 Import hygiene | PASS | no star imports; function-local imports are documented cycle-avoidance |
| #11 Input validation at boundary | **FAIL (Medium)** | `companion_of` unbounded (messages.py:364); `relationship` enum-gated (PASS) |
| #12 Dependency hygiene | N/A | no dep changes |
| No Silent Fallbacks (SOUL) | PASS | unknown → closed + warning span; no path widens on unknown/malformed |
| OTEL Observability (CLAUDE) | PASS | `companion.bond_resolved` + `companion.routed_as_pet` both fire; the PII issue is *what's in* the span, not whether it fires |
| Verify Wiring / non-test consumers | PARTIAL | feature wired (emitters.py:658, connect.py:509) BUT no test guards the call site; `companion_owner_identity` has no production consumer |

### Devil's Advocate

Argue this code is broken. **Privacy:** the moment a second human joins a session and a companion bonds to them, `bind_companion_bond` writes that human's Cf-Access email into the persisted telemetry table and broadcasts it to every GM-dashboard subscriber. The author knew this was wrong — the function three lines up goes out of its way to publish "the SOURCE only." This is not hypothetical: ADR-119 authenticated identity is partially live, and `companion.bond_resolved` fires on every companion connect regardless of trust model. **Resource abuse:** `companion_of` is an unbounded string from an API boundary. A cooperative-but-careless (or compromised) client can send a multi-megabyte `companion_of`; it's `.strip()`ed and stored verbatim as a dict key-value in the long-lived `SessionRoom`, then serialized into every `companion.bond_resolved` telemetry row. Nothing bounds it. **The wiring is a lie of omission:** the suite advertises a "load-bearing wiring test," but a maintainer who deletes the single production call at `emitters.py:658` during an unrelated refactor sees 27 green tests and ships a dead feature — pets silently stop seeing owner-private narration, and no alarm fires. The OTEL `companion.routed_as_pet` span would simply never emit, which no test asserts at the production path. **The fail-closed signal is half-built:** the rejection path emits `severity="warning"`, but no test pins that severity and no `logger.warning()` exists, so a regression that downgrades rejections to `severity="info"` (making malicious/malformed bonds look normal on the GM panel) passes every test and leaves no log trace. **Stale state:** a pet that disconnects and reconnects leaves an orphaned bond; `pets_of` then names a dead player_id as a recipient, and the firewall dutifully includes a ghost, generating recipient-dropped warnings forever. **What a confused maintainer breaks:** the two dead `emitters._watcher_publish` patches invite someone to "clean up the redundant session_handler patch," which silently kills every span assertion. None of these are showstoppers for a cooperative-local v1 demo — but each is exactly the class of defect this project's rules were written to stop, and the PII leak alone clears the bar to send it back.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][SEC] | PII (owner Cf-Access email) published into persisted+broadcast `companion.bond_resolved` watcher event — violates `bind_player_identity` "no PII in telemetry" convention + lang-review #4 | connect.py:294 | Drop `owner_identity` from the span fields; publish player_id + resolved + non-PII indicator only (mirror `bind_player_identity`) |
| [MEDIUM][TEST] | "Wiring test" bypasses `emit_event`; deleting emitters.py:658 keeps all tests green — AC "proven by a firewall wiring test" unmet at the production path | tests/server/test_companion_perception_wiring.py | Add a fixture-driven `emit_event`/`_project_frames` test asserting a pet-bonded room delivers the owner-private frame to the pet's queue |
| [MEDIUM][TEST] | Dead `emitters._watcher_publish` monkeypatch (no-op) + false "both patches" docstring | test_companion_visibility_expand.py:23, test_companion_perception_wiring.py:26 | Remove emitters patch; keep `session_handler` patch; fix the comment |
| [MEDIUM][TEST] | `_capture_spans` drops `severity` — fail-closed tests can't assert `severity="warning"` | test_companion_bond_connect.py | Capture+assert severity on the resolved=False tests |
| [MEDIUM][TEST] | Missing hireling dispatch test; `test_hireling/peer_is_not_widened` no-op-satisfiable | test_companion_bond_connect.py, test_companion_visibility_expand.py | Add hireling dispatch case + a "no `routed_as_pet` span" assertion |
| [MEDIUM][RULE] | No `logger.warning()` on the two fail-closed paths (lang-review #4) | session_room.py:137, connect.py:294 | Add `logger.warning()` alongside the OTEL span |
| [MEDIUM][RULE] | `companion_of` unbounded at the connect API boundary (lang-review #11) | messages.py:364 | `Annotated[str, Field(max_length=254)] \| None` |
| [MEDIUM][SIMPLE] | `companion_owner_identity` orphan — no non-test consumer | session_room.py:748 | Remove (switch connect tests to `pets_of`) or name a consumer |

**Data flow traced:** WebSocket `SESSION_EVENT{connect, companion_of, relationship}` → `ConnectHandler.handle` → `bind_companion_bond` (parse → register PET bond / fail-closed + `companion.bond_resolved` span) → later `emit_event` → `expand_visibility_for_companions` widens owner-private `visible_to` to bonded pets + `companion.routed_as_pet` span → `CoreInvariantStage` includes the pet by membership. The *logic* is correct and default-closed; the leak is `owner_identity` exiting into telemetry, and the *call-site* wiring is untested.

**Tags present:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]

**Handoff:** Back to TEA (Amos Burton) for red rework — the dominant cluster is test-design (production-path wiring test, dead patch, dropped severity, missing hireling/exclusion-span coverage, a regression test asserting `owner_identity` absent from the span, a `companion_of` max-length rejection test). Once tests pin the gaps, Dev (green) applies the production fixes (drop the PII span field, add the two `logger.warning()` lines, bound `companion_of`, remove the orphan).

## Dev Assessment — Review Rework (round-trip 1)

**Implementation Complete:** Yes — all 8 reviewer findings addressed. Commit `25b36939` (pushed).

| # | Finding | Resolution |
|---|---------|-----------|
| [HIGH][SEC] | PII (owner email) in `companion.bond_resolved` span | Dropped `owner_identity` from the span (connect.py); publishes `player_id`+`relationship`+`resolved` only, mirroring `bind_player_identity`. Regression guard: `test_pet_bond_registered_and_span_emitted` asserts `"owner_identity" not in fields`. |
| [MEDIUM][TEST] | Wiring test bypassed `emit_event` | Added `test_emit_event_widens_owner_private_segment_to_bonded_pet` — drives the REAL Postgres-backed `emit_event` fan-out, asserts the pet's `projection.filter.decide` is `include=True`. **Verified it FAILS when the emitters.py:658 call site is disabled** (then restored). |
| [MEDIUM][TEST] | Dead `emitters._watcher_publish` patch | Removed from both wiring/expand test files; kept the live `session_handler` target; docstrings corrected. |
| [MEDIUM][TEST] | Dropped `severity` kwarg | `_capture_spans` now captures kwargs; both fail-closed tests assert `severity == "warning"`. |
| [MEDIUM][TEST] | Missing hireling dispatch + tautological exclusion tests | Added `test_hireling_bond_registered_but_grants_no_owner_view`; hireling/peer exclusion tests now assert no `routed_as_pet` span fires. |
| [MEDIUM][RULE] | No `logger.warning()` on fail-closed | Added `logger.warning()` in `bind_companion_bond` resolved=False (handler layer; see deviation re: not double-logging in the pure parser). |
| [MEDIUM][RULE] | `companion_of` unbounded | Bounded `companion_of` (max_length=254) + `relationship` (max_length=32) via `Annotated[str, Field(...)]`; 2 rejection tests added. |
| [MEDIUM][SIMPLE] | `companion_owner_identity` orphan | Removed; registry + connect tests now verify the bond via `pets_of` (the production read path). |

**Tests:** 31 companion tests passing (was 27: +2 protocol bound, +1 hireling dispatch, +1 emit_event wiring; orphan assertions folded into existing `pets_of` checks). ruff clean; no new pyright errors; regression sweep on touched subsystems clean (the only 9 failures are the pre-existing `monster_manual_inject.py:184` baseline).
**Branch:** `feat/159-3-server-companion-bond-perception-seam` (pushed, `25b36939`).

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results — Re-Review (round-trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 31 green, ruff clean, 0 smells, wiring confirmed, orphan removed (0 refs) | N/A — confirms all fixes |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge analysis by Reviewer |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — fail-closed re-verified by Reviewer (rule-checker #17) |
| 4 | reviewer-test-analyzer | Yes | findings | 3 new (1 med, 2 low) | all 6 prior FIXED; 3 new non-blocking test-completeness (deferred) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 residual low | 2 prior nits resolved; 1 residual LOW docstring (deferred) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled — annotations clean (rule-checker #3) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled — PII fix + bounds re-verified by Reviewer (rule-checker #4/#11) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled — orphan removed; no new dead code |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations (5 prior resolved) | N/A — all prior violations resolved |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled as Skipped)
**Total findings:** 0 blocking; 4 non-blocking deferred (1 med + 3 low — test-completeness + 1 doc nit)

## Reviewer Re-Review — Verification of Rework

Every blocking finding from the first review is resolved and independently verified:

- **[HIGH][SEC] PII** — RESOLVED. `owner_identity` is absent from the `companion.bond_resolved` span (connect.py); machine-checked by `assert "owner_identity" not in fields`. (Confirmed by comment-analyzer + rule-checker #4.) The email still lives only in the ephemeral room dict (consistent with `_player_identities`), never in telemetry.
- **[MEDIUM][TEST] Wiring** — RESOLVED. `test_emit_event_widens_owner_private_segment_to_bonded_pet` drives the REAL `emit_event` (Postgres-backed) and asserts the pet's `projection.filter.decide` is `include=True`. Deletion-sensitive: removing the emitters.py:658 call site flips it to exclude (Dev verified manually; test-analyzer + rule-checker #19 confirm the guard is genuine, OTEL-based, not source-grep). [TEST]
- **[MEDIUM][TEST] Dead patch** — RESOLVED. `emitters._watcher_publish` patch removed from all test files; only the live `session_handler` target remains. [TEST]
- **[MEDIUM][TEST] Severity** — RESOLVED. `_capture_spans` captures kwargs; fail-closed tests assert `severity == "warning"`. [TEST]
- **[MEDIUM][TEST] Hireling + exclusion spans** — RESOLVED. `test_hireling_bond_registered_but_grants_no_owner_view` added; hireling/peer exclusion tests assert no `routed_as_pet` span. [TEST]
- **[MEDIUM][RULE] logger.warning** — RESOLVED at the handler. rule-checker #4 explicitly judged logging at `bind_companion_bond` (not the pure parser) ACCEPTABLE. [RULE]
- **[MEDIUM][SEC/RULE] companion_of unbounded** — RESOLVED. `companion_of` (254) + `relationship` (32) bounded via `Annotated[str, Field(max_length=N)]`; rejection tests added. [SEC][RULE]
- **[MEDIUM][SIMPLE] Orphan** — RESOLVED. `companion_owner_identity` removed (0 references anywhere); tests verify via `pets_of`, the production read path. [SIMPLE]

**New non-blocking findings (deferred — captured as Delivery Findings, none are defects):**
- [MEDIUM][TEST] The Layer-2 wiring test asserts `p_pet` included but not `p_owner` still included — redundant with the Layer-1 composition test which already asserts owner inclusion; the helper copies-then-appends and never drops the owner. Deferred. [TEST]
- [LOW][TEST] SECRET_NOTE composition test checks 3 seats vs the narration test's 5; SECRET_NOTE shares the same gated path. [TEST]
- [LOW][TEST] Bound tests assert the over-limit rejection but not the valid-boundary (254/32) pass. [TEST]
- [LOW][DOC] `bind_companion_bond` docstring "behaves as a non-widening hireling" conflates outcome with registry state (unknown = unregistered, resolved=False; hireling = registered, resolved=True). [DOC]
- **[VERIFIED][EDGE]** bond registered before `attach_outbound`/fan-out (connect.py) — correct ordering so `pets_of` is populated before any emit. [EDGE]
- **[VERIFIED][TYPE]** annotations clean; bounds typed via `Annotated[str, Field(...)]`; pyright clean on new code. [TYPE]

### Devil's Advocate (rework)

Could the rework have introduced a regression while fixing the findings? The PII fix removed `owner_identity` from the span — does anything still read it? No: the span's only consumers are tests and the GM panel, and `owner_identity` is still stored in `_companion_bonds` for the actual bond logic, so registration is unaffected. Could dropping it have broken correlation? The `companion.routed_as_pet` span carries `owner_player_id` (server-minted, not PII), so the GM panel can still correlate — no functional loss. Could the new bounds reject legitimate input? `companion_of=254` is the RFC-5321 email max and `relationship=32` dwarfs the three 3–8 char role tokens; a legitimate companion connect fits, and an over-limit value fails the whole connect (fail-closed, the safe direction). Could the orphan removal have left a caller stranded? Grep confirms zero references in production and tests. Could the heavyweight Postgres wiring test be flaky or vacuous? It is deletion-sensitive (proven), uses the established `_pg_isolation`/`migrated_db` pattern shared by 9+ files, and asserts a specific decide-span value — not a truthy check. The one residual risk a malicious actor poses (registering as another human's pet to read their private view) is the documented, out-of-scope v1 cooperative-local trust boundary, already captured as a v2 Delivery Finding. The remaining gaps are test-completeness (owner-still-included in Layer-2, valid-boundary asserts) — none mask a defect in the current code, which is correct on every path I traced. Nothing here rises to blocking.

### Reviewer (audit) — Rework Deviations

- **Dev — "logger.warning() at the handler, not the pure parser"** → ✓ ACCEPTED: rule-checker #4 independently judged this correct design — the rejection event is logged once at the boundary with context; coupling a pure reusable parser to logging would be worse.
- **Dev — "owner_identity dropped entirely (not hashed)"** → ✓ ACCEPTED: minimal fix matching the `bind_player_identity` precedent; correlation rides the no-PII `companion.routed_as_pet` span. A future hash can be added if a GM-panel grouping need arises.

## Reviewer Assessment

**Verdict:** APPROVED
**Data flow traced:** `SESSION_EVENT{connect, companion_of, relationship}` → `bind_companion_bond` (bounded input → exact-match parse → PET bond / fail-closed + `companion.bond_resolved` span, **no PII**) → `emit_event` → `expand_visibility_for_companions` widens owner-private `visible_to` to bonded pets + `companion.routed_as_pet` span → `CoreInvariantStage` includes the pet by membership. Default-closed on every non-PET/unknown/malformed path; spoofing is the documented out-of-scope v1 trust boundary.
**Pattern observed:** widen-before-projection (firewall untouched, only the authorized recipient set grows) at emitters.py:658; lock-guarded identity-keyed bond registry in session_room.py.
**Error handling:** unknown/empty relationship → no bond + `logger.warning` + `resolved=False`/`severity=warning` span; over-bound input → connect rejected; `room is None`/non-gated kind/non-list visibility → envelope unchanged.
**Quality:** 31 tests green; ruff + pyright clean on new code; production-path wiring test is deletion-sensitive; all 8 prior findings resolved; rule-checker 0 violations.
**Tags present:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]
**Handoff:** To SM (Camina Drummer) for finish-story.