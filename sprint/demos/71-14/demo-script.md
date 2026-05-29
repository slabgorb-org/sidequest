**Total runtime: ~6 minutes**

**Slide 1: Title (30 seconds)**
Introduce the story: "This was a one-point housekeeping ticket that restored our type-checker's credibility on two recently-shipped test files."

**Slide 2: Problem (60 seconds)**
Reference the 38-error baseline. Say: "Before this change, running `uv run pyright` on these two files produced 38 errors. Here's what that looked like."
Show (Slide 2): the error count and a representative error — `error: No parameter named "visibility_sidecar" (reportCallIssue)`.
*If live terminal available:* `cd /path/to/sidequest-server && git show HEAD~1:tests/server/test_opening_pov_swap_71_5.py | head -20`
*Fallback:* Slide 2 with the error screenshot.

**Slide 3: What We Built (90 seconds)**
"Zero errors. Here's the after state."
Live terminal command: `uv run pyright tests/server/test_opening_pov_swap_71_5.py tests/server/test_opening_emit_event_71_13.py`
Expected output: `0 errors, 0 warnings`
Then: `uv run pytest -n0 tests/server/test_opening_pov_swap_71_5.py tests/server/test_opening_emit_event_71_13.py`
Expected output: `10 passed`
*Fallback if commands unavailable:* Show Slide 3 with the "0 errors / 10 passed" result as static text.

**Slide 4: Why This Approach (60 seconds)**
Walk through the three categories of fix. Highlight the difference between "real fix" and "targeted suppression with a specific reason."
Point to example: `assert sd is not None` at line 85 of `test_opening_pov_swap_71_5.py` — "this is not a workaround, it's a guarantee the checker can use."

**Before/After Slide (60 seconds)**
Show the two-column comparison (see Before/After section below). Emphasize: same test behavior, cleaner signal.

**Roadmap Slide (45 seconds)**
"One finding came out of this work that feeds directly into a future story: the `handle_message` function signature is mismatched with how it's actually called everywhere in the codebase. That's a small production fix that will let us remove seven suppression comments added here." Reference delivery finding at `sidequest/server/websocket_session_handler.py:364`.

**Questions (open)**

---