from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import (
    meta_handlers as api_meta_handlers,
)
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
from aware_code.types import JsonObject
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_history.stable_ids import stable_branch_id
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
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
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_orm.session.session import Session
from aware_service_ontology.service.service_enums import (
    ServiceOperationFulfillmentKind,
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
    stable_service_config_id,
    stable_service_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_api_endpoint_function_id,
    stable_service_operation_config_id,
    stable_service_operation_id,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from aware_service_runtime.api_ingress import resolve_service_api_dispatch
from aware_service_runtime.api_ingress.execution import (
    _resolve_api_call_outcome_response_class_config,
    execute_service_api_dispatch_plan,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomyFinalizationInput,
    ServiceOperationEconomyReservationInput,
)
from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationMeteringContextV1,
    ServiceOperationSettlementFinalization,
    ServiceOperationSettlementPreparation,
)
from aware_service_runtime.materialization.service import (
    _resolve_canonical_service_config_projection_hash,
    _resolve_canonical_service_projection_hash,
)
from aware_service_runtime.ontology.materialization import (
    materialize_service,
    materialize_service_config,
    materialize_service_config_api,
    materialize_service_operation,
    materialize_service_operation_config,
    materialize_service_operation_config_api_endpoint,
)
from _service_runtime_test_paths import REPO_ROOT
from pydantic import BaseModel, create_model

from aware_api_runtime.invocation import (
    ResolvedApiInvocationEnvelope,
    ResolvedApiInvocationFulfillmentBinding,
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityEndpointResponseConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import materialize_api_call
from aware_api_runtime.service_protocol import (
    decode_inline_value_instance_to_mapping_strict,
)
from aware_api_runtime.service_protocol import (
    ApiServiceDispatchFulfillmentBinding,
    ApiServiceDispatchPlan,
)
from aware_api_runtime.service_protocol.runtime import ApiServiceProtocolInvoker

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


@dataclass(frozen=True, slots=True)
class _MetaLaneIds:
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    branch_id: UUID
    actor_id: UUID | None = None


def _service_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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


def _build_service_meta_runtime(
    repo_root: Path,
    *,
    workspace_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=workspace_root,
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


def _authored_class_ref_from_class_fqn(class_fqn: str) -> str:
    parts = [part.strip() for part in class_fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return class_fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


def _payload_id(payload: object) -> UUID:
    if hasattr(payload, "id"):
        return UUID(str(getattr(payload, "id")))
    assert isinstance(payload, dict)
    if "id" in payload:
        return UUID(str(payload["id"]))
    value = payload.get("value")
    if hasattr(value, "id"):
        return UUID(str(getattr(value, "id")))
    assert isinstance(value, dict)
    return UUID(str(value["id"]))


def _sample_value_for_primitive(base_type: CodePrimitiveBaseType) -> object | None:
    if base_type == CodePrimitiveBaseType.string:
        return "front-door"
    if base_type == CodePrimitiveBaseType.boolean:
        return True
    if base_type == CodePrimitiveBaseType.integer:
        return 7
    if base_type == CodePrimitiveBaseType.float:
        return 1.5
    if base_type == CodePrimitiveBaseType.uuid:
        return UUID("12345678-1234-5678-9234-567812345678")
    return None


def _type_hint_for_value(value: object) -> object:
    if isinstance(value, bool):
        return bool
    if isinstance(value, str):
        return str
    if isinstance(value, int):
        return int
    if isinstance(value, float):
        return float
    if isinstance(value, UUID):
        return UUID
    raise AssertionError(f"Unsupported proof value type: {type(value)!r}")


@pytest.mark.asyncio
async def test_service_operation_db_receipt_catches_up_committed_lane_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.ontology.materialization.service_operation as operation_mod

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-projection",
    )
    calls: list[dict[str, object]] = []

    async def _fake_ensure_projection_readiness(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return SimpleNamespace(
            status="ready",
            skipped_reason=None,
            commits_applied=2,
            head_commit_id=uuid4(),
        )

    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "db")
    monkeypatch.setattr(
        operation_mod,
        "ensure_projection_readiness",
        _fake_ensure_projection_readiness,
    )

    result = await operation_mod._ensure_target_lane_projected_for_db_receipt(
        index=cast(MetaGraphRuntimeIndex, SimpleNamespace()),
        target_lane=lane,
        commit=True,
        receipt_kind="service_operation",
    )

    assert result is not None
    assert result.status == "ready"
    assert len(calls) == 1
    requirement = calls[0]["requirement"]
    assert requirement.name == "service_operation.read_model_receipt"
    assert requirement.branch_id == lane.branch_id
    assert requirement.projection_hash == lane.projection_hash
    assert requirement.mode == "required_db"


@pytest.mark.asyncio
async def test_service_operation_projection_catchup_skips_without_explicit_db_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.ontology.materialization.service_operation as operation_mod

    calls: list[dict[str, object]] = []

    async def _fake_ensure_projection_readiness(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return SimpleNamespace(
            status="skipped", skipped_reason="mode:off", commits_applied=0
        )

    monkeypatch.delenv("AWARE_PERSISTENCE_BACKEND", raising=False)
    monkeypatch.setattr(
        operation_mod,
        "ensure_projection_readiness",
        _fake_ensure_projection_readiness,
    )

    result = await operation_mod._ensure_target_lane_projected_for_db_receipt(
        index=cast(MetaGraphRuntimeIndex, SimpleNamespace()),
        target_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="service-projection",
        ),
        commit=True,
        receipt_kind="service_operation",
    )

    assert result is not None
    assert result.status == "skipped"
    assert calls[0]["index"] is None
    assert calls[0]["requirement"].mode == "off"


@pytest.mark.asyncio
async def test_materialize_service_operation_config_fulfillment_kinds_from_committed_truth(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    service_config_name = "fulfillment_kind_service"
    expected_service_config_id = stable_service_config_id(name=service_config_name)
    operation_specs = {
        "read_calendar": ServiceOperationFulfillmentKind.view,
        "sync_calendar": ServiceOperationFulfillmentKind.coordination,
        "open_door": ServiceOperationFulfillmentKind.actuation,
    }

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_operation_fulfillment_kind",
    ) as aware_root:
        runtime = _build_service_meta_runtime(repo_root, workspace_root=aware_root)
        runtime_index = _runtime_index(runtime)
        environment_id = uuid4()
        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id,
        )
        lane = _MetaLaneIds(
            environment_id=environment_id,
            process_id=boot_process_id,
            thread_id=boot_thread_id,
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        service_config_lane = MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=_resolve_canonical_service_config_projection_hash(
                runtime_index,
            ),
        )

        materialized_service_config = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
            description="Fulfillment kind proof service catalog",
        )
        assert (
            materialized_service_config.binding.service_config_id
            == expected_service_config_id
        )

        expected_operation_ids: dict[UUID, ServiceOperationFulfillmentKind] = {}
        for operation_name, fulfillment_kind in operation_specs.items():
            result = await materialize_service_operation_config(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_config_id=expected_service_config_id,
                name=operation_name,
                description=f"{operation_name} fulfillment kind proof",
                fulfillment_kind=fulfillment_kind.value,
            )
            expected_operation_id = stable_service_operation_config_id(
                service_config_id=expected_service_config_id,
                name=operation_name,
            )
            assert result.binding.service_operation_config_id == expected_operation_id
            assert result.service_operation_config.fulfillment_kind is fulfillment_kind
            expected_operation_ids[expected_operation_id] = fulfillment_kind

        scratch = await _hydrate_committed_session(
            index=runtime_index,
            branch_id=lane.branch_id,
            projection_hash=service_config_lane.projection_hash,
        )

    for operation_id, expected_kind in expected_operation_ids.items():
        operation_config = scratch.imap_get(ServiceOperationConfig, operation_id)
        assert operation_config is not None
        assert operation_config.fulfillment_kind is expected_kind


class _RecordingSettlementCoordinator:
    def __init__(self) -> None:
        self.metering_coin_id = uuid4()
        self.metering_context_preparations: list[
            ServiceOperationSettlementPreparation
        ] = []
        self.preparations: list[ServiceOperationSettlementPreparation] = []
        self.finalizations: list[
            tuple[ServiceOperationSettlementFinalization, object | None]
        ] = []

    async def resolve_metering_context(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> ServiceOperationMeteringContextV1:
        assert session.branch_id is not None
        self.metering_context_preparations.append(preparation)
        return ServiceOperationMeteringContextV1(
            schema="aware.service.operation_metering_context.v1",
            cost_basis_coin_id=self.metering_coin_id,
        )

    async def before_execute(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> object | None:
        assert session.branch_id is not None
        self.preparations.append(preparation)
        return {"reservation_state": "prepared"}

    async def after_execute(
        self,
        *,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationSettlementFinalization,
    ) -> None:
        assert session.branch_id is not None
        self.finalizations.append((finalization, prepared_state))


def test_api_call_outcome_response_class_config_resolves_registered_dto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.api_ingress.execution as execution_mod

    response_class_config_id = uuid4()
    response_class_config = ClassConfig(
        id=response_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeResponse",
        name="WorkspaceMaterializeResponse",
        value_mode=ClassValueMode.inline_value,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 1

    monkeypatch.setattr(
        execution_mod, "register_pydantic_package_class_configs", _register_package
    )
    monkeypatch.setattr(
        execution_mod,
        "iter_registered_class_config_payloads",
        lambda: (
            SimpleNamespace(
                source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
                payload=response_class_config.model_dump(mode="json"),
            ),
        ),
    )

    resolved = _resolve_api_call_outcome_response_class_config(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        response_type_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeResponse",
    )

    assert registered_packages == ["aware_workspace_service_dto"]
    assert resolved == response_class_config


class _RecordingEconomySettlementAdapter:
    def __init__(self) -> None:
        self.reservations: list[ServiceOperationEconomyReservationInput] = []
        self.finalizations: list[
            tuple[ServiceOperationEconomyFinalizationInput, object | None]
        ] = []

    async def reserve(
        self,
        *,
        runtime: object,
        index: MetaGraphRuntimeIndex,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
        commit: bool,
        publish: bool,
    ) -> object | None:
        _ = runtime, index, commit, publish
        assert session.branch_id is not None
        self.reservations.append(reservation)
        return {"economy_state": "prepared"}

    async def finalize(
        self,
        *,
        runtime: object,
        index: MetaGraphRuntimeIndex,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationEconomyFinalizationInput,
        commit: bool,
        publish: bool,
    ) -> None:
        _ = runtime, index, commit, publish
        assert session.branch_id is not None
        self.finalizations.append((finalization, prepared_state))


def _create_required_model(
    *,
    model_name: str,
    field_name: str,
    field_value: object,
) -> type[BaseModel]:
    return cast(
        type[BaseModel],
        create_model(
            model_name,
            **cast(Any, {field_name: (_type_hint_for_value(field_value), ...)}),
        ),
    )


def _select_runtime_inline_contract(
    runtime_index: MetaGraphRuntimeIndex,
    *,
    preferred_base_types: tuple[CodePrimitiveBaseType, ...],
) -> tuple[ClassConfig, str, object]:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    candidates: list[tuple[CodePrimitiveBaseType, ClassConfig, str, object]] = []
    for class_config in class_configs:
        if class_config.value_mode != ClassValueMode.inline_value:
            continue
        attribute_links = [
            link
            for link in sorted(
                class_config.class_config_attribute_configs,
                key=lambda item: item.position,
            )
            if link.attribute_config is not None
            and not link.attribute_config.is_virtual
        ]
        if len(attribute_links) != 1:
            continue
        attribute_config = attribute_links[0].attribute_config
        if attribute_config is None or not attribute_config.name:
            continue
        type_info = resolve_type_info(attribute_config)
        if (
            type_info.kind.value != "primitive"
            or type_info.is_collection
            or type_info.primitive_config is None
        ):
            continue
        primitive_type = CodePrimitiveType.model_validate(
            type_info.primitive_config.primitive_type
        )
        sample_value = _sample_value_for_primitive(primitive_type.base_type)
        if sample_value is None:
            continue
        candidates.append(
            (
                primitive_type.base_type,
                class_config,
                attribute_config.name,
                sample_value,
            )
        )

    for preferred_base_type in preferred_base_types:
        for base_type, class_config, attribute_name, sample_value in candidates:
            if base_type == preferred_base_type:
                return class_config, attribute_name, sample_value

    if not candidates:
        raise AssertionError(
            "Expected one compiled inline_value ClassConfig with a single supported primitive attribute"
        )
    _base_type, class_config, attribute_name, sample_value = candidates[0]
    return class_config, attribute_name, sample_value


def _select_runtime_function_config_id(runtime_index: MetaGraphRuntimeIndex) -> UUID:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            if function_link.function_config_id is not None:
                return function_link.function_config_id
    raise AssertionError(
        "Expected one runtime ClassConfigFunctionConfig for API graph materialization proof"
    )


def _api_ownership_for_runtime(
    *,
    request_class_ref: str,
    response_class_ref: str,
) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="openai-api",
            source_path="runtime-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="door",
                    source_path="runtime-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open",
                            source_path="runtime-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="runtime-proof",
                                response_config=APICapabilityEndpointResponseConfigOwnership(
                                    class_ref=response_class_ref,
                                    source_path="runtime-proof",
                                ),
                            ),
                            functions=(
                                APICapabilityEndpointFunctionOwnership(
                                    name="open",
                                    graph_target="aware_home",
                                    graph_capability_function_name="open",
                                    source_path="runtime-proof",
                                ),
                            ),
                            description="Open the API proof door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


def _seed_boot_environment(
    *,
    environment_id: UUID,
) -> tuple[UUID, UUID, UUID]:
    process_id = uuid4()
    thread_id = uuid4()
    boot_branch_id = stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    return process_id, thread_id, boot_branch_id


async def _hydrate_committed_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> Session:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert target_head is not None
    assert target_head.get("commit_id") is not None
    opg = index.opg_by_hash[projection_hash]
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=branch_id,
    )


def _dispatch_plan(
    *,
    envelope: ResolvedApiInvocationEnvelope,
    request_object: BaseModel,
    invoke: ApiServiceProtocolInvoker,
    fulfillment_name: str,
    response_type_ref: str | None,
) -> ApiServiceDispatchPlan:
    fulfillment_binding = envelope.fulfillment_bindings[0]
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root="aware_proof_api",
        service_protocol_import_root="aware_proof_protocol",
        endpoint_ref=envelope.endpoint_ref,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        request_type_ref=f"aware_proof_api.models.{request_object.__class__.__name__}",
        response_type_ref=response_type_ref,
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(
            ApiServiceDispatchFulfillmentBinding(
                name=fulfillment_binding.name,
                graph_target=fulfillment_binding.graph_target,
                graph_capability_function_name=fulfillment_binding.graph_capability_function_name,
                graph_function_python_ref="aware_home.home.Door.open",
                graph_function_runtime_target="aware_home_ontology.home.home.Door.open",
                call_target_kind="instance",
                exact_output_field_name=None,
                method_name=fulfillment_name,
                request_type_ref="aware_proof_protocol.protocols.OpenExecutionRequest",
                response_type_ref="aware_proof_protocol.protocols.OpenExecutionResponse",
                source_path="service-runtime-proof",
                api_capability_endpoint_function_id=fulfillment_binding.api_capability_endpoint_function_id,
            ),
        ),
        request_object=request_object,
        invoke=invoke,
    )


def _fake_envelope(
    *,
    branch_id: UUID,
    projection_hash: str,
    api_call_id: UUID,
    api_capability_endpoint_id: UUID,
    request_hash: str,
    request_model_id: UUID,
    request_class_config_id: UUID,
    fulfillment_name: str,
) -> ResolvedApiInvocationEnvelope:
    return ResolvedApiInvocationEnvelope(
        api_call_id=api_call_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=uuid4(),
        request_hash=request_hash,
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=branch_id,
        projection_hash=projection_hash,
        api_name="openai",
        capability_name="door",
        endpoint_name="open",
        endpoint_ref="openai.door.open",
        discriminant="openai.door.open",
        source_path="service-runtime-proof",
        request_model_id=request_model_id,
        request_class_config_id=request_class_config_id,
        request_class_ref="aware_proof_types.door.OpenRequest",
        request_source_path="service-runtime-proof",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(
            ResolvedApiInvocationFulfillmentBinding(
                name=fulfillment_name,
                graph_target="aware_home",
                graph_capability_function_name=fulfillment_name,
                source_path="service-runtime-proof",
            ),
        ),
        description="Service materialization proof",
    )


async def _invoke_open_factory(
    response_model_cls: type[BaseModel], response_payload: dict[str, Any]
) -> object:
    return response_model_cls.model_validate(response_payload)


@pytest.mark.asyncio
async def test_materialize_service_operation_from_api_dispatch_plan(
    tmp_path: Path,
) -> None:
    from aware_service_runtime.api_ingress.telemetry import (
        collect_service_api_trace_timings,
    )

    repo_root = REPO_ROOT
    service_config_name = "compiler"
    service_name = "workspace_compiler"
    operation_config_name = "compile_module"
    operation_key = "turn-001"
    api_id = uuid4()
    api_call_id = uuid4()
    api_capability_endpoint_id = uuid4()

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_service_id = stable_service_id(
        service_config_id=expected_service_config_id,
        name=service_name,
    )
    expected_operation_config_id = stable_service_operation_config_id(
        service_config_id=expected_service_config_id,
        name=operation_config_name,
    )
    expected_service_config_api_id = stable_service_config_api_id(
        service_config_id=expected_service_config_id,
        api_id=api_id,
    )
    expected_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
        service_operation_config_id=expected_operation_config_id,
        service_config_api_id=expected_service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    expected_service_operation_id = stable_service_operation_id(
        service_id=expected_service_id,
        service_operation_config_id=expected_operation_config_id,
        operation_key=operation_key,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_operation_materialization",
    ) as aware_root:
        runtime = _build_service_meta_runtime(repo_root, workspace_root=aware_root)
        runtime_index = _runtime_index(runtime)
        environment_id = uuid4()
        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id,
        )
        lane = _MetaLaneIds(
            environment_id=environment_id,
            process_id=boot_process_id,
            thread_id=boot_thread_id,
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(runtime_index)
        )
        service_projection_hash = _resolve_canonical_service_projection_hash(
            runtime_index
        )
        active_branch_id = lane.branch_id
        assert active_branch_id is not None
        service_config_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_projection_hash,
        )

        materialized_service_config = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
            description="Compiler service catalog",
        )
        assert (
            materialized_service_config.binding.service_config_id
            == expected_service_config_id
        )

        materialized_service_config_api = await materialize_service_config_api(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            api_id=api_id,
            description="Shared API bridge",
        )
        assert (
            materialized_service_config_api.binding.service_config_api_id
            == expected_service_config_api_id
        )

        materialized_operation_config = await materialize_service_operation_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            name=operation_config_name,
            description="Compile one module",
        )
        assert (
            materialized_operation_config.binding.service_operation_config_id
            == expected_operation_config_id
        )

        materialized_api_endpoint = (
            await materialize_service_operation_config_api_endpoint(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_operation_config_id=expected_operation_config_id,
                service_config_api_id=expected_service_config_api_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                description="Public endpoint binding",
            )
        )
        assert (
            materialized_api_endpoint.binding.service_operation_config_api_endpoint_id
            == expected_api_endpoint_id
        )

        materialized_service = await materialize_service(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_lane,
            service_config_id=expected_service_config_id,
            name=service_name,
            description="Primary compiler service instance",
        )
        assert materialized_service.binding.service_id == expected_service_id

        scratch = await _hydrate_committed_session(
            index=runtime_index,
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )

        envelope = _fake_envelope(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
            api_call_id=api_call_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            request_hash="sha256:service-runtime-proof",
            request_model_id=uuid4(),
            request_class_config_id=uuid4(),
            fulfillment_name="open",
        )

        async def _noop_invoke(*_: object) -> object | None:
            return None

        dispatch_plan = _dispatch_plan(
            envelope=envelope,
            request_object=create_model("FakeRequest", label=(str, ...))(
                label="front-door"
            ),
            invoke=_noop_invoke,
            fulfillment_name="open",
            response_type_ref=None,
        )
        resolved_dispatch = resolve_service_api_dispatch(
            session=scratch,
            dispatch_plan=dispatch_plan,
        )

        with collect_service_api_trace_timings() as timings:
            materialized = await materialize_service_operation(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_lane,
                resolved_dispatch=resolved_dispatch,
                service_id=expected_service_id,
                operation_key=operation_key,
                execution_context=cast(JsonObject, {"source": "service-api-dispatch"}),
                service_config_session=scratch,
            )

        assert (
            materialized.binding.service_operation_id == expected_service_operation_id
        )
        assert "service_operation.materialize.resolve_candidate_s" in timings
        assert "service_operation.materialize.hydrate_service_root_s" in timings
        assert "service_lane_hydration.head_lookup_s" in timings
        assert "service_lane_hydration.resolve_projection_s" in timings
        assert "service_lane_hydration.materializer_get_s" in timings
        assert "service_lane_hydration.reify_root_s" in timings
        assert "service_operation.materialize.ensure_projection_readiness_s" in timings
        assert "service_operation.materialize.commit_snapshot_s" in timings
        assert "service_snapshot.commit.resolve_projection_identity_s" in timings
        assert "service_snapshot.commit.load_before_oig_s" in timings
        assert "service_snapshot.load_before_oig.head_lookup_s" in timings
        assert "service_snapshot.load_before_oig.materializer_get_s" in timings
        assert "service_snapshot.commit.build_change_set_s" in timings
        assert "service_snapshot.commit.build_changes_s" in timings
        assert "service_snapshot.commit.materialize_post_oig_s" in timings
        assert "service_snapshot.commit.build_commit_id_s" in timings
        assert "service_snapshot.commit.append_lane_commit_s" in timings
        assert "service_snapshot.commit.build_result_s" in timings
        assert (
            "service_operation.materialize.hydrate_materialized_operation_s" in timings
        )
        assert "service_operation.materialize.build_result_s" in timings
        assert (
            materialized.binding.service_operation_config_id
            == expected_operation_config_id
        )
        assert materialized.binding.service_id == expected_service_id
        assert materialized.binding.api_call_id == api_call_id
        assert materialized.binding.api_endpoint_id == expected_api_endpoint_id
        assert materialized.binding.operation_key == operation_key
        assert materialized.binding.commit_id is not None
        assert materialized.binding.head_commit_id is not None
        assert materialized.service_operation.id == expected_service_operation_id
        assert materialized.service_operation.service_id == expected_service_id
        assert (
            materialized.service_operation.service_operation_config_id
            == expected_operation_config_id
        )
        assert materialized.service_operation.api_call_id == api_call_id
        assert materialized.service_operation.service_operation_config is not None
        assert (
            materialized.service_operation.service_operation_config.id
            == expected_operation_config_id
        )
        assert materialized.service_operation.api_endpoint is not None
        assert (
            materialized.service_operation.api_endpoint.id == expected_api_endpoint_id
        )
        assert materialized.service_operation.operation_key == operation_key
        assert materialized.service_operation.status == ServiceOperationStatus.queued
        assert materialized.service_operation.execution_context == {
            "source": "service-api-dispatch"
        }

        fast_operation_key = f"{operation_key}:fast"
        expected_fast_service_operation_id = stable_service_operation_id(
            service_id=expected_service_id,
            service_operation_config_id=expected_operation_config_id,
            operation_key=fast_operation_key,
        )
        with collect_service_api_trace_timings() as fast_timings:
            fast_materialized = await materialize_service_operation(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_lane,
                resolved_dispatch=resolved_dispatch,
                service_id=expected_service_id,
                operation_key=fast_operation_key,
                execution_context=cast(JsonObject, {"source": "service-api-dispatch"}),
                service_config_session=scratch,
                hydrate_committed_operation=False,
            )

        assert (
            fast_materialized.binding.service_operation_id
            == expected_fast_service_operation_id
        )
        assert (
            "service_operation.materialize.skip_hydrate_materialized_operation_s"
            in fast_timings
        )
        assert (
            "service_operation.materialize.hydrate_materialized_operation_s"
            not in fast_timings
        )
        assert fast_materialized.service_operation.id == (
            expected_fast_service_operation_id
        )
        assert fast_materialized.service_operation.service_id == expected_service_id
        assert (
            fast_materialized.service_operation.service_operation_config_id
            == expected_operation_config_id
        )
        assert fast_materialized.service_operation.api_call_id == api_call_id
        assert fast_materialized.service_operation.service_operation_config is None


@pytest.mark.parametrize(
    ("settlement_mode",),
    [
        ("coordinator",),
        ("economy_adapter",),
    ],
    ids=("coordinator", "economy_adapter"),
)
@pytest.mark.parametrize(
    ("settlement_policy", "expected_preparation_calls", "expected_finalization_calls"),
    [
        (ServiceOperationSettlementPolicy.none, 0, 0),
        (ServiceOperationSettlementPolicy.reserve_before_execute, 1, 0),
        (ServiceOperationSettlementPolicy.reserve_and_finalize, 1, 1),
    ],
    ids=("none", "reserve-before-execute", "reserve-and-finalize"),
)
@pytest.mark.parametrize(
    ("invoke_failure", "expected_operation_status", "expected_outcome_status"),
    [
        (False, ServiceOperationStatus.succeeded, "succeeded"),
        (True, ServiceOperationStatus.failed, "failed"),
    ],
    ids=("success", "failure"),
)
@pytest.mark.asyncio
async def test_execute_service_api_dispatch_plan_records_api_call_outcome_and_updates_service_operation(
    tmp_path: Path,
    settlement_mode: str,
    settlement_policy: ServiceOperationSettlementPolicy,
    expected_preparation_calls: int,
    expected_finalization_calls: int,
    invoke_failure: bool,
    expected_operation_status: ServiceOperationStatus,
    expected_outcome_status: str,
) -> None:
    repo_root = REPO_ROOT
    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_dispatch_operation_materialization",
    ) as aware_root:
        runtime = _build_service_meta_runtime(repo_root, workspace_root=aware_root)
        runtime_index = _runtime_index(runtime)

        request_class_config, request_attr_name, request_attr_value = (
            _select_runtime_inline_contract(
                runtime_index,
                preferred_base_types=(
                    CodePrimitiveBaseType.string,
                    CodePrimitiveBaseType.boolean,
                ),
            )
        )
        response_class_config, response_attr_name, response_attr_value = (
            _select_runtime_inline_contract(
                runtime_index,
                preferred_base_types=(
                    CodePrimitiveBaseType.boolean,
                    CodePrimitiveBaseType.string,
                ),
            )
        )

        request_model_cls = _create_required_model(
            model_name="ProofOpenRequest",
            field_name=request_attr_name,
            field_value=request_attr_value,
        )
        response_model_cls = _create_required_model(
            model_name="ProofOpenResponse",
            field_name=response_attr_name,
            field_value=response_attr_value,
        )
        request_object = request_model_cls.model_validate(
            {request_attr_name: request_attr_value}
        )
        response_payload = {response_attr_name: response_attr_value}
        expected_decoded_response_payload = {
            key: str(value) if isinstance(value, UUID) else value
            for key, value in response_payload.items()
        }

        environment_id = uuid4()
        boot_process_id, boot_thread_id, boot_branch_id = _seed_boot_environment(
            environment_id=environment_id,
        )
        lane = _MetaLaneIds(
            environment_id=environment_id,
            process_id=boot_process_id,
            thread_id=boot_thread_id,
            branch_id=boot_branch_id,
            actor_id=uuid4(),
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="Api",
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )
        endpoint_ref = "openai-api.door.open"
        branch_id = lane.branch_id
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            api_name="openai-api",
            endpoint_refs=(endpoint_ref,),
            endpoint_request_class_config_ids={
                endpoint_ref: request_class_config.id,
            },
            endpoint_fulfillment_names={endpoint_ref: ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        api_id = api_snapshot.api.id
        endpoint_id = api_snapshot.endpoint_ids_by_ref[endpoint_ref]
        api_capability_endpoint_function_id = api_snapshot.endpoint_function_ids_by_ref[
            endpoint_ref
        ]["open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
                response_class_ref=str(response_class_config.class_fqn or ""),
            ),
            endpoint_ref=endpoint_ref,
            request_payload={request_attr_name: request_attr_value},
        )
        materialized_api_call = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            ),
            target_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_call_projection_hash,
            ),
            ir=ir,
        )
        envelope = build_resolved_api_invocation_envelope(
            ir=ir,
            materialized_call=materialized_api_call.binding,
        )

        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(runtime_index)
        )
        service_projection_hash = _resolve_canonical_service_projection_hash(
            runtime_index
        )

        service_config_name = "compiler"
        service_name = "workspace_compiler"
        operation_config_name = "compile_module"
        operation_key = "turn-002"
        configured_price_id = uuid4()
        expected_service_config_id = stable_service_config_id(name=service_config_name)
        expected_service_id = stable_service_id(
            service_config_id=expected_service_config_id,
            name=service_name,
        )
        expected_operation_config_id = stable_service_operation_config_id(
            service_config_id=expected_service_config_id,
            name=operation_config_name,
        )
        expected_service_config_api_id = stable_service_config_api_id(
            service_config_id=expected_service_config_id,
            api_id=api_id,
        )
        expected_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=expected_service_config_api_id,
            api_capability_endpoint_id=endpoint_id,
        )
        expected_api_endpoint_function_binding_id = (
            stable_service_operation_config_api_endpoint_function_id(
                service_operation_config_api_endpoint_id=expected_api_endpoint_id,
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
            )
        )
        expected_service_operation_id = stable_service_operation_id(
            service_id=expected_service_id,
            service_operation_config_id=expected_operation_config_id,
            operation_key=operation_key,
        )

        service_config_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=service_projection_hash,
        )

        _ = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
            description="Compiler service catalog",
        )
        _ = await materialize_service_config_api(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            api_id=api_id,
            description="Shared API bridge",
        )
        _ = await materialize_service_operation_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            name=operation_config_name,
            description="Compile one module",
            price_id=configured_price_id,
            admission_mode="public_read",
            settlement_policy=settlement_policy,
        )
        _ = await materialize_service_operation_config_api_endpoint(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=expected_service_config_api_id,
            api_capability_endpoint_id=endpoint_id,
            description="Public endpoint binding",
        )
        bound_service_config_lane = runtime.bind(
            projection=service_config_projection_hash,
            branch_id=branch_id,
            actor_id=lane.actor_id,
        )
        create_function = await bound_service_config_lane.invoke_instance(
            orm_model=ServiceOperationConfigApiEndpoint(
                id=expected_api_endpoint_id,
                service_operation_config_id=expected_operation_config_id,
                service_config_api_id=expected_service_config_api_id,
                api_capability_endpoint_id=endpoint_id,
            ),
            function_name="create_function",
            payload={
                "api_capability_endpoint_function_id": api_capability_endpoint_function_id,
                "description": "Allowed API fulfillment",
            },
        )
        assert create_function.status == "succeeded", create_function.error
        assert (
            _payload_id(create_function.payload)
            == expected_api_endpoint_function_binding_id
        )
        _ = await materialize_service(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_lane,
            service_config_id=expected_service_config_id,
            name=service_name,
            description="Primary compiler service instance",
        )

        scratch = await _hydrate_committed_session(
            index=runtime_index,
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )

        observed_metering_contexts: list[ServiceOperationMeteringContextV1 | None] = []

        async def _invoke_open(*_: object) -> object | None:
            from aware_service_runtime.api_ingress.host_context import (
                current_service_api_host_context,
            )

            host_context = current_service_api_host_context()
            observed_metering_contexts.append(
                host_context.operation_metering_context
                if host_context is not None
                else None
            )
            if invoke_failure:
                raise RuntimeError("settlement-proof-boom")
            return response_model_cls.model_validate(response_payload)

        dispatch_plan = _dispatch_plan(
            envelope=envelope,
            request_object=cast(BaseModel, request_object),
            invoke=_invoke_open,
            fulfillment_name="open",
            response_type_ref=_authored_class_ref_from_class_fqn(
                str(response_class_config.class_fqn or "")
            ),
        )

        settlement_coordinator = (
            _RecordingSettlementCoordinator()
            if settlement_mode == "coordinator"
            else None
        )
        economy_settlement_adapter = (
            _RecordingEconomySettlementAdapter()
            if settlement_mode == "economy_adapter"
            else None
        )

        if invoke_failure:
            with pytest.raises(RuntimeError, match="settlement-proof-boom"):
                await execute_service_api_dispatch_plan(
                    runtime=runtime,
                    index=runtime_index,
                    session=scratch,
                    actor_id=lane.actor_id,
                    target_lane=service_lane,
                    dispatch_plan=dispatch_plan,
                    service_id=expected_service_id,
                    operation_key=operation_key,
                    handler=object(),
                    execution_context=cast(
                        JsonObject, {"source": "service-api-dispatch"}
                    ),
                    settlement_coordinator=settlement_coordinator,
                    economy_settlement_adapter=economy_settlement_adapter,
                )
            executed = None
        else:
            executed = await execute_service_api_dispatch_plan(
                runtime=runtime,
                index=runtime_index,
                session=scratch,
                actor_id=lane.actor_id,
                target_lane=service_lane,
                dispatch_plan=dispatch_plan,
                service_id=expected_service_id,
                operation_key=operation_key,
                handler=object(),
                execution_context=cast(JsonObject, {"source": "service-api-dispatch"}),
                settlement_coordinator=settlement_coordinator,
                economy_settlement_adapter=economy_settlement_adapter,
            )

        post_finalization_result_info: str | None = None
        post_finalization_error: str | None = None
        post_finalization_response_model_id: UUID | None = None

        if settlement_coordinator is not None:
            assert (
                len(settlement_coordinator.metering_context_preparations)
                == expected_preparation_calls
            )
            if observed_metering_contexts:
                expected_metering_context = (
                    ServiceOperationMeteringContextV1(
                        schema="aware.service.operation_metering_context.v1",
                        cost_basis_coin_id=settlement_coordinator.metering_coin_id,
                    )
                    if expected_preparation_calls == 1
                    else None
                )
                assert observed_metering_contexts == [expected_metering_context]
            assert (
                len(settlement_coordinator.preparations) == expected_preparation_calls
            )
            if expected_preparation_calls == 1:
                preparation = settlement_coordinator.preparations[0]
                assert preparation.context.actor_id == lane.actor_id
                assert preparation.context.service_id == expected_service_id
                assert preparation.context.service_ref.id == expected_service_id
                assert (
                    preparation.context.service_operation_id
                    == expected_service_operation_id
                )
                assert (
                    preparation.context.service_operation_ref.id
                    == expected_service_operation_id
                )
                assert (
                    preparation.context.service_operation_config_id
                    == expected_operation_config_id
                )
                assert (
                    preparation.context.service_operation_config_ref.id
                    == expected_operation_config_id
                )
                assert (
                    preparation.context.service_config_api_id
                    == expected_service_config_api_id
                )
                assert (
                    preparation.context.service_config_api_ref.id
                    == expected_service_config_api_id
                )
                assert (
                    preparation.context.service_api_endpoint_binding_id
                    == expected_api_endpoint_id
                )
                assert preparation.context.service_api_endpoint_binding_ref is not None
                assert (
                    preparation.context.service_api_endpoint_binding_ref.id
                    == expected_api_endpoint_id
                )
                assert preparation.context.api_capability_endpoint_id == endpoint_id
                assert preparation.context.api_capability_endpoint_ref.id == endpoint_id
                assert (
                    preparation.context.api_call_id
                    == materialized_api_call.binding.api_call_id
                )
                assert (
                    preparation.context.api_call_ref.id
                    == materialized_api_call.binding.api_call_id
                )
                assert (
                    preparation.context.request_hash
                    == materialized_api_call.binding.request_hash
                )
                assert preparation.context.operation_key == operation_key
                assert preparation.context.price_id == configured_price_id
                assert preparation.context.settlement_policy == settlement_policy
                assert "request_payload" not in preparation.__dataclass_fields__

            assert (
                len(settlement_coordinator.finalizations) == expected_finalization_calls
            )
            if expected_finalization_calls == 1:
                finalization, prepared_state = settlement_coordinator.finalizations[0]
                assert prepared_state == {"reservation_state": "prepared"}
                assert (
                    finalization.context.service_operation_id
                    == expected_service_operation_id
                )
                assert (
                    finalization.context.api_call_id
                    == materialized_api_call.binding.api_call_id
                )
                assert (
                    finalization.context.request_hash
                    == materialized_api_call.binding.request_hash
                )
                assert finalization.context.price_id == configured_price_id
                assert finalization.context.settlement_policy == settlement_policy
                assert (
                    finalization.service_operation_status == expected_operation_status
                )
                assert finalization.api_call_outcome_status is not None
                assert (
                    finalization.api_call_outcome_status.value
                    == expected_outcome_status
                )
                assert finalization.api_call_outcome_id is not None
                assert finalization.api_call_outcome_ref is not None
                assert (
                    finalization.api_call_outcome_ref.id
                    == finalization.api_call_outcome_id
                )
                assert "response_payload" not in finalization.__dataclass_fields__

                if invoke_failure:
                    assert finalization.result_info == "settlement-proof-boom"
                    assert (
                        finalization.api_call_outcome_error == "settlement-proof-boom"
                    )
                    assert finalization.api_call_outcome_response_model_id is None
                else:
                    post_finalization_result_info = finalization.result_info
                    post_finalization_error = finalization.api_call_outcome_error
                    post_finalization_response_model_id = (
                        finalization.api_call_outcome_response_model_id
                    )
        else:
            assert economy_settlement_adapter is not None
            assert (
                len(economy_settlement_adapter.reservations)
                == expected_preparation_calls
            )
            if expected_preparation_calls == 1:
                reservation = economy_settlement_adapter.reservations[0]
                assert reservation.actor_id == lane.actor_id
                assert reservation.service_ref.id == expected_service_id
                assert (
                    reservation.service_operation_ref.id
                    == expected_service_operation_id
                )
                assert (
                    reservation.service_operation_config_ref.id
                    == expected_operation_config_id
                )
                assert (
                    reservation.service_config_api_ref.id
                    == expected_service_config_api_id
                )
                assert reservation.service_api_endpoint_binding_ref is not None
                assert (
                    reservation.service_api_endpoint_binding_ref.id
                    == expected_api_endpoint_id
                )
                assert reservation.api_capability_endpoint_ref.id == endpoint_id
                assert (
                    reservation.api_call_ref.id
                    == materialized_api_call.binding.api_call_id
                )
                assert (
                    reservation.request_hash
                    == materialized_api_call.binding.request_hash
                )
                assert reservation.operation_key == operation_key
                assert reservation.price_id == configured_price_id
                assert reservation.settlement_policy == settlement_policy
                assert "request_payload" not in reservation.__dataclass_fields__

            assert (
                len(economy_settlement_adapter.finalizations)
                == expected_finalization_calls
            )
            if expected_finalization_calls == 1:
                finalization_input, prepared_state = (
                    economy_settlement_adapter.finalizations[0]
                )
                assert prepared_state == {"economy_state": "prepared"}
                assert (
                    finalization_input.reservation_input.service_ref.id
                    == expected_service_id
                )
                assert (
                    finalization_input.reservation_input.api_call_ref.id
                    == materialized_api_call.binding.api_call_id
                )
                assert (
                    finalization_input.reservation_input.request_hash
                    == materialized_api_call.binding.request_hash
                )
                assert (
                    finalization_input.reservation_input.settlement_policy
                    == settlement_policy
                )
                assert (
                    finalization_input.service_operation_status
                    == expected_operation_status
                )
                assert (
                    finalization_input.api_call_outcome_status.value
                    == expected_outcome_status
                )
                assert finalization_input.api_call_outcome_ref.id.int != 0
                assert "response_payload" not in finalization_input.__dataclass_fields__

                if invoke_failure:
                    assert finalization_input.result_info == "settlement-proof-boom"
                    assert (
                        finalization_input.api_call_outcome_error
                        == "settlement-proof-boom"
                    )
                    assert finalization_input.api_call_outcome_response_model_id is None
                else:
                    post_finalization_result_info = finalization_input.result_info
                    post_finalization_error = finalization_input.api_call_outcome_error
                    post_finalization_response_model_id = (
                        finalization_input.api_call_outcome_response_model_id
                    )

        if invoke_failure:
            return

        assert executed is not None

        assert (
            executed.materialized_operation.binding.service_operation_id
            == expected_service_operation_id
        )
        assert (
            executed.materialized_operation.binding.api_call_id
            == materialized_api_call.binding.api_call_id
        )
        assert (
            executed.materialized_operation.binding.api_endpoint_id
            == expected_api_endpoint_id
        )
        assert (
            executed.materialized_operation.service_operation.api_call_id
            == materialized_api_call.binding.api_call_id
        )
        assert (
            executed.materialized_operation.service_operation.status
            == ServiceOperationStatus.queued
        )

        assert executed.updated_operation is not None
        assert (
            executed.updated_operation.binding.service_operation_id
            == expected_service_operation_id
        )
        assert (
            executed.updated_operation.service_operation.id
            == expected_service_operation_id
        )
        assert (
            executed.updated_operation.service_operation.status
            == ServiceOperationStatus.succeeded
        )
        assert executed.updated_operation.service_operation.result_info is None
        assert (
            executed.updated_operation.service_operation.api_call_id
            == materialized_api_call.binding.api_call_id
        )
        assert len(executed.validated_fulfillment.bindings) == 1
        assert (
            executed.validated_fulfillment.bindings[
                0
            ].service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )
        assert (
            executed.validated_fulfillment.bindings[
                0
            ].api_capability_endpoint_function_id
            == api_capability_endpoint_function_id
        )

        assert executed.recorded_api_call_outcome is not None
        assert (
            executed.recorded_api_call_outcome.binding.api_call_id
            == materialized_api_call.binding.api_call_id
        )
        assert (
            executed.recorded_api_call_outcome.api_call.id
            == materialized_api_call.binding.api_call_id
        )
        assert executed.recorded_api_call_outcome.api_call_outcome.id is not None
        assert (
            executed.recorded_api_call_outcome.api_call_outcome.api_call_id
            == materialized_api_call.binding.api_call_id
        )
        assert (
            executed.recorded_api_call_outcome.api_call_outcome.status.value
            == "succeeded"
        )
        assert executed.recorded_api_call_outcome.api_call_outcome.error is None
        assert executed.recorded_api_call_outcome.binding.response_model_id is not None
        api_call_session = await _hydrate_committed_session(
            index=runtime_index,
            branch_id=branch_id,
            projection_hash=api_call_projection_hash,
        )
        committed_outcome = api_call_session.imap_get(
            ApiCallOutcome,
            executed.recorded_api_call_outcome.binding.api_call_outcome_id,
        )
        assert committed_outcome is not None
        response_model_id = executed.recorded_api_call_outcome.binding.response_model_id
        assert response_model_id is not None
        response_model = api_call_session.imap_get(
            InlineValueInstance,
            response_model_id,
        )
        assert response_model is not None
        assert (
            decode_inline_value_instance_to_mapping_strict(
                inline_value_instance=response_model,
                class_config=response_class_config,
                class_configs_by_id=runtime_index.class_configs_by_id,
            )
            == expected_decoded_response_payload
        )
        assert isinstance(executed.response_object, response_model_cls)
        if expected_finalization_calls == 1:
            assert post_finalization_result_info is None
            assert post_finalization_error is None
            assert (
                post_finalization_response_model_id
                == executed.recorded_api_call_outcome.binding.response_model_id
            )
