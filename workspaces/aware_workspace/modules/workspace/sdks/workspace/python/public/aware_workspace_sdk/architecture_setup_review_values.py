"""Detached durable A1 review records; these values never grant execution authority.

The v1 contracts are authored here. Owner data types remain with their suppliers;
optional physical types are imported only for static checking.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from aware_file_system.private_directory import (
        PrivateDirectoryCleanup,
        PrivateDirectoryObservation,
        PrivateDirectoryRefusalEvidence,
        PrivateFileReadResult,
        PrivateSequenceCleanup,
        PrivateSequenceObservation,
    )
    from aware_issue_sdk.operation import (
        IssueBindScopePathsRequest as OriginalScopeRequest,
    )
    from aware_issue_sdk.operation import (
        IssueMutationError as OriginalScopeFailure,
    )
    from aware_issue_sdk.operation import (
        IssueMutationResult as OriginalScopeResult,
    )
    from aware_issue_sdk.operation import (
        IssueReadProjectionResolveResult as OriginalIssueReadResult,
    )
    from aware_issue_sdk.workspace_setup_admission_values import (
        IssueWorkspaceSetupClientCleanup as OriginalIssueClientCleanup,
    )

    from .architecture_setup import (
        ArchitectureSetupRequest as OriginalArchitectureRequest,
    )
    from .architecture_setup_admission_values import (
        WorkspaceSetupClientCleanup as OriginalWorkspaceClientCleanup,
    )
    from .architecture_setup_command_values import (
        WorkspaceSetupA1CommandEvidence as OriginalCommandEvidence,
    )
    from .architecture_setup_command_values import (
        WorkspaceSetupA1CommandRequest as OriginalReviewRequest,
    )
    from .architecture_setup_command_values import (
        WorkspaceSetupA1ReviewGuards as OriginalReviewGuards,
    )

ReviewPurpose = Literal["history", "current_use"]
ScopeChoice = Literal["accept_reviewed_effect_scope"]
FinalChoice = Literal["accept_reviewed_final_files"]
DispatchAction = Literal["scope", "apply"]
DispatchKnowledge = Literal["not_observed", "attempted", "unknown"]
CaptureKind = Literal["command_v1", "issue_result_v1", "issue_failure_v1"]
ScopeOutcomeKind = Literal["result", "failure", "unknown"]
ScopeCompletionStatus = Literal["continuation_ready", "refused", "incomplete"]
RetentionStatus = Literal[
    "not_attempted", "captured", "published", "incomplete", "unknown"
]
ProductStatus = Literal[
    "not_invoked", "preview_completed", "apply_completed", "refused", "incomplete"
]
DecisionRequired = Literal["scope_review", "apply_review", "none"]
PrivacyProfile = Literal["effective_user_private_namespace_v1"]


@dataclass(frozen=True, slots=True)
class SetupTarget:
    repository_root: str
    issue_tag: str
    issue_path: str
    authority_manifest_locator: str


@dataclass(frozen=True, slots=True)
class SetupReviewRequest:
    target: SetupTarget
    architecture_request: OriginalArchitectureRequest
    execution_ref: str
    client_intent_id: str
    actor_ref: str | None
    actor_evidence_ref: str | None
    include_issue_lifecycle: bool


@dataclass(frozen=True, slots=True)
class SetupEvidenceRef:
    evidence_root: str
    root_identity: DirectoryIdentity
    locator: str
    record_contract: str
    record_sha256: str
    record_bytes: int
    attempt_ref: str
    target: SetupTarget


@dataclass(frozen=True, slots=True)
class SetupChunkDescriptor:
    ordinal: int
    locator: str
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SetupCaptureDescriptor:
    kind: CaptureKind
    byte_count: int
    sha256: str
    chunks: tuple[SetupChunkDescriptor, ...]


@dataclass(frozen=True, slots=True)
class SetupReviewRecord:
    request: SetupReviewRequest
    capture: SetupCaptureDescriptor
    issue_read: OriginalIssueReadResult
    review_guards: OriginalReviewGuards
    existing_scope: tuple[str, ...]
    physical_scope: tuple[str, ...]
    final_files: tuple[str, ...]
    correspondence_sha256: str
    scope_outcome_ref: SetupEvidenceRef | None
    ready_for_decision: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SetupReviewRead:
    reference: SetupEvidenceRef
    record: SetupReviewRecord
    original_evidence: OriginalCommandEvidence
    purpose: ReviewPurpose
    private_observation: PrivateDirectoryObservation
    reads: tuple[PrivateFileReadResult, ...]


@dataclass(frozen=True, slots=True)
class SetupScopeDecision:
    review: SetupEvidenceRef
    scope_choice: ScopeChoice
    execution_ref: str
    client_intent_id: str


@dataclass(frozen=True, slots=True)
class SetupApplyDecision:
    review: SetupEvidenceRef
    final_files_choice: FinalChoice
    execution_ref: str
    client_intent_id: str


@dataclass(frozen=True, slots=True)
class SetupScopeInputRecord:
    decision: SetupScopeDecision
    scope_paths: tuple[str, ...]
    request: OriginalScopeRequest


@dataclass(frozen=True, slots=True)
class SetupApplyInputRecord:
    decision: SetupApplyDecision
    final_files: tuple[str, ...]
    review_guards: OriginalReviewGuards
    request: OriginalReviewRequest


@dataclass(frozen=True, slots=True)
class SetupDispatchIntent:
    action: DispatchAction
    review: SetupEvidenceRef
    inputs_ref: SetupEvidenceRef
    execution_ref: str
    client_intent_id: str
    action_key: str
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class ReviewedSetupScopeInputs:
    reference: SetupEvidenceRef
    record: SetupScopeInputRecord
    intent_ref: SetupEvidenceRef


@dataclass(frozen=True, slots=True)
class ReviewedSetupApplyInputs:
    reference: SetupEvidenceRef
    record: SetupApplyInputRecord


@dataclass(frozen=True, slots=True)
class SetupUnknownScopeOutcome:
    dispatch: DispatchKnowledge
    cause_type: str
    interruption: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SetupScopeOutcomeRecord:
    scope_inputs_ref: SetupEvidenceRef
    intent_ref: SetupEvidenceRef
    outcome_kind: ScopeOutcomeKind
    capture: SetupCaptureDescriptor | None
    unknown: SetupUnknownScopeOutcome | None
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class SetupScopeContinuation:
    first_review: SetupEvidenceRef
    scope_inputs: ReviewedSetupScopeInputs
    scope_outcome_ref: SetupEvidenceRef
    original_request: OriginalScopeRequest
    original_result: OriginalScopeResult


@dataclass(frozen=True, slots=True)
class SetupScopeCompletion:
    status: ScopeCompletionStatus
    reference: SetupEvidenceRef | None
    original_outcome: (
        OriginalScopeResult | OriginalScopeFailure | SetupUnknownScopeOutcome
    )
    continuation: SetupScopeContinuation | None
    retention: RetentionEvidence
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetentionEvidence:
    status: RetentionStatus
    intent_ref: SetupEvidenceRef | None
    capture: SetupCaptureDescriptor | None
    sequence_observations: tuple[PrivateSequenceObservation, ...]
    sequence_cleanup: tuple[PrivateSequenceCleanup, ...]
    directory_cleanup: PrivateDirectoryCleanup | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]
    physical_refusal: PrivateDirectoryRefusalEvidence | None


@dataclass(frozen=True, slots=True)
class SetupOutcomeRecord:
    inputs_ref: SetupEvidenceRef
    intent_ref: SetupEvidenceRef
    product_status: ProductStatus
    capture: SetupCaptureDescriptor
    retention_prefix: RetentionEvidence
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class SetupCommandOutcome:
    product_status: ProductStatus
    original_evidence: OriginalCommandEvidence | None
    reference: SetupEvidenceRef | None
    retention: RetentionEvidence
    diagnostics: tuple[str, ...]
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class SetupEvidenceRead:
    reference: SetupEvidenceRef
    raw_bytes: bytes
    private_observation: PrivateDirectoryObservation
    reads: tuple[PrivateFileReadResult, ...]


@dataclass(frozen=True, slots=True)
class SetupConciseResult:
    product_status: ProductStatus
    reference: SetupEvidenceRef | None
    decision_required: DecisionRequired
    retention_status: RetentionStatus
    ledger_complete: bool
    diagnostics: tuple[str, ...]
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class SetupReviewFailure:
    code: str
    phase: str
    target: SetupTarget | None
    outcome: SetupCommandOutcome | None
    reference: SetupEvidenceRef | None
    retention: RetentionEvidence
    cleanup: SetupReviewClientCleanup | None
    interruption: bool


@dataclass(frozen=True, slots=True)
class SetupReviewClientCleanup:
    workspace: OriginalWorkspaceClientCleanup | None
    issue: OriginalIssueClientCleanup | None
    directory: PrivateDirectoryCleanup | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DirectoryIdentity:
    device: int
    inode: int


class SetupReviewError(RuntimeError):
    """Typed known prefix; failure does not authorize retry."""

    def __init__(self, code: str, *, failure: SetupReviewFailure):
        self.code = code
        self.failure = failure
        super().__init__(code)


REVIEW_SCHEMA_IDS = MappingProxyType(
    {
        SetupTarget: "aware.workspace.setup-review.setup-target.v1",
        SetupReviewRequest: "aware.workspace.setup-review.setup-review-request.v1",
        SetupEvidenceRef: "aware.workspace.setup-review.setup-evidence-ref.v1",
        SetupChunkDescriptor: "aware.workspace.setup-review.setup-chunk-descriptor.v1",
        SetupCaptureDescriptor: "aware.workspace.setup-review.setup-capture-descriptor.v1",
        SetupReviewRecord: "aware.workspace.setup-review.setup-review-record.v1",
        SetupReviewRead: None,
        SetupScopeDecision: "aware.workspace.setup-review.setup-scope-decision.v1",
        SetupApplyDecision: "aware.workspace.setup-review.setup-apply-decision.v1",
        SetupScopeInputRecord: "aware.workspace.setup-review.setup-scope-input-record.v1",
        SetupApplyInputRecord: "aware.workspace.setup-review.setup-apply-input-record.v1",
        SetupDispatchIntent: "aware.workspace.setup-review.setup-dispatch-intent.v1",
        ReviewedSetupScopeInputs: None,
        ReviewedSetupApplyInputs: None,
        SetupUnknownScopeOutcome: "aware.workspace.setup-review.setup-unknown-scope-outcome.v1",
        SetupScopeOutcomeRecord: "aware.workspace.setup-review.setup-scope-outcome-record.v1",
        SetupScopeContinuation: None,
        SetupScopeCompletion: None,
        RetentionEvidence: "aware.workspace.setup-review.retention-evidence.v1",
        SetupOutcomeRecord: "aware.workspace.setup-review.setup-outcome-record.v1",
        SetupCommandOutcome: None,
        SetupEvidenceRead: None,
        SetupConciseResult: "aware.workspace.setup-review.setup-concise-result.v1",
        SetupReviewFailure: None,
        SetupReviewClientCleanup: "aware.workspace.setup-review.setup-review-client-cleanup.v1",
        DirectoryIdentity: "aware.workspace.setup-review.directory-identity.v1",
    }
)

REVIEW_FIELD_TYPES = MappingProxyType(
    {
        SetupTarget: (
            ("repository_root", "RootPath"),
            ("issue_tag", "Ref"),
            ("issue_path", "RelativePath"),
            ("authority_manifest_locator", "RelativePath"),
        ),
        SetupReviewRequest: (
            ("target", "SetupTarget"),
            ("architecture_request", "OriginalArchitectureRequest"),
            ("execution_ref", "Ref"),
            ("client_intent_id", "Ref"),
            ("actor_ref", "Nullable[Ref]"),
            ("actor_evidence_ref", "Nullable[Ref]"),
            ("include_issue_lifecycle", "Bool"),
        ),
        SetupEvidenceRef: (
            ("evidence_root", "RootPath"),
            ("root_identity", "DirectoryIdentity"),
            ("locator", "RelativePath"),
            ("record_contract", "Ref"),
            ("record_sha256", "Digest"),
            ("record_bytes", "MetadataFileBytes"),
            ("attempt_ref", "Ref"),
            ("target", "SetupTarget"),
        ),
        SetupChunkDescriptor: (
            ("ordinal", "ChunkOrdinal"),
            ("locator", "RelativePath"),
            ("byte_count", "ChunkBytes"),
            ("sha256", "Digest"),
        ),
        SetupCaptureDescriptor: (
            ("kind", "CaptureKind"),
            ("byte_count", "CaptureBytes"),
            ("sha256", "Digest"),
            ("chunks", "Array[SetupChunkDescriptor,32]"),
        ),
        SetupReviewRecord: (
            ("request", "SetupReviewRequest"),
            ("capture", "SetupCaptureDescriptor"),
            ("issue_read", "OriginalIssueReadResult"),
            ("review_guards", "OriginalReviewGuards"),
            ("existing_scope", "Array[RelativePath,4096]"),
            ("physical_scope", "Array[RelativePath,4096]"),
            ("final_files", "Array[RelativePath,1024]"),
            ("correspondence_sha256", "Digest"),
            ("scope_outcome_ref", "Nullable[SetupEvidenceRef]"),
            ("ready_for_decision", "Bool"),
            ("diagnostics", "Array[Diagnostic,16]"),
        ),
        SetupReviewRead: (
            ("reference", "SetupEvidenceRef"),
            ("record", "SetupReviewRecord"),
            ("original_evidence", "OriginalCommandEvidence"),
            ("purpose", "ReviewPurpose"),
            ("private_observation", "PrivateDirectoryObservation"),
            ("reads", "Array[PrivateFileReadResult,40]"),
        ),
        SetupScopeDecision: (
            ("review", "SetupEvidenceRef"),
            ("scope_choice", "ScopeChoice"),
            ("execution_ref", "Ref"),
            ("client_intent_id", "Ref"),
        ),
        SetupApplyDecision: (
            ("review", "SetupEvidenceRef"),
            ("final_files_choice", "FinalChoice"),
            ("execution_ref", "Ref"),
            ("client_intent_id", "Ref"),
        ),
        SetupScopeInputRecord: (
            ("decision", "SetupScopeDecision"),
            ("scope_paths", "Array[RelativePath,4096]"),
            ("request", "OriginalScopeRequest"),
        ),
        SetupApplyInputRecord: (
            ("decision", "SetupApplyDecision"),
            ("final_files", "Array[RelativePath,1024]"),
            ("review_guards", "OriginalReviewGuards"),
            ("request", "OriginalReviewRequest"),
        ),
        SetupDispatchIntent: (
            ("action", "DispatchAction"),
            ("review", "SetupEvidenceRef"),
            ("inputs_ref", "SetupEvidenceRef"),
            ("execution_ref", "Ref"),
            ("client_intent_id", "Ref"),
            ("action_key", "Digest"),
            ("authorizes_retry", "False"),
        ),
        ReviewedSetupScopeInputs: (
            ("reference", "SetupEvidenceRef"),
            ("record", "SetupScopeInputRecord"),
            ("intent_ref", "SetupEvidenceRef"),
        ),
        ReviewedSetupApplyInputs: (
            ("reference", "SetupEvidenceRef"),
            ("record", "SetupApplyInputRecord"),
        ),
        SetupUnknownScopeOutcome: (
            ("dispatch", "DispatchKnowledge"),
            ("cause_type", "Code"),
            ("interruption", "Bool"),
            ("diagnostics", "Array[Diagnostic,16]"),
        ),
        SetupScopeOutcomeRecord: (
            ("scope_inputs_ref", "SetupEvidenceRef"),
            ("intent_ref", "SetupEvidenceRef"),
            ("outcome_kind", "ScopeOutcomeKind"),
            ("capture", "Nullable[SetupCaptureDescriptor]"),
            ("unknown", "Nullable[SetupUnknownScopeOutcome]"),
            ("authorizes_retry", "False"),
        ),
        SetupScopeContinuation: (
            ("first_review", "SetupEvidenceRef"),
            ("scope_inputs", "ReviewedSetupScopeInputs"),
            ("scope_outcome_ref", "SetupEvidenceRef"),
            ("original_request", "OriginalScopeRequest"),
            ("original_result", "OriginalScopeResult"),
        ),
        SetupScopeCompletion: (
            ("status", "ScopeCompletionStatus"),
            ("reference", "Nullable[SetupEvidenceRef]"),
            ("original_outcome", "ScopeOutcome"),
            ("continuation", "Nullable[SetupScopeContinuation]"),
            ("retention", "RetentionEvidence"),
            ("diagnostics", "Array[Diagnostic,16]"),
        ),
        RetentionEvidence: (
            ("status", "RetentionStatus"),
            ("intent_ref", "Nullable[SetupEvidenceRef]"),
            ("capture", "Nullable[SetupCaptureDescriptor]"),
            ("sequence_observations", "Array[PrivateSequenceObservation,16]"),
            ("sequence_cleanup", "Array[PrivateSequenceCleanup,16]"),
            ("directory_cleanup", "Nullable[PrivateDirectoryCleanup]"),
            ("ledger_complete", "Bool"),
            ("diagnostics", "Array[Diagnostic,16]"),
            ("physical_refusal", "Nullable[PrivateDirectoryRefusalEvidence]"),
        ),
        SetupOutcomeRecord: (
            ("inputs_ref", "SetupEvidenceRef"),
            ("intent_ref", "SetupEvidenceRef"),
            ("product_status", "ProductStatus"),
            ("capture", "SetupCaptureDescriptor"),
            ("retention_prefix", "RetentionEvidence"),
            ("authorizes_retry", "False"),
        ),
        SetupCommandOutcome: (
            ("product_status", "ProductStatus"),
            ("original_evidence", "Nullable[OriginalCommandEvidence]"),
            ("reference", "Nullable[SetupEvidenceRef]"),
            ("retention", "RetentionEvidence"),
            ("diagnostics", "Array[Diagnostic,16]"),
            ("authorizes_retry", "False"),
        ),
        SetupEvidenceRead: (
            ("reference", "SetupEvidenceRef"),
            ("raw_bytes", "RawBytes"),
            ("private_observation", "PrivateDirectoryObservation"),
            ("reads", "Array[PrivateFileReadResult,40]"),
        ),
        SetupConciseResult: (
            ("product_status", "ProductStatus"),
            ("reference", "Nullable[SetupEvidenceRef]"),
            ("decision_required", "DecisionRequired"),
            ("retention_status", "RetentionStatus"),
            ("ledger_complete", "Bool"),
            ("diagnostics", "Array[Diagnostic,16]"),
            ("authorizes_retry", "False"),
        ),
        SetupReviewFailure: (
            ("code", "Code"),
            ("phase", "Code"),
            ("target", "Nullable[SetupTarget]"),
            ("outcome", "Nullable[SetupCommandOutcome]"),
            ("reference", "Nullable[SetupEvidenceRef]"),
            ("retention", "RetentionEvidence"),
            ("cleanup", "Nullable[SetupReviewClientCleanup]"),
            ("interruption", "Bool"),
        ),
        SetupReviewClientCleanup: (
            ("workspace", "Nullable[OriginalWorkspaceClientCleanup]"),
            ("issue", "Nullable[OriginalIssueClientCleanup]"),
            ("directory", "Nullable[PrivateDirectoryCleanup]"),
            ("ledger_complete", "Bool"),
            ("diagnostics", "Array[Diagnostic,16]"),
        ),
        DirectoryIdentity: (("device", "U64"), ("inode", "U64")),
    }
)

REVIEW_ENUMS = MappingProxyType(
    {
        "ReviewPurpose": ("history", "current_use"),
        "ScopeChoice": ("accept_reviewed_effect_scope",),
        "FinalChoice": ("accept_reviewed_final_files",),
        "DispatchAction": ("scope", "apply"),
        "DispatchKnowledge": ("not_observed", "attempted", "unknown"),
        "CaptureKind": ("command_v1", "issue_result_v1", "issue_failure_v1"),
        "ScopeOutcomeKind": ("result", "failure", "unknown"),
        "ScopeCompletionStatus": ("continuation_ready", "refused", "incomplete"),
        "RetentionStatus": (
            "not_attempted",
            "captured",
            "published",
            "incomplete",
            "unknown",
        ),
        "ProductStatus": (
            "not_invoked",
            "preview_completed",
            "apply_completed",
            "refused",
            "incomplete",
        ),
        "DecisionRequired": ("scope_review", "apply_review", "none"),
        "PrivacyProfile": ("effective_user_private_namespace_v1",),
    }
)
REVIEW_SCALARS = MappingProxyType(
    {
        "Bool": {"kind": "boolean"},
        "False": {"kind": "literal", "value": False},
        "U64": {"kind": "integer", "minimum": 0, "maximum": 18446744073709551615},
        "U32": {"kind": "integer", "minimum": 0, "maximum": 4294967295},
        "PermissionMode": {"kind": "integer", "minimum": 0, "maximum": 4095},
        "ChunkOrdinal": {"kind": "integer", "minimum": 0, "maximum": 31},
        "ChunkBytes": {"kind": "integer", "minimum": 1, "maximum": 1048576},
        "CaptureBytes": {"kind": "integer", "minimum": 1, "maximum": 33554432},
        "MetadataFileBytes": {"kind": "integer", "minimum": 1, "maximum": 1048576},
        "Ref": {"kind": "string", "minimum_bytes": 1, "maximum_bytes": 1024},
        "Code": {"kind": "string", "minimum_bytes": 1, "maximum_bytes": 128},
        "Diagnostic": {"kind": "string", "minimum_bytes": 1, "maximum_bytes": 256},
        "Digest": {
            "kind": "string",
            "pattern": "^sha256:[0-9a-f]{64}$",
            "maximum_bytes": 71,
        },
        "RootPath": {
            "kind": "string",
            "minimum_bytes": 1,
            "maximum_bytes": 4096,
            "profile": "absolute_canonical_posix_no_symlink",
        },
        "RelativePath": {
            "kind": "string",
            "minimum_bytes": 1,
            "maximum_bytes": 1024,
            "profile": "relative_posix_no_dot_segments_max64_components",
        },
        "RawBytes": {"kind": "bytes", "minimum_bytes": 1, "maximum_bytes": 33554432},
    }
)
