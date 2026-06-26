---
story_id: "159-5"
jira_key: ""
epic: "159"
workflow: "tdd"
---
# Story 159-5: Companion run loop, WebSocket transport, CLI, and full-loop wiring

## Story Details
- **ID:** 159-5
- **Jira Key:** (none - Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** 159-4 (Companion package core — intent, manifest, persona, dice, protocol, brain, actuation)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-26T11:55:01Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T10:40:00+00:00 | 2026-06-26T10:42:20Z | 2m 20s |
| red | 2026-06-26T10:42:20Z | 2026-06-26T10:56:46Z | 14m 26s |
| green | 2026-06-26T10:56:46Z | 2026-06-26T11:08:48Z | 12m 2s |
| review | 2026-06-26T11:08:48Z | 2026-06-26T11:26:27Z | 17m 39s |
| red | 2026-06-26T11:26:27Z | 2026-06-26T11:37:22Z | 10m 55s |
| green | 2026-06-26T11:37:22Z | 2026-06-26T11:45:06Z | 7m 44s |
| review | 2026-06-26T11:45:06Z | 2026-06-26T11:55:01Z | 9m 55s |
| finish | 2026-06-26T11:55:01Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the WS transport's `websockets` dep and the `companion` console-script
  entry are not declared. GREEN must add `websockets>=12` to `[project.dependencies]`, add
  `companion = "companion.cli:app"` to `[project.scripts]`, and run `uv sync`.
  Affects `sidequest-understudy/pyproject.toml` (add dep + script). Enforced by
  `tests/companion/test_cli_packaging.py`, `test_ws_transport.py`, `test_cli.py`.
  *Found by TEA during test design.*
- **Question** (non-blocking): Plan C's run loop (Task 9) connects then reacts to frames with no
  explicit `PLAYER_SEAT` handshake, yet `protocol.seat_frame` exists (159-4) and design spec
  Section 3 describes a Seat step. Confirm the server auto-seats the companion on connect; if not,
  the loop + a test need a SEAT step, otherwise `seat_frame` is dead code (No Stubbing).
  Affects `src/companion/run.py`, `src/companion/protocol.py`. *Found by TEA during test design.*
- **Question** (non-blocking): Plan C's `_chargen_choice` maps a non-ACT / empty brain decision to
  `"0"` (first option) — a "never stall chargen" degradation that borders on a silent fallback
  (SOUL *No Silent Fallbacks*). I did NOT test this branch to avoid locking in contested behavior;
  Reviewer/Dev should confirm intent or fail loud + log on unexpected chargen decisions.
  Affects `src/companion/run.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the ADR-134 token-ledger cost guard is deferred (per Plan C
  Self-Review); decide-timeout + event-driven loop bound runaway, but no token ceiling. Not tested;
  recommend before unattended runs. Affects future companion work. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): pre-existing lint debt on develop — `tests/test_reconnect.py` (understudy
  test, NOT touched by 159-5) has 2 `E402` ruff errors (imports after test functions, lines 53-54),
  present on `origin/develop` (commit `1584329`). My 159-5 files are all ruff-clean; a repo-wide
  `ruff check .` reports only these 2. Left untouched per minimalist discipline. Affects
  `sidequest-understudy/tests/test_reconnect.py` (add `# noqa: E402` or hoist imports).
  *Found by Dev during implementation.*
- **Question** (non-blocking) — RESPONSE to TEA's PLAYER_SEAT finding: I implemented the loop per
  Plan C Task 9 (connect → react; the mirror takes `self_player_id` from `SESSION_EVENT{connected/
  ready}`); the loop does NOT send `PLAYER_SEAT`. `protocol.seat_frame` stays built-but-unused-by-the-
  loop (it retains its 159-4 unit tests, so not dead). The "does the server auto-seat on connect?"
  question is a LIVE-server / playtest verification, unanswerable offline — flagged for the real-server
  smoke. Affects `src/companion/run.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking — rework): HIGH functional defect — `connect_frame` sends `game_slug =
  session_url` (full ws:// URL) where the server/real-UI expect a short room slug, so the companion
  cannot join the human's `SessionRoom` (epic 159's core promise). `CompanionDef` lacks a slug field.
  Confirmed against `sidequest-ui/src/App.tsx:2310` + the `/ws` route (no path slug). 159-4 reviewer
  flagged this as blocking-for-159-5. Affects `src/companion/protocol.py`, `src/companion/manifest.py`,
  `tests/companion/test_full_loop.py`. *Found by Reviewer during code review.*
- **Conflict** (blocking — rework): 6 further confirmed findings (full detail + fixes in the Reviewer
  Assessment severity table): lang-review #3 violation (unannotated `ws` param), a misleading
  `_chargen_choice` comment, and 4 test-coverage locks (malformed-JSON propagation, chargen `"0"`
  fallback, d20 face validation, full-loop chargen-choice value).
  Affects `src/companion/ws_transport.py`, `src/companion/run.py`, `tests/companion/`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, future): the companion has no resilience to a single malformed/non-dict
  server frame — `recv` propagates the error and the run loop dies mid-session (no reconnect /
  `last_seen_seq` backfill in v1, per spec Section 5). Acceptable for offline v1, but a real table loses
  its companion to one protocol hiccup. Affects `src/companion/run.py`, `src/companion/ws_transport.py`
  (future hardening epic). *Found by Reviewer during code review.*
- **Improvement** (non-blocking, round 2): the CLI `--session` flag overrides only `session_url` (the WS
  endpoint), but the spec describes `companion play <def> --session <game_slug|url>`. With `game_slug`
  now a separate required field, an operator cannot point the companion at a different ROOM from the CLI —
  they must edit the YAML. Correct (manifest carries a valid slug) but a usability gap vs. the spec.
  Affects `src/companion/cli.py` (consider a `--game-slug` flag or clarify `--session` semantics).
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Companion full-loop wiring test placed in `tests/companion/`, not `tests/wiring/`**
  - Rationale: the standalone `sidequest-companion` repo is void (159-6); `tests/wiring/` already
  - Severity: minor
- **No `PLAYER_SEAT` handshake asserted in the run-loop tests**
  - Rationale: spec-authority hierarchy — Plan C (the concrete implementation plan for this scope)
  - Severity: minor
  - Forward impact: if the server requires an explicit seat, Dev adds the step + a covering test.
- **Rework: a new REQUIRED `game_slug` field on `CompanionDef` (room slug to join)**
  - Rationale: a companion that cannot name the human's room cannot join the session — epic 159's core
  - Severity: medium
  - Forward impact: every companion definition (YAML + any example) must now carry `game_slug`; the CLI
- **Added an `@app.callback()` to the companion CLI (not in Plan C's sample code)**
  - Rationale: a single-command Typer app collapses the subcommand, so `companion play <def>` would
  - Severity: minor
  - Forward impact: none — purely the documented CLI surface

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Companion full-loop wiring test placed in `tests/companion/`, not `tests/wiring/`**
  - Spec source: Plan C Task 11
  - Spec text: "Create ../sidequest-companion/tests/wiring/test_full_loop.py"
  - Implementation: `tests/companion/test_full_loop.py`
  - Rationale: the standalone `sidequest-companion` repo is void (159-6); `tests/wiring/` already
    holds understudy's own full-loop wiring test in the single repo, and 159-4 keeps companion tests
    under `tests/companion/`. Same test content, relocated home.
  - Severity: minor
  - Forward impact: none
- **No `PLAYER_SEAT` handshake asserted in the run-loop tests**
  - Spec source: design spec Section 3 (Data flow — Seat)
  - Spec text: "Seat — PLAYER_SEAT{character_slot} → SEAT_CONFIRMED"
  - Implementation: run-loop tests follow Plan C Task 9 (connect → react to frames); no test
    requires the loop to send `PLAYER_SEAT`.
  - Rationale: spec-authority hierarchy — Plan C (the concrete implementation plan for this scope)
    omits an explicit seat step; the spec is lower authority. Flagged as a Delivery Finding so Dev
    confirms server-side auto-seat rather than silently shipping dead `seat_frame`.
  - Severity: minor
  - Forward impact: if the server requires an explicit seat, Dev adds the step + a covering test.
- **Rework: a new REQUIRED `game_slug` field on `CompanionDef` (room slug to join)**
  - Spec source: Reviewer 159-5 HIGH finding + design spec Section 3 ("connect → SESSION_EVENT{connect,
    game_slug, ...}; Same game_slug → same SessionRoom as the human") + real client contract
    (`sidequest-ui/src/App.tsx:2310` sends `game_slug: slug`)
  - Spec text: Plan C's `CompanionDef` has no `game_slug`; `connect_frame` put `session_url` into the
    `game_slug` field ("slug is carried by the URL path server-side" — false; the `/ws` route has no slug)
  - Implementation: tests now require a REQUIRED `game_slug: str` field on `CompanionDef`, fail-loud at
    load if absent, and `connect_frame` must send `defn.game_slug` (not `session_url`)
  - Rationale: a companion that cannot name the human's room cannot join the session — epic 159's core
    promise. Required (not optional) + fail-loud-at-load honors No Silent Fallbacks; optional would let a
    companion silently fail to connect at runtime.
  - Severity: medium
  - Forward impact: every companion definition (YAML + any example) must now carry `game_slug`; the CLI
    `--session` arg semantics (`<game_slug|url>` per spec) may want a follow-up to set `game_slug` too.

### Dev (implementation)
- **Added an `@app.callback()` to the companion CLI (not in Plan C's sample code)**
  - Spec source: Plan C Task 10 (cli.py sample), design spec Section 2 ("`companion play <companion.yaml>`")
  - Spec text: Plan C's cli.py registers a single `play` command via `app.command(name="play")` with no callback
  - Implementation: added a no-op `@app.callback()` so the Typer app stays a subcommand group
  - Rationale: a single-command Typer app collapses the subcommand, so `companion play <def>` would
    parse `play` as the manifest argument ("Got unexpected extra argument(s)"). The callback preserves
    the spec's intended `companion play <def>` UX. Mirrors understudy's own `cli.py` (`@app.callback()` +
    `understudy run`). Plan C's sample was buggy on this point; I honored the spec's intent.
  - Severity: minor
  - Forward impact: none — purely the documented CLI surface

### Reviewer (audit)
- **TEA: full-loop wiring test in `tests/companion/` not `tests/wiring/`** → ✓ ACCEPTED by Reviewer:
  sound — the standalone `sidequest-companion` repo is void (159-6) and `tests/wiring/` holds
  understudy's own wiring test; `tests/companion/` is the established home (159-4). Same content, right place.
- **TEA: no `PLAYER_SEAT` handshake asserted in the run-loop tests** → ✓ ACCEPTED by Reviewer:
  spec-authority is correct (Plan C Task 9 omits an explicit seat step; the mirror takes `self_player_id`
  from `SESSION_EVENT{connected/ready}`). The "does the server auto-seat on connect?" question is a
  genuine live-server matter, properly carried as a Delivery Finding for the real-server smoke — not a
  blocker for offline v1. `seat_frame` retains its 159-4 unit tests, so it is not dead code.
- **Dev: added an `@app.callback()` to the companion CLI (not in Plan C's sample)** → ✓ ACCEPTED by
  Reviewer: correct and necessary — a single-command Typer app collapses the subcommand, so the spec's
  `companion play <def>` UX requires the callback. Mirrors understudy's own `cli.py`. Plan C's sample
  was buggy here; honoring the spec's intent over the literal sample is the right call.
- **No undocumented spec deviations found.** The `_chargen_choice` "0"-for-all-non-ACT behavior and the
  unannotated `ws` param are captured as Reviewer findings (comment fix + rule #3), not new deviations.
- **(Round 2) TEA: new REQUIRED `game_slug` field on `CompanionDef`** → ✓ ACCEPTED by Reviewer: correct
  and necessary — it is the fix for the HIGH connect-slug defect, matches the design spec's connect
  contract ("same game_slug → same SessionRoom") and the real client (`sidequest-ui` sends
  `game_slug: slug`). REQUIRED + fail-loud-at-load is the right call over optional (No Silent Fallbacks).
  The forward-impact note (every companion YAML must carry it; `--session` can't override game_slug) is
  accurate and carried as a non-blocking delivery finding.

## Sm Assessment

**Scope.** Final story of epic 159 (Companion Seat — full-PC AI companion over WS). Builds the
companion's run loop, WebSocket transport, CLI entrypoint, and full-loop wiring that ties the
already-built package core into a runnable seat. 4pts, p2, tdd (phased).

**Dependencies — all satisfied:**
- 159-4 (DONE) — companion package core: intent, manifest, persona, dice, protocol, brain, actuation. This story wires those parts into a loop.
- 159-3 (DONE) — server companion bond + perception seam. The companion client connects to this existing server seam; 159-5 is the client side of the loop.
- 159-6 (DONE) — seat_core relocated in-tree into sidequest-understudy. No `../sidequest-seat-core` path dependency exists anywhere.

**Repo correction (SM action).** The story's `repos` field was stale: `sidequest-companion` —
a target the 159-4 owner ruling (2026-06-26) declared VOID. Corrected to **sidequest-understudy**
via targeted yq edit (single-line diff, structure preserved). This is not a new decision — the
owner already ruled: ONE REPO (sidequest-understudy), MULTIPLE PACKAGES. The companion ships as a
SIBLING package inside sidequest-understudy, alongside seat_core and understudy.

**Package-boundary invariant (load-bearing for implementation).** The companion imports the
in-tree **seat_core** package directly. It does **NOT** depend on the **understudy** (test-harness)
package — the "companion must not depend on the test harness" constraint is honored at the PACKAGE
boundary, not the repo boundary. TEA/Dev: keep companion imports off `understudy.*`.

**Design references:**
- docs/superpowers/specs/2026-06-25-companion-seat-design.md
- docs/superpowers/plans/2026-06-25-companion-C-companion-package.md
- docs/superpowers/plans/2026-06-25-companion-epic-breakdown.md

**Routing.** tdd is phased → next phase **red**, owner **tea** (Amos Burton). Merge gate was clear
at setup (0 in progress, 0 in review). Branch `feat/159-5-companion-run-loop-transport-cli-wiring`
created in sidequest-understudy.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 4pt feature story (run loop, WS transport, CLI, full-loop wiring) — behavior must be
locked before implementation.

**Scope mapping.** 159-4 already landed the companion package CORE (intent, manifest, persona, dice,
protocol, brain, actuation — 47 passing tests). 159-5 is the remaining trio from Plan C
(`docs/superpowers/plans/2026-06-25-companion-C-companion-package.md`): Task 9 (run loop), Task 10
(WS transport + CLI), Task 11 (full-loop wiring). Tests are written against the **actual** landed
159-4 APIs, not the plan's idealized signatures (the plan predates the 159-4/159-6 repackaging).

**Test Files (all RED):**
- `tests/companion/test_run.py` — the `run_companion` event loop: connect-first, plays a turn,
  answers DICE/CONFRONTATION/FATE_DEFEND prompts, ignores non-self turns, exits on closed transport
  AND on `SESSION_EVENT{ended}` (never plays a post-ended turn), slow-brain → YIELD (never stalls),
  typed signature. (11 tests)
- `tests/companion/test_ws_transport.py` — `WebSocketTransport`: JSON encode on send, dict decode on
  recv, `None` on `websockets.ConnectionClosed`, and a non-close error PROPAGATES (no broad swallow).
  (4 tests)
- `tests/companion/test_cli.py` — `companion play <def.yaml> [--session URL]`: exit 2 on
  missing/invalid manifest (fail loud at the boundary), `--session` override, manifest default.
  (3 tests)
- `tests/companion/test_full_loop.py` — **load-bearing wiring test**: drives the real `run_companion`
  through connect → chargen scene → play turn → dice request → session end with a fake brain + a
  scripted fake server; asserts the full outgoing frame sequence incl. bond metadata on connect.
  (1 test)
- `tests/companion/test_cli_packaging.py` — distribution-surface wiring: `websockets` declared +
  pinned; `companion = "companion.cli:app"` console-script entry. (2 tests)

**Tests Written:** 21 tests covering the 3 ACs implied by the title (run loop / WS transport+CLI /
full-loop wiring), defined here since the sprint YAML carried none.
**Status:** RED — 4 files fail at collection (missing `companion.run`/`companion.cli`/
`companion.ws_transport`/`websockets`), 1 file fails on clean assertions (packaging). Pre-existing
47 companion tests still pass — no regression. Verified via testing-runner (RUN_ID `159-5-tea-red`).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing | `test_ws_transport::test_recv_does_not_swallow_unexpected_errors` | failing (RED) |
| #3 type annotations at boundary | `test_run::test_run_companion_has_typed_signature` | failing (RED) |
| #6 test quality | self-check (below) | n/a |
| #9 async/await pitfalls | `test_run::test_slow_brain_yields_and_does_not_stall`, `test_exits_cleanly_on_closed_transport` | failing (RED) |
| #11 input validation @ CLI boundary | `test_cli::test_play_rejects_missing_manifest` | failing (RED) |
| #12 dependency hygiene (pinned) | `test_cli_packaging::test_websockets_dependency_declared_and_pinned` | failing (RED) |

**Rules N/A this diff:** #2 (helpers use `None` defaults, no mutable defaults), #4 (no logging module
in scope — Dev may add error-path logging; flagged), #5 (paths via `pathlib` already), #7 (the WS
adapter wraps the socket with `async with` in CLI `play()`; recv/send don't leak), #8 (`json.loads`
on TRUSTED server frames — loud-fail on malformed is the intended contract-drift tripwire per spec
Section 5), #10 (no star imports; 159-4's `test_packaging::test_companion_source_does_not_import_understudy`
guards import hygiene), #13 (meta — Dev re-scans fix diffs in GREEN).

**Rules checked:** 6 of the applicable lang-review rules have dedicated test coverage.
**Self-check:** 0 vacuous tests; 1 test strengthened — `test_exits_cleanly_on_closed_transport` got
an explicit `assert` so it is not a "calls a function with no assertion" smell (#6).

**Handoff:** To Dev (Naomi Nagata) for GREEN. Implement `companion/run.py`, `companion/ws_transport.py`,
`companion/cli.py`; add `websockets>=12` + the `companion` script entry to `pyproject.toml` and
`uv sync`. See Delivery Findings for the two open Questions (PLAYER_SEAT handshake, chargen fallback).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-understudy):**
- `src/companion/run.py` (new) — `run_companion(defn, transport, brain, *, rng=None)`: the event-driven
  run loop. Sends `connect_frame` first; on `CHARACTER_CREATION{scene}` answers in persona; on a
  `DICE_REQUEST`/`CONFRONTATION`/`FATE_DEFEND_REQUEST` prompt or a `TURN_STATUS` where it's my seat,
  runs the BOUNDED `companion.brain.decide` (so a slow/broken brain degrades to YIELD — never stalls)
  then `actuate`s + sends. Exits on a closed transport (`recv()→None`) or `SESSION_EVENT{ended}`.
- `src/companion/ws_transport.py` (new) — `WebSocketTransport`: JSON-encodes on `send`, decodes on
  `recv`, returns `None` on `websockets.ConnectionClosed` (clean loop exit), and lets any other error
  propagate (no broad swallow).
- `src/companion/cli.py` (new) — `companion play <def.yaml> [--session URL]` Typer app; fail-loud
  exit-2 on a missing/invalid manifest; `--session` overrides `session_url`. Added `@app.callback()`
  to keep `play` a subcommand (see Design Deviations).
- `pyproject.toml` — added `websockets>=12` to `[project.dependencies]` and
  `companion = "companion.cli:app"` to `[project.scripts]`.
- `uv.lock` — `uv sync` (resolved `websockets 16.0`).

**Tests:** companion suite **67/67 passing** (47 pre-existing 159-4 + 20 new 159-5). Full understudy
suite **193/193 passing** — no regressions. Verified via testing-runner (RUN_ID `159-5-dev-green`)
plus a confirming `uv run pytest -q`.

**Lint:** `ruff check` on all five 159-5 files — clean. (A repo-wide `ruff check .` reports 2 `E402`
errors in `tests/test_reconnect.py`, pre-existing on develop and untouched by 159-5 — see Delivery
Findings.)

**Branch:** `feat/159-5-companion-run-loop-transport-cli-wiring` (pushed to origin).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review. Two open Questions to adjudicate:
the chargen `"0"` fallback (kept per Plan C) and the unused-by-loop `seat_frame` (PLAYER_SEAT is a
live-server question). Pre-existing `test_reconnect.py` E402 lint debt flagged, not fixed (scope).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (193/193 green, 159-5 files lint-clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4, dismissed 0, deferred 2 (low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1, dismissed 0, deferred 2 (low) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 violation (17 rules, 62 instances) | confirmed 1 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 7 confirmed (6 from subagents + 1 reviewer-found HIGH via the 159-4 sidecar lead:
the `connect_frame` `game_slug` = URL defect, verified against `sidequest-ui` + the `/ws` route),
0 dismissed, 4 deferred (low, non-blocking)

## Rule Compliance

Exhaustive check against `.pennyfarthing/gates/lang-review/python.md` (13 rules) + SOUL/CLAUDE
additional rules, cross-referenced with reviewer-rule-checker (62 instances examined):

- **#1 silent exceptions** — COMPLIANT. `ws_transport.recv` (ws_transport.py:22-26) catches only
  `websockets.ConnectionClosed`→None; `json.loads` is OUTSIDE the `try` so JSONDecodeError propagates.
  `cli.py:41-45` catches `ManifestError` specifically, re-raises `typer.Exit(2) from exc`.
- **#2 mutable defaults** — COMPLIANT. Only defaults are `rng=None`, `session=None` (immutable).
- **#3 type annotations at boundaries** — **VIOLATION** (1): `WebSocketTransport.__init__(self, ws)`
  at ws_transport.py:15 — `ws` is unannotated on a public `__init__`. All other boundaries
  (`run_companion`, `send`/`recv` return, `play`, `play_cmd`) are annotated.
- **#4 logging** — N/A (no module imports logging; CLI uses `typer.echo` for user output).
- **#5 path handling** — COMPLIANT (`pathlib.Path`; `read_text(encoding="utf-8")` in tests).
- **#6 test quality** — COMPLIANT for what's present (24 instances, all meaningful assertions; the
  `wait_for` guards are genuine non-hang assertions). Coverage GAPS noted as findings (not vacuous).
- **#7 resource leaks** — COMPLIANT (`async with websockets.connect(...)` in `play()`).
- **#8 unsafe deserialization** — COMPLIANT (`json.loads` on TRUSTED server frames; no pickle/eval/yaml).
- **#9 async pitfalls** — COMPLIANT (all coroutines awaited; bounded decide; no blocking calls in the diff).
- **#10 import hygiene** — COMPLIANT (explicit imports, no star, no cycles; companion never imports understudy).
- **#11 input validation @ CLI boundary** — COMPLIANT (`load_companion` fail-loud → exit 2 before socket).
- **#12 dependency hygiene** — COMPLIANT (`websockets>=12` pinned per project lower-bound convention).
- **#13 fix-regressions** — N/A (new code, not a fix).
- **SOUL No-Silent-Fallbacks / Never-Stall / Act-only-for-self** — COMPLIANT (the `"0"` chargen
  fallback is documented never-stall degradation; decide is timeout-bounded at all 3 sites; only
  own-action frames emitted). The `_chargen_choice` COMMENT is inaccurate though (see findings).

## Devil's Advocate

Assume this companion is broken. A malformed server frame that is valid JSON but **not a dict** —
say a bare JSON array — sails past `ws_transport.recv` (it only guards `ConnectionClosed`), then
`mirror.apply(frame)` calls `frame.get(...)` and the run loop calls `frame.get("type")` on a `list`
→ `AttributeError`, which propagates and **kills the companion mid-session**. That's "loud" per spec
Section 5, but it's untested and there is no reconnect/backfill in v1, so one bad frame ends the
companion with no graceful degrade — a real human's table loses its Donut to a single protocol hiccup.
A **non-JSON text frame** hits the same fate via `json.loads` raising `JSONDecodeError` — and *that
propagation path is not covered by any test*, despite the module docstring promising "any other error
propagates." A **confused brain during chargen** that returns `ROLL`/`BEAT`/`DEFEND` (wrong context)
is silently mapped to `"0"` — the companion picks the first character-creation option it never
intended, a quiet cousin of the SOUL *Test* violation (acting without choosing), and the comment
actively hides this by naming only `YIELD`. The decide-timeout protects the loop, but `make_brain(model)`
is constructed **synchronously inside the async `play()`** — a real backend that does blocking I/O at
construction would stall the event loop before the loop ever starts (brain.py is out of scope, but the
seam is here). There is **no cost ceiling** (ADR-134) — an unattended companion pointed at a live
session bills per turn with no hard stop. And the unannotated `ws` param means a wrong object handed
to `WebSocketTransport` fails only at the first `await`, deep in the loop, not at construction. None of
these are data-corruption or security holes — but the malformed-frame fragility and the silent
wrong-context chargen mapping are exactly the "ships to a real table" reliability seams that deserve a
test lock and an honest comment before merge.

## Reviewer Assessment

**Verdict:** REJECTED

**Rationale:** There IS a High-severity functional defect — the companion cannot join the human's live
session because the connect frame carries the wrong room identifier (full URL where the server expects a
short slug). The feature is "wired" only against a fake server that never checks it; against a real
server it fails its single purpose. On top of that: a confirmed, **non-dismissable** project-rule
violation (lang-review #3), a materially misleading comment in a No-Silent-Fallbacks-sensitive spot, and
unverified reliability behaviors. Per the blocking rule (any High → REJECT) and this project's "fix what
you see, don't defer" doctrine, these are addressed now, in-story.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][EDGE] | **Companion cannot join the human's room.** `connect_frame` sets `game_slug = defn.session_url` (full `ws://...` URL), but the real client (`sidequest-ui/src/App.tsx:2310`, `ConnectScreen.tsx:411`) sends `game_slug` = a short room slug, and the `/ws` route carries NO path slug (so the frame comment "slug is carried by the URL path server-side" is false). The companion would fail to join the human's `SessionRoom` — the core promise of epic 159 ("same game_slug → same room"). `CompanionDef` has no slug field to source it from. The full-loop test passes only because the fake server never validates `game_slug`. 159-4 reviewer flagged this as "blocking-for-159-5"; 159-5 is the story that takes the connect frame live, so it owns the fix. | `src/companion/protocol.py` (`connect_frame`), `src/companion/manifest.py` (`CompanionDef` needs a `game_slug`/room-slug field), `tests/companion/test_full_loop.py` (fake server / wiring test must assert a valid slug) | Add a room-slug field to `CompanionDef` (e.g. `game_slug`) and have `connect_frame` send THAT, not `session_url`. Add a wiring assertion that the connect frame's `game_slug` is the room slug, not the URL. Verify the exact contract against the server's connect handler / `sidequest-ui` connect. |
| [MEDIUM][RULE] | `WebSocketTransport.__init__(self, ws)` — `ws` param unannotated; violates lang-review #3 (public `__init__` boundary). Confirmed by reviewer-rule-checker; cannot dismiss (matches stated rule). | `src/companion/ws_transport.py:15` | Annotate `ws` — e.g. `ws: ClientConnection` (`from websockets.asyncio.client import ClientConnection`), or a minimal `Protocol` with async `send`/`recv` so the `_FakeWS` test double type-checks. |
| [MEDIUM][DOC] | `_chargen_choice` comment is misleading: names only `YIELD`, but ALL non-ACT kinds (ASIDE/ROLL/BEAT/DEFEND) fall through to `"0"`; and "empty decision" (ACT w/o text) is a state Pydantic forbids (`intent.py:34`). Hides that a wrong-context intent silently picks the first option. | `src/companion/run.py:91-96` | Rewrite the comment to state: forward ACT prose verbatim; ANY other kind maps to `"0"` (first option) so chargen always completes. |
| [MEDIUM][TEST] | `ws_transport.recv` malformed-JSON propagation untested — the docstring's "any other error propagates" contract is only half-verified (close→None and ValueError-from-recv are tested; a successful recv returning non-JSON → `json.JSONDecodeError` is not). | `tests/companion/test_ws_transport.py` | Add a test: `_FakeWS(incoming=["not json"])` → `recv()` raises (JSONDecodeError/ValueError). |
| [MEDIUM][TEST] | `_chargen_choice` `"0"` never-stall fallback branch untested — only the ACT path is exercised. The documented "chargen always completes" invariant has no lock. | `tests/companion/test_run.py` | Add a test: chargen scene + a YIELD/Slow brain → sent `CHARACTER_CREATION` payload `choice == "0"`. |
| [LOW][TEST] | `test_plays_turn_then_throws_then_exits` asserts `DICE_THROW` present but not the d20 face count/range (other dice tests do; full_loop does cover d20 faces). | `tests/companion/test_run.py:84` | Assert `len(faces)==1 and 1<=faces[0]<=20`. |
| [LOW][TEST] | `test_full_loop` checks `CHARACTER_CREATION` presence but not the choice value (covered at unit level by `test_chargen_scene_answered_in_persona`). | `tests/companion/test_full_loop.py` | Assert the sent chargen `choice == "Show cat, OBVIOUSLY."`. |

**Verified good (evidence):**
- [VERIFIED] `ws_transport.recv` catches only `ConnectionClosed`→None; `json.loads` outside `try` → other errors propagate — ws_transport.py:22-26; confirmed by `test_recv_does_not_swallow_unexpected_errors`. Complies #1. [SILENT]/[RULE]-domain self-covered (those subagents disabled).
- [VERIFIED] `run_companion` exits on closed transport AND `SESSION_EVENT{ended}` before consuming more — run.py:40-46; confirmed by the two exit tests. No hang.
- [VERIFIED] decide is timeout-bounded via `defn.decide_timeout_s` at all 3 call sites — run.py:51,61,73; confirmed by `test_slow_brain_yields_and_does_not_stall`. Never stalls the table.
- [VERIFIED] CLI fails loud (exit 2) on bad manifest BEFORE opening a socket; socket via `async with` — cli.py:41-47, 32. Complies #11, #7.
- [VERIFIED] `websockets>=12` declared+pinned, `companion` console-script registered — pyproject.toml:13,17. Complies #12 + wiring mandate.

**Data flow traced:** `companion play donut.yaml --session URL` → `load_companion` (fail-loud) →
`play()` opens `async with websockets.connect` → `WebSocketTransport(ws)` →
`run_companion(defn, transport, make_brain(model))` → loop: `recv` JSON → `mirror.apply` → on my-turn /
prompt → bounded `decide` → `actuate` → `send` JSON. Exercised end-to-end by `test_full_loop` with fakes.

**Subagent tags:** [TEST] (analyzer, confirmed 4) · [DOC] (comment-analyzer, confirmed 1) ·
[RULE] (rule-checker, confirmed 1) · [EDGE]/[SILENT]/[TYPE]/[SEC]/[SIMPLE] — subagents disabled via
`workflow.reviewer_subagents`; domains self-covered in Rule Compliance + Devil's Advocate above.

**Handoff:** Back to TEA (Amos Burton) for red rework — the bundle includes missing-edge-case tests
(routes to red→tea). The two code fixes (annotate `ws`; correct the `_chargen_choice` comment) land in
the subsequent green. All items are small and in-story; nothing deferred.

## TEA Assessment (Rework Round 1)

**Tests Required:** Yes — reviewer REJECTED with testable findings.
**Status:** RED — 50 passed, 22 failed (verified via testing-runner RUN_ID `159-5-tea-red-rework`).
All 22 failures trace to the two intended fronts; no unexpected pass/fail.

**Tests added/strengthened (drive the reviewer's required fixes):**
- `test_protocol.py::test_connect_frame_game_slug_is_room_slug_not_url` (NEW) — the HIGH fix: asserts
  `connect_frame` sends `game_slug == defn.game_slug` and `!= defn.session_url`. Drives BOTH a required
  `CompanionDef.game_slug` field AND the `connect_frame` change (stop using `session_url`).
- `test_manifest.py::test_missing_game_slug_fails_loud` (NEW) + `test_load_valid` now asserts
  `d.game_slug` — forces `game_slug` REQUIRED, fail-loud at load.
- `test_full_loop.py` — wiring now asserts the connect frame's `game_slug` is the room slug (not the URL)
  AND the chargen `choice` value is the brain's actual answer (not a silent fallback).
- `test_ws_transport.py::test_init_ws_param_is_annotated` (NEW) — lang-review #3 lock: fails until the
  `ws` param is annotated.
- `test_ws_transport.py::test_recv_propagates_malformed_json` (NEW) — closes the recv contract triple
  (close→None, other-error→propagate, malformed-JSON→propagate). Passes already (regression lock).
- `test_run.py::test_chargen_falls_back_to_first_option_when_brain_yields` (NEW) — locks the never-stall
  `"0"` degradation. `test_plays_turn` now validates the d20 face count/range.
- All `CompanionDef` fixtures (kwargs in test_run/test_protocol/test_full_loop; YAML in
  test_manifest/test_persona/test_cli) updated to carry `game_slug` — so the RED is coherent and GREEN
  is clean (no surprise breakage when the required field lands).

### Rule Coverage (rework)

| Rule | Test(s) | Status |
|------|---------|--------|
| #3 type annotations | `test_ws_transport::test_init_ws_param_is_annotated` | failing (RED) |
| #1 silent exceptions | `test_ws_transport::test_recv_propagates_malformed_json` | passing (lock) |
| SOUL No-Silent-Fallbacks | `test_manifest::test_missing_game_slug_fails_loud` (game_slug required) | failing (RED) |
| epic-159 core (join human's room) | `test_protocol::test_connect_frame_game_slug_is_room_slug_not_url`, `test_full_loop` connect assertion | failing (RED) |

**Self-check:** 0 vacuous tests. The game_slug contract test asserts both equality-to-slug AND
inequality-to-URL (proves the bug is actually fixed, not just that a field exists).

**Delivery findings (rework):** No NEW upstream findings beyond what the Reviewer already logged.

**Handoff:** To Dev (Naomi Nagata) for GREEN. Required fixes: (1) add a REQUIRED `game_slug: str` field
to `CompanionDef` (`manifest.py`); (2) `connect_frame` sends `defn.game_slug`, not `defn.session_url`,
and fix the false "slug is carried by the URL path" comment (`protocol.py`); (3) annotate the `ws` param
on `WebSocketTransport.__init__` (`ws_transport.py`); (4) correct the misleading `_chargen_choice`
comment (`run.py`). Then all 22 reds flip green; re-run the full suite for regressions.

## Dev Assessment (Rework Round 1)

**Implementation Complete:** Yes — all 6 reviewer findings addressed.

**Files Changed (sidequest-understudy):**
- `src/companion/manifest.py` — `CompanionDef` gains a REQUIRED `game_slug: str` (the human's room
  slug). Absent → pydantic ValidationError → wrapped as `ManifestError` by `load_companion` (fail-loud
  at load, before any socket). Fixes the HIGH defect's data side.
- `src/companion/protocol.py` — `connect_frame` now sends `defn.game_slug` (not `defn.session_url`), so
  the companion lands in the human's `SessionRoom`. Replaced the false "slug is carried by the URL path"
  comment with an accurate one (the `/ws` route has no path slug; the server reads game_slug from the payload).
- `src/companion/ws_transport.py` — annotated the `ws` param via a minimal `_WSConnection` `Protocol`
  (async `send(str)`/`recv()->str`), satisfying lang-review #3 and structurally typing both the real
  `websockets` connection and the test double. (One of the two annotation options the Reviewer offered.)
- `src/companion/run.py` — corrected the `_chargen_choice` comment to state that ALL non-ACT kinds
  (YIELD/ASIDE/ROLL/BEAT/DEFEND) map to `"0"`, not just YIELD; dropped the impossible "empty decision".

**Tests:** companion suite **72/72 passing** (67 + 5 rework). Full understudy suite **198/198 passing**
— no regressions. All 22 round-1 reds flipped green. My 4 changed src files are ruff-clean.

**No new deviations** beyond those already logged (the `game_slug`-required field — TEA; the
`@app.callback()` — Dev round 1). The `_WSConnection` Protocol is a Reviewer-offered option, not a
spec deviation.

**Delivery findings (rework):** No new upstream findings during rework.

**Branch:** `feat/159-5-companion-run-loop-transport-cli-wiring` (pushed, commit `2a595a3`).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review. The HIGH connect-slug defect is fixed and
locked (contract test asserts `game_slug == defn.game_slug != session_url`); rule #3, the chargen
comment, and the four coverage locks are all green.

## Subagent Results (Re-review Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (72/72 + 198/198 green, lint clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (both low) | confirmed 0, dismissed 0, deferred 2 (low, non-blocking) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (low) | dismissed 1 (unreachable per intent.py:34 validator) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | error | API connection closed mid-response | self-covered (4 fix sites read directly) |

**All received:** Yes (3 enabled returned, 1 enabled errored → self-covered, 5 disabled pre-filled)
**Total findings:** 0 confirmed blocking, 1 dismissed (with rationale), 2 deferred (low, non-blocking)

## Reviewer Assessment (Re-review Round 2)

**Verdict:** APPROVED

**Round-1 findings — all resolved (verified):**
- [HIGH][EDGE] connect-slug defect — **FIXED.** `CompanionDef.game_slug: str` is REQUIRED (no default,
  `manifest.py:31`); `connect_frame` sends `defn.game_slug` (`protocol.py:28`), not `session_url`.
  Double-locked: `test_connect_frame_game_slug_is_room_slug_not_url` (asserts `== game_slug` AND
  `!= session_url` — a field-only fix would still fail) + `test_full_loop` connect assertion +
  `test_missing_game_slug_fails_loud` (proves fail-loud-at-load).
- [MEDIUM][RULE] `ws` unannotated — **FIXED.** `ws: _WSConnection` (`ws_transport.py:24`); the new
  `_WSConnection` Protocol (async `send(str)`/`recv()->str`) is sound and its own methods are annotated.
  Locked by `test_init_ws_param_is_annotated`.
- [MEDIUM][DOC] `_chargen_choice` comment — **FIXED.** Now enumerates all non-ACT kinds → "0"; the
  impossible "empty decision" claim is gone (`run.py:92`).
- [MEDIUM/LOW][TEST] four coverage locks — **CLOSED** (malformed-JSON propagation, chargen "0"
  fallback, d20 faces, full-loop chargen-choice value). Test-analyzer confirmed each is non-vacuous.

**New findings this round (none blocking):**
- [DOC] (dismissed): comment-analyzer flagged that `_chargen_choice`'s comment ignores an
  "ACT-with-empty-text → 0" path. **Dismissed** — `intent.py:34`'s validator (`ACT/ASIDE require text`)
  makes an ACT intent with empty text unconstructible, so the path is unreachable and the comment is
  accurate for every constructible intent.
- [TEST] (low, deferred): `test_init_ws_param_is_annotated` checks annotation-present, not that it is
  `_WSConnection` specifically. Adequate for lang-review #3 (which requires params be annotated, not a
  particular type). Non-blocking; optional strengthening.
- [TEST] (low, deferred): CLI tests don't assert `game_slug` survives a `--session` override.
  `model_copy(update={"session_url": session})` touches only `session_url`, so it's correct-but-untested.
  Non-blocking; recorded as a delivery finding.

**Rule Compliance (re-verified; rule-checker errored → self-covered):** #1 silent-exceptions — recv
still catches only `ConnectionClosed`→None, else propagates (ws_transport.py:33). #3 annotations — all
boundaries annotated incl. the previously-bare `ws`. SOUL No-Silent-Fallbacks — `game_slug` required,
fail-loud at load. #8 — `json.loads` on trusted frames unchanged. No new violations from the rework
(the required field + extra=forbid interact correctly; the Protocol is type-only).

### Devil's Advocate (Round 2)

Assume the rework broke something. The newly-REQUIRED `game_slug` means every companion YAML an author
writes must now include it — a future hand-authored `donut.yaml` that omits it fails loud at load
(correct, but it's a new authoring burden; no shipped example exists yet to verify). The real residual:
the spec's CLI is `companion play <def> --session <game_slug|url>`, but `play_cmd` overrides only
`session_url` via `model_copy(update={"session_url": session})` — it cannot override `game_slug`. So an
operator who wants to point the companion at a DIFFERENT room than the manifest names has no CLI lever;
they must edit the YAML. That's a usability gap against the spec's `<game_slug|url>` intent, though not
a correctness bug (the manifest still carries a valid slug). The `_WSConnection` Protocol narrows to
text frames (`str`); if the server ever sent a binary frame, `recv()` would return `bytes` — but
`json.loads` accepts `bytes` in modern Python, so no break. The connect frame now carries the correct
slug SHAPE, but the *live* server contract (does it accept `companion_of`/`relationship` alongside
`game_slug`?) remains unexercised offline — the same deferred real-server-smoke item, not newly broken.
No malformed-frame resilience still (recv propagates, loop dies) — already logged as a future-hardening
finding. Nothing here rises to blocking; the one actionable residual (CLI can't set game_slug) is
recorded as a non-blocking delivery finding.

**Verified good:** [EDGE] connect carries room slug (protocol.py:28, double-locked). [SILENT] recv
close→None / else-propagate intact (ws_transport.py:30-35). [TEST] all six locks non-vacuous
(test-analyzer confirmed). [DOC] both round-1 comments corrected (comment-analyzer confirmed).
[RULE] #3 satisfied (ws annotated). [TYPE]/[SEC]/[SIMPLE] — subagents disabled; self-covered, no
concerns (type-only Protocol, no auth/secrets surface, no added complexity). 198/198 full suite green.

**Data flow re-traced:** `companion play donut.yaml` → `load_companion` (fail-loud incl. missing
game_slug) → `play()` `async with websockets.connect(session_url)` → `WebSocketTransport(ws)` →
`run_companion` → `connect_frame` now sends `game_slug` (the room) so the companion joins the human's
SessionRoom → loop. The HIGH defect's path is now correct end-to-end (offline-verifiable parts).

**Handoff:** To SM (Camina Drummer) for finish.