"""Exact Goal byte-effect claims and original publication handles.

Goal owns semantic validation. These data codecs grant no authority; only the
selected owner's retained plan/admission enters its original publication engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from .authority import _selected_owner
from .values import PROFILE, InitialProjectRequest, _canonical, initial_reference

_SOURCE_TYPES = set()
_STATE_TYPES = set()
_STATES = WeakKeyDictionary()
_PINS = WeakKeyDictionary()
_RESERVATIONS = WeakKeyDictionary()
_LOCK = threading.Lock()


def _ref(value, domain):
    if (
        type(value) is not str
        or re.fullmatch(re.escape(domain) + r":sha256:[0-9a-f]{64}", value) is None
    ):
        raise ValueError("initial_goal_publication_reference_invalid")


@dataclass(frozen=True, slots=True)
class InitialGoalPublicationRequest:
    source_json: str
    idempotency_key: str
    request_ref: str

    def __post_init__(self):
        self.to_wire()

    def to_wire(self) -> dict[str, Any]:
        if type(self.source_json) is not str or len(self.source_json.encode()) > 180000:
            raise ValueError("initial_goal_publication_source_limit")
        source = json.loads(self.source_json)
        if (
            type(source) is not dict
            or set(source)
            != {
                "schema_id",
                "context",
                "project_request",
                "intent_permission",
                "goal_plan",
                "repository_root",
                "execution_id",
                "target_path",
                "expected_head",
                "parent_preimages",
                "content_utf8",
                "content_sha256",
                "source_ref",
            }
            or _canonical(source).decode() != self.source_json
        ):
            raise ValueError("initial_goal_publication_source_shape")
        context, permission, plan = (
            source["context"],
            source["intent_permission"],
            source["goal_plan"],
        )
        if any(type(value) is not dict for value in (context, permission, plan)):
            raise ValueError("initial_goal_publication_nested_shape")
        if set(context) != {
            "schema_id",
            "repository_root",
            "execution_id",
            "enrollment_ref",
            "issuer_ref",
            "issuer_generation",
            "assurance",
            "selected_ref",
            "source_revision",
            "source_inventory_sha256",
            "manifest_sha256",
            "protocol_digest",
            "protocol_profile",
            "goal_record_profile",
            "goal_root",
            "goal_template",
            "project_request_ref",
            "project_path",
            "project_blob_oid",
            "project_publication_ref",
            "project_projection_ref",
            "target_path",
            "parent_preimages",
            "coverage",
            "creation_permission",
            "source_ref",
        } or set(permission) != {
            "schema_id",
            "profile",
            "operation_key",
            "source",
            "intent_utf8",
            "intent_sha256",
            "idempotency_key",
            "issuer_ref",
            "issuer_generation",
            "publication_admission",
            "issued_at",
            "expires_at",
            "permission_ref",
        }:
            raise ValueError("initial_goal_publication_nested_fields")
        if any(
            type(value) is not str
            for name, value in context.items()
            if name != "parent_preimages"
        ) or any(
            type(value) is not str
            for name, value in permission.items()
            if name != "source"
        ):
            raise ValueError("initial_goal_publication_nested_types")
        project = InitialProjectRequest.from_wire(source["project_request"])
        if (
            type(self.idempotency_key) is not str
            or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}", self.idempotency_key)
            is None
            or source["schema_id"] != "aware.workspace.initial-goal-postimage-source.v1"
            or context.get("schema_id")
            != "aware.workspace.initial-goal-source-context.v1"
            or permission.get("schema_id")
            != "aware.workspace.initial-goal-intent-permission.v1"
            or permission.get("profile") != PROFILE
            or permission.get("operation_key") != "authorize_proposed_goal_intent"
            or permission.get("publication_admission") != "not_issued"
            or _canonical(permission.get("source")) != _canonical(context)
            or permission.get("idempotency_key") != self.idempotency_key
            or permission["issuer_ref"] != context["issuer_ref"]
            or permission["issuer_generation"] != context["issuer_generation"]
            or context["coverage"] != "complete_first_project_tree"
            or context["creation_permission"] != "not_issued"
            or context["selected_ref"] != "refs/heads/main"
            or context["assurance"] != "local_fresh_repository_execution_correlation"
            or context["protocol_profile"] != "aware.collaboration.fs_v4"
            or context["goal_record_profile"] != "aware.goal.native.markdown.v2"
            or context["enrollment_ref"] != project.enrollment_ref
            or type(source["parent_preimages"]) is not list
            or source["repository_root"] != context.get("repository_root")
            or source["execution_id"] != context.get("execution_id")
            or source["execution_id"] != project.execution_id
            or source["target_path"] != context.get("target_path")
            or source["expected_head"] != context.get("source_revision")
            or type(source["expected_head"]) is not str
            or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source["expected_head"])
            is None
            or _canonical(source["parent_preimages"])
            != _canonical(context.get("parent_preimages"))
            or project.request_ref != context.get("project_request_ref")
            or project.source["repository_root"] != source["repository_root"]
            or type(source["content_utf8"]) is not str
            or not 0 < len(source["content_utf8"].encode()) <= 131072
            or source["content_utf8"] != plan.get("carrier_utf8")
            or source["content_sha256"] != plan.get("carrier_sha256")
            or source["content_sha256"]
            != "sha256:" + hashlib.sha256(source["content_utf8"].encode()).hexdigest()
            or type(permission.get("intent_utf8")) is not str
            or permission.get("intent_utf8", "").encode()
            != _canonical(plan.get("request"))
            or permission["intent_sha256"]
            != "sha256:"
            + hashlib.sha256(permission["intent_utf8"].encode()).hexdigest()
        ):
            raise ValueError("initial_goal_publication_source_binding")
        path = source["target_path"]
        if (
            type(path) is not str
            or not path.isascii()
            or len(path) > 2048
            or "\\" in path
            or any(p in {"", ".", "..", ".git"} for p in path.split("/"))
            or any(ord(c) < 32 for c in path)
        ):
            raise ValueError("initial_goal_publication_target_invalid")
        parts = path.split("/")
        parents = source["parent_preimages"]
        if len(parts) > 65 or len(parents) != len(parts) - 1:
            raise ValueError("initial_goal_publication_parent_census_invalid")
        absent = False
        for index, parent in enumerate(parents, 1):
            if type(parent) is not dict or parent.get("path") != "/".join(
                parts[:index]
            ):
                raise ValueError("initial_goal_publication_parent_census_invalid")
            if parent.get("state") == "absent":
                if set(parent) != {"path", "state"}:
                    raise ValueError("initial_goal_publication_parent_census_invalid")
                absent = True
            elif (
                absent
                or parent.get("state") != "directory"
                or set(parent) != {"path", "state", "identity", "mode"}
                or type(parent["identity"]) is not list
                or len(parent["identity"]) != 2
                or any(type(item) is not int or item < 0 for item in parent["identity"])
                or type(parent["mode"]) is not int
                or not 0 <= parent["mode"] <= 0o7777
            ):
                raise ValueError("initial_goal_publication_parent_census_invalid")
        for body, field, domain in (
            (context, "source_ref", "workspace-initial-goal-source-context"),
            (permission, "permission_ref", "workspace-initial-goal-intent-permission"),
            (source, "source_ref", "workspace-initial-goal-postimage-source"),
        ):
            _ref(body.get(field), domain)
            if body[field] != initial_reference(
                domain, {k: v for k, v in body.items() if k != field}
            ):
                raise ValueError("initial_goal_publication_nested_digest")
        body = {
            "schema_id": "aware.workspace.initial-goal-request.v1",
            "profile": PROFILE,
            "operation_key": "publish_initial_goal_intent",
            "source": source,
            "idempotency_key": self.idempotency_key,
        }
        if self.request_ref != initial_reference(
            "workspace-initial-goal-request", body
        ):
            raise ValueError("initial_goal_publication_request_digest")
        return {**body, "request_ref": self.request_ref}

    @property
    def source(self) -> dict[str, Any]:
        return self.to_wire()["source"]

    @property
    def execution_id(self):
        return self.source["execution_id"]

    @property
    def enrollment_ref(self):
        return self.source["context"]["enrollment_ref"]

    @classmethod
    def from_wire(cls, raw):
        if type(raw) is not dict or set(raw) != {
            "schema_id",
            "profile",
            "operation_key",
            "source",
            "idempotency_key",
            "request_ref",
        }:
            raise ValueError("initial_goal_publication_request_fields")
        value = cls(
            _canonical(raw["source"]).decode(),
            raw["idempotency_key"],
            raw["request_ref"],
        )
        if _canonical(value.to_wire()) != _canonical(raw):
            raise ValueError("initial_goal_publication_request_constants")
        return value


def goal_publication_request(source, key):
    body = {
        "schema_id": "aware.workspace.initial-goal-request.v1",
        "profile": PROFILE,
        "operation_key": "publish_initial_goal_intent",
        "source": source,
        "idempotency_key": key,
    }
    return InitialGoalPublicationRequest.from_wire(
        {
            **body,
            "request_ref": initial_reference("workspace-initial-goal-request", body),
        }
    )


class InitialGoalPublicationPlan:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use original Workspace plan_initial_goal")

    def __copy__(self):
        raise TypeError("initial_goal_publication_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_goal_publication_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_goal_publication_not_serializable")

    @property
    def request(self):
        state = _state(self, InitialGoalPublicationPlan)
        return InitialGoalPublicationRequest.from_wire(state.request.to_wire())


class InitialGoalPublicationAdmission(InitialGoalPublicationPlan):
    __slots__ = ()


def _state(handle, kind):
    state = _STATES.get(handle) if type(handle) is kind else None
    pins = _PINS.get(handle) if type(handle) is kind else None
    if (
        state is None
        or type(state) not in _STATE_TYPES
        or pins is None
        or state.pins() != pins
    ):
        raise ValueError("initial_goal_publication_handle_not_issued_or_mutated")
    state.validate()
    return state


def _issue(owner, state, kind):
    if (
        not _selected_owner(owner)
        or state.owner is not owner
        or type(state) not in _STATE_TYPES
        or kind not in (InitialGoalPublicationPlan, InitialGoalPublicationAdmission)
    ):
        raise ValueError("original_initial_goal_publication_required")
    handle = object.__new__(kind)
    _STATES[handle], _PINS[handle] = state, state.pins()
    return handle


class _GoalReservation:
    pass


def _reservation(owner, state):
    # Current source is required at admission and again by the physical spender
    # immediately before durable reservation. Do not invent another issuer.
    state.validate()
    claim = _GoalReservation()
    with _LOCK:
        _RESERVATIONS[claim] = (owner, state, os.getpid(), state.pins())
    return claim


def _spend_goal_reservation(physical, claim):
    with _LOCK:
        value = (
            _RESERVATIONS.pop(claim, None) if type(claim) is _GoalReservation else None
        )
    if value is None:
        raise ValueError("original_initial_goal_reservation_required")
    owner, state, pid, pins = value
    if (
        owner._physical is not physical
        or pid != os.getpid()
        or state.pins() != pins
        or state.phase != "reserving"
    ):
        raise ValueError("initial_goal_reservation_binding_mismatch")
    state.validate(current=True)
    return state.request, state.workspace_plan.binding


def _retire_reservation(claim):
    with _LOCK:
        _RESERVATIONS.pop(claim, None)


def _require_source(owner, source):
    if type(source) not in _SOURCE_TYPES:
        raise ValueError("original_goal_postimage_source_required")
    return source._workspace_goal_publication_input(owner)
