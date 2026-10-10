"""Own Issue source observation, never Workspace SDK/implementation calls."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from .source_change import _read_issue, _target


@dataclass(frozen=True)
class _IssueSource:
    repository_ref: str
    issue_ref: str
    path: str
    digest: str
    identity: tuple
    parents: tuple
    manifest_digest: str
    owner: str
    status: str
    scope: tuple[str, ...]
    body: bytes


class FilesystemIssueRepositorySourcePort:
    def __init__(self, provider):
        from .provider import FilesystemIssueOperationProvider

        if type(provider) is not FilesystemIssueOperationProvider:
            raise TypeError("Original Issue filesystem provider required")
        root = provider._repository_root
        if not root.is_absolute() or root.resolve() != root:
            raise ValueError("canonical_absolute_issue_repository_root_required")
        value = root.stat()
        self._root_identity = (value.st_dev, value.st_ino)
        self._pid = os.getpid()
        self._provider = provider

    def observe(self, issue_ref):
        from aware_issue_runtime import IssueReadProjection

        provider = self._provider
        value = provider._repository_root.stat()
        if (
            os.getpid() != self._pid
            or (value.st_dev, value.st_ino) != self._root_identity
        ):
            raise ValueError("original_issue_repository_source_required")
        path = _target(provider, issue_ref)
        body, identity, parents = _read_issue(provider._repository_root, path)
        profile = provider._admit_manifest()
        if not hasattr(profile, "protocol_manifest"):
            raise ValueError("issue_repository_profile_unavailable")
        projection = provider._parse_projection(
            operation_ref="issue_sdk.admit_repository_publication",
            issue_ref=issue_ref,
            relative_path=path,
            source=body,
        )
        if not isinstance(projection, IssueReadProjection):
            raise TypeError("issue_repository_projection_unavailable")
        if projection.issue_ref != issue_ref:
            raise ValueError("issue_repository_identity_mismatch")
        return _IssueSource(
            str(provider._repository_root),
            issue_ref,
            path,
            "sha256:" + hashlib.sha256(body).hexdigest(),
            identity,
            parents,
            profile.protocol_manifest.digest,
            projection.owner_ref or "",
            projection.status,
            projection.ownership_scope,
            body,
        )

    def retain_closeout(self, original, candidate):
        from aware_file_system.retained_mutation import (
            retain_confined_manifest_replacement,
        )

        if self.observe(original.issue_ref) != original:
            raise ValueError("issue_closeout_source_stale")
        return retain_confined_manifest_replacement(
            root=self._provider._repository_root,
            target_path=original.path,
            expected_content_digest=original.digest,
            content=candidate,
        )

    def validate_closeout(self, original, physical):
        if self.observe(original.issue_ref) != original:
            raise ValueError("issue_closeout_source_stale")
        physical.validate_current()

    def apply_closeout(self, original, physical):
        # The runtime supplies its retained original physical handle. This
        # port decides no Issue lifecycle and never invokes a foreign SDK.
        self.validate_closeout(original, physical)
        physical.replace_manifest()
        physical.finish()
        physical.validate_consumed_current()
        return self.observe(original.issue_ref)


from aware_issue_operational_runtime.repository_publication import _SOURCE_PORT_TYPES

_SOURCE_PORT_TYPES.add(FilesystemIssueRepositorySourcePort)
