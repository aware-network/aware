# Validating Aware Grammar

## Run Tests

From repo root:

```bash
# If you hit UV cache permission issues, set UV_CACHE_DIR to a writable location.
UV_CACHE_DIR=$PWD/.uv-cache uv run --project languages/aware/grammar/grammar pytest -q languages/aware/grammar/grammar/tests
```

OCG builder tests (Aware):

```bash
UV_CACHE_DIR=$PWD/.uv-cache uv run --project languages/aware/grammar/grammar pytest -q languages/aware/grammar/grammar/tests/test_object_config_graph_builder.py
```

## Regenerate the Parser

The tree-sitter grammar lives at `languages/aware/grammar/tree_sitter/tree_sitter_aware/grammar.js`.

From `languages/aware/grammar/tree_sitter/tree_sitter_aware/`:

```bash
tree-sitter generate --abi 14
```

Rebuild the python extension binding (repo-local):

```bash
cd languages/aware/grammar/tree_sitter
python3 setup.py build_ext --inplace
```

## Known Parser Gaps (Tracked)

- Annotation paths support multiple `::` segments semantically (see `libs/meta/.../annotation/compiler.py`), but the current tree-sitter rule only models one segment structurally. This affects highlighting more than compilation.
- Void return signatures in the kernel ontology use `-> { }`; tree-sitter recovery allows this, and builders treat missing return types as empty outputs.
