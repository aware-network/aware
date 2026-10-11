"""Exact V5 transition mechanics; disposable persistence is not an approval."""

import copy
import itertools

import pytest
from aware_local_service_runtime import LocalOperationalStateConflict
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore
from aware_workspace_runtime import materialization_head_v5 as heads
from aware_workspace_runtime import package_occurrence_lineage as records
from aware_workspace_runtime import semantic_materialization_publication as publication
from test_materialization_head_v5 import _binding, _digest, _head, _restamp
from test_package_occurrence_lineage import (
    BodyStore,
    fixture_record,
    head_binding,
    stamp,
)

ERROR = publication.WorkspaceSemanticMaterializationPublicationError


def advance(previous, **changes):
    value = copy.deepcopy(previous)
    value.update(
        record_revision=previous["record_revision"] + 1,
        previous_record_digest=previous["record_digest"],
        **changes,
    )
    return stamp(value)


def cycle(previous=None, previous_head=None, *, incarnation=None):
    """Return concrete data for all four original-issuer publication phases."""
    prior_revision = 0 if previous is None else previous["record_revision"]
    head, _, _, _ = _head(expected_revision=prior_revision)
    if incarnation is not None:
        head["incarnation_ref"] = incarnation
    successor = previous is not None and previous["state_tag"] == "active"
    if successor:
        head["operation_ref"] = "command:successor"
        head["operation_digest"] = _digest(b"successor operation")
        head["predecessor_head_digest"] = previous_head["head_digest"]
        pair_body = b'{"pair":2}'
        head["meta_pair_binding"] = _binding(
            "meta_committed_pair", "test.pair.v2", {"pair": 2}, pair_body
        )
    _restamp(head)
    head_body = heads.encode_head(head, expected_output_roles=())
    reserved, _, _ = fixture_record("reserved_genesis")
    reserved.update(
        record_revision=prior_revision + 1,
        previous_record_digest=None if previous is None else previous["record_digest"],
        incarnation_ref=head["incarnation_ref"],
        state_tag="reserved_successor" if successor else "reserved_genesis",
        public_head=copy.deepcopy(previous["public_head"]) if successor else None,
    )
    pending = reserved["pending_operation"]
    pending.update(
        operation_ref=head["operation_ref"],
        operation_digest=head["operation_digest"],
        source_epoch_digest=head["source_epoch_digest"],
        expected_prior_record_revision=prior_revision,
        expected_prior_head_digest=head["predecessor_head_digest"],
        claimed_prior_meta_pair_digest=(
            previous_head["meta_pair_binding"]["body_digest"] if successor else None
        ),
    )
    stamp(reserved)
    committed = advance(reserved)
    committed["pending_operation"].update(
        phase="meta_committed",
        committed_meta_pair_digest=head["meta_pair_binding"]["body_digest"],
    )
    stamp(committed)
    stored = advance(
        committed, state_tag="active_pending", public_head=head_binding(head, head_body)
    )
    stored["pending_operation"].update(
        phase="head_stored", proposed_head_digest=head["head_digest"]
    )
    stamp(stored)
    confirmed = advance(
        stored,
        state_tag="active",
        pending_operation=None,
        confirmation={
            "operation_ref": head["operation_ref"],
            "head_cas_revision": stored["record_revision"],
            "head_digest": head["head_digest"],
            "head_wire_digest": _digest(head_body),
            "head_reread_evidence_digest": _digest(b"disposable fixture reread"),
            "meta_pair_body_digest": head["meta_pair_binding"]["body_digest"],
            "source_epoch_digest": head["source_epoch_digest"],
        },
    )
    return (reserved, committed, stored, confirmed), head, head_body


def validate(
    previous, proposed, previous_head=None, proposed_head=None, *, publisher=None
):
    call = (
        records.validate_record_transition
        if publisher is None
        else publisher._validate_graph_v5_record_transition
    )
    call(
        None if previous is None else records.encode_record(previous),
        records.encode_record(proposed),
        previous_head_body=previous_head,
        proposed_head_body=proposed_head,
        expected_output_roles=(),
    )


def retire(previous, head):
    return advance(
        previous,
        state_tag="retired",
        retirement={
            "operation_ref": "command:retire",
            "operation_digest": _digest(b"retire"),
            "expected_head_digest": head["head_digest"],
            "terminal_meta_pair_body_digest": head["meta_pair_binding"]["body_digest"],
            "declaration_evidence_digest": _digest(b"fixture retirement"),
            "reason": "explicit_owner_retirement",
        },
    )


def test_complete_genesis_successor_retirement_and_new_lineage_are_persistable(
    tmp_path,
):
    database = tmp_path / "disposable.sqlite3"
    store = SqliteLocalOperationalStateStore(database)
    bodies = BodyStore()
    publisher = publication.WorkspaceSemanticMaterializationPublisher(
        state_store=store,
        body_store=bodies,
        state_namespace=publication._V5_STATE_NAMESPACE,
    )
    previous = previous_head = previous_head_body = None
    cycles = []
    for kind in ("genesis", "successor", "new_lineage"):
        data, head, head_body = cycle(
            previous,
            previous_head,
            incarnation="lineage:new" if kind == "new_lineage" else None,
        )
        cycles.append(data)
        for proposed in data:
            proposed_head_body = (
                head_body
                if proposed["state_tag"] in ("active_pending", "active")
                else previous_head_body
                if proposed["public_head"] is not None
                else None
            )
            validate(
                previous,
                proposed,
                previous_head_body,
                proposed_head_body,
                publisher=publisher,
            )
            # Original store CAS is exercised directly as disposable mechanics.
            # No installed issuer, source approval or Meta verification is forged.
            persisted = store.compare_and_set(
                publication._V5_STATE_NAMESPACE,
                proposed["occurrence_key"],
                expected_revision=0
                if previous is None
                else previous["record_revision"],
                value=proposed,
            )
            assert persisted.revision == proposed["record_revision"]
            if proposed_head_body is not None:
                bodies.bodies[proposed["public_head"]["body_ref"]] = proposed_head_body
            assert publisher._read_graph_v5_head_data(
                proposed["occurrence"], expected_output_roles=()
            ) == (records.encode_record(proposed), proposed_head_body)
            previous, previous_head_body = proposed, proposed_head_body
        previous_head = head
        if kind == "successor":
            proposed = retire(previous, head)
            validate(previous, proposed, previous_head_body, previous_head_body)
            store.compare_and_set(
                publication._V5_STATE_NAMESPACE,
                proposed["occurrence_key"],
                expected_revision=previous["record_revision"],
                value=proposed,
            )
            previous = proposed
    restarted = SqliteLocalOperationalStateStore(database)
    record = restarted.read(publication._V5_STATE_NAMESPACE, previous["occurrence_key"])
    assert record.revision == 13
    assert records.encode_record(
        records._plain_state_value(record.value)
    ) == records.encode_record(previous)
    assert cycles[2][0]["pending_operation"]["expected_prior_record_revision"] == 9
    with pytest.raises(LocalOperationalStateConflict):
        restarted.compare_and_set(
            publication._V5_STATE_NAMESPACE,
            previous["occurrence_key"],
            expected_revision=12,
            value=previous,
        )


@pytest.mark.parametrize(
    "before,after",
    [(i, j) for i, j in itertools.product(range(4), repeat=2) if j != i + 1],
)
def test_replay_skipping_and_backwards_phases_reject(before, after):
    data, _, head_body = cycle()
    proposed = advance(
        data[before],
        **{
            k: v
            for k, v in data[after].items()
            if k not in ("record_revision", "previous_record_digest", "record_digest")
        },
    )
    with pytest.raises(ERROR):
        validate(
            data[before],
            proposed,
            head_body if data[before]["public_head"] else None,
            head_body if proposed["public_head"] else None,
        )


@pytest.mark.parametrize(
    "field",
    [
        "operation_ref",
        "operation_digest",
        "idempotency_key",
        "source_epoch_digest",
        "expected_prior_record_revision",
    ],
)
def test_pending_correlation_cannot_be_replaced(field):
    data, _, _ = cycle()
    proposed = copy.deepcopy(data[1])
    pending = proposed["pending_operation"]
    pending[field] = (
        1
        if field == "expected_prior_record_revision"
        else (
            "command:foreign"
            if field in ("operation_ref", "idempotency_key")
            else _digest(b"foreign")
        )
    )
    stamp(proposed)
    with pytest.raises(ERROR):
        validate(data[0], proposed)


@pytest.mark.parametrize(
    "field",
    [
        "installation_digest",
        "occurrence_key",
        "incarnation_ref",
        "previous_record_digest",
        "record_revision",
    ],
)
def test_wrong_previous_or_immutable_record_refuses(field):
    data, _, _ = cycle()
    proposed = copy.deepcopy(data[1])
    proposed[field] = (
        3
        if field == "record_revision"
        else ("lineage:foreign" if field == "incarnation_ref" else _digest(b"foreign"))
    )
    stamp(proposed)
    with pytest.raises(ERROR):
        validate(data[0], proposed)


def test_confirmation_cannot_name_an_earlier_head_cas():
    data, _, head_body = cycle()
    proposed = copy.deepcopy(data[3])
    proposed["confirmation"]["head_cas_revision"] = 2
    stamp(proposed)
    with pytest.raises(ERROR, match="exact HEAD CAS"):
        validate(data[2], proposed, head_body, head_body)


def test_changed_source_epoch_cannot_reuse_prior_meta_pair():
    data, old_head, old_body = cycle()
    successor, _, _ = cycle(data[3], old_head)
    reserved, committed = successor[:2]
    for value in (reserved, committed):
        value["pending_operation"]["source_epoch_digest"] = _digest(b"changed epoch")
        stamp(value)
    committed["pending_operation"]["committed_meta_pair_digest"] = old_head[
        "meta_pair_binding"
    ]["body_digest"]
    committed["previous_record_digest"] = reserved["record_digest"]
    stamp(committed)
    with pytest.raises(ERROR, match="epoch requires a pair successor"):
        validate(reserved, committed, old_body, old_body)


def test_retired_lineage_cannot_resume_its_original_incarnation():
    data, head, head_body = cycle()
    retired = retire(data[3], head)
    revived, _, _ = cycle(retired, head)
    with pytest.raises(ERROR, match="new incarnation"):
        validate(retired, revived[0], head_body)


def test_missing_or_foreign_head_body_rejects_before_store_effect():
    data, _, head_body = cycle()
    for body in (None, b"foreign", head_body + b" "):
        with pytest.raises(ERROR, match="retained HEAD body differs"):
            validate(data[1], data[2], proposed_head=body)


def test_absent_data_does_not_allow_stored_or_confirmed_first_record():
    data, _, head_body = cycle()
    for value in data[1:]:
        with pytest.raises(ERROR, match="first record"):
            validate(
                None, value, proposed_head=head_body if value["public_head"] else None
            )


def test_unchanged_epoch_allows_exact_current_pair_data():
    data, old_head, old_body = cycle()
    successor, _, _ = cycle(data[3], old_head)
    successor[1]["pending_operation"]["committed_meta_pair_digest"] = old_head[
        "meta_pair_binding"
    ]["body_digest"]
    stamp(successor[1])
    validate(successor[0], successor[1], old_body, old_body)


def test_two_disposable_connections_cannot_both_spend_one_record_revision(tmp_path):
    database = tmp_path / "race.sqlite3"
    first = SqliteLocalOperationalStateStore(database)
    second = SqliteLocalOperationalStateStore(database)
    data, _, _ = cycle()
    reserved, committed = data[:2]
    for store in (first, second):
        validate(None, reserved)
    first.compare_and_set(
        publication._V5_STATE_NAMESPACE,
        reserved["occurrence_key"],
        expected_revision=0,
        value=reserved,
    )
    with pytest.raises(LocalOperationalStateConflict):
        second.compare_and_set(
            publication._V5_STATE_NAMESPACE,
            reserved["occurrence_key"],
            expected_revision=0,
            value=reserved,
        )
    validate(reserved, committed)
    second.compare_and_set(
        publication._V5_STATE_NAMESPACE,
        committed["occurrence_key"],
        expected_revision=1,
        value=committed,
    )
    with pytest.raises(LocalOperationalStateConflict):
        first.compare_and_set(
            publication._V5_STATE_NAMESPACE,
            committed["occurrence_key"],
            expected_revision=1,
            value=committed,
        )


@pytest.mark.parametrize(
    "roles", [("duplicate", "duplicate"), ["role"], ("role",) * 65]
)
def test_role_inventory_rejects_even_before_genesis_has_a_head(roles):
    data, _, _ = cycle()
    with pytest.raises(ERROR):
        records.validate_record_transition(
            None,
            records.encode_record(data[0]),
            previous_head_body=None,
            proposed_head_body=None,
            expected_output_roles=roles,
        )


def test_replacement_values_cannot_dispatch_foreign_behavior():
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError(name)

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("equality")

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("hash")

    data, _, _ = cycle()
    canonical = records.encode_record(data[0])
    for previous, proposed in ((Hostile(), canonical), (None, Hostile())):
        with pytest.raises(ERROR):
            records.validate_record_transition(
                previous,
                proposed,
                previous_head_body=None,
                proposed_head_body=None,
                expected_output_roles=(),
            )
    assert calls == []


def test_confirmed_publication_cannot_be_replaced_during_retirement():
    data, head, head_body = cycle()
    retired = retire(data[3], head)
    retired["confirmation"]["head_reread_evidence_digest"] = _digest(b"substituted")
    stamp(retired)
    with pytest.raises(ERROR, match="terminal publication evidence"):
        validate(data[3], retired, head_body, head_body)
