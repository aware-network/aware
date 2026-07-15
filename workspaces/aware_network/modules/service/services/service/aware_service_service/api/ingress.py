from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, ContextManager, cast
from uuid import uuid4

from aware_history.stable_ids import stable_branch_id
from aware_meta_service.local_sdk import MaterializationLaneContext
from aware_environment.stable_ids import stable_boot_thread_id
from aware_service_runtime.api_ingress.execution import (
    ServiceApiDispatchReceiptPolicy,
    ServiceOperationAdmissionDenied,
    service_operation_admission_blocked_payload,
)
from aware_service_runtime.api_ingress.admission_context import (
    normalize_service_operation_admission_context,
)
from aware_service_runtime.api_ingress.telemetry import (
    await_with_service_api_trace,
    service_api_trace_phase,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    RequestStatus,
    ServiceGraphGateway,
    ServiceHostApiIngressRequest,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
)
from aware_service_runtime.implementation_package import (
    build_activated_service_api_dispatch_plan_from_ingress,
    build_activated_service_api_read_model_dispatch_plan_from_ingress,
    build_prepared_service_config_session_for_api_dispatch,
    execute_activated_service_api_dispatch,
    load_committed_service_lane_session,
    resolve_activated_service_api_source_lane,
)
from aware_types import JsonValue
from aware_utils.logging import logger


def api_ingress_receipt_policy(
    *,
    request: object,
    activated: object,
    service_name: str,
    receipt_policy_resolver: Callable[..., object] | None = None,
    receipt_policy_type: object | None = None,
) -> object:
    policy_type = receipt_policy_type or _service_api_dispatch_receipt_policy_type()
    if bool(getattr(request, "stream_requested", False)):
        return getattr(policy_type, "committed")
    resolver = (
        receipt_policy_resolver
        if receipt_policy_resolver is not None
        else _resolve_prepared_service_api_receipt_policy
    )
    receipt_policy = resolver(
        activated=activated,
        service_name=service_name,
        endpoint_ref=getattr(request, "endpoint_ref"),
    )
    if _enum_value(receipt_policy) == _enum_value(getattr(policy_type, "read_model")):
        return getattr(policy_type, "read_model")
    return getattr(policy_type, "committed")


def api_ingress_execution_target_lane(
    *,
    request: object,
    fallback_lane: MaterializationLaneContext,
) -> MaterializationLaneContext:
    target_projection_hash = str(
        getattr(request, "target_projection_hash", "") or ""
    ).strip()
    target_branch_id = getattr(request, "target_branch_id", None)
    if (target_branch_id is None) != (not target_projection_hash):
        raise RuntimeError(
            "Service host API ingress target lane must provide both target_branch_id "
            "and target_projection_hash, or neither."
        )
    if target_branch_id is None:
        return fallback_lane
    return MaterializationLaneContext(
        branch_id=target_branch_id,
        projection_hash=target_projection_hash,
    )


async def handle_service_host_api_ingress_request(
    *,
    request: ServiceHostApiIngressRequest,
    active_stream_session_id: object | None,
    resolve_activated_implementation_endpoint: Callable[..., Any],
    resolve_dispatch_runtime_context: Callable[[], Any],
    materialization_runtime_persistence_context: Callable[[], ContextManager[None]],
    build_service_contract_lane: Callable[..., MaterializationLaneContext],
    build_service_subscription_lane: Callable[..., MaterializationLaneContext],
    build_economy_settlement_adapter: Callable[..., object | None],
    ontology_orm_package_path_context: Callable[..., ContextManager[None]],
    graph_gateway_for_activated_package: Callable[..., ServiceGraphGateway],
    send_service_response: Callable[..., Awaitable[None]],
    close_service_stream: Callable[..., Awaitable[None]],
    default_execution_backend_mode: Callable[[], object],
    workspace_root: Path,
    ontology_authority_package_names: tuple[str, ...],
    ontology_authority_source_kind: str,
    ontology_authority_root: Path | None,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...],
    meta_temporal_graph_route: MetaTemporalGraphRoute | None,
    build_environment_commit_receipt_source: Callable[[], object],
    ontology_replica_query: object,
    build_ontology_replica_orm_session: Callable[..., object],
    resolve_activated_service_lane: Callable[..., MaterializationLaneContext],
    service_package_name_for_activated_binding: Callable[..., str | None],
    load_contract_access_context_bootstrap_session: Callable[..., Awaitable[object]],
    merge_service_sessions: Callable[..., object],
    require_service_session: Callable[..., object],
) -> ServiceOperationResponse:
    trace_fields: dict[str, Any] = {
        "endpoint_ref": request.endpoint_ref,
        "discriminant": request.discriminant,
        "network_request_id": str(request.network_request_id),
        "stream_requested": request.stream_requested,
    }
    stream_requested = request.stream_requested
    if stream_requested and active_stream_session_id is None:
        raise RuntimeError(
            "Service host API ingress stream execution requires an active duplex stream session."
        )
    with service_api_trace_phase(
        "service_host.api_ingress.resolve_endpoint_binding",
        **trace_fields,
    ):
        endpoint_binding = resolve_activated_implementation_endpoint(
            endpoint_ref=request.endpoint_ref,
        )
    trace_fields["service_name"] = endpoint_binding.service_name
    receipt_policy = api_ingress_receipt_policy(
        request=request,
        activated=endpoint_binding.activated.binding,
        service_name=endpoint_binding.service_name,
    )
    trace_fields["receipt_policy"] = receipt_policy.value
    runtime_context = await await_with_service_api_trace(
        resolve_dispatch_runtime_context(),
        phase="service_host.api_ingress.resolve_dispatch_runtime_context",
        fields=trace_fields,
    )
    harness = runtime_context.runtime
    index = runtime_context.index
    with service_api_trace_phase(
        "service_host.api_ingress.resolve_implementation_lanes",
        environment_id=str(runtime_context.environment_config_id),
        runtime_index_source=runtime_context.runtime_index_source,
        **trace_fields,
    ):
        lanes = runtime_context.lanes
    api_source_lane = resolve_activated_service_api_source_lane(
        activated=endpoint_binding.activated.binding,
        default_lane=lanes.api,
        endpoint_ref=request.endpoint_ref,
    )
    receipt_projection_backend = _current_persistence_backend()
    if receipt_policy is ServiceApiDispatchReceiptPolicy.read_model:
        with materialization_runtime_persistence_context():
            dispatch_plan = await await_with_service_api_trace(
                build_activated_service_api_read_model_dispatch_plan_from_ingress(
                    activated=endpoint_binding.activated.binding,
                    index=index,
                    api_call_lane=lanes.api_call,
                    service_name=endpoint_binding.service_name,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    request_payload=request.request_payload,
                ),
                phase="service_host.api_ingress.build_read_model_dispatch_plan",
                fields=trace_fields,
                api_call_branch_id=str(getattr(lanes.api_call, "branch_id", None)),
            )
    else:
        with materialization_runtime_persistence_context():
            dispatch_plan = await await_with_service_api_trace(
                build_activated_service_api_dispatch_plan_from_ingress(
                    activated=endpoint_binding.activated.binding,
                    runtime=harness,
                    index=index,
                    actor_id=request.actor_id,
                    api_source_lane=api_source_lane,
                    api_call_lane=lanes.api_call,
                    service_name=endpoint_binding.service_name,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    request_payload=request.request_payload,
                    call_key=request.network_request_id,
                    receipt_projection_backend=receipt_projection_backend,
                ),
                phase="service_host.api_ingress.build_dispatch_plan",
                fields=trace_fields,
                api_source_branch_id=str(getattr(api_source_lane, "branch_id", None)),
                api_call_branch_id=str(getattr(lanes.api_call, "branch_id", None)),
            )
    with service_api_trace_phase(
        "service_host.api_ingress.resolve_execution_lanes",
        **trace_fields,
    ):
        service_config_lane = resolve_activated_service_lane(
            activated=endpoint_binding.activated.binding,
            service_name=endpoint_binding.service_name,
            lane_attr="service_config_lanes_by_name",
            fallback=lanes.service_config,
        )
        service_lane = resolve_activated_service_lane(
            activated=endpoint_binding.activated.binding,
            service_name=endpoint_binding.service_name,
            lane_attr="service_lanes_by_name",
            fallback=lanes.service,
        )
        execution_target_lane = api_ingress_execution_target_lane(
            request=request,
            fallback_lane=service_lane,
        )

    async def _load_service_config_session_for_api_ingress() -> object:
        prepared_session = build_prepared_service_config_session_for_api_dispatch(
            activated=endpoint_binding.activated.binding,
            service_name=endpoint_binding.service_name,
            dispatch_plan=dispatch_plan,
            service_config_lane=service_config_lane,
        )
        if prepared_session is not None:
            logger.info(
                "Service host API ingress reused prepared ServiceConfig session "
                "for endpoint-only dispatch endpoint_ref=%s service_name=%s "
                "service_config_branch_id=%s",
                request.endpoint_ref,
                endpoint_binding.service_name,
                service_config_lane.branch_id,
            )
            service_config_session = prepared_session
        else:
            logger.info(
                "Service host API ingress hydrating committed ServiceConfig lane "
                "endpoint_ref=%s service_name=%s service_config_branch_id=%s",
                request.endpoint_ref,
                endpoint_binding.service_name,
                service_config_lane.branch_id,
            )
            service_config_session = await load_committed_service_lane_session(
                index=index,
                lane=service_config_lane,
                error_context="Service host API ingress",
            )
        contract_access_context_ref_present = (
            _api_ingress_contract_access_context_ref_present(
                invocation_context=request.invocation_context,
                actor_id=request.actor_id,
            )
        )
        if prepared_session is not None and not contract_access_context_ref_present:
            logger.info(
                "Service host API ingress using prepared endpoint-only session "
                "without committed contract lane hydration endpoint_ref=%s "
                "service_name=%s receipt_policy=%s service_config_branch_id=%s",
                request.endpoint_ref,
                endpoint_binding.service_name,
                receipt_policy.value,
                service_config_lane.branch_id,
            )
            return require_service_session(
                service_config_session,
                error_context="Service host API ingress ServiceConfig lane",
            )
        if prepared_session is not None:
            logger.info(
                "Service host API ingress using prepared ServiceConfig session "
                "with committed contract lane hydration endpoint_ref=%s "
                "service_name=%s receipt_policy=%s service_config_branch_id=%s",
                request.endpoint_ref,
                endpoint_binding.service_name,
                receipt_policy.value,
                service_config_lane.branch_id,
            )
        service_contract_lane = build_service_contract_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        service_subscription_lane = build_service_subscription_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        contract_access_session = await load_contract_access_context_bootstrap_session(
            index=index,
            service_config_session=(
                None if prepared_session is not None else service_config_session
            ),
            service_config_lane=service_config_lane,
            service_lane=service_lane,
            service_contract_lane=service_contract_lane,
            service_subscription_lane=service_subscription_lane,
        )
        logger.info(
            "Service host API ingress merged contract access lanes "
            "endpoint_ref=%s service_name=%s service_contract_branch_id=%s "
            "service_subscription_branch_id=%s",
            request.endpoint_ref,
            endpoint_binding.service_name,
            service_contract_lane.branch_id,
            service_subscription_lane.branch_id,
        )
        return merge_service_sessions(
            require_service_session(
                service_config_session,
                error_context="Service host API ingress ServiceConfig lane",
            ),
            contract_access_session,
        )

    session = await await_with_service_api_trace(
        _load_service_config_session_for_api_ingress(),
        phase="service_host.api_ingress.load_service_config_session",
        fields=trace_fields,
        service_config_branch_id=str(service_config_lane.branch_id),
        service_config_projection_hash=service_config_lane.projection_hash,
    )
    stream_thread_id = stable_boot_thread_id(
        environment_id=runtime_context.environment_config_id
    )
    economy_settlement_adapter = (
        None
        if receipt_policy is ServiceApiDispatchReceiptPolicy.read_model
        else build_economy_settlement_adapter(
            actor_id=request.actor_id,
        )
    )
    stream_request = (
        ServiceOperationRequest(
            context=ServiceOperationContext(
                actor_id=request.actor_id,
                branch_id=stable_branch_id(
                    environment_id=runtime_context.environment_config_id,
                    thread_id=stream_thread_id,
                    key="service_host_api_ingress_stream",
                ),
                projection_hash="service.api_ingress",
            ),
            service=endpoint_binding.service_name,
            operation={
                "kind": "api_ingress_stream",
                "endpoint_ref": request.endpoint_ref,
            },
            stream_target_id=active_stream_session_id,
            network_request_id=request.network_request_id,
        )
        if stream_requested
        else None
    )

    async def _stream_event_sink(event_payload: object) -> None:
        if stream_request is None:
            raise RuntimeError(
                "Service host API ingress stream execution requires a stream request context."
            )
        await send_service_response(
            request=stream_request,
            response=ServiceOperationResponse(
                status=RequestStatus.pending,
                response_payload=_dump_service_duplex_payload(event_payload),
                stream_lifecycle=StreamLifecycle.started,
            ),
        )

    try:
        with ontology_orm_package_path_context(
            activated_package=endpoint_binding.activated
        ):
            with service_api_trace_phase(
                "service_host.api_ingress.prepare_dispatch_dependencies",
                **trace_fields,
            ):
                execution_backend_mode = default_execution_backend_mode()
                graph_gateway = graph_gateway_for_activated_package(
                    activated_package=endpoint_binding.activated,
                    service_name=endpoint_binding.service_name,
                )
                environment_commit_receipt_source = (
                    build_environment_commit_receipt_source()
                )
                ontology_replica_orm_session = build_ontology_replica_orm_session(
                    branch_id=None,
                )
            executed = await await_with_service_api_trace(
                execute_activated_service_api_dispatch(
                    activated=endpoint_binding.activated.binding,
                    runtime=harness,
                    index=index,
                    session=cast(Any, session),
                    actor_id=request.actor_id,
                    target_lane=service_lane,
                    api_source_lane=api_source_lane,
                    execution_target_lane=execution_target_lane,
                    service_package_id=endpoint_binding.activated.service_package_id,
                    service_package_name=service_package_name_for_activated_binding(
                        endpoint_binding.activated.binding
                    ),
                    service_name=endpoint_binding.service_name,
                    operation_key=_commercial_operation_key(
                        request_payload=request.request_payload,
                        endpoint_ref=request.endpoint_ref,
                    ),
                    dispatch_plan=dispatch_plan,
                    execution_backend_mode=execution_backend_mode,
                    graph_gateway=graph_gateway,
                    meta_temporal_graph_route=meta_temporal_graph_route,
                    workspace_root=workspace_root,
                    stream_requested=stream_requested,
                    stream_event_sink=(
                        _stream_event_sink if stream_requested else None
                    ),
                    economy_settlement_adapter=economy_settlement_adapter,
                    invocation_context=request.invocation_context,
                    ontology_authority_package_names=ontology_authority_package_names,
                    ontology_authority_source_kind=ontology_authority_source_kind,
                    ontology_authority_root=ontology_authority_root,
                    receipt_policy=receipt_policy,
                    service_api_dependency_routes=service_api_dependency_routes,
                    service_view_provider_routes=service_view_provider_routes,
                    environment_commit_receipt_source=environment_commit_receipt_source,
                    ontology_replica_query=ontology_replica_query,
                    ontology_replica_orm_session=ontology_replica_orm_session,
                ),
                phase="service_host.api_ingress.execute_dispatch",
                fields=trace_fields,
                service_branch_id=str(service_lane.branch_id),
                service_projection_hash=service_lane.projection_hash,
                execution_branch_id=str(execution_target_lane.branch_id),
                execution_projection_hash=execution_target_lane.projection_hash,
            )
    except ServiceOperationAdmissionDenied as exc:
        return ServiceOperationResponse(
            status=RequestStatus.failed,
            error=str(exc),
            response_payload=cast(
                JsonValue,
                service_operation_admission_blocked_payload(
                    admission=exc.admission,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    network_request_id=request.network_request_id,
                ),
            ),
            stream_lifecycle=StreamLifecycle.auto_close,
        )
    if stream_request is not None:
        await await_with_service_api_trace(
            close_service_stream(request=stream_request),
            phase="service_host.api_ingress.close_stream",
            fields=trace_fields,
        )
    with service_api_trace_phase(
        "service_host.api_ingress.shape_response_payload",
        **trace_fields,
    ):
        response_payload = _service_api_dispatch_response_payload(executed=executed)
    with service_api_trace_phase(
        "service_host.api_ingress.shape_dispatch_receipt",
        **trace_fields,
    ):
        receipt = _service_api_dispatch_receipt(
            executed=executed,
            network_request_id=request.network_request_id,
        )
    with service_api_trace_phase(
        "service_host.api_ingress.build_operation_response",
        **trace_fields,
    ):
        return ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload=response_payload,
            receipt=receipt,
            stream_lifecycle=(
                StreamLifecycle.started
                if stream_requested
                else StreamLifecycle.auto_close
            ),
        )


def _commercial_operation_key(
    *,
    request_payload: Mapping[str, object] | object,
    endpoint_ref: str,
) -> str:
    """Resolve the stable operation authorized by Service/Economy contracts.

    Invocation identity is carried independently by the API call id, request
    hash, and optional network request id. It must never be mixed into the
    reusable commercial operation key carried by a permit.
    """

    if isinstance(request_payload, Mapping):
        raw_operation = request_payload.get("operation")
        operation = str(raw_operation or "").strip()
        if operation:
            return operation
    endpoint = str(endpoint_ref or "").strip()
    if not endpoint:
        raise RuntimeError(
            "Service API ingress requires a stable operation discriminator or endpoint ref"
        )
    return endpoint


async def handle_service_operation_api_dispatch_request(
    *,
    request: object,
    execute_api_dispatch: Callable[..., Awaitable[object]],
    send_service_response: Callable[..., Awaitable[None]],
    close_service_stream: Callable[..., Awaitable[None]],
    default_execution_backend_mode: object,
) -> object:
    contracts = _service_runtime_contracts()
    dispatch_request = getattr(request, "api_dispatch", None)
    if dispatch_request is None:
        raise RuntimeError("Service host API dispatch request payload is required.")
    stream_requested = (
        getattr(request, "stream_target_id", None) is not None
        or getattr(request, "stream_correlation_id", None) is not None
    )

    async def _stream_event_sink(event_payload: object) -> None:
        await send_service_response(
            request=request,
            response=contracts.ServiceOperationResponse(
                status=contracts.RequestStatus.pending,
                response_payload=_dump_service_duplex_payload(event_payload),
                stream_lifecycle=contracts.StreamLifecycle.started,
            ),
        )

    executed = await execute_api_dispatch(
        service_name=getattr(request, "service"),
        dispatch_request=dispatch_request,
        actor_id=getattr(getattr(request, "context"), "actor_id"),
        execution_backend_mode=default_execution_backend_mode,
        stream_requested=stream_requested,
        stream_event_sink=(_stream_event_sink if stream_requested else None),
    )
    if stream_requested:
        await close_service_stream(request=request)
    return contracts.ServiceOperationResponse(
        status=contracts.RequestStatus.succeeded,
        response_payload=_service_api_dispatch_response_payload(executed=executed),
        receipt=_service_api_dispatch_receipt(
            executed=executed,
            network_request_id=getattr(request, "network_request_id", None),
        ),
        stream_lifecycle=(
            contracts.StreamLifecycle.started
            if stream_requested
            else contracts.StreamLifecycle.auto_close
        ),
    )


def _api_ingress_contract_access_context_ref_present(
    *,
    invocation_context: Mapping[str, object] | None,
    actor_id: object,
) -> bool:
    admission_context = normalize_service_operation_admission_context(
        invocation_context=invocation_context,
        legacy_actor_id=actor_id,
    )
    return admission_context.contract_access_context_ref is not None


def _service_api_dispatch_receipt_policy_type() -> object:
    from aware_service_runtime.api_ingress.execution import (
        ServiceApiDispatchReceiptPolicy,
    )

    return ServiceApiDispatchReceiptPolicy


def _resolve_prepared_service_api_receipt_policy(**kwargs: object) -> object:
    from aware_service_runtime.implementation_package import (
        resolve_prepared_service_api_receipt_policy,
    )

    return resolve_prepared_service_api_receipt_policy(**kwargs)


def _service_runtime_contracts() -> object:
    from aware_service_runtime import contracts

    return contracts


def _dump_service_duplex_payload(event_payload: object) -> object:
    from aware_service_runtime.duplex import dump_service_duplex_payload

    return dump_service_duplex_payload(event_payload)


def _service_api_dispatch_response_payload(*, executed: object) -> object:
    from aware_service_runtime.api_ingress.execution import (
        service_api_dispatch_response_payload,
    )

    return service_api_dispatch_response_payload(executed=executed)


def _service_api_dispatch_receipt(
    *,
    executed: object,
    network_request_id: object,
) -> object:
    from aware_service_runtime.api_ingress.execution import (
        service_api_dispatch_receipt,
    )

    return service_api_dispatch_receipt(
        executed=executed,
        network_request_id=network_request_id,
    )


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _current_persistence_backend() -> str | None:
    import os

    return os.environ.get("AWARE_PERSISTENCE_BACKEND")


__all__ = [
    "api_ingress_execution_target_lane",
    "api_ingress_receipt_policy",
    "handle_service_host_api_ingress_request",
    "handle_service_operation_api_dispatch_request",
]
