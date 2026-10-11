# Non-executable qualification signatures. No capability constructors or codecs.
# Existing owner return values remain their original types, not copied evaluators.
from pathlib import Path
from typing import Literal

from aware_issue_sdk.operation import IssueMutationResult, IssueStartProgressRequest
from aware_workspace_runtime.repository_mutation import (
    WorkspaceRepositoryAuthorizedMutation,
)

type WorkspaceSourceProjectionPhase = Literal[
    "prepared", "enrolled", "spent", "terminal", "retired"
]
type WorkspaceSourcePhysicalEffectState = Literal["none", "applied", "unknown"]
type WorkspaceSourcePhysicalReturnState = Literal[
    "not_dispatched", "returned", "unavailable"
]
type WorkspaceSourceBodyRetentionState = Literal["not_attempted", "retained", "unknown"]
type WorkspaceSourceConvergenceState = Literal[
    "not_attempted", "converged", "failed", "unknown"
]
type WorkspaceSourceRetentionState = Literal[
    "not_attempted", "retained", "unavailable", "unknown"
]
type WorkspaceSourceCleanupState = Literal[
    "not_attempted", "completed", "incomplete", "unknown"
]
type WorkspaceSourcePhysicalGuarantee = Literal[
    "descriptor_walk_v1", "continuous_root_v1"
]

class RepositoryObservationCoordinate:
    repository_binding_ref: str
    epoch: str
    cursor: int
    snapshot_digest: str
    visibility_policy_ref: str
    visibility_policy_version: str

class WorkspaceRepositoryPhysicalEffect:
    state: WorkspaceSourcePhysicalEffectState
    durability_confirmed: bool
    before_exists: bool
    before_content_digest: str | None
    before_size_bytes: int | None
    after_exists: bool
    after_content_digest: str | None
    after_size_bytes: int | None

class WorkspaceRepositoryMutationExecutionEvidence:
    physical_return_state: WorkspaceSourcePhysicalReturnState
    body_retention_state: WorkspaceSourceBodyRetentionState
    ledger_complete: bool
    diagnostics: tuple[str, ...]

class WorkspaceSourceProviderBinding:
    provider_ref: str
    provider_generation: str
    execution_id: str
    original_process_id: int
    original_thread_id: int

class WorkspaceSourceFileIdentity:
    device: int
    inode: int

class WorkspaceSourceObservation:
    observation_ref: str
    provider: WorkspaceSourceProviderBinding
    repository_binding_ref: str
    target_path: str
    root_identity: WorkspaceSourceFileIdentity
    target_identity: WorkspaceSourceFileIdentity
    coordinate: RepositoryObservationCoordinate
    content_digest: str
    size_bytes: int
    body_ref: str

class WorkspaceSourceProjectionRequest:
    source: WorkspaceSourceObservation
    operation_ref: str
    domain_target_ref: str
    profile_ref: str
    projected_content_digest: str
    projected_size_bytes: int
    projected_body_ref: str
    physical_guarantee: WorkspaceSourcePhysicalGuarantee

class WorkspaceSourceProjectionBinding:
    binding_ref: str
    attempt_ref: str
    provider: WorkspaceSourceProviderBinding
    operation_ref: str
    domain_target_ref: str
    profile_ref: str
    source_observation_ref: str
    repository_binding_ref: str
    target_path: str
    root_identity: WorkspaceSourceFileIdentity
    target_identity: WorkspaceSourceFileIdentity
    expected_coordinate: RepositoryObservationCoordinate
    expected_content_digest: str
    projected_content_digest: str
    projected_size_bytes: int
    preimage_body_ref: str
    projected_body_ref: str
    physical_guarantee: WorkspaceSourcePhysicalGuarantee

class WorkspaceSourceProjectionPlanObservation:
    binding: WorkspaceSourceProjectionBinding
    phase: WorkspaceSourceProjectionPhase
    original_plan_recognized: bool
    diagnostics: tuple[str, ...]

class WorkspaceSourceProjectionRetentionObservation:
    state: WorkspaceSourceRetentionState
    retention_ref: str | None
    preimage_body_ref: str | None
    postimage_body_ref: str | None
    capture_ref: str | None
    content_delta_ref: str | None
    before_coordinate: RepositoryObservationCoordinate | None
    after_coordinate: RepositoryObservationCoordinate | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]

class WorkspaceSourceProjectionCleanupObservation:
    state: WorkspaceSourceCleanupState
    observer_cleanup_state: WorkspaceSourceCleanupState
    retention_cleanup_state: WorkspaceSourceCleanupState
    physical_cleanup_state: WorkspaceSourceCleanupState
    ledger_complete: bool
    diagnostics: tuple[str, ...]

class WorkspaceSourceProjectionObservation:
    binding: WorkspaceSourceProjectionBinding
    phase: WorkspaceSourceProjectionPhase
    source_effect_state: WorkspaceSourcePhysicalEffectState
    mutation_receipt_ref: str | None
    physical_effect: WorkspaceRepositoryPhysicalEffect | None
    execution_evidence: WorkspaceRepositoryMutationExecutionEvidence | None
    convergence_state: WorkspaceSourceConvergenceState
    retention: WorkspaceSourceProjectionRetentionObservation
    cleanup: WorkspaceSourceProjectionCleanupObservation
    ledger_complete: bool
    diagnostics: tuple[str, ...]

class WorkspaceSourceProjectionRefusalEvidence:
    code: str
    observation: WorkspaceSourceProjectionObservation | None
    cleanup: WorkspaceSourceProjectionCleanupObservation | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]

# All following classes describe original handles, not serializable values.
class WorkspaceSourceProjectionPlan: ...
class WorkspaceSourceProjectionAdmission: ...
class IssueStartProgressProjectionPlan: ...
class IssueSourceProjectionAdmission: ...
class IssueSourceProjectionConsumption: ...

class WorkspaceRepositorySourceProjectionClient:
    @classmethod
    def filesystem(
        cls, *, repository_root: Path, state_root: Path, execution_id: str
    ) -> WorkspaceRepositorySourceProjectionClient: ...
    async def observe_source(
        self, *, target_path: str
    ) -> WorkspaceSourceObservation: ...
    async def retain_projection_body(
        self,
        content: bytes,
        *,
        expected_content_digest: str,
        expected_size_bytes: int,
    ) -> str: ...
    async def prepare_source_projection(
        self, request: WorkspaceSourceProjectionRequest
    ) -> WorkspaceSourceProjectionPlan: ...
    def observe_source_projection_plan(
        self, plan: WorkspaceSourceProjectionPlan
    ) -> WorkspaceSourceProjectionPlanObservation: ...
    def verify_source_projection_plan(
        self,
        plan: WorkspaceSourceProjectionPlan,
        *,
        expected_binding: WorkspaceSourceProjectionBinding,
    ) -> WorkspaceSourceProjectionPlanObservation: ...
    async def enroll_issue_projection(
        self,
        plan: WorkspaceSourceProjectionPlan,
        *,
        issue_admission: IssueSourceProjectionAdmission,
    ) -> WorkspaceSourceProjectionAdmission: ...
    async def project_source(
        self,
        plan: WorkspaceSourceProjectionPlan,
        *,
        admission: WorkspaceSourceProjectionAdmission,
    ) -> WorkspaceSourceProjectionObservation: ...
    def observe_source_projection(
        self, admission: WorkspaceSourceProjectionAdmission
    ) -> WorkspaceSourceProjectionObservation: ...
    async def resolve_source_projection_receipt(
        self, admission: WorkspaceSourceProjectionAdmission
    ) -> WorkspaceRepositoryAuthorizedMutation | None: ...
    async def release_source_projection(
        self,
    ) -> WorkspaceSourceProjectionCleanupObservation: ...

class IssueStartProgressProjectionClient:
    @classmethod
    def filesystem(
        cls, *, repository_root: Path, execution_id: str
    ) -> IssueStartProgressProjectionClient: ...
    async def prepare_start_progress_projection(
        self,
        request: IssueStartProgressRequest,
        *,
        workspace_client: WorkspaceRepositorySourceProjectionClient,
    ) -> IssueStartProgressProjectionPlan: ...
    async def admit_start_progress_projection(
        self, plan: IssueStartProgressProjectionPlan
    ) -> IssueSourceProjectionAdmission: ...
    async def execute_start_progress_projection(
        self,
        plan: IssueStartProgressProjectionPlan,
        *,
        admission: IssueSourceProjectionAdmission,
    ) -> IssueMutationResult: ...

# Fixed supplying Issue SDK leaf ports, never a caller-injected instance/callback.
def verify_source_projection_admission(
    admission: IssueSourceProjectionAdmission,
    *,
    expected_binding: WorkspaceSourceProjectionBinding,
) -> WorkspaceSourceProjectionBinding: ...
def consume_source_projection_admission(
    admission: IssueSourceProjectionAdmission,
    *,
    binding: WorkspaceSourceProjectionBinding,
) -> IssueSourceProjectionConsumption: ...
