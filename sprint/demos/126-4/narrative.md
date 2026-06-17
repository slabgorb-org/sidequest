# Narrative

## Problem Statement
**Problem:** In a two-player SideQuest session, when one player submitted their action, the other player could not reliably see what their partner had typed — even though they were both waiting at the same moment for the round to resolve. The text would only appear *after* the round was over, not during the suspenseful WAIT window when seeing your partner's move could help the table coordinate. The failure was intermittent (~50% of turns), which made it feel random and confusing.

**Why it matters:** The ability to see what your partner just submitted — before the narrator resolves the scene — is a core multiplayer social contract. It replaces the feeling of "whispering your action to the DM behind a screen" with the collaborative energy of a table where everyone can see the cards going down. When this breaks, players feel isolated and confused mid-turn. For Keith's playgroup specifically (where Alex may need extra time and the table benefits from coordinated actions), this failure actively degrades the group experience.

---

## What Changed
Think of it like a whiteboard at a table-top game. When a player announces their action, that announcement goes up on the whiteboard so everyone can see it while waiting for the DM to respond. Before this fix, the whiteboard only had one marker — and if that marker was knocked off the table during a fast, confident move (a player typing quickly and hitting Enter without a pause), the announcement was gone. Everyone would see the "✓ Submitted" checkmark, but the whiteboard was blank.

The fix adds a second, more reliable marker. The server now keeps a backup copy of every player's submitted action in an authoritative log. When the status update goes out to all players at the table, it carries that backup text along with it. The display logic then checks: "do I already have this player's text from the first marker? If yes, use it. If not, pull it from the backup." Result: the whiteboard is always filled in, whether the first marker made it or not.

---

## Why This Approach
The intermittency turned out to be deterministic, not random. It depended on *how fast* a player typed. A deliberate typist would emit a "composing" event that also carried their text — giving the system two chances to deliver it. A fast typist who pasted text and hit Enter skipped that event entirely, leaving a single delivery window that could be dropped under normal network churn. There was no way to "fix the delivery guarantee" for that single window — network drops are real.

The right fix was to stop relying on best-effort delivery for something that needs to be reliable. The server already had the text buffered (it uses it to resolve the round). This change makes that buffer do double duty: the text rides the same *authoritative* status broadcast that already reliably tells every client "this player is sealed." The sealed-status channel never drops; now the text travels with it.

This pattern is consistent with how the rest of the multiplayer coordination layer works — authoritative events carry the ground truth, best-effort events are optimistic fast-paths. The text joins the authoritative channel where it belongs.

---
