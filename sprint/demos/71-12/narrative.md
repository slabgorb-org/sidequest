# Narrative

## Problem Statement
**Problem:** The multiplayer game client contains a hidden trap — a spot in the code where a future developer could accidentally feed stale player data into a critical tracking system, and every existing test would stay green, meaning the bug would ship undetected. **Why it matters:** When players are in a multiplayer session, the game keeps a running log of what each player did each round. If that log accidentally picks up "processed" data instead of the raw original, it gets frozen at an old snapshot — players could see each other's actions attributed to the wrong context, or worse, actions from a past turn echoing into the current one. The game looked correct today, but the code had no warning sign to stop a future change from breaking it silently.

---

## What Changed
Think of the game's player-action tracker like a security camera recording raw footage. There are actually *two* video feeds available in the code — the raw unprocessed feed, and a display-processed version that adds overlays and status banners. The processed feed is great for showing players what's on screen, but if you accidentally recorded the *processed* feed to permanent storage instead of the raw one, your archive would be full of frames with burned-in text from an old turn.

This change added a clearly visible warning sign right next to the recording connection point in the code: **"This MUST plug into the raw feed, never the processed one."** The sign also explains *why* (stale data, frozen status) and points engineers to the relevant design documents. The underlying code was already correct — this is a prophylactic label, not a bug fix in the traditional sense. But without the label, any developer refactoring nearby could flip the connection without realizing the consequences.

---

## Why This Approach
The "right" fix would be an automated test that catches the wrong connection at build time — and that follow-up work has already been identified and queued. However, adding that automated test is a separate, slightly larger change. This story takes the faster, lower-risk step first: get a clear, accurate warning in place immediately so the gap is documented and visible to anyone touching that code *today*, rather than waiting for the automated guard.

The label approach is also the minimum-impact choice: zero logic changes means zero risk of introducing a new bug while protecting against a future one. All 1,744 automated tests continued to pass. The comment was verified accurate against the live code — every claim it makes checks out — so it cannot mislead a future developer.

---

## Before/After
| | Before (71-12) | After (71-12) |
|---|---|---|
| **State of the code** | Correct — but silently so | Correct — and visibly so |
| **Risk of future regression** | High: any nearby refactor could flip raw→processed, all tests pass | Reduced: engineer sees an explicit warning before making the change |
| **Failure mode if wrong** | Player actions logged under stale/frozen turn context; appears correct until a live session surfaces oddness | Same failure mode, but now named and documented at the exact danger point |
| **Test coverage** | Display path covered; accumulator path uncovered (gap pre-existed this story) | Unchanged — gap documented, follow-up queued |
| **Build output** | 1,744/1,744 tests passing | 1,744/1,744 tests passing (no change) |
| **Code change** | — | +7 comment lines, 0 logic lines |
| **Reviewer verdict** | — | APPROVED — all six factual claims verified against live code |
