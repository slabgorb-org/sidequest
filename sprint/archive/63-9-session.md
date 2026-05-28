---
story_id: "63-9"
epic: "63"
workflow: "tdd"
---
# Story 63-9: Reference renderer humanization guard — never emit raw key/dict/snake_case/bool/dev-note prose; humanize section-key headings; + output-scan test

## Story Details
- **ID:** 63-9
- **Epic:** 63 — Reference pages v3 — chrome + wiki-like anchor links
- **Workflow:** tdd
- **Branch:** feat/63-9-renderer-humanization-guard
- **Points:** 5
- **Priority:** p2
- **Type:** bug
- **Repos:** sidequest-server

## Story Context

The `/reference/rules/<pack>` and `/reference/lore/<pack>/<world>` pages are rendering raw developer strings into the user-facing UI. This story hardens the reference renderer to never emit:
- Raw Python key names (snake_case)
- Raw dict/list repr() output
- Raw bool values (True/False)
- Dev-note comments or placeholder prose

**Specific issues to guard:**
1. Section-key headings (h2/h3) must be humanized (title case, underscores→spaces, bool→Yes/No, etc)
2. Any dict/list keys from schema objects must be humanized before rendering
3. Output scan test to verify no raw dev strings leak into the final HTML

Related stories:
- 63-4 (Chrome rendering) — landed
- 63-5 (Cleanup & validation) — landed
- 63-6 (LocationPanel reference_url) — landed
- 63-8 (Lore page POI images) — landed

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-05-27

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): Story has no Architect-ratified ACs. TEA derived the **dev-note marker set** (`TODO`, `FIXME`, `XXX`, `PLACEHOLDER`, `DEV NOTE` — leading-token, case-insensitive) and a **leading-underscore-key = private/suppress** policy. Affects `reference_renderer.py` fallback walk + a new guard helper. Tests constrain only the *safe invariant* (no raw dev string in HTML), not casing/marker impl, so Architect can finalize the exact set without rewriting tests. *Found by TEA during test design.*
- **Gap** (non-blocking): The conservative `_humanize_label` bails on ANY uppercase, so an underscore-bearing key that also has caps (`MECHANICAL_surface`) leaks its underscore into the heading. Pinned `test_heading_with_underscore_and_caps_strips_underscore` — Dev should strip underscores even when caps are present, while still preserving acronyms (`USB`, no underscore) and authored prose (`Floor It`, whitespace). Affects `_humanize_label` in `reference_renderer.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): Underscore-prefixed keys (`_dev_note`) are NOT caught by the visibility gate — `lore`/`rules` stems are stem-default PUBLIC, so every key under them (including `_`-prefixed) classifies PUBLIC and reaches the fallback walk. Suppression must happen in the renderer guard, not via `reference_visibility`. Affects `reference_renderer._render_dict`. *Found by TEA during test design.*
- **Improvement** (non-blocking): AC2 (no raw container repr) is *already structurally satisfied* — the fallback walk recurses dicts/lists into markup and never `str()`s a container; the depth-cap path emits YAML, not Python repr. No current leak exists. Pinned as a passing regression-lock (`test_dict_value_renders_as_markup_not_repr`) rather than a RED test. *Found by TEA during test design.*
- **Note** (non-blocking): AC6 — TEA scoped the new OTEL span to the **suppression decision only** (`SPAN_REFERENCE_DEVNOTE_SUPPRESSED`), per No-Silent-Fallbacks (dropping author content is a loud decision). TEA deliberately did NOT require a per-bool/per-heading *humanization* span — that is a cosmetic transform (CLAUDE.md "Not needed for: cosmetic changes") and one span per bool would be telemetry noise. Architect may revisit if a humanization span is wanted. *Found by TEA during test design.*

### Reviewer (code review)
- **Gap** (blocking): The dev-note guard has a **structural hole on the list path**. `_render_dict` checks `_is_devnote(value)` only for scalar values; a list-valued field (`{notes: ["TODO: fix this section", ...]}`) takes `_render_list`'s scalar-only fast path, which calls `_scalar_text` — and `_scalar_text` does NOT check `_is_devnote`. Confirmed empirically: renders `<li>TODO: fix this section</li>`. This violates AC4 ("no dev-note leakage") through a sibling code path and directly undercuts the story's "safe by construction" thesis. Affects `reference_renderer._render_list` / `_scalar_text`. *Found by Reviewer during code review.*
- **Gap** (blocking): The AC5 output-scan GATE (`test_lore_page_output_scan_has_no_raw_dev_strings`) has **zero positive assertions** — every check is `X not in html`, and the heading for-loop is vacuous on empty output. If the `genre_conventions` section were ever dropped wholesale (e.g. a future visibility reclassification) the gate would still pass green. The marquee deliverable cannot distinguish surgical suppression from total section failure. Affects `tests/server/test_reference_humanization_guard.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_DEVNOTE_MARKERS` is duplicated verbatim in the test file instead of imported from `reference_renderer`; the parametrize set will silently go stale if production adds a marker. Import the production constant. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `_is_devnote` matches `"DEV NOTE"` (single space) only — `"DEV  NOTE"`/tab/NBSP-separated variants bypass the guard (confirmed `_is_devnote('DEV  NOTE: rewrite') == False`). Normalize internal whitespace before the startswith test. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `_scalar_text(None)` returns `"None"`, so `["x", None]` renders `<li>None</li>` (bare Python token to the reader). Standalone `None` correctly renders `(none)` via `_render_scalar`; the list path is inconsistent. *Found by Reviewer during code review.*
- **Question** (non-blocking): SM asked me to scrutinize the TEA-derived contract. Verdict: marker set is reasonable; leading-underscore-key suppression is a sound convention. BUT the docstring overclaims — it lists `USB` as "preserved" yet `_humanize_label("USB_port")` returns `"Usb Port"` (acronym destroyed in compound keys, confirmed). Behavior is *acceptable* (the safe invariant — no raw `_` in HTML — holds), but the docstring should note compound-acronym keys are title-cased, not preserved. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Dev-note contract derived without Architect ratification:** Spec said "suppress dev-note/placeholder prose" without defining markers. Tests use marker set (`TODO`/`FIXME`/`XXX`/`PLACEHOLDER`/`DEV NOTE`, leading-token) + leading-underscore-key suppression. Reason: story had no formal ACs and RED was requested now; constrained tests to the safe invariant so the contract can be finalized in design without test churn.
- **AC2 pinned as passing regression-lock, not RED:** Spec listed "no raw container repr" as a guard requirement. Reason: current renderer already recurses containers into markup and never emits Python repr — no failing case exists, so it is locked green rather than faked RED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug-fix with a testable output-scan gate.

**Test Files:**
- `sidequest-server/tests/server/test_reference_humanization_guard.py` — 18 tests pinning the humanization guard (bool→Yes/No, heading underscore-strip, dev-note + private-key suppression, OTEL suppression span, end-to-end output-scan gate).

**Tests Written:** 18 tests covering ACs 1–6 (16 RED + 2 green regression-locks).
**Status:** RED (16 failing for the right reasons; 2 intentional locks pass). Baseline clean — existing `test_reference_renderer.py` + `test_reference_otel.py` = 53 passed, 0 regressions.

**Handoff:** To Dev for implementation (GREEN).

## Design Deviations — Dev

### Dev (implementation)
- No deviations from spec. Implemented exactly to TEA's RED contract: dev-note markers (TODO/FIXME/XXX/PLACEHOLDER/DEV NOTE, leading-token, case-insensitive), leading-underscore key suppression, bool→Yes/No, underscore-stripping humanization, suppression-only OTEL span. The marker set / underscore policy remain TEA-derived pending Architect ratification (TEA's logged finding) — did not widen the contract. AC2 (container-repr) was a regression-lock already structurally held; untouched.

## Delivery Findings — Dev

### Dev (implementation)
- No upstream findings. TEA's contract was implementable as written; the only behavioral change to `_humanize_label` (process underscore keys even when caps present) was anticipated by TEA's gap finding and broke no baseline test.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/reference_renderer.py` — bool-aware `_render_scalar` + new `_scalar_text` helper (lists) → Yes/No; `_humanize_label` rewritten so underscore/hyphen keys always split-and-title-case (no raw `_` survives) while authored prose / acronyms / proper nouns stay untouched; new `_DEVNOTE_MARKERS` + `_is_devnote` leading-token detector; dev-note/private-key suppression guard placed first in `_render_dict` loop (fires OTEL span, then `continue`s).
- `sidequest-server/sidequest/telemetry/spans/reference.py` — new `SPAN_REFERENCE_DEVNOTE_SUPPRESSED` constant (registered flat-only) + `reference_devnote_suppressed_span` helper (pack/world/file_stem/key_path attrs).

**Tests:** 18/18 new + 53 baseline = 71/71 GREEN. Full suite (tests/server + tests/integration + tests/genre, with SIDEQUEST_GENRE_PACKS + test DB provisioned): **2985 passed, 234 skipped, 0 failed, 0 errors**. The 33 failures seen on a first run without a DB URL were all `MissingDatabaseUrlError` (ADR-115) — environment-only, vanished once `SIDEQUEST_DATABASE_URL` was set. 0 regressions.
**Branch:** feat/63-9-renderer-humanization-guard (pushed)

**Handoff:** To verify (TEA)

## Dev Assessment — GREEN patch (Reviewer HIGH gaps)

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/reference_renderer.py`:
  - `_render_list` scalar fast-path now suppresses dev-note list items via `_is_devnote` and fires `reference_devnote_suppressed_span` (ctx already available) — closes the AC4 list-path hole (Reviewer HIGH #1). Benign siblings survive (surgical).
  - `_is_devnote` collapses internal whitespace (`re.sub(r"\s+", " ", …)`) before marker match so `"DEV  NOTE"` / tab / NBSP variants are caught (NIT #2).
  - `_scalar_text(None)` now returns `<em>(none)</em>` to match `_render_scalar`, never bare `None` in a `<li>` (NIT #3).
  - `_humanize_label` docstring corrected: compound-acronym keys (`USB_port` → `Usb Port`) are title-cased, not preserved — the AC1 no-raw-`_` invariant wins (NIT #4).

**Tests:** 20/20 guard tests GREEN (2 new functions + strengthened AC5 gate + 17 prior) + 53 baseline. Full suite (server + integration + genre, SIDEQUEST_GENRE_PACKS + SIDEQUEST_DATABASE_URL both set): **2987 passed, 234 skipped, 0 failed, 0 errors**. 0 regressions.
**Branch:** feat/63-9-renderer-humanization-guard (pushed)

**Handoff:** To verify (TEA re-verify)

### Dev (implementation) — patch deviations
- No deviations. All four changes are exactly the Reviewer findings; no contract widened. List-path span uses the list's own `key_path` (`ctx.key_path`) since list items have no key of their own.

## TEA Verify Assessment

**Verdict:** VERIFY PASS
**Full suite (HEAD 7f54bdec, SIDEQUEST_DATABASE_URL + SIDEQUEST_GENRE_PACKS set):** 2719 passed, 0 failed, 0 errors, 500 skipped. New file 18/18 GREEN.

**Over-fitting / spec-satisfaction review (not just test letter):**
- Suppression guard is genuinely in the fallback walk — first statement in the `_render_dict` per-key loop, `ctx is not None` gated, fires span then `continue`. NOT routed through `reference_visibility` (finding #2 honored). ✅
- Span fires from the REAL render path — inline `reference_devnote_suppressed_span(...)` call in `_render_dict`; the wiring test drives `assemble_lore_page` end-to-end and observes the span. No shim. ✅
- `_humanize_label` is not overzealous: whitespace-bearing prose ("Floor It", "Item 3") untouched; separator-free acronyms/proper-nouns ("USB", "McGuffin") untouched; only separator-bearing identifiers always split+title-case. Baseline `test_humanize_label_leaves_authored_prose_untouched` still passes. ✅ (Documented edge, not a defect: an acronym embedded in snake_case like `USB_port` → "Usb Port" — acceptable given the hard "no raw underscore" requirement.)
- bool→Yes/No uses explicit `isinstance(value, bool)` BEFORE the str path, so int `1` does NOT become "Yes" (no over-broad coercion). ✅
- `_is_devnote` is leading-token-only with a boundary check — "todos" is not matched (over-suppression guard test passes). ✅
- OTEL scope held to the suppression decision only; no per-bool/heading humanization span added (finding #5/#3). ✅

**Handoff:** To Reviewer.

## Reviewer Deviation Audit

- **TEA — dev-note contract derived without Architect ratification:** ACCEPTED. The marker set and leading-underscore convention are reasonable and the tests constrain only the safe invariant. Sound call to unblock RED. One caveat folded into findings: the `_humanize_label` docstring overclaims acronym preservation (`USB_port`→"Usb Port"); documentation NIT, not a behavior defect.
- **TEA — AC2 pinned as passing regression-lock, not RED:** ACCEPTED. Verified: the fallback walk recurses containers into markup and the depth-cap path emits YAML, never Python `repr()`. No leak exists; locking it green is correct.
- **Dev — no deviations:** ACCEPTED. Implementation matches the RED contract; the `_humanize_label` caps-handling change was anticipated by TEA's gap finding.

## Reviewer Assessment

**Verdict:** REQUEST-CHANGES

The core playtest failure (raw snake_case headings + bare `True`/`False`) is genuinely and well fixed, with a real end-to-end OTEL wiring test and clean full-suite green. But the story's explicit thesis is "safe **by construction**, structural not per-section," and two confirmed gaps undercut that on the named ACs (AC4, AC5). Both fixes are small.

**Data flow traced:** authored YAML value → `_render_dict` per-key loop → `_is_devnote`/`_`-prefix suppression (fires span, `continue`) for scalars → recurse. Hole: list-valued fields bypass the scalar guard via `_render_list`'s fast path (`_scalar_text`, no `_is_devnote`). Empirically confirmed `{notes:["TODO: fix this section"]}` → `<li>TODO: fix this section</li>`.

**Pattern observed:** suppression guard correctly placed FIRST in the dict loop, `ctx`-gated, loud (OTEL) not silent — honors No-Silent-Fallbacks. Good. The hole is that the guard was only wired into one of the two leaf paths.

**Error handling:** suppression fires `reference_devnote_suppressed_span` with key_path; verified it fires from the real `assemble_lore_page` path, not a shim.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Dev-note leaks via list-valued fields (AC4 hole) — `_scalar_text` doesn't check `_is_devnote` | `reference_renderer._render_list` (line 381) / `_scalar_text` (213) | Apply `_is_devnote` suppression to scalar-list items too (fire the span when ctx present), so `["TODO: …"]` cannot reach `<li>`. |
| [HIGH] | AC5 GATE test is all-negative + vacuous heading loop — passes green even if the whole section is dropped | `tests/server/test_reference_humanization_guard.py::test_lore_page_output_scan_has_no_raw_dev_strings` (290) | Add ≥1 positive assertion proving non-suppressed content rendered (e.g. `assert "Mechanical Surface" in html` and `assert "Yes" in html`), proving suppression is surgical not total. |
| [NIT] | `_DEVNOTE_MARKERS` duplicated in test — silently goes stale if production adds a marker | test file (57) | Import `_DEVNOTE_MARKERS` from `reference_renderer` and parametrize off it. |
| [NIT] | `"DEV  NOTE"` (multi-space/tab/NBSP) bypasses `_is_devnote` | `reference_renderer._is_devnote` (197) | Normalize internal whitespace before the `startswith` test. |
| [NIT] | `_scalar_text(None)` → bare `"None"` in list items | `reference_renderer._scalar_text` (213) | Match `_render_scalar`'s `(none)` handling for `None`. |
| [NIT] | Docstring overclaims acronym preservation (`USB_port`→"Usb Port") | `_humanize_label` docstring (155) | Note compound-acronym keys are title-cased, not preserved. |

**Observations (8):** (1) snake_case + bool fixes solid & tested; (2) OTEL wiring test is real end-to-end — exemplary per CLAUDE.md; (3) suppression is loud, not silent; (4) list-path dev-note leak confirmed empirically; (5) gate test cannot prove surgical suppression; (6) marker set & `_`-key convention are sound (answers SM's question); (7) USB_port→"Usb Port" acceptable behavior, misleading docstring; (8) no security/data-corruption/dead-code issues — `git diff` is clean, no stubs.

**Handoff:** Back to Dev for the two HIGH items (and ideally the NIT sweep — all are ≤3-line fixes). NITs alone would not block; the two AC-touching HIGH gaps do.

## Reviewer Assessment — Re-review (RED 8a10e475 / GREEN a057c750)

**Verdict:** APPROVED

Both HIGH findings genuinely resolved — verified empirically through the real `assemble_lore_page` path, not by trusting test names:
- **HIGH #1 (list dev-note leak):** `_render_list` scalar fast-path now applies `_is_devnote` and fires `reference_devnote_suppressed_span` (ctx-gated, `key_path=ctx.key_path` points at the list field — honest, not a fabricated per-item index). Confirmed: fixture `notes: ["TODO: fix this section", "real lore fact"]` → `TODO` suppressed, sibling "real lore fact" survives. Surgical, loud-not-silent. ✅
- **HIGH #2 (vacuous gate):** `test_lore_page_output_scan_has_no_raw_dev_strings` now carries positive assertions (`assert headings`, "Mechanical Surface", "Yes", "No", surviving list item, nested `<p>5</p>`) alongside the negatives — a total-section drop now fails the gate. ✅

NITs all clean (verified): `_DEVNOTE_MARKERS` imported from renderer (single source); `_is_devnote('DEV  NOTE')`/tab now `True` while `'a list of todos'` stays `False`; `_scalar_text(None)` → `(none)`; `_humanize_label` docstring honestly documents `USB_port`→"Usb Port" (safe invariant wins). Guard suite 20/20 green; TEA full suite 2721 pass / 0 regress.

**Handoff:** To SM for finish ceremony.
