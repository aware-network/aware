from __future__ import annotations

from aware_specification_fs_adapter import (
    SpecificationFsSchemaResolutionContext,
    adapt_specification_fs_roots,
    close_specification_fs_adapter,
    consume_specification_fs_adaptation,
    install_specification_fs_adapter,
)


def test_canonical_tree_lowers_to_snapshot(
    source_fd: int, canonical_tree, schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        result = adapt_specification_fs_roots(adapter, (spec_root,))
        definition = result.lowering.snapshot.definitions[0]
        assert definition.key == "example.spec"
        assert tuple(phase.phase_key for phase in definition.phases) == (
            "consumer",
            "foundation",
        )
    finally:
        close_specification_fs_adapter(adapter)


def test_toml_formatting_advances_source_but_preserves_meaning(
    source_fd: int, canonical_tree, schema_bytes: bytes
) -> None:
    root, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        before = adapt_specification_fs_roots(adapter, (spec_root,))
        consume_specification_fs_adaptation(adapter, before)
        manifest = root / spec_root / "aware.spec.toml"
        manifest.write_text("# format-only comment\n" + manifest.read_text())
        after = adapt_specification_fs_roots(adapter, (spec_root,))
        consume_specification_fs_adaptation(adapter, after)
        assert (
            before.lowering.closures[0].closure_digest
            != after.lowering.closures[0].closure_digest
        )
        assert (
            before.lowering.snapshot.snapshot_digest
            == after.lowering.snapshot.snapshot_digest
        )
    finally:
        close_specification_fs_adapter(adapter)
