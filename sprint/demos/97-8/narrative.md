# Narrative

## Problem Statement
**Problem:** A test that verifies the game lobby's "leave and start again" flow was intermittently hanging for 5 seconds and failing, causing the test suite to report a false failure that had nothing to do with any actual game defect.

**Why it matters:** Flaky tests — tests that fail randomly without a real bug — erode trust in the test suite. When developers see red on a passing build, they start ignoring failures. Over time, ignoring failures lets real bugs slip through. This test specifically guards a critical security boundary: ensuring a player can't accidentally reconnect to someone else's saved game when they start a new session.

---

## What Changed
A single word in a single test file was changed: `'Tarn'` was changed to `'Keith'`.

Here's the story: the test was written in April 2026 to check that when a player leaves a game and starts a new one, the game opens a *fresh* connection — not a stale one to the old game. To make the test work correctly, the test author deliberately used a fake player name (`'Tarn'`) in the test's setup data, so that a different safety check wouldn't short-circuit the test early.

In June 2026, a security improvement was added to the app: it now requires that both the *game ID* **and** the *player's name* match before allowing a silent reconnect. This was added to prevent a class of silent identity-rebind bugs (imagine Groucho accidentally resuming Alice's saved game without being asked). That was a correct and intentional security hardening.

But the old test's fake `'Tarn'` name no longer passed this new combined check. The app saw a mismatch, stopped the connection, showed the name prompt instead — and the test waited forever for a WebSocket connection that was never going to open.

The fix: update the test's fake name from `'Tarn'` to `'Keith'` (the name the test was already running under) so it correctly satisfies the new security gate.

---

## Why This Approach
The investigation team first had to figure out *why* it was flaky. The initial hypothesis — that a test-library interaction with React's rendering mode was causing a race condition — turned out to be wrong. The team proved this by systematically eliminating suspects: they raised the timeout (still hung), removed the suspected React flag (still hung), and traced where exactly it stalled. It always stalled at the very first step, before any race could even begin.

Once the real cause was identified (stale test data, not a timing bug), the correct fix was obvious: update the test data, not the production code. Loosening the security gate to satisfy the old test would have been wrong — the gate exists for a good reason. Bypassing or disabling the test would have eliminated coverage. The minimally correct fix was to bring the test's expectations into alignment with the app's current (correct) behavior.

The team also verified that the security *rejection* path — what happens when names *don't* match — still has dedicated test coverage in a different test file, so no firewall was weakened by this change.

---

## Before/After
| | Before | After |
|---|---|---|
| **Test result** | ✗ Timeout after 5003ms | ✓ Pass in ~198ms |
| **What the app showed** | Name Prompt (game never connected) | Game connection opened correctly |
| **Root cause** | `player_name: 'Tarn'` failed the June 2026 security gate | `player_name: 'Keith'` matches the session identity |
| **Files changed** | — | 1 (test fixture only) |
| **Production code changed** | — | None |
| **Security gate status** | Intact but tripping the stale test | Intact, correctly satisfied by the updated fixture |
| **Rejection-path coverage** | Present in `slug-routing.test.tsx` | Unchanged — still present and passing |
