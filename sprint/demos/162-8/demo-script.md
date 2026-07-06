**Total runtime: ~5 minutes.** This is a lean, code-focused walkthrough — there is no UI change to show, so the "demo" is proving the removal via terminal output.

**Scene 1 — Slide 1: Title (0:00–0:15)**
Say: "This is a quick housekeeping story — no player-facing change, just removing two pieces of dead code that were left over from earlier work."

**Scene 2 — Slide 2: Problem (0:15–1:00)**
Explain the two stubs in plain terms (pipe capped in the wall / unwired light switch analogy above). Mention this was the closing cleanup story (162-8) in a seven-story initiative (162-1 through 162-7) to unify NPC creation.

**Scene 3 — Slide 3: What We Built — live demo (1:00–3:00)**
Run the following in the terminal, narrating each result:

```bash
cd sidequest-server
git log --oneline -1
```
Show the commit for story 162-8.

```bash
grep -rn "resolve_encounter_from_trope" sidequest/
```
Expected output: **zero matches** — narrate: "This function used to exist here; now it's fully gone, not just disabled."

```bash
grep -rn "name_generators" sidequest/
```
Expected output: **zero matches** — same point for the second target.

```bash
uv run pytest tests/server/test_dead_spawn_path_cleanup_162_8.py -v
```
Expected output: **4 passed** — narrate: "These are the four tests that specifically prove both dead paths are gone: one for the deleted function, one for the de-registered tool, one for the deleted module, and one for the removed field."

```bash
uv run pytest -q
```
Expected output: **14651 passed, 0 failed, 341 skipped** — narrate: "The full test suite — over 14,600 tests — still passes clean. Nothing broke."

*Fallback if live demo fails (e.g., environment not available): show the Before/After slide instead and read the diff stats directly (713 lines removed, 85 added — almost entirely new tests and one count fix).*

**Scene 4 — Slide 4: Why This Approach (3:00–3:45)**
Walk through the two rules (no stubbing, no silent fallbacks) and why deletion beat wiring for both targets — the live replacement systems already existed.

**Scene 5 — Before/After (3:45–4:15)**
Show the diff stat line: `713 deletions(-), 85 insertions(+)` and the tool-count change `41 → 40` in the narrator's advertised tool list.

**Scene 6 — Roadmap (4:15–4:45)**
Cover the epic context (below) and the one follow-up flagged for later.

**Scene 7 — Questions (4:45–5:00)**