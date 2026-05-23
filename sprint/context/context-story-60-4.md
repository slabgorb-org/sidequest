---
parent: context-epic-60.md
workflow: tdd
---

# Story 60-4: Fix narrator cache_write churn — 1h cache breakpoint on tool-loop continuation

## Business Context

Closes Epic 60. Story 60-3 (diagnosis spike) **measured** that every narrator turn
in `tea_and_murder/glenross` wastes ~$0.089 in `cache_write` — about **76% of the
$0.116/turn cost**. The cause is *not* the original "mis-zoned state sections"
hypothesis (60-3 disproved that): the cached `system_blocks[0] + tools` prefix is
byte-stable (`7c926d96` constant across turns) and the suspect `state` sections
are User-bucket / uncached. The real cause is the narrator's **tool-use loop**:
the first call of a turn caches the prefix at **1h**, but every continuation call
(iter 2+, carrying `tool_use`/`tool_result`) **re-mints the whole ~11.7k prefix
at the default 5-minute TTL** — because the growing tool-use conversation carries
no `cache_control` breakpoint (markers sit only on `system_blocks[0]` and the
tools array, which precede the messages in cache-prefix order). At
submit-and-wait cadence the 5m copy expires between turns, so the prefix is
re-paid every turn — twice, since both iter 1 and iter 2 write before iter 3
reads.

**Value delivered:** ~70% per-turn narrator cost reduction (measured: $0.116 →
~$0.035/turn). An 85-turn glenross session drops from ~$9.88 to ~$3.01. Beyond
the dollars, the fix removes a "looks-fine-on-the-Prompt-tab" trap — the cached
prefix is *byte-stable* and *cache-marked* yet still re-written every turn — so
future cache work proceeds against a baseline that actually rebates.

This story also corrects two paper-cuts surfaced by 60-3: (a) the `mis_zoned`
flag in `_compute_zones_payload` is bucket-blind and flags User-bucket sections
that cannot churn block 0 (false positive that misled the original epic
framing); and (b) `anthropic_cost.py` prices 1h writes at the 5m rate, so the
GM-panel `cost_usd` understates real 1h-write billing.

## Technical Guardrails

**Authoritative reference:** `sprint/archive/60-3-session.md` →
"Dev Diagnosis (60-3 — FINAL, measured 2026-05-22)". The fix paragraph and the
measurement chain there are the spec; this story implements it. No
re-interpretation.

**Key files (server only):**

| File | Lines | Role |
|------|-------|------|
| `sidequest/agents/anthropic_sdk_client.py` | `complete_with_tools` ~105-274 (append site ~267-270) | **Primary fix.** Add moving 1h `cache_control` breakpoint on the newest continuation message; clear stale markers. |
| `sidequest/agents/orchestrator.py` | `_compute_zones_payload` ~140-200 (assignment line ~186) | **Secondary fix.** `mis_zoned` must AND zone-`cached` with bucket — only flag sections that actually ride `system_blocks[0]`. |
| `sidequest/agents/anthropic_cost.py` | 1h-write pricing | **Tertiary fix.** Price 1h writes at the real 2× rate (~$6/Mtok for Sonnet), not the 5m rate ($3.75). |
| `tests/agents/test_anthropic_sdk_client.py` | new tests | Regression coverage for the continuation marker. |
| `tests/agents/test_prompt_cache_attribution_otel.py` *(or sibling)* | new test | `mis_zoned` AND-with-bucket regression. |

**Patterns to follow:**

- **No silent fallback.** If the API still bills the continuation at 5m, surface
  it — don't downgrade or retry. The existing 1h beta-header logic (line 140-142)
  already follows this rule; the new marker must too.
- **Breakpoint cap = 4.** Anthropic rejects more than 4 `cache_control` markers
  per request. Two are already in use (`system_blocks[0]` + last tool entry).
  The new continuation marker must **clear any stale message-level markers from
  previous iterations** before adding itself, so the count stays ≤ 4 regardless
  of loop depth.
- **Use `self.cache_ttl`** (not a hardcoded `"1h"`). The client supports both 5m
  and 1h TTLs and chooses the beta header accordingly (line 140-142). The marker
  TTL must match the configured client TTL so the 5m configuration path stays
  functional. Default is 1h per `ttl_default()`.
- **Mark the LAST content block of the newest message**, per 60-3's measurement
  (the proved-effective configuration was `cache_control{ttl:1h}` on the last
  block of the user `tool_result` message). Marking the `assistant` `tool_use`
  message instead, or marking only the first content block, is *not* the
  measured fix.
- **OTEL discipline (CLAUDE.md).** Every subsystem decision emits a span. The
  per-iter `narrator.sdk.usage` log + the LLM request span (lines 145-200) are
  already in place and break out `5m`/`1h` per-TTL writes — the fix is testable
  through them. No new OTEL surface required, but tests should assert against
  span attributes / the per-iter ledger rather than scraping log lines.
- **No source-text wiring tests (CLAUDE.md).** Tests assert on
  `cache_creation.ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens`
  values from a real `complete_with_tools` invocation, or on the dict structure
  of the `messages` payload sent to the SDK — not on regexing the source of
  `anthropic_sdk_client.py`.

**Integration points:**

- The marker placement happens **after** `running_messages` is extended with the
  new assistant+user pair (line 267-270) but **before** the next loop iteration's
  `messages.create` call (line 146). This is a one-line conceptual change at the
  end of the loop body.
- `_compute_zones_payload`'s callers must keep working: `mis_zoned` is consumed
  by the Prompt tab (60-2 work). Verify no downstream regression by exercising
  the existing `prompt_assembled` test surface.

**What NOT to touch:**

- **Do NOT re-zone the three suspect `state` sections**
  (`narrator_available_confrontations`, `trope_beat_directives`, `npc_roster`).
  60-3 measured them as User-bucket → uncached → re-zoning is a no-op for cost
  and a regression risk against ADR-101 Phase D zoning.
- **Do NOT change `_build_system_array` or `_build_tools_array`.** Their
  existing markers are correct; they cache the byte-stable prefix. The bug is at
  the messages-array layer, not the system-array layer.
- **Do NOT introduce a "retry at 5m" fallback** if 1h is configured. CLAUDE.md
  is explicit: no silent downgrades.
- **Do NOT touch ADR-101 Phase D zone assembly** (`orchestrator.py:3199-3222`).
  Out of scope; covered by 60-3's measurement that the cached prefix is correct.

## Scope Boundaries

**In scope:**

- Add a moving `cache_control={"type":"ephemeral", "ttl": self.cache_ttl}`
  marker on the last content block of the newest continuation message inside
  `complete_with_tools`, with stale-marker cleanup so total breakpoints stay
  ≤ 4.
- AND-correct the `mis_zoned` flag in `_compute_zones_payload` so it only flags
  `state`-category sections that actually ride `system_blocks[0]` (zone-cached
  **and** bucket-stable).
- Correct `anthropic_cost.py` 1h-write pricing to the real 2× rate (Sonnet:
  $6/Mtok input-1h-write, vs the current $3.75 5m rate). Update any unit tests
  that pin the old rate.
- Regression tests: continuation `cache_creation` lands in
  `ephemeral_1h_input_tokens` (not 5m), steady-state continuation `cache_write`
  → 0 after warmup, `cache_read > 0` on the continuation.
- Test for `mis_zoned`: a `state`-category section in a cached zone but a
  User-bucket section returns `mis_zoned=False`; a `state`-category section in a
  cached zone AND a stable-bucket section returns `mis_zoned=True`.
- Update the 60-3-annotated docstrings in `anthropic_sdk_client.py` /
  `orchestrator.py` to reflect the fix (replace "60-4 will fix" → "fixed in
  60-4"; cite this story's commit).

**Out of scope:**

- Re-zoning of any `state`-category section. (Disproved by 60-3 as a no-op for
  cost.)
- ADR-110 snapshot slimming, ADR-111 recency-zone guardrails, ADR-112 prose
  cache promotion. (Independent deferred ADRs; this story is a behavior fix
  inside the SDK client, not a prompt-shape change.)
- Any change to `system_blocks` assembly, `STABLE_SECTION_NAMES`, or zone→bucket
  routing.
- Prompt-tab UI changes. (60-2 already shipped the eyes used for measurement;
  this story's verification reads the existing per-iter `cache_creation`
  breakdown.)
- Multi-narrator-backend changes. The `claude -p` and Ollama backends do not
  participate in the cache-write problem (no tool-use loop, no Anthropic
  caching surface).

## AC Context

Story description lists the fix in one paragraph; the testable AC set derived
from the 60-3 evidence chain is:

**AC-1 — Continuation writes land in the 1h bucket.**
On a tool-use-loop turn where the client is configured with `cache_ttl="1h"`,
the iter-2+ `messages.create` response must show
`cache_creation.ephemeral_1h_input_tokens > 0` and
`cache_creation.ephemeral_5m_input_tokens == 0` for the prefix-sized write
(~11k tokens) that previously landed in `5m`. *Verifies the marker is attached
to the right content block and that the beta header propagates on continuation
calls.* Edge case: a turn that resolves in one iter (no tool use) must remain
unchanged — no continuation write happens, no extra marker is added.

**AC-2 — Steady-state continuation re-reads at 1h.**
After AC-1 has happened once on a given prefix, a subsequent identical
continuation (same `system_blocks` + tools + a matching `tool_use`/`tool_result`
pair) must show `cache_write == 0` and `cache_read >= prefix_size`. *This is
the savings: the prefix is paid once at the 1h cold-write rate, then rebated on
every subsequent continuation within the hour.* Edge case: a continuation
issued after `cache_ttl` has elapsed must re-write at 1h again (not silently
degrade to 5m).

**AC-3 — Breakpoint count stays ≤ 4.**
For a tool-use loop of arbitrary depth (test at iter=1, iter=2, iter=3), the
final `messages` payload sent to the SDK must carry **at most one**
message-level `cache_control` marker (on the newest message), regardless of how
many continuations precede it. Combined with the 2 system+tools markers, total
breakpoints ≤ 4. *Verifies the stale-marker cleanup.* Failure mode this
prevents: a deep tool-use loop accumulating markers and tripping the API's
4-breakpoint cap.

**AC-4 — `mis_zoned` AND-corrects.**
`_compute_zones_payload` must return `mis_zoned=True` for a section that is
**both** in a zone that rides `system_blocks[0]` (`cached=True`) **and** in a
stable bucket (i.e., its name is in `STABLE_SECTION_NAMES`). A `state`-category
section that is `cached=True` but User-bucketed must return `mis_zoned=False`.
*Verifies the bucket AND-fix.* Edge case: every existing
`narrator_available_confrontations` / `trope_beat_directives` / `npc_roster`
fixture must flip from `mis_zoned=True` → `mis_zoned=False`.

**AC-5 — 1h-write cost is priced at the real rate.**
`compute_cost_usd` (or whatever the live entrypoint in `anthropic_cost.py` is)
must price a 1h cache-write at the real 2× input rate (Sonnet 4.6:
$6/Mtok input-1h-write input). The current 5m-equivalent rate ($3.75) is a
known under-count. *Verifies the cost panel matches Anthropic's bill.* Edge
case: 5m-write pricing is unchanged.

**AC-6 — Server gate stays green.**
`uv run ruff check .` and the full `pytest` suite pass. Specifically the
existing cache-attribution and 60-2 OTEL gates remain green; the new
regression tests run as part of the suite.

## Assumptions

- **Anthropic SDK ≥ 0.51** exposes `usage.cache_creation.ephemeral_1h_input_tokens`
  and `ephemeral_5m_input_tokens`. The existing per-TTL ledger (lines 164-174)
  depends on this; tests will too. If a CI environment pins an older SDK,
  surface it as a deviation — do not silently fall back to aggregate-only
  assertions.
- **The 1h extended-cache-ttl beta header continues to be required** for 1h
  markers. Tests must run against a path that includes the
  `anthropic-beta: extended-cache-ttl-2025-04-11` header (line 140-142). If the
  beta is GA'd before this story lands, the marker still works without the
  header — but absence of the header on a 1h marker request must continue to
  surface an error (no silent 5m fallback).
- **Existing 60-2 OTEL telemetry is the verification surface.** The per-iter
  `narrator.sdk.usage` log + LLM request span attributes already break out
  `5m`/`1h` writes. Tests assert on these — no new spans required.
- **60-3's measurement is reproducible.** The fix paragraph ("`cache_control`
  on last block of last message") was measured against the captured real iter-2
  body and produced `1h=20434` on write, `write=0` on the next read. Tests will
  validate the same effect against a synthetic but realistic
  `complete_with_tools` invocation.
- **`anthropic_cost.py` pricing constants are the only place 1h pricing is
  wrong.** If any other call site (GM-panel summary, OTEL cost rollups,
  per-iter ledger output) computes cost independently, it must be audited and
  reconciled in this story.
- **No Anthropic API-side changes are required.** The 1h cache and the
  `tool_use`/`tool_result` continuation protocol are both stable and
  documented; the fix is purely client-side message construction.

If any of these proves wrong during implementation, log a Design Deviation and
notify SM. Wrong assumptions about cache_control placement or SDK fields are
the most likely failure modes here.
