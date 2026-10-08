# Branchability (Projection-Scoped)

Canonical rule:

- **Branchability is a property of a Projection identity (OPGI)**, not a `class`/`edge`/`enum`.
- If a projection is **branchable**, multiple branches may legitimately coexist for the same projection identity.
- If a projection is **not** branchable (default), it is treated as **single-branch / canonical** (1:1 with the ObjectProjectionGraphIdentity).

## Canonical representation: `projection ... is_branchable { ... }`

Branchability is expressed on the `projection` declaration itself:

```aware
projection Repository name "repository" is_branchable {
    root repository.Repository

    // Membership edges (same projection)
    repository.Repository::contents

    // Portal edges (cross-projection)
    repository.Repository::owner identity
}
```

Notes:

- `is_branchable` is a **flag**. If omitted, `ObjectProjectionGraphIdentity.is_branchable` remains `false`.
- `Identity` in the portal example may be either:
  - a projection id (unqualified authored token), or
  - a qualified projection symbol (recommended for cross-package disambiguation): `aware_identity.Identity`.
- See `docs/architecture/opg-portals.md` for runtime behavior and portal semantics.

## Legacy representation (deprecated)

Branchability is no longer documented via legacy annotation syntax. Use `projection ... is_branchable { ... }`.

## Removed: type-level `: branchable` / `: nonbranchable`

`branchable` and `nonbranchable` were removed from the type modifier list.

- They are no longer valid in Aware syntax (tree-sitter + canonical grammar).
- The only canonical type modifier today is `: inline_value`.

## Migration checklist

- Remove `: branchable` from all type declarations.
- If you need branching behavior, mark the **projection root** with `is_branchable`.
- Do not encode branching policy at class level.
