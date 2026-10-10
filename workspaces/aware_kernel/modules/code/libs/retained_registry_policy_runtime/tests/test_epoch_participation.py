"""Tracker mechanics with original guarded fixture owner, not integrated coverage."""

import copy
import gc
import os
from contextlib import contextmanager
from dataclasses import replace
from threading import RLock, Thread, get_ident

import pytest
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)


class Owner:
    def __init__(self):
        self.parent = object()
        self.invocation = DirectInvocationExpectation(object(), object(), os.getpid())
        self.lock = RLock()
        self.guards = {}
        self.live = True
        self.close_on_epoch = False
        self.current = object()
        digest = ContentDigest.of_bytes(b"catalog")
        self.epoch = CatalogPairEpochExpectation(
            self.invocation, object(), digest, digest, digest
        )
        self.next = CatalogPublicationExpectation(
            object(),
            self.epoch,
            replace(self.epoch, publication_identity=object()),
            digest,
        )

    def validate_catalog_epoch_exclusion(self, guard, *, parent, expected):
        if (
            not self.live
            or parent is not self.parent
            or self.guards.get(guard) != (os.getpid(), get_ident())
            or expected.invocation_identity is not self.invocation.invocation_identity
            or expected.lifetime_epoch_identity
            is not self.invocation.lifetime_epoch_identity
            or expected.process_id != os.getpid()
        ):
            raise ContractViolation("original guard unavailable")

    def validate_current_catalog_epoch(self, epoch, *, expected):
        if (
            not self.live
            or epoch is not self.current
            or expected.publication_identity is not self.epoch.publication_identity
        ):
            raise ContractViolation("epoch retired")
        if self.close_on_epoch:
            self.live = False

    @contextmanager
    def held(self):
        with self.lock:
            guard = object()
            self.guards[guard] = (os.getpid(), get_ident())
            try:
                yield guard
            finally:
                self.guards.pop(guard)


def setup():
    owner = Owner()
    with owner.held() as guard:
        participant = ep._assemble_code_epoch_participation(
            owner=owner,
            parent=owner.parent,
            invocation=owner.invocation,
            epoch_owner=owner,
            guard=guard,
        )
        participant._register_epoch(guard, owner.current, expected=owner.epoch)
    return owner, participant


def test_pending_and_running_block_then_actual_finish_allows():
    owner, participant = setup()
    with owner.held() as guard:
        use = participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        with pytest.raises(ContractViolation, match="active"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )
        participant._start_epoch_use(guard, use)
        with pytest.raises(ContractViolation, match="active"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )
        participant._finish_epoch_use(guard, use)
        participant.validate_catalog_publication_exclusion(guard, expected=owner.next)
        with pytest.raises(ContractViolation):
            participant._finish_epoch_use(guard, use)


def test_unstarted_abandonment_and_no_running_abandonment():
    owner, participant = setup()
    with owner.held() as guard:
        first = participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        participant._abandon_unstarted_epoch_use(guard, first)
        second = participant._begin_epoch_use(
            guard, owner.current, expected=owner.epoch
        )
        participant._start_epoch_use(guard, second)
        with pytest.raises(ContractViolation):
            participant._abandon_unstarted_epoch_use(guard, second)
        participant._finish_epoch_use(guard, second)


def test_uncertainty_cannot_be_cleared_by_finish_or_abandon():
    owner, participant = setup()
    with owner.held() as guard:
        use = participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        participant._start_epoch_use(guard, use)
        participant._mark_epoch_use_uncertain(guard, use)
        with pytest.raises(ContractViolation):
            participant._finish_epoch_use(guard, use)
        with pytest.raises(ContractViolation):
            participant._abandon_unstarted_epoch_use(guard, use)
        with pytest.raises(ContractViolation, match="active"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )
        participant._close_under_exclusion(guard)
        with pytest.raises(ContractViolation):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )


def test_dropping_handle_does_not_drop_obligation():
    owner, participant = setup()
    with owner.held() as guard:
        participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        gc.collect()
        with pytest.raises(ContractViolation, match="active"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )
        participant._close_under_exclusion(guard)


def test_forged_guard_and_expired_guard_reject():
    owner, participant = setup()
    with pytest.raises(ContractViolation):
        participant.validate_catalog_publication_exclusion(
            object(), expected=owner.next
        )
    with owner.held() as guard:
        participant.validate_catalog_publication_exclusion(guard, expected=owner.next)
    with pytest.raises(ContractViolation):
        participant.validate_catalog_publication_exclusion(guard, expected=owner.next)


def test_foreign_ticket_and_copy_reject():
    owner, participant = setup()
    other, foreign = setup()
    with other.held() as guard:
        use = foreign._begin_epoch_use(guard, other.current, expected=other.epoch)
    with owner.held() as guard:
        with pytest.raises(ContractViolation):
            participant._start_epoch_use(guard, use)
        with pytest.raises(TypeError):
            copy.copy(use)
    with other.held() as guard:
        foreign._abandon_unstarted_epoch_use(guard, use)


def test_retirement_refuses_new_use_and_publication():
    owner, participant = setup()
    old = owner.current
    owner.current = object()
    with owner.held() as guard:
        with pytest.raises(ContractViolation):
            participant._begin_epoch_use(guard, old, expected=owner.epoch)
        with pytest.raises(ContractViolation):
            participant.validate_catalog_publication_exclusion(
                guard, expected=owner.next
            )


@pytest.mark.parametrize(
    "method", ["validate_catalog_epoch_exclusion", "validate_current_catalog_epoch"]
)
def test_original_owner_method_substitution_rejects(method):
    owner, participant = setup()
    setattr(owner, method, lambda *a, **k: None)
    with owner.held() as guard, pytest.raises(ContractViolation):
        participant.validate_catalog_publication_exclusion(guard, expected=owner.next)


def test_original_participant_method_substitution_rejects():
    owner, participant = setup()
    original = participant.validate_catalog_publication_exclusion
    participant.validate_catalog_publication_exclusion = lambda *a, **k: None
    with owner.held() as guard, pytest.raises(ContractViolation):
        original(guard, expected=owner.next)


def test_installation_replay_rejects():
    owner, _participant = setup()
    with owner.held() as guard, pytest.raises(ContractViolation, match="replay"):
        ep._assemble_code_epoch_participation(
            owner=owner,
            parent=owner.parent,
            invocation=owner.invocation,
            epoch_owner=owner,
            guard=guard,
        )


def test_fork_refuses_before_locks(monkeypatch):
    owner, participant = setup()
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(ep.os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            participant.validate_catalog_publication_exclusion(
                object(), expected=owner.next
            )


def test_foreign_publication_rejects():
    owner, participant = setup()
    other = Owner()
    with owner.held() as guard, pytest.raises(ContractViolation):
        participant.validate_catalog_publication_exclusion(guard, expected=other.next)


def test_close_during_epoch_check_cannot_issue_reservation():
    owner, participant = setup()
    owner.close_on_epoch = True
    with owner.held() as guard, pytest.raises(ContractViolation):
        participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)


def test_other_thread_publication_sees_outstanding_work():
    owner, participant = setup()
    with owner.held() as guard:
        use = participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        participant._start_epoch_use(guard, use)
    refused = []

    def publish():
        with owner.held() as guard:
            try:
                participant.validate_catalog_publication_exclusion(
                    guard, expected=owner.next
                )
            except ContractViolation:
                refused.append(True)

    thread = Thread(target=publish)
    thread.start()
    thread.join(3)
    assert not thread.is_alive() and refused == [True]
    with owner.held() as guard:
        participant._finish_epoch_use(guard, use)
        participant.validate_catalog_publication_exclusion(guard, expected=owner.next)


def test_guard_from_other_thread_refuses_without_blocking():
    owner, participant = setup()
    refused = []
    with owner.held() as guard:

        def use_foreign_thread():
            try:
                participant.validate_catalog_publication_exclusion(
                    guard, expected=owner.next
                )
            except ContractViolation:
                refused.append(True)

        thread = Thread(target=use_foreign_thread)
        thread.start()
        thread.join(3)
        assert not thread.is_alive() and refused == [True]
