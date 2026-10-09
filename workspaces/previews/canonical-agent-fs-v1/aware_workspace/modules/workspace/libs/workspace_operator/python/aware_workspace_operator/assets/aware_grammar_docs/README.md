# Aware Grammar

Aware is a domain language for describing canonical object graphs. Aware source (`.aware`) is treated as a **single source of truth** for:

- building Object Config Graphs (OCG) from code sections
- cross-language materializations (Python, Dart, SQL, …)
- editor tooling (VS Code/Cursor via LSP)

Canonical examples live in `environments/kernel-graph/ontology/aware/`.

## Docs

- `languages/aware/grammar/docs/SYNTAX.md` — syntax reference (classes, edges, enums, functions, literals)
- `languages/aware/grammar/docs/PROGRAMS.md` — deterministic invocation plans (`program { let/call }`) and `InvocationPlan` IR
- `languages/aware/grammar/docs/ANNOTATIONS.md` — `ann` verbs (`load`, `overlay`, `override`)
- `languages/aware/grammar/docs/BRANCHABILITY.md` — projection-scoped branch policy (OPGI)
- `languages/aware/grammar/docs/PROJECTIONS.md` — first-class `projection { ... }` declarations (OPG)
- `languages/aware/grammar/docs/PROJECTION_VIEWS.md` — projection-scoped view descriptors
- `languages/aware/grammar/docs/IMPORTS.md` — import/alias semantics (resolver-friendly, deterministic)
- `languages/aware/grammar/docs/TRANSPILATION.md` — language mapping rules (Python/Dart/SQL)
- `languages/aware/grammar/docs/PATTERNS.md` — modeling patterns and conventions
- `languages/aware/grammar/docs/VALIDATION.md` — tests and parser regeneration
- `languages/aware/grammar/docs/HIGHLIGHTING.md` — syntax highlighting goals and scope map

## Quick Example (Kernel Ontology Style)

```aware
class Repository {
    bucket storage.StorageBucket
    contents content.Content[] @RepositoryContent many
    codes code.Code[] @RepositoryCode

    name String
    workspace_root String
}

ann repository.Repository::codes::RepositoryCode load eager
```

## Key Invariants

- **Deterministic resolution:** unqualified `Name` resolves only in the current schema; cross-schema references must be explicit (`schema.Name`, `domain.schema.Name`, or fully-qualified `package.domain.schema.Name`).
- **Relationships are owner-first:** a relationship is encoded only on the owning side; reverse accessors are materialized downstream (often via overlays).
- **Edges carry payload:** use `@EdgeSpec` on relationships to attach association payload without adding back-references into the edge schema.
- **Annotations are semantic:** `ann` sections compile into load/overlay/override views. Projections are authored via `projection { ... }` and lowered to compiler-owned `ObjectProjectionGraphDeclaration` / `ObjectProjectionGraphBinding` on the OCG for deterministic OPG building + hashing.
