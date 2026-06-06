---
story_id: "91-6"
jira_key: ""
epic: "91"
workflow: "trivial"
---
# Story 91-6: Gate narrator.cache.both_writes_fired WARNING on cache_read>0 (cold-start dual writes are unavoidable, not a pathology)

## Story Details
- **ID:** 91-6
- **Jira Key:** (none)
- **Workflow:** trivial
- **Repos:** sidequest-server
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/91-6-gate-both-writes-warning)

## Sm Assessment

**Story:** 91-6 — Gate `narrator.cache.both_writes_fired` WARNING on `cache_read>0` (1 pt, p3, chore, trivial workflow).

**Why now:** Epic 91 (Dark Spend) sibling stories are either blocked on 91-1 (in flight in another workspace) or carry merge-conflict risk against 91-1's SDK choke-point refactor in `llm_factory.py`. 91-6 is the only collision-free story: an isolated watcher-event change with no overlap in the SDK call path.

**Scope:** The `narrator.cache.both_writes_fired` WARNING currently fires on every cold-start dual write (1h stable prefix + 5m volatile both written on turn 1), which is unavoidable and expected — not a pathology. Gate the WARNING so it only fires when `cache_read > 0` (a genuine warm-session re-write of the stable prefix). Cold-start cases should drop to DEBUG/INFO.

**Acceptance criteria:**
1. Cold start (cache_read == 0) with dual writes → no WARNING (DEBUG/INFO acceptable).
2. Warm session (cache_read > 0) with dual writes → WARNING still fires.
3. Existing tests updated/added to cover both branches; wiring intact (event still emitted through the watcher path, observable on the GM dashboard).

**Context:** `sprint/context/context-story-91-6.md` (validated, exists).
**Jira:** none set for this story — claim explicitly skipped.
**Branch:** `feat/91-6-gate-both-writes-warning` in sidequest-server, created from develop per repos.yaml gitflow strategy.

**Routing:** trivial → phased → next agent `dev` (implement phase).

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-06T00:22:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T12:00:00Z | 2026-06-06T00:11:22Z | 12h 11m |
| implement | 2026-06-06T00:11:22Z | 2026-06-06T00:17:08Z | 5m 46s |
| review | 2026-06-06T00:17:08Z | 2026-06-06T00:22:33Z | 5m 25s |
| finish | 2026-06-06T00:22:33Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings during implementation. (A stale test-file module docstring describing the pre-91-6 unconditional WARN was found and fixed in-scope rather than logged.)

### Reviewer (code review)
- **Improvement** (non-blocking): Repo-wide pre-existing lint/format debt — 3 ruff I001 errors in untouched lull_escalation test files and 162 files failing `ruff format --check`, none introduced by this branch.
  Affects `sidequest-server` repo hygiene (a dedicated format/lint sweep chore would clear it; running it inside feature branches would bloat diffs).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Cold-start test asserts the absence of the WARNING log record but not the presence of the INFO log record; the logging-layer half of the downgrade is only negatively asserted.
  Affects `tests/agents/test_60_7_iter1_cache_marker.py` (add a one-line positive assertion on the INFO record in `test_both_writes_fired_cold_start_downgrades_to_info`).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. (Where the context offered options — DEBUG vs INFO for the cold case, downgrade vs fold-into-usage — the preferred option named in the context was taken: explicit downgrade at INFO with the same event name, severity="info". `cache_read_tokens` was added to the event payload in both branches so the GM panel can see which case fired; this is the `both_writes_fired` event payload, not the `narrator.sdk.usage` line format owned by 91-1.)
  → ✓ ACCEPTED by Reviewer: the context explicitly named "explicit downgrade" as preferred (context-story-91-6.md, Technical Guardrails); the `cache_read_tokens` payload addition is the gating field itself — surfacing it to the GM panel is the OTEL Observability Principle applied, and it does not touch the 91-1-owned `narrator.sdk.usage` shape (verified: usage event fields at anthropic_sdk_client.py:501-513 unchanged in diff).

### Reviewer (audit)
- No undocumented deviations found. The diff is exactly the gating predicate + severity split + payload field + test reconciliation the spec described; cache tiers, marker placement, and cost math are untouched (verified against full diff — only the both_writes block and tests changed).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/agents/anthropic_sdk_client.py` — gated the `narrator.cache.both_writes_fired` emit on `cache_read > 0`: warm pathology (cache_read > 0 + dual write) keeps `logger.warning` + watcher `severity="warn"`; cold start (cache_read == 0) downgrades to `logger.info` + watcher `severity="info"`. Added `cache_read_tokens` to the event payload. No cache behavior, marker placement, tier split, or cost math touched.
- `tests/agents/test_60_7_iter1_cache_marker.py` — warm-warn test updated (response now carries `cache_read=11_988`, asserts `cache_read_tokens` field); new `test_both_writes_fired_cold_start_downgrades_to_info` (AC-1: zero warn events, zero `logger.warning` records, exactly one info event); per-iter tool-loop test made warm-offending (`_tool_use` gained a `cache_read` param) and filters on warn severity; module docstring reconciled.

**Tests:** 11/11 targeted file passing; full `tests/agents/` suite 1769 passed / 1 skipped (expected) / 0 failed. Ruff lint + format clean.
**Branch:** `feat/91-6-gate-both-writes-warning` (pushed, commit `5d2a96f8`)

**AC verification:**
1. Cold start (cache_read == 0) dual write → no WARN event, no `logger.warning`; INFO observation emitted. ✅ (new test)
2. Warm (cache_read > 0) dual write → warn-severity event + `logger.warning` still fire. ✅ (updated tests)
3. Existing tests reconciled, one test per case, assertions on emitted watcher events / log records (no source-text checks). ✅

**Handoff:** To review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (pre-existing repo lint/format debt in untouched files noted) | N/A — branch-owned files clean; debt deferred as non-blocking note |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 2 (LOW), dismissed 2, deferred 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | confirmed 1 (LOW) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (16 rules, 47 instances, 0 violations) | N/A |

**All received:** Yes (4 enabled returned, 5 disabled via settings)
**Total findings:** 3 confirmed (all LOW, non-blocking), 2 dismissed (with rationale), 2 deferred

**Finding decisions in detail:**
- [TEST] **Dismissed** — "caplog.at_level scope doesn't cover the asyncio.sleep" (medium): the `logger.warning`/`logger.info` calls are inline in the body of `complete_with_tools` (anthropic_sdk_client.py:549/565), synchronous within the awaited coroutine — they fire inside the `with` block. The sleep is only needed for watcher socket fan-out, which the test asserts separately via `sock.events`. Additionally caplog's handler persists for the whole test; `at_level` only adjusts the threshold, and WARNING records are captured at the default threshold regardless.
- [TEST] **Dismissed** — "tool-loop test won't catch a bug emitting both info and warn for the same iter" (low): the production branches are a strict `if cache_read > 0 / else` (anthropic_sdk_client.py:548-578) — emitting both for one iter is structurally impossible; the hypothesized bug cannot exist without rewriting the branch structure the other tests pin.
- [TEST] **Confirmed LOW (non-blocking)** — cold-start test asserts no WARNING log record but never asserts the INFO log record fired; the logging-layer downgrade is only half-asserted (the watcher-layer downgrade IS fully asserted via `info_events == 1`). One-line hardening for a follow-up.
- [TEST] **Confirmed LOW (non-blocking)** — no boundary test at `cache_read == 1`; warm tests use 9_000/11_988. A threshold drift (e.g. `> 100`) would not be caught. Parametrization nicety, non-blocking.
- [TEST] **Deferred** — tool-loop iter=2 is cold-clean (cache_read=0, 1h-only), not warm-clean; a warm-clean iter shape is untested in the loop path. Outer guard (`5m > 0 and 1h > 0`) makes both shapes inert identically; marginal value.
- [TEST] **Deferred** — negative suite lacks the healthy-warm shape (cache_read>0, 5m>0, 1h=0). Same outer-guard reasoning: that shape cannot reach the gate at all (1h == 0 fails the conjunction), so the case is structurally covered by case (c) already.
- [DOC] **Confirmed LOW (non-blocking)** — cold `logger.info` format omits `cache_read` while the comment frames the branch as a pure severity downgrade; harmless (cache_read is definitionally 0 in that branch, and the watcher payload carries `cache_read_tokens=0`), but either the format string or the comment could be made symmetric.

### Rule Compliance

Rules sources read: `.pennyfarthing/gates/lang-review/python.md` (13 checks), CLAUDE.md server + orchestrator (No Silent Fallbacks, No Stubbing, OTEL Observability Principle, No Source-Text Wiring Tests, wiring rules), SOUL.md (no code-level rules applicable to this diff). Rule-checker swept all 16 rules across 47 instances; I spot-verified the load-bearing ones:

- **No Silent Fallbacks** — COMPLIANT. Both branches of the new conditional are explicit; the cold path emits (info), it does not swallow. No alternative-path defaulting introduced (anthropic_sdk_client.py:548-578).
- **OTEL Observability Principle** — COMPLIANT. Cold path keeps both the log line (`logger.info`, :565) and the watcher event (`_watcher_publish_event` severity="info", :573-578) — downgrade, not deletion. Payload gains `cache_read_tokens` in both branches, improving GM-panel legibility.
- **No Source-Text Wiring Tests** — COMPLIANT. New/updated tests assert on runtime log records (`r.getMessage()`/`r.levelno`) and watcher socket events; no `read_text()`/regex-on-source anywhere in the diff.
- **Python #4 logging correctness** — COMPLIANT. Lazy `%`-formatting in both log calls; info for expected behavior, warning for pathology — exactly the level-classification the checklist requires; no sensitive data (token counts + model id only).
- **Python #3 type annotations** — COMPLIANT. `both_writes_fields: dict[str, Any]` annotated; test helpers fully typed including the new `cache_read: int = 0` param.
- **Python #6 test quality** — COMPLIANT. All new assertions check specific values/counts; no vacuous asserts; no skips.
- **Python #2/5/7/8/9/10/11/12** — no instances introduced by this diff (no defaults, paths, resources, deserialization, new awaits, imports beyond stdlib `logging`, boundaries, or deps). Verified by rule-checker, spot-confirmed in diff.

### Devil's Advocate

Let me argue this code is broken. First attack: the gate conflates "cache_read > 0" with "warm pathology," but `cache_read_input_tokens` aggregates reads from BOTH tiers. Suppose the 1h stable prefix legitimately expired (2h idle session) while the 5m tail somehow read back — then cache_read > 0 with a legitimate 1h re-mint, and we false-positive a WARN. Does that scenario exist? No: a 5m read implies activity within the last 5 minutes, and Anthropic cache reads refresh TTL, so the 1h prefix cannot have expired while the 5m tail stayed alive. The conjunction is sound. Second attack: the inverse — after any idle gap > 1h, everything expires, cache_read == 0, and a genuine churn bug on the very first turn back is masked as "cold start, info." True — but that is exactly one masked observation per cold start, and the next warm turn (turn 2) exposes the churn at WARN. The tripwire loses at most one turn of latency, which is the explicit, documented trade the story makes. Third attack: the gate could hide a regression where iter=1 of EVERY turn dual-writes on a fresh prefix — but that shape has cache_read > 0 from iter-2-of-prior-turn reads... no, within the same session every turn after the first reads the prefix, so steady-state churn still WARNs. Fourth attack: severity="info" might not be a value the watcher transport/GM panel accepts — refuted: the sibling `narrator.sdk.usage` event ships severity="info" through the identical `_watcher_publish_event` path (:501-513). Fifth attack: the cold-start INFO event now fires ~7x/day where WARN did — could that flood the panel? No: same emit frequency as before, lower severity; the volume is unchanged, only the alarm level. Conclusion: the design holds; the residual exposures (one-turn cold-start masking latency, missing INFO-log positive assertion, untested cache_read==1 boundary) are noted as LOW findings, none load-bearing.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** SDK `response.usage` → `cache_read`/`cache_write_5m`/`cache_write_1h` coerced to int via `int(getattr(...))` (anthropic_sdk_client.py:421-438, safe on missing attrs) → dual-write predicate (:548) → branch on `cache_read > 0` → log line + `_watcher_publish_event` → `watcher_hub.publish_event` → WS subscribers (GM panel). Safe because all inputs are int-coerced with defaults before the gate; no user-controlled strings flow into the event beyond `response.model` (SDK-provided).

**Pattern observed:** the info-severity downgrade mirrors the sibling `narrator.sdk.usage` info emit (anthropic_sdk_client.py:501-513) — same component, same transport, consistent severity taxonomy. Good pattern reuse.

**Error handling:** no new failure modes — the block is pure conditional logic on already-coerced ints; `_watcher_publish_event` is the established fire-and-forget path; a missing `cache_creation` on old SDKs yields 0/0 writes and the gate is never reached (verified :428-438).

**Wiring:** [VERIFIED] event reaches subscribers end-to-end — tests drive the real `complete_with_tools` against the bound `watcher_hub` and assert arrival on a subscribed `FakeSocket` (test_60_7_iter1_cache_marker.py, cold + warm + tool-loop cases). Complies with Every-Test-Suite-Needs-a-Wiring-Test; not a unit-only suite.

**Observations (≥5):**
1. [VERIFIED] Warm pathology stays loud — anthropic_sdk_client.py:549-563 fires `logger.warning` + severity="warn" iff `cache_read > 0` within the dual-write guard; complies with story AC-2 and the OTEL principle (no rule requires more).
2. [VERIFIED] Cold path does not go dark — :565-578 emits info log + info watcher event with full field set including `cache_read_tokens=0`; complies with No Silent Fallbacks and the context's "prefer downgrade over deletion" guardrail.
3. [RULE] Rule-checker: 16 rules, 47 instances, zero violations — including the three CLAUDE.md criticals applicable here.
4. [TEST] LOW — missing positive assertion on the cold-path INFO log record (watcher-layer is fully asserted; logging-layer only negatively). Non-blocking.
5. [TEST] LOW — `cache_read == 1` boundary unexercised; threshold drift would survive the suite. Non-blocking.
6. [DOC] LOW — cold `logger.info` format omits `cache_read` (always 0 there); comment/format symmetry nicety. Non-blocking.
7. [EDGE] Cold-start masking latency of exactly one turn (first turn after full TTL expiry) is inherent to the design and accepted by the story; steady-state churn still WARNs from turn 2. No unhandled boundary found beyond the LOW items above.
8. [SILENT] No swallowed errors introduced — both branches emit; no try/except added. (Specialist disabled; assessed directly from the diff.)
9. [TYPE] / [SEC] / [SIMPLE] — specialists disabled; my own pass: types annotated (`dict[str, Any]`, typed test helpers), no security surface (no user input, no secrets in logs — token counts and model id only), no unnecessary complexity (the if/else is the minimal expression of the spec; no abstraction added).

**Severity table:** no Critical, no High. 3× LOW (listed above) — none block.

**Handoff:** To SM for finish-story