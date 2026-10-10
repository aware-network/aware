"""Canonical Code transport codecs for portable retained-input projections."""

from __future__ import annotations

import json
from typing import cast

from .codec import _binding, _package
from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractInvocation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyTarget,
)
from .materialization_planning_codec import _constraint
from .portable_semantic_package_authority import CodePortableSemanticContract
from .retained_input_projections import (
    MAX_PROJECTION_BODY_BYTES,
    MAX_PROJECTION_ITEMS,
    CodeSemanticDeclarationTarget,
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticPackageContextInput,
    CodeSemanticRegistryPackageInput,
    planning_input_wire,
)
from .runtime import SemanticBody


def _keys(value: object, keys: set[str]) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ContractViolation("projection field set differs")
    return value


def _rows(value: object) -> list:
    if type(value) is not list or len(value) > MAX_PROJECTION_ITEMS:
        raise ContractViolation("projection list exceeds bound or is not exact")
    return value


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate projection key")
        result[key] = value
    return result


def _load(body: bytes) -> dict:
    if type(body) is not bytes or len(body) > MAX_PROJECTION_BODY_BYTES:
        raise ContractViolation("projection bytes exceed bound or are not exact")
    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ContractViolation("invalid projection JSON") from exc
    if type(value) is not dict:
        raise ContractViolation("projection must be object")
    return value


def _entry(row: object) -> CodeSemanticDeclarationTarget:
    r = _keys(
        row, {"dependency_kind", "dependency_ref", "targets", "target_constraints"}
    )
    targets = []
    for raw in _rows(r["targets"]):
        t = _keys(raw, {"package", "semantic_root_refs"})
        targets.append(
            SemanticDependencyTarget(
                _package(t["package"], "target.package"),
                tuple(_rows(t["semantic_root_refs"])),
            )
        )
    return CodeSemanticDeclarationTarget(
        r["dependency_kind"],
        r["dependency_ref"],
        tuple(targets),
        tuple(_constraint(c, "constraint") for c in _rows(r["target_constraints"])),
    )


def encode_registry_package_input(value: CodeSemanticRegistryPackageInput) -> bytes:
    return RegistryPackageInputCodec().encode(value)


def decode_registry_package_input(body: bytes) -> CodeSemanticRegistryPackageInput:
    r = _keys(
        _load(body),
        {
            "contract",
            "manifest_contract_kind",
            "manifest_filename",
            "semantic_provider_key",
            "semantic_package_family",
            "semantic_package_kind",
            "semantic_contract",
            "supported_languages",
            "code_package_surface",
            "fqn_prefix",
            "owned_semantic_root_refs",
            "profile_ref",
            "profile_version",
            "profile_digest",
            "binding",
        },
    )
    c = _keys(r["semantic_contract"], {"role", "name", "provider_key", "coordinate"})
    value = CodeSemanticRegistryPackageInput(
        r["manifest_contract_kind"],
        r["manifest_filename"],
        r["semantic_provider_key"],
        r["semantic_package_family"],
        r["semantic_package_kind"],
        CodePortableSemanticContract(**c),
        tuple(_rows(r["supported_languages"])),
        r["code_package_surface"],
        r["fqn_prefix"],
        tuple(_rows(r["owned_semantic_root_refs"])),
        r["profile_ref"],
        r["profile_version"],
        ContentDigest.of_wire(r["profile_digest"]),
        _binding(r["binding"], "binding"),
    )
    _canonical(encode_registry_package_input(value), body)
    return value


def encode_package_context_input(value: CodeSemanticPackageContextInput) -> bytes:
    return PackageContextInputCodec().encode(value)


def decode_package_context_input(body: bytes) -> CodeSemanticPackageContextInput:
    r = _keys(
        _load(body),
        {
            "contract",
            "package",
            "source_identity_digest",
            "manifest_relative_path",
            "code_package_name",
            "semantic_version",
            "source_code_package_id",
            "config_id",
            "config_key",
        },
    )
    value = CodeSemanticPackageContextInput(
        _package(r["package"], "package"),
        ContentDigest.of_wire(r["source_identity_digest"]),
        r["manifest_relative_path"],
        r["code_package_name"],
        r["semantic_version"],
        r["source_code_package_id"],
        r["config_id"],
        r["config_key"],
    )
    _canonical(encode_package_context_input(value), body)
    return value


def encode_declaration_target_inventory(
    value: CodeSemanticDeclarationTargetInventory,
) -> bytes:
    return DeclarationTargetInventoryCodec().encode(value)


def decode_declaration_target_inventory(
    body: bytes,
) -> CodeSemanticDeclarationTargetInventory:
    r = _keys(_load(body), {"contract", "package", "source_identity_digest", "entries"})
    value = CodeSemanticDeclarationTargetInventory(
        _package(r["package"], "package"),
        ContentDigest.of_wire(r["source_identity_digest"]),
        tuple(_entry(e) for e in _rows(r["entries"])),
    )
    _canonical(encode_declaration_target_inventory(value), body)
    return value


def encode_dependency_planning_input(value: SemanticDependencyPlanningInput) -> bytes:
    return canonical_json_bytes(planning_input_wire(value))


def decode_dependency_planning_input(body: bytes) -> SemanticDependencyPlanningInput:
    r = _keys(
        _load(body), {"contract", "package", "source_identity_digest", "dependencies"}
    )
    entries = tuple(_entry(e) for e in _rows(r["dependencies"]))
    value = SemanticDependencyPlanningInput(
        _package(r["package"], "package"),
        ContentDigest.of_wire(r["source_identity_digest"]),
        tuple(
            SemanticAuthoredDependency(
                e.dependency_kind, e.dependency_ref, e.targets, e.target_constraints
            )
            for e in entries
        ),
    )
    _canonical(encode_dependency_planning_input(value), body)
    return value


def _canonical(expected: bytes, actual: bytes) -> None:
    if expected != actual:
        raise ContractViolation("projection wire is not canonical")


def _ref(key: str) -> SemanticContractRef:
    return SemanticContractRef(
        key,
        "1",
        ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "contract": key,
                    "revision": "input-only-projections.v1",
                    "max_bytes": MAX_PROJECTION_BODY_BYTES,
                    "max_items": MAX_PROJECTION_ITEMS,
                    "max_text_bytes": 4096,
                }
            )
        ),
    )


REGISTRY_PACKAGE_INPUT_REF = _ref("aware.code.semantic-registry-package-input.v1")
PACKAGE_CONTEXT_INPUT_REF = _ref("aware.code.semantic-package-context-input.v1")
DECLARATION_TARGET_INVENTORY_REF = _ref(
    "aware.code.semantic-declaration-target-inventory.v1"
)
DEPENDENCY_PLANNING_INPUT_REF = _ref("aware.code.semantic-dependency-planning-input.v1")


class _ProjectionCodec:
    value_type: type
    contract: SemanticContractRef

    @property
    def implementation(self) -> SemanticImplementationCoordinate:
        return SemanticImplementationCoordinate(
            self.contract.key + ".codec",
            ContentDigest.of_bytes(canonical_json_bytes(self.contract.to_wire())),
        )

    def encode(self, value: object) -> bytes:
        if type(value) is not self.value_type:
            raise ContractViolation("exact projection value required")
        projection = cast(
            CodeSemanticRegistryPackageInput
            | CodeSemanticPackageContextInput
            | CodeSemanticDeclarationTargetInventory,
            value,
        )
        projection.__post_init__()
        return canonical_json_bytes(projection.to_wire())

    def validate_invocation(
        self, value: object, invocation: SemanticContractInvocation
    ) -> None:
        self.encode(value)
        if (
            type(value)
            in (
                CodeSemanticPackageContextInput,
                CodeSemanticDeclarationTargetInventory,
                SemanticDependencyPlanningInput,
            )
            and cast(
                CodeSemanticPackageContextInput
                | CodeSemanticDeclarationTargetInventory
                | SemanticDependencyPlanningInput,
                value,
            ).package
            != invocation.target_package
        ):
            raise ContractViolation("projection target differs from invocation")
        # Issuers and cross-input source/profile joins are not established by this transport codec.


class RegistryPackageInputCodec(_ProjectionCodec):
    value_type = CodeSemanticRegistryPackageInput
    contract = REGISTRY_PACKAGE_INPUT_REF
    decode = staticmethod(decode_registry_package_input)


class PackageContextInputCodec(_ProjectionCodec):
    value_type = CodeSemanticPackageContextInput
    contract = PACKAGE_CONTEXT_INPUT_REF
    decode = staticmethod(decode_package_context_input)


class DeclarationTargetInventoryCodec(_ProjectionCodec):
    value_type = CodeSemanticDeclarationTargetInventory
    contract = DECLARATION_TARGET_INVENTORY_REF
    decode = staticmethod(decode_declaration_target_inventory)


class DependencyPlanningInputCodec(_ProjectionCodec):
    value_type = SemanticDependencyPlanningInput
    contract = DEPENDENCY_PLANNING_INPUT_REF
    decode = staticmethod(decode_dependency_planning_input)

    def encode(self, value: object) -> bytes:
        if type(value) is not SemanticDependencyPlanningInput:
            raise ContractViolation("exact planning input required")
        return encode_dependency_planning_input(value)


def retained_projection_body(value: object) -> SemanticBody:
    codecs = {
        CodeSemanticRegistryPackageInput: (
            RegistryPackageInputCodec(),
            "registry_package",
        ),
        CodeSemanticPackageContextInput: (
            PackageContextInputCodec(),
            "package_context",
        ),
        CodeSemanticDeclarationTargetInventory: (
            DeclarationTargetInventoryCodec(),
            "declaration_inventory",
        ),
        SemanticDependencyPlanningInput: (
            DependencyPlanningInputCodec(),
            "dependency_planning",
        ),
    }
    if type(value) not in codecs:
        raise ContractViolation("unsupported retained projection type")
    codec, role = codecs[type(value)]
    body = codec.encode(value)
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(
        SemanticValueCoordinate(
            role,
            codec.contract,
            f"code-retained-projection:{digest.value}",
            digest,
            len(body),
        ),
        body,
    )
