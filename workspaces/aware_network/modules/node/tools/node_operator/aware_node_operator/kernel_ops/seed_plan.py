from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

# Identity Runtime
from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_identity_id,
    stable_organization_id,
    stable_organization_member_id,
)

# Economy Runtime
from aware_economy.stable_ids import (
    stable_finance_entity_id,
    stable_smart_contract_config_id,
    stable_smart_contract_id,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_id,
    stable_service_id,
)

from aware_node_operator.kernel_ops.seed_spec import KernelSeedSpec


@dataclass(frozen=True, slots=True)
class PlannedIdentity:
    label: str
    identity_type: str
    public_key: str
    identity_id: UUID
    actor_id: UUID


@dataclass(frozen=True, slots=True)
class PlannedOrganization:
    provider: PlannedIdentity
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class PlannedOrganizationMember:
    organization_id: UUID
    member_identity: PlannedIdentity
    member_id: UUID
    role: str


@dataclass(frozen=True, slots=True)
class PlannedEconomyCatalog:
    provider_finance_entity_id: UUID
    smart_contract_config_id: UUID
    smart_contract_id: UUID


@dataclass(frozen=True, slots=True)
class PlannedServiceCatalog:
    service_config_id: UUID
    inference_service_id: UUID


@dataclass(frozen=True, slots=True)
class KernelSeedPlan:
    spec_id: str
    spec_version: int
    system_identity: PlannedIdentity
    provider_org: PlannedOrganization
    executors: tuple[PlannedIdentity, ...]
    members: tuple[PlannedOrganizationMember, ...]
    service: PlannedServiceCatalog
    economy: PlannedEconomyCatalog


def build_kernel_seed_plan(spec: KernelSeedSpec) -> KernelSeedPlan:
    system_key, _ = canonicalize_ed25519_public_key(spec.system.public_key)
    system_identity_id = stable_identity_id(
        public_key=system_key,
        type="system",
    )
    system_actor_id = stable_actor_id(identity_id=system_identity_id)
    system_identity = PlannedIdentity(
        label=spec.system.key_label,
        identity_type="system",
        public_key=system_key,
        identity_id=system_identity_id,
        actor_id=system_actor_id,
    )

    org_key, _ = canonicalize_ed25519_public_key(spec.organization.public_key)
    org_identity_id = stable_identity_id(
        public_key=org_key,
        type="organization",
    )
    org_actor_id = stable_actor_id(identity_id=org_identity_id)
    org_identity = PlannedIdentity(
        label=spec.organization.key_label,
        identity_type="organization",
        public_key=org_key,
        identity_id=org_identity_id,
        actor_id=org_actor_id,
    )
    organization_id = stable_organization_id(actor_id=org_actor_id)
    org = PlannedOrganization(provider=org_identity, organization_id=organization_id)

    executors: list[PlannedIdentity] = []
    members: list[PlannedOrganizationMember] = []
    for executor in spec.executors:
        key, _ = canonicalize_ed25519_public_key(executor.public_key)
        identity_id = stable_identity_id(
            public_key=key,
            type="agent",
        )
        actor_id = stable_actor_id(identity_id=identity_id)
        planned = PlannedIdentity(
            label=executor.key_label,
            identity_type="agent",
            public_key=key,
            identity_id=identity_id,
            actor_id=actor_id,
        )
        executors.append(planned)
        member_id = stable_organization_member_id(
            organization_id=organization_id,
            identity_id=identity_id,
        )
        members.append(
            PlannedOrganizationMember(
                organization_id=organization_id,
                member_identity=planned,
                member_id=member_id,
                role=(executor.role or "member"),
            )
        )

    provider_finance_entity_id = stable_finance_entity_id(identity_id=org_identity_id)
    service_config_id = stable_service_config_id(
        name=spec.service.service_config_name,
    )
    inference_service_id = stable_service_id(
        service_config_id=service_config_id,
        name=spec.service.inference_service_name,
    )
    smart_contract_config_id = stable_smart_contract_config_id(
        name=spec.economy.smart_contract_config_name,
        type=spec.economy.smart_contract_type,
    )
    smart_contract_id = stable_smart_contract_id(
        smart_contract_config_id=smart_contract_config_id,
        blockchain_address=spec.economy.smart_contract_address,
    )
    economy = PlannedEconomyCatalog(
        provider_finance_entity_id=provider_finance_entity_id,
        smart_contract_config_id=smart_contract_config_id,
        smart_contract_id=smart_contract_id,
    )
    service = PlannedServiceCatalog(
        service_config_id=service_config_id,
        inference_service_id=inference_service_id,
    )

    return KernelSeedPlan(
        spec_id=spec.meta.seed_id,
        spec_version=spec.meta.version,
        system_identity=system_identity,
        provider_org=org,
        executors=tuple(executors),
        members=tuple(members),
        service=service,
        economy=economy,
    )


__all__ = [
    "KernelSeedPlan",
    "PlannedEconomyCatalog",
    "PlannedIdentity",
    "PlannedOrganization",
    "PlannedOrganizationMember",
    "PlannedServiceCatalog",
    "build_kernel_seed_plan",
]
