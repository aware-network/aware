from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind, CollectionKind
from typing_extensions import override

from dart_grammar.type_parser import DartTypeParser
from dart_grammar.primitive_codec import DartPrimitiveCodec


class DartTypeDescriptorAdapter(CodeTypeDescriptorAdapter):
    """Parse Dart type annotations into a language-agnostic TypeNode tree.

    Handles:
    - Nullable types: T? -> Union[T, Null]
    - Collections: List<T>, Set<T>
    - Mapping: Map<K, V>
    - Primitives via DartPrimitiveType
    - Idents (classes/enums) as IDENT leaves
    """

    def __init__(
        self,
        parser: DartTypeParser | None = None,
        primitive_codec: DartPrimitiveCodec | None = None,
    ) -> None:
        self._parser: DartTypeParser = parser or DartTypeParser()
        self._primitive_codec: DartPrimitiveCodec = primitive_codec or DartPrimitiveCodec(parser=self._parser)

    @override
    def parse_type(self, type_text: str | None) -> TypeNode:
        s = (type_text or "").strip()
        if not s:
            return TypeNode(kind=TypeNodeKind.IDENT, text="dynamic")

        parser = self._parser
        primitive_codec = self._primitive_codec

        # Nullable: T? -> Union[T, null]
        opt_inner = parser.get_optional_inner(s)
        if opt_inner is not None:
            return TypeNode(kind=TypeNodeKind.UNION, members=[self.parse_type(opt_inner), self.parse_type("null")])

        # Map<K, V>
        kv = parser.get_dict_kv(s)
        if kv is not None:
            k_s, v_s = kv
            return TypeNode(kind=TypeNodeKind.MAPPING, key=self.parse_type(k_s), value=self.parse_type(v_s))

        # List<T>
        list_inner = parser.get_list_inner(s)
        if list_inner is not None:
            return TypeNode(
                kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.LIST, element=self.parse_type(list_inner)
            )

        # Set<T>
        set_inner = parser.get_set_inner(s)
        if set_inner is not None:
            return TypeNode(
                kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.SET, element=self.parse_type(set_inner)
            )

        # Primitive
        prim = primitive_codec.parse(s)
        if prim is not None:
            label = primitive_codec.render(prim) or s
            return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=label)

        # IDENT (class/enum/alias)
        return TypeNode(kind=TypeNodeKind.IDENT, text=s)
