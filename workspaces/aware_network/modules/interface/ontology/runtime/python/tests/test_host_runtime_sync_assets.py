from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from aware_interface.host_runtime import (
    InterfaceHostRuntime,
    load_committed_interface_config_bundle_from_package_ref,
    resolve_interface_config_bundle,
)
from aware_interface.package_ref_resolution import InterfaceRuntimePackageRef
from aware_interface.runtime_artifact_refs import runtime_artifact_refs_from_payload
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)


def _make_interface_config_bundle(
    *,
    name: str,
    description: str | None = None,
) -> InterfaceConfigBundle:
    return InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name=f"{name}-package",
        name=name,
        description=description,
        pane_configs=[],
    )


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


def test_interface_host_runtime_environment_artifact_boot_api_is_removed() -> None:
    assert not hasattr(InterfaceHostRuntime, "from_environment_artifacts")


def test_interface_host_runtime_artifact_set_boot_rejects_sync_assets(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "state" / "db.schema.registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("{}", encoding="utf-8")
    runtime = InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=tmp_path / "repo",
        state_home=tmp_path / "state",
        namespace="service",
        environment_id=uuid4(),
        runtime_artifact_refs=runtime_artifact_refs_from_payload(
            [_ontology_runtime_artifact_ref()]
        ),
        db_schema_registry_path=registry_path,
    )

    with pytest.raises(RuntimeError, match="Projection sync assets"):
        runtime.load_sync_assets(projection_hash="focus-scope-hash")


def test_resolve_interface_config_bundle_loads_workspace_interface_bundle(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "workspace"
    interface_root = repository_root / "interfaces" / "aware_app"
    interface_root.mkdir(parents=True, exist_ok=True)
    _ = (repository_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "home_story_workspace"',
                'title = "Home Story Workspace"',
                'environments = ["aware.environment.toml"]',
                "apis = []",
                "services = []",
                "experiences = []",
                'interfaces = ["interfaces/aware_app/aware.interface.toml"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (interface_root / "aware.interface.toml").write_text(
        "\n".join(
            [
                "aware_interface = 1",
                "",
                "[interface]",
                'package_name = "home-story-aware-app-interface"',
                'fqn_prefix = "aware_home_story_aware_app_interface"',
                "",
                "[build]",
                'config_bundle_path = "bundles/interface.config.bundle.json"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    bundle = _make_interface_config_bundle(
        name="aware_app",
        description="Workspace-declared Interface bundle truth.",
    )
    bundles_dir = interface_root / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    _ = (bundles_dir / "interface.config.bundle.json").write_text(
        bundle.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )

    result = resolve_interface_config_bundle(
        manifest_path=None,
        repository_root=repository_root,
        local_interface_package_name=bundle.interface_package_name,
    )

    assert result.bundle == bundle
    assert result.source == "workspace_interface_artifact"
    assert result.path == (bundles_dir / "interface.config.bundle.json").resolve()


def test_resolve_interface_config_bundle_prefers_committed_interface_package_bundle(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    legacy_bundle = _make_interface_config_bundle(
        name="legacy-local-artifact",
    )
    _ = (runtime_dir / "interface.config.bundle.json").write_text(
        legacy_bundle.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
    committed_bundle = _make_interface_config_bundle(
        name="committed-interface-package",
    )

    result = resolve_interface_config_bundle(
        manifest_path=runtime_dir / "environment.manifest.json",
        committed_interface_config_bundle=committed_bundle,
        allow_local_artifact_fallback=False,
    )

    assert result.bundle == committed_bundle
    assert result.source == "committed_interface_package"
    assert result.path is None


def test_resolve_interface_config_bundle_can_disable_local_artifact_fallback(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    bundle = _make_interface_config_bundle(
        name="local-artifact",
    )
    _ = (runtime_dir / "interface.config.bundle.json").write_text(
        bundle.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )

    result = resolve_interface_config_bundle(
        manifest_path=runtime_dir / "environment.manifest.json",
        allow_local_artifact_fallback=False,
    )

    assert result.bundle is None
    assert result.source is None
    assert result.path is None


@pytest.mark.asyncio
async def test_load_committed_interface_config_bundle_from_package_ref_projects_resolved_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_ref = InterfaceRuntimePackageRef(
        family_key="interface",
        package_kind="interface",
        package_name="aware-workspace-interface",
        semantic_branch_id=str(uuid4()),
        semantic_head_commit_id=str(uuid4()),
    )
    index = object()
    resolved_ref = object()
    bundle = _make_interface_config_bundle(
        name="projected-committed-interface-package",
    )

    async def _fake_resolve(**kwargs: Any) -> object:
        assert kwargs["index"] is index
        assert kwargs["package_ref"] is package_ref
        assert kwargs["materialized_workspace_root"] == tmp_path
        return resolved_ref

    def _fake_project(resolved: object) -> InterfaceConfigBundle:
        assert resolved is resolved_ref
        return bundle

    monkeypatch.setattr(
        "aware_interface.host_runtime.resolve_committed_interface_runtime_package_ref",
        _fake_resolve,
    )
    monkeypatch.setattr(
        "aware_interface.host_runtime.project_interface_config_bundle_from_committed_package",
        _fake_project,
    )

    loaded = await load_committed_interface_config_bundle_from_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=tmp_path,
    )

    assert loaded == bundle
