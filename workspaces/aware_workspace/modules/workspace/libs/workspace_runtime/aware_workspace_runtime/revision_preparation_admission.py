# pyright: reportUninitializedInstanceVariable=false
"""Process-local authority for Workspace revision preparation inputs."""

from __future__ import annotations

from typing import Never, cast

from aware_code_semantic_contract_runtime import canonical_json_bytes

from .revision_preparation_contracts import (
    WorkspaceMaterializationGraphExecutionAdmission,
    WorkspaceRevisionPackageMembershipTransitionSet,
    WorkspaceRevisionPredecessorAdmission,
    WorkspaceRevisionSelectionScopeAdmission,
    WorkspaceRevisionSourceClosure,
    WorkspaceRevisionSourceClosureAdmission,
)
from .semantic_dependency_graph import (
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
)


class WorkspaceRevisionPreparationAdmissionError(RuntimeError):
    """Raised when process-local preparation authority is absent or moved."""


class WorkspaceMaterializationGraphExecutionAdmissionCapability:
    """Opaque authority for one exact completed Graph V2 execution."""

    __slots__ = ("__weakref__",)

    def __new__(cls):  # type: ignore[no-untyped-def]
        raise TypeError("graph execution capability is host-issued only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("graph execution capability is sealed")

    def __copy__(self) -> Never:
        raise TypeError("graph execution capability is not copyable")

    def __deepcopy__(self, memo: object) -> Never:
        del memo
        raise TypeError("graph execution capability is not copyable")

    def __reduce__(self) -> Never:
        raise TypeError("graph execution capability is not serializable")


class WorkspaceRevisionPreparationContextCapability:
    """Opaque authority joining predecessor, source, membership and selection."""

    __slots__ = ("__weakref__",)

    def __new__(cls):  # type: ignore[no-untyped-def]
        raise TypeError("revision preparation context is issuer-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("revision preparation context is sealed")

    def __copy__(self) -> Never:
        raise TypeError("revision preparation context is not copyable")

    def __deepcopy__(self, memo: object) -> Never:
        del memo
        raise TypeError("revision preparation context is not copyable")

    def __reduce__(self) -> Never:
        raise TypeError("revision preparation context is not serializable")


def _completed_state(execution: object):  # type: ignore[no-untyped-def]
    from .materialization_graph_coordinator import (
        AdmittedWorkspaceSemanticMaterializationGraphExecution,
        WorkspaceSemanticMaterializationGraphExecutionError,
        _execution_state,
    )

    try:
        return _execution_state(
            cast(AdmittedWorkspaceSemanticMaterializationGraphExecution, execution)
        )
    except (TypeError, WorkspaceSemanticMaterializationGraphExecutionError) as error:
        raise WorkspaceRevisionPreparationAdmissionError(
            "graph completion is not the exact current-process execution"
        ) from error


def admit_completed_workspace_materialization_graph_execution(
    *,
    execution: object,
    owner: object,
    result: WorkspaceSemanticMaterializationGraphResultV3,
) -> tuple[
    WorkspaceMaterializationGraphExecutionAdmission,
    WorkspaceMaterializationGraphExecutionAdmissionCapability,
]:
    """Return the pair minted inside the exact completed coordinator boundary."""

    if type(result) is not WorkspaceSemanticMaterializationGraphResultV3:
        raise TypeError("completed graph result must be exact")
    from .materialization_graph_coordinator import (
        _current_graph_execution_incarnation,
    )

    state = _completed_state(execution)
    process_id, incarnation = _current_graph_execution_incarnation()
    if (
        state.status != "completed"
        or state.revision_preparation_process_id != process_id
        or state.revision_preparation_incarnation is not incarnation
        or state.owner is not owner
        or state.revision_preparation_result is not result
        or type(state.revision_preparation_admission)
        is not WorkspaceMaterializationGraphExecutionAdmission
        or type(state.revision_preparation_capability)
        is not WorkspaceMaterializationGraphExecutionAdmissionCapability
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "graph completion is not the exact current-process execution"
        )
    verify_workspace_materialization_graph_execution_admission(
        capability=state.revision_preparation_capability,
        admission=state.revision_preparation_admission,
        execution=execution,
        owner=owner,
        plan=state.admitted_plan_result,
        result=result,
    )
    return state.revision_preparation_admission, state.revision_preparation_capability


def verify_workspace_materialization_graph_execution_admission(
    *,
    capability: WorkspaceMaterializationGraphExecutionAdmissionCapability,
    admission: WorkspaceMaterializationGraphExecutionAdmission,
    execution: object,
    owner: object,
    plan: WorkspaceSemanticMaterializationGraphPlanResult,
    result: WorkspaceSemanticMaterializationGraphResultV3,
) -> None:
    if (
        type(capability)
        is not WorkspaceMaterializationGraphExecutionAdmissionCapability
    ):
        raise TypeError("graph capability must be exact")
    if type(admission) is not WorkspaceMaterializationGraphExecutionAdmission:
        raise TypeError("graph admission must be exact")
    if type(plan) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph plan must be exact")
    if type(result) is not WorkspaceSemanticMaterializationGraphResultV3:
        raise TypeError("graph result must be exact")
    from .materialization_graph_coordinator import (
        _current_graph_execution_incarnation,
    )

    state = _completed_state(execution)
    process_id, incarnation = _current_graph_execution_incarnation()
    if (
        state.status != "completed"
        or state.revision_preparation_process_id != process_id
        or state.revision_preparation_incarnation is not incarnation
        or state.owner is not owner
        or state.admitted_plan_result is not plan
        or state.revision_preparation_result is not result
        or state.revision_preparation_admission is not admission
        or state.revision_preparation_capability is not capability
        or state.plan_wire != canonical_json_bytes(plan.to_wire())
        or state.revision_preparation_result_wire
        != canonical_json_bytes(result.to_wire())
        or state.revision_preparation_admission_wire != admission.canonical_bytes()
    ):
        raise WorkspaceRevisionPreparationAdmissionError(
            "graph execution admission context differs"
        )


def verify_workspace_revision_preparation_context(
    *,
    capability: WorkspaceRevisionPreparationContextCapability,
    owner: object,
    operation_authority_digest: str,
    workspace_ref: str,
    branch_ref: str,
    predecessor: WorkspaceRevisionPredecessorAdmission,
    predecessor_state: object | None,
    predecessor_source_closure: WorkspaceRevisionSourceClosure | None,
    source_closure: WorkspaceRevisionSourceClosure,
    source_admission: WorkspaceRevisionSourceClosureAdmission,
    selection: WorkspaceRevisionSelectionScopeAdmission,
    transitions: WorkspaceRevisionPackageMembershipTransitionSet,
) -> None:
    _verify_workspace_revision_preparation_context_stage(
        stage="selection",
        capability=capability,
        owner=owner,
        operation_authority_digest=operation_authority_digest,
        workspace_ref=workspace_ref,
        branch_ref=branch_ref,
        predecessor=predecessor,
        predecessor_state=predecessor_state,
        predecessor_source_closure=predecessor_source_closure,
        source_closure=source_closure,
        source_admission=source_admission,
        selection=selection,
        transitions=transitions,
    )


def _verify_workspace_revision_preparation_context_stage(
    *,
    stage: str,
    capability: WorkspaceRevisionPreparationContextCapability,
    owner: object,
    operation_authority_digest: str,
    workspace_ref: str,
    branch_ref: str,
    predecessor: WorkspaceRevisionPredecessorAdmission,
    predecessor_state: object | None,
    predecessor_source_closure: WorkspaceRevisionSourceClosure | None,
    source_closure: WorkspaceRevisionSourceClosure,
    source_admission: WorkspaceRevisionSourceClosureAdmission,
    selection: WorkspaceRevisionSelectionScopeAdmission,
    transitions: WorkspaceRevisionPackageMembershipTransitionSet,
) -> None:
    """Fail closed until a separately governed host context issuer is installed."""

    if stage not in ("predecessor", "source", "selection"):
        raise ValueError("revision preparation verification stage is unsupported")
    if type(capability) is not WorkspaceRevisionPreparationContextCapability:
        raise TypeError("revision preparation context capability must be exact")
    del (
        owner,
        operation_authority_digest,
        workspace_ref,
        branch_ref,
        predecessor,
        predecessor_state,
        predecessor_source_closure,
        source_closure,
        source_admission,
        selection,
        transitions,
    )
    raise WorkspaceRevisionPreparationAdmissionError(
        "revision preparation context issuer is unavailable"
    )


__all__ = [
    "WorkspaceMaterializationGraphExecutionAdmissionCapability",
    "WorkspaceRevisionPreparationAdmissionError",
    "WorkspaceRevisionPreparationContextCapability",
    "admit_completed_workspace_materialization_graph_execution",
    "verify_workspace_materialization_graph_execution_admission",
    "verify_workspace_revision_preparation_context",
]
