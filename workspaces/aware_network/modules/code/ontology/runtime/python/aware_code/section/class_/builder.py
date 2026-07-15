"""Builder for constructing CodeSectionClass instances from source code."""

from typing import Protocol, cast

# Kernel Graph Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.class_.code_section_class_attribute import (
    CodeSectionClassAttribute,
)
from aware_code_ontology.class_.code_section_class_function import (
    CodeSectionClassFunction,
)
from aware_code_ontology.class_.code_section_class_base import CodeSectionClassBase
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.section.builder import build_section_from_code, make_identity_hash
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.section.attribute.builder import (
    build_section_from_code_with_param_discriminator,
    build_attribute_section,
)
from aware_code.section.class_.adapter import CodeSectionClassAdapter
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter
from aware_code.section.decorator.builder import build_decorator_section
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.section.function.builder import build_function_section

# Aware Storage
from aware_storage.blob_store import BlobStore


class _TreeNodeWithParentId(Protocol):
    parent: "_TreeNodeWithParentId | None"
    id: object


def build_class_section(
    adapter: CodeSectionClassAdapter[T_Node],
    attribute_adapter: CodeSectionAttributeAdapter[T_Node],
    function_adapter: CodeSectionFunctionAdapter[T_Node],
    code: Code,
    code_section: CodeSection,
    node: CodeNode[T_Node],
    source: bytes,
    section_index: CodeSectionBuilderIndex,
    decorator_adapter: CodeSectionDecoratorAdapter[T_Node] | None = None,
    expression_adapter: CodeSectionExpressionAdapter[T_Node] | None = None,
    blob_store: BlobStore | None = None,
    parent_ref: str | None = None,
) -> tuple[CodeSectionClass, list[CodeSection]]:
    """
    Build a CodeSectionClass instance from the provided node.

    NOTE: This builder constructs the class section and all its nested sections (attributes, functions and decorators).

    Args:
        adapter: The adapter to use for the class section
        attribute_adapter: The adapter to use for the attribute section
        function_adapter: The adapter to use for the function section
        decorator_adapter: The adapter to use for the decorator section
        code: The code object
        code_section: The code section to build
        node: The node to build the section from
        source: Source code bytes
        section_index: Shared index of sections for cross-references
        parent_ref: Optional parent name to prepend to the qualname
    """
    # Get the section segment
    section_segment = code_section.content_part_text_segment

    # Get qualified name
    qualname = adapter.qualname(node, parent=parent_ref)

    reference_string = adapter.reference_string(node, parent=parent_ref)

    # Get the class name
    name_node = adapter.get_name(node)
    name_segment = ContentPartTextSegment(
        content_part_text=code.content_part_text,
        byte_start=name_node.byte_start,
        byte_end=name_node.byte_end,
        parent_id=section_segment.id,
    )
    name = get_segment_text(content_part_text_segment=name_segment, blob_store=blob_store)

    # Get the keyword segment if present
    keyword_segment: ContentPartTextSegment | None = None
    keyword_node = adapter.get_keyword(node)
    if keyword_node:
        keyword_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=keyword_node.byte_start,
            byte_end=keyword_node.byte_end,
            parent_id=section_segment.id,
        )

    # Get the modifiers segment if present
    modifiers_segment: ContentPartTextSegment | None = None
    modifiers_nodes = list(adapter.get_modifiers(node))
    if modifiers_nodes:
        # Create a segment that spans all modifier nodes
        min_start = min(mod_node.byte_start for mod_node in modifiers_nodes)
        max_end = max(mod_node.byte_end for mod_node in modifiers_nodes)
        modifiers_segment = ContentPartTextSegment(
            content_part_text=code.content_part_text,
            byte_start=min_start,
            byte_end=max_end,
            parent_id=section_segment.id,
        )

    # Get the verb if present
    verb: str | None = None
    verb_target: str | None = None
    verb_node = adapter.get_verb(node)
    if verb_node:
        verb = verb_node.node_text()
        verb_target_node = adapter.get_verb_target(node)
        if verb_target_node:
            verb_target = verb_target_node.node_text()
        else:
            raise ValueError(f"Found verb {verb} but no verb target")

    # Get the class flags
    is_edge = adapter.is_edge(node)
    is_inline_value = adapter.is_inline_value(node)

    # Create the class section
    class_section = CodeSectionClass(
        code_section=code_section,
        name=name,
        verb=verb,
        verb_target=verb_target,
        is_edge=is_edge,
        is_inline_value=is_inline_value,
        name_segment_id=name_segment.id,
        name_segment=name_segment,
        keyword_segment=keyword_segment,
        modifiers_segment=modifiers_segment,
    )
    code_section.code_section_class = class_section

    # Get base nodes
    base_nodes = list(adapter.get_bases(node))
    if base_nodes:
        base_nodes.sort(key=lambda n: n.byte_start)
        is_augment = adapter.is_augment(node)
        for base_node in base_nodes:
            base_segment = ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=base_node.byte_start,
                byte_end=base_node.byte_end,
                parent_id=section_segment.id,
            )
            base_ref = get_segment_text(content_part_text_segment=base_segment, blob_store=blob_store)
            class_section.code_section_class_bases.append(
                CodeSectionClassBase(
                    code_section_class_id=class_section.id,
                    base_ref=base_ref,
                    is_augment=is_augment,
                    segment_id=base_segment.id,
                    segment=base_segment,
                )
            )

    child_sections: list[CodeSection] = []

    attr_nodes = list(adapter.get_attributes(node))
    # Ensure deterministic attribute ordering based on source position
    attr_nodes.sort(key=lambda n: n.byte_start)
    attr_index = len(class_section.code_section_class_attributes)

    for attr_node in attr_nodes:
        # Calculate identity hash for this attribute
        attr_qualname = attribute_adapter.qualname_for_role(
            attr_node,
            is_parameter=False,
            parent=qualname,
        )
        attr_body = attribute_adapter.body_bytes(attr_node, source)
        attr_hash = make_identity_hash(
            code_section_type=CodeSectionType.attribute,
            code_id=code.id,
            qualname=attr_qualname,
            body_bytes=attr_body,
        )
        # Find attribute in section index
        code_section_for_attribute = section_index.get_by_hash(CodeSectionType.attribute, attr_hash)

        if code_section_for_attribute is None:
            code_section_for_attribute = build_section_from_code_with_param_discriminator(
                adapter=attribute_adapter,
                source=source,
                code=code,
                node=attr_node,
                section_index=section_index,
                parent_ref=reference_string,
                parent_id=section_segment.id,
                is_parameter=False,
            )
            built_attr_section = build_attribute_section(
                adapter=attribute_adapter,
                code=code,
                code_section=code_section_for_attribute,
                node=attr_node,
                is_parameter=False,
                blob_store=blob_store,
            )
            code_section_for_attribute.code_section_attribute = built_attr_section

        child_sections.append(code_section_for_attribute)
        resolved_attr_section = code_section_for_attribute.code_section_attribute
        if resolved_attr_section is None:
            raise ValueError("Unable to retrieve/build attribute section")

        # Link the attribute to this class with canonical position
        code_section_class_attribute = CodeSectionClassAttribute(
            code_section_class_id=class_section.id,
            code_section_attribute_id=resolved_attr_section.id,
            code_section_attribute=resolved_attr_section,
            position=attr_index,
        )
        class_section.code_section_class_attributes.append(code_section_class_attribute)
        attr_index += 1

    # Process methods
    method_index = len(class_section.code_section_class_functions)
    method_nodes = list(adapter.get_methods(node))
    # Ensure deterministic ordering by source position irrespective of adapter capture order.
    method_nodes.sort(key=lambda n: n.byte_start)
    for method_node in method_nodes:
        if function_adapter:
            # Calculate identity hash for this method
            method_qualname = function_adapter.qualname(method_node, parent=name)
            method_body = function_adapter.body_bytes(method_node, source)
            method_hash = make_identity_hash(
                code_section_type=CodeSectionType.function,
                code_id=code.id,
                qualname=method_qualname,
                body_bytes=method_body,
            )

            # Find or build the function section
            code_section_for_function = section_index.get_by_hash(CodeSectionType.function, method_hash)
            if code_section_for_function is None:
                code_section_for_function = build_section_from_code(
                    adapter=function_adapter,
                    code_section_type=CodeSectionType.function,
                    source=source,
                    code=code,
                    node=method_node,
                    section_index=section_index,
                    parent=name,
                    parent_id=section_segment.id,
                )
                method_section, method_child_sections = build_function_section(
                    adapter=function_adapter,
                    attribute_adapter=attribute_adapter,
                    code=code,
                    code_section=code_section_for_function,
                    node=method_node,
                    source=source,
                    section_index=section_index,
                    decorator_adapter=decorator_adapter,
                    expression_adapter=expression_adapter,
                    blob_store=blob_store,
                    parent_ref=name,
                )
                code_section_for_function.code_section_function = method_section
                child_sections.extend(method_child_sections)

            child_sections.append(code_section_for_function)
            resolved_method_section = code_section_for_function.code_section_function
            if resolved_method_section is None:
                raise ValueError("Unable to retrieve/build function section")

            # Link the method to this class
            code_section_class_function = CodeSectionClassFunction(
                code_section_class_id=class_section.id,
                code_section_function_id=resolved_method_section.id,
                code_section_function=resolved_method_section,
                position=method_index,
            )
            class_section.code_section_class_functions.append(code_section_class_function)
            method_index += 1

    # Process decorators if decorator adapter is available
    if decorator_adapter is not None:
        if expression_adapter is None:
            raise ValueError("Expression adapter is required to build decorators")
        # Get the module-root
        root = cast(_TreeNodeWithParentId, node.node)
        while root.parent:
            root = root.parent

        # Find decorators for this class
        for decorator_node in decorator_adapter.match_nodes(cast(T_Node, root), source):
            target = decorator_adapter.get_target(decorator_node)
            # Only process if this decorator targets our current class
            if target and cast(_TreeNodeWithParentId, target.node).id == cast(_TreeNodeWithParentId, node.node).id:
                code_section_for_decorator = build_section_from_code(
                    adapter=decorator_adapter,
                    code_section_type=CodeSectionType.decorator,
                    source=source,
                    code=code,
                    node=decorator_node,
                    section_index=section_index,
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
                class_section.code_section_decorators.append(decorator_section)
                child_sections.append(code_section_for_decorator)
                child_sections.extend(decorator_child_sections)
    return class_section, child_sections
