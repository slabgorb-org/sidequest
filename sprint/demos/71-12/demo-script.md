**Audience:** Non-technical stakeholders / sprint review  
**Duration:** ~6 minutes  
**Live demo:** Optional (code view) — fallback slides provided

---

**Scene 1 — Title (0:00–0:30)**  
*Slide 1: Title*  
Open with: "Today I want to show you a small but important piece of housekeeping we did to protect the multiplayer experience from a class of bugs that are hard to catch."

---

**Scene 2 — The Problem (0:30–2:00)**  
*Slide 2: Problem*  
Draw the analogy verbally: "Imagine our multiplayer game has two versions of player data flowing through it at any given moment — a raw version, and a processed display version. One critical part of the system has to use the raw version. The code was correct, but there was no sign on the door saying so. Any developer touching that area could flip it to the processed version and all our tests would still pass — we'd only find out when players reported weird behavior in a live session."

Concrete: "If this happened, players could see each other's actions attributed to stale turn context — imagine Alex's action from Round 4 appearing to be filed under Round 2's context because the processed snapshot was frozen there."

---

**Scene 3 — What We Built (2:00–3:30)**  
*Slide 3: What We Built*  
"We added a clearly labeled warning sign directly in the source code at the exact point where the raw feed is consumed. It names the rule, explains the failure mode, and points to the design documents."

**Live demo option:** Open `sidequest-ui/src/App.tsx`, navigate to line 1343. Show the 7-line guard comment. Read aloud: *"MUST use raw reveals from perception-filtered map, never merged."*

**Fallback (if live demo unavailable):** Show Slide 3 with the comment pasted as a code block. Point out that it names both the rule AND the consequence of breaking it.

---

**Scene 4 — Why This Approach (3:30–4:30)**  
*Slide 4: Why This Approach*  
"We chose the fastest, lowest-risk protection first. Zero logic changes. All 1,744 tests green. Comment verified accurate against the live code by three independent automated reviewers."

"The stronger version — an automated test that would *catch* this at build time — is already identified and queued as the next story. This delivers immediate protection while that work is scoped."

---

**Scene 5 — Before/After (4:30–5:15)**  
*Optional Before/After Slide*  
Walk through the comparison table below.

---

**Scene 6 — Roadmap (5:15–5:45)**  
*Roadmap Slide*  
"The follow-up story converts this comment guard into a machine guard — an automated test that will fail the build if someone ever wires the wrong data source here."

---

**Scene 7 — Questions (5:45–6:00)**  
Open floor.

---