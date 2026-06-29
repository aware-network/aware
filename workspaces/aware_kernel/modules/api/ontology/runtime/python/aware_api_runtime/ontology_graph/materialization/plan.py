from __future__ import annotations

from collections.abc import Sequence

from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationStep,
)

from .specs import (
    APIOntologyMaterializationSpec,
    encode_api_ontology_materialization_step_payload,
)


def build_api_ontology_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[APIOntologyMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"api:{spec.api_name}",
            step_kind="api.ontology",
            payload=encode_api_ontology_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="api",
        pipeline_id="api.compile_plan.ontology",
        lane=lane,
        steps=steps,
    )


__all__ = ["build_api_ontology_materialization_plan"]
