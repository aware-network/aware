---
title: "OCG Validation (Kernel Meta)"
code_path:
  - ../../aware_meta/graph/config/builder.py
  - ../../aware_meta/graph/config/hash.py
  - ../../aware_meta/graph/config/annotation/compiler.py
test_path:
  - ../../tests/test_ocg_builder_smoke.py
  - ../../tests/test_ocg_annotations_hash.py
  - ../../tests/test_ocg_annotations_compilation.py
  - ../../tests/test_cross_ocg_inheritance_augment.py
last_validated: "2025-12-21 13:52:42"
---

## Goal
This module is canonicalized in `aware_meta`. We do **not** validate the deprecated `aware_meta` package.

## What these tests cover
- **Class-first OCG build** invariants (no ObjectConfig SSOT)
- **Relationship SSOT**: `ClassConfigRelationship` + `ClassConfigRelationshipAttribute`
- **Cross-OCG inheritance augment** behavior
- **Annotation compilation** semantics and **hash** sensitivity to semantics

## How to run (from repo root)

```bash
uv run pytest -q libs/meta/tests/test_ocg_builder_smoke.py
uv run pytest -q libs/meta/tests/test_ocg_annotations_hash.py
uv run pytest -q libs/meta/tests/test_ocg_annotations_compilation.py
uv run pytest -q libs/meta/tests/test_cross_ocg_inheritance_augment.py
```

## Notes
- Kernel-meta tests may use `.aware` code snippets as an input mechanism to produce SSOT `CodeSections`.
  Assertions must stay on **meta invariants**, not grammar parsing details.


