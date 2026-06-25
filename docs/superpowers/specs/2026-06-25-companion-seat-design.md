# Companion Seat — Design Spec

**Status:** Approved (brainstorming complete 2026-06-25)
**Author:** Architect (design mode)
**Supersedes:** nothing — new direction

## Context

`sidequest-understudy` is a naive-player playtest harness: bots join a real
session through the React UI in a headless browser, perceive the page like a
screen reader, and role-play a seat — the *naivety invariant* makes interface
confusion a finding. It is charter-bound to never ship to players.

This spec describes a **new direction** that reuses understudy's bones for a
different goal: an AI **companion** — Donut to your Carl (*Dungeon Crawler
Carl*) — that joins *your live game* as its own seat and is **a character you
care about**. It is not a playtest instrument; it ships.

### Decided shape (from brainstorming)

- **Role is a configurable dial**, re-centered by the Donut reference as
  *willful↔deferential × bonded↔transactional*: **pet** (intimate, willful,
  theatrical) → **peer** → **hireling** (distant, transactional, knows less).
- **Own seat.** The companion joins as a full participant — its own PC.
- **External protocol client.** It talks to the engine over the **WebSocket
  protocol** (no browser — driving a headless Chromium per companion is pure
  cost). Keep understudy's *brain* and *persona/role* ideas; drop its
  *perception (aria-snapshot)* and *actuation (Playwright)* layers.
- **Type-scoped perception.** The role dial gates knowledge: a **pet** is privy
  to its owner's inner character view; a **hireling** sees only the publicly
  observable. Enforced by the engine's existing per-player perception firewall.
- **Full mechanical PC from day one** — chargen, abilities, dice,
  confrontations.
- **Persistent + evolving personality** — the relationship and personality
  drift across sessions; reuse the engine's disposition/OCEAN/relationship
  systems rather than rebuild them.
- **Purpose: a character you care about.** Voice/personality is the
  load-bearing craft; the bar is "good enough to make Keith care."

## Goals

- A full-PC companion that joins a live session over WS and plays beside a human.
- A configurable role dial that sets both behavior and perception scope.
- A bond that evolves — within a campaign (v1) and across campaigns (v2).
- Maximal reuse of the existing engine; the smallest honest server change.
- Mechanical correctness guaranteed by CI; experiential quality judged by play.

## Non-Goals

- No browser/UI driving. No findings/report pipeline (that's understudy).
- No re-balancing of mechanics — the companion is a player the narrator
  adjudicates, same as any human (SOUL.md *Bind the Ruleset*).
- v1 does **not** include cross-campaign memory or personality drift (that's v2).
- No owner-consent/multi-tenant bond authority in v1 (cooperative local use).

---

## Section 1 — Architecture & boundaries

Three parts: one new package, one small server seam, the rest reuse.

```
   YOUR LIVE GAME (unchanged)                      THE NEW THING
 ┌───────────────────────────┐            ┌──────────────────────────────┐
 │  React UI  (you + table)  │            │   sidequest-companion  (NEW) │
 │      │  WebSocket :8765    │            │   • WS protocol client       │
 └──────┼────────────────────┘            │   • state mirror             │
        │            same game_slug        │   • run loop ("play beside") │
        ▼            ▼────────────────────▶│   • companion persona/voice  │
 ┌─────────────────────────────────────┐  │   • role dial (pet↔hireling) │
 │        sidequest-server             │  └───────────┬──────────────────┘
 │  narrator · turn barrier · chargen  │              │ depends on
 │  dice/confrontation · perception    │              ▼
 │  disposition/OCEAN · Postgres       │  ┌──────────────────────────────┐
 │                                     │  │  shared SEAT CORE  (extracted │
 │  + bond registry        ◀───────── │  │  from understudy)            │
 │  + CompanionVisibilityStage  (NEW)  │  │  • model backends            │
 └─────────────────────────────────────┘  │  • persona AXIS model        │
              ▲ also depends on            │    (+ new role dial)         │
              └─────────────────────────── │                              │
                  understudy (test harness)└──────────────────────────────┘
```

**Reused, untouched (server engine):** narrator, submit-and-wait turn barrier,
chargen FSM, dice/confrontation/Fate resolution, the perception firewall's
*tool layer*, disposition/relationship/OCEAN data shapes, per-session Postgres.
The companion is just another player to all of it.

**Extracted into a neutral shared core (`sidequest-seat-core`):** the model
backends (`brain/llm/*` — model-agnostic `decide()`) and the persona **axis
model** (`Archetype` + the new role dial). A shipping artifact must not depend
on a test harness, so the charter-neutral bits become a third package both
understudy and companion depend on. Naivety stays behind in understudy.

**New:**
- *Companion package:* WS client (connect → chargen → turns → dice/confrontation
  + state mirror), companion voice/role persona (NOT the naive frame), run loop,
  companion definition as authored YAML content.
- *Server (v1):* bond registry on `SessionRoom` + one `CompanionVisibilityStage`
  in the broadcast projection.
- *Server (v2):* cross-campaign companion store + revived OCEAN evolution loop.

**Two invariants the boundary buys for free:**
1. **The companion is a player, never a narrator.** It can only emit
   `PLAYER_ACTION` for its *own* character and respond to roll prompts; the
   narrator adjudicates. SOUL.md's *Test* holds structurally — no channel to
   author anyone else's character, including yours.
2. **Naivety does not cross into the companion.** The shared core carries no
   screen-reader/affordance assumptions; those live only in understudy's persona
   prompt, which the companion doesn't import.

**v1 / v2 line:**
- **v1 — a Donut you can play beside:** companion package + server bond/perception
  seam + within-campaign evolving bond (free from live disposition machinery).
- **v2 — a Donut who remembers:** cross-campaign persistence key + revived OCEAN
  drift + memory digest.

---

## Section 2 — Components

### A) `sidequest-companion` (new package)

| Module | Job | understudy analog |
|---|---|---|
| `cli.py` | Typer entry: `companion play <companion.yaml> --session <game_slug\|url>` | `understudy run` |
| `manifest.py` | Loads companion definition (see D) + session target. Fails loud. | `manifest.py` |
| `protocol/` | WS client: handshake, **typed message codec**, **state mirror** merging `NARRATION`/`PARTY_STATUS`/`NARRATION_END` deltas + `seq` backfill (ADR-026/027/133). | *replaces* browser read |
| `perception/` | Assembles per-turn **context** for the brain from the mirror (server already scoped by bond). | `perception/snapshot.py` |
| `brain/` | Calls shared-core backend with the **companion decision contract** → `CompanionIntent`. | `brain/core.py` |
| `persona/` | The **voice/role** system prompt — "you *are* this character, beside your human; your bond, manner, current standing." | `persona/` (not the naive frame) |
| `actuation/` | `CompanionIntent` → outgoing message: `PLAYER_ACTION`/`DICE_THROW`/`FATE_THROW`/beat-pick/`YIELD`. | `actuation/act.py` |
| `dice/` | Fair-RNG faces per die system (d20, 2d6, 4dF). Physics-is-the-roll. | — (new) |
| `orchestrate/` | Run loop: connect → seat → chargen → main loop + guards. | `orchestrate/` |

**`CompanionIntent`** verbs: `ACT` (in-character prose — IntentRouter extracts
any ability from the text, so this covers most of "playing"), `ROLL`/`BEAT`/
`DEFEND` (responses to server-pushed `DICE_REQUEST`/`CONFRONTATION`/
`FATE_DEFEND_REQUEST`), `ASIDE` (OOC), `YIELD`.

### B) `sidequest-seat-core` (extracted, charter-neutral)

- `llm/` — model backends (`claude_p`/`anthropic`/`ollama`) + factory +
  `ActionModel` protocol + `DecideResult`. Lifted from understudy `brain/llm`.
- `persona/axis.py` — `Archetype` axis dataclass **plus the role axis**
  (`willful↔deferential × bonded↔transactional` naming pet/peer/hireling).
- Data models + backends only — no prompts, no naivety, no WS, no browser.

### C) Server seam (v1 — the entire server footprint)

- **Bond registry:** `SessionRoom._companion_bonds: {companion_player_id →
  (owner_player_id, relationship_type)}`, populated when the companion declares
  itself at connect (small protocol addition: companion metadata on the
  connect/seat handshake — `{companion_of, relationship}`).
- **`CompanionVisibilityStage`** in the broadcast projection: a **pet's**
  outgoing events get the owner's private routes (`NARRATION_SEGMENT`,
  `SECRET_NOTE`) merged into `visible_to`; a **hireling is a vanilla separate
  seat** needing no special handling. The stage's only real job is *pet-widening*.
- **OTEL:** `companion.bond_resolved`, `companion.routed_as_<type>` spans (the
  GM-panel lie-detector mandate).

### D) Companion definition is authored content (YAML)

Drop-in file: name, species, role (pet/peer/hireling), personality/voice,
`bonded_to` (which human), genre/world, model backend — the way understudy
archetypes drop into a folder. Long-term home: a first-class companion content
type in `sidequest-content`. v1 carries example definitions in-package.

### Explicit decision — protocol types

The companion needs typed versions of ~15 message types. Options: import the
server's `protocol/` models (couples to engine), extract `protocol/` into a
shared package (heavy, out of scope), or hand-write a **thin typed client
subset** validated by a wiring test against the real server. **Decision: thin
subset for v1** — smallest blast radius; slots aside cleanly if protocol
extraction ever happens. The wiring test guards against contract drift.

---

## Section 3 — Data flow

**Lifecycle (once per session):**

1. **Launch** — `companion play donut.yaml --session <game_slug>` loads the
   definition, resolves the model backend, builds the persona.
2. **Connect** — `SESSION_EVENT{connect, game_slug, player_name, companion_of,
   relationship}`. Server resolves the companion's own distinct identity, mints
   `player_id`, records the bond, emits `companion.bond_resolved`. Same
   `game_slug` → same `SessionRoom` as the human.
3. **Seat** — `PLAYER_SEAT{character_slot}` → `SEAT_CONFIRMED`. Now a seated
   player the narrator must account for.
4. **Chargen** — if new to this campaign, server drives `CHARACTER_CREATION`
   FSM; the brain answers each scene *in persona*. If resuming, the sheet is
   already persisted under this `game_slug`. Then `SESSION_EVENT{ready}`.

**One play-turn:**

- Server pushes `NARRATION` (+ scoped `state_delta`), `PARTY_STATUS`,
  reactive `RELATIONSHIPS`/`QUESTS`/`FATE_STATE`, `TURN_STATUS`. The mirror
  merges deltas. A **pet's** stream includes owner-private `NARRATION_SEGMENT`;
  a **hireling's** never contains them — **the companion never scopes its own
  knowledge; the server already did.**
- `TURN_STATUS{my seat: pending}` → "it's my turn."
- `brain.decide(persona + scoped context + history + current standing)` →
  `CompanionIntent.ACT(...)`. The standing comes from the live
  `RELATIONSHIPS`/disposition projection, so **the voice shifts as the bond
  shifts** (warmer, frostier, wounded).
- `actuation` sends `PLAYER_ACTION{action, round}` (optionally `ACTION_REVEAL`
  for table courtesy). The barrier waits for all seats; the round resolves;
  the companion consumes the new `NARRATION`; loop.

**Dice/confrontation branch:** on `DICE_REQUEST`/`CONFRONTATION`/
`FATE_DEFEND_REQUEST` aimed at the companion, the brain returns
`ROLL`/`BEAT`/`DEFEND`; actuation generates **fair faces** matching the
requested die system and sends `DICE_THROW`/`FATE_THROW`; consumes
`DICE_RESULT`/`CONFRONTATION_OUTCOME`.

**Cadence:** event-driven (not turn-capped). Runs as long as the session does;
exits on session end, disconnect, or operator stop.

---

## Section 4 — The bond: perception scope + evolving personality

The bond has two faces. **Perception scope** (pet vs hireling) is the registry
+ visibility stage (Sections 2–3). **Personality + standing** is this section.

**Honesty note.** The disposition system, `DispositionBeat` log, `OceanProfile`,
band-derivation, and `RELATIONSHIPS` projection are live, reusable shapes — but
they model an **NPC's global standing** (one scalar all players share). The
companion's bond is the *opposite arrow*: **the companion's feeling toward one
specific human**, per-`(companion, human)`. The engine does not model per-PC
relationships today (explicit YAGNI in ADR-136). So the bond is a **new instance
keyed differently, built from existing shapes** — ~85% reused parts, small new
wiring. Not free, but cheap.

**v1 — within-campaign bond (lightweight, legible):**
- **Personality:** static `OceanProfile` seeded from the authored definition
  (`OceanProfile.from_authored`, live). Shapes the voice; no drift yet.
- **Standing:** a **bond ledger** on the companion's per-session state — a
  disposition value + a `DispositionBeat` log (reused shape), keyed to the human.
  Beats recorded when narrative events touch the bond. Current band + one-line
  "why" feed the persona prompt each turn **and** emit an OTEL span per beat.
- **Persistence:** rides the per-session Postgres blob. Evolves over the
  campaign; resets between campaigns.
- **Open sub-decision (for the plan):** beats emitted by the **narrator**
  (treat the bond as a patchable world-patch target — cleaner, slightly more
  server) vs **self-reported** by the companion as a structured turn field the
  server records (zero narrator change, cooperative). *Lean: narrator-emitted
  for legibility.*

**v2 — cross-campaign, growing personality (the one large new build):**
- **Cross-session store:** a `companions` table keyed to `(companion_id,
  human_identity)` holding personality (`OceanProfile`), bond standing + beat
  log, and a **memory digest**. Loaded on connect, merged into the fresh
  session. This is the single load-bearing persistence gap (per-session storage
  has no cross-campaign key today).
- **Personality drift:** revive the **dormant** ADR-042 loop —
  `PersonalityEvent` → `OceanShiftProposal` → apply — so weighty events nudge
  the OCEAN between campaigns. Shape exists from the Rust era; never ported.
- **Memory re-injection:** the digest is summarized forward and re-injected
  next campaign.

---

## Section 5 — Error handling & reliability

A playtest bot's confusion is data; a companion's failure is a table-stopper.
Every failure mode must degrade without holding real humans hostage.

1. **Never stall the table.** The barrier waits for the companion's seat.
   - **Decide-timeout → auto-`YIELD`.** Brain too slow → pass, don't hang. The
     AI yields to humans, never the reverse.
   - **Absence yields, doesn't pause.** A human drop triggers `GAME_PAUSED`
     (correct for humans). A companion drop must **not** hard-pause the table;
     the companion seat auto-yields after a short grace. Configurable, default
     yield.
   - **Reconnect via `last_seen_seq` backfill** so a blip replays missed events.
2. **Model failure → safe pass, never fabrication.** Malformed brain output is
   logged as a *model* failure and degrades to `YIELD` + OTEL warning — never a
   guessed `PLAYER_ACTION` the persona didn't choose.
3. **Perception firewall is default-closed.** Unresolved/malformed/unknown bond
   → treat as **hireling** (least access) and log loudly; never default to pet.
   *Trust boundary (flagged for plan):* v1 targets cooperative local use (the
   human launches the companion pointed at their own session). Multi-tenant
   deployment needs owner-consent / server-side bond authority (ADR-119) before
   granting pet access — noted, not built in v1.
4. **Cost guards (ADR-134).** The companion spends as its own brain (per turn)
   and as an extra participant the narrator narrates. It carries understudy's
   token/wall-clock ledger + per-turn cap, and respects the server's ADR-134
   ceiling (session hard-kill → companion exits cleanly). Model default favors
   voice quality at a sane tier, configurable.
5. **Loud failure on unknown protocol/chargen states.** An unhandled
   `input_type` or message → operator-visible error, no garbage submission, no
   guess. Doubles as the contract-drift tripwire.
6. **"Act only for myself" guarantee.** Structural (own `PLAYER_ACTION` only) +
   persona prompt forbids narrating others (SOUL.md *Test*).

---

## Section 6 — Testing

Project rule: every suite needs a wiring test proving the thing is reachable
from production paths. Only scripted brain is `fake`; everything else is a real
LLM.

**Unit layer:**
- *Shared core:* model-backend tests move with the extraction; new role-axis
  tests (pet/peer/hireling → expected axis values; unknown role fails loud).
- *Companion package:* `manifest` load + fail-loud; `protocol` codec
  round-trips; **state-mirror merge** (delta sequence → expected mirror, incl.
  `seq` backfill); `actuation` intent→message mapping (faces match requested
  `die_system`); **error paths** (malformed→`YIELD`, timeout→`YIELD`,
  cost-ceiling→stop); `dice` fairness per system.
- *Server seam:* bond registry records on connect; `CompanionVisibilityStage`
  (pet sees owner-private, hireling doesn't, **unresolved → default-closed +
  loud**); OTEL spans fire.

**Two load-bearing wiring tests:**
1. **Companion full-loop** (companion package) — `fake` brain ↔ a scripted WS
   server fixture: connect → seat → chargen → play turns → `DICE_REQUEST` →
   clean exit. Analog of understudy `tests/wiring/test_full_loop.py`.
2. **Bond/perception wiring** (server repo) — real server, human + **pet**
   seats: server emits owner-private `NARRATION_SEGMENT`; assert it reaches the
   pet and is **absent** from a hireling. Proves the stage is in the real
   fan-out; doubles as the security regression guard.

**Contract-drift tripwire:** the thin protocol subset means the full-loop
wiring test against the real server catches protocol moves in CI, not silently
in a game.

**What CI cannot test:** "is the voice good? do I care about Donut?" — a human
playtest (Keith plays beside it; transcript review reuses the understudy report
pattern). CI guards the mechanics: never stall the table, never leak the
firewall, never fabricate. An optional gated end-to-end smoke (real server +
real companion + scripted human) can follow; not v1-blocking.

---

## Open decisions deferred to the plan(s)

- **Bond-beat emitter:** narrator-emitted (lean) vs companion-self-reported.
- **Shared-core packaging:** standalone repo vs path/workspace dependency.
- **Companion-definition home:** in-package examples (v1) vs `sidequest-content`
  first-class type (later).
- **Trust model:** cooperative-local only in v1; owner-consent deferred.

## Grounding references (from codebase scan, 2026-06-25)

- **Protocol:** connect `SESSION_EVENT{connect}` (`sidequest-server/.../protocol/
  messages.py:179`); seat `PLAYER_SEAT` (`:1279`) → `SEAT_CONFIRMED` (`:1287`);
  chargen `CHARACTER_CREATION` (`:415-579`); turn `PLAYER_ACTION` (`:64-81`) +
  `TURN_STATUS` barrier (ADR-036); dice `DICE_REQUEST`/`DICE_THROW`/`DICE_RESULT`
  (`:1356-1447`, ADR-074); Fate `FATE_THROW`/`FATE_DEFEND_REQUEST` (ADR-148);
  confrontation server-driven (`:937-1028`, ADR-116). **Ability use is implicit
  in prose** (IntentRouter), not a discrete message. MVP ≈ 15 message types.
- **Perception:** enforced at tool layer (`narrator_perception_filter.py`) +
  broadcast fan-out (`emitters.py:590-707`, `composed.py:47-88`). `_visibility.
  visible_to` is a JSON player_id list — the extension seam. Identity per
  connection via `player_identity.resolve_player_identity` (ADR-119); bond
  recorded in `SessionRoom`. Change size S–M, tool layer untouched.
- **Personality/persistence:** disposition LIVE (`disposition.py:167-210`,
  `session.py:1762-1797`); `RELATIONSHIPS` projection LIVE (`projection/
  relationships.py:52-152`, ADR-136); `OceanProfile` shape live (`genre/models/
  ocean.py:43-92`) but **evolution loop dormant** (ADR-042 never ported);
  persistence Postgres per-session-slug only (ADR-115) — **no cross-campaign
  key** (the v2 gap). Relationships are global per-NPC, not per-PC.
