from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
import pytest_asyncio

from aware_ontology_sdk import OntologySdkClient
from aware_ontology_service_api import AwareOntologyServiceApiClient
from aware_ontology_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactReceipt,
    OntologyDatabaseArtifactRef,
)
from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_service_runtime.host_contract import (
    ServiceHostContractBackendInput,
    ServiceHostContractTargetInput,
    ontology_authority_runtime_manifest_paths,
    ontology_runtime_artifact_sql_root_from_manifest_path,
    ontology_runtime_manifest_db_schema_hash,
    resolve_service_host_contracts_for_tomls,
)
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT
from aware_service_service_dto.host import (
    ServiceHostDbRequirement,
    ServiceHostDbRequirementKind,
)
from aware_sdk_network.testing.live import (
    LiveSdkEndpointProofRow,
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
    load_json_payload,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


ONTOLOGY_API_PACKAGE_NAME = "ontology-service-api"
STORAGE_ONTOLOGY_AWARE_TOML = (
    "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml"
)
WORKSPACE_ROOT = "/home/luis/aware"
WORKSPACE_ROOT_PATH = Path(WORKSPACE_ROOT).resolve()
ONTOLOGY_SERVICE_TOML_PATH = (
    WORKSPACE_ROOT_PATH
    / "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml"
)


@dataclass(frozen=True, slots=True)
class OntologyLiveSdk:
    sdk: OntologySdkClient
    actor_id: UUID


ONTOLOGY_ENDPOINT_MATRIX: tuple[LiveSdkEndpointProofRow, ...] = (
    LiveSdkEndpointProofRow(
        "ontology.commit.subscribe",
        "sdk.subscribe_commits",
        2,
        "green",
        "unary subscription acceptance plus generated SDK commit stream event",
    ),
    LiveSdkEndpointProofRow(
        "ontology.graph.get_lane_head",
        "sdk.get_lane_head",
        1,
        "green",
        "read-back of storage-ontology ObjectConfigGraphPackage lane head",
    ),
    LiveSdkEndpointProofRow(
        "ontology.graph.get_object_instance_graph_commit",
        "sdk.get_object_instance_graph_commit",
        1,
        "green",
        "read-back of storage-ontology ObjectInstanceGraphCommit",
    ),
    LiveSdkEndpointProofRow(
        "ontology.graph.invoke_function",
        "sdk.invoke_function",
        3,
        "green",
        "OntologyPackage.build constructor mutation with lane-head read-back",
    ),
    LiveSdkEndpointProofRow(
        "ontology.graph.resolve_projection",
        "sdk.resolve_projection",
        1,
        "green",
        "projection hash resolution for OntologyPackage and ObjectConfigGraphPackage",
    ),
    LiveSdkEndpointProofRow(
        "ontology.package.ensure_object_config_graph_package",
        "sdk.ensure_object_config_graph_package",
        2,
        "green",
        "idempotent storage-ontology package ensure in isolated live Ontology DB",
    ),
    LiveSdkEndpointProofRow(
        "ontology.persistence.ensure_ready",
        "sdk.ensure_ready",
        2,
        "green",
        "composite Ontology authority DB readiness confirmation against live marker",
    ),
    LiveSdkEndpointProofRow(
        "ontology.runtime.resolve_runtime_artifact_set",
        "sdk.resolve_runtime_artifact_set",
        1,
        "green",
        "explicit-coordinate artifact-set resolve; full artifact payload needs source fixture",
    ),
)


def test_ontology_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in ONTOLOGY_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(ONTOLOGY_ENDPOINT_MATRIX) == 8


def test_live_ontologies_advertise_generated_ontology_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=ONTOLOGY_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest_asyncio.fixture()
async def ontology_sdk(
    live_sdk_api_dependency_routes,
    live_sdk_actor_id,
):
    if live_sdk_actor_id is None:
        pytest.skip(
            "Ontology live SDK calls require Service admission actor context; "
            "set AWARE_SDK_LIVE_ACTOR_ID"
        )
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=ONTOLOGY_API_PACKAGE_NAME,
        actor_id=live_sdk_actor_id,
    )
    try:
        yield OntologyLiveSdk(
            sdk=OntologySdkClient(
                api_client=AwareOntologyServiceApiClient(api_invoker),
            ),
            actor_id=live_sdk_actor_id,
        )
    finally:
        await close_live_api_client(api_invoker)


@pytest.mark.asyncio
async def test_ontology_runtime_artifact_set_coordinates_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    response = await ontology_sdk.sdk.resolve_runtime_artifact_set(
        actor_id=ontology_sdk.actor_id,
        package_name="ontology-ontology",
        fqn_prefix="aware_ontology",
        include_artifacts=False,
    )
    assert response.status == "resolved"
    assert response.package_name == "ontology-ontology"
    assert response.fqn_prefix == "aware_ontology"
    assert response.artifact_set is not None
    assert response.artifact_set.package_name == "ontology-ontology"
    assert response.artifact_set.fqn_prefix == "aware_ontology"
    assert response.artifact_set.activation_allowed is False
    assert response.artifact_set.artifacts == []


@pytest.mark.asyncio
async def test_ontology_commit_subscribe_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    response = await ontology_sdk.sdk.subscribe_commits(
        subscriber_id="live-sdk-ontology-proof",
        include_artifact_refs=False,
    )
    assert response.accepted is True
    assert response.subscriber_id == "live-sdk-ontology-proof"
    assert response.error is None


@pytest.mark.asyncio
async def test_ontology_projection_resolve_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    response = await ontology_sdk.sdk.resolve_projection(
        actor_id=ontology_sdk.actor_id,
        projection_name="OntologyPackage",
        include_available=True,
    )
    assert response.status == "succeeded"
    assert response.projection_name == "OntologyPackage"
    assert response.projection_hash
    assert response.object_projection_graph_id is not None
    assert "OntologyPackage" in response.available_projection_names


@pytest.mark.asyncio
async def test_ontology_storage_package_ensure_and_readback_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    package_response = await ontology_sdk.sdk.ensure_object_config_graph_package(
        actor_id=ontology_sdk.actor_id,
        workspace_root=WORKSPACE_ROOT,
        aware_toml_path=STORAGE_ONTOLOGY_AWARE_TOML,
        include_object_config_graph=False,
        collect_telemetry=False,
    )
    assert package_response.status == "succeeded"
    assert package_response.package_name == "storage-ontology"
    assert package_response.fqn_prefix == "aware_storage"
    assert package_response.package_branch_id is not None
    assert package_response.object_config_graph_package_head_commit_id is not None
    assert (
        package_response.object_config_graph_package_object_instance_graph_commit_id
        is not None
    )

    projection_response = await ontology_sdk.sdk.resolve_projection(
        actor_id=ontology_sdk.actor_id,
        projection_name="ObjectConfigGraphPackage",
    )
    assert projection_response.status == "succeeded"
    assert projection_response.projection_hash

    lane_head = await ontology_sdk.sdk.get_lane_head(
        actor_id=ontology_sdk.actor_id,
        domain_branch_id=package_response.package_branch_id,
        domain_projection_hash=projection_response.projection_hash,
    )
    assert lane_head.status == "succeeded"
    assert (
        lane_head.domain_commit_id
        == package_response.object_config_graph_package_head_commit_id
    )
    assert lane_head.object_instance_graph_id is not None

    commit = await ontology_sdk.sdk.get_object_instance_graph_commit(
        actor_id=ontology_sdk.actor_id,
        domain_branch_id=package_response.package_branch_id,
        domain_projection_hash=projection_response.projection_hash,
        domain_commit_id=lane_head.domain_commit_id,
    )
    assert commit.status == "succeeded"
    assert (
        commit.object_instance_graph_commit_id
        == package_response.object_config_graph_package_object_instance_graph_commit_id
    )
    assert commit.object_instance_graph_identity_id is not None


@pytest.mark.asyncio
async def test_ontology_persistence_ensure_ready_live_sdk(
    ontology_sdk: OntologyLiveSdk,
    live_sdk_provider_refs_path: Path,
    tmp_path: Path,
) -> None:
    receipt = _build_ontology_authority_readiness_receipt(
        provider_refs_path=live_sdk_provider_refs_path,
        tmp_path=tmp_path,
    )

    response = await ontology_sdk.sdk.ensure_ready(
        actor_id=ontology_sdk.actor_id,
        database_artifact_receipt=receipt,
        boot_policy="fail",
    )

    assert response.status == "succeeded"
    assert response.ontology_package_id == receipt.ontology_package_id
    assert response.ocg_hash == receipt.ocg_hash
    assert response.db_schema_hash == receipt.db_schema_hash
    assert response.marker_ocg_hash == receipt.db_schema_hash
    assert response.sql_root_count == len(receipt.sql_roots)
    assert response.step_count == 0
    assert response.installed is False
    assert response.migrated is False


@pytest.mark.asyncio
async def test_ontology_invoke_function_mutates_and_reads_lane_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    projection = await ontology_sdk.sdk.resolve_projection(
        actor_id=ontology_sdk.actor_id,
        projection_name="OntologyPackage",
    )
    assert projection.status == "succeeded"
    assert projection.projection_hash
    assert projection.object_projection_graph_id is not None

    branch_id = uuid4()
    response = await ontology_sdk.sdk.invoke_function(
        actor_id=ontology_sdk.actor_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection.projection_hash,
        object_projection_graph_id=projection.object_projection_graph_id,
        function_id=_ontology_package_build_function_id(),
        call_target="opg_constructor",
        kwargs=_ontology_package_build_kwargs("invoke"),
        commit=True,
        publish=True,
    )

    assert response.status == "succeeded"
    assert response.domain_branch_id == branch_id
    assert response.domain_projection_hash == projection.projection_hash
    assert response.domain_commit_id is not None
    assert response.object_instance_graph_commit_id is not None
    assert response.root_object_id is not None
    assert response.commit_event is not None
    assert response.commit_event.domain_commit_id == response.domain_commit_id
    assert response.commit_event.commit_action is not None
    assert (
        response.commit_event.commit_action.operation_label == "OntologyPackage.build"
    )

    lane_head = await ontology_sdk.sdk.get_lane_head(
        actor_id=ontology_sdk.actor_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection.projection_hash,
    )
    assert lane_head.status == "succeeded"
    assert lane_head.domain_commit_id == response.domain_commit_id
    assert lane_head.root_object_id == response.root_object_id


@pytest.mark.asyncio
async def test_ontology_commit_stream_observes_invoke_function_live_sdk(
    ontology_sdk: OntologyLiveSdk,
) -> None:
    projection = await ontology_sdk.sdk.resolve_projection(
        actor_id=ontology_sdk.actor_id,
        projection_name="OntologyPackage",
    )
    assert projection.status == "succeeded"
    assert projection.projection_hash
    assert projection.object_projection_graph_id is not None

    branch_id = uuid4()
    stream = ontology_sdk.sdk.stream_commits(
        subscriber_id=f"live-sdk-ontology-stream-{uuid4().hex[:12]}",
        branch_filters=(branch_id,),
        projection_hash_filters=(projection.projection_hash,),
        include_artifact_refs=False,
    )
    event_task = asyncio.create_task(anext(stream))
    try:
        await asyncio.sleep(0.2)
        response = await ontology_sdk.sdk.invoke_function(
            actor_id=ontology_sdk.actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection.projection_hash,
            object_projection_graph_id=projection.object_projection_graph_id,
            function_id=_ontology_package_build_function_id(),
            call_target="opg_constructor",
            kwargs=_ontology_package_build_kwargs("stream"),
            commit=True,
            publish=True,
        )

        event = await asyncio.wait_for(event_task, timeout=45.0)
    finally:
        if not event_task.done():
            event_task.cancel()
            await asyncio.gather(event_task, return_exceptions=True)
        await stream.aclose()

    assert response.status == "succeeded"
    assert event.event_family == "ontology.oig_commit"
    assert event.ontology_authority_id == "aware_ontology"
    assert event.actor_id == ontology_sdk.actor_id
    assert event.domain_branch_id == branch_id
    assert event.domain_projection_hash == projection.projection_hash
    assert event.domain_commit_id == response.domain_commit_id
    assert event.object_instance_graph_commit_id == (
        response.object_instance_graph_commit_id
    )
    assert event.commit_action is not None
    assert event.commit_action.function_id == _ontology_package_build_function_id()
    assert event.commit_action.operation_label == "OntologyPackage.build"


def _ontology_package_build_kwargs(prefix: str) -> dict[str, object]:
    return {
        "name": f"live-sdk-{prefix}-ontology-package-{uuid4().hex[:12]}",
        "fqn_prefix": f"live_sdk_{prefix}_{uuid4().hex[:8]}",
        "title": f"Live SDK Ontology {prefix} proof",
        "description": "SDK live integration proof fixture.",
    }


def _ontology_package_build_function_id() -> UUID:
    environment_path = (
        Path(WORKSPACE_ROOT)
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/compiler/environment.json"
    )
    payload = json.loads(environment_path.read_text(encoding="utf-8"))
    for object_config_graph in payload.get("object_config_graphs", []):
        for node in object_config_graph.get("object_config_graph_nodes", []):
            class_config = node.get("class_config") or {}
            if class_config.get("class_fqn") != (
                "aware_ontology.default.ontology.OntologyPackage"
            ):
                continue
            for function_link in class_config.get("class_config_function_configs", []):
                function_config = function_link.get("function_config") or {}
                if function_config.get("name") == "build":
                    return UUID(function_config["id"])
    raise RuntimeError("Could not resolve OntologyPackage.build FunctionConfig id.")


def _build_ontology_authority_readiness_receipt(
    *,
    provider_refs_path: Path,
    tmp_path: Path,
) -> OntologyDatabaseArtifactReceipt:
    provider_ref = load_json_payload(provider_refs_path)[0]
    runtime_source = provider_ref["provider_node_runtime_source"]
    package_names = tuple(
        item["package_name"] for item in runtime_source["ontology_targets"]
    )
    source_manifest_path = _service_protocol_runtime_source_manifest_path(
        provider_ref=provider_ref
    )
    requirements = (
        *_activation_projection_db_requirements(
            runtime_manifest_path=source_manifest_path,
        ),
        *_ontology_authority_db_requirements(
            source_kind=str(runtime_source["source_kind"]),
            package_names=package_names,
            runtime_manifest_path=source_manifest_path,
        ),
    )
    schema_hashes = tuple(requirement.db_schema_hash for requirement in requirements)
    sql_roots = _unique_requirement_sql_roots(requirements)
    db_schema_hash = _service_host_contract_db_schema_hash(
        requirements=requirements,
        schema_hashes=schema_hashes,
    )
    marker_scope_id = _service_host_contract_marker_scope_id(
        source_manifest_path=source_manifest_path,
        requirements=requirements,
        schema_hashes=schema_hashes,
    )
    registry_path = tmp_path / "ontology-authority-db.schema.registry.json"
    registry_payload = {
        "schema_registry_version": 1,
        "environment_id": str(marker_scope_id),
        "entries": [
            {
                "backend_targets": ["postgres"],
                "package_kind": "ontology",
                "source_label": requirement.package_name
                or ",".join(requirement.package_names),
                "source_hash": db_schema_hash,
                "sql_roots": list(requirement.sql_roots),
            }
            for requirement in requirements
        ],
    }
    registry_path.write_text(
        json.dumps(registry_payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    return OntologyDatabaseArtifactReceipt(
        environment_id=marker_scope_id,
        ontology_package_id=marker_scope_id,
        ontology_manifest_ref=OntologyDatabaseArtifactRef(
            path=source_manifest_path.as_posix(),
            hash=_sha256_ref(source_manifest_path),
        ),
        ocg_id=marker_scope_id,
        ocg_hash=db_schema_hash,
        db_schema_registry_ref=OntologyDatabaseArtifactRef(
            path=registry_path.as_posix(),
            hash=_sha256_ref(registry_path),
        ),
        db_schema_hash=db_schema_hash,
        db_backend_target="postgres",
        db_package_kind="ontology",
        sql_roots=[path.as_posix() for path in sql_roots],
    )


def _service_protocol_runtime_source_manifest_path(
    *,
    provider_ref: dict[str, object],
) -> Path:
    service_package_ref = provider_ref["service_package_ref"]
    if not isinstance(service_package_ref, dict):
        raise RuntimeError("Provider ref missing service_package_ref object.")
    dependencies = service_package_ref["dependencies"]
    if not isinstance(dependencies, list):
        raise RuntimeError(
            "Provider ref service_package_ref.dependencies must be a list."
        )
    expected_hashes = {
        item["expected_hash_sha256"]
        for item in dependencies
        if isinstance(item, dict)
        and item.get("package_name") == ONTOLOGY_API_PACKAGE_NAME
        and isinstance(item.get("expected_hash_sha256"), str)
    }
    if not expected_hashes:
        raise RuntimeError("Provider ref does not carry ontology-service-api hash.")
    candidates = sorted(
        (WORKSPACE_ROOT_PATH / ".aware/service/runtime").glob(
            "service-protocol-*/runtime.sources.json"
        )
    )
    for path in candidates:
        payload = json.loads(path.read_text(encoding="utf-8"))
        api_dependencies = payload.get("api_dependencies")
        if not isinstance(api_dependencies, list):
            continue
        for dependency in api_dependencies:
            if not isinstance(dependency, dict):
                continue
            if dependency.get("package_name") != ONTOLOGY_API_PACKAGE_NAME:
                continue
            if dependency.get("service_protocol_plan_hash_sha256") in expected_hashes:
                return path.resolve()
    raise RuntimeError("Could not resolve service-protocol runtime source manifest.")


def _activation_projection_db_requirements(
    *,
    runtime_manifest_path: Path,
) -> tuple[ServiceHostDbRequirement, ...]:
    package_names = _activation_projection_package_names()
    manifest_paths = ontology_authority_runtime_manifest_paths(
        package_names=package_names,
        authority_root=WORKSPACE_ROOT_PATH,
    )
    requirements: list[ServiceHostDbRequirement] = []
    for package_name, manifest_path in zip(package_names, manifest_paths, strict=True):
        requirements.append(
            ServiceHostDbRequirement(
                kind=ServiceHostDbRequirementKind.activation_projection,
                provider_key="aware-service-host",
                package_name=package_name,
                package_names=[package_name],
                role="service_activation_projection",
                requirement_mode="required",
                schema_scope="activation_projection",
                manifest_paths=[manifest_path.as_posix()],
                sql_roots=[
                    ontology_runtime_artifact_sql_root_from_manifest_path(
                        manifest_path
                    ).as_posix()
                ],
                db_schema_hash=ontology_runtime_manifest_db_schema_hash(manifest_path),
                authority=False,
                required=True,
                description=(
                    "ServiceHost-owned Service activation projection read model "
                    "for committed ServicePackage/ServiceConfig lanes."
                ),
                metadata={
                    "source": "service_host.activation_projection.semantic_contract",
                    "runtime_manifest_path": runtime_manifest_path.as_posix(),
                },
            )
        )
    return tuple(requirements)


def _activation_projection_package_names() -> tuple[str, ...]:
    package_names: list[str] = []
    for contract in (
        AWARE_CODE_SEMANTIC_CONTRACT,
        AWARE_API_SEMANTIC_CONTRACT,
        AWARE_SERVICE_SEMANTIC_CONTRACT,
    ):
        for descriptor in contract.materialization_runtime_for():
            for package_name in descriptor.runtime_ontology_package_names:
                normalized = str(package_name or "").strip()
                if normalized and normalized not in package_names:
                    package_names.append(normalized)
    if not package_names:
        raise RuntimeError("ServiceHost activation projection packages are empty.")
    return tuple(package_names)


def _ontology_authority_db_requirements(
    *,
    source_kind: str,
    package_names: tuple[str, ...],
    runtime_manifest_path: Path,
) -> tuple[ServiceHostDbRequirement, ...]:
    response = resolve_service_host_contracts_for_tomls(
        service_toml_paths=(ONTOLOGY_SERVICE_TOML_PATH,),
        target=ServiceHostContractTargetInput(
            backend="db",
            runtime_manifest_path=runtime_manifest_path,
            artifact_root=WORKSPACE_ROOT_PATH,
            authority_root=WORKSPACE_ROOT_PATH,
            ontology_authority_source_kind=source_kind,
            ontology_authority_package_names=package_names,
            implementation_toml_paths=(ONTOLOGY_SERVICE_TOML_PATH,),
        ),
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )
    if response.db_requirement_plan is None:
        return ()
    return tuple(
        requirement
        for requirement in response.db_requirement_plan.requirements
        if requirement.manifest_paths or requirement.sql_roots
    )


def _unique_requirement_sql_roots(
    requirements: tuple[ServiceHostDbRequirement, ...],
) -> tuple[Path, ...]:
    sql_roots: list[Path] = []
    for requirement in requirements:
        for raw_path in requirement.sql_roots:
            path = Path(raw_path).expanduser().resolve()
            if path not in sql_roots:
                sql_roots.append(path)
    return tuple(sql_roots)


def _service_host_contract_marker_scope_id(
    *,
    source_manifest_path: Path,
    requirements: tuple[ServiceHostDbRequirement, ...],
    schema_hashes: tuple[str, ...],
) -> UUID:
    payload_hash = _canonical_json_sha256(
        {
            "scope": "service_host_contract_db_marker",
            "source_manifest_path": source_manifest_path.as_posix(),
            "schema_hashes": list(dict.fromkeys(schema_hashes)),
            "requirements": [
                _service_host_contract_db_requirement_payload(requirement)
                for requirement in requirements
            ],
        }
    )
    return uuid5(NAMESPACE_URL, f"aware-service-host:db-marker:{payload_hash}")


def _service_host_contract_db_schema_hash(
    *,
    requirements: tuple[ServiceHostDbRequirement, ...],
    schema_hashes: tuple[str, ...],
) -> str:
    unique_hashes = tuple(dict.fromkeys(schema_hashes))
    if len(unique_hashes) == 1:
        return unique_hashes[0]
    return "sha256:" + _canonical_json_sha256(
        {
            "scope": "service_host_contract_db_requirements",
            "requirements": [
                _service_host_contract_db_requirement_payload(requirement)
                for requirement in requirements
            ],
        }
    )


def _service_host_contract_db_requirement_payload(
    requirement: ServiceHostDbRequirement,
) -> dict[str, object]:
    return {
        "kind": requirement.kind.value,
        "provider_key": requirement.provider_key,
        "package_name": requirement.package_name,
        "package_names": list(requirement.package_names),
        "manifest_paths": list(requirement.manifest_paths),
        "sql_roots": list(requirement.sql_roots),
        "db_schema_hash": requirement.db_schema_hash,
    }


def _canonical_json_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha256_ref(path: Path) -> str:
    return f"sha256:{_sha256(path)}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
