from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


@dataclass(frozen=True, slots=True)
class AttentionSectionConfigOwnership:
    key: str
    source_path: str
    order: int
    title: str | None = None
    description: str | None = None
    flex: float | None = None
    is_visible: bool | None = None


@dataclass(frozen=True, slots=True)
class AttentionLayoutConfigOwnership:
    key: str
    is_default: bool
    source_path: str
    sections: tuple[AttentionSectionConfigOwnership, ...]


@dataclass(frozen=True, slots=True)
class AttentionSourceOwnership:
    layouts: tuple[AttentionLayoutConfigOwnership, ...]


def load_attention_layout_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> AttentionSourceOwnership:
    parser = Parser(language=AWARE_LANGUAGE)
    layout_by_key: dict[str, AttentionLayoutConfigOwnership] = {}

    for relpath in source_files:
        if relpath.suffix != ".aware":
            continue
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="attention source"
        )
        source_text = source_path.read_text(encoding="utf-8")
        source_bytes = source_text.encode("utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_bytes)
        if tree.root_node.has_error:
            raise ValueError(f"Invalid authored Attention source in {source_path}")

        for node in tree.root_node.named_children:
            if node.type != "attention_layout_def":
                continue
            layout = _load_attention_layout_definition(
                node=node,
                source_bytes=source_bytes,
                source_path=source_path,
                source_rel=source_rel,
            )
            layout_key = layout.key.casefold()
            if layout_key in layout_by_key:
                raise ValueError(
                    f"Duplicate Attention layout declaration {layout.key!r} across sources"
                )
            layout_by_key[layout_key] = layout

    default_count = sum(1 for layout in layout_by_key.values() if layout.is_default)
    if default_count > 1:
        raise ValueError(
            "Attention authored topology allows at most one default layout; "
            + f"got {default_count}"
        )
    return AttentionSourceOwnership(
        layouts=tuple(
            sorted(
                layout_by_key.values(), key=lambda item: (item.key, item.source_path)
            )
        )
    )


def _load_attention_layout_definition(
    *,
    node: Node,
    source_bytes: bytes,
    source_path: Path,
    source_rel: str,
) -> AttentionLayoutConfigOwnership:
    layout_key = _symbol_key(_field_text(source_bytes, node, "layout_name"))
    if not layout_key:
        raise ValueError(f"Attention layout has empty key in {source_path}")
    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Attention layout {layout_key!r} is missing a body in {source_path}"
        )

    sections: list[AttentionSectionConfigOwnership] = []
    seen_section_keys: set[str] = set()
    for child in _iter_semantic_children(body, "attention_layout_item"):
        if child.type == "attention_section_def":
            section_key = _symbol_key(_field_text(source_bytes, child, "section_name"))
            if not section_key:
                raise ValueError(
                    f"Attention layout {layout_key!r} has an empty section key in {source_path}"
                )
            section_key_token = section_key.casefold()
            if section_key_token in seen_section_keys:
                raise ValueError(
                    f"Attention layout {layout_key!r} duplicates section {section_key!r} in {source_path}"
                )
            seen_section_keys.add(section_key_token)
            section_body = child.child_by_field_name("body")
            section_config = _load_attention_section_config(
                node=section_body,
                source_bytes=source_bytes,
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
                default_order=len(sections),
            )
            sections.append(
                AttentionSectionConfigOwnership(
                    key=section_key,
                    source_path=source_rel,
                    order=section_config.order,
                    title=section_config.title,
                    description=section_config.description,
                    flex=section_config.flex,
                    is_visible=section_config.is_visible,
                )
            )
            continue

    if not sections:
        raise ValueError(
            f"Attention layout {layout_key!r} must declare at least one section in {source_path}"
        )
    return AttentionLayoutConfigOwnership(
        key=layout_key,
        is_default=node.child_by_field_name("default_marker") is not None,
        source_path=source_rel,
        sections=tuple(sections),
    )


@dataclass(frozen=True, slots=True)
class _SectionConfigFields:
    order: int
    title: str | None = None
    description: str | None = None
    flex: float | None = None
    is_visible: bool | None = None


def _load_attention_section_config(
    *,
    node: Node | None,
    source_bytes: bytes,
    layout_key: str,
    section_key: str,
    source_path: Path,
    default_order: int,
) -> _SectionConfigFields:
    if node is None:
        return _SectionConfigFields(order=default_order)

    title: str | None = None
    description: str | None = None
    order: int | None = None
    flex: float | None = None
    is_visible: bool | None = None
    seen_fields: set[str] = set()

    for child in _iter_semantic_children(node, "attention_section_item"):
        if child.type == "attention_section_title_stmt":
            _assert_unique_field(
                seen_fields,
                "title",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            title = _string_literal_value(_field_text(source_bytes, child, "title"))
        elif child.type == "attention_section_description_stmt":
            _assert_unique_field(
                seen_fields,
                "description",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            description = _string_literal_value(
                _field_text(source_bytes, child, "description")
            )
        elif child.type == "attention_section_order_stmt":
            _assert_unique_field(
                seen_fields,
                "order",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            order = _int_value(
                _field_text(source_bytes, child, "order"),
                label="order",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
        elif child.type == "attention_section_flex_stmt":
            _assert_unique_field(
                seen_fields,
                "flex",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            flex = _float_value(
                _field_text(source_bytes, child, "flex"),
                label="flex",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            if flex <= 0:
                raise ValueError(
                    "Attention section flex must be greater than 0: "
                    + f"layout {layout_key!r} section {section_key!r} in {source_path}"
                )
        elif child.type == "attention_section_visible_stmt":
            _assert_unique_field(
                seen_fields,
                "is_visible",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )
            is_visible = _bool_value(
                _field_text(source_bytes, child, "is_visible"),
                label="visible",
                layout_key=layout_key,
                section_key=section_key,
                source_path=source_path,
            )

    return _SectionConfigFields(
        order=default_order if order is None else order,
        title=title,
        description=description,
        flex=flex,
        is_visible=is_visible,
    )


def _assert_unique_field(
    seen_fields: set[str],
    field_name: str,
    *,
    layout_key: str,
    section_key: str,
    source_path: Path,
) -> None:
    if field_name not in seen_fields:
        seen_fields.add(field_name)
        return
    raise ValueError(
        "Attention section config declares duplicate field "
        + f"{field_name!r}: layout {layout_key!r} section {section_key!r} in {source_path}"
    )


def _string_literal_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _int_value(
    value: str,
    *,
    label: str,
    layout_key: str,
    section_key: str,
    source_path: Path,
) -> int:
    text = value.strip()
    if not text.isdigit():
        raise ValueError(
            "Attention section config requires integer "
            + f"{label}: layout {layout_key!r} section {section_key!r} in {source_path}"
        )
    return int(text)


def _float_value(
    value: str,
    *,
    label: str,
    layout_key: str,
    section_key: str,
    source_path: Path,
) -> float:
    text = value.strip()
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(
            "Attention section config requires numeric "
            + f"{label}: layout {layout_key!r} section {section_key!r} in {source_path}"
        ) from exc


def _bool_value(
    value: str,
    *,
    label: str,
    layout_key: str,
    section_key: str,
    source_path: Path,
) -> bool:
    text = value.strip().casefold()
    if text == "true":
        return True
    if text == "false":
        return False
    raise ValueError(
        "Attention section config requires boolean "
        + f"{label}: layout {layout_key!r} section {section_key!r} in {source_path}"
    )


def _iter_semantic_children(node: Node, *node_types: str) -> tuple[Node, ...]:
    if not node_types:
        return tuple(node.named_children)
    out: list[Node] = []
    for child in node.named_children:
        if child.type in node_types:
            out.extend(child.named_children)
            continue
        out.append(child)
    return tuple(out)


def _symbol_key(value: str) -> str:
    return (value or "").strip()


def _field_text(source_bytes: bytes, node: Node, field_name: str) -> str:
    child = node.child_by_field_name(field_name)
    return _qualified_text(source_bytes, child)


def _qualified_text(source_bytes: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8").strip()


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
    "AttentionLayoutConfigOwnership",
    "AttentionSectionConfigOwnership",
    "AttentionSourceOwnership",
    "load_attention_layout_ownership_from_sources",
]
