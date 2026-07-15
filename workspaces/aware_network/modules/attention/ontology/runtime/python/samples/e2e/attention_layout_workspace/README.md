# Attention Layout Workspace (E2E anchor)

This workspace is the canonical Attention anchor for layout/section/focus-scope evolution.

It exists to lock execution order:

1. anchor workspace + proof contract
2. grammar token contracts
3. lowering/IR contracts

## Anchor source

- `anchors/layout_section.anchor.toml`

## Proof rail

- `uv run pytest -q workspaces/aware_network/modules/attention/ontology/runtime/python/tests/test_attention_layout_section_anchor_e2e.py`

## Local spec docs

- `docs/specs/runtime-via-aware-grammar/README.md`
