"""Original A1 Issue authority IO; no Workspace callback during consumption."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath
from uuid import uuid4

from aware_file_system import confined_mutation as native
from aware_issue_runtime import parse_issue_projection
from aware_protocol_fs_adapter import (
    FilesystemProtocolProfile,
    admit_protocol_manifest_bytes,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceSetupFileObservation,
    WorkspaceSetupResourceEvidence,
)

from .provider import FilesystemIssueOperationLimits, FilesystemIssueOperationProvider
from .source_change import _execution


class FilesystemIssueSetupPort:
    def __init__(
        self,
        *,
        repository_root: Path,
        execution_id: str,
        authority_manifest_locator: str,
    ):
        from aware_workspace_sdk.architecture_setup_admission_codec import _location

        if (
            type(repository_root) is not type(Path())
            or not repository_root.is_absolute()
            or repository_root.resolve(strict=True) != repository_root
        ):
            raise ValueError("original_issue_setup_root_required")
        _location(
            authority_manifest_locator,
            "authority_manifest_locator",
            absolute=False,
            maximum=1024,
        )
        if PurePosixPath(authority_manifest_locator).name != "aware.protocol.toml":
            raise ValueError("explicit_authority_manifest_required")
        self.root = repository_root
        self.execution = execution_id
        self.locator = authority_manifest_locator
        info = os.lstat(self.root)
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError("issue_setup_root_directory_required")
        self.identity = (info.st_dev, info.st_ino)
        self.generation = "issue-setup-generation:" + uuid4().hex
        self.resources = []
        self.ledger_complete = True
        self.closed = False
        self.provider = FilesystemIssueOperationProvider(
            repository_root=repository_root,
            protocol_source_ref=authority_manifest_locator,
            limits=FilesystemIssueOperationLimits(source_bytes=1048576),
        )
        self.current()

    def current(self):
        if self.closed or _execution() != self.execution:
            raise ValueError("issue_setup_execution_not_current")
        info = os.lstat(self.root)
        if (
            not stat.S_ISDIR(info.st_mode)
            or (info.st_dev, info.st_ino) != self.identity
        ):
            raise ValueError("issue_setup_root_changed")

    def _adopt_read(self, ledger):
        self.ledger_complete = self.ledger_complete and not (
            ledger.acquisition_unknown
            or ledger.release_unknown
            or ledger.context_unknown
        )
        for row in ledger.resources:
            unknown = (
                ledger.acquisition_unknown
                or ledger.release_unknown
                or ledger.context_unknown
            )
            self.resources.append(
                WorkspaceSetupResourceEvidence(
                    row.resource_ref,
                    "aware.issue.setup-a1.fs.v1",
                    row.kind,
                    row.path,
                    "unknown" if unknown else "released",
                    row.spent,
                    "unknown" if unknown else "confirmed",
                    (),
                )
            )

    def _read(self, path):
        if len(self.resources) + len(path.split("/")) + 1 > 16384:
            raise ValueError("issue_setup_resource_record_limit")
        try:
            view, info, ledger = native._observe_confined_file_with_custody(
                root=self.root, path=path, maximum_bytes=1048576
            )
        except native.ConfinedFileObservationError as error:
            ledger = getattr(error, "_original_read_ledger", None)
            if type(ledger) is native._ReadLedger:
                self._adopt_read(ledger)
            else:
                self.ledger_complete = False
            raise
        self._adopt_read(ledger)
        if not view.observation.exists or info is None or info.st_nlink != 1:
            raise ValueError("issue_setup_authority_regular_unique_file_required")
        body = view.observation.content
        if type(body) is not bytes:
            raise ValueError("original_issue_setup_body_required")
        return (
            body,
            (
                info.st_dev,
                info.st_ino,
                info.st_mode,
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns,
            ),
            WorkspaceSetupFileObservation(
                "observed",
                True,
                info.st_dev,
                info.st_ino,
                info.st_mode,
                len(body),
                info.st_mtime_ns,
                info.st_ctime_ns,
                "sha256:" + hashlib.sha256(body).hexdigest(),
            ),
        )

    def read_sources(self, issue_ref):
        from aware_workspace_sdk.architecture_setup_admission_codec import _location

        self.current()
        _location(issue_ref, "issue_ref", absolute=False, maximum=1024)
        issue, identity, issue_observation = self._read(issue_ref)
        manifest, manifest_identity, manifest_observation = self._read(self.locator)
        if len(issue) + len(manifest) > 2097152:
            raise ValueError("issue_setup_authority_body_limit")
        admission = admit_protocol_manifest_bytes(
            source=manifest, repository_root=self.root
        )
        if (
            admission.admission.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1
            or type(admission.filesystem_profile) is not FilesystemProtocolProfile
        ):
            raise ValueError("issue_setup_manifest_refused")
        binding = next(
            (
                row
                for row in admission.filesystem_profile.record_bindings
                if row.record_key == "issue"
            ),
            None,
        )
        if binding is None or not issue_ref.startswith(binding.root + "/"):
            raise ValueError("issue_setup_path_outside_authority")
        projection = parse_issue_projection(
            text=issue.decode("utf-8"), source_path=issue_ref
        )
        selected = self.provider._mutation_target(
            operation_ref="issue_sdk.workspace_setup_a1", issue_ref=projection.tag or ""
        )
        if type(selected) is not tuple or selected[1] != issue_ref:
            raise ValueError("issue_setup_authority_identity_or_path_mismatch")
        if self.provider._duplicate_identity_diagnostics(
            profile=selected[0],
            expected_issue_ref=projection.tag or "",
            selected_path=selected[2],
        ):
            raise ValueError("issue_setup_duplicate_authority_identity")
        self.current()
        return (
            (issue, identity, manifest, manifest_identity),
            projection,
            issue_observation,
            manifest_observation,
        )

    def release(self):
        self.closed = True
        return tuple(self.resources), self.ledger_complete
