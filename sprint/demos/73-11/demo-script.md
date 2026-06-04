**Slide 1 — Title:** Introduce the story: "One small cleanup, one less landmine."

**Slide 2 — Problem (2 min):** Walk through the risk scenario. Say: "Our test suite had a 208-line factory function living in two files. Neither file flagged a conflict. If a developer edited one copy to support a new feature and forgot the other, half the tests would behave differently — and we'd have no warning until something mysterious broke in CI." Show Slide 2's "two keys" visual.

**Slide 3 — What We Built (1 min):** "We deleted the duplicate. The root copy already had a comment saying it had been moved from the old location — this just makes that comment true." Show the before/after diff: `tests/server/conftest.py` shrinks by 208 lines.

**Slide 4 — Why This Approach (1 min):** "Pytest inheritance means the tests still work exactly as before — they just have one source of truth now." No behavior change, no test failures introduced.

**Live demo (optional, 2 min):**
```bash
# Show the root conftest still contains the factory
grep -n "session_handler_factory" tests/conftest.py

# Show tests/server/conftest.py no longer contains it
grep -n "session_handler_factory" tests/server/conftest.py || echo "Removed."

# Run the full server test suite to confirm nothing broke
cd sidequest-server && uv run pytest tests/server/ -q
```
**Fallback:** If demo environment unavailable, show the Before/After slide with the line counts.

**Roadmap slide:** Transition to how this fits the 73-series test hygiene epic.

**Questions:** Open floor.

---