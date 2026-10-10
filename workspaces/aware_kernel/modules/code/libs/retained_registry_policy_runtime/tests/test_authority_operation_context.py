"""Bounded negative entrances; real lineage proof is the owner/Workspace canary."""

import copy
import gc
import os
from contextlib import contextmanager, nullcontext
from types import SimpleNamespace

import pytest
from aware_code_retained_registry_policy_runtime import (
    authority_operation_context as authority,
)
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from test_operation_context import setup
from test_stage_context_derivation import paired  # noqa: F401


def test_source_only_host_cannot_issue_authority_context():
    _, host, _, _, _, request = setup()
    try:
        with pytest.raises(
            ContractViolation, match="authority stage retention required"
        ):
            authority.begin_authority_operation(host, request)
        with pytest.raises(
            ContractViolation, match="authority stage retention required"
        ):
            authority.authority_context_validator(host)
    finally:
        hosts.close_direct_validation_host(host)


def test_portable_value_cannot_replace_original_products(paired):  # noqa: F811
    _, host, _, proposed, _ = paired
    _, request = proposed("authority_derivation")
    with pytest.raises(TypeError, match="exact admitted dependency products"):
        authority.begin_authority_operation(host, request.registry_package)
    assert host not in authority._BY_SOURCE


def test_original_validator_not_reconstructible(paired):  # noqa: F811
    _, host, _, _, _ = paired
    validator = authority.authority_context_validator(host)
    assert authority.authority_context_validator(host) is validator
    with pytest.raises(TypeError):
        copy.copy(validator)
    with pytest.raises(ContractViolation, match="foreign authority validator"):
        object.__new__(type(validator)).validate_retained_semantic_operation_context(
            object(), expected=object()
        )
    with pytest.raises(TypeError, match="exact authority context"):
        validator.validate_retained_semantic_operation_context(
            object(), expected=object()
        )


def test_original_validator_method_substitution_refuses(paired, monkeypatch):  # noqa: F811
    _, host, _, _, _ = paired
    validator = authority.authority_context_validator(host)
    original = type(validator).validate_retained_semantic_operation_context
    monkeypatch.setattr(
        type(validator),
        "validate_retained_semantic_operation_context",
        lambda *a, **k: None,
    )
    with pytest.raises(ContractViolation, match="method substituted"):
        original(validator, object(), expected=object())


def test_validator_release_cannot_create_a_new_origin(paired):  # noqa: F811
    _, host, _, _, _ = paired
    validator = authority.authority_context_validator(host)
    del validator
    gc.collect()
    with pytest.raises(ContractViolation, match="validator was released"):
        authority.authority_context_validator(host)


def test_fork_and_host_close_refuse_validator(paired, monkeypatch):  # noqa: F811
    _, host, _, _, _ = paired
    validator = authority.authority_context_validator(host)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation, match="process"):
            validator.validate_retained_semantic_operation_context(
                object(), expected=object()
            )
    hosts.close_direct_validation_host(host)
    with pytest.raises(ContractViolation):
        validator.validate_retained_semantic_operation_context(
            object(), expected=object()
        )


def test_product_reread_uses_original_demand_validation_session(monkeypatch):
    events = []
    operation = object()
    coordinate = object()
    body = SimpleNamespace(canonical_body=b"products", coordinate=coordinate)

    @contextmanager
    def session(actual):
        assert actual is operation
        events.append("enter")
        try:
            yield
        finally:
            events.append("exit")

    reader = SimpleNamespace(call=lambda: events.append("read") or body)
    expected = object()
    snapshot = object()
    record = SimpleNamespace(
        demand=SimpleNamespace(binding=object()),
        product_reader=reader,
        product_record=SimpleNamespace(operation=operation),
        product_wire=b"products",
        product_coordinate=coordinate,
        stage=object(),
        completion_snapshot=snapshot,
        expected=expected,
    )
    monkeypatch.setattr(authority.hooks, "_guard", lambda _binding: nullcontext())
    monkeypatch.setattr(authority, "_identity", lambda _record, _guard: None)
    monkeypatch.setattr(
        authority.demands, "dependency_resolution_validation_session", session
    )
    monkeypatch.setattr(
        authority.planning_completion,
        "_validate_retained_completion",
        lambda _stage: snapshot,
    )
    monkeypatch.setattr(
        authority.comparison, "_same_portable", lambda actual, retained: actual is retained
    )

    assert authority._validate(record, read_products=True) is expected
    assert events == ["enter", "read", "exit"]
