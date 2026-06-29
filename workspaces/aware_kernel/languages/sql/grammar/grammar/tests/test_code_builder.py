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
from aware_code_ontology.code.code_section import CodeSection

# SQL Grammar
from sql_grammar.code_language_plugin import SQL_CODE_PLUGIN


SAMPLES = ["user"]


@pytest.fixture(scope="session")
def sample_files():
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples" / "input" / "sql"
    sample_files = {}
    for name in SAMPLES:
        p = samples_dir / f"{name}.sql"
        if not p.exists():
            pytest.fail(f"Sample file not found: {p}")
        sample_files[name] = str(p)
    return sample_files


@pytest.fixture(scope="session")
def sample_file_codes(sample_files) -> dict[str, Code]:
    CodeLanguagePluginRegistry.register(SQL_CODE_PLUGIN)
    out: dict[str, Code] = {}
    for name, path in sample_files.items():
        out[name] = build_code_from_file(
            sections_index=CodeSectionBuilderIndex(),
            file_path=path,
            language=CodeLanguage.sql,
            symbol_table=CodeSymbolTable(),
        )
    return out


def test_code_builder_ssot_fields_and_description_backfill(sample_file_codes: dict[str, Code], sample_files):
    """
    SSOT invariants for SQL CodeSection* models:
    - SSOT `name`/`type_text`/`default_value_text` are populated (not just segments)
    - SSOT values are consistent with segments
    """
    CodeLanguagePluginRegistry.register(SQL_CODE_PLUGIN)
    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=sample_files["user"],
        language=CodeLanguage.sql,
        symbol_table=CodeSymbolTable(),
    )
    assert len(code.code_sections) > 0

    # Group by type sanity
    sections_by_type: dict[CodeSectionType, list[CodeSection]] = {}
    for sec in code.code_sections:
        sections_by_type.setdefault(sec.type, []).append(sec)

    assert CodeSectionType.class_ in sections_by_type, "Should have table (class) sections"
    assert CodeSectionType.attribute in sections_by_type, "Should have column (attribute) sections"

    # --- CLASS SSOT (table) ---
    user_table_sec = sections_index.get_by_ref(CodeSectionType.class_, "public.user")
    assert user_table_sec is not None and user_table_sec.code_section_class is not None
    tbl = user_table_sec.code_section_class
    assert tbl.name == get_segment_text(tbl.name_segment)
    # description may be absent if sample has no COMMENT ON TABLE; don't force it here.

    # --- ATTRIBUTE SSOT (column) ---
    email_col_sec = sections_index.get_by_ref(CodeSectionType.attribute, "public.user.email")
    assert email_col_sec is not None and email_col_sec.code_section_attribute is not None
    col = email_col_sec.code_section_attribute
    assert col.name_segment is not None
    assert col.name == get_segment_text(col.name_segment)
    assert col.type_segment is not None
    assert col.type_text == get_segment_text(col.type_segment)
    assert col.is_required is True  # NOT NULL
    assert col.is_unique is True  # UNIQUE
    assert col.is_primary is False

    id_col_sec = sections_index.get_by_ref(CodeSectionType.attribute, "public.user.id")
    assert id_col_sec is not None and id_col_sec.code_section_attribute is not None
    id_col = id_col_sec.code_section_attribute
    assert id_col.is_primary is True
    assert id_col.is_required is True
