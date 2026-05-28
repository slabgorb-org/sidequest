---
id: 105
title: "Broadcast-Layer Perception Firewall — Completing ADR-104 in the MP Fan-Out"
status: accepted
date: 2026-05-16
deciders: ["Keith Avery", "Major Margaret Houlihan (Architect)", "oq-1/SM (scope)"]
supersedes: []
superseded-by: null
related: [28, 36, 67, 101, 102, 104]
depends_on: [101, 104]
tags: [multiplayer, agent-system]
implementation-status: partial
implementation-pointer: 101
load_bearing: true
---

# ADR-105: Broadcast-Layer Perception Firewall — Completing ADR-104 in the MP Fan-Out

## Status

**Accepted.** Scope ratified in the tandem playtest coordination record
(`sq-playtest-pingpong.md`, HIGH bug entry, 2026-05-16): one Sprint-3
story, two tracks. ADR-104 stays `accepted` but its
`implementation-pointer` flips to this ADR — ADR-104's tool-layer
decision is correct and live; its broadcast-layer half was never built
and is completed here.

## Context

ADR-104 ("Perception Filtering at the **Tool Layer**") is correctly
scoped and live for what it covers: `NarratorPerceptionFilter`
(`sidequest/agents/narrator_perception_filter.py`) filters every
read-category tool result against a single `perspective_pc` before the
model sees it, so a *solo* narration is perception-correct at
generation time.

It has one structural blind spot. **Merged multiplayer dispatch has no
single `perspective_pc`.** When two PCs submit on the same turn, the
SDK narrator (ADR-101, made default by #293) composes one shared
narration covering both PCs. There is no single perspective the
tool-layer filter can be correct for, so the tool-layer firewall —
correct as designed — structurally cannot cover the merged-MP turn.
ADR-104 explicitly deferred the broadcast-layer half ("the MP fan-out
filter retains its targeted scope: status-effect override of fidelity
on broadcast") and the visibility classifier left an explicit,
never-done deferral (`visibility_classifier.py:136-138`).

The 2026-05-16 `caverns_sunden` playtest confirmed the breach with
verbatim Jaeger + UI evidence (traces `b72a0f80…`, `3a2524f5…`,
`2d84bd32…`, `efcdf315…`, `faeae95c…` — deterministic 5/5 turns).
Willes (Mage) declared *"push my arcane senses through the bars… I keep
the reading to myself for now."* Narder (Fighter, no arcane sense,
facing away) received Willes's **private arcane-probe result verbatim**
on his tab. Severity HIGH — but framed precisely (per the audience
rubric in CLAUDE.md and the oq-1/SM nuance): Keith's playgroup is
co-located and collaborative (ADR-036 doctrine), so casual-session
card-leak severity is *lower* than it sounds. The leak is genuinely
**severe for the asymmetric-perception use-cases the system explicitly
exists to support** — SOUL "Cost Scales with Drama": a charmed player
perceiving a false reality, a traitor with secret objectives, a blind
character navigating by sound. Frame severity on those, not on casual
co-located play.

### Root cause — verified by code read, with two corrections to the shared diagnosis

The investigation in the coordination record is symptom-solid and
Jaeger-proven. Two of its code-level sub-claims are **imprecise**, and
this ADR records the correction loudly (CLAUDE.md "No Silent
Fallbacks"; getting the next dev to fix the right line matters more
than preserving the original framing):

**Correction 1 — there is no live "passthrough stub" to kill.** The
shared diagnosis says `game/projection_filter.py:13-20`'s `project()`
is the live passthrough stub and should be deleted. It is **not on the
live broadcast path**. The live filter is `ComposedFilter`
(`game/projection/composed.py`), bound at `handlers/connect.py:803` and
`:808`. `PassThroughFilter` in `projection_filter.py` is the documented
"no genre rules configured" fallback used by tests and
`ComposedFilter.with_no_genre_rules()` — **deleting it would be wrong.**
`ComposedFilter.project()` (composed.py:42) *does* emit the
`projection.filter.decide` span (composed.py:49 →
`telemetry/spans/projection.py:50`, opened via the generic
`sidequest-server` span infra — which is why oq-1's Jaeger scope read
showed `otel.scope.name: sidequest-server`), and it delegates to
`GenreRuleStage`, which **already honors `_visibility.visible_to`**
(`game/projection/genre_stage.py:86-96`) via `VisibilityTagRule`. The
playtest pack already wires it: `caverns_and_claudes/projection.yaml`
configures `NARRATION: visibility_tag: {}` and
`SECRET_NOTE: visibility_tag: {}`.

The consequence of Correction 1 is **good news that shrinks Track B**:
per-recipient `visible_to` *enforcement* is already built and wired.
The only reason it never fires is that nothing ever produces a
non-`"all"` `visible_to`. `classify_narration_visibility`
(`visibility_classifier.py:138`) hardcodes `"visible_to": "all"`, and
the `VisibilityTagRule` exclusion branch is `if visible_to != "all"
and …` — so the firewall pipe is fully plumbed and **the valve is
welded open at the source**. Track B is a *derivation* problem, not an
*enforcement* problem.

**Correction 2 — the SECRET_NOTE per-PC channel (which Track B reuses)
is itself broken by a key mismatch.** `CoreInvariantStage`
(`game/projection/invariants.py:27-32`) lists `"SECRET_NOTE": "to"` in
`TARGETED_KINDS` and reads `payload.get("to")`. But `SecretNotePayload`
(`protocol/messages.py`) has **no `to` field** — it carries
`visibility_sidecar` / `_visibility.visible_to`, and
`build_secret_note_events` (`server/session_helpers.py:82-91`) sets
`_visibility.visible_to` and no top-level `to`. So for every non-GM
player the targeted invariant resolves `to_value = None`, returns
**terminal `include=False`**, and SECRET_NOTE never reaches the
`GenreRuleStage` `VisibilityTagRule` that `SecretNotePayload`'s own
docstring claims delivers it. **The per-PC SECRET_NOTE channel
currently delivers to GM only.** Track B's reuse of this channel is
blocked until this mismatch is resolved.

### The four defects

| # | Defect | Locus | Track |
|---|--------|-------|-------|
| D1 | `visible_to` is never derived — hardcoded `"all"` | `visibility_classifier.py:138` | B |
| D2 | SECRET_NOTE recipient match reads `to` (absent) not `_visibility.visible_to` → channel dead for players | `invariants.py:27-32,92-104` | B |
| D3 | Private content baked into the **shared** NARRATION `text`; no layer redacts prose (`rewrite_for_recipient` strips `spans` only; `_apply_pov_swap` swaps POV only) | SDK-narrator output contract (ADR-101/102) | B |
| D4 | Single `anchor_pc` POV + rotated-emitter authorship: `emitter_player_id = handler._session_data.player_id` (`emitters.py:214`) reads the **rotated** shared session PC (hazard `websocket_session_handler.py:3282`), collapsing `recipients` and the emitter-path swap (`:321`/`:341`) to one stuck PC | `emitters.py:214/321/341`; `visibility_classifier.py:133` | A |

D4's emitter-authorship half is the exact, Jaeger-verified cause of the
`×2 first-submitter / ×0 second-submitter` `projection.filter.decide`
pattern and the POV decoupling (T13: `perception_rewrite viewer=Narder`
while `second_person_swap target=Willes`). It is mechanically
verifiable and is **Track A**.

## Decision

Complete the broadcast-layer firewall ADR-104 deferred, in two tracks
under one Sprint-3 story. Track A is a targeted structural correctness
fix (verifiable via existing spans). Track B is the design-bearing
content firewall.

### Track A — Per-row emitter authorship

`emit_event()` must receive the **true author of the row being
emitted**, not read the rotated shared `handler._session_data.player_id`
at `emitters.py:214`. Thread the per-row author explicitly through
`emit_event()` (and the emitter-path POV swap at `:321`/`:341`). This
restores exactly one `projection.filter.decide` + `perception_rewrite`
+ `second_person_swap` per **distinct** recipient, with the swap target
bound to that recipient. No new abstraction — the author is already
known at each emit call site (the dispatched PC for NARRATION; the
acting PC for SECRET_NOTE). This is a correctness fix at the root line,
not a band-aid: it is independently provable through the existing
polygraph spans, satisfying the CLAUDE.md OTEL principle.

### Track B — The content firewall

**B1 — Secret routing is a CoreInvariant, not a genre rule.** Per
`invariants.py`'s own charter ("structural guarantees genre packs
cannot weaken"), a security boundary must not depend on a pack
remembering to add `visibility_tag` to its `projection.yaml` (a missing
rule today *silently* passes the secret through — a No-Silent-Fallbacks
violation). The targeted-recipient invariant is extended so that for
kinds carrying `_visibility.visible_to` (SECRET_NOTE, and the per-PC
NARRATION segment channel from B3), the recipient match reads
`_visibility.visible_to` (resolving D2). `VisibilityTagRule` in
`GenreRuleStage` remains for *fidelity* shaping; the *exclusion*
decision becomes structural. Genre packs may tighten, never weaken.

**B2 — `classify_narration_visibility` derives real `visible_to`.** It
already receives `connected_player_ids`. It additionally reads the
narrator's structured private-routing signal —
`result.secret_routes` (the `redact_dispatch_package` `removed` list;
each a `SubsystemDispatch` with `.visibility.visible_to: list[str] |
"all"` and `.redact_from_narrator_canonical=True`), mirroring the
existing `session_helpers.aggregate_visibility` union logic. The shared
NARRATION's `visible_to` becomes the set of players who may see the
**public-safe** prose (all connected, minus no one — see B3: the
shared blob is public-safe by contract). Each private route yields a
per-PC channel entry whose `visible_to` is that route's recipients.
The hardcoded `"all"` (D1) is removed.

**B3 — SDK-narrator output contract: the shared NARRATION `text` is
public-safe.** This is the load-bearing architectural decision and the
durable half. ADR-101/102's narrator output contract is amended:
`NarrationPayload.text` MUST contain only prose observable by **every**
PC present (the public scene). Any PC-private perception —
the withheld arcane probe, the traitor's secret briefing, the blind
PC's sound-only read — MUST NOT be composed into the shared `text`. It
travels the **per-PC channel**:

- structured subsystem results already flagged
  `redact_from_narrator_canonical` → emitted as `SECRET_NOTE` to that
  PC's `visible_to` (existing mechanism, unblocked by B1);
- PC-private *prose* → a new structured, repeated field on the
  narration payload: per-PC narration **segments**, each carrying its
  own `text`, `visible_to` (single PC + GM), and `anchor_pc`. Public
  `text` + zero or more private segments. The segment field is
  additive; legacy/atmospheric turns carry zero segments and are
  unchanged.

You cannot un-bake a sentence: post-hoc prose redaction of a shared
blob is unsound (this is why D3 cannot be fixed downstream of the
narrator). The narrator must partition at generation time. The
tool-layer filter (ADR-104) already gives the model per-`perspective_pc`
correct *inputs*; B3 makes it emit per-PC-partitioned *outputs* for the
merged-MP turn. `narrator_perception_filter.py` is invoked
per-segment-perspective during composition.

**B4 — Per-PC-segment POV model (replaces single `anchor_pc`).** Each
private segment carries its own `anchor_pc`; the public `text` carries
an `anchor_pc` only when it is genuinely single-PC-anchored, else
atmospheric. `_apply_pov_swap` runs per segment against its recipient
(Track A having fixed recipient binding). This dissolves the
single-`anchor_pc` limitation (D4 POV half) structurally rather than by
loop-patching.

### OTEL — every decision emits a span (CLAUDE.md mandate)

The GM panel is the lie detector; a firewall that cannot be observed
cannot be trusted. Required spans (Dev handoff specifies attributes):

- `narration.visibility_classified` (exists) — extend: emit the
  derived `visible_to` (not the constant `"all"`) and a
  `private_segment_count`.
- `projection.filter.decide` (exists, `ComposedFilter`) — must fire
  **once per DISTINCT recipient** with `player_id` == that recipient
  (Track A makes this true; it is the verification signal).
- `narrator.perception_rewrite` (exists) — once per DISTINCT viewer.
- `narration.second_person_swap` (exists) — `swap_target_name` ==
  the recipient, per segment.
- new `narration.segment_routed` — per private segment:
  `anchor_pc`, `visible_to`, `recipient_count`, `withheld_from_count`.
- new `invariant.secret_routed` — when B1's CoreInvariant excludes a
  player from a `_visibility`-gated kind: `kind`, `player_id`,
  `included`, `source="invariant:visibility_gated"`.

Verification command (oq-1 owns, existing): drive 1 MP turn → pull
newest `turn` trace → assert one `projection.filter.decide` +
`perception_rewrite` per DISTINCT recipient, `swap_target_name` ==
recipient, and the UI leak check (second submitter's tab MUST NOT
contain the first's withheld content).

## Consequences

### Positive

- The firewall is structural (CoreInvariant), not pack-configurable —
  a pack cannot silently weaken it.
- Track A is independently verifiable this session via existing spans;
  unblocks oq-1 re-verification the moment `origin/develop` advances.
- B3's public-safe contract makes the existing emitter-bypass
  (`emitters.py:301` "Invariant 3 — visibility filter bypassed for the
  emitter") *safe by construction*: the shared blob the emitter
  receives raw is public-safe, so the bypass no longer leaks.
- Sealed-visibility (PvP) becomes trivial later: route a private
  segment to one client, emit no public `text`.
- Reuses existing wired machinery (`ComposedFilter` →
  `VisibilityTagRule`, `secret_routes`/SECRET_NOTE,
  `aggregate_visibility`); near-zero new infrastructure. The new
  surface is the per-PC narration segment field and one CoreInvariant
  branch.

### Negative / risks

- B3 is an output-contract change to the SDK narrator (ADR-101/102) —
  the highest-risk piece. It needs prompt + structured-output schema
  work and is the durable-half cost. Track A does **not** depend on
  B3 and lands first.
- Two visibility surfaces remain conceptually (CoreInvariant exclusion
  + GenreRuleStage fidelity). Documented in both module docstrings, as
  ADR-104 already required.
- A pack whose `projection.yaml` lacks `NARRATION: visibility_tag`
  loses *fidelity* shaping but — post-B1 — no longer loses the
  *secret-routing* firewall. This is the intended asymmetry.

### Doctrine preserved

- ADR-036 collaborative-visibility (peer action text visible during
  submit-and-wait) is untouched: public `text` is exactly the
  collaborative surface; only genuinely private perception is
  partitioned.
- ADR-104's tool-layer decision is unchanged and correct; this ADR
  completes its deferred broadcast half.

## References

- ADR-104 — Perception Filtering at the Tool Layer (parent; this
  completes its deferred broadcast-layer half)
- ADR-101 — Anthropic SDK as Narrator Backend (B3 amends its output
  contract)
- ADR-102 — Tool-Use Protocol for Structured Output (per-PC segment
  schema substrate)
- ADR-028 — Perception Rewriter (superseded by 104; historical intent
  delivered here for the merged-MP path)
- ADR-036 — Multiplayer Turn Coordination (collaborative-visibility
  doctrine, preserved)
- Coordination record: `sq-playtest-pingpong.md` HIGH bug entry
  "MP per-recipient perception pipeline runs TWICE…" — authoritative
  scope record (Track A / Track B split, 2026-05-16)

## Amendment 2026-05-28 — Implementation reconciliation (both tracks now live)

A re-audit flagged this ADR as "Track A partially done, Track B
unimplemented," specifically claiming: (a) `private_prose_segments` does
NOT exist on `NarrationTurnResult`; (b) per-recipient private-prose
partitioning is not implemented; (c) `emitters.py` still reads the rotated
`handler._session_data.player_id` rather than per-row authorship. **All
three claims are now FALSE** — the code has advanced well past the audited
state. Both tracks have landed. Re-verified against `sidequest-server/`:

### Track A — per-row emitter authorship: IMPLEMENTED

`emit_event` now takes an explicit `author_player_id` parameter
(`sidequest-server/sidequest/server/emitters.py:246`) documented as the
ADR-105 Track A fix (`emitters.py:255-261`). The emitter resolves the
author per row: `emitter_player_id = author_player_id if author_player_id
is not None else _rotated_session_player_id` (`emitters.py:300-306`), and
`project_emitter = author_player_id is not None` (`:308`) drives the
per-recipient projection pass. The rotated
`handler._session_data.player_id` is now only the *fallback* for
single-author turns, not the unconditional read the audit (and original D4)
described. The NARRATION emit threads the real author:
`websocket_session_handler.py:1370` passes
`author_player_id=_mp_author`.

### Track B — content firewall: IMPLEMENTED

- **`private_prose_segments` EXISTS** on the narrator result —
  `sidequest-server/sidequest/agents/orchestrator.py:470`
  (`private_prose_segments: list[dict[str, Any]] = field(default_factory=list)`),
  documented inline as the ADR-105 B3 per-PC private-prose field. It is
  populated on both backends (`orchestrator.py:3105,3414`) from the
  narrator's partitioned `game_patch.private_segments`
  (`orchestrator.py:1194-1222`), with `_scrub_public_prose`
  (`orchestrator.py:1030`) keeping the shared blob public-safe (B3
  contract).
- **D1 fixed — `visible_to` is derived, not hardcoded `"all"`.**
  `classify_narration_visibility` now lives at
  `sidequest-server/sidequest/server/visibility_classifier.py:85` (note:
  moved from the audited `sidequest/agents/...` path) and reads
  `result.secret_routes` to build per-route `private_segments`
  (`visibility_classifier.py:163-193`), unioning via `union_visible_to`.
  The shared NARRATION stays `"all"` *by contract* (public-safe), exactly
  as B2/B3 specify.
- **D2 fixed — secret routing is a CoreInvariant.**
  `sidequest/game/projection/invariants.py` now has a visibility-gated
  branch: `SECRET_NOTE` was *removed* from `TARGETED_KINDS`
  (`invariants.py:49-53`) and both `SECRET_NOTE` and `NARRATION_SEGMENT`
  are handled by reading `_visibility.visible_to`
  (`invariants.py:59-67,145-176`), failing closed with a
  `source="invariant:visibility_gated"` span (`:176,251`) — B1 done.
- **B3 emission — NARRATION_SEGMENT is wired.** Each private segment is
  emitted as its own `NARRATION_SEGMENT` event routed by `visible_to`:
  `websocket_session_handler.py:1378` reads `result.private_prose_segments`,
  `:1424-1426` emits `NARRATION_SEGMENT` with `author_player_id=_owner_pid`
  (the owning PC), and unroutable segments are **dropped, not leaked**
  (`:1393-1417`, fail-loud `narration.segment_unroutable` + watcher span).
  `NarrationSegmentPayload` / `NarrationSegmentMessage` are registered in
  `server/session_handler.py:34-35,69`.
- **OTEL.** `narration.segment_routed` (`websocket_session_handler.py:1407`)
  and the `narration.visibility_classified` extension carrying
  `private_segment_count` / `private_visible_to`
  (`visibility_classifier.py:216-219`) both fire, plus the
  `invariant:visibility_gated` exclusion span.

### Net

ADR-104's tool-layer filtering is live (unchanged). ADR-105's
broadcast-layer completion — Track A per-row authorship AND Track B content
firewall (private prose segments, derived `visible_to`, visibility-gated
CoreInvariant, NARRATION_SEGMENT routing, OTEL) — is **now implemented.**
The `partial` framing reflected an earlier code state; the firewall the ADR
specifies is built. (Residual `partial` scope, if any, would be playtest
re-verification of the leak check, not missing implementation.)
