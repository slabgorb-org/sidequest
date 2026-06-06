---
name: sq-llm-costs
description: LLM cost and cache forensics — reconcile server-log narrator costs against the Anthropic Admin API, attribute per-model spend, detect dead caching and invisible callers. Use when analyzing API costs, auditing cache efficiency, or when the Console bill doesn't match expectations.
---

# sq-llm-costs — LLM Cost & Cache Forensics

<run>
You are running a **cost reconciliation audit**. The cardinal rule, learned 2026-06-05: **server logs only see the narrator.** The Console bill includes consumers the logs are blind to. Always reconcile all three layers before drawing conclusions.

## The Three Layers (run all of them)

| Layer | Source | Sees | Blind to |
|-------|--------|------|----------|
| 1. Server logs | `narrator.sdk.usage` lines | Narrator Sonnet loop only | Haiku router/asides, `claude -p` subprocesses, anything off-box |
| 2. OTEL / Jaeger | `llm.request` spans | Instrumented SDK call sites | Subprocess callers, span-less paths, trace-limit truncation |
| 3. Admin API | `scripts/anthropic_usage.py` | **Everything billed to the org** | Per-turn attribution (no request counts) |

If Layer 3 ≫ Layer 1, something uninstrumented is spending money. That is a finding, not noise.

## Layer 1 — Server-log narrator aggregation

Usage lines are emitted by `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (grep anchor: `narrator.sdk.usage`). Logs live at `~/.sidequest/logs/sidequest-server.log` with rotations `*.log.YYYYMMDD-HHMMSS` (30-day retention, **rotation-stamped local time** — each "day" can include the prior evening's tail).

**Run under `bash -c`, not zsh** — zsh does not word-split `$files`, which silently yields zero matches.

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
- Haiku (router + asides) *should* be ~1 call/turn with a warm 1h prefix → cents/day. (As of 2026-06-05 it is NOT: caching dead + ~8 calls/turn ≈ $3+/day. See pingpong/backlog.)

## Known Pitfalls

- zsh word-splitting silently breaks multi-file greps — use `bash -c`.
- Log "days" are rotation-stamped local; Admin buckets are UTC.
- `narrator.sdk.usage` exists ONLY in the narrator loop. Haiku adapters (`llm_factory.py`) emit OTEL spans only; subprocess `claude -p` callers emit neither.
- `ANTHROPIC_API_KEY` in the shell means every `claude -p` on the box bills the workspace key, while interactive Claude Code rides the OAuth subscription — the Console chart splits accordingly.
- Jaeger query `limit` truncates by trace; never use it for absolute call counts.
</run>

<output>
1. **Per-day table** — calls, turns, cost, ¢/turn, cache hit rate, 5m/1h write split, warm-1h re-write count.
2. **Reconciliation** — Layer 1 (log) total vs Layer 3 (Admin) total, gap attributed by model and per-call token shape.
3. **Findings** in GM playtest-finding format with billing/OTEL evidence (severity, expected vs actual, root cause: content/code/config).
4. **Routing** — code bugs (dead caching, missing spans, missing usage logs) go to the dev lane via pingpong/backlog with evidence; never fix code from this skill.
</output>
