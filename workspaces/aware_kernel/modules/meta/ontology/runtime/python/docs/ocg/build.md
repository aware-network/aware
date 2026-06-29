---
title: "OCG Build (Kernel Meta)"
code_path:
  - ../../aware_meta/graph/config/builder.py
  - ../../aware_meta/graph/config/hash.py
test_path:
  - ../../tests/test_ocg_annotations_hash.py
  - ../../tests/test_ocg_annotations_compilation.py
  - ../../tests/test_cross_ocg_inheritance_augment.py
last_validated: "2025-12-21 12:26:37"
---

## Scope
This document describes the **kernel-meta** OCG build path:
`aware_meta.graph.config.builder.build_object_config_graph_from_code`.

It is **class-first** and **language-agnostic**: it consumes already-parsed SSOT `CodeSections` (from `aware_code`)
and emits a canonical `ObjectConfigGraph` topology without heuristics.

## Inputs
- **`file_codes`**: list of `(path, Code)` where each `Code` already contains `CodeSections` (classes, enums, functions, annotations).
- **`namespace_by_code_id`**: deterministic namespace mapping (`code_id -> NamespacePath(package, namespace)`).
- **`external_graphs`** (optional): additional graphs used for deterministic cross-OCG resolution by full FQN.

## Outputs
`ObjectConfigGraphBuildResult`:
- **`graph`**: the built `ObjectConfigGraph` (class-first nodes).
- **`cross_relationships_by_target_ocg`**: detached relationships targeting external graphs.
- **`cross_class_configs_by_target_ocg`**: detached child class configs targeting external parent graphs.

## Canonical invariants enforced by the builder
- **Class-first identity**: OCG nodes include `ClassConfig` and `ClassConfigRelationship` as SSOT.
- **Strict relationship resolution**: any relationship attribute must resolve to **exactly one** target class.
- **Relationship representation is explicit**:
  - `ClassConfigRelationship` stores endpoints + relationship type + forward/reverse loading semantics
  - `ClassConfigRelationshipAttribute` stores the attribute-level representation (`direction`, `role`, `attribute_config_id`)
  - Canonical emission: **one** `FORWARD + REFERENCE` relationship attribute per relationship.
- **Association edge containers** are modeled via `ClassConfigRelationshipAssociation`; association/edge classes do **not**
  emit relationships from their own attributes in canonical mode.
- **Deterministic cross-OCG resolution**:
  - external symbol universe is keyed by **full FQN only**
  - cross relationships and cross inheritance are returned detached (not embedded in `graph`)

## Hashing
`aware_meta.graph.config.hash.compute_object_config_graph_hash` is deterministic:
- avoids UUIDs, hashes stable signatures (FQNs, ordering, relationship attribute signatures)
- includes compiled annotation semantics, so semantic annotation changes change the OCG hash
- includes function signatures (inputs/outputs + ordering), so API-shape changes invalidate caches/materializations

`ObjectConfigGraph.layout_hash` extends the semantic hash with layout metadata (paths + ordering) to
invalidate materialization caches when files move without semantic changes.

Materialization/transform caches also include a deterministic overlay signature (explicit overlays +
reserved keyword policies). Overlay changes must invalidate caches even when layout_hash is unchanged.
