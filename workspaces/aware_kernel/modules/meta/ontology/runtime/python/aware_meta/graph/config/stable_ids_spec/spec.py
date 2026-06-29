from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


NamespaceKind: TypeAlias = Literal["ns_url", "uuid"]
ParamType: TypeAlias = Literal["uuid", "str", "bytes", "bool", "int", "float", "str_list"]
LetOp: TypeAlias = Literal[
    "hex",
    "normalize",
    "normalize_default",
    "prefix_if_set",
    "sorted_pair",
    "bool_int",
    "uuid_str_default",
    "int_str_default",
    "list_join",
]
ParsedDefaultPrimitive: TypeAlias = str | bool | int | float | None


@dataclass(frozen=True, slots=True)
class NamespaceSpec:
    name: str
    kind: NamespaceKind
    value: str


@dataclass(frozen=True, slots=True)
class ParamSpec:
    name: str
    type: ParamType
    optional: bool = False
    default: ParsedDefaultPrimitive = None
    non_empty: bool = False
    normalize: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LetSpec:
    # NOTE: some ops assign multiple names (e.g. sorted_pair).
    op: LetOp
    name: str | None = None
    names: tuple[str, ...] = ()
    param: str | None = None
    params: tuple[str, ...] = ()
    normalize: tuple[str, ...] = ()
    default: str | None = None
    prefix: str | None = None
    sep: str | None = None
    unique: bool = False
    sort: bool = False


@dataclass(frozen=True, slots=True)
class FunctionSpec:
    name: str
    namespace: str
    template: str
    params: tuple[ParamSpec, ...] = ()
    lets: tuple[LetSpec, ...] = ()
    doc: str | None = None
    dart_name: str | None = None


@dataclass(frozen=True, slots=True)
class StableIdsSpec:
    version: int
    namespaces: tuple[NamespaceSpec, ...] = ()
    functions: tuple[FunctionSpec, ...] = ()

    @property
    def namespaces_by_name(self) -> dict[str, NamespaceSpec]:
        return {n.name: n for n in self.namespaces}


__all__ = [
    "FunctionSpec",
    "LetOp",
    "LetSpec",
    "NamespaceKind",
    "NamespaceSpec",
    "ParamSpec",
    "ParamType",
    "ParsedDefaultPrimitive",
    "StableIdsSpec",
]
