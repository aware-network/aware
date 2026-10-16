"""Closed owner-neutral input plans; no source or execution authority."""

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.product_execution_input_plan import (
    ProductExecutionInputPlan,
    ProductExecutionInputSourceScope,
    ProductExecutionInputStep,
    _tree,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputJoinedProducerDeclaration,
    SemanticInputSourceContract,
)
from test_semantic_input_producer import _DECLARATION


def producer(_value):
    raise AssertionError("validation never executes a source producer")


def assembler(_value):
    raise AssertionError("validation never executes an assembler")


def plan():
    first = replace(_DECLARATION, producer_ref="prefix", result_role="prefix")
    final = SemanticInputJoinedProducerDeclaration(
        replace(_DECLARATION, producer_ref="final"),
        (SemanticInputSourceContract(first.result_role, first.result_contract),),
        ("prefix",),
    )
    scope = (ProductExecutionInputSourceScope("source"),)
    return ProductExecutionInputPlan(
        (
            ProductExecutionInputStep("prefix", first, producer, scope),
            ProductExecutionInputStep("final", final, producer, scope),
        ),
        (1, 0),
        assembler,
    )


def test_original_plan_closed_tree_and_declared_suffixes():
    value = plan()
    value.__post_init__()
    _tree(value).check(value)
    scope = ProductExecutionInputSourceScope("source", (".example",))
    scope.__post_init__()


@pytest.mark.parametrize("indices", [(True,), (-1,), (2,), (0, 0), ()])
def test_bad_result_indices_refuse(indices):
    with pytest.raises(ContractViolation):
        replace(plan(), input_result_indices=indices)


@pytest.mark.parametrize(
    "suffixes",
    [("*.example",), ("../example",), (".x", ".x"), (".z", ".a"), ("",), [".x"]],
)
def test_nonliteral_or_noncanonical_source_filters_refuse(suffixes):
    with pytest.raises(ContractViolation):
        ProductExecutionInputSourceScope("source", suffixes)


@pytest.mark.parametrize(
    "change", ["tuple", "declaration", "producer_code", "slot", "accessor"]
)
def test_retained_identity_and_behavior_poison_refuse_without_invocation(
    monkeypatch, change
):
    value = plan()
    tree = _tree(value)
    touched = []
    if change == "tuple":
        object.__setattr__(value, "steps", tuple(iter(value.steps)))
    elif change == "declaration":
        object.__setattr__(
            value.steps[0], "declaration", replace(value.steps[0].ordinary)
        )
    elif change == "producer_code":
        code = producer.__code__
        producer.__code__ = assembler.__code__
    elif change == "slot":

        class Poison:
            def __get__(self, *_args):
                touched.append(True)
                raise AssertionError("descriptor must not be invoked")

        monkeypatch.setattr(ProductExecutionInputPlan, "steps", Poison())
    else:

        def poison(self, name):
            touched.append(name)
            raise AssertionError("foreign accessor must not run")

        monkeypatch.setattr(ProductExecutionInputStep, "__getattribute__", poison)
    try:
        with pytest.raises(ContractViolation):
            tree.check(value)
        assert touched == []
    finally:
        if change == "producer_code":
            producer.__code__ = code


def test_wrong_join_prefix_refuses():
    value = plan()
    final = replace(value.steps[1].declaration, predecessor_stages=("foreign",))
    with pytest.raises(ContractViolation, match="prefix"):
        replace(
            value, steps=(value.steps[0], replace(value.steps[1], declaration=final))
        )


def test_protocol_like_plan_never_runs_foreign_behavior():
    class Foreign:
        def __getattribute__(self, _name):
            raise AssertionError("foreign plan must not be inspected")

    with pytest.raises(TypeError):
        _tree(Foreign())
