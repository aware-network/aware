"""Aware implementation of the CodeSectionAnnotationAdapter."""

from collections.abc import Iterable
from typing_extensions import override
from typing import final

from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode
from aware_code.section.annotation.adapter import CodeSectionAnnotationAdapter


@final
class AwareAnnotationAdapter(CodeSectionAnnotationAdapter[Node]):
    """Extract `ann` statements from Aware sources."""

    ANN_QUERY = AWARE_LANGUAGE.query(
        """
        (ann_def) @ann
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.ANN_QUERY.captures(root)
        for n in sorted(captures.get("ann", []), key=lambda node: (node.start_byte, node.end_byte)):
            line_end = source.find(b"\n", n.start_byte)
            if line_end < 0:
                line_end = len(source)
            code_node = CodeNode(node=n, byte_start=n.start_byte, byte_end=line_end)
            setattr(code_node, "raw_text", source[n.start_byte:line_end])
            yield code_node

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.annotation

    def _node_text(self, node: Node) -> str:
        if not node.text:
            return ""
        return node.text.decode("utf-8")

    def _raw_text(self, node: CodeNode[Node]) -> str:
        raw = getattr(node, "raw_text", None)
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        if isinstance(raw, str):
            return raw
        return self._node_text(node.node)

    def _tokenize(self, text: str) -> list[str]:
        tokens: list[str] = []
        buf: list[str] = []
        quote: str | None = None
        i = 0
        while i < len(text):
            c = text[i]
            if quote is None and c == "/" and i + 1 < len(text) and text[i + 1] == "/":
                break
            if quote is None and c.isspace():
                if buf:
                    tokens.append("".join(buf))
                    buf = []
                i += 1
                continue
            if quote is None and c in {"'", '"'}:
                quote = c
                i += 1
                continue
            if quote is not None and c == quote:
                quote = None
                i += 1
                continue
            buf.append(c)
            i += 1
        if buf:
            tokens.append("".join(buf))
        return tokens

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        # Use the raw annotation text as a stable qualname.
        text = self._raw_text(node).strip()
        return f"ann:{text}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """Return the raw bytes spanned by the annotation node."""
        raw = getattr(node, "raw_text", None)
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, str):
            return raw.encode("utf-8")
        return source[node.byte_start:node.byte_end]

    @override
    def get_path(self, node: CodeNode[Node]) -> str:
        tokens = self._tokenize(self._raw_text(node).strip())
        if len(tokens) < 2 or tokens[0] != "ann":
            return ""
        return tokens[1]

    @override
    def get_verb(self, node: CodeNode[Node]) -> str:
        tokens = self._tokenize(self._raw_text(node).strip())
        if len(tokens) < 3 or tokens[0] != "ann":
            return ""
        return tokens[2]

    @override
    def get_args(self, node: CodeNode[Node]) -> list[str]:
        # NOTE: Tree-sitter grammar tokenization for `ann` args is intentionally conservative
        # (identifiers/strings). For protocol-level annotations we need to allow dotted / member
        # paths (e.g. `pkg.schema.Name::attr`) to appear as arguments without forcing quotes.
        #
        # Therefore, parse args from the raw annotation text via a tiny tokenizer that respects
        # quotes and stops at line comments.
        raw = self._raw_text(node).strip()
        if not raw:
            return []
        tokens = self._tokenize(raw)
        if len(tokens) < 3 or tokens[0] != "ann":
            return []
        return [t for t in tokens[3:] if t]
