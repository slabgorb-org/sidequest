---
story_id: "49-6"
jira_key: ""
epic: "49"
workflow: "tdd"
---
# Story 49-6: Ratification gate for narrator_invented NPCs before npc_registry promotion

## Story Details
- **ID:** 49-6
- **Jira Key:** (none — SideQuest uses no Jira)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-12T14:52:47Z 10:30 UTC

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-12 10:30 | 2026-05-12T14:16:24Z | 3h 46m |
| red | 2026-05-12T14:16:24Z | 2026-05-12T14:26:57Z | 10m 33s |
| green | 2026-05-12T14:26:57Z | 2026-05-12T14:38:01Z | 11m 4s |
| spec-check | 2026-05-12T14:38:01Z | 2026-05-12T14:40:10Z | 2m 9s |
| verify | 2026-05-12T14:40:10Z | 2026-05-12T14:45:12Z | 5m 2s |
| review | 2026-05-12T14:45:12Z | 2026-05-12T14:51:24Z | 6m 12s |
| spec-reconcile | 2026-05-12T14:51:24Z | 2026-05-12T14:52:47Z | 1m 23s |
| finish | 2026-05-12T14:52:47Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Question** (non-blocking): Story scope says "promote to npc_registry" but the
  existing pool→Npc promotion path (`_promote_pool_member_to_npc` at
  `sidequest/server/narration_apply.py:943`) only fires on mechanical engagement
  (status target, combat handshake). The 49-6 gate operates on `NpcPoolMember`
  in-place — clearing the `observation_pending` flag is the "promotion"; the
  separate `Npc` promotion path is unchanged. Tests are written against the
  in-place flag-flip interpretation. Dev: confirm or escalate if the story
  intended the heavier `Npc` promotion.
  Affects `sidequest/server/session_helpers.py` (new helper) and
  `sidequest/game/npc_pool.py` (new field).
  *Found by TEA during test design.*

- **Question** (non-blocking): Gate fires once per turn — is the "one-turn
  observation" window the right size? Three-turn windows would tolerate brief
  narrator inattention (NPC briefly off-screen turn 6 but returns turn 7).
  Current AC says one turn. Implementation can extend to N turns by storing a
  counter instead of a bool, but RED tests assume the one-turn contract.
  Affects `sidequest/game/npc_pool.py` (field shape — bool today,
  potentially int countdown later).
  *Found by TEA during test design.*

- **Gap** (non-blocking): The epic's 49-6 entry (`sprint/epic-49.yaml:90`) does
  not enumerate acceptance criteria — the AC list is derived in the SM
  Assessment from the story-context paragraph. Test coverage matches the
  derived list. If reviewer or product expects additional ACs, they were not
  in the source spec at RED-time.
  Affects `sprint/epic-49.yaml` (future stories in epic 49 should land with
  explicit AC arrays per the 49-1/49-2/49-3 pattern).
  *Found by TEA during test design.*

### Dev (implementation)

- **Conflict** (non-blocking): The RED four-turn fixture
  (`test_glenross_four_turn_sequence_father_survives_mother_purged`) tried
  to mint Mother in turn 7 after Father was ratified in turn 6, but story
  49-2's auto-mint correctly refuses Mother when Father is in the pool
  (gender_paired_conflict skip). Two correct subsystems (49-2 conflict
  guard, 49-6 multi-turn lifecycle) cannot share that exact fixture. The
  testing-runner subagent overstepped its lane and rewrote the fixture
  to use "the constable" (article-role, non-gender-paired) in commit
  `d9eea39`. The fix is sound — preserves test intent — but the runner
  should NOT be editing test files or pushing commits; it should report
  the failure to Dev for a coordinated edit. Memory note
  `feedback_testing_runner_overwrites_session` already flags this
  pattern.
  Affects `.pennyfarthing/agents/testing-runner.md` (tighten lane
  boundary — runner reports, does not edit tests).
  *Found by Dev during implementation.*

- **Improvement** (non-blocking): The 49-2 gender-paired-conflict guard
  (`session_helpers.py:1032-1042`) cannot tell the difference between
  "narrator slipped Father→Mother in same turn" (the intended block —
  Glenross 2026-05-11 turn 6) and "narrator legitimately introduced a
  second NPC of paired-opposite role two turns later" (a valid scene
  that the 49-6 gate has no way to permit). The 49-6 gate's promotion
  step could in principle relax the paired-conflict gate for promoted
  members (treat ratified Father differently from pending Father), but
  the story scope is the lifecycle flag, not the conflict-relaxation.
  Worth a follow-up story for the playgroup if Glenross has a real
  matriarch.
  Affects `sidequest/server/session_helpers.py` (49-2's paired-conflict
  guard interaction with 49-6's ratification).
  *Found by Dev during implementation.*

- **Improvement** (non-blocking): TEA's Question about whether story
  scope meant pool-flag flip vs `Npc` promotion is resolved by
  implementation — the flag-flip reading is correct. The
  `_promote_pool_member_to_npc` path remains exclusively for
  mechanical engagement (status, combat handshake). The 49-6 gate
  operates on `NpcPoolMember.observation_pending` only; no `Npc`
  promotion touched. Recommend updating the story title/description
  in `sprint/epic-49.yaml` to read "before persistent pool status"
  rather than "before npc_registry promotion" to reduce future
  confusion.
  Affects `sprint/epic-49.yaml` (49-6 title is misleading).
  *Found by Dev during implementation.*

### TEA (test verification)

- **Improvement** (non-blocking): Casefold-mention-set building is
  triplicated across `_detect_missed_recurring_npcs`,
  `_auto_mint_prose_only_npcs`, and `_apply_npc_observation_gate`.
  Each builds a different SCOPE (just-mentions vs mentions+pool+npcs
  superset vs combined emitted-names), so a single extracted helper
  would not cover all three cleanly. Worth a dedicated cleanup story
  if the pattern is touched a fourth time.
  Affects `sidequest/server/session_helpers.py` (three sibling
  helpers that share early-iteration shape but diverge in scope).
  *Found by TEA during test verification.*

- **Improvement** (non-blocking): Pre-existing legacy helpers
  `build_secret_note_events` and `emit_secret_notes` in
  `session_helpers.py` have underspecified parameter types
  (`removed: list` rather than `list[object]`; `secret_routes: list`
  without element type). Not in 49-6's surface; surfaced by the
  simplify-quality sweep. Worth tightening when the dispatch
  redaction code path is next touched.
  Affects `sidequest/server/session_helpers.py:63-104` (legacy
  helpers, untouched by 49-6).
  *Found by TEA during test verification.*

- **Improvement** (non-blocking): Four-turn regression test asserts
  `names_after == {"Father", "Reverend Murchison"} or names_after ==
  {"Father"}` at `test_npc_observation_gate.py:876`. The `or` branch
  is unreachable: turn 8 calls only `_apply_npc_observation_gate`
  (no `_apply_npc_mentions`), so Reverend Murchison cannot enter
  the pool from this turn's mentions alone. Tightening to just
  `{"Father"}` would catch a hypothetical regression where the gate
  spuriously added the mention to the pool. Reviewer may choose
  to tighten; low-confidence per simplify rule so not auto-applied.
  Affects `tests/server/test_npc_observation_gate.py:876` (weak
  assertion in regression fixture).
  *Found by TEA during test verification.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Prescribed function name `_apply_npc_observation_gate`**
  - Spec source: `.session/49-6-session.md` SM Assessment (AC enumeration)
  - Spec text: "At the start of each turn, check whether observation_pending
    NPCs are included in the new turn's npcs_present patch"
  - Implementation: Tests import a helper named `_apply_npc_observation_gate`
    from `sidequest.server.session_helpers` (parallel to `_auto_mint_prose_only_npcs`
    and `_detect_missed_recurring_npcs`). The spec does not name the helper —
    TEA picked the name to match the sibling pattern.
  - Rationale: Concrete imports must name a symbol; without a name, RED tests
    cannot fail meaningfully. Dev may rename, but tests will need a corresponding
    update if so.
  - Severity: minor
  - Forward impact: Dev can rename freely; test imports are a localized refactor.

- **Prescribed OTEL constant names `SPAN_NPC_OBSERVATION_GATE_PROMOTED` / `SPAN_NPC_OBSERVATION_GATE_PURGED`**
  - Spec source: `.session/49-6-session.md` SM Assessment
  - Spec text: "Emit OTEL span npc.observation_gate_promoted /
    npc.observation_gate_purged per decision"
  - Implementation: Tests assert the exact string values
    `"npc.observation_gate_promoted"` and `"npc.observation_gate_purged"`,
    matching the spec. Module-level constants follow the existing
    `SPAN_NPC_*` naming pattern in `sidequest/telemetry/spans/npc.py`.
  - Rationale: The string values are spec-given; the constant names follow
    catalog convention.
  - Severity: trivial
  - Forward impact: None — constant names are mechanical.

- **Wiring tests use `_apply_narration_result_to_snapshot` with `pack=None`**
  - Spec source: `sprint/epic-49.yaml` (49-2 and 49-3 sibling tests pattern)
  - Spec text: 49-2 RED file uses the same `room_for(snapshot)` + `pack=None`
    shape; 49-3 likewise.
  - Implementation: Tests bypass the genre pack to test ONLY the NPC-gate
    portion of the apply pipeline. Encounter lifecycle, magic working, and
    location-patch enforcement code paths receive `pack=None` and skip.
  - Rationale: Scoped test — the gate's correctness is independent of the
    encounter / magic / location subsystems. Full pack-loaded integration is
    expected in the Glenross-replay style integration test (deferred to
    Dev/Reviewer as the 49-2 replay test is the precedent).
  - Severity: minor
  - Forward impact: None — replay-style integration test can be added later
    in the same TDD cycle if the apply-pipeline gate needs pack-loaded
    coverage. Reviewer may request it.

### Dev (implementation)

- **Test fixture edit absorbed from testing-runner commit `d9eea39`**
  - Spec source: `tests/server/test_npc_observation_gate.py`
    (TEA RED commit `6e3d742`)
  - Spec text: Four-turn fixture used "Mother" as the role auto-minted
    in turn 7 after Father was ratified in turn 6.
  - Implementation: testing-runner replaced the role with "the constable"
    (article-role, non-gender-paired) so the auto-minter does not refuse
    the second mint under 49-2's gender-paired-conflict guard. Test
    intent (gate processes multiple pending across turns) preserved.
  - Rationale: The original fixture conflicted with 49-2's
    `_GENDER_PAIRED_ROLES` check, which correctly refuses Mother when
    Father is in pool. Two correct subsystems cannot share that fixture.
    Lane: runner should have reported and routed to Dev for the edit,
    not committed directly — captured as a Delivery Finding above.
  - Severity: minor
  - Forward impact: None — Reviewer should still validate the
    constable-substituted four-turn scenario expresses the intended AC.

### Architect (reconcile)

- **Story title scoped broader than implementation — gate restricted to
  `dialogue_extraction` provenance**
  - Spec source: `sprint/epic-49.yaml:90` (story 49-6 `title` field)
  - Spec text: "Ratification gate for narrator_invented NPCs before
    npc_registry promotion"
  - Implementation: The gate evaluates only pool members with
    `observation_pending=True`. The auto-mint flag-on-mint
    (`session_helpers.py:957`) sets the flag exclusively in
    `_auto_mint_prose_only_npcs._mint`, which is on the
    `drawn_from="dialogue_extraction"` path. The structured-patch
    `narrator_invented` mint path (`narration_apply.py:1321-1328`,
    in `_apply_npc_mentions` Step 3) creates pool members with the
    model default `observation_pending=False` — exempt from the gate.
    So the IMPLEMENTATION scopes the gate to
    `drawn_from="dialogue_extraction"` only, NOT to all
    `narrator_invented` mints.
  - Rationale: The story body and the SM Assessment AC list both
    describe the gate as a follow-up to 49-2 (the dialogue-extraction
    path), not as a guard on the structured-patch path. The narrower
    scope is also the correct behavioral choice: structured-patch
    `narrator_invented` mints are the narrator's explicit declaration
    (player saw the NPC in `npcs_present`); `dialogue_extraction`
    mints are server-side rescues from a narrator omission. Different
    trust profiles — only the rescue path needs verification. Spec-
    check Architect Assessment already flagged this as an Option-C
    spec clarification (update title, code unchanged).
  - Severity: minor (cosmetic / documentation)
  - Forward impact: The next story that touches `_apply_npc_mentions`
    Step 3 or any other `narrator_invented` provenance path should
    NOT assume the 49-6 gate covers it. If future scope wants to
    gate ALL narrator-invented entries (or any other provenance),
    the auto-mint flag-on-mint needs to be lifted into the appropriate
    site AND the gate's identity-equivalence rule needs to be
    re-evaluated against the new provenance. Title update recommended:
    `s/narrator_invented/prose-extracted/` and
    `s/npc_registry promotion/persistent pool status/`.

- **No additional deviations found beyond those logged above.**

  Reviewer's three confirmed findings (vacuous-`or` test assertion at
  test_npc_observation_gate.py:876, `>= 1` purge bound at line 945,
  "at the start" docstring framing at session_helpers.py:1074) are
  NOT deviations from spec — they are code-quality issues against
  general project standards, captured in the Reviewer Assessment with
  recommended polish patches. Per `deviation-format.md`, a deviation
  is a divergence between spec and implementation; these are
  intra-implementation polish items.

  Existing TEA and Dev deviation entries verified — all six fields
  present and substantive in each; spec sources reference real
  paths (`.session/49-6-session.md` SM Assessment, `sprint/epic-49.yaml`,
  `tests/server/test_npc_observation_gate.py`); implementation
  descriptions match the actual code state at commits `7aff04c`
  (Dev GREEN) and `2ff0d14` (TEA verify boy-scout).

  No AC deferrals to reconcile — story 49-6 has no AC accountability
  table because the epic lacked an explicit `acceptance_criteria` array
  at story-time; the AC list was derived in the SM Assessment and all
  derived ACs are addressed in code (see Architect spec-check
  Substantive AC walkthrough above).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/npc_pool.py` — added
  `observation_pending: bool = False` to `NpcPoolMember` (legacy/world
  default = False; only the 49-2 auto-minter flags new mints `True`)
- `sidequest-server/sidequest/telemetry/spans/npc.py` — added
  `SPAN_NPC_OBSERVATION_GATE_PROMOTED` (state_transition route) and
  `SPAN_NPC_OBSERVATION_GATE_PURGED` (state_transition route at
  severity=warning); plus `npc_observation_gate_promoted_span` and
  `npc_observation_gate_purged_span` context-manager helpers
- `sidequest-server/sidequest/server/session_helpers.py` —
  implemented `_apply_npc_observation_gate(*, snapshot,
  emitted_mentions, turn_num)`; one-line edit to
  `_auto_mint_prose_only_npcs::_mint` to set
  `observation_pending=True` on new mints; added the two new spans
  to the telemetry-import block
- `sidequest-server/sidequest/server/narration_apply.py` — added
  `_apply_npc_observation_gate` to the `session_helpers` import block;
  wired the gate call BEFORE `_auto_mint_prose_only_npcs` in
  `_apply_narration_result_to_snapshot` (order is load-bearing —
  documented inline)

**Tests:** 32/32 passing in `tests/server/test_npc_observation_gate.py`.
Regression sweep across `tests/server/`,
`tests/integration/test_glenross_replay_npc_auto_mint.py`, and
`tests/agents/`: 2080 passed, 25 skipped, 0 failed, 0 new failures.

**Branch:** `feat/49-6-npc-ratification-gate` in sidequest-server,
pushed to origin. Commits:
- `6e3d742` test: add failing tests for 49-6 (TEA RED)
- `d9eea39` fix(test): resolve gender-paired conflict (testing-runner
  lane crossing — see Delivery Findings)
- `7aff04c` feat(49-6): NPC ratification gate before pool persistence
  (Dev GREEN)

**Self-review:**
- [x] Code is wired through the production apply pipeline
  (`_apply_narration_result_to_snapshot` calls the gate every turn)
- [x] Code follows project patterns (sibling helpers in
  `session_helpers.py`; spans mirror `npc_recurring_presence_missed`
  pattern; gate placement mirrors 49-2 auto-mint placement)
- [x] All ACs met (model field, two OTEL spans with attrs, helper
  function with promote/purge paths, auto-mint flag-on-mint, pipeline
  wiring with correct ordering, multi-turn regression scenario)
- [x] Error handling appropriate to scope (no validation needed —
  server-internal lifecycle, no user input)
- [x] Durable retention preserved (default observation_pending=False
  means legacy snapshots, world-authored, name-generator, and
  narrator_invented-from-patch members are all exempt from the gate)
- [x] OTEL Observability Principle satisfied (both gate outcomes emit
  routed spans; purge fires at severity=warning per CLAUDE.md guidance
  for destructive ops)

**Handoff:** To Reviewer for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned with caveat — implementation matches the AC list
and story description; ONE title-vs-scope ambiguity surfaced.

**Mismatches Found:** 1 (cosmetic — title only; no code drift)

- **Story title says "narrator_invented" but gate scopes to "dialogue_extraction"**
  (Ambiguous spec — Cosmetic, Minor)
  - Spec: Story title in `sprint/epic-49.yaml:90` reads "Ratification gate
    for narrator_invented NPCs before npc_registry promotion."
    `narrator_invented` is a specific `drawn_from` value used by
    `_apply_npc_mentions` Step 3 (`narration_apply.py:1327`) when the
    narrator's *structured* `npcs_present` patch introduces a brand-new
    name.
  - Code: The gate flags only `drawn_from="dialogue_extraction"` mints
    (49-2's prose-scanner path). Structured-patch
    `narrator_invented` mints enter the pool with the model default
    `observation_pending=False` — exempt from the gate.
  - Recommendation: **C — Clarify spec.** Update the story title to
    "Ratification gate for prose-extracted NPCs before persistent
    pool status" and update the epic description accordingly. The
    narrow scope (gate the slip path, not the explicit-emission path)
    is the *correct* behavioral choice: narrator_invented entries in
    `npcs_present` are the narrator's deliberate declaration; the
    `dialogue_extraction` path is the server's catch-loop rescue from
    a narrator omission. Those have different trust profiles — only
    the rescue path needs verification.
  - Severity: Minor. No code change; documentation polish only. Already
    flagged in Dev's Delivery Findings (improvement #3, line 113).

### Substantive AC walkthrough

| AC | Implementation | Status |
|----|----------------|--------|
| Establish `observation_pending` field on `NpcPoolMember` | `npc_pool.py` — `observation_pending: bool = False` with docstring explaining default rationale | ✓ aligned |
| At start of each turn, check pending NPCs against new turn's `npcs_present` | `_apply_npc_observation_gate` at `session_helpers.py:1060`; called from `narration_apply.py:2249` BEFORE `_auto_mint_prose_only_npcs` (line 2264) | ✓ aligned |
| Promote on match (flag → False) | Lines 1116-1126 — `member.observation_pending = False; survivors.append(member)`; emits promote span | ✓ aligned |
| Purge on miss (remove from pool) | Lines 1127-1137 — purge by reconstruction (`snapshot.npc_pool[:] = survivors`); emits purge span | ✓ aligned |
| OTEL spans for both decisions | `spans/npc.py` adds two `SPAN_NPC_OBSERVATION_GATE_*` constants with `SpanRoute` entries (state_transition / npc_registry); purge fires at severity=warning | ✓ aligned |
| Regression test: turn-sequence fixture (turn 5 Father, turn 6 use, turn 7 Mother, turn 8 drop) | `test_glenross_four_turn_sequence_father_survives_mother_purged` — turn-7 mint role swapped from "Mother" to "the constable" by testing-runner (commit `d9eea39`) to circumvent 49-2's gender-paired-conflict block. Test intent (gate processes multiple pending across turns) is preserved | ✓ aligned (with subscope deviation logged) |

### Pattern compliance

- **Reuse-first.** Implementation reuses the existing
  `_auto_mint_prose_only_npcs` / `_detect_missed_recurring_npcs` sibling
  pattern. Identity-equivalence rule (case-folded name OR role match)
  mirrors the same dedup logic at `session_helpers.py:921-927`. The
  gate is a small symmetric counterpart — no new infrastructure.
- **OTEL Observability Principle.** Both gate outcomes emit routed
  spans with role + name + turn_number attributes. Purge is
  severity=warning per the destructive-op convention
  (`npc_recurring_presence_missed_span` precedent).
- **No silent fallbacks.** No silent skip paths in the gate — every
  pending member produces exactly one span (promote XOR purge).
- **Durable retention.** Default `observation_pending=False` means
  legacy snapshots, world-authored, name-generator, and
  narrator-invented-from-patch members are all immune. Round-trip
  serialization test (`test_npc_pool_member_observation_pending_round_trips_through_serialization`)
  confirms the flag survives save/load.

### Ordering invariant verification

Read `narration_apply.py:2222-2275`. Order of NPC operations:

1. `_apply_npc_mentions` (line 2223) — process narrator's structured
   `npcs_present`; mark `Npc.last_seen_turn`; upsert identity fields on
   pool_hit (does NOT modify `observation_pending`); Step 3 creates
   `narrator_invented` pool members with `observation_pending=False`
2. `_detect_missed_recurring_npcs` (line 2233) — warn-only
3. `_apply_npc_observation_gate` (line 2249) — 49-6 gate; sees
   prior-turn pending members AFTER mentions have done identity
   upsert, ratifies based on this turn's mention contents
4. `_auto_mint_prose_only_npcs` (line 2264) — fresh mints from prose;
   sets `observation_pending=True` for next turn's gate

The gate position is correct. If a pending member is cited by name in
`npcs_present` this turn, Step 2 of `_apply_npc_mentions` upserts
identity fields (without touching the flag), THEN the gate flips the
flag to False and emits promote. Both side-effects compose cleanly.

### Cross-finding adjudication

- **TEA Question (one-turn window)** — story scope explicitly says
  one turn. Future-extension to N-turn countdown is straightforward
  (`bool` → `int`) but out of scope here. Defer to a follow-up story
  IF the playgroup reports the one-turn window is too aggressive.
- **TEA Question (pool flag flip vs Npc promotion)** — resolved by
  implementation. The gate operates on `NpcPoolMember.observation_pending`
  only; `_promote_pool_member_to_npc` (the heavier Npc construction)
  remains gated on mechanical engagement. This is the correct
  interpretation; no rework needed.
- **TEA Gap (epic AC absent)** — confirmed. Story metadata
  (`sprint/epic-49.yaml:88-91`) lacks the AC array that 49-1/49-2/49-3
  carry. Recommendation: Reviewer / SM populate the AC field at
  finish, or accept the derived AC list as authoritative for archival.
- **Dev Conflict (testing-runner lane crossing)** — substantive issue
  with subagent governance; out of 49-6 scope but worth a separate
  process story. The fixture edit itself is sound; commit `d9eea39`
  stays in the branch.
- **Dev Improvement #2 (49-2 paired-conflict guard rigidity)** —
  legitimate future-story candidate. The 49-2 guard cannot tell
  same-turn slip from later-turn legitimate introduction. The 49-6
  gate could in principle relax the guard for ratified entries.
  Defer.

**Decision:** Proceed to TEA verify. The one mismatch is title-only,
no code rework needed; Dev's Improvement #3 already proposes the title
correction in the Delivery Findings for the boss to action.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (32/32 target + 2080 regression sweep; one
simplify fix applied; no regression after fix)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5 (npc_pool.py, narration_apply.py, session_helpers.py,
spans/npc.py, test_npc_observation_gate.py)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | findings (4) | 1 high (casefold dedup across 3 functions), 2 medium (span helper, test fixtures), 1 low (defensive casefold pattern) |
| simplify-quality | findings (4) | 1 high (redundant `json` import in build_secret_note_events), 2 medium (type annotations on legacy helpers), 1 low (weak `or` assert in test) |
| simplify-efficiency | clean | No findings |

**Applied:** 1 high-confidence fix
- `session_helpers.py:76` — removed redundant local `import json` inside
  `build_secret_note_events` (module-level `import json` at line 14 already
  covers `json.dumps` usage at line 97). Bounded boy-scout fix in a file
  already touched by 49-6. Committed as `2ff0d14`.

**Flagged for Reviewer (not auto-applied):**

- **(medium-conf reuse)** Casefold-set-building pattern duplicated across
  `_detect_missed_recurring_npcs`, `_auto_mint_prose_only_npcs`, and the
  new `_apply_npc_observation_gate`. Reuse agent flagged HIGH, but on
  closer inspection the three sites build DIFFERENT scopes (the gate
  builds just-mentions; auto-mint builds mentions+npcs+pool superset;
  detect-recurring builds yet another shape). Extracting a single helper
  would either undershoot (leave the others untouched) or require a
  three-function refactor outside 49-6 scope. Flag for a dedicated
  cleanup story if the pattern is touched again.
- **(medium-conf reuse)** `npc_observation_gate_promoted_span` and
  `npc_observation_gate_purged_span` share signature structure with
  only `severity` differing. Could be parameterized into one factory.
  Declined: matches the existing 49-2 pattern of distinct mint vs skip
  span helpers (`npc_auto_minted_from_prose_span` vs
  `npc_auto_mint_skipped_span`) — keeping a parallel shape across the
  bundle reads better than introducing an outlier factory.
- **(medium-conf reuse)** Test helper duplication with
  `test_npc_auto_mint_from_prose.py`. Declined: extracting a shared
  `tests/_helpers/npc_fixtures.py` is a test-org refactor that should
  be its own story; the duplication is small.
- **(medium-conf quality)** `build_secret_note_events.removed: list`
  and `emit_secret_notes.secret_routes: list` lack element types.
  Declined: pre-existing in code outside 49-6 surface; flag as
  follow-up.
- **(low-conf quality)** Four-turn test asserts
  `names_after == {"Father", "Reverend Murchison"} or names_after ==
  {"Father"}`. The `or` branch is unreachable given the test only calls
  the gate (not `_apply_npc_mentions`) on turn 8. Reviewer may choose
  to tighten to just `{"Father"}`. Not auto-applied per low-confidence
  rule.

**Noted:** 1 low-confidence observation (defensive casefold pattern
in `member.name.casefold() if member.name else ""`). Acceptable as-is.

**Reverted:** 0

**Overall:** simplify: applied 1 high-confidence fix (redundant import).
All other findings flagged for reviewer judgment; no other auto-applied
edits. No regression detected (ruff clean, pyright baseline preserved,
67 targeted tests pass).

**Quality Checks:** ruff clean on changed file; pyright at pre-existing
mid-port baseline (no fresh errors); 32/32 target tests + 35 sibling
49-2 tests + full regression sweep all pass.

**Handoff:** To Reviewer for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (ruff PASS, pyright 0 new errors over pre-port baseline, 67 tests pass, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (2 high, 2 medium, 1 low) | confirmed 2, deferred 2, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (high) | confirmed 1 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (3 high, all post-triage downgraded) | confirmed 0, dismissed 3 |

**All received:** Yes (4 enabled subagents returned; 5 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 3 confirmed (1 test-assertion tightening, 1 wiring-test bound tightening, 1 docstring correction), 2 deferred (low-value test additions), 4 dismissed (with rationale)

### Confirmed findings

**[TEST] Vacuous `or` branch in four-turn regression test**
- File: `tests/server/test_npc_observation_gate.py:876`
- Detail: `assert names_after == {"Father", "Reverend Murchison"} or names_after == {"Father"}` — the second branch is unreachable. The turn-8 setup only calls `_apply_npc_observation_gate` (no `_apply_npc_mentions`), so "Reverend Murchison" cannot enter the pool from this turn's mentions alone. The OR hides the unreachable state and weakens regression detection.
- Confirmed by: simplify-quality (low-conf), reviewer-test-analyzer (high-conf). Already flagged in TEA verify assessment.
- Severity: Minor (test tightness; not behavior)
- Recommendation: Tighten to `assert names_after == {"Father"}`.

**[TEST] Wiring test purge-count assertion too loose**
- File: `tests/server/test_npc_observation_gate.py:945` (test_apply_narration_result_invokes_observation_gate)
- Detail: `assert len(purges) >= 1` permits >1 purges to slip through. The narration text contains "Reverend Murchison" which would normally trigger `_HONORIFIC_PROPER_RE` in auto-mint, but is deduped because the same name is in `emitted_mentions`. If that dedup ever regresses, a stray auto-mint of Reverend Murchison could trigger an extra purge (or other side effect) and the loose bound would mask it.
- Severity: Minor (regression-detection tightness)
- Recommendation: Tighten to `assert len(purges) == 1`.

**[DOC] Gate docstring misrepresents pipeline position**
- File: `sidequest/server/session_helpers.py:1074` (in `_apply_npc_observation_gate` docstring)
- Detail: Docstring says "This gate runs once at the start of every narration-apply turn, BEFORE the auto-minter scans this turn's prose." The "at the start" framing is wrong — the gate is the THIRD NPC operation in `_apply_narration_result_to_snapshot`, after `_apply_npc_mentions` (line 2223) and `_detect_missed_recurring_npcs` (line 2233). The load-bearing claim (BEFORE auto-minter) is correct; the relative-to-pipeline framing is misleading.
- Severity: Minor (documentation clarity)
- Recommendation: Change "at the start of every narration-apply turn" → "after NPC mention registration and recurring-presence detection, BEFORE the auto-minter scans this turn's prose."

### Deferred findings (test additions, low-value)

- **[TEST] Missing double-match edge case** — no test verifies that a pool member matched BOTH by name AND role in the same mention emits exactly one promote span. Implementation uses `or` so a double-match short-circuits at the first hit; no double-emit possible without a structural change. Defer — low-conf finding from reviewer-test-analyzer, not load-bearing.
- **[TEST] Parametrized test_gate_ignores_non_dialogue_extraction_when_non_pending exercises same code path 4x** — reviewer-test-analyzer flagged as duplicate-input parametrize; reviewer-rule-checker accepted same parametrization as "valid boundary test." Defer — the parametrization is a forward-looking guard: if a future story extends gate scope to other `drawn_from` provenances, the test will need to differentiate. Cost of keeping is trivial; cost of collapsing then re-expanding later is higher.

### Dismissed findings (with rationale)

- **[TEST] hasattr-only field test is redundant** (reviewer-test-analyzer, medium-conf) — DISMISSED. The `test_npc_pool_member_has_observation_pending_field` test is intentionally a separate existence-check from the default-value test (which would also fail if the field were absent, but with a less specific error message). The hasattr test produces a more diagnostic failure message ("field missing — add `observation_pending: bool = False` to ...") that aids debug. Keeping.
- **[RULE-10] npc.py has no `__all__`** (reviewer-rule-checker, high-conf) — DISMISSED. `sidequest/telemetry/spans/__init__.py` uses wildcard `from .npc import *` (line 63) — this is the established pattern across ALL spans/ submodules. No spans/ submodule defines `__all__`. Adding one to `npc.py` only would create an outlier. The architectural choice is intentional and pre-existing. Refactoring the whole spans/ subdirectory is out of 49-6 scope.
- **[RULE-3] `_mention()` test helper missing return annotation** (reviewer-rule-checker, high-conf) — DISMISSED. Rule-checker text claimed "`_mention` has no underscore prefix." This is false — `tests/server/test_npc_observation_gate.py:117` reads `def _mention(name: str = "", role: str = "") -> NpcMention:` — the helper HAS both an underscore prefix AND a `-> NpcMention` return annotation. Hallucinated finding.
- **[RULE-13] Missing blank lines between four-turn test and wiring test (claimed E302)** (reviewer-rule-checker, high-conf) — DISMISSED as a hard rule violation. Ruff lint passes (`uv run ruff check tests/server/test_npc_observation_gate.py` → "All checks passed!"); this project's ruff config does not enable E302. The blank-line gap is a cosmetic byproduct of the testing-runner's gender-pair fixture fix in commit `d9eea39` (which removed the "Group F" section header). Not a lint failure; minor style polish at most.

## Reviewer Assessment

**Verdict:** **APPROVED with non-blocking polish recommendations.**

**Specialist coverage incorporated:** findings tagged [TEST] (from
reviewer-test-analyzer), [DOC] (from reviewer-comment-analyzer), and
[RULE] (from reviewer-rule-checker — all three dismissed with rationale
in the Dismissed section above; rule-checker also independently confirmed
the [TEST] vacuous-`or` finding via Rule #6 cross-check).

**Summary:** The 49-6 implementation is correct, well-tested, properly
wired through the production apply pipeline, OTEL-instrumented per
project doctrine, and preserves durable-retention defaults for legacy
and world-authored pool members. Preflight is clean across the board
(ruff PASS, pyright no new errors, 67/67 targeted tests pass). The
ratification gate solves the 2026-05-11 Glenross false-positive
failure mode at the correct pipeline position with the correct
ordering invariant (before auto-mint, after mention registration).

**Three minor polish items surfaced**, all non-blocking:

1. Tighten `tests/server/test_npc_observation_gate.py:876` `or`-disjunction
   assertion to a single expected set.
2. Tighten `tests/server/test_npc_observation_gate.py:945` `>= 1` purge
   count to `== 1`.
3. Correct `_apply_npc_observation_gate` docstring at
   `sidequest/server/session_helpers.py:1074` — the gate is the third NPC
   operation, not the first.

None of these affect runtime behavior, gameplay correctness, OTEL
fidelity, durable retention, or test coverage of the load-bearing
behaviors. Per `feedback_just_fix_it`, these are small enough that
a single fix-up commit on this branch is cleaner than carrying them
as TODOs.

**Recommendation to SM:** Request a small Dev rework commit for the
three confirmed findings, then finish. If project tempo doesn't allow,
finish as-is — none are blockers and all are captured in Delivery
Findings for archival.

### Rule Compliance Summary

Per `.pennyfarthing/gates/lang-review/python.md` 13 checks, exhaustively
verified by reviewer-rule-checker across 74 code instances:

| Rule | Status |
|------|--------|
| #1 Silent exceptions | Clean (5 instances) |
| #2 Mutable defaults | Clean (5 instances) |
| #3 Type annotations | Clean (8 instances; one false-positive dismissed) |
| #4 Logging coverage/severity | Clean (6 instances; promote=info, purge=warning correct) |
| #5 Path handling | N/A (no path ops) |
| #6 Test quality | Clean (29 instances; one `or`-branch flagged separately) |
| #7 Resource leaks | Clean (4 instances; all `with` context managers) |
| #8 Unsafe deserialization | N/A (no pickle/yaml/eval/exec) |
| #9 Async pitfalls | N/A (no async functions) |
| #10 Import hygiene | Clean (7 instances; `__all__` dismissed as project pattern) |
| #11 Input validation | Clean (Pydantic + None-guards) |
| #12 Dependency hygiene | Clean (no pyproject.toml change) |
| #13 Fix regressions | Clean (5 instances; verify-phase boy-scout commit re-checked) |

Project rules from CLAUDE.md / SOUL.md:
- **OTEL Observability Principle:** ✓ promote + purge both emit routed
  spans with severity=warning on purge
- **No Silent Fallbacks:** ✓ no swallowed errors; gate decisions are
  explicit branches
- **Verify Wiring, Not Just Existence:** ✓ two wiring tests cover both
  the gate-runs and the gate-runs-BEFORE-automint contracts
- **Durable retention:** ✓ default `observation_pending=False`
  preserves legacy/world-authored/name-generator/narrator-invented
  exemption

**Decision:** Proceed. Optional: Dev applies three polish items as a
single fix-up commit before SM finish.

**Handoff:** To SM for finish (with optional Dev fix-up loop).

## Context

**Epic Context (49):** Playtest 4 Closeout — Glenross / ADR-098 Continuity Recovery

The 2026-05-11 victoria/glenross playtest revealed narrative-continuity regressions from ADR-098 (stateless narrator turns, dropping --resume). ADR-098 delivered the speed win (turns now 14-20s instead of 60s+) but introduced:
1. Narrator teleports the scene by titling a new room without filling the structured location patch (49-3, completed)
2. Recent narrative facts drop between turns (49-1, completed)
3. **Dialogue-only NPCs never get extracted to the NPC roster** (49-2, completed)
4. Victoria archetypes have no starting_inventory (49-4, backlog)

**Story 49-6 Context:**

This story is the **ratification gate** that prevents false positives from dialogue-only NPC references after story 49-2 auto-mints NPCs from prose. Story 49-2 established the server-side catch-loop to scan narration prose for named individuals and auto-mint `NpcPoolMember` entries when the narrator's structured `npcs_present` patch omits them.

However, 49-2's auto-mint is **fire-and-forget**: if the narrator mentions "Father" in dialogue but never actually uses him again (a one-off reference, dialogue filler, or narrative aside), the NPC gets pinned to the registry indefinitely. This is the "false positive" problem — the roster fills with phantom NPCs that only existed in that one turn's prose.

**The fix:** Add a one-turn observation gate. Auto-minted NPCs must survive one complete turn in the current_npc_pool *without being dropped* before being promoted to the persistent `npc_registry`. If the narrator drops an auto-minted NPC in the follow-up turn (doesn't include it in the next turn's `npcs_present`), purge it. If it persists, promote it.

**Acceptance Criteria (from epic-49.yaml line 90-96):**

The epic does not spell out detailed AC. From the story context and pattern:

- Establish an `observation_pending` status on `NpcPoolMember` — when an NPC is auto-minted, mark it `observation_pending=True`
- At the start of each turn, check whether `observation_pending` NPCs are included in the new turn's `npcs_present` patch
- If included (survived one turn), promote `observation_pending=False` → persistent
- If dropped (absent from the new turn), purge from `npc_pool` entirely
- Emit OTEL span `npc.observation_gate_promoted` / `npc.observation_gate_purged` per decision
- Regression test: fixture turn sequence where turn 5 auto-mints Father, turn 6 uses him (survive + promote), turn 7 auto-mints Mother, turn 8 drops Mother (purge)

## Ownership
- **Lead Dev:** (self-assigned on claim)
- **Workflow Type:** Phased (TDD)
- **Estimated Duration:** 5 points (~8-10 hours focused work)

---

## Sm Assessment

**Scope:** Add one-turn observation gate between 49-2's auto-mint and persistent `npc_registry`. Server-only change in `sidequest-server`. No protocol changes expected (purely server-side lifecycle on `NpcPoolMember`).

**Loaded vs research:** Loaded. 49-2 (auto-mint), 49-1 (recent-fact retention), and 49-3 (location patch enforcement) have all shipped, so the surrounding plumbing exists. TEA can read `npcs_present` patch handling and `NpcPoolMember`/`npc_registry` code paths to derive the AC into concrete test cases. The AC list in story context covers the four lifecycle transitions plus OTEL plus the regression fixture turn sequence.

**OTEL discipline:** Per project doctrine, both `npc.observation_gate_promoted` and `npc.observation_gate_purged` spans are first-class deliverables — GM panel needs to see the gate firing, not just trust that it does. TEA: include OTEL emission assertions in the RED tests.

**Risk:** Low. Scoped, server-only, no concurrency surface (turn-boundary state machine). The only judgment call is whether "survived one turn" means "present in the NEXT turn's `npcs_present`" or "present at end of NEXT turn after all patches resolve" — TEA should pick the simpler reading (next turn's patch contains the NPC) and flag in Delivery Findings if research suggests otherwise.

**Pre-handoff checklist:**
- [x] Session file exists and is populated
- [x] Workflow + phase set (tdd / setup)
- [x] Context written (epic + story, with AC enumerated)
- [x] Branch created on subrepo (`feat/49-6-npc-ratification-gate` in sidequest-server)
- [x] Jira: N/A per project policy (no Jira)

Handoff: TEA (RED phase).

---

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5pt TDD story with behavioral surface (model field, OTEL spans,
new helper, pipeline wiring). Pure mechanical/lifecycle work that benefits
from comprehensive RED coverage.

**Test Files:**
- `sidequest-server/tests/server/test_npc_observation_gate.py` — 32 tests
  across 6 groups (model fields, OTEL catalog, auto-mint wiring, gate
  evaluation unit, multi-turn regression, pipeline wiring).

**Tests Written:** 32 tests covering 6 ACs (model field, OTEL spans,
gate evaluation, auto-mint flag-on-mint, regression scenario, pipeline
wiring). The story's "regression test" AC is satisfied by the
`test_glenross_four_turn_sequence_father_survives_mother_purged` fixture
plus the two two-turn subsets.

**Status:** RED (32/32 failing — ImportError / AttributeError /
ValidationError on the unimplemented symbols; zero unexpected passes;
zero collection errors)

### Rule Coverage

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`)
— applicable rules:

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 logging — error paths with severity | `test_gate_purge_emits_observation_gate_purged_span` asserts severity='warning' indirectly via the SpanRoute pattern (route attrs match `npc_recurring_presence_missed_span` precedent) | failing |
| #6 test quality — no vacuous assertions | Self-check pass: every test has at least one specific-value assertion; no `assert True`, no `assert result` truthy-only checks, no `let _ =` equivalents. Empty-pool no-op test (`test_gate_empty_pool_is_noop`) asserts `snapshot.npc_pool == []` AND that no spans fired — both specific. | failing |
| #11 input validation at boundaries | Not applicable — gate is server-internal, no user input | n/a |
| Project: OTEL Observability Principle (CLAUDE.md) | `test_gate_promote_emits_observation_gate_promoted_span`, `test_gate_purge_emits_observation_gate_purged_span` enforce that both gate outcomes emit auditable spans | failing |
| Project: "Every Test Suite Needs a Wiring Test" (CLAUDE.md) | `test_apply_narration_result_invokes_observation_gate` + `test_apply_narration_result_runs_gate_before_auto_mint` verify the gate is called from production code paths, not just unit-testable in isolation | failing |
| Project: "Verify Wiring, Not Just Existence" (CLAUDE.md) | Same pair as above — wiring tests target the production caller (`_apply_narration_result_to_snapshot`), not a fake test-only entry point | failing |
| Project: No silent fallbacks (CLAUDE.md) | `test_gate_does_not_touch_non_pending_members` asserts NO span fires for non-pending members (silent-skip variant of fallback) | failing |
| Project: durable retention (memory note) | `test_npc_pool_member_observation_pending_default_is_false`, `test_auto_mint_preserves_unrelated_pool_members_observation_state`, `test_gate_ignores_non_dialogue_extraction_when_non_pending` (parametrized 4x) guard that world-authored / legacy / non-prose NPCs are NEVER purged | failing |

**Rules checked:** 7 of 13 applicable lang-review + project rules have
test coverage. Remaining rules (#1 silent exceptions, #2 mutable defaults,
#3 type annotations, #5 path handling, #7 resource leaks, #8 unsafe deser,
#9 async pitfalls, #10 import hygiene, #12 dep hygiene) are
implementation-time concerns for Dev's code, not test-design concerns —
they are enforced by Reviewer's lang-review gate at green-exit.

**Self-check:** Zero vacuous tests. Every assertion has a concrete
expected value or a structural shape claim. No `assert True`, no
`is_some()` without value-check, no `let _ = result`.

### Test Strategy Notes

1. **One-turn observation window** is hardcoded into the gate contract.
   If product decides on a 2- or 3-turn observation window later,
   ``NpcPoolMember.observation_pending: bool`` becomes
   ``observation_pending: int`` (countdown) and the gate body re-orchestrates,
   but the test surface stays valid for the boolean shape.

2. **Match semantics** — casefold name OR casefold role. Tests cover all
   three positive paths (name match, role match, casefold match) and the
   negative path (no match → purge). The match-strategy mirrors the
   `known_names / known_roles` dedup in `_auto_mint_prose_only_npcs`
   (line 921-927 of session_helpers.py) so the two paths use the same
   identity-equivalence rule.

3. **Ordering invariant** — gate must run BEFORE auto-mint in the apply
   pipeline. `test_apply_narration_result_runs_gate_before_auto_mint`
   establishes this constraint with a fixture where the wrong order
   would cause a same-turn self-cancellation.

4. **OTEL contract** — distinct routes for promote and purge so the GM
   panel can show them as separate streams (parallel to
   `auto_minted_from_prose` vs `auto_mint_skipped` from 49-2). Required
   attributes: `npc_name`, `role`, `turn_number`.

5. **Serialization round-trip** — explicit test that
   `model_dump → model_validate` preserves `observation_pending`. Without
   this assertion, the gate could silently break across save/load cycles
   (Pydantic field-exclusion flags would mask the bug).

### What Dev Needs to Build (RED-to-GREEN map)

1. `sidequest/game/npc_pool.py` — add
   `observation_pending: bool = False` to `NpcPoolMember`.

2. `sidequest/telemetry/spans/npc.py` — add two `SPAN_*` constants,
   two `SpanRoute` entries, two context-manager helpers
   (`npc_observation_gate_promoted_span`,
   `npc_observation_gate_purged_span`). Pattern: copy
   `npc_auto_minted_from_prose_span` block (lines 118-131 and 328-364).

3. `sidequest/server/session_helpers.py` — implement
   `_apply_npc_observation_gate(*, snapshot, emitted_mentions, turn_num)`.
   Iterate `snapshot.npc_pool`; for each `observation_pending=True`
   member, check if its casefolded name OR casefolded role appears in
   any `emitted_mentions` element's `.name` or `.role` field. Promote
   (flip flag to False) on match; purge (remove from list) on miss.
   Emit the corresponding OTEL span per decision. New members from
   this turn's narration are NOT processed (auto-mint runs after the
   gate per pipeline ordering).

4. `sidequest/server/session_helpers.py::_auto_mint_prose_only_npcs` —
   one-line change: append `observation_pending=True` to the
   `NpcPoolMember(...)` kwargs at line 949 (the `_mint` inner function).

5. `sidequest/server/narration_apply.py::_apply_narration_result_to_snapshot` —
   add a call to `_apply_npc_observation_gate(snapshot=snapshot,
   emitted_mentions=list(result.npcs_present), turn_num=turn_num)`
   BEFORE the `_auto_mint_prose_only_npcs` call (around line 2246).
   Import the helper alongside the existing
   `_auto_mint_prose_only_npcs` / `_detect_missed_recurring_npcs` /
   `_detect_npc_identity_drift` import block.

### Files Expected to Change in GREEN

```
sidequest/game/npc_pool.py
sidequest/telemetry/spans/npc.py
sidequest/server/session_helpers.py
sidequest/server/narration_apply.py
```

No `sidequest/protocol/`, `sidequest/agents/`, or UI changes —
server-internal lifecycle change.

**Handoff:** To Dev for implementation (GREEN phase). RED commit:
`6e3d742 test: add failing tests for 49-6 NPC observation gate`
on branch `feat/49-6-npc-ratification-gate` in sidequest-server.

---

**Session created:** 2026-05-12 10:30 UTC
**Branch:** feat/49-6-npc-ratification-gate (sidequest-server)