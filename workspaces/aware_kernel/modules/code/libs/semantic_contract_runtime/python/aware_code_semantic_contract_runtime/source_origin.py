"""Portable selected-source locations and logical addresses, never admissions."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from typing import cast

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
from .semantic_input_producer import SemanticInputSourceCoordinate
from .source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSourceSelection,
    decode_source_selection,
    encode_source_selection,
)

SOURCE_ORIGIN = "aware.code.semantic-input-source-origin.v1"
MAX_SOURCE_ORIGIN_BYTES = 8_388_608
MAX_ORIGIN_TEXT_BYTES = 512
MAX_LOCATION_BYTES = 4_096
_ASCII_DROP = {ord(c): None for c in "\x00\t\n\r\v\f\x1c\x1d\x1e\x1f "}


def _text(value: str, *, limit: int = MAX_ORIGIN_TEXT_BYTES) -> None:
    if type(value) is not str:
        raise ContractViolation("origin text must be exact str")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise ContractViolation("origin text must be UTF-8") from exc
    ascii_text = value.isascii()
    forbidden = (len(value.translate(_ASCII_DROP)) != len(value) if ascii_text
                 else any(c.isspace() or c == "\x00" for c in value))
    if (not 1 <= len(encoded) <= limit
            or (not ascii_text and unicodedata.normalize("NFC", value) != value)
            or forbidden):
        raise ContractViolation("origin token must be bounded UTF-8 NFC")


def _digest(value: ContentDigest) -> None:
    if type(value) is not ContentDigest or type(value.value) is not str:
        raise ContractViolation("origin digest must be exact")
    value.__post_init__()


def _ref(value: SemanticContractRef) -> None:
    if type(value) is not SemanticContractRef:
        raise ContractViolation("origin contract must be exact")
    _text(value.key)
    _text(value.version)
    _digest(value.schema_digest)


def _coordinate(value: SemanticValueCoordinate) -> None:
    if type(value) is not SemanticValueCoordinate:
        raise ContractViolation("origin coordinate must be exact")
    _text(value.role)
    _text(value.value_ref)
    _ref(value.contract)
    _digest(value.digest)
    if type(value.size_bytes) is not int or not 0 <= value.size_bytes <= MAX_SOURCE_ORIGIN_BYTES:
        raise ContractViolation("origin coordinate size exceeds bound")


def _source(value: SemanticInputSourceCoordinate) -> None:
    if type(value) is not SemanticInputSourceCoordinate:
        raise ContractViolation("origin source must be exact")
    _coordinate(value.coordinate)
    CodeSemanticCandidate(value.relative_path, value.coordinate.digest)
    if value.coordinate.contract == SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF:
        raise ContractViolation("dependency products require their admitted product rail")


def _location(value: str) -> None:
    # Lexical POSIX wire only. No filesystem access or physical authority.
    if type(value) is not str or not value.startswith("/"):
        raise ContractViolation("outer location must be exact absolute POSIX text")
    if value == "/":
        return
    CodeSemanticCandidate(value[1:], ContentDigest.of_bytes(b"location grammar"))
    if len(value.encode("utf-8")) > MAX_LOCATION_BYTES:
        raise ContractViolation("outer location exceeds byte bound")


def _coordinate_wire(value: SemanticValueCoordinate) -> dict[str, object]:
    """Projection after this synchronous call's exact closed validation."""
    contract = value.contract
    return {"role": value.role, "contract": {"key": contract.key,
        "version": contract.version, "schema_digest": contract.schema_digest.value},
        "value_ref": value.value_ref, "digest": value.digest.value, "size_bytes": value.size_bytes}


def _source_wire(value: SemanticInputSourceCoordinate) -> dict[str, object]:
    return {"relative_path": value.relative_path, "coordinate": _coordinate_wire(value.coordinate)}


def _canonical_wire(wire: dict[str, object]) -> bytes:
    # This projection has already been checked against the closed exact-type
    # origin shape. Preserve the shared canonical JSON rules without walking
    # that freshly built JSON-only projection a second time.
    return json.dumps(wire, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SemanticInputPackageOccurrence:
    """Logical declaration address; content/epoch/physical continuity are separate."""

    repository_binding_ref: str
    scope_key: str
    module_id: str
    package_id: str
    package_root: str
    outer_manifest_path: str

    def __post_init__(self) -> None:
        _text(self.repository_binding_ref)
        for item in (self.module_id, self.package_id):
            _text(item, limit=255)
            if "/" in item or "\\" in item or item in {".", ".."}:
                raise ContractViolation("occurrence IDs must be single components")
        digest = ContentDigest.of_bytes(b"occurrence path grammar")
        for item in (self.scope_key, self.outer_manifest_path):
            CodeSemanticCandidate(item, digest)
        # Empty package_root explicitly means the admitted repository root.
        if type(self.package_root) is not str:
            raise ContractViolation("occurrence package root must be exact text")
        if self.package_root:
            CodeSemanticCandidate(self.package_root, digest)

    def to_wire(self) -> dict[str, object]:
        return {"repository_binding_ref": self.repository_binding_ref,
                "scope_key": self.scope_key, "module_id": self.module_id,
                "package_id": self.package_id, "package_root": self.package_root,
                "outer_manifest_path": self.outer_manifest_path}

    @property
    def occurrence_ref(self) -> str:
        self.__post_init__()
        return "code-package-occurrence:" + ContentDigest.of_bytes(
            canonical_json_bytes(self.to_wire())).value


def source_occurrence_ref(occurrence: SemanticInputPackageOccurrence, relative_path: str) -> str:
    """Deterministic logical address data; this function issues no authority."""
    if type(occurrence) is not SemanticInputPackageOccurrence:
        raise ContractViolation("exact package occurrence required")
    occurrence.__post_init__()
    CodeSemanticCandidate(relative_path, ContentDigest.of_bytes(b"occurrence path grammar"))
    return "code-source-occurrence:" + ContentDigest.of_bytes(canonical_json_bytes({
        **occurrence.to_wire(), "relative_path": relative_path,
    })).value


@dataclass(frozen=True, slots=True)
class SemanticInputSourceOccurrence:
    source: SemanticInputSourceCoordinate
    occurrence_ref: str

    def __post_init__(self) -> None:
        _source(self.source)
        _text(self.occurrence_ref)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _source_occurrence_wire(self)


def _source_occurrence_wire(value: SemanticInputSourceOccurrence) -> dict[str, object]:
    return {"source": _source_wire(value.source), "occurrence_ref": value.occurrence_ref}


@dataclass(frozen=True, slots=True)
class SemanticInputSourceOrigin:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    selection_coordinate: SemanticValueCoordinate
    selection_input_digest: ContentDigest
    occurrence: SemanticInputPackageOccurrence
    outer_package_root: str
    outer_manifest: SemanticInputSourceCoordinate
    sources: tuple[SemanticInputSourceOccurrence, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not SemanticPackageCoordinate:
            raise ContractViolation("origin package must be exact")
        _text(self.package.package_ref)
        _text(self.package.package_kind)
        _digest(self.package.manifest_digest)
        _digest(self.source_identity_digest)
        _digest(self.selection_input_digest)
        _coordinate(self.selection_coordinate)
        if self.selection_coordinate.contract != SOURCE_SELECTION_REF:
            raise ContractViolation("origin must bind a source-selection coordinate")
        if type(self.occurrence) is not SemanticInputPackageOccurrence:
            raise ContractViolation("origin package occurrence must be exact")
        self.occurrence.__post_init__()
        _location(self.outer_package_root)
        _source(self.outer_manifest)
        if (self.outer_manifest.relative_path != self.occurrence.outer_manifest_path
                or self.outer_manifest.coordinate.digest != self.package.manifest_digest):
            raise ContractViolation("outer manifest differs from occurrence/package")
        if type(self.sources) is not tuple or len(self.sources) > MAX_CANDIDATES:
            raise ContractViolation("origin sources exceed count bound")
        previous = b""
        budget = len(_canonical_wire(self._wire([])))
        occurrence_wire = self.occurrence.to_wire()
        roles: dict[str, SemanticContractRef] = {}
        for i, row in enumerate(self.sources):
            if type(row) is not SemanticInputSourceOccurrence:
                raise ContractViolation("origin source row must be exact")
            row.__post_init__()
            path = row.source.relative_path.encode("utf-8")
            if path <= previous:
                raise ContractViolation("origin paths must be unique UTF-8 ordered")
            previous = path
            # Occurrence and source path were already validated in this pure
            # synchronous pass. Reuse their projection, never an admission.
            expected_ref = "code-source-occurrence:" + ContentDigest.of_bytes(_canonical_wire({
                **occurrence_wire, "relative_path": row.source.relative_path,
            })).value
            if row.occurrence_ref != expected_ref:
                raise ContractViolation("logical source occurrence differs")
            coordinate = row.source.coordinate
            if coordinate.role in roles and roles[coordinate.role] != coordinate.contract:
                raise ContractViolation("origin role has multiple contracts")
            roles[coordinate.role] = coordinate.contract
            budget += len(_canonical_wire(_source_occurrence_wire(row))) + int(i > 0)
            if budget > MAX_SOURCE_ORIGIN_BYTES:
                raise ContractViolation("origin canonical body exceeds byte bound")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return self._project_wire()

    def _project_wire(self) -> dict[str, object]:
        return self._wire([_source_occurrence_wire(row) for row in self.sources])

    def _wire(self, rows: list[dict[str, object]]) -> dict[str, object]:
        return {"contract": SOURCE_ORIGIN, "package": {
                    "package_ref": self.package.package_ref, "package_kind": self.package.package_kind,
                    "manifest_digest": self.package.manifest_digest.value},
                "source_identity_digest": self.source_identity_digest.value,
                "selection_coordinate": _coordinate_wire(self.selection_coordinate),
                "selection_input_digest": self.selection_input_digest.value,
                "occurrence": self.occurrence.to_wire(),
                "outer_package_root": self.outer_package_root,
                "outer_manifest": _source_wire(self.outer_manifest),
                "sources": rows}


SOURCE_ORIGIN_DESCRIPTOR = canonical_json_bytes({
    "contract": SOURCE_ORIGIN, "version": 1,
    "fields": ["package", "source_identity_digest", "selection_coordinate",
               "selection_input_digest", "occurrence", "outer_package_root",
               "outer_manifest", "sources[source,occurrence_ref]"],
    "occurrence_fields": ["repository_binding_ref", "scope_key", "module_id",
                          "package_id", "package_root", "outer_manifest_path"],
    "bounds": {"rows": MAX_CANDIDATES, "bytes": MAX_SOURCE_ORIGIN_BYTES,
               "tokens": MAX_ORIGIN_TEXT_BYTES, "IDs": 255, "absolute_location": MAX_LOCATION_BYTES},
    "paths": "existing Code candidate grammar; empty package_root means repository root; lexical absolute POSIX location",
    "occurrence": "code-source-occurrence: plus SHA256 of canonical occurrence fields and relative_path; no content/epoch; code-package-occurrence: uses occurrence fields only",
    "correspondence": "outer manifest matches package digest and occurrence path; unique UTF8-ordered source paths; one contract per role; logical refs recomputed; original selection/input digest kept distinct",
    "authority": "portable location and logical address data only; original host/source/result/lifetime admission remains issuer-owned; no physical continuity or lineage",
})
SOURCE_ORIGIN_REF = SemanticContractRef(SOURCE_ORIGIN, "1", ContentDigest.of_bytes(SOURCE_ORIGIN_DESCRIPTOR))
SOURCE_ORIGIN_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.semantic-input-source-origin.codec.v1", ContentDigest.of_bytes(canonical_json_bytes({
        "contract": SOURCE_ORIGIN_REF.to_wire(),
        "validation": "exact bounded canonical closed shape and portable correspondence; no filesystem or authority issuance",
    })),
)


def encode_source_origin(value: SemanticInputSourceOrigin) -> bytes:
    if type(value) is not SemanticInputSourceOrigin:
        raise ContractViolation("exact source origin required")
    value.__post_init__()
    return _canonical_wire(value._project_wire())


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ContractViolation("duplicate origin JSON key")
        value[key] = item
    return value


def _keys(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ContractViolation("origin fields differ")
    return cast(dict[str, object], value)


def _read_ref(value: object) -> SemanticContractRef:
    v = _keys(value, {"key", "version", "schema_digest"})
    # Validate text before contract constructors, including their normalization.
    for key in ("key", "version"):
        _text(cast(str, v[key]))
    return SemanticContractRef(cast(str, v["key"]), cast(str, v["version"]), ContentDigest.of_wire(v["schema_digest"]))


def _read_coordinate(value: object) -> SemanticValueCoordinate:
    v = _keys(value, {"role", "contract", "value_ref", "digest", "size_bytes"})
    for key in ("role", "value_ref"):
        _text(cast(str, v[key]))
    return SemanticValueCoordinate(cast(str, v["role"]), _read_ref(v["contract"]),
        cast(str, v["value_ref"]), ContentDigest.of_wire(v["digest"]), cast(int, v["size_bytes"]))


def _read_source(value: object) -> SemanticInputSourceCoordinate:
    v = _keys(value, {"relative_path", "coordinate"})
    # Constructors validate their own shape. The completed origin constructor
    # performs the stricter closed origin checks over every row before return.
    return SemanticInputSourceCoordinate(cast(str, v["relative_path"]), _read_coordinate(v["coordinate"]))


def decode_source_origin(body: bytes) -> SemanticInputSourceOrigin:
    if type(body) is not bytes or len(body) > MAX_SOURCE_ORIGIN_BYTES:
        raise ContractViolation("origin body must be bounded exact bytes")
    try:
        v = _keys(json.loads(body.decode("utf-8"), object_pairs_hook=_pairs), {
            "contract", "package", "source_identity_digest", "selection_coordinate",
            "selection_input_digest", "occurrence", "outer_package_root", "outer_manifest", "sources",
        })
        if v["contract"] != SOURCE_ORIGIN:
            raise ContractViolation("origin contract differs")
        p = _keys(v["package"], {"package_ref", "package_kind", "manifest_digest"})
        for key in ("package_ref", "package_kind"):
            _text(cast(str, p[key]))
        o = _keys(v["occurrence"], {"repository_binding_ref", "scope_key", "module_id",
                                 "package_id", "package_root", "outer_manifest_path"})
        if type(v["sources"]) is not list or len(v["sources"]) > MAX_CANDIDATES:
            raise ContractViolation("origin row count exceeds bound")
        rows = []
        for item in cast(list[object], v["sources"]):
            row = _keys(item, {"source", "occurrence_ref"})
            rows.append(SemanticInputSourceOccurrence(_read_source(row["source"]), cast(str, row["occurrence_ref"])))
        result = SemanticInputSourceOrigin(
            SemanticPackageCoordinate(cast(str, p["package_ref"]), cast(str, p["package_kind"]), ContentDigest.of_wire(p["manifest_digest"])),
            ContentDigest.of_wire(v["source_identity_digest"]), _read_coordinate(v["selection_coordinate"]),
            ContentDigest.of_wire(v["selection_input_digest"]),
            SemanticInputPackageOccurrence(*(cast(str, o[k]) for k in (
                "repository_binding_ref", "scope_key", "module_id", "package_id", "package_root", "outer_manifest_path"))),
            cast(str, v["outer_package_root"]), _read_source(v["outer_manifest"]), tuple(rows),
        )
        # Constructor just validated this exact freshly built graph. No owner
        # callback or await separates validation and canonical wire comparison.
        if _canonical_wire(result._project_wire()) != body:
            raise ContractViolation("origin body is not canonical")
        return result
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ContractViolation("invalid source origin JSON") from exc


def validate_source_origin_selection(value: SemanticInputSourceOrigin, *,
    selection: SemanticSourceSelection, selection_coordinate: SemanticValueCoordinate,
    source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
) -> None:
    """Portable complete correspondence only; callers still require original admission."""
    if type(value) is not SemanticInputSourceOrigin:
        raise ContractViolation("exact source origin required")
    value.__post_init__()
    if type(selection) is not SemanticSourceSelection:
        raise ContractViolation("exact source selection required")
    selected_body = encode_source_selection(selection)
    _coordinate(selection_coordinate)
    _validate_source_origin_correspondence(
        value, selection, selection_coordinate, selected_body, source_coordinates,
    )


def decode_source_origin_selection(
    body: bytes, *, selection_body: bytes,
    source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
) -> SemanticInputSourceOrigin:
    """Decode both canonical bodies and check complete correspondence once.

    Each existing decoder freshly validates its complete closed value. Only
    pure synchronous correspondence follows; there is no callback, await or
    retained validation state. This does not authenticate a source admission.
    Borrowed values still use the independently validating public checker.
    """
    value = decode_source_origin(body)
    selection = decode_source_selection(selection_body)
    _validate_source_origin_correspondence(
        value, selection, value.selection_coordinate, selection_body, source_coordinates,
    )
    return value


def _validate_source_origin_correspondence(
    value: SemanticInputSourceOrigin, selection: SemanticSourceSelection,
    selection_coordinate: SemanticValueCoordinate, selected_body: bytes,
    source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
) -> None:
    # Private continuation of validation in the same synchronous call only.
    # All three values have been completely validated by their caller above.
    if (value.selection_coordinate != selection_coordinate
            or selection_coordinate.contract != SOURCE_SELECTION_REF
            or selection_coordinate.digest != ContentDigest.of_bytes(selected_body)
            or selection_coordinate.size_bytes != len(selected_body)
            or value.package != selection.package
            or value.source_identity_digest != selection.source_identity_digest
            or value.selection_input_digest != selection.production_input_digest):
        raise ContractViolation("origin selection correspondence differs")
    if (type(source_coordinates) is not tuple
            or len(source_coordinates) != len(value.sources)
            or len(selection.sources) != len(value.sources)):
        raise ContractViolation("origin complete source set differs")
    for row, requested, admitted in zip(value.sources, selection.sources, source_coordinates, strict=True):
        _source(admitted)
        if (row.source != admitted or requested.relative_path != admitted.relative_path
                or requested.role != admitted.coordinate.role
                or requested.contract != admitted.coordinate.contract
                or requested.content_digest != admitted.coordinate.digest):
            raise ContractViolation("origin source correspondence differs")


def source_origin_body(value: SemanticInputSourceOrigin, *, role: str) -> SemanticBody:
    _text(role)
    body = encode_source_origin(value)
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(SemanticValueCoordinate(role, SOURCE_ORIGIN_REF,
        "source-origin:" + digest.value, digest, len(body)), body)


class SemanticInputSourceOriginCodec:
    contract = SOURCE_ORIGIN_REF
    implementation = SOURCE_ORIGIN_CODEC_IMPLEMENTATION

    def encode(self, value: object) -> bytes:
        if type(value) is not SemanticInputSourceOrigin:
            raise ContractViolation("exact source origin required")
        return encode_source_origin(value)

    def decode(self, body: bytes) -> SemanticInputSourceOrigin:
        return decode_source_origin(body)


__all__ = ["SemanticInputPackageOccurrence", "SemanticInputSourceOccurrence",
           "SemanticInputSourceOrigin", "SemanticInputSourceOriginCodec",
           "SOURCE_ORIGIN_DESCRIPTOR", "SOURCE_ORIGIN_REF", "SOURCE_ORIGIN_CODEC_IMPLEMENTATION",
           "source_occurrence_ref", "encode_source_origin", "decode_source_origin",
           "validate_source_origin_selection", "source_origin_body"]
