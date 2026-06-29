from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
from aware_meta_ontology.class_.class_config import ClassConfig

from aware_code.language_service.features.navigation_capabilities.contracts import (
    AttributeDefinitionTargetResolver,
    ClassDefinitionTargetResolver,
    CursorInRangeMatcher,
    NodeTextReader,
    ProjectionTargetResolver,
)
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot

from ..diagnostics_capabilities.projection import build_projection_lookup, match_projection_symbol


@dataclass(frozen=True, slots=True)
class _ProjectionNavigationCatalog:
    classes_by_name: dict[str, ClassConfig]
    relationship_targets_by_parent: dict[str, dict[str, str]]


def collect_api_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    projection_targets_by_symbol: ProjectionTargetResolver,
    class_definition_target: ClassDefinitionTargetResolver,
    attribute_definition_target: AttributeDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if b"api" not in document_bytes:
        return []

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return []

    projection_lookup = build_projection_lookup(snapshot=snapshot, code=snapshot.codes_by_uri[uri])
    catalog_cache: dict[tuple[str, str], _ProjectionNavigationCatalog] = {}
    cursor = max(int(byte_offset), 0)
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type != "api_def":
            continue
        if not cursor_in_range(byte_offset=cursor, start=node.start_byte, end=node.end_byte):
            continue

        for api_child in _iter_api_children(node=node):
            if api_child.type != "api_graph_def":
                continue
            for graph_child in _iter_api_graph_children(node=api_child):
                if graph_child.type != "api_graph_projection_def":
                    continue

                projection_node = graph_child.child_by_field_name("projection")
                projection_ref = node_text(projection_node).strip()
                if projection_node is not None and cursor_in_range(
                    byte_offset=cursor,
                    start=projection_node.start_byte,
                    end=projection_node.end_byte,
                ):
                    if not projection_ref:
                        return []
                    return projection_targets_by_symbol(uri=uri, symbol=projection_ref)
                if not projection_ref:
                    continue

                matches = match_projection_symbol(symbol=projection_ref, lookup=projection_lookup)
                if not matches:
                    continue
                resolved_uri, _resolved_pkg, resolved_projection = matches[0]
                resolved_projection_name = _projection_lookup_key(resolved_projection)
                cache_key = (resolved_uri, resolved_projection_name)
                projection_catalog = catalog_cache.get(cache_key)
                if projection_catalog is None:
                    projection_catalog = _build_projection_navigation_catalog(
                        snapshot=snapshot,
                        projection_uri=resolved_uri,
                        projection=resolved_projection,
                    )
                    catalog_cache[cache_key] = projection_catalog

                for contract in _iter_api_graph_projection_children(node=graph_child):
                    if contract.type != "api_graph_projection_contract_def":
                        continue
                    anchor = contract.child_by_field_name("anchor")
                    if anchor is None or anchor.type != "api_contract_anchor":
                        continue

                    parent_node = anchor.child_by_field_name("parent")
                    relationship_node = anchor.child_by_field_name("relationship")
                    key_node = anchor.child_by_field_name("key")
                    parent_name = _symbol_key(node_text(parent_node))
                    relationship_name = _symbol_key(node_text(relationship_node))
                    key_name = _symbol_key(node_text(key_node))

                    if (
                        parent_node is not None
                        and cursor_in_range(
                            byte_offset=cursor,
                            start=parent_node.start_byte,
                            end=parent_node.end_byte,
                        )
                        and parent_name
                    ):
                        parent_class = projection_catalog.classes_by_name.get(parent_name)
                        if parent_class is None:
                            return []
                        target = class_definition_target(parent_class)
                        return [target] if target is not None else []

                    if (
                        relationship_node is not None
                        and cursor_in_range(
                            byte_offset=cursor,
                            start=relationship_node.start_byte,
                            end=relationship_node.end_byte,
                        )
                        and parent_name
                        and relationship_name
                    ):
                        parent_class = projection_catalog.classes_by_name.get(parent_name)
                        if parent_class is None:
                            return []
                        relationship_attr = _class_attribute(parent_class=parent_class, attribute_name=relationship_name)
                        if relationship_attr is None:
                            return []
                        target = attribute_definition_target(relationship_attr)
                        return [target] if target is not None else []

                    if (
                        key_node is not None
                        and cursor_in_range(
                            byte_offset=cursor,
                            start=key_node.start_byte,
                            end=key_node.end_byte,
                        )
                        and parent_name
                        and relationship_name
                        and key_name
                    ):
                        relationship_targets = projection_catalog.relationship_targets_by_parent.get(parent_name, {})
                        target_class_name = relationship_targets.get(relationship_name)
                        if not target_class_name:
                            return []
                        target_class = projection_catalog.classes_by_name.get(target_class_name)
                        if target_class is None:
                            return []
                        key_attr = _class_attribute(parent_class=target_class, attribute_name=key_name)
                        if key_attr is None:
                            return []
                        target = attribute_definition_target(key_attr)
                        return [target] if target is not None else []

    return []


def _build_projection_navigation_catalog(
    *,
    snapshot: WorkspaceSnapshot,
    projection_uri: str,
    projection: CodeSectionProjection,
) -> _ProjectionNavigationCatalog:
    code = snapshot.codes_by_uri.get(projection_uri)
    if code is None:
        return _ProjectionNavigationCatalog(classes_by_name={}, relationship_targets_by_parent={})
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    queue: list[ClassConfig] = []
    relationship_targets_by_parent: dict[str, dict[str, str]] = {}
    seen_ids: set[str] = set()

    root_type_ref = (projection.root_type_ref or "").strip()
    if root_type_ref:
        resolved = scope.try_resolve_class_with_fqn(root_type_ref)
        if resolved is not None:
            _fqn, class_cfg = resolved
            queue.append(class_cfg)

    for edge in projection.projection_edges:
        edge_type_ref = (edge.type_ref or "").strip()
        if not edge_type_ref:
            continue
        resolved = scope.try_resolve_class_with_fqn(edge_type_ref)
        if resolved is None:
            continue
        _fqn, class_cfg = resolved
        queue.append(class_cfg)
        edge_member = (edge.member or "").strip()
        target_segment = edge.target_segment
        if not edge_member or target_segment is None:
            continue
        if target_segment.byte_start is None or target_segment.byte_end is None:
            continue
        if target_segment.byte_end <= target_segment.byte_start:
            continue
        inline_text = code.content_part_text.inline_text
        if not isinstance(inline_text, str):
            continue
        target_ref = inline_text[target_segment.byte_start:target_segment.byte_end].strip().strip("'\"")
        if not target_ref:
            continue
        resolved_target = scope.try_resolve_class_with_fqn(target_ref)
        if resolved_target is None:
            continue
        _target_fqn, target_class_cfg = resolved_target
        queue.append(target_class_cfg)
        class_relationship_targets = relationship_targets_by_parent.setdefault(class_cfg.name, {})
        class_relationship_targets[edge_member] = target_class_cfg.name

    classes_by_name: dict[str, ClassConfig] = {}
    while queue:
        class_cfg = queue.pop()
        class_id = str(class_cfg.id)
        if class_id in seen_ids:
            continue
        seen_ids.add(class_id)
        classes_by_name[class_cfg.name] = class_cfg

    return _ProjectionNavigationCatalog(
        classes_by_name=classes_by_name,
        relationship_targets_by_parent=relationship_targets_by_parent,
    )


def _class_attribute(*, parent_class: ClassConfig, attribute_name: str) -> CodeSectionAttribute | None:
    class_section = parent_class.code_section_class
    if class_section is None:
        return None
    for attr in class_section.code_section_attributes:
        if (attr.name or "").strip() == attribute_name:
            return attr
    return None


def _projection_lookup_key(projection: CodeSectionProjection) -> str:
    projection_name = (projection.projection_name or "").strip()
    if projection_name:
        return projection_name
    return (projection.name or "").strip()


def _iter_api_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _iter_api_graph_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_graph_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _iter_api_graph_projection_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_graph_projection_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()
