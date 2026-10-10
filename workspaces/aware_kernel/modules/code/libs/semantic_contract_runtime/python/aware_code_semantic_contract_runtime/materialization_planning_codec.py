"""Strict canonical codecs for Code materialization planning values."""

from __future__ import annotations

import json
from typing import cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticPackageCoordinate,
)
from .materialization_planning import (
    CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT,
    CODE_SEMANTIC_DEPENDENCY_DEMAND,
    CODE_SEMANTIC_DEPENDENCY_DEMAND_SET,
    CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT,
    CODE_SEMANTIC_MATERIALIZATION_INTENT,
    CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT,
    CodeComposedSemanticMaterializationIntent,
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticDependencyTargetConstraint,
)

_MAX_WIRE_BYTES = 1_000_000


def encode_code_semantic_materialization_intent(
    value: CodeSemanticMaterializationIntent,
) -> bytes:
    if type(value) is not CodeSemanticMaterializationIntent:
        raise TypeError("intent must be exact CodeSemanticMaterializationIntent")
    return _encode_admitted_wire(value.to_wire())


def decode_code_semantic_materialization_intent(
    wire: bytes,
) -> CodeSemanticMaterializationIntent:
    root = _decode_object(
        wire,
        {
            "contract",
            "intent_digest",
            "operation_kind",
            "requested_semantic_root_refs",
            "requested_terminal_output_roles",
            "semantic_configuration_coordinate",
        },
        "intent",
    )
    if (
        _text(root["contract"], "intent.contract")
        != CODE_SEMANTIC_MATERIALIZATION_INTENT
    ):
        raise ContractViolation("intent contract unsupported")
    result = CodeSemanticMaterializationIntent(
        operation_kind=_text(root["operation_kind"], "intent.operation_kind"),
        requested_semantic_root_refs=_text_tuple(
            root["requested_semantic_root_refs"],
            "intent.requested_semantic_root_refs",
        ),
        requested_terminal_output_roles=_text_tuple(
            root["requested_terminal_output_roles"],
            "intent.requested_terminal_output_roles",
        ),
        semantic_configuration_coordinate=_configuration(
            root["semantic_configuration_coordinate"],
            "intent.semantic_configuration_coordinate",
        ),
        intent_digest=ContentDigest.of_wire(
            root["intent_digest"], "intent.intent_digest"
        ),
    )
    if encode_code_semantic_materialization_intent(result) != wire:
        raise ContractViolation("intent wire is not canonical")
    return result


def encode_code_semantic_required_result_product(
    value: CodeSemanticRequiredResultProduct,
) -> bytes:
    if type(value) is not CodeSemanticRequiredResultProduct:
        raise TypeError("required result must be exact Code value")
    return _encode_admitted_wire(value.to_wire())


def decode_code_semantic_required_result_product(
    wire: bytes,
) -> CodeSemanticRequiredResultProduct:
    result = _required_product(
        _decode_object(
            wire,
            {"contract", "requirement_digest", "result_contract", "role"},
            "requirement",
        ),
        "requirement",
    )
    if encode_code_semantic_required_result_product(result) != wire:
        raise ContractViolation("required result wire is not canonical")
    return result


def encode_code_composed_semantic_materialization_intent(
    value: CodeComposedSemanticMaterializationIntent,
    *,
    target_package: SemanticPackageCoordinate,
    demands: tuple[SemanticDependencyDemand, ...],
) -> bytes:
    expected = CodeComposedSemanticMaterializationIntent.create(
        target_package=target_package, demands=demands
    )
    if type(value) is not CodeComposedSemanticMaterializationIntent:
        raise TypeError("composed intent must be exact Code value")
    value.__post_init__()
    value_wire = _encode_admitted_wire(value.to_wire())
    expected_wire = _encode_admitted_wire(expected.to_wire())
    if value_wire != expected_wire:
        raise ContractViolation("composed intent differs from exact demand context")
    return expected_wire


def decode_code_composed_semantic_materialization_intent(
    wire: bytes,
    *,
    target_package: SemanticPackageCoordinate,
    demands: tuple[SemanticDependencyDemand, ...],
) -> CodeComposedSemanticMaterializationIntent:
    root = _decode_object(
        wire,
        {
            "composed_intent",
            "composition_digest",
            "contract",
            "contributing_demand_digests",
            "contributing_intent_digests",
            "required_result_products",
            "target_package",
        },
        "composition",
    )
    if (
        _text(root["contract"], "composition.contract")
        != CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT
    ):
        raise ContractViolation("composition contract unsupported")
    expected = CodeComposedSemanticMaterializationIntent.create(
        target_package=target_package, demands=demands
    )
    if _encode_admitted_wire(expected.to_wire()) != wire:
        raise ContractViolation("composition differs from exact demand context")
    return expected


def encode_semantic_dependency_demand_set(
    value: SemanticDependencyDemandSet,
    *,
    package: SemanticPackageCoordinate,
    intent: CodeSemanticMaterializationIntent,
    profile_ref: str,
    profile_digest: ContentDigest,
    contract_profile_binding_digest: ContentDigest,
    planner_implementation_ref: str,
    planner_implementation_digest: ContentDigest,
    planner_configuration: SemanticConfigurationCoordinate,
) -> bytes:
    _validate_demand_set_context(
        value,
        package=package,
        intent=intent,
        profile_ref=profile_ref,
        profile_digest=profile_digest,
        contract_profile_binding_digest=contract_profile_binding_digest,
        planner_implementation_ref=planner_implementation_ref,
        planner_implementation_digest=planner_implementation_digest,
        planner_configuration=planner_configuration,
    )
    return _encode_admitted_wire(value.to_wire())


def decode_semantic_dependency_demand_set(
    wire: bytes,
    *,
    package: SemanticPackageCoordinate,
    intent: CodeSemanticMaterializationIntent,
    profile_ref: str,
    profile_digest: ContentDigest,
    contract_profile_binding_digest: ContentDigest,
    planner_implementation_ref: str,
    planner_implementation_digest: ContentDigest,
    planner_configuration: SemanticConfigurationCoordinate,
) -> SemanticDependencyDemandSet:
    root = _decode_object(
        wire,
        {
            "contract",
            "contract_profile_binding_digest",
            "demand_set_digest",
            "demands",
            "intent_digest",
            "package",
            "planner_implementation_digest",
            "planner_implementation_ref",
            "planner_configuration_digest",
            "planner_configuration_ref",
            "profile_digest",
            "profile_ref",
        },
        "demand_set",
    )
    if (
        _text(root["contract"], "demand_set.contract")
        != CODE_SEMANTIC_DEPENDENCY_DEMAND_SET
    ):
        raise ContractViolation("demand set contract unsupported")
    result = _unchecked_value(
        SemanticDependencyDemandSet,
        package=_package(root["package"], "demand_set.package"),
        intent_digest=ContentDigest.of_wire(
            root["intent_digest"], "demand_set.intent_digest"
        ),
        profile_ref=_text(root["profile_ref"], "demand_set.profile_ref"),
        profile_digest=ContentDigest.of_wire(
            root["profile_digest"], "demand_set.profile_digest"
        ),
        contract_profile_binding_digest=ContentDigest.of_wire(
            root["contract_profile_binding_digest"],
            "demand_set.contract_profile_binding_digest",
        ),
        planner_implementation_ref=_text(
            root["planner_implementation_ref"],
            "demand_set.planner_implementation_ref",
        ),
        planner_implementation_digest=ContentDigest.of_wire(
            root["planner_implementation_digest"],
            "demand_set.planner_implementation_digest",
        ),
        planner_configuration_ref=_text(
            root["planner_configuration_ref"],
            "demand_set.planner_configuration_ref",
        ),
        planner_configuration_digest=ContentDigest.of_wire(
            root["planner_configuration_digest"],
            "demand_set.planner_configuration_digest",
        ),
        demands=tuple(
            _demand(item, f"demand_set.demands[{index}]")
            for index, item in enumerate(_list(root["demands"], "demand_set.demands"))
        ),
        demand_set_digest=ContentDigest.of_wire(
            root["demand_set_digest"], "demand_set.demand_set_digest"
        ),
    )
    _validate_demand_set_context(
        result,
        package=package,
        intent=intent,
        profile_ref=profile_ref,
        profile_digest=profile_digest,
        contract_profile_binding_digest=contract_profile_binding_digest,
        planner_implementation_ref=planner_implementation_ref,
        planner_implementation_digest=planner_implementation_digest,
        planner_configuration=planner_configuration,
    )
    if (
        encode_semantic_dependency_demand_set(
            result,
            package=package,
            intent=intent,
            profile_ref=profile_ref,
            profile_digest=profile_digest,
            contract_profile_binding_digest=contract_profile_binding_digest,
            planner_implementation_ref=planner_implementation_ref,
            planner_implementation_digest=planner_implementation_digest,
            planner_configuration=planner_configuration,
        )
        != wire
    ):
        raise ContractViolation("demand set wire is not canonical")
    return result


def _validate_demand_set_context(
    value: object,
    *,
    package: object,
    intent: object,
    profile_ref: object,
    profile_digest: object,
    contract_profile_binding_digest: object,
    planner_implementation_ref: object,
    planner_implementation_digest: object,
    planner_configuration: object,
) -> SemanticDependencyDemandSet:
    if type(value) is not SemanticDependencyDemandSet:
        raise TypeError("demand set must be exact SemanticDependencyDemandSet")
    if type(package) is not SemanticPackageCoordinate:
        raise TypeError("package must be exact SemanticPackageCoordinate")
    if type(intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("intent must be exact CodeSemanticMaterializationIntent")
    if type(profile_digest) is not ContentDigest:
        raise TypeError("profile digest must be exact ContentDigest")
    if type(planner_implementation_digest) is not ContentDigest:
        raise TypeError("planner implementation digest must be exact ContentDigest")
    if type(contract_profile_binding_digest) is not ContentDigest:
        raise TypeError("profile binding digest must be exact ContentDigest")
    if type(planner_configuration) is not SemanticConfigurationCoordinate:
        raise TypeError("planner configuration must be exact")
    package.__post_init__()
    intent.__post_init__()
    profile_digest.__post_init__()
    planner_implementation_digest.__post_init__()
    contract_profile_binding_digest.__post_init__()
    planner_configuration.__post_init__()
    if type(value.package) is not SemanticPackageCoordinate:
        raise TypeError("demand set package must be exact SemanticPackageCoordinate")
    value.package.__post_init__()
    if type(value.intent_digest) is not ContentDigest:
        raise TypeError("demand set intent digest must be exact ContentDigest")
    value.intent_digest.__post_init__()
    if (
        value.package != package
        or value.intent_digest != intent.intent_digest
        or value.profile_ref != _text(profile_ref, "profile_ref")
        or value.profile_digest != profile_digest
        or value.contract_profile_binding_digest != contract_profile_binding_digest
        or value.planner_implementation_ref
        != _text(planner_implementation_ref, "planner_implementation_ref")
        or value.planner_implementation_digest != planner_implementation_digest
        or value.planner_configuration_ref != planner_configuration.configuration_ref
        or value.planner_configuration_digest != planner_configuration.digest
    ):
        raise ContractViolation("demand set differs from exact planning context")
    return value


def _constraint(value: object, path: str) -> SemanticDependencyTargetConstraint:
    root = _object(
        value,
        {"constraint_digest", "constraint_kind", "constraint_value", "contract"},
        path,
    )
    if (
        _text(root["contract"], f"{path}.contract")
        != CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT
    ):
        raise ContractViolation(f"{path}.contract unsupported")
    return _unchecked_value(
        SemanticDependencyTargetConstraint,
        constraint_kind=_text(root["constraint_kind"], f"{path}.constraint_kind"),
        constraint_value=_text(root["constraint_value"], f"{path}.constraint_value"),
        constraint_digest=ContentDigest.of_wire(
            root["constraint_digest"], f"{path}.constraint_digest"
        ),
    )


def _demand(value: object, path: str) -> SemanticDependencyDemand:
    root = _object(
        value,
        {
            "authored_dependency_kind",
            "authored_dependency_ref",
            "cardinality",
            "consumer_semantic_role",
            "contract",
            "demand_digest",
            "required_result_role",
            "result_product_contract",
            "target_intent",
            "target_constraints",
        },
        path,
    )
    if _text(root["contract"], f"{path}.contract") != CODE_SEMANTIC_DEPENDENCY_DEMAND:
        raise ContractViolation(f"{path}.contract unsupported")
    return _unchecked_value(
        SemanticDependencyDemand,
        consumer_semantic_role=_text(
            root["consumer_semantic_role"], f"{path}.consumer_semantic_role"
        ),
        authored_dependency_kind=_text(
            root["authored_dependency_kind"], f"{path}.authored_dependency_kind"
        ),
        authored_dependency_ref=_text(
            root["authored_dependency_ref"], f"{path}.authored_dependency_ref"
        ),
        target_constraints=tuple(
            _constraint(item, f"{path}.target_constraints[{index}]")
            for index, item in enumerate(
                _list(root["target_constraints"], f"{path}.target_constraints")
            )
        ),
        required_result_role=_text(
            root["required_result_role"], f"{path}.required_result_role"
        ),
        result_product_contract=_contract_ref(
            root["result_product_contract"], f"{path}.result_product_contract"
        ),
        target_intent=_intent_object(root["target_intent"], f"{path}.target_intent"),
        cardinality=_text(root["cardinality"], f"{path}.cardinality"),
        demand_digest=ContentDigest.of_wire(
            root["demand_digest"], f"{path}.demand_digest"
        ),
    )


def _intent_object(value: object, path: str) -> CodeSemanticMaterializationIntent:
    root = _object(
        value,
        {
            "contract",
            "intent_digest",
            "operation_kind",
            "requested_semantic_root_refs",
            "requested_terminal_output_roles",
            "semantic_configuration_coordinate",
        },
        path,
    )
    if (
        _text(root["contract"], f"{path}.contract")
        != CODE_SEMANTIC_MATERIALIZATION_INTENT
    ):
        raise ContractViolation(f"{path}.contract unsupported")
    return CodeSemanticMaterializationIntent(
        operation_kind=_text(root["operation_kind"], f"{path}.operation_kind"),
        requested_semantic_root_refs=_text_tuple(
            root["requested_semantic_root_refs"],
            f"{path}.requested_semantic_root_refs",
        ),
        requested_terminal_output_roles=_text_tuple(
            root["requested_terminal_output_roles"],
            f"{path}.requested_terminal_output_roles",
        ),
        semantic_configuration_coordinate=_configuration(
            root["semantic_configuration_coordinate"],
            f"{path}.semantic_configuration_coordinate",
        ),
        intent_digest=ContentDigest.of_wire(
            root["intent_digest"], f"{path}.intent_digest"
        ),
    )


def _required_product(value: object, path: str) -> CodeSemanticRequiredResultProduct:
    root = _object(
        value,
        {"contract", "requirement_digest", "result_contract", "role"},
        path,
    )
    if (
        _text(root["contract"], f"{path}.contract")
        != CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT
    ):
        raise ContractViolation(f"{path}.contract unsupported")
    return CodeSemanticRequiredResultProduct(
        role=_text(root["role"], f"{path}.role"),
        contract=_contract_ref(root["result_contract"], f"{path}.result_contract"),
        requirement_digest=ContentDigest.of_wire(
            root["requirement_digest"], f"{path}.requirement_digest"
        ),
    )


def _unchecked_value[T](expected: type[T], **fields: object) -> T:
    """Build a parsed exact value; the outer canonical reconstruction validates it."""
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _encode_admitted_wire(value: object) -> bytes:
    """Encode a wire returned by fresh module-owned validation without rewalking it."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _configuration(value: object, path: str) -> SemanticConfigurationCoordinate | None:
    if value is None:
        return None
    root = _object(value, {"configuration_ref", "digest"}, path)
    return SemanticConfigurationCoordinate(
        configuration_ref=_text(root["configuration_ref"], f"{path}.configuration_ref"),
        digest=ContentDigest.of_wire(root["digest"], f"{path}.digest"),
    )


def _contract_ref(value: object, path: str) -> SemanticContractRef:
    root = _object(value, {"key", "schema_digest", "version"}, path)
    return SemanticContractRef(
        key=_text(root["key"], f"{path}.key"),
        version=_text(root["version"], f"{path}.version"),
        schema_digest=ContentDigest.of_wire(
            root["schema_digest"], f"{path}.schema_digest"
        ),
    )


def _package(value: object, path: str) -> SemanticPackageCoordinate:
    root = _object(value, {"manifest_digest", "package_kind", "package_ref"}, path)
    return SemanticPackageCoordinate(
        package_ref=_text(root["package_ref"], f"{path}.package_ref"),
        package_kind=_text(root["package_kind"], f"{path}.package_kind"),
        manifest_digest=ContentDigest.of_wire(
            root["manifest_digest"], f"{path}.manifest_digest"
        ),
    )


def _decode_object(wire: bytes, keys: set[str], path: str) -> dict[str, object]:
    if type(wire) is not bytes:
        raise TypeError("wire must be exact bytes")
    if not wire or len(wire) > _MAX_WIRE_BYTES:
        raise ContractViolation("wire size unsupported")
    try:
        value = json.loads(wire.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation("wire is not canonical JSON") from error
    return _object(value, keys, path)


def _object(value: object, keys: set[str], path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact object")
    result = cast(dict[object, object], value)
    if any(type(key) is not str for key in result) or set(result) != keys:
        raise ContractViolation(f"{path} fields differ")
    return cast(dict[str, object], result)


def _list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return cast(list[object], value)


def _text(value: object, path: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(character.isspace() for character in value)
    ):
        raise TypeError(f"{path} must be nonempty token text")
    return value


def _text_tuple(value: object, path: str) -> tuple[str, ...]:
    return tuple(
        _text(item, f"{path}[{index}]") for index, item in enumerate(_list(value, path))
    )


__all__ = [
    "decode_code_composed_semantic_materialization_intent",
    "decode_code_semantic_materialization_intent",
    "decode_code_semantic_required_result_product",
    "decode_semantic_dependency_demand_set",
    "encode_code_composed_semantic_materialization_intent",
    "encode_code_semantic_materialization_intent",
    "encode_code_semantic_required_result_product",
    "encode_semantic_dependency_demand_set",
]
