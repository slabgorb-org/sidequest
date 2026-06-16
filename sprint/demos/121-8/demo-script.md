> **Setup before the room fills:** Start a local dev session with a Fate-enabled genre. Navigate to the Connect screen. Have a second browser tab open on a Without Number session to show the negative case.

---

**Scene 1 — The Problem (Slide 2: Problem)** *(~2 min)*
Open the Without Number session tab. Show the existing character creation form. Point out that the fields say "name your skills" with numbers. Say: "This is what a Fate player sees today. Fate doesn't have numbered skill lists — it has a pyramid with adjectives. The game is fighting the interface from turn one."

*Fallback: If the tab won't load, show the screenshot on Slide 2 of the old form.*

---

**Scene 2 — Aspects (Slide 3: What We Built)** *(~3 min)*
Switch to the Fate session tab. The Fate chargen screen appears.

Click into the **High Concept** field. Type: `Disgraced Imperial Pilot`. Show the character counter: it should accept the phrase and mark it valid (green checkmark or border change).

Now clear the field entirely. The field border turns red and a hint appears: *"Your High Concept is who you are in a sentence — it can't be empty."*

Type `ok` — two characters. If there's a minimum-length guard, show it trigger.
Re-type `Disgraced Imperial Pilot`. Valid again.

Move to **Trouble**. Type `The Empire Wants Me Dead`. Valid.

Move to the two **free Aspect** fields. Type anything. Say: "These are the player's own invention — no genre constraints."

*Fallback: If the dev server is down, show the Slide 3 mockup/screenshot.*

---

**Scene 3 — Skill Pyramid (Slide 3 continued)** *(~4 min)*
Scroll down or navigate to the pyramid widget.

Show the starting state: all slots empty, the pyramid shape visible (1 peak slot, 2 below, 3 below that, etc.)

Drag **Pilot** to the peak slot (Superb, +5). Say: "This is legal — one peak skill."

Now drag a second skill to the same peak level. The pyramid turns red and a warning appears: *"A Fate pyramid can only have one skill at each rank if the rank above has fewer."* Say: "The game is enforcing the rule before you even submit."

Move the second skill down one rank (Great, +4). Still red — you need two slots at the Great level filled before the peak is legal, or you need to move the peak skill down. Demonstrate the correction: move Pilot to Great (+4), add a second skill at Good (+3). The pyramid goes green.

Say: "Players can't accidentally build an illegal character. The feedback is immediate, not a rejection after they click Submit."

*Fallback: If drag-and-drop is broken, show the Slide 3 static mockup with annotated callouts.*

---

**Scene 4 — Stunts and Refresh (Slide 3 continued)** *(~2 min)*
Navigate to the **Stunt Picker**. Show the Refresh counter in the corner: **3**.

Click to add a stunt. Counter drops to **2**.
Add another. Counter: **1**.
Try to add a third. The picker is now locked with a message: *"Refresh minimum reached (1). You can't take more stunts unless you raise your Refresh."*

Say: "Refresh is how many Fate Points you start each session with. The game won't let you bargain yourself below 1."

Remove one stunt. The picker unlocks.

*Fallback: Show the Slide 3 screenshot of the locked/unlocked stunt picker.*

---

**Scene 5 — The Negative Test (Slide 4: Why This Approach)** *(~1 min)*
Switch back to the Without Number session tab. Navigate to character creation. Say: "This is a player in a Without Number game. No Fate UI. Zero overlap." Point to the absence of Aspects, pyramid, Refresh counter — a completely different form.

*Fallback: Show Slide 4 side-by-side screenshot.*

---

**Scene 6 — Wrap (Slide 6: Roadmap)** *(~1 min)*
Say: "The character they just built on that Fate screen goes straight to the server for validation. The server is the authority — if anything on the screen is off, the server says so. The client never adjudicates the rules."

---