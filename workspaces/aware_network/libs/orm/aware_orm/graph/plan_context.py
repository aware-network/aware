"""Context objects for plan-driven GraphSQL generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .config_registry import GraphConfigRegistry, TableDescriptor
from .plan_cache import GraphPlan

__all__ = ["PlanContext"]


@dataclass(frozen=True)
class PlanContext:
    plan: GraphPlan
    config_registry: GraphConfigRegistry

    def root_descriptor(self) -> TableDescriptor:
        descriptor = self.config_registry.get(self.plan.root_table_key)
        if descriptor:
            return descriptor
        schema, table = self.plan.root_table_key.split(".", 1)
        return TableDescriptor(
            table_schema=schema,
            table_name=table,
            attributes=self.plan.root_projection_fields,
        )

    def iter_step_descriptors(self) -> Iterable[tuple]:
        for step in self.plan.steps:
            descriptor = self.config_registry.get(step.table_key)
            if descriptor is None:
                schema, table = step.table_key.split(".", 1)
                descriptor = TableDescriptor(
                    table_schema=schema,
                    table_name=table,
                    attributes=step.projection_fields,
                )
            yield step, descriptor
