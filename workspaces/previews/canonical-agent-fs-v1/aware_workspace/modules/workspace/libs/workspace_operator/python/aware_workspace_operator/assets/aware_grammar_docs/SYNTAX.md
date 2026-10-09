# Aware Syntax Reference

This document describes the canonical syntax supported by the Aware tree-sitter grammar and consumed by the code → OCG pipeline.

## File Structure

An `.aware` file is a sequence of:

1. zero or more `import` statements (optional)
2. any number of top-level declarations:
   - `program` (deterministic invocation plans; v0 body is opaque)
   - `projection` (OPG membership + view metadata)
   - `class` (including `augment`)
   - `edge`
   - `enum`
   - top-level `fn`
   - `ann`

Comments (`//` and `///`) may appear anywhere.

## Identifiers

- Identifiers match `[_A-Za-z][_A-Za-z0-9]*`.
- Dotted qualification (`schema.Name`, `domain.schema.Name`, `package.domain.schema.Name`) is treated as a single syntactic unit; the resolver interprets meaning by part-count and context.

## Classes

```aware
class Name {
    field Type
    fn doThing() -> Bool { }
}
```

- Modifiers come after the name as a colon-prefixed list. Canonical v0 supports:
  - `: inline_value` (inline payloads, not graph refs)
  - Branchability is **not** a type modifier; it is projection-scoped (see `languages/aware/grammar/docs/BRANCHABILITY.md`).
- Class bodies contain:
  - attributes (field declarations)
  - function declarations
  - comments

### Augment (Inheritance / Extension)

```aware
class TerminalEnv augment Terminal {
    // Extension attributes are allowed
    provider String?

    fn create(host TerminalHost) -> Terminal { }
    async fn attach(host TerminalHost) -> Terminal { }
}
```

Canonical rule: `augment` introduces a base relationship (similar to inheritance). The augment target must resolve within the current dependency universe so downstream materializers can treat `TerminalEnv` as a subclass/extension of `Terminal`.

## Attributes (Fields)

```aware
name String
bucket storage.StorageBucket
contents content.Content[] @RepositoryContent many
container_name String? unique
shell String = "/bin/bash"
```

Attribute syntax:

```
<name> <type_ref> [unique|many] [= <default>]
```

### Type References

A `type_ref` has:

- a base type (a qualified name like `String` or `schema.ClassName`)
- optional list marker `[]`
- optional nullable marker `?`
- optional edge spec `@EdgeSpec` for association payload

Examples:

- `Post[]`
- `storage.StorageBlob? @ContentPartFile`
- `Vector(768)?`
- `Dict[String, Float]`

### Mapping Types

Mapping types use `Dict[KeyType, ValueType]` and can be nested or wrapped:

- `Dict[String, Int]`
- `Dict[String, Vector(1536)]`
- `Dict[String, Int]?`
- `Dict[String, Int][]`

### Parametric Types

Parametric types look like `Vector(1408)` where the parameters are numbers or identifiers.

## Edges

Edges represent association payload schemas.

```aware
edge DomainSchema {
    layout_rect_w Float?

    fn build construct(domain_id UUID, schema schema.Schema) -> DomainSchema { }
}
```

Edges support the same modifier list as classes (`: inline_value`) and may contain attributes and functions.

## Enums

```aware
enum ChangeType {
    CREATED
    UPDATED
    DELETED
}
```

Enum options may optionally specify explicit values:

```aware
enum Foo {
    A = "a"
    B = 2
}
```

## Functions

Functions can be declared:

- inside a `class` or `edge`
- at the top-level of a file

### Signature

```aware
fn get_display_name(p_human_id UUID) -> String { }
async fn attach(host TerminalHost) -> Terminal { }
```

- Functions may be prefixed with `async`.
- Functions may include an optional *verb* token after the name (e.g. `construct`).

### Tuple Returns

Tuple returns use named outputs:

```aware
fn list() -> (thread_id UUID, count Int, terminals Terminal[]) { }
```

### Void Returns

Kernel ontology commonly uses an empty return clause to mean "no outputs":

```aware
fn update_sources(p_event_config_id UUID, p_valid_sources String[]) -> { }
```

Downstream builders treat this as a void/empty output signature.

## Literals

Default values and `ann` arguments accept literals:

- strings: `"text"` or `'text'`
- numbers: `123`, `3.14`
- booleans: `true`, `false`
- null: `null`
- multi-line blocks:
  - `""" ... """`
  - `$$ ... $$`

## Imports

Import statements are supported, but the kernel ontology mostly uses explicit qualified names instead.

See `languages/aware/grammar/docs/IMPORTS.md`.

## Annotations

Annotations use the `ann` keyword:

```aware
ann repository.Repository::codes::RepositoryCode load eager
```

See `languages/aware/grammar/docs/ANNOTATIONS.md` for verb-specific semantics and path forms.

## Programs (v0)

`program` is a first-class top-level declaration intended to model deterministic instance evolution
as commit-backed `FunctionCall` steps.

Canonical v0 syntax:

```aware
program KernelSeed {
    let public_key = "ed25519:..."
    call identity.Identity.signup(public_key=public_key, type=human)
}
```

v0 notes:
- Statements: `let` + `call` only (no control flow).
- Expressions: refs, calls, scalar literals, strict JSON objects/arrays.
- The canonical compiler API is `aware_experience.program.language.compile_invocation_plans(...)` which produces an `InvocationPlan` IR. The tree-sitter grammar owns syntax recognition only.

See `languages/aware/grammar/docs/PROGRAMS.md` for semantics, validation rules, and a real seed example.
