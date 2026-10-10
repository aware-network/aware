"""Context-bound strict codecs for the Code materialization catalog."""

from __future__ import annotations

import json

from .contracts import (
    ContractViolation,
    SemanticContractRef,
    SemanticPackageCoordinate,
)
from .materialization_catalog import (
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticPackagePlanningContext,
)
from .materialization_planning import (
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
)

_MAX_WIRE_BYTES = 4_000_000


def encode_code_semantic_contract_catalog(
    value: CodeSemanticContractCatalog,
) -> bytes:
    if type(value) is not CodeSemanticContractCatalog:
        raise TypeError("catalog must be exact Code catalog")
    return _encode(value.to_wire())


def decode_code_semantic_contract_catalog(
    wire: bytes,
    *,
    catalog_ref: str,
    catalog_generation: int,
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...],
) -> CodeSemanticContractCatalog:
    expected = CodeSemanticContractCatalog.create(
        catalog_ref=catalog_ref,
        catalog_generation=catalog_generation,
        entries=entries,
    )
    _require_exact_wire(wire, expected.to_wire(), "Code catalog")
    return expected


def encode_code_semantic_package_planning_context(
    value: CodeSemanticPackagePlanningContext,
) -> bytes:
    if type(value) is not CodeSemanticPackagePlanningContext:
        raise TypeError("context must be exact Code planning context")
    return _encode(value.to_wire())


def decode_code_semantic_package_planning_context(
    wire: bytes,
    *,
    package: SemanticPackageCoordinate,
    package_family: str,
    package_role: str,
    manifest_contract: SemanticContractRef,
    code_intent: CodeSemanticMaterializationIntent,
    required_result_products: tuple[CodeSemanticRequiredResultProduct, ...],
    required_semantic_provider_keys: tuple[str, ...],
) -> CodeSemanticPackagePlanningContext:
    expected = CodeSemanticPackagePlanningContext.create(
        package=package,
        package_family=package_family,
        package_role=package_role,
        manifest_contract=manifest_contract,
        code_intent=code_intent,
        required_result_products=required_result_products,
        required_semantic_provider_keys=required_semantic_provider_keys,
    )
    _require_exact_wire(wire, expected.to_wire(), "Code planning context")
    return expected


def encode_code_semantic_contract_match(
    value: CodeSemanticContractMatch,
    *,
    context: CodeSemanticPackagePlanningContext,
    resolver: CodeSemanticContractCatalogResolver,
) -> bytes:
    match, _ = resolver.resolve(context)
    if type(value) is not CodeSemanticContractMatch:
        raise TypeError("match must be exact Code semantic match")
    value.__post_init__()
    value_wire = _encode(value.to_wire())
    expected_wire = _encode(match.to_wire())
    if value_wire != expected_wire:
        raise ContractViolation("Code match differs from fresh catalog resolution")
    return expected_wire


def decode_code_semantic_contract_match(
    wire: bytes,
    *,
    context: CodeSemanticPackagePlanningContext,
    resolver: CodeSemanticContractCatalogResolver,
) -> CodeSemanticContractMatch:
    match, _ = resolver.resolve(context)
    _require_exact_wire(wire, match.to_wire(), "Code match")
    return match


def encode_code_semantic_contract_match_admission(
    value: CodeSemanticContractMatchAdmission,
    *,
    context: CodeSemanticPackagePlanningContext,
    resolver: CodeSemanticContractCatalogResolver,
) -> bytes:
    _, admission = resolver.resolve(context)
    if type(value) is not CodeSemanticContractMatchAdmission:
        raise TypeError("admission must be exact Code semantic match admission")
    value.__post_init__()
    value_wire = _encode(value.to_wire())
    expected_wire = _encode(admission.to_wire())
    if value_wire != expected_wire:
        raise ContractViolation("match admission differs from fresh catalog resolution")
    return expected_wire


def decode_code_semantic_contract_match_admission(
    wire: bytes,
    *,
    context: CodeSemanticPackagePlanningContext,
    resolver: CodeSemanticContractCatalogResolver,
) -> CodeSemanticContractMatchAdmission:
    _, admission = resolver.resolve(context)
    _require_exact_wire(wire, admission.to_wire(), "match admission")
    return admission


def _require_exact_wire(wire: bytes, expected: dict[str, object], path: str) -> None:
    if type(wire) is not bytes:
        raise TypeError("wire must be exact bytes")
    if not wire or len(wire) > _MAX_WIRE_BYTES:
        raise ContractViolation("wire size unsupported")
    try:
        json.loads(wire.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation(f"{path} wire is not canonical JSON") from error
    if wire != _encode(expected):
        raise ContractViolation(f"{path} differs from exact semantic context")


def _encode(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


__all__ = [
    "decode_code_semantic_contract_catalog",
    "decode_code_semantic_contract_match",
    "decode_code_semantic_contract_match_admission",
    "decode_code_semantic_package_planning_context",
    "encode_code_semantic_contract_catalog",
    "encode_code_semantic_contract_match",
    "encode_code_semantic_contract_match_admission",
    "encode_code_semantic_package_planning_context",
]
