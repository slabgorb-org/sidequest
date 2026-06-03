---
parent: context-epic-75.md
workflow: tdd
---

# Story 75-9: [DESIGN] NPC-pool ratification gate + pool/Npc split (ADR-135) — governs ADR-118 projection source

## Business Context

Epic 75 restored and extended the RAG retrieval layer. The universal retrieval
layer (ADR-118, **live**) now projects NPCs, locations, and factions into a
vector index and retrieves them per turn under a token budget. ADR-118's NPC
projector reads its `content` "from `NpcPoolMember` / promoted `Npc`" (ADR-118
§D3) — but the ADR did not pin down **which** pool members are eligible to be
projected, nor reconcile that against the *already-existing* pool→`Npc`
ratification gate (Story 49-6).

The risk this design closes: the narrator auto-mints prose-only pool members
every turn (`_auto_mint_prose_only_npcs`), and many are one-off mentions that
the 49-6 gate later **purges** as phantoms. If the ADR-118 index projects those
unratified members before the gate has ruled, the retrieval layer pins,
embeds, and can re-surface NPCs the world never actually committed to — exactly
the "narrator improvises a phantom cast" failure the OTEL lie-detector exists to
catch. The same unratified-phantom question applies to ADR-135's public
reference pages, which render `npcs.yaml`/pool NPCs to players.

This is a **design-only** story (like its sibling 75-3): the deliverable is a
written design of record — the ratification gate's role as the authoritative
source for *what is projectable* — plus the follow-on implementation stories it
spawns. **No production engine code lands in 75-9.**

## Technical Guardrails

**Reuse-first — the split and the gate already exist. Do not rebuild them.**

- **The pool/Npc split is live.** `NpcPoolMember`
  (`sidequest/game/npc_pool.py:19`) is identity-only scaffolding (name, role,
  pronouns, appearance, disposition, `drawn_from` provenance). `Npc`
  (`sidequest/game/session.py:126`) is the mechanical entity (CreatureCore,
  EdgePool, beliefs, last-seen). Promotion sets `Npc.pool_origin = member.name`;
  the pool member is **not consumed** — it stays in `GameSnapshot.npc_pool` and
  is shadowed by the `Npc` lookup at narration_apply time. This split was Wave 2A
  of the 2026-05-04 snapshot-split-brain cleanup. The design *describes and
  governs* this split; it does not redesign it.
- **The ratification gate is live (Story 49-6).** `NpcPoolMember.observation_pending`
  (`npc_pool.py:58`) is the gate flag. `_auto_mint_prose_only_npcs` is the only
  writer that sets it `True`. Each turn the gate either flips it to `False`
  (narrator re-cited the member → promote/canonize) or removes the entry (narrator
  dropped it → purge the phantom). World-authored, name-generator, and legacy
  members enter **already ratified** (`observation_pending=False`).
- **The ADR-118 index machinery is live.** `entity_card.py`, `entity_store.py`,
  `entity_embedding.py`, `entity_sync.py`, `retrieval_orchestration.py`. The NPC
  `to_card()` projector is what this design governs the *input* to.

**The design question (what 75-9 must decide and write down):**
1. Is `observation_pending=True` (unratified) the boundary that gates entry into
   the ADR-118 projection/index? (Strong default: yes — phantoms must not be
   embedded or retrieved until ratified.)
2. What happens to an index card when the gate **purges** its pool member —
   eviction path, and how is it observable (cf. ADR-118 §D5 `stale_card_count`,
   `card_reproject_count`)?
3. Does ADR-135's public reference rendering share the same ratification gate
   (i.e. don't render unratified phantoms to players)?

**Doctrine to honor in the design:**
- *No Silent Fallbacks* — gate outcomes (promote/purge/pending) and any
  projection-eligibility decision must be OTEL-observable, never a silent skip.
- *Diamonds and Coal / Living World (ADR-014)* — ratification is promotion of
  coal to diamond when players engage; the design must not delete history, only
  gate what enters context.
- *Crunch in genre, flavor in world* — N/A to engine design, but the gate must
  not bake world-specific assumptions into the engine.

## Scope Boundaries

**In scope:**
- A written design of record (design spec under `docs/superpowers/specs/`, and/or
  a new ADR — see Assumptions re: ADR numbering) defining the ratification gate as
  the authoritative source governing the ADR-118 NPC projection source.
- Clarification/specification of the pool ↔ `Npc` split as it pertains to
  projection eligibility (what is projectable, when).
- Reconciliation with ADR-118 (projection source) and ADR-135 (public reference
  rendering of NPCs).
- The list of follow-on implementation stories this design spawns (with crisp
  acceptance boundaries), mirroring how ADR-118/75-3 spawned 75-4…75-8.

**Out of scope:**
- Production engine code implementing the gate→projection wiring (that is the
  follow-on stories' job — 75-9 is design-only).
- Redesigning the pool/Npc split itself or the 49-6 gate mechanics (reuse as-is).
- Locations and factions projection eligibility (NPC-pool-focused; name as
  follow-on if the same gate pattern generalizes).
- Inventory (already out of ADR-118 v1 scope).

## AC Context

This is a `[DESIGN]` story tagged `tdd`/`chore` at 3 pts. The sprint YAML carries
no explicit acceptance-criteria list, so the design phase (Architect-led) must
ratify the ACs before RED. Proposed testable completion criteria for TEA/Dev to
confirm or refine:

- **AC1 — Design artifact exists and is reviewable.** A design spec (and ADR if
  warranted) is written that states, unambiguously, whether `observation_pending`
  gates ADR-118 projection eligibility, with the rationale and the rejected
  alternatives. *Verify:* the artifact exists, names the real structures
  (`NpcPoolMember.observation_pending`, the `to_card()` NPC projector), and a
  reviewer can trace each decision.
- **AC2 — Purge/eviction path specified.** The design states what happens to an
  index card when its pool member is purged by the gate, and which OTEL span
  makes it observable. *Verify:* the eviction + observability path is named and
  consistent with ADR-118 §D5.
- **AC3 — ADR-135 reconciliation stated.** The design says whether public
  reference rendering shares the ratification gate. *Verify:* an explicit
  statement (yes/no + why) is present.
- **AC4 — Follow-on stories enumerated.** The design names the implementation
  stories it spawns with scope boundaries. *Verify:* a concrete story list exists,
  ready for `pf sprint story add`.

Because the deliverable is a design (not code), the "tests" for a TDD framing are
primarily **review gates** on the artifact's completeness and internal
consistency. If the Architect/Dev determine there is a small, testable engine
seam worth landing (e.g. a pure `is_projectable(member) -> bool` predicate the
follow-on stories will consume), that is the only code candidate — and it must
arrive with a unit test and a wiring assertion per repo doctrine.

## Assumptions

- **The "(ADR-135)" in the title is a cross-reference, not the ADR this story
  produces.** The latest ADR on disk is **137**; ADR-135 is *Reference Pages Are
  a Public Table Tool*. ADR-135 is relevant because reference pages render the
  public NPC pool, so the ratification gate plausibly governs that surface too —
  but the *primary* governed surface is **ADR-118's projection source** (per the
  title's own "governs ADR-118 projection source"). **If this design warrants its
  own ADR, it takes the next free number (138), not 135.** *Architect: confirm
  whether a new ADR is required or whether a design spec amending ADR-118 §D3
  suffices.* Logged as a Question finding in the session.
- The 49-6 ratification gate fires reliably each turn and is the right hook to
  read for projection eligibility (vs. introducing a second, parallel gate).
- ADR-118's index is in-memory (§D1), so card eviction on purge is a cheap
  in-memory operation, not a persistence migration.
- 75-4…75-8 (the ADR-118 implementation) are merged (all marked `done`), so the
  projector and store this design governs are live and inspectable.
