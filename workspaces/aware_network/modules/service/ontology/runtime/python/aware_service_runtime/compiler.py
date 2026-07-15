from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import TypedDict

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_types import decimal_value


from .models import (
    ServiceApiOwnership,
    ServiceApiProjectionOwnership,
    ServiceCodePackageConfigOwnership,
    ServiceContractActorRoleGrantOwnership,
    ServiceContractConfigOwnership,
    ServiceContractOperationGrantOwnership,
    ServiceExperienceOwnership,
    ServiceInlinePriceDefinition,
    ServiceOperationApiViewOwnership,
    ServiceOperationEndpointOwnership,
    ServiceOperationOwnership,
    ServiceOperationRoleRequirementOwnership,
    ServiceOwnership,
)

_SUPPORTED_SERVICE_OPERATION_ADMISSION_MODES = {
    "contract_and_permit_required",
    "contract_required",
    "identity_required",
    "metered_settlement_required",
    "public_read",
}
_SUPPORTED_SERVICE_CODE_PACKAGE_CARDINALITIES = {"many", "one"}


class _ServiceRoleGateDefinition(TypedDict):
    access_scope: str
    scope_kind: str
    scope_ref: str
    class_instance_identity_required: bool
    role_assignment_binding_required: bool


def load_service_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[ServiceOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    service_by_name: dict[str, ServiceOwnership] = {}

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="service source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        if tree.root_node.has_error:
            raise ValueError(f"Service source {source_path} has parse errors")

        for node in tree.root_node.named_children:
            if node.type != "service_def":
                continue
            service_name = _symbol_key(_field_text(node, "name"))
            if not service_name:
                raise ValueError(f"Service declaration has empty name in {source_path}")
            if service_name in service_by_name:
                raise ValueError(
                    f"Duplicate service declaration {service_name!r} across service sources"
                )

            apis_by_ref: dict[str, ServiceApiOwnership] = {}
            experiences_by_ref: dict[str, ServiceExperienceOwnership] = {}
            code_package_configs_by_slot: dict[
                str, ServiceCodePackageConfigOwnership
            ] = {}
            operations_by_name: dict[str, ServiceOperationOwnership] = {}
            contract_configs_by_name: dict[str, ServiceContractConfigOwnership] = {}

            for child in _iter_service_children(node=node):
                if child.type == "service_api_decl":
                    api_ref = _qualified_text(child.child_by_field_name("api"))
                    if not api_ref:
                        raise ValueError(
                            f"Service declaration {service_name!r} has api declaration "
                            + f"with empty target in {source_path}"
                        )
                    api_key = api_ref.casefold()
                    if api_key in apis_by_ref:
                        raise ValueError(
                            f"Service declaration {service_name!r} has duplicate "
                            + f"api binding {api_ref!r} in {source_path}"
                        )
                    api_projections_by_ref: dict[str, ServiceApiProjectionOwnership] = (
                        {}
                    )
                    for api_child in _iter_service_api_children(node=child):
                        if api_child.type != "service_api_projection_decl":
                            continue
                        projection_ref = _qualified_text(
                            api_child.child_by_field_name("projection")
                        )
                        if not projection_ref:
                            raise ValueError(
                                f"Service declaration {service_name!r} api {api_ref!r} has projection "
                                + f"with empty target in {source_path}"
                            )
                        projection_key = projection_ref.casefold()
                        if projection_key in api_projections_by_ref:
                            raise ValueError(
                                f"Service declaration {service_name!r} api {api_ref!r} has duplicate "
                                + f"projection {projection_ref!r} in {source_path}"
                            )
                        api_projections_by_ref[projection_key] = (
                            ServiceApiProjectionOwnership(
                                projection_ref=projection_ref,
                                source_path=source_rel,
                            )
                        )
                    apis_by_ref[api_key] = ServiceApiOwnership(
                        api_ref=api_ref,
                        source_path=source_rel,
                        api_projections=tuple(
                            sorted(
                                api_projections_by_ref.values(),
                                key=lambda item: (
                                    item.projection_ref,
                                    item.source_path,
                                ),
                            )
                        ),
                    )
                    continue

                if child.type == "service_experience_decl":
                    experience_ref = _qualified_text(
                        child.child_by_field_name("experience")
                    )
                    if not experience_ref:
                        raise ValueError(
                            f"Service declaration {service_name!r} has experience declaration "
                            + f"with empty target in {source_path}"
                        )
                    experience_key = experience_ref.casefold()
                    if experience_key in experiences_by_ref:
                        raise ValueError(
                            f"Service declaration {service_name!r} has duplicate "
                            + f"experience binding {experience_ref!r} in {source_path}"
                        )
                    experiences_by_ref[experience_key] = ServiceExperienceOwnership(
                        experience_ref=experience_ref,
                        source_path=source_rel,
                    )
                    continue

                if child.type == "service_code_package_config_decl":
                    code_package_config = _load_service_code_package_config_definition(
                        node=child,
                        service_name=service_name,
                        source_path=source_path,
                        source_rel=source_rel,
                    )
                    slot_key = code_package_config.slot_key.casefold()
                    if slot_key in code_package_configs_by_slot:
                        raise ValueError(
                            f"Service declaration {service_name!r} has duplicate "
                            + f"package slot {code_package_config.slot_key!r} in {source_path}"
                        )
                    code_package_configs_by_slot[slot_key] = code_package_config
                    continue

                if child.type == "service_operation_def":
                    operation = _load_service_operation_definition(
                        node=child,
                        service_name=service_name,
                        source_path=source_path,
                        source_rel=source_rel,
                        declared_api_refs=tuple(
                            api.api_ref for api in apis_by_ref.values()
                        ),
                    )
                    operation_key = operation.name.casefold()
                    if operation_key in operations_by_name:
                        raise ValueError(
                            f"Service declaration {service_name!r} has duplicate "
                            + f"operation {operation.name!r} in {source_path}"
                        )
                    operations_by_name[operation_key] = operation
                    continue

                if child.type == "service_contract_config_def":
                    contract_config = _load_service_contract_config_definition(
                        node=child,
                        service_name=service_name,
                        source_path=source_path,
                        source_rel=source_rel,
                    )
                    contract_key = contract_config.name.casefold()
                    if contract_key in contract_configs_by_name:
                        raise ValueError(
                            f"Service declaration {service_name!r} has duplicate "
                            + f"contract config {contract_config.name!r} in {source_path}"
                        )
                    contract_configs_by_name[contract_key] = contract_config

            if not apis_by_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} must include at least one api in {source_path}"
                )
            if not operations_by_name:
                raise ValueError(
                    f"Service declaration {service_name!r} must include at least one operation in {source_path}"
                )

            for contract_config in contract_configs_by_name.values():
                for operation_grant in contract_config.operation_grants:
                    operation_ref_key = _symbol_key(
                        operation_grant.operation_ref
                    ).casefold()
                    if operation_ref_key not in operations_by_name:
                        raise ValueError(
                            f"Service declaration {service_name!r} contract {contract_config.name!r} "
                            + f"grants unknown operation {operation_grant.operation_ref!r} in {source_path}"
                        )

            service_by_name[service_name] = ServiceOwnership(
                name=service_name,
                source_path=source_rel,
                apis=tuple(
                    sorted(
                        apis_by_ref.values(),
                        key=lambda item: (item.api_ref, item.source_path),
                    )
                ),
                experiences=tuple(
                    sorted(
                        experiences_by_ref.values(),
                        key=lambda item: (item.experience_ref, item.source_path),
                    )
                ),
                operations=tuple(
                    sorted(
                        operations_by_name.values(),
                        key=lambda item: (item.name, item.source_path),
                    )
                ),
                code_package_configs=tuple(
                    sorted(
                        code_package_configs_by_slot.values(),
                        key=lambda item: (item.slot_key, item.source_path),
                    )
                ),
                contract_configs=tuple(
                    sorted(
                        contract_configs_by_name.values(),
                        key=lambda item: (item.name, item.source_path),
                    )
                ),
            )

    return tuple(
        sorted(service_by_name.values(), key=lambda item: (item.name, item.source_path))
    )


def _load_service_code_package_config_definition(
    *,
    node: Node,
    service_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceCodePackageConfigOwnership:
    slot_key = _symbol_key(_field_text(node, "slot")).casefold()
    if not slot_key:
        raise ValueError(
            f"Service declaration {service_name!r} has package slot with empty name in {source_path}"
        )

    manifest_kind: str | None = None
    surface: str | None = None
    cardinality = "many"
    required = False
    saw_manifest_kind = False
    saw_surface = False
    saw_cardinality = False
    saw_required = False

    for child in _iter_service_code_package_config_children(node=node):
        if child.type == "service_code_package_config_manifest_decl":
            if saw_manifest_kind:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has duplicate manifest "
                    + f"in {source_path}"
                )
            saw_manifest_kind = True
            manifest_kind = _symbol_key(_field_text(child, "manifest_kind")).casefold()
            if not manifest_kind:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has empty manifest "
                    + f"in {source_path}"
                )
            continue

        if child.type == "service_code_package_config_surface_decl":
            if saw_surface:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has duplicate surface "
                    + f"in {source_path}"
                )
            saw_surface = True
            surface = _symbol_key(_field_text(child, "surface")).casefold()
            if not surface:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has empty surface "
                    + f"in {source_path}"
                )
            continue

        if child.type == "service_code_package_config_cardinality_decl":
            if saw_cardinality:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has duplicate cardinality "
                    + f"in {source_path}"
                )
            saw_cardinality = True
            cardinality = _symbol_key(_field_text(child, "cardinality")).casefold()
            if cardinality not in _SUPPORTED_SERVICE_CODE_PACKAGE_CARDINALITIES:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has unsupported cardinality "
                    + f"{cardinality!r} in {source_path}"
                )
            continue

        if child.type == "service_code_package_config_required_decl":
            if saw_required:
                raise ValueError(
                    f"Service declaration {service_name!r} package {slot_key!r} has duplicate required "
                    + f"in {source_path}"
                )
            saw_required = True
            required = _parse_service_boolean_literal(
                node=child.child_by_field_name("required"),
                field_name="required",
                service_name=service_name,
                block_name=f"package {slot_key}",
                source_path=source_path,
            )

    if manifest_kind is None:
        raise ValueError(
            f"Service declaration {service_name!r} package {slot_key!r} must declare manifest in {source_path}"
        )
    if surface is None:
        raise ValueError(
            f"Service declaration {service_name!r} package {slot_key!r} must declare surface in {source_path}"
        )
    return ServiceCodePackageConfigOwnership(
        slot_key=slot_key,
        manifest_kind=manifest_kind,
        surface=surface,
        cardinality=cardinality,
        required=required,
        source_path=source_rel,
    )


def _load_service_operation_definition(
    *,
    node: Node,
    service_name: str,
    source_path: Path,
    source_rel: str,
    declared_api_refs: tuple[str, ...],
) -> ServiceOperationOwnership:
    operation_name = _symbol_key(_field_text(node, "operation_name"))
    if not operation_name:
        raise ValueError(
            f"Service declaration {service_name!r} has operation with empty name in {source_path}"
        )

    endpoint_bindings_by_ref: dict[str, ServiceOperationEndpointOwnership] = {}
    view_bindings_by_ref: dict[str, ServiceOperationApiViewOwnership] = {}
    role_requirements_by_key: dict[
        tuple[str, str, str, str], ServiceOperationRoleRequirementOwnership
    ] = {}
    receipt_policy = "committed"
    saw_receipt_policy = False
    settlement_policy = "none"
    saw_settlement_policy = False
    admission_mode: str | None = None
    saw_admission_mode = False
    operation_price: ServiceInlinePriceDefinition | None = None
    operation_price_ref: str | None = None
    for child in _iter_service_operation_children(node=node):
        if child.type == "service_operation_endpoint_def":
            endpoint_ref = _qualified_text(child.child_by_field_name("endpoint"))
            if not endpoint_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has endpoint with empty ref in {source_path}"
                )
            if len(endpoint_ref.split(".")) < 3:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has invalid endpoint ref "
                    + f"{endpoint_ref!r} in {source_path}; expected api.capability.endpoint"
                )
            if (
                _resolve_declared_api_ref(
                    endpoint_ref=endpoint_ref, declared_api_refs=declared_api_refs
                )
                is None
            ):
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} references undeclared api "
                    + f"endpoint {endpoint_ref!r} in {source_path}"
                )
            endpoint_key = endpoint_ref.casefold()
            if endpoint_key in endpoint_bindings_by_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate endpoint binding "
                    + f"{endpoint_ref!r} in {source_path}"
                )
            endpoint_bindings_by_ref[endpoint_key] = ServiceOperationEndpointOwnership(
                endpoint_ref=endpoint_ref,
                source_path=source_rel,
            )
            continue

        if child.type == "service_operation_view_def":
            view_binding = _load_service_operation_view_definition(
                node=child,
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            view_key = view_binding.view_ref.casefold()
            if view_key in view_bindings_by_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate view binding {view_binding.view_ref!r} in {source_path}"
                )
            view_bindings_by_ref[view_key] = view_binding
            continue

        if child.type == "service_operation_role_requirement_def":
            role_requirement = _load_service_operation_role_requirement_definition(
                node=child,
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            role_key = (
                role_requirement.role_ref.casefold(),
                role_requirement.access_scope.casefold(),
                role_requirement.scope_kind.casefold(),
                role_requirement.scope_ref.casefold(),
            )
            if role_key in role_requirements_by_key:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate role requirement {role_requirement.role_ref!r} "
                    + f"in {source_path}"
                )
            role_requirements_by_key[role_key] = role_requirement
            continue

        if child.type == "service_operation_admission_policy_decl":
            if saw_admission_mode:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate admission "
                    + f"policy in {source_path}"
                )
            saw_admission_mode = True
            admission_mode = _symbol_key(
                _field_text(child, "admission_mode")
            ).casefold()
            if admission_mode not in _SUPPORTED_SERVICE_OPERATION_ADMISSION_MODES:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has unsupported admission "
                    + f"mode {admission_mode!r} in {source_path}"
                )
            continue

        if child.type == "service_operation_receipt_policy_decl":
            if saw_receipt_policy:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate receipt "
                    + f"policy in {source_path}"
                )
            saw_receipt_policy = True
            receipt_policy = _symbol_key(
                _field_text(child, "receipt_policy")
            ).casefold()
            if receipt_policy not in {"committed", "read_model"}:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has unsupported receipt "
                    + f"policy {receipt_policy!r} in {source_path}"
                )
            continue

        if child.type == "service_operation_settlement_decl":
            if saw_settlement_policy:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate settlement "
                    + f"policy in {source_path}"
                )
            saw_settlement_policy = True
            settlement_policy = _symbol_key(
                _field_text(child, "settlement_policy")
            ).casefold()
            if settlement_policy not in {
                "none",
                "reserve_before_execute",
                "reserve_and_finalize",
            }:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has unsupported settlement "
                    + f"policy {settlement_policy!r} in {source_path}"
                )
            continue

        if child.type != "service_operation_price_def":
            continue

        price_body = child.child_by_field_name("body")
        if price_body is not None:
            if operation_price is not None or operation_price_ref is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price binding "
                    + f"in {source_path}"
                )
            operation_price = _load_service_inline_price_definition(
                node=child,
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        price_ref = _qualified_text(child.child_by_field_name("price"))
        if not price_ref:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} "
                + f"has price with empty ref in {source_path}"
            )
        if operation_price is not None or operation_price_ref is not None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price binding "
                + f"{price_ref!r} in {source_path}"
            )
        operation_price_ref = price_ref

    if not endpoint_bindings_by_ref and not view_bindings_by_ref:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"must include at least one endpoint or API view in {source_path}"
        )
    has_price = operation_price is not None or operation_price_ref is not None
    resolved_admission_mode = (
        admission_mode
        or _default_service_operation_admission_mode(
            receipt_policy=receipt_policy,
            settlement_policy=settlement_policy,
            has_price=has_price,
        )
    )
    _validate_service_operation_admission_mode(
        admission_mode=resolved_admission_mode,
        explicit=saw_admission_mode,
        receipt_policy=receipt_policy,
        settlement_policy=settlement_policy,
        has_price=has_price,
        service_name=service_name,
        operation_name=operation_name,
        source_path=source_path,
    )

    return ServiceOperationOwnership(
        name=operation_name,
        source_path=source_rel,
        api_endpoints=tuple(
            sorted(
                endpoint_bindings_by_ref.values(),
                key=lambda item: (item.endpoint_ref, item.source_path),
            )
        ),
        api_views=tuple(
            sorted(
                view_bindings_by_ref.values(),
                key=lambda item: (item.view_ref, item.source_path),
            )
        ),
        role_requirements=tuple(
            sorted(
                role_requirements_by_key.values(),
                key=lambda item: (
                    item.role_ref,
                    item.access_scope,
                    item.scope_kind,
                    item.scope_ref,
                ),
            )
        ),
        admission_mode=resolved_admission_mode,
        fulfillment_kind=_default_service_operation_fulfillment_kind(
            receipt_policy=receipt_policy
        ),
        receipt_policy=receipt_policy,
        settlement_policy=settlement_policy,
        price=operation_price,
        price_ref=operation_price_ref,
    )


def _default_service_operation_admission_mode(
    *, receipt_policy: str, settlement_policy: str, has_price: bool
) -> str:
    if receipt_policy == "read_model" and settlement_policy == "none" and not has_price:
        return "public_read"
    return "contract_required"


def _default_service_operation_fulfillment_kind(*, receipt_policy: str) -> str:
    if receipt_policy == "read_model":
        return "view"
    return "coordination"


def _validate_service_operation_admission_mode(
    *,
    admission_mode: str,
    explicit: bool,
    receipt_policy: str,
    settlement_policy: str,
    has_price: bool,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> None:
    if admission_mode == "public_read":
        if receipt_policy != "read_model":
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} has public_read admission "
                + f"with receipt policy {receipt_policy!r} in {source_path}; public reads must use read_model"
            )
        if settlement_policy != "none" or has_price:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} has public_read admission "
                + f"with settlement/price policy in {source_path}"
            )
        return
    if (
        admission_mode == "metered_settlement_required"
        and explicit
        and settlement_policy == "none"
    ):
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} has metered_settlement_required "
            + f"admission without a settlement policy in {source_path}"
        )


def _load_service_operation_view_definition(
    *,
    node: Node,
    service_name: str,
    operation_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceOperationApiViewOwnership:
    view_ref = _qualified_text(node.child_by_field_name("view"))
    if not view_ref:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"has view with empty ref in {source_path}"
        )
    if len([part for part in view_ref.split(".") if part.strip()]) < 2:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"has invalid API view ref {view_ref!r} in {source_path}; expected api_view_ref"
        )

    if node.child_by_field_name("body") is not None:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"uses retired nested view provider syntax in {source_path}; "
            + f"use `view {view_ref}` because the owning service operation fulfills the ApiView"
        )

    return ServiceOperationApiViewOwnership(
        view_ref=view_ref,
        source_path=source_rel,
    )


def _load_service_operation_role_requirement_definition(
    *,
    node: Node,
    service_name: str,
    operation_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceOperationRoleRequirementOwnership:
    role_ref = _qualified_text(node.child_by_field_name("role"))
    if not role_ref:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"has role requirement with empty role ref in {source_path}"
        )
    gate = _load_service_role_gate_definition(
        node=node,
        service_name=service_name,
        operation_name=operation_name,
        source_path=source_path,
        default_access_scope="operation",
        default_scope_kind="operation",
        default_scope_ref=operation_name,
    )
    return ServiceOperationRoleRequirementOwnership(
        role_ref=role_ref,
        source_path=source_rel,
        access_scope=gate["access_scope"],
        scope_kind=gate["scope_kind"],
        scope_ref=gate["scope_ref"],
        class_instance_identity_required=gate["class_instance_identity_required"],
        role_assignment_binding_required=gate["role_assignment_binding_required"],
    )


def _load_service_contract_config_definition(
    *,
    node: Node,
    service_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceContractConfigOwnership:
    contract_name = _symbol_key(_field_text(node, "name"))
    if not contract_name:
        raise ValueError(
            f"Service declaration {service_name!r} has contract with empty name in {source_path}"
        )

    default_kind = "subscription"
    projection_experience_ref: str | None = None
    saw_kind = False
    saw_projection_experience = False
    operation_grants_by_ref: dict[str, ServiceContractOperationGrantOwnership] = {}
    actor_role_grants_by_key: dict[
        tuple[str, str, str, str],
        ServiceContractActorRoleGrantOwnership,
    ] = {}

    for child in _iter_service_contract_config_children(node=node):
        if child.type == "service_contract_kind_decl":
            if saw_kind:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has duplicate kind in {source_path}"
                )
            saw_kind = True
            default_kind = _symbol_key(_field_text(child, "contract_kind")).casefold()
            if default_kind not in {"metered", "one_time", "subscription"}:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has unsupported kind {default_kind!r} in {source_path}"
                )
            continue

        if child.type == "service_contract_projection_experience_decl":
            if saw_projection_experience:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has duplicate projection_experience in {source_path}"
                )
            saw_projection_experience = True
            projection_experience_ref = _qualified_text(
                child.child_by_field_name("projection_experience")
            )
            if not projection_experience_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has empty projection_experience in {source_path}"
                )
            continue

        if child.type == "service_contract_operation_grant_def":
            operation_grant = _load_service_contract_operation_grant_definition(
                node=child,
                service_name=service_name,
                contract_name=contract_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            operation_key = _symbol_key(operation_grant.operation_ref).casefold()
            if operation_key in operation_grants_by_ref:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has duplicate operation grant {operation_grant.operation_ref!r} "
                    + f"in {source_path}"
                )
            operation_grants_by_ref[operation_key] = operation_grant
            continue

        if child.type == "service_contract_actor_role_grant_def":
            actor_role_grant = _load_service_contract_actor_role_grant_definition(
                node=child,
                service_name=service_name,
                contract_name=contract_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            actor_role_key = (
                actor_role_grant.role_ref.casefold(),
                actor_role_grant.access_scope.casefold(),
                actor_role_grant.scope_kind.casefold(),
                actor_role_grant.scope_ref.casefold(),
            )
            if actor_role_key in actor_role_grants_by_key:
                raise ValueError(
                    f"Service declaration {service_name!r} contract {contract_name!r} "
                    + f"has duplicate actor_role grant {actor_role_grant.role_ref!r} "
                    + f"in {source_path}"
                )
            actor_role_grants_by_key[actor_role_key] = actor_role_grant

    return ServiceContractConfigOwnership(
        name=contract_name,
        source_path=source_rel,
        default_kind=default_kind,
        projection_experience_ref=projection_experience_ref,
        operation_grants=tuple(
            sorted(
                operation_grants_by_ref.values(),
                key=lambda item: (item.operation_ref, item.source_path),
            )
        ),
        actor_role_grants=tuple(
            sorted(
                actor_role_grants_by_key.values(),
                key=lambda item: (
                    item.role_ref,
                    item.access_scope,
                    item.scope_kind,
                    item.scope_ref,
                ),
            )
        ),
    )


def _load_service_contract_operation_grant_definition(
    *,
    node: Node,
    service_name: str,
    contract_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceContractOperationGrantOwnership:
    operation_ref = _qualified_text(node.child_by_field_name("operation"))
    if not operation_ref:
        raise ValueError(
            f"Service declaration {service_name!r} contract {contract_name!r} "
            + f"has operation grant with empty operation ref in {source_path}"
        )

    access_scope = "operation"
    saw_access = False
    for child in _iter_service_contract_operation_grant_children(node=node):
        if child.type != "service_role_access_decl":
            continue
        if saw_access:
            raise ValueError(
                f"Service declaration {service_name!r} contract {contract_name!r} "
                + f"operation grant {operation_ref!r} has duplicate access in {source_path}"
            )
        saw_access = True
        access_scope = _symbol_key(_field_text(child, "access_scope")).casefold()
        if not access_scope:
            raise ValueError(
                f"Service declaration {service_name!r} contract {contract_name!r} "
                + f"operation grant {operation_ref!r} has empty access in {source_path}"
            )

    return ServiceContractOperationGrantOwnership(
        operation_ref=operation_ref,
        source_path=source_rel,
        access_scope=access_scope,
    )


def _load_service_contract_actor_role_grant_definition(
    *,
    node: Node,
    service_name: str,
    contract_name: str,
    source_path: Path,
    source_rel: str,
) -> ServiceContractActorRoleGrantOwnership:
    role_ref = _qualified_text(node.child_by_field_name("role"))
    if not role_ref:
        raise ValueError(
            f"Service declaration {service_name!r} contract {contract_name!r} "
            + f"has actor_role grant with empty role ref in {source_path}"
        )
    gate = _load_service_role_gate_definition(
        node=node,
        service_name=service_name,
        operation_name=f"contract {contract_name}",
        source_path=source_path,
        default_access_scope="service",
        default_scope_kind="service",
        default_scope_ref="default",
    )
    return ServiceContractActorRoleGrantOwnership(
        role_ref=role_ref,
        source_path=source_rel,
        access_scope=gate["access_scope"],
        scope_kind=gate["scope_kind"],
        scope_ref=gate["scope_ref"],
        class_instance_identity_required=gate["class_instance_identity_required"],
        role_assignment_binding_required=gate["role_assignment_binding_required"],
    )


def _load_service_role_gate_definition(
    *,
    node: Node,
    service_name: str,
    operation_name: str,
    source_path: Path,
    default_access_scope: str,
    default_scope_kind: str,
    default_scope_ref: str,
) -> _ServiceRoleGateDefinition:
    access_scope = default_access_scope
    scope_kind = default_scope_kind
    scope_ref = default_scope_ref
    class_instance_identity_required = False
    role_assignment_binding_required = True
    saw_access = False
    saw_scope = False
    saw_class_instance_identity_required = False
    saw_role_assignment_binding_required = False

    for child in _iter_service_role_gate_children(node=node):
        if child.type == "service_role_access_decl":
            if saw_access:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate role access in {source_path}"
                )
            saw_access = True
            access_scope = _symbol_key(_field_text(child, "access_scope")).casefold()
            if not access_scope:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has empty role access in {source_path}"
                )
            continue

        if child.type == "service_role_scope_decl":
            if saw_scope:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate role scope in {source_path}"
                )
            saw_scope = True
            scope_kind = _symbol_key(_field_text(child, "scope_kind")).casefold()
            scope_ref = _field_text(child, "scope_ref") or "default"
            if not scope_kind:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has empty role scope kind in {source_path}"
                )
            continue

        if child.type == "service_role_class_instance_identity_required_decl":
            if saw_class_instance_identity_required:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate class_instance_identity_required in {source_path}"
                )
            saw_class_instance_identity_required = True
            class_instance_identity_required = _parse_boolean_literal(
                node=child.child_by_field_name("class_instance_identity_required"),
                field_name="class_instance_identity_required",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        if child.type == "service_role_assignment_binding_required_decl":
            if saw_role_assignment_binding_required:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} "
                    + f"has duplicate role_assignment_binding_required in {source_path}"
                )
            saw_role_assignment_binding_required = True
            role_assignment_binding_required = _parse_boolean_literal(
                node=child.child_by_field_name("role_assignment_binding_required"),
                field_name="role_assignment_binding_required",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )

    return {
        "access_scope": access_scope,
        "scope_kind": scope_kind,
        "scope_ref": scope_ref,
        "class_instance_identity_required": class_instance_identity_required,
        "role_assignment_binding_required": role_assignment_binding_required,
    }


def _load_service_inline_price_definition(
    *,
    node: Node,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> ServiceInlinePriceDefinition:
    coin_symbol: str | None = None
    price_type: str | None = None
    fixed_amount: Decimal | None = None
    markup_percentage: Decimal | None = None
    effective_from: str | None = None
    effective_until: str | None = None
    policy_fail_closed = True
    saw_policy = False

    for child in _iter_service_operation_price_children(node=node):
        if child.type == "service_operation_price_coin_decl":
            if coin_symbol is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price coin "
                    + f"in {source_path}"
                )
            coin_symbol = _symbol_key(_field_text(child, "coin_symbol")).upper()
            if not coin_symbol:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has empty price coin "
                    + f"in {source_path}"
                )
            continue

        if child.type == "service_operation_price_type_decl":
            if price_type is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price type "
                    + f"in {source_path}"
                )
            price_type = _symbol_key(_field_text(child, "price_type")).casefold()
            if price_type not in {"fixed", "dynamic"}:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has unsupported price type "
                    + f"{price_type!r} in {source_path}"
                )
            continue

        if child.type == "service_operation_price_fixed_amount_decl":
            if fixed_amount is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate fixed_amount "
                    + f"in {source_path}"
                )
            fixed_amount = _parse_decimal_literal(
                node=child.child_by_field_name("fixed_amount"),
                field_name="fixed_amount",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        if child.type == "service_operation_price_markup_percentage_decl":
            if markup_percentage is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate "
                    + f"markup_percentage in {source_path}"
                )
            markup_percentage = _parse_decimal_literal(
                node=child.child_by_field_name("markup_percentage"),
                field_name="markup_percentage",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        if child.type == "service_operation_price_effective_from_decl":
            if effective_from is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate "
                    + f"effective_from in {source_path}"
                )
            effective_from = _parse_datetime_literal(
                node=child.child_by_field_name("effective_from"),
                field_name="effective_from",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        if child.type == "service_operation_price_effective_until_decl":
            if effective_until is not None:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate "
                    + f"effective_until in {source_path}"
                )
            effective_until = _parse_datetime_literal(
                node=child.child_by_field_name("effective_until"),
                field_name="effective_until",
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            continue

        if child.type == "service_operation_price_policy_def":
            if saw_policy:
                raise ValueError(
                    f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price policy "
                    + f"in {source_path}"
                )
            saw_policy = True
            policy_fail_closed = _load_service_inline_price_policy(
                node=child,
                service_name=service_name,
                operation_name=operation_name,
                source_path=source_path,
            )

    if not coin_symbol:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price requires coin in {source_path}"
        )
    if price_type is None:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price requires type in {source_path}"
        )
    if effective_from is None:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price requires effective_from "
            + f"in {source_path}"
        )

    effective_from_value = _parse_iso_datetime_text(
        effective_from,
        field_name="effective_from",
        service_name=service_name,
        operation_name=operation_name,
        source_path=source_path,
    )
    effective_until_value: datetime | None = None
    if effective_until is not None:
        effective_until_value = _parse_iso_datetime_text(
            effective_until,
            field_name="effective_until",
            service_name=service_name,
            operation_name=operation_name,
            source_path=source_path,
        )
        if effective_until_value < effective_from_value:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} has effective_until before "
                + f"effective_from in {source_path}"
            )

    if price_type == "fixed":
        if fixed_amount is None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} fixed price requires "
                + f"fixed_amount in {source_path}"
            )
        if markup_percentage is not None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} fixed price must not include "
                + f"markup_percentage in {source_path}"
            )
    elif price_type == "dynamic":
        if markup_percentage is None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} dynamic price requires "
                + f"markup_percentage in {source_path}"
            )
        if fixed_amount is not None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} dynamic price must not include "
                + f"fixed_amount in {source_path}"
            )

    return ServiceInlinePriceDefinition(
        coin_symbol=coin_symbol,
        price_type=price_type,
        effective_from=effective_from,
        fixed_amount=fixed_amount,
        markup_percentage=markup_percentage,
        effective_until=effective_until,
        policy_fail_closed=policy_fail_closed,
    )


def _load_service_inline_price_policy(
    *,
    node: Node,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> bool:
    fail_closed: bool | None = None
    for child in _iter_service_operation_price_policy_children(node=node):
        if child.type != "service_operation_price_policy_fail_closed_decl":
            continue
        if fail_closed is not None:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} has duplicate price "
                + f"policy fail_closed in {source_path}"
            )
        fail_closed = _parse_boolean_literal(
            node=child.child_by_field_name("fail_closed"),
            field_name="fail_closed",
            service_name=service_name,
            operation_name=operation_name,
            source_path=source_path,
        )
    return True if fail_closed is None else fail_closed


def _resolve_declared_api_ref(
    *, endpoint_ref: str, declared_api_refs: tuple[str, ...]
) -> str | None:
    matches = [
        api_ref
        for api_ref in declared_api_refs
        if endpoint_ref == api_ref or endpoint_ref.startswith(api_ref + ".")
    ]
    if not matches:
        return None
    return max(matches, key=len)


def _iter_service_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {
            "service_api_decl",
            "service_experience_decl",
            "service_code_package_config_decl",
            "service_operation_def",
            "service_contract_config_def",
        }:
            children.append(child)
            continue
        if child.type == "service_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_api_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_api_projection_decl":
            children.append(child)
            continue
        if child.type == "service_api_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_code_package_config_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type in {
            "service_code_package_config_manifest_decl",
            "service_code_package_config_surface_decl",
            "service_code_package_config_cardinality_decl",
            "service_code_package_config_required_decl",
        }:
            children.append(child)
            continue
        if child.type == "service_code_package_config_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_operation_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type in {
            "service_operation_endpoint_def",
            "service_operation_view_def",
            "service_operation_role_requirement_def",
            "service_operation_settlement_decl",
            "service_operation_price_def",
        }:
            children.append(child)
            continue
        if child.type == "service_operation_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_operation_view_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_operation_view_provider_decl":
            children.append(child)
            continue
        if child.type == "service_operation_view_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_role_gate_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type in {
            "service_role_access_decl",
            "service_role_scope_decl",
            "service_role_class_instance_identity_required_decl",
            "service_role_assignment_binding_required_decl",
        }:
            children.append(child)
            continue
        if child.type == "service_role_gate_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_contract_config_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type in {
            "service_contract_kind_decl",
            "service_contract_projection_experience_decl",
            "service_contract_operation_grant_def",
            "service_contract_actor_role_grant_def",
        }:
            children.append(child)
            continue
        if child.type == "service_contract_config_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_contract_operation_grant_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_role_access_decl":
            children.append(child)
            continue
        if child.type == "service_contract_operation_grant_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_operation_price_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type in {
            "service_operation_price_coin_decl",
            "service_operation_price_type_decl",
            "service_operation_price_fixed_amount_decl",
            "service_operation_price_markup_percentage_decl",
            "service_operation_price_effective_from_decl",
            "service_operation_price_effective_until_decl",
            "service_operation_price_policy_def",
        }:
            children.append(child)
            continue
        if child.type == "service_operation_price_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_service_operation_price_policy_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_operation_price_policy_fail_closed_decl":
            children.append(child)
            continue
        if child.type == "service_operation_price_policy_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _parse_decimal_literal(
    *,
    node: Node | None,
    field_name: str,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> Decimal:
    raw = _qualified_text(node)
    if not raw:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price {field_name} is empty "
            + f"in {source_path}"
        )
    try:
        return decimal_value(raw, field_name=field_name)
    except ValueError as exc:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} has invalid price {field_name} "
            + f"{raw!r} in {source_path}"
        ) from exc


def _parse_boolean_literal(
    *,
    node: Node | None,
    field_name: str,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> bool:
    raw = _qualified_text(node).casefold()
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise ValueError(
        f"Service declaration {service_name!r} operation {operation_name!r} has invalid {field_name} "
        + f"in {source_path}"
    )


def _parse_service_boolean_literal(
    *,
    node: Node | None,
    field_name: str,
    service_name: str,
    block_name: str,
    source_path: Path,
) -> bool:
    raw = _qualified_text(node).casefold()
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise ValueError(
        f"Service declaration {service_name!r} {block_name} has invalid {field_name} "
        + f"in {source_path}"
    )


def _parse_string_or_symbol_literal(
    *,
    node: Node | None,
    field_name: str,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> str:
    raw = _qualified_text(node)
    if not raw:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} "
            + f"has empty {field_name} in {source_path}"
        )
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} "
                + f"{field_name} must be a string literal or symbol in {source_path}"
            ) from exc
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Service declaration {service_name!r} operation {operation_name!r} "
                + f"{field_name} must be non-empty in {source_path}"
            )
        return value.strip()
    return raw.strip()


def _parse_datetime_literal(
    *,
    node: Node | None,
    field_name: str,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> str:
    raw = _qualified_text(node)
    if not raw:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price {field_name} is empty "
            + f"in {source_path}"
        )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price {field_name} must be "
            + f"a string literal in {source_path}"
        ) from exc
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price {field_name} must be "
            + f"a non-empty string literal in {source_path}"
        )
    return value.strip()


def _parse_iso_datetime_text(
    value: str,
    *,
    field_name: str,
    service_name: str,
    operation_name: str,
    source_path: Path,
) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Service declaration {service_name!r} operation {operation_name!r} price {field_name} must be "
            + f"an ISO-8601 timestamp in {source_path}"
        ) from exc


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} path must stay within package root: {candidate_resolved}"
    )


__all__ = [
    "load_service_ownership_from_sources",
]
