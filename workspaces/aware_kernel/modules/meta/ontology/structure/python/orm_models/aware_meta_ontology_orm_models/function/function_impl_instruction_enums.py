from __future__ import annotations

# Standard
from enum import Enum


class FunctionImplDeleteTargetKind(Enum):
    """Canonical delete target semantics for FunctionImpl lifecycle instructions."""

    self = "self"


class FunctionImplInstructionType(Enum):
    """Polymorphic instruction shape for function implementation lowering."""

    let = "let"
    invoke = "invoke"
    construct = "construct"
    set = "set"
    require = "require"
    delete = "delete"


class FunctionImplInvokeKind(Enum):
    """Canonical invoke semantics for function impl instruction payloads."""

    call = "call"
    construct = "construct"


class FunctionImplRequireCompareOperator(Enum):
    """Canonical comparator semantics for `compare`/`cardinality` require kinds."""

    eq = "eq"
    neq = "neq"
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"


class FunctionImplRequireKind(Enum):
    """Canonical predicate semantics for `FunctionImplInstructionRequire`."""

    exists = "exists"
    equals = "equals"
    member = "member"
    unique = "unique"
    compare = "compare"
    cardinality = "cardinality"
    all_or_none = "all_or_none"
    text_matches_regex = "text_matches_regex"


class FunctionImplValueSourceKind(Enum):
    """Canonical assignment-source semantics for function mutation instructions."""

    literal = "literal"
    function_input_ref = "function_input_ref"
    let_ref = "let_ref"
    transform = "transform"
    read_path = "read_path"


class FunctionImplValueSourceReadPathRootKind(Enum):
    """Canonical root semantics for read-only FunctionImpl value-source traversal."""

    function_input = "function_input"
    let_binding = "let_binding"
    target_attribute = "target_attribute"


class FunctionImplValueTransformKind(Enum):
    """
    Canonical pure transforms for `FunctionImplValueSource`.
    These are expression/value-source semantics, not standalone instructions.
    """

    text_strip = "text_strip"
    text_casefold = "text_casefold"
    text_lower = "text_lower"
    text_default_if_blank = "text_default_if_blank"
    text_slice = "text_slice"
    text_concat = "text_concat"
