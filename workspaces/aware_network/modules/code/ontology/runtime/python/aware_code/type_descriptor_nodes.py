from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TypeNodeKind(str, Enum):
    PRIMITIVE = "primitive"
    IDENT = "ident"
    COLLECTION = "collection"
    MAPPING = "mapping"
    TUPLE = "tuple"
    UNION = "union"


class CollectionKind(str, Enum):
    LIST = "list"
    SET = "set"


@dataclass
class TypeNode:
    """
    Language-agnostic type node produced by a CodeTypeDescriptorAdapter.

    - PRIMITIVE: text holds normalized primitive label (language-specific mapping).
    - IDENT: text holds identifier (class/enum/alias name). Flags indicate Self/forward-ref if detected.
    - COLLECTION: collection_kind + element
    - MAPPING: key + value
    - TUPLE: elements
    - UNION: members (normalized Optional[T] as Union[T, None])
    """

    kind: TypeNodeKind
    text: str | None = None
    is_self: bool = False
    is_forward_ref: bool = False

    # Structural
    collection_kind: CollectionKind | None = None
    element: TypeNode | None = None
    key: TypeNode | None = None
    value: TypeNode | None = None
    elements: list[TypeNode] = field(default_factory=list)
    members: list[TypeNode] = field(default_factory=list)
    label: str | None = None
