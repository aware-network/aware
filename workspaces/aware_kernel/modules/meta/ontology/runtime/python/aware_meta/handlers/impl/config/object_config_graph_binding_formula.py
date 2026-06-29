from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_binding_formula import ObjectConfigGraphBindingFormula
from aware_meta_ontology.graph.config.object_config_graph_binding_formula_segment_reference import (
    ObjectConfigGraphBindingFormulaSegmentReference,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_segment_reference(
    object_config_graph_binding_formula: ObjectConfigGraphBindingFormula,
    content_part_text_segment_id: UUID,
    source_class_config_attribute_config_id: UUID,
) -> ObjectConfigGraphBindingFormulaSegmentReference:
    """
    Create deterministic placeholder/source-attribute reference within this
    formula scope.

    Contract:
    - Placeholder semantics stay in Meta; `content` remains generic.
    - The referenced segment must belong to this formula's `content_part_text`.
    - Stable identity resolves from formula scope plus the referenced segment
    and source class attribute config.
    """

    # --- AWARE: LOGIC START create_segment_reference
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_segment_reference


async def build_via_object_config_graph_binding_class(
    object_config_graph_binding_class_id: UUID, key: str = "default", content_part_text_id: UUID | None = None
) -> ObjectConfigGraphBindingFormula:
    """
    Build deterministic ObjectConfigGraphBindingFormula within an
    ObjectConfigGraphBindingClass scope.

    Contract:
    - Parent binding-class scope is propagated via
    `ObjectConfigGraphBindingClass -> ObjectConfigGraphBindingFormula`.
    - Stable identity resolves from
    `(object_config_graph_binding_class_id via path, key)`.
    - `content_part_text_id` may be set during construction or later.
    """

    # --- AWARE: LOGIC START build_via_object_config_graph_binding_class
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_object_config_graph_binding_class
