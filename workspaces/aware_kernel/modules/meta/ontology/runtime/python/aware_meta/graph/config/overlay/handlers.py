from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta.graph.config.model_bootstrap import get_node_function_config

from aware_meta.graph.config.overlay.payload import (
    ObjectConfigGraphOverlayPayload,
    ClassOverlayPayload,
    EnumOverlayPayload,
    EnumOptionOverlayPayload,
    AttributeOverlayPayload,
    FunctionOverlayPayload,
)


def build_object_config_graph_overlay_payload(
    object_config_graph_overlay: ObjectConfigGraphOverlay,
) -> ObjectConfigGraphOverlayPayload:
    """Build overlay payloads from meta overlays."""
    payload_language = str(object_config_graph_overlay.language.value).lower()
    payload = ObjectConfigGraphOverlayPayload(language=payload_language)

    # Classes
    for cls_overlay in object_config_graph_overlay.class_config_overlays:
        if not cls_overlay.class_config_id:
            continue
        key = str(cls_overlay.class_config_id)
        payload.class_overlays[key] = ClassOverlayPayload(
            rendered_name=cls_overlay.rendered_name,
            lang_flags=cls_overlay.lang_flags,
        )

    # Enums
    for enum_overlay in object_config_graph_overlay.enum_config_overlays:
        if not enum_overlay.enum_config_id:
            continue
        key = str(enum_overlay.enum_config_id)
        payload.enum_overlays[key] = EnumOverlayPayload(
            rendered_name=enum_overlay.rendered_name,
        )

    # Enum options
    for opt_overlay in object_config_graph_overlay.enum_option_overlays:
        if not opt_overlay.enum_option_id:
            continue
        key = str(opt_overlay.enum_option_id)
        payload.enum_option_overlays[key] = EnumOptionOverlayPayload(
            rendered_name=opt_overlay.rendered_name,
            wire_name=opt_overlay.wire_name,
        )

    # Attributes
    for attr_overlay in object_config_graph_overlay.attribute_config_overlays:
        if not attr_overlay.attribute_config_id:
            continue
        key = str(attr_overlay.attribute_config_id)
        payload.attribute_overlays[key] = AttributeOverlayPayload(
            rendered_name=attr_overlay.rendered_name,
            wire_name=attr_overlay.wire_name,
        )

    # Functions
    for fn_overlay in object_config_graph_overlay.function_config_overlays:
        if not fn_overlay.function_config_id:
            continue
        key = str(fn_overlay.function_config_id)
        payload.function_overlays[key] = FunctionOverlayPayload(
            rendered_name=fn_overlay.rendered_name,
            lang_flags=fn_overlay.lang_flags,
        )

    return payload


def hydrate_object_config_graph_overlays(
    ocg: ObjectConfigGraph,
    *,
    overlays: list[ObjectConfigGraphOverlay] | None = None,
) -> None:
    """
    Attach overlay edge targets by ID so overlay descriptors can resolve names
    after graph reloads (relationships are excluded from serialization).
    """
    overlays = overlays if overlays is not None else ocg.object_config_graph_overlays
    if not overlays:
        return

    class_by_id: dict[UUID, ClassConfig] = {}
    function_by_id: dict[UUID, FunctionConfig] = {}
    enum_by_id: dict[UUID, EnumConfig] = {}
    attribute_by_id: dict[UUID, AttributeConfig] = {}
    enum_option_by_id: dict[UUID, EnumOption] = {}

    for node in ocg.object_config_graph_nodes:
        if node.class_config is not None:
            class_by_id[node.class_config.id] = node.class_config
        node_function_config = get_node_function_config(node)
        if node_function_config is not None:
            function_by_id[node_function_config.id] = node_function_config
        if node.enum_config is not None:
            enum_by_id[node.enum_config.id] = node.enum_config

    for enum_cfg in enum_by_id.values():
        for opt in enum_cfg.enum_options or []:
            enum_option_by_id[opt.id] = opt

    for cls in class_by_id.values():
        for link in cls.class_config_attribute_configs:
            attr = link.attribute_config
            if attr is not None:
                attribute_by_id[attr.id] = attr
        for fn_link in cls.class_config_function_configs or []:
            fn = fn_link.function_config
            if fn is None:
                continue
            for fn_attr_edge in fn.function_config_attribute_configs or []:
                attr = fn_attr_edge.attribute_config
                if attr is not None:
                    attribute_by_id[attr.id] = attr

    for fn in function_by_id.values():
        for fn_attr_edge in fn.function_config_attribute_configs or []:
            attr = fn_attr_edge.attribute_config
            if attr is not None and attr.id not in attribute_by_id:
                attribute_by_id[attr.id] = attr

    for overlay in overlays:
        for edge in overlay.class_config_overlays:
            if edge.class_config is None and edge.class_config_id in class_by_id:
                edge.class_config = class_by_id[edge.class_config_id]
        for edge in overlay.function_config_overlays:
            if (
                edge.function_config is None
                and edge.function_config_id in function_by_id
            ):
                edge.function_config = function_by_id[edge.function_config_id]
        for edge in overlay.enum_config_overlays:
            if edge.enum_config is None and edge.enum_config_id in enum_by_id:
                edge.enum_config = enum_by_id[edge.enum_config_id]
        for edge in overlay.enum_option_overlays:
            if edge.enum_option is None and edge.enum_option_id in enum_option_by_id:
                edge.enum_option = enum_option_by_id[edge.enum_option_id]
        for edge in overlay.attribute_config_overlays:
            if (
                edge.attribute_config is None
                and edge.attribute_config_id in attribute_by_id
            ):
                edge.attribute_config = attribute_by_id[edge.attribute_config_id]
