"""Test suite for Python language adapters."""

import pytest
from pathlib import Path

# Aware Core
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter
from aware_code.tree.tree import CodeTree
from aware_code.node.node import CodeNode

# Kernel Graph Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.expression.code_section_expression_enums import (
    CodeSectionExpressionType,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Python Grammar
from python_grammar.adapters.attribute_adapter import PythonAttributeAdapter
from python_grammar.adapters.class_adapter import PythonClassAdapter
from python_grammar.adapters.function_adapter import PythonFunctionAdapter
from python_grammar.adapters.enum_adapter import PythonEnumAdapter
from python_grammar.adapters.enum_value_adapter import PythonEnumValueAdapter
from python_grammar.adapters.comment_adapter import PythonCommentAdapter, PythonCommentTargetType
from python_grammar.adapters.decorator_adapter import PythonDecoratorAdapter
from python_grammar.adapters.expression_adapter import PythonExpressionAdapter
from python_grammar.adapters.import_adapter import PythonImportAdapter

from tree_sitter import Parser
from tree_sitter_python.tree_sitter_language import PYTHON_LANGUAGE

# Set up language and parser
parser = Parser(language=PYTHON_LANGUAGE)


@pytest.fixture(scope="session")
def sample_python_file():
    """Fixture that returns the path to the sample Python file."""
    current_dir = Path(__file__).parent
    sample_file = current_dir / "samples" / "user_post.py"

    if not sample_file.exists():
        pytest.fail(f"Sample file not found: {sample_file}")

    return str(sample_file)


@pytest.fixture
def parsed_tree(sample_python_file):
    """Fixture that returns the parsed tree for the sample file."""
    with open(sample_python_file, "rb") as f:
        source_bytes = f.read()

    tree = parser.parse(source_bytes)
    root_node = CodeNode(node=tree.root_node, byte_start=tree.root_node.start_byte, byte_end=tree.root_node.end_byte)

    return CodeTree(root=root_node, source_bytes=source_bytes)


def test_tree_adapter(sample_python_file):
    """Test the CodeTreeSitterAdapter with Python code."""
    adapter = CodeTreeSitterAdapter(language=PYTHON_LANGUAGE)
    code_tree = adapter.parse(sample_python_file)

    assert code_tree is not None, "Tree adapter should return a CodeTree"
    assert code_tree.root is not None, "CodeTree should have a root node"
    assert len(code_tree.source_bytes) > 0, "CodeTree should have source bytes"


def test_class_adapter(parsed_tree):
    """Test the PythonClassAdapter for class definitions."""
    adapter = PythonClassAdapter()

    # Find all class definitions
    class_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    assert (
        len(class_nodes) == 6
    ), f"Should find 6 class definitions: User, Post, Comment, Image, UserPost, UserComment. Found: {','.join([adapter.get_name(node).node_text() for node in class_nodes])}"

    # Test class names
    class_names = [adapter.get_name(node).node_text() for node in class_nodes]
    assert "User" in class_names, "Should find User class"
    assert "Post" in class_names, "Should find Post class"
    assert "Comment" in class_names, "Should find Comment class"
    assert "Image" in class_names, "Should find Image class"
    assert "UserPost" in class_names, "Should find UserPost class"
    assert "UserComment" in class_names, "Should find UserComment class"

    # Test User class in more detail
    user_node = next(node for node in class_nodes if adapter.get_name(node).node_text() == "User")

    # Test attributes in User
    attributes = list(adapter.get_attributes(user_node))
    assert len(attributes) > 0, "User should have attributes"

    # Test methods in User
    methods = list(adapter.get_methods(user_node))
    assert len(methods) == 10, "User should have 10 methods"

    # Test qualname
    assert adapter.qualname(user_node) == "User", "Qualname should be 'User'"


def test_class_adapter_modifiers_keyword_bases():
    """Test the new PythonClassAdapter methods for modifiers, keyword, and bases extraction."""
    # Create test Python code with class inheritance
    sample_code = '''
class User(BaseModel, Serializable):
    """A user class with multiple inheritance."""
    id: int
    name: str

class Post:
    """A simple post class with no inheritance."""
    title: str
    content: str

class Comment(Post, Timestamped):
    """A comment class inheriting from Post and Timestamped."""
    content: str
    author: User
'''.encode()

    # Parse the test code
    tree = parser.parse(sample_code)

    # Test our adapter
    adapter = PythonClassAdapter()

    # Find all class definitions
    class_nodes = list(adapter.match_nodes(tree.root_node, sample_code))
    assert len(class_nodes) == 3, "Should find 3 class definitions"

    # Test each class
    for class_node in class_nodes:
        class_name = adapter.get_name(class_node).node_text()
        print(f"Testing {class_name} class...")

        # Test get_keyword - should return 'class' keyword
        keyword_node = adapter.get_keyword(class_node)
        assert keyword_node is not None, f"{class_name} should have keyword node"
        assert keyword_node.node_text() == "class", f"Keyword should be 'class' for {class_name}"

        # Test get_modifiers - should return empty (not implemented yet)
        modifiers = list(adapter.get_modifiers(class_node))
        assert len(modifiers) == 0, f"{class_name} should have no modifiers (not implemented yet)"

        # Test get_bases - should return appropriate base classes
        bases = list(adapter.get_bases(class_node))
        base_names = [base.node_text() for base in bases]

        if class_name == "User":
            assert len(bases) == 2, "User should have 2 base classes"
            assert "BaseModel" in base_names, "User should inherit from BaseModel"
            assert "Serializable" in base_names, "User should inherit from Serializable"
        elif class_name == "Post":
            assert len(bases) == 0, "Post should have no base classes"
        elif class_name == "Comment":
            assert len(bases) == 2, "Comment should have 2 base classes"
            assert "Post" in base_names, "Comment should inherit from Post"
            assert "Timestamped" in base_names, "Comment should inherit from Timestamped"


def test_attribute_adapter(parsed_tree):
    """Test the PythonAttributeAdapter for attribute definitions."""
    class_adapter = PythonClassAdapter()
    attribute_adapter = PythonAttributeAdapter()

    # Get the User class
    user_node = next(
        node
        for node in class_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if class_adapter.get_name(node).node_text() == "User"
    )

    # Get attributes in User
    attributes = list(class_adapter.get_attributes(user_node))

    # Test finding an attribute's name
    id_attr = next(iter(attributes))  # Get the first attribute
    name_node = attribute_adapter.get_name(id_attr, is_parameter=False)
    assert name_node is not None, "Should be able to extract attribute name"

    # Test default value
    name_attr = None
    for attr in attributes:
        try:
            name = attribute_adapter.get_name(attr, is_parameter=False).node_text()
            if "name" in name:
                name_attr = attr
                break
        except (ValueError, AttributeError):
            continue

    assert name_attr is not None, "Should find name attribute"
    default_val = attribute_adapter.get_default_value(name_attr, is_parameter=False)
    assert default_val is not None, "Name attribute should have a default value"


def test_function_adapter(parsed_tree):
    """Test the PythonFunctionAdapter for function definitions."""
    fn_adapter = PythonFunctionAdapter()

    # Test standalone functions
    standalone_fns = list(fn_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    # NOTE: On python we find 4 - 2 of them used later as decorators.
    assert (
        len(standalone_fns) == 4
    ), f"Should find 4 standalone functions, found {len(standalone_fns)}: {','.join([fn.node_text() for fn in standalone_fns])}"

    # Test function names
    fn_names = [fn_adapter.get_name(fn).node_text() for fn in standalone_fns]
    assert "validate_email" in fn_names, "Should find validate_email function"
    assert "send_notification" in fn_names, "Should find send_notification function"

    # Test async function
    send_notification_fn = next(
        fn for fn in standalone_fns if fn_adapter.get_name(fn).node_text() == "send_notification"
    )
    assert fn_adapter.is_async(send_notification_fn), "send_notification should be async"

    # Test parameters
    params = list(fn_adapter.get_parameters(send_notification_fn))
    assert len(params) == 2, "send_notification should have 2 parameters"

    # Test return type
    return_type = fn_adapter.get_return_type(send_notification_fn)
    assert return_type is not None, "Should find return type"
    assert return_type.node_text() == "bool", "Return type should be bool"


def test_function_adapter_async_method_qualname(parsed_tree):
    """
    Invariant: adapter-level qualname must be deterministic without external parent context,
    even for async/decorated methods.
    """
    fn_adapter = PythonFunctionAdapter()
    class_adapter = PythonClassAdapter()

    # Find User class
    user_node = next(
        node
        for node in class_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if class_adapter.get_name(node).node_text() == "User"
    )

    # Find send_email method node
    method_nodes = list(class_adapter.get_methods(user_node))
    send_email_node = next(m for m in method_nodes if fn_adapter.get_name(m).node_text() == "send_email")
    assert fn_adapter.is_async(send_email_node), "send_email should be async"

    # Must include class qualification even when wrapped by decorated_definition
    assert fn_adapter.qualname(send_email_node) == "User.send_email"
    assert fn_adapter.reference_string(send_email_node) == "User.send_email"


def test_function_adapter_methods_and_classmethods_param_handling():
    """Validate method/classmethod parameter extraction behavior (self/cls handling)."""
    fn_adapter = PythonFunctionAdapter()
    class_adapter = PythonClassAdapter()
    attr_adapter = PythonAttributeAdapter()

    sample = b"""
class C:
    @classmethod
    def build(cls, name: str) -> "C":
        return C()

    def do(self, x: int, y: int = 0) -> int:
        return x + y

    @staticmethod
    def util(x: int) -> int:
        return x * 2
"""

    tree = parser.parse(sample)
    root = CodeNode(node=tree.root_node, byte_start=tree.root_node.start_byte, byte_end=tree.root_node.end_byte)

    # Find class and its methods
    classes = list(class_adapter.match_nodes(root.node, sample))
    assert len(classes) == 1, "Should find one class"

    methods = list(class_adapter.get_methods(classes[0]))
    # We expect three methods: build, do, util (decorated/undecorated forms)
    names = [fn_adapter.get_name(m).node_text() for m in methods]
    assert set(names) == {"build", "do", "util"}

    # Validate is_method detection
    for m in methods:
        assert fn_adapter.is_method(m), "All class functions should be considered methods by adapter"

    # Map for quick access
    by_name = {fn_adapter.get_name(m).node_text(): m for m in methods}

    # Classmethod: implicit 'cls' should be excluded; only 'name' remains
    build_param_nodes = list(fn_adapter.get_parameters(by_name["build"]))
    build_param_names = [attr_adapter.get_name(p, is_parameter=True).node_text() for p in build_param_nodes]
    assert build_param_names == ["name"], f"Expected only ['name'] for classmethod, got {build_param_names}"

    # Instance method: 'self' should be excluded, leaving x, y
    do_param_nodes = list(fn_adapter.get_parameters(by_name["do"]))
    do_param_names = [attr_adapter.get_name(p, is_parameter=True).node_text() for p in do_param_nodes]
    assert do_param_names[:2] == ["x", "y"], f"Expected params ['x','y'], got {do_param_names}"

    # Staticmethod: no self/cls to exclude; should include 'x'
    util_param_nodes = list(fn_adapter.get_parameters(by_name["util"]))
    util_param_names = [attr_adapter.get_name(p, is_parameter=True).node_text() for p in util_param_nodes]
    assert util_param_names == ["x"], f"Expected ['x'] for staticmethod, got {util_param_names}"


def test_decorator_adapter(parsed_tree):
    """Test the PythonDecoratorAdapter for decorator definitions."""
    decorator_adapter = PythonDecoratorAdapter()

    # Find all decorator nodes
    decorator_nodes = list(decorator_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(decorator_nodes) >= 5, f"Should find at least 5 decorators, found {len(decorator_nodes)}"

    # Categorize decorators by name
    network_decorators = []
    intelligent_object_decorators = []

    for dec_node in decorator_nodes:
        name_node = decorator_adapter.get_name(dec_node)
        name = name_node.node_text()
        if name == "network":
            network_decorators.append(dec_node)
        elif name == "intelligent_object":
            intelligent_object_decorators.append(dec_node)

    # Verify we found the expected decorators
    assert len(network_decorators) >= 3, "Should find at least 3 network decorators"
    assert len(intelligent_object_decorators) >= 2, "Should find at least 2 intelligent_object decorators"

    # Test decorator arguments with new tuple format
    for dec_node in network_decorators:
        args = list(decorator_adapter.get_arguments(dec_node))
        assert len(args) >= 1, "Network decorator should have at least 1 argument"
        # The required_access argument should be present in all network decorators
        has_required_access = False
        for name_node, value_node in args:
            if name_node:  # This is a keyword argument
                name_text = name_node.node_text()
                if name_text == "required_access":
                    has_required_access = True
                    break
            else:  # This is a positional argument, check if it contains required_access
                arg_text = value_node.node_text()
                if "required_access=" in arg_text:
                    has_required_access = True
                    break
        assert has_required_access, "Network decorator should have required_access argument"

    # Test decorator targets
    for dec_node in intelligent_object_decorators:
        target = decorator_adapter.get_target(dec_node)
        assert target is not None, "Decorator should have a target"
        target_type = decorator_adapter.get_target_type(dec_node)
        assert target_type == "class", "intelligent_object should decorate a class"

    # Test finding a specific function decorator
    send_email_decorator = None
    for dec_node in network_decorators:
        target = decorator_adapter.get_target(dec_node)
        if target:
            target_children = list(target.node.children)
            for child in target_children:
                if child.type == "identifier" and child.text and child.text.decode("utf-8") == "send_email":
                    send_email_decorator = dec_node
                    break
            if send_email_decorator:
                break

    assert send_email_decorator is not None, "Should find decorator for send_email method"

    # Test qualname for the decorator
    qualname = decorator_adapter.qualname(send_email_decorator)
    assert "network" in qualname, "Qualname should include the decorator name"


def test_expression_adapter(parsed_tree):
    """Test the PythonExpressionAdapter for expression classification."""
    expression_adapter = PythonExpressionAdapter()
    decorator_adapter = PythonDecoratorAdapter()

    # Find decorator nodes to test expression classification on their arguments
    decorator_nodes = list(decorator_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(decorator_nodes) > 0, "Should find at least one decorator to test expressions"

    # Test expression classification on decorator arguments
    expression_count = 0
    for dec_node in decorator_nodes:
        args = list(decorator_adapter.get_arguments(dec_node))
        for name_node, value_node in args:
            expression_count += 1

            # Test classification
            expr_type = expression_adapter.classify(value_node)
            assert expr_type is not None, "Should be able to classify expression"

            # Test body_bytes normalization
            body_bytes = expression_adapter.body_bytes(value_node, parsed_tree.source_bytes)
            assert isinstance(body_bytes, bytes), "body_bytes should return bytes"
            assert len(body_bytes) > 0, "body_bytes should not be empty"

            # Test qualname generation
            qualname = expression_adapter.qualname(value_node)
            assert isinstance(qualname, str), "qualname should return a string"
            assert "@" in qualname, "qualname should contain position marker"

            # Test specific expression types based on node content
            value_text = value_node.node_text()
            if value_text.startswith('"') or value_text.startswith("'"):
                # String literal
                assert (
                    expr_type == CodeSectionExpressionType.literal
                ), f"String '{value_text}' should be classified as LITERAL"
            elif "(" in value_text and ")" in value_text:
                # Likely a call expression
                assert expr_type == CodeSectionExpressionType.call, f"Call '{value_text}' should be classified as CALL"
            elif value_text.isdigit() or (value_text.replace(".", "").isdigit() and value_text.count(".") <= 1):
                # Numeric literal
                assert (
                    expr_type == CodeSectionExpressionType.literal
                ), f"Number '{value_text}' should be classified as LITERAL"
            elif value_text.replace(".", "").replace("_", "").isalnum() and not value_text.isdigit():
                # Likely an identifier (but not a pure number)
                assert (
                    expr_type == CodeSectionExpressionType.identifier
                ), f"Identifier '{value_text}' should be classified as IDENTIFIER"

    assert expression_count > 0, "Should have tested at least one expression"


def test_enum_adapter(parsed_tree):
    """Test the PythonEnumAdapter for enum definitions."""
    enum_adapter = PythonEnumAdapter()

    # Find all enum definitions
    enum_nodes = list(enum_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(enum_nodes) == 2, "Should find 2 enum definitions"

    # Test enum name
    enum_names = [enum_adapter.get_name(enum).node_text() for enum in enum_nodes]
    assert "Status" in enum_names, "Should find Status enum"
    assert "AccessLevelType" in enum_names, "Should find AccessLevelType enum"

    # Test Status enum in more detail
    status_enum = next(enum for enum in enum_nodes if enum_adapter.get_name(enum).node_text() == "Status")

    # Extract enum values
    enum_values = list(enum_adapter.get_values(status_enum))
    assert len(enum_values) == 3, "Status enum should have 3 values"

    # Test enum values
    value_names = []
    for val in enum_values:
        name = val.node_text()
        value_names.append(name)

    assert "active" in value_names, "Should find active enum value"
    assert "inactive" in value_names, "Should find inactive enum value"
    assert "pending" in value_names, "Should find pending enum value"


def test_enum_value_adapter(parsed_tree):
    """Test the PythonEnumValueAdapter for enum value extraction."""
    enum_adapter = PythonEnumAdapter()
    enum_value_adapter = PythonEnumValueAdapter()

    enum_nodes = list(enum_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(enum_nodes) == 2, "Should find 2 enum definitions"

    status_enum = next(enum for enum in enum_nodes if enum_adapter.get_name(enum).node_text() == "Status")
    status_values = list(enum_value_adapter.match_nodes(status_enum.node, parsed_tree.source_bytes))
    status_value_names = [enum_value_adapter.get_name(v).node_text() for v in status_values]
    assert status_value_names == ["active", "inactive", "pending"]

    access_enum = next(enum for enum in enum_nodes if enum_adapter.get_name(enum).node_text() == "AccessLevelType")
    access_values = list(enum_value_adapter.match_nodes(access_enum.node, parsed_tree.source_bytes))
    access_value_names = [enum_value_adapter.get_name(v).node_text() for v in access_values]
    assert access_value_names == ["read", "write", "admin"]


def test_comment_adapter(parsed_tree):
    """Test the PythonCommentAdapter for comment detection and linkage."""
    comment_adapter = PythonCommentAdapter()
    class_adapter = PythonClassAdapter()
    fn_adapter = PythonFunctionAdapter()

    # Find all comments
    comment_nodes = list(comment_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(comment_nodes) > 0, "Should find at least one comment or docstring"

    # Test docstring detection
    docstring_comments = [
        node for node in comment_nodes if comment_adapter.get_comment_type(node) == CodeSectionCommentType.doc
    ]
    assert len(docstring_comments) > 0, "Should find at least one docstring"

    # Test association with classes and functions
    for comment_node in comment_nodes:
        associated_node = comment_adapter.get_associated_node(comment_node, parsed_tree.source_bytes)
        if associated_node:
            # Check if the associated node is a class
            if associated_node.node.type == "class_definition":
                class_name = class_adapter.get_name(associated_node).node_text()
                assert class_name, f"Associated class should have a name"

                # Verify the target info
                target_type, target_name = comment_adapter.get_comment_target_info(comment_node)
                assert target_type in [
                    PythonCommentTargetType.CLASS,
                    PythonCommentTargetType.METHOD,
                ], f"Comment should be associated with class or method, got {target_type}"

                if target_type == PythonCommentTargetType.CLASS:
                    assert (
                        target_name == class_name
                    ), f"Class comment should be linked to {class_name}, got {target_name}"

            # Check if the associated node is a function
            elif associated_node.node.type == "function_definition":
                function_name = fn_adapter.get_name(associated_node).node_text()
                assert function_name, f"Associated function should have a name"

                # Verify the target info
                target_type, target_name = comment_adapter.get_comment_target_info(comment_node)
                assert (
                    target_type == PythonCommentTargetType.FUNCTION
                ), f"Comment should be associated with function, got {target_type}"
                assert (
                    target_name == function_name
                ), f"Function comment should be linked to {function_name}, got {target_name}"


def test_comment_adapter_section_lookup_key_enum_and_async_method(parsed_tree):
    """
    Invariant: comment adapter section_lookup_key must return the same section types/refs
    that the builder indexes, including:
    - Enum classes (AccessLevelType) -> CodeSectionType.enum
    - Async/decorated methods -> CodeSectionType.function with Class.method qualification
    """
    comment_adapter = PythonCommentAdapter()
    class_adapter = PythonClassAdapter()
    fn_adapter = PythonFunctionAdapter()
    enum_adapter = PythonEnumAdapter()

    comment_nodes = list(comment_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    docstrings = [n for n in comment_nodes if comment_adapter.get_comment_type(n) == CodeSectionCommentType.doc]
    assert docstrings, "Should have docstring nodes in sample"

    # AccessLevelType is an enum class and is intentionally excluded from PythonClassAdapter.match_nodes.
    access_level_enum = next(
        node
        for node in enum_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if enum_adapter.get_name(node).node_text() == "AccessLevelType"
    )
    access_key = comment_adapter.section_lookup_key(access_level_enum)
    assert access_key == (CodeSectionType.enum, "AccessLevelType")

    # send_email docstring should map to FUNCTION lookup key with class qualification
    user_node = next(
        node
        for node in class_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if class_adapter.get_name(node).node_text() == "User"
    )
    send_email_node = next(
        m for m in class_adapter.get_methods(user_node) if fn_adapter.get_name(m).node_text() == "send_email"
    )
    assert fn_adapter.is_async(send_email_node)
    send_email_key = comment_adapter.section_lookup_key(send_email_node)
    assert send_email_key == (CodeSectionType.function, "User.send_email")


def test_import_adapter(parsed_tree):
    """Test the PythonImportAdapter for import statements."""
    import_adapter = PythonImportAdapter()

    # Find all import statements
    import_nodes = list(import_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))

    # We should have at least these imports:
    # - from __future__ import annotations
    # - import os
    # - import sys as system
    # - from datetime import timezone as tz
    # - from typing import *
    # - from . import local_module
    # - from datetime import datetime
    # - from enum import Enum
    # - from pydantic import BaseModel, Field
    # - from typing import Optional
    # - import uuid
    assert len(import_nodes) >= 11, f"Expected at least 11 import nodes, found {len(import_nodes)}"

    # Check from __future__ import annotations
    future_import = None
    for node in import_nodes:
        if b"__future__" in node.node_text().encode("utf-8"):
            future_import = node
            break

    assert future_import is not None, "Should find from __future__ import annotations"
    assert import_adapter.is_from_import(future_import), "Should be a from-import"
    assert not import_adapter.is_star_import(future_import), "Should not be a star import"

    module_name = import_adapter.get_module_name(future_import)
    assert module_name.node_text() == "__future__", "Module name should be __future__"

    names = list(import_adapter.get_import_names(future_import))
    assert len(names) == 1, "Should have one imported name"
    name, alias = names[0]
    assert name.node_text() == "annotations", "Should import annotations"
    assert alias is None, "Should not have an alias"

    # Check import sys as system
    sys_import = None
    for node in import_nodes:
        if b"sys" in node.node_text().encode("utf-8") and not import_adapter.is_from_import(node):
            sys_import = node
            break

    assert sys_import is not None, "Should find import sys as system"
    assert not import_adapter.is_from_import(sys_import), "Should be a regular import"

    names = list(import_adapter.get_import_names(sys_import))
    assert len(names) == 1, "Should have one imported name"
    name, alias = names[0]
    assert name.node_text() == "sys", "Should import sys"
    assert alias is not None, "Should have an alias"
    assert alias.node_text() == "system", "Alias should be system"

    # Check from typing import *
    star_import = None
    for node in import_nodes:
        if b"typing" in node.node_text().encode("utf-8") and b"*" in node.node_text().encode("utf-8"):
            star_import = node
            break

    assert star_import is not None, "Should find from typing import *"
    assert import_adapter.is_from_import(star_import), "Should be a from-import"
    assert import_adapter.is_star_import(star_import), "Should be a star import"

    module_name = import_adapter.get_module_name(star_import)
    assert module_name.node_text() == "typing", "Module name should be typing"

    # Check from . import local_module (relative import)
    relative_import = None
    for node in import_nodes:
        if node.node and b"local_module" in node.node_text().encode("utf-8"):
            relative_import = node
            break

    assert relative_import is not None, "Should find from . import local_module"
    assert import_adapter.is_from_import(relative_import), "Should be a from-import"
    assert import_adapter.get_relative_level(relative_import) == 1, "Should have relative level 1"


def test_import_adapter_reference_string_is_none(parsed_tree):
    """
    Invariant: imports should NOT emit reference_string by default, because import 'qualname'
    is not guaranteed unique (duplicate imports are common) and would cause ref collisions.
    """
    import_adapter = PythonImportAdapter()
    import_nodes = list(import_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert import_nodes, "Should have import nodes"
    assert import_adapter.reference_string(import_nodes[0]) is None
