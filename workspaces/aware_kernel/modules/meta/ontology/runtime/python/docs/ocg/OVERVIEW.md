---
title: "Object Config Graph (OCG) — Kernel Meta Overview"
code_path:
  - ../../aware_meta/graph/config/builder.py
  - ../../aware_meta/graph/config/hash.py
  - ../../aware_meta/graph/config/namespace_index.py
  - ../../aware_meta/graph/config/annotation/compiler.py
test_path:
  - ../../tests/test_ocg_annotations_hash.py
  - ../../tests/test_ocg_annotations_compilation.py
  - ../../tests/test_cross_ocg_inheritance_augment.py
last_validated: "2025-12-21 12:26:37"
---

## Purpose
`aware_meta` owns the **canonical, language-agnostic** meta build of the Object Config Graph (OCG) from SSOT `CodeSections`.

This is the “honesty wall” version of OCG:
- **SSOT nodes** are **`ClassConfig`** (+ enums, functions, primitives) and **`ClassConfigRelationship`**
- Relationships are explicit and self-descriptive:
  - **`ClassConfigRelationship`** stores topology + loading semantics (forward/reverse)
  - **`ClassConfigRelationshipAttribute`** stores the attribute-level representation of a relationship (direction + role)
- **Attributes are relationship-agnostic**: `AttributeConfig` models type/shape only (via `AttributeTypeDescriptor`).

## What kernel-meta is responsible for
- **Build**: `build_object_config_graph_from_code(...)` produces an `ObjectConfigGraph` whose nodes are class-first.
- **Relationship extraction**:
  - Each relationship attribute must resolve to **exactly one** target class (strict policy).
  - Association/edge container classes are modeled via `ClassConfigRelationshipAssociation`.
  - Canonical constraint (builder-level): canonical emits **one** relationship attribute representation: `FORWARD + REFERENCE`.
- **Cross-OCG resolution**:
  - External graphs extend the FQN resolver deterministically by full FQN only.
  - Cross-OCG relationships are returned detached in `cross_relationships_by_target_ocg`.
  - Cross-OCG inheritance/augmentation is returned detached in `cross_class_configs_by_target_ocg`.
- **Annotations**: compile `ann` sections into `ObjectConfigGraphAnnotation*` and include semantics in graph hash.
- **Hashing**:
  - `compute_object_config_graph_hash(...)` is deterministic and changes when semantics change.
  - `ObjectConfigGraph.layout_hash` additionally includes layout metadata (paths + ordering) to
    invalidate materialization caches on file moves without semantic changes.
  - Materialization/transform caches also include a deterministic overlay signature (explicit overlays +
    reserved keyword policies) so overlay policy changes invalidate caches.

## What kernel-meta is NOT responsible for
- **Parsing language syntax** into `CodeSections` (grammar responsibility).
- **Language-specific inference/heuristics** for relationships or identity (canonical OCG avoids guessing).

## Validation scope
Kernel-meta tests should validate **meta invariants** (topology, determinism, cross-OCG behavior, annotation semantics),
not grammar parsing details.

For canonical `.aware` fixtures, kernel-meta tests may use `.aware` text only as an input mechanism to produce `CodeSections`,
but assertions should stay at the meta level.
