"""Neutral Workspace semantic source-package identity values.

This module owns portable values and strict codecs only.  Registry selection,
operation admission, persistence, and process-local capability issuance belong
to the contextual Workspace adapter.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from threading import RLock
from typing import ClassVar, NoReturn, Self, cast
from uuid import UUID
from weakref import ReferenceType, ref

ORIGIN_AUTHORITY_SCHEMA = "aware.workspace.semantic-source-package-origin-authority.v1"
_REGISTRY_PROJECTION_MEMBER_DOMAIN = (
    "aware.workspace.semantic-source-package-registry-projection-member.v1"
)
_REGISTRY_PROJECTION_SCHEMA = (
    "aware.workspace.semantic-source-package-registry-projection.v1"
)
_REGISTRY_PROJECTION_REF_SCHEMA = (
    "aware.workspace.semantic-source-package-registry-projection-ref.v1"
)
MODULE_MEMBERSHIP_AUTHORITY_SCHEMA = (
    "aware.workspace.semantic-source-package-module-membership-authority.v1"
)
ORIGIN_MEMBERSHIP_ADMISSION_SCHEMA = (
    "aware.workspace.semantic-source-package-origin-membership-admission.v1"
)
ORIGIN_SELECTION_RECORD_SCHEMA = (
    "aware.workspace.semantic-source-package-origin-selection-record.v1"
)
INGRESS_IDENTITY_AUTHORITY_SCHEMA = (
    "aware.workspace.semantic-source-package-ingress-identity-authority.v1"
)
_PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA = (
    "aware.workspace.semantic-provider-delta-request-key-preimage.v1"
)
_PROVIDER_REQUEST_BINDING_ADMISSION_SCHEMA = (
    "aware.workspace.semantic-source-package-provider-request-binding-admission.v1"
)
OPERATION_ORIGIN_JOIN_ADMISSION_SCHEMA = (
    "aware.workspace.semantic-source-package-operation-origin-join-admission.v1"
)
OPERATION_ORIGIN_JOIN_RECEIPT_SCHEMA = (
    "aware.workspace.semantic-source-package-operation-origin-join-journal-receipt.v1"
)
ORIGIN_ADMISSION_SCHEMA = "aware.workspace.semantic-source-package-origin-admission.v1"
CODEC_VERSION = 1

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_PACKAGE_COORDINATE = re.compile(
    r"^module-package:([a-z0-9][a-z0-9._-]*)/([a-z0-9][a-z0-9._-]*)$"
)
_SELECTION_BASES = frozenset({"expected_branch_head", "session_baseline"})
_ISSUANCE_LOCK = RLock()


class WorkspaceSemanticSourcePackageIdentityError(ValueError):
    """Raised when portable source-package identity evidence is inexact."""


@dataclass(frozen=True, slots=True)
class _IssuanceRecord:
    reference: ReferenceType[object]
    canonical_bytes: bytes


_ISSUANCE_BY_ID: dict[int, _IssuanceRecord] = {}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(domain: str, body: Mapping[str, object]) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            domain.encode("utf-8") + b"\0" + _canonical_bytes(body)
        ).hexdigest()
    )


def _plain_sha(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _exact[T](value: object, expected: type[T], field: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    return value


def _text(value: object, field: str) -> str:
    result = _exact(value, str, field)
    try:
        result.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be UTF-8 text"
        ) from error
    if (
        not result
        or result.strip() != result
        or unicodedata.normalize("NFC", result) != result
    ):
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be nonempty canonical text"
        )
    return result


def _token(value: object, field: str) -> str:
    result = _text(value, field)
    if any(character.isspace() for character in result):
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must not contain whitespace"
        )
    return result


def _digest_value(value: object, field: str) -> str:
    result = _exact(value, str, field)
    if _DIGEST.fullmatch(result) is None:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be sha256:<64 lowercase hex>"
        )
    return result


def _uuid(value: object, field: str) -> str:
    result = _token(value, field)
    try:
        canonical = str(UUID(result))
    except ValueError as error:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be a canonical UUID"
        ) from error
    if result != canonical:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be a lowercase canonical UUID"
        )
    return result


def _non_negative(value: object, field: str) -> int:
    result = _exact(value, int, field)
    if result < 0:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be nonnegative"
        )
    return result


def _relative_path(value: object, field: str) -> str:
    result = _text(value, field)
    if (
        result.startswith("/")
        or result.endswith("/")
        or "\\" in result
        or "\0" in result
    ):
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be a canonical relative POSIX path"
        )
    components = result.split("/")
    if any(not item or item in {".", ".."} for item in components):
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} contains a forbidden path component"
        )
    if PurePosixPath(*components).as_posix() != result:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be a canonical relative POSIX path"
        )
    return result


def _coordinate(value: object, field: str) -> str:
    result = _token(value, field)
    if _PACKAGE_COORDINATE.fullmatch(result) is None:
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} must be an exact module-package coordinate"
        )
    return result


def _dict(value: object, field: str) -> dict[str, object]:
    result = _exact(value, dict, field)
    if any(type(key) is not str for key in result):
        raise TypeError(f"{field} keys must be exact str")
    return cast(dict[str, object], result)


def _list(value: object, field: str) -> list[object]:
    return cast(list[object], _exact(value, list, field))


def _strict_json(value: object, field: str) -> object:
    if value is None or type(value) in {str, bool, int}:
        if type(value) is str:
            _text(value, field)
        return value
    if type(value) is list:
        return [
            _strict_json(item, f"{field}[{index}]")
            for index, item in enumerate(cast(list[object], value))
        ]
    if type(value) is dict:
        body = _dict(value, field)
        return {
            _text(key, f"{field}.key"): _strict_json(item, f"{field}.{key}")
            for key, item in body.items()
        }
    raise TypeError(f"{field} contains an unsupported JSON value")


def _keys(value: dict[str, object], expected: frozenset[str], field: str) -> None:
    if frozenset(value) != expected or len(value) != len(expected):
        raise WorkspaceSemanticSourcePackageIdentityError(
            f"{field} has an unexpected field set"
        )


def _decode_canonical(value: object) -> dict[str, object]:
    raw = _exact(value, bytes, "canonical bytes")

    def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in items:
            if key in result:
                raise WorkspaceSemanticSourcePackageIdentityError(
                    f"duplicate JSON key: {key}"
                )
            result[key] = item
        return result

    def _float(_: str) -> NoReturn:
        raise WorkspaceSemanticSourcePackageIdentityError("JSON floats are forbidden")

    try:
        decoded = raw.decode("utf-8", errors="strict")
        payload = json.loads(
            decoded,
            object_pairs_hook=_pairs,
            parse_float=_float,
            parse_constant=_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceSemanticSourcePackageIdentityError(
            "canonical bytes are invalid JSON"
        ) from error
    body = _dict(payload, "canonical body")
    if _canonical_bytes(body) != raw:
        raise WorkspaceSemanticSourcePackageIdentityError(
            "input bytes are not exact canonical JSON"
        )
    return body


def _register(value: object, wire: dict[str, object]) -> None:
    identity = id(value)
    canonical = _canonical_bytes(_strict_json(wire, "portable wire"))
    with _ISSUANCE_LOCK:
        existing = _ISSUANCE_BY_ID.get(identity)
        if existing is not None and existing.reference() is value:
            if existing.canonical_bytes != canonical:
                raise WorkspaceSemanticSourcePackageIdentityError(
                    "portable value was mutated after construction"
                )
            return

        def _discard(reference: ReferenceType[object]) -> None:
            with _ISSUANCE_LOCK:
                current = _ISSUANCE_BY_ID.get(identity)
                if current is not None and current.reference is reference:
                    del _ISSUANCE_BY_ID[identity]

        reference = ref(value, _discard)
        _ISSUANCE_BY_ID[identity] = _IssuanceRecord(reference, canonical)


def _require(value: object, wire: dict[str, object]) -> None:
    identity = id(value)
    canonical = _canonical_bytes(_strict_json(wire, "portable wire"))
    with _ISSUANCE_LOCK:
        existing = _ISSUANCE_BY_ID.get(identity)
        if (
            existing is None
            or existing.reference() is not value
            or existing.canonical_bytes != canonical
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "portable value is unissued or was mutated"
            )


class _Portable:
    _schema: ClassVar[str]
    schema: str = ""
    codec_version: int = 0

    def __copy__(self) -> NoReturn:
        raise WorkspaceSemanticSourcePackageIdentityError(
            "portable values cannot be copied"
        )

    def __deepcopy__(self, memo: object) -> NoReturn:
        del memo
        raise WorkspaceSemanticSourcePackageIdentityError(
            "portable values cannot be copied"
        )

    def __reduce_ex__(self, protocol: object) -> NoReturn:
        del protocol
        raise WorkspaceSemanticSourcePackageIdentityError(
            "portable values cannot be pickled"
        )

    def _wire_unchecked(self) -> dict[str, object]:
        raise NotImplementedError

    def to_wire(self) -> dict[str, object]:
        if type(self) is not self.__class__:
            raise TypeError("portable value must be exact type")
        wire = self._wire_unchecked()
        _require(self, wire)
        return wire

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_wire())


def _finish[T: _Portable](value: T) -> T:
    _register(value, value._wire_unchecked())
    return value


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOriginAuthority(_Portable):
    workspace_id: str
    module_id: str
    module_package_id: str
    module_package_kind: str
    semantic_contract_role: str
    origin_digest: str
    schema: str = ORIGIN_AUTHORITY_SCHEMA
    codec_version: int = CODEC_VERSION

    _schema: ClassVar[str] = ORIGIN_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageOriginAuthority:
            raise TypeError("origin authority must be exact")
        _uuid(self.workspace_id, "workspace_id")
        _token(self.module_id, "module_id")
        _token(self.module_package_id, "module_package_id")
        _token(self.module_package_kind, "module_package_kind")
        _token(self.semantic_contract_role, "semantic_contract_role")
        if (
            self.schema != self._schema
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "origin codec is unsupported"
            )
        expected = _digest(self._schema, self._body())
        if self.origin_digest != expected:
            raise WorkspaceSemanticSourcePackageIdentityError(
                "origin digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "module_id": self.module_id,
            "module_package_id": self.module_package_id,
            "module_package_kind": self.module_package_kind,
            "schema": self.schema,
            "semantic_contract_role": self.semantic_contract_role,
            "workspace_id": self.workspace_id,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "origin_digest": self.origin_digest}

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        module_id: str,
        module_package_id: str,
        module_package_kind: str,
        semantic_contract_role: str,
    ) -> Self:
        body = {
            "codec_version": 1,
            "module_id": module_id,
            "module_package_id": module_package_id,
            "module_package_kind": module_package_kind,
            "schema": cls._schema,
            "semantic_contract_role": semantic_contract_role,
            "workspace_id": workspace_id,
        }
        return cls(
            workspace_id=workspace_id,
            module_id=module_id,
            module_package_id=module_package_id,
            module_package_kind=module_package_kind,
            semantic_contract_role=semantic_contract_role,
            origin_digest=_digest(cls._schema, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "origin authority")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "workspace_id",
                    "module_id",
                    "module_package_id",
                    "module_package_kind",
                    "semantic_contract_role",
                    "origin_digest",
                }
            ),
            "origin authority",
        )
        return cls(
            workspace_id=_exact(body["workspace_id"], str, "workspace_id"),
            module_id=_exact(body["module_id"], str, "module_id"),
            module_package_id=_exact(
                body["module_package_id"], str, "module_package_id"
            ),
            module_package_kind=_exact(
                body["module_package_kind"], str, "module_package_kind"
            ),
            semantic_contract_role=_exact(
                body["semantic_contract_role"], str, "semantic_contract_role"
            ),
            origin_digest=_exact(body["origin_digest"], str, "origin_digest"),
            schema=_exact(body["schema"], str, "schema"),
            codec_version=_exact(body["codec_version"], int, "codec_version"),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageRegistryProjectionMember(_Portable):
    module_id: str
    module_package_id: str
    module_package_kind: str
    manifest_relative_path: str
    semantic_contract_role: str
    semantic_contract_name: str
    semantic_contract_provider_key: str
    semantic_contract_module: str
    member_digest: str

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageRegistryProjectionMember:
            raise TypeError("registry projection member must be exact")
        for name in (
            "module_id",
            "module_package_id",
            "module_package_kind",
            "semantic_contract_role",
            "semantic_contract_name",
            "semantic_contract_provider_key",
            "semantic_contract_module",
        ):
            _token(getattr(self, name), name)
        _relative_path(self.manifest_relative_path, "manifest_relative_path")
        if self.member_digest != _digest(
            _REGISTRY_PROJECTION_MEMBER_DOMAIN, self._body()
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection member digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "manifest_relative_path": self.manifest_relative_path,
            "module_id": self.module_id,
            "module_package_id": self.module_package_id,
            "module_package_kind": self.module_package_kind,
            "semantic_contract_module": self.semantic_contract_module,
            "semantic_contract_name": self.semantic_contract_name,
            "semantic_contract_provider_key": self.semantic_contract_provider_key,
            "semantic_contract_role": self.semantic_contract_role,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "member_digest": self.member_digest}

    @classmethod
    def create(cls, **values: object) -> Self:
        expected = frozenset(
            {
                "module_id",
                "module_package_id",
                "module_package_kind",
                "manifest_relative_path",
                "semantic_contract_role",
                "semantic_contract_name",
                "semantic_contract_provider_key",
                "semantic_contract_module",
            }
        )
        body = dict(values)
        _keys(body, expected, "registry projection member fields")
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            member_digest=_digest(_REGISTRY_PROJECTION_MEMBER_DOMAIN, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "registry projection member")
        _keys(
            body,
            frozenset(
                {
                    "module_id",
                    "module_package_id",
                    "module_package_kind",
                    "manifest_relative_path",
                    "semantic_contract_role",
                    "semantic_contract_name",
                    "semantic_contract_provider_key",
                    "semantic_contract_module",
                    "member_digest",
                }
            ),
            "registry projection member",
        )
        return cls(**body)  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageRegistryProjection(_Portable):
    workspace_id: str
    members: tuple[WorkspaceSemanticSourcePackageRegistryProjectionMember, ...]
    registry_projection_digest: str
    schema: str = _REGISTRY_PROJECTION_SCHEMA
    codec_version: int = CODEC_VERSION

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageRegistryProjection:
            raise TypeError("registry projection must be exact")
        _uuid(self.workspace_id, "workspace_id")
        if type(self.members) is not tuple:
            raise TypeError("registry projection members must be exact tuple")
        coordinates: list[tuple[bytes, bytes]] = []
        digests: list[str] = []
        for member in self.members:
            exact = WorkspaceSemanticSourcePackageRegistryProjectionMember.from_wire(
                _exact(
                    member,
                    WorkspaceSemanticSourcePackageRegistryProjectionMember,
                    "registry projection member",
                ).to_wire()
            )
            coordinates.append(
                (
                    exact.module_id.encode("utf-8"),
                    exact.module_package_id.encode("utf-8"),
                )
            )
            digests.append(exact.member_digest)
        if coordinates != sorted(coordinates) or len(coordinates) != len(
            set(coordinates)
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection members must be canonically ordered and unique"
            )
        if len(digests) != len(set(digests)):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection member digests must be unique"
            )
        if (
            self.schema != _REGISTRY_PROJECTION_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection codec is unsupported"
            )
        if self.registry_projection_digest != _digest(
            _REGISTRY_PROJECTION_SCHEMA, self._body()
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "members": [member.to_wire() for member in self.members],
            "schema": self.schema,
            "workspace_id": self.workspace_id,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(),
            "registry_projection_digest": self.registry_projection_digest,
        }

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        members: tuple[WorkspaceSemanticSourcePackageRegistryProjectionMember, ...],
    ) -> Self:
        exact_members = _exact(members, tuple, "members")
        body = {
            "codec_version": 1,
            "members": [
                _exact(
                    member,
                    WorkspaceSemanticSourcePackageRegistryProjectionMember,
                    "registry projection member",
                ).to_wire()
                for member in exact_members
            ],
            "schema": _REGISTRY_PROJECTION_SCHEMA,
            "workspace_id": workspace_id,
        }
        return cls(
            workspace_id=workspace_id,
            members=exact_members,
            registry_projection_digest=_digest(_REGISTRY_PROJECTION_SCHEMA, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "registry projection")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "workspace_id",
                    "members",
                    "registry_projection_digest",
                }
            ),
            "registry projection",
        )
        return cls(
            workspace_id=_exact(body["workspace_id"], str, "workspace_id"),
            members=tuple(
                WorkspaceSemanticSourcePackageRegistryProjectionMember.from_wire(item)
                for item in _list(body["members"], "members")
            ),
            registry_projection_digest=_exact(
                body["registry_projection_digest"],
                str,
                "registry_projection_digest",
            ),
            schema=_exact(body["schema"], str, "schema"),
            codec_version=_exact(body["codec_version"], int, "codec_version"),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageRegistryProjectionRef(_Portable):
    ref: str
    digest: str
    size_bytes: int
    schema: str = _REGISTRY_PROJECTION_REF_SCHEMA
    codec_version: int = CODEC_VERSION
    role: str = "semantic_source_package_registry_projection"
    body_schema: str = _REGISTRY_PROJECTION_SCHEMA
    media_type: str = "application/json;charset=utf-8"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageRegistryProjectionRef:
            raise TypeError("registry projection ref must be exact")
        digest = _digest_value(self.digest, "digest")
        _non_negative(self.size_bytes, "size_bytes")
        expected_ref = (
            "cas://workspace-semantic-source-package-registry-projection/"
            f"{digest[7:]}.json"
        )
        if self.ref != expected_ref:
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection ref suffix mismatched digest"
            )
        if (
            self.schema != _REGISTRY_PROJECTION_REF_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.role != "semantic_source_package_registry_projection"
            or self.body_schema != _REGISTRY_PROJECTION_SCHEMA
            or self.media_type != "application/json;charset=utf-8"
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "registry projection ref constants are unsupported"
            )
        _finish(self)

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "body_schema": self.body_schema,
            "codec_version": self.codec_version,
            "digest": self.digest,
            "media_type": self.media_type,
            "ref": self.ref,
            "role": self.role,
            "schema": self.schema,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def create(
        cls, projection: WorkspaceSemanticSourcePackageRegistryProjection
    ) -> Self:
        return cls.for_revision(projection)

    @classmethod
    def for_revision(
        cls, projection: WorkspaceSemanticSourcePackageRegistryProjection
    ) -> Self:
        exact = WorkspaceSemanticSourcePackageRegistryProjection.from_wire(
            _exact(
                projection,
                WorkspaceSemanticSourcePackageRegistryProjection,
                "registry projection",
            ).to_wire()
        )
        body = exact.canonical_bytes()
        digest = _plain_sha(body)
        return cls(
            ref=(
                "cas://workspace-semantic-source-package-registry-projection/"
                f"{digest[7:]}.json"
            ),
            digest=digest,
            size_bytes=len(body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "registry projection ref")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "role",
                    "body_schema",
                    "media_type",
                    "ref",
                    "digest",
                    "size_bytes",
                }
            ),
            "registry projection ref",
        )
        return cls(**body)  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageModuleMembershipAuthority(_Portable):
    workspace_id: str
    selected_workspace_revision_id: str
    registry_projection_ref: WorkspaceSemanticSourcePackageRegistryProjectionRef
    registry_projection_digest: str
    module_id: str
    module_package_id: str
    module_package_kind: str
    manifest_relative_path: str
    semantic_contract_role: str
    semantic_contract_name: str
    semantic_contract_provider_key: str
    semantic_contract_module: str
    membership_digest: str
    schema: str = MODULE_MEMBERSHIP_AUTHORITY_SCHEMA
    codec_version: int = CODEC_VERSION

    _schema: ClassVar[str] = MODULE_MEMBERSHIP_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageModuleMembershipAuthority:
            raise TypeError("module membership authority must be exact")
        _uuid(self.workspace_id, "workspace_id")
        _uuid(
            self.selected_workspace_revision_id,
            "selected_workspace_revision_id",
        )
        for field_name in (
            "module_id",
            "module_package_id",
            "module_package_kind",
            "semantic_contract_role",
            "semantic_contract_name",
            "semantic_contract_provider_key",
            "semantic_contract_module",
        ):
            _token(getattr(self, field_name), field_name)
        WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
            _exact(
                self.registry_projection_ref,
                WorkspaceSemanticSourcePackageRegistryProjectionRef,
                "registry_projection_ref",
            ).to_wire()
        )
        _digest_value(self.registry_projection_digest, "registry_projection_digest")
        _relative_path(self.manifest_relative_path, "manifest_relative_path")
        if (
            self.schema != self._schema
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "membership codec is unsupported"
            )
        if self.membership_digest != _digest(self._schema, self._body()):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "membership digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "manifest_relative_path": self.manifest_relative_path,
            "module_id": self.module_id,
            "module_package_id": self.module_package_id,
            "module_package_kind": self.module_package_kind,
            "registry_projection_digest": self.registry_projection_digest,
            "registry_projection_ref": self.registry_projection_ref.to_wire(),
            "schema": self.schema,
            "semantic_contract_module": self.semantic_contract_module,
            "semantic_contract_name": self.semantic_contract_name,
            "semantic_contract_provider_key": self.semantic_contract_provider_key,
            "semantic_contract_role": self.semantic_contract_role,
            "selected_workspace_revision_id": self.selected_workspace_revision_id,
            "workspace_id": self.workspace_id,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "membership_digest": self.membership_digest}

    @classmethod
    def create(cls, **values: object) -> Self:
        projection_ref = _exact(
            values.get("registry_projection_ref"),
            WorkspaceSemanticSourcePackageRegistryProjectionRef,
            "registry_projection_ref",
        )
        body = {
            "schema": cls._schema,
            "codec_version": 1,
            **{
                key: item
                for key, item in values.items()
                if key != "registry_projection_ref"
            },
            "registry_projection_ref": projection_ref.to_wire(),
        }
        expected_keys = frozenset(
            {
                "schema",
                "codec_version",
                "workspace_id",
                "selected_workspace_revision_id",
                "registry_projection_ref",
                "registry_projection_digest",
                "module_id",
                "module_package_id",
                "module_package_kind",
                "manifest_relative_path",
                "semantic_contract_role",
                "semantic_contract_name",
                "semantic_contract_provider_key",
                "semantic_contract_module",
            }
        )
        _keys(body, expected_keys, "membership fields")
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            membership_digest=_digest(cls._schema, body),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "module membership authority")
        expected = frozenset(
            {
                "schema",
                "codec_version",
                "workspace_id",
                "selected_workspace_revision_id",
                "registry_projection_ref",
                "registry_projection_digest",
                "module_id",
                "module_package_id",
                "module_package_kind",
                "manifest_relative_path",
                "semantic_contract_role",
                "semantic_contract_name",
                "semantic_contract_provider_key",
                "semantic_contract_module",
                "membership_digest",
            }
        )
        _keys(body, expected, "module membership authority")
        return cls(
            **{  # pyright: ignore[reportArgumentType]
                key: item
                for key, item in body.items()
                if key != "registry_projection_ref"
            },
            registry_projection_ref=WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
                body["registry_projection_ref"]
            ),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOriginMembershipAdmission(_Portable):
    source_package_origin_digest: str
    selected_workspace_revision_id: str
    registry_projection_ref: WorkspaceSemanticSourcePackageRegistryProjectionRef
    registry_projection_digest: str
    module_package_membership_digest: str
    origin_membership_admission_digest: str
    schema: str = ORIGIN_MEMBERSHIP_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "member"

    _schema: ClassVar[str] = ORIGIN_MEMBERSHIP_ADMISSION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageOriginMembershipAdmission:
            raise TypeError("origin membership admission must be exact")
        for name in (
            "source_package_origin_digest",
            "registry_projection_digest",
            "module_package_membership_digest",
        ):
            _digest_value(getattr(self, name), name)
        _uuid(
            self.selected_workspace_revision_id,
            "selected_workspace_revision_id",
        )
        WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
            _exact(
                self.registry_projection_ref,
                WorkspaceSemanticSourcePackageRegistryProjectionRef,
                "registry_projection_ref",
            ).to_wire()
        )
        if (
            self.schema != self._schema
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.disposition != "member"
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "origin membership constants are unsupported"
            )
        if self.origin_membership_admission_digest != _digest(
            self._schema, self._body()
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "origin membership digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "disposition": self.disposition,
            "module_package_membership_digest": self.module_package_membership_digest,
            "registry_projection_digest": self.registry_projection_digest,
            "registry_projection_ref": self.registry_projection_ref.to_wire(),
            "schema": self.schema,
            "selected_workspace_revision_id": self.selected_workspace_revision_id,
            "source_package_origin_digest": self.source_package_origin_digest,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(),
            "origin_membership_admission_digest": self.origin_membership_admission_digest,
        }

    @classmethod
    def create(cls, **values: object) -> Self:
        projection_ref = _exact(
            values.get("registry_projection_ref"),
            WorkspaceSemanticSourcePackageRegistryProjectionRef,
            "registry_projection_ref",
        )
        body = {
            "schema": cls._schema,
            "codec_version": 1,
            "disposition": "member",
            **{
                key: item
                for key, item in values.items()
                if key != "registry_projection_ref"
            },
            "registry_projection_ref": projection_ref.to_wire(),
        }
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            origin_membership_admission_digest=_digest(cls._schema, body),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "origin membership admission")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "disposition",
                    "source_package_origin_digest",
                    "selected_workspace_revision_id",
                    "registry_projection_ref",
                    "registry_projection_digest",
                    "module_package_membership_digest",
                    "origin_membership_admission_digest",
                }
            ),
            "origin membership admission",
        )
        return cls(
            **{  # pyright: ignore[reportArgumentType]
                key: item
                for key, item in body.items()
                if key != "registry_projection_ref"
            },
            registry_projection_ref=WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
                body["registry_projection_ref"]
            ),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


class _ScalarPortable(_Portable):
    schema: str
    codec_version: int
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]]
    _digest_field: ClassVar[str]
    _constants: ClassVar[Mapping[str, object]] = {}

    def _body(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "codec_version": self.codec_version,
            **self._constants,
            **{name: getattr(self, name) for name, _ in self._fields},
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), self._digest_field: getattr(self, self._digest_field)}

    def _validate_scalar(self, expected_type: type[_ScalarPortable]) -> None:
        if type(self) is not expected_type:
            raise TypeError(f"{expected_type.__name__} must be exact")
        if (
            self.schema != self._schema
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                f"{expected_type.__name__} codec is unsupported"
            )
        for name, expected in self._constants.items():
            if getattr(self, name) != expected:
                raise WorkspaceSemanticSourcePackageIdentityError(
                    f"{expected_type.__name__}.{name} is unsupported"
                )
        for name, validator in self._fields:
            _ = validator(getattr(self, name), name)
        if getattr(self, self._digest_field) != _digest(self._schema, self._body()):
            raise WorkspaceSemanticSourcePackageIdentityError(
                f"{expected_type.__name__} digest mismatched"
            )
        _finish(self)

    @classmethod
    def create(cls, **values: object) -> Self:
        body = {"schema": cls._schema, "codec_version": 1, **cls._constants, **values}
        return cls(
            **values,
            **cls._constants,
            **{cls._digest_field: _digest(cls._schema, body)},
        )  # pyright: ignore[reportCallIssue, reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, cls.__name__)
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    cls._digest_field,
                    *cls._constants,
                    *(name for name, _ in cls._fields),
                }
            ),
            cls.__name__,
        )
        return cls(**body)  # pyright: ignore[reportCallIssue, reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageIngressIdentityAuthority(_ScalarPortable):
    workspace_id: str
    materialization_operation_id: str
    operation_request_digest: str
    origin_selection_digest: str
    request_position: int
    requested_package_coordinate: str
    module_package_id: str
    source_package_origin_digest: str
    module_package_membership_digest: str
    capture_attempt_digest: str
    source_snapshot_digest: str
    source_movement_digest: str
    package_name: str
    manifest_relative_path: str
    ingress_source_change_authority_digest: str
    ingress_identity_digest: str
    schema: str = INGRESS_IDENTITY_AUTHORITY_SCHEMA
    codec_version: int = CODEC_VERSION

    _schema: ClassVar[str] = INGRESS_IDENTITY_AUTHORITY_SCHEMA
    _digest_field: ClassVar[str] = "ingress_identity_digest"
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]] = (
        ("workspace_id", _uuid),
        ("materialization_operation_id", _uuid),
        ("operation_request_digest", _digest_value),
        ("origin_selection_digest", _digest_value),
        ("request_position", _non_negative),
        ("requested_package_coordinate", _coordinate),
        ("module_package_id", _token),
        ("source_package_origin_digest", _digest_value),
        ("module_package_membership_digest", _digest_value),
        ("capture_attempt_digest", _digest_value),
        ("source_snapshot_digest", _digest_value),
        ("source_movement_digest", _digest_value),
        ("package_name", _token),
        ("manifest_relative_path", _relative_path),
        ("ingress_source_change_authority_digest", _digest_value),
    )

    def __post_init__(self) -> None:
        self._validate_scalar(WorkspaceSemanticSourcePackageIngressIdentityAuthority)


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticProviderDeltaRequestKeyPreimage(_Portable):
    key_payload: dict[str, object]
    key_payload_sha256: str
    preimage_digest: str
    schema: str = _PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA
    codec_version: int = CODEC_VERSION
    key_scheme: str = "provider_delta_request:sha256"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticProviderDeltaRequestKeyPreimage:
            raise TypeError("provider request key preimage must be exact")
        payload = cast(
            dict[str, object],
            _strict_json(_dict(self.key_payload, "key_payload"), "key_payload"),
        )
        object.__setattr__(self, "key_payload", payload)
        _keys(
            payload,
            frozenset(
                {
                    "package",
                    "semantic_contract",
                    "current_delta_fingerprint",
                    "baseline_oig_commit_refs",
                    "baseline_ref",
                    "provider_delta_lane_state",
                    "source_change_set_digest",
                    "execution_authority",
                    "semantic_migration_authority",
                }
            ),
            "key_payload",
        )
        package = _dict(payload["package"], "key_payload.package")
        _keys(
            package,
            frozenset(
                {
                    "package_name",
                    "workspace_manifest_kind",
                    "manifest_path",
                    "source_code_package_id",
                    "package_authority",
                }
            ),
            "key_payload.package",
        )
        semantic_contract = _dict(
            payload["semantic_contract"], "key_payload.semantic_contract"
        )
        _keys(
            semantic_contract,
            frozenset({"module", "provider_key", "role", "name"}),
            "key_payload.semantic_contract",
        )
        baseline_refs = _dict(
            payload["baseline_oig_commit_refs"],
            "key_payload.baseline_oig_commit_refs",
        )
        _keys(
            baseline_refs,
            frozenset(
                {
                    "source_object_instance_graph_commit_id",
                    "semantic_object_instance_graph_commit_id",
                    "semantic_root_object_instance_graph_commit_id",
                }
            ),
            "key_payload.baseline_oig_commit_refs",
        )
        _strict_json(payload, "key_payload")
        if (
            self.schema != _PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.key_scheme != "provider_delta_request:sha256"
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "provider request key preimage constants are unsupported"
            )
        expected_payload_sha = _plain_sha(_canonical_bytes(payload))
        if self.key_payload_sha256 != expected_payload_sha:
            raise WorkspaceSemanticSourcePackageIdentityError(
                "provider request key payload digest mismatched"
            )
        if self.preimage_digest != _digest(
            _PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA, self._body()
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "provider request key preimage digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "key_payload": _strict_json(self.key_payload, "key_payload"),
            "key_payload_sha256": self.key_payload_sha256,
            "key_scheme": self.key_scheme,
            "schema": self.schema,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "preimage_digest": self.preimage_digest}

    @classmethod
    def create(cls, *, key_payload: dict[str, object]) -> Self:
        payload = cast(
            dict[str, object],
            _strict_json(_dict(key_payload, "key_payload"), "key_payload"),
        )
        payload_sha = _plain_sha(_canonical_bytes(payload))
        body = {
            "codec_version": 1,
            "key_payload": payload,
            "key_payload_sha256": payload_sha,
            "key_scheme": "provider_delta_request:sha256",
            "schema": _PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA,
        }
        return cls(
            key_payload=payload,
            key_payload_sha256=payload_sha,
            preimage_digest=_digest(_PROVIDER_REQUEST_KEY_PREIMAGE_SCHEMA, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "provider request key preimage")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "key_scheme",
                    "key_payload",
                    "key_payload_sha256",
                    "preimage_digest",
                }
            ),
            "provider request key preimage",
        )
        return cls(
            key_payload=_dict(body["key_payload"], "key_payload"),
            key_payload_sha256=_exact(
                body["key_payload_sha256"], str, "key_payload_sha256"
            ),
            preimage_digest=_exact(body["preimage_digest"], str, "preimage_digest"),
            schema=_exact(body["schema"], str, "schema"),
            codec_version=_exact(body["codec_version"], int, "codec_version"),
            key_scheme=_exact(body["key_scheme"], str, "key_scheme"),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageProviderRequestBindingAdmission(_ScalarPortable):
    materialization_operation_id: str
    operation_request_digest: str
    origin_selection_digest: str
    request_position: int
    requested_package_coordinate: str
    source_package_origin_digest: str
    module_package_membership_digest: str
    ingress_identity_digest: str
    semantic_contract_role: str
    semantic_contract_name: str
    semantic_contract_provider_key: str
    semantic_contract_module: str
    package_name: str
    provider_delta_request_key: str
    provider_request_key_preimage_digest: str
    provider_delta_operation_id: str
    provider_delta_operation_authority_digest: str
    selected_workspace_revision_id: str
    registry_projection_body_sha256: str
    registry_projection_digest: str
    provider_request_binding_digest: str
    schema: str = _PROVIDER_REQUEST_BINDING_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "bound"

    _schema: ClassVar[str] = _PROVIDER_REQUEST_BINDING_ADMISSION_SCHEMA
    _digest_field: ClassVar[str] = "provider_request_binding_digest"
    _constants: ClassVar[Mapping[str, object]] = {"disposition": "bound"}
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]] = (
        ("materialization_operation_id", _uuid),
        ("operation_request_digest", _digest_value),
        ("origin_selection_digest", _digest_value),
        ("request_position", _non_negative),
        ("requested_package_coordinate", _coordinate),
        ("source_package_origin_digest", _digest_value),
        ("module_package_membership_digest", _digest_value),
        ("ingress_identity_digest", _digest_value),
        ("semantic_contract_role", _token),
        ("semantic_contract_name", _token),
        ("semantic_contract_provider_key", _token),
        ("semantic_contract_module", _token),
        ("package_name", _token),
        ("provider_delta_request_key", _token),
        ("provider_request_key_preimage_digest", _digest_value),
        ("provider_delta_operation_id", _token),
        ("provider_delta_operation_authority_digest", _digest_value),
        ("selected_workspace_revision_id", _uuid),
        ("registry_projection_body_sha256", _digest_value),
        ("registry_projection_digest", _digest_value),
    )

    def __post_init__(self) -> None:
        self._validate_scalar(
            WorkspaceSemanticSourcePackageProviderRequestBindingAdmission
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOperationOriginJoinAdmission(_ScalarPortable):
    materialization_operation_id: str
    operation_request_digest: str
    origin_selection_digest: str
    request_position: int
    requested_package_coordinate: str
    source_package_origin_digest: str
    module_package_membership_digest: str
    ingress_identity_digest: str
    ingress_source_change_authority_digest: str
    provider_delta_request_key: str
    provider_request_binding_digest: str
    provider_delta_operation_id: str
    provider_delta_operation_authority_digest: str
    operation_origin_join_digest: str
    schema: str = OPERATION_ORIGIN_JOIN_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "joined"

    _schema: ClassVar[str] = OPERATION_ORIGIN_JOIN_ADMISSION_SCHEMA
    _digest_field: ClassVar[str] = "operation_origin_join_digest"
    _constants: ClassVar[Mapping[str, object]] = {"disposition": "joined"}
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]] = (
        ("materialization_operation_id", _uuid),
        ("operation_request_digest", _digest_value),
        ("origin_selection_digest", _digest_value),
        ("request_position", _non_negative),
        ("requested_package_coordinate", _coordinate),
        ("source_package_origin_digest", _digest_value),
        ("module_package_membership_digest", _digest_value),
        ("ingress_identity_digest", _digest_value),
        ("ingress_source_change_authority_digest", _digest_value),
        ("provider_delta_request_key", _token),
        ("provider_request_binding_digest", _digest_value),
        ("provider_delta_operation_id", _token),
        ("provider_delta_operation_authority_digest", _digest_value),
    )

    def __post_init__(self) -> None:
        self._validate_scalar(
            WorkspaceSemanticSourcePackageOperationOriginJoinAdmission
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOperationOriginJoinJournalReceipt(_ScalarPortable):
    materialization_operation_id: str
    request_position: int
    requested_package_coordinate: str
    operation_origin_record_digest: str
    provider_delta_operation_authority_digest: str
    journal_receipt_digest: str
    schema: str = OPERATION_ORIGIN_JOIN_RECEIPT_SCHEMA
    codec_version: int = CODEC_VERSION

    _schema: ClassVar[str] = OPERATION_ORIGIN_JOIN_RECEIPT_SCHEMA
    _digest_field: ClassVar[str] = "journal_receipt_digest"
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]] = (
        ("materialization_operation_id", _uuid),
        ("request_position", _non_negative),
        ("requested_package_coordinate", _coordinate),
        ("operation_origin_record_digest", _digest_value),
        ("provider_delta_operation_authority_digest", _digest_value),
    )

    def __post_init__(self) -> None:
        self._validate_scalar(
            WorkspaceSemanticSourcePackageOperationOriginJoinJournalReceipt
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOriginAdmission(_ScalarPortable):
    operation_authority_digest: str
    origin_digest: str
    selected_workspace_revision_id: str
    module_package_membership_digest: str
    origin_admission_digest: str
    schema: str = ORIGIN_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "admitted"

    _schema: ClassVar[str] = ORIGIN_ADMISSION_SCHEMA
    _digest_field: ClassVar[str] = "origin_admission_digest"
    _constants: ClassVar[Mapping[str, object]] = {"disposition": "admitted"}
    _fields: ClassVar[tuple[tuple[str, Callable[[object, str], object]], ...]] = (
        ("operation_authority_digest", _digest_value),
        ("origin_digest", _digest_value),
        ("selected_workspace_revision_id", _uuid),
        ("module_package_membership_digest", _digest_value),
    )

    def __post_init__(self) -> None:
        self._validate_scalar(WorkspaceSemanticSourcePackageOriginAdmission)


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOriginSelectionMember(_Portable):
    request_position: int
    requested_package_coordinate: str
    membership_authority: WorkspaceSemanticSourcePackageModuleMembershipAuthority
    origin_authority: WorkspaceSemanticSourcePackageOriginAuthority
    membership_admission: WorkspaceSemanticSourcePackageOriginMembershipAdmission

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageOriginSelectionMember:
            raise TypeError("origin selection member must be exact")
        _non_negative(self.request_position, "request_position")
        coordinate = _coordinate(
            self.requested_package_coordinate, "requested_package_coordinate"
        )
        membership = WorkspaceSemanticSourcePackageModuleMembershipAuthority.from_wire(
            _exact(
                self.membership_authority,
                WorkspaceSemanticSourcePackageModuleMembershipAuthority,
                "membership_authority",
            ).to_wire()
        )
        origin = WorkspaceSemanticSourcePackageOriginAuthority.from_wire(
            _exact(
                self.origin_authority,
                WorkspaceSemanticSourcePackageOriginAuthority,
                "origin_authority",
            ).to_wire()
        )
        admission = WorkspaceSemanticSourcePackageOriginMembershipAdmission.from_wire(
            _exact(
                self.membership_admission,
                WorkspaceSemanticSourcePackageOriginMembershipAdmission,
                "membership_admission",
            ).to_wire()
        )
        match = _PACKAGE_COORDINATE.fullmatch(coordinate)
        assert match is not None
        if (match.group(1), match.group(2)) != (
            membership.module_id,
            membership.module_package_id,
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection coordinate mismatched membership"
            )
        if (
            (
                origin.workspace_id,
                origin.module_id,
                origin.module_package_id,
                origin.module_package_kind,
                origin.semantic_contract_role,
            )
            != (
                membership.workspace_id,
                membership.module_id,
                membership.module_package_id,
                membership.module_package_kind,
                membership.semantic_contract_role,
            )
            or admission.source_package_origin_digest != origin.origin_digest
            or admission.module_package_membership_digest
            != membership.membership_digest
            or admission.selected_workspace_revision_id
            != membership.selected_workspace_revision_id
            or admission.registry_projection_ref.canonical_bytes()
            != membership.registry_projection_ref.canonical_bytes()
            or admission.registry_projection_digest
            != membership.registry_projection_digest
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection member authority mismatched"
            )
        _finish(self)

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "membership_admission": self.membership_admission.to_wire(),
            "membership_authority": self.membership_authority.to_wire(),
            "origin_authority": self.origin_authority.to_wire(),
            "request_position": self.request_position,
            "requested_package_coordinate": self.requested_package_coordinate,
        }

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "origin selection member")
        _keys(
            body,
            frozenset(
                {
                    "request_position",
                    "requested_package_coordinate",
                    "membership_authority",
                    "origin_authority",
                    "membership_admission",
                }
            ),
            "origin selection member",
        )
        return cls(
            request_position=_exact(body["request_position"], int, "request_position"),
            requested_package_coordinate=_exact(
                body["requested_package_coordinate"],
                str,
                "requested_package_coordinate",
            ),
            membership_authority=WorkspaceSemanticSourcePackageModuleMembershipAuthority.from_wire(
                body["membership_authority"]
            ),
            origin_authority=WorkspaceSemanticSourcePackageOriginAuthority.from_wire(
                body["origin_authority"]
            ),
            membership_admission=WorkspaceSemanticSourcePackageOriginMembershipAdmission.from_wire(
                body["membership_admission"]
            ),
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticSourcePackageOriginSelectionRecord(_Portable):
    workspace_id: str
    operation_id: str
    operation_request_digest: str
    branch_key: str
    selection_basis: str
    selected_workspace_revision_id: str
    registry_projection_ref: WorkspaceSemanticSourcePackageRegistryProjectionRef
    registry_projection_digest: str
    resolved_request_package_coordinates: tuple[str, ...]
    members: tuple[WorkspaceSemanticSourcePackageOriginSelectionMember, ...]
    selection_digest: str
    schema: str = ORIGIN_SELECTION_RECORD_SCHEMA
    codec_version: int = CODEC_VERSION

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticSourcePackageOriginSelectionRecord:
            raise TypeError("origin selection record must be exact")
        _uuid(self.workspace_id, "workspace_id")
        _uuid(self.operation_id, "operation_id")
        _digest_value(self.operation_request_digest, "operation_request_digest")
        _token(self.branch_key, "branch_key")
        if self.selection_basis not in _SELECTION_BASES:
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection_basis is unsupported"
            )
        _uuid(self.selected_workspace_revision_id, "selected_workspace_revision_id")
        WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
            _exact(
                self.registry_projection_ref,
                WorkspaceSemanticSourcePackageRegistryProjectionRef,
                "registry_projection_ref",
            ).to_wire()
        )
        _digest_value(self.registry_projection_digest, "registry_projection_digest")
        if (
            type(self.resolved_request_package_coordinates) is not tuple
            or type(self.members) is not tuple
        ):
            raise TypeError("selection arrays must be exact tuples")
        coordinates = tuple(
            _coordinate(item, "resolved coordinate")
            for item in self.resolved_request_package_coordinates
        )
        if len(coordinates) != len(set(coordinates)):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "request coordinates must be unique"
            )
        positions: list[int] = []
        for member in self.members:
            exact = _exact(
                member, WorkspaceSemanticSourcePackageOriginSelectionMember, "member"
            )
            WorkspaceSemanticSourcePackageOriginSelectionMember.from_wire(
                exact.to_wire()
            )
            if (
                exact.request_position >= len(coordinates)
                or coordinates[exact.request_position]
                != exact.requested_package_coordinate
            ):
                raise WorkspaceSemanticSourcePackageIdentityError(
                    "selection member position mismatched"
                )
            if (
                exact.membership_authority.selected_workspace_revision_id
                != self.selected_workspace_revision_id
                or exact.membership_authority.registry_projection_ref.canonical_bytes()
                != self.registry_projection_ref.canonical_bytes()
                or exact.membership_authority.registry_projection_digest
                != self.registry_projection_digest
            ):
                raise WorkspaceSemanticSourcePackageIdentityError(
                    "selection registry mismatched"
                )
            positions.append(exact.request_position)
        if positions != sorted(set(positions)):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection members must be position ordered and unique"
            )
        if (
            self.schema != ORIGIN_SELECTION_RECORD_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection codec is unsupported"
            )
        if self.selection_digest != _digest(
            ORIGIN_SELECTION_RECORD_SCHEMA, self._body()
        ):
            raise WorkspaceSemanticSourcePackageIdentityError(
                "selection digest mismatched"
            )
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "branch_key": self.branch_key,
            "codec_version": self.codec_version,
            "members": [item.to_wire() for item in self.members],
            "operation_id": self.operation_id,
            "operation_request_digest": self.operation_request_digest,
            "registry_projection_digest": self.registry_projection_digest,
            "registry_projection_ref": self.registry_projection_ref.to_wire(),
            "resolved_request_package_coordinates": list(
                self.resolved_request_package_coordinates
            ),
            "schema": self.schema,
            "selected_workspace_revision_id": self.selected_workspace_revision_id,
            "selection_basis": self.selection_basis,
            "workspace_id": self.workspace_id,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "selection_digest": self.selection_digest}

    @classmethod
    def create(cls, **values: object) -> Self:
        members = _exact(values.get("members"), tuple, "members")
        coordinates = _exact(
            values.get("resolved_request_package_coordinates"),
            tuple,
            "resolved_request_package_coordinates",
        )
        projection_ref = _exact(
            values.get("registry_projection_ref"),
            WorkspaceSemanticSourcePackageRegistryProjectionRef,
            "registry_projection_ref",
        )
        body = {
            "schema": ORIGIN_SELECTION_RECORD_SCHEMA,
            "codec_version": 1,
            **{
                key: value
                for key, value in values.items()
                if key
                not in {
                    "members",
                    "registry_projection_ref",
                    "resolved_request_package_coordinates",
                }
            },
            "registry_projection_ref": projection_ref.to_wire(),
            "members": [
                _exact(
                    item, WorkspaceSemanticSourcePackageOriginSelectionMember, "member"
                ).to_wire()
                for item in members
            ],
            "resolved_request_package_coordinates": list(coordinates),
        }
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            selection_digest=_digest(ORIGIN_SELECTION_RECORD_SCHEMA, body),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "origin selection record")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "workspace_id",
                    "operation_id",
                    "operation_request_digest",
                    "branch_key",
                    "selection_basis",
                    "selected_workspace_revision_id",
                    "registry_projection_ref",
                    "registry_projection_digest",
                    "resolved_request_package_coordinates",
                    "members",
                    "selection_digest",
                }
            ),
            "origin selection record",
        )
        return cls(
            workspace_id=_exact(body["workspace_id"], str, "workspace_id"),
            operation_id=_exact(body["operation_id"], str, "operation_id"),
            operation_request_digest=_exact(
                body["operation_request_digest"], str, "operation_request_digest"
            ),
            branch_key=_exact(body["branch_key"], str, "branch_key"),
            selection_basis=_exact(body["selection_basis"], str, "selection_basis"),
            selected_workspace_revision_id=_exact(
                body["selected_workspace_revision_id"],
                str,
                "selected_workspace_revision_id",
            ),
            registry_projection_ref=WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
                body["registry_projection_ref"]
            ),
            registry_projection_digest=_exact(
                body["registry_projection_digest"],
                str,
                "registry_projection_digest",
            ),
            resolved_request_package_coordinates=tuple(
                _exact(item, str, "coordinate")
                for item in _list(
                    body["resolved_request_package_coordinates"],
                    "resolved_request_package_coordinates",
                )
            ),
            members=tuple(
                WorkspaceSemanticSourcePackageOriginSelectionMember.from_wire(item)
                for item in _list(body["members"], "members")
            ),
            selection_digest=_exact(body["selection_digest"], str, "selection_digest"),
            schema=_exact(body["schema"], str, "schema"),
            codec_version=_exact(body["codec_version"], int, "codec_version"),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


__all__ = [
    "CODEC_VERSION",
    "INGRESS_IDENTITY_AUTHORITY_SCHEMA",
    "MODULE_MEMBERSHIP_AUTHORITY_SCHEMA",
    "OPERATION_ORIGIN_JOIN_ADMISSION_SCHEMA",
    "OPERATION_ORIGIN_JOIN_RECEIPT_SCHEMA",
    "ORIGIN_ADMISSION_SCHEMA",
    "ORIGIN_AUTHORITY_SCHEMA",
    "ORIGIN_MEMBERSHIP_ADMISSION_SCHEMA",
    "ORIGIN_SELECTION_RECORD_SCHEMA",
    "WorkspaceSemanticProviderDeltaRequestKeyPreimage",
    "WorkspaceSemanticSourcePackageIdentityError",
    "WorkspaceSemanticSourcePackageIngressIdentityAuthority",
    "WorkspaceSemanticSourcePackageModuleMembershipAuthority",
    "WorkspaceSemanticSourcePackageOperationOriginJoinAdmission",
    "WorkspaceSemanticSourcePackageOperationOriginJoinJournalReceipt",
    "WorkspaceSemanticSourcePackageOriginAdmission",
    "WorkspaceSemanticSourcePackageOriginAuthority",
    "WorkspaceSemanticSourcePackageOriginMembershipAdmission",
    "WorkspaceSemanticSourcePackageOriginSelectionMember",
    "WorkspaceSemanticSourcePackageOriginSelectionRecord",
    "WorkspaceSemanticSourcePackageProviderRequestBindingAdmission",
    "WorkspaceSemanticSourcePackageRegistryProjection",
    "WorkspaceSemanticSourcePackageRegistryProjectionMember",
    "WorkspaceSemanticSourcePackageRegistryProjectionRef",
]
