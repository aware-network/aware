from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from aware_code.manifest_resolution import (
    SemanticManifestResolution,
    matching_manifest_resolution_descriptors,
    resolve_semantic_manifest,
)
from aware_code.manifest_summary import (
    code_package_info_from_semantic_manifest_resolution,
)
from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
)
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT


_FAKE_OWNER = "aware_fake.provider"
_FAKE_DESCRIPTOR = ModuleSemanticManifestResolutionDescriptor(
    semantic_owner=_FAKE_OWNER,
    manifest_kind="aware_fake_toml",
    filename="aware.fake.toml",
    contract="aware.fake",
    loader_module="aware_fake.manifest.loader",
    loader_name="load_aware_fake_toml_spec",
    workspace_manifest_kind="fake",
    package_role=_FAKE_OWNER,
    semantic_package_family="fake",
    semantic_package_kind="fake_package",
    semantic_projection_name="FakePackage",
    semantic_root_kind="fake",
    code_package_surface="fake",
    copy_code_package_metadata_keys=("fqn_prefix",),
    priority=20,
)
_LOWER_PRIORITY_FAKE_DESCRIPTOR = ModuleSemanticManifestResolutionDescriptor(
    semantic_owner="aware_fake.fallback",
    manifest_kind="aware_fake_toml",
    filename="aware.fake.toml",
    contract="aware.fake",
    loader_module="aware_fake.manifest.loader",
    loader_name="load_aware_fake_toml_spec",
    workspace_manifest_kind="fake",
    code_package_surface="fake",
    priority=50,
)
_FAKE_CONTRACT = ModuleSemanticContract(
    provider_key="aware_fake",
    manifest_resolution=(_LOWER_PRIORITY_FAKE_DESCRIPTOR, _FAKE_DESCRIPTOR),
)


def test_manifest_resolution_descriptors_filter_and_sort_by_contract_truth() -> None:
    descriptors = matching_manifest_resolution_descriptors(
        manifest_path=Path("packages/demo/aware.fake.toml"),
        contracts=(_FAKE_CONTRACT,),
        manifest_kind="aware_fake_toml",
        workspace_manifest_kind="fake",
    )

    assert descriptors == (_FAKE_DESCRIPTOR, _LOWER_PRIORITY_FAKE_DESCRIPTOR)


def test_manifest_resolution_fails_closed_for_unowned_manifest() -> None:
    with pytest.raises(LookupError, match="No semantic contract manifest resolver"):
        resolve_semantic_manifest(
            manifest_path=Path("packages/demo/aware.unknown.toml"),
            contracts=(_FAKE_CONTRACT,),
        )


def test_module_manifest_resolution_is_code_owned(tmp_path: Path) -> None:
    manifest_path = tmp_path / "modules" / "demo" / "aware.module.toml"
    _write(
        manifest_path,
        "\n".join(
            (
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "ontology/structure/aware.toml"',
                "",
            )
        ),
    )

    resolution = resolve_semantic_manifest(
        manifest_path=manifest_path,
        contracts=(AWARE_CODE_SEMANTIC_CONTRACT,),
        workspace_manifest_kind="module",
    )

    assert resolution.descriptor.manifest_kind == "aware_module_toml"
    assert resolution.descriptor.loader_module == "aware_code.module_manifest.loader"
    assert resolution.manifest.packages[0].manifest == "ontology/structure/aware.toml"
    assert resolution.manifest.stable_ids_resolution_policy == "class_strict"


def test_semantic_manifest_summary_uses_descriptor_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path
    manifest_path = workspace_root / "packages" / "demo" / "aware.fake.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("aware_fake = 1\n", encoding="utf-8")
    resolution = SemanticManifestResolution(
        manifest_path=manifest_path,
        descriptor=_FAKE_DESCRIPTOR,
        manifest=SimpleNamespace(
            fake=SimpleNamespace(
                package_name="demo-fake",
                fqn_prefix="aware_demo_fake",
                kind="fake_package",
            ),
            build=SimpleNamespace(
                sources_dir="fake",
                include_paths=("**/*.aware",),
                exclude_paths=("ignored/**",),
            ),
        ),
    )

    code_package = code_package_info_from_semantic_manifest_resolution(
        resolution=resolution,
        workspace_root=workspace_root,
    )

    assert code_package is not None
    assert code_package.name == "demo-fake"
    assert code_package.root_path.as_posix() == "packages/demo"
    assert code_package.manifest_path.as_posix() == "packages/demo/aware.fake.toml"
    assert code_package.metadata["manifest_kind"] == "aware_fake_toml"
    assert code_package.metadata["package_kind"] == "fake_package"
    assert code_package.metadata["code_package_surface"] == "fake"
    assert code_package.metadata["semantic_owner"] == _FAKE_OWNER
    assert code_package.metadata["fqn_prefix"] == "aware_demo_fake"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
