"""Canonical dependency products admitted through the existing Code body runtime."""

from __future__ import annotations

import base64

from .codec import (
    _dependency,
    _digest,
    _keys,
    _list,
    _load,
    _object,
    _package,
    _string,
    _value,
)
from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .dependency_inputs import SemanticDependencyProduct, SemanticDependencyProductInput
from .materialization_planning_codec import (
    decode_code_semantic_materialization_intent,
    decode_semantic_dependency_demand_set,
)
from .runtime import SemanticBody

SEMANTIC_DEPENDENCY_PRODUCT_INPUT = "aware.code.semantic-dependency-product-input.v1"
SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF = SemanticContractRef(
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT,
    "1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": SEMANTIC_DEPENDENCY_PRODUCT_INPUT,
                "shape": "package/source_identity_digest/declared_dependencies/intent/demand_set/products",
                "product": "demand_digest/coordinate/body_coordinate/body_base64/provenance_digest",
            }
        )
    ),
)
DEPENDENCY_INPUT_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.semantic-dependency-product-input.codec.v1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF.to_wire(),
                "validation": "canonical closure plus invocation package/profile/dependencies",
            }
        )
    ),
)
_MAX_BYTES = 8 * 1024 * 1024


def encode_dependency_product_input(value: SemanticDependencyProductInput) -> bytes:
    if type(value) is not SemanticDependencyProductInput:
        raise TypeError("exact Code dependency product input required")
    value.__post_init__()
    wire = canonical_json_bytes(
        {
            "contract": SEMANTIC_DEPENDENCY_PRODUCT_INPUT,
            "package": value.package.to_wire(),
            "source_identity_digest": value.source_identity_digest.to_wire(),
            "declared_dependencies": [list(key) for key in value.declared_dependencies],
            "demand_set": value.demand_set.to_wire(),
            "intent": value.intent.to_wire(),
            "products": [
                {
                    "demand_digest": item.demand_digest.to_wire(),
                    "coordinate": item.coordinate.to_wire(),
                    "body_coordinate": item.body.coordinate.to_wire(),
                    "body_base64": base64.b64encode(item.body.canonical_body).decode(
                        "ascii"
                    ),
                    "provenance_digest": item.provenance_digest.to_wire(),
                }
                for item in value.products
            ],
        }
    )
    if len(wire) > _MAX_BYTES:
        raise ContractViolation("dependency input exceeds wire limit")
    return wire


def decode_dependency_product_input(wire: bytes) -> SemanticDependencyProductInput:
    if type(wire) is not bytes:
        raise TypeError("dependency input wire must be exact bytes")
    if not wire or len(wire) > _MAX_BYTES:
        raise ContractViolation("dependency input exceeds wire limit")
    root = _load(wire.decode("utf-8"))
    _keys(
        root,
        {
            "contract",
            "package",
            "source_identity_digest",
            "declared_dependencies",
            "intent",
            "demand_set",
            "products",
        },
        "dependency input",
    )
    if root["contract"] != SEMANTIC_DEPENDENCY_PRODUCT_INPUT:
        raise ContractViolation("dependency input contract differs")
    declarations = []
    for value in _list(root["declared_dependencies"], "declarations"):
        pair = _list(value, "declaration")
        if len(pair) != 2:
            raise ContractViolation("dependency declaration must be a pair")
        declarations.append((_string(pair[0], "kind"), _string(pair[1], "ref")))
    products = []
    for value in _list(root["products"], "products"):
        item = _object(value, "product")
        _keys(
            item,
            {
                "demand_digest",
                "coordinate",
                "body_coordinate",
                "body_base64",
                "provenance_digest",
            },
            "product",
        )
        try:
            body = base64.b64decode(
                _string(item["body_base64"], "body_base64"), validate=True
            )
        except ValueError as error:
            raise ContractViolation("dependency body base64 invalid") from error
        products.append(
            SemanticDependencyProduct(
                _digest(item["demand_digest"], "demand_digest"),
                _dependency(item["coordinate"], "coordinate"),
                SemanticBody(_value(item["body_coordinate"], "body_coordinate"), body),
                _digest(item["provenance_digest"], "provenance_digest"),
            )
        )
    package = _package(root["package"], "package")
    intent = decode_code_semantic_materialization_intent(
        canonical_json_bytes(root["intent"])
    )
    demand_wire = _object(root["demand_set"], "demand_set")
    demand_set = decode_semantic_dependency_demand_set(
        canonical_json_bytes(demand_wire),
        package=package,
        intent=intent,
        profile_ref=_string(demand_wire.get("profile_ref"), "profile_ref"),
        profile_digest=_digest(demand_wire.get("profile_digest"), "profile_digest"),
        contract_profile_binding_digest=_digest(
            demand_wire.get("contract_profile_binding_digest"), "binding_digest"
        ),
        planner_implementation_ref=_string(
            demand_wire.get("planner_implementation_ref"), "planner_ref"
        ),
        planner_implementation_digest=_digest(
            demand_wire.get("planner_implementation_digest"), "planner_digest"
        ),
        planner_configuration=SemanticConfigurationCoordinate(
            _string(demand_wire.get("planner_configuration_ref"), "configuration_ref"),
            _digest(
                demand_wire.get("planner_configuration_digest"), "configuration_digest"
            ),
        ),
    )
    result = SemanticDependencyProductInput(
        package,
        _digest(root["source_identity_digest"], "source_identity_digest"),
        tuple(declarations),
        demand_set,
        tuple(products),
        intent,
    )
    if encode_dependency_product_input(result) != wire:
        raise ContractViolation("dependency input is not canonical")
    return result


class SemanticDependencyProductInputCodec:
    contract = SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF
    implementation = DEPENDENCY_INPUT_CODEC_IMPLEMENTATION

    def decode(self, canonical_body: bytes) -> SemanticDependencyProductInput:
        return decode_dependency_product_input(canonical_body)

    def encode(self, value: object) -> bytes:
        if type(value) is not SemanticDependencyProductInput:
            raise TypeError("exact Code dependency product input required")
        return encode_dependency_product_input(value)

    def validate_invocation(
        self, value: object, invocation: SemanticContractInvocation
    ) -> None:
        _validate_dependency_product_invocation(
            value,
            invocation,
            source_profile_ref=invocation.profile_ref,
            source_profile_digest=invocation.profile_digest,
        )


def _validate_dependency_product_invocation(
    value: object,
    invocation: SemanticContractInvocation,
    *,
    source_profile_ref: str,
    source_profile_digest: ContentDigest,
) -> None:
    if type(value) is not SemanticDependencyProductInput:
        raise TypeError("exact Code dependency product input required")
    value.__post_init__()
    expected = tuple(
        sorted(
            {item.coordinate for item in value.products},
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    if (
        value.package != invocation.target_package
        or value.intent.operation_kind != invocation.operation_kind
        or value.demand_set.profile_ref != source_profile_ref
        or value.demand_set.profile_digest != source_profile_digest
        or expected != invocation.dependencies
    ):
        raise ContractViolation("dependency input differs from invocation")


def dependency_product_input_body(
    value: SemanticDependencyProductInput, *, role: str = "semantic_dependencies"
) -> SemanticBody:
    wire = encode_dependency_product_input(value)
    digest = ContentDigest.of_bytes(wire)
    return SemanticBody(
        SemanticValueCoordinate(
            role,
            SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF,
            f"code-dependency-input:{digest.value}",
            digest,
            len(wire),
        ),
        wire,
    )


__all__ = [
    "DEPENDENCY_INPUT_CODEC_IMPLEMENTATION",
    "SEMANTIC_DEPENDENCY_PRODUCT_INPUT",
    "SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF",
    "SemanticDependencyProductInputCodec",
    "decode_dependency_product_input",
    "dependency_product_input_body",
    "encode_dependency_product_input",
]
