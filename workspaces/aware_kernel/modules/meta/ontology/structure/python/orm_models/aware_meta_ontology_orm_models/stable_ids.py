# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_META = uuid5(NAMESPACE_URL, "aware://meta/v1")


def stable_attribute_id(*, attribute_config_id: UUID, owner_key: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: attribute_config_id, owner_key"""

    return uuid5(NS_META, f"aware:attribute:{attribute_config_id}:{owner_key}")


def stable_attribute_change_id(*, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id"""

    return uuid5(NS_META, f"aware:attribute_change:{change_id}")


def stable_attribute_config_id(*, owner_key: str, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: owner_key, name"""

    owner_key_norm = (owner_key or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(NS_META, f"aware:attribute_config:{owner_key_norm}:{name_norm}")


def stable_attribute_config_overlay_id(*, object_config_graph_overlay_id: UUID, attribute_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_overlay_id, attribute_config_id"""

    return uuid5(NS_META, f"aware:attribute_config_overlay:{object_config_graph_overlay_id}:{attribute_config_id}")


def stable_attribute_type_descriptor_id(
    *, collection_kind: str = "single", kind: str, entity_id: UUID | None = None, child_links_fingerprint: str = ""
) -> UUID:
    """Compiler-generated from class-attribute identity keys: collection_kind, kind, entity_id, child_links_fingerprint"""

    collection_kind_norm = (collection_kind or "").casefold().strip() or "single"
    kind_norm = (kind or "").casefold().strip()
    entity_id_str = str(entity_id) if entity_id is not None else ""
    return uuid5(
        NS_META,
        f"aware:attribute_type_descriptor:{collection_kind_norm}:{kind_norm}:{entity_id_str}:{child_links_fingerprint}",
    )


def stable_attribute_type_descriptor_link_id(
    *, attribute_type_descriptor_id: UUID, child_id: UUID, role: str, position: int = 0
) -> UUID:
    """Compiler-generated from class-attribute identity keys: attribute_type_descriptor_id, child_id, role, position"""

    role_norm = (role or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:attribute_type_descriptor_link:{attribute_type_descriptor_id}:{child_id}:{role_norm}:{position}",
    )


def stable_attribute_value_id(*, type_descriptor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: type_descriptor_id"""

    return uuid5(NS_META, f"aware:attribute_value:{type_descriptor_id}")


def stable_attribute_value_change_id(*, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id"""

    return uuid5(NS_META, f"aware:attribute_value_change:{change_id}")


def stable_attribute_value_link_id(*, child_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: child_id"""

    return uuid5(NS_META, f"aware:attribute_value_link:{child_id}")


def stable_attribute_value_link_change_id(*, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id"""

    return uuid5(NS_META, f"aware:attribute_value_link_change:{change_id}")


def stable_class_config_id(*, object_config_graph_node_id: UUID, class_fqn: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_node_id, class_fqn"""

    class_fqn_norm = (class_fqn or "").casefold().strip()
    return uuid5(NS_META, f"aware:class_config:{object_config_graph_node_id}:{class_fqn_norm}")


def stable_class_config_attribute_config_id(*, class_config_id: UUID, attribute_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_id, attribute_config_id"""

    return uuid5(NS_META, f"aware:class_config_attribute_config:{class_config_id}:{attribute_config_id}")


def stable_class_config_function_config_id(*, class_config_id: UUID, function_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_id, function_config_id"""

    return uuid5(NS_META, f"aware:class_config_function_config:{class_config_id}:{function_config_id}")


def stable_class_config_overlay_id(*, object_config_graph_overlay_id: UUID, class_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_overlay_id, class_config_id"""

    return uuid5(NS_META, f"aware:class_config_overlay:{object_config_graph_overlay_id}:{class_config_id}")


def stable_class_config_relationship_id(
    *, class_config_id: UUID, target_class_config_id: UUID, relationship_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_id, target_class_config_id, relationship_key"""

    relationship_key_norm = (relationship_key or "").casefold().strip()
    return uuid5(
        NS_META, f"aware:class_config_relationship:{class_config_id}:{target_class_config_id}:{relationship_key_norm}"
    )


def stable_class_config_relationship_association_id(
    *, class_config_id: UUID, class_config_relationship_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_id, class_config_relationship_id"""

    return uuid5(
        NS_META, f"aware:class_config_relationship_association:{class_config_id}:{class_config_relationship_id}"
    )


def stable_class_config_relationship_attribute_id(
    *, class_config_relationship_id: UUID, attribute_config_id: UUID, direction: str, role: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_relationship_id, attribute_config_id, direction, role"""

    direction_norm = (direction or "").casefold().strip()
    role_norm = (role or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:class_config_relationship_attribute:{class_config_relationship_id}:{attribute_config_id}:{direction_norm}:{role_norm}",
    )


def stable_class_instance_id(*, object_instance_graph_id: UUID, class_config_id: UUID, source_object_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_id, class_config_id, source_object_id"""

    return uuid5(NS_META, f"aware:class_instance:{object_instance_graph_id}:{class_config_id}:{source_object_id}")


def stable_class_instance_attribute_id(*, class_instance_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_instance_id, attribute_id"""

    return uuid5(NS_META, f"aware:class_instance_attribute:{class_instance_id}:{attribute_id}")


def stable_class_instance_change_id(*, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id"""

    return uuid5(NS_META, f"aware:class_instance_change:{change_id}")


def stable_class_instance_identity_id(*, object_instance_graph_identity_id: UUID, class_instance_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_identity_id, class_instance_id"""

    return uuid5(NS_META, f"aware:class_instance_identity:{object_instance_graph_identity_id}:{class_instance_id}")


def stable_class_instance_relationship_id(
    *, class_config_relationship_id: UUID, source_class_instance_id: UUID, target_class_instance_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_relationship_id, source_class_instance_id, target_class_instance_id"""

    return uuid5(
        NS_META,
        f"aware:class_instance_relationship:{class_config_relationship_id}:{source_class_instance_id}:{target_class_instance_id}",
    )


def stable_class_instance_relationship_change_id(
    *,
    change_id: UUID,
    class_config_relationship_id: UUID,
    source_class_instance_id: UUID,
    target_class_instance_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id, class_config_relationship_id, source_class_instance_id, target_class_instance_id"""

    return uuid5(
        NS_META,
        f"aware:class_instance_relationship_change:{change_id}:{class_config_relationship_id}:{source_class_instance_id}:{target_class_instance_id}",
    )


def stable_class_instance_relationship_identity_id(
    *, object_instance_graph_identity_id: UUID, class_instance_relationship_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_identity_id, class_instance_relationship_id"""

    return uuid5(
        NS_META,
        f"aware:class_instance_relationship_identity:{object_instance_graph_identity_id}:{class_instance_relationship_id}",
    )


def stable_code_section_annotation_discriminate_id(
    *, fqn_prefix: str, namespace: str, class_name: str, attribute_name: str, mode: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, attribute_name, mode"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    attribute_name_norm = (attribute_name or "").casefold().strip()
    mode_norm = (mode or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_discriminate:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{attribute_name_norm}:{mode_norm}",
    )


def stable_code_section_annotation_identity_id(
    *, fqn_prefix: str, namespace: str, class_name: str, mode: str = "contained"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, mode"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    mode_norm = (mode or "").casefold().strip() or "contained"
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_identity:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{mode_norm}",
    )


def stable_code_section_annotation_index_id(*, fqn_prefix: str, namespace: str, class_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    return uuid5(NS_META, f"aware:code_section_annotation_index:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}")


def stable_code_section_annotation_load_id(
    *, fqn_prefix: str, namespace: str, class_name: str, attribute_name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, attribute_name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    attribute_name_norm = (attribute_name or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_load:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{attribute_name_norm}",
    )


def stable_code_section_annotation_one_of_id(
    *, fqn_prefix: str, namespace: str, class_name: str, mode: str = "validation"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, mode"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    mode_norm = (mode or "").casefold().strip() or "validation"
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_one_of:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{mode_norm}",
    )


def stable_code_section_annotation_overlay_id(
    *, source_path: str, language: str, entity: str, fqn_prefix: str, namespace: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: source_path, language, entity, fqn_prefix, namespace"""

    source_path_norm = (source_path or "").casefold().strip()
    language_norm = (language or "").casefold().strip()
    entity_norm = (entity or "").casefold().strip()
    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_overlay:{source_path_norm}:{language_norm}:{entity_norm}:{fqn_prefix_norm}:{namespace_norm}",
    )


def stable_code_section_annotation_override_id(
    *, fqn_prefix: str, namespace: str, class_name: str, attribute_name: str, target: str, nullable: bool = False
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, attribute_name, target, nullable"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    attribute_name_norm = (attribute_name or "").casefold().strip()
    target_norm = (target or "").casefold().strip()
    nullable_int = int(nullable)
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_override:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{attribute_name_norm}:{target_norm}:{nullable_int}",
    )


def stable_code_section_annotation_reference_id(
    *, fqn_prefix: str, namespace: str, class_name: str, attribute_name: str, mode: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, attribute_name, mode"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    attribute_name_norm = (attribute_name or "").casefold().strip()
    mode_norm = (mode or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_reference:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{attribute_name_norm}:{mode_norm}",
    )


def stable_code_section_annotation_storage_id(
    *, fqn_prefix: str, namespace: str, class_name: str, name: str, operation: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name, name, operation"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    operation_norm = (operation or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:code_section_annotation_storage:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}:{name_norm}:{operation_norm}",
    )


def stable_enum_id(*, enum_config_id: UUID, enum_option_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: enum_config_id, enum_option_id"""

    return uuid5(NS_META, f"aware:enum:{enum_config_id}:{enum_option_id}")


def stable_enum_change_id(*, change_id: UUID, enum_option_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id, enum_option_id"""

    return uuid5(NS_META, f"aware:enum_change:{change_id}:{enum_option_id}")


def stable_enum_config_id(*, object_config_graph_node_id: UUID, enum_fqn: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_node_id, enum_fqn"""

    enum_fqn_norm = (enum_fqn or "").casefold().strip()
    return uuid5(NS_META, f"aware:enum_config:{object_config_graph_node_id}:{enum_fqn_norm}")


def stable_enum_config_overlay_id(*, object_config_graph_overlay_id: UUID, enum_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_overlay_id, enum_config_id"""

    return uuid5(NS_META, f"aware:enum_config_overlay:{object_config_graph_overlay_id}:{enum_config_id}")


def stable_enum_option_id(*, enum_config_id: UUID, value: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: enum_config_id, value"""

    value_norm = (value or "").casefold().strip()
    return uuid5(NS_META, f"aware:enum_option:{enum_config_id}:{value_norm}")


def stable_enum_option_overlay_id(*, object_config_graph_overlay_id: UUID, enum_option_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_overlay_id, enum_option_id"""

    return uuid5(NS_META, f"aware:enum_option_overlay:{object_config_graph_overlay_id}:{enum_option_id}")


def stable_function_call_id(*, object_instance_graph_lane_id: UUID, function_config_id: UUID, call_key: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_lane_id, function_config_id, call_key"""

    return uuid5(NS_META, f"aware:function_call:{object_instance_graph_lane_id}:{function_config_id}:{call_key}")


def stable_function_call_argument_id(*, function_call_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_call_id, attribute_id"""

    return uuid5(NS_META, f"aware:function_call_argument:{function_call_id}:{attribute_id}")


def stable_function_call_response_id(*, function_call_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_call_id"""

    return uuid5(NS_META, f"aware:function_call_response:{function_call_id}")


def stable_function_call_response_attribute_id(*, function_call_response_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_call_response_id, attribute_id"""

    return uuid5(NS_META, f"aware:function_call_response_attribute:{function_call_response_id}:{attribute_id}")


def stable_function_call_response_commit_id(
    *, function_call_response_id: UUID, object_instance_graph_commit_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_call_response_id, object_instance_graph_commit_id"""

    return uuid5(
        NS_META, f"aware:function_call_response_commit:{function_call_response_id}:{object_instance_graph_commit_id}"
    )


def stable_function_config_id(*, owner_key: str, name: str, kind: str = "instance") -> UUID:
    """Compiler-generated from class-attribute identity keys: owner_key, name, kind"""

    owner_key_norm = (owner_key or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    kind_norm = (kind or "").casefold().strip() or "instance"
    return uuid5(NS_META, f"aware:function_config:{owner_key_norm}:{name_norm}:{kind_norm}")


def stable_function_config_attribute_config_id(*, function_config_id: UUID, name: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_config_id, name, type"""

    name_norm = (name or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_META, f"aware:function_config_attribute_config:{function_config_id}:{name_norm}:{type_norm}")


def stable_function_config_invocation_id(
    *,
    function_config_id: UUID,
    target_function_config_id: UUID,
    position: int,
    kind: str,
    relationship_fingerprint: str = "owner",
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_config_id, target_function_config_id, position, kind, relationship_fingerprint"""

    kind_norm = (kind or "").casefold().strip()
    relationship_fingerprint_norm = (relationship_fingerprint or "").casefold().strip() or "owner"
    return uuid5(
        NS_META,
        f"aware:function_config_invocation:{function_config_id}:{target_function_config_id}:{position}:{kind_norm}:{relationship_fingerprint_norm}",
    )


def stable_function_config_overlay_id(*, object_config_graph_overlay_id: UUID, function_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_overlay_id, function_config_id"""

    return uuid5(NS_META, f"aware:function_config_overlay:{object_config_graph_overlay_id}:{function_config_id}")


def stable_function_impl_id(*, function_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_config_id"""

    return uuid5(NS_META, f"aware:function_impl:{function_config_id}")


def stable_function_impl_instruction_id(*, function_impl_id: UUID, type: str, sequence: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_id, type, sequence"""

    type_norm = (type or "").casefold().strip()
    return uuid5(NS_META, f"aware:function_impl_instruction:{function_impl_id}:{type_norm}:{sequence}")


def stable_function_impl_instruction_construct_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_construct:{function_impl_instruction_id}")


def stable_function_impl_instruction_construct_assignment_id(
    *,
    function_impl_instruction_construct_id: UUID,
    target_class_config_attribute_config_id: UUID,
    value_source_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_construct_id, target_class_config_attribute_config_id, value_source_id"""

    return uuid5(
        NS_META,
        f"aware:function_impl_instruction_construct_assignment:{function_impl_instruction_construct_id}:{target_class_config_attribute_config_id}:{value_source_id}",
    )


def stable_function_impl_instruction_delete_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_delete:{function_impl_instruction_id}")


def stable_function_impl_instruction_invoke_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_invoke:{function_impl_instruction_id}")


def stable_function_impl_instruction_invoke_attribute_config_id(
    *, function_impl_instruction_invoke_id: UUID, attribute_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_invoke_id, attribute_config_id"""

    return uuid5(
        NS_META,
        f"aware:function_impl_instruction_invoke_attribute_config:{function_impl_instruction_invoke_id}:{attribute_config_id}",
    )


def stable_function_impl_instruction_let_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_let:{function_impl_instruction_id}")


def stable_function_impl_instruction_require_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_require:{function_impl_instruction_id}")


def stable_function_impl_instruction_require_operand_id(
    *, function_impl_instruction_require_id: UUID, position: int
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_require_id, position"""

    return uuid5(
        NS_META, f"aware:function_impl_instruction_require_operand:{function_impl_instruction_require_id}:{position}"
    )


def stable_function_impl_instruction_set_id(*, function_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id"""

    return uuid5(NS_META, f"aware:function_impl_instruction_set:{function_impl_instruction_id}")


def stable_function_impl_value_source_id(*, function_impl_instruction_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_instruction_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_META, f"aware:function_impl_value_source:{function_impl_instruction_id}:{key_norm}")


def stable_function_impl_value_source_literal_primitive_id(*, function_impl_value_source_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_value_source_id"""

    return uuid5(NS_META, f"aware:function_impl_value_source_literal_primitive:{function_impl_value_source_id}")


def stable_function_impl_value_source_read_path_id(*, function_impl_value_source_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_value_source_id"""

    return uuid5(NS_META, f"aware:function_impl_value_source_read_path:{function_impl_value_source_id}")


def stable_function_impl_value_source_read_path_segment_id(
    *, function_impl_value_source_read_path_id: UUID, position: int
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_value_source_read_path_id, position"""

    return uuid5(
        NS_META,
        f"aware:function_impl_value_source_read_path_segment:{function_impl_value_source_read_path_id}:{position}",
    )


def stable_function_impl_value_source_transform_id(*, function_impl_value_source_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_value_source_id"""

    return uuid5(NS_META, f"aware:function_impl_value_source_transform:{function_impl_value_source_id}")


def stable_function_impl_value_source_transform_operand_id(
    *, function_impl_value_source_transform_id: UUID, position: int
) -> UUID:
    """Compiler-generated from class-attribute identity keys: function_impl_value_source_transform_id, position"""

    return uuid5(
        NS_META,
        f"aware:function_impl_value_source_transform_operand:{function_impl_value_source_transform_id}:{position}",
    )


def stable_inline_value_instance_id(*, class_config_id: UUID, owner_key: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: class_config_id, owner_key"""

    return uuid5(NS_META, f"aware:inline_value_instance:{class_config_id}:{owner_key}")


def stable_inline_value_instance_attribute_id(*, inline_value_instance_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: inline_value_instance_id, attribute_id"""

    return uuid5(NS_META, f"aware:inline_value_instance_attribute:{inline_value_instance_id}:{attribute_id}")


def stable_object_config_graph_id(*, fqn_prefix: str, language: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, language"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    language_norm = (language or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph:{fqn_prefix_norm}:{language_norm}")


def stable_object_config_graph_annotation_id(*, kind: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: kind"""

    kind_norm = (kind or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_annotation:{kind_norm}")


def stable_object_config_graph_binding_id(*, object_config_graph_id: UUID, target_object_config_graph_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_id, target_object_config_graph_id"""

    return uuid5(NS_META, f"aware:object_config_graph_binding:{object_config_graph_id}:{target_object_config_graph_id}")


def stable_object_config_graph_binding_class_id(
    *, object_config_graph_binding_id: UUID, source_class_id: UUID, target_class_id: UUID, target_attribute_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_binding_id, source_class_id, target_class_id, target_attribute_id"""

    return uuid5(
        NS_META,
        f"aware:object_config_graph_binding_class:{object_config_graph_binding_id}:{source_class_id}:{target_class_id}:{target_attribute_id}",
    )


def stable_object_config_graph_binding_formula_id(
    *, object_config_graph_binding_class_id: UUID, key: str = "default"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_binding_class_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(
        NS_META, f"aware:object_config_graph_binding_formula:{object_config_graph_binding_class_id}:{key_norm}"
    )


def stable_object_config_graph_binding_formula_segment_reference_id(
    *,
    object_config_graph_binding_formula_id: UUID,
    content_part_text_segment_id: UUID,
    source_class_config_attribute_config_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_binding_formula_id, content_part_text_segment_id, source_class_config_attribute_config_id"""

    return uuid5(
        NS_META,
        f"aware:object_config_graph_binding_formula_segment_reference:{object_config_graph_binding_formula_id}:{content_part_text_segment_id}:{source_class_config_attribute_config_id}",
    )


def stable_object_config_graph_identity_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_identity:{key_norm}")


def stable_object_config_graph_mirror_id(
    *,
    source_object_config_graph_id: UUID,
    code_section_mirror_id: UUID,
    fqn_prefix: str,
    namespace: str,
    target_text: str,
    layout_kind: str = "aware",
    relative_path: str,
    target_kind: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: source_object_config_graph_id, code_section_mirror_id, fqn_prefix, namespace, target_text, layout_kind, relative_path, target_kind"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    target_text_norm = (target_text or "").casefold().strip()
    layout_kind_norm = (layout_kind or "").casefold().strip() or "aware"
    relative_path_norm = (relative_path or "").casefold().strip()
    target_kind_norm = (target_kind or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:object_config_graph_mirror:{source_object_config_graph_id}:{code_section_mirror_id}:{fqn_prefix_norm}:{namespace_norm}:{target_text_norm}:{layout_kind_norm}:{relative_path_norm}:{target_kind_norm}",
    )


def stable_object_config_graph_node_id(*, object_config_graph_id: UUID, type: str, node_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_id, type, node_key"""

    type_norm = (type or "").casefold().strip()
    node_key_norm = (node_key or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_node:{object_config_graph_id}:{type_norm}:{node_key_norm}")


def stable_object_config_graph_node_layout_id(*, layout_kind: str = "aware", relative_path: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: layout_kind, relative_path"""

    layout_kind_norm = (layout_kind or "").casefold().strip() or "aware"
    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_node_layout:{layout_kind_norm}:{relative_path_norm}")


def stable_object_config_graph_overlay_id(*, language: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: language"""

    language_norm = (language or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_overlay:{language_norm}")


def stable_object_config_graph_package_id(*, package_name: str, fqn_prefix: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: package_name, fqn_prefix"""

    package_name_norm = (package_name or "").casefold().strip()
    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_package:{package_name_norm}:{fqn_prefix_norm}")


def stable_object_config_graph_package_build_id(*, object_config_graph_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_package_id"""

    return uuid5(NS_META, f"aware:object_config_graph_package_build:{object_config_graph_package_id}")


def stable_object_config_graph_package_dependency_id(*, target_object_config_graph_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: target_object_config_graph_package_id"""

    return uuid5(NS_META, f"aware:object_config_graph_package_dependency:{target_object_config_graph_package_id}")


def stable_object_config_graph_package_language_materialization_id(*, target_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: target_key"""

    target_key_norm = (target_key or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_config_graph_package_language_materialization:{target_key_norm}")


def stable_object_config_graph_package_language_materialization_package_id(*, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id"""

    return uuid5(NS_META, f"aware:object_config_graph_package_language_materialization_package:{code_package_id}")


def stable_object_config_graph_relationship_id(
    *, object_config_graph_id: UUID, target_object_config_graph_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_id, target_object_config_graph_id"""

    return uuid5(
        NS_META, f"aware:object_config_graph_relationship:{object_config_graph_id}:{target_object_config_graph_id}"
    )


def stable_object_config_graph_relationship_class_id(
    *, object_config_graph_relationship_id: UUID, class_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_relationship_id, class_config_id"""

    return uuid5(
        NS_META, f"aware:object_config_graph_relationship_class:{object_config_graph_relationship_id}:{class_config_id}"
    )


def stable_object_instance_graph_id(*, object_projection_graph_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_instance_graph:{object_projection_graph_id}:{key_norm}")


def stable_object_instance_graph_branch_id(*, object_instance_graph_identity_id: UUID, branch_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_identity_id, branch_id"""

    return uuid5(NS_META, f"aware:object_instance_graph_branch:{object_instance_graph_identity_id}:{branch_id}")


def stable_object_instance_graph_branch_relationship_id(
    *, object_instance_graph_branch_id: UUID, target_object_instance_graph_branch_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_branch_id, target_object_instance_graph_branch_id"""

    return uuid5(
        NS_META,
        f"aware:object_instance_graph_branch_relationship:{object_instance_graph_branch_id}:{target_object_instance_graph_branch_id}",
    )


def stable_object_instance_graph_change_id(*, object_instance_graph_identity_id: UUID, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_identity_id, change_id"""

    return uuid5(NS_META, f"aware:object_instance_graph_change:{object_instance_graph_identity_id}:{change_id}")


def stable_object_instance_graph_commit_id(*, object_instance_graph_identity_id: UUID, commit_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_identity_id, commit_id"""

    return uuid5(NS_META, f"aware:object_instance_graph_commit:{object_instance_graph_identity_id}:{commit_id}")


def stable_object_instance_graph_identity_id(
    *, object_projection_graph_identity_id: UUID, object_instance_graph_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_identity_id, object_instance_graph_id"""

    return uuid5(
        NS_META,
        f"aware:object_instance_graph_identity:{object_projection_graph_identity_id}:{object_instance_graph_id}",
    )


def stable_object_instance_graph_lane_id(*, object_instance_graph_branch_id: UUID, lane_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_branch_id, lane_id"""

    return uuid5(NS_META, f"aware:object_instance_graph_lane:{object_instance_graph_branch_id}:{lane_id}")


def stable_object_instance_graph_relationship_id(
    *, target_object_instance_graph_id: UUID, source_class_instance_id: UUID, target_class_instance_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: target_object_instance_graph_id, source_class_instance_id, target_class_instance_id"""

    return uuid5(
        NS_META,
        f"aware:object_instance_graph_relationship:{target_object_instance_graph_id}:{source_class_instance_id}:{target_class_instance_id}",
    )


def stable_object_projection_graph_id(*, object_config_graph_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_projection_graph:{object_config_graph_id}:{name_norm}")


def stable_object_projection_graph_binding_id(*, fqn_prefix: str, namespace: str, class_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, namespace, class_name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    namespace_norm = (namespace or "").casefold().strip()
    class_name_norm = (class_name or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_projection_graph_binding:{fqn_prefix_norm}:{namespace_norm}:{class_name_norm}")


def stable_object_projection_graph_constructor_id(
    *, object_projection_graph_id: UUID, root_node_id: UUID, function_constructor_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_id, root_node_id, function_constructor_id"""

    return uuid5(
        NS_META,
        f"aware:object_projection_graph_constructor:{object_projection_graph_id}:{root_node_id}:{function_constructor_id}",
    )


def stable_object_projection_graph_declaration_id(*, projection_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_name"""

    projection_name_norm = (projection_name or "").casefold().strip()
    return uuid5(NS_META, f"aware:object_projection_graph_declaration:{projection_name_norm}")


def stable_object_projection_graph_edge_id(
    *, object_projection_graph_id: UUID, class_config_relationship_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_id, class_config_relationship_id"""

    return uuid5(
        NS_META, f"aware:object_projection_graph_edge:{object_projection_graph_id}:{class_config_relationship_id}"
    )


def stable_object_projection_graph_identity_id(
    *, object_config_graph_identity_id: UUID, object_projection_graph_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_config_graph_identity_id, object_projection_graph_id"""

    return uuid5(
        NS_META,
        f"aware:object_projection_graph_identity:{object_config_graph_identity_id}:{object_projection_graph_id}",
    )


def stable_object_projection_graph_node_id(*, object_projection_graph_id: UUID, class_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_id, class_config_id"""

    return uuid5(NS_META, f"aware:object_projection_graph_node:{object_projection_graph_id}:{class_config_id}")


def stable_object_projection_graph_node_key_id(
    *, object_projection_graph_node_id: UUID, object_config_graph_binding_class_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_node_id, object_config_graph_binding_class_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_META,
        f"aware:object_projection_graph_node_key:{object_projection_graph_node_id}:{object_config_graph_binding_class_id}:{key_norm}",
    )


def stable_object_projection_graph_observable_id(
    *, object_projection_graph_identity_id: UUID, observable_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_identity_id, observable_key"""

    observable_key_norm = (observable_key or "").casefold().strip()
    return uuid5(
        NS_META, f"aware:object_projection_graph_observable:{object_projection_graph_identity_id}:{observable_key_norm}"
    )


def stable_object_projection_graph_relationship_id(
    *,
    object_projection_graph_id: UUID,
    target_object_projection_graph_id: UUID,
    class_config_relationship_id: UUID,
    source_object_projection_graph_node_id: UUID,
    target_object_projection_graph_node_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_id, target_object_projection_graph_id, class_config_relationship_id, source_object_projection_graph_node_id, target_object_projection_graph_node_id"""

    return uuid5(
        NS_META,
        f"aware:object_projection_graph_relationship:{object_projection_graph_id}:{target_object_projection_graph_id}:{class_config_relationship_id}:{source_object_projection_graph_node_id}:{target_object_projection_graph_node_id}",
    )


def stable_primitive_id(*, primitive_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: primitive_config_id"""

    return uuid5(NS_META, f"aware:primitive:{primitive_config_id}")


def stable_primitive_change_id(*, change_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id"""

    return uuid5(NS_META, f"aware:primitive_change:{change_id}")


def stable_primitive_config_id(*, primitive_type_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: primitive_type_id"""

    return uuid5(NS_META, f"aware:primitive_config:{primitive_type_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0b07fdff-3505-5a6d-906c-51d418182584": (
        "stable_function_impl_instruction_require_id",
        ("function_impl_instruction_id",),
    ),
    "0b2f6e6d-0d51-5dce-9fa7-a786782df0f0": ("stable_object_projection_graph_id", ("object_config_graph_id", "name")),
    "0d824274-d187-5f2b-bb9f-c5a69a518553": ("stable_object_instance_graph_id", ("object_projection_graph_id", "key")),
    "0e9106d0-99f0-531b-9fd2-1d4e3621d913": (
        "stable_function_impl_instruction_construct_id",
        ("function_impl_instruction_id",),
    ),
    "102207b6-cdea-5c2c-ae69-2ee93be3f704": (
        "stable_object_config_graph_node_id",
        ("object_config_graph_id", "type", "node_key"),
    ),
    "136e4527-7f39-5dd2-9631-39cfe710ee63": (
        "stable_object_instance_graph_lane_id",
        ("object_instance_graph_branch_id", "lane_id"),
    ),
    "14e83a49-4b04-5ff9-b5ce-cc72759b43fb": (
        "stable_object_instance_graph_commit_id",
        ("object_instance_graph_identity_id", "commit_id"),
    ),
    "1c2cd560-5486-5536-89f5-1cde3b2817af": (
        "stable_object_instance_graph_change_id",
        ("object_instance_graph_identity_id", "change_id"),
    ),
    "22abd186-841e-52d6-ac87-272e757af4be": (
        "stable_attribute_type_descriptor_link_id",
        ("attribute_type_descriptor_id", "child_id", "role", "position"),
    ),
    "23595872-2435-505b-a693-47e7044c1a96": (
        "stable_object_config_graph_binding_class_id",
        ("object_config_graph_binding_id", "source_class_id", "target_class_id", "target_attribute_id"),
    ),
    "24306491-dfa2-5f5e-8531-3ddfa9d4eca7": (
        "stable_object_config_graph_binding_id",
        ("object_config_graph_id", "target_object_config_graph_id"),
    ),
    "24d12de6-3c84-5c50-9c83-97b913ae90ef": (
        "stable_class_config_relationship_association_id",
        ("class_config_id", "class_config_relationship_id"),
    ),
    "282599c0-61dc-5e72-a457-a343989277fd": ("stable_enum_config_id", ("object_config_graph_node_id", "enum_fqn")),
    "2b11f642-38bd-5869-b67b-c8cf5d524cd8": (
        "stable_function_call_id",
        ("object_instance_graph_lane_id", "function_config_id", "call_key"),
    ),
    "2c740880-fd3a-5341-a7a4-e5f8cba606e0": (
        "stable_object_projection_graph_observable_id",
        ("object_projection_graph_identity_id", "observable_key"),
    ),
    "2d0c5135-02cb-50ab-a243-4792ff2f4e05": (
        "stable_function_impl_value_source_transform_operand_id",
        ("function_impl_value_source_transform_id", "position"),
    ),
    "2e1a491f-f7f1-5036-a44b-9535a9582da3": ("stable_object_config_graph_package_id", ("package_name", "fqn_prefix")),
    "37e775bf-2989-5f1c-bdfd-b6ca72544db5": ("stable_function_impl_id", ("function_config_id",)),
    "386f612d-244d-5b3a-bf29-95644d517f79": (
        "stable_class_instance_id",
        ("object_instance_graph_id", "class_config_id", "source_object_id"),
    ),
    "3a7d9c8b-251e-594f-83c9-e5239cd5cf9b": (
        "stable_object_projection_graph_relationship_id",
        (
            "object_projection_graph_id",
            "target_object_projection_graph_id",
            "class_config_relationship_id",
            "source_object_projection_graph_node_id",
            "target_object_projection_graph_node_id",
        ),
    ),
    "405d562c-542d-5b1e-870b-1c552f6e6cb9": (
        "stable_object_config_graph_relationship_id",
        ("object_config_graph_id", "target_object_config_graph_id"),
    ),
    "4bcf8bf7-3fcd-5d03-a0aa-f4e3c7be86b1": (
        "stable_class_config_function_config_id",
        ("class_config_id", "function_config_id"),
    ),
    "523af0e8-2e37-56f7-8b2c-d6c8f5eaa3cd": (
        "stable_function_impl_instruction_id",
        ("function_impl_id", "type", "sequence"),
    ),
    "57ae65cc-b16f-5212-8a54-7b15340787a2": ("stable_object_config_graph_id", ("fqn_prefix", "language")),
    "5c5d7430-9306-5502-96a3-2486aeff5a16": (
        "stable_function_impl_instruction_invoke_id",
        ("function_impl_instruction_id",),
    ),
    "5ff06af4-0efb-5723-83c4-63e9a2803729": ("stable_object_config_graph_identity_id", ("key",)),
    "615953a6-9d3f-50fa-b385-08a8343d22fa": ("stable_attribute_config_id", ("owner_key", "name")),
    "6664465f-8f9e-518a-84dc-bf87978161ef": (
        "stable_function_impl_value_source_id",
        ("function_impl_instruction_id", "key"),
    ),
    "666c0708-6e2c-56c4-8346-e0fac9d85c9a": (
        "stable_function_impl_instruction_construct_assignment_id",
        ("function_impl_instruction_construct_id", "target_class_config_attribute_config_id", "value_source_id"),
    ),
    "785bc927-42bd-53d2-bded-e1ae398c766e": (
        "stable_object_instance_graph_identity_id",
        ("object_projection_graph_identity_id", "object_instance_graph_id"),
    ),
    "79e96270-dac3-5814-aac2-0e62a8491b7c": (
        "stable_object_config_graph_binding_formula_id",
        ("object_config_graph_binding_class_id", "key"),
    ),
    "88a971f5-178f-5b1c-ae29-c562b93c27a6": (
        "stable_function_impl_instruction_delete_id",
        ("function_impl_instruction_id",),
    ),
    "8a206f1e-584b-5740-8d9b-81329d618097": ("stable_attribute_id", ("attribute_config_id", "owner_key")),
    "8ce3cbbd-b4e5-50a1-a914-1289ce73d80c": (
        "stable_object_projection_graph_constructor_id",
        ("object_projection_graph_id", "root_node_id", "function_constructor_id"),
    ),
    "923f7ecf-a644-5d3d-a692-7463c4c792d0": (
        "stable_function_impl_instruction_invoke_attribute_config_id",
        ("function_impl_instruction_invoke_id", "attribute_config_id"),
    ),
    "95b54c55-c785-5fcf-a84d-4c2d49b6c7dd": ("stable_function_call_response_id", ("function_call_id",)),
    "9600091b-e605-5278-bdec-348df9469583": (
        "stable_function_impl_value_source_transform_id",
        ("function_impl_value_source_id",),
    ),
    "997e714f-61ec-554e-9b32-4ae2a38287d5": (
        "stable_object_projection_graph_node_key_id",
        ("object_projection_graph_node_id", "object_config_graph_binding_class_id", "key"),
    ),
    "9c3fecaf-6630-52f8-98ba-98829d593a8f": (
        "stable_class_config_relationship_attribute_id",
        ("class_config_relationship_id", "attribute_config_id", "direction", "role"),
    ),
    "a22d2949-c06c-5866-9322-315792108f81": (
        "stable_object_instance_graph_branch_relationship_id",
        ("object_instance_graph_branch_id", "target_object_instance_graph_branch_id"),
    ),
    "a303d44d-53e1-5c85-8511-5e1509ab1021": (
        "stable_object_projection_graph_identity_id",
        ("object_config_graph_identity_id", "object_projection_graph_id"),
    ),
    "a3ff672b-5ead-51bd-8092-cbde9d868023": (
        "stable_object_config_graph_binding_formula_segment_reference_id",
        (
            "object_config_graph_binding_formula_id",
            "content_part_text_segment_id",
            "source_class_config_attribute_config_id",
        ),
    ),
    "a4df4f29-a955-5f78-8aaa-9841c84c35e5": (
        "stable_function_config_invocation_id",
        ("function_config_id", "target_function_config_id", "position", "kind", "relationship_fingerprint"),
    ),
    "a589119f-29a7-51b8-baa4-0982795817c6": (
        "stable_object_config_graph_relationship_class_id",
        ("object_config_graph_relationship_id", "class_config_id"),
    ),
    "a78f4526-f95d-5aba-9ff7-2b40463209d7": ("stable_inline_value_instance_id", ("class_config_id", "owner_key")),
    "ac3205d2-d898-5380-bfca-b2998c43d978": ("stable_class_config_id", ("object_config_graph_node_id", "class_fqn")),
    "ac95ec59-722d-52c9-9f23-3209f09f4da0": (
        "stable_object_instance_graph_branch_id",
        ("object_instance_graph_identity_id", "branch_id"),
    ),
    "b43867f9-8d1e-5b66-8fab-9f195d2aeede": (
        "stable_function_impl_value_source_read_path_segment_id",
        ("function_impl_value_source_read_path_id", "position"),
    ),
    "be3308e7-f15c-550b-8ce2-bb6305423c02": ("stable_function_config_id", ("owner_key", "name", "kind")),
    "bf7be671-75b0-5077-bf2a-7029b9fabd0b": (
        "stable_function_impl_instruction_set_id",
        ("function_impl_instruction_id",),
    ),
    "c1356253-0a65-5c70-9366-05186b2739b1": (
        "stable_object_projection_graph_edge_id",
        ("object_projection_graph_id", "class_config_relationship_id"),
    ),
    "c38986a2-94b9-53d8-8e27-79313b0a4117": (
        "stable_function_impl_value_source_literal_primitive_id",
        ("function_impl_value_source_id",),
    ),
    "c6619ca6-b035-599b-9498-e7c9258e17d8": (
        "stable_class_instance_identity_id",
        ("object_instance_graph_identity_id", "class_instance_id"),
    ),
    "c7ad7495-ce85-5e58-a538-6cbc4aaeb937": (
        "stable_function_config_attribute_config_id",
        ("function_config_id", "name", "type"),
    ),
    "ceb3aa47-df0e-5429-ad25-99dae61bacd7": (
        "stable_class_config_relationship_id",
        ("class_config_id", "target_class_config_id", "relationship_key"),
    ),
    "d2da5a41-edd8-5d16-876e-a06a9252eafc": (
        "stable_function_impl_instruction_let_id",
        ("function_impl_instruction_id",),
    ),
    "d53964f4-3a0b-582d-9bc2-91f401f6dca7": (
        "stable_class_config_attribute_config_id",
        ("class_config_id", "attribute_config_id"),
    ),
    "ea70b7f4-8092-591d-9eed-56b518828b8c": ("stable_enum_option_id", ("enum_config_id", "value")),
    "f0efabd0-4e1b-5c12-8948-6fbb892e4a16": (
        "stable_function_impl_instruction_require_operand_id",
        ("function_impl_instruction_require_id", "position"),
    ),
    "f12a49af-e1d8-53cb-b794-c4585f828384": (
        "stable_function_impl_value_source_read_path_id",
        ("function_impl_value_source_id",),
    ),
    "f8e2ffa2-6254-5b9d-a822-8f8318707212": (
        "stable_object_projection_graph_node_id",
        ("object_projection_graph_id", "class_config_id"),
    ),
    "fa742756-9b18-504c-b5dd-428542f3841e": (
        "stable_class_instance_relationship_identity_id",
        ("object_instance_graph_identity_id", "class_instance_relationship_id"),
    ),
}

__all__ = [
    "stable_attribute_id",
    "stable_attribute_change_id",
    "stable_attribute_config_id",
    "stable_attribute_config_overlay_id",
    "stable_attribute_type_descriptor_id",
    "stable_attribute_type_descriptor_link_id",
    "stable_attribute_value_id",
    "stable_attribute_value_change_id",
    "stable_attribute_value_link_id",
    "stable_attribute_value_link_change_id",
    "stable_class_config_id",
    "stable_class_config_attribute_config_id",
    "stable_class_config_function_config_id",
    "stable_class_config_overlay_id",
    "stable_class_config_relationship_id",
    "stable_class_config_relationship_association_id",
    "stable_class_config_relationship_attribute_id",
    "stable_class_instance_id",
    "stable_class_instance_attribute_id",
    "stable_class_instance_change_id",
    "stable_class_instance_identity_id",
    "stable_class_instance_relationship_id",
    "stable_class_instance_relationship_change_id",
    "stable_class_instance_relationship_identity_id",
    "stable_code_section_annotation_discriminate_id",
    "stable_code_section_annotation_identity_id",
    "stable_code_section_annotation_index_id",
    "stable_code_section_annotation_load_id",
    "stable_code_section_annotation_one_of_id",
    "stable_code_section_annotation_overlay_id",
    "stable_code_section_annotation_override_id",
    "stable_code_section_annotation_reference_id",
    "stable_code_section_annotation_storage_id",
    "stable_enum_id",
    "stable_enum_change_id",
    "stable_enum_config_id",
    "stable_enum_config_overlay_id",
    "stable_enum_option_id",
    "stable_enum_option_overlay_id",
    "stable_function_call_id",
    "stable_function_call_argument_id",
    "stable_function_call_response_id",
    "stable_function_call_response_attribute_id",
    "stable_function_call_response_commit_id",
    "stable_function_config_id",
    "stable_function_config_attribute_config_id",
    "stable_function_config_invocation_id",
    "stable_function_config_overlay_id",
    "stable_function_impl_id",
    "stable_function_impl_instruction_id",
    "stable_function_impl_instruction_construct_id",
    "stable_function_impl_instruction_construct_assignment_id",
    "stable_function_impl_instruction_delete_id",
    "stable_function_impl_instruction_invoke_id",
    "stable_function_impl_instruction_invoke_attribute_config_id",
    "stable_function_impl_instruction_let_id",
    "stable_function_impl_instruction_require_id",
    "stable_function_impl_instruction_require_operand_id",
    "stable_function_impl_instruction_set_id",
    "stable_function_impl_value_source_id",
    "stable_function_impl_value_source_literal_primitive_id",
    "stable_function_impl_value_source_read_path_id",
    "stable_function_impl_value_source_read_path_segment_id",
    "stable_function_impl_value_source_transform_id",
    "stable_function_impl_value_source_transform_operand_id",
    "stable_inline_value_instance_id",
    "stable_inline_value_instance_attribute_id",
    "stable_object_config_graph_id",
    "stable_object_config_graph_annotation_id",
    "stable_object_config_graph_binding_id",
    "stable_object_config_graph_binding_class_id",
    "stable_object_config_graph_binding_formula_id",
    "stable_object_config_graph_binding_formula_segment_reference_id",
    "stable_object_config_graph_identity_id",
    "stable_object_config_graph_mirror_id",
    "stable_object_config_graph_node_id",
    "stable_object_config_graph_node_layout_id",
    "stable_object_config_graph_overlay_id",
    "stable_object_config_graph_package_id",
    "stable_object_config_graph_package_build_id",
    "stable_object_config_graph_package_dependency_id",
    "stable_object_config_graph_package_language_materialization_id",
    "stable_object_config_graph_package_language_materialization_package_id",
    "stable_object_config_graph_relationship_id",
    "stable_object_config_graph_relationship_class_id",
    "stable_object_instance_graph_id",
    "stable_object_instance_graph_branch_id",
    "stable_object_instance_graph_branch_relationship_id",
    "stable_object_instance_graph_change_id",
    "stable_object_instance_graph_commit_id",
    "stable_object_instance_graph_identity_id",
    "stable_object_instance_graph_lane_id",
    "stable_object_instance_graph_relationship_id",
    "stable_object_projection_graph_id",
    "stable_object_projection_graph_binding_id",
    "stable_object_projection_graph_constructor_id",
    "stable_object_projection_graph_declaration_id",
    "stable_object_projection_graph_edge_id",
    "stable_object_projection_graph_identity_id",
    "stable_object_projection_graph_node_id",
    "stable_object_projection_graph_node_key_id",
    "stable_object_projection_graph_observable_id",
    "stable_object_projection_graph_relationship_id",
    "stable_primitive_id",
    "stable_primitive_change_id",
    "stable_primitive_config_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
