"""Same owner, epoch-bound Code legs; isolated record owner is not bootstrap proof."""

import copy
import os
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import catalog_host_leg as leg
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from test_catalog_host_leg import Owner as LegacyOwner
from test_materialization_catalog import _binding, _catalog, _execution_closure


class Owner(LegacyOwner):
    def __init__(self):
        super().__init__()
        self.invocation = DirectInvocationExpectation(object(), object(), os.getpid())
        self.pending = {}
        self.current = None
        self.guard = object()

    def validate_prepared_catalog_publication(self, preparation, *, expected):
        self.validate_catalog_parent()
        if preparation not in self.pending or preparation is self.current:
            raise ContractViolation("not pending")
        original = self.pending[preparation]
        if (
            original.preparation_identity is not expected.preparation_identity
            or original.successor.publication_identity
            is not expected.successor.publication_identity
            or original.entry_inputs_digest != expected.entry_inputs_digest
        ):
            raise ContractViolation("different preparation")

    def validate_catalog_epoch_publication_guard(self, guard, *, preparation, expected):
        if guard is not self.guard:
            raise ContractViolation("foreign guard")
        self.validate_prepared_catalog_publication(preparation, expected=expected)

    def validate_current_catalog_epoch(self, epoch, *, expected):
        self.validate_catalog_parent()
        if epoch is not self.current or epoch not in self.pending:
            raise ContractViolation("not current")
        original = self.pending[epoch].successor
        if (
            expected.publication_identity is not original.publication_identity
            or expected.code_catalog_digest != original.code_catalog_digest
            or expected.membership_catalog_digest != original.membership_catalog_digest
            or expected.contribution_digest != original.contribution_digest
        ):
            raise ContractViolation("different epoch")


def prepare(owner, predecessor=None):
    catalog = _catalog(_binding())
    digest = ContentDigest.of_bytes(b"membership")
    expected = CatalogPublicationExpectation(
        object(),
        predecessor,
        CatalogPairEpochExpectation(
            owner.invocation, object(), catalog.catalog_root_digest, digest, digest
        ),
        digest,
    )
    providers, planners = _execution_closure(catalog)
    prepared = leg.prepare_code_catalog_leg(
        joint_host=owner,
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        publication=expected,
    )
    return prepared, expected


def bind(owner, prepared, expected):
    preparation = object()
    owner.pending[preparation] = expected
    leg.bind_code_catalog_leg_publication(prepared, preparation, owner.guard)
    return preparation


def test_unbound_and_pending_hidden_then_same_bytes_successor_retires_old():
    owner = Owner()
    first, expected = prepare(owner)
    with pytest.raises(ContractViolation):
        leg.published_code_catalog_leg(first)
    first_preparation = bind(owner, first, expected)
    with pytest.raises(ContractViolation):
        leg.published_code_catalog_leg(first)
    owner.current = first_preparation
    owner.published = True
    old_admission, old_resolver = leg.published_code_catalog_leg(first)
    second, successor = prepare(owner, expected.successor)
    second_preparation = bind(owner, second, successor)
    assert old_resolver.catalog == leg.code_catalog_leg_snapshot(second)
    owner.current = second_preparation
    new_admission, new_resolver = leg.published_code_catalog_leg(second)
    assert new_admission is not old_admission
    assert new_resolver.catalog == leg.code_catalog_leg_snapshot(second)
    with pytest.raises(ContractViolation):
        _ = old_resolver.catalog
    with pytest.raises(ContractViolation):
        CodeSemanticContractCatalogResolver(old_admission)
    with pytest.raises(ContractViolation):
        leg.published_code_catalog_leg(first)


def test_binding_is_once_only_and_original_preparation_required():
    owner = Owner()
    prepared, expected = prepare(owner)
    with pytest.raises(ContractViolation):
        leg.bind_code_catalog_leg_publication(prepared, object(), owner.guard)
    original = bind(owner, prepared, expected)
    with pytest.raises(ContractViolation, match="replay"):
        leg.bind_code_catalog_leg_publication(prepared, original, owner.guard)


def test_failed_successor_does_not_revoke_predecessor():
    owner = Owner()
    first, expected = prepare(owner)
    owner.current = bind(owner, first, expected)
    _, resolver = leg.published_code_catalog_leg(first)
    second, successor = prepare(owner, expected.successor)
    bind(owner, second, successor)
    leg.revoke_code_catalog_leg(second)
    assert resolver.catalog


@pytest.mark.parametrize(
    "method",
    ["validate_current_catalog_epoch", "validate_prepared_catalog_publication"],
)
def test_original_epoch_method_substitution_rejects(method):
    owner = Owner()
    prepared, _ = prepare(owner)
    setattr(owner, method, lambda *a, **k: None)
    with pytest.raises(ContractViolation, match="substituted"):
        leg.validate_code_catalog_leg(prepared)


def test_parent_closure_revokes_all_epochs():
    owner = Owner()
    prepared, expected = prepare(owner)
    owner.current = bind(owner, prepared, expected)
    _, resolver = leg.published_code_catalog_leg(prepared)
    owner.live = False
    with pytest.raises(ContractViolation):
        _ = resolver.catalog


def test_binding_expected_values_are_detached_from_caller():
    owner = Owner()
    prepared, expected = prepare(owner)
    saved = replace(expected)
    object.__setattr__(
        expected, "entry_inputs_digest", ContentDigest.of_bytes(b"replacement")
    )
    original = object()
    owner.pending[original] = saved
    leg.bind_code_catalog_leg_publication(prepared, original, owner.guard)
    owner.current = original
    assert leg.published_code_catalog_leg(prepared)
    with pytest.raises(TypeError):
        copy.copy(prepared)


def test_foreign_guard_cannot_bind():
    owner = Owner()
    prepared, expected = prepare(owner)
    preparation = object()
    owner.pending[preparation] = expected
    with pytest.raises(ContractViolation):
        leg.bind_code_catalog_leg_publication(prepared, preparation, object())
    leg.bind_code_catalog_leg_publication(prepared, preparation, owner.guard)
