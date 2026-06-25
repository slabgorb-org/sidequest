# Plan A — `sidequest-seat-core` Extraction Implementation Plan

> ⚠️ **PARTIALLY REVERSED by story 159-6 (Keith, 2026-06-25).** The standalone-repo
> direction in this plan was undone: `seat_core` now lives **in-tree** inside
> `sidequest-understudy` (`sidequest-understudy/src/seat_core/`), the standalone
> `sidequest-seat-core` repo has been **deleted**, and there is **no
> `../sidequest-seat-core` uv path dependency** anywhere. Tasks below that scaffold
> a standalone repo, set up a uv path source, or "migrate understudy onto the path
> package" are historical — read them for the package's internal shape (modules,
> generic-over-output-model backends, the load-bearing invariants), not for its
> location or packaging. The **open question** this plan no longer answers: how the
> shipping companion (159-4/159-5) reaches `seat_core` now that it is inside the
> charter-bound understudy harness — companion-depends-on-understudy vs.
> seat_core-re-extracted. **Flagged for the Architect.**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract a charter-neutral `sidequest-seat-core` package (schema-generic model backends + a shared persona-axis model + the new role dial) out of `sidequest-understudy`, then migrate understudy onto it, leaving understudy's test suite green.

**Architecture:** The three LLM backends currently hardcode understudy's naive `Intent` (the ollama `format` schema, the anthropic `submit_intent` tool, the claude_p prompt shape). We generalize each backend over a **pydantic output model bound at construction**, so the same debugged code (anthropic prompt-caching, claude_p key-stripping, ollama JSON-format) serves both understudy's `Intent` and the companion's future `CompanionIntent`. The shared axis primitives (`SeatAxes`) and the new `RoleDial` move with it. understudy keeps its public brain API via thin shims so nothing downstream of it changes.

**Tech Stack:** Python 3.12, pydantic v2, `anthropic` SDK, `httpx`, `uv` (path source), `hatchling`, `pytest` + `pytest-asyncio`, `ruff`.

## Global Constraints

- Python `>=3.12`; pydantic v2; `ruff` line-length `100`, target `py312`.
- `pytest` `asyncio_mode = "auto"` (async tests need no decorator).
- New distribution package is `sidequest-seat-core`; import module is `seat_core`; `src/` layout; `hatchling` build.
- The core holds **data models + backends only** — no prompts, no naivety, no WebSocket, no browser.
- Every backend is **generic over a pydantic output model** bound at construction; structured output is forced at the API/runtime layer (anthropic tool, ollama `format`, claude_p schema-in-prompt) — never regex-parsed from prose.
- `ClaudePModel` MUST strip `ANTHROPIC_API_KEY` and `ANTHROPIC_ADMIN_KEY` from the child env (bills the plan, fails loud — never silently to API spend).
- `AnthropicModel` MUST cache the system prefix and meter **true** input volume (`input_tokens + cache_read + cache_creation`).
- After migration, `sidequest-understudy`'s full `pytest` run MUST pass unchanged in behavior.
- seat-core repo branch: work on `main` (new repo). understudy repo branch: create `feat/seat-core-migration` (understudy targets `develop`; never commit to it directly).

---

### Task 1: Scaffold the `sidequest-seat-core` package

**Files:**
- Create: `../sidequest-seat-core/pyproject.toml`
- Create: `../sidequest-seat-core/src/seat_core/__init__.py`
- Create: `../sidequest-seat-core/src/seat_core/llm/__init__.py`
- Create: `../sidequest-seat-core/src/seat_core/persona/__init__.py`
- Create: `../sidequest-seat-core/tests/__init__.py`
- Test: `../sidequest-seat-core/tests/test_smoke.py`

**Interfaces:**
- Produces: an importable `seat_core` package consumable as a uv path dependency at `../sidequest-seat-core`.

- [ ] **Step 1: Create the package directory and git repo**

Run (paths are relative to the orchestrator root `/Users/slabgorb/Projects/oq-1`):
```bash
mkdir -p sidequest-seat-core/src/seat_core/llm sidequest-seat-core/src/seat_core/persona sidequest-seat-core/tests
cd sidequest-seat-core && git init -q && cd -
```

- [ ] **Step 2: Write `pyproject.toml`**

Create `sidequest-seat-core/pyproject.toml`:
```toml
[project]
name = "sidequest-seat-core"
version = "0.1.0"
description = "Charter-neutral seat brain: schema-generic model backends + persona axes shared by understudy and the companion"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "anthropic>=0.40",
    "httpx>=0.27",
]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "ruff>=0.6"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/seat_core"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 3: Write the package `__init__.py` files**

Create `sidequest-seat-core/src/seat_core/__init__.py`:
```python
"""Charter-neutral seat brain shared by understudy (test harness) and the
companion (ships). Data models + model backends only — no prompts, no naivety,
no transport."""
```

Create `sidequest-seat-core/src/seat_core/llm/__init__.py` (empty):
```python
```

Create `sidequest-seat-core/src/seat_core/persona/__init__.py` (empty):
```python
```

Create `sidequest-seat-core/tests/__init__.py` (empty):
```python
```

- [ ] **Step 4: Write the smoke test**

Create `sidequest-seat-core/tests/test_smoke.py`:
```python
def test_package_imports():
    import seat_core

    assert seat_core.__doc__
```

- [ ] **Step 5: Sync and run the smoke test**

Run:
```bash
cd sidequest-seat-core && uv sync && uv run pytest tests/test_smoke.py -v
```
Expected: PASS (1 passed).

- [ ] **Step 6: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "chore: scaffold sidequest-seat-core package"
```

---

### Task 2: Core primitives — `Message`, `ModelError`, `DecideResult`, `parse_structured`, `StructuredModel`, `FakeStructuredModel`

**Files:**
- Create: `sidequest-seat-core/src/seat_core/core.py`
- Test: `sidequest-seat-core/tests/test_core.py`

**Interfaces:**
- Produces:
  - `Message(role: Literal["user","assistant"], content: str)` — frozen dataclass.
  - `ModelError(Exception)`.
  - `DecideResult(value: BaseModel, input_tokens: int, output_tokens: int)` — frozen dataclass.
  - `parse_structured(raw: str, model: type[BaseModel]) -> BaseModel` — fence-tolerant strict JSON → validated instance; `ModelError` on anything else.
  - `StructuredModel` protocol: `async decide(system: str, transcript: list[Message]) -> DecideResult`.
  - `FakeStructuredModel(script: list[BaseModel], default: BaseModel)`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_core.py`:
```python
from typing import Literal

import pytest
from pydantic import BaseModel

from seat_core.core import (
    DecideResult,
    FakeStructuredModel,
    Message,
    ModelError,
    parse_structured,
)


class Ping(BaseModel):
    kind: Literal["a", "b"]


def test_parse_structured_strict_json():
    assert parse_structured('{"kind": "a"}', Ping).kind == "a"


def test_parse_structured_tolerates_code_fence():
    assert parse_structured('```json\n{"kind": "b"}\n```', Ping).kind == "b"


def test_parse_structured_raises_on_prose():
    with pytest.raises(ModelError):
        parse_structured("I choose a!", Ping)


def test_parse_structured_raises_on_bad_shape():
    with pytest.raises(ModelError):
        parse_structured('{"kind": "z"}', Ping)  # not in Literal


async def test_fake_plays_script_then_default():
    fake = FakeStructuredModel([Ping(kind="a")], default=Ping(kind="b"))
    first = await fake.decide("sys", [Message(role="user", content="x")])
    assert isinstance(first, DecideResult)
    assert first.value.kind == "a"
    assert (first.input_tokens, first.output_tokens) == (0, 0)
    second = await fake.decide("sys", [])
    assert second.value.kind == "b"  # script exhausted → default forever
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.core'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/core.py`:
```python
"""Brain seam: the structured-decision protocol every backend implements.

Backends are generic over a pydantic output model bound at construction, so the
same code serves understudy's Intent and the companion's CompanionIntent. The
protocol returns DecideResult (value + token usage) so a run's token ledger can
meter API backends.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, ValidationError


class ModelError(Exception):
    """The model produced output that is not a valid instance of the target
    schema. Callers log this as a model failure — never a guess."""


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class DecideResult:
    value: BaseModel
    input_tokens: int
    output_tokens: int


class StructuredModel(Protocol):
    async def decide(self, system: str, transcript: list[Message]) -> DecideResult: ...


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_structured(raw: str, model: type[BaseModel]) -> BaseModel:
    """Strict JSON → validated model instance. Anything else is a ModelError."""
    cleaned = _FENCE.sub("", raw.strip()).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ModelError(f"model output is not JSON: {raw[:200]!r}") from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ModelError(f"model JSON is not a valid {model.__name__}: {exc}") from exc


class FakeStructuredModel:
    """Scripted brain for tests and wiring lanes. Zero tokens, zero LLM.
    Plays `script` in order, then returns `default` forever."""

    def __init__(self, script: list[BaseModel], default: BaseModel):
        self._script = list(script)
        self._default = default

    async def decide(self, system: str, transcript: list[Message]) -> DecideResult:
        value = self._script.pop(0) if self._script else self._default
        return DecideResult(value=value, input_tokens=0, output_tokens=0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest tests/test_core.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: core structured-decision primitives (generic over output model)"
```

---

### Task 3: `AnthropicModel` (generic over output model, with prompt caching)

**Files:**
- Create: `sidequest-seat-core/src/seat_core/llm/anthropic_model.py`
- Test: `sidequest-seat-core/tests/test_anthropic.py`

**Interfaces:**
- Consumes: `DecideResult`, `Message`, `ModelError` from `seat_core.core`.
- Produces: `AnthropicModel(model: str, output_model: type[BaseModel], client=None, tool_name: str = "submit")` with `async decide(...) -> DecideResult`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_anthropic.py`:
```python
import json
from typing import Literal

import anthropic
import httpx
from pydantic import BaseModel

from seat_core.core import Message
from seat_core.llm.anthropic_model import AnthropicModel


class Ping(BaseModel):
    kind: Literal["a", "b"]


def _transport(seen: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-4-5-20251001",
                "content": [
                    {"type": "tool_use", "id": "tu_1", "name": "submit", "input": {"kind": "b"}}
                ],
                "stop_reason": "tool_use",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "cache_read_input_tokens": 200,
                    "cache_creation_input_tokens": 30,
                },
            },
        )

    return httpx.MockTransport(handler)


async def test_anthropic_forces_tool_caches_prefix_and_meters_true_input():
    seen: dict = {}
    client = anthropic.AsyncAnthropic(
        api_key="test", http_client=httpx.AsyncClient(transport=_transport(seen))
    )
    model = AnthropicModel("claude-haiku-4-5-20251001", Ping, client=client)
    result = await model.decide("STABLE SYSTEM", [Message(role="user", content="screen")])

    assert result.value.kind == "b"
    assert seen["body"]["tools"][0]["input_schema"] == Ping.model_json_schema()
    assert seen["body"]["tool_choice"] == {"type": "tool", "name": "submit"}
    assert seen["body"]["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert seen["body"]["system"][0]["text"] == "STABLE SYSTEM"
    assert result.input_tokens == 10 + 200 + 30
    assert result.output_tokens == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_anthropic.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.llm.anthropic_model'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/llm/anthropic_model.py`:
```python
"""Anthropic SDK backend. The output shape is forced via a tool call so it is
validated at the API layer, not parsed from prose.

A seat's `system` prompt is byte-stable for the whole run, so it carries a
`cache_control` breakpoint: every turn re-reads the same cached prefix (tool
schema + system) at ~0.1x input cost. `input_tokens` reported to the ledger
sums cached and uncached input, so a token ceiling still bounds true work."""

from __future__ import annotations

import anthropic
from pydantic import BaseModel, ValidationError

from seat_core.core import DecideResult, Message, ModelError


class AnthropicModel:
    def __init__(
        self,
        model: str,
        output_model: type[BaseModel],
        client: anthropic.AsyncAnthropic | None = None,
        tool_name: str = "submit",
    ):
        self._model = model
        self._output_model = output_model
        self._tool_name = tool_name
        self._client = client or anthropic.AsyncAnthropic()
        self._tool = {
            "name": tool_name,
            "description": "Submit your structured decision.",
            "input_schema": output_model.model_json_schema(),
        }

    async def decide(self, system: str, transcript: list[Message]) -> DecideResult:
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": m.role, "content": m.content} for m in transcript],
            tools=[self._tool],
            tool_choice={"type": "tool", "name": self._tool_name},
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        if block is None:
            raise ModelError("anthropic response contained no tool_use block")
        try:
            value = self._output_model.model_validate(block.input)
        except ValidationError as exc:
            raise ModelError(
                f"tool input is not a valid {self._output_model.__name__}: {exc}"
            ) from exc
        usage = resp.usage
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
        return DecideResult(
            value=value,
            input_tokens=usage.input_tokens + cache_read + cache_creation,
            output_tokens=usage.output_tokens,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest tests/test_anthropic.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: AnthropicModel backend (generic output model + prompt caching)"
```

---

### Task 4: `OllamaModel` (generic over output model)

**Files:**
- Create: `sidequest-seat-core/src/seat_core/llm/ollama_model.py`
- Test: `sidequest-seat-core/tests/test_ollama.py`

**Interfaces:**
- Consumes: `DecideResult`, `Message`, `ModelError`, `parse_structured` from `seat_core.core`.
- Produces: `OllamaModel(model: str, output_model: type[BaseModel], host="http://localhost:11434", client=None)` with `async decide(...) -> DecideResult`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_ollama.py`:
```python
import json
from typing import Literal

import httpx
import pytest
from pydantic import BaseModel

from seat_core.core import Message, ModelError
from seat_core.llm.ollama_model import OllamaModel


class Ping(BaseModel):
    kind: Literal["a", "b"]


def _transport(reply: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body["stream"] is False
        assert body["format"]["properties"]["kind"]  # output schema passed
        return httpx.Response(200, json=reply)

    return httpx.MockTransport(handler)


async def test_ollama_decides_and_meters_tokens():
    reply = {
        "message": {"role": "assistant", "content": '{"kind": "a"}'},
        "prompt_eval_count": 100,
        "eval_count": 12,
    }
    model = OllamaModel("qwen3:8b", Ping, client=httpx.AsyncClient(transport=_transport(reply)))
    result = await model.decide("sys", [Message(role="user", content="screen")])
    assert result.value.kind == "a"
    assert (result.input_tokens, result.output_tokens) == (100, 12)


async def test_ollama_garbage_raises_model_error():
    reply = {"message": {"role": "assistant", "content": "lol no"}}
    model = OllamaModel("qwen3:8b", Ping, client=httpx.AsyncClient(transport=_transport(reply)))
    with pytest.raises(ModelError):
        await model.decide("sys", [Message(role="user", content="screen")])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_ollama.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.llm.ollama_model'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/llm/ollama_model.py`:
```python
"""Ollama backend — the zero-cost local lane. Uses /api/chat with a JSON-schema
`format` so structured output comes from the runtime, not regex."""

from __future__ import annotations

import httpx
from pydantic import BaseModel

from seat_core.core import DecideResult, Message, ModelError, parse_structured


class OllamaModel:
    def __init__(
        self,
        model: str,
        output_model: type[BaseModel],
        host: str = "http://localhost:11434",
        client: httpx.AsyncClient | None = None,
    ):
        self._model = model
        self._output_model = output_model
        self._host = host.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=300.0)

    async def decide(self, system: str, transcript: list[Message]) -> DecideResult:
        payload = {
            "model": self._model,
            "stream": False,
            "format": self._output_model.model_json_schema(),
            "messages": [
                {"role": "system", "content": system},
                *({"role": m.role, "content": m.content} for m in transcript),
            ],
        }
        resp = await self._client.post(f"{self._host}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ModelError(f"ollama response missing message content: {data!r:.300}") from exc
        value = parse_structured(content, self._output_model)
        return DecideResult(
            value=value,
            input_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest tests/test_ollama.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: OllamaModel backend (generic output model)"
```

---

### Task 5: `ClaudePModel` (generic, schema-in-prompt, key-stripping)

**Files:**
- Create: `sidequest-seat-core/src/seat_core/llm/claude_p_model.py`
- Test: `sidequest-seat-core/tests/test_claude_p.py`

**Interfaces:**
- Consumes: `DecideResult`, `Message`, `ModelError`, `parse_structured` from `seat_core.core`.
- Produces: `ClaudePModel(model: str, output_model: type[BaseModel])` with `async decide(...) -> DecideResult`; module-level `_API_KEY_VARS` and `_plan_env()`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_claude_p.py`:
```python
from seat_core.llm.claude_p_model import _API_KEY_VARS, _plan_env


def test_claude_p_scrubs_api_keys_from_child_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-leak")
    monkeypatch.setenv("ANTHROPIC_ADMIN_KEY", "sk-ant-admin")
    monkeypatch.setenv("PATH", "/usr/bin")  # ordinary vars survive
    env = _plan_env()
    for var in _API_KEY_VARS:
        assert var not in env, f"{var} would route claude -p to API billing"
    assert env["PATH"] == "/usr/bin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_claude_p.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.llm.claude_p_model'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/llm/claude_p_model.py`:
```python
"""`claude -p` subprocess backend. One-shot; no token metering (reported zeros).

To bill the operator's plan (the point of this backend) the subprocess must NOT
see an API key — `claude -p` prefers ANTHROPIC_API_KEY over subscription OAuth
and would otherwise bill the metered API. We strip the key from the child env:
with a subscription login it bills the plan; with none it fails loud."""

from __future__ import annotations

import asyncio
import json
import os

from pydantic import BaseModel

from seat_core.core import DecideResult, Message, ModelError, parse_structured

# Env vars that, if inherited, would silently route claude -p to API billing.
_API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_ADMIN_KEY")


def _plan_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _API_KEY_VARS}


class ClaudePModel:
    def __init__(self, model: str, output_model: type[BaseModel]):
        self._model = model
        self._output_model = output_model

    async def decide(self, system: str, transcript: list[Message]) -> DecideResult:
        convo = "\n\n".join(f"[{m.role}]\n{m.content}" for m in transcript)
        schema = json.dumps(self._output_model.model_json_schema())
        prompt = (
            f"{system}\n\n{convo}\n\n"
            "Reply with ONLY a JSON object matching this schema — no prose:\n"
            f"{schema}"
        )
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            "-",
            "--output-format",
            "json",
            "--model",
            self._model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_plan_env(),
        )
        stdout, stderr = await proc.communicate(prompt.encode())
        if proc.returncode != 0:
            raise ModelError(f"claude -p exited {proc.returncode}: {stderr.decode()[:300]}")
        try:
            envelope = json.loads(stdout.decode())
        except json.JSONDecodeError as exc:
            raise ModelError(f"claude -p emitted non-JSON envelope: {exc}") from exc
        value = parse_structured(str(envelope.get("result", "")), self._output_model)
        return DecideResult(value=value, input_tokens=0, output_tokens=0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest tests/test_claude_p.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: ClaudePModel backend (generic, schema-in-prompt, key-stripping)"
```

---

### Task 6: `make_model` factory

**Files:**
- Create: `sidequest-seat-core/src/seat_core/llm/factory.py`
- Test: `sidequest-seat-core/tests/test_factory.py`

**Interfaces:**
- Consumes: `StructuredModel`, `FakeStructuredModel` from `seat_core.core`; the three backends.
- Produces: `make_model(spec: str, output_model: type[BaseModel], *, default: BaseModel | None = None) -> StructuredModel`. Spec form `"<backend>/<model-id>"` or bare `"fake"`. `"fake"` requires `default`. Unknown backend raises `ValueError`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_factory.py`:
```python
from typing import Literal

import pytest
from pydantic import BaseModel

from seat_core.llm.factory import make_model


class Ping(BaseModel):
    kind: Literal["a", "b"]


def test_factory_dispatches_by_prefix(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")  # AsyncAnthropic() needs a key at construct
    assert type(make_model("anthropic/claude-haiku-4-5-20251001", Ping)).__name__ == "AnthropicModel"
    assert type(make_model("ollama/qwen3:8b", Ping)).__name__ == "OllamaModel"
    assert type(make_model("claude_p/haiku", Ping)).__name__ == "ClaudePModel"
    assert type(make_model("fake", Ping, default=Ping(kind="a"))).__name__ == "FakeStructuredModel"


def test_factory_fake_requires_default():
    with pytest.raises(ValueError, match="fake backend requires a default"):
        make_model("fake", Ping)


def test_factory_fails_loud_on_unknown_backend():
    with pytest.raises(ValueError, match="unknown model backend"):
        make_model("bard/gpt-1", Ping)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_factory.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.llm.factory'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/llm/factory.py`:
```python
"""Per-seat model factory. Spec form '<backend>/<model-id>' (e.g.
'anthropic/claude-haiku-4-5-20251001', 'ollama/qwen3:8b', 'claude_p/haiku')
or bare 'fake'. Unknown backend = loud failure."""

from __future__ import annotations

from pydantic import BaseModel

from seat_core.core import FakeStructuredModel, StructuredModel
from seat_core.llm.anthropic_model import AnthropicModel
from seat_core.llm.claude_p_model import ClaudePModel
from seat_core.llm.ollama_model import OllamaModel


def make_model(
    spec: str, output_model: type[BaseModel], *, default: BaseModel | None = None
) -> StructuredModel:
    backend, _, model_id = spec.partition("/")
    match backend:
        case "anthropic":
            return AnthropicModel(model_id, output_model)
        case "ollama":
            return OllamaModel(model_id, output_model)
        case "claude_p":
            return ClaudePModel(model_id or "haiku", output_model)
        case "fake":
            if default is None:
                raise ValueError("fake backend requires a default value")
            return FakeStructuredModel([], default)
        case _:
            raise ValueError(f"unknown model backend: {spec!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest tests/test_factory.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: make_model factory (generic over output model)"
```

---

### Task 7: Persona axes — `SeatAxes`, `Role`, `RoleDial`

**Files:**
- Create: `sidequest-seat-core/src/seat_core/persona/axis.py`
- Test: `sidequest-seat-core/tests/test_axis.py`

**Interfaces:**
- Produces:
  - `Level = Literal["low","medium","high"]`.
  - `SeatAxes(BaseModel)` with `narrative_vs_mechanical: float (0..1)`, `verbosity: Level`, `decisiveness: Level`, `reading_tolerance: Level`; `extra="forbid"`.
  - `Role(StrEnum)`: `PET="pet"`, `PEER="peer"`, `HIRELING="hireling"`.
  - `RoleDial(BaseModel)` with `role: Role` and property `perception_scope -> "owner_private"|"party"|"public"`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-seat-core/tests/test_axis.py`:
```python
import pytest
from pydantic import ValidationError

from seat_core.persona.axis import Role, RoleDial, SeatAxes


def test_seat_axes_validate_bounds():
    a = SeatAxes(
        narrative_vs_mechanical=0.85, verbosity="low", decisiveness="high", reading_tolerance="medium"
    )
    assert a.narrative_vs_mechanical == 0.85


def test_seat_axes_reject_out_of_range():
    with pytest.raises(ValidationError):
        SeatAxes(
            narrative_vs_mechanical=1.5, verbosity="low", decisiveness="high", reading_tolerance="low"
        )


def test_role_dial_perception_scope():
    assert RoleDial(role=Role.PET).perception_scope == "owner_private"
    assert RoleDial(role=Role.PEER).perception_scope == "party"
    assert RoleDial(role=Role.HIRELING).perception_scope == "public"


def test_role_rejects_unknown():
    with pytest.raises(ValidationError):
        RoleDial(role="sidekick")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-seat-core && uv run pytest tests/test_axis.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seat_core.persona.axis'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-seat-core/src/seat_core/persona/axis.py`:
```python
"""Persona axes shared by any seated player-agent.

SeatAxes are behavior/attention dials true of a naive playtest bot AND a
companion. The role dial adds the companion's autonomy/bond axis and the
perception scope it implies. No prompts here — consumers build prompts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["low", "medium", "high"]


class SeatAxes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    narrative_vs_mechanical: float = Field(ge=0.0, le=1.0)  # 0 = narrative, 1 = crunch
    verbosity: Level
    decisiveness: Level
    reading_tolerance: Level


class Role(StrEnum):
    PET = "pet"
    PEER = "peer"
    HIRELING = "hireling"


_PERCEPTION_SCOPE: dict[Role, str] = {
    Role.PET: "owner_private",
    Role.PEER: "party",
    Role.HIRELING: "public",
}


class RoleDial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role

    @property
    def perception_scope(self) -> str:
        """What the server should let this companion see about its human:
        owner_private (pet), party (peer), public (hireling)."""
        return _PERCEPTION_SCOPE[self.role]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-seat-core && uv run pytest -v`
Expected: PASS (all seat-core tests green — 14 passed across the suite).

- [ ] **Step 5: Commit**

```bash
cd sidequest-seat-core && git add -A && git commit -q -m "feat: shared SeatAxes + Role/RoleDial persona axes"
```

---

### Task 8: Wire understudy onto seat-core (path dep + shims; delete moved backends)

**Files:**
- Modify: `sidequest-understudy/pyproject.toml`
- Modify: `sidequest-understudy/src/understudy/brain/core.py` (becomes a shim)
- Modify: `sidequest-understudy/src/understudy/brain/llm/factory.py` (becomes a shim)
- Delete: `sidequest-understudy/src/understudy/brain/llm/anthropic_model.py`
- Delete: `sidequest-understudy/src/understudy/brain/llm/ollama_model.py`
- Delete: `sidequest-understudy/src/understudy/brain/llm/claude_p_model.py`
- Delete: `sidequest-understudy/tests/test_backends.py`

**Interfaces:**
- Consumes: `seat_core` package (Tasks 1–7).
- Produces: `understudy.brain.core` re-exporting `Message, ModelError, DecideResult, ActionModel`, plus `parse_intent(raw) -> Intent` and `FakeActionModel(script)`. `understudy.brain.llm.factory.make_model(spec) -> ActionModel`.

- [ ] **Step 1: Create the understudy feature branch**

Run:
```bash
cd sidequest-understudy && git checkout -b feat/seat-core-migration
```

- [ ] **Step 2: Add the path dependency**

In `sidequest-understudy/pyproject.toml`, change the `dependencies` list: remove `"anthropic>=0.40"` (the SDK is now used only by seat-core) and add `"sidequest-seat-core"`. The block becomes:
```toml
dependencies = [
    "playwright>=1.49",
    "httpx>=0.27",
    "pydantic>=2.7",
    "typer>=0.12",
    "pyyaml>=6.0",
    "sidequest-seat-core",
]
```
Then add this block immediately after the `[project.scripts]` block:
```toml
[tool.uv.sources]
sidequest-seat-core = { path = "../sidequest-seat-core", editable = true }
```

- [ ] **Step 3: Replace `brain/core.py` with a shim**

Replace the entire contents of `sidequest-understudy/src/understudy/brain/core.py` with:
```python
"""Brain seam (shim). The structured-decision primitives now live in
seat_core; understudy binds them to its naive Intent. parse_intent and
FakeActionModel preserve understudy's public API so no caller changed."""

from __future__ import annotations

from seat_core.core import (  # noqa: F401  (re-exported for understudy callers)
    DecideResult,
    Message,
    ModelError,
    StructuredModel as ActionModel,
    parse_structured,
)
from seat_core.core import FakeStructuredModel

from understudy.types import Intent, IntentKind


def parse_intent(raw: str) -> Intent:
    """Strict JSON → Intent. Anything else is a ModelError — never a guess."""
    return parse_structured(raw, Intent)  # type: ignore[return-value]


class FakeActionModel(FakeStructuredModel):
    """Scripted Intent brain — script then WAIT forever (understudy default)."""

    def __init__(self, script: list[Intent]):
        super().__init__(list(script), default=Intent(kind=IntentKind.WAIT))
```

- [ ] **Step 4: Replace `brain/llm/factory.py` with a shim**

Replace the entire contents of `sidequest-understudy/src/understudy/brain/llm/factory.py` with:
```python
"""Per-seat model factory (shim). Binds seat_core's generic factory to
understudy's Intent. 'fake' returns understudy's FakeActionModel so its type
identity is preserved for callers that check it."""

from __future__ import annotations

from seat_core.llm.factory import make_model as _make_model

from understudy.brain.core import ActionModel, FakeActionModel
from understudy.types import Intent


def make_model(spec: str) -> ActionModel:
    if spec == "fake":
        return FakeActionModel([])
    return _make_model(spec, Intent)
```

- [ ] **Step 5: Delete the moved backend modules and superseded test**

Run:
```bash
cd sidequest-understudy && git rm -q \
  src/understudy/brain/llm/anthropic_model.py \
  src/understudy/brain/llm/ollama_model.py \
  src/understudy/brain/llm/claude_p_model.py \
  tests/test_backends.py
```

- [ ] **Step 6: Sync the environment**

Run:
```bash
cd sidequest-understudy && uv sync
```
Expected: resolves and installs `sidequest-seat-core` from the path source.

- [ ] **Step 7: Commit**

```bash
cd sidequest-understudy && git add -A && git commit -q -m "refactor: depend on sidequest-seat-core; shim brain backends"
```

---

### Task 9: Update understudy read sites + tests + Archetype; prove the suite green

**Files:**
- Modify: `sidequest-understudy/src/understudy/orchestrate/seat.py:134`
- Modify: `sidequest-understudy/src/understudy/persona/model.py`
- Modify: `sidequest-understudy/tests/test_brain_core.py`
- Modify: `sidequest-understudy/tests/test_seat_loop.py:84`

**Interfaces:**
- Consumes: `DecideResult.value` (renamed from `.intent`); `seat_core.persona.axis.SeatAxes`.
- Produces: `understudy.persona.model.Archetype` now subclasses `SeatAxes` (same YAML field set).

- [ ] **Step 1: Update the seat loop read site**

In `sidequest-understudy/src/understudy/orchestrate/seat.py`, line 134, change:
```python
                intent = result.intent
```
to:
```python
                intent = result.value
```

- [ ] **Step 2: Make `Archetype` subclass `SeatAxes`**

Replace the entire contents of `sidequest-understudy/src/understudy/persona/model.py` with:
```python
"""Play-style archetypes — the playgroup as test matrix.

An archetype shapes BEHAVIOR AND ATTENTION, not knowledge: a mechanics_first
bot does not know the dice tray exists — it wants it to exist and goes
looking. 'Looked and could not find' is the per-user-type finding the
instrument exists to produce.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from seat_core.persona.axis import Level, SeatAxes

_ARCHETYPE_DIR = Path(__file__).parent / "archetypes"


class Archetype(SeatAxes):
    id: str
    affordance_hunger: Level
    prompt_fragment: str


def load_archetype(archetype_id: str) -> Archetype:
    path = _ARCHETYPE_DIR / f"{archetype_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no archetype {archetype_id!r} at {path}")
    return Archetype.model_validate(yaml.safe_load(path.read_text()))


def load_all_archetypes() -> dict[str, Archetype]:
    return {p.stem: load_archetype(p.stem) for p in sorted(_ARCHETYPE_DIR.glob("*.yaml"))}
```

- [ ] **Step 3: Update `test_brain_core.py` to the `.value` field**

Replace the entire contents of `sidequest-understudy/tests/test_brain_core.py` with:
```python
import pytest

from understudy.brain.core import (
    DecideResult,
    FakeActionModel,
    Message,
    ModelError,
    parse_intent,
)
from understudy.types import Intent, IntentKind


def test_parse_intent_strict_json():
    raw = '{"kind": "act", "target_role": "button", "target_name": "Send"}'
    assert parse_intent(raw).kind is IntentKind.ACT


def test_parse_intent_tolerates_code_fence():
    raw = '```json\n{"kind": "wait"}\n```'
    assert parse_intent(raw).kind is IntentKind.WAIT


def test_parse_intent_raises_model_error_on_garbage():
    with pytest.raises(ModelError):
        parse_intent("I attack the goblin!")


def test_parse_intent_raises_model_error_on_bad_shape():
    with pytest.raises(ModelError):
        parse_intent('{"kind": "act"}')  # act without target


async def test_fake_model_plays_script_then_waits():
    script = [Intent(kind=IntentKind.ACT, target_role="button", target_name="Send")]
    fake = FakeActionModel(script)
    first = await fake.decide("sys", [Message(role="user", content="screen")])
    assert isinstance(first, DecideResult)
    assert first.value.kind is IntentKind.ACT
    assert (first.input_tokens, first.output_tokens) == (0, 0)
    second = await fake.decide("sys", [])
    assert second.value.kind is IntentKind.WAIT  # script exhausted → wait forever
```

- [ ] **Step 4: Update the `CostlyFake` rebuild in `test_seat_loop.py`**

In `sidequest-understudy/tests/test_seat_loop.py`, line 84, change:
```python
            return type(result)(intent=result.intent, input_tokens=600, output_tokens=0)
```
to:
```python
            return type(result)(value=result.value, input_tokens=600, output_tokens=0)
```

- [ ] **Step 5: Run the full understudy suite**

Run:
```bash
cd sidequest-understudy && uv run pytest -q
```
Expected: PASS (all tests green; the suite no longer contains `test_backends.py`).

- [ ] **Step 6: Lint both repos**

Run:
```bash
cd sidequest-seat-core && uv run ruff check . && cd ../sidequest-understudy && uv run ruff check .
```
Expected: no errors in either.

- [ ] **Step 7: Commit**

```bash
cd sidequest-understudy && git add -A && git commit -q -m "refactor: migrate read sites + Archetype to seat-core; suite green"
```

---

## Self-Review

**Spec coverage:** Plan A implements the spec's "Component B — `sidequest-seat-core` (extracted, charter-neutral)" and the "explicit decision — protocol types" prerequisite that the backends be schema-generic so the companion can bind `CompanionIntent`. The role dial (`Role`/`RoleDial`) and shared `SeatAxes` from Section 1/2 are delivered in Task 7. v1/v2 boundary respected — no persistence, perception, or WS here.

**Placeholder scan:** No TBD/TODO; every code step shows complete file contents or an exact line change.

**Type consistency:** `DecideResult.value` used consistently (core, all three backends, fake, understudy read sites, tests). `make_model(spec, output_model, *, default=None)` signature matches its one understudy caller via the shim. `SeatAxes` field set equals the union consumed by `Archetype` (narrative_vs_mechanical, verbosity, decisiveness, reading_tolerance) plus Archetype's own (id, affordance_hunger, prompt_fragment) — equal to the original Archetype fields, so existing archetype YAML still validates.

**Ambiguity check:** Shared-core packaging resolved to a uv path source at `../sidequest-seat-core` (the spec's open decision). `"fake"` default-value requirement made explicit in the factory.
