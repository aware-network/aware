from __future__ import annotations

from dataclasses import dataclass

from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphAppendReadyChanges,
    MetaGraphHandlerExecutionRequest,
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationBoundaryValidation,
    MetaGraphMutationSet,
)


class MetaGraphAppendReadyAssemblyError(RuntimeError):
    """Raised when append-ready OIG changes cannot be assembled safely."""


@dataclass(frozen=True, slots=True)
class MetaGraphAppendReadyChangeAssemblerPhase:
    """Assemble append-ready OIG changes after boundary validation."""

    async def assemble_append_ready_changes(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
        boundary_validation: MetaGraphMutationBoundaryValidation,
    ) -> MetaGraphAppendReadyChanges:
        return build_meta_graph_append_ready_changes(
            request=request,
            mutation_set=mutation_set,
            boundary_validation=boundary_validation,
        )


def build_meta_graph_append_ready_changes(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
    boundary_validation: MetaGraphMutationBoundaryValidation,
) -> MetaGraphAppendReadyChanges:
    _validate_append_ready_inputs(
        request=request,
        mutation_set=mutation_set,
        boundary_validation=boundary_validation,
    )
    if boundary_validation.status is not MetaGraphMutationBoundaryStatus.accepted:
        raise MetaGraphAppendReadyAssemblyError(
            "Cannot assemble append-ready changes for rejected mutations. "
            f"violation_message={boundary_validation.violation_message}"
        )
    if not mutation_set.graph_hash_pre:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes require graph_hash_pre from mutation set."
        )
    if not mutation_set.graph_hash_post:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes require graph_hash_post from mutation set."
        )
    return MetaGraphAppendReadyChanges(
        execution_plan=request.execution_plan,
        before_oig=mutation_set.before_oig,
        changes=mutation_set.changes,
        graph_hash_pre=mutation_set.graph_hash_pre,
        graph_hash_post=mutation_set.graph_hash_post,
        root_object_id=mutation_set.root_object_id,
        root_class_instance_identity_id=mutation_set.root_class_instance_identity_id,
    )


def _validate_append_ready_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
    boundary_validation: MetaGraphMutationBoundaryValidation,
) -> None:
    execution_plan = request.execution_plan
    if mutation_set.execution_plan is not execution_plan:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires mutations from the same execution plan."
        )
    if boundary_validation.execution_plan is not execution_plan:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires boundary validation from the same "
            "execution plan."
        )
    if boundary_validation.mutation_set is not mutation_set:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires boundary validation for the same "
            "mutation set."
        )


__all__ = [
    "build_meta_graph_append_ready_changes",
    "MetaGraphAppendReadyAssemblyError",
    "MetaGraphAppendReadyChangeAssemblerPhase",
]
