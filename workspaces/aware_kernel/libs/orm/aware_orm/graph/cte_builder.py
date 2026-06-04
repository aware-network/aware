"""Build Common Table Expressions (CTEs) from plan context."""

from __future__ import annotations

from typing import List

from .plan_context import PlanContext

__all__ = ["CTEBuilder"]


class CTEBuilder:
    def __init__(self, context: PlanContext):
        self._context = context

    def build(self) -> List[str]:
        ctes: List[str] = []
        for index, (step, descriptor) in enumerate(self._context.iter_step_descriptors(), start=1):
            alias = f"cte_{index}"
            join_condition = step.join_condition or "TRUE"
            cte_sql = (
                f"{alias} AS (\n"
                f"    SELECT * FROM {descriptor.table_schema}.{descriptor.table_name}\n"
                f"    WHERE {join_condition}\n"
                f")"
            )
            ctes.append(cte_sql)
        return ctes
