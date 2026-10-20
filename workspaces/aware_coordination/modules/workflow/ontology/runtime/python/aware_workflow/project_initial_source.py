"""Bounded local first-Project provider, not an Identity or Service View issuer.

Only the original fresh-root Workspace enrollment/configuration chain qualifies
this first Project. Protocol provides location admission; Project retains its
meaning. Later Project edits/membership and neutral installed packaging are not
admitted by this source composition.
"""

from __future__ import annotations

import json
import os
from typing import Any
from weakref import WeakKeyDictionary

from aware_protocol_fs_adapter import require_project_resolver
from aware_protocol_fs_adapter.project_templates import match_project_path
from aware_workspace_sdk.initial_authoring.authority import (
    InitialProjectSource,
)
from aware_workspace_sdk.initial_authoring.values import (
    InitialProjectRequest,
)
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryCommitResult,
    WorkspaceRepositoryPublicationClient,
)
from aware_workspace_sdk.repository_publication.authority import _CLIENT_PROVIDERS

from .project_create_contract import ProjectCreateRequestV1, canonical, reference
from .project_create_runtime import plan_project_context_creation
from .project_read_contract import ProjectGoalsContentV1
from .project_read_runtime import ProjectReadInput, read_project_goals
from .project_source_codec import decode_project_context_toml


def _workspace(client):
    owner = (
        _CLIENT_PROVIDERS.get(client)
        if type(client) is WorkspaceRepositoryPublicationClient
        else None
    )
    if owner is None or client._provider is not owner:
        raise ValueError("original_initial_project_workspace_required")
    owner._current()
    return owner


def validate_initial_project_descriptor(source):
    """Recompute domain law; this validates data, not original publication."""
    if type(source) is not dict:
        raise ValueError("exact initial Project source required")
    # The Workspace envelope owns concrete shape/reference/epoch validation.
    from aware_workspace_sdk.initial_authoring.values import project_request

    project_request(source, "descriptor-validation")
    from aware_workspace_sdk.initial_authoring.configuration_successor import (
        project_configuration_request,
    )

    config_request = project_configuration_request(source)
    config = config_request.to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("initial_project_configuration_invalid")
    submitted = source["project_plan"]
    request = ProjectCreateRequestV1.from_wire(submitted["request"])
    plan = plan_project_context_creation(request)
    prefix = config["project_root"] + "/"
    if (
        canonical(submitted) != canonical(plan.to_wire())
        or source["manifest_sha256"] != config["source_sha256"]
        or not source["target_path"].startswith(prefix)
        or match_project_path(
            "project-<slug>.toml", source["target_path"][len(prefix) :]
        )
        is None
    ):
        raise ValueError("initial_project_descriptor_mismatch")
    return plan


def prepare_initial_project_source(
    *,
    workspace,
    resolver_capability,
    protocol_plan,
    configuration_idempotency_key,
    target_path,
    request: ProjectCreateRequestV1,
    configuration_origin=None,
):
    """Read-only preparation; the actual key is authored, not the location slug."""
    owner = _workspace(workspace)
    capability = require_project_resolver(resolver_capability)
    if capability.repository_root != owner._physical._root:
        raise ValueError("initial_project_repository_mismatch")
    location = capability.resolve_project_path(target_path)
    if location.relative_path != target_path:
        raise ValueError("initial_project_target_substituted")
    original: dict[str, Any]
    if configuration_origin is None:
        original = workspace.observe_initial_configuration_projection(
            protocol_plan, idempotency_key=configuration_idempotency_key
        )
    else:
        observed_origin = workspace.observe_initial_configuration_origin(current=True)
        if (
            canonical(observed_origin) != canonical(configuration_origin)
            or observed_origin["kind"] != "successor"
        ):
            raise ValueError("initial_project_successor_origin_changed")
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_from_payload,
        )

        effective = observed_origin["effective"]
        original = {
            "projection_state": "installed",
            "original_result": repository_publication_value_from_payload(
                WorkspaceRepositoryCommitResult,
                effective["publication"]["original_result"],
            ),
            "publication": effective["publication"],
            "projection": effective["projection"],
        }
    if original.get("projection_state") != "installed":
        raise ValueError("initial_project_configuration_projection_unavailable")
    result = original["original_result"]
    if (
        type(result) is not WorkspaceRepositoryCommitResult
        or type(original["publication"]) is not dict
        or type(original["projection"]) is not dict
    ):
        raise ValueError("initial_project_configuration_result_invalid")
    plan = plan_project_context_creation(request)
    body = {
        "schema_id": "aware.project.initial-source.v1"
        if configuration_origin is None
        else "aware.project.initial-source.v2",
        "repository_root": str(capability.repository_root),
        "execution_id": owner._execution,
        "configuration_publication_ref": original["publication"]["publication_ref"],
        "configuration_projection_ref": original["projection"]["projection_ref"],
        "expected_head": result.commit_hash,
        "manifest_sha256": capability.manifest_sha256,
        "target_path": target_path,
        "project_plan": plan.to_wire(),
        "parent_preimages": owner._physical.observe_initial_project_preimage(
            target_path
        ),
    }
    if configuration_origin is None:
        body["configuration_request"] = original["configuration_request"]
    else:
        body["configuration_origin"] = configuration_origin
    descriptor = {**body, "source_ref": reference("project-initial-source", body)}
    validate_initial_project_descriptor(descriptor)
    return workspace.prepare_initial_project_source(
        descriptor,
        resolver_capability=capability,
        protocol_plan=protocol_plan,
        configuration_idempotency_key=configuration_idempotency_key,
    )


def require_initial_project_source(physical, source, *, current=False):
    """Compatibility spelling for the original Workspace exact-byte verifier."""
    if type(source) is not InitialProjectSource:
        raise ValueError("original_initial_project_source_required")
    return physical.require_initial_project_source(source, current=current)


class InitialProjectReading:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use show_initial_project")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial Project reading is not copyable or serializable")

    def to_wire(self):
        retained = _READINGS.get(self) if type(self) is InitialProjectReading else None
        if retained is None or retained[0] != os.getpid():
            raise ValueError("initial_project_reading_not_issued")
        owner = _workspace(retained[1])
        if owner._execution != retained[5]:
            raise ValueError("initial_project_reading_execution_mismatch")
        return json.loads(retained[4])

    @property
    def content(self):
        return ProjectGoalsContentV1.from_wire(self.to_wire()["content"])

    def require_current(self):
        retained = _READINGS.get(self)
        if retained is None:
            raise ValueError("initial_project_reading_not_issued")
        current = show_initial_project(
            workspace=retained[1],
            resolver_capability=retained[2],
            publication_request=retained[3],
        )
        if canonical(current.to_wire()) != retained[4]:
            raise ValueError("initial_project_reading_stale")


_READINGS = WeakKeyDictionary()


def show_initial_project(*, workspace, resolver_capability, publication_request):
    """Qualify local caller/origin/current source before existing pure reduction.

    This is a complete-empty local reading, not a Service View observation.
    No Goal/Issue reader is created merely because the manifest declares roots.
    """
    owner = _workspace(workspace)
    capability = require_project_resolver(resolver_capability)
    if type(publication_request) is not InitialProjectRequest:
        raise ValueError("exact initial Project publication request required")
    source = publication_request.source
    plan = validate_initial_project_descriptor(source)
    if (
        capability.repository_root != owner._physical._root
        or str(capability.repository_root) != source["repository_root"]
        or capability.manifest_sha256 != source["manifest_sha256"]
        or owner._execution != source["execution_id"]
    ):
        raise ValueError("initial_project_reading_caller_or_manifest_mismatch")
    capability.resolve_project_path(source["target_path"])
    observed = workspace.observe_initial_project_projection(publication_request)
    if observed.get("projection_state") != "installed":
        raise ValueError("initial_project_reading_source_unavailable")
    result = observed["original_result"]
    blob = owner._physical._git(
        "rev-parse", result.commit_hash + ":" + source["target_path"]
    )
    # The original provider independently verified this exact committed blob and
    # projection against the frozen plan; no worktree metadata is interpreted.
    record = decode_project_context_toml(plan.content)
    content = read_project_goals(ProjectReadInput("available", record, ()))
    wire = {
        "content": content.to_wire(),
        "source": {
            "revision": result.commit_hash,
            "path": source["target_path"],
            "blob_oid": blob,
            "manifest_sha256": source["manifest_sha256"],
            "publication_ref": observed["publication"]["publication_ref"],
            "projection_ref": observed["projection"]["projection_ref"],
            "origin_ref": source["source_ref"],
        },
        "caller": {
            "execution_id": owner._execution,
            "assurance": "local_fresh_repository_execution_correlation",
            "profile": "initial_project_author_local_v1",
        },
    }
    capability.resolve_project_path(source["target_path"])
    terminal = workspace.observe_initial_project_projection(publication_request)
    if (
        terminal.get("projection_state") != "installed"
        or terminal["publication"]["publication_ref"]
        != observed["publication"]["publication_ref"]
        or terminal["projection"]["projection_ref"]
        != observed["projection"]["projection_ref"]
    ):
        raise ValueError("initial_project_reading_source_changed")
    if owner._physical._head() != ("refs/heads/main", result.commit_hash):
        raise ValueError("initial_project_reading_head_advanced")
    owner._current()
    reading = object.__new__(InitialProjectReading)
    _READINGS[reading] = (
        os.getpid(),
        workspace,
        capability,
        publication_request,
        canonical(wire),
        owner._execution,
    )
    return reading
