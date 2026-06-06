---
parent: context-epic-91.md
workflow: tdd
---

# Story 91-3: Intent Router cache repair + fail-loud floor guard (combined prefix ≥4096 or raise at build; live-gated test: cache_creation>0 turn 1, cache_read>0 turn 2; DESCOPE if local routing epic lands first)

## Business Context

The Intent Router (ADR-113, `_IntentRouterLlm.emit_tool`) fires a Haiku 4.5 call **once per
player turn** carrying a ~4,730-token static tools+system prefix. The cost forensics on
2026-06-05 (pingpong **[COST-1]**, see `context-epic-91.md` Background) found that prefix
re-billing in full every turn: Admin API ground truth shows `cache_creation = 0` **and**
`cache_read = 0` for Haiku 4.5 org-wide, every day. The cache is **dead**. Warm reads would
cut Haiku spend ~**75%** (~**$2.5/day** at current volume) — a Haiku cache read is billed at
0.1× the base input rate, so amortizing a 4.7k-token prefix across a multi-turn session is
the single largest available Haiku saving.

> **DESCOPE GATE — READ FIRST.** This story is **independent (no deps)** but is **DESCOPED if
> epic 92 story 92-2 (local classification routing) lands first.** A local router runs the
> classification on a local model — it has *no Anthropic cache floor and no Haiku cache bill*,
> so repairing the Anthropic-side cache becomes dead work. Before starting: check whether 92-2
> is merged to `origin/develop`. If it is, **DESCOPE this story and record the descope
> decision in the session** (`pf` status note + a line in the story session file) — **do not
> silently drop it**. The epic's sequencing block (`context-epic-91.md` §Sequencing) flags
> this explicitly. Also coordinate with **82-10** (router prompt slimming, backlog): slimming
> the combined prefix below 4,096 tokens makes Anthropic-side caching *impossible* and the
> floor guard this story installs would correctly refuse it — so if 91-3 lands, 82-10 must keep
> the prefix above the floor; if the router goes local, 82-10 may slim freely.

This serves Keith-as-operator (per-turn unit economics, P1) and indirectly the playgroup: the
1h TTL exists specifically because of the **submit-and-wait MP turn cadence** — a slow typist
(Alex) can space router calls minutes apart, and a 5m prefix would expire between turns. The
cache repair must not regress that.

## Technical Guardrails

### Root-cause hypotheses (ranked — diagnose before fixing)

The fix marker landed **today** (commit `2f0de99b`, "cache the Intent Router Haiku system
prompt (0% → warm)", 2026-06-05, same day as the forensics), so the zero-cache evidence in the
epic is from a window that **mostly predates the marker**. The first job is to confirm the
marker now actually warms the cache against the live API, then close the remaining gap. Ranked
hypotheses from reading the code:

1. **(TOP) Missing `cache_control` on the tools array — single-block marker doesn't extend the
   prefix the way the narrator's does.** The *working* narrator (`anthropic_sdk_client.py`)
   marks **two** blocks: the last tool entry (`_build_tools_array`, line 1235 —
   `out[-1]["cache_control"] = {"type": "ephemeral", "ttl": self.cache_ttl}`) **and** the
   system block (`_build_system_array`, line 1207). The Intent Router's `emit_tool`
   (`llm_factory.py` lines 229–252) marks **only** the system block:

   ```python
   system=[{"type": "text", "text": system,
            "cache_control": {"type": "ephemeral", "ttl": _INTENT_ROUTER_CACHE_TTL}}],
   ...
   tools=[{"name": tool_name, "description": tool_description, "input_schema": tool_schema}],
   #      ^^^ NO cache_control marker on the tools array
   ```

   The in-code comment (lines 137–145, 218–227) asserts "one marker on the system block caches
   the whole tools+system prefix (canonical order tools → system → messages)." Verify this
   claim against the live API. Anthropic evaluates breakpoints in canonical order and a system
   marker *should* cache the earlier tools too — but the narrator's empirically-confirmed path
   marks **both**, and the comment's "system ALONE is sub-floor; the margin is the tool schema"
   means the cacheable content lives largely in a block that carries **no marker of its own**.
   If a single system-block breakpoint does not warm the tools, this is the defect. **The
   minimal, behavior-matching fix is to mirror the narrator: mark the last tool entry too.**

2. **Beta header / marker present but the prefix is genuinely sub-floor in production.** The
   ~4,730-tok figure is an estimate; verify with `count_tokens` (see Assumptions). Measured
   today: system 9,661 chars ≈ 3,019 tok, schema 5,628 chars ≈ 1,759 tok, combined ≈ **4,778
   tok** (above floor). So a *shrunk-below-floor* prompt is **unlikely** to be the cause — the
   char tripwire is green — but the live `count_tokens` floor check is the only authority.

3. **TTL expiry between turns** — if real cadence exceeds 1h the prefix legitimately re-mints
   every turn (cache_creation>0, cache_read≈0). The 1h TTL is already the longest available
   and was chosen for exactly the slow-typist cadence; this would be a *volume*/cadence finding
   (91-2 territory), not a marker defect. Distinguish it from hypothesis 1 by watching whether
   `cache_creation` ever goes non-zero at all (it currently does not — pointing at 1, not 3).

4. **Header missing in the prod path** — ruled out by reading: `emit_tool` sends
   `extra_headers={"anthropic-beta": _EXTENDED_CACHE_TTL_BETA}` (line 251), and
   `_EXTENDED_CACHE_TTL_BETA` is imported from `anthropic_sdk_client` (the narrator's proven
   1h string `"extended-cache-ttl-2025-04-11"`, not a drifted copy). Header is present.

### Fail-loud floor guard contract (No Silent Fallbacks)

Below Haiku 4.5's **4,096-token cacheable floor**, a `cache_control` marker is *accepted by the
API and silently never caches* — a No-Silent-Fallbacks violation baked into API behavior. The
guard must **raise at client-BUILD time** (i.e. when `_IntentRouterLlm` is constructed / first
emits, before any production turn ships) if the combined cacheable prefix is `< 4096` tokens.
Never ship a marker that silently no-ops.

- **What to count:** the **combined** cacheable prefix = tools schema (name + description +
  `input_schema`) **+** the system block, in canonical cache order **tools → system →
  messages**. NOT the system block in isolation (the system prompt alone ≈ 3,019 tok is
  *below* floor; the margin comes entirely from bundling the DispatchPackage schema). The
  authoritative count is `Anthropic().messages.count_tokens(model=_HAIKU_MODEL, system=[...],
  tools=[...], messages=[{"role":"user","content":"x"}])` — char-length is only a coarse early
  warning.
- **Where it fires:** at build/first-call time, loud, with a message naming the measured token
  count and the 4,096 floor — mirroring the existing fail-loud `ANTHROPIC_API_KEY` check in
  `_IntentRouterLlm.__init__` (lines 192–198). It must be reachable from the production path,
  not just a test.

### Live-gated test pattern

Real-API cache assertions must be **gated like the composer's Gymnopedie smoke test** — they
make real Anthropic calls and **must not run in default CI**. The repo already has the exact
pattern in `tests/agents/test_haiku_cache_control.py::test_intent_router_prefix_token_floor_live`
(lines 246–286): gated on `SIDEQUEST_VERIFY_HAIKU_CACHE_FLOOR`, `pytest.skip` when the flag is
unset, and **fail-loud** (not skip) if the flag is set but `ANTHROPIC_API_KEY` is missing. The
new two-call cache test follows this gate.

The **two-call test** (the core acceptance proof) must, against the live API:
1. **Turn 1 (cold):** `cache_creation_input_tokens > 0` (the prefix was *minted*).
2. **Turn 2 (warm), identical prefix:** `cache_read_input_tokens > 0` (the prefix *read back*).

These are the `response.usage` fields the Admin API rolls up as `cache_creation` / `cache_read`.

### What already exists (reuse, don't reinvent)

- `_record_haiku_usage_on_span` (`llm_factory.py` lines 150–168) stamps
  `llm.cached_input_read_tokens` (from `cache_read_input_tokens`) and
  `llm.cached_input_write_tokens` (from `cache_creation_input_tokens`) onto the `llm.request`
  span — the comment names `cached_input_read_tokens` the **"lie-detector field."** Assert on it.
- `test_haiku_cache_control.py` already pins: system is a content-block list with the 1h marker,
  the beta header is sent, the span carries cache-read tokens, the aside stays a bare string
  (sub-floor), and a char tripwire + the gated live token-floor check. Extend this file; do not
  fork it. The **gap** these tests leave is exactly why production was dead: every assertion is
  on the payload the adapter *builds* (mocked SDK) — none prove the *live* cache engages, and
  none cover the **tools-array marker** (hypothesis 1).

## Scope Boundaries

**In scope:**
- Root-cause the zero-cache (run hypothesis 1 first: live two-call check with the current
  marker, then add the tools-array marker if a system-only breakpoint doesn't warm tools).
- Fix the marker/header/prefix so `cache_creation>0` then `cache_read>0` against the live API.
- **Build-time fail-loud floor guard** (combined prefix < 4096 tok → raise; never ship a
  silent-no-op marker).
- **Live-gated two-call test** (`cache_creation>0` turn 1, `cache_read>0` turn 2), gated like
  the Gymnopedie/`SIDEQUEST_VERIFY_HAIKU_CACHE_FLOOR` smoke tests, **not** in default CI.
- **OTEL assertion** on `llm.cached_input_read_tokens` (the existing lie-detector field via
  `_record_haiku_usage_on_span`) — proves the warm read is observable on the GM panel.

**Out of scope:**
- **Prompt slimming (82-10)** — explicit design tension: slimming the router prompt below 4,096
  tokens makes Anthropic-side caching *impossible*, and this story's floor guard would correctly
  refuse it. **Coordinate**: if 91-3 lands, 82-10 must keep the combined prefix above floor.
- **Local routing (epic 92 / 92-2)** — the descope trigger for this whole story.
- **The 8×/turn volume anomaly (91-2)** — caching repairs cost-per-call, not call count. A
  cadence/expiry finding that surfaces here is *evidence for* 91-2, handed off, not fixed here.
- **Universal usage instrumentation / choke point (91-1)** — 91-3 is independent of it; do not
  refactor `_IntentRouterLlm` into the choke point as part of this story.
- The **aside** adapter (`_AsideLlm`) — sub-floor (~361 tok) and correctly stays a bare string;
  leave it uncached (a marker there would be a silent no-op).

## AC Context

For each acceptance criterion, the **exact observable** that proves it:

- **Cache writes on cold turn:** `response.usage.cache_creation_input_tokens > 0` on turn 1
  (Admin API: `cache_creation` column non-zero for Haiku 4.5). Mirrored onto the span as
  `llm.cached_input_write_tokens`.
- **Cache reads on warm turn:** `response.usage.cache_read_input_tokens > 0` on turn 2 with the
  identical prefix (Admin API: `cache_read` non-zero). Mirrored as `llm.cached_input_read_tokens`
  — the lie-detector field the GM panel watches go non-zero on turn 2+.
- **Floor guard fires loud below floor:** constructing/invoking the adapter with a sub-4,096-tok
  combined prefix raises at build time with a message naming the measured count and the floor —
  no marker shipped that silently no-ops.
- **Live token floor cleared:** `count_tokens(system + tools)` ≥ 4,096 (the existing
  `test_intent_router_prefix_token_floor_live`, run under the gate).

**Edge cases:**
- **1h TTL expiry between turns** — the slow-typist MP cadence (why `_INTENT_ROUTER_CACHE_TTL =
  "1h"`, not 5m) means turns can be minutes apart; a turn-pair spaced > 1h would legitimately
  show `cache_creation>0, cache_read≈0` (re-mint, not a defect). The live two-call test must run
  turns back-to-back so it tests the marker, not the clock.
- **Prefix changes invalidating the cache mid-session** — the cached prefix is *static*
  (`_SYSTEM_PROMPT` + `_dispatch_tool_schema`); the per-turn action goes in the **user** message
  (`_build_user_prompt`), which is past the breakpoint and is *not* cached. Confirm the user
  prompt carries no marker, so each turn's volatile action doesn't poison the static prefix.
  Any future schema/prompt edit silently shrinks or shifts the prefix → re-run the gated
  `count_tokens` floor check (the char tripwire is the coarse early warning that forces it).

## Assumptions

- **`ANTHROPIC_API_KEY` is available** in the dev/CI-gated environment for the live two-call and
  `count_tokens` floor tests. When the gate flag is set but the key is missing, the test
  **fails loud** (does not skip) — matching the existing live floor test (lines 259–260).
- **The combined prefix today totals ~4,730 tok — VERIFY.** Measured this story: system 9,661
  chars ≈ 3,019 tok + schema 5,628 chars ≈ 1,759 tok = **~4,778 tok** (char tripwire green at
  15,289 ≥ 13,500). If a live `count_tokens` returns **< 4,096**, that *is* the root cause
  (hypothesis 2) and the fix is restoring prefix size (and coordinating 82-10), not the marker.
  Above floor → root cause is the marker/tools-array gap (hypothesis 1).
- **The 1h beta string is correct and shared** — `_EXTENDED_CACHE_TTL_BETA` is imported from the
  narrator's proven path, so a drifted header is not the cause.
- **The descope check has been run** — 92-2's merge status against `origin/develop` was checked
  before any code was written, and the outcome (proceed / descope) recorded in the session.
