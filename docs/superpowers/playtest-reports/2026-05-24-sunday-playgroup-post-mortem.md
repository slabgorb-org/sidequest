# Sunday Playgroup Session — Post-Mortem

**Date:** 2026-05-24
**Mode:** Multiplayer (Keith + remote players, multiple IPv6/IPv4 origins observed in server logs)
**Primary session:** `2026-05-24-dust_and_lead-mp` (genre `spaghetti_western`, world `dust_and_lead`)
**Sessions touched (lobby/restart sprawl):** `dust_and_lead-mp`, `franchise_nations-mp`, `franchise_nations`, `franchise_nations-2`, `franchise_nations-3`, `coyote_star`, `annees_folles`, `annees_folles-2`, `annees_folles-3`, `beneath_sunden` — every one re-bound today; many short-lived after a disconnect.
**Save artifacts:** `~/.sidequest/saves/games/2026-05-24-dust_and_lead-mp/save.db` (+ `.db-shm`, `.db-wal` — WAL still uncheckpointed at 4.0 MB after the session ended at ~13:59 local; left in place for forensic inspection rather than truncated)
**Server-process churn:** 18 process rotations between 09:06 and 14:00 (`~/.sidequest/logs/sidequest-server.log.20260524-*`). Several were intentional (in-session IntentRouter fix deploys); most were not.
**Outcome:** **Bad.** Players intermittently stuck mid-round in MP, repeated reconnect/restart cycles, IntentRouter empty-response failures at narration start. Single-player improved markedly after the in-session IntentRouter fix (`#410`); MP did not.

---

## Outcome — honest version

This was not a feature playtest. It was a discovery session where three different failure modes layered on top of each other and Keith spent most of the table-time triaging instead of playing. The IntentRouter empty-response fix (`#410`) and the `close_store` re-bind fix (`#411`) shipped during the session and rescued SP cleanly, but the MP-specific failure modes — stuck rounds and a previously-silent telemetry data race — were not addressed and remain open.

The most important finding is **not** any of the user-visible failures. It is the SQLite write race documented in §3 below, which has been silently corrupting OTEL telemetry every turn for at least six days (since `2026-05-18`, per the comment in `persistence.py:297-298`) and which makes the GM panel structurally untrustworthy as a lie-detector for any MP playtest. Per CLAUDE.md OTEL Observability Principle, *if a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising.* For four of the five busiest playtest hours today, mechanical census and trope census never reached the panel — every turn's "did combat fire?" lie-detector question was unanswerable.

---

## 1. The Bomb Inventory

Ordered by severity within the session, not by detection order.

### Bomb #1 — Stuck MP rounds (CRITICAL, OPEN)

**User-reported.** Players were "constantly getting stuck in MP rounds."

**Log signature** (worst hour, log `20260524-131755`):

```
turn_status_active player=Buffalo Byron   (handlers/player_action.py:355)
turn_status_active player=Zanzibar Jones
turn_status_active player=Colt Kingsley
turn_status_active player=Hiken
turn_status_active player=Caliente Romano
session.turn_status_resolved player=Buffalo Byron       (one player narrates)
   ... no other player resolutions for this barrier ...
turn_status_active player=Buffalo Byron   (re-activated)
turn_status_active player=Hiken           (re-activated)
... pattern repeats ...
```

Five players submit, one player's narration completes, the rest re-submit instead of resolving. This is *the* stuck-round signature.

**Hypothesis (not yet verified by code-walk in this report):** The submit-and-wait barrier counts submissions correctly when all five players hold a stable WebSocket, but when one disconnects-and-reconnects between submits (WS close codes `1001` and `1005` are abundant in the logs — these are normal browser/tab-close codes, not server crashes), the barrier state can desynchronize from the lobby-participant set. ADR-036's barrier is held by `snapshot.turn_manager._submitted` — explicitly runtime-only and skipped in serialization (`turn.py:53-55, 63-65`). The `phase` and `player_count` *are* persisted. A reconnect that rebinds `_snapshot` (after the just-shipped `close_store` fix in `#411`) reloads `phase=InputCollection` and `player_count=N` but materializes a fresh `_submitted=set()`. Whether the room's shared `_snapshot.turn_manager._submitted` survives the reconnect (because all sockets share the room's snapshot) depends on whether `close_store` was actually fired — and `close_store` only fires on **last-disconnect** per `#399`. So a single player tab-dropping mid-round should *not* nuke the barrier, but the failure pattern in the log suggests something *does* — either the player_count is being recomputed and reduced when a player drops (so 4-of-5 fires the barrier with one player not actually heard from), or some other path is clearing `_submitted` between submissions.

**Suspect code:** `handlers/player_action.py:408-413` — `set_player_count(playing_count)` is called *every submission* off `session._room.playing_player_count()`. If `playing_player_count()` returns a value that fluctuates with disconnect events (and there's no evidence yet that it doesn't), the barrier denominator drifts mid-round.

**Why this matters more than the cosmetic UI bug:** the dispatch CAS (`session._room.last_dispatched_round >= current_interaction`, `player_action.py:486-493`) guarantees only one narrator dispatches per round — but it does *not* guarantee everyone got narrated. If the barrier fires with the wrong denominator, one player gets a turn, the rest are stuck "submitted" forever, and re-submitting wedges them further.

**Not blocked by this bomb:** SP turns. SP barrier is `playing_count == 1` and fires on first submission. The post-IntentRouter-fix improvement Keith observed is consistent with SP being unaffected by this bug.

**Action:** Story 36-? — *Audit `playing_player_count()` and the per-submission `set_player_count()` call for disconnect-driven denominator drift; add a `barrier.denominator_drift` watcher event that fires whenever `set_player_count` changes value within a single `interaction`; replay a recorded MP session with a forced disconnect mid-round.*

---

### Bomb #2 — IntentRouter empty-response (HIGH, PARTIALLY PATCHED IN-SESSION)

**User-reported and self-diagnosed.** IntentRouter was named as a "big source of problems."

**Patches shipped during the session:**

- `e4a3a29` `feat(59-4): atomic IntentRouter cutover — retire begin_confrontation (ADR-113)` *(yesterday)*
- `9121458` `fix(narrator): ADR-105 B3 public-safe ENFORCEMENT — mechanical scrub (#408)`
- `165678f` `fix(intent-router): diagnose empty-response failures + env-gated degrade unblock (#410)`

The atomic cutover (`59-4` / ADR-113) retired the `begin_confrontation` fallback path. After cutover, an IntentRouter failure no longer falls back to a soft mechanical engagement — it can only either route to a confrontation, route to a non-confrontation intent, or fail. The `#410` "env-gated degrade unblock" is presumably the temporary safety net that lets a router failure not hard-block the turn, which is what made SP playable again.

**Post-fix SP improvement** (per user): real and immediate. **Post-fix MP improvement:** not observed — the MP failure modes are not IntentRouter-driven.

**Remaining surface that may still be raw** (verify before claiming closed):

- `narrator.region_patch_check` and `validation_warning` both appear once each in the dropped-telemetry list (see §3) — these are likely from the IntentRouter→narrator handoff and were lost to the SQLite race. We cannot say from log evidence alone whether the router was healthy after the fix; the telemetry that would have proven it was eaten.
- `subsystem_exercise_summary` was also dropped once. If that's the post-turn router-vs-engine lie-detector watcher (`59-3`), then *the lie-detector for the thing we just patched is itself blind because of Bomb #3.*

**Action:** Story 59-? — *Re-run a recorded MP session against `develop` after Bomb #3 is fixed; verify `subsystem_exercise_summary` and `narrator.region_patch_check` events land in Jaeger; close `59-4` follow-ups only if they do.*

---

### Bomb #3 — Telemetry SQLite write race (CRITICAL, NEWS TO USER, OPEN — root cause identified)

**Not user-reported.** Surfaced by reading the rotated server logs.

**Symptom:** Every MP turn drops at least two OTEL watcher events with `sqlite3.OperationalError: database is locked` at `watcher_hub.py:403`. The wrapping `try/except` (`watcher_hub.py:404-411`) **silently swallows the failure by design** — telemetry must never crash a turn. So the GM panel goes blind without anyone noticing at the table.

**Per-log lock-failure counts** (today's playtest window only):

| Log | Lock failures | Drop categories (event_type) |
|---|---|---|
| `20260524-123103` | 18 | `census` (×9), `trope_census` (×9) |
| `20260524-131755` | 10 | mixed: `census`, `state_transition`, `trope_census`, `action_reveal.composing`, `shared_world_frame_broadcast`, `turn_status`, `turn_complete`, ... |
| `20260524-132958` | 22 | mostly `census` and `state_transition` |
| `sidequest-server.log` (current) | 11 | mixed |

**Total dropped events across the window** (deduplicated by event_type):

```
38 × census                          (every MP turn's mechanical-state record)
17 × state_transition                (snapshot save acknowledgement)
 9 × trope_census                    (trope-engine activity record)
 4 × action_reveal.composing         (MP sealed-letter UI signal)
 3 × shared_world_frame_broadcast    (MP world sync notice)
 1 × turn_status                     (the turn-coordinator state event)
 1 × turn_complete                   (validator's end-of-turn signal)
 1 × subsystem_exercise_summary      (router-vs-engine lie-detector — Bomb #2's verifier!)
 1 × prompt_assembled                (narrator prompt audit)
 1 × narrator.region_patch_check     (region-patch verify)
 1 × game_state_snapshot
 1 × session.cost_running_total
 1 × state.footnote_fact_id_minted
 1 × validation_warning
```

**Compounding factor — OTLP dormant.** Every rotated log also contains:

```
WARNING [sidequest.telemetry.setup] otel.otlp_dormant —
    SIDEQUEST_OTLP_ENDPOINT is unset; no spans will leave this process.
```

So events that *did* persist to SQLite still never reached Jaeger. The GM panel for this session is doubly blind: locked out of the local sink **and** not exporting upstream.

**Root cause — process-wide cross-thread connection race.** Found by code-walk:

`SqliteStore.open` (`persistence.py:347`) opens `sqlite3.connect(path, check_same_thread=False)`. The docstring at `persistence.py:340-345` is explicit about why:

> `check_same_thread=False` is intentional: the watcher hub's
> telemetry sink (`_persist_turn_telemetry`) is invoked from any
> thread that calls `publish_event` — narrator workers, the
> renderer, the daemon client. **Per-write serialization is enforced
> at the watcher layer with a module-level lock; without that lock
> this flag would not be safe.**

But that promise is broken. The two write paths to the shared connection are:

1. **`SqliteStore.save()`** at `persistence.py:439-448`:
   ```python
   with self._conn:                  # opens implicit txn
       self._conn.execute(INSERT OR REPLACE INTO game_state ...)
       self._conn.execute(UPDATE session_meta ...)
                                     # commits on __exit__
   ```
   *Acquires no `_persist_lock`.*

2. **`watcher_hub._persist_turn_telemetry`** at `watcher_hub.py:395-403`:
   ```python
   with _persist_lock:
       if conn.in_transaction:                       # ← rides whoever opened it
           ev_seq = conn.execute("SELECT MAX(seq) FROM events").fetchone()[0]
           conn.execute(insert, (ev_seq, ...))
       else:
           with conn:                                 # own short txn
               conn.execute(insert, (None, ...))
   ```
   *Acquires `_persist_lock`.*

Two consequences flow from this:

**(a) "Database is locked" failures.** When path (1) is mid-flight (`store.save` holds an implicit write transaction on the connection) and path (2) tries to execute, Python's `sqlite3` module returns `OperationalError: database is locked` because the connection's per-statement state machine can't serve two concurrent executes — even with `busy_timeout=5000`, because busy_timeout is for *inter-connection* contention against the WAL, not *intra-connection* statement contention. `_persist_lock` does not help here because path (1) does not acquire it.

**(b) Cross-purpose transaction sharing.** When `conn.in_transaction` returns `True` from path (2), the `else` branch is skipped and the telemetry INSERT rides the *snapshot save's* transaction. The snapshot save then commits whatever telemetry rows happened to land in its window. This is "working" in the sense that some rows do persist, but it is **two unrelated subsystems sharing a transaction boundary by accident** — a recipe for partial-commit bugs, telemetry rows attached to the wrong session save, and "telemetry persisted" timestamps that don't match wall-clock.

**Why the 2026-05-18 `busy_timeout=5000` fix didn't actually fix it.** The comment at `persistence.py:294-298` attributes the existing busy_timeout to the same symptom on 2026-05-18. But `busy_timeout` is the wrong tool for this race. It tells SQLite to retry against another *connection's* WAL lock; it does nothing for a single connection's statement-level contention or for the `in_transaction` branch in `_persist_turn_telemetry`. The symptom has continued since 2026-05-18 in every MP playtest. We just stopped noticing because the failures are wrapped in `except Exception: logger.warning`.

**The structural fix is one of three** (Architect to recommend in the closing story, not blind-pick here):

- **(i) One write mutex for all writers**, not just telemetry. Either elevate `_persist_lock` out of `watcher_hub.py` and require every write site (including `SqliteStore.save`, `narrative_log` appends, world_save writes) to acquire it; or move to a single dedicated writer thread fed by a queue. The "one mutex" pattern preserves the current connection model but actually keeps the doctrine the docstring already promises.
- **(ii) Two connections, one writer.** Telemetry on a *separate* `sqlite3.Connection` (still `check_same_thread=False`) so writes go through the WAL like normal SQLite multi-writer access; `busy_timeout=5000` will then actually do its job. Costs one extra open file handle per session.
- **(iii) Telemetry off the save DB entirely.** Move the `turn_telemetry` table into a per-process telemetry SQLite (or an OTLP-only pipeline) so the save DB never has more than one writer. Largest blast radius but cleanest separation — and reopens the conversation about whether telemetry should be inline at all (it's currently in the save file because nothing else durable existed).

I am not picking between these in this post-mortem. The story that fixes Bomb #3 should propose all three and pick one with a clear rationale.

**Action:** Story 31-? — *Eliminate the `SqliteStore` write race. Architect recommends; Dev implements one of (i)/(ii)/(iii); TEA writes a regression test that fires concurrent `publish_event` and `store.save()` from different threads and asserts zero `turn_telemetry.sink_failed` warnings over 100 turns.* **Treat this as a Sebastien-the-dev concern** (lie-detector restoration), not a Sebastien-the-player feature.

---

### Bomb #4 — MP session sprawl (MEDIUM, OPEN)

**Symptom:** Ten session DBs created today across six different worlds — `franchise_nations-mp`, `-2`, `-3`, plus `annees_folles`, `-2`, `-3`. Each suffix increment is a player typing the wrong slug, or the lobby refusing to merge them onto the existing MP session, or the deterministic-slug doctrine being defeated by a UI path that doesn't honor it.

**Background:** Per memory, MP session URLs *should* be deterministic — `/play/{date}-{world}-mp` rejoins existing sessions. We're seeing the dispatcher create `-2`, `-3` suffixes instead of rejoining the canonical `-mp`. Either:

- The lobby flow is computing a different slug per attempt (e.g., a fresh timestamp or a collision-suffix when it shouldn't), **or**
- Players are landing in lobbies that look identical but resolve to different rooms because the canonical `-mp` room was held by stale players (now-disconnected) and the system refused to evict them.

**Action:** Story 36-? — *Audit the lobby slug-resolution path; assert one MP slug per `{date}-{world}-mp`; force-evict abandoned seats older than N minutes; emit `lobby.slug_collision` watcher event whenever a `-N` suffix is appended.*

---

### Bomb #5 — `close_store` reconnect crash (HIGH, PATCHED IN-SESSION)

Shipped today: `eba8100 fix(session-room): close_store must null _snapshot/_session for clean re-bind (#411)`.

Per the prior memory entry on this incident (`close_store partial teardown bombs reconnects`), the previous teardown nulled only `_store` and left `_snapshot` set, so the next `bind_world` early-returned on its `_snapshot is not None` idempotency check and never re-attached — every reconnect crashed at `sd.store.recent_narrative`. The fix syncs all three at the teardown seam.

**Confirmed live.** The number of `session.disconnect_save` events followed by `WebSocket /ws [accepted]` reconnects in today's logs (dozens) suggests the fix was load-tested by the playtest itself, and the only post-fix crash log line we see in subsequent log rotations is the unrelated `sqlite3.OperationalError` from Bomb #3.

**Action:** Close `61-followup-C`/`#399`-family work, and *write a regression test that exercises last-disconnect-then-rebind* if one doesn't exist already. (Suggest `tests/server/test_session_room_close_store.py::test_rebind_after_close_clears_snapshot`.)

---

## 2. Bombs found by inspection, not in user report

These were turned up by the post-mortem investigation and are surfaced here in case they're known/intentional:

- **OTLP endpoint dormant** (`SIDEQUEST_OTLP_ENDPOINT` unset in `just up`). Even if Bomb #3 is fixed, telemetry isn't reaching Jaeger. The GM panel reads from the local SQLite, so the panel will work post-fix, but Jaeger-side investigation (the cross-process trace flow per ADR-103) is off. Suggest adding `SIDEQUEST_OTLP_ENDPOINT=localhost:4317` to the `just up` env so a Jaeger sidecar (if running) catches spans automatically. Not load-bearing for today's failures.
- **`turn_manager._submitted` runtime-only & undocumented in failure mode.** The pydantic-level "skipped in serialization" comment at `turn.py:53-55` is correct for SP semantics but doesn't surface the MP failure mode: the room-shared `_snapshot.turn_manager._submitted` can be silently truncated by any code path that re-bind-loads the snapshot from disk. Not a sync bug per se — but the comment should at least *name* the MP fragility, especially with Bomb #1 still open. Suggest adding a tripwire watcher event (`barrier.submitted_set_reset`) whenever `_submitted` transitions from non-empty to empty *outside* `record_interaction`/`advance`/`advance_round`/`submit_input(threshold-hit)`.

---

## 3. What's actually grade-able from this session

Almost nothing on the mechanical side. Of the ~50 turn-level mechanical watcher events that should have landed for `dust_and_lead-mp`, ~38 `census` and ~9 `trope_census` are missing. The narration prose path is intact in the saves (you can read every turn back from `~/.sidequest/saves/games/2026-05-24-dust_and_lead-mp/save.db`), and `session.narration_complete` lines confirm that narration actually ran. So you can re-read the *story* but you cannot reconstruct *which mechanics fired or didn't*.

**Per memory rubric, evaluate this session as a Keith-the-dev observability failure, not a Keith-the-player narrative failure.** The Sebastien-the-player math-visibility question isn't even askable: the math isn't in the panel.

---

## 4. Recommended sprint reaction

Suggest these stories, in this order:

1. **Bomb #3 first.** Until the SQLite race is closed, every other MP fix lands without verification. (Story candidate: epic 31 or epic 60 — pick whichever currently houses lie-detector infra.)
2. **Bomb #1 second**, with the verifier from Bomb #3 in place. Add the `barrier.denominator_drift` and `barrier.submitted_set_reset` tripwires; re-run a recorded MP session against develop with a forced mid-round disconnect.
3. **Bomb #4 third.** Lobby slug-collision audit. UX-and-server, lower urgency.
4. **Bomb #2 verification close-out.** Re-run a recorded SP and MP session after #3, confirm `subsystem_exercise_summary` actually lands.

These are recommendations from the Architect lane, not stories I'm authorizing. PM/SM owns prioritization; this post-mortem is the input.

---

## 5. What I am explicitly *not* claiming

- I have **not** code-walked the `playing_player_count()` denominator-drift hypothesis in Bomb #1 — that's where the next investigative pass should start.
- I have **not** verified that the post-`#410` IntentRouter is healthy in MP — the telemetry that would prove it was eaten by Bomb #3, so the proof has to wait for Bomb #3's fix.
- I have **not** counted *which* players were stuck (only that the pattern existed); the per-player breakdown is recoverable from the surviving `~/.sidequest/saves/games/2026-05-24-dust_and_lead-mp/save.db` if needed.
- I have **not** opened backlog stories — the recommendations in §4 are bullet points, not commitments.
- I have **not** touched any code. Per Architect lane: design recommendations only.
