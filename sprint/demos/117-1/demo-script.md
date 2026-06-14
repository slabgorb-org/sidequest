**Estimated runtime:** 3 minutes. No live system required.

**Slide 1 — Title (0:00–0:20)**
Open with: "This is the smallest story in Epic 117, but it's a good example of how a big investigation surfaces small cleanup debt."

**Slide 2 — Problem (0:20–1:00)**
Reference Slide 2. Say: "During our June 14th playtest, the quest log was empty after 15 turns of a scripted detective hook. While investigating why, we audited the OTEL tooling — the 'lie detector' that tells us whether the engine is actually doing what the narrator claims. We ran `just otel` and checked the guide. The guide pointed at a deleted page. It was a ten-second confusion, but it's the kind of thing that compounds."

Show (terminal):
```bash
grep -n "just otel" CLAUDE.md
```
Output will show line 190 with the **fixed** text. Then say: "The previous text said 'server HTML dashboard.' That dashboard was deleted in PR #859. This line is now corrected."

**Fallback:** If terminal unavailable, show Slide 4 (Before/After) instead.

**Slide 3 — What We Built (1:00–1:45)**
Reference Slide 3. Show the diff — old text vs new text side by side (one line changed). Point at the React Inspector URL: `localhost:5173/#/dashboard`. Say: "The justfile already had the correct URL in its recipe comments. We made the human summary match."

Exact terminal demo:
```bash
just otel   # opens localhost:5173/#/dashboard in the browser
```
Say: "This is the live OTEL GM panel. It shows every span the engine emits in real time. This is the tool we use to verify that the quest engine, the lie-detector, and the narrator are all doing real work — not improvising."

**Fallback:** If the dev server isn't running, show the React Inspector screenshot on Slide 3 instead.

**Slide 4 — Why This Approach (1:45–2:15)**
Reference Slide 4. Say: "One-line fix, standalone story, full traceability. The pattern here is that documentation rot is a proxy for system rot — when the guide lies, developers stop trusting it, and then they stop reading it."

**Slide 5 — Before/After (2:15–2:45)**
Reference the Before/After slide. Walk through both states. Emphasize: "The fix required reading two files and typing one line."

**Roadmap slide (2:45–3:00)**
Say: "Story 117-1 is the cleanup. Stories 117-2 through 117-5 are the actual engineering work — making the quest engine deterministic so the GM panel *always* shows something real."

**Questions (3:00+)**

---