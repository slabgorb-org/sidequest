# Intent Router Output-Slim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the Intent Router's per-turn latency (p50 ~8.6s, tail ~26s) by shrinking the `DispatchPackage` it generates down to the fields actually consumed pre-narration.

**Architecture:** Latency is 0.94-correlated with output tokens (single-shot, zero-retry — measured 2026-06-20). The router emits a `DispatchPackage` that accreted fields nothing reads. We remove the dead/redundant fields (`resolved[]`, `action_rewrite.you`, the router's `lethality[]`), make `VisibilityTag` server-defaulted instead of model-emitted, reorder fields so the narrator-critical bytes generate first, and rewrite the system prompt to stop instructing the cut fields. Server-only; no UI, no new LLM call. Spec: `docs/superpowers/specs/2026-06-20-intent-router-output-slim-design.md`.

**Tech Stack:** Python 3, Pydantic v2, pytest (`uv run pytest`, parallel by default), Anthropic SDK (Haiku classifier), Jaeger (span capture for verification).

## Global Constraints

- **Repo:** `sidequest-server` only. Branch from `develop` (`feat/intent-router-output-slim`); PRs target `develop` (github-flow).
- **No Silent Fallbacks / No Stubbing** (CLAUDE.md). Stripping a *deliberately removed* field is normalization (logged), not a silent fallback — mirror the existing `_coerce_stringified_lists` doctrine.
- **`ProtocolBase` has `extra="forbid"`** — removing a schema field means a straggler from the model rejects the whole package unless explicitly stripped first.
- **No Source-Text Wiring Tests** (CLAUDE.md): assert on behavior/spans, never on prompt/source string matches as a wiring proof.
- **Keep:** `confidence_global`, per-dispatch `confidence` + its gate, all existing validators (`_coerce_stringified_lists`, `_unique_idempotency_keys`, `CrossAction._witnesses_include_participants`), `LethalityVerdict`/`LethalityVerdictKind`/`Reversibility` classes (the arbiter + `genre/models/lethality.py` use them).
- **Run tests:** `cd sidequest-server && uv run pytest <path> -v`. Lint/format: `uv run ruff check . && uv run ruff format .`.

---

## File Structure

- `sidequest/protocol/dispatch.py` — the output contract. Cut fields, reorder, server-default visibility, strip stragglers. (Tasks 1, 2)
- `sidequest/protocol/__init__.py` — drop the `Referent` re-export. (Task 1)
- `sidequest/agents/lethality_arbiter.py` — remove the merge loop that read the cut router `lethality`. (Task 3)
- `sidequest/agents/intent_router.py` — rewrite `_SYSTEM_PROMPT`: drop the referent-resolution step, the visibility mandate, and `action_rewrite.you`. (Task 4)
- Tests: `tests/protocol/test_dispatch.py`, `tests/agents/test_intent_router.py`, `tests/agents/test_lethality_arbiter*.py` (the arbiter test home — find via grep in Task 3).
- Verification: `scenarios/latency_diag_82_9.yaml` + Jaeger (Task 5).

---

### Task 1: Reshape the output contract — cut dead fields, reorder, tolerate stragglers

**Files:**
- Modify: `sidequest/protocol/dispatch.py` (remove `Referent` 101-115; `PlayerDispatch.resolved` 204 + `PlayerDispatch.lethality` 206; `ActionRewrite.you` 265-267; reorder `PlayerDispatch` + `DispatchPackage` fields; add straggler-strip validators; update `__all__` 400-413)
- Modify: `sidequest/protocol/__init__.py` (remove `Referent` from import 34 + `__all__` 152)
- Test: `tests/protocol/test_dispatch.py`

**Interfaces:**
- Produces: `PlayerDispatch` with fields `dispatch`, `narrator_instructions`, `player_id`, `raw_action` (no `resolved`, no `lethality`). `ActionRewrite` with `named`, `intent` only. `DispatchPackage` order: `per_player`, `cross_player`, `confidence_global`, `action_rewrite`, `turn_id`. A raw input dict carrying `resolved`/`lethality`/`you` validates with those keys silently dropped (logged once).
- Consumes: nothing new.

- [ ] **Step 1: Write failing tests for the new shape + straggler tolerance**

Add to `tests/protocol/test_dispatch.py`:

```python
import logging
from sidequest.protocol.dispatch import (
    ActionRewrite,
    DispatchPackage,
    PlayerDispatch,
    SubsystemDispatch,
)


def test_player_dispatch_has_no_resolved_or_lethality_fields():
    assert "resolved" not in PlayerDispatch.model_fields
    assert "lethality" not in PlayerDispatch.model_fields


def test_action_rewrite_has_no_you_field():
    assert "you" not in ActionRewrite.model_fields
    assert set(ActionRewrite.model_fields) == {"named", "intent"}


def test_referent_is_removed():
    import sidequest.protocol.dispatch as d
    assert not hasattr(d, "Referent")


def test_straggler_resolved_lethality_are_stripped_not_rejected(caplog):
    # Haiku may still emit removed fields out of habit; extra="forbid" must
    # not reject the package — the deprecated keys are dropped + logged.
    raw = {
        "player_id": "player:alice",
        "raw_action": "hit the goblin",
        "resolved": [{"token": "the goblin", "resolved_to": "npc:g1", "confidence": 0.9}],
        "lethality": [{"entity": "npc:g1", "verdict": "defeated", "cause": "x",
                       "reversibility": "permanent", "narrator_directive": "y",
                       "soul_md_constraint": "z"}],
        "dispatch": [],
    }
    with caplog.at_level(logging.INFO):
        pd = PlayerDispatch.model_validate(raw)
    assert not hasattr(pd, "resolved")
    assert "dispatch_package.stripped_deprecated" in caplog.text


def test_straggler_action_rewrite_you_is_stripped():
    ar = ActionRewrite.model_validate(
        {"you": "You draw", "named": "Alice draws", "intent": "draw sword"}
    )
    assert ar.named == "Alice draws"
    assert ar.intent == "draw sword"


def test_dispatch_package_field_order_dispatch_critical_first():
    # Field declaration order drives the emitted JSON-schema property order,
    # which drives generation order (the latency lever). per_player first.
    fields = list(DispatchPackage.model_fields)
    assert fields[0] == "per_player"
    assert fields.index("action_rewrite") > fields.index("per_player")
    pd_fields = list(PlayerDispatch.model_fields)
    assert pd_fields[0] == "dispatch"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_dispatch.py -v -k "resolved or lethality or you or referent or straggler or field_order"`
Expected: FAIL (fields still present; `Referent` still exists; stragglers raise `ValidationError`).

- [ ] **Step 3: Remove `Referent`, cut fields, reorder, add straggler strip**

In `sidequest/protocol/dispatch.py`:

(a) Delete the entire `Referent` class (lines ~101-115) and its `# Referent resolution` banner.

(b) Replace the `PlayerDispatch` class (lines ~201-207) with the reordered, slimmed version + a straggler-strip validator:

```python
class PlayerDispatch(ProtocolBase):
    # Field order = JSON-schema property order = generation order. The
    # dispatch list is the only narrator-blocking output, so it leads.
    dispatch: list[SubsystemDispatch] = Field(default_factory=list)
    narrator_instructions: list[NarratorDirective] = Field(default_factory=list)
    player_id: str
    raw_action: str

    @model_validator(mode="before")
    @classmethod
    def _strip_deprecated(cls, data: Any) -> Any:
        """Drop fields the contract removed (Story: output-slim).

        ``resolved`` (referent list) and ``lethality`` were emitted but never
        read (the dispatches carry resolved names in ``params``; the
        LethalityArbiter computes its own HP=0 verdicts). They are removed from
        the schema, but Haiku may still emit them out of habit — and
        ``extra="forbid"`` would reject the whole package. Strip-and-log,
        same normalize-don't-reject doctrine as ``_coerce_stringified_lists``.
        """
        if isinstance(data, dict):
            dropped = [k for k in ("resolved", "lethality") if k in data]
            for k in dropped:
                data.pop(k, None)
            if dropped:
                logger.info(
                    "dispatch_package.stripped_deprecated fields=%s", ",".join(dropped)
                )
        return data
```

(c) Replace `ActionRewrite` (lines ~253-276) — drop the `you` field and add the same strip:

```python
class ActionRewrite(ProtocolBase):
    """The player's own action rewritten into two perspectives consumed
    pre-narration. ``named`` (third person w/ acting character) feeds
    visibility_classifier; ``intent`` (neutral, no pronouns) feeds the
    confrontation-intent lie-detector. ADR-150 §1.
    """

    named: str = Field(default="", description="Third person w/ the acting character's name.")
    intent: str = Field(default="", description="Neutral distilled intent, no pronouns.")

    @model_validator(mode="before")
    @classmethod
    def _strip_deprecated(cls, data: Any) -> Any:
        """Drop the removed ``you`` field if the model still emits it."""
        if isinstance(data, dict) and "you" in data:
            data.pop("you", None)
            logger.info("dispatch_package.stripped_deprecated fields=you")
        return data
```

(d) In `DispatchPackage` (lines ~284-301), reorder fields so `per_player` leads and `action_rewrite` trails. Keep `confidence_global` and `action_rewrite` (both still required/optional as before). The declaration order becomes: `per_player`, `cross_player`, `confidence_global`, `action_rewrite`, `turn_id`.

(e) In `__all__` (lines ~400-413): remove `"Referent"`. Keep `LethalityVerdict`, `LethalityVerdictKind`, `Reversibility` (used by the arbiter + genre models).

In `sidequest/protocol/__init__.py`: remove `Referent` from the import block (line ~34) and from `__all__` (line ~152).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_dispatch.py -v`
Expected: PASS (new tests green; existing dispatch tests still green — if an existing test constructs `Referent` or `PlayerDispatch(resolved=...)`, update it to the new shape).

- [ ] **Step 5: Commit**

```bash
git add sidequest/protocol/dispatch.py sidequest/protocol/__init__.py tests/protocol/test_dispatch.py
git commit -m "feat(intent-router): slim DispatchPackage — cut resolved/lethality/you, reorder, strip stragglers"
```

---

### Task 2: Make `VisibilityTag` server-defaulted instead of model-emitted

**Files:**
- Modify: `sidequest/protocol/dispatch.py` (`SubsystemDispatch.visibility` line ~131; `NarratorDirective.visibility` line ~165)
- Test: `tests/protocol/test_dispatch.py`

**Interfaces:**
- Produces: `SubsystemDispatch` and `NarratorDirective` validate with `visibility` omitted, defaulting to `VisibilityTag(visible_to="all")`. Consumers reading `.visibility.redact_from_narrator_canonical` (`prompt_redaction.py:41,47,73`) and `entry.visibility` (`visibility_classifier.py:169`) keep working — the field is always a `VisibilityTag`, never `None`.

- [ ] **Step 1: Write the failing test**

Add to `tests/protocol/test_dispatch.py`:

```python
from sidequest.protocol.dispatch import NarratorDirective, SubsystemDispatch, VisibilityTag


def test_subsystem_dispatch_visibility_defaults_to_all_when_omitted():
    d = SubsystemDispatch.model_validate(
        {"subsystem": "confrontation", "idempotency_key": "k1", "confidence": 0.9}
    )
    assert d.visibility.visible_to == "all"
    assert d.visibility.redact_from_narrator_canonical is False


def test_narrator_directive_visibility_defaults_to_all_when_omitted():
    n = NarratorDirective.model_validate({"kind": "must_narrate", "payload": "x"})
    assert n.visibility.visible_to == "all"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_dispatch.py -v -k "visibility_defaults"`
Expected: FAIL (`visibility` is currently required → `ValidationError`).

- [ ] **Step 3: Add the default_factory**

In `sidequest/protocol/dispatch.py`, change the `visibility` field on `SubsystemDispatch` (line ~131) and `NarratorDirective` (line ~165) from required to:

```python
    visibility: VisibilityTag = Field(
        default_factory=lambda: VisibilityTag(visible_to="all"),
        description=(
            "Server-defaulted to 'all'; the model emits this ONLY for genuinely "
            "asymmetric visibility (a secret seen by some PCs and not others)."
        ),
    )
```

- [ ] **Step 4: Run to verify pass + no consumer regression**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_dispatch.py tests/agents/test_dispatch_engagement_watcher.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/protocol/dispatch.py tests/protocol/test_dispatch.py
git commit -m "feat(intent-router): VisibilityTag is server-defaulted, model emits only for secrets"
```

---

### Task 3: Remove the lethality-arbiter merge loop (read the now-gone router field)

**Files:**
- Modify: `sidequest/agents/lethality_arbiter.py` (the `# Merge decomposer-authored verdicts` loop, ~lines 99-105; docstring line ~18)
- Test: the arbiter's test (find with `grep -rl "LethalityArbiter\|arbitrate(" tests/`)

**Interfaces:**
- Consumes: `DispatchPackage` (now without `per_player[].lethality`).
- Produces: `arbitrate()` returns `LethalityResult` whose verdicts come solely from the deterministic HP=0 path (`_emit`). Paired `must_narrate`/`must_not_narrate` directives unchanged — the death-RP "belt" is untouched.

- [ ] **Step 1: Write/Update the failing test**

First locate the arbiter test: `grep -rln "LethalityArbiter\|arbitrate(" tests/`. In that file (create `tests/agents/test_lethality_arbiter_no_merge.py` if none asserts this), add:

```python
from sidequest.agents.lethality_arbiter import LethalityArbiter
from sidequest.agents.subsystems import BankResult
from sidequest.protocol.dispatch import DispatchPackage, PlayerDispatch
# build a minimal LethalityPolicy via the genre loader/fixtures already used by
# the existing arbiter test — reuse that fixture, do not hand-roll the policy.


def test_arbiter_emits_hp_zero_verdict_without_router_lethality(lethality_policy, downed_npc_core):
    # The deterministic HP=0 path still fires; the router no longer supplies lethality.
    pkg = DispatchPackage(
        turn_id="t1",
        per_player=[PlayerDispatch(player_id="player:alice", raw_action="strike")],
        confidence_global=0.9,
    )
    result = LethalityArbiter(policy=lethality_policy).arbitrate(
        package=pkg,
        bank_result=BankResult(),
        pc_cores_by_player={},
        npc_cores_by_name={"goblin": downed_npc_core},  # hp.current == 0
    )
    entities = {v.entity for v in result.verdicts}
    assert "npc:goblin" in entities  # HP=0 belt fired
    # and the paired must_narrate / must_not_narrate directives are present
    kinds = {d.kind for d in result.directives}
    assert "must_narrate" in kinds and "must_not_narrate" in kinds
```

(Reuse the existing arbiter test's policy/core fixtures — match their names. If the existing test already covers HP=0 emission, this task is just deleting the merge loop and confirming that test still passes.)

- [ ] **Step 2: Run to verify current state**

Run: `cd sidequest-server && uv run pytest <arbiter_test_path> -v`
Expected: the HP=0 test passes today (the belt already works); proceed to remove the dead merge.

- [ ] **Step 3: Delete the merge loop**

In `sidequest/agents/lethality_arbiter.py`, remove the block:

```python
            # Merge decomposer-authored verdicts. Arbiter wins on entity
            # conflict; decomposer-only entities pass through.
            arbiter_entities = {v.entity for v in result.verdicts}
            for pd in package.per_player:
                for decomposer_v in pd.lethality:
                    if decomposer_v.entity not in arbiter_entities:
                        result.verdicts.append(decomposer_v)
```

Keep the `span.set_attribute("verdict_count", len(result.verdicts))` and `return result` lines. Update the module docstring (line ~18) that says the decomposer "may still emit `LethalityVerdict` entries" — note the router no longer emits lethality; the arbiter is sole source.

- [ ] **Step 4: Run to verify pass**

Run: `cd sidequest-server && uv run pytest <arbiter_test_path> tests/integration/test_group_c_e2e.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/agents/lethality_arbiter.py <arbiter_test_path>
git commit -m "refactor(lethality): drop arbiter merge of cut router lethality field; HP=0 belt is sole source"
```

---

### Task 4: Rewrite the system prompt — drop referent step, visibility mandate, action_rewrite.you

**Files:**
- Modify: `sidequest/agents/intent_router.py` (`_SYSTEM_PROMPT`, lines ~133-318)
- Test: `tests/agents/test_intent_router.py`

**Interfaces:**
- Produces: a prompt that no longer instructs referent resolution, no longer mandates a visibility tag per dispatch, and describes `action_rewrite` as `{named, intent}` only. The forced tool/output schema (derived from the slimmed `DispatchPackage`) already excludes the cut fields.

- [ ] **Step 1: Update the prompt fixture + behavior tests**

In `tests/agents/test_intent_router.py`, the `haiku_response_pronoun_resolved` fixture (line ~44) emits `resolved`, `lethality`, and a per-dispatch `visibility`. Update it to the new shape: drop `resolved` and `lethality`; omit `visibility` (now server-defaulted). Update `test_intent_router_decompose_returns_dispatch_package` (line ~147): replace the `pkg.per_player[0].resolved[0]` assertion (line ~172) with an assertion on a dispatch (e.g. `pkg.per_player[0].dispatch` or `pkg.action_rewrite.intent`). Add:

```python
async def test_prompt_omits_referent_resolution_step(make_intent_router):
    router = make_intent_router()
    prompt = router._system_prompt  # or the module-level _SYSTEM_PROMPT
    assert "Resolve referents" not in prompt
    assert "action_rewrite" in prompt and '"you"' not in prompt
```

(Match the existing tests' access pattern for the prompt — reuse whatever `test_intent_router_prompt_documents_*` at lines 203/247/284 already use to reach the prompt text. This asserts the *contract surface the model sees*, not a wiring proof.)

- [ ] **Step 2: Run to verify failure**

Run: `cd sidequest-server && uv run pytest tests/agents/test_intent_router.py -v`
Expected: FAIL (fixture still has `resolved`/`lethality`; prompt still says "Resolve referents" and shows `"you"`).

- [ ] **Step 3: Rewrite `_SYSTEM_PROMPT`**

In `sidequest/agents/intent_router.py`:
- Remove numbered **step 1 "Resolve referents…"** (lines ~140-144) entirely; renumber the remaining steps.
- In **step 5 action_rewrite** (lines ~304-310): change the description + example to two perspectives only — `{"named": "Kael draws their sword", "intent": "draw sword"}`. Delete the `"you"` perspective and the `"You draw your sword"` example.
- Replace the **visibility paragraph** (lines ~312-313, "Every dispatch carries a visibility tag. Default visible_to=all…") with: `Visibility is server-defaulted to "all". Emit a visibility tag ONLY when an action is genuinely secret (seen by some PCs and not others); otherwise omit it.`
- Leave the subsystem `params` contract, confrontation/opponent rules, confidence scoring, and `FATE_ROUTING_RULES` unchanged.

- [ ] **Step 4: Run to verify pass**

Run: `cd sidequest-server && uv run pytest tests/agents/test_intent_router.py tests/corpus/test_router_corpus.py -v`
Expected: PASS. (If a `test_intent_router_prompt_documents_*` test referenced a removed instruction, update its assertion to the new prompt.)

- [ ] **Step 5: Lint + commit**

```bash
cd sidequest-server && uv run ruff check . && uv run ruff format .
git add sidequest/agents/intent_router.py tests/agents/test_intent_router.py
git commit -m "feat(intent-router): slim system prompt — drop referent step, visibility mandate, action_rewrite.you"
```

---

### Task 5: Verify — latency win + zero-regression (the lie-detector)

**Files:** none (measurement task). Server must be running with Jaeger up (`localhost:16686`).

**Interfaces:**
- Consumes: the merged Tasks 1-4.
- Produces: a before/after latency report and a clean mismatch-span check, recorded in the PR description.

- [ ] **Step 1: Capture the AFTER latency sample**

Restart the server so the new code + prompt load (cold prompt cache). Then:

```bash
cd sidequest-server && uv run --with rich python3 ../scripts/playtest.py \
  --scenario ../scenarios/latency_diag_82_9.yaml \
  --span-jsonl /tmp/latency_after.spans.jsonl --no-contact-sheet \
  --max-projected-cost-usd 1.00
```

- [ ] **Step 2: Compute the percentiles and compare to baseline**

Query Jaeger for `intent_router.decompose` (and `llm.request` filtered to `llm.caller=intent_router`) over the run; compute `output_tokens` and `latency_ms` p50/p95/max. Baseline (2026-06-20): output p50 314 tok; latency p50 8.6s / p95 18.4s / max 26.6s.
Expected: output p50 roughly halved (~150 tok); latency p50 down to ~4–5s; the 15–26s tail crushed.

- [ ] **Step 3: Regression — assert zero NEW mismatch spans (the existing lie-detector)**

Run a combat scenario before/after and compare `dispatch_engagement.{subsystem}.mismatch` span counts + dispatch counts:

```bash
cd sidequest-server && uv run --with rich python3 ../scripts/playtest.py \
  --scenario ../scenarios/combat_otel.yaml \
  --span-jsonl /tmp/combat_after.spans.jsonl --no-contact-sheet --max-projected-cost-usd 1.00
```

Then grep the captured spans: count `dispatch_engagement.*.mismatch`. Expected: **no new mismatch spans vs. a pre-change baseline run**, and identical dispatch counts on equivalent turns. Drive at least one pronoun-heavy action ("hit him with it") to prove no consumer depended on the removed `resolved[]` list.

- [ ] **Step 4: Record results in the PR**

Paste the before/after percentile table and the mismatch-span counts into the PR description as the verification evidence (no code change).

---

## Self-Review

- **Spec coverage:** cut `resolved[]` (T1), `action_rewrite.you` (T1), router `lethality[]` (T1) + arbiter merge (T3); `VisibilityTag` defaultable (T2); field reorder (T1); prompt rewrite (T4); keep `confidence_global` + gate + validators (T1 constraints); verify via Jaeger + mismatch regression (T5). All spec items mapped.
- **`extra="forbid"` hazard:** addressed by the straggler-strip validators (T1) — the one non-obvious failure mode, covered with a test.
- **Type consistency:** `LethalityVerdict`/`LethalityVerdictKind`/`Reversibility` retained (arbiter + `genre/models/lethality.py` import them); only `Referent` removed (sole consumer was the cut `resolved` field) with its `protocol/__init__.py` re-export fixed. `ActionRewrite` → `{named, intent}`; consumers read `.named`/`.intent` only (`.you` had no consumer).
- **No placeholders:** every code step shows real code; the two "find the test file via grep" steps (arbiter test in T3, prompt-access pattern in T4) are explicit grep commands, not vague references, because the exact filename must be confirmed at execution.
