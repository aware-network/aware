"""Latest stable-id rail for Meta runtime consumers.

Runtime should bind to the authored `.aware` contract here first. Generated
ontology helpers must catch up to this surface; they do not define it.
"""

from __future__ import annotations

from uuid import UUID, uuid5

from aware_code_ontology import stable_ids as _code_ontology_stable_ids
from aware_meta_ontology import stable_ids as _ontology_stable_ids


OCG_STABLE_ID_NAMESPACE = getattr(
    _ontology_stable_ids,
    "OCG_STABLE_ID_NAMESPACE",
    UUID("6d36d6d2-6b8a-4a5b-9c1c-5d2331c1f0c0"),
)


def ocg_stable_uuid(key: str) -> UUID:
    return uuid5(OCG_STABLE_ID_NAMESPACE, key)


# ---------------------------
# Graph-level
# ---------------------------


def stable_object_config_graph_id(*, fqn_prefix: str, language: str) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_config_graph_id", None)
    if fn is None:
        return ocg_stable_uuid(f"ocg:{fqn_prefix}:{language}")
    return fn(fqn_prefix=fqn_prefix, language=language)


def stable_object_config_graph_identity_id(*, key: str) -> UUID:
    ontology_fn = getattr(
        _ontology_stable_ids, "stable_object_config_graph_identity_id", None
    )
    if ontology_fn is not None:
        return ontology_fn(key=key)
    key_norm = (key or "").strip().casefold()
    if not key_norm:
        raise ValueError("key is required for stable ObjectConfigGraphIdentity IDs")
    return ocg_stable_uuid(f"object_config_graph_identity:{key_norm}")


def stable_object_config_graph_node_id(
    *, object_config_graph_id: UUID, type: str, node_key: str
) -> UUID:
    node_type_norm = (type or "").strip().casefold()
    node_key_norm = (node_key or "").strip().casefold()
    ontology_fn = getattr(
        _ontology_stable_ids, "stable_object_config_graph_node_id", None
    )
    if ontology_fn is not None:
        try:
            return ontology_fn(
                object_config_graph_id=object_config_graph_id,
                type=type,
                node_key=node_key,
            )
        except TypeError:
            pass
    if not node_type_norm:
        raise ValueError("type is required for stable ObjectConfigGraphNode IDs")
    if not node_key_norm:
        raise ValueError("node_key is required for stable ObjectConfigGraphNode IDs")
    return ocg_stable_uuid(
        f"ocg_node:{object_config_graph_id}:{node_type_norm}:{node_key_norm}"
    )


def stable_object_config_graph_binding_id(
    *, object_config_graph_id: UUID, target_object_config_graph_id: UUID
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_config_graph_binding_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"object_config_graph_binding:{object_config_graph_id}:{target_object_config_graph_id}"
        )
    return fn(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )


def stable_object_config_graph_binding_class_id(
    *,
    object_config_graph_binding_id: UUID,
    source_class_id: UUID,
    target_class_id: UUID,
    target_attribute_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_object_config_graph_binding_class_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            "object_config_graph_binding_class:"
            f"{object_config_graph_binding_id}:{source_class_id}:{target_class_id}:{target_attribute_id}"
        )
    return fn(
        object_config_graph_binding_id=object_config_graph_binding_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
    )


def stable_ocg_node_layout_id(
    *, object_config_graph_node_id: UUID, layout_kind: str
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_ocg_node_layout_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"ocg_node_layout:{object_config_graph_node_id}:{layout_kind}"
        )
    return fn(
        object_config_graph_node_id=object_config_graph_node_id, layout_kind=layout_kind
    )


def stable_object_projection_graph_identity_id(
    *,
    object_config_graph_identity_id: UUID,
    object_projection_graph_id: UUID,
) -> UUID:
    ontology_fn = getattr(
        _ontology_stable_ids, "stable_object_projection_graph_identity_id", None
    )
    if ontology_fn is not None:
        return ontology_fn(
            object_config_graph_identity_id=object_config_graph_identity_id,
            object_projection_graph_id=object_projection_graph_id,
        )
    return ocg_stable_uuid(
        f"object_projection_graph_identity:{object_config_graph_identity_id}:{object_projection_graph_id}"
    )


# ---------------------------
# Overlays (rename policies)
# ---------------------------


def stable_ocg_overlay_id(*, object_config_graph_id: UUID, language: str) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_ocg_overlay_id", None)
    if fn is None:
        lang = (language or "").strip()
        if not lang:
            raise ValueError("language is required for stable OCG overlay IDs")
        return ocg_stable_uuid(f"ocg_overlay:{object_config_graph_id}:{lang}")
    return fn(object_config_graph_id=object_config_graph_id, language=language)


def stable_ocg_overlay_entry_id(
    *, overlay_id: UUID, kind: str, target_id: UUID
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_ocg_overlay_entry_id", None)
    if fn is None:
        k = (kind or "").strip()
        if not k:
            raise ValueError("kind is required for stable OCG overlay entry IDs")
        return ocg_stable_uuid(f"ocg_overlay_entry:{overlay_id}:{k}:{target_id}")
    return fn(overlay_id=overlay_id, kind=kind, target_id=target_id)


# ---------------------------
# Meta entities (FQN-driven)
# ---------------------------


def stable_class_config_id(
    *, object_config_graph_node_id: UUID, class_fqn: str
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_config_id", None)
    class_fqn_norm = (class_fqn or "").strip().casefold()
    if fn is not None:
        try:
            return fn(
                object_config_graph_node_id=object_config_graph_node_id,
                class_fqn=class_fqn,
            )
        except TypeError:
            pass
    return ocg_stable_uuid(f"class:{object_config_graph_node_id}:{class_fqn_norm}")


def stable_enum_config_id(*, object_config_graph_node_id: UUID, enum_fqn: str) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_enum_config_id", None)
    enum_fqn_norm = (enum_fqn or "").strip().casefold()
    if fn is not None:
        try:
            return fn(
                object_config_graph_node_id=object_config_graph_node_id,
                enum_fqn=enum_fqn,
            )
        except TypeError:
            pass
    return ocg_stable_uuid(f"enum:{object_config_graph_node_id}:{enum_fqn_norm}")


def stable_enum_option_id(*, enum_config_id: UUID, value: str) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_enum_option_id", None)
    if fn is None:
        return ocg_stable_uuid(f"enum_option:{enum_config_id}:{value}")
    return fn(enum_config_id=enum_config_id, value=value)


def stable_function_config_id(
    *, owner_key: str, name: str, kind: str = "instance"
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_config_id", None)
    owner_key_norm = (owner_key or "").strip().casefold()
    name_norm = (name or "").strip().casefold()
    kind_norm = (kind or "instance").strip().casefold() or "instance"
    if fn is not None:
        try:
            return fn(owner_key=owner_key, name=name, kind=kind)
        except TypeError:
            pass
    return ocg_stable_uuid(f"function:{owner_key_norm}:{kind_norm}:{name_norm}")


def stable_class_config_function_config_id(
    *,
    class_config_id: UUID,
    function_config_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_config_function_config_id", None)
    if fn is not None:
        try:
            return fn(
                class_config_id=class_config_id, function_config_id=function_config_id
            )
        except TypeError:
            pass
    return ocg_stable_uuid(
        f"class_config_function_config:{class_config_id}:{function_config_id}"
    )


def stable_function_config_invocation_id(
    *,
    function_config_id: UUID | None = None,
    position: int,
    kind: str,
    target_function_config_id: UUID,
    relationship_fingerprint: str = "owner",
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_config_invocation_id", None)
    relationship_fp = (relationship_fingerprint or "").strip() or "owner"
    if fn is None:
        return ocg_stable_uuid(
            "function_invocation:"
            f"{function_config_id}:{position}:{kind}:{target_function_config_id}:{relationship_fp}"
        )
    try:
        return fn(
            function_config_id=function_config_id,
            position=position,
            kind=kind,
            target_function_config_id=target_function_config_id,
            relationship_fingerprint=relationship_fp,
        )
    except TypeError:
        return fn(
            position=position,
            kind=kind,
            target_function_config_id=target_function_config_id,
            relationship_fingerprint=relationship_fp,
        )


def stable_function_config_attribute_config_id(
    *,
    function_config_id: UUID,
    name: str,
    type: str = "input",
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_function_config_attribute_config_id", None
    )
    name_norm = (name or "").strip().casefold()
    type_norm = (type or "").strip().casefold() or "input"
    if fn is not None:
        try:
            return fn(function_config_id=function_config_id, name=name, type=type)
        except TypeError:
            pass
    return ocg_stable_uuid(
        f"function_config_attribute_config:{function_config_id}:{name_norm}:{type_norm}"
    )


def stable_function_impl_id(*, function_config_id: UUID) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_impl_id", None)
    if fn is None:
        return ocg_stable_uuid(f"function_impl:{function_config_id}")
    return fn(function_config_id=function_config_id)


def stable_function_impl_instruction_id(
    *,
    function_impl_id: UUID,
    sequence: int,
    type: str,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_impl_instruction_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction:{function_impl_id}:{sequence}:{type}"
        )
    return fn(function_impl_id=function_impl_id, sequence=sequence, type=type)


def stable_function_impl_instruction_require_id(
    *, function_impl_instruction_id: UUID
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_function_impl_instruction_require_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_require:{function_impl_instruction_id}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id)


def stable_function_impl_instruction_delete_id(
    *, function_impl_instruction_id: UUID
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_function_impl_instruction_delete_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_delete:{function_impl_instruction_id}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id)


def stable_function_impl_instruction_invoke_id(
    *, function_impl_instruction_id: UUID
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_function_impl_instruction_invoke_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_invoke:{function_impl_instruction_id}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id)


def stable_function_impl_instruction_require_operand_id(
    *,
    function_impl_instruction_require_id: UUID,
    position: int,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids,
        "stable_function_impl_instruction_require_operand_id",
        None,
    )
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_require_operand:{function_impl_instruction_require_id}:{position}"
        )
    return fn(
        function_impl_instruction_require_id=function_impl_instruction_require_id,
        position=position,
    )


def stable_function_impl_value_source_id(
    *,
    function_impl_instruction_id: UUID,
    key: str,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_impl_value_source_id", None)
    key_norm = (key or "").strip().casefold()
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_value_source:{function_impl_instruction_id}:{key_norm}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id, key=key)


def stable_function_impl_value_source_literal_primitive_id(
    *, function_impl_value_source_id: UUID
) -> UUID:
    fn = getattr(
        _ontology_stable_ids,
        "stable_function_impl_value_source_literal_primitive_id",
        None,
    )
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_value_source_literal_primitive:{function_impl_value_source_id}"
        )
    return fn(function_impl_value_source_id=function_impl_value_source_id)


def stable_function_impl_instruction_invoke_attribute_config_id(
    *,
    function_impl_instruction_invoke_id: UUID,
    attribute_config_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids,
        "stable_function_impl_instruction_invoke_attribute_config_id",
        None,
    )
    if fn is None:
        return ocg_stable_uuid(
            "function_impl_instruction_invoke_attribute_config:"
            f"{function_impl_instruction_invoke_id}:{attribute_config_id}"
        )
    return fn(
        function_impl_instruction_invoke_id=function_impl_instruction_invoke_id,
        attribute_config_id=attribute_config_id,
    )


def stable_function_impl_instruction_let_id(
    *, function_impl_instruction_id: UUID
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_impl_instruction_let_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_let:{function_impl_instruction_id}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id)


def stable_function_impl_instruction_set_id(
    *, function_impl_instruction_id: UUID
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_function_impl_instruction_set_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"function_impl_instruction_set:{function_impl_instruction_id}"
        )
    return fn(function_impl_instruction_id=function_impl_instruction_id)


def stable_attribute_id(*, owner_key: UUID, attribute_config_id: UUID) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_attribute_id", None)
    if fn is not None:
        try:
            return fn(owner_key=owner_key, attribute_config_id=attribute_config_id)
        except TypeError:
            pass
    return ocg_stable_uuid(f"attribute:{attribute_config_id}:{owner_key}")


def stable_class_instance_id(
    *,
    object_instance_graph_id: UUID,
    class_config_id: UUID,
    source_object_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_instance_id", None)
    if fn is not None:
        try:
            return fn(
                object_instance_graph_id=object_instance_graph_id,
                class_config_id=class_config_id,
                source_object_id=source_object_id,
            )
        except TypeError:
            pass
    return ocg_stable_uuid(
        f"class_instance:{object_instance_graph_id}:{class_config_id}:{source_object_id}"
    )


def stable_class_instance_identity_id(
    *,
    object_instance_graph_identity_id: UUID | None = None,
    class_instance_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_instance_identity_id", None)
    if fn is None:
        if object_instance_graph_identity_id is None:
            return ocg_stable_uuid(f"class_instance_identity:{class_instance_id}")
        return ocg_stable_uuid(
            f"class_instance_identity:{object_instance_graph_identity_id}:{class_instance_id}"
        )
    try:
        return fn(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_id=class_instance_id,
        )
    except TypeError:
        try:
            return fn(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                class_instance_identity_id=class_instance_id,
            )
        except TypeError:
            return fn(class_instance_identity_id=class_instance_id)


def stable_object_instance_graph_identity_id(
    *, object_projection_graph_identity_id: UUID, object_instance_graph_id: UUID
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_instance_graph_identity_id", None)
    if fn is not None:
        return fn(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
        )
    return ocg_stable_uuid(
        f"object_instance_graph_identity:{object_projection_graph_identity_id}:{object_instance_graph_id}"
    )


def stable_object_instance_graph_branch_id(
    *,
    object_instance_graph_identity_id: UUID | None = None,
    branch_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_instance_graph_branch_id", None)
    if fn is None:
        if object_instance_graph_identity_id is None:
            return ocg_stable_uuid(f"object_instance_graph_branch:{branch_id}")
        return ocg_stable_uuid(
            f"object_instance_graph_branch:{object_instance_graph_identity_id}:{branch_id}"
        )
    try:
        return fn(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            branch_id=branch_id,
        )
    except TypeError:
        return fn(branch_id=branch_id)


def stable_object_instance_graph_branch_relationship_id(
    *,
    object_instance_graph_branch_id: UUID | None = None,
    target_object_instance_graph_branch_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids,
        "stable_object_instance_graph_branch_relationship_id",
        None,
    )
    if fn is None:
        if object_instance_graph_branch_id is None:
            return ocg_stable_uuid(
                f"object_instance_graph_branch_relationship:{target_object_instance_graph_branch_id}"
            )
        return ocg_stable_uuid(
            "object_instance_graph_branch_relationship:"
            f"{object_instance_graph_branch_id}:{target_object_instance_graph_branch_id}"
        )
    try:
        return fn(
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            target_object_instance_graph_branch_id=target_object_instance_graph_branch_id,
        )
    except TypeError:
        return fn(
            target_object_instance_graph_branch_id=target_object_instance_graph_branch_id
        )


def stable_object_instance_graph_commit_id(
    *,
    object_instance_graph_identity_id: UUID | None = None,
    commit_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_instance_graph_commit_id", None)
    if fn is None:
        if object_instance_graph_identity_id is None:
            return ocg_stable_uuid(f"object_instance_graph_commit:{commit_id}")
        return ocg_stable_uuid(
            f"object_instance_graph_commit:{object_instance_graph_identity_id}:{commit_id}"
        )
    try:
        return fn(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        )
    except TypeError:
        return fn(commit_id=commit_id)


def stable_object_instance_graph_lane_id(
    *,
    object_instance_graph_branch_id: UUID | None = None,
    lane_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_object_instance_graph_lane_id", None)
    if fn is None:
        if object_instance_graph_branch_id is None:
            return ocg_stable_uuid(f"object_instance_graph_lane:{lane_id}")
        return ocg_stable_uuid(
            f"object_instance_graph_lane:{object_instance_graph_branch_id}:{lane_id}"
        )
    try:
        return fn(
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            lane_id=lane_id,
        )
    except TypeError:
        return fn(lane_id=lane_id)


def stable_class_config_attribute_config_id(
    *,
    class_config_id: UUID,
    attribute_config_id: UUID,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_config_attribute_config_id", None)
    if fn is not None:
        try:
            return fn(
                class_config_id=class_config_id, attribute_config_id=attribute_config_id
            )
        except TypeError:
            pass
    return ocg_stable_uuid(
        f"class_config_attribute_config:{class_config_id}:{attribute_config_id}"
    )


def stable_attribute_config_id(*, owner_key: str, name: str) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_attribute_config_id", None)
    owner_key_norm = (owner_key or "").strip().casefold()
    name_norm = (name or "").strip().casefold()
    if fn is not None:
        try:
            return fn(owner_key=owner_key, name=name)
        except TypeError:
            pass
    return ocg_stable_uuid(f"attribute:{owner_key_norm}:{name_norm}")


# ---------------------------
# Link entities (relationship/join rows)
# ---------------------------


def stable_join_id(
    *, join_kind: str, left_id: UUID, right_id: UUID, extra: str | None = None
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_join_id", None)
    if fn is None:
        suffix = f":{extra}" if extra else ""
        return ocg_stable_uuid(f"join:{join_kind}:{left_id}:{right_id}{suffix}")
    return fn(join_kind=join_kind, left_id=left_id, right_id=right_id, extra=extra)


# ---------------------------
# Relationships (ClassConfigRelationship rail)
# ---------------------------


def stable_class_relationship_id(
    *,
    source_class_id: UUID,
    target_class_id: UUID,
    relationship_key: str,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_config_relationship_id", None)
    relationship_key_norm = (relationship_key or "").strip().casefold()
    if fn is not None:
        try:
            return fn(
                class_config_id=source_class_id,
                target_class_config_id=target_class_id,
                relationship_key=relationship_key,
            )
        except TypeError:
            pass
    return ocg_stable_uuid(
        f"class_rel:{source_class_id}:{target_class_id}:{relationship_key_norm}"
    )


def stable_class_relationship_attribute_id(
    *,
    relationship_id: UUID,
    attribute_config_id: UUID,
    direction: str,
    role: str,
) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_class_relationship_attribute_id", None)
    if fn is None:
        return ocg_stable_uuid(
            f"class_rel_attr:{relationship_id}:{attribute_config_id}:{direction}:{role}"
        )
    return fn(
        relationship_id=relationship_id,
        attribute_config_id=attribute_config_id,
        direction=direction,
        role=role,
    )


def stable_class_relationship_association_edge_id(
    *,
    relationship_id: UUID,
    association_class_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_class_relationship_association_edge_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"class_rel_assoc:{relationship_id}:{association_class_id}"
        )
    return fn(
        relationship_id=relationship_id, association_class_id=association_class_id
    )


# ---------------------------
# Cross-OCG relationship binding rail
# ---------------------------


def stable_object_config_graph_relationship_id(
    *,
    object_config_graph_id: UUID,
    target_object_config_graph_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_object_config_graph_relationship_id", None
    )
    if fn is None:
        return stable_join_id(
            join_kind="ocg_relationship",
            left_id=object_config_graph_id,
            right_id=target_object_config_graph_id,
        )
    try:
        return fn(
            object_config_graph_id=object_config_graph_id,
            target_object_config_graph_id=target_object_config_graph_id,
        )
    except TypeError:
        return stable_join_id(
            join_kind="ocg_relationship",
            left_id=object_config_graph_id,
            right_id=target_object_config_graph_id,
        )


def stable_object_config_graph_relationship_class_id(
    *,
    object_config_graph_relationship_id: UUID,
    class_config_id: UUID,
) -> UUID:
    fn = getattr(
        _ontology_stable_ids, "stable_object_config_graph_relationship_class_id", None
    )
    if fn is None:
        return stable_join_id(
            join_kind="ocg_relationship_class",
            left_id=object_config_graph_relationship_id,
            right_id=class_config_id,
        )
    try:
        return fn(
            object_config_graph_relationship_id=object_config_graph_relationship_id,
            class_config_id=class_config_id,
        )
    except TypeError:
        return stable_join_id(
            join_kind="ocg_relationship_class",
            left_id=object_config_graph_relationship_id,
            right_id=class_config_id,
        )


# ---------------------------
# Primitive/type-descriptor rail
# ---------------------------


def stable_code_primitive_type_id(*, signature: str) -> UUID:
    fn = getattr(_code_ontology_stable_ids, "stable_code_primitive_type_id", None)
    if fn is None:
        return ocg_stable_uuid(f"code_primitive_type:{signature}")
    return fn(signature=signature)


def stable_code_primitive_type_element_type_id(
    *,
    code_primitive_type_id: UUID,
    position: int,
) -> UUID:
    fn = getattr(
        _code_ontology_stable_ids, "stable_code_primitive_type_element_type_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"code_primitive_type_element_type:{code_primitive_type_id}:{position}"
        )
    return fn(code_primitive_type_id=code_primitive_type_id, position=position)


def stable_code_primitive_type_union_type_id(
    *,
    code_primitive_type_id: UUID,
    position: int,
) -> UUID:
    fn = getattr(
        _code_ontology_stable_ids, "stable_code_primitive_type_union_type_id", None
    )
    if fn is None:
        return ocg_stable_uuid(
            f"code_primitive_type_union_type:{code_primitive_type_id}:{position}"
        )
    return fn(code_primitive_type_id=code_primitive_type_id, position=position)


def stable_primitive_config_id(*, primitive_type_id: UUID) -> UUID:
    fn = getattr(_ontology_stable_ids, "stable_primitive_config_id", None)
    if fn is None:
        return ocg_stable_uuid(f"primitive_config:{primitive_type_id}")
    return fn(primitive_type_id=primitive_type_id)


def stable_attribute_type_descriptor_id(
    *,
    kind: str,
    collection_kind: str | None,
    entity_id: UUID | None,
    child_links_fingerprint: str,
) -> UUID:
    return _ontology_stable_ids.stable_attribute_type_descriptor_id(
        kind=kind,
        collection_kind=collection_kind,
        entity_id=entity_id,
        child_links_fingerprint=child_links_fingerprint,
    )


def stable_attribute_type_descriptor_link_id(
    *,
    attribute_type_descriptor_id: UUID,
    child_id: UUID,
    role: str,
    position: int,
) -> UUID:
    return _ontology_stable_ids.stable_attribute_type_descriptor_link_id(
        attribute_type_descriptor_id=attribute_type_descriptor_id,
        child_id=child_id,
        role=role,
        position=position,
    )


__all__ = [
    "OCG_STABLE_ID_NAMESPACE",
    "ocg_stable_uuid",
    "stable_object_config_graph_id",
    "stable_object_config_graph_node_id",
    "stable_ocg_node_layout_id",
    "stable_ocg_overlay_id",
    "stable_ocg_overlay_entry_id",
    "stable_class_config_id",
    "stable_enum_config_id",
    "stable_enum_option_id",
    "stable_function_config_id",
    "stable_function_config_attribute_config_id",
    "stable_function_config_invocation_id",
    "stable_attribute_id",
    "stable_class_instance_id",
    "stable_class_config_attribute_config_id",
    "stable_class_instance_identity_id",
    "stable_function_impl_id",
    "stable_function_impl_instruction_id",
    "stable_function_impl_instruction_invoke_id",
    "stable_function_impl_instruction_invoke_attribute_config_id",
    "stable_function_impl_instruction_let_id",
    "stable_function_impl_instruction_delete_id",
    "stable_function_impl_instruction_require_id",
    "stable_function_impl_instruction_require_operand_id",
    "stable_function_impl_instruction_set_id",
    "stable_function_impl_value_source_id",
    "stable_function_impl_value_source_literal_primitive_id",
    "stable_attribute_config_id",
    "stable_object_instance_graph_identity_id",
    "stable_object_instance_graph_branch_id",
    "stable_object_instance_graph_branch_relationship_id",
    "stable_object_instance_graph_commit_id",
    "stable_object_instance_graph_lane_id",
    "stable_join_id",
    "stable_class_relationship_id",
    "stable_class_relationship_attribute_id",
    "stable_class_relationship_association_edge_id",
    "stable_object_config_graph_relationship_id",
    "stable_object_config_graph_relationship_class_id",
    "stable_code_primitive_type_id",
    "stable_code_primitive_type_element_type_id",
    "stable_code_primitive_type_union_type_id",
    "stable_primitive_config_id",
    "stable_attribute_type_descriptor_id",
    "stable_attribute_type_descriptor_link_id",
]
