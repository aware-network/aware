"""Nominal boundary checks; the real Workspace/Environment canary proves sealing."""

import copy

import pytest
from aware_code_retained_registry_policy_runtime.catalog_completion_transfer import (
    AuthorityCatalogCompletionTransferRuntime,
    CatalogCompletionTransfer,
    _Entrance,
    bind_catalog_completion_transfer_runtime,
)
from aware_code_semantic_contract_runtime import ContractViolation


class Owner:
    def validate(self):
        return None


def test_nominal_transfer_and_runtime_cannot_be_constructed_or_copied():
    with pytest.raises(TypeError):
        CatalogCompletionTransfer()
    with pytest.raises(TypeError):
        AuthorityCatalogCompletionTransferRuntime()
    with pytest.raises(TypeError):
        copy.copy(object.__new__(CatalogCompletionTransfer))


def test_unregistered_host_cannot_bind_transfer_runtime():
    with pytest.raises(ContractViolation, match="epoch-bound"):
        bind_catalog_completion_transfer_runtime(Owner())


def test_original_bound_entrance_rejects_instance_substitution():
    owner = Owner()
    entrance = _Entrance.capture(owner, "validate")
    assert entrance.call() is None
    owner.validate = lambda: None
    with pytest.raises(ContractViolation, match="substituted"):
        entrance.call()


def test_protocol_shaped_callable_is_not_an_original_bound_entrance():
    with pytest.raises(TypeError, match="original"):
        _Entrance.capture(lambda: None, "__call__")
