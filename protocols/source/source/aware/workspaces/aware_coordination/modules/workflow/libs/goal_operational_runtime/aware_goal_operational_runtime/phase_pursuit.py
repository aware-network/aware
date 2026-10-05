"""Runtime-neutral pursuit and observation for native Goal Lane Phases."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import cast

from .phase_document import (
    GoalLanePhaseDefinitionV1,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    encode_goal_phase_native_document,
)
from .phase_contracts import GoalPhaseCoordinate

GOAL_PHASE_PURSUIT_SCHEMA = "aware.goal.phase-pursuit.v1"
GOAL_PHASE_PURSUIT_CURRENTNESS_SCHEMA = "aware.goal.phase-pursuit-currentness.v1"
GOAL_PHASE_NATIVE_OBSERVATION_SCHEMA = "aware.goal.phase-native-observation.v1"
GOAL_PHASE_REVISION_LINEAGE_SCHEMA = "aware.goal.phase-revision-lineage.v1"
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^(?:git:|repository-commit:)?[0-9a-f]{40}$")
_BLOB = re.compile(r"^(?:git-blob:)?(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class GoalPhasePursuitError(ValueError):
    """A Phase pursuit or observation is invalid or noncanonical."""


@dataclass(frozen=True, slots=True)
class GoalPhaseSourceBindingV1:
    repository_revision_ref: str
    goal_sha256: str
    goal_blob_oid: str

    def __post_init__(self) -> None:
        if not _COMMIT.fullmatch(self.repository_revision_ref):
            raise GoalPhasePursuitError("repository_revision_ref is not a commit")
        if not _SHA.fullmatch(self.goal_sha256):
            raise GoalPhasePursuitError("goal_sha256 must be qualified SHA-256")
        if not _BLOB.fullmatch(self.goal_blob_oid):
            raise GoalPhasePursuitError("goal_blob_oid is not a Git blob identity")

    def to_wire(self) -> dict[str, object]:
        return {
            "repository_revision_ref": self.repository_revision_ref,
            "goal_sha256": self.goal_sha256,
            "goal_blob_oid": self.goal_blob_oid,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseRevisionLineageV1:
    expected_revision_ref: str
    observed_revision_ref: str
    relation: str
    lineage_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_REVISION_LINEAGE_SCHEMA
    authority_profile: str = "repository_revision_lineage_v1"

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_REVISION_LINEAGE_SCHEMA:
            raise GoalPhasePursuitError("unsupported revision-lineage schema")
        if self.authority_profile != "repository_revision_lineage_v1":
            raise GoalPhasePursuitError("unsupported revision-lineage authority")
        if not _COMMIT.fullmatch(self.expected_revision_ref):
            raise GoalPhasePursuitError("expected lineage revision is invalid")
        if not _COMMIT.fullmatch(self.observed_revision_ref):
            raise GoalPhasePursuitError("observed lineage revision is invalid")
        if self.relation not in {"equal", "descendant", "unproven"}:
            raise GoalPhasePursuitError("unsupported revision-lineage relation")
        revisions_equal = self.expected_revision_ref == self.observed_revision_ref
        if revisions_equal != (self.relation == "equal"):
            raise GoalPhasePursuitError("revision-lineage relation contradicts coordinates")
        object.__setattr__(
            self,
            "lineage_ref",
            "goal-phase-revision-lineage:" + _digest(_lineage_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_lineage_body(self), "lineage_ref": self.lineage_ref}


@dataclass(frozen=True, slots=True)
class GoalPhasePursuitReceiptV1:
    coordinate: GoalPhaseCoordinate
    ordinal: int
    definition_ref: str
    gate_digest: str
    document_ref: str
    compatibility_profile: str
    source: GoalPhaseSourceBindingV1
    pursuit_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_PURSUIT_SCHEMA
    effect_profile: str = "direction_only_non_authorizing"

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_PURSUIT_SCHEMA:
            raise GoalPhasePursuitError("unsupported pursuit schema")
        if self.effect_profile != "direction_only_non_authorizing":
            raise GoalPhasePursuitError("unsupported pursuit effect profile")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        if type(self.ordinal) is not int or self.ordinal < 1:
            raise GoalPhasePursuitError("ordinal must be positive integer")
        _qualified(self.definition_ref, "goal-phase-definition", "definition_ref")
        _qualified(self.document_ref, "goal-phase-document", "document_ref")
        if not _SHA.fullmatch(self.gate_digest):
            raise GoalPhasePursuitError("gate_digest must be qualified SHA-256")
        _ = _text(self.compatibility_profile, "compatibility_profile")
        if type(self.source) is not GoalPhaseSourceBindingV1:
            raise TypeError("source must be GoalPhaseSourceBindingV1")
        self.source.__post_init__()
        object.__setattr__(
            self,
            "pursuit_ref",
            "goal-phase-pursuit:" + _digest(_pursuit_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_pursuit_body(self), "pursuit_ref": self.pursuit_ref}


@dataclass(frozen=True, slots=True)
class GoalPhasePursuitCurrentnessV1:
    expected_pursuit_ref: str
    observed_pursuit_ref: str | None
    status: str
    projection_currentness: str
    replay_disposition: str
    reasons: tuple[str, ...]
    expected_document_ref: str
    observed_document_ref: str
    expected_source_revision_ref: str
    observed_source_revision_ref: str
    source_revision_lineage: str
    source_revision_lineage_ref: str
    currentness_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_PURSUIT_CURRENTNESS_SCHEMA
    effect_profile: str = "read_only_non_authorizing"

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_PURSUIT_CURRENTNESS_SCHEMA:
            raise GoalPhasePursuitError("unsupported currentness schema")
        if self.effect_profile != "read_only_non_authorizing":
            raise GoalPhasePursuitError("unsupported currentness effect profile")
        _qualified(self.expected_pursuit_ref, "goal-phase-pursuit", "expected_pursuit_ref")
        if self.observed_pursuit_ref is not None:
            _qualified(self.observed_pursuit_ref, "goal-phase-pursuit", "observed_pursuit_ref")
        if self.status not in {"current", "stale", "ambiguous"}:
            raise GoalPhasePursuitError("unsupported currentness status")
        if self.projection_currentness not in {"current", "advanced", "unproven"}:
            raise GoalPhasePursuitError("unsupported projection currentness")
        if self.replay_disposition not in {
            "exact",
            "reobserved_unchanged",
            "refuse",
        }:
            raise GoalPhasePursuitError("unsupported replay disposition")
        if type(self.reasons) is not tuple or any(not item for item in self.reasons):
            raise GoalPhasePursuitError("reasons must be exact non-empty tokens")
        if (self.status == "current") != (not self.reasons):
            raise GoalPhasePursuitError("currentness status and reasons disagree")
        expected_replay = (
            "refuse"
            if self.status != "current"
            else (
                "reobserved_unchanged"
                if self.projection_currentness == "advanced"
                else "exact"
            )
        )
        if self.replay_disposition != expected_replay:
            raise GoalPhasePursuitError(
                "currentness and replay disposition disagree"
            )
        _qualified(self.expected_document_ref, "goal-phase-document", "expected_document_ref")
        _qualified(self.observed_document_ref, "goal-phase-document", "observed_document_ref")
        if not _COMMIT.fullmatch(self.expected_source_revision_ref):
            raise GoalPhasePursuitError("expected source revision is invalid")
        if not _COMMIT.fullmatch(self.observed_source_revision_ref):
            raise GoalPhasePursuitError("observed source revision is invalid")
        if self.source_revision_lineage not in {"equal", "descendant", "unproven"}:
            raise GoalPhasePursuitError("unsupported source revision lineage")
        expected_lineage = GoalPhaseRevisionLineageV1(
            expected_revision_ref=self.expected_source_revision_ref,
            observed_revision_ref=self.observed_source_revision_ref,
            relation=self.source_revision_lineage,
        )
        if self.source_revision_lineage_ref != expected_lineage.lineage_ref:
            raise GoalPhasePursuitError("source revision lineage reference is not canonical")
        expected_projection = {
            "equal": "current",
            "descendant": "advanced",
            "unproven": "unproven",
        }[self.source_revision_lineage]
        if self.projection_currentness != expected_projection:
            raise GoalPhasePursuitError("projection currentness contradicts revision lineage")
        object.__setattr__(
            self,
            "currentness_ref",
            "goal-phase-pursuit-currentness:" + _digest(_currentness_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_currentness_body(self), "currentness_ref": self.currentness_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeObservationV1:
    document: NativePhaseDocument
    source: GoalPhaseSourceBindingV1
    observation_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_OBSERVATION_SCHEMA
    authority_profile: str = "native_phase_document_observation_v1"
    effect_profile: str = "read_only_non_authorizing"

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_OBSERVATION_SCHEMA:
            raise GoalPhasePursuitError("unsupported observation schema")
        if self.authority_profile != "native_phase_document_observation_v1":
            raise GoalPhasePursuitError("unsupported observation authority profile")
        if self.effect_profile != "read_only_non_authorizing":
            raise GoalPhasePursuitError("unsupported observation effect profile")
        if type(self.document) not in {GoalPhaseNativeDocumentV1, GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
            raise TypeError("document must be a supported native Phase document")
        self.document.__post_init__()
        if type(self.source) is not GoalPhaseSourceBindingV1:
            raise TypeError("source must be GoalPhaseSourceBindingV1")
        self.source.__post_init__()
        object.__setattr__(
            self,
            "observation_ref",
            "goal-phase-native-observation:" + _digest(_observation_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_observation_body(self), "observation_ref": self.observation_ref}


def issue_goal_phase_pursuit(
    *,
    document: NativePhaseDocument,
    coordinate: GoalPhaseCoordinate,
    source: GoalPhaseSourceBindingV1,
    expected_document_ref: str,
) -> GoalPhasePursuitReceiptV1:
    """Issue direction evidence for one exact admitted native Phase."""

    document.__post_init__()
    if document.document_ref != expected_document_ref:
        raise GoalPhasePursuitError("native document differs from expected reference")
    definition = _definition(document, coordinate)
    return GoalPhasePursuitReceiptV1(
        coordinate=coordinate,
        ordinal=definition.ordinal,
        definition_ref=definition.definition_ref,
        gate_digest=definition.gate.gate_digest,
        document_ref=document.document_ref,
        compatibility_profile=document.compatibility_profile,
        source=source,
    )


def verify_goal_phase_pursuit_currentness(
    *,
    expected: GoalPhasePursuitReceiptV1,
    observed_document: NativePhaseDocument,
    observed_source: GoalPhaseSourceBindingV1,
    revision_lineage: GoalPhaseRevisionLineageV1,
) -> GoalPhasePursuitCurrentnessV1:
    """Compare retained Phase direction with one freshly supplied authority read."""

    expected.__post_init__()
    revision_lineage.__post_init__()
    if revision_lineage.expected_revision_ref != expected.source.repository_revision_ref:
        raise GoalPhasePursuitError("revision lineage differs from expected pursuit")
    if revision_lineage.observed_revision_ref != observed_source.repository_revision_ref:
        raise GoalPhasePursuitError("revision lineage differs from observed source")
    reasons: list[str] = []
    observed: GoalPhasePursuitReceiptV1 | None = None
    try:
        observed = issue_goal_phase_pursuit(
            document=observed_document,
            coordinate=expected.coordinate,
            source=observed_source,
            expected_document_ref=observed_document.document_ref,
        )
    except GoalPhasePursuitError:
        reasons.append("phase_unavailable")
    else:
        if observed.document_ref != expected.document_ref:
            reasons.append("document_advanced")
        if observed.definition_ref != expected.definition_ref:
            reasons.append("definition_changed")
        if observed.gate_digest != expected.gate_digest:
            reasons.append("gate_changed")
        if observed.compatibility_profile != expected.compatibility_profile:
            reasons.append("compatibility_profile_changed")
        if observed.source.goal_sha256 != expected.source.goal_sha256:
            reasons.append("goal_digest_changed")
        if observed.source.goal_blob_oid != expected.source.goal_blob_oid:
            reasons.append("goal_blob_changed")
    semantic_reasons = bool(reasons)
    if revision_lineage.relation == "unproven":
        reasons.append("source_revision_lineage_unproven")
    status = (
        "stale"
        if semantic_reasons
        else ("ambiguous" if revision_lineage.relation == "unproven" else "current")
    )
    projection_currentness = {
        "equal": "current",
        "descendant": "advanced",
        "unproven": "unproven",
    }[revision_lineage.relation]
    return GoalPhasePursuitCurrentnessV1(
        expected_pursuit_ref=expected.pursuit_ref,
        observed_pursuit_ref=None if observed is None else observed.pursuit_ref,
        status=status,
        projection_currentness=projection_currentness,
        replay_disposition=(
            "refuse" if status != "current" else (
                "reobserved_unchanged"
                if revision_lineage.relation == "descendant"
                else "exact"
            )
        ),
        reasons=tuple(dict.fromkeys(reasons)),
        expected_document_ref=expected.document_ref,
        observed_document_ref=observed_document.document_ref,
        expected_source_revision_ref=expected.source.repository_revision_ref,
        observed_source_revision_ref=observed_source.repository_revision_ref,
        source_revision_lineage=revision_lineage.relation,
        source_revision_lineage_ref=revision_lineage.lineage_ref,
    )


NativePhaseDocument = GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3


def observe_goal_phase_native_document(
    *, document: NativePhaseDocument, source: GoalPhaseSourceBindingV1
) -> GoalPhaseNativeObservationV1:
    """Carry the exact native graph without evaluating or authorizing it."""

    return GoalPhaseNativeObservationV1(document=document, source=source)


def encode_goal_phase_pursuit(value: GoalPhasePursuitReceiptV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_pursuit(
    payload: bytes,
    *,
    document: NativePhaseDocument,
    source: GoalPhaseSourceBindingV1,
) -> GoalPhasePursuitReceiptV1:
    raw = _json(payload, "pursuit")
    _keys(raw, set(_pursuit_keys()), "pursuit")
    coordinate = _coordinate(raw["coordinate"])
    value = issue_goal_phase_pursuit(
        document=document,
        coordinate=coordinate,
        source=source,
        expected_document_ref=_text(raw["document_ref"], "document_ref"),
    )
    if not _exact(value.to_wire(), raw):
        raise GoalPhasePursuitError("pursuit is not canonical")
    return value


def encode_goal_phase_pursuit_currentness(
    value: GoalPhasePursuitCurrentnessV1,
) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_pursuit_currentness(
    payload: bytes,
    *,
    expected: GoalPhasePursuitReceiptV1,
    observed_document: NativePhaseDocument,
    observed_source: GoalPhaseSourceBindingV1,
    revision_lineage: GoalPhaseRevisionLineageV1,
) -> GoalPhasePursuitCurrentnessV1:
    raw = _json(payload, "currentness")
    _keys(raw, set(_currentness_keys()), "currentness")
    value = verify_goal_phase_pursuit_currentness(
        expected=expected,
        observed_document=observed_document,
        observed_source=observed_source,
        revision_lineage=revision_lineage,
    )
    if not _exact(value.to_wire(), raw):
        raise GoalPhasePursuitError("currentness is not canonical")
    return value


def encode_goal_phase_native_observation(value: GoalPhaseNativeObservationV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_native_observation(
    payload: bytes,
    *,
    document: NativePhaseDocument,
    source: GoalPhaseSourceBindingV1,
) -> GoalPhaseNativeObservationV1:
    raw = _json(payload, "observation")
    _keys(raw, set(_observation_keys()), "observation")
    value = GoalPhaseNativeObservationV1(
        schema_id=_text(raw["schema_id"], "schema_id"),
        authority_profile=_text(raw["authority_profile"], "authority_profile"),
        effect_profile=_text(raw["effect_profile"], "effect_profile"),
        document=document,
        source=source,
    )
    if not _exact(value.to_wire(), raw):
        raise GoalPhasePursuitError("observation is not canonical")
    return value


def _definition(
    document: NativePhaseDocument, coordinate: GoalPhaseCoordinate
) -> GoalLanePhaseDefinitionV1:
    matches = tuple(item for item in document.definitions if item.coordinate == coordinate)
    if len(matches) != 1:
        raise GoalPhasePursuitError("Phase coordinate is not uniquely admitted")
    return matches[0]


def _pursuit_body(value: GoalPhasePursuitReceiptV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "effect_profile": value.effect_profile,
        "coordinate": _coordinate_wire(value.coordinate),
        "ordinal": value.ordinal,
        "definition_ref": value.definition_ref,
        "gate_digest": value.gate_digest,
        "document_ref": value.document_ref,
        "compatibility_profile": value.compatibility_profile,
        "source": value.source.to_wire(),
    }


def _currentness_body(value: GoalPhasePursuitCurrentnessV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "effect_profile": value.effect_profile,
        "expected_pursuit_ref": value.expected_pursuit_ref,
        "observed_pursuit_ref": value.observed_pursuit_ref,
        "status": value.status,
        "projection_currentness": value.projection_currentness,
        "replay_disposition": value.replay_disposition,
        "reasons": list(value.reasons),
        "expected_document_ref": value.expected_document_ref,
        "observed_document_ref": value.observed_document_ref,
        "expected_source_revision_ref": value.expected_source_revision_ref,
        "observed_source_revision_ref": value.observed_source_revision_ref,
        "source_revision_lineage": value.source_revision_lineage,
        "source_revision_lineage_ref": value.source_revision_lineage_ref,
    }


def _lineage_body(value: GoalPhaseRevisionLineageV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "authority_profile": value.authority_profile,
        "expected_revision_ref": value.expected_revision_ref,
        "observed_revision_ref": value.observed_revision_ref,
        "relation": value.relation,
    }


def _observation_body(value: GoalPhaseNativeObservationV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "authority_profile": value.authority_profile,
        "effect_profile": value.effect_profile,
        "document": cast(object, json.loads(encode_goal_phase_native_document(value.document))),
        "source": value.source.to_wire(),
    }


def _pursuit_keys() -> tuple[str, ...]:
    return (
        "schema_id", "effect_profile", "coordinate", "ordinal", "definition_ref",
        "gate_digest", "document_ref", "compatibility_profile", "source", "pursuit_ref",
    )


def _currentness_keys() -> tuple[str, ...]:
    return (
        "schema_id", "effect_profile", "expected_pursuit_ref", "observed_pursuit_ref",
        "status", "projection_currentness", "replay_disposition", "reasons",
        "expected_document_ref", "observed_document_ref",
        "expected_source_revision_ref", "observed_source_revision_ref",
        "source_revision_lineage", "source_revision_lineage_ref", "currentness_ref",
    )


def _observation_keys() -> tuple[str, ...]:
    return (
        "schema_id", "authority_profile", "effect_profile", "document", "source",
        "observation_ref",
    )


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, object]:
    return {"goal_tag": value.goal_tag, "lane_key": value.lane_key, "phase_key": value.phase_key}


def _coordinate(raw: object) -> GoalPhaseCoordinate:
    values = _mapping(raw, "coordinate")
    _keys(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        _text(values["goal_tag"], "goal_tag"),
        _text(values["lane_key"], "lane_key"),
        _text(values["phase_key"], "phase_key"),
    )


def _json(payload: bytes, name: str) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError(f"{name} payload must be exact bytes")
    try:
        raw = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhasePursuitError(f"{name} is not JSON") from error
    return _mapping(raw, name)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhasePursuitError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _mapping(value: object, name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise GoalPhasePursuitError(f"{name} must be object")
    return cast(dict[str, object], value)


def _keys(value: dict[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise GoalPhasePursuitError(f"{name} fields are not canonical")


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise GoalPhasePursuitError(f"{name} must be non-empty text")
    return value


def _qualified(value: str, domain: str, name: str) -> None:
    if not re.fullmatch(rf"{re.escape(domain)}:sha256:[0-9a-f]{{64}}", value):
        raise GoalPhasePursuitError(f"{name} is not qualified")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_map = cast(dict[object, object], left)
        right_map = cast(dict[object, object], right)
        return set(left_map) == set(right_map) and all(
            _exact(left_map[key], right_map[key]) for key in left_map
        )
    if type(left) is list:
        left_items = cast(list[object], left)
        right_items = cast(list[object], right)
        return len(left_items) == len(right_items) and all(
            _exact(a, b) for a, b in zip(left_items, right_items, strict=True)
        )
    return left == right


__all__ = [
    "GOAL_PHASE_NATIVE_OBSERVATION_SCHEMA",
    "GOAL_PHASE_PURSUIT_CURRENTNESS_SCHEMA",
    "GOAL_PHASE_PURSUIT_SCHEMA",
    "GOAL_PHASE_REVISION_LINEAGE_SCHEMA",
    "GoalPhaseNativeObservationV1",
    "GoalPhasePursuitCurrentnessV1",
    "GoalPhasePursuitError",
    "GoalPhasePursuitReceiptV1",
    "GoalPhaseRevisionLineageV1",
    "GoalPhaseSourceBindingV1",
    "decode_goal_phase_native_observation",
    "decode_goal_phase_pursuit",
    "decode_goal_phase_pursuit_currentness",
    "encode_goal_phase_native_observation",
    "encode_goal_phase_pursuit",
    "encode_goal_phase_pursuit_currentness",
    "issue_goal_phase_pursuit",
    "observe_goal_phase_native_document",
    "verify_goal_phase_pursuit_currentness",
]
