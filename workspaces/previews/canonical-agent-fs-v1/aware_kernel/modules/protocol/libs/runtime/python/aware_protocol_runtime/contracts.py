"""Representation-neutral Protocol contracts."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Mapping

PROTOCOL_MANIFEST_CONTRACT = "aware.protocol.manifest.v1"
_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class ProtocolContractError(ValueError):
    """Raised when a canonical Protocol value is malformed."""


class ProtocolTargetKind(StrEnum):
    REPOSITORY = "repository"


class ProtocolAuthorityMode(StrEnum):
    FILESYSTEM = "filesystem"
    SERVICE_API = "service_api"


class ProtocolRecordRole(StrEnum):
    AUTHORITY = "authority"
    PROJECTION = "projection"
    BOOTSTRAP = "bootstrap"
    UNAVAILABLE = "unavailable"


class ProtocolAdmissionOutcomeKind(StrEnum):
    CANONICAL_V1 = "canonical_v1"
    LEGACY_SUPPORTED_STRUCTURE = "legacy_supported_structure"
    MALFORMED_V1 = "malformed_v1"
    FOREIGN_PROFILE = "foreign_profile"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"
    SOURCE_UNAVAILABLE = "source_unavailable"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def protocol_digest(contract: str, payload: object) -> str:
    envelope = {"contract": _text(contract, "contract"), "payload": payload}
    return f"sha256:{sha256(canonical_json_bytes(envelope)).hexdigest()}"


def _text(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ProtocolContractError(f"{field_name} must be normalized non-empty text")
    return value


def _key(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if _KEY.fullmatch(result) is None:
        raise ProtocolContractError(f"{field_name} has invalid key syntax")
    return result


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 1:
        raise ProtocolContractError(f"{field_name} must be an integer >= 1")
    return value


@dataclass(frozen=True, slots=True)
class ProtocolIdentity:
    name: str
    profile: str
    semantic_version: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _key(self.name, "protocol.name"))
        object.__setattr__(self, "profile", _key(self.profile, "protocol.profile"))
        object.__setattr__(
            self,
            "semantic_version",
            _positive_int(self.semantic_version, "protocol.semantic_version"),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "name": self.name,
            "profile": self.profile,
            "semantic_version": self.semantic_version,
        }


@dataclass(frozen=True, slots=True)
class ProtocolTarget:
    kind: ProtocolTargetKind
    authority_mode: ProtocolAuthorityMode
    authority_ref: str | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not ProtocolTargetKind:
            raise ProtocolContractError("target.kind must be ProtocolTargetKind")
        if type(self.authority_mode) is not ProtocolAuthorityMode:
            raise ProtocolContractError(
                "target.authority_mode must be ProtocolAuthorityMode"
            )
        authority_ref = self.authority_ref
        if authority_ref is not None:
            authority_ref = _text(authority_ref, "target.authority_ref")
            object.__setattr__(self, "authority_ref", authority_ref)
        if self.authority_mode is ProtocolAuthorityMode.FILESYSTEM and authority_ref:
            raise ProtocolContractError(
                "filesystem target must not declare service authority_ref"
            )
        if self.authority_mode is ProtocolAuthorityMode.SERVICE_API and not authority_ref:
            raise ProtocolContractError(
                "service_api target requires authority_ref"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "authority_mode": self.authority_mode.value,
            "authority_ref": self.authority_ref,
        }


@dataclass(frozen=True, slots=True)
class ProtocolBootstrap:
    agent_contract_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "agent_contract_ref",
            _text(self.agent_contract_ref, "bootstrap.agent_contract_ref"),
        )

    def to_wire(self) -> dict[str, object]:
        return {"agent_contract_ref": self.agent_contract_ref}


@dataclass(frozen=True, slots=True)
class ProtocolRecordBinding:
    record_key: str
    profile: str
    role: ProtocolRecordRole

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_key", _key(self.record_key, "record_key"))
        object.__setattr__(self, "profile", _key(self.profile, "record.profile"))
        if type(self.role) is not ProtocolRecordRole:
            raise ProtocolContractError("record.role must be ProtocolRecordRole")

    def to_wire(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "role": self.role.value,
        }


@dataclass(frozen=True, slots=True)
class ProtocolManifest:
    protocol: ProtocolIdentity
    target: ProtocolTarget
    bootstrap: ProtocolBootstrap
    records: tuple[ProtocolRecordBinding, ...]

    def __post_init__(self) -> None:
        if type(self.protocol) is not ProtocolIdentity:
            raise ProtocolContractError("protocol must be ProtocolIdentity")
        if type(self.target) is not ProtocolTarget:
            raise ProtocolContractError("target must be ProtocolTarget")
        if type(self.bootstrap) is not ProtocolBootstrap:
            raise ProtocolContractError("bootstrap must be ProtocolBootstrap")
        try:
            records = tuple(self.records)
        except TypeError as error:
            raise ProtocolContractError("records must be iterable") from error
        object.__setattr__(self, "records", records)
        if not records:
            raise ProtocolContractError("records must not be empty")
        if any(type(item) is not ProtocolRecordBinding for item in records):
            raise ProtocolContractError("records must contain ProtocolRecordBinding")
        keys = tuple(item.record_key for item in records)
        if len(keys) != len(set(keys)):
            raise ProtocolContractError("record bindings must have unique record_key")

    @classmethod
    def from_mapping(
        cls,
        *,
        protocol: ProtocolIdentity,
        target: ProtocolTarget,
        bootstrap: ProtocolBootstrap,
        records: Mapping[str, ProtocolRecordBinding],
    ) -> ProtocolManifest:
        for key, binding in records.items():
            if key != binding.record_key:
                raise ProtocolContractError(
                    "record mapping key must match binding.record_key"
                )
        return cls(
            protocol=protocol,
            target=target,
            bootstrap=bootstrap,
            records=tuple(records[key] for key in sorted(records)),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": PROTOCOL_MANIFEST_CONTRACT,
            "protocol": self.protocol.to_wire(),
            "target": self.target.to_wire(),
            "bootstrap": self.bootstrap.to_wire(),
            "records": {
                item.record_key: item.to_wire()
                for item in sorted(self.records, key=lambda value: value.record_key)
            },
        }

    @property
    def digest(self) -> str:
        return protocol_digest(PROTOCOL_MANIFEST_CONTRACT, self.to_wire())


@dataclass(frozen=True, slots=True)
class ProtocolAdmissionResult:
    outcome: ProtocolAdmissionOutcomeKind
    source_sha256: str | None
    manifest: ProtocolManifest | None = None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.outcome) is not ProtocolAdmissionOutcomeKind:
            raise ProtocolContractError(
                "outcome must be ProtocolAdmissionOutcomeKind"
            )
        source_sha256 = self.source_sha256
        if source_sha256 is not None:
            if type(source_sha256) is not str:
                raise ProtocolContractError(
                    "source_sha256 must be a lowercase SHA-256 ref or null"
                )
            digest_body = source_sha256.removeprefix("sha256:")
            if (
                not source_sha256.startswith("sha256:")
                or len(digest_body) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in digest_body
                )
            ):
                raise ProtocolContractError(
                    "source_sha256 must be a lowercase SHA-256 ref or null"
                )
        if self.manifest is not None and type(self.manifest) is not ProtocolManifest:
            raise ProtocolContractError("manifest must be ProtocolManifest or null")
        if isinstance(self.diagnostics, (str, bytes)):
            raise ProtocolContractError("diagnostics must be an iterable of strings")
        try:
            diagnostics = tuple(self.diagnostics)
        except TypeError as error:
            raise ProtocolContractError("diagnostics must be iterable") from error
        if any(type(item) is not str or not item for item in diagnostics):
            raise ProtocolContractError(
                "diagnostics must contain non-empty strings"
            )
        object.__setattr__(self, "diagnostics", diagnostics)
        if self.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            if source_sha256 is None or self.manifest is None or diagnostics:
                raise ProtocolContractError(
                    "canonical_v1 requires source digest, manifest, and no diagnostics"
                )
        elif self.manifest is not None:
            raise ProtocolContractError(
                "non-canonical admission outcome must not expose manifest"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "outcome": self.outcome.value,
            "source_sha256": self.source_sha256,
            "manifest": None if self.manifest is None else self.manifest.to_wire(),
            "diagnostics": list(self.diagnostics),
        }
