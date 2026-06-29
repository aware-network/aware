from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

# Kernel Graph Ontology
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

# Meta Runtime
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind
from aware_meta.graph.instance.member import ObjectInstanceGraphMember
from aware_meta.class_.instance.member import ClassInstanceMember
from aware_meta.class_.instance.relationship.member import (
    ClassInstanceRelationshipMember,
)
from aware_meta.attribute.instance.member import AttributeMember
from aware_meta.attribute.instance.value.member import (
    AttributeValueLinkMember,
    AttributeValueMember,
)
from aware_meta.primitive.instance.member import PrimitiveMember
from aware_meta.enum.instance.member import EnumMember

# Meta graph support
from aware_meta.graph.support.member import GraphMember
from aware_meta.graph.support.topology import GraphTopology


class ObjectInstanceGraphTopology(GraphTopology[ObjectInstanceGraphMemberKind]):
    """
    Topology for ObjectInstanceGraph over GraphMember wrappers.

    This implementation constructs child members on demand directly from the
    canonical kernel ontology models; members themselves remain pure views
    (identity + path + content) without traversal logic.
    """

    def get_children(
        self,
        parent: GraphMember[ObjectInstanceGraphMemberKind],
    ) -> Mapping[
        ObjectInstanceGraphMemberKind,
        Iterable[GraphMember[ObjectInstanceGraphMemberKind]],
    ]:
        children: dict[
            ObjectInstanceGraphMemberKind,
            list[GraphMember[ObjectInstanceGraphMemberKind]],
        ] = defaultdict(list)
        # Root: ObjectInstanceGraphMember → ObjectInstanceMember children
        if isinstance(parent, ObjectInstanceGraphMember):
            graph: ObjectInstanceGraph = parent.object_instance_graph

            # All stored instances – including the root. Callers are expected
            # to ensure the root instance is present in `object_instances`;
            # we avoid adding it twice here to keep topology and diffs stable.
            for inst in graph.class_instances:
                children[ObjectInstanceGraphMemberKind.class_instance].append(ClassInstanceMember(class_instance=inst))

            # Relationships: attach one member per relationship (global view)
            for rel in graph.class_instance_relationships:
                children[ObjectInstanceGraphMemberKind.relationship_instance].append(
                    ClassInstanceRelationshipMember(class_instance_relationship=rel)
                )

            return children

        # ClassInstanceMember → AttributeMember children
        if isinstance(parent, ClassInstanceMember):
            cls_inst = parent.class_instance
            for attr in cls_inst.attributes:
                children[ObjectInstanceGraphMemberKind.attribute].append(AttributeMember(attribute=attr))
            return children

        # AttributeMember → PrimitiveMember / EnumMember children
        if isinstance(parent, AttributeMember):
            attr = parent.attribute
            # Canonical: descriptor-driven value tree.
            if attr.value_root is not None:
                children[ObjectInstanceGraphMemberKind.attribute_value].append(
                    AttributeValueMember(attribute_value=attr.value_root)
                )
                return children

            # Legacy fallback: primitive/enum fields (deprecated).
            prim = attr.primitive
            if prim is not None:
                children[ObjectInstanceGraphMemberKind.primitive].append(PrimitiveMember(primitive=prim))
            enum_val = attr.enum
            if enum_val is not None:
                children[ObjectInstanceGraphMemberKind.enum].append(EnumMember(enum=enum_val))
            return children

        # AttributeValueMember → AttributeValueLinkMember children
        if isinstance(parent, AttributeValueMember):
            node = parent.attribute_value
            links = node.child_links
            links.sort(
                key=lambda l: (
                    l.role.value,
                    l.position if l.position is not None else -1,
                    l.identity_key or "",
                )
            )
            for link in links:
                children[ObjectInstanceGraphMemberKind.attribute_value_link].append(
                    AttributeValueLinkMember(attribute_value_link=link)
                )
            return children

        # AttributeValueLinkMember → AttributeValueMember child
        if isinstance(parent, AttributeValueLinkMember):
            link = parent.attribute_value_link
            if link.child is None:
                raise ValueError(f"AttributeValueLink {link.id} missing child (cannot traverse value tree)")
            children[ObjectInstanceGraphMemberKind.attribute_value].append(
                AttributeValueMember(attribute_value=link.child)
            )
            return children

        # Primitive / Enum members are leaves
        if isinstance(parent, (PrimitiveMember, EnumMember)):
            return {}

        # Fallback: no children for unknown member types
        return {}


__all__ = ["ObjectInstanceGraphTopology"]
