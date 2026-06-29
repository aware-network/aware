from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SdkApiOwnership:
    api_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SdkOperationEndpointOwnership:
    endpoint_ref: str
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkOperationDependencyOwnership:
    target_operation_ref: str
    target_sdk_name: str
    target_operation_name: str
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkOperationOwnership:
    name: str
    source_path: str
    endpoints: tuple[SdkOperationEndpointOwnership, ...]
    operation_dependencies: tuple[SdkOperationDependencyOwnership, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkSurfaceMethodOwnership:
    name: str
    surface_name: str
    source_path: str
    operation_ref: str
    operation_name: str
    method_family: str
    effect: str
    mutation_scope: str
    confirmation_policy: str
    execution_mode: str
    runtime_binding_kind: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkSurfaceOwnership:
    name: str
    source_path: str
    methods: tuple[SdkSurfaceMethodOwnership, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkOwnership:
    name: str
    source_path: str
    apis: tuple[SdkApiOwnership, ...]
    operations: tuple[SdkOperationOwnership, ...]
    surfaces: tuple[SdkSurfaceOwnership, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkConfigApiPlan:
    api_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SdkOperationEndpointPlan:
    name: str
    endpoint_ref: str
    api_ref: str
    capability_name: str
    source_path: str
    order: int
    role: str = "primary"
    required: bool = True
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkOperationDependencyPlan:
    target_operation_ref: str
    target_sdk_name: str
    target_operation_name: str
    target_package_name: str | None
    source_path: str
    order: int
    role: str = "dependency"
    required: bool = True
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkOperationPlan:
    name: str
    source_path: str
    api_endpoints: tuple[SdkOperationEndpointPlan, ...]
    sdk_operation_dependencies: tuple[SdkOperationDependencyPlan, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkSurfaceMethodPlan:
    name: str
    surface_name: str
    source_path: str
    operation_ref: str
    operation_name: str
    method_family: str
    effect: str
    mutation_scope: str
    confirmation_policy: str
    execution_mode: str
    runtime_binding_kind: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkSurfacePlan:
    name: str
    source_path: str
    methods: tuple[SdkSurfaceMethodPlan, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkConfigPlan:
    name: str
    source_path: str
    apis: tuple[SdkConfigApiPlan, ...]
    operations: tuple[SdkOperationPlan, ...]
    surfaces: tuple[SdkSurfacePlan, ...] = ()
    description: str | None = None


__all__ = [
    "SdkApiOwnership",
    "SdkConfigApiPlan",
    "SdkConfigPlan",
    "SdkOperationEndpointOwnership",
    "SdkOperationEndpointPlan",
    "SdkOperationDependencyOwnership",
    "SdkOperationDependencyPlan",
    "SdkOperationOwnership",
    "SdkOperationPlan",
    "SdkSurfaceMethodOwnership",
    "SdkSurfaceMethodPlan",
    "SdkSurfaceOwnership",
    "SdkSurfacePlan",
    "SdkOwnership",
]
