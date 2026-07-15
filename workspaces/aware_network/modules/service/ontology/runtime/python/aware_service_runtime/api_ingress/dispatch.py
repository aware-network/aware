from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from uuid import UUID

from aware_orm.session.session import Session
from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint

if TYPE_CHECKING:
    from aware_api_runtime.service_protocol import ApiServiceDispatchPlan


@dataclass(frozen=True, slots=True)
class ResolvedServiceApiDispatchCandidate:
    service_config_api_id: UUID
    service_operation_config_id: UUID
    service_operation_config_api_endpoint_id: UUID


@dataclass(frozen=True, slots=True)
class ResolvedServiceApiDispatch:
    dispatch_plan: ApiServiceDispatchPlan
    candidates: tuple[ResolvedServiceApiDispatchCandidate, ...]


def resolve_service_api_dispatch(
    *,
    session: Session,
    dispatch_plan: ApiServiceDispatchPlan,
) -> ResolvedServiceApiDispatch:
    endpoint_candidates: list[ResolvedServiceApiDispatchCandidate] = []
    for endpoint_binding in _all_endpoint_bindings(session=session):
        if endpoint_binding.api_capability_endpoint_id != dispatch_plan.envelope.api_capability_endpoint_id:
            continue
        endpoint_candidates.append(
            ResolvedServiceApiDispatchCandidate(
                service_config_api_id=endpoint_binding.service_config_api_id,
                service_operation_config_id=endpoint_binding.service_operation_config_id,
                service_operation_config_api_endpoint_id=cast(UUID, endpoint_binding.id),
            )
        )

    if not endpoint_candidates:
        raise RuntimeError(
            "Service runtime could not resolve any ServiceOperationConfigApiEndpoint candidates from "
            + "the API-owned dispatch plan: "
            + f"endpoint_ref={dispatch_plan.endpoint_ref!r} "
            + f"api_capability_endpoint_id={dispatch_plan.envelope.api_capability_endpoint_id}"
        )

    return ResolvedServiceApiDispatch(
        dispatch_plan=dispatch_plan,
        candidates=tuple(
            sorted(
                endpoint_candidates,
                key=lambda item: (
                    str(item.service_operation_config_id),
                    str(item.service_config_api_id),
                    str(item.service_operation_config_api_endpoint_id),
                ),
            )
        ),
    )


def require_single_service_api_dispatch_candidate(
    *,
    resolved_dispatch: ResolvedServiceApiDispatch,
) -> ResolvedServiceApiDispatchCandidate:
    candidates = resolved_dispatch.candidates
    if not candidates:
        raise RuntimeError("Service runtime requires at least one resolved API dispatch candidate.")
    if len(candidates) != 1:
        raise RuntimeError(
            "Service runtime requires exactly one API dispatch candidate before ServiceOperation materialization: "
            + f"endpoint_ref={resolved_dispatch.dispatch_plan.endpoint_ref!r} "
            + f"candidate_count={len(candidates)}"
        )
    return candidates[0]


def _all_endpoint_bindings(*, session: Session) -> tuple[ServiceOperationConfigApiEndpoint, ...]:
    objects = session.imap_all_objects()
    return tuple(
        sorted(
            (
                cast(ServiceOperationConfigApiEndpoint, obj)
                for obj in objects
                if isinstance(obj, ServiceOperationConfigApiEndpoint)
            ),
            key=lambda item: (
                str(item.service_operation_config_id),
                str(item.service_config_api_id),
                str(item.api_capability_endpoint_id),
                str(item.id),
            ),
        )
    )


__all__ = [
    "ResolvedServiceApiDispatch",
    "ResolvedServiceApiDispatchCandidate",
    "require_single_service_api_dispatch_candidate",
    "resolve_service_api_dispatch",
]
