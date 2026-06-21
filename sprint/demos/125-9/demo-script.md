**Total runtime: ~6 minutes**

---

**Slide 1: Title** *(0:00–0:20)*
Open on the title slide. Say: "This is a five-point bugfix that closes a monitoring contamination problem we discovered during the 126-34 assessment. It's not glamorous, but it's the kind of fix that makes everything downstream more trustworthy."

---

**Slide 2: Problem** *(0:20–1:30)*
Walk through the problem. Say: "Here's what was happening before."

Live demo — open a terminal and run:
```bash
just server-test 2>&1 | grep "WatcherHub"
```
Before the fix, this would show lines like `WatcherHub: session registered test-abc123`. Point out: "That registration was going to the same hub a real operator watches. Now show the GM panel at `localhost:5173/#/dashboard` — you'd see ghost sessions listed alongside real ones."

*Fallback if demo unavailable*: Switch to Slide 2 and show the screenshot of the GM panel with test session IDs mixed in. Point to specific entries like `test-abc123` and `pytest-session-7f3a` appearing in the session list.

---

**Slide 3: What We Built** *(1:30–3:00)*
Switch to Slide 3.

Live demo — start the test server in no-watcher mode:
```bash
SIDEQUEST_NO_WATCHER=1 uv run pytest tests/server/ -v -k "test_session" 2>&1 | grep -E "(WatcherHub|PASSED|FAILED)"
```
Expected output: zero `WatcherHub: session registered` lines. All `PASSED`. Say: "The tests ran, sessions were created and torn down, and the live hub heard nothing."

Then show the GM panel again. Zero phantom sessions. Point to the empty session list: "Clean. Operators see only real player sessions."

*Fallback*: Show the before/after slide with the two GM panel states side by side.

---

**Slide 4: Why This Approach** *(3:00–4:15)*
Walk through the two-option design. Use the analogy on the slide. Emphasize: "We didn't tag test sessions differently — we blocked them at the source. Tags are promises; port isolation and mode flags are guarantees."

---

**Before/After slide** *(4:15–4:45)*
Let the comparison speak. Point to the specific numbers: "Before: every test run injected N phantom sessions into the live hub. After: zero."

---

**Roadmap slide** *(4:45–5:30)*
Connect to upcoming work. Two sentences max per item.

---

**Questions** *(5:30–6:00)*

---