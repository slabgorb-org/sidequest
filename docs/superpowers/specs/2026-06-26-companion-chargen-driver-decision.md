# Companion Chargen Finalisation — Contract Decision

**Status:** Proposed (Architect decision, awaiting Keith's ruling on §6)
**Author:** Architect (design mode)
**Amends:** `2026-06-25-companion-seat-design.md` §3 step 4 ("Chargen")
**Trigger:** GM playtest 2026-06-26 — companion seat, `caverns_and_claudes/beneath_sunden`, first real end-to-end run after story 159-7.

---

## 1. Problem

The companion seat (epic 159) cannot **finalise** a character against the live
engine. Story 159-7 fixed the per-scene *choice mapping* (prose → index/label),
and that fix is verified working. But the lifecycle still dead-ends: the
companion connects, bonds, answers the two opening picks, then never commits a
PC. The server logs `char_count=0 seat_count=0` on disconnect, and the companion
receives an `ERROR` frame (`Invalid …`) mid-chargen.

**Root cause (single line).** The companion only ever speaks **one** chargen
phase. `companion/protocol.py:41` hardcodes:

```python
def chargen_choice_frame(choice: str) -> dict:
    return {"type": "CHARACTER_CREATION", "payload": {"phase": "scene", "choice": choice}}
```

and `companion/run.py:42-85` only reacts to received frames whose `phase == "scene"`.

**The real contract is a multi-phase FSM.** The server pushes an `input_type` on
every chargen step and dispatches inbound frames on `payload.phase`
(`sidequest-server/.../handlers/character_creation.py:96-129`). Proven by the
human seat in the same session:

```
scene → scene → story_confirm → continue → continue → portrait_confirm → confirmation → complete
```

The companion sends `phase:"scene"` for *all* of these. Once the builder is past
the scene stage, a `scene` frame routes to `_chargen_scene` at a step that is not
a scene → validation error → `ERROR` frame. No commit, ever.

**Why CI missed it.** The companion full-loop wiring test
(`tests/companion/test_full_loop.py`) runs against a *scripted WS fixture* that
accepts whatever the companion sends. It models the `scene` phase only — never
`story_confirm`/`continue`/`portrait_confirm`/`confirmation` — so it cannot
enforce the real FSM. The same blind spot hid 159-7. The spec promised a
"contract-drift tripwire" (design spec §6); the fixture is too thin to be one.

---

## 2. The real chargen contract (ground truth)

The server emits a scene per step carrying an `input_type`; the client dispatches
on it and replies with the matching **phase**. Observed `input_type` vocabulary
(`sidequest-server/sidequest/game/builder.py`, `chargen_mixin.py`) and the
browser's reply (`sidequest-ui/.../CharacterCreation/CharacterCreation.tsx`,
`character_creation.py:96-129`):

| Server `input_type` | Client replies `phase` | Payload the client sends |
|---|---|---|
| `choice` | `scene` | `{choice: "<1-based index>"}` |
| `stock` | `scene` | `{choice: "<1-based index>"}` |
| `text` | `scene` | `{choice: "<freeform prose>"}` |
| `name` | `scene` | `{choice: "<name>"}` |
| `continue` | `continue` | `{}` (display-only ack) |
| `story` | `story_confirm` | `{pronouns, background, description}` (+ `story_autogen` to roll) |
| `pick_portrait` | `portrait_confirm` | `{selected_portrait_ref: <slug>\|null}` (null = skip) |
| `stat_arrange` | `arrange_assign`×N → `arrange_confirm` | `{stat, value}` per assign |
| `roll_the_bones` | `bones_confirm` (opt. `bones_reroll`) | `{}` / `{stat}` |
| *(Fate genres)* | `fate_aspects_confirm`, `fate_pyramid_confirm`, `fate_stunts_confirm` | structured Fate fields |
| *(final summary)* | `confirmation` | `{choice: "1"}` (commit) |

Note `beneath_sunden` (WWN, Mage) did **not** require `stat_arrange`/`roll_the_bones`
in the observed run — stats were auto-assigned — but a genre-general driver must
handle them, because the companion is meant to play any genre/world.

**The server already is the single source of chargen truth.** It validates every
phase, re-prompts on illegal input, and owns ruleset-specific steps (WWN bones,
Fate pyramid). The browser is a thin driver that reads `input_type` and presses
the right button. That is the reference implementation.

---

## 3. Options considered

### Option A — Companion-side phase driver that mirrors the browser  ✅ recommended

Teach the companion to dispatch on the server's `input_type` (exactly as the
browser does) and emit the matching phase frame. The brain is consulted only for
the *creative* phases; the *mechanical* phases are deterministic.

- **Reuse:** server chargen FSM untouched (as the spec already committed:
  "Reused, untouched … chargen FSM"). Mirrors an existing, debugged client
  (sidequest-ui). New code is confined to the companion package.
- **Single source of truth preserved:** the companion *drives* server logic
  (sends `arrange_confirm`, server validates); it never *re-implements* chargen.
- **Genre-general for free:** WWN bones, Fate pyramid, etc. are driven, not
  duplicated. New ruleset steps the server adds need only a new dispatch arm.
- **Matches spec intent:** §3 step 4 already said the companion "answers each
  scene"; this completes that to "answers each *step*," which is what the FSM
  actually requires.

### Option B — Server-side "headless chargen" affordance  ❌

Add a server path: a headless client sends seed choices and the server walks the
rest with defaults / auto-commit.

- **Splits chargen into two code paths** (interactive vs headless) that will
  drift — the exact failure mode that just bit us, promoted to the engine.
- **Re-implements ruleset chargen twice:** a headless path that produces a
  *legal* WWN/Fate sheet must replicate bones/arrange/pyramid logic or bypass it
  (producing a different character than the interactive path). Either way it
  fights the engine.
- **Violates SOUL "Bind the Ruleset, Don't Balance It" in spirit** and the
  spec's "smallest honest server change" — it is the *largest* server change on
  the list.
- **Larger blast radius** on the load-bearing engine to fix a client that simply
  doesn't press all the buttons.

### Option C — Reuse understudy's browser actuation (Playwright)  ❌

The understudy already drives chargen through the real UI, handling every phase
by clicking real buttons — the most complete reuse on paper.

- **Rejected by the spec's decided shape:** "no browser — driving a headless
  Chromium per companion is pure cost," and a shipping artifact must not depend
  on the test harness's browser layer. Noted only for completeness.

---

## 4. Decision

**Option A.** The companion owns a client-side chargen **phase driver** that
dispatches on the server-pushed `input_type` and emits the matching phase frame,
mirroring `sidequest-ui`. The server chargen FSM and its contract are the single
source of truth and stay **untouched**.

Principle to carry forward: **the companion presses the buttons a human would; it
does not own chargen logic.** Any future chargen step the engine adds is a new
dispatch arm in the driver + a new arm in the wiring fixture — never a second
chargen implementation.

---

## 5. Design of the driver (implementation guidance for Dev)

**Replace** the single `chargen_choice_frame(choice)` + scene-only branch with an
`input_type`-dispatched handler in `companion/run.py` (frames in
`companion/protocol.py`). Two tiers:

**Brain-driven phases (persona matters — keep the voice load-bearing):**
- `choice` / `stock` → existing `_chargen_choice` mapping (159-7) — keep as-is.
- `text` / `name` → freeform prose / chosen name from the brain (existing path).
- `story` → derive `{pronouns, background, description}` from the companion
  definition's persona/voice (Donut's species, manner) — one brain call, or a
  deterministic projection from the def plus `story_autogen` fallback. The cat
  should describe *herself*; this is a "do I care about Donut?" surface.

**Deterministic phases (no brain — press the sensible button):**
- `continue` → `{phase: "continue"}`.
- `pick_portrait` → `{phase: "portrait_confirm", selected_portrait_ref: null}`
  (skip; the daemon may be down and portraits are not load-bearing for a bot).
- `stat_arrange` → assign the server-offered pool to the class's qualifying
  layout, then `arrange_confirm`; the server validates and re-prompts if illegal.
- `roll_the_bones` → `bones_confirm` (accept the array; no reroll loop in v1).
- `fate_*` → confirm with the pack-suggested defaults the server already sent
  (`suggestion`/`fate_current_allocation`), then the server validates.
- final summary → `{phase: "confirmation", choice: "1"}` to commit.

**Fail loud on unknown `input_type`** (SOUL/No-Silent-Fallbacks + spec §5.5):
log + safe stop, never a guessed frame. This *is* the contract-drift tripwire.

**Wiring-test fix (mandatory, same story):** upgrade the full-loop fixture to
model the real FSM — emit `story`/`continue`/`pick_portrait`/`confirmation` (and
at least one ruleset step: `stat_arrange` or `roll_the_bones`) and assert the
companion drives through to a committed character (`complete`). Until the fixture
enforces the multi-phase contract, this regresses silently again.

**Blast radius:** `sidequest-understudy` only — `companion/run.py`,
`companion/protocol.py`, `tests/companion/test_full_loop.py`. Zero server, zero
UI, zero content. (`sidequest-understudy` branches from / PRs to **`develop`**.)

---

## 6. Orthogonal decision flagged for Keith (mechanics — your lane)

The driver makes the companion complete chargen as a **full PC**, per the spec
("Full mechanical PC from day one"). The playtest surfaced a Genre-Truth wrinkle
worth your ruling, *separately* from this fix:

> Donut the **cat** was asked to pick a WWN **calling** (Warrior/Expert/Mage) and
> a human background ("worked a crowd," "left the temple"). A familiar going
> through the human PC chargen reads slightly off.

Two paths, both downstream of this decision (not blocking it):
- **(i) Keep full-PC chargen for pets** (spec as written). The driver above is
  complete; the oddity is cosmetic and arguably charming ("Expert. Obviously.").
- **(ii) Pets get a simpler companion stat-block** (a familiar template, not the
  PC FSM). That is a *new* mechanics/content decision and a larger change — out
  of scope for unblocking the lifecycle, but it would change what the driver
  needs to drive.

Recommendation: ship **(i)** to unblock v1 and get a playable Donut; treat **(ii)**
as a separate mechanics story if the cat-as-PC framing bothers you in play. This
keeps the fix small and the mechanics question yours to decide unhurried.

---

## 7. Open sub-decisions for the plan

- **`story` phase authoring:** one brain call for in-persona self-description vs a
  deterministic projection from the def + `story_autogen` fallback. *Lean:*
  deterministic-from-def with autogen fallback (cheaper, resume-safe; the voice
  already lands in the scene choices).
- **`stat_arrange` assignment policy:** simplest legal qualifying layout for the
  chosen class vs a persona-weighted spread. *Lean:* simplest legal — the server
  is the arbiter; don't re-balance (SOUL *Bind the Ruleset*).
- **Carryover items** (re-confirmed open this playtest, fold into the same
  effort): `manifest.DEFAULT_MODEL` is `anthropic/*` (breaks on the dev box →
  `claude_p/sonnet`/`haiku`); `companion play` lacks `--game-slug`/`--as`
  overrides.

---

## 8. Verification (definition of done)

1. `companion play donut_sunden.yaml` against a live `beneath_sunden` MP session
   reaches `chargen.complete` with `char_count=1 seat_count=1` (server log).
2. Donut appears seated "at the table" under her authored name (re-checks the
   open UUID-vs-name finding once she actually seats).
3. With the Inspector open *before* launch: `companion.bond_resolved(resolved=true)`
   fires at connect, and an owner-private `NARRATION_SEGMENT` reaches the pet
   (`companion.routed_as_pet`) once play begins — the bond/perception goals that
   have been blocked behind chargen since day one.
4. Upgraded full-loop fixture drives the full multi-phase FSM to `complete` in CI.
