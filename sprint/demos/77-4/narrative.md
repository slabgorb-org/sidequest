# Narrative

## Problem Statement
**Problem:** The game engine had two competing ways to update quest and stakes information during a session — a legacy "update lane" built early in development, and a newer, structured system built in the three preceding stories. Having two paths for the same job creates hidden complexity: bugs could slip through undetected, the system's internal monitoring (the "GM panel lie-detector") could report inaccurate counts, and future developers would need to understand and maintain both pathways.

**Why it matters:** In a live multiplayer session, any misfired or silently-dropped quest update could mean a player's progress goes unrecorded, or the narrator makes decisions based on stale state. For a game designed to satisfy a career GM's expectation of a responsive, trustworthy narrator, invisible failure is unacceptable.

---

## What Changed
Imagine a building with two stairwells between floors — one brand new with handrails, lighting, and a fire-code certificate, and one old servants' staircase from the 1920s that still technically works but nobody has inspected in years. This story bricked up the old staircase.

Specifically:
- The old "quest_updates" pathway — a leftover from before the structured quest tools existed — was completely removed from the engine's data models and message-processing code.
- Eight files were touched: the pathway was removed from the game's session model, the narration result model, three extraction points in the orchestration layer, the WebSocket communication layer, and the escape-hatch tool that lets the narrator override world state directly.
- In place of a silent deletion, a **safety net** was installed: if a narrator ever accidentally sends a message using the old format, the engine catches it, translates it to the new format, records it properly, AND fires a loud monitoring alert — it never silently drops data, never crashes the session.
- The monitoring alert itself was then hardened mid-story when a code review found it was reporting inaccurate counts (claiming to forward items it had actually dropped). The final version correctly reports exactly what forwarded, what was skipped, and why.

---

## Why This Approach
Three principles drove the design:

1. **One mechanism, not two.** Two pathways for the same job means two things to test, two things to monitor, and two failure modes. Collapsing to one structured path makes the system easier to reason about and audit.

2. **No silent failures.** The team's core engineering rule: if something goes wrong, say so loudly. Rather than simply deleting the old path and risking silent data loss if any old-format messages ever arrive (from a cached narrator prompt, a test fixture, or a future integration), the safety net catches and translates them while emitting a visible alert to the GM monitoring panel.

3. **The lie-detector must not lie.** The monitoring span that reports "an old-format quest update was auto-forwarded" is specifically used by the GM panel to verify the narrator is doing real mechanical work. When the code review found it was over-counting forwarded items, the team immediately fixed it — a monitoring signal that misreports defeats the entire purpose of having monitoring.

---

## Before/After
| Dimension | Before (77-3 baseline) | After (77-4) |
|-----------|----------------------|--------------|
| **Quest update pathways** | Two: `quest_updates` legacy lane + `record_quest` typed tool | One: `record_quest`/`set_stakes` typed tools only |
| **`WorldStatePatch` model** | Had `quest_updates: dict[str, str] \| None` field | Field removed; `extra="forbid"` rejects stray payload at load time |
| **`NarrationTurnResult` model** | Had `quest_updates` field + 3 extraction sites | Field and all sites removed |
| **Stale narrator emissions** | Silently forwarded (or ignored) with no monitoring signal | Auto-forward guard: translates to `quest_log`, fires `quest.updates.legacy_emitted` span with forwarded count + skipped count, logs a WARNING — never silent, never crashes the turn |
| **`apply_world_patch` escape hatch** | `/active_stakes` was an allowed override path | Removed; narrator is directed to `set_stakes` (typed home); hard reject returns a recoverable error |
| **GM panel observability** | `quest_update` span could fire from two sources; counts were raw input (inflated) | `quest_update` span fires only from the trope handshake (independent subsystem); new `quest.updates.legacy_emitted` span reports only actually-forwarded items + `skipped_count` for drops |
| **Test coverage** | 2 legacy-field tests (exercised the deleted field) | 11 retirement tests: field excision (3), auto-forward correctness (1), span accuracy/hardening (3), atomicity guard (1), escape-hatch allowlist (1), behavioral guards (2) |
| **Suite health** | 8,897 passed, 20 failed (DB-env), 1,446 skipped | 8,901 passed (+3 hardening), same 20 DB-env failures, zero new regressions |
