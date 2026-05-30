---
story_id: "72-2"
jira_key: ""
epic: "72"
workflow: "tdd"
---
# Story 72-2: Preserve disposition on pool to Npc promotion + reconcile npcs vs npc_pool on load

## Story Details
- **ID:** 72-2
- **Epic:** NPC Identity Hardening (Epic 72)
- **Jira Key:** None (no Jira integration)
- **Workflow:** tdd
- **Points:** 5
- **Priority:** p2
- **Type:** bug
- **Stack Parent:** none

## Context

Perseus_cloud session 894, 2026-05-29 DEEP-DIVE #1: An NPC has no stable id—identity is a case-folded NAME STRING split across two unreconciled stores:

1. **snapshot.npcs** (mechanical state): full Npc with CreatureCore, EdgePool, beliefs, disposition, last_seen tracking
2. **snapshot.npc_pool** (identity scaffold): NpcPoolMember with name, role, pronouns, appearance, no disposition or mechanical state

There are two critical failures:

### Leg 1: Disposition Loss on Pool-to-Npc Promotion

When an NPC is promoted from `npc_pool` to a full `Npc` (via `_promote_pool_member_to_npc` in `narration_apply.py`), the disposition is lost. The function creates a fresh `Npc` with default neutral disposition, even if the pool member has already been cited with developed disposition during the same session.

**Root cause:** `NpcPoolMember` carries no `disposition` field, so the promotion code has no way to preserve it.

**Mechanical impact (per ADR-020 NPC Disposition System):** an NPC's disposition drifts on non-transactional engagement (via the development pipeline, story 72-1). If that NPC is then promoted to mechanical engagement (combat, status mutation), the accumulated disposition delta is discarded and the NPC spawns neutral, losing continuity.

### Leg 2: npcs vs npc_pool Reconciliation on Load

When a save file is loaded:
- `snapshot.npcs` and `snapshot.npc_pool` can contain the same NPC by name (case-folded)
- No reconciliation logic exists; the NPC exists in two stores with potentially divergent state
- No consistency invariant is enforced

**Mechanical impact:** the narrator reads `npc_pool` for identity scaffolding, but the mechanical state in `npcs` is invisible to that lookup; at narration_apply time, a pool member might shadow a mechanically-engaged Npc, or vice versa.

## Acceptance Criteria

### AC 1: NpcPoolMember carries disposition field
- Add `disposition: Disposition = Field(default_factory=Disposition)` to `NpcPoolMember`
- Disposition field is optional in load/serialization (backward-compatible with existing saves)
- Disposition is **not** updated by the NPC development pipeline (that's mechanical state, pipeline only touches `npcs`)
- New story 72-5 will handle disposition defaults for narrator-invented NPCs

### AC 2: Pool-to-Npc promotion preserves disposition
- `_promote_pool_member_to_npc` reads `member.disposition` and passes it to the `Npc` constructor
- If `member.disposition` is default (Disposition()), the promoted NPC spawns with default disposition (existing behavior preserved)
- If `member.disposition` has a non-default value, the promoted NPC preserves that value
- Emit OTEL span `npc.promoted_from_pool` carrying:
  - `npc_name`: the NPC's name
  - `disposition_before`: disposition value from the pool member
  - `disposition_after`: disposition value on the created Npc (should match)
  - `pool_origin`: member.name
- Span is fired **inside** `_promote_pool_member_to_npc`, not at call sites

### AC 3: Reconciliation on load
- Add reconciliation logic in `Session.load()` or an explicit reconciliation function called during load
- **For each NPC in `snapshot.npcs`:**
  - Search `snapshot.npc_pool` by name (case-folded, matching `_apply_npc_mentions` logic)
  - If found: remove the pool member (it's shadowed by the mechanical Npc)
  - Emit OTEL span `npc.pool_reconciliation.shadowed_npc` carrying `npc_name` + `removed_pool_member: bool`
- **For each pool member in `snapshot.npc_pool` with no matching NPC:**
  - Leave it intact (it's a future promotion candidate)
  - Emit OTEL span `npc.pool_reconciliation.orphan_pool_member` carrying `member_name`
- Reconciliation runs **once per load**, not per turn
- Reconciliation is a separate function (`_reconcile_npc_pool_on_load` or similar) wired into the load path

### AC 4: OTEL Wiring Test
- New integration test `test_pool_disposition_preservation.py` drives a synthetic scenario:
  - Mint a narrator-invented pool member via narration
  - Cite it again (development pipeline fires, disposition drifts)
  - Promote it to mechanical engagement (e.g., combat status mutation)
  - Assert the promoted Npc carries the drifted disposition from the pool member
  - Assert the `npc.promoted_from_pool` span fired with matching disposition values
- Separate integration test `test_pool_reconciliation_on_load.py`:
  - Create a snapshot with overlapping npcs + npc_pool entries (same name)
  - Call load/reconciliation
  - Assert orphaned pool members remain; shadowed pool members are removed
  - Assert both reconciliation span types fired with correct attributes

## Delivery Findings

No upstream findings at story intake.

### TEA (test design)
- **Conflict** (non-blocking): The session-file ACs and the story-context ACs disagree on implementation seam, and BOTH partly disagree with the live code. Session AC1 says "add `disposition` field to `NpcPoolMember`"; session AC3 says reconcile in `Session.load()` with shadow/orphan framing. `context-story-72-2.md` (authored with verified line numbers) says the disposition *source* is the implementer's choice and reconcile belongs in `migrate_legacy_snapshot` raw-dict space, with `Npc` authoritative for disposition. The live promotion fn already carries a **Story 72-5** comment ("a pool member carries no disposition, so promotion spawns it neutral") and emits `npc_spawn_disposition_span`. Tests were written to the **behavior** both specs share (round-trip preservation, reconcile-to-single-source, OTEL on both legs) against the **verified context-story seams**. Dev: see Design Deviations → TEA for the exact choices and where they may diverge.
- **Question** (non-blocking): The reconcile OTEL attribute names (`s5_pool_shadowed_removed`, `s5_disposition_conflicts`) are a TEA-proposed contract mirroring the existing `s2_*` count style. If Dev prefers a dedicated NPC reconcile span over folding into `snapshot.canonicalize` (context-story sanctions either), the AC5b assertions in `test_pool_reconciliation_on_load.py` must move to that span. Affects `tests/game/test_pool_reconciliation_on_load.py` (span-name + attr-name assertions). *Found by TEA during test design.*
- **Improvement** (non-blocking): `_migrate_s5_reconcile_npc_pool` depends on running **after** `_migrate_s2_npc_registry_split` (it reconciles against the post-split pool). The dependency is documented in the docstring + tuple comment but not runtime-enforced. A future tuple reorder would silently reconcile against a pre-split pool on legacy `npc_registry` saves. Not fixed here: a fail-loud guard (`if "npc_registry" in out: raise`) is *new behavior* (needs a test, belongs in TDD not the verify simplify-pass) and would be inconsistent with the existing un-guarded S1–S4 ordering. Candidate for a follow-up hardening story if migration ordering ever proves fragile. Affects `sidequest/game/migrations.py`. *Found by TEA during test verification (simplify-quality flag, triaged).*

### Dev (implementation)
- **Improvement** (non-blocking): `Disposition` was a documented value type without `__eq__`/`__hash__`; added now so models carrying it compare by value. Worth an audit of other "value type" wrappers in `sidequest/game/` for the same gap. Affects `sidequest/game/disposition.py` (done) and potentially sibling wrappers. *Found by Dev during implementation.*
- **Question** (non-blocking): A new `spawn_disposition` provenance value `carried_from_pool` was introduced (see Dev deviation). Any GM-panel/telemetry consumer that enumerates provenance values should add it. Affects GM-panel disposition-provenance display (UI, out of this story's scope). *Found by Dev during implementation.*
- **Confirmation:** The 2 full-suite failures (`test_pack_validator` content + crossref) are **pre-existing** — verified failing on the clean base with all 72-2 changes stashed (missing image-asset directories + unknown trope ids; pure content, no overlap with the Python seams this story touched).
- No blocking upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `_migrate_s5_reconcile_npc_pool` should mirror `_migrate_s2_npc_registry_split`'s corrupt-input observability — add an `int`-guard when reading `npc`/`member` disposition in raw-dict space and an `s5_malformed_pool_members_skipped` count for non-dict pool entries, so the lie-detector counts stay accurate on legacy/corrupt saves (today a corrupt disposition can inflate `s5_disposition_conflicts`, and a non-dict pool member is kept uncounted). All valid-data paths are already correct; corrupt paths fail loud at validation. Affects `sidequest/game/migrations.py:334,343,351-352`. Convergent finding (silent-failure-hunter, security, edge-hunter). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Test coverage gaps in correct code — no test for (a) shadow removal where member disposition is present and *equal* to the Npc (false-arm of the conflict guard), (b) *multiple* shadowed members in one pass (count vs boolean), (c) a non-dict pool entry surviving reconcile, (d) the `carried_from_pool` provenance branch. Affects `tests/game/test_pool_reconciliation_on_load.py`, `tests/integration/test_pool_disposition_preservation.py`. These should accompany the hardening above. *Found by Reviewer during code review.*
- **Gap** (non-blocking, OUT OF SCOPE — pre-existing): `world_materialization.py:502` `existing.disposition = int(npc_data.disposition)` assigns a raw int to the typed `Disposition` field (`Npc` has no `validate_assignment`), so a later `.attitude()` on an NPC updated through the chapter-apply/update-existing path raises `AttributeError`. **Not in the 72-2 diff and not introduced or worsened by it** (verified: `__eq__` is neutral to `int==Disposition`; `test_world_materialization.py` 39 passed). The correct pattern is `session.py:1400` (`npc.disposition = Disposition(before + delta)`). Worth a follow-up hardening story for the disposition subsystem. Affects `sidequest/game/world_materialization.py:502`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, Low): doc accuracy — `npc_pool.py` module docstring still says "no mechanical state" (member now carries disposition); `disposition.py` `__eq__` comment "clamped scores" → "stored values"; `_migrate_s5` docstring understates the None no-op surface. And a Low simplification: `key = name.casefold() if name else ""` is a dead branch (use S2's `if not name: continue`). *Found by Reviewer during code review.*

## Design Deviations

None at story intake.

### TEA (test design)
- **AC1 disposition-carry mechanism pinned to a scaffold-side field**
  - Spec source: context-story-72-2.md, AC1 ("where the disposition is carried from is a design decision for the implementer")
  - Spec text: "an existing same-name `Npc`, a scaffold-side value, or a passed-in argument"
  - Implementation: Tests pin the mechanism as a `disposition` field on `NpcPoolMember` (the session-file AC1 choice + the context-story's sanctioned "scaffold-side value"), exercised via `resolve_status_target` → `_promote_pool_member_to_npc`.
  - Rationale: It is the highest-authority spec (session AC1), the cleanest round-trip to assert, and backward-compatible with the live 72-5 neutral-default test. If Dev instead carries disposition from a same-name `Npc`, only the fixture wiring (how the value reaches the member) changes; the round-trip + event assertions stand.
  - Severity: minor
  - Forward impact: Adding the field to a `extra="forbid"` model — Dev must default it neutral (0) so `test_npc_spawn_disposition_otel.py` (72-5) keeps passing.
- **Reconcile tested at `migrate_legacy_snapshot`, not `Session.load()`**
  - Spec source: 72-2-session.md, AC3 ("reconciliation logic in `Session.load()` … remove the pool member (shadowed)")
  - Spec text: session AC3 framing of `Session.load()` + shadowed/orphan removal
  - Implementation: Tests drive the public `migrate_legacy_snapshot(dict)` raw-dict seam per context-story (the actual load canonicalization path, verified; `PgSnapshot.load` runs it pre-validation), mirroring `_migrate_s2_npc_registry_split`.
  - Rationale: The session file's `Session.load()` is not the real reconcile seam; the context-story seam is verified and CLAUDE.md "No Source-Text Wiring Tests" pushes behavior/OTEL assertions on the live entrypoint. The new sub-function must be appended to the migration tuple (after S2) — an unwired helper is dead code (No Stubbing).
  - Severity: minor
  - Forward impact: Dev wires a new `_migrate_s5_*`-style sub into the `migrate_legacy_snapshot` tuple; reconcile reads integer disposition in raw-dict space.
- **OTEL span for reconcile asserted as a fold into `snapshot.canonicalize`**
  - Spec source: 72-2-session.md AC3 (spans `npc.pool_reconciliation.shadowed_npc` / `orphan_pool_member`) vs context-story-72-2.md AC5 ("merge into canonicalize OR a dedicated NPC reconcile span — author's choice")
  - Spec text: session names dedicated spans; context-story allows folding into the shared canonicalize span
  - Implementation: Tests assert reconcile counts on the `snapshot.canonicalize` span (the `_migrate_s2` default the context-story leads with), not on dedicated `npc.pool_reconciliation.*` spans.
  - Rationale: The fold-in path matches the existing migration-span idiom and is the lowest-friction wiring; context-story explicitly sanctions it.
  - Severity: minor
  - Forward impact: If Dev emits a dedicated reconcile span instead, the AC5b assertions move to it (flagged as a Question in Delivery Findings).

### Dev (implementation)
- **Confirmed TEA's seam choices — disposition field on `NpcPoolMember`, reconcile folded into `migrate_legacy_snapshot`/`snapshot.canonicalize`.** Implemented exactly as the TEA deviations specify (scaffold-side disposition field defaulting neutral-0; new `_migrate_s5_reconcile_npc_pool` appended to the migration tuple after S2; `s5_pool_shadowed_removed` / `s5_disposition_conflicts` counts on the canonicalize span; `Npc` authoritative). No further deviation from those choices.
- **`Disposition` gains `__eq__` / `__hash__` (value semantics)**
  - Spec source: tests/game/test_npc_pool_model.py (existing) — `test_npc_pool_member_json_round_trip_*`
  - Spec text: "Pool members serialize to JSON and back with no field drift … `assert restored == original`"
  - Implementation: Added `__eq__` (compares clamped `.value`, returns `NotImplemented` for non-`Disposition`) and `__hash__` to `Disposition` (`sidequest/game/disposition.py`).
  - Rationale: `Disposition` is documented "a value type" but had no value equality, so two `Disposition(0)` instances compared by identity. Adding `NpcPoolMember.disposition` made the model's BaseModel `__eq__` compare the field, breaking the pre-existing round-trip equality tests. The test is correct; `Disposition` was incomplete — root-cause fix, not a test weakening.
  - Severity: minor
  - Forward impact: positive — `Npc` (also carries a `Disposition` field) now compares by value on round-trip too. No behavioral change to attitude derivation or serialization (still serializes to bare int).
- **`spawn_disposition` span provenance gains `carried_from_pool`**
  - Spec source: telemetry/spans/disposition.py (Story 72-5), OTEL Observability Principle
  - Spec text: 72-5 comment — "provenance is always `default_neutral` here"
  - Implementation: In `_promote_pool_member_to_npc`, provenance is `default_neutral` when the carried disposition is 0, else `carried_from_pool`.
  - Rationale: Once 72-2 carries a non-neutral disposition through promotion, labeling it `default_neutral` would make the lie-detector span report a false default. `provenance` is a free-form string (not enum-validated), so a new honest value is safe and the 72-5 neutral-default test (Wexley → 0 → `default_neutral`) stays green.
  - Severity: minor
  - Forward impact: GM panel / any consumer keying on provenance must treat `carried_from_pool` as a third value alongside `default_neutral` / `default_creature_hostile`.

### Reviewer (audit)
- **TEA — AC1 disposition-carry mechanism (scaffold-side field)** → ✓ ACCEPTED: highest-authority spec choice, backward-compatible, round-trip-testable. Sound.
- **TEA — Reconcile at `migrate_legacy_snapshot`, not `Session.load()`** → ✓ ACCEPTED: verified by rule-checker (#15) as wired into the live tuple; the real universal load-canonicalization seam. Architecturally correct (Architect spec-check concurred).
- **TEA — Reconcile OTEL folded into `snapshot.canonicalize`** → ✓ ACCEPTED: mirrors the established `_migrate_s2` idiom; primitive attrs confirmed by rule-checker (#17).
- **Dev — Confirmed TEA seam choices** → ✓ ACCEPTED.
- **Dev — `Disposition.__eq__`/`__hash__` value semantics** → ✓ ACCEPTED with evidence: empirically verified neutral to existing `int==Disposition` comparisons (`Disposition(-5) == -5` is `False` before and after; `test_world_materialization.py` 39 passed). Root-cause fix for a documented value type; rule-checker's Rule-13 regression claim **dismissed with evidence** (suite green). type-design confirmed `__eq__`/`__hash__` value-consistency.
- **Dev — `carried_from_pool` provenance** → ✓ ACCEPTED: keeps the spawn_disposition lie-detector honest; free-form string field; 72-5 neutral path preserved. (One residual: it cannot distinguish unset-0 from explicit-0 — captured as a non-blocking finding, not a deviation flaw.)

No undocumented in-scope deviations found — the implementation matches the logged TEA/Dev choices and the context-story ACs (Architect spec-check verified alignment).

### Architect (reconcile)

Reviewed all in-flight entries (TEA, Dev, Reviewer-audit): spec sources (`72-2-session.md`, `context-story-72-2.md`) exist and are quoted accurately, implementation descriptions match the merged code, all 6 fields present. No ACs were deferred (Dev marked AC1–AC5 met; ac-completion table shows no DEFERRED/DESCOPED). Two spec→implementation deviations were *accepted in spec-check* but not yet captured as formal 6-field entries — recording them here so the manifest is auditable from the session file alone.

- **Promotion OTEL surface diverges from session AC2's prescribed span**
  - Spec source: `.session/72-2-session.md`, AC2
  - Spec text: "Emit OTEL span `npc.promoted_from_pool` carrying ... `disposition_before` ... `disposition_after` ... Span is fired **inside** `_promote_pool_member_to_npc`, not at call sites"
  - Implementation: No dedicated `npc.promoted_from_pool` span and no before/after pair. Instead, `disposition` + `attitude` are carried as attributes on the **existing** `promoted_from_pool` watcher event emitted by `resolve_status_target` (the call site, `narration_apply.py:1149`), and the in-function `spawn_disposition` span gains a `carried_from_pool` provenance tag.
  - Rationale: Matches `context-story-72-2.md` AC5 verbatim ("a disposition-preserved attribute on the **existing** `promoted_from_pool` watcher event") — the verified, lower-friction wiring. The GM panel receives the preserved disposition either way; a new span type and a before/after pair were unnecessary. Accepted in Architect spec-check (Recommendation A).
  - Severity: minor
  - Forward impact: Telemetry consumers read `disposition`/`attitude` from the `promoted_from_pool` event `fields`, not from a dedicated span's before/after attributes. The new `carried_from_pool` provenance is a third value alongside `default_neutral`/`default_creature_hostile`.

- **Reconcile OTEL granularity + orphan-span omission diverges from session AC3**
  - Spec source: `.session/72-2-session.md`, AC3
  - Spec text: "Emit OTEL span `npc.pool_reconciliation.shadowed_npc` carrying `npc_name` + `removed_pool_member: bool` ... For each pool member ... with no matching NPC ... Emit OTEL span `npc.pool_reconciliation.orphan_pool_member` carrying `member_name`"
  - Implementation: No dedicated per-NPC `npc.pool_reconciliation.*` spans. Aggregate counts `s5_pool_shadowed_removed` / `s5_disposition_conflicts` are folded into the shared `snapshot.canonicalize` span (`migrations.py`). Pool-only ("orphan") members are a silent no-op — the reconcile returns `None` and emits no orphan span.
  - Rationale: `context-story-72-2.md` AC3 requires only that a pool-only name "reconciles without error and without fabricating a spurious `Npc` ... No silent drop" — it does **not** require an orphan span; and AC5 sanctions folding counts into `snapshot.canonicalize`. The aggregate-count + fold-in approach mirrors the established `_migrate_s2_npc_registry_split` idiom (Don't Reinvent) and the universal load-canonicalization seam. Accepted in Architect spec-check (Recommendation A).
  - Severity: minor
  - Forward impact: The GM panel reads aggregate `s5_*` counts on `snapshot.canonicalize`, not per-NPC reconciliation spans; orphan/pool-only members produce no telemetry (consistent with migration no-op semantics). A future story wanting per-NPC reconcile forensics would add a dedicated span. (Reviewer separately flagged that the malformed-pool-skip path lacks an `s5_malformed_*` count — a non-blocking hardening item in Delivery Findings, not a spec deviation.)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN: 58 story tests pass, lint clean, story files type-clean; 32 narration_apply pyright errors + 2 pack-validator fails confirmed pre-existing) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 11 | confirmed 5, dismissed 1, deferred(low) 5 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 3 (Medium), deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6 (Medium coverage gaps) |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 (Low/doc) |
| 6 | reviewer-type-design | Yes | findings | 3 | confirmed 3 (1 out-of-scope Gap, 2 Low) |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2 (Medium/Low), no injection/ReDoS/PII |
| 8 | reviewer-simplifier | Yes | findings | 1 (+1 pre-existing noted) | confirmed 1 (Low) |
| 9 | reviewer-rule-checker | Yes | findings | 2 (15/17 rules clean) | dismissed 1 (Rule 13, with evidence), confirmed 1 (Rule 9, Low) |

**All received:** Yes (9 returned, 8 with findings)
**Total findings:** 14 confirmed, 2 dismissed (with rationale), 0 deferred-blocking. **Zero in-scope Critical/High.**

## Reviewer Assessment

**Verdict:** APPROVED

A correct, spec-complete, fully-wired, OTEL-instrumented implementation. All nine specialists ran; the convergent signal is a single cluster of **Medium/Low** hardening items around corrupt/legacy-data telemetry accuracy — none of which corrupt valid data or block the PR. One **out-of-scope pre-existing** bug was discovered and is captured for follow-up.

**Data flow traced:** A save snapshot loads → `PgSnapshot.load` → `migrate_legacy_snapshot(raw dict)` → `_migrate_s5_reconcile_npc_pool` reads `npcs`/`npc_pool` (case-folded), drops pool members shadowed by a same-name `Npc`, counts `s5_pool_shadowed_removed`/`s5_disposition_conflicts` on `snapshot.canonicalize` → pydantic `model_validate` (fails loud on any non-int/None disposition that survived) → live snapshot. Separately, a status mutation on a pool-only name → `resolve_status_target` → `_promote_pool_member_to_npc` carries `member.disposition` onto the new `Npc`, emits `spawn_disposition` (provenance `carried_from_pool` when non-zero) and the `promoted_from_pool` watcher event (now carrying `disposition` + `attitude`). **Safe because** every corrupt-input path either fails loud at validation or is dropped during reconcile; reconciliation *decisions* are name-based and unaffected by disposition values.

**Pattern observed:** `_migrate_s5_reconcile_npc_pool` faithfully mirrors `_migrate_s2_npc_registry_split` (dict-in/dict-out, isinstance guards, count-or-None return, OTEL fold-in) — `sidequest/game/migrations.py:290` — the correct idiom.

**Error handling:** Defensive `isinstance` guards on `npcs`/`pool`/`npc`/`core`; `is not None` guard on member disposition; input never mutated (deep-copied `out`, verified by `test_reconcile_does_not_mutate_input`).

### Confirmed observations (5+ required)

1. `[VERIFIED]` Wiring — `_migrate_s5_reconcile_npc_pool` is in the live `migrate_legacy_snapshot` tuple at `migrations.py:387` (after S2), which runs on every load (`test_save_load_runs_migrate`). Not half-wired. `[RULE #15]` confirms.
2. `[VERIFIED]` OTEL primitives — `s5_pool_shadowed_removed`/`s5_disposition_conflicts` (int), `disposition` (int), `attitude` (str via StrEnum `.value`). `[RULE #17]` confirms. Lie-detector requirement met.
3. `[VERIFIED]` Backward/forward compat — `NpcPoolMember.disposition` has `default_factory=Disposition`; old saves (no key) deserialize neutral, re-serialize to bare int. `[TYPE]` confirms; `test_npc_pool_member_json_round_trip_*` green.
4. `[VERIFIED]` `Disposition.__eq__`/`__hash__` value-consistency and **neutrality to existing int comparisons** — `Disposition(-5) == -5` is `False` identically before/after; `test_world_materialization.py` **39 passed**. `[RULE #13]` regression claim **dismissed with evidence**.
5. `[MEDIUM][SILENT][SEC][EDGE]` Disposition raw-dict type-guard cluster — `npc.get("disposition", 0)` (absent→0) vs `member.get("disposition")` (absent→None) asymmetry; a corrupt non-int or a legacy null disposition can inflate `s5_disposition_conflicts`. **Non-blocking:** corrupt values fail loud at pydantic validation post-migration; on all *valid* data the counts are correct. `migrations.py:334,351-352`.
6. `[MEDIUM][SILENT]` Malformed pool members (`not isinstance(member, dict)`) are kept with **no** `s5_malformed_pool_members_skipped` count — asymmetric with S2's `s2_malformed_npcs_skipped`. No-Silent-Fallbacks/OTEL gap, but data is preserved then rejected loud at validation. `migrations.py:343`.
7. `[LOW][EDGE]` Duplicate case-folded npc name → last-write-wins in `npc_disposition`, uncounted. Out of scope (npcs-side dedup is a sibling story). `migrations.py:334`.
8. `[MEDIUM][TEST]` Coverage gaps in correct code: same-value-no-conflict false-arm, multiple-shadowed-members count, non-dict-pool-entry survival, and the `carried_from_pool` provenance branch are untested. Regressions could slip silently.
9. `[LOW][SILENT][EDGE][DOC]` `provenance` cannot distinguish unset-0 from explicit-0 (`int(member.disposition)==0`). No live writer of non-zero pool dispositions yet (that's 72-1), so no current consumer is harmed.
10. `[LOW][DOC]` `npc_pool.py` module docstring "no mechanical state" now inaccurate (member carries disposition); `disposition.py:160` "clamped scores" → "stored"; `_migrate_s5` docstring understates the None no-op surface.
11. `[LOW][SIMPLE]` `key = name.casefold() if name else ""` is a dead branch (`"".casefold()==""`); S2's `if not name: continue` idiom is cleaner. `migrations.py:347`.
12. `[LOW][TYPE]` `Disposition.__hash__` on a mutable object is a latent footgun (never used as a dict key today); `npc_disposition: dict[str, Any]` could tighten to `dict[str, int]`.
13. `[LOW][RULE #9][TEST]` `await asyncio.sleep(0)` (test:235) lacks the why-comment Rule 9 wants; mirrors the 72-5 sibling pattern. `asyncio.get_event_loop().time()` is pre-existing copy-paste debt across many tests.
14. `[GAP — OUT OF SCOPE][TYPE]` **Pre-existing bug** at `world_materialization.py:502`: `existing.disposition = int(npc_data.disposition)` assigns a raw int to the typed `Disposition` field (`Npc` has no `validate_assignment`), so a later `.attitude()` on that NPC would `AttributeError`. **Not in the 72-2 diff, not introduced or worsened by this change** (verified). Captured as a Delivery Finding for a follow-up.

### Rule Compliance

Per `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md/SOUL.md, enumerated by reviewer-rule-checker across 17 rules / 54 instances:
- **#1 silent-exceptions, #2 mutable-defaults, #3 type-annotations, #4 logging, #5 paths, #7 resource-leaks, #8 deserialization, #10 imports, #11 input-validation, #12 deps:** compliant across all changed functions/fields.
- **#6 test-quality:** compliant — every test asserts specific values; the `model_fields` check is the sanctioned reflection tripwire; no vacuous assertions.
- **#9 async:** one Low — `await asyncio.sleep(0)` without comment (test:235).
- **#13 fix-regressions:** the flagged `Disposition.__eq__` regression is **dismissed with evidence** (suite green; int-comparison semantics unchanged).
- **No Silent Fallbacks (#14):** conflict path counts divergence (compliant); the malformed-pool-skip path lacks a count (obs #6, Medium) — confirmed, not dismissed, but downstream validation fails loud.
- **No Stubbing / wiring (#15):** reconcile wired into the live tuple; field consumed by promotion. Compliant.
- **No Source-Text Wiring Tests (#16):** tests drive real seams + assert OTEL/behavior. Compliant.
- **OTEL primitives (#17):** all attrs primitive. Compliant.

### Devil's Advocate

Argue this is broken. **The attack:** feed a hand-edited save where `npc_pool` carries `[{"name":"Mara","disposition":{"evil":true}}]` and `npcs` carries `[{"core":{"name":"Mara"},"disposition":null}]`. Reconcile reads `npc.get("disposition", 0)` → wait, the key is present with `null`, so `npc_disposition["mara"] = None`. Member disposition `{"evil":true}` is not None → `{"evil":true} != None` → True → `s5_disposition_conflicts += 1`, member dropped. The GM panel now shows a "disposition conflict" that is really structural garbage — the lie-detector lies. **But:** the member is *dropped* (shadowed), so the garbage never reaches validation; and had it survived (pool-only), `model_validate` would reject `{"evil":true}` against the `Disposition` schema and fail the entire load loudly. So the worst real outcome is one inflated forensic counter on a save that is already corrupt — no state corruption, no silent success. **Second attack:** a confused author resets a befriended NPC to neutral by authoring `disposition: 0` on the pool member, expecting the GM panel to show "carried" — but promotion emits `default_neutral`, indistinguishable from never-set. Misleading, yes; harmful, no — and no production path writes non-zero pool dispositions yet, so this is dormant until 72-1. **Third:** could the reconcile drop a *real* relationship? Only if a freshly-promoted neutral `Npc` (the very bug this epic fixes elsewhere) shadows a scaffold that held the true value — and even then it's *counted* as a conflict (surfaced), per the documented "Npc authoritative" rule. **Conclusion:** every adversarial path terminates in either a loud validation failure or a surfaced/counted decision. Nothing silently corrupts state. The findings are real but bounded to telemetry accuracy on already-invalid data and to test-coverage of correct code — Medium at most. The code holds.

**Dispatch tags present:** `[EDGE]` `[SILENT]` `[TEST]` `[DOC]` `[TYPE]` `[SEC]` `[SIMPLE]` `[RULE]` (+ `[PREFLIGHT]` clean).

**Decision rationale:** Zero in-scope Critical/High; severity rubric makes Medium/Low non-blocking. The convergent cluster is confirmed (not dismissed) and routed to a follow-up hardening story so it reaches the boss's deviation manifest. Spec-complete (Architect-verified), wired (rule-checker-verified), suite green (9210).

**Handoff:** To Morpheus (SM) for finish-story.

## Sm Assessment

**Routing decision:** Story 72-2 set up and routed to TEA for the RED phase (tdd workflow, phased).

- **Story selected by Operator** (explicit `72-2` call), highest-value leg of fresh epic 72 (NPC Identity Hardening, perseus_cloud session 894 DEEP-DIVE #1, 2026-05-29).
- **Scope is well-bounded:** two legs (disposition-preserving promotion; npcs/npc_pool reconciliation on load), 4 ACs, all in `sidequest-server`.
- **OTEL is non-negotiable here** — three span families are named in the ACs (`npc.promoted_from_pool`, `npc.pool_reconciliation.shadowed_npc`, `npc.pool_reconciliation.orphan_pool_member`). Per the project's OTEL Observability Principle, the GM panel is the lie detector for this subsystem; AC4's wiring tests must assert the spans fired with correct attributes, not just that the code path ran.
- **Merge gate:** clear — no blocking open PRs in sidequest-server.
- **Branch:** `feat/72-2-preserve-disposition-reconcile-npc-pool` off `develop` (per repos.yaml; server targets develop, not main).
- **Watch items for TEA:** backward-compat on load (existing saves have no disposition on pool members — AC1 says optional/default-neutral); reuse the case-folded name-match logic from `_apply_npc_mentions` for reconciliation rather than reinventing it (Don't Reinvent principle). AC1 explicitly excludes disposition from the development pipeline — that's mechanical state on `npcs`, not pool scaffold.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5pt bug across two seams (promotion + load reconcile); behavior + OTEL must be pinned before Dev.

**Test Files:**
- `sidequest-server/tests/integration/test_pool_disposition_preservation.py` — leg 1: disposition survives pool→Npc promotion (round-trip) + `promoted_from_pool` event carries the preserved value. Mirrors the 72-5 watcher-capture harness (`test_npc_spawn_disposition_otel.py`).
- `sidequest-server/tests/game/test_pool_reconciliation_on_load.py` — leg 2: `migrate_legacy_snapshot` reconcile pass (shadow removal, divergent-disposition-to-Npc, pool-only/npcs-only no-ops, input-not-mutated) + `s5_*` OTEL counts on `snapshot.canonicalize`. Mirrors `test_npc_pool_migration.py`.

**Tests Written:** 12 tests (8 RED drivers + 4 green invariant guards) covering 5 derived ACs (context-story AC1–AC5).
**Status:** RED — verified via `testing-runner` (RUN_ID 72-2-tea-red) and direct `pytest -n0`: **8 failed, 4 passed**.

### RED breakdown (8 failing drivers)
| AC | Test | Fails because |
|----|------|---------------|
| AC1 | `test_npc_pool_member_carries_disposition_field` | `NpcPoolMember` has no `disposition` field (reflection tripwire) |
| AC1 | `test_disposition_field_defaults_neutral` | `AttributeError: no attribute 'disposition'` |
| AC1 | `test_promotion_preserves_nonneutral_disposition` | member rejects `disposition=` kwarg; promotion drops to neutral |
| AC1 | `test_promotion_preserves_hostile_disposition` | same (−22 round-trip) |
| AC5a | `test_promoted_from_pool_event_carries_disposition` | event payload carries no `disposition`/`attitude` attr |
| AC2 | `test_shadowed_pool_member_removed_on_load` | no reconcile pass — duplicate `Mara` survives in `npc_pool` |
| AC5b | `test_reconcile_counts_shadowed_removal_in_otel` | no `snapshot.canonicalize` span / no `s5_pool_shadowed_removed` |
| AC4 | `test_divergent_disposition_resolves_to_npc_and_is_counted` | divergent +5 scaffold survives, uncounted |

### Green invariant guards (4 — must STAY green)
- `test_promotion_with_no_prior_disposition_stays_neutral` — 72-5 neutral default preserved (don't drag no-prior-value members off neutral).
- `test_pool_only_member_is_left_intact` (AC3) — reconcile must not over-reach: pool-only scaffold survives, no spurious `Npc`, clean no-op (no span).
- `test_npcs_only_name_unaffected` (AC4 first clause) — npcs-only name authoritative, no spurious pool member.
- `test_reconcile_does_not_mutate_input` — `migrate_legacy_snapshot` purity contract.

### Rule Coverage
| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (divergence counted, not first-wins) | `test_divergent_disposition_resolves_to_npc_and_is_counted` | failing |
| No Source-Text Wiring Tests (OTEL/fixture, not grep) | all reconcile tests drive public `migrate_legacy_snapshot` + span asserts | failing/guard |
| No Stubbing (reconcile wired into live tuple) | `test_shadowed_pool_member_removed_on_load` (public entrypoint) | failing |
| Reflection-based type check (sanctioned exception) | `test_npc_pool_member_carries_disposition_field` | failing |
| python.md #6 test quality (no vacuous asserts) | self-check below | n/a |

**Rules checked:** 4 of the applicable project rules have test coverage (python.md lang-review checks #1–#5,#7–#13 are dev-implementation rules, not test-design rules; #6 self-applied).
**Self-check:** 0 vacuous tests — every test asserts a specific value (disposition int, attitude band, span attr count, membership), no `assert True`, no bare-truthy, no `let _`-equivalent.

**Handoff:** To Agent Smith (Dev) for GREEN. Implementation notes are in Design Deviations → TEA (disposition-field mechanism, reconcile seam = `migrate_legacy_snapshot` tuple, `Npc`-authoritative conflict rule, `s5_*` span contract) and Delivery Findings → TEA (span-name flexibility). Critical guardrail: the new `disposition` field must default neutral-0 so the 72-5 `test_npc_spawn_disposition_otel.py` suite keeps passing.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (no source change in this phase)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 6 (4 source + 2 test)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | S5↔S2 parallel is deliberate (not duplication); case-fold/by-name pattern not worth extracting at 2 sites |
| simplify-quality | 7 findings | 1 high, 3 medium, 3 low — all triaged below |
| simplify-efficiency | clean | reconcile is O(npcs+pool) single-pass; `__eq__`/`__hash__` minimal; no over-engineering |

**Applied:** 0 high-confidence fixes — the sole "high" finding (S5 ordering guard) is a *behavioral* addition (a `raise`), not a simplification; applying untested behavior in the verify simplify-pass would violate TDD and be inconsistent with the un-guarded S1–S4 pattern. Recorded as a non-blocking Improvement (Delivery Findings → TEA, test verification).
**Flagged for Review:** 0 medium findings carried forward — triaged as invalid or churn (see below).
**Noted:** 3 low cosmetic nits dismissed (test-helper naming, two doc nits) — below the bar.
**Reverted:** 0.

**Triage of simplify-quality findings:**
- *disposition.py `__ne__` missing* (low) — invalid: Python 3 auto-derives `__ne__` from `__eq__`.
- *narration_apply.py `int(member.disposition)` may raise on None* (medium) — invalid: `disposition` is a typed `Disposition` field (`default_factory`), never None.
- *narration_apply.py attitude may drift from numeric* (medium) — invalid: attitude is derived-on-demand by design (disposition.py's two-layer split); freezing it would violate the architecture.
- *migrations.py `member.get("disposition")` type-check* (medium) — dismissed: already None-guarded; a stray non-int only mis-counts a harmless aggregate, and the existing `_migrate_s2` pattern doesn't over-guard.
- *migrations.py S5 ordering guard* (high) — valid observation, **not applied** (new behavior, needs TDD; inconsistent with existing pattern). Logged as Improvement for a potential follow-up.
- 3 low doc/naming nits — dismissed as cosmetic.

**Overall:** simplify: clean (0 fixes applied; 1 valid robustness observation deferred to a follow-up, 6 findings dismissed as invalid/cosmetic with rationale).

**Quality Checks:** Full server suite GREEN at green-phase exit (9210 passed; 2 pre-existing pack-validator failures proven independent via stash-verify). No source touched in verify, so no regression surface introduced.
**Handoff:** To The Merovingian (Reviewer) for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with logged, sound deviations from the session-file ACs toward the verified context-story ACs)
**Gate:** spec-check PASS (AC coverage, implementation-complete, TEA+Dev deviation subsections all present).
**Mismatches Found:** 4 — all against the *session-file* ACs (sm-setup-authored); all resolve to the *context-story* ACs (authored with verified seams), which is the operative spec here. None require hand-back.

- **Reconcile seam: `migrate_legacy_snapshot` vs `Session.load()`** (Different behavior — Architectural, Minor)
  - Spec: session AC3 says reconcile "in `Session.load()`" with dedicated `npc.pool_reconciliation.shadowed_npc`/`orphan_pool_member` spans.
  - Code: new `_migrate_s5_reconcile_npc_pool` in the `migrate_legacy_snapshot` tuple (after S2), aggregate `s5_*` counts on `snapshot.canonicalize`.
  - Recommendation: **A — accept/update spec.** `migrate_legacy_snapshot` is the actual universal load-canonicalization seam (runs on every load pre-validation per `test_save_load_runs_migrate`); `Session.load()` has no raw-dict reconcile point. The impl mirrors the existing `_migrate_s2_npc_registry_split` pattern (Don't Reinvent) and folds counts into the established canonicalize span. Architecturally superior to the session AC's guess. Logged by TEA + Dev.
- **Promotion OTEL: event-attribute vs dedicated `npc.promoted_from_pool` span** (Different behavior — Behavioral, Minor)
  - Spec: session AC2 wants a `npc.promoted_from_pool` span with `disposition_before`/`disposition_after` fired *inside* the promote fn.
  - Code: carries `disposition`+`attitude` on the existing `promoted_from_pool` watcher event (in `resolve_status_target`); the in-fn `spawn_disposition` span gains `carried_from_pool` provenance.
  - Recommendation: **A — accept.** Matches context-story AC5 verbatim ("a disposition-preserved attribute on the existing `promoted_from_pool` watcher event"). GM panel sees the carried value either way; no new span type needed. Logged.
- **Extra: `Disposition.__eq__`/`__hash__`** (Extra in code — Architectural, Minor, positive)
  - Spec: not in any AC.
  - Code: value-equality + hash on the `Disposition` value type.
  - Recommendation: **A — accept.** Root-cause fix for a latent gap the new `NpcPoolMember.disposition` field exposed in pre-existing round-trip tests. A documented "value type" gaining value semantics is correct design; also fixes `Npc` round-trip equality. Logged.
- **Extra: `carried_from_pool` provenance value** (Extra in code — Behavioral, Minor)
  - Spec: 72-5 comment said provenance is "always `default_neutral` here".
  - Code: `default_neutral` when carried disposition is 0, else `carried_from_pool`.
  - Recommendation: **A — accept.** Keeps the `spawn_disposition` lie-detector honest once a non-neutral disposition rides through (OTEL Observability Principle). Free-form string field, 72-5 neutral case unaffected. Logged; flagged to GM-panel consumers in Delivery Findings.

**Scope discipline confirmed:** reconcile drops shadowed pool members without merging identity fields (`pronouns`/`drawn_from`) that 72-3/72-7 own; `Npc` authoritative for disposition per context-story assumption; divergence counted, never silent-first-wins.

**Decision:** Proceed to verify (TEA). No hand-back.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/npc_pool.py` — `NpcPoolMember` gains a `disposition: Disposition` field (default neutral-0; preserves 72-5 born-neutral default).
- `sidequest-server/sidequest/server/narration_apply.py` — `_promote_pool_member_to_npc` carries `member.disposition` onto the `Npc`; `spawn_disposition` span provenance is `carried_from_pool` when a known value rides through; `promoted_from_pool` watcher event carries `disposition` + `attitude`.
- `sidequest-server/sidequest/game/migrations.py` — new `_migrate_s5_reconcile_npc_pool` sub-function wired into the `migrate_legacy_snapshot` tuple (after S2); removes shadowed pool members, resolves divergent disposition to the authoritative `Npc`, emits `s5_pool_shadowed_removed` / `s5_disposition_conflicts` on the `snapshot.canonicalize` span.
- `sidequest-server/sidequest/game/disposition.py` — `Disposition` gains `__eq__` / `__hash__` (value semantics) so models carrying the field round-trip-compare by value.

**Tests:** All 12 story tests GREEN (8 drivers + 4 invariant guards). Regression-clean: `test_npc_pool_model` round-trips fixed, 72-5 `test_npc_spawn_disposition_otel` + all migration/disposition suites still pass. Full server suite: **9210 passed, 361 skipped, 2 pre-existing pack-validator failures** (proven independent of this story via stash-verify).
**Quality:** `ruff check` clean, `ruff format` applied, `pyright` 0 errors on changed source.
**Branch:** `feat/72-2-preserve-disposition-reconcile-npc-pool` (pushed).

**AC coverage:** AC1 (disposition field + round-trip preservation), AC2 (shadow removal → single source of truth), AC3 (pool-only no-op), AC4 (npcs-only authoritative + divergent-disposition resolution, counted), AC5 (OTEL on both legs: `promoted_from_pool` event carries disposition; reconcile counts on `snapshot.canonicalize`). All met.

**Handoff:** To The Merovingian (Reviewer) for code review.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-30T22:21:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30T17:47:00Z | 2026-05-30T21:43:03Z | 3h 56m |
| red | 2026-05-30T21:43:03Z | 2026-05-30T21:53:20Z | 10m 17s |
| green | 2026-05-30T21:53:20Z | 2026-05-30T22:01:44Z | 8m 24s |
| spec-check | 2026-05-30T22:01:44Z | 2026-05-30T22:03:59Z | 2m 15s |
| verify | 2026-05-30T22:03:59Z | 2026-05-30T22:08:08Z | 4m 9s |
| review | 2026-05-30T22:08:08Z | 2026-05-30T22:19:32Z | 11m 24s |
| spec-reconcile | 2026-05-30T22:19:32Z | 2026-05-30T22:21:16Z | 1m 44s |
| finish | 2026-05-30T22:21:16Z | - | - |

## Technical Approach

### Step 1: Add disposition field to NpcPoolMember
- Modify `sidequest/game/npc_pool.py` to add `disposition` field (optional, defaults to neutral)
- Update Pydantic schema to preserve backward compatibility

### Step 2: Update promotion function
- Modify `_promote_pool_member_to_npc` in `sidequest/server/narration_apply.py`
- Read `member.disposition` and pass to `Npc` constructor
- Add OTEL span emission with pre/post disposition values
- Update comment referencing Story 72-5 if needed

### Step 3: Add reconciliation function
- Create `_reconcile_npc_pool_on_load` in `sidequest/server/narration_apply.py` or `sidequest/game/session.py`
- Implement case-folded name matching (reuse lookup logic from `_apply_npc_mentions`)
- Emit OTEL spans for shadowed and orphan pool members
- Wire into load path

### Step 4: Write RED tests
- `test_pool_disposition_preservation.py`: fixture-driven wiring test proving disposition survives promotion
- `test_pool_reconciliation_on_load.py`: fixture-driven wiring test proving reconciliation cleans shadow entries

### Step 5: Implement GREEN
- Make all RED tests pass

### Step 6: Spec-check
- Verify no undocumented deviations from ADR-020 (NPC Disposition System)
- Verify OTEL spans carry all required attributes for GM panel visibility