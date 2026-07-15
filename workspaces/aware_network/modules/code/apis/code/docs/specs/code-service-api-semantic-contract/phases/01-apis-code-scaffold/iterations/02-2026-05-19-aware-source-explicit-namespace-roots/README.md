# Iteration 02 - Aware Source Explicit Namespace Roots

- Issue: `fb/2026-05-19/aware-source-explicit-namespace-roots-v0`
- Status: complete
- Owner: `codex-019e3efc-1c8c-7361-bbbe-6374ded0fb8a`
- Commit: `a5f4a9c3084ed88861ff00326a205b041fa30545`

## Goal

Add a package-manifest namespace contract so nested `.aware` source folders can
be organizational without changing public domain/schema FQNs.

## Contract

Default behavior remains `layout_derived`: folder depth still derives
domain/schema identity for packages that intentionally use layout semantics.

Packages that need modular feature folders can opt into explicit roots:

```toml
[build.namespace]
mode = "explicit_roots"

[[build.namespace.roots]]
path = "code/**/*.aware"
domain = "default"
schema = "code"
```

With that contract, `code/features/semantic_contract.aware` can still materialize
public `code.*` DTO references instead of drifting to `code.features.*`.

## Acceptance

- `aware.toml` loader parses and validates `build.namespace`.
- Invalid namespace roots fail closed at the manifest boundary.
- Meta semantic analysis consumes explicit roots when building OCG namespaces.
- Unmatched source files and conflicting overlapping roots fail closed.
- Existing layout-derived packages keep current behavior.
