from __future__ import annotations

from typing_extensions import override

from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind, CollectionKind

# Raw token parser (SSOT for Python type text syntax)
from python_grammar.type_parser import PythonTypeParser

# Primitive codec (builds CodePrimitiveType when node is PRIMITIVE)
from python_grammar.primitive_codec import PythonPrimitiveCodec


class PythonTypeDescriptorAdapter(CodeTypeDescriptorAdapter):
    """Parse Python type annotations into a language-agnostic TypeNode tree.

    Normalizations:
    - Optional[T] -> Union[T, None]
    - Preserve Self as IDENT with is_self=True
    - Strip surrounding quotes for forward refs but set is_forward_ref=True
    """

    def __init__(
        self,
        parser: PythonTypeParser | None = None,
        primitive_codec: PythonPrimitiveCodec | None = None,
    ):
        self._parser: PythonTypeParser = parser or PythonTypeParser()
        self._primitive_codec: PythonPrimitiveCodec = primitive_codec or PythonPrimitiveCodec(parser=self._parser)

    @override
    def parse_type(self, type_text: str | None) -> TypeNode:
        s = (type_text or "").strip()
        if not s:
            # Unknown, treat as IDENT Any
            return TypeNode(kind=TypeNodeKind.IDENT, text="Any")

        parser = self._parser
        primitive_codec = self._primitive_codec

        # Optional[T] -> Union[T, None] (normalized at the node layer)
        opt_inner = parser.get_optional_inner(s)
        if opt_inner is not None:
            return TypeNode(
                kind=TypeNodeKind.UNION,
                members=[self.parse_type(opt_inner), self.parse_type("None")],
            )

        # Annotated[T, ...] – peel wrapper; special-case Annotated[Vector, VectorDim(n)] → PRIMITIVE Vector(dim)
        annotated = parser.get_annotated_parts(s)
        if annotated is not None:
            base, metas = annotated
            # Recognize Vector with VectorDim(n)
            if base.endswith("Vector") or base == "Vector":
                dim = parser.get_vector_dim_meta(metas)
                if dim is not None:
                    return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=f"Vector({dim})")
                return TypeNode(kind=TypeNodeKind.PRIMITIVE, text="Vector")
            return self.parse_type(base)

        # Literal[...]: encode as PRIMITIVE so primitive parser can attach constraints.one_of
        if parser.get_literal_inner(s) is not None:
            return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=s)

        # Tuple
        tuple_parts = parser.get_tuple_elements(s)
        if tuple_parts is not None:
            tuple_nodes: list[TypeNode] = [self.parse_type(p) for p in tuple_parts]
            return TypeNode(kind=TypeNodeKind.TUPLE, elements=tuple_nodes)

        # Union
        union_members = parser.get_union_members(s)
        if union_members is not None:
            union_nodes: list[TypeNode] = [self.parse_type(m) for m in union_members]
            return TypeNode(kind=TypeNodeKind.UNION, members=union_nodes)

        # Mapping (dict)
        kv = parser.get_dict_kv(s)
        if kv is not None:
            key_s, val_s = kv
            key = self.parse_type(key_s)
            val = self.parse_type(val_s)
            return TypeNode(kind=TypeNodeKind.MAPPING, key=key, value=val)

        # Collections (list/set)
        set_inner = parser.get_set_inner(s)
        if set_inner is not None:
            elem = self.parse_type(set_inner)
            return TypeNode(kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.SET, element=elem)

        list_inner = parser.get_list_inner(s)
        if list_inner is not None:
            elem = self.parse_type(list_inner)
            return TypeNode(kind=TypeNodeKind.COLLECTION, collection_kind=CollectionKind.LIST, element=elem)

        # Primitive
        prim = primitive_codec.parse(s)
        if prim is not None:
            # Use to_string to produce normalized primitive label (e.g., "int", "list[int]")
            label = primitive_codec.render(prim)
            return TypeNode(kind=TypeNodeKind.PRIMITIVE, text=label)

        # IDENT (class/enum/alias)
        s, is_forward_ref = parser.strip_forward_ref_quotes(s)
        is_self = s == "Self"
        return TypeNode(kind=TypeNodeKind.IDENT, text=s, is_self=is_self, is_forward_ref=is_forward_ref)
