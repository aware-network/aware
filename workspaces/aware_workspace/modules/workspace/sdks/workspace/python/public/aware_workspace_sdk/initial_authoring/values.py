"""Initial-authoring claims; detached data is never publication permission.

The filesystem profile is deliberately local: execution correlation and
owner-private retained metadata are not authenticated Identity or namespace
authority. The original publisher must separately admit each exact effect.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass

PROFILE = "repository_initial_authoring_v1"
SCHEMA = "aware.workspace.initial-authoring-enrollment.v1"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class InitialAuthoringEnrollmentEvidence:
    schema_id: str
    profile: str
    enrollment_id: str
    repository_root: str
    root_device: int
    root_inode: int
    metadata_device: int
    metadata_inode: int
    local_uid: int
    execution_id: str
    preparation_attempt_ref: str
    selected_ref: str
    issuer_ref: str
    issuer_generation: str
    assurance: str
    enrollment_ref: str

    def __post_init__(self):
        self.to_wire()

    def to_wire(self) -> dict[str, object]:
        body = asdict(self)
        reference = body.pop("enrollment_ref")
        if (
            any(
                type(body[name]) is not str
                for name in (
                    "schema_id",
                    "profile",
                    "enrollment_id",
                    "repository_root",
                    "execution_id",
                    "preparation_attempt_ref",
                    "selected_ref",
                    "issuer_ref",
                    "issuer_generation",
                    "assurance",
                )
            )
            or self.schema_id != SCHEMA
            or self.profile != PROFILE
            or self.assurance != "local_fresh_repository_execution_correlation"
            or type(self.repository_root) is not str
            or not self.repository_root.startswith("/")
            or self.repository_root == "/"
            or any(
                part in ("", ".", "..") for part in self.repository_root[1:].split("/")
            )
            or any(
                type(value) is not int or value < 0
                for value in (
                    self.root_device,
                    self.root_inode,
                    self.metadata_device,
                    self.metadata_inode,
                    self.local_uid,
                )
            )
            or type(self.execution_id) is not str
            or re.fullmatch(r"(?:codex|claude_code)-[^\s]+", self.execution_id) is None
            or type(self.preparation_attempt_ref) is not str
            or re.fullmatch(
                r"repository-attempt:[0-9a-f]{32}", self.preparation_attempt_ref
            )
            is None
            or self.selected_ref != "refs/heads/main"
            or type(self.enrollment_id) is not str
            or re.fullmatch(r"[0-9a-f]{32}", self.enrollment_id) is None
            or type(self.issuer_ref) is not str
            or re.fullmatch(r"workspace-publication:[0-9a-f]{32}", self.issuer_ref)
            is None
            or type(self.issuer_generation) is not str
            or re.fullmatch(r"[0-9a-f]{32}", self.issuer_generation) is None
            or type(reference) is not str
            or reference
            != "workspace-initial-enrollment:sha256:"
            + hashlib.sha256(_canonical(body)).hexdigest()
        ):
            raise ValueError("initial_authoring_enrollment_invalid")
        return {**body, "enrollment_ref": reference}

    @classmethod
    def from_wire(cls, value: object) -> InitialAuthoringEnrollmentEvidence:
        if type(value) is not dict or set(value) != set(cls.__dataclass_fields__):
            raise ValueError("initial_authoring_enrollment_fields_invalid")
        evidence = cls(**value)
        evidence.to_wire()
        return evidence


def enrollment_evidence(**fields: object) -> InitialAuthoringEnrollmentEvidence:
    """Construct detached evidence; this function issues no live capability."""
    body = {"schema_id": SCHEMA, "profile": PROFILE, **fields}
    return InitialAuthoringEnrollmentEvidence.from_wire(
        {
            **body,
            "enrollment_ref": "workspace-initial-enrollment:sha256:"
            + hashlib.sha256(_canonical(body)).hexdigest(),
        }
    )


def initial_reference(domain: str, body: object) -> str:
    return domain + ":sha256:" + hashlib.sha256(_canonical(body)).hexdigest()


@dataclass(frozen=True, slots=True)
class InitialConfigurationRequest:
    """Exact initial manifest intent. A strict request is still not admission."""

    enrollment_ref: str
    execution_id: str
    idempotency_key: str
    configuration_json: str
    request_ref: str

    def __post_init__(self):
        self.to_wire()

    def to_wire(self):
        if any(
            type(value) is not str
            for value in (
                self.enrollment_ref,
                self.execution_id,
                self.idempotency_key,
                self.configuration_json,
                self.request_ref,
            )
        ):
            raise ValueError("initial_configuration_request_types_invalid")
        config = json.loads(self.configuration_json)
        if (
            type(config) is not dict
            or set(config)
            != {
                "repository_root",
                "issue_root",
                "goal_root",
                "project_root",
                "content_utf8",
                "source_sha256",
            }
            or any(type(value) is not str for value in config.values())
            or _canonical(config).decode("utf-8") != self.configuration_json
            or len(self.configuration_json.encode("utf-8")) > 32768
            or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}", self.idempotency_key)
            is None
            or re.fullmatch(
                r"workspace-initial-enrollment:sha256:[0-9a-f]{64}", self.enrollment_ref
            )
            is None
            or re.fullmatch(r"(?:codex|claude_code)-[^\s]+", self.execution_id) is None
            or config["source_sha256"]
            != "sha256:"
            + hashlib.sha256(config["content_utf8"].encode("utf-8")).hexdigest()
        ):
            raise ValueError("initial_configuration_request_invalid")
        body = {
            "schema_id": "aware.workspace.initial-authoring-request.v1",
            "profile": PROFILE,
            "operation_key": "publish_initial_configuration",
            "enrollment_ref": self.enrollment_ref,
            "execution_id": self.execution_id,
            "idempotency_key": self.idempotency_key,
            "selected_ref": "refs/heads/main",
            "expected_head": None,
            "target_path": "aware.protocol.toml",
            "preimage": "absent",
            "configuration": config,
        }
        if self.request_ref != initial_reference("workspace-initial-request", body):
            raise ValueError("initial_configuration_request_reference_invalid")
        return {**body, "request_ref": self.request_ref}

    @classmethod
    def from_wire(cls, wire):
        if type(wire) is not dict or set(wire) != {
            "schema_id",
            "profile",
            "operation_key",
            "enrollment_ref",
            "execution_id",
            "idempotency_key",
            "selected_ref",
            "expected_head",
            "target_path",
            "preimage",
            "configuration",
            "request_ref",
        }:
            raise ValueError("initial_configuration_request_fields_invalid")
        request = cls(
            wire["enrollment_ref"],
            wire["execution_id"],
            wire["idempotency_key"],
            _canonical(wire["configuration"]).decode("utf-8"),
            wire["request_ref"],
        )
        # Exact-type equality: True/1 and false/0 cannot be accepted as null or
        # version fields by Python's normal equality rules.
        if _canonical(wire) != _canonical(request.to_wire()):
            raise ValueError("initial_configuration_request_constants_invalid")
        return request


def configuration_request(enrollment, config, idempotency_key):
    body = {
        "schema_id": "aware.workspace.initial-authoring-request.v1",
        "profile": PROFILE,
        "operation_key": "publish_initial_configuration",
        "enrollment_ref": enrollment.enrollment_ref,
        "execution_id": enrollment.execution_id,
        "idempotency_key": idempotency_key,
        "selected_ref": "refs/heads/main",
        "expected_head": None,
        "target_path": "aware.protocol.toml",
        "preimage": "absent",
        "configuration": config.to_wire(),
    }
    return InitialConfigurationRequest.from_wire(
        {**body, "request_ref": initial_reference("workspace-initial-request", body)}
    )
