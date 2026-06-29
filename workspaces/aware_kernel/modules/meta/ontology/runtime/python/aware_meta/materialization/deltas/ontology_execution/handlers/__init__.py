from __future__ import annotations

from aware_meta.materialization.deltas.ontology_execution.handlers.attribute import (
    plan_attribute_operation,
)
from aware_meta.materialization.deltas.ontology_execution.handlers.class_ import (
    plan_class_operation,
)
from aware_meta.materialization.deltas.ontology_execution.handlers.function_impl import (
    plan_function_impl_operation,
)
from aware_meta.materialization.deltas.ontology_execution.handlers.relationship import (
    plan_relationship_operation,
)

__all__ = [
    "plan_attribute_operation",
    "plan_class_operation",
    "plan_function_impl_operation",
    "plan_relationship_operation",
]
