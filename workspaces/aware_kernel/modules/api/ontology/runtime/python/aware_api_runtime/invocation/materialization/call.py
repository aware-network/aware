from __future__ import annotations

from dataclasses import dataclass
import inspect
import os
from typing import Awaitable, ContextManager, Mapping, Protocol
from uuid import UUID, uuid4

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import (
    ApiCapabilityEndpointFunction,
)
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex, reify_oig_root_model
from aware_orm.registry import ORMModelRegistry
from aware_utils.logging import logger
from aware_utils.pydantic.class_config_registry import (
    get_registered_class_config_payload,
    iter_registered_class_config_payloads,
    iter_pydantic_package_class_config_payloads,
    register_pydantic_package_class_configs,
)

from ..resolution import (
    ApiInvocationIR,
    ApiInvocationSourceCommit,
    MaterializedApiCallBinding,
    ResolvedApiInvocationFulfillmentBinding,
)
from .context import (
    api_receipt_payload_summary,
    scoped_api_call_materialization_input,
    should_use_compact_api_receipt_payload,
)
from .pydantic_class_config_closure import pydantic_class_configs_by_id_for_ref


class _MetaRuntimeLaneProtocol(Protocol):
    @property
    def last_commit_id(self) -> UUID | None: ...

    @property
    def last_head_commit_id(self) -> UUID | None: ...

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> ContextManager[object]: ...


class _RuntimeProtocol(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> _MetaRuntimeLaneProtocol | Awaitable[_MetaRuntimeLaneProtocol]: ...


@dataclass(frozen=True, slots=True)
class ApiCallMaterializationResult:
    binding: MaterializedApiCallBinding
    api_call: ApiCall
    request_class_config: ClassConfig
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None


@dataclass(frozen=True, slots=True)
class _ResolvedApiEndpointRequestContract:
    endpoint_id: UUID
    request_class_config: ClassConfig
    fulfillment_bindings: tuple[ResolvedApiInvocationFulfillmentBinding, ...]
    endpoint: ApiCapabilityEndpoint | None = None


async def _resolve_runtime_lane(
    *,
    runtime: _RuntimeProtocol,
    lane: MaterializationLaneContext,
    actor_id: UUID | None,
) -> _MetaRuntimeLaneProtocol:
    runtime_lane = runtime.bind(
        projection=lane.projection_hash,
        branch_id=lane.branch_id,
        actor_id=actor_id,
    )
    if inspect.isawaitable(runtime_lane):
        runtime_lane = await runtime_lane
    return runtime_lane


async def materialize_api_call(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None = None,
    call_key: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
    receipt_projection_backend: str | None = None,
) -> ApiCallMaterializationResult:
    logger.info(
        "ApiCall materialization subphase started: resolve_request_contract "
        f"endpoint_ref={ir.endpoint_ref!r} request_class_config_id={ir.request_class_config_id}"
    )
    request_contract = await _resolve_api_endpoint_request_contract(
        index=index,
        source_lane=source_lane,
        ir=ir,
        source_commit=source_commit,
        require_endpoint=False,
    )
    logger.info(
        "ApiCall materialization subphase finished: resolve_request_contract "
        f"endpoint_ref={ir.endpoint_ref!r} "
        f"resolved_request_class_config_id={request_contract.request_class_config.id}"
    )
    request_class_config_id = request_contract.request_class_config.id
    effective_call_key = call_key or uuid4()
    source_opg = index.opg_by_hash.get(source_lane.projection_hash)
    target_opg = index.opg_by_hash.get(target_lane.projection_hash)
    logger.info(
        "ApiCall materialization subphase started: resolve_target_lane "
        f"endpoint_ref={ir.endpoint_ref!r} target_branch_id={target_lane.branch_id} "
        f"source_projection_hash={source_lane.projection_hash} "
        f"source_opg_name={getattr(source_opg, 'name', None)!r} "
        f"target_projection_hash={target_lane.projection_hash} "
        f"target_opg_name={getattr(target_opg, 'name', None)!r} "
        f"receipt_projection_backend={_receipt_projection_backend_name(receipt_projection_backend)!r}"
    )
    target_branch_head = await FSCommitStore().head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    effective_target_lane = (
        MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash=target_lane.projection_hash,
        )
        if target_branch_head is not None and target_branch_head.get("commit_id")
        else target_lane
    )
    logger.info(
        "ApiCall materialization subphase finished: resolve_target_lane "
        f"endpoint_ref={ir.endpoint_ref!r} effective_branch_id={effective_target_lane.branch_id}"
    )

    runtime_lane = await _resolve_runtime_lane(
        runtime=runtime,
        lane=effective_target_lane,
        actor_id=actor_id,
    )

    logger.info(
        "ApiCall materialization subphase started: create_api_call "
        f"endpoint_ref={ir.endpoint_ref!r} effective_branch_id={effective_target_lane.branch_id}"
    )
    use_compact_receipt_payload = should_use_compact_api_receipt_payload(
        payload=ir.request_payload,
        commit=commit,
        receipt_projection_backend=receipt_projection_backend,
    )
    compact_request_hash = (
        _compute_compact_request_hash(payload=ir.request_payload)
        if use_compact_receipt_payload
        else None
    )
    if use_compact_receipt_payload:
        summary = api_receipt_payload_summary(ir.request_payload)
        logger.info(
            "ApiCall materialization selected compact request payload receipt "
            f"endpoint_ref={ir.endpoint_ref!r} "
            f"request_hash={compact_request_hash!r} "
            f"field_count={summary['field_count']} "
            f"container_field_count={summary['container_field_count']} "
            f"nested_container_count={summary['nested_container_count']}"
        )
    with runtime_lane.activate(commit=commit, publish=publish):
        request_payload_for_receipt = (
            {} if use_compact_receipt_payload else ir.request_payload
        )
        request_class_configs_by_id = (
            None
            if use_compact_receipt_payload
            else _request_class_configs_by_id_for_materialization(
                index=index,
                request_class_config=request_contract.request_class_config,
                request_class_ref=ir.request_class_ref,
            )
        )
        with scoped_api_call_materialization_input(
            request_payload=request_payload_for_receipt,
            request_class_config=request_contract.request_class_config,
            request_class_configs_by_id=request_class_configs_by_id,
        ):
            api_call = await ApiCall.create_via_api_capability_endpoint(
                api_capability_endpoint_id=request_contract.endpoint_id,
                call_key=effective_call_key,
                request_class_config_id=request_class_config_id,
                description=ir.description,
            )
            if compact_request_hash is not None:
                api_call.request_hash = compact_request_hash
    logger.info(
        "ApiCall materialization subphase finished: create_api_call "
        f"endpoint_ref={ir.endpoint_ref!r} api_call_id={api_call.id}"
    )

    api_call_id = api_call.id
    request_model_id = api_call.request_model_id
    request_hash = (api_call.request_hash or "").strip()
    if api_call_id is None or request_model_id is None:
        raise RuntimeError(
            "ApiCall materialization must produce both api_call.id and request_model_id"
        )
    if not request_hash:
        raise RuntimeError("ApiCall materialization must produce api_call.request_hash")
    hydrated_api_call = api_call
    if hydrated_api_call.request_model is None:
        logger.info(
            "ApiCall materialization subphase started: hydrate_materialized_api_call "
            f"endpoint_ref={ir.endpoint_ref!r} api_call_id={api_call_id}"
        )
        hydrated_api_call = await _hydrate_materialized_api_call(
            index=index,
            target_lane=effective_target_lane,
            api_call_id=api_call_id,
            request_model_id=request_model_id,
        )
        logger.info(
            "ApiCall materialization subphase finished: hydrate_materialized_api_call "
            f"endpoint_ref={ir.endpoint_ref!r} api_call_id={api_call_id}"
        )

    logger.info(
        "ApiCall materialization finished "
        f"endpoint_ref={ir.endpoint_ref!r} api_call_id={api_call_id}"
    )
    return ApiCallMaterializationResult(
        binding=MaterializedApiCallBinding(
            api_call_id=api_call_id,
            api_capability_endpoint_id=request_contract.endpoint_id,
            call_key=effective_call_key,
            request_hash=request_hash,
            request_model_id=request_model_id,
            request_class_config_id=request_class_config_id,
            fulfillment_bindings=request_contract.fulfillment_bindings,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=effective_target_lane.branch_id,
            projection_hash=effective_target_lane.projection_hash,
        ),
        api_call=hydrated_api_call,
        request_class_config=request_contract.request_class_config,
        last_commit_id=runtime_lane.last_commit_id,
        last_head_commit_id=runtime_lane.last_head_commit_id,
    )


async def _resolve_api_endpoint_request_contract(
    *,
    index: MetaGraphRuntimeIndex,
    source_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None,
    require_endpoint: bool = False,
) -> _ResolvedApiEndpointRequestContract:
    if source_commit is None:
        source_branch_id = source_lane.branch_id
        source_projection_hash = source_lane.projection_hash
        source_head = await FSCommitStore().head(
            branch_id=source_branch_id,
            projection_hash=source_projection_hash,
        )
        if source_head is None or not source_head.get("commit_id"):
            raise RuntimeError(
                "ApiCall materialization requires a committed api lane head "
                "before endpoint identity can be derived"
            )
        source_commit_id = UUID(str(source_head["commit_id"]))
        source_oig_id = (
            UUID(str(source_head["object_instance_graph_id"]))
            if source_head.get("object_instance_graph_id")
            else None
        )
    else:
        source_branch_id = source_commit.branch_id
        source_projection_hash = source_commit.projection_hash
        source_commit_id = source_commit.commit_id
        source_oig_id = source_commit.object_instance_graph_id

    if ir.api_capability_endpoint_id is not None:
        endpoint = await _hydrate_source_api_endpoint(
            index=index,
            source_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            source_commit_id=source_commit_id,
            source_oig_id=source_oig_id,
            endpoint_id=ir.api_capability_endpoint_id,
        )
        if endpoint is None:
            raise RuntimeError(
                "ApiCall materialization could not resolve explicit ApiCapabilityEndpoint "
                "from the committed api lane: "
                f"endpoint_ref={ir.endpoint_ref!r} endpoint_id={ir.api_capability_endpoint_id}"
            )
        _validate_explicit_endpoint_identity(endpoint=endpoint, ir=ir)
        return await _resolve_endpoint_request_contract_from_endpoint(
            index=index,
            endpoint=endpoint,
            ir=ir,
        )

    verified_ir_contract = _resolve_verified_ir_endpoint_request_contract(
        index=index,
        ir=ir,
    )
    if verified_ir_contract is not None and not require_endpoint:
        return verified_ir_contract

    api_id = stable_api_id(name=ir.api_name)
    capability_id = stable_api_capability_id(api_id=api_id, name=ir.capability_name)
    endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=ir.endpoint_name,
    )
    endpoint = await _hydrate_source_api_endpoint(
        index=index,
        source_branch_id=source_branch_id,
        source_projection_hash=source_projection_hash,
        source_commit_id=source_commit_id,
        source_oig_id=source_oig_id,
        endpoint_id=endpoint_id,
    )
    if endpoint is None:
        api_root = await _hydrate_source_api_root(
            index=index,
            source_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            source_commit_id=source_commit_id,
            source_oig_id=source_oig_id,
            api_id=api_id,
        )
        endpoint = (
            _resolve_endpoint_from_api(api=api_root, ir=ir)
            if api_root is not None
            else None
        )
    if endpoint is None:
        raise RuntimeError(
            "ApiCall materialization could not resolve committed ApiCapabilityEndpoint from the api lane "
            "to derive the request contract through the endpoint portal: "
            f"api_name={ir.api_name} capability_name={ir.capability_name} "
            f"endpoint_name={ir.endpoint_name} endpoint_id={endpoint_id}"
        )

    return await _resolve_endpoint_request_contract_from_endpoint(
        index=index,
        endpoint=endpoint,
        ir=ir,
    )


def _receipt_projection_backend_name(receipt_projection_backend: str | None) -> str:
    backend = (
        receipt_projection_backend
        if receipt_projection_backend is not None
        else os.getenv("AWARE_PERSISTENCE_BACKEND")
    )
    return (backend or "").strip().lower()


def _compute_compact_request_hash(*, payload: Mapping[str, object]) -> str:
    from aware_api_runtime.request_hash import compute_api_request_hash_from_mapping

    return compute_api_request_hash_from_mapping(payload=payload)


async def _hydrate_source_api_endpoint(
    *,
    index: MetaGraphRuntimeIndex,
    source_branch_id: UUID,
    source_projection_hash: str,
    source_commit_id: UUID,
    source_oig_id: UUID | None,
    endpoint_id: UUID,
) -> ApiCapabilityEndpoint | None:
    opg = index.opg_by_hash.get(source_projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown source projection hash for ApiCall materialization: "
            f"{source_projection_hash}"
        )

    source_oig, _ = await CachedLaneMaterializer().get(
        branch_id=source_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=source_commit_id,
        oig_id=source_oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )

    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=source_oig,
        model_type=ApiCapabilityEndpoint,
        root_id=endpoint_id,
        branch_id=source_branch_id,
    )


async def _hydrate_source_api_root(
    *,
    index: MetaGraphRuntimeIndex,
    source_branch_id: UUID,
    source_projection_hash: str,
    source_commit_id: UUID,
    source_oig_id: UUID | None,
    api_id: UUID,
) -> Api | None:
    opg = index.opg_by_hash.get(source_projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown source projection hash for ApiCall materialization: "
            f"{source_projection_hash}"
        )

    source_oig, _ = await CachedLaneMaterializer().get(
        branch_id=source_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=source_commit_id,
        oig_id=source_oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )

    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=source_oig,
        model_type=Api,
        root_id=api_id,
        branch_id=source_branch_id,
    )


def _validate_explicit_endpoint_identity(
    *,
    endpoint: ApiCapabilityEndpoint,
    ir: ApiInvocationIR,
) -> None:
    endpoint_name = (endpoint.name or "").strip()
    if endpoint_name != ir.endpoint_name:
        raise RuntimeError(
            "ApiCall materialization resolved explicit ApiCapabilityEndpoint with mismatched name: "
            f"endpoint_id={endpoint.id} expected={ir.endpoint_name!r} got={endpoint_name!r}"
        )

    api_id = stable_api_id(name=ir.api_name)
    capability_id = stable_api_capability_id(api_id=api_id, name=ir.capability_name)
    if endpoint.api_capability_id != capability_id:
        raise RuntimeError(
            "ApiCall materialization resolved explicit ApiCapabilityEndpoint with mismatched capability: "
            f"endpoint_id={endpoint.id} expected_api_capability_id={capability_id} "
            f"got_api_capability_id={endpoint.api_capability_id}"
        )

    expected_endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=ir.endpoint_name,
    )
    if endpoint.id != expected_endpoint_id:
        raise RuntimeError(
            "ApiCall materialization resolved explicit ApiCapabilityEndpoint with mismatched endpoint identity: "
            f"expected_endpoint_id={expected_endpoint_id} got_endpoint_id={endpoint.id}"
        )


def _resolve_endpoint_from_api(
    *,
    api: Api,
    ir: ApiInvocationIR,
) -> ApiCapabilityEndpoint | None:
    if (api.name or "").strip() != ir.api_name:
        return None
    for capability in api.api_capabilities or ():
        if not isinstance(capability, ApiCapability):
            continue
        if (capability.name or "").strip() != ir.capability_name:
            continue
        for endpoint in capability.api_capability_endpoints or ():
            if not isinstance(endpoint, ApiCapabilityEndpoint):
                continue
            if (endpoint.name or "").strip() == ir.endpoint_name:
                return endpoint
    return None


async def _resolve_endpoint_request_contract_from_endpoint(
    *,
    index: MetaGraphRuntimeIndex,
    endpoint: ApiCapabilityEndpoint,
    ir: ApiInvocationIR,
) -> _ResolvedApiEndpointRequestContract:
    request_config = endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise RuntimeError(
            "ApiCall materialization resolved ApiCapabilityEndpoint without request_config: "
            f"endpoint_id={endpoint.id}"
        )

    request_class_config = _resolve_registered_pydantic_request_class_config(
        ir=ir,
        request_class_config_id=request_config.class_config_id,
    )
    if request_class_config is None:
        request_class_config = request_config.class_config
        if inspect.isawaitable(request_class_config):
            request_class_config = await request_class_config
    if request_class_config is None:
        request_class_config = index.class_configs_by_id.get(
            request_config.class_config_id
        )
    if request_class_config is None:
        orm_class = ORMModelRegistry.get_class_by_class_config_id(
            request_config.class_config_id
        )
        if orm_class is not None:
            request_class_config = orm_class.get_class_config()
    if request_class_config is None or request_class_config.id is None:
        raise RuntimeError(
            "ApiCall materialization requires request_config.class_config to resolve through the api "
            "projection portal before request-model materialization: "
            f"endpoint_id={endpoint.id} request_class_config_id={request_config.class_config_id}"
        )
    if request_config.class_config_id != request_class_config.id:
        raise RuntimeError(
            "ApiCall materialization resolved mismatched endpoint request contract: "
            f"endpoint_id={endpoint.id} expected_request_class_config_id={request_config.class_config_id} "
            f"got_request_class_config_id={request_class_config.id}"
        )
    if ir.request_class_config_id is not None:
        if request_class_config.id != ir.request_class_config_id:
            raise RuntimeError(
                "ApiCall materialization resolved endpoint request contract that disagrees with InvocationIR: "
                f"endpoint_id={endpoint.id} resolved_request_class_config_id={request_class_config.id} "
                f"invocation_request_class_config_id={ir.request_class_config_id}"
            )
    else:
        resolved_class_ref = (request_class_config.class_fqn or "").strip()
        if resolved_class_ref != ir.request_class_ref.strip():
            raise RuntimeError(
                "ApiCall materialization resolved endpoint request contract that disagrees with InvocationIR: "
                f"endpoint_id={endpoint.id} resolved_class_ref={resolved_class_ref!r} "
                f"invocation_request_class_ref={ir.request_class_ref!r}"
            )

    return _ResolvedApiEndpointRequestContract(
        endpoint_id=endpoint.id,
        request_class_config=request_class_config,
        fulfillment_bindings=await _resolve_committed_endpoint_fulfillment_bindings(
            endpoint=endpoint,
            invocation_fulfillment_bindings=ir.fulfillment_bindings,
        ),
        endpoint=endpoint,
    )


def _resolve_verified_ir_endpoint_request_contract(
    *,
    index: MetaGraphRuntimeIndex,
    ir: ApiInvocationIR,
) -> _ResolvedApiEndpointRequestContract | None:
    if ir.fulfillment_bindings:
        return None

    request_class_config = _resolve_verified_ir_request_class_config(
        index=index,
        ir=ir,
    )
    if request_class_config is None:
        return None

    api_id = stable_api_id(name=ir.api_name)
    capability_id = stable_api_capability_id(api_id=api_id, name=ir.capability_name)
    endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=ir.endpoint_name,
    )
    return _ResolvedApiEndpointRequestContract(
        endpoint_id=endpoint_id,
        request_class_config=request_class_config,
        fulfillment_bindings=(),
    )


def _resolve_verified_ir_request_class_config(
    *,
    index: MetaGraphRuntimeIndex,
    ir: ApiInvocationIR,
) -> ClassConfig | None:
    request_class_config_id = ir.request_class_config_id
    if request_class_config_id is not None:
        request_class_config = _resolve_registered_pydantic_request_class_config(
            ir=ir,
            request_class_config_id=request_class_config_id,
        )
        if request_class_config is not None:
            if request_class_config.id != request_class_config_id:
                return None
            return request_class_config

        request_class_config = index.class_configs_by_id.get(request_class_config_id)
        if request_class_config is None:
            orm_class = ORMModelRegistry.get_class_by_class_config_id(
                request_class_config_id
            )
            if orm_class is not None:
                request_class_config = orm_class.get_class_config()
        if request_class_config is None or request_class_config.id is None:
            return None
        if request_class_config.id != request_class_config_id:
            return None
        return request_class_config

    return _resolve_registered_pydantic_request_class_config(
        ir=ir,
        request_class_config_id=None,
    )


def _resolve_registered_pydantic_request_class_config(
    *,
    ir: ApiInvocationIR,
    request_class_config_id: UUID | None,
) -> ClassConfig | None:
    package_prefix = ir.request_class_ref.split(".", 1)[0].strip()
    if package_prefix:
        register_pydantic_package_class_configs(package_prefix=package_prefix)

    if request_class_config_id is not None:
        package_prefix = ir.request_class_ref.split(".", 1)[0].strip()
        for class_config in _iter_package_class_configs(package_prefix=package_prefix):
            if class_config.id == request_class_config_id:
                return class_config

        payload = get_registered_class_config_payload(
            class_config_id=str(request_class_config_id)
        )
        if payload is None:
            return None
        request_class_config = ClassConfig.model_validate(payload)
        if request_class_config.id != request_class_config_id:
            return None
        return request_class_config

    class_name = ir.request_class_ref.rsplit(".", 1)[-1].strip()
    matches: list[ClassConfig] = []
    entries = tuple(_iter_package_entries(package_prefix=package_prefix))
    if not entries:
        entries = tuple(iter_registered_class_config_payloads())
    for entry in entries:
        source = (entry.source or "").strip()
        if package_prefix and source and not source.startswith(package_prefix + "/"):
            continue
        payload = entry.payload
        payload_class_fqn = str(payload.get("class_fqn") or "").strip()
        payload_name = str(payload.get("name") or "").strip()
        if (
            payload_class_fqn == ir.request_class_ref
            or (class_name and payload_name == class_name)
            or (class_name and payload_class_fqn.endswith("." + class_name))
        ):
            matches.append(ClassConfig.model_validate(payload))

    unique_matches = {item.id: item for item in matches if item.id is not None}
    if len(unique_matches) != 1:
        return None
    return next(iter(unique_matches.values()))


def _request_class_configs_by_id_for_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    request_class_config: ClassConfig,
    request_class_ref: str,
) -> dict[UUID, ClassConfig]:
    return pydantic_class_configs_by_id_for_ref(
        base_class_configs_by_id=index.class_configs_by_id,
        root_class_config=request_class_config,
        class_ref=request_class_ref,
    )


def _iter_package_entries(*, package_prefix: str):
    if not package_prefix:
        return ()
    return tuple(
        iter_pydantic_package_class_config_payloads(package_prefix=package_prefix)
    )


def _iter_package_class_configs(*, package_prefix: str) -> tuple[ClassConfig, ...]:
    if not package_prefix:
        return ()
    class_configs: list[ClassConfig] = []
    for entry in _iter_package_entries(package_prefix=package_prefix):
        class_config = ClassConfig.model_validate(entry.payload)
        if class_config.id is not None:
            class_configs.append(class_config)
    return tuple(class_configs)


async def _resolve_committed_endpoint_fulfillment_bindings(
    *,
    endpoint: ApiCapabilityEndpoint,
    invocation_fulfillment_bindings: tuple[
        ResolvedApiInvocationFulfillmentBinding, ...
    ],
) -> tuple[ResolvedApiInvocationFulfillmentBinding, ...]:
    if not invocation_fulfillment_bindings:
        return ()

    endpoint_functions = endpoint.api_capability_endpoint_functions or ()
    if inspect.isawaitable(endpoint_functions):
        endpoint_functions = await endpoint_functions

    functions_by_name: dict[str, ApiCapabilityEndpointFunction] = {}
    for endpoint_function in endpoint_functions:
        if not isinstance(endpoint_function, ApiCapabilityEndpointFunction):
            continue
        normalized_name = (endpoint_function.name or "").strip().casefold()
        if not normalized_name:
            continue
        functions_by_name[normalized_name] = endpoint_function

    resolved_bindings: list[ResolvedApiInvocationFulfillmentBinding] = []
    for binding in invocation_fulfillment_bindings:
        normalized_name = binding.name.strip().casefold()
        endpoint_function = functions_by_name.get(normalized_name)
        if endpoint_function is None or endpoint_function.id is None:
            raise RuntimeError(
                "ApiCall materialization could not resolve committed ApiCapabilityEndpointFunction "
                "for API-owned fulfillment binding on the selected endpoint: "
                f"endpoint_id={endpoint.id} fulfillment_name={binding.name!r}"
            )
        resolved_bindings.append(
            type(binding)(
                name=binding.name,
                graph_target=binding.graph_target,
                graph_capability_function_name=binding.graph_capability_function_name,
                source_path=binding.source_path,
                api_capability_endpoint_function_id=endpoint_function.id,
            )
        )
    return tuple(resolved_bindings)


async def _hydrate_materialized_api_call(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    api_call_id: UUID,
    request_model_id: UUID,
) -> ApiCall:
    if target_lane.branch_id is None:
        raise RuntimeError(
            "ApiCall materialization requires branch_id on target lane for post-hydration."
        )

    target_head = await FSCommitStore().head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(
            "ApiCall materialization requires a committed api_call lane head for post-hydration."
        )

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown target projection hash for ApiCall post-hydration: "
            f"{target_lane.projection_hash}"
        )

    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=target_lane.branch_id,
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

    hydrated_api_call = reify_oig_root_model(
        index=index,
        opg=opg,
        oig=target_oig,
        model_type=ApiCall,
        root_id=api_call_id,
        branch_id=target_lane.branch_id,
    )
    if hydrated_api_call is None:
        raise RuntimeError(
            "ApiCall post-hydration could not resolve the committed ApiCall from the api_call lane: "
            f"api_call_id={api_call_id}"
        )

    if hydrated_api_call.request_model is None:
        request_model = reify_oig_root_model(
            index=index,
            opg=opg,
            oig=target_oig,
            model_type=InlineValueInstance,
            root_id=request_model_id,
            branch_id=target_lane.branch_id,
        )
        if request_model is None:
            raise RuntimeError(
                "ApiCall post-hydration could not resolve the committed request model from the api_call lane: "
                f"request_model_id={request_model_id}"
            )
        hydrated_api_call.request_model = request_model

    return hydrated_api_call


__all__ = [
    "ApiCallMaterializationResult",
    "materialize_api_call",
]
