---
id: 138
title: "NPC Ratification Gates Projection Eligibility — Unratified Pool Members Stay Out of the ADR-118 Index and the ADR-135 Public Surface"
status: proposed
date: 2026-06-03
deciders: ["Keith Avery", "Ponder Stibbons (Dev)"]
supersedes: []
superseded-by: null
related: [14, 20, 53, 104, 118, 135]
tags: [agent-system, npc-character, observability]
implementation-status: deferred
implementation-pointer: "Design-only (story 75-9). Governs existing sidequest-server/sidequest/game/npc_pool.py (NpcPoolMember.observation_pending — Story 49-6 gate) and the ADR-118 §D3 NPC to_card() projector (game/entity_card.py / entity_sync.py). Implementation deferred to follow-on stories 75-11..75-14."
---

# ADR-138: NPC Ratification Gates Projection Eligibility — Unratified Pool Members Stay Out of the ADR-118 Index and the ADR-135 Public Surface

> **Design story (75-9).** Deliverable is this ADR plus the implementation-story
> breakdown in §Implementation Stories — **no production code lands in 75-9**. The
> pool/`Npc` split and the ratification gate this ADR governs **already exist and
> are live**; this is a *governance / reconciliation* design over existing
> structures, not a greenfield build. The engine work is scoped into follow-on
> stories 75-11…75-14 (server), each of which carries its own failing tests.

## Context

Two facts about the current tree set up this decision.

**1. The pool/`Npc` split and a ratification gate are already live.**
`NpcPoolMember` (`sidequest/game/npc_pool.py`) is identity-only scaffolding —
name, role, pronouns, appearance, disposition, `drawn_from` provenance — that
the narrator cites for name-continuity. `Npc` (`sidequest/game/session.py`) is the
mechanical entity (CreatureCore, EdgePool, beliefs, last-seen). A pool member is
*promoted* to an `Npc` (with `pool_origin = member.name`) when it engages
mechanically; the pool member is **not consumed**. Story 49-6 added a
**ratification gate**: `NpcPoolMember.observation_pending`. `True` means the member
was auto-minted from prose this turn by `_auto_mint_prose_only_npcs` and has not
yet been re-cited. Each turn the gate either flips it to `False` (the narrator
re-cited it → **promote**, treat as canonical) or removes the entry entirely (the
narrator dropped the one-off → **purge** the phantom). World-authored,
name-generator, and legacy members enter **already ratified**
(`observation_pending = False`).

**2. ADR-118 left the projection *source* under-specified.** The universal
retrieval layer (ADR-118, live) projects NPCs into a vector index via a `to_card()`
projector whose `content` is drawn, per §D3, "from `NpcPoolMember` / promoted
`Npc`." ADR-118 did not say **which** pool members are eligible to be projected.
Taken literally, every auto-minted member — including the prose-only phantoms the
49-6 gate exists to purge — would be embedded and become semantically retrievable.
That is the precise failure the OTEL lie-detector is built to catch: the narrator
re-surfaces a one-off NPC the world never committed to, dressed up as a recalled,
canonical cast member. Embedding phantoms also wastes the embedding worker on
entries that may not survive the next turn.

**3. ADR-135 has the same question from the other side.** The public reference
pages (ADR-135) render the NPC pool to players as a public projection (name + role
+ appearance + portrait). An unratified, auto-minted phantom rendered there is the
same defect on a different surface: the table is shown a "character" that does not
really exist yet.

Both surfaces — the ADR-118 retrieval index and the ADR-135 reference page — are
**downstream projections of the same NPC cast**, and both need the same upstream
answer: *is this member real enough to project?* That shared question is what the
"(ADR-135)" cross-reference in the story title points at: ratification is the
common gate governing what is projectable to **any** projection surface.

## Decision

### D1 — Ratification is the projection-eligibility gate

A pool member with `observation_pending = True` is **not projectable**. Only
**ratified** pool members (`observation_pending = False`) and **promoted `Npc`s**
are eligible to be projected into the ADR-118 index. Rationale: an unratified
member is a candidate the gate may purge next turn; the world has not committed to
it, so it must not be embedded or made semantically retrievable as if it had been.

### D2 — The gate governs the FILL/index, never the FLOOR

This is the load-bearing reconciliation with ADR-118 §D4 (floor + fill) and the
SOUL doctrines. The **floor** (75-2 working-set selection) reads the *live*
`npc_pool` / `Npc` structs for entities present this turn (current location's NPCs,
`last_seen ≤ N`). A freshly-minted, still-`observation_pending` member that the
player is interacting with **right now** is scene-present and therefore **still in
the floor, at full detail, via the live-struct path** — it is never dropped from
the prompt. Ratification governs only the **fill**: whether a member is *embedded
and semantically retrievable when it is not scene-present*. An unratified member is
withheld from the index, not from the present scene. This honors *Guitar Solo* (the
soloist's present scene stays whole) and ADR-014 *Living World* (entities move in
and out of context by relevance, never by deletion).

### D3 — One predicate, consulted by every projection surface

Define a single eligibility predicate so no surface re-implements the rule:

```
is_projectable(member: NpcPoolMember) -> bool   # == not member.observation_pending
# promoted Npc (sidequest.game.session.Npc) is always projectable
```

It lives beside the model in `npc_pool.py`. Both the ADR-118 NPC `to_card()` /
sync path **and** the ADR-135 reference NPC projection consult this one predicate.
This is **design only** — the predicate's implementation, its truth-table unit
test, and its wiring into each surface are deferred to the follow-on stories (per
the TEA tripwire recorded on story 75-9: any code landing on the 75-9 branch would
require bouncing back to RED; the clean outcome is to keep 75-9 design-only).

### D4 — ADR-135 reconciliation: the reference page shares the gate (yes)

Public reference rendering **shares** the ratification gate. An unratified,
`observation_pending` phantom is **not** rendered on the public reference page,
for the same reason it is not indexed: the world has not committed to it. ADR-135's
spoiler firewall is unchanged and orthogonal — this gate is an *existence/canonical*
filter applied **before** the public-vs-keeper projection, not a new audience axis.
A ratified member still renders only its public projection (name + role +
appearance + portrait), exactly as ADR-135 §2 specifies.

### D5 — Lifecycle and eviction (and why purge needs no eviction)

Because unratified members are never indexed (D1), the lifecycle is clean:

- **Mint (pending):** member created `observation_pending = True` → **not indexed**.
- **Ratify (promote):** gate flips to `False` → now projectable → marked dirty →
  re-embedded by the existing embedding worker on its next pass (ADR-118 §D3 / the
  75-6 reproject hook).
- **Purge:** gate removes a still-pending member → **no index eviction required**,
  because it was never indexed. This is the design's tidiest property: the
  eligibility gate makes phantom eviction a non-event.

A **defensive eviction** path is still specified for the invariant-violation case
(a card exists for a member that is no longer projectable — e.g. a future code path
re-marks a member pending). Such a card MUST be evicted and the eviction MUST emit
an observable span (D6) — it is never silently served stale. Note this is distinct
from an NPC *leaving the scene* or *dying*: per ADR-014 those entities are **not**
deleted and **stay indexed** (the late Borin remains part of the world's cast); D5
eviction is only for the never-should-have-been-projected case.

### D6 — OTEL observability (doctrine-mandated)

Per the project OTEL principle and ADR-118 §D5, every decision here is observable:

- **Gate decisions** (49-6): emit `npc.ratification.{outcome}` with
  `outcome ∈ {promote, purge, pending}` and the member id, so the GM panel can see
  the gate firing rather than inferring it.
- **Projection skip:** the retrieval seam emits a per-pass
  `retrieval.npc_unratified_skipped` count (extends the ADR-118 §D5 attribute set)
  so the number of members withheld from the index is visible.
- **Defensive eviction:** `entity_card.evicted{reason=unprojectable}` — never a
  silent drop (honors *No Silent Fallbacks*).

## Reconciliation with existing ADRs

- **ADR-118 (Universal Retrieval Layer):** this ADR *completes* §D3 by naming the
  projection source precisely — ratified members + promoted `Npc`s — and confirms
  the gate touches the fill, not the floor (§D4). No change to the floor+fill
  contract or the embedding machinery.
- **ADR-135 (Reference Pages):** the reference NPC projection gains the same
  upstream ratification filter (D4). ADR-135's one-fixed-public-projection and
  spoiler firewall are unchanged; ratification runs *before* the public projection.
- **Story 49-6 (ratification gate):** reused as-is. This ADR adds **consumers** of
  the existing `observation_pending` flag; it does not change the gate's
  promote/purge logic.
- **ADR-014 (Diamonds & Coal / Living World):** honored. Ratification is exactly
  "coal becomes a diamond when players engage." No entity is deleted; the present
  scene is never dropped (§D2).
- **ADR-104 (Perception Filtering):** orthogonal. Ratification decides *what is
  real enough to project*; perception filtering still decides *what a given player
  may perceive*, downstream and unchanged.

## Implementation Stories (this ADR spawns)

Story 75-9 delivers **design only**. The following implement it; each lands in
`sidequest-server` with its own failing tests (RED) per the TEA tripwire:

- **75-11 — `is_projectable()` predicate + unit tests.** Implement the D3 predicate
  in `npc_pool.py`; truth-table tests (ratified → `True`; `observation_pending=True`
  → `False`; promoted `Npc` → `True`). No wiring yet.
- **75-12 — Wire the gate into the ADR-118 NPC projection.** Consult
  `is_projectable()` in the NPC `to_card()` / `entity_sync` path so pending members
  are not embedded; emit `retrieval.npc_unratified_skipped`; re-embed on ratify via
  the 75-6 reproject hook. Wiring proven by an OTEL/behaviour test, not a
  source-text grep.
- **75-13 — Wire the gate into the ADR-135 reference projection.** Pending members
  are absent from the public reference page; test that an `observation_pending`
  member does not render while its ratified sibling does.
- **75-14 (optional) — Defensive eviction + `entity_card.evicted` span.** Only if
  75-12 surfaces a real path that can strand a card on a now-unprojectable member;
  otherwise fold the invariant assertion into 75-12 and drop this story.

## Consequences

**Positive:**

- The retrieval index and the public reference surface stop carrying phantom NPCs;
  relevance recall and public rendering both reflect the *committed* cast only.
- One predicate, one rule — the projection-eligibility question has a single source
  of truth shared by every downstream surface, present and future.
- Purge becomes a non-event for the index (D5) — no eviction bookkeeping for the
  common phantom case.
- Every decision is GM-panel-observable (D6); a withheld or evicted NPC is visible,
  never silent.

**Negative / risks:**

- A member that *should* have been re-cited but the narrator phrased differently
  could be purged before it is ever indexed, briefly losing a borderline-real NPC
  from semantic recall. Mitigation: it is still in the floor while scene-present,
  and the 49-6 gate's re-citation window is the existing tuning knob — not widened
  here.
- The reference page will not show a just-invented NPC until it ratifies (next
  turn at the earliest). Accepted: a not-yet-real NPC should not appear on a public
  table tool.
- Adds one consumer-side check to two hot paths; cost is a boolean read per member,
  negligible against the embedding cost it avoids.

## Alternatives considered

- **Project everything, filter at retrieval time.** Rejected — still pays the
  embedding cost for phantoms and lets a phantom rank into the fill before the
  filter runs; the gate belongs at *projection*, not *retrieval*.
- **Project everything; let the 49-6 purge evict stale cards.** Rejected — inverts
  the clean property of D5 (purge-needs-no-eviction) and creates a window where a
  phantom is retrievable before its purge turn.
- **A second, retrieval-specific eligibility flag separate from `observation_pending`.**
  Rejected — duplicates the existing gate, invites the two flags to drift, and
  violates reuse-first. The 49-6 gate already answers "is this member real yet?"
- **Gate the floor too (drop pending members from the working set).** Rejected —
  would drop the entity the player is interacting with this very turn, violating
  *Guitar Solo* and ADR-014. The floor reads live structs and must stay whole.
