from __future__ import annotations

import os
import subprocess
from pathlib import Path

import aware_specification_fs_adapter.observation as observation_module
import pytest
from aware_specification_fs_adapter import (
    SpecificationFsAdapterError,
    SpecificationFsProfileOutcomeKind,
    SpecificationFsSchemaResolutionContext,
    close_specification_fs_adapter,
    inspect_specification_fs_profile,
    install_specification_fs_adapter,
)


def test_canonical_profile_is_observed(
    source_fd: int, canonical_tree, schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        outcome = inspect_specification_fs_profile(adapter, spec_root)
        assert outcome.kind is SpecificationFsProfileOutcomeKind.CANONICAL_V1
    finally:
        close_specification_fs_adapter(adapter)


def test_manifest_absent_truth_table_and_foreign_profile(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    root, spec_root = canonical_tree
    target = root / spec_root
    manifest = target / "aware.spec.toml"
    manifest_body = manifest.read_text()
    manifest.unlink()
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        outcome = inspect_specification_fs_profile(adapter, spec_root)
        assert (
            outcome.kind is SpecificationFsProfileOutcomeKind.LEGACY_SUPPORTED_STRUCTURE
        )
        for child in tuple(target.iterdir()):
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
            else:
                child.unlink()
        outcome = inspect_specification_fs_profile(adapter, spec_root)
        assert (
            outcome.kind
            is SpecificationFsProfileOutcomeKind.LEGACY_NONCANONICAL_STRUCTURE
        )
        manifest.write_text(
            manifest_body.replace(
                'profile = "specification_fs_v1"', 'profile = "foreign_v1"'
            )
        )
        outcome = inspect_specification_fs_profile(adapter, spec_root)
        assert outcome.kind is SpecificationFsProfileOutcomeKind.FOREIGN_PROFILE
    finally:
        close_specification_fs_adapter(adapter)


def test_installed_mount_namespace_identity_is_revalidated(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        original = adapter._namespace_identity
        adapter._namespace_identity = (original[0], original[1], original[2] + 1)
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"
    finally:
        close_specification_fs_adapter(adapter)


def test_special_node_and_internal_hardlink_reject(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    root, spec_root = canonical_tree
    target = root / spec_root
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        fifo = target / "special"
        os.mkfifo(fifo)
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"
        fifo.unlink()
        os.link(target / "SPEC.md", target / "duplicate.md")
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"
    finally:
        close_specification_fs_adapter(adapter)


def test_sacrificial_linux_mount_boundaries(
    source_fd: int,
    canonical_tree: tuple[Path, str],
    schema_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get("AWARE_SPECIFICATION_SACRIFICIAL_MOUNT_PROOF") != "1":
        pytest.skip("requires a separately admitted sacrificial mount namespace")
    root, spec_root = canonical_tree
    target = root / spec_root
    alternate = root / "alternate"
    alternate.mkdir()
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )

    def expect_rejection() -> None:
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"

    try:
        subprocess.run(["mount", "--bind", alternate, target], check=True)
        try:
            expect_rejection()
        finally:
            subprocess.run(["umount", target], check=True)

        subprocess.run(["mount", "-t", "tmpfs", "tmpfs", target], check=True)
        try:
            expect_rejection()
        finally:
            subprocess.run(["umount", target], check=True)

        original_inventory = observation_module._inventory

        def mount_during_observation(root_fd: int, expected_mnt_id: int):
            subprocess.run(["mount", "--bind", alternate, target], check=True)
            return original_inventory(root_fd, expected_mnt_id)

        monkeypatch.setattr(observation_module, "_inventory", mount_during_observation)
        try:
            expect_rejection()
        finally:
            subprocess.run(["umount", target], check=True)
    finally:
        close_specification_fs_adapter(adapter)
