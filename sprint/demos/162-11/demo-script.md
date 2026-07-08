**Total runtime: ~6 minutes**

**Scene 1 — Slide 1: Title (0:00–0:20)**
Open on the title slide ("Catching the Bot That Couldn't See: Fixing Understudy's Blind Spot"). One-line framing: "Our automated playtester had a broken smoke detector. Here's how we found it and fixed it — and made every other detector stronger in the process."

**Scene 2 — Slide 2: Problem (0:20–1:15)**
Walk through the "two names, one enemy" scenario verbally: narration says "Molgrath the Eyeless," the roster says "Thief." Say explicitly: "The watchdog meant to catch this has been live for weeks and has never fired once — not because it's never happened, but because it was never actually looking." Land on the stakes: this is our only automated proof that earlier identity-fix work holds up live.

**Scene 3 — Slide 3: What We Built (1:15–2:30)**
Explain the three-part fix using the accessibility-layer analogy from "What Changed" above. Keep it visual/conceptual — no terminal yet. End with: "Now let's watch the detector actually catch something."

**Scene 4 — Live Demo Part 1: proving the labels are real (2:30–3:45)**
Switch to terminal. From the `sidequest-ui` repo root, run:
```
npx vitest run src/components/__tests__/ConfrontationOverlay.aria-enemies-162-11.test.tsx src/components/__tests__/NarrationScroll.aria-log-162-11.test.tsx
```
Narrate while it runs: "This confirms the enemy roster is a real, labeled 'Enemies' region and the narration feed is a real, labeled log — the two pieces of invisible scaffolding we added." Point out the pass count in the output (6 tests, all green).

*Fallback if this fails (e.g., dependency/environment issue):* Skip to Slide 5 (Before/After) and show the captured before/after snapshot text instead of live output — see Scene 6 content below, which has the exact strings to display.

**Scene 5 — Live Demo Part 2: the detector actually firing (3:45–5:00)**
From the `sidequest-understudy` repo root, run:
```
uv run pytest tests/wiring/test_identity_fork_realdom_162_11.py -v
```
Narrate: "This drives our actual bot through a real browser session against a page shaped exactly like the live game, and checks whether the 'two names, one enemy' finding shows up in its report." Call out the specific assertion in the output: the finding `two_names_one_enemy` appears in `findings.json` with a grade of `CONFIRMED` or `BEHAVIORAL` — not empty, not `None`. Say: "Three weeks ago, this same test would have reported nothing. That's the blind spot, closed."

*Fallback if Playwright/browser isn't available in the room:* Show Slide 5 (Before/After) with the two snapshot blocks from Scene 6 side by side — this is the exact evidence the live run would have produced.

**Scene 6 — Slide 5: Before/After (5:00–5:35)**
Show two blocks of captured output side by side.
- *Before (what the bot saw — nothing usable):* no "Enemies" region, no "log" role — detector input was empty, output was `None` on every real session.
- *After (what the bot sees now):*
```
- region "Enemies":
  - listitem: Thief
- log:
  - paragraph: Molgrath the Eyeless lunges at you from the dark.
```
Say: "That's the exact mismatch the detector is designed to catch — 'Thief' in the roster, 'Molgrath the Eyeless' in the narration — and now it's visible to the bot for the first time."

**Scene 7 — Slide 4: Why This Approach (5:35–6:20)**
Cover the "fix the source, not the symptom" reasoning and the two-round adversarial review (first round rejected with a real, specific silent-failure bug; second round independently verified every fix by deliberately breaking it). Close with the test-suite scoreboard: 282/282 automated-bot tests passing, 2,561/2,561 UI tests passing, zero regressions.

**Scene 8 — Slide 6: Roadmap (6:20–7:00)**
See Roadmap & Integration section below.

**Scene 9 — Slide 7: Questions (7:00+)**
Open floor.