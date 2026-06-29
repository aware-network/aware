"""Test suite for Dart language adapters (end-to-end)."""

from pathlib import Path
import pytest

# Core
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter
from aware_code.tree.tree import CodeTree
from aware_code.node.node import CodeNode

# Tree-sitter
from tree_sitter import Parser

# Dart Grammar
from dart_grammar.adapters.class_adapter import DartClassAdapter
from dart_grammar.adapters.attribute_adapter import DartAttributeAdapter
from dart_grammar.adapters.function_adapter import DartFunctionAdapter
from dart_grammar.adapters.enum_adapter import DartEnumAdapter
from dart_grammar.adapters.enum_value_adapter import DartEnumValueAdapter
from dart_grammar.adapters.comment_adapter import DartCommentAdapter
from dart_grammar.adapters.decorator_adapter import DartDecoratorAdapter
from dart_grammar.adapters.import_adapter import DartImportAdapter


from tree_sitter_dart.tree_sitter_language import DART_LANGUAGE


# Set up language and parser
parser = Parser(language=DART_LANGUAGE)


def _text_from_node(node_or_codenode) -> str:
    node = getattr(node_or_codenode, "node", node_or_codenode)
    b = getattr(node, "text", None)
    return b.decode("utf-8") if b is not None else ""


@pytest.fixture(scope="session")
def sample_file():
    """Fixture that returns the path to the sample Dart file."""
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    sample_file = samples_dir / "user_post.dart"
    if not sample_file.exists():
        pytest.fail(f"Sample file not found: {sample_file}")
    return sample_file


@pytest.fixture(scope="session")
def parsed_tree(sample_file: Path) -> CodeTree:
    with open(sample_file, "rb") as f:
        source_bytes = f.read()
    tree = parser.parse(source_bytes)
    root_node = CodeNode(node=tree.root_node, byte_start=tree.root_node.start_byte, byte_end=tree.root_node.end_byte)
    return CodeTree(root=root_node, source_bytes=source_bytes)


def test_tree_adapter(sample_file: Path):
    adapter = CodeTreeSitterAdapter(language=DART_LANGUAGE)
    code_tree = adapter.parse(sample_file)
    assert code_tree is not None
    assert code_tree.root is not None
    assert len(code_tree.source_bytes) > 0


def test_class_adapter(parsed_tree: CodeTree):
    adapter = DartClassAdapter()
    class_nodes = list(adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    names = [_text_from_node(adapter.get_name(n)) for n in class_nodes]
    assert set(["User", "Post", "Comment", "Image"]).issubset(set(names))

    # Test attributes for User
    user_node = next(n for n in class_nodes if _text_from_node(adapter.get_name(n)) == "User")
    attrs = list(adapter.get_attributes(user_node))
    assert len(attrs) >= 3

    # Methods
    methods = list(adapter.get_methods(user_node))
    assert len(methods) >= 2
    assert adapter.qualname(user_node) == "User"


def test_attribute_adapter(parsed_tree: CodeTree):
    class_adapter = DartClassAdapter()
    attr_adapter = DartAttributeAdapter()
    user_node = next(
        node
        for node in class_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes)
        if _text_from_node(class_adapter.get_name(node)) == "User"
    )
    attributes = list(class_adapter.get_attributes(user_node))
    assert any(_text_from_node(attr_adapter.get_name(a, is_parameter=False)) == "id" for a in attributes)


def test_function_adapter(parsed_tree: CodeTree):
    fn_adapter = DartFunctionAdapter()
    fns = list(fn_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    names = [_text_from_node(fn_adapter.get_name(fn)) for fn in fns]
    assert "validateEmail" in names
    assert "sendNotification" in names


def test_decorator_adapter(parsed_tree: CodeTree):
    dec_adapter = DartDecoratorAdapter()
    nodes = list(dec_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(nodes) >= 1
    names = [_text_from_node(dec_adapter.get_name(n)) for n in nodes]
    assert any(n in names for n in ["JsonSerializable"]) or any("json" in n for n in names)


def test_enum_adapter(parsed_tree: CodeTree):
    enum_adapter = DartEnumAdapter()
    enums = list(enum_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(enums) >= 1
    status = next(e for e in enums if _text_from_node(enum_adapter.get_name(e)) == "Status")
    values = [_text_from_node(v) for v in enum_adapter.get_values(status)]
    assert set(["active", "inactive", "pending"]).issubset(set(values))


def test_enum_value_adapter(parsed_tree: CodeTree):
    enum_adapter = DartEnumAdapter()
    enum_value_adapter = DartEnumValueAdapter()

    enums = list(enum_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    status = next(e for e in enums if _text_from_node(enum_adapter.get_name(e)) == "Status")

    value_nodes = list(enum_value_adapter.match_nodes(status.node, parsed_tree.source_bytes))
    names = [_text_from_node(enum_value_adapter.get_name(v)) for v in value_nodes]
    assert names == ["active", "inactive", "pending"]


def test_comment_adapter(parsed_tree: CodeTree):
    comment_adapter = DartCommentAdapter()
    comment_nodes = list(comment_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(comment_nodes) > 0


def test_import_adapter(parsed_tree: CodeTree):
    import_adapter = DartImportAdapter()
    import_nodes = list(import_adapter.match_nodes(parsed_tree.root.node, parsed_tree.source_bytes))
    assert len(import_nodes) >= 3  # import + part directives
