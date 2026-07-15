from aware_meta_ontology import _bootstrap_models
import pytest
import tomllib

from aware_meta.manifest.loader import (
    AwareTomlError,
    load_aware_toml_spec,
    load_aware_toml_spec_from_text,
)
from _meta_runtime_test_paths import REPO_ROOT


def test_meta_ontology_aware_toml_loads() -> None:
    _bootstrap_models()

    repo_root = REPO_ROOT
    toml_path = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "meta"
        / "ontology"
        / "structure"
        / "aware.toml"
    )
    assert toml_path.exists(), f"Expected aware.toml at {toml_path}"

    spec = load_aware_toml_spec(toml_path=toml_path)
    assert spec.package.package_name == "meta-ontology"
    assert spec.package.fqn_prefix == "aware_meta"
    assert spec.build.environment_slug == "aware_meta"
    assert spec.build.sources_dir == "aware"


def test_aware_toml_language_materialization_accepts_class_strict_policy() -> None:
    spec = load_aware_toml_spec_from_text(
        toml_text=_aware_toml_with_stable_ids_policy("class_strict")
    )

    assert spec.language_materializations[0].stable_ids_resolution_policy == (
        "class_strict"
    )


def test_aware_toml_language_materialization_rejects_compat_policy() -> None:
    with pytest.raises(
        AwareTomlError,
        match=(
            r"language_materializations\[0\]\.stable_ids_resolution_policy "
            r"must be class_strict"
        ),
    ):
        load_aware_toml_spec_from_text(
            toml_text=_aware_toml_with_stable_ids_policy("compat")
        )


def test_kernel_compiler_owned_manifests_declare_class_strict_stable_ids() -> None:
    modules_root = REPO_ROOT / "workspaces" / "aware_kernel" / "modules"
    manifest_paths = tuple(modules_root.glob("*/aware.module.toml")) + tuple(
        modules_root.glob("*/ontology/aware.ontology.toml")
    )

    assert manifest_paths
    for manifest_path in manifest_paths:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        policy_owner = (
            data.get("ontology") if "ontology" in data else data.get("module")
        )
        if not isinstance(policy_owner, dict):
            continue
        if policy_owner.get("stable_ids_ownership") != "compiler":
            continue
        assert (
            policy_owner.get("stable_ids_resolution_policy") == "class_strict"
        ), f"{manifest_path} must declare stable_ids_resolution_policy = class_strict"


def test_storage_stable_id_sources_declare_class_identity_keys() -> None:
    storage_sources = {
        "StorageBlob": (
            REPO_ROOT
            / "workspaces"
            / "aware_kernel"
            / "modules"
            / "storage"
            / "ontology"
            / "structure"
            / "aware"
            / "blob"
            / "storage_blob.aware",
            "sha String key",
        ),
        "StorageBucket": (
            REPO_ROOT
            / "workspaces"
            / "aware_kernel"
            / "modules"
            / "storage"
            / "ontology"
            / "structure"
            / "aware"
            / "bucket"
            / "storage_bucket.aware",
            "name String key",
        ),
    }

    for class_name, (source_path, identity_line) in storage_sources.items():
        source_text = source_path.read_text(encoding="utf-8")
        assert identity_line in source_text, (
            f"{class_name} must declare class-level identity key " f"{identity_line!r}"
        )


def _aware_toml_with_stable_ids_policy(policy: str) -> str:
    return "\n".join(
        (
            "aware = 1",
            "",
            "[package]",
            'package_name = "demo-ontology"',
            'fqn_prefix = "aware_demo"',
            'kind = "ontology"',
            "",
            "[build]",
            'environment_slug = "aware_demo"',
            "",
            "[[language_materializations]]",
            'role = "runtime"',
            'language = "python"',
            'output_dir = "python"',
            'import_root = "aware_demo"',
            'package_name = "aware-demo"',
            f'stable_ids_resolution_policy = "{policy}"',
            "",
        )
    )
