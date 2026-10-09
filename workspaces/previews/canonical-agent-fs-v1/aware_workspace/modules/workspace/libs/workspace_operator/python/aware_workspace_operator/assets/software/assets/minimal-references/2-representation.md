# Stage 2 - Representation (Projection Views -> Pane Materialization)

Goal: map declared projection views to pane routes/registrars and verify rendering rails.

Minimal references:

- `docs/aware/grammar/PROJECTION_VIEWS.md`
- `docs/rules/SOFTWARE/2-representation.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Rules:

- `FocusScope.view_id` must resolve to declared projection views.
- Pane registrar binds view routes; host must not invent views.

Done criteria:

- Pane registrar tests pass.
- Projection-view route aligns with `.aware` declaration.
