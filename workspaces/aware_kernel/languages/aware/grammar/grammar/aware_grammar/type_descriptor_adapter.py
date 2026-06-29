from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind, CollectionKind

from aware_grammar.primitive_codec import AwarePrimitiveCodec, OPTIONAL_LIST_TYPE_ERROR_PREFIX
from aware_grammar.type_parser import AwareTypeParser
from typing import final
from typing_extensions import override


@final
class AwareTypeDescriptorAdapter(CodeTypeDescriptorAdapter):
    """Parse Aware type annotations into a language‑agnostic TypeNode tree.

    Grammar conventions:
    - Optional: Type? -> UNION[Type, null]
    - Collections: Type[] -> COLLECTION(list, element=Type)
    - Parametric primitives: Vector(1536)
    - Qualified idents: schema.Type (kept as IDENT text; resolution happens later)
    - Field modifiers: trailing tokens like `@EdgeName`, `many`, `unique` are ignored here
      (they are handled by attribute/field adapters and relationship builders).
    """

    def __init__(
        self,
        parser: AwareTypeParser | None = None,
        primitive_codec: AwarePrimitiveCodec | None = None,
    ):
        self._parser = parser or AwareTypeParser()
        self._primitive_codec = primitive_codec or AwarePrimitiveCodec(parser=self._parser)

    @override
    def parse_type(self, type_text: str | None) -> TypeNode:
        s = (type_text or "").strip()
        if not s:
            return TypeNode(kind=TypeNodeKind.IDENT, text="Any")

        parser = self._parser
        primitive_codec = self._primitive_codec

        # Aware field declarations can include trailing modifiers (e.g. `Type[] @Edge many`).
        s = parser.strip_trailing_field_modifiers(s)

        # Optional suffix: Type?  (normalize to Union[Type, null])
        opt_inner = parser.get_optional_suffix_inner(s)
        if opt_inner is not None:
            if parser.get_array_suffix_inner(opt_inner) is not None:
                raise ValueError(f"{OPTIONAL_LIST_TYPE_ERROR_PREFIX}: {s}")
            return TypeNode(
                kind=TypeNodeKind.UNION,
                members=[self.parse_type(opt_inner), TypeNode(kind=TypeNodeKind.PRIMITIVE, text="Null")],
            )

        # Tuple return: (TypeA, TypeB, ...) with optional labels `name: Type`
        tuple_entries = parser.get_tuple_entries(s)
        if tuple_entries is not None:
            elements: list[TypeNode] = []
            for entry in tuple_entries:
                node = self.parse_type(entry.type_text)
                if entry.label:
                    node.label = entry.label
                elements.append(node)
            return TypeNode(kind=TypeNodeKind.TUPLE, elements=elements)

        # Collection suffix: Type[]
        arr_inner = parser.get_array_suffix_inner(s)
        if arr_inner is not None:
            return TypeNode(
                kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.LIST, element=self.parse_type(arr_inner)
            )

        # Mapping: Dict[K, V]
        kv = parser.get_dict_kv(s)
        if kv is not None:
            key_text, value_text = kv
            return TypeNode(kind=TypeNodeKind.MAPPING, key=self.parse_type(key_text), value=self.parse_type(value_text))

        # Leaf: delegate to AwarePrimitiveCodec for primitive recognition (SSOT)
        prim = primitive_codec.parse(s)
        if prim is not None:
            # Normalize to language label via to_string()
            label = primitive_codec.render(prim)
            return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=label)

        # Qualified ident or bare ident (enum/class); resolution occurs later
        return TypeNode(kind=TypeNodeKind.IDENT, text=parser.strip_edge_annotation(s))
