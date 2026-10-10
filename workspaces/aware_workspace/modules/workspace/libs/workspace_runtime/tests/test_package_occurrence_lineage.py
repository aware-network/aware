"""Original publisher/disposable-store reads; no installed V5 approval."""

import copy
import gc
import weakref
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import canonical_json_bytes
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore
from aware_workspace_runtime import materialization_head_v5 as heads
from aware_workspace_runtime import package_occurrence_lineage as records
from aware_workspace_runtime import semantic_materialization_publication as publication
from test_materialization_head_v5 import _digest, _head

ERROR = publication.WorkspaceSemanticMaterializationPublicationError
NAMESPACE = publication._V5_STATE_NAMESPACE


def stamp(value):
    payload = {k: v for k, v in value.items() if k != "record_digest"}
    value["record_digest"] = _digest(
        canonical_json_bytes({"contract": records.RECORD_CONTRACT, "value": payload})
    )
    return value


def head_binding(head, body):
    digest = _digest(body)
    return {
        "contract": heads.BINDING_CONTRACT,
        "role": "public_v5_head",
        "owner_contract": heads.HEAD_CONTRACT,
        "coordinate_digest": head["head_digest"],
        "body_ref": "cas://workspace-semantic-materialization/body/" + digest[7:],
        "body_digest": digest,
        "body_size": len(body),
    }


def fixture_record(state="active"):
    head, _, _, _ = _head(expected_revision=0)
    body = heads.encode_head(head, expected_output_roles=())
    binding = head_binding(head, body)
    pending = {
        "operation_ref": head["operation_ref"],
        "operation_digest": head["operation_digest"],
        "idempotency_key": "command:idempotency",
        "source_epoch_digest": head["source_epoch_digest"],
        "expected_prior_record_revision": 0,
        "expected_prior_head_digest": None,
        "claimed_prior_meta_pair_digest": None,
        "committed_meta_pair_digest": head["meta_pair_binding"]["body_digest"],
        "proposed_head_digest": head["head_digest"],
        "phase": "head_stored",
    }
    confirmation = {
        "operation_ref": head["operation_ref"],
        "head_cas_revision": 3,
        "head_digest": head["head_digest"],
        "head_wire_digest": _digest(body),
        "head_reread_evidence_digest": _digest(
            b"original writer evidence is not present in this fixture"
        ),
        "meta_pair_body_digest": head["meta_pair_binding"]["body_digest"],
        "source_epoch_digest": head["source_epoch_digest"],
    }
    value = {
        "contract": records.RECORD_CONTRACT,
        "installation_digest": _digest(b"fixture installation is not authority"),
        "occurrence_key": publication._v5_occurrence_key(head["package_occurrence"]),
        "occurrence": head["package_occurrence"],
        "incarnation_ref": head["incarnation_ref"],
        "record_revision": 4,
        "previous_record_digest": _digest(b"previous record"),
        "state_tag": state,
        "public_head": binding,
        "pending_operation": None,
        "confirmation": confirmation,
        "retirement": None,
        "checkpoint": None,
    }
    if state == "reserved_genesis":
        value.update(
            record_revision=1,
            previous_record_digest=None,
            public_head=None,
            confirmation=None,
            pending_operation=pending,
        )
        pending.update(
            phase="reserved", committed_meta_pair_digest=None, proposed_head_digest=None
        )
    elif state == "reserved_successor":
        value.update(record_revision=5, confirmation=None, pending_operation=pending)
        pending.update(
            operation_ref="command:next",
            operation_digest=_digest(b"next command"),
            expected_prior_record_revision=4,
            expected_prior_head_digest=head["head_digest"],
            claimed_prior_meta_pair_digest=head["meta_pair_binding"]["body_digest"],
            phase="reserved",
            committed_meta_pair_digest=None,
            proposed_head_digest=None,
        )
    elif state == "active_pending":
        value.update(record_revision=3, confirmation=None, pending_operation=pending)
    elif state == "retired":
        value.update(
            record_revision=5,
            retirement={
                "operation_ref": "command:retire",
                "operation_digest": _digest(b"retirement"),
                "expected_head_digest": head["head_digest"],
                "terminal_meta_pair_body_digest": head["meta_pair_binding"][
                    "body_digest"
                ],
                "declaration_evidence_digest": _digest(
                    b"fixture nonmembership is not authority"
                ),
                "reason": "explicit_owner_retirement",
            },
        )
    return stamp(value), head, body


class BodyStore:
    def __init__(self):
        self.bodies = {}
        self.reads = []
        self.on_read = None

    def read_body(self, body_ref):
        self.reads.append(body_ref)
        if self.on_read is not None:
            self.on_read()
        return self.bodies.get(body_ref)


class StateStore(InMemoryLocalOperationalStateStore):
    def __init__(self):
        super().__init__()
        self.reads = 0
        self.on_read = None
        self.overridden = False
        self.return_record = None

    def read(self, namespace, key, *, include_deleted=False):
        self.reads += 1
        result = super().read(namespace, key, include_deleted=include_deleted)
        if self.on_read is not None:
            self.on_read()
        return self.return_record if self.overridden else result


def store_fixture(state="active"):
    value, head, body = fixture_record(state)
    store = StateStore()
    # Persist the exact final revision without pretending these local records
    # came from a protected issuer or lawful lifecycle/history transitions.
    for revision in range(value["record_revision"]):
        store.compare_and_set(
            NAMESPACE, value["occurrence_key"], expected_revision=revision, value=value
        )
    bodies = BodyStore()
    if value["public_head"] is not None:
        bodies.bodies[value["public_head"]["body_ref"]] = body
    publisher = publication.WorkspaceSemanticMaterializationPublisher(
        state_store=store,
        body_store=bodies,
        state_namespace=NAMESPACE,
    )
    return publisher, store, bodies, value, head, body


def read(publisher, value):
    return publisher._read_graph_v5_head_data(
        value["occurrence"], expected_output_roles=()
    )


@pytest.mark.parametrize(
    "state",
    ["reserved_genesis", "reserved_successor", "active_pending", "active", "retired"],
)
def test_complete_record_and_original_publisher_head_read_are_detached_and_historical(
    state,
):
    publisher, store, bodies, value, _, body = store_fixture(state)
    wire = records.encode_record(value)
    detached = records.decode_record(wire)
    assert detached == value and detached is not value
    detached["occurrence"]["package_id"] = "foreign"
    result = read(publisher, value)
    assert type(result) is tuple and result[0] == wire
    assert result[1] == (None if state == "reserved_genesis" else body)
    assert store.reads == 2
    assert len(bodies.reads) == (0 if state == "reserved_genesis" else 1)
    if bodies.reads:
        assert bodies.reads == [value["public_head"]["body_ref"]]
    # Never return a nominal V3/V4 reread/admission or read a Meta pair body.
    assert all(item is None or type(item) is bytes for item in result)


@pytest.mark.parametrize("field", sorted(records._RECORD_FIELDS))
@pytest.mark.parametrize("mutation", ["missing", "foreign"])
def test_complete_field_inventory_and_hostile_values_reject_without_behavior(
    field, mutation
):
    value, _, _ = fixture_record()
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

    if mutation == "missing":
        del value[field]
    else:
        value[field] = Hostile()
    with pytest.raises(ERROR):
        records.encode_record(value)
    assert calls == []


@pytest.mark.parametrize(
    "change",
    [
        "state",
        "key",
        "revision",
        "previous",
        "pending",
        "confirmation",
        "retirement",
        "head",
        "checkpoint",
    ],
)
def test_coherently_restamped_record_cannot_hide_inconsistent_lifecycle(change):
    value, _, _ = fixture_record()
    if change == "state":
        value["state_tag"] = "reserved_genesis"
    elif change == "key":
        value["occurrence_key"] = _digest(b"another occurrence")
    elif change == "revision":
        value["record_revision"] = True
    elif change == "previous":
        value["previous_record_digest"] = None
    elif change == "pending":
        value["pending_operation"] = fixture_record("active_pending")[0][
            "pending_operation"
        ]
    elif change == "confirmation":
        value["confirmation"]["head_digest"] = _digest(b"foreign head")
    elif change == "retirement":
        value["retirement"] = fixture_record("retired")[0]["retirement"]
    elif change == "head":
        value["public_head"]["role"] = "meta_committed_pair"
    else:
        value["checkpoint"] = copy.deepcopy(value["public_head"])
    stamp(value)
    with pytest.raises(ERROR):
        records.encode_record(value)


@pytest.mark.parametrize(
    "change",
    [
        "pending-phase",
        "pending-pair",
        "proposed",
        "prior-pair",
        "prior-revision",
        "confirmation-cas",
        "retirement-reason",
    ],
)
def test_phase_and_cas_correlations_are_checked_after_restamping(change):
    state = (
        "retired"
        if change == "retirement-reason"
        else "active"
        if change == "confirmation-cas"
        else "active_pending"
    )
    value, _, _ = fixture_record(state)
    if change == "pending-phase":
        value["pending_operation"]["phase"] = "reserved"
    elif change == "pending-pair":
        value["pending_operation"]["committed_meta_pair_digest"] = None
    elif change == "proposed":
        value["pending_operation"]["proposed_head_digest"] = _digest(b"wrong")
    elif change == "prior-pair":
        value["pending_operation"]["claimed_prior_meta_pair_digest"] = _digest(b"wrong")
    elif change == "prior-revision":
        value["pending_operation"]["expected_prior_record_revision"] = value[
            "record_revision"
        ]
    elif change == "confirmation-cas":
        value["confirmation"]["head_cas_revision"] = value["record_revision"]
    else:
        value["retirement"]["reason"] = "filesystem_missing"
    stamp(value)
    with pytest.raises(ERROR):
        records.encode_record(value)


def test_post_retirement_genesis_preserves_nonzero_prior_revision_and_history_link():
    value, _, _ = fixture_record("reserved_genesis")
    value.update(
        record_revision=6,
        previous_record_digest=_digest(b"retired record"),
        incarnation_ref="lineage:new",
    )
    value["pending_operation"]["expected_prior_record_revision"] = 5
    stamp(value)
    assert records.decode_record(records.encode_record(value)) == value


def test_checkpoint_binding_is_bounded_metadata_not_history_validation():
    value, _, _ = fixture_record()
    binding = copy.deepcopy(value["public_head"])
    binding.update(
        role="lineage_checkpoint",
        owner_contract=records.CHECKPOINT_CONTRACT,
        body_size=16_384,
    )
    value["checkpoint"] = binding
    stamp(value)
    records.encode_record(value)
    binding["body_size"] += 1
    stamp(value)
    with pytest.raises(ERROR):
        records.encode_record(value)


@pytest.mark.parametrize(
    "variant", ["space", "duplicate", "extra", "too-large", "nonfinite", "deep"]
)
def test_noncanonical_or_unbounded_wires_refuse(variant):
    value, _, _ = fixture_record()
    body = records.encode_record(value)
    if variant == "space":
        body += b" "
    elif variant == "duplicate":
        body = b'{"contract":"foreign",' + body[1:]
    elif variant == "extra":
        value["extra"] = None
        body = canonical_json_bytes(value)
    elif variant == "too-large":
        body = b" " * 65_537
    elif variant == "nonfinite":
        body = body.replace(b'"record_revision":4', b'"record_revision":NaN')
    else:
        body = b"[" * 1000 + b"0" + b"]" * 1000
    with pytest.raises(ERROR):
        records.decode_record(body)


def test_absent_row_is_only_absence_not_genesis_and_never_reads_owner_bodies():
    publisher, store, bodies, value, _, _ = store_fixture()
    other = copy.deepcopy(value["occurrence"])
    other["package_id"] = "unobserved"
    assert publisher._read_graph_v5_head_data(other, expected_output_roles=()) is None
    assert store.reads == 2 and bodies.reads == []


@pytest.mark.parametrize(
    "change",
    [
        "deleted",
        "stored-revision",
        "occurrence",
        "head-domain",
        "head-body",
        "missing-body",
        "pending-source",
        "pending-operation",
        "pending-pair",
        "prior-revision",
        "confirmation-source",
        "confirmation-pair",
        "retired-pair",
    ],
)
def test_restamped_wrong_store_head_or_operation_is_not_accepted(change):
    state = (
        "retired"
        if change == "retired-pair"
        else "active_pending"
        if change.startswith("pending") or change == "prior-revision"
        else "active"
    )
    publisher, store, bodies, value, head, body = store_fixture(state)
    requested_occurrence = copy.deepcopy(head["package_occurrence"])
    if change == "deleted":
        store.delete(
            NAMESPACE,
            value["occurrence_key"],
            expected_revision=value["record_revision"],
        )
    elif change == "head-body":
        bodies.bodies[value["public_head"]["body_ref"]] = body + b" "
    elif change == "missing-body":
        bodies.bodies.clear()
    else:
        if change == "stored-revision":
            pass
        elif change == "occurrence":
            value["occurrence"]["package_id"] = "other"
            value["occurrence_key"] = publication._v5_occurrence_key(
                value["occurrence"]
            )
        elif change == "head-domain":
            value["public_head"]["coordinate_digest"] = _digest(b"wrong domain")
            value["confirmation"]["head_digest"] = value["public_head"][
                "coordinate_digest"
            ]
        elif change.startswith("pending"):
            field = {
                "pending-source": "source_epoch_digest",
                "pending-operation": "operation_digest",
                "pending-pair": "committed_meta_pair_digest",
            }[change]
            value["pending_operation"][field] = _digest(b"wrong")
        elif change == "prior-revision":
            value["pending_operation"]["expected_prior_record_revision"] = 1
        elif change == "retired-pair":
            value["retirement"]["terminal_meta_pair_body_digest"] = _digest(b"wrong")
        else:
            field = (
                "source_epoch_digest"
                if change == "confirmation-source"
                else "meta_pair_body_digest"
            )
            value["confirmation"][field] = _digest(b"wrong")
        if change != "stored-revision":
            value["record_revision"] += 1
            stamp(value)
        store.compare_and_set(
            NAMESPACE,
            publication._v5_occurrence_key(requested_occurrence),
            expected_revision=value["record_revision"]
            - (0 if change == "stored-revision" else 1),
            value=value,
        )
    with pytest.raises(ERROR):
        read(publisher, {"occurrence": requested_occurrence})


def test_revision_movement_during_body_io_refuses_even_when_head_bytes_do_not_change():
    publisher, store, bodies, value, _, _ = store_fixture()

    def move():
        value["record_revision"] += 1
        stamp(value)
        store.compare_and_set(
            NAMESPACE,
            value["occurrence_key"],
            expected_revision=value["record_revision"] - 1,
            value=value,
        )

    bodies.on_read = move
    with pytest.raises(ERROR, match="changed during"):
        read(publisher, value)


@pytest.mark.parametrize("entrance", ["state", "body", "resource"])
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_mid_io_reader_substitution_never_dispatches_hostile_call(entrance, behavior):
    publisher, store, bodies, value, _, _ = store_fixture()
    calls = []
    receiver, name = (store, "read") if entrance == "state" else (bodies, "read_body")

    def hostile(*args):
        calls.append("hostile")
        if behavior == "restore":
            delattr(receiver, name)
        if behavior == "raise":
            raise AssertionError("hostile")

    def substitute():
        store.on_read = None
        if entrance == "resource":
            publisher._body_store = object()
        else:
            setattr(receiver, name, hostile)

    store.on_read = substitute
    with pytest.raises(ERROR, match="resources changed|entrance substituted"):
        read(publisher, value)
    assert calls == [] and bodies.reads == []


def test_foreign_state_record_rejects_without_foreign_field_behavior():
    publisher, store, bodies, value, _, _ = store_fixture()
    calls = []
    original = store.read(NAMESPACE, value["occurrence_key"])

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError(name)

    store.overridden = True
    store.return_record = Foreign()
    with pytest.raises(ERROR):
        read(publisher, value)
    assert calls == [] and bodies.reads == []
    store.return_record = replace(original, key="other")
    with pytest.raises(ERROR):
        read(publisher, value)


def test_wrong_publisher_namespace_refuses_before_any_reads():
    publisher, store, bodies, value, _, _ = store_fixture()
    publisher._state_namespace = (
        publication.DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE
    )
    with pytest.raises(ERROR, match="namespace differs"):
        read(publisher, value)
    assert store.reads == 0 and bodies.reads == []


def test_sqlite_restart_reads_exact_historical_record_head_without_owner_access(
    tmp_path,
):
    value, _, body = fixture_record()
    path = tmp_path / "disposable-v5.sqlite3"
    writer = SqliteLocalOperationalStateStore(path)
    for revision in range(value["record_revision"]):
        writer.compare_and_set(
            NAMESPACE, value["occurrence_key"], expected_revision=revision, value=value
        )
    bodies = BodyStore()
    bodies.bodies[value["public_head"]["body_ref"]] = body
    publisher = publication.WorkspaceSemanticMaterializationPublisher(
        state_store=SqliteLocalOperationalStateStore(path),
        body_store=bodies,
        state_namespace=NAMESPACE,
    )
    assert read(publisher, value) == (records.encode_record(value), body)
    assert bodies.reads == [value["public_head"]["body_ref"]]


def test_hostile_metaclass_is_rejected_before_equality_or_attribute_behavior():
    calls = []

    class Meta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            raise AssertionError("metaclass equality")

        def __getattribute__(cls, name):
            calls.append("metaclass attribute")
            raise AssertionError(name)

    class Foreign(metaclass=Meta):
        pass

    value, _, _ = fixture_record()
    value["installation_digest"] = Foreign()
    with pytest.raises(ERROR):
        records.encode_record(value)
    assert calls == []


@pytest.mark.parametrize("roles", [None, [], ("duplicate", "duplicate"), (object(),)])
def test_wrong_role_inventory_refuses_before_even_absence_io(roles):
    publisher, store, bodies, value, _, _ = store_fixture()
    with pytest.raises(ERROR):
        publisher._read_graph_v5_head_data(
            value["occurrence"], expected_output_roles=roles
        )
    assert store.reads == 0 and bodies.reads == []


@pytest.mark.parametrize("fault", ["body", "namespace", "reader"])
def test_held_workspace_rejection_does_not_pin_borrowed_publisher_or_stores(fault):
    def reject():
        publisher, store, bodies, value, _, _ = store_fixture()
        references = (weakref.ref(publisher), weakref.ref(store), weakref.ref(bodies))
        if fault == "body":
            bodies.bodies[value["public_head"]["body_ref"]] = b"foreign body"
        elif fault == "namespace":
            publisher._state_namespace = "foreign"
        else:

            def substitute():
                store.read = lambda *args, **kwargs: None

            store.on_read = substitute
        try:
            publisher._read_graph_v5_head_data(
                value["occurrence"], expected_output_roles=()
            )
        except ERROR as error:
            retained = error
        finally:
            # This test owns its caller frame; never clear foreign owner frames.
            publisher = store = bodies = None
        return retained, references

    error, references = reject()
    gc.collect()
    assert all(reference() is None for reference in references)
    assert error.__traceback__ is not None
