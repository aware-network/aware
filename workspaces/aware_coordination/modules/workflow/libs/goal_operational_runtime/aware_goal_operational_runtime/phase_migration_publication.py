"""Repository-neutral planning for one whole-Goal Lane/Phase migration."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

GOAL_PHASE_MIGRATION_AGGREGATE_SCHEMA = (
    "aware.goal.lane-phase-migration-aggregate.v1"
)
GOAL_PHASE_MIGRATION_PLAN_SCHEMA = (
    "aware.goal.lane-phase-migration-publication-plan.v1"
)
GOAL_PHASE_MIGRATION_RECEIPT_SCHEMA = (
    "aware.goal.lane-phase-migration-publication-receipt.v1"
)

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
_ACCEPTANCE = re.compile(
    r"^goal-phase-migration-(?:aggregate|operation)-acceptance:sha256:[0-9a-f]{64}$"
)
_PARITY = re.compile(r"^goal-phase-migration-parity:sha256:[0-9a-f]{64}$")
_PURSUIT = re.compile(r"^goal-pursuit:sha256:[0-9a-f]{64}$")


class GoalPhaseMigrationPublicationError(ValueError):
    """The migration publication input is incomplete, stale, or noncanonical."""


@dataclass(frozen=True, slots=True)
class GoalPhaseMigrationPublicationPlanV1:
    goal_doc_path: str
    source_repository_commit: str
    source_goal_sha256: str
    candidate_goal_sha256: str
    compatibility_projection_sha256: str
    aggregate_sha256: str
    coordinator_acceptance_ref: str
    operation_acceptance_ref: str
    semantic_parity_ref: str
    pursuit_ref: str
    idempotency_ref: str
    semantic_intent_ref: str
    phase_mapping_count: int
    dependency_mapping_count: int
    schema_id: str = GOAL_PHASE_MIGRATION_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_MIGRATION_PLAN_SCHEMA:
            raise GoalPhaseMigrationPublicationError("unsupported migration plan")
        _ = _path(self.goal_doc_path, "goal_doc_path")
        if not _COMMIT.fullmatch(self.source_repository_commit):
            raise GoalPhaseMigrationPublicationError(
                "source_repository_commit is not canonical"
            )
        _ = _sha(self.source_goal_sha256, "source_goal_sha256")
        _ = _sha(self.candidate_goal_sha256, "candidate_goal_sha256")
        _ = _sha(
            self.compatibility_projection_sha256,
            "compatibility_projection_sha256",
        )
        _ = _sha(self.aggregate_sha256, "aggregate_sha256")
        if not _ACCEPTANCE.fullmatch(self.coordinator_acceptance_ref):
            raise GoalPhaseMigrationPublicationError(
                "coordinator_acceptance_ref is not qualified"
            )
        if not self.coordinator_acceptance_ref.startswith(
            "goal-phase-migration-aggregate-acceptance:"
        ):
            raise GoalPhaseMigrationPublicationError(
                "coordinator acceptance has the wrong domain"
            )
        if not _ACCEPTANCE.fullmatch(self.operation_acceptance_ref):
            raise GoalPhaseMigrationPublicationError(
                "operation_acceptance_ref is not qualified"
            )
        if not self.operation_acceptance_ref.startswith(
            "goal-phase-migration-operation-acceptance:"
        ):
            raise GoalPhaseMigrationPublicationError(
                "operation acceptance has the wrong domain"
            )
        if not _PARITY.fullmatch(self.semantic_parity_ref):
            raise GoalPhaseMigrationPublicationError(
                "semantic_parity_ref is not qualified"
            )
        if not _PURSUIT.fullmatch(self.pursuit_ref):
            raise GoalPhaseMigrationPublicationError("pursuit_ref is not qualified")
        _ = _text(self.idempotency_ref, "idempotency_ref")
        if self.semantic_intent_ref != _intent_ref(
            goal_doc_path=self.goal_doc_path,
            source_repository_commit=self.source_repository_commit,
            source_goal_sha256=self.source_goal_sha256,
            candidate_goal_sha256=self.candidate_goal_sha256,
            compatibility_projection_sha256=self.compatibility_projection_sha256,
            aggregate_sha256=self.aggregate_sha256,
            coordinator_acceptance_ref=self.coordinator_acceptance_ref,
            operation_acceptance_ref=self.operation_acceptance_ref,
            semantic_parity_ref=self.semantic_parity_ref,
            pursuit_ref=self.pursuit_ref,
            idempotency_ref=self.idempotency_ref,
            phase_mapping_count=self.phase_mapping_count,
            dependency_mapping_count=self.dependency_mapping_count,
        ):
            raise GoalPhaseMigrationPublicationError("semantic_intent_ref mismatch")
        _ = _positive(self.phase_mapping_count, "phase_mapping_count")
        _ = _nonnegative(
            self.dependency_mapping_count,
            "dependency_mapping_count",
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "goal_doc_path": self.goal_doc_path,
            "source_repository_commit": self.source_repository_commit,
            "source_goal_sha256": self.source_goal_sha256,
            "candidate_goal_sha256": self.candidate_goal_sha256,
            "compatibility_projection_sha256": self.compatibility_projection_sha256,
            "aggregate_sha256": self.aggregate_sha256,
            "coordinator_acceptance_ref": self.coordinator_acceptance_ref,
            "operation_acceptance_ref": self.operation_acceptance_ref,
            "semantic_parity_ref": self.semantic_parity_ref,
            "pursuit_ref": self.pursuit_ref,
            "idempotency_ref": self.idempotency_ref,
            "semantic_intent_ref": self.semantic_intent_ref,
            "phase_mapping_count": self.phase_mapping_count,
            "dependency_mapping_count": self.dependency_mapping_count,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseMigrationPublicationReceiptV1:
    plan: GoalPhaseMigrationPublicationPlanV1
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    publication_state: str
    reconciliation_reason: str | None
    receipt_ref: str
    schema_id: str = GOAL_PHASE_MIGRATION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_MIGRATION_RECEIPT_SCHEMA:
            raise GoalPhaseMigrationPublicationError("unsupported migration receipt")
        if type(self.plan) is not GoalPhaseMigrationPublicationPlanV1:
            raise TypeError("plan must be GoalPhaseMigrationPublicationPlanV1")
        self.plan.__post_init__()
        if not _COMMIT.fullmatch(self.repository_commit_ref):
            raise GoalPhaseMigrationPublicationError(
                "repository_commit_ref is not canonical"
            )
        repository_commit_receipt_ref = _text(
            self.repository_commit_receipt_ref,
            "repository_commit_receipt_ref",
        )
        if repository_commit_receipt_ref != (
            f"repository-commit:{self.repository_commit_ref}"
        ):
            raise GoalPhaseMigrationPublicationError(
                "repository commit receipt does not bind commit"
            )
        if self.publication_state not in {
            "repository_published",
            "reconciliation_required",
        }:
            raise GoalPhaseMigrationPublicationError("invalid publication_state")
        if self.publication_state == "repository_published":
            if self.reconciliation_reason is not None:
                raise GoalPhaseMigrationPublicationError(
                    "published receipt cannot carry reconciliation reason"
                )
        else:
            _ = _text(self.reconciliation_reason, "reconciliation_reason")
        expected = _receipt_ref(
            plan=self.plan,
            repository_commit_ref=self.repository_commit_ref,
            repository_commit_receipt_ref=self.repository_commit_receipt_ref,
            publication_state=self.publication_state,
            reconciliation_reason=self.reconciliation_reason,
        )
        if self.receipt_ref != expected:
            raise GoalPhaseMigrationPublicationError("migration receipt_ref mismatch")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "plan": self.plan.to_wire(),
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "publication_state": self.publication_state,
            "reconciliation_reason": self.reconciliation_reason,
            "receipt_ref": self.receipt_ref,
        }


def plan_goal_phase_native_migration_publication(
    *,
    source_goal_bytes: bytes,
    candidate_goal_bytes: bytes,
    compatibility_projection_bytes: bytes,
    aggregate_bytes: bytes,
    expected_aggregate_sha256: str,
    coordinator_acceptance_ref: str,
    operation_acceptance_ref: str,
    idempotency_ref: str,
) -> GoalPhaseMigrationPublicationPlanV1:
    """Validate the complete accepted intent and return one deterministic plan."""

    for value, name in (
        (source_goal_bytes, "source_goal_bytes"),
        (candidate_goal_bytes, "candidate_goal_bytes"),
        (compatibility_projection_bytes, "compatibility_projection_bytes"),
        (aggregate_bytes, "aggregate_bytes"),
    ):
        if type(value) is not bytes:
            raise TypeError(f"{name} must be exact bytes")
    _ = _sha(expected_aggregate_sha256, "expected_aggregate_sha256")
    envelope = _decode_json(aggregate_bytes)
    _keys(
        envelope,
        {
            "schema_id",
            "canonicalization",
            "manifest",
            "canonical_manifest_byte_count",
            "canonical_manifest_sha256",
        },
        "aggregate",
    )
    if envelope["schema_id"] != GOAL_PHASE_MIGRATION_AGGREGATE_SCHEMA:
        raise GoalPhaseMigrationPublicationError("unsupported aggregate schema")
    if not _exact_equal(envelope["canonicalization"], {
        "profile": "sorted-keys-utf8-compact-json-v1",
        "ensure_ascii": False,
        "separators": [",", ":"],
        "trailing_newline_in_digest": False,
    }):
        raise GoalPhaseMigrationPublicationError(
            "unsupported aggregate canonicalization"
        )
    manifest = _mapping(envelope["manifest"], "manifest")
    canonical = _canonical(manifest)
    canonical_byte_count = _nonnegative(
        envelope["canonical_manifest_byte_count"],
        "canonical_manifest_byte_count",
    )
    if canonical_byte_count != len(canonical):
        raise GoalPhaseMigrationPublicationError("aggregate byte count mismatch")
    aggregate_sha256 = _digest(canonical)
    if _sha(
        envelope["canonical_manifest_sha256"],
        "canonical_manifest_sha256",
    ) != aggregate_sha256:
        raise GoalPhaseMigrationPublicationError("aggregate digest mismatch")
    if expected_aggregate_sha256 != aggregate_sha256:
        raise GoalPhaseMigrationPublicationError("aggregate is not accepted root")
    _keys(
        manifest,
        {
            "source",
            "authority_statement",
            "lane_manifests",
            "dependency_mappings",
            "coordinator_acceptance",
            "totals",
            "publication_preconditions",
            "publication_candidate",
        },
        "manifest",
    )
    _validate_governance(manifest)
    source = _mapping(manifest["source"], "source")
    _keys(
        source,
        {
            "goal_doc_path",
            "goal_tag",
            "goal_sha256",
            "repository_commit",
            "authority_profile",
        },
        "source",
    )
    goal_doc_path = _path(source["goal_doc_path"], "source.goal_doc_path")
    source_goal_sha256 = _digest(source_goal_bytes)
    if source["goal_sha256"] != source_goal_sha256:
        raise GoalPhaseMigrationPublicationError("source Goal digest mismatch")
    source_repository_commit = _text(
        source["repository_commit"], "source.repository_commit"
    )
    if not _COMMIT.fullmatch(source_repository_commit):
        raise GoalPhaseMigrationPublicationError(
            "source repository commit is not canonical"
        )
    candidate = _mapping(manifest["publication_candidate"], "publication_candidate")
    _keys(
        candidate,
        {
            "goal_doc_path",
            "before_goal_sha256",
            "after_goal_sha256",
            "compatibility_projection_sha256",
            "changed_paths",
            "phase_mapping_count",
            "dependency_mapping_count",
            "semantic_parity_ref",
            "current_phase_profile_pursuit_ref",
        },
        "publication_candidate",
    )
    if candidate["goal_doc_path"] != goal_doc_path:
        raise GoalPhaseMigrationPublicationError("candidate Goal path mismatch")
    if candidate["before_goal_sha256"] != source_goal_sha256:
        raise GoalPhaseMigrationPublicationError("candidate preimage mismatch")
    candidate_goal_sha256 = _digest(candidate_goal_bytes)
    if candidate["after_goal_sha256"] != candidate_goal_sha256:
        raise GoalPhaseMigrationPublicationError("candidate Goal digest mismatch")
    if candidate_goal_sha256 == source_goal_sha256:
        raise GoalPhaseMigrationPublicationError("migration candidate is unchanged")
    compatibility_sha256 = _digest(compatibility_projection_bytes)
    if candidate["compatibility_projection_sha256"] != compatibility_sha256:
        raise GoalPhaseMigrationPublicationError(
            "compatibility projection digest mismatch"
        )
    if candidate["changed_paths"] != [goal_doc_path]:
        raise GoalPhaseMigrationPublicationError(
            "migration must change exactly the Goal path"
        )
    totals = _mapping(manifest["totals"], "totals")
    phase_count = _positive(totals.get("phase_mapping_count"), "phase count")
    dependency_count = _nonnegative(
        totals.get("dependency_mapping_count"), "dependency count"
    )
    if _positive(
        candidate["phase_mapping_count"], "candidate Phase count"
    ) != phase_count:
        raise GoalPhaseMigrationPublicationError("candidate Phase count mismatch")
    if _nonnegative(
        candidate["dependency_mapping_count"], "candidate dependency count"
    ) != dependency_count:
        raise GoalPhaseMigrationPublicationError(
            "candidate dependency count mismatch"
        )
    semantic_parity_ref = _text(
        candidate["semantic_parity_ref"], "semantic_parity_ref"
    )
    pursuit_ref = _text(
        candidate["current_phase_profile_pursuit_ref"], "pursuit_ref"
    )
    canonical_idempotency_ref = _text(idempotency_ref, "idempotency_ref")
    body: dict[str, object] = {
        "goal_doc_path": goal_doc_path,
        "source_repository_commit": source_repository_commit,
        "source_goal_sha256": source_goal_sha256,
        "candidate_goal_sha256": candidate_goal_sha256,
        "compatibility_projection_sha256": compatibility_sha256,
        "aggregate_sha256": aggregate_sha256,
        "coordinator_acceptance_ref": coordinator_acceptance_ref,
        "operation_acceptance_ref": operation_acceptance_ref,
        "semantic_parity_ref": semantic_parity_ref,
        "pursuit_ref": pursuit_ref,
        "idempotency_ref": canonical_idempotency_ref,
        "phase_mapping_count": phase_count,
        "dependency_mapping_count": dependency_count,
    }
    semantic_intent_ref = "goal-phase-migration-intent:" + _digest(_canonical(body))
    return GoalPhaseMigrationPublicationPlanV1(
        goal_doc_path=goal_doc_path,
        source_repository_commit=source_repository_commit,
        source_goal_sha256=source_goal_sha256,
        candidate_goal_sha256=candidate_goal_sha256,
        compatibility_projection_sha256=compatibility_sha256,
        aggregate_sha256=aggregate_sha256,
        coordinator_acceptance_ref=coordinator_acceptance_ref,
        operation_acceptance_ref=operation_acceptance_ref,
        semantic_parity_ref=semantic_parity_ref,
        pursuit_ref=pursuit_ref,
        idempotency_ref=canonical_idempotency_ref,
        phase_mapping_count=phase_count,
        dependency_mapping_count=dependency_count,
        semantic_intent_ref=semantic_intent_ref,
    )


def issue_goal_phase_migration_publication_receipt(
    *,
    plan: GoalPhaseMigrationPublicationPlanV1,
    repository_commit_ref: str,
    repository_commit_receipt_ref: str,
    publication_state: str,
    reconciliation_reason: str | None = None,
) -> GoalPhaseMigrationPublicationReceiptV1:
    if type(plan) is not GoalPhaseMigrationPublicationPlanV1:
        raise TypeError("plan must be GoalPhaseMigrationPublicationPlanV1")
    plan.__post_init__()
    receipt_ref = _receipt_ref(
        plan=plan,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=repository_commit_receipt_ref,
        publication_state=publication_state,
        reconciliation_reason=reconciliation_reason,
    )
    return GoalPhaseMigrationPublicationReceiptV1(
        plan=plan,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=repository_commit_receipt_ref,
        publication_state=publication_state,
        reconciliation_reason=reconciliation_reason,
        receipt_ref=receipt_ref,
    )


def _validate_governance(manifest: Mapping[str, object]) -> None:
    acceptance = _mapping(manifest["coordinator_acceptance"], "acceptance")
    if not _exact_equal(acceptance, {
        "required": True,
        "authority": "actorworld_goal_governance_coordinator",
        "binding": "canonical_manifest_sha256",
        "receipt_location": "governance_issue_append_only_update",
    }):
        raise GoalPhaseMigrationPublicationError(
            "aggregate coordinator acceptance contract mismatch"
        )
    lanes = _list(manifest["lane_manifests"], "lane_manifests")
    if not lanes:
        raise GoalPhaseMigrationPublicationError("aggregate has no lanes")
    phase_count = 0
    for raw in lanes:
        lane = _mapping(raw, "lane manifest")
        if lane.get("owner_verdict_status") != "optional_consultation":
            raise GoalPhaseMigrationPublicationError(
                "lane owner verdict remains a publication dependency"
            )
        if lane.get("publication_dependency") is not False:
            raise GoalPhaseMigrationPublicationError(
                "lane consultation must be non-vetoing"
            )
        _ = _sha(lane.get("canonical_manifest_sha256"), "lane manifest digest")
        phase_count += _positive(lane.get("phase_count"), "lane Phase count")
    totals = _mapping(manifest["totals"], "totals")
    if _nonnegative(
        totals.get("pending_lane_owner_verdict_count"),
        "pending lane owner verdict count",
    ) != 0:
        raise GoalPhaseMigrationPublicationError("pending lane owner verdicts remain")
    if _positive(totals.get("lane_count"), "lane count") != len(lanes):
        raise GoalPhaseMigrationPublicationError("lane count mismatch")
    if _positive(totals.get("phase_mapping_count"), "Phase count") != phase_count:
        raise GoalPhaseMigrationPublicationError("Phase count mismatch")
    dependencies = _list(manifest["dependency_mappings"], "dependency_mappings")
    if _nonnegative(
        totals.get("dependency_mapping_count"), "dependency count"
    ) != len(dependencies):
        raise GoalPhaseMigrationPublicationError("dependency count mismatch")
    for raw in dependencies:
        dependency = _mapping(raw, "dependency")
        if dependency.get("required_prerequisite_gate_digest") is None:
            if (
                dependency.get("mapping_state") != "external_gate_digest_unresolved"
                or dependency.get("eligibility_effect") != "none"
                or dependency.get("publication_disposition")
                != "typed_unresolved_non_eligibility_producing"
                or dependency.get("operational_observation") is not None
            ):
                raise GoalPhaseMigrationPublicationError(
                    "unresolved dependency could produce eligibility"
                )
        else:
            _ = _sha(
                dependency.get("required_prerequisite_gate_digest"),
                "prerequisite Gate digest",
            )
    required = {
        "independent_coordinator_acceptance_of_aggregate_root",
        "independently_accepted_repository_cas_migration_effect",
        "fresh_whole_goal_recapture",
        "regenerated_aggregate_root_at_final_source_revision",
        "current_phase_profile_pursuit",
    }
    preconditions = _list(manifest["publication_preconditions"], "preconditions")
    if (
        len(preconditions) != len(required)
        or any(type(item) is not str for item in preconditions)
        or set(cast(list[str], preconditions)) != required
    ):
        raise GoalPhaseMigrationPublicationError("publication preconditions mismatch")


def _receipt_ref(
    *,
    plan: GoalPhaseMigrationPublicationPlanV1,
    repository_commit_ref: str,
    repository_commit_receipt_ref: str,
    publication_state: str,
    reconciliation_reason: str | None,
) -> str:
    body = {
        "plan": plan.to_wire(),
        "repository_commit_ref": _text(
            repository_commit_ref, "repository_commit_ref"
        ),
        "repository_commit_receipt_ref": _text(
            repository_commit_receipt_ref, "repository_commit_receipt_ref"
        ),
        "publication_state": _text(publication_state, "publication_state"),
        "reconciliation_reason": reconciliation_reason,
    }
    return "goal-phase-migration-publication:" + _digest(_canonical(body))


def _intent_ref(
    *,
    goal_doc_path: str,
    source_repository_commit: str,
    source_goal_sha256: str,
    candidate_goal_sha256: str,
    compatibility_projection_sha256: str,
    aggregate_sha256: str,
    coordinator_acceptance_ref: str,
    operation_acceptance_ref: str,
    semantic_parity_ref: str,
    pursuit_ref: str,
    idempotency_ref: str,
    phase_mapping_count: int,
    dependency_mapping_count: int,
) -> str:
    return "goal-phase-migration-intent:" + _digest(
        _canonical(
            {
                "goal_doc_path": goal_doc_path,
                "source_repository_commit": source_repository_commit,
                "source_goal_sha256": source_goal_sha256,
                "candidate_goal_sha256": candidate_goal_sha256,
                "compatibility_projection_sha256": (
                    compatibility_projection_sha256
                ),
                "aggregate_sha256": aggregate_sha256,
                "coordinator_acceptance_ref": coordinator_acceptance_ref,
                "operation_acceptance_ref": operation_acceptance_ref,
                "semantic_parity_ref": semantic_parity_ref,
                "pursuit_ref": pursuit_ref,
                "idempotency_ref": idempotency_ref,
                "phase_mapping_count": phase_mapping_count,
                "dependency_mapping_count": dependency_mapping_count,
            }
        )
    )


def _decode_json(payload: bytes) -> Mapping[str, object]:
    try:
        value = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseMigrationPublicationError("aggregate is not JSON") from error
    return _mapping(value, "aggregate")


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise GoalPhaseMigrationPublicationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise GoalPhaseMigrationPublicationError(f"{name} must be an object")
    return cast(Mapping[str, object], value)


def _list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseMigrationPublicationError(f"{name} must be an array")
    return cast(list[object], value)


def _keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise GoalPhaseMigrationPublicationError(f"{name} fields are not canonical")


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise GoalPhaseMigrationPublicationError(f"{name} must be canonical text")
    return value


def _path(value: object, name: str) -> str:
    result = _text(value, name)
    if result.startswith("/") or ".." in result.split("/"):
        raise GoalPhaseMigrationPublicationError(f"{name} must be repository-relative")
    return result


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise GoalPhaseMigrationPublicationError(f"{name} must be positive integer")
    return value


def _nonnegative(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise GoalPhaseMigrationPublicationError(
            f"{name} must be nonnegative integer"
        )
    return value


def _sha(value: object, name: str) -> str:
    result = _text(value, name)
    if not _SHA256.fullmatch(result):
        raise GoalPhaseMigrationPublicationError(f"{name} must be qualified SHA-256")
    return result


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _exact_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_mapping = cast(dict[object, object], left)
        right_mapping = cast(dict[object, object], right)
        return left_mapping.keys() == right_mapping.keys() and all(
            _exact_equal(left_mapping[key], right_mapping[key])
            for key in left_mapping
        )
    if type(left) is list:
        left_list = cast(list[object], left)
        right_list = cast(list[object], right)
        return len(left_list) == len(right_list) and all(
            _exact_equal(left_item, right_item)
            for left_item, right_item in zip(left_list, right_list, strict=True)
        )
    return left == right


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


__all__ = [
    "GOAL_PHASE_MIGRATION_AGGREGATE_SCHEMA",
    "GOAL_PHASE_MIGRATION_PLAN_SCHEMA",
    "GOAL_PHASE_MIGRATION_RECEIPT_SCHEMA",
    "GoalPhaseMigrationPublicationError",
    "GoalPhaseMigrationPublicationPlanV1",
    "GoalPhaseMigrationPublicationReceiptV1",
    "issue_goal_phase_migration_publication_receipt",
    "plan_goal_phase_native_migration_publication",
]
