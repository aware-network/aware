"""Initial membership byte-effect claims; only the original owner admits them.

Codecs check closed transport joins, not Project policy or Git authority.
Decoded requests cannot restore a live plan, reservation or admission.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from .authority import _selected_owner
from .goal_publication import InitialGoalPublicationRequest
from .values import PROFILE, _canonical, initial_reference

_STATES = WeakKeyDictionary()
_PINS = WeakKeyDictionary()
_STATE_TYPES = set()
_RESERVATIONS = WeakKeyDictionary()
_LOCK = threading.Lock()


def _object(value, fields):
    if type(value) is not dict or set(value) != set(fields.split()):
        raise ValueError("initial_membership_claim_fields_invalid")
    return value


def _ref(value, domain):
    if (
        type(value) is not str
        or re.fullmatch(re.escape(domain) + r":sha256:[0-9a-f]{64}", value) is None
    ):
        raise ValueError("initial_membership_claim_reference_invalid")


def _derived(value, domain, field):
    _ref(value[field], domain)
    if value[field] != initial_reference(
        domain, {k: v for k, v in value.items() if k != field}
    ):
        raise ValueError("initial_membership_claim_digest_mismatch")


@dataclass(frozen=True, slots=True)
class InitialMembershipRequest:
    source_json: str
    idempotency_key: str
    request_ref: str

    def __post_init__(self):
        self.to_wire()

    @property
    def source(self):
        self.to_wire()
        return json.loads(self.source_json)

    @property
    def execution_id(self):
        return self.source["execution_id"]

    @property
    def enrollment_ref(self):
        return InitialGoalPublicationRequest.from_wire(
            self.source["preparation"]["source"]["goal_creation_request"]
        ).enrollment_ref

    def to_wire(self):
        if type(self.source_json) is not str or len(self.source_json.encode()) > 230000:
            raise ValueError("initial_membership_source_limit")
        source = _object(
            json.loads(self.source_json),
            "schema_id preparation repository_root execution_id expected_head target_path before_content_utf8 content_utf8 source_ref",
        )
        if (
            _canonical(source).decode() != self.source_json
            or source["schema_id"] != "aware.workspace.initial-membership-source.v1"
        ):
            raise ValueError("initial_membership_source_noncanonical")
        preparation = _object(
            source["preparation"],
            "schema_id request plan source assurance permission membership_state preparation_ref",
        )
        facts = _object(
            preparation["source"],
            "repository_root execution_id selected_ref revision manifest_sha256 project_path project_blob_oid project_content_utf8 project_creation_request goal_creation_request goal_creation_publication goal_creation_projection goal_reading",
        )
        plan = _object(
            preparation["plan"],
            "schema_id request before after content_utf8 content_sha256 plan_ref",
        )
        intent = _object(
            preparation["request"], "schema_id project_key goal_tag request_ref"
        )
        for record in (plan["before"], plan["after"]):
            record = _object(
                record, "schema_id project_key title priority_level status goal_tags"
            )
            if (
                any(type(record[k]) is not str for k in record if k != "goal_tags")
                or type(record["goal_tags"]) is not list
                or any(type(tag) is not str for tag in record["goal_tags"])
            ):
                raise ValueError("initial_membership_record_types_invalid")
        goal = InitialGoalPublicationRequest.from_wire(facts["goal_creation_request"])
        publication = _object(
            facts["goal_creation_publication"],
            "schema_id admission_ref request_ref original_result publication_ref",
        )
        projection = _object(
            facts["goal_creation_projection"],
            "schema_id intent target effects projection_ref",
        )
        _object(
            projection["intent"],
            "schema_id publication_ref request_ref commit target_path preimage physical_profile directory_paths",
        )
        reading = _object(
            facts["goal_reading"],
            "schema_id document planning_status source caller reading_ref",
        )
        _object(
            reading["source"],
            "revision path blob_oid manifest_sha256 publication_ref projection_ref origin_intent_ref source_context_ref project_path project_publication_ref",
        )
        _object(reading["caller"], "execution_id profile assurance")
        if (
            projection["schema_id"] != "aware.workspace.initial-goal-projection.v1"
            or type(projection["effects"]) is not list
            or type(projection["target"]) is not dict
        ):
            raise ValueError("initial_membership_projection_claim_invalid")
        from ..repository_publication.codec import (
            repository_publication_value_from_payload,
        )
        from ..repository_publication.values import WorkspaceRepositoryCommitResult

        result = repository_publication_value_from_payload(
            WorkspaceRepositoryCommitResult, publication["original_result"]
        )
        _ref(publication["admission_ref"], "workspace-initial-admission")
        if (
            preparation["schema_id"]
            != "aware.project.initial-membership-preparation.v1"
            or preparation["assurance"]
            != "local_fresh_repository_execution_correlation"
            or preparation["permission"] != "not_issued"
            or preparation["membership_state"] != "not_published"
            or facts["selected_ref"] != "refs/heads/main"
            or plan["schema_id"] != "aware.project.goal-membership-plan.v1"
            or intent["schema_id"] != "aware.project.goal-membership-request.v1"
            or _canonical(intent) != _canonical(plan["request"])
            or publication["schema_id"]
            != "aware.workspace.initial-authoring-publication.v1"
            or publication["request_ref"] != goal.request_ref
            or result.publication_state != "published"
            or not result.ledger_complete
            or result.expected_head != goal.source["expected_head"]
            or publication["admission_ref"] != result.work_admission_receipt_ref
            or result.updated_reference != "refs/heads/main"
            or result.reference_update != "cas_applied"
            or result.admission_completion != "completed"
            or result.index_projection != "applied"
            or projection["intent"]["publication_ref"] != publication["publication_ref"]
            or projection["intent"]["request_ref"] != goal.request_ref
            or projection["intent"]["commit"] != source["expected_head"]
            or projection["intent"]["target_path"] != goal.source["target_path"]
            or source["expected_head"] != facts["revision"]
            or source["expected_head"] != result.commit_hash
            or source["repository_root"] != facts["repository_root"]
            or source["repository_root"] != goal.source["repository_root"]
            or source["execution_id"] != facts["execution_id"]
            or source["execution_id"] != goal.execution_id
            or source["target_path"] != facts["project_path"]
            or source["target_path"] != goal.source["context"]["project_path"]
            or source["before_content_utf8"] != facts["project_content_utf8"]
            or source["content_utf8"] != plan["content_utf8"]
            or _canonical(facts["project_creation_request"])
            != _canonical(goal.source["project_request"])
            or any(type(source[k]) is not str for k in source if k != "preparation")
            or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source["expected_head"])
            is None
            or not 0 < len(source["content_utf8"].encode()) <= 131072
            or plan["content_sha256"]
            != "sha256:" + hashlib.sha256(source["content_utf8"].encode()).hexdigest()
            or not 0 < len(source["before_content_utf8"].encode()) <= 131072
            or type(self.idempotency_key) is not str
            or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}", self.idempotency_key)
            is None
        ):
            raise ValueError("initial_membership_claim_binding_mismatch")
        path = source["target_path"]
        if (
            not path.isascii()
            or len(path) > 2048
            or "\\" in path
            or any(p in {"", ".", "..", ".git"} for p in path.split("/"))
            or any(ord(c) < 32 for c in path)
        ):
            raise ValueError("initial_membership_target_invalid")
        for value, domain, field in (
            (intent, "project-goal-membership-request", "request_ref"),
            (plan, "project-goal-membership-plan", "plan_ref"),
            (publication, "workspace-initial-publication", "publication_ref"),
            (projection, "workspace-initial-goal-projection", "projection_ref"),
            (reading, "goal-initial-planning-reading", "reading_ref"),
            (preparation, "project-initial-membership-preparation", "preparation_ref"),
            (source, "workspace-initial-membership-source", "source_ref"),
        ):
            _derived(value, domain, field)
        body = {
            "schema_id": "aware.workspace.initial-membership-request.v1",
            "profile": PROFILE,
            "operation_key": "attach_created_goal_membership",
            "source": source,
            "idempotency_key": self.idempotency_key,
        }
        if type(self.request_ref) is not str or self.request_ref != initial_reference(
            "workspace-initial-membership-request", body
        ):
            raise ValueError("initial_membership_request_reference_invalid")
        return {**body, "request_ref": self.request_ref}

    @classmethod
    def from_wire(cls, wire):
        wire = _object(
            wire, "schema_id profile operation_key source idempotency_key request_ref"
        )
        if (
            wire["schema_id"] != "aware.workspace.initial-membership-request.v1"
            or wire["profile"] != PROFILE
            or wire["operation_key"] != "attach_created_goal_membership"
        ):
            raise ValueError("initial_membership_request_profile_mismatch")
        return cls(
            _canonical(wire["source"]).decode(),
            wire["idempotency_key"],
            wire["request_ref"],
        )


def membership_request(source, key):
    body = {
        "schema_id": "aware.workspace.initial-membership-request.v1",
        "profile": PROFILE,
        "operation_key": "attach_created_goal_membership",
        "source": source,
        "idempotency_key": key,
    }
    return InitialMembershipRequest.from_wire(
        {
            **body,
            "request_ref": initial_reference(
                "workspace-initial-membership-request", body
            ),
        }
    )


class InitialMembershipPlan:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use original Workspace plan_initial_membership")

    def __copy__(self):
        raise TypeError("initial_membership_handle_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_membership_handle_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_membership_handle_not_serializable")

    @property
    def request(self):
        return InitialMembershipRequest.from_wire(
            _state(self, type(self)).request.to_wire()
        )


class InitialMembershipAdmission(InitialMembershipPlan):
    __slots__ = ()


def _state(handle, kind):
    if kind not in (InitialMembershipPlan, InitialMembershipAdmission):
        raise ValueError("initial_membership_handle_kind_invalid")
    state = _STATES.get(handle) if type(handle) is kind else None
    if (
        state is None
        or type(state) not in _STATE_TYPES
        or state.pins() != _PINS.get(handle)
    ):
        raise ValueError("initial_membership_handle_not_issued_or_mutated")
    state.validate()
    return state


def _issue(owner, state, kind):
    if (
        not _selected_owner(owner)
        or state.owner is not owner
        or type(state) not in _STATE_TYPES
        or kind not in (InitialMembershipPlan, InitialMembershipAdmission)
    ):
        raise ValueError("original_initial_membership_owner_required")
    handle = object.__new__(kind)
    _STATES[handle], _PINS[handle] = state, state.pins()
    return handle


class _Reservation:
    pass


def _reservation(owner, state):
    state.validate()
    token = _Reservation()
    with _LOCK:
        _RESERVATIONS[token] = (owner, state, os.getpid(), state.pins())
    return token


def _spend_membership_reservation(physical, token):
    with _LOCK:
        retained = (
            _RESERVATIONS.pop(token, None) if type(token) is _Reservation else None
        )
    if retained is None:
        raise ValueError("original_membership_reservation_required")
    owner, state, pid, pins = retained
    if (
        owner._physical is not physical
        or pid != os.getpid()
        or state.pins() != pins
        or state.phase != "reserving"
    ):
        raise ValueError("initial_membership_reservation_mismatch")
    state.validate(current=True)
    return state.request, state.workspace_plan.binding


def _retire_reservation(token):
    with _LOCK:
        _RESERVATIONS.pop(token, None)
