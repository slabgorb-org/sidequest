# Story Context: 117-6 Un-seeded Narrator-Objective Classifier

## Story Overview

**ID:** 117-6
**Title:** Un-seeded narrator-objective classifier — detect open-ended objective-giving in narration without a keyword list
**Points:** 8
**Type:** Feature/Enhancement (TDD)
**Repos:** sidequest-server

## Problem Statement

### Current State (117-4 aftermath)
- Story 117-4 hardened only the SEEDED path (intent router `quest_offer` signal) with real mechanical detection
- The UN-SEEDED fallback still uses a brittle 13-phrase hardcoded substring matcher (`_UNMINTED_OBJECTIVE_MARKERS` in `dispatch_engagement_watcher.py:100-114`)
- This keyword list is the Zork verb-set anti-pattern: tries to recognize open-ended natural language with curated phrases
- A noir "discreet job" hook (e.g., "I have a situation...") trips NONE of the 13 markers, so the lie-detector stays silent
- Result: `narration.unminted_objective.suspected` OTEL span never fires on improvised (non-seeded) objectives

### Root Cause
- The intent router is PRE-NARRATION and PLAYER-TURN-SCOPED, so it has NO signal for a narrator-initiated objective (no pending_quest_offer to detect acceptance of)
- An un-seeded hook is pure prose improvisation with no structured quest_seed behind it
- Catching this requires a POST-NARRATION micro-pass (a real classifier, not keyword matching) that can examine the narration text itself

## Acceptance Criteria

### AC-1: Un-seeded Objective Detection (Real Classification)
- Implement a post-narration pass that classifies whether the narrator gave an open-ended objective
- The pass must NOT rely on `_UNMINTED_OBJECTIVE_MARKERS` substring matching
- Approach: a lightweight Haiku classification (similar to intent router) that takes:
  - Narration text (the narrator's response)
  - Game state context (no pending quest_offer present → signals un-seeded)
  - Character/NPC context
  - And outputs a binary decision: "objective-given" vs "no objective"
- Must handle examples like "I have a... situation. Someone of mine has stopped checking in."

### AC-2: OTEL Span Routing
- The `narration.unminted_objective.suspected` span MUST emit on un-seeded objective detection
- Span already exists in SPAN_ROUTES (wired in 117-4), route must be verified
- Span carries metrics: detection_method (e.g., "classifier" vs "keyword"), confidence if applicable

### AC-3: Keyword Matcher Deprecation Path
- Retain `_UNMINTED_OBJECTIVE_MARKERS` as a provisional fallback (don't delete yet; other code may reference it)
- Add a deprecation comment with ADR-146 pointer
- Mark the keyword path as non-primary in dispatch_engagement_watcher.py
- Prefer the new classifier path; keyword match is emergency backstop only

### AC-4: Cost Analysis (ADR-146 Addendum)
- Document the cost of a per-turn post-narration classification:
  - Cost-Scales-with-Drama (longer narration = more tokens to classify)
  - Typical cost: Haiku full-output (1K context, ~200 tokens, ~$0.001 per call)
  - Compare to keyword matching (free, but brittle)
- Update ADR-146 with rationale: brittleness of keywords justifies the cost
- Recommend: activate classifier for multi-turn objectives (stakes > X) or always-on if drama tier permits

### AC-5: Wiring Test (MUST PASS)
- Fixture-driven test: craft a narration with an un-seeded objective hook (noir example)
- No pending_quest_offer in game state
- Fire the post-narration pass
- Assert `narration.unminted_objective.suspected` span emits with detection_method="classifier"
- Wiring test: verify the pass is actually called from websocket_session_handler.py (not just unit-testable)

## Technical Approach

### 1. New Classifier Module
**File:** `sidequest/agents/post_narration_classifier.py` (new)

```python
@dataclass(frozen=True)
class UnseededObjectiveClassification:
    """Output of un-seeded objective detection."""
    is_objective_given: bool
    confidence: float  # 0.0-1.0
    reasoning: str | None  # for OTEL/debugging
    
async def classify_unseeded_objective(
    narration: str,
    game_state: GameState,
    has_pending_quest_offer: bool,
) -> UnseededObjectiveClassification:
    """
    Post-narration classifier: detect open-ended objective-giving
    in narration when no quest_offer is pending (un-seeded).
    
    Uses Haiku (lightweight, fast) via the Anthropic SDK.
    """
```

### 2. Integration Point
**File:** `sidequest/server/websocket_session_handler.py` (modify)

After narrator runs and narration is prepared for emission:
```python
if not game_state.pending_quest_offers:  # Un-seeded scenario
    classification = await classify_unseeded_objective(
        narration=narration_text,
        game_state=game_state,
        has_pending_quest_offer=bool(game_state.pending_quest_offers),
    )
    if classification.is_objective_given:
        emit_span("narration.unminted_objective.suspected", 
                  detection_method="classifier",
                  confidence=classification.confidence,
                  reasoning=classification.reasoning)
```

### 3. OTEL Span Routing
**File:** `sidequest/telemetry/spans/narration.py` (verify/enhance)

- Span `narration.unminted_objective.suspected` must be routed to the typed SPAN_ROUTES feed
- Add optional fields: `detection_method` (enum: "classifier" | "keyword"), `confidence` (float)
- GM panel shows the method and confidence so reviewers know if keyword fallback fired

### 4. Deprecation / Keyword Fallback
**File:** `sidequest/agents/dispatch_engagement_watcher.py` (modify lines 100-114, 674, 704)

- Keep `_UNMINTED_OBJECTIVE_MARKERS` but add deprecation comment:
  ```python
  # DEPRECATED (ADR-146): Keyword matcher is superseded by post-narration
  # classifier (117-6). Retained as emergency fallback for edge cases.
  # Prefer narration.unminted_objective.suspected via classifier.
  ```
- In `detect_unminted_objective()`, add conditional:
  ```python
  if detection_method == "classifier":
      return classification.is_objective_given
  else:  # keyword fallback
      return any(marker in lowered for marker in _UNMINTED_OBJECTIVE_MARKERS)
  ```

### 5. Test Structure

**Unit Tests:** `tests/agents/test_unseeded_objective_classifier.py`
- Test Haiku prompt + response parsing
- Test classification on noir / open-ended hooks
- Test cost (token estimation, not actual calls)
- Test edge cases: empty narration, context-less objective, multiple objectives

**Integration/Wiring Test:** `tests/server/test_unseeded_objective_wiring.py`
- Fixture: game state with NO pending_quest_offers
- Fire websocket_session_handler with noir-style narration
- Assert OTEL span `narration.unminted_objective.suspected` emitted
- Assert detection_method="classifier"

## Dependencies & Blockers

- **No blockers.** Story 117-4 provides the lie-detector infrastructure and SPAN_ROUTES routing.
- Relies on: ADR-146 (quest-seed contract, done), ADR-113 (intent router, live/partial)

## Cost Estimate (ADR-146 Addendum)

| Scenario | Cost | Frequency | Annual |
|----------|------|-----------|--------|
| Per-turn classifier (always-on) | $0.001/call | ~10 per session | ~$36 per 100 sessions |
| Keyword fallback (current, free) | $0 | N/A | $0 |
| **Classifier (Drama >= High)** | $0.001/call | ~3 per session | ~$11 per 100 sessions |

**Recommendation:** Enable classifier on multi-turn objectives or drama scaling. For baseline playtest, always-on is acceptable (< $0.01 per session).

## References

- **ADR-146:** Quest-Seed Authoring Contract (accepted, 2026-06-14)
- **ADR-113:** Intent Router (live/partial)
- **Story 117-4:** Harden the unminted-objective lie-detector (approved, 2026-06-14)
- **Span route:** `sidequest/telemetry/spans/quests.py` + SPAN_ROUTES
- **Related code:**
  - `sidequest/agents/dispatch_engagement_watcher.py:591` (detect_unminted_objective)
  - `sidequest/agents/intent_router.py:348` (IntentRouter template)
  - `sidequest/server/websocket_session_handler.py` (turn dispatch)
