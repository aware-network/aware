import pytest
from pathlib import Path

# Kernel Graph Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.builder import build_code_from_content
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder import build_section_from_code
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Content
from aware_content.builder import get_segment_text

# Aware Grammar
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN


SAMPLES = ["user_post", "nested_attributes", "augment", "association_relationship", "many_to_many"]


@pytest.fixture(scope="session")
def sample_files() -> dict[str, str]:
    """Fixture that returns the path to the sample Aware file."""
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    sample_files: dict[str, str] = {}
    for sample_name in SAMPLES:
        sample_file = samples_dir / f"{sample_name}.aware"
        if not sample_file.exists():
            pytest.fail(f"Sample file not found: {sample_file}")
        sample_files[sample_name] = str(sample_file)
    return sample_files


@pytest.fixture(scope="session")
def sample_file_codes(sample_files: dict[str, str]) -> dict[str, tuple[Code, CodeSectionBuilderIndex]]:
    """Fixture that returns the file codes for the sample file."""
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]] = {}
    for sample_name, sample_file in sample_files.items():
        sections_index = CodeSectionBuilderIndex()
        code = build_code_from_file(
            sections_index=sections_index,
            file_path=sample_file,
            language=CodeLanguage.aware,
            symbol_table=CodeSymbolTable(),
        )
        sample_file_codes[sample_name] = (code, sections_index)
    return sample_file_codes


def test_code_builder_from_file(sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]]):
    """Test the integrated code building process with all adapters."""
    code, _sections_index = sample_file_codes["user_post"]

    # Validate code sections
    sections_by_type: dict[CodeSectionType, list[CodeSection]] = {}
    for section in code.code_sections:
        if section.type not in sections_by_type:
            sections_by_type[section.type] = []
        sections_by_type[section.type].append(section)

    # Check class sections (classes + edges)
    assert CodeSectionType.class_ in sections_by_type, "Should have class sections"
    assert len(sections_by_type[CodeSectionType.class_]) == 6, "Should have 6 class sections (4 classes + 2 edges)"

    # Check function sections (both standalone and methods)
    assert CodeSectionType.function in sections_by_type, "Should have function sections"

    # Check attribute sections (as part of classes, not standalone)
    # Get a class section and check if it has attribute children
    class_section = sections_by_type[CodeSectionType.class_][0]
    assert class_section.code_section_class is not None, "Should have a code_section_class"
    assert (
        len(class_section.code_section_class.code_section_attributes) > 0
    ), "Should have attribute sections as part of classes"


def test_code_builder_binds_doc_comments_to_enum_value_sections() -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_content(
        sections_index=sections_index,
        content="""\
enum Foo {
    /// First
    a
    b
}
""",
        code_key="test:aware:enum-foo",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    value_sections = [s for s in code.code_sections if s.type is CodeSectionType.enum_value]
    assert {s.qualname for s in value_sections} == {"Foo.a", "Foo.b"}

    sec_a = sections_index.get_by_ref(CodeSectionType.enum_value, "Foo.a")
    assert sec_a is not None
    assert sec_a.code_section_enum_value is not None
    assert sec_a.code_section_enum_value.value == "a"
    assert sec_a.code_section_enum_value.description == "First"
    assert len(sec_a.code_section_enum_value.code_section_comments) == 1

    sec_b = sections_index.get_by_ref(CodeSectionType.enum_value, "Foo.b")
    assert sec_b is not None
    assert sec_b.code_section_enum_value is not None
    assert sec_b.code_section_enum_value.value == "b"
    assert sec_b.code_section_enum_value.description is None
    assert len(sec_b.code_section_enum_value.code_section_comments) == 0


def test_code_builder_does_not_materialize_program_sections() -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    from tree_sitter import Parser
    from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

    sections_index = CodeSectionBuilderIndex()
    content = """\
program KernelSeed {
    // v0: restricted statement grammar (let/call).
    let public_key = "ed25519:..."
    call identity.Identity.signup(public_key=public_key, type=human)
}
"""

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(content.encode("utf-8"))
    assert not tree.root_node.has_error, "Expected program source to parse without errors"

    code = build_code_from_content(
        sections_index=sections_index,
        content=content,
        code_key="test:aware:program-kernelseed",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    assert {section.type for section in code.code_sections}.isdisjoint(
        {
            getattr(CodeSectionType, "program", None),
            getattr(CodeSectionType, "event", None),
        }
    )


def test_code_builder_binds_doc_comments_to_projection_sections() -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_content(
        sections_index=sections_index,
        content="""\
class Wallet {}

/// Wallet projection.
/// Holds balances and transactions.
projection Wallet {
    root test.Wallet
}
""",
        code_key="test:aware:projection-wallet",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    _ = code  # keep symmetry with other builder tests

    proj_sec = sections_index.get_by_ref(CodeSectionType.projection, "projection:Wallet")
    assert proj_sec is not None
    assert proj_sec.code_section_projection is not None

    assert proj_sec.code_section_projection.description == (
        "Wallet projection.\nHolds balances and transactions."
    )
    assert len(proj_sec.code_section_projection.code_section_comments) == 1

    comment = proj_sec.code_section_projection.code_section_comments[0]
    assert comment.code_section_projection_id == proj_sec.code_section_projection.id


def test_code_builder_binding_sections_capture_maps_and_docstring_descriptions() -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_content(
        sections_index=sections_index,
        content="""\
binding aware_home_api aware_home {
    map door_by_label door.DoorDevice home.Door.label {
        \"\"\"Resolve external door payload onto canonical Door.label.\"\"\"
        template {
            "device_id::{device_id}_provider::{provider}_label::{door_label}"
        }
    }
}
""",
        code_key="test:aware:binding-home",
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    _ = code

    binding_sec = sections_index.get_by_ref(CodeSectionType.binding, "binding:aware_home_api->aware_home")
    assert binding_sec is not None
    assert binding_sec.code_section_binding is not None
    assert binding_sec.code_section_binding.source_graph_ref == "aware_home_api"
    assert binding_sec.code_section_binding.target_graph_ref == "aware_home"
    assert len(binding_sec.code_section_binding.code_section_binding_maps) == 1

    binding_map = binding_sec.code_section_binding.code_section_binding_maps[0]
    assert binding_map.name == "door_by_label"
    assert binding_map.source_ref == "door.DoorDevice"
    assert binding_map.target_ref == "home.Door.label"
    assert binding_map.description == "Resolve external door payload onto canonical Door.label."
    assert binding_map.template_segment is not None
    assert binding_map.template_text == "device_id::{device_id}_provider::{provider}_label::{door_label}"


def test_code_builder_ref_lookup_and_class_method_linkage(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    Validate that builder correctly:
    - Registers ref keys in CodeSectionBuilderIndex for class methods and parameters
    - Links class -> method using CodeSectionClassFunction.code_section_function_id == CodeSectionFunction.id
    """
    code, sections_index = sample_file_codes["user_post"]

    # --- Ref lookup for class method ---
    method_ref = "User.buildUser"
    method_section = sections_index.get_by_ref(CodeSectionType.function, method_ref)
    assert method_section is not None, f"Expected ref lookup for FUNCTION {method_ref}"
    assert method_section.type == CodeSectionType.function
    assert method_section.qualname == method_ref
    assert method_section.code_section_function is not None

    # --- Class -> method linkage should reference CodeSectionFunction.id (not base CodeSection.id) ---
    user_section = sections_index.get_by_ref(CodeSectionType.class_, "User")
    assert user_section is not None, "Expected ref lookup for CLASS User"
    assert user_section.code_section_class is not None

    edges = user_section.code_section_class.code_section_class_functions
    assert len(edges) > 0, "Expected User to have method edges"

    build_user_edge = next(
        (e for e in edges if e.code_section_function.code_section.qualname == method_ref),
        None,
    )
    assert build_user_edge is not None, f"Expected to find class->method edge for {method_ref}"
    assert build_user_edge.code_section_function_id == build_user_edge.code_section_function.id

    # --- Parameter ref lookup for method parameter (email) ---
    param_ref = "User.buildUser.email"
    param_section = sections_index.get_by_ref(CodeSectionType.attribute, param_ref)
    assert param_section is not None, f"Expected ref lookup for ATTRIBUTE {param_ref}"
    assert param_section.type == CodeSectionType.attribute
    assert param_section.code_section_attribute is not None

    # --- Parameter ref lookup for top-level function parameters ---
    for ref in ["addUser.role", "addUser.isActive", "addUser.metadata"]:
        sec = sections_index.get_by_ref(CodeSectionType.attribute, ref)
        assert sec is not None, f"Expected ref lookup for ATTRIBUTE {ref}"
        assert sec.type == CodeSectionType.attribute
        assert sec.code_section_attribute is not None

    # Ensure code object retained sections (sanity)
    assert len(code.code_sections) > 0


def test_code_builder_builds_output_attributes_for_tuple_returns(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    Canonical: if a function exposes named return parameters (tuple return), the Code builder must
    materialize OUTPUT CodeSectionAttributes and link them via CodeSectionFunctionAttribute.is_output.
    """
    _code, sections_index = sample_file_codes["user_post"]

    fn_sec = sections_index.get_by_ref(CodeSectionType.function, "resolveUserArtifacts")
    assert fn_sec is not None
    assert fn_sec.code_section_function is not None
    fn = fn_sec.code_section_function

    # Return clause segment must exist (provenance)
    assert fn.return_type_segment is not None
    blob_store = sections_index.get_blob_store()
    assert get_segment_text(fn.return_type_segment, blob_store=blob_store) == "(user User, post Post, comment Comment)"

    edges = fn.code_section_function_attributes
    assert edges, "Expected function to have attribute edges (inputs and outputs)"

    input_edges = [e for e in edges if not e.is_output]
    output_edges = [e for e in edges if e.is_output]

    assert len(input_edges) == 1
    assert input_edges[0].code_section_attribute.name == "userId"

    assert len(output_edges) == 3
    output_edges = sorted(output_edges, key=lambda e: e.position)
    assert [e.code_section_attribute.name for e in output_edges] == ["user", "post", "comment"]
    assert [e.code_section_attribute.type_text for e in output_edges] == ["User", "Post", "Comment"]


def test_code_builder_builds_output_attribute_for_single_returns(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    Canonical: if a function exposes a single return type, the Code builder must
    materialize a synthetic OUTPUT attribute named `value` so downstream meta
    builders can type return values (no missing OUTPUT edges).
    """
    _code, sections_index = sample_file_codes["user_post"]

    fn_sec = sections_index.get_by_ref(CodeSectionType.function, "User.getFullName")
    assert fn_sec is not None
    assert fn_sec.code_section_function is not None
    fn = fn_sec.code_section_function

    assert fn.return_type_segment is not None
    blob_store = sections_index.get_blob_store()
    assert get_segment_text(fn.return_type_segment, blob_store=blob_store) == "String"

    edges = fn.code_section_function_attributes
    output_edges = [e for e in edges if e.is_output]
    assert len(output_edges) == 1
    assert output_edges[0].code_section_attribute.name == "value"
    assert output_edges[0].code_section_attribute.type_text == "String"


def test_code_builder_class_base_edges_for_augment(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    _code, sections_index = sample_file_codes["augment"]
    env_section = sections_index.get_by_ref(CodeSectionType.class_, "TerminalEnv")
    assert env_section is not None
    assert env_section.code_section_class is not None
    env = env_section.code_section_class
    assert env.verb == "augment"
    assert env.verb_target == "Terminal"
    assert len(env.code_section_class_bases) == 1
    base = env.code_section_class_bases[0]
    assert base.is_augment is True
    assert base.base_ref == "Terminal"


def test_code_builder_attribute_relationship_hints_edge_spec_and_many_to_many(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    # Edge spec name should be extracted from `@EdgeSpec`
    _code, sections_index = sample_file_codes["association_relationship"]
    classes_attr = sections_index.get_by_ref(CodeSectionType.attribute, "ObjectConfigSample.classes")
    assert classes_attr is not None
    assert classes_attr.code_section_attribute is not None
    assert classes_attr.code_section_attribute.edge_spec_name == "ObjectClassEdge"
    assert classes_attr.code_section_attribute.is_many_to_many is False

    # many-to-many should be extracted from `many` modifier
    _code, sections_index = sample_file_codes["many_to_many"]
    users_attr = sections_index.get_by_ref(CodeSectionType.attribute, "Membership.users")
    assert users_attr is not None
    assert users_attr.code_section_attribute is not None
    assert users_attr.code_section_attribute.edge_spec_name == "UserGroupEdge"
    assert users_attr.code_section_attribute.is_many_to_many is True


def test_builder_index_add_section_node_is_idempotent_on_reuse(
    sample_files: dict[str, str],
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    The new invariant: multi-pass code should be able to attempt building the same section twice
    without crashing, as long as it's the same node byte-range.
    """
    code, sections_index = sample_file_codes["user_post"]

    # Pick an existing section + its original node from the index
    user_section = sections_index.get_by_ref(CodeSectionType.class_, "User")
    assert user_section is not None

    user_node = sections_index.get_section_node(user_section.id)
    assert user_node is not None

    # Rebuild the same base section from the same node and same code_id:
    # this should reuse existing identity_hash and *not* error on add_section_node.
    language_plugin = CodeLanguagePluginRegistry.get(CodeLanguage.aware)
    assert language_plugin is not None

    code_tree = language_plugin.tree_sitter_adapter.parse(sample_files["user_post"])
    assert code_tree is not None

    class_adapter = language_plugin.node_adapters[CodeSectionType.class_]
    rebuilt = build_section_from_code(
        adapter=class_adapter,
        code_section_type=CodeSectionType.class_,
        source=code_tree.source_bytes,
        code=code,
        node=user_node,
        section_index=sections_index,
    )
    assert rebuilt.id == user_section.id
    assert rebuilt.identity_hash == user_section.identity_hash


def test_code_builder_import_sections_have_canonical_text_fields(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    source = """
import module.submodule;
import package.utils as helpers;
import core.* as CoreUtils;
""".lstrip()
    path = tmp_path / "imports.aware"
    _ = path.write_text(source, encoding="utf-8")

    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )

    imports = [s for s in code.code_sections if s.type == CodeSectionType.import_]
    assert len(imports) == 3

    imp1 = imports[0].code_section_import
    assert imp1 is not None
    assert imp1.module_text == "module.submodule"
    assert imp1.module_segment_id == imp1.module_segment.id
    assert len(imp1.code_section_import_names) == 1
    assert imp1.code_section_import_names[0].name_text == "module.submodule"
    assert imp1.code_section_import_names[0].alias_text is None
    assert imp1.code_section_import_names[0].name_segment_id == imp1.code_section_import_names[0].name_segment.id
    assert imp1.code_section_import_names[0].alias_segment_id is None

    imp2 = imports[1].code_section_import
    assert imp2 is not None
    assert imp2.module_text == "package.utils"
    assert imp2.module_segment_id == imp2.module_segment.id
    assert len(imp2.code_section_import_names) == 1
    assert imp2.code_section_import_names[0].name_text == "package.utils"
    assert imp2.code_section_import_names[0].alias_text == "helpers"
    assert imp2.code_section_import_names[0].name_segment_id == imp2.code_section_import_names[0].name_segment.id
    assert imp2.code_section_import_names[0].alias_segment is not None
    assert imp2.code_section_import_names[0].alias_segment_id == imp2.code_section_import_names[0].alias_segment.id

    imp3 = imports[2].code_section_import
    assert imp3 is not None
    assert imp3.module_text == "core"
    assert imp3.is_star_import is True
    assert imp3.module_segment_id == imp3.module_segment.id
    assert len(imp3.code_section_import_names) == 1
    assert imp3.code_section_import_names[0].name_text == "*"
    assert imp3.code_section_import_names[0].alias_text == "CoreUtils"
    assert imp3.code_section_import_names[0].name_segment_id == imp3.code_section_import_names[0].name_segment.id
    assert imp3.code_section_import_names[0].alias_segment is not None
    assert imp3.code_section_import_names[0].alias_segment_id == imp3.code_section_import_names[0].alias_segment.id


def test_code_builder_links_docstring_comment_to_method(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    End-to-end: ensure docstring comment gets attached to CodeSectionFunction for a method.
    """
    _code, sections_index = sample_file_codes["user_post"]

    method_section = sections_index.get_by_ref(CodeSectionType.function, "User.buildUser")
    assert method_section is not None
    assert method_section.code_section_function is not None

    comments = method_section.code_section_function.code_section_comments
    assert len(comments) > 0, "Expected at least one doc comment linked to User.buildUser"

    # Validate the content includes the expected substring from the sample file
    blob_store = sections_index.get_blob_store()
    combined = "\n".join(
        "\n".join(
            get_segment_text(link.content_part_text_segment, blob_store=blob_store)
            for link in c.code_section_comment_contents
        )
        for c in comments
    )
    assert "Constructor-style function declared on User" in combined


def test_code_builder_propagates_nested_sections_to_code_sections(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    Validate the "flat registry" invariant:
    all base CodeSections (global + nested) are present in code.code_sections.

    We check a few known nested/global refs from the sample file and also assert
    that code.code_sections contains no duplicate CodeSection ids.
    """
    code, sections_index = sample_file_codes["user_post"]

    # Unique ids invariant (avoid silently appending duplicates in multi-pass orchestration)
    ids = [sec.id for sec in code.code_sections]
    assert len(ids) == len(set(ids)), "code.code_sections should not contain duplicate CodeSection ids"

    # Helper: resolve by ref from index and assert the base section is present in code.code_sections
    def _assert_present(section_type: CodeSectionType, ref: str) -> None:
        sec = sections_index.get_by_ref(section_type, ref)
        assert sec is not None, f"Expected section_index ref lookup for {section_type.value} {ref}"
        assert sec in code.code_sections, f"Expected {section_type.value} {ref} to be present in code.code_sections"

    # Nested method + param
    _assert_present(CodeSectionType.function, "User.buildUser")
    _assert_present(CodeSectionType.attribute, "User.buildUser.email")

    # Top-level function + params
    _assert_present(CodeSectionType.function, "addUser")
    _assert_present(CodeSectionType.attribute, "addUser.role")
    _assert_present(CodeSectionType.attribute, "addUser.isActive")
    _assert_present(CodeSectionType.attribute, "addUser.metadata")


def test_code_builder_ssot_fields_and_description_backfill(
    sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]],
):
    """
    SSOT invariants for CodeSection* models:
    - SSOT `name`/`type_text`/`default_value_text` are populated (not just segments)
    - SSOT values are consistent with segments
    - `description` is backfilled after comment linkage for key entities
    """
    code, sections_index = sample_file_codes["user_post"]
    assert len(code.code_sections) > 0

    # --- CLASS SSOT ---
    user_sec = sections_index.get_by_ref(CodeSectionType.class_, "User")
    assert user_sec is not None and user_sec.code_section_class is not None
    user_cls = user_sec.code_section_class
    assert user_cls.name == get_segment_text(user_cls.name_segment)
    assert user_cls.description is not None and "Represents a user" in user_cls.description

    # --- ENUM SSOT ---
    status_sec = sections_index.get_by_ref(CodeSectionType.enum, "Status")
    assert status_sec is not None and status_sec.code_section_enum is not None
    status_enum = status_sec.code_section_enum
    assert status_enum.name == get_segment_text(status_enum.name_segment)
    assert status_enum.description is not None and "Status enumeration" in status_enum.description

    # --- FUNCTION SSOT ---
    send_email_sec = sections_index.get_by_ref(CodeSectionType.function, "User.sendEmail")
    assert send_email_sec is not None and send_email_sec.code_section_function is not None
    send_email_fn = send_email_sec.code_section_function
    assert send_email_fn.name_segment is not None
    assert send_email_fn.name == get_segment_text(send_email_fn.name_segment)
    assert send_email_fn.is_async is True
    assert send_email_fn.description is not None and "Sends an email" in send_email_fn.description

    # --- ATTRIBUTE SSOT ---
    email_attr_sec = sections_index.get_by_ref(CodeSectionType.attribute, "User.email")
    assert email_attr_sec is not None and email_attr_sec.code_section_attribute is not None
    email_attr = email_attr_sec.code_section_attribute
    assert email_attr.name_segment is not None
    assert email_attr.name == get_segment_text(email_attr.name_segment)
    assert email_attr.type_segment is not None
    assert email_attr.type_text == get_segment_text(email_attr.type_segment)
    assert email_attr.type_text == "String?"
    assert email_attr.default_value_text is None
    assert email_attr.is_public is True
    assert email_attr.is_required is False  # Optional via '?'
    assert email_attr.is_unique is False
    assert email_attr.is_primary is False
    assert email_attr.description is not None and "User's email address" in email_attr.description


def test_attribute_type_detection(sample_file_codes: dict[str, tuple[Code, CodeSectionBuilderIndex]]):
    """Test that attribute types are correctly detected by the attribute adapter."""
    code, _sections_index = sample_file_codes["nested_attributes"]

    # Find the class section
    class_sections = [s for s in code.code_sections if s.type == CodeSectionType.class_]
    assert len(class_sections) == 1

    class_section = class_sections[0]

    # Check the attributes
    assert class_section.code_section_class is not None
    attrs = list(class_section.code_section_class.code_section_attributes)

    # We should find all the attributes defined in the type
    assert len(attrs) >= 15

    # Check some specific attributes to verify type detection
    attr_types = {}
    for attr in attrs:
        assert attr.name_segment is not None
        attr_name = get_segment_text(attr.name_segment)
        if attr.type_segment:
            type_text = get_segment_text(attr.type_segment)
            attr_types[attr_name] = type_text

    # Verify basic types were correctly detected
    expected_types = {
        "stringAttr": "String",
        "intAttr": "Int",
        "boolAttr": "Bool",
        "floatAttr": "Float",
        "optionalString": "String?",
        "stringArray": "String[]",
        "basicVector": "Vector",
        "dimensionVector": "Vector(1536)",
        "optionalVector": "Vector(512)?",
        "vectorArray": "Vector(256)[]",
    }

    for attr_name, expected_type in expected_types.items():
        if attr_name in attr_types:
            assert (
                attr_types[attr_name] == expected_type
            ), f"Expected {attr_name} to be {expected_type}, got {attr_types[attr_name]}"
