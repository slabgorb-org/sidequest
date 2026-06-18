# Narrative

## Problem Statement
**Problem:** A June 16th infrastructure upgrade accidentally turned on an AI "extended thinking" mode for the game's narrator, making every player turn take roughly three times longer than normal — responses that used to arrive in about 20 seconds were now taking 60–70 seconds.

**Why it matters:** SideQuest is a real-time multiplayer RPG. A 3× latency spike means players sit staring at a loading screen where they used to be talking to each other. For the target audience — Alex (who needs a patient, inclusive pace) and Jade/Sebastien (who crave fast mechanical feedback) — a 50-second wait per turn breaks immersion and undermines the core promise of the game. This was a p1 issue filed the same day it landed.

---

## What Changed
The narrator is the AI "game master" that reads every player's action and writes the story response. It runs on Claude (Anthropic's AI), which has two modes: a normal mode where it just answers, and an "extended thinking" mode where it privately works through a problem before answering — like showing your work on a math test, except you're paying for it and waiting for it.

When the team upgraded the narrator to a newer, cleaner SDK (software toolkit) in PR #908, that SDK silently defaulted to extended thinking **on**. The old SDK had it **off**. Because the narrator calls the AI up to eight times per turn (once per tool call in the game loop), that hidden thinking pass multiplied across eight iterations — burning 50+ seconds where 16 were needed.

The fix was one line of code: explicitly tell the SDK "thinking is disabled" rather than accepting whatever the default happens to be. No quality cut — the narrator was excellent *without* extended thinking from day one; this restores the long-tested baseline.

A regression guard (automated test) was also added. It will fail the build if anyone ever accidentally re-enables thinking on the narrator, so this can't silently come back.

---

## Why This Approach
Three options existed:
1. **Cap the tool-loop iterations** — fewer AI calls per turn. This would have cut latency but also cut narration quality. Rejected.
2. **Disable extended thinking explicitly** — one kwarg, zero quality loss, exact restore. Chosen.
3. **Revert PR #908 entirely** — throws away a valuable infrastructure upgrade to fix a side effect. Not worth it.

Option 2 is the minimum effective dose. The explicit disable kwarg also future-proofs the code: if someone later decides extended thinking *should* be used for something (it might genuinely help a slow, deep planning step), they can enable it deliberately and measurably — not by accident via a framework default.

---

## Before/After
| Metric | Before (regression — June 16) | After (fix — June 18) |
|---|---|---|
| Narrator `agent_duration_ms` | ~50,000–57,000 ms | ~16,000 ms |
| Total turn time (non-Fate) | ~60–70s | ~20–25s |
| Extended thinking mode | ON (SDK default, accidental) | OFF (explicit `{"type":"disabled"}`) |
| Thinking passes per turn | Up to 8 (one per tool-loop iteration) | 0 |
| Regression guard | None | Unit test in CI; build fails on re-enable |
| Example world (wry_whimsy/oz) | 56.7s | ~16s (baseline restored) |
| Code delta | — | 1 kwarg + 1 docstring + 1 test assertion |

**The narrator's output quality is unchanged.** Extended thinking was never part of the shipped product — the baseline was always thinking-off, and the system was well-tuned to it. The regression introduced thinking accidentally; the fix removes the accident.
