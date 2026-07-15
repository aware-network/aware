"""Builder for constructing CodeSectionBinding instances from source code."""

from __future__ import annotations

import ast

from aware_code_ontology.binding.code_section_binding import CodeSectionBinding
from aware_code_ontology.binding.code_section_binding_map import CodeSectionBindingMap
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_content.builder import get_segment_text
from aware_utils.description_normalizer import DescriptionNormalizer

from aware_code.node.node import CodeNode, T_Node
from aware_code.section.binding.adapter import CodeSectionBindingAdapter

from aware_storage.blob_store import BlobStore


def _extract_body_description(body_text: str) -> str | None:
    raw = (body_text or "").strip()
    if not raw:
        return None
    if raw.startswith("{") and raw.endswith("}"):
        raw = raw[1:-1].strip()
    for fence in ('"""', "'''"):
        if raw.startswith(fence):
            end = raw.find(fence, len(fence))
            if end == -1:
                return None
            content = raw[len(fence) : end]
            return DescriptionNormalizer.normalize_description(content)
    return None


def _decode_template_literal(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if text.startswith("$$") and text.endswith("$$"):
        return text[2:-2]
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Invalid binding template literal: {text!r}") from exc
    if not isinstance(value, str):
        raise ValueError(f"Binding template literal must decode to string, got {type(value).__name__}")
    return value


def build_binding_section(
    *,
    adapter: CodeSectionBindingAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    blob_store: BlobStore | None = None,
) -> CodeSectionBinding:
    _ = source
    code_section_segment = code_section.content_part_text_segment

    source_graph_node = adapter.get_source_graph(node)
    target_graph_node = adapter.get_target_graph(node)

    source_graph_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=source_graph_node.byte_start,
        byte_end=source_graph_node.byte_end,
        parent_id=code_section_segment.id,
    )
    target_graph_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=target_graph_node.byte_start,
        byte_end=target_graph_node.byte_end,
        parent_id=code_section_segment.id,
    )

    binding_section = CodeSectionBinding(
        code_section=code_section,
        source_graph_segment=source_graph_segment,
        source_graph_segment_id=source_graph_segment.id,
        target_graph_segment=target_graph_segment,
        target_graph_segment_id=target_graph_segment.id,
        source_graph_ref=(get_segment_text(source_graph_segment, blob_store=blob_store) or "").strip(),
        target_graph_ref=(get_segment_text(target_graph_segment, blob_store=blob_store) or "").strip(),
    )
    code_section.code_section_binding = binding_section

    maps = adapter.get_maps(node)
    maps.sort(key=lambda m: (m.name_node.byte_start, m.source_node.byte_start, m.target_node.byte_start))
    for map_spec in maps:
        name_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=map_spec.name_node.byte_start,
            byte_end=map_spec.name_node.byte_end,
            parent_id=code_section_segment.id,
        )
        source_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=map_spec.source_node.byte_start,
            byte_end=map_spec.source_node.byte_end,
            parent_id=code_section_segment.id,
        )
        target_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=map_spec.target_node.byte_start,
            byte_end=map_spec.target_node.byte_end,
            parent_id=code_section_segment.id,
        )
        body_segment: ContentPartTextSegment | None = None
        body_text = ""
        template_segment: ContentPartTextSegment | None = None
        template_text: str | None = None
        if map_spec.body_node is not None:
            body_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=map_spec.body_node.byte_start,
                byte_end=map_spec.body_node.byte_end,
                parent_id=code_section_segment.id,
            )
            body_text = get_segment_text(body_segment, blob_store=blob_store) or ""
        if map_spec.template_value_node is not None:
            template_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=map_spec.template_value_node.byte_start,
                byte_end=map_spec.template_value_node.byte_end,
                parent_id=code_section_segment.id,
            )
            template_text = _decode_template_literal(get_segment_text(template_segment, blob_store=blob_store) or "")

        binding_section.code_section_binding_maps.append(
            CodeSectionBindingMap(
                code_section_binding_id=binding_section.id,
                name_segment=name_segment,
                name_segment_id=name_segment.id,
                source_segment=source_segment,
                source_segment_id=source_segment.id,
                target_segment=target_segment,
                target_segment_id=target_segment.id,
                body_segment=body_segment,
                body_segment_id=(body_segment.id if body_segment is not None else None),
                template_segment=template_segment,
                template_segment_id=(template_segment.id if template_segment is not None else None),
                name=(get_segment_text(name_segment, blob_store=blob_store) or "").strip(),
                source_ref=(get_segment_text(source_segment, blob_store=blob_store) or "").strip(),
                target_ref=(get_segment_text(target_segment, blob_store=blob_store) or "").strip(),
                description=_extract_body_description(body_text),
                template_text=template_text,
            )
        )

    return binding_section
