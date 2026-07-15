"""Builder for constructing CodeSectionProjection instances from source code."""

from __future__ import annotations

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
from aware_code_ontology.projection.code_section_projection_edge import (
    CodeSectionProjectionEdge,
)
from aware_code_ontology.projection.code_section_projection_view import (
    CodeSectionProjectionView,
)
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_content.builder import get_segment_text
from aware_utils.description_normalizer import DescriptionNormalizer
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.projection.adapter import (
    CodeSectionProjectionAdapter,
    ProjectionOptionSpec,
)

# Storage
from aware_storage.blob_store import BlobStore


def _strip_string_literal(value: str) -> str:
    raw = (value or "").strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def _normalize_projection_target(raw: str) -> str:
    return _strip_string_literal(raw)


def _projection_identity(
    *,
    projection_symbol: str,
    options: list[ProjectionOptionSpec[T_Node]],
) -> tuple[str, str | None, bool]:
    projection_id_override: str | None = None
    label: str | None = None
    is_branchable = False

    for opt in options:
        key = (opt.keyword or "").strip().lower()
        if key == "name" and opt.value_node is not None:
            projection_id_override = _strip_string_literal(opt.value_node.node_text())
            continue
        if key == "label" and opt.value_node is not None:
            label = _strip_string_literal(opt.value_node.node_text())
            continue
        if key == "is_branchable":
            is_branchable = True
            continue

    projection_name = (projection_id_override or projection_symbol).strip()
    return projection_name, label, is_branchable


def _extract_view_description(body_text: str) -> str | None:
    raw = (body_text or "").strip()
    if not raw:
        return None

    # Strip outer braces when present.
    if raw.startswith("{") and raw.endswith("}"):
        raw = raw[1:-1].strip()

    # Leading docstring convention (same spirit as `fn { ... }`).
    for fence in ('"""', "'''"):
        if raw.startswith(fence):
            end = raw.find(fence, len(fence))
            if end == -1:
                return None
            content = raw[len(fence) : end]
            return DescriptionNormalizer.normalize_description(content)
    return None


def build_projection_section(
    *,
    adapter: CodeSectionProjectionAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    blob_store: BlobStore | None = None,
) -> CodeSectionProjection:
    _ = source
    section_segment = code_section.content_part_text_segment

    name_node = adapter.get_name(node)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    projection_symbol = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

    options = adapter.get_options(node)
    projection_name, label, is_branchable = _projection_identity(
        projection_symbol=projection_symbol,
        options=options,
    )

    root_type_ref: str | None = None
    root_type_segment: ContentPartTextSegment | None = None
    root_node = adapter.get_root_type(node)
    if root_node is not None:
        root_type_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=root_node.byte_start,
            byte_end=root_node.byte_end,
            parent_id=section_segment.id,
        )
        root_type_ref = get_segment_text(
            content_part_text_segment=root_type_segment,
            blob_store=blob_store,
        )

    projection_section = CodeSectionProjection(
        code_section=code_section,
        name=projection_symbol,
        projection_name=projection_name,
        label=label,
        is_branchable=is_branchable,
        root_type_ref=root_type_ref,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        root_type_segment=root_type_segment,
        root_type_segment_id=(root_type_segment.id if root_type_segment is not None else None),
    )
    code_section.code_section_projection = projection_section

    edges = adapter.get_edges(node)
    edges.sort(key=lambda e: e.byte_start)
    for edge_node in edges:
        type_node = adapter.get_edge_type(edge_node)
        member_node = adapter.get_edge_member(edge_node)
        target_node = adapter.get_edge_target(edge_node)

        type_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=type_node.byte_start,
            byte_end=type_node.byte_end,
            parent_id=section_segment.id,
        )
        member_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=member_node.byte_start,
            byte_end=member_node.byte_end,
            parent_id=section_segment.id,
        )

        type_ref = get_segment_text(content_part_text_segment=type_segment, blob_store=blob_store)
        member = get_segment_text(content_part_text_segment=member_segment, blob_store=blob_store)

        target_segment: ContentPartTextSegment | None = None
        target_projection_ref: str | None = None
        if target_node is not None:
            target_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=target_node.byte_start,
                byte_end=target_node.byte_end,
                parent_id=section_segment.id,
            )
            raw_target = get_segment_text(content_part_text_segment=target_segment, blob_store=blob_store)
            normalized = _normalize_projection_target(raw_target)
            target_projection_ref = normalized or None

        projection_section.projection_edges.append(
            CodeSectionProjectionEdge(
                code_section_projection_id=projection_section.id,
                type_ref=type_ref,
                member=member,
                target_projection_ref=target_projection_ref,
                type_segment=type_segment,
                type_segment_id=type_segment.id,
                member_segment=member_segment,
                member_segment_id=member_segment.id,
                target_segment=target_segment,
                target_segment_id=(target_segment.id if target_segment is not None else None),
            )
        )

    views = adapter.get_views(node)
    views.sort(key=lambda v: v.key_node.byte_start)
    for view in views:
        key_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=view.key_node.byte_start,
            byte_end=view.key_node.byte_end,
            parent_id=section_segment.id,
        )
        body_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=view.body_node.byte_start,
            byte_end=view.body_node.byte_end,
            parent_id=section_segment.id,
        )
        body_text = get_segment_text(
            content_part_text_segment=body_segment,
            blob_store=blob_store,
        )
        description = _extract_view_description(body_text)

        projection_section.projection_views.append(
            CodeSectionProjectionView(
                code_section_projection_id=projection_section.id,
                key=view.full_key,
                kind=view.kind,
                is_default=view.is_default,
                description=description,
                key_segment=key_segment,
                key_segment_id=key_segment.id,
                body_segment=body_segment,
                body_segment_id=body_segment.id,
            )
        )

    return projection_section
