**Target audience:** Non-technical stakeholders, product leads, playgroup members
**Duration:** ~4 minutes
**Format:** Screen share of the character creation flow (or pre-recorded clip if live server isn't available)

### Scene 1 — Title (Slide 1) | 0:00–0:20
Open on the title slide. "Today we're showing a small but meaningful polish fix to the SWN character creation experience — specifically the moment the game confirms who your character is."

### Scene 2 — The Problem (Slide 2) | 0:20–1:00
Show or quote the old confirmation text verbatim: *"Yara Chen. The Pilot from Spacer space. The galaxy doesn't know it yet, but it's going to be your story."*

Point out "Spacer space" specifically. "Spacer is the character's origin — where they come from culturally. But bolting 'from Spacer space' onto 'The Pilot' creates a weird echo. If this were a book, an editor would catch it on the first pass."

> **Fallback if live server isn't available:** Show Slide 2 with the before/after text side by side. The quote is accurate — pull from the session archive.

### Scene 3 — What We Built (Slide 3) | 1:00–1:45
Navigate to the character creation flow in a running game instance. Choose the **Aureate Span** world, pick the **Pilot** class, select **Spacer** as origin. Reach the confirmation screen.

Show the new text: *"Yara Chen. The Spacer Pilot. The galaxy doesn't know it yet, but it's going to be your story."*

"The origin — Spacer — now functions as a descriptor for the class. It reads like a title, not a sentence fragment."

> **Exact terminal command to start server if needed:**
> ```bash
> cd ~/Projects/oq-1 && just server
> ```
> Then open `http://localhost:5173` in the browser.

> **Fallback:** Slide 3 has the before/after text. Quote it directly and move on.

### Scene 4 — Why This Approach (Slide 4) | 1:45–2:30
"The text didn't live in code — it lived in content configuration files, one per world. That's intentional: writers and game designers can update prose without touching the engine. The fix was a one-line reorder in three files. We also added an automated test that loads the real templates and checks the output, so this specific regression can never sneak back in."

### Scene 5 — Before / After (optional slide) | 2:30–3:00
Show the two strings side by side if the slide deck includes a before/after:
- **Before:** `"Yara Chen. The Pilot from Spacer space."`
- **After:** `"Yara Chen. The Spacer Pilot."`

Apply to all three SWN worlds: Aureate Span, Coyote Star, Perseus Cloud.

### Scene 6 — Roadmap (Slide: Roadmap & Integration) | 3:00–3:30
"This is part of a broader polish sweep across the character creation flow. Related fixes in this sprint address name-answer handling and missing SFX audio. The content-layer architecture that made this a one-line fix is the same system that lets Jade or any future author add new worlds without touching server code."

### Scene 7 — Questions | 3:30–4:00
Open floor. If asked "could this happen again?" — point to the regression test. "If anyone edits the template incorrectly, the automated test suite catches it before it ships."

---