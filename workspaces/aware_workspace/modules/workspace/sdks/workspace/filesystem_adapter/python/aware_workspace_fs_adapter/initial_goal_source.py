"""Concrete first-Goal source observation through the original Project chain.

Facts are limited local source evidence. No Goal semantics, permission issuer,
repository writer, target creation, repair or durable attempt lives here.
"""

from __future__ import annotations

import hashlib
import os
import stat

from aware_protocol_fs_adapter import require_project_resolver
from aware_protocol_fs_adapter.native_goal_resolver import (
    require_planning_goal_resolver,
)
from aware_workspace_sdk.initial_authoring.values import (
    InitialProjectRequest,
    initial_reference,
)

from .initial_authoring import (
    _projection_stat,
    _root_and_metadata,
    project_attempt,
    project_preimage,
)
from .initial_authoring import (
    observe as observe_enrollment,
)


def observe(port, project_request, capability, target_path):
    if type(project_request) is not InitialProjectRequest:
        raise ValueError("exact_initial_project_request_required")
    project_request.to_wire()
    selected = require_project_resolver(capability)
    goal = require_planning_goal_resolver(selected.goal_capability)
    if type(target_path) is not str or not target_path.isascii():
        raise ValueError("initial_goal_writer_path_profile_unavailable")
    source = project_request.source
    if (
        selected.repository_root != port._root
        or source["repository_root"] != str(port._root)
        or selected.manifest_sha256 != source["manifest_sha256"]
    ):
        raise ValueError("initial_goal_source_repository_or_manifest_mismatch")
    selected.resolve_project_path(source["target_path"])
    goal.resolve_goal_path(target_path)
    enrollment = observe_enrollment(port, confirm_durability=True, _attempt=True)
    if enrollment.execution_id != project_request.execution_id:
        raise ValueError("initial_goal_source_execution_mismatch")
    with project_attempt(port, project_request) as attempt:
        original = attempt.recover()
        if original["disposition"] != "recorded":
            raise ValueError("initial_goal_original_project_required")
        projected = attempt.project_project(read_only=True)
        if projected["projection_state"] != "installed":
            raise ValueError("initial_goal_project_projection_unavailable")
        revision = original["original_result"].commit_hash
        tree = port._git("ls-tree", "-r", "--name-only", "-z", revision)
        if set(tree.split("\0")) - {""} != {
            "aware.protocol.toml",
            source["target_path"],
        }:
            raise ValueError("initial_goal_first_project_tree_required")
        parents = project_preimage(port, target_path)
        with _root_and_metadata(port) as (_, metadata_fd, _, _):
            index = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            if not stat.S_ISREG(index.st_mode) or index.st_nlink != 1:
                raise ValueError("initial_goal_regular_index_required")
            if port._git("diff", "--cached", "--name-only", "-z"):
                raise ValueError("initial_goal_clean_index_required")
            project_blob = port._git(
                "rev-parse", revision + ":" + source["target_path"]
            )
            selected.resolve_project_path(source["target_path"])
            goal.resolve_goal_path(target_path)
            if project_preimage(port, target_path) != parents:
                raise ValueError("initial_goal_target_preimage_changed")
            terminal = attempt.project_project(read_only=True)
            if (
                terminal["projection_state"] != "installed"
                or terminal["projection"]["projection_ref"]
                != projected["projection"]["projection_ref"]
            ):
                raise ValueError("initial_goal_project_projection_changed")
            # Terminal Project qualification can race with an untracked target
            # or parent change. Reobserve without refreshing the frozen preimage.
            if project_preimage(port, target_path) != parents:
                raise ValueError("initial_goal_target_preimage_changed")
            if _projection_stat(
                os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            ) != _projection_stat(index):
                raise ValueError("initial_goal_index_changed")
            # HEAD must be checked after ALL at-use path resolutions and source
            # checks, not before a resolver can observe a concurrent commit.
            if port._head() != ("refs/heads/main", revision):
                raise ValueError("initial_goal_repository_head_advanced")
        body = {
            "schema_id": "aware.workspace.initial-goal-source-context.v1",
            "repository_root": str(port._root),
            "execution_id": enrollment.execution_id,
            "enrollment_ref": enrollment.enrollment_ref,
            "issuer_ref": enrollment.issuer_ref,
            "issuer_generation": enrollment.issuer_generation,
            "assurance": enrollment.assurance,
            "selected_ref": "refs/heads/main",
            "source_revision": revision,
            "source_inventory_sha256": "sha256:"
            + hashlib.sha256(tree.encode()).hexdigest(),
            "manifest_sha256": selected.manifest_sha256,
            "protocol_digest": selected.protocol_digest,
            "protocol_profile": goal.protocol_profile,
            "goal_record_profile": goal.goal_record_profile,
            "goal_root": goal.goal_root,
            "goal_template": goal.goal_template,
            "project_request_ref": project_request.request_ref,
            "project_path": source["target_path"],
            "project_blob_oid": project_blob,
            "project_publication_ref": original["publication"]["publication_ref"],
            "project_projection_ref": projected["projection"]["projection_ref"],
            "target_path": target_path,
            "parent_preimages": parents,
            "coverage": "complete_first_project_tree",
            "creation_permission": "not_issued",
        }
        return {
            **body,
            "source_ref": initial_reference(
                "workspace-initial-goal-source-context", body
            ),
        }
