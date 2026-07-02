---
story_id: "161-2"
jira_key: ""
epic: "161"
workflow: "tdd"
---
# Story 161-2: Produce companion-seat brain telemetry (server + understudy)

## Story Details
- **ID:** 161-2
- **Title:** Produce companion-seat brain telemetry (server + understudy): seat_core DecideResult enrichment (parse the claude -p envelope tokens/cost), companion run-loop timing + outcome emit via the existing /internal/watcher/emit bridge, and a server session_slug+severity passthrough
- **Jira Key:** (none — Jira integration not enabled)
- **Points:** 3
- **Workflow:** tdd
- **Priority:** p2
- **Repos:** understudy, server (CROSS-REPO)
- **Stack Parent:** 161-1 (DESIGN/ADR-154, status: done)

## Technical Approach

**Per 161-1 Approach C:** Companion-seat brain telemetry self-reports via the existing `/internal/watcher/emit` bridge (mirroring daemon's `watcher_bridge.py`), NOT via native claude -p OTEL at :55801.

### Part (a): seat_core DecideResult Enrichment

**Location:** `sidequest-understudy/src/understudy/brain/seat_core.py`

Enrich `DecideResult` class to carry:
- `model`: backend model identifier
- `tokens_input`: token count (cache-aware for claude-p, real for anthropic/ollama)
- `tokens_output`: output token count
- `tokens_cache`: cache tokens (claude-p context reuse)
- `cost_usd`: real cost (claude-p notional subscription cost, anthropic/ollama metered)

**claude_p envelope parsing** (`brain/claude_p_model.py` line ~60):
- Current behavior: hardcodes `tokens_input=0, tokens_output=0, cost_usd=0` from the JSON envelope's `usage` field
- Required: extract and store real values from the JSON response:
  ```
  {
    "usage": {
      "input_tokens": ...,
      "output_tokens": ...,
      "cache_creation_input_tokens": ...,
      "cache_read_input_tokens": ...,
      ...
    },
    "total_cost_usd": ...
  }
  ```
- Apply to all backends: claude_p (JSON envelope) + anthropic (native) + ollama (pass through)
- Default/fail-safe: 0 tokens if parsing fails (never block the decision)

### Part (b): Companion Run Loop Telemetry Emit

**Location:** `sidequest-understudy/src/understudy/companion/run.py`

Per-decision cycle:
1. **Timing:** Record `start_time` before `await decide()`, calculate `duration_ms`
2. **Outcome:** Derive from DecideResult + any exceptions:
   - `outcome`: "YIELD" (assistant chose to hold) vs "act" (performed an action)
   - `intent_kind`: the decision's intent category
   - `degraded`: boolean (set true if timed out or errored)
   - `timed_out`: boolean (distinguish timeout from other errors)
3. **Tagging:** Assemble record with:
   - `session_slug`: from `defn.game_slug` (session identifier)
   - `seat`: from `defn.name` (seat identifier)
   - `role`: from DefnRole enum (pet/peer/hireling)
   - `species`: companion species
   - `owner`: player who owns/controls the companion
4. **Bridge emit:** Call new `understudy_watcher_bridge` module (see part c infrastructure)
   ```python
   companion_brain_decide_event = {
     "component": "companion_brain",
     "event_type": "companion_brain_decide",
     "severity": "info" if not degraded else "warning",
     "session_slug": session_slug,
     "fields": {
       "seat": seat,
       "role": str(role),
       "species": species,
       "owner": owner,
       "outcome": outcome,
       "intent_kind": intent_kind,
       "degraded": degraded,
       "timed_out": timed_out,
       "backend": model_backend,
       "model": model_name,
       "duration_ms": duration_ms,
       "tokens": tokens_input + tokens_output,
       "cost_usd": cost_usd,
     }
   }
   emit_watcher_event(companion_brain_decide_event)
   ```

**Error resilience (fail-loud-non-fatal):**
- If emit fails: log WARNING with context, continue the turn (never break companion's move)
- Timed-out or errored decisions: still emit with `degraded=true, severity=warning` (silence is not acceptable for lie-detector)

### Part (c): Server Bridge for session_slug + severity Passthrough

**Location 1 — understudy bridge module:** `sidequest-understudy/src/understudy/telemetry/watcher_bridge.py` (NEW, mirrors daemon's implementation)

New module to POST companion_brain_decide events to the server's `/internal/watcher/emit` endpoint:
- Uses `stdlib requests.post()` or `httpx`
- URL: `http://localhost:8765/internal/watcher/emit` (configurable, env `SIDEQUEST_SERVER_URL`)
- Timeout: 2 seconds
- Headers: `Content-Type: application/json`
- Payload: WatcherEmitPayload (see server changes below)
- Error handling:
  ```python
  try:
    response.raise_for_status()
  except Exception as e:
    logger.warning(
      f"Companion brain telemetry emit failed (session={session_slug}, seat={seat}): {e}",
      exc_info=True
    )
    # Never re-raise; turn continues
  ```
- Reference: `sidequest-daemon/src/sidequest_daemon/telemetry/watcher_bridge.py` (2026-05-25 implementation)

**Location 2 — server modifications:** `sidequest-server/sidequest/protocol/protocol.py` + `sidequest/server/watcher.py`

Modify `WatcherEmitPayload` (protocol definition):
```python
class WatcherEmitPayload(BaseModel):
  component: str  # e.g., "companion_brain", "narrator", "daemon_renderer"
  event_type: str  # e.g., "companion_brain_decide", "narrator_turn"
  severity: Optional[str] = None  # "info", "warning", "error" (default: from ContextVar)
  session_slug: Optional[str] = None  # session identifier override
  fields: dict  # event-specific fields
```

Modify `publish_event()` in `sidequest/server/watcher.py`:
```python
def publish_event(
  component: str,
  event_type: str,
  fields: dict,
  severity: Optional[str] = None,
  session_slug: Optional[str] = None,
) -> None:
  """
  Publish a watcher event to the hub.
  
  Args:
    session_slug: explicit session identifier override (beats ContextVar)
    severity: explicit severity level (beats ContextVar)
  
  If both are None, fall back to ContextVar (existing behavior, no change to daemon or in-process callers).
  """
  # Explicit override beats ContextVar
  _session_slug = session_slug or _get_session_slug_from_context()
  _severity = severity or _get_severity_from_context()
  
  # ... rest of publish_event logic
```

**Backward compatibility:** Existing in-process callers and daemon bridge unchanged (default `None` preserves ContextVar behavior).

## Acceptance Criteria

1. **seat_core enrichment:** DecideResult carries model, input/output/cache tokens, and cost_usd; claude_p parses these from the JSON envelope (no more hardcoded zeros); anthropic and ollama fill real values

2. **companion emit breadth:** companion run loop emits one companion_brain_decide event per decision with fields: seat, role, species, owner, outcome, intent_kind, degraded, timed_out, backend, model, duration_ms, tokens, cost_usd — tagged with session_slug

3. **degraded resilience:** Timed-out or errored decisions still emit, with degraded=true and severity=warning (silence is not acceptable for a lie-detector)

4. **server passthrough:** server /internal/watcher/emit accepts optional session_slug + severity and forwards to publish_event; existing callers and the daemon bridge are unaffected (default None preserves ContextVar behavior)

5. **emit non-fatal:** emit failures are logged at WARNING and never break the companion's turn (fail-loud-non-fatal, mirrors watcher_bridge.py)

6. **wiring test:** a fake-brain companion decision produces a companion_brain_decide watcher event on the hub with correct session_slug + seat + role (behavior/OTEL assertion, not source-text grep)

## SM Assessment

**Verdict:** Ready for RED. Clean, well-scoped 3-pt story on a solid foundation.

**Why this is ready:**
- Predecessor 161-1 (DESIGN/ADR-154, Approach C) is **done** — the design decision is settled: understudy self-reports via the existing `/internal/watcher/emit` bridge, mirroring the daemon's `watcher_bridge.py`. This is a PRODUCE story executing an approved design, not net-new design.
- Cross-repo scope is clear and separable: understudy owns (a) `seat_core` DecideResult enrichment + `claude_p_model.py` envelope parsing and (b) the companion run-loop emit + new bridge module; server owns (c) the `WatcherEmitPayload`/`publish_event` optional `session_slug`+`severity` passthrough.
- Backward-compat contract is explicit: server change defaults to `None`, preserving ContextVar behavior for every existing in-process caller and the daemon — TEA should assert this non-regression, not just the new path.

**Caveats for TEA (Amos) — read before writing RED:**
1. **Verify paths/line numbers against the live tree.** The technical approach above cites specifics (`claude_p_model.py:60`, `WatcherEmitPayload` in `protocol/protocol.py`, `publish_event` in `server/watcher.py`). These are the setup pass's *inference*, not verified. Grep the actual locations first — the hardcoded-zeros site and the real `WatcherEmitPayload`/`publish_event` definitions may live elsewhere. Do not encode a wrong path into a test.
2. **AC #6 is the load-bearing test.** Per project doctrine (OTEL Observability Principle) the wiring test must be a **behavior/OTEL assertion on the hub** — a fake-brain companion decision produces a real `companion_brain_decide` event carrying correct `session_slug` + `seat` + `role`. Source-text grep does NOT satisfy this AC. This is the lie-detector; it is the point of the story.
3. **The degraded/timed-out path (AC #3) must emit, not swallow.** A timeout or backend error still fires an event with `degraded=true, severity=warning`. Silence on failure is a test failure — cover the error path explicitly.
4. **Emit is fail-loud-non-fatal (AC #5):** a bridge POST failure logs WARNING and the companion's turn continues. Test both halves — the WARNING log AND that the exception never propagates out of the run loop.

**Routing:** Phased TDD → handing off to **tea** for the RED phase. Sequence: RED (Amos) → GREEN (Naomi) → REVIEW (Avasarala) → FINISH (me).

**Stale-YAML note for Bossmang:** `sprint/epic-161.yaml` records `repos: understudy` for this story; it is genuinely cross-repo (server + understudy per AC #4). Session records the correct repos. `pf sprint story update` has no `--repos` flag, so the YAML field remains stale — finish flow reads repos from this session, so it's non-blocking.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (10 failing + 3 non-regression guards green) — verified by testing-runner, zero test-file bugs.

**Ground-truth correction (the setup paths were largely wrong — Camina flagged it):**
- Companion uses **`src/seat_core/core.py::DecideResult`** (`value/input_tokens/output_tokens`), NOT `understudy/brain/core.py` (a different DecideResult with an `intent` field). Part (a) targets `seat_core`.
- Hardcoded zeros: `seat_core/llm/claude_p_model.py:60`. Backends: `seat_core/llm/{anthropic,ollama,claude_p}_model.py`.
- `src/companion/run.py` **does** exist (`run_companion(defn, transport, brain, *, rng)`); `companion/brain.py::decide()` is the single `asyncio.wait_for` chokepoint but currently discards the DecideResult and swallows timeout-vs-error.
- Server: `WatcherEmitPayload` at `server/app.py:43`, handler `watcher_emit` at `app.py:314`, `publish_event` at `telemetry/watcher_hub.py:729` (already has `severity=`; derives slug from the `current_session_slug()` ContextVar — part c adds the `session_slug` override).
- Daemon template: `sidequest-daemon/sidequest_daemon/telemetry/watcher_bridge.py` (no `src/`).

**Test Files:**
- `sidequest-understudy/tests/seat_core/test_decide_result_enrichment.py` — AC #1: DecideResult gains `cache_tokens/model/cost_usd`; claude_p parses the envelope usage + `total_cost_usd` (no more zeros) and defaults to 0 when absent (never crashes); anthropic/ollama report `model`; ollama cost is a real 0.0.
- `sidequest-understudy/tests/companion/test_telemetry.py` — parts b/c: the NEW `companion.telemetry` bridge posts `{event_type, fields, component, session_slug, severity}` to `/internal/watcher/emit`, swallows URLError/ConnectionError with a WARNING (fail-loud-non-fatal), honors `SIDEQUEST_SERVER_URL`, typed signature.
- `sidequest-understudy/tests/companion/test_brain_telemetry.py` — AC #2/#3/#5/#6: drives the real `run_companion` spine + asserts on the bridge network boundary (behavior, not grep). Wiring (session_slug+seat+role+full field set), degraded/timed-out emit at WARNING, emit-failure-never-breaks-turn.
- `sidequest-server/tests/server/test_companion_brain_telemetry_passthrough.py` — AC #4/#6-server: `publish_event` session_slug override beats the ContextVar; endpoint forwards session_slug+severity to the hub. Asserted on the hub via `watcher_hub.publish` spy. + 2 non-regression guards.

**Tests Written:** 19 tests across 4 files covering all 6 ACs.

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing (must LOG, not silent) | `test_emit_swallows_urllib_error_and_logs_warning`, `..._connection_error...`, `test_emit_failure_never_breaks_the_companion_turn` | failing |
| #3 type annotations at boundaries | `test_emit_watcher_event_has_typed_signature` | failing |
| #4 logging coverage+correctness (network/client error → warning) | bridge swallow tests + AC #3 severity=warning | failing |
| #6 test quality (meaningful asserts, patch-where-used) | self-check: all patches target where-used (`companion.telemetry._post`, `hub_mod.watcher_hub.publish`); no vacuous asserts | pass (self) |
| #9 async pitfalls (blocking call in async loop) | flagged as Delivery Finding, NOT pinned (see below) | noted |

**Rules checked:** 4 of the applicable lang-review rules have failing test coverage; #6 self-verified; #9 flagged for Dev.
**Self-check:** 0 vacuous tests found (all new files).

**Handoff:** To Dev (Naomi) for GREEN — implement seat_core enrichment (part a), the `companion.telemetry` bridge + run-loop emit (part b), and the server session_slug/severity passthrough (part c). See Delivery Findings for the async-offload note and the two open field-derivation questions.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 173/173 passing (GREEN) — 19 new 161-2 tests + 4 server passthrough + all touched existing suites; 0 regressions. Ruff check + format clean.

**Files Changed:**

*understudy (`feat/161-2-produce-companion-brain-telemetry`):*
- `src/seat_core/core.py` — `DecideResult` gains `cache_tokens/model/cost_usd` (defaulted, so every existing 3-arg call site is unchanged).
- `src/seat_core/llm/claude_p_model.py` — parse the `claude -p` JSON envelope's `usage` + `total_cost_usd` (no more hardcoded zeros; missing fields → 0, never a crash).
- `src/seat_core/llm/anthropic_model.py` — report `model` + `cache_tokens` (input_tokens keeps summing cache for the ceiling; cost_usd stays 0.0 — see finding).
- `src/seat_core/llm/ollama_model.py` — report `model`; `cost_usd` a real 0.0 (free/local).
- `src/companion/telemetry.py` (NEW) — the understudy→server watcher bridge (stdlib urllib POST, session_slug + severity, network errors logged WARNING + swallowed).
- `src/companion/brain.py` — `decide()` times the await, distinguishes `TimeoutError` from other errors, derives outcome/degraded/timed_out, and (when `defn` is passed) emits one `companion_brain_decide` event per decision, offloaded via `asyncio.to_thread` and fully guarded.
- `src/companion/run.py` — threads `defn=defn` into all four `decide()` call sites.

*server (`feat/161-2-produce-companion-brain-telemetry`):*
- `sidequest/server/app.py` — `WatcherEmitPayload` gains optional `session_slug` + `severity`; the `/internal/watcher/emit` handler forwards them only when supplied (daemon path calls `publish_event` with its exact prior signature).
- `sidequest/telemetry/watcher_hub.py` — `publish_event` gains `session_slug` override (`slug = session_slug or current_session_slug()`); None preserves ContextVar behavior for every in-process caller.

**AC coverage:** #1 (enrichment + envelope parse) ✓ · #2 (full field set per decision) ✓ · #3 (degraded/timeout emits at WARNING) ✓ · #4 (server passthrough, daemon unaffected) ✓ · #5 (emit non-fatal) ✓ · #6 (wiring — behavior/OTEL) ✓.

**Self-review (judgment):** wired end-to-end (companion decision → bridge → server endpoint → publish_event → hub); follows the daemon `watcher_bridge.py` pattern; error handling per SOUL (fail-loud-non-fatal, never stall the table); no debug code; branches pushed.

**Branches:** `feat/161-2-produce-companion-brain-telemetry` (understudy + server), both pushed. **No PR created** (SM finish handles it).

**Handoff:** To Reviewer (Avasarala) for review. Note the one judgment call flagged below: anthropic `cost_usd` stays 0.0 (SDK reports no per-call price; claude_p is the metered path).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (253 pre-existing FastAPI `on_event` deprecations, not this diff) | confirmed 0, dismissed 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed + covered by rule-checker) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 (+1 clean) | confirmed 8, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (+6 verified accurate) | confirmed 2, dismissed 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (self-assessed + rule-checker #11) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 9 | reviewer-rule-checker | Yes | findings | 1 rule-match (LOW, mitigated) + 2 informational | confirmed 1, dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 11 confirmed (all MEDIUM/LOW, none blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Correct, wired, well-documented cross-repo work. All six ACs functionally met and verified end-to-end (two subagents independently ran both suites and confirmed the `companion_brain_decide` event actually reaches `watcher_hub.publish` — it is not a no-op). 173/173 tests green, lint + format clean. Every finding below is a **quality/coverage** improvement, not a defect — none is Critical or High, so none blocks. I confirmed (did not dismiss) all of them and downgraded the rule-match with rationale.

**Data flow traced:** a companion decision (`run_companion` → `decide(defn=defn)` → `_emit_decision` → `asyncio.to_thread(emit_watcher_event)` → `_post` → HTTP `POST /internal/watcher/emit`) → `watcher_emit` → `publish_event(session_slug, severity)` → `watcher_hub.publish`. The bridge body keys (`event_type/fields/component/session_slug/severity`) match `WatcherEmitPayload` field-for-field, so the two independently-tested halves genuinely compose. Safe: telemetry failure never propagates (bridge swallows network errors + `_emit_decision` has a belt-and-suspenders guard).

**Observations (11 confirmed + VERIFIEDs):**

- `[RULE][SILENT]` **LOW** — `decide()`'s `except asyncio.TimeoutError` (brain.py:52) and `except Exception` (brain.py:56) degrade to YIELD without any `logger` call, so the original exception's type/message is lost. *Confirmed* (matches lang-review #1/#4 — cannot dismiss a rule match). *Downgraded to LOW*: (a) pre-existing — the original `except Exception: return YIELD_INTENT` also did not log; (b) substantially mitigated — this diff now emits an OTEL `degraded=true, severity=warning` event on that path, which is the project's *preferred* visibility mechanism (OTEL doctrine, satisfies AC #3). Residual gap is exception detail only, a beyond-AC enhancement.
- `[TEST]` **MEDIUM** — value-blind field mapping at test_brain_telemetry.py:430-443: the AC#2 breadth loop asserts `key in f` but never the VALUE for `owner/backend/model/cost_usd/tokens`. The fixture's FakeStructuredModel returns all-zero/None, so four injected value bugs (wrong owner, unsplit backend, wrong model, cost=999.99) all passed. The story's deliverable IS these values; a future `_emit_decision` mapping regression would not be caught.
- `[TEST]` **MEDIUM** — the `asyncio.to_thread` offload (the non-blocking guarantee) is never proven; deleting `to_thread` leaves all 3 tests green (test_brain_telemetry.py:429).
- `[TEST]` **MEDIUM** — no test bridges seat_core enrichment (part a) → brain emit mapping (part b) with realistic non-zero values; the two halves are only tested in isolation.
- `[TEST]` **LOW** — the non-timeout degrade branch (wrong-shape value / plain Exception with `defn` supplied → degraded=True, timed_out=False) is untested; only the timeout path exercises `degraded`.
- `[TEST]` **LOW** — anthropic `cache_tokens` never exercised non-zero; dropping `cache_creation` from the sum stays green.
- `[TEST]` **LOW** — `test_emit_failure_never_breaks_the_companion_turn` exercises the bridge's swallow, NOT brain.py's own guard (URLError is caught inside the bridge first); deleting brain.py's guard causes 0 failures.
- `[TEST]` **LOW** — `test_emit_watcher_event_has_typed_signature` checks annotations are non-empty, not correct; happy-path `severity=="info"` never asserted.
- `[DOC]` **LOW** — `claude_p_model.py:1` module docstring still says "One-shot; no token metering (reported zeros)" — this diff makes the file meter real tokens/cost. Self-inflicted contradiction.
- `[DOC]` **LOW** — `app.py:315` section header frames `/internal/watcher/emit` as daemon-only; it now serves the companion too (the new inline comment at :320 is correct; the header wasn't broadened).
- `[SEC]` **LOW/informational** (self-assessed, security subagent disabled + rule-checker #11) — `companion_of` (an owner email) is emitted as a telemetry field over the localhost `/internal/watcher/emit` endpoint and persisted. Not a new class of exposure — identity already flows via `session_slug`/`player_id`/`connect_frame(companion_of)`, the endpoint is localhost-only and unauthenticated by original design, and the owner→companion binding on the GM panel is a legitimate dev-facing (Keith) datum. `severity` typed `str` (not `Literal["info","warning","error"]`) — LOW, internal endpoint.

**VERIFIEDs (evidence + rule compatibility):**
- `[VERIFIED]` async offload is correct — brain.py:107 `await asyncio.to_thread(emit_watcher_event, ...)` offloads the genuinely-blocking `urllib.request.urlopen` (telemetry.py:47) off the event loop. Complies with lang-review #9 (no blocking call in async). (The *test* doesn't prove it — see finding above — but the *code* is correct.)
- `[VERIFIED]` no circular import — `manifest ← telemetry ← brain ← run` is a strict DAG; `companion.telemetry` has zero `companion.*` imports. Complies with lang-review #10.
- `[VERIFIED][SIMPLE]` (self-assessed, simplifier disabled) no dead code / no stubbing — every new symbol has a live consumer: `emit_watcher_event`←brain, `_emit_decision`←decide, `session_slug` param←handler, the three DecideResult fields←all backends + the emit. No empty shells. Complies with SOUL No Stubbing.
- `[VERIFIED][TYPE]` (self-assessed, type-design disabled) `slug = session_slug or current_session_slug()` (watcher_hub.py) treats `""` as falsy — but `game_slug` is a required non-empty manifest field, so `""` never occurs in practice; the daemon-guard test proves the None path preserves ContextVar behavior. `DecideResult` new fields are defaulted immutables — every existing 3-arg construction is unchanged. Complies with backward-compat contract (AC #4).
- `[VERIFIED][EDGE]` (self-assessed, edge-hunter disabled) `except asyncio.TimeoutError` correctly precedes `except Exception`; a non-`asyncio.TimeoutError` backend failure (ModelError, httpx.TimeoutException, anthropic.APITimeoutError — none are builtin `TimeoutError`) is classified `degraded=True, timed_out=False` correctly. claude_p missing-usage → zeros, not a crash (tested). Server HTTPError (5xx) from a bad hub → caught by the bridge's URLError branch, swallowed.
- `[VERIFIED]` Naivety Invariant intact — telemetry reports the bot's own decision *outward*; no engine data feeds back into perception/decision. No alias tables, no action allowlists added.

### Rule Compliance (lang-review/python.md, exhaustive)

- **#1 silent exceptions** — `decide()` two `except` (brain.py:52,56): **finding above** (LOW, mitigated). `_emit_decision` `except Exception` (brain.py:115) → logs WARNING + exc_info: compliant. `telemetry.py` `except (URLError,ConnectionError,OSError,TimeoutError)` → logs WARNING: compliant. claude_p/ollama unchanged `except`s: compliant.
- **#2 mutable defaults** — all new defaults (`defn=None`, `component/session_slug/severity`, `cache_tokens=0/model=None/cost_usd=0.0`) immutable: compliant.
- **#3 type annotations at boundaries** — `decide`, `_emit_decision`, `emit_watcher_event`, `_post`, `_server_base_url`, `publish_event`, `watcher_emit`, `DecideResult` fields, `WatcherEmitPayload` fields all annotated: compliant.
- **#4 logging** — see #1; all new logs correct level (WARNING for network/client) + lazy `%s`: compliant except the `decide()` gap.
- **#5 path handling** — 0 instances.
- **#6 test quality** — mock targets correct (patch-where-used: `companion.telemetry._post`, `hub_mod.watcher_hub.publish`, `asyncio.create_subprocess_exec`); no vacuous `assert True`; but value-blind breadth loop is a coverage finding (above).
- **#7 resource leaks** — `urlopen` in `with`: compliant.
- **#8 unsafe deserialization** — none; `int()/float() or 0` safe coercion: compliant.
- **#9 async pitfalls** — `to_thread` offload correct, all awaits present: compliant.
- **#10 import hygiene** — no star imports, no cycle: compliant.
- **#11 input validation** — endpoint pre-existing localhost-only; `severity` unconstrained `str` (informational, above).
- **#12 dependency hygiene** — no dep changes; stdlib urllib chosen deliberately: compliant.
- **#13 fix-regressions** — claude_p fix keeps fail-loud ModelError; publish_event change has explicit non-regression guards: compliant.

### Devil's Advocate

Assume this is broken. **The lie-detector that can't detect its own lies.** This story exists so the GM panel can catch the narrator (and now the companion brain) "winging it." Yet the tests prove *structure*, not *substance*: I can make `_emit_decision` report `cost_usd=999.99`, the wrong owner, and an un-split backend, and every test stays green (empirically confirmed). For a feature whose entire purpose is telemetry *accuracy*, the accuracy of the emitted values is the one thing left unguarded. A confused future maintainer refactoring the field dict — reordering, renaming a key, mis-sourcing `cost_usd` from `input_tokens` — ships a corrupt lie-detector and CI says fine. That is the single most important gap, and it is exactly the class of bug this project fears most. **The stressed-backend scenario:** a real backend starts failing for a new reason (an SDK exception type nobody's seen). `decide()` swallows it to YIELD; the OTEL event says `degraded=true` but carries no error type, and Python logs are silent. The operator sees "the cat keeps yielding" with zero forensic trail — they cannot tell a timeout from an auth failure from a malformed-JSON crash. **The malicious/confused caller:** the `/internal/watcher/emit` endpoint is unauthenticated and now accepts an arbitrary `session_slug` string that becomes an envelope-level partition key on the hub — someone could spoof another session's slug and inject events into that session's GM-panel stream. It's localhost-only by design, so the blast radius is a dev machine, but the override *does* let a caller claim any session identity. **The latency coupling:** `await asyncio.to_thread(...)` means each companion turn now waits for the telemetry POST to complete (bounded at 2s); a hung-but-not-refused telemetry server adds up to 2s to every companion move. The loop stays responsive (good) but the soloing companion's turn drags — a mild "never stall the table" tension on a pathological server. **Verdict of the advocate:** none of these are correctness bugs in the happy path — the code is right — but they are real robustness/observability gaps on the exact axis the feature is about. They are worth fixing, and I am recording them as strong non-blocking findings; they do not rise to Critical/High, so they do not block a correct, green, wired implementation.

**Handoff:** To SM for finish-story.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-01T23:17:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-01T22:31:11Z | 2026-07-01T22:34:49Z | 3m 38s |
| red | 2026-07-01T22:34:49Z | 2026-07-01T22:52:33Z | 17m 44s |
| green | 2026-07-01T22:52:33Z | 2026-07-01T23:02:39Z | 10m 6s |
| review | 2026-07-01T23:02:39Z | 2026-07-01T23:17:54Z | 15m 15s |
| finish | 2026-07-01T23:17:54Z | - | - |

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the new `companion.telemetry` bridge is a *sync* stdlib `urllib` POST (mirroring the daemon), but it is called from inside the companion's *async* `run_companion` loop. A 2s telemetry timeout would block the event loop and stall the table. Affects `sidequest-understudy/src/companion/telemetry.py` + its call site (offload via `asyncio.to_thread`, or an async POST). *Deliberately not pinned as a test* (would over-dictate Dev's approach; the daemon's own bridge is sync). *Found by TEA during test design.*
- **Question** (non-blocking): AC #1 says "anthropic and ollama fill real values" for `cost_usd`, but only the `claude -p` envelope carries `total_cost_usd` — the Anthropic SDK response does not. Dev decides: compute anthropic cost from tokens×price, or leave 0.0/None. The tests pin anthropic reports `model` and ollama `cost_usd == 0.0` but deliberately do NOT pin anthropic `cost_usd`. Affects `seat_core/llm/anthropic_model.py`. *Found by TEA during test design.*
- **Question** (non-blocking): AC #2 lists both `backend` and `model` as event fields, and part (a) adds `model` to DecideResult. Suggest `backend` = the spec prefix (`defn.model` → `anthropic`/`claude_p`/`ollama`) and `model` = the concrete id from `DecideResult.model`. The wiring test asserts both keys are present but not their exact values. Affects `companion/run.py` (or wherever the record is assembled). *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): resolved TEA's cost question by leaving anthropic `cost_usd = 0.0` — the Anthropic SDK response carries no per-call price, and a hardcoded per-model price table (fragile, drifts on price changes) is beyond this story's tested contract. `claude_p` carries real cost via the envelope's `total_cost_usd`; ollama is a real 0.0. Since the companion's `DEFAULT_MODEL` is `anthropic/…`, most decisions will report cost 0.0. If real anthropic per-call cost matters, a follow-up needs a maintained price table (or reuse of the server-side cost model in `sq-llm-costs`). Affects `seat_core/llm/anthropic_model.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): every companion decision now fires a synchronous urllib POST (offloaded to a worker thread). At high turn cadence across many companions this is one blocking-thread POST per decision with a 2s ceiling. Fine for the current single-digit companion counts; if the fleet grows, consider batching or an async client. Affects `sidequest-understudy/src/companion/telemetry.py`. *Found by Reviewer during code review.*

### Reviewer (code review)
- **Improvement** (non-blocking, RECOMMENDED before/soon-after merge): the wiring test asserts field *presence* but never the *values* of `owner/backend/model/cost_usd/tokens` — four injected value bugs all pass green. For a telemetry-accuracy feature this is the highest-value gap. Add one test driving `run_companion` with a stub `StructuredModel` returning a realistic `DecideResult(model="claude-x", input_tokens=120, output_tokens=45, cost_usd=0.0034)` and assert the emitted `companion_brain_decide` fields carry `tokens==165`, `model=="claude-x"`, `cost_usd≈0.0034`, `backend=="anthropic"` (split), `owner=="alice@home"`. Affects `sidequest-understudy/tests/companion/test_brain_telemetry.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `decide()`'s degrade paths (`except asyncio.TimeoutError` / `except Exception`, brain.py:52,56) capture no exception type/message — the OTEL event says `degraded=true` but not *why*. For the lie-detector's forensic value, add the exception class to the telemetry (e.g. a `degrade_reason` field) or a `logger.warning(..., exc_info=True)` on the non-timeout branch. Affects `sidequest-understudy/src/companion/brain.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): stale docs — `seat_core/llm/claude_p_model.py:1` module docstring ("no token metering (reported zeros)") now contradicts the code; `sidequest-server/sidequest/server/app.py:315` `/internal/watcher/emit` header still frames the endpoint as daemon-only though it now serves the companion. Both trivial one-liners. *Found by Reviewer during code review.*
- **Question** (non-blocking): the `/internal/watcher/emit` endpoint is unauthenticated (localhost-only by design) and now accepts a caller-supplied `session_slug` that becomes an envelope-level partition key — a caller could claim any session's identity on the hub stream. Blast radius is a dev machine today; worth a note if the endpoint ever leaves localhost. Affects `sidequest-server/sidequest/server/app.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 1 Question, 0 Improvement)
**Blocking:** None

- **Question:** AC #2 lists both `backend` and `model` as event fields, and part (a) adds `model` to DecideResult. Suggest `backend` = the spec prefix (`defn.model` → `anthropic`/`claude_p`/`ollama`) and `model` = the concrete id from `DecideResult.model`. The wiring test asserts both keys are present but not their exact values. Affects `companion/run.py`.

### Downstream Effects

- **`companion`** — 1 finding

### Deviation Justifications

4 deviations

- **AC #6 wiring split across two repos instead of one end-to-end test**
  - Rationale: the two halves together cover the full path; a live-server end-to-end test belongs to integration/dogfood (160-3), not the unit RED phase.
  - Severity: minor
  - Forward impact: Dev should ensure the bridge's POST body key names match the server's `WatcherEmitPayload` field names exactly (`session_slug`, `severity`) so the two tested halves actually compose.
- **Run-loop emit asserted at the bridge network boundary, not the emit call-site**
  - Rationale: refactor-stable behavior assertion; does not dictate the internal call-site, which is a Dev design choice.
  - Severity: minor
  - Forward impact: none — the emit must ultimately reach `companion.telemetry._post` via urllib (story mandates stdlib POST mirroring the daemon).
- **Emit centralized in `brain.py::decide()`, not `run.py`**
  - Rationale: one emit site covers all four call sites (TURN_STATUS, PROMPT_KINDS, two chargen) uniformly; the optional `defn` keeps the 4 pre-existing `test_brain.py` tests green (defn omitted → no emit). TEA explicitly did not pin the call-site.
  - Severity: minor
  - Forward impact: none — observable behavior (one `companion_brain_decide` POST per decision) is identical; the record is assembled in `brain.py::_emit_decision`, not `run.py`.
- **Anthropic `cost_usd` left at 0.0 rather than computed**
  - Rationale: a price table is fragile, drifts on pricing changes, and no test required it; `claude_p` is the cost-metered backend (envelope `total_cost_usd`). Keeps the change in-scope and honest (0.0 = "not metered here", not a fabricated number).
  - Severity: minor
  - Forward impact: the 161-3 Inspector tab should treat anthropic `cost_usd == 0.0` as "cost not metered for this backend" (it already labels claude_p as notional vs anthropic as metered) — or a follow-up adds a price table.

## Design Deviations

No design deviations at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC #6 wiring split across two repos instead of one end-to-end test**
  - Spec source: context-story-161-2.md, AC #6
  - Spec text: "a fake-brain companion decision produces a companion_brain_decide watcher event on the hub with correct session_slug + seat + role"
  - Implementation: The "on the hub" landing crosses a cross-process HTTP boundary (understudy → POST → server hub) that no single unit test can span. Split into (1) understudy-side: the decision produces the bridge POST with the right session_slug/seat/role (`test_brain_telemetry.py`), and (2) server-side: a POST to `/internal/watcher/emit` lands on the hub carrying session_slug+severity (`test_companion_brain_telemetry_passthrough.py`).
  - Rationale: the two halves together cover the full path; a live-server end-to-end test belongs to integration/dogfood (160-3), not the unit RED phase.
  - Severity: minor
  - Forward impact: Dev should ensure the bridge's POST body key names match the server's `WatcherEmitPayload` field names exactly (`session_slug`, `severity`) so the two tested halves actually compose.
- **Run-loop emit asserted at the bridge network boundary, not the emit call-site**
  - Spec source: context-story-161-2.md, part (b)
  - Spec text: "companion run loop (companion/run.py): time the decide() await ... assemble a companion_brain_decide record ... and emit it"
  - Implementation: The wiring tests patch `companion.telemetry._post` (the network boundary) rather than a specific emit function in `run.py`, so they pass whether Dev emits from `run.py` or centralizes in `brain.py::decide()`.
  - Rationale: refactor-stable behavior assertion; does not dictate the internal call-site, which is a Dev design choice.
  - Severity: minor
  - Forward impact: none — the emit must ultimately reach `companion.telemetry._post` via urllib (story mandates stdlib POST mirroring the daemon).

### Dev (implementation)
- **Emit centralized in `brain.py::decide()`, not `run.py`**
  - Spec source: context-story-161-2.md, part (b)
  - Spec text: "companion run loop (companion/run.py): time the decide() await ... assemble a companion_brain_decide record ... and emit it"
  - Implementation: The timing + record assembly + emit live in `companion/brain.py::decide()` (behind an optional `defn` kwarg), not directly in `run.py`. `run.py` threads `defn=defn` into all four `decide()` call sites. `decide()` is the single `asyncio.wait_for` chokepoint that already holds the `DecideResult` and the timing boundary.
  - Rationale: one emit site covers all four call sites (TURN_STATUS, PROMPT_KINDS, two chargen) uniformly; the optional `defn` keeps the 4 pre-existing `test_brain.py` tests green (defn omitted → no emit). TEA explicitly did not pin the call-site.
  - Severity: minor
  - Forward impact: none — observable behavior (one `companion_brain_decide` POST per decision) is identical; the record is assembled in `brain.py::_emit_decision`, not `run.py`.
- **Anthropic `cost_usd` left at 0.0 rather than computed**
  - Spec source: context-story-161-2.md, AC #1
  - Spec text: "anthropic and ollama fill real values" (for model, tokens, and cost_usd)
  - Implementation: anthropic fills `model` + `cache_tokens` + real token counts, but `cost_usd` stays 0.0 (the SDK response reports no per-call price). Real cost would need a hardcoded per-model price table.
  - Rationale: a price table is fragile, drifts on pricing changes, and no test required it; `claude_p` is the cost-metered backend (envelope `total_cost_usd`). Keeps the change in-scope and honest (0.0 = "not metered here", not a fabricated number).
  - Severity: minor
  - Forward impact: the 161-3 Inspector tab should treat anthropic `cost_usd == 0.0` as "cost not metered for this backend" (it already labels claude_p as notional vs anthropic as metered) — or a follow-up adds a price table.

### Reviewer (audit)
- **TEA: AC #6 wiring split across two repos** → ✓ ACCEPTED by Reviewer: a single unit test genuinely cannot span the cross-process HTTP boundary; the split is sound and the two halves compose (verified — bridge body keys match `WatcherEmitPayload` field-for-field, and the server-side hub test proves the landing). The forward-impact caution (matching key names) is satisfied in the implementation.
- **TEA: Run-loop emit asserted at the bridge network boundary, not the call-site** → ✓ ACCEPTED by Reviewer: refactor-stable behavior assertion; Dev's choice to centralize in `brain.py::decide()` (rather than `run.py`) is transparently accommodated by patching `companion.telemetry._post`. Sound.
- **Dev: Emit centralized in `brain.py::decide()`, not `run.py`** → ✓ ACCEPTED by Reviewer: one chokepoint over four call sites is cleaner and correct; the optional `defn` kwarg preserves the 4 pre-existing `test_brain.py` tests. Observable behavior (one event per decision) is identical. TEA explicitly left the call-site free.
- **Dev: Anthropic `cost_usd` left at 0.0 rather than computed** → ✓ ACCEPTED by Reviewer: defensible and honest — the Anthropic SDK reports no per-call price, and a hardcoded price table is fragile scope-creep no test demanded; `claude_p` is the metered path; `0.0` reads as "not metered here," not a fabricated number. Recorded as a non-blocking follow-up (a price table, or reuse of the `sq-llm-costs` server-side model) if per-call anthropic cost is later required. This is the one judgment call Dev flagged; I concur.
- No undocumented spec deviations found — the emitting-telemetry-for-chargen-decisions behavior (all four `decide()` sites pass `defn`) is consistent with AC #2's "one event per decision," not a divergence.