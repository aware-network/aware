# Aware Annotations (`ann`)

Annotations are first-class, semantic directives attached to code sections (classes, relationships, edges, functions, enums, …). They are compiled by meta into canonical OCG annotation views.

## Syntax

```aware
ann <path> <verb> <arg> <arg> ...
```

- `<verb>` is an identifier, normalized to lowercase by the compiler.
- `<arg>` is an identifier or literal (string/number/bool/null).
- `<path>` is a *type reference* plus optional member segments separated by `::`.

### Path Splitting Rule

- Dots (`.`) belong to the type reference (FQN-style).
- `::` separates *member segments* within/under the type reference.

Example:

```aware
ann domain.Domain::schemas::DomainSchema::schema overlay language python entity attribute rename schema_ wire_name schema
```

Here:

- `type_ref = "domain.Domain"`
- `members = ["schemas", "DomainSchema", "schema"]`

## Supported Verbs

### `load`

Defines relationship loading/serialization strategy.

Canonical forms:

- `ann TypeRef::relationship load eager`
- `ann TypeRef::relationship load forward eager reverse lazy`
- `ann TypeRef::relationship::EdgeName load eager` (edge-qualified)

Examples:

```aware
ann repository.Repository::codes::RepositoryCode load eager
ann graph.ObjectProjectionGraph::object_projection_graph_edges load forward eager reverse lazy
```

### Projections

Projection membership + portals are declared via first-class `projection { ... }` blocks.

See `languages/aware/grammar/docs/PROJECTIONS.md`.

### `overlay`

Declares a language-specific overlay (rename/wire_name) for a target entity.

Overlay args are parsed from tokens:

- `language <python|dart|sql|...>`
- `entity <class|attribute|function|enum|enum_option>`
- `rename <new_name>` (optional)
- `wire_name <wire_name>` (optional)

Canonical target forms depend on `entity`:

- `entity class`:
  - `TypeRef`
- `entity attribute`:
  - class attribute: `TypeRef::attribute`
  - function IO attribute: `TypeRef::function::attribute`
  - edge endpoint attribute via relationship path:
    - `TypeRef::relationship_attr::EdgeName::edge_member`
    - `TypeRef::relationship_attr::EdgeName::edge_fn::edge_fn_attr`
- `entity function`:
  - `TypeRef::function`
- `entity enum`:
  - `TypeRef`
- `entity enum_option`:
  - `TypeRef::enum_option`

Example (Python overlay to avoid shadowing `BaseModel.schema`):

```aware
ann domain.Domain::schemas::DomainSchema::schema overlay language python entity attribute rename schema_ wire_name schema
```

### `override`

Overrides relationship-level details that are downstream-materialized (e.g. FK nullability, relationship name).

Canonical forms:

- FK override:
  - `ann TypeRef::relationship override fk nullable`
  - `ann TypeRef::relationship override fk name some_fk_id`
  - `ann TypeRef::relationship override fk nullable name some_fk_id`
- Relationship rename:
  - `ann TypeRef::relationship::EdgeName override relationship name new_name`

Examples:

```aware
ann version.Version::parents override fk nullable
ann domain.Domain::schemas::DomainSchema override relationship name schema
```

#### FK Requiredness Contract

- Default truth:
  - Relationship requiredness comes from `.aware` relationship semantics (`forward_required`).
  - FK requiredness follows that truth on the FK-owning side.
- For `one_to_many`:
  - FK is owned on the reverse/target side.
  - If the relationship is required, reverse FK is required by default.
- `load eager|lazy` controls serialization/loading behavior, not DB/commit FK truth.
- The canonical opt-out is explicit annotation:
  - `ann TypeRef::relationship override fk nullable`
  - optional rename can be combined: `ann TypeRef::relationship override fk nullable name some_fk_id`

Example (required-by-default, explicit nullable override):

```aware
class CodeSectionAttribute {
    code_section_comments comment.CodeSectionComment[]
}

ann attribute.CodeSectionAttribute::code_section_comments load eager
ann attribute.CodeSectionAttribute::code_section_comments override fk nullable
```

## Notes

- Annotations are validated and compiled in `libs/meta/aware_meta/graph/config/annotation/compiler.py`.
- The tree-sitter grammar currently parses only one `::` segment structurally; deeper member paths are handled via parser recovery and the code-section text segments. This primarily affects syntax highlighting; compilation remains canonical.
