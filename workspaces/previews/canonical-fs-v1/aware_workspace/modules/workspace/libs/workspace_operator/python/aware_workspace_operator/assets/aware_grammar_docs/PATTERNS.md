# Aware Patterns

This document captures conventions used in the kernel ontology and recommended for new Aware packages.

## Relationships

- Model relationships on the **owning side only**. Avoid back-references; they are derived downstream.
- Use `many`/`unique` on relationship fields for multiplicity and uniqueness constraints.
- Use `@EdgeSpec` when you need association payload or distinct relationship identity.

Example:

```aware
class Repository {
    contents content.Content[] @RepositoryContent many
}

edge RepositoryContent {
    // payload fields live here
}
```

## Annotations

- Use `ann ... load ...` to define canonical load/serialization strategy.
- Use `ann ... overlay ...` for language-specific naming and wire compatibility.
- Prefer overlays over hand-editing materialized outputs.

## Functions

- Use function verbs to express intent, especially `construct` for constructor-like builders:
  ```aware
  fn build construct(relative_path String, repository_id UUID) -> RepositoryPath { }
  ```
- Prefer tuple returns with named outputs when returning multiple values:
  ```aware
  fn list() -> (count Int, terminals Terminal[]) { }
  ```
- Use `-> { }` for "void" functions when there are no outputs.

## Augment

- Use `augment` when you need an inheritance/extension relationship:
  ```aware
  class TerminalEnv augment Terminal {
      provider String?
      fn create(host TerminalHost) -> Terminal { }
  }
  ```
- Canonical expectation: the augment target resolves within the current dependency universe (no "magic globals").

## Naming

- Keep schema and class names stable; use overlays (`wire_name`) to preserve external compatibility.
- Keep output tuple names stable; downstream clients use them as structured keys.
