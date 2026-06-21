# Epic 126: Fate Core playtest follow-ups — annees_folles / dust_and_lead eval

## Overview

Open findings from the Fate Core (ADR-144) evaluation playtests: the original 2026-06-16/17 `pulp_noir/annees_folles` eval, plus the 2026-06-19/20 full-stack 150-1/150-2 verify pass (`annees_folles` + `spaghetti_western/dust_and_lead`) that exercised the now-unblocked Fate conflict spine end-to-end and surfaced a second wave of follow-ups (126-29…126-36). The marquee cluster (#936 contest resolution / 126-7 4dF determinative / 126-1 harm ablation) is **verified in play**; what remains is correctness/legibility cleanup on the Fate confrontation surface, the NPC-binding seam, and a handful of observability/UX items.

**Priority:** P3 (p2 on the de-nativize-seating, proactive-tile gating, win-meter, and NPC-binding cluster)
**Repo:** server, ui (some content)
**Stories:** 36 (126-1…126-36)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **sq-playtest ping-pong** (`~/Projects/sq-playtest-pingpong.md`) | 150-1/150-2 task log + SM TRIAGE table (finding → story map for 126-29…126-36) |
| **ADR-143** (`docs/adr/`) | Bind the Ruleset, Don't Balance It — WWN-combat dead end; the doctrine behind de-nativizing Fate seating (126-30) |
| **ADR-144** (`docs/adr/`) | Fate Core binding replaces the native ruleset — `compute_dc` is `NotImplementedError`, the 4dF + ladder conflict engine is the resolution surface |
| **ADR-129 / ADR-151** (`docs/adr/`) | N-seat sealed-commit loop + the DEFEND follow-up barrier — the one-action-per-participant-per-exchange invariant 126-29 must gate on (not relax) |
| **ADR-122** (`docs/adr/`) | RoomRegistry never-evict — why stale test-`*` sessions linger on the live GM panel (126-34) |

## Background

The first wave (126-1…126-28) cleared the blockers that kept the Fate conflict spine from seating at all: the `_offer_dc` native-overlay crash (#964), the sheetless-opponent crash (#966), stunts projection (#967/#427), the defend-throw UI (126-17), and chargen seeding (126-24). With those merged and live, the 150-1/150-2 verify pass drove a full Fate conflict — seat → attack → 4dF → DEFEND barrier → ablative harm — and confirmed the marquee ACs. That same pass exposed the **second wave** this epic now also carries: the conflict surface still has correctness and legibility gaps once the engine actually runs.

The open stories fall into four clusters. **(1) Fate confrontation correctness** — de-nativize *seating* so a Fate standoff is a pure Fate contest with no vestigial native tension-dial/beat track (126-30, the upstream half of the Bind-the-Ruleset cleanup #964 only partially did), and gate the proactive action tiles on the sealed-commit state so a resumed mid-exchange conflict doesn't offer actions the server correctly rejects (126-29). **(2) Conflict legibility** — render the opponent stress track + a taken-out win-meter from the now-projected `FATE_STATE.conflict` data (126-31, the UI half of server PR #973). **(3) NPC identity + culture routing** — one root seam (narrated NPCs not promoted to `snapshot.npcs` before mint/seating) that manifests as a wrong-creature opponent, a hollow canonical-figure duplicate, and a `shuffle_fallback` wrong-culture name reroute (126-32, large/risky). **(4) Observability + UX hygiene** — keep test-run sessions off the live GM dashboard (126-34), dedup inventory grants (126-33), resolve the on-play item→aspect promotion question (126-35, Keith design call), and scale solo-session framing (126-36).

Several adjacent findings were deliberately **not** re-filed: chargen-seed confirm-repros (already 126-17), the harm-under-application question (GM-ruled *not a bug*), the ~15 fixes merged in-session awaiting only DRIVER verification (PRs #964/#966/#967/#972/#973 + ui #427/#429/#430/#431/#432 + dice-lib #27/#28), and the pulp_noir `confrontations:` content gap (shipped as content PR #479).

## Technical Architecture

The open work concentrates on the Fate confrontation seam (server + UI) plus the NPC-minting timing seam. Key files (paths as documented by FIXER/DRIVER in the ping-pong log):

| Concern | Key files | Stories |
|---------|-----------|---------|
| Fate confrontation **seating** (de-nativize) | `server/dispatch/encounter_lifecycle.py`, `server/dispatch/confrontation.py` (`should_emit_native_confrontation` gate), `game/ruleset/fate.py` (`compute_dc` guard, ADR-144) | 126-30 |
| Sealed-commit **state on the wire** | `protocol/models.py` (`FateConflictParticipant`), `game/ruleset/fate_projection.py`, `server/websocket_handlers/fate_state_emit.py`; UI `FateConflictSurface.tsx` (`fate-sealed-hint`) | 126-29, 126-31 |
| Win-meter / opponent track render | `FateConflictSurface.tsx` (mirror `ConfrontationOverlay` `EdgeBar`); data already on `FATE_STATE.conflict.participants[opponent].stress/consequences` + `fate.conflict.projected` span | 126-31 |
| NPC **binding + culture routing** | `server/narration_apply.py` (`_resolve_invented_naming_context`, person-mint, promotion-before-seating), `encounter_lifecycle.py` (`_resolve_opponent_from_roster`, `_seed_fate_opponents`) | 126-32 |
| Inventory dedup | `state.inventory_update` apply path (server) | 126-33 |
| OTEL session hygiene | UI `useLiveSource.ts:347-355` (picker/State-tab filter), `last_activity_ts` on-read bump, WatcherHub session-tagging; test-isolation (separate port / no-watcher mode) | 126-34 |

**Invariants to preserve (do not "fix" by relaxing):** the `dispatch_fate_throw` sealed-commit guard (ADR-129/151) — 126-29 gates the *UI*, not the server; the `compute_dc` `NotImplementedError` (ADR-144 safety net); the `decide_opponent_action` sheet-required guard (#966). Per ADR-143, the Fate win signal is **opponent stress+consequence fill toward taken-out**, never the vestigial `opponent_metric.tension` dial.

## Cross-Epic Dependencies

**Depends on:**
- Epic 150 (Fate-world full-stack verify — `annees_folles` / `dust_and_lead`) — the playtest source that produces these findings; 150-2 verify confirmed the spine these stories refine.
- ADR-143 / ADR-144 (Fate binding doctrine) — the rules the correctness stories (126-30, 126-32) must satisfy.

**Depended on by:**
- None directly — this is a follow-up/cleanup epic. 126-31 (win-meter UI) consumes the server projection already shipped in PR #973; 126-32 is the canonical NPC-binding fix that downstream worlds (Oz, dust_and_lead) need for identity coherence.

---
_Refreshed 2026-06-20 (SM, Camina Drummer) to add the 150-1/150-2 second-wave stories 126-29…126-36 and bring the doc to schema-compliance (Technical Architecture). Source: sq-playtest-pingpong._
