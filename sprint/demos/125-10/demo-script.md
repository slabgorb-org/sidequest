**Before the demo:** Have a terminal open in the `sidequest-server` directory and the `sidequest-ui` directory side by side. Have the test suite pre-run so results load quickly.

**Scene 1 — The Hidden Risk (0:00–1:30) → Slide 2: Problem**
Open `sidequest-server/sidequest/server/watcher_hub.py` and search for `is_test_session`. Show the function — it checks for the prefix `test-` or `tool-test-`. Then open `sidequest-ui/src/hooks/useLiveSource.ts` and show `isTestSession`. Both look the same today. Say: "Right now they match. But there's nothing stopping a developer from adding `demo-` to the server list and forgetting the UI."

**Scene 2 — The Contract Test (1:30–3:00) → Slide 3: What We Built**
Navigate to the contract test file. Run it live:
```bash
cd sidequest-ui && npx vitest run --reporter=verbose src/__tests__/testSessionContract.test.ts
```
Show the green output. Then say: "Now watch what happens if they drift." Open `useLiveSource.ts`, temporarily add `|| slug.startsWith('demo-')` to `isTestSession`, save, and re-run. The test fails with a clear message explaining what the two sides disagree on. Revert the change.

*Fallback if live edit fails:* Switch to Slide 3 and describe the output verbally — "the test prints exactly which prefixes are present in one place but not the other."

**Scene 3 — Why It Matters for the Dashboard (3:00–4:00) → Slide 4: Why This Approach**
Pull up the GM dashboard briefly. Remind the audience that 126-34 (the parent story) filtered test-run sessions out of the live GM view. Say: "That filter only works if both sides agree on what a test session is. This story is the lock on the door we built last sprint."

---