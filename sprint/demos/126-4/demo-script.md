**Setup required:** Two browser windows open to the same session, logged in as two different players. Server and UI running locally (`just server` + `just client`).

---

**Slide 1 — Title**
*Open with the title slide. 30 seconds.*

Introduce the story: "We're looking at a bug that made multiplayer feel broken — your partner's move would disappear during the WAIT phase. Here's what it looked like, and here's the fix."

---

**Slide 2 — Problem**
*60 seconds. Show screenshot `126-4-040-BUG-instant-submit-no-text-turn3.png`.*

"Here's the actual failure from our playtest. Player A submitted their action — you can see the '✓ Sealed' chip appeared. But there's no text. Player B is sitting there waiting, knowing their partner moved, but having no idea what they said. This happened roughly half the time, depending on how fast the submitter typed."

Point to the chip. Point to the blank space where the text should be. "This is turn 3 — turns 1 and 2 worked fine because the player paused while typing, which triggered a redundant delivery path. Turn 3, they pasted and submitted instantly. One delivery window, one drop."

**Fallback if live demo unavailable:** Stay on this screenshot. It's self-explanatory.

---

**Slide 3 — What We Built**
*90 seconds. Transition to live demo if possible.*

Show screenshot `126-4-020-WAIT-peer-sealed-text-VISIBLE-turn1.png` first.

"After the fix, here's what the WAIT phase looks like. Player A submitted. Player B immediately sees the action text — same turn, same moment, reliably."

Then show `126-4-030-WAIT-peer-sealed-text-VISIBLE-turn2-reverse.png`.

"And here's the reverse view — Player B submitted first, Player A sees it. Works both ways, every turn."

**Live demo (if running):**
- Window 1: submit an action by typing something, hitting Enter fast (paste if possible)
- Switch to Window 2: the peer's action text should appear in the WAIT strip immediately
- Point to the text: "That's the recovery path. The server's authoritative roster delivered the text even though the fast-submit path's single frame was never waited on."

**Fallback:** Use the two screenshots above side by side.

---

**Slide 4 — Why This Approach**
*45 seconds.*

"We didn't try to 'fix the network.' We made the text redundant — it now travels with the reliable channel that was already working, instead of living or dying on a single fast-path frame. Same principle as insuring your luggage: the airline still tries to get your bag to you, but if the bag doesn't make it, you're not left with nothing."

---

**Before/After (optional slide)**
*30 seconds.*

"Turn 3, fast submit, before the fix: sealed chip, no text. Turn 3, fast submit, after the fix: sealed chip, action text. Same table, same network, same speed of typing."

---

**Roadmap slide**
*30 seconds.*

"This lays the groundwork for the sealed-visibility / PvP mode described in our architecture docs — where players deliberately *shouldn't* see each other's moves during WAIT. The authoritative channel now controls what text travels; a PvP mode would simply not populate that field for opposing players. The infrastructure is ready."

---

**Questions**

---