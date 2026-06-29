"""Code Builder."""

from typing import TypeVar, cast

# Code Models
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Content
from aware_content_ontology.part.content_part_text import ContentPartText

# Storage
from aware_storage_ontology.bucket.storage_bucket import StorageBucket

# Code
from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.tree.tree import CodeTree

# Code Section
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.builder import build_section_from_code
from aware_code.stable_ids import (
    stable_code_id,
    stable_code_package_code_id,
    stable_code_package_config_id,
    stable_code_package_id,
)

# Annotation
from aware_code.section.annotation.adapter import CodeSectionAnnotationAdapter
from aware_code.section.annotation.builder import build_annotation_section

# Binding
from aware_code.section.binding.adapter import CodeSectionBindingAdapter
from aware_code.section.binding.builder import build_binding_section

# Attribute
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.section.attribute.builder import (
    build_section_from_code_with_param_discriminator,
    build_attribute_section,
)

# Class
from aware_code.section.class_.adapter import CodeSectionClassAdapter
from aware_code.section.class_.builder import build_class_section

# Comment
from aware_code.section.comment.builder import build_comment_section
from aware_code.section.comment.adapter import CodeSectionCommentAdapter
from aware_code.section.comment.handlers import get_docstring

# Enum
from aware_code.section.enum.builder import build_enum_section
from aware_code.section.enum.adapter import CodeSectionEnumAdapter
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter

# Expression
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter

# Function
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.section.function.builder import build_function_section

# Import
from aware_code.section.import_.adapter import CodeSectionImportAdapter
from aware_code.section.import_.builder import build_import_section

# Mirror
from aware_code.section.mirror.adapter import CodeSectionMirrorAdapter
from aware_code.section.mirror.builder import build_mirror_section

# Projection
from aware_code.section.projection.adapter import CodeSectionProjectionAdapter
from aware_code.section.projection.builder import build_projection_section

# Decorator
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter

from aware_code.node.node import CodeNode
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.symbol_table import CodeSymbolTable

# Content Part Text Builders
from aware_content.builder import (
    build_content_part_text_inline,
    build_content_part_text_blob,
)

# Storage Blob
from aware_storage.blob_store import BlobStore

# Logging
from aware_utils.logging import logger

# Import the normalizer
from aware_utils.description_normalizer import DescriptionNormalizer

T_AdapterNode = TypeVar("T_AdapterNode")


def build_code_from_content(
    sections_index: CodeSectionBuilderIndex,
    content: str,
    code_key: str,
    language: CodeLanguage,
    symbol_table: CodeSymbolTable,
    bucket: StorageBucket | None = None,
    blob_store: BlobStore | None = None,
) -> Code:
    """
    Process single content string and extract code sections using multi-pass approach.

    Args:
        sections_index: Sections index to use for building sections
        content: Source code content
        language: Programming language of the content
        bucket: Optional bucket to use for storing code blobs
        blob_store: Optional blob store to use for storing code blobs
    Returns:
        Newly built Code instance
    """
    # Get the section builders
    language_plugin: CodeLanguagePlugin[object] = CodeLanguagePluginRegistry.get(
        language
    )

    # Parse content directly using enhanced tree-sitter adapter
    code_tree = language_plugin.tree_sitter_adapter.parse_content(content)
    if not code_tree:
        raise ValueError("Failed to parse content directly")

    return build_code_from_tree(
        sections_index,
        code_tree,
        code_key,
        language,
        symbol_table,
        bucket,
        blob_store,
    )


def build_code_from_file(
    sections_index: CodeSectionBuilderIndex,
    file_path: str,
    language: CodeLanguage,
    symbol_table: CodeSymbolTable,
    bucket: StorageBucket | None = None,
    blob_store: BlobStore | None = None,
    *,
    code_key: str | None = None,
) -> Code:
    # Get the language plugin
    language_plugin: CodeLanguagePlugin[object] = CodeLanguagePluginRegistry.get(
        language
    )

    # Parse file via tree-sitter
    code_tree = language_plugin.tree_sitter_adapter.parse(file_path)
    if not code_tree:
        if language_plugin.tree_sitter_adapter.is_empty_file_allowed(file_path):
            logger.debug(f"Skipping empty file: {file_path}")
            raise ValueError(f"File is empty: {file_path}")
        else:
            logger.warning(f"Failed to parse file: {file_path}")
            raise ValueError(f"Failed to parse file: {file_path}")

    return build_code_from_tree(
        sections_index,
        code_tree,
        code_key or file_path,
        language,
        symbol_table,
        bucket,
        blob_store,
    )


def build_code_from_tree(
    sections_index: CodeSectionBuilderIndex,
    code_tree: CodeTree[T_AdapterNode],
    code_key: str,
    language: CodeLanguage,
    symbol_table: CodeSymbolTable,
    bucket: StorageBucket | None = None,
    blob_store: BlobStore | None = None,
) -> Code:
    # Get the section builders
    language_plugin: CodeLanguagePlugin[T_AdapterNode] = (
        CodeLanguagePluginRegistry.get_typed(language)
    )

    # Create a code object for this content
    if bucket and blob_store:
        code = create_from_blob(
            content=code_tree.text,
            code_key=code_key,
            bucket=bucket,
            blob_store=blob_store,
            language=language,
        )
    else:
        code = create_from_text(
            text=code_tree.text,
            code_key=code_key,
            language=language,
        )

    # Set virtual file path for section processing
    virtual_path = f"content.{language.value}"
    sections_index.set_code_path_mapping(code.id, virtual_path)

    # Build import sections
    if CodeSectionType.import_ in language_plugin.node_adapters:
        import_adapter = cast(
            CodeSectionImportAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.import_],
        )
        import_nodes = collect_nodes(import_adapter, code_tree)

        for node in import_nodes:
            code_section = build_section_from_code(
                adapter=import_adapter,
                code_section_type=CodeSectionType.import_,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            import_section = build_import_section(
                adapter=import_adapter,
                code=code,
                code_section=code_section,
                node=node,
                symbol_table=symbol_table,
                blob_store=blob_store,
            )
            code_section.code_section_import = import_section
            code.code_sections.append(code_section)

    # Build mirror sections
    if CodeSectionType.mirror in language_plugin.node_adapters:
        mirror_adapter = cast(
            CodeSectionMirrorAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.mirror],
        )
        mirror_nodes = collect_nodes(mirror_adapter, code_tree)

        for node in mirror_nodes:
            code_section = build_section_from_code(
                adapter=mirror_adapter,
                code_section_type=CodeSectionType.mirror,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            mirror_section = build_mirror_section(
                adapter=mirror_adapter,
                code=code,
                code_section=code_section,
                node=node,
                blob_store=blob_store,
            )
            code_section.code_section_mirror = mirror_section
            code.code_sections.append(code_section)

    # Build projection sections
    if CodeSectionType.projection in language_plugin.node_adapters:
        projection_adapter = cast(
            CodeSectionProjectionAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.projection],
        )
        projection_nodes = collect_nodes(projection_adapter, code_tree)
        for node in projection_nodes:
            code_section = build_section_from_code(
                adapter=projection_adapter,
                code_section_type=CodeSectionType.projection,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            projection_section = build_projection_section(
                adapter=projection_adapter,
                code=code,
                code_section=code_section,
                node=node,
                source=code_tree.source_bytes,
                blob_store=blob_store,
            )
            code_section.code_section_projection = projection_section
            code.code_sections.append(code_section)

    # Build binding sections
    if CodeSectionType.binding in language_plugin.node_adapters:
        binding_adapter = cast(
            CodeSectionBindingAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.binding],
        )
        binding_nodes = collect_nodes(binding_adapter, code_tree)
        for node in binding_nodes:
            code_section = build_section_from_code(
                adapter=binding_adapter,
                code_section_type=CodeSectionType.binding,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            binding_section = build_binding_section(
                adapter=binding_adapter,
                code=code,
                code_section=code_section,
                node=node,
                source=code_tree.source_bytes,
                blob_store=blob_store,
            )
            code_section.code_section_binding = binding_section
            code.code_sections.append(code_section)

    # Build attribute sections
    if CodeSectionType.attribute in language_plugin.node_adapters:
        attribute_adapter = cast(
            CodeSectionAttributeAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.attribute],
        )
        attribute_nodes = collect_nodes(attribute_adapter, code_tree)
        for node in attribute_nodes:
            code_section = build_section_from_code_with_param_discriminator(
                adapter=attribute_adapter,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
                is_parameter=False,
                parent_ref=None,
                parent_id=None,
            )
            attribute_section = build_attribute_section(
                adapter=attribute_adapter,
                code=code,
                code_section=code_section,
                node=node,
                is_parameter=False,
                blob_store=blob_store,
            )
            code_section.code_section_attribute = attribute_section
            code.code_sections.append(code_section)

    # Build enum sections
    if CodeSectionType.enum in language_plugin.node_adapters:
        enum_adapter = cast(
            CodeSectionEnumAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.enum],
        )
        enum_value_adapter = cast(
            CodeSectionEnumValueAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.enum_value],
        )
        enum_nodes = collect_nodes(enum_adapter, code_tree)
        for node in enum_nodes:
            code_section = build_section_from_code(
                adapter=enum_adapter,
                code_section_type=CodeSectionType.enum,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            enum_section, enum_value_sections = build_enum_section(
                adapter=enum_adapter,
                enum_value_adapter=enum_value_adapter,
                code=code,
                code_section=code_section,
                node=node,
                source=code_tree.source_bytes,
                section_index=sections_index,
                blob_store=blob_store,
            )
            code_section.code_section_enum = enum_section
            code.code_sections.append(code_section)
            code.code_sections.extend(enum_value_sections)

    # Build function sections
    if CodeSectionType.function in language_plugin.node_adapters:
        function_adapter = cast(
            CodeSectionFunctionAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.function],
        )
        attribute_adapter = cast(
            CodeSectionAttributeAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.attribute],
        )
        raw_decorator_adapter = language_plugin.node_adapters.get(
            CodeSectionType.decorator
        )
        decorator_adapter: CodeSectionDecoratorAdapter[T_AdapterNode] | None = (
            cast(CodeSectionDecoratorAdapter[T_AdapterNode], raw_decorator_adapter)
            if raw_decorator_adapter
            else None
        )
        raw_expression_adapter = language_plugin.node_adapters.get(
            CodeSectionType.expression
        )
        expression_adapter: CodeSectionExpressionAdapter[T_AdapterNode] | None = (
            cast(CodeSectionExpressionAdapter[T_AdapterNode], raw_expression_adapter)
            if raw_expression_adapter
            else None
        )

        function_nodes = collect_nodes(function_adapter, code_tree)
        for node in function_nodes:
            code_section = build_section_from_code(
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
                adapter=function_adapter,
                code_section_type=CodeSectionType.function,
            )
            function_section, child_sections = build_function_section(
                adapter=function_adapter,
                attribute_adapter=attribute_adapter,
                code=code,
                code_section=code_section,
                node=node,
                source=code_tree.source_bytes,
                section_index=sections_index,
                decorator_adapter=decorator_adapter,
                expression_adapter=expression_adapter,
                blob_store=blob_store,
            )
            code_section.code_section_function = function_section
            code.code_sections.append(code_section)
            code.code_sections.extend(child_sections)

    # Build class sections
    if CodeSectionType.class_ in language_plugin.node_adapters:
        # Get the adapters required for the class section
        class_adapter = cast(
            CodeSectionClassAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.class_],
        )
        attribute_adapter = cast(
            CodeSectionAttributeAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.attribute],
        )
        function_adapter = cast(
            CodeSectionFunctionAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.function],
        )
        raw_decorator_adapter = language_plugin.node_adapters.get(
            CodeSectionType.decorator
        )
        class_decorator_adapter: CodeSectionDecoratorAdapter[T_AdapterNode] | None = (
            cast(CodeSectionDecoratorAdapter[T_AdapterNode], raw_decorator_adapter)
            if raw_decorator_adapter
            else None
        )
        raw_expression_adapter = language_plugin.node_adapters.get(
            CodeSectionType.expression
        )
        class_expression_adapter: CodeSectionExpressionAdapter[T_AdapterNode] | None = (
            cast(CodeSectionExpressionAdapter[T_AdapterNode], raw_expression_adapter)
            if raw_expression_adapter
            else None
        )

        class_nodes = collect_nodes(class_adapter, code_tree)
        for node in class_nodes:
            code_section = build_section_from_code(
                adapter=class_adapter,
                code_section_type=CodeSectionType.class_,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            class_section, child_sections = build_class_section(
                adapter=class_adapter,
                source=code_tree.source_bytes,
                section_index=sections_index,
                attribute_adapter=attribute_adapter,
                function_adapter=function_adapter,
                code=code,
                code_section=code_section,
                node=node,
                decorator_adapter=class_decorator_adapter,
                expression_adapter=class_expression_adapter,
                blob_store=blob_store,
            )
            code_section.code_section_class = class_section
            code.code_sections.append(code_section)
            code.code_sections.extend(child_sections)

    # Build annotation sections
    if CodeSectionType.annotation in language_plugin.node_adapters:
        annotation_adapter = cast(
            CodeSectionAnnotationAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.annotation],
        )
        annotation_nodes = collect_nodes(annotation_adapter, code_tree)
        for node in annotation_nodes:
            code_section = build_section_from_code(
                adapter=annotation_adapter,
                code_section_type=CodeSectionType.annotation,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            annotation_section = build_annotation_section(
                adapter=annotation_adapter,
                code_section=code_section,
                node=node,
            )
            code_section.code_section_annotation = annotation_section
            code.code_sections.append(code_section)

    # Build comment sections
    if CodeSectionType.comment in language_plugin.node_adapters:
        comment_adapter = cast(
            CodeSectionCommentAdapter[T_AdapterNode],
            language_plugin.node_adapters[CodeSectionType.comment],
        )
        raw_enum_adapter = language_plugin.node_adapters.get(CodeSectionType.enum)
        comment_enum_adapter: CodeSectionEnumAdapter[T_AdapterNode] | None = (
            cast(CodeSectionEnumAdapter[T_AdapterNode], raw_enum_adapter)
            if raw_enum_adapter
            else None
        )
        raw_class_adapter = language_plugin.node_adapters.get(CodeSectionType.class_)
        comment_class_adapter: CodeSectionClassAdapter[T_AdapterNode] | None = (
            cast(CodeSectionClassAdapter[T_AdapterNode], raw_class_adapter)
            if raw_class_adapter
            else None
        )
        raw_function_adapter = language_plugin.node_adapters.get(
            CodeSectionType.function
        )
        comment_function_adapter: CodeSectionFunctionAdapter[T_AdapterNode] | None = (
            cast(CodeSectionFunctionAdapter[T_AdapterNode], raw_function_adapter)
            if raw_function_adapter
            else None
        )
        raw_attribute_adapter = language_plugin.node_adapters.get(
            CodeSectionType.attribute
        )
        comment_attribute_adapter: CodeSectionAttributeAdapter[T_AdapterNode] | None = (
            cast(CodeSectionAttributeAdapter[T_AdapterNode], raw_attribute_adapter)
            if raw_attribute_adapter
            else None
        )
        raw_projection_adapter = language_plugin.node_adapters.get(
            CodeSectionType.projection
        )
        comment_projection_adapter: (
            CodeSectionProjectionAdapter[T_AdapterNode] | None
        ) = (
            cast(CodeSectionProjectionAdapter[T_AdapterNode], raw_projection_adapter)
            if raw_projection_adapter
            else None
        )
        comment_nodes = collect_nodes(comment_adapter, code_tree)
        for node in comment_nodes:
            code_section = build_section_from_code(
                adapter=comment_adapter,
                code_section_type=CodeSectionType.comment,
                source=code_tree.source_bytes,
                code=code,
                node=node,
                section_index=sections_index,
            )
            comment_section = build_comment_section(
                adapter=comment_adapter,
                code=code,
                code_section=code_section,
                node=node,
                source=code_tree.source_bytes,
                section_index=sections_index,
                enum_adapter=comment_enum_adapter,
                class_adapter=comment_class_adapter,
                function_adapter=comment_function_adapter,
                attribute_adapter=comment_attribute_adapter,
                projection_adapter=comment_projection_adapter,
            )
            code_section.code_section_comment = comment_section
            code.code_sections.append(code_section)

    # Rebuild code sections docstrings after comments have been built
    for code_section in code.code_sections:
        if code_section.type is CodeSectionType.enum:
            if not code_section.code_section_enum:
                raise ValueError(
                    f"Code section enum is not found for code section {code_section.id}"
                )
            code_section.code_section_enum.description = get_clean_description(
                language_plugin,
                CodeSectionType.enum,
                get_docstring(
                    code_section.code_section_enum.code_section_comments,
                    blob_store=blob_store,
                ),
            )
        elif code_section.type is CodeSectionType.enum_value:
            if not code_section.code_section_enum_value:
                raise ValueError(
                    f"Code section enum value is not found for code section {code_section.id}"
                )
            code_section.code_section_enum_value.description = get_clean_description(
                language_plugin,
                CodeSectionType.enum_value,
                get_docstring(
                    code_section.code_section_enum_value.code_section_comments,
                    blob_store=blob_store,
                ),
            )
        elif code_section.type is CodeSectionType.class_:
            if not code_section.code_section_class:
                raise ValueError(
                    f"Code section class is not found for code section {code_section.id}"
                )
            code_section.code_section_class.description = get_clean_description(
                language_plugin,
                CodeSectionType.class_,
                get_docstring(
                    code_section.code_section_class.code_section_comments,
                    blob_store=blob_store,
                ),
            )
        elif code_section.type is CodeSectionType.function:
            if not code_section.code_section_function:
                raise ValueError(
                    f"Code section function is not found for code section {code_section.id}"
                )
            code_section.code_section_function.description = get_clean_description(
                language_plugin,
                CodeSectionType.function,
                get_docstring(
                    code_section.code_section_function.code_section_comments,
                    blob_store=blob_store,
                ),
            )
        elif code_section.type is CodeSectionType.attribute:
            if not code_section.code_section_attribute:
                raise ValueError(
                    f"Code section attribute is not found for code section {code_section.id}"
                )
            code_section.code_section_attribute.description = get_clean_description(
                language_plugin,
                CodeSectionType.attribute,
                get_docstring(
                    code_section.code_section_attribute.code_section_comments,
                    blob_store=blob_store,
                ),
            )
        elif code_section.type is CodeSectionType.projection:
            if not code_section.code_section_projection:
                raise ValueError(
                    f"Code section projection is not found for code section {code_section.id}"
                )
            code_section.code_section_projection.description = get_clean_description(
                language_plugin,
                CodeSectionType.projection,
                get_docstring(
                    code_section.code_section_projection.code_section_comments,
                    blob_store=blob_store,
                ),
            )
    logger.debug(f"Processed content with {len(code.code_sections)} sections")
    return code


def build_code(
    content_part_text: ContentPartText,
    code_key: str,
    language: CodeLanguage | None = None,
) -> Code:
    """
    Build a Code object from a ContentPartText.

    Args:
        content_part_text: ContentPartText object (already built)
        language: Programming language of the code

    Returns:
        Newly built Code instance
    """
    normalized_code_key = (code_key or "").strip()
    resolved_language = language.value if language is not None else "unknown"
    synthetic_package_id = stable_code_package_id(
        code_package_config_id=stable_code_package_config_id(
            config_key="synthetic:builder",
        ),
        package_name=f"__aware_builder__.{resolved_language}:{normalized_code_key.casefold()}",
        language=resolved_language,
    )
    synthetic_code_package_code_id = stable_code_package_code_id(
        code_package_id=synthetic_package_id,
        relative_path=normalized_code_key,
    )

    # Create a deterministic synthetic Code shell for non-canonical builder usage.
    code = Code(
        id=stable_code_id(
            code_package_code_id=synthetic_code_package_code_id,
            relative_path=normalized_code_key,
        ),
        code_package_code_id=synthetic_code_package_code_id,
        relative_path=normalized_code_key,
        content_part_text_id=content_part_text.id,
        content_part_text=content_part_text,
        language=language,
    )
    return code


def create_from_text(
    text: str, code_key: str, language: CodeLanguage | None = None
) -> Code:
    """
    Create a Code object from text content.

    Args:
        text: The source code text
        language: The programming language

    Returns:
        New Code instance
    """
    content_part_text = build_content_part_text_inline(inline_text=text)
    return build_code(
        content_part_text=content_part_text, code_key=code_key, language=language
    )


def create_from_blob(
    content: str,
    code_key: str,
    bucket: StorageBucket,
    blob_store: BlobStore,
    language: CodeLanguage | None = None,
) -> Code:
    """
    Create a Code object from content.

    Args:
        content: Text content for the code
        bucket: Storage bucket to use for blob creation
        blob_store: Blob store to use for blob creation
        language: Programming language of the code

    Returns:
        New Code instance
    """
    content_part_text = build_content_part_text_blob(
        content=content, bucket=bucket, blob_store=blob_store
    )
    code = build_code(
        content_part_text=content_part_text, code_key=code_key, language=language
    )
    logger.debug(
        f"Created Code {code.id} for language {language.value if language else 'None'}"
    )
    return code


def collect_nodes(
    adapter: CodeNodeAdapter[T_AdapterNode],
    code_tree: CodeTree[T_AdapterNode],
) -> list[CodeNode[T_AdapterNode]]:
    nodes = list(adapter.match_nodes(code_tree.root.node, code_tree.source_bytes))
    nodes.sort(key=lambda n: n.byte_start)
    return nodes


def get_clean_description(
    language_plugin: CodeLanguagePlugin[T_AdapterNode],
    section_type: CodeSectionType,
    raw_docstring: str | None,
) -> str | None:
    """
    Extract clean description using language-specific metadata adapters.

    Args:
        section_type: Type of code section (CLASS, FUNCTION, etc.)
        raw_docstring: Raw docstring/comment text

    Returns:
        Clean description with metadata stripped out
    """
    if not raw_docstring:
        return None

    # Use metadata adapter to extract clean description
    metadata_adapter = language_plugin.metadata_adapters.get(section_type)
    if not metadata_adapter:
        # No metadata adapter for this section type, normalize and return raw
        return DescriptionNormalizer.normalize_description(raw_docstring)

    # Extract metadata and get clean description
    section_metadata = metadata_adapter.from_raw_comment(raw_docstring)
    description = section_metadata.description

    # Check if the metadata adapter indicates it needs additional normalization
    if not section_metadata.requires_normalization:
        # This metadata adapter preserves formatting - don't normalize further
        return description
    else:
        # Apply additional normalization to ensure consistency
        return DescriptionNormalizer.normalize_description(description)
