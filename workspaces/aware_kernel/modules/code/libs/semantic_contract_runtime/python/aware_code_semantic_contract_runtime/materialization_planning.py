"""Portable Code-owned semantic materialization planning values."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticPackageCoordinate,
    _instance,
    _token,
    _token_tuple,
)

CODE_SEMANTIC_MATERIALIZATION_INTENT = "aware.code.semantic-materialization-intent.v1"
CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT = (
    "aware.code.semantic-dependency-target-constraint.v1"
)
CODE_SEMANTIC_DEPENDENCY_DEMAND = "aware.code.semantic-dependency-demand.v1"
CODE_SEMANTIC_DEPENDENCY_DEMAND_SET = "aware.code.semantic-dependency-demand-set.v1"
CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT = "aware.code.semantic-required-result-product.v1"
CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT = (
    "aware.code.composed-semantic-materialization-intent.v1"
)

SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT_KINDS = (
    "module_ref",
    "package_family",
    "package_kind",
    "package_ref",
    "semantic_provider_key",
    "semantic_root_ref",
)
_SINGLETON_CONSTRAINT_KINDS = frozenset(
    {
        "module_ref",
        "package_family",
        "package_kind",
        "package_ref",
        "semantic_provider_key",
    }
)
SEMANTIC_DEPENDENCY_CARDINALITIES = ("optional", "required")
_INTERNAL_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _digest(contract: str, payload: dict[str, object]) -> ContentDigest:
    value = (
        "sha256:"
        + hashlib.sha256(
            _internal_canonical_bytes({"contract": contract, **payload})
        ).hexdigest()
    )
    result = object.__new__(ContentDigest)
    object.__setattr__(result, "value", value)
    return result


def _internal_canonical_bytes(value: object) -> bytes:
    """Encode an already recursively admitted internal body without a second walk."""
    return _INTERNAL_JSON_ENCODER.encode(value).encode("utf-8")


def _content_digest(value: object, path: str) -> ContentDigest:
    return _instance(value, ContentDigest, path)


def _preflight_exact[T](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    return value


def _preflight_tuple[T](value: object, expected: type[T], path: str) -> tuple[T, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    result: list[T] = []
    for index, item in enumerate(value):
        result.append(_preflight_exact(item, expected, f"{path}[{index}]"))
    return tuple(result)


def _digest_wire(value: object, path: str) -> str:
    digest = _content_digest(value, path)
    return digest.value


@dataclass(frozen=True, slots=True)
class CodeSemanticMaterializationIntent:
    operation_kind: str
    requested_semantic_root_refs: tuple[str, ...]
    requested_terminal_output_roles: tuple[str, ...]
    semantic_configuration_coordinate: SemanticConfigurationCoordinate | None
    intent_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        operation_kind: str,
        requested_semantic_root_refs: tuple[str, ...],
        requested_terminal_output_roles: tuple[str, ...],
        semantic_configuration_coordinate: SemanticConfigurationCoordinate | None,
    ) -> CodeSemanticMaterializationIntent:
        if semantic_configuration_coordinate is not None:
            _preflight_exact(
                semantic_configuration_coordinate,
                SemanticConfigurationCoordinate,
                "intent.semantic_configuration_coordinate",
            )
        payload = _intent_payload(
            operation_kind=operation_kind,
            requested_semantic_root_refs=requested_semantic_root_refs,
            requested_terminal_output_roles=requested_terminal_output_roles,
            semantic_configuration_coordinate=semantic_configuration_coordinate,
        )
        return cls(
            operation_kind=operation_kind,
            requested_semantic_root_refs=requested_semantic_root_refs,
            requested_terminal_output_roles=requested_terminal_output_roles,
            semantic_configuration_coordinate=semantic_configuration_coordinate,
            intent_digest=_digest(CODE_SEMANTIC_MATERIALIZATION_INTENT, payload),
        )

    def __post_init__(self) -> None:
        payload = _intent_payload(
            operation_kind=self.operation_kind,
            requested_semantic_root_refs=self.requested_semantic_root_refs,
            requested_terminal_output_roles=self.requested_terminal_output_roles,
            semantic_configuration_coordinate=self.semantic_configuration_coordinate,
        )
        digest = _content_digest(self.intent_digest, "intent.intent_digest")
        if digest != _digest(CODE_SEMANTIC_MATERIALIZATION_INTENT, payload):
            raise ContractViolation("intent digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_MATERIALIZATION_INTENT,
            **_intent_payload(
                operation_kind=self.operation_kind,
                requested_semantic_root_refs=self.requested_semantic_root_refs,
                requested_terminal_output_roles=self.requested_terminal_output_roles,
                semantic_configuration_coordinate=(
                    self.semantic_configuration_coordinate
                ),
            ),
            "intent_digest": self.intent_digest.to_wire(),
        }


def _intent_payload(
    *,
    operation_kind: object,
    requested_semantic_root_refs: object,
    requested_terminal_output_roles: object,
    semantic_configuration_coordinate: object,
) -> dict[str, object]:
    operation = _token(operation_kind, "intent.operation_kind")
    roots = _token_tuple(
        requested_semantic_root_refs,
        "intent.requested_semantic_root_refs",
        nonempty=True,
    )
    roles = _token_tuple(
        requested_terminal_output_roles,
        "intent.requested_terminal_output_roles",
        nonempty=True,
    )
    if semantic_configuration_coordinate is None:
        configuration_wire: object = None
    else:
        configuration = _instance(
            semantic_configuration_coordinate,
            SemanticConfigurationCoordinate,
            "intent.semantic_configuration_coordinate",
        )
        configuration_wire = configuration.to_wire()
    return {
        "operation_kind": operation,
        "requested_semantic_root_refs": list(roots),
        "requested_terminal_output_roles": list(roles),
        "semantic_configuration_coordinate": configuration_wire,
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticRequiredResultProduct:
    role: str
    contract: SemanticContractRef
    requirement_digest: ContentDigest

    @classmethod
    def create(
        cls, *, role: str, contract: SemanticContractRef
    ) -> CodeSemanticRequiredResultProduct:
        _preflight_exact(contract, SemanticContractRef, "requirement.contract")
        payload = _required_result_payload(role=role, contract=contract)
        return cls(
            role=role,
            contract=contract,
            requirement_digest=_digest(CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT, payload),
        )

    def __post_init__(self) -> None:
        payload = _required_result_payload(role=self.role, contract=self.contract)
        if _content_digest(
            self.requirement_digest, "requirement.requirement_digest"
        ) != _digest(CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT, payload):
            raise ContractViolation("required result product digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT,
            **_required_result_payload(role=self.role, contract=self.contract),
            "requirement_digest": self.requirement_digest.to_wire(),
        }


def _required_result_payload(*, role: object, contract: object) -> dict[str, object]:
    if type(contract) is not SemanticContractRef:
        raise TypeError("requirement.contract must be exact SemanticContractRef")
    contract.__post_init__()
    return {
        "role": _token(role, "requirement.role"),
        "result_contract": contract.to_wire(),
    }


def _required_result_tuple(
    value: object, path: str, *, nonempty: bool = True
) -> tuple[CodeSemanticRequiredResultProduct, ...]:
    values = _preflight_tuple(value, CodeSemanticRequiredResultProduct, path)
    roles: list[str] = []
    for index, item in enumerate(values):
        item.__post_init__()
        roles.append(item.role)
    if nonempty and not values:
        raise ContractViolation(f"{path} must not be empty")
    if roles != sorted(set(roles), key=str.encode):
        raise ContractViolation(f"{path} must be role-unique and ordered")
    return values


@dataclass(frozen=True, slots=True)
class SemanticDependencyTargetConstraint:
    constraint_kind: str
    constraint_value: str
    constraint_digest: ContentDigest

    @classmethod
    def create(
        cls, *, constraint_kind: str, constraint_value: str
    ) -> SemanticDependencyTargetConstraint:
        payload = _constraint_payload(
            constraint_kind=constraint_kind,
            constraint_value=constraint_value,
        )
        return cls(
            constraint_kind=constraint_kind,
            constraint_value=constraint_value,
            constraint_digest=_digest(
                CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _constraint_payload(
            constraint_kind=self.constraint_kind,
            constraint_value=self.constraint_value,
        )
        digest = _content_digest(self.constraint_digest, "constraint.constraint_digest")
        if digest != _digest(CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT, payload):
            raise ContractViolation("constraint digest mismatched")

    def to_wire(self) -> dict[str, object]:
        payload = _constraint_payload(
            constraint_kind=self.constraint_kind,
            constraint_value=self.constraint_value,
        )
        if _content_digest(
            self.constraint_digest, "constraint.constraint_digest"
        ) != _digest(CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT, payload):
            raise ContractViolation("constraint digest mismatched")
        return {
            "contract": CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT,
            **payload,
            "constraint_digest": self.constraint_digest.to_wire(),
        }


def _constraint_payload(
    *, constraint_kind: object, constraint_value: object
) -> dict[str, object]:
    kind = _token(constraint_kind, "constraint.constraint_kind")
    if kind not in SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT_KINDS:
        raise ContractViolation("constraint kind unsupported")
    return {
        "constraint_kind": kind,
        "constraint_value": _token(constraint_value, "constraint.constraint_value"),
    }


def _validated_constraint_wire(
    value: SemanticDependencyTargetConstraint, path: str
) -> dict[str, object]:
    payload = _constraint_payload(
        constraint_kind=value.constraint_kind,
        constraint_value=value.constraint_value,
    )
    digest = _content_digest(value.constraint_digest, f"{path}.constraint_digest")
    if digest != _digest(CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT, payload):
        raise ContractViolation(f"{path} digest mismatched")
    return {
        "contract": CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT,
        **payload,
        "constraint_digest": digest.value,
    }


@dataclass(frozen=True, slots=True)
class SemanticDependencyDemand:
    consumer_semantic_role: str
    authored_dependency_kind: str
    authored_dependency_ref: str
    target_constraints: tuple[SemanticDependencyTargetConstraint, ...]
    required_result_role: str
    result_product_contract: SemanticContractRef
    target_intent: CodeSemanticMaterializationIntent
    cardinality: str
    demand_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        consumer_semantic_role: str,
        authored_dependency_kind: str,
        authored_dependency_ref: str,
        target_constraints: tuple[SemanticDependencyTargetConstraint, ...],
        required_result_role: str,
        result_product_contract: SemanticContractRef,
        target_intent: CodeSemanticMaterializationIntent,
        cardinality: str,
    ) -> SemanticDependencyDemand:
        _preflight_tuple(
            target_constraints,
            SemanticDependencyTargetConstraint,
            "demand.target_constraints",
        )
        _preflight_exact(
            result_product_contract,
            SemanticContractRef,
            "demand.result_product_contract",
        )
        _preflight_exact(
            target_intent,
            CodeSemanticMaterializationIntent,
            "demand.target_intent",
        )
        payload = _demand_payload(
            consumer_semantic_role=consumer_semantic_role,
            authored_dependency_kind=authored_dependency_kind,
            authored_dependency_ref=authored_dependency_ref,
            target_constraints=target_constraints,
            required_result_role=required_result_role,
            result_product_contract=result_product_contract,
            target_intent=target_intent,
            cardinality=cardinality,
        )
        return cls(
            consumer_semantic_role=consumer_semantic_role,
            authored_dependency_kind=authored_dependency_kind,
            authored_dependency_ref=authored_dependency_ref,
            target_constraints=target_constraints,
            required_result_role=required_result_role,
            result_product_contract=result_product_contract,
            target_intent=target_intent,
            cardinality=cardinality,
            demand_digest=_digest(CODE_SEMANTIC_DEPENDENCY_DEMAND, payload),
        )

    def __post_init__(self) -> None:
        payload = _demand_payload(
            consumer_semantic_role=self.consumer_semantic_role,
            authored_dependency_kind=self.authored_dependency_kind,
            authored_dependency_ref=self.authored_dependency_ref,
            target_constraints=self.target_constraints,
            required_result_role=self.required_result_role,
            result_product_contract=self.result_product_contract,
            target_intent=self.target_intent,
            cardinality=self.cardinality,
        )
        digest = _content_digest(self.demand_digest, "demand.demand_digest")
        if digest != _digest(CODE_SEMANTIC_DEPENDENCY_DEMAND, payload):
            raise ContractViolation("demand digest mismatched")

    def to_wire(self) -> dict[str, object]:
        payload = _demand_payload(
            consumer_semantic_role=self.consumer_semantic_role,
            authored_dependency_kind=self.authored_dependency_kind,
            authored_dependency_ref=self.authored_dependency_ref,
            target_constraints=self.target_constraints,
            required_result_role=self.required_result_role,
            result_product_contract=self.result_product_contract,
            target_intent=self.target_intent,
            cardinality=self.cardinality,
        )
        if _content_digest(self.demand_digest, "demand.demand_digest") != _digest(
            CODE_SEMANTIC_DEPENDENCY_DEMAND, payload
        ):
            raise ContractViolation("demand digest mismatched")
        return {
            "contract": CODE_SEMANTIC_DEPENDENCY_DEMAND,
            **payload,
            "demand_digest": self.demand_digest.to_wire(),
        }


def _demand_payload(
    *,
    consumer_semantic_role: object,
    authored_dependency_kind: object,
    authored_dependency_ref: object,
    target_constraints: object,
    required_result_role: object,
    result_product_contract: object,
    target_intent: object,
    cardinality: object,
) -> dict[str, object]:
    if type(target_constraints) is not tuple:
        raise TypeError("demand.target_constraints must be exact tuple")
    constraints: list[SemanticDependencyTargetConstraint] = []
    constraint_wires: list[dict[str, object]] = []
    for index, candidate in enumerate(target_constraints):
        path = f"demand.target_constraints[{index}]"
        if type(candidate) is not SemanticDependencyTargetConstraint:
            raise TypeError(f"{path} must be exact SemanticDependencyTargetConstraint")
        constraints.append(candidate)
        constraint_wires.append(_validated_constraint_wire(candidate, path))
    canonical_wires = tuple(
        _internal_canonical_bytes(item) for item in constraint_wires
    )
    if canonical_wires != tuple(sorted(set(canonical_wires))):
        raise ContractViolation(
            "demand.target_constraints must be unique and canonical-byte ordered"
        )
    seen_singletons: set[str] = set()
    for constraint in constraints:
        if constraint.constraint_kind in _SINGLETON_CONSTRAINT_KINDS:
            if constraint.constraint_kind in seen_singletons:
                raise ContractViolation("demand repeats a singleton constraint kind")
            seen_singletons.add(constraint.constraint_kind)
    if type(result_product_contract) is not SemanticContractRef:
        raise TypeError(
            "demand.result_product_contract must be exact SemanticContractRef"
        )
    result_contract = result_product_contract
    contract_key = _token(result_contract.key, "demand.result_product_contract.key")
    contract_version = _token(
        result_contract.version, "demand.result_product_contract.version"
    )
    contract_schema_digest = _digest_wire(
        result_contract.schema_digest,
        "demand.result_product_contract.schema_digest",
    )
    admitted_cardinality = _token(cardinality, "demand.cardinality")
    if admitted_cardinality not in SEMANTIC_DEPENDENCY_CARDINALITIES:
        raise ContractViolation("demand cardinality unsupported")
    if type(target_intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("demand.target_intent must be exact Code intent")
    target_intent.__post_init__()
    required_role = _token(required_result_role, "demand.required_result_role")
    if target_intent.requested_terminal_output_roles != (required_role,):
        raise ContractViolation(
            "demand target intent must request exactly its required result role"
        )
    return {
        "authored_dependency_kind": _token(
            authored_dependency_kind, "demand.authored_dependency_kind"
        ),
        "authored_dependency_ref": _token(
            authored_dependency_ref, "demand.authored_dependency_ref"
        ),
        "cardinality": admitted_cardinality,
        "consumer_semantic_role": _token(
            consumer_semantic_role, "demand.consumer_semantic_role"
        ),
        "required_result_role": required_role,
        "result_product_contract": {
            "key": contract_key,
            "schema_digest": contract_schema_digest,
            "version": contract_version,
        },
        "target_intent": target_intent.to_wire(),
        "target_constraints": constraint_wires,
    }


def _validated_demand_wire(
    value: SemanticDependencyDemand, path: str
) -> dict[str, object]:
    payload = _demand_payload(
        consumer_semantic_role=value.consumer_semantic_role,
        authored_dependency_kind=value.authored_dependency_kind,
        authored_dependency_ref=value.authored_dependency_ref,
        target_constraints=value.target_constraints,
        required_result_role=value.required_result_role,
        result_product_contract=value.result_product_contract,
        target_intent=value.target_intent,
        cardinality=value.cardinality,
    )
    digest = _content_digest(value.demand_digest, f"{path}.demand_digest")
    if digest != _digest(CODE_SEMANTIC_DEPENDENCY_DEMAND, payload):
        raise ContractViolation(f"{path} digest mismatched")
    return {
        "contract": CODE_SEMANTIC_DEPENDENCY_DEMAND,
        **payload,
        "demand_digest": digest.value,
    }


@dataclass(frozen=True, slots=True)
class CodeComposedSemanticMaterializationIntent:
    target_package: SemanticPackageCoordinate
    contributing_demand_digests: tuple[ContentDigest, ...]
    contributing_intent_digests: tuple[ContentDigest, ...]
    composed_intent: CodeSemanticMaterializationIntent
    required_result_products: tuple[CodeSemanticRequiredResultProduct, ...]
    composition_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        target_package: SemanticPackageCoordinate,
        demands: tuple[SemanticDependencyDemand, ...],
    ) -> CodeComposedSemanticMaterializationIntent:
        _preflight_exact(
            target_package, SemanticPackageCoordinate, "composition.target_package"
        )
        admitted_demands = _preflight_tuple(
            demands, SemanticDependencyDemand, "composition.demands"
        )
        if not admitted_demands:
            raise ContractViolation("composition demands must not be empty")
        for demand in admitted_demands:
            demand.__post_init__()
        if tuple(item.demand_digest.value for item in admitted_demands) != tuple(
            sorted({item.demand_digest.value for item in admitted_demands})
        ):
            raise ContractViolation(
                "composition demands must be unique and demand-digest ordered"
            )
        first = admitted_demands[0].target_intent
        operation_kind = first.operation_kind
        configuration = first.semantic_configuration_coordinate
        roots: set[str] = set()
        requirements: dict[str, CodeSemanticRequiredResultProduct] = {}
        for demand in admitted_demands:
            intent = demand.target_intent
            if (
                intent.operation_kind != operation_kind
                or intent.semantic_configuration_coordinate != configuration
            ):
                raise ContractViolation("dependency target intent conflict")
            roots.update(intent.requested_semantic_root_refs)
            existing = requirements.get(demand.required_result_role)
            if (
                existing is not None
                and existing.contract != demand.result_product_contract
            ):
                raise ContractViolation("dependency result contract conflict")
            if existing is None:
                requirements[demand.required_result_role] = (
                    CodeSemanticRequiredResultProduct.create(
                        role=demand.required_result_role,
                        contract=demand.result_product_contract,
                    )
                )
        ordered_requirements = tuple(
            requirements[role] for role in sorted(requirements, key=str.encode)
        )
        composed = CodeSemanticMaterializationIntent.create(
            operation_kind=operation_kind,
            requested_semantic_root_refs=tuple(sorted(roots, key=str.encode)),
            requested_terminal_output_roles=tuple(
                item.role for item in ordered_requirements
            ),
            semantic_configuration_coordinate=configuration,
        )
        demand_digests = tuple(item.demand_digest for item in admitted_demands)
        intent_digests = tuple(
            item.target_intent.intent_digest for item in admitted_demands
        )
        payload = _composition_payload(
            target_package=target_package,
            contributing_demand_digests=demand_digests,
            contributing_intent_digests=intent_digests,
            composed_intent=composed,
            required_result_products=ordered_requirements,
        )
        return cls(
            target_package=target_package,
            contributing_demand_digests=demand_digests,
            contributing_intent_digests=intent_digests,
            composed_intent=composed,
            required_result_products=ordered_requirements,
            composition_digest=_digest(
                CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _composition_payload(
            target_package=self.target_package,
            contributing_demand_digests=self.contributing_demand_digests,
            contributing_intent_digests=self.contributing_intent_digests,
            composed_intent=self.composed_intent,
            required_result_products=self.required_result_products,
        )
        if _content_digest(
            self.composition_digest, "composition.composition_digest"
        ) != _digest(CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT, payload):
            raise ContractViolation("composed semantic intent digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT,
            **_composition_payload(
                target_package=self.target_package,
                contributing_demand_digests=self.contributing_demand_digests,
                contributing_intent_digests=self.contributing_intent_digests,
                composed_intent=self.composed_intent,
                required_result_products=self.required_result_products,
            ),
            "composition_digest": self.composition_digest.to_wire(),
        }


def _compose_prevalidated_dependency_demands(
    *,
    target_package: SemanticPackageCoordinate,
    demands: tuple[SemanticDependencyDemand, ...],
) -> CodeComposedSemanticMaterializationIntent:
    """Compose resolver-snapshotted demands without a second recursive walk."""

    _preflight_exact(
        target_package, SemanticPackageCoordinate, "composition.target_package"
    )
    admitted_demands = _preflight_tuple(
        demands, SemanticDependencyDemand, "composition.demands"
    )
    if not admitted_demands:
        raise ContractViolation("composition demands must not be empty")
    if tuple(item.demand_digest.value for item in admitted_demands) != tuple(
        sorted({item.demand_digest.value for item in admitted_demands})
    ):
        raise ContractViolation(
            "composition demands must be unique and demand-digest ordered"
        )
    first = admitted_demands[0].target_intent
    operation_kind = first.operation_kind
    configuration = first.semantic_configuration_coordinate
    roots: set[str] = set()
    requirements: dict[str, CodeSemanticRequiredResultProduct] = {}
    for demand in admitted_demands:
        intent = demand.target_intent
        if (
            intent.operation_kind != operation_kind
            or intent.semantic_configuration_coordinate != configuration
        ):
            raise ContractViolation("dependency target intent conflict")
        roots.update(intent.requested_semantic_root_refs)
        existing = requirements.get(demand.required_result_role)
        if existing is not None and existing.contract != demand.result_product_contract:
            raise ContractViolation("dependency result contract conflict")
        if existing is None:
            requirements[demand.required_result_role] = (
                CodeSemanticRequiredResultProduct.create(
                    role=demand.required_result_role,
                    contract=demand.result_product_contract,
                )
            )
    ordered_requirements = tuple(
        requirements[role] for role in sorted(requirements, key=str.encode)
    )
    composed = CodeSemanticMaterializationIntent.create(
        operation_kind=operation_kind,
        requested_semantic_root_refs=tuple(sorted(roots, key=str.encode)),
        requested_terminal_output_roles=tuple(
            item.role for item in ordered_requirements
        ),
        semantic_configuration_coordinate=configuration,
    )
    demand_digests = tuple(item.demand_digest for item in admitted_demands)
    intent_digests = tuple(
        item.target_intent.intent_digest for item in admitted_demands
    )
    payload = _composition_payload(
        target_package=target_package,
        contributing_demand_digests=demand_digests,
        contributing_intent_digests=intent_digests,
        composed_intent=composed,
        required_result_products=ordered_requirements,
    )
    return CodeComposedSemanticMaterializationIntent(
        target_package=target_package,
        contributing_demand_digests=demand_digests,
        contributing_intent_digests=intent_digests,
        composed_intent=composed,
        required_result_products=ordered_requirements,
        composition_digest=_digest(
            CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT, payload
        ),
    )


def _composition_payload(
    *,
    target_package: object,
    contributing_demand_digests: object,
    contributing_intent_digests: object,
    composed_intent: object,
    required_result_products: object,
) -> dict[str, object]:
    if type(target_package) is not SemanticPackageCoordinate:
        raise TypeError("composition target package must be exact")
    target_package.__post_init__()
    demand_digests = _preflight_tuple(
        contributing_demand_digests, ContentDigest, "composition.demand_digests"
    )
    intent_digests = _preflight_tuple(
        contributing_intent_digests, ContentDigest, "composition.intent_digests"
    )
    if not demand_digests or len(demand_digests) != len(intent_digests):
        raise ContractViolation("composition contributor closure differs")
    for value in (*demand_digests, *intent_digests):
        value.__post_init__()
    if tuple(item.value for item in demand_digests) != tuple(
        sorted({item.value for item in demand_digests})
    ):
        raise ContractViolation("composition demand digests are not canonical")
    if type(composed_intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("composition intent must be exact Code intent")
    composed_intent.__post_init__()
    requirements = _required_result_tuple(
        required_result_products, "composition.required_result_products"
    )
    if composed_intent.requested_terminal_output_roles != tuple(
        item.role for item in requirements
    ):
        raise ContractViolation("composition result requirements differ from intent")
    return {
        "composed_intent": composed_intent.to_wire(),
        "contributing_demand_digests": [item.to_wire() for item in demand_digests],
        "contributing_intent_digests": [item.to_wire() for item in intent_digests],
        "required_result_products": [item.to_wire() for item in requirements],
        "target_package": target_package.to_wire(),
    }


@dataclass(frozen=True, slots=True)
class SemanticDependencyDemandSet:
    package: SemanticPackageCoordinate
    intent_digest: ContentDigest
    profile_ref: str
    profile_digest: ContentDigest
    contract_profile_binding_digest: ContentDigest
    planner_implementation_ref: str
    planner_implementation_digest: ContentDigest
    planner_configuration_ref: str
    planner_configuration_digest: ContentDigest
    demands: tuple[SemanticDependencyDemand, ...]
    demand_set_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        package: SemanticPackageCoordinate,
        intent: CodeSemanticMaterializationIntent,
        profile_ref: str,
        profile_digest: ContentDigest,
        contract_profile_binding_digest: ContentDigest,
        planner_implementation_ref: str,
        planner_implementation_digest: ContentDigest,
        planner_configuration: SemanticConfigurationCoordinate,
        demands: tuple[SemanticDependencyDemand, ...],
    ) -> SemanticDependencyDemandSet:
        _preflight_exact(package, SemanticPackageCoordinate, "demand_set.package")
        _preflight_exact(intent, CodeSemanticMaterializationIntent, "demand_set.intent")
        _preflight_exact(profile_digest, ContentDigest, "demand_set.profile_digest")
        _preflight_exact(
            contract_profile_binding_digest,
            ContentDigest,
            "demand_set.contract_profile_binding_digest",
        )
        _preflight_exact(
            planner_implementation_digest,
            ContentDigest,
            "demand_set.planner_implementation_digest",
        )
        _preflight_exact(
            planner_configuration,
            SemanticConfigurationCoordinate,
            "demand_set.planner_configuration",
        )
        _preflight_tuple(demands, SemanticDependencyDemand, "demand_set.demands")
        intent.__post_init__()
        payload = _demand_set_payload(
            package=package,
            intent_digest=intent.intent_digest,
            profile_ref=profile_ref,
            profile_digest=profile_digest,
            contract_profile_binding_digest=contract_profile_binding_digest,
            planner_implementation_ref=planner_implementation_ref,
            planner_implementation_digest=planner_implementation_digest,
            planner_configuration_ref=planner_configuration.configuration_ref,
            planner_configuration_digest=planner_configuration.digest,
            demands=demands,
        )
        result = object.__new__(cls)
        object.__setattr__(result, "package", package)
        object.__setattr__(result, "intent_digest", intent.intent_digest)
        object.__setattr__(result, "profile_ref", profile_ref)
        object.__setattr__(result, "profile_digest", profile_digest)
        object.__setattr__(
            result,
            "contract_profile_binding_digest",
            contract_profile_binding_digest,
        )
        object.__setattr__(
            result, "planner_implementation_ref", planner_implementation_ref
        )
        object.__setattr__(
            result,
            "planner_implementation_digest",
            planner_implementation_digest,
        )
        object.__setattr__(
            result,
            "planner_configuration_ref",
            planner_configuration.configuration_ref,
        )
        object.__setattr__(
            result,
            "planner_configuration_digest",
            planner_configuration.digest,
        )
        object.__setattr__(result, "demands", demands)
        object.__setattr__(
            result,
            "demand_set_digest",
            _digest(CODE_SEMANTIC_DEPENDENCY_DEMAND_SET, payload),
        )
        return result

    def __post_init__(self) -> None:
        payload = _demand_set_payload(
            package=self.package,
            intent_digest=self.intent_digest,
            profile_ref=self.profile_ref,
            profile_digest=self.profile_digest,
            contract_profile_binding_digest=self.contract_profile_binding_digest,
            planner_implementation_ref=self.planner_implementation_ref,
            planner_implementation_digest=self.planner_implementation_digest,
            planner_configuration_ref=self.planner_configuration_ref,
            planner_configuration_digest=self.planner_configuration_digest,
            demands=self.demands,
        )
        digest = _content_digest(self.demand_set_digest, "demand_set.demand_set_digest")
        if digest != _digest(CODE_SEMANTIC_DEPENDENCY_DEMAND_SET, payload):
            raise ContractViolation("demand set digest mismatched")

    def to_wire(self) -> dict[str, object]:
        payload = _demand_set_payload(
            package=self.package,
            intent_digest=self.intent_digest,
            profile_ref=self.profile_ref,
            profile_digest=self.profile_digest,
            contract_profile_binding_digest=self.contract_profile_binding_digest,
            planner_implementation_ref=self.planner_implementation_ref,
            planner_implementation_digest=self.planner_implementation_digest,
            planner_configuration_ref=self.planner_configuration_ref,
            planner_configuration_digest=self.planner_configuration_digest,
            demands=self.demands,
        )
        if _content_digest(
            self.demand_set_digest, "demand_set.demand_set_digest"
        ) != _digest(CODE_SEMANTIC_DEPENDENCY_DEMAND_SET, payload):
            raise ContractViolation("demand set digest mismatched")
        return {
            "contract": CODE_SEMANTIC_DEPENDENCY_DEMAND_SET,
            **payload,
            "demand_set_digest": self.demand_set_digest.to_wire(),
        }


def _demand_set_payload(
    *,
    package: object,
    intent_digest: object,
    profile_ref: object,
    profile_digest: object,
    contract_profile_binding_digest: object,
    planner_implementation_ref: object,
    planner_implementation_digest: object,
    planner_configuration_ref: object,
    planner_configuration_digest: object,
    demands: object,
) -> dict[str, object]:
    if type(package) is not SemanticPackageCoordinate:
        raise TypeError("demand_set.package must be exact SemanticPackageCoordinate")
    package_ref = _token(package.package_ref, "demand_set.package.package_ref")
    package_kind = _token(package.package_kind, "demand_set.package.package_kind")
    package_manifest_digest = _digest_wire(
        package.manifest_digest, "demand_set.package.manifest_digest"
    )
    if type(demands) is not tuple:
        raise TypeError("demand_set.demands must be exact tuple")
    demand_wires: list[dict[str, object]] = []
    demand_order: list[str] = []
    for index, candidate in enumerate(demands):
        path = f"demand_set.demands[{index}]"
        if type(candidate) is not SemanticDependencyDemand:
            raise TypeError(f"{path} must be exact SemanticDependencyDemand")
        demand_wires.append(_validated_demand_wire(candidate, path))
        demand_order.append(candidate.demand_digest.value)
    if tuple(demand_order) != tuple(sorted(set(demand_order))):
        raise ContractViolation(
            "demand_set.demands must be unique and demand-digest ordered"
        )
    return {
        "demands": demand_wires,
        "intent_digest": _digest_wire(intent_digest, "demand_set.intent_digest"),
        "package": {
            "manifest_digest": package_manifest_digest,
            "package_kind": package_kind,
            "package_ref": package_ref,
        },
        "planner_implementation_digest": _digest_wire(
            planner_implementation_digest,
            "demand_set.planner_implementation_digest",
        ),
        "planner_implementation_ref": _token(
            planner_implementation_ref,
            "demand_set.planner_implementation_ref",
        ),
        "planner_configuration_digest": _digest_wire(
            planner_configuration_digest,
            "demand_set.planner_configuration_digest",
        ),
        "planner_configuration_ref": _token(
            planner_configuration_ref,
            "demand_set.planner_configuration_ref",
        ),
        "contract_profile_binding_digest": _digest_wire(
            contract_profile_binding_digest,
            "demand_set.contract_profile_binding_digest",
        ),
        "profile_digest": _digest_wire(profile_digest, "demand_set.profile_digest"),
        "profile_ref": _token(profile_ref, "demand_set.profile_ref"),
    }


__all__ = [
    "CODE_COMPOSED_SEMANTIC_MATERIALIZATION_INTENT",
    "CODE_SEMANTIC_DEPENDENCY_DEMAND",
    "CODE_SEMANTIC_DEPENDENCY_DEMAND_SET",
    "CODE_SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT",
    "CODE_SEMANTIC_MATERIALIZATION_INTENT",
    "CODE_SEMANTIC_REQUIRED_RESULT_PRODUCT",
    "SEMANTIC_DEPENDENCY_CARDINALITIES",
    "SEMANTIC_DEPENDENCY_TARGET_CONSTRAINT_KINDS",
    "CodeComposedSemanticMaterializationIntent",
    "CodeSemanticMaterializationIntent",
    "CodeSemanticRequiredResultProduct",
    "SemanticDependencyDemand",
    "SemanticDependencyDemandSet",
    "SemanticDependencyTargetConstraint",
]
