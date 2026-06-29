from uuid import UUID

# Code Ontology
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror

# Meta Ontology
from aware_meta.fqn_resolver import FqnResolver, NamespacePath
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror import (
    ObjectConfigGraphMirror,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror_enums import (
    ObjectConfigGraphMirrorTargetKind,
)


def _build_object_config_graph_mirror(
    *,
    namespace: str,
    values: dict[str, object],
) -> ObjectConfigGraphMirror:
    model_fields = getattr(ObjectConfigGraphMirror, "model_fields", {})
    if "namespace" in model_fields:
        return ObjectConfigGraphMirror(**values, namespace=namespace)
    mirror = ObjectConfigGraphMirror.model_construct(**values)
    object.__setattr__(mirror, "namespace", namespace)
    return mirror


def build_object_config_graph_mirrors(
    object_config_graph_id: UUID,
    mirror_sections: list[CodeSectionMirror],
    rel_path_by_code_id: dict[UUID, str],
    fqn_resolver: FqnResolver,
    namespace_by_code_id: dict[UUID, NamespacePath],
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> list[ObjectConfigGraphMirror]:
    """
    Build ObjectConfigGraphMirrors from the given mirror sections.

    Args:
        object_config_graph_id: Owning ObjectConfigGraph id for the mirrors
        mirror_sections: List of CodeSectionMirror sections
        rel_path_by_code_id: Dictionary of relative paths by code ID
        fqn_resolver: FqnResolver to use for resolving FQNs
        namespace_by_code_id: Namespace by code ID
        external_graphs: List of external ObjectConfigGraphs
    Returns:
        List of ObjectConfigGraphMirrors
    """
    if mirror_sections and not external_graphs:
        raise ValueError("Mirror statements require external graphs for resolution")

    # Map class/enum ids to their owning graphs (external only).
    class_graph_by_id: dict[UUID, ObjectConfigGraph] = {}
    enum_graph_by_id: dict[UUID, ObjectConfigGraph] = {}
    for g in external_graphs or []:
        for node in g.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                class_graph_by_id[node.class_config.id] = g
            elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
                enum_graph_by_id[node.enum_config.id] = g

    mirrors: list[ObjectConfigGraphMirror] = []
    for mirror in mirror_sections:
        target = (mirror.target_text or "").strip()
        if not target:
            raise ValueError("Mirror statement missing target text")

        rel_path = rel_path_by_code_id.get(mirror.code_section.code_id)
        if not rel_path:
            raise ValueError(f"Mirror statement missing relative path for code_id={mirror.code_section.code_id}")
        segment = mirror.code_section.content_part_text_segment
        source_position = None
        if segment is not None and segment.byte_start is not None:
            source_position = int(segment.byte_start)

        mirror_scope = fqn_resolver.scope_for_code_id(mirror.code_section.code_id)
        class_hit = mirror_scope.try_resolve_class_with_fqn(target)
        enum_hit = mirror_scope.try_resolve_enum_with_fqn(target)
        if class_hit and enum_hit:
            raise ValueError(f"Mirror target is ambiguous (class+enum): {target}")

        if class_hit:
            _target_fqn, class_config = class_hit
            target_ns = namespace_by_code_id.get(mirror.code_section.code_id)
            if target_ns is None:
                raise ValueError(
                    f"Mirror target namespace not found for code_id={mirror.code_section.code_id} ({target})"
                )
            source_graph = class_graph_by_id.get(class_config.id)
            if source_graph is None:
                raise ValueError(f"Mirror source graph not found for class_config_id={class_config.id} ({target})")
            mirrors.append(
                _build_object_config_graph_mirror(
                    namespace=target_ns.namespace,
                    values={
                        "code_section_mirror": mirror,
                        "object_config_graph_id": object_config_graph_id,
                        "source_object_config_graph_id": source_graph.id,
                        "code_section_mirror_id": mirror.id,
                        "class_config": class_config,
                        "class_config_id": class_config.id,
                        "enum_config": None,
                        "fqn_prefix": target_ns.package,
                        "target_text": target,
                        "target_kind": ObjectConfigGraphMirrorTargetKind.class_,
                        "layout_kind": "aware",
                        "relative_path": rel_path,
                        "source_position": source_position,
                    },
                )
            )
        elif enum_hit:
            _target_fqn, enum_config = enum_hit
            target_ns = namespace_by_code_id.get(mirror.code_section.code_id)
            if target_ns is None:
                raise ValueError(
                    f"Mirror target namespace not found for code_id={mirror.code_section.code_id} ({target})"
                )
            source_graph = enum_graph_by_id.get(enum_config.id)
            if source_graph is None:
                raise ValueError(f"Mirror source graph not found for enum_config_id={enum_config.id} ({target})")
            mirrors.append(
                _build_object_config_graph_mirror(
                    namespace=target_ns.namespace,
                    values={
                        "code_section_mirror": mirror,
                        "object_config_graph_id": object_config_graph_id,
                        "source_object_config_graph_id": source_graph.id,
                        "code_section_mirror_id": mirror.id,
                        "class_config": None,
                        "enum_config": enum_config,
                        "enum_config_id": enum_config.id,
                        "fqn_prefix": target_ns.package,
                        "target_text": target,
                        "target_kind": ObjectConfigGraphMirrorTargetKind.enum,
                        "layout_kind": "aware",
                        "relative_path": rel_path,
                        "source_position": source_position,
                    },
                )
            )
        else:
            raise ValueError(f"Mirror target not found: {target}")

    return mirrors
