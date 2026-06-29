from __future__ import annotations

from dataclasses import dataclass
from tree_sitter import Node

from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_workspace.compiler.workspace import WorkspaceSnapshot

from aware_code.language_service.position import ByteRange

from .projection import (
    ProjectionAddDiagnostic,
    ProjectionLookup,
    ProjectionSuggestFn,
    match_projection_symbol,
)


@dataclass(frozen=True, slots=True)
class _ProjectionCatalog:
    class_truth_by_name: dict[str, _ProjectionOwnedClassTruth]
    relationship_targets_by_parent: dict[str, dict[str, str]]


@dataclass(frozen=True, slots=True)
class _ProjectionOwnedClassTruth:
    class_fqn: str
    attributes: frozenset[str]
    identity_key_attributes: frozenset[str]


def collect_api_diagnostics(
    *,
    projection_root: Node | None,
    document_bytes: bytes,
    snapshot: WorkspaceSnapshot,
    lookup: ProjectionLookup,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
    enabled_groups: frozenset[str] | None = None,
) -> None:
    if projection_root is None:
        return
    if b"api" not in document_bytes:
        return

    def _is_enabled(group: str) -> bool:
        return enabled_groups is None or group in enabled_groups

    projection_name_candidates: list[str] = []
    for _uri, _pkg, projection in lookup.projection_index:
        name = (projection.name or "").strip()
        projection_name = (projection.projection_name or "").strip()
        if name:
            projection_name_candidates.append(name)
        if projection_name:
            projection_name_candidates.append(projection_name)

    projection_catalog_cache: dict[tuple[str, str], _ProjectionCatalog] = {}
    seen_api_names: set[str] = set()

    api_queue: list[Node] = [projection_root]
    while api_queue:
        node = api_queue.pop()
        api_queue.extend(node.children)
        if node.type != "api_def":
            continue

        api_name_node = node.child_by_field_name("name")
        api_name = _symbol_key(_tree_node_text(api_name_node))
        if api_name_node is None or not api_name or api_name_node.end_byte <= api_name_node.start_byte:
            continue

        if _is_enabled("api"):
            api_name_range = _node_range(api_name_node)
            if api_name in seen_api_names:
                add(
                    rng=api_name_range,
                    message=f"Duplicate api declaration {api_name!r}.",
                    code="aware.api.api_duplicate",
                )
            else:
                seen_api_names.add(api_name)

        if not _is_enabled("projection"):
            continue

        for api_child in _iter_api_children(node=node):
            if api_child.type != "api_graph_def":
                continue
            for graph_child in _iter_api_graph_children(node=api_child):
                if graph_child.type != "api_graph_projection_def":
                    continue
                _collect_api_graph_projection_diagnostics(
                    api_name=api_name,
                    graph_projection_node=graph_child,
                    projection_name_candidates=projection_name_candidates,
                    projection_catalog_cache=projection_catalog_cache,
                    snapshot=snapshot,
                    lookup=lookup,
                    add=add,
                    suggest=suggest,
                )


def _collect_api_graph_projection_diagnostics(
    *,
    api_name: str,
    graph_projection_node: Node,
    projection_name_candidates: list[str],
    projection_catalog_cache: dict[tuple[str, str], _ProjectionCatalog],
    snapshot: WorkspaceSnapshot,
    lookup: ProjectionLookup,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
) -> None:
    projection_node = graph_projection_node.child_by_field_name("projection")
    projection_ref = _tree_node_text(projection_node).strip()
    if projection_node is None or not projection_ref or projection_node.end_byte <= projection_node.start_byte:
        return

    matches = match_projection_symbol(symbol=projection_ref, lookup=lookup)
    if not matches:
        add(
            rng=_node_range(projection_node),
            message=f"Projection not found for api graph binding: {projection_ref}",
            code="aware.api.projection_not_found",
            data={
                "suggestions": suggest(
                    projection_ref,
                    sorted(set(projection_name_candidates)),
                )
            },
        )
        return

    match_candidates = list(matches)
    packages = {pkg for _uri, pkg, _proj in match_candidates if isinstance(pkg, str) and pkg}
    if "." not in projection_ref and lookup.local_pkg is not None and lookup.local_pkg in packages:
        packages = {lookup.local_pkg}
    if len(packages) > 1:
        add(
            rng=_node_range(projection_node),
            message=(
                f"Ambiguous api projection {projection_ref!r}; "
                "qualify with package (e.g. `aware_home.home.Home`)."
            ),
            code="aware.api.projection_ambiguous",
            data={"matches": sorted(packages)},
            severity=2,
        )

    resolved_uri, _resolved_pkg, resolved_projection = match_candidates[0]
    resolved_projection_name = _projection_lookup_key(resolved_projection)
    cache_key = (resolved_uri, resolved_projection_name)
    projection_catalog = projection_catalog_cache.get(cache_key)
    if projection_catalog is None:
        projection_catalog = _build_projection_catalog(
            snapshot=snapshot,
            projection_uri=resolved_uri,
            projection=resolved_projection,
        )
        projection_catalog_cache[cache_key] = projection_catalog

    seen_contract_bindings: set[tuple[str, str, str, str]] = set()
    contract_count = 0
    for contract_node in _iter_api_graph_projection_children(node=graph_projection_node):
        if contract_node.type != "api_graph_projection_contract_def":
            continue
        contract_count += 1

        class_node = contract_node.child_by_field_name("class")
        class_ref = _tree_node_text(class_node).strip()
        anchor_node = contract_node.child_by_field_name("anchor")
        if anchor_node is None or anchor_node.type != "api_contract_anchor":
            continue

        parent_node = anchor_node.child_by_field_name("parent")
        relationship_node = anchor_node.child_by_field_name("relationship")
        key_node = anchor_node.child_by_field_name("key")
        parent_name = _symbol_key(_tree_node_text(parent_node))
        relationship_name = _symbol_key(_tree_node_text(relationship_node))
        key_name = _symbol_key(_tree_node_text(key_node))

        if class_ref and parent_name and relationship_name and key_name:
            contract_binding = (
                class_ref.casefold(),
                parent_name.casefold(),
                relationship_name.casefold(),
                key_name.casefold(),
            )
            if contract_binding in seen_contract_bindings:
                duplicate_node = class_node or anchor_node
                add(
                    rng=_node_range(duplicate_node),
                    message=(
                        f"Duplicate api contract binding for class {class_ref!r} "
                        f"and anchor {parent_name}::{relationship_name}::{key_name} in api {api_name!r}."
                    ),
                    code="aware.api.contract_duplicate",
                )
            else:
                seen_contract_bindings.add(contract_binding)

        if parent_node is None or not parent_name:
            continue

        class_truth = projection_catalog.class_truth_by_name.get(parent_name)
        if class_truth is None:
            add(
                rng=_node_range(parent_node),
                message=(
                    f"API declaration {api_name!r} references unknown parent class "
                    f"{parent_name!r} for projection {resolved_projection_name!r}."
                ),
                code="aware.api.anchor_parent_not_found",
                data={
                    "suggestions": suggest(
                        parent_name,
                        sorted(projection_catalog.class_truth_by_name.keys()),
                    )
                },
            )
            continue

        if relationship_node is None or not relationship_name:
            continue
        if relationship_name not in class_truth.attributes:
            add(
                rng=_node_range(relationship_node),
                message=(
                    f"API declaration {api_name!r} references unknown relationship "
                    f"{parent_name}::{relationship_name}."
                ),
                code="aware.api.anchor_relationship_not_found",
                data={
                    "suggestions": suggest(
                        relationship_name,
                        sorted(class_truth.attributes),
                    )
                },
            )
            continue

        relationship_targets = projection_catalog.relationship_targets_by_parent.get(parent_name, {})
        target_class_name = relationship_targets.get(relationship_name)
        if not target_class_name:
            add(
                rng=_node_range(relationship_node),
                message=(
                    f"API declaration {api_name!r} cannot resolve relationship target "
                    f"for anchor {parent_name}::{relationship_name}::{key_name}."
                ),
                code="aware.api.anchor_target_unresolved",
            )
            continue

        target_truth = projection_catalog.class_truth_by_name.get(target_class_name)
        if target_truth is None:
            add(
                rng=_node_range(relationship_node),
                message=(
                    f"API declaration {api_name!r} target class {target_class_name!r} "
                    f"is not owned by projection {resolved_projection_name!r}."
                ),
                code="aware.api.anchor_target_not_found",
            )
            continue

        if key_node is None or not key_name:
            continue
        if key_name not in target_truth.identity_key_attributes:
            add(
                rng=_node_range(key_node),
                message=(
                    f"API declaration {api_name!r} key attribute {key_name!r} "
                    f"is not an identity key on class {target_class_name!r}."
                ),
                code="aware.api.anchor_key_not_identity",
                data={
                    "suggestions": suggest(
                        key_name,
                        sorted(target_truth.identity_key_attributes),
                    )
                },
            )

    if contract_count == 0:
        add(
            rng=_node_range(graph_projection_node),
            message=f"API declaration {api_name!r} must include at least one contract.",
            code="aware.api.contract_missing",
        )


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


def _build_projection_catalog(
    *,
    snapshot: WorkspaceSnapshot,
    projection_uri: str,
    projection: CodeSectionProjection,
) -> _ProjectionCatalog:
    code = snapshot.codes_by_uri.get(projection_uri)
    if code is None:
        return _ProjectionCatalog(class_truth_by_name={}, relationship_targets_by_parent={})
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
        parent_targets = relationship_targets_by_parent.setdefault(class_cfg.name, {})
        parent_targets[edge_member] = target_class_cfg.name

    class_truth_by_name: dict[str, _ProjectionOwnedClassTruth] = {}
    while queue:
        class_cfg = queue.pop()
        class_id = str(class_cfg.id)
        if class_id in seen_ids:
            continue
        seen_ids.add(class_id)

        class_truth = _class_truth(class_cfg=class_cfg)
        class_truth_by_name[class_cfg.name] = class_truth

        for relationship in class_cfg.class_config_relationships:
            target_class_cfg = relationship.target_class_config
            if target_class_cfg is not None:
                queue.append(target_class_cfg)

    return _ProjectionCatalog(
        class_truth_by_name=class_truth_by_name,
        relationship_targets_by_parent=relationship_targets_by_parent,
    )


def _class_truth(*, class_cfg: ClassConfig) -> _ProjectionOwnedClassTruth:
    class_fqn = ""
    attributes: set[str] = set()
    class_section = class_cfg.code_section_class
    if class_section is not None:
        for attr in class_section.code_section_attributes:
            attr_name = (attr.name or "").strip()
            if attr_name:
                attributes.add(attr_name)
        class_fqn = class_cfg.name

    identity_keys: set[str] = set()
    for class_attr_config in class_cfg.class_config_attribute_configs:
        if not bool(class_attr_config.is_identity_key):
            continue
        attr_cfg = class_attr_config.attribute_config
        attr_name = (attr_cfg.name or "").strip()
        if attr_name:
            identity_keys.add(attr_name)

    if not class_fqn:
        class_fqn = class_cfg.name

    return _ProjectionOwnedClassTruth(
        class_fqn=class_fqn,
        attributes=frozenset(attributes),
        identity_key_attributes=frozenset(identity_keys),
    )


def _projection_lookup_key(projection: CodeSectionProjection) -> str:
    projection_name = (projection.projection_name or "").strip()
    if projection_name:
        return projection_name
    return (projection.name or "").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _tree_node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace").strip()


def _node_range(node: Node) -> ByteRange:
    return ByteRange(start=node.start_byte, end=node.end_byte)


def _char_to_byte_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for ch in text:
        total += len(ch.encode("utf-8"))
        offsets.append(total)
    return offsets


def _char_span_to_byte_range(*, byte_offsets: list[int], start: int, end: int) -> ByteRange:
    return ByteRange(start=byte_offsets[start], end=byte_offsets[end])
