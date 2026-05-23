---
parent: context-epic-61.md
workflow: tdd
---

# Story 61-7: Unify _npc_in_scene predicate with list_npcs_in_scene scene resolution

## Business Context

The 2026-05-23 cost-runaway incident's structural fix (epic 61) introduced
per-field snapshot projections under story 61-2, including an `_npc_in_scene`
predicate at `sidequest-server/sidequest/server/session_helpers.py:84-117`.
The 61-2 verify-phase added an adversarial probe
(`test_npc_in_scene_predicate_divergence_from_list_npcs_in_scene_tool` in
`sidequest-server/tests/server/test_61_2_snapshot_seven_field_projection.py`)
that **measured a real divergence** between two scene-resolution sites:

- `_npc_in_scene` (the new 61-2 projection predicate) — uses
  `Npc.last_seen_location` only, plus encounter actor membership.
- `list_npcs_in_scene.py:102` (the existing tool the narrator calls
  in-loop to enumerate present NPCs) — uses `Npc.current_room` /
  `Npc.location`.

Three NPC fields currently signal scene membership: `last_seen_location`,
`current_room`, `location`. Narrator prose paths update `last_seen_location`
on observation; structured-state paths (encounter resolution, world
patches) may set `current_room` / `location` and leave `last_seen_location`
stale. The probe constructed an NPC where these diverge and confirmed
the snapshot projection and the tool reach different verdicts on whether
the NPC is "in scene."

This is a **silent-correctness bug** for the narrator's lie-detector
posture: the snapshot the narrator sees says NPC X is present, while
the tool the narrator can call says NPC X is absent. The two sources
of ground truth disagree. ADR-014's diamonds-and-coal discipline and
the narrator-gaslighting doctrine (`project_narrator_gaslighting_doctrine`
memory) both depend on a single coherent ground-truth surface. The
divergence is the precondition for confabulation regressions that
cannot be diagnosed by OTEL because both sources individually report
"correct per their own contract."

**Also a prerequisite for 61-5.** The architecture-gate story (61-5)
introduces a `_PHASE_C_PROJECTIONS` registry that the gate test reflects
over. Encoding `_npc_in_scene` into that registry while it diverges
from `list_npcs_in_scene` would freeze a known divergence into the
architecture's named contract. 61-7 unifies first; 61-5 codifies the
unified shape.

## Technical Guardrails

**Key files to modify:**

- `sidequest-server/sidequest/server/session_helpers.py:84-117` —
  `_npc_in_scene(npc, snapshot, *, current_room)`. The 61-2 predicate.
  Currently consumes `getattr(npc, "last_seen_location", None)` and
  the unresolved-encounter actor list.
- `sidequest-server/sidequest/agents/tools/list_npcs_in_scene.py:102` —
  the tool-side scene resolution. Consumes `current_room` / `location`
  on the NPC.
- `sidequest-server/sidequest/game/session.py` — `Npc` model definition
  (location of the three competing fields).

**Folded-in cleanups from 61-2 review-fix deferrals** (per
`sprint/archive/61-2-handoff-implement.md` §"Out-of-scope (deferred to
61-7)"):

- `_npc_in_scene` parameter annotation: `npc: object` → `npc: Npc`
  (drop the `object` annotation that exists only because the predicate
  was written to avoid a circular import).
- Eliminate `payload["npcs"] = []` / `payload["room_states"] = {}`
  noise — when the projection runs to completion with zero in-scene
  NPCs or zero matching rooms, the empty-collection assignment is
  cosmetic noise. The structural-anchor argument doesn't apply when
  pydantic's `exclude_defaults` already drops empty collections.
- Adversarial-probe fixture NIT (small cleanup in
  `test_npc_in_scene_predicate_divergence_from_list_npcs_in_scene_tool`
  flagged in 61-2 verify-phase notes).

**Design pattern to follow — single named predicate:**

Extract a single module-level function (likely
`is_npc_in_scene_for_perspective(npc: Npc, *, current_room: str | None,
encounter: StructuredEncounter | None) -> bool`) that:

1. Lives somewhere both call sites can import without circular-import
   pain. Candidates: a new `sidequest/game/npc_scene.py` module, or
   inside `sidequest/game/npc_pool.py` if the import graph allows.
   `session_helpers.py` and `tools/list_npcs_in_scene.py` both depend
   on the `Npc` model already, so co-locating with `Npc` definition
   (`session.py`) is the natural home if no circularity emerges.
2. Resolves all three NPC fields with a **single documented precedence
   order**. Recommendation (subject to red-phase verification):
   `current_room` > `location` > `last_seen_location`, with the first
   non-None value winning. Reasoning: structured-state writes are
   higher-trust than narrator-prose observations; if encounter
   resolution wrote `current_room`, that's the authoritative location.
3. Adds the encounter-actor membership branch (carried over from
   `_npc_in_scene`) so an NPC participating in an unresolved structured
   encounter is "in scene" even if their location field is stale.

**Both call sites import and consume the unified predicate.** No
duplicate logic. The 61-2 adversarial-probe test should change shape
(or get a follow-on companion test) to assert **convergence** rather
than measuring divergence — the contract flips from "measure the bug"
to "guard the fix."

**OTEL:** the existing `prompt.game_state.bytes` span already carries
`npcs_dropped`. After unification, the count should remain accurate
under both the old (last_seen_location-only) and the new (precedence)
resolution; the test contract is that span attributes stay
load-bearing.

**No source-text wiring tests** (sidequest-server CLAUDE.md "No
Source-Text Wiring Tests" rule). Tests must drive behavior through the
real call paths or use pydantic reflection — not grep production source
for the predicate name.

## Scope Boundaries

**In scope:**

- Extract the unified scene-resolution predicate to a single named
  function with a documented field-precedence order.
- Update `session_helpers.py:_npc_in_scene` to delegate to the unified
  predicate (or be replaced by it).
- Update `tools/list_npcs_in_scene.py:102` to delegate to the unified
  predicate.
- Update or replace the 61-2 divergence-probe test to assert
  convergence post-fix.
- 61-2 deferral cleanups: `npc: object` → `npc: Npc` annotation;
  remove empty-collection noise assignments; probe-fixture NIT.
- Wiring test (per repo CLAUDE.md): at least one integration test
  proving both call sites consume the same predicate.

**Out of scope:**

- Reconciling the three NPC fields into one (deleting
  `last_seen_location`, or `location`, or `current_room`). The fields
  serve different write paths and ownership domains; merging them is
  an ADR-shaped decision, not a 2pt refactor.
- ADR-053 belief/clue gossip propagation refactor.
- The `_PHASE_C_PROJECTIONS` registry — that belongs to 61-5 and
  depends on this story landing.
- Any change to `npc_pool` seeding semantics — gaslighting-doctrine
  anchor stays as-is.
- Changes to encounter actor model (`StructuredEncounter.actors`).

## AC Context

**AC-1: Single named predicate exists, both call sites import it.**

A new module-level function (e.g.,
`sidequest.game.npc_scene.is_npc_in_scene_for_perspective` — exact
module placement is a red-phase decision) is the only place
scene-membership resolution logic lives. `session_helpers.py` and
`tools/list_npcs_in_scene.py` both import and call it. No duplicate
logic. Test verifies via Python import / call-graph reflection or by
constructing a fixture that exercises both call sites and asserts they
reach the same verdict.

**AC-2: Field-precedence order is documented and load-bearing.**

The unified predicate consults the three NPC location fields in a
single documented order (recommendation: `current_room` > `location`
> `last_seen_location`). A test exercises the precedence — an NPC
with conflicting values across the three fields resolves to the
highest-precedence non-None value. The 61-2 divergence-probe scenario
(NPC with `last_seen_location="main_hall"` but `current_room="distant_chamber"`)
flips outcome to the precedence winner, not the old `last_seen_location`-only
verdict.

**AC-3: Encounter-actor membership branch preserved.**

NPCs named in an unresolved `StructuredEncounter.actors[*].name` are
"in scene" regardless of their location-field state. The 61-2
predicate carried this branch; the unified predicate must keep it.
Test: encounter actor named "X" with all three location fields set to
some `other_room` resolves to "in scene" via the encounter branch.

**AC-4: Divergence probe flips contract from "measure" to "guard."**

`test_npc_in_scene_predicate_divergence_from_list_npcs_in_scene_tool`
(currently asserts the two paths disagree) is either rewritten to
assert convergence, or paired with a companion test that asserts
post-unification both call sites agree on every fixture. The
"measure divergence" framing must not persist past this story — that
test's success becomes a regression indicator post-fix.

**AC-5: Folded-in cleanups land.**

- `_npc_in_scene` (or its replacement) annotates `npc: Npc`, not
  `npc: object`. Pyright check confirms no circular-import regression
  from the annotation change.
- Empty-collection assignments (`payload["npcs"] = []` /
  `payload["room_states"] = {}`) removed where they're cosmetic noise.
  Tests verify the projection's contract is unchanged (consumer sees
  the same payload shape when collections are genuinely empty —
  either the key is absent OR the empty collection sits there; pick
  one and document it).
- Adversarial-probe fixture NIT addressed (small cosmetic cleanup
  flagged in 61-2 verify notes).

**AC-6: Wiring test (CLAUDE.md mandate).**

At least one integration test drives a real call path — synthesize a
snapshot fixture, fire `_build_turn_context` (the
`session_helpers.py` consumer) AND fire the `list_npcs_in_scene` tool
through its registry registration, assert both reach the same verdict
on the same NPCs. Tests pure helper functions in isolation are not
sufficient (repo rule: "Every Test Suite Needs a Wiring Test").

**AC-7: No regression on 61-2's projection counts.**

`prompt.game_state.bytes` span continues to carry accurate
`npcs_dropped` after the predicate change. The 61-2 tests
(`test_61_2_snapshot_seven_field_projection.py`) all still pass,
modulo the divergence-probe rewrite in AC-4.

**AC-8: Full server suite green; no source-text wiring tests added.**

`uv run pytest -n auto` passes with the new tests. Any test added by
this story drives behavior, not source text. Grep verification: no
new test reads `session_helpers.py` or `list_npcs_in_scene.py` source
text as a wiring assertion.

## Assumptions

- **The three NPC location fields are the only scene-resolution signals.**
  If a fourth signal exists (e.g., a `scene_membership: set[str]` field
  on a higher-level scene object that I haven't surveyed), red-phase
  will surface it and the precedence order needs expansion.
  *Verification:* TEA red-phase greps `Npc.` field accesses across
  the agents/server/game packages.
- **`current_room` > `location` > `last_seen_location` is the right
  precedence.** Based on write-path trust hierarchy
  (structured-state writes are higher-trust than narrator-prose
  observations). If the codebase has a contrary convention (e.g.,
  some writer treats `last_seen_location` as canonical), red-phase
  may flip the order. *Verification:* TEA surveys the write sites
  for each field and reports the de-facto trust ordering.
- **No circular-import landmine on a new module.** Co-locating with
  `Npc` definition in `sidequest/game/session.py` is preferred if the
  import graph allows. If a circular import emerges (e.g.,
  `tools/list_npcs_in_scene.py` already imports from `session.py` and
  adding the predicate would invert layering somewhere), Dev picks
  a different home — likely a new `sidequest/game/npc_scene.py`.
  *Verification:* Dev runs `pyright` and `uv run pytest -n0 -x` early
  in green phase.
- **61-2's tests are the canonical contract for projection counts.**
  No undocumented consumer of `_npc_in_scene` exists outside the
  projection code path. *Verification:* TEA greps for `_npc_in_scene`
  callers; if any consumer exists outside `_apply_phase_c_projections`,
  it must be updated to consume the unified predicate.
- **Sidequest-server is on branch `feat/61-7-unify-npc-in-scene-predicate`
  (off develop) before any commit.** sm-setup created this branch;
  verify it exists before the first red-phase commit.
  *Verification:* `cd sidequest-server && git rev-parse --abbrev-ref HEAD`.
- **No Jira interactions** (OQ-2 personal project). `JIRA_KEY: none`
  is the intentional state, not an error.
