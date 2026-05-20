# Demo Script — 57-2

**Total runtime: ~4 minutes**

---

**Slide 1: Title** (~15 sec)
Introduce story 57-2. Say: "This is a one-point audit story from Epic 57 — our narrator cost-cutting initiative. The question was simple: are any of our narrator instruction files accidentally empty?"

---

**Slide 2: Problem** (~45 sec)
Explain the concern. Say: "In May 2026, we reorganized the narrator's rulebook from one big file into 11 separate instruction files — combat rules, dialogue rules, player agency guardrails, and so on. A concern was logged at the time: did any of those files get extracted as empty placeholders? An empty file the narrator loads is invisible dead weight — tokens spent, no guidance delivered."

Point to the bullet: "Five files were flagged as potentially empty." Ask the audience: "What do you do when you're not sure if your AI's rulebook has blank pages?"

---

**Slide 3: What We Built** (~60 sec)

Live demo option — open a terminal:
```bash
wc -c sidequest-server/sidequest/agents/narrator_prompts/*.md
```
Show the output. Point out that every file has a non-zero byte count. Say: "All 11 files have content. The smallest is `identity.md` at 210 bytes — one tight principle. The largest are the output format specs at 24,000+ bytes each."

Then open the new file:
```bash
cat sidequest-server/sidequest/agents/narrator_prompts/AUDIT.md
```
Show the table. Say: "This is what we shipped — a living audit log. Date-stamped, file inventory, byte counts, integration chain. Next time someone asks, this is the answer."

**Fallback if terminal unavailable:** Show Slide 3 with a screenshot of the AUDIT.md table.

---

**Slide 4: Why This Approach** (~30 sec)
Say: "We chose a document over a test for speed and placement. The doc lives right next to the files it audits — no hunting. We flagged a future test as a follow-up; it's the right longer-term tool, but out of scope for a one-point check."

---

**Before/After slide** (~30 sec)
Before: "Open question — possibly five empty files contributing nothing to narrator quality while burning token budget." After: "Confirmed clean: 11/11 files substantive, integrated, named accurately in a durable audit log."

---

**Roadmap slide** (~30 sec)
Say: "This story is the foundation check for Epic 57. We now know the instruction files themselves aren't the savings opportunity. Stories 57-3, 57-4, and 57-5 target the actual cuts — redundant content, prompt structure, caching strategy."

---

**Questions** — open floor.

---
