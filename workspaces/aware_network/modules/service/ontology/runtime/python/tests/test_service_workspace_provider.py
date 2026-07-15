from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_ontology.stable_ids import stable_api_package_id
from aware_code.semantic_materialization import (
    SemanticPackageMaterializationExecutionContext,
    SemanticPackageMaterializationRequest,
)
from aware_service_runtime.materialization import workspace_provider
from aware_service_runtime import workspace_context
from aware_service_runtime.runtime_resolution import (
    ServiceProtocolApiReferenceLaneInput,
)


@pytest.mark.asyncio
async def test_service_dependency_api_branch_requires_current_committed_witness() -> (
    None
):
    package_name = "reactivity-service-api"
    branch_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    projection_hash = "api-projection-hash"
    expected_branch_id = branch_id

    class _CommitStore:
        async def head(self, *, branch_id: UUID, projection_hash: str) -> object:
            assert branch_id == expected_branch_id
            assert projection_hash == "api-projection-hash"
            return {"commit_id": str(head_commit_id)}

    resolved = await workspace_context._validated_dependency_api_package_branch_id(
        entry={
            "semantic_lane_ref": {
                "branch_id": str(branch_id),
                "projection_hash": projection_hash,
                "head_commit_id": str(head_commit_id),
                "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
                "semantic_projection_name": "ApiPackage",
                "semantic_package_id": str(stable_api_package_id(name=package_name)),
            }
        },
        package_name=package_name,
        api_projection_name="ApiPackage",
        api_projection_hash=projection_hash,
        commit_store=cast(Any, _CommitStore()),
    )

    assert resolved == branch_id


@pytest.mark.asyncio
async def test_service_dependency_api_branch_rejects_stale_head_witness() -> None:
    package_name = "reactivity-service-api"
    branch_id = uuid4()
    witnessed_head_commit_id = uuid4()

    class _CommitStore:
        async def head(self, **_: object) -> object:
            return {"commit_id": str(uuid4())}

    with pytest.raises(RuntimeError, match="witness HEAD mismatch"):
        await workspace_context._validated_dependency_api_package_branch_id(
            entry={
                "semantic_lane_ref": {
                    "branch_id": str(branch_id),
                    "projection_hash": "api-projection-hash",
                    "head_commit_id": str(witnessed_head_commit_id),
                    "object_instance_graph_commit_id": str(uuid4()),
                    "semantic_projection_name": "ApiPackage",
                    "semantic_package_id": str(
                        stable_api_package_id(name=package_name)
                    ),
                }
            },
            package_name=package_name,
            api_projection_name="ApiPackage",
            api_projection_hash="api-projection-hash",
            commit_store=cast(Any, _CommitStore()),
        )


def test_service_dependency_api_commit_store_uses_owner_workspace_root(
    tmp_path: Path,
) -> None:
    commit_store = workspace_context._dependency_entry_commit_store(
        entry={"owner_workspace_root": tmp_path.as_posix()},
        package_name="reactivity-service-api",
    )

    assert commit_store.aware_root == tmp_path.resolve()


@pytest.mark.asyncio
async def test_service_workspace_provider_reports_full_rebuild_fallback_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "aware.service.toml"
    service_toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "demo-service"',
                'fqn_prefix = "demo_service"',
                "",
                "[build]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    source_code_package_id = uuid4()
    implementation_code_package_id = uuid4()
    implementation_oig_commit_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    package_oig_commit_id = uuid4()
    service_config_oig_commit_id = uuid4()
    owned_ocg_package_id = uuid4()
    owned_ocg_id = uuid4()
    owned_ocg_source_code_package_id = uuid4()
    owned_ocg_package_oig_commit_id = uuid4()
    owned_ocg_root_oig_commit_id = uuid4()
    activation_service_config_id = uuid4()
    activation_service_id = uuid4()
    activation_service_config_branch_id = uuid4()
    activation_service_config_head_commit_id = uuid4()
    activation_service_config_oig_commit_id = uuid4()
    activation_service_branch_id = uuid4()
    activation_service_head_commit_id = uuid4()
    activation_service_oig_commit_id = uuid4()

    async def _fake_materialize_service_package_from_manifest(
        **_: object,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            service_toml_path=tmp_path / "aware.service.toml",
            workspace_root=tmp_path,
            service_config=SimpleNamespace(name="demo_service", id=uuid4()),
            service_package=SimpleNamespace(name="demo-service", id=uuid4()),
            source_code_package_id=source_code_package_id,
            implementation_code_package_ids=(implementation_code_package_id,),
            implementation_code_package_refs=(
                {
                    "code_package_id": implementation_code_package_id,
                    "object_instance_graph_commit_id": implementation_oig_commit_id,
                    "package_name": "demo-service",
                    "manifest_relative_path": "pyproject.toml",
                    "package_root": ".",
                    "sources_root": "aware_demo_service",
                    "language": "python",
                },
            ),
            object_config_graph_packages=(
                SimpleNamespace(
                    manifest_path=tmp_path / "db" / "aware.toml",
                    manifest_relative_path="db/aware.toml",
                    role="local_state",
                    package_name="demo-service-db",
                    package_fqn_prefix="demo_service_local",
                    package_kind="state",
                    object_config_graph_package_id=owned_ocg_package_id,
                    object_config_graph_id=owned_ocg_id,
                    package_branch_id=None,
                    source_code_package_id=owned_ocg_source_code_package_id,
                    object_config_graph_package_commit_id=None,
                    object_config_graph_package_head_commit_id=None,
                    object_config_graph_package_object_instance_graph_commit_id=(
                        owned_ocg_package_oig_commit_id
                    ),
                    object_config_graph_commit_id=None,
                    object_config_graph_head_commit_id=None,
                    object_config_graph_object_instance_graph_commit_id=(
                        owned_ocg_root_oig_commit_id
                    ),
                    language_materialization_targets=(
                        {
                            "role": "sqlite_schema",
                            "language": "sqlite",
                            "output_dir": "sqlite",
                            "import_root": "demo_service_local",
                            "package_name": "demo-service-db",
                            "materialization_source": "ontology",
                        },
                    ),
                ),
            ),
            api_provider_set_refs=(),
            api_provider_set_commit_id=None,
            api_provider_set_head_commit_id=None,
            service_source_path="services/demo.aware",
            source_files=("services/demo.aware",),
            phase_timings_s={},
            definition_commit_id=uuid4(),
            service_config_object_instance_graph_commit_id=(
                service_config_oig_commit_id
            ),
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            package_object_instance_graph_commit_id=package_oig_commit_id,
            activation_lanes=(
                SimpleNamespace(
                    service_name="demo_service",
                    service_config_id=activation_service_config_id,
                    service_id=activation_service_id,
                    service_config_branch_id=activation_service_config_branch_id,
                    service_config_projection_hash="service-config-projection",
                    service_config_head_commit_id=(
                        activation_service_config_head_commit_id
                    ),
                    service_config_object_instance_graph_commit_id=(
                        activation_service_config_oig_commit_id
                    ),
                    service_branch_id=activation_service_branch_id,
                    service_projection_hash="service-projection",
                    service_head_commit_id=activation_service_head_commit_id,
                    service_object_instance_graph_commit_id=(
                        activation_service_oig_commit_id
                    ),
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_service_package_from_manifest",
        _fake_materialize_service_package_from_manifest,
    )
    monkeypatch.setattr(
        workspace_provider,
        "load_service_protocol_api_reference_lane_inputs_from_dependencies",
        lambda **_: (),
    )

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=service_toml_path,
            change_preview={
                "affected_semantic_keys": (
                    "service:demo_service",
                    " service:demo_service ",
                ),
            },
        )
    )

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("service:demo_service",)
    assert result.applied_semantic_keys == ("service:demo_service",)
    assert result.skipped_semantic_keys == ()
    assert result.stale_semantic_keys == ()
    assert result.fallback_reason is not None
    assert "not implemented delta materialization" in result.fallback_reason
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert len(result.bundle_packages) == 3
    bundle = result.bundle_packages[0]
    assert bundle.package_key == "demo-service"
    assert bundle.semantic_head_commit_id == package_head_commit_id
    assert bundle.semantic_object_instance_graph_commit_id == package_oig_commit_id
    assert bundle.semantic_root_object_instance_graph_commit_id == (
        service_config_oig_commit_id
    )
    assert bundle.semantic_root_kind == "service_config"
    assert bundle.source_code_package_id == source_code_package_id
    assert bundle.runtime_code_package_refs == (
        {
            "role": "service_implementation_package",
            "source_code_package_id": implementation_code_package_id,
            "source_object_instance_graph_commit_id": implementation_oig_commit_id,
            "package_name": "demo-service",
            "manifest_relative_path": "pyproject.toml",
            "package_root": ".",
            "sources_root": "aware_demo_service",
            "language": "python",
        },
    )
    assert result.details["object_config_graph_packages"] == [
        {
            "manifest_path": (tmp_path / "db" / "aware.toml").as_posix(),
            "manifest_relative_path": "db/aware.toml",
            "role": "local_state",
            "package_name": "demo-service-db",
            "package_fqn_prefix": "demo_service_local",
            "package_kind": "state",
            "code_package_surface": "structure",
            "object_config_graph_package_id": str(owned_ocg_package_id),
            "object_config_graph_id": str(owned_ocg_id),
            "package_branch_id": None,
            "source_code_package_id": str(owned_ocg_source_code_package_id),
            "object_config_graph_package_head_commit_id": None,
            "object_config_graph_package_object_instance_graph_commit_id": str(
                owned_ocg_package_oig_commit_id
            ),
            "object_config_graph_object_instance_graph_commit_id": str(
                owned_ocg_root_oig_commit_id
            ),
            "language_materialization_targets": [
                {
                    "role": "sqlite_schema",
                    "language": "sqlite",
                    "output_dir": "sqlite",
                    "import_root": "demo_service_local",
                    "package_name": "demo-service-db",
                    "materialization_source": "ontology",
                }
            ],
        }
    ]
    assert result.details["emitted_owned_object_config_graph_package_count"] == 1
    assert len(result.emitted_package_outputs) == 1
    output = result.emitted_package_outputs[0]
    assert output.producer_provider_key == "aware_service"
    assert output.producer_key == "aware_service.owned_object_config_graph_package"
    assert output.target_provider_key == "aware_meta"
    assert output.target_input_key == "aware_meta.object_config_graph_package_manifest"
    assert output.package_key == "demo-service-db"
    assert output.input_artifact_path == tmp_path / "db" / "aware.toml"
    assert output.input_artifact_payload["package_name"] == "demo-service-db"
    assert output.input_artifact_payload["fqn_prefix"] == "demo_service_local"
    assert output.input_artifact_payload["package_kind"] == "state"
    assert output.input_artifact_payload["code_package_surface"] == "structure"
    assert output.input_artifact_payload["package_root"] == "db"
    assert output.input_artifact_payload["object_instance_graph_commit_id"] == str(
        owned_ocg_package_oig_commit_id
    )
    assert output.provider_payload["source"] == "service.object_config_graph_packages"
    service_config_bundle, service_bundle = result.bundle_packages[1:]
    assert service_config_bundle.package_key == (
        "demo-service:activation:service-config:demo_service"
    )
    assert service_config_bundle.semantic_package_id == activation_service_config_id
    assert (
        service_config_bundle.semantic_branch_id == activation_service_config_branch_id
    )
    assert (
        service_config_bundle.semantic_head_commit_id
        == activation_service_config_head_commit_id
    )
    assert (
        service_config_bundle.semantic_object_instance_graph_commit_id
        == activation_service_config_oig_commit_id
    )
    assert service_config_bundle.semantic_projection_name == "ServiceConfig"
    assert service_bundle.package_key == (
        "demo-service:activation:service:demo_service"
    )
    assert service_bundle.semantic_package_id == activation_service_id
    assert service_bundle.semantic_branch_id == activation_service_branch_id
    assert service_bundle.semantic_head_commit_id == activation_service_head_commit_id
    assert (
        service_bundle.semantic_object_instance_graph_commit_id
        == activation_service_oig_commit_id
    )
    assert service_bundle.semantic_projection_name == "Service"


@pytest.mark.asyncio
async def test_service_workspace_provider_materializes_api_reference_lanes_from_runtime_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "aware.service.toml"
    service_toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "demo-service"',
                'fqn_prefix = "demo_service"',
                "",
                "[build]",
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    api_projection_hash = "api-projection"
    api_head_commit_id = uuid4()
    api_oig_commit_id = uuid4()
    api_root_source_object_id = uuid4()
    preseed_branch_id = uuid4()
    stale_proof_branch_id = uuid4()
    captured_api_lane_branch_id: UUID | None = None
    captured_accessible_graphs: tuple[object, ...] | None = None
    captured_service_accessible_graphs: tuple[object, ...] | None = None
    captured_service_api_refs: dict[str, UUID] | None = None
    captured_service_api_roots: dict[str, Path] | None = None
    captured_dependencies: tuple[object, ...] | None = None
    api_materialized = False

    class _CommitStore:
        async def head(self, **_: object) -> dict[str, str] | None:
            if not api_materialized:
                return None
            return {"commit_id": str(api_head_commit_id)}

        async def get_commit_envelope(self, **_: object) -> SimpleNamespace:
            return SimpleNamespace(
                object_instance_graph_commit_id=api_oig_commit_id,
                root_source_object_id=api_root_source_object_id,
            )

    class _Graph:
        name = "aware_proof_api"

    def _resolve_dependency_payloads(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "package_name": "proof-service-api",
                "version_number": None,
                "kind": "api_service_protocol",
                "expected_hash_sha256": "1" * 64,
            },
        )

    def _load_api_reference_inputs(
        **kwargs: object,
    ) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
        nonlocal captured_dependencies
        captured_dependencies = tuple(cast(tuple[object, ...], kwargs["dependencies"]))
        return (
            ServiceProtocolApiReferenceLaneInput(
                package_name="proof-service-api",
                api_name="proof",
                api_source_path="apis/proof/bindings/proof.apis.aware",
                branch_key="proof-service-api:proof",
                compile_plan_payload={
                    "package_name": "proof-service-api",
                    "api_ontology": [
                        {
                            "api": {
                                "name": "proof",
                                "source_path": "apis/proof/bindings/proof.apis.aware",
                            }
                        }
                    ],
                },
                accessible_graphs=(cast(Any, _Graph()),),
                projection_refs=frozenset(),
                endpoint_refs=frozenset(),
                endpoint_function_refs=frozenset(),
            ),
        )

    async def _materialize_api_compile_plan_ontology(**kwargs: object) -> object:
        nonlocal api_materialized
        nonlocal captured_api_lane_branch_id, captured_accessible_graphs
        lane = cast(Any, kwargs["lane"])
        captured_api_lane_branch_id = lane.branch_id
        assert lane.projection_hash == api_projection_hash
        captured_accessible_graphs = tuple(
            cast(tuple[object, ...], kwargs["accessible_graphs"])
        )
        api_materialized = True
        return object()

    async def _materialize_service_package_from_manifest(
        **kwargs: object,
    ) -> SimpleNamespace:
        nonlocal captured_service_accessible_graphs
        nonlocal captured_service_api_refs
        nonlocal captured_service_api_roots
        captured_service_api_refs = cast(
            dict[str, UUID],
            kwargs["api_reference_branch_ids_by_api_name"],
        )
        captured_service_api_roots = cast(
            dict[str, Path],
            kwargs["api_reference_commit_store_roots_by_api_name"],
        )
        captured_service_accessible_graphs = tuple(
            cast(tuple[object, ...], kwargs["api_reference_accessible_graphs"])
        )
        return SimpleNamespace(
            service_toml_path=service_toml_path,
            workspace_root=tmp_path,
            service_config=SimpleNamespace(name="demo_service", id=uuid4()),
            service_package=SimpleNamespace(name="demo-service", id=uuid4()),
            source_code_package_id=None,
            implementation_code_package_ids=(),
            implementation_code_package_refs=(),
            object_config_graph_packages=(),
            api_provider_set_refs=(),
            api_provider_set_commit_id=None,
            api_provider_set_head_commit_id=None,
            service_source_path="services/demo.aware",
            source_files=("services/demo.aware",),
            phase_timings_s={},
            definition_commit_id=uuid4(),
            service_config_object_instance_graph_commit_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            package_object_instance_graph_commit_id=uuid4(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "resolve_service_package_dependency_payloads",
        _resolve_dependency_payloads,
    )
    monkeypatch.setattr(
        workspace_provider,
        "load_service_protocol_api_reference_lane_inputs_from_dependencies",
        _load_api_reference_inputs,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        lambda **_: api_projection_hash,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_api_compile_plan_ontology",
        _materialize_api_compile_plan_ontology,
    )
    monkeypatch.setattr(
        workspace_provider,
        "FSCommitStore",
        _CommitStore,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_service_package_from_manifest",
        _materialize_service_package_from_manifest,
    )

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=service_toml_path,
            change_preview={},
            context={
                "workspace_dependency_semantic_package_entries": (
                    {
                        "code_package_name": "proof-service-api",
                        "owner_workspace_root": tmp_path.as_posix(),
                    },
                ),
            },
            execution_context=SemanticPackageMaterializationExecutionContext(
                provider_entries={
                    "aware_service": {
                        "api_reference_branch_ids_by_api_name": {
                            "other": preseed_branch_id,
                            "proof": stale_proof_branch_id,
                        }
                    }
                }
            ),
        )
    )

    assert captured_api_lane_branch_id is not None
    assert captured_api_lane_branch_id == (
        workspace_provider.service_protocol_api_reference_branch_id(
            "proof-service-api:proof"
        )
    )
    assert captured_service_api_refs is not None
    assert captured_dependencies == (
        {
            "package_name": "proof-service-api",
            "version_number": None,
            "kind": "api_service_protocol",
            "expected_hash_sha256": "1" * 64,
        },
    )
    assert captured_service_api_refs["other"] == preseed_branch_id
    assert captured_service_api_refs["proof"] == captured_api_lane_branch_id
    assert captured_service_api_refs["proof"] != stale_proof_branch_id
    assert captured_service_api_refs["proof".casefold()] == captured_api_lane_branch_id
    assert captured_service_api_roots == {
        "proof-service-api": tmp_path.resolve(),
    }
    assert captured_accessible_graphs is not None
    assert [getattr(graph, "name") for graph in captured_accessible_graphs] == [
        "aware_proof_api"
    ]
    assert captured_service_accessible_graphs is not None
    assert [getattr(graph, "name") for graph in captured_service_accessible_graphs] == [
        "aware_proof_api"
    ]
    assert len(result.bundle_packages) == 2
    api_reference_bundle = result.bundle_packages[1]
    assert api_reference_bundle.package_key == (
        "demo-service:api-reference:proof-service-api:proof"
    )
    assert api_reference_bundle.semantic_package_id == api_root_source_object_id
    assert api_reference_bundle.semantic_root_id == api_root_source_object_id
    assert api_reference_bundle.semantic_branch_id == captured_api_lane_branch_id
    assert api_reference_bundle.semantic_head_commit_id == api_head_commit_id
    assert (
        api_reference_bundle.semantic_object_instance_graph_commit_id
        == api_oig_commit_id
    )
    assert (
        api_reference_bundle.semantic_root_object_instance_graph_commit_id
        == api_oig_commit_id
    )
    assert api_reference_bundle.semantic_root_kind == "service_protocol_api_reference"
    assert api_reference_bundle.semantic_projection_name == "Api"
    assert api_reference_bundle.semantic_projection_hash == api_projection_hash
