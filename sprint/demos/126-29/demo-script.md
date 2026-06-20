**Setup before presenting:**
- Have two browser tabs open, both connected to the same session running a Fate conflict
- Player 1 (Tab A) has already submitted their action — e.g., Attack
- Close Tab A to simulate a disconnect/reconnect
- Leave Tab B (Player 2) at the "waiting for all players" screen

**Slide 2: Problem**

Open Tab A fresh (reconnect). Scroll to the conflict panel. Point to the four action tiles — Overcome, Create Advantage, Attack, Concede — all lit up and clickable. Say: "This player already locked in their attack. But look — the buttons are all still active." Click Attack. Pause. Nothing happens. Say: "The server rejected it silently. The player has no idea why."

*Fallback if live demo is unavailable: show a screenshot of the pre-fix state with the active tiles visible on a reconnected session.*

**Slide 3: What We Built**

Refresh Tab A with the fix deployed. Reconnect. Point to the same conflict panel area. The four action tiles are replaced by the fate-sealed indicator — the same greyed-out "your action is locked in" visual that appears after a live commit. Say: "Same player, same moment in the conflict. Now the interface matches reality. Their action is locked. The buttons are gone. No confusion, no failed clicks."

*Fallback: side-by-side screenshot — before (active tiles) vs. after (sealed indicator).*

**Slide 4: Why This Approach**

Briefly show the game's conflict panel in Tab B. Point to Player 2's tiles — still active, because they haven't committed yet. Say: "The server's rules didn't change. Only one commit per player per round, no exceptions. We just made the UI honest about what the server already knew."

---