"""Owner-produced portable source requests; membership remains host-owned."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .dependency_input_codec import SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF
from .runtime import SemanticBody
from .semantic_candidates import MAX_CANDIDATES, CodeSemanticCandidate

SOURCE_SELECTION = "aware.code.semantic-source-selection.v1"
MAX_SOURCE_SELECTION_BYTES = 8_388_608
MAX_SOURCE_SELECTION_PREDECESSORS = 64


def _contract_wire(value: SemanticContractRef) -> dict[str, object]:
    return {"key": value.key, "version": value.version,
            "schema_digest": value.schema_digest.value}


def _coordinate_wire(value: SemanticValueCoordinate) -> dict[str, object]:
    return {"role": value.role, "contract": _contract_wire(value.contract),
            "value_ref": value.value_ref, "digest": value.digest.value,
            "size_bytes": value.size_bytes}


def _source_wire(value: SemanticSelectedSource) -> dict[str, object]:
    return {"role": value.role, "contract": _contract_wire(value.contract),
            "relative_path": value.relative_path,
            "content_digest": value.content_digest.value}


def _selection_wire(value: SemanticSourceSelection) -> dict[str, object]:
    # Private projection only: the complete exact graph is synchronously
    # validated before this call. No owner callback, await or retained cache
    # separates validation from projection.
    package = value.package
    return {"contract": SOURCE_SELECTION,
            "package": {"package_ref": package.package_ref,
                        "package_kind": package.package_kind,
                        "manifest_digest": package.manifest_digest.value},
            "source_identity_digest": value.source_identity_digest.value,
            "production_input_digest": value.production_input_digest.value,
            "predecessor_coordinates": [_coordinate_wire(x) for x in value.predecessor_coordinates],
            "sources": [_source_wire(x) for x in value.sources]}


def _canonical_wire(value: dict[str, object]) -> bytes:
    # The projection contains only validated exact strings/integers and our
    # fresh native containers. Use the existing canonical JSON policy without
    # repeating a generic admission walk of those newly constructed values.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SemanticSelectedSource:
    role: str
    contract: SemanticContractRef
    relative_path: str
    content_digest: ContentDigest

    def __post_init__(self) -> None:
        if type(self.role) is not str or not self.role or any(c.isspace() for c in self.role):
            raise ContractViolation("selected source role must be an exact token")
        if type(self.contract) is not SemanticContractRef:
            raise ContractViolation("selected source contract must be exact")
        self.contract.__post_init__()
        if self.contract == SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF:
            raise ContractViolation("dependency products require their existing admitted entrance")
        CodeSemanticCandidate(self.relative_path, self.content_digest)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _source_wire(self)


@dataclass(frozen=True, slots=True)
class SemanticSourceSelection:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    production_input_digest: ContentDigest
    predecessor_coordinates: tuple[SemanticValueCoordinate, ...]
    sources: tuple[SemanticSelectedSource, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not SemanticPackageCoordinate:
            raise ContractViolation("selected package must be exact")
        self.package.__post_init__()
        for digest in (self.source_identity_digest, self.production_input_digest):
            if type(digest) is not ContentDigest:
                raise ContractViolation("selection digest must be exact")
            digest.__post_init__()
        if (type(self.predecessor_coordinates) is not tuple
                or len(self.predecessor_coordinates) > MAX_SOURCE_SELECTION_PREDECESSORS):
            raise ContractViolation("selection predecessors exceed bound")
        for item in self.predecessor_coordinates:
            if type(item) is not SemanticValueCoordinate:
                raise ContractViolation("selection predecessor must be exact")
            item.__post_init__()
        if type(self.sources) is not tuple or len(self.sources) > MAX_CANDIDATES:
            raise ContractViolation("selected source count exceeds bound")
        keys = []
        roles = {}
        for item in self.sources:
            if type(item) is not SemanticSelectedSource:
                raise ContractViolation("selected source must be exact")
            item.__post_init__()
            keys.append(item.relative_path.encode())
            if item.role in roles and roles[item.role] != item.contract:
                raise ContractViolation("selected source role has multiple contracts")
            roles[item.role] = item.contract
        if keys != sorted(set(keys)):
            raise ContractViolation("selected source paths must be unique and UTF-8 ordered")
        if len(_canonical_wire(_selection_wire(self))) > MAX_SOURCE_SELECTION_BYTES:
            raise ContractViolation("selected source body exceeds bound")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _selection_wire(self)


SOURCE_SELECTION_REF = SemanticContractRef(SOURCE_SELECTION, "1", ContentDigest.of_bytes(
    canonical_json_bytes({
        "contract": SOURCE_SELECTION,
        "shape": "package/source_identity_digest/production_input_digest/predecessor_coordinates/sources[role,contract,relative_path,content_digest]",
        "bounds": [MAX_CANDIDATES, MAX_SOURCE_SELECTION_BYTES, MAX_SOURCE_SELECTION_PREDECESSORS],
        "paths": "existing Code candidate POSIX NFC grammar; unique UTF-8 path order; one contract per role",
        "authority": "portable owner request only; original result and membership validated separately",
    })
))
SOURCE_SELECTION_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.semantic-source-selection.codec.v1", ContentDigest.of_bytes(canonical_json_bytes({
        "contract": SOURCE_SELECTION_REF.to_wire(),
        "validation": "strict bounded canonical portable source requests; no membership authority",
    })),
)


def encode_source_selection(value: SemanticSourceSelection) -> bytes:
    if type(value) is not SemanticSourceSelection:
        raise ContractViolation("exact source selection required")
    value.__post_init__()
    return _canonical_wire(_selection_wire(value))


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate selection JSON key")
        result[key] = value
    return result


def _keys(value, keys):
    if type(value) is not dict or set(value) != keys:
        raise ContractViolation("selection fields differ")
    return value


def _ref(value):
    v = _keys(value, {"key", "version", "schema_digest"})
    return SemanticContractRef(v["key"], v["version"], ContentDigest.of_wire(v["schema_digest"]))


def _coordinate(value):
    v = _keys(value, {"role", "contract", "value_ref", "digest", "size_bytes"})
    return SemanticValueCoordinate(v["role"], _ref(v["contract"]), v["value_ref"],
                                   ContentDigest.of_wire(v["digest"]), v["size_bytes"])


def decode_source_selection(body: bytes) -> SemanticSourceSelection:
    if type(body) is not bytes or len(body) > MAX_SOURCE_SELECTION_BYTES:
        raise ContractViolation("selection body must be bounded exact bytes")
    try:
        v = _keys(json.loads(body.decode("utf-8"), object_pairs_hook=_object), {
            "contract", "package", "source_identity_digest", "production_input_digest",
            "predecessor_coordinates", "sources",
        })
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ContractViolation("invalid source selection JSON") from exc
    if v["contract"] != SOURCE_SELECTION:
        raise ContractViolation("source selection contract differs")
    p = _keys(v["package"], {"package_ref", "package_kind", "manifest_digest"})
    if (type(v["sources"]) is not list or len(v["sources"]) > MAX_CANDIDATES
            or type(v["predecessor_coordinates"]) is not list
            or len(v["predecessor_coordinates"]) > MAX_SOURCE_SELECTION_PREDECESSORS):
        raise ContractViolation("selection row bounds differ")
    rows = []
    for row in v["sources"]:
        row = _keys(row, {"role", "contract", "relative_path", "content_digest"})
        rows.append(SemanticSelectedSource(row["role"], _ref(row["contract"]),
                                          row["relative_path"], ContentDigest.of_wire(row["content_digest"])))
    result = SemanticSourceSelection(
        SemanticPackageCoordinate(p["package_ref"], p["package_kind"], ContentDigest.of_wire(p["manifest_digest"])),
        ContentDigest.of_wire(v["source_identity_digest"]),
        ContentDigest.of_wire(v["production_input_digest"]),
        tuple(_coordinate(x) for x in v["predecessor_coordinates"]), tuple(rows),
    )
    # The freshly constructed result has already validated its complete closed
    # graph and bound. No foreign call can intervene before canonical parity.
    if _canonical_wire(_selection_wire(result)) != body:
        raise ContractViolation("source selection body is not canonical")
    return result


def source_selection_body(value: SemanticSourceSelection, *, role: str) -> SemanticBody:
    body = encode_source_selection(value)
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(SemanticValueCoordinate(role, SOURCE_SELECTION_REF,
        "source-selection:" + digest.value, digest, len(body)), body)


class SemanticSourceSelectionCodec:
    contract = SOURCE_SELECTION_REF
    implementation = SOURCE_SELECTION_CODEC_IMPLEMENTATION

    def encode(self, value: object) -> bytes:
        if type(value) is not SemanticSourceSelection:
            raise ContractViolation("exact source selection required")
        return encode_source_selection(value)

    def decode(self, body: bytes) -> SemanticSourceSelection:
        return decode_source_selection(body)


__all__ = ["SemanticSelectedSource", "SemanticSourceSelection", "SemanticSourceSelectionCodec",
           "SOURCE_SELECTION_REF", "SOURCE_SELECTION_CODEC_IMPLEMENTATION",
           "encode_source_selection", "decode_source_selection", "source_selection_body"]
