# Aware Object Config Graph Transformers

This directory contains bidirectional transformers that enable **Aware grammar to be the single source of truth** for your entire application stack.

## Overview

The transformers allow you to:

1. **Write once in Aware grammar** - Define your data models, relationships, and business logic
2. **Generate everywhere** - Automatically create SQL schemas, Python models, Dart models, etc.
3. **Maintain consistency** - Round-trip transformations ensure no data loss or inconsistencies

## AwareToSQLTransformer

The `AwareToSQLTransformer` converts Aware ObjectConfigGraphs into SQL ObjectConfigGraphs, enabling database schema generation from Aware grammar.

### Key Features

- **Relationship Classification**: Automatically determines whether to generate FK columns or join tables
- **Naming Consistency**: Uses the same naming rules as the reverse SQL→Aware transformer
- **Round-trip Compatible**: Ensures Aware→SQL→Aware transformations are lossless
- **Cardinality Handling**: Properly handles 1:1, 1:N, N:1, and M:N relationships
- **Edge Object Support**: Converts Aware edge objects to addressable join tables

### Transformation Rules

| Aware Relationship | SQL Generation | Detection |
|-------------------|----------------|-----------|
| M:N with edge object | Addressable join table (edge becomes table) | `object_config_relationship_association` exists |
| M:N without edge | Pure join table (no payload) | `MANY_TO_MANY` + no association |
| 1:N, N:1 | Foreign key column on N-side | `ONE_TO_MANY` / `MANY_TO_ONE` |
| 1:1 | FK column + UNIQUE constraint | `ONE_TO_ONE` |

### Naming Rules

The transformer uses deterministic naming that mirrors the SQL→Aware logic:

```python
# Forward side (user-specified)
author_id           # from "author Author" field
parent_thread_id    # from "parent_thread Thread" field

# Reverse side (synthetic)
book_id             # from table name "book"
user_role_id        # from table name + fk stub when multiple FKs

# Join tables
user_role           # alphabetically sorted: "role_user" → "user_role"
```

### Usage Example

```python
from aware_languages.transformers import AwareToSQLTransformer

# Initialize transformer with SQL graph builder
transformer = AwareToSQLTransformer(sql_graph_builder)

# Transform Aware graph to SQL
sql_graph = transformer.transform(
    aware_graph, 
    code_primitive_type=YourCodePrimitiveType
)

# Use SQL graph to generate database schema
schema_generator = SQLSchemaGenerator()
ddl_statements = schema_generator.generate(sql_graph)
```

### Round-trip Testing

To ensure consistency, always test round-trips:

```python
# Aware → SQL → Aware
original_aware = parse_aware_files(...)
sql_graph = aware_to_sql.transform(original_aware)
roundtrip_aware = sql_to_aware.transform(sql_graph)

# Should be identical
assert compare_graphs(original_aware, roundtrip_aware) == []
```

## Architecture Benefits

### Before: SQL as Source of Truth
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│   SQL   │───▶│ Python  │    │  Dart   │
│ Schema  │    │ Models  │    │ Models  │
└─────────┘    └─────────┘    └─────────┘
```
- Manual SQL schema design
- Separate model generation for each language
- Inconsistencies between languages
- Difficult to maintain relationships

### After: Aware as Source of Truth
```
               ┌─────────┐
               │  Aware  │
               │ Grammar │
               └────┬────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │   SQL   │ │ Python  │ │  Dart   │
   │ Schema  │ │ Models  │ │ Models  │
   └─────────┘ └─────────┘ └─────────┘
```
- Single source of truth in Aware
- Automatic generation for all targets
- Guaranteed consistency across languages
- Easy relationship management

## Future Transformers

This architecture enables additional transformers:

- `AwareToPythonTransformer` - Generate SQLAlchemy models
- `AwareToDartTransformer` - Generate Dart data classes  
- `AwareToTypeScriptTransformer` - Generate TypeScript interfaces
- `AwareToRustTransformer` - Generate Rust structs

## Implementation Notes

### Relationship Direction

The transformer uses the same relationship direction logic as the Aware parser:

1. **Backref annotations** take precedence (explicit child side)
2. **Eager loading** side becomes the source
3. **Scalar side** (non-list) preferred as source
4. **Lexicographic** tie-breaker for deterministic results

### Loading Strategy Preservation

Original Aware loading strategies are preserved in the SQL graph:

- `@lazy` annotations → `LAZY` loading strategy
- Default behavior → `EAGER` loading strategy
- Context-specific strategies (INTERFACE, NETWORK) maintained

### Audit Columns

Standard audit columns are automatically added to all SQL tables:

- `id` (primary key)
- `created_at` (NOT NULL)
- `updated_at` (NOT NULL) 
- `version` (NOT NULL)
- `deleted_at` (nullable)

This ensures SQL tables have proper tracking and versioning capabilities. 