# Understudy Reconnect via Persisted Browser State — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let understudy bot seats reconnect to a session they already created — skipping chargen — by persisting and restoring each seat's browser localStorage, exactly the way a returning player's browser does.

**Architecture:** Every run automatically snapshots each bot seat's Playwright `storage_state()` into `<report-dir>/state/seat-{idx}.json`. A new `--reconnect <DIR>` flag rebuilds each bot seat's context with `new_context(storage_state=<DIR>/state/seat-{idx}.json)`; the restored `sidequest-history` localStorage surfaces the one-click resume entry, which the naive bot clicks to rejoin past chargen. No server, UI, or `seat.py` changes — the perceive/decide/act loop is identity-agnostic. All work is in `sidequest-understudy`.

**Tech Stack:** Python 3.14, Playwright (async), Typer CLI, pydantic v2 manifest, pytest (`uv run pytest`).

---

## Source of truth & spec

Design spec: `docs/superpowers/specs/2026-06-12-understudy-reconnect-browser-state-design.md` (approved, pre-plan).

## Repo / branch

Single repo: `sidequest-understudy`. Branch + PR to its base branch per `repos.yaml` (github-flow `develop`). All paths below are relative to the `sidequest-understudy/` repo root.

## Spec deviations baked into this plan (read before starting)

1. **No Playwright fake exists.** The spec's Testing §3 says "with the existing injection seams (a Playwright fake + `model_factory`)". This repo has **no** Playwright fake — `tests/wiring/test_full_loop.py` and `tests/conftest.py` drive a **real** headless chromium against a local `file://` fixture. The faithful, reuse-first equivalent of "assert `new_context` receives `storage_state`" is a **pure helper**, `reconnect_context_kwargs(reconnect, idx) -> dict`, that produces exactly the kwargs `new_context` is called with. We unit-test that helper directly (Task 1) and assert the real save path with a real browser (Task 4). This mirrors the spec's own "single `seat_state_path` helper" instinct — one place owns the convention.

2. **`write_report` resolves the run dir internally today**, but the state snapshot must land in that same dir *before* `browser.close()` (you need the live context). Rather than reorder everything, Task 3 makes the run dir **injectable** (`run_dir: Path | None = None`, default preserves current behavior) so `run_table` resolves it up front, saves state into it, then hands it to `write_report`. Existing `test_report.py` calls stay green untouched.

## File structure

New:
- `src/understudy/orchestrate/reconnect.py` — pure path/kwargs/validation helpers (single source of the `state/seat-{idx}.json` convention).
- `tests/test_reconnect.py` — unit tests for the helpers + the fail-loud run_table guard.
- `tests/wiring/test_reconnect_state.py` — real-browser save-wiring test.

Modified:
- `src/understudy/report/write.py` — rename `_next_run_dir` → public `resolve_run_dir`; add `run_dir` param to `write_report`.
- `src/understudy/orchestrate/run.py` — `reconnect` param; restore kwargs on `new_context`; keep context handles; save state after `gather`; resolve run dir up front.
- `src/understudy/cli.py` — `--reconnect` option; catch `ManifestError` from `run_table` → exit 2.
- `tests/test_cli.py` — extend the two `fake_run_table` stubs with the `reconnect` kwarg; add a `--reconnect` threading test.
- `tests/test_report.py` — add a `run_dir` passthrough test.

No justfile change: the orchestrator recipe `understudy manifest *flags` (`justfile:581`) already forwards `--reconnect <dir>`.

## Test command

Run from repo root: `uv run pytest -q` (single test: `uv run pytest tests/test_reconnect.py::test_seat_state_path -v`). Wiring tests need Playwright's chromium installed (already the case — `test_full_loop.py` uses it).

---

### Task 1: Reconnect path + context-kwargs helpers

**Files:**
- Create: `src/understudy/orchestrate/reconnect.py`
- Test: `tests/test_reconnect.py`

- [ ] **Step 1: Write the failing tests (path + kwargs)**

Create `tests/test_reconnect.py`:

```python
from pathlib import Path

import pytest

from understudy.manifest import ManifestError
from understudy.orchestrate.reconnect import (
    reconnect_context_kwargs,
    seat_state_path,
    validate_reconnect_dir,
)


def test_seat_state_path_uses_state_subdir():
    d = Path("reports/2026-06-12-demo-r1")
    assert seat_state_path(d, 1) == d / "state" / "seat-1.json"
    assert seat_state_path(d, 3) == d / "state" / "seat-3.json"


def test_context_kwargs_empty_when_not_reconnecting():
    assert reconnect_context_kwargs(None, 1) == {}


def test_context_kwargs_carry_storage_state_path():
    d = Path("reports/run1")
    assert reconnect_context_kwargs(d, 2) == {
        "storage_state": str(d / "state" / "seat-2.json")
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_reconnect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'understudy.orchestrate.reconnect'`.

- [ ] **Step 3: Write the helper module**

Create `src/understudy/orchestrate/reconnect.py`:

```python
"""Browser-state reconnect helpers.

Persisting a bot seat's localStorage lets a later run rejoin its character past
chargen — the same way a returning player's browser would. These are the pure
path/kwargs/validation helpers; the live save/restore calls live in run.py. The
``state/seat-{idx}.json`` convention lives here and nowhere else.
"""

from __future__ import annotations

from pathlib import Path

from understudy.manifest import ManifestError


def seat_state_path(report_dir: Path, idx: int) -> Path:
    """The storage_state file for seat ``idx`` under a run's report dir."""
    return report_dir / "state" / f"seat-{idx}.json"


def reconnect_context_kwargs(reconnect: Path | None, idx: int) -> dict:
    """kwargs for ``browser.new_context()``.

    Restores seat ``idx``'s saved state when reconnecting, empty otherwise. This
    is the seam the wiring asserts on: exactly what ``new_context`` receives.
    """
    if reconnect is None:
        return {}
    return {"storage_state": str(seat_state_path(reconnect, idx))}


def validate_reconnect_dir(reconnect: Path, bot_seat_indices: list[int]) -> None:
    """Fail loud before any browser launches.

    The dir, its ``state/`` subdir, and a ``seat-{idx}.json`` for every bot seat
    must all exist. No silent fall-through to chargen (No Silent Fallbacks).
    Raises ManifestError (usage class — CLI maps it to exit 2).
    """
    if not reconnect.exists():
        raise ManifestError(f"--reconnect dir does not exist: {reconnect}")
    if not (reconnect / "state").is_dir():
        raise ManifestError(f"--reconnect dir has no state/ subdir: {reconnect}")
    for idx in bot_seat_indices:
        p = seat_state_path(reconnect, idx)
        if not p.is_file():
            raise ManifestError(
                f"--reconnect: missing browser state for seat {idx}: {p}"
            )
```

- [ ] **Step 4: Run tests to verify path + kwargs pass**

Run: `uv run pytest tests/test_reconnect.py -v`
Expected: the three tests written so far PASS (validation tests are added in Task 2).

- [ ] **Step 5: Commit**

```bash
git add src/understudy/orchestrate/reconnect.py tests/test_reconnect.py
git commit -m "feat(reconnect): seat_state_path + context-kwargs helpers"
```

---

### Task 2: Fail-loud reconnect validation

**Files:**
- Modify: `src/understudy/orchestrate/reconnect.py` (already has `validate_reconnect_dir` from Task 1)
- Test: `tests/test_reconnect.py`

- [ ] **Step 1: Write the failing validation tests**

Append to `tests/test_reconnect.py`:

```python
def test_validate_raises_when_dir_missing(tmp_path):
    with pytest.raises(ManifestError, match="does not exist"):
        validate_reconnect_dir(tmp_path / "ghost", [1])


def test_validate_raises_when_state_subdir_missing(tmp_path):
    with pytest.raises(ManifestError, match="no state/"):
        validate_reconnect_dir(tmp_path, [1])


def test_validate_names_the_missing_seat(tmp_path):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "seat-1.json").write_text("{}")
    with pytest.raises(ManifestError, match="seat 2"):
        validate_reconnect_dir(tmp_path, [1, 2])


def test_validate_passes_when_all_seat_files_present(tmp_path):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "seat-1.json").write_text("{}")
    validate_reconnect_dir(tmp_path, [1])  # no raise
```

- [ ] **Step 2: Run tests to verify they pass**

`validate_reconnect_dir` already exists from Task 1, so these should pass immediately — this task is the explicit fail-loud coverage the spec's Testing §2 requires.

Run: `uv run pytest tests/test_reconnect.py -v`
Expected: all seven tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_reconnect.py
git commit -m "test(reconnect): fail-loud validation covers missing dir/state/seat"
```

---

### Task 3: Make the run dir injectable in `write_report`

**Files:**
- Modify: `src/understudy/report/write.py:21-28` (`_next_run_dir`), `:59-67` (`write_report` signature/body)
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing passthrough test**

Append to `tests/test_report.py` (it already imports `write_report` and defines `_manifest()`):

```python
def test_write_report_uses_injected_run_dir(tmp_path):
    out_dir = tmp_path / "premade-r1"
    out_dir.mkdir()
    out = write_report(
        tmp_path, _manifest(), [], [], spans=None, spans_error=None, run_dir=out_dir
    )
    assert out == out_dir
    assert (out_dir / "report.md").exists()
    assert (out_dir / "findings.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_report.py::test_write_report_uses_injected_run_dir -v`
Expected: FAIL — `write_report() got an unexpected keyword argument 'run_dir'`.

- [ ] **Step 3: Rename `_next_run_dir` → `resolve_run_dir` and add the `run_dir` param**

In `src/understudy/report/write.py`, rename the helper (make it public) — change the definition at line 21:

```python
def resolve_run_dir(root: Path, name: str) -> Path:
    today = datetime.date.today().isoformat()
    n = 1
    while (root / f"{today}-{name}-r{n}").exists():
        n += 1
    out = root / f"{today}-{name}-r{n}"
    out.mkdir(parents=True)
    return out
```

Change the `write_report` signature and its first body line (lines 59-67) to:

```python
def write_report(
    out_root: Path,
    manifest: RunManifest,
    rows: list[TranscriptRow],
    findings: list[Finding],
    spans: list[dict] | None,
    spans_error: str | None,
    run_dir: Path | None = None,
) -> Path:
    out = run_dir if run_dir is not None else resolve_run_dir(out_root, manifest.name)
```

Leave the rest of `write_report` unchanged — it already writes everything under `out`.

- [ ] **Step 4: Run the full report suite to verify green**

Run: `uv run pytest tests/test_report.py -v`
Expected: PASS — the new passthrough test plus the four existing `write_report` tests (which pass `run_dir=None` implicitly and still resolve internally).

- [ ] **Step 5: Commit**

```bash
git add src/understudy/report/write.py tests/test_report.py
git commit -m "refactor(report): inject run_dir; expose resolve_run_dir"
```

---

### Task 4: Wire save + restore into `run_table`

**Files:**
- Modify: `src/understudy/orchestrate/run.py:20` (import), `:23-29` (signature), `:32-89` (body)
- Test: `tests/wiring/test_reconnect_state.py`

- [ ] **Step 1: Write the failing save-wiring test (real browser)**

Create `tests/wiring/test_reconnect_state.py`:

```python
import shutil
from pathlib import Path

from understudy.brain.core import FakeActionModel
from understudy.manifest import RunManifest, SeatSpec
from understudy.orchestrate.run import run_table
from understudy.types import Intent, IntentKind

FIXTURE = Path(__file__).parent / "fixture_table.html"


async def test_run_saves_browser_state_for_bot_seats_only(tmp_path):
    page_copy = tmp_path / "table.html"
    shutil.copy(FIXTURE, page_copy)

    # one quick resolving act so the seat loop runs and exits fast
    script = [
        Intent(
            kind=IntentKind.ACT,
            target_role="textbox",
            target_name="Action",
            text_input="hi",
        )
    ]

    manifest = RunManifest(
        name="statesave",
        genre="fixture",
        world="fixture",
        session_url=page_copy.as_uri(),
        seats=[
            SeatSpec(archetype="mechanics_first", model="fake"),  # seat 1 (bot)
            SeatSpec(archetype="human"),                          # seat 2 (not driven)
        ],
        turns=1,
        settle_ms=50,
        capture_spans=False,
    )

    code = await run_table(
        manifest,
        out_root=tmp_path / "reports",
        model_factory=lambda spec: FakeActionModel(list(script)),
    )
    assert code == 0

    out = next((tmp_path / "reports").iterdir())
    assert (out / "state" / "seat-1.json").exists()       # bot seat persisted
    assert not (out / "state" / "seat-2.json").exists()   # human seat skipped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/wiring/test_reconnect_state.py -v`
Expected: FAIL — `state/seat-1.json` does not exist (no save wiring yet).

- [ ] **Step 3: Wire save + restore into `run_table`**

In `src/understudy/orchestrate/run.py`, update the import line 20 and add the reconnect import after it:

```python
from understudy.report.write import resolve_run_dir, write_report
from understudy.orchestrate.reconnect import (
    reconnect_context_kwargs,
    seat_state_path,
    validate_reconnect_dir,
)
```

Change the signature (lines 23-29) to add the `reconnect` parameter:

```python
async def run_table(
    manifest: RunManifest,
    *,
    headed: bool = False,
    out_root: Path = Path("reports"),
    reconnect: Path | None = None,
    model_factory=make_model,  # injection seam for the wiring test
) -> int:
```

After `bot_seats` is computed (current line 34) and before the human-seat print loop, validate reconnect and resolve the run dir up front:

```python
    bot_seats = [
        (idx, spec) for idx, spec in enumerate(manifest.seats, start=1) if spec.archetype != "human"
    ]
    if reconnect is not None:
        validate_reconnect_dir(reconnect, [idx for idx, _ in bot_seats])
    out_dir = resolve_run_dir(out_root, manifest.name)
```

Inside the `async with async_playwright()` block, keep each bot seat's context handle and apply the restore kwargs. Replace the context-build loop and the gather/close region (current lines 45-67) with:

```python
        browser = await pw.chromium.launch(headless=not headed)
        runners: list[SeatRunner] = []
        seat_contexts: list[tuple[int, object]] = []  # (idx, BrowserContext)
        for idx, spec in bot_seats:
            context = await browser.new_context(**reconnect_context_kwargs(reconnect, idx))
            seat_contexts.append((idx, context))
            page = await context.new_page()
            await page.goto(manifest.session_url)
            runners.append(
                SeatRunner(
                    seat=idx,
                    archetype=load_archetype(spec.archetype),
                    model=model_factory(spec.model),
                    page=page,
                    turns=manifest.turns,
                    decide_timeout_s=manifest.decide_timeout_s,
                    settle_ms=manifest.settle_ms,
                    ledger=ledger,
                    deadline=deadline,
                    world=manifest.world,
                    genre=manifest.genre,
                    party_size=len(manifest.seats),  # humans count — they share the table
                )
            )
        all_rows_nested = await asyncio.gather(*(r.run() for r in runners))
        (out_dir / "state").mkdir(parents=True, exist_ok=True)
        for idx, context in seat_contexts:
            await context.storage_state(path=str(seat_state_path(out_dir, idx)))
        await browser.close()
```

Finally, pass the resolved dir to `write_report` (current line 84):

```python
    out = write_report(out_root, manifest, rows, findings, spans, spans_error, run_dir=out_dir)
```

- [ ] **Step 4: Run the save-wiring test plus the existing full-loop test**

Run: `uv run pytest tests/wiring/ -v`
Expected: PASS — `test_run_saves_browser_state_for_bot_seats_only` and the unchanged `test_full_loop_produces_graded_report` (which now exercises the up-front `resolve_run_dir` + `run_dir` passthrough path).

- [ ] **Step 5: Add the fail-loud run_table guard test**

Append to `tests/test_reconnect.py`:

```python
from understudy.manifest import RunManifest, SeatSpec
from understudy.orchestrate.run import run_table


async def test_run_table_reconnect_missing_seat_raises_before_launch(tmp_path):
    rc = tmp_path / "rc"
    (rc / "state").mkdir(parents=True)  # state/ exists but no seat-1.json
    manifest = RunManifest(
        name="x",
        genre="g",
        world="w",
        session_url="http://x",
        seats=[SeatSpec(archetype="mechanics_first", model="fake")],
        capture_spans=False,
    )
    with pytest.raises(ManifestError, match="seat 1"):
        await run_table(manifest, out_root=tmp_path / "reports", reconnect=rc)
```

- [ ] **Step 6: Run the guard test**

Run: `uv run pytest tests/test_reconnect.py::test_run_table_reconnect_missing_seat_raises_before_launch -v`
Expected: PASS — validation raises before any browser launches (no chromium needed; fast).

- [ ] **Step 7: Commit**

```bash
git add src/understudy/orchestrate/run.py tests/wiring/test_reconnect_state.py tests/test_reconnect.py
git commit -m "feat(reconnect): save per-seat storage_state and restore on --reconnect"
```

---

### Task 5: CLI `--reconnect` flag

**Files:**
- Modify: `src/understudy/cli.py:27-45`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI test + fix the existing stubs**

In `tests/test_cli.py`, the two existing `fake_run_table` stubs (`test_turns_flag_overrides_manifest`, `test_no_turns_flag_keeps_manifest_value`) have signature `async def fake_run_table(m, *, headed, out_root)`. The CLI will now also pass `reconnect`, so **update both** stub signatures to:

```python
    async def fake_run_table(m, *, headed, out_root, reconnect):
```

Then append a new threading test:

```python
def test_reconnect_flag_threaded_to_run_table(tmp_path, monkeypatch):
    good = tmp_path / "ok.yaml"
    good.write_text(
        "name: t\ngenre: g\nworld: w\nsession_url: http://x\nseats: [hesitant]\n"
    )
    captured = {}

    async def fake_run_table(m, *, headed, out_root, reconnect):
        captured["reconnect"] = reconnect
        return 0

    monkeypatch.setattr("understudy.cli.run_table", fake_run_table)
    result = runner.invoke(app, ["run", str(good), "--reconnect", "reports/prev"])
    assert result.exit_code == 0
    assert captured["reconnect"] == Path("reports/prev")
```

Add `from pathlib import Path` to the top of `tests/test_cli.py` if not already present.

- [ ] **Step 2: Run tests to verify the new one fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: `test_reconnect_flag_threaded_to_run_table` FAILS — `run` has no `--reconnect` option (and the stub already accepts `reconnect`, so the two turns tests still pass once their signatures are updated).

- [ ] **Step 3: Add the `--reconnect` option and ManifestError catch**

In `src/understudy/cli.py`, update the `run` command (lines 27-45). Add the option and wrap the run call so a reconnect validation error maps to exit 2:

```python
@app.command()
def run(
    manifest: Path,
    headed: bool = typer.Option(False, "--headed", help="show the browser windows"),
    out: Path = typer.Option(Path("reports"), "--out", help="report output root"),
    turns: int | None = typer.Option(
        None, "--turns", min=1, help="override the manifest's per-seat turn cap"
    ),
    reconnect: Path | None = typer.Option(
        None,
        "--reconnect",
        help="restore each bot seat's browser state from <DIR>/state/seat-{idx}.json "
        "(a prior run's report dir) so seats skip chargen and rejoin",
    ),
) -> None:
    """Run a table from a manifest: N naive bot seats join the session and play."""
    try:
        m = load_manifest(manifest)
    except ManifestError as exc:
        typer.echo(f"invalid manifest: {exc}")
        raise typer.Exit(2)
    if turns is not None:
        m = m.model_copy(update={"turns": turns})
    try:
        code = asyncio.run(
            run_table(m, headed=headed, out_root=out, reconnect=reconnect)
        )
    except ManifestError as exc:
        typer.echo(f"reconnect error: {exc}")
        raise typer.Exit(2)
    raise typer.Exit(code)
```

(`ManifestError` is already imported at `cli.py:16`.)

- [ ] **Step 4: Run the full CLI suite to verify green**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS — all four prior tests plus the new threading test.

- [ ] **Step 5: Commit**

```bash
git add src/understudy/cli.py tests/test_cli.py
git commit -m "feat(cli): --reconnect flag threads to run_table, errors map to exit 2"
```

---

### Task 6: Document the reconnect workflow + close the spec

**Files:**
- Modify: `README.md` (repo root) — add a Reconnect section
- Modify: `docs/superpowers/specs/2026-06-12-understudy-reconnect-browser-state-design.md` (orchestrator repo) — flip Status to Built

- [ ] **Step 1: Add a Reconnect section to the understudy README**

Append to `sidequest-understudy/README.md` (under the run/usage section — match the file's existing heading style):

```markdown
## Reconnect (skip chargen)

Every run automatically snapshots each bot seat's browser state to
`reports/<run>/state/seat-{idx}.json`. Re-run with `--reconnect` pointed at a
prior run's report dir to restore that state — the bot's lobby surfaces its
one-click resume entry and it rejoins its character past chargen, so the turn
budget goes to play instead of character creation.

```bash
just understudy four_seat_demo                              # run 1: chargen + play; writes state/
just understudy four_seat_demo --reconnect reports/<run1>   # run 2: resume, skip chargen
```

The reconnect run must declare the same seat order and count as the seed run
(same manifest is the normal case); mapping is by seat index. A missing or
incomplete `<DIR>/state/` fails loud (exit 2) before any browser launches. If a
stored session no longer loads (server restarted, different day), the bot
naively falls into chargen — a legitimate finding, not a suppressed error.
Reconnect targets the iterate-on-play loop within a session's life, not
long-term replay.
```

- [ ] **Step 2: Manual end-to-end smoke (not a unit test — record the result)**

With the server + UI running and a fresh four-seat demo session:

```bash
just understudy four_seat_demo                              # note the printed report dir
just understudy four_seat_demo --reconnect reports/<that-dir>
```

Confirm run 2's transcript shows seats reaching real play in early turns (resume clicked, no chargen cycles). Record the run-2 report dir in the session file. This is the only end-to-end proof that restored localStorage surfaces the real lobby resume entry — the unit tests prove the wiring, not the live UI.

- [ ] **Step 3: Flip the spec status to Built**

In `docs/superpowers/specs/2026-06-12-understudy-reconnect-browser-state-design.md` (orchestrator repo), change the header line:

```markdown
**Status:** Built (PR merged)
```

- [ ] **Step 4: Commit (understudy repo)**

```bash
git add README.md
git commit -m "docs(reconnect): document --reconnect workflow"
```

Commit the spec status change in the orchestrator repo separately (it is a different repo; follow the branch-protection rule and commit from each repo's root cwd).

---

## Self-Review

**Spec coverage:**
- Mechanism — save (auto) → Task 4 step 3 (`storage_state(path=...)` after gather). Restore (`--reconnect`) → Task 4 (`reconnect_context_kwargs` on `new_context`) + Task 5 (flag).
- CLI/Manifest surface — `--reconnect <DIR>`, saving always-on/unflagged → Task 5 + Task 4 (save is unconditional).
- Seat → state mapping by index, same order/count validated → Task 1/2 (`validate_reconnect_dir` over bot-seat indices) + Task 4 step 1 (seat-1 bot, seat-2 human).
- Architecture/touchpoints — `run.py` reconnect param + context handles + save; `cli.py` flag; single `seat_state_path` helper → Tasks 1, 4, 5. Run-dir-up-front concern → Task 3.
- Failure modes (fail loud, exit 2; human seats skipped; stale session is a finding not an error) → Task 2 + Task 4 step 5 (guard) + Task 5 (exit-2 catch) + Task 4 step 1 (human seat skipped) + README (stale-session-is-a-finding).
- Testing §1 path resolution → Task 1. §2 fail-loud → Task 2 + Task 4 step 5. §3 restore wiring (storage_state passed) → Task 1 `reconnect_context_kwargs` test (Playwright-fake deviation documented). §4 save wiring → Task 4 step 1.
- Out of scope / YAGNI (`--reconnect-latest`, `--no-save-state`, server seeding, cross-manifest remap) → none implemented. Confirmed absent.

**Placeholder scan:** no TBD/TODO/"add error handling"/"similar to Task N" — every code step shows complete code.

**Type consistency:** `seat_state_path(report_dir, idx)`, `reconnect_context_kwargs(reconnect, idx)`, `validate_reconnect_dir(reconnect, bot_seat_indices)`, `resolve_run_dir(root, name)`, `write_report(..., run_dir=None)`, `run_table(..., reconnect=None)` — names and signatures match across Tasks 1, 3, 4, 5. `ManifestError` reused for the exit-2 usage class throughout (raised in `reconnect.py`, caught in `cli.py`).
