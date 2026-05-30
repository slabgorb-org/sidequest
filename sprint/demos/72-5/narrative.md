# Narrative

## Problem Statement
**Problem:** When the game's narrator AI invents a new character — a shopkeeper, a guard, a bystander — that character was supposed to arrive on stage as a neutral stranger. The system's disposition model (the number that governs how an NPC feels about the players) had a default of **−20**, which the game reads as **hostile**. Monsters *should* spawn hostile — that's intentional. Ordinary people should not. Additionally, the GM dashboard had no way to *see* what disposition an NPC spawned with, so even if the fix were in place, there was no proof it was working.

**Why it matters:** SideQuest is built on the principle that NPCs earn their reactions through play. A world where every narrator-invented character walks in pre-loaded for a fight is not a living world — it's a shooting gallery. Jade and Sebastien's five-hour *Coyote Star* session surfaced this through a deep-dive audit: narrator-invented characters were arriving with unexplained hostility the game master couldn't verify or trace.

---

## What Changed
Think of each NPC as a new employee walking into their first day. Before this fix, the HR system would hand every new hire — whether a barista or a bouncer — the same "adversarial" badge with no explanation. The bouncer should get that badge (they're supposed to be intimidating). The barista shouldn't.

The investigation revealed something surprising: the underlying number was actually *already correct* for narrator-invented people. The `-20` default only fires when the game engine detects a creature (something with hit points, a threat level, or a monster ID). Narrator-invented people carry none of those markers, so they were already spawning neutral.

The *real* gap was that the GM dashboard had **no way to see this happening**. There was no readout, no log, no confirmation. The "unexplained hostility" the team saw in the playtest session could not be verified one way or the other.

What changed:
1. Both places in the code where an NPC materializes now emit a **telemetry signal** — a timestamped record that says "this NPC spawned with this disposition, for this reason."
2. The GM panel can now read that signal in real time, showing the spawn disposition and whether it was a neutral default or an explicit hostile assignment.
3. Three automated tests confirm the signals fire on real production code paths (not just in test environments).

---

## Why This Approach
The team initially expected to flip a number (change `-20` to `0` somewhere in the code). A careful root-cause trace showed the number was never wrong for the cases we care about — which is actually *good* news, because changing a default you don't understand can break things downstream.

The more defensible fix was to add observability first: make the behavior visible before changing it. That way:
- If the default *was* wrong somewhere, the new spans would expose it.
- If it was already right (which it was), the spans prove it — and give the team a permanent audit trail going forward.

This is the "GM panel as lie detector" principle: Claude the narrator is excellent at improvising convincing behavior with zero mechanical backing. The only way to catch it drifting is to log every subsystem decision. Spawn disposition is now logged.

---

## Before/After
| | Before (Story 72-5) | After (Story 72-5) |
|---|---|---|
| **Narrator-invented NPC spawns** | Disposition value correct (0/neutral) but invisible | Disposition value correct (0/neutral) **and** confirmed via `npc.spawn_disposition` span |
| **Monster/creature spawns** | Disposition value correct (−20/hostile) but invisible | Disposition value correct (−20/hostile) **and** confirmed via `npc.spawn_disposition` span with `provenance: default_creature_hostile` |
| **GM dashboard** | No NPC spawn events. Team had to read source code to check defaults. | `npc.spawn_disposition` event fires for every materialization: name, disposition, provenance, creature flag — visible in real time |
| **Verification method** | "Trust the code" | OTEL span assertion on production paths + three wiring tests |
| **Explicit hostile override** | Not expressible at narrator-invented seam (no `disposition` field on `NpcPatch`) | Same — correctly out of scope; explicit disposition lives in `world_materialization.py` |
| **Number of lines changed** | — | 4 files; **zero** disposition values altered |
| **Risk** | — | Additive telemetry only; span is outside the `return npc` control path and cannot block NPC materialization |
