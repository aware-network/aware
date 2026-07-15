# Attention Layout Workspace — Runtime Via Aware Grammar — SPEC

Status: in progress
Owner: `codex-019ca6f9-7806-7170-b79f-b9a14c1f1f33`

## Goal

Establish a canonical Attention runtime anchor workspace that proofs can consume before grammar-token and lowering/IR expansion.

## Canonical Direction

Non-negotiable invariants:

- Attention runtime/sample anchor is first gate before grammar-token and lowering/IR work.
- Anchor source values are explicit and committed (`anchors/layout_section.anchor.toml`).
- Proof rails validate canonical chain `layout -> layout_section -> section -> section_focus_scope`.
- Focus-scope linkage is section-owned (`Section.add_focus_scope`) with no thread-focus guess rail.

## Current Truth (Repo State)

Exists today:

- Attention module proofs validate layout and section primitives.
- Environment-attention boundary proofs validate portal traversal into layout/section/focus-scope.

Missing before this lane:

- Dedicated Attention runtime sample anchor under `workspaces/aware_network/modules/attention/ontology/runtime/python/samples/e2e/`.
- Sample-local spec package declaring anchor-first execution order.

## Scope

In scope:

- Bootstrap Attention anchor workspace and sample-local specs.
- Add first runtime proof that consumes anchor source values.
- Define dependency contract for follow-up grammar and lowering/IR phases.

Out of scope:

- New grammar token implementation.
- Lowering/IR implementation.
- Experience-side consumption changes.

## Integration Contract

- Attention runtime sample anchor is upstream dependency for `workspaces/aware_network/modules/attention/docs/specs/layout-compiler` implementation phases.
- Environment/Interface rails consume resulting attention contracts after anchor+grammar+lowering gates.

## Evidence And Testing Contract

- `uv run pytest -q workspaces/aware_network/modules/attention/ontology/runtime/python/tests/test_attention_layout_section_anchor_e2e.py`
- `uv run pytest -q workspaces/aware_network/modules/attention/ontology/runtime/python/tests/test_layout_module_proof.py workspaces/aware_network/modules/attention/ontology/runtime/python/tests/test_section_module_proof.py`

## Work Governance

- Phases ledger: `PHASES.md`
- Shared iteration contract: `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`
- Phase directories: `phases/<phase_order>-<phase_slug>/README.md`
- Iteration artifacts: `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
