# Demo Script — 61-8

**Deck structure:** Slide 1 (Title) → Slide 2 (Problem) → Slide 3 (What We Built) → Slide 4 (Why This Approach) → Slide 5 (Before/After) → Slide 6 (Roadmap) → Slide 7 (Questions)

---

**Opening (Slide 1 — Title, 0:00–0:30)**

Introduce the story: "This is the punch-list close for Epic 61 — the sprint that was triggered by a $313 runaway charge in 48 hours. The big fixes shipped over five stories. This one closes the items the reviewers flagged as 'real but not blocking.' They're small. They matter."

---

**Problem (Slide 2 — Problem, 0:30–1:30)**

"After the main stories shipped, we had a short whiteboard list. Two of the items were observability gaps — alarms that fired into log files no one was watching. One was a constant with a misleading name that would confuse the next engineer to read it. One was a silent data bug that could cause the narrator to forget an NPC's identity on old save files. And five lines of static-analysis errors that had been pre-existing but unaddressed."

Point to the 'Why it matters' framing: "None of these would have caused a $313 bill by themselves. But the runaway happened because several small observability gaps added up. We close gaps."

---

**What We Built (Slide 3 — What We Built, 1:30–3:30)**

**Live demo — dashboard event (if server is running):**

```bash
# In one terminal, start the server
just server

# In another terminal, tail the watcher event log
just logs server | grep narrator_context_missing_lore_store
```

"Before this story, that grep returns nothing even when the lore store is misconfigured — the warning only goes to a log file. After this story, it fires a watcher event the GM panel can subscribe to."

**Fallback (if server not running): show Slide 3 with the before/after code snippet** — `logger.warning(...)` alone vs. `logger.warning(...) + watcher_hub.publish_event(...)`.

---

**Live demo — constant rename:**

```bash
cd ../sidequest-server
grep -n "PROMPT_BUDGET_BYTES_HARD" sidequest/agents/orchestrator.py | head -5
```

Expected output: lines showing the renamed constant. "It used to say SOFT. It hard-refuses. The name was a lie. Now it doesn't lie."

---

**Test suite (Slide 3 continued):**

```bash
cd ../sidequest-server
uv run pytest tests/server/test_61_8_projection_edge_cases.py -v
```

Expected output: four tests passing — empty encounter actors (2), PC with no current room (2). "These edge cases had no regression coverage. Now they do."

---

**Why This Approach (Slide 4, 3:30–4:30)**

"Twelve sub-items, one PR, one implementer pass. We deliberately did not run the full TDD ceremony — test-engineer RED phase, separate GREEN phase, individual reviewer fan-out per item — on a list of constant renames and counter splits. That ceremony costs more time than the items themselves. We ran the adversarial nine-specialist review once at the end. It found three real bugs. We fixed them. That's the right-sized process for a cleanup bundle."

---

**Before/After (Slide 5, 4:30–5:30)**

Walk through the before/after table (see section below).

---

**Roadmap (Slide 6, 5:30–6:30)**

"Epic 61 still has open items. The architecture gate (61-5) enforces at the test layer that any new snapshot field must have a documented bounding decision — that story is unblocked now that 61-7 and 61-8 are merged. The 50-turn playtest validation (61-6) is the empirical proof that per-turn costs stay flat over a long session. And four follow-up stories (A through D) close the cross-session state hazards the cost-alarm introduced. This story was the last cleanup; the remaining work is validation and structural enforcement."

---

**Questions (Slide 7)**

---
