**Setup (before presenting):**
- Have a running local instance with `just server` and `just client`
- Load a save file that has at least one active quest with lore attached (any save from the caverns_and_claudes or space_opera genre that has progressed past the first scene works)
- Have the QuestsPanel open on screen

---

**Scene 1 — The Problem (Slide 2: Problem)**
*Timing: ~60 seconds*

Open the Quests panel in the game UI. Point to a quest entry: title, status, maybe an objective line. Ask: "What does this quest connect to in the world? What has this character actually learned that's relevant?" The panel has nothing to say. The quest exists in isolation.

Now open the browser dev tools (F12 → Network tab → WS), find the `QUESTS` message, and expand a quest entry in the payload. Show the `related_lore` array already sitting in the wire data — a list of fact strings the server assembled. Point out: this data arrived, the UI received it, and displayed nothing. The folder was full; the detective got an empty desk.

*Fallback if live server isn't available: show Slide 2 with a screenshot of the empty QuestsPanel alongside a JSON snippet of the `related_lore` array in the wire payload.*

---

**Scene 2 — What We Built (Slide 3: What We Built)**
*Timing: ~90 seconds*

Refresh or reload the same save. Open the Quests panel. Scroll to the same quest. Below the objective, a new block appears: **"What I've learned about this job"** followed by a bulleted list of lore facts — for example:

- *"The Thornfield estate was seized by the Merchant Consortium three seasons ago under contested debt claims."*
- *"Locals say the eastern gatehouse hasn't been staffed since the original steward disappeared."*

These aren't invented for the demo — they're the actual facts the server tied to this quest based on what the character has encountered. Point out that none of this required new server work: the server was sending this data already. The client now reads it and shows it.

*Fallback: Show Slide 3 with a before/after screenshot — empty panel on the left, lore-populated panel on the right.*

---

**Scene 3 — The Test Lock (Slide 4: Why This Approach)**
*Timing: ~45 seconds*

Briefly show the terminal:

```bash
cd sidequest-ui && npx vitest run --reporter=verbose src/__tests__/QuestsPanel
```

The wiring test passes — it confirms that when the server sends a `QuestLogEntry` with `related_lore` populated, the panel renders the lore block. This is the guarantee that the behavior won't silently disappear in a future update.

*Fallback: Show Slide 4 with a screenshot of the passing test output.*

---