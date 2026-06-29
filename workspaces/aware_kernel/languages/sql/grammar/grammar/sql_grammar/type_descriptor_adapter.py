from __future__ import annotations

from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind, CollectionKind
from typing_extensions import override

from sql_grammar.primitive_codec import SqlPrimitiveCodec
from sql_grammar.type_parser import SqlTypeParser


class SqlTypeDescriptorAdapter(CodeTypeDescriptorAdapter):
    """Parse SQL type annotations into a language‑agnostic TypeNode tree.

    Conventions:
    - Arrays: type[] → COLLECTION(LIST, element=type)
    - Vector: VECTOR(n) → PRIMITIVE text "vector(n)" (mapper adds constraints)
    - User‑defined enum types: schema.type or type → IDENT (resolution to ENUM by name happens in factory)
    - Keywords map to PRIMITIVE via plugin primitive mapper later
    """

    def __init__(
        self,
        parser: SqlTypeParser | None = None,
        primitive_codec: SqlPrimitiveCodec | None = None,
    ):
        self._parser = parser or SqlTypeParser()
        self._primitive_codec = primitive_codec or SqlPrimitiveCodec(parser=self._parser)

    _parser: SqlTypeParser
    _primitive_codec: SqlPrimitiveCodec

    @override
    def parse_type(self, type_text: str | None) -> TypeNode:
        s = (type_text or "").strip()
        if not s:
            return TypeNode(kind=TypeNodeKind.IDENT, text="text")  # default to text

        parser = self._parser
        primitive_codec = self._primitive_codec

        # Arrays
        inner = parser.get_array_inner(s)
        if inner is not None:
            return TypeNode(
                kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.LIST, element=self.parse_type(inner)
            )

        # Qualified user-defined type name → IDENT (enum/domain types)
        if parser.is_qualified_ident(s):
            return TypeNode(kind=TypeNodeKind.IDENT, text=s)

        # Primitive (SSOT via codec)
        prim = primitive_codec.parse(s)
        if prim is not None:
            label = primitive_codec.render(prim) or s
            return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=label)

        # Schema-qualified or unknown identifiers → IDENT (enum/domain types)
        return TypeNode(kind=TypeNodeKind.IDENT, text=s)
