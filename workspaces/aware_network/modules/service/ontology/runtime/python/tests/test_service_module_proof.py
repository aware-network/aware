from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID
from uuid import uuid4

import pytest

from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
    run_multi_lane_meta_runtime_proof,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT

_SERVICE_CONFIG_ROOT_CLASS_FQN = "aware_service.service.ServiceConfig"
_SERVICE_CONTRACT_CONFIG_CLASS_FQN = "aware_service.service.ServiceContractConfig"
_SERVICE_CONFIG_API_CLASS_FQN = "aware_service.service.ServiceConfigApi"
_SERVICE_PACKAGE_CLASS_FQN = "aware_service.service.ServicePackage"
_SERVICE_CLASS_FQN = "aware_service.service.Service"
_SERVICE_OPERATION_CONFIG_CLASS_FQN = "aware_service.service.ServiceOperationConfig"
_SERVICE_OPERATION_CONFIG_API_ENDPOINT_CLASS_FQN = (
    "aware_service.service.ServiceOperationConfigApiEndpoint"
)
_SERVICE_OPERATION_CLASS_FQN = "aware_service.service.ServiceOperation"

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)
_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
)


def _service_module_proof_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_module_proof_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_module_proof_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _SERVICE_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
            _SERVICE_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    assert runtime.context is not None
    return runtime.context.index


def _class_instance_id_for_source(
    *, assertions, source_object_id: UUID
) -> UUID:  # noqa: ANN001 - test helper
    for class_instance in assertions.oig.class_instances:
        if (
            class_instance.source_object_id == source_object_id
            and class_instance.id is not None
        ):
            return class_instance.id
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


def _payload_id(payload: object) -> UUID:
    assert isinstance(payload, dict)
    return UUID(str(payload["id"]))


def _expect_uuid_primitive(
    assertions,  # noqa: ANN001 - test helper
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


async def _create_api_endpoint_function_contract(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: LaneIds,
    api_projection_hash: str,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> tuple[UUID, UUID, UUID, UUID]:
    branch_id = lane.branch_id or uuid4()
    endpoint_ref = f"{api_name}.{capability_name}.{endpoint_name}"
    request_class_config = _select_runtime_inline_request_class_config(index)
    api_snapshot = await commit_api_reference_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=api_projection_hash,
        api_name=api_name,
        endpoint_refs=(endpoint_ref,),
        endpoint_request_class_config_ids={
            endpoint_ref: request_class_config.id,
        },
        endpoint_fulfillment_names={endpoint_ref: (endpoint_name,)},
        api_graph_function_config_id=_select_runtime_function_config_id(index),
    )
    assert api_snapshot.api.id is not None
    endpoint_id = api_snapshot.endpoint_ids_by_ref[endpoint_ref]
    endpoint_function_id = api_snapshot.endpoint_function_ids_by_ref[endpoint_ref][
        endpoint_name
    ]

    return (
        api_snapshot.api.id,
        endpoint_id,
        endpoint_function_id,
        branch_id,
    )


def _select_runtime_inline_request_class_config(
    index: MetaGraphRuntimeIndex,
) -> ClassConfig:
    for class_config in sorted(
        index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    ):
        if class_config.value_mode == ClassValueMode.inline_value:
            return class_config
    raise AssertionError("Expected one inline_value ClassConfig for API proof seeding")


def _select_runtime_function_config_id(index: MetaGraphRuntimeIndex) -> UUID:
    for class_config in sorted(
        index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    ):
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            if function_link.function_config_id is not None:
                return function_link.function_config_id
    raise AssertionError("Expected one runtime ClassConfigFunctionConfig")


@pytest.mark.asyncio
async def test_service_config_projection_proves_config_service_and_operation_config(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401

    from aware_service_ontology.stable_ids import (
        stable_service_config_api_id,
        stable_service_config_experience_id,
        stable_service_config_id,
        stable_service_contract_config_id,
        stable_service_contract_config_operation_grant_id,
        stable_service_operation_config_id,
    )

    service_config_name = "compiler"
    operation_config_name = "compile_module"
    contract_config_name = "default"
    api_id = uuid4()
    projection_experience_id = uuid4()

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_operation_config_id = stable_service_operation_config_id(
        service_config_id=expected_service_config_id,
        name=operation_config_name,
    )
    expected_service_config_api_id = stable_service_config_api_id(
        service_config_id=expected_service_config_id,
        api_id=api_id,
    )
    expected_service_config_experience_id = stable_service_config_experience_id(
        service_config_id=expected_service_config_id,
        projection_experience_id=projection_experience_id,
    )
    expected_contract_config_id = stable_service_contract_config_id(
        service_config_id=expected_service_config_id,
        name=contract_config_name,
    )
    expected_operation_grant_id = stable_service_contract_config_operation_grant_id(
        service_contract_config_id=expected_contract_config_id,
        service_operation_config_id=expected_operation_config_id,
    )
    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        lane = LaneIds(
            actor_id=uuid4(),
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ServiceConfig",
            root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": service_config_name,
                        "description": "Compiler service catalog",
                    },
                    expected_root_object_id=expected_service_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="create_service_operation_config",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "name": operation_config_name,
                        "description": "Compile one module",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="create_api",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "api_id": api_id,
                        "description": "Shared API bridge",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="create_experience",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_id": projection_experience_id,
                        "description": "Shared Experience bridge",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="create_contract_config",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "name": contract_config_name,
                        "description": "Default commercial contract",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONTRACT_CONFIG_CLASS_FQN,
                    function_name="grant_operation",
                    object_id=SourceObjectId(expected_contract_config_id),
                    kwargs={
                        "service_operation_config_id": expected_operation_config_id,
                        "access_scope": "operation",
                        "description": "Compile operation access",
                    },
                ),
            ],
        )

        assert result.root_object_id == expected_service_config_id
        service_config_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_config_id,
        )
        operation_config_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_operation_config_id,
        )
        service_config_api_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_config_api_id,
        )
        service_config_experience_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_config_experience_id,
        )
        contract_config_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_contract_config_id,
        )
        operation_grant_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_operation_grant_id,
        )
        assertions.expect_root(service_config_ci_id)
        assertions.expect_instance(service_config_ci_id)
        assertions.expect_instance(operation_config_ci_id)
        assertions.expect_instance(service_config_api_ci_id)
        assertions.expect_instance(service_config_experience_ci_id)
        assertions.expect_instance(contract_config_ci_id)
        assertions.expect_instance(operation_grant_ci_id)
        assertions.expect_edge(
            source_id=service_config_ci_id,
            target_id=operation_config_ci_id,
            relationship_name="service_operation_configs",
        )
        assertions.expect_edge(
            source_id=service_config_ci_id,
            target_id=service_config_api_ci_id,
            relationship_name="apis",
        )
        assertions.expect_edge(
            source_id=service_config_ci_id,
            target_id=service_config_experience_ci_id,
            relationship_name="experiences",
        )
        assertions.expect_edge(
            source_id=service_config_ci_id,
            target_id=contract_config_ci_id,
            relationship_name="contract_configs",
        )
        assertions.expect_edge(
            source_id=contract_config_ci_id,
            target_id=operation_grant_ci_id,
            relationship_name="operation_grants",
        )
        assertions.expect_primitive(
            instance_id=service_config_ci_id,
            field_name="name",
            expected=service_config_name,
        )
        assertions.expect_primitive(
            instance_id=operation_config_ci_id,
            field_name="name",
            expected=operation_config_name,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=service_config_api_ci_id,
            field_name="api_id",
            expected=api_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=service_config_experience_ci_id,
            field_name="projection_experience_id",
            expected=projection_experience_id,
        )


@pytest.mark.asyncio
async def test_service_config_projection_proves_api_projection_binding(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401

    from aware_service_ontology.stable_ids import (
        stable_service_config_api_id,
        stable_service_config_api_projection_id,
        stable_service_config_id,
    )

    service_config_name = "compiler"
    api_id = uuid4()
    api_graph_projection_id = uuid4()

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_service_config_api_id = stable_service_config_api_id(
        service_config_id=expected_service_config_id,
        api_id=api_id,
    )
    expected_projection_id = stable_service_config_api_projection_id(
        service_config_api_id=expected_service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        lane = LaneIds(
            actor_id=uuid4(),
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ServiceConfig",
            root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": service_config_name,
                        "description": "Compiler service catalog",
                    },
                    expected_root_object_id=expected_service_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    function_name="create_api",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "api_id": api_id,
                        "description": "Shared API bridge",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_CONFIG_API_CLASS_FQN,
                    function_name="create_projection",
                    object_id=SourceObjectId(expected_service_config_api_id),
                    kwargs={
                        "api_graph_projection_id": api_graph_projection_id,
                        "description": "Expose one shared projection contract",
                    },
                ),
            ],
        )

        assert result.root_object_id == expected_service_config_id
        service_config_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_config_id,
        )
        service_config_api_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_config_api_id,
        )
        projection_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_projection_id,
        )

        assertions.expect_root(service_config_ci_id)
        assertions.expect_instance(service_config_api_ci_id)
        assertions.expect_instance(projection_ci_id)
        assertions.expect_edge(
            source_id=service_config_ci_id,
            target_id=service_config_api_ci_id,
            relationship_name="apis",
        )
        assertions.expect_edge(
            source_id=service_config_api_ci_id,
            target_id=projection_ci_id,
            relationship_name="api_projections",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=projection_ci_id,
            field_name="service_config_api_id",
            expected=expected_service_config_api_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=projection_ci_id,
            field_name="api_graph_projection_id",
            expected=api_graph_projection_id,
        )


@pytest.mark.asyncio
async def test_service_package_projection_proves_api_package_dependency_bridges(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401

    from aware_service_ontology.stable_ids import (
        stable_service_package_id,
        stable_service_package_required_api_package_id,
    )

    service_package_name = "aware-environment-service"
    service_config_id = uuid4()
    required_api_package_id = uuid4()

    expected_service_package_id = stable_service_package_id(name=service_package_name)
    expected_required_bridge_id = stable_service_package_required_api_package_id(
        service_package_id=expected_service_package_id,
        api_package_id=required_api_package_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        lane = LaneIds(
            actor_id=uuid4(),
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ServicePackage",
            root_class_fqn=_SERVICE_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SERVICE_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": service_package_name,
                        "service_config_id": service_config_id,
                    },
                    expected_root_object_id=expected_service_package_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SERVICE_PACKAGE_CLASS_FQN,
                    function_name="attach_required_api_package",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "api_package_id": required_api_package_id,
                        "description": "Meta service API dependency",
                    },
                ),
            ],
        )

        assert result.root_object_id == expected_service_package_id
        service_package_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_service_package_id,
        )
        required_bridge_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=expected_required_bridge_id,
        )

        assertions.expect_root(service_package_ci_id)
        assertions.expect_instance(required_bridge_ci_id)
        assertions.expect_edge(
            source_id=service_package_ci_id,
            target_id=required_bridge_ci_id,
            relationship_name="required_api_packages",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=required_bridge_ci_id,
            field_name="api_package_id",
            expected=required_api_package_id,
        )


@pytest.mark.asyncio
async def test_service_projection_proves_operation_receipt_and_status_mutation(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401

    from aware_service_ontology.service.service_enums import ServiceOperationStatus
    from aware_service_ontology.stable_ids import (
        stable_service_config_api_id,
        stable_service_config_id,
        stable_service_id,
        stable_service_operation_config_id,
        stable_service_operation_config_api_endpoint_id,
        stable_service_operation_config_api_endpoint_function_id,
        stable_service_operation_id,
    )

    service_config_name = "compiler"
    service_name = "workspace_compiler"
    operation_config_name = "compile_module"
    operation_key = "turn-001"
    api_name = "service-module-proof-api"
    capability_name = "compiler"
    endpoint_name = "compile"

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_service_id = stable_service_id(
        service_config_id=expected_service_config_id,
        name=service_name,
    )
    expected_operation_config_id = stable_service_operation_config_id(
        service_config_id=expected_service_config_id,
        name=operation_config_name,
    )
    expected_operation_id = stable_service_operation_id(
        service_id=expected_service_id,
        service_operation_config_id=expected_operation_config_id,
        operation_key=operation_key,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        idx = _runtime_index(runtime)
        branch_id = uuid4()
        lane = LaneIds(
            branch_id=branch_id,
            actor_id=uuid4(),
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="Api",
        )
        (
            api_id,
            api_capability_endpoint_id,
            api_capability_endpoint_function_id,
            branch_id,
        ) = await _create_api_endpoint_function_contract(
            index=idx,
            actor_id=lane.actor_id,
            lane=lane,
            api_projection_hash=api_projection_hash,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        lane = LaneIds(
            actor_id=lane.actor_id,
            branch_id=branch_id,
        )
        expected_service_config_api_id = stable_service_config_api_id(
            service_config_id=expected_service_config_id,
            api_id=api_id,
        )
        expected_service_operation_config_api_endpoint_id = (
            stable_service_operation_config_api_endpoint_id(
                service_operation_config_id=expected_operation_config_id,
                service_config_api_id=expected_service_config_api_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
            )
        )
        expected_service_operation_config_api_endpoint_function_id = stable_service_operation_config_api_endpoint_function_id(
            service_operation_config_api_endpoint_id=expected_service_operation_config_api_endpoint_id,
            api_capability_endpoint_function_id=api_capability_endpoint_function_id,
        )
        results_by_opg, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "name": service_config_name,
                            "description": "Compiler service catalog",
                        },
                        expected_root_object_id=expected_service_config_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                        function_name="create_service_operation_config",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "name": operation_config_name,
                            "description": "Compile one module",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                        function_name="create_api",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "api_id": api_id,
                            "description": "Shared API bridge",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_OPERATION_CONFIG_CLASS_FQN,
                        function_name="create_api_endpoint",
                        object_id=SourceObjectId(expected_operation_config_id),
                        kwargs={
                            "service_config_api_id": expected_service_config_api_id,
                            "api_capability_endpoint_id": api_capability_endpoint_id,
                            "description": "Compile endpoint binding",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_OPERATION_CONFIG_API_ENDPOINT_CLASS_FQN,
                        function_name="create_function",
                        object_id=SourceObjectId(
                            expected_service_operation_config_api_endpoint_id
                        ),
                        kwargs={
                            "api_capability_endpoint_function_id": api_capability_endpoint_function_id,
                            "description": "Allowed compile action",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Service",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_SERVICE_CLASS_FQN,
                        function_name="build_via_service_config",
                        kwargs={
                            "service_config_id": expected_service_config_id,
                            "name": service_name,
                            "description": "Primary workspace compiler service",
                        },
                        expected_root_object_id=expected_service_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Service",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CLASS_FQN,
                        function_name="create_operation",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "service_operation_config_id": expected_operation_config_id,
                            "api_endpoint_id": expected_service_operation_config_api_endpoint_id,
                            "operation_key": operation_key,
                            "status": ServiceOperationStatus.queued.value,
                            "result_info": None,
                            "execution_context": {
                                "source": "module-proof",
                                "attempt": 1,
                            },
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Service",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_OPERATION_CLASS_FQN,
                        function_name="set_status",
                        object_id=SourceObjectId(expected_operation_id),
                        kwargs={
                            "status": ServiceOperationStatus.succeeded.value,
                            "result_info": "completed",
                        },
                    ),
                ),
            ],
        )
        service_config_result = results_by_opg["ServiceConfig"]
        service_config_assertions = assertions_by_opg["ServiceConfig"]
        assert service_config_result.root_object_id == expected_service_config_id
        operation_config_ci_id = _class_instance_id_for_source(
            assertions=service_config_assertions,
            source_object_id=expected_operation_config_id,
        )
        api_endpoint_ci_id = _class_instance_id_for_source(
            assertions=service_config_assertions,
            source_object_id=expected_service_operation_config_api_endpoint_id,
        )
        api_endpoint_function_ci_id = _class_instance_id_for_source(
            assertions=service_config_assertions,
            source_object_id=expected_service_operation_config_api_endpoint_function_id,
        )
        service_result = results_by_opg["Service"]
        service_assertions = assertions_by_opg["Service"]
        assert service_result.root_object_id == expected_service_id
        service_ci_id = _class_instance_id_for_source(
            assertions=service_assertions,
            source_object_id=expected_service_id,
        )
        operation_ci_id = _class_instance_id_for_source(
            assertions=service_assertions,
            source_object_id=expected_operation_id,
        )

        service_config_assertions.expect_root(
            _class_instance_id_for_source(
                assertions=service_config_assertions,
                source_object_id=expected_service_config_id,
            )
        )
        service_config_assertions.expect_instance(operation_config_ci_id)
        service_config_assertions.expect_instance(api_endpoint_ci_id)
        service_config_assertions.expect_instance(api_endpoint_function_ci_id)
        service_config_assertions.expect_edge(
            source_id=operation_config_ci_id,
            target_id=api_endpoint_ci_id,
            relationship_name="api_endpoints",
        )
        service_config_assertions.expect_edge(
            source_id=api_endpoint_ci_id,
            target_id=api_endpoint_function_ci_id,
            relationship_name="endpoint_functions",
        )
        service_assertions.expect_root(service_ci_id)
        service_assertions.expect_instance(service_ci_id)
        service_assertions.expect_instance(operation_ci_id)
        service_assertions.expect_edge(
            source_id=service_ci_id,
            target_id=operation_ci_id,
            relationship_name="service_operations",
        )
        service_assertions.expect_primitive(
            instance_id=service_ci_id,
            field_name="name",
            expected=service_name,
        )
        _expect_uuid_primitive(
            service_config_assertions,
            instance_id=api_endpoint_function_ci_id,
            field_name="api_capability_endpoint_function_id",
            expected=api_capability_endpoint_function_id,
        )
        service_assertions.expect_primitive(
            instance_id=operation_ci_id,
            field_name="operation_key",
            expected=operation_key,
        )
        _expect_uuid_primitive(
            service_assertions,
            instance_id=operation_ci_id,
            field_name="service_operation_config_id",
            expected=expected_operation_config_id,
        )
        service_assertions.expect_primitive(
            instance_id=operation_ci_id,
            field_name="status",
            expected=ServiceOperationStatus.succeeded.value,
        )
        service_assertions.expect_primitive(
            instance_id=operation_ci_id,
            field_name="result_info",
            expected="completed",
        )


@pytest.mark.asyncio
async def test_service_projection_proves_branch_binding(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401

    from aware_service_ontology.stable_ids import (
        stable_service_branch_id,
        stable_service_config_api_id,
        stable_service_config_api_projection_id,
        stable_service_config_id,
        stable_service_id,
    )

    service_config_name = "compiler"
    service_name = "workspace_compiler"
    api_id = uuid4()
    api_graph_projection_id = uuid4()
    object_instance_graph_branch_id = uuid4()

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_service_config_api_id = stable_service_config_api_id(
        service_config_id=expected_service_config_id,
        api_id=api_id,
    )
    expected_service_config_api_projection_id = stable_service_config_api_projection_id(
        service_config_api_id=expected_service_config_api_id,
        api_graph_projection_id=api_graph_projection_id,
    )
    expected_service_id = stable_service_id(
        service_config_id=expected_service_config_id,
        name=service_name,
    )
    expected_service_branch_id = stable_service_branch_id(
        service_id=expected_service_id,
        service_config_api_projection_id=expected_service_config_api_projection_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        lane = LaneIds(
            actor_id=uuid4(),
        )
        results_by_opg, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "name": service_config_name,
                            "description": "Compiler service catalog",
                        },
                        expected_root_object_id=expected_service_config_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                        function_name="create_api",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "api_id": api_id,
                            "description": "Shared API bridge",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ServiceConfig",
                    root_class_fqn=_SERVICE_CONFIG_ROOT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CONFIG_API_CLASS_FQN,
                        function_name="create_projection",
                        object_id=SourceObjectId(expected_service_config_api_id),
                        kwargs={
                            "api_graph_projection_id": api_graph_projection_id,
                            "description": "Expose one shared projection contract",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Service",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_SERVICE_CLASS_FQN,
                        function_name="build_via_service_config",
                        kwargs={
                            "service_config_id": expected_service_config_id,
                            "name": service_name,
                            "description": "Primary workspace compiler service",
                        },
                        expected_root_object_id=expected_service_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Service",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SERVICE_CLASS_FQN,
                        function_name="create_branch",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "service_config_api_projection_id": expected_service_config_api_projection_id,
                            "object_instance_graph_branch_id": object_instance_graph_branch_id,
                            "description": "Subscribe this service to the shared branch lane",
                        },
                    ),
                ),
            ],
        )

        service_config_result = results_by_opg["ServiceConfig"]
        service_result = results_by_opg["Service"]
        service_config_assertions = assertions_by_opg["ServiceConfig"]
        service_assertions = assertions_by_opg["Service"]

        assert service_config_result.root_object_id == expected_service_config_id
        assert service_result.root_object_id == expected_service_id

        service_config_api_ci_id = _class_instance_id_for_source(
            assertions=service_config_assertions,
            source_object_id=expected_service_config_api_id,
        )
        projection_ci_id = _class_instance_id_for_source(
            assertions=service_config_assertions,
            source_object_id=expected_service_config_api_projection_id,
        )
        service_ci_id = _class_instance_id_for_source(
            assertions=service_assertions,
            source_object_id=expected_service_id,
        )
        branch_ci_id = _class_instance_id_for_source(
            assertions=service_assertions,
            source_object_id=expected_service_branch_id,
        )

        service_config_assertions.expect_instance(service_config_api_ci_id)
        service_config_assertions.expect_instance(projection_ci_id)
        service_config_assertions.expect_edge(
            source_id=service_config_api_ci_id,
            target_id=projection_ci_id,
            relationship_name="api_projections",
        )
        service_assertions.expect_root(service_ci_id)
        service_assertions.expect_instance(branch_ci_id)
        service_assertions.expect_edge(
            source_id=service_ci_id,
            target_id=branch_ci_id,
            relationship_name="branches",
        )
        _expect_uuid_primitive(
            service_assertions,
            instance_id=branch_ci_id,
            field_name="service_config_api_projection_id",
            expected=expected_service_config_api_projection_id,
        )
        _expect_uuid_primitive(
            service_assertions,
            instance_id=branch_ci_id,
            field_name="object_instance_graph_branch_id",
            expected=object_instance_graph_branch_id,
        )
