# FOLLOW-UP note — getting the narrator to honor mechanically-determined death

**Status:** FOLLOW-UP (not an active spec). Captured 2026-06-20, split off from the
intent-router output-slim work (`2026-06-20-intent-router-output-slim-design.md`) when we
cut the router's dead `lethality[]` field.

**Owner's words (2026-06-20):** "it is hard to get claude to rp death. I completely
understand the reasoning behind that safeguard and honestly I approve. However, it
certainly gets in the way here."

## The concern

Claude's general safety training softens or dodges character death. The owner *approves*
the safeguard in principle — but for a genre-true RPG it obstructs real stakes. Per
SOUL.md **Genre Truth** ("consequences follow the genre pack's lethality; don't soften
beyond it") and **Living World** (NPCs — and PCs — "can die without player permission"),
and the load-bearing project goal (a narrator good enough to satisfy a 40-year career GM,
where things that should die, die). A game whose deaths always get softened can't deliver
that.

## Why this is NOT the router-lethality field we just cut

Distinct problem. The router's `lethality[]` field was **dead weight** (never read except
as a rare arbiter fallback) — cutting it changes nothing about death RP. The real
lethality pipeline is already built and wired:

- `LethalityPolicy` (`sidequest/genre/models/lethality.py`): `verdicts_on_zero_hp` (pc/npc),
  `must_narrate`, `must_not_narrate`, `soul_md_constraint`. Authored per genre in
  `genre_packs/<genre>/lethality_policy.yaml` (most packs ship one).
- `LethalityArbiter` (`sidequest/agents/lethality_arbiter.py`): deterministically
  synthesises verdicts from post-bank HP=0 + policy, then emits **paired**
  `NarratorDirective`s — `must_narrate` ("{entity} verdict={kind}. {policy.must_narrate}")
  and `must_not_narrate` (policy text) — at lines ~120-133. These render into the narrator
  prompt (`orchestrator.py:3090`) pre-narration.
- `post_resolution_lethality.py` handles the PC-down mechanical side and always emits the
  `encounter.post_resolution_lethality` OTEL span.

So the **determination** and the **instruction** already reach the narrator. The gap is
**narrator compliance**: does the model obey the death directive, or write around it?

## The real question (what the follow-up must answer)

Drive a lethal combat to HP=0 (PC and NPC) and compare three layers:

1. **Mechanics fired?** `encounter.post_resolution_lethality` span present, verdict =
   policy's `verdicts_on_zero_hp`. (Almost certainly yes — it's deterministic.)
2. **Directive emitted?** The `must_narrate` / `must_not_narrate` pair present in the
   rendered narrator prompt for that turn.
3. **Narration honored it?** Read the actual prose. Did the character die on the page, or
   did the narrator soften (knocked out, "barely clinging on", scene cut away)?

If 1 and 2 fire but 3 softens, this is a **compliance** problem, and the fix space is
narrator-side, NOT more mechanical output:

- Directive **strength / placement** — is the death directive in the highest-attention
  recency zone, or buried? Is it phrased as an unconditional instruction?
- Genre `lethality_policy` **text** — is `must_narrate` worded strongly enough; does
  `must_not_narrate` explicitly forbid the dodges (knockout, fade-to-black, retcon)?
- Prompt **framing** — establishing up front that this is authored fiction with
  consequences (the SOUL.md framing) so the model treats death as genre-required, not
  gratuitous.
- A possible **lethality-compliance lie-detector**: a post-narration span that flags
  "verdict=dead but the narration did not kill the entity" — the same lie-detector pattern
  as `dispatch_engagement.*.mismatch`. This is the OTEL hook that would make the problem
  *measurable* turn over turn instead of anecdotal.

## Scope boundary

This is a **narrator-compliance** investigation (genre policy text + prompt framing +
possible compliance span), separate from:
- the router output-slim latency work (done in the companion spec), and
- the parked clarify-loop.

## Suggested next step

A focused headless playtest: `combat_stress.yaml` (or a PC-death scenario) with
`--span-jsonl`, read `encounter.post_resolution_lethality` + the rendered directives, then
read the narration prose against the verdict. Quantify the softening rate before deciding
the fix. Bring it back through brainstorming as its own design.
