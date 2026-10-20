"""One additive lane effect; structural planning is never source authority."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import cast

from .identity import fingerprint
from .phase_document import (
    GoalNativeLaneAuthorityV1, GoalPhaseExecutionAuthorityV1, GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
)
from .phase_document import (
    attach_goal_phase_native_carrier, extract_goal_phase_native_carrier,
)


def _target(candidate: bytes, lane: GoalNativeLaneAuthorityV1,
            represented_lane_keys: tuple[str, ...]) -> GoalPhaseNativeDocumentV4:
    if type(candidate) is not bytes or type(lane) is not GoalNativeLaneAuthorityV1:
        raise TypeError("native lane introduction requires exact bytes and lane")
    lane.__post_init__()
    if type(represented_lane_keys) is not tuple or any(type(k) is not str for k in represented_lane_keys):
        raise TypeError("represented lane keys require exact tuple of strings")
    if tuple(sorted(set(represented_lane_keys))) != represented_lane_keys:
        raise ValueError("represented_lane_inventory_not_canonical")
    _, before = extract_goal_phase_native_carrier(candidate)
    if type(before) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4}:
        raise ValueError("native_lane_introduction_source_profile_unsupported")
    before = cast(GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4, before)
    before.__post_init__()
    execution_authority = before.execution_authority
    if type(execution_authority) is not GoalPhaseExecutionAuthorityV1:
        raise ValueError("native_lane_introduction_genesis_profile_unsupported")
    prior = before.native_lane_authorities if type(before) is GoalPhaseNativeDocumentV4 else ()
    if any(r.lane_key in represented_lane_keys for r in prior):
        raise ValueError("native_lane_partition_conflict")
    if lane.lane_key in represented_lane_keys or any(r.lane_key == lane.lane_key for r in prior):
        raise ValueError("native_lane_already_represented")
    if lane.goal_tag != before.goal_tag:
        raise ValueError("native_lane_goal_mismatch")
    if lane.operational_state in {"held", "blocked"}:
        raise ValueError("native_lane_introduction_hold_profile_unsupported")
    if any(p.coordinate.lane_key == lane.lane_key and p.gate_observations
           for p in before.operational_bundle.phases):
        raise ValueError("native_lane_introduction_gate_profile_unsupported")
    if type(before) is GoalPhaseNativeDocumentV4:
        profile, journal = before.operation_journal_profile, before.phase_operation_journal
    elif type(before) is GoalPhaseNativeDocumentV3:
        profile, journal = "v1", before.phase_operation_journal
    else:
        profile, journal = "none", None
    return GoalPhaseNativeDocumentV4(
        goal_tag=before.goal_tag,
        compatibility_projection_sha256=before.compatibility_projection_sha256,
        compatibility_projection_byte_count=before.compatibility_projection_byte_count,
        definitions=before.definitions, operational_bundle=before.operational_bundle,
        unresolved_dependencies=before.unresolved_dependencies,
        source_refs=before.source_refs, execution_authority=execution_authority,
        native_lane_authorities=tuple(sorted((*prior, lane), key=lambda r: r.lane_key)),
        operation_journal_profile=profile, phase_operation_journal=journal,
    )


@dataclass(frozen=True, slots=True)
class GoalNativeLaneIntroductionPlanV1:
    before_candidate: bytes
    lane: GoalNativeLaneAuthorityV1
    represented_lane_keys: tuple[str, ...]
    after_document: GoalPhaseNativeDocumentV4 = field(init=False)
    after_candidate: bytes = field(init=False)
    semantic_intent_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneIntroductionPlanV1:
            raise TypeError("introduction plan type must be exact")
        document = _target(self.before_candidate, self.lane, self.represented_lane_keys)
        compatibility, _ = extract_goal_phase_native_carrier(self.before_candidate)
        after = attach_goal_phase_native_carrier(compatibility, document)
        object.__setattr__(self, "after_document", document)
        object.__setattr__(self, "after_candidate", after)
        object.__setattr__(self, "semantic_intent_ref", "goal-native-lane-introduction-intent:" + fingerprint({
            "operation": "qualify_native_lane_unheld_v1",
            "before_sha256": "sha256:" + hashlib.sha256(self.before_candidate).hexdigest(),
            "after_sha256": "sha256:" + hashlib.sha256(after).hexdigest(),
            "lane_authority_ref": self.lane.lane_authority_ref,
            "represented_lane_keys": list(self.represented_lane_keys),
        }))


def plan_goal_native_lane_introduction(*, candidate: bytes, lane: GoalNativeLaneAuthorityV1,
                                      represented_lane_keys: tuple[str, ...]) -> GoalNativeLaneIntroductionPlanV1:
    return GoalNativeLaneIntroductionPlanV1(candidate, lane, represented_lane_keys)


def validate_goal_native_lane_introduction_plan(plan: GoalNativeLaneIntroductionPlanV1) -> None:
    """Recompute full plan at consumption; do not repair a mutated instance."""
    if type(plan) is not GoalNativeLaneIntroductionPlanV1:
        raise TypeError("introduction plan type must be exact")
    expected = plan_goal_native_lane_introduction(candidate=plan.before_candidate,
        lane=plan.lane, represented_lane_keys=plan.represented_lane_keys)
    if (plan.after_candidate != expected.after_candidate
        or plan.after_document != expected.after_document
        or plan.semantic_intent_ref != expected.semantic_intent_ref):
        raise ValueError("native_lane_introduction_plan_mutated")
