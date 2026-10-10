"""Real Code policy hooks with fixture owner; no fixed application trust claim."""

import os
from dataclasses import replace
from threading import get_ident

import pytest
import test_direct_host as fixtures
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
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


class Owner(fixtures.Owner):
    def __init__(self, projection):
        super().__init__(projection)
        self.parent = object()
        self.guards = {}
        self.current = object()
        self.on_read = None
        self.on_validate = None
        self.substitute_acquire = False

    def validate_direct_invocation_context_binding(
        self, parent, lifetime, *, invocation, expected
    ):
        self.validate_command_lifetime(lifetime, expected=expected)
        if (
            parent is not self.parent
            or invocation.invocation_identity is not expected.invocation_identity
            or invocation.lifetime_epoch_identity is not expected.epoch_identity
            or invocation.process_id != expected.process_id
        ):
            raise ContractViolation("foreign parent correspondence")

    def acquire_catalog_epoch_exclusion(self, parent, *, expected):
        self.lock.acquire()
        guard = object()
        self.guards[guard] = (os.getpid(), get_ident())
        try:
            self.validate_catalog_epoch_exclusion(
                guard, parent=parent, expected=expected
            )
        except BaseException:
            self.release_catalog_epoch_exclusion(guard)
            raise
        if self.substitute_acquire:
            self.acquire_catalog_epoch_exclusion = lambda *a, **kw: object()
        return guard

    def validate_catalog_epoch_exclusion(self, guard, *, parent, expected):
        if (
            not self.live
            or parent is not self.parent
            or self.guards.get(guard) != (os.getpid(), get_ident())
            or expected.invocation_identity is not self.expected.invocation_identity
            or expected.lifetime_epoch_identity is not self.expected.epoch_identity
        ):
            raise ContractViolation("original exclusion unavailable")

    def release_catalog_epoch_exclusion(self, guard):
        assert self.guards.pop(guard) == (os.getpid(), get_ident())
        self.lock.release()

    def validate_current_catalog_epoch(self, epoch, *, expected):
        if (
            epoch is not self.current
            or expected.publication_identity is not self.epoch.publication_identity
        ):
            raise ContractViolation("retired epoch")

    def read_code_catalog_for_epoch(self, epoch, *, expected):
        self.validate_current_catalog_epoch(epoch, expected=expected)
        return self.expected.catalog

    def read_complete_scope_projection(self, snapshot):
        assert not self.guards, "source read under epoch exclusion"
        if self.on_read:
            self.on_read()
        return super().read_complete_scope_projection(snapshot)

    def validate_complete_scope_projection(self, snapshot, *, projection_digest=None):
        assert not self.guards, "source validation under epoch exclusion"
        if self.on_validate:
            self.on_validate()
        return super().validate_complete_scope_projection(
            snapshot, projection_digest=projection_digest
        )


def setup(monkeypatch, *, bind=True):
    monkeypatch.setattr(fixtures, "Owner", Owner)
    owner, bootstrap = fixtures.assembly()
    host = direct.register_direct_workspace_origin(bootstrap, owner.lifetime)
    invocation = DirectInvocationExpectation(
        owner.expected.invocation_identity, owner.expected.epoch_identity, os.getpid()
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
        participant = ep._assemble_code_epoch_participation(
            owner=owner,
            parent=owner.parent,
            invocation=invocation,
            epoch_owner=owner,
            guard=guard,
        )
        if bind:
            _bind_direct_policy_epoch(
                host, participant, owner.current, expected=owner.epoch, guard=guard
            )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    return owner, host, participant


def clearance(owner, participant):
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        participant.validate_catalog_publication_exclusion(
            guard, expected=owner.successor
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)


def test_real_policy_and_validation_block_successor(monkeypatch):
    owner, host, participant = setup(monkeypatch)
    calls = []

    def during():
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, participant)
        calls.append(True)

    owner.on_read = during
    owner.on_validate = during
    policy = direct.produce_registry_policy(host, owner.snapshot)
    clearance(owner, participant)
    calls.clear()
    assert direct.validate_admitted_registry_policy(host, policy).grants
    assert calls
    clearance(owner, participant)
    direct.close_direct_validation_host(host)
    with pytest.raises(ContractViolation):
        direct.validate_admitted_registry_policy(host, policy)


def test_failed_synchronous_read_releases_actual_finished_work(monkeypatch):
    owner, host, participant = setup(monkeypatch)

    def fail():
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, participant)
        raise ValueError("read failed")

    owner.on_read = fail
    with pytest.raises(ValueError, match="read failed"):
        direct.produce_registry_policy(host, owner.snapshot)
    clearance(owner, participant)
    assert not owner.guards
    direct.close_direct_validation_host(host)


@pytest.mark.parametrize("prior_use", [True, False])
def test_late_or_replayed_binding_refuses(monkeypatch, prior_use):
    owner, host, participant = setup(monkeypatch, bind=not prior_use)
    if prior_use:
        direct.produce_registry_policy(host, owner.snapshot)
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        with pytest.raises(ContractViolation, match="late or replayed"):
            _bind_direct_policy_epoch(
                host, participant, owner.current, expected=owner.epoch, guard=guard
            )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    direct.close_direct_validation_host(host)


def test_retired_epoch_refuses_before_source_read(monkeypatch):
    owner, host, _participant = setup(monkeypatch)
    owner.current = object()
    owner.on_read = lambda: pytest.fail("stale source entrance")
    with pytest.raises(ContractViolation, match="retired"):
        direct.produce_registry_policy(host, owner.snapshot)
    assert not owner.guards
    direct.close_direct_validation_host(host)


def test_original_validator_substitution_refuses(monkeypatch):
    owner, host, _participant = setup(monkeypatch)
    owner.validate_direct_invocation_context_binding = lambda *args, **kwargs: None
    with pytest.raises(ContractViolation, match="substituted"):
        direct.produce_registry_policy(host, owner.snapshot)
    direct.close_direct_validation_host(host)


def test_foreign_catalog_binding_refuses(monkeypatch):
    owner, host, participant = setup(monkeypatch, bind=False)
    monkeypatch.setattr(Owner, "read_code_catalog_for_epoch", lambda *a, **kw: object())
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        with pytest.raises(ContractViolation, match="catalog differs"):
            _bind_direct_policy_epoch(
                host, participant, owner.current, expected=owner.epoch, guard=guard
            )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    direct.close_direct_validation_host(host)


def test_close_during_read_does_not_return_policy(monkeypatch):
    owner, host, _participant = setup(monkeypatch)
    owner.on_read = lambda: direct.close_direct_validation_host(host)
    with pytest.raises(ContractViolation):
        direct.produce_registry_policy(host, owner.snapshot)
    assert not owner.guards
    assert host not in direct._HOSTS


def test_concurrent_source_read_blocks_publication(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    owner, host, participant = setup(monkeypatch)
    entered, release = Event(), Event()

    def wait_read():
        entered.set()
        assert release.wait(5)

    owner.on_read = wait_read
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(direct.produce_registry_policy, host, owner.snapshot)
        try:
            assert entered.wait(5)
            with pytest.raises(ContractViolation, match="active"):
                clearance(owner, participant)
        finally:
            release.set()
        policy = result.result(timeout=5)
    clearance(owner, participant)
    assert direct.validate_admitted_registry_policy(host, policy).grants
    direct.close_direct_validation_host(host)


def test_fork_refuses_before_code_lock(monkeypatch):
    from aware_code_retained_registry_policy_runtime import (
        direct_epoch_tracking as hooks,
    )

    owner, host, _participant = setup(monkeypatch)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(hooks.os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation, match="process changed"):
            direct.produce_registry_policy(host, owner.snapshot)
        with pytest.raises(ContractViolation, match="process changed"):
            direct.close_direct_validation_host(host)
    direct.produce_registry_policy(host, owner.snapshot)
    direct.close_direct_validation_host(host)


def test_acquire_substitution_still_releases_original_guard(monkeypatch):
    owner, host, _participant = setup(monkeypatch)
    owner.substitute_acquire = True
    with pytest.raises(ContractViolation, match="substituted"):
        direct.produce_registry_policy(host, owner.snapshot)
    assert not owner.guards
    del owner.acquire_catalog_epoch_exclusion
    owner.substitute_acquire = False
    direct.close_direct_validation_host(host)


def test_explicit_nested_uses_preserve_each_original_obligation(monkeypatch):
    from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
        _policy_epoch_use,
    )

    owner, host, participant = setup(monkeypatch)
    tracker = ep._state(participant)
    with _policy_epoch_use(host) as outer:
        binding, outer_use = outer
        assert binding.participant is participant
        assert tracker.uses[outer_use].status == "running"
        assert not owner.guards
        with _policy_epoch_use(host) as inner:
            assert inner[0] is binding and inner[1] is not outer_use
            assert set(tracker.uses) == {outer_use, inner[1]}
            with pytest.raises(ContractViolation, match="active"):
                clearance(owner, participant)
        assert set(tracker.uses) == {outer_use}
    assert not tracker.uses
    clearance(owner, participant)


def test_explicit_use_finishes_on_body_failure(monkeypatch):
    from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
        _policy_epoch_use,
    )

    _, host, participant = setup(monkeypatch)
    with pytest.raises(ValueError, match="body failed"), _policy_epoch_use(host) as pair:
        use = pair[1]
        raise ValueError("body failed")
    assert use not in ep._state(participant).uses


def test_validator_consumes_actual_yielded_use(monkeypatch):
    from aware_code_retained_registry_policy_runtime import (
        dependency_scope_operation as operations,
    )
    from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
        _policy_epoch_use,
    )
    from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
        RetainedDependencyScopeExpectation,
    )

    owner, host, _ = setup(monkeypatch)
    validator = operations._create_dependency_scope_operation_validator(host)
    with _policy_epoch_use(host) as pair:
        binding, use = pair
        # Fixture owner identities; this does not qualify source membership.
        expected = RetainedDependencyScopeExpectation(
            owner.parent, binding.epoch, use, os.getpid(), object(), owner, "consumer"
        )
        operations._retain_dependency_scope_operation(
            validator, use, expected=expected, purpose="policy_calculation"
        )
        assert (
            validator.validate_dependency_scope_operation(use, expected=expected)
            is None
        )
        operations._release_dependency_scope_operation(validator, use)
    with pytest.raises(ContractViolation):
        validator.validate_dependency_scope_operation(use, expected=expected)
