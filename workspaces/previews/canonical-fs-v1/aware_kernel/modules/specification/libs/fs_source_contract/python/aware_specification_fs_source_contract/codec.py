"""Strict canonical codec for Specification filesystem source evidence."""

from __future__ import annotations

import json
from typing import cast

from .values import (
    FS_SOURCE_CLOSURE_CONTRACT,
    SpecificationFsContractError,
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
    SpecificationFsSourceMember,
    SpecificationFsSourceRole,
    canonical_json_bytes,
    closure_to_wire,
)

MAX_ENCODED_CLOSURE_BYTES = 536_870_912

type JsonObject = dict[str, object]


def _validate_encoded_closure_size(size_bytes: int) -> None:
    if (
        type(size_bytes) is not int
        or size_bytes < 0
        or size_bytes > MAX_ENCODED_CLOSURE_BYTES
    ):
        raise SpecificationFsContractError("encoded closure exceeds byte limit")


def _encoded_closure_size(body: bytes) -> int:
    return len(body)


def _pairs(pairs: list[tuple[str, object]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise SpecificationFsContractError("duplicate JSON field")
        result[key] = value
    return result


def _reject_constant(_: str) -> object:
    raise SpecificationFsContractError("non-finite JSON number")


def _object(value: object, fields: frozenset[str], field_name: str) -> JsonObject:
    if type(value) is not dict or frozenset(value) != fields:
        raise SpecificationFsContractError(f"{field_name} fields must be exact")
    return cast(JsonObject, value)


def _text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise SpecificationFsContractError(f"{field_name} must be text")
    return value


def _integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise SpecificationFsContractError(f"{field_name} must be an integer")
    return value


def _list(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise SpecificationFsContractError(f"{field_name} must be a list")
    return value


def _profile(value: object) -> SpecificationFsParserProfileCoordinate:
    body = _object(
        value,
        frozenset(
            {
                "parser_implementation_digest",
                "parser_implementation_ref",
                "profile_coordinate_digest",
                "profile_ref",
                "profile_schema_digest",
                "profile_schema_ref",
            }
        ),
        "profile",
    )
    result = SpecificationFsParserProfileCoordinate(
        parser_implementation_ref=_text(
            body["parser_implementation_ref"], "parser_implementation_ref"
        ),
        parser_implementation_digest=_text(
            body["parser_implementation_digest"], "parser_implementation_digest"
        ),
        profile_ref=_text(body["profile_ref"], "profile_ref"),
        profile_schema_ref=_text(body["profile_schema_ref"], "profile_schema_ref"),
        profile_schema_digest=_text(
            body["profile_schema_digest"], "profile_schema_digest"
        ),
    )
    retained_digest = _text(
        body["profile_coordinate_digest"], "profile_coordinate_digest"
    )
    if retained_digest != result.profile_coordinate_digest:
        raise SpecificationFsContractError("profile digest is not freshly derived")
    return result


def _member(value: object) -> SpecificationFsSourceMember:
    body = _object(
        value,
        frozenset(
            {
                "body_digest",
                "canonical_body",
                "member_digest",
                "relative_path",
                "role",
                "size_bytes",
            }
        ),
        "member",
    )
    try:
        role = SpecificationFsSourceRole(_text(body["role"], "role"))
    except ValueError as error:
        raise SpecificationFsContractError("role is invalid") from error
    result = SpecificationFsSourceMember(
        relative_path=_text(body["relative_path"], "relative_path"),
        role=role,
        canonical_body=_text(body["canonical_body"], "canonical_body"),
    )
    retained_size = _integer(body["size_bytes"], "size_bytes")
    retained_body_digest = _text(body["body_digest"], "body_digest")
    retained_member_digest = _text(body["member_digest"], "member_digest")
    if (
        retained_size != result.size_bytes
        or retained_body_digest != result.body_digest
        or retained_member_digest != result.member_digest
    ):
        raise SpecificationFsContractError("member evidence is not freshly derived")
    return result


def encode_specification_fs_source_closure(
    value: SpecificationFsSourceClosure,
) -> bytes:
    body = canonical_json_bytes(closure_to_wire(value))
    _validate_encoded_closure_size(_encoded_closure_size(body))
    return body


def _decode_utf8(body: bytes) -> str:
    return body.decode("utf-8", errors="strict")


def _decode_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)


def decode_specification_fs_source_closure(body: bytes) -> SpecificationFsSourceClosure:
    if type(body) is not bytes:
        raise SpecificationFsContractError("body must be exact bytes")
    _validate_encoded_closure_size(_encoded_closure_size(body))
    try:
        text = _decode_utf8(body)
        parsed = _decode_json(text)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, SpecificationFsContractError):
            raise
        raise SpecificationFsContractError("body must be canonical JSON") from error
    root = _object(
        parsed,
        frozenset(
            {
                "closure_digest",
                "contract",
                "manifest_member_digest",
                "member_set_digest",
                "members",
                "profile",
                "spec_root",
                "total_size_bytes",
            }
        ),
        "closure",
    )
    contract = _text(root["contract"], "contract")
    if contract != FS_SOURCE_CLOSURE_CONTRACT:
        raise SpecificationFsContractError("closure contract must be exact")
    result = SpecificationFsSourceClosure(
        spec_root=_text(root["spec_root"], "spec_root"),
        profile=_profile(root["profile"]),
        members=tuple(_member(item) for item in _list(root["members"], "members")),
        contract=contract,
    )
    manifest_member_digest = _text(
        root["manifest_member_digest"], "manifest_member_digest"
    )
    member_set_digest = _text(root["member_set_digest"], "member_set_digest")
    total_size_bytes = _integer(root["total_size_bytes"], "total_size_bytes")
    closure_digest = _text(root["closure_digest"], "closure_digest")
    if (
        manifest_member_digest != result.manifest_member_digest
        or member_set_digest != result.member_set_digest
        or total_size_bytes != result.total_size_bytes
        or closure_digest != result.closure_digest
    ):
        raise SpecificationFsContractError("closure evidence is not freshly derived")
    expected = encode_specification_fs_source_closure(result)
    if body != expected:
        raise SpecificationFsContractError("body must be canonical closure bytes")
    return result
