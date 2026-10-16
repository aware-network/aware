"""Canonical evidence wires stay fresh while duplicate payload work is removed."""

import copy
import hashlib
import sys

import pytest
from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes

# isort: split
from aware_workspace_runtime import (
    WorkspaceMaterializationPlanningTimingEntry,
    WorkspaceMaterializationSessionError,
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
    WorkspaceSemanticMaterializationPublicationError,
)
from aware_workspace_runtime import semantic_dependency_graph as graph_module

# isort: split
from test_semantic_dependency_graph_codec import (
    _portable_execution_evidence,
    _result_counters,
)

# Captured with the accepted preimage, before changing any serializer.
GOLDEN = {
    "plan": (
        "0ebf9fbb5a845c9a0ad474b00d4facc841911ebbc7392ba928d22f3bcecad0d7",
        36242,
    ),
    "execution_binding": (
        "99b9af182031ca40b164c7a30b09d9d4e74c20220f266776de40d45e08fa9188",
        29012,
    ),
    "node_binding": (
        "2d4bc12cf667f175b71132593d973b9a5a5b1ce9a82182431b63fbfd4b97a3ac",
        12291,
    ),
    "request": (
        "e7296e9de9a58938fadf315f60efc68d518dd3c6fcfbab7b9a778e40b333e2c9",
        1234,
    ),
    "head": ("f1cdc5351364912f84463c69a058531c655f03636ce7760edb4096ed2bdeec8d", 2446),
    "receipt": (
        "5dfc1175713d26210d8c3981e64282a1daa520cd4bfdaf356d25dd746ffcb28a",
        4034,
    ),
    "head_reread": (
        "41f606dfa7cf319e08b8584b3c98c3e3ddeae5715c0eb2cc1076e883c5c4b667",
        3859,
    ),
    "source": ("cc2ab7bb6fef38de57df6229434a5f4dd86386663b6ec8470b66680b0de9c6ca", 404),
    "event": ("a10272fbd16d9d6d76d54c20b76705ba63cc57bd70e3b14d2429981dec3645cd", 722),
    "event_reread": (
        "bbc42066180398bb0c94f0e91744e3c8c6d423a04f573c2ff82edea416b8327b",
        653,
    ),
    "fanout": ("10b9c08ca0bd04d90a8c59be6af4c8b203336df4081d598df6127800fc11e51e", 429),
    "node": ("9482ca8bd27e0be979633310fade00056e5aa1411be04ee874bdc4f53be7059e", 11188),
    "graph": (
        "137d9a421cb2a0d3432c62bb5c256ccc02dd5726ae513054efc6c27fb76b58df",
        24595,
    ),
}
DIGEST_FIELDS = {
    "plan": "planning_result_digest",
    "execution_binding": "binding_digest",
    "node_binding": "binding_digest",
    "request": "request_digest",
    "head": "head_digest",
    "receipt": "receipt_digest",
    "head_reread": "reread_evidence_digest",
    "source": "source_evidence_digest",
    "event": "event_digest",
    "event_reread": "reread_evidence_digest",
    "fanout": "receipt_digest",
    "node": "node_result_digest",
    "graph": "result_digest",
}
ERRORS = (
    ValueError,
    TypeError,
    WorkspaceMaterializationSessionError,
    WorkspaceSemanticMaterializationPublicationError,
)


@pytest.fixture
async def values():
    plan, _, _, product, executed, reused = await _portable_execution_evidence()
    graph = WorkspaceSemanticMaterializationGraphResultV3.create(
        plan_result=plan,
        status="succeeded",
        ordered_node_results=(executed, reused),
        terminal_failure=None,
        ordered_fulfilled_products=(product,),
        counter_entries=_result_counters(),
    )
    head = executed.package_head_reread_evidence
    # Planning timings are measured; pin only this fixture's elapsed values.
    stable_plan = WorkspaceSemanticMaterializationGraphPlanResult.create(
        selection_resolution=plan.selection_resolution,
        graph=plan.graph,
        graph_plan_admission=plan.graph_plan_admission,
        graph_execution_binding=plan.graph_execution_binding,
        timing_entries=tuple(
            WorkspaceMaterializationPlanningTimingEntry(stage=item.stage, elapsed_ns=0)
            for item in plan.timing_entries
        ),
        counter_entries=plan.counter_entries,
    )
    return {
        "plan": stable_plan,
        "execution_binding": plan.graph_execution_binding,
        "node_binding": plan.graph_execution_binding.ordered_node_bindings[0],
        "request": head.head.request,
        "head": head.head,
        "receipt": executed.publication_receipt,
        "head_reread": head,
        "source": executed.session_source_evidence,
        "event": executed.session_event_reread_evidence.event,
        "event_reread": executed.session_event_reread_evidence,
        "fanout": executed.session_fanout_receipt,
        "node": executed,
        "graph": graph,
    }


@pytest.mark.parametrize("name", GOLDEN)
def test_wire_matches_accepted_preimage_and_remains_detached(values, name):
    value = values[name]
    returned = value.to_wire()
    wire = canonical_json_bytes(returned)
    assert (hashlib.sha256(wire).hexdigest(), len(wire)) == GOLDEN[name]
    returned["contract"] = "mutated returned dictionary"
    if "package" in returned:
        returned["package"]["package_ref"] = "mutated nested dictionary"
    assert canonical_json_bytes(value.to_wire()) == wire


@pytest.mark.parametrize("name", GOLDEN)
def test_every_serializer_revalidates_its_own_digest(values, name):
    value = copy.deepcopy(values[name])
    value.to_wire()
    object.__setattr__(value, DIGEST_FIELDS[name], ContentDigest.of_bytes(b"changed"))
    with pytest.raises(ERRORS):
        value.to_wire()


@pytest.mark.parametrize(
    "name",
    [
        "head",
        "receipt",
        "head_reread",
        "source",
        "event",
        "event_reread",
        "fanout",
        "node",
        "graph",
    ],
)
def test_nested_request_mutation_cannot_reuse_an_earlier_validation(values, name):
    values[name].to_wire()
    object.__setattr__(values["request"], "expected_head_revision", True)
    with pytest.raises(ERRORS):
        values[name].to_wire()


GRAPH_SERIALIZERS = {
    "plan": "_graph_plan_result_payload",
    "execution_binding": "_graph_execution_binding_payload",
    "node_binding": "_node_execution_binding_payload",
}


@pytest.mark.parametrize("name", GRAPH_SERIALIZERS)
def test_graph_serializer_builds_one_fresh_payload_per_call(values, name, monkeypatch):
    original = getattr(graph_module, GRAPH_SERIALIZERS[name])
    calls = []

    def counted(**kwargs):
        calls.append(None)
        return original(**kwargs)

    monkeypatch.setattr(graph_module, GRAPH_SERIALIZERS[name], counted)
    value = values[name]
    first = value.to_wire()
    assert len(calls) == 1
    assert value.to_wire() == first
    assert len(calls) == 2


@pytest.mark.parametrize("name", GRAPH_SERIALIZERS)
def test_graph_serializer_rejects_nested_mutation_after_prior_read(values, name):
    values[name].to_wire()
    node = values["node_binding"]
    object.__setattr__(node.code_match, "match_digest", ContentDigest.of_bytes(b"changed"))
    with pytest.raises(ERRORS):
        values[name].to_wire()


@pytest.mark.parametrize("name", GRAPH_SERIALIZERS)
def test_graph_serializer_checks_identity_after_payload_build(values, name, monkeypatch):
    value = values[name]
    original = getattr(graph_module, GRAPH_SERIALIZERS[name])

    def changed(**kwargs):
        payload = original(**kwargs)
        object.__setattr__(value, DIGEST_FIELDS[name], ContentDigest.of_bytes(b"late"))
        return payload

    monkeypatch.setattr(graph_module, GRAPH_SERIALIZERS[name], changed)
    with pytest.raises(ERRORS):
        value.to_wire()


@pytest.mark.parametrize("name", GRAPH_SERIALIZERS)
def test_graph_serializer_rejects_foreign_nested_binding_without_behavior(values, name):
    class Hostile:
        def __getattribute__(self, attr):
            raise AssertionError("foreign behavior invoked")

    node = values["node_binding"]
    object.__setattr__(node, "code_match", Hostile())
    with pytest.raises(ERRORS):
        values[name].to_wire()


SNAPSHOT_CASES = {
    "node_binding": (
        "node_digest",
        "_node_execution_binding_identity_payload",
        graph_module.WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING,
    ),
    "execution_binding": (
        "graph_digest",
        "_graph_execution_binding_identity_payload",
        graph_module.WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING,
    ),
    "plan": (
        "timing_entries",
        "_graph_plan_result_identity_payload",
        graph_module.WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT,
    ),
}


@pytest.mark.parametrize("name", SNAPSHOT_CASES)
@pytest.mark.parametrize(
    "window",
    ["payload_return", "restore_during_check", "check_return", "check_return_restore"],
)
def test_graph_serializer_authenticates_one_snapshot_with_genuine_helpers(
    values, name, window
):
    value = values[name]
    original_wire = value.to_wire()
    field_name, identity_name, contract = SNAPSHOT_CASES[name]
    digest_name = DIGEST_FIELDS[name]
    original_field = getattr(value, field_name)
    original_digest = getattr(value, digest_name)
    if field_name == "timing_entries":
        changed_field = tuple(
            graph_module.WorkspaceMaterializationPlanningTimingEntry(
                stage=item.stage, elapsed_ns=1
            )
            for item in original_field
        )
    else:
        changed_field = ContentDigest.of_bytes(b"coherent snapshot mutation")
    # The genuine identity helper constructs a valid coherent successor.
    fields = {
        field: getattr(value, field)
        for field in type(value).__dataclass_fields__
        if field != digest_name
    }
    changed_digest = graph_module._digest(
        contract,
        getattr(graph_module, identity_name)(**{**fields, field_name: changed_field}),
    )
    payload_code = getattr(graph_module, GRAPH_SERIALIZERS[name]).__code__
    digest_code = graph_module._digest.__code__
    mutations = []
    restorations = []

    def mutate():
        object.__setattr__(value, field_name, changed_field)
        object.__setattr__(value, digest_name, changed_digest)
        mutations.append(None)

    def restore():
        object.__setattr__(value, field_name, original_field)
        object.__setattr__(value, digest_name, original_digest)
        restorations.append(None)

    def profile(frame, event, arg):
        if event != "return":
            return
        if (
            frame.f_code is payload_code
            and not mutations
            and window in ("payload_return", "restore_during_check")
        ):
            mutate()
        if frame.f_code is digest_code and frame.f_locals["contract"] == contract:
            if window == "restore_during_check" and mutations and not restorations:
                restore()
            elif window in ("check_return", "check_return_restore") and not mutations:
                mutate()
                if window == "check_return_restore":
                    restore()

    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        if window in ("payload_return", "restore_during_check"):
            with pytest.raises(ERRORS, match="digest mismatched"):
                value.to_wire()
        else:
            # A post-check live mutation cannot restamp the returned snapshot.
            assert value.to_wire() == original_wire
        # The coherent successor itself is valid; rejection is snapshot mismatch.
        value.__post_init__()
    finally:
        sys.setprofile(previous)
        object.__setattr__(value, field_name, original_field)
        object.__setattr__(value, digest_name, original_digest)
    assert len(mutations) == 1
    assert len(restorations) == (window in ("restore_during_check", "check_return_restore"))
    assert value.to_wire() == original_wire


@pytest.mark.parametrize("name", ["request", "head", "receipt", "head_reread", "source", "event", "event_reread", "fanout", "node", "graph"])
@pytest.mark.parametrize("restore", [False, True])
def test_complete_payload_serializer_returns_its_captured_digest(values, name, restore):
    value = values[name]
    original_wire = value.to_wire()
    field = DIGEST_FIELDS[name]
    original_digest = getattr(value, field)
    module = sys.modules[type(value).__module__]
    digest_helper = getattr(module, {
        "semantic_materialization_publication": "_v2_digest",
        "materialization_session": "_session_v2_digest",
        "semantic_dependency_graph": "_digest",
    }[module.__name__.rsplit(".", 1)[1]])
    changed_digest = ContentDigest.of_bytes(b"late digest restamp")
    fired = False

    def observe(frame, event, result):
        nonlocal fired
        if (not fired and event == "return" and frame.f_code is digest_helper.__code__
            and frame.f_locals.get("contract") == original_wire["contract"]):
            fired = True
            object.__setattr__(value, field, changed_digest)
            if restore:
                object.__setattr__(value, field, original_digest)

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        assert value.to_wire() == original_wire
    finally:
        sys.setprofile(previous)
        object.__setattr__(value, field, original_digest)
    assert fired
    assert value.to_wire() == original_wire


@pytest.mark.parametrize("name", ["request", "head", "receipt", "head_reread", "source", "event", "event_reread", "fanout", "node", "graph"])
def test_complete_payload_serializer_rejects_foreign_digest_scalars_without_equality(values, name):
    value = values[name]
    digest = getattr(value, DIGEST_FIELDS[name])
    original_scalar = digest.value
    calls = []

    class ForeignScalar:
        def __eq__(self, other):
            calls.append("eq")
            return True

        def __ne__(self, other):
            calls.append("ne")
            return False

    object.__setattr__(digest, "value", ForeignScalar())
    try:
        with pytest.raises(TypeError, match="exact str"):
            value.to_wire()
        assert calls == []
    finally:
        object.__setattr__(digest, "value", original_scalar)
    value.__post_init__()
