**Slide 1 (Title):** Introduce 152-3 as the final piece of the WWN combat restoration sprint — the safety net that confirms all the engine work from 152-1 and 152-2 actually holds.

**Slide 2 (Problem):** Show the failing test output before the fix. The key detail to call out: `target_class Warrior not in [None, None, None, None, None, None]` — six blank answers. Explain that the test helper was hitting the background-selection screen and didn't know what to do with it.

**Slide 3 (What We Built):** Show the before/after of the `_build_character` helper. Before: a single loop that assumed every choice contained a class hint. After: a branching walk that checks whether the current screen is the class screen (`the_calling`) or the background screen (`the_trade`) and picks accordingly.

**Live demo command (run from `sidequest-server/`):**
```bash
uv run pytest tests/server/test_class_signature_wiring.py tests/server/test_cc_chargen_e2e.py -v
```
Expected output: both tests green, with assertions firing on class names, Killing Blow / Veteran's Luck / Read the Ledger / Read the Worked Stone signature abilities, and pronoun-agnostic prose.

**Fallback (if demo environment not available):** Show Slide 3's Before/After comparison instead of running live.

**Slide 4 (Why This Approach):** Emphasize the "no production code changed" point — this is test-only, which means there's no risk of introducing a new bug into the game engine to make a broken test pass.

**Before/After slide:** Show the `[None x6]` crash log side-by-side with the green test run.

**Roadmap slide:** 152-3 closes the test-debt chapter of the WWN combat restoration. The next open story (152-4) extends the same pattern to the *opponent* side of combat.

**Questions.**

---