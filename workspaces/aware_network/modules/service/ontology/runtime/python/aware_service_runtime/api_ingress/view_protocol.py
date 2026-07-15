from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_actor_role_grant import (
    ServiceContractConfigActorRoleGrant,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_view import (
    ServiceOperationConfigApiView,
)

from aware_service_runtime.api_ingress.execution import (
    ServiceActorRoleEvidence,
    ServiceOperationAccessContext,
)
from aware_service_runtime.api_ingress.view_fulfillment import (
    ServiceApiViewFulfillmentPlan,
    resolve_service_api_view_fulfillment,
)
from aware_service_runtime.materialization.service import (
    resolve_service_definition_materialization_specs,
)


@dataclass(frozen=True, slots=True)
class ServiceViewProtocolBinding:
    service_name: str
    operation_name: str
    view_ref: str
    endpoint_refs: tuple[str, ...]
    role_refs: tuple[str, ...]
    contract_refs: tuple[str, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceViewProtocolFulfillment:
    binding: ServiceViewProtocolBinding
    plan: ServiceApiViewFulfillmentPlan
    service_contract_config_actor_role_grant_ids: tuple[UUID, ...]


def build_service_view_protocol_bindings(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ServiceViewProtocolBinding, ...]:
    specs = resolve_service_definition_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    bindings: list[ServiceViewProtocolBinding] = []
    for spec in specs:
        service_config = spec.service_config
        for operation in service_config.service_operation_configs:
            endpoint_refs = tuple(
                endpoint.endpoint_ref for endpoint in operation.api_endpoints
            )
            role_refs = tuple(role.role_ref for role in operation.role_requirements)
            contract_refs = tuple(
                contract.name
                for contract in service_config.contract_configs
                if any(
                    grant.operation_ref == operation.name
                    for grant in contract.operation_grants
                )
            )
            for view in operation.api_views:
                bindings.append(
                    ServiceViewProtocolBinding(
                        service_name=service_config.name,
                        operation_name=operation.name,
                        view_ref=view.view_ref,
                        endpoint_refs=endpoint_refs,
                        role_refs=role_refs,
                        contract_refs=contract_refs,
                        source_path=view.source_path,
                    )
                )
    return tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.service_name.casefold(),
                item.operation_name.casefold(),
                item.view_ref.casefold(),
            ),
        )
    )


def require_service_view_protocol_binding(
    *,
    bindings: Sequence[ServiceViewProtocolBinding],
    service_name: str,
    view_ref: str,
    operation_name: str | None = None,
) -> ServiceViewProtocolBinding:
    normalized_service_name = _norm(service_name)
    normalized_view_ref = _norm(view_ref)
    normalized_operation_name = _norm(operation_name) if operation_name else None
    matches = tuple(
        binding
        for binding in bindings
        if _norm(binding.service_name) == normalized_service_name
        and _norm(binding.view_ref) == normalized_view_ref
        and (
            normalized_operation_name is None
            or _norm(binding.operation_name) == normalized_operation_name
        )
    )
    if len(matches) != 1:
        raise RuntimeError(
            "Service view protocol requires exactly one binding: "
            + f"service_name={service_name!r} view_ref={view_ref!r} "
            + f"operation_name={operation_name!r} match_count={len(matches)}"
        )
    return matches[0]


def resolve_service_view_protocol_fulfillment(
    *,
    session: Session,
    service_id: UUID,
    binding: ServiceViewProtocolBinding,
    actor_id: UUID | None,
    operation_access_context: ServiceOperationAccessContext | None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
) -> ServiceViewProtocolFulfillment:
    service = session.imap_get(Service, service_id)
    if service is None:
        raise RuntimeError(
            "Service view protocol fulfillment requires a concrete Service: "
            + f"service_id={service_id}"
        )
    if _norm(service.name) != _norm(binding.service_name):
        raise RuntimeError(
            "Service view protocol binding does not match concrete Service: "
            + f"binding_service_name={binding.service_name!r} service_name={service.name!r}"
        )

    operation_config = _require_operation_config(
        session=session,
        service_config_id=service.service_config_id,
        operation_name=binding.operation_name,
    )
    view_binding = _require_operation_view_binding(
        session=session,
        operation_config=operation_config,
        binding=binding,
    )
    plan = resolve_service_api_view_fulfillment(
        session=session,
        service_id=service_id,
        api_view_id=view_binding.api_view_id,
        actor_id=actor_id,
        operation_access_context=operation_access_context,
        actor_role_evidence=actor_role_evidence,
    )
    actor_role_grant_ids = _require_contract_actor_role_grants(
        plan=plan,
        operation_access_context=operation_access_context,
    )
    return ServiceViewProtocolFulfillment(
        binding=binding,
        plan=plan,
        service_contract_config_actor_role_grant_ids=actor_role_grant_ids,
    )


def _require_operation_config(
    *,
    session: Session,
    service_config_id: UUID,
    operation_name: str,
) -> ServiceOperationConfig:
    matches = tuple(
        cast(ServiceOperationConfig, obj)
        for obj in session.imap_all_objects()
        if isinstance(obj, ServiceOperationConfig)
        and obj.service_config_id == service_config_id
        and _norm(obj.name) == _norm(operation_name)
    )
    if len(matches) != 1:
        raise RuntimeError(
            "Service view protocol requires exactly one ServiceOperationConfig: "
            + f"service_config_id={service_config_id} operation_name={operation_name!r} "
            + f"match_count={len(matches)}"
        )
    return matches[0]


def _require_operation_view_binding(
    *,
    session: Session,
    operation_config: ServiceOperationConfig,
    binding: ServiceViewProtocolBinding,
) -> ServiceOperationConfigApiView:
    if operation_config.id is None:
        raise RuntimeError(
            "Service view protocol requires ServiceOperationConfig.id before fulfillment."
        )
    matches = tuple(
        cast(ServiceOperationConfigApiView, obj)
        for obj in session.imap_all_objects()
        if isinstance(obj, ServiceOperationConfigApiView)
        and obj.service_operation_config_id == operation_config.id
    )
    if len(matches) != 1:
        raise RuntimeError(
            "Service view protocol requires exactly one committed API view binding "
            + "for this operation. "
            + f"operation_name={operation_config.name!r} view_ref={binding.view_ref!r} "
            + f"match_count={len(matches)}"
        )
    return matches[0]


def _require_contract_actor_role_grants(
    *,
    plan: ServiceApiViewFulfillmentPlan,
    operation_access_context: ServiceOperationAccessContext | None,
) -> tuple[UUID, ...]:
    if operation_access_context is None:
        raise PermissionError(
            "Service view protocol fulfillment requires Service operation access context."
        )
    access_evidence = plan.preflight.access_evidence
    if access_evidence is None:
        raise PermissionError(
            "Service view protocol fulfillment requires Service operation grant evidence."
        )
    if access_evidence.service_contract_config_operation_grant_id is None:
        raise PermissionError(
            "Service view protocol fulfillment requires a ServiceContractConfig operation grant."
        )
    if not plan.preflight.actor_role_evidence:
        raise PermissionError(
            "Service view protocol fulfillment requires accepted ActorRole evidence."
        )

    service_contract_config_id = access_evidence.service_contract_config_id
    if service_contract_config_id is None:
        raise PermissionError(
            "Service view protocol fulfillment requires ServiceContractConfig evidence."
        )
    service_contract_config = (
        operation_access_context.service_contract_configs_by_id or {}
    ).get(service_contract_config_id)
    if service_contract_config is None:
        raise PermissionError(
            "Service view protocol fulfillment requires the ServiceContractConfig "
            "that granted operation access."
        )

    grant_ids: list[UUID] = []
    for evidence in plan.preflight.actor_role_evidence:
        grant = _matching_actor_role_grant(
            contract_config=service_contract_config,
            evidence=evidence,
        )
        if grant is None or grant.id is None:
            raise PermissionError(
                "Service view protocol fulfillment requires a matching "
                "ServiceContractConfig ActorRole grant."
            )
        grant_ids.append(grant.id)
    return tuple(grant_ids)


def _matching_actor_role_grant(
    *,
    contract_config: ServiceContractConfig,
    evidence: ServiceActorRoleEvidence,
) -> ServiceContractConfigActorRoleGrant | None:
    for grant in contract_config.actor_role_grants:
        if grant.role_config_id != evidence.role_config_id:
            continue
        if (
            grant.class_instance_identity_required
            and evidence.class_instance_identity_id is None
        ):
            continue
        if (
            grant.role_assignment_binding_required
            and evidence.role_assignment_binding_id is None
        ):
            continue
        return grant
    return None


def _norm(value: str) -> str:
    return (value or "").casefold().strip()


__all__ = [
    "ServiceViewProtocolBinding",
    "ServiceViewProtocolFulfillment",
    "build_service_view_protocol_bindings",
    "require_service_view_protocol_binding",
    "resolve_service_view_protocol_fulfillment",
]
