"""Dependency-free, fail-closed portable ``CodePackageDelta`` values."""

from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Self, cast
from uuid import UUID

CODE_PACKAGE_DELTA_CONTRACT = "aware.code.package-delta.v1"
CODE_PACKAGE_DELTA_OUTPUT_ROOT_CONTRACT = "aware.code.package-delta-output-root.v1"
CODE_PACKAGE_OUTPUT_STATE_CONTRACT = "aware.code.package-output-state.v1"
CODE_PACKAGE_OUTPUT_STATE_ROOT_CONTRACT = "aware.code.package-output-state-root.v1"


class CodePackageDeltaContractError(ValueError):
    """Raised when a portable Code delta is malformed or noncanonical."""


class CodePackageDeltaKind(StrEnum):
    create = "create"
    update = "update"
    delete = "delete"


class CodePackageDeltaAuthorityKind(StrEnum):
    code_package_delta = "code_package_delta"


class CodePackagePathRole(StrEnum):
    authored_source = "authored_source"
    generated_code = "generated_code"
    generated_manifest = "generated_manifest"
    generated_metadata = "generated_metadata"


class CodeLanguage(StrEnum):
    aware = "aware"
    dart = "dart"
    python = "python"
    sql = "sql"


type JsonValue = (
    str | int | float | bool | None | tuple[JsonValue, ...] | FrozenJsonObject
)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def _digest(contract: str, payload: object) -> str:
    envelope = {"contract": contract, "payload": payload}
    return "sha256:" + sha256(_canonical_json_bytes(envelope)).hexdigest()


def _token(value: object, field: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise CodePackageDeltaContractError(f"{field} must be normalized text")
    return value


def _sha256(value: object, field: str) -> str:
    if type(value) is not str or not value.startswith("sha256:"):
        raise CodePackageDeltaContractError(f"{field} must be SHA-256")
    raw = value.removeprefix("sha256:")
    if len(raw) != 64 or any(item not in "0123456789abcdef" for item in raw):
        raise CodePackageDeltaContractError(f"{field} must be SHA-256")
    return value


def _optional_sha256(value: object, field: str) -> str | None:
    return None if value is None else _sha256(value, field)


def _relative_path(value: object) -> str:
    path_text = _token(value, "relative_path")
    path = PurePosixPath(path_text)
    if (
        "\\" in path_text
        or path.is_absolute()
        or path.as_posix() != path_text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CodePackageDeltaContractError(
            "relative_path must be a normalized package-relative POSIX path"
        )
    return path_text


def _freeze(value: object) -> JsonValue:
    if value is None or type(value) in (str, bool, int):
        return cast(JsonValue, value)
    if type(value) is float:
        if not math.isfinite(value):
            raise CodePackageDeltaContractError("JSON numbers must be finite")
        return value
    if isinstance(value, Mapping):
        raw = cast(Mapping[object, object], value)
        if any(type(key) is not str for key in raw):
            raise CodePackageDeltaContractError("JSON object keys must be strings")
        return FrozenJsonObject.from_mapping(
            {cast(str, key): item for key, item in raw.items()}
        )
    if type(value) in (list, tuple):
        return tuple(
            _freeze(item) for item in cast(list[object] | tuple[object, ...], value)
        )
    raise CodePackageDeltaContractError("portable Code delta contains non-JSON value")


def _thaw(value: JsonValue) -> object:
    if type(value) is FrozenJsonObject:
        return _encode_frozen_json(value)
    if type(value) is tuple:
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class FrozenJsonObject(Mapping[str, JsonValue]):
    entries: tuple[tuple[str, JsonValue], ...]

    def __post_init__(self) -> None:
        if type(self) is not FrozenJsonObject:
            raise CodePackageDeltaContractError(
                "JSON object must use the exact contract type"
            )
        if type(self.entries) is not tuple or any(
            type(item) is not tuple or len(item) != 2 for item in self.entries
        ):
            raise CodePackageDeltaContractError("JSON object must be immutable")
        for key, value in self.entries:
            _token(key, "JSON object key")
            if (
                isinstance(value, FrozenJsonObject)
                and type(value) is not FrozenJsonObject
            ):
                raise CodePackageDeltaContractError(
                    "JSON object contains a subclassed authority value"
                )
            if type(value) is FrozenJsonObject:
                value.__post_init__()
            if _freeze(_thaw(value)) != value:
                raise CodePackageDeltaContractError("JSON value is not canonical")
        if tuple(sorted(self.entries, key=lambda item: item[0])) != self.entries:
            raise CodePackageDeltaContractError("JSON object keys must be canonical")
        if len({key for key, _ in self.entries}) != len(self.entries):
            raise CodePackageDeltaContractError("JSON object keys must be unique")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        return cls(
            tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
        )

    def __getitem__(self, key: str) -> JsonValue:
        for candidate, value in self.entries:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_frozen_json(self)


def _encode_frozen_json(value: FrozenJsonObject) -> dict[str, object]:
    return {key: _thaw(item) for key, item in value.entries}


@dataclass(frozen=True, slots=True)
class CodePackageDeltaProducerRef:
    provider_key: str
    producer_key: str
    producer_kind: str | None = None
    provider_payload: FrozenJsonObject | None = None

    def __post_init__(self) -> None:
        if type(self) is not CodePackageDeltaProducerRef:
            raise CodePackageDeltaContractError(
                "producer must use the exact contract type"
            )
        _token(self.provider_key, "provider_key")
        _token(self.producer_key, "producer_key")
        if self.producer_kind is not None:
            _token(self.producer_kind, "producer_kind")
        if self.provider_payload is not None:
            if type(self.provider_payload) is not FrozenJsonObject:
                raise CodePackageDeltaContractError(
                    "provider_payload must be exact immutable JSON"
                )
            self.provider_payload.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_producer(self)


def _encode_producer(value: CodePackageDeltaProducerRef) -> dict[str, object]:
    return {
        "provider_key": value.provider_key,
        "producer_key": value.producer_key,
        "producer_kind": value.producer_kind,
        "provider_payload": None
        if value.provider_payload is None
        else _encode_frozen_json(value.provider_payload),
    }


@dataclass(frozen=True, slots=True)
class CodePackageDeltaProduction:
    producer: CodePackageDeltaProducerRef
    input_code_package_id: UUID | None = None
    input_digest: str | None = None
    output_digest: str | None = None
    emission_payload: FrozenJsonObject | None = None

    def __post_init__(self) -> None:
        if type(self) is not CodePackageDeltaProduction:
            raise CodePackageDeltaContractError(
                "production must use the exact contract type"
            )
        if type(self.producer) is not CodePackageDeltaProducerRef:
            raise CodePackageDeltaContractError("production producer is invalid")
        self.producer.__post_init__()
        if (
            self.input_code_package_id is not None
            and type(self.input_code_package_id) is not UUID
        ):
            raise CodePackageDeltaContractError("input_code_package_id is invalid")
        _optional_sha256(self.input_digest, "input_digest")
        _optional_sha256(self.output_digest, "output_digest")
        if self.emission_payload is not None:
            if type(self.emission_payload) is not FrozenJsonObject:
                raise CodePackageDeltaContractError(
                    "emission_payload must be exact immutable JSON"
                )
            self.emission_payload.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_production(self)


def _encode_production(value: CodePackageDeltaProduction) -> dict[str, object]:
    return {
        "producer": _encode_producer(value.producer),
        "input_code_package_id": None
        if value.input_code_package_id is None
        else str(value.input_code_package_id),
        "input_digest": value.input_digest,
        "output_digest": value.output_digest,
        "emission_payload": None
        if value.emission_payload is None
        else _encode_frozen_json(value.emission_payload),
    }


@dataclass(frozen=True, slots=True)
class CodePackageDeltaPath:
    relative_path: str
    kind: CodePackageDeltaKind
    content_text: str | None
    before_hash: str | None
    after_hash: str | None
    size_bytes: int | None
    language: CodeLanguage | None
    is_structural: bool
    path_role: CodePackagePathRole
    production: CodePackageDeltaProduction
    metadata: FrozenJsonObject

    def __post_init__(self) -> None:
        if type(self) is not CodePackageDeltaPath:
            raise CodePackageDeltaContractError("path must use the exact contract type")
        object.__setattr__(self, "relative_path", _relative_path(self.relative_path))
        if type(self.kind) is not CodePackageDeltaKind or (
            self.language is not None and type(self.language) is not CodeLanguage
        ):
            raise CodePackageDeltaContractError("path enum value is invalid")
        if (
            type(self.is_structural) is not bool
            or type(self.path_role) is not CodePackagePathRole
        ):
            raise CodePackageDeltaContractError("path role/structural value is invalid")
        if (
            type(self.production) is not CodePackageDeltaProduction
            or type(self.metadata) is not FrozenJsonObject
        ):
            raise CodePackageDeltaContractError("path production/metadata is invalid")
        self.production.__post_init__()
        self.metadata.__post_init__()
        before = _optional_sha256(self.before_hash, "before_hash")
        after = _optional_sha256(self.after_hash, "after_hash")
        if self.content_text is not None and type(self.content_text) is not str:
            raise CodePackageDeltaContractError("content_text must be text or null")
        content_size = (
            None if self.content_text is None else len(self.content_text.encode())
        )
        content_hash = (
            None
            if self.content_text is None
            else "sha256:" + sha256(self.content_text.encode()).hexdigest()
        )
        expected = {
            CodePackageDeltaKind.create: (False, True),
            CodePackageDeltaKind.update: (True, True),
            CodePackageDeltaKind.delete: (True, False),
        }[self.kind]
        if (before is not None, self.content_text is not None, after is not None) != (
            expected[0],
            expected[1],
            expected[1],
        ):
            raise CodePackageDeltaContractError(
                f"{self.kind.value} lifecycle is invalid"
            )
        if after != content_hash:
            raise CodePackageDeltaContractError("after_hash differs from content")
        if self.size_bytes != content_size:
            raise CodePackageDeltaContractError("size differs from content")
        if self.kind is CodePackageDeltaKind.update and before == after:
            raise CodePackageDeltaContractError("update cannot be a no-op")

    def output_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_path_output(self)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_path(self)


def _encode_path_output(value: CodePackageDeltaPath) -> dict[str, object]:
    return {
        "relative_path": value.relative_path,
        "kind": value.kind.value,
        "before_hash": value.before_hash,
        "after_hash": value.after_hash,
        "size_bytes": value.size_bytes,
        "language": None if value.language is None else value.language.value,
        "is_structural": value.is_structural,
        "path_role": value.path_role.value,
    }


def _encode_path(value: CodePackageDeltaPath) -> dict[str, object]:
    return {
        "relative_path": value.relative_path,
        "kind": value.kind.value,
        "content_text": value.content_text,
        "before_hash": value.before_hash,
        "after_hash": value.after_hash,
        "size_bytes": value.size_bytes,
        "language": None if value.language is None else value.language.value,
        "is_structural": value.is_structural,
        "path_role": value.path_role.value,
        "production": _encode_production(value.production),
        "metadata": _encode_frozen_json(value.metadata),
    }


def code_package_delta_output_digest(
    *,
    package_name: str,
    authority: CodePackageDeltaAuthorityKind,
    authority_kind: str,
    source_revision_id: str,
    production: CodePackageDeltaProduction,
    paths: tuple[CodePackageDeltaPath, ...],
) -> str:
    _token(package_name, "package_name")
    if type(authority) is not CodePackageDeltaAuthorityKind:
        raise CodePackageDeltaContractError("delta authority is invalid")
    _token(authority_kind, "authority_kind")
    _sha256(source_revision_id, "source_revision_id")
    if (
        type(production) is not CodePackageDeltaProduction
        or type(paths) is not tuple
        or not paths
        or any(type(item) is not CodePackageDeltaPath for item in paths)
    ):
        raise CodePackageDeltaContractError("delta production/paths are invalid")
    production.__post_init__()
    for item in paths:
        item.__post_init__()
        if item.production != production:
            raise CodePackageDeltaContractError("path production differs from delta")
    return _digest(
        CODE_PACKAGE_DELTA_OUTPUT_ROOT_CONTRACT,
        {
            "package_name": package_name,
            "authority": authority.value,
            "authority_kind": authority_kind,
            "source_revision_id": source_revision_id,
            "producer": _encode_producer(production.producer),
            "input_code_package_id": None
            if production.input_code_package_id is None
            else str(production.input_code_package_id),
            "input_digest": production.input_digest,
            "paths": [_encode_path_output(item) for item in paths],
        },
    )


@dataclass(frozen=True, slots=True)
class CodePackageDelta:
    package_name: str
    authority: CodePackageDeltaAuthorityKind
    authority_kind: str
    source_revision_id: str
    production: CodePackageDeltaProduction
    paths: tuple[CodePackageDeltaPath, ...]
    contract: str = CODE_PACKAGE_DELTA_CONTRACT

    def __post_init__(self) -> None:
        if type(self) is not CodePackageDelta:
            raise CodePackageDeltaContractError(
                "delta must use the exact contract type"
            )
        if self.contract != CODE_PACKAGE_DELTA_CONTRACT:
            raise CodePackageDeltaContractError("delta contract is unsupported")
        _token(self.package_name, "package_name")
        if (
            type(self.authority) is not CodePackageDeltaAuthorityKind
            or self.authority.value != self.authority_kind
        ):
            raise CodePackageDeltaContractError("delta authority identity is invalid")
        _sha256(self.source_revision_id, "source_revision_id")
        if (
            type(self.production) is not CodePackageDeltaProduction
            or type(self.paths) is not tuple
            or not self.paths
        ):
            raise CodePackageDeltaContractError("delta production/paths are invalid")
        self.production.__post_init__()
        if any(type(item) is not CodePackageDeltaPath for item in self.paths):
            raise CodePackageDeltaContractError("delta contains invalid path")
        for item in self.paths:
            item.__post_init__()
        if tuple(sorted(self.paths, key=lambda item: item.relative_path)) != self.paths:
            raise CodePackageDeltaContractError("delta paths are not canonical")
        if len({item.relative_path for item in self.paths}) != len(self.paths):
            raise CodePackageDeltaContractError("delta paths are not unique")
        if any(item.production != self.production for item in self.paths):
            raise CodePackageDeltaContractError("path production differs from delta")
        expected = code_package_delta_output_digest(
            package_name=self.package_name,
            authority=self.authority,
            authority_kind=self.authority_kind,
            source_revision_id=self.source_revision_id,
            production=self.production,
            paths=self.paths,
        )
        if self.production.output_digest != expected:
            raise CodePackageDeltaContractError("production output root mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_delta(self)

    def to_json_bytes(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes(_encode_delta(self))

    @classmethod
    def from_json_bytes(cls, body: bytes) -> Self:
        if type(body) is not bytes or not body:
            raise CodePackageDeltaContractError("delta body must be nonempty bytes")
        try:
            value = json.loads(body)
            item = _object(value, "delta")
            _exact(
                item,
                {
                    "contract",
                    "package_name",
                    "authority",
                    "authority_kind",
                    "source_revision_id",
                    "production",
                    "paths",
                },
                "delta",
            )
            raw_paths = item["paths"]
            if type(raw_paths) is not list:
                raise CodePackageDeltaContractError("delta.paths must be an array")
            production = _decode_production(item["production"], "delta.production")
            result = cls(
                _text(item, "package_name", "delta"),
                CodePackageDeltaAuthorityKind(_text(item, "authority", "delta")),
                _text(item, "authority_kind", "delta"),
                _text(item, "source_revision_id", "delta"),
                production,
                tuple(
                    _decode_path(path, f"delta.paths[{index}]", production)
                    for index, path in enumerate(raw_paths)
                ),
                _text(item, "contract", "delta"),
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            if isinstance(error, CodePackageDeltaContractError):
                raise
            raise CodePackageDeltaContractError("delta body is invalid") from error
        if result.to_json_bytes() != body:
            raise CodePackageDeltaContractError("delta body is noncanonical")
        return result


def _encode_delta(value: CodePackageDelta) -> dict[str, object]:
    return {
        "contract": value.contract,
        "package_name": value.package_name,
        "authority": value.authority.value,
        "authority_kind": value.authority_kind,
        "source_revision_id": value.source_revision_id,
        "production": _encode_production(value.production),
        "paths": [_encode_path(item) for item in value.paths],
    }


@dataclass(frozen=True, slots=True, order=True)
class CodePackageOutputPathState:
    relative_path: str
    content_hash: str
    size_bytes: int
    language: CodeLanguage | None
    is_structural: bool
    path_role: CodePackagePathRole
    metadata: FrozenJsonObject

    def __post_init__(self) -> None:
        if type(self) is not CodePackageOutputPathState:
            raise CodePackageDeltaContractError(
                "output path state must use the exact contract type"
            )
        object.__setattr__(self, "relative_path", _relative_path(self.relative_path))
        _sha256(self.content_hash, "content_hash")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise CodePackageDeltaContractError("size_bytes must be a nonnegative int")
        if self.language is not None and type(self.language) is not CodeLanguage:
            raise CodePackageDeltaContractError("output path language is invalid")
        if (
            type(self.is_structural) is not bool
            or type(self.path_role) is not CodePackagePathRole
            or type(self.metadata) is not FrozenJsonObject
        ):
            raise CodePackageDeltaContractError("output path metadata is invalid")
        self.metadata.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _encode_output_path_state(self)


def _encode_output_path_state(value: CodePackageOutputPathState) -> dict[str, object]:
    return {
        "relative_path": value.relative_path,
        "content_hash": value.content_hash,
        "size_bytes": value.size_bytes,
        "language": None if value.language is None else value.language.value,
        "is_structural": value.is_structural,
        "path_role": value.path_role.value,
        "metadata": _encode_frozen_json(value.metadata),
    }


@dataclass(frozen=True, slots=True)
class CodePackageOutputState:
    package_name: str
    source_revision_id: str | None
    producer: CodePackageDeltaProducerRef | None
    paths: tuple[CodePackageOutputPathState, ...]
    state_digest: str
    contract: str = CODE_PACKAGE_OUTPUT_STATE_CONTRACT

    def __post_init__(self) -> None:
        if type(self) is not CodePackageOutputState:
            raise CodePackageDeltaContractError(
                "output state must use the exact contract type"
            )
        if self.contract != CODE_PACKAGE_OUTPUT_STATE_CONTRACT:
            raise CodePackageDeltaContractError("output state contract is unsupported")
        _token(self.package_name, "package_name")
        if self.source_revision_id is not None:
            _sha256(self.source_revision_id, "source_revision_id")
        if self.producer is not None:
            if type(self.producer) is not CodePackageDeltaProducerRef:
                raise CodePackageDeltaContractError("output state producer is invalid")
            self.producer.__post_init__()
        if type(self.paths) is not tuple or any(
            type(item) is not CodePackageOutputPathState for item in self.paths
        ):
            raise CodePackageDeltaContractError("output state paths are invalid")
        for item in self.paths:
            item.__post_init__()
        if tuple(sorted(self.paths, key=lambda item: item.relative_path)) != self.paths:
            raise CodePackageDeltaContractError("output state paths are not canonical")
        if len({item.relative_path for item in self.paths}) != len(self.paths):
            raise CodePackageDeltaContractError("output state paths are not unique")
        if (self.source_revision_id is None) != (self.producer is None) or (
            self.paths and self.source_revision_id is None
        ):
            raise CodePackageDeltaContractError(
                "empty and populated output state fields are inconsistent"
            )
        expected = _digest(
            CODE_PACKAGE_OUTPUT_STATE_ROOT_CONTRACT, self._wire_without_digest()
        )
        if self.state_digest != expected:
            raise CodePackageDeltaContractError("output state digest mismatched")

    @classmethod
    def empty(cls, package_name: str) -> Self:
        return cls.create(
            package_name=package_name,
            source_revision_id=None,
            producer=None,
            paths=(),
        )

    @classmethod
    def create(
        cls,
        *,
        package_name: str,
        source_revision_id: str | None,
        producer: CodePackageDeltaProducerRef | None,
        paths: tuple[CodePackageOutputPathState, ...],
    ) -> Self:
        if type(paths) is not tuple or any(
            type(item) is not CodePackageOutputPathState for item in paths
        ):
            raise TypeError("paths must be an exact output-state tuple")
        ordered = tuple(sorted(paths, key=lambda item: item.relative_path))
        provisional = object.__new__(cls)
        object.__setattr__(provisional, "package_name", package_name)
        object.__setattr__(provisional, "source_revision_id", source_revision_id)
        object.__setattr__(provisional, "producer", producer)
        object.__setattr__(provisional, "paths", ordered)
        object.__setattr__(provisional, "state_digest", "sha256:" + "0" * 64)
        object.__setattr__(provisional, "contract", CODE_PACKAGE_OUTPUT_STATE_CONTRACT)
        digest = _digest(
            CODE_PACKAGE_OUTPUT_STATE_ROOT_CONTRACT,
            provisional._wire_without_digest(),
        )
        return cls(package_name, source_revision_id, producer, ordered, digest)

    def _wire_without_digest(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "package_name": self.package_name,
            "source_revision_id": self.source_revision_id,
            "producer": None
            if self.producer is None
            else _encode_producer(self.producer),
            "paths": [_encode_output_path_state(item) for item in self.paths],
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {**self._wire_without_digest(), "state_digest": self.state_digest}

    def to_json_bytes(self) -> bytes:
        return _canonical_json_bytes(self.to_wire())

    @classmethod
    def from_json_bytes(cls, body: bytes) -> Self:
        if type(body) is not bytes or not body:
            raise CodePackageDeltaContractError(
                "output state body must be nonempty bytes"
            )
        try:
            root = _object(json.loads(body), "output_state")
            _exact(
                root,
                {
                    "contract",
                    "package_name",
                    "source_revision_id",
                    "producer",
                    "paths",
                    "state_digest",
                },
                "output_state",
            )
            raw_paths = root["paths"]
            if type(raw_paths) is not list:
                raise CodePackageDeltaContractError(
                    "output_state.paths must be an array"
                )
            raw_producer = root["producer"]
            result = cls(
                _text(root, "package_name", "output_state"),
                _optional_text(root, "source_revision_id", "output_state"),
                None
                if raw_producer is None
                else _decode_producer(raw_producer, "output_state.producer"),
                tuple(
                    _decode_output_path_state(value, f"output_state.paths[{index}]")
                    for index, value in enumerate(raw_paths)
                ),
                _text(root, "state_digest", "output_state"),
                _text(root, "contract", "output_state"),
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            if isinstance(error, CodePackageDeltaContractError):
                raise
            raise CodePackageDeltaContractError(
                "output state body is invalid"
            ) from error
        if result.to_json_bytes() != body:
            raise CodePackageDeltaContractError("output state body is noncanonical")
        return result


def derive_code_package_output_state(
    prior_state: CodePackageOutputState, delta: CodePackageDelta
) -> CodePackageOutputState:
    if type(prior_state) is not CodePackageOutputState:
        raise TypeError("prior_state must be exact CodePackageOutputState")
    if type(delta) is not CodePackageDelta:
        raise TypeError("delta must be exact CodePackageDelta")
    prior_state.__post_init__()
    delta.__post_init__()
    if prior_state.package_name != delta.package_name:
        raise CodePackageDeltaContractError("delta package differs from prior state")
    paths = {item.relative_path: item for item in prior_state.paths}
    for movement in delta.paths:
        prior = paths.get(movement.relative_path)
        if movement.kind is CodePackageDeltaKind.create:
            if prior is not None:
                raise CodePackageDeltaContractError("create path already exists")
        else:
            if prior is None:
                raise CodePackageDeltaContractError("update/delete path is absent")
            if prior.content_hash != movement.before_hash:
                raise CodePackageDeltaContractError("movement before_hash is stale")
        if movement.kind is CodePackageDeltaKind.delete:
            del paths[movement.relative_path]
            continue
        if movement.after_hash is None or movement.size_bytes is None:
            raise CodePackageDeltaContractError("retained movement has no output state")
        paths[movement.relative_path] = CodePackageOutputPathState(
            movement.relative_path,
            movement.after_hash,
            movement.size_bytes,
            movement.language,
            movement.is_structural,
            movement.path_role,
            movement.metadata,
        )
    return CodePackageOutputState.create(
        package_name=delta.package_name,
        source_revision_id=delta.source_revision_id,
        producer=delta.production.producer,
        paths=tuple(paths.values()),
    )


def _object(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise CodePackageDeltaContractError(f"{path} must be an object")
    return cast(dict[str, object], value)


def _exact(value: dict[str, object], fields: set[str], path: str) -> None:
    if set(value) != fields:
        raise CodePackageDeltaContractError(f"{path} fields are invalid")


def _text(value: dict[str, object], key: str, path: str) -> str:
    item = value[key]
    if type(item) is not str:
        raise CodePackageDeltaContractError(f"{path}.{key} must be text")
    return item


def _optional_text(value: dict[str, object], key: str, path: str) -> str | None:
    item = value[key]
    if item is not None and type(item) is not str:
        raise CodePackageDeltaContractError(f"{path}.{key} must be text or null")
    return cast(str | None, item)


def _optional_json(
    value: dict[str, object], key: str, path: str
) -> FrozenJsonObject | None:
    item = value[key]
    return None if item is None else FrozenJsonObject.from_mapping(_object(item, path))


def _decode_producer(value: object, path: str) -> CodePackageDeltaProducerRef:
    item = _object(value, path)
    _exact(
        item,
        {"provider_key", "producer_key", "producer_kind", "provider_payload"},
        path,
    )
    return CodePackageDeltaProducerRef(
        _text(item, "provider_key", path),
        _text(item, "producer_key", path),
        _optional_text(item, "producer_kind", path),
        _optional_json(item, "provider_payload", f"{path}.provider_payload"),
    )


def _decode_production(value: object, path: str) -> CodePackageDeltaProduction:
    item = _object(value, path)
    _exact(
        item,
        {
            "producer",
            "input_code_package_id",
            "input_digest",
            "output_digest",
            "emission_payload",
        },
        path,
    )
    raw_id = item["input_code_package_id"]
    if raw_id is not None and type(raw_id) is not str:
        raise CodePackageDeltaContractError(f"{path}.input_code_package_id is invalid")
    return CodePackageDeltaProduction(
        _decode_producer(item["producer"], f"{path}.producer"),
        None if raw_id is None else UUID(raw_id),
        _optional_text(item, "input_digest", path),
        _optional_text(item, "output_digest", path),
        _optional_json(item, "emission_payload", f"{path}.emission_payload"),
    )


def _decode_path(
    value: object, path: str, production: CodePackageDeltaProduction
) -> CodePackageDeltaPath:
    item = _object(value, path)
    _exact(
        item,
        {
            "relative_path",
            "kind",
            "content_text",
            "before_hash",
            "after_hash",
            "size_bytes",
            "language",
            "is_structural",
            "path_role",
            "production",
            "metadata",
        },
        path,
    )
    size = item["size_bytes"]
    structural = item["is_structural"]
    if size is not None and type(size) is not int:
        raise CodePackageDeltaContractError(f"{path}.size_bytes is invalid")
    if type(structural) is not bool:
        raise CodePackageDeltaContractError(f"{path}.is_structural is invalid")
    if _decode_production(item["production"], f"{path}.production") != production:
        raise CodePackageDeltaContractError(f"{path}.production differs from delta")
    return CodePackageDeltaPath(
        _text(item, "relative_path", path),
        CodePackageDeltaKind(_text(item, "kind", path)),
        _optional_text(item, "content_text", path),
        _optional_text(item, "before_hash", path),
        _optional_text(item, "after_hash", path),
        cast(int | None, size),
        (
            None
            if (language := _optional_text(item, "language", path)) is None
            else CodeLanguage(language)
        ),
        cast(bool, structural),
        CodePackagePathRole(_text(item, "path_role", path)),
        production,
        FrozenJsonObject.from_mapping(_object(item["metadata"], f"{path}.metadata")),
    )


def _decode_output_path_state(value: object, path: str) -> CodePackageOutputPathState:
    item = _object(value, path)
    _exact(
        item,
        {
            "relative_path",
            "content_hash",
            "size_bytes",
            "language",
            "is_structural",
            "path_role",
            "metadata",
        },
        path,
    )
    size = item["size_bytes"]
    structural = item["is_structural"]
    if type(size) is not int or size < 0:
        raise CodePackageDeltaContractError(f"{path}.size_bytes is invalid")
    if type(structural) is not bool:
        raise CodePackageDeltaContractError(f"{path}.is_structural is invalid")
    language = _optional_text(item, "language", path)
    return CodePackageOutputPathState(
        _text(item, "relative_path", path),
        _text(item, "content_hash", path),
        size,
        None if language is None else CodeLanguage(language),
        structural,
        CodePackagePathRole(_text(item, "path_role", path)),
        FrozenJsonObject.from_mapping(_object(item["metadata"], f"{path}.metadata")),
    )


__all__ = [
    "CODE_PACKAGE_DELTA_CONTRACT",
    "CODE_PACKAGE_DELTA_OUTPUT_ROOT_CONTRACT",
    "CODE_PACKAGE_OUTPUT_STATE_CONTRACT",
    "CODE_PACKAGE_OUTPUT_STATE_ROOT_CONTRACT",
    "CodeLanguage",
    "CodePackageDelta",
    "CodePackageDeltaAuthorityKind",
    "CodePackageDeltaContractError",
    "CodePackageDeltaKind",
    "CodePackageDeltaPath",
    "CodePackageDeltaProducerRef",
    "CodePackageDeltaProduction",
    "CodePackageOutputPathState",
    "CodePackageOutputState",
    "CodePackagePathRole",
    "FrozenJsonObject",
    "code_package_delta_output_digest",
    "derive_code_package_output_state",
]
