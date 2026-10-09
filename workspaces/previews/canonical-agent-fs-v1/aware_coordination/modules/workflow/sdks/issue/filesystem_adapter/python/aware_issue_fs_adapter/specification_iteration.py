"""Read-only Workflow composition over real Protocol, SPEC, Issue and Git reads.

Import explicitly with the ``specification`` extra. Ordinary Issue operations
never import this module or acquire a Specification dependency. The caller
supplies a real live SPEC admission, not decoded source/binding evidence.
"""

import os
import shutil
import subprocess
from pathlib import Path

from aware_issue_sdk import (
    CommittedSpecificationMember,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveResult,
    IssueSpecificationIterationBindingError,
    IssueSpecificationIterationBindingObservation,
    IssueSpecificationIterationBindingObserveRequest,
    SpecificationIterationBindingOutcome,
)
from aware_protocol_fs_adapter import (
    MANIFEST_FILENAME,
    FilesystemProtocolProfile,
    admit_protocol_manifest,
    resolve_repository_path_at_use,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from aware_specification_fs_adapter.observation import (
    mount_namespace_identity,
    validate_source_base,
)
from aware_specification_fs_sdk_adapter import (
    SpecificationIterationAdmission,
    SpecificationIterationSourceEvidence,
    revalidate_specification_iteration_source_evidence,
)
from aware_specification_fs_source_contract.values import canonical_relative_path
from aware_specification_sdk import SpecificationOperationError

from .provider import FilesystemIssueOperationProvider

PROVIDER_REF = "aware_issue_fs_adapter.specification-iteration-pairing.v1"
SPECIFICATION_PATH_TEMPLATE = "<spec-key>/aware.spec.toml"


class FilesystemSpecificationIterationBindingProvider(FilesystemIssueOperationProvider):
    """Retain source admission and actual manifest issuance in one read context.

    No caller-built FilesystemRecordBinding or admission result is accepted.
    The genuine SPEC provider must stay alive; its own retirement rules apply.
    Unique identity is established in the explicit assembled closure, not an
    invented repository-global catalog. No durable binding is created here.
    """

    def __init__(
        self,
        *,
        repository_root: str | Path,
        iteration_admission: SpecificationIterationAdmission,
        protocol_source_ref: str = MANIFEST_FILENAME,
    ) -> None:
        super().__init__(
            repository_root=repository_root, protocol_source_ref=protocol_source_ref
        )
        self._pairing_fd = -1
        self._pairing_closed = False
        try:
            self._selected_root = Path(repository_root).absolute()
            self._pairing_root = self._selected_root.resolve(strict=True)
            self._pairing_fd = os.open(
                self._pairing_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            self._pairing_repository_identity = validate_source_base(self._pairing_fd)
            self._pairing_namespace = mount_namespace_identity()
            self._pairing_admission = iteration_admission
            self._pairing_manifest_sha256, self._pairing_profile = (
                self._fresh_manifest()
            )
            self._pairing_manifest_path = (
                self._pairing_root / protocol_source_ref
            ).resolve(strict=True)
            evidence = self._source_evidence()
            self._check_selection(evidence)
        except (OSError, RuntimeError, TypeError, ValueError, AttributeError) as error:
            self.close()
            if isinstance(error, IssueSpecificationIterationBindingError):
                raise
            raise IssueSpecificationIterationBindingError(
                "pairing_context_unavailable"
            ) from error

    @property
    def manifest_sha256(self) -> str:
        return self._pairing_manifest_sha256

    def close(self) -> None:
        if self._pairing_fd >= 0:
            os.close(self._pairing_fd)
            self._pairing_fd = -1
        self._pairing_closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _check_repository(self) -> None:
        if self._pairing_closed:
            raise IssueSpecificationIterationBindingError("pairing_context_closed")
        try:
            if self._selected_root.resolve(strict=True) != self._pairing_root:
                raise ValueError("repository selection changed")
            fd = os.open(
                self._pairing_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            try:
                if validate_source_base(fd) != self._pairing_repository_identity:
                    raise ValueError("repository replaced")
            finally:
                os.close(fd)
            if (
                validate_source_base(self._pairing_fd)
                != self._pairing_repository_identity
                or mount_namespace_identity() != self._pairing_namespace
            ):
                raise ValueError("repository topology changed")
        except (OSError, ValueError, RuntimeError) as error:
            raise IssueSpecificationIterationBindingError(
                "pairing_repository_changed"
            ) from error

    def _fresh_manifest(self) -> tuple[str, FilesystemProtocolProfile]:
        self._check_repository()
        admission = admit_protocol_manifest(
            repository_root=self._pairing_root,
            manifest_path=self._pairing_root / self._protocol_source_ref,
        )
        if (
            admission.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1
            or admission.filesystem_profile is None
            or admission.source_sha256 is None
        ):
            raise IssueSpecificationIterationBindingError(
                "pairing_manifest_unavailable", diagnostics=admission.diagnostics
            )
        return admission.source_sha256, admission.filesystem_profile

    def _check_manifest(self) -> None:
        digest, profile = self._fresh_manifest()
        if (
            digest != self._pairing_manifest_sha256
            or profile != self._pairing_profile
            or (self._pairing_root / self._protocol_source_ref).resolve(strict=True)
            != self._pairing_manifest_path
        ):
            raise IssueSpecificationIterationBindingError("pairing_manifest_changed")

    def _source_evidence(self) -> SpecificationIterationSourceEvidence:
        try:
            # Mandatory fresh original-provider port. Never inspect its private
            # descriptor, roots, registry, identity fields or cached observation.
            evidence = revalidate_specification_iteration_source_evidence(
                self._pairing_admission
            )
            if type(evidence) is not SpecificationIterationSourceEvidence:
                raise ValueError("wrong source evidence type")
            evidence.__post_init__()
        except (
            SpecificationOperationError,
            AttributeError,
            TypeError,
            ValueError,
        ) as error:
            raise IssueSpecificationIterationBindingError(
                "pairing_specification_admission_refused", diagnostics=(str(error),)
            ) from error
        if (
            evidence.source_base_identity != self._pairing_repository_identity
            or evidence.namespace_identity != self._pairing_namespace
        ):
            raise IssueSpecificationIterationBindingError(
                "pairing_source_repository_mismatch"
            )
        return evidence

    def _check_selection(self, evidence: SpecificationIterationSourceEvidence) -> None:
        binding = next(
            (
                b
                for b in self._pairing_profile.record_bindings
                if b.record_key == "specification"
            ),
            None,
        )
        if binding is None or binding.path_template != SPECIFICATION_PATH_TEMPLATE:
            raise IssueSpecificationIterationBindingError(
                "pairing_specification_binding_unsupported"
            )
        prefix = binding.root + "/"
        for closure in evidence.closures:
            canonical_relative_path(closure.spec_root, "spec_root")
            if (
                not closure.spec_root.startswith(prefix)
                or "/" in closure.spec_root[len(prefix) :]
            ):
                raise IssueSpecificationIterationBindingError(
                    "pairing_specification_outside_binding"
                )
            # The strict owner has already authenticated each manifest's semantic
            # identity and uniqueness across this explicit closure. Directory
            # <spec-key> is a location slot, not another parser of that identity.
            resolution = resolve_repository_path_at_use(
                repository_root=self._pairing_root,
                relative_path=closure.spec_root,
                field_name="records.specification.target",
            )
            if (
                resolution.path is None
                or resolution.path != self._pairing_root / closure.spec_root
            ):
                raise IssueSpecificationIterationBindingError(
                    "pairing_specification_target_unresolvable",
                    diagnostics=resolution.diagnostics,
                )

    def _git(self, *arguments: str) -> bytes:
        self._check_repository()
        git = shutil.which("git", path=os.defpath)
        if git is None:
            raise IssueSpecificationIterationBindingError("pairing_git_unavailable")
        try:
            result = subprocess.run(
                [
                    git,
                    "--no-replace-objects",
                    "--literal-pathspecs",
                    "-C",
                    str(self._pairing_root),
                    *arguments,
                ],
                env={
                    "PATH": os.defpath,
                    "LC_ALL": "C",
                    "GIT_OPTIONAL_LOCKS": "0",
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_NO_LAZY_FETCH": "1",
                },
                capture_output=True,
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise IssueSpecificationIterationBindingError(
                "pairing_git_unavailable"
            ) from error
        if result.returncode != 0:
            raise IssueSpecificationIterationBindingError(
                "pairing_git_epoch_unavailable"
            )
        return result.stdout

    def _head(self) -> str:
        root = os.fsdecode(self._git("rev-parse", "--show-toplevel")).rstrip("\n")
        if Path(root) != self._pairing_root:
            raise IssueSpecificationIterationBindingError(
                "pairing_git_repository_mismatch"
            )
        return (
            self._git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        )

    def _committed_sources(
        self, evidence: SpecificationIterationSourceEvidence, head: str
    ) -> tuple[CommittedSpecificationMember, ...]:
        members = []
        for closure in evidence.closures:
            entries = self._git("ls-tree", "-r", "-z", head, "--", closure.spec_root)
            tree = {}
            for entry in entries.split(b"\0"):
                if not entry:
                    continue
                metadata, path_bytes = entry.split(b"\t", 1)
                mode, kind, oid = metadata.decode("ascii").split(" ")
                path = path_bytes.decode("utf-8")
                if path in tree:
                    raise IssueSpecificationIterationBindingError(
                        "pairing_committed_path_duplicate"
                    )
                tree[path] = (mode, kind, oid)
            for member in closure.members:
                path = f"{closure.spec_root}/{member.relative_path}"
                entry = tree.get(path)
                if (
                    entry is None
                    or entry[0] not in {"100644", "100755"}
                    or entry[1] != "blob"
                ):
                    raise IssueSpecificationIterationBindingError(
                        "pairing_specification_not_committed_regular",
                        diagnostics=(path,),
                    )
                blob = self._git("cat-file", "blob", entry[2])
                if blob != member.canonical_body.encode("utf-8"):
                    raise IssueSpecificationIterationBindingError(
                        "pairing_committed_source_mismatch", diagnostics=(path,)
                    )
                members.append(
                    CommittedSpecificationMember(path, entry[2], member.body_digest)
                )
        return tuple(sorted(members, key=lambda member: member.path))

    def _issue(self, request: IssueSpecificationIterationBindingObserveRequest):
        result = self.resolve_read_projection(
            IssueReadProjectionResolveRequest(request.issue_ref)
        )
        if type(result) is not IssueReadProjectionResolveResult:
            raise IssueSpecificationIterationBindingError(
                "pairing_issue_result_invalid"
            )
        result.__post_init__()
        if result.outcome is not IssueReadProjectionResolveOutcome.FOUND:
            raise IssueSpecificationIterationBindingError(
                "pairing_issue_unavailable", diagnostics=result.diagnostics
            )
        projection = result.projection
        if projection.source_digest != request.expected_issue_source_sha256:
            raise IssueSpecificationIterationBindingError("pairing_issue_changed")
        return projection

    def observe_specification_iteration_binding(
        self, request: IssueSpecificationIterationBindingObserveRequest
    ) -> IssueSpecificationIterationBindingObservation:
        if type(request) is not IssueSpecificationIterationBindingObserveRequest:
            raise IssueSpecificationIterationBindingError("pairing_request_invalid")
        request.__post_init__()
        try:
            self._check_manifest()
            if request.expected_manifest_sha256 != self._pairing_manifest_sha256:
                raise IssueSpecificationIterationBindingError(
                    "pairing_expected_manifest_mismatch"
                )
            if self._head() != request.expected_head:
                raise IssueSpecificationIterationBindingError("pairing_head_changed")
            evidence = self._source_evidence()
            self._check_selection(evidence)
            identity = evidence.identity
            if (
                identity.iteration_ref != request.iteration_ref
                or identity.plan.plan_revision != request.plan_revision
                or identity.plan_digest != request.plan_digest
            ):
                raise IssueSpecificationIterationBindingError(
                    "pairing_iteration_identity_mismatch"
                )
            if (
                evidence.observation.source_digest
                != request.expected_specification_source_digest
            ):
                raise IssueSpecificationIterationBindingError(
                    "pairing_specification_source_mismatch"
                )
            members = self._committed_sources(evidence, request.expected_head)
            issue = self._issue(request)
            fresh = self._source_evidence()
            self._check_selection(fresh)
            if fresh != evidence:
                raise IssueSpecificationIterationBindingError(
                    "pairing_specification_changed"
                )
            if self._issue(request) != issue:
                raise IssueSpecificationIterationBindingError("pairing_issue_changed")
            self._check_manifest()
            if self._head() != request.expected_head:
                raise IssueSpecificationIterationBindingError("pairing_head_changed")
            self._check_repository()
            return IssueSpecificationIterationBindingObservation(
                request,
                SpecificationIterationBindingOutcome.VERIFIED,
                PROVIDER_REF,
                phase_ref=identity.phase_ref,
                specification_source_digest=evidence.observation.source_digest,
                source_context_digest=evidence.observation.source_context_digest,
                snapshot_digest=evidence.observation.snapshot.snapshot_digest,
                manifest_sha256=self._pairing_manifest_sha256,
                head=request.expected_head,
                issue_projection=issue,
                roots=tuple(c.spec_root for c in evidence.closures),
                committed_members=members,
            )
        except IssueSpecificationIterationBindingError as error:
            return IssueSpecificationIterationBindingObservation(
                request,
                SpecificationIterationBindingOutcome.REFUSED,
                PROVIDER_REF,
                diagnostics=error.diagnostics,
            )
        except (
            OSError,
            RuntimeError,
            AttributeError,
            TypeError,
            ValueError,
        ) as error:
            return IssueSpecificationIterationBindingObservation(
                request,
                SpecificationIterationBindingOutcome.REFUSED,
                PROVIDER_REF,
                diagnostics=("pairing_observation_failed", type(error).__name__),
            )
