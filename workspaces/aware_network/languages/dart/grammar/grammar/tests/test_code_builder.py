import pytest
from pathlib import Path


# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Dart Grammar
from dart_grammar.code_language_plugin import DART_CODE_PLUGIN
from dart_grammar.type_descriptor_adapter import DartTypeDescriptorAdapter

SAMPLES = ["user_post"]


@pytest.fixture(scope="session")
def sample_files():
    """Fixture that returns the path to the sample Python file."""
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    sample_files = {}
    for sample_name in SAMPLES:
        sample_file = samples_dir / f"{sample_name}.dart"
        if not sample_file.exists():
            pytest.fail(f"Sample file not found: {sample_file}")
        sample_files[sample_name] = str(sample_file)
    return sample_files


@pytest.fixture(scope="session")
def sample_file_codes(sample_files):
    """Fixture that returns the file codes for the sample file."""
    CodeLanguagePluginRegistry.register(DART_CODE_PLUGIN)
    sample_file_codes = {}
    for sample_name, sample_file in sample_files.items():
        code = build_code_from_file(
            sections_index=CodeSectionBuilderIndex(),
            file_path=sample_file,
            code_key=sample_file,
            language=CodeLanguage.dart,
            symbol_table=CodeSymbolTable(),
        )
        sample_file_codes[sample_name] = code
    return sample_file_codes


def test_integrated_builder(sample_file_codes: dict[str, Code]):
    sample_name = "user_post"
    code = sample_file_codes[sample_name]
    assert code is not None

    # Basic adapter/factory sanity check
    adapter = DartTypeDescriptorAdapter()
    node = adapter.parse_type("List<String>")
    assert node.kind.name.lower() == "collection"

    # !! TODO: MOVE TO META Attribute Type Descriptor Factory tests.
    # factory = AttributeTypeDescriptorFactory(DART_CODE_PLUGIN, [EnumConfig(name="Status")])
    # desc = factory.build("String?")
    # assert desc.kind == Kind.UNION


def test_code_builder_ssot_fields_and_description_backfill(sample_files):
    """
    SSOT invariants for CodeSection* models:
    - SSOT `name`/`type_text`/`default_value_text` are populated (not just segments)
    - SSOT values are consistent with segments
    - `description` is backfilled after comment linkage for key entities
    """
    CodeLanguagePluginRegistry.register(DART_CODE_PLUGIN)
    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=sample_files["user_post"],
        code_key=sample_files["user_post"],
        language=CodeLanguage.dart,
        symbol_table=CodeSymbolTable(),
    )
    assert len(code.code_sections) > 0

    # --- CLASS SSOT ---
    user_sec = sections_index.get_by_ref(CodeSectionType.class_, "User")
    assert user_sec is not None and user_sec.code_section_class is not None
    user_cls = user_sec.code_section_class
    assert user_cls.name == get_segment_text(user_cls.name_segment)
    # Dart doc comments should backfill into description
    assert user_cls.description is not None

    # --- ENUM SSOT ---
    status_sec = sections_index.get_by_ref(CodeSectionType.enum, "Status")
    assert status_sec is not None and status_sec.code_section_enum is not None
    status_enum = status_sec.code_section_enum
    assert status_enum.name == get_segment_text(status_enum.name_segment)
    assert status_enum.description is not None and "status" in status_enum.description.lower()

    # --- FUNCTION SSOT ---
    fn_sec = sections_index.get_by_ref(CodeSectionType.function, "User.getFullName")
    assert fn_sec is not None and fn_sec.code_section_function is not None
    fn = fn_sec.code_section_function
    assert fn.name == get_segment_text(fn.name_segment)
    assert fn.description is not None and "full name" in fn.description.lower()
    assert fn.is_public is True

    # --- ATTRIBUTE SSOT ---
    attr_sec = sections_index.get_by_ref(CodeSectionType.attribute, "User.profilePicture")
    assert attr_sec is not None and attr_sec.code_section_attribute is not None
    attr = attr_sec.code_section_attribute
    assert attr.name == get_segment_text(attr.name_segment)
    assert attr.type_segment is not None
    assert attr.type_text == get_segment_text(attr.type_segment)
    assert "Image" in (attr.type_text or "")
    assert attr.is_public is True
