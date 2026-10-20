"""Native lane hold decisions: strict claims, never an authority issuer.

The concrete provider authenticates stewardship publication. Neither decoding
nor a content-derived reference qualifies a decision or changes lane state.
"""

from __future__ import annotations

# Reuse the owning runtime's exact calendar validator; never duplicate it.
# pyright: reportPrivateUsage=false

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from .identity import fingerprint
from .phase_contracts import _utc_instant
from .phase_document import GoalNativeLaneAuthorityV1

SCHEMA = "aware.goal.native-lane-hold-decision.v1"
_OPEN = "<!-- " + SCHEMA + ":start -->\n```json\n"
_CLOSE = "\n```\n<!-- " + SCHEMA + ":end -->"
_DOCUMENT = re.compile(r"goal-phase-document:sha256:[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class GoalNativeLaneHoldDecisionV1:
    goal_tag: str
    lane_key: str
    source_document_ref: str
    source_revision_ref: str
    owner_profile: str
    owner_ref: str
    target_state: str
    state_detail: str
    current_work_association_ref: str | None
    issued_at: str
    governing_issue_tag: str
    decision_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneHoldDecisionV1:
            raise TypeError("hold decision type must be exact")
        for name in (
            "goal_tag", "lane_key", "source_document_ref", "source_revision_ref",
            "owner_profile", "owner_ref", "target_state", "state_detail", "governing_issue_tag",
        ):
            value = cast(object, getattr(self, name))
            if type(value) is not str or not value.strip() or value != value.strip():
                raise ValueError("native_lane_hold_invalid_" + name)
        if _DOCUMENT.fullmatch(self.source_document_ref) is None:
            raise ValueError("native_lane_hold_invalid_source_document")
        if self.target_state not in {"held", "blocked"}:
            raise ValueError("native_lane_hold_state_unsupported")
        _ = _utc_instant(self.issued_at, "issued_at")
        # Use the carrier's structural ownership/state law, never invent a
        # second reducer. This construction does not authenticate the record.
        _ = GoalNativeLaneAuthorityV1(
            goal_tag=self.goal_tag, lane_key=self.lane_key, role="hold-decision",
            owner_profile=self.owner_profile, owner_ref=self.owner_ref,
            operational_state=self.target_state, state_detail=self.state_detail,
            hold_authority_refs=("goal-native-lane-hold:sha256:" + "0" * 64,),
            current_work_association_ref=self.current_work_association_ref,
        )
        object.__setattr__(self, "decision_ref", "goal-native-lane-hold:" + fingerprint(self.body()))

    def body(self) -> dict[str, object]:
        return {
            "schema_id": SCHEMA,
            "goal_tag": self.goal_tag, "lane_key": self.lane_key,
            "source_document_ref": self.source_document_ref,
            "source_revision_ref": self.source_revision_ref,
            "owner_profile": self.owner_profile, "owner_ref": self.owner_ref,
            "target_state": self.target_state, "state_detail": self.state_detail,
            "current_work_association_ref": self.current_work_association_ref,
            "issued_at": self.issued_at, "governing_issue_tag": self.governing_issue_tag,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "decision_ref": self.decision_ref}


def decode_goal_native_lane_hold_decision(payload: object) -> GoalNativeLaneHoldDecisionV1:
    if type(payload) is not dict:
        raise ValueError("native_lane_hold_wire_invalid")
    values = cast(dict[str, object], payload)
    names = (
        "goal_tag", "lane_key", "source_document_ref", "source_revision_ref",
        "owner_profile", "owner_ref", "target_state", "state_detail", "issued_at",
        "governing_issue_tag",
    )
    if set(values) != {"schema_id", "decision_ref", "current_work_association_ref", *names}:
        raise ValueError("native_lane_hold_wire_fields")
    if values["schema_id"] != SCHEMA or any(type(values[n]) is not str for n in names):
        raise ValueError("native_lane_hold_wire_types")
    current = values["current_work_association_ref"]
    if current is not None and type(current) is not str:
        raise ValueError("native_lane_hold_wire_types")
    decision = GoalNativeLaneHoldDecisionV1(
        **cast(dict[str, str], {name: values[name] for name in names}),
        current_work_association_ref=current,
    )
    if not exact_hold_wire(values, decision.to_wire()):
        raise ValueError("native_lane_hold_wire_digest")
    return decision


def exact_hold_wire(left: object, right: object) -> bool:
    """Strict recursive JSON equality: bool never equals int."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        a, b = cast(dict[str, object], left), cast(dict[str, object], right)
        return a.keys() == b.keys() and all(exact_hold_wire(a[k], b[k]) for k in a)
    if type(left) is list:
        a_list, b_list = cast(list[object], left), cast(list[object], right)
        return len(a_list) == len(b_list) and all(exact_hold_wire(a, b) for a, b in zip(a_list, b_list))
    return left == right


def encode_goal_native_lane_hold_block(decision: GoalNativeLaneHoldDecisionV1) -> str:
    canonical = decode_goal_native_lane_hold_decision(decision.to_wire())
    return _OPEN + json.dumps(canonical.to_wire(), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + _CLOSE


def extract_goal_native_lane_hold_block(issue_text: str) -> GoalNativeLaneHoldDecisionV1:
    if type(issue_text) is not str or issue_text.count(_OPEN) != 1 or issue_text.count(_CLOSE) != 1:
        raise ValueError("native_lane_hold_issue_block_ambiguous")
    payload = issue_text.split(_OPEN, 1)[1].split(_CLOSE, 1)[0]

    def pairs(items: list[tuple[str, object]]) -> Mapping[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("native_lane_hold_duplicate_json_key")
            result[key] = value
        return result

    decoded = cast(object, json.loads(payload, object_pairs_hook=pairs))
    decision = decode_goal_native_lane_hold_decision(decoded)
    if encode_goal_native_lane_hold_block(decision) != _OPEN + payload + _CLOSE:
        raise ValueError("native_lane_hold_issue_block_noncanonical")
    return decision
