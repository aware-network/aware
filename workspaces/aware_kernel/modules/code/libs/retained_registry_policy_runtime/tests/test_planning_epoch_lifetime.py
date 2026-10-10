"""Original planning reservations; fixture parent is not application authority."""

import gc
import os
from dataclasses import replace
from weakref import ref

import pytest
import test_operation_context as fixtures
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_retained_registry_policy_runtime import operation_context as op
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from test_direct_epoch_tracking import Owner as EpochOwner
from test_direct_epoch_tracking import clearance


class Owner(EpochOwner):
    def read_complete_scope_projection(self, snapshot):
        assert self.guard is None, "source read under command publication guard"
        return super().read_complete_scope_projection(snapshot)

    def validate_complete_scope_projection(self, snapshot, *, projection_digest=None):
        assert self.guard is None, "source revalidation under command publication guard"
        return super().validate_complete_scope_projection(
            snapshot, projection_digest=projection_digest
        )


def setup(monkeypatch):
    participant = []
    original = direct.produce_registry_policy

    def bind_first(host, snapshot):
        owner = direct._HOSTS[host].methods["lifetime"].receiver
        invocation = DirectInvocationExpectation(
            owner.expected.invocation_identity,
            owner.expected.epoch_identity,
            os.getpid(),
        )
        digest = ContentDigest.of_bytes(b"membership")
        owner.epoch = CatalogPairEpochExpectation(
            invocation, object(), direct._HOSTS[host].catalog_digest, digest, digest
        )
        owner.successor = CatalogPublicationExpectation(
            object(),
            owner.epoch,
            replace(owner.epoch, publication_identity=object()),
            digest,
        )
        guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=invocation)
        try:
            tracker = ep._assemble_code_epoch_participation(
                owner=owner,
                parent=owner.parent,
                invocation=invocation,
                epoch_owner=owner,
                guard=guard,
            )
            _bind_direct_policy_epoch(
                host, tracker, owner.current, expected=owner.epoch, guard=guard
            )
            participant.append(tracker)
        finally:
            owner.release_catalog_epoch_exclusion(guard)
        return original(host, snapshot)

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "Owner", Owner)
        patch.setattr(direct, "produce_registry_policy", bind_first)
        values = fixtures.setup()
    return values, participant[0]


def test_context_remains_pending_across_repeated_validation(monkeypatch):
    values, tracker = setup(monkeypatch)
    owner, host, _, provider, registration, _ = values
    clearance(owner, tracker)
    context = fixtures.begin(values)
    for _ in range(2):
        expected = op.source_planning_expectation(host, context)
        op.source_planning_context_validator(
            host
        ).validate_retained_semantic_operation_context(context, expected=expected)
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, tracker)
    assert provider.calls == 0
    assert fixtures.selected._registration_state(registration).sequence == 0
    direct.close_direct_validation_host(host)


def test_source_reads_run_outside_both_guards_while_pending(monkeypatch):
    values, tracker = setup(monkeypatch)
    owner = values[0]
    reads = []

    def during():
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, tracker)
        reads.append(True)

    owner.on_read = during
    fixtures.begin(values)
    assert reads
    direct.close_direct_validation_host(values[1])


def test_unpublished_bad_request_abandons_only_its_reservation(monkeypatch):
    values, tracker = setup(monkeypatch)
    owner, host, policy, _, registration, _ = values
    with pytest.raises(TypeError):
        op.begin_source_planning_operation(host, policy, registration, object())
    clearance(owner, tracker)
    fixtures.begin(values)
    with pytest.raises(TypeError):
        op.begin_source_planning_operation(host, policy, registration, object())
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)
    direct.close_direct_validation_host(host)


def test_gc_does_not_retire_context_obligation(monkeypatch):
    values, tracker = setup(monkeypatch)
    context = fixtures.begin(values)
    weak = ref(context)
    del context
    gc.collect()
    assert weak() is None
    with pytest.raises(ContractViolation, match="active"):
        clearance(values[0], tracker)
    direct.close_direct_validation_host(values[1])


def test_failed_context_validation_does_not_retire_obligation(monkeypatch):
    values, tracker = setup(monkeypatch)
    context = fixtures.begin(values)
    expected = op.source_planning_expectation(values[1], context)
    validator = op.source_planning_context_validator(values[1])
    with pytest.raises(ContractViolation, match="expectation differs"):
        validator.validate_retained_semantic_operation_context(
            context, expected=replace(expected, operation_identity=object())
        )
    with pytest.raises(ContractViolation, match="active"):
        clearance(values[0], tracker)
    with pytest.raises(ContractViolation, match="foreign planning context"):
        op.source_planning_expectation(values[1], context)
    direct.close_direct_validation_host(values[1])


def test_forked_context_validation_refuses(monkeypatch):
    values, _tracker = setup(monkeypatch)
    context = fixtures.begin(values)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            op.source_planning_expectation(values[1], context)
    direct.close_direct_validation_host(values[1])


def test_original_validator_fork_rejection_preserves_parent_context(monkeypatch):
    values, _tracker = setup(monkeypatch)
    context = fixtures.begin(values)
    expected = op.source_planning_expectation(values[1], context)
    validator = op.source_planning_context_validator(values[1])
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation, match="process changed"):
            validator.validate_retained_semantic_operation_context(
                context, expected=expected
            )
    validator.validate_retained_semantic_operation_context(context, expected=expected)
    direct.close_direct_validation_host(values[1])


def test_revocation_during_read_prevents_successful_validation(monkeypatch):
    values, tracker = setup(monkeypatch)
    owner, host, *_rest = values
    context = fixtures.begin(values)
    expected = op.source_planning_expectation(host, context)
    validator = op.source_planning_context_validator(host)

    def revoke():
        owner.on_read = None
        with pytest.raises(ContractViolation, match="expectation differs"):
            validator.validate_retained_semantic_operation_context(
                context, expected=replace(expected, operation_identity=object())
            )

    owner.on_read = revoke
    with pytest.raises(ContractViolation, match="revoked during validation"):
        validator.validate_retained_semantic_operation_context(
            context, expected=expected
        )
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)
    direct.close_direct_validation_host(host)
