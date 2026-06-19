**Total runtime: ~8 minutes**

**Scene 1 (Slide 1 — Title, 0:00–0:30)**
Open with the slide. "Today we're closing a navigation gap in our engineering documentation — a mismatch between where nine files said to look for answers and where the answers actually lived."

**Scene 2 (Slide 2 — Problem, 0:30–2:00)**
Walk through the problem. "Imagine our ADR library is a law library. ADR-149 is the intellectual property chapter. But nine files in our combat system were citing it as the authority for how player defense rolls work — like filing a personal injury case under copyright law. The correct chapter didn't exist yet."

Show the before state on Slide 2 or in a terminal:
```bash
grep -n "ADR-148/149" sidequest/handlers/fate_throw.py
```
Expected output: lines showing `# See ADR-148/149` in comments. Point out the citation. "That 149 is wrong."

*Fallback if terminal unavailable: Slide 2 bullet "9 files, same wrong citation."*

**Scene 3 (Slide 3 — What We Built, 2:00–4:30)**
"We did two things: wrote the missing rulebook, and corrected all nine files."

Show the new ADR exists:
```bash
ls docs/adr/151-fate-defend-followup-barrier.md
wc -l docs/adr/151-fate-defend-followup-barrier.md
```
Expected output: the file exists, roughly 200+ lines.

"This document describes the four-phase combat round — Commit, Reveal, Defend, Resolve — how the server parks and waits for a player's dice roll before proceeding, how it prevents one player from defending for another, and how every decision is logged for our GM dashboard."

Then show the fix:
```bash
grep -n "ADR-148/151" sidequest/handlers/fate_throw.py
```
Expected output: the same lines now correctly reading `ADR-148/151`.

```bash
grep -rn "ADR-148/149" sidequest/
```
Expected output: *no results*. "Zero remaining wrong citations across the entire codebase."

*Fallback: Slide 3 Before/After bullets.*

**Scene 4 (Slide 4 — Why This Approach, 4:30–5:30)**
"We could have just done a find-and-replace. We didn't. We categorized every citation first — is this about the dice source? The SRD license? Or the defense barrier? It turned out every server occurrence was the barrier case, which validated the uniform fix. The categorization step is what makes this safe."

**Scene 5 (Before/After slide, 5:30–6:30)**
Point to the Before/After comparison. "Before: follow the citation, land in the wrong rulebook. After: follow the citation, land in the document that actually describes what the code does."

**Scene 6 (Roadmap slide, 6:30–7:30)**
"ADR-151 is the foundation that story 126-17 builds on — the player-facing defense tray UI. Having the barrier formally documented means the UI team has an unambiguous contract to implement against."

**Scene 7 (Questions, 7:30–8:00)**
Open for questions.

---