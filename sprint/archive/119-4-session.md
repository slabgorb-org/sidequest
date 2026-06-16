---
story_id: "119-4"
jira_key: ""
epic: "119"
workflow: "tdd"
---
# Story 119-4: Auth Durability + Cost/Credit Observability

## Story Details
- **ID:** 119-4
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** 119-3 (done — unblocked)
- **Branch Strategy:** gitflow (feat/119-4-auth-durability-cost-observability)
- PR (MERGED 2026-06-16, squash 1e84cb5f): #921 — slabgorb-org/sidequest-server → develop. Merged manually with `-R` because `pf sprint story finish` runs `gh pr merge` without a repo flag from the orchestrator root and cannot resolve a subrepo PR (see Delivery Findings).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T22:54:24Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T21:42:20Z | 2026-06-16T21:44:49Z | 2m 29s |
| red | 2026-06-16T21:44:49Z | 2026-06-16T22:02:18Z | 17m 29s |
| green | 2026-06-16T22:02:18Z | 2026-06-16T22:10:04Z | 7m 46s |
| review | 2026-06-16T22:10:04Z | 2026-06-16T22:20:37Z | 10m 33s |
| red | 2026-06-16T22:20:37Z | 2026-06-16T22:35:07Z | 14m 30s |
| green | 2026-06-16T22:35:07Z | 2026-06-16T22:42:12Z | 7m 5s |
| review | 2026-06-16T22:42:12Z | 2026-06-16T22:54:24Z | 12m 12s |
| finish | 2026-06-16T22:54:24Z | - | - |

## Story Summary

This story hardens auth durability and adds cost/observability instrumentation after the 119-3 agent-SDK migration.

**Dependency:** 119-3 (narrator migration to claude-agent-sdk) — DONE (merged 2026-06-16).

**Three acceptance criteria:**

1. **Auth Durability (AC1):** Long-running server uses an auto-refreshing `ant auth login` profile on the host. The print-credentials env token is short-lived and not auto-refreshed. Construct the client to pick up the refreshing profile, not a baked-in token. Fail LOUD on expiry, never silently fall back to PAYG (SOUL No-Silent-Fallbacks doctrine is load-bearing).

2. **Cost/Billing-Pool OTEL (AC2):** Emit OTEL spans tagging which auth path / billing pool each inference draws (subscription free tier vs. PAYG overflow). This surfaces to the GM/cost panel so Keith/dev can VERIFY the narrator is on the free subscription. This is a Keith/dev observability concern per CLAUDE.md OTEL principle, NOT a player-facing surface.

3. **Budget Monitoring (AC3):** Monitor the 200 monthly free subscription credit + the pool-3 prepaid overflow buffer (currently 50.52). Surface mid-month exhaustion BEFORE silent PAYG billing kicks in. This is mid-month visibility into the budget ceiling.

**Implementation Load-Bearing Points:**
- The credential refresh must not require token baking into `.env` — use the `ant auth login` profile from the host.
- Every inference decision (narrator Sonnet, classifier Haiku) must emit OTEL with auth-path/billing-pool tag so the cost panel can verify the actual path taken.
- The cost-safety ceiling (ADR-134, cost_safety.py) was calibrated for PAYG; under subscription auth it now meters notional cost. AC must address this recalibration so the ceiling neither fires spuriously nor silently never-fires.
- Cache-observability: 119-3 left the narrator per-TTL (5m/1h) cache-write split documented as zero (anthropic_sdk_client.py:557-561, cached_input_write_5m/1h_tokens=0); aggregate cache read/write preserved. Surface the real split if the agent SDK exposes it, or document the permanent gap on the cost/GM panel (No Silent Fallbacks).

## Sm Assessment

**Setup verdict: ready for red.** Story 119-4 selected as the highest-priority unblocked p2 — it *is* the sprint goal's "cost observability" objective, now that its dependency 119-3 (agent-SDK narrator migration) merged 2026-06-16. Board was clean at selection (0 in-progress, 0 in-review, no merge-gate blocker).

**Scope is server-only, three ACs (see Story Summary).** This is a phased `tdd` workflow: setup → red → green → review → finish.

**Risk flags for TEA/Dev — read these before writing tests:**
- **AC1 is the load-bearing one.** "No Silent Fallbacks" is doctrine here, not a nicety: on auth-profile expiry the client must fail LOUD, never silently fall back to PAYG. The RED suite must include a test that asserts a *loud* failure on expiry (not a silent PAYG redirect) — that negative is the whole point of the story.
- **AC2 is a Keith/dev observability surface, not a player surface.** OTEL span tags auth-path/billing-pool. Do not let this leak into player-facing UI; it feeds the GM/cost panel only (CLAUDE.md OTEL principle).
- **AC3** surfaces mid-month budget exhaustion (200 monthly credit + ~50.52 overflow buffer) before silent PAYG billing.
- **Cost-ceiling recalibration (ADR-134 cost_safety.py)** was calibrated for PAYG; under subscription auth it now meters *notional* cost. Tests should pin behavior so the ceiling neither fires spuriously nor silently never-fires.
- **Cache-split gap from 119-3** (anthropic_sdk_client.py:557-561 — per-TTL cache-write split documented as zero). Either surface the real split if the agent SDK exposes it, or assert the permanent gap is documented on the panel — don't let it read as "verified" when it isn't.

**Routing:** workflow phased → next agent **tea** (red phase). Jira not configured; sprint runs YAML-only, claim skipped intentionally.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes

**Scope note (read first):** 119-4 was scoped for the 119-2 migration (static env token) but **119-3 (agent-SDK) shipped**, and the epic was reframed 2026-06-15 (Agent SDK credit CANCELLED → subscription is free). Two headline AC clauses reference a void premise; user confirmed "build the real subset" 2026-06-16. See **Design Deviations → TEA** for the three descopes/reframes. RED covers only the genuinely-buildable subset.

**Test File:**
- `tests/agents/test_119_4_auth_durability_cost_otel.py` — 11 tests, hermetic fake-`query` seam (no live subscription).

**Tests Written:** 11 tests covering 4 ACs (AC2 auth-path label, AC1' legible fail-loud, AC4 notional cost-basis, AC3' honest usage monitor).
**Status:** RED — verified via `testing-runner` (RUN_ID 119-4-tea-red). File collects cleanly; **8 fail for the right reason** (missing field/event/typed-error), **3 negative guards pass** and must keep passing.

| # | Test | AC | RED status |
|---|------|----|-----------|
| 1 | `test_usage_event_tags_subscription_auth_path` | AC2 | failing (no `auth_path`) |
| 2 | `test_llm_request_span_tags_subscription_auth_path` (WIRING) | AC2 | failing (no `llm.auth_path`) |
| 3 | `test_raised_query_maps_to_typed_auth_unavailable` | AC1' | failing (raw RuntimeError, not typed) |
| 4 | `test_auth_failure_emits_watcher_event_before_raise` | AC1' | failing (no `narrator.auth_unavailable`) |
| 5 | `test_is_error_still_raises_no_silent_success` | AC1' guard | **passing** (must hold) |
| 6 | `test_usage_event_marks_cost_notional` | AC4 | failing (no `cost_basis`) |
| 7 | `test_cost_running_total_marks_notional` | AC4 | failing (no `cost_basis`) |
| 8 | `test_ceiling_still_fires_and_is_marked_notional` | AC4 | failing (no `cost_basis`; raise fires) |
| 9 | `test_ceiling_does_not_fire_spuriously_on_normal_turn` | AC4 guard | **passing** (must hold) |
| 10 | `test_usage_event_surfaces_sdk_reported_cost` | AC3' | failing (no `sdk_reported_cost_usd`) |
| 11 | `test_usage_surfaces_never_fabricate_subscription_budget` | AC3' guard | **passing** (must hold) |

**Contract constants** (top of the test file) are the exact names Dev implements: `auth_path="subscription"`, span `llm.auth_path`, event `narrator.auth_unavailable`, `cost_basis="notional"`, `sdk_reported_cost_usd`.

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #1 No silent exception swallowing (auth must fail LOUD) | `test_raised_query_maps_to_typed_auth_unavailable`, `test_auth_failure_emits_watcher_event_before_raise`, `test_is_error_still_raises_no_silent_success` | failing / failing / passing |
| #1 No Silent Fallbacks — never report a measured value we don't have | `test_usage_surfaces_never_fabricate_subscription_budget` | passing (guard) |
| #6 Test quality — meaningful assertions, no vacuous | self-checked: every test asserts a specific value/type/raise; no `assert True`/`is_none`-on-always-None | n/a |
| #9 Async correctness — awaited coroutines | all 11 tests `await` the real `complete_with_tools` | n/a |

**Rules checked:** 3 of 13 lang-review rules are AC-relevant (the rest — path handling, deserialization, SQL, resource leaks — don't apply to an OTEL-labeling + auth-guard story). **Self-check:** 0 vacuous tests.

**Wiring test:** `test_llm_request_span_tags_subscription_auth_path` drives the real production `complete_with_tools` and asserts the live `llm.request` span — span-assertion wiring per CLAUDE.md ("No Source-Text Wiring Tests"; OTEL-span assertion is the sanctioned form).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/anthropic_sdk_client.py` — (1) three module constants (`_AUTH_PATH_SUBSCRIPTION`, `_COST_BASIS_NOTIONAL`, `_AUTH_UNAVAILABLE_EVENT`); (2) wrapped the `query()` iteration in `complete_with_tools` so a raised transport exception maps to the typed `AgentSdkAuthUnavailable` (re-raises an already-typed one unchanged); (3) `auth_path='subscription'` + `cost_basis='notional'` + `sdk_reported_cost_usd` on the `narrator.sdk.usage` event and `llm.auth_path` on the `llm.request` span; (4) `_emit_auth_unavailable()` helper emitting `narrator.auth_unavailable` (severity error) before both auth raises; (5) `cost_basis='notional'` on `session.cost_running_total`.
- `sidequest/agents/cost_safety.py` — `cost_basis='notional'` on the `session.cost_ceiling_exceeded` event.

**Tests:** 11/11 passing (GREEN) — verified via `testing-runner` (RUN_ID 119-4-dev-green, re-confirmed post-ruff-format). **Regression:** 52/52 passing across the touched-file suites (119-3 narrator port, subscription auth, Haiku port, cost_safety unit, fake SDK client, 91-5 ledger). **ruff** check+format clean; **pyright** 0 errors on both files.

**Approach:** Minimal — implemented exactly the contract constants TEA named, narrator path only (per the user-confirmed RED scope). No new abstraction beyond the one `_emit_auth_unavailable` helper (shared by the two auth-raise sites). The notional/auth labels are additive event/span fields — no behavior change to convergence, the tool loop, or the ceiling's firing logic (only its event now declares its basis).

**Branch:** `feat/119-4-auth-durability-cost-observability` (pushed to origin).

**Handoff:** To Reviewer (Chrisjen Avasarala) for review (this tdd workflow routes green → review directly).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Gap** (non-blocking): a *raised* `query()` exception (absent/expired subscription login, OQ-5) propagates RAW — the `async for message in query(...)` loop has no try/except, so it is NOT mapped to the typed `AgentSdkAuthUnavailable`. Only the `ResultMessage(is_error=True)` path raises the typed error. Affects `sidequest/agents/anthropic_sdk_client.py` (`complete_with_tools`, ~line 391) — wrap the query iteration, map a raised transport error to `AgentSdkAuthUnavailable`. *Found by TEA during test design.*
- **Gap** (non-blocking): NEITHER auth-failure path (raised query OR `is_error`) emits a watcher event before raising — the GM panel is blind to auth failures. Affects `sidequest/agents/anthropic_sdk_client.py` (the `is_error` raise ~line 519 and the new query-exception handler) — emit `narrator.auth_unavailable` (component `narrator.sdk`, severity `error`) before the raise. Both the narrator and the 4 Haiku sites share this choke point; consider whether the Haiku sites need the same event. *Found by TEA during test design.*
- **Improvement** (non-blocking): `llm.request` span documents an `llm.ratelimit_input_tokens_remaining` attribute (`sidequest/telemetry/spans/llm_request.py` docstring) that NO production code populates — a dead vestige of the pre-119-3 raw-SDK era (the agent-SDK subprocess can't reach HTTP response headers). Affects `llm_request.py` — correct or remove the docstring line so the 0/absent value is never read as measured. *Found by TEA during test design.*
- **Question** (non-blocking): the four Haiku adapter sites (`_AsideLlm`, `_IntentRouterLlm`, classifier) run the same subscription transport via `llm_factory`, but the RED suite scopes the `auth_path`/`cost_basis` labels to the **narrator** surfaces (`narrator.sdk.usage` / `llm.request`). If the cost panel needs the labels on adapter spend too, Dev/Architect should decide whether to thread `auth_path`/`cost_basis` through the `llm_factory` Haiku path + ledger events. Out of the RED scope as confirmed with the user, flagged for completeness. *Found by TEA during test design.*

_(round 2 — red-phase rework after Reviewer rejection)_
- **Improvement** (non-blocking): the round-2 honesty contract is pinned by error ORIGIN — Dev must separate the transport-iteration boundary (`async for ... in query(...)` / `__anext__`) from loop-body message processing so an INTERNAL error (e.g. a parse bug) escapes un-relabeled while a *raised* `query()` still maps to `AgentSdkAuthUnavailable`. A pure exception-TYPE narrow will NOT satisfy `test_raised_query_emits_auth_event_before_raise` (its fake raises a bare `RuntimeError`, which a typed `except` would stop catching). Affects `sidequest/agents/anthropic_sdk_client.py` (`complete_with_tools`, the `except Exception` at ~:443). *Found by TEA during test design.*
- **Gap** (non-blocking): the Reviewer's [LOW] comment-honesty cluster (the `except` comment claiming it catches "a RAISED query() exception"; "every inference drew the free pool" → "every **successful** inference"; the `_emit_auth_unavailable` / `AgentSdkAuthUnavailable` docstrings) is NOT test-enforced — comments cannot be pinned without a forbidden source-text grep (house rule "No Source-Text Wiring Tests"). Dev must apply those by hand per the Reviewer table; a green suite will not flag a stale comment. Affects `sidequest/agents/anthropic_sdk_client.py` (~:92, ~:113, ~:444, ~:874). *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (non-blocking): confirmed TEA's Haiku-parity question — the `llm_factory` Haiku adapter usage events and the `cost_safety` adapter ledger path (`record_call` → `cost_runaway_suspected`) do NOT carry `auth_path`/`cost_basis`. Only the narrator surfaces were in scope. If the panel wants a complete free-pool/notional picture, a follow-up should thread both labels through the Haiku adapter usage emit and the `cost_runaway_suspected` event. Affects `sidequest/agents/llm_factory.py` + `sidequest/agents/cost_safety.py` (`check_and_emit_runaway`). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the dead `llm.ratelimit_input_tokens_remaining` doc line on `sidequest/telemetry/spans/llm_request.py` (TEA flagged) was left untouched — out of the minimal GREEN scope. It still documents an attribute no code populates; a one-line docstring fix should land with the Haiku-parity follow-up or in tech-debt. *Found by Dev during implementation.*
- **Question** (non-blocking): `sdk_reported_cost_usd` is surfaced as the PAYG-leak tell, but its real value over a subscription is unverified (the fake defaults it to 0.0). A live operator/playtest check should confirm what `ResultMessage.total_cost_usd` actually reports over the Max subscription — $0 (clean) vs a notional figure — so the panel knows how to read it. Affects the cost panel interpretation, not server code. *Found by Dev during implementation.*

_(round 2 — green rework after Reviewer rejection)_
- No new upstream findings during the round-2 rework. The two prior Dev findings remain open and out of this rework's scope: (1) the Haiku-parity gap (`llm_factory.py` + `cost_safety.py` adapter path carries no `auth_path`/`cost_basis`), and (2) the dead `llm.ratelimit_input_tokens_remaining` doc-line on `sidequest/telemetry/spans/llm_request.py:11` (still untouched — I left `llm_request.py` alone since the Reviewer's [LOW] DOC cluster scoped only `anthropic_sdk_client.py`). Both belong with the Haiku-parity follow-up. *Found by Dev during implementation.*

### Reviewer (code review)

- **Gap** (blocking): the broad `except Exception` in `complete_with_tools` mislabels ANY loop-body error (message-parse bug, SDK `CLINotFoundError`, etc.) as `AgentSdkAuthUnavailable("subscription login absent or expired")` with watcher `reason="query_raised"` — a false signal on the lie-detector panel this story exists to make honest. Affects `sidequest/agents/anthropic_sdk_client.py:~443` (narrow the catch to real transport/SDK errors, OR make the comment + message + `reason` honestly non-committal about cause). *Found by Reviewer during code review.*
- **Gap** (blocking): half of AC1' is untested — the `query_raised` branch's `narrator.auth_unavailable` emit (`anthropic_sdk_client.py:449`) has NO test; only the `is_error` branch is event-verified. Affects `tests/agents/test_119_4_auth_durability_cost_otel.py` (add a RaisingFakeQuery test asserting the event fires before the raise). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `logger.error` vs `warning` for `_emit_auth_unavailable` is debatable (lang-review #4 says client-config errors are `warning`), but a narrator-halting auth-absence matches the existing error-level precedent for `session.cost_ceiling_exceeded`; left as error per the OTEL max-visibility doctrine. Noted, not required. *Found by Reviewer during code review.*

_(round 2 — re-review, APPROVED with [LOW] follow-ups)_
- **Improvement** (non-blocking): the module-constant comment "affirms a **successful** inference drew the free pool" overclaims — `narrator.sdk.usage` (carrying `auth_path`) fires at `anthropic_sdk_client.py:532-550` INSIDE the `with llm_request_span` block, BEFORE the `is_error` gate at `:568`, so `is_error` results emit it too. Reword to "every **transport-completed** inference". Affects `sidequest/agents/anthropic_sdk_client.py:94` (one-word comment fix). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_auth_failure_emits_watcher_event_before_raise` (the `is_error` branch) should assert `reason="is_error"` to mirror the query_raised test's reason check — otherwise a refactor emitting the wrong `reason` from the `is_error` branch stays green. Affects `tests/agents/test_119_4_auth_durability_cost_otel.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `cost_safety.py:314` uses the bare literal `"notional"` rather than a shared `cost_basis` constant; the obvious "import `_COST_BASIS_NOTIONAL`" fix is a CIRCULAR import (`anthropic_sdk_client` already imports `cost_safety`). A real fix promotes the constant to a shared module. Bundle with the Haiku-parity follow-up. Affects `sidequest/agents/cost_safety.py` + `anthropic_sdk_client.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 5 findings (3 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** 2 BLOCKING items — see below

**BLOCKING:**
- **Gap:** the broad `except Exception` in `complete_with_tools` mislabels ANY loop-body error (message-parse bug, SDK `CLINotFoundError`, etc.) as `AgentSdkAuthUnavailable("subscription login absent or expired")` with watcher `reason="query_raised"` — a false signal on the lie-detector panel this story exists to make honest. Affects `sidequest/agents/anthropic_sdk_client.py:~443`.
- **Gap:** half of AC1' is untested — the `query_raised` branch's `narrator.auth_unavailable` emit (`anthropic_sdk_client.py:449`) has NO test; only the `is_error` branch is event-verified. Affects `tests/agents/test_119_4_auth_durability_cost_otel.py`.

- **Improvement:** the round-2 honesty contract is pinned by error ORIGIN — Dev must separate the transport-iteration boundary (`async for ... in query(...)` / `__anext__`) from loop-body message processing so an INTERNAL error (e.g. a parse bug) escapes un-relabeled while a *raised* `query()` still maps to `AgentSdkAuthUnavailable`. A pure exception-TYPE narrow will NOT satisfy `test_raised_query_emits_auth_event_before_raise` (its fake raises a bare `RuntimeError`, which a typed `except` would stop catching). Affects `sidequest/agents/anthropic_sdk_client.py`.
- **Gap:** the Reviewer's [LOW] comment-honesty cluster (the `except` comment claiming it catches "a RAISED query() exception"; "every inference drew the free pool" → "every **successful** inference"; the `_emit_auth_unavailable` / `AgentSdkAuthUnavailable` docstrings) is NOT test-enforced — comments cannot be pinned without a forbidden source-text grep (house rule "No Source-Text Wiring Tests"). Dev must apply those by hand per the Reviewer table; a green suite will not flag a stale comment. Affects `sidequest/agents/anthropic_sdk_client.py`.
- **Improvement:** the module-constant comment "affirms a **successful** inference drew the free pool" overclaims — `narrator.sdk.usage` (carrying `auth_path`) fires at `anthropic_sdk_client.py:532-550` INSIDE the `with llm_request_span` block, BEFORE the `is_error` gate at `:568`, so `is_error` results emit it too. Reword to "every **transport-completed** inference". Affects `sidequest/agents/anthropic_sdk_client.py:94`.

### Downstream Effects

Cross-module impact: 5 findings across 2 modules

- **`sidequest/agents`** — 4 findings
- **`tests/agents`** — 1 finding

### Deviation Justifications

3 deviations

- **Descoped AC1's "swap the static env token for an auto-refreshing `ant auth login` profile"**
  - Rationale: Writing tests for a token swap that the shipped migration already deleted would test fiction. The buildable AC1 residual (legible fail-loud on expiry/absence) IS covered (`test_raised_query_maps_to_typed_auth_unavailable`, `test_auth_failure_emits_watcher_event_before_raise`).
  - Severity: major (drops a headline AC clause)
  - Forward impact: none — the durability property AC1 wanted (auto-refresh, no expiry surprise) is a property of the agent-SDK transport already; only the *mechanism* named in the spec is void.
- **Descoped AC3's "200 monthly credit + 50.52 prepaid overflow buffer … before it silently bills PAYG"**
  - Rationale: The premise is void per ADR-101 Amendment (2026-06-15). Fabricating a budget number we cannot measure would itself violate No Silent Fallbacks.
  - Severity: major (drops a headline AC)
  - Forward impact: none — replaced by the honest AC3' usage monitor (notional cumulative + SDK-reported spend).
- **Reframed AC3's "rate-limit/usage monitor" from anthropic-ratelimit headers to SDK-reported `total_cost_usd`**
  - Rationale: the panel is the lie detector; softening only the wording leaves it showing an `auth_unavailable` event for a parse bug. The origin discriminator reconciles "map a raised query to auth (AC1')" with "never mislabel our own bugs as auth" without coupling the hermetic fakes to the SDK exception taxonomy.
  - Severity: minor (strengthens the Reviewer's required fix; drops no scope)
  - Forward impact: directs Dev to a loop restructure (separate the transport boundary from body processing), not a type-narrow; the comment-honesty [LOW] cluster stays a hand-applied DOC fix (not test-pinnable — see Delivery Findings).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Descoped AC1's "swap the static env token for an auto-refreshing `ant auth login` profile"**
  - Spec source: session Story Summary AC1 / 119-2 design spec §6 (`docs/superpowers/specs/2026-06-15-narrator-subscription-oauth-reauth-design.md`)
  - Spec text: "swap the static env token for an auto-refreshing `ant auth login` profile resolved on the host"
  - Implementation: No test/work for a static-token→profile swap. The 119-2 migration (static `ANTHROPIC_AUTH_TOKEN`) never shipped; **119-3 (agent-SDK) shipped**, and its transport already resolves the host's auto-refreshing OAuth login via the bundled CLI — there is no static env token in this path (`assert_subscription_auth()` in fact *requires* `ANTHROPIC_AUTH_TOKEN` UNSET). The "swap" has no referent.
  - Rationale: Writing tests for a token swap that the shipped migration already deleted would test fiction. The buildable AC1 residual (legible fail-loud on expiry/absence) IS covered (`test_raised_query_maps_to_typed_auth_unavailable`, `test_auth_failure_emits_watcher_event_before_raise`).
  - Severity: major (drops a headline AC clause)
  - Forward impact: none — the durability property AC1 wanted (auto-refresh, no expiry surprise) is a property of the agent-SDK transport already; only the *mechanism* named in the spec is void.

- **Descoped AC3's "200 monthly credit + 50.52 prepaid overflow buffer … before it silently bills PAYG"**
  - Spec source: session Story Summary AC3 / story title
  - Spec text: "monitor the 200 monthly credit + the pool-3 prepaid overflow buffer (currently 50.52) so mid-month exhaustion is visible before it silently bills PAYG"
  - Implementation: No test for a $200 credit / $50.52 buffer monitor. The epic was **reframed 2026-06-15: the Agent SDK credit was CANCELLED** — the subscription is simply free; there is no metered credit and no $50.52 overflow pool. And 119-3 *fails loud* (no silent PAYG fallback), so "before it silently bills PAYG" has no path. A negative guard (`test_usage_surfaces_never_fabricate_subscription_budget`) instead asserts these numbers are NEVER resurrected as fabricated measured values.
  - Rationale: The premise is void per ADR-101 Amendment (2026-06-15). Fabricating a budget number we cannot measure would itself violate No Silent Fallbacks.
  - Severity: major (drops a headline AC)
  - Forward impact: none — replaced by the honest AC3' usage monitor (notional cumulative + SDK-reported spend).

- **Reframed AC3's "rate-limit/usage monitor" from anthropic-ratelimit headers to SDK-reported `total_cost_usd`**
  - Spec source: the RED-scope option text approved by the user 2026-06-16 ("AC3' rate-limit/usage monitor from the anthropic-ratelimit headers we already capture")
  - Spec text: "monitor … from the anthropic-ratelimit-* headers we already capture"
  - Implementation: AC3' is tested via `test_usage_event_surfaces_sdk_reported_cost` (surface `ResultMessage.total_cost_usd` as `sdk_reported_cost_usd`) — NOT via ratelimit headers. The headers are unreachable: the `llm.request` span documents `llm.ratelimit_input_tokens_remaining` but NO code captures it (grep-confirmed empty), and the claude-agent-sdk runs as a **subprocess** returning a `ResultMessage`, not raw HTTP response headers.
  - Rationale: I was wrong in the option text that we "already capture" those headers — we do not, and the transport cannot reach them. The honest, buildable usage signal is the SDK's own `total_cost_usd` (the `ResultMessage` exposes it) surfaced alongside the notional figure. Flagged loudly to the user at decision time.
  - Severity: minor (same AC intent — verify the free pool / catch a PAYG leak — different, actually-available signal)
  - Forward impact: a follow-up could re-home the dead `llm.ratelimit_input_tokens_remaining` span-attr doc (it now documents an unpopulated field). Captured as a Delivery Finding.

- **Pinned the STRONG honesty option (no auth signal for non-auth errors) over the Reviewer's softer "OR", and discriminated by error ORIGIN not exception type** _(round 2 — red rework)_
  - Spec source: Reviewer Assessment round 1, [HIGH] row (`anthropic_sdk_client.py:~443`)
  - Spec text: "Narrow the catch to genuine transport/SDK errors (preferred), OR keep it broad but make the comment, the exception message, and the watcher reason non-committal about cause."
  - Implementation: `test_internal_processing_error_is_not_mislabeled_as_auth` forbids BOTH halves of the weak "OR" path — an internal/non-auth error must emit NO `narrator.auth_unavailable` AND must NOT be coerced to `AgentSdkAuthUnavailable` (a non-committal *message* still leaves the event name + exception type asserting auth). The contract is pinned by error ORIGIN (transport `query()` raise → auth+event per AC1'; loop-body processing raise → propagates raw) rather than by exception type, because the AC1' fakes raise a bare `RuntimeError` a type-narrowed `except` could not catch.
  - Rationale: the panel is the lie detector; softening only the wording leaves it showing an `auth_unavailable` event for a parse bug. The origin discriminator reconciles "map a raised query to auth (AC1')" with "never mislabel our own bugs as auth" without coupling the hermetic fakes to the SDK exception taxonomy.
  - Severity: minor (strengthens the Reviewer's required fix; drops no scope)
  - Forward impact: directs Dev to a loop restructure (separate the transport boundary from body processing), not a type-narrow; the comment-honesty [LOW] cluster stays a hand-applied DOC fix (not test-pinnable — see Delivery Findings).

### Dev (implementation)

- No deviations from spec (round 2 — green rework). Implemented exactly the origin-based contract TEA's round-2 tests pin: drove the async iterator by hand (`aiter`/`anext`) so the auth-mapping catch wraps ONLY the transport boundary, with our message processing OUTSIDE it (an internal error propagates raw, no auth signal); added a "transport error" acknowledgement to the query-failure headline; kept the transport-raise → `AgentSdkAuthUnavailable` + `narrator.auth_unavailable` (reason `query_raised`) mapping for AC1'. Also applied the Reviewer's [LOW] comment/docstring honesty cluster by hand (module-constant "successful inference", `AgentSdkAuthUnavailable` + `_emit_auth_unavailable` docstrings). No data-structure or algorithm choice diverged from the test contract.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (51 tests green, ruff/pyright/format clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own edge analysis |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own silent-failure analysis |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 4, downgraded 3, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 2, downgraded 2 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own type analysis (clean) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own security analysis (1 LOW) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own simplifier analysis (clean) |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 2, downgraded 2 |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents` and assessed by Reviewer directly)
**Total findings:** 2 blocking confirmed, 4 non-blocking confirmed, 5 downgraded (with rationale), 1 dismissed, 1 deferred

## Reviewer Assessment

**Verdict:** REJECTED

The feature is functionally correct and green (51 tests pass), but it ships a **dishonest error path on the exact panel the story exists to make honest**, and leaves **half of the load-bearing AC1' untested**. On a story whose purpose is verifiable cost/auth observability — the OTEL lie detector — a false "subscription login expired" signal is not a nitpick; it is the failure mode the story is supposed to prevent.

### Severity Table

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Broad `except Exception` re-raises ANY loop-body error (parse bug, SDK `CLINotFoundError`, timeout) as `AgentSdkAuthUnavailable("subscription login absent or expired")` + watcher `reason="query_raised"`. Loud + cause-chained, but mislabels non-auth failures as auth on the lie-detector panel. HONESTY / lang-review #1 ("catch specifically when the type is known"). [RULE][DOC] | `anthropic_sdk_client.py:~443` (catch), `:~449` (event), comment `:~444` | Narrow the catch to genuine transport/SDK errors (preferred), OR keep it broad but make the comment, the exception message, and the watcher `reason` non-committal about cause (e.g. "query failed — subscription login absent/expired or transport error"). The detail/cause already carry the truth; stop the top-level label asserting auth. |
| [MEDIUM] | AC1' half-untested: the `query_raised` branch's `narrator.auth_unavailable` emit has NO test (only `is_error` is event-verified). A future edit could drop the emit and stay green. [TEST] | `test_119_4_...py` (missing) | Add a RaisingFakeQuery test capturing watcher events and asserting `narrator.auth_unavailable` fires before `AgentSdkAuthUnavailable`. |
| [MEDIUM] | Weak negative guard: `test_is_error_still_raises_no_silent_success` catches base `AnthropicSdkClientError`, so it passes even if the wrong subclass (`AnthropicSdkConfigError`, `AnthropicSdkLoopExceeded`) were raised. [TEST][RULE] | `test_119_4_...py:263` | Tighten to `pytest.raises(AgentSdkAuthUnavailable)`. |
| [LOW] | No test that a non-auth exception (e.g. `ValueError`) maps with cause chained + honest `detail`; no test that `error_max_turns` does NOT emit a spurious `narrator.auth_unavailable`; never-fabricate guard checks watcher events but not span attrs; `sdk_reported_cost_usd=None` case untested. [TEST] | `test_119_4_...py` | Add while in the file (bundle with the MEDIUM test work). |
| [LOW] | Comment honesty cluster: the `except` comment says it catches "a RAISED query() exception" (it catches all); "every inference drew the free pool" should be "every **successful** inference"; `_emit_auth_unavailable` + `AgentSdkAuthUnavailable` docstrings don't mention the new broad-catch raise condition. [DOC] | `anthropic_sdk_client.py:~92,~113,~444,~874` | Correct the comments/docstrings to match what the code does. |

### Rule Compliance (lang-review/python.md + SOUL/CLAUDE honesty rules)

- **#1 Silent exception swallowing / No Silent Fallbacks** — The new `except Exception` does NOT swallow (re-raises with `from exc`, emits first) ✓, BUT violates the "catch specifically when the type is known" clause and the HONESTY rule by mislabeling. **VIOLATION (blocking).**
- **#3 Type annotations** — `_emit_auth_unavailable` fully annotated ✓. `sdk_reported_cost_usd` local untyped (`getattr`→`Any` narrowed silently) — LOW; test helpers `_new_client/_drive -> Any` lack the rule-required inline comment — LOW (private test helpers).
- **#4 Logging correctness** — `logger.error` for auth-absence flagged vs the 4xx→warning rule; **downgraded to LOW** — a narrator-halting auth failure matches the existing error-level precedent for `session.cost_ceiling_exceeded` and the OTEL max-visibility doctrine. Not blocking.
- **#6 Test quality** — one weak guard (base-class catch, above). Otherwise assertions are specific (exact string/value/approx). One real gap (query_raised event).
- **#7 Resource leaks / #9 Async** — `try/except` sits INSIDE the `with llm_request_span` (no leak) ✓; `async for` correctly awaited; `except Exception` does not catch `asyncio.CancelledError` (BaseException) ✓.
- **#11 Security** — `detail=str(exc)` is operator-visible only, and no PAYG cred is set on this path (`assert_subscription_auth`), so no token leak. LOW. ✓
- **No Stubbing / dead code** — every new field (`auth_path`, `cost_basis`, `sdk_reported_cost_usd`) is read by tests AND the watcher/panel consumer; constants used. ✓
- **#2/#5/#8/#10/#12** — N/A or clean (no mutable defaults, no path/deserialization/SQL, no new imports/deps).

### Observations

- [HIGH] Broad `except Exception` mislabels non-auth errors as auth — `anthropic_sdk_client.py:443`. [RULE][DOC] (3 subagents concur.)
- [MEDIUM] `query_raised` watcher-event emit untested — `anthropic_sdk_client.py:449` / test gap. [TEST]
- [MEDIUM] Negative guard catches base class not `AgentSdkAuthUnavailable` — `test:263`. [TEST][RULE]
- [VERIFIED] `auth_path="subscription"` is an ENFORCED invariant — `build_agent_sdk_options()` (`:391`) calls `assert_subscription_auth()` (`:217`) BEFORE the query loop and the label (`:494`/`:523`); a set PAYG cred raises first. The label complies with the HONESTY rule (reflects an enforced precondition, not a claim). [DOC]
- [VERIFIED] Emit-before-raise holds — both `_emit_auth_unavailable` sites (`:449`, `:566`) are immediately followed by `raise AgentSdkAuthUnavailable`; `error_max_turns` correctly exits earlier via `AnthropicSdkLoopExceeded` without emitting. [SILENT]
- [VERIFIED] `cost = compute_cost_usd(...)` is token×PAYG-rate, so `cost_basis="notional"` is accurate; `sdk_reported_cost_usd` is genuinely read from `result_msg.total_cost_usd` (`:483`), not fabricated. [DOC]
- [VERIFIED] No money risk introduced — additive OTEL labels + error mapping; auth resolution, the ceiling firing, and convergence are unchanged. [SEC]
- [DISMISSED] Ledger state-bleed under `-n0` (test-analyzer #6) — `tests/conftest.py:16-28` autouse `_reset_cost_safety_ledger` calls `ledger().reset_for_tests()` before every test. Moot.
- [DEFERRED] Wiring-test reachability (test-analyzer, low) — `complete_with_tools` is the production inference entry, and sibling `test_complete_with_tools_reachable_from_orchestrator` (119-3) establishes the orchestrator wiring; the 119-4 span test proves the label fires on that same production method. Acceptable; docstring could narrow its claim. [TEST]
- [LOW] `detail=str(exc)` is operator-visible only; no cred on this path → minimal leak risk. [SEC]

### Devil's Advocate

Argue this code is broken. The whole story is "make the cost/auth panel honest so Keith can VERIFY the narrator is on the free pool." Now imagine the failure mode the broad `except Exception` invites. A future edit adds a new message-processing branch inside the `async for` loop — say, a handler that does `message.content[0]` and one day gets an empty list. That raises `IndexError`. The new try/except catches it, fires `narrator.auth_unavailable` with `reason="query_raised"`, and re-raises `AgentSdkAuthUnavailable("subscription login absent or expired")`. Keith opens the GM panel — the lie detector — and sees a red "subscription login expired" event. He spends an hour re-running `ant auth login`, checking his Max subscription, restarting the server. The real bug was an `IndexError` in a parser. The panel built to END "winging it" just lied to him, because the error path asserts a diagnosis it cannot support. The cause is chained, yes — but the chained traceback is in the logs, not the panel, and the panel's `reason` and the exception's headline both say "auth." This is precisely the El-Dorado illusion the OTEL doctrine names: a convincing signal with no mechanical backing. A confused operator trusts the panel over the logs — that's why the panel exists. Second angle: the load-bearing AC1' is the GM-panel visibility of auth failures, and exactly ONE of its two branches (`is_error`) is tested; the `query_raised` branch — the one the broad catch feeds — has no event assertion. So the very branch most likely to misbehave is the one with no guard. A malicious or merely unlucky input that makes the SDK raise mid-stream lands on untested code that emits a possibly-wrong signal. The honest version costs three lines: stop asserting auth as the cause when you caught `Exception`, and test the branch you added. Until then, the panel can lie, and we can't prove the lie won't happen.

**Handoff:** Back to TEA (Amos Burton) for red-phase rework — the blocking fixes are test-driven (the mislabel must be pinned by a non-auth-exception test; the `query_raised` event and the tightened guard are new/changed tests), and the impl honesty fix (narrow catch or non-committal message) follows from them.

### Dev (implementation)
- No deviations from spec. Implemented exactly the contract constants and surfaces TEA's 11 tests specify (narrator-path `auth_path`/`cost_basis`/`sdk_reported_cost_usd` + the `narrator.auth_unavailable` event + the typed-error mapping), within the user-confirmed RED scope. The scope reductions themselves are TEA's logged deviations above, not new Dev choices.

### Reviewer (audit)

- **TEA — Descoped AC1 static-token swap** → ✓ ACCEPTED by Reviewer: 119-2 never shipped; the agent-SDK transport resolves the host OAuth profile and `assert_subscription_auth()` requires `ANTHROPIC_AUTH_TOKEN` UNSET. The "swap" has no referent. Sound.
- **TEA — Descoped AC3 $200 credit / $50.52 buffer** → ✓ ACCEPTED by Reviewer: void per ADR-101 Amendment (2026-06-15, credit CANCELLED). The negative guard against fabricating the numbers is the right posture (No Silent Fallbacks). Sound.
- **TEA — Reframed AC3 ratelimit-headers → SDK `total_cost_usd`** → ✓ ACCEPTED by Reviewer: I confirmed the agent-SDK subprocess returns a `ResultMessage`, not HTTP headers; `total_cost_usd` is read at `anthropic_sdk_client.py:483` and surfaced. Honest reframe, flagged to the user at decision time. Sound.
- **Dev — No deviations** → ✓ ACCEPTED by Reviewer: the diff matches the test contract; no undisclosed divergence found.
- **UNDOCUMENTED (Reviewer audit):** the broad `except Exception` re-raises non-auth errors as `AgentSdkAuthUnavailable("subscription login absent or expired")` with `reason="query_raised"`. This is a divergence from the TEA Delivery-Finding intent ("map a raised **transport** error") — the implemented catch is wider than "transport" and was not logged as a deviation. Raised as a blocking review finding below (not a clean deviation, a defect).

## TEA Assessment — Round 2 (red-phase rework)

**Tests Required:** Yes — the Reviewer's blocking fixes are test-driven (mislabel pinned by a non-auth-exception test; the `query_raised` event made a real test; the weak guard tightened).

**Test File:** `tests/agents/test_119_4_auth_durability_cost_otel.py` — now **15 tests** (was 11: +3 new, 1 tightened, 1 extended).

**Status:** RED — verified via `testing-runner` (RUN_ID 119-4-tea-red-rework). File collects cleanly; **2 fail for the right reason**, 13 pass (guards + tightened). Raw: `2 failed, 13 passed`.

| Test | Reviewer driver | RED status |
|------|-----------------|-----------|
| `test_internal_processing_error_is_not_mislabeled_as_auth` (NEW) | [HIGH] mislabel | **failing** — broad catch maps an internal `ValueError` to `AgentSdkAuthUnavailable` + fires `narrator.auth_unavailable reason=query_raised` |
| `test_raised_query_emits_auth_event_before_raise` (NEW) | [MEDIUM] query_raised event + [HIGH] non-committal headline | **failing** — message asserts auth only; no "transport" acknowledgement |
| `test_is_error_still_raises_no_silent_success` (TIGHTENED) | [MEDIUM] weak guard | passing — base `AnthropicSdkClientError` → exact `AgentSdkAuthUnavailable` |
| `test_max_turns_does_not_emit_spurious_auth_event` (NEW) | [LOW] | passing (guard) — `error_max_turns` raises `AnthropicSdkLoopExceeded`, no auth event |
| `test_usage_surfaces_sdk_reported_cost_none_honestly` (NEW) | [LOW] | passing (guard) — `total_cost_usd=None` surfaces as `None`, key present, not fabricated `0.0` |
| `test_usage_surfaces_never_fabricate_subscription_budget` (EXTENDED) | [LOW] | passing (guard) — now also checks `llm.request` span attrs |

**How the contract resolves the Reviewer's two requests — by error ORIGIN.** A transport `query()` raise → `AgentSdkAuthUnavailable` + `narrator.auth_unavailable` (AC1'; existing #3/#4 + new query_raised event test). An internal loop-body raise → propagates raw, no auth signal (the [HIGH] pin). This deliberately forbids the "broad catch + soft message" option — the event name and exception type would still assert auth — and points Dev at a loop restructure, not a type-narrow (the fakes raise a bare `RuntimeError`).

### Rule Coverage (round 2)

| Rule (lang-review/python.md) | Test | Status |
|------|------|--------|
| #1 catch specifically / HONESTY — non-auth not mislabeled as auth | `test_internal_processing_error_is_not_mislabeled_as_auth` | failing (RED) |
| #1 No Silent Fallbacks — `None` spend surfaced as `None`, not `0.0` | `test_usage_surfaces_sdk_reported_cost_none_honestly` | passing (guard) |
| #6 Test quality — exact subclass not base | `test_is_error_still_raises_no_silent_success` (tightened) | passing (guard) |
| #6 Test quality — guard covers span attrs too | `test_usage_surfaces_never_fabricate_subscription_budget` (extended) | passing (guard) |

**Self-check:** 0 vacuous tests; every assertion checks a specific type / value / event presence / event absence. Cause survival asserted robustly (`isinstance(raised, ValueError) or isinstance(raised.__cause__, ValueError)`) so Dev may propagate raw OR `raise … from exc`. Comment-honesty [LOW] is flagged as a Delivery Finding — not test-pinnable without a forbidden source-text grep.

**Handoff:** To Dev (Naomi Nagata) for GREEN — narrow/restructure the catch so internal errors escape un-relabeled, add a "transport" acknowledgement to the query-raised headline, and apply the [LOW] comment/docstring honesty fixes by hand.

## Dev Assessment — Round 2 (green-phase rework)

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/anthropic_sdk_client.py` — (1) **loop restructure** ([HIGH] mislabel fix): replaced `async for message in query(...)` + a broad `except Exception` with a hand-driven `aiter()`/`anext()` loop. The auth-mapping catch now wraps ONLY the transport boundary (`await anext(...)`); our message processing runs OUTSIDE it, so an internal/non-auth error propagates raw and is never relabeled as auth. (2) The transport-raise headline now reads "subscription login absent/expired **or a transport error**" so it no longer asserts auth as the sole cause ([HIGH]/wording). The `reason="query_raised"` event and the `AgentSdkAuthUnavailable` mapping are preserved for the AC1' contract. (3) [LOW] comment-honesty cluster applied by hand: module-constant "**successful** inference", and the `AgentSdkAuthUnavailable` + `_emit_auth_unavailable` docstrings now describe the real raise conditions (two transport surfaces; internal errors NOT mapped).

**Tests:** 15/15 passing (GREEN) on `tests/agents/test_119_4_auth_durability_cost_otel.py` — verified via `testing-runner` (RUN_ID 119-4-dev-green-rework). The 2 previously-failing tests now pass; all 13 guards hold. **Regression:** `tests/agents/` full suite **1975 passed, 2 skipped** — no regression from the iterator restructure. **ruff** check + format clean; **pyright** 0 errors.

**Approach:** Minimal and contract-faithful. The only structural change is the hand-driven iterator (the smallest change that separates transport-origin from body-origin errors — a pure type-narrow would have broken the bare-`RuntimeError` AC1' fakes, exactly as TEA flagged). No new abstraction; no behavior change to the usage event, the cost ledger, the ceiling, or convergence — only the error path's honesty and the comment/docstring accuracy.

**Branch:** `feat/119-4-auth-durability-cost-observability` (pushed).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results — Round 2

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 15/15 story + 1975 pass / 2 skip; ruff+pyright clean; 1 smell | confirmed 1 → [LOW] (cost_safety literal) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed [EDGE] below |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed [SILENT] below |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 2 → [LOW] (reason-asymmetry, ordering-not-pinned); 4 noted low/acceptable |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 → [LOW][DOC] ("successful inference" overclaim, "raised earlier" imprecise) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed [TYPE] below |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — self-assessed [SEC] below |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed [SIMPLE] below |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 2 → [LOW] (cost_safety literal = dup of #1; aclose hygiene, not a regression) |

**All received:** Yes (4 enabled returned, 5 disabled via `workflow.reviewer_subagents` and self-assessed)
**Total findings:** 0 blocking, 7 non-blocking [LOW]/[MEDIUM] confirmed (several overlapping), 0 dismissed

## Reviewer Assessment — Round 2

**Verdict:** APPROVED

The round-1 rejection is fully answered. The dishonest error path is fixed at the structural level — not papered over with softer wording — and the two untested branches are now pinned. Every round-2 finding is [LOW]; there is no Critical or High issue. A third round-trip over a one-word comment imprecision would be disproportionate over-blocking (the severity table reserves rejection for Critical/High). Approved, with the [LOW]s captured for a finish-time tidy or follow-up.

**Data flow traced:** a player turn → `complete_with_tools` → `aiter(query(...))` → per-message `await anext(...)` (transport boundary) → message processing (our code) → terminal `ResultMessage` → usage/cost OTEL + `narrator.sdk.usage` (auth_path/cost_basis/sdk_reported_cost) → `is_error` gate (raise `AgentSdkAuthUnavailable` or `AnthropicSdkLoopExceeded` with the panel event). A transport-boundary raise maps to auth + event; an internal-processing raise propagates raw. Verified safe: the failure surfaces are loud, typed, and panel-visible, and a non-auth fault is no longer relabeled as auth.

### Round-1 blocking issues — resolution

| Round-1 Issue | Status | Evidence |
|---------------|--------|----------|
| [HIGH] broad `except Exception` mislabels any in-loop error as auth | **RESOLVED** | `anthropic_sdk_client.py:417-443` — the auth-catch now wraps ONLY `await anext(...)` (`:420`); message processing (`:445`+) runs in the `while` body outside it. `test_internal_processing_error_is_not_mislabeled_as_auth` passes (internal `ValueError` propagates raw, no auth event). Rule-checker traced + confirmed. |
| [HIGH]/wording headline asserts auth as sole cause | **RESOLVED** | `:434-441` message now reads "subscription login absent/expired **or a transport error**" + chains `from exc`; `test_raised_query_emits_auth_event_before_raise` pins the "transport" acknowledgement. |
| [MEDIUM] query_raised branch event untested | **RESOLVED** | `test_raised_query_emits_auth_event_before_raise` asserts the event + `reason="query_raised"` fires before the raise. |
| [MEDIUM] weak negative guard (base class) | **RESOLVED** | `test:273` tightened to `pytest.raises(AgentSdkAuthUnavailable)`. |
| [LOW] additional tests (max_turns, None-cost, span-attr) | **RESOLVED** | three new guard tests added, all passing. |
| [LOW] comment-honesty cluster | **MOSTLY RESOLVED** | three comments fixed; one over-corrected (see [LOW][DOC] below). |

### Observations

- [VERIFIED] The [HIGH] mislabel is structurally fixed — `anthropic_sdk_client.py:417-443`. The `except Exception as exc` (`:426`) wraps only `await anext(message_stream)` (`:420`, the transport boundary); our message processing at `:445`+ is in the `while` body, outside the catch. An internal error therefore propagates raw. Complies with lang-review #1 ("catch specifically when the type is known") and the OTEL honesty rule. Evidence: read + rule-checker trace + passing `test_internal_processing_error_is_not_mislabeled_as_auth`.
- [VERIFIED] [RULE] `StopAsyncIteration` handled correctly — `:421` `except StopAsyncIteration: break` precedes `:426`; `StopAsyncIteration` derives from `BaseException` not `Exception`, so it cannot be swallowed by the auth-catch (rule-checker runtime-verified). The loop terminates cleanly; an empty stream then hits the `result_msg is None` fail-loud raise. Complies with #9 (async pitfalls).
- [VERIFIED] [SILENT] (self-assessed; silent_failure_hunter disabled) The catch does NOT swallow — it emits `narrator.auth_unavailable` then `raise … from exc` (`:435-443`). No bare except, no `pass`, no silent fallback. The entire rework exists to STOP a silent mislabel. Clean.
- [VERIFIED] [EDGE] (self-assessed; edge_hunter disabled) Boundary paths enumerated and covered: empty stream → `result_msg is None` loud raise; transport raise → auth+event; `is_error` → auth+event; `error_max_turns` → `AnthropicSdkLoopExceeded` with NO auth event (pinned by `test_max_turns_does_not_emit_spurious_auth_event`); internal body raise → raw; `total_cost_usd=None` → surfaced as `None`. No unhandled path.
- [VERIFIED] [TYPE] (self-assessed; type_design disabled) No new types; the query-raised path maps to the existing typed `AgentSdkAuthUnavailable` (not a stringly-typed raise), cause chained. `_record_into` test helper lacks a return annotation (rule-checker #3) — test-helper, rule-exempt, [LOW].
- [VERIFIED] [SEC] (self-assessed; security disabled) `detail=str(exc)` is operator-visible only (OTEL event + logger). No PAYG credential exists on this path — `assert_subscription_auth()` requires both `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` UNSET — so no token can leak through the detail. No new input-validation boundary. Clean.
- [VERIFIED] [SIMPLE] (self-assessed; simplifier disabled) The hand-driven `aiter()`/`anext()` loop is the MINIMAL change that separates transport-origin from body-origin errors (a type-narrow would break the bare-`RuntimeError` AC1' fakes). No over-engineering; no dead code introduced.
- [LOW] [DOC] Module-constant comment overclaims — `:94` "affirms a **successful** inference drew the free Max subscription pool". But `narrator.sdk.usage` (carrying `auth_path`) fires at `:532-550`, INSIDE the `with llm_request_span` block, which is BEFORE the `is_error` gate at `:568` — so an `is_error`/auth-failure result emits the usage+auth_path label too. Accurate framing: "every **transport-completed** inference." Confirmed by line trace (comment-analyzer, high-confidence factual / [LOW] severity — comment only, the `auth_path` value itself is correct).
- [LOW] [DOC] `_emit_auth_unavailable` docstring (`:~895`) calls the `error_max_turns` exit "raised earlier" — it's a branch exit (`:569` → `AnthropicSdkLoopExceeded`), not temporal precedence. Net contract correct, phrasing imprecise. (comment-analyzer)
- [LOW] [TEST] `test_auth_failure_emits_watcher_event_before_raise` (the `is_error` branch) does not assert `reason="is_error"`, while the query_raised test asserts its `reason`. A future refactor emitting `reason="query_raised"` from the `is_error` branch would not be caught. Asymmetric coverage. (test-analyzer #6)
- [LOW] [TEST] The auth-event tests verify event PRESENCE, not event-BEFORE-raise ORDERING (the docstrings imply ordering). Production structure (emit then raise, adjacent statements) makes the regression unlikely and precise ordering is awkward to pin; acceptable. (test-analyzer #1)
- [LOW] [SIMPLE]/[RULE] `cost_safety.py:314` uses the bare literal `"notional"` instead of `_COST_BASIS_NOTIONAL`. Pre-existing (round-1, already accepted), NOT a round-2 regression. The obvious "import the constant" fix is WRONG — `anthropic_sdk_client` already imports `cost_safety`, so importing back is a circular import; a real fix needs a shared constants module. Non-blocking. (preflight + rule-checker #13)
- [LOW] [RULE] The hand-driven loop does not `aclose()` the async generator if message processing raises — NOT a regression: the prior `async for message in query(...)` also relied on GC (async-for never aclose()'s either). `contextlib.aclosing()` would be a nice-to-have. (rule-checker #7)

### Rule Compliance (lang-review/python.md)

- **#1 silent exception swallowing / catch specifically** — the round-1 VIOLATION is RESOLVED. The `except Exception` now wraps exactly one `await anext(...)`; message processing is outside it; the catch re-raises with cause + emits the event first. The residual breadth (not knowing the SDK's exception type at the boundary) is genuinely undisambiguable and documented in the comment + message. **Compliant.**
- **#3 type annotations** — production fully annotated; `_record_into` test helper missing a return type — [LOW], rule-exempt (test helper).
- **#4 logging** — `_emit_auth_unavailable` uses `logger.error` (%-style) on an auth-failure error path; consistent with the round-1-accepted `session.cost_ceiling_exceeded` precedent and the OTEL max-visibility doctrine. Compliant.
- **#6 test quality** — 13/15 tests re-checked by rule-checker: all assertions specific (exact value/type/event-presence/event-absence/`pytest.approx`), correct monkeypatch targets (patch where used). No vacuous assertions. Compliant.
- **#7 resource leaks** — async generator not explicitly `aclose()`'d on a body exception — [LOW], not a regression (see observation).
- **#9 async/await** — `aiter()`/`anext()` are 3.10+ builtins (project on 3.14), correctly awaited; `StopAsyncIteration` (BaseException) not subsumed by `except Exception`; no missing await, no blocking call in async. Compliant.
- **#13 fix-introduced regressions** — the restructure reuses the existing typed exception (no wrong type), the `error_max_turns` early-exit correctly precedes the auth emit, and the catch narrowing is sound. The only fix-adjacent inconsistency is the pre-existing `cost_safety` literal — [LOW].
- **#2/#5/#8/#10/#11/#12** — N/A or clean (no mutable defaults, no path/deserialization/SQL/injection, no star imports, no dependency changes).

### Devil's Advocate

Argue the code is broken. Attack one: the restructure moved message processing outside the transport catch — so does a transport failure that occurs MID-stream (after several messages) still map to auth? Yes — `anext()` runs every iteration, so a raise on the 5th `anext()` is still caught at `:426` and mapped. No regression there. Attack two: the `except Exception` around `anext()` could still catch a non-transport fault if the SDK's own generator body has a bug — that bug surfaces through `anext()` and gets the auth label. But that IS the transport boundary failing, and the message names "a transport error" as an alternative cause with the original chained, so the panel is not asserting a diagnosis it can't support. Honest enough. Attack three: a confused operator reads the source comment "a successful inference drew the free pool" (`:94`), then sees a `narrator.sdk.usage` event with `auth_path=subscription` IMMEDIATELY followed by `narrator.auth_unavailable` for the same failed turn, and concludes the panel is contradicting itself. That confusion is real but it is a comment imprecision, not a behavior bug — the usage event legitimately accounts for the tokens a failed attempt consumed, and I have flagged the comment as [LOW][DOC]. Attack four: empty stream — `query()` yields nothing → `StopAsyncIteration` → `break` → `result_msg is None` → loud `AnthropicSdkClientError` (No Silent Fallbacks). Safe. Attack five: the `is_error` branch could one day emit `reason="query_raised"` after a careless refactor and no test would catch the mislabel because the `is_error` test omits the `reason` assertion (test-analyzer #6). Real, but [LOW] — the event name and the raise type are both tested, and `reason` is a secondary discriminator. Attack six: under a non-CPython runtime the un-`aclose()`'d SDK generator could linger — but the project runs CPython 3.14 and the prior `async for` had identical GC-reliance, so this is not introduced here. Conclusion: every attack surfaces only [LOW] issues. The load-bearing honesty contract — the panel never asserts an auth cause for a non-auth fault — holds under adversarial reading.

### Reviewer (audit) — Round 2 deviations

- **TEA — "Pinned the STRONG honesty option over the Reviewer's softer 'OR', discriminated by error ORIGIN not exception type"** → ✓ ACCEPTED by Reviewer: this is the correct, stronger reading of my round-1 fix text. Softening only the wording (the weak "OR") would leave the event name + exception type asserting auth; forbidding any auth signal for a non-auth error is the honest posture, and pinning by origin (not type) is what reconciles it with the bare-`RuntimeError` AC1' fakes. Sound and well-reasoned.
- **Dev — "No deviations from spec (round 2 — green rework)"** → ✓ ACCEPTED by Reviewer: the diff implements exactly the origin-based contract the round-2 tests pin (hand-driven `aiter`/`anext`, transport-acknowledging headline, the [LOW] comment fixes). No data-structure or algorithm divergence. Confirmed against the diff.

**Handoff:** To SM (Camina Drummer) for finish-story.