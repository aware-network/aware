"""Builder for constructing CodeSectionExpression instances from source code."""

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.expression.code_section_expression import CodeSectionExpression

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter


def build_expression_section(
    adapter: CodeSectionExpressionAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
) -> CodeSectionExpression:
    """
    Build a CodeSectionExpression instance from the provided node.

    Args:
        code: The code object
        code_section: The code section to build
        node: Node representing an expression

    Returns:
        Constructed CodeSectionExpression instance
    """
    # Get section segment
    section_segment = code_section.content_part_text_segment

    # Classify the expression type
    expression_type = adapter.classify(node)

    # Create the value segment for the entire expression
    value_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=node.byte_start,
        byte_end=node.byte_end,
        parent_id=section_segment.id,
    )

    # Create the expression section
    expression_section = CodeSectionExpression(
        code_section=code_section,
        type=expression_type,
        value_segment=value_segment,
    )
    return expression_section
