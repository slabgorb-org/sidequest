---
parent: context-epic-92.md
workflow: tdd
---

# Story 92-4: Playtest verification + cost proof — full session with agent.backend=ollama spans firing; 91-5 reconciliation shows Haiku line ~zero

## Business Context

This is the **proof story** — the receipt that the epic-91 + epic-92 bet paid off.
Epics 91 and 92 exist because per-turn unit economics make or break the SideQuest
business model (operator, 2026-06-05): the Haiku classification tier was ~half the
daily Anthropic bill ($3.3–3.5/day, 100% uncached, ~8×/turn and growing with play
volume). 92-2 flipped that workload to the local Ollama/qwen stack at $0 marginal
cost. **This story produces the before/after evidence** that the flip actually
worked: the Haiku line on the Admin API goes to ~zero, and the narrator (Sonnet)
numbers are *unchanged* — savings without collateral damage.

It is also the **SOUL check**. A misclassified dispatch is an agency problem, not
just a cost problem (epic-92 Background, "Why a hard A/B gate"): the player attempts
something and the wrong subsystem — or none — engages. 92-1's offline A/B gate
cleared classification *agreement* on captured corpus, but a full live session is the
only thing that proves local classification doesn't degrade **play**: real intent
router dispatch firing correctly *in vivo*, turn latency within budget, the
mechanical-engagement spine still engaging the right engines. The before/after cost
report is the business-model receipt; the live session is the agency receipt.

## Technical Guardrails

- **Verification is OTEL-first, not vibes.** The GM panel is the lie-detector
  (CLAUDE.md OTEL Observability Principle). The evidence that classification went
  local is `agent.backend="ollama"` spans (the attribution shipped in 48-2, lives on
  `agent_call_span` / `agent_call_session_span` in
  `sidequest-server/sidequest/telemetry/spans/agent.py`) plus 91-1's per-call caller
  tags on the choke-point usage telemetry. "The router feels local" is not evidence;
  the span census is.
- **Drive with the scripted playtest driver against a live server configured for
  Ollama.** `scripts/playtest.py` mints a fresh game, auto-completes chargen, and
  drains a scenario's scripted actions one per turn (`just playtest-scenario <name>`).
  Capture the span tree with `--span-jsonl` (requires `just jaeger` + `just up-traced`
  so the server exports OTEL→Jaeger; a missing/empty capture fails the run loud,
  exit 1). The concrete scenarios that exercise the intent router every turn:
  - **`scenarios/combat_otel.yaml`** — 25 combat/exploration/NPC/inventory actions,
    explicitly built as an OTEL telemetry generator; maximal router + dispatch-bank
    engagement (confrontation, movement, npc_agency). **Primary run.**
  - **`scenarios/smoke_test.yaml`** — short 7-action basic-loop sanity pass (includes
    `/status`, `/inventory` slash commands) for a fast confidence check first.
  - **`scenarios/latency_diag_82_9.yaml`** — tea_and_murder/glenross investigation
    session built specifically to produce a usable router-decompose + narration p50/p95
    sample; use it for the latency comparison (see below).
- **Cost proof = 91-5 reconciliation + Admin API over the post-flip window.** Run the
  91-5 dark-spend reconciliation (instrumented per-model totals vs Admin API per-model
  totals) and read the **Haiku** line. Mind the bucketing: Admin API buckets are
  **UTC** while server-log rotations are local-time stamped — allow a **clean full UTC
  day** after the flip so the window isn't smeared by the pre-flip tail (91-5 AC-4 day
  boundary caveat). Use the `/sq-llm-costs` three-layer method as the manual backstop:
  Layer-3 Admin API (`uv run --project . python scripts/anthropic_usage.py --days 7
  [--raw]`) is the **ground truth** for "Haiku line ~zero."
- **Latency: compare turn p95 against the pre-flip baseline.** The harness exists —
  `sidequest/telemetry/latency_report.py` (`latency_percentiles` /
  `LatencyPercentiles`, reuses `validator._percentile`, no second impl) feeds from the
  `--span-jsonl` capture; `scenarios/latency_diag_82_9.yaml` is the driver. Local
  classification adds per-turn inference overhead, so this is the SOUL-side risk to
  measure: turn p95 must stay within the budget 92-1 set (48-2 validated ≤3× the Claude
  baseline for narration; classification is per-turn overhead the player feels).
- **Narrator baselines must hold.** This story changes **nothing** Sonnet-side — the
  narrator loop is healthy and out of scope (epic-91 "What is healthy — do not touch").
  Confirm cost/turn stays in **6.6–7.6¢** and cache hit rate in **76–82%** post-flip.
  A regression here means the flip leaked into the narrator path — a finding, not a
  pass.
- **Distinguish residual Haiku before declaring victory.** "~Zero" will not be exactly
  zero. Any residual Haiku spend after the flip is **either** asides not yet folded
  (check 92-3 status — if 92-3 hasn't landed, ADR-107 asides still route to Haiku and
  that residual is *expected*) **or** a NEW dark spender (a fresh uninstrumented caller,
  exactly the [COST-1] failure mode). Name which one before calling it a win — an
  un-attributed residual is a finding to file, not noise to round away.

## Scope Boundaries

**In scope:**
- Scripted **and** interactive playtest of a full session with local classification
  routing enabled (config = ollama).
- OTEL evidence capture: `agent.backend=ollama` span census + 91-1 caller tags proving
  every router pass went local.
- A written **before/after cost report** (Haiku $/day pre-flip → ~0 post-flip,
  narrator unchanged) — the business-model receipt.
- **Latency comparison** (turn p95 post-flip vs pre-flip baseline).
- **Filing findings via pingpong** for anything the playtest breaks (dispatch
  misclassification, span gaps, latency regressions, malformed qwen tool output).

**Out of scope:**
- **Fixing what the playtest finds.** This story *verifies*; bugs get filed with
  evidence (same discipline as `/sq-llm-costs`: "never fix code from this skill").
- **92-3 (asides → local) if it hasn't landed.** Do not implement it here; report the
  residual aside-Haiku spend as the expected un-migrated caller and name it.
- **Any tuning or fine-tuning** — no prompt slimming (82-10), no qwen model swaps, no
  threshold adjustment. Verification only.

## AC Context

Testable acceptance — each is an evidence artifact, not a vibe:

1. **Full scripted scenario completes with config=ollama, every router pass emitting
   `backend=ollama`.** Run `combat_otel.yaml` end to end; in the `--span-jsonl`
   capture, **count of router/classification spans carrying `agent.backend="ollama"`
   == count of turns** (one router pass per turn). The 91-2 budget assertion (call
   volume per turn) validates this from the cost side too — call count should be ~1
   classification call/turn, not the pre-flip ~8×.
2. **Post-flip Admin API window shows Haiku tokens ~zero.** Over a clean full UTC day
   after the flip, the Admin API Haiku line is ~zero. **Define "~zero" by enumeration:**
   only un-migrated callers remain, each one named (e.g. ADR-107 asides if 92-3 hasn't
   landed; the `CallType.SCRATCH` dungeon-curate path if it fired). Zero un-named
   residual.
3. **Turn-latency p95 within the 92-1 budget.** From the `latency_diag_82_9.yaml`
   capture fed through `latency_report.latency_percentiles`, solo-turn p95 is within
   the latency budget 92-1 established. Cite the pre-flip baseline number in the report.
4. **Narrator cost/turn and hit-rate within the healthy band.** Post-flip narrator
   cost/turn in 6.6–7.6¢ and cache hit rate 76–82% (Sonnet untouched).
5. **Written before/after report committed** — the business-model receipt. Suggest
   `docs/` (a dated cost-proof note) or the session artifact. Must contain: Haiku
   $/day before → after, the named residual callers, narrator-unchanged confirmation,
   latency before/after, and the `agent.backend=ollama` span count == turn count
   evidence.

## Assumptions

- **92-2 is merged and configured** — the router's local rung is live and the running
  server is started with the Ollama backend selected (config = ollama). If 92-2 isn't
  in, this story cannot start (hard dependency).
- **91-5 reconciliation is available.** If 91-5 landed, use its programmatic
  per-model reconciliation for the cost proof. **If 91-5 is NOT landed, fall back to
  the manual `/sq-llm-costs` three-layer method (Layer-3 Admin API ground truth) and
  SAY SO explicitly in the report** — don't silently substitute and imply the
  automated detector ran.
- **A server + Ollama environment is available for a full session** — the M3 Ultra
  with the qwen model resident (48-2 setup), Jaeger up for span capture
  (`just jaeger` / `just up-traced`), and the Admin key (`ANTHROPIC_ADMIN_KEY`,
  `sk-ant-admin…`) in env for the Layer-3 / 91-5 Admin pull.
