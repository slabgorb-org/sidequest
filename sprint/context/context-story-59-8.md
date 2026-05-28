---
parent: context-epic-59.md
workflow: trivial
---

# Story 59-8: Glenross playtest validation — folds 59-1 AC1 LLM behavior leg

## ⚠️ Staleness Check

**Premise is LIVE — this is a genuinely owed playtest, not stale work.** Verified
against current code on 2026-05-28:

- The Intent Router spine is fully shipped. All of 59-8's blocking dependencies
  (59-4 confrontation cutover, 59-5 magic, 59-6 scenario_clue, 59-7 the three
  subsystems) are `status: done` in `sprint/epic-59.yaml`. The live pre-narrator
  pass is `sidequest-server/sidequest/server/intent_router_pass.py:158`
  (`execute_intent_router_pre_narrator_pass`); the router is
  `sidequest-server/sidequest/agents/intent_router.py`; handlers live in
  `sidequest-server/sidequest/agents/subsystems/` (confrontation, magic_working,
  scenario_clue, npc_agency, distinctive_detail, reflect_absence, movement).
- 59-8 itself is still `status: backlog` (`sprint/epic-59.yaml:148`).
- **A prior close attempt FAILED loudly.** The SM tried to verify-by-log on
  2026-05-26 (commit `7e5f407`, recorded as the last AC in the YAML) and could
  NOT close it: no qualifying ~30-turn Glenross/tea_and_murder SDK session ever
  existed in the rotated logs. The only two real Glenross sessions found
  (`005245` ~16 turns, `003023` ~5 turns) had ZERO confrontations engage —
  `intent_router.dispatch.*`/`encounter.created` spans absent — because
  (a) the router degraded every turn on unparseable JSON, and (b) the dispatch
  seam threw `run_scenario_clue_dispatch() missing 1 required keyword-only
  argument: snapshot` (the kw-only-arg trap, memory `project_opposed_check_wiring_trap`
  cousin).

**What has changed since that failed attempt (why a fresh run is now warranted):**
The pre-narrator pass at `intent_router_pass.py:158` now threads the full
`run_dispatch_bank` context — `{snapshot, pack, player_name, npcs_present,
additional_player_names, dungeon_store, palette, lookahead_handle}` — so the
kw-only `snapshot` TypeError that killed the 2026-05-26 `003023` dispatch is
addressed in pass 1. The genre-vocabulary feed (59-10, done) also targets the
JSON-degrade root cause. The remaining `run_dispatch_bank` double-run is tracked
separately as 59-11 (still backlog) and is now NON-FATAL OTEL noise, not a turn
killer. **None of this is a substitute for the live session — it must actually
be run and observed.** This is a *validation* story: ACs are playtest steps and
a writeup, not code changes.

## Business Context

This is the capstone of Epic 59 and the discharge of a debt carried since Phase 0.
Story 59-1 shipped the `begin_confrontation` point-fix with deterministic fixture
coverage but explicitly deferred its AC1 "LLM free tool-choice playtest" leg — the
question fixtures can never answer: *does a real SDK narrator/router actually engage
the mechanical engine in a live Glenross session, or does it wing convincing prose
with zero backing?* That is the SOUL "Illusionism" failure mode, the project-existential
bug this whole epic exists to kill. Fixtures prove the substrate; only a playtest
proves the illusion holds against a career-GM player.

Glenross (`tea_and_murder`) is the right proving ground precisely because it is
**social-first** — its confrontation types are `negotiation`, `trial`, `auction`,
`social_duel`, `scandal` (`sidequest-content/genre_packs/tea_and_murder/rules.yaml:153,201,247,299,341`),
with no HP/combat lethality to mask a misfire. If the router engages a social
confrontation here, the spine works for the hardest case.

Per the CLAUDE.md player rubric, **Sebastien's (and Jade's) mechanics-first
perspective is load-bearing** for AC4: the GM panel's router-trace must let a
mechanics-first reader *see* that the engine fired. Note the framing carefully —
59-8's GM-panel evaluation is a **Keith/dev observability** judgement (is the
router-trace usable as a lie detector?), written *from* a Sebastien-style
mechanical-visibility lens. It is not a claim that Sebastien sees the GM panel;
he does not. The writeup asks "can a mechanics-first reader trust this trace,"
which is the right sharpening question for the dev tool.

## Technical Guardrails

**This story writes NO production code.** It is a `trivial`-workflow playtest
report. The only artifacts are a session writeup and a post-mortem capture file.

**What to drive (read-only against the running stack):**
- Run against the **SDK backend** (`SIDEQUEST_LLM_BACKEND=anthropic_sdk`, the
  default per ADR-101) — the whole point is validating LLM behavior, not fixtures.
- Pack/world: `tea_and_murder` / `glenross`
  (`sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`).
- Boot via `just up`; logs tee to `~/.sidequest/logs/sidequest-server.log`
  (re-tail with `just logs server`). Watch the GM panel via `just otel`.

**OTEL spans that are the lie detector (verify these by their REAL names — the
epic/AC prose uses shorthand that does not match the code):**
- Router entry: `intent_router.decompose`
  (`telemetry/spans/intent_router.py:44`).
- Per-subsystem engagement: **`intent_router.subsystem`**
  (`telemetry/spans/intent_router.py:82`) carrying `subsystem`, `idempotency_key`,
  `produced_directives`, `error` attributes — this is the actual dispatch span;
  there is NO `intent_router.dispatch.confrontation` span literally named.
- Bank summary: `intent_router.dispatch_bank` (`:71`).
- Encounter actually created: `encounter.confrontation_initiated`
  (`telemetry/spans/encounter.py:65`) / `encounter.phase_transition` (`:15`) —
  the AC's `encounter.created` is shorthand for this family; there is no span
  literally named `encounter.created`.
- Lie-detector mismatch: `dispatch_engagement.confrontation.mismatch`
  (`telemetry/spans/dispatch_engagement.py:31`, Story 59-3). AC3 requires ZERO
  of these family spans in real play.
- Router failure: `intent_router.failed` (`:59`) — its presence is a red flag,
  not a pass.

**Honesty discipline (memory `feedback_measure_dont_assert`):** Do not assert the
spine works from indirect evidence (tests passing, code reading). Capture the real
log/span stream and read it. If the session degrades or the dispatch seam throws
(as it did 2026-05-26), the story is NOT verifiable — record that loudly and bounce
it, exactly as the prior SM did. A failed run is a legitimate, useful outcome.

## Scope Boundaries

**In scope:**
- One real ~30-turn Glenross (`tea_and_murder`) session on the SDK backend with
  at least three distinct social confrontation triggers attempted.
- OTEL/GM-panel observation and verification of engagement + zero mismatch spans.
- Latency observation of the per-turn router add.
- A ~200-word session writeup from the Sebastien-style mechanical-visibility lens
  (is the GM-panel router-trace usable as a lie detector?).
- A post-mortem capture at `sprint/archive/59-8-session.md` for narrative misses /
  surprises, fed back into router-prompt tuning.

**Out of scope:**
- Any code change. If the session surfaces a bug (e.g. dispatch seam TypeError,
  router JSON degrade), FILE it — do not fix it here. Candidate homes already
  exist: 59-11 (redundant second dispatch run), 59-14 (magic_state load), 59-9
  (cross_player redaction). Per memory `feedback_check_inflight_work_before_filing`,
  grep the epic before filing a "new" bug.
- Non-Glenross packs (beneath_sunden/road_warrior engagement e2e is 59-15).
- Magic/clue/npc_agency deep validation — this run is confrontation-focused; the
  other subsystems' fixture coverage already shipped in 59-5/59-6/59-7.
- Playtest-driven balance/calibration tuning of confrontation difficulty (ADR-093).

## AC Context

**AC1 — 30-turn Glenross session, three distinct confrontation triggers.**
Drive a real SDK session reaching at least three of `negotiation`,
`social_duel`/`scandal`, and `trial`/`auction` (whichever the scenario makes
reachable — Glenross is murder-investigation shaped, so `negotiation` and
`scandal`/`social_duel` are the natural ones; `trial`/`auction` may not be
organically reachable in 30 turns — note which fired and which were unreachable).
Per memory `feedback_playtest_short_actions`, scripted player actions stay 1-2
sentences and push toward the confrontation triggers, not flowery prose.

**AC2 — All three confrontations engage, verified via OTEL + GM panel.**
On each triggering turn confirm the span chain `intent_router.decompose` →
`intent_router.subsystem` (subsystem=`confrontation`) → `encounter.confrontation_initiated`
fires, in order, in one round, BEFORE the narrator turn. Cross-check on the GM
panel, not just the raw log. This is the literal discharge of 59-1 AC1's owed leg.

**AC3 — Zero `dispatch_engagement.*.mismatch` spans.**
The 59-3 watcher (`telemetry/spans/dispatch_engagement.py`) fires when the router
dispatched a subsystem but the engine did not engage on the post-turn snapshot.
Zero of these in real play means no false positives AND no silent misfires. A
single mismatch span is a finding to capture, not necessarily a story failure —
record it.

**AC4 — ~200-word writeup, Sebastien-style mechanical-visibility lens.**
The core qualitative question: can a mechanics-first reader look at the GM panel's
router-trace and *trust* that the engine fired (vs. the narrator improvising)?
This is a Keith/dev observability judgement written from that lens — NOT a claim
about what Sebastien sees in the player UI (per CLAUDE.md: GM-panel/OTEL are
dev-side tools). Evaluate trace legibility, span ordering clarity, and whether a
misfire would be obvious.

**AC5 — Latency budget: per-turn router add < 1.2s.**
Haiku 4.5 via SDK expected ~0.3-0.5s (per epic §Cross-cutting risks). Capture real
timing from the `intent_router.decompose`/`dispatch_bank` spans — the prior attempt
logged NO router timing, so this must be measured this run, not assumed.

**AC6 — Capture misses/surprises in `sprint/archive/59-8-session.md`.**
Post-mortem for narrative misses and router-prompt tuning feedback. If the run
cannot complete (degrade/crash), THIS file records the blocker and the story
bounces — that is the correct outcome, matching the 2026-05-26 SM precedent.

## Assumptions

- The SDK backend is the default and reachable; `just up` boots a clean stack with
  exactly one server on port 8765 (memory `project_duplicate_stack_cost_runaway` —
  check `lsof :8765` first; duplicate servers across oq-1/oq-2 corrupt cost and
  cache signals).
- The 59-4 pre-narrator pass plus the 59-10 vocabulary feed have addressed the
  two 2026-05-26 blockers (kw-only dispatch TypeError + JSON degrade) well enough
  for a session to complete. If they have NOT, this run discovers that and the
  story bounces — the assumption is testable, not load-bearing.
- The GM panel (`just otel`, server `/dashboard`) renders `intent_router.*` and
  `dispatch_engagement.*` spans; the router-trace surface exists for AC4 to evaluate.
- 30 turns is enough Glenross runway to organically reach three confrontation
  triggers; if not, AC1 is satisfied by documenting which fired and why the others
  were unreachable, not by forcing artificial triggers.
