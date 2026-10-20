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
from typing import Any

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


def _project_configuration_request(source):
    if source.get("schema_id") == "aware.project.initial-source.v2":
        # Optional versioned codec entrance; no static values/successor cycle.
        import importlib

        return importlib.import_module(
            "aware_workspace_sdk.initial_authoring.configuration_successor"
        ).project_configuration_request(source)
    return InitialConfigurationRequest.from_wire(source["configuration_request"])


@dataclass(frozen=True, slots=True)
class InitialProjectRequest:
    """Exact first-Project byte effect, not a Project semantic verdict.

    The Project owner independently validates its intention/initial-state plan.
    Workspace binds these opaque bytes to its own concrete authoring scope;
    neither decoding nor a writer receipt grants domain or execution authority.
    """

    source_json: str
    idempotency_key: str
    request_ref: str

    def __post_init__(self):
        self.to_wire()

    def to_wire(self) -> dict[str, Any]:
        if any(
            type(value) is not str
            for value in (self.source_json, self.idempotency_key, self.request_ref)
        ):
            raise ValueError("initial_project_request_types_invalid")
        source = json.loads(self.source_json)
        successor = (
            type(source) is dict
            and source.get("schema_id") == "aware.project.initial-source.v2"
        )
        if (
            type(source) is not dict
            or set(source)
            != {
                "schema_id",
                "repository_root",
                "execution_id",
                "configuration_origin" if successor else "configuration_request",
                "configuration_publication_ref",
                "configuration_projection_ref",
                "expected_head",
                "manifest_sha256",
                "target_path",
                "parent_preimages",
                "project_plan",
                "source_ref",
            }
            or _canonical(source).decode("utf-8") != self.source_json
            or len(self.source_json.encode("utf-8")) > 524288
        ):
            raise ValueError("initial_project_source_shape_invalid")
        config = _project_configuration_request(source)
        configuration = config.to_wire()["configuration"]
        if type(configuration) is not dict:
            raise ValueError("initial_project_configuration_invalid")
        plan = source["project_plan"]
        if type(plan) is not dict or set(plan) != {
            "schema_id",
            "request",
            "content_utf8",
            "content_sha256",
            "plan_ref",
        }:
            raise ValueError("initial_project_plan_shape_invalid")
        content = plan["content_utf8"]
        path = source["target_path"]
        if (
            source["schema_id"]
            != (
                "aware.project.initial-source.v2"
                if successor
                else "aware.project.initial-source.v1"
            )
            or source["repository_root"] != configuration["repository_root"]
            or source["execution_id"] != config.execution_id
            or type(path) is not str
            or len(path) > 2048
            or any(part in {"", ".", "..", ".git"} for part in path.split("/"))
            or "\\" in path
            or any(ord(c) < 32 for c in path)
            or type(content) is not str
            or not 0 < len(content.encode("utf-8")) <= 262144
            or plan["content_sha256"]
            != "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
            or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}", self.idempotency_key)
            is None
        ):
            raise ValueError("initial_project_request_invalid")
        parents = source["parent_preimages"]
        prefixes = [
            "/".join(path.split("/")[:i]) for i in range(1, len(path.split("/")))
        ]
        if (
            type(parents) is not list
            or len(parents) > 64
            or len(parents) != len(prefixes)
        ):
            raise ValueError("initial_project_parent_inventory_invalid")
        absent = False
        for prefix, item in zip(prefixes, parents, strict=True):
            if type(item) is not dict or item.get("path") != prefix:
                raise ValueError("initial_project_parent_inventory_invalid")
            if item.get("state") == "absent":
                if set(item) != {"path", "state"}:
                    raise ValueError("initial_project_parent_inventory_invalid")
                absent = True
            elif item.get("state") == "directory":
                if (
                    absent
                    or set(item) != {"path", "state", "identity", "mode"}
                    or type(item["identity"]) is not list
                    or len(item["identity"]) != 2
                    or any(type(v) is not int or v < 0 for v in item["identity"])
                    or type(item["mode"]) is not int
                    or not 0 <= item["mode"] <= 0o7777
                ):
                    raise ValueError("initial_project_parent_inventory_invalid")
            else:
                raise ValueError("initial_project_parent_inventory_invalid")
        for key, domain in (
            (
                "configuration_publication_ref",
                "workspace-initial-configuration-successor-publication"
                if successor
                else "workspace-initial-publication",
            ),
            (
                "configuration_projection_ref",
                "workspace-initial-configuration-successor-projection"
                if successor
                else "workspace-initial-configuration-projection",
            ),
            ("manifest_sha256", ""),
        ):
            if (
                type(source[key]) is not str
                or re.fullmatch(
                    (domain + ":" if domain else "") + r"sha256:[0-9a-f]{64}",
                    source[key],
                )
                is None
            ):
                raise ValueError("initial_project_source_reference_invalid")
        if (
            type(source["expected_head"]) is not str
            or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source["expected_head"])
            is None
        ):
            raise ValueError("initial_project_source_epoch_invalid")
        if source["source_ref"] != initial_reference(
            "project-initial-source",
            {k: v for k, v in source.items() if k != "source_ref"},
        ):
            raise ValueError("initial_project_source_reference_invalid")
        if successor:
            effective = source["configuration_origin"]["effective"]
            if (
                source["configuration_publication_ref"]
                != effective["publication"]["publication_ref"]
                or source["configuration_projection_ref"]
                != effective["projection"]["projection_ref"]
                or source["expected_head"]
                != effective["publication"]["original_result"]["commit_hash"]
            ):
                raise ValueError("initial_project_successor_epoch_mismatch")
        body = {
            "schema_id": "aware.workspace.initial-project-request.v2"
            if successor
            else "aware.workspace.initial-project-request.v1",
            "profile": PROFILE,
            "operation_key": "publish_initial_project_context",
            "source": source,
            "idempotency_key": self.idempotency_key,
        }
        if self.request_ref != initial_reference(
            "workspace-initial-project-request", body
        ):
            raise ValueError("initial_project_request_reference_invalid")
        return {**body, "request_ref": self.request_ref}

    @property
    def source(self) -> dict[str, Any]:
        return self.to_wire()["source"]

    @property
    def enrollment_ref(self):
        return _project_configuration_request(self.source).enrollment_ref

    @property
    def execution_id(self):
        return self.source["execution_id"]

    @classmethod
    def from_wire(cls, value):
        if type(value) is not dict or set(value) != {
            "schema_id",
            "profile",
            "operation_key",
            "source",
            "idempotency_key",
            "request_ref",
        }:
            raise ValueError("initial_project_request_fields_invalid")
        result = cls(
            _canonical(value["source"]).decode("utf-8"),
            value["idempotency_key"],
            value["request_ref"],
        )
        if _canonical(result.to_wire()) != _canonical(value):
            raise ValueError("initial_project_request_constants_invalid")
        return result


def project_request(source, idempotency_key):
    body = {
        "schema_id": "aware.workspace.initial-project-request.v2"
        if source.get("schema_id") == "aware.project.initial-source.v2"
        else "aware.workspace.initial-project-request.v1",
        "profile": PROFILE,
        "operation_key": "publish_initial_project_context",
        "source": source,
        "idempotency_key": idempotency_key,
    }
    return InitialProjectRequest.from_wire(
        {
            **body,
            "request_ref": initial_reference("workspace-initial-project-request", body),
        }
    )
