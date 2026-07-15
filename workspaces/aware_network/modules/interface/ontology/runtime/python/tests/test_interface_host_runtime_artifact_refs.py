from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_interface.host_runtime import InterfaceHostRuntime
from aware_interface.runtime_artifact_refs import runtime_artifact_refs_from_payload


_REPO_ROOT = Path(__file__).resolve().parents[8]


def _ontology_runtime_artifact_ref() -> dict[str, object]:
    artifact_set = {
        "artifact_set_id": "ontology-runtime-artifact-set:test",
        "package_name": "aware-test-ontology",
        "fqn_prefix": "aware_test",
        "runtime_contract_version": "aware.ontology.runtime_artifact_set.v1",
        "runtime_projection_descriptors": [
            {
                "projection_name": "FocusScope",
                "projection_hash": "focus-scope-hash",
            }
        ],
    }
    return {
        "artifact_family": "ontology_runtime_artifact_set",
        "artifact_key": "ontology-runtime-artifact-set:test",
        "artifact_role": "runtime_artifact_set",
        "required_for": ["service_boot"],
        "status": "available",
        "package_name": "aware-test-ontology",
        "runtime_contract_version": "aware.ontology.runtime_artifact_set.v1",
        "receipt": {"ontology_runtime_artifact_set": artifact_set},
    }


def test_interface_host_runtime_boots_from_ontology_runtime_artifact_refs(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "state" / "db.schema.registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("{}", encoding="utf-8")
    environment_id = uuid4()

    runtime = InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=tmp_path / "repo",
        state_home=tmp_path / "state",
        namespace="service",
        environment_id=environment_id,
        runtime_artifact_refs=runtime_artifact_refs_from_payload(
            [_ontology_runtime_artifact_ref()]
        ),
        db_schema_registry_path=registry_path,
    )

    assert runtime.manifest_path is None
    assert runtime.environment_id == environment_id
    assert runtime.runtime_artifact_set_count == 1
    assert runtime.opg_count == 1
    assert len(runtime.runtime_artifact_refs) == 1
    with pytest.raises(RuntimeError, match="artifact-set boot"):
        runtime.build_runtime_index()
    with pytest.raises(RuntimeError, match="Projection sync assets"):
        runtime.load_sync_assets(projection_hash="focus-scope-hash")


def test_interface_host_runtime_requires_ontology_runtime_artifact_set_refs(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "state" / "db.schema.registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="requires ontology runtime artifact-set"):
        InterfaceHostRuntime.from_runtime_artifact_refs(
            repository_root=tmp_path / "repo",
            state_home=tmp_path / "state",
            namespace="service",
            environment_id=uuid4(),
            runtime_artifact_refs=(),
            db_schema_registry_path=registry_path,
        )


def test_interface_host_runtime_has_no_environment_artifact_boot_api() -> None:
    assert not hasattr(InterfaceHostRuntime, "from_environment_artifacts")


def test_interface_runtime_sources_do_not_import_environment_bundle_loader() -> None:
    source_paths = (
        _REPO_ROOT
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_interface"
        / "host_runtime.py",
        _REPO_ROOT
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_interface"
        / "projection_runtime.py",
    )
    forbidden = (
        "aware_environment.environment_config.bundle",
        "aware_environment.environment_config.manifest",
        "aware_structure.environment_config.bundle",
        "environment_runtime_resolution",
        "from_environment_artifacts",
        "load_environment_bundle",
        "load_projection_plan_bundle_from_environment_manifest",
    )
    for source_path in source_paths:
        source = source_path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source
