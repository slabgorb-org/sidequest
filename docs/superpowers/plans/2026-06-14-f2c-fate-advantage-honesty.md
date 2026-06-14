# F2c — Create-Advantage Rendering + Fate Honesty Lie-Detector — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Story:** 116-4 · **Epic:** 116 (ADR-144 F2) · **Branch base:** `develop` (gitflow) · **Repo:** `sidequest-server`
**Decomposition:** `docs/superpowers/plans/2026-06-14-f2-narrator-intent-router-integration.md` (slice F2c).
**Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.5, §5, §6 (OTEL).
**Depends on:** F1c (`situation_aspects`, `_resolve_create_advantage`, `narrator_hints`, `fate.aspect.created`/`fate.taken_out` spans) + F2a + **F2b (story 116-2)** for the prompt-section seam this renders into — F1c/F2a merged; **F2b must merge first** (this story is `depends-on 116-2`).

---

## 1. Goal

Two gaps remain after F2b:
1. **Create-advantage is invisible in the prose.** `_resolve_create_advantage` (fate_conflict.py:550-592) appends a situation aspect and fires `fate.aspect.created`, and on **failure** it appends a `narrator_hint` — but on **success it appends no hint** (fate_conflict.py:578-580). So the engine silently places "**Pinned Down (2 free invokes)**" and the narrator never hears about it. F2c surfaces created situation aspects into the prompt + narration so the advantage is rendered honestly.
2. **The narrator can lie about Fate outcomes with zero mechanical backing.** This is the exact failure the GM-panel lie-detector exists to catch (CLAUDE.md OTEL principle; cf. the F2a improvised-combat watcher). F2c adds a **`fate_engagement_watcher`** mirroring `dispatch_engagement_watcher`: when the prose claims a Fate outcome (an advantage created, a foe taken out) that the engine state does not show, it emits `fate.narration.mismatch`.

## 2. Architecture — mirror the existing watcher (CLAUDE.md "Don't Reinvent")

```
run_fate_exchange (F1c) → _resolve_create_advantage appends situation_aspect + fate.aspect.created
   ◀── NEW: append a SUCCESS narrator_hint ("X created advantage: <aspect> (N free invokes)")
                                                   so encounter_render.py:44-45 surfaces it to the prompt

build_narrator_prompt → the F2b fate_state section + encounter narrator_hints (encounter_render.py:44-45)
   ◀── NEW: ensure live situation_aspects render as in-play scene aspects (honest "what's true now")

post-narration (websocket_session_handler.py:1141-1157, beside run_dispatch_engagement_watcher
                and run_improvised_combat_watcher)
   ◀── NEW: run_fate_engagement_watcher(narration=, package=, snapshot=, tracer=)
              → detect_fate_narration_mismatch(narration, snapshot, package) -> list[FateNarrationMismatch]   (PURE)
              → emit fate.narration.mismatch per mismatch                                                       (wrapper, non-fatal)
```

**The watcher reads STATE, not a span buffer** (verified): `dispatch_engagement_watcher` and the F2a `run_improvised_combat_watcher` derive evidence from `snapshot` (+ the prose text + the `DispatchPackage`), NOT from an OTEL span record — spans are for the GM panel only. So `detect_fate_narration_mismatch` compares **narration claims** against **authoritative snapshot state**: `encounter.situation_aspects`, the `withdrawn` flags on `encounter.actors`, and `encounter.fate_commits` — exactly how `run_improvised_combat_watcher` reads `narration` + `snapshot.encounter`.

**The template** (verified, mirror exactly):
- Pure: `detect_dispatch_engagement_mismatch(*, package, snapshot) -> list[DispatchMismatch]` (dispatch_engagement_watcher.py:371-410); per-witness `_check_*_engaged(dispatch, snapshot, player_id) -> str | None`; `@dataclass(frozen=True) DispatchMismatch{subsystem, idempotency_key, dispatched_type, evidence}`.
- Wrapper: `run_dispatch_engagement_watcher(*, package, snapshot, tracer=None) -> None` — calls the pure fn, emits one span per mismatch, **non-fatal** (try/except → watcher-crashed span; a watcher must never break a turn).
- Wired post-narration at websocket_session_handler.py:1141-1157, **after** `_apply_narration_result_to_snapshot` (1129-1134), beside the improvised-combat watcher (which already takes `narration=`).

## 3. Detection rules (the honesty check)

`detect_fate_narration_mismatch(*, narration: str, snapshot: GameSnapshot, package: DispatchPackage | None) -> list[FateNarrationMismatch]`. Gated to fate-bound packs / an active Fate encounter (no-op otherwise — like the other watchers' early returns). Two witnesses this slice:

1. **`create_advantage` claim vs state.** If the prose asserts a *new advantage/aspect was created* (a small, conservative phrase set — "create an advantage", "creates the aspect", "now <Aspect>", "gains the advantage"; keep the matcher tight and documented, mirroring the improvised-combat injury-marker approach), then `encounter.situation_aspects` must contain a matching aspect (and/or the turn's `fate_commits` includes a resolved `create_advantage`). If the prose names an advantage that is **not** in `situation_aspects`, emit a mismatch (`subsystem="create_advantage"`, evidence = the claimed text + "no matching situation aspect in state").
2. **`taken_out` claim vs state.** If the prose asserts a participant was *taken out / defeated / drops / is out of the fight*, then some `encounter.actors` entry must be `withdrawn` (the F1c taken-out flag). If the prose claims a foe is out but **no** actor is withdrawn, emit a mismatch (`subsystem="taken_out"`).

Keep witnesses **conservative** (false-positives erode trust in the lie-detector): match only clear claims, prefer to under-flag. Each witness is a pure `_check_*(narration, snapshot) -> str | None` returning an evidence string or `None`, exactly like the dispatch witnesses.

**Why state, not spans:** the engine's authoritative truth is the snapshot mutation (`situation_aspects`, `withdrawn`), which is durable and present post-apply; spans are ephemeral GM-panel signals. This matches every existing watcher and the explicit "ground-truth is state-derived" finding for this codebase.

## 4. OTEL

New span: **`fate.narration.mismatch`** (spec §6) — mirror `dispatch_engagement_mismatch_span` + its `SPAN_ROUTES` entry (telemetry/spans/...). Attributes: `subsystem` (`create_advantage` | `taken_out`), `claim` (the prose evidence), `reason`. `event_type="state_transition"`, `component="fate"` (or the watcher's component, matching the dispatch-engagement route). Literal key, no `SPAN_*` constant (the F2a/F2d precedent). Fires once per detected mismatch. This is the F2 lie-detector anchor the GM panel reads.

Live spans this slice **fires/honors, not redefines:** `fate.aspect.created`, `fate.taken_out` (F1c).

---

## Task 1 — Create-advantage success rendering (close the silent-success gap)

- [ ] **Step 1: Write the failing test** — extend `tests/server/dispatch/test_fate_conflict.py` (or a new `tests/server/dispatch/test_fate_create_advantage_render.py`): a resolved `create_advantage` with shifts>0 appends a **success** `narrator_hint` naming the created aspect + its free-invoke count (today only failure appends a hint — fate_conflict.py:578-580 success path appends none). Assert the hint text reaches `encounter.narrator_hints` and that `render_encounter_summary` (encounter_render.py:44-45) includes it. Drive the real `run_fate_exchange`; assert state, not source text. **F1c regression bar: the existing create-advantage tests stay green** — you are ADDING a success hint, not changing the resolution math.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** — in `_resolve_create_advantage`, on success append `hints.append(f"{commit.actor} created an advantage: {aspect.text} ({free} free invoke(s)).")` mirroring the failure-hint style already there. (Pure rendering — no resolution-math change; the situation aspect + `fate.aspect.created` span already fire.)
- [ ] **Step 4: Run test to verify it passes** + run the full F1c suite `tests/server/dispatch/test_fate_conflict.py` → green (0 behavior diffs to the walk math).
- [ ] **Step 5: Surface live situation aspects honestly** — confirm (test) that current `encounter.situation_aspects` are visible to the narrator prompt as in-play scene aspects (via the F2b `fate_state` section's `scene_aspects` and/or the encounter summary). If F2b already renders `scene_aspects` from `_build_fate_summary`, this is an assertion, not new code; if a gap remains (e.g. boosts not surfaced), close it minimally here.
- [ ] **Step 6: Commit** — `feat(fate): F2c — render create-advantage success into narrator hints + scene aspects`.

## Task 2 — `fate_engagement_watcher` (the honesty lie-detector)

- [ ] **Step 1: Write the failing test** — `tests/agents/test_fate_engagement_watcher.py` (mirror `tests/agents/test_dispatch_engagement_watcher.py`: pure-function tests + an `InMemorySpanExporter` span test + a wiring test). Cover:
  - **pure, create_advantage:** narration claims an advantage that is NOT in `encounter.situation_aspects` → one `FateNarrationMismatch(subsystem="create_advantage")`; narration claims one that IS present → no mismatch.
  - **pure, taken_out:** narration claims a foe is out while no actor is `withdrawn` → mismatch; claim matches a withdrawn actor → none.
  - **conservative matcher:** ordinary combat-flavor prose with no explicit create/taken-out claim → no mismatch (guard against false positives).
  - **non-fate / no-encounter:** the watcher is a no-op (early return).
  - **span:** `run_fate_engagement_watcher` emits `fate.narration.mismatch` (real exporter) per mismatch and is **non-fatal** on an internal error (mirror the dispatch watcher's try/except — a raised exception inside emits a crashed span, never propagates).
  - **wiring:** the watcher is invoked from the post-narration path (drive a fixture turn / assert the span fires through the real handler seam — NOT a source grep).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** — `sidequest/agents/fate_engagement_watcher.py`: `@dataclass(frozen=True) FateNarrationMismatch{subsystem, claim, reason}`; pure `detect_fate_narration_mismatch(*, narration, snapshot, package)` with `_check_create_advantage_claim(...)` and `_check_taken_out_claim(...)` witnesses (each `-> str | None`); wrapper `run_fate_engagement_watcher(*, narration, package, snapshot, tracer=None) -> None` that emits `fate.narration.mismatch` per mismatch, wrapped non-fatally. Add the `fate.narration.mismatch` span emit fn + `SPAN_ROUTES` entry (mirror `dispatch_engagement_mismatch_span`).
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Wire it** — in `websocket_session_handler.py` (the 1141-1157 block, beside `run_improvised_combat_watcher`), add `run_fate_engagement_watcher(narration=getattr(result, "narration", "") or "", package=turn_context.dispatch_package, snapshot=snapshot)`. The Step-1 wiring test proves this seam fires.
- [ ] **Step 6: Commit** — `feat(fate): F2c — fate_engagement_watcher emits fate.narration.mismatch (GM-panel lie-detector)`.

## Task 3 — Final verification

- [ ] **Step 1: Lint** — `uv run ruff check` on all changed files.
- [ ] **Step 2: Format check** — `uv run ruff format --check` on the changed set.
- [ ] **Step 3: Type check** — `uv run pyright` on the changed source; 0 errors.
- [ ] **Step 4: Fate + watcher suites** — `SIDEQUEST_DATABASE_URL=... uv run pytest -n0 -q tests/agents/test_fate_engagement_watcher.py tests/server/dispatch/test_fate_conflict.py tests/agents/test_dispatch_engagement_watcher.py tests/telemetry/ -k "fate or engagement"`.
- [ ] **Step 5: Full sweep** — `SIDEQUEST_DATABASE_URL=... SIDEQUEST_GENRE_PACKS=... uv run pytest`; baseline-compare. Confirm the existing dispatch-engagement + improvised-combat watchers still pass (you added a sibling, didn't alter them).
- [ ] **Step 6: Commit any fixups.**

## 5. Test strategy

- **No source-text wiring tests.** The watcher's wiring is proven by **driving the post-narration seam and asserting the `fate.narration.mismatch` span fires** on a fabricated-lie fixture; the rendering is proven by asserting `narrator_hints` / prompt content.
- **False-positive discipline.** A lie-detector that cries wolf is worse than none. Tests explicitly include benign prose that must NOT flag; witnesses err toward under-flagging.
- **Non-fatal contract.** A test forces an internal watcher error and asserts the turn survives (crashed-span, no propagation) — the dispatch watcher's contract.
- **F1c walk unchanged.** Task 1 only adds a success hint; the resolution math is untouched (regression suite green).

## 6. Open / deferred (flagged, not dropped)

1. **Richer claim matching.** This slice covers create-advantage and taken-out claims with a conservative matcher. Claims about invoke/compel/concede outcomes are deferred — add witnesses incrementally as playtest surfaces narrator lies (the GM panel will show which `fate.narration.mismatch` subsystems are missing).
2. **Auto-correction.** F2c *detects and reports* a mismatch (GM-panel visibility); it does not rewrite the prose. Narrator self-correction (re-prompt on mismatch) is a separate, larger concern — out of scope.
3. **Per-turn aspect delta.** Detection compares prose claims to current `situation_aspects` (claim-vs-state). A stricter "created **this turn**" check (pre/post snapshot delta of `situation_aspects`) is a possible hardening if claim-vs-state proves too loose in playtest — flagged, not built.

## 7. Done when

- A successful create-advantage produces a narrator hint naming the aspect + free invokes, and live situation aspects are honestly visible to the narrator.
- `fate_engagement_watcher` emits `fate.narration.mismatch` when prose claims an advantage/taken-out the engine state doesn't show, is wired post-narration beside the existing watchers, is non-fatal, and does not false-positive on benign prose.
- All gates green; full sweep clean against baseline; existing watchers unaffected.
