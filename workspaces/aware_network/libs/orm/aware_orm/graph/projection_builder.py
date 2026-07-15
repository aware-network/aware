"""Build JSON projection expressions from plan context."""

from __future__ import annotations

from typing import List

from .plan_context import PlanContext

__all__ = ["ProjectionBuilder"]


class ProjectionBuilder:
    def __init__(self, context: PlanContext):
        self._context = context

    def build_root_projection(self) -> str:
        descriptor = self._context.root_descriptor()
        fields = [f"'{attr}', roots.{attr}" for attr in descriptor.attributes if attr]
        if "id" not in descriptor.attributes:
            fields.insert(0, "'id', roots.id")
        return f"json_build_object({', '.join(fields)})"

    def build_step_projection(self) -> List[str]:
        projections: List[str] = []
        for idx, (step, descriptor) in enumerate(self._context.iter_step_descriptors(), start=1):
            alias = f"cte_{idx}"
            if step.projection_fields:
                fields = [f"'{field}', {alias}.{field}" for field in step.projection_fields]
            else:
                fields = [f"'{attr}', {alias}.{attr}" for attr in descriptor.attributes if attr]
            projections.append(f"json_agg(json_build_object({', '.join(fields)})) AS {descriptor.table_name}")
        return projections
