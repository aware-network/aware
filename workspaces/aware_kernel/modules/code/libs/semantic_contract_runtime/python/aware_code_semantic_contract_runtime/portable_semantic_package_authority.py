"""Strict Code-owned portable semantic-package authority."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from threading import RLock
from typing import NoReturn, cast, override
from uuid import UUID
from weakref import ReferenceType, ref

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes

CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA = (
    "aware.code.portable-semantic-package-authority.v1"
)
CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_SCHEMA = (
    "aware.code.portable-semantic-package-authority-codec.v1"
)
CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION = 1
CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE = (
    "application/vnd.aware.code.portable-semantic-package-authority+json;version=1"
)
CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE = (
    "portable_semantic_package_authority"
)

_AUTHORITY_DOMAIN = b"aware.code.portable-semantic-package-authority.v1\0"
_CODEC_DOMAIN = b"aware.code.portable-semantic-package-authority-codec.v1\0"
_CAS_PREFIX = "cas://aware.code/portable-semantic-package-authority/sha256/"
_PACKAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SEMANTIC_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]*$")
_PACKAGE_REF = re.compile(
    r"^package:([A-Za-z0-9][A-Za-z0-9._-]*)@([0-9A-Za-z][0-9A-Za-z.+_-]*)$"
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSEALED_MARKER = object()
_CODE_PACKAGE_MARKER = object()
_SEMANTIC_PACKAGE_MARKER = object()
_SEMANTIC_CONTRACT_MARKER = object()
_EMPTY_MARKER = object()
_AUTHORITY_MARKER = object()
_REFERENCE_MARKER = object()


@dataclass(frozen=True, slots=True)
class _IssuanceRecord:
    reference: ReferenceType[object]
    canonical_bytes: bytes
    marker: object
    seal: str | None


_ISSUANCE_LOCK = RLock()
_ISSUANCE_BY_ID: dict[int, _IssuanceRecord] = {}


def _codec_declaration() -> dict[str, object]:
    return {
        "codec_version": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
        "media_type": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE,
        "schema": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_SCHEMA,
        "value_schema": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
    }


def _derive_codec_digest() -> ContentDigest:
    return ContentDigest.of_bytes(
        _CODEC_DOMAIN + canonical_json_bytes(_codec_declaration())
    )


CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST = _derive_codec_digest()


class _StrictPortableValue:
    __slots__: tuple[str, ...] = ()

    def __copy__(self) -> NoReturn:
        raise ContractViolation("portable authority values cannot be copied")

    def __deepcopy__(self, memo: object) -> NoReturn:
        del memo
        raise ContractViolation("portable authority values cannot be copied")

    @override
    def __reduce_ex__(self, protocol: object) -> NoReturn:
        del protocol
        raise ContractViolation("portable authority values cannot be pickled")


def _exact[T](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    return value


def _utf8_nfc(value: object, path: str) -> str:
    text = _exact(value, str, path)
    try:
        _ = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ContractViolation(f"{path} must be valid UTF-8 text") from error
    if unicodedata.normalize("NFC", text) != text:
        raise ContractViolation(f"{path} must be Unicode NFC")
    return text


def _token(value: object, path: str) -> str:
    text = _utf8_nfc(value, path)
    if not text or any(character.isspace() for character in text):
        raise ContractViolation(f"{path} must be nonempty token text")
    return text


def _nullable_token(value: object, path: str) -> str | None:
    return None if value is None else _token(value, path)


def _package_name(value: object, path: str) -> str:
    text = _token(value, path)
    if not _PACKAGE_NAME.fullmatch(text):
        raise ContractViolation(f"{path} is not a canonical package name")
    return text


def _semantic_version(value: object, path: str) -> str:
    text = _token(value, path)
    if not _SEMANTIC_VERSION.fullmatch(text):
        raise ContractViolation(f"{path} is not a canonical semantic version")
    return text


def _uuid(value: object, path: str) -> str:
    text = _token(value, path)
    try:
        canonical = str(UUID(text))
    except ValueError as error:
        raise ContractViolation(f"{path} must be a canonical UUID") from error
    if text != canonical:
        raise ContractViolation(f"{path} must be a lowercase canonical UUID")
    return text


def _nullable_uuid(value: object, path: str) -> str | None:
    return None if value is None else _uuid(value, path)


def _relative_path(value: object, path: str, *, allow_dot: bool) -> str:
    text = _utf8_nfc(value, path)
    if allow_dot and text == ".":
        return text
    if not text or text == "." or text.startswith("/") or text.endswith("/"):
        raise ContractViolation(f"{path} must be a canonical relative path")
    if "\\" in text or "\x00" in text:
        raise ContractViolation(f"{path} must be a canonical POSIX path")
    components = text.split("/")
    if any(
        not component or component in {".", ".."} or not component.strip()
        for component in components
    ):
        raise ContractViolation(f"{path} contains a forbidden path component")
    if PurePosixPath(*components).as_posix() != text:
        raise ContractViolation(f"{path} is not canonically reconstructed")
    return text


def _package_ref(value: object, path: str) -> str:
    text = _token(value, path)
    if not _PACKAGE_REF.fullmatch(text):
        raise ContractViolation(f"{path} must be a canonical versioned package ref")
    return text


def _ordered_tuple(
    value: object,
    path: str,
    validator: Callable[[object, str], str],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    items = cast(tuple[object, ...], value)
    admitted = tuple(
        validator(item, f"{path}[{index}]") for index, item in enumerate(items)
    )
    keys = tuple(item.encode("utf-8") for item in admitted)
    if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
        raise ContractViolation(f"{path} must be unique and UTF-8 byte ordered")
    return admitted


def _content_digest(value: object, path: str) -> ContentDigest:
    digest = _exact(value, ContentDigest, path)
    text = _exact(digest.value, str, f"{path}.value")
    if not _DIGEST.fullmatch(text):
        raise ContractViolation(f"{path} must be sha256:<64 lowercase hex>")
    return ContentDigest(text)


def _digest_from_wire(value: object, path: str) -> ContentDigest:
    text = _exact(value, str, path)
    if not _DIGEST.fullmatch(text):
        raise ContractViolation(f"{path} must be sha256:<64 lowercase hex>")
    return ContentDigest(text)


def _object(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact dict")
    result = cast(dict[object, object], value)
    if any(type(key) is not str for key in result):
        raise TypeError(f"{path} keys must be exact strings")
    return cast(dict[str, object], result)


def _array(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return cast(list[object], value)


def _keys(value: dict[str, object], expected: frozenset[str], path: str) -> None:
    if frozenset(value) != expected or len(value) != len(expected):
        raise ContractViolation(f"{path} has an unexpected field set")


def _wire_seal(value: Mapping[str, object]) -> str:
    return ContentDigest.of_bytes(canonical_json_bytes(value)).value


def _register_or_require_issuance(
    value: object,
    *,
    canonical_bytes: bytes,
    marker: object,
    seal: str | None,
    path: str,
) -> None:
    identity = id(value)
    with _ISSUANCE_LOCK:
        existing = _ISSUANCE_BY_ID.get(identity)
        if existing is not None:
            if existing.reference() is not value:
                del _ISSUANCE_BY_ID[identity]
            else:
                if (
                    existing.canonical_bytes != canonical_bytes
                    or existing.marker is not getattr(value, "_marker", None)
                    or existing.seal != (
                        None if seal is None else getattr(value, "_seal", None)
                    )
                ):
                    raise ContractViolation(f"{path} was mutated after construction")
                return

        if getattr(value, "_marker", None) is not marker or (
            seal is not None and getattr(value, "_seal", None) != seal
        ):
            raise ContractViolation(f"{path} construction is incomplete")

        def _discard(reference: ReferenceType[object]) -> None:
            with _ISSUANCE_LOCK:
                current = _ISSUANCE_BY_ID.get(identity)
                if current is not None and current.reference is reference:
                    del _ISSUANCE_BY_ID[identity]

        reference = ref(value, _discard)
        _ISSUANCE_BY_ID[identity] = _IssuanceRecord(
            reference=reference,
            canonical_bytes=canonical_bytes,
            marker=marker,
            seal=seal,
        )


def _require_issuance(
    value: object,
    *,
    canonical_bytes: bytes,
    marker: object,
    seal: str | None,
    path: str,
) -> None:
    identity = id(value)
    with _ISSUANCE_LOCK:
        existing = _ISSUANCE_BY_ID.get(identity)
        if existing is None or existing.reference() is not value:
            raise ContractViolation(f"{path} construction is incomplete")
        if (
            existing.canonical_bytes != canonical_bytes
            or existing.marker is not marker
            or existing.marker is not getattr(value, "_marker", None)
            or existing.seal != seal
            or existing.seal != (
                None if seal is None else getattr(value, "_seal", None)
            )
        ):
            raise ContractViolation(f"{path} was mutated after construction")


@dataclass(frozen=True, slots=True, weakref_slot=True)
class CodePortableCodePackage(_StrictPortableValue):
    name: str
    language: str
    manifest_kind: str
    source_code_package_id: str | None
    config_id: str | None
    config_key: str | None
    surface: str | None
    _seal: str = field(init=False, repr=False, compare=False)
    _marker: object = field(
        init=False, repr=False, compare=False, default=_UNSEALED_MARKER
    )

    def __post_init__(self) -> None:
        if type(self) is not CodePortableCodePackage:
            raise TypeError("code_package must be exact CodePortableCodePackage")
        seal = _wire_seal(_code_package_fields(self))
        marker = getattr(self, "_marker", None)
        if marker is _UNSEALED_MARKER:
            object.__setattr__(self, "_seal", seal)
            object.__setattr__(self, "_marker", _CODE_PACKAGE_MARKER)
        _register_or_require_issuance(
            self,
            canonical_bytes=canonical_json_bytes(_code_package_fields(self)),
            marker=_CODE_PACKAGE_MARKER,
            seal=seal,
            path="code_package",
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class CodePortableSemanticPackage(_StrictPortableValue):
    family: str
    kind: str
    name: str
    _seal: str = field(init=False, repr=False, compare=False)
    _marker: object = field(
        init=False, repr=False, compare=False, default=_UNSEALED_MARKER
    )

    def __post_init__(self) -> None:
        if type(self) is not CodePortableSemanticPackage:
            raise TypeError(
                "semantic_package must be exact CodePortableSemanticPackage"
            )
        seal = _wire_seal(_semantic_package_fields(self))
        marker = getattr(self, "_marker", None)
        if marker is _UNSEALED_MARKER:
            object.__setattr__(self, "_seal", seal)
            object.__setattr__(self, "_marker", _SEMANTIC_PACKAGE_MARKER)
        _register_or_require_issuance(
            self,
            canonical_bytes=canonical_json_bytes(_semantic_package_fields(self)),
            marker=_SEMANTIC_PACKAGE_MARKER,
            seal=seal,
            path="semantic_package",
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class CodePortableSemanticContract(_StrictPortableValue):
    role: str
    name: str
    provider_key: str
    coordinate: str
    _seal: str = field(init=False, repr=False, compare=False)
    _marker: object = field(
        init=False, repr=False, compare=False, default=_UNSEALED_MARKER
    )

    def __post_init__(self) -> None:
        if type(self) is not CodePortableSemanticContract:
            raise TypeError(
                "semantic_contract must be exact CodePortableSemanticContract"
            )
        seal = _wire_seal(_semantic_contract_fields(self))
        marker = getattr(self, "_marker", None)
        if marker is _UNSEALED_MARKER:
            object.__setattr__(self, "_seal", seal)
            object.__setattr__(self, "_marker", _SEMANTIC_CONTRACT_MARKER)
        _register_or_require_issuance(
            self,
            canonical_bytes=canonical_json_bytes(_semantic_contract_fields(self)),
            marker=_SEMANTIC_CONTRACT_MARKER,
            seal=seal,
            path="semantic_contract",
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class CodeEmptySemanticMetadata(_StrictPortableValue):
    _marker: object = field(
        init=False, repr=False, compare=False, default=_EMPTY_MARKER
    )

    def __post_init__(self) -> None:
        if type(self) is not CodeEmptySemanticMetadata:
            raise TypeError("semantic_metadata must be exact CodeEmptySemanticMetadata")
        if getattr(self, "_marker", None) is not _EMPTY_MARKER:
            raise ContractViolation("semantic_metadata construction is incomplete")
        _register_or_require_issuance(
            self,
            canonical_bytes=b"{}",
            marker=_EMPTY_MARKER,
            seal=None,
            path="semantic_metadata",
        )


@dataclass(frozen=True, slots=True, weakref_slot=True, init=False)
class CodePortableSemanticPackageAuthority(_StrictPortableValue):
    schema: str
    codec_version: int
    manifest_contract_kind: str
    manifest_relative_path: str
    code_package: CodePortableCodePackage
    semantic_provider_key: str
    semantic_package: CodePortableSemanticPackage
    semantic_contract: CodePortableSemanticContract
    semantic_version: str
    package_ref: str
    fqn_prefix: str
    sources_root: str
    declared_source_paths: tuple[str, ...]
    direct_dependency_package_refs: tuple[str, ...]
    owned_semantic_root_refs: tuple[str, ...]
    semantic_metadata: CodeEmptySemanticMetadata
    authority_digest: ContentDigest
    _marker: object = field(init=False, repr=False, compare=False)
    _seal: str = field(init=False, repr=False, compare=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ContractViolation(
            "use create_portable_semantic_package_authority or a strict decoder"
        )

    def __post_init__(self) -> None:
        _ = _authority_wire(self)

    def to_wire(self) -> dict[str, object]:
        return _authority_wire(self)

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(_authority_wire(self))

    @classmethod
    def from_wire(cls, wire: dict[str, object]) -> CodePortableSemanticPackageAuthority:
        if cls is not CodePortableSemanticPackageAuthority:
            raise TypeError("authority decoder class must be exact")
        return _authority_from_wire(wire)

    @classmethod
    def from_canonical_bytes(cls, value: bytes) -> CodePortableSemanticPackageAuthority:
        if cls is not CodePortableSemanticPackageAuthority:
            raise TypeError("authority decoder class must be exact")
        payload = _exact(value, bytes, "canonical authority bytes")
        try:
            text = payload.decode("utf-8", errors="strict")
            wire = cast(
                object,
                json.loads(
                    text,
                    object_pairs_hook=_unique_pairs,
                    parse_float=_reject_float,
                    parse_constant=_reject_constant,
                ),
            )
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ContractViolation("invalid canonical authority JSON") from error
        authority = _authority_from_wire(_object(wire, "authority"))
        if authority.canonical_bytes() != payload:
            raise ContractViolation("authority bytes are not exact canonical JSON")
        return authority


@dataclass(frozen=True, slots=True, weakref_slot=True, init=False)
class CodePortableSemanticPackageAuthorityRef(_StrictPortableValue):
    role: str
    schema: str
    media_type: str
    codec_version: int
    codec_digest: ContentDigest
    sha256: ContentDigest
    ref: str
    size_bytes: int
    _marker: object = field(init=False, repr=False, compare=False)
    _seal: str = field(init=False, repr=False, compare=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ContractViolation("use code_portable_semantic_package_authority_body_ref")

    def __post_init__(self) -> None:
        _validate_reference(self)


def _code_package_fields(package: CodePortableCodePackage) -> dict[str, object]:
    return {
        "config_id": _nullable_uuid(package.config_id, "code_package.config_id"),
        "config_key": _nullable_token(package.config_key, "code_package.config_key"),
        "language": _token(package.language, "code_package.language"),
        "manifest_kind": _token(package.manifest_kind, "code_package.manifest_kind"),
        "name": _package_name(package.name, "code_package.name"),
        "source_code_package_id": _nullable_uuid(
            package.source_code_package_id,
            "code_package.source_code_package_id",
        ),
        "surface": _nullable_token(package.surface, "code_package.surface"),
    }


def _code_package_wire(value: object) -> dict[str, object]:
    package = _exact(value, CodePortableCodePackage, "code_package")
    wire = _code_package_fields(package)
    _require_issuance(
        package,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_CODE_PACKAGE_MARKER,
        seal=_wire_seal(wire),
        path="code_package",
    )
    return wire


def _semantic_package_fields(
    package: CodePortableSemanticPackage,
) -> dict[str, object]:
    return {
        "family": _token(package.family, "semantic_package.family"),
        "kind": _token(package.kind, "semantic_package.kind"),
        "name": _package_name(package.name, "semantic_package.name"),
    }


def _semantic_package_wire(value: object) -> dict[str, object]:
    package = _exact(value, CodePortableSemanticPackage, "semantic_package")
    wire = _semantic_package_fields(package)
    _require_issuance(
        package,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_SEMANTIC_PACKAGE_MARKER,
        seal=_wire_seal(wire),
        path="semantic_package",
    )
    return wire


def _semantic_contract_fields(
    contract: CodePortableSemanticContract,
) -> dict[str, object]:
    return {
        "coordinate": _token(contract.coordinate, "semantic_contract.coordinate"),
        "name": _token(contract.name, "semantic_contract.name"),
        "provider_key": _token(contract.provider_key, "semantic_contract.provider_key"),
        "role": _token(contract.role, "semantic_contract.role"),
    }


def _semantic_contract_wire(value: object) -> dict[str, object]:
    contract = _exact(value, CodePortableSemanticContract, "semantic_contract")
    wire = _semantic_contract_fields(contract)
    _require_issuance(
        contract,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_SEMANTIC_CONTRACT_MARKER,
        seal=_wire_seal(wire),
        path="semantic_contract",
    )
    return wire


def _metadata_wire(value: object) -> dict[str, object]:
    metadata = _exact(value, CodeEmptySemanticMetadata, "semantic_metadata")
    _require_issuance(
        metadata,
        canonical_bytes=b"{}",
        marker=_EMPTY_MARKER,
        seal=None,
        path="semantic_metadata",
    )
    return {}


def _authority_payload(
    *,
    manifest_contract_kind: object,
    manifest_relative_path: object,
    code_package: object,
    semantic_provider_key: object,
    semantic_package: object,
    semantic_contract: object,
    semantic_version: object,
    package_ref: object,
    fqn_prefix: object,
    sources_root: object,
    declared_source_paths: object,
    direct_dependency_package_refs: object,
    owned_semantic_root_refs: object,
    semantic_metadata: object,
) -> dict[str, object]:
    code_wire = _code_package_wire(code_package)
    semantic_package_wire = _semantic_package_wire(semantic_package)
    semantic_contract_wire = _semantic_contract_wire(semantic_contract)
    manifest_kind = _token(manifest_contract_kind, "manifest_contract_kind")
    provider_key = _token(semantic_provider_key, "semantic_provider_key")
    version = _semantic_version(semantic_version, "semantic_version")
    current_package_ref = _package_ref(package_ref, "package_ref")
    source_root = _relative_path(sources_root, "sources_root", allow_dot=True)
    source_paths = _ordered_tuple(
        declared_source_paths,
        "declared_source_paths",
        lambda item, path: _relative_path(item, path, allow_dot=False),
    )
    dependency_refs = _ordered_tuple(
        direct_dependency_package_refs,
        "direct_dependency_package_refs",
        _package_ref,
    )
    semantic_roots = _ordered_tuple(
        owned_semantic_root_refs, "owned_semantic_root_refs", _token
    )
    if code_wire["manifest_kind"] != manifest_kind:
        raise ContractViolation("manifest kind inputs do not converge")
    if semantic_contract_wire["provider_key"] != provider_key:
        raise ContractViolation("semantic provider inputs do not converge")
    expected_package_ref = f"package:{semantic_package_wire['name']}@{version}"
    if current_package_ref != expected_package_ref:
        raise ContractViolation("package_ref differs from canonical derivation")
    if current_package_ref in dependency_refs:
        raise ContractViolation("a package cannot depend on itself")
    if source_root != ".":
        prefix = source_root + "/"
        if any(not item.startswith(prefix) for item in source_paths):
            raise ContractViolation("declared source path is outside sources_root")
    return {
        "codec_version": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
        "code_package": code_wire,
        "declared_source_paths": list(source_paths),
        "direct_dependency_package_refs": list(dependency_refs),
        "fqn_prefix": _token(fqn_prefix, "fqn_prefix"),
        "manifest_contract_kind": manifest_kind,
        "manifest_relative_path": _relative_path(
            manifest_relative_path, "manifest_relative_path", allow_dot=False
        ),
        "owned_semantic_root_refs": list(semantic_roots),
        "package_ref": current_package_ref,
        "schema": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
        "semantic_contract": semantic_contract_wire,
        "semantic_metadata": _metadata_wire(semantic_metadata),
        "semantic_package": semantic_package_wire,
        "semantic_provider_key": provider_key,
        "semantic_version": version,
        "sources_root": source_root,
    }


def _derive_authority_digest(payload: dict[str, object]) -> ContentDigest:
    return ContentDigest.of_bytes(_AUTHORITY_DOMAIN + canonical_json_bytes(payload))


def _issue_authority(
    payload: dict[str, object], digest: ContentDigest
) -> CodePortableSemanticPackageAuthority:
    result = object.__new__(CodePortableSemanticPackageAuthority)
    object.__setattr__(result, "schema", payload["schema"])
    object.__setattr__(result, "codec_version", payload["codec_version"])
    object.__setattr__(
        result, "manifest_contract_kind", payload["manifest_contract_kind"]
    )
    object.__setattr__(
        result, "manifest_relative_path", payload["manifest_relative_path"]
    )
    object.__setattr__(
        result, "code_package", _code_package_from_wire(payload["code_package"])
    )
    object.__setattr__(
        result, "semantic_provider_key", payload["semantic_provider_key"]
    )
    object.__setattr__(
        result,
        "semantic_package",
        _semantic_package_from_wire(payload["semantic_package"]),
    )
    object.__setattr__(
        result,
        "semantic_contract",
        _semantic_contract_from_wire(payload["semantic_contract"]),
    )
    object.__setattr__(result, "semantic_version", payload["semantic_version"])
    object.__setattr__(result, "package_ref", payload["package_ref"])
    object.__setattr__(result, "fqn_prefix", payload["fqn_prefix"])
    object.__setattr__(result, "sources_root", payload["sources_root"])
    object.__setattr__(
        result,
        "declared_source_paths",
        tuple(
            _exact(item, str, f"declared_source_paths[{index}]")
            for index, item in enumerate(
                _array(payload["declared_source_paths"], "declared_source_paths")
            )
        ),
    )
    object.__setattr__(
        result,
        "direct_dependency_package_refs",
        tuple(
            _exact(item, str, f"direct_dependency_package_refs[{index}]")
            for index, item in enumerate(
                _array(
                    payload["direct_dependency_package_refs"],
                    "direct_dependency_package_refs",
                )
            )
        ),
    )
    object.__setattr__(
        result,
        "owned_semantic_root_refs",
        tuple(
            _exact(item, str, f"owned_semantic_root_refs[{index}]")
            for index, item in enumerate(
                _array(
                    payload["owned_semantic_root_refs"],
                    "owned_semantic_root_refs",
                )
            )
        ),
    )
    object.__setattr__(result, "semantic_metadata", CodeEmptySemanticMetadata())
    object.__setattr__(result, "authority_digest", digest)
    object.__setattr__(result, "_marker", _AUTHORITY_MARKER)
    object.__setattr__(
        result,
        "_seal",
        _wire_seal({**payload, "authority_digest": digest.value}),
    )
    wire = {**payload, "authority_digest": digest.value}
    _register_or_require_issuance(
        result,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_AUTHORITY_MARKER,
        seal=_wire_seal(wire),
        path="portable authority",
    )
    result.__post_init__()
    return result


def _authority_wire(value: object) -> dict[str, object]:
    authority = _exact(
        value, CodePortableSemanticPackageAuthority, "portable authority"
    )
    if getattr(authority, "_marker", None) is not _AUTHORITY_MARKER:
        raise ContractViolation("portable authority construction is incomplete")
    if _exact(authority.schema, str, "authority.schema") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA
    ):
        raise ContractViolation("portable authority schema mismatched")
    if _exact(authority.codec_version, int, "authority.codec_version") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION
    ):
        raise ContractViolation("portable authority codec version mismatched")
    payload = _authority_payload(
        manifest_contract_kind=authority.manifest_contract_kind,
        manifest_relative_path=authority.manifest_relative_path,
        code_package=authority.code_package,
        semantic_provider_key=authority.semantic_provider_key,
        semantic_package=authority.semantic_package,
        semantic_contract=authority.semantic_contract,
        semantic_version=authority.semantic_version,
        package_ref=authority.package_ref,
        fqn_prefix=authority.fqn_prefix,
        sources_root=authority.sources_root,
        declared_source_paths=authority.declared_source_paths,
        direct_dependency_package_refs=authority.direct_dependency_package_refs,
        owned_semantic_root_refs=authority.owned_semantic_root_refs,
        semantic_metadata=authority.semantic_metadata,
    )
    supplied = _content_digest(authority.authority_digest, "authority_digest")
    expected = _derive_authority_digest(payload)
    if supplied.value != expected.value:
        raise ContractViolation("authority_digest differs from canonical derivation")
    wire = {**payload, "authority_digest": expected.value}
    _require_issuance(
        authority,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_AUTHORITY_MARKER,
        seal=_wire_seal(wire),
        path="portable authority",
    )
    return wire


def _code_package_from_wire(value: object) -> CodePortableCodePackage:
    root = _object(value, "code_package")
    _keys(
        root,
        frozenset(
            {
                "config_id",
                "config_key",
                "language",
                "manifest_kind",
                "name",
                "source_code_package_id",
                "surface",
            }
        ),
        "code_package",
    )
    return CodePortableCodePackage(
        name=_exact(root["name"], str, "code_package.name"),
        language=_exact(root["language"], str, "code_package.language"),
        manifest_kind=_exact(root["manifest_kind"], str, "code_package.manifest_kind"),
        source_code_package_id=(
            None
            if root["source_code_package_id"] is None
            else _exact(
                root["source_code_package_id"],
                str,
                "code_package.source_code_package_id",
            )
        ),
        config_id=(
            None
            if root["config_id"] is None
            else _exact(root["config_id"], str, "code_package.config_id")
        ),
        config_key=(
            None
            if root["config_key"] is None
            else _exact(root["config_key"], str, "code_package.config_key")
        ),
        surface=(
            None
            if root["surface"] is None
            else _exact(root["surface"], str, "code_package.surface")
        ),
    )


def _semantic_package_from_wire(value: object) -> CodePortableSemanticPackage:
    root = _object(value, "semantic_package")
    _keys(root, frozenset({"family", "kind", "name"}), "semantic_package")
    return CodePortableSemanticPackage(
        family=_exact(root["family"], str, "semantic_package.family"),
        kind=_exact(root["kind"], str, "semantic_package.kind"),
        name=_exact(root["name"], str, "semantic_package.name"),
    )


def _semantic_contract_from_wire(value: object) -> CodePortableSemanticContract:
    root = _object(value, "semantic_contract")
    _keys(
        root,
        frozenset({"coordinate", "name", "provider_key", "role"}),
        "semantic_contract",
    )
    return CodePortableSemanticContract(
        role=_exact(root["role"], str, "semantic_contract.role"),
        name=_exact(root["name"], str, "semantic_contract.name"),
        provider_key=_exact(
            root["provider_key"], str, "semantic_contract.provider_key"
        ),
        coordinate=_exact(root["coordinate"], str, "semantic_contract.coordinate"),
    )


def _authority_from_wire(value: object) -> CodePortableSemanticPackageAuthority:
    root = _object(value, "authority")
    _keys(
        root,
        frozenset(
            {
                "authority_digest",
                "codec_version",
                "code_package",
                "declared_source_paths",
                "direct_dependency_package_refs",
                "fqn_prefix",
                "manifest_contract_kind",
                "manifest_relative_path",
                "owned_semantic_root_refs",
                "package_ref",
                "schema",
                "semantic_contract",
                "semantic_metadata",
                "semantic_package",
                "semantic_provider_key",
                "semantic_version",
                "sources_root",
            }
        ),
        "authority",
    )
    schema = _exact(root["schema"], str, "authority.schema")
    if schema != CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA:
        raise ContractViolation("portable authority schema mismatched")
    codec_version = _exact(root["codec_version"], int, "authority.codec_version")
    if codec_version != CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION:
        raise ContractViolation("portable authority codec version mismatched")
    metadata = _object(root["semantic_metadata"], "semantic_metadata")
    _keys(metadata, frozenset(), "semantic_metadata")
    payload = _authority_payload(
        manifest_contract_kind=_exact(
            root["manifest_contract_kind"], str, "manifest_contract_kind"
        ),
        manifest_relative_path=_exact(
            root["manifest_relative_path"], str, "manifest_relative_path"
        ),
        code_package=_code_package_from_wire(root["code_package"]),
        semantic_provider_key=_exact(
            root["semantic_provider_key"], str, "semantic_provider_key"
        ),
        semantic_package=_semantic_package_from_wire(root["semantic_package"]),
        semantic_contract=_semantic_contract_from_wire(root["semantic_contract"]),
        semantic_version=_exact(root["semantic_version"], str, "semantic_version"),
        package_ref=_exact(root["package_ref"], str, "package_ref"),
        fqn_prefix=_exact(root["fqn_prefix"], str, "fqn_prefix"),
        sources_root=_exact(root["sources_root"], str, "sources_root"),
        declared_source_paths=tuple(
            _exact(item, str, f"declared_source_paths[{index}]")
            for index, item in enumerate(
                _array(root["declared_source_paths"], "declared_source_paths")
            )
        ),
        direct_dependency_package_refs=tuple(
            _exact(item, str, f"direct_dependency_package_refs[{index}]")
            for index, item in enumerate(
                _array(
                    root["direct_dependency_package_refs"],
                    "direct_dependency_package_refs",
                )
            )
        ),
        owned_semantic_root_refs=tuple(
            _exact(item, str, f"owned_semantic_root_refs[{index}]")
            for index, item in enumerate(
                _array(root["owned_semantic_root_refs"], "owned_semantic_root_refs")
            )
        ),
        semantic_metadata=CodeEmptySemanticMetadata(),
    )
    supplied = _digest_from_wire(root["authority_digest"], "authority_digest")
    expected = _derive_authority_digest(payload)
    if supplied.value != expected.value:
        raise ContractViolation("authority_digest differs from canonical derivation")
    return _issue_authority(payload, expected)


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation(f"duplicate JSON key {key}")
        result[key] = value
    return result


def _reject_float(value: str) -> NoReturn:
    raise ContractViolation(f"floating-point JSON value is forbidden: {value}")


def _reject_constant(value: str) -> NoReturn:
    raise ContractViolation(f"noncanonical JSON constant is forbidden: {value}")


def create_portable_semantic_package_authority(
    *,
    manifest_contract_kind: str,
    manifest_relative_path: str,
    code_package: CodePortableCodePackage,
    semantic_provider_key: str,
    semantic_package: CodePortableSemanticPackage,
    semantic_contract: CodePortableSemanticContract,
    semantic_version: str,
    package_ref: str,
    fqn_prefix: str,
    sources_root: str,
    declared_source_paths: tuple[str, ...],
    direct_dependency_package_refs: tuple[str, ...],
    owned_semantic_root_refs: tuple[str, ...],
    semantic_metadata: CodeEmptySemanticMetadata,
) -> CodePortableSemanticPackageAuthority:
    payload = _authority_payload(
        manifest_contract_kind=manifest_contract_kind,
        manifest_relative_path=manifest_relative_path,
        code_package=code_package,
        semantic_provider_key=semantic_provider_key,
        semantic_package=semantic_package,
        semantic_contract=semantic_contract,
        semantic_version=semantic_version,
        package_ref=package_ref,
        fqn_prefix=fqn_prefix,
        sources_root=sources_root,
        declared_source_paths=declared_source_paths,
        direct_dependency_package_refs=direct_dependency_package_refs,
        owned_semantic_root_refs=owned_semantic_root_refs,
        semantic_metadata=semantic_metadata,
    )
    return _issue_authority(payload, _derive_authority_digest(payload))


def _issue_reference(
    *, sha256: ContentDigest, ref: str, size_bytes: int
) -> CodePortableSemanticPackageAuthorityRef:
    result = object.__new__(CodePortableSemanticPackageAuthorityRef)
    object.__setattr__(
        result, "role", CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE
    )
    object.__setattr__(
        result, "schema", CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA
    )
    object.__setattr__(
        result, "media_type", CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE
    )
    object.__setattr__(
        result,
        "codec_version",
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
    )
    object.__setattr__(result, "codec_digest", _derive_codec_digest())
    object.__setattr__(result, "sha256", sha256)
    object.__setattr__(result, "ref", ref)
    object.__setattr__(result, "size_bytes", size_bytes)
    object.__setattr__(result, "_marker", _REFERENCE_MARKER)
    object.__setattr__(
        result,
        "_seal",
        _wire_seal(
            {
                "codec_digest": _derive_codec_digest().value,
                "codec_version": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
                "media_type": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE,
                "ref": ref,
                "role": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE,
                "schema": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
                "sha256": sha256.value,
                "size_bytes": size_bytes,
            }
        ),
    )
    wire: dict[str, object] = {
        "codec_digest": _derive_codec_digest().value,
        "codec_version": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
        "media_type": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE,
        "ref": ref,
        "role": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE,
        "schema": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
        "sha256": sha256.value,
        "size_bytes": size_bytes,
    }
    _register_or_require_issuance(
        result,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_REFERENCE_MARKER,
        seal=_wire_seal(wire),
        path="portable authority reference",
    )
    result.__post_init__()
    return result


def _validate_reference(value: object) -> None:
    reference = _exact(
        value,
        CodePortableSemanticPackageAuthorityRef,
        "portable authority reference",
    )
    if getattr(reference, "_marker", None) is not _REFERENCE_MARKER:
        raise ContractViolation(
            "portable authority reference construction is incomplete"
        )
    if _exact(reference.role, str, "reference.role") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE
    ):
        raise ContractViolation("portable authority reference role mismatched")
    if _exact(reference.schema, str, "reference.schema") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA
    ):
        raise ContractViolation("portable authority reference schema mismatched")
    if _exact(reference.media_type, str, "reference.media_type") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE
    ):
        raise ContractViolation("portable authority reference media type mismatched")
    if _exact(reference.codec_version, int, "reference.codec_version") != (
        CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION
    ):
        raise ContractViolation("portable authority reference codec version mismatched")
    codec_digest = _content_digest(reference.codec_digest, "reference.codec_digest")
    if codec_digest.value != _derive_codec_digest().value:
        raise ContractViolation("portable authority reference codec digest mismatched")
    body_digest = _content_digest(reference.sha256, "reference.sha256")
    size = _exact(reference.size_bytes, int, "reference.size_bytes")
    if size < 0:
        raise ContractViolation("reference.size_bytes must be nonnegative")
    expected_ref = _CAS_PREFIX + body_digest.value.removeprefix("sha256:") + ".json"
    if _exact(reference.ref, str, "reference.ref") != expected_ref:
        raise ContractViolation("portable authority reference URI mismatched")
    wire: dict[str, object] = {
        "codec_digest": codec_digest.value,
        "codec_version": reference.codec_version,
        "media_type": reference.media_type,
        "ref": reference.ref,
        "role": reference.role,
        "schema": reference.schema,
        "sha256": body_digest.value,
        "size_bytes": size,
    }
    _require_issuance(
        reference,
        canonical_bytes=canonical_json_bytes(wire),
        marker=_REFERENCE_MARKER,
        seal=_wire_seal(wire),
        path="portable authority reference",
    )


def code_portable_semantic_package_authority_body_ref(
    authority: CodePortableSemanticPackageAuthority,
) -> CodePortableSemanticPackageAuthorityRef:
    value = _exact(
        authority, CodePortableSemanticPackageAuthority, "portable authority"
    )
    body = value.canonical_bytes()
    digest = ContentDigest.of_bytes(body)
    ref = _CAS_PREFIX + digest.value.removeprefix("sha256:") + ".json"
    return _issue_reference(sha256=digest, ref=ref, size_bytes=len(body))
