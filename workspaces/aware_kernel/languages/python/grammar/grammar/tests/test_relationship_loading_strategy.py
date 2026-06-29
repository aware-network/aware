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

# Python Grammar
from python_grammar.relationship_loading_filter import determine_loading_from_attribute


DEFAULT_CONTENT = """
from pydantic import BaseModel, Field


class Profile(BaseModel):
    display_name: str


class Example(BaseModel):
    profile: Profile = Field(..., exclude=True)
    identity: Profile
"""


def test_python_relationship_loading_filter():
    code = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=DEFAULT_CONTENT.strip(),
        code_key="inline://python-relationship-loading",
        language=CodeLanguage.python,
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

    attribute_sections = {
        get_segment_text(attribute.name_segment): attribute
        for attribute in example_class.code_section_attributes
        if attribute is not None and attribute.name_segment is not None
    }
    assert "profile" in attribute_sections and "identity" in attribute_sections

    lazy_loading = determine_loading_from_attribute(attribute_sections["profile"])
    eager_loading = determine_loading_from_attribute(attribute_sections["identity"])

    assert lazy_loading == ClassConfigRelationshipSideLoadingStrategy.lazy
    assert eager_loading == ClassConfigRelationshipSideLoadingStrategy.eager
