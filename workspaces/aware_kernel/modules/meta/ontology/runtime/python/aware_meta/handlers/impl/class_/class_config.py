from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.function.function_config import FunctionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta.graph.config.model_bootstrap import (
    build_class_config,
    get_class_config_fqn,
)
from aware_meta.graph.config.stable_ids import stable_class_config_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def update_config(
    class_config: ClassConfig,
    description: str | None = None,
    is_base: bool = True,
    is_edge: bool = False,
    value_mode: ClassValueMode = ClassValueMode.graph_ref,
    identity_mode: ClassIdentityMode = ClassIdentityMode.contained,
) -> None:
    """
    Update mutable ClassConfig metadata.

    Contract:
    - `class_fqn` and `name` are identity and are not mutable here.
    - Attribute, function, and relationship membership changes use their
      own ontology functions.
    """

    # --- AWARE: LOGIC START update_config
    class_config.description = description
    class_config.is_base = is_base
    class_config.is_edge = is_edge
    class_config.value_mode = value_mode
    class_config.identity_mode = identity_mode
    return None
    # --- AWARE: LOGIC END update_config


async def create_primitive_attribute_config(
    class_config: ClassConfig,
    name: str,
    primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    position: int = 0,
) -> AttributeConfig:
    """
    Materialize one AttributeConfig and bind it through ClassConfigAttributeConfig.
    """

    # --- AWARE: LOGIC START create_primitive_attribute_config
    owner_class_config_id = class_config.id
    if owner_class_config_id is None:
        raise RuntimeError("ClassConfig.create_primitive_attribute_config requires class_config.id")
    class_owner_key = get_class_config_fqn(class_config)
    if not class_owner_key:
        raise RuntimeError("ClassConfig.create_primitive_attribute_config requires class_config.class_fqn")
    if position < 0:
        raise RuntimeError("ClassConfig.create_primitive_attribute_config requires position >= 0")

    edge = await ClassConfigAttributeConfig.create_primitive_via_class_config(
        class_config_id=owner_class_config_id,
        owner_key=class_owner_key,
        name=name,
        primitive_base_type=primitive_base_type,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        position=position,
        is_identity_key=is_primary,
    )
    attribute_config = edge.attribute_config
    if attribute_config is None:
        raise RuntimeError(
            "ClassConfig.create_primitive_attribute_config expected edge.attribute_config after creation"
        )
    for existing_edge in class_config.class_config_attribute_configs:
        if existing_edge.id == edge.id:
            if existing_edge.attribute_config is None:
                existing_edge.attribute_config = attribute_config
                existing_edge.attribute_config_id = attribute_config.id
            return existing_edge.attribute_config

    class_config.class_config_attribute_configs.append(edge)
    return attribute_config
    # --- AWARE: LOGIC END create_primitive_attribute_config


async def create_enum_attribute_config(
    class_config: ClassConfig,
    name: str,
    enum_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    position: int = 0,
) -> AttributeConfig:
    """
    Materialize one enum AttributeConfig and bind it through ClassConfigAttributeConfig.
    """

    # --- AWARE: LOGIC START create_enum_attribute_config
    owner_class_config_id = class_config.id
    if owner_class_config_id is None:
        raise RuntimeError("ClassConfig.create_enum_attribute_config requires class_config.id")
    class_owner_key = get_class_config_fqn(class_config)
    if not class_owner_key:
        raise RuntimeError("ClassConfig.create_enum_attribute_config requires class_config.class_fqn")
    if position < 0:
        raise RuntimeError("ClassConfig.create_enum_attribute_config requires position >= 0")

    edge = await ClassConfigAttributeConfig.create_enum_via_class_config(
        class_config_id=owner_class_config_id,
        owner_key=class_owner_key,
        name=name,
        enum_config_id=enum_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        position=position,
        is_identity_key=is_primary,
    )
    attribute_config = edge.attribute_config
    if attribute_config is None:
        raise RuntimeError("ClassConfig.create_enum_attribute_config expected edge.attribute_config after creation")
    for existing_edge in class_config.class_config_attribute_configs:
        if existing_edge.id == edge.id:
            if existing_edge.attribute_config is None:
                existing_edge.attribute_config = attribute_config
                existing_edge.attribute_config_id = attribute_config.id
            return existing_edge.attribute_config

    class_config.class_config_attribute_configs.append(edge)
    return attribute_config
    # --- AWARE: LOGIC END create_enum_attribute_config


async def create_class_attribute_config(
    class_config: ClassConfig,
    name: str,
    type_class_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    position: int = 0,
) -> AttributeConfig:
    """
    Materialize one class AttributeConfig and bind it through ClassConfigAttributeConfig.
    """

    # --- AWARE: LOGIC START create_class_attribute_config
    owner_class_config_id = class_config.id
    if owner_class_config_id is None:
        raise RuntimeError("ClassConfig.create_class_attribute_config requires class_config.id")
    class_owner_key = get_class_config_fqn(class_config)
    if not class_owner_key:
        raise RuntimeError("ClassConfig.create_class_attribute_config requires class_config.class_fqn")
    if position < 0:
        raise RuntimeError("ClassConfig.create_class_attribute_config requires position >= 0")

    edge = await ClassConfigAttributeConfig.create_class_via_class_config(
        class_config_id=owner_class_config_id,
        owner_key=class_owner_key,
        name=name,
        type_class_config_id=type_class_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        position=position,
        is_identity_key=is_primary,
    )
    attribute_config = edge.attribute_config
    if attribute_config is None:
        raise RuntimeError("ClassConfig.create_class_attribute_config expected edge.attribute_config after creation")
    for existing_edge in class_config.class_config_attribute_configs:
        if existing_edge.id == edge.id:
            if existing_edge.attribute_config is None:
                existing_edge.attribute_config = attribute_config
                existing_edge.attribute_config_id = attribute_config.id
            return existing_edge.attribute_config

    class_config.class_config_attribute_configs.append(edge)
    return attribute_config
    # --- AWARE: LOGIC END create_class_attribute_config


async def remove_attribute_config(
    class_config: ClassConfig, name: str, attribute_config_id: UUID | None = None
) -> None:
    """
    Remove one AttributeConfig membership from this ClassConfig.

    Contract:
    - Mutates only class_config_attribute_configs on this ClassConfig.
    - Attribute identity comes from committed semantic baseline truth when available.
    - Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.
    """

    # --- AWARE: LOGIC START remove_attribute_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ClassConfig.remove_attribute_config requires non-empty name")

    normalized_attribute_config_id = UUID(str(attribute_config_id)) if attribute_config_id is not None else None

    retained_edges: list[ClassConfigAttributeConfig] = []
    removed = False
    for edge in class_config.class_config_attribute_configs:
        edge_attribute_config_id = edge.attribute_config_id
        if edge_attribute_config_id is None:
            edge_attribute_config_id = edge.attribute_config.id
        edge_matches_id = (
            normalized_attribute_config_id is not None and edge_attribute_config_id == normalized_attribute_config_id
        )
        edge_matches_name = False
        if normalized_attribute_config_id is None:
            edge_matches_name = (edge.attribute_config.name or "").strip() == normalized_name
        if edge_matches_id or edge_matches_name:
            removed = True
            continue
        retained_edges.append(edge)

    if removed:
        class_config.class_config_attribute_configs[:] = retained_edges
    return None
    # --- AWARE: LOGIC END remove_attribute_config


async def create_function_config(
    class_config: ClassConfig,
    name: str,
    description: str | None = None,
    verb: str | None = None,
    is_async: bool = False,
    kind: FunctionKind = FunctionKind.instance,
    is_public: bool = True,
    is_constructor: bool = False,
    position: int = 0,
) -> FunctionConfig:
    """
    Materialize one FunctionConfig and bind it through ClassConfigFunctionConfig.
    """

    # --- AWARE: LOGIC START create_function_config
    owner_class_config_id = class_config.id
    if owner_class_config_id is None:
        raise RuntimeError("ClassConfig.create_function_config requires class_config.id")
    class_owner_key = get_class_config_fqn(class_config)
    if not class_owner_key:
        raise RuntimeError("ClassConfig.create_function_config requires class_config.class_fqn")
    if position < 0:
        raise RuntimeError("ClassConfig.create_function_config requires position >= 0")

    edge = await ClassConfigFunctionConfig.create_via_class_config(
        class_config_id=owner_class_config_id,
        owner_key=class_owner_key,
        name=name,
        description=description,
        verb=verb,
        is_async=is_async,
        kind=kind,
        is_public=is_public,
        is_constructor=is_constructor,
        position=position,
    )
    function_config = edge.function_config
    if function_config is None:
        raise RuntimeError("ClassConfig.create_function_config expected edge.function_config after creation")
    for existing_edge in class_config.class_config_function_configs:
        if existing_edge.id == edge.id:
            if existing_edge.function_config is None:
                existing_edge.function_config = function_config
                existing_edge.function_config_id = function_config.id
            return existing_edge.function_config

    class_config.class_config_function_configs.append(edge)
    return function_config
    # --- AWARE: LOGIC END create_function_config


async def remove_function_config(
    class_config: ClassConfig, name: str, function_config_id: UUID | None = None
) -> None:
    """
    Remove one FunctionConfig membership from this ClassConfig.

    Contract:
    - Mutates only class_config_function_configs on this ClassConfig.
    - Function identity comes from committed semantic baseline truth when available.
    - Rooted OIG commit reachability owns stale FunctionConfig deletion after membership removal.
    """

    # --- AWARE: LOGIC START remove_function_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ClassConfig.remove_function_config requires non-empty name")

    normalized_function_config_id = (
        UUID(str(function_config_id)) if function_config_id is not None else None
    )

    retained_edges: list[ClassConfigFunctionConfig] = []
    removed = False
    for edge in class_config.class_config_function_configs:
        edge_function_config_id = edge.function_config_id
        if edge_function_config_id is None and edge.function_config is not None:
            edge_function_config_id = edge.function_config.id
        edge_matches_id = (
            normalized_function_config_id is not None
            and edge_function_config_id == normalized_function_config_id
        )
        edge_matches_name = False
        if normalized_function_config_id is None:
            function_config = edge.function_config
            if function_config is None and edge_function_config_id is not None:
                function_config = current_handler_session().imap_get(
                    FunctionConfig,
                    edge_function_config_id,
                )
            edge_matches_name = (
                function_config is not None
                and (function_config.name or "").strip() == normalized_name
            )
        if edge_matches_id or edge_matches_name:
            removed = True
            continue
        retained_edges.append(edge)

    if removed:
        class_config.class_config_function_configs[:] = retained_edges
    return None
    # --- AWARE: LOGIC END remove_function_config


async def create_relationship(
    class_config: ClassConfig,
    target_class_config_id: UUID,
    relationship_key: str,
    relationship_type: ClassConfigRelationshipType,
    identity_rail: ClassConfigRelationshipIdentityRail | None = None,
    forward_required: bool = False,
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reified_from_relationship_id: UUID | None = None,
    reified_role: ClassConfigRelationshipReifiedRole | None = None,
) -> ClassConfigRelationship:
    """
    Materialize one deterministic relationship owned by this ClassConfig.

    Contract:
    - Parent `ClassConfig` scope is propagated by traversal lowering.
    - Stable identity derives from parent scope + `(target_class_config_id, relationship_key)`.
    - Association class metadata is optional, materialized on the child rail, and is not part of stable
    identity.
    """

    # --- AWARE: LOGIC START create_relationship
    owner_class_config_id = class_config.id
    if owner_class_config_id is None:
        raise RuntimeError("ClassConfig.create_relationship requires class_config.id")
    normalized_relationship_key = (relationship_key or "").strip()
    if not normalized_relationship_key:
        raise RuntimeError("ClassConfig.create_relationship requires non-empty relationship_key")

    relationship = await ClassConfigRelationship.create_via_class_config(
        class_config_id=owner_class_config_id,
        target_class_config_id=target_class_config_id,
        relationship_key=normalized_relationship_key,
        relationship_type=relationship_type,
        identity_rail=identity_rail,
        forward_required=forward_required,
        forward_loading_strategy=forward_loading_strategy,
        reverse_loading_strategy=reverse_loading_strategy,
        reified_from_relationship_id=reified_from_relationship_id,
        reified_role=reified_role,
    )
    for existing_relationship in class_config.class_config_relationships:
        if existing_relationship.id == relationship.id:
            return existing_relationship

    class_config.class_config_relationships.append(relationship)
    return relationship
    # --- AWARE: LOGIC END create_relationship


async def remove_relationship_config(
    class_config: ClassConfig, relationship_key: str, relationship_config_id: UUID | None = None
) -> None:
    """
    Remove one ClassConfigRelationship membership from this ClassConfig.

    Contract:
    - Mutates only class_config_relationships on this ClassConfig.
    - Relationship identity comes from committed semantic baseline truth when available.
    - Rooted OIG commit reachability owns stale relationship object deletion after membership removal.
    """

    # --- AWARE: LOGIC START remove_relationship_config
    normalized_relationship_key = (relationship_key or "").strip()
    if not normalized_relationship_key:
        raise RuntimeError("ClassConfig.remove_relationship_config requires non-empty relationship_key")
    normalized_relationship_config_id = (
        UUID(str(relationship_config_id)) if relationship_config_id is not None else None
    )

    retained_relationships: list[ClassConfigRelationship] = []
    removed = False
    for relationship in class_config.class_config_relationships:
        relationship_matches_id = (
            normalized_relationship_config_id is not None and relationship.id == normalized_relationship_config_id
        )
        relationship_matches_key = False
        if normalized_relationship_config_id is None:
            relationship_matches_key = (relationship.relationship_key or "").strip() == normalized_relationship_key
        if relationship_matches_id or relationship_matches_key:
            removed = True
            continue
        retained_relationships.append(relationship)

    if removed:
        class_config.class_config_relationships[:] = retained_relationships
    return None
    # --- AWARE: LOGIC END remove_relationship_config


async def create_via_object_config_graph_node(
    object_config_graph_node_id: UUID,
    class_fqn: str,
    name: str,
    is_base: bool = True,
    is_edge: bool = False,
    description: str | None = None,
    value_mode: ClassValueMode = ClassValueMode.graph_ref,
) -> ClassConfig:
    """
    Create deterministic ClassConfig under an ObjectConfigGraphNode.
    """

    # --- AWARE: LOGIC START create_via_object_config_graph_node
    normalized_name = (name or "").strip()
    normalized_class_fqn = (class_fqn or "").strip()
    if not normalized_name:
        raise RuntimeError("ClassConfig.create_via_object_config_graph_node requires non-empty name")
    if not normalized_class_fqn:
        raise RuntimeError("ClassConfig.create_via_object_config_graph_node requires non-empty class_fqn")
    class_config_id = stable_class_config_id(
        object_config_graph_node_id=object_config_graph_node_id,
        class_fqn=normalized_class_fqn,
    )

    session = current_handler_session()
    existing = session.imap_get(ClassConfig, class_config_id)
    if existing is not None:
        if (
            (get_class_config_fqn(existing) or normalized_class_fqn) != normalized_class_fqn
            or (existing.name or "").strip() != normalized_name
            or existing.is_base != is_base
            or existing.is_edge != is_edge
            or (existing.description or None) != (description or None)
            or existing.value_mode != value_mode
        ):
            raise RuntimeError(
                "ClassConfig.create_via_object_config_graph_node payload mismatch for existing ClassConfig: "
                f"class_config_id={class_config_id}"
            )
        return existing

    return build_class_config(
        class_config_id=class_config_id,
        object_config_graph_node_id=object_config_graph_node_id,
        class_fqn=normalized_class_fqn,
        name=normalized_name,
        is_base=is_base,
        is_edge=is_edge,
        description=description,
        value_mode=value_mode,
    )
    # --- AWARE: LOGIC END create_via_object_config_graph_node
