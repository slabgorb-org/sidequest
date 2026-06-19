**Pre-demo setup:** Have two browser windows open side by side, both connected to a running Fate Core session. Left window = the attacker (Player A). Right window = the defender (Player B, the local player being targeted). A conflict scene should already be in progress with both characters seated.

---

**Scene 1 — The Problem (Slide 2: Problem)**
*~1 minute*

Before this fix, trigger an attack from Player A's window. Switch to Player B's window. Show the screen: nothing. No prompt, no tray, no indication anything happened. The game is waiting. Point out that there is no way forward — the table is stuck. Say: "This was every Fate combat before today."

*Fallback: Skip the live freeze demo; show a screenshot of the blank screen with the caption "Game hangs here."*

---

**Scene 2 — What We Built (Slide 3: What We Built)**
*~2 minutes*

With the fix deployed, repeat the attack from Player A's window. Switch to Player B's window within 2–3 seconds.

Show the defend tray that has mounted. Point to each element:
- Attacker name pulled from the payload — e.g., **"Cora Vale"**
- Skill used — e.g., **"Fight"**
- Attack total — e.g., **"+3"**

Say: "Every value you see came from the server. We didn't write a single one into the code."

Click **Roll Defense** on Player B's window. The 4dF dice animate and settle, e.g., `[+, +, -, 0]` = **+1**. The tray closes. Switch to Player A's window to show the outcome logged in the narration feed.

*Fallback: Show a screen recording of the tray mounting and closing.*

---

**Scene 3 — Concede (Slide 3 continued or Before/After slide)**
*~1 minute*

Start a fresh attack. When the defend tray appears on Player B's window, click **Concede** instead of rolling dice. Show the tray closing immediately. Show the narration feed updating with the concede outcome.

Say: "Fate rules let you choose to lose gracefully and take a story benefit. That's a real mechanical option — it's in the rulebook — and now it's on the screen."

*Fallback: Describe what would appear; this is a one-tap interaction with no complex state.*

---

**Scene 4 — It's Wired to the Real Game (Slide 4: Why This Approach)**
*~30 seconds*

Pull up the test output in a terminal:

```bash
cd ../sidequest-ui && npx vitest run --reporter=verbose src/__tests__/FateDefend
```

Show the passing tests. Point to the test name that says something like `mounts defend tray via real GameBoard path` — not just the component in isolation.

Say: "We proved this works inside the actual game screen, not in a lab."

---