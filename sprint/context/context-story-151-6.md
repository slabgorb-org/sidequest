---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-6: Shrink output_only.md to prose + private_segments brief; perception-firewall guard

## Business Context

Once the bucket-B fields and `action_rewrite` are gone (151-3/4/5), the narrator's
output contract collapses from ~255 lines of recording manual to a short
storytelling brief: *write the prose; obey the perception firewall; withhold
single-PC perception into `private_segments`.* This is where the "mostly
storytelling" win is realized. `private_segments` is the **one field that stays**
— it is generation-entangled (ADR-105 MOVE-not-COPY is decided as prose is written).
This story also adds a permanent guard so no future optimization sweeps
`private_segments` into the extractor and silently reopens the perception leak.

## Technical Guardrails

- **Rewrite** `sidequest/agents/narrator_prompts/output_only.md` to contain only:
  the prose brief, the perception-firewall rule, and the `private_segments`
  instruction. Remove all bucket-B and `action_rewrite` field instructions.
- **`private_segments` STAYS narrator-inline.** Do NOT move it to the extractor —
  a post-hoc reader cannot recover information already leaked into PART 1.
- **Perception-firewall guard test (non-negotiable, per ADR-150 §Implementation
  Notes):** prove a single-PC perception present in a turn NEVER appears in PART 1 —
  it exists only in `private_segments`. Any trace in PART 1 (label, summary, or
  ordinary narration) fails the test. This is the regression tripwire for ADR-105.
- Keep consistency with 151-1: the shrunk contract is still byte-stable and cached.

## Scope Boundaries

**In scope:**
- Shrink `output_only.md`; the `private_segments`-stays-inline guard test.

**Out of scope:**
- Any field still in flight — this story gates on 151-3, 151-4, and 151-5 all merged.
- Moving `private_segments` anywhere (it stays).

## AC Context

1. **Shrunk:** `output_only.md` contains only the prose + perception-firewall +
   `private_segments` brief; the bucket-B / `action_rewrite` recording instructions
   are gone.
2. **Still cached/stable:** the shrunk section remains byte-stable and rides the
   cached prefix (consistent with 151-1).
3. **Firewall guard:** a turn with single-PC perception emits that perception ONLY in
   `private_segments`; the guard test fails on ANY trace of it in PART 1.
4. **Routing intact:** `private_segments` still routes per `anchor_pc` to the right
   player (ADR-105 path unbroken).
5. Full suite (with content) green.

## Assumptions

- **Depends on 151-3, 151-4, 151-5 all merged** (every migrated field is gone). If any
  remains sidecar-owned, this shrink is premature — log and notify SM.
- `private_segments` is the sole remaining sidecar-owned field after the cutovers.
