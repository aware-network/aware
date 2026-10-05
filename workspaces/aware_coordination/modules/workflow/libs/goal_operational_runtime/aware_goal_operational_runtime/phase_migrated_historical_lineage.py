# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Structural V1 source scope for migrated historical implementation review.

These portable values are *not* authority. A repository/Issue provider must
derive the original path set and verify every committed binding before the
scope can participate in Gate evaluation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from .identity import fingerprint
from .phase_contracts import GoalPhaseCoordinate
from .phase_migrated_gate_evaluation import EvaluationResult, ReasonCode

SOURCE_SCOPE_SCHEMA = "aware.goal.migrated-phase-source-scope.v1"
LINEAGE_EVALUATION_SCHEMA = "aware.goal.migrated-phase-lineage-evaluation.v1"
LINEAGE_EVALUATOR_PROFILE = "aware.goal.migrated-phase-gate-evaluator/historical-lineage-v1"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class HistoricalLineageError(ValueError):
    """A historical-lineage value is not canonical."""


def _string(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise HistoricalLineageError(f"{name} must be exact canonical string")
    if any(char.isspace() for char in value) or "|" in value:
        raise HistoricalLineageError(f"{name} must be one token")
    return value


def _path(value: object, name: str) -> str:
    result = _string(value, name)
    parsed = PurePosixPath(result)
    if (
        parsed.is_absolute()
        or result.startswith("./")
        or "//" in result
        or any(part in {".", ".."} for part in result.split("/"))
        or str(parsed) != result
    ):
        raise HistoricalLineageError(f"{name} must be canonical relative path")
    return result


def _ordered_paths(values: object, name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise HistoricalLineageError(f"{name} must be exact tuple")
    paths = tuple(_path(value, name) for value in values)
    if paths != tuple(sorted(set(paths))):
        raise HistoricalLineageError(f"{name} must be sorted and unique")
    return paths


@dataclass(frozen=True, slots=True)
class HistoricalPathOidV1:
    path: str
    blob_oid: str | None

    def __post_init__(self) -> None:
        if type(self) is not HistoricalPathOidV1:
            raise HistoricalLineageError("path binding type must be exact")
        _path(self.path, "path")
        if self.blob_oid is not None and (
            type(self.blob_oid) is not str or not _OID.fullmatch(self.blob_oid)
        ):
            raise HistoricalLineageError("blob_oid must be exact Git identity or absent")

    def to_wire(self) -> dict[str, object]:
        return {"path": self.path, "blob_oid": self.blob_oid}


@dataclass(frozen=True, slots=True)
class HistoricalLineageEventV1:
    commit: str
    parent: str
    path: str
    before_blob_oid: str | None
    after_blob_oid: str | None
    role: str
    repository_commit_receipt_ref: str | None

    def __post_init__(self) -> None:
        if type(self) is not HistoricalLineageEventV1:
            raise HistoricalLineageError("lineage event type must be exact")
        for name in ("commit", "parent"):
            value = getattr(self, name)
            if type(value) is not str or not _OID.fullmatch(value):
                raise HistoricalLineageError(f"{name} must be exact Git identity")
        _path(self.path, "path")
        for name in ("before_blob_oid", "after_blob_oid"):
            value = getattr(self, name)
            if value is not None and (type(value) is not str or not _OID.fullmatch(value)):
                raise HistoricalLineageError(f"{name} must be Git identity or absent")
        if self.before_blob_oid is None and self.after_blob_oid is None:
            raise HistoricalLineageError("lineage event must change a path")
        if self.role not in {"issue_closeout", "source_evolution", "other_change"}:
            raise HistoricalLineageError("lineage event role is unsupported")
        if self.repository_commit_receipt_ref is not None and (
            self.repository_commit_receipt_ref != f"repository-commit:{self.commit}"
        ):
            raise HistoricalLineageError("event repository receipt differs")
        if (
            self.role in {"issue_closeout", "source_evolution"}
            and self.repository_commit_receipt_ref is None
        ):
            raise HistoricalLineageError("governed lineage event requires repository receipt")

    def to_wire(self) -> dict[str, object]:
        return {
            "commit": self.commit,
            "parent": self.parent,
            "path": self.path,
            "before_blob_oid": self.before_blob_oid,
            "after_blob_oid": self.after_blob_oid,
            "role": self.role,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
        }


def migrated_historical_lineage_ref(
    *, implementation_commit: str, reviewed_source_commit: str,
    events: tuple[HistoricalLineageEventV1, ...],
) -> str:
    """Canonical event identity; only the Git provider may assert completeness."""
    if type(implementation_commit) is not str or not _OID.fullmatch(implementation_commit):
        raise HistoricalLineageError("implementation_commit must be Git identity")
    if type(reviewed_source_commit) is not str or not _OID.fullmatch(reviewed_source_commit):
        raise HistoricalLineageError("reviewed_source_commit must be Git identity")
    if type(events) is not tuple or any(type(item) is not HistoricalLineageEventV1 for item in events):
        raise HistoricalLineageError("events must be exact tuple")
    return "goal-migrated-phase-lineage:" + fingerprint(
        {
            "implementation_commit": implementation_commit,
            "reviewed_source_commit": reviewed_source_commit,
            "events": [item.to_wire() for item in events],
        }
    )


@dataclass(frozen=True, slots=True)
class MigratedHistoricalSourceScopeV1:
    repository_ref: str
    goal_path: str
    coordinate: GoalPhaseCoordinate
    definition_ref: str
    gate_digest: str
    implementation_ref: str
    lineage_ref: str
    reviewed_source_commit: str
    original_paths: tuple[str, ...]
    additional_gate_paths: tuple[str, ...]
    path_oids: tuple[HistoricalPathOidV1, ...]
    source_scope_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not MigratedHistoricalSourceScopeV1:
            raise HistoricalLineageError("source scope type must be exact")
        _string(self.repository_ref, "repository_ref")
        _path(self.goal_path, "goal_path")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise HistoricalLineageError("coordinate type must be exact")
        self.coordinate.__post_init__()
        for name in ("definition_ref", "implementation_ref", "lineage_ref"):
            _string(getattr(self, name), name)
        if type(self.gate_digest) is not str or not _DIGEST.fullmatch(self.gate_digest):
            raise HistoricalLineageError("gate_digest must be sha256 identity")
        if (
            type(self.reviewed_source_commit) is not str
            or not _OID.fullmatch(self.reviewed_source_commit)
        ):
            raise HistoricalLineageError("reviewed_source_commit must be Git identity")
        original = _ordered_paths(self.original_paths, "original_paths")
        additional = _ordered_paths(self.additional_gate_paths, "additional_gate_paths")
        if not original or set(original) & set(additional):
            raise HistoricalLineageError("original paths must be nonempty and disjoint")
        if type(self.path_oids) is not tuple or any(
            type(item) is not HistoricalPathOidV1 for item in self.path_oids
        ):
            raise HistoricalLineageError("path_oids must be exact path bindings")
        for item in self.path_oids:
            item.__post_init__()
        observed_paths = tuple(item.path for item in self.path_oids)
        expected_paths = tuple(sorted((*original, *additional)))
        if observed_paths != expected_paths:
            raise HistoricalLineageError("path inventory must equal closed source union")
        object.__setattr__(
            self,
            "source_scope_ref",
            "goal-migrated-phase-source-scope:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "repository_ref": self.repository_ref,
            "goal_path": self.goal_path,
            "coordinate": {
                "goal_tag": self.coordinate.goal_tag,
                "lane_key": self.coordinate.lane_key,
                "phase_key": self.coordinate.phase_key,
            },
            "definition_ref": self.definition_ref,
            "gate_digest": self.gate_digest,
            "implementation_ref": self.implementation_ref,
            "lineage_ref": self.lineage_ref,
            "reviewed_source_commit": self.reviewed_source_commit,
            "original_paths": list(self.original_paths),
            "additional_gate_paths": list(self.additional_gate_paths),
            "path_oids": [item.to_wire() for item in self.path_oids],
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": SOURCE_SCOPE_SCHEMA,
            **self.body(),
            "source_scope_ref": self.source_scope_ref,
        }

    def require_committed_original_paths(self, paths: tuple[str, ...]) -> None:
        """Compare with provider-derived commit effect, never a caller list."""
        if _ordered_paths(paths, "committed_original_paths") != self.original_paths:
            raise HistoricalLineageError("original implementation path set differs")


def decode_migrated_historical_source_scope(raw: object) -> MigratedHistoricalSourceScopeV1:
    """Strict structural decoder; this does not authenticate repository authority."""
    if type(raw) is not dict:
        raise HistoricalLineageError("source scope must be exact object")
    expected = {
        "schema_id", "repository_ref", "goal_path", "coordinate",
        "definition_ref", "gate_digest", "implementation_ref", "lineage_ref",
        "reviewed_source_commit", "original_paths", "additional_gate_paths",
        "path_oids", "source_scope_ref",
    }
    if set(raw) != expected or raw["schema_id"] != SOURCE_SCOPE_SCHEMA:
        raise HistoricalLineageError("source scope schema or fields differ")
    coord = raw["coordinate"]
    if type(coord) is not dict or set(coord) != {"goal_tag", "lane_key", "phase_key"}:
        raise HistoricalLineageError("coordinate fields differ")
    for key in ("original_paths", "additional_gate_paths", "path_oids"):
        if type(raw[key]) is not list:
            raise HistoricalLineageError(f"{key} must be exact array")
    bindings: list[HistoricalPathOidV1] = []
    for item in raw["path_oids"]:
        if type(item) is not dict or set(item) != {"path", "blob_oid"}:
            raise HistoricalLineageError("path binding fields differ")
        bindings.append(HistoricalPathOidV1(**item))
    result = MigratedHistoricalSourceScopeV1(
        repository_ref=raw["repository_ref"],
        goal_path=raw["goal_path"],
        coordinate=GoalPhaseCoordinate(**coord),
        definition_ref=raw["definition_ref"],
        gate_digest=raw["gate_digest"],
        implementation_ref=raw["implementation_ref"],
        lineage_ref=raw["lineage_ref"],
        reviewed_source_commit=raw["reviewed_source_commit"],
        original_paths=tuple(raw["original_paths"]),
        additional_gate_paths=tuple(raw["additional_gate_paths"]),
        path_oids=tuple(bindings),
    )
    if raw != result.to_wire():
        raise HistoricalLineageError("source scope is not canonical")
    return result


_LINEAGE_REASONS = {
    "lineage_unreviewed",
    "current_proof_unavailable",
    "current_proof_stale",
    "current_review_rejected",
}
_REJECTED_REASONS = {
    ReasonCode.COORDINATOR_REVOKED.value,
    ReasonCode.INDEPENDENT_ACCEPTANCE_REJECTED.value,
    ReasonCode.DEPENDENCY_PENDING.value,
    ReasonCode.DEPENDENCY_REJECTED.value,
    "current_review_rejected",
}
_STALE_REASONS = {
    ReasonCode.DEFINITION_QUALIFICATION_STALE.value,
    ReasonCode.IMPLEMENTATION_PUBLICATION_STALE.value,
    ReasonCode.INDEPENDENT_ACCEPTANCE_STALE.value,
    ReasonCode.IMPLEMENTATION_CLOSEOUT_STALE.value,
    ReasonCode.DEPENDENCY_STALE.value,
    "current_proof_stale",
}


@dataclass(frozen=True, slots=True, order=True)
class HistoricalEvaluationReasonV1:
    code: str
    role_key: str

    def __post_init__(self) -> None:
        if self.code not in {*(item.value for item in ReasonCode), *_LINEAGE_REASONS}:
            raise HistoricalLineageError("evaluation reason code is not closed")
        _string(self.role_key, "role_key")

    def to_wire(self) -> dict[str, str]:
        return {"code": self.code, "role_key": self.role_key}


@dataclass(frozen=True, slots=True)
class MigratedHistoricalLineageEvaluationV1:
    """Portable result; decoding is structural, not provider authentication."""

    m14_evaluation_ref: str
    original_implementation_ref: str
    source_scope_ref: str
    lineage_ref: str
    proof_publication_binding_ref: str | None
    review_publication_binding_ref: str | None
    observed_head: str
    protected_paths: tuple[str, ...]
    result: EvaluationResult
    reasons: tuple[HistoricalEvaluationReasonV1, ...]
    gate_observation_ref: str | None
    evaluation_ref: str = field(init=False)

    def __post_init__(self) -> None:
        for name in ("m14_evaluation_ref", "original_implementation_ref", "source_scope_ref", "lineage_ref"):
            _string(getattr(self, name), name)
        for name in ("proof_publication_binding_ref", "review_publication_binding_ref"):
            value = getattr(self, name)
            if value is not None:
                _string(value, name)
        if self.review_publication_binding_ref is not None and self.proof_publication_binding_ref is None:
            raise HistoricalLineageError("review cannot exist without proof")
        if type(self.observed_head) is not str or not _OID.fullmatch(self.observed_head):
            raise HistoricalLineageError("observed_head must be Git identity")
        _ordered_paths(self.protected_paths, "protected_paths")
        if type(self.result) is not EvaluationResult:
            raise HistoricalLineageError("evaluation result type differs")
        if type(self.reasons) is not tuple or any(type(item) is not HistoricalEvaluationReasonV1 for item in self.reasons):
            raise HistoricalLineageError("evaluation reasons must be exact tuple")
        if self.reasons != tuple(sorted(set(self.reasons))):
            raise HistoricalLineageError("evaluation reasons must be sorted and unique")
        codes = {item.code for item in self.reasons}
        expected = (
            EvaluationResult.REJECTED if codes & _REJECTED_REASONS else
            EvaluationResult.STALE if codes & _STALE_REASONS else
            EvaluationResult.UNAVAILABLE if codes else EvaluationResult.SATISFIED
        )
        if self.result is not expected:
            raise HistoricalLineageError("evaluation result contradicts reasons")
        if self.result is EvaluationResult.SATISFIED:
            if self.gate_observation_ref is None or self.review_publication_binding_ref is None:
                raise HistoricalLineageError("satisfaction requires reviewed proof and observation")
            _string(self.gate_observation_ref, "gate_observation_ref")
        elif self.gate_observation_ref is not None:
            raise HistoricalLineageError("negative result cannot carry Gate observation")
        object.__setattr__(self, "evaluation_ref", "goal-migrated-phase-lineage-evaluation:" + fingerprint(self.body()))

    def body(self) -> dict[str, object]:
        return {
            "schema_id": LINEAGE_EVALUATION_SCHEMA,
            "evaluator_profile": LINEAGE_EVALUATOR_PROFILE,
            "m14_evaluation_ref": self.m14_evaluation_ref,
            "original_implementation_ref": self.original_implementation_ref,
            "source_scope_ref": self.source_scope_ref,
            "lineage_ref": self.lineage_ref,
            "proof_publication_binding_ref": self.proof_publication_binding_ref,
            "review_publication_binding_ref": self.review_publication_binding_ref,
            "observed_head": self.observed_head,
            "protected_paths": list(self.protected_paths),
            "result": self.result.value,
            "reasons": [item.to_wire() for item in self.reasons],
            "gate_observation_ref": self.gate_observation_ref,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "evaluation_ref": self.evaluation_ref}


def decode_migrated_historical_lineage_evaluation(raw: object) -> MigratedHistoricalLineageEvaluationV1:
    """Reject noncanonical transport; provider re-verification remains mandatory."""
    if type(raw) is not dict:
        raise HistoricalLineageError("evaluation must be exact object")
    fields = {
        "schema_id", "evaluator_profile", "m14_evaluation_ref", "original_implementation_ref",
        "source_scope_ref", "lineage_ref", "proof_publication_binding_ref",
        "review_publication_binding_ref", "observed_head", "protected_paths",
        "result", "reasons", "gate_observation_ref", "evaluation_ref",
    }
    if set(raw) != fields or raw["schema_id"] != LINEAGE_EVALUATION_SCHEMA or raw["evaluator_profile"] != LINEAGE_EVALUATOR_PROFILE:
        raise HistoricalLineageError("evaluation schema or fields differ")
    if type(raw["protected_paths"]) is not list or type(raw["reasons"]) is not list:
        raise HistoricalLineageError("evaluation arrays must be exact lists")
    reasons: list[HistoricalEvaluationReasonV1] = []
    for item in raw["reasons"]:
        if type(item) is not dict or set(item) != {"code", "role_key"}:
            raise HistoricalLineageError("reason fields differ")
        reasons.append(HistoricalEvaluationReasonV1(**item))
    result = MigratedHistoricalLineageEvaluationV1(
        m14_evaluation_ref=raw["m14_evaluation_ref"],
        original_implementation_ref=raw["original_implementation_ref"],
        source_scope_ref=raw["source_scope_ref"],
        lineage_ref=raw["lineage_ref"],
        proof_publication_binding_ref=raw["proof_publication_binding_ref"],
        review_publication_binding_ref=raw["review_publication_binding_ref"],
        observed_head=raw["observed_head"],
        protected_paths=tuple(raw["protected_paths"]),
        result=EvaluationResult(raw["result"]),
        reasons=tuple(reasons),
        gate_observation_ref=raw["gate_observation_ref"],
    )
    if raw != result.to_wire():
        raise HistoricalLineageError("evaluation is not canonical")
    return result
