from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_history_ontology.change.change_enums import ChangeType

from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationBoundaryValidation,
    MetaGraphMutationSet,
)


class MetaGraphMutationBoundaryError(RuntimeError):
    """Raised when Meta cannot safely validate mutation boundaries."""


class MetaGraphMutationBoundaryNotReadyError(MetaGraphMutationBoundaryError):
    """Raised when no Meta mutation boundary policy is wired."""


class MetaGraphMutationBoundaryPolicy(Protocol):
    async def validate_mutation_boundary(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
    ) -> MetaGraphMutationBoundaryValidation: ...


@dataclass(frozen=True, slots=True)
class MetaGraphMutationBoundaryValidatorPhase:
    """Validate Meta mutation sets before append-ready OIG assembly."""

    policy: MetaGraphMutationBoundaryPolicy | None = None

    async def validate_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
    ) -> MetaGraphMutationBoundaryValidation:
        _validate_boundary_inputs(request=request, mutation_set=mutation_set)
        if self.policy is None:
            function_config = request.execution_plan.implementation.function_config
            raise MetaGraphMutationBoundaryNotReadyError(
                "Meta mutation boundary policy is not wired. "
                f"function_call_id={request.staged_call.function_call.id} "
                f"function_id={function_config.id} "
                f"mutation_change_count={len(mutation_set.changes)}"
            )
        validation = await self.policy.validate_mutation_boundary(
            request,
            mutation_set,
        )
        return build_meta_graph_mutation_boundary_validation(
            request=request,
            mutation_set=mutation_set,
            validation=validation,
        )


@dataclass(frozen=True, slots=True)
class MetaGraphMutateSelfOnlyPolicy:
    """Enforce the Graph-OS mutate-self-only doctrine."""

    async def validate_mutation_boundary(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
    ) -> MetaGraphMutationBoundaryValidation:
        _validate_boundary_inputs(request=request, mutation_set=mutation_set)
        violation = _mutate_self_violation(request=request, mutation_set=mutation_set)
        if violation is not None:
            return MetaGraphMutationBoundaryValidation(
                execution_plan=request.execution_plan,
                mutation_set=mutation_set,
                status=MetaGraphMutationBoundaryStatus.rejected,
                violation_message=violation,
            )
        return MetaGraphMutationBoundaryValidation(
            execution_plan=request.execution_plan,
            mutation_set=mutation_set,
            status=MetaGraphMutationBoundaryStatus.accepted,
        )


def build_meta_graph_mutation_boundary_validation(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
    validation: MetaGraphMutationBoundaryValidation,
) -> MetaGraphMutationBoundaryValidation:
    _validate_boundary_inputs(request=request, mutation_set=mutation_set)
    if validation.execution_plan is not request.execution_plan:
        raise MetaGraphMutationBoundaryError(
            "Meta mutation boundary validation used a different execution plan."
        )
    if validation.mutation_set is not mutation_set:
        raise MetaGraphMutationBoundaryError(
            "Meta mutation boundary validation used a different mutation set."
        )
    return validation


def _mutate_self_violation(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
) -> str | None:
    execution_plan = request.execution_plan
    target_class_instance_id = (
        mutation_set.target_class_instance_id or execution_plan.target_object_id
    )
    is_constructor = execution_plan.implementation.is_constructor
    constructor_root_class_instance_id = None
    if is_constructor:
        constructor_root_class_instance_id = (
            mutation_set.before_oig.root_class_instance_id
        )
    constructed_ids = set(mutation_set.constructed_class_instance_ids)
    constructor_root_descendant_ids = (
        _descendant_class_instance_ids(
            mutation_set=mutation_set,
            target_class_instance_id=constructor_root_class_instance_id,
        )
        if constructor_root_class_instance_id is not None
        else set()
    )
    target_descendant_ids = (
        _descendant_class_instance_ids(
            mutation_set=mutation_set,
            target_class_instance_id=target_class_instance_id,
        )
        if target_class_instance_id is not None
        else set()
    )
    created_ids: set[UUID] = set()

    for root in mutation_set.changes:
        for class_change in root.class_instance_changes:
            change_type = class_change.change.type
            class_instance_id = class_change.class_instance_id
            if change_type is ChangeType.create:
                created_ids.add(class_instance_id)
                if not is_constructor and class_instance_id not in constructed_ids:
                    return (
                        "Class instance create is allowed only through a "
                        "constructor invocation or an explicit nested "
                        "constructor message. "
                        f"class_instance_id={class_instance_id} "
                        f"function_call_id={request.staged_call.function_call.id}"
                    )
                continue
            if (
                is_constructor
                and class_instance_id == constructor_root_class_instance_id
            ):
                continue
            if is_constructor and class_instance_id in constructor_root_descendant_ids:
                continue
            if class_instance_id in constructed_ids:
                continue
            if class_instance_id in target_descendant_ids:
                continue
            if target_class_instance_id is None:
                return (
                    "Class instance mutation requires an invoked target object. "
                    f"class_instance_id={class_instance_id} "
                    f"change_type={change_type.value}"
                )
            if class_instance_id != target_class_instance_id:
                return (
                    "Cross-object class mutation detected. "
                    f"target_object_id={target_class_instance_id} "
                    f"class_instance_id={class_instance_id} "
                    f"change_type={change_type.value}"
                )

    for root in mutation_set.changes:
        for relationship_change in root.class_instance_relationship_changes:
            source_id = relationship_change.source_class_instance_id
            if source_id == target_class_instance_id:
                continue
            if is_constructor and source_id == constructor_root_class_instance_id:
                continue
            if is_constructor and source_id in constructor_root_descendant_ids:
                continue
            if is_constructor and source_id in created_ids:
                continue
            if source_id in constructed_ids:
                continue
            if source_id in target_descendant_ids:
                continue
            return (
                "Cross-object relationship mutation detected. "
                f"target_object_id={target_class_instance_id} "
                f"source_class_instance_id={source_id} "
                f"target_class_instance_id="
                f"{relationship_change.target_class_instance_id}"
            )
    return None


def _descendant_class_instance_ids(
    *,
    mutation_set: MetaGraphMutationSet,
    target_class_instance_id: UUID,
) -> set[UUID]:
    relationships_by_source: dict[UUID, list[UUID]] = {}
    for relationship in mutation_set.before_oig.class_instance_relationships:
        relationships_by_source.setdefault(
            relationship.source_class_instance_id,
            [],
        ).append(relationship.target_class_instance_id)

    descendants: set[UUID] = set()
    stack = list(relationships_by_source.get(target_class_instance_id, ()))
    while stack:
        class_instance_id = stack.pop()
        if class_instance_id in descendants:
            continue
        descendants.add(class_instance_id)
        stack.extend(relationships_by_source.get(class_instance_id, ()))
    return descendants


def _validate_boundary_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
) -> None:
    if mutation_set.execution_plan is not request.execution_plan:
        raise MetaGraphMutationBoundaryError(
            "Meta mutation boundary validation requires mutations from the "
            "same execution plan."
        )


__all__ = [
    "build_meta_graph_mutation_boundary_validation",
    "MetaGraphMutateSelfOnlyPolicy",
    "MetaGraphMutationBoundaryError",
    "MetaGraphMutationBoundaryNotReadyError",
    "MetaGraphMutationBoundaryPolicy",
    "MetaGraphMutationBoundaryValidatorPhase",
]
