from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_interface.manifest.app_spec import (
    AwareAppScreenSourceSpec,
    AwareAppSourceSpec,
)


class AwareAppSourceError(ValueError):
    """Raised when authored app `.aware` sources fail validation."""


def load_aware_app_source_spec_from_text(
    *,
    source_text: str,
    source_path: str | Path | None = None,
) -> tuple[AwareAppSourceSpec, ...]:
    path_label = str(source_path) if source_path is not None else "<app.aware>"
    source_bytes = source_text.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    if tree.root_node.has_error:
        raise AwareAppSourceError(f"Invalid authored app source in {path_label}")

    apps: list[AwareAppSourceSpec] = []
    seen_names: set[str] = set()
    for node in tree.root_node.named_children:
        if node.type != "app_def":
            continue
        app = _load_app_definition(
            node=node,
            source_bytes=source_bytes,
            source_path=path_label,
        )
        name_key = app.name.casefold()
        if name_key in seen_names:
            raise AwareAppSourceError(f"Duplicate app declaration {app.name!r} in {path_label}")
        seen_names.add(name_key)
        apps.append(app)
    return tuple(apps)


def load_aware_app_source_specs(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[AwareAppSourceSpec, ...]:
    app_by_name: dict[str, AwareAppSourceSpec] = {}
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="app source")
        apps = load_aware_app_source_spec_from_text(
            source_text=source_path.read_text(encoding="utf-8"),
            source_path=relpath.as_posix(),
        )
        for app in apps:
            name_key = app.name.casefold()
            if name_key in app_by_name:
                raise AwareAppSourceError(f"Duplicate app declaration {app.name!r} across app sources")
            app_by_name[name_key] = app
    return tuple(
        sorted(
            app_by_name.values(),
            key=lambda item: (item.name, item.source_path),
        )
    )


def _load_app_definition(
    *,
    node: Node,
    source_bytes: bytes,
    source_path: str,
) -> AwareAppSourceSpec:
    app_name = _node_text(source_bytes, node.child_by_field_name("name"))
    if not app_name:
        raise AwareAppSourceError(f"App declaration has empty name in {source_path}")
    body = node.child_by_field_name("body")
    if body is None:
        raise AwareAppSourceError(f"App {app_name!r} is missing a body in {source_path}")

    title: str | None = None
    description: str | None = None
    screens: list[AwareAppScreenSourceSpec] = []
    seen_screen_keys: set[str] = set()
    for child in _iter_semantic_children(body, "app_item"):
        if child.type == "app_title_decl":
            if title is not None:
                raise AwareAppSourceError(f"App {app_name!r} has multiple title declarations in {source_path}")
            title = _strip_string_literal(_node_text(source_bytes, child.child_by_field_name("title")))
            continue
        if child.type == "app_description_decl":
            if description is not None:
                raise AwareAppSourceError(f"App {app_name!r} has multiple description declarations in {source_path}")
            description = _strip_string_literal(_node_text(source_bytes, child.child_by_field_name("description")))
            continue
        if child.type == "app_screen_def":
            screen = _load_app_screen_definition(
                node=child,
                source_bytes=source_bytes,
                app_name=app_name,
                source_path=source_path,
            )
            screen_key = screen.screen_key.casefold()
            if screen_key in seen_screen_keys:
                raise AwareAppSourceError(f"App {app_name!r} duplicates screen {screen.screen_key!r} in {source_path}")
            seen_screen_keys.add(screen_key)
            screens.append(screen)

    if not screens:
        raise AwareAppSourceError(f"App {app_name!r} must declare at least one screen in {source_path}")

    return AwareAppSourceSpec(
        name=app_name,
        title=title,
        description=description,
        screens=tuple(screens),
        source_path=source_path,
    )


def _load_app_screen_definition(
    *,
    node: Node,
    source_bytes: bytes,
    app_name: str,
    source_path: str,
) -> AwareAppScreenSourceSpec:
    screen_key = _node_text(source_bytes, node.child_by_field_name("screen_key"))
    if not screen_key:
        raise AwareAppSourceError(f"App {app_name!r} has a screen with empty key in {source_path}")
    body = node.child_by_field_name("body")
    if body is None:
        raise AwareAppSourceError(f"App {app_name!r} screen {screen_key!r} is missing a body in {source_path}")

    projection_layouts = [
        child
        for child in _iter_semantic_children(body, "app_screen_item")
        if child.type == "app_screen_projection_layout_decl"
    ]
    if len(projection_layouts) != 1:
        raise AwareAppSourceError(
            f"App {app_name!r} screen {screen_key!r} must declare exactly one "
            + f"projection/layout target in {source_path}; got {len(projection_layouts)}"
        )
    target = projection_layouts[0]
    projection = _node_text(source_bytes, target.child_by_field_name("projection"))
    layout = _node_text(source_bytes, target.child_by_field_name("layout"))
    if not projection or not layout:
        raise AwareAppSourceError(
            f"App {app_name!r} screen {screen_key!r} has an empty projection/layout target in {source_path}"
        )
    return AwareAppScreenSourceSpec(
        screen_key=screen_key,
        projection_experience=projection,
        projection_experience_layout=layout,
        source_path=source_path,
    )


def _iter_semantic_children(body: Node, wrapper_type: str) -> list[Node]:
    out: list[Node] = []
    for child in body.named_children:
        if child.type == wrapper_type:
            out.extend(child.named_children)
            continue
        out.append(child)
    return out


def _node_text(source_bytes: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8").strip()


def _strip_string_literal(value: str) -> str:
    text = value.strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1]
    return text.strip() or value.strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents:
        return
    raise AwareAppSourceError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "AwareAppSourceError",
    "load_aware_app_source_spec_from_text",
    "load_aware_app_source_specs",
]
