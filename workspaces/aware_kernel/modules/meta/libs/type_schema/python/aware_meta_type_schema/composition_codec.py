"""Strict deterministic codecs for R2 fragment and composition authorities."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from .codec import _decode_type
from .composition import (
    TYPE_OWNER_BINDING_CONTRACT,
    TYPE_SCHEMA_CATALOG_ROOT_CONTRACT,
    TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT,
    TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
    ComposedPackageEvidence,
    ComposedTypeOwnerEvidence,
    TypeOwnerBinding,
    TypeSchemaCatalogRoot,
    TypeSchemaComposedSlice,
    TypeSchemaPackageRoot,
)
from .definition_fragment import (
    SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT,
    TYPE_DEFINITION_FRAGMENT_CONTRACT,
    SourceDefinitionBinding,
    TypeDefinitionFragment,
    TypeSchemaSourceAttributionFragment,
)
from .encoding import canonical_json
from .persistent_index import (
    decode_persistent_index_node,
    persistent_body_coordinate_from_wire,
    persistent_index_root_from_wire,
)
from .positive_reader import (
    PersistentIndexMembershipProof,
    PersistentIndexProofBundle,
)

SUPPORTED_COMPOSITION_CONTRACTS = (
    TYPE_DEFINITION_FRAGMENT_CONTRACT,
    SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT,
    TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
    TYPE_OWNER_BINDING_CONTRACT,
    TYPE_SCHEMA_CATALOG_ROOT_CONTRACT,
    TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT,
)


class TypeSchemaCompositionDecodeError(ValueError):
    """Raised when an R2 payload is unsupported, noncanonical, or substituted."""


def negotiate_composition_contract(
    offered: Sequence[str],
    *,
    supported: Sequence[str] = SUPPORTED_COMPOSITION_CONTRACTS,
) -> str:
    offered_values = _tokens(offered, "offered")
    supported_values = _tokens(supported, "supported")
    for contract in supported_values:
        if contract in offered_values:
            return contract
    raise TypeSchemaCompositionDecodeError(
        f"no supported contract; offered={list(offered_values)!r}, "
        f"supported={list(supported_values)!r}"
    )


def encode_composition_value(value: object) -> bytes:
    to_wire = getattr(value, "to_wire", None)
    if not callable(to_wire):
        raise TypeError("value must expose to_wire()")
    return canonical_json(to_wire()).encode("utf-8")


def decode_definition_fragment(payload: bytes | str) -> TypeDefinitionFragment:
    item, original = _root(payload)
    _exact(
        item,
        {"contract", "definition", "referenced_type_refs", "fragment_ref"},
        "$",
    )
    _contract(item, TYPE_DEFINITION_FRAGMENT_CONTRACT)
    try:
        value = TypeDefinitionFragment(
            definition=_decode_type(item["definition"], "$.definition"),
            referenced_type_refs=_text_array(item, "referenced_type_refs", "$"),
            fragment_ref=_text(item, "fragment_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaCompositionDecodeError(
            f"definition fragment invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def decode_source_attribution_fragment(
    payload: bytes | str,
) -> TypeSchemaSourceAttributionFragment:
    item, original = _root(payload)
    _exact(
        item,
        {
            "contract",
            "package_ref",
            "source_path",
            "document_coordinate_ref",
            "bindings",
            "attribution_ref",
        },
        "$",
    )
    _contract(item, SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT)
    try:
        bindings: list[SourceDefinitionBinding] = []
        for index, raw in enumerate(_array(item, "bindings", "$")):
            binding = _object(raw, f"$.bindings[{index}]")
            _exact(binding, {"type_ref", "definition"}, f"$.bindings[{index}]")
            bindings.append(
                SourceDefinitionBinding(
                    _text(binding, "type_ref", f"$.bindings[{index}]"),
                    persistent_body_coordinate_from_wire(binding["definition"]),
                )
            )
        value = TypeSchemaSourceAttributionFragment(
            package_ref=_text(item, "package_ref", "$"),
            source_path=_text(item, "source_path", "$"),
            document_coordinate_ref=_text(item, "document_coordinate_ref", "$"),
            bindings=tuple(bindings),
            attribution_ref=_text(item, "attribution_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaCompositionDecodeError(
            f"source attribution invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def decode_package_root(payload: bytes | str) -> TypeSchemaPackageRoot:
    item, original = _root(payload)
    _exact(
        item,
        {
            "contract",
            "package_ref",
            "package_name",
            "namespace",
            "semantic_version",
            "dependency_package_refs",
            "definition_index",
            "source_attribution_index",
            "package_root_ref",
        },
        "$",
    )
    _contract(item, TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT)
    try:
        value = TypeSchemaPackageRoot(
            package_ref=_text(item, "package_ref", "$"),
            package_name=_text(item, "package_name", "$"),
            namespace=_text(item, "namespace", "$"),
            semantic_version=_text(item, "semantic_version", "$"),
            dependency_package_refs=_text_array(item, "dependency_package_refs", "$"),
            definition_index=persistent_index_root_from_wire(item["definition_index"]),
            source_attribution_index=persistent_index_root_from_wire(
                item["source_attribution_index"]
            ),
            package_root_ref=_text(item, "package_root_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaCompositionDecodeError(
            f"package root invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def decode_type_owner_binding(payload: bytes | str) -> TypeOwnerBinding:
    item, original = _root(payload)
    _exact(item, {"contract", "type_ref", "package_ref", "owner_ref"}, "$")
    _contract(item, TYPE_OWNER_BINDING_CONTRACT)
    try:
        value = TypeOwnerBinding(
            type_ref=_text(item, "type_ref", "$"),
            package_ref=_text(item, "package_ref", "$"),
            owner_ref=_text(item, "owner_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaCompositionDecodeError(
            f"owner binding invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def decode_catalog_root(payload: bytes | str) -> TypeSchemaCatalogRoot:
    item, original = _root(payload)
    _exact(
        item,
        {
            "contract",
            "target_package_ref",
            "package_index",
            "owner_index",
            "package_count",
            "owner_count",
            "catalog_ref",
        },
        "$",
    )
    _contract(item, TYPE_SCHEMA_CATALOG_ROOT_CONTRACT)
    try:
        value = TypeSchemaCatalogRoot(
            target_package_ref=_text(item, "target_package_ref", "$"),
            package_index=persistent_index_root_from_wire(item["package_index"]),
            owner_index=persistent_index_root_from_wire(item["owner_index"]),
            package_count=_integer(item, "package_count", "$"),
            owner_count=_integer(item, "owner_count", "$"),
            catalog_ref=_text(item, "catalog_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaCompositionDecodeError(
            f"catalog root invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def decode_composed_slice(payload: bytes | str) -> TypeSchemaComposedSlice:
    item, original = _root(payload)
    _exact(
        item,
        {
            "contract",
            "catalog",
            "target_package_ref",
            "dependency_package_refs",
            "root_type_refs",
            "packages",
            "definitions",
            "owners",
            "membership_proofs",
            "slice_ref",
        },
        "$",
    )
    _contract(item, TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT)
    try:
        packages: list[ComposedPackageEvidence] = []
        for index, raw in enumerate(_array(item, "packages", "$")):
            package_evidence = _object(raw, f"$.packages[{index}]")
            _exact(
                package_evidence,
                {"package_ref", "package", "coordinate"},
                f"$.packages[{index}]",
            )
            packages.append(
                ComposedPackageEvidence(
                    _text(package_evidence, "package_ref", f"$.packages[{index}]"),
                    decode_package_root(
                        canonical_json(
                            _object(
                                package_evidence["package"],
                                f"$.packages[{index}].package",
                            )
                        ).encode()
                    ),
                    persistent_body_coordinate_from_wire(
                        package_evidence["coordinate"]
                    ),
                )
            )
        definitions = tuple(
            decode_definition_fragment(
                canonical_json(_object(raw, f"$.definitions[{index}]")).encode()
            )
            for index, raw in enumerate(_array(item, "definitions", "$"))
        )
        owners: list[ComposedTypeOwnerEvidence] = []
        for index, raw in enumerate(_array(item, "owners", "$")):
            owner = _object(raw, f"$.owners[{index}]")
            _exact(
                owner,
                {"type_ref", "package_ref", "owner", "package", "definition"},
                f"$.owners[{index}]",
            )
            owners.append(
                ComposedTypeOwnerEvidence(
                    _text(owner, "type_ref", f"$.owners[{index}]"),
                    _text(owner, "package_ref", f"$.owners[{index}]"),
                    persistent_body_coordinate_from_wire(owner["owner"]),
                    persistent_body_coordinate_from_wire(owner["package"]),
                    persistent_body_coordinate_from_wire(owner["definition"]),
                )
            )
        proof_wire = _object(item["membership_proofs"], "$.membership_proofs")
        _exact(
            proof_wire,
            {"contract", "memberships", "nodes", "bundle_ref"},
            "$.membership_proofs",
        )
        memberships: list[PersistentIndexMembershipProof] = []
        for index, raw in enumerate(
            _array(proof_wire, "memberships", "$.membership_proofs")
        ):
            membership = _object(raw, f"$.membership_proofs.memberships[{index}]")
            _exact(
                membership,
                {"contract", "root", "key", "value", "node_refs", "membership_ref"},
                f"$.membership_proofs.memberships[{index}]",
            )
            memberships.append(
                PersistentIndexMembershipProof(
                    root=persistent_index_root_from_wire(membership["root"]),
                    key=_text(membership, "key", "$.membership_proofs.memberships"),
                    value=persistent_body_coordinate_from_wire(membership["value"]),
                    node_refs=_text_array(
                        membership, "node_refs", "$.membership_proofs.memberships"
                    ),
                    membership_ref=_text(
                        membership,
                        "membership_ref",
                        "$.membership_proofs.memberships",
                    ),
                    contract=_text(
                        membership, "contract", "$.membership_proofs.memberships"
                    ),
                )
            )
        proof_nodes = tuple(
            decode_persistent_index_node(
                canonical_json(
                    _object(raw, f"$.membership_proofs.nodes[{index}]")
                ).encode()
            )
            for index, raw in enumerate(
                _array(proof_wire, "nodes", "$.membership_proofs")
            )
        )
        proof_bundle = PersistentIndexProofBundle(
            memberships=tuple(memberships),
            nodes=proof_nodes,
            bundle_ref=_text(proof_wire, "bundle_ref", "$.membership_proofs"),
            contract=_text(proof_wire, "contract", "$.membership_proofs"),
        )
        value = TypeSchemaComposedSlice(
            catalog=decode_catalog_root(
                canonical_json(_object(item["catalog"], "$.catalog")).encode()
            ),
            target_package_ref=_text(item, "target_package_ref", "$"),
            dependency_package_refs=_text_array(item, "dependency_package_refs", "$"),
            root_type_refs=_text_array(item, "root_type_refs", "$"),
            packages=tuple(packages),
            definitions=definitions,
            owners=tuple(owners),
            membership_proofs=proof_bundle,
            slice_ref=_text(item, "slice_ref", "$"),
            contract=_text(item, "contract", "$"),
        )
    except (TypeError, ValueError) as error:
        if isinstance(error, TypeSchemaCompositionDecodeError):
            raise
        raise TypeSchemaCompositionDecodeError(
            f"composed slice invalid: {error}"
        ) from error
    _canonical(original, value)
    return value


def _contract(item: Mapping[str, object], expected: str) -> None:
    contract = _text(item, "contract", "$")
    negotiate_composition_contract((contract,))
    if contract != expected:
        raise TypeSchemaCompositionDecodeError(
            f"decoder expected {expected!r}, received {contract!r}"
        )


def _root(payload: bytes | str) -> tuple[Mapping[str, object], bytes]:
    if isinstance(payload, bytes):
        original = payload
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TypeSchemaCompositionDecodeError("payload is not UTF-8") from error
    elif isinstance(payload, str):
        text = payload
        original = payload.encode("utf-8")
    else:
        raise TypeError("payload must be bytes or str")
    try:
        value = json.loads(text, object_pairs_hook=_without_duplicates)
    except json.JSONDecodeError as error:
        raise TypeSchemaCompositionDecodeError("payload is not JSON") from error
    return _object(value, "$"), original


def _without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TypeSchemaCompositionDecodeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise TypeSchemaCompositionDecodeError(f"{path} must be object")
    return value


def _array(value: Mapping[str, object], field: str, path: str) -> list[object]:
    result = value.get(field)
    if not isinstance(result, list):
        raise TypeSchemaCompositionDecodeError(f"{path}.{field} must be array")
    return result


def _text(value: Mapping[str, object], field: str, path: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise TypeSchemaCompositionDecodeError(f"{path}.{field} must be text")
    return result


def _integer(value: Mapping[str, object], field: str, path: str) -> int:
    result = value.get(field)
    if type(result) is not int:
        raise TypeSchemaCompositionDecodeError(f"{path}.{field} must be int")
    return result


def _text_array(value: Mapping[str, object], field: str, path: str) -> tuple[str, ...]:
    result = _array(value, field, path)
    if any(not isinstance(item, str) for item in result):
        raise TypeSchemaCompositionDecodeError(f"{path}.{field} must contain text")
    return tuple(item for item in result if isinstance(item, str))


def _tokens(values: Sequence[str], field: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, str) or not value for value in result):
        raise TypeSchemaCompositionDecodeError(f"{field} must contain text")
    if len(result) != len(set(result)):
        raise TypeSchemaCompositionDecodeError(f"{field} contains duplicates")
    return result


def _exact(value: Mapping[str, object], expected: set[str], path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise TypeSchemaCompositionDecodeError(
            f"{path} fields are not exact; "
            f"missing={sorted(expected - actual)!r}, extra={sorted(actual - expected)!r}"
        )


def _canonical(original: bytes, value: object) -> None:
    if encode_composition_value(value) != original:
        raise TypeSchemaCompositionDecodeError("payload is not canonical JSON")


__all__ = [
    "SUPPORTED_COMPOSITION_CONTRACTS",
    "TypeSchemaCompositionDecodeError",
    "decode_catalog_root",
    "decode_composed_slice",
    "decode_definition_fragment",
    "decode_package_root",
    "decode_source_attribution_fragment",
    "decode_type_owner_binding",
    "encode_composition_value",
    "negotiate_composition_contract",
]
