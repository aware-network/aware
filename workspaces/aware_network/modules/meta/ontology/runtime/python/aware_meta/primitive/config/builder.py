# Code Runtime
from aware_code.primitive_signature import build_code_primitive_signature

# Code Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Meta Ontology
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# Meta Runtime
from aware_meta.graph.config.stable_ids import (
    stable_code_primitive_type_id,
    stable_code_primitive_type_element_type_id,
    stable_code_primitive_type_union_type_id,
    stable_primitive_config_id,
)


def build_primitive_config(code_primitive_type: CodePrimitiveType) -> PrimitiveConfig:
    """
    Create a primitive config from a code primitive type.

    Returns:
        A PrimitiveConfig with the specified type
    """

    def _ensure_stable_code_primitive_type_ids(t: CodePrimitiveType) -> None:
        # Stabilize children first so parent signatures can reference them canonically.
        if t.item_type is not None:
            _ensure_stable_code_primitive_type_ids(t.item_type)
        if t.key_type is not None:
            _ensure_stable_code_primitive_type_ids(t.key_type)
        if t.value_type is not None:
            _ensure_stable_code_primitive_type_ids(t.value_type)

        element_edges = list(t.code_primitive_type_element_types or [])
        union_edges = list(t.code_primitive_type_union_types or [])

        for edge in element_edges:
            if edge.element_type is not None:
                _ensure_stable_code_primitive_type_ids(edge.element_type)
        for edge in union_edges:
            if edge.union_type is not None:
                _ensure_stable_code_primitive_type_ids(edge.union_type)

        # Preserve authored ordering for structural signatures.
        ordered_element_types = tuple(
            edge.element_type
            for edge in sorted(element_edges, key=lambda e: int(e.position or 0))
            if edge.element_type is not None
        )
        ordered_union_types = tuple(
            edge.union_type
            for edge in sorted(union_edges, key=lambda e: int(e.position or 0))
            if edge.union_type is not None
        )

        signature = build_code_primitive_signature(
            base_type=t.base_type,
            item_type=t.item_type,
            key_type=t.key_type,
            value_type=t.value_type,
            element_types=ordered_element_types,
            union_types=ordered_union_types,
            constraints=t.constraints,
        )
        t.signature = signature
        t.id = stable_code_primitive_type_id(signature=signature)

        if t.item_type is not None:
            t.item_type_id = t.item_type.id
        if t.key_type is not None:
            t.key_type_id = t.key_type.id
        if t.value_type is not None:
            t.value_type_id = t.value_type.id

        if element_edges:
            for edge in sorted(element_edges, key=lambda e: int(e.position or 0)):
                edge.code_primitive_type_id = t.id
                edge.element_type_id = edge.element_type.id if edge.element_type is not None else None
                edge.id = stable_code_primitive_type_element_type_id(
                    code_primitive_type_id=t.id,
                    position=int(edge.position or 0),
                )
            t.code_primitive_type_element_types = sorted(
                element_edges,
                key=lambda e: int(e.position or 0),
            )
        if union_edges:
            for edge in sorted(union_edges, key=lambda e: int(e.position or 0)):
                edge.code_primitive_type_id = t.id
                edge.union_type_id = edge.union_type.id if edge.union_type is not None else None
                edge.id = stable_code_primitive_type_union_type_id(
                    code_primitive_type_id=t.id,
                    position=int(edge.position or 0),
                )
            t.code_primitive_type_union_types = sorted(
                union_edges,
                key=lambda e: int(e.position or 0),
            )

    _ensure_stable_code_primitive_type_ids(code_primitive_type)

    prim_cfg_id = stable_primitive_config_id(primitive_type_id=code_primitive_type.id)

    return PrimitiveConfig(
        id=prim_cfg_id,
        primitive_type_id=code_primitive_type.id,
        primitive_type=code_primitive_type,
    )
