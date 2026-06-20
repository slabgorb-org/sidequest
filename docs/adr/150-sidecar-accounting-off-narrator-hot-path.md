---
id: 150
title: "Sidecar Accounting Leaves the Narrator Hot Path — Pre-Narration Rewrite, Post-Narration Extraction, and the One Field That Stays"
status: accepted
date: 2026-06-18
deciders: ["Keith Avery", "The Man in Black (Architect)"]
supersedes: []
superseded-by: null
related: [113, 67, 98, 102, 5, 104, 105, 110, 112, 13, 31]
tags: [agent-system, narrator, narrator-migration, observability]
implementation-status: deferred
implementation-pointer: null
---

# ADR-150: Sidecar Accounting Leaves the Narrator Hot Path — Pre-Narration Rewrite, Post-Narration Extraction, and the One Field That Stays

> **Design-only ADR.** This decision ratifies the *structure*; it ships no code.
> The dev work is sized after this ADR lands (see §Implementation Notes →
> *Sizing the follow-up*). It extends the ADR-113 intent-router lineage: a
> pre-narrator pass already exists and a post-narration watcher already exists;
> this ADR gives each of them a bookkeeping job and shrinks the narrator's turn
> to (almost) pure storytelling.

## Status

Accepted 2026-06-18 (Keith Avery, decider). Found in the 2026-06-18 narrator
hot-path deep-dive. `implementation-status: deferred` — the structure is ratified;
the dev work is sized in the follow-up epic this ADR scopes but does not perform
(see §Implementation Notes → *Sizing the follow-up*).

## Amendment — RENDER-NO-SUBJECT (2026-06-20): bucket-B Is Extractive-Only; Generative Fields Stay Narrator-Owned

Found in the 2026-06-20 full-stack playtest (wry_whimsy/gulliver, story 150-7;
root-caused by the Architect). The cutover (Story 151-5, server #956) routed **all**
of bucket-B through the post-narration *never-invent* extractor (`sidecar_extractor.py`:
"report only what the prose states; never invent — an empty field is correct"). Two of
those fields are **not extractive facts**; they are **generative/authorial outputs**:

- **`visual_scene`** — an art-direction directive (*what illustration to PAINT*).
  Prose never literally states a render subject; composing one **is** invention. The
  reader correctly returned it empty every turn → `render.eligible_no_subject` → the
  daemon was never called → **zero scrapbook illustrations on every world** since the
  cutover.
- **`footnotes`** — the player's knowledge/journal feed (an authorial "what did the
  player just learn" decision). Same mechanism → empty feed → `known_facts=0` on
  mystery worlds.

A reader-that-cannot-invent **structurally cannot produce** a generative field.
Per SOUL *Diamonds & Coal* (the narrator chooses *what* is worth drawing) and
*Bind the Ruleset, Don't Balance It* (the bound mechanism replaces, it is not
layered-and-tuned), the fix is **not** a generative second pass (that re-introduces
cost and splits art-direction authority); it is to **keep generative fields on the
narrator hot path**.

**Amended decision:** bucket-B is **extractive-only**. The post-narration extractor
owns the facts the prose *states* — `items_gained/lost/discarded/consumed`,
`gold_change`, `companions_added/dismissed`, `npcs_present`, `scene_mood`. The two
**generative** fields **`visual_scene`** and **`footnotes`** stay **narrator-owned**,
the same exception already granted to `private_segments` (ADR-105 firewall). The
narrator's "one field that stays" is now *three* — the firewall field plus the two
generative fields.

Implemented in server PR #994 (reverses #956 for these two fields only): restored to
`extract_structured_from_response` + the narrator `output_only.md` contract; removed
from `BUCKET_B_FIELDS`, the `SidecarExtraction` model, and
`merge_sidecar_extraction_cosmetic` (now scene_mood-only). The §Decision bucket-B
table below predates this amendment — `visual_scene`/`footnotes` listed there as
extractor-sourced are superseded by this section.

## Context

### The narrator is carrying ten pounds in a five-pound bag

A single narrator generation today must do three jobs at once, in one Opus call:

1. **Write prose** — the only job that needs Opus, the only job that serves the
   load-bearing project goal (a narrator *good enough to fool a career GM*).
2. **Emit ~13 structured sidecar fields** in a fenced `game_patch` JSON block
   (the "PART 2" of `narrator_prompts/output_only.md`).
3. **Fire up to 8 categories of native tool calls** inline alongside the prose
   (status/HP, world-patch, magic, confrontation beats, day-advance, disposition,
   dice, scenario-clue).

The contract that teaches the model to do all of this is
`sidequest-server/sidequest/agents/narrator_prompts/output_only.md`. Measured
2026-06-18:

- **15,961 bytes ≈ 3,990 tokens** of output contract, of which roughly **94% is
  bookkeeping** (≈35% explaining the tool-owned half, ≈59% explaining the
  sidecar-owned half) and **≈0% is craft** — it teaches *recording*, not
  *storytelling*.
- It is injected as the `narrator_output_only` `PromptSection` in
  `AttentionZone.Primacy` (`narrator.py:271`, assembled at
  `orchestrator.py:1928`), but `narrator_output_only` is **not** in
  `STABLE_SECTION_NAMES` (`prompt_framework/bucket.py:28-96`), so
  `default_bucket_for_section` drops it into `SectionBucket.User`
  (`bucket.py:99-108`). The cache predicate `_section_rides_cache` requires
  **both** System bucket **and** Primacy/Early zone (`orchestrator.py:132-146`),
  so this section rides the **uncached** per-turn user message. It is
  **byte-identical every turn** and **paid fresh every turn** — ~4k uncached
  input tokens per turn buying nothing but re-explanation.

Two costs compound: the **token cost** (4k uncached/turn) and the far more
expensive **attention cost** — every paragraph of bookkeeping the model reads
and every field it stops to emit is attention it is *not* spending on the prose.
For a project whose reason to exist is narrator quality, the attention cost is
the one that matters. This is the SOUL principle *Cost Scales with Drama* read in
reverse: we are spending the narrator's most expensive cognitive cycles on the
least dramatic work in the turn.

### The lineage already built the two passes we need

ADR-113 (Intent Router — Mechanical-Engagement Spine) established the pattern
this ADR extends. It is **live**:

- A **pre-narrator pass** — `IntentRouter.decompose` (`agents/intent_router.py`),
  a Haiku-via-SDK classifier run by `execute_intent_router_pre_narrator_pass`
  (`server/intent_router_pass.py`) from `websocket_session_handler.py` *before*
  the narrator. It reads the player's action and a slimmed state summary and
  emits a `DispatchPackage`, then `run_dispatch_bank` engages the mechanical
  engines so the narrator narrates *already-real* state.
- A **post-narration pass** — `dispatch_engagement_watcher.py`, a lie-detector
  that reads the narrator's output *after the fact* and emits
  `dispatch_engagement.{subsystem}.mismatch` spans.

The shape this ADR needs — "decide some bookkeeping *before* the narrator, derive
the rest *after* it" — is already the lineage's skeleton. We are adding muscle to
existing bone, not growing a new limb.

### The sidecar fields are mostly post-hoc readouts of prose the narrator already wrote

The 13 sidecar fields parse into `NarrationTurnResult`
(`orchestrator.py:474-587`) via `_extract_game_patch_json`
(`orchestrator.py:1015-1051`). Tracing each field to its information *source*
yields a clean three-way partition:

| Field(s) | Source bucket | Where it lands today | Evidence |
|----------|---------------|----------------------|----------|
| `action_rewrite` (`you`/`named`/`intent`) | **A — player input** | sidecar | A rewrite of the player's *own submitted action* into three perspectives. Needs nothing from the prose. Its `.named`/`.intent` then *drive* visibility classification (`visibility_classifier.py:124-129`) — which runs *after* the narrator anyway. |
| `items_gained/lost/discarded/consumed`, `gold_change`, `companions_added/dismissed`, `npcs_present`, `mood`, `visual_scene`, `footnotes` | **B — readout of prose** | sidecar | Each is a structured summary of something the prose *already states* ("you pocket a silver ring" → `items_gained`). The server **already** reconstructs these from prose as safety nets: `_detect_missed_recurring_npcs`, `_auto_mint_prose_only_npcs` (`narration_apply.py:5134-5206`), `unmatched_*` item watchers (`narration_apply.py:4683-4970`), companion dedup watchers (`narration_apply.py:6535-6695`). The fallback extractor exists; today it is the *backup*, not the *primary*. |
| `private_segments` | **C — generation-entangled** | sidecar | The ADR-105 perception firewall: single-PC perception must be **MOVED, not copied**, out of PART 1 (`output_only.md:238-247`). The decision of *what not to say* is made as the prose is written; a post-hoc reader cannot recover information that has already leaked into PART 1. The `_PRIVATE_ASIDE_LINE` scrub (`orchestrator.py:1100-1108`) is a mechanical backstop, not the primary mechanism. |

The headline: **12 of 13 fields are derivable off the critical generation step**
— one before it, eleven after it — and **exactly one** is irreducibly entangled
with the act of writing prose.

### Constraints this ADR must respect

- **ADR-067 (Unified Narrator) is not violated.** ADR-067 collapsed a 4-agent
  system and forbids a *competing pre-narration intent classifier* (its 8–17s
  Sonnet subprocess). It **explicitly blesses** "post-narration extraction
  (already existing for inventory, location, NPC detection)… non-blocking, for
  observability." A passive post-narration extractor is the pattern ADR-067
  named as acceptable, not the anti-pattern it killed. The narrator remains one
  agent, one Opus call, on the critical path, handling all intents.
- **ADR-098 (Stateless Narrator Turns) helps.** Per-turn prompts are already
  bounded and auditable (`prompt_assembled` OTEL: system_len/user_len/bounded).
  Shrinking the output contract makes the bounded prompt smaller and the cache
  prefix larger; it does not fight the regime.
- **ADR-104/105 (Perception Firewall) is sacrosanct.** Whatever happens to the
  other 12 fields, the privacy MOVE-not-COPY guarantee cannot regress. This is
  why field C stays put.
- **The Zork Problem (SOUL).** The post-extractor must be an *open* reader of
  prose, not a closed regex verb-set. Haiku is that open reader; a deterministic
  parser is not (mirrors ADR-113 Alternative C).
- **No Silent Fallbacks (SOUL / CLAUDE.md).** The new passes fail loud with OTEL,
  exactly as the IntentRouter does (`intent_router.failed`).

## Decision

**Split the narrator's bookkeeping out of its generation into the two passes the
ADR-113 lineage already provides, leaving the narrator turn to do prose plus the
single generation-entangled privacy field. The output contract shrinks from a
~4k-token recording manual to a short storytelling brief.**

Concretely, the 13 sidecar fields move to three homes:

### 1. Pre-narration home — `action_rewrite` (field bucket A)

`action_rewrite` is produced by the **pre-narrator pass** (the existing
`IntentRouter`, which already reads the player's raw action and already performs
referent resolution). The three perspectives (`you`/`named`/`intent`) are a
mechanical transform of the submitted action, available *before* the narrator
runs. This is strictly better ordering than today: `action_rewrite.named` and
`.intent` feed visibility classification and the confrontation-intent check,
both of which run after the narrator — so sourcing them from the pre-pass closes
a current ordering hazard (today they are emitted by the very turn whose
visibility they are supposed to gate).

### 2. Narrator home — prose, and `private_segments` only (field bucket C)

The narrator turn keeps **PART 1 prose** and the **one** field that cannot be
recovered post-hoc: `private_segments`. This field *defaults empty* and fires
only when single-PC perception must be withheld — a rare, high-drama event.
Keeping it inline is *Cost Scales with Drama* applied correctly: the unusual
private-perception turn earns its small inline complexity; the common public
turn pays nothing. The pre-narrator pass MAY additionally hand the narrator a
directive ("PC X has a private channel this turn") to prime the partition,
reusing the `DispatchPackage` `narrator_instructions` slot — but the *text*
stays narrator-authored, and the broadcast-layer firewall (ADR-105) remains the
enforcement backstop.

The rewritten `output_only.md` therefore collapses from ~255 lines of recording
contract to a short brief: *write the prose; obey the perception firewall;
withhold single-PC perception into `private_segments`.* The bulk of the 4k
uncached tokens evaporates from every turn.

### 3. Post-narration home — the prose-readout fields (field bucket B)

A new **post-narration extraction pass** reads the narrator's emitted prose and
produces the eleven bucket-B fields. It is a Haiku-via-SDK single-shot
**forced-tool-use** call (ADR-102 `emit_tool` protocol — the structured input
dict comes back validated, no JSON parsing), modeled on the existing
`AsideResolver` (`agents/aside_resolver.py`) and routed through the existing
`CallType.CLASSIFICATION → claude-haiku-4-5` ladder (`agents/model_routing.py`).
**No new model-routing, transport, or protocol infrastructure is required.**

This is, deliberately, a **clean revival of the ADR-013 "lazy extraction" idea**
— but as a *separate, auditable Haiku pass*, not the inline three-tier
JSON-scraping ADR-113 retired. The difference is everything: ADR-013's extraction
competed with the narrator inside one response; this extraction is its own pass
with its own model, its own prompt, and its own OTEL.

**One field that looks like B is owned by the engine, not the extractor:**
`npcs_present.side`/membership. The descriptive enrichment (`appearance`,
`pronouns`, `role`) is fine to extract from prose, but the load-bearing
combatant-membership `side` is better owned by the confrontation the
**IntentRouter already engaged** (it seats opponents pre-narrator) than by a
post-hoc reading of prose. The extractor enriches; the engine adjudicates
membership. This removes a current class of "wrong side breaks momentum routing"
bug at its source.

### Ordering and latency — post-narration, mostly pre-broadcast, partly async

The extraction pass runs **after** the narrator's prose is produced. Whether each
field blocks the broadcast depends on whether the *same turn* consumes it:

- **Pre-broadcast (on the critical path, ~0.3–0.5s Haiku):** the fields a
  subsequent same-turn step or the immediate UI depends on — `npcs_present`
  enrichment (the combatant panel), `items_*`/`gold_change` (inventory state the
  player sees settle this turn). These settle before fan-out.
- **Async (off the critical path, ADR-005 background-first):** the purely
  cosmetic/feed fields — `mood`, `visual_scene`, `footnotes` — may be spawned via
  `asyncio.create_task` and arrive a beat after the prose, exactly as image and
  audio already do. The player reads prose immediately.

Net per-turn latency is expected to be **neutral-to-positive**: the Opus call
sheds ~4k input tokens and the cognitive load of structured emission (a smaller,
more focused, plausibly *faster* generation), while the added Haiku extraction is
~0.3–0.5s and partly off the critical path. Net cost improves: a smaller Opus
prompt with a larger cached prefix, plus a cheap Haiku call, beats a fat uncached
Opus turn.

### Companion quick-win (do it regardless): cache the residual contract

Independent of the extraction work, the residual `output_only.md` (and anything
that stays byte-stable) should be **promoted into the cached prefix** by adding
`narrator_output_only` to `STABLE_SECTION_NAMES` (`bucket.py`). This is the
cheap, already-available lever that stops paying for a byte-identical section
every turn. It is *necessary but not sufficient* — caching fixes the token cost
but not the attention cost — so it is a companion to, not a substitute for, the
extraction. (See Alternative A.)

### Telemetry (OTEL discipline, ADR-031 / CLAUDE.md OTEL Principle)

The GM panel is the lie detector; the new passes must be visible to it.

- `sidecar_extraction.run` — model, input prose length, field count, latency,
  pre-broadcast vs async.
- `sidecar_extraction.{field}` — per-field emitted/empty, on the extraction pass.
- `sidecar_extraction.mismatch` — a lie-detector span (reusing the
  `dispatch_engagement_watcher` pattern) when the extractor's output disagrees
  with what the engine/state already holds (e.g. extractor reports an item the
  inventory mutation could not match), so confabulation in *either* the narrator
  or the extractor surfaces on the panel.
- `intent_router.action_rewrite` — emitted/derived, on the pre-pass.

### No-fallbacks discipline

Per ADR-113's precedent: extraction failure (Haiku timeout, transport error,
schema-invalid output) emits an ERROR span, gets **one bounded retry**, and on
second failure surfaces an explicit GM-panel error — the existing per-field
catch-loops (`unmatched_*`, `_auto_mint_prose_only_npcs`) remain as the
already-built *loud* safety net, never silently masking a failed pass.

## Consequences

### Positive

- **The narrator's attention returns to prose.** The single most load-bearing
  project goal — a narrator good enough to fool a career GM — is served directly:
  Opus stops spending cycles on recording and spends them on craft. This is the
  decision's real payoff; cost is secondary.
- **~4k uncached tokens/turn removed** from the Opus call, with the residual
  contract cache-promotable on top.
- **Reuse-first, near-zero new infrastructure.** Pre-pass = the live
  `IntentRouter`. Post-pass = the live `AsideResolver`/`emit_tool` pattern on the
  live Haiku routing ladder. Watcher = the live `dispatch_engagement_watcher`
  pattern. The build is wiring + a prompt + OTEL, not a new subsystem.
- **The safety nets become the primary path.** The server already reconstructs
  most bucket-B fields from prose as fallbacks; this promotes that capability
  from backup to first-class and gives it OTEL, so the "narrator forgot to emit
  X" class of bug is handled by design rather than by catch-loop luck.
- **An ordering hazard closes.** `action_rewrite` moves *ahead* of the
  visibility classification it feeds.
- **`npcs_present.side` correctness improves** by sourcing membership from the
  engine the router already engaged.

### Negative

- **A second LLM call per turn** (the post-extractor). Bounded (~0.3–0.5s Haiku),
  partly async, on the same transport — but it is one more dependency on the
  turn's success path, and the no-fallbacks retry adds a tail. Mitigated by
  per-field catch-loops surviving as the loud net.
- **Two readers of one prose** can disagree (narrator wrote it; extractor read
  it). The `sidecar_extraction.mismatch` span is the detector, but reconciling
  genuine disagreements (extractor sees an item the prose only implied) is new
  operational surface.
- **An atomic-ish migration.** Like ADR-113's confrontation cutover, moving a
  field from narrator-emitted to extractor-derived should not run both producers
  in parallel (project memory: *one mechanism per problem*). Each field migrates
  in one change, lie-detector watching from day one.
- **`private_segments` stays inline**, so the output contract does not go to
  zero. This is correct (field C is irreducible) but means the "mostly
  storytelling" win is ~92% of the bookkeeping, not 100%.

### Neutral / explicit non-goals

- **No narrator replacement; ADR-067 stands.** One narrator, one Opus call, on
  the critical path.
- **The 8 tool-owned categories are out of scope for the Decision.** This ADR
  moves the *sidecar* (`game_patch`) bookkeeping. A subset of tool-owned
  categories are *also* post-extraction candidates (descriptive
  `apply_world_patch` location/atmosphere, `tick_tropes` day-advance inferable
  from prose), but the mechanically load-bearing tools (`roll_dice`
  anti-fabrication, engine-owned `advance_*`, `apply_damage`) are deliberately
  ADR-113/114 territory and stay. Folding world-patch/day-advance into the
  extractor is flagged for the sizing pass as *Phase 2*, not decided here.
- **No new engines, no per-genre extraction taxonomies.** One extraction
  vocabulary across all genres, mirroring the IntentRouter's single vocabulary.

## Alternatives Considered

### A. Cache the contract and stop there (the cheap fix)

Promote `narrator_output_only` to `STABLE_SECTION_NAMES` so it rides the cached
prefix. **Partially adopted as a companion, rejected as the whole answer.** It
removes the *token* cost but leaves the *attention* cost fully intact — the
narrator still reads and obeys the full recording contract and still emits 13
fields inline. It is a quick win worth taking immediately, but it does not make
the narrator turn "mostly storytelling," which is the point.

### B. Keep everything inline; just trim the prose of `output_only.md`

Tighten the wording to shave tokens. **Rejected.** Same failure as A and worse —
it trades against clarity of a load-bearing contract for a marginal token saving,
and does nothing for attention load.

### C. Deterministic post-parse (regex/keyword extractor, no LLM)

Parse prose with hand-tuned rules into the sidecar fields. **Rejected — violates
the Zork Problem.** Free-form genre prose ("you palm the locket as the others
look away") is exactly the open input a closed verb-set cannot read. Haiku is the
open reader; this is the same reasoning ADR-113 used to reject a rules-engine
router (its Alternative C).

### D. Per-engine SDK tools for the sidecar (one `emit_*` tool per field)

Give the narrator a tool per sidecar field instead of a JSON block. **Rejected.**
This is the tool-proliferation ADR-113 already rejected for engagement: more tool
descriptions dilute the cache, and the narrator's tool-selection across a wide
arsenal is exactly the unreliability we are removing — moving the same inline
burden from a JSON block into N tool calls keeps it on the Opus hot path.

### E. Do nothing — the catch-loops already reconstruct missing fields

Lean entirely on the existing fallbacks and drop the sidecar contract. **Rejected
as-is, but instructive.** The catch-loops are *unaudited best-effort backups*
with no OTEL story of their own and no model behind them for the hard cases
(`side` assignment, multi-recipient item splits). Promoting reconstruction to a
first-class, instrumented Haiku pass is precisely E done honestly. This ADR is
"E, but as a real pass with a lie-detector," not "E by neglect."

## Implementation Notes

> The ADR ratifies structure. The following is guidance for the sizing pass, not
> an implementation.

### Sizing the follow-up (the dev epic this ADR seeds)

Suggested decomposition for the sizing story to cost out — each is a candidate
story, sequence mirrors ADR-113's incremental cutover:

1. **Quick win:** promote `narrator_output_only` to `STABLE_SECTION_NAMES`;
   verify byte-stability and validate cache write/read deltas via the existing
   cost spans (`narration.turn.cached_input_*`). Independent, shippable first.
2. **Post-extractor skeleton:** new `CallType` (or reuse `CLASSIFICATION`), the
   Haiku `emit_tool` extraction call (AsideResolver-shaped), its
   `sidecar_extraction.*` OTEL, and the no-fallbacks retry. No fields cut over
   yet — runs in shadow, lie-detector watching (ADR-113's "watcher from day one"
   discipline).
3. **`action_rewrite` to the pre-pass:** emit from `IntentRouter`; rewire
   `visibility_classifier` to read the pre-pass value; retire the sidecar field.
4. **Bucket-B cutover, field-group at a time** (items → gold → companions →
   `npcs_present` enrichment → `mood`/`visual_scene`/`footnotes`), each atomic,
   each retiring its sidecar emission as the extractor takes over, each keeping
   its catch-loop as the loud net. `npcs_present.side` routes from the engine.
5. **Shrink `output_only.md`** to the prose + `private_segments` brief once the
   bucket-B fields are gone.
6. **Validation:** a playtest gate (mirroring ADR-113's 59-8) confirming prose
   quality is unharmed and sidecar fidelity is at-or-above the catch-loop floor,
   with `sidecar_extraction.mismatch` rates on the GM panel as the metric.

### Testing strategy (project memory: `feedback_no_content_coupled_tests`)

Fixture-based only. Synthetic prose fixtures drive the real extractor; assert the
emitted fields and the OTEL spans (never source-text grep — CLAUDE.md *No
Source-Text Wiring Tests*). The wiring test drives a synthetic turn through the
real pipeline (router → narrator stub → extractor → `narration_apply`) and
asserts the extractor is reached and its output applied. A retirement guard
asserts `narration_apply` no longer reads the migrated field from the
`game_patch` sidecar once its cutover lands.

### Perception-firewall guard (non-negotiable)

The migration must include a test proving `private_segments` is *not* derivable
post-hoc — i.e. that a single-PC perception present in the turn never appears in
PART 1 — so no future "optimization" sweeps field C into the extractor and
silently reopens the ADR-105 leak.

## References

- ADR-113 — Intent Router — Mechanical-Engagement Spine (the lineage: the live
  pre-narrator pass and post-narration watcher this ADR extends)
- ADR-067 — Unified Narrator Agent (not violated; blesses non-blocking
  post-narration extraction, forbids competing pre-narration classifiers)
- ADR-098 — Stateless Narrator Turns (the bounded-prompt regime a smaller
  contract reinforces)
- ADR-102 — Tool-Use Protocol for Structured Output (`emit_tool` forced-tool-use
  the extractor uses)
- ADR-005 — Background-First Pipeline (the async/off-critical-path home for the
  cosmetic bucket-B fields)
- ADR-104 / ADR-105 — Perception Filtering / Broadcast-Layer Perception Firewall
  (the firewall that keeps `private_segments` narrator-inline)
- ADR-110 — Game-State Snapshot Slimming (sibling uncached-payload concern)
- ADR-112 — Genre Prose Cache Promotion (the `STABLE_SECTION_NAMES` mechanism the
  companion quick-win uses)
- ADR-013 — Lazy JSON Extraction (the idea this ADR revives as a clean separate
  pass; ADR-113 retired its inline three-tier form on the SDK path)
- ADR-031 — Game Watcher (the OTEL discipline the new spans honor)
- SOUL.md — *Cost Scales with Drama* (attention is the expensive resource; spend
  it on prose), *The Zork Problem* (the extractor must be an open reader), *No
  Silent Fallbacks* (loud failure, never quiet degradation)
- Source: `sidequest-server/sidequest/agents/narrator_prompts/output_only.md`
  (the contract being split); `agents/orchestrator.py:474-587,1015-1051`
  (`NarrationTurnResult` + `_extract_game_patch_json`); `server/narration_apply.py`
  (the bucket-B consumers + catch-loops); `agents/prompt_framework/bucket.py`
  (the cache-bucket assignment)
