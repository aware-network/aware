"""Original FS provider checks for exact initial Project membership admission.

No second Git writer or new issuer. Replacement uses original FileSystem effects.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import stat
from datetime import UTC, datetime
from types import MappingProxyType

from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.initial_authoring.values import _canonical

from .initial_authoring import (
    _InitialCreationProjection,
    _private,
    _projection_stat,
    _read_record,
)


def validate_source(source):
    original = importlib.import_module("aware_workflow.project_initial_membership")
    return original.validate_membership_publication_input(source)


def preimage(source):
    content = source["before_content_utf8"].encode()
    return {
        "path": source["target_path"],
        "state": "file",
        "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "mode": 0o100644,
        "body": content,
    }


def verify_origin(port, request, *, current=False):
    _verify_source(port, request.source, current=current)


def _verify_source(port, source, *, current=False):
    validate_source(source)
    facts = source["preparation"]["source"]
    goal = InitialGoalPublicationRequest.from_wire(facts["goal_creation_request"])
    with port.initial_goal_attempt(goal) as attempt:
        recovered = attempt.recover()
        if (
            recovered["disposition"] != "recorded"
            or recovered["original_result"].commit_hash != source["expected_head"]
            or _canonical(recovered["publication"])
            != _canonical(facts["goal_creation_publication"])
        ):
            raise ValueError("initial_membership_original_goal_mismatch")
        actual_blob = port._git(
            "rev-parse", source["expected_head"] + ":" + goal.source["target_path"]
        )
        if actual_blob != facts["goal_reading"]["source"]["blob_oid"]:
            raise ValueError("initial_membership_goal_blob_mismatch")
        if current:
            if port._head() != (
                "refs/heads/main",
                source["expected_head"],
            ) or port._postimage(source["target_path"]) != preimage(source):
                raise ValueError("initial_membership_source_not_current")
            # Historical/blob resolution must precede the original projection's
            # coherent Goal/Project/manifest index-and-HEAD barrier. Do not do
            # another source lookup after that final currentness qualification.
            observed = attempt.project_goal(read_only=True)
            if observed.get("projection_state") != "installed" or _canonical(
                observed["projection"]
            ) != _canonical(facts["goal_creation_projection"]):
                raise ValueError("initial_membership_goal_projection_unavailable")


def _postimage(source):
    content = source["content_utf8"].encode()
    return {
        **preimage(source),
        "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "body": content,
    }


def _postimage_digest(postimage):
    digest_body = {
        "profile": "workspace-postimages-v1",
        "paths": [{key: value for key, value in postimage.items() if key != "body"}],
    }
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(digest_body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )


def staging_snapshot(capture, binding):
    """Detached immutable postimages, joined to the original admission binding."""
    if type(capture.initial_source_json) is not bytes:
        raise ValueError("initial_membership_original_capture_source_required")
    source = json.loads(capture.initial_source_json)
    validate_source(source)
    postimage = _postimage(source)
    if (
        capture.initial_profile != "initial_membership"
        or binding.repository_ref != source["repository_root"]
        or binding.expected_head != source["expected_head"]
        or binding.publication_reference != "refs/heads/main"
        or binding.target_paths != (source["target_path"],)
        or binding.postimages_digest != _postimage_digest(postimage)
        or binding.message_digest
        != "sha256:" + hashlib.sha256(b"Attach created Goal to Project").hexdigest()
    ):
        raise ValueError("initial_membership_staging_admission_mismatch")
    return (MappingProxyType(postimage),)


def verify_staged_index(port, index, runner, command_log, snapshot, binding):
    """Verify the actual isolated stage and pin its exact immutable Git tree."""
    if not index.enabled or index.transaction_index_path is None:
        raise ValueError("initial_membership_isolated_index_required")
    item = snapshot[0]
    path = item["path"]
    oid = port._git("hash-object", "--stdin", input=item["body"])

    def read(*args):
        return port._membership_stage_read(index, runner, command_log, args)

    before = index.transaction_index_path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError("initial_membership_regular_isolated_index_required")
    staged = read("ls-files", "--stage", "-z", "--", path)
    changed = read("diff", "--cached", "--name-only", "-z", binding.expected_head)
    if (
        staged != f"100644 {oid} 0\t{path}\0"
        or changed != path + "\0"
        or _projection_stat(before)
        != _projection_stat(index.transaction_index_path.lstat())
    ):
        raise ValueError("initial_membership_staged_index_mismatch")
    # write-tree can update the index cache. Check the resulting immutable tree,
    # not the capture or a path observation made before that operation.
    tree = read("write-tree").strip()
    if (
        port._git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-z",
            "-r",
            binding.expected_head,
            tree,
        )
        != path + "\0"
        or port._git("ls-tree", "-z", tree, "--", path)
        != f"100644 blob {oid}\t{path}\0"
    ):
        raise ValueError("initial_membership_staged_tree_mismatch")
    return tree


def verify_capture(port, capture):
    """Requalify the original frozen replacement before physical publication."""
    if type(capture.initial_source_json) is not bytes:
        raise ValueError("initial_membership_original_capture_source_required")
    source = json.loads(capture.initial_source_json)
    expected_postimage = _postimage(source)
    if (
        capture.expected_head != source["expected_head"]
        or capture.repository_ref != source["repository_root"]
        or capture.publication_reference != "refs/heads/main"
        or capture.request.target_paths != (source["target_path"],)
        or capture.preimages != (preimage(source),)
        or capture.postimages != (expected_postimage,)
        or capture.postimages_digest != _postimage_digest(expected_postimage)
        or capture.request.message != "Attach created Goal to Project"
        or capture.message_digest
        != "sha256:" + hashlib.sha256(capture.request.message.encode()).hexdigest()
    ):
        raise ValueError("initial_membership_capture_source_mismatch")
    _verify_source(port, source, current=True)


class MembershipAttempt(_InitialCreationProjection):
    def recover(self):
        if not set(os.listdir(self.directory)).issubset(
            {
                "lock",
                "admission.json",
                "dispatch.json",
                "result.json",
                "projection-start.json",
                "projection-result.json",
            }
        ):
            raise ValueError("initial_membership_unexpected_attempt_event")
        return super().recover()

    def observe_admission(self):
        if set(os.listdir(self.directory)) != {"lock", "admission.json"}:
            raise ValueError("initial_membership_unexpected_attempt_event")
        descriptor = os.open(
            "admission.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=self.directory,
        )
        try:
            _private(os.fstat(descriptor), 0o600)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(self.directory)
        os.fsync(self.parent_directory)
        observed = _read_record(self.directory, "admission.json")
        if _canonical(observed) != _canonical(self.record) or set(
            os.listdir(self.directory)
        ) != {"lock", "admission.json"}:
            raise ValueError("initial_membership_admission_changed")
        return observed

    def _publication_source(self):
        source = self.record["request"]["source"]
        return (
            source["target_path"],
            source["content_utf8"].encode(),
            source["expected_head"],
            "Attach created Goal to Project",
        )

    def consume(self, admission=None):
        from aware_workspace_runtime.initial_membership import (
            require_initial_membership_dispatch,
        )

        request = require_initial_membership_dispatch(self.port, self, admission)
        now = datetime.now(UTC)
        if (
            not datetime.fromisoformat(self.record["issued_at"])
            <= now
            < datetime.fromisoformat(self.record["expires_at"])
        ):
            raise ValueError("initial_membership_dispatch_authority_expired")
        verify_origin(
            self.port,
            # The genuine live admission and original attempt were checked
            # above; this exact request is not another permission entrance.
            request,
            current=True,
        )
        return super().consume()

    def _verify_original_result(self, result):
        super()._verify_original_result(result)
        source = self.record["request"]["source"]
        old = preimage(source)
        blob = self.port._git("hash-object", "--stdin", input=old["body"])
        if (
            self.port._git(
                "ls-tree", "-z", source["expected_head"], "--", source["target_path"]
            )
            != f"100644 blob {blob}\t{source['target_path']}\0"
        ):
            raise ValueError("initial_membership_original_preimage_mismatch")

    def project_configuration(self, *, read_only=False):
        raise ValueError("initial_membership_projection_not_enabled")

    def project_membership(self, *, read_only=False):
        from .initial_membership_projection import project_membership

        return project_membership(self, read_only=read_only)
