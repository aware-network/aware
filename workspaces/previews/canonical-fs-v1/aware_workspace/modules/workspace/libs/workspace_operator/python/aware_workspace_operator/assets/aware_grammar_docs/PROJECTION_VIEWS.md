# Projection Views (OPGI + ObjectProjectionGraphView) — Grammar + Compiler Contract

Projection views are becoming a core Aware-OS concept:

- `ObjectProjectionGraphIdentity` (OPGI) identifies a projection family (“what can be shown”).
- `ObjectProjectionGraphView` selects a projection-scoped view/step (“what is shown”).
- `FocusScope.view_id` selects a view deterministically (shared co-navigation).

Reference contracts:
- `apps/interface_flutter/aware_pane_runtime/docs/projection-views.md`
- `docs/architecture/window-focus-scope.md` (“View selection (v0+)”)
- Ontology:
  - `modules/meta/structure/ontology/aware/graph/projection/object_projection_graph_identity.aware`
  - `modules/meta/structure/ontology/aware/graph/projection/object_projection_graph_view.aware`

## Goal

Enable `.aware` to describe available views *descriptively* so the compiler can seed them canonically, and so UI + agent context can converge (AX == UX).

## Grammar (function-like)

Views live inside `projection` blocks:

```aware
projection Identity {
    root identity.Identity

    view onboarding {
        view welcome construct default {
            """
            Welcome flow for first-time identity onboarding.
            Intended for shared navigation via FocusScope.view_id.
            """
        }
    }

    view profile {
        view home instance {
            """
            Identity profile overview.
            """
        }
    }
}
```

Design intent:
- Looks like `fn <name> construct { """doc""" }` (room for evolution inside `{ ... }`).
- Supports hierarchical keys via nested `view <prefix> { ... }`.

Example (Agent mirror hierarchy):

```aware
projection Agent {
    root agent.Agent

    view agent {
        view home instance default { """Agent root context.""" }
    }
    view process {
        view home instance { """Selected process context.""" }
    }
    view thread {
        view home instance { """Selected thread context.""" }
    }
}
```

Produced keys:
- `agent.home`
- `process.home`
- `thread.home`

Ownership boundary note:
- View keys describe navigation contexts for the owning projection only.
- Do not duplicate another projection's SSOT in a new view key.
- Example: Agent projection may expose `agent.home/process.home/thread.home`, while conversation chat remains owned by `aware_conversation:conversation` (`chat`).

## Semantics (canonical)

### View keys (hierarchical)

- `view onboarding { view welcome ... }` produces: `view_key = "onboarding.welcome"`.
- Nested groups concatenate with `.` and never create a separate object (v0).
- Each segment is a `view_path` token (letters/digits/`_`/`-`), enabling keys like:
  - `onboarding.profile.photo-name`

### View kinds

Two kinds (align with Interface contract):
- `construct`: no branch state required (gate-friendly).
- `instance`: requires branch state (materialized OIGB).

### Default view

- Exactly **one default view per projection**.
- `default` maps to `ObjectProjectionGraphView.is_default = true`.

### Description (docstring)

- The first triple-quoted string literal in the view body is the `description`.
- Future: add structured prompt/context composition (see below).

### Projection description (doc comments)

- Leading `///` doc comments on the `projection` declaration become `ObjectProjectionGraph.description`.
- This is distinct from view descriptions (which attach to `ObjectProjectionGraphView.description`).

## Ownership + seeding contract (compiler-owned)

Canonical rule:

- `.aware` is the SSOT for which views exist under a projection identity.
- The compiler must **seed** `ObjectProjectionGraphView` objects into the compiler-owned OPGI lane
  (`object_projection_graph_identity`) so:
  - `FocusScope.view_id` always points at a materialized view object, and
  - the Interface never needs to “invent” views at runtime.

Determinism:
- `ObjectProjectionGraphIdentity.key` is compiler-owned: `{ocg_key}:{projection_name}`.
- `ObjectProjectionGraphView.id` is deterministic for `(opgi_id, view_key)` (stable-id derivation).

Implication:
- Runtime creation via `ObjectProjectionGraphIdentity.create_view(...)` is **legacy / compatibility-only**.
  Once a projection declares views, the host should treat missing views as a compile/seed failure.

Compiler rules (v1):
- `construct` / `instance` map to `ObjectProjectionGraphView.kind`.
- `default` maps to `ObjectProjectionGraphView.is_default`.
- Canonical: at most one explicit default view; when omitted, the compiler defaults the first declared view.
- The first triple-quoted string literal in the view body becomes `ObjectProjectionGraphView.description`.

Implementation refs:
- Code sections: `modules/code/runtime/aware_code/section/projection/builder.py`
- Meta compiler: `modules/meta/runtime/aware_meta/graph/config/projection/compiler.py`

## v0 compatibility (host-created views)

In older environments (or during migration), views may be missing from the OPGI lane.
Historically, the host used `ObjectProjectionGraphIdentity.create_view(...)` to seed them deterministically.

This is problematic long-term:
- Multiple callers can disagree on `kind` for the same `(opgIdentityKey, view_key)`, causing runtime conflicts.
- The Interface becomes an implicit compiler for view registries.

Canonical direction:
- Keep `create_view` only as a temporary fallback while migrating modules to declarative `.aware` views.
- Prefer compiler-seeded views for all production environments.

## Prompt/context composition (follow-on)

To lock AX == UX, view declarations should eventually support *deterministic context assembly* (not ad-hoc prompt strings), e.g.:
- typed references to OPG members / state paths
- stable FQN-bound selectors for attributes, relationships, and projection portals

This should be tracked as a separate design once view seeding is implemented.
