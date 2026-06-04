# Narrative

## Problem Statement
**Problem:** Players stared at a blank screen while SideQuest's AI narrator composed their story. Even though the AI was generating text word-by-word in real time, the game waited until every sentence was finished before revealing anything — a jarring pause of several seconds on every turn that broke immersion and made the game feel unresponsive.

**Why it matters:** The core promise of SideQuest is a narrator "good enough to fool a career GM." A GM who makes you wait in silence for five seconds before reading your fate isn't a good narrator — they're a bad one. For players like Alex, who already feel pressure at the keyboard, an unresponsive screen amplifies anxiety. For a group accustomed to responsive software, it signals that something is wrong.

---

## What Changed
Think of a typewriter effect in a chat app: instead of receiving a wall of text that pops into existence, each word appears as it's typed. That's what this story delivers.

Before this change, the AI narrator would finish writing the entire scene — sometimes a paragraph or more — and only then send it to the player's screen all at once. The connection between the AI's "typing" and the player's screen simply wasn't wired up.

After this change, words appear on screen as the narrator generates them, letter-group by letter-group. The player watches the story unfold in real time. When the full scene is confirmed complete, the screen quietly locks in the final text. To the player, it just looks like the narrator is typing to them live.

One important safety rule was enforced: this live streaming only activates in solo play. In a group game, each player may receive a slightly different version of events (one player might learn a secret the others don't). Sending raw, unfiltered text mid-sentence to a multiplayer room could accidentally reveal those secrets before the game engine has had a chance to tailor each player's view. The multiplayer path was deliberately left unchanged — it waits for the fully processed, player-appropriate version before sending anything.

---

## Why This Approach
The team discovered both ends of this connection already existed and were built correctly — the server knew how to send streaming chunks, and the player's browser knew how to receive and display them. The work was simply connecting them.

Rather than build something new, the team verified the existing wiring was incomplete, identified the exact missing link (the server wasn't forwarding its real-time chunks to the WebSocket), and completed that connection. This is consistent with the project's core principle: "Don't reinvent — wire up what exists."

A key judgment call was made during review: an early version streamed text to all players in a room regardless of game mode, which would have been a subtle but serious bug in multiplayer games (different players would see raw unfiltered text flash on screen before their personalized version arrived). The team caught this, added a test that proved the bug existed, and fixed it before shipping — multiplayer rooms now receive zero streaming chunks, same as before.

---
