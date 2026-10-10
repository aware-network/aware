"""Code-leg mechanics only; fake joint owner is not bootstrap authority."""

import copy

import pytest
from aware_code_semantic_contract_runtime import catalog_host_leg as leg
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from test_materialization_catalog import _binding, _catalog, _execution_closure


class Owner:
    def __init__(self):
        self.live = True
        self.published = False

    def validate_catalog_parent(self):
        if not self.live:
            raise RuntimeError("closed")

    def catalogs_published(self):
        return self.published


def prepare(owner=None, catalog=None, **changes):
    owner = Owner() if owner is None else owner
    catalog = _catalog(_binding()) if catalog is None else catalog
    providers, planners = _execution_closure(catalog)
    args = {
        "joint_host": owner,
        "catalog": catalog,
        "provider_executable_bindings": providers,
        "dependency_planner_bindings": planners,
    }
    args.update(changes)
    return owner, catalog, leg.prepare_code_catalog_leg(**args)


def test_hidden_until_paired_publication_then_close_revokes():
    owner, catalog, prepared = prepare()
    assert leg.code_catalog_leg_snapshot(prepared) == catalog
    with pytest.raises(ContractViolation, match="not published"):
        leg.published_code_catalog_leg(prepared)
    owner.published = True
    admission, resolver = leg.published_code_catalog_leg(prepared)
    assert resolver.catalog == catalog
    owner.live = False
    with pytest.raises(ContractViolation):
        CodeSemanticContractCatalogResolver(admission)
    leg.revoke_code_catalog_leg(prepared)
    leg.revoke_code_catalog_leg(prepared)


@pytest.mark.parametrize(
    "field", ["provider_executable_bindings", "dependency_planner_bindings"]
)
def test_incomplete_executable_closure_rejects(field):
    with pytest.raises(ContractViolation):
        prepare(**{field: ()})


def test_pending_canonical_admission_is_unusable(monkeypatch):
    original = leg._issue_code_semantic_contract_catalog
    captured = []

    def capture(**kwargs):
        admission = original(**kwargs)
        captured.append(admission)
        return admission

    monkeypatch.setattr(leg, "_issue_code_semantic_contract_catalog", capture)
    _, _, prepared = prepare()
    with pytest.raises(ContractViolation):
        CodeSemanticContractCatalogResolver(captured[0])
    leg.revoke_code_catalog_leg(prepared)


def test_source_movement_retires_leg():
    _, catalog, prepared = prepare()
    object.__setattr__(catalog, "catalog_generation", 999)
    with pytest.raises(ContractViolation):
        leg.validate_code_catalog_leg(prepared)
    with pytest.raises(ContractViolation, match="retired"):
        leg.code_catalog_leg_snapshot(prepared)


@pytest.mark.parametrize("method", ["validate_catalog_parent", "catalogs_published"])
def test_original_method_substitution_rejects(method):
    owner, _, prepared = prepare()
    setattr(owner, method, lambda: True)
    with pytest.raises(ContractViolation, match="substituted"):
        leg.validate_code_catalog_leg(prepared)
    leg.revoke_code_catalog_leg(prepared)


def test_rollback_after_canonical_issue_revokes(monkeypatch):
    original = leg._issue_code_semantic_contract_catalog
    owner = Owner()
    captured = []

    def close_after_issue(**kwargs):
        admission = original(**kwargs)
        captured.append(admission)
        owner.live = False
        return admission

    monkeypatch.setattr(leg, "_issue_code_semantic_contract_catalog", close_after_issue)
    with pytest.raises(RuntimeError, match="closed"):
        prepare(owner)
    with pytest.raises(ContractViolation, match="not registered"):
        CodeSemanticContractCatalogResolver(captured[0])


def test_detached_snapshot_mutation_does_not_change_retention():
    _, catalog, prepared = prepare()
    snapshot = leg.code_catalog_leg_snapshot(prepared)
    object.__setattr__(snapshot, "catalog_generation", 999)
    assert leg.code_catalog_leg_snapshot(prepared) == catalog
    leg.revoke_code_catalog_leg(prepared)


def test_published_parent_cannot_prepare_again():
    owner = Owner()
    owner.published = True
    with pytest.raises(ContractViolation):
        prepare(owner)


def test_handle_reconstruction_and_copy_reject():
    with pytest.raises(TypeError):
        leg.PreparedCodeCatalogLeg()
    _, _, prepared = prepare()
    with pytest.raises(TypeError):
        copy.copy(prepared)
    with pytest.raises(ContractViolation):
        leg.validate_code_catalog_leg(object.__new__(leg.PreparedCodeCatalogLeg))
    leg.revoke_code_catalog_leg(prepared)


def test_process_change_rejects_before_lock(monkeypatch):
    _, _, prepared = prepare()
    original_pid = leg.os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(leg.os, "getpid", lambda: original_pid + 1)
        with pytest.raises(ContractViolation, match="live"):
            leg.validate_code_catalog_leg(prepared)
    leg.revoke_code_catalog_leg(prepared)
