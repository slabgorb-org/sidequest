# 49-3

## Problem

**Problem:** During the May 11th Glenross playtest, the game's narrator kept describing new rooms in its prose — "The Bee Garden," "Front Parlour," "The Study" — but never told the underlying game engine it had moved. The engine's official record of where Ziggy was standing said `the_manse` for five full turns, even while the narrator was writing vivid descriptions of entirely different spaces. The two systems were running on separate tracks.

**Why it matters:** The GM observation panel — the dashboard Sebastien uses to watch every mechanical decision the engine makes — was showing the wrong location for the entire first half of the session. Any subsystem that uses party location (room-specific events, NPC triggers, scene transitions) would have been working off stale data. More broadly, this is the exact failure mode the architecture was designed to prevent: the AI narrator improvising facts that the engine doesn't know about. When the map in the engine's head doesn't match the room in the narrator's prose, the game is silently lying to itself.

---

## What Changed

Imagine the game engine as a secretary who keeps a ledger. The narrator writes beautiful scene descriptions on paper — "The party enters **The Front Parlour**" — but the secretary only updates the ledger when the narrator fills out the official move form. Previously, if the narrator forgot the form, the ledger stayed wrong and nobody noticed.

This fix gives the secretary a new habit: before filing any turn, she glances at the top of the narrator's prose. If it starts with a bold room title — `**The Front Parlour**` — and the ledger says the party is somewhere else, she:

1. Quietly corrects the ledger to match the prose title
2. Writes a loud warning in the audit log: *"I had to fix this — the narrator said 'Front Parlour' but the record said 'the_manse.'"*

At the same time, the narrator's instruction sheet now includes an explicit reminder: *"If your prose names a new room with a bold header, you must also file the location form. The auto-correction is a safety net, not your primary job."*

---

## Why This Approach

The game engine has two choices when it detects a contradiction between prose and state: stop the turn and demand a correction, or repair silently and log loudly. Stopping a turn mid-play is expensive — it means the player stares at a spinner while the system retries. Repairing silently (no log) would hide the problem forever and make the narrator worse over time with no signal to improve it.

This fix takes the middle path: repair gracefully so the player sees nothing unusual, but make every repair visible in the GM dashboard at WARNING level. The OTEL span `narrator.location_drift_repaired` fires with the old location, the new one, the turn number, and the character — enough information to audit every incident from the observation panel. The goal is to make the auto-repair a backstop that fires rarely, not a crutch the narrator leans on every turn.

The bold-title pattern was chosen because it is already the narrator's own convention for announcing rooms — the fix is reading a signal the narrator already produces, not inventing a new one.

---
