"""Requested branch Subjects, not issued Subjects or operational Object addresses.

Original Meta products own all identity calculations. These values carry their
results with explicit roles; a provider must independently verify derivation,
the selected source/branch association, permission and currentness before use.
No constructor, resolver, allocation, provider selection or live handle exists
in this module. Copies/decoded references remain freely constructible content.
"""
# pyright: strict

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast
from uuid import UUID

from .codec import WireError, canonical_bytes, decode_canonical

SUBJECT_REFERENCE_CONTRACT = "aware.ontology.requested-branch-subject.v1"
MAX_SUBJECT_REFERENCE_BYTES = 16_384


class SubjectReferenceError(ValueError):
    """Invalid reference content; never an authorization decision."""


class SubjectIdentityRole(StrEnum):
    SOURCE_ANCHOR = "source_anchor"
    PROJECTION = "projection"
    OBSERVABLE_CONFIG = "observable_config"


def _token(value: object) -> None:
    if type(value) is not str or not value:
        raise SubjectReferenceError("invalid_reference_token")
    try:
        length = len(value.encode("utf-8"))
    except UnicodeError as error:
        raise SubjectReferenceError("invalid_reference_token") from error
    if length > 512:
        raise SubjectReferenceError("invalid_reference_token")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise SubjectReferenceError("invalid_reference_token")


def _uuid(value: object) -> None:
    if type(value) is not UUID:
        raise SubjectReferenceError("exact_uuid_required")


@dataclass(frozen=True, slots=True)
class SubjectIdentity:
    """One declared original identity result; product refs are not issuer seals."""

    role: SubjectIdentityRole
    profile_ref: str
    product_ref: str
    class_id: UUID
    constructor_id: UUID
    value: UUID
    _initial: tuple[object, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if hasattr(self, "_initial"):
            self.require_unchanged()
            return
        object.__setattr__(self, "_initial", self._content())

    def _content(self) -> tuple[object, ...]:
        if type(self.role) is not SubjectIdentityRole:
            raise SubjectReferenceError("identity_role_invalid")
        _token(self.profile_ref)
        if (
            type(self.product_ref) is not str
            or re.fullmatch(
                r"meta-identity-product:sha256:[0-9a-f]{64}", self.product_ref
            )
            is None
        ):
            raise SubjectReferenceError("identity_product_ref_invalid")
        for value in (self.class_id, self.constructor_id, self.value):
            _uuid(value)
        return (
            self.role,
            self.profile_ref,
            self.product_ref,
            self.class_id,
            self.constructor_id,
            self.value,
        )

    def require_unchanged(self) -> tuple[object, ...]:
        if not hasattr(self, "_initial"):
            raise SubjectReferenceError("reference_uninitialized")
        try:
            content = self._content()
        except AttributeError as error:
            raise SubjectReferenceError("invalid_reference_fields") from error
        if content != self._initial:
            raise SubjectReferenceError("reference_mutated")
        return content


@dataclass(frozen=True, slots=True)
class SubjectReference:
    """Request an existing branch target; construction proves no such existence.

    ``branch_ref`` is the selected owner's explicit coordinate, never an
    inferred Git branch, default allocation or canonical OIG claim. Runtime
    Observable/address/history bindings are outputs of original admission,
    not fabricated from the three identities supplied here.
    """

    namespace_ref: str
    context_ref: str
    branch_ref: str
    projection: SubjectIdentity
    observable_config: SubjectIdentity
    source_anchor: SubjectIdentity
    _initial: tuple[object, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if hasattr(self, "_initial"):
            self.require_unchanged()
            return
        object.__setattr__(self, "_initial", self._content())

    def _content(self) -> tuple[object, ...]:
        for token in (self.namespace_ref, self.context_ref, self.branch_ref):
            _token(token)
        identities: list[tuple[object, ...]] = []
        for identity, role in (
            (self.projection, SubjectIdentityRole.PROJECTION),
            (self.observable_config, SubjectIdentityRole.OBSERVABLE_CONFIG),
            (self.source_anchor, SubjectIdentityRole.SOURCE_ANCHOR),
        ):
            if type(identity) is not SubjectIdentity:
                raise SubjectReferenceError("identity_role_mismatch")
            content = identity.require_unchanged()
            if identity.role is not role:
                raise SubjectReferenceError("identity_role_mismatch")
            identities.append(content)
        return (self.namespace_ref, self.context_ref, self.branch_ref, *identities)

    def require_unchanged(self) -> None:
        if not hasattr(self, "_initial"):
            raise SubjectReferenceError("reference_uninitialized")
        try:
            content = self._content()
        except AttributeError as error:
            raise SubjectReferenceError("invalid_reference_fields") from error
        if content != self._initial:
            raise SubjectReferenceError("reference_mutated")


def _identity_wire(identity: SubjectIdentity) -> dict[str, str]:
    identity.require_unchanged()
    return {
        "role": identity.role.value,
        "profile_ref": identity.profile_ref,
        "product_ref": identity.product_ref,
        "class_id": str(identity.class_id),
        "constructor_id": str(identity.constructor_id),
        "value": str(identity.value),
    }


def encode_subject_reference(reference: SubjectReference) -> bytes:
    if type(reference) is not SubjectReference:
        raise SubjectReferenceError("reference_type_invalid")
    reference.require_unchanged()
    body = canonical_bytes(
        {
            "contract": SUBJECT_REFERENCE_CONTRACT,
            "namespace_ref": reference.namespace_ref,
            "context_ref": reference.context_ref,
            "branch_ref": reference.branch_ref,
            "projection": _identity_wire(reference.projection),
            "observable_config": _identity_wire(reference.observable_config),
            "source_anchor": _identity_wire(reference.source_anchor),
        },
    )
    if len(body) > MAX_SUBJECT_REFERENCE_BYTES:
        raise SubjectReferenceError("reference_body_invalid")
    return body


def _record(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[object, object], value)) != keys:
        raise SubjectReferenceError("invalid_reference_fields")
    return cast(dict[str, object], value)


def _wire_uuid(value: object) -> UUID:
    if type(value) is not str:
        raise SubjectReferenceError("uuid_spelling_invalid")
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise SubjectReferenceError("uuid_spelling_invalid") from error
    if str(parsed) != value:
        raise SubjectReferenceError("uuid_spelling_invalid")
    return parsed


def _decode_identity(value: object) -> SubjectIdentity:
    row = _record(
        value,
        {"role", "profile_ref", "product_ref", "class_id", "constructor_id", "value"},
    )
    if type(row["role"]) is not str:
        raise SubjectReferenceError("identity_role_invalid")
    try:
        role = SubjectIdentityRole(row["role"])
    except ValueError as error:
        raise SubjectReferenceError("identity_role_invalid") from error
    _token(row["profile_ref"])
    _token(row["product_ref"])
    return SubjectIdentity(
        role,
        cast(str, row["profile_ref"]),
        cast(str, row["product_ref"]),
        _wire_uuid(row["class_id"]),
        _wire_uuid(row["constructor_id"]),
        _wire_uuid(row["value"]),
    )


def decode_subject_reference(body: bytes) -> SubjectReference:
    if type(body) is not bytes or not 1 <= len(body) <= MAX_SUBJECT_REFERENCE_BYTES:
        raise SubjectReferenceError("reference_body_invalid")
    try:
        row = _record(
            decode_canonical(body),
            {
                "contract",
                "namespace_ref",
                "context_ref",
                "branch_ref",
                "projection",
                "observable_config",
                "source_anchor",
            },
        )
        if row["contract"] != SUBJECT_REFERENCE_CONTRACT:
            raise SubjectReferenceError("unsupported_reference_contract")
        for key in ("namespace_ref", "context_ref", "branch_ref"):
            _token(row[key])
        reference = SubjectReference(
            cast(str, row["namespace_ref"]),
            cast(str, row["context_ref"]),
            cast(str, row["branch_ref"]),
            _decode_identity(row["projection"]),
            _decode_identity(row["observable_config"]),
            _decode_identity(row["source_anchor"]),
        )
        if encode_subject_reference(reference) != body:
            raise SubjectReferenceError("noncanonical_reference")
        return reference
    except (WireError, ValueError, TypeError, RecursionError, UnicodeError) as error:
        if isinstance(error, SubjectReferenceError):
            raise
        raise SubjectReferenceError("reference_body_invalid") from error
