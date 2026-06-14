# Design — Quest-Seed Authoring Contract: authored hooks carry a machine-readable seed that mints a tracked quest on router-detected acceptance

**Date:** 2026-06-14
**Author:** Architect (Atlas the Endurer), at Keith's direction
**Status:** Draft — pending user review
**Promote to:** ADR-146 (companion ADR authored alongside this spec).
**Context:** Epic 117 ("Quest-seed lifecycle — authored hooks mint tracked quests, and a lie-detector that actually catches silent objectives"), story 117-2. Direct response to the 2026-06-14 perseus_cloud playtest (session 594dcc7e): a player took the scripted floor-boss detective hook, worked it ~15 turns, and `quest_log` stayed `{}`. This spec is the implementation design for story 117-3.

---

## Why

When a human DM hands you a job, the quest is real the moment you take it — not when the
DM remembers to write it on an index card. SideQuest's authored opening hooks have been
the index card no one wrote.

The repro: opening `solo_new_kowloon_arrival`
(`sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/openings.yaml`) declares
a floor-boss complication in **prose only** (`tone.complication`). The narrator threaded
it into a 15-turn detective arc, wrote a concrete objective into narration — and never
called `record_quest`. Result: `quests.emitted quests=0`, an empty QuestsPanel, and 29
lore fragments with no `QuestEntry` to cohere under.

Two root causes:

1. Minting a quest is the narrator's discretion (`record_quest` is the only writer of a
   structured `QuestEntry`), and the narrator did not exercise it.
2. The authored hook had nothing machine-readable behind it — even a willing narrator
   would mint an LLM re-reading of prose, not authored intent.

The existing safety net, `detect_unminted_objective`
(`sidequest-server/sidequest/agents/dispatch_engagement_watcher.py:591`), gates on a
14-phrase keyword list (`_UNMINTED_OBJECTIVE_MARKERS`, lines 100-114). A noir hook trips
none of them. This is the Zork verb-set anti-pattern story 117-4 exists to retire.

## What changes (the contract)

An authored hook declares a **`quest_seed`**. The Intent Router (ADR-113) classifies the
turn the player accepts that offer. A new `quest_offer` dispatch mints a `QuestEntry`
from the seed deterministically — no narrator tool-call. One new OTEL span (`quest.seeded`)
makes the authored mint visible and attributable on the GM panel.

No new engine is built. This wires authored content into `QuestEntry`/`quest_log`, the
Intent Router dispatch bank, and the typed `SPAN_ROUTES` feed — all live.

## Grounding (real code, real fields)

| Thing | File:line | Note |
|---|---|---|
| `QuestEntry` | `game/session.py:462` | `title`/`objective`/`status="active"`/`anchor_id` |
| `quest_log: dict[str, QuestEntry]` | `game/session.py:822` | the snapshot's quest store |
| `seed_quest_spine()` | `game/quest_seed.py:36` | drive-spine seed; **fill-don't-clobber** at `:53` |
| seed call site | `chargen_mixin.py:1399` | where the spine seeds at chargen-complete |
| `record_quest` | `agents/tools/record_quest.py:105` | narrator mint; cardinality cap 32 at `:46`; mint shape at `:123` |
| `RecordQuestArgs` | `agents/tools/record_quest.py:49` | `quest_id`/`title`/`objective`/`status`/`anchor` — the seed mirrors this |
| `Opening` model | `genre/models/narrative.py:209` | `extra="allow"` top-level |
| `OpeningTone` | `genre/models/narrative.py:114` | `extra="forbid"` — `complication` lives here at `:119` |
| Opening resolution | `server/dispatch/opening.py:205`, `opening_helpers.py:31` | selects + stashes Opening at chargen-complete |
| IntentRouter | `agents/intent_router.py:348`; subsystem prompt `:148-273` | pre-narrator classifier → `DispatchPackage` |
| `SubsystemDispatch` | `protocol/dispatch.py:122`; `confidence` field `:138` | typed dispatch with confidence |
| dispatch bank + threshold | `agents/subsystems/__init__.py:68` | default 0.6; `rules.yaml` `dispatch_confidence_thresholds` override |
| engagement witnesses | `dispatch_engagement_watcher.py:352` (`_WITNESSES`) | per-subsystem engine-engaged checks |
| `quest.created` span | `telemetry/spans/state_patch.py:71` + fn `:215` | narrator-mint span (template for `quest.seeded`) |
| `quest.seeded_at_creation` span | `telemetry/spans/state_patch.py:49` | creation-spine span |
| `quests.emitted` span | `telemetry/spans/quests.py:17` | QUESTS-projection lie-detector |
| keyword lie-detector | `dispatch_engagement_watcher.py:591` (`detect_unminted_objective`) | the anti-pattern; 117-4 retunes |

## Implementation plan (story 117-3)

### 1. `QuestSeed` model + authored field — content schema

`sidequest/genre/models/narrative.py`:

```python
class QuestSeed(BaseModel):
    """Machine-readable quest behind an authored hook (ADR-146)."""
    model_config = {"extra": "forbid"}

    quest_id: str
    title: str
    objective: str
    stakes: str = ""
    anchor: str | None = None
    giver: str = ""
```

- Add `quest_seed: QuestSeed | None = None` to `OpeningTone` (next to `complication`,
  `narrative.py:119`). It MUST be a typed field — `OpeningTone` is `extra="forbid"`, so a
  free-form key would fail load.
- Add the same optional field to the seed-trope model (ADR-128) so a *drawn* hook can
  carry a seed, not only an opening.
- **Validation (pack validator, not unit test — per the no-content-in-unit-tests rule):**
  a `quest_seed.anchor` that names no real beat/location, or two seeds sharing a
  `quest_id` within a world, is a content error caught at pack-validate time.

### 2. Resume-safe stash — snapshot state

`sidequest/game/session.py`:

```python
pending_quest_offers: dict[str, QuestSeed] = Field(default_factory=dict)
```

Persisted on `GameSnapshot` (NOT only on the ephemeral `_SessionData` opening directive,
which is consumed once and lost on resume). Populated at chargen-complete from the
resolved Opening's `tone.quest_seed`, right beside the existing `seed_quest_spine` call
(`chargen_mixin.py:1399`); the resolved Opening is reachable there via
`_populate_opening_directive_on_chargen_complete` / `_resolve_opening_post_chargen`.

```python
# chargen-complete, after seed_quest_spine(materialized, character):
if opening.tone.quest_seed is not None:
    materialized.pending_quest_offers[opening.tone.quest_seed.quest_id] = opening.tone.quest_seed
```

### 3. `quest_offer` router subsystem — three connections (no half-wiring)

**(a) Prompt block** in `intent_router.py` (the subsystem enumeration, `:148-273`):

```
- quest_offer: the player ACCEPTS or DECLINES a job an NPC/role has offered.
  params={"quest_id": "<one of game_state.pending_quest_offers[].quest_id>",
          "decision": "accept" | "decline"}.
  Emit quest_offer ONLY when game_state.pending_quest_offers is non-empty AND the
  player's action answers one of those offers — taking the job ("I'll do it", "fine,
  where do I start", "I'm in", "tell me who's missing and I'll find them") OR refusing
  it ("not interested", "I'll pass"). quest_id MUST be one of the listed offer ids —
  never invent one. Confidence scores how clearly the player committed to/refused THIS
  offer; merely asking a clarifying question that does not commit is low confidence.
```

Surface live offers in the router's `<game_state>` as
`pending_quest_offers: [{quest_id, title, giver}]` (objective + giver give the classifier
the context to bind a "yes" to the right offer). This is **classification against named
structured offers, not a fixed phrase list** — the ADR-113 lesson.

**(b) Registered handler** `run_quest_offer_dispatch` in `agents/subsystems/` (registered
in `subsystems/__init__.py` alongside the eight existing handlers):

```python
async def run_quest_offer_dispatch(dispatch, snapshot, ...) -> SubsystemOutput:
    quest_id = dispatch.params.get("quest_id")
    decision = dispatch.params.get("decision", "accept")
    seed = snapshot.pending_quest_offers.get(quest_id)
    if seed is None:
        # router named an unknown offer — surface, do not mint (No Silent Fallbacks)
        return SubsystemOutput.mismatch(evidence=f"quest_id={quest_id!r} not in pending_quest_offers")
    if decision == "decline":
        snapshot.pending_quest_offers.pop(quest_id, None)
        quest_offer_declined_span(quest_id=quest_id)
        return SubsystemOutput.ok()
    if quest_id in snapshot.quest_log:
        snapshot.pending_quest_offers.pop(quest_id, None)   # idempotent: already minted
        return SubsystemOutput.ok()
    if len(snapshot.quest_log) >= _QUEST_LOG_CARDINALITY_CAP:   # share the cap (record_quest.py:46)
        return SubsystemOutput.mismatch(evidence="quest_log cardinality cap reached")
    anchor_count = 0
    snapshot.quest_log[quest_id] = QuestEntry(
        title=seed.title, objective=seed.objective, status="active", anchor_id=seed.anchor)
    if seed.anchor and seed.anchor not in snapshot.quest_anchors:
        snapshot.quest_anchors.append(seed.anchor)
        anchor_count = 1
    if seed.stakes and not snapshot.active_stakes.strip():
        snapshot.active_stakes = seed.stakes          # fill-don't-clobber
    snapshot.pending_quest_offers.pop(quest_id, None)
    quest_seeded_span(quest_id=quest_id, title=seed.title, source="authored_seed",
                      anchor_count=anchor_count, confidence=dispatch.confidence)
    return SubsystemOutput.ok()
```

Confidence gating is automatic — the dispatch bank only runs a handler when
`confidence >= threshold` (`subsystems/__init__.py:68`). Add an optional per-pack override
key `quest_offer` to `dispatch_confidence_thresholds` if a pack wants it tighter/looser.

**(c) Engagement witness** `_check_quest_offer_engaged` in
`dispatch_engagement_watcher.py:_WITNESSES` (`:352`) + `_DISPATCHED_TYPE_KEY` (`:340`):

```python
def _check_quest_offer_engaged(dispatch, snapshot, player_id) -> str | None:
    quest_id = _required_str_param(dispatch, "quest_id")
    if quest_id is None:
        return _MALFORMED_EVIDENCE.format(subsystem="quest_offer", key="quest_id")
    if dispatch.params.get("decision") == "decline":
        return None  # decline engages by consuming the offer, not by minting
    if quest_id in snapshot.quest_log:
        return None
    return f"quest_offer accept for {quest_id!r} but quest_log has no such entry (engine did not mint)"
```

This is the structurally-sound lie-detector: it fires on *router-claimed-but-engine-idle*
(`dispatch_engagement.quest_offer.mismatch`), replacing the keyword guess.

### 4. `quest.seeded` OTEL span

`telemetry/spans/state_patch.py` — mirror `quest_created_span` (`:215`) / its route (`:71`):

```python
SPAN_QUEST_SEEDED = "quest.seeded"
SPAN_ROUTES[SPAN_QUEST_SEEDED] = SpanRoute(
    event_type="state_transition",
    component="quest_log",
    extract=lambda span: {
        "field": "quest_log",
        "op": "seeded",
        "quest_id": (span.attributes or {}).get("quest_id", ""),
        "title": (span.attributes or {}).get("title", ""),
        "source": (span.attributes or {}).get("source", "authored_seed"),
        "anchor_count": (span.attributes or {}).get("anchor_count", 0),
        "confidence": (span.attributes or {}).get("confidence", 0.0),
    },
)

def quest_seeded_span(*, quest_id, title, source, anchor_count, confidence, _tracer=None):
    with Span.open(SPAN_QUEST_SEEDED, {...}, tracer_override=_tracer):
        ...
```

Same `state_transition` / `component="quest_log"` shape as the other quest spans, so the
GM-panel Inspector picks it up with no new plumbing (ADR-053/ADR-100 quest-coherence
observability). A `quest.offer_declined` span is optional but cheap and worth it.

### 5. The perseus_cloud exemplar — content

`sidequest-content/.../perseus_cloud/openings.yaml`, opening `solo_new_kowloon_arrival`:

```yaml
    tone:
      register: grounded, grimy, neon-lit
      stakes: low for now — but in the Cloud, work always finds the people standing still
      complication: a Conglomerate floor-boss two tiers up has been watching you for
        longer than idle interest explains
      quest_seed:
        quest_id: floor_boss_missing_person
        title: "The Floor-Boss's Missing Person"
        objective: >-
          Find out who the Conglomerate floor-boss has lost in the under-levels of
          New Kowloon, and decide whether to bring them back.
        stakes: a corporate favour owed — or a corporate enemy made — in a sector you can't leave
        giver: "the Conglomerate floor-boss"
```

The MP opening `mp_glitter_consignment` (the missing-consignment hook) can carry a
parallel seed (`quest_id: glitter_missing_consignment`) — a natural second exemplar, but
not required for 117-3.

## Coexistence rules (the three minting paths)

Keyed on `quest_id`, one `quest_log`:

- **`seed_quest_spine`** (`quest_seed.py`) owns the **turn-0 drive spine** (`seed_drive`).
  Different id from any authored offer; they coexist (who-the-PC-is vs the-job-the-world-hands).
- **`quest_offer`** (this design) owns **authored hooks accepted in play**. Mints the
  seed's `quest_id`. **Idempotent / first-writer-wins** — if the narrator already minted
  the same id via `record_quest`, or the player re-accepts, it no-ops.
- **`record_quest`** (`record_quest.py`) stays the narrator's lane for **emergent,
  un-seeded** objectives. Authoring a seed removes the narrator's *obligation* for
  authored hooks, not the tool.
- All three share the cardinality cap (32) and the `quest_id` namespace; the `quest_offer`
  handler honours the cap and fails loud past it.

## Acceptance criteria (for TEA in 117-3)

1. An `Opening` with `tone.quest_seed` loads; a malformed seed (missing `quest_id`/
   `title`/`objective`) fails pydantic load loudly.
2. At chargen-complete, the seed lands in `snapshot.pending_quest_offers` keyed by
   `quest_id`, and survives a save→load round-trip (resume-safe).
3. **OTEL-driven wiring test:** drive a turn where the (mocked) router emits
   `quest_offer {decision: accept}` at confidence ≥ threshold against a stashed seed →
   assert `quest_log` gains the `QuestEntry`, `quest.seeded` span fires with
   `source="authored_seed"`, and `quests.emitted` fires with `quests=1`. (Span assertion,
   not source-grep — per the No-Source-Text-Wiring-Tests rule.)
4. Idempotency: a second `quest_offer accept` for an already-minted `quest_id` does not
   double-mint and does not error.
5. Below-threshold confidence does NOT mint (degrades to narrator hint).
6. `decision: decline` consumes the offer (removes it from `pending_quest_offers`) and
   does not mint.
7. Engagement witness: a `quest_offer accept` dispatch whose engine minted nothing emits
   `dispatch_engagement.quest_offer.mismatch`.

## Out of scope (other 117 stories)

- **117-4** retunes/demotes `detect_unminted_objective` to the un-seeded backstop (do NOT
  delete it in 117-3; it still watches narrator improvisation with no authored seed).
- **117-5** coheres lore fragments under the minted `QuestEntry` (ADR-053 + ADR-100).
- Backfilling `quest_seed` across other worlds' openings is content work, tracked
  separately; 117-3 ships the engine + the one perseus_cloud exemplar.

## Risks / watch-outs

- **Router prompt bloat / token cost.** The offer block fires the subsystem only while
  `pending_quest_offers` is non-empty; surface offers in `<game_state>` only when present.
- **Resume correctness.** `pending_quest_offers` MUST be on `GameSnapshot` and persisted —
  the opening directive (`_SessionData`) is consumed once and gone on reconnect.
- **Confidence calibration.** The default 0.6 threshold is shared infra; if seeded mints
  fire too eagerly on clarifying questions, tune via `dispatch_confidence_thresholds`
  per pack rather than hardcoding a `quest_offer` special case.
