---
id: 146
title: "Quest-Seed Authoring Contract"
status: accepted
date: 2026-06-14
deciders: ["Keith Avery", "Atlas the Endurer (Architect)"]
supersedes: []
superseded-by: null
related: [14, 18, 53, 100, 113, 123, 128, 137]
tags: [game-systems, agent-system, npc-character]
implementation-status: deferred
implementation-pointer: "Design only — implemented by epic 117 story 117-3 (QuestSeed model + quest_offer subsystem + minting handler + OTEL span) and 117-4 (retune the redundant keyword lie-detector). Schema target: sidequest-server/sidequest/genre/models/narrative.py (QuestSeed sub-model on Opening.tone.complication + seed_trope). Mint seam: sidequest/agents/subsystems/ (quest_offer handler). Stash seam: sidequest/server/websocket_handlers/opening_helpers.py + chargen_mixin.py:1399. Anchor-crossing addendum: story 158-43 (mint_on_anchor_crossing in sidequest/game/quest_offer.py, wired in game/session.py pc_region genuine-change block)."
---

# ADR-146: Quest-Seed Authoring Contract

> **A DM who hands you a job has handed you a quest.** When a human GM leans across
> the table and says "the floor-boss wants you to find someone," the quest exists the
> moment you take the job — not when the GM remembers to write it on an index card.
> SideQuest's authored opening hooks have been the index card no one wrote: the
> floor-boss detective hook in `perseus_cloud` lived entirely in prose, and minting a
> tracked quest depended on the narrator *remembering* to call a tool. This ADR makes
> the authored hook carry a **machine-readable quest seed** so that taking the job mints
> a real `QuestEntry` deterministically — the same way a good GM's quest is real the
> instant the player accepts it.

## Context

### The repro (live playtest, 2026-06-14, perseus_cloud, session 594dcc7e)

A player took the scripted opening's floor-boss detective hook
(`genre_packs/space_opera/worlds/perseus_cloud/openings.yaml`, opening
`solo_new_kowloon_arrival`) and worked it for ~15 turns. `quest_log` stayed `{}` the
entire time. `quests.emitted` reported `quests=0`
(`sidequest/server/websocket_handlers/quests_emit.py:84`), the `QuestsPanel` was
correctly empty, and the 29 lore fragments the session accumulated had no `QuestEntry`
to cohere under (the lore→quest projection, story 117-5).

Two distinct root causes, both real:

1. **The narrator never minted.** `record_quest`
   (`sidequest/agents/tools/record_quest.py`) is the only path that writes a structured
   `QuestEntry` into `quest_log`, and the narrator simply never called it. Minting an
   objective lived entirely in the LLM's discretion. The narrator wrote a concrete
   objective into prose and moved on; nothing in `quest_log`.

2. **The authored hook had nothing machine-readable behind it.** The floor-boss is
   prose: `tone.complication` in `openings.yaml` ("a Conglomerate floor-boss two tiers
   up has been watching you...") plus `establishing_narration` and
   `first_turn_invitation`. The `Opening` model
   (`sidequest/genre/models/narrative.py:209`) carries no structured quest. Even if the
   narrator *had* wanted to mint, the seed it would have minted was an LLM re-reading of
   prose, not authored intent.

### Why the existing lie-detector did not catch it

`detect_unminted_objective` (`sidequest/agents/dispatch_engagement_watcher.py:591`,
added the same day in commit `aa309f5d`) gates on a **14-phrase hardcoded keyword
list** (`_UNMINTED_OBJECTIVE_MARKERS`, lines 100-114: `"find the missing"`, `"your task
is"`, `"settle the debt"`, …). A noir floor-boss hook ("I have a... situation. Someone
of mine has stopped checking in.") trips none of them. This is the **Zork verb-set
anti-pattern**: a keyword matcher trying to recognise an open-ended natural-language
event. Story 117-4 owns retiring/retuning it; this ADR removes its *load-bearing* role
by making seeded offers mint deterministically, so the keyword watcher is demoted to a
backstop for *un-seeded* improvisation only.

### What already exists (reuse-first inventory)

This ADR adds **no new subsystem**. It wires authored content into three live systems:

| System | Where | What it already does |
|---|---|---|
| `QuestEntry` + `quest_log` | `game/session.py:462`, `:822` | Structured quest: `title`/`objective`/`status`/`anchor_id`. `dict[str, QuestEntry]` on the snapshot. |
| `seed_quest_spine()` | `game/quest_seed.py:36`, called `chargen_mixin.py:1399` | Seeds ONE creation-time quest from the PC's `drive`/`calling`. **Fill-don't-clobber**: defers when `active_stakes` is already authored. |
| `record_quest` tool | `agents/tools/record_quest.py:105` | Narrator-minted quests. Mints on new id, evolves on existing. Cardinality cap 32. Fires `quest.created`/`quest.updated`. |
| Intent Router (ADR-113) | `agents/intent_router.py:348` | Pre-narrator Haiku pass → `DispatchPackage`. Classifies player actions into typed, confidence-scored subsystem dispatches **before** the narrator runs. |
| Dispatch bank | `agents/subsystems/__init__.py` | Executes each `SubsystemDispatch` against a registered handler when `confidence >= threshold` (default 0.6, `:68`). |
| Engagement watcher | `agents/dispatch_engagement_watcher.py:395` | Per-subsystem witnesses prove the engine engaged what the router dispatched. |
| Opening resolution | `server/dispatch/opening.py:205`, `opening_helpers.py:31` | Selects an `Opening` at chargen-complete, stashes seed+directive on `_SessionData`. |
| Quest OTEL spans | `telemetry/spans/state_patch.py:71` (`quest.created`), `spans/quests.py:17` (`quests.emitted`) | Routed into the typed `SPAN_ROUTES` feed → GM-panel lie-detector. |

The gap is not a missing engine. It is a missing **content contract** (the seed) and a
missing **router subsystem** (`quest_offer`) to detect acceptance and fire the existing
minting path.

## Decision

**An authored hook declares a structured `quest_seed`. When the Intent Router classifies
a player turn as accepting that offer, a `quest_offer` dispatch deterministically mints a
`QuestEntry` from the seed — no narrator tool-call required.**

Four parts.

### 1. The `QuestSeed` schema, declared on authored content

A new `QuestSeed` pydantic sub-model in `sidequest/genre/models/narrative.py`, declared
as a typed field on `Opening` (alongside `tone.complication`) and on the seed-trope
model (ADR-128 deck). Because `OpeningTone` is `extra="forbid"` (`narrative.py:114`) and
`Opening` is `extra="allow"` (`:218`), the seed is a **typed field on the model**, not a
free-form passthrough — a typo fails loud at world load.

```python
class QuestSeed(BaseModel):
    """Machine-readable quest behind an authored hook (ADR-146).

    The structured form of `tone.complication`: when the player accepts this
    offer, the engine mints a QuestEntry from these fields deterministically.
    """
    model_config = {"extra": "forbid"}

    quest_id: str          # stable mint id, e.g. "floor_boss_missing_person"
    title: str             # player-facing quest title
    objective: str         # what the player must do — the concrete objective
    stakes: str = ""       # one clause of consequence; seeds active_stakes when empty
    anchor: str | None = None   # optional beat/location id → quest_anchors
    giver: str = ""        # the NPC/role offering the job (acceptance-context hint)
```

`quest_id`/`title`/`objective` map 1:1 onto `QuestEntry`
(`session.py:462`) and onto `RecordQuestArgs` (`record_quest.py:49`) — the seed is the
*authored* form of exactly what `record_quest` mints, so minting is a straight copy, not
a re-derivation. `stakes` feeds `active_stakes` (the same field `seed_quest_spine` and
`set_stakes` write). `giver` is the role naming the job, so the router's acceptance
detection has context for *which* offer a "yes" answers.

YAML shape on the opening (`openings.yaml`):

```yaml
openings:
  - id: solo_new_kowloon_arrival
    tone:
      complication: a Conglomerate floor-boss two tiers up has been watching you...
      quest_seed:
        quest_id: floor_boss_missing_person
        title: "The Floor-Boss's Missing Person"
        objective: >-
          Find out who the Conglomerate floor-boss has lost in the under-levels
          of New Kowloon, and decide whether to bring them back.
        stakes: a corporate favour owed — or a corporate enemy made — in a sector you can't leave
        giver: "the Conglomerate floor-boss"
```

The seed may also ride a seed-trope (ADR-128), so a *drawn* hook (lull/engagement draw),
not only the opening, can carry one.

### 2. The acceptance trigger: a `quest_offer` router subsystem, not a keyword list

The deterministic answer to *"the player took the job"* rides ADR-113's Intent Router.
The router is already an objective-reality classifier that runs **before** the narrator
and decomposes a turn into confidence-scored subsystem dispatches. We add one subsystem:

- **`quest_offer`** — emitted when the player's action *accepts (or declines) an offered
  job*. params: `{"quest_id": "<the seed's quest_id>", "decision": "accept" | "decline"}`.

The router knows the live offers because the resolved seed is surfaced in the router's
`<game_state>` (see §Stash, below) as `pending_quest_offers: [{quest_id, title, giver}]`.
The router's job is the thing an LLM is genuinely good at and a keyword matcher is
genuinely bad at: reading "yeah, alright, I'll look into it" / "tell me more about who's
missing" / "I take the job" / "not interested" against the *specific* offer on the table
and naming which `quest_id` it answers. This is **not** a Zork verb-set — there is no
fixed vocabulary; the classifier reads intent against named, structured offers.

The dispatch carries the standard per-dispatch `confidence` (`dispatch.py:138`) and is
gated by the existing per-subsystem threshold (`subsystems/__init__.py:68`,
default 0.6, overridable in `rules.yaml` `dispatch_confidence_thresholds`). A clear "I'll
take it" scores high and mints; an ambiguous turn scores low and degrades to a narrator
hint (no phantom mint). **Acceptance is a router classification, not a string match.**

When `decision == "accept"` and confidence clears the gate, the `quest_offer` handler
mints from the stashed seed:

```
run_quest_offer_dispatch:
  seed = snapshot.pending_quest_offers.get(params["quest_id"])
  if seed is None: emit quest_offer mismatch span (router named an unknown offer); return
  if params["decision"] == "decline":
      mark the offer consumed (declined); emit quest.offer_declined; return
  if seed.quest_id in snapshot.quest_log: return   # idempotent — already minted
  snapshot.quest_log[seed.quest_id] = QuestEntry(
      title=seed.title, objective=seed.objective, status="active", anchor_id=seed.anchor)
  if seed.anchor: snapshot.quest_anchors.append(seed.anchor)  # dedup
  if seed.stakes and not snapshot.active_stakes: snapshot.active_stakes = seed.stakes
  snapshot.pending_quest_offers.pop(seed.quest_id)             # consumed
  emit quest.seeded(...)  # the new authored-mint span
```

This reuses `QuestEntry` minting verbatim (same shape as `record_quest.py:123`). The
minting is **engine-side and deterministic** the instant the router classifies
acceptance — the narrator is no longer the load-bearing minter for authored hooks.

### 3. Coexistence: authored seed vs `seed_quest_spine` vs `record_quest`

Three minting paths, one `quest_log`. The ownership and precedence rules:

| Path | Owns | When it mints | Span |
|---|---|---|---|
| `seed_quest_spine` (77-1) | The **turn-0 spine** from the PC's `drive`/`calling`. One quest (`seed_drive`). | At chargen-complete. **Fill-don't-clobber**: defers if `active_stakes` already authored (`quest_seed.py:53`). | `quest.seeded_at_creation` |
| **`quest_offer` (this ADR)** | An **authored hook accepted in play**. Mints the seed's `quest_id`. | When the router classifies acceptance, mid-session. | **`quest.seeded`** (new) |
| `record_quest` (77-2) | Narrator-minted quests for **emergent/un-seeded** objectives. | Whenever the narrator calls the tool. | `quest.created` |

**Precedence and dedup**, keyed on `quest_id` (the single identity for all three):

- **Authored seed is fill, not clobber** — consistent with `seed_quest_spine`'s own
  doctrine. The `quest_offer` handler is idempotent: if `seed.quest_id` is already in
  `quest_log` (the narrator front-ran it with `record_quest`, or the player re-accepts),
  it no-ops. First writer wins; no double-mint.
- **`seed_quest_spine` and `quest_offer` do not collide** — the spine seeds from the PC's
  `drive` under id `seed_drive`; an authored hook seeds under its own authored
  `quest_id`. They are different quests with different ids and coexist (the spine is "who
  the PC is"; the offer is "the job the world hands them"). Both can be active.
- **`record_quest` stays the narrator's lane for the un-seeded case** — emergent
  objectives the world never authored (the player invents a goal mid-session). Authoring
  a seed does **not** remove `record_quest`; it removes the narrator's *obligation* to
  remember it for *authored* hooks. The two paths share `quest_id` namespace and the
  cardinality cap (32, `record_quest.py:46`) — the `quest_offer` mint MUST honour the
  same cap (fail loud past it, never silently drop the offer).
- **Same `quest_id` across an opening seed and a seed-trope** is a content authoring
  error caught by the pack validator, not the engine (one offer, one id).

### 4. The OTEL span: `quest.seeded`

A new span proves the authored-mint fired, distinct from the narrator-mint
(`quest.created`) and the creation spine (`quest.seeded_at_creation`):

```
SPAN_QUEST_SEEDED = "quest.seeded"
SPAN_ROUTES["quest.seeded"] = SpanRoute(
    event_type="state_transition",
    component="quest_log",
    extract=lambda span: {
        "field": "quest_log",
        "op": "seeded",                                   # authored-hook mint
        "quest_id": attrs.get("quest_id", ""),
        "title": attrs.get("title", ""),
        "source": attrs.get("source", "authored_seed"),   # vs "narrator" / "drive"
        "anchor_count": attrs.get("anchor_count", 0),
        "confidence": attrs.get("confidence", 0.0),        # the router score that minted
    },
)
```

It routes through the same `state_transition` / `component="quot_log"` shape as
`quest.created` (`state_patch.py:72`) and `quest.seeded_at_creation` (`:50`), so the
GM-panel lie-detector and the Inspector's `SPAN_ROUTES` feed surface it with zero new
plumbing (aligns with ADR-053/ADR-100 quest-coherence observability). The
`source="authored_seed"` attribute lets the panel distinguish *who minted*: the engine
from authored intent (`quest.seeded`), the narrator improvising (`quest.created`), or the
turn-0 spine (`quest.seeded_at_creation`). `confidence` records the router score that
crossed the gate, so a marginal mint is visible.

The **engagement-watcher witness** for `quest_offer` (added to `_WITNESSES`,
`dispatch_engagement_watcher.py:352`) proves the inverse: when the router dispatched
`quest_offer accept` but `quest_log` gained nothing, that is a real mismatch — surfaced
as `dispatch_engagement.quest_offer.mismatch`. This is the structurally-sound replacement
for the keyword `detect_unminted_objective`: it fires on *router-claimed-but-engine-idle*
(objective reality), not on *prose-matched-a-phrase* (string guess).

## The acceptance flow, end to end

```
chargen-complete:
  _resolve_opening_post_chargen → Opening with tone.quest_seed
  seed_quest_spine(snapshot, character)          # drive-spine, unchanged
  snapshot.pending_quest_offers[seed.quest_id] = seed   # NEW: stash the authored seed

per turn (player: "alright, I'll find out who's missing"):
  IntentRouter.decompose → DispatchPackage
    pending_quest_offers surfaced in <game_state> → router emits
    quest_offer {quest_id: floor_boss_missing_person, decision: accept} conf=0.9
  run_dispatch_bank: conf 0.9 ≥ threshold → run_quest_offer_dispatch
    mints QuestEntry(floor_boss_missing_person) → quest.seeded span
  _maybe_emit_quests: spine changed → QUESTS message → quests.emitted quests=1
  dispatch_engagement_watcher: quest_offer witness sees the QuestEntry → no mismatch
```

The player's quest log now shows "The Floor-Boss's Missing Person" the turn they take
the job — without the narrator calling a single tool.

## Consequences

**Positive**
- Authored hooks mint tracked quests deterministically; the narrator is no longer the
  single point of failure for the campaign spine of a scripted opening.
- The acceptance trigger is a real classifier (ADR-113), not a Zork verb-set — it reads
  open-ended natural language against named offers, exactly the LocalDM-vs-keyword
  lesson of story 117-4.
- The lie-detector for un-minted objectives becomes structurally sound
  (`quest_offer.mismatch` = router-vs-engine), with the keyword watcher demoted to a
  backstop for genuinely un-seeded improvisation.
- One span (`quest.seeded`) makes the authored mint visible and attributable on the GM
  panel, aligned with the existing quest-span routes.

**Negative / costs**
- One more router subsystem widens the Intent Router prompt (`intent_router.py:148`) and
  costs a few classification tokens per turn that an offer is live. Bounded: the offer is
  surfaced only while `pending_quest_offers` is non-empty, and consumed on accept/decline.
- Three connections required (no half-wiring, CLAUDE.md): prompt block + registered
  handler + engagement witness. Story 117-3 must land all three.
- `pending_quest_offers` is new snapshot state that must survive resume (persisted on
  `GameSnapshot`, not stashed only on the ephemeral `_SessionData` directive).

**Neutral**
- Authoring a seed is optional. An opening with no `quest_seed` behaves exactly as today
  (narrator-discretion minting via `record_quest`); the keyword backstop still watches it.

## Alternatives considered

**A. Keep narrator-only minting; just prompt harder.** Rejected. The repro *is* the
narrator not minting despite the tool description already saying "mint as soon as a
concrete objective forms" (`record_quest.py:56`). Stronger prompting is the illusionism
the OTEL principle exists to catch — it makes minting *more likely*, never *deterministic*.

**B. Auto-mint the seed at chargen-complete (like `seed_quest_spine`).** Rejected. A hook
the player has not yet engaged is bait (ADR-014 Diamonds & Coal: "taken bait must earn
promotion into persistent state"). Auto-minting every authored complication floods the
quest log with quests the player declined or ignored, and violates SOUL "Cost Scales with
Drama." The seed must mint *on acceptance*, which is why it rides the router.

**C. A dedicated keyword/regex acceptance detector** (the path `detect_unminted_objective`
took). Rejected as the documented anti-pattern: a fixed phrase list cannot recognise
open-ended acceptance ("yeah, fine, where do I start" / "I'm in"). Story 117-4 exists to
retire exactly this approach.

**D. A new `accept_quest` narrator tool.** Rejected. It reintroduces the same failure
mode one layer over: minting still depends on the narrator *choosing* to call the tool.
The router runs unconditionally before the narrator; classification there is not
optional, which is the whole point.

## Implementation pointer

Epic 117, story 117-3 implements:
1. `QuestSeed` sub-model + `quest_seed` field on `Opening` (and the seed-trope model) —
   `sidequest/genre/models/narrative.py`.
2. `pending_quest_offers: dict[str, QuestSeed]` on `GameSnapshot` (`game/session.py`),
   persisted and resume-safe; stashed at chargen-complete next to `seed_quest_spine`
   (`chargen_mixin.py:1399`) from the resolved Opening (`opening_helpers.py`).
3. `quest_offer` router subsystem: prompt block (`intent_router.py`), registered handler
   `run_quest_offer_dispatch` (`agents/subsystems/`), engagement witness
   (`dispatch_engagement_watcher.py:_WITNESSES`).
4. `quest.seeded` span + `SPAN_ROUTES` entry (`telemetry/spans/state_patch.py`).
5. The `perseus_cloud` floor-boss seed in `openings.yaml` (the worked exemplar above) —
   content, not engine.

Story 117-4 retunes/demotes `detect_unminted_objective` to the un-seeded backstop. Story
117-5 coheres lore fragments under the now-minted `QuestEntry` (ADR-053 + ADR-100).

## Addendum (Story 117-6): the un-seeded objective classifier replaces the keyword backstop

117-4 hardened the **seeded** path (router `quest_offer` → `detect_unminted_objective`
beeps keyword-free) but left the **un-seeded** case — a narrator who *improvises* an
open-ended objective hook mid-scene with no `quest_offer` behind it — on the brittle
13-phrase `_UNMINTED_OBJECTIVE_MARKERS` substring matcher. That matcher is the Zork
verb-set anti-pattern (SOUL: The Zork Problem): a noir "discreet job" hook
("Someone of mine stopped checking in… discreet work") trips zero curated phrases, so
`narration.unminted_objective.suspected` stayed silent (the perseus_cloud failure,
session 594dcc7e).

117-6 replaces that backstop with a real classification: a single-shot Haiku tool-use
pass (ADR-102) over the narration prose itself —
`post_narration_classifier.classify_unseeded_objective`, run by
`run_unseeded_objective_classifier_watcher` and wired into the post-narration block of
`_execute_narration_turn`. On a hit it emits the existing span tagged
`detection_method="classifier"` (vs. `"keyword"` for the retained backstop) so the GM
panel can tell a real classification from a lucky substring match. The keyword matcher
is **retained, not deleted** — demoted to a non-primary emergency backstop for the
router-silent / classifier-unavailable edge; full removal is deferred until the
classifier has soaked in playtest.

### Cost analysis (SOUL: Cost Scales with Drama)

A per-turn post-narration classification is not free, so the watcher **gates** before
spending a token. No Haiku call is made unless **all** hold:

1. narration is non-empty,
2. `quest_log` is empty (nothing minted — the same gate the sync detector uses), and
3. the turn carries **no** router `quest_offer` dispatch (the seeded 117-4 path already
   owns that case).

A quiet, already-minted, or router-seeded turn therefore costs **$0**. When it does
fire, it is one Haiku 4.5 call with a small bare-string system prompt (well below the
cacheable floor — no `cache_control` marker, which would be accepted and silently never
cache: the epic-91 trap) and `max_tokens=256`.

| Scenario | LLM calls | Approx. cost |
|----------|-----------|--------------|
| Quiet turn / combat / already-minted / router-seeded | 0 | $0 |
| Un-seeded turn with objective-bearing prose | 1 (Haiku, ~1K in / ~50 out) | ~$0.001 |

Spend is recorded under caller `unseeded_objective_classifier` (distinct from
`intent_router`) and runs the ADR-134 pre-flight ceiling check + per-session ledger, so
the [COST-1] forensics attribute it cleanly. Activation is **gated-always-on** (run on
every un-seeded objective-eligible turn); a future drama-tier gate could narrow it
further if the per-session count proves material, but at ~a-few-calls-per-session the
brittleness it removes is worth the sub-cent cost.

## Addendum (Story 158-43): Anchor-Crossing Acceptance — a Deterministic Second Mint Trigger

**Approved by Keith 2026-07-02.** This addendum closes a gap in the original decision;
it is not a redesign.

### The gap this ADR left open

**ADR-146 as written covered only giver-hook offers.** The acceptance trigger (§2) is
the Intent Router's `quest_offer` classification, and that classification reads the
player's words against a *named offer from a giver* — "yeah, I'll take the job" answered
to "the Conglomerate floor-boss." The worked exemplar, the router prompt, and the
`giver` field's own docstring ("so the router's acceptance detection has context for
*which* offer a 'yes' answers") all assume someone made the offer and the player answers
them.

**Self-directed / giver-less seeds were never covered.** beneath_sunden's
`the_unspent_hold` (`giver: ""`, `anchor: the_dropmouth`) is authored with the comment
"acceptance is the descent, not a yes to anyone." There is no NPC to answer; the player
accepts by *doing the objective*. The router classifies that turn as `movement`, the
`quest_offer` subsystem never fires, and the offer sits in `pending_quest_offers`
forever — the Quests tab stays blank. Live repro: sq-playtest 2026-06-27,
beneath_sunden, Harpo, descending the Dropmouth.

### The decision

**A second, deterministic mint trigger, independent of the router:** when a seated PC
makes a *genuine region transition into* a pending seed's `anchor` region, the engine
mints the offer — no LLM in the loop.

- **Seam:** `mint_on_anchor_crossing(snapshot, *, pc_name, from_region, to_region)` in
  `sidequest/game/quest_offer.py`, called from the `pc_region` genuine-change block of
  `GameSnapshot._apply_world_patch_inner` (beside `notify_region_transition`) — the
  choke point that movement dispatch, seam descent (`game/seams/deep_descent.py`), and
  both procedural relocation paths all route through.
- **Trigger scope: ANY anchor-bearing seed** — giver-less AND giver-hook offers that
  carry an `anchor` mint on crossing. Walking into the job site accepts the job the
  same as saying yes.
- **All matching seeds mint, not first-match.** Two seeds anchored on the same region
  are both accepted by the crossing; leaving the second stranded would re-create the
  exact stuck-offer bug this trigger exists to fix.
- **First-placement exclusion:** a falsy `from_region` (spawn / turn-0 placement) never
  mints — acceptance requires a genuine *transition*. The `current_region`
  spawn/teleport anchor branch deliberately does not call the seam.
- **Respect the decline:** a declined/consumed offer stays gone. No tombstone state is
  needed — the decline path pops the offer from `pending_quest_offers`, and the seam
  only scans what is still pending.
- **First-writer-wins, unchanged:** each mint flows through the existing idempotent
  `mint_quest_offer`; if the router or narrator `record_quest` front-ran it, the
  crossing no-ops (and still consumes the offer, per the existing leak-prevention
  doctrine). The cardinality cap stays loud and propagates out of the world-patch apply
  (No Silent Fallbacks) — a failed mint never silently consumes the offer.
- **Router extension: deferred.** The `quest_offer` prompt is NOT extended to cover
  self-directed seeds; the deterministic path fully covers the failing case and keeps
  per-turn token cost flat.

### OTEL

The `quest.seeded` span's `source` vocabulary gains **`anchor_crossed`** (vs
`authored_seed` for the router's verbal accept), with `confidence=1.0` — a state watch
is certainty, not a classifier score — and `pc_name` in the attrs naming whose crossing
minted. The existing `SPAN_ROUTES` extraction passes `source` through untouched, so the
GM panel distinguishes "Haiku classified a yes" from "engine watched the crossing" with
zero new plumbing.

### Known limitation

Region-mode worlds (oz/wonderland/gulliver-style cartography) relocate PCs in the
`narration_apply` region-mode block and apply **no** `pc_region` patch by design (Story
59-30's Site A/Site B split). An anchor-bearing seed authored in a region-mode world
would not mint on crossing. No such seed exists today; if one is authored, the same
seam must be called from Site B (a follow-up story, not this one).

**Implementation:** Story 158-43 — `mint_on_anchor_crossing` + the session-block call +
the span-vocabulary extension, with the RED contract in
`sidequest-server/tests/game/test_anchor_crossing_mint.py` (includes the real
`the_unspent_hold` descent as a wiring test).
