---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-14: magic_working — load magic_state for worlds with caster classes (or degrade cleanly) so Mage casting isn't a no-op

## ⚠️ Staleness Check — THIS STORY IS ALREADY DONE (verified 2026-05-28)

**Mage casting is NOT a no-op in current `develop`. The premise of this
story — "magic_state isn't loaded, so the 59-5 handler no-ops" — is
false against today's code.** Everything the title asks for (load
magic_state for caster-class worlds; degrade cleanly+loudly for
non-caster worlds; OTEL proving non-no-op engagement) already shipped and
is test-covered. Recommend the SM **close 59-14 as done-by-landed-work**
(same disposition as 59-18) after a quick e2e confirmation, OR re-file it
narrowly if a *specific* caster world is still failing to load (see "If
NOT stale" below). Do not run a fresh RED→GREEN cycle against the stated
premise — there is no red to find.

### Evidence (file:line, all on current `develop`)

**1. magic_state IS loaded for caster-class worlds — three live seams:**
- `sidequest/server/websocket_handlers/chargen_mixin.py:935` — host
  chargen-complete calls `init_magic_state_for_session(...)` (the
  "production hook that pairs Phase 1's loader with Phase 2's snapshot
  field"). Comment at :925-934 explicitly: "without it, `snapshot.magic_state`
  stays None and the LedgerPanel never surfaces bars."
- `sidequest/server/websocket_handlers/chargen_mixin.py:1147` — MP
  second-commit/joiner mirrors the same call (Pingpong 2026-05-07 fix:
  "magic.init only fires for the host" — joiners had no actor row).
- `sidequest/handlers/connect.py:191` — `_backfill_magic_state_on_resume`
  re-runs `init_magic_state_for_session` on slug-resume when
  `snapshot.magic_state is None` and the world ships `magic.yaml`
  (playtest 2026-04-30 #9 fix).

**2. The loader itself (`sidequest/server/magic_init.py:98`,
`init_magic_state_for_session`) already does the "load for caster classes
or degrade cleanly" work this story names:**
- Loads `genre/magic.yaml` + `worlds/<slug>/magic.yaml`, builds
  `MagicState.from_config`, registers the actor via `add_character`, and
  seeds `learned_v1` known-spells + per-level slot bars for casters whose
  `ClassDef.magic_config` is set (`magic_init.py:263-311`).
- "Caster class" = a `ClassDef` with `magic_access`/`magic_config`
  populated (`sidequest/genre/models/character.py:164-165`); the
  `learned_v1` seed only fires when `class_def.magic_config is not None`
  (`magic_init.py:265`). Non-casters are a deliberate no-op at this seam.

**3. Degradation is clean AND LOUD (not silent) — matches CLAUDE.md "No
Silent Fallbacks":**
- World with no `magic.yaml` → `magic.init_skipped` watcher event,
  severity `info`, returns `False` (`magic_init.py:139-157`). Surfaced to
  GM panel so "invisible" never reads as "broken."
- Malformed `magic.yaml` → `magic.init_failed` ERROR log + watcher event,
  snapshot left untouched, does NOT crash chargen (`magic_init.py:159-182`).
- `innate_v1` active but zero character bars instantiated →
  `magic.init_no_actor_bars` WARNING (`magic_init.py:343-366`).
- Missing catalog for a declared caster tradition →
  `magic.init_no_catalog` WARNING (`magic_init.py:276-295`).
- A working dispatched against a `None` magic_state raises
  `MagicWorkingParseError("magic_working emitted but world has no
  magic_state loaded")` (`sidequest/server/narration_apply.py:655`), which
  the 59-5 handler propagates by design
  (`sidequest/agents/subsystems/magic_working.py:14-17,53-56`) — the no-op
  is impossible because it fails loud.

**4. OTEL proving engagement is non-no-op already fires:**
- `magic.init` span/watcher on load with `plugins`/`bars`/`first_commit`
  (`magic_init.py:324-336`).
- `magic.backfill_on_resume` span on the resume path (`connect.py:187`).
- `magic_working_span` + `state_transition`/`op=working` watcher on every
  applied working, with `costs_debited` + `ledger_after`
  (`narration_apply.py:691-714`).
- The 59-3 lie-detector watches the gap:
  `dispatch_engagement_watcher.py:121-125` reports
  `"snapshot.magic_state is None (world has no magic config loaded)"` or
  `"no WorkingRecord with actor=… in magic_state.working_log"` as a
  mismatch.

**5. Test coverage already exists** (`tests/server/`):
- `test_magic_init.py`, `test_magic_init_caverns_and_claudes.py`,
  `test_magic_init_mp_second_commit.py`, `test_magic_state_resume_backfill.py`.

**6. Git history** — 59-5 (handler) and the magic-init wiring all landed:
`37b2b80 complete 59-5`, `bd1bc48 complete 50-22 — scene-harness
magic_state + Character.abilities hydration`, `3bfb9a6 Magic Phase 4 smoke
verify (47-2)`. No open commit touches a "magic_state not loaded" gap.

### If NOT stale (what a real residual bug would look like)

The only thing that could still be live is a *specific* caster world
whose `magic.yaml` exists but whose chargen never reaches the seam, or a
world that ships caster `ClassDef`s but no `magic.yaml` (so casting silently
no-ops *because there's nothing to load*, which would be a content/loader
gap, not a server-wiring gap). **Before treating this as live work, run
the e2e in AC1 below against the actual suspect world and capture the
spans.** If `magic.init` fires and `magic.working` lands, it is stale —
close it. The matching e2e validation story is **59-15** ("Engagement e2e
validation — beneath_sunden + road_warrior … magic actually fire
mechanically (OTEL span proof)"); 59-14's residual value, if any, folds
there.

## Business Context

Per the SOUL "Illusionism" failure mode (epic 59 §Overview), a caster
class whose mechanical engine never engages produces convincing prose with
zero crunch — exactly what Sebastien and Jade (the playgroup's two
mechanics-first players, per root `CLAUDE.md`) notice and miss. A Mage who
"casts" with no ledger debit, no slot spend, and no threshold promotion is
a lie the GM panel is supposed to catch. This story was filed to guarantee
`snapshot.magic_state` is populated for any world with caster classes so
the 59-5 `magic_working` dispatch handler has bars to debit — and to make
the absence of magic config (non-caster worlds) a *visible, justified*
non-engagement rather than silent nothing.

As the Staleness Check documents, that guarantee already holds in code.
The business value is therefore **verification, not construction**: prove
the load happens for every caster world the playgroup plays
(space_opera/coyote_star, heavy_metal/long_foundry, caverns_and_claudes),
and that non-caster worlds degrade loudly.

## Technical Guardrails

**Key files (all already implemented — read, do not rewrite):**
- `sidequest/server/magic_init.py:98` — `init_magic_state_for_session`,
  the load-or-degrade core. This is the function the title describes.
- `sidequest/server/websocket_handlers/chargen_mixin.py:935,1147` — the
  two chargen call seams (host + MP joiner).
- `sidequest/handlers/connect.py:140-204` — `_backfill_magic_state_on_resume`,
  the resume-path load.
- `sidequest/agents/subsystems/magic_working.py` — the 59-5 dispatch
  handler that consumes the loaded state; raises `MagicWorkingParseError`
  on `magic_state is None` (no-op is impossible by design).
- `sidequest/server/narration_apply.py:633` — `apply_magic_working`,
  parse-validate-apply + `magic_working_span`.
- `sidequest/genre/models/character.py:164-165` — `magic_access` /
  `magic_config` on `ClassDef` define what "caster class" means.

**Patterns to follow if any residual fix is needed:**
- No silent fallbacks (CLAUDE.md, memory `feedback_no_fallbacks_hard`):
  degradation MUST emit a watcher event (`magic.init_skipped` /
  `magic.init_failed` / `magic.init_no_catalog` / `magic.init_no_actor_bars`)
  — never return silently.
- No source-text wiring tests (server `CLAUDE.md`): prove engagement via
  OTEL span assertions (`magic.init`, `magic.working`) or fixture-driven
  behavior, never by grepping handler source.
- Content/server cross-repo (story `repos: server,content`): if a caster
  world is missing its `magic.yaml`, that fix lands in `sidequest-content`
  (the world dir), not server. Branch each subrepo before the first commit
  (memory `feedback_pf_hook_scans_subrepos`).

**What NOT to touch:**
- The 59-5 handler, `run_dispatch_bank`, or `apply_magic_working` — all
  stable, all consuming the loaded state correctly.
- The idempotence branch in `magic_init.py:201-256` — it is load-bearing
  for MP (Pingpong 2026-04-30 / 2026-05-07 fixes); a fresh
  `MagicState.from_config` per joiner wipes prior committers.

## Scope Boundaries

**In scope (if the e2e proves a residual gap exists):**
- Confirming `init_magic_state_for_session` reaches every caster world's
  chargen/resume path and produces a non-empty ledger.
- A clean+loud degradation assertion for at least one non-caster world.
- An OTEL span assertion proving a real working lands (non-no-op).
- Content fix ONLY if a caster world ships caster `ClassDef`s but no
  `magic.yaml` (loader/content gap).

**Out of scope:**
- The 59-5 dispatch handler (done).
- Magic system mechanics / game-design changes — this is load + verify.
- Confrontation/movement engagement (59-15 covers those e2e).
- The IntentRouter core, `run_dispatch_bank`, lie-detector watcher (59-2/3/4).
- beneath_sunden's unmapped deep (memory: unmapped by design — not a magic
  gap).

## AC Context

**AC1 — magic_state is loaded for caster-class worlds (OTEL-proven):**
Drive chargen for a caster (e.g. a Mage on caverns_and_claudes, or the
coyote_star/long_foundry magic worlds) through the real pipeline; assert
`init_magic_state_for_session` returns `True`, `snapshot.magic_state` is
non-None with per-character bars, and a `magic.init` span fired with
`bars > 0`. **Already covered** by `tests/server/test_magic_init.py` +
`test_magic_init_caverns_and_claudes.py`. The residual leg is the resume
seam (`test_magic_state_resume_backfill.py`) and MP joiner
(`test_magic_init_mp_second_commit.py`) — also already present. If writing
new RED, you will not get a failing test against current code.

**AC2 — clean AND LOUD degradation for non-caster worlds:**
Drive chargen for a world with no `magic.yaml` (the common non-caster
case); assert `init_magic_state_for_session` returns `False`,
`snapshot.magic_state` stays `None`, AND a `magic.init_skipped` watcher
event fired (severity `info`, `reason="no_magic_yaml"`) — the degradation
is GM-panel-visible, not silent (`magic_init.py:139-157`). Separately,
assert a `magic_working` dispatched against a `None` magic_state raises
`MagicWorkingParseError` (`narration_apply.py:655`) rather than silently
no-opping — this is the "isn't a no-op" guarantee in its loud form.

**AC3 — an OTEL span proves magic engagement is non-no-op:**
Drive a real spellcasting working through `apply_magic_working` /
`run_magic_working_dispatch` and assert the `magic.working` span fired with
`costs_debited` and a `ledger_after` reflecting the spend
(`narration_apply.py:691-714`), proving the ledger actually mutated — not
just narration. Cross-check the 59-3 lie-detector
(`dispatch_engagement_watcher.py:121-125`) emits NO mismatch on this turn
(router dispatched magic AND the engine engaged). A mismatch span here
would be the only signature of a genuine residual no-op.

## Assumptions

- The story was filed against an older snapshot where the chargen/resume
  magic-init wiring had not yet been confirmed live; the 47-x Magic Phase 4
  work + 59-5 closed that gap before this story was picked up.
- "Caster class" = a genre-pack `ClassDef` with `magic_config` set; "world
  with caster classes" = a world shipping the genre+world `magic.yaml`
  pair that `init_magic_state_for_session` loads.
- If the SM confirms the e2e passes for all playgroup caster worlds, the
  correct disposition is **close as done-by-landed-work** (cite this
  staleness check), folding any e2e proof into 59-15.
