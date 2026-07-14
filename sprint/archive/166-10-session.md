---
story_id: "166-10"
jira_key: ""
epic: "166"
workflow: "tdd"
---
# Story 166-10: Green Room §6 coal→diamond: promote the seated Other's placeholder name when prose names them — panel shows 'the loudest one' while narration says the proper name (player-visible split)

## Story Details
- **ID:** 166-10
- **Jira Key:** (none — Jira not enabled for this story)
- **Epic:** 166
- **Workflow:** tdd
- **Points:** 3
- **Priority:** p2
- **Repository:** sidequest-server
- **Type:** feature
- **Stack Parent:** none

## Technical Approach

**Context:** ADR-156 §6 defines the alias ledger and the narrator-mint feeder's attach-before-mint flow. When the narrator prose names a seated Other in a scene, that name should be recorded as an alias for the identity's canonical form, and the panel display should reflect the prose name, not the generic placeholder.

**Problem Statement:**
The seated Other (coal — generic bestiary entry like "the loudest one") is seeded into a confrontation. The narrator prose then names it ("Molgrath the Eyeless"). The panel continues showing the placeholder generic name, while the narration says the proper name. This is a player-visible inconsistency — one name in UI, different name in prose.

**Design:** 
1. When the narrator-mint feeder encounters a prose name in narration that matches the seated confrontation Other:
   - Record the prose name as an alias on that identity (via `Npc.aliases`)
   - Do NOT fork identity or create a new entry in snapshot.npcs
   - Emit `green_room.alias_attached` OTEL span with the promotion signal

2. Panel rendering for confrontation display:
   - If the seated Other has aliases, prefer the first prose-derived alias (non-generic)
   - Fall back to the creature's display_name or `invented_from` if no suitable alias exists
   - This makes "Molgrath the Eyeless" appear in the ConfrontationOverlay instead of "Thief" or "the loudest one"

3. The promotion is a player-facing rename — the mechanical identity (`creature_id`, HP, stats) remains unchanged, but the player sees the narrator's proper name.

**Implementation Notes:**
- This builds on story 162-2 (identity-by-id + alias ledger) — the infrastructure already exists
- Focus on the attach path in the narrator-mint feeder (sidequest/server/dispatch/narration_apply.py `_apply_npc_mentions`)
- Wire the alias selection logic into the confrontation display layer (ConfrontationOverlay panel rendering)
- Ensure OTEL spans capture alias attachment with provenance (from_tier, prose_name, promotion_signal)

## Acceptance Criteria
- [ ] When narrator prose names the seated confrontation Other, the alias is recorded on that identity in snapshot.npcs
- [ ] The ConfrontationOverlay panel displays the prose-provided alias instead of the generic placeholder name
- [ ] OTEL spans emit `green_room.alias_attached` with the alias and promotion signal when prose names a coal creature
- [ ] No new NPCs are created in snapshot.npcs; identity remains stable (identity_key unchanged)
- [ ] Tests cover: prose naming a seated Other → alias recorded + panel shows proper name (not placeholder)
- [ ] Tests cover: plural aliases on one identity; panel selects the prose-derived one
- [ ] OTEL watcher can verify the alias attachment occurred

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-13T21:52:12Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-13T13:43:53Z | 2026-07-13T13:47:43Z | 3m 50s |
| red | 2026-07-13T13:47:43Z | 2026-07-13T14:19:29Z | 31m 46s |
| green | 2026-07-13T14:19:29Z | 2026-07-13T15:42:37Z | 1h 23m |
| review | 2026-07-13T15:42:37Z | 2026-07-13T15:57:21Z | 14m 44s |
| red | 2026-07-13T15:57:21Z | 2026-07-13T16:07:22Z | 10m 1s |
| green | 2026-07-13T16:07:22Z | 2026-07-13T16:16:03Z | 8m 41s |
| review | 2026-07-13T16:16:03Z | 2026-07-13T16:32:40Z | 16m 37s |
| red | 2026-07-13T16:32:40Z | 2026-07-13T21:20:12Z | 4h 47m |
| green | 2026-07-13T21:20:12Z | 2026-07-13T21:37:47Z | 17m 35s |
| review | 2026-07-13T21:37:47Z | 2026-07-13T21:52:12Z | 14m 25s |
| finish | 2026-07-13T21:52:12Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → RED phase, owner `tea`. 3 pts, p2, single repo (`sidequest-server`).

**What this story is.** A player-visible name split. The confrontation panel shows the coal
placeholder ("the loudest one") while the narration prose calls the same seated Other by a
proper name. One entity, two names, both on screen. This is the *Diamonds and Coal* promotion
path (ADR-014) failing to close the loop: the prose promoted the coal, the panel didn't hear
about it. Filed out of the Green Room (ADR-156) final reviews, §6.

**Jira:** explicitly skipped — `jira: null` in `sprint/epic-166.yaml`. No key to claim.

**Two things TEA should resolve before writing the RED tests:**

1. **Branch base is `feat/green-room`, not `develop`.** 166-5 (the Green Room big-bang) is
   still `in_review` with server PR #1140 open, and this follow-up depends on the §6 alias
   ledger landing there. That makes 166-10 effectively stacked on an unmerged PR. Confirm the
   attach-before-mint / alias-ledger code TEA is testing against is present on that base before
   writing a single test — if it isn't, the RED tests will fail for the wrong reason.

2. **Scope may cross the server/UI line.** The story is filed `repos: server`, but the setup
   context names `ConfrontationOverlay` panel rendering, which lives in `sidequest-ui`. The
   likely truth is that this is a *server-side projection* fix (ADR-136 reactive projection —
   the server sends the display name, the UI just renders it), in which case `repos: server` is
   correct and no UI change is needed. Verify that before assuming. If the panel picks the name
   client-side, this story needs `sidequest-ui` added to `repos` and re-pointing — flag it as a
   blocking Delivery Finding rather than quietly editing UI from a server-scoped story.

**OTEL:** per project doctrine, the alias promotion must emit a watcher span
(`green_room.alias_attached`) — the GM panel is the lie detector for whether the promotion
actually fired or the narrator just improvised a name. Non-negotiable in the ACs.

## TEA Assessment

**Tests Required:** Yes
**Test File:** `sidequest-server/tests/server/test_166_10_coal_to_diamond_panel_name.py` (new, 8 tests)
**Tests Written:** 8 tests — **3 RED** (the story), **5 green guards** (invariants + negatives)
**Status:** RED confirmed. Commit `abbe6f9b`. Lint + format clean.

### Both of Drummer's setup flags: RESOLVED

**Flag 1 — branch base.** The ADR-156 §6 code IS present on `feat/green-room`. `attach_alias`
(`sidequest/game/green_room.py:78-99`) and `_attach_before_mint`
(`sidequest/server/narration_apply.py:2636-2694`) are both live, and the sibling suite
`test_green_room_attach_before_mint.py` passes 10/10 on this base. The RED tests fail for the
right reason, not for a missing dependency.

**Flag 2 — server/UI scope. `repos: server` is CORRECT; no UI change needed.** The panel name is
100% server-chosen. `build_confrontation_payload`'s `_actor_with_portrait`
(`dispatch/confrontation.py:344-350`) serializes `EncounterActor.model_dump()` verbatim into
`ConfrontationPayload.actors[].name`. The UI picks no name — `ConfrontationOverlay.tsx:1219` just
renders `humanizeActorName(opponent.name)` (underscore→space, capitalize) and explicitly refuses to
rewrite the id. Fix the server projection and the panel follows. Story stays server-scoped.

### What's actually broken (sharper than the story text)

The *attach* half of §6 already works — the prose name lands in `Npc.aliases`. Nothing downstream
**reads** it. `attach_alias` appends to the ledger and touches nothing else, while
`EncounterActor.name` was baked with the coal placeholder once, at seat time
(`encounter_lifecycle.py:565-566`). So the table reads `NARRATION: "Ihnsch of the Rusted Works…"`
against `PANEL: [ the Scrapborn ]`. This is a **projection gap, not an attach gap.**

### The trap Dev must not fall into

`EncounterActor.name` is a **load-bearing entity id, not a label.** `find_actor`
(`encounter.py:446`) is an exact string match and is the universal targeting seam; the UI states
outright that `actor.name` backs *tag targets and `last_beat_impacts` keys*
(`ConfrontationOverlay.tsx:649-656`). Two plausible fixes each break something:

- **Rename the wire payload only** → the UI targets a name `find_actor` cannot resolve → dead click.
- **Rename `EncounterActor.name` in place** → earlier-turn tag targets / `last_beat_impacts` keys /
  pending commits stamped with the placeholder now dangle → the impact badge silently drops.

The honest contract is ADR-156 §6's own words — *"one enemy, one identity, **two names**"* — so
**both** names must resolve to the same seated actor. Tests 3 and 4 pin exactly that, in both
directions. A naive in-place rename passes 3 and fails 4.

Third landmine: **do not rewrite `Npc.core.name`.** For a GENERIC origin `identity_key` keys on the
normalized *display name* (`origin.py:101-118` — a `generics:` row is a stat donor, not an
identity), so "promoting" the canonical name silently **forks the identity** — the exact thing §6
exists to prevent. Test 2 pins `identity_key` stable. The promotion is display-layer only.

### Test Coverage

| # | Test | State | What it has teeth on |
|---|------|-------|----------------------|
| 1 | `panel_shows_the_prose_name_after_the_coal_other_is_named` | **RED** | The story. Panel shows `the Scrapborn`, must show `Ihnsch of the Rusted Works`. Doubles as the wiring test (drives real `_apply_npc_mentions` + real `build_confrontation_payload`). |
| 2 | `promotion_does_not_churn_the_identity` | green guard | `identity_key` stable, `core.name` stays coal, same `Npc` object, creature_id + HP intact, no new roster/pool member. |
| 3 | `seated_actor_is_findable_by_the_promoted_name` | **RED** | `find_actor("Ihnsch…")` → currently `None`. The UI hands this string back as a tag target. |
| 4 | `seated_actor_is_still_findable_by_the_original_placeholder` | **RED** | Both names must land on the same actor. **This is the one a naive rename fails.** |
| 5 | `authored_other_is_not_renamed_by_a_hostile_mention` | green guard | No hijack of a named villain — promotion is for coal. |
| 6 | `two_live_opponents_are_ambiguous_and_neither_is_renamed` | green guard | Never guess (No Silent Fallbacks). |
| 7 | `bystander_mention_does_not_rename_the_seated_other` | green guard | Non-hostile mention isn't the enemy's true name. |
| 8 | `promotion_emits_the_alias_attached_span` | green guard | `green_room.alias_attached` — the GM panel is the lie detector. |

### Rule Coverage

Rules from `.pennyfarthing/gates/lang-review/python.md` + the CLAUDE.md/SOUL.md doctrine that are
*applicable to this story's surface* (a display-layer projection fix — it adds no new constructors,
enums, deserializers, async paths, file handles or external inputs, so python.md rules 2/5/7/8/9/11/12
have no reachable surface here and are honestly N/A rather than silently skipped).

| Rule | Test(s) | Status |
|------|---------|--------|
| python #6 — Test quality (no vacuous assertions) | whole suite; 1 tautological test found and rewritten (see Self-check) | passing |
| python #3 — Type annotation gaps at boundaries | suite is fully annotated (`-> None`, `dict[str, Any]` helpers); `ruff check` clean | passing |
| python #10 — Import hygiene | no star-imports, no local re-imports; `ruff check` clean | passing |
| python #1 — Silent exception swallowing | `_actor`/`_panel` helpers raise `AssertionError` on miss rather than returning a default | passing |
| CLAUDE.md — No Silent Fallbacks | `two_live_opponents_are_ambiguous_and_neither_is_renamed` (never guess between two Others) | passing (guard) |
| CLAUDE.md — No Source-Text Wiring Tests | every test drives real production functions; zero `read_text()`/grep/regex-on-source assertions | passing |
| CLAUDE.md — Every Test Suite Needs a Wiring Test | `panel_shows_the_prose_name_after_the_coal_other_is_named` spans both seams (real `_apply_npc_mentions` → real `build_confrontation_payload`) | **failing (RED)** |
| CLAUDE.md — OTEL Observability Principle | `promotion_emits_the_alias_attached_span` (`green_room.alias_attached`) | passing (guard) |
| SOUL.md — Diamonds and Coal (ADR-014/-128 promotion) | tests 1, 5, 7 — coal gets promoted when the world names it; a diamond (authored Other) and a bystander do not | 1 failing (RED), 2 passing |

**Rules checked:** 9 of 9 applicable rules have test coverage (4 of python.md's 13 are reachable on
this surface; the other 9 are N/A for the reason given above).

**Self-check:** 1 vacuous test found and fixed. Test 3 originally derived its lookup key from the
panel payload (`find_actor(shown)`) and therefore **passed on RED** — the key moved with the bug, so
it could never fail. Rewritten to assert against the literal prose name; it now fails correctly. No
`assert True`, no bare `is_none()`, no unbound `let _`-equivalents remain.

**Handoff:** To Naomi (Dev) for GREEN.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Question** (non-blocking): SM's server/UI scope flag is RESOLVED — the confrontation panel name
  is server-chosen end-to-end and the UI rewrites nothing, so `repos: server` is correct and no
  `sidequest-ui` change is required. Affects `sprint/epic-166.yaml` (no re-scope needed — recording
  so the question isn't re-litigated in review). *Found by TEA during test design.*
- **Gap** (non-blocking): `sprint/context/context-story-166-10.md` is a generated stub — "No
  description in the sprint YAML", "No acceptance criteria recorded... TEA to define". The real spec
  is ADR-156 §6 plus the code. ACs were derived from those and are now pinned in the test suite.
  Affects `sprint/context/context-story-166-10.md` (has no usable content for Dev/Reviewer; read the
  test docstrings and this assessment instead). *Found by TEA during test design.*
- **Conflict** (blocking for Dev's design choice): `EncounterActor.name` is simultaneously the
  player-visible label AND a load-bearing entity id (`find_actor` exact-match; UI tag targets and
  `last_beat_impacts` keys). ADR-156 §6 asserts the panel "may show 'Molgrath the Eyeless' while the
  engine keys on `creature_id=Thief`" but does not say how the two names coexist at the lookup seam.
  Affects `sidequest/game/encounter.py:446` (`find_actor` must become alias-aware, or the promotion
  must carry the old name forward — Dev's call, but one of the two is required). *Found by TEA during
  test design.*
- **Improvement** (non-blocking): `identity_key`'s GENERIC exception (`origin.py:101-118`) is a real
  footgun for any future "promote the name" work — it means the canonical name IS the identity for
  coal. Worth an explicit warning in ADR-156 §6 alongside the alias-ledger text. Affects
  `docs/adr/156-green-room-npc-origin-precedence.md` (§6 documents the principle but not this
  hazard). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): AC bullet 6 ("Tests cover: plural aliases on one identity; panel selects the
  prose-derived one") is unreachable under the implemented design — the seated-Other attach leg gates
  on an EMPTY alias ledger, so an Other promotes exactly once and the panel selects nothing. The AC
  presumes a display-layer alias-selection design that would leave the promoted name unresolvable by
  `find_actor`. Affects `sprint/epic-166.yaml` (drop the AC, or file the second-promotion / disguise-
  reveal story it actually describes). *Found by Dev during implementation.*
- **Question** (non-blocking): TEA's brief warns that `last_beat_impacts` keys reference `actor.name`
  (citing `ConfrontationOverlay.tsx:649-656`). The server model disagrees — `last_beat_impacts` is
  keyed by actor SIDE ("player"/"opponent") and rebuilt each beat (`encounter.py`, Story 73-4). Either
  the UI comment is stale or the UI derives something the server does not. Harmless for this story
  (the rename sweep covers the fields that ARE name-keyed), but the comment misleads. Affects
  `sidequest-ui/src/components/ConfrontationOverlay.tsx` (verify + correct the comment). *Found by Dev
  during implementation.*
- **Improvement** (non-blocking): the confrontation portrait resolver keys on `actor.name`
  (`_actor_with_portrait` → `_resolve_npc_portrait_url`, which slugifies the name against the world's
  portrait manifest). After a promotion that lookup uses the PROSE name. No regression today — the
  promotion only fires for GENERIC/NARRATOR_INVENTED coal, whose placeholder is not in any portrait
  manifest either, so both names miss and the existing not-found span fires. But a world that ever
  authors a portrait keyed to a `generics:` placeholder slug would see the portrait silently drop at
  promotion. Affects `sidequest/server/dispatch/confrontation.py` (resolve the portrait through the
  identity, not the display name, if that day comes). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `EncounterActor.aliases` now rides the CONFRONTATION wire payload
  (`_actor_with_portrait` dumps the model verbatim, and `ConfrontationPayload.actors` is
  `list[dict[str, Any]]`, so it passes through untyped). The UI ignores it. It is free signal for an
  "also known as" tooltip on a promoted Other. Affects `sidequest-ui` (opt-in UI story, not required
  by this one). *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): `EncounterActor.name` is load-bearing for mechanical resolution — `GameSnapshot.find_creature_core` (`session.py:1915-1921`) exact-matches it against `Npc.core.name`, and `encounter_lifecycle.py:438-446` enforces `actor.name == npc.core.name` as a review-mandated invariant ("a seat left under the prose alias is an unreachable opponent"). ADR-156 §6 says the panel "may show 'Molgrath the Eyeless' while the engine keys on `creature_id=Thief`" but never says the two names live in the SAME field. Affects `docs/adr/156-*.md` (§6 should state explicitly that the display name is a separate projection, not a rename of the seat) and `sprint/epic-166.yaml` (166-10 needs `repos: server, ui`). *Found by Reviewer during code review.*
- **Gap** (blocking): the story was scoped `repos: server` on TEA's finding that "the panel name is 100% server-chosen; no UI change needed". That is true of *rendering* but not of *fixing* — the only safe fix carries a display name in a new field, which the UI must render. SM flagged this exact question at setup and it was closed prematurely. Affects `sprint/epic-166.yaml` (re-scope to include `sidequest-ui`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): a second hostile prose naming of an already-promoted Other mints a phantom `NpcPoolMember` instead of no-oping — the phantom-twin failure ADR-156 §6 exists to prevent, resurfacing for the second naming. Pre-dates 166-10 (the gate is `not other.aliases` at `narration_apply.py:2687`). Affects `sidequest/server/narration_apply.py` (needs its own story + a RED test). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_attach_before_mint`'s seated-Other leg has **no encounter-type gate**, so it fires on a `table_showdown` (poker/auction) encounter just as readily as on combat, where `TableState.seats[].party_name` mirrors `EncounterActor.name` and would be left dangling. Affects `sidequest/server/narration_apply.py` (gate the leg, or sweep the table seats). *Found by Reviewer during code review.*
- **Question** (non-blocking): Dev's finding that `last_beat_impacts` is keyed by SIDE, not by actor name, contradicts the UI comment at `ConfrontationOverlay.tsx:649-656`. Confirmed: the server model is side-keyed. The UI comment is stale or describes something the server does not do. Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx`. *Found by Reviewer during code review.*

### TEA (test design — rework round 2)
- **Gap** (blocking, now resolved): the story was scoped `repos: server` on my round-1 finding that "no UI change is needed". That was true of *rendering the existing field* and false of *fixing the bug*. Re-scoped to `repos: server, ui` in `sprint/epic-166.yaml`; a `sidequest-ui` RED suite is now in place. *Found by TEA during rework.*
- **Gap** (non-blocking): `sprint/epic-166.yaml` had no `--repos` affordance on `pf sprint story update`, so the re-scope required a direct YAML edit despite the project rule "always use `pf sprint` CLI — never manually edit sprint YAML". Affects `pennyfarthing` (`pf sprint story update` needs a `--repos` option). *Found by TEA during rework.*
- **Improvement** (non-blocking): the ACs were rewritten (`--clear-ac` + `--add-ac`). The old AC 6 ("plural aliases on one identity; panel selects the prose-derived one") described a display-layer selection design that never existed and is now impossible; the new AC set pins mechanical reachability and the HP-bar survival instead. *Found by TEA during rework.*
- **Question** (non-blocking): Reviewer confirmed a second hostile naming of an already-promoted Other mints a phantom `NpcPoolMember` (`narration_apply.py:2687`, gate is `not other.aliases`). This suite does NOT pin it — it is pre-existing and out of 166-10's scope, but it is a real table event (a narrator re-flavouring an ongoing villain). Affects `sprint/epic-166.yaml` (needs its own story). *Found by TEA during rework.*

### Dev (implementation — rework round 2)
- **Improvement** (non-blocking): the `id` vs `label` distinction that broke this story is not enforced by anything — `EncounterActor.name` and `display_name` are both bare `str`. A `NewType`/branded id would make "never render the id, never resolve the label" a type error instead of a code-review finding. Worth considering the next time a seam like this is touched. Affects `sidequest/game/encounter.py`. *Found by Dev during rework.*
- **Question** (non-blocking): `find_creature_core` is now the only actor→core resolver that is alias-aware. Several sites still do a direct `next((n for n in snapshot.npcs if n.core.name == actor.name), None)` (`map_emit.py:99`, `fate_contest.py:157`, `narration_apply.py:9037`, `dogfight.py:198`). They are **correct today** — `actor.name` is canonical again, so they resolve — but they are the same latent trap: any future code that puts a non-canonical string in an actor name silently degrades them (map token loses HP/AC; presence stamps skip). Routing them through `resolve_roster_npc` would close the class. Out of scope here. Affects the four files above. *Found by Dev during rework.*
- **Improvement** (non-blocking): `pf sprint story update` has no `--repos` option, so TEA's re-scope to `server, ui` required hand-editing `sprint/epic-166.yaml` against the project's own "never manually edit sprint YAML" rule. Affects `pennyfarthing`. *Found by Dev during rework (corroborating TEA).*

### Reviewer (code review — round 2)
- **Gap** (blocking): the Green Room promotion is **not ruleset-gated** (`narration_apply.py:2687`), so it fires on Fate encounters, but `fate_projection._project_conflict_participant` (`fate_projection.py:156`) drops `display_name` and `FateConflictSurface.tsx:861` renders the seat id — including in the attack-target dropdown. The story's own bug is live on the 4 Fate packs (pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy). Affects `sidequest/game/ruleset/fate_projection.py`, `sidequest-ui/src/components/FateConflictSurface.tsx`, `sidequest-ui/src/types/payloads.ts` (forward + render `display_name`, keep `value={o.name}`). *Found by Reviewer during code review.*
- **Conflict** (blocking): `find_creature_core`'s widening to `resolve_roster_npc` changed exact-match semantics to normalized-first-wins, so two roster NPCs colliding under case/diacritic fold now resolve to the wrong creature — `apply_damage` can damage the wrong NPC, silently, at ~40 call sites. AUTHORED NPCs are not deduped by name (they key on `authored_id`), so this is reachable from content. Affects `sidequest/game/session.py:1928` (exact match first, then fall back). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the id-vs-label distinction that has now cost two review rounds is enforced by nothing — `name` and `display_name` are both bare `str`, and `FateConflictParticipant.name` is a third bare `str` carrying the same id. A branded/NewType id would make "never render the id, never resolve the label, never send the label" a type error rather than a review finding. Naomi filed the same observation independently. Affects `sidequest/game/encounter.py`, `sidequest/protocol/`. *Found by Reviewer during code review.*
- **Question** (non-blocking): `resolve_roster_npc` re-emits `identity.resolved` on **every** narrator tool call that targets a promoted Other by its prose name — which ADR-156 §6 explicitly expects to be most of them, for the rest of the encounter. Mechanical callers pass the canonical seat id and emit nothing, so this is not a hot-path problem, but the GM-panel volume is unbounded and undocumented. Affects `sidequest/game/origin.py` (decide: accept the volume, or dedup per turn). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): a local dev save written while the **rejected** round-1 code was running carries `aliases` on `EncounterActor` and will now fail `extra="forbid"` with `SaveSchemaIncompatibleError`. Loud, local-only, never merged — recording so it is not diagnosed twice. Affects `sidequest/game/migrations.py` (no action required). *Found by Reviewer during code review.*

### TEA (test design — rework round 3)
- **Gap** (blocking, now pinned): a **third** projection drops `display_name` and no review round found it. `map_emit._place_tokens_on_anchors` (`map_emit.py:107`) builds the tactical battle-map token as `TokenPayload(token_id=f"creature:{actor.name}", label=actor.name, ...)`. `TokenPayload` **already has the id/label split this entire story is about** (`token_id` vs `label`) and the seat id is being fed to both. The promoted Other's token on the battle map reads "the Scrapborn" under narration saying "Ihnsch of the Rusted Works" — this story's bug, third surface. Affects `sidequest/server/websocket_handlers/map_emit.py` (`label=actor.display_name or actor.name`; `token_id` unchanged). No UI change needed — `TacticalGridRenderer` renders `label` and derives its glyph from `label[0]`. *Found by TEA during test design.*
- **Gap** (blocking, now pinned): the Fate surface has **seven** broken display sites, not the one the Reviewer found. Beyond the attack-target dropdown (`FateConflictSurface.tsx:862`): the participants roster (`:449`), the opponent-track heading (`:528`), the win-meter's **sr-only `aria-label`** (`:539` — the only name a screen-reader user or the understudy playtest bot gets for that meter), the Defend! banner (`:644`), and both halves of the Last Exchange ledger clause (`:193`, `:215`). The last three are fed by `FateExchangeLine` / `FateDefendRequestPayload`, which carry bare name strings — but the component already has `conflict.participants` (which will carry `display_name`) in scope, so they resolve client-side with **no new protocol fields**. Affects `sidequest-ui/src/components/FateConflictSurface.tsx`. *Found by TEA during test design.*
- **Gap** (non-blocking): `FateConflictSurface` does **no name humanization at all**, unlike `ConfrontationOverlay`. A slug seat id (`unknown_dark_contact`) renders verbatim in the participant list, the target dropdown and the exchange ledger today, on all four Fate packs. Routing every display site through a shared `actorDisplayName()` fixes the stage-name bug and this one in the same edit. `actorDisplayName`/`humanizeActorName` are currently **module-private to `ConfrontationOverlay.tsx`** and must be exported (better: hoisted to `src/lib/`) — the file's own docstring already promises "one helper, used at every display site". Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx`, `FateConflictSurface.tsx`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the explicit-kwarg wire-model construction is the **structural cause** of this story's two rejections and deserves a rule, not just a fix. `build_confrontation_payload` carries `display_name` for free because it projects via `actor.model_dump()`. `_project_conflict_participant` and `_place_tokens_on_anchors` drop it because they construct their wire models with explicit kwargs — which are *allowlists*: a new field on the source model is discarded by construction, with no error, no type failure, and no test failure. Any story adding a field to a projected model must grep for every explicit-kwarg construction of every wire model fed by that source. Worth a lang-review checklist entry. Affects `.pennyfarthing/gates/lang-review/python.md`. *Found by TEA during test design.*
- **Gap** (non-blocking): the NPC identity surfaces **outside** the confrontation still show canonical names for a promoted Other — `RelationshipsPanel.tsx:108`, `ScrapbookGallery.tsx:112/121/131`, `CartographyMap.tsx:135`, and the tactical move-budget chip (`TacticalGridRenderer.tsx:194`) / selected-token header (`CavernActionPanel.tsx:33`). These are fed by **different wire types** (not `EncounterActor`), so they are genuinely a separate story rather than this one's half-wiring — but they are the same ADR-156 identity, and a table will eventually notice. Scoped OUT deliberately, recorded loudly rather than dropped. Affects the five files above (needs its own story). *Found by TEA during test design.*
- **Question** (non-blocking): `reviewer-rule-checker` has now certified "No half-wired features — verified no gap at any hop" **twice**, and been wrong both times, because it walks only the hops the diff shows it. Its "clean" verdict on a *wiring* rule is evidence about the diff, never about the system, and it reads as authoritative in the review record. Either the rule should be removed from its remit or its prompt must require a consumer sweep from the changed **type** rather than the changed **lines**. Affects `.pennyfarthing/agents/reviewer-rule-checker.md`. *Found by TEA during test design.*

### Dev (implementation — rework round 3)
- **Improvement** (non-blocking): the **explicit-kwarg wire projection** is the structural cause of this story's two rejections and deserves a rule, not just three fixes. `build_confrontation_payload` carried `display_name` for free because it projects via `actor.model_dump()`. `_project_conflict_participant` and `_place_tokens_on_anchors` dropped it because they construct their wire models with explicit kwargs — which are **allowlists**: a new source field is discarded by construction, with no error, no `pyright` failure and no test failure. Invisible from the diff, obvious from the type. Amos filed the same observation independently; two of us landing on it separately is the argument for codifying it. Affects `.pennyfarthing/gates/lang-review/python.md` (a checklist entry: "when adding a field to a model that is projected onto a wire payload, grep every explicit-kwarg construction of every wire model fed by that source"). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `FateConflictSurface` did **no name humanization at all** before this story — a slug seat id (`unknown_dark_contact`) rendered verbatim in the participant list, the target dropdown and the exchange ledger on all four Fate packs, while `ConfrontationOverlay` humanized. Routing every site through the shared helper fixed it as a side effect, but the two surfaces having silently different display rules for two months is the real finding, and the cause was a module-private helper. Affects `sidequest-ui/src/lib/actorDisplayName.ts` (now the single seam — keep it that way). *Found by Dev during implementation.*
- **Question** (non-blocking): the four direct `next((n for n in snapshot.npcs if n.core.name == actor.name), None)` roster matches I flagged in round 2 (`map_emit.py:99`, `fate_contest.py:157`, `narration_apply.py:9037`, `dogfight.py:198`) are **still** direct exact compares. They remain correct — `actor.name` is canonical by construction — and Amos's `the_named_others_map_token_keeps_its_hp` now pins the map one so a future rename fails loudly there instead of silently dropping the token's HP bar. The other three are still unpinned. Routing them all through `resolve_roster_npc` would close the class. Affects the four files above (needs its own story). *Found by Dev during implementation.*
- **Gap** (non-blocking): three test failures in the full server suite (`test_102_5_wn_tool_narrator_wiring`, `test_pregen_bestiary_90_1[evropi]`, and the two `test_companion_brain_telemetry_passthrough` cases) are **pre-existing and unrelated** — I verified them against a stashed clean tree (clean: 10 failed / 14984 passed; with my changes: 4 failed / 14990 passed — exactly the 6 RED tests flipping, no regressions). Two of them (`wn_tool_narrator_wiring`, `pregen_bestiary`) **pass when run serially and fail under `-n auto`**, i.e. they are xdist-order-flaky, not broken. Flaky tests in the gate erode the signal that this story has now been rejected twice for missing. Affects `sidequest-server/tests/` (needs a flake-isolation story). *Found by Dev during implementation.*

### Reviewer (code review — round 3)
- **Gap** (non-blocking, needs its own story): **the narrator's own participant list still names the promoted Other by its coal seat id.** `narrator.py:399/482` and `query_encounter.py:121` feed the narrator `a.name` ("the Scrapborn"). Having just written "Ihnsch of the Rusted Works", the narrator's next turn reads a structured state block calling the enemy "the Scrapborn" — and may revert, reopening this story's split with the surfaces swapped (panel: Ihnsch, prose: the Scrapborn). **The naive fix is a trap:** `find_actor` (`encounter.py:469`) is exact-only, so handing the narrator the label would leak it into narrator-supplied tag targets and dangle them silently. The right shape is a dual-name line — `- the Scrapborn (aka "Ihnsch of the Rusted Works", side=opponent)` — so the narrator has the prose name for prose and the canonical id for tools. That is a design decision, not a one-liner. Affects `sidequest/agents/narrator.py`, `sidequest/agents/tools/query_encounter.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking, sharpens an already-filed finding): **the FIRST hostile prose mention wins the promotion — even a generic epithet — and the second name mints a phantom.** Reproduced end-to-end: narrator says "the raider" on turn 5 → the panel locks to "The Raider"; narrator says "Ihnsch of the Rusted Works" on turn 8 → the panel is **still** "The Raider" and `Ihnsch of the Rusted Works` is minted into `npc_pool` as a phantom twin of the seated Other. Two names on screen again — this story's own bug, on a plausible table. Root cause is the pre-existing `not other.aliases` gate (`narration_apply.py:2694`), **unchanged by this round** (the second naming never reaches `promote_actor`), and already filed by Reviewer, TEA and Dev across two rounds. Recording the reproduction so the follow-up story starts from a failing case rather than a hypothesis. Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): **`reviewer-rule-checker` returned an evidence-backed rule-21 verdict for the first time — because its prompt was changed to forbid diff-reasoning.** Twice it certified "verified no gap at any hop" by walking only the hops the diff showed it, and twice it was wrong. This round it was ordered to reason from the changed **type** (enumerate every projection reading `EncounterActor`, every consumer of `FateConflictParticipant`/`TokenPayload.label`, classify each DISPLAY vs ID/KEY/VALUE) and it produced an exhaustive consumer table that matched an independent sweep hop-for-hop. **That prompt change should be made permanent** — a wiring rule cannot be checked from a diff. TEA filed the same observation. Affects `.pennyfarthing/agents/reviewer-rule-checker.md`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): five stale `encounter_lifecycle.py` comments (`440`, `521`, `829`, `889`, `1929`) still justify seat-canonicalization by asserting `find_creature_core` is EXACT-match — falsified by this story's own change. **I flagged four of these in round 2 and they were not addressed**; the Dev assessment's finding table does not mention them. The code remains correct (canonicalization is still required for `find_actor` / the initiative walk / sealed commits / the map-token roster match, which ARE exact-only) — only the stated reasoning is wrong, which is the worst kind of comment. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the JSDoc block that documented `humanizeActorName` was orphaned when the helper moved to `lib/` and now floats directly above `function SpellPicker` (`ConfrontationOverlay.tsx:671-682`), where it reads as SpellPicker's docstring while describing actor-name humanizing. Introduced by this diff. Also `exchangeClause`'s docstring (`FateConflictSurface.tsx:187`) never mentions its new `labelFor` parameter. Affects both files. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the session file's `## Acceptance Criteria` block is **stale** — it still lists the original 7 ACs, including the one TEA correctly deleted in round 2 as unmeetable ("plural aliases on one identity; panel selects the prose-derived one"). The authoritative rewritten 8 live in `sprint/epic-166.yaml` and all 8 are met. A reviewer reading only the session file would score this story against an AC the design deliberately made impossible. Affects `.session/166-10-session.md` / the `pf context` regeneration path. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two pre-existing dead fields surfaced during the consumer sweep and are worth deleting rather than carrying: `build_confrontation_payload`'s `initiative_order[].name` (`confrontation.py:559`) has **zero consumers in the UI**, and `TacticalAdjudication.actor` is gated behind the not-live `dungeon_store` path. Neither is touched by this story. Dead code is worse than no code (CLAUDE.md). Affects `sidequest/server/dispatch/confrontation.py`, `sidequest/protocol/models.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Pinned the promoted name on the existing `actors[].name` key rather than a new `display_name` key**
  - Spec source: story title (166-10) + ADR-156 §6
  - Spec text: "the panel shows 'the loudest one' while narration says the proper name"; §6 — "The
    combat panel may show 'Molgrath the Eyeless' while the engine keys on `creature_id=Thief`"
  - Implementation: tests assert `payload["actors"][i]["name"] == <prose name>`, not a new
    `display_name` field.
  - Rationale: `actors[].name` is the only name the overlay renders today
    (`ConfrontationOverlay.tsx:1219`). A new key would leave the rendered name unchanged and the
    player-visible split still on screen unless `sidequest-ui` also changes — which this
    server-scoped story does not carry. Pinning `name` keeps the fix server-only, as scoped.
  - Severity: minor
  - Forward impact: if the Architect prefers an additive `display_name` field, the UI must render it
    and the story must be re-scoped to include `sidequest-ui`. Test 1 is the single assertion to
    change.
- **Added an invariant the story text does not state: the pre-promotion placeholder must STILL resolve**
  - Spec source: ADR-156 §6
  - Spec text: "one enemy, one identity, two names"
  - Implementation: test 4 asserts `find_actor(<placeholder>)` still returns the seated Other after
    the promotion, in addition to `find_actor(<prose name>)`.
  - Rationale: `EncounterActor.name` backs UI tag targets and `last_beat_impacts` keys stamped in
    earlier turns; a destructive rename orphans them and the impact badge silently drops. §6's "two
    names" is read as a two-way contract, not a one-way rename. This constrains the implementation
    beyond the literal story text.
  - Severity: minor
  - Forward impact: forces the promotion to be alias-aware (or old-name-preserving) rather than a
    one-line `actor.name = alias`. If Dev/Architect judges the old name genuinely dead after
    promotion, this test is the one to challenge — challenge it explicitly, don't delete it quietly.

### Dev (implementation)
- **Promoted the seat at the ATTACH site instead of selecting an alias at the DISPLAY site**
  - Spec source: context-story-166-10 / session "Technical Approach", design step 2
  - Spec text: "Panel rendering for confrontation display: If the seated Other has aliases, prefer the
    first prose-derived alias (non-generic); Fall back to the creature's display_name or
    `invented_from` if no suitable alias exists."
  - Implementation: `build_confrontation_payload` is unchanged. The promotion happens once, at the
    attach site (`_attach_before_mint` → new `StructuredEncounter.promote_actor`), which renames the
    seated `EncounterActor` and parks the placeholder in a new `EncounterActor.aliases` ledger. The
    panel keeps projecting the actor verbatim.
  - Rationale: a read-time "prefer the alias" projection fixes the LABEL and nothing else — the UI
    hands `actor.name` back as a tag target and `find_actor` is an exact string match, so the panel
    would show a name the engine cannot resolve (dead click; TEA's test 3). It is also not reachable
    from where the spec puts it: `build_confrontation_payload(encounter, cdef, genre_slug)` never sees
    the `GameSnapshot`, so it cannot read `Npc.aliases` without threading the snapshot through every
    call site (supplier, dice union, websocket union, yield projection). Writing the promotion once,
    into the encounter, gives one name on the wire and one name in the engine.
  - Severity: minor
  - Forward impact: none for siblings — the ACs are met and the panel shows the prose name. Anyone
    reading the story's "Implementation Notes" will look for display-layer selection logic and not
    find it; the promotion is in `encounter.py` + `narration_apply.py`.
- **AC "plural aliases on one identity; panel selects the prose-derived one" is not exercised — the design makes it unreachable**
  - Spec source: session Acceptance Criteria, bullet 6
  - Spec text: "Tests cover: plural aliases on one identity; panel selects the prose-derived one"
  - Implementation: no such test exists (TEA wrote none) and I added none. The seated-Other attach leg
    gates on an EMPTY alias ledger, so an Other can be promoted exactly ONCE; a second hostile prose
    name falls through to mint its own identity. The seat therefore carries exactly one name and the
    panel selects nothing.
  - Rationale: the AC presumes the display-layer-selection design I did not take (see the deviation
    above). Under a promote-at-attach design there is no selection to test — writing a test for it
    would mean building the plural-alias selection path first, which nothing needs. Flagged as a
    delivery finding rather than silently dropped.
  - Severity: minor
  - Forward impact: if a future story wants a SECOND promotion (a disguise reveal, a true-name
    reveal), it must relax the empty-ledger gate and will then need the selection rule this AC asked
    for. `promote_actor` is the seam it would call.
- **Added `green_room.actor_promoted` and the `_repoint_actor_name` reference sweep — neither is required by any test**
  - Spec source: the RED suite (8 tests) + CLAUDE.md
  - Spec text: tests require only that both names resolve and the panel shows the prose name;
    CLAUDE.md — "Every backend fix that touches a subsystem MUST add OTEL watcher events", "No Silent
    Fallbacks", "no half-wired features".
  - Implementation: `promote_actor` emits a new `green_room.actor_promoted` span, and
    `_repoint_actor_name` repoints every in-encounter reference that holds an actor name by exact
    match and outlives a rename (`initiative[].token_id`, `wn_commits[].actor/.target`,
    `fate_commits[].actor/.target`, `pending_defenses[].attacker/.defender`, `pending_compels[].target`,
    `tags[].created_by/.target`, `taunt.active_actor`).
  - Rationale: the test fixture seats a bare encounter with no initiative, commits or tags, so a
    rename passes all 8 tests while silently orphaning a WN round walk's initiative token in a real
    game. That is precisely the silent failure the project rules forbid, and it is not visible from
    the tests. The span is project OTEL doctrine — `alias_attached` proves the identity learned the
    name; only `actor_promoted` proves it reached the surface the player is looking at.
  - Severity: minor
  - Forward impact: `EncounterActor.aliases` and `promote_actor` are now the seam for any future
    "rename a seated actor" work; `TableState` seats are deliberately NOT swept (separate `seat_id`
    id space).

### Reviewer (audit)

- **TEA — "Pinned the promoted name on the existing `actors[].name` key rather than a new `display_name` key"** → ✗ **FLAGGED by Reviewer.** This is the root cause of the CRITICAL. TEA's rationale was that a new key "would leave the rendered name unchanged... which this server-scoped story does not carry" — i.e. the design was chosen to preserve the story's server-only scope. But `actors[].name` is not a label; it is the key every mechanical seam resolves the opponent by (`find_creature_core`, `session.py:1915-1921`), and `encounter_lifecycle.py:438-446` carries a review-mandated invariant that it must equal `Npc.core.name`. Repointing it makes the enemy unhittable. Scope is not a reason to ship an unkillable opponent. The `display_name` option TEA rejected is the correct one, and it is what ADR-156 §6 actually describes. Re-scope the story to include `sidequest-ui`.
- **TEA — "Added an invariant the story text does not state: the pre-promotion placeholder must STILL resolve"** → ✓ **ACCEPTED by Reviewer.** Correct instinct, correctly forced the implementation to be alias-aware rather than destructive. Test 4 is good. It simply did not go far enough: it pinned that the OLD name still resolves through `find_actor`, but never asked whether the NEW name resolves through `find_creature_core`. That second half is the missing test.
- **Dev — "Promoted the seat at the ATTACH site instead of selecting an alias at the DISPLAY site"** → ✗ **FLAGGED by Reviewer.** The *attach-site* choice is sound and Naomi's reasoning against a read-time projection is correct as far as it goes (`build_confrontation_payload` genuinely cannot reach `Npc.aliases`). What is flagged is the consequence she inherited from TEA's deviation: promoting by mutating `EncounterActor.name`. Her own analysis — "`EncounterActor.name` is simultaneously the label the panel renders and a load-bearing entity id" — was exactly right, and the correct conclusion from it is *stop overloading the field*, not *make the field resolve two ways*. She made it resolve two ways inside the encounter; it still resolves only one way outside it.
- **Dev — "AC 'plural aliases on one identity' is not exercised — the design makes it unreachable"** → ✓ **ACCEPTED by Reviewer, with an amendment.** The unreachability claim is TRUE and `reviewer-test-analyzer` verified it against the real gate (`not other.aliases` closes leg 2 permanently after the first attach). Flagging it rather than fudging a test was the right call. **Amendment:** what happens *instead* is worse than "nothing" — a second hostile naming of an already-promoted Other mints a phantom `NpcPoolMember`, the exact phantom-twin ADR-156 §6 exists to prevent. That belongs in a ticket, not in this AC.
- **Dev — "Added `green_room.actor_promoted` and the `_repoint_actor_name` reference sweep — neither is required by any test"** → ✓ **ACCEPTED by Reviewer (intent), with two defects.** The instinct was right and is the best work in this diff: Naomi correctly reasoned that the RED fixture seats a bare encounter, so a rename would pass all 8 tests while silently orphaning a WN initiative token in a real game. That is exactly the reasoning a reviewer wants to see. Two defects, neither fatal: (a) the sweep is **incomplete** — it misses `TableState.seats[].party_name` and `FateExchangeLine.actor/.target`; (b) it is **entirely untested**, so a bug in any of its 7 branches would fail nothing (rule 18). Keep the sweep — it survives the redesign.

### TEA (test design — rework round 2)
- **Reversed my own round-1 deviation: the promoted name moves OFF `actors[].name` and onto a new `display_name` field**
  - Spec source: my own round-1 deviation ("Pinned the promoted name on the existing `actors[].name` key rather than a new `display_name` key"), FLAGGED by Reviewer
  - Spec text (round 1, mine): "A new key would leave the rendered name unchanged and the player-visible split still on screen unless `sidequest-ui` also changes — which this server-scoped story does not carry. Pinning `name` keeps the fix server-only, as scoped."
  - Implementation: the suite is rewritten to assert `actors[].display_name == PROSE` **and** `actors[].name == COAL`. A new `sidequest-ui` RED suite pins `display_name ?? name` rendering. Story re-scoped to `repos: server, ui`.
  - Rationale: my round-1 rationale was wrong, and wrong in a specific way — I chose the design that fit the story's scope instead of the design that worked. `actors[].name` is the entity id `find_creature_core` resolves the opponent's stat block by; writing the prose name into it made the enemy unhittable. ADR-156 §6 already describes two names on two surfaces ("the panel may show 'Molgrath the Eyeless' **while the engine keys on** `creature_id=Thief`"), and both `encounter_lifecycle.py:438-446` and `ConfrontationOverlay.tsx` already carry comments saying the field must never be rewritten. I designed against the codebase's own documented invariant to avoid touching a second repo.
  - Severity: **major** (this deviation caused the CRITICAL that rejected the story)
  - Forward impact: Dev's `_repoint_actor_name` sweep, `EncounterActor.aliases`, and the `find_actor` alias leg all become unnecessary — with no rename there is nothing to repoint and no collision to guard. The GREEN implementation is now smaller than the one being replaced. `find_creature_core` must gain an alias-aware roster leg so the narrator can still target by the prose name.
- **`green_room.actor_promoted` span attributes changed from `old_name`/`new_name` to `seat_id`/`display_name`**
  - Spec source: Reviewer finding (the span had zero test coverage); the new design
  - Spec text: Dev's span carried `old_name`, `new_name`, `references_rewritten`
  - Implementation: the suite now pins `seat_id` + `display_name` + `side`. `references_rewritten` is dropped — nothing is rewritten any more.
  - Rationale: the old attributes describe a rename that no longer happens. A span whose schema describes a deleted mechanism is worse than no span.
  - Severity: minor
  - Forward impact: `telemetry/spans/green_room.py`'s route extractor must change with it.

### TEA (test design — rework round 3)
- **Scope EXPANDED beyond the Reviewer's finding: a third broken projection (the tactical battle-map token) is pinned, which no review round identified**
  - Spec source: Reviewer round-2 finding ("[HIGH] Fate confrontation surface is half-wired"), which named two surfaces (Fate projection + `ConfrontationOverlay`'s `ActorChip`)
  - Spec text: "Forward `display_name` onto `FateConflictParticipant` and render `{o.display_name ?? o.name}` while keeping `value={o.name}`. Same pattern as `ConfrontationOverlay`."
  - Implementation: I ran a consumer sweep from the *field* rather than from the diff and found **three** projections that read `EncounterActor`, not two. `map_emit._place_tokens_on_anchors` (`map_emit.py:107`) builds `TokenPayload(token_id=f"creature:{actor.name}", label=actor.name, ...)` — a wire model that **already has a clean id/label split** — and feeds the seat id into `label`. Tests 4-6 of the new suite pin it.
  - Rationale: I nearly scoped this out as "a different subsystem (the battle map), needs its own design decision." That reasoning did not survive reading the code: the token is built directly from `EncounterActor`, the promotion fires for it with no ruleset gate, and `TokenPayload.label` is unambiguously the display field. It is this story's bug on a third surface, and the fix is one line because the id/label split already exists. Scoping it out would have been choosing the boundary that was convenient over the boundary that was true — which is precisely the round-1 error (I picked the design that fit the scope instead of the one that worked).
  - Severity: minor (scope grows; the implementation does not — one line server-side, zero UI changes, since `TacticalGridRenderer` already renders `label` and derives its glyph from `label[0]`)
  - Forward impact: Dev fixes three projections, not two. The map needs no UI change.
- **`promote_actor`'s contract is DEFINED here, not merely pinned — the ACs never specified re-promotion or no-op semantics**
  - Spec source: Reviewer round-2 finding ("[LOW] `promote_actor` has no direct unit tests... Pin the intended contract"); ADR-156 §6; SOUL.md *Diamonds and Coal*
  - Spec text: ADR-156 §6 defines attach-before-mint and "one enemy, one identity, two names" but is silent on what a *second*, different stage name means, and on a stage name identical to the seat id.
  - Implementation: I pinned **first-name-wins** (an already-promoted seat refuses a different stage name and keeps the first) and **no-op-emits-no-span** (a blank name, or a label equal to the seat id, returns `False` and emits **no** `green_room.actor_promoted`).
  - Rationale: first-name-wins because promotion is coal→diamond, a one-way door — silently relabelling would make the panel's name *churn* mid-fight while the prose and the alias ledger keep the original, re-introducing this story's exact bug from the other direction. No-op-emits-no-span because the GM panel reads `actor_promoted` as proof the player's screen changed; a span for a promotion that changed nothing makes the lie detector lie, which is the failure mode this entire review round exists to punish. The narrator path already cannot re-promote (`_attach_before_mint` gates on an empty alias ledger), so the contract is currently held **by accident, by a caller** — pinning it at the seam that owns it is the point.
  - Severity: minor (a contract choice, not a behavior change to any live path)
  - Forward impact: Dev adds two guard clauses to `promote_actor`. If the project later wants last-name-wins, this is the test to argue with — which is the correct place for that argument.
- **The end-to-end `apply_damage` tests land GREEN, not RED — they are regression pins, not new behavior**
  - Spec source: Reviewer round-2 finding ("[MEDIUM] The suite still never drives the damage path end-to-end... Add the end-to-end damage test using the existing harness")
  - Spec text: "A suite that stops one call short of the bug it exists to prevent is how we got here."
  - Implementation: `test_the_promoted_other_actually_takes_damage_by_its_prose_name` and `..._by_its_seat_id` both **pass on arrival**, because Naomi's round-2 `find_creature_core` fix already works. I am handing Dev two green tests.
  - Rationale: the Reviewer verified this by hand with a throwaway script; a hand-run script protects nothing. These are the round-1 kill-shot converted into permanent guards — if anyone ever re-points the seat id again, they go red instantly. A green regression guard in a rework round is correct, not vacuous (same call as 162-7). **Stating it explicitly so `testing-runner`'s "all green" is not misread as "nothing to do."**
  - Severity: minor
  - Forward impact: none — but do not delete them for being green.


## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:** (all `sidequest-server`, +155/-3)
- `sidequest/game/encounter.py` — `EncounterActor.aliases` ledger; `find_actor` made alias-aware
  (two whole-list passes: canonical, then aliases, so one actor's canonical always outranks
  another's alias); new `StructuredEncounter.promote_actor` (additive rename: placeholder moves to
  `aliases`, name is repointed, span emitted) and `_repoint_actor_name` (sweeps the in-encounter
  references that hold an actor name by exact match and outlive a rename).
- `sidequest/server/narration_apply.py` — `_attach_before_mint`'s seated-Other leg now calls
  `enc.promote_actor(seat, name)` on a fresh attach. Docstring updated: the leg does two things now.
- `sidequest/telemetry/spans/green_room.py` — new `green_room.actor_promoted` route.

**What was actually broken.** The attach half of ADR-156 §6 already worked — the prose name landed in
`Npc.aliases`. Nothing read it. The panel renders `EncounterActor.name`, baked with the coal
placeholder once at seat time, so the table read *"Ihnsch of the Rusted Works"* in the narration
against `[ the Scrapborn ]` in the panel. A projection gap, not an attach gap.

**The fix, and why it isn't a rename.** `EncounterActor.name` is simultaneously the label the panel
renders and a load-bearing entity id (the UI hands it back as a tag target; `find_actor` is an exact
string match). Both naive fixes break something — rename the payload only and the UI targets a name
the engine can't resolve; rename in place and every earlier-turn reference dangles. So the promotion
is *additive*: the seat is renamed, the placeholder survives in a new `EncounterActor.aliases`, and
`find_actor` resolves BOTH names onto the same actor. Identity does not churn — `core.name` stays
coal, so the GENERIC origin's `identity_key` (which keys on the normalized display name) is stable;
promoting the canonical would have forked the very ledger §6 exists to prevent.

Beyond the tests, `_repoint_actor_name` repoints the references a rename would otherwise orphan
(`initiative[].token_id` — the WN round walk keys on the actor name — plus WN/Fate sealed commits, the
Fate DEFEND barrier, compels, tags, taunt). The RED fixture seats a bare encounter, so a rename passes
all 8 tests while silently breaking a real WN round; that's the silent failure the project rules
forbid and it isn't visible from the suite. See Design Deviations.

**Tests:** 8/8 passing (3 were RED). Full server suite: 14,972 passed / 4 failed / 341 skipped.

**The 4 failures are pre-existing — verified, not assumed.** I stashed my changes and ran the full
suite on the branch base: it fails 7 (my 3 RED tests + the same 4). Post-change it fails exactly those
4. Zero regressions. They are `test_companion_brain_telemetry_passthrough.py` (2, ADR-154 territory,
fail in isolation on a clean tree) and two xdist-ordering flakes
(`test_102_5_wn_tool_narrator_wiring`, `test_pregen_bestiary_90_1[evropi]`) — all four already logged
under "Known suite noise as of 2026-07-10" in `dev-gotchas.md`, and that entry held up exactly.

**Lint / format / types:** `ruff check` + `ruff format --check` clean on all 3 files; `pyright` adds 0
new errors (the 37 in `narration_apply.py` / `encounter.py` are pre-existing on the base).

**OTEL:** `green_room.alias_attached` proves the identity learned the name; the new
`green_room.actor_promoted` proves it reached the surface the player is looking at, and its
`references_rewritten` count means a dangling tag target shows up in the GM panel as a `0` that should
not be. Without both, a panel still reading "the Scrapborn" under narration saying "Ihnsch" is
indistinguishable from the narrator improvising a name with no engine behind it.

**Branch:** `feat/166-10-green-room-coal-to-diamond-name-promotion` (pushed, commit `db69a6d0`)

**Handoff:** To next phase (verify / review). No PR — SM opens it at finish.
---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8/8 story green; 4 known-noise failures verified pre-existing; ruff/pyright clean) | N/A — mechanically clean, which decides nothing |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | Disabled via settings — domain covered by Reviewer (collision + persistence probes, below) |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped | disabled | Disabled via settings — domain covered by Reviewer (the CRITICAL is a silent-failure finding) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 (3 real, 2 explicit "no action") | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | Skipped | disabled | Disabled via settings — domain covered by Reviewer (pydantic/persistence probe: SAFE) |
| 7 | reviewer-security | Yes | Skipped | disabled | Disabled via settings — no auth/injection/tenant surface in this diff (narrator-derived prose → pydantic `str`) |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | Disabled via settings — no over-engineering observed; the sweep is warranted, just incomplete |
| 9 | reviewer-rule-checker | Yes | findings | 2 (rule 18 x2) | confirmed 2; **1 VERDICT CHALLENGED** — see below |

**All received:** Yes (4 ran, 5 disabled and covered by Reviewer)
**Total findings:** 11 confirmed, 0 dismissed, 0 deferred

### Challenged subagent verdict

`reviewer-rule-checker` concluded *"The change is functionally correct and well-wired to production"* and passed rules 15 (No Stubbing), 17 (Verify Wiring) and 21 (No half-wired features — *"all 7 connections present"*). **I am overriding that.** It enumerated the connections *inside the diff* and never followed `EncounterActor.name` out of the encounter to its consumers. There is an **8th connection it missed**: the actor→`CreatureCore` resolution seam (`GameSnapshot.find_creature_core`, `session.py:1904-1921`), which is an EXACT match against `Npc.core.name` — a name this change deliberately leaves as coal. That connection is severed, and `reviewer-comment-analyzer` reproduced the same break independently. Rule 21 is a **violation**, not a pass. Evidence below.

## Reviewer Assessment

**Verdict:** REJECTED

### The one-line version

The story set out to make the panel show the enemy's real name. It succeeds — and in doing so makes that enemy **impossible to hit**.

### Data flow traced (the finding that decides this review)

`narrator prose "Ihnsch of the Rusted Works"` → `_apply_npc_mentions` → `_attach_before_mint` leg 2 → `attach_alias(npc)` **+ NEW** `enc.promote_actor(seat)` → `EncounterActor.name = "Ihnsch of the Rusted Works"` → `build_confrontation_payload` → **panel shows "Ihnsch of the Rusted Works"** → player clicks it / narrator targets it → `DICE_THROW.target` / `apply_damage.target` = `"Ihnsch of the Rusted Works"` → `GameSnapshot.find_creature_core(name)` → **`None`**.

`find_creature_core` (`session.py:1915-1921`) is an exact match against `Npc.core.name`. Story 166-10 *deliberately* keeps `core.name` as the coal placeholder (`"the Scrapborn"`) to hold `identity_key` stable — TEA's test 2 pins exactly that. So after a promotion, `actor.name != npc.core.name`, **permanently, by design**, and every consumer that resolves the opponent's mechanical core by name gets nothing.

I reproduced it against the real code, not by reading it:

```
=== AFTER promotion ===
  seat.name     = 'Ihnsch of the Rusted Works'   <- what the PANEL shows
  npc.core.name = 'the Scrapborn'                <- stays coal BY DESIGN
  find_creature_core('Ihnsch of the Rusted Works') -> *** None ***
  find_creature_core('the Scrapborn')             -> FOUND hp=8
```

`find_creature_core` is the `edge_resolver` for `apply_beat`/`resolve_opposed_check` and backs `apply_damage.py:86`, `wn_tools.py:236`, `apply_status`, `commit_effort`, `query_encounter`, `use_mutation`, `stabilize_mortal_injury`, `veterans_luck`, `adjust_system_strain`. Both attack tools hard-fail identically: `if target_core is None: return ToolResult.not_found(f"unknown target: {args.target!r}")`. The player's own path is no better — `dice.py:754` resolves the target through `find_creature_core` and passes it as `edge_resolver` into `apply_beat` (`dice.py:1995, 2004`).

**So: the player throws the dice, the dice land, and nothing happens.** For the two mechanics-first players this project explicitly names — Sebastien and Jade — that is the worst failure the engine can produce: visible math that does nothing.

### The codebase already told us this

`encounter_lifecycle.py:438-446` carries a comment written to close a *prior* review's [HIGH] finding:

> *"an alias / case-variant hit must CANONICALIZE the seat — every downstream consumer resolves the opponent core by exact `actor.name` (`find_creature_core`: the HP-bar filter, WN attack tools, query_encounter, payload builder), so **a seat left under the prose alias is an unreachable opponent**."*

That is a documented, review-mandated invariant: **`EncounterActor.name` MUST equal `Npc.core.name`.** This story breaks it deliberately. Worse, the two sites enforcing it (`encounter_lifecycle.py:446` and `:1114`) do `actor.name = npc.core.name` — so on the next seating/handshake pass they will **silently revert the promotion** and the panel flips back to "the Scrapborn". The feature undoes itself.

### Severity table

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [CRITICAL] | Promoted opponent is mechanically unreachable. `find_creature_core` is exact-match on `Npc.core.name`, which the promotion leaves as coal — so `apply_damage`, `wn_tools`, `apply_status`, `query_encounter` and `dice.py`'s `edge_resolver` all return `not_found` for the name the panel shows. The enemy takes no damage. | `sidequest/game/encounter.py:473` (promote) ↔ `sidequest/game/session.py:1904-1921` (resolve) | Do not repoint `EncounterActor.name`. Carry the display name in a separate field and render *that* (needs a `sidequest-ui` change), OR make `find_creature_core` + every `core.name ==` seam alias-aware. See "Fix direction". |
| [HIGH] `[DOC]` | Panel silently drops `opponent_hp` post-promotion on every hp_depletion (WWN/SWN) encounter — the HP bar vanishes from the overlay. Independently reproduced by `reviewer-comment-analyzer`. | `sidequest/server/dispatch/confrontation.py:538-551` | Same root cause. |
| [HIGH] | Violates the documented, review-mandated invariant `EncounterActor.name == Npc.core.name`; the two sites enforcing it will silently **revert** the promotion on the next seat/handshake. | `sidequest/server/dispatch/encounter_lifecycle.py:438-446`, `:1105-1114` | Reconcile with the invariant, or change it deliberately and update those sites. |
| [HIGH] | `wn_round.py:277`'s 0-HP `actor_downed` check resolves via `find_creature_core(token)` → silently no-ops for a promoted actor. A promoted enemy at 0 HP never goes down. | `sidequest/server/dispatch/wn_round.py:277` | Same root cause. |
| [HIGH] | Actor→NPC lookups that use a direct `n.core.name == actor.name` comparison silently degrade: the tactical-map token loses HP **and** AC (`map_emit.py:99`), and the Fate-contest / opposed-check presence stamps are skipped — so an *actively fighting* NPC reads as stale to the last-seen prune, the exact bug those stamps exist to prevent. | `map_emit.py:99`, `fate_contest.py:157`, `narration_apply.py:9037`, `dogfight.py:198` | Route through `resolve_roster_npc`, or remove the root cause. |
| [MEDIUM] `[EDGE]` | `promote_actor` has **no collision guard**. Reproduced: promoting onto a name another seated actor already answers to yields two actors sharing a canonical name, and `find_actor` is first-wins — the bystander **shadows the enemy**. Silent misroute, not a loud failure (No Silent Fallbacks). | `sidequest/game/encounter.py:473` | Reject the promotion loudly on collision. |
| [MEDIUM] `[TEST]` | `_repoint_actor_name` misses two name-bearing families: `TableState.seats[].party_name` (the leg has no encounter-type gate, so it fires on a poker/auction table too, breaking payout attribution) and `FateExchangeLine.actor/.target` (the player-facing "Last Exchange" ledger). | `sidequest/game/table/types.py:28`, `sidequest/protocol/models.py:1159` | Extend the sweep or gate the leg. |
| [MEDIUM] `[TEST]` | A **second** hostile naming of an already-promoted Other mints a phantom `NpcPoolMember` — precisely the phantom-twin ADR-156 §6 exists to prevent. Reproduced by `reviewer-test-analyzer` against the real `_apply_npc_mentions`. | `sidequest/server/narration_apply.py:2687` | Ticket separately; pin current behavior with a regression test. |
| [MEDIUM] `[RULE]` | Rule 18 (Every Test Suite Needs a Wiring Test): `_repoint_actor_name`'s ~50 lines across 7 field families have **zero** coverage — test 4 passes identically if the method is deleted. The new `green_room.actor_promoted` span is likewise never asserted. Confirmed by both `reviewer-rule-checker` and `reviewer-test-analyzer`. | `tests/server/test_166_10_coal_to_diamond_panel_name.py` | Seed each family pre-promotion and assert the repoint + the span. |
| [LOW] `[DOC]` | `promote_actor`'s docstring asserts "the rename is additive, never destructive" and "nothing stamped before the promotion dangles". Both are false — see CRITICAL. A confidently wrong docstring is worse than none. | `sidequest/game/encounter.py:487` | Rewrite once the design is settled. |
| [LOW] `[DOC]` | Test docstring cites `find_actor` at `encounter.py:446`; this diff moved it to `:457`. Stale on arrival. | `tests/server/test_166_10_coal_to_diamond_panel_name.py:259` | Drop the line number. |

### Verified good (with evidence, and rule-checked)

- `[VERIFIED]` **Persistence is safe.** `EncounterActor.aliases` is `Field(default_factory=list)` on a model with `extra="forbid"` — I loaded a pre-166-10 actor dict with no `aliases` key and it defaulted cleanly, and a promoted encounter round-trips through `model_dump`→`model_validate` intact. `extra="forbid"` rejects unknown keys on input; it does not require declared keys. Complies with python.md #2 (mutable defaults) and the ADR-115 snapshot contract.
- `[VERIFIED]` **`find_actor`'s precedence order is correct.** Two whole-list passes — canonical, then alias — so one actor's canonical always outranks another's alias. Reproduced: with actor A aliased "Ihnsch" and actor B *named* "Ihnsch", `find_actor("Ihnsch")` returns B. `encounter.py:457-470`. Mirrors `origin.resolve_roster_npc`'s documented order.
- `[VERIFIED]` **The OTEL span is properly registered.** `SPAN_GREEN_ROOM_ACTOR_PROMOTED` is in `SPAN_ROUTES` with a valid `event_type`/extractor (`telemetry/spans/green_room.py:76-95`); `tests/telemetry/test_routing_completeness.py` passes. Complies with the OTEL Observability Principle *as registration* — though nothing asserts it fires (see MEDIUM).
- `[VERIFIED]` **The lazy telemetry import is the house pattern, not a hygiene violation.** `promote_actor`'s function-local `from sidequest.telemetry.spans import ...` (`encounter.py:500`) mirrors its own ADR-156 siblings `green_room.attach_alias:87` and `admit:113`. Complies with python.md #10.
- `[VERIFIED]` **No regressions.** Dev's "4 pre-existing failures" claim is true — I confirmed the clean-tree baseline independently before trusting it.

### Devil's Advocate

Let me argue the other side as hard as I can, because a REJECT on a story whose tests are 8/8 green deserves the challenge.

*The defence:* Naomi identified exactly the right class of bug — dangling references after a rename — and went beyond her tests to sweep them. The rule-checker, reading the diff on its own terms, called the work correct. Persistence is safe. The span is registered. The precedence order is right. Every test passes, ruff is clean, pyright adds nothing. On the evidence *inside the diff*, this is careful, disciplined work, and I should approve it.

*And that is precisely the trap.* The diff is internally coherent and externally catastrophic. The bug does not live in any line Naomi wrote; it lives in the seam between the line she wrote (`actor.name = new_name`) and a line she never opened (`session.py:1919`, `if npc.core.name == name`). Her tests could not catch it because they construct a `StructuredEncounter` directly and drive only `_apply_npc_mentions` and `build_confrontation_payload` — they never resolve a `CreatureCore`, never apply damage, never walk a WN round. The suite is a closed loop around the two functions that changed, and it is green *because* it never asks the one question that matters: after you rename the enemy, can you still hit it?

What would a confused user do? Exactly what the feature invites. They see "Ihnsch of the Rusted Works" on the panel — the story's whole purpose — and they attack it. It doesn't die. They attack again. It still doesn't die. There is no error, no red text, no span screaming in the GM panel; `apply_damage` returns a tidy `not_found` and the narrator, being Claude, cheerfully improvises a miss. This is *the exact failure mode this project's OTEL doctrine exists to catch* — "Claude is excellent at winging it, writing convincing narration with zero mechanical backing" — and the change ships a brand-new way to manufacture it. The irony is total: a story filed under *Diamonds and Coal*, to make the world's naming legible to the player, ends by making the enemy invulnerable and invisible to the math.

And the codebase warned us, in plain English, in a comment written to close a previous [HIGH] on this very seam: *"a seat left under the prose alias is an unreachable opponent."* We had already paid for this lesson once. The honest conclusion is that the design is wrong, not the execution — and the design was chosen to keep the story inside a server-only scope. Scope is not a reason to ship an unkillable enemy.

### Fix direction (for Amos and Naomi)

The three constraints are jointly unsatisfiable as currently framed:
1. `identity_key` for a GENERIC origin keys on normalized `core.name` → renaming `core.name` **forks the identity** (§6's whole point). Correct — keep it.
2. Every mechanical seam resolves the opponent core by exact `core.name`, and `encounter_lifecycle` actively enforces `actor.name == core.name`.
3. The panel renders `actor.name`.

You cannot have (1), (2) and a promoted `actor.name` at once. So drop (3) as the lever:

**Carry the display name as a separate field.** `EncounterActor.display_name: str | None` (or project it in `_actor_with_portrait`), leave `name` canonical so every mechanical seam keeps working, and have `ConfrontationOverlay` render `display_name ?? name`. This is what ADR-156 §6 actually describes — *"the combat panel may show 'Molgrath the Eyeless' **while the engine keys on** `creature_id=Thief`"* — two names on two surfaces, not one field doing double duty. It costs a small `sidequest-ui` change, which means **re-scoping the story to `repos: server, ui`**. Drummer flagged that exact server/UI question at setup; TEA closed it as "server-only, no UI change needed", and that closure — made to protect scope — is the root cause of this rejection.

The alias-aware `find_actor`, the `EncounterActor.aliases` ledger, and the `_repoint_actor_name` sweep are all still useful under that design and should be kept — they just stop being load-bearing for the panel.

**Handoff:** Back to Amos (TEA) — the findings are testable, and the missing test is the root cause. The RED suite needs a test that promotes an Other and then **attacks it**.

### Dev (implementation — rework round 2)
- **Deleted `_repoint_actor_name`, `EncounterActor.aliases`, and `find_actor`'s alias leg — all of it was my own round-1 code**
  - Spec source: TEA's rework suite (test 6, `promotion_leaves_the_seat_id_and_its_references_alone`); Reviewer's REJECT
  - Spec text: round 1 I logged this sweep as a deliberate above-spec addition — "a rename that silently dangles initiative would be a silent regression... that's the silent failure the project rules forbid."
  - Implementation: removed entirely. `promote_actor` now writes only `EncounterActor.display_name`; the seat id is never touched.
  - Rationale: the reasoning was sound but it was defending the wrong thing. The sweep existed only because I was renaming a load-bearing entity id; once the promotion becomes a display-only label, nothing moves, so nothing can dangle. **When the implementation needs a defensive sweep to survive a test, suspect the test.** Net −41 lines against the implementation this replaces.
  - Severity: minor (deletion of my own dead machinery — no external consumer ever existed)
  - Forward impact: none. `EncounterActor.aliases` never shipped past review, so no save carries it; the field is gone with no migration needed.
- **`find_creature_core`'s NPC leg is now alias-aware (`resolve_roster_npc`); the character leg keeps its exact match and is still checked FIRST**
  - Spec source: TEA rework test 4 (`the_narrator_can_target_the_other_by_its_prose_name`)
  - Spec text: AC — "find_creature_core resolves it BOTH by seat id and by the prose name (via the alias ledger)"
  - Implementation: `session.py:find_creature_core` — characters exact-match first (unchanged), then NPCs resolve through `resolve_roster_npc` (canonical → alias → `invented_from`).
  - Rationale: once the world names the Other, the narrator's *next* turn hands that prose name to `apply_damage(target=...)`. On a bare exact match that is a `not_found` and the damage silently never lands. Character-leg-first ordering means a PC can never be shadowed by an NPC's alias.
  - Severity: minor — a widening, not a behavior change: every name that resolved before still resolves to the same core (`resolve_roster_npc`'s leg 1 IS the old exact match, modulo `normalize_name` case/whitespace folding).
  - Forward impact: `resolve_roster_npc` emits `identity.resolved` on alias/`invented_from` hits only, so canonical lookups (the overwhelming majority, incl. every PC) add no span traffic. A promoted Other targeted by prose name emits one span per resolution — informative, not spam.
- **`green_room.actor_promoted` span attributes changed to `seat_id` + `display_name` (dropping `old_name`/`new_name`/`references_rewritten`)**
  - Spec source: TEA rework test 8
  - Spec text: the span must carry "the seat id it promoted and the display name it gave it"
  - Implementation: `telemetry/spans/green_room.py` route extractor updated to match.
  - Rationale: the old attributes described a rename that no longer happens. Carrying `seat_id` *and* `display_name` is what lets the GM panel verify the two stayed **distinct** — which is the whole invariant.
  - Severity: minor
  - Forward impact: the span never shipped past review, so no dashboard or forensic query depends on the old shape.

### Dev (implementation — rework round 3)
- **I EDITED ONE OF TEA'S TESTS — the Last Exchange ledger assertion was re-scoped (not weakened)**
  - Spec source: TEA's RED suite, `fate-conflict-display-name-166-10.test.tsx` → `"shows the prose name in the Last Exchange ledger"`
  - Spec text: `expect(screen.getByText(new RegExp(PROSE))).toBeInTheDocument();` — an **unscoped** document-wide query.
  - Implementation: re-scoped to the section under test — `const ledger = within(screen.getByTestId("fate-last-exchange")); expect(ledger.getByText(new RegExp(\`^${PROSE} attacks\`)))...` plus `ledger.queryByText(/Scrapborn/)` must be absent.
  - Rationale: the unscoped query matched **zero** elements at RED (every site showed the coal name) and **three** once I fixed all seven display sites — the participants roster, the opponent-track heading and the ledger clause all legitimately contain the prose name now, so `getByText` threw "found multiple elements". **The implementation is correct and the test's scope was the bug.** I did not touch the implementation to satisfy a loose assertion, and I did not weaken the test: the anchored `^${PROSE} attacks` regex is *stricter* than the original (it pins the clause's subject position, not a substring anywhere in the DOM), and the negative `/Scrapborn/` assertion is retained inside the scope. Flagging it loudly because Dev editing TEA's test is exactly the move that should get scrutiny.
  - Severity: minor
  - Forward impact: none. Amos should sanity-check the re-scope in verify.
- **The shared display helper was HOISTED to `src/lib/actorDisplayName.ts` rather than exported from `ConfrontationOverlay.tsx`**
  - Spec source: TEA handoff — "route **every** Fate display site + `ActorChip`'s initial through a shared `actorDisplayName()` (which must be exported from `ConfrontationOverlay.tsx`, **or hoisted to `src/lib/`**)"
  - Spec text: TEA offered both options and named the hoist as the better one.
  - Implementation: new `src/lib/actorDisplayName.ts` exporting `humanizeActorName`, `actorDisplayName`, and a `DisplayableActor { name; display_name? }` interface. Both surfaces import it; the private copies in `ConfrontationOverlay` are deleted.
  - Rationale: typing the helper on a minimal `DisplayableActor` shape lets it serve `EncounterActor` **and** `FateConflictParticipant` with no coupling between the two wire types. Exporting from `ConfrontationOverlay` would have made the Fate surface import from a sibling *component* — it would work, and it is the wrong seam. The helper's own docstring already promised "one helper, used at every display site"; that promise was true within the file and false across the app, which is how the Fate surface drifted.
  - Severity: minor
  - Forward impact: any future actor-rendering surface imports from `@/lib/actorDisplayName`. Nothing else moves.
- **`promote_actor`'s "already promoted" guard is `actor.display_name is not None`, which also makes an IDEMPOTENT re-promotion return False**
  - Spec source: TEA's tests 9-11 (`promote_actor` contract)
  - Spec text: TEA pinned blank → False, `display_name == actor.name` → False, and re-promotion with a *different* name → False.
  - Implementation: three sequential guards; the third is `if actor.display_name is not None: return False`. This means re-promoting with the **same** name also returns False (the old code's `display_name == actor.display_name` check returned False for that case too, so behavior is unchanged) — but it is now covered by the broader "first name wins" rule rather than an equality check.
  - Rationale: one rule ("a promoted seat is not re-promotable") is simpler than two ("not with a different name" + "not with the same name") and produces identical behavior on every input. Fewer branches, same contract.
  - Severity: minor
  - Forward impact: none — no caller re-promotes (`_attach_before_mint` gates on an empty alias ledger).


### Reviewer (audit — round 2)
- **Dev — "Deleted `_repoint_actor_name`, `EncounterActor.aliases`, and `find_actor`'s alias leg — all of it was my own round-1 code"** → ✓ **ACCEPTED by Reviewer.** Correct, and the right instinct stated in the right words: *"when the implementation needs a defensive sweep to survive a test, suspect the test."* Verified repo-wide: zero orphans. The deletion is the best thing in this diff.
- **Dev — "`find_creature_core`'s NPC leg is now alias-aware; the character leg keeps its exact match and is still checked FIRST"** → ✗ **FLAGGED by Reviewer.** The character-first ordering is correct and I verified it (a PC cannot be shadowed by an NPC alias). But the deviation is logged as *"a widening, not a behavior change: every name that resolved before still resolves to the same core."* **That claim is false.** `resolve_roster_npc` normalizes (casefold + diacritic-fold + whitespace-collapse) and returns the first roster match; the old leg was an exact `==`. Two NPCs whose names differ only by case now resolve to the **wrong one** — I reproduced it, and so did `reviewer-test-analyzer`. The parenthetical "modulo `normalize_name` case/whitespace folding" is doing far more work than it admits: that modulo IS the regression. Fix: exact match first, then fall back.
- **Dev — "`green_room.actor_promoted` span attributes changed to `seat_id` + `display_name`"** → ✓ **ACCEPTED by Reviewer.** Right call, right reason (*"a span whose schema describes a deleted mechanism is worse than no span"*). Registered, extractor matches the emit, routing test passes. Carrying both the id and the label is exactly what lets the GM panel verify they stayed distinct.

### Reviewer (audit — UNDOCUMENTED deviations)
- **The story's fix was applied to ONE of the two confrontation surfaces, and this was not logged.** The Dev assessment states the helper was wired into "**all four** display sites" — that is four sites within `ConfrontationOverlay`. `FateConflictSurface` (fed by `fate_projection.py`) is a second, independent confrontation surface that renders the actor name — including the attack-target dropdown — and it was neither wired nor flagged. Spec: the AC says "the confrontation panel carries the prose name to the player." Code: only the native/WN panel does. Severity: **HIGH**. Not documented by Dev or TEA.
- **`ActorChip`'s avatar initial (`ConfrontationOverlay.tsx:384`) is a fifth display site in the very component that was "fully wired".** Renders `actor.name.charAt(0)`, so the coal name still reaches the screen. Severity: **MEDIUM**. Not documented.

---
## TEA Assessment (rework round 2)

**Tests Required:** Yes
**Test Files:**
- `sidequest-server/tests/server/test_166_10_coal_to_diamond_panel_name.py` — **rewritten**, 12 tests: **7 RED**, 5 green guards
- `sidequest-ui/src/__tests__/confrontation-display-name-166-10.test.tsx` — **new**, 3 tests: **2 RED**, 1 green guard (the fallback regression guard)

**Status:** RED confirmed on both repos. Server: 7 failed / 5 passed, every failure a real assertion (no collection or fixture errors — I hit one `WnSealedCommit.outcome` fixture error on the first run and fixed it; a test that errors is not a test). `ruff check` + `ruff format` clean. UI: 2 failed / 1 passed, `tsc --noEmit` and `eslint` clean.

### I wrote the test that shipped the bug

Round 1 of this suite pinned the promoted name on `actors[].name`, Dev implemented exactly that, all 8 tests went green, and the review found the enemy had become **impossible to hit**. `find_creature_core` exact-matches `Npc.core.name` — which the design deliberately keeps as coal to hold `identity_key` stable — so the moment `actor.name` carried the prose name instead, `apply_damage`, `wn_tools`, `apply_status`, `query_encounter` and the player's own dice throw all returned `not_found` for the enemy on screen.

My suite was green because it never left the blast radius. It constructed a `StructuredEncounter` directly and drove only the two functions that were going to change. **The test I owed and didn't write was one sentence long: rename the enemy, then attack it.** It is now test 3.

### The design this suite pins

Two names, two surfaces — which is what ADR-156 §6 said all along:

| | field | who reads it |
|---|---|---|
| **id** | `EncounterActor.name` — **unchanged**, canonical, `== Npc.core.name` | `find_creature_core`, `find_actor`, tag targets, initiative tokens, sealed commits |
| **label** | `EncounterActor.display_name: str \| None` — **new**, display only | `ConfrontationOverlay` → `display_name ?? name` |

Plus: `find_creature_core`'s roster leg becomes alias-aware (`resolve_roster_npc`) so the narrator — who now knows the enemy as "Ihnsch" — can still target it by that name.

**The corrected design is strictly smaller than the one it replaces.** Because nothing is renamed, there is nothing to dangle: Dev's `_repoint_actor_name` sweep across 7 structures, the `EncounterActor.aliases` ledger, and the `find_actor` alias leg all become unnecessary, and the two-actors-share-a-name collision the Reviewer found cannot occur. **Naomi: delete them.** That ~50 lines of careful defensive code existed only to survive my bad assertion.

### Test coverage

| # | Test | State | Teeth |
|---|------|-------|-------|
| 1 | `panel_shows_the_prose_name_after_the_coal_other_is_named` | **RED** | The story. `display_name == "Ihnsch…"`. Also the wiring test (real `_apply_npc_mentions` → real `build_confrontation_payload`). |
| 2 | `the_seat_id_the_engine_targets_stays_canonical` | **RED** | **The guard round 1 lacked.** `actors[].name` must stay `"the Scrapborn"`. This assertion fails a rename. It is the whole review. |
| 3 | `the_named_other_can_still_be_hit` | **RED** | **The question round 1 never asked.** `find_creature_core(seat.name)` must resolve to the live stat block. |
| 4 | `the_narrator_can_target_the_other_by_its_prose_name` | **RED** | The narrator now says "Ihnsch" and will pass it to `apply_damage`. Both names, one creature. |
| 5 | `the_panel_still_shows_the_others_hp_after_it_is_named` | **RED** | `_primary_hp` silently omits `opponent_hp` on a resolver miss — the HP bar vanishes. Asserts it survives, with a pre-promotion precondition so the fixture can't lie. |
| 6 | `promotion_leaves_the_seat_id_and_its_references_alone` | **RED** | Seeds an initiative token, a sealed commit and a tag under the seat id; all must be untouched. Pins *why* no sweep is needed. |
| 7 | `promotion_emits_the_alias_attached_span` | green guard | The identity learned the name. |
| 8 | `promotion_emits_the_actor_promoted_span` | **RED** | The name reached the surface. Now carries `seat_id` + `display_name`. |
| 9 | `promotion_does_not_churn_the_identity` | green guard | `identity_key` stable, `core.name` stays coal — and this is *why* `actor.name` can't carry the prose name either. Same constraint. |
| 10 | `authored_other_is_not_renamed_by_a_hostile_mention` | green guard | No hijack of a named villain. |
| 11 | `two_live_opponents_are_ambiguous_and_neither_is_renamed` | green guard | Never guess (No Silent Fallbacks). |
| 12 | `bystander_mention_does_not_rename_the_seated_other` | green guard | A merchant is not the enemy's true name. |

**UI:** `shows the narrator's prose name` (**RED**), `humanizes a slug display_name` (**RED**), `falls back to the seat id when the Other has not been named yet` (green guard — the regression guard for every actor in every existing confrontation).

### Rule coverage

Rules from `.pennyfarthing/gates/lang-review/python.md` + project doctrine applicable to this surface:

| Rule | Test(s) | Status |
|------|---------|--------|
| CLAUDE.md — **No Silent Fallbacks** | test 5 (`_primary_hp` silently drops `opponent_hp`); test 11 (never guess between two Others) | 1 RED, 1 guard |
| CLAUDE.md — **Verify Wiring, Not Just Existence** | tests 3, 4 — the promoted Other must be reachable from the *production* resolvers, not just present in the payload | RED |
| CLAUDE.md — Every Test Suite Needs a Wiring Test | test 1 spans both seams; UI suite renders the real `ConfrontationOverlay` | RED |
| CLAUDE.md — No Source-Text Wiring Tests | zero `read_text()`/grep assertions in either suite; both drive real code | passing |
| CLAUDE.md — OTEL Observability Principle | tests 7 + 8 — both halves of the promotion emit | 1 RED, 1 guard |
| SOUL.md — Diamonds and Coal | tests 1, 10, 12 — coal is promoted when the world names it; a diamond and a bystander are not | 1 RED, 2 guards |
| python #6 — Test quality (no vacuous assertions) | whole suite; test 5 carries a pre-promotion precondition so it cannot pass vacuously | passing |
| python #3 — Type annotations | fully annotated; `ruff check` clean; UI `tsc --noEmit` clean | passing |

**Self-check:** one fixture error found and fixed (`WnSealedCommit` requires `outcome`) — it surfaced as a `ValidationError`, not an assertion, and I will not hand Dev a suite whose failures aren't real. Re-ran: all 7 server failures are genuine assertions.

**Handoff:** To Naomi (Dev) for GREEN. The implementation gets *smaller*: add `display_name`, set it in `promote_actor`, make `find_creature_core` alias-aware, render `display_name ?? name` — and **delete** `_repoint_actor_name`, `EncounterActor.aliases`, and the `find_actor` alias leg.

---
## Dev Assessment (rework round 2)

**Implementation Complete:** Yes

**Files Changed:**

*`sidequest-server` (+84 / −125 — a net **41 fewer lines** than the implementation it replaces):*
- `sidequest/game/encounter.py` — `EncounterActor.display_name: str | None` (the label). **Removed** `EncounterActor.aliases`, `find_actor`'s alias leg, and `_repoint_actor_name` entirely. `promote_actor` now writes only the label and emits the span.
- `sidequest/game/session.py` — `find_creature_core`'s NPC leg resolves through `resolve_roster_npc` (canonical → alias → `invented_from`); characters keep their exact match and are still checked first.
- `sidequest/telemetry/spans/green_room.py` — `green_room.actor_promoted` now carries `seat_id` + `display_name` + `side`.
- `sidequest/server/narration_apply.py` — call site + docstring say what the leg actually does now.

*`sidequest-ui`:*
- `src/components/ConfrontationOverlay.tsx` — `EncounterActor.display_name?: string | null`; new `actorDisplayName(actor)` = `humanizeActorName(display_name ?? name)`, wired into **all four** display sites (roster chip title, portrait alt, sr-only roster label, THEM panel) so the roster and the panel cannot drift apart.

**What I got wrong, and what fixed it.** Round 1 I built exactly what the RED suite asked for and shipped an enemy that could not be hit. My own assessment contained the bug report — *"`EncounterActor.name` is simultaneously the label the panel renders and a load-bearing entity id"* — and I drew the wrong conclusion from it. The right move was to stop overloading the field; instead I made it resolve two ways and wrote a 7-structure reference sweep, an alias ledger and a two-pass `find_actor` to hold the overload together. **All of that machinery was the smell.** The rework deleted every line of it. `id` and `label` are now two fields, and the entire class of bug — dangling references, name collisions, the reverting seat-canonicalizer — cannot occur.

**Tests:** server 12/12 (7 were RED); UI 3/3 (2 were RED).
**Full suites:** server 14,976 passed / 4 failed / 341 skipped — the same 4 pre-existing failures I verified against a stashed clean tree earlier in this story, no regressions. UI 2,610/2,610 passed. `ruff check` + `ruff format --check` clean on all changed files; `pyright` adds 0 new errors; UI `tsc --noEmit` and `eslint` clean.

**Every Reviewer finding, addressed:**

| Sev | Finding | Resolution |
|-----|---------|------------|
| CRITICAL | Promoted opponent mechanically unreachable | **Fixed.** Seat id never repointed; `find_creature_core` also resolves the prose name. Pinned by tests 2, 3, 4. |
| HIGH | Panel silently drops `opponent_hp` | **Fixed.** `_primary_hp` resolves the canonical seat id again. Pinned by test 5 (with a pre-promotion precondition so it can't pass vacuously). |
| HIGH | Violates the `name == core.name` invariant; seat-canonicalizer would revert the promotion | **Fixed.** The invariant now holds by construction — there is nothing for `encounter_lifecycle` to canonicalize. |
| HIGH | `wn_round` downed-check no-ops for a promoted actor | **Fixed** by the same root cause. |
| HIGH | Map token loses HP/AC; presence stamps skipped | **Fixed** by the same root cause. Filed a follow-up finding: those four sites still use direct `core.name ==` comparisons and remain a latent trap. |
| MEDIUM | `promote_actor` has no collision guard | **Cannot occur.** No rename ⇒ no two actors can share a canonical name. |
| MEDIUM | Sweep misses `TableSeat.party_name` / `FateExchangeLine` | **Cannot occur.** The sweep is deleted; nothing is rewritten. |
| MEDIUM | Second naming mints a phantom `NpcPoolMember` | **Not fixed — pre-existing and out of scope.** Filed as a delivery finding by both Reviewer and TEA; needs its own story. |
| MEDIUM | `_repoint_actor_name` + the new span have zero coverage | **Fixed.** The sweep is gone; the span is now pinned by test 8. |
| LOW | `promote_actor` docstring claims "nothing dangles" (false) | **Fixed.** Rewritten — and now true, because nothing moves. |
| LOW | Stale `encounter.py:446` line citation in the test docstring | **Fixed** by TEA in the rework suite. |

**OTEL:** `green_room.alias_attached` proves the identity learned the name; `green_room.actor_promoted` carries `seat_id` **and** `display_name`, so the GM panel can verify the two stayed distinct — which is now the load-bearing invariant.

**Branch:** `feat/166-10-green-room-coal-to-diamond-name-promotion` on **both** `sidequest-server` and `sidequest-ui` (pushed).

**Handoff:** To review. No PR — SM opens them at finish (two now: server + ui).
---
## Subagent Results (review round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (server 12/12 + full suite clean; UI 2610/2610; lint/tsc/eslint clean) | N/A — mechanically clean, which again decides nothing |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | Disabled via settings — domain covered by Reviewer (I re-ran the round-1 kill-shot probe + attacked the `find_creature_core` widening) |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped | disabled | Disabled via settings — covered by Reviewer (the fold-collision finding is a silent-wrong-answer) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 6, dismissed 0, deferred 2 (low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | Skipped | disabled | Disabled via settings — covered by Reviewer (the id-vs-label distinction IS this story's type question; filed as an Improvement) |
| 7 | reviewer-security | Yes | Skipped | disabled | Disabled via settings — no auth/injection/tenant surface |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | Disabled via settings — the diff is a net deletion; nothing to simplify |
| 9 | reviewer-rule-checker | Yes | findings | 0 violations ("clean") | **VERDICT CHALLENGED AGAIN** — see below |

**All received:** Yes (4 ran, 5 disabled and covered by Reviewer)
**Total findings:** 9 confirmed, 0 dismissed, 2 deferred

### Challenged subagent verdict (second time)

`reviewer-rule-checker` returned **0 violations across 26 rules**, and specifically passed **rule 21 (No half-wired features)** with: *"display_name flows end to end: EncounterActor field → promote_actor → model_dump → WS payload → UI EncounterActor.display_name → actorDisplayName at all 4 render sites. **Verified no gap at any hop.**"*

**That is wrong, and it is wrong the same way it was wrong last round.** It traced the hops *the diff touches* and declared the pipeline complete. There is a second confrontation surface it never looked at, fed by a different projection the diff does not touch: `fate_projection._project_conflict_participant` → `FateConflictParticipant` → `FateConflictSurface.tsx`. `display_name` is dropped at that hop and the coal name renders — **including inside the dropdown the player uses to pick their attack target**. Rule 21 is a **violation**. Confirmed independently by `reviewer-test-analyzer` and re-verified by me at `fate_projection.py:156` and `FateConflictSurface.tsx:861`.

Twice now the rule-checker has certified a pipeline complete by enumerating only the path in front of it. Its "clean" is evidence about the diff, never about the system.

I also **do not accept** its dismissal of the `find_creature_core` fold-collision as *"acceptable given it mirrors this function's existing behavior everywhere else."* Everywhere else was already normalized; `find_creature_core` was not. The widening makes `apply_damage` pick the **wrong NPC**, deterministically and silently, at ~40 call sites. "Consistent with the other seams" is not a reason to kill the wrong creature.

## Reviewer Assessment

**Verdict:** REJECTED

### Credit where it's due — the CRITICAL is genuinely dead

I re-ran the exact probe that killed round 1, against the real code:

```
seat.name (the ID)        = 'the Scrapborn'      <- untouched, canonical
seat.display_name (label) = 'Ihnsch of the Rusted Works'
find_creature_core(seat id) -> FOUND hp=8
find_creature_core(prose)   -> FOUND hp=8
APPLY 3 DAMAGE via the resolved core -> npc hp now 5   <-- the enemy CAN be hit
```

The design is right, it is what ADR-156 §6 always described, and it came in **41 lines smaller** than the implementation it replaces. The reference sweep, the alias ledger and the collision hazard are all gone because the rename is gone. Naomi took the correction properly.

**This is a completeness rejection, not a correctness one.** The engine is sound. The feature is not finished.

### Why it is rejected anyway: the same bug is still live on four of eleven packs

`_attach_before_mint` has **no ruleset gate** (`narration_apply.py:2687-2705`) — the promotion fires for any encounter with a lone GENERIC/NARRATOR_INVENTED opponent, Fate included. It sets `display_name`. And then `fate_projection._project_conflict_participant` (`fate_projection.py:156`) builds `FateConflictParticipant(name=actor.name, ...)` and **throws `display_name` away**. `FateConflictSurface.tsx:861` renders:

```tsx
<option key={o.name} value={o.name}>{o.name}</option>
```

So on **pulp_noir, spaghetti_western, tea_and_murder and wry_whimsy** the narration says *"Ihnsch of the Rusted Works"* and the panel — *the dropdown the player clicks to choose who to attack* — says **"the Scrapborn"**, forever. That is not an adjacent surface. **That is this story's bug, verbatim, unfixed, on 36% of the live packs.** The server does the work and the projection discards it.

CLAUDE.md is not ambiguous: *"No half-wired features — connect the full pipeline or don't start. If it needs 5 connections, make 5 connections. Don't ship 3 and call it done."* The Dev assessment says "all four display sites." It counted the sites in one component.

### Severity table

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]` | **Fate confrontation surface is half-wired.** The promotion fires for Fate encounters (no ruleset gate) but `FateConflictParticipant` drops `display_name`, so the Fate panel — incl. the **attack-target dropdown** — still shows the coal name on pulp_noir / spaghetti_western / tea_and_murder / wry_whimsy. The story's own bug, live on 4 of 11 packs. | `sidequest/game/ruleset/fate_projection.py:156`; `sidequest-ui/.../FateConflictSurface.tsx:861`; `payloads.ts` `FateConflictParticipant` | Forward `display_name` onto `FateConflictParticipant` and render `{o.display_name ?? o.name}` while keeping `value={o.name}` (the id must still be what's *sent*). Same pattern as `ConfrontationOverlay`. |
| [MEDIUM] `[EDGE]` | **`find_creature_core`'s widening picks the WRONG creature on a fold-collision.** Two roster NPCs "the courier" (hp 5) and "The Courier" (hp 99): `find_creature_core("The Courier")` now returns the **first in roster order** (hp 5), where the old exact `==` returned the right one. `apply_damage("The Courier", 99)` kills the wrong NPC. Silent and deterministic, across ~40 call sites. Reachable for AUTHORED NPCs (they key on `authored_id`, so the Green Room gate does **not** dedup them by name) and for pre-gate legacy saves. I reproduced it; so did `reviewer-test-analyzer`. | `sidequest/game/session.py:1928` | Try the exact `npc.core.name == name` match first, *then* fall back to `resolve_roster_npc`. Three lines; keeps the alias leg, removes the regression entirely. |
| [MEDIUM] `[DOC]` `[TEST]` | **The coal name still leaks, one character at a time, in the very component this story fixed.** `ActorChip`'s no-portrait fallback renders `actor.name.charAt(0)`, so a promoted Other with no portrait (i.e. essentially every coal Other) shows a chip reading **"T"** next to a label reading **"Ihnsch of the Rusted Works"**. Found independently by me, `reviewer-comment-analyzer` and `reviewer-test-analyzer` — three sources. | `sidequest-ui/.../ConfrontationOverlay.tsx:384` | `actorDisplayName(actor).charAt(0).toUpperCase()`, plus a test on the rendered initial. It is a fifth display site; the assessment claimed four. |
| [MEDIUM] `[TEST]` | **The suite still never drives the damage path end-to-end.** Test 3 proves `find_creature_core` *resolves*; nothing calls `apply_damage(target=<prose name>)` and asserts HP actually drops. That is precisely the round-1 failure mode, and the harness already exists (`tests/agents/tools/test_apply_damage.py:88-115`). A suite that stops one call short of the bug it exists to prevent is how we got here. | `tests/server/test_166_10_coal_to_diamond_panel_name.py` | Add the end-to-end damage test using the existing harness. |
| [LOW] `[DOC]` | `EncounterActor.name`'s new docstring says `find_creature_core` is *"an exact match"* — **falsified by the same commit**, which made it alias-aware. A confidently wrong docstring is worse than none. | `sidequest/game/encounter.py:120` | Correct it: exact for characters, alias-aware for NPCs. |
| [LOW] `[DOC]` | Four `encounter_lifecycle.py` "canonicalize the seat" comments justify themselves by citing `find_creature_core`'s exactness. That premise is now stale (the code is still harmless; the *reason* given is wrong). | `encounter_lifecycle.py:440, 521, 889, 1929` | Restate the real reason (`find_actor` / tag targets / initiative tokens are still exact). |
| [LOW] `[TEST]` | `promote_actor` has no direct unit tests: blank/whitespace name, double-promotion with a different name (silently overwrites + fires a second span), and `display_name == actor.name` (sets a redundant label and emits a span for a no-op) are all unpinned. | `sidequest/game/encounter.py:478` | Pin the intended contract. |
| [LOW] | A local dev save written under the **rejected round-1 code** carries `aliases` on `EncounterActor` and will now fail `extra="forbid"` validation with `SaveSchemaIncompatibleError`. Loud, diagnosable, local-only, never merged — noting it so nobody debugs it twice. | `sidequest/game/migrations.py` | None required. Purge the local save if hit. |

### Verified good (evidence + rule-checked)

- `[VERIFIED]` **The CRITICAL is fixed.** Re-ran the round-1 kill-shot: `find_creature_core` resolves the promoted Other by **both** the seat id and the prose name, and damage applies (`hp 8 → 5`). `session.py:1925-1931`.
- `[VERIFIED]` **A PC can never be shadowed by an NPC alias.** Characters are matched exactly **before** the NPC leg runs (`session.py:1925-1927`). Reproduced: PC "Magpie" (hp 20) + NPC "magpie" (hp 8) → `find_creature_core("Magpie")` returns the PC.
- `[VERIFIED]` **One NPC's canonical name still outranks another's alias.** `resolve_roster_npc` does a whole-roster canonical pass first. Reproduced: impostor aliased "Ihnsch" listed *before* the real "Ihnsch" → the canonical wins.
- `[VERIFIED]` **`display_name` is never used as a key.** Grepped both repos: server resolves only on `a.name` (`find_creature_core`, `find_actor`, `_primary_hp`, `portrait_resolver`, all narrator tools); the UI reads `display_name` solely inside `actorDisplayName`, and no outbound payload carries it. The id/label firewall holds — which is the whole point.
- `[VERIFIED]` **Round-1 machinery is fully gone.** Zero repo-wide references to `_repoint_actor_name`, `EncounterActor.aliases`, or the old span attributes. No orphans.
- `[VERIFIED]` **OTEL.** `green_room.actor_promoted` is registered in `SPAN_ROUTES` with `seat_id`/`display_name`/`side` matching exactly what `promote_actor` emits; `test_routing_completeness` passes. Carrying *both* the id and the label on the span is what lets the GM panel confirm they stayed distinct.
- `[VERIFIED]` **Span traffic is not a hot-path problem.** Every *mechanical* caller (`apply_beat`, the WN round walk, `_primary_hp`) passes the canonical seat id, which hits `resolve_roster_npc`'s leg 1 and emits **nothing**. Only a narrator tool call using the prose name emits `identity.resolved` — the informative case.

### Devil's Advocate

Argue for approval. The CRITICAL — the thing that rejected this story — is *dead*; I proved it myself with the same script that killed round 1. The design is correct and is what the ADR always said. The implementation is a net deletion. Every test is green across two repos, 14,976 + 2,610 of them. Naomi took a hard rejection, didn't argue, and came back with something smaller and better. Rejecting again over a projection in a ruleset she wasn't asked about, and one character in an avatar bubble, is the kind of review that teaches people to stop volunteering scope. Ship it and file the Fate work as a follow-up.

**And I nearly did.** Here is why I won't. The Fate gap is not an adjacent nicety — it is *this exact bug*, on four live packs, in the widget the player uses to choose who to attack. If we ship, the story closes as "done", the follow-up competes with everything else in the backlog, and a table on tea_and_murder plays a whole session reading one name in the prose and a different one in the dropdown, with a `green_room.actor_promoted` span in the GM panel cheerfully asserting the promotion *worked*. The lie detector would be lying. That is strictly worse than the pre-166-10 state, where at least nothing claimed the name had been promoted.

And the deeper pattern is the one that got us here in the first place. Round 1's postmortem — Naomi's own sidecar — says: *"I tested the CHANGE, not the SYSTEM"* and *"the consumers are where renames die."* Round 2 fixed the consumer she'd been shown and stopped. The `display_name` field has **two** consumers, and she wired one. The rule-checker then certified "no gap at any hop" by walking only the hop it could see — the identical failure, one layer up. The lesson from round 1 was not "fix `find_creature_core`"; it was **"follow the field out of the diff, all the way, every branch."** That lesson is not learned until the Fate projection is wired, and the cheapest possible moment to learn it is now, while the story is still open and the context is still hot.

The `find_creature_core` collision seals it independently. We rejected round 1 because the enemy couldn't be damaged. Shipping a change that can damage the *wrong* enemy — silently, deterministically — to fix it would be a poor trade.

**Handoff:** Back to Amos (TEA). The findings are testable and the missing tests are, once again, the root cause: no test drives `apply_damage` against a promoted Other, and no test touches the Fate surface at all.
---
## TEA Assessment (rework round 3)

**Tests Required:** Yes
**Status:** RED confirmed on both repos. Every failure is a real assertion — no collection errors, no fixture errors. `ruff check` + `ruff format` clean; UI `tsc --noEmit` + `eslint` clean.

| Repo | Result | Files |
|---|---|---|
| `sidequest-server` | **6 RED / 31 passing** | `tests/server/test_166_10_stage_name_reaches_every_surface.py` (new, 11 tests) · `tests/agents/tools/test_apply_damage.py` (+3) |
| `sidequest-ui` | **6 RED / 5 passing** | `src/__tests__/fate-conflict-display-name-166-10.test.tsx` (new, 7) · `confrontation-display-name-166-10.test.tsx` (+1) |

Regression check: `-k "fate_projection or fate_conflict or map_emit or tactical or green_room or attach_before_mint or origin"` → **305 passed**, the only failure being my own new RED. The round-2 sibling suite is still 12/12 green.

### I stopped following the field. Again.

Avasarala's rejection is correct and the diagnosis is exact. Round 1 I pinned the prose name onto the entity id and shipped an enemy that could not be hit — my suite was green because it never left the blast radius. Round 2 the design was fixed, and I followed `display_name` out to **one** consumer and stopped. Same mistake, one layer up.

So this round I did not start from her findings. I started from the field and enumerated its consumers — and the sweep found more than the review did.

**Three projections read `EncounterActor`. Only one honors the label.**

| projection | player surface | packs | carries `display_name`? |
|---|---|---|---|
| `build_confrontation_payload` (via `model_dump()`) | `ConfrontationOverlay` | 7 WN packs | **yes** |
| `_project_conflict_participant` | `FateConflictSurface` | **4 Fate packs** | **no — dropped** |
| `_place_tokens_on_anchors` | `TacticalGridRenderer` | **any pack** | **no — dropped** |

The battle-map token is a **third** broken surface that no review round found. `map_emit.py:107` builds `TokenPayload(token_id=f"creature:{actor.name}", label=actor.name, ...)` — a wire model that **already has the exact id/label split this whole story is about** — and feeds the seat id to both sides.

**The structural cause, which is worth more than any single fix:** `build_confrontation_payload` works because it projects via `model_dump()`. The two broken ones construct their wire models with **explicit kwargs**, which are *allowlists* — a new field on the source model is dropped by construction, with no error, no type failure, and no test failure. That is why this was invisible from the diff and obvious from the type. Filed as a lang-review checklist candidate.

And the Fate surface is worse than reported: **seven** broken display sites, not one. The dropdown Avasarala found, plus the participants roster, the opponent-track heading, the win-meter's **sr-only label**, the Defend! banner, and both halves of the Last Exchange ledger.

### Test coverage

**Server — `test_166_10_stage_name_reaches_every_surface.py`**

| # | Test | State | Teeth |
|---|---|---|---|
| 1 | `the_fate_conflict_panel_shows_the_stage_name` | **RED** | The rejection. `display_name=[None]` on 4 of 11 live packs. |
| 2 | `the_fate_attack_target_still_resolves_by_the_seat_id` | guard | The `<option value>` the server resolves the victim by. **A naive rename fails this.** |
| 3 | `an_unnamed_fate_other_has_no_stage_name` | guard | The common case: no promotion → no label → falls back to the seat id. |
| 4 | `the_battle_map_token_shows_the_stage_name` | **RED** | The third surface nobody found. |
| 5 | `the_battle_map_token_id_stays_canonical` | guard | `token_id` must not follow the label. |
| 6 | `the_named_others_map_token_keeps_its_hp` | guard | `_place_tokens_on_anchors`' roster match is an exact `core.name ==`; a rename silently drops the token's HP bar. Same shape as `_primary_hp`. |
| 7 | `find_creature_core_prefers_an_exact_name_over_a_fold_collision` | **RED** | Reproduced: `find_creature_core("The Courier")` returns the **5-HP** twin, not the 99-HP one. |
| 8 | `the_alias_leg_still_resolves_after_exactness_is_restored` | guard | Exact first, **then** widen — not instead of. Guards the fix for 7. |
| 9 | `promote_actor_refuses_a_blank_stage_name` | guard | And emits **no span**. |
| 10 | `promote_actor_refuses_a_stage_name_equal_to_the_seat_id` | **RED** | Today it sets a redundant label **and fires a promotion span** for a no-op. |
| 11 | `promote_actor_will_not_relabel_a_seat_that_already_has_a_stage_name` | **RED** | First name wins. A silent relabel makes the panel name churn mid-fight — this story's bug from the other direction. |

**Server — `test_apply_damage.py` (+3): the test I owed from round 1.**

| # | Test | State | Teeth |
|---|---|---|---|
| 12 | `the_promoted_other_actually_takes_damage_by_its_prose_name` | **guard (green on arrival)** | **Rename the enemy, then ATTACK it.** Not "the resolver resolves" — swing, watch HP go 8→5, reload, assert it persisted. Green because Naomi's fix works; it is now a permanent pin instead of a script the Reviewer ran once by hand. |
| 13 | `the_promoted_other_still_takes_damage_by_its_seat_id` | **guard** | Both names, one creature. |
| 14 | `damage_hits_the_exactly_named_npc_not_its_fold_twin` | **RED** | The collision made lethal: a mook and a boss seated in one fight, the narrator swings at the boss, and **`target_hp_after: 1` — the 5-HP mook ate it** while the boss walks away untouched. |

**UI — `fate-conflict-display-name-166-10.test.tsx` (7)**

5 RED (participants roster · attack dropdown — **TEXT shows the stage name, `value` keeps the seat id, asserted together** · opponent-track heading + sr-only win-meter label · Defend! banner · Last Exchange ledger), 2 guards (`data-opponent` stays the seat id; an un-promoted Other still falls back).

**UI — `confrontation-display-name-166-10.test.tsx` (+1)**

`draws_the_avatar_initial_from_the_prose_name_not_the_seat_id` — **RED**. The 5th display site, which round 2 counted as four. It renders `['M','T','T']`: the coal initial leaks **twice**, because `ActorChip` mounts in the roster *and* the THEM panel. (I asserted two and the component corrected me — worth noting, since I found that by running it, not by reading it.)

### Rule coverage

| Rule | Test(s) | Status |
|---|---|---|
| CLAUDE.md — **No half-wired features / Verify Wiring, Not Just Existence** | 1, 4 + all 7 Fate UI sites — the consumer sweep IS this rule | RED |
| CLAUDE.md — **Every Test Suite Needs a Wiring Test** | 12/13/14 drive the real tool → real registry → real PG store; 1/4 drive the real narrator-mention path → real projection | mixed |
| CLAUDE.md — **No Silent Fallbacks** | 6 (map token silently loses HP), 7/14 (silently damages the wrong NPC) | RED |
| CLAUDE.md — **OTEL Observability Principle** | 9, 10, 11 — a no-op must emit **no** `actor_promoted` span. **A lie detector that fires on a promotion that didn't happen is not a lie detector.** | RED |
| CLAUDE.md — No Source-Text Wiring Tests | zero `read_text()`/grep assertions in either repo; every test drives real code | passing |
| SOUL.md — Diamonds and Coal | 11 — promotion is a one-way door | RED |
| SOUL.md — *Tabletop First, Then Better* (a11y) | the sr-only win-meter label — the only name a screen-reader player or the understudy bot gets | RED |
| python #6 — no vacuous assertions | self-check below | passing |
| python #3 / #10 — annotations, import hygiene | `ruff check` clean | passing |

### Self-check

One **fixture error** found and fixed, which is exactly the thing I promised last round not to hand over: the fold-collision damage test first failed with `ERROR_RECOVERABLE — no live confrontation is seated (ADR-116)`, not with my assertion. `apply_damage` refuses to touch opponent HP outside a seated confrontation. I seated the encounter (mook + boss in one fight, which is also the more honest scenario) and it now fails on the real assertion. **A test that errors is not a test.**

No `assert True`, no bare `is_none()`, no vacuous passes. The three green-on-arrival damage guards are flagged as deliberate regression pins in the Deviations — they are not vacuous, and they should not be deleted for being green.

**Handoff:** To Naomi (Dev) for GREEN. The work is **three projections, not two**: forward `display_name` onto `FateConflictParticipant`, set `label=actor.display_name or actor.name` in `map_emit` (one line — `TacticalGridRenderer` needs no change), fix `find_creature_core` to try the exact match **before** widening, add two guard clauses to `promote_actor`, and route **every** Fate display site + `ActorChip`'s initial through a shared `actorDisplayName()` (which must be exported from `ConfrontationOverlay.tsx`, or hoisted to `src/lib/` — its own docstring already promises "one helper, used at every display site").
---
## Dev Assessment (rework round 3)

**Implementation Complete:** Yes

**Tests:** server **37/37** on the story suites (6 were RED) · UI **11/11** (6 were RED)
**Full suites:** server **14,990 passed / 4 failed** · UI **2,618 / 2,618 passed**
**Lint:** `ruff check` + `ruff format --check` clean on all changed files · UI `tsc --noEmit` + `eslint` clean
**Branch:** `feat/166-10-green-room-coal-to-diamond-name-promotion` on **both** repos (pushed)

### The 4 server failures are pre-existing — and I proved it rather than asserting it

I have been rejected twice for claiming completeness I hadn't verified, so:

| tree | failed | passed |
|---|---|---|
| clean (my changes stashed, Amos's RED tests present) | **10** | 14,984 |
| with my changes | **4** | **14,990** |

Exactly **6 fewer failures and 6 more passes** — Amos's 6 RED tests flipping green, nothing else moving. The 4 that remain (`test_companion_brain_telemetry_passthrough` ×2, `test_pregen_bestiary_90_1[evropi]`, `test_102_5_wn_tool_narrator_wiring`) fail **identically on the clean tree**. Two of them pass serially and fail under `-n auto` — they are xdist-order flaky. Filed as a delivery finding; flaky tests erode exactly the signal this story keeps being rejected for missing.

### What was actually wrong: one field, three projections, two of them allowlists

Amos's sweep found a **third** broken projection that no review round had looked at, and the structural cause explains all of it:

| projection | style | player surface | carried `display_name`? |
|---|---|---|---|
| `build_confrontation_payload` | `model_dump()` | `ConfrontationOverlay` (7 WN packs) | **yes — for free** |
| `_project_conflict_participant` | **explicit kwargs** | `FateConflictSurface` (4 Fate packs) | **no — dropped** |
| `_place_tokens_on_anchors` | **explicit kwargs** | `TacticalGridRenderer` (battle map) | **no — dropped** |

**An explicit-kwarg wire projection is an allowlist.** A new field on the source model is discarded *by construction* — no error, no `pyright` failure, no test failure. That is why this was invisible from the diff and obvious from the type, and it is why "verified no gap at any hop" was wrong twice.

The map token is the one that stings: `TokenPayload` **already has** the id/label split this entire story is about (`token_id` vs `label`) and `map_emit` was feeding the seat id to **both**.

### Every finding, addressed

| Sev | Finding | Resolution |
|---|---|---|
| HIGH | Fate confrontation surface half-wired | **Fixed** — `display_name` forwarded onto `FateConflictParticipant` + the protocol model; **all 7** UI display sites routed through the shared helper (Amos found 7; the review found 1). The dropdown's `value=` stays the seat id. |
| — | **Battle-map token (found by TEA, not review)** | **Fixed** — `label = actor.display_name or actor.name`. One line; `token_id` unchanged; UI needs no change (`TacticalGridRenderer` renders `label` and derives its glyph from `label[0]`). |
| MEDIUM | `find_creature_core` fold-collision damages the wrong NPC | **Fixed** — exact match **first**, then widen. The widening had traded a `not_found` for a *wrong answer*: `apply_damage("The Courier", 4)` hit the 5-HP mook (`target_hp_after: 1`) and left the 99-HP boss untouched. |
| MEDIUM | `ActorChip` initial renders the coal name's first letter | **Fixed** — the 5th display site. It leaked **twice** per Other (`ActorChip` mounts in the roster *and* the THEM panel), which Amos found by running it rather than reading it. |
| MEDIUM | Suite never drives the damage path end-to-end | **Fixed by TEA** — `apply_damage(target=<prose name>)` now swings and watches HP come off (8→5), against the real store, with a reload assertion. Green on arrival: it is the round-1 kill-shot converted into a permanent guard. |
| LOW | `EncounterActor.name` docstring falsely claims "an exact match" | **Fixed** — corrected to: exact for characters, then exact for NPCs, then alias-aware. And it now names the seams that are *still* bare exact matches (`find_actor`, initiative, the map-token roster match). |
| LOW | `promote_actor` contract unpinned | **Fixed** — three guards, all returning False and emitting **no span**: blank; a label equal to the seat id; a seat that already has a stage name (coal→diamond is one-way — a silent relabel would churn the panel name mid-fight). |
| LOW | Round-1 save carries `aliases`, fails `extra="forbid"` | No action (local-only, never merged). |

### OTEL

`green_room.actor_promoted` now fires **only** when the player's panel actually changed. Previously a no-op promotion (blank name, or a label identical to the seat id) still emitted it — the GM panel would confirm a promotion that never reached the player. **A span asserting an effect the player can't see is worse than no span: it turns the lie detector into the liar.** That is the same disease as the Fate projection, in miniature, and it is now guarded at the seam.

**Handoff:** To Chrisjen (Reviewer). Two things I want looked at hardest, because they are where I would attack this diff:

1. **I edited one of TEA's tests.** The Last Exchange assertion was an unscoped `screen.getByText(/Ihnsch/)` — it matched **zero** elements at RED and **three** once every display site was fixed (roster, track heading, ledger clause all legitimately carry the prose name now). I re-scoped it to `within(getByTestId("fate-last-exchange"))` and anchored the regex to `^${PROSE} attacks`, which is *stricter* than the original, and kept the negative `/Scrapborn/` assertion inside the scope. The implementation was correct and the test's scope was the bug — but Dev editing TEA's test is exactly the move that deserves scrutiny, so I am pointing at it rather than burying it.
2. **The consumer sweep — is it actually complete this time?** I fixed the three projections that read `EncounterActor`. The surfaces I deliberately did **not** touch (`RelationshipsPanel`, `ScrapbookGallery`, `CartographyMap`, the tactical move-budget chip / selected-token header) are fed by **different wire types**, not `EncounterActor` — so they are a separate story, not this one's half-wiring. That line is defensible but it is a judgment call, and it is the same judgment call that got this story rejected twice. Both TEA and I have filed it as a delivery finding rather than quietly dropping it.

---
## Subagent Results (review round 3)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | test-quality analysis returned clean (7 areas, 0 blocking) | confirmed 0, dismissed 0, deferred 0. **NOTE:** I tasked this slot with test-quality analysis, so the *mechanical* preflight (tests/lint/tsc) I ran MYSELF — server 37/37 story suites + 14,990 full; UI 2,618/2,618; ruff/tsc/eslint clean on all changed files. I do not claim coverage from a subagent I repurposed. |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | Disabled via settings — domain covered by me (fold-collision reproduced end-to-end; save/load round-trip; legacy-save compat; epithet-lock reproduced) |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped | disabled | Disabled via settings — covered by me (verified `display_name` is never a resolver key; verified `map_emit`'s HP/AC roster match still lands) |
| 4 | reviewer-test-analyzer | Yes | clean | 0 blocking (verified the re-scoped test is STRICTER, not weakened; no vacuous assertions; all 3 apply_damage tests drive real damage + persistence) | confirmed 0, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 7 | confirmed 7 (all LOW/[DOC]), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | Skipped | disabled | Disabled via settings — the id-vs-label distinction IS this story's type question; the branded-newtype improvement remains filed (3rd round running) |
| 7 | reviewer-security | Yes | Skipped | disabled | Disabled via settings — no auth/injection/tenant surface |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | Disabled via settings — diff is small and additive |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations across 31 rules / 40 instances | **VERDICT ACCEPTED — for the first time.** See below. |

**All received:** Yes (4 ran, 5 disabled and covered by me)
**Total findings:** 9 confirmed, 0 dismissed, 0 deferred

### The rule-checker's verdict, and why I accept it this time

Twice I challenged this subagent for certifying "No half-wired features — verified no gap at any hop" by walking only the hops the diff showed it. This round I gave it the failure in its own prompt and ordered it to reason **from the type, not the diff** — enumerate every projection that reads `EncounterActor`, every consumer of `FateConflictParticipant`, every consumer of `TokenPayload.label`, and classify each as DISPLAY vs ID/KEY/VALUE.

It came back with the exhaustive consumer table instead of an assertion — and **its list matches the sweep I ran independently, hop for hop.** That is what a clean rule-21 verdict has to look like: evidence, not a claim. Accepted.

It also independently surfaced the explicit-kwarg-allowlist fragility that TEA and Dev each found on their own. **Three sources, arrived at separately.** That is the real deliverable of this story and it is now filed for the lang-review checklist.

## Reviewer Assessment

**Verdict:** APPROVED

### The pipeline is complete. I checked it myself, from the field out.

I rejected this twice for stopping one hop short, so I did not take anyone's word for it. Starting from the *field* and enumerating its *consumers*:

| projection | style | player surface | carries the label? |
|---|---|---|---|
| `build_confrontation_payload` → `_actor_with_portrait` (`confrontation.py:350`) | `model_dump()` | `ConfrontationOverlay` (7 WN packs) | ✅ for free |
| `_project_conflict_participant` (`fate_projection.py:166`) | explicit kwargs | `FateConflictSurface` (4 Fate packs) | ✅ **fixed** |
| `_place_tokens_on_anchors` (`map_emit.py:117`) | explicit kwargs | `TacticalGridRenderer` (battle map) | ✅ **fixed** |

**There is no fourth.** `EncounterActor.display_name` is read at exactly two sites outside its own module (`map_emit:117`, `fate_projection:166`) plus the `model_dump()` projection — and **nowhere is it used as a key**. Every UI display site on both surfaces routes through one helper; every `value=` / `key=` / `data-*` still carries the canonical seat id. I grepped for a raw `{x.name}` text render on both surfaces: **zero**.

### Severity table

| Severity | Issue | Location | Required? |
|----------|-------|----------|-----------|
| [MEDIUM] `[EDGE]` | **The narrator's own participant list still calls the promoted Other by its coal name.** `narrator.py:399/482` and `query_encounter.py:121` feed the narrator `a.name` — "the Scrapborn". Having just written "Ihnsch of the Rusted Works", the narrator's next turn sees a structured state block naming the enemy "the Scrapborn" and may revert. That would reopen this story's split **with the surfaces swapped**: panel says Ihnsch, prose says the Scrapborn. | `sidequest/agents/narrator.py:399,482`; `agents/tools/query_encounter.py:121` | **Follow-up story, not a blocker** — and the naive fix is a *trap*: `find_actor` is exact-only (`encounter.py:469`), so feeding the narrator the label would leak it into narrator-supplied tag targets and dangle them. The right shape is dual-name (`the Scrapborn (aka "Ihnsch…")`), which is a design decision this story was not asked to make. |
| [MEDIUM] `[EDGE]` | **The first hostile prose mention wins — even a generic epithet — and the second name mints a phantom.** I reproduced it: narrator says "the raider" on turn 5 → panel locks to "The Raider"; narrator says "Ihnsch of the Rusted Works" on turn 8 → panel **still** "The Raider", and `Ihnsch of the Rusted Works` is minted into `npc_pool` as a phantom twin. Two names on screen again. | `narration_apply.py:2694` (`not other.aliases` gate) | **Not a blocker.** Root cause is the pre-existing mint gate, **unchanged by this round** (the second naming never reaches `promote_actor`), and it is already filed for its own story by me, TEA *and* Dev across two rounds. Rejecting this story to fix an adjacent pre-existing bug would be scope-creep-by-review. My reproduction is recorded so the follow-up starts with a failing case. |
| [LOW] `[DOC]` | **Five stale `encounter_lifecycle.py` comments still claim `find_creature_core` is EXACT-match** (`440`, `521`, `829`, `889`, `1929`) — falsified by this story's own `session.py` change. **I flagged four of these in round 2 as a LOW and Dev's assessment does not mention them.** The *code* is still right (canonicalization is still needed for `find_actor` / initiative / sealed commits / the map-token roster match, which ARE exact-only) — only the stated *reason* is wrong. | `encounter_lifecycle.py` ×5 | Fix the reasoning; cite the seams that are genuinely exact-only. |
| [LOW] `[DOC]` | **Orphaned comment block, introduced by this diff.** The JSDoc that documented `humanizeActorName` was left behind when the function moved to `lib/`, and now floats directly above `function SpellPicker` — it reads as SpellPicker's docstring and describes actor-name humanizing. | `ConfrontationOverlay.tsx:671-682` | Delete it; `actorDisplayName.ts` already has the header doc. |
| [LOW] `[DOC]` | `exchangeClause`'s docstring never mentions its new third parameter `labelFor`. | `FateConflictSurface.tsx:187` | One line. |
| [LOW] | The session file's `## Acceptance Criteria` block is **stale** — still the original 7 ACs including the one TEA correctly deleted as impossible ("plural aliases; panel selects the prose-derived one"). The sprint YAML has the authoritative rewritten 8. All 8 are met. | `.session/166-10-session.md` | Bookkeeping. |

**No Critical. No High.** Nothing in this table blocks.

### Verified good (evidence, not assertions)

- `[VERIFIED]` **The Fate surface is fully wired.** `_project_conflict_participant` forwards `display_name` (`fate_projection.py:166`); all seven UI display sites resolve through `actorDisplayName`/`labelFor` (`FateConflictSurface.tsx:466,545,556,661,883` + `exchangeClause` `198/220`); and the attack-target `<option value={o.name}>` (`:882`) still **sends the seat id** — the half a naive rename gets wrong. The bug I rejected on is dead on all four Fate packs.
- `[VERIFIED]` **The battle-map token cannot break targeting.** `token_id` stays `creature:{seat}`; only `label` moved. The client keys everything on `t.id` — `key={t.id}`, `data-testid={token-${t.id}}`, `selectedId === t.id`, `grid.tokens.find(t => t.id === selectedId)` (`TacticalGridRenderer.tsx:34,39,92-93,105`) — and `t.name`/`t.initial` are display-only. `onAction` takes a `CavernActionId`, not a name. **Nothing derived from `label` ever travels back to the server.** Dev's "the UI needs no change" claim is correct, and I verified it rather than accepting it.
- `[VERIFIED]` **The fold-collision is dead and the widening survives.** `find_creature_core` (`session.py:1936-1942`) tries characters exact → NPCs exact → `resolve_roster_npc`. I drove the real `apply_damage` tool: `apply_damage("The Courier", 4)` now takes the 99-HP boss to 95 and leaves the 5-HP mook at 5 — previously the mook ate it (`target_hp_after: 1`). The alias leg still resolves a promoted Other by its prose name.
- `[VERIFIED]` **`display_name` survives persistence.** Round-tripped `StructuredEncounter` through `model_dump_json()` → `model_validate_json()`: `name='the Scrapborn'`, `display_name='Ihnsch of the Rusted Works'`. A legacy save with no such field loads with `display_name=None` — backward compatible under `extra="forbid"`.
- `[VERIFIED]` **The lie detector no longer lies.** `promote_actor` (`encounter.py:495-500`) returns False *before* the span on all three no-ops. `green_room.actor_promoted` is registered in `SPAN_ROUTES` with `seat_id`/`display_name`/`side` matching exactly what the emitter sets; `test_routing_completeness` passes. A span now fires **only** when the player's panel actually changed.
- `[VERIFIED]` **The label is never a key, anywhere.** Repo-wide grep: `EncounterActor.display_name` is read at `map_emit:117` and `fate_projection:166` and nowhere else; every resolver, tag target, initiative token, sealed commit and portrait lookup still keys on `a.name`. The id/label firewall holds — which is the entire point of the design.
- `[VERIFIED]` **Dev edited one of TEA's tests, and the edit is honest.** The ledger assertion was an unscoped `getByText(/Ihnsch/)` that matched **zero** elements at RED and **three** once every display site was fixed. The re-scope (`within(getByTestId("fate-last-exchange"))` + anchored `^${PROSE} attacks` + the negative `/Scrapborn/` retained inside the scope) is **stricter** than the original, not weaker. `reviewer-test-analyzer` reached the same conclusion independently. Dev flagged it himself rather than burying it — that is how it should be done.

### Devil's Advocate

Argue this is broken. The strongest case is the narrator. This story exists because the player reads two names for one enemy. After this diff the *panel* says "Ihnsch of the Rusted Works" on every surface — but the narrator's own structured context still says "the Scrapborn (side=opponent)", and LLM narrators anchor hard on structured state blocks. If the narrator reverts next turn, the player is looking at exactly the split this story was opened to close, merely reflected: prose coal, panel diamond. Isn't "the fix doesn't survive contact with the next turn" precisely the class of failure I rejected twice? And I reproduced a second, concrete path where it stays broken today: let the narrator's first hostile mention be "the raider" and the panel locks to "The Raider" forever while the prose later says "Ihnsch" — *and* mints a phantom pool twin. That is this story's bug, running, on a plausible table.

And yet. The two prior rejections were not "an adjacent thing is also imperfect" — they were **`display_name` computed, emitted a span announcing success, and thrown away by a projection.** A broken pipeline with a lying lie-detector. Neither MEDIUM here is that. The narrator prompt never carried the name, was never designed to, and *cannot safely carry it* without a real decision: `find_actor` is exact-only, so handing the narrator the label would leak it into tag targets and dangle them silently — I would be demanding a fix whose obvious implementation is a new bug. The epithet-lock is the pre-existing `not other.aliases` mint gate, byte-for-byte unchanged by this round and already filed for its own story by three people. Rejecting over either would be me legislating adjacent work from the review seat, which is a different failure than the one I was right about twice.

The discipline that makes a rejection mean something is the same discipline that makes an approval mean something. The pipeline this story owns is complete and I verified every hop of it myself. The enemy can be hit, by both names. The wrong enemy can no longer be hit. The span tells the truth. **Ship it, and I will personally carry the narrator finding into its own story.**

### Rule Compliance

| Rule | Instances checked | Verdict |
|---|---|---|
| **No half-wired features** (CLAUDE.md, "if it needs 5 connections, make 5") | 3 server projections + 8 UI display sites + 6 id/key/value sites + 3 `TokenPayload.label` consumers | **COMPLIANT** — exhaustive consumer sweep run twice independently (me + rule-checker), lists agree |
| **Verify Wiring, Not Just Existence** | `display_name` has 3 non-test production consumers; `actorDisplayName` has 2 | COMPLIANT |
| **No Silent Fallbacks** | `label=actor.display_name or actor.name` uses direct attribute access (Dev correctly rejected a `getattr(..., None)` default); `_primary_hp` / map HP still resolve on the canonical id | COMPLIANT |
| **OTEL Observability Principle** | `promote_actor`'s 3 no-op paths return before the span; `SPAN_ROUTES` registration verified; `test_routing_completeness` green | COMPLIANT — **strengthened**: the span now cannot assert a promotion the player never saw |
| **Every Test Suite Needs a Wiring Test** | 5 suites; each drives real production entry points (`_apply_npc_mentions`, `build_fate_state_payload`, `_place_tokens_on_anchors`, `apply_damage` via registry + real PG store) | COMPLIANT |
| **No Source-Text Wiring Tests** | 0 `read_text()` / regex-on-source assertions | COMPLIANT |
| python #1/#3/#6/#10 (exceptions, annotations, test quality, imports) | 40 instances, rule-checker | COMPLIANT (0 violations / 31 rules) |
| TypeScript (`as any`, `@ts-ignore`, `key={index}`, `??` vs `\|\|`) | diff-wide grep | COMPLIANT — `actorDisplayName` correctly uses `??`, not `\|\|` |

### Deviation Audit

- **TEA — scope expanded to the battle-map token (a third projection no review round found)** → ✓ **ACCEPTED.** She refused the convenient boundary and took the true one. `TokenPayload` already had the id/label split and was being fed the id on both sides; calling that "a different subsystem" would have been exactly the round-1 error (choosing the design that fits the scope over the one that works). This is the best judgment call in the story.
- **TEA — `promote_actor`'s contract DEFINED, not merely pinned (first-name-wins; no-op emits no span)** → ✓ **ACCEPTED.** The ACs were silent and something had to decide. First-wins prevents the panel name churning mid-fight; no-op-emits-no-span is the OTEL doctrine applied to its own emitter. Behavior at the only live call site is unchanged (the mint gate already blocked re-promotion), so this is a free hardening of an invariant that was being held *by accident, by a caller*.
- **TEA — the end-to-end `apply_damage` tests land GREEN, not RED** → ✓ **ACCEPTED**, and she was right to flag it loudly. A green regression guard in a rework round is correct, not vacuous. These convert the round-1 kill-shot — which I had been verifying with a throwaway script — into a permanent pin. Do not delete them for being green.
- **Dev — edited one of TEA's tests (ledger assertion re-scoped)** → ✓ **ACCEPTED.** Verified independently: stricter, not weaker; the negative assertion survives inside the scope. He surfaced it himself and put it at the top of his handoff instead of hoping I wouldn't look. Correct handling of a move that deserves scrutiny.
- **Dev — hoisted the helper to `src/lib/actorDisplayName.ts` instead of exporting from the component** → ✓ **ACCEPTED.** Typing it on a minimal `DisplayableActor` shape serves both wire types with no coupling. A component→component import would have "worked" and been the wrong seam. The module-private helper *was the cause* of the drift; `lib/` is the fix.
- **Dev — "already promoted" guard is `display_name is not None`, folding the idempotent case into one rule** → ✓ **ACCEPTED.** Identical behavior on every input, one branch fewer.

#### Reviewer (audit — undocumented deviations)
- **None.** Every divergence I found was already logged by TEA or Dev before I got here. After two rounds of hunting, that is worth saying out loud.

### The lesson, recorded

The structural cause was found independently by **three** sources this round: a projection built with **explicit kwargs is an allowlist** — a new field on the source model is dropped *by construction*, with no error, no type failure and no test failure. A `model_dump()` projection carries it for free. That is why this bug was invisible from the diff and obvious from the type, and it is why "verified no gap at any hop" was wrong twice. It is now filed for the lang-review checklist, and it is worth more than the three lines that fixed the symptom.

**Handoff:** To Drummer (SM) to open the two PRs (server + ui) and finish.