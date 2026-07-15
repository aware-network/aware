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

# Python Grammar
from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN


SAMPLES = ["user_post", "nested_attributes"]


@pytest.fixture(scope="session")
def sample_files():
    """Fixture that returns the path to the sample Python file."""
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    sample_files = {}
    for sample_name in SAMPLES:
        sample_file = samples_dir / f"{sample_name}.py"
        if not sample_file.exists():
            pytest.fail(f"Sample file not found: {sample_file}")
        sample_files[sample_name] = str(sample_file)
    return sample_files


@pytest.fixture(scope="session")
def sample_file_codes(sample_files):
    """Fixture that returns the file codes for the sample file."""
    CodeLanguagePluginRegistry.register(PYTHON_CODE_PLUGIN)
    sample_file_codes = {}
    for sample_name, sample_file in sample_files.items():
        code = build_code_from_file(
            sections_index=CodeSectionBuilderIndex(),
            file_path=sample_file,
            code_key=sample_file,
            language=CodeLanguage.python,
            symbol_table=CodeSymbolTable(),
        )
        sample_file_codes[sample_name] = code
    return sample_file_codes


def test_code_builder_from_file(sample_file_codes: dict[str, Code]):
    """Test the code builder from file with all Python adapters."""
    code = sample_file_codes["user_post"]

    # Validate code sections
    sections_by_type: dict[CodeSectionType, list[CodeSection]] = {}
    for section in code.code_sections:
        if section.type not in sections_by_type:
            sections_by_type[section.type] = []
        sections_by_type[section.type].append(section)

    # Check class sections
    assert CodeSectionType.class_ in sections_by_type, "Should have class sections"
    assert len(sections_by_type[CodeSectionType.class_]) >= 6, "Should have at least 6 class sections"

    # Check function sections (both standalone and methods)
    assert CodeSectionType.function in sections_by_type, "Should have function sections"

    # Check enum sections
    assert CodeSectionType.enum in sections_by_type, "Should have enum sections"
    assert len(sections_by_type[CodeSectionType.enum]) == 2, "Should have 2 enum sections"

    # Check comment sections
    assert CodeSectionType.comment in sections_by_type, "Should have comment sections"
    assert len(sections_by_type[CodeSectionType.comment]) > 0, "Should have at least one comment section"

    # Verify network decorator on GLOBAL functions
    network_decorators = []
    for function_section in sections_by_type.get(CodeSectionType.function, []):
        if hasattr(function_section, "code_section_function") and function_section.code_section_function:
            for decorator in function_section.code_section_function.code_section_decorators:
                if get_segment_text(decorator.name_segment) == "network":
                    network_decorators.append(decorator)

    assert len(network_decorators) >= 2, f"Should have at least 2 network decorators, found {len(network_decorators)}"

    # Verify intelligent_object decorator on classes
    intelligent_object_decorators = []
    for class_section in sections_by_type.get(CodeSectionType.class_, []):
        if hasattr(class_section, "code_section_class") and class_section.code_section_class:
            for decorator in class_section.code_section_class.code_section_decorators:
                if get_segment_text(decorator.name_segment) == "intelligent_object":
                    intelligent_object_decorators.append(decorator)

    assert (
        len(intelligent_object_decorators) >= 2
    ), f"Should have at least 2 intelligent_object decorators, found {len(intelligent_object_decorators)}"

    # Check comment linkage
    for class_section in sections_by_type.get(CodeSectionType.class_, []):
        if hasattr(class_section, "code_section_class") and class_section.code_section_class:
            class_name = get_segment_text(class_section.code_section_class.name_segment)
            if class_name in ["User", "Post"]:  # Classes with known docstrings
                assert (
                    class_section.code_section_class.code_section_comments is not None
                ), f"Class {class_name} should have code_section_comments"
                # At minimum, each of these classes should have a docstring
                assert (
                    len(class_section.code_section_class.code_section_comments) > 0
                ), f"Class {class_name} should have at least one associated comment"

            # Check method comment linkage
            for method_section in class_section.code_section_class.code_section_functions:
                if method_section:
                    method_name = get_segment_text(method_section.name_segment)
                    if method_name in ["get_full_name", "send_email"]:  # Methods with known docstrings
                        assert (
                            method_section.code_section_comments is not None
                        ), f"Function {method_name} should have code_section_comments"
                        assert (
                            len(method_section.code_section_comments) > 0
                        ), f"Function {method_name} should have at least one associated comment"

    # Check enum comment linkage
    for enum_section in sections_by_type.get(CodeSectionType.enum, []):
        if hasattr(enum_section, "code_section_enum") and enum_section.code_section_enum:
            enum_name = get_segment_text(enum_section.code_section_enum.name_segment)
            if enum_name == "Status":
                assert (
                    enum_section.code_section_enum.code_section_comments is not None
                ), f"Enum {enum_name} should have code_section_comments"
                assert (
                    len(enum_section.code_section_enum.code_section_comments) > 0
                ), f"Enum {enum_name} should have at least one associated comment"


def test_decorator_attributes(sample_file_codes: dict[str, Code]):
    """Test that decorator expressions are properly linked to decorators."""
    # Build code from file
    code = sample_file_codes["user_post"]

    # Collect sections by type
    sections_by_type: dict[CodeSectionType, list[CodeSection]] = {}
    for section in code.code_sections:
        if section.type not in sections_by_type:
            sections_by_type[section.type] = []
        sections_by_type[section.type].append(section)

    # 1. Test network decorator on validate_email function
    function_sections = sections_by_type.get(CodeSectionType.function, [])
    validate_email_section = None

    for section in function_sections:
        if hasattr(section, "code_section_function") and section.code_section_function:
            if get_segment_text(section.code_section_function.name_segment) == "validate_email":
                validate_email_section = section
                break

    assert validate_email_section is not None, "Should find validate_email function"

    # Get network decorator for validate_email
    network_decorator = None
    assert validate_email_section.code_section_function is not None, "validate_email function should not be None"
    for decorator in validate_email_section.code_section_function.code_section_decorators:
        if get_segment_text(decorator.name_segment) == "network":
            network_decorator = decorator
            break

    assert network_decorator is not None, "validate_email should have network decorator"

    # Check decorator expressions (new system)
    assert len(network_decorator.code_section_decorator_expressions) > 0, "Decorator should have linked expressions"
    assert len(network_decorator.code_section_decorator_expressions) == 1, "Decorator should have 1 expression"

    # Find required_access expression
    required_access_expr = None
    for expr_link in network_decorator.code_section_decorator_expressions:
        if expr_link.name_segment and "required_access" in get_segment_text(expr_link.name_segment):
            required_access_expr = expr_link
            break

    assert required_access_expr is not None, "network decorator should have required_access expression"
    assert required_access_expr.code_section_expression is not None, "required_access expression should not be None"
    assert "AccessLevelType.read" in get_segment_text(
        required_access_expr.code_section_expression.value_segment
    ), "required_access should be AccessLevelType.read"

    # 2. Test network decorator with multiple expressions on send_notification function
    send_notification_section = None
    for section in function_sections:
        if hasattr(section, "code_section_function") and section.code_section_function:
            if get_segment_text(section.code_section_function.name_segment) == "send_notification":
                send_notification_section = section
                break

    assert send_notification_section is not None, "Should find send_notification function"

    # Get network decorator for send_notification
    network_decorator = None
    assert send_notification_section.code_section_function is not None, "send_notification function should not be None"
    for decorator in send_notification_section.code_section_function.code_section_decorators:
        if get_segment_text(decorator.name_segment) == "network":
            network_decorator = decorator
            break

    assert network_decorator is not None, "send_notification should have network decorator"

    # Check decorator has both required_access and timeout expressions
    assert (
        len(network_decorator.code_section_decorator_expressions) >= 2
    ), "Decorator should have at least 2 expressions"

    # Find expressions by name
    required_access_expr = None
    timeout_expr = None
    for expr_link in network_decorator.code_section_decorator_expressions:
        if expr_link.name_segment:
            name_text = get_segment_text(expr_link.name_segment)
            if name_text == "required_access":
                required_access_expr = expr_link
            elif name_text == "timeout":
                timeout_expr = expr_link

    assert required_access_expr is not None, "network decorator should have required_access expression"
    assert required_access_expr.code_section_expression is not None, "required_access expression should not be None"
    assert "AccessLevelType.admin" in get_segment_text(
        required_access_expr.code_section_expression.value_segment
    ), "required_access should be AccessLevelType.admin"

    assert timeout_expr is not None, "network decorator should have timeout expression"
    assert timeout_expr.code_section_expression is not None, "timeout expression should not be None"
    assert "60" in get_segment_text(timeout_expr.code_section_expression.value_segment), "timeout should be 60"

    # 3. Test intelligent_object decorator on User class
    class_sections = sections_by_type.get(CodeSectionType.class_, [])
    user_class_section = None

    for section in class_sections:
        if hasattr(section, "code_section_class") and section.code_section_class:
            if get_segment_text(section.code_section_class.name_segment) == "User":
                user_class_section = section
                break

    assert user_class_section is not None, "Should find User class"

    # Get intelligent_object decorator for User class
    intelligent_object_decorator = None
    assert user_class_section.code_section_class is not None, "User class should not be None"
    for decorator in user_class_section.code_section_class.code_section_decorators:
        if get_segment_text(decorator.name_segment) == "intelligent_object":
            intelligent_object_decorator = decorator
            break

    assert intelligent_object_decorator is not None, "User class should have intelligent_object decorator"

    # Check decorator expressions
    assert (
        len(intelligent_object_decorator.code_section_decorator_expressions) > 0
    ), "Decorator should have linked expressions"

    # Find object_type expression
    object_type_expr = None
    for expr_link in intelligent_object_decorator.code_section_decorator_expressions:
        if expr_link.name_segment and "object_type" in get_segment_text(expr_link.name_segment):
            object_type_expr = expr_link
            break

    assert object_type_expr is not None, "intelligent_object decorator should have object_type expression"
    assert object_type_expr.code_section_expression is not None, "object_type expression should not be None"
    assert '"user"' in get_segment_text(
        object_type_expr.code_section_expression.value_segment
    ), 'object_type should be "user"'


def test_imports_detection(sample_file_codes: dict[str, Code]):
    """Test that imports are correctly extracted by the builder process."""
    code = sample_file_codes["user_post"]

    sections_by_type: dict[CodeSectionType, list[CodeSection]] = {}
    for section in code.code_sections:
        if section.type not in sections_by_type:
            sections_by_type[section.type] = []
        sections_by_type[section.type].append(section)

    assert CodeSectionType.import_ in sections_by_type, "Should have import sections"
    assert (
        len(sections_by_type[CodeSectionType.import_]) >= 11
    ), f"Should have at least 11 import sections, found {len(sections_by_type[CodeSectionType.import_])}"

    # Check from __future__ import annotations
    future_import_section = None
    for section in sections_by_type[CodeSectionType.import_]:
        if hasattr(section, "code_section_import") and section.code_section_import:
            module_text = get_segment_text(section.code_section_import.module_segment)
            if module_text == "__future__":
                future_import_section = section
                break

    assert future_import_section is not None, "Should find __future__ import section"
    assert future_import_section.code_section_import is not None, "future import section should not be None"
    assert future_import_section.code_section_import.is_from_import, "Should be a from-import"
    assert not future_import_section.code_section_import.is_star_import, "Should not be a star import"

    # Check import names
    import_names = future_import_section.code_section_import.code_section_import_names
    assert len(import_names) == 1, "Should have one imported name"
    assert get_segment_text(import_names[0].name_segment) == "annotations", "Should import annotations"
    assert import_names[0].alias_segment is None, "Should not have an alias"


def test_attribute_type_detection(sample_file_codes: dict[str, Code]):
    """Test that attribute types are correctly detected by the attribute adapter."""
    # Create a test file with various typed attributes
    code = sample_file_codes["nested_attributes"]

    # Find the class section
    class_sections = [s for s in code.code_sections if s.type == CodeSectionType.class_]
    assert len(class_sections) == 1

    class_section = class_sections[0]

    # Check the attributes
    assert class_section.code_section_class is not None
    attrs = list(class_section.code_section_class.code_section_attributes)

    # We should find all the attributes defined in the class
    assert len(attrs) >= 10

    # Check some specific attributes to verify type detection
    attr_types = {}
    for attr in attrs:
        if attr.name_segment is None:
            continue
        attr_name = get_segment_text(attr.name_segment)
        if attr.type_segment:
            type_text = get_segment_text(attr.type_segment)
            attr_types[attr_name] = type_text

    # Verify basic types were correctly detected
    assert "string_attr" in attr_types and attr_types["string_attr"] == "str"
    assert "int_attr" in attr_types and attr_types["int_attr"] == "int"
    assert "bool_attr" in attr_types and attr_types["bool_attr"] == "bool"

    # Verify container types
    assert "list_attr" in attr_types and "list[str]" in attr_types["list_attr"]
    assert "dict_attr" in attr_types and "dict[str, int]" in attr_types["dict_attr"]

    # Verify instance attributes from __init__ are found
    assert class_section.code_section_class is not None
    methods = list(class_section.code_section_class.code_section_functions)
    init_methods = [m for m in methods if get_segment_text(m.name_segment) == "__init__"]
    assert len(init_methods) == 1


def test_code_builder_flat_registry_invariants(sample_files):
    """
    Canonical invariants for the builder output:
    - code.code_sections is a complete flat registry of base CodeSections (global + nested)
    - no duplicate CodeSection ids in code.code_sections
    - any section resolved via sections_index.get_by_ref(...) is present in code.code_sections
    - decorator expression base sections exist in the flat registry
    """
    CodeLanguagePluginRegistry.register(PYTHON_CODE_PLUGIN)
    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=sample_files["user_post"],
        code_key=sample_files["user_post"],
        language=CodeLanguage.python,
        symbol_table=CodeSymbolTable(),
    )

    # No duplicate ids in flat registry
    ids = [sec.id for sec in code.code_sections]
    assert len(ids) == len(set(ids)), "code.code_sections should not contain duplicate CodeSection ids"

    # Helper: ref lookup must produce a section that is in the flat registry
    def _assert_ref_present(section_type: CodeSectionType, ref: str) -> CodeSection:
        sec = sections_index.get_by_ref(section_type, ref)
        assert sec is not None, f"Expected ref lookup for {section_type.value} {ref}"
        assert sec in code.code_sections, f"Expected {section_type.value} {ref} to be present in code.code_sections"
        return sec

    # Async decorated method + params
    _assert_ref_present(CodeSectionType.function, "User.send_email")
    _assert_ref_present(CodeSectionType.attribute, "User.send_email.subject")
    _assert_ref_present(CodeSectionType.attribute, "User.send_email.body")

    # Module-level function + params
    _assert_ref_present(CodeSectionType.function, "send_notification")
    _assert_ref_present(CodeSectionType.attribute, "send_notification.user_id")
    _assert_ref_present(CodeSectionType.attribute, "send_notification.message")

    # Ensure decorator expression base sections are also present in the flat registry
    validate_email = _assert_ref_present(CodeSectionType.function, "validate_email")
    assert validate_email.code_section_function is not None
    net_decorator = next(
        (
            d
            for d in validate_email.code_section_function.code_section_decorators
            if get_segment_text(d.name_segment) == "network"
        ),
        None,
    )
    assert net_decorator is not None
    assert len(net_decorator.code_section_decorator_expressions) > 0
    for expr_link in net_decorator.code_section_decorator_expressions:
        assert expr_link.code_section_expression is not None
        # Base expression CodeSection should be in code.code_sections
        assert (
            expr_link.code_section_expression.code_section in code.code_sections
        ), "Decorator expression base CodeSection should be present in code.code_sections"


def test_code_builder_ssot_fields_and_description_backfill(sample_files):
    """
    SSOT invariants for CodeSection* models:
    - SSOT `name`/`type_text`/`default_value_text` are populated (not just segments)
    - SSOT values are consistent with segments
    - `description` is backfilled after comment linkage for key entities
    """
    CodeLanguagePluginRegistry.register(PYTHON_CODE_PLUGIN)
    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=sample_files["user_post"],
        code_key=sample_files["user_post"],
        language=CodeLanguage.python,
        symbol_table=CodeSymbolTable(),
    )
    assert len(code.code_sections) > 0

    # --- CLASS SSOT ---
    user_sec = sections_index.get_by_ref(CodeSectionType.class_, "User")
    assert user_sec is not None and user_sec.code_section_class is not None
    user_cls = user_sec.code_section_class
    assert user_cls.name == get_segment_text(user_cls.name_segment)
    assert user_cls.description is not None and "user account" in user_cls.description.lower()

    # --- ENUM SSOT ---
    status_sec = sections_index.get_by_ref(CodeSectionType.enum, "Status")
    assert status_sec is not None and status_sec.code_section_enum is not None
    status_enum = status_sec.code_section_enum
    assert status_enum.name == get_segment_text(status_enum.name_segment)
    assert status_enum.description is not None and "status" in status_enum.description.lower()

    # --- FUNCTION SSOT (async decorated method) ---
    send_email_sec = sections_index.get_by_ref(CodeSectionType.function, "User.send_email")
    assert send_email_sec is not None and send_email_sec.code_section_function is not None
    send_email_fn = send_email_sec.code_section_function
    assert send_email_fn.name == get_segment_text(send_email_fn.name_segment)
    assert send_email_fn.is_async is True
    assert send_email_fn.description is not None and "send an email" in send_email_fn.description.lower()

    # --- ATTRIBUTE SSOT (class field) ---
    email_attr_sec = sections_index.get_by_ref(CodeSectionType.attribute, "User.email")
    assert email_attr_sec is not None and email_attr_sec.code_section_attribute is not None
    email_attr = email_attr_sec.code_section_attribute
    assert email_attr.name == get_segment_text(email_attr.name_segment)
    assert email_attr.type_segment is not None
    assert email_attr.type_text == get_segment_text(email_attr.type_segment)
    assert email_attr.type_text is not None and "optional" in email_attr.type_text.lower()
    # In the sample file `email` is `Field(default=None)`, so the SSOT default literal is "None".
    assert email_attr.default_value_text == "None"
    assert email_attr.is_public is True
    assert email_attr.is_required is False  # Optional[...] should be not required
    assert email_attr.is_unique is False
    assert email_attr.is_primary is False
