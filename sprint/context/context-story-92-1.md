---
parent: context-epic-92.md
workflow: tdd
---

# Story 92-1 Context

## Title
A/B eval: Haiku vs local qwen on real captured Intent Router corpus (48-4 harness; acceptance threshold on DispatchPackage classification agreement + latency budget)

## Metadata
- **Story ID:** 92-1
- **Type:** chore
- **Points:** 3
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Epic:** 92 — Local Classification Routing (Haiku → Ollama/qwen)
- **Deps:** none. **GATES** 92-2 (router local rung) and 92-3 (asides).

## Business Context

This is **the gate story**. Epic 92 takes the high-frequency classification
workload (Intent Router ADR-113) off Anthropic billing and onto the local
Ollama/qwen stack — $3.3–3.5/day → $0 marginal. But the Intent Router is the
**mechanical-engagement spine** (ADR-113 → ADR-123 dispatch bank): it reads each
player action and emits a `DispatchPackage` that decides *which subsystem
engages before the narrator runs*. A misclassified dispatch silently degrades
player agency — the player attempts something and the wrong engine (or none)
fires, while the narrator still reads fine. That is a **SOUL/agency failure, not
a cost line**, and exactly the Illusionism the OTEL panel exists to catch. Cost
savings cannot buy it back.

So **no routing flip without evidence.** This story produces *only data and a
documented go/no-go threshold* — it changes no production routing. Its output is
the artifact 92-2's acceptance gates on: classification-agreement rate, qwen
schema-validity rate, and a latency distribution, plus a written recommendation
against the epic's proposed **≥95% dispatch-selection agreement** bar (with
disagreements manually adjudicated — where qwen is *right* and Haiku was *wrong*,
that counts **for** the local model, not against). If agreement fails the gate,
that is a **finding** that informs 92-2/ADR-073, not a defect to patch in this
story.

## Technical Guardrails

**Extend the 48-4 harness — do not fork it.** `sidequest/agents/ab_eval_harness.py`
(the `AbEvalHarness` + `AbEvalResult`/`AbEvalReport` dataclasses) already exists
and is the named epic deliverable to reuse. But read its current shape honestly:
it is **narration-shaped, not router-shaped**. Today it:
- drives both backends through `LlmClient.send_stateless(system_prompt, user_message, model)`
  — a free-text completion boundary, **not** the router's `emit_tool` tool-use call;
- scores *patch validity* by splitting the response at the first `{` and checking the
  JSON tail parses to a dict (`_validate_patch`) — this is the **narrator's** game-patch
  protocol, not `DispatchPackage` validation;
- scores *narration similarity* (`SequenceMatcher` on prose) and *declared-key Jaccard*
  (`_beats_overlap`) — neither is a dispatch-selection agreement metric;
- consumes `TrainingPair` rows (`pair.input_text` = player action, `pair.output_text` =
  narrator output) via `eval_batch`.

So the harness gives us the **runner skeleton, the per-side isolation discipline
(rule #9 — one backend failing never loses the other), the latency timing, the
markdown report shape, and the `LlmClient`-protocol guard** — all reusable. What
it does **not** give us is anything that understands `DispatchPackage`. The real
work is teaching it to (a) drive the router's actual call shape and (b) score
**dispatch selection**, **schema validity against `DispatchPackage`**, and
**latency** — the three measurements below.

**The router's real call shape.** `IntentRouter.decompose` (intent_router.py)
does NOT use `send_stateless`. It calls the `IntentRouterLLM` protocol's
`emit_tool(system, user, tool_name, tool_description, tool_schema)` and expects
back an already-structured dict, which it feeds to
`DispatchPackage.model_validate`. The user prompt is built by
`_build_user_prompt(action, state_summary)` — `<game_state>…</game_state>` +
`<raw_action>…</raw_action>`. **Any qwen adapter the harness drives must satisfy
this `IntentRouterLLM` protocol** (or the harness must call the real router with
a qwen-backed adapter injected), so that what we measure is the *production code
path*, not a parallel reimplementation.

**Corpus = REAL captured router prompts — and capture is likely the bulk of this
story.** The existing corpus pipeline (`sidequest/corpus/miner.py` →
`mine_save`) emits `TrainingPair` = (player action → **narrator** output). That
is the wrong corpus: it has no `state_summary` and no `DispatchPackage` ground
truth. A router A/B needs `(action, state_summary) → DispatchPackage` triples.
Two viable capture sources exist; pick and state which:
- **OTEL spans.** `intent_router_decompose_span` records `action_length`,
  `dispatch_count`, `confidence_global`, `latency_ms` (success), and
  `intent_router_failed_span` records a `raw_preview` (160 char cap). These are
  *summaries*, not full prompts — `raw_preview` is truncated and the decompose
  span does not persist the full `(action, state_summary)` input or the emitted
  `DispatchPackage`. Usable as a *signal of real traffic distribution*, probably
  not as replayable corpus without enrichment.
- **Save replay / scene harness.** Saves hold the per-round player actions and
  the canonical snapshots; re-running `IntentRouter.decompose` against
  reconstructed `(action, state_summary)` from a real save gives Haiku-baseline
  `DispatchPackage` outputs to use as ground truth. ADR-092's scene harness is
  the dev-gated fixture hook if a synthetic-but-realistic spine is needed.

**Flag corpus-capture as possibly the real work of this story.** There is no
existing capture path that emits replayable `(action, state_summary) →
DispatchPackage` rows. Building one (a router-corpus schema sibling to
`TrainingPair`, plus a capture/replay tool) is net-new and is where the points
go.

**Measure THREE things:**
1. **Dispatch-selection agreement** — per-turn, do Haiku and qwen select the same
   subsystem dispatch set (`SubsystemDispatch.subsystem` keys, and the load-bearing
   `params` like confrontation `type`/`opponent`)? This is the ≥95% gate metric.
   Report it **per dispatch type** (confrontation / magic_working / scenario_clue /
   npc_agency / movement / equip / witnessed_act / …) so a single weak class is
   visible, not averaged away.
2. **Schema-validity rate of qwen tool output** — the epic's **named top risk**.
   qwen tool-calling ≠ Anthropic tool-calling: `OllamaClient.capabilities()`
   reports **`supports_tools=False`** (verified — see Assumptions). So qwen cannot
   issue a native forced-tool call; it must emit `DispatchPackage` JSON some other
   way, and the rate at which that JSON survives `DispatchPackage.model_validate`
   (with `extra="forbid"` — one stray key rejects the whole package) is a
   first-class metric, not a footnote.
3. **Latency distribution (p50/p95)** — classification is **per-turn overhead** on
   the live path. Report percentiles, not just the harness's current average. Honor
   the **48-2 precedent**: `num_ctx` must be set load-time via the Modelfile, never
   per-request — a per-request override forces a **~28s KV reload** that would poison
   every latency sample. Keep the model resident (M3 Ultra); avoid anything that
   evicts it (ADR-046 GPU coordination if the daemon renders concurrently).

## Scope Boundaries

**In scope:**
- Capture/curation of a real router corpus: `(action, state_summary) →
  Haiku-baseline DispatchPackage` rows from saves/OTEL, plus the schema + tool to
  produce them deterministically.
- Harness extension to drive **both backends on identical prompts through the
  router's real `emit_tool`/DispatchPackage shape**, deterministically re-runnable.
- A report covering per-dispatch-type **agreement**, qwen **schema-validity %**,
  and **latency percentiles** (p50/p95).
- A **recommended threshold + written go/no-go artifact** for 92-2, evaluated
  against the ≥95% proposal, with disagreements manually adjudicated and
  classified.

**Out of scope:**
- **Any production routing change** — that is 92-2 (the local rung in
  `model_routing.py`/`llm_factory.py`). This story touches no live turn path.
- **Aside prompts** — 92-3 (ADR-107). 92-3 can *reuse this story's method*; do not
  build it here.
- **Fine-tuning qwen** — future ADR-073 work. If agreement fails the ≥95% gate,
  that is a recorded **finding**, not a fix to attempt in this story.
- **The dark-spend fallback temptation** — do not add a Haiku fallback path "to be
  safe." Per No Silent Fallbacks, a wedged Ollama must fail loud; the harness only
  *measures*, it does not wire routing.

## AC Context (testable)

1. **Corpus exists.** A corpus of **N real `DispatchPackage` prompts** is captured
   with ground-truth / Haiku-baseline outputs. Pick and justify N — **suggest
   ≥100**, spanning the live dispatch types (confrontation, magic_working,
   scenario_clue, npc_agency, movement, equip, witnessed_act, distinctive_detail,
   reflect_absence) so per-type agreement is meaningful. Each row carries
   `(action, state_summary)` plus the Haiku-baseline `DispatchPackage`.
2. **Harness drives both backends on identical prompts, deterministically
   re-runnable.** Same `(action, state_summary)` → both Haiku and qwen, through the
   router's `emit_tool`/`DispatchPackage` path; re-running yields the same report
   modulo backend nondeterminism (and that nondeterminism is itself characterized,
   not hidden).
3. **Report produced** with: per-dispatch-type **agreement**, qwen
   **schema-validity %**, and **latency percentiles (p50/p95)** for each backend.
4. **Disagreements manually adjudicated** and classified as **qwen-wrong /
   haiku-wrong / both-defensible** (reuse the spirit of
   `corpus/schema.py::DisputeTag`). qwen-right-Haiku-wrong counts **for** qwen.
5. **Written go/no-go recommendation** against the **≥95%** dispatch-selection
   proposal, naming the latency budget 92-2 should inherit (p95 ceiling) and the
   schema-validity floor below which the flip is unsafe regardless of agreement.

**TDD note:** the CI-safe unit layer stays fully mocked (mirror the existing
`AbEvalHarness` `LlmClient`-protocol guard and `tests/agents/test_ab_eval_harness.py`);
the **live A/B is operator-evidence on the M3 Ultra**, exactly as the 48-4 CLI
(`scripts/ab_eval_harness_cli.py`) already handles via the exit-4 Ollama-unreachable
no-op. Per CLAUDE.md, include at least one wiring test proving the new scoring path
is reachable from the real router call shape (OTEL-span or fixture-driven behavior,
**not** source-grep).

## Assumptions

- **qwen models still resident on the M3 Ultra:** `qwen3-coder:30b` and
  `qwen2.5:7b-instruct` (the harness's `OLLAMA_MODEL` default is `qwen2.5:7b-instruct`).
  **Suggest testing both** — 7b for the latency picture, 30b for the accuracy picture
  — and reporting them as separate columns; the go/no-go may differ by model.
- **Ollama structured-output capability:** **VERIFIED ABSENT at the tool layer.**
  `OllamaClient.capabilities()` returns `supports_tools=False`, and the client has
  **no `emit_tool` method** — it only exposes `send_with_model` / `send_with_session`
  / `send_stateless`. There is therefore **no native forced-tool path** to satisfy
  `IntentRouterLLM.emit_tool`. The fallback is the production reality this story must
  measure: **prompt-coerced JSON (Ollama `format=json` / a JSON-mode prompt) →
  `DispatchPackage.model_validate`**, with the **schema-validity rate** standing in for
  what Anthropic tool-use guarantees by construction. (Building the qwen
  `IntentRouterLLM` adapter that wraps that JSON path is 92-2's job; this story may
  need a thin measurement-only version of it to run the A/B — keep it in the harness,
  not the live router.)
- **Haiku baseline is ground truth-ish, not gospel.** The Haiku-baseline
  `DispatchPackage` is the comparison anchor, but AC4's adjudication explicitly allows
  "haiku-wrong / both-defensible" — do not treat Haiku agreement as the sole correctness
  signal.
- **No live-path mutation.** Running the harness must not write saves, mutate game
  state, or hit the production WebSocket path; corpus capture reads saves
  **read-only** (the `SaveReader` `immutable=1` contract).
