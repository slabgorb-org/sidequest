---
name: sq-llm-costs
description: LLM cost and cache forensics — reconcile server-log narrator costs against the Anthropic Admin API, attribute per-model spend, detect dead caching and invisible callers. Use when analyzing API costs, auditing cache efficiency, or when the Console bill doesn't match expectations.
---

# sq-llm-costs — LLM Cost & Cache Forensics

<run>
You are running a **cost reconciliation audit**. Two cardinal rules:
- **(2026-06-05) Server logs do not see everything.** The narrator and the Haiku adapters log to *different* anchors (`narrator.sdk.usage` vs `llm.sdk.usage`), and subprocess `claude -p` logs to neither. The Console bill is the only ground truth. Reconcile all layers before concluding.
- **(2026-06-06) A clean log is not a clean session — it may be the wrong log.** Before you read a single usage line, run **Layer 0** below. The live server may run from a *different clone* (oq-1 vs oq-3), may have *restarted minutes ago* (rotating the busy log out from under you), and the Haiku/router lines live in **rotated files**, not the current one. Never conclude "no Haiku" from a grep that returned zero — a null result means *validate the grep*, not *the calls didn't happen*. Open the Console (Layer 3) **first** when investigating a specific caller.

## Layer 0 — Provenance preflight (MANDATORY, run before any log read)

Skipping this is how the 2026-06-06 audit spent an hour reading an empty post-restart log and declared Haiku silent while the Console showed it firing every turn.

```bash
# Which process serves the game on :8765, from WHICH checkout, started WHEN?
ps -eo pid,lstart,command | grep -iE "uvicorn.*sidequest.server.app" | grep -v grep
# ^ note the .venv path in the child proc — oq-1 vs oq-2 vs oq-3. The log you must
#   read belongs to THAT clone's server, and the code you cite must be THAT clone.

# Which log file is it writing, and when did it last rotate?
ls -lt ~/.sidequest/logs/sidequest-server.log* | head -5
head -1 ~/.sidequest/logs/sidequest-server.log | cut -c1-30   # current-log start time

# Is the classification rung Haiku or local? (unset => anthropic => Haiku)
ps eww <server-pid> | tr ' ' '\n' | grep -E "SIDEQUEST_(CLASSIFICATION_BACKEND|LLM_BACKEND)"
```

**Rule:** if the current `sidequest-server.log` starts *after* the window you care about, the traffic is in a rotated `*.log.YYYYMMDD-HHMMSS` file. **Grep the rotations, not just the live file.** Every Layer 1 query below must include rotated files for the window.

## The Three Layers (run all of them)

| Layer | Source | Sees | Blind to |
|-------|--------|------|----------|
| 1a. Server logs — narrator | `narrator.sdk.usage` lines | Narrator Sonnet loop only | Haiku router/asides, `claude -p`, anything off-box |
| 1b. Server logs — Haiku | `llm.sdk.usage` lines (`caller=intent_router\|aside`, since story 91-1) | Router + aside Haiku calls | `claude -p` subprocesses, anything off-box |
| 2. OTEL / Jaeger | `llm.request` spans | Instrumented SDK call sites | Subprocess callers, span-less paths, trace-limit truncation |
| 3. Admin API | `scripts/anthropic_usage.py` | **Everything billed to the org** | Per-turn attribution (no request counts) |

If Layer 3 ≫ Layer 1, something uninstrumented is spending money. That is a finding, not noise.

## Layer 1 — Server-log narrator aggregation

Usage lines are emitted by `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (grep anchor: `narrator.sdk.usage`). Logs live at `~/.sidequest/logs/sidequest-server.log` with rotations `*.log.YYYYMMDD-HHMMSS` (30-day retention, **rotation-stamped local time** — each "day" can include the prior evening's tail).

**Run under `bash -c`, not zsh** — zsh does not word-split `$files`, which silently yields zero matches.

**Anchor the sed on `iter=`, not `usage iter=`.** As of the 92-eval work the line gained `caller=` and `model=` fields between `usage` and `iter=`, so the old `.*usage iter=` anchor silently matches nothing on current logs and the awk divides by zero. Use `.*iter=([0-9]+) input=...`.

```bash
bash -c '
cd ~/.sidequest/logs
for i in $(seq 30 -1 0); do
  d=$(date -v-${i}d +%Y%m%d)
  files=$(ls sidequest-server.log.$d-* 2>/dev/null)
  [ "$i" -eq 0 ] && files="$files sidequest-server.log"
  [ -z "${files// /}" ] && continue
  grep -h "narrator.sdk.usage" $files 2>/dev/null | \
  sed -E "s/.*usage iter=([0-9]+) input=([0-9]+) output=([0-9]+) cache_read=([0-9]+) cache_write=([0-9]+) 5m=([0-9]+) 1h=([0-9]+) cost_usd=([0-9.]+).*/\1 \2 \3 \4 \5 \6 \7 \8/" | \
  awk -v d=$d "{
    n++; in_+=\$2; out+=\$3; cr+=\$4; cw+=\$5; m5+=\$6; h1+=\$7; cost+=\$8;
    if(\$1==1)turns++;
    if(\$4>0 && \$7>0)warm1h++;
  }
  END{ if(n>0) printf \"%s|calls=%d|turns=%d|cost=\$%.2f|c_per_turn=%.1f|hit=%.1f%%|5mW=\$%.2f|1hW=\$%.2f|out=\$%.2f|warm1h=%d\n\", d, n, turns, cost, (turns?100*cost/turns:0), 100*cr/(cr+cw+in_), m5*3.75/1e6, h1*6/1e6, out*15/1e6, warm1h }"
done'
```

Column semantics:
- `turns` = iter=1 calls (one per game turn, including cold starts)
- `warm1h` = warm calls that re-wrote the 1h tier. **Healthy ≈ 0–2/day.** Sustained high values = the stable prefix is churning (the May 25–30 pathology: every warm call re-billed the 1h tier at $6/M; fixed May 31).
- Dollar split uses Sonnet 4.6 rates: read $0.30/M, 5m write $3.75/M, 1h write $6/M, out $15/M, in $3/M.

### Layer 1b — Haiku (router + aside) aggregation

The narrator script above only parses `narrator.sdk.usage`. Haiku is a **separate anchor** — run this too, over the same rotated-file set, or you will report "no Haiku" while it bills every turn.

```bash
bash -c '
cd ~/.sidequest/logs
files=$(ls sidequest-server.log sidequest-server.log.$(date +%Y%m%d)-* 2>/dev/null)
grep -h "llm.sdk.usage" $files 2>/dev/null | \
sed -E "s/.*caller=([a-z_]+) model=[^ ]* input=([0-9]+) output=([0-9]+) cache_read=([0-9]+) cache_write=([0-9]+) cost_usd=([0-9.]+).*/\1 \2 \3 \4 \5 \6/" | \
awk "{n[\$1]++; unc[\$1]+=\$2; cr[\$1]+=\$4; cost[\$1]+=\$6}
END{for(c in n) printf \"%-16s calls=%d uncached_in=%d cache_read=%d cost=\$%.4f\n\", c, n[c], unc[c], cr[c], cost[c]}"'
```

Per-call shape tells the story: `cache_read>0` means 91-3's cache-floor guard is reading the warm prefix; the `uncached_in` remainder (~3k for the router) is the per-turn variable tail — the only remaining lever now that the local rung is NO-GO (see Pitfalls).

## Layer 2 — OTEL span census

```bash
curl -s 'http://localhost:16686/api/traces?service=sidequest-server&operation=llm.request&limit=2000&lookback=72h' | \
python3 -c "
import json,sys
from collections import Counter
data=json.load(sys.stdin); c=Counter(); toks=Counter()
for t in data.get('data',[]):
    for s in t.get('spans',[]):
        if s.get('operationName')!='llm.request': continue
        tags={x['key']:x['value'] for x in s.get('tags',[])}
        m=str(tags.get('llm.model','?')); c[m]+=1
        toks[m]+=int(tags.get('llm.input_tokens',0))
print('spans:',dict(c)); print('uncached input:',dict(toks))
"
```

Caveat: `limit` counts **traces**, not spans — heavy days truncate. Use this for *shape* (per-call token profile), not absolute counts. Per-call uncached input ≈ `tokens/spans` identifies the caller: ~5.2k = Intent Router shape (~4.7k tools+system prefix + user content).

**Stale-store trap:** if a `lookback=6h` and a `lookback=72h` query return *identical* counts, Jaeger is handing you its whole retained store, not your window — the data is **stale, not live**. Do not attribute old span counts (e.g. aside calls from a prior session) to the current playtest. Cross-check call existence against the live log (Layer 1b) and the Console (Layer 3), which are time-accurate.

## Layer 3 — Admin API ground truth

Needs `ANTHROPIC_ADMIN_KEY` (`sk-ant-admin…`) in env. **Buckets are UTC** — expect ±1-day smear vs the local-time log table.

```bash
cd <orchestrator-root>
uv run --project . python scripts/anthropic_usage.py --days 7          # daily $ totals
uv run --project . python scripts/anthropic_usage.py --days 7 --raw    # per-model JSON
```

For per-model / per-key attribution beyond what the script prints:

```bash
curl -s "https://api.anthropic.com/v1/organizations/usage_report/messages?starting_at=<ISO>&ending_at=<ISO>&bucket_width=1d&group_by[]=api_key_id&group_by[]=model&limit=7" \
  -H "x-api-key: $ANTHROPIC_ADMIN_KEY" -H "anthropic-version: 2023-06-01"
```

Per-model pricing for estimates ($/M): Sonnet 4.6 = 3 in / 15 out / 3.75 w5m / 6 w1h / 0.30 read. Haiku 4.5 = 1 / 5 / 1.25 / 2 / 0.10. Opus = 15 / 75 / 18.75 / 30 / 1.50.

## Red Flags (what each anomaly means)

| Symptom | Diagnosis |
|---------|-----------|
| Admin $ ≫ log $ | Uninstrumented caller (subprocess `claude -p`, hooks, scripts on the same key). Group by api_key_id + model; match per-call token shape to known call sites. |
| Haiku/model shows `cache_creation=0` AND `cache_read=0` org-wide | That caller's prompt caching is **dead** — marker missing, beta header missing, or prefix below Haiku's 4,096-token cacheable floor (markers below the floor are accepted and silently never cache). |
| `warm1h` high in Layer 1 | Stable prefix churning at $6/M — the pre-May-31 pathology. Check what invalidates the 1h block. |
| `narrator.cache.both_writes_fired` WARNING | Noisy on iter=1 cold starts (both tiers MUST populate). Only meaningful when `cache_read>0`. |
| Calls/turn ratio ≫ expected | Count calls ÷ turns per subsystem. Intent Router should be ~1/turn; 8/turn means retries, fan-out, or a sibling caller sharing the prompt shape. |
| Zero Opus calls | **Expected** — the `NARRATION_IMPORTANT` Opus rung is intentionally unused (Keith, 2026-06-05: Sonnet is fine and cheaper). Not a dormant-trigger bug. |
| 5m-write $/turn creeping up across days | Volatile zone fattening (~11k tokens/turn as of 2026-06-05). The lever is ADR-110's deferred diff-with-anchor work. |

## Healthy Baselines (post-2026-05-31 tier fix)

- Cost/turn: **6.5–8¢** (narrator, Sonnet). The pre-fix plateau was 9–17¢.
- Prompt cache hit rate: **76–82%**.
- Output: ~320 tokens/call, stable.
- Cold starts: a handful/day under dev restarts; each ~12–16¢ (22–30k dual-tier write).
- Haiku (router) is ~1 call/turn (91-2 cut the 8x), ~7.5k total input = **~4.4k cache-read + ~3.1k uncached tail** (91-3 cache-floor guard working), ~$0.005/turn. Asides are ~0 unless a player actually sends OOC table-talk — do not assume aside traffic from stale Jaeger.
- **Local Qwen rung is NO-GO / OFF.** Story 92-2's A/B gate FAILED (qwen2.5:7b: 86% schema vs ≥95%, p95 24,134ms vs ≤5000ms; qwen3-coder:30b aborted). `SIDEQUEST_CLASSIFICATION_BACKEND` is unset → defaults to `anthropic` → router = Haiku. **Zero-Haiku does NOT mean the local rung is working — verify the env var and the gate before claiming it.** Remaining cost lever is cutting the ~3.1k uncached router tail ("cut the prompt size"), since route-to-local is dead.

## Known Pitfalls

- zsh word-splitting silently breaks multi-file greps — use `bash -c`.
- Log "days" are rotation-stamped local; Admin buckets are UTC.
- `narrator.sdk.usage` exists ONLY in the narrator loop. **Haiku adapters (`llm_factory.py`) DO log `llm.sdk.usage` (caller=intent_router|aside) since story 91-1** — grep that anchor (Layer 1b), not just the narrator one. Only subprocess `claude -p` callers emit neither log nor span.
- **The live server may run from a different clone than the one you pulled/read.** `ps` the `:8765` process for its `.venv` path (oq-1/oq-2/oq-3). Read that clone's logs and cite that clone's code. Auditing oq-3's tree while oq-1 serves the game = wrong code, wrong conclusions.
- **A grep returning zero is a hypothesis to disprove, not a finding.** Before reporting "X never fired," confirm you read the right log file (post-restart rotations included), the right anchor, and cross-checked the Console. The 2026-06-06 audit reported "no Haiku" three times while Haiku billed every turn — each time the cause was a wrong file/anchor, never an absent call.
- `ANTHROPIC_API_KEY` in the shell means every `claude -p` on the box bills the workspace key, while interactive Claude Code rides the OAuth subscription — the Console chart splits accordingly.
- Jaeger query `limit` truncates by trace; never use it for absolute call counts.
</run>

<output>
1. **Per-day table** — calls, turns, cost, ¢/turn, cache hit rate, 5m/1h write split, warm-1h re-write count.
2. **Reconciliation** — Layer 1 (log) total vs Layer 3 (Admin) total, gap attributed by model and per-call token shape.
3. **Findings** in GM playtest-finding format with billing/OTEL evidence (severity, expected vs actual, root cause: content/code/config).
4. **Routing** — code bugs (dead caching, missing spans, missing usage logs) go to the dev lane via pingpong/backlog with evidence; never fix code from this skill.
</output>
