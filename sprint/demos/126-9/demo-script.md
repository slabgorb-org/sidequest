**Setup:** Server running with the fix merged, OTEL dashboard open at `localhost:5173/#/dashboard`. Have a terminal ready with a Postgres connection.

---

**Slide 1 (Title) — 30 seconds**

Introduce: "We shipped a latency fix today that cut narrator response time from ~60 seconds back to ~20 seconds. Here's what happened and what we did about it."

---

**Slide 2 (Problem) — 2 minutes**

"On June 16th, we shipped PR #908 — a healthy infrastructure upgrade that moved the narrator onto a newer, more capable SDK. What we didn't know: the new SDK defaults AI 'extended thinking' to ON. Every player turn, the narrator was secretly running a hidden reasoning pass — up to eight times — before writing the story."

Show the before numbers: "Here's the database showing what we saw. The same world — wry_whimsy/oz — went from 15.9 seconds to 56.7 seconds overnight."

Live query (or fallback to the pre-baked screenshot on this slide):
```bash
psql sidequest -c "SELECT payload_json->>'agent_duration_ms' AS duration_ms, payload_json->>'world' AS world FROM turn_telemetry WHERE component='validator' AND event_type='turn_complete' ORDER BY created_at DESC LIMIT 20;"
```

Point to the 56,700 ms rows from June 16–17. "That's a three-times regression, and it's invisible unless you're watching OTEL."

---

**Slide 3 (What We Built) — 2 minutes**

"The fix is one line of code. We added `thinking={"type":"disabled"}` to the narrator's SDK call. But more importantly, we added a test that will break the build the instant anyone re-enables thinking accidentally."

Show the test file name: `tests/agents/test_126_9_narrator_thinking_disabled.py`. "27 tests, all green. The wiring test — `test_orchestrator_routes_narration_through_sdk` — now asserts thinking is disabled end-to-end from the game orchestrator all the way to the transport layer."

Run the test suite live (or show the CI green badge):
```bash
cd sidequest-server && uv run pytest tests/agents/ -v --tb=short
```

Fallback if live test fails: Slide 3 screenshot of green CI.

---

**Slide 4 (Why This Approach) — 90 seconds**

"We had three options. Capping iterations would have cut the loop short and hurt narration quality — not acceptable. Reverting PR #908 would throw away a good upgrade to fix a side-effect. Disabling thinking explicitly restores the long-tested baseline with zero quality loss. If we ever want extended thinking deliberately — say for a slow planning step — we'll turn it on intentionally, with a threshold and a measurement."

---

**Before/After Slide — 90 seconds**

Show the comparison table (see Before/After section below). "Same world, same turn structure, different SDK default. The only thing that changed was one keyword argument."

---

**Roadmap Slide — 60 seconds**

Point to 126-10 (Fate-world prompt bloat). "There's a second latency spike — unrelated, different cause — that's still live in Fate worlds. That's next."

---

**Questions — open**

---