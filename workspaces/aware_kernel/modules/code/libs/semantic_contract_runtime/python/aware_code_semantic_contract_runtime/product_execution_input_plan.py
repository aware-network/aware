"""Factory-owned source-input recipes. Values declare work, never admit it.

This bounded first recipe uses ordinary source producers and an optional final
joined producer. Dependency-backed inputs keep their existing separate rail.
Code treats stage, role, contract and path-suffix values as owner declarations.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from types import FunctionType
from typing import Any, cast

from .contracts import ContractViolation, SemanticPackageCoordinate
from .runtime import SemanticBody
from .semantic_input_producer import (
    SemanticInputJoinedProducerDeclaration,
    SemanticInputProducerDeclaration,
    _result_tree,
    _token,
)

MAX_PRODUCT_INPUT_STEPS = 16


@dataclass(frozen=True, slots=True)
class ProductExecutionInputSourceScope:
    role: str
    # Empty selects all original candidates. Literal suffixes are case-sensitive.
    suffixes: tuple[str, ...] = ()

    def __post_init__(self):
        _token(self.role, "source scope role")
        if type(self.suffixes) is not tuple or len(self.suffixes) > 16:
            raise ContractViolation("exact bounded source suffix tuple required")
        for suffix in self.suffixes:
            if (
                type(suffix) is not str
                or not 1 <= len(suffix) <= 128
                or any(char.isspace() or char in "/\\*?\x00" for char in suffix)
            ):
                raise ContractViolation("literal bounded source suffix required")
        if self.suffixes != tuple(sorted(set(self.suffixes))):
            raise ContractViolation("source suffixes must be unique and ordered")


@dataclass(frozen=True, slots=True)
class ProductExecutionInputStep:
    stage: str
    declaration: (
        SemanticInputProducerDeclaration | SemanticInputJoinedProducerDeclaration
    )
    producer: Callable[..., Any]
    source_scopes: tuple[ProductExecutionInputSourceScope, ...]

    @property
    def ordinary(self) -> SemanticInputProducerDeclaration:
        if type(self.declaration) is SemanticInputJoinedProducerDeclaration:
            return self.declaration.ordinary
        return cast(SemanticInputProducerDeclaration, self.declaration)

    def __post_init__(self):
        _token(self.stage, "input step stage")
        if type(self.declaration) not in (
            SemanticInputProducerDeclaration,
            SemanticInputJoinedProducerDeclaration,
        ):
            raise TypeError("exact original input declaration required")
        _result_tree(self.declaration).check(self.declaration)
        self.declaration.__post_init__()
        if type(self.producer) is not FunctionType:
            raise TypeError("exact original input producer function required")
        if (
            type(self.source_scopes) is not tuple
            or not 1 <= len(self.source_scopes) <= 16
        ):
            raise ContractViolation("exact bounded source-scope tuple required")
        for scope in self.source_scopes:
            if type(scope) is not ProductExecutionInputSourceScope:
                raise TypeError("exact source scope required")
            scope.__post_init__()
        if tuple(scope.role for scope in self.source_scopes) != tuple(
            contract.role for contract in self.ordinary.source_contracts
        ):
            raise ContractViolation(
                "source scopes must cover declaration roles in order"
            )


@dataclass(frozen=True, slots=True)
class ProductExecutionInputPlan:
    steps: tuple[ProductExecutionInputStep, ...]
    input_result_indices: tuple[int, ...]
    assembler: Callable[..., object]

    def __post_init__(self):
        if (
            type(self.steps) is not tuple
            or not 1 <= len(self.steps) <= MAX_PRODUCT_INPUT_STEPS
        ):
            raise ContractViolation("exact bounded execution-input steps required")
        for index, step in enumerate(self.steps):
            if type(step) is not ProductExecutionInputStep:
                raise TypeError("exact input step required")
            step.__post_init__()
            if type(step.declaration) is SemanticInputJoinedProducerDeclaration:
                if not index or index != len(self.steps) - 1:
                    raise ContractViolation(
                        "only one final joined producer is supported"
                    )
                declared = step.declaration
                previous = self.steps[:index]
                stages = declared.predecessor_stages or tuple(
                    x.role for x in declared.predecessor_contracts
                )
                if (
                    tuple(
                        (x.ordinary.result_role, x.ordinary.result_contract)
                        for x in previous
                    )
                    != tuple(
                        (x.role, x.contract) for x in declared.predecessor_contracts
                    )
                    or tuple(x.stage for x in previous) != stages
                ):
                    raise ContractViolation(
                        "joined input must bind the complete ordered prefix"
                    )
        refs = tuple(step.ordinary.producer_ref for step in self.steps)
        if len(set(refs)) != len(refs):
            raise ContractViolation("input producers must have unique references")
        if (
            type(self.input_result_indices) is not tuple
            or not self.input_result_indices
        ):
            raise ContractViolation("exact nonempty result-index tuple required")
        if any(
            type(i) is not int or not 0 <= i < len(self.steps)
            for i in self.input_result_indices
        ):
            raise ContractViolation("execution input result index is invalid")
        if len(set(self.input_result_indices)) != len(self.input_result_indices):
            raise ContractViolation("execution input results cannot be duplicated")
        if type(self.assembler) is not FunctionType:
            raise TypeError("exact original input assembler function required")


@dataclass(frozen=True, slots=True)
class ProductExecutionInputAssemblyInput:
    package: SemanticPackageCoordinate
    invocation_ref: str
    idempotency_key: str
    input_bodies: tuple[SemanticBody, ...]
    predecessor_body: SemanticBody | None = None

    def __post_init__(self):
        _result_tree((self.package, self.input_bodies, self.predecessor_body))
        self.package.__post_init__()
        _token(self.invocation_ref, "invocation ref")
        _token(self.idempotency_key, "idempotency key")
        if type(self.input_bodies) is not tuple or not self.input_bodies:
            raise ContractViolation("exact original input bodies required")
        for body in self.input_bodies:
            if type(body) is not SemanticBody:
                raise TypeError("exact original input body required")
            body.__post_init__()
        if self.predecessor_body is not None:
            if type(self.predecessor_body) is not SemanticBody:
                raise TypeError("exact prior body required")
            self.predecessor_body.__post_init__()


# Closed strong traversal: never call equality or an injected descriptor on a
# model, tuple, callable or declaration. Shared declarations use Code's tree.
_FIELDS = {
    ProductExecutionInputSourceScope: ("role", "suffixes"),
    ProductExecutionInputStep: ("stage", "declaration", "producer", "source_scopes"),
    ProductExecutionInputPlan: ("steps", "input_result_indices", "assembler"),
}
_SLOTS = {
    cls: tuple(inspect.getattr_static(cls, name) for name in fields)
    for cls, fields in _FIELDS.items()
}
_POST_INIT = {
    cls: (inspect.getattr_static(cls, "__post_init__"), cls.__post_init__.__code__)
    for cls in _FIELDS
}
_ORDINARY = inspect.getattr_static(ProductExecutionInputStep, "ordinary")


def _check_model(kind):
    function, code = _POST_INIT[kind]
    if (
        inspect.getattr_static(kind, "__getattribute__") is not object.__getattribute__
        or inspect.getattr_static(kind, "__post_init__") is not function
        or object.__getattribute__(function, "__code__") is not code
        or (
            kind is ProductExecutionInputStep
            and inspect.getattr_static(kind, "ordinary") is not _ORDINARY
        )
    ):
        raise ContractViolation("original execution input model behavior changed")


@dataclass(frozen=True, slots=True)
class _Tree:
    original: object
    kind: type
    children: tuple = ()
    shared: Any = None
    code: object = None

    def check(self, current):
        pending = [(self, current)]
        while pending:
            tree, node = pending.pop()
            kind = tree.kind
            if type(node) is not kind:
                raise ContractViolation("execution input plan node type changed")
            if kind is str or kind is int:
                if node != tree.original:
                    raise ContractViolation("execution input plan scalar changed")
                continue
            if node is not tree.original:
                raise ContractViolation(
                    "original execution input plan identity changed"
                )
            if kind is FunctionType:
                if object.__getattribute__(node, "__code__") is not tree.code:
                    raise ContractViolation(
                        "original execution input function code changed"
                    )
            elif tree.shared is not None:
                tree.shared.check(node)
            elif kind is tuple:
                if len(node) != len(tree.children):
                    raise ContractViolation("execution input tuple changed")
                pending.extend(zip(tree.children, node, strict=True))
            else:
                _check_model(kind)
                for name, slot, child in zip(
                    _FIELDS[kind], _SLOTS[kind], tree.children, strict=True
                ):
                    if inspect.getattr_static(kind, name) is not slot:
                        raise ContractViolation(
                            "original execution input descriptor changed"
                        )
                    pending.append((child, slot.__get__(node)))


def _tree(value):
    kind = type(value)
    if kind is str or kind is int:
        return _Tree(value, kind)
    if kind is FunctionType:
        return _Tree(value, kind, code=object.__getattribute__(value, "__code__"))
    if (
        kind is SemanticInputProducerDeclaration
        or kind is SemanticInputJoinedProducerDeclaration
    ):
        return _Tree(value, kind, shared=_result_tree(value))
    if kind is tuple:
        return _Tree(value, kind, tuple(_tree(child) for child in value))
    if not any(kind is cls for cls in _FIELDS):
        raise TypeError("exact closed execution-input plan value required")
    _check_model(kind)
    values = []
    for name, slot in zip(_FIELDS[kind], _SLOTS[kind], strict=True):
        if inspect.getattr_static(kind, name) is not slot:
            raise ContractViolation("original execution input descriptor changed")
        values.append(_tree(slot.__get__(value)))
    return _Tree(value, kind, tuple(values))
