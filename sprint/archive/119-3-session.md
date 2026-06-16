---
story_id: "119-3"
jira_key: ""
epic: ""
workflow: "sdd"
---
# Story 119-3: Narrator Agent SDK Port

## Story Details
- **ID:** 119-3
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** sdd
- **Stack Parent:** 119-1 (Conditional on 119-1 NO-GO; mutually exclusive with 119-2)

## Workflow Tracking
**Workflow:** sdd
**Phase:** finish
**Phase Started:** 2026-06-16T09:25:53Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T02:01:52Z | 2026-06-16T04:56:19Z | 2h 54m |
| red | 2026-06-16T04:56:19Z | 2026-06-16T05:39:17Z | 42m 58s |
| green | 2026-06-16T05:39:17Z | 2026-06-16T08:53:58Z | 3h 14m |
| spec-check | 2026-06-16T08:53:58Z | 2026-06-16T09:02:31Z | 8m 33s |
| verify | 2026-06-16T09:02:31Z | 2026-06-16T09:12:16Z | 9m 45s |
| review | 2026-06-16T09:12:16Z | 2026-06-16T09:23:51Z | 11m 35s |
| spec-reconcile | 2026-06-16T09:23:51Z | 2026-06-16T09:25:53Z | 2m 2s |
| finish | 2026-06-16T09:25:53Z | - | - |

## Sm Assessment

**Workflow choice:** Story was tagged `tdd`; SM escalated to `sdd` (Operator decision) because this is an 8pt architectural port with no design spec — sdd adds architect spec-check (post-green) + spec-reconcile (post-review) governance and deviation tracking, which an undesigned port of the narrator tool-loop warrants.

**Spec-first routing (deliberate deviation):** sdd's machine routes setup → red (TEA). Per Operator decision, the Architect (Neo) authors the port design spec BEFORE red so TEA writes tests against a real spec, not an unshaped port. The setup handoff therefore routes to Architect first; Neo hands to TEA for red once the spec lands. sdd's spec-check/spec-reconcile gates then govern fidelity against that spec.

**Dependency:** `depends_on: 119-1` (the spike) is satisfied — 119-1 is `done`. GO/derisked: `scripts/spike_119_3_agentsdk_subscription.py` already proves clean subscription inference.

**Key landmines for the spec to resolve:** (1) claude-agent-sdk inherits project context from cwd — the smoke test answered in an SM persona; the port MUST pin system_prompt + cwd + setting_sources. (2) No-Silent-Fallbacks: both creds unset, fail-loud if auth absent, never silent PAYG. (3) Preserve every narration tool contract, complete_with_tools convergence, and OTEL — the manual ~120-line loop maps onto the SDK's loop model.

**Jira:** none (project has no Jira configured) — claim skipped, not an oversight.

**Next agent:** Architect (Neo) — author the port design spec, then hand to TEA for red.

## Port Design Specification

**REQUIRED BEFORE RED PHASE:** Architect (Neo) must author `docs/superpowers/specs/2026-06-15-narrator-agentsdk-port-design.md` before the red phase begins. TEA writes red tests against the design spec. The sdd spec-check and spec-reconcile gates GOVERN specification fidelity; they do NOT author the spec.

**STATUS: AUTHORED (2026-06-15), AMENDED + VERIFIED (2026-06-16) by Architect (Neo). RED-READY — no remaining BLOCKING open questions.** Spec lives at `docs/superpowers/specs/2026-06-15-narrator-agentsdk-port-design.md`. 2026-06-16: scope expanded to the four Haiku callers per Operator ruling on DF-1/OQ-7 (8→13 pts); the `output_format` spike (`scripts/spike_119_3_haiku_outputformat.py`) then resolved the load-bearing forced-extraction risk — **Path A GO at `max_turns=2`; OQ-15/OQ-16 RESOLVED.** The only residual is the OQ-3 green-phase real-schema round-trip gate (non-blocking for red).

## Architect Assessment

**Decision:** Port the narrator inference path off the raw `anthropic` Messages SDK onto `claude-agent-sdk` with subscription auth, confined to a single seam: the Story-91-1 construction choke point (`llm_factory.build_async_anthropic`, `llm_factory.py:77-97`) and the body of `AnthropicSdkClient.complete_with_tools` (`anthropic_sdk_client.py:248-705`). The `ToolingLlmClient` signature, the `ToolingResult` dataclass, the 26-tool registry (`tool_registry.py`), the orchestrator, `cost_safety`, and all OTEL span helpers are REUSED UNCHANGED. The 26 Pydantic tool schemas are re-expressed as Agent-SDK `@tool`/`create_sdk_mcp_server` tools at the client boundary (not in the registry), and the SDK's own `query()` loop replaces the manual `stop_reason==tool_use` re-call loop — with a thin `@tool` handler bridge that re-enters `default_registry.dispatch` so WRITE-tool mutations, perception filtering, and per-tool OTEL spans stay live.

**Rationale:** Smallest change that moves the transport. The 119-1 NO-GO proved raw-SDK-over-OAuth routes to the empty PAYG ledger; only the Agent SDK (via the bundled CLI's subscription login) draws the free pool — proven by `scripts/spike_119_3_agentsdk_subscription.py`. Reuse-first: the frozen signature means rollback is a single-commit revert with zero caller changes.

**2026-06-16 scope expansion + verification:** Operator RULED IN the four Haiku callers (Intent Router, aside, unseeded-objective classifier, archetype inference). They port too, through the same choke point (§6.4), each preserving its structured-payload contract (`dict`/`str`/`None`) and caller-tagged OTEL + `session_id` cost-safety. **The hard part — RESOLVED:** three of the four rely on forced `tool_choice` structured extraction, which the Agent SDK CANNOT express (no `tool_choice`, handlers always execute). The `output_format` spike settled it: **Path A — `output_format={"type":"json_schema","schema": tool_schema}` → `ResultMessage.structured_output` — is VERIFIED GO** (API-enforced, on `claude-haiku-4-5`/subscription), so it IS the implementation; Path B (prompt-coerced) is dropped to documented-unused. **Caveat: `max_turns=2`, not `1`** — the SDK spends an internal finalize turn, so `max_turns=1` fails closed (`error_max_turns`); the +1 is MANDATORY and is a RED/GREEN guardrail in §9. Canonical surface: `ClaudeAgentOptions(model="claude-haiku-4-5", max_turns=2, allowed_tools=[], system_prompt=..., output_format={...}); async for msg in query(...): if ResultMessage: return msg.structured_output`.

**Alternatives Considered:**
- 119-2 (re-auth the raw SDK to subscription OAuth): rejected — the 119-1 spike NO-GO is exactly this path PAYGing.
- Haiku forced-tool via `PreToolUse`-deny hook (read tool input without execution): rejected as primary — it does NOT force the model to call the tool (no `tool_choice`), reading input from a hook is unverified (OQ-16), and it is strictly more fragile than Path B for no gain.
- A process-wide static SDK-MCP server: rejected — the tool set is ruleset-filtered per turn, so a static server would silently advertise the wrong tools (No Silent Fallbacks). Server is built per `complete_with_tools` call.

**Implementation Guidance (for TEA red, then Dev):**
- Pin context isolation in `ClaudeAgentOptions`: `system_prompt=<assembled narrator string, plain — no preset>`, `cwd=<non-repo dir>`, `setting_sources=[]`, `add_dirs=[]` (AC1, the landmine). Behavioral non-contamination test is the gate.
- Invert the auth check: narrator path must RAISE if `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` is SET (a set key re-routes to PAYG); both unset → subscription resolution; auth-absent → raise `AgentSdkAuthUnavailable`, never a degraded-success result (AC2, No Silent Fallbacks).
- Preserve every `ToolingResult` field and every OTEL span (§7.4 map). Where the Agent SDK can't supply a figure (per-TTL cache split, OQ-6), populate documented-zero + a loud "unavailable on agent-sdk" marker — never a silent 0.
- Haiku (2026-06-16, VERIFIED): port each of the four single-shot sites preserving its `dict`/`str`/`None` return contract and its caller-tagged `llm.request`/`llm.sdk.usage` + `session_id` cost-safety. The three forced-extraction sites use **Path A `output_format` at `max_turns=2`**, reading `ResultMessage.structured_output`; raise the site's existing loud error on `structured_output=None`/`is_error`. Do NOT implement Path B. Do NOT hardcode `max_turns=1` (fails closed). `_AsideLlm` is the easy one (already no-tools), also `max_turns=2`.
- The remaining Open Questions (§11) are non-blocking. **OQ-3** is now a GREEN-PHASE GATE (Dev round-trips the REAL `DispatchPackage.model_json_schema()` through `output_format` before commit; apply a schema-adapt shim if rejected). OQ-4 (setting_sources isolation) and OQ-9 (fake-`query` injection seam) remain the load-bearing red-test concerns; OQ-1/2/6/10/11/13/14/17 are confirm-against-installed-SDK or follow-up.
- Dependency: `claude-agent-sdk` is NOT in `sidequest-server/pyproject.toml` or root (spikes used `uv run --with`). Declaring it + an import-wiring test is a first Dev step.

**Handoff:** To TEA (red) — write failing tests against this spec; spec-check/spec-reconcile gates govern fidelity. **DF-1 RESOLVED (Haiku ruled in); DF-5/OQ-15/OQ-16 RESOLVED (Path A GO @ `max_turns=2`). No remaining BLOCKING open questions — RED-READY.** TEA's red MUST drive the confirmed `output_format` `max_turns=2` path (guardrail in §9); the OQ-3 real-schema round-trip is a green-phase verification gate, not a red blocker.

## Delivery Findings

### Architect (design)
- **Question** (blocking) — **DF-1: RESOLVED 2026-06-16 (RULED IN).** Operator ruled the four Haiku callers (`IntentRouter`, aside, classifier, archetype) move off PAYG in this story, not a follow-up (8→13 pts). §6.4 + OQ-15/16/17 cover the design. *Found by Architect during design; resolved by Operator ruling.*
- **Risk** (blocking) — **DF-5: RESOLVED GO-WITH-CAVEAT (VERIFIED 2026-06-16, `scripts/spike_119_3_haiku_outputformat.py`).** The Agent SDK has no `tool_choice`, but the forced-extraction need is met by its first-class `output_format` JSON-schema structured output (Path A, API-enforced) — confirmed on `claude-haiku-4-5`/subscription, accepting `{"type":"json_schema","schema": <dict>}` verbatim and returning a clean schema-valid dict via `ResultMessage.structured_output`. **Caveat: `max_turns=2`, not `1`** (the SDK spends an internal finalize turn; `max_turns=1` fails closed with `error_max_turns`). Path B dropped to documented-unused. **Residual (OQ-3-adjacent, NOT a red blocker):** the spike used a minimal hand-written schema — the real `DispatchPackage.model_json_schema()` ($defs/nested) round-trip is a green-phase gate. Affects `sidequest/agents/llm_factory.py`. *Found by Architect during design; resolved by the output_format spike.*
- **Improvement** (non-blocking): Subscription `total_cost_usd` is the CLI's *notional* estimate (narrator AND Haiku — same `session_id` ledger), not a billed charge; the cost-runaway detector + $10 ceiling (`cost_safety.py`) are PAYG-dollar-calibrated and likely need recalibration / re-framing as notional-shape signals. Affects `sidequest/agents/cost_safety.py`. *Found by Architect during design.*
- **Question** (non-blocking): The aside's `tool_choice={"type":"none"}` cache-prefix-preservation trick has no Agent-SDK analog (CLI owns caching); aside likely becomes a plain no-tools completion. Affects `sidequest/agents/aside_resolver.py`. *Found by Architect during design.*
- **Gap** (non-blocking): The `claude-code-guide` doc claims subscription OAuth is unsupported by the Agent SDK, contradicting the working spike GO; spike is authoritative (every-playtest-is-production). Worth a note in ADR-101's amendment. *Found by Architect during design.*

## Context Summary

**WHAT:** Port the SideQuest narrator's inference path from the raw `anthropic` Messages SDK onto the `claude-agent-sdk` package with subscription auth. Activated 2026-06-15 by the 119-1 spike NO-GO: raw anthropic Messages SDK over subscription OAuth routes to the metered API-platform ledger (400 "credit balance too low"), NOT the subscription pool. The claude-agent-sdk with subscription login draws the subscription pool cleanly — the GO/derisked path.

**KEY FILES (sidequest-server):**
- `sidequest/agents/llm_factory.py:77-97` — `build_async_anthropic()`, the SINGLE Story-91-1 auth choke point (Sonnet narrator + Haiku classifier/router + aside + archetype all flow through it)
- `sidequest/agents/anthropic_sdk_client.py:248-705` — `complete_with_tools()`, the manual ~120-line tool loop (reads response.stop_reason==tool_use, appends assistant/user tool blocks, re-calls messages.create). This is what gets rewritten onto the Agent SDK's own tool/loop model.
- `sidequest/agents/tool_registry.py:225-249` — Pydantic-generated tool schemas to re-express as Agent SDK tools.

**DERISK REFERENCE:** `scripts/spike_119_3_agentsdk_subscription.py` — runs claude-agent-sdk with BOTH ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN unset, returns clean Sonnet inference (is_error=False, service_tier='standard', no 400). Use as the working seed.

## Acceptance Criteria

1. **System Prompt & Context Isolation:** Agent SDK client pins system_prompt + cwd + setting_sources so it does NOT inherit project CLAUDE.md / repo context from the launch cwd (the spike smoke test absorbed an SM persona). Covered by a test asserting narrator output is not contaminated by repo project context.
2. **Subscription Auth, No PAYG Fallback:** ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN both unset in server env; auth resolves via the subscription login profile. Fail-loud if absent (no silent PAYG fallback — SOUL No-Silent-Fallbacks).
3. **Port Fidelity:** Preserve EVERY narration tool contract, the complete_with_tools convergence semantics, and OTEL spans.

## Branch Strategy
**Branch Strategy:** gitflow (feat/119-3-narrator-agentsdk-port)

## TEA Assessment

**Tests Required:** Yes
**Reason:** 13pt architectural transport port with AC-bearing behavioral contracts (context isolation, fail-loud auth, port fidelity). Not a chore.

**Test Files (all new, `sidequest-server`):**
- `tests/agents/fakes/fake_agent_sdk.py` — hermetic, duck-typed `claude-agent-sdk` transport fakes (no `claude_agent_sdk` import; the OQ-9 fake-`query` seam). `FakeQuery` / `ContaminatingFakeQuery` / `RaisingFakeQuery` + scripted-stream builders.
- `tests/agents/test_119_3_dependency_and_seam.py` — dep declared/importable + module-level `query` seam present (4 tests).
- `tests/agents/test_119_3_context_isolation.py` — AC1: options-pin unit gate + behavioral spike-regression + Haiku router isolation (3 tests).
- `tests/agents/test_119_3_subscription_auth.py` — AC2: narrator + Haiku fail-loud auth, both-creds-unset resolves subscription, auth-absent raises-not-degrades (10 tests).
- `tests/agents/test_119_3_narrator_port.py` — AC3 narrator: convergence, max_turns→`AnthropicSdkLoopExceeded`, OTEL (`narrator.tool_loop` + `narrator.sdk.usage`) preserved, toolless path, `@tool`→dispatch bridge, orchestrator wiring (6 tests).
- `tests/agents/test_119_3_haiku_port.py` — AC3 Haiku: per-site `structured_output` dict-or-raise, aside text, `max_turns=2`+`output_format` guardrail, `max_turns=1` fail-closed, per-site caller-tagged OTEL + ledger cost-safety (15 tests).

**Tests Written:** 38 tests covering AC1/AC2/AC3 (narrator + 4 Haiku sites) + dependency/seam wiring.
**Status:** RED (38 failing — verified `uv run pytest -n0`, all fail for feature-not-implemented reasons: no-key construction guard not inverted, `AgentSdkAuthUnavailable` / `_build_narration_tool_handler` / module-level `query` absent, `build_async_anthropic` still the choke point). Full agents suite still collects (2138).

### Rule Coverage

| Rule (python.md / SOUL) | Test(s) | Status |
|---|---|---|
| No Silent Fallbacks (auth) | `test_narrator_auth_absent_raises_not_degrades`, `test_haiku_site_auth_absent_raises_not_silent` | failing |
| No Silent Fallbacks (PAYG re-route) | `test_narrator_raises_when_payg_cred_set`, `test_haiku_site_raises_when_api_key_set` | failing |
| No Silent Fallbacks (context absorption) | `test_narrator_options_pin_isolation`, `test_narrator_output_not_contaminated_by_repo_persona`, `test_haiku_router_options_pin_isolation` | failing |
| OTEL Observability Principle | `test_narrator_tool_loop_span_and_usage_event_preserved`, `test_haiku_site_emits_caller_tagged_span_and_records_cost` | failing |
| Every Test Suite Needs a Wiring Test | `test_complete_with_tools_reachable_from_orchestrator` | failing |
| No Source-Text Wiring Tests | all (behavior + OTEL + captured-options; zero `read_text()` greps) | n/a |
| Dependency hygiene (#12) | `test_claude_agent_sdk_declared_in_pyproject` | failing |
| `max_turns=2` fail-closed guardrail (spec §9) | `test_forced_extraction_sites_use_output_format_at_max_turns_two`, `test_max_turns_one_fail_closed_shape_raises`, `test_aside_uses_no_tools_at_max_turns_two` | failing |
| Structured-payload contract preserved | `test_intent_router_emit_tool_returns_structured_output` (+ raises_on_none), `test_unseeded_classifier_*`, `test_archetype_inference_*`, `test_aside_complete_returns_text` | failing |
| async/await (#9) | all behavioral tests drive `async for msg in query(...)` via the fake seam | failing |

**Rules checked:** the load-bearing python.md/SOUL rules (No Silent Fallbacks ×3, OTEL, wiring, dependency hygiene, async) have test coverage. Implementation-only rules (#2 mutable defaults, #5 paths, #7 resource leaks, #8 deserialization) are Dev-GREEN concerns with no RED surface.
**Self-check:** every test asserts a specific value/exception (no `assert True`, no bare truthy, no `let _ =`); construction-vs-raise ordering audited so no auth/ledger test false-greens on the legacy missing-key error (fixed `test_haiku_site_auth_absent_raises_not_silent` to construct outside `pytest.raises`).

**Handoff:** To Dev (Agent Smith) for GREEN.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The `_record_usage_telemetry` helper reads token counts off `resp.usage` via `getattr`, but the Agent SDK's `ResultMessage.usage` is a `dict` (spec §3.2) — `getattr(dict, "input_tokens", 0)` silently returns 0, so per-call cost would read as $0 unless Dev adapts the usage read to dict-key access. Affects `sidequest/agents/llm_factory.py::_record_usage_telemetry` (and the narrator usage rollup) — adapt to read `usage["input_tokens"]` etc. for the agent-sdk shape. *Found by TEA during test design.*
- **Question** (non-blocking): The new `query` transport seam is pinned as a module-level symbol in BOTH `anthropic_sdk_client` and `llm_factory` (each `from claude_agent_sdk import query`, monkeypatched independently) to mirror the `build_async_anthropic` doctrine. If Dev prefers one shared seam, the import-cycle (`llm_factory` ↔ `anthropic_sdk_client`) must be handled with the existing function-level-import dodge — flagged so the choice is deliberate. Affects both modules. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The full suite has ~88 PRE-EXISTING failures (70 in `tests/integration`) — WN/WWN combat + chargen + wiring tests (`test_106_2_wwn_defensive_reprisal`, `test_102_4_*`, `test_wwn_*`, `test_dice_path_spell_cast_102_2`, etc.) failing with `DiceDispatchError: unknown beat_id 'committed_blow' for encounter 'combat' — available: []`. **Baselined against `origin/develop`'s transport (path-limited stash of my two source files): identical failure set — `mine ⊆ develop`, zero regressions from this port.** These are epic-108 WN-owns-the-round / ADR-106/114/143 *partial* work, not this story. The remaining ~18 of the 88 are heavy-e2e casualties of the global `--timeout=30` under xdist (pass at `--timeout=300`; e.g. `test_resources_wired_on_session_create`). Affects `tests/integration/*` (epic 108) — not a 119-3 deliverable. *Found by Dev during implementation.*
- **Improvement** (non-blocking): TEA's `_record_usage_telemetry` dict-usage Improvement is RESOLVED — the port reads the agent-SDK `ResultMessage.usage` dict via a `_usage_int(usage, key)` helper (`anthropic_sdk_client.py:441-442`, mirrored in `llm_factory`), so per-call cost no longer silently reads $0. Affects `sidequest/agents/llm_factory.py` + `anthropic_sdk_client.py`. *Found by Dev during implementation.*

### TEA (test verification)
- **Improvement** (non-blocking): simplify-reuse flagged that the four single-shot Haiku adapters (`_AsideLlm.complete`, `_IntentRouterLlm.emit_tool`, `_UnseededObjectiveClassifierLlm.emit_tool`, `infer_archetype_from_freeform`) repeat a pre-flight-ceiling → `build_agent_sdk_options` → `llm_request_span`+`_consume_to_result`+`_record_usage_telemetry` → `record_call` → structured-extract skeleton; a `_call_haiku_sdk(...)` + `_extract_structured_output_or_raise(...)` consolidation would cut ~40 lines. NOT applied this story (works against the minimal-diff/single-commit-rollback design value; the genuinely-shared leaf helpers are already factored; the per-site orchestration is deliberately explicit on a cost-safety-critical path with per-site error types). Affects `sidequest/agents/llm_factory.py` — a candidate follow-up refactor once the transport has soaked. *Found by TEA during test verification.*
- **Improvement** (non-blocking): simplify-efficiency flagged `_compose_structured_system` (medium — inline the 4 call sites) and `_consume_to_result` re-implementing `_is_agent_result_message`'s terminal-message duck-check (low — cross-module reuse). Both declined: the named helper carries a load-bearing docstring (WHY the tool name/description fold into the system prompt under Path A), and a cross-module import would couple `llm_factory` to `anthropic_sdk_client` internals for a 1-line check. Affects `sidequest/agents/llm_factory.py`. *Found by TEA during test verification.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_neutral_cwd()` creates a `mkdtemp` dir with no `atexit`/cleanup — one empty dir per process lifetime leaks until reboot. Trivial hygiene fix (register an `atexit shutil.rmtree`). Affects `sidequest/agents/anthropic_sdk_client.py:156-161`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): AC1 context-isolation correctness depends on `claude-agent-sdk` honoring `setting_sources=[]`/`add_dirs=[]`/neutral-`cwd`; the regression test `test_narrator_output_not_contaminated_by_repo_persona` mocks the `query` seam, so it would NOT catch a real-SDK behavior change that re-absorbs repo context. A periodic LIVE smoke (the existing `scripts/spike_119_3_agentsdk_subscription.py` harness) is the only true tripwire. Affects `sidequest/agents/anthropic_sdk_client.py` (isolation) — recommend a gated live smoke in CI/ops, not a code change. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): OQ-17 — the vestigial `IntentRouterCacheFloorError` guard (`llm_factory.py:646-667`) is live-but-uncovered after `test_haiku_cache_control.py` was deleted. A follow-up ticket should delete it or re-home it onto an SDK-exposed cache signal and restore coverage. Affects `sidequest/agents/llm_factory.py`. *Found by Reviewer during code review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Per-tool schema byte-equivalence deferred to the green gate, not red-pinned**
  - Spec source: 2026-06-15-narrator-agentsdk-port-design.md, §9 AC3 "per-tool contract" + §6.4.2 / OQ-3
  - Spec text: "assert each tool's name, description, and input_schema survive the Pydantic→Agent-SDK translation byte-equivalent (the OQ-3 gate)"
  - Implementation: RED pins only that the bare tool name + args reach `default_registry.dispatch` (`test_tool_bridge_dispatches_bare_name_and_accumulates`); the real-schema `@tool`/`output_format` round-trip is left to the spec's own green-phase gate.
  - Rationale: §6.4.2 explicitly makes the REAL `DispatchPackage.model_json_schema()` round-trip a GREEN-PHASE GATE (the SDK must be live to accept/reject the schema), and `claude_agent_sdk` is uninstalled in RED — a red byte-equivalence test would have to guess the `@tool` wrapper's introspection shape (OQ-1 unverified).
  - Severity: minor
  - Forward impact: Dev MUST run the real-schema round-trip before commit (spec §9 GREEN gate); apply the OQ-3 schema-adapt shim if rejected.
- **`@tool`→dispatch bridge tested at a pinned callable factory, not by driving the live SDK loop**
  - Spec source: §9 AC3 "per-tool contract"; §5.3
  - Spec text: "a tool call routed through the @tool bridge invokes default_registry.dispatch with a ToolUseBlock carrying the bare name and the model's args, and the returned ToolResultBlock content flows back to the SDK"
  - Implementation: pinned a `_build_narration_tool_handler(*, bare_name, tool_dispatch, accumulator)` factory and unit-tested its handler; the fake `query` does NOT introspect the SDK-MCP server to invoke handlers.
  - Rationale: the SDK owns the loop and invokes handlers via the in-process MCP server whose structure is OQ-1-unverified; a fake that reached into it would be guessing the transport internals the spec warns against. The factory boundary is the smallest honest seam for "dispatch gets the bare name."
  - Severity: minor
  - Forward impact: Dev must expose an equivalent callable bridge (name `_build_narration_tool_handler` or update this test in lockstep). Full SDK-drives-handler convergence is a live/integration concern (OQ-1/OQ-8).
- **Haiku usage telemetry asserted by caller-tag + ledger record, not token-exact values**
  - Spec source: §7.4 "Haiku llm.request spans + _record_usage_telemetry"; §9 AC3(Haiku) "Per-site OTEL + cost"
  - Spec text: "each ported site opens an llm.request span and emits llm.sdk.usage with the correct caller tag ... and the session_id-keyed check_ceiling/record_call still fire"
  - Implementation: `test_haiku_site_emits_caller_tagged_span_and_records_cost` asserts the `llm.caller`-tagged span fired and a `_SpyLedger` saw `check_ceiling`+`record_call` under the right caller; it does NOT assert exact token/cost numbers.
  - Rationale: the agent-sdk `ResultMessage.usage` dict shape (OQ-2) and per-TTL split (OQ-6) are unverified; pinning token math would couple RED to an unverified adaptation. The [COST-1] attribution axis (caller tag + ledger record) is the load-bearing contract.
  - Severity: minor
  - Forward impact: none for the contract; exact figures verified at green against the installed SDK.
- **New seams pinned that the spec left to "Dev/TEA refine"**
  - Spec source: §6.2 (construction seam), §7.5 (auth error type), §6.2/OQ-9 (fake seam)
  - Spec text: "A new construction seam (e.g. build_agent_sdk_options() or an AgentSdkNarratorClient)..."; "raise an AnthropicSdkClientError subclass (e.g. AgentSdkAuthUnavailable)"
  - Implementation: RED contractually pins (a) module-level `query` in `anthropic_sdk_client` + `llm_factory`; (b) `AgentSdkAuthUnavailable(AnthropicSdkClientError)`; (c) no-`sdk=` `AnthropicSdkClient()` construction succeeding with both creds unset and inverting to raise when a cred is set; (d) `ClaudeAgentOptions` reachable via the captured `query(options=...)` argument (no builder-function name pinned).
  - Rationale: tests are contracts; concrete names are required to make the spec's "e.g." surfaces executable. Chose the spec's own suggested names and inverted the existing `AnthropicSdkClient` ctor (spec §6.2 says its key-presence check "is replaced for the narrator path"), keeping rollback a single-class revert.
  - Severity: minor
  - Forward impact: Dev implements these exact names or updates the pinned tests in lockstep (logged so it's a deliberate, not silent, contract).
- **Per-tool dispatch spans + archetype `{}`/empty-freeform paths not re-pinned (covered by untouched suites)**
  - Spec source: §7.4 "per-tool dispatch spans — Untouched"; §9 AC3(Haiku) archetype `{}`/`None`
  - Spec text: "per-tool dispatch spans (tool_dispatch_span in Registry.dispatch) — Untouched"; archetype "returns ... {} when nothing missing ... None ... on empty freeform"
  - Implementation: the port OTEL test asserts only the narrator-emitted `narrator.tool_loop`/`narrator.sdk.usage`; the archetype RED tests cover the transport-changed dict + out-of-enum paths, not the pre-SDK short-circuit (`{}` / empty-freeform `None`) paths.
  - Rationale: `tool_registry.dispatch` is explicitly OUT of scope/unchanged (its spans are covered by the existing registry suite), and the archetype short-circuits return BEFORE any transport call — unchanged by the port and already green in `test_93_1_archetype_inference.py`.
  - Severity: minor
  - Forward impact: none — those behaviors are guarded by existing green suites that must stay green (spec-check gate).

### Dev (implementation)
- **Full-replace of the obsolete raw-SDK transport test suite (20 deleted, 13 migrated, 2 new)**
  - Spec source: 2026-06-15-narrator-agentsdk-port-design.md, §6.5 (test disposition) + Operator ruling
  - Spec text: "§6.5 — disposition of the legacy raw-`anthropic` transport tests (cache-marker split, `messages.create` loop iterations, cache-TTL prefix/OTEL)"
  - Implementation: Deleted 20 transport-internal test files that pinned machinery the port removes — `test_anthropic_sdk_client.py`, `test_anthropic_sdk_tool_loop_iterations.py`, `test_cache_ttl_prefix_and_otel.py`, `test_haiku_cache_control.py`, `test_narration_multi_text_block.py`, `test_narrator_iteration_cap_toggle.py`, `test_tool_loop_caller_tag.py`, `test_tool_loop_loop_exceeded_visibility.py`, and the epic-60/61/91 cache + cost-runaway followups. Migrated 13 behavioral files onto the `query`/fake-`query` seam; added `test_cost_safety_unit.py` + `test_119_3_narrator_behavior_on_agent_sdk.py`; updated server `conftest.py` hermetic guard to patch the `query` seam. Migration executed by 3 sub-agents (Agent Clones) + me against `/tmp/119_3_migration_cheatsheet.md`.
  - Rationale: Operator approved "full replace" over mechanical per-test porting. The deleted tests asserted raw-`anthropic` internals (cache_control block layout, manual `stop_reason==tool_use` re-call loop, per-TTL cache split) that the Agent SDK deletes — porting them would assert behavior that no longer exists (a vacuous green).
  - Severity: moderate
  - Forward impact: The explicit cache-marker / cache-TTL coverage is gone; the residual cache-floor guard (see OQ-17 entry below) is now live-but-untested. Future caching-strategy work that re-introduces explicit cache control must re-establish coverage.
- **OQ-6: per-TTL cache-creation split emitted as documented-zero (follows spec directive)**
  - Spec source: §7.4 (OTEL span map) / OQ-6
  - Spec text: "Where the Agent SDK can't supply a figure (per-TTL cache split, OQ-6), populate documented-zero + a loud 'unavailable on agent-sdk' marker — never a silent 0."
  - Implementation: `anthropic_sdk_client.py:557-561` sets `cached_input_write_5m_tokens=0` / `cached_input_write_1h_tokens=0` with an inline OQ-6 comment; the aggregate `cache_read_input_tokens` / `cache_creation_input_tokens` ARE preserved (read via `_usage_int`, lines 441-442).
  - Rationale: The agent-SDK `ResultMessage.usage` dict has no 5m-vs-1h breakdown (the CLI owns prompt caching). Documented-zero per the spec, not a silent 0.
  - Severity: minor
  - Forward impact: Narrator cost telemetry loses the 5m-vs-1h cache-write split; aggregate cache figures remain. Re-home if the SDK later exposes the split.
- **OQ-17: Intent-Router cache-floor guard retained live but now vestigial + uncovered**
  - Spec source: §11 OQ-17 (cache TTL/floor follow-up)
  - Spec text: "OQ-17 ... confirm-against-installed-SDK or follow-up."
  - Implementation: Left `IntentRouterCacheFloorError`, `HAIKU_CACHEABLE_PREFIX_FLOOR_TOKENS`, `_INTENT_ROUTER_CACHE_TTL`, and the `build_intent_router_llm` floor check (`llm_factory.py:646-667`) untouched. Its dedicated test (`test_haiku_cache_control.py`) was deleted in the full-replace, so the guard is now live-but-uncovered. The agent-SDK path no longer emits `cache_control` markers, so the guard protects against a trap our code can no longer spring.
  - Rationale: Removing the guard touches the caching strategy (OQ-6/OQ-17) — a follow-up larger than this transport swap. Keeping the port a pure transport change; deferred per the handoff/spec OQ-17.
  - Severity: minor
  - Forward impact: A follow-up must delete the guard or re-home it onto an SDK-exposed cache signal and restore coverage. Until then it can still raise if the router prefix drops below 4096 tokens (currently ~4730 — dormant).
- **Two module-level `query` seams kept rather than one shared seam (resolves TEA Question)**
  - Spec source: §6.2 / OQ-9 (construction + fake seam); TEA Delivery Finding (Question)
  - Spec text: "the new `query` transport seam is pinned as a module-level symbol in BOTH `anthropic_sdk_client` and `llm_factory` ... If Dev prefers one shared seam, the import-cycle must be handled with the existing function-level-import dodge."
  - Implementation: Kept two independently-monkeypatchable module-level `query` symbols (one per module), mirroring the `build_async_anthropic` doctrine, rather than collapsing to a single shared seam.
  - Rationale: The `llm_factory` ↔ `anthropic_sdk_client` import cycle would force a function-level-import dodge for marginal benefit; two seams keep each call site's fake injection local and match the existing per-module doctrine. TEA flagged the choice for deliberate confirmation — confirmed.
  - Severity: minor
  - Forward impact: Tests patch the seam in the module under test; a future consolidation must update both modules in lockstep.

### TEA (test verification)
- **Declined to auto-apply the high-confidence simplify-reuse findings in the verify phase**
  - Spec source: workflows/sdd verify-workflow, Step 5 ("Apply High-Confidence Fixes")
  - Spec text: "For each finding with `confidence: high`: 1. Read the file ... 2. Apply the suggestion (edit the file) 3. Track what was changed and why."
  - Implementation: Ran the simplify fan-out (reuse/quality/efficiency); quality=clean; reuse returned 3 high-confidence consolidation findings (`_call_haiku_sdk`, `_extract_structured_output_or_raise`) + 1 medium; efficiency 2 medium/low. Applied ZERO — working tree left byte-identical to the committed green state. All findings documented as non-blocking Improvements (Delivery Findings → TEA test verification).
  - Rationale: Story scope (highest authority per the spec-authority hierarchy) makes this port a deliberately MINIMAL transport swap with a frozen `ToolingLlmClient`/`ToolingResult` signature for single-commit rollback; the Architect spec-check affirmed the current structure as reuse-correct (leaf helpers already factored). Auto-applying new consolidation abstractions that NO test requires enlarges the diff against that value, and Step-7 `pf check` regression detection is unreliable here (88 documented pre-existing `tests/integration` failures would force spurious reverts). The findings are real but are design-choice refactors, not defects.
  - Severity: minor
  - Forward impact: The reuse consolidation remains a clean follow-up once the new transport has soaked; no behavior change deferred — the declined refactors are structural-only.

### Reviewer (audit)
Every logged deviation is stamped below. No undocumented deviations found beyond what TEA/Dev recorded.
- **TEA (test design) — all 5 entries** (schema byte-equiv deferred, `@tool` bridge at factory not live SDK, Haiku usage by caller-tag, new seams pinned, per-tool/archetype paths covered by untouched suites) → ✓ ACCEPTED: sound red-phase contracting given `claude_agent_sdk` was uninstalled in RED; each is a behavior-preserving test-shape choice with a named green-phase follow-through, all of which the green suite (1993 passed) now satisfies.
- **Dev — Full-replace of the obsolete transport test suite (20 deleted / 13 migrated / 2 new)** → ✓ ACCEPTED: the deleted tests pinned raw-`anthropic` internals (cache_control layout, manual re-call loop) the port deletes; porting them would assert non-existent behavior (vacuous green). Operator-approved. No story-domain coverage lost (preflight confirmed the domain suite grew ~1900 lines).
- **Dev — OQ-6 per-TTL cache split documented-zero** → ✓ ACCEPTED: follows the spec directive verbatim; aggregate cache read/write preserved; the 0s carry a loud comment, not a silent measured-0. Compliant with No Silent Fallbacks.
- **Dev — OQ-17 cache-floor guard retained live but vestigial + uncovered** → ✓ ACCEPTED (with a follow-up flag): keeping the port a pure transport swap is the right call; the guard is dormant (prefix ~4730 > 4096) and cannot mis-fire silently. **This is the one item worth a follow-up ticket** — a later story should delete or re-home it onto an SDK cache signal and restore coverage. Not blocking.
- **Dev — Two module-level `query` seams (not one shared)** → ✓ ACCEPTED: collapsing to one seam would force a function-level-import dodge across the `llm_factory`↔`anthropic_sdk_client` cycle for marginal benefit; two seams keep fake-injection local and match the prior `build_async_anthropic` doctrine.
- **TEA (test verification) — declined to auto-apply high-confidence simplify-reuse findings** → ✓ ACCEPTED: story-scope authority (minimal-diff / single-commit rollback) over a process-doc Step-5, with the Architect's spec-check affirmation and the unreliable-`pf check` rationale. The findings are real but structural-only; correctly deferred and recorded as non-blocking Improvements.

### Architect (reconcile)

**Manifest verification:** All in-flight deviation entries (TEA test design ×5, Dev implementation ×4, TEA test verification ×1) were reviewed for accuracy. Spec source `docs/superpowers/specs/2026-06-15-narrator-agentsdk-port-design.md` (61 KB) exists and the cited sections (§3.6, §6.2, §6.4.2, §6.5, §7.4, §9, §11/OQ-3/OQ-6/OQ-9/OQ-16/OQ-17) are real; the workflow Step-5 citation for the TEA verification entry is accurate. Each entry's Implementation field matches the code (line citations spot-verified during spec-check: OQ-6 documented-zero `anthropic_sdk_client.py:557-561`; OQ-17 floor guard `llm_factory.py:646-667`; the two `query` seams). All entries carry the full 6 fields. No corrections required.

**Missed deviations:** No additional deviations found. The `del max_tokens, tool_choice` signature-compat and the `add_dirs=[]` AC1 hardening are spec-CONFORMANT (spec §3.6 / §6.1), not deviations — already recorded as spec-check observations, not re-logged here.

**AC deferral verification:** No-op — no ACs were deferred or descoped. AC1 (context isolation), AC2 (subscription auth / no-PAYG-fallback), and AC3 (port fidelity) are all DONE and behaviorally GREEN (38 AC-bearing tests within the 1993-passed domain suite; spec-check verified each against the code; Reviewer APPROVED with no Critical/High). The "deferred" tokens elsewhere in this section refer to test-shape choices and structural follow-ups, not AC deferrals.

**Definitive follow-up manifest (the carry-forward, non-blocking):**
1. **OQ-17 — remove or re-home the vestigial Intent-Router cache-floor guard** (`llm_factory.py:646-667`): live-but-uncovered after `test_haiku_cache_control.py` was deleted; the agent-SDK path emits no `cache_control` markers. *The one item that warrants a dedicated follow-up ticket.*
2. **OQ-6 — narrator per-TTL (5m/1h) cache-write split is documented-zero**: aggregate cache figures preserved; re-home if the SDK later exposes the split.
3. **Reviewer hygiene** — `_neutral_cwd()` `atexit` cleanup (one empty dir/process leak) + a periodic LIVE isolation smoke (the contamination regression mocks `query`, so it cannot catch a real-SDK context-absorption regression; use `scripts/spike_119_3_agentsdk_subscription.py`).
4. **Architect design-DF (cost calibration)** — the $10 ceiling / runaway detector are PAYG-dollar-calibrated but now meter *notional* subscription cost; recalibrate as notional-shape signals.
5. **Deferred reuse refactor** — consolidate the 4 Haiku adapters (`_call_haiku_sdk` / `_extract_structured_output_or_raise`) once the transport has soaked (structural-only, no behavior change).

**Spec-reconcile verdict:** Manifest complete and accurate. No spec drift slipped through undocumented. Proceed to SM finish.

## Dev Assessment

**Implementation Complete:** Yes

**Summary:** Ported the narrator inference path + the four single-shot Haiku call sites off the raw `anthropic` Messages SDK onto `claude-agent-sdk` `query()` over subscription auth, confined to the Story-91-1 construction choke point. The narrator's manual `stop_reason==tool_use` re-call loop is replaced by the SDK's own `query()` loop with a `@tool`/`create_sdk_mcp_server` bridge that re-enters `default_registry.dispatch` (WRITE-tool mutations, perception filtering, per-tool OTEL spans stay live). The three forced-extraction Haiku sites use `output_format` JSON-schema structured output at `max_turns=2` (reading `ResultMessage.structured_output`); the aside is a plain no-tools completion. Auth is inverted per AC2 — a set `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` (PAYG re-route) raises `AgentSdkAuthUnavailable`; both unset → subscription; auth-absent → raise, never degrade. OQ-3 gate CONFIRMED: the real `DispatchPackage` schema ($defs/$ref) is accepted verbatim by both `output_format` and `@tool`/`create_sdk_mcp_server` at build time — no schema-adapt shim needed.

**Files Changed (sidequest-server):**
- `pyproject.toml` + `uv.lock` — added `claude-agent-sdk>=0.2.102`
- `sidequest/agents/anthropic_sdk_client.py` — narrator `complete_with_tools` rewritten onto the SDK `query()` loop; new `query` seam, `AgentSdkAuthUnavailable`, `assert_subscription_auth()`, `build_agent_sdk_options()`, `_build_narration_tool_handler()`, `_build_narration_mcp()`, `_usage_int()`; deleted the raw `messages.create` loop + all cache-marker machinery
- `sidequest/agents/llm_factory.py` — deleted `build_async_anthropic`; 4 Haiku sites now use `query` + `build_agent_sdk_options`; `_record_usage_telemetry` reads dict usage; stale-docstring cleanup
- `sidequest/server/intent_router_pass.py` — seam-reference comment refresh
- Tests: 20 obsolete transport files deleted, 13 migrated onto the `query`/fake seam, 2 new (`test_cost_safety_unit.py`, `test_119_3_narrator_behavior_on_agent_sdk.py`), server `conftest.py` hermetic guard patches the `query` seam; RED added the 38-test `test_119_3_*` suite + `fakes/fake_agent_sdk.py`

**Tests:**
- 38 TEA tests (AC1/AC2/AC3, narrator + 4 Haiku sites + dependency/seam): GREEN
- `tests/agents`: **1958 passed, 2 skipped** (GREEN)
- Migrated server wiring tests (`test_93_1_archetype_inference`, `test_turn_context_sdk_wiring`, `test_world_grounding_wiring`): **35 passed**
- `ruff check` on all changed/new files: clean

**Pre-existing failures (NOT a regression):** The full suite carries ~88 PRE-EXISTING failures (70 in `tests/integration`, WN/WWN combat + chargen + wiring — `DiceDispatchError ... beat_id 'committed_blow' ... available: []`). **Baselined against `origin/develop`'s transport via path-limited stash: identical set, `mine ⊆ develop`, ZERO regressions introduced by this port.** They are epic-108 WN-owns-the-round / ADR-106/114/143 *partial* work; the remaining ~18 are heavy-e2e `--timeout=30`/xdist casualties (pass at `--timeout=300`). See `## Delivery Findings → ### Dev` (Gap).

**Branch:** feat/119-3-narrator-agentsdk-port (pushed)

**Handoff:** To Architect (Neo) for sdd spec-check (post-green spec-fidelity gate), then verify/review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None requiring action (2 spec-sanctioned deferrals affirmed; verified against the actual code, not just the Dev Assessment)

**AC-by-AC verification (read against `anthropic_sdk_client.py` + `llm_factory.py`, not the assessment prose):**
- **AC1 — context isolation: ALIGNED.** `build_agent_sdk_options` (`anthropic_sdk_client.py:184-216`) pins a plain-string `system_prompt`, `setting_sources=[]`, `add_dirs=[]`, and `cwd=_neutral_cwd()` (a process-stable empty tempdir holding no `CLAUDE.md`/`.claude`). The narrator path concatenates the cacheable system blocks into one plain string (`:370`), never the `claude_code` preset. Covered by `test_119_3_context_isolation.py` (options-pin + behavioral spike-regression + Haiku-router isolation), GREEN.
- **AC2 — subscription auth / no PAYG fallback: ALIGNED.** `assert_subscription_auth` (`:164-181`) raises `AgentSdkAuthUnavailable` if `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` is SET (the inverse of the old key-required check) and is invoked inside `build_agent_sdk_options` so every call asserts; an auth-absent query surfaces `is_error` → `AgentSdkAuthUnavailable` (`:504-527`), never a degraded-success result. Covered by `test_119_3_subscription_auth.py` (10 tests), GREEN.
- **AC3 — port fidelity: ALIGNED.** The SDK `query()` loop (`:392-393`) replaces the manual `messages.create`/`stop_reason==tool_use` loop; the `@tool`→`default_registry.dispatch` bridge (`_build_narration_tool_handler` `:236-264`, `_build_narration_mcp` `:564+`) preserves the `tool_calls` ledger via `all_tool_uses`; the per-turn server is rebuilt per call (ruleset-filtered — no static-server tool leak). OTEL preserved: `llm_request_span` wraps the loop, usage attrs + `narrator.sdk.usage` watcher event (`:474-486`), `narrator_tool_loop_span` (+ `cap_hit` + `loop_exceeded` variants), and a multi-text-block-discard WARNING span. Full `ToolingResult` shape returned (`:547-562`); `result_msg is None` → loud raise (`:430-435`). `error_max_turns` → `AnthropicSdkLoopExceeded` (convergence semantics preserved).
- **Expanded Haiku scope (4 sites, 2026-06-16 Operator ruling 8→13 pts): ALIGNED.** Aside / Intent-Router / unseeded-classifier / archetype all route through `build_agent_sdk_options` + the `query` seam; the three forced-extraction sites use `output_format` at `max_turns=2` reading `ResultMessage.structured_output`, raising the site's loud error on `None`/`is_error`. OQ-3 green gate CONFIRMED (real `DispatchPackage` `$defs`/`$ref` schema accepted verbatim — no shim).

**Observations (no action — recorded for traceability):**
- **`add_dirs=[]` beyond the literal AC1 text** (Extra in code — Cosmetic, Trivial). The story AC names "system_prompt + cwd + setting_sources"; the code also pins `add_dirs=[]`. Spec Implementation-Guidance §6.1 explicitly lists it. Recommendation **A** — already in spec; strictly safer (closes another context-absorption door).
- **`max_tokens`/`tool_choice` accepted-but-ignored** (`del max_tokens, tool_choice`, `:359`) (Different behavior — Cosmetic, Trivial). Kept for `ToolingLlmClient` signature parity (single-commit rollback); spec §3.6 documents that the CLI owns output length and the Agent SDK exposes no `tool_choice`. Recommendation **C** — spec already clarifies. Note for verify: narrator output length is now CLI-governed, not capped at our 4096.
- **OQ-6 per-TTL cache split = documented-zero** (`:557-561`) (Behavioral — Minor). Aggregate cache read/write preserved; the 5m/1h split is `0` with a loud comment. Already a logged Dev deviation. Recommendation **D** — defer to a caching-strategy follow-up. Affirmed.
- **OQ-17 cache-floor guard retained live but now vestigial + uncovered** (`llm_factory.py:646-667`) (Architectural — Minor). The agent-SDK path no longer emits `cache_control` markers, and the guard's test (`test_haiku_cache_control.py`) was deleted in the full-replace, so it guards a trap our code can no longer spring yet can still raise if the router prefix shrinks below 4096 tok (currently ~4730 — dormant). Already a logged Dev deviation. Recommendation **D** — defer; a follow-up should delete or re-home it onto an SDK cache signal and restore coverage. **This is the single item worth a follow-up ticket.** Affirmed.

**Reuse note (pragmatic-restraint lens):** the port is reuse-correct — the `ToolingLlmClient`/`ToolingResult` signature, the 26-tool registry, `cost_safety`, and every OTEL span helper are preserved; the change is confined to the transport seam and the per-call SDK-MCP boundary. No new infrastructure introduced.

**Decision:** Proceed to verify (TEA / The Architect). No Option-B fixes; no hand-back to Dev. The two affirmed deferrals (OQ-6, OQ-17) carry into spec-reconcile as known deviations.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (changed production source: `anthropic_sdk_client.py`, `llm_factory.py`, `intent_router_pass.py`). The 24 changed test files are mechanical full-replace migrations, already ruff-clean and Dev-reviewed — out of simplify scope.

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings (3 high, 1 medium) | 4-site Haiku SDK-call skeleton + structured-output extraction repeat; proposes `_call_haiku_sdk` / `_extract_structured_output_or_raise` |
| simplify-quality | clean | No dead code / silent-fallback / inconsistency in the new code |
| simplify-efficiency | 2 findings (1 medium, 1 low) | inline `_compose_structured_system`; reuse `_is_agent_result_message` in `_consume_to_result` |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** all 6 findings → recorded as non-blocking Improvements (Delivery Findings → TEA test verification)
**Noted:** the reuse consolidation is a legitimate follow-up; declined here to preserve the story's minimal-diff/single-commit-rollback design value (story-scope authority), which the Architect spec-check affirmed
**Reverted:** 0

**Overall:** simplify: clean (0 fixes applied — all findings deliberately deferred, see Design Deviations → TEA test verification)

### Quality-Pass

- **Working tree:** clean — byte-identical to the committed green state (`ba572b9b`); zero simplify edits, so no regression surface.
- **Tests (independent re-confirm):** `tests/agents` + the 3 migrated server wiring files = **1993 passed, 2 skipped** (`-n auto`, `--timeout=120`). The 38 AC-bearing 119-3 tests are within this set, GREEN.
- **Lint:** `ruff check` on the 3 changed source files + 2 new test files — clean.
- **Pre-existing failures:** the full-suite ~88 failures (70 `tests/integration` WN/WWN combat, epic-108) are PRE-EXISTING — baselined `mine ⊆ develop` in green, zero regressions from this port. `pf check`/full-suite is intentionally NOT used as the quality-pass signal here because those pre-existing failures would mask the story's true GREEN; the scoped story suites + lint are the honest gate.

**Quality Checks:** All passing (scoped to the story domain, with the pre-existing-failure caveat documented).

**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (0 blocking smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer's own edge analysis) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer's own silent-failure analysis) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (all LOW) | confirmed 1 (LOW non-blocking), dismissed 2 (speculative) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered by verify-phase simplify fan-out) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (no `lang-review/python.md` exists; Reviewer did manual Rule Compliance) |

**All received:** Yes (2 enabled subagents returned — preflight clean, security 3×LOW; 7 disabled via `workflow.reviewer_subagents`, pre-filled and non-blocking per the gate)
**Total findings:** 1 confirmed (LOW, non-blocking), 2 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. The port is a clean, reuse-correct transport swap; all three ACs are behaviorally tested and GREEN (1993 passed in the story domain), the No-Silent-Fallbacks auth invariant is unbypassable, and OTEL/wiring are preserved.

### Observations (≥5, tagged by source)

- **[PRE][VERIFIED]** Story-domain suite GREEN — `tests/agents` + 3 migrated server files = 1993 passed / 2 skipped; ruff clean on all 5 changed/new files. Evidence: reviewer-preflight run + my re-confirm. The ~88 full-suite failures are PRE-EXISTING (epic-108 WN combat), baselined `mine ⊆ develop` — not this story.
- **[SEC][VERIFIED]** Auth invariant unbypassable — `assert_subscription_auth()` (`anthropic_sdk_client.py:164-181`) raises on a SET `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN`, and is the FIRST statement of `build_agent_sdk_options()` (`:205`); every `query()` call site (narrator + all 4 Haiku) routes through it. Security agent enumerated 5 call sites, 0 bypass paths. Complies with No Silent Fallbacks.
- **[SILENT][VERIFIED]** Fail-loud on every non-success transport outcome — `result_msg is None` → raise (`:430-435`); `is_error` + `error_max_turns` → `AnthropicSdkLoopExceeded` (`:504-519`); other `is_error` → `AgentSdkAuthUnavailable` (`:520-527`); per-Haiku-site `structured_output is None` → the site's loud error (e.g. `IntentRouterEmptyResponse`, `llm_factory.py:497-504`). No swallowed errors, no degraded-success masking a missing credential.
- **[VERIFIED]** OTEL preserved — `llm_request_span` wraps the loop; `narrator_tool_loop_span` (+ `cap_hit` + `loop_exceeded` variants); `narrator.sdk.usage` watcher event (`:474-486`); multi-text-block discard emits a WARNING span (audited, not silent). Complies with the OTEL Observability Principle.
- **[VERIFIED]** Wiring real — `complete_with_tools` is reachable from the orchestrator (TEA's `test_complete_with_tools_reachable_from_orchestrator`); the `@tool`→`default_registry.dispatch` bridge (`_build_narration_tool_handler` `:236-264`) accumulates `all_tool_uses` so the fabricated-roll detector + GM-panel ledger see the full `tool_calls` list. Not a half-wired feature.
- **[SEC][LOW]** `_neutral_cwd()` (`:156-161`) creates a temp dir via `mkdtemp` with no `atexit`/cleanup — one empty dir per process lifetime (global-memoized, not per-call). Non-blocking hygiene nit; recorded as an Improvement. (The security agent's paired claim "no test verifies cwd isolation" is REFUTED — `test_narrator_output_not_contaminated_by_repo_persona` is a behavioral spike-regression proving the `setting_sources=[]`/`add_dirs=[]`/neutral-cwd pins defeat contamination.)
- **[SEC][dismissed]** `subtype` embedded in `AgentSdkAuthUnavailable` message (`:524`) — DISMISSED: `ResultMessage.subtype` is a closed SDK enum (`success`/`error_max_turns`/`error_during_execution`), not a server-error-body passthrough; no credential surface. Speculative against a hypothetical future SDK.
- **[SEC][dismissed]** `system_blocks`→plain-string collapse (`:370`) — DISMISSED: the Agent SDK's `system_prompt` is a plain string by API design; player free-text is sanitized upstream (ADR-047) and the security agent found no player text reaching `system_blocks` at this layer; no new injection surface vs the old path, which also rendered system content as text.

### Rule Compliance (manual — no `lang-review/python.md` present)

| Rule (CLAUDE.md / SOUL.md) | Instances enumerated | Verdict |
|---|---|---|
| **No Silent Fallbacks** | auth assert (1) + 5 query call sites + `result_msg None` raise + 2× `is_error` raises + 4× per-Haiku `structured_output None` raises + OQ-6 documented-zero (loud comment, not a measured 0) | **Compliant** — every failure path raises; no silent degrade/PAYG re-route |
| **No Stubbing / dead code** | `build_agent_sdk_options`, `_build_narration_mcp/_handler`, `_consume_to_result`, `_usage_int`, `assert_subscription_auth`, `_neutral_cwd` all have live callers; OQ-17 cache-floor guard retained = documented vestigial (logged deviation), not a stub | **Compliant** (OQ-17 flagged as a follow-up, not dead-on-arrival) |
| **OTEL Observability Principle** | narrator: `llm_request_span` + `narrator_tool_loop_span`(×3) + `narrator.sdk.usage` watcher; Haiku: per-site `llm.request`/`_record_usage_telemetry` caller-tagged | **Compliant** |
| **Verify Wiring / wiring test** | `test_complete_with_tools_reachable_from_orchestrator` + the `@tool`→dispatch bridge feeding `tool_calls` | **Compliant** |
| **ADR-047 prompt-injection sanitization** | `_compose_structured_system` receives only internal `_TOOL_DESCRIPTION` constants; `system_blocks` sanitized upstream | **Compliant** (pre-existing narrator_hints concern unchanged by this port) |

### Data flow traced

Player action → `intent_router_pass` builds `_IntentRouterLlm` → `emit_tool` (`llm_factory.py:444`) → `build_agent_sdk_options(output_format=schema)` (asserts subscription auth) → `_consume_to_result` drives the module-level `query` seam → terminal `ResultMessage` → `structured_output` dict (or loud raise on `None`/`is_error`) → `DispatchPackage`. Narrator turn: `complete_with_tools` → `query()` loop with the `@tool`→`dispatch` bridge → converged `ResultMessage.result` → `ToolingResult`. **Safe because:** no credential ever flows into a prompt; auth is asserted before any spend; every non-success outcome raises rather than returning a degraded result.

### Tenant isolation audit

**N/A** — the diff introduces no tenant-bearing types or trait methods. `session_id` is a cost-ledger key (per-session cumulative + ceiling), not a security boundary; it is keyword-only and `None` explicitly opts out of the ledger (never silently). No `pub`-field / mutable-shared-state concern in the changed code.

### Devil's Advocate

Assume this port is broken. The scariest claim is the **money** claim: this entire story exists to move spend off the metered PAYG ledger onto the free subscription pool. What if it silently *still* bills PAYG? The defense is `assert_subscription_auth` — but a malicious or careless operator who exports `ANTHROPIC_API_KEY` "to be safe" would, under the OLD code, get billed; under the NEW code they get a loud `AgentSdkAuthUnavailable` and a dead server. That's the correct fail-loud direction, but it means a previously-working deployment that set the key will now refuse to start its narrator — an operational sharp edge. It is the *intended* edge (No Silent Fallbacks > convenience), and it is tested (`test_narrator_raises_when_payg_cred_set`), so I accept it. Next: what does a **confused player** do? Nothing reaches this layer un-sanitized — player text is ADR-047-sanitized before `system_blocks`, and the `@tool` args go to the same registry validation as before. What about a **stressed runtime**? If the subscription login is absent, `query()` yields `is_error` and we raise — no hang, no silent empty narration. If the model loops, `error_max_turns` raises `AnthropicSdkLoopExceeded` (the `max_turns=2` floor prevents the `max_turns=1` always-fail trap). The genuine residual risks are *external to this code*: (1) the AC1 isolation depends on the `claude-agent-sdk` honoring `setting_sources=[]`/`add_dirs=[]` — a future SDK regression could silently re-absorb repo context; the behavioral contamination test is our tripwire, but it mocks `query`, so it would NOT catch a real-SDK behavior change (worth a periodic live smoke). (2) The cost ceiling ($10) is PAYG-dollar-calibrated but now meters *notional* subscription cost (Architect DF) — it could fire spuriously or never; that's a known follow-up, not a defect in this diff. (3) The OQ-17 cache-floor guard is live-but-uncovered. None rise to blocking. Verdict stands.

### Challenge of VERIFIEDs

Each `[VERIFIED]` above was cross-checked against the two returning subagents: preflight corroborates the GREEN/lint VERIFIED; security corroborates the auth-invariant VERIFIED (and its only non-dismissed finding is the LOW cwd-cleanup nit, which does not contradict any VERIFIED). No subagent contradicts a VERIFIED conclusion.

**Handoff:** To Architect (Neo) for spec-reconcile, then SM for finish.