"""Meta-owned ObjectConfigGraph -> ORM graph binding translator."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from aware_meta.attribute.config.type_descriptor_helpers import (
    resolve_type_class_config_id,
    resolve_type_info,
)
from aware_orm.runtime.graph_artifacts import (
    OrmEntitySpec,
    OrmFieldBinding,
    OrmFieldSpec,
    OrmFieldValueTypeSpec,
    OrmFunctionBinding,
    OrmFunctionSpec,
    OrmGraphBindingSnapshot,
    OrmProducerRef,
    OrmRelationshipField,
    OrmRelationshipSpec,
)
from aware_orm.runtime.graph_binding import dump_orm_graph_binding_snapshot_msgpack


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _producer_ref(
    *, kind: str, obj: Any, node_id: UUID | None = None
) -> OrmProducerRef:
    obj_id = getattr(obj, "id", None)
    return OrmProducerRef(
        producer="aware-meta",
        kind=kind,
        id=str(obj_id) if obj_id is not None else None,
        node_id=str(node_id) if node_id is not None else None,
    )


def _field_value_type(attr: Any | None) -> OrmFieldValueTypeSpec | None:
    if attr is None or getattr(attr, "type_descriptor", None) is None:
        return None
    info = resolve_type_info(attr)
    return OrmFieldValueTypeSpec(
        kind=_value(getattr(info, "kind", None)),
        entity_id=resolve_type_class_config_id(attr),
        primitive_id=getattr(getattr(info, "primitive_config", None), "id", None),
        enum_id=getattr(getattr(info, "enum_config", None), "id", None),
        collection_kind=_value(getattr(info, "collection_kind", None)),
        is_collection=bool(getattr(info, "is_collection", False)),
    )


def _field_spec(attr: Any | None) -> OrmFieldSpec | None:
    if attr is None:
        return None
    return OrmFieldSpec(
        id=getattr(attr, "id", None),
        name=getattr(attr, "name", None),
        owner_key=getattr(attr, "owner_key", None),
        description=getattr(attr, "description", None),
        default_value=getattr(attr, "default_value", None),
        is_primary=getattr(attr, "is_primary", None),
        is_public=getattr(attr, "is_public", None),
        is_required=getattr(attr, "is_required", None),
        is_unique=getattr(attr, "is_unique", None),
        is_virtual=getattr(attr, "is_virtual", None),
        value_type=_field_value_type(attr),
        producer_ref=_producer_ref(kind="field", obj=attr),
    )


def _field_binding(link: Any) -> OrmFieldBinding:
    attr = getattr(link, "attribute_config", None)
    binding_role = _value(getattr(link, "type", None))
    return OrmFieldBinding(
        id=getattr(link, "id", None),
        entity_id=getattr(link, "class_config_id", None),
        function_id=getattr(link, "function_config_id", None),
        field_id=getattr(link, "attribute_config_id", None),
        position=getattr(link, "position", None),
        binding_role=binding_role,
        is_identity_key=_field_binding_identity_key(
            link=link,
            attr=attr,
            binding_role=binding_role,
        ),
        field=_field_spec(attr),
    )


def _field_binding_identity_key(
    *,
    link: Any,
    attr: Any | None,
    binding_role: Any,
) -> bool:
    return bool(getattr(link, "is_identity_key", False))


def _function_spec(function: Any | None) -> OrmFunctionSpec | None:
    if function is None:
        return None
    links = [
        _field_binding(link)
        for link in (getattr(function, "function_config_attribute_configs", None) or [])
        if link is not None
    ]
    return OrmFunctionSpec(
        id=getattr(function, "id", None),
        owner_key=getattr(function, "owner_key", None),
        name=getattr(function, "name", None),
        description=getattr(function, "description", None),
        verb=getattr(function, "verb", None),
        is_async=getattr(function, "is_async", None),
        kind=_value(getattr(function, "kind", None)),
        is_public=getattr(function, "is_public", None),
        is_constructor=getattr(function, "is_constructor", None),
        field_bindings=links,
        producer_ref=_producer_ref(kind="function", obj=function),
    )


def _function_binding(link: Any) -> OrmFunctionBinding:
    function = getattr(link, "function_config", None)
    return OrmFunctionBinding(
        id=getattr(link, "id", None),
        entity_id=getattr(link, "class_config_id", None),
        function_id=getattr(link, "function_config_id", None),
        position=getattr(link, "position", None),
        is_public=getattr(link, "is_public", None),
        is_constructor=getattr(link, "is_constructor", None),
        function=_function_spec(function),
    )


def _relationship_field(field: Any) -> OrmRelationshipField:
    attr = getattr(field, "attribute_config", None)
    return OrmRelationshipField(
        id=getattr(field, "id", None),
        relationship_id=getattr(field, "class_config_relationship_id", None),
        field_id=getattr(field, "attribute_config_id", None),
        direction=_value(getattr(field, "direction", None)),
        role=_value(getattr(field, "role", None)),
        field=_field_spec(attr),
        producer_ref=_producer_ref(kind="relationship_field", obj=field),
    )


def _relationship_spec(rel: Any) -> OrmRelationshipSpec:
    fields = [
        _relationship_field(field)
        for field in (getattr(rel, "class_config_relationship_attributes", None) or [])
        if field is not None
    ]
    return OrmRelationshipSpec(
        id=getattr(rel, "id", None),
        source_entity_id=getattr(rel, "class_config_id", None),
        target_entity_id=getattr(rel, "target_class_config_id", None),
        relationship_key=getattr(rel, "relationship_key", None),
        relationship_type=_value(getattr(rel, "relationship_type", None)),
        identity_rail=_value(getattr(rel, "identity_rail", None)),
        forward_required=getattr(rel, "forward_required", None),
        forward_loading_strategy=_value(getattr(rel, "forward_loading_strategy", None)),
        reverse_loading_strategy=_value(getattr(rel, "reverse_loading_strategy", None)),
        fields=fields,
        producer_ref=_producer_ref(kind="relationship", obj=rel),
    )


def _entity_spec(class_config: Any, *, node_id: UUID | None = None) -> OrmEntitySpec:
    return OrmEntitySpec(
        id=getattr(class_config, "id", None),
        entity_fqn=getattr(class_config, "class_fqn", None),
        name=getattr(class_config, "name", None),
        value_mode=_value(getattr(class_config, "value_mode", "graph_ref")),
        identity_mode=_value(getattr(class_config, "identity_mode", "contained")),
        parent_entity_id=getattr(class_config, "parent_class_id", None),
        field_bindings=[
            _field_binding(link)
            for link in (
                getattr(class_config, "class_config_attribute_configs", None) or []
            )
            if link is not None
        ],
        function_bindings=[
            _function_binding(link)
            for link in (
                getattr(class_config, "class_config_function_configs", None) or []
            )
            if link is not None
        ],
        relationships=[
            _relationship_spec(rel)
            for rel in (getattr(class_config, "class_config_relationships", None) or [])
            if rel is not None
        ],
        producer_ref=_producer_ref(kind="entity", obj=class_config, node_id=node_id),
    )


def orm_graph_binding_snapshot_from_object_config_graph(
    *, object_config_graph: Any
) -> OrmGraphBindingSnapshot:
    """Translate a Meta ObjectConfigGraph into the ORM-owned binding artifact."""

    entities: list[OrmEntitySpec] = []
    for node in getattr(object_config_graph, "object_config_graph_nodes", ()) or ():
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        entities.append(_entity_spec(class_config, node_id=getattr(node, "id", None)))

    return OrmGraphBindingSnapshot(
        source_package=getattr(object_config_graph, "fqn_prefix", None),
        graph_id=getattr(object_config_graph, "id", None),
        entities=entities,
    )


def dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
    *, object_config_graph: Any
) -> bytes:
    """Translate Meta graph truth into deterministic ORM graph binding bytes."""

    snapshot = orm_graph_binding_snapshot_from_object_config_graph(
        object_config_graph=object_config_graph
    )
    return dump_orm_graph_binding_snapshot_msgpack(snapshot=snapshot)


__all__ = [
    "dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph",
    "orm_graph_binding_snapshot_from_object_config_graph",
]
