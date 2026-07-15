from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ServiceApiProjectionOwnership:
    projection_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceApiOwnership:
    api_ref: str
    source_path: str
    api_projections: tuple[ServiceApiProjectionOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceExperienceOwnership:
    experience_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceCodePackageConfigOwnership:
    slot_key: str
    manifest_kind: str
    surface: str
    source_path: str
    cardinality: str = "many"
    required: bool = False


@dataclass(frozen=True, slots=True)
class ServiceOperationEndpointOwnership:
    endpoint_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceOperationApiViewOwnership:
    view_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceOperationRoleRequirementOwnership:
    role_ref: str
    source_path: str
    access_scope: str = "operation"
    scope_kind: str = "operation"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceInlinePriceDefinition:
    coin_symbol: str
    price_type: str
    effective_from: str
    fixed_amount: Decimal | None = None
    markup_percentage: Decimal | None = None
    effective_until: str | None = None
    policy_fail_closed: bool = True


@dataclass(frozen=True, slots=True)
class ServiceOperationOwnership:
    name: str
    source_path: str
    api_endpoints: tuple[ServiceOperationEndpointOwnership, ...] = ()
    api_views: tuple[ServiceOperationApiViewOwnership, ...] = ()
    role_requirements: tuple[ServiceOperationRoleRequirementOwnership, ...] = ()
    admission_mode: str = "contract_required"
    fulfillment_kind: str = "coordination"
    receipt_policy: str = "committed"
    settlement_policy: str = "none"
    price: ServiceInlinePriceDefinition | None = None
    price_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceContractOperationGrantOwnership:
    operation_ref: str
    source_path: str
    access_scope: str = "operation"


@dataclass(frozen=True, slots=True)
class ServiceContractActorRoleGrantOwnership:
    role_ref: str
    source_path: str
    access_scope: str = "service"
    scope_kind: str = "service"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceContractConfigOwnership:
    name: str
    source_path: str
    default_kind: str = "subscription"
    projection_experience_ref: str | None = None
    operation_grants: tuple[ServiceContractOperationGrantOwnership, ...] = ()
    actor_role_grants: tuple[ServiceContractActorRoleGrantOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceOwnership:
    name: str
    source_path: str
    apis: tuple[ServiceApiOwnership, ...]
    experiences: tuple[ServiceExperienceOwnership, ...]
    operations: tuple[ServiceOperationOwnership, ...]
    code_package_configs: tuple[ServiceCodePackageConfigOwnership, ...] = ()
    contract_configs: tuple[ServiceContractConfigOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceConfigApiProjectionPlan:
    projection_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceConfigApiPlan:
    api_ref: str
    source_path: str
    api_projections: tuple[ServiceConfigApiProjectionPlan, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceConfigExperiencePlan:
    experience_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceConfigCodePackageConfigPlan:
    slot_key: str
    manifest_kind: str
    surface: str
    code_package_config_key: str
    code_package_config_id: UUID
    source_path: str
    cardinality: str = "many"
    required: bool = False


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigApiEndpointPlan:
    endpoint_ref: str
    api_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigApiViewPlan:
    view_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigRoleRequirementPlan:
    role_ref: str
    source_path: str
    access_scope: str = "operation"
    scope_kind: str = "operation"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigPlan:
    name: str
    source_path: str
    api_endpoints: tuple[ServiceOperationConfigApiEndpointPlan, ...] = ()
    api_views: tuple[ServiceOperationConfigApiViewPlan, ...] = ()
    role_requirements: tuple[ServiceOperationConfigRoleRequirementPlan, ...] = ()
    admission_mode: str = "contract_required"
    fulfillment_kind: str = "coordination"
    receipt_policy: str = "committed"
    settlement_policy: str = "none"
    price: ServiceInlinePriceDefinition | None = None
    price_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceContractConfigOperationGrantPlan:
    operation_ref: str
    source_path: str
    access_scope: str = "operation"


@dataclass(frozen=True, slots=True)
class ServiceContractConfigActorRoleGrantPlan:
    role_ref: str
    source_path: str
    access_scope: str = "service"
    scope_kind: str = "service"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceContractConfigPlan:
    name: str
    source_path: str
    default_kind: str = "subscription"
    projection_experience_ref: str | None = None
    operation_grants: tuple[ServiceContractConfigOperationGrantPlan, ...] = ()
    actor_role_grants: tuple[ServiceContractConfigActorRoleGrantPlan, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceConfigPlan:
    name: str
    source_path: str
    apis: tuple[ServiceConfigApiPlan, ...]
    experiences: tuple[ServiceConfigExperiencePlan, ...]
    service_operation_configs: tuple[ServiceOperationConfigPlan, ...]
    code_package_configs: tuple[ServiceConfigCodePackageConfigPlan, ...] = ()
    contract_configs: tuple[ServiceContractConfigPlan, ...] = ()


__all__ = [
    "ServiceApiProjectionOwnership",
    "ServiceApiOwnership",
    "ServiceContractActorRoleGrantOwnership",
    "ServiceContractConfigActorRoleGrantPlan",
    "ServiceContractConfigOperationGrantPlan",
    "ServiceContractConfigOwnership",
    "ServiceContractConfigPlan",
    "ServiceContractOperationGrantOwnership",
    "ServiceConfigExperiencePlan",
    "ServiceConfigApiProjectionPlan",
    "ServiceConfigApiPlan",
    "ServiceCodePackageConfigOwnership",
    "ServiceConfigCodePackageConfigPlan",
    "ServiceConfigPlan",
    "ServiceInlinePriceDefinition",
    "ServiceExperienceOwnership",
    "ServiceOperationConfigApiEndpointPlan",
    "ServiceOperationConfigPlan",
    "ServiceOperationConfigApiViewPlan",
    "ServiceOperationConfigRoleRequirementPlan",
    "ServiceOperationEndpointOwnership",
    "ServiceOperationOwnership",
    "ServiceOperationRoleRequirementOwnership",
    "ServiceOperationApiViewOwnership",
    "ServiceOwnership",
]
