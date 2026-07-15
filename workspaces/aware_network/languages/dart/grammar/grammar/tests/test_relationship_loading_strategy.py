# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.builder import build_code_from_content
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)

# Dart Grammar
from dart_grammar.relationship_loading_filter import determine_loading_from_attribute

DEFAULT_CONTENT = """
import 'package:json_annotation/json_annotation.dart';

class Example {
  final Profile eagerProfile;

  @JsonKey(includeFromJson: false, includeToJson: false)
  final Profile lazyProfile;
}
"""


def test_dart_relationship_loading_filter():
    code = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=DEFAULT_CONTENT.strip(),
        code_key="inline://dart-relationship-loading",
        language=CodeLanguage.dart,
        symbol_table=CodeSymbolTable(),
    )
    assert code is not None

    example_class = next(
        section.code_section_class
        for section in code.code_sections
        if section.type == CodeSectionType.class_
        and section.code_section_class is not None
        and get_segment_text(section.code_section_class.name_segment) == "Example"
    )

    attrs = {
        get_segment_text(attribute.name_segment): attribute
        for attribute in example_class.code_section_attributes
        if attribute is not None and attribute.name_segment is not None
    }
    eager_attr = attrs.get("eagerProfile")
    lazy_attr = attrs.get("lazyProfile")
    assert eager_attr is not None and lazy_attr is not None

    eager_loading = determine_loading_from_attribute(eager_attr)
    lazy_loading = determine_loading_from_attribute(lazy_attr)

    assert eager_loading == ClassConfigRelationshipSideLoadingStrategy.eager
    assert lazy_loading == ClassConfigRelationshipSideLoadingStrategy.lazy
