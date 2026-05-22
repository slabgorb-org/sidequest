# Epic 60: Narrator Token & Cost Budget — Cache-Write Efficiency

## Overview

Continuation of archived epic 57 (Narrator Prompt Token Reduction). A 2026-05-21
`tea_and_murder/glenross` playtest surfaced ~$0.046/call of wasted `cache_write`.
The original framing blamed the `game_state` snapshot; reading the code (and the
OTEL Prompt zone-breakdown at T5 on 2026-05-22) **disproved that** and pinned the
real cause. This epic builds the observability to *see* the cost, confirms the
root cause with those eyes, then fixes it — in that order (you cannot reposition
what you cannot see drift).

**Priority:** P2
**Repo:** server (60-2 also touches ui)
**Stories:** 3 active (60-2, 60-3, 60-4), split from the original 60-1 (status: split)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **ADR-101 Anthropic SDK Narrator Backend** (`docs/adr/101-*.md`) | Phase D three-zone cacheable layout; `system_blocks[0]` cache marker; four-region cache amendment |
| **ADR-112 Genre Prose Cache Promotion** (`docs/adr/112-*.md`) | Mutability rubric: always-fire+static promotes to Stable; **conditional/volatile must NOT** ride the cached zone (combat/chase) |
| **ADR-110 Snapshot Slimming** (`docs/adr/110-*.md`) | Snapshot size — *complementary, not this epic* |
| **ADR-090 / ADR-103 OTEL** | Watcher events + GM panel; `prompt_assembled` event powering the Prompt tab |
| **Archived epic 57** (`sprint/archive/epic-57.yaml`) | 57-3 promoted static prose to Early; that re-zoning is adjacent to the bug |

## Background

### The corrected root cause

The narrator prompt is assembled into Anthropic `system` blocks. Per ADR-101
Phase D (`orchestrator.py:3199-3222`):

- **`system_blocks[0]` = Primacy + Early zones, `cache=True`** — one `cache_control`
  marker at its end. ~11.7k tokens.
- `system_blocks[1]` = Valley, `cache=False`. Contains `game_state` (703 tok) and
  `world_context` — **uncached, innocent.**
- `system_blocks[2]` = Late + Recency, `cache=False`.
- tools array — byte-stable ~11k, separately cache-marked → healthy `cache_read`.

Anthropic caches the longest matching prefix up to a breakpoint. Block 0 has ONE
marker at its end, so the **entire 11.7k block must be byte-identical** to hit the
cache. The 2026-05-22 OTEL zone-breakdown shows three `state`-category
(volatile) sections sitting in the **Early** zone — therefore inside cached block 0:

- `narrator_available_confrontations` (~56–80 tok) — changes as confrontations open/close
- `trope_beat_directives` (~20 tok) — changes per beat
- `npc_roster` (~80 tok) — changes as NPCs enter/leave the scene

Any per-turn change to these invalidates the whole cached prefix → block 0
re-writes every turn (`cache_write≈12281`), while the byte-stable tools array
reads fine (`cache_read≈11168`). The snapshot was never the cost.

### Why observability comes first

Today's Prompt-tab display is built from a **separate** per-zone, char/4
*estimate* path (`orchestrator.py:2228` `prompt_assembled`), decoupled from the
real `system_blocks` and from the real API `cache_read/cache_write`
(`narrator.sdk.usage`). It can show "looks fine" while the cached prefix churns.
The bug hid for exactly this reason. So: build the eyes (60-2), confirm with them
(60-3), then fix (60-4).

## Technical Architecture

**Three-story arc:**

- **60-2 (OTEL eyes — START HERE).** Extend the existing Prompt-tab Zone Breakdown
  so it makes caching legible: mark the cache boundary (which sections ride cached
  block 0 vs uncached blocks vs tools), join the **real** API `cache_read/cache_write`
  (not estimates), emit a per-block content **digest** and show drift vs the prior
  turn, and flag `state`-category sections that landed in a cached zone. The display
  must be sourced from the **actual assembled blocks** sent to Anthropic — no
  divergent recomputation. Repos: **server + ui**.
- **60-3 (Diagnose/confirm — spike).** Using 60-2's eyes, run an instrumented
  multi-turn `tea_and_murder` session and confirm the churn is the three mis-zoned
  `state` sections in Early (drift), not 5m-TTL expiry across slow cadence. Produce
  the finding that scopes 60-4. Repos: server.
- **60-4 (Fix).** Re-zone the offending `state` sections out of the cached zone
  (Early → Valley/uncached) so `system_blocks[0]` is byte-stable; also audit the
  conditional `genre_combat_voice`/`genre_chase_voice` (ADR-112 says conditionals
  must not ride Stable). Success: steady-state `cache_write≈0`, `cache_read>0`,
  per-call cost down ~40-50%, verified in the 60-2 display. Repos: server.

**Key files:** `agents/orchestrator.py` (zone registration 1320-1460; `system_blocks`
assembly 3199-3222; `prompt_assembled` emission 2228-2306), `agents/anthropic_sdk_client.py`
(`narrator.sdk.usage`, real cache usage), `agents/prompt_framework/bucket.py`
(`STABLE_SECTION_NAMES`, zone→bucket), `sidequest-ui/src/components/Dashboard/tabs/PromptTab.tsx`.

## Cross-Epic Dependencies

**Depends on:** None hard. ADR-101 Phase D caching is live.

**Depended on by:** None.

**Related (not blocking):** Archived epic 57 (57-3 promoted prose into Early — the
adjacent re-zoning; 57-5 snapshot slimming — orthogonal size lever). 60-4 should
coordinate so re-zoning state OUT of Early doesn't fight 57-3's promotion of static
prose INTO Early — they are compatible (static stays, volatile leaves).
