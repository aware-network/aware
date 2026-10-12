"""Portable grouped source correspondence; never membership or write authority."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .runtime import SemanticBody
from .semantic_candidates import MAX_CANDIDATES, CodeSemanticCandidate
from .semantic_input_producer import SemanticInputSourceCoordinate
from .source_origin import SOURCE_ORIGIN_REF, decode_source_origin_selection
from .source_selection import SOURCE_SELECTION_REF

GRAMMAR_SOURCE_GROUP = "aware.code.grammar-source-group.v1"
MAX_GROUP_BYTES = 8_388_608
MAX_GROUP_MEMBERS = 128
MAX_GROUP_EDGES = 256
MAX_GROUP_DEPTH = 64
_HEX = re.compile(r"[0-9a-f]*\Z")
_TOKEN = re.compile(r"^[^\s]+$")

GRAMMAR_SOURCE_GROUP_DESCRIPTOR = canonical_json_bytes(
    {
        "contract": GRAMMAR_SOURCE_GROUP,
        "version": 1,
        "fields": {
            "group": ["contract", "root_occurrence_ref", "members", "dependency_edges"],
            "member": [
                "occurrence_ref",
                "selection_coordinate",
                "selection_body_hex",
                "origin_coordinate",
                "origin_body_hex",
                "sources",
            ],
            "source": ["relative_path", "coordinate", "body_hex"],
            "edge": [
                "owner_occurrence_ref",
                "target_occurrence_ref",
                "dependency_kind",
                "dependency_ref",
            ],
        },
        "selection_contract": SOURCE_SELECTION_REF.to_wire(),
        "origin_contract": SOURCE_ORIGIN_REF.to_wire(),
        "coordinates": "complete existing SemanticValueCoordinate V1 wire",
        "body_encoding": "lowercase even-length hex; canonical selection/origin bodies; exact original source bytes",
        "bounds": {
            "members_including_root": MAX_GROUP_MEMBERS,
            "dependency_edges": MAX_GROUP_EDGES,
            "member_sources": MAX_CANDIDATES,
            "aggregate_context_bytes": MAX_GROUP_BYTES,
            "edge_token_bytes": 512,
        },
        "order": {
            "members": "unique UTF-8 occurrence_ref order",
            "dependency_edges": "unique UTF-8 four-field tuple order",
            "sources": "original source-selection order",
        },
        "correspondence": "canonical selection/origin codecs; complete source coordinates and bodies; root present; all endpoints present and reachable",
        "authority": "portable correspondence only; original Workspace source/result/edge/lifetime authentication remains separate",
    }
)
GRAMMAR_SOURCE_GROUP_REF = SemanticContractRef(
    GRAMMAR_SOURCE_GROUP, "1", ContentDigest.of_bytes(GRAMMAR_SOURCE_GROUP_DESCRIPTOR)
)
GRAMMAR_SOURCE_GROUP_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.grammar-source-group.codec.v1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": GRAMMAR_SOURCE_GROUP_REF.to_wire(),
                "validation": "closed exact-type canonical group; bounded full selection/origin/source correspondence and opaque connectivity; no owner callbacks, authority issuance, grammar interpretation or source access",
            }
        )
    ),
)


def _exact[T](value: object, expected: type[T]) -> T:
    if type(value) is not expected:
        raise TypeError("group value has an incompatible exact type")
    return cast(T, value)


def _field(value: object, name: str) -> object:
    try:
        return cast(object, object.__getattribute__(value, name))
    except AttributeError as exc:
        raise ContractViolation("group value has an uninitialized field") from exc


def _token(value: object, *, limit: int | None = None) -> str:
    text = _exact(value, str)
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractViolation("group token must be UTF-8") from exc
    if not text or not _TOKEN.fullmatch(text):
        raise ContractViolation("group token must preserve the Code token grammar")
    if limit is not None and size > limit:
        raise ContractViolation("group token exceeds byte bound")
    return text


def _tuple_items(value: object) -> tuple[object, ...]:
    return cast(tuple[object, ...], _exact(value, tuple))


def _digest(value: object) -> ContentDigest:
    digest = _exact(value, ContentDigest)
    _ = _exact(_field(digest, "value"), str)
    ContentDigest.__post_init__(digest)
    return digest


def _coordinate(value: object) -> SemanticValueCoordinate:
    item = _exact(value, SemanticValueCoordinate)
    _ = _token(_field(item, "role"))
    _ = _token(_field(item, "value_ref"))
    ref = _exact(_field(item, "contract"), SemanticContractRef)
    _ = _token(_field(ref, "key"))
    _ = _token(_field(ref, "version"))
    _ = _digest(_field(ref, "schema_digest"))
    _ = _digest(_field(item, "digest"))
    size = _exact(_field(item, "size_bytes"), int)
    if not 0 <= size <= MAX_GROUP_BYTES:
        raise ContractViolation("source coordinate exceeds group byte bound")
    return item


def _hex_bytes(value: object) -> bytes:
    text = _exact(value, str)
    if len(text) > MAX_GROUP_BYTES * 2 or len(text) % 2 or not _HEX.fullmatch(text):
        raise ContractViolation("source body must be bounded lowercase even-length hex")
    return bytes.fromhex(text)


def _body(coordinate: SemanticValueCoordinate, value: object) -> bytes:
    body = _hex_bytes(value)
    if coordinate.size_bytes != len(
        body
    ) or coordinate.digest != ContentDigest.of_bytes(body):
        raise ContractViolation("source body differs from its complete coordinate")
    return body


def _coordinate_wire(value: SemanticValueCoordinate) -> dict[str, object]:
    # Complete exact-type validation precedes this private synchronous projection.
    ref = value.contract
    return {
        "role": value.role,
        "contract": {
            "key": ref.key,
            "version": ref.version,
            "schema_digest": ref.schema_digest.value,
        },
        "value_ref": value.value_ref,
        "digest": value.digest.value,
        "size_bytes": value.size_bytes,
    }


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceBodyV1:
    relative_path: str
    coordinate: SemanticValueCoordinate
    body_hex: str

    def __post_init__(self) -> None:
        _validate_source(self)

    def to_wire(self) -> dict[str, object]:
        _validate_source(self)
        return _source_wire(self)


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceMemberV1:
    occurrence_ref: str
    selection_coordinate: SemanticValueCoordinate
    selection_body_hex: str
    origin_coordinate: SemanticValueCoordinate
    origin_body_hex: str
    sources: tuple[CodeGrammarSourceBodyV1, ...]

    def __post_init__(self) -> None:
        _validate_member(self)

    def to_wire(self) -> dict[str, object]:
        _validate_member(self)
        return _member_wire(self)


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceEdgeV1:
    owner_occurrence_ref: str
    target_occurrence_ref: str
    dependency_kind: str
    dependency_ref: str

    def __post_init__(self) -> None:
        _validate_edge(self)

    def to_wire(self) -> dict[str, object]:
        _validate_edge(self)
        return _edge_wire(self)


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceGroupV1:
    root_occurrence_ref: str
    members: tuple[CodeGrammarSourceMemberV1, ...]
    dependency_edges: tuple[CodeGrammarSourceEdgeV1, ...]

    def __post_init__(self) -> None:
        _ = _validated_wire(self)

    def to_wire(self) -> dict[str, object]:
        return _validated_wire(self)


def _validate_source(value: object) -> None:
    source = _exact(value, CodeGrammarSourceBodyV1)
    path = _exact(_field(source, "relative_path"), str)
    coordinate = _coordinate(_field(source, "coordinate"))
    _ = CodeSemanticCandidate(path, coordinate.digest)
    _ = _body(coordinate, _field(source, "body_hex"))


def _validate_member(value: object) -> None:
    member = _exact(value, CodeGrammarSourceMemberV1)
    occurrence = _token(_field(member, "occurrence_ref"))
    selected = _coordinate(_field(member, "selection_coordinate"))
    original = _coordinate(_field(member, "origin_coordinate"))
    source_items = _tuple_items(_field(member, "sources"))
    if len(source_items) > MAX_CANDIDATES:
        raise ContractViolation("group member source count exceeds bound")
    sources = tuple(_exact(source, CodeGrammarSourceBodyV1) for source in source_items)
    selected_body = _body(selected, _field(member, "selection_body_hex"))
    original_body = _body(original, _field(member, "origin_body_hex"))
    if (
        selected.contract != SOURCE_SELECTION_REF
        or original.contract != SOURCE_ORIGIN_REF
    ):
        raise ContractViolation("group member must preserve original V1 contracts")
    for source in sources:
        _validate_source(source)
    origin = decode_source_origin_selection(
        original_body,
        selection_body=selected_body,
        source_coordinates=tuple(
            SemanticInputSourceCoordinate(source.relative_path, source.coordinate)
            for source in sources
        ),
    )
    if (
        origin.selection_coordinate != selected
        or origin.occurrence.occurrence_ref != occurrence
    ):
        raise ContractViolation("group member origin or selection coordinate differs")


def _validate_edge(value: object) -> None:
    edge = _exact(value, CodeGrammarSourceEdgeV1)
    for name in (
        "owner_occurrence_ref",
        "target_occurrence_ref",
        "dependency_kind",
        "dependency_ref",
    ):
        _ = _token(_field(edge, name), limit=512)


def _source_wire(value: CodeGrammarSourceBodyV1) -> dict[str, object]:
    return {
        "relative_path": value.relative_path,
        "coordinate": _coordinate_wire(value.coordinate),
        "body_hex": value.body_hex,
    }


def _member_wire(value: CodeGrammarSourceMemberV1) -> dict[str, object]:
    return {
        "occurrence_ref": value.occurrence_ref,
        "selection_coordinate": _coordinate_wire(value.selection_coordinate),
        "selection_body_hex": value.selection_body_hex,
        "origin_coordinate": _coordinate_wire(value.origin_coordinate),
        "origin_body_hex": value.origin_body_hex,
        "sources": [_source_wire(source) for source in value.sources],
    }


def _edge_wire(value: CodeGrammarSourceEdgeV1) -> dict[str, object]:
    return {
        "owner_occurrence_ref": value.owner_occurrence_ref,
        "target_occurrence_ref": value.target_occurrence_ref,
        "dependency_kind": value.dependency_kind,
        "dependency_ref": value.dependency_ref,
    }


def _validated_wire(value: object) -> dict[str, object]:
    group = _exact(value, CodeGrammarSourceGroupV1)
    root = _token(_field(group, "root_occurrence_ref"))
    member_items = _tuple_items(_field(group, "members"))
    edge_items = _tuple_items(_field(group, "dependency_edges"))
    if (
        not 1 <= len(member_items) <= MAX_GROUP_MEMBERS
        or len(edge_items) > MAX_GROUP_EDGES
    ):
        raise ContractViolation("group collection counts exceed bounds")
    members = tuple(_exact(item, CodeGrammarSourceMemberV1) for item in member_items)
    edges = tuple(_exact(item, CodeGrammarSourceEdgeV1) for item in edge_items)
    # Reject the hex lower-bound before nested decoding or aggregate allocation.
    lower_bound = 0
    for member in members:
        for name in ("selection_body_hex", "origin_body_hex"):
            lower_bound += len(_exact(_field(member, name), str))
        sources = _tuple_items(_field(member, "sources"))
        if len(sources) > MAX_CANDIDATES:
            raise ContractViolation("group member source count exceeds bound")
        for source in sources:
            _ = _exact(source, CodeGrammarSourceBodyV1)
            lower_bound += len(_exact(_field(source, "body_hex"), str))
        if lower_bound > MAX_GROUP_BYTES:
            raise ContractViolation("group hex bodies exceed byte bound")
    for member in members:
        _validate_member(member)
    for edge in edges:
        _validate_edge(edge)
    refs = [member.occurrence_ref for member in members]
    if refs != sorted(set(refs), key=str.encode) or root not in refs:
        raise ContractViolation("group members must be unique ordered and contain root")
    edge_keys = [
        (
            edge.owner_occurrence_ref,
            edge.target_occurrence_ref,
            edge.dependency_kind,
            edge.dependency_ref,
        )
        for edge in edges
    ]
    if edge_keys != sorted(
        set(edge_keys), key=lambda row: tuple(item.encode() for item in row)
    ):
        raise ContractViolation("group edges must be unique and UTF-8 ordered")
    known = set(refs)
    adjacency: dict[str, set[str]] = {ref: set() for ref in refs}
    for owner, target, _, _ in edge_keys:
        if owner not in known or target not in known:
            raise ContractViolation("group edge names an absent occurrence")
        adjacency[owner].add(target)
    reachable = {root}
    pending = [root]
    while pending:
        for target in adjacency[pending.pop()]:
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    if reachable != known:
        raise ContractViolation("group contains unreachable occurrences")
    wire: dict[str, object] = {
        "contract": GRAMMAR_SOURCE_GROUP,
        "root_occurrence_ref": root,
        "members": [_member_wire(member) for member in members],
        "dependency_edges": [_edge_wire(edge) for edge in edges],
    }
    if len(canonical_json_bytes(wire)) > MAX_GROUP_BYTES:
        raise ContractViolation("complete group body exceeds byte bound")
    return wire


def encode_grammar_source_group(value: CodeGrammarSourceGroupV1) -> bytes:
    return canonical_json_bytes(_validated_wire(value))


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate group JSON key")
        result[key] = value
    return result


def _keys(value: object, keys: set[str]) -> dict[str, object]:
    row = cast(dict[object, object], _exact(value, dict))
    if set(row) != keys:
        raise ContractViolation("group JSON fields differ")
    return cast(dict[str, object], row)


def _list(value: object, limit: int) -> list[object]:
    items = cast(list[object], _exact(value, list))
    if len(items) > limit:
        raise ContractViolation("group JSON collection exceeds bound")
    return items


def _read_coordinate(value: object) -> SemanticValueCoordinate:
    row = _keys(value, {"role", "contract", "value_ref", "digest", "size_bytes"})
    ref = _keys(row["contract"], {"key", "version", "schema_digest"})
    return SemanticValueCoordinate(
        _token(row["role"]),
        SemanticContractRef(
            _token(ref["key"]),
            _token(ref["version"]),
            ContentDigest.of_wire(ref["schema_digest"]),
        ),
        _token(row["value_ref"]),
        ContentDigest.of_wire(row["digest"]),
        _exact(row["size_bytes"], int),
    )


def decode_grammar_source_group(body: bytes) -> CodeGrammarSourceGroupV1:
    _ = _exact(body, bytes)
    if not body or len(body) > MAX_GROUP_BYTES:
        raise ContractViolation("group body exceeds wire bound")
    try:
        value = cast(object, json.loads(body.decode("utf-8"), object_pairs_hook=_pairs))
        stack: list[tuple[object, int]] = [(value, 1)]
        while stack:
            item, depth = stack.pop()
            if depth > MAX_GROUP_DEPTH:
                raise ContractViolation("group JSON exceeds nesting bound")
            if type(item) is dict:
                row_values = cast(dict[str, object], item)
                stack.extend((child, depth + 1) for child in row_values.values())
            elif type(item) is list:
                children = cast(list[object], item)
                stack.extend((child, depth + 1) for child in children)
        if canonical_json_bytes(value) != body:
            raise ContractViolation("group JSON must be canonical")
        row = _keys(
            value, {"contract", "root_occurrence_ref", "members", "dependency_edges"}
        )
        if _exact(row["contract"], str) != GRAMMAR_SOURCE_GROUP:
            raise ContractViolation("group contract differs")
        members: list[CodeGrammarSourceMemberV1] = []
        for item in _list(row["members"], MAX_GROUP_MEMBERS):
            member = _keys(
                item,
                {
                    "occurrence_ref",
                    "selection_coordinate",
                    "selection_body_hex",
                    "origin_coordinate",
                    "origin_body_hex",
                    "sources",
                },
            )
            sources: list[CodeGrammarSourceBodyV1] = []
            for item in _list(member["sources"], MAX_CANDIDATES):
                source = _keys(item, {"relative_path", "coordinate", "body_hex"})
                sources.append(
                    CodeGrammarSourceBodyV1(
                        _exact(source["relative_path"], str),
                        _read_coordinate(source["coordinate"]),
                        _exact(source["body_hex"], str),
                    )
                )
            members.append(
                CodeGrammarSourceMemberV1(
                    _token(member["occurrence_ref"]),
                    _read_coordinate(member["selection_coordinate"]),
                    _exact(member["selection_body_hex"], str),
                    _read_coordinate(member["origin_coordinate"]),
                    _exact(member["origin_body_hex"], str),
                    tuple(sources),
                )
            )
        edges: list[CodeGrammarSourceEdgeV1] = []
        for item in _list(row["dependency_edges"], MAX_GROUP_EDGES):
            edge = _keys(
                item,
                {
                    "owner_occurrence_ref",
                    "target_occurrence_ref",
                    "dependency_kind",
                    "dependency_ref",
                },
            )
            edges.append(
                CodeGrammarSourceEdgeV1(
                    *(
                        _token(edge[name])
                        for name in (
                            "owner_occurrence_ref",
                            "target_occurrence_ref",
                            "dependency_kind",
                            "dependency_ref",
                        )
                    )
                )
            )
        return CodeGrammarSourceGroupV1(
            _token(row["root_occurrence_ref"]), tuple(members), tuple(edges)
        )
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ContractViolation("invalid portable grammar source group") from exc


def grammar_source_group_body(value: CodeGrammarSourceGroupV1) -> SemanticBody:
    body = encode_grammar_source_group(value)
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(
        SemanticValueCoordinate(
            "grammar_source_group",
            GRAMMAR_SOURCE_GROUP_REF,
            "grammar-source-group:" + digest.value,
            digest,
            len(body),
        ),
        body,
    )


class CodeGrammarSourceGroupCodec:
    contract: SemanticContractRef = GRAMMAR_SOURCE_GROUP_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_SOURCE_GROUP_CODEC_IMPLEMENTATION
    )

    def encode(self, value: object) -> bytes:
        return encode_grammar_source_group(_exact(value, CodeGrammarSourceGroupV1))

    def decode(self, body: bytes) -> CodeGrammarSourceGroupV1:
        return decode_grammar_source_group(body)
