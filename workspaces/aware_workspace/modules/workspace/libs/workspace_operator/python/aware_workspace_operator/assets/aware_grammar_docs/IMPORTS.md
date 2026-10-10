# Aware Imports

Imports are an ergonomics feature for authoring: they provide **alias expansion** before canonical FQN resolution. They do not change dependency loading or package discovery.

## Syntax

```aware
import aware.workflow.analytic as wf
import aware.workflow.* as wf
```

An import may target:

- a dotted module path (`a.b.c`)
- a dotted module wildcard (`a.b.*`)

Imports may include an alias: `as <ident>`.

## Semantics (Canonical)

- Imports only provide alias expansion; they do not "widen" unqualified name lookup.
- Package dependencies are discovered through `aware.toml`; imports do not pull packages into scope.
- Resolution is deterministic:
  - try the identifier as-written in the current schema first
  - then try the import-expanded identifier (if any)

### Prefix Alias Expansion

If an alias maps to a target module path:

- `wf.Analytic` expands to `aware.workflow.analytic.Analytic` when `wf` targets `aware.workflow.analytic`
- `wf.analytic.Analytic` expands to `aware.workflow.analytic.Analytic` when `wf` targets `aware.workflow.*`

Wildcard targets are normalized by removing `.*` during expansion.

## Policy Defaults

The Aware meta language plugin defaults to **no implicit alias binding** for unaliased imports. If you want an import to affect resolution, use `as <alias>`.

Recommended style: prefer **module aliases** (`as wf`) and keep type references explicit (`wf.Analytic`) rather than relying on bare-name symbol aliases.
