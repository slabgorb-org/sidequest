# Narrative

## Problem Statement
**Problem:** Two test files for the "opening point-of-view" feature were left with 38 type errors flagged by our automated code-quality checker (Pyright). **Why it matters:** Type errors in test files aren't just noise — they can mask real bugs, confuse future developers, and erode the quality signal that the type checker provides. When everything is an error, nothing is an error. Cleaning the slate restores the checker's ability to catch *real* problems as development continues.

---

## What Changed
Think of a spell-checker on a document that has 38 red underlines. This story removed all 38, without changing a single word of meaning — only the formatting and annotations around those words.

Specifically:
- **Two test files** (for the character point-of-view and event emission features) went from **38 type errors to zero**.
- No game logic changed. No test assertions changed. All 10 tests pass exactly as before.
- No production source code was touched — this was purely a housekeeping pass on the test files.

The fixes fell into three categories:
1. **Better labels** — telling the checker "this list contains `NarrationMessage` objects, not just generic objects."
2. **Safety assertions** — adding `assert sd is not None` before accessing fields, so the checker (and the runtime) know the value is guaranteed to exist.
3. **Targeted suppressions** — for two cases where the checker is technically wrong (a known alias pattern in our message protocol), we added precise, narrow "ignore this specific issue on this specific line" markers rather than blanket silencing.

---

## Why This Approach
The goal was to fix errors with real solutions wherever possible, and use surgical suppression only where a real fix would require touching production code (which is out of scope for a 1-point hygiene story).

**Real fixes first:** Where we could add an annotation or a safety check without changing behavior, we did. This is the right answer — it makes the code clearer and the type-check meaningful.

**Targeted suppression last resort:** Two categories needed suppression:
- The `visibility_sidecar` alias pattern — a genuine Pyright false positive. Our protocol message models use field aliases (the Python field is `_visibility`, but the serialized name is `visibility_sidecar`). Pyright sees a call with a parameter name it can't find, but the code is correct. We suppress this with a precise, labeled comment.
- The `handle_message` argument type — the production function signature says it accepts a `GameMessage` wrapper, but all callers (correctly, at runtime) pass the inner message directly. Fixing this would require editing production code, which this story explicitly prohibits. We suppressed in test, and filed a dedicated delivery finding for a follow-up story.

This approach means every suppression is:
- On one specific line
- Carries a specific error code
- Is documented in the session as a deliberate, reasoned choice

---

## Before/After
| Dimension | Before | After |
|---|---|---|
| Pyright errors | **38** across 2 files | **0** |
| Pyright warnings | 0 | 0 |
| Tests passing | 10/10 | 10/10 |
| Production files modified | — | 0 |
| Suppression comments | 0 (errors unaddressed) | 16 targeted, all with specific codes |
| Narrowing asserts | 0 | 5 (`assert sd/handler is not None`) |
| Type annotations improved | 0 | 1 (`list[object]` → `list[NarrationMessage]`) |
| Checker signal quality | Low (38 errors = everything is noise) | High (0 errors = every new error is real) |

**Representative before (line 77, `test_opening_pov_swap_71_5.py`):**
```python
# No guard — pyright flags access below as reportOptionalMemberAccess
sd = game_state.solo_data
sd.pov_character_id = "char_1"  # ERROR: sd could be None
```

**Representative after:**
```python
sd = game_state.solo_data
assert sd is not None  # narrowing: guarantees sd is SoloData here
sd.pov_character_id = "char_1"  # clean
```

**Representative before (visibility_sidecar false-positive):**
```python
CharacterCreationMessage(visibility_sidecar="public")  # ERROR: No parameter named "visibility_sidecar"
```

**Representative after:**
```python
CharacterCreationMessage(visibility_sidecar="public")  # pyright: ignore[reportCallIssue]
# ^^ Pydantic alias (_visibility → visibility_sidecar), populate_by_name=True. Genuine FP.
```
