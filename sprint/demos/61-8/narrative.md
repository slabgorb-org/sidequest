# 61-8

## Problem

**Problem:** Small but real gaps remained after four previous cleanup stories shipped — a monitoring alarm that logged warnings nobody could see, an NPC identity register that silently missed entries for characters loaded from old save files, a constant with a misleading name, and a cluster of diagnostic counters that couldn't distinguish between two different failure modes. **Why it matters:** Each gap was harmless in isolation, but together they reduced the team's ability to detect the next expensive runaway before it billed hundreds of dollars — the exact scenario that triggered Epic 61 in the first place.

---

## What Changed

Think of the game engine as a kitchen with a complicated prep line. Previous stories fixed the big problems: the overstuffed grocery bags going into every order, the missing price-cap alarm, and the inconsistent way cooks decided which ingredients were "in the room." This story handled the punch list left on the whiteboard after those fixes shipped.

Specifically:

- **The warning nobody could see** — When a key lookup table (the "lore store") goes missing from production, the engine already logs a warning. The problem: that warning goes into a text log file, not the operator dashboard. Now it also fires a real-time dashboard event that operators can actually see.
- **The ghost NPC problem** — Characters loaded from save files made before a June fix could disappear from the engine's identity register during scene transitions. The engine would then forget who they were and improvise a replacement name. Fixed: every character gets a register entry on load, old saves included.
- **The misleading constant name** — A variable called `SOFT_PROMPT_BUDGET_BYTES` sounded like a gentle suggestion. It wasn't — it triggers a hard refusal when a prompt is too large. Renamed to `PROMPT_BUDGET_BYTES_HARD` to match reality. The word "soft" was a lie baked into the codebase since the canary shipped.
- **Diagnostic counters that blurred two failure modes** — The engine tracks how many NPCs get filtered out of the snapshot each turn. Before: all filtered NPCs counted as one bucket. Now: NPCs filtered because they're legitimately off-stage count separately from NPCs filtered because their names were malformed. Operators can now tell the difference.
- **Five type errors in the session helpers** — Static analysis flagged these pre-existing issues. Three were fixed structurally (proper type narrowing), two got annotated with accurate explanations of why a global fix is a bigger project.
- **Eight new regression tests** — Added tests for empty encounter actor lists, a PC with no current room, the new counters, and the dashboard-event wiring.

---

## Why This Approach

These fixes were bundled rather than split into individual stories because each item is small, mechanical, and independently testable — no shared state, no shared risk. Splitting them would have generated more ceremony (session files, branch setup, PR overhead) than the fixes themselves warranted. The downshifted workflow (trivial rather than test-driven development) is the right tool for a "clean up the whiteboard" story: one implementer pass, one adversarial review, done.

The three-round review cycle (rejected twice, approved on the third pass) is the process working as designed. Round one surfaced three real bugs via a nine-specialist fan-out. Round two fixed all eleven findings, introduced one tiny lint regression. Round three cleared it in one line. That's a tight feedback loop, not a red flag.

---
