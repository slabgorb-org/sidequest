**Duration:** 3–4 minutes. No live demo required — the "before/after" is a terminal output comparison.

**Slide 1 (Title):** Introduce the story: "A one-word fix that took a detective investigation to find."

**Slide 2 (Problem):** Show the test failure output — the test hung at exactly 5003ms every time. Explain what the test is guarding (leave-and-restart flow, identity firewall). Say: "The initial title said it was a React/WebSocket library interaction. It was not."

**Slide 3 (What We Built):** Show the one-line diff — `player_name: 'Tarn'` → `player_name: 'Keith'`. This is the entire change. The slide makes the point: sometimes the right fix *is* one word.

**Slide 4 (Why This Approach):** Walk through the investigation steps — timeout raised (still hung), React flag removed (still hung), DOM inspection (showing NamePrompt instead of a game), bisect to exact line. End with: "The security gate was right. The test data was stale."

**Before/After slide:** Side-by-side terminal. Left: `✗ Leave + Start opens a new WebSocket — timeout 5003ms`. Right: `✓ Leave + Start opens a new WebSocket — 198ms`.

Fallback: if running live tests fails for any reason, show the static terminal screenshots; the output is deterministic and pre-captured.

**Terminal command for live demo:**
```bash
cd ../sidequest-ui && npx vitest run src/__tests__/lobby-start-ws-open.test.tsx
```
Expected output: `2 tests passed` in under 300ms.

**Roadmap slide:** See below.

**Questions slide:** Anticipated question — "How did we know the security gate was correct and not the bug?" Answer: the gate has its own dedicated tests in `slug-routing.test.tsx` that specifically verify rejection behavior. Those tests were never failing.

---