"""Filesystem provider for canonical Issue SDK operations."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import replace
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_issue_sdk.draft_package import (
        IssueDraftPackageBinding,
        IssueDraftPackageCleanupDisposition,
        IssueDraftPackageRequest,
    )
    from aware_issue_sdk.source_change import (
        IssueSourceChangeAdmission,
        IssueSourceChangeRequest,
    )

    from .draft_package import FilesystemIssueDraftPackageAdmission
    from .source_change import FilesystemIssueSourceChangeAdmission

from aware_issue_operational_runtime import (
    ActorEvidence,
    AppendIssueEvidenceIntent,
    AppendIssueUpdateIntent,
    AuthorityKind,
    BindIssueScopePathsIntent,
    BlockIssueIntent,
    EnsureIssueIntent,
    IssueAuthorityEvidence,
    IssueIntent,
    IssueIntentContext,
    IssueOperationalState,
    IssueOwnershipScopePath,
    IssueSnapshot,
    IssueStatus,
    ResumeIssueIntent,
    SetIssueOwnerIntent,
    StartIssueProgressIntent,
    TransitionOutcome,
    apply_issue_intent,
)
from aware_issue_operational_runtime.contracts import (
    IssueEvidenceRef,
    IssueUpdateLogEntry,
)
from aware_issue_runtime import (
    IssueReadProjection,
    parse_issue_projection,
    parse_issue_source,
)
from aware_issue_sdk import (
    IssueAppendEvidenceRequest,
    IssueAppendUpdateRequest,
    IssueBindScopePathsRequest,
    IssueBlockRequest,
    IssueCloseRequest,
    IssueCommitWorkspaceRequest,
    IssueCommitWorkspaceResult,
    IssueDocument,
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssueMutationRequest,
    IssueMutationResult,
    IssuePublicationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveResult,
    IssueResumeRequest,
    IssueSetOwnerRequest,
    IssueStartProgressRequest,
    append_update_line,
    build_issue_document,
    get_section,
    parse_issue_document_text,
    render_issue_document,
    set_header_value,
    set_ownership_scope,
    set_verified_by,
)
from aware_protocol_fs_adapter import (
    MANIFEST_FILENAME,
    FilesystemProtocolProfile,
    admit_protocol_manifest,
    resolve_repository_path_at_use,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind

FILESYSTEM_ISSUE_PROVIDER_REF = "aware_issue_fs_adapter.filesystem.v1"
FILESYSTEM_ISSUE_DISTRIBUTION = "aware-issue-fs-adapter"
WORKSPACE_COMMIT_OPERATOR_REF = "aware_issue_sdk.repository_publication"
ISSUE_PATH_TEMPLATE = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
_ISSUE_REF = re.compile(
    r"^fb/(?P<date>\d{4}-\d{2}-\d{2})/"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)


class FilesystemIssueOperationProvider:
    """Invoke canonical Issue operations through one admitted filesystem target."""

    def __init__(
        self,
        *,
        repository_root: str | Path,
        protocol_source_ref: str = MANIFEST_FILENAME,
    ) -> None:
        if not isinstance(repository_root, (str, Path)):
            raise TypeError("repository_root must be text or pathlib.Path")
        if type(repository_root) is str and not repository_root:
            raise ValueError("repository_root must not be empty")
        if type(protocol_source_ref) is not str or not protocol_source_ref:
            raise ValueError("protocol_source_ref must be non-empty text")
        self._repository_root = Path(repository_root)
        self._protocol_source_ref = protocol_source_ref

    def resolve_read_projection(
        self,
        request: IssueReadProjectionResolveRequest,
    ) -> IssueReadProjectionResolveResult:
        if type(request) is not IssueReadProjectionResolveRequest:
            raise TypeError("request must be IssueReadProjectionResolveRequest")
        match = _ISSUE_REF.fullmatch(request.issue_ref)
        if match is None:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=("issue_ref_invalid",),
            )
        admission = self._admit_manifest()
        if not isinstance(admission, FilesystemProtocolProfile):
            outcome, evidence, diagnostics = admission
            return self._result(
                request=request,
                outcome=outcome,
                evidence=evidence,
                diagnostics=diagnostics,
            )
        binding = next(
            (item for item in admission.record_bindings if item.record_key == "issue"),
            None,
        )
        if binding is None:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.UNSUPPORTED_PROFILE,
                diagnostics=("issue_record_unavailable",),
            )
        if binding.path_template != ISSUE_PATH_TEMPLATE:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.UNSUPPORTED_PROFILE,
                diagnostics=(
                    f"issue_path_template_unsupported:{binding.path_template}",
                ),
            )
        date = match.group("date")
        year, month, day = date.split("-")
        relative_path = (
            f"{binding.root}/{year}/{month}/{day}/fb-{date}-{match.group('slug')}.md"
        )
        resolution = resolve_repository_path_at_use(
            repository_root=self._repository_root,
            relative_path=relative_path,
            field_name="records.issue.target",
        )
        if resolution.path is None:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.AUTHORITY_UNAVAILABLE,
                diagnostics=resolution.diagnostics,
            )
        try:
            source = resolution.path.read_bytes()
        except FileNotFoundError:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.ABSENT,
                evidence=(f"record_path:{relative_path}",),
            )
        except OSError as error:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.AUTHORITY_UNAVAILABLE,
                diagnostics=(f"issue_source_unavailable:{type(error).__name__}",),
            )
        try:
            markdown = source.decode("utf-8")
        except UnicodeDecodeError:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=("issue_source_not_utf8",),
            )
        duplicates = self._duplicate_identity_diagnostics(
            profile=admission,
            expected_issue_ref=request.issue_ref,
            selected_path=resolution.path,
        )
        if duplicates:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=duplicates,
            )
        try:
            projection = parse_issue_projection(
                text=markdown,
                source_path=relative_path,
            )
        except (TypeError, ValueError) as error:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=(f"issue_projection_failed:{type(error).__name__}",),
            )
        if projection.issue_ref != request.issue_ref:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=(f"issue_identity_mismatch:{projection.issue_ref}",),
            )
        if not projection.title:
            return self._result(
                request=request,
                outcome=IssueReadProjectionResolveOutcome.MALFORMED,
                diagnostics=("issue_title_missing",),
            )
        return self._result(
            request=request,
            outcome=IssueReadProjectionResolveOutcome.FOUND,
            projection=projection,
            evidence=(
                "authority_mode:filesystem",
                f"protocol_digest:{admission.protocol_manifest.digest}",
                f"record_path:{relative_path}",
                f"source_sha256:{projection.source_digest}",
            ),
        )

    def admit_source_change(
        self, request: IssueSourceChangeRequest
    ) -> FilesystemIssueSourceChangeAdmission:
        from .source_change import _admit

        return _admit(self, request)

    def validate_source_change(self, admission: IssueSourceChangeAdmission) -> None:
        from .source_change import _validate_bound

        _validate_bound(self, admission)

    def retain_draft_inputs(
        self,
        *,
        protocol_target: object,
        physical_plan: object,
        attempt_ref: str,
        client_intent_id: str,
    ) -> object:
        from .draft_package import _retain_inputs

        return _retain_inputs(
            self, protocol_target, physical_plan, attempt_ref, client_intent_id
        )

    def require_draft_input_custody(
        self, value, *, protocol_target, physical_plan, client_intent_id
    ):
        from .draft_package import require_draft_input_custody

        return require_draft_input_custody(
            value,
            provider=self,
            protocol_target=protocol_target,
            physical_plan=physical_plan,
            client_intent_id=client_intent_id,
        )

    def claim_draft_input_custody(
        self, value, *, protocol_target, physical_plan, client_intent_id, context_ref
    ):
        from .draft_package import claim_draft_input_custody

        return claim_draft_input_custody(
            value,
            provider=self,
            protocol_target=protocol_target,
            physical_plan=physical_plan,
            client_intent_id=client_intent_id,
            context_ref=context_ref,
        )

    def admit_draft_package(
        self,
        request: IssueDraftPackageRequest,
        *,
        protocol_target: object,
        physical_plan: object,
        input_custody: object | None = None,
    ) -> FilesystemIssueDraftPackageAdmission:
        from .draft_package import _admit

        return _admit(self, request, protocol_target, physical_plan, input_custody)

    def validate_draft_package(self, admission: object) -> None:
        from .draft_package import _validate_bound

        _validate_bound(self, admission)

    def observe_draft_package_binding(
        self, admission: object
    ) -> IssueDraftPackageBinding:
        from .draft_package import _observe_binding

        return _observe_binding(self, admission)

    def observe_draft_package_cleanup(
        self, *, protocol_target: object, physical_plan: object
    ) -> IssueDraftPackageCleanupDisposition:
        """Detached original-attempt disposition, including failed issuance."""
        from .draft_package import _observe_cleanup

        return _observe_cleanup(self, protocol_target, physical_plan)

    def ensure_issue_snapshot(
        self,
        request: IssueEnsureSnapshotRequest,
    ) -> IssueMutationResult:
        if type(request) is not IssueEnsureSnapshotRequest:
            raise TypeError("request must be IssueEnsureSnapshotRequest")
        target = self._mutation_target(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
        )
        if isinstance(target, IssueMutationResult):
            return target
        profile, relative_path, path = target
        try:
            source = path.read_bytes()
        except FileNotFoundError:
            source = None
        except OSError as error:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.AUTHORITY_UNAVAILABLE,
                diagnostics=(f"issue_source_unavailable:{type(error).__name__}",),
            )
        if source is not None:
            before = _source_digest(source)
            if request.expected_source_sha256 not in {None, before}:
                return self._mutation_result(
                    operation_ref=request.operation_ref,
                    issue_ref=request.issue_ref,
                    outcome=IssueMutationOutcome.STALE,
                    source_sha256_before=before,
                    diagnostics=("expected_source_sha256_mismatch",),
                )
            projection = self._parse_projection(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                relative_path=relative_path,
                source=source,
            )
            if isinstance(projection, IssueMutationResult):
                return projection
            expected_owner = request.owner_ref
            if (
                projection.title != request.title
                or projection.priority != request.priority
                or projection.owner_ref != expected_owner
            ):
                return self._mutation_result(
                    operation_ref=request.operation_ref,
                    issue_ref=request.issue_ref,
                    outcome=IssueMutationOutcome.CONFLICT,
                    source_sha256_before=before,
                    diagnostics=("issue_identity_already_exists_with_other_values",),
                )
            if (
                (
                    request.problem_items
                    and request.problem_items != projection.problem_items
                )
                or (
                    request.objective_items
                    and request.objective_items != projection.goal_items
                )
                or (
                    request.acceptance_items
                    and request.acceptance_items
                    != tuple(item.text for item in projection.acceptance_items)
                )
            ):
                return self._mutation_result(
                    operation_ref=request.operation_ref,
                    issue_ref=request.issue_ref,
                    outcome=IssueMutationOutcome.CONFLICT,
                    source_sha256_before=before,
                    diagnostics=(
                        "issue_authored_content_already_exists_with_other_values",
                    ),
                )
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.IDEMPOTENT,
                projection=projection,
                source_sha256_before=before,
                source_sha256_after=before,
                evidence=self._mutation_evidence(
                    profile=profile,
                    relative_path=relative_path,
                    source_sha256=before,
                    projection_effect="unchanged",
                ),
            )
        if request.expected_source_sha256 is not None:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.STALE,
                diagnostics=("issue_must_exist_for_expected_source_sha256",),
            )
        duplicates = self._duplicate_identity_diagnostics(
            profile=profile,
            expected_issue_ref=request.issue_ref,
            selected_path=path,
        )
        if duplicates:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.CONFLICT,
                diagnostics=duplicates,
            )
        match = _ISSUE_REF.fullmatch(request.issue_ref)
        if match is None:
            raise AssertionError("validated Issue ref did not match")
        state = self._empty_operational_state(relative_path=relative_path)
        transition = apply_issue_intent(
            state,
            EnsureIssueIntent(
                context=self._intent_context(
                    request=request,
                    expected_issue_revision=None,
                ),
                tag=request.issue_ref,
                title=request.title,
                priority_level=request.priority,
                owner_session_id=request.owner_ref,
            ),
        )
        if transition.outcome is not TransitionOutcome.APPLIED:
            return self._transition_refusal(
                request=request,
                transition_outcome=transition.outcome,
                blocker_code=transition.blocker_code,
            )
        document = build_issue_document(
            title=request.title,
            slug=match.group("slug"),
            tag=request.issue_ref,
            status_display="Open",
            owner_session_id=request.owner_ref,
            priority=request.priority,
            goal=request.goal_ref,
            captured=match.group("date"),
            recorder=request.actor_ref,
            source=request.source_description,
            ownership_scope=(),
            problem_items=request.problem_items,
            objective_items=request.objective_items,
            acceptance_items=request.acceptance_items,
            updates=(
                (
                    f"- Ensured through `{request.operation_ref}`. "
                    f"(recorder: `{request.actor_ref}`)"
                ),
            ),
        )
        rendered = render_issue_document(document=document).encode("utf-8")
        write_result = self._create_source(
            relative_path=relative_path,
            path=path,
            source=rendered,
        )
        if write_result is not None:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=write_result,
                diagnostics=("issue_create_race",),
            )
        projection = parse_issue_projection(
            text=rendered.decode("utf-8"),
            source_path=relative_path,
        )
        after = _source_digest(rendered)
        return self._mutation_result(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
            outcome=IssueMutationOutcome.APPLIED,
            projection=projection,
            source_sha256_after=after,
            evidence=self._mutation_evidence(
                profile=profile,
                relative_path=relative_path,
                source_sha256=after,
                projection_effect="applied",
            ),
        )

    def start_issue_progress(
        self,
        request: IssueStartProgressRequest,
    ) -> IssueMutationResult:
        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: StartIssueProgressIntent(
                context=context,
                issue_ref=request.issue_ref,
            ),
            document_mutator=lambda document: self._set_lifecycle(
                document=document,
                status="In Progress",
                operation_ref=request.operation_ref,
                actor_ref=request.actor_ref,
            ),
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def block_issue(self, request: IssueBlockRequest) -> IssueMutationResult:
        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: BlockIssueIntent(
                context=context,
                issue_ref=request.issue_ref,
            ),
            document_mutator=lambda document: self._set_lifecycle(
                document=document,
                status="Blocked",
                operation_ref=request.operation_ref,
                actor_ref=request.actor_ref,
            ),
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def resume_issue(self, request: IssueResumeRequest) -> IssueMutationResult:
        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: ResumeIssueIntent(
                context=context,
                issue_ref=request.issue_ref,
            ),
            document_mutator=lambda document: self._set_lifecycle(
                document=document,
                status="In Progress",
                operation_ref=request.operation_ref,
                actor_ref=request.actor_ref,
            ),
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def set_issue_owner(self, request: IssueSetOwnerRequest) -> IssueMutationResult:
        def set_owner(document: IssueDocument) -> None:
            set_header_value(
                document=document,
                field="Owner",
                value=f"`{request.new_owner_ref}`",
            )
            append_update_line(
                document=document,
                line=(
                    f"- Transferred Issue ownership from `{request.actor_ref}` to "
                    f"`{request.new_owner_ref}` through `{request.operation_ref}`. "
                    f"(recorder: `{request.actor_ref}`)"
                ),
            )

        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: SetIssueOwnerIntent(
                context=context,
                issue_ref=request.issue_ref,
                new_owner_session_id=request.new_owner_ref,
            ),
            document_mutator=set_owner,
        )

    def bind_issue_scope_paths(
        self,
        request: IssueBindScopePathsRequest,
    ) -> IssueMutationResult:
        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: BindIssueScopePathsIntent(
                context=context,
                issue_ref=request.issue_ref,
                scope_paths=tuple(
                    IssueOwnershipScopePath(relative_path=path)
                    for path in request.scope_paths
                ),
            ),
            document_mutator=lambda document: set_ownership_scope(
                document=document,
                scope_paths=request.scope_paths,
            ),
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def append_issue_update(
        self,
        request: IssueAppendUpdateRequest,
    ) -> IssueMutationResult:
        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: AppendIssueUpdateIntent(
                context=context,
                issue_ref=request.issue_ref,
                message=request.message,
                outcome=request.outcome,
            ),
            document_mutator=lambda document: append_update_line(
                document=document,
                line=(
                    f"- {request.message} (outcome: {request.outcome}) "
                    f"(recorder: `{request.actor_ref}`)"
                ),
            ),
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def append_issue_evidence(
        self,
        request: IssueAppendEvidenceRequest,
    ) -> IssueMutationResult:
        def append_evidence(document: IssueDocument) -> None:
            section = get_section(document=document, heading="Verified-by")
            entries = (
                ()
                if section is None
                else tuple(
                    line.removeprefix("- ").strip()
                    for line in section.lines
                    if line.strip().startswith("- ")
                )
            )
            description = (
                request.path
                if request.description is None
                else f"{request.path} — {request.description}"
            )
            set_verified_by(document=document, entries=(*entries, description))

        return self._mutate_existing(
            request=request,
            intent_factory=lambda context: AppendIssueEvidenceIntent(
                context=context,
                issue_ref=request.issue_ref,
                path=request.path,
                description=request.description,
            ),
            document_mutator=append_evidence,
            precondition=lambda projection: self._owner_precondition(
                projection=projection,
                actor_ref=request.actor_ref,
            ),
        )

    def close_issue(self, request: IssueCloseRequest) -> IssueMutationResult:
        """Retired physical orchestration: select the genuine Issue SDK runtime.

        This compatibility refusal performs no source/Git IO and never calls a
        foreign SDK. The consumer must explicitly bind the original runtime.
        """
        if type(request) is not IssueCloseRequest:
            raise TypeError("request must be IssueCloseRequest")
        return self._mutation_result(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
            outcome=IssueMutationOutcome.AUTHORITY_UNAVAILABLE,
            diagnostics=("issue_repository_runtime_required",),
        )

    def commit_workspace(
        self, request: IssueCommitWorkspaceRequest
    ) -> IssueCommitWorkspaceResult:
        """No writer fallback or foreign orchestration in a physical provider."""
        if type(request) is not IssueCommitWorkspaceRequest:
            raise TypeError("request must be IssueCommitWorkspaceRequest")
        return self._publication_result(
            request=request,
            outcome=IssuePublicationOutcome.AUTHORITY_UNAVAILABLE,
            diagnostics=("issue_repository_runtime_required",),
        )

    def _publication_result_from_mutation_refusal(
        self,
        *,
        request: IssueCommitWorkspaceRequest,
        refusal: IssueMutationResult,
    ) -> IssueCommitWorkspaceResult:
        outcome = {
            IssueMutationOutcome.STALE: IssuePublicationOutcome.STALE,
            IssueMutationOutcome.UNAUTHORIZED: IssuePublicationOutcome.UNAUTHORIZED,
            IssueMutationOutcome.CONFLICT: IssuePublicationOutcome.CONFLICT,
            IssueMutationOutcome.AUTHORITY_UNAVAILABLE: (
                IssuePublicationOutcome.AUTHORITY_UNAVAILABLE
            ),
        }.get(refusal.outcome, IssuePublicationOutcome.INVALID)
        return self._publication_result(
            request=request,
            outcome=outcome,
            evidence=refusal.evidence,
            diagnostics=refusal.diagnostics,
        )

    def _publication_result(
        self,
        *,
        request: IssueCommitWorkspaceRequest,
        outcome: IssuePublicationOutcome,
        commit_hash: str | None = None,
        transaction_mode: str = "not_run",
        reference_update: str = "not_run",
        shared_index_projection: str | None = None,
        shared_index_projection_error: str | None = None,
        index_reconciliation_pending: bool | None = None,
        evidence: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> IssueCommitWorkspaceResult:
        return IssueCommitWorkspaceResult(
            outcome=outcome,
            issue_ref=request.issue_ref,
            target_paths=request.target_paths,
            provider_ref=FILESYSTEM_ISSUE_PROVIDER_REF,
            provider_distribution=FILESYSTEM_ISSUE_DISTRIBUTION,
            provider_version=_distribution_version(FILESYSTEM_ISSUE_DISTRIBUTION),
            operator_ref=WORKSPACE_COMMIT_OPERATOR_REF,
            transaction_mode=transaction_mode,
            commit_hash=commit_hash,
            reference_update=reference_update,
            shared_index_projection=shared_index_projection,
            shared_index_projection_error=shared_index_projection_error,
            index_reconciliation_pending=index_reconciliation_pending,
            evidence=evidence,
            diagnostics=diagnostics,
        )

    def _mutation_target(
        self,
        *,
        operation_ref: str,
        issue_ref: str,
    ) -> tuple[FilesystemProtocolProfile, str, Path] | IssueMutationResult:
        match = _ISSUE_REF.fullmatch(issue_ref)
        if match is None:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.MALFORMED,
                diagnostics=("issue_ref_invalid",),
            )
        admission = self._admit_manifest()
        if not isinstance(admission, FilesystemProtocolProfile):
            read_outcome, evidence, diagnostics = admission
            outcome = {
                IssueReadProjectionResolveOutcome.UNSUPPORTED_PROFILE: (
                    IssueMutationOutcome.UNSUPPORTED_PROFILE
                ),
                IssueReadProjectionResolveOutcome.AUTHORITY_UNAVAILABLE: (
                    IssueMutationOutcome.AUTHORITY_UNAVAILABLE
                ),
                IssueReadProjectionResolveOutcome.MALFORMED: (
                    IssueMutationOutcome.MALFORMED
                ),
            }.get(read_outcome, IssueMutationOutcome.MALFORMED)
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=outcome,
                evidence=evidence,
                diagnostics=diagnostics,
            )
        binding = next(
            (item for item in admission.record_bindings if item.record_key == "issue"),
            None,
        )
        if binding is None:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.UNSUPPORTED_PROFILE,
                diagnostics=("issue_record_unavailable",),
            )
        if binding.path_template != ISSUE_PATH_TEMPLATE:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.UNSUPPORTED_PROFILE,
                diagnostics=(
                    f"issue_path_template_unsupported:{binding.path_template}",
                ),
            )
        date = match.group("date")
        year, month, day = date.split("-")
        relative_path = (
            f"{binding.root}/{year}/{month}/{day}/fb-{date}-{match.group('slug')}.md"
        )
        resolution = resolve_repository_path_at_use(
            repository_root=self._repository_root,
            relative_path=relative_path,
            field_name="records.issue.target",
        )
        if resolution.path is None:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.AUTHORITY_UNAVAILABLE,
                diagnostics=resolution.diagnostics,
            )
        return admission, relative_path, resolution.path

    def _parse_projection(
        self,
        *,
        operation_ref: str,
        issue_ref: str,
        relative_path: str,
        source: bytes,
    ) -> IssueReadProjection | IssueMutationResult:
        try:
            markdown = source.decode("utf-8")
        except UnicodeDecodeError:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.MALFORMED,
                diagnostics=("issue_source_not_utf8",),
            )
        try:
            projection = parse_issue_projection(
                text=markdown,
                source_path=relative_path,
            )
        except (TypeError, ValueError) as error:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.MALFORMED,
                diagnostics=(f"issue_projection_failed:{type(error).__name__}",),
            )
        if projection.issue_ref != issue_ref:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.MALFORMED,
                diagnostics=(f"issue_identity_mismatch:{projection.issue_ref}",),
            )
        if not projection.title:
            return self._mutation_result(
                operation_ref=operation_ref,
                issue_ref=issue_ref,
                outcome=IssueMutationOutcome.MALFORMED,
                diagnostics=("issue_title_missing",),
            )
        return projection

    def _mutate_existing(
        self,
        *,
        request: IssueMutationRequest,
        intent_factory: Callable[[IssueIntentContext], IssueIntent],
        document_mutator: Callable[[IssueDocument], None],
        precondition: Callable[
            [IssueReadProjection],
            tuple[IssueMutationOutcome, tuple[str, ...]] | None,
        ]
        | None = None,
    ) -> IssueMutationResult:
        target = self._mutation_target(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
        )
        if isinstance(target, IssueMutationResult):
            return target
        profile, relative_path, path = target
        try:
            source = path.read_bytes()
        except FileNotFoundError:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.ABSENT,
                evidence=(f"record_path:{relative_path}",),
            )
        except OSError as error:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.AUTHORITY_UNAVAILABLE,
                diagnostics=(f"issue_source_unavailable:{type(error).__name__}",),
            )
        before = _source_digest(source)
        if before != request.expected_source_sha256:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.STALE,
                source_sha256_before=before,
                diagnostics=("expected_source_sha256_mismatch",),
            )
        duplicates = self._duplicate_identity_diagnostics(
            profile=profile,
            expected_issue_ref=request.issue_ref,
            selected_path=path,
        )
        if duplicates:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.CONFLICT,
                source_sha256_before=before,
                diagnostics=duplicates,
            )
        projection = self._parse_projection(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
            relative_path=relative_path,
            source=source,
        )
        if isinstance(projection, IssueMutationResult):
            return projection
        if precondition is not None:
            refusal = precondition(projection)
            if refusal is not None:
                outcome, diagnostics = refusal
                return self._mutation_result(
                    operation_ref=request.operation_ref,
                    issue_ref=request.issue_ref,
                    outcome=outcome,
                    source_sha256_before=before,
                    diagnostics=diagnostics,
                )
        state = self._operational_state(
            projection=projection,
            relative_path=relative_path,
        )
        transition = apply_issue_intent(
            state,
            intent_factory(
                self._intent_context(
                    request=request,
                    expected_issue_revision=0,
                )
            ),
        )
        if transition.outcome not in {
            TransitionOutcome.APPLIED,
            TransitionOutcome.IDEMPOTENT,
        }:
            return self._transition_refusal(
                request=request,
                transition_outcome=transition.outcome,
                blocker_code=transition.blocker_code,
                source_sha256_before=before,
            )
        if transition.outcome is TransitionOutcome.IDEMPOTENT:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=IssueMutationOutcome.IDEMPOTENT,
                projection=projection,
                source_sha256_before=before,
                source_sha256_after=before,
                evidence=self._mutation_evidence(
                    profile=profile,
                    relative_path=relative_path,
                    source_sha256=before,
                    projection_effect="unchanged",
                ),
            )
        document = parse_issue_document_text(text=source.decode("utf-8"))
        document_mutator(document)
        rendered = render_issue_document(document=document).encode("utf-8")
        write_outcome = self._replace_source(
            relative_path=relative_path,
            path=path,
            expected_source_sha256=before,
            source=rendered,
        )
        if write_outcome is not None:
            return self._mutation_result(
                operation_ref=request.operation_ref,
                issue_ref=request.issue_ref,
                outcome=write_outcome,
                source_sha256_before=before,
                diagnostics=("source_changed_before_write",),
            )
        updated_projection = parse_issue_projection(
            text=rendered.decode("utf-8"),
            source_path=relative_path,
        )
        after = _source_digest(rendered)
        return self._mutation_result(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
            outcome=IssueMutationOutcome.APPLIED,
            projection=updated_projection,
            source_sha256_before=before,
            source_sha256_after=after,
            evidence=self._mutation_evidence(
                profile=profile,
                relative_path=relative_path,
                source_sha256=after,
                projection_effect="applied",
            ),
        )

    def _mutation_evidence(
        self,
        *,
        profile: FilesystemProtocolProfile,
        relative_path: str,
        source_sha256: str,
        projection_effect: str,
    ) -> tuple[str, ...]:
        feed_record = next(
            (
                item
                for item in profile.protocol_manifest.records
                if item.record_key == "feed"
            ),
            None,
        )
        feed_effect = (
            "unavailable"
            if feed_record is None or feed_record.role.value == "unavailable"
            else "pending"
        )
        return (
            "authority_mode:filesystem",
            f"protocol_digest:{profile.protocol_manifest.digest}",
            f"record_path:{relative_path}",
            f"source_sha256:{source_sha256}",
            f"projection_effect:issue_authority:{projection_effect}",
            "projection_effect:issue_day_index:pending",
            f"projection_effect:feed:{feed_effect}",
        )

    def _empty_operational_state(self, *, relative_path: str) -> IssueOperationalState:
        return IssueOperationalState(
            authority=IssueAuthorityEvidence(
                kind=AuthorityKind.CANONICAL_COMMITTED,
                provider_key="aware_issue_fs_adapter",
                authority_ref=f"repository:{relative_path}",
                generation=0,
            )
        )

    def _operational_state(
        self,
        *,
        projection: IssueReadProjection,
        relative_path: str,
    ) -> IssueOperationalState:
        state = self._empty_operational_state(relative_path=relative_path)
        status = {
            "open": IssueStatus.OPEN,
            "in_progress": IssueStatus.IN_PROGRESS,
            "blocked": IssueStatus.BLOCKED,
            "closed": IssueStatus.CLOSED,
        }.get(projection.status)
        if status is None:
            raise ValueError(f"unsupported Issue status: {projection.status}")
        updates = tuple(
            IssueUpdateLogEntry(
                sequence=index,
                message=item.message or "authored Issue activity",
                actor_ref=item.actor_ref or "filesystem-projection",
                actor_evidence_ref=projection.source_digest,
                outcome=item.outcome or "info",
            )
            for index, item in enumerate(projection.activities, start=1)
        )
        evidence = tuple(
            IssueEvidenceRef(
                sequence=index,
                path=item.reference,
            )
            for index, item in enumerate(projection.evidence, start=1)
        )
        snapshot = IssueSnapshot(
            issue_ref=projection.issue_ref,
            tag=projection.issue_ref,
            title=projection.title,
            status=status,
            priority_level=projection.priority or "medium",
            owner_session_id=projection.owner_ref,
            scope_paths=tuple(
                sorted(
                    IssueOwnershipScopePath(relative_path=path)
                    for path in projection.ownership_scope
                )
            ),
            updates=updates,
            evidence_refs=evidence,
            authority=state.authority,
        )
        return replace(state, issues=(snapshot,))

    def _intent_context(
        self,
        *,
        request: IssueMutationRequest | IssueEnsureSnapshotRequest,
        expected_issue_revision: int | None,
    ) -> IssueIntentContext:
        return IssueIntentContext(
            client_intent_id=request.client_intent_id,
            expected_issue_revision=expected_issue_revision,
            expected_authority_generation=0,
            actor_evidence=ActorEvidence(
                actor_ref=request.actor_ref,
                evidence_ref=request.actor_evidence_ref,
            ),
        )

    def _set_lifecycle(
        self,
        *,
        document: IssueDocument,
        status: str,
        operation_ref: str,
        actor_ref: str,
    ) -> None:
        set_header_value(document=document, field="Status", value=status)
        append_update_line(
            document=document,
            line=(f"- Applied `{operation_ref}`. (recorder: `{actor_ref}`)"),
        )

    def _close_precondition(
        self,
        *,
        projection: IssueReadProjection,
        request: IssueCloseRequest,
    ) -> tuple[IssueMutationOutcome, tuple[str, ...]] | None:
        owner_refusal = self._owner_precondition(
            projection=projection,
            actor_ref=request.actor_ref,
        )
        if owner_refusal is not None:
            return owner_refusal
        diagnostics: list[str] = []
        if projection.status != "in_progress":
            diagnostics.append("close_requires_in_progress")
        if not request.verified_by:
            diagnostics.append("close_requires_verification_evidence")
        if not request.publication_receipt_ref:
            diagnostics.append("close_requires_publication_receipt")
        if diagnostics:
            return IssueMutationOutcome.BLOCKED, tuple(diagnostics)
        return None

    def _owner_precondition(
        self,
        *,
        projection: IssueReadProjection,
        actor_ref: str,
    ) -> tuple[IssueMutationOutcome, tuple[str, ...]] | None:
        if projection.owner_ref is None:
            return IssueMutationOutcome.UNAUTHORIZED, ("issue_owner_unassigned",)
        if projection.owner_ref != actor_ref:
            return IssueMutationOutcome.UNAUTHORIZED, ("issue_owner_mismatch",)
        return None

    def _transition_refusal(
        self,
        *,
        request: IssueMutationRequest | IssueEnsureSnapshotRequest,
        transition_outcome: TransitionOutcome,
        blocker_code: str | None,
        source_sha256_before: str | None = None,
    ) -> IssueMutationResult:
        outcome = {
            TransitionOutcome.IDEMPOTENT: IssueMutationOutcome.IDEMPOTENT,
            TransitionOutcome.STALE: IssueMutationOutcome.STALE,
            TransitionOutcome.CONFLICT: IssueMutationOutcome.CONFLICT,
            TransitionOutcome.UNRESOLVED: IssueMutationOutcome.ABSENT,
            TransitionOutcome.INVALID: IssueMutationOutcome.INVALID,
            TransitionOutcome.UNAUTHORIZED: IssueMutationOutcome.UNAUTHORIZED,
            TransitionOutcome.BLOCKED: IssueMutationOutcome.BLOCKED,
        }.get(transition_outcome, IssueMutationOutcome.INVALID)
        return self._mutation_result(
            operation_ref=request.operation_ref,
            issue_ref=request.issue_ref,
            outcome=outcome,
            source_sha256_before=source_sha256_before,
            diagnostics=(blocker_code or "issue_transition_refused",),
        )

    def _create_source(
        self,
        *,
        relative_path: str,
        path: Path,
        source: bytes,
    ) -> IssueMutationOutcome | None:
        path.parent.mkdir(parents=True, exist_ok=True)
        resolution = resolve_repository_path_at_use(
            repository_root=self._repository_root,
            relative_path=relative_path,
            field_name="records.issue.target_at_write",
        )
        if resolution.path != path:
            return IssueMutationOutcome.AUTHORITY_UNAVAILABLE
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            return IssueMutationOutcome.CONFLICT
        except OSError:
            return IssueMutationOutcome.AUTHORITY_UNAVAILABLE
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(source)
            stream.flush()
            os.fsync(stream.fileno())
        return None

    def _replace_source(
        self,
        *,
        relative_path: str,
        path: Path,
        expected_source_sha256: str,
        source: bytes,
    ) -> IssueMutationOutcome | None:
        resolution = resolve_repository_path_at_use(
            repository_root=self._repository_root,
            relative_path=relative_path,
            field_name="records.issue.target_at_write",
        )
        if resolution.path != path:
            return IssueMutationOutcome.AUTHORITY_UNAVAILABLE
        try:
            current = path.read_bytes()
        except OSError:
            return IssueMutationOutcome.AUTHORITY_UNAVAILABLE
        if _source_digest(current) != expected_source_sha256:
            return IssueMutationOutcome.STALE
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(source)
                stream.flush()
                os.fsync(stream.fileno())
            if _source_digest(path.read_bytes()) != expected_source_sha256:
                return IssueMutationOutcome.STALE
            os.replace(temporary_path, path)
        except OSError:
            return IssueMutationOutcome.AUTHORITY_UNAVAILABLE
        finally:
            temporary_path.unlink(missing_ok=True)
        return None

    def _mutation_result(
        self,
        *,
        operation_ref: str,
        issue_ref: str,
        outcome: IssueMutationOutcome,
        projection: IssueReadProjection | None = None,
        source_sha256_before: str | None = None,
        source_sha256_after: str | None = None,
        closeout_publication_receipt_ref: str | None = None,
        evidence: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> IssueMutationResult:
        return IssueMutationResult(
            operation_ref=operation_ref,
            outcome=outcome,
            issue_ref=issue_ref,
            projection=projection,
            provider_ref=FILESYSTEM_ISSUE_PROVIDER_REF,
            provider_distribution=FILESYSTEM_ISSUE_DISTRIBUTION,
            provider_version=_distribution_version(FILESYSTEM_ISSUE_DISTRIBUTION),
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            closeout_publication_receipt_ref=closeout_publication_receipt_ref,
            evidence=evidence,
            diagnostics=diagnostics,
        )

    def _admit_manifest(
        self,
    ) -> (
        FilesystemProtocolProfile
        | tuple[
            IssueReadProjectionResolveOutcome,
            tuple[str, ...],
            tuple[str, ...],
        ]
    ):
        manifest_path = Path(self._protocol_source_ref)
        if not manifest_path.is_absolute():
            manifest_path = self._repository_root / manifest_path
        admission = admit_protocol_manifest(
            manifest_path=manifest_path,
            repository_root=self._repository_root,
        )
        if admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            if admission.filesystem_profile is None:
                raise AssertionError("canonical Protocol admission omitted its profile")
            return admission.filesystem_profile
        outcome = {
            ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE: (
                IssueReadProjectionResolveOutcome.UNSUPPORTED_PROFILE
            ),
            ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE: (
                IssueReadProjectionResolveOutcome.AUTHORITY_UNAVAILABLE
            ),
            ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE: (
                IssueReadProjectionResolveOutcome.AUTHORITY_UNAVAILABLE
            ),
            ProtocolAdmissionOutcomeKind.MALFORMED_V1: (
                IssueReadProjectionResolveOutcome.MALFORMED
            ),
        }.get(admission.outcome, IssueReadProjectionResolveOutcome.MALFORMED)
        evidence = (
            ()
            if admission.source_sha256 is None
            else (f"protocol_source_sha256:{admission.source_sha256}",)
        )
        return outcome, evidence, admission.diagnostics

    def _duplicate_identity_diagnostics(
        self,
        *,
        profile: FilesystemProtocolProfile,
        expected_issue_ref: str,
        selected_path: Path,
    ) -> tuple[str, ...]:
        binding = next(
            item for item in profile.record_bindings if item.record_key == "issue"
        )
        root_resolution = resolve_repository_path_at_use(
            repository_root=self._repository_root,
            relative_path=binding.root,
            field_name="records.issue.root_at_use",
        )
        if root_resolution.path is None or not root_resolution.path.is_dir():
            return ()
        matches = 0
        for directory, directory_names, file_names in os.walk(
            root_resolution.path,
            followlinks=False,
        ):
            directory_names.sort()
            for name in sorted(file_names):
                if not name.startswith("fb-") or not name.endswith(".md"):
                    continue
                candidate = Path(directory) / name
                if candidate == selected_path:
                    continue
                relative_to_issue_root = candidate.relative_to(root_resolution.path)
                candidate_resolution = resolve_repository_path_at_use(
                    repository_root=self._repository_root,
                    relative_path=(
                        f"{binding.root}/{relative_to_issue_root.as_posix()}"
                    ),
                    field_name="records.issue.duplicate_candidate",
                )
                if candidate_resolution.path is None:
                    continue
                try:
                    document = parse_issue_source(
                        candidate_resolution.path.read_text(encoding="utf-8")
                    )
                except (OSError, UnicodeError):
                    continue
                tag = document.header("Tag")
                if tag == expected_issue_ref:
                    matches += 1
        if matches == 0:
            return ()
        return (f"issue_identity_duplicate_matches:{matches + 1}",)

    def _result(
        self,
        *,
        request: IssueReadProjectionResolveRequest,
        outcome: IssueReadProjectionResolveOutcome,
        projection: IssueReadProjection | None = None,
        evidence: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> IssueReadProjectionResolveResult:
        return IssueReadProjectionResolveResult(
            outcome=outcome,
            issue_ref=request.issue_ref,
            projection=projection,
            provider_ref=FILESYSTEM_ISSUE_PROVIDER_REF,
            provider_distribution=FILESYSTEM_ISSUE_DISTRIBUTION,
            provider_version=_distribution_version(FILESYSTEM_ISSUE_DISTRIBUTION),
            evidence=evidence,
            diagnostics=diagnostics,
        )


def _distribution_version(distribution_name: str) -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "source"


def _source_digest(source: bytes) -> str:
    return f"sha256:{hashlib.sha256(source).hexdigest()}"


def _publication_refusal_outcome(error: str) -> IssuePublicationOutcome:
    if "stale" in error or "changed_before" in error:
        return IssuePublicationOutcome.STALE
    if "outside ownership scope" in error or "outside issue scope" in error:
        return IssuePublicationOutcome.OUT_OF_SCOPE
    if "owner" in error:
        return IssuePublicationOutcome.UNAUTHORIZED
    if any(
        token in error
        for token in (
            "repository_ref",
            "reference update",
            "shared_index",
            "already staged",
        )
    ):
        return IssuePublicationOutcome.CONFLICT
    if any(
        token in error
        for token in (
            "not writable",
            "not a git repository",
            "Repo root",
            "repository_git_path_unavailable",
        )
    ):
        return IssuePublicationOutcome.AUTHORITY_UNAVAILABLE
    return IssuePublicationOutcome.INVALID


__all__ = [
    "FILESYSTEM_ISSUE_DISTRIBUTION",
    "FILESYSTEM_ISSUE_PROVIDER_REF",
    "FilesystemIssueOperationProvider",
]
