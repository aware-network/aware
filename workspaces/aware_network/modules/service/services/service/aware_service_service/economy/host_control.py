from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from aware_meta_service.local_sdk import MaterializationLaneContext
from aware_service_runtime.contracts import (
    BootstrapServiceContractAccessContextHostControlRequest,
    BootstrapServiceContractAccessContextHostControlResponse,
    EnsureServiceContractAccessContextHostControlRequest,
    EnsureServiceContractAccessContextHostControlResponse,
    RequestStatus,
)
from aware_utils.logging import logger

from aware_service_service.economy.contract_control import (
    activated_service_lane_or_none,
    ensure_wallet_backed_service_contract_access_context,
    resolve_wallet_backed_service_contract_access_context,
)


async def handle_contract_access_context_bootstrap_request(
    *,
    request: BootstrapServiceContractAccessContextHostControlRequest,
    resolve_activated_implementation_package_by_service_id: Callable[..., Any],
    resolve_dispatch_runtime_context: Callable[[], Awaitable[Any]],
    build_implementation_package_lanes: Callable[..., Any],
    build_service_subscription_lane: Callable[..., MaterializationLaneContext],
    build_service_contract_lane: Callable[..., MaterializationLaneContext],
    load_committed_service_lane_session: Callable[..., Awaitable[object]],
) -> BootstrapServiceContractAccessContextHostControlResponse:
    started_at = perf_counter()
    try:
        logger.info(
            "ServiceHost contract access context bootstrap started: service_id=%s",
            request.service_id,
        )
        (
            activated_package,
            service_name,
        ) = resolve_activated_implementation_package_by_service_id(
            service_id=request.service_id
        )
        logger.info(
            "ServiceHost contract access context bootstrap resolved implementation package: "
            "service_id=%s service_name=%s",
            request.service_id,
            service_name,
        )
        runtime_context = await resolve_dispatch_runtime_context()
        harness = runtime_context.runtime
        index = runtime_context.index
        logger.info(
            "ServiceHost contract access context bootstrap runtime context ready: "
            "service_id=%s",
            request.service_id,
        )
        service_config_lane = activated_service_lane_or_none(
            activated=activated_package.binding,
            service_name=service_name,
            lane_attr="service_config_lanes_by_name",
        )
        service_lane = activated_service_lane_or_none(
            activated=activated_package.binding,
            service_name=service_name,
            lane_attr="service_lanes_by_name",
        )
        if service_config_lane is None or service_lane is None:
            logger.info(
                "ServiceHost contract access context bootstrap building fallback lanes: "
                "service_id=%s service_config_lane_missing=%s service_lane_missing=%s",
                request.service_id,
                service_config_lane is None,
                service_lane is None,
            )
            lanes = build_implementation_package_lanes(
                runtime_context=runtime_context,
                runtime=harness,
                index=index,
            )
            service_config_lane = service_config_lane or lanes.service_config
            service_lane = service_lane or lanes.service
        else:
            logger.info(
                "ServiceHost contract access context bootstrap reused activated lanes: "
                "service_id=%s service_config_branch_id=%s service_branch_id=%s",
                request.service_id,
                service_config_lane.branch_id,
                service_lane.branch_id,
            )
        service_subscription_lane = build_service_subscription_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        service_contract_lane = build_service_contract_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        resolution = await resolve_wallet_backed_service_contract_access_context(
            index=index,
            service_id=request.service_id,
            consumer_finance_entity_id=request.consumer_finance_entity_id,
            service_operation_config_id=request.service_operation_config_id,
            service_subscription_id=request.service_subscription_id,
            service_contract_id=request.service_contract_id,
            service_contract_config_id=request.service_contract_config_id,
            smart_contract_id=request.smart_contract_id,
            service_config_lane=service_config_lane,
            service_lane=service_lane,
            service_contract_lane=service_contract_lane,
            service_subscription_lane=service_subscription_lane,
            load_session=load_committed_service_lane_session,
        )
        logger.info(
            "ServiceHost contract access context bootstrap session loaded: service_id=%s",
            request.service_id,
        )
        logger.info(
            "ServiceHost contract access context bootstrap finished: "
            "service_id=%s ready=%s blockers=%s duration_s=%.3f",
            request.service_id,
            resolution.ready,
            resolution.blockers,
            perf_counter() - started_at,
        )
        return BootstrapServiceContractAccessContextHostControlResponse(
            status=RequestStatus.succeeded,
            error=None,
            ready=resolution.read_model.ready,
            blocker=resolution.read_model.blocker,
            blockers=resolution.read_model.blockers,
            next_action=resolution.read_model.next_action,
            bootstrap=resolution.payload,
        )
    except Exception as exc:
        logger.exception(
            "ServiceHost contract access context bootstrap failed: "
            "service_id=%s duration_s=%.3f",
            request.service_id,
            perf_counter() - started_at,
        )
        return BootstrapServiceContractAccessContextHostControlResponse(
            status=RequestStatus.failed,
            error=str(exc),
            ready=False,
            blocker="servicehost_contract_access_context_bootstrap_failed",
            blockers=("servicehost_contract_access_context_bootstrap_failed",),
            next_action="inspect_servicehost_contract_access_context_bootstrap",
            bootstrap=None,
        )


async def handle_contract_access_context_ensure_request(
    *,
    request: EnsureServiceContractAccessContextHostControlRequest,
    resolve_activated_implementation_package_by_service_id: Callable[..., Any],
    resolve_dispatch_runtime_context: Callable[[], Awaitable[Any]],
    build_implementation_package_lanes: Callable[..., Any],
    build_service_subscription_lane: Callable[..., MaterializationLaneContext],
    build_service_contract_lane: Callable[..., MaterializationLaneContext],
    load_committed_service_lane_session: Callable[..., Awaitable[object]],
) -> EnsureServiceContractAccessContextHostControlResponse:
    started_at = perf_counter()
    try:
        logger.info(
            "ServiceHost contract access context ensure started: service_id=%s",
            request.service_id,
        )
        (
            activated_package,
            service_name,
        ) = resolve_activated_implementation_package_by_service_id(
            service_id=request.service_id
        )
        runtime_context = await resolve_dispatch_runtime_context()
        harness = runtime_context.runtime
        index = runtime_context.index
        service_config_lane = activated_service_lane_or_none(
            activated=activated_package.binding,
            service_name=service_name,
            lane_attr="service_config_lanes_by_name",
        )
        service_lane = activated_service_lane_or_none(
            activated=activated_package.binding,
            service_name=service_name,
            lane_attr="service_lanes_by_name",
        )
        if service_config_lane is None or service_lane is None:
            lanes = build_implementation_package_lanes(
                runtime_context=runtime_context,
                runtime=harness,
                index=index,
            )
            service_config_lane = service_config_lane or lanes.service_config
            service_lane = service_lane or lanes.service
        service_subscription_lane = build_service_subscription_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        service_contract_lane = build_service_contract_lane(
            runtime_context=runtime_context,
            branch_id=service_lane.branch_id,
        )
        resolution = await ensure_wallet_backed_service_contract_access_context(
            index=index,
            service_name=service_name,
            service_id=request.service_id,
            consumer_finance_entity_id=request.consumer_finance_entity_id,
            service_operation_config_id=request.service_operation_config_id,
            service_subscription_id=request.service_subscription_id,
            service_contract_id=request.service_contract_id,
            service_contract_config_id=request.service_contract_config_id,
            smart_contract_id=request.smart_contract_id,
            service_contract_config_name=request.service_contract_config_name,
            commercial_profile_id=request.commercial_profile_id,
            producer_finance_entity_id=request.producer_finance_entity_id,
            service_plan_id=request.service_plan_id,
            service_config_lane=service_config_lane,
            service_lane=service_lane,
            service_contract_lane=service_contract_lane,
            service_subscription_lane=service_subscription_lane,
            load_session=load_committed_service_lane_session,
        )
        logger.info(
            "ServiceHost contract access context ensure finished: "
            "service_id=%s ready=%s ensured=%s blockers=%s duration_s=%.3f",
            request.service_id,
            resolution.ready,
            resolution.ensured,
            resolution.blockers,
            perf_counter() - started_at,
        )
        return EnsureServiceContractAccessContextHostControlResponse(
            status=RequestStatus.succeeded,
            error=None,
            ready=resolution.read_model.ready,
            ensured=resolution.ensured,
            blocker=resolution.read_model.blocker,
            blockers=resolution.read_model.blockers,
            next_action=resolution.read_model.next_action,
            bootstrap=resolution.payload,
            admission=resolution.admission,
        )
    except Exception as exc:
        logger.exception(
            "ServiceHost contract access context ensure failed: "
            "service_id=%s duration_s=%.3f",
            request.service_id,
            perf_counter() - started_at,
        )
        return EnsureServiceContractAccessContextHostControlResponse(
            status=RequestStatus.failed,
            error=str(exc),
            ready=False,
            ensured=False,
            blocker="servicehost_contract_access_context_ensure_failed",
            blockers=("servicehost_contract_access_context_ensure_failed",),
            next_action="inspect_servicehost_contract_access_context_ensure",
            bootstrap=None,
            admission=None,
        )


__all__ = [
    "handle_contract_access_context_bootstrap_request",
    "handle_contract_access_context_ensure_request",
]
