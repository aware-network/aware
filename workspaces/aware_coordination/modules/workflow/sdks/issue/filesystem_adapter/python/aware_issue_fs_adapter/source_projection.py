"""Issue-owned read/render IO. No Workspace SDK or foreign implementation IO."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from aware_issue_runtime import IssueReadProjection, parse_issue_projection
from aware_issue_sdk import parse_issue_document_text, render_issue_document
from aware_issue_sdk.operation import IssueMutationResult
from aware_issue_sdk.source_projection import IssueSourceProjectionRefusal

from .provider import FilesystemIssueOperationProvider
from .source_change import _execution, _read_issue


class FilesystemIssueProjectionPort:
    def __init__(self, *, repository_root: Path, execution_id: str):
        if (
            not isinstance(repository_root, Path)
            or not repository_root.is_absolute()
            or repository_root.resolve() != repository_root
            or not repository_root.is_dir()
        ):
            raise IssueSourceProjectionRefusal("original_repository_root_required")
        self.root = repository_root
        self.execution_id = execution_id
        original = os.stat(repository_root, follow_symlinks=False)
        self.root_identity = original.st_dev, original.st_ino
        self.provider = FilesystemIssueOperationProvider(
            repository_root=repository_root
        )
        self.check_execution()

    def check_execution(self):
        try:
            current = _execution()
        except BaseException as error:
            raise IssueSourceProjectionRefusal(
                "provider_execution_identity_unavailable"
            ) from error
        if current != self.execution_id:
            raise IssueSourceProjectionRefusal("issue_projection_execution_mismatch")

    def read(self, request):
        self.check_execution()
        try:
            current_root = os.stat(self.root, follow_symlinks=False)
            if (current_root.st_dev, current_root.st_ino) != self.root_identity:
                raise IssueSourceProjectionRefusal("issue_projection_root_changed")
            target = self.provider._mutation_target(
                operation_ref=request.operation_ref, issue_ref=request.issue_ref
            )
            if isinstance(target, IssueMutationResult):
                raise IssueSourceProjectionRefusal(
                    "issue_projection_target_unavailable",
                    diagnostics=target.diagnostics,
                )
            profile, path, _absolute = target
            source, identity, parents = _read_issue(self.root, path)
            manifest, _manifest_identity, _manifest_parents = _read_issue(
                self.root, "aware.protocol.toml"
            )
            projection = self.provider._parse_projection(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                relative_path=path,
                source=source,
            )
            if type(projection) is not IssueReadProjection:
                raise IssueSourceProjectionRefusal("issue_projection_malformed")
            duplicates = self.provider._duplicate_identity_diagnostics(
                profile=profile,
                expected_issue_ref=request.issue_ref,
                selected_path=_absolute,
            )
            if duplicates:
                raise IssueSourceProjectionRefusal(
                    "issue_projection_duplicate_identity", diagnostics=duplicates
                )
            return (path, source, identity, parents, manifest), projection
        except IssueSourceProjectionRefusal:
            raise
        except BaseException as error:
            raise IssueSourceProjectionRefusal(
                "issue_projection_read_unavailable", diagnostics=(type(error).__name__,)
            ) from error

    def operational_inputs(self, request, projection, path):
        return (
            self.provider._operational_state(projection=projection, relative_path=path),
            self.provider._intent_context(request=request, expected_issue_revision=0),
        )

    def render(self, request, source):
        document = parse_issue_document_text(text=source.decode("utf-8"))
        self.provider._set_lifecycle(
            document=document,
            status="In Progress",
            operation_ref=request.operation_ref,
            actor_ref=request.actor_ref,
        )
        return render_issue_document(document=document).encode("utf-8")

    def projected_read(self, request, path, body):
        return parse_issue_projection(text=body.decode("utf-8"), source_path=path)

    @staticmethod
    def digest(body):
        return "sha256:" + hashlib.sha256(body).hexdigest()

    def read_tree_authority(self, request):
        """Original Issue and manifest byte/identity guards; no foreign SDK IO."""
        from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

        try:
            capture, projection = self.read(request)
            manifest, identity, parents = _read_issue(self.root, "aware.protocol.toml")
            if manifest != capture[4]:
                raise IssueTreeProjectionRefusal("issue_tree_manifest_changed")
            return (*capture, identity, parents), projection
        except BaseException as error:
            from aware_issue_sdk.source_change import IssueSourceChangeRefusal

            original = error
            code = getattr(error, "code", "issue_tree_authority_read_unavailable")
            # v0's wrapper stays unchanged; preserve the own reader's precise
            # original refusal (particularly unknown descriptor cleanup) for C.
            for _ in range(32):
                if isinstance(original, IssueSourceChangeRefusal):
                    code = original.code
                    break
                original = original.__cause__
                if original is None:
                    break
            raise IssueTreeProjectionRefusal(code) from error
