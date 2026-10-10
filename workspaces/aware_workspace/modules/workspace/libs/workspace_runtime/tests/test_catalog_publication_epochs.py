"""Private records with inert leg/transfer markers; no catalog or Code authority."""

import copy
import os
from contextlib import contextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import ContentDigest
from aware_workspace_runtime.catalog_publication_epochs import (
    _CatalogPublicationRecords,
)
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeRuntime


def fixture():
    owner = WorkspaceCommandLifetimeRuntime()
    parent = owner._retain_direct_invocation_parent()
    invocation = DirectInvocationExpectation(
        owner.invocation_identity, owner.epoch_identity, os.getpid()
    )
    records = _CatalogPublicationRecords(
        owner=owner, parent=parent, invocation=invocation
    )
    return owner, parent, invocation, records


@contextmanager
def guarded(owner, parent, invocation):
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    try:
        yield guard
    finally:
        owner.release_catalog_epoch_exclusion(guard)


def publication(invocation, predecessor=None):
    digest = ContentDigest.of_bytes(b"inert snapshot")
    epoch = CatalogPairEpochExpectation(invocation, object(), digest, digest, digest)
    return CatalogPublicationExpectation(object(), predecessor, epoch, digest)


def initial(records, guard, invocation):
    expected = publication(invocation)
    pair = (object(), object())
    prep = records._prepare(guard, expected=expected, pair=pair)
    record = records._commit(guard, prep, expected=expected, transfer=None)
    return expected, prep, record


def test_exact_pair_transfer_retirement_and_historical_record():
    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        first, first_prep, old = initial(records, guard, invocation)
        expected = publication(invocation, first.successor)
        pair = (object(), object())
        prep = records._prepare(guard, expected=expected, pair=pair)
        assert records._read_current(guard, expected=first.successor) is old
        transfer = object()
        current = records._commit(guard, prep, expected=expected, transfer=transfer)
        assert records._read_current(guard, expected=expected.successor) is current
        assert current.attempt.pair is pair and current.transfer is transfer
        with pytest.raises(RuntimeError):
            records._read_current(guard, expected=first.successor)
        assert records._read_committed(guard, first_prep, transfer=None) is old
        with pytest.raises(RuntimeError):
            records._read_committed(guard, prep, transfer=object())
        with pytest.raises(RuntimeError):
            records._discard(guard, prep)
        next_expected = publication(invocation, expected.successor)
        next_prep = records._prepare(
            guard, expected=next_expected, pair=(object(), object())
        )
        with pytest.raises(RuntimeError):
            records._commit(guard, next_prep, expected=next_expected, transfer=transfer)


def test_stale_attempt_cannot_revoke_winner_and_failed_preparation_preserves_current():
    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        first, _, old = initial(records, guard, invocation)
        a, b = (
            publication(invocation, first.successor),
            publication(invocation, first.successor),
        )
        pa = records._prepare(guard, expected=a, pair=(object(), object()))
        pb = records._prepare(guard, expected=b, pair=(object(), object()))
        with pytest.raises(RuntimeError):
            records._commit(guard, pa, expected=a, transfer=None)
        assert records._read_current(guard, expected=first.successor) is old
        winner = records._commit(guard, pa, expected=a, transfer=object())
        with pytest.raises(RuntimeError):
            records._commit(guard, pb, expected=b, transfer=object())
        records._discard(guard, pb)
        records._discard(guard, pb)
        assert records._read_current(guard, expected=a.successor) is winner
        with pytest.raises(RuntimeError):
            records._prepare(guard, expected=b, pair=(object(), object()))


@pytest.mark.parametrize(
    "change", ["preparation", "publication", "digest", "predecessor"]
)
def test_substitution_and_snapshot_detachment(change):
    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        first, _, _ = initial(records, guard, invocation)
        expected = publication(invocation, first.successor)
        prep = records._prepare(guard, expected=expected, pair=(object(), object()))
        with pytest.raises(TypeError):
            copy.copy(prep)
        if change == "preparation":
            bad = replace(expected, preparation_identity=object())
        elif change == "publication":
            bad = replace(
                expected,
                successor=replace(expected.successor, publication_identity=object()),
            )
        elif change == "digest":
            bad = replace(
                expected, entry_inputs_digest=ContentDigest.of_bytes(b"other")
            )
        else:
            bad = replace(expected, predecessor=None)
        with pytest.raises(RuntimeError):
            records._commit(guard, prep, expected=bad, transfer=object())
        records._commit(guard, prep, expected=expected, transfer=object())
        with pytest.raises(RuntimeError):
            records._commit(guard, prep, expected=expected, transfer=object())


def test_foreign_guard_replacement_and_all_epoch_closure(monkeypatch):
    owner, parent, invocation, records = fixture()
    foreign, fp, fi, _ = fixture()
    with guarded(foreign, fp, fi) as other:
        with pytest.raises(RuntimeError):
            records._prepare(
                other, expected=publication(invocation), pair=(object(), object())
            )
    with guarded(owner, parent, invocation) as guard:
        expected, prep, _ = initial(records, guard, invocation)
        original = owner.validate_catalog_epoch_exclusion
        monkeypatch.setattr(
            owner, "validate_catalog_epoch_exclusion", lambda *a, **k: None
        )
        with pytest.raises(RuntimeError):
            records._read_current(guard, expected=expected.successor)
        monkeypatch.delattr(owner, "validate_catalog_epoch_exclusion")
        assert owner.validate_catalog_epoch_exclusion == original
        owner.close()
        with pytest.raises(RuntimeError):
            records._read_current(guard, expected=expected.successor)
        with pytest.raises(RuntimeError):
            records._read_committed(guard, prep, transfer=None)


def test_discarded_identity_replay_and_closed_records():
    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        expected = publication(invocation)
        prep = records._prepare(guard, expected=expected, pair=(object(), object()))
        records._discard(guard, prep)
        with pytest.raises(RuntimeError):
            records._prepare(guard, expected=expected, pair=(object(), object()))
        with pytest.raises(RuntimeError):
            records._commit(guard, prep, expected=expected, transfer=None)
        records._close(guard)
        with pytest.raises(RuntimeError):
            records._prepare(
                guard, expected=publication(invocation), pair=(object(), object())
            )


def test_read_current_under_command_guard_does_not_grant_epoch_mutation():
    from test_command_lifetime import assembled

    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        expected, _, record = initial(records, guard, invocation)
    _, context, lifetime = assembled(owner)
    guard = owner.acquire_command_publication_guard(lifetime, expected=context)
    try:
        assert records._read_current_for_parent(expected=expected.successor) is record
        assert owner._guard is guard
        with pytest.raises(Exception):
            records._prepare(
                guard,
                expected=publication(invocation, expected.successor),
                pair=(object(), object()),
            )
        with pytest.raises(Exception):
            records._close(guard)
        with pytest.raises(RuntimeError):
            records._read_current_for_parent(
                expected=replace(expected.successor, publication_identity=object())
            )
    finally:
        owner.release_command_publication_guard(guard)
    owner.close()
    with pytest.raises(Exception):
        records._read_current_for_parent(expected=expected.successor)


@pytest.mark.parametrize("failure", ["validator", "records_closed", "fork"])
def test_parent_current_read_fails_closed(monkeypatch, failure):
    owner, parent, invocation, records = fixture()
    with guarded(owner, parent, invocation) as guard:
        expected, _, _ = initial(records, guard, invocation)
        if failure == "records_closed":
            records._close(guard)
    if failure == "validator":
        monkeypatch.setattr(
            owner, "validate_direct_invocation_parent", lambda *a, **k: None
        )
    elif failure == "fork":
        monkeypatch.setattr(os, "getpid", lambda: invocation.process_id + 1)
    with pytest.raises(Exception):
        records._read_current_for_parent(expected=expected.successor)
