# Save File Management

Reference for managing SideQuest save data — cleanup, inspection, migration.

> **ADR-115 changed everything here.** Saves no longer live in per-session SQLite
> `.db` files. They live in **one PostgreSQL database**, one `sessions` row per
> genre/world session. The old `~/.sidequest/saves/**/save.db` files are **never
> written anymore**; they survive only as read-only import sources. See the
> "Legacy SQLite files" section at the bottom for how to bring an old save forward.

## Where Saves Live

A single PostgreSQL database holds every save. The runtime resolves it from the
`SIDEQUEST_DATABASE_URL` environment variable, e.g.:

```
postgresql://USER@localhost:5432/sidequest
```

This is **required** — there is no silent default. If the variable is unset, the
server raises `MissingDatabaseUrlError` (see `sidequest/game/db_config.py`) and
fails loud rather than guessing a localhost connection. If Postgres is
unreachable, the app fails loud too — no fallback to SQLite.

Tests use a separate database via `SIDEQUEST_TEST_DATABASE_URL`
(`postgresql://USER@localhost:5432/sidequest_test`).

Provision both locally with:

```bash
just pg-up        # installs/starts postgresql@18, creates sidequest + sidequest_test
just pg-status    # service status
```

### Connection internals

- **Driver / pool:** psycopg3 + `psycopg_pool.ConnectionPool`.
- **Concurrency:** per-session row locks (`SELECT ... FOR UPDATE` on the
  `sessions` row). Read-side forensics are lock-free MVCC (plain pooled reads).
- **Repositories:** `sidequest/game/pg/` — `PgSaveRepository`,
  `PgDungeonRepository`, `PgTelemetrySink`, `PgForensicReader`. Forensic reads
  go through `PgForensicReader` (the old `SqliteStore.open()` path is retired).

## Schema

The schema is created and versioned by **Alembic** (raw SQL via `op.execute`, no
ORM). Migration files live in `sidequest-server/alembic/versions/`:

- `0001_initial_unified_schema.py` — the unified schema (ADR-115 direct port)
- `0002_asset_ledger.py` — per-session runtime asset ledger

All per-session tables carry a `session_id BIGINT` foreign key referencing
`sessions(session_id)` **`ON DELETE CASCADE`** (verified in
`0001_initial_unified_schema.py` / `0002_asset_ledger.py`).

### The `sessions` table

The natural anchor for everything. Columns (verified against
`0001_initial_unified_schema.py`):

| Column | Type | Notes |
|--------|------|-------|
| `session_id` | `BIGINT` identity | Primary key (integer surrogate) |
| `session_slug` | `TEXT` | `NOT NULL UNIQUE` — natural key (e.g. `2026-05-17-coyote_star-mp`) |
| `mode` | `TEXT` | `CHECK (mode IN ('solo', 'multiplayer'))` |
| `genre_slug` | `TEXT` | |
| `world_slug` | `TEXT` | |
| `claude_session_id` | `TEXT` | nullable |
| `schema_version` | `INTEGER` | default `1` |
| `created_at` | `TEXT` | ISO-8601 |
| `last_played` | `TEXT` | ISO-8601 |

### Per-session tables

Each of these has a `session_id` FK with `ON DELETE CASCADE` (verified):

| Table | Shape | Contents |
|-------|-------|----------|
| `game_state` | one row / session | `snapshot_json` (full GameSnapshot as JSON), `saved_at` |
| `world_save` | one row / session | `payload_json`, `saved_at` |
| `narrative_log` | append-only | `round_number`, `author`, `content`, `tags`, `created_at` |
| `lore_fragments` | per fragment | `category`, `content`, `source`, `turn_created`, `metadata_json` |
| `scenario_archive` | one row / session | `scenario_json`, `saved_at` |
| `scrapbook_entries` | per entry | `turn_id`, `scene_title`, `scene_type`, `location`, `image_url`, `narrative_excerpt`, `world_facts`, `npcs_present`, `render_status` |
| `events` | per event | `seq`, `kind`, `payload_json`, `created_at` (PK `session_id, seq`) |
| `projection_cache` | per event/player | `event_seq`, `player_id`, `include`, `payload_json` (FK to `events`) |
| `turn_telemetry` | per telemetry row | `event_seq`, `round`, `ts`, `component`, `event_type`, `payload_json` |
| `location_promotions` | per promotion | `region_id`, `entity_id`, `provenance`, `label`, ... |
| `asset_ledger` | per artifact | `r2_key` (PK), `asset_type`, `entity_ref`, `created_turn`, `created_at` |

Plus the dungeon family (`dungeon_map`, `dungeon_edge`, `dungeon_frontier`,
`dungeon_mutation_overlay`, `dungeon_complication_ledger`, `dungeon_meta`) — all
likewise `session_id`-keyed with `ON DELETE CASCADE`.

## Listing Saves

### Via the forensic reader / REST (preferred)

The GM dashboard's State tab is backed by `PgForensicReader.list_saves()`, exposed
at the read-only REST endpoint `GET /api/debug/saves`. Each row carries
`slug`, `genre`, `world`, `created_at`, `last_played`, `last_activity_ts` (ms),
plus `telemetry_rows` and `mechanical_rows` counts, sorted newest-first. With the
server running:

```bash
curl -s http://localhost:8765/api/debug/saves | jq .
```

`PgForensicReader` (`sidequest/game/pg/forensic.py`) also provides
`build_timeline(session_id)` and `build_turn_bundle(session_id, round_number)` for
per-round drill-down — the same data the GM forensics panel renders.

### Via psql

Connect to whatever `SIDEQUEST_DATABASE_URL` points at and query `sessions`
directly. (Exact column names verified against the migration above.)

```bash
psql "$SIDEQUEST_DATABASE_URL"
```

```sql
-- All saves, newest first
SELECT session_slug, genre_slug, world_slug, mode, created_at, last_played
FROM sessions
ORDER BY last_played DESC;

-- Count by genre
SELECT genre_slug, COUNT(*)
FROM sessions
GROUP BY genre_slug
ORDER BY COUNT(*) DESC;
```

## Inspecting a Save

Look up the `session_id` for a slug, then drill into the per-session tables.

```sql
-- Resolve the surrogate id
SELECT session_id FROM sessions WHERE session_slug = '2026-05-17-coyote_star-mp';

-- Narrative log size for a session
SELECT COUNT(*) FROM narrative_log WHERE session_id = :sid;

-- Last few narrative entries
SELECT round_number, author, substr(content, 1, 80)
FROM narrative_log
WHERE session_id = :sid
ORDER BY id DESC
LIMIT 5;

-- Event stream size
SELECT COUNT(*) FROM events WHERE session_id = :sid;
```

`snapshot_json` in `game_state` is stored as `TEXT` holding the serialized
GameSnapshot. To pull a field, cast and use Postgres JSON operators (the exact
JSON path depends on the GameSnapshot shape; treat the snapshot as opaque unless
you know the structure):

```sql
SELECT (snapshot_json::jsonb) -> 'characters'
FROM game_state
WHERE session_id = :sid;
```

For programmatic, lock-free inspection prefer `PgForensicReader.snapshot_json(session_id)`,
which returns the stored dict verbatim without deserializing through the domain
model.

## Cleanup Procedure

Deleting a save means deleting its rows in Postgres. Because every per-session
table declares `ON DELETE CASCADE` on its `session_id` FK (verified in the
migration), **deleting the `sessions` row cascades to all child rows** —
narrative, events, telemetry, scrapbook, dungeon tables, asset ledger, etc.

1. **List everything** with the queries above and identify keepers.
2. **Back up first** (see below) if there's any doubt.
3. **Delete by slug** — the cascade handles the rest:

   ```sql
   DELETE FROM sessions WHERE session_slug = 'SLUG-TO-REMOVE';
   ```

4. **Delete by genre** (drops every session for a genre and all their children):

   ```sql
   DELETE FROM sessions WHERE genre_slug = 'GENRE-TO-REMOVE';
   ```

5. **Verify** what remains:

   ```sql
   SELECT session_slug, genre_slug, last_played FROM sessions ORDER BY last_played DESC;
   ```

> The cascade is the *only* deletion mechanism documented here because it is the
> only one the schema guarantees. Do not hand-delete child rows table-by-table —
> let the `sessions` delete cascade.

Saves are **durable by default**. Never reap save-referenced artifacts
(portraits, audio, anything in `asset_ledger`) on a timer.

## Backup Before Surgery

Use `pg_dump` against the configured database. Dump a whole DB, or scope to one
session with `--table` filters if you only need specific rows.

```bash
# Full database backup
pg_dump "$SIDEQUEST_DATABASE_URL" -Fc -f ~/.sidequest/db-backup-$(date +%Y%m%d).dump

# Restore
pg_restore -d "$SIDEQUEST_DATABASE_URL" ~/.sidequest/db-backup-YYYYMMDD.dump
```

(A row-scoped dump of a single session is fiddly because of the FK web; a full
`-Fc` dump is the safe default before destructive work.)

## Migration

### Applying / upgrading the schema

Alembic owns the schema. Both the runtime pool and the migration runner resolve
the URL through `sidequest.game.db_config` (`alembic.ini` + `alembic/env.py`
call `alembic_url()`), so it is defined in exactly one place. From
`sidequest-server/`:

```bash
alembic upgrade head     # apply all migrations to the configured DB
alembic current          # show the applied revision
alembic downgrade -1     # roll back one revision
```

Run against the right DB by exporting `SIDEQUEST_DATABASE_URL` first.

### Importing a legacy SQLite save

A read-only importer brings **one** legacy `save.db` into Postgres:

```bash
python -m sidequest.game.importer
```

What it does (see `sidequest/game/importer.py`):

- Opens the source SQLite file **read-only + immutable** — it is never written,
  checkpointed, or copy-then-mutated.
- Performs **FK-ordered inserts** (`sessions` → per-session tables →
  `projection_cache` last) inside **one transaction**, so a partial failure rolls
  back the whole import.
- **Normalizes** `created_at` / `last_played` / `saved_at` / `ts` timestamps to
  T-isoformat (load-bearing for forensic round bucketing) while preserving
  `seq`/`round`/`payload`/`content` verbatim.
- Returns a per-table `ImportSummary` row count for a round-trip check.

> The importer is intentionally narrow: it covers exactly the tables a real save
> populates (`session_meta`/`games`, `game_state`, `narrative_log`,
> `scrapbook_entries`, `events`, `turn_telemetry`, `projection_cache`). If a
> source SQLite file carries rows in *other* tables (e.g. `world_save`,
> `lore_fragments`, `location_promotions`, `dungeon_*`), it **raises rather than
> silently dropping them** (No Silent Fallbacks). It also has no argparse CLI —
> the target file path is set in `__main__`; point it at your save and run with
> the target `SIDEQUEST_DATABASE_URL` exported.

## Legacy SQLite Files

Old saves used to live at:

```
~/.sidequest/saves/{genre}/{world}/{character}/save.db   (+ -shm / -wal WAL companions)
```

After ADR-115 these files are **no longer written** by the running game — the
SQLite-per-session store (`SqliteStore`, the save write lock, WAL tuning) is
retired. Existing files on disk are inert: nothing reads them at runtime, and
nothing keeps them in sync.

To bring an old save forward, import it with `python -m sidequest.game.importer`
(see Migration above). Until imported, an old `save.db` is just an archive — safe
to leave in place, safe to back up, but not a live save.
