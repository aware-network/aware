"""Builder for constructing CodeSectionDecorator instances from source code."""

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_code_ontology.decorator.code_section_decorator_expression import (
    CodeSectionDecoratorExpression,
)

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.builder import build_section_from_code
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter
from aware_code.section.expression.builder import build_expression_section


def build_decorator_section(
    adapter: CodeSectionDecoratorAdapter[T_Node],
    expression_adapter: CodeSectionExpressionAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    section_index: CodeSectionBuilderIndex,
) -> tuple[CodeSectionDecorator, list[CodeSection]]:
    """
    Build a CodeSectionDecorator instance from the provided node.

    Args:
        adapter: The adapter for the decorator section
        expression_adapter: The adapter for the expression section
        code: The code object
        code_section: The code section to build
        node: Node representing a decorator
    Returns:
        Constructed CodeSectionDecorator instance
    """
    # Get section segment
    section_segment = code_section.content_part_text_segment

    # Get the name of the decorator
    decorator_name_node = adapter.get_name(node)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=decorator_name_node.byte_start,
        byte_end=decorator_name_node.byte_end,
        parent_id=section_segment.id,
    )

    # Create the decorator section
    decorator_section = CodeSectionDecorator(
        code_section=code_section,
        name_segment=name_segment,
    )
    code_section.code_section_decorator = decorator_section

    # Link expressions to decorator
    arguments = list(adapter.get_arguments(node))
    arguments.sort(key=lambda n: n[1].byte_start)
    child_sections: list[CodeSection] = []

    for index, (arg_name_node, value_node) in enumerate(arguments):
        code_section_for_expression = build_section_from_code(
            adapter=expression_adapter,
            code_section_type=CodeSectionType.expression,
            source=source,
            code=code,
            node=value_node,
            section_index=section_index,
            parent_id=section_segment.id,
        )
        child_sections.append(code_section_for_expression)

        # Build the expression section
        expr_section = build_expression_section(
            adapter=expression_adapter,
            code=code,
            code_section=code_section_for_expression,
            node=value_node,
        )
        code_section_for_expression.code_section_expression = expr_section

        # Create the decorator-expression link
        decorator_expr_link = CodeSectionDecoratorExpression(
            code_section_decorator_id=decorator_section.id,
            code_section_expression_id=expr_section.id,
            code_section_expression=expr_section,
            name_segment_id=name_segment.id,
            position=index,
        )

        # Add name segment if this is a keyword argument
        if arg_name_node:
            decorator_expr_link.name_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=arg_name_node.byte_start,
                byte_end=arg_name_node.byte_end,
                parent_id=section_segment.id,
            )

        decorator_section.code_section_decorator_expressions.append(decorator_expr_link)

    return decorator_section, child_sections
