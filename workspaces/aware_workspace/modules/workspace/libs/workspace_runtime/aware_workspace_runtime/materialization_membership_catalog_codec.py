"""Context-bound strict codecs for Workspace materialization membership."""

from __future__ import annotations

import json
from typing import Protocol

from aware_code_semantic_contract_runtime import ContractViolation

from .materialization_membership_catalog import (
    WorkspaceSemanticAuthoredDependency,
    WorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationPackageEntry,
)

_MAX_WIRE_BYTES = 8_000_000


class _WireValue(Protocol):
    def __post_init__(self) -> None: ...
    def to_wire(self) -> object: ...


def encode_workspace_semantic_authored_dependency(
    value: WorkspaceSemanticAuthoredDependency,
) -> bytes:
    return _encode_exact(value, WorkspaceSemanticAuthoredDependency, "dependency")


def decode_workspace_semantic_authored_dependency(
    wire: bytes, *, expected: WorkspaceSemanticAuthoredDependency
) -> WorkspaceSemanticAuthoredDependency:
    return _decode_expected(
        wire, expected, WorkspaceSemanticAuthoredDependency, "dependency"
    )


def encode_workspace_semantic_materialization_package_entry(
    value: WorkspaceSemanticMaterializationPackageEntry,
) -> bytes:
    return _encode_exact(value, WorkspaceSemanticMaterializationPackageEntry, "entry")


def decode_workspace_semantic_materialization_package_entry(
    wire: bytes, *, expected: WorkspaceSemanticMaterializationPackageEntry
) -> WorkspaceSemanticMaterializationPackageEntry:
    return _decode_expected(
        wire, expected, WorkspaceSemanticMaterializationPackageEntry, "entry"
    )


def encode_workspace_semantic_materialization_membership_catalog(
    value: WorkspaceSemanticMaterializationMembershipCatalog,
) -> bytes:
    return _encode_exact(
        value, WorkspaceSemanticMaterializationMembershipCatalog, "catalog"
    )


def decode_workspace_semantic_materialization_membership_catalog(
    wire: bytes,
    *,
    catalog_ref: str,
    catalog_generation: int,
    entries: tuple[WorkspaceSemanticMaterializationPackageEntry, ...],
) -> WorkspaceSemanticMaterializationMembershipCatalog:
    expected = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref=catalog_ref,
        catalog_generation=catalog_generation,
        entries=entries,
    )
    return _decode_expected(
        wire, expected, WorkspaceSemanticMaterializationMembershipCatalog, "catalog"
    )


def _decode_expected[T: _WireValue](
    wire: bytes, expected: T, expected_type: type[T], path: str
) -> T:
    if type(expected) is not expected_type:
        raise TypeError(f"{path} expected value must be exact {expected_type.__name__}")
    expected.__post_init__()
    _parse(wire, path)
    if wire != _encode(expected.to_wire()):
        raise ContractViolation(f"{path} differs from exact Workspace context")
    return expected


def _encode_exact[T: _WireValue](value: T, expected: type[T], path: str) -> bytes:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    value.__post_init__()
    return _encode(value.to_wire())


def _parse(wire: bytes, path: str) -> None:
    if type(wire) is not bytes:
        raise TypeError("wire must be exact bytes")
    if not wire or len(wire) > _MAX_WIRE_BYTES:
        raise ContractViolation("wire size unsupported")
    try:
        value = json.loads(wire.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation(f"{path} wire is not canonical JSON") from error
    if type(value) is not dict:
        raise TypeError(f"{path} wire root must be exact object")


def _encode(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


__all__ = [
    "decode_workspace_semantic_authored_dependency",
    "decode_workspace_semantic_materialization_membership_catalog",
    "decode_workspace_semantic_materialization_package_entry",
    "encode_workspace_semantic_authored_dependency",
    "encode_workspace_semantic_materialization_membership_catalog",
    "encode_workspace_semantic_materialization_package_entry",
]
