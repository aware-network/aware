"""Builder for ClassConfigRelationship instances."""

from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_association import (
    ClassConfigRelationshipAssociation,
)

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

# FQN resolution (language-agnostic)
from aware_meta.fqn_resolver import FqnResolver
from aware_meta.graph.config.stable_ids import (
    stable_class_relationship_id,
    stable_class_relationship_attribute_id,
    stable_class_relationship_association_edge_id,
)


def _descriptor_contains_class(descriptor: AttributeTypeDescriptor) -> bool:
    """Return True if the descriptor tree contains any CLASS leaf."""
    stack: list[AttributeTypeDescriptor] = [descriptor]
    while stack:
        cur = stack.pop()
        if cur.kind == AttributeTypeDescriptorKind.class_:
            return True
        # Preserve deterministic traversal (child_links order)
        for lnk in reversed(cur.child_links):
            if lnk.child is not None:
                stack.append(lnk.child)
    return False


def build_class_config_relationships(
    class_configs: list[ClassConfig],
    fqn_resolver: FqnResolver,
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> tuple[list[ClassConfigRelationship], dict[UUID, list[ClassConfigRelationship]]]:
    """
    Build ClassConfigRelationships from already-built ClassConfigs + SSOT CodeSection fields.

    Canonical constraint: no adapters, no CodeNode, no raw-text peeks. We only use:
    - AttributeConfig.type_descriptor (already resolved via FqnScope)
    - CodeSectionAttribute.edge_spec_name / is_many_to_many
    """
    class_relationships: list[ClassConfigRelationship] = []
    cross_map: dict[UUID, list[ClassConfigRelationship]] = {}

    local_class_ids = {c.id for c in class_configs}

    value_mode_by_class_id: dict[UUID, ClassValueMode] = {c.id: c.value_mode for c in class_configs}

    external_class_id_to_graph_id: dict[UUID, UUID] = {}
    if external_graphs:
        for g in external_graphs:
            for node in g.object_config_graph_nodes:
                if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                    external_class_id_to_graph_id[node.class_config.id] = g.id
                    value_mode_by_class_id.setdefault(node.class_config.id, node.class_config.value_mode)

    # ---------------------------------------------------------------------
    # Pre-scan: collect association (edge container) class IDs referenced by relationships.
    #
    # Canonical rule: association classes are relationship containers and should not emit
    # their own relationships from attributes. We therefore skip relationship extraction
    # for any class referenced as an association via `edge_spec_name`.
    # ---------------------------------------------------------------------
    association_class_ids: set[UUID] = set()
    for class_config in class_configs:
        code_section_class = class_config.code_section_class
        if code_section_class is None:
            continue
        scope = fqn_resolver.scope_for_code_id(code_section_class.code_section.code_id)
        for class_config_attribute_config in class_config.class_config_attribute_configs:
            attribute_config = class_config_attribute_config.attribute_config
            code_attr = attribute_config.code_section_attribute
            if code_attr is None:
                continue
            if not code_attr.edge_spec_name:
                continue
            assoc_class = scope.try_resolve_class(code_attr.edge_spec_name)
            if assoc_class is None:
                raise ValueError(f"Association class not found for edge spec name={code_attr.edge_spec_name}")
            association_class_ids.add(assoc_class.id)

    for class_config in class_configs:
        # Inline-value classes are pure value types: CLASS-typed attributes are value composition,
        # not graph relationships.
        if class_config.value_mode != ClassValueMode.graph_ref:
            continue

        if class_config.id in association_class_ids:
            # -----------------------------------------------------------------
            # Hard invariant: association (edge container) classes must never
            # declare relationships (CLASS-typed attributes) in canonical SSOT.
            # -----------------------------------------------------------------
            for link in class_config.class_config_attribute_configs:
                attr = link.attribute_config
                if attr is None:
                    continue
                if _descriptor_contains_class(attr.type_descriptor):
                    raise ValueError(
                        "Invalid canonical Aware: association (edge container) classes must not declare relationships. "
                        f"Found relationship-like attribute on association {class_config.name}.{attr.name}. "
                        "Declare the relationship on the source class (with @EdgeSpec) and use annotations "
                        "to control association endpoints."
                    )
            # Association/edge container classes do not emit relationships.
            continue
        code_section_class = class_config.code_section_class
        if code_section_class is None:
            raise ValueError(f"ClassConfig {class_config.id} missing code_section_class")

        source_code_id = code_section_class.code_section.code_id
        fqn_scope = fqn_resolver.scope_for_code_id(source_code_id)

        for class_config_attribute_config in class_config.class_config_attribute_configs:
            attribute_config = class_config_attribute_config.attribute_config
            code_attr = attribute_config.code_section_attribute
            if code_attr is None:
                raise ValueError(f"AttributeConfig {attribute_config.id} missing code_section_attribute")

            target_class_ids = _walk_descriptor_for_class(attribute_config.type_descriptor)
            if not target_class_ids:
                continue

            target_modes: list[ClassValueMode] = []
            for target_id in target_class_ids:
                mode = value_mode_by_class_id.get(target_id)
                if mode is None:
                    raise ValueError(
                        f"Target class missing value_mode for relationship resolution: class_id={target_id}"
                    )
                target_modes.append(mode)

            if any(m == ClassValueMode.inline_value for m in target_modes):
                # Value composition: inline_value targets are not relationship endpoints.
                if any(m == ClassValueMode.graph_ref for m in target_modes):
                    raise ValueError(
                        "AttributeTypeDescriptor mixes inline_value and graph_ref class targets; not supported. "
                        f"source_class_id={class_config.id} attribute={attribute_config.name} targets={target_class_ids}"
                    )
                continue

            if len(target_class_ids) != 1:
                raise ValueError(
                    "Relationship attributes must resolve to exactly one graph_ref target class. "
                    f"source_class_id={class_config.id} attribute={attribute_config.name} targets={target_class_ids}"
                )
            if len(target_class_ids) != 1:
                raise ValueError(
                    f"Relationship attribute must resolve to exactly one class. "
                    f"Got {len(target_class_ids)} targets for {class_config.name}.{attribute_config.name}: {target_class_ids}"
                )

            # Relationship type (declared by the source attribute)
            if code_attr.is_many_to_many:
                rel_type = ClassConfigRelationshipType.many_to_many
            elif attribute_config.type_descriptor.kind == AttributeTypeDescriptorKind.collection:
                rel_type = ClassConfigRelationshipType.one_to_many
            elif attribute_config.is_unique:
                rel_type = ClassConfigRelationshipType.one_to_one
            else:
                rel_type = ClassConfigRelationshipType.many_to_one

            target_class_id = target_class_ids[0]
            target_graph_id: UUID | None = None
            if target_class_id not in local_class_ids:
                target_graph_id = external_class_id_to_graph_id.get(target_class_id)
                if target_graph_id is None:
                    raise ValueError(f"Target class not found for class_id={target_class_id}")

            # Create the relationship
            relationship_key = attribute_config.name
            rel_id = stable_class_relationship_id(
                source_class_id=class_config.id,
                target_class_id=target_class_id,
                relationship_key=relationship_key,
            )
            rel = ClassConfigRelationship(
                id=rel_id,
                relationship_key=relationship_key,
                relationship_type=rel_type,
                forward_required=bool(attribute_config.is_required),
                # Canonical default: forward relationships are LAZY unless overridden by LOAD annotations.
                forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
                reverse_loading_strategy=None,
                class_config_id=class_config.id,
                target_class_config_id=target_class_id,
            )

            # Create the association if edge spec name is present
            if code_attr.edge_spec_name:
                # Resolve association class by edge spec symbol (class name)
                assoc_class = fqn_scope.try_resolve_class(code_attr.edge_spec_name)
                if assoc_class is None:
                    raise ValueError(f"Association class not found for edge spec name={code_attr.edge_spec_name}")
                assoc = ClassConfigRelationshipAssociation(
                    id=stable_class_relationship_association_edge_id(
                        relationship_id=rel.id,
                        association_class_id=assoc_class.id,
                    ),
                    class_config_id=assoc_class.id,
                    class_config_relationship_id=rel.id,
                    forward_loading_strategy=None,
                    reverse_loading_strategy=None,
                )
                rel.class_config_relationship_association_edge = assoc

            # Canonical relationship representation: one attribute on the forward side.
            rel_attr = ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=rel.id,
                    attribute_config_id=attribute_config.id,
                    direction=ClassConfigRelationshipDirection.forward.value,
                    role=ClassConfigRelationshipAttributeRole.reference.value,
                ),
                class_config_relationship_id=rel.id,
                attribute_config_id=attribute_config.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            )
            rel.class_config_relationship_attributes.append(rel_attr)

            if target_graph_id is not None:
                # Canonical invariant:
                # - Cross-OCG relationships are returned detached (NOT embedded as relationship nodes
                #   in the local ObjectConfigGraph). This keeps the local graph self-contained.
                # - They are still first-class SSOT relationships for downstream stages, via the
                #   returned `cross_map` keyed by target graph id.
                cross_map.setdefault(target_graph_id, []).append(rel)
                continue

            # Local relationship: include it so it becomes an OCG relationship node.
            class_relationships.append(rel)

    return class_relationships, cross_map


def _walk_descriptor_for_class(descriptor: AttributeTypeDescriptor) -> list[UUID]:
    """
    Return all class_config_ids reachable within a descriptor tree.
    """
    found: list[UUID] = []
    stack: list[AttributeTypeDescriptor] = [descriptor]
    while stack:
        cur = stack.pop()
        if cur.kind == AttributeTypeDescriptorKind.class_:
            if cur.class_config_id is None:
                raise ValueError("Unresolved CLASS descriptor: class_config_id is None")
            found.append(cur.class_config_id)
        # Preserve deterministic traversal order (child_links order)
        children = [lnk.child for lnk in cur.child_links]
        for ch in reversed(children):
            stack.append(ch)
    # Deterministic output (and avoid duplicates from UNION, etc.)
    return sorted(set(found), key=lambda u: str(u))
