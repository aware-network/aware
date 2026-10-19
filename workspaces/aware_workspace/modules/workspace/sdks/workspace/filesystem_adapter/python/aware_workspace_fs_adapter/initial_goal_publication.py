"""Initial Goal exact-effect verification using the original retained attempts.

The original engine publishes, projects and recovers. This module supplies its
Goal source profile, not another installer or an interpretation of Gate meaning.
"""

from __future__ import annotations

import os
import stat
from datetime import UTC, datetime

from aware_workspace_sdk.initial_authoring.values import (
    InitialProjectRequest,
    _canonical,
)

from .initial_authoring import (
    _InitialCreationProjection,
    _private,
    _projection_stat,
    _read_record,
    _root_and_metadata,
    project_attempt,
)
from .initial_goal_intent import _content, _validate


def verify_origin(port, request):
    """Historical issuance proof; never restores permission or claims currentness."""
    source = request.source
    project = InitialProjectRequest.from_wire(source["project_request"])
    context = source["context"]
    with project_attempt(port, project) as attempt:
        original = attempt.recover()
        if (
            original["disposition"] != "recorded"
            or original["original_result"].commit_hash != source["expected_head"]
            or original["publication"]["publication_ref"]
            != context["project_publication_ref"]
        ):
            raise ValueError("initial_goal_original_project_mismatch")
        permission = _validate(
            _read_record(attempt.directory, "goal-intent.json"),
            _content(
                context,
                _canonical(source["goal_plan"]["request"]),
                request.idempotency_key,
            ),
        )
        if _canonical(permission) != _canonical(source["intent_permission"]):
            raise ValueError("initial_goal_original_permission_mismatch")
        descriptor = os.open(
            "goal-intent.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=attempt.directory,
        )
        try:
            _private(os.fstat(descriptor), 0o600)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(attempt.directory)
        if _canonical(
            _read_record(attempt.directory, "goal-intent.json")
        ) != _canonical(permission):
            raise ValueError("initial_goal_original_permission_changed")
    if (
        str(port._root) != source["repository_root"]
        or context["enrollment_ref"] != project.enrollment_ref
        or context["selected_ref"] != "refs/heads/main"
    ):
        raise ValueError("initial_goal_original_source_mismatch")


class GoalAttempt(_InitialCreationProjection):
    _projection_kind = "goal"

    def project_configuration(self, *, read_only=False):
        # Reuse only the original admission/dispatch/result machinery. The
        # configuration projector cannot be inherited as a Goal write entrance.
        raise ValueError("initial_goal_projection_not_enabled")

    def _publication_source(self):
        source = self.record["request"]["source"]
        return (
            source["target_path"],
            source["content_utf8"].encode("utf-8"),
            source["expected_head"],
            "Create Proposed Goal intent",
        )

    def project_goal(self, *, read_only=False):
        return self._project_creation(read_only=read_only)

    def _project_current(self, result):
        target, content = super()._project_current(result)
        source = self.record["request"]["source"]
        project = InitialProjectRequest.from_wire(source["project_request"])
        # The old Project reading is historical at H0, not magically current at
        # H1. Qualify its unchanged physical projection against ORIGINAL effects
        # without calling its H0-only currentness entrance or repairing it.
        with project_attempt(self.port, project) as attempt:
            record = _read_record(attempt.directory, "projection-result.json")
            intent = _read_record(attempt.directory, "projection-start.json")
            expected_intent = {
                "schema_id": "aware.workspace.initial-project-projection-intent.v1",
                "publication_ref": source["context"]["project_publication_ref"],
                "request_ref": project.request_ref,
                "commit": source["expected_head"],
                "target_path": source["context"]["project_path"],
                "preimage": "absent",
                "physical_profile": "descriptor_walk_v1",
                "directory_paths": [
                    item["path"]
                    for item in project.source["parent_preimages"]
                    if item["state"] == "absent"
                ],
            }
            if (
                type(record) is not dict
                or record.get("projection_ref")
                != source["context"]["project_projection_ref"]
                or _canonical(intent) != _canonical(expected_intent)
            ):
                raise ValueError("initial_goal_project_projection_binding_mismatch")
            attempt._verify_project_projection(
                record,
                expected_intent,
                project.source["project_plan"]["content_utf8"].encode(),
            )
            project_path, project_content, _, _ = attempt._publication_source()
            project_blob = self.port._git(
                "hash-object", "--stdin", input=project_content
            )
            if (
                self.port._git("ls-files", "--stage", "-z", "--", project_path)
                != f"100644 {project_blob} 0\t{project_path}\0"
            ):
                raise ValueError("initial_goal_project_index_mismatch")
        from aware_workspace_sdk.initial_authoring.values import (
            InitialConfigurationRequest,
        )

        from .initial_authoring import configuration_attempt

        config_request = InitialConfigurationRequest.from_wire(
            project.source["configuration_request"]
        )
        config = config_request.to_wire()["configuration"]
        if type(config) is not dict:
            raise ValueError("initial_goal_manifest_source_invalid")
        with configuration_attempt(self.port, config_request) as attempt:
            record = _read_record(attempt.directory, "projection-result.json")
            intent = _read_record(attempt.directory, "projection-start.json")
            if (
                type(record) is not dict
                or record.get("projection_ref")
                != project.source["configuration_projection_ref"]
            ):
                raise ValueError("initial_goal_manifest_projection_binding_mismatch")
            attempt._verify_projection(record, intent, config["content_utf8"].encode())
            blob = self.port._git(
                "hash-object", "--stdin", input=config["content_utf8"].encode()
            )
            if (
                self.port._git("ls-files", "--stage", "-z", "--", "aware.protocol.toml")
                != f"100644 {blob} 0\taware.protocol.toml\0"
            ):
                raise ValueError("initial_goal_manifest_index_mismatch")
        # Rechecking only Goal against a new index snapshot can hide a Project
        # change during the manifest check. Observe every participating entry
        # together, with one stable no-follow index observation, at the barrier.
        super()._project_current(result)
        goal_blob = self.port._git("hash-object", "--stdin", input=content)
        entries = sorted(
            (
                (target, goal_blob),
                (project_path, project_blob),
                ("aware.protocol.toml", blob),
            ),
            key=lambda entry: entry[0].encode("utf-8"),
        )
        with _root_and_metadata(self.port) as (_, metadata_fd, _, _):
            before = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("initial_goal_regular_index_required")
            observed = self.port._git(
                "ls-files", "--stage", "-z", "--", *(path for path, _ in entries)
            )
            if observed != "".join(
                f"100644 {oid} 0\t{path}\0" for path, oid in entries
            ):
                raise ValueError("initial_goal_participating_index_mismatch")
            if self.port._head() != ("refs/heads/main", result.commit_hash):
                raise ValueError("initial_goal_projection_head_advanced")
            if _projection_stat(before) != _projection_stat(
                os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            ):
                raise ValueError("initial_goal_participating_index_changed")
        return target, content

    def consume(self):
        now = datetime.now(UTC)
        permission = self.record["request"]["source"]["intent_permission"]
        if not datetime.fromisoformat(
            self.record["issued_at"]
        ) <= now < datetime.fromisoformat(
            self.record["expires_at"]
        ) or not datetime.fromisoformat(
            permission["issued_at"]
        ) <= now < datetime.fromisoformat(permission["expires_at"]):
            raise ValueError("initial_goal_dispatch_authority_expired")
        return super().consume()
