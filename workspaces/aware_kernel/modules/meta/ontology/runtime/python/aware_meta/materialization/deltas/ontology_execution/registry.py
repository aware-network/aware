from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.materialization.deltas.feature_registry import (
    ontology_operation_registrations as feature_ontology_operation_registrations,
)

OntologyOperationPlanner = Callable[
    [OntologyTypedOperation, OntologyExecutionPlanningContext],
    OntologyOperationHandlerResult,
]


@dataclass(frozen=True, slots=True)
class OntologyOperationHandlerRegistration:
    handler_key: str
    ontology_subject_kind: str
    operation_families: tuple[str, ...]
    planner: OntologyOperationPlanner

    def registration_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (self.ontology_subject_kind, operation_family)
            for operation_family in self.operation_families
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "handler_key": self.handler_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_families": self.operation_families,
        }


_LEGACY_HANDLER_REGISTRATIONS: tuple[OntologyOperationHandlerRegistration, ...] = ()


def _feature_handler_registrations() -> tuple[
    OntologyOperationHandlerRegistration,
    ...,
]:
    return tuple(
        OntologyOperationHandlerRegistration(
            handler_key=registration.handler_key,
            ontology_subject_kind=registration.ontology_subject_kind,
            operation_families=registration.operation_families,
            planner=registration.planner,
        )
        for registration in feature_ontology_operation_registrations()
    )


_HANDLER_REGISTRATIONS = (
    *_LEGACY_HANDLER_REGISTRATIONS,
    *_feature_handler_registrations(),
)

_HANDLER_BY_KEY: Mapping[tuple[str, str], OntologyOperationPlanner] = {
    registration_key: registration.planner
    for registration in _HANDLER_REGISTRATIONS
    for registration_key in registration.registration_keys()
}


def plan_operation(
    operation: OntologyTypedOperation,
    *,
    context: OntologyExecutionPlanningContext | None = None,
) -> OntologyOperationHandlerResult:
    planning_context = context or OntologyExecutionPlanningContext()
    planner = _HANDLER_BY_KEY.get(
        (operation.ontology_subject_kind, operation.operation_family)
    )
    if planner is not None:
        return planner(operation, planning_context)
    return blocked_handler_result(
        operation=operation,
        handler_key=f"{operation.ontology_subject_kind}.unimplemented",
        reason="meta_ocg_ontology_execution_handler_not_registered",
        blockers=(
            "ontology_function_call_handler_missing:"
            f"{operation.ontology_subject_kind}.{operation.operation_family}",
        ),
    )


def registered_operation_handler_keys() -> tuple[str, ...]:
    return tuple(
        sorted(
            dict.fromkeys(
                registration.handler_key for registration in _HANDLER_REGISTRATIONS
            )
        )
    )


def registered_operation_families() -> dict[str, tuple[str, ...]]:
    families_by_subject: dict[str, set[str]] = {}
    for registration in _HANDLER_REGISTRATIONS:
        families_by_subject.setdefault(
            registration.ontology_subject_kind,
            set(),
        ).update(registration.operation_families)
    return {
        subject_kind: tuple(sorted(operation_families))
        for subject_kind, operation_families in sorted(families_by_subject.items())
    }


def registered_operation_handler_specs() -> tuple[dict[str, object], ...]:
    return tuple(
        registration.evidence_payload()
        for registration in _HANDLER_REGISTRATIONS
    )


__all__ = [
    "OntologyOperationHandlerRegistration",
    "plan_operation",
    "registered_operation_families",
    "registered_operation_handler_keys",
    "registered_operation_handler_specs",
]
