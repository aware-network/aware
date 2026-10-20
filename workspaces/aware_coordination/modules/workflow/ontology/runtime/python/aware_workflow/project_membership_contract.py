"""One pure Project member-append law. Plans and digests grant no permission."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import cast

from .project_create_contract import canonical, reference
from .project_read_contract import (
    ProjectContextRecordV1,
    goal_tag,
    project_key,
    strict_object,
)
from .project_source_codec import encode_project_context_toml


@dataclass(frozen=True, slots=True)
class ProjectGoalMembershipRequestV1:
    project_key: str
    goal_tag: str
    request_ref: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        body = {
            "schema_id": "aware.project.goal-membership-request.v1",
            "project_key": project_key(self.project_key),
            "goal_tag": goal_tag(self.goal_tag),
        }
        if type(self.request_ref) is not str or self.request_ref != reference(
            "project-goal-membership-request", body
        ):
            raise ValueError("invalid Project membership request reference")
        return {**body, "request_ref": self.request_ref}

    @classmethod
    def author(cls, key: str, tag: str) -> ProjectGoalMembershipRequestV1:
        body = {
            "schema_id": "aware.project.goal-membership-request.v1",
            "project_key": project_key(key),
            "goal_tag": goal_tag(tag),
        }
        return cls(key, tag, reference("project-goal-membership-request", body))

    @classmethod
    def from_wire(cls, value: object) -> ProjectGoalMembershipRequestV1:
        wire = strict_object(
            value,
            {"schema_id", "project_key", "goal_tag", "request_ref"},
            "Project membership request",
        )
        if (
            type(wire["schema_id"]) is not str
            or wire["schema_id"] != "aware.project.goal-membership-request.v1"
            or type(wire["request_ref"]) is not str
        ):
            raise ValueError("invalid Project membership request schema")
        return cls(
            project_key(wire["project_key"]),
            goal_tag(wire["goal_tag"]),
            wire["request_ref"],
        )


def _append(
    request: ProjectGoalMembershipRequestV1, before: ProjectContextRecordV1
) -> ProjectContextRecordV1:
    if (
        type(request) is not ProjectGoalMembershipRequestV1
        or type(before) is not ProjectContextRecordV1
    ):
        raise ValueError("exact Project membership inputs required")
    _ = request.to_wire()
    _ = before.to_wire()
    if request.project_key != before.project.project_key:
        raise ValueError("Project membership key mismatch")
    if request.goal_tag in before.goal_tags:
        # Only original-effect recovery can prove a completed retry. The pure
        # law cannot treat an existing tag as an authenticated prior effect.
        raise ValueError("Project membership already present")
    return ProjectContextRecordV1(before.project, (*before.goal_tags, request.goal_tag))


def _body(
    request: ProjectGoalMembershipRequestV1,
    before: ProjectContextRecordV1,
    after: ProjectContextRecordV1,
) -> dict[str, object]:
    expected = _append(request, before)
    if type(after) is not ProjectContextRecordV1 or canonical(
        after.to_wire()
    ) != canonical(expected.to_wire()):
        raise ValueError("Project membership changes more than the exact append")
    content = encode_project_context_toml(after)
    return {
        "schema_id": "aware.project.goal-membership-plan.v1",
        "request": request.to_wire(),
        "before": before.to_wire(),
        "after": after.to_wire(),
        "content_utf8": content.decode("utf-8"),
        "content_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
    }


@dataclass(frozen=True, slots=True)
class ProjectGoalMembershipPlanV1:
    request: ProjectGoalMembershipRequestV1
    before: ProjectContextRecordV1
    after: ProjectContextRecordV1
    plan_ref: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        body = _body(self.request, self.before, self.after)
        if type(self.plan_ref) is not str or self.plan_ref != reference(
            "project-goal-membership-plan", body
        ):
            raise ValueError("invalid Project membership plan reference")
        return {**body, "plan_ref": self.plan_ref}

    @property
    def content(self) -> bytes:
        _ = self.to_wire()
        return encode_project_context_toml(self.after)

    @classmethod
    def from_wire(cls, value: object) -> ProjectGoalMembershipPlanV1:
        wire = strict_object(
            value,
            {
                "schema_id",
                "request",
                "before",
                "after",
                "content_utf8",
                "content_sha256",
                "plan_ref",
            },
            "Project membership plan",
        )
        if (
            type(wire["schema_id"]) is not str
            or wire["schema_id"] != "aware.project.goal-membership-plan.v1"
            or any(
                type(wire[key]) is not str
                for key in ("content_utf8", "content_sha256", "plan_ref")
            )
        ):
            raise ValueError("invalid Project membership plan schema")
        plan = cls(
            ProjectGoalMembershipRequestV1.from_wire(wire["request"]),
            ProjectContextRecordV1.from_wire(wire["before"]),
            ProjectContextRecordV1.from_wire(wire["after"]),
            cast(str, wire["plan_ref"]),
        )
        if canonical(wire) != canonical(plan.to_wire()):
            raise ValueError("Project membership content differs from exact plan")
        return plan


def plan_project_goal_membership(
    request: ProjectGoalMembershipRequestV1, before: ProjectContextRecordV1
) -> ProjectGoalMembershipPlanV1:
    # Validate issued inputs before detaching. Never reconstruct an invalid ref
    # into a repaired request, or mutate the caller's original source record.
    after = _append(request, before)
    detached_request = ProjectGoalMembershipRequestV1.from_wire(request.to_wire())
    detached_before = ProjectContextRecordV1.from_wire(before.to_wire())
    detached_after = ProjectContextRecordV1.from_wire(after.to_wire())
    body = _body(detached_request, detached_before, detached_after)
    return ProjectGoalMembershipPlanV1(
        detached_request,
        detached_before,
        detached_after,
        reference("project-goal-membership-plan", body),
    )
