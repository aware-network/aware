"""Portable shape and signature proofs only; no nominal or lock qualification."""

import inspect
import pickle
from dataclasses import FrozenInstanceError, replace

import pytest
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    DependencyScopeLockedValidator,
    DependencyScopeValidator,
    RetainedDependencyScopeExpectation,
)


def expectation(**changes):
    values = {
        "parent_identity": object(), "epoch_identity": object(), "operation_identity": object(),
        "process_id": 123, "repository_membership_identity": object(),
        "closure_runtime_identity": object(), "consumer_scope_key": "workspaces/a/aware.workspace.toml",
    }
    return RetainedDependencyScopeExpectation(**(values | changes))


def test_comparison_context_preserves_original_references_without_admission():
    value = expectation()
    duplicate = replace(value)
    assert duplicate is not value and duplicate != value
    for name in (
        "parent_identity", "epoch_identity", "operation_identity",
        "repository_membership_identity", "closure_runtime_identity",
    ):
        assert getattr(duplicate, name) is getattr(value, name)
    with pytest.raises(FrozenInstanceError):
        value.process_id = 456


@pytest.mark.parametrize("pid", [True, False, 1.0, "123", None])
def test_process_requires_exact_integer(pid):
    with pytest.raises(ContractViolation):
        expectation(process_id=pid)


@pytest.mark.parametrize("key", ["", "/absolute", "../foreign", "a//b", "a\\b"])
def test_scope_key_uses_existing_canonical_path_contract(key):
    with pytest.raises(ContractViolation):
        expectation(consumer_scope_key=key)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_no_pickle_transport_for_context(protocol):
    with pytest.raises(TypeError, match="not serializable"):
        pickle.dumps(expectation(), protocol=protocol)


def test_full_and_locked_checks_have_distinct_explicit_signatures():
    full = inspect.signature(DependencyScopeValidator.validate_dependency_scope_closure)
    locked = inspect.signature(DependencyScopeLockedValidator.check_dependency_scope_closure_locked)
    assert list(full.parameters) == ["self", "closure", "expected", "closure_digest"]
    assert list(locked.parameters) == ["self", "closure", "expected", "closure_digest", "guard"]
    assert full.parameters["closure_digest"].default is None
    assert locked.parameters["closure_digest"].default is inspect.Parameter.empty
    for signature in (full, locked):
        for name in list(signature.parameters)[2:]:
            assert signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    for protocol in (DependencyScopeValidator, DependencyScopeLockedValidator):
        with pytest.raises(TypeError):
            protocol()
