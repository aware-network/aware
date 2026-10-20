"""Neutral first-Project intention. Strict data is not initial-authoring authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .project_read_contract import ProjectContextRecordV1, strict_object


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def reference(domain: str, body: object) -> str:
    return domain + ":sha256:" + hashlib.sha256(canonical(body)).hexdigest()


@dataclass(frozen=True, slots=True)
class ProjectCreateRequestV1:
    record: ProjectContextRecordV1
    request_ref: str

    def __post_init__(self) -> None:
        self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self.record) is not ProjectContextRecordV1:
            raise ValueError("exact initial Project record required")
        record = self.record.to_wire()
        if self.record.project.status != "initializing" or self.record.goal_tags:
            raise ValueError(
                "initial Project must be initializing with empty membership"
            )
        body = {"schema_id": "aware.project.create-request.v1", "record": record}
        if type(self.request_ref) is not str or self.request_ref != reference(
            "project-create-request", body
        ):
            raise ValueError("invalid Project create request reference")
        return {**body, "request_ref": self.request_ref}

    @classmethod
    def from_wire(cls, value: object) -> ProjectCreateRequestV1:
        wire = strict_object(
            value, {"schema_id", "record", "request_ref"}, "Project creation"
        )
        if (
            wire["schema_id"] != "aware.project.create-request.v1"
            or type(wire["request_ref"]) is not str
        ):
            raise ValueError("invalid Project creation schema")
        return cls(
            ProjectContextRecordV1.from_wire(wire["record"]), wire["request_ref"]
        )

    @classmethod
    def author(cls, record: ProjectContextRecordV1) -> ProjectCreateRequestV1:
        body = {
            "schema_id": "aware.project.create-request.v1",
            "record": record.to_wire(),
        }
        return cls(record, reference("project-create-request", body))
