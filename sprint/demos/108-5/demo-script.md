**Setup before demo:** Start a WWN-bound session (e.g., heavy_metal/barsoom). Ensure at least one other character is in the scene so a confrontation can seat. Have the GM dashboard open in a second window.

---

**Scene 1 — "Before" (Slide 2: Problem)** *(~60 seconds)*
Open a save from a session before this story landed — or describe verbally. Show the old beat menu: a list of generic narrative beats with no combat-specific labels. Ask the audience: "Which one is Attack? Which fires a dice roll?" The answer is: you can't tell. That's the problem.

*Fallback if no old save is available:* Remain on Slide 2 and describe the experience verbally using the screenshot in the slide deck.

---

**Scene 2 — "New Action Bar" (Slide 3: What We Built)** *(~90 seconds)*
Launch a WWN session live or show a screen recording. Enter a combat encounter. Point to the four buttons now visible in the action bar:
- **Attack** — melee or ranged, rolls to-hit vs. AC
- **Move-Disengage** — withdraw from melee safely, triggers the movement roll
- **Use Item** — activates an inventory item; if it's a weapon, fires appropriate roll
- **Cast Spell** — available only to magic-capable characters; disabled and grayed out otherwise

Click **Attack**. Show the dice tray animate and resolve. Point to the exact roll displayed: "d20 + to-hit bonus vs. AC 14 — result: 17, hit. 1d8+2 damage: 6."

*Fallback:* Show the recorded demo clip on Slide 3.

---

**Scene 3 — "No Brace Button" (Slide 3 continued)** *(~30 seconds)*
Point out that there are only four buttons — not five. Explain that in WWN, your armor is always working. There is no "defend yourself" action because defense never turns off. This is the rules being respected, not a missing feature.

---

**Scene 4 — "Flavor Rider" (Slide 4: Why This Approach)** *(~60 seconds)*
Have a player type: *"I leap from the table, grab the ceiling beam, and drop my axe into the demon's skull."*
Show that the narration picks up the chandelier imagery — the narrator describes the theatrical move. Then point to the dice tray: the roll is identical to a plain Attack click. The story got richer; the math did not change.

Open the GM dashboard. Navigate to the OTEL event stream. Filter for `wn.action.flavor_rider`. Show the event with `affected_mechanics: false`. "This log line is the guarantee. The system is proving to itself — and to us — that flavor stayed flavor."

*Fallback if OTEL panel isn't loading:* Show the screenshot on Slide 4 with the event highlighted.

---

**Scene 5 — "Bare Text Does Nothing" (Slide 4 continued)** *(~30 seconds)*
Type a combat action with no button pressed. Show that the narrator responds narratively but no dice appear in the tray and no HP changes. "You can describe your action. The game won't let that description win a fight on its own."

---