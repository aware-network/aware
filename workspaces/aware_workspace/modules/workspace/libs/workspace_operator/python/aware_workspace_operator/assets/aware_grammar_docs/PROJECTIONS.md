# Projections (ObjectProjectionGraph)

This document describes the canonical AWARE grammar + compiler representation for projections.

## Legacy representation (deprecated)

Historically, projections could be expressed via scattered `project` annotations. Canonical now is `projection { ... }` blocks.

### Canonical semantics (runtime SSOT)
- The compiler lowers `projection { ... }` blocks into compiler-owned OCG SSOT:
  - `ObjectProjectionGraphDeclaration` (one per projection)
  - `ObjectProjectionGraphBinding` (root + member + portal bindings)
  This keeps OPG hashing + building stable without lowering into annotations.
- Portal edges are expressed by a trailing target projection on a relationship member (see below).
- OPG validation requires **exactly one root node** per projection.

See:
- `modules/meta/runtime/aware_meta/graph/projection/builder.py` (membership edges)
- `modules/meta/runtime/aware_meta/graph/config/handlers.py` (portal provisioning)
- `modules/meta/runtime/aware_meta/graph/instance/validator_opg.py` (single-root invariant)
- `modules/meta/runtime/aware_meta/graph/config/projection/compiler.py` (projection compilation)

## Grammar: `projection` as a first-class declaration (implemented)

Use a top-level declaration that reads like a single “projection object”:

```aware
projection ActorFocus {
    root actor.ActorFocus
    actor.ActorFocus::suggestions
    actor.ActorFocus::focus Focus
}

projection Focus {
    root focus.Focus
}
```

### Semantics (v0)
- `root <TypeRef>`: defines the single root class for the projection.
- `<TypeRef>::<relationship>`: membership edge in the same projection.
- `<TypeRef>::<relationship> <ProjectionName>`: portal edge to another projection.

## Projection entry reads (retired)

The old projection-entry read rail is retired:

- no authored ontology `fn ... read` functions,
- no `ObjectProjectionGraphRead` metadata,
- no runtime `opg_read` invocation target,
- no API/Service endpoint projection-read-target grants.

Reads are now commit-driven and service-owned. Services consume lane commits,
commit replay, or materialized DB/read-model state, then expose service/view
DTOs. Environment committed DTO verification is the trust layer when a caller
needs proven Ontology DTO evidence.

See: `docs/architecture/projection-read-contract.md`.

## Projection description (doc comments)

The compiler derives `ObjectProjectionGraph.description` from leading doc comments on the projection declaration:

```aware
/// Wallet projection.
/// Holds balances and transactions.
projection Wallet {
    root wallet.Wallet
}
```

Contract:
- The first doc comment bound to the `projection` section becomes the projection description.
- This is intended for UX selection (projection pickers, FocusScope affordances) and future agent prompts.

## Qualified portal targets (cross-package / cross-OCG)

Portals may target projections that live in dependency graphs (external OCGs).

Today, portal resolution is name-based (unqualified targets like `Identity`). As the system grows, projection
names may collide across packages. To keep portal provisioning deterministic, the grammar should
support *qualified* projection references.

Recommended shape:

```aware
projection Wallet {
    root wallet.Wallet
    wallet.Wallet::owner aware_identity.Identity
}
```

Resolution rule (recommended):
- `aware_identity.Identity` binds the **target projection owner** (`fqn_prefix="aware_identity"`) plus the **target projection id** (`Identity`).
- The compiler preserves the qualifier (so meta can resolve deterministically).

Unqualified portal targets use the same authored identity (`Identity`), while qualified references avoid
cross-package ambiguity.

## Projection identities + views (implemented)

The Interface OS treats views as fundamental:
- `ObjectProjectionGraphIdentity` (OPGI) = “what can be shown” (projection family)
- `ObjectProjectionGraphView` = “what is shown” (view/step within the family)

The long-term goal is for `.aware` to define available views (label/description/default) so the compiler can seed them,
and the Interface does not need to “invent” views at runtime.

Recommended shape (function-like, with room for future state/prompt refs):

```aware
projection Identity {
    root identity.Identity

    view onboarding {
        view welcome construct default {
            """
            Welcome onboarding gate (no branch state required).
            """
        }
    }

    view profile {
        view home instance {
            """
            Profile home (requires branch state / materialized OIGB).
            """
        }
    }
}
```

Tracking design: `docs/projects/aware-orm-production-ready/tasks/aware-grammar-projection-declaration/design/2026-02-01T22-27-36Z-projection-views-canonicalization.md`.
Compiler status:
- `projection` declarations compile into `ObjectProjectionGraphDeclaration` / `ObjectProjectionGraphBinding`.
  - Stored on `ObjectConfigGraph.object_projection_graph_declarations`.
  - Included in `ObjectConfigGraph.hash` (semantic).
- Projection views compile into `ObjectProjectionGraphIdentity.object_projection_graph_views` (OPGI seeding).
  - The first triple-quoted string in the view body becomes `ObjectProjectionGraphView.description`.
- Projection identity is authored-name preserving. `projection FocusScope { ... }` materializes as
  `ObjectProjectionGraphDeclaration.projection_name = "FocusScope"` unless the declaration explicitly
  supplies `name "..."`.

Implementation refs:
- Code sections: `modules/code/runtime/aware_code/section/projection/builder.py`
- Meta compiler: `modules/meta/runtime/aware_meta/graph/config/projection/compiler.py`

## Roadmap

- Migrate legacy projection annotations to `projection { ... }` per module.
- Add projection entry-read declarations and compiler lowering for root-entry read routing.
- Extend view bodies with structured prompt/context composition (state + FQN-bound references).
- Add optional view labels/positions when UX needs it (keep docstring as `description`).

## Tracking
- Design notes and migration examples are tracked at:
  - `docs/projects/object-config-graph/tasks/aware-grammar/design/2026-02-03T00-00-00Z-projection-declaration-ssot.md`
  - `docs/projects/aware-orm-production-ready/tasks/aware-grammar-projection-declaration/design/2026-01-24T14-01-35Z-first-class-projection-declaration.md`
  - `docs/projects/aware-orm-production-ready/tasks/aware-grammar-projection-declaration/design/2026-02-01T22-27-36Z-projection-views-canonicalization.md`
