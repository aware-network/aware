"""Builder for constructing CodeSectionFunction instances from source code."""

from typing import Protocol, cast

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.function.code_section_function_attribute import (
    CodeSectionFunctionAttribute,
)
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.section.attribute.builder import (
    build_section_from_code_with_param_discriminator,
    build_attribute_section,
)
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter
from aware_code.section.decorator.builder import build_decorator_section
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.section.builder import build_section_from_bytes, build_section_from_code

# Aware Storage
from aware_storage.blob_store import BlobStore


class _TreeNodeWithParentId(Protocol):
    parent: "_TreeNodeWithParentId | None"
    id: object


def build_function_section(
    adapter: CodeSectionFunctionAdapter[T_Node],
    attribute_adapter: CodeSectionAttributeAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    section_index: CodeSectionBuilderIndex,
    decorator_adapter: CodeSectionDecoratorAdapter[T_Node] | None = None,
    expression_adapter: CodeSectionExpressionAdapter[T_Node] | None = None,
    blob_store: BlobStore | None = None,
    parent_ref: str | None = None,
) -> tuple[CodeSectionFunction, list[CodeSection]]:
    """
    Build a CodeSectionFunction instance from the provided source code.
    """
    # Get the section segment
    section_segment = code_section.content_part_text_segment

    # Get the function qualname
    function_reference_string = adapter.reference_string(node, parent=parent_ref)

    # Get the function name
    name_node = adapter.get_name(node)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

    # Get the function signature
    signature_node = adapter.get_signature(node)
    signature_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=signature_node.byte_start,
        byte_end=signature_node.byte_end,
        parent_id=section_segment.id,
    )

    # Get the function body
    body_segment = None
    body_node = adapter.get_body(node)
    if body_node:
        body_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=body_node.byte_start,
            byte_end=body_node.byte_end,
            parent_id=section_segment.id,
        )

    # Get function properties
    is_async = adapter.is_async(node)
    is_public = adapter.is_public(node)
    is_static = adapter.is_staticmethod(node)
    is_classmethod = adapter.is_classmethod(node)
    verb = adapter.get_verb(node)

    # Get return type segment
    return_type_segment = None
    return_type_node = adapter.get_return_type(node)
    if return_type_node:
        return_type_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=return_type_node.byte_start,
            byte_end=return_type_node.byte_end,
            parent_id=section_segment.id,
        )

    # Create the function section
    code_section_function = CodeSectionFunction(
        code_section=code_section,
        name_segment=name_segment,
        signature_segment=signature_segment,
        body_segment=body_segment,
        return_type_segment=return_type_segment,
        name=name,
        is_async=is_async,
        is_public=is_public,
        is_static=is_static,
        is_classmethod=is_classmethod,
        verb=verb,
        description=None,
    )
    code_section.code_section_function = code_section_function
    child_sections: list[CodeSection] = []

    # Process parameters
    param_nodes = list(adapter.get_parameters(node))
    # Ensure deterministic attribute ordering based on source position
    param_nodes.sort(key=lambda n: n.byte_start)
    for index, param_node in enumerate(param_nodes):
        code_section_for_attribute = build_section_from_code_with_param_discriminator(
            adapter=attribute_adapter,
            source=source,
            code=code,
            node=param_node,
            section_index=section_index,
            parent_ref=function_reference_string,
            parent_id=section_segment.id,
            is_parameter=True,
        )
        child_sections.append(code_section_for_attribute)
        attr_section = build_attribute_section(
            adapter=attribute_adapter,
            code=code,
            code_section=code_section_for_attribute,
            node=param_node,
            is_parameter=True,
            blob_store=blob_store,
        )
        code_section_for_attribute.code_section_attribute = attr_section

        # Link the attribute to the function with canonical position
        code_section_function_attribute = CodeSectionFunctionAttribute(
            code_section_function_id=code_section_function.id,
            code_section_attribute=attr_section,
            position=index,
            is_output=False,
        )
        code_section_function.code_section_function_attributes.append(code_section_function_attribute)

    # Process named return parameters (outputs) if the language supports them
    out_nodes = adapter.get_return_parameters(node)
    if out_nodes:
        out_nodes = list(out_nodes)
        out_nodes.sort(key=lambda n: n.byte_start)
        for index, out_node in enumerate(out_nodes):
            code_section_for_attribute = build_section_from_code_with_param_discriminator(
                adapter=attribute_adapter,
                source=source,
                code=code,
                node=out_node,
                section_index=section_index,
                parent_ref=function_reference_string,
                parent_id=section_segment.id,
                is_parameter=True,
                discriminator="out",
            )
            child_sections.append(code_section_for_attribute)
            attr_section = build_attribute_section(
                adapter=attribute_adapter,
                code=code,
                code_section=code_section_for_attribute,
                node=out_node,
                is_parameter=True,
                blob_store=blob_store,
            )
            code_section_for_attribute.code_section_attribute = attr_section

            # Link the attribute to the function as an OUTPUT with canonical position
            code_section_function_attribute = CodeSectionFunctionAttribute(
                code_section_function_id=code_section_function.id,
                code_section_attribute=attr_section,
                position=index,
                is_output=True,
            )
            code_section_function.code_section_function_attributes.append(code_section_function_attribute)
    elif return_type_segment is not None:
        # Canonical: single-value returns must materialize an OUTPUT attribute so downstream
        # meta builders (and language renderers) can type return values.
        #
        # For tuple returns, languages should provide `output_attr` nodes and this branch is skipped.
        return_type_text = get_segment_text(content_part_text_segment=return_type_segment, blob_store=blob_store)
        normalized = (return_type_text or "").strip()
        if normalized and normalized not in {"Void", "None"}:
            # Unnamed returns are represented as a single synthetic attribute called `value`.
            out_name = "value"
            out_qualname = f"{function_reference_string}.{out_name} (out)"
            out_reference = f"{function_reference_string}.{out_name} (out)"
            body_bytes = f"out:{out_name} {normalized}".encode("utf-8")
            # Use the return type node as the anchor for this synthesized section (deterministic offsets).
            assert return_type_node is not None
            out_section = build_section_from_bytes(
                code_section_type=CodeSectionType.attribute,
                code=code,
                section_index=section_index,
                qualname=out_qualname,
                body_bytes=body_bytes,
                byte_start=return_type_node.byte_start,
                byte_end=return_type_node.byte_end,
                parent_id=section_segment.id,
                reference=out_reference,
            )
            section_index.add_section_node(
                code_section_id=out_section.id,
                code_node=cast(CodeNode[object], return_type_node),
            )

            out_attr = CodeSectionAttribute(
                code_section=out_section,
                name=out_name,
                type_text=normalized,
                default_value_text=None,
                description=None,
                is_required=True,
                is_public=True,
                is_unique=False,
                is_primary=False,
                is_many_to_many=False,
                edge_spec_name=None,
            )
            out_section.code_section_attribute = out_attr
            child_sections.append(out_section)

            code_section_function.code_section_function_attributes.append(
                CodeSectionFunctionAttribute(
                    code_section_function_id=code_section_function.id,
                    code_section_attribute=out_attr,
                    position=0,
                    is_output=True,
                )
            )

    # Process decorators if decorator adapter is available
    if decorator_adapter is not None:
        if expression_adapter is None:
            raise ValueError("Expression adapter is required to build decorators")

        # Get the module-root
        root = cast(_TreeNodeWithParentId, node.node)
        while root.parent:
            root = root.parent

        # Find decorators for this function
        for decorator_node in decorator_adapter.match_nodes(cast(T_Node, root), source):
            target = decorator_adapter.get_target(decorator_node)
            # Only process if this decorator targets our current function
            if target and cast(_TreeNodeWithParentId, target.node).id == cast(_TreeNodeWithParentId, node.node).id:
                code_section_for_decorator = build_section_from_code(
                    adapter=decorator_adapter,
                    code_section_type=CodeSectionType.decorator,
                    source=source,
                    code=code,
                    node=decorator_node,
                    section_index=section_index,
                    parent=function_reference_string,
                    parent_id=section_segment.id,
                )

                # Build the decorator section
                decorator_section, decorator_child_sections = build_decorator_section(
                    adapter=decorator_adapter,
                    expression_adapter=expression_adapter,
                    code=code,
                    code_section=code_section_for_decorator,
                    node=decorator_node,
                    source=source,
                    section_index=section_index,
                )
                code_section_for_decorator.code_section_decorator = decorator_section
                code_section_function.code_section_decorators.append(decorator_section)
                child_sections.append(code_section_for_decorator)
                child_sections.extend(decorator_child_sections)
    return code_section_function, child_sections
