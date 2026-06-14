# F2d — Deterministic Opponent AI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Story:** 116-3 · **Epic:** 116 (ADR-144 F2) · **Branch base:** `develop` (gitflow) · **Repo:** `sidequest-server`
**Decision of record:** ADR-144 (Fate Core binding replaces the native ruleset).
**Decomposition:** `docs/superpowers/plans/2026-06-14-f2-narrator-intent-router-integration.md` (slice F2d).
**Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.5, §5 (epic F2), §6 (OTEL).
**Depends on:** F1c (`run_fate_exchange`, `seal_fate_commit`, `_resolve_attack`, `FateSealedCommit`) + F2a — **both merged.**

---

## 1. Goal

A live Fate conflict today is **half-alive**: F1c's exchange rolls **reactive defense only**. `run_fate_exchange` walks the seated actors and, at `fate_conflict.py:324-328`, **skips any opponent slot with no sealed commit** ("Reactive defense only"). The module header (`fate_conflict.py:10`) states plainly: *"Opponent actions are committed by the F2 narrator (F1c authors no opponent AI)."* The consequence: **an opponent can only defend and be taken out — it can never attack, never threaten the player, never win.** A Fate conflict cannot be lost.

F2d closes that gap with a **deterministic** opponent AI (no LLM call, mirroring WN's `_resolve_opponent_reprisal` at `dice.py:2011`): at the top of every exchange walk, each undefeated opponent that has no sealed commit gets one **decided, rolled, and sealed** — so when the walk reaches its slot, `_resolve_attack` fires and a PC takes stress / consequences / is taken out. Every decision emits `fate.opponent.decided` (the GM-panel polygraph — *Bind the Ruleset, the opponent's choice is mechanical, not improvised*).

**Non-goals (this slice):** opponent `create_advantage` / `overcome` / aspect-invocation (attack is the keystone threat; the others don't drive taken-out). Opponent fate-point spends. LLM-driven opponent personality. These are flagged in §7, not silently dropped.

## 2. Architecture — one engine entry, two tiers

```
dispatch_fate_action (F1d, unchanged)
  → PCs seal via seal_fate_commit; barrier closes
  → run_fate_exchange(...)                       fate_conflict.py:283
       → _seat_opponent_commits(...)   ◀── NEW   seat every undefeated, uncommitted opponent
       │    for each opponent:
       │      decision = decide_opponent_action(...)   game/fate_opponent.py  (PURE — no rng, no I/O)
       │      outcome  = ruleset.resolve_action(...)    roll 4dF + skill (same call PCs use, dispatch_fate_action:660)
       │      seal_fate_commit(action=attack, target=PC, ladder_total=..., dice=...)
       │      fate_opponent_decided_span(...)           NEW span
       → fate_exchange_committed_span(...)       now includes the opponent(s)
       → fate_turn_order / walk                  _resolve_attack fires on the opponent's slot → PC takes stress
```

**Why the top of `run_fate_exchange`, not inside `dispatch_fate_action`'s barrier-closed branch:**
- `run_fate_exchange` is the **single** place an exchange resolves. Seating opponents there means they appear in `fate.exchange.committed`, `fate.exchange.order`, and the walk — one coherent telemetry story.
- `commits = {c.actor: c for c in encounter.fate_commits}` is built at line 315; seating before line 304 means the committed-span (304-305), the order span (308-313), and the commits dict all see the opponent. Inserting in `dispatch_fate_action` would leave the committed-span blind to opponents.
- `fate_barrier_closed` is **PC-side only** (`fate_waiting_actors` skips non-PC actors, `fate_conflict.py:128-131`), so sealing opponent commits never disturbs the barrier.

**Why split `decide` (game tier) from `seat/roll/seal` (dispatch tier):** the heuristic is a pure function of state — `decide_opponent_action` takes `(encounter, snapshot, opponent, mental)` and returns an `OpponentDecision | None` with **no rng, no rolling, no sealing**. That makes the heuristic exhaustively unit-testable without dice, and keeps the dice/seal orchestration in `fate_conflict.py` next to the PC path it mirrors. Same separation as `decide`-vs-`resolve` elsewhere in the engine.

## 3. The heuristic (§7.3 resolved — deterministic, no LLM)

`decide_opponent_action(*, encounter, snapshot, opponent, mental) -> OpponentDecision | None`

**Target selection** (first match wins; every tiebreak is deterministic seating order — `encounter.actors` order):
1. A live (`not withdrawn`) **player-side** PC who **already holds a consequence on the conflict track** this fight (read `core.fate_sheet` consequence slots for `track = mental if mental else physical`) — finish the most-pressured target.
2. Else the PC who **attacked this opponent this exchange** (scan `encounter.fate_commits` for a commit with `action == "attack"` and `target == opponent.name`) — answer the aggressor (the WN "taunter" analog, `dice.py` reprisal targeting).
3. Else the **highest-threat** live PC — the PC with the highest rating in the conflict-track attack skill (`Fight` physical / `Provoke` mental). Tiebreak: seating order.
4. Else the first live player-side PC in seating order.
5. If **no** live player-side PC exists → return `None` (the side is cleared; `_maybe_resolve_side_cleared` will end it — do not seat a phantom attack).

**Action:** always `"attack"` this slice (the keystone threat). Documented extension in §7.

**Skill:** the opponent's best conflict-track attack skill from its `fate_sheet.skills` — `max` over the physical attack skills (`Fight`, `Shoot`) for a physical conflict, the social attack skills (`Provoke`) for a mental one. If the sheet has none rated, fall back to the track's canonical attack skill at rating 0 (an unskilled swing still rolls 4dF — faithful to Fate; **not** a silent skip). Pick the skill name deterministically (defined order, highest rating first, then declaration order).

**Roll & seal** (in `_seat_opponent_commits`, not the pure fn): identical to the PC path at `dispatch_fate_action:659-683` —
```python
rating = opp_core.fate_sheet.skills.get(decision.skill, 0)
outcome = ruleset.resolve_action(
    skill_rating=rating,
    opposition=Opposition(value=0, kind="active"),   # target named ⇒ active; defense rolled at resolution
    rng=rng,
    actor=opponent.name,
    _tracer=_tracer,
)
seal_fate_commit(
    encounter=encounter, actor=opponent, action="attack", skill=decision.skill,
    target=decision.target, ladder_total=outcome.ladder_total, dice=outcome.dice,
)
fate_opponent_decided_span(
    actor=opponent.name, action="attack", skill=decision.skill,
    target=decision.target, ladder_total=outcome.ladder_total, _tracer=_tracer,
)
```
`rng` is the exchange's threaded `random.Random` — opponent rolls are **resume-safe and deterministic given the seed** (project rule: no `Math.random`-style nondeterminism in the engine path).

**Idempotency / safety rails (No Silent Fallbacks):**
- Only opponents with **no existing commit** are seated (a future narrator-committed opponent is respected; `seal_fate_commit` raises `FateConflictError` on a double-commit — never swallow it).
- Only `side == "opponent"` and `not withdrawn`.
- An opponent with **no `fate_sheet`** raises `FateConflictError` (a seated opponent in a Fate conflict must have a sheet — same loudness as `_resolve_attack:430`).

## 4. Shared surface

| Surface | File | New / changed |
|---|---|---|
| `OpponentDecision` dataclass + `decide_opponent_action` | `sidequest/game/fate_opponent.py` | **new module** |
| `_seat_opponent_commits` helper + call at `run_fate_exchange` top | `sidequest/server/dispatch/fate_conflict.py` | changed |
| `fate_opponent_decided_span` + `SPAN_ROUTES["fate.opponent.decided"]` | `sidequest/telemetry/spans/fate.py` | new span |
| Decision unit tests | `tests/game/test_fate_opponent.py` | new |
| Seat/roll/seal + exchange wiring tests | `tests/server/dispatch/test_fate_opponent_seating.py` | new |
| Span route test | `tests/telemetry/test_fate_opponent_decided_span.py` | new |

**No import-time registration.** `decide_opponent_action` is called directly from `run_fate_exchange` — it is **not** registered in the dispatch bank or any registry. Therefore **no subprocess registry test is required** (the `import-sideeffect-registry-wiring-needs-subprocess-test` rule applies only to import-time `_register_*` side effects; this slice has none). The wiring proof is the OTEL-span-driven exchange test in §6.

## 5. OTEL — the new span

`fate.opponent.decided` joins the live Fate inventory (spec §6). Mirror `fate_taken_out_span` exactly (emit fn + `SPAN_ROUTES` entry, `component="fate"`, `event_type="state_transition"`):

| Attribute | Source |
|---|---|
| `actor` | opponent name |
| `action` | `"attack"` |
| `skill` | chosen skill |
| `target` | PC named |
| `ladder_total` | the opponent's rolled 4dF + skill |

Fires **once per opponent seated per exchange**. The GM panel reads it to confirm the opponent's swing was an engine decision, not narrator improvisation.

---

## Task 1 — The pure heuristic (`game/fate_opponent.py`)

- [ ] **Step 1: Write the failing test** — `tests/game/test_fate_opponent.py`. Construct a `StructuredEncounter` + `GameSnapshot` fixture (reuse the F1c test fixtures in `tests/server/dispatch/test_fate_conflict.py` as the pattern — real `FateSheet`s, seated `EncounterActor`s) and assert each heuristic branch with **no dice**:
  - (a) targets the PC holding a physical consequence over an unwounded PC;
  - (b) with no consequence, targets the PC whose `fate_commits` entry attacked this opponent;
  - (c) with neither, targets the highest-`Fight` PC; seating-order tiebreak on equal ratings;
  - (d) returns `None` when every player-side actor is `withdrawn`;
  - (e) picks the opponent's highest-rated attack skill; mental conflict (`mental=True`) selects `Provoke`, physical selects `Fight`/`Shoot`.
- [ ] **Step 2: Run test to verify it fails** (`uv run pytest tests/game/test_fate_opponent.py -n0`).
- [ ] **Step 3: Implement `decide_opponent_action` + `OpponentDecision`** per §3. Pure: params `(*, encounter, snapshot, opponent, mental)`, returns `OpponentDecision(action="attack", skill, target) | None`. No `rng`, no imports from `server.dispatch`, no `seal_*`. Read consequences off `core.fate_sheet`; read skills off `fate_sheet.skills`. Define the physical/mental attack-skill name lists as module constants next to `_DEFENSE_SKILL`/`_ORDER_SKILL`'s conventions.
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Commit** — `feat(fate): F2d — deterministic opponent action heuristic (decide_opponent_action)`.

## Task 2 — The span (`telemetry/spans/fate.py`)

- [ ] **Step 1: Write the failing test** — `tests/telemetry/test_fate_opponent_decided_span.py`: emit via a real `InMemorySpanExporter` (mirror `tests/telemetry/test_fate_action_classified_span.py`), assert the span name `fate.opponent.decided` and its attributes; assert `SPAN_ROUTES["fate.opponent.decided"]` exists and its `extract` maps `actor/action/skill/target/ladder_total`.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Add `fate_opponent_decided_span` + the `SPAN_ROUTES` entry** mirroring `fate_taken_out_span` (lines 375-388) and `SPAN_ROUTES["fate.taken_out"]` (279-288). Place the route literal beside the other Fate routes; place the emit fn beside the other `fate_*_span` fns. (Literal key — the routing-completeness lint inspects `SPAN_*` module constants only, same note as F2a's `fate.action.classified`.)
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Commit** — `feat(fate): F2d — fate.opponent.decided OTEL span + route`.

## Task 3 — Seat opponents in the exchange (`fate_conflict.py`)

- [ ] **Step 1: Write the failing wiring test** — `tests/server/dispatch/test_fate_opponent_seating.py`. Drive the **real** registered `FateRulesetModule` + a real `InMemorySpanExporter` (the F1c wiring-test shape) through `dispatch_fate_action`:
  - **(1) End-to-end threat:** a one-PC-vs-one-opponent conflict; the PC seals an `attack` that closes the barrier; assert after `run_fate_exchange` that (i) `fate.opponent.decided` fired for the opponent, (ii) the opponent appears in the `fate.exchange.committed` span's `committed_actors`, and (iii) the targeted PC's physical stress/consequence state changed **or** the PC is `withdrawn` (taken out) — i.e. the opponent actually threatened. Seed the `rng` so the opponent's roll lands a hit.
  - **(2) Respects a pre-committed opponent:** pre-seal an opponent commit, run the exchange, assert `decide_opponent_action` was **not** re-applied (exactly one commit for that opponent; no `FateConflictError`).
  - **(3) Cleared side:** all PCs withdrawn → no opponent is seated, no `fate.opponent.decided`, exchange resolves via `_maybe_resolve_side_cleared`.
  - **(4) Determinism:** same seed ⇒ identical opponent target/skill/`ladder_total` across two runs.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Add `_seat_opponent_commits(*, encounter, snapshot, ruleset, rng, mental, _tracer)`** in `fate_conflict.py` per §3 (roll via `ruleset.resolve_action`, seal via `seal_fate_commit`, emit `fate_opponent_decided_span`). Call it at the **top of `run_fate_exchange`, before line 304** (the committed-span). Derive `mental = encounter.category == "social"` once and pass it down (it's already computed at line 307 — hoist it above the seating call). Loop `[a for a in encounter.actors if a.side == "opponent" and not a.withdrawn]`, skip any already in the commits set, `decide` → skip if `None` → roll → seal → span.
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Prove the reactive-only path is preserved for the no-opponent case** — extend or assert against an existing F1c test: a PC-vs-PC (no `opponent`-side actor) exchange seats nothing and behaves exactly as before (no `fate.opponent.decided`). Run the full F1c suite `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0` — **0 diffs** (F1c regression-clean, the WN-doctrine bar: we add the opponent path, we do not alter the existing walk).
- [ ] **Step 6: Commit** — `feat(fate): F2d — seat deterministic opponent attacks at exchange open (closes inert-opponent gap)`.

## Task 4 — Final verification

- [ ] **Step 1: Lint changed files (scoped)** — `uv run ruff check sidequest/game/fate_opponent.py sidequest/server/dispatch/fate_conflict.py sidequest/telemetry/spans/fate.py tests/game/test_fate_opponent.py tests/server/dispatch/test_fate_opponent_seating.py tests/telemetry/test_fate_opponent_decided_span.py`.
- [ ] **Step 2: Format changed files (scoped)** — `uv run ruff format` the same set (project trap: `ruff format --check` is ungated — run it before completing).
- [ ] **Step 3: Type check** — `uv run pyright` on the changed modules; 0 errors.
- [ ] **Step 4: Run the Fate + exchange suites** — `uv run pytest tests/game/test_fate_opponent.py tests/server/dispatch/test_fate_conflict.py tests/server/dispatch/test_fate_opponent_seating.py tests/telemetry/test_fate_opponent_decided_span.py -n0`.
- [ ] **Step 5: Full sweep** — `uv run pytest` (set `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS`; baseline-compare any failure — a failure not in the recorded develop baseline is a regression, not "pre-existing").
- [ ] **Step 6: Commit any fixups.**

---

## 6. Test strategy (per server CLAUDE.md)

- **No source-text wiring tests.** Every wiring claim is proven by **driving the real path and asserting an OTEL span or a state mutation** — never `read_text()` on a source file. Task 3's test fires `dispatch_fate_action` through the real registry and asserts `fate.opponent.decided` + a PC stress mutation.
- **Determinism is a first-class assertion** (Task 3 step (4)) — the engine path must be resume-safe; same seed ⇒ same opponent decision and roll.
- **F1c regression bar = 0 diffs** — F2d *adds* the opponent-seating step; it does not retune the reactive walk. (SOUL: *Bind the Ruleset, Don't Balance It* — we are completing the engine, not balancing native mechanics against it.)

## 7. Open / deferred (flagged, not dropped)

1. **Opponent `create_advantage` / `overcome` / aspect-invoke.** This slice commits `attack` only — the action that produces taken-out. A richer opponent (set up an advantage, then attack into it; invoke a situation aspect it benefits from) is a clean follow-up (`F2d-2` or folded into F2c's narration work). It rides the same `_seat_opponent_commits` seam — `decide_opponent_action` returns a different `action`/`aspect_text`; the existing `_resolve_create_advantage` walk already handles it. **No engine change needed, only a heuristic extension.**
2. **Opponent fate-point economy.** Opponents don't spend fate points to invoke here. Deferred with F2b/F1b's invoke surfacing — the opponent invoke-bonus path would mirror `dispatch_fate_action:644-653`.
3. **Multi-opponent ordering.** Each undefeated opponent is seated independently; `fate_turn_order` already interleaves them with PCs by initiative skill. No special multi-opponent logic this slice (the loop handles N opponents; each picks its own target via the §3 heuristic).
4. **Concede-to-the-player.** An opponent never concedes here (concede earns fate points and is a player-agency move). A losing opponent is taken out by the walk, or yields via the existing disposition path (`opponents_disposition`, `encounter.py:380`). Out of scope.

## 8. Done when

- A seeded one-PC-vs-one-opponent Fate conflict can **take the PC out** — the opponent attacks, the PC's stress/consequences absorb or fail, `fate.taken_out` can fire against a PC.
- `fate.opponent.decided` fires once per undefeated, uncommitted opponent per exchange, visible on the GM panel.
- `decide_opponent_action` is pure and exhaustively unit-tested; the seat/roll/seal path is wiring-tested through the real dispatch; F1c suite is 0-diff; full sweep green against baseline.
