"""Portable pre-owner-filter candidates; no membership or currentness authority."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractInvocation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .runtime import SemanticBody

SEMANTIC_CANDIDATE_LISTING = "aware.code.semantic-candidate-listing.v1"
MAX_CANDIDATES = 16_384
MAX_CANDIDATE_BODY_BYTES = 8_388_608
MAX_CANDIDATE_PATH_BYTES = 4_096
MAX_CANDIDATE_COMPONENT_BYTES = 255
MAX_CANDIDATE_COMPONENTS = 128


def _path(value: str) -> bytes:
    if type(value) is not str:
        raise ContractViolation("candidate path must be an exact string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise ContractViolation("candidate path must be UTF-8") from exc
    parts = value.split("/")
    if (
        not 1 <= len(encoded) <= MAX_CANDIDATE_PATH_BYTES
        or unicodedata.normalize("NFC", value) != value
        or "\\" in value
        or "\x00" in value
        or len(parts) > MAX_CANDIDATE_COMPONENTS
        or any(
            not part.strip()
            or part in (".", "..")
            or len(part.encode("utf-8")) > MAX_CANDIDATE_COMPONENT_BYTES
            for part in parts
        )
    ):
        raise ContractViolation(
            "candidate path must be bounded canonical relative POSIX NFC"
        )
    return encoded


@dataclass(frozen=True, slots=True)
class CodeSemanticCandidate:
    relative_path: str
    content_digest: ContentDigest

    def __post_init__(self) -> None:
        _path(self.relative_path)
        if type(self.content_digest) is not ContentDigest:
            raise ContractViolation(
                "candidate content digest must be exact ContentDigest"
            )
        self.content_digest.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "relative_path": self.relative_path,
            "content_digest": self.content_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeSemanticCandidateListing:
    source_identity_digest: ContentDigest
    candidates: tuple[CodeSemanticCandidate, ...]

    def __post_init__(self) -> None:
        if type(self.source_identity_digest) is not ContentDigest:
            raise ContractViolation("source identity must be exact ContentDigest")
        self.source_identity_digest.__post_init__()
        if type(self.candidates) is not tuple or len(self.candidates) > MAX_CANDIDATES:
            raise ContractViolation(
                "candidate tuple exceeds count bound or is not exact tuple"
            )
        previous = b""
        for candidate in self.candidates:
            if type(candidate) is not CodeSemanticCandidate:
                raise ContractViolation("exact CodeSemanticCandidate required")
            candidate.__post_init__()
            path = _path(candidate.relative_path)
            if path <= previous:
                raise ContractViolation(
                    "candidate paths must be unique and UTF-8 ordered"
                )
            previous = path
        if len(canonical_json_bytes(self.to_wire())) > MAX_CANDIDATE_BODY_BYTES:
            raise ContractViolation("candidate listing exceeds canonical body bound")

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": SEMANTIC_CANDIDATE_LISTING,
            "source_identity_digest": self.source_identity_digest.to_wire(),
            "candidates": [candidate.to_wire() for candidate in self.candidates],
        }


def encode_semantic_candidate_listing(value: CodeSemanticCandidateListing) -> bytes:
    if type(value) is not CodeSemanticCandidateListing:
        raise ContractViolation("exact CodeSemanticCandidateListing required")
    value.__post_init__()
    return canonical_json_bytes(value.to_wire())


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate candidate JSON key")
        result[key] = value
    return result


def decode_semantic_candidate_listing(body: bytes) -> CodeSemanticCandidateListing:
    if type(body) is not bytes or len(body) > MAX_CANDIDATE_BODY_BYTES:
        raise ContractViolation("candidate body must be bounded exact bytes")
    try:
        raw = json.loads(body.decode("utf-8"), object_pairs_hook=_object)
    except (ValueError, UnicodeError) as exc:
        raise ContractViolation("invalid candidate JSON") from exc
    if type(raw) is not dict or set(raw) != {
        "contract",
        "source_identity_digest",
        "candidates",
    }:
        raise ContractViolation("candidate body fields differ")
    if raw["contract"] != SEMANTIC_CANDIDATE_LISTING:
        raise ContractViolation("candidate contract differs")
    rows = raw["candidates"]
    if type(rows) is not list or len(rows) > MAX_CANDIDATES:
        raise ContractViolation("candidate rows exceed bound or are not a list")
    candidates = []
    for row in rows:
        if type(row) is not dict or set(row) != {"relative_path", "content_digest"}:
            raise ContractViolation("candidate row fields differ")
        candidates.append(
            CodeSemanticCandidate(
                row["relative_path"], ContentDigest.of_wire(row["content_digest"])
            )
        )
    value = CodeSemanticCandidateListing(
        ContentDigest.of_wire(raw["source_identity_digest"]), tuple(candidates)
    )
    if encode_semantic_candidate_listing(value) != body:
        raise ContractViolation("candidate body is not canonical")
    return value


SEMANTIC_CANDIDATE_LISTING_REF = SemanticContractRef(
    SEMANTIC_CANDIDATE_LISTING,
    "1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": SEMANTIC_CANDIDATE_LISTING,
                "shape": "source_identity_digest/candidates[relative_path,content_digest]",
                "bounds": [
                    MAX_CANDIDATES,
                    MAX_CANDIDATE_BODY_BYTES,
                    MAX_CANDIDATE_PATH_BYTES,
                    MAX_CANDIDATE_COMPONENT_BYTES,
                    MAX_CANDIDATE_COMPONENTS,
                ],
                "paths": "NFC POSIX relative unique UTF-8 ordered; no normalization",
            }
        )
    ),
)
SEMANTIC_CANDIDATE_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.semantic-candidate-listing.codec.v1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": SEMANTIC_CANDIDATE_LISTING_REF.to_wire(),
                "validation": "strict canonical bounded portable candidates; no authority",
            }
        )
    ),
)


class SemanticCandidateListingCodec:
    contract = SEMANTIC_CANDIDATE_LISTING_REF
    implementation = SEMANTIC_CANDIDATE_CODEC_IMPLEMENTATION

    def encode(self, value: object) -> bytes:
        if type(value) is not CodeSemanticCandidateListing:
            raise ContractViolation("exact CodeSemanticCandidateListing required")
        return encode_semantic_candidate_listing(value)

    def decode(self, canonical_body: bytes) -> object:
        return decode_semantic_candidate_listing(canonical_body)

    def validate_invocation(
        self, value: object, invocation: SemanticContractInvocation
    ) -> None:
        self.encode(value)
        # Observation identity/completeness requires its issuer join, not this codec.


def semantic_candidate_listing_body(
    value: CodeSemanticCandidateListing,
) -> SemanticBody:
    body = encode_semantic_candidate_listing(value)
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(
        SemanticValueCoordinate(
            "candidate_listing",
            SEMANTIC_CANDIDATE_LISTING_REF,
            f"code-semantic-candidates:{digest.value}",
            digest,
            len(body),
        ),
        body,
    )
