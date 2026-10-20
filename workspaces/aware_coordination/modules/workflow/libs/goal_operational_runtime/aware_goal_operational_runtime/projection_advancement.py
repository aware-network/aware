from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .identity import fingerprint, required_token


class GoalProjectionChange(StrEnum):
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    AMBIGUOUS = "ambiguous"


class GoalProjectionSourceCurrentness(StrEnum):
    CURRENT = "current"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class GoalProjectionEvidenceV1:
    source_revision: str
    goal_path: str
    goal_sha256: str
    projector_ref: str
    projector_version: str
    lowered_intent_stream_digest: str
    operational_state_digest: str
    projection_receipt_ref: str
    source_verification_receipt_ref: str

    def __post_init__(self) -> None:
        for field, value in (
            ("source_revision", self.source_revision),
            ("goal_path", self.goal_path),
            ("goal_sha256", self.goal_sha256),
            ("projector_ref", self.projector_ref),
            ("projector_version", self.projector_version),
            ("lowered_intent_stream_digest", self.lowered_intent_stream_digest),
            ("operational_state_digest", self.operational_state_digest),
            ("projection_receipt_ref", self.projection_receipt_ref),
            (
                "source_verification_receipt_ref",
                self.source_verification_receipt_ref,
            ),
        ):
            object.__setattr__(self, field, required_token(value, field))
        if not self.goal_sha256.startswith("sha256:"):
            raise ValueError("goal_sha256 must be a sha256: reference")

    def to_wire(self) -> dict[str, object]:
        return {
            "source_revision": self.source_revision,
            "goal_path": self.goal_path,
            "goal_sha256": self.goal_sha256,
            "projector_ref": self.projector_ref,
            "projector_version": self.projector_version,
            "lowered_intent_stream_digest": self.lowered_intent_stream_digest,
            "operational_state_digest": self.operational_state_digest,
            "projection_receipt_ref": self.projection_receipt_ref,
            "source_verification_receipt_ref": self.source_verification_receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalProjectionAdvancementReceiptV1:
    previous: GoalProjectionEvidenceV1
    candidate: GoalProjectionEvidenceV1
    observed_current_source_revision: str
    source_currentness: GoalProjectionSourceCurrentness
    projection_change: GoalProjectionChange
    blocker_codes: tuple[str, ...]
    receipt_ref: str

    @property
    def host_rebinding_eligible(self) -> bool:
        return (
            self.source_currentness is GoalProjectionSourceCurrentness.CURRENT
            and self.projection_change is GoalProjectionChange.UNCHANGED
            and not self.blocker_codes
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": "aware.goal.projection_advancement.receipt.v1",
            "previous": self.previous.to_wire(),
            "candidate": self.candidate.to_wire(),
            "observed_current_source_revision": self.observed_current_source_revision,
            "source_currentness": self.source_currentness.value,
            "projection_change": self.projection_change.value,
            "blocker_codes": list(self.blocker_codes),
            "host_rebinding_eligible": self.host_rebinding_eligible,
            "receipt_ref": self.receipt_ref,
            "effects": {
                "goal_mutation": "none",
                "host_rebinding": "none",
                "issue_transition": "none",
                "dependency_evaluation": "none",
                "dispatch": "none",
            },
        }


def assess_goal_projection_advancement(
    *,
    previous: GoalProjectionEvidenceV1,
    candidate: GoalProjectionEvidenceV1,
    observed_current_source_revision: str,
) -> GoalProjectionAdvancementReceiptV1:
    if type(previous) is not GoalProjectionEvidenceV1:
        raise TypeError("previous must be GoalProjectionEvidenceV1")
    if type(candidate) is not GoalProjectionEvidenceV1:
        raise TypeError("candidate must be GoalProjectionEvidenceV1")
    current_revision = required_token(
        observed_current_source_revision, "observed_current_source_revision"
    )
    source_currentness = (
        GoalProjectionSourceCurrentness.CURRENT
        if candidate.source_revision == current_revision
        else GoalProjectionSourceCurrentness.STALE
    )
    blockers: list[str] = []
    if previous.goal_path != candidate.goal_path:
        blockers.append("goal_path_changed")
    if (
        previous.projector_ref != candidate.projector_ref
        or previous.projector_version != candidate.projector_version
    ):
        blockers.append("projector_identity_changed")
    if source_currentness is GoalProjectionSourceCurrentness.STALE:
        blockers.append("candidate_source_stale")

    if blockers:
        change = GoalProjectionChange.AMBIGUOUS
    elif (
        previous.lowered_intent_stream_digest
        == candidate.lowered_intent_stream_digest
        and previous.operational_state_digest
        == candidate.operational_state_digest
    ):
        change = GoalProjectionChange.UNCHANGED
    else:
        change = GoalProjectionChange.CHANGED

    body: dict[str, object] = {
        "schema_id": "aware.goal.projection_advancement.receipt.v1",
        "previous": previous.to_wire(),
        "candidate": candidate.to_wire(),
        "observed_current_source_revision": current_revision,
        "source_currentness": source_currentness.value,
        "projection_change": change.value,
        "blocker_codes": blockers,
    }
    return GoalProjectionAdvancementReceiptV1(
        previous=previous,
        candidate=candidate,
        observed_current_source_revision=current_revision,
        source_currentness=source_currentness,
        projection_change=change,
        blocker_codes=tuple(blockers),
        receipt_ref="goal-projection-advancement:" + fingerprint(body),
    )


__all__ = [
    "GoalProjectionAdvancementReceiptV1",
    "GoalProjectionChange",
    "GoalProjectionEvidenceV1",
    "GoalProjectionSourceCurrentness",
    "assess_goal_projection_advancement",
]
