"""Closed successor claims and original-owner handles. Decoding issues nothing."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any
from weakref import WeakKeyDictionary

from .authority import _selected_owner
from .values import (
    PROFILE,
    InitialAuthoringEnrollmentEvidence,
    InitialConfigurationRequest,
    _canonical,
    initial_reference,
)

PREFIX = "aware.workspace.initial-configuration-successor-"
DOMAIN = "workspace-initial-configuration-successor-"
MESSAGE = "Publish separately admitted initial configuration successor"
_TYPES = set()
_STATES = WeakKeyDictionary()
_PINS = WeakKeyDictionary()
_CLAIMS = WeakKeyDictionary()
_LOCK = threading.Lock()


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys.split()):
        raise ValueError("configuration_successor_fields_invalid")


def _time(value):
    if type(value) is not str:
        raise ValueError("configuration_successor_time_invalid")
    result = datetime.fromisoformat(value)
    if (
        result.utcoffset() != timedelta(0)
        or result.isoformat(timespec="microseconds") != value
    ):
        raise ValueError("configuration_successor_time_invalid")
    return result


def validate_admission(record, *, successor):
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_from_payload,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryPublicationBinding,
    )

    _closed(record, "schema_id request binding issued_at expires_at admission_ref")
    request = (
        InitialConfigurationSuccessorRequest
        if successor
        else InitialConfigurationRequest
    ).from_wire(record["request"])
    schema = (
        PREFIX + "admission.v1"
        if successor
        else "aware.workspace.initial-authoring-admission.v1"
    )
    domain = DOMAIN + "admission" if successor else "workspace-initial-admission"
    binding = repository_publication_value_from_payload(
        WorkspaceRepositoryPublicationBinding, record["binding"]
    )
    config = request.to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("configuration_successor_configuration_invalid")
    if (
        record["schema_id"] != schema
        or _time(record["expires_at"]) - _time(record["issued_at"])
        != timedelta(seconds=300)
        or record["admission_ref"]
        != initial_reference(
            domain, {k: v for k, v in record.items() if k != "admission_ref"}
        )
        or binding.attempt_ref != request.request_ref
        or binding.execution_id != request.execution_id
        or binding.repository_ref != config["repository_root"]
        or binding.publication_reference != "refs/heads/main"
        or binding.expected_head is not None
        or binding.target_paths != ("aware.protocol.toml",)
    ):
        raise ValueError("configuration_successor_admission_invalid")
    return request


def validate_publication(record, admission, *, successor):
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_to_payload,
    )

    raw_record, raw_admission = (
        _canonical(record).decode(),
        _canonical(admission).decode(),
    )
    if len(raw_record.encode()) > 262144 or len(raw_admission.encode()) > 262144:
        raise ValueError("configuration_successor_publication_limit")
    result = copy.deepcopy(
        _validate_publication_bytes(raw_record, raw_admission, successor)
    )
    # Only exact-byte portable decoding is cached, never authority/currentness.
    # Independent copies cannot poison subsequent decodes or share a grant.
    if _canonical(repository_publication_value_to_payload(result)) != _canonical(
        record["original_result"]
    ):
        raise ValueError("configuration_successor_cached_value_changed")
    return result


@lru_cache(maxsize=32)
def _validate_publication_bytes(raw_record, raw_admission, successor):
    record, admission = json.loads(raw_record), json.loads(raw_admission)
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_from_payload,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryCommitResult,
    )

    request = validate_admission(admission, successor=successor)
    _closed(
        record, "schema_id admission_ref request_ref original_result publication_ref"
    )
    result = repository_publication_value_from_payload(
        WorkspaceRepositoryCommitResult, record["original_result"]
    )
    schema = (
        PREFIX + "publication.v1"
        if successor
        else "aware.workspace.initial-authoring-publication.v1"
    )
    domain = DOMAIN + "publication" if successor else "workspace-initial-publication"
    binding = admission["binding"]
    lock = result.lock_release
    writer = result.original_writer_report
    if (
        record["schema_id"] != schema
        or record["admission_ref"] != admission["admission_ref"]
        or record["request_ref"] != request.request_ref
        or record["publication_ref"]
        != initial_reference(
            domain, {k: v for k, v in record.items() if k != "publication_ref"}
        )
        or result.attempt_ref != request.request_ref
        or result.binding_ref != binding["binding_ref"]
        or result.work_admission_receipt_ref != admission["admission_ref"]
        or result.expected_head is not None
        or result.updated_reference != "refs/heads/main"
        or lock is None
        or (
            lock.binding_ref,
            lock.attempt_ref,
            lock.provider_ref,
            lock.provider_generation,
        )
        != (
            binding["binding_ref"],
            binding["attempt_ref"],
            binding["provider_ref"],
            binding["provider_generation"],
        )
        or (
            writer is not None
            and (
                writer.repository_admission_ref != admission["admission_ref"]
                or writer.owner_id != binding["execution_id"]
                or writer.repo_root != binding["repository_ref"]
                or writer.issue_tag is not None
                or writer.requested_paths != ["aware.protocol.toml"]
                or writer.reference_update != result.reference_update
                or writer.commit_hash != result.commit_hash
                or writer.candidate_commit != result.candidate_commit
                or writer.shared_index_projection != result.index_projection
            )
        )
        or (
            result.publication_state == "published"
            and (
                writer is None
                or result.commit_hash is None
                or result.candidate_commit != result.commit_hash
                or result.reference_update != "cas_applied"
            )
        )
    ):
        raise ValueError("configuration_successor_publication_invalid")
    return result


def validate_predecessor(bundle):
    # Cache only pure structural validation of exact complete bytes, never a
    # live handle/provider verdict. Return a new detached request every time.
    raw = _canonical(bundle).decode()
    return InitialConfigurationRequest.from_wire(
        json.loads(_validate_predecessor_bytes(raw))
    )


@lru_cache(maxsize=32)
def _validate_predecessor_bytes(raw):
    if len(raw.encode()) > 131072:
        raise ValueError("configuration_successor_predecessor_limit")
    bundle = json.loads(raw)
    _closed(bundle, "enrollment admission dispatch publication")
    enrollment = InitialAuthoringEnrollmentEvidence.from_wire(bundle["enrollment"])
    request = validate_admission(bundle["admission"], successor=False)
    _closed(bundle["dispatch"], "schema_id admission_ref request_ref")
    if (
        _canonical(bundle["dispatch"])
        != _canonical(
            {
                "schema_id": "aware.workspace.initial-authoring-dispatch.v1",
                "admission_ref": bundle["admission"]["admission_ref"],
                "request_ref": request.request_ref,
            }
        )
        or request.enrollment_ref != enrollment.enrollment_ref
        or request.execution_id != enrollment.execution_id
    ):
        raise ValueError("configuration_successor_predecessor_invalid")
    validate_publication(bundle["publication"], bundle["admission"], successor=False)
    return _canonical(request.to_wire()).decode()


@dataclass(frozen=True, slots=True)
class InitialConfigurationSuccessorRequest:
    body_json: str
    request_ref: str

    def __post_init__(self):
        self.to_wire()

    def to_wire(self) -> dict[str, Any]:
        if type(self.body_json) is not str or len(self.body_json.encode()) > 131072:
            raise ValueError("configuration_successor_request_limit")
        body = json.loads(self.body_json)
        _closed(
            body,
            "schema_id profile operation_key attempt_number idempotency_key predecessor source configuration",
        )
        original = validate_predecessor(body["predecessor"])
        source = body["source"]
        _closed(
            source,
            "repository_root root_identity metadata_identity git_config_stat git_config_utf8 git_config_sha256 author committer selected_ref expected_head index_state target_path target_state",
        )
        for key, size in (
            ("root_identity", 2),
            ("metadata_identity", 2),
            ("git_config_stat", 7),
        ):
            if (
                type(source[key]) is not list
                or len(source[key]) != size
                or any(type(v) is not int or v < 0 for v in source[key])
            ):
                raise ValueError("configuration_successor_identity_invalid")
        for key in ("author", "committer"):
            _closed(source[key], "name email")
            if any(
                type(v) is not str
                or not v.strip()
                or len(v.encode()) > 1024
                or any(c in v for c in "\r\n<>")
                for v in source[key].values()
            ):
                raise ValueError("configuration_successor_attribution_invalid")
        text = source["git_config_utf8"]
        if (
            type(text) is not str
            or len(text.encode()) > 16384
            or source["git_config_sha256"]
            != "sha256:" + hashlib.sha256(text.encode()).hexdigest()
            or not stat.S_ISREG(source["git_config_stat"][2])
            or source["git_config_stat"][3] != 1
            or source["git_config_stat"][4] != len(text.encode())
        ):
            raise ValueError("configuration_successor_config_invalid")
        enrollment = body["predecessor"]["enrollment"]
        if (
            _canonical(body).decode() != self.body_json
            or body["schema_id"] != PREFIX + "request.v1"
            or body["profile"] != PROFILE
            or body["operation_key"] != "publish_initial_configuration_successor"
            or type(body["attempt_number"]) is not int
            or body["attempt_number"] != 1
            or body["idempotency_key"] != "configuration-successor-1"
            or _canonical(body["configuration"])
            != _canonical(original.to_wire()["configuration"])
            or source["repository_root"] != enrollment["repository_root"]
            or source["root_identity"]
            != [enrollment["root_device"], enrollment["root_inode"]]
            or source["metadata_identity"]
            != [enrollment["metadata_device"], enrollment["metadata_inode"]]
            or source["selected_ref"] != "refs/heads/main"
            or source["expected_head"] is not None
            or source["index_state"] != "absent"
            or source["target_state"] != "absent"
            or source["target_path"] != "aware.protocol.toml"
            or type(self.request_ref) is not str
            or self.request_ref != initial_reference(DOMAIN + "request", body)
        ):
            raise ValueError("configuration_successor_request_invalid")
        return {**body, "request_ref": self.request_ref}

    @classmethod
    def from_wire(cls, wire):
        _closed(
            wire,
            "schema_id profile operation_key attempt_number idempotency_key predecessor source configuration request_ref",
        )
        return cls(
            _canonical({k: v for k, v in wire.items() if k != "request_ref"}).decode(),
            wire["request_ref"],
        )

    @property
    def execution_id(self):
        return self.to_wire()["predecessor"]["enrollment"]["execution_id"]

    @property
    def enrollment_ref(self):
        return self.to_wire()["predecessor"]["enrollment"]["enrollment_ref"]


def successor_request(predecessor, source):
    body = {
        "schema_id": PREFIX + "request.v1",
        "profile": PROFILE,
        "operation_key": "publish_initial_configuration_successor",
        "attempt_number": 1,
        "idempotency_key": "configuration-successor-1",
        "predecessor": predecessor,
        "source": source,
        "configuration": predecessor["admission"]["request"]["configuration"],
    }
    return InitialConfigurationSuccessorRequest.from_wire(
        {**body, "request_ref": initial_reference(DOMAIN + "request", body)}
    )


def validate_origin(wire):
    raw = _canonical(wire).decode()
    if len(raw.encode()) > 262144:
        raise ValueError("configuration_origin_limit")
    _validate_origin_bytes(raw)
    return wire


@lru_cache(maxsize=32)
def _validate_origin_bytes(raw):
    # No currentness or authority is cached. Every different byte sequence is
    # revalidated; concrete custody/source checks always execute at use.
    wire = json.loads(raw)
    _closed(wire, "schema_id kind enrollment predecessor effective origin_ref")
    if len(_canonical(wire)) > 262144:
        raise ValueError("configuration_origin_limit")
    enrollment = InitialAuthoringEnrollmentEvidence.from_wire(wire["enrollment"])
    successor = wire["kind"] == "successor"
    if wire["kind"] not in {"initial", "successor"}:
        raise ValueError("configuration_origin_kind_invalid")
    effect = wire["effective"]
    _closed(effect, "request admission publication projection_intent projection")
    request = validate_admission(effect["admission"], successor=successor)
    if _canonical(effect["request"]) != _canonical(request.to_wire()):
        raise ValueError("configuration_origin_request_invalid")
    result = validate_publication(
        effect["publication"], effect["admission"], successor=successor
    )
    if successor:
        validate_predecessor(wire["predecessor"])
        if _canonical(request.to_wire()["predecessor"]) != _canonical(
            wire["predecessor"]
        ):
            raise ValueError("configuration_origin_predecessor_invalid")
    elif wire["predecessor"] is not None:
        raise ValueError("configuration_origin_predecessor_invalid")
    intent, projection = effect["projection_intent"], effect["projection"]
    _closed(
        intent,
        "schema_id publication_ref request_ref commit target_path preimage physical_profile",
    )
    _closed(projection, "schema_id intent file effect projection_ref")
    schema = (
        PREFIX + "projection"
        if successor
        else "aware.workspace.initial-configuration-projection"
    )
    domain = (
        DOMAIN + "projection"
        if successor
        else "workspace-initial-configuration-projection"
    )
    if (
        wire["schema_id"] != "aware.workspace.initial-configuration-origin.v2"
        or wire["origin_ref"]
        != initial_reference(
            "workspace-initial-configuration-origin",
            {k: v for k, v in wire.items() if k != "origin_ref"},
        )
        or request.enrollment_ref != enrollment.enrollment_ref
        or request.execution_id != enrollment.execution_id
        or not result.ledger_complete
        or result.publication_state != "published"
        or _canonical(intent)
        != _canonical(
            {
                "schema_id": schema + "-intent.v1",
                "publication_ref": effect["publication"]["publication_ref"],
                "request_ref": request.request_ref,
                "commit": result.commit_hash,
                "target_path": "aware.protocol.toml",
                "preimage": "absent",
                "physical_profile": "descriptor_walk_v1",
            }
        )
        or projection["schema_id"] != schema + ".v1"
        or _canonical(projection["intent"]) != _canonical(intent)
        or projection["projection_ref"]
        != initial_reference(
            domain, {k: v for k, v in projection.items() if k != "projection_ref"}
        )
    ):
        raise ValueError("configuration_origin_invalid")
    # The shared original physical evidence codec is consumed by the provider;
    # here bind its exact closed file/effect structure without claiming authority.
    file, effect_record = projection["file"], projection["effect"]
    _closed(file, "stat sha256")
    _closed(
        effect_record,
        "path kind state durability_confirmed mode before_digest after_digest after_identity",
    )
    values = file["stat"]
    config = request.to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("configuration_origin_configuration_invalid")
    if (
        type(values) is not list
        or len(values) != 7
        or any(type(v) is not int or v < 0 for v in values)
        or values[2] != stat.S_IFREG | 0o644
        or values[3] != 1
        or values[4] != len(config["content_utf8"].encode())
        or file["sha256"] != config["source_sha256"]
        or _canonical(effect_record)
        != _canonical(
            {
                "path": "aware.protocol.toml",
                "kind": "file",
                "state": "applied",
                "durability_confirmed": True,
                "mode": 0o644,
                "before_digest": None,
                "after_digest": file["sha256"],
                "after_identity": values[:2],
            }
        )
    ):
        raise ValueError("configuration_origin_projection_invalid")


def project_configuration_request(source):
    """Decode a discriminated Project source; no qualification or permission."""
    if source.get("schema_id") == "aware.project.initial-source.v2":
        origin = validate_origin(source["configuration_origin"])
        if origin["kind"] != "successor":
            raise ValueError("project_successor_origin_required")
        return InitialConfigurationSuccessorRequest.from_wire(
            origin["effective"]["request"]
        )
    return InitialConfigurationRequest.from_wire(source["configuration_request"])


class _SuccessorHandle:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- Python owns weakref storage

    def __new__(cls):
        raise TypeError("original_configuration_successor_handle_required")

    def __copy__(self):
        raise TypeError("configuration_successor_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("configuration_successor_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("configuration_successor_not_portable")


class ConfigurationSuccessorPlan(_SuccessorHandle):
    __slots__ = ()

    @property
    def request(self):
        return InitialConfigurationSuccessorRequest.from_wire(
            _state(self, ConfigurationSuccessorPlan).request.to_wire()
        )

    def to_wire(self):
        state = _state(self, ConfigurationSuccessorPlan)
        return {
            "request": state.request.to_wire(),
            "binding": json.loads(state.binding_wire),
            "authorizes_publication": False,
        }


class ConfigurationSuccessorAdmission(_SuccessorHandle):
    __slots__ = ()


class _Reservation(_SuccessorHandle):
    __slots__ = ()


def _state(handle, kind):
    state = _STATES.get(handle) if type(handle) is kind else None
    if (
        state is None
        or type(state) not in _TYPES
        or _PINS.get(handle) != state.pins()
        or state.pid != os.getpid()
        or not _selected_owner(state.owner)
    ):
        raise ValueError("original_configuration_successor_handle_required")
    state.validate()
    return state


def _issue(state, kind):
    if (
        type(state) not in _TYPES
        or not _selected_owner(state.owner)
        or kind not in (ConfigurationSuccessorPlan, ConfigurationSuccessorAdmission)
    ):
        raise ValueError("original_configuration_successor_state_required")
    state.validate()
    handle = object.__new__(kind)
    _STATES[handle] = state
    _PINS[handle] = state.pins()
    return handle


def _reservation(state):
    if (
        type(state) not in _TYPES
        or not _selected_owner(state.owner)
        or state.pid != os.getpid()
        or state.phase != "reserving"
        or not any(
            value is state and _PINS.get(handle) == state.pins()
            for handle, value in list(_STATES.items())
        )
    ):
        raise ValueError("original_configuration_successor_state_required")
    state.validate()
    handle = object.__new__(_Reservation)
    with _LOCK:
        _CLAIMS[handle] = (state, os.getpid(), state.pins())
    return handle


def _spend(physical, handle):
    with _LOCK:
        item = _CLAIMS.pop(handle, None) if type(handle) is _Reservation else None
    if item is None:
        raise ValueError("configuration_successor_original_reservation_required")
    state, pid, pins = item
    if type(state) not in _TYPES or not _selected_owner(state.owner):
        raise ValueError("original_configuration_successor_state_required")
    state.validate()
    if (
        pid != os.getpid()
        or pins != state.pins()
        or state.owner._physical is not physical
        or state.phase != "reserving"
    ):
        raise ValueError("configuration_successor_reservation_mismatch")
    return state.request, state.workspace_plan.binding


def _retire(handle):
    with _LOCK:
        _CLAIMS.pop(handle, None)
