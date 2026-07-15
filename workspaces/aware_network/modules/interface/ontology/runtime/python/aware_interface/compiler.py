from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


@dataclass(frozen=True, slots=True)
class InterfacePaneViewOwnership:
    ref: str
    is_default: bool
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InterfacePaneOwnership:
    name: str
    pane_kind: str
    source_path: str
    description: str | None
    views: tuple[InterfacePaneViewOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfaceWindowLayoutSectionOwnership:
    key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class InterfaceWindowLayoutOwnership:
    key: str
    is_default: bool
    source_path: str
    sections: tuple[InterfaceWindowLayoutSectionOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfaceWindowOwnership:
    key: str
    source_path: str
    layouts: tuple[InterfaceWindowLayoutOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfacePaneMountOwnership:
    window_key: str
    layout_key: str
    section_key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class InterfacePaneCompositionOwnership:
    pane_name: str
    source_path: str
    narrative_key: str | None
    mounts: tuple[InterfacePaneMountOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfaceOwnership:
    name: str
    source_path: str
    windows: tuple[InterfaceWindowOwnership, ...]
    panes: tuple[InterfacePaneCompositionOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfaceSourceOwnership:
    pane_ownership: tuple[InterfacePaneOwnership, ...]
    interface_ownership: tuple[InterfaceOwnership, ...]


def load_interface_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> InterfaceSourceOwnership:
    parser = Parser(language=AWARE_LANGUAGE)
    pane_by_name: dict[str, InterfacePaneOwnership] = {}
    interface_by_name: dict[str, InterfaceOwnership] = {}

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="interface source"
        )
        source_text = source_path.read_text(encoding="utf-8")
        source_bytes = source_text.encode("utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_bytes)
        if tree.root_node.has_error:
            raise ValueError(f"Invalid authored Interface source in {source_path}")

        for node in tree.root_node.named_children:
            if node.type == "pane_def":
                pane = _load_pane_definition(
                    node=node,
                    source_bytes=source_bytes,
                    source_path=source_path,
                    source_rel=source_rel,
                )
                pane_key = pane.name.casefold()
                if pane_key in pane_by_name:
                    raise ValueError(
                        f"Duplicate pane declaration {pane.name!r} across interface sources"
                    )
                pane_by_name[pane_key] = pane
                continue
            if node.type == "interface_def":
                interface = _load_interface_definition(
                    node=node,
                    source_bytes=source_bytes,
                    source_path=source_path,
                    source_rel=source_rel,
                )
                interface_key = interface.name.casefold()
                if interface_key in interface_by_name:
                    raise ValueError(
                        f"Duplicate interface declaration {interface.name!r} across interface sources"
                    )
                interface_by_name[interface_key] = interface

    return InterfaceSourceOwnership(
        pane_ownership=tuple(
            sorted(
                pane_by_name.values(), key=lambda item: (item.name, item.source_path)
            )
        ),
        interface_ownership=tuple(
            sorted(
                interface_by_name.values(),
                key=lambda item: (item.name, item.source_path),
            )
        ),
    )


def _load_pane_definition(
    *,
    node: Node,
    source_bytes: bytes,
    source_path: Path,
    source_rel: str,
) -> InterfacePaneOwnership:
    pane_name = _symbol_key(_field_text(source_bytes, node, "name"))
    if not pane_name:
        raise ValueError(f"Interface pane declaration has empty name in {source_path}")
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Interface pane declaration {pane_name!r} is missing a body in {source_path}"
        )

    pane_kind: str | None = None
    views: list[InterfacePaneViewOwnership] = []
    seen_view_refs: set[str] = set()

    for child in _iter_semantic_children(body, "pane_item"):
        if child.type == "pane_kind_decl":
            if pane_kind is not None:
                raise ValueError(
                    f"Interface pane {pane_name!r} has multiple kind declarations in {source_path}"
                )
            pane_kind = _symbol_key(_field_text(source_bytes, child, "kind"))
            continue
        if child.type == "pane_view_def":
            view_ref = _qualified_text(source_bytes, child.child_by_field_name("view"))
            if not view_ref:
                raise ValueError(
                    f"Interface pane {pane_name!r} has a view with empty reference in {source_path}"
                )
            view_ref_key = view_ref.casefold()
            if view_ref_key in seen_view_refs:
                raise ValueError(
                    f"Interface pane {pane_name!r} duplicates view {view_ref!r} in {source_path}"
                )
            seen_view_refs.add(view_ref_key)
            view_body = child.child_by_field_name("body")
            views.append(
                InterfacePaneViewOwnership(
                    ref=view_ref,
                    is_default=child.child_by_field_name("default_marker") is not None,
                    source_path=source_rel,
                    description=_extract_block_description(source_bytes, view_body),
                )
            )
            continue
        if child.type == "pane_endpoint_def":
            raise ValueError(
                f"Interface pane {pane_name!r} declares retired endpoint ownership in {source_path}; "
                + "declare projection-view invocation actions and bind render actions by view_action_key"
            )
        if child.type == "pane_operation_def":
            raise ValueError(
                f"Interface pane {pane_name!r} declares retired SDK operation ownership in {source_path}; "
                + "declare projection-view invocation actions and bind render actions by view_action_key"
            )

    normalized_kind = (pane_kind or "").strip()
    if not normalized_kind:
        raise ValueError(
            f"Interface pane {pane_name!r} must declare exactly one kind in {source_path}"
        )
    if len(views) != 1:
        raise ValueError(
            f"Interface pane {pane_name!r} must declare exactly one view in {source_path}; "
            + f"got {len(views)}"
        )
    default_view_count = sum(1 for item in views if item.is_default)
    if default_view_count != 1:
        raise ValueError(
            f"Interface pane {pane_name!r} requires exactly one default view in {source_path}; got {default_view_count}"
        )

    return InterfacePaneOwnership(
        name=pane_name,
        pane_kind=normalized_kind,
        source_path=source_rel,
        description=_extract_block_description(source_bytes, body),
        views=tuple(views),
    )


def _load_interface_definition(
    *,
    node: Node,
    source_bytes: bytes,
    source_path: Path,
    source_rel: str,
) -> InterfaceOwnership:
    interface_name = _symbol_key(_field_text(source_bytes, node, "name"))
    if not interface_name:
        raise ValueError(f"Interface declaration has empty name in {source_path}")
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Interface declaration {interface_name!r} is missing a body in {source_path}"
        )

    windows: list[InterfaceWindowOwnership] = []
    panes: list[InterfacePaneCompositionOwnership] = []
    seen_window_keys: set[str] = set()
    seen_pane_names: set[str] = set()

    for child in _iter_semantic_children(body, "interface_item"):
        if child.type == "interface_api_decl":
            raise ValueError(
                f"Interface {interface_name!r} declares retired api ownership in {source_path}; "
                + "declare projection-view invocation actions instead"
            )
        if child.type == "interface_window_def":
            window = _load_interface_window_definition(
                node=child,
                source_bytes=source_bytes,
                interface_name=interface_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            window_key = window.key.casefold()
            if window_key in seen_window_keys:
                raise ValueError(
                    f"Interface {interface_name!r} duplicates window {window.key!r} in {source_path}"
                )
            seen_window_keys.add(window_key)
            windows.append(window)
            continue
        if child.type == "interface_pane_def":
            pane = _load_interface_pane_definition(
                node=child,
                source_bytes=source_bytes,
                interface_name=interface_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            pane_key = pane.pane_name.casefold()
            if pane_key in seen_pane_names:
                raise ValueError(
                    f"Interface {interface_name!r} duplicates pane composition {pane.pane_name!r} in {source_path}"
                )
            seen_pane_names.add(pane_key)
            panes.append(pane)

    if not windows:
        raise ValueError(
            f"Interface {interface_name!r} must declare at least one window in {source_path}"
        )

    return InterfaceOwnership(
        name=interface_name,
        source_path=source_rel,
        windows=tuple(windows),
        panes=tuple(panes),
    )


def _load_interface_window_definition(
    *,
    node: Node,
    source_bytes: bytes,
    interface_name: str,
    source_path: Path,
    source_rel: str,
) -> InterfaceWindowOwnership:
    window_key = _symbol_key(_field_text(source_bytes, node, "window_name"))
    if not window_key:
        raise ValueError(
            f"Interface {interface_name!r} has a window with empty key in {source_path}"
        )
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Interface {interface_name!r} window {window_key!r} is missing a body in {source_path}"
        )

    layouts: list[InterfaceWindowLayoutOwnership] = []
    seen_layout_keys: set[str] = set()
    default_layout_count = 0
    for child in _iter_semantic_children(body, "interface_layout_item"):
        if child.type != "interface_layout_def":
            continue
        layout = _load_interface_layout_definition(
            node=child,
            source_bytes=source_bytes,
            interface_name=interface_name,
            window_key=window_key,
            source_path=source_path,
            source_rel=source_rel,
        )
        layout_key = layout.key.casefold()
        if layout_key in seen_layout_keys:
            raise ValueError(
                f"Interface {interface_name!r} window {window_key!r} duplicates layout {layout.key!r} in {source_path}"
            )
        seen_layout_keys.add(layout_key)
        default_layout_count += 1 if layout.is_default else 0
        layouts.append(layout)

    if not layouts:
        raise ValueError(
            f"Interface {interface_name!r} window {window_key!r} must declare at least one layout in {source_path}"
        )
    if default_layout_count > 1:
        raise ValueError(
            f"Interface {interface_name!r} window {window_key!r} allows at most one default layout in {source_path}"
        )

    return InterfaceWindowOwnership(
        key=window_key,
        source_path=source_rel,
        layouts=tuple(layouts),
    )


def _load_interface_layout_definition(
    *,
    node: Node,
    source_bytes: bytes,
    interface_name: str,
    window_key: str,
    source_path: Path,
    source_rel: str,
) -> InterfaceWindowLayoutOwnership:
    layout_key = _symbol_key(_field_text(source_bytes, node, "layout_name"))
    if not layout_key:
        raise ValueError(
            f"Interface {interface_name!r} window {window_key!r} has a layout with empty key in {source_path}"
        )
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Interface {interface_name!r} window {window_key!r} layout {layout_key!r} "
            + f"is missing a body in {source_path}"
        )

    sections: list[InterfaceWindowLayoutSectionOwnership] = []
    seen_section_keys: set[str] = set()
    for child in _iter_semantic_children(body, "interface_layout_item"):
        if child.type == "interface_layout_section_def":
            section_key = _symbol_key(_field_text(source_bytes, child, "section_name"))
            if not section_key:
                raise ValueError(
                    f"Interface {interface_name!r} window {window_key!r} layout {layout_key!r} "
                    + f"has an empty section key in {source_path}"
                )
            section_key_token = section_key.casefold()
            if section_key_token in seen_section_keys:
                raise ValueError(
                    f"Interface {interface_name!r} window {window_key!r} layout {layout_key!r} "
                    + f"duplicates section {section_key!r} in {source_path}"
                )
            seen_section_keys.add(section_key_token)
            sections.append(
                InterfaceWindowLayoutSectionOwnership(
                    key=section_key,
                    source_path=source_rel,
                )
            )
            continue

    return InterfaceWindowLayoutOwnership(
        key=layout_key,
        is_default=node.child_by_field_name("default_marker") is not None,
        source_path=source_rel,
        sections=tuple(sections),
    )


def _load_interface_pane_definition(
    *,
    node: Node,
    source_bytes: bytes,
    interface_name: str,
    source_path: Path,
    source_rel: str,
) -> InterfacePaneCompositionOwnership:
    pane_name = _symbol_key(_field_text(source_bytes, node, "pane_name"))
    if not pane_name:
        raise ValueError(
            f"Interface {interface_name!r} has a pane composition with empty name in {source_path}"
        )
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Interface {interface_name!r} pane composition {pane_name!r} is missing a body in {source_path}"
        )

    mounts: list[InterfacePaneMountOwnership] = []
    narrative_key: str | None = None
    seen_mount_targets: set[str] = set()
    for child in _iter_semantic_children(body, "interface_pane_item"):
        if child.type == "interface_pane_mount_def":
            target_ref = _qualified_text(
                source_bytes, child.child_by_field_name("target")
            )
            target_parts = target_ref.split(".")
            if len(target_parts) != 3:
                raise ValueError(
                    f"Interface {interface_name!r} pane composition {pane_name!r} has invalid mount target "
                    + f"{target_ref!r} in {source_path}"
                )
            mount_key = target_ref.casefold()
            if mount_key in seen_mount_targets:
                raise ValueError(
                    f"Interface {interface_name!r} pane composition {pane_name!r} duplicates mount "
                    + f"{target_ref!r} in {source_path}"
                )
            seen_mount_targets.add(mount_key)
            mounts.append(
                InterfacePaneMountOwnership(
                    window_key=target_parts[0],
                    layout_key=target_parts[1],
                    section_key=target_parts[2],
                    source_path=source_rel,
                )
            )
            continue
        if child.type == "interface_pane_narrative_def":
            if narrative_key is not None:
                raise ValueError(
                    f"Interface {interface_name!r} pane composition {pane_name!r} "
                    + f"has multiple narratives in {source_path}"
                )
            narrative_key = _qualified_text(
                source_bytes,
                child.child_by_field_name("narrative"),
            )

    if not mounts:
        raise ValueError(
            f"Interface {interface_name!r} pane composition {pane_name!r} "
            + f"must declare at least one mount in {source_path}"
        )

    return InterfacePaneCompositionOwnership(
        pane_name=pane_name,
        source_path=source_rel,
        narrative_key=narrative_key,
        mounts=tuple(mounts),
    )


def _symbol_key(value: str) -> str:
    return (value or "").strip()


def _field_text(source_bytes: bytes, node: Node, field_name: str) -> str:
    child = node.child_by_field_name(field_name)
    return _qualified_text(source_bytes, child)


def _qualified_text(source_bytes: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8").strip()


def _extract_block_description(source_bytes: bytes, body: Node | None) -> str | None:
    if body is None:
        return None
    for child in body.named_children:
        if child.type == "triple_string_literal":
            return _strip_triple_string(_qualified_text(source_bytes, child))
        if child.type == "string_literal":
            return _strip_string_literal(_qualified_text(source_bytes, child))
    return None


def _iter_semantic_children(body: Node, wrapper_type: str) -> list[Node]:
    out: list[Node] = []
    for child in body.named_children:
        if child.type == wrapper_type:
            out.extend(child.named_children)
            continue
        out.append(child)
    return out


def _strip_triple_string(value: str) -> str:
    text = value.strip()
    if text.startswith('"""') and text.endswith('"""') and len(text) >= 6:
        text = text[3:-3]
    return text.strip() or value.strip()


def _strip_string_literal(value: str) -> str:
    text = value.strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1]
    return text.strip() or value.strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "InterfaceOwnership",
    "InterfacePaneCompositionOwnership",
    "InterfacePaneMountOwnership",
    "InterfacePaneOwnership",
    "InterfacePaneViewOwnership",
    "InterfaceSourceOwnership",
    "InterfaceWindowLayoutOwnership",
    "InterfaceWindowLayoutSectionOwnership",
    "InterfaceWindowOwnership",
    "load_interface_ownership_from_sources",
]
