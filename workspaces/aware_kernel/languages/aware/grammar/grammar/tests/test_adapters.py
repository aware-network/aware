from pathlib import Path

import pytest

# Code Runtime
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode
from aware_code.tree.tree import CodeTree
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter

# Aware Grammar
from aware_grammar.adapters.class_composite_adapter import AwareClassCompositeAdapter
from aware_grammar.adapters.edge_adapter import AwareEdgeAdapter
from aware_grammar.adapters.class_adapter import AwareClassAdapter
from aware_grammar.adapters.attribute_adapter import AwareAttributeAdapter
from aware_grammar.adapters.function_adapter import AwareFunctionAdapter
from aware_grammar.adapters.comment_adapter import AwareCommentAdapter
from aware_grammar.adapters.import_adapter import AwareImportAdapter
from aware_grammar.adapters.annotation_adapter import AwareAnnotationAdapter
from aware_grammar.adapters.binding_adapter import AwareBindingAdapter

# Tree-sitter
from tree_sitter import Parser, Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Set up language and parser
parser = Parser(language=AWARE_LANGUAGE)


def _safe_text(node: Node | None) -> str:
    """Safely extract text from a node."""
    if node is None:
        return ""
    text_bytes = node.text
    if text_bytes is None:
        return ""
    return text_bytes.decode("utf-8")


@pytest.fixture
def sample_aware_file() -> str:
    """Fixture that returns the path to the sample Aware file."""
    current_dir = Path(__file__).parent
    sample_file = current_dir / "samples" / "user_post.aware"

    if not sample_file.exists():
        pytest.fail(f"Sample file not found: {sample_file}")

    return str(sample_file)


@pytest.fixture
def parsed_tree(sample_aware_file: str) -> CodeTree[Node]:
    """Fixture that returns the parsed tree for the sample file."""
    with open(sample_aware_file, "rb") as f:
        source_bytes = f.read()

    tree = parser.parse(source_bytes)
    root_node = CodeNode(
        node=tree.root_node,
        byte_start=tree.root_node.start_byte,
        byte_end=tree.root_node.end_byte,
    )

    return CodeTree(root=root_node, source_bytes=source_bytes)


def test_tree_adapter(sample_aware_file: str) -> None:
    """Test the CodeTreeSitterAdapter."""
    adapter = CodeTreeSitterAdapter(language=AWARE_LANGUAGE)
    code_tree = adapter.parse(sample_aware_file)

    assert code_tree is not None, "Tree adapter should return a CodeTree"
    assert code_tree.root is not None, "CodeTree should have a root node"
    assert len(code_tree.source_bytes) > 0, "CodeTree should have source bytes"


def test_class_adapter(parsed_tree: CodeTree[Node]) -> None:
    """Test the AwareClassAdapter for class definitions."""
    adapter = AwareClassAdapter()

    # Find all class definitions
    class_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    assert len(class_nodes) == 4, "Should find 4 class definitions: User, Post, Comment, Image"

    # Test class names
    class_names = [_safe_text(adapter.get_name(node).node) for node in class_nodes]
    assert "User" in class_names, "Should find User class"
    assert "Post" in class_names, "Should find Post class"
    assert "Comment" in class_names, "Should find Comment class"
    assert "Image" in class_names, "Should find Image class"

    # Test User class in more detail
    user_node = next(node for node in class_nodes if _safe_text(adapter.get_name(node).node) == "User")

    # Test attributes in User
    attributes = list(adapter.get_attributes(user_node))
    assert len(attributes) == 7, "User should have 7 attributes"

    # Test methods in User
    functions = list(adapter.get_methods(user_node))
    assert len(functions) == 3, "User should have 3 functions"
    fn_adapter = AwareFunctionAdapter()
    build_user_method = next(
        function for function in functions if _safe_text(fn_adapter.get_name(function).node) == "buildUser"
    )
    assert fn_adapter.get_verb(build_user_method) == "construct"

    # Test qualname
    assert adapter.qualname(user_node) == "User", "Qualname should be 'User'"
    assert adapter.qualname(user_node, "models") == "models.User", "Qualname with parent"


def test_function_adapter_reads_read_verb():
    """Ensure function verb tokens capture read-only verbs."""
    sample_code = """
class User {
    fn list read() -> String { }
}
"""
    tree = parser.parse(sample_code.encode())
    class_adapter = AwareClassAdapter()
    fn_adapter = AwareFunctionAdapter()

    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    user_node = next(node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "User")
    functions = list(class_adapter.get_methods(user_node))
    list_fn = next(fn for fn in functions if _safe_text(fn_adapter.get_name(fn).node) == "list")
    assert fn_adapter.get_verb(list_fn) == "read"


def test_class_adapter_bounds_sibling_method_bodies_for_runtime_impls():
    sample_code = """
class Interface {
    os InterfaceOs key
    version String key

    fn build construct (
        os InterfaceOs key,
        version String key,
        dependencies JsonArray = [],
        dart JsonObject = {}
    ) -> Interface {
        \"""
        Build.
        \"""
    }

    fn attach_window (window_id UUID) -> InterfaceWindow {
        \"""
        Attach a window.
        \"""
        let attached = construct interface_windows.create(
            window_id = window_id,
        )
    }

    fn attach_environment (environment_id UUID) -> InterfaceEnvironment {
        \"""
        Attach an environment.
        \"""
        let attached = construct environments.create(
            environment_id = environment_id,
        )
    }

    fn set_active_window_thread (
        interface_window_id UUID,
        thread_id UUID,
    ) -> Interface {
        let active_window_thread_id = thread_id
    }
}
"""
    tree = parser.parse(sample_code.encode())
    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()
    fn_adapter = AwareFunctionAdapter()
    source_bytes = sample_code.encode()

    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    interface_node = next(node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "Interface")
    methods = list(class_adapter.get_methods(interface_node))

    method_names = [_safe_text(fn_adapter.get_name(method).node) for method in methods]
    assert method_names == [
        "build",
        "attach_window",
        "attach_environment",
        "set_active_window_thread",
    ]

    method_bodies = {
        _safe_text(fn_adapter.get_name(method).node): _safe_text(fn_adapter.get_body(method).node) for method in methods
    }
    assert "fn attach_window" not in method_bodies["build"]
    assert "fn attach_environment" not in method_bodies["attach_window"]
    assert "fn set_active_window_thread" not in method_bodies["attach_environment"]
    assert "active_window_thread_id" in method_bodies["set_active_window_thread"]

    build_method = methods[0]
    params = list(fn_adapter.get_parameters(build_method))
    dependencies_param = next(
        param
        for param in params
        if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "dependencies"
    )
    dart_param = next(
        param for param in params if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "dart"
    )

    dependencies_type = attribute_adapter.get_type(
        dependencies_param,
        is_parameter=True,
    )
    dart_default = attribute_adapter.get_default_value(dart_param, is_parameter=True)
    assert source_bytes[dependencies_type.byte_start : dependencies_type.byte_end].decode() == "JsonArray"
    assert dart_default is not None
    assert source_bytes[dart_default.byte_start : dart_default.byte_end].decode() == "{}"


def test_class_adapter_modifiers_keyword_bases():
    """Test the class adapter methods for modifiers, keyword, and bases extraction."""
    from tree_sitter import Parser

    # Sample Aware code with types that have modifiers
    sample_code = """
class User : inline_value {
    id UUID = "gen_random_uuid()"
    name String
    posts Post[] @UserPost
}

edge UserPost {
    id UUID = "gen_random_uuid()"
    user_id UUID
    post_id UUID
    created_at DateTime
}

class PatchPayload : inline_value {
    line String
}

class Post {
    id UUID
    title String
    content String
}
"""

    # Parse the sample code
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    # Create adapters
    class_adapter = AwareClassAdapter()
    edge_adapter = AwareEdgeAdapter()
    composite_adapter = AwareClassCompositeAdapter()

    # Test class modifiers
    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    user_node = next(node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "User")

    # Test get_modifiers - should return individual class modifier nodes
    modifier_nodes = list(class_adapter.get_modifiers(user_node))
    assert len(modifier_nodes) == 1, "User class should have 1 modifier: inline_value"

    modifier_texts = [_safe_text(mod.node) for mod in modifier_nodes]
    assert "inline_value" in modifier_texts, "Should find inline_value modifier"

    # Test get_keyword - should return the 'class' keyword
    keyword_node = class_adapter.get_keyword(user_node)
    assert keyword_node is not None, "Should find keyword node"
    assert _safe_text(keyword_node.node) == "class", "Keyword should be 'class'"

    # Test get_bases - should return empty for Aware (no inheritance)
    base_nodes = list(class_adapter.get_bases(user_node))
    assert len(base_nodes) == 0, "Aware classes should not have base classes"

    # Test Post class (no modifiers)
    post_node = next(node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "Post")

    post_modifier_nodes = list(class_adapter.get_modifiers(post_node))
    assert len(post_modifier_nodes) == 0, "Post class should have no modifiers"
    assert class_adapter.is_inline_value(post_node) is False, "Post should not be inline_value"

    post_keyword_node = class_adapter.get_keyword(post_node)
    assert post_keyword_node is not None, "Should find keyword node"
    assert _safe_text(post_keyword_node.node) == "class", "Keyword should be 'class'"

    # Test inline_value class modifiers
    payload_node = next(node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "PatchPayload")
    payload_mods = [_safe_text(m.node) for m in class_adapter.get_modifiers(payload_node)]
    assert payload_mods == ["inline_value"]
    assert class_adapter.is_inline_value(payload_node) is True

    # Test edge modifiers
    edge_nodes = list(edge_adapter.match_nodes(tree.root_node, sample_code.encode()))
    user_post_edge = next(node for node in edge_nodes if _safe_text(edge_adapter.get_name(node).node) == "UserPost")

    # Test edge keyword
    edge_keyword_node = edge_adapter.get_keyword(user_post_edge)
    assert edge_keyword_node is not None, "Should find edge keyword node"
    assert _safe_text(edge_keyword_node.node) == "edge", "Keyword should be 'edge'"

    # Test edge modifiers (currently return empty as noted in implementation)
    edge_modifier_nodes = list(edge_adapter.get_modifiers(user_post_edge))
    assert len(edge_modifier_nodes) == 0, "Edge modifiers should be 0"

    # Test edge bases
    edge_base_nodes = list(edge_adapter.get_bases(user_post_edge))
    assert len(edge_base_nodes) == 0, "Aware edges should not have base classes"

    # Test composite adapter delegation
    all_class_nodes = list(composite_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(all_class_nodes) == 4, "Should find 4 class nodes (3 classes + 1 edge)"

    # Test delegation works correctly
    for class_node in all_class_nodes:
        keyword_node = composite_adapter.get_keyword(class_node)
        assert keyword_node is not None, "Should find keyword for all class nodes"
        keyword_text = _safe_text(keyword_node.node)
        assert keyword_text in [
            "class",
            "edge",
        ], f"Keyword should be 'class' or 'edge', got '{keyword_text}'"

        modifier_nodes = list(composite_adapter.get_modifiers(class_node))
        base_nodes = list(composite_adapter.get_bases(class_node))
        assert len(base_nodes) == 0, "Aware doesn't support base classes"


def test_type_adapter_detects_augment_verb():
    """Ensure augment verb is parsed and exposed via the class adapter."""
    sample_code = """
class TerminalEnv augment Terminal {
    provider String?
    fn create(thread Thread) -> Terminal {
        \"\"\"Creates a terminal via the environment overlay\"\"\"
    }
}
"""
    tree = parser.parse(sample_code.encode())
    adapter = AwareClassAdapter()
    type_nodes = list(adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(type_nodes) == 1, "Should find the Terminal class definition"

    terminal_node = type_nodes[0]
    verb_node = adapter.get_verb(terminal_node)
    assert verb_node is not None, "Augment verb should be detected"
    assert _safe_text(verb_node.node) == "augment", "Verb text should be 'augment'"
    verb_target_node = adapter.get_verb_target(terminal_node)
    assert verb_target_node is not None, "Verb target should be detected"
    assert _safe_text(verb_target_node.node) == "Terminal", "Verb target should be 'Terminal'"

    attributes = list(adapter.get_attributes(terminal_node))
    assert len(attributes) == 1, "Augment classes should expose attribute nodes in the adapter"


def test_binding_adapter_extracts_named_maps() -> None:
    sample_code = """
binding aware_home_api aware_home {
    map door_by_label door.DoorDevice home.Door.label {
        \"\"\"Resolve external door payload onto canonical Door.label.\"\"\"
        template {
            "device_id::{device_id}_provider::{provider}_label::{door_label}"
        }
    }
}
"""
    tree = parser.parse(sample_code.encode())
    adapter = AwareBindingAdapter()

    binding_nodes = list(adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(binding_nodes) == 1

    binding_node = binding_nodes[0]
    assert _safe_text(adapter.get_source_graph(binding_node).node) == "aware_home_api"
    assert _safe_text(adapter.get_target_graph(binding_node).node) == "aware_home"

    maps = adapter.get_maps(binding_node)
    assert len(maps) == 1
    assert _safe_text(maps[0].name_node.node) == "door_by_label"
    assert _safe_text(maps[0].source_node.node) == "door.DoorDevice"
    assert _safe_text(maps[0].target_node.node) == "home.Door.label"
    assert maps[0].body_node is not None
    assert maps[0].template_value_node is not None
    assert '"""Resolve external door payload onto canonical Door.label."""' in _safe_text(maps[0].body_node.node)
    assert '"device_id::{device_id}_provider::{provider}_label::{door_label}"' == _safe_text(
        maps[0].template_value_node.node
    )


def test_attribute_adapter(parsed_tree: CodeTree[Node]) -> None:
    """Test the AwareAttributeAdapter for attribute definitions."""
    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()

    # Get the User class
    user_node = next(
        node
        for node in class_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if _safe_text(class_adapter.get_name(node).node) == "User"
    )

    # Get attributes in User
    attributes = list(class_adapter.get_attributes(user_node))

    # Test attribute names
    attribute_names = [
        _safe_text(attribute_adapter.get_name(attribute, is_parameter=False).node) for attribute in attributes
    ]
    assert "name" in attribute_names, "Should have name attribute"
    assert "email" in attribute_names, "Should have email attribute"

    # Test email attribute for optional
    email_attribute = next(
        attribute
        for attribute in attributes
        if _safe_text(attribute_adapter.get_name(attribute, is_parameter=False).node) == "email"
    )
    assert attribute_adapter.is_optional(email_attribute), "Email attribute should be optional"

    # Test name attribute for default value
    name_attribute = next(
        attribute
        for attribute in attributes
        if _safe_text(attribute_adapter.get_name(attribute, is_parameter=False).node) == "name"
    )
    default_val = attribute_adapter.get_default_value(name_attribute, is_parameter=False)
    assert default_val is not None, "Name attribute should have a default value"

    # Test attribute type
    email_type = attribute_adapter.get_base_type(email_attribute, is_parameter=False)
    assert email_type is not None, "Email attribute should have a type"
    assert _safe_text(email_type.node) == "String", "Email attribute should be of type String"


def test_attribute_adapter_detects_identity_key_markers() -> None:
    sample_code = """
class User {
    identity_email String key

    fn buildUser construct(email String key, display_name String?) -> User {
    }
}
"""
    tree = parser.parse(sample_code.encode())
    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()
    function_adapter = AwareFunctionAdapter()

    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(class_nodes) == 1
    user_node = class_nodes[0]

    attributes = list(class_adapter.get_attributes(user_node))
    identity_email_attr = next(
        attr
        for attr in attributes
        if _safe_text(attribute_adapter.get_name(attr, is_parameter=False).node) == "identity_email"
    )
    assert attribute_adapter.is_primary(identity_email_attr, is_parameter=False) is True

    methods = list(class_adapter.get_methods(user_node))
    build_user = next(fn for fn in methods if _safe_text(function_adapter.get_name(fn).node) == "buildUser")
    params = list(function_adapter.get_parameters(build_user))
    email_param = next(
        p for p in params if _safe_text(attribute_adapter.get_name(p, is_parameter=True).node) == "email"
    )
    display_name_param = next(
        p for p in params if _safe_text(attribute_adapter.get_name(p, is_parameter=True).node) == "display_name"
    )

    assert attribute_adapter.is_primary(email_param, is_parameter=True) is True
    assert attribute_adapter.is_primary(display_name_param, is_parameter=True) is False


def test_attribute_adapter_keeps_key_as_normal_field_name_after_optional() -> None:
    sample_code = """
class ProgramConfigGraph {
    intent String?
    key String?
}
"""
    tree = parser.parse(sample_code.encode())
    assert tree.root_node.has_error is False

    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()
    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(class_nodes) == 1

    attrs = list(class_adapter.get_attributes(class_nodes[0]))
    names = [_safe_text(attribute_adapter.get_name(a, is_parameter=False).node) for a in attrs]
    types = [_safe_text(attribute_adapter.get_type(a, is_parameter=False).node) for a in attrs]

    assert names == ["intent", "key"]
    assert types == ["String?", "String?"]
    assert all(not attribute_adapter.is_primary(a, is_parameter=False) for a in attrs)


def test_attribute_adapter_accepts_terminal_identity_key_with_trailing_comment() -> None:
    sample_code = """
class User {
    identity_email String key // canonical identity selector
}
"""
    tree = parser.parse(sample_code.encode())
    assert tree.root_node.has_error is False

    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()
    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(class_nodes) == 1
    attrs = list(class_adapter.get_attributes(class_nodes[0]))
    assert len(attrs) == 1
    assert _safe_text(attribute_adapter.get_name(attrs[0], is_parameter=False).node) == "identity_email"
    assert attribute_adapter.is_primary(attrs[0], is_parameter=False) is True


def test_attribute_adapter_edge_specification():
    """Test the AwareAttributeAdapter for edge specification extraction."""
    from tree_sitter import Parser

    # Sample Aware code with edge specifications
    sample_code = """
class FunctionCall {
    attributes attribute.Attribute[] @FunctionCallArgument
    other_attribute String
    function Function?
    metrics analytics.Metric[] @FunctionCallMetric
}

class UserProfile {
    user_id UUID
    posts social.Post[] @UserPostEdge
    comments social.Comment[]
}
"""

    # Parse the sample code
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    # Create adapters
    class_adapter = AwareClassAdapter()
    attribute_adapter = AwareAttributeAdapter()

    # Find all class definitions
    class_nodes = list(class_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(class_nodes) == 2, "Should find 2 class definitions"

    # Get FunctionCall class
    function_call_node = next(
        node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "FunctionCall"
    )

    # Get attributes in FunctionCall
    attributes = list(class_adapter.get_attributes(function_call_node))

    # Test edge specification extraction for each attribute
    edge_specs_found: dict[str, dict[str, str | None]] = {}
    for attribute in attributes:
        attribute_name = _safe_text(attribute_adapter.get_name(attribute, is_parameter=False).node)
        edge_spec = attribute_adapter.get_edge_spec(attribute, is_parameter=False)
        base_type = attribute_adapter.get_base_type(attribute, is_parameter=False)
        base_type_text = _safe_text(base_type.node) if base_type else None
        edge_specs_found[attribute_name] = {
            "edge_spec": edge_spec,
            "base_type": base_type_text,
        }

    # Verify edge specifications
    assert (
        edge_specs_found["attributes"]["edge_spec"] == "FunctionCallArgument"
    ), "attributes attribute should have edge spec FunctionCallArgument"
    assert (
        edge_specs_found["attributes"]["base_type"] == "Attribute"
    ), "attributes attribute should have base type Attribute"

    assert (
        edge_specs_found["metrics"]["edge_spec"] == "FunctionCallMetric"
    ), "metrics attribute should have edge spec FunctionCallMetric"
    assert edge_specs_found["metrics"]["base_type"] == "Metric", "metrics attribute should have base type Metric"

    # Verify attributes without edge specifications
    assert edge_specs_found["other_attribute"]["edge_spec"] is None, "other_attribute should not have edge spec"
    assert edge_specs_found["function"]["edge_spec"] is None, "function attribute should not have edge spec"

    # Get UserProfile class and test more edge specs
    user_profile_node = next(
        node for node in class_nodes if _safe_text(class_adapter.get_name(node).node) == "UserProfile"
    )

    user_profile_attributes = list(class_adapter.get_attributes(user_profile_node))
    user_profile_specs = {}
    for attribute in user_profile_attributes:
        attribute_name = _safe_text(attribute_adapter.get_name(attribute, is_parameter=False).node)
        edge_spec = attribute_adapter.get_edge_spec(attribute, is_parameter=False)
        user_profile_specs[attribute_name] = edge_spec

    # Verify UserProfile edge specifications
    assert user_profile_specs["posts"] == "UserPostEdge", "posts attribute should have edge spec UserPostEdge"
    assert user_profile_specs["comments"] is None, "comments attribute should not have edge spec"
    assert user_profile_specs["user_id"] is None, "user_id attribute should not have edge spec"


def test_parameter_defaults(parsed_tree: CodeTree[Node]) -> None:
    """Test that function parameter default values are correctly detected."""
    function_adapter = AwareFunctionAdapter()
    attribute_adapter = AwareAttributeAdapter()

    # Find all standalone functions
    standalone_functions = list(function_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    # Test addUser function with multiple parameter defaults
    add_user_fn = next(
        function
        for function in standalone_functions
        if _safe_text(function_adapter.get_name(function).node) == "addUser"
    )

    # Get parameters from addUser function
    params = list(function_adapter.get_parameters(add_user_fn))
    assert len(params) == 3, "addUser should have 3 parameters"

    # Test parameter names
    param_names = [_safe_text(attribute_adapter.get_name(param, is_parameter=True).node) for param in params]
    assert "role" in param_names, "Should have role parameter"
    assert "isActive" in param_names, "Should have isActive parameter"
    assert "metadata" in param_names, "Should have metadata parameter"

    # Test role parameter (enum default)
    role_param = next(
        param for param in params if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "role"
    )
    role_default = attribute_adapter.get_default_value(role_param, is_parameter=True)
    assert role_default is not None, "role parameter should have a default value"
    assert _safe_text(role_default.node) == "active", "role default should be active"

    # Test isActive parameter (boolean default)
    is_active_param = next(
        param for param in params if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "isActive"
    )
    is_active_default = attribute_adapter.get_default_value(is_active_param, is_parameter=True)
    assert is_active_default is not None, "isActive parameter should have a default value"
    assert _safe_text(is_active_default.node) == "true", "isActive default should be true"

    # Test metadata parameter (optional with default)
    metadata_param = next(
        param for param in params if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "metadata"
    )
    metadata_default = attribute_adapter.get_default_value(metadata_param, is_parameter=True)
    assert metadata_default is not None, "metadata parameter should have a default value"
    assert _safe_text(metadata_default.node) == "null", "metadata default should be null"
    assert attribute_adapter.is_optional(metadata_param, is_parameter=True), "metadata parameter should be optional"
    assert not attribute_adapter.is_required(
        metadata_param, is_parameter=True
    ), "metadata parameter should not be required"

    # Test validateEmail function with boolean default and optional parameter
    validate_email_fn = next(
        function
        for function in standalone_functions
        if _safe_text(function_adapter.get_name(function).node) == "validateEmail"
    )
    validate_params = list(function_adapter.get_parameters(validate_email_fn))
    assert len(validate_params) == 3, "validateEmail should have 3 parameters"

    check_domain_param = next(
        param
        for param in validate_params
        if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "checkDomain"
    )
    check_domain_default = attribute_adapter.get_default_value(check_domain_param, is_parameter=True)
    assert check_domain_default is not None, "checkDomain parameter should have a default value"
    assert _safe_text(check_domain_default.node) == "true", "checkDomain default should be true"
    assert not attribute_adapter.is_optional(
        check_domain_param, is_parameter=True
    ), "checkDomain parameter should not be optional"

    timeout_param = next(
        param
        for param in validate_params
        if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "timeout"
    )
    timeout_default = attribute_adapter.get_default_value(timeout_param, is_parameter=True)
    assert timeout_default is not None, "timeout parameter should have a default value"
    assert _safe_text(timeout_default.node) == "null", "timeout default should be null"
    assert attribute_adapter.is_optional(timeout_param, is_parameter=True), "timeout parameter should be optional"
    assert not attribute_adapter.is_required(
        timeout_param, is_parameter=True
    ), "timeout parameter should not be required"

    # Test scheduleTask function with mixed optional/required parameters
    schedule_task_fn = next(
        function
        for function in standalone_functions
        if _safe_text(function_adapter.get_name(function).node) == "scheduleTask"
    )
    schedule_params = list(function_adapter.get_parameters(schedule_task_fn))
    assert len(schedule_params) == 4, "scheduleTask should have 4 parameters"

    # Test endTime parameter (optional, no default)
    end_time_param = next(
        param
        for param in schedule_params
        if _safe_text(attribute_adapter.get_name(param, is_parameter=True).node) == "endTime"
    )
    end_time_default = attribute_adapter.get_default_value(end_time_param, is_parameter=True)
    assert end_time_default is None, "endTime parameter should not have a default value"
    assert attribute_adapter.is_optional(end_time_param, is_parameter=True), "endTime parameter should be optional"
    assert not attribute_adapter.is_required(
        end_time_param, is_parameter=True
    ), "endTime parameter should not be required"


def test_fn_adapter(parsed_tree: CodeTree[Node]) -> None:
    """Test the AwareFunctionAdapter for function definitions."""
    function_adapter = AwareFunctionAdapter()

    # Test standalone functions
    standalone_functions = list(function_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(standalone_functions) == 6, "Should find 6 standalone functions"

    # Test function names
    fn_names = [_safe_text(function_adapter.get_name(function).node) for function in standalone_functions]
    assert "validateEmail" in fn_names, "Should find validateEmail function"
    assert "sendNotification" in fn_names, "Should find sendNotification function"
    assert "addUser" in fn_names, "Should find addUser function"
    assert "scheduleTask" in fn_names, "Should find scheduleTask function"
    assert "processUserData" in fn_names, "Should find processUserData function"
    assert "resolveUserArtifacts" in fn_names, "Should find resolveUserArtifacts function"

    # Test async function
    send_notification_fn = next(
        function
        for function in standalone_functions
        if _safe_text(function_adapter.get_name(function).node) == "sendNotification"
    )
    assert function_adapter.is_async(send_notification_fn), "sendNotification should be async"

    # Test parameters
    params = list(function_adapter.get_parameters(send_notification_fn))
    assert len(params) == 4, "sendNotification should have 4 parameters"

    # Test return type
    return_type = function_adapter.get_return_type(send_notification_fn)
    assert return_type is not None, "Return type should not be None"
    assert return_type.node_text() == "Bool", "Return type should be Bool"

    tuple_fn = next(
        function
        for function in standalone_functions
        if _safe_text(function_adapter.get_name(function).node) == "resolveUserArtifacts"
    )
    tuple_return = function_adapter.get_return_type(tuple_fn)
    assert tuple_return is not None, "Tuple return node should not be None"
    assert tuple_return.node_text() == "(user User, post Post, comment Comment)"

    # Named return parameters should be exposed for tuple returns
    out_params = function_adapter.get_return_parameters(tuple_fn)
    assert out_params is not None, "Tuple return should expose return parameters"
    out_params = list(out_params)
    assert len(out_params) == 3
    # Sort to ensure deterministic ordering
    out_params.sort(key=lambda x: x.byte_start or 0)
    out_texts = [p.node_text() for p in out_params]
    # Sort to ensure deterministic ordering
    assert out_texts == ["user User", "post Post", "comment Comment"]


def test_edge_adapter(parsed_tree: CodeTree[Node]) -> None:
    """Test the AwareEdgeAdapter for edge definitions."""
    edge_adapter = AwareEdgeAdapter()

    # Find all edge definitions
    edge_nodes = list(edge_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(edge_nodes) == 2, "Should find 2 edge definitions"

    # Test edge names
    edge_names = [_safe_text(edge_adapter.get_name(edge).node) for edge in edge_nodes]
    assert "UserPost" in edge_names, "Should find UserPost edge"
    assert "UserComment" in edge_names, "Should find UserComment edge"

    # Test UserPost edge in more detail
    user_post_edge = next(edge for edge in edge_nodes if _safe_text(edge_adapter.get_name(edge).node) == "UserPost")
    assert user_post_edge is not None, "Should find UserPost edge"
    assert (
        _safe_text(edge_adapter.get_name(user_post_edge).node) == "UserPost"
    ), "UserPost edge should have name UserPost"


def test_comment_adapter_linkage(parsed_tree: CodeTree[Node]) -> None:
    """Test the AwareCommentAdapter for comment linkage to functions, classes, and attributes."""
    comment_adapter = AwareCommentAdapter()

    # Find all comments in the source
    comment_nodes = list(comment_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    # Should find comments - exact count depends on sample file but should be > 0
    assert len(comment_nodes) > 0, "Should find comment nodes in the sample file"

    # Track successful linkages by type + collect concrete lookup keys (deterministic assertions)
    linked_to_class = 0
    linked_to_function = 0
    linked_to_attribute = 0
    multiline_comments = 0
    lookup_keys: list[tuple[CodeSectionType, str]] = []
    associated_node_types: list[str] = []

    for comment_node in comment_nodes:
        comment_type = comment_adapter.get_comment_type(comment_node)
        assert comment_type is not None, "Should determine comment type"

        # Test association with code elements
        associated_node = comment_adapter.get_associated_node(comment_node, parsed_tree.source_bytes)

        if associated_node is not None:
            associated_node_types.append(associated_node.node.type)
            # Test section lookup key mapping
            lookup_key = comment_adapter.section_lookup_key(associated_node)

            if lookup_key is not None:
                section_type, section_name = lookup_key
                lookup_keys.append((section_type, section_name))

                # Validate section type and name
                assert section_type in [
                    CodeSectionType.class_,
                    CodeSectionType.function,
                    CodeSectionType.attribute,
                    CodeSectionType.enum,
                ], f"Should map to valid section type, got: {section_type}"

                assert len(section_name) > 0, "Section name should not be empty"
                assert not section_name.startswith("unk@"), "Should extract proper identifier name"

                # Count linkages by type
                if section_type == CodeSectionType.class_:
                    linked_to_class += 1
                elif section_type == CodeSectionType.function:
                    linked_to_function += 1
                elif section_type == CodeSectionType.attribute:
                    linked_to_attribute += 1

        # Test multiline comment detection
        if (
            comment_node.node.type == "comment"
            and comment_node.node_text().startswith("///")
            and comment_node.byte_end > comment_node.node.end_byte
        ):
            multiline_comments += 1

            # Test multiline content extraction
            body_bytes = comment_adapter.body_bytes(comment_node, parsed_tree.source_bytes)
            content_str = body_bytes.decode("utf-8")

            # Should not contain /// markers in the final content
            assert "///" not in content_str, "Processed multiline comment should not contain /// markers"

            # Should contain actual content (not just whitespace)
            assert len(content_str.strip()) > 0, "Multiline comment should have actual content"

    # We should have found at least some comments linked to code elements
    total_linked = linked_to_class + linked_to_function + linked_to_attribute
    assert total_linked > 0, "Should find comments linked to code elements"

    # --- Canonical, deterministic expectations from the sample file ---
    # 1) There must be at least one grouped multiline /// block (e.g. above enum Status)
    assert multiline_comments >= 1, "Expected at least one grouped multiline /// comment block"

    # 2) We should have at least one class doc bound via /// (e.g. User)
    assert (
        CodeSectionType.class_,
        "User",
    ) in lookup_keys, "Expected /// doc to bind to class User"

    # 3) We should have at least one enum doc bound via /// (Status has top doc block)
    assert (
        CodeSectionType.enum,
        "Status",
    ) in lookup_keys, "Expected /// doc to bind to enum Status"

    # 4) We should have at least one method docstring bound to its function (buildUser is inside class User)
    assert (
        CodeSectionType.function,
        "User.buildUser",
    ) in lookup_keys, "Expected docstring to bind to User.buildUser"

    # 5) We should have at least one inline attribute comment bound to an attribute (e.g. Comment.isApproved)
    assert (
        CodeSectionType.attribute,
        "Comment.isApproved",
    ) in lookup_keys, "Expected inline // comment to bind to Comment.isApproved"

    # Sanity: these are the only node types we expect to associate with
    assert set(associated_node_types).issubset(
        {"class_def", "edge_def", "fn_def", "attr_def", "enum_def", "enum_value_def"}
    )


def test_comment_adapter_with_comments():
    """Test the AwareCommentAdapter with a sample that actually contains comments."""
    from tree_sitter import Parser

    # Sample Aware code with various types of comments
    sample_code = """
/// This is a multiline comment
/// for the Space class that describes
/// what spaces are in the system
class Space {
    id UUID  // This is an inline comment for the id attribute
    name String  // Name of the space
    /// This is a single line doc comment for description
    description String
}

/// Single line comment for a function
fn createSpace(name String) -> Space {

}

// Inline comment not associated with anything
"""

    # Parse the sample code
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    # Create adapters
    comment_adapter = AwareCommentAdapter()

    # Find all comments
    comment_nodes = list(comment_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Should find comments now
    assert len(comment_nodes) > 0, "Should find comment nodes in the sample with comments"

    # Collect lookup keys for deterministic assertions
    keys: list[tuple[CodeSectionType, str]] = []
    for comment_node in comment_nodes:
        # Must always be able to extract content segments (even if empty in weird cases)
        _ = list(comment_adapter.get_content_segments(comment_node, sample_code.encode()))

        associated = comment_adapter.get_associated_node(comment_node, sample_code.encode())
        if not associated:
            continue
        lookup_key = comment_adapter.section_lookup_key(associated)
        if lookup_key:
            keys.append(lookup_key)

    # Expect /// block to bind to class Space
    assert (CodeSectionType.class_, "Space") in keys
    # Expect inline comment to bind to Space.id attribute
    assert (CodeSectionType.attribute, "Space.id") in keys
    # Expect /// line to bind to standalone function createSpace
    assert (CodeSectionType.function, "createSpace") in keys

    # Test that we can extract content segments properly
    multiline_comment = next((c for c in comment_nodes if c.byte_end > c.node.end_byte), None)
    if multiline_comment:
        segments = list(comment_adapter.get_content_segments(multiline_comment, sample_code.encode()))
        assert len(segments) > 1, "Multiline comment should have multiple segments"

        # Verify no segments contain /// markers
        for segment in segments:
            segment_text = sample_code.encode()[segment.byte_start : segment.byte_end].decode("utf-8")
            assert "///" not in segment_text, f"Segment should not contain /// markers: {segment_text}"


def test_comment_adapter_qualified_attribute_linkage():
    """Test that comment adapter generates correct qualified lookup keys for attribute comments."""
    # Sample Aware code with attribute comments
    sample_code = """
class User {
    id UUID  // User identifier attribute
    name String      // User display attribute
    /// Height of the user
    height Float?
}

class Post {
    title String  // Post title attribute
    content String   // Post content
}
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create adapters
    comment_adapter = AwareCommentAdapter()

    # Find all comments
    comment_nodes = list(comment_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Test each comment that should be linked to an attribute
    qualified_names_found: list[str] = []

    for comment_node in comment_nodes:
        # Find associated node
        associated_node = comment_adapter.get_associated_node(comment_node, sample_code.encode())

        if associated_node and associated_node.node.type == "attr_def":
            # Generate lookup key
            lookup_key = comment_adapter.section_lookup_key(associated_node)

            if lookup_key:
                section_type, section_name = lookup_key
                if section_type == CodeSectionType.attribute:
                    qualified_names_found.append(section_name)

    # Verify we found qualified names with parent context
    assert len(qualified_names_found) > 0, "Should find some qualified attribute names"
    # Deterministic: verify a couple of known ones are present
    assert "User.id" in qualified_names_found
    assert "Post.title" in qualified_names_found

    # Check that the qualified names include parent context
    for qualified_name in qualified_names_found:
        assert "." in qualified_name, f"Qualified name '{qualified_name}' should include parent context"
        parent, attribute = qualified_name.split(".", 1)
        assert parent in [
            "User",
            "Post",
        ], f"Parent '{parent}' should be a valid type name"
        assert attribute in [
            "id",
            "name",
            "height",
            "title",
            "content",
        ], f"Attribute '{attribute}' should be a valid attribute name"


def test_void_return_function_keeps_class_field_comment_context() -> None:
    """Void `-> { ... }` methods must not break enclosing class parse context."""
    sample_code = '''
class Graph {
    /// Stable identity for this graph.
    graph_identity GraphIdentity?

    fn delete_node(node_key String) -> {
        """
        Delete one graph node.
        """
    }
}
'''
    tree = parser.parse(sample_code.encode())
    assert not tree.root_node.has_error

    comment_adapter = AwareCommentAdapter()
    comments = list(comment_adapter.match_nodes(tree.root_node, sample_code.encode()))
    field_comment = next(item for item in comments if "Stable identity for this graph" in item.node_text())
    associated = comment_adapter.get_associated_node(
        field_comment,
        sample_code.encode(),
    )
    assert associated is not None
    assert comment_adapter.section_lookup_key(associated) == (
        CodeSectionType.attribute,
        "Graph.graph_identity",
    )


def test_function_docstring_detection():
    """Test that docstrings inside functions are properly detected and linked."""
    from tree_sitter import Parser

    # Sample Aware code with function docstrings
    sample_code = '''
class ContentPartText {
    id UUID = "gen_random_uuid()"
    text String

    fn get_next_segment_position(p_content_part_text_id UUID) -> Int {
        """
        Gets the next available position for a text segment within a content part text.
        Parameters:
            p_content_part_text_id: The UUID of the content part text.
        """
    }

    fn process_text(content String, options Json?) -> Bool {
        """
        Processes text content with optional parameters.
        Returns true if processing was successful.
        """
    }
}

fn standalone_function(param String) -> String {
    """
    This is a standalone function with a docstring.
    It returns the processed parameter.
    """
}
'''

    # Parse the sample code
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    # Create comment adapter
    comment_adapter = AwareCommentAdapter()

    # Find all comments (including docstrings)
    comment_nodes = list(comment_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Should find 3 docstrings
    assert len(comment_nodes) >= 3, f"Should find at least 3 docstring comments, found {len(comment_nodes)}"

    # Test that docstrings are associated with functions
    function_linked_docstrings = 0
    function_names: set[str] = set()

    for comment_node in comment_nodes:
        # Check if this is a docstring (block type indicates synthetic docstring from function)
        if comment_node.node.type == "block" and comment_node.byte_start != comment_node.node.start_byte:
            # Test content extraction using content segments
            content_segments = list(comment_adapter.get_content_segments(comment_node, sample_code.encode()))
            assert len(content_segments) > 0, "Should have content segments"

            # Get the content from the first segment
            if len(content_segments) == 1:
                content_bytes = sample_code.encode()[content_segments[0].byte_start : content_segments[0].byte_end]
            else:
                # Multiple segments - combine them
                segment_texts: list[str] = []
                for segment in content_segments:
                    segment_text = sample_code.encode()[segment.byte_start : segment.byte_end].decode("utf-8")
                    segment_texts.append(segment_text)
                content_bytes = "\n".join(segment_texts).encode("utf-8")

            content_text = content_bytes.decode("utf-8")

            # Verify content is properly extracted (no triple quotes)
            assert '"""' not in content_text, f"Content should not contain triple quotes: {content_text[:50]}"
            assert len(content_text.strip()) > 0, "Content should not be empty"

            # Test association with function
            associated = comment_adapter.get_associated_node(comment_node, sample_code.encode())
            if associated and associated.node.type == "fn_def":
                function_linked_docstrings += 1

                # Test lookup key generation
                lookup_key = comment_adapter.section_lookup_key(associated)
                assert lookup_key is not None, "Should generate lookup key for function"
                section_type, section_name = lookup_key
                assert section_type == CodeSectionType.function, "Should map to FUNCTION section type"
                function_names.add(section_name)

    # Should have 3 docstrings linked to functions
    assert (
        function_linked_docstrings == 3
    ), f"Should find exactly 3 function docstrings, found {function_linked_docstrings}"

    # Verify the specific function names are detected
    expected_functions = {
        "ContentPartText.get_next_segment_position",
        "ContentPartText.process_text",
        "standalone_function",
    }
    assert function_names == expected_functions, f"Expected functions {expected_functions}, found {function_names}"


def test_import_adapter_basic():
    """Test the AwareImportAdapter with basic import statements."""
    # Sample Aware code with various import statements
    sample_code = """
import module.submodule;
import package.utils as helpers;
import external.*;
import core.types;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Should find 4 import statements
    assert len(import_nodes) == 4, f"Should find 4 import statements, found {len(import_nodes)}"

    # Test first import: "import module.submodule;"
    first_import = import_nodes[0]

    # Test basic properties
    assert not import_adapter.is_from_import(first_import), "Aware doesn't have from-imports"
    assert not import_adapter.is_star_import(first_import), "First import should not be star import"
    assert import_adapter.get_relative_level(first_import) == 0, "Aware doesn't support relative imports"

    # Test module name extraction
    module_name = import_adapter.get_module_name(first_import)
    module_text = _safe_text(module_name.node)
    assert module_text == "module.submodule", f"Module name should be 'module.submodule', got '{module_text}'"

    # Test import names
    import_names = list(import_adapter.get_import_names(first_import))
    assert len(import_names) == 1, "Should have one import name"
    name_node, alias_node = import_names[0]
    assert _safe_text(name_node.node) == "module.submodule", "Import name should match module name"
    assert alias_node is None, "First import should not have alias"


def test_import_adapter_star_import():
    """Test the AwareImportAdapter with star imports."""
    # Sample Aware code with star import
    sample_code = """
import external.*;
import utils.* as helpers;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Should find 2 import statements
    assert len(import_nodes) == 2, f"Should find 2 import statements, found {len(import_nodes)}"

    # Test first star import: "import external.*;"
    first_import = import_nodes[0]
    assert import_adapter.is_star_import(first_import), "First import should be star import"

    # Test module name for star import (should return just the module part)
    module_name = import_adapter.get_module_name(first_import)
    module_text = _safe_text(module_name.node)
    assert module_text == "external", f"Star import module name should be 'external', got '{module_text}'"

    # Test import names for star import
    import_names = list(import_adapter.get_import_names(first_import))
    assert len(import_names) == 1, "Star import should have one import name"
    name_node, alias_node = import_names[0]
    assert _safe_text(name_node.node) == "*", "Star import name should be '*'"
    assert alias_node is None, "First star import should not have alias"

    # Test second star import with alias: "import utils.* as helpers;"
    second_import = import_nodes[1]
    assert import_adapter.is_star_import(second_import), "Second import should be star import"

    # Test import names for aliased star import
    import_names = list(import_adapter.get_import_names(second_import))
    assert len(import_names) == 1, "Aliased star import should have one import name"
    name_node, alias_node = import_names[0]
    assert _safe_text(name_node.node) == "*", "Star import name should be '*'"
    assert alias_node is not None, "Second star import should have alias"
    assert _safe_text(alias_node.node) == "helpers", "Alias should be 'helpers'"


def test_import_adapter_aliased_imports():
    """Test the AwareImportAdapter with aliased imports."""
    # Sample Aware code with aliased imports
    sample_code = """
import package.utils as helpers;
import core.database as db;
import models.user as UserModel;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Should find 3 import statements
    assert len(import_nodes) == 3, f"Should find 3 import statements, found {len(import_nodes)}"

    # Test each aliased import
    expected_imports = [
        ("package.utils", "helpers"),
        ("core.database", "db"),
        ("models.user", "UserModel"),
    ]

    for i, (expected_module, expected_alias) in enumerate(expected_imports):
        import_node = import_nodes[i]

        # Test module name
        module_name = import_adapter.get_module_name(import_node)
        module_text = _safe_text(module_name.node)
        assert module_text == expected_module, f"Import {i+1} module should be '{expected_module}', got '{module_text}'"

        # Test import names and alias
        import_names = list(import_adapter.get_import_names(import_node))
        assert len(import_names) == 1, f"Import {i+1} should have one import name"
        name_node, alias_node = import_names[0]

        assert _safe_text(name_node.node) == expected_module, f"Import {i+1} name should be '{expected_module}'"
        assert alias_node is not None, f"Import {i+1} should have alias"
        assert _safe_text(alias_node.node) == expected_alias, f"Import {i+1} alias should be '{expected_alias}'"


def test_import_adapter_qualname():
    """Test the qualname generation for import statements."""
    # Sample Aware code with various imports
    sample_code = """
import module.submodule;
import package.utils as helpers;
import external.*;
import core.* as CoreUtils;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Test qualname for each import
    expected_qualnames = [
        "import.module.submodule",
        "import.package.utils:as:helpers",
        "import.external.*",
        "import.core.*:as:CoreUtils",
    ]

    for i, expected_qualname in enumerate(expected_qualnames):
        import_node = import_nodes[i]
        qualname = import_adapter.qualname(import_node)
        assert qualname == expected_qualname, f"Import {i+1} qualname should be '{expected_qualname}', got '{qualname}'"

        # Test with parent
        parent_qualname = import_adapter.qualname(import_node, "parent")
        expected_parent_qualname = f"parent:{expected_qualname}"
        assert (
            parent_qualname == expected_parent_qualname
        ), f"Import {i+1} with parent should be '{expected_parent_qualname}', got '{parent_qualname}'"


def test_import_adapter_alias_bindings():
    """Test the alias bindings extraction for import statements."""
    # Sample Aware code with various imports
    sample_code = """
import module.submodule;
import package.utils as helpers;
import external.*;
import core.* as CoreUtils;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Test alias bindings for each import
    # Import 1: "import module.submodule;" -> ('module', 'module.submodule')
    bindings1 = list(import_adapter.get_alias_bindings(import_nodes[0]))
    assert len(bindings1) == 1, "First import should have one binding"
    assert bindings1[0] == (
        "module",
        "module.submodule",
    ), f"First binding should be ('module', 'module.submodule'), got {bindings1[0]}"

    # Import 2: "import package.utils as helpers;" -> ('helpers', 'package.utils')
    bindings2 = list(import_adapter.get_alias_bindings(import_nodes[1]))
    assert len(bindings2) == 1, "Second import should have one binding"
    assert bindings2[0] == (
        "helpers",
        "package.utils",
    ), f"Second binding should be ('helpers', 'package.utils'), got {bindings2[0]}"

    # Import 3: "import external.*;" -> no bindings (star imports without alias don't create bindings)
    bindings3 = list(import_adapter.get_alias_bindings(import_nodes[2]))
    assert len(bindings3) == 0, "Third import (star without alias) should have no bindings"

    # Import 4: "import core.* as CoreUtils;" -> ('CoreUtils', 'core.*')
    bindings4 = list(import_adapter.get_alias_bindings(import_nodes[3]))
    assert len(bindings4) == 1, "Fourth import should have one binding"
    assert bindings4[0] == (
        "CoreUtils",
        "core.*",
    ), f"Fourth binding should be ('CoreUtils', 'core.*'), got {bindings4[0]}"


def test_import_adapter_body_bytes():
    """Test the body_bytes normalization for import statements."""
    # Sample Aware code with imports that need normalization
    sample_code = """
import   module.submodule  ;  // with comment
import package.utils    as   helpers;
import external.*;
"""

    # Parse the sample code
    tree = parser.parse(sample_code.encode())

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, sample_code.encode()))

    # Test body bytes normalization
    for i, import_node in enumerate(import_nodes):
        body_bytes = import_adapter.body_bytes(import_node, sample_code.encode())
        body_text = body_bytes.decode("utf-8")

        # Should not contain comments
        assert "//" not in body_text, f"Import {i+1} body should not contain comments"

        # Should not contain extra semicolons
        assert not body_text.endswith(";"), f"Import {i+1} body should not end with semicolon"

        # Should be normalized (no excessive whitespace)
        assert "  " not in body_text, f"Import {i+1} body should not contain excessive whitespace"

        # Should be trimmed
        assert body_text == body_text.strip(), f"Import {i+1} body should be trimmed"


def test_import_adapter_with_sample_file(sample_aware_file: str) -> None:
    """Test the import adapter with the actual sample file if it contains imports."""
    # Read the sample file to check if it has imports
    with open(sample_aware_file, "r") as f:
        content = f.read()

    # Only run this test if the file contains imports
    if "import " not in content:
        pytest.skip("Sample file does not contain import statements")

    # Parse the sample file
    with open(sample_aware_file, "rb") as f:
        source_bytes = f.read()

    tree = parser.parse(source_bytes)

    # Create import adapter
    import_adapter = AwareImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(tree.root_node, source_bytes))

    # Test that we can process all imports without errors
    for import_node in import_nodes:
        # Test basic methods don't throw errors
        assert not import_adapter.is_from_import(import_node), "Aware doesn't have from-imports"
        _ = import_adapter.is_star_import(import_node)
        relative_level = import_adapter.get_relative_level(import_node)
        assert relative_level == 0, "Aware doesn't support relative imports"

        # Test module name extraction
        module_name = import_adapter.get_module_name(import_node)
        assert module_name is not None, "Should extract module name"

        # Test import names extraction
        import_names = list(import_adapter.get_import_names(import_node))
        assert len(import_names) > 0, "Should extract import names"

        # Test qualname generation
        qualname = import_adapter.qualname(import_node)
        assert len(qualname) > 0, "Should generate qualname"

        # Test body bytes
        body_bytes = import_adapter.body_bytes(import_node, source_bytes)
        assert len(body_bytes) > 0, "Should generate body bytes"

        # Test alias bindings
        _ = list(import_adapter.get_alias_bindings(import_node))
        # Bindings may be empty for star imports without aliases


def test_annotation_adapter_extracts_path_verb_args():
    """Test the AwareAnnotationAdapter for ANN statements."""
    from tree_sitter import Parser

    sample_code = """
class User {
    posts Post[]
}

class Post {
    title String
}

ann default.User::posts load forward eager reverse lazy
ann default.User overlay entity "class" language "python" rename UserDTO wire_name user_dto
"""

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())
    adapter = AwareAnnotationAdapter()
    nodes = list(adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(nodes) == 2, "Should find 2 ANN statements"

    # Sort deterministically by raw text
    nodes.sort(key=lambda n: adapter.body_bytes(n, sample_code.encode()))

    # load
    load_node = next(n for n in nodes if adapter.get_verb(n) == "load")
    assert adapter.get_path(load_node) == "default.User::posts"
    assert adapter.get_args(load_node) == ["forward", "eager", "reverse", "lazy"]

    # overlay
    ov_node = next(n for n in nodes if adapter.get_verb(n) == "overlay")
    assert adapter.get_path(ov_node) == "default.User"
    assert adapter.get_args(ov_node) == [
        "entity",
        "class",
        "language",
        "python",
        "rename",
        "UserDTO",
        "wire_name",
        "user_dto",
    ]


def test_annotation_adapter_preserves_discriminator_cases_with_keyword_variants():
    """Keyword-like discriminator variants such as `class` must remain in ANN args."""
    from tree_sitter import Parser

    sample_code = (
        "ann default.AttributeTypeDescriptor oneof identity class_config enum_config primitive_config "
        "discriminator kind class class_config enum enum_config primitive primitive_config"
    )

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())
    adapter = AwareAnnotationAdapter()
    nodes = list(adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(nodes) == 1

    node = nodes[0]
    assert adapter.get_path(node) == "default.AttributeTypeDescriptor"
    assert adapter.get_verb(node) == "oneof"
    assert adapter.get_args(node) == [
        "identity",
        "class_config",
        "enum_config",
        "primitive_config",
        "discriminator",
        "kind",
        "class",
        "class_config",
        "enum",
        "enum_config",
        "primitive",
        "primitive_config",
    ]


def test_projection_adapter_extracts_projection_blocks() -> None:
    """Ensure `projection { ... }` parses as first-class projection sections."""
    from tree_sitter import Parser

    from aware_grammar.adapters.projection_adapter import AwareProjectionAdapter

    sample_code = """
projection ActorFocus is_branchable {
    root actor.ActorFocus
    branch main
    actor.ActorFocus::suggestions
    actor.ActorFocus::focus aware_identity.Identity
}
""".strip()

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    ann_adapter = AwareAnnotationAdapter()
    ann_nodes = list(ann_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert ann_nodes == []

    proj_adapter = AwareProjectionAdapter()
    projections = list(proj_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(projections) == 1
    projection = projections[0]

    assert proj_adapter.get_name(projection).node_text().strip() == "ActorFocus"

    options = proj_adapter.get_options(projection)
    assert [o.keyword for o in options] == ["is_branchable"]

    root = proj_adapter.get_root_type(projection)
    assert root is not None
    assert root.node_text().strip() == "actor.ActorFocus"

    edges = proj_adapter.get_edges(projection)
    assert len(edges) == 2

    suggestions = edges[0]
    assert proj_adapter.get_edge_type(suggestions).node_text().strip() == "actor.ActorFocus"
    assert proj_adapter.get_edge_member(suggestions).node_text().strip() == "suggestions"
    assert proj_adapter.get_edge_target(suggestions) is None

    focus = edges[1]
    assert proj_adapter.get_edge_type(focus).node_text().strip() == "actor.ActorFocus"
    assert proj_adapter.get_edge_member(focus).node_text().strip() == "focus"
    focus_target = proj_adapter.get_edge_target(focus)
    assert focus_target is not None
    assert focus_target.node_text().strip() == "aware_identity.Identity"


def test_projection_adapter_extracts_observable_blocks() -> None:
    """Observable keyword is canonical; legacy aliases remain supported."""
    from tree_sitter import Parser

    from aware_grammar.adapters.projection_adapter import AwareProjectionAdapter

    sample_code = """
projection Identity {
    root identity.Identity
    observable onboarding {
        observable welcome construct default { }
    }
}
""".strip()

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode())

    proj_adapter = AwareProjectionAdapter()
    projections = list(proj_adapter.match_nodes(tree.root_node, sample_code.encode()))
    assert len(projections) == 1

    views = proj_adapter.get_views(projections[0])
    assert len(views) == 1
    assert views[0].full_key == "onboarding.welcome"
    assert views[0].kind == "construct"
    assert views[0].is_default is True


def test_treesitter_parses_experience_observable_hierarchy() -> None:
    from tree_sitter import Parser

    sample_code = """
experience AgentMind on Agent {
    branch default default { }
    branch economical_agent { }

    observable agent {
        view home default state Agent { }
    }

    observable process {
        view home state Process { }
    }

    observable thread {
        view home state Thread { }
    }
}
""".strip()

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode("utf-8"))

    assert tree.root_node.has_error is False
    top = [n for n in tree.root_node.named_children if n.type == "experience_def"]
    assert len(top) == 1
    exp = top[0]

    name_node = exp.child_by_field_name("name")
    projection_node = exp.child_by_field_name("projection")
    assert name_node is not None
    assert projection_node is not None
    assert name_node.text is not None
    assert projection_node.text is not None
    assert name_node.text.decode("utf-8") == "AgentMind"
    assert projection_node.text.decode("utf-8") == "Agent"

    branch_nodes: list[Node] = []
    observable_nodes: list[Node] = []
    for child in exp.named_children:
        if child.type != "experience_item":
            continue
        for inner in child.named_children:
            if inner.type == "experience_branch":
                branch_nodes.append(inner)
            elif inner.type == "experience_observable_group":
                observable_nodes.append(inner)

    assert len(branch_nodes) == 2
    assert len(observable_nodes) == 3


def test_treesitter_parses_environment_experience_profile_hierarchy() -> None:
    from tree_sitter import Parser

    def _find_nodes(node: Node, node_type: str) -> list[Node]:
        matches: list[Node] = []
        if node.type == node_type:
            matches.append(node)
        for child in node.named_children:
            matches.extend(_find_nodes(child, node_type))
        return matches

    sample_code = """
experience home_story {
    profile os.default {
        title "Home Story OS"
        narrative "Primary home environment experience."

        process continuous home default {
            intent workspace

            thread home.main default {
                workspace_view thread.workspace
                projection home_story view overview.home default
                layout configuration_map default {
                    section main projection home_story view overview.home binding home.main default
                }
                layout scene_view
            }
        }
    }
}
""".strip()

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(sample_code.encode("utf-8"))

    assert tree.root_node.has_error is False
    scopes = [n for n in tree.root_node.named_children if n.type == "experience_profile_scope_def"]
    assert len(scopes) == 1
    scope = scopes[0]

    scope_name = scope.child_by_field_name("name")
    assert scope_name is not None
    assert scope_name.text is not None
    assert scope_name.text.decode("utf-8") == "home_story"

    profiles = _find_nodes(scope, "experience_profile_def")
    assert len(profiles) == 1
    assert _safe_text(profiles[0].child_by_field_name("key")).strip() == "os.default"

    processes = _find_nodes(scope, "experience_profile_process_def")
    assert len(processes) == 1
    assert _safe_text(processes[0].child_by_field_name("type")).strip() == "continuous"
    assert _safe_text(processes[0].child_by_field_name("key")).strip() == "home"

    threads = _find_nodes(scope, "experience_profile_thread_def")
    assert len(threads) == 1
    assert _safe_text(threads[0].child_by_field_name("key")).strip() == "home.main"

    projections = _find_nodes(scope, "experience_profile_thread_projection_def")
    assert len(projections) == 1
    assert _safe_text(projections[0].child_by_field_name("experience")).strip() == "home_story"
    assert _safe_text(projections[0].child_by_field_name("view_key")).strip() == "overview.home"

    layouts = _find_nodes(scope, "experience_profile_thread_layout_def")
    assert len(layouts) == 2
    assert _safe_text(layouts[0].child_by_field_name("layout_key")).strip() == "configuration_map"
    assert _safe_text(layouts[1].child_by_field_name("layout_key")).strip() == "scene_view"
    layout_sections = _find_nodes(scope, "experience_profile_thread_layout_section_def")
    assert len(layout_sections) == 1
    assert _safe_text(layout_sections[0].child_by_field_name("section_key")).strip() == "main"
    assert _safe_text(layout_sections[0].child_by_field_name("experience")).strip() == "home_story"
    assert _safe_text(layout_sections[0].child_by_field_name("view_key")).strip() == "overview.home"
    assert _safe_text(layout_sections[0].child_by_field_name("binding_key")).strip() == "home.main"
