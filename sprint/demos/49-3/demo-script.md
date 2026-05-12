# Demo Script — 49-3

**Setup (before the room):** Have the Glenross save file open. Have the GM dashboard visible on a second monitor or tab. Know your terminal location: `~/Projects/oq-2/sidequest-server`.

---

**Scene 1 — The Problem (Slide 2: Problem)**
*Approx. 2 minutes*

Walk the audience through the playtest recording. Open the session archive:

```
cat ~/Projects/oq-2/sprint/archive/49-3-session.md
```

Read aloud the five-turn sequence from the "Story Context" section: narrator titled rooms "The Bee Garden → The Manse Garden → Front Parlour → Study → Sickroom Passage" while the engine recorded `the_manse` for turns 1 through 5. Point to the phrase `has_location=False` in the context block — that is the game patch log saying the narrator never filed the move form.

*Fallback if terminal is unavailable:* Slide 2 has the five-turn sequence as a table. Read from the slide.

---

**Scene 2 — The Fix in Code (Slide 3: What We Built)**
*Approx. 3 minutes*

Open `narration_apply.py` at the extractor function:

```
grep -n "_extract_leading_bold_title\|_LEADING_BOLD_TITLE_RE" \
  ~/Projects/oq-2/sidequest-server/sidequest/server/narration_apply.py
```

Show the regex on line 88: `\A\s*(?:#{1,2}\s+)?\*\*([^*\n]+)\*\*` — "this is the secretary reading the top of the prose page." Then jump to the application logic:

```
sed -n '1684,1707p' \
  ~/Projects/oq-2/sidequest-server/sidequest/server/narration_apply.py
```

Point to the four-line logic: (1) location is empty, (2) extract bold title, (3) compare to current state, (4) if different — fill the field and fire the OTEL span. Highlight `result.location = _candidate` — one line, one fix.

*Fallback:* Slide 3 has a simplified pseudocode box. Walk through it verbally.

---

**Scene 3 — The Guardrail in the Prompt (Slide 3 continued)**
*Approx. 1 minute*

Explain the second half of the fix: the narrator's instruction sheet now explicitly says *"If you write a bold room header, you must set location."* The auto-repair becomes a backstop, not standard operating procedure.

```
grep -rn "location_patch_constraint" \
  ~/Projects/oq-2/sidequest-server/sidequest/agents/
```

Show the section name in the output. No need to read the full text — the point is that it exists and fires every turn.

*Fallback:* Describe verbally that the narrator now has a written reminder at the top of its instruction set.

---

**Scene 4 — The GM Dashboard Visibility (Slide 3 continued / optional Before-After)**
*Approx. 2 minutes*

Open the OTEL dashboard:

```
just otel
```

Navigate to the Narrator spans filter. Show what `narrator.location_drift_repaired` looks like: a yellow WARNING badge with fields `old_state="the_manse"`, `new_from_title="The Manse — Front Parlour"`, `turn=3`, `char="Ziggy"`. If the live dashboard isn't populated, show the Before/After slide — point to the "After" column where the span is present vs. the "Before" column where there is nothing.

---

**Scene 5 — Regression Test (Slide 4: Why This Approach)**
*Approx. 1 minute*

Run the regression test to prove it works:

```
cd ~/Projects/oq-2/sidequest-server && \
  uv run pytest tests/ -k "location_drift" -v
```

Expected output: one test named `test_location_drift_repaired_from_bold_title` — PASSED. Point to the test: it loads a fixture with `character_locations[Ziggy]='the_manse'` and narration opening `**The Manse — Front Parlour**\n\nThe kettle...` with `patch.location=None`. After apply, the location is `The Manse — Front Parlour` and the span fired.

*Fallback:* Show the test file path and describe what it asserts. Slide 4 has the before/after state diagram.

---
