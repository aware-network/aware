from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_types import canonical_decimal_text
from aware_service_ontology.service.service_package import ServicePackage

from .compiler import load_service_ownership_from_sources
from .models import (
    ServiceApiOwnership,
    ServiceCodePackageConfigOwnership,
    ServiceContractConfigActorRoleGrantPlan,
    ServiceContractConfigOperationGrantPlan,
    ServiceContractConfigPlan,
    ServiceConfigCodePackageConfigPlan,
    ServiceConfigApiProjectionPlan,
    ServiceConfigApiPlan,
    ServiceConfigExperiencePlan,
    ServiceConfigPlan,
    ServiceInlinePriceDefinition,
    ServiceOperationConfigApiEndpointPlan,
    ServiceOperationConfigApiViewPlan,
    ServiceOperationConfigPlan,
    ServiceOperationConfigRoleRequirementPlan,
    ServiceOperationOwnership,
    ServiceOwnership,
)
from .workspace import ServiceWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class ServiceCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    service_ownership: tuple[ServiceOwnership, ...]
    service_configs: tuple[ServiceConfigPlan, ...]


@dataclass(frozen=True, slots=True)
class ServiceCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class ServiceActivationDependencyPin:
    package_name: str
    version_number: int | None
    kind: str
    service_package_provided_api_package_id: UUID | None = None
    api_package_id: UUID | None = None
    api_package_object_instance_graph_commit_id: UUID | None = None
    service_protocol_package_id: UUID | None = None
    service_protocol_code_package_id: UUID | None = None
    service_protocol_code_package_object_instance_graph_commit_id: UUID | None = None
    service_protocol_plan_hash_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceActivationProtocolLock:
    package_name: str
    service_package_provided_api_package_id: UUID
    api_package_id: UUID
    api_package_object_instance_graph_commit_id: UUID
    service_protocol_package_id: UUID
    service_protocol_code_package_id: UUID
    service_protocol_code_package_object_instance_graph_commit_id: UUID
    service_protocol_plan_hash_sha256: str


@dataclass(frozen=True, slots=True)
class ServiceActivationPlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    service_surface: str
    activation_mode: str
    materialize_on_start: bool
    compile_plan_artifact_relpath: str
    compile_plan_artifact_hash_sha256: str
    dependency_pins: tuple[ServiceActivationDependencyPin, ...]
    service_package_id: UUID | None = None
    service_package_object_instance_graph_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ServiceActivationPlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_service_compile_plan(
    *, snapshot: ServiceWorkspaceSnapshot
) -> ServiceCompilePlan:
    source_files = tuple(path.as_posix() for path in snapshot.source_files)
    service_ownership = load_service_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    endpoint_stream_modes = _load_api_endpoint_stream_modes(snapshot=snapshot)
    service_configs = tuple(
        _build_service_config_plan(
            service=service,
            endpoint_stream_modes=endpoint_stream_modes,
        )
        for service in service_ownership
    )
    return ServiceCompilePlan(
        schema_version=1,
        package_name=(snapshot.spec.service.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.service.fqn_prefix or "").strip(),
        source_files=source_files,
        service_ownership=service_ownership,
        service_configs=service_configs,
    )


def _load_api_endpoint_stream_modes(
    *,
    snapshot: ServiceWorkspaceSnapshot,
) -> dict[str, str]:
    runtime_root = snapshot.repo_root / ".aware" / "api" / "runtime"
    if not runtime_root.is_dir():
        return {}
    modes_by_endpoint_ref: dict[str, str] = {}
    for compile_plan_path in sorted(runtime_root.glob("*/api.compile_plan.json")):
        payload = json.loads(compile_plan_path.read_text(encoding="utf-8"))
        raw_api_ontology = payload.get("api_ontology", [])
        if not isinstance(raw_api_ontology, list):
            raise ValueError(
                "API compile plan has invalid api_ontology payload: "
                + str(compile_plan_path)
            )
        for raw_api in raw_api_ontology:
            if not isinstance(raw_api, dict):
                raise ValueError(
                    "API compile plan has invalid api_ontology entry: "
                    + str(compile_plan_path)
                )
            raw_stream_configs = raw_api.get(
                "capability_endpoint_stream_configs",
                [],
            )
            if not isinstance(raw_stream_configs, list):
                raise ValueError(
                    "API compile plan has invalid endpoint stream configs: "
                    + str(compile_plan_path)
                )
            for raw_stream_config in raw_stream_configs:
                if not isinstance(raw_stream_config, dict):
                    raise ValueError(
                        "API compile plan has invalid endpoint stream config entry: "
                        + str(compile_plan_path)
                    )
                api_name = str(raw_stream_config.get("api_name") or "").strip()
                capability_name = str(
                    raw_stream_config.get("capability_name") or ""
                ).strip()
                endpoint_name = str(
                    raw_stream_config.get("endpoint_name") or ""
                ).strip()
                stream_mode = (
                    str(raw_stream_config.get("stream_mode") or "").strip().casefold()
                )
                if not api_name or not capability_name or not endpoint_name:
                    raise ValueError(
                        "API compile plan stream config has incomplete endpoint identity: "
                        + str(compile_plan_path)
                    )
                if stream_mode not in {"server", "client", "bidirectional"}:
                    raise ValueError(
                        "API compile plan stream config has unsupported stream mode "
                        + f"{stream_mode!r}: {compile_plan_path}"
                    )
                endpoint_ref = ".".join(
                    (api_name, capability_name, endpoint_name)
                ).casefold()
                existing = modes_by_endpoint_ref.get(endpoint_ref)
                if existing is not None and existing != stream_mode:
                    raise ValueError(
                        "Conflicting API endpoint stream modes across compile plans: "
                        + f"endpoint_ref={endpoint_ref!r} "
                        + f"{existing!r} != {stream_mode!r}"
                    )
                modes_by_endpoint_ref[endpoint_ref] = stream_mode
    return modes_by_endpoint_ref


def _resolve_service_operation_fulfillment_kind(
    *,
    service: ServiceOwnership,
    operation: ServiceOperationOwnership,
    endpoint_stream_modes: dict[str, str],
) -> str:
    stream_modes = tuple(
        endpoint_stream_modes.get(endpoint.endpoint_ref.casefold())
        for endpoint in operation.api_endpoints
    )
    if not stream_modes or not any(mode is not None for mode in stream_modes):
        return operation.fulfillment_kind
    if any(mode is None for mode in stream_modes):
        raise ValueError(
            "Service operation cannot mix streaming and unary API endpoints: "
            + f"service={service.name!r} operation={operation.name!r}."
        )
    if operation.api_views:
        raise ValueError(
            "Service streaming operation cannot also bind an API view: "
            + f"service={service.name!r} operation={operation.name!r}."
        )
    if operation.receipt_policy == "read_model":
        raise ValueError(
            "Service streaming operation cannot use read_model receipt policy: "
            + f"service={service.name!r} operation={operation.name!r}."
        )
    if operation.fulfillment_kind == "view":
        raise ValueError(
            "Service streaming operation cannot compile from view fulfillment: "
            + f"service={service.name!r} operation={operation.name!r}."
        )
    return "actuation"


def emit_service_compile_plan_artifact(
    *,
    plan: ServiceCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ServiceCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "service.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ServiceCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def build_service_activation_plan(
    *,
    snapshot: ServiceWorkspaceSnapshot,
    compile_plan_artifact: ServiceCompilePlanArtifact,
    service_package: ServicePackage | None = None,
    service_package_object_instance_graph_commit_id: UUID | None = None,
    protocol_locks: tuple[ServiceActivationProtocolLock, ...] = (),
) -> ServiceActivationPlan:
    dependency_pins = _service_activation_dependency_pins(
        snapshot=snapshot,
        protocol_locks=protocol_locks,
    )
    return ServiceActivationPlan(
        schema_version=2,
        package_name=(snapshot.spec.service.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.service.fqn_prefix or "").strip(),
        service_surface=(snapshot.spec.host.service_surface or "").strip(),
        activation_mode=snapshot.spec.host.activation_mode.value,
        materialize_on_start=snapshot.spec.host.materialize_on_start,
        compile_plan_artifact_relpath=compile_plan_artifact.relpath,
        compile_plan_artifact_hash_sha256=compile_plan_artifact.hash_sha256,
        dependency_pins=dependency_pins,
        service_package_id=(
            service_package.id if service_package is not None else None
        ),
        service_package_object_instance_graph_commit_id=(
            service_package_object_instance_graph_commit_id
        ),
    )


def _service_activation_dependency_pins(
    *,
    snapshot: ServiceWorkspaceSnapshot,
    protocol_locks: tuple[ServiceActivationProtocolLock, ...],
) -> tuple[ServiceActivationDependencyPin, ...]:
    protocol_locks_by_package: dict[str, ServiceActivationProtocolLock] = {}
    for lock in protocol_locks:
        package_name = lock.package_name.strip()
        if not package_name:
            raise RuntimeError(
                "Committed Service activation lock requires ApiPackage.name."
            )
        if package_name in protocol_locks_by_package:
            raise RuntimeError(
                "Committed Service activation lock contains duplicate API package "
                f"relations: {package_name!r}"
            )
        protocol_locks_by_package[package_name] = lock

    result: list[ServiceActivationDependencyPin] = []
    consumed_protocol_locks: set[str] = set()
    for dependency in snapshot.spec.dependencies:
        package_name = dependency.package_name.strip()
        kind = dependency.kind.value
        lock = (
            protocol_locks_by_package.get(package_name)
            if kind == "api_service_protocol"
            else None
        )
        if lock is None:
            result.append(
                ServiceActivationDependencyPin(
                    package_name=package_name,
                    version_number=dependency.version_number,
                    kind=kind,
                )
            )
            continue

        result.append(
            ServiceActivationDependencyPin(
                package_name=package_name,
                version_number=dependency.version_number,
                kind=kind,
                service_package_provided_api_package_id=(
                    lock.service_package_provided_api_package_id
                ),
                api_package_id=lock.api_package_id,
                api_package_object_instance_graph_commit_id=(
                    lock.api_package_object_instance_graph_commit_id
                ),
                service_protocol_package_id=lock.service_protocol_package_id,
                service_protocol_code_package_id=lock.service_protocol_code_package_id,
                service_protocol_code_package_object_instance_graph_commit_id=(
                    lock.service_protocol_code_package_object_instance_graph_commit_id
                ),
                service_protocol_plan_hash_sha256=(
                    lock.service_protocol_plan_hash_sha256
                ),
            )
        )
        consumed_protocol_locks.add(package_name)

    unconsumed = sorted(
        set(protocol_locks_by_package) - consumed_protocol_locks,
        key=str.casefold,
    )
    if unconsumed:
        raise RuntimeError(
            "Committed Service activation lock contains API relations absent from "
            f"manifest dependency intent: {unconsumed!r}"
        )
    return tuple(result)


def emit_service_activation_plan_artifact(
    *,
    plan: ServiceActivationPlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ServiceActivationPlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_activation_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "service.activation_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ServiceActivationPlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def _build_service_config_plan(
    *,
    service: ServiceOwnership,
    endpoint_stream_modes: dict[str, str],
) -> ServiceConfigPlan:
    api_plans = tuple(
        ServiceConfigApiPlan(
            api_ref=api.api_ref,
            source_path=api.source_path,
            api_projections=tuple(
                ServiceConfigApiProjectionPlan(
                    projection_ref=projection.projection_ref,
                    source_path=projection.source_path,
                )
                for projection in api.api_projections
            ),
        )
        for api in service.apis
    )
    experience_plans = tuple(
        ServiceConfigExperiencePlan(
            experience_ref=experience.experience_ref,
            source_path=experience.source_path,
        )
        for experience in service.experiences
    )
    code_package_config_plans = tuple(
        _build_service_config_code_package_config_plan(item)
        for item in service.code_package_configs
    )
    operation_plans = tuple(
        ServiceOperationConfigPlan(
            name=operation.name,
            source_path=operation.source_path,
            api_endpoints=tuple(
                ServiceOperationConfigApiEndpointPlan(
                    endpoint_ref=endpoint.endpoint_ref,
                    api_ref=_resolve_api_ref_for_endpoint(
                        endpoint_ref=endpoint.endpoint_ref, apis=service.apis
                    ),
                    source_path=endpoint.source_path,
                )
                for endpoint in operation.api_endpoints
            ),
            api_views=tuple(
                ServiceOperationConfigApiViewPlan(
                    view_ref=view.view_ref,
                    source_path=view.source_path,
                )
                for view in operation.api_views
            ),
            role_requirements=tuple(
                ServiceOperationConfigRoleRequirementPlan(
                    role_ref=requirement.role_ref,
                    access_scope=requirement.access_scope,
                    scope_kind=requirement.scope_kind,
                    scope_ref=requirement.scope_ref,
                    class_instance_identity_required=(
                        requirement.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        requirement.role_assignment_binding_required
                    ),
                    source_path=requirement.source_path,
                )
                for requirement in operation.role_requirements
            ),
            admission_mode=operation.admission_mode,
            fulfillment_kind=_resolve_service_operation_fulfillment_kind(
                service=service,
                operation=operation,
                endpoint_stream_modes=endpoint_stream_modes,
            ),
            receipt_policy=operation.receipt_policy,
            settlement_policy=operation.settlement_policy,
            price=operation.price,
            price_ref=operation.price_ref,
        )
        for operation in service.operations
    )
    contract_config_plans = tuple(
        ServiceContractConfigPlan(
            name=contract_config.name,
            source_path=contract_config.source_path,
            default_kind=contract_config.default_kind,
            projection_experience_ref=contract_config.projection_experience_ref,
            operation_grants=tuple(
                ServiceContractConfigOperationGrantPlan(
                    operation_ref=grant.operation_ref,
                    access_scope=grant.access_scope,
                    source_path=grant.source_path,
                )
                for grant in contract_config.operation_grants
            ),
            actor_role_grants=tuple(
                ServiceContractConfigActorRoleGrantPlan(
                    role_ref=grant.role_ref,
                    access_scope=grant.access_scope,
                    scope_kind=grant.scope_kind,
                    scope_ref=grant.scope_ref,
                    class_instance_identity_required=(
                        grant.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        grant.role_assignment_binding_required
                    ),
                    source_path=grant.source_path,
                )
                for grant in contract_config.actor_role_grants
            ),
        )
        for contract_config in service.contract_configs
    )
    return ServiceConfigPlan(
        name=service.name,
        source_path=service.source_path,
        apis=api_plans,
        experiences=experience_plans,
        service_operation_configs=operation_plans,
        code_package_configs=code_package_config_plans,
        contract_configs=contract_config_plans,
    )


def _build_service_config_code_package_config_plan(
    item: ServiceCodePackageConfigOwnership,
) -> ServiceConfigCodePackageConfigPlan:
    config_key = code_package_source_config_key(
        manifest_kind=item.manifest_kind,
        surface=item.surface,
    )
    return ServiceConfigCodePackageConfigPlan(
        slot_key=item.slot_key,
        manifest_kind=item.manifest_kind,
        surface=item.surface,
        code_package_config_key=config_key,
        code_package_config_id=stable_code_package_config_id(config_key=config_key),
        cardinality=item.cardinality,
        required=item.required,
        source_path=item.source_path,
    )


def _resolve_api_ref_for_endpoint(
    *, endpoint_ref: str, apis: tuple[ServiceApiOwnership, ...]
) -> str:
    matches = [
        api.api_ref
        for api in apis
        if endpoint_ref == api.api_ref or endpoint_ref.startswith(api.api_ref + ".")
    ]
    if not matches:
        raise ValueError(
            f"Service compile plan cannot resolve api_ref for endpoint {endpoint_ref!r}"
        )
    return max(matches, key=len)


def _encode_plan(*, plan: ServiceCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "service_ownership": [
            {
                "name": service.name,
                "source_path": service.source_path,
                "apis": [
                    {
                        "api_ref": api.api_ref,
                        "source_path": api.source_path,
                        "api_projections": [
                            {
                                "projection_ref": projection.projection_ref,
                                "source_path": projection.source_path,
                            }
                            for projection in api.api_projections
                        ],
                    }
                    for api in service.apis
                ],
                "experiences": [
                    {
                        "experience_ref": experience.experience_ref,
                        "source_path": experience.source_path,
                    }
                    for experience in service.experiences
                ],
                "code_package_configs": [
                    {
                        "slot_key": item.slot_key,
                        "manifest_kind": item.manifest_kind,
                        "surface": item.surface,
                        "cardinality": item.cardinality,
                        "required": item.required,
                        "source_path": item.source_path,
                    }
                    for item in service.code_package_configs
                ],
                "operations": [
                    {
                        "name": operation.name,
                        "source_path": operation.source_path,
                        "admission_mode": operation.admission_mode,
                        "fulfillment_kind": operation.fulfillment_kind,
                        "receipt_policy": operation.receipt_policy,
                        "settlement_policy": operation.settlement_policy,
                        "price": _encode_inline_price_definition(operation.price),
                        "price_ref": operation.price_ref,
                        "api_endpoints": [
                            {
                                "endpoint_ref": endpoint.endpoint_ref,
                                "source_path": endpoint.source_path,
                            }
                            for endpoint in operation.api_endpoints
                        ],
                        "api_views": [
                            {
                                "view_ref": view.view_ref,
                                "source_path": view.source_path,
                            }
                            for view in operation.api_views
                        ],
                        "role_requirements": [
                            {
                                "role_ref": requirement.role_ref,
                                "access_scope": requirement.access_scope,
                                "scope_kind": requirement.scope_kind,
                                "scope_ref": requirement.scope_ref,
                                "class_instance_identity_required": (
                                    requirement.class_instance_identity_required
                                ),
                                "role_assignment_binding_required": (
                                    requirement.role_assignment_binding_required
                                ),
                                "source_path": requirement.source_path,
                            }
                            for requirement in operation.role_requirements
                        ],
                    }
                    for operation in service.operations
                ],
                "contract_configs": [
                    {
                        "name": contract_config.name,
                        "source_path": contract_config.source_path,
                        "default_kind": contract_config.default_kind,
                        "projection_experience_ref": contract_config.projection_experience_ref,
                        "operation_grants": [
                            {
                                "operation_ref": grant.operation_ref,
                                "access_scope": grant.access_scope,
                                "source_path": grant.source_path,
                            }
                            for grant in contract_config.operation_grants
                        ],
                        "actor_role_grants": [
                            {
                                "role_ref": grant.role_ref,
                                "access_scope": grant.access_scope,
                                "scope_kind": grant.scope_kind,
                                "scope_ref": grant.scope_ref,
                                "class_instance_identity_required": (
                                    grant.class_instance_identity_required
                                ),
                                "role_assignment_binding_required": (
                                    grant.role_assignment_binding_required
                                ),
                                "source_path": grant.source_path,
                            }
                            for grant in contract_config.actor_role_grants
                        ],
                    }
                    for contract_config in service.contract_configs
                ],
            }
            for service in plan.service_ownership
        ],
        "service_configs": [
            {
                "name": service_config.name,
                "source_path": service_config.source_path,
                "apis": [
                    {
                        "api_ref": api.api_ref,
                        "source_path": api.source_path,
                        "api_projections": [
                            {
                                "projection_ref": projection.projection_ref,
                                "source_path": projection.source_path,
                            }
                            for projection in api.api_projections
                        ],
                    }
                    for api in service_config.apis
                ],
                "experiences": [
                    {
                        "experience_ref": experience.experience_ref,
                        "source_path": experience.source_path,
                    }
                    for experience in service_config.experiences
                ],
                "code_package_configs": [
                    {
                        "slot_key": item.slot_key,
                        "manifest_kind": item.manifest_kind,
                        "surface": item.surface,
                        "code_package_config_key": item.code_package_config_key,
                        "code_package_config_id": str(item.code_package_config_id),
                        "cardinality": item.cardinality,
                        "required": item.required,
                        "source_path": item.source_path,
                    }
                    for item in service_config.code_package_configs
                ],
                "service_operation_configs": [
                    {
                        "name": operation.name,
                        "source_path": operation.source_path,
                        "admission_mode": operation.admission_mode,
                        "fulfillment_kind": operation.fulfillment_kind,
                        "receipt_policy": operation.receipt_policy,
                        "settlement_policy": operation.settlement_policy,
                        "price": _encode_inline_price_definition(operation.price),
                        "price_ref": operation.price_ref,
                        "api_endpoints": [
                            {
                                "endpoint_ref": endpoint.endpoint_ref,
                                "api_ref": endpoint.api_ref,
                                "source_path": endpoint.source_path,
                            }
                            for endpoint in operation.api_endpoints
                        ],
                        "api_views": [
                            {
                                "view_ref": view.view_ref,
                                "source_path": view.source_path,
                            }
                            for view in operation.api_views
                        ],
                        "role_requirements": [
                            {
                                "role_ref": requirement.role_ref,
                                "access_scope": requirement.access_scope,
                                "scope_kind": requirement.scope_kind,
                                "scope_ref": requirement.scope_ref,
                                "class_instance_identity_required": (
                                    requirement.class_instance_identity_required
                                ),
                                "role_assignment_binding_required": (
                                    requirement.role_assignment_binding_required
                                ),
                                "source_path": requirement.source_path,
                            }
                            for requirement in operation.role_requirements
                        ],
                    }
                    for operation in service_config.service_operation_configs
                ],
                "contract_configs": [
                    {
                        "name": contract_config.name,
                        "source_path": contract_config.source_path,
                        "default_kind": contract_config.default_kind,
                        "projection_experience_ref": contract_config.projection_experience_ref,
                        "operation_grants": [
                            {
                                "operation_ref": grant.operation_ref,
                                "access_scope": grant.access_scope,
                                "source_path": grant.source_path,
                            }
                            for grant in contract_config.operation_grants
                        ],
                        "actor_role_grants": [
                            {
                                "role_ref": grant.role_ref,
                                "access_scope": grant.access_scope,
                                "scope_kind": grant.scope_kind,
                                "scope_ref": grant.scope_ref,
                                "class_instance_identity_required": (
                                    grant.class_instance_identity_required
                                ),
                                "role_assignment_binding_required": (
                                    grant.role_assignment_binding_required
                                ),
                                "source_path": grant.source_path,
                            }
                            for grant in contract_config.actor_role_grants
                        ],
                    }
                    for contract_config in service_config.contract_configs
                ],
            }
            for service_config in plan.service_configs
        ],
    }


def _encode_inline_price_definition(
    price: ServiceInlinePriceDefinition | None,
) -> dict[str, object] | None:
    if price is None:
        return None
    return {
        "coin_symbol": price.coin_symbol,
        "price_type": price.price_type,
        "effective_from": price.effective_from,
        "fixed_amount": (
            canonical_decimal_text(price.fixed_amount)
            if price.fixed_amount is not None
            else None
        ),
        "markup_percentage": (
            canonical_decimal_text(price.markup_percentage)
            if price.markup_percentage is not None
            else None
        ),
        "effective_until": price.effective_until,
        "policy_fail_closed": price.policy_fail_closed,
    }


def _encode_activation_plan(*, plan: ServiceActivationPlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "service_surface": plan.service_surface,
        "activation_mode": plan.activation_mode,
        "materialize_on_start": plan.materialize_on_start,
        "compile_plan_artifact": {
            "relpath": plan.compile_plan_artifact_relpath,
            "hash_sha256": plan.compile_plan_artifact_hash_sha256,
        },
        "service_package_lock": (
            {
                "service_package_id": str(plan.service_package_id),
                "service_package_object_instance_graph_commit_id": str(
                    plan.service_package_object_instance_graph_commit_id
                ),
            }
            if plan.service_package_id is not None
            and plan.service_package_object_instance_graph_commit_id is not None
            else None
        ),
        "dependency_pins": [
            {
                "package_name": dependency.package_name,
                "version_number": dependency.version_number,
                "kind": dependency.kind,
                **_encode_service_protocol_dependency_lock(dependency),
            }
            for dependency in plan.dependency_pins
        ],
    }


def _encode_service_protocol_dependency_lock(
    dependency: ServiceActivationDependencyPin,
) -> dict[str, object]:
    if dependency.kind != "api_service_protocol":
        return {}
    coordinates = (
        dependency.service_package_provided_api_package_id,
        dependency.api_package_id,
        dependency.api_package_object_instance_graph_commit_id,
        dependency.service_protocol_package_id,
        dependency.service_protocol_code_package_id,
        dependency.service_protocol_code_package_object_instance_graph_commit_id,
        dependency.service_protocol_plan_hash_sha256,
    )
    if all(value is None for value in coordinates):
        return {}
    if any(value is None for value in coordinates):
        raise RuntimeError(
            "Committed Service protocol activation lock requires complete relational "
            f"coordinates: package_name={dependency.package_name!r}"
        )
    return {
        "service_package_provided_api_package_id": str(
            dependency.service_package_provided_api_package_id
        ),
        "api_package_id": str(dependency.api_package_id),
        "api_package_object_instance_graph_commit_id": str(
            dependency.api_package_object_instance_graph_commit_id
        ),
        "service_protocol_package_id": str(dependency.service_protocol_package_id),
        "service_protocol_code_package_id": str(
            dependency.service_protocol_code_package_id
        ),
        "service_protocol_code_package_object_instance_graph_commit_id": str(
            dependency.service_protocol_code_package_object_instance_graph_commit_id
        ),
        "service_protocol_plan_hash_sha256": (
            dependency.service_protocol_plan_hash_sha256
        ),
    }


__all__ = [
    "ServiceActivationDependencyPin",
    "ServiceActivationPlan",
    "ServiceActivationPlanArtifact",
    "ServiceActivationProtocolLock",
    "ServiceCompilePlan",
    "ServiceCompilePlanArtifact",
    "build_service_activation_plan",
    "build_service_compile_plan",
    "emit_service_activation_plan_artifact",
    "emit_service_compile_plan_artifact",
]
