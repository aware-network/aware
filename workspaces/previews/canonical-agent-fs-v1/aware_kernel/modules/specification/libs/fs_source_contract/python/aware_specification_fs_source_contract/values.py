"""Dependency-free values for portable Specification filesystem evidence."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import cast

FS_PARSER_PROFILE_CONTRACT = "aware.specification.fs-parser-profile-coordinate.v1"
FS_SOURCE_MEMBER_CONTRACT = "aware.specification.fs-source-member.v1"
FS_SOURCE_MEMBER_SET_CONTRACT = "aware.specification.fs-source-member-set.v1"
FS_SOURCE_CLOSURE_CONTRACT = "aware.specification.fs-source-closure.v1"
PROFILE_REF = "specification_fs_v1"
PROFILE_SCHEMA_REF = "urn:aware:schema:specification:filesystem-manifest:v1"
PROFILE_SCHEMA_DIGEST = (
    "sha256:142acd207dd179cbcd7e397f39802d6b2d919ac70c4354319d9d73e9a6d493d3"
)
MAX_PATH_BYTES = 1024
MAX_MEMBER_BYTES = 2_097_152
MAX_MEMBERS = 4096
MAX_TOTAL_BYTES = 67_108_864

_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SEMANTIC_REF_RE = re.compile(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z")
_FORBIDDEN_PATH_RANGES = ((0x00, 0x1F), (0x7F, 0x9F), (0xD800, 0xDFFF))
_FORBIDDEN_BODY = frozenset({0x00, 0x0B, 0x0C, 0x0D, 0x85, 0x2028, 0x2029})
_TRAILING_WHITESPACE = frozenset(
    {0x09, 0x20, 0xA0, 0x1680, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000}
)


class SpecificationFsContractError(ValueError):
    """Raised when portable filesystem source evidence is malformed."""


class SpecificationFsSourceRole(StrEnum):
    MANIFEST = "manifest"
    SPECIFICATION = "specification"
    INVARIANT_INDEX = "invariant_index"
    INVARIANT = "invariant"
    PHASE_INDEX = "phase_index"
    PHASE = "phase"
    ITERATION = "iteration"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(contract: str, payload: object) -> str:
    body = canonical_json_bytes({"contract": contract, "payload": payload})
    return f"sha256:{sha256(body).hexdigest()}"


def _exact_text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise SpecificationFsContractError(f"{field_name} must be exact text")
    return value


def _sha256_ref(value: object, field_name: str) -> str:
    result = _exact_text(value, field_name)
    if _SHA256_RE.fullmatch(result) is None:
        raise SpecificationFsContractError(f"{field_name} must be lowercase SHA-256")
    return result


def _semantic_ref(value: object, field_name: str) -> str:
    result = _exact_text(value, field_name)
    if (
        not result
        or result.strip() != result
        or not unicodedata.is_normalized("NFC", result)
        or _SEMANTIC_REF_RE.fullmatch(result) is None
    ):
        raise SpecificationFsContractError(f"{field_name} must be a semantic ref")
    return result


def _exact_int(value: object, field_name: str, *, maximum: int | None = None) -> int:
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise SpecificationFsContractError(
            f"{field_name} must be an exact bounded integer"
        )
    return value


def _forbidden_path_codepoint(codepoint: int) -> bool:
    return any(lower <= codepoint <= upper for lower, upper in _FORBIDDEN_PATH_RANGES)


def canonical_relative_path(value: object, field_name: str) -> str:
    result = _exact_text(value, field_name)
    try:
        encoded = result.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise SpecificationFsContractError(
            f"{field_name} must be strict UTF-8"
        ) from error
    parts = result.split("/")
    if (
        not 1 <= len(encoded) <= MAX_PATH_BYTES
        or not unicodedata.is_normalized("NFC", result)
        or result.startswith("/")
        or result.endswith("/")
        or "\\" in result
        or any(part in {"", ".", ".."} for part in parts)
        or any(_forbidden_path_codepoint(ord(character)) for character in result)
    ):
        raise SpecificationFsContractError(
            f"{field_name} must be a canonical relative path"
        )
    return result


def canonical_source_body(value: object) -> tuple[str, bytes]:
    result = _exact_text(value, "canonical_body")
    try:
        encoded = result.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise SpecificationFsContractError(
            "canonical_body must be strict UTF-8"
        ) from error
    if (
        not unicodedata.is_normalized("NFC", result)
        or not result.endswith("\n")
        or result.endswith("\n\n")
        or any(chr(codepoint) in result for codepoint in _FORBIDDEN_BODY)
        or len(encoded) > MAX_MEMBER_BYTES
    ):
        raise SpecificationFsContractError(
            "canonical_body is not canonical source text"
        )
    if any(f"{chr(codepoint)}\n" in result for codepoint in _TRAILING_WHITESPACE):
        raise SpecificationFsContractError("canonical_body has trailing whitespace")
    return result, encoded


def profile_preimage(
    value: SpecificationFsParserProfileCoordinate,
) -> dict[str, object]:
    profile = _validate_profile(value)
    return _profile_preimage_unchecked(profile)


def _profile_preimage_unchecked(
    value: SpecificationFsParserProfileCoordinate,
) -> dict[str, object]:
    return {
        "parser_implementation_digest": value.parser_implementation_digest,
        "parser_implementation_ref": value.parser_implementation_ref,
        "profile_ref": value.profile_ref,
        "profile_schema_digest": value.profile_schema_digest,
        "profile_schema_ref": value.profile_schema_ref,
    }


def profile_to_wire(value: SpecificationFsParserProfileCoordinate) -> dict[str, object]:
    profile = _validate_profile(value)
    result = _profile_preimage_unchecked(profile)
    result["profile_coordinate_digest"] = value.profile_coordinate_digest
    return result


@dataclass(frozen=True, slots=True)
class SpecificationFsParserProfileCoordinate:
    parser_implementation_ref: str
    parser_implementation_digest: str
    profile_ref: str = PROFILE_REF
    profile_schema_ref: str = PROFILE_SCHEMA_REF
    profile_schema_digest: str = PROFILE_SCHEMA_DIGEST
    profile_coordinate_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsParserProfileCoordinate:
            raise SpecificationFsContractError("profile type must be exact")
        _ = _semantic_ref(self.parser_implementation_ref, "parser_implementation_ref")
        _ = _sha256_ref(
            self.parser_implementation_digest, "parser_implementation_digest"
        )
        profile_ref = _exact_text(self.profile_ref, "profile_ref")
        profile_schema_ref = _exact_text(self.profile_schema_ref, "profile_schema_ref")
        profile_schema_digest = _sha256_ref(
            self.profile_schema_digest, "profile_schema_digest"
        )
        if profile_ref != PROFILE_REF or profile_schema_ref != PROFILE_SCHEMA_REF:
            raise SpecificationFsContractError("profile identity must be exact")
        if profile_schema_digest != PROFILE_SCHEMA_DIGEST:
            raise SpecificationFsContractError("profile schema digest must be exact")
        payload = {
            "parser_implementation_digest": self.parser_implementation_digest,
            "parser_implementation_ref": self.parser_implementation_ref,
            "profile_ref": self.profile_ref,
            "profile_schema_digest": self.profile_schema_digest,
            "profile_schema_ref": self.profile_schema_ref,
        }
        object.__setattr__(
            self,
            "profile_coordinate_digest",
            _digest(FS_PARSER_PROFILE_CONTRACT, payload),
        )


def _validate_profile(value: object) -> SpecificationFsParserProfileCoordinate:
    if type(value) is not SpecificationFsParserProfileCoordinate:
        raise SpecificationFsContractError("profile type must be exact")
    profile = cast(SpecificationFsParserProfileCoordinate, value)
    try:
        retained_fields = (
            profile.parser_implementation_ref,
            profile.parser_implementation_digest,
            profile.profile_ref,
            profile.profile_schema_ref,
            profile.profile_schema_digest,
            profile.profile_coordinate_digest,
        )
        if any(type(item) is not str for item in retained_fields):
            raise SpecificationFsContractError("profile fields must be exact text")
        expected = SpecificationFsParserProfileCoordinate(
            parser_implementation_ref=profile.parser_implementation_ref,
            parser_implementation_digest=profile.parser_implementation_digest,
            profile_ref=profile.profile_ref,
            profile_schema_ref=profile.profile_schema_ref,
            profile_schema_digest=profile.profile_schema_digest,
        )
        retained_digest = profile.profile_coordinate_digest
    except AttributeError as error:
        raise SpecificationFsContractError("profile is incomplete") from error
    if retained_digest != expected.profile_coordinate_digest:
        raise SpecificationFsContractError("profile digest is not freshly derived")
    return profile


def member_preimage(value: SpecificationFsSourceMember) -> dict[str, object]:
    member = _validate_member(value)
    return _member_preimage_unchecked(member)


def _member_preimage_unchecked(value: SpecificationFsSourceMember) -> dict[str, object]:
    member = value
    return {
        "body_digest": member.body_digest,
        "canonical_body": member.canonical_body,
        "relative_path": member.relative_path,
        "role": member.role.value,
        "size_bytes": member.size_bytes,
    }


def member_to_wire(value: SpecificationFsSourceMember) -> dict[str, object]:
    member = _validate_member(value)
    result = _member_preimage_unchecked(member)
    result["member_digest"] = value.member_digest
    return result


def _member_wire_unchecked(value: SpecificationFsSourceMember) -> dict[str, object]:
    result = _member_preimage_unchecked(value)
    result["member_digest"] = value.member_digest
    return result


@dataclass(frozen=True, slots=True)
class SpecificationFsSourceMember:
    relative_path: str
    role: SpecificationFsSourceRole
    canonical_body: str
    size_bytes: int = field(init=False)
    body_digest: str = field(init=False)
    member_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsSourceMember:
            raise SpecificationFsContractError("member type must be exact")
        if type(self.role) is not SpecificationFsSourceRole:
            raise SpecificationFsContractError("role type must be exact")
        _ = canonical_relative_path(self.relative_path, "relative_path")
        _, body_bytes = canonical_source_body(self.canonical_body)
        body_digest = f"sha256:{sha256(body_bytes).hexdigest()}"
        object.__setattr__(self, "size_bytes", len(body_bytes))
        object.__setattr__(self, "body_digest", body_digest)
        payload = {
            "body_digest": body_digest,
            "canonical_body": self.canonical_body,
            "relative_path": self.relative_path,
            "role": self.role.value,
            "size_bytes": len(body_bytes),
        }
        object.__setattr__(
            self, "member_digest", _digest(FS_SOURCE_MEMBER_CONTRACT, payload)
        )


def _validate_member(value: object) -> SpecificationFsSourceMember:
    if type(value) is not SpecificationFsSourceMember:
        raise SpecificationFsContractError("member type must be exact")
    member = cast(SpecificationFsSourceMember, value)
    try:
        if (
            type(member.relative_path) is not str
            or type(member.role) is not SpecificationFsSourceRole
            or type(member.canonical_body) is not str
            or type(member.size_bytes) is not int
            or type(member.body_digest) is not str
            or type(member.member_digest) is not str
        ):
            raise SpecificationFsContractError("member fields must have exact types")
        expected = SpecificationFsSourceMember(
            member.relative_path, member.role, member.canonical_body
        )
        retained = (member.size_bytes, member.body_digest, member.member_digest)
    except AttributeError as error:
        raise SpecificationFsContractError("member is incomplete") from error
    if (
        retained[0] != expected.size_bytes
        or retained[1] != expected.body_digest
        or retained[2] != expected.member_digest
    ):
        raise SpecificationFsContractError("member evidence is not freshly derived")
    return member


def member_set_preimage(
    members: tuple[SpecificationFsSourceMember, ...],
) -> dict[str, object]:
    return {
        "members": [
            {
                "member_digest": member.member_digest,
                "relative_path": member.relative_path,
                "role": member.role.value,
            }
            for member in members
        ]
    }


def closure_preimage(value: SpecificationFsSourceClosure) -> dict[str, object]:
    closure = _validate_closure(value)
    return _closure_preimage_unchecked(closure)


def _closure_preimage_unchecked(
    value: SpecificationFsSourceClosure,
) -> dict[str, object]:
    closure = value
    return {
        "contract": closure.contract,
        "manifest_member_digest": closure.manifest_member_digest,
        "member_set_digest": closure.member_set_digest,
        "members": [_member_wire_unchecked(member) for member in closure.members],
        "profile": {
            **_profile_preimage_unchecked(closure.profile),
            "profile_coordinate_digest": closure.profile.profile_coordinate_digest,
        },
        "spec_root": closure.spec_root,
        "total_size_bytes": closure.total_size_bytes,
    }


def closure_to_wire(value: SpecificationFsSourceClosure) -> dict[str, object]:
    result = closure_preimage(value)
    result["closure_digest"] = value.closure_digest
    return result


@dataclass(frozen=True, slots=True)
class SpecificationFsSourceClosure:
    spec_root: str
    profile: SpecificationFsParserProfileCoordinate
    members: tuple[SpecificationFsSourceMember, ...]
    contract: str = FS_SOURCE_CLOSURE_CONTRACT
    manifest_member_digest: str = field(init=False)
    member_set_digest: str = field(init=False)
    total_size_bytes: int = field(init=False)
    closure_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsSourceClosure:
            raise SpecificationFsContractError("closure type must be exact")
        contract = _exact_text(self.contract, "contract")
        if contract != FS_SOURCE_CLOSURE_CONTRACT:
            raise SpecificationFsContractError("closure contract must be exact")
        _ = canonical_relative_path(self.spec_root, "spec_root")
        _ = _validate_profile(self.profile)
        if type(self.members) is not tuple or not 1 <= len(self.members) <= MAX_MEMBERS:
            raise SpecificationFsContractError("members must be a bounded exact tuple")
        members = tuple(_validate_member(member) for member in self.members)
        ordered = tuple(
            sorted(members, key=lambda member: member.relative_path.encode("utf-8"))
        )
        if members != ordered:
            raise SpecificationFsContractError("members must be canonically ordered")
        paths = tuple(member.relative_path for member in members)
        identities = tuple((member.relative_path, member.role) for member in members)
        if len(set(paths)) != len(paths) or len(set(identities)) != len(identities):
            raise SpecificationFsContractError(
                "member paths and identities must be unique"
            )
        manifests = tuple(
            member
            for member in members
            if member.role is SpecificationFsSourceRole.MANIFEST
        )
        if len(manifests) != 1 or manifests[0].relative_path != "aware.spec.toml":
            raise SpecificationFsContractError(
                "closure requires exact aware.spec.toml manifest"
            )
        total = sum(member.size_bytes for member in members)
        if total > MAX_TOTAL_BYTES:
            raise SpecificationFsContractError("closure source bytes exceed limit")
        member_set_digest = _digest(
            FS_SOURCE_MEMBER_SET_CONTRACT, member_set_preimage(members)
        )
        object.__setattr__(self, "manifest_member_digest", manifests[0].member_digest)
        object.__setattr__(self, "member_set_digest", member_set_digest)
        object.__setattr__(self, "total_size_bytes", total)
        payload = {
            "contract": self.contract,
            "manifest_member_digest": manifests[0].member_digest,
            "member_set_digest": member_set_digest,
            "members": [_member_wire_unchecked(member) for member in members],
            "profile": {
                **_profile_preimage_unchecked(self.profile),
                "profile_coordinate_digest": self.profile.profile_coordinate_digest,
            },
            "spec_root": self.spec_root,
            "total_size_bytes": total,
        }
        object.__setattr__(
            self, "closure_digest", _digest(FS_SOURCE_CLOSURE_CONTRACT, payload)
        )


def _validate_closure(value: object) -> SpecificationFsSourceClosure:
    if type(value) is not SpecificationFsSourceClosure:
        raise SpecificationFsContractError("closure type must be exact")
    closure = cast(SpecificationFsSourceClosure, value)
    try:
        if (
            type(closure.spec_root) is not str
            or type(closure.profile) is not SpecificationFsParserProfileCoordinate
            or type(closure.members) is not tuple
            or type(closure.contract) is not str
            or type(closure.manifest_member_digest) is not str
            or type(closure.member_set_digest) is not str
            or type(closure.total_size_bytes) is not int
            or type(closure.closure_digest) is not str
        ):
            raise SpecificationFsContractError("closure fields must have exact types")
        expected = SpecificationFsSourceClosure(
            spec_root=closure.spec_root,
            profile=closure.profile,
            members=closure.members,
            contract=closure.contract,
        )
        retained = (
            closure.manifest_member_digest,
            closure.member_set_digest,
            closure.total_size_bytes,
            closure.closure_digest,
        )
    except AttributeError as error:
        raise SpecificationFsContractError("closure is incomplete") from error
    if (
        retained[0] != expected.manifest_member_digest
        or retained[1] != expected.member_set_digest
        or retained[2] != expected.total_size_bytes
        or retained[3] != expected.closure_digest
    ):
        raise SpecificationFsContractError("closure evidence is not freshly derived")
    return closure
