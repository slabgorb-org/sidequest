# Doc-Drift Check

> A lightweight regression guard that keeps the canonical, agent-facing docs from
> drifting back out of sync with reality. Proposed and shipped in **epic-127**
> (story 127-7) after a sweep that reconciled the Rust→Python, SQLite→Postgres,
> TTS-removal, native-ruleset, Opus-model, and pack-count drift.

## Why

These docs *steer AI agents*. A stale claim ("the engine is Rust", "saves are
SQLite", "Opus 4.7", "10 packs") is not cosmetic — it sends an agent down a dead
path. Epic-127 fixed a batch of these by hand; the check exists so the **same
classes of drift can't creep back** without a loud signal.

It is a **tripwire**, not a semantic linter. Each pattern is a high-confidence
stale claim with essentially zero legitimate live use, so a hit means a doc has
regressed.

## Run it

```bash
just doc-drift              # scan; exit 1 on any hit
just doc-drift --list       # print the tripwire table
python3 scripts/check_doc_drift.py   # same, without just
```

Exit `0` = clean, `1` = drift found (or a configured doc path went missing).

## Scope

**Scanned (canonical docs):** `README.md`, `JARGONFILE.md`, `docs/**/*.md`, and
the six subrepo `README.md` files.

**Excluded — historical / process artifacts where stale terms are *correct*:**

- `docs/adr/**` — decision records (capture the as-decided state at a point in time)
- `docs/superpowers/**` — specs, plans, and dev notes (completed & superseded)

## Tripwires (current set)

| id | pattern | reconciled by |
|----|---------|---------------|
| `opus-model-id` | `claude-opus-4-7` | 127-6 (Opus → 4.8) |
| `opus-version` | `Opus 4.7` | 127-6 |
| `pack-count-prod` | `10 production packs` | 127-7 (11 packs) |
| `pack-count-all` | `all 10 packs` | 127-7 |
| `dead-rust-link` | `](../sidequest-api/…` | 127-2 (Rust→Python, ADR-082) |
| `workshop-tree-path` | `genre_workshopping/<name>` | 127-5 (tree retired 2026-06-03) |
| `hp-removed` | `No HP field on sheet` | 127-7 (ADR-114 ablative HP) |

Run `just doc-drift --list` for the live list with remediation hints.

## Adding a tripwire

When you reconcile a new class of drift, add a `(id, regex, hint)` row to
`TRIPWIRES` in `scripts/check_doc_drift.py` so it can't return. Keep each pattern
**unambiguously stale** — specific enough that it has no legitimate live use.

### Why some terms are NOT auto-tripwired

`SqliteStore`, `TTS`, `native` (ruleset), and `low_fantasy` are **deliberately
excluded** from the automated set. Each has legitimate "removed / retired /
deleted" mentions in canonical docs (e.g. "the old `SqliteStore.open()` path is
gone", "TTS was removed 2026-04", "native is vestigial — no pack binds it"). A
bare-term pattern would fire on those accurate notes, and a check that cries wolf
gets ignored. Review these by hand when touching persistence / audio / ruleset /
pack docs.

## Escape hatch

For a genuinely-historical mention that has to live inside a *canonical* doc,
append a suppression marker to the line:

```markdown
... the legacy `genre_workshopping/road_warrior` path ...  <!-- drift-ok: historical migration note -->
```

Use it sparingly — the right fix is almost always to correct the drift.

## Proposed CI wiring

The check is fast (pure stdlib, no deps) and side-effect-free. Recommended
adoption, lightest first:

1. **Local pre-flight** — run `just doc-drift` before opening a docs PR. (Available now.)
2. **CI gate** — add `doc-drift` to the aggregate gate, alongside the existing
   `adr-check` / `feature-inventory-check` doc guards, e.g. a `docs-check` recipe
   or a step in the GitHub Actions docs job. Non-zero exit fails the build with
   `file:line` + a remediation hint.
3. **Pre-commit hook** (optional) — wire into `.githooks/` for an even tighter loop.

CI wiring is intentionally left as a follow-up decision rather than forced here —
the script is the load-bearing piece; where it runs is a process choice.
