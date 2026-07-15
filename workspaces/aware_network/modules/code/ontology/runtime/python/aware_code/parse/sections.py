from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import replace
from typing import cast

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.node.node import CodeNode, T_Node
from aware_code.parse.content import parse_content_tree
from aware_code.parse.models import (
    AnnotationPlanDescriptor,
    ImportNamePlanDescriptor,
    ImportPlanDescriptor,
    SegmentPlanDescriptor,
    SectionPlanDescriptor,
)
from aware_code.section.annotation.adapter import CodeSectionAnnotationAdapter
from aware_code.section.import_.adapter import CodeSectionImportAdapter
from aware_code.tree.tree import CodeTree
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType


def make_section_identity_hash(
    *,
    section_type: CodeSectionType,
    qualname: str,
    body_bytes: bytes,
) -> str:
    body_hash = hashlib.sha1(body_bytes).hexdigest()
    combined = f"{section_type.name}:{qualname}:{body_hash}".encode()
    return hashlib.sha1(combined).hexdigest()


def make_section_key(
    *,
    section_type: CodeSectionType,
    qualname: str,
    reference: str | None,
) -> str:
    qualname_clean = qualname.strip()
    if qualname_clean:
        return qualname_clean
    reference_clean = (reference or "").strip()
    if reference_clean:
        return reference_clean
    raise ValueError(
        "Code section plan requires a canonical descriptive key: "
        f"section_type={section_type.value}"
    )


def _node_text(*, source: bytes, node: CodeNode[T_Node]) -> str:
    return node.text(source).decode("utf-8").strip()


def _build_import_plan(
    *,
    adapter: CodeSectionImportAdapter[T_Node],
    code_tree: CodeTree[T_Node],
    node: CodeNode[T_Node],
) -> ImportPlanDescriptor:
    source = code_tree.source_bytes
    module_node = adapter.get_module_name(node)
    name_plans: list[ImportNamePlanDescriptor] = []
    for name_node, alias_node in adapter.get_import_names(node):
        alias_text = _node_text(source=source, node=alias_node) if alias_node is not None else None
        name_plans.append(
            ImportNamePlanDescriptor(
                name_text=_node_text(source=source, node=name_node),
                alias_text=alias_text,
                name_segment_plan=SegmentPlanDescriptor(
                    slot_key="name",
                    byte_start=name_node.byte_start,
                    byte_end=name_node.byte_end,
                ),
                alias_segment_plan=(
                    SegmentPlanDescriptor(
                        slot_key="alias",
                        byte_start=alias_node.byte_start,
                        byte_end=alias_node.byte_end,
                    )
                    if alias_node is not None
                    else None
                ),
            )
        )
    return ImportPlanDescriptor(
        module_text=_node_text(source=source, node=module_node).removesuffix(".*"),
        is_from_import=adapter.is_from_import(node),
        is_star_import=adapter.is_star_import(node),
        relative_level=adapter.get_relative_level(node),
        module_segment_plan=SegmentPlanDescriptor(
            slot_key="module",
            byte_start=module_node.byte_start,
            byte_end=module_node.byte_end,
        ),
        name_plans=tuple(name_plans),
    )


def collect_section_identity_descriptors(
    *,
    adapter: CodeNodeAdapter[T_Node],
    code_tree: CodeTree[T_Node],
    parent: str | None = None,
) -> tuple[SectionPlanDescriptor, ...]:
    descriptors: list[SectionPlanDescriptor] = []
    nodes = list(adapter.match_nodes(code_tree.root.node, code_tree.source_bytes))
    nodes.sort(key=lambda node: node.byte_start)

    for node in nodes:
        qualname = adapter.qualname(node, parent)
        body_bytes = adapter.body_bytes(node, code_tree.source_bytes)
        reference = adapter.reference_string(node, parent)
        annotation_plan: AnnotationPlanDescriptor | None = None
        import_plan: ImportPlanDescriptor | None = None
        if isinstance(adapter, CodeSectionAnnotationAdapter):
            annotation_plan = AnnotationPlanDescriptor(
                path=adapter.get_path(node).strip(),
                verb=adapter.get_verb(node).strip(),
                args=tuple(arg.strip() for arg in adapter.get_args(node) if arg.strip()),
            )
        if isinstance(adapter, CodeSectionImportAdapter):
            import_plan = _build_import_plan(
                adapter=adapter,
                code_tree=code_tree,
                node=node,
            )
        descriptors.append(
            SectionPlanDescriptor(
                section_key=make_section_key(
                    section_type=adapter.section_type,
                    qualname=qualname,
                    reference=reference,
                ),
                section_type=adapter.section_type,
                qualname=qualname,
                identity_hash=make_section_identity_hash(
                    section_type=adapter.section_type,
                    qualname=qualname,
                    body_bytes=body_bytes,
                ),
                byte_start=node.byte_start,
                byte_end=node.byte_end,
                reference=reference,
                annotation_plan=annotation_plan,
                import_plan=import_plan,
            )
        )

    return tuple(descriptors)


def collect_top_level_section_identity_descriptors(
    *,
    content: str,
    language: CodeLanguage,
) -> tuple[SectionPlanDescriptor, ...]:
    code_tree = parse_content_tree(content=content, language=language)
    language_plugin = CodeLanguagePluginRegistry.get_typed(language)

    descriptors: list[SectionPlanDescriptor] = []
    for _section_type, adapter in language_plugin.node_adapters.items():
        descriptors.extend(
            collect_section_identity_descriptors(
                adapter=cast(CodeNodeAdapter[object], adapter),
                code_tree=cast(CodeTree[object], code_tree),
            )
        )

    descriptors.sort(key=lambda item: (item.byte_start, item.byte_end, item.section_type.value))
    return _with_unique_section_keys(tuple(descriptors))


def _with_unique_section_keys(
    descriptors: tuple[SectionPlanDescriptor, ...],
) -> tuple[SectionPlanDescriptor, ...]:
    key_counts = Counter((descriptor.section_type, descriptor.section_key) for descriptor in descriptors)
    if not any(count > 1 for count in key_counts.values()):
        return descriptors

    occurrences: defaultdict[tuple[CodeSectionType, str], int] = defaultdict(int)
    unique_descriptors: list[SectionPlanDescriptor] = []
    for descriptor in descriptors:
        key = (descriptor.section_type, descriptor.section_key)
        occurrences[key] += 1
        if key_counts[key] == 1 or occurrences[key] == 1:
            unique_descriptors.append(descriptor)
            continue
        unique_descriptors.append(
            replace(
                descriptor,
                section_key=f"{descriptor.section_key}#{occurrences[key]}",
            )
        )
    return tuple(unique_descriptors)
