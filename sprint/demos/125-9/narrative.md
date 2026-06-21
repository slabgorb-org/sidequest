# Narrative

## Problem Statement
Problem: When developers ran automated tests, those test sessions silently registered themselves with the live WatcherHub — the real-time monitoring hub that operators use to observe active game sessions. Why it matters: Operators watching the GM panel would see phantom "ghost sessions" from test runs mixed in with real player activity, making it impossible to distinguish what was a real game and what was a test artifact. Worse, this cross-contamination meant test events could trigger monitoring alerts, skew telemetry dashboards, and — in the worst case — cause test teardown to disrupt state that a live session was relying on.

---

## What Changed
Think of the WatcherHub like an air traffic control tower. Before this fix, every plane that taxied out of the hangar for a test flight automatically showed up on the live radar alongside real commercial flights. Controllers couldn't tell the difference.

The fix installs a gate at the hangar door. Test "planes" now either use a separate tower frequency (a dedicated test port) or file a flight plan marked `--no-watcher`, which tells them to fly without broadcasting to the live radar at all. Real game sessions continue to appear exactly as before. Test sessions stay invisible to the operator's monitoring surface.

---

## Why This Approach
Two options were evaluated:

1. **Separate port** — Run the test server on a different address entirely. Clean isolation by network address; the live WatcherHub simply never hears from a server it isn't configured to watch.

2. **`--no-watcher` mode** — A flag that tells the server to skip WatcherHub registration at startup. Useful when spinning up an in-process test server where port separation is awkward.

Both options were kept. Port separation is the default for integration test suites; `--no-watcher` handles edge cases like unit tests that boot a minimal server inline. The root cause — the WatcherHub being a process-level singleton that accepted any registrant without checking whether it was a test — is closed. The singleton now checks the mode it was started in before accepting a session.

This approach was chosen over "just tag test sessions differently" because tagging is a downstream mitigation. It would still pollute the event stream and require every downstream consumer to filter. Blocking at the source is cheaper and more reliable.

---
