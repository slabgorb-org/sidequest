**Total runtime: ~5 minutes**

**Scene 1 — Title (0:00–0:15)**
Slide 1: Title. Presenter opens on: "Giving mutant characters a real choice in combat." One sentence, no build-up.

**Scene 2 — The Problem (0:15–1:00)**
Slide 2: Problem. Say: "Mutant characters in our post-apocalyptic setting have special powers — things like Iron Hide or Keen Sight. Until this update, a player could not actually choose to use one of these in a fight. The game either errored out, or silently treated it like a boring, generic punch." Show the before-state: a screenshot or live screen of the combat overlay with no picker present when a power-use moment comes up.

**Scene 3 — What We Built (1:00–3:00)**
Slide 3: What We Built. This is the live demo.

Terminal setup (run these before the meeting starts, in two separate terminal panes, so they're already warm):
```
just server
```
```
just client
```
Then open a browser to `http://localhost:5173`.

Live walkthrough:
1. Connect to a Mutant Wasteland session (world: `seaboard_of_saints`) with a mutant character already in play.
2. Trigger a "Wasteland Brawl" combat encounter and take an offensive action.
3. When the mutation-use moment ("mutant_ability" beat) comes up, click it — **show the picker opening** instead of the fight just resolving immediately.
4. Point out the two listed powers with their exact display data: `Iron Hide` (id `structure/iron_hide`, Strain cost **2**) and `Keen Sight` (id `sense/keen_sight`, Strain cost **1**).
5. Click **Keen Sight** — show the cost and choice riding along with the action as it's sent, and the fight resolving using that specific power (not a generic attack).

**Fallback if the live demo fails (server won't start, session won't connect, etc.):** Skip straight to a static screenshot on Slide 3 showing the picker mid-selection with the same two powers and cost values called out. Narrate the same 5 steps over the static image instead of clicking through them live.

**Scene 4 — Why This Approach (3:00–3:45)**
Slide 4: Why This Approach. Say: "We didn't invent a new mechanism — we copied the exact pattern already used for spellcasters, so this feels consistent and shipped faster. And in testing, we caught a scenario where a renamed or removed power could have crashed the game for the whole table — we fixed that before anyone could hit it."

**Scene 5 — Before/After (3:45–4:15, optional)**
Show side-by-side: Before = combat overlay with no picker (action just resolves generically or errors). After = picker open, showing `Iron Hide` / Strain 2 and `Keen Sight` / Strain 1, selection highlighted.

**Scene 6 — Roadmap (4:15–4:45)**
Slide: Roadmap. Cover the points in the Roadmap & Integration section below at a high level — one sentence per bullet.

**Scene 7 — Questions (4:45–5:00)**
Slide: Questions.