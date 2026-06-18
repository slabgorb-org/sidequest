# Demo Script — Story 119-6

## Scene 1: Setup (30 sec)

**Presenter says:** "Problem: 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked.. Why it matters: the codebase needed restructuring for maintainability."

**Show:** The state of the system before the refactor

## Scene 2: Act 1 (2 min)

**Presenter says:** "We implemented: 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked.."

**Show:** ## Demo Script — 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked.

### Scene 1: Setup (30 sec)
**Presenter says:** "Today we're going to show you what we built for 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked.."
**Show:** The project overview

### Scene 2: Demo (1 min)
**Presenter says:** "Let me show you the changes."
**Show:** The implementation in action

### Scene 3: Closing (30 sec)
**Presenter says:** "That's 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked. — shipped and verified."

## Scene 3: Act 2 (1 min)

**Presenter says:** "Before: The existing implementation had grown complex and difficult to maintain.
After: 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed. _AsideLlm.complete, _IntentRouterLlm.emit_tool, _UnseededObjectiveClassifierLlm.emit_tool, and infer_archetype_from_freeform (llm_factory.py) each repeat the same skeleton — pre-flight ceiling check -> build_agent_sdk_options -> llm_request_span + _consume_to_result + _record_usage_telemetry -> record_call -> structured_output extract/raise. Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (the verify-phase simplify-reuse high-confidence findings, ~40 lines saved). STRUCTURAL-ONLY, no behavior change: the existing agents suite (1993 passed) must stay green, and each site keeps its distinct caller tag, model, and loud error type. Deferred from 119-3 verify per story-scope minimal-diff / single-commit-rollback (Architect spec-check affirmed the then-current factoring); safe to do now the swap has soaked. — the code is now cleaner, more modular, and easier to extend."

**Show:** The improvements after the refactor

## Scene 4: Closing (30 sec)

**Presenter says:** "The refactor is complete and the system is cleaner and faster."

**Show:** Final comparison of before and after