**Total runtime: ~8 minutes**

**Slide 1 — Title (0:00–0:30)**
Introduce the story: "Story 77-4 closes out the Quest & Stakes Substrate epic. Today we're showing the final cleanup — one mechanism, one path, no legacy debt."

**Slide 2 — Problem (0:30–2:00)**
Walk through the two-pathway problem. Reference the three earlier stories (77-1, 77-2, 77-3) that built the new system. "By 77-3, we had a fully structured create/evolve path for quests and stakes. But the old lane was still alive in the code. Two writers, same destination — a telemetry nightmare and a correctness risk."

**Slide 3 — What We Built (2:00–4:00)**
Show the before/after summary (see section below). Point to the key numbers: **7 production files changed, 9 test files changed, net +180/-118 lines in the core PR, plus a hardening pass of +75/-29.**

Live demo (if server is running):
```bash
cd ~/Projects/sidequest-server
uv run pytest tests/game/test_quest_updates_retirement.py -v -n0
```
Expected output: `11 passed` — the full retirement suite including the 3 hardening tests that verified the lie-detector was reporting accurately.

*Fallback if demo fails: Slide 3 — show the table of 11 test names and their coverage areas.*

**Slide 4 — Why This Approach (4:00–5:30)**
Walk through the three principles. Emphasize the safety net: "We didn't just delete the old path. We left a bridge — but a bridge with a siren. Any old-format message gets translated and the GM panel immediately sees `quest.updates.legacy_emitted` with an exact count of what forwarded and what was skipped."

*Optional before/after slide (5:30–6:30):*
Show the before/after table below. Point to the `legacy_emitted` span's attribute table in the Reviewer delta re-review — specifically the row: `{q1:"active", q2:9}` → OLD reports `ids=[q1,q2]` (a lie), NEW reports `ids=["q1"], skipped=1` (the truth).

**Slide — Roadmap (6:30–7:30)**
"With 77-4 merged, the quest/stakes substrate is structurally complete. Story 77-5 is next: surfacing quest_log, quest_anchors, and active_stakes in the player UI as a dedicated quests panel."

**Slide — Questions (7:30–8:00)**

---