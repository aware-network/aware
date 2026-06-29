"""Index for storing and retrieving meta entities during graph building and diffing."""

# Standard Imports
from uuid import UUID

# Aware Kernel Graph Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship

# Meta graph support
from aware_meta.graph.support.index.index import GraphIndex
from aware_meta.graph.support.member import GraphMember

# Aware Meta
from aware_meta.graph.config.member_kind import ObjectConfigGraphMemberKind


class ObjectConfigGraphIndex(GraphIndex[ObjectConfigGraphMemberKind]):
    """OCG-specific index that skips link nodes in path segments.

    Link nodes remain GraphMembers for diff/apply, but they should not contribute to the
    human/semantic path. We therefore avoid adding them to the path while still walking
    their children.
    """

    def __init__(self, root: ObjectConfigGraph):
        super().__init__()
        self.rel_by_pair_ids: dict[tuple[UUID, UUID], list[ClassConfigRelationship]] = {}
        self.class_config_id_to_object_config_id: dict[UUID, UUID] = {}
        self._build_fast_maps(root)

    def _build_fast_maps(self, ocg: ObjectConfigGraph) -> None:
        ocg_relationships: list[ClassConfigRelationship] = []
        for node in ocg.object_config_graph_nodes:
            if node.class_config:
                # No object configs in canonical class-first graph nodes
                pass
            if node.class_config_relationship:
                ocg_relationships.append(node.class_config_relationship)

        # (a) relationships by (src_id, tgt_id) and reverse
        for rel in ocg_relationships:
            key = (rel.class_config_id, rel.target_class_config_id)
            self.rel_by_pair_ids.setdefault(key, []).append(rel)
            self.rel_by_pair_ids.setdefault((key[1], key[0]), []).append(rel)

        # No ObjectConfig mapping in canonical mode: identity is the base ClassConfig.

        # No side mappings in canonical mode: relationships are single-sided SSOT.

    def _make_path(
        self,
        node: GraphMember[ObjectConfigGraphMemberKind],
        parent_path: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Build semantic path; keep root segment compatible with tests."""
        kind = node.node_kind()
        # Root uses "{name}-{language}" for compatibility
        if kind == ObjectConfigGraphMemberKind.ROOT:
            name = getattr(node, "name", "unknown")
            language = getattr(getattr(node, "language", None), "value", None) or str(
                getattr(node, "language", "unknown")
            )
            segment = f"{name}-{language}"
        else:
            segment = getattr(node, "path_key", None)
            segment = str(segment) if isinstance(segment, str) and segment else "unknown"
        return parent_path + (segment,)

    def _walk(
        self,
        node: GraphMember[ObjectConfigGraphMemberKind],
        parent_path: tuple[str, ...],
    ) -> None:
        kind = node.node_kind()
        is_link = kind in (
            ObjectConfigGraphMemberKind.OBJECT_CLASS_LINK,
            ObjectConfigGraphMemberKind.CLASS_ATTRIBUTE_LINK,
            ObjectConfigGraphMemberKind.CLASS_FUNCTION_LINK,
            ObjectConfigGraphMemberKind.ATTRIBUTE_PRIMITIVE_LINK,
            ObjectConfigGraphMemberKind.ATTRIBUTE_ENUM_LINK,
            ObjectConfigGraphMemberKind.ATTRIBUTE_CLASS_LINK,
        )

        # Decide local path: skip link kinds by not adding a segment
        if is_link:
            path = parent_path
        else:
            path = self._make_path(node, parent_path)
            self.add(node, path, kind)

        # Always walk children
        # NOTE: GraphMember protocol differs across packages; use getattr to keep typing strict.
        children_map = getattr(node, "get_children")()
        for child_kind, children in children_map.items():
            for child in children:
                self._walk(child, path)

    def remove_entity(self, entity_id: UUID) -> None:
        """Remove a cached entity by its ID (used for incremental updates)."""
        entity = self._by_id.pop(entity_id, None)
        if entity is None:
            return
        paths_to_remove = [path for path, (entry, _) in self._by_path.items() if entry is entity]
        for path in paths_to_remove:
            self._by_path.pop(path, None)

    def add_entity(
        self,
        path: tuple[str, ...],
        entity: GraphMember[ObjectConfigGraphMemberKind],
        kind: ObjectConfigGraphMemberKind,
    ) -> None:
        """Add an entity to the index."""
        self.add(entity, path, kind)

    def index_by_schema_class_attribute(
        self,
        entity: GraphMember[ObjectConfigGraphMemberKind],
        schema: str,
        class_name: str,
        attribute: str | None,
    ) -> None:
        """Index an entity by its schema, object, and attribute."""
        path = (schema, class_name)
        if attribute is None:
            member_kind = ObjectConfigGraphMemberKind.OBJECT_CLASS_LINK
        else:
            member_kind = ObjectConfigGraphMemberKind.ATTRIBUTE
            path += (attribute,)

        self.add(entity, path, member_kind)

    def get_object_config_id_by_class_config_id(self, class_config_id: UUID) -> UUID | None:
        """Deprecated in canonical mode (class-first graphs)."""
        _ = class_config_id
        return None
