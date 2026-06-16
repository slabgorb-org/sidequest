# Design Spec — 119-3: Port the Narrator Inference Path onto `claude-agent-sdk` (Subscription Auth)

**Date:** 2026-06-15
**Author:** Architect (Neo)
**Status:** Design — **GO/derisked**. The 119-1 spike was a NO-GO for raw-SDK-over-OAuth
(400 "credit balance too low"); `scripts/spike_119_3_agentsdk_subscription.py` proves the
`claude-agent-sdk`-over-subscription-login path draws the subscription pool cleanly
(`is_error=False`, `service_tier='standard'`, no 400). This spec is the productionization
of that spike.
**Workflow:** `sdd` — TEA writes red against this spec; the spec-check (post-green) and
spec-reconcile (post-review) gates govern fidelity. Deviations go to the session file's
`## Design Deviations` section.
**ADR:** ADR-101, Amendment (2026-06-15). **Epic:** 119. **Repo:** `sidequest-server`.
**Mutually exclusive with:** 119-2 (re-auth raw SDK to subscription OAuth — superseded by
the 119-1 NO-GO; that path PAYGs).

> **AMENDED 2026-06-16 — scope expanded to include Haiku callers per Operator ruling on
> DF-1/OQ-7; 8→13 pts.** 119-3 now ports BOTH the narrator (`complete_with_tools`) path AND
> the four single-shot Haiku call sites (Intent Router, aside, unseeded-objective
> classifier, archetype inference) off PAYG onto the subscription via `claude-agent-sdk`,
> in this one story. The Haiku port surfaces a **load-bearing new risk**: the Agent SDK
> exposes **no `tool_choice`**, so the forced-single-tool structured-extraction mechanism
> three of those four calls depend on is **not directly expressible**. See the rewritten
> §6.4 (now the Haiku port design) and Open Questions **OQ-15 / OQ-16 / OQ-17**, flagged to
> the Operator as a risk before red.
>
> **VERIFIED 2026-06-16 by `output_format` spike (`scripts/spike_119_3_haiku_outputformat.py`)
> — Path A GO at `max_turns=2`; OQ-15 / OQ-16 RESOLVED.** The forced-extraction gap is closed
> by the Agent SDK's first-class `output_format` JSON-schema structured output (API-enforced,
> not prompt-coerced). One caveat: the SDK spends an internal finalize turn, so the single-shot
> needs **`max_turns=2`** (a literal `max_turns=1` fails closed with `error_max_turns`). The
> prompt-coerced Path B is no longer required (kept as documented-unused fallback). Residual:
> the spike used a minimal hand-written schema — the **real `DispatchPackage.model_json_schema()`
> (`$defs`/nested) is NOT yet exercised** (OQ-3-adjacent); a green-phase round-trip gate covers
> it (§6.4.2, §9). **No remaining BLOCKING open questions — RED-READY.**

---

## 1. Goal

Move **all** Anthropic inference off the metered API-platform PAYG ledger (~$150/mo) onto
the free Max subscription pool by rewriting the inference transport from the raw `anthropic`
Messages SDK (`AsyncAnthropic().messages.create(...)`) onto the `claude-agent-sdk` package,
which authenticates through the bundled Claude Code CLI's subscription OAuth login. Target
spend: **~$150/mo → ~$0**.

**Two transport shapes flow through the one Story-91-1 choke point and both must move
(2026-06-16 amendment):**
1. **The narrator tool loop** — `complete_with_tools` (Sonnet, multi-turn, the 26-tool
   registry). The bulk of the work; §4–§8.
2. **The four single-shot Haiku call sites** — Intent Router, aside, unseeded-objective
   classifier, archetype inference (`llm_factory.py`). Single inference, no agent loop;
   three of the four use **forced `tool_choice` structured extraction** and one (aside) uses
   `tool_choice={"type":"none"}`. §6.4 designs their port; the forced-`tool_choice` gap is
   the load-bearing risk.

This is a transport + auth change scoped to the single Story-91-1 SDK construction point
(`build_async_anthropic`) and the two call shapes it feeds. Everything *above* the
`complete_with_tools` boundary — the orchestrator, the 26-tool registry, perception
filtering, the sidecar, the cost-rollup span, the `NarrationTurnResult` contract — and the
**structured-payload contract each Haiku producer returns to its consumer** are **untouched
in interface**. The port succeeds when no caller — narrator orchestrator or Haiku consumer —
can tell which transport it is calling.

### 1.1 Why a port and not an auth swap (the 119-1 result)

The 119-1 spike fed an OAuth bearer token to the raw `anthropic` SDK's `messages.create()`.
It 400'd with "credit balance too low": the raw Messages API routes a bearer token to the
**metered API-platform ledger**, which has a $0 balance, not the subscription pool. The
subscription pool is only reachable through the Claude Code CLI's own auth resolution,
which `claude-agent-sdk` wraps. Hence the port: we change the *client library*, not just
the credential.

---

## 2. Scope — the seam and what stays untouched

### 2.1 In scope (the two edit sites)

| Site | File:line (current) | Change |
|---|---|---|
| The SDK construction choke point | `sidequest/agents/llm_factory.py:77-97` (`build_async_anthropic`) | Replace/augment so **neither** the narrator path **nor** the Haiku call sites construct an `AsyncAnthropic`. See §6. |
| The manual tool loop | `sidequest/agents/anthropic_sdk_client.py:248-705` (`complete_with_tools`) | Rewrite the `messages.create` + `stop_reason=="tool_use"` re-call loop onto `claude-agent-sdk`'s `query()` + in-process SDK-MCP tool model. See §5, §7. |
| The four single-shot Haiku sites | `llm_factory.py:251-289` (`_AsideLlm.complete`), `:414-498` (`_IntentRouterLlm.emit_tool`), `:696-749` (`_UnseededObjectiveClassifierLlm.emit_tool`), `:788-961` (`infer_archetype_from_freeform`) | Rewrite each `messages.create(..., tool_choice=...)` single-shot onto `claude-agent-sdk`, preserving the structured-payload each returns. See §6.4. **The forced-`tool_choice` gap is the load-bearing risk (OQ-15).** |

### 2.2 Explicitly OUT of scope (untouched)

- **`tool_registry.py`** (`tool_registry.py:225-249`, `Registry.tool_definitions`,
  `Registry.dispatch`, `@tool` decorator, `ToolContext`). The narration tool catalog,
  its Pydantic args models, and the dispatch path stay exactly as they are. The port
  *consumes* `tool_definitions(ruleset)` and `dispatch(block, ctx)` — it does not rewrite
  them. (§5 maps the Pydantic schema → Agent-SDK-tool translation, performed at the
  client boundary, not in the registry.)
- **`orchestrator._run_narration_turn_sdk`** (`orchestrator.py:3763-4211`) and its
  `dispatch` closure (`orchestrator.py:4086-4087`), the `narration.turn` cost-rollup span,
  the `prompt_assembled` event, `_assemble_turn_result_sdk`, and the fabricated-roll
  repair. These call `complete_with_tools` and read its `ToolingResult`; both contracts
  are preserved (§4).
- **The dungeon `materializer.py` curate stage** (`materializer.py:1233`) and
  `aside_resolver.py:293` — other `complete_with_tools` callers. They share the
  `ToolingLlmClient` surface and inherit the port (§8.1).
- **Cost-safety machinery** (`cost_safety.py`, the per-session ledger, the runaway
  detector, the $10 ceiling). Re-wired onto the new usage figures (§7.4), behavior preserved.

### 2.3 Pragmatic-restraint note

The reuse-first stance holds: the `complete_with_tools` *signature*
(`tooling_protocol.ToolingLlmClient`), the `ToolingResult` dataclass, the 26-tool registry,
the OTEL span helpers, and `cost_safety` are all reused unchanged. The new code is confined
to the body of one method and the construction seam that feeds it. This is the smallest
change that satisfies "move the transport."

---

## 3. The `claude-agent-sdk` surface (authoritative facts + flagged unknowns)

Sourced from the `claude-api`/`claude-code-guide` references and the working spike. Where
a fact could not be verified against the SDK without running it, it is marked **[OQ-n]** and
carried to §11 Open Questions. **No Silent Fallbacks applies to specs too** — unverified
items are flagged, not guessed into the design.

### 3.1 Imports (proven by the spike, `scripts/spike_119_3_agentsdk_subscription.py:54-61`)

```python
from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query,
)
```
Additional symbols the port needs (custom tools, blocks) — `tool`,
`create_sdk_mcp_server`, `ToolUseBlock`, `ToolResultBlock`, `UserMessage`,
`SystemMessage` — are documented in the Agent SDK Python reference. **[OQ-1]** the exact
import paths/names for the tool-definition helpers and block classes must be confirmed
against the installed package version before red is finalized (the spike only exercised
the query/result path, not tools).

### 3.2 `query()` and the loop model

`query(prompt=..., options=ClaudeAgentOptions(...))` returns an **async iterator of
messages**. The SDK runs the agent loop **itself**: when the model calls a tool defined in
an in-process SDK-MCP server, the SDK invokes the registered handler, feeds the result
back, and continues until convergence — emitting `AssistantMessage`/`UserMessage` along the
way and a terminal `ResultMessage`. This is the key structural shift: **we no longer drive
the `stop_reason==tool_use` re-call loop by hand; the SDK owns it.** Our handler is called
*by* the SDK.

Message/block taxonomy the port consumes:
- `AssistantMessage.content` → list of `TextBlock` (final + intermediate prose) and
  `ToolUseBlock` (tool invocations the model made). The narrator's converged prose is the
  text of the assistant turn(s); see §7.3 for the multi-text-block rule.
- `ResultMessage` → terminal. Carries `is_error: bool`, `subtype: str`
  (`"success"` | `"error_*"`), `result: str` (final text), `num_turns: int`,
  `total_cost_usd: float | None`, `usage: dict | None`. **[OQ-2]** the exact field set and
  the `subtype` error-code strings (e.g. is it `"error_max_turns"`?) are **UNVERIFIED** —
  confirm against the SDK types; the convergence/error mapping in §7.4 depends on it.

### 3.3 Custom tools (in-process, SDK-MCP)

Tools are defined with the `@tool(name, description, input_schema)` decorator, collected
into an in-process server via `create_sdk_mcp_server(name=..., version=..., tools=[...])`,
passed to `ClaudeAgentOptions(mcp_servers={"<server>": server}, allowed_tools=[...])`, and
surfaced to the model under the **namespaced id `mcp__<server>__<tool>`**. The handler is
`async def handler(args: dict) -> dict` returning
`{"content": [{"type": "text", "text": ...}], "is_error": bool}`.

- **Raw-JSON-Schema input:** the references indicate `input_schema` accepts a full JSON
  Schema dict (not only the `{name: type}` shorthand). Our registry already produces
  `args_model.model_json_schema()` (a JSON Schema dict). **[OQ-3]** that raw Pydantic
  JSON-Schema dict is accepted **as-is** by `@tool` (including `$defs`, `enum`, nested
  objects, `additionalProperties`) is **UNVERIFIED** — the single highest-risk unknown for
  port fidelity. If it is NOT accepted verbatim, a thin schema-adaptation shim is required
  (still no registry change). TEA must cover this with a per-tool schema round-trip test.

### 3.4 Context-isolation options on `ClaudeAgentOptions`

- `system_prompt` — accepts a **plain replacement string** (what we want), or a preset
  form `{"type": "preset", "preset": "claude_code", "append": "..."}`. We pass our own
  string; we do **not** use the `claude_code` preset (it injects Claude-Code agent
  scaffolding).
- `cwd` — working directory the SDK treats as the project root.
- `setting_sources` — controls which on-disk config tiers load
  (`"user"` = `~/.claude/`, `"project"` = `./.claude/` + repo `CLAUDE.md`, `"local"`).
  **Default loads all three.** Passing `[]` (empty list) loads **none**. **[OQ-4]** the
  exact accepted values and that `[]` (vs `None`) is the "load nothing" form are
  **UNVERIFIED against the installed version** — but this is the load-bearing landmine
  (the spike answered in an SM persona because it absorbed the repo `CLAUDE.md`), so TEA's
  context-isolation test (§9, AC1) is the gate, and the implementation must set this
  explicitly, not rely on a default.
- `add_dirs` — extra accessible dirs; set to `[]`.
- `model` — pins the model id (e.g. `"claude-sonnet-4-6"`).
- `max_turns` — agent-loop iteration cap (the convergence ceiling; §7.2).

### 3.5 Subscription auth resolution

With `ANTHROPIC_API_KEY` **and** `ANTHROPIC_AUTH_TOKEN` both unset in the process env, the
SDK falls through to the bundled CLI's subscription OAuth login profile (the credential
written by `claude` interactive `/login`, stored under the Claude Code config dir). The
spike proves this draws the subscription pool. **Doctrine note:** the `claude-code-guide`
reference *claimed* subscription OAuth is "not supported" by the Agent SDK — that claim is
**contradicted by the spike's empirical GO result** and is treated as stale/incorrect for
this environment. Per project doctrine (No Silent Fallbacks, "every playtest is production"),
**the working spike is the source of truth**, not the doc claim. **[OQ-5]** there is no
documented up-front "is a subscription credential present?" probe; absence surfaces as a
failed query/`ResultMessage(is_error=True)`. The fail-loud contract (§7.5, AC2) is built on
detecting that failure, not on a pre-check — unless OQ-5 resolves to a real probe API.

### 3.6 No `tool_choice`; the single-shot structured-extraction story (the 2026-06-16 risk)

The Haiku port hinges on whether the Agent SDK can reproduce the raw SDK's forced-single-tool
extraction. The `claude-code-guide` reference (citing
[`claude-agent-sdk-python` issue #655](https://github.com/anthropics/claude-agent-sdk-python/issues/655))
is blunt:

- **No `tool_choice`.** `ClaudeAgentOptions` exposes **no** `tool_choice` field and no
  "force/require a tool call" option. The Messages API supports
  `tool_choice={"type":"tool","name":...}` and `{"type":"none"}`; the Agent SDK does **not**
  surface either. This is a documented, open gap.
- **Handlers always execute.** When the model calls a registered SDK-MCP tool, the SDK
  **always invokes the handler and loops** — there is no "observe the tool's `input` without
  executing" mode. So the raw SDK's "force a tool, read its `.input`, never run a handler"
  extraction pattern (the Intent Router / classifier / archetype mechanism) has **no direct
  analog**. (A `PreToolUse` hook can *deny* execution, but it cannot *force* the model to
  call the tool in the first place, and reading the input from a hook is unverified — §6.4.)
- **`output_format` structured output (the replacement — VERIFIED GO).** `ClaudeAgentOptions`
  exposes a first-class `output_format={"type":"json_schema","schema": <JSON Schema>}` option
  that constrains the **final result** to schema-valid JSON, surfaced as
  `ResultMessage.structured_output`. **OQ-15 RESOLVED GO (VERIFIED 2026-06-16 by
  `scripts/spike_119_3_haiku_outputformat.py`):** on `claude-haiku-4-5` over subscription
  auth (`service_tier='standard'`, no 400) — `output_format`/`structured_output` exist on the
  released SDK (dataclass introspection); the `{"type":"json_schema","schema": <dict>}` shape
  is accepted verbatim (a 3-field typed schema with `enum`/`number`/`required`/
  `additionalProperties:false` round-tripped to a clean dict, e.g.
  `{'intent':'attack','target':'bandit captain','confidence':0.95}`). This **preserves
  API-enforced "schema-valid structured output in one shot"** without the tool dance — it is
  the design's primary path (Path A, §6.4.2).
- **Single-shot requires `max_turns=2`, NOT `max_turns=1` (VERIFIED — OQ-16 RESOLVED).** The
  SDK consumes an internal finalize/validate turn even with **zero tools**, so it always
  spends `num_turns=2`. Empirically: `max_turns=1` → `is_error=True`,
  `subtype='error_max_turns'`, `structured_output=None`, and `query()` RAISES "Reached
  maximum number of turns (1)"; `max_turns=2` (and 3, 4) → `is_error=False`,
  `subtype='success'`, a clean schema-valid dict. **The +1 headroom is MANDATORY, not
  optional** — a literal `max_turns=1` from any stale spec text fails closed. Every
  structured-extraction single-shot in this spec specifies **`max_turns=2`**.
- **Suppressing tools (aside).** No `tool_choice={"type":"none"}` analog; the equivalent is
  simply passing **no tools** (`allowed_tools=[]`, no `mcp_servers`) for a plain completion.

These facts drive §6.4. The forced-extraction gap is **resolved**, not papered over: Path A
(`output_format`) is the verified, API-enforced replacement; the prompt-coerced Path B is
retained as a documented-but-unused fallback (the analysis, not a requirement).

---

## 4. The preserved boundary contract (what the orchestrator sees)

The port is a body rewrite of `complete_with_tools`. Its **signature and return type are
frozen** by `ToolingLlmClient` (`tooling_protocol.py:96-129`) and the `ToolingResult`
dataclass (`tooling_protocol.py:59-81`). The orchestrator at `orchestrator.py:4089-4166`
reads, after the call:

- `result.text` — converged narration prose
- `result.tool_calls: list[ToolUseBlock]` — every tool the model invoked (count + ledger;
  drives `tool_call_count`, `tool_calls_json`, and the fabricated-roll detector at
  `orchestrator.py:3194`)
- `result.input_tokens / output_tokens / cached_input_read_tokens /
  cached_input_write_tokens / cached_input_write_5m_tokens / cached_input_write_1h_tokens`
  — the cost-rollup span attributes (`orchestrator.py:4114-4146`) and `prompt_assembled`
  cache_usage (`orchestrator.py:4192-4200`)
- `result.cumulative_cost_usd` — `$/turn`, `cost_band`
- `result.model`, `result.stop_reason`

**Fidelity rule:** every field above must be populated to the same *semantics* as today.
Where the Agent SDK cannot supply a figure (see §7.4 / OQ-6 on per-TTL cache split), the
port must populate it **loudly-degraded** (documented zero with a logged/OTEL note), never
silently faked.

The `dispatch` closure (`orchestrator.py:4086-4087`) — `async def dispatch(block:
ToolUseBlock) -> ToolResultBlock: return await default_registry.dispatch(block, tool_ctx)`
— is passed as `tool_dispatch`. The port must keep invoking it for **every** tool call,
because `Registry.dispatch` is where the WRITE-tool state mutations, perception filtering,
and per-tool OTEL spans live. (§5.3 covers how the SDK-owned loop calls back into it.)

---

## 5. Translation table — Pydantic tool schema → Agent SDK tool

### 5.1 The narration tool catalog (what must be preserved)

The catalog is data-driven and ruleset-filtered, not a fixed list. The orchestrator
computes `advertised_tool_defs = default_registry.tool_definitions(bound_ruleset)`
(`orchestrator.py:3889`) — a list of `ToolDefinition(name, description, input_schema)`
where `input_schema = args_model.model_json_schema()` (`tool_registry.py:242-246`). The v1
catalog is ~26-27 tools (READ/WRITE/GENERATE categories), with WWN/CWN/AWN-family tools
filtered in or out by the bound ruleset (ADR-117). **The port must reproduce the exact set
`tool_definitions(bound_ruleset)` returns for a given turn — same names, same descriptions,
same JSON Schemas — as Agent-SDK tools.** The port enumerates that list at call time; it
does not hardcode tool names (a hardcoded list would silently drop ruleset-filtered tools —
No Silent Fallbacks).

### 5.2 Per-tool mapping

For each `ToolDefinition` in `tools` (the already-filtered list passed into
`complete_with_tools`):

| Old (raw Anthropic) | New (`claude-agent-sdk`) |
|---|---|
| `{"name": t.name, "description": t.description, "input_schema": t.input_schema}` in the `tools=[...]` array of `messages.create` (`anthropic_sdk_client.py:1107-1132`) | A `@tool(t.name, t.description, t.input_schema)`-decorated async handler, collected into `create_sdk_mcp_server(name="<narration-server>", tools=[...])` and exposed via `ClaudeAgentOptions(mcp_servers={...}, allowed_tools=["mcp__<server>__<t.name>", ...])` |
| Model calls tool by bare `t.name` | Model calls tool by namespaced `mcp__<server>__<t.name>`; the port maps the namespaced id **back to the bare `t.name`** before constructing the `ToolUseBlock` it hands to `tool_dispatch` (the registry only knows bare names — `Registry.dispatch` looks up `block.name` against `self._tools`, `tool_registry.py:263`). **[OQ-1]** confirm the namespacing scheme and that the un-prefixed name is recoverable. |
| `input_schema = args_model.model_json_schema()` consumed verbatim by the API | Same dict passed as `@tool`'s `input_schema` — **pending OQ-3** (raw JSON Schema accepted as-is). If rejected, a schema-adapt shim translates at this boundary only. |
| Tool args arrive as `block.input` (a dict) on the model's `tool_use` block | Handler receives `args: dict`; the port wraps `(name, args, tool_use_id)` into a `tooling_protocol.ToolUseBlock(id=..., name=<bare>, arguments=args)` |

### 5.3 The handler that bridges SDK-MCP → registry dispatch

Because the SDK owns the loop and calls our handler, the per-tool `@tool` handler is a thin
bridge that re-enters the existing dispatch path:

1. Receive `(args, tool_use_id)` from the SDK for tool `<bare name>`.
2. Build `ToolUseBlock(id=tool_use_id, name=<bare>, arguments=args)`.
3. `await tool_dispatch(block)` → `ToolResultBlock(tool_use_id, content, is_error)` — this
   is the orchestrator's `dispatch` closure → `default_registry.dispatch` → WRITE-lock +
   perception filter + per-tool OTEL span (`tool_registry.py:251-337`), **unchanged**.
4. Append the `ToolUseBlock` to the accumulating `all_tool_uses` list (so
   `ToolingResult.tool_calls` is complete — the fabricated-roll detector and the GM-panel
   ledger depend on it).
5. Return `{"content": [{"type": "text", "text": result.content}], "is_error":
   result.is_error}` to the SDK so it feeds the result back to the model.

**Closure-capture note:** the `tool_dispatch` callable and the `all_tool_uses` accumulator
must be in scope of each `@tool` handler for this turn. Since `tool_definitions` is
per-turn and ruleset-dependent, the SDK-MCP server is **built per `complete_with_tools`
call** from the `tools` argument, with handlers closing over that turn's `tool_dispatch`.
(The tool *set* changes per ruleset, so a process-wide static server would be wrong — No
Silent Fallbacks against advertising the wrong tools.) **[OQ-8]** the per-call cost of
building an SDK-MCP server (subprocess/transport spin-up) is unknown; if it is significant,
a caching strategy keyed on the tool-set signature is a follow-up, not a 119-3 requirement.

---

## 6. Auth & construction — the choke-point change

### 6.1 The contract

- **`ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` both unset** in the server env — for
  **both** the narrator and the Haiku paths (they share the one choke point). The SDK
  resolves the subscription login.
- **Fail loud if subscription auth is absent.** Never silently fall back to PAYG. There is
  no PAYG path on this transport to fall back to — the failure mode is a failed query,
  which the port must surface as an `AnthropicSdkClientError` subclass, not swallow. This
  applies uniformly to the narrator and every Haiku site (one choke point, one contract).
- **No silent context absorption** — `system_prompt` + `cwd` + `setting_sources=[]` pinned
  (§6.3) on every `ClaudeAgentOptions`, narrator and Haiku alike (a Haiku classifier that
  absorbed the repo `CLAUDE.md` would misclassify on persona-tainted context).

### 6.2 Where construction moves

Today `AnthropicSdkClient.__init__` (`anthropic_sdk_client.py:142-196`) calls
`llm_factory.build_async_anthropic()` (`llm_factory.py:77-97`) which reads
`ANTHROPIC_API_KEY` (fail-loud if unset) and returns `AsyncAnthropic(api_key=...)`.

The port replaces the **narrator-path** construction so it no longer builds an
`AsyncAnthropic`. The recommended shape (Dev/TEA refine):

- A new construction seam (e.g. `build_agent_sdk_options()` or an
  `AgentSdkNarratorClient`) builds the frozen `ClaudeAgentOptions` (model-less base;
  per-turn `system_prompt`/tools layered in `complete_with_tools`). It asserts the
  no-PAYG-creds invariant **loudly**: if `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is
  *set* on the narrator path, raise (a set key would silently re-route to PAYG — the exact
  failure 119-1 hit). This is the inverse of today's "key must be set" check.
- `AnthropicSdkClient`'s `__init__` API-key presence check (`anthropic_sdk_client.py:142-147`)
  is replaced for the narrator path with the new invariant. The `sdk=`-injection escape
  hatch for the fake-SDK test fleet (`anthropic_sdk_client.py:186-196`) is **preserved** —
  tests inject a fake SDK/transport and never touch real auth. **[OQ-9]** the exact
  fake-injection seam for `claude-agent-sdk` (there is no `messages.create` to monkeypatch;
  the seam is now `query`/the transport) must be designed so TEA can drive convergence
  without a live subscription. Candidate: a `query`-callable injection or a fake transport;
  the spike pattern (`query` imported at module scope) suggests a module-dict late-bound
  `query` reference, mirroring the existing `build_async_anthropic` monkeypatch doctrine.

### 6.3 Context-isolation pinning (AC1)

In the `ClaudeAgentOptions` the narrator path constructs:
- `system_prompt=<the narrator's assembled system text>` — a **plain string**, our content
  only. On `complete_with_tools` the `system_blocks` (the three-zone cacheable layout,
  `orchestrator.py:3844-3848`) are concatenated into this string. **No `claude_code`
  preset, no `append`-to-preset.**
- `cwd=` — a **neutral directory that contains no `CLAUDE.md` / `.claude/`** (e.g. a
  dedicated empty/temp working dir, or an explicit non-repo path). Not the server repo
  root, not the orchestrator clone. **[OQ-4]** whether `cwd` alone can leak context even
  with `setting_sources=[]` is unverified — set both defensively.
- `setting_sources=[]` — load **no** user/project/local config tiers (no `CLAUDE.md`, no
  settings, no output styles).
- `add_dirs=[]` — no extra accessible directories.

The AC1 test (§9) asserts these pins prevent contamination behaviorally.

### 6.4 The Haiku single-shot port (RULED IN, 2026-06-16)

**Operator ruling on DF-1/OQ-7: the four Haiku call sites move in this story.** They share
the `build_async_anthropic` choke point and, left on PAYG, would defeat the "$150→$0" goal —
the narrator is roughly half the bill; the every-turn Intent Router is the [COST-1] dark
spender, and aside/classifier/archetype add to it. All four must reach the subscription pool.

#### 6.4.1 The four contracts to preserve (what each returns to its consumer)

| Site | File:line | Call shape today | Structured payload it returns |
|---|---|---|---|
| `_AsideLlm.complete` | `llm_factory.py:251-289` | `messages.create(system, messages, max_tokens=512)` — **no tools**, plain completion | `str` (the joined assistant text) |
| `_IntentRouterLlm.emit_tool` | `llm_factory.py:414-498` | `messages.create(..., tools=[one], tool_choice={"type":"tool","name":tool_name}, ttl:"1h" cache)` | `dict` — the forced tool's `.input` (DispatchPackage), via `for block … if tool_use and name==tool_name: return dict(block.input)`; raises `IntentRouterEmptyResponse` if no tool_use block |
| `_UnseededObjectiveClassifierLlm.emit_tool` | `llm_factory.py:696-749` | `messages.create(..., tools=[one], tool_choice={"type":"tool"}, max_tokens=256)` | `dict` — forced tool's `.input`; raises `LlmClientError` if no tool_use block |
| `infer_archetype_from_freeform` | `llm_factory.py:788-961` | `messages.create(..., tools=[one], tool_choice={"type":"tool"}, max_tokens=256)` | `dict[str,str] | None` — forced tool's `.input`, enum-validated; `None`/`{}` on the documented edge cases |

The **`emit_tool` Protocol** (`IntentRouterLLM` / `ObjectiveClassifierLLM`) and the
`infer_archetype_from_freeform` return contract are the frozen interfaces. The port changes
the *transport beneath them*, not their signatures or return shapes. Note: the Ollama twin
`_OllamaIntentRouterLlm` (`llm_factory.py:541-600`) **already** satisfies `emit_tool` via
**prompt-coerced JSON** (qwen has no forced-tool path) — proof that a non-forced-tool producer
can honor this contract. The Agent-SDK port does **not** need that pattern (Path A's
`output_format` is API-enforced); it remains the documented-unused Path B fallback (§6.4.2).

#### 6.4.2 Forced extraction via `output_format` (Path A — VERIFIED GO at `max_turns=2`)

Three of the four (Router, classifier, archetype) depend on
`tool_choice={"type":"tool","name":...}`: force exactly one named tool, read its
schema-validated `.input` as the structured result, **never execute a handler, never loop.**
Per §3.6, the Agent SDK exposes **no `tool_choice`** and **always executes a called tool's
handler**, so the raw mechanism cannot be transliterated. The verified replacement is the
Agent SDK's first-class **`output_format` JSON-schema structured output**, which enforces
schema-validity at the *response* level instead of the *tool* level — the consumer cannot
tell the difference (same `dict`, same enum constraints, same raise-on-absent).

- **Path A — `output_format` JSON-schema structured output (VERIFIED GO, OQ-15 resolved).**
  Canonical surface (the spike's working shape, `scripts/spike_119_3_haiku_outputformat.py`):

  ```python
  opts = ClaudeAgentOptions(
      model="claude-haiku-4-5",
      max_turns=2,                      # MANDATORY +1: the SDK spends an internal
                                        # finalize turn; max_turns=1 fails closed
                                        # with subtype='error_max_turns' (OQ-16).
      allowed_tools=[],                 # no tools — pure structured completion
      system_prompt=<the call's system text>,   # plain string (no preset)
      setting_sources=[], cwd=<neutral>, add_dirs=[],   # AC1 isolation (§6.3)
      output_format={"type": "json_schema", "schema": <tool_schema>},
  )
  async for msg in query(prompt=<user text>, options=opts):
      if isinstance(msg, ResultMessage):
          return msg.structured_output   # the schema-valid dict — where .input went
  ```

  Hand `structured_output` to the consumer exactly where the forced tool's `.input` dict went
  today; raise the site's existing error (`IntentRouterEmptyResponse` / `LlmClientError`) if
  `structured_output` is absent or `is_error` (preserves the loud-raise contract). **This is
  the design's primary and sufficient path.** VERIFIED 2026-06-16: `output_format`/
  `structured_output` exist on the released SDK; the `{"type":"json_schema","schema": <dict>}`
  shape is accepted verbatim for a typed schema with `enum`/`number`/`required`/
  `additionalProperties:false`; `max_turns=2` returns `is_error=False`/`subtype='success'`
  with a clean dict.

- **Path B — prompt-coerced JSON (DOCUMENTED-UNUSED fallback; NOT required).** Path A is
  verified, so Path B is **not** in the implementation. Retained only as the recorded analysis:
  if a future SDK regression removed `output_format`, the `_OllamaIntentRouterLlm` pattern
  (`llm_factory.py:541-600`) — tool schema embedded in the system prompt, no-tools
  `max_turns=2` `query()`, parsed via the existing `_extract_json_object`
  (`llm_factory.py:501-520`, raises loudly on unparseable/non-object), with the SEC discipline
  of keeping player text in the `role:user` turn (`llm_factory.py:587-593`) — would honor the
  same `dict`/raise contract at a weaker (instruction-coerced) guarantee. Do not implement it
  in 119-3.
- **Path C — `PreToolUse`-deny hook extraction — REJECTED.** Does not force the call (no
  `tool_choice`); strictly more fragile than B for no gain. Recorded only for completeness.

**Decision:** **Path A, `max_turns=2`.** The consumer's `dict`/`str`/`None` contract and the
fail-loud-on-malformed behavior are preserved. The aside (`_AsideLlm`) is the easy one — it
already uses **no tools**; it ports to a plain `max_turns=2` no-tools `query()` returning the
result text (its `tool_choice={"type":"none"}` cousin in `complete_with_tools` is the aside
*resolver*, §8.1/DF-3 — distinct from this `_AsideLlm.complete`).

**Green-phase verification gate (residual OQ-3-adjacent risk — NOT a red blocker).** The spike
exercised a **minimal hand-written** schema, not the **real `DispatchPackage.model_json_schema()`**
(which carries `$defs` / nested objects / `additionalProperties`); the ephemeral `uv run
--with claude-agent-sdk` env lacked the `sidequest` package, so the production schema was never
round-tripped. **Before committing the implementation, Dev MUST round-trip the REAL Pydantic
tool schema(s) through `output_format` and confirm a schema-valid `structured_output`.** If the
raw schema is rejected, apply the OQ-3 schema-adapt shim at the call boundary (same shim OQ-3
contemplates for the narrator tools). OQ-3 stays open as the umbrella for raw-Pydantic-schema
acceptance across both the narrator tools and these Haiku `output_format` schemas.

#### 6.4.3 Caching note (Intent Router's 1h prefix)

The Intent Router today rides a 1h ephemeral cache on its tools+system prefix
(`llm_factory.py:445-469`) — the [COST-1]-motivated saving (story 91-3 floor guard, the
`extended-cache-ttl` beta). Under the Agent SDK the CLI manages its own caching and the
`cache_control`/beta-header machinery does **not** apply. **[OQ-17]** whether the Agent SDK
caches a stable Haiku system prefix at all, and whether the 91-3 cache-floor guard
(`build_intent_router_llm`, `llm_factory.py:603-667`) becomes inert/removable, is
**UNVERIFIED** — but on the subscription pool the *dollar* cost is ~$0 regardless, so the
cache's purpose (cost control) is largely moot; the floor guard's fail-loud value drops to
"prevent a phantom-cache claim," which the Agent SDK transport doesn't make. Flag, don't
delete blindly: a removed guard + a re-introduced raw-SDK Haiku path later would silently
lose protection (No Silent Fallbacks). Treat as a follow-up cleanup, not a port requirement.

#### 6.4.4 Shared construction seam

All four (and the narrator) go through the same new auth-resolving construction (§6.2). The
Haiku sites stop calling `build_async_anthropic()` and instead build their single-shot
`ClaudeAgentOptions` from the shared seam. The `session_id`-keyed cost-safety wiring
(`check_ceiling`/`record_call` at each site, `llm_factory.py:267-288`, `:441-484`, `:707-741`,
`:858-927`) is **preserved** — it runs against the new usage figures (§7.4 / DF-2 notional-$
caveat applies identically to Haiku).

### 6.5 Rollback

The change is confined to the construction seam + the `complete_with_tools` body. Rollback
is: restore `build_async_anthropic` to return `AsyncAnthropic(api_key=...)`, restore the
`complete_with_tools` raw-loop body, and re-set `ANTHROPIC_API_KEY` in the env. Because the
`ToolingLlmClient` signature and `ToolingResult` shape are frozen, no caller changes are
needed to revert — a single-commit revert restores PAYG narration. Keep the raw-loop body
recoverable (the git history is the artifact; do not leave a dead parallel implementation
in-tree — No Stubbing).

---

## 7. The loop rewrite — old → new mapping

### 7.1 What the old loop does (`anthropic_sdk_client.py:303-705`)

A `for iteration in range(1, max_iterations+1)` loop that:
1. Builds the messages payload with cache markers (`_build_messages_payload`).
2. Calls `self._sdk.messages.create(...)` inside an `llm_request_span`.
3. Records usage → cost → cumulative; emits `narrator.sdk.usage` watcher event; runs the
   both-writes lie-detector, the cost-runaway detector, the per-session cumulative update.
4. Splits `response.content` into text + tool_use blocks (`_split_content`).
5. If `stop_reason != "tool_use"` → emit `narrator.tool_loop` span + per-turn cost pulse +
   cache-write split, return `ToolingResult`.
6. Else: dispatch each tool via `tool_dispatch`, append assistant `tool_use` + user
   `tool_result` blocks to `running_messages`, loop.
7. If the loop exhausts `max_iterations` → emit `narrator.tool_loop(loop_exceeded=True)`,
   raise `AnthropicSdkLoopExceeded`.

### 7.2 What the new loop does

The SDK owns steps 4-6. The port becomes: **start a `query()`, consume the message stream,
let the SDK call our `@tool` handlers (which run `tool_dispatch` and append to
`all_tool_uses`), and on `ResultMessage` build the `ToolingResult`.**

| Old semantic | New semantic |
|---|---|
| `for iteration in range(1, max_iterations+1)` manual re-call | `async for message in query(...)`; SDK drives iterations |
| `max_iterations` (default 8) hard ceiling → `AnthropicSdkLoopExceeded` | `ClaudeAgentOptions(max_turns=max_iterations)`; a `max_turns` hit surfaces on `ResultMessage` (`subtype`/`is_error`) and the port **raises `AnthropicSdkLoopExceeded`** to preserve the fail-loud convergence contract. **[OQ-2]** exact `subtype` string to match. |
| `iteration_cap` soft warning (`narrator_tool_loop_cap_hit_span`) | Emit the cap-hit span when the SDK reports `num_turns >= iteration_cap` (post-hoc, from `ResultMessage.num_turns`) OR while streaming if per-turn boundaries are observable. **[OQ-10]** whether intermediate turn boundaries are observable mid-stream for a *live* cap warning, or only post-hoc from `num_turns`. Post-hoc preserves the signal; live is a nice-to-have. |
| `stop_reason != "tool_use"` → converged | `ResultMessage` with `is_error=False` / `subtype="success"` → converged |
| `response.content` split → last text block is the prose | The converged prose is the last `TextBlock` of the assistant turn(s) / `ResultMessage.result`. The §7.3 multi-text rule is preserved. |
| `tool_dispatch(tu)` called by us per tool | Called by the SDK *via our `@tool` handler bridge* (§5.3); same `ToolResultBlock` flows back |
| `all_tool_uses` accumulated by us | Accumulated in the `@tool` handler bridge (§5.3 step 4) |
| `running_messages` append of assistant/user tool blocks | **Owned by the SDK** — we no longer hand-assemble the tool round-trip messages |

### 7.3 Multi-text-block discard rule (preserved — `anthropic_sdk_client.py:564-594`)

The "keep only the LAST text block, discard earlier drafts, emit
`narrator.multi_text_block_discarded`" rule (the five_points doubled-narration fix) must be
preserved. **[OQ-11]** whether the Agent SDK exposes multiple `TextBlock`s in one assistant
message (so the discard is still needed) or already returns a single converged
`result` — confirm; if it returns one converged string, the discard span becomes
unreachable-but-harmless (do not delete the helper; it documents intent), and TEA's test
asserts the single-string path. Either way the *output* must be the single converged
telling, never two concatenated.

### 7.4 OTEL & cost-accounting preservation (the load-bearing fidelity surface)

Every span and watcher event the old loop emits must still fire. Map per source:

| Signal (old site) | New source |
|---|---|
| `llm.request` span per iteration (`llm_request_span`, `:350`) | One span per SDK turn. If mid-stream turn boundaries aren't observable **[OQ-10]**, emit one `llm.request` span for the whole `query()` with `num_turns` recorded, OR per-turn from streamed `AssistantMessage`s. Must not lose the span entirely. |
| `narrator.sdk.usage` watcher event + `narrator.sdk.usage` INFO log (`:429-466`) | From `ResultMessage.usage` (+ per-turn if available). `caller`/`model` tags preserved. |
| `narrator.cache.both_writes_fired` lie-detector (`:493-531`) | **[OQ-6]** the Agent SDK may not expose the per-TTL cache-creation breakdown (`ephemeral_5m_input_tokens`/`ephemeral_1h_input_tokens`) the raw SDK exposes via `usage.cache_creation`. If absent, this lie-detector and the `narrator.cache.write_split` event degrade to documented-zero (logged once, OTEL-noted) — **No Silent Fallbacks: emit a "breakdown unavailable on agent-sdk" marker, do not silently report 0 as if measured.** |
| `_maybe_emit_cost_runaway` (cost-runaway detector, `:542-549`) | Fed from `ResultMessage.usage` + `total_cost_usd`. **Caveat:** `total_cost_usd` on the subscription path is the CLI's *notional* estimate (spike note, `:121-123`), not a PAYG charge. The detector still works as a *shape* signal (input-token fingerprint) but the cost-trigger thresholds may need recalibration — **DF-2 / OQ-12.** |
| per-session cumulative + `$10` ceiling (`_update_session_cumulative`, `:557-562`) | Same — fed from the notional `total_cost_usd`. Behavior preserved; semantics shift from "real $" to "notional $" (DF-2). |
| `narrator.tool_loop` summary span (`:607-612`, `:695-701`) | Emit on `ResultMessage` with `iterations_used = ResultMessage.num_turns`, `caller`, and `loop_exceeded` on the raise path. |
| `narrator.tool_loop.cap_hit` (`:308-315`) | §7.2 / OQ-10. |
| `session.cost_running_total` per-turn pulse (`_emit_cost_running_total`, `:618-622`) | Preserved, on converged return. |
| per-tool dispatch spans (`tool_dispatch_span` in `Registry.dispatch`) | **Untouched** — fire inside `default_registry.dispatch`, which the §5.3 bridge still calls. |
| **Haiku `llm.request` spans** (`llm_request_span` at `llm_factory.py:271`, `:445`, `:711`, `:894`) + `_record_usage_telemetry` (`llm_factory.py:112-180`: `llm.sdk.usage` log + `llm.caller`/cost span attrs, caller ∈ `aside`/`intent_router`/`unseeded_objective_classifier`/`archetype_inference`) | **Preserved per Haiku site.** Each ported single-shot still opens an `llm.request` span and runs `_record_usage_telemetry` against the Agent SDK's `ResultMessage.usage`/`total_cost_usd`. The `caller` tag (the [COST-1] attribution axis) must survive — it is what splits Router from aside from classifier in cost forensics. Notional-$ caveat (DF-2/OQ-12) applies. |
| **`intent_router.cache_floor` span** (`intent_router_cache_floor_span`, `llm_factory.py:640-646`) | §6.4.3 / OQ-17 — the cache-floor guard is Anthropic-cache-specific; under the Agent SDK it likely becomes inert. Do not silently drop the span; either keep it emitting "n/a on agent-sdk transport" or document its retirement. |

**Cost figures must map to `ToolingResult` fields** (`input_tokens`, `output_tokens`,
`cached_input_read_tokens`, `cached_input_write_tokens`, the 5m/1h split, `cumulative_cost_usd`).
Where the Agent SDK supplies a figure → use it. Where it does not (per-TTL split, OQ-6) →
documented-zero + loud marker. The orchestrator's cost-rollup span
(`orchestrator.py:4114-4154`) reads these and must not crash on a zero it didn't expect (it
won't — they're ints/floats).

### 7.5 Fail-loud error surface (AC2)

`complete_with_tools` raises today via `AnthropicSdkClientError` /
`AnthropicSdkLoopExceeded` / `AnthropicSdkCostCeilingExceeded`. The port preserves these and
adds the auth-failure mapping:
- `ResultMessage(is_error=True)` with an auth/credit `subtype` (or a raised SDK exception on
  missing subscription) → raise an `AnthropicSdkClientError` subclass (e.g.
  `AgentSdkAuthUnavailable`) naming "subscription login absent — no PAYG fallback." **Never
  return a degraded-but-successful result for an auth failure** (that would mask the missing
  credential — the exact silent-fallback the SOUL rule forbids).
- `max_turns` hit → `AnthropicSdkLoopExceeded` (preserve the existing convergence-failure type).
- The pre-flight cost-ceiling check (`_check_cost_ceiling`, `:268-269`) stays at the top of
  `complete_with_tools`, unchanged.

---

## 8. Other `complete_with_tools` callers (inherited port)

### 8.1 Shared-surface callers

`complete_with_tools` is also called by:
- `aside_resolver.py:293` (the read-only aside, `tool_choice={"type":"none"}`)
- `materializer.py:1233` (dungeon curate one-shot, `session_id=None`, `caller` non-narrator)
- `orchestrator._rewrite_prose_without_fabricated_roll` (`orchestrator.py:3250`, `tools=[]`,
  toolless rewrite)

All three go through the same ported method and inherit subscription auth automatically.
Two contract points to preserve:
- **`tools=[]`** (toolless rewrite, fabricated-roll repair) — the SDK-MCP server is built
  with zero tools; `query()` must converge in one turn. **[OQ-13]** confirm `query()` with
  no tools + `system_prompt` behaves as a plain completion (the spike ran with
  `allowed_tools=[]` and converged, so this is low-risk but should be tested).
- **`tool_choice={"type":"none"}`** (aside) — the raw SDK forwards this to forbid tool
  calls while presenting the tools array (cache-prefix preservation). The Agent SDK has no
  documented `tool_choice` passthrough. **[OQ-14]** the aside's "present tools but forbid
  calls for cache-prefix preservation" trick is raw-SDK-cache-specific; under the Agent SDK
  the caching model is different (the CLI manages its own caching), so the aside likely just
  passes **no tools** (`allowed_tools=[]`). Confirm the aside still converges and the
  cache-preservation intent is either preserved or explicitly N/A on this transport (DF-3).

### 8.2 The non-narrator session_id=None bypass

`materializer.py` passes `session_id=None` (no per-session cost tracking, no runaway
detector — `:830-831`, `:557`). The port preserves the `session_id is None` bypass exactly.

---

## 9. Test strategy seeds for RED (TEA writes these)

Precise failing-test targets per AC. All tests must run **without a live subscription** —
they drive a **fake `query`/transport** injected via the seam in §6.2/OQ-9. The
project's import-side-effect-registry rule and the "no source-text wiring tests" rule
(server `CLAUDE.md`) apply: assert **behavior and OTEL spans**, never grep source.

**AC1 — Context isolation (the landmine):**
- `test_agent_sdk_options_pin_isolation` — construct the narrator client; assert the
  `ClaudeAgentOptions` it builds has `setting_sources == []`, `add_dirs == []`, `cwd` set
  to a non-repo path, and `system_prompt` equal to the assembled narrator string (no
  `preset`). (Unit on the options builder.)
- `test_narrator_output_not_contaminated_by_repo_claude_md` — the **behavioral** gate:
  drive a turn through a fake `query` that would (in the contaminated case) surface
  absorbed `CLAUDE.md` persona text; assert the converged narration contains none of the
  repo-context tells (no SM persona, no "SideQuest orchestrator" scaffolding). This is the
  spike-regression test — the spike answered in an SM persona; this proves the pins fix it.

**AC2 — Subscription auth, fail-loud, no PAYG fallback:**
- `test_narrator_path_raises_when_api_key_set` — with `ANTHROPIC_API_KEY` set on the
  narrator path, construction (or first call) **raises** (a set key would re-route to PAYG;
  the inverse of the old "key required" check).
- `test_auth_absent_raises_not_degrades` — a fake `query` that yields
  `ResultMessage(is_error=True, subtype=<auth/credit>)` (or raises) makes
  `complete_with_tools` raise `AgentSdkAuthUnavailable`, **not** return a degraded-success
  `ToolingResult`.
- `test_both_creds_unset_resolves_subscription` — with both creds unset, the options/seam
  is built for subscription resolution (no `api_key`/`auth_token` plumbed into the SDK).

**AC3 — Port fidelity:**
- **Per-tool contract** (`test_each_narration_tool_round_trips`): for the catalog
  `tool_definitions(ruleset)` returns, assert each tool's `name`, `description`, and
  `input_schema` survive the Pydantic→Agent-SDK translation **byte-equivalent** (the OQ-3
  gate); and that a tool call routed through the `@tool` bridge invokes
  `default_registry.dispatch` with a `ToolUseBlock` carrying the **bare** name and the
  model's args, and the returned `ToolResultBlock` content flows back to the SDK.
- **Convergence** (`test_tool_loop_converges` / `test_max_turns_raises`): a fake `query`
  that drives N tool calls then a clean `ResultMessage` yields a `ToolingResult` with
  `tool_calls` of length N, the converged text, and the right token/cost fields; a fake
  that hits `max_turns` raises `AnthropicSdkLoopExceeded`.
- **OTEL emission** (`test_otel_spans_preserved`): drive a converged tool-using turn through
  the fake; assert `narrator.tool_loop` fires with `iterations_used == num_turns` and
  `caller="narrator"`; `narrator.sdk.usage` watcher event fires; per-tool
  `tool.{read,write,gen}.{name}` dispatch spans fire (they come from the untouched
  registry); and — per OQ-6 — if the per-TTL split is unavailable, the documented-zero +
  marker path is asserted, not a silent 0.
- **Wiring test** (server `CLAUDE.md` "Every Test Suite Needs a Wiring Test"): one test
  proves the ported `complete_with_tools` is reachable from `_run_narration_turn_sdk`
  (fixture-driven behavior test — synthetic snapshot + real orchestrator call + assert
  narration emitted), not in isolation.
- **`tools=[]` toolless path** (`test_toolless_rewrite_converges`): the fabricated-roll
  repair / aside path converges with zero tools.

**AC3 (Haiku) — single-shot structured-extraction fidelity (2026-06-16 scope; Path A
`output_format` @ `max_turns=2`):**
All Haiku tests drive the **same fake `query`/transport seam** (OQ-9) — no live subscription.
**RED/GREEN GUARDRAIL: TEA's red MUST drive the confirmed `output_format` Path A at
`max_turns=2`; Dev MUST NOT hardcode `max_turns=1` from any stale spec text — `max_turns=1`
fails closed with `subtype='error_max_turns'` (VERIFIED, §3.6/OQ-16). At least one test
asserts the site builds `ClaudeAgentOptions(max_turns=2, output_format={"type":"json_schema",
"schema": <tool_schema>}, allowed_tools=[])` and reads `ResultMessage.structured_output`.**
- **Forced-extraction contract preserved** (Path A `structured_output`), per producing site:
  - `test_intent_router_emit_tool_returns_dispatch_package` — `_IntentRouterLlm.emit_tool`
    returns the structured `dict` (the DispatchPackage fields) from `structured_output` and
    **raises `IntentRouterEmptyResponse`** when the fake yields `structured_output=None` /
    `is_error=True`.
  - `test_unseeded_classifier_emit_tool_returns_objective` — same `dict`-or-raise contract
    for `_UnseededObjectiveClassifierLlm.emit_tool`.
  - `test_archetype_inference_returns_enum_validated_dict` — `infer_archetype_from_freeform`
    returns only newly-inferred axes, `{}` when nothing missing, **`None`** on empty freeform
    AND on out-of-enum (the existing No-Silent-Fallbacks reject at `llm_factory.py:944-960`),
    unchanged by transport.
- **`max_turns=1` fails closed** (`test_haiku_max_turns_one_raises`): a fake whose
  `ResultMessage` carries `subtype='error_max_turns'`/`structured_output=None` (the empirical
  `max_turns=1` shape) makes the site raise its loud error — guards against a stale
  `max_turns=1` regression.
- **Aside no-tools behavior** (`test_aside_complete_returns_text`): `_AsideLlm.complete`
  returns the assistant text via a plain no-tools `max_turns=2` `query()`.
- **Per-site OTEL + cost** (`test_haiku_llm_request_spans_and_caller_tags`): each ported site
  opens an `llm.request` span and emits `llm.sdk.usage` with the correct `caller` tag
  (`aside`/`intent_router`/`unseeded_objective_classifier`/`archetype_inference`) and the
  `session_id`-keyed `check_ceiling`/`record_call` still fire (or bypass on `session_id=None`).
- **Haiku auth fail-loud** (`test_haiku_path_raises_when_api_key_set` /
  `test_haiku_auth_absent_raises`): a set `ANTHROPIC_API_KEY` on a Haiku site raises; an
  auth-absent fake makes the site raise (not silently return an empty/`None` payload that a
  consumer might mistake for a legitimate "nothing to infer").

**GREEN-PHASE GATE (real-schema round-trip — NOT a red blocker, OQ-3-adjacent):** before
committing the implementation, Dev MUST round-trip the **real** `DispatchPackage.model_json_schema()`
(and the other producers' real schemas) through `output_format` against the live SDK and
confirm a schema-valid `structured_output`. The spike used a minimal hand-written schema; the
production schema's `$defs`/nested/`additionalProperties` were NOT exercised. If the raw schema
is rejected, apply the OQ-3 schema-adapt shim. This is a verification-before-commit gate, not a
red test (a red test cannot exercise a live subscription).

---

## 10. Migration & rollback summary

- **Edit surface:** the construction seam (§6.2) + the `complete_with_tools` body (§7) +
  the four Haiku single-shot bodies (§6.4). `tool_registry.py`, the orchestrator,
  `tooling_protocol.py` (signature), the `IntentRouterLLM`/`ObjectiveClassifierLLM`
  Protocols, the `infer_archetype_from_freeform` signature, and `cost_safety.py` are
  untouched in interface.
- **Env:** `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` **unset** on the host (narrator AND
  Haiku); subscription `claude` login present.
- **Dependency:** add `claude-agent-sdk` to `sidequest-server/pyproject.toml`. **Confirmed
  2026-06-16: it is NOT currently a dependency of `sidequest-server` or the orchestrator root**
  — the spikes pulled it via `uv run --with claude-agent-sdk`. Declaring it is a first
  implementation step (Dev), and a wiring/import test must prove the production path imports
  it, not a `--with` shim.
- **Rollback:** single-commit revert of the seam + bodies restores `AsyncAnthropic(api_key)`
  PAYG inference for all five sites; re-set `ANTHROPIC_API_KEY`. No caller/consumer changes
  needed (frozen signatures/contracts).
- **Scope (2026-06-16):** narrator path **and** all four Haiku sites — the whole bill moves.

---

## 11. Open Questions / Risks (flag, don't guess)

| # | Question | Why it matters | Disposition |
|---|---|---|---|
| OQ-1 | Exact import paths/names for `tool`, `create_sdk_mcp_server`, `ToolUseBlock`/`ToolResultBlock`, and the `mcp__<server>__<tool>` namespacing + recoverability of the bare name | The §5 translation depends on it | Confirm against installed package before red is finalized |
| OQ-2 | Exact `ResultMessage` field set and `subtype` error-code strings (`is_error`, `num_turns`, `usage`, the `max_turns`/auth/credit subtypes) | §7.2/§7.4/§7.5 convergence + error mapping | **UNVERIFIED** — read SDK types |
| OQ-3 | Does the raw Pydantic `model_json_schema()` dict ($defs/enum/nested/additionalProperties) round-trip verbatim — through `@tool`'s `input_schema` (narrator tools) AND `output_format`'s `schema` (Haiku, OQ-15 confirmed the *shape* but only on a minimal hand-written schema)? | **Highest remaining port-fidelity risk** (non-blocking for red). If not, a schema-adapt shim is needed at the boundary | **GREEN-PHASE GATE** (§6.4.2, §9): Dev round-trips the REAL schema(s) before commit; apply the shim if rejected. Stays OPEN as the umbrella for raw-schema acceptance. |
| OQ-4 | Exact `setting_sources` accepted values; is `[]` (vs `None`) the "load nothing" form; can `cwd` leak context with `setting_sources=[]`? | **The landmine** (AC1) | Set both defensively; behavioral test is the gate |
| OQ-5 | Is there an up-front "subscription credential present?" probe, or only post-hoc failure? | Fail-loud (AC2) shape | Build on failure detection unless a probe exists |
| OQ-6 | Does the Agent SDK expose the per-TTL cache-creation split (`ephemeral_5m/1h_input_tokens`)? | `narrator.cache.both_writes_fired` + `write_split` fidelity | If absent → documented-zero + loud marker (No Silent Fallbacks) |
| OQ-7 | ~~Is 119-3 narrator-only, with the Haiku callers a separate follow-up?~~ | — | **RESOLVED 2026-06-16: RULED IN.** Operator ruled the Haiku callers move in this story (8→13 pts). The risk this surfaced is now tracked as OQ-15/16/17. |
| **OQ-15** | ~~Does the Agent SDK expose `output_format` → `ResultMessage.structured_output` accepting our schema dicts?~~ | — | **RESOLVED GO (VERIFIED 2026-06-16, `scripts/spike_119_3_haiku_outputformat.py`).** `output_format={"type":"json_schema","schema": <dict>}` and `ResultMessage.structured_output` exist on the released SDK and round-trip a typed schema to a clean dict on `claude-haiku-4-5`/subscription. **Path A is the implementation; Path B (prompt-coerced) is NOT required.** Caveat folded into the `max_turns=2` requirement (OQ-16) and the OQ-3 green-phase real-schema gate. |
| **OQ-16** | ~~Under `max_turns=1`, does the single-shot yield output or stop?~~ | — | **RESOLVED (VERIFIED 2026-06-16).** `max_turns=1` fails closed: `is_error=True`, `subtype='error_max_turns'`, `structured_output=None`, `query()` raises — the SDK always spends an internal finalize turn (`num_turns=2`). **`max_turns=2` is the minimum viable** and is specified for every structured-extraction single-shot. RED/GREEN guardrail in §9 prevents a stale `max_turns=1`. |
| **OQ-17** | Does the Agent SDK cache a stable Haiku system prefix; does the 91-3 `intent_router.cache_floor` guard + `extended-cache-ttl` machinery become inert? | The Intent Router's 1h cache is the [COST-1] saving on PAYG; on the subscription pool the $ is ~$0 so the cache's purpose is largely moot, but the floor-guard span and its fail-loud value need a disposition | UNVERIFIED; treat cache-guard removal as a follow-up cleanup, not silently — a future raw-SDK Haiku path would lose protection (§6.4.3) |
| OQ-8 | Cost of building an SDK-MCP server per `complete_with_tools` call (per-turn) | Latency; possible caching follow-up | Not a 119-3 blocker; measure |
| OQ-9 | The fake-SDK/transport injection seam for `claude-agent-sdk` (no `messages.create` to patch) so TEA drives convergence without a live subscription | All RED tests depend on it | Candidate: late-bound module-dict `query` reference (mirrors `build_async_anthropic` doctrine) |
| OQ-10 | Are intermediate turn boundaries observable mid-stream (for live `llm.request`/cap-hit spans) or only post-hoc via `num_turns`? | OTEL granularity | Post-hoc preserves the signal; live is nice-to-have |
| OQ-11 | Does the SDK surface multiple `TextBlock`s per assistant message (multi-text discard still needed) or one converged `result`? | §7.3 doubled-narration rule | Either way output must be the single converged telling |
| OQ-12 | `total_cost_usd` on the subscription path is the CLI's *notional* estimate, not a real charge | Cost-runaway detector + $10 ceiling thresholds may need recalibration | DF-2; thresholds likely loosen — Operator to weigh |
| OQ-13 | Does `query()` with no tools + `system_prompt` behave as a plain one-turn completion? | Toolless rewrite / aside | Low-risk (spike converged with `allowed_tools=[]`); test it |
| OQ-14 | The aside's `tool_choice={"type":"none"}` "present tools, forbid calls, preserve cache prefix" trick has no Agent-SDK analog | Aside cache-preservation intent | Likely N/A on this transport (CLI owns caching); confirm + document (DF-3) |

---

## 12. Delivery Findings (upstream observations)

### Architect (design)
- **Question (blocking) — DF-1: RESOLVED 2026-06-16 (RULED IN).** Operator ruled the four
  Haiku callers (`IntentRouter`, aside, classifier, archetype) move off PAYG in this story,
  not a follow-up (8→13 pts). The §6.4 Haiku port design and OQ-15/16/17 now cover it.
  *Found by Architect during design; resolved by Operator ruling.*
- **Risk (blocking) — DF-5: RESOLVED GO-WITH-CAVEAT (VERIFIED 2026-06-16,
  `scripts/spike_119_3_haiku_outputformat.py`).** The Agent SDK exposes no `tool_choice`, but
  the forced-extraction need is met by its first-class `output_format` JSON-schema structured
  output (Path A) — API-enforced, not prompt-coerced. The spike confirmed `output_format` /
  `ResultMessage.structured_output` on `claude-haiku-4-5`/subscription, accepting the
  `{"type":"json_schema","schema": <dict>}` shape verbatim and returning a clean schema-valid
  dict. **Caveat: `max_turns=2`, not `1`** — the SDK spends an internal finalize turn, so
  `max_turns=1` fails closed (`error_max_turns`). Path B (prompt-coerced) is dropped to a
  documented-unused fallback. **Residual (OQ-3-adjacent, NOT a red blocker):** the spike used a
  minimal hand-written schema; the real `DispatchPackage.model_json_schema()` ($defs/nested)
  was not exercised — a green-phase round-trip gate (§6.4.2/§9) covers it before Dev commits.
  Affects `sidequest/agents/llm_factory.py` (the three forced-extraction sites). *Found by
  Architect during design (2026-06-16 scope expansion); resolved by the output_format spike.*
- **Improvement (non-blocking)** — DF-2: The subscription path's `total_cost_usd` is the
  CLI's *notional* estimate, not a billed charge — for **both** the narrator and the Haiku
  sites (which feed the same `session_id`-keyed ledger). The cost-runaway detector and the
  $10 per-session ceiling (`cost_safety.py`) are calibrated against real PAYG dollars; their
  thresholds likely need recalibration (or re-framing as "notional-$ shape signals").
  Affects `sidequest/agents/cost_safety.py` (threshold semantics). *Found by Architect during design.*
- **Question (non-blocking)** — DF-3: The aside's `tool_choice={"type":"none"}`
  cache-prefix-preservation trick (ADR cache layout) has no Agent-SDK analog — the CLI owns
  its own caching. The aside likely becomes a plain no-tools completion under the new
  transport; the cache-preservation intent is probably N/A here. Affects
  `sidequest/agents/aside_resolver.py`. *Found by Architect during design.*
- **Gap (non-blocking)** — DF-4: The `claude-code-guide` doc claims subscription OAuth is
  "not supported" by the Agent SDK, directly contradicting the working
  `scripts/spike_119_3_agentsdk_subscription.py` GO result. The spike is authoritative for
  this environment (every-playtest-is-production doctrine); the doc claim is stale. Worth a
  note in ADR-101's amendment so a future reader doesn't "correct" the working code to the
  doc. *Found by Architect during design.*
