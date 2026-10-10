"""Exact public values for Specification filesystem adaptation."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import cast

from aware_specification_fs_source_contract import SpecificationFsSourceClosure
from aware_specification_runtime import SpecificationSnapshot

ONTOLOGY_PACKAGE_REF = "specification-ontology"
ONTOLOGY_PACKAGE_DIGEST = (
    "sha256:66ee97811891c037eefecab9f659bfc9d7d90108ca9e72a8bb8f3889c4167ade"
)
SEMANTIC_PROFILE_REF = "aware_specification.projection.Specification.home"
SEMANTIC_PROFILE_DIGEST = (
    "sha256:0e570389168a42161345092812c0c7d8771baa3ec3e17b9283c6392546c1beb7"
)
NEUTRAL_EVIDENCE_REF = (
    "workspaces/aware_kernel/modules/specification/docs/specs/"
    "kernel-specification-core/phases/02-neutral-semantic-acceptance/"
    "neutral-evidence-pfs-02.md"
)
NEUTRAL_EVIDENCE_DIGEST = (
    "sha256:fb47fa97c6f36a4134995b0af3ef4008f061b780165e473960cd65e5053401f1"
)
SEMANTIC_RESOLUTION_DIGEST = (
    "sha256:1cf02d11891bf7447e97db5732432048fddf345a47792fe7b1b2a1831537840a"
)
MANIFEST_SCHEMA_REF = "urn:aware:schema:specification:filesystem-manifest:v1"
MANIFEST_SCHEMA_DIGEST = (
    "sha256:142acd207dd179cbcd7e397f39802d6b2d919ac70c4354319d9d73e9a6d493d3"
)
PARSER_IMPLEMENTATION_REF = "aware.specification.fs-adapter.v1"

_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(contract: str, payload: object) -> str:
    body = canonical_json_bytes({"contract": contract, "payload": payload})
    return f"sha256:{sha256(body).hexdigest()}"


def _exact_text(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exact text")
    return value


def _sha256(value: object, name: str) -> str:
    result = _exact_text(value, name)
    if _SHA256_RE.fullmatch(result) is None:
        raise ValueError(f"{name} must be lowercase SHA-256")
    return result


def _relative_path(value: object, name: str) -> str:
    result = _exact_text(value, name)
    try:
        encoded = result.encode("utf-8", "strict")
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} must be strict UTF-8") from error
    parts = result.split("/")
    if (
        not encoded
        or len(encoded) > 1024
        or not unicodedata.is_normalized("NFC", result)
        or result.startswith("/")
        or result.endswith("/")
        or "\\" in result
        or any(part in {"", ".", ".."} for part in parts)
        or any(
            ord(character) <= 0x1F
            or 0x7F <= ord(character) <= 0x9F
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in result
        )
    ):
        raise ValueError(f"{name} must be a canonical relative path")
    return result


class SpecificationFsAdapterErrorKind(StrEnum):
    INPUT = "input"
    PLATFORM = "platform"
    SOURCE = "source"
    PROFILE = "profile"
    SEMANTIC = "semantic"
    CAPACITY = "capacity"
    LIFECYCLE = "lifecycle"
    INTEGRITY = "integrity"


class SpecificationFsAdapterError(Exception):
    """Closed public failure for every adapter entrance."""

    __slots__ = ("code", "kind", "profile_outcome", "spec_root")

    def __init__(
        self,
        kind: SpecificationFsAdapterErrorKind,
        code: str,
        *,
        spec_root: str | None = None,
        profile_outcome: SpecificationFsProfileOutcome | None = None,
    ) -> None:
        if type(kind) is not SpecificationFsAdapterErrorKind or type(code) is not str:
            raise TypeError("adapter error identity must be exact")
        allowed = _ERROR_CODES.get(kind)
        if allowed is None or code not in allowed:
            raise TypeError("adapter error kind/code is invalid")
        if spec_root is not None and type(spec_root) is not str:
            raise TypeError("adapter error spec_root must be exact text or None")
        if (
            profile_outcome is not None
            and type(profile_outcome) is not SpecificationFsProfileOutcome
        ):
            raise TypeError("adapter error outcome must be exact or None")
        if code == "source_observation_failed":
            if spec_root is None or profile_outcome is not None:
                raise TypeError("source observation error fields are invalid")
        elif code == "noncanonical_specification_profile":
            if spec_root is None or profile_outcome is None:
                raise TypeError("profile error fields are invalid")
        elif spec_root is not None or profile_outcome is not None:
            raise TypeError("adapter error fields are invalid")
        self.kind = kind
        self.code = code
        self.spec_root = spec_root
        self.profile_outcome = profile_outcome
        super().__init__(code)


class SpecificationFsObservationGrade(StrEnum):
    LOCAL_STRUCTURAL_OBSERVATION = "local_structural_observation"


class SpecificationFsProfileOutcomeKind(StrEnum):
    CANONICAL_V1 = "canonical_v1"
    LEGACY_SUPPORTED_STRUCTURE = "legacy_supported_structure"
    LEGACY_NONCANONICAL_STRUCTURE = "legacy_noncanonical_structure"
    MALFORMED_V1 = "malformed_v1"
    FOREIGN_PROFILE = "foreign_profile"


_OUTCOME_CODES = {
    SpecificationFsProfileOutcomeKind.CANONICAL_V1: "canonical",
    SpecificationFsProfileOutcomeKind.LEGACY_SUPPORTED_STRUCTURE: "profile_upgrade_required",
    SpecificationFsProfileOutcomeKind.LEGACY_NONCANONICAL_STRUCTURE: "legacy_layout_unsupported",
    SpecificationFsProfileOutcomeKind.MALFORMED_V1: "malformed_specification_fs_v1",
    SpecificationFsProfileOutcomeKind.FOREIGN_PROFILE: "unsupported_specification_profile",
}


@dataclass(frozen=True, slots=True)
class SpecificationFsProfileOutcome:
    spec_root: str
    kind: SpecificationFsProfileOutcomeKind
    diagnostic_code: str
    outcome_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsProfileOutcome:
            raise ValueError("profile outcome type must be exact")
        if (
            type(self.spec_root) is not str
            or type(self.kind) is not SpecificationFsProfileOutcomeKind
        ):
            raise ValueError("profile outcome fields must be exact")
        _relative_path(self.spec_root, "spec_root")
        if (
            type(self.diagnostic_code) is not str
            or self.diagnostic_code != _OUTCOME_CODES[self.kind]
        ):
            raise ValueError("profile outcome diagnostic is invalid")
        expected = digest(
            "aware.specification.fs-profile-outcome.v1",
            {
                "diagnostic_code": self.diagnostic_code,
                "kind": self.kind.value,
                "spec_root": self.spec_root,
            },
        )
        retained = getattr(self, "outcome_digest", expected)
        if type(retained) is not str or retained != expected:
            raise ValueError("profile outcome digest is invalid")
        object.__setattr__(self, "outcome_digest", expected)


def _implementation_digest() -> str:
    return digest(
        "aware.specification.fs-adapter-implementation.v1",
        {
            "implementation_ref": PARSER_IMPLEMENTATION_REF,
            "implementation_version": 1,
            "manifest_schema_digest": MANIFEST_SCHEMA_DIGEST,
            "semantic_resolution_digest": SEMANTIC_RESOLUTION_DIGEST,
        },
    )


@dataclass(frozen=True, slots=True)
class SpecificationFsSchemaResolutionContext:
    ontology_package_ref: str = ONTOLOGY_PACKAGE_REF
    ontology_package_digest: str = ONTOLOGY_PACKAGE_DIGEST
    semantic_profile_ref: str = SEMANTIC_PROFILE_REF
    semantic_profile_digest: str = SEMANTIC_PROFILE_DIGEST
    neutral_evidence_ref: str = NEUTRAL_EVIDENCE_REF
    neutral_evidence_digest: str = NEUTRAL_EVIDENCE_DIGEST
    semantic_resolution_digest: str = SEMANTIC_RESOLUTION_DIGEST
    manifest_schema_ref: str = MANIFEST_SCHEMA_REF
    manifest_schema_digest: str = MANIFEST_SCHEMA_DIGEST
    parser_implementation_ref: str = PARSER_IMPLEMENTATION_REF
    parser_implementation_digest: str = field(init=False)
    context_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsSchemaResolutionContext:
            raise ValueError("schema context type must be exact")
        expected_literals = (
            (self.ontology_package_ref, ONTOLOGY_PACKAGE_REF),
            (self.ontology_package_digest, ONTOLOGY_PACKAGE_DIGEST),
            (self.semantic_profile_ref, SEMANTIC_PROFILE_REF),
            (self.semantic_profile_digest, SEMANTIC_PROFILE_DIGEST),
            (self.neutral_evidence_ref, NEUTRAL_EVIDENCE_REF),
            (self.neutral_evidence_digest, NEUTRAL_EVIDENCE_DIGEST),
            (self.semantic_resolution_digest, SEMANTIC_RESOLUTION_DIGEST),
            (self.manifest_schema_ref, MANIFEST_SCHEMA_REF),
            (self.manifest_schema_digest, MANIFEST_SCHEMA_DIGEST),
            (self.parser_implementation_ref, PARSER_IMPLEMENTATION_REF),
        )
        if any(
            type(value) is not str or value != expected
            for value, expected in expected_literals
        ):
            raise ValueError("schema context literals are invalid")
        implementation_digest = _implementation_digest()
        preimage = {
            "manifest_schema_digest": self.manifest_schema_digest,
            "manifest_schema_ref": self.manifest_schema_ref,
            "neutral_evidence_digest": self.neutral_evidence_digest,
            "neutral_evidence_ref": self.neutral_evidence_ref,
            "ontology_package_digest": self.ontology_package_digest,
            "ontology_package_ref": self.ontology_package_ref,
            "parser_implementation_digest": implementation_digest,
            "parser_implementation_ref": self.parser_implementation_ref,
            "semantic_profile_digest": self.semantic_profile_digest,
            "semantic_profile_ref": self.semantic_profile_ref,
            "semantic_resolution_digest": self.semantic_resolution_digest,
        }
        context_digest = digest(
            "aware.specification.fs-schema-resolution-context.v1", preimage
        )
        for name, expected in (
            ("parser_implementation_digest", implementation_digest),
            ("context_digest", context_digest),
        ):
            retained = getattr(self, name, expected)
            if type(retained) is not str or retained != expected:
                raise ValueError(f"{name} is invalid")
            object.__setattr__(self, name, expected)


@dataclass(frozen=True, slots=True)
class SpecificationFsLoweringResult:
    closures: tuple[SpecificationFsSourceClosure, ...]
    schema_context: SpecificationFsSchemaResolutionContext
    root_set_digest: str
    snapshot: SpecificationSnapshot
    lowering_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsLoweringResult:
            raise ValueError("lowering result type must be exact")
        if type(self.closures) is not tuple or not self.closures:
            raise ValueError("closures must be a nonempty exact tuple")
        if any(
            type(item) is not SpecificationFsSourceClosure for item in self.closures
        ):
            raise ValueError("closure types must be exact")
        if type(self.schema_context) is not SpecificationFsSchemaResolutionContext:
            raise ValueError("schema context type must be exact")
        if (
            type(self.root_set_digest) is not str
            or _SHA256_RE.fullmatch(self.root_set_digest) is None
        ):
            raise ValueError("root set digest is invalid")
        if type(self.snapshot) is not SpecificationSnapshot:
            raise ValueError("snapshot type must be exact")
        payload = {
            "closure_members": [
                {
                    "closure_coordinate": [
                        "specification_fs_source",
                        closure.profile.profile_ref,
                        closure.spec_root,
                    ],
                    "closure_digest": closure.closure_digest,
                }
                for closure in self.closures
            ],
            "root_set_digest": self.root_set_digest,
            "schema_context_digest": self.schema_context.context_digest,
            "snapshot_digest": self.snapshot.snapshot_digest,
        }
        expected = digest("aware.specification.fs-lowering-result.v1", payload)
        retained = getattr(self, "lowering_digest", expected)
        if type(retained) is not str or retained != expected:
            raise ValueError("lowering digest is invalid")
        object.__setattr__(self, "lowering_digest", expected)


@dataclass(frozen=True, slots=True)
class SpecificationFsAdaptationResult:
    outcomes: tuple[SpecificationFsProfileOutcome, ...]
    lowering: SpecificationFsLoweringResult
    observation_grade: SpecificationFsObservationGrade
    adaptation_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationFsAdaptationResult:
            raise ValueError("adaptation result type must be exact")
        if type(self.outcomes) is not tuple or not self.outcomes:
            raise ValueError("outcomes must be a nonempty exact tuple")
        if any(
            type(value) is not SpecificationFsProfileOutcome for value in self.outcomes
        ):
            raise ValueError("outcome types must be exact")
        if any(
            value.kind is not SpecificationFsProfileOutcomeKind.CANONICAL_V1
            for value in self.outcomes
        ):
            raise ValueError("adaptation outcomes must all be canonical")
        if type(self.lowering) is not SpecificationFsLoweringResult:
            raise ValueError("lowering must be exact")
        if type(self.observation_grade) is not SpecificationFsObservationGrade:
            raise ValueError("observation grade must be exact")
        if tuple(value.spec_root for value in self.outcomes) != tuple(
            closure.spec_root for closure in self.lowering.closures
        ):
            raise ValueError("outcomes and closures do not align")
        expected = digest(
            "aware.specification.fs-adaptation-result.v1",
            {
                "outcome_digests": [value.outcome_digest for value in self.outcomes],
                "lowering_digest": self.lowering.lowering_digest,
                "observation_grade": self.observation_grade.value,
            },
        )
        retained = getattr(self, "adaptation_digest", expected)
        if type(retained) is not str or retained != expected:
            raise ValueError("adaptation digest is invalid")
        object.__setattr__(self, "adaptation_digest", expected)


def validate_context(value: object) -> SpecificationFsSchemaResolutionContext:
    if type(value) is not SpecificationFsSchemaResolutionContext:
        raise ValueError("schema context type must be exact")
    result = cast(SpecificationFsSchemaResolutionContext, value)
    result.__post_init__()
    return result


def validate_adaptation_result(value: object) -> SpecificationFsAdaptationResult:
    if type(value) is not SpecificationFsAdaptationResult:
        raise ValueError("adaptation result type must be exact")
    result = cast(SpecificationFsAdaptationResult, value)
    if type(result.outcomes) is not tuple or any(
        type(outcome) is not SpecificationFsProfileOutcome
        for outcome in result.outcomes
    ):
        raise ValueError("adaptation outcome closure must be exact")
    if type(result.lowering) is not SpecificationFsLoweringResult:
        raise ValueError("adaptation lowering must be exact")
    for outcome in result.outcomes:
        outcome.__post_init__()
    lowering = result.lowering
    if type(lowering.closures) is not tuple or any(
        type(closure) is not SpecificationFsSourceClosure
        for closure in lowering.closures
    ):
        raise ValueError("lowering closure must be exact")
    if type(lowering.schema_context) is not SpecificationFsSchemaResolutionContext:
        raise ValueError("lowering context must be exact")
    if type(lowering.snapshot) is not SpecificationSnapshot:
        raise ValueError("lowering snapshot must be exact")
    for closure in lowering.closures:
        closure.__post_init__()
    lowering.schema_context.__post_init__()
    lowering.snapshot.__post_init__()
    lowering.__post_init__()
    result.__post_init__()
    return result


_ERROR_CODES = {
    SpecificationFsAdapterErrorKind.INPUT: frozenset(
        {
            "invalid_installation_input",
            "invalid_inspection_request",
            "invalid_adaptation_request",
            "invalid_adaptation_result",
            "invalid_close_request",
            "invalid_lowering_input",
        }
    ),
    SpecificationFsAdapterErrorKind.PLATFORM: frozenset(
        {"platform_observation_unsupported"}
    ),
    SpecificationFsAdapterErrorKind.SOURCE: frozenset(
        {"source_base_invalid", "source_observation_failed"}
    ),
    SpecificationFsAdapterErrorKind.PROFILE: frozenset(
        {"noncanonical_specification_profile"}
    ),
    SpecificationFsAdapterErrorKind.SEMANTIC: frozenset(
        {"specification_semantic_lowering_failed"}
    ),
    SpecificationFsAdapterErrorKind.CAPACITY: frozenset(
        {"adaptation_capacity_exhausted"}
    ),
    SpecificationFsAdapterErrorKind.LIFECYCLE: frozenset(
        {"specification_fs_adapter_closed"}
    ),
    SpecificationFsAdapterErrorKind.INTEGRITY: frozenset(
        {
            "specification_fs_adaptation_invalid",
            "specification_fs_adapter_internal_failure",
        }
    ),
}
