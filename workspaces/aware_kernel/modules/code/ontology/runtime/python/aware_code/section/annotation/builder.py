"""Builder for constructing CodeSectionAnnotation instances from source code."""

# Kernel Graph Ontology
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.annotation.adapter import CodeSectionAnnotationAdapter
from aware_code.stable_ids import stable_code_section_annotation_id


def build_annotation_section(
    adapter: CodeSectionAnnotationAdapter[T_Node],
    code_section: CodeSection,
    node: CodeNode[T_Node],
) -> CodeSectionAnnotation:
    """Build a CodeSectionAnnotation from a parser node."""
    path = adapter.get_path(node).strip()
    verb = adapter.get_verb(node).strip()
    args = [arg.strip() for arg in adapter.get_args(node)]

    annotation_id = stable_code_section_annotation_id(
        code_section_id=code_section.id,
    )

    annotation = CodeSectionAnnotation(
        id=annotation_id,
        code_section=code_section,
        code_section_id=code_section.id,
        path=path,
        verb=verb,
        args=args,
    )
    return annotation
