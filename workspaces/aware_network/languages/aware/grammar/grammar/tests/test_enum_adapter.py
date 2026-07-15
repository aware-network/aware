"""Test suite for the Aware enum adapter."""

import pytest

# Tree-sitter
from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Code Runtime
from aware_code.tree.tree import CodeTree
from aware_code.node.node import CodeNode

# Aware Grammar
from aware_grammar.adapters.enum_adapter import AwareEnumAdapter

# Set up language and parser
parser = Parser(language=AWARE_LANGUAGE)


@pytest.fixture
def sample_enum_source() -> bytes:
    """Sample Aware enum source code."""
    return b"""
    // Color enum definition
    enum Color {
        red = "#ff0000"
        green = "#00ff00"
        blue = "#0000ff"
    }

    // Status enum without values
    enum Status {
        active
        inactive
        pending
    }
    """


@pytest.fixture
def parsed_tree(sample_enum_source: bytes) -> CodeTree[Node]:
    """Fixture that returns the parsed tree for the sample source."""
    tree = parser.parse(sample_enum_source)
    root_node = CodeNode(node=tree.root_node, byte_start=tree.root_node.start_byte, byte_end=tree.root_node.end_byte)
    return CodeTree(root=root_node, source_bytes=sample_enum_source)


def test_enum_adapter_match(parsed_tree: CodeTree[Node]) -> None:
    """Test finding enum definitions."""
    adapter = AwareEnumAdapter()

    enum_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(enum_nodes) == 2, "Should find 2 enum definitions"


def test_enum_adapter_name(parsed_tree: CodeTree[Node]) -> None:
    """Test extracting enum names."""
    adapter = AwareEnumAdapter()

    enum_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    enum_names = [adapter.get_name(node).node_text() for node in enum_nodes]

    assert "Color" in enum_names, "Should find Color enum"
    assert "Status" in enum_names, "Should find Status enum"


def test_enum_adapter_values(parsed_tree: CodeTree[Node]) -> None:
    """Test extracting enum values."""
    adapter = AwareEnumAdapter()

    enum_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    color_enum = next(node for node in enum_nodes if adapter.get_name(node).node_text() == "Color")

    values = list(adapter.get_values(color_enum))
    value_names = [value.node_text() for value in values]

    assert "red" in value_names, "Should find red value"
    assert "green" in value_names, "Should find green value"
    assert "blue" in value_names, "Should find blue value"


def test_enum_adapter_qualname(parsed_tree: CodeTree[Node]) -> None:
    """Test qualname generation."""
    adapter = AwareEnumAdapter()

    enum_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    status_enum = next(node for node in enum_nodes if adapter.get_name(node).node_text() == "Status")

    # Test qualname without parent
    assert adapter.qualname(status_enum) == "Status"

    # Test qualname with parent
    assert adapter.qualname(status_enum, "models") == "Status"


def test_enum_adapter_body_bytes(parsed_tree: CodeTree[Node]) -> None:
    """Test body bytes normalization."""
    adapter = AwareEnumAdapter()

    enum_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    color_enum = next(node for node in enum_nodes if adapter.get_name(node).node_text() == "Color")

    body_bytes = adapter.body_bytes(color_enum, parsed_tree.source_bytes)

    assert b"enum" in body_bytes, "Body bytes should contain enum keyword"
    assert b"Color" in body_bytes, "Body bytes should contain enum name"
    assert b"red" in body_bytes, "Body bytes should contain red value"
