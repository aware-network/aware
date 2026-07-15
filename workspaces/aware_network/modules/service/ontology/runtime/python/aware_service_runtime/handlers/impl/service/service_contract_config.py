from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceContractKind
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_actor_role_grant import ServiceContractConfigActorRoleGrant
from aware_service_ontology.service.service_contract_config_operation_grant import ServiceContractConfigOperationGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_experience_ontology.projection.projection_experience import ProjectionExperience
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.stable_ids import stable_service_contract_config_id

# --- AWARE: USER_IMPORTS END


async def grant_operation(
    service_contract_config: ServiceContractConfig,
    service_operation_config_id: UUID,
    access_scope: str = "operation",
    quota_policy_json: JsonObject | None = JsonObject(),
    permit_policy_json: JsonObject | None = JsonObject(),
    price_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ServiceContractConfigOperationGrant:
    """
    Grants access to one ServiceOperationConfig for contracts created from this config.

    Contract:
    - ServiceContractConfig grants reusable executable operation access.
    - Economy primitives fund, reserve, and settle concrete ServiceContract use.
    - Service runtime must resolve the concrete ServiceContract to this config before execution.
    """

    # --- AWARE: LOGIC START grant_operation
    created = await ServiceContractConfigOperationGrant.build_via_service_contract_config(
        service_contract_config_id=service_contract_config.id,
        service_operation_config_id=service_operation_config_id,
        access_scope=access_scope,
        quota_policy_json=quota_policy_json,
        permit_policy_json=permit_policy_json,
        price_policy_json=price_policy_json,
        description=description,
    )
    for existing in service_contract_config.operation_grants:
        if existing.id == created.id:
            return existing
    service_contract_config.operation_grants.append(created)
    return created
    # --- AWARE: LOGIC END grant_operation


async def grant_actor_role(
    service_contract_config: ServiceContractConfig,
    role_config_id: UUID,
    scope_kind: str = "service",
    scope_ref: str = "default",
    access_scope: str = "service",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    grant_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ServiceContractConfigActorRoleGrant:
    """
    Declares the ActorRole grant/evidence contracts created from this config activate.

    Contract:
    - Role policy remains owned by Identity RoleConfig.
    - This config is activation/evidence input; Identity owns concrete ActorRole assignment truth.
    - Runtime uses resolved ActorRole evidence, not this declaration alone, for execution.
    """

    # --- AWARE: LOGIC START grant_actor_role
    created = await ServiceContractConfigActorRoleGrant.build_via_service_contract_config(
        service_contract_config_id=service_contract_config.id,
        role_config_id=role_config_id,
        scope_kind=scope_kind,
        scope_ref=scope_ref,
        access_scope=access_scope,
        class_instance_identity_required=class_instance_identity_required,
        role_assignment_binding_required=role_assignment_binding_required,
        grant_policy_json=grant_policy_json,
        description=description,
    )
    for existing in service_contract_config.actor_role_grants:
        if existing.id == created.id:
            return existing
    service_contract_config.actor_role_grants.append(created)
    return created
    # --- AWARE: LOGIC END grant_actor_role


async def build_via_service_config(
    service_config_id: UUID,
    name: str,
    default_kind: ServiceContractKind = ServiceContractKind.subscription,
    projection_experience_id: UUID | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceContractConfig:
    """
    Creates one ServiceConfig-owned reusable contract definition.

    Contract:
    - Parent ServiceConfig scope is propagated by constructor lowering.
    - Stable identity is `(service_config_id, name)`.
    - This config declares reusable operation and ActorRole grants.
    - Concrete ServiceContract receipts point here when activated for a producer/consumer.
    """

    # --- AWARE: LOGIC START build_via_service_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServiceContractConfig.build_via_service_config requires non-empty name")

    resolved_default_kind = default_kind if default_kind is not None else ServiceContractKind.subscription
    metadata_payload = cast(JsonObject, dict(metadata_json or {}))
    contract_config_id = stable_service_contract_config_id(
        service_config_id=service_config_id,
        name=normalized_name,
    )
    session = current_handler_session()
    _ = session.imap_get(ServiceConfig, service_config_id)
    if projection_experience_id is not None:
        _ = session.imap_get(ProjectionExperience, projection_experience_id)

    existing = session.imap_get(ServiceContractConfig, contract_config_id)
    if existing is not None:
        if (
            existing.service_config_id != service_config_id
            or (existing.name or "").strip() != normalized_name
            or existing.default_kind != resolved_default_kind
            or existing.projection_experience_id != projection_experience_id
        ):
            raise RuntimeError(
                "ServiceContractConfig.build_via_service_config payload mismatch for existing config: "
                + f"service_contract_config_id={contract_config_id}"
            )
        existing.description = description
        existing.metadata_json = metadata_payload
        return existing

    return ServiceContractConfig(
        id=contract_config_id,
        service_config_id=service_config_id,
        name=normalized_name,
        default_kind=resolved_default_kind,
        projection_experience_id=projection_experience_id,
        description=description,
        metadata_json=metadata_payload,
    )
    # --- AWARE: LOGIC END build_via_service_config
