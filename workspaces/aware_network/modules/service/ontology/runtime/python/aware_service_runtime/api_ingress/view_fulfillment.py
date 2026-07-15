from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_view import (
    ServiceOperationConfigApiView,
)

from aware_service_runtime.api_ingress.execution import (
    ServiceActorRoleEvidence,
    ServiceOperationAccessContext,
    ServiceOperationPreflightResult,
    validate_service_operation_preflight,
)


@dataclass(frozen=True, slots=True)
class ServiceApiViewFulfillmentCandidate:
    service_operation_config_api_view_id: UUID
    service_operation_config_id: UUID
    service_config_api_id: UUID
    api_view_id: UUID


@dataclass(frozen=True, slots=True)
class ServiceApiViewFulfillmentPlan:
    service_id: UUID
    api_view_id: UUID
    service_operation_config_api_view_id: UUID
    service_operation_config_id: UUID
    service_config_api_id: UUID
    preflight: ServiceOperationPreflightResult


def resolve_service_api_view_fulfillment(
    *,
    session: Session,
    service_id: UUID,
    api_view_id: UUID,
    actor_id: UUID | None,
    operation_access_context: ServiceOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
) -> ServiceApiViewFulfillmentPlan:
    service = session.imap_get(Service, service_id)
    if service is None:
        raise RuntimeError(
            "Service view fulfillment requires the concrete Service in the resolver session: "
            + f"service_id={service_id}"
        )

    candidates = _resolve_service_api_view_candidates(
        session=session,
        service_config_id=service.service_config_id,
        api_view_id=api_view_id,
    )
    if not candidates:
        raise RuntimeError(
            "Service view fulfillment could not resolve a ServiceOperationConfigApiView: "
            + f"service_id={service_id} "
            + f"api_view_id={api_view_id}"
        )
    if len(candidates) != 1:
        raise RuntimeError(
            "Service view fulfillment requires exactly one ServiceOperationConfigApiView "
            + "candidate for a concrete Service: "
            + f"service_id={service_id} "
            + f"api_view_id={api_view_id} "
            + f"candidate_count={len(candidates)}"
        )

    candidate = candidates[0]
    preflight = validate_service_operation_preflight(
        session=session,
        service_id=service_id,
        service_operation_config_id=candidate.service_operation_config_id,
        actor_id=actor_id,
        operation_access_context=operation_access_context,
        actor_role_evidence=actor_role_evidence,
    )
    return ServiceApiViewFulfillmentPlan(
        service_id=service_id,
        api_view_id=api_view_id,
        service_operation_config_api_view_id=candidate.service_operation_config_api_view_id,
        service_operation_config_id=candidate.service_operation_config_id,
        service_config_api_id=candidate.service_config_api_id,
        preflight=preflight,
    )


def _resolve_service_api_view_candidates(
    *,
    session: Session,
    service_config_id: UUID,
    api_view_id: UUID,
) -> tuple[ServiceApiViewFulfillmentCandidate, ...]:
    candidates: list[ServiceApiViewFulfillmentCandidate] = []
    for binding in _all_api_view_bindings(session=session):
        if binding.api_view_id != api_view_id:
            continue

        service_operation_config = session.imap_get(
            ServiceOperationConfig,
            binding.service_operation_config_id,
        )
        if service_operation_config is None:
            raise RuntimeError(
                "Service view fulfillment binding references missing ServiceOperationConfig: "
                + f"binding_id={binding.id} "
                + f"service_operation_config_id={binding.service_operation_config_id}"
            )
        if service_operation_config.service_config_id != service_config_id:
            continue
        if binding.id is None:
            raise RuntimeError(
                "ServiceOperationConfigApiView requires id before fulfillment."
            )

        candidates.append(
            ServiceApiViewFulfillmentCandidate(
                service_operation_config_api_view_id=cast(UUID, binding.id),
                service_operation_config_id=binding.service_operation_config_id,
                service_config_api_id=binding.service_config_api_id,
                api_view_id=binding.api_view_id,
            )
        )
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                str(item.service_operation_config_id),
                str(item.service_operation_config_api_view_id),
            ),
        )
    )


def _all_api_view_bindings(
    *, session: Session
) -> tuple[ServiceOperationConfigApiView, ...]:
    return tuple(
        cast(ServiceOperationConfigApiView, obj)
        for obj in session.imap_all_objects()
        if isinstance(obj, ServiceOperationConfigApiView)
    )


__all__ = [
    "ServiceApiViewFulfillmentCandidate",
    "ServiceApiViewFulfillmentPlan",
    "resolve_service_api_view_fulfillment",
]
