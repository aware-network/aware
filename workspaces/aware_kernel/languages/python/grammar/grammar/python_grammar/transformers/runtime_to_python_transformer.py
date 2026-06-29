"""Runtime IR -> Python lowering transformer.

Python ORM facades are the SSOT runtime surface, but required cross-projection portal
object refs cannot always be hydrated during the write that creates them. The runtime
already preserves canonical `*_id` truth for these rails; this transformer lowers the
Python object field shape to match that runtime contract without weakening ontology
requiredness or hiding policy in the renderer.
"""

from __future__ import annotations

from uuid import UUID

from typing_extensions import override

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.graph.config.transformer import (
    ObjectConfigGraphTransformer,
    ObjectConfigGraphTransformerPolicy,
)
from aware_meta.graph.projection.portal_index import (
    ObjectProjectionGraphPortalClosureContext,
    build_portal_index,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_utils.logging import logger


class RuntimeToPythonTransformer(ObjectConfigGraphTransformer):
    """Lower runtime IR into Python-ready facade semantics."""

    def __init__(
        self,
        *,
        namespace_by_code_id: dict[UUID, object] | None = None,
        external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
        portal_closure_context: ObjectProjectionGraphPortalClosureContext | None = None,
    ) -> None:
        _ = namespace_by_code_id
        self._external_graphs_by_id: dict[UUID, ObjectConfigGraph] = external_graphs_by_id or {}
        self._portal_closure_context = portal_closure_context

    @override
    def set_policy(self, policy: ObjectConfigGraphTransformerPolicy | None) -> None:
        _ = policy

    @override
    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type

        if not object_config_graph.object_projection_graphs:
            return object_config_graph

        portal_index = build_portal_index(
            object_config_graph,
            external_graphs=list(self._external_graphs_by_id.values()),
            closure_context=self._portal_closure_context,
        )
        if not portal_index.portals:
            return object_config_graph

        attr_by_id: dict[UUID, AttributeConfig] = {}
        relationship_by_id: dict[UUID, ClassConfigRelationship] = {}
        for node in object_config_graph.object_config_graph_nodes:
            if node.class_config is not None:
                for link in node.class_config.class_config_attribute_configs:
                    attr_by_id[link.attribute_config.id] = link.attribute_config
            if node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
                relationship_by_id[node.class_config_relationship.id] = node.class_config_relationship
        for rel_group in object_config_graph.object_config_graph_relationships:
            for rel in rel_group.class_config_relationships:
                relationship_by_id[rel.id] = rel

        lowered_refs = 0
        strengthened_fks = 0

        for portal in portal_index.portals:
            attr = attr_by_id.get(portal.reference_attribute_config_id)
            if attr is None:
                continue
            desc = attr.type_descriptor
            if desc.kind == AttributeTypeDescriptorKind.class_ and attr.is_required:
                # Cross-projection portal refs remain required in ontology/runtime via their FK,
                # but Python object hydration must be allowed to arrive later.
                attr.is_required = False
                lowered_refs += 1

            rel = relationship_by_id.get(portal.class_config_relationship_id)
            fk_attr_id = portal_index.foreign_key_attribute_config_id_by_relationship_id.get(portal.class_config_relationship_id)
            fk_attr = attr_by_id.get(fk_attr_id) if fk_attr_id is not None else None
            if rel is None or fk_attr is None:
                continue
            if bool(getattr(rel, "forward_required", False)):
                fk_attr.is_required = True
                fk_attr.default_value = None
                strengthened_fks += 1

        if lowered_refs or strengthened_fks:
            logger.debug(
                "RuntimeToPythonTransformer lowered %s portal ref(s) and strengthened %s portal FK(s)",
                lowered_refs,
                strengthened_fks,
            )

        return object_config_graph


__all__ = ["RuntimeToPythonTransformer"]
