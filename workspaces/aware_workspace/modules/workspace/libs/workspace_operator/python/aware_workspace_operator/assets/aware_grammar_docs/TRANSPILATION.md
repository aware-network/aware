# AWARE Language Transpilation Rules

## Overview

This document defines the rules for converting AWARE language constructs to and from Python, Dart, and SQL. AWARE serves as the canonical source for entity definitions, with other languages generated from AWARE specifications.

## Type Conversion Rules

### Primitive Type Mappings

| AWARE Type | Python Type | Dart Type | SQL Type | Notes |
|------------|-------------|-----------|----------|-------|
| String     | str         | String    | TEXT     | Text data |
| Int        | int         | int       | INTEGER  | Whole numbers |
| Bool       | bool        | bool      | BOOLEAN  | True/false values |
| UUID       | UUID        | UuidValue | UUID     | Universally unique identifiers |
| DateTime   | datetime    | DateTime  | TIMESTAMP| Date and time values |
| Float      | float       | double    | REAL     | Floating-point numbers |
| Bytes      | bytes       | Uint8List | BYTEA    | Binary data |
| Json       | dict        | Map<String, dynamic> | JSONB | JSON objects |

### Complex Type Mappings

#### Arrays/Lists
```aware
// AWARE
posts Post[]

// Python
posts: List[Post]

// Dart
List<Post> posts

// SQL
-- Handled through relationship tables
```

#### Optional Types
```aware
// AWARE
bio String?

// Python
bio: Optional[str]

// Dart
String? bio

// SQL
bio TEXT NULL
```

#### References/Relationships
```aware
// AWARE
author User

// Python
author_id: UUID = Field(foreign_key="users.id")
author: User = Relationship()

// Dart
String authorId
User? author

// SQL
author_id UUID REFERENCES users(id)
```

## Syntax Conversion Rules

### Entity Definitions
> **Auto-managed fields**: The platform automatically materialises `id`, `created_at`, and `updated_at` columns for every type. Do not declare `primary` attributes or explicit `= "now()"` defaults in AWARE definitions—downstream languages infer these from the canonical schema.

#### AWARE → Python (SQLAlchemy)
```aware
// AWARE
class WorkspaceProject {
    name String
    owner WorkspaceIdentity?
}
```

```python
# Python
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from aware_orm.models.orm_model import ORMModel
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class WorkspaceProject(ORMModel):
    __tablename__ = "workspace_project"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    name: str = Column(String, nullable=False)
    owner_id: UUID | None = Column(UUID(as_uuid=True), ForeignKey("workspace_identity.id"), nullable=True)
    owner = relationship("WorkspaceIdentity")
    created_at: datetime = Column(DateTime, default=func.now())
```

#### AWARE → Dart (Freezed)
```aware
// AWARE
class WorkspaceIdentity {
    public_key String
}
```

```dart
@freezed
class WorkspaceIdentity with _$WorkspaceIdentity {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory WorkspaceIdentity.def({
    @UuidValueConverter() required UuidValue id,
    required String publicKey,
  }) = _WorkspaceIdentity;

  factory WorkspaceIdentity.fromJson(Map<String, dynamic> json) => _$WorkspaceIdentityFromJson(json);
}
```

#### AWARE → SQL (PostgreSQL)
```aware
// AWARE
class WorkspaceTask {
    title String
    project WorkspaceProject
}
```

```sql
CREATE TABLE workspace_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    project_id UUID REFERENCES workspace_project(id)
);
```

These examples illustrate the directional semantics: the owning side encodes the relationship (`project WorkspaceProject`) and downstream targets materialise the foreign key.

### Augment (Inheritance / Extension)
The `augment` verb declares a base relationship (inheritance-style) between two classes:
```aware
class TerminalEnv augment Terminal {
    provider String?

    fn create(thread Thread, cwd String?) -> Terminal {
        """
        Creates a terminal via the environment extension.
        """
    }
}
```
- Augment blocks may declare **attributes and functions**; downstream materializers interpret the base relationship according to the target language/runtime (subclassing, mixins, overlays, …).
- Meta models the relationship by setting `ClassConfig.parent_class_id` on the child class config. This preserves canonical identity while allowing deterministic extension.

### Function verbs and constructors
- Function declarations support an optional verb token (e.g., `fn build construct(...)`). Tree-sitter parses it as an optional identifier after the function name; adapters expose it via `CodeSectionFunctionAdapter.get_verb`, and the meta builders store it on `FunctionConfig.verb`.
- The canonical graph treats verbs as metadata only; no additional attributes/relationships are generated. Downstream languages should read the verb from the FunctionConfig rather than re-parsing source files.
- The `construct` verb has reserved meaning: when detected, the builder records the verb and sets `ClassConfigFunctionConfig.is_constructor` on the link connecting the function to its class. Renderers use that link metadata (not the function itself) to switch semantics (e.g., Python emits `@classmethod` + `cls` while other languages can mark special constructors).
- The `read` verb marks read-only functions; canonical validation allows only `construct` and `read` so runtime policies can be enforced deterministically.
- Additional verbs should follow the same pipeline—grammar → adapter → builder → graph—so every downstream consumer sees a consistent view of the verb plus any derived flags.

### Tuple return clauses
- The `->` clause accepts either a single return type or a named tuple literal:
  ```aware
  fn list() -> (count Int, terminals Terminal[]) { }
  ```
- Tree-sitter surfaces the return clause, adapters emit output attributes, and the meta builders create one OUTPUT attribute config per element (preserving name + position) so materializers can render structured payloads deterministically.
- Transpilers render tuple returns using each language’s idioms:
  - **Aware** emits `(name Type, ...)` syntax.
  - **Python** typically emits a `TypedDict`/`dict`-like payload or a `tuple[...]` depending on the target API contract.
  - **Dart** typically emits a dedicated return model (or record/tuple where supported).
