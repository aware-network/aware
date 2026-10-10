# Stage 0 - Configuration (Ontology, Projection, Functions)

Goal: define SSOT in `.aware` so compiler can deterministically produce runtime/representation artifacts.

Minimal references:

- `docs/aware/grammar/README.md`
- `docs/aware/grammar/SYNTAX.md`
- `docs/aware/grammar/IMPORTS.md`
- `docs/aware/grammar/PROJECTIONS.md`
- `docs/aware/grammar/PROJECTION_VIEWS.md`
- `docs/aware/grammar/PROGRAMS.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Minimal commands:

```bash
aware-cli module create <module_id> --repo-root <repo_root>
aware-cli compile --update-lock --materialization-mode runtime module <module_id>
```

Done criteria:

- `.aware` compiles without errors.
- Projection view keys are declared in `.aware` (not invented at runtime).
- Function signatures align with intended runtime mutation boundary.
