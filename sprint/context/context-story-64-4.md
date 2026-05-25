---
parent: context-epic-64.md
workflow: tdd
---

# Story 64-4: Schema-validate pack file contents — model_validate pass in the validator

## Business Context

The pack validator currently lies by omission: a green `just
content-validate-all` means "all required files exist", not "the pack loads".
During epic 64's review the seven new world files had to be hand-run through
the pydantic models to prove they parse — the validator could not. This story
makes that proof automatic, so a malformed `tropes.yaml` or `archetypes.yaml`
fails at validation time instead of at runtime when a player loads the world.
The value is authoring confidence: content authors (the GM agent, future
world-builders) get a real signal, not a file-existence checkbox.

## Technical Guardrails

**Reuse the loader's models — do not reimplement schema.** The authority is
`sidequest/genre/models/*` (and `dungeon/themes.py`, `game/projection/`). For
each present, schema-known file, parse it and run it through its model:

| File | Model / loader entry |
|------|----------------------|
| world `archetypes.yaml`, genre `archetypes.yaml` | `genre.models.character.NpcArchetype` |
| world/genre `tropes.yaml` | `genre.models.tropes.TropeDefinition` |
| `portrait_manifest.yaml` | `genre.models.pack.PortraitManifestEntry` (handle both `{characters: [...]}` and bare-list shapes — see `loader._load_portrait_manifest` l.638-645) |
| `archetype_constraints.yaml` | `genre.models.archetype_constraints.ArchetypeConstraints` |
| `projection.yaml` | `game.projection.rules.load_rules_from_yaml_path` + `validator.validate_projection_rules` |
| `themes/*.yaml` | `dungeon.themes.load_theme_palette` (palette-level) |

- **No silent fallback:** the swallowed `world.yaml` YAMLError at
  `pack.py:203-204` (`except (yaml.YAMLError, UnicodeDecodeError): pass`) must
  become a reported ERROR.
- **Import-cycle hazard:** importing `genre.loader` transitively reaches the
  `session_handler`/`websocket_session_handler` cycle (64-6). If 64-6 has not
  landed, importing the loader graph inside the validator may fail — coordinate
  ordering or import the leaf model modules directly rather than the loader.
- Keep the structural checks intact; this is an *added* content-validation pass
  that runs only on files that exist and have a known schema. Files with no
  registered schema are not errors (don't regress the orphan-warning behavior).
- Reuse `_find_default_schema` / `packs_in`; preserve the PASS/FAIL/warning
  output format and the `--verbose` flag.

## Scope Boundaries

**In scope:**
- A content-validation pass in `validate/pack.py` that `model_validate`s every
  present, schema-known pack-tier and world-tier file.
- Parse failures reported as ERRORs carrying filename + the pydantic/YAML message.
- Fix the swallowed `world.yaml` parse error to report loudly.
- Keep all 10 live packs PASSING after the pass is added.

**Out of scope:**
- Cross-reference / ID-membership / adjacency checks — that is 64-5.
- Breaking the import cycle — that is 64-6 (this story consumes the fix, or
  side-steps it by importing model leaves directly).
- Any change to `pack_schema.yaml` or to the genre models themselves.

## AC Context

1. **Validator runs each present, schema-known file through its model and
   reports parse failures as ERRORs (filename + message).** Test: point the
   validator at a synthetic pack whose `archetypes.yaml` has an extra/forbidden
   field; assert a FAIL with the filename and the pydantic error text. Edge
   case: `portrait_manifest.yaml` in both `{characters: [...]}` and bare-list
   forms must both validate.
2. **A deliberately malformed world `tropes.yaml`/`archetypes.yaml` produces a
   FAIL, not a PASS.** Test: fixture pack with a `tropes.yaml` missing a
   required field → FAIL. This is the regression the story exists to prevent;
   it would currently PASS.
3. **`world.yaml` YAML parse errors are reported loudly (pack.py:203-204).**
   Test: fixture world with invalid YAML in `world.yaml` → ERROR mentioning the
   file, not a silently-skipped draft check.
4. **All 10 live packs still PASS.** Test: run `just content-validate-all`
   (or the validator over `genre_packs/`) → 0 errors across all 10 packs. Use a
   real-content smoke check, not a fixture, for this one AC — it guards against
   the new pass falsely rejecting shipped content.

## Assumptions

- The genre models (`NpcArchetype`, `TropeDefinition`, etc.) are the correct
  and current schemas; the live packs already satisfy them (verified in epic 64
  review). If a live pack fails the new pass, that is a real latent bug to
  surface, not a reason to weaken the validator.
- 64-6 lands first, or the validator imports model leaf-modules directly to
  avoid the loader's import cycle. If neither holds, log a deviation.
- Test fixtures live under `tests/cli/validate/` (next to
  `test_pack_validator.py`) and are owned by the suite — never point validator
  tests at live content (epic 64's own lesson: prod-rows-in-tests is banned).
