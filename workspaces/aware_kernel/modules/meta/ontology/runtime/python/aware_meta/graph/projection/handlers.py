"""
Builder for constructing a canonical ObjectInstanceGraph from OCG + OPG + runtime instances.

SSOT: OPG membership + traversal rules. There is no separate policy registry for canonical OIG build.
"""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_meta.attribute.instance.value.builder import (
    EnumOptionResolver,
    UnionSelection,
)
from aware_meta.graph.instance.builder import (
    RelationshipResolver,
    build_object_instance_graph as build_object_instance_graph_canonical,
)

# ORM / introspection
from aware_orm.models.introspection import ModelIntrospection


async def build_object_instance_graph(
    root: ModelIntrospection,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    name: str,
    description: str,
    *,
    oig_id: UUID | None = None,
    instance_registry: Iterable[ModelIntrospection] | None = None,
    relationship_resolver: RelationshipResolver | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
) -> ObjectInstanceGraph:
    return build_object_instance_graph_canonical(
        root_instance=root,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name=name or f"OIG_{root.__class__.__name__}_{root.id}",
        description=description or f"Graph built via OPG {opg.id}",
        oig_id=oig_id,
        instance_registry=instance_registry,
        relationship_resolver=relationship_resolver,
        enum_option_resolver=enum_option_resolver,
        union_selections=union_selections,
    )
