# Narrative

## Problem Statement
**Problem:** When a player in SideQuest rolled an attack or tried to move their character across the map, the game told them the outcome — hit, miss, moved, blocked — but never showed the math behind it. There was no way to see how far away a target was, what range band a weapon was actually firing at, or how much movement budget was left for the turn.

**Why it matters:** For part of our playgroup, seeing the numbers *is* the fun. Two of our most dedicated players are "mechanics-first" — they want to understand exactly why a shot succeeded or failed, not just be told it did. Without visible math, the game reads as if outcomes are simply narrated rather than calculated, which erodes trust in the system for the players who care most about the rules. This story puts that math on screen.

## What Changed
Think of it like adding a receipt to a purchase. Before, you'd swipe your card and just get a "approved" message. Now you get an itemized receipt showing exactly what you were charged for.

Two places in the game now show their receipts:

1. **The attack roll card** — when you roll to attack, the result card now shows a small line of math: what range band the shot was made at (e.g., "melee," or a weapon's real range like 100/600) and how many grid squares away the target was. Previously this information was calculated internally but never made it onto the screen.

2. **The tactical map** — a small chip now sits next to each character showing their movement budget for the round (cells used out of cells available), and a banner explains clearly when a move isn't allowed and why, instead of just silently refusing it.

Nothing about how combat or movement actually *works* changed — this is purely about surfacing math the game was already computing internally, so players can see it instead of taking it on faith.

## Why This Approach
The heavy lifting — actually calculating range, distance, and reach — was already built in a prior story that landed just before this one. This story didn't need to invent new math; it needed to carry numbers that already existed inside the engine out to the screen, like running a wire from a meter that was already reading correctly to a display the customer can actually see. That made this a low-risk, "plumbing" change rather than a new mechanic.

Worth calling out for confidence in the process: our review pipeline is deliberately adversarial. On the first pass, the team built the on-screen display correctly but had not yet connected it to the real data — the display existed, but nothing was feeding it live numbers yet, which would have shipped as a convincing-looking feature that quietly did nothing. Our review process caught this before release, sent it back for a second pass, and verified end-to-end that a real attack roll now produces a real number on screen before approving it. That's the system working as designed — catching "looks done" versus "is actually wired up" before it reaches players.

One known follow-up: the movement-budget chip's data pipeline still depends on a separate, already-tracked cleanup (a legacy storage reference used elsewhere in the map code) before it's reachable during real play. That fix is scoped as its own piece of work and doesn't block or risk this release — it only means the movement chip's wiring is proven correct but not yet "live" for players, while the attack-range math is live today.
