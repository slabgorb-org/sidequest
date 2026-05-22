---
parent: context-epic-60.md
workflow: tdd
---

# Story 60-2: OTEL — per-system-block prompt-prefix digest + cache TTL in the Prompt-tab display

## Business Context

The narrator cache-write bug (epic 60) hid for weeks because the GM panel's Prompt
tab couldn't show it: today's Zone Breakdown is built from a **separate char/4
estimate path** (`orchestrator.py:2228` `prompt_assembled`), decoupled from the
real `system_blocks` sent to Anthropic and from the real API `cache_read/cache_write`
(`narrator.sdk.usage`). So a cached prefix can churn every turn while the display
reads "fine." This story builds the eyes: extend the **existing** Prompt-tab Zone
Breakdown so a GM (Sebastien, the mechanics-first player; Keith debugging cost) can
see, at a glance, which sections are cached, whether the cached block actually held
or drifted this turn, and what the API truly charged. OTEL is SideQuest's
lie-detector (CLAUDE.md) — and the lie-detector must not itself lie.

## Technical Guardrails

- **Extend, don't replace.** Build on `PromptTab.tsx` + the `prompt_assembled`
  watcher event. Do not stand up a parallel panel. (Don't-Reinvent.)
- **Reflect reality — single source of truth.** The cached/uncached partition shown
  MUST be derived from the *same* zone→`CacheableBlock` mapping the SDK path uses
  (`orchestrator.py:3199-3222`: stable=Primacy+Early `cache=True`; Valley `cache=False`;
  Late+Recency `cache=False`). Do not re-derive the boundary independently in the
  telemetry path or the UI — that's how the current estimate path drifted from
  reality. Ideally emit the partition + digest from where `system_blocks` are built.
- **Real usage, not estimates.** Join the SDK response numbers (`cache_read`,
  `cache_write`, `ephemeral_5m`/`ephemeral_1h`, `cost_usd`, and `cache_ttl`) onto the
  turn. `narration.turn.cache_ttl` already exists (see
  `tests/agents/test_cache_ttl_prefix_and_otel.py`) — reuse it; add the rest.
- **Account for drift.** Emit a content digest (e.g. `sha256(block.text)[:8]`) per
  cacheable block per turn. The display shows whether each cached block's digest
  changed vs the previous turn for the same session — a changed digest on a
  `cache=True` block is a wasted write and must be visually obvious.
- **Flag mis-zoned state.** Each section already carries a `category`
  (identity/guardrail/state/genre/format/soul/action — visible in the T5 screenshot).
  A section whose `category == "state"` that lands in a cached zone (Primacy/Early)
  is the bug signature — flag it explicitly.
- **No silent fallbacks** (CLAUDE.md): if the SDK usage for a turn isn't available
  (e.g. a non-SDK backend), show "n/a" loudly — never display a fabricated/estimated
  number styled as an actual.
- **Key files:** `agents/orchestrator.py` (2228-2306 emission, 3199-3222 blocks),
  `agents/anthropic_sdk_client.py` (real usage), `agents/prompt_framework/bucket.py`
  (zone→bucket / `STABLE_SECTION_NAMES`), `sidequest-ui/.../Dashboard/tabs/PromptTab.tsx`,
  `sidequest-ui/.../types/watcher.ts` (PromptFields type).
- **Repos:** **server + ui** (the story's `repos` field reads `server` from the epic
  default — SM must set up BOTH at session setup; this is a setup-time `REPOS=server,ui`).

## Scope Boundaries

**In scope:**
- Cache-boundary labeling of zones/sections in the existing Zone Breakdown.
- Per-block content digest + per-turn drift indicator, sourced from the real blocks.
- Joining real API cache usage (read/write, 5m/1h, cost, ttl) onto the displayed turn.
- Mis-zoned `state`-in-cached-zone flag.
- Server emission changes to carry the above on `prompt_assembled` (or a sibling
  event), + UI rendering in `PromptTab.tsx`.
- Tests: accuracy (partition matches real `system_blocks`), drift detection, wiring.

**Out of scope:**
- *Fixing* the mis-zoning (that is 60-4). 60-2 only makes it visible.
- Diagnosing drift-vs-TTL conclusively (that is 60-3, using these eyes).
- Snapshot slimming (ADR-110 / 57-5) and stable-prose promotion (ADR-112 / 57-3).
- Any change to what gets cached or the TTL value.

## AC Context

(Authoritative ACs live in the sprint YAML; expanded here.)

1. **Cache boundary visible.** Every zone/section row indicates cached (rides
   `system_blocks[0]`) vs uncached (Valley/Late/Recency) vs tools-array, derived from
   the same mapping the SDK path uses. Verifiable: Primacy+Early render as "cached",
   Valley/Late/Recency as "uncached".
2. **Real usage joined.** The selected turn shows actual `cache_read`, `cache_write`
   (with 5m/1h split), `cost_usd`, and `cache_ttl` from the SDK response — not char/4
   estimates. When unavailable, shown as explicit "n/a".
3. **Drift shown.** Each cacheable block displays a digest and a changed/unchanged
   indicator vs the prior turn of the same session. A `cache=True` block whose digest
   changed is flagged as a wasted write.
4. **Mis-zoned state flagged.** Any `state`-category section in Primacy/Early is
   visibly marked (e.g. warning chip). On current `tea_and_murder` data this fires for
   `narrator_available_confrontations`, `trope_beat_directives`, `npc_roster`.
5. **Accuracy test.** A test asserts the displayed cached/uncached partition (and the
   block digests) match the actual `system_blocks` handed to the SDK client on the same
   turn — the display cannot claim "stable" while the real prompt drifted.
6. **Wiring test.** New fields are emitted on the live `prompt_assembled` (or successor)
   path during a real narrator turn AND consumed by `PromptTab.tsx` — server→ui end to
   end (CLAUDE.md: every test suite needs a wiring test).

## Assumptions

- The `category` per section is already available in the emission (the T5 screenshot
  shows it). If not fully wired through `prompt_assembled`, plumbing it is in scope.
- Digest + cache-usage join is cheapest emitted server-side from the SDK path where
  both `system_blocks` and the API `usage` are in hand; the UI then renders. Dev may
  choose the seam, but the single-source-of-truth guardrail holds.
