---
story_id: "64-16"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 64-16: Expand polynesian.txt + georgian.txt shared corpora for WARN headroom

## Bundled Delivery Notice

**This session covers both 64-16 AND 64-17 as co-delivered deliverables.**

- **64-16** (this story, driver): Content repo — expand polynesian.txt + georgian.txt shared corpora
- **64-17** (co-delivered): Server repo — tidy two pre-existing weak/stale tests in test_audit_namegen_corpora.py

Both are p3 trivial 1-pointers, fallout from epic 64-7. Two PRs will result:
- `sidequest-content` → `develop` (64-16)
- `sidequest-server` → `develop` (64-17)

## Story Details
- **Driver ID:** 64-16
- **Co-Delivered ID:** 64-17
- **Jira Key:** (none — no jira enabled)
- **Workflow:** trivial
- **Stack Parent:** none (both are independent stories, standard repos)
- **Repos:** content, server

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-03T19:48:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T00:00:00Z | 2026-06-03T19:34:06Z | 19h 34m |
| implement | 2026-06-03T19:34:06Z | 2026-06-03T19:43:13Z | 9m 7s |
| review | 2026-06-03T19:43:13Z | 2026-06-03T19:48:20Z | 5m 7s |
| finish | 2026-06-03T19:48:20Z | - | - |

## Sm Assessment

**Routing:** trivial / phased → setup complete, hand to Dev (Agent Smith) for the implement phase.

**Bundled scope (two independent stories, one session, two PRs):**
- **64-16 (content, driver):** Append modest *real-word* headroom to
  `sidequest-content/corpus/shared/polynesian.txt` (1005) and `georgian.txt` (1004) — both sit
  only ~5 words above `WARN_BELOW_WORDS=1000`. Target ~1050+ each so a future trim can't flip
  them THIN. Verify with `count_words` (strips blanks/comments), **not** `wc -l`. No dup lines —
  dedup would erase the headroom. See `sprint/context/context-story-64-16.md`.
- **64-17 (server, co-delivered):** Test-only tidy in
  `sidequest-server/tests/scripts/test_audit_namegen_corpora.py` —
  (a) add an OK-classification assertion to `test_audit_synthetic_ample_corpus_exits_zero`;
  (b) fix the stale docstring in `test_audit_live_tree_exits_zero_after_corpus_expansion`
  (real prior failure is MISSING/rc=1, not THIN). No production/audit-script changes. See
  `sprint/context/context-story-64-17.md`.

**Verification bar:** `just server-test` green (esp. `test_audit_live_tree_no_named_corpora_left_thin_post_expansion`
and the two edited tests). No real ordering dependency between the two — but doing them in one
pass avoids the content/server audit-test interplay surprising anyone later.

**Branches:** `feat/64-16-corpus-headroom-audit-test-tidy` on both subrepos (each off `develop`).
At finish: two PRs (content→develop, server→develop); finish 64-16 via the flow and 64-17 by hand.

## Dev Assessment

**Implementation Complete:** Yes (both bundled deliverables)

**Files Changed:**
- `sidequest-content/corpus/shared/polynesian.txt` — +55 unique real words (1005 → 1060 count_words)
- `sidequest-content/corpus/shared/georgian.txt` — +56 unique real words (1004 → 1060 count_words)
- `sidequest-server/tests/scripts/test_audit_namegen_corpora.py` — strengthened
  `test_audit_synthetic_ample_corpus_exits_zero` (co-located OK-row assertion) + refreshed
  the stale docstring on `test_audit_live_tree_exits_zero_after_corpus_expansion`
  (pre-fix mode = MISSING/rc=1, not THIN). Test-only; no production change.

**Implementation notes:**
- 64-16: `count_words` = `len(text.split())` (token count incl. dups, no blank/comment
  stripping). Both corpora now sit 60 words above `WARN_BELOW_WORDS=1000`. Appended words are
  genuine Hawaiian/Māori/Samoan/Tongan (polynesian) and Georgian names + vocabulary, filtered
  against the existing sets so every appended token is new (no padding, no dup inflation —
  preserves Markov namegen quality).
- 64-17: verified the audit's actual classify/gate behavior in
  `scripts/audit_namegen_corpora.py` — `_classify` emits OK/THIN/FAIL, MISSING is set on
  unresolved corpora, and the rc=1 gate (`has_fail`) fires on FAIL **and** MISSING (THIN warns
  at rc=0). The corrected docstring matches this.

**Tests:** 9925/9925 passing (GREEN), 349 skipped — full `sidequest-server` suite via
testing-runner (RUN_ID 64-16-dev-green). The affected module
`tests/scripts/test_audit_namegen_corpora.py` is 20/20 green. Ruff clean on the changed file.

**Branches (pushed):**
- `sidequest-content` → `feat/64-16-corpus-headroom-audit-test-tidy` (commit c48f611)
- `sidequest-server` → `feat/64-16-corpus-headroom-audit-test-tidy` (commit edf079f)

**Handoff:** To review phase (The Merovingian). Two PRs to follow at finish (content→develop,
server→develop); finish 64-16 via the flow and 64-17 by hand.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings

### Dev (implementation)
- No upstream findings during implementation. Both deliverables were self-contained;
  the audit's classify/gate semantics matched the story-context description exactly.

### Reviewer (code review)
- No upstream findings during code review. Both changes are self-contained; no spec gaps,
  conflicts, or follow-up debt surfaced.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

No deviations

### Dev (implementation)
- No deviations from spec. (Story context targeted "~1050+" headroom; landed at 1060 each,
  within the intended range. 64-17 wired both sub-tasks (a) and (b) as specified, test-only.)

### Reviewer (audit)
- **Dev's "no deviations" entry** → ✓ ACCEPTED by Reviewer: confirmed. Story-context 64-16
  targeted "~1050+" headroom; both corpora landed at exactly 1060 count_words — within the
  intended band, not over-padded. 64-17 implemented both (a) the OK co-location assertion and
  (b) the docstring correction, test-only, no production/audit-script change as scoped.
- No UNDOCUMENTED deviations found. The implementation matches story-context
  `context-story-64-16.md` and `context-story-64-17.md` on every AC.

## Subagent Results

Per `workflow.reviewer_subagents` settings, only `preflight` and `security` are enabled;
the other seven are disabled and pre-filled as Skipped (they do not block the gate).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN: 9926 passed/0 failed; module 20/20; ruff clean; content PASS; 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned, both clean; 7 disabled via settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

> Note: with test-analyzer, comment-analyzer, and simplifier disabled, I performed their
> domains myself (this is a test + data-file change, squarely in those lanes) — see
> Observations and Rule Compliance below. I cannot claim subagent coverage for disabled
> specialists, so the manual analysis is recorded explicitly.

## Reviewer Assessment

**Verdict:** APPROVED

Two-deliverable trivial bundle (64-16 content + 64-17 server test). Diff is 111 additions to
two corpus data files and a +30/−11 test-only change. Both enabled specialists returned clean;
the full server suite is green (9926 passed, 0 failed); my independent corpus verification
confirms uniqueness and well-formedness.

**Data flow traced:** corpus word (e.g. `siqvaruli` in `georgian.txt`) → `count_words` token
count in `audit_namegen_corpora.py:205` → `_classify` (≥1000 ⇒ OK) → report row. Also →
Markov n-gram namegen (ADR-091): decomposed into n-grams and recombined into synthetic names;
never injected verbatim into an LLM prompt. Safe — no instruction-bearing passthrough
(confirmed by [SEC]).

**Observations (8):**
1. `[VERIFIED]` Headroom achieved — `polynesian.txt`/`georgian.txt` both 1060 count_words,
   60 above `WARN_BELOW_WORDS=1000` (`thresholds.py:25`). A future ≤60-word trim can no longer
   flip them THIN. Evidence: independent `len(text.split())` recount = 1060/1060. (AC1)
2. `[VERIFIED]` Append uniqueness — every one of the 55/56 appended tokens is new: 0 collisions
   with the pre-existing set, 0 internal dups. Evidence: set-difference recount over the
   appended slice. `count_words` rising by N alone does NOT prove uniqueness (it counts dups),
   so this was verified directly rather than inferred. (AC2)
3. `[VERIFIED]` Quality preserved — all appended tokens are single lowercase alphabetic words
   (0 malformed: no blanks, digits, spaces, or uppercase); genuine Hawaiian/Māori/Samoan/Tongan
   and Georgian names + vocabulary. No padding/placeholder tokens. (AC2)
4. `[VERIFIED]` Audit stays OK — `test_audit_live_tree_no_named_corpora_left_thin_post_expansion`
   and `test_shared_corpora_clear_warn_threshold` pass on the live tree post-expansion (module
   20/20 green via preflight). (AC3, 64-16)
5. `[TEST]` (self, analyzer disabled) Strengthened assertion is correct, not vacuous —
   `ok_rows = [l for l in out.splitlines() if "synth.txt" in l and "OK" in l]; assert ok_rows`
   pins the OK *classification* co-located on the synth.txt row, replacing the old loose
   presence check. The report row format `corpus | count | status |`
   (`audit_namegen_corpora.py:274`) guarantees corpus and status share a line; `## OK (N)`
   headers and the `N OK.` summary do NOT contain `synth.txt`, so no false-positive match.
   Mirrors the existing co-location idiom in `test_audit_surfaces_consumption_by_culture`. (64-17a)
6. `[DOC]` (self, analyzer disabled) Docstring correction is accurate — the refreshed
   `test_audit_live_tree_exits_zero_after_corpus_expansion` note now matches the audit's real
   behavior: `_classify` + the `has_fail` gate (`audit_namegen_corpora.py:328`,
   `status in ("FAIL","MISSING")`) means pre-fix MISSING ⇒ rc=1, while THIN warns at rc=0. The
   old "pre-fix = THIN/exit-0" claim was self-contradictory and wrong; corrected, and
   corroborated by the sibling test's docstring. (64-17b)
7. `[SIMPLE]` (self, simplifier disabled) No over-engineering — data appends are minimal; the
   test change adds exactly one list-comprehension + assert. No dead code, no new abstraction.
8. `[VERIFIED]` Pre-existing `kupenga` duplicate (`polynesian.txt:1004-1005`) is upstream, NOT
   introduced by this branch (diff appends start at line 1006). Correctly left untouched —
   dedup is out of scope and would erode headroom.

**Dispatch tags:** `[EDGE]` N/A (disabled; boundary = the 1000-word floor, covered by Obs 1).
`[SILENT]` N/A (disabled; no error-handling paths in a data/test change). `[TEST]` self — Obs 5.
`[DOC]` self — Obs 6. `[TYPE]` N/A (disabled; no type/signature changes — test sigs unchanged,
`-> None`). `[SEC]` clean — security specialist, no findings. `[SIMPLE]` self — Obs 7.
`[RULE]` N/A (disabled) — manual Rule Compliance below.

### Rule Compliance

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) applied to the one
changed `.py` file (`tests/scripts/test_audit_namegen_corpora.py`); corpus `.txt` files are data,
outside the Python checklist.

- **Rule 1 (silent exception swallowing):** Compliant — no `try/except` in changed lines.
- **Rule 3 (type annotations at boundaries):** Compliant — `test_*(... ) -> None`, `tmp_path: Path`
  unchanged and annotated.
- **Rule 6 (test quality):** Compliant and IMPROVED — this change is the fix Rule 6 calls for.
  Old `assert "synth.txt" in result.stdout` was a loose presence check; new assertion pins the
  specific OK classification co-located on the row. `assert ok_rows` is a filtered-list check
  (non-vacuous: the filter requires both `synth.txt` and `OK` on one line). No `assert True`, no
  no-assertion tests, no `mock.patch`, no skips.
- **Rule 7 (resource leaks):** Compliant — no `open()`/sockets in changed lines; subprocess via
  the existing `_run_audit` helper (unchanged).
- **Rule 8 (unsafe deserialization):** Compliant — `_run_audit` uses `subprocess.run([list], ...)`
  (no `shell=True`, no interpolation); unchanged by this diff. No `eval`/`pickle`/`yaml.load`.
- **Rules 2, 4, 5, 9, 10:** Not implicated by the changed lines (no mutable defaults, no logging,
  no path strings, no async, no new imports).

### Devil's Advocate

Let me argue this is broken. **First attack — the OK assertion is a false friend.** `"OK" in line`
is a substring test; if any corpus slug, culture name, or pack name in a synth.txt row ever
contained the letters "OK" (e.g. a future fixture pack named `bookworld` or a culture `Tokoloshe`),
the assertion would pass even if the real status were THIN. Rebuttal: the synthetic fixture is
named `synth`/`synth.txt` (`_build_synthetic_pack`), the row format is
`corpus | word_count | status |`, and the only status token containing "OK" is "OK" itself —
"THIN"/"FAIL"/"MISSING" share no substring with it. The risk is theoretical for the current
fixture; a stricter form would assert the trailing `| OK |` cell. I judge this LOW, not blocking —
the assertion is strictly stronger than what it replaced and matches the codebase's existing
co-location idiom. **Second attack — the corpus words are garbage/offensive/duplicated.** A
malicious or careless author could append slurs, real PII, or near-dup tokens that inflate the
count without adding Markov diversity. Rebuttal: I independently recounted — 0 collisions, 0
internal dups, 0 malformed tokens; the words are recognizable Polynesian/Georgian names and common
nouns. No count-inflation-without-headroom. **Third attack — the headroom is illusory because
`count_words` counts dups.** If the appended block secretly repeated existing words, the file would
read 1060 but carry no new Markov material and a trim could still strip uniques below the warn
floor. Rebuttal: this is exactly why I verified uniqueness directly (Obs 2) rather than trusting
the token count — every appended token is genuinely new. **Fourth attack — a stressed filesystem
/ encoding.** Non-ASCII? The Georgian additions are romanized ASCII (`tskhali`, not Mkhedruli
script), so no encoding surprise; files end with a trailing newline (no merged last line). **Fifth
— could the live-tree test now be over-tight?** The corrected docstring changes no logic; the
assertion `returncode == 0` is unchanged. Nothing the Devil raised rises to High/Critical.

**Pattern observed:** co-located substring assertion (stronger than bare presence) at
`tests/scripts/test_audit_namegen_corpora.py:338-343`, consistent with
`test_audit_surfaces_consumption_by_culture:133`.
**Error handling:** N/A — data + test change, no production error paths touched.
**Handoff:** To SM (Morpheus) for finish-story (two PRs: content→develop, server→develop).