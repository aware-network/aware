"""Thin source-level Project customer composition over the accepted owners.

No new reducer, issuer, store, Git/FS writer or public command. Packaging and
Agent mounting remain separate. Historical selection never restores a grant.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from weakref import WeakKeyDictionary

from aware_protocol_fs_adapter import admit_project_resolver, require_project_resolver
from aware_protocol_fs_adapter.project_bootstrap import (
    prepare_planning_project_configuration,
    require_project_configuration,
)
from aware_workspace_sdk.initial_authoring.authority import InitialProjectPlan
from aware_workspace_sdk.initial_authoring.values import (
    InitialConfigurationRequest,
    InitialProjectRequest,
)
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryPublicationClient,
)
from aware_workspace_sdk.repository_publication.codec import (
    repository_publication_value_to_payload,
)

from .project_create_contract import ProjectCreateRequestV1, canonical
from .project_initial_source import (
    _workspace,
    prepare_initial_project_source,
    show_initial_project,
)
from .project_read_contract import ProjectContextRecordV1, ProjectMetadataV1

_CLIENTS = WeakKeyDictionary()
_CLIENT_PINS = WeakKeyDictionary()
_PLANS = WeakKeyDictionary()
_PLAN_PINS = WeakKeyDictionary()


def _client(client):
    state = (
        _CLIENTS.get(client) if type(client) is InitialProjectCustomerClient else None
    )
    pins = (
        _CLIENT_PINS.get(client)
        if type(client) is InitialProjectCustomerClient
        else None
    )
    if state is None or state != pins or state[0] != os.getpid():
        raise ValueError("original_project_customer_client_required")
    _, workspace, capability, execution = state
    owner = _workspace(workspace)
    selected = require_project_resolver(capability)
    if (
        owner._execution != execution
        or selected.repository_root != owner._physical._root
        or selected.protocol_profile != "aware.collaboration.fs_v4"
    ):
        raise ValueError("project_customer_caller_or_profile_changed")
    return workspace, selected


def _path(capability, name):
    if type(name) is not str or not name or "/" in name or "\\" in name:
        raise ValueError("project_customer_name_invalid")
    target = capability.project_root + "/project-" + name + ".toml"
    if capability.match_project_path(target) != name:
        raise ValueError("project_customer_name_invalid")
    if capability.resolve_project_path(target).relative_path != target:
        raise ValueError("project_customer_target_substituted")
    return target


def _wire_observation(observed):
    """Only transport conversion; original results remain complete."""
    result = dict(observed)
    if "original_result" in result and result["original_result"] is not None:
        result["original_result"] = repository_publication_value_to_payload(
            result["original_result"]
        )
    return result


def _configuration(workspace, capability):
    origin = workspace.observe_initial_configuration_origin(current=True)
    if origin["kind"] == "successor":
        config = origin["effective"]["request"]["configuration"]
        if config["source_sha256"] != capability.manifest_sha256:
            raise ValueError("project_customer_configuration_substituted")
        return None, "configuration-successor-1", origin
    selected = workspace.observe_initial_authoring_request("configuration")
    if (
        selected["state"] != "retained"
        or selected["recovery"]["disposition"] != "recorded"
    ):
        raise ValueError("project_customer_configuration_not_recorded")
    request = selected["request"]
    if type(request) is not InitialConfigurationRequest:
        raise ValueError("project_customer_original_configuration_required")
    config = request.to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("project_customer_configuration_invalid")
    plan = prepare_planning_project_configuration(
        repository_root=config["repository_root"],
        issue_root=config["issue_root"],
        goal_root=config["goal_root"],
        project_root=config["project_root"],
    )
    if (
        canonical(require_project_configuration(plan).to_wire()) != canonical(config)
        or config["source_sha256"] != capability.manifest_sha256
    ):
        raise ValueError("project_customer_configuration_substituted")
    # This reconstructs a read-only Protocol plan, NOT original publication or
    # enrollment authority. The original owner independently verifies both.
    observed = workspace.observe_initial_configuration_projection(
        plan, idempotency_key=request.idempotency_key
    )
    if observed.get("projection_state") != "installed" or canonical(
        observed["publication"]
    ) != canonical(selected["recovery"]["publication"]):
        raise ValueError("project_customer_configuration_projection_unavailable")
    return plan, request.idempotency_key, None


@dataclass
class _PlanState:
    pid: int
    client: InitialProjectCustomerClient
    original: InitialProjectPlan
    client_binding: tuple[object, ...]
    frozen: bytes
    preview: bytes
    phase: str = "prepared"

    def pins(self):
        return (
            self.pid,
            self.client,
            self.original,
            self.client_binding,
            self.frozen,
            self.preview,
        )


def _plan(plan):
    state = _PLANS.get(plan) if type(plan) is ProjectCustomerCreationPlan else None
    pins = _PLAN_PINS.get(plan) if type(plan) is ProjectCustomerCreationPlan else None
    if state is None or pins != state.pins() or state.pid != os.getpid():
        raise ValueError("original_project_customer_plan_required")
    _client(state.client)
    if _CLIENTS.get(state.client) != state.client_binding:
        raise ValueError("project_customer_plan_client_changed")
    if canonical(state.original.request.to_wire()) != state.frozen:
        raise ValueError("project_customer_plan_mutated")
    return state


class ProjectCustomerCreationPlan:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use prepare_create")

    def __copy__(self):
        raise TypeError("project_customer_plan_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("project_customer_plan_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("project_customer_plan_not_serializable")

    def to_wire(self):
        state = _plan(self)
        if state.phase != "prepared":
            raise ValueError("project_customer_preview_spent")
        return json.loads(state.preview)


class InitialProjectCustomerClient:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(self, *, workspace, resolver_capability):
        if type(self) is not InitialProjectCustomerClient:
            raise ValueError("original_project_customer_client_required")
        owner = _workspace(workspace)
        capability = require_project_resolver(resolver_capability)
        state = (os.getpid(), workspace, capability, owner._execution)
        _CLIENTS[self] = _CLIENT_PINS[self] = state
        _client(self)

    @classmethod
    def filesystem(cls, *, repository_root, manifest_path="aware.protocol.toml"):
        if cls is not InitialProjectCustomerClient:
            raise ValueError("original_project_customer_client_required")
        workspace = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=repository_root
        )
        root = Path(repository_root)
        manifest = Path(manifest_path)
        if not manifest.is_absolute():
            manifest = root / manifest
        admission = admit_project_resolver(repository_root=root, manifest_path=manifest)
        if admission.capability is None:
            raise ValueError("project_customer_protocol_admission_unavailable")
        return cls(workspace=workspace, resolver_capability=admission.capability)

    def prepare_create(self, name, *, title, priority="medium", project_key=None):
        workspace, capability = _client(self)
        target = _path(capability, name)
        record = ProjectContextRecordV1(
            ProjectMetadataV1(
                name if project_key is None else project_key,
                title,
                priority,
                "initializing",
            ),
            (),
        )
        intent = ProjectCreateRequestV1.author(record)
        retained = workspace.observe_initial_authoring_request("project")
        if retained["state"] != "absent":
            raise ValueError("project_customer_attempt_retained_use_observe")
        config, key, origin = _configuration(workspace, capability)
        source = prepare_initial_project_source(
            workspace=workspace,
            resolver_capability=capability,
            protocol_plan=config,
            configuration_idempotency_key=key,
            target_path=target,
            request=intent,
            configuration_origin=origin,
        )
        original = workspace.plan_initial_project(
            source, idempotency_key="project-create-" + name
        )
        request = original.request
        preview = {
            "operation": "project_create",
            "disposition": "planned",
            "name": name,
            "project": record.to_wire(),
            "target_path": target,
            "source_revision": request.source["expected_head"],
            "request": request.to_wire(),
            "planned_effects": [
                "publish_project_context",
                "project_project_file",
                "qualified_project_read",
            ],
            "publication_admission": "not_issued",
            "dispatch_effect": "none",
            "assurance": "local_fresh_repository_execution_correlation",
        }
        # Qualify original source/intent after final provider planning; never
        # reconstruct or repair a mutated caller request.
        if canonical(intent.to_wire()) != canonical(
            request.source["project_plan"]["request"]
        ):
            raise ValueError("project_customer_intent_changed")
        capability.resolve_project_path(target)
        source_owner = _workspace(workspace)
        source_owner._physical.require_initial_project_source(source, current=True)
        handle = object.__new__(ProjectCustomerCreationPlan)
        state = _PlanState(
            os.getpid(),
            self,
            original,
            _CLIENTS[self],
            canonical(request.to_wire()),
            canonical(preview),
        )
        _PLANS[handle] = state
        _PLAN_PINS[handle] = state.pins()
        _plan(handle)
        return handle

    def apply_create(self, plan):
        state = _plan(plan)
        if state.client is not self or state.phase != "prepared":
            raise ValueError("project_customer_plan_foreign_or_spent")
        workspace, _ = _client(self)
        request = state.original.request
        state.phase = "applying"
        result = {
            "operation": "project_create",
            "disposition": "uncertain",
            "request": request.to_wire(),
            "authorizes_redispatch": False,
        }
        try:
            admission = workspace.admit_initial_project(state.original)
            original = workspace.publish_initial_project(admission)
            result["original_result"] = repository_publication_value_to_payload(
                original
            )
            recovered = workspace.recover_initial_project(request)
            result["recovery"] = _wire_observation(recovered)
            if (
                recovered["disposition"] != "recorded"
                or original.publication_state != "published"
                or not original.ledger_complete
                or original != recovered["original_result"]
            ):
                return result
            projected = workspace.project_initial_project(request)
            result["projection"] = _wire_observation(projected)
            if projected.get("projection_state") == "installed":
                result["reading"] = self.show(json.loads(state.preview)["name"])
                result["disposition"] = "created"
            return result
        except (OSError, TypeError, ValueError, RuntimeError) as error:
            result["diagnostics"] = [str(error)]
            # Original owner recovery only; never issue new admission or retry
            # a writer to obtain nicer output after a lost acknowledgement.
            try:
                selected = workspace.observe_initial_authoring_request("project")
                if selected["state"] == "retained":
                    if canonical(selected["request"].to_wire()) != state.frozen:
                        raise ValueError("project_customer_recovery_request_changed")
                    result["recovery"] = _wire_observation(selected["recovery"])
            except (OSError, TypeError, ValueError, RuntimeError) as recovery_error:
                result["recovery_diagnostics"] = [str(recovery_error)]
            return result
        finally:
            state.phase = "spent"

    def _selected(self, name):
        workspace, capability = _client(self)
        target = _path(capability, name)
        selected = workspace.observe_initial_authoring_request("project")
        if selected["state"] != "retained":
            raise ValueError("project_customer_no_retained_attempt")
        request = selected["request"]
        if (
            type(request) is not InitialProjectRequest
            or request.source["target_path"] != target
        ):
            raise ValueError("project_customer_selection_mismatch")
        return workspace, capability, request, selected["recovery"]

    def observe(self, name):
        workspace, _, request, recovered = self._selected(name)
        result = {
            "operation": "project_observe",
            "request": request.to_wire(),
            "recovery": _wire_observation(recovered),
            "authorizes_redispatch": False,
        }
        if recovered["disposition"] == "recorded":
            result["projection"] = _wire_observation(
                workspace.observe_initial_project_projection(request)
            )
        return result

    def project(self, name):
        """Explicit exact original projection; never called by show/observe."""
        workspace, _, request, recovered = self._selected(name)
        return {
            "operation": "project_projection",
            "recovery": _wire_observation(recovered),
            "projection": _wire_observation(workspace.project_initial_project(request)),
            "authorizes_redispatch": False,
        }

    def show(self, name):
        workspace, capability, request, recovered = self._selected(name)
        if recovered["disposition"] != "recorded":
            raise ValueError("project_customer_original_publication_unavailable")
        reading = show_initial_project(
            workspace=workspace,
            resolver_capability=capability,
            publication_request=request,
        )
        return {
            "operation": "project_show",
            "reading": reading.to_wire(),
            "publication": recovered["publication"],
        }


def summarize_project_customer(result):
    """Describe owner output, never decide permission or eligibility."""
    if result["operation"] == "project_show":
        project = result["reading"]["content"]["project"]
        return f"Project {project['title']}.\nStatus: {project['status']} · no Goals yet.\nSuggested next step: create a Proposed Goal."
    if result["disposition"] == "planned":
        project = result["project"]
        return f"Create Project {project['title']}?\nPriority: {project['priority_level']}. Target: {result['target_path']}\nNo publication permission issued or files changed. Apply requires explicit initiation."
    if result["disposition"] == "created":
        return "Project created and verified. No work started.\nSuggested next step: create a Proposed Goal."
    return "Project creation is incomplete or uncertain.\nInspect the retained original outcome before continuing; do not repeat creation."
