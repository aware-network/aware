"""One pure initial-state law; no filesystem, publisher or caller permission."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .project_create_contract import ProjectCreateRequestV1, canonical, reference
from .project_source_codec import encode_project_context_toml


@dataclass(frozen=True, slots=True)
class ProjectCreatePlanV1:
    request: ProjectCreateRequestV1
    content: bytes
    plan_ref: str

    def to_wire(self) -> dict[str, object]:
        if (
            type(self.request) is not ProjectCreateRequestV1
            or type(self.content) is not bytes
        ):
            raise ValueError("exact Project creation plan required")
        request = self.request.to_wire()
        if self.content != encode_project_context_toml(self.request.record):
            raise ValueError("Project candidate differs from authored intention")
        body = {
            "schema_id": "aware.project.create-plan.v1",
            "request": request,
            "content_utf8": self.content.decode("utf-8"),
            "content_sha256": "sha256:" + hashlib.sha256(self.content).hexdigest(),
        }
        if type(self.plan_ref) is not str or self.plan_ref != reference(
            "project-create-plan", body
        ):
            raise ValueError("invalid Project creation plan reference")
        return {**body, "plan_ref": self.plan_ref}


def plan_project_context_creation(
    request: ProjectCreateRequestV1,
) -> ProjectCreatePlanV1:
    if type(request) is not ProjectCreateRequestV1:
        raise ValueError("exact Project creation request required")
    # Consumption validates without repairing a mutated instance.
    wire = request.to_wire()
    copied = ProjectCreateRequestV1.from_wire(wire)
    if canonical(wire) != canonical(copied.to_wire()):
        raise ValueError("Project intention changed")
    content = encode_project_context_toml(copied.record)
    body = {
        "schema_id": "aware.project.create-plan.v1",
        "request": wire,
        "content_utf8": content.decode("utf-8"),
        "content_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
    }
    return ProjectCreatePlanV1(copied, content, reference("project-create-plan", body))
