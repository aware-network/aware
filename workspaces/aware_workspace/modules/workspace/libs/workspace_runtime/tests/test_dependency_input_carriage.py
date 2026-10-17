"""Original publication/input custody; fixture resolution is not live admission."""

import asyncio
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ProfileInputDeclaration,
    RoleBinding,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractRuntime,
    SemanticDependencyDemandSet,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
    decode_dependency_product_input,
    dependency_product_input_body,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.materialization_operation import (
    WorkspaceMaterializeOperationError,
    derive_workspace_materialize_execution_input_closure_digest,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceSemanticMaterializationRequestV3,
    _body_ref,
)
from test_dependency_fulfillment import issue, read
from test_semantic_materialization_publication import (
    EFFECT,
    OUTPUT,
    RESULT,
    SOURCE,
    TRANSITION,
    _invocation,
    _JsonCodec,
    _profile,
    _Provider,
)

pytest_plugins = ("test_dependency_fulfillment",)


def _request(original, **changes):
    values = {
        name: getattr(original, name)
        for name in original.__dataclass_fields__ if name != "request_digest"
    }
    return WorkspaceSemanticMaterializationRequestV3.create(**(values | changes))


def _retain(f):
    _, bodies = _invocation("a")
    request = _request(
        f.request,
        expected_head_revision=1,
        execution_input_closure_digest=ContentDigest(
            derive_workspace_materialize_execution_input_closure_digest(bodies)
        ),
    )
    _, evidence = f.publisher._publish_graph_v2(
        request=request, snapshot=f.snapshot, invocation=f.invocation,
        input_bodies=bodies,
    )
    return bodies, evidence


def test_original_publisher_retains_inputs_for_a_fresh_receiver(published_dependency, monkeypatch):
    f = published_dependency
    bodies, evidence = _retain(f)
    before = dict(f.body_store.bodies)
    receiver = WorkspaceSemanticMaterializationPublisher(
        state_store=f.store, body_store=f.body_store,
    )
    selected = receiver._read_graph_package_head_evidence(
        f.request.package.package_ref, observation_role="dependency_h1",
    )
    assert selected.head == evidence.head
    def refuse_execution(*args, **kwargs):
        raise AssertionError("input reread must not consult the original execution")

    monkeypatch.setattr(f.runtime, "execute", refuse_execution)
    monkeypatch.setattr(f.runtime, "snapshot_completion", refuse_execution)
    assert receiver._read_graph_input_bodies(selected.head) == bodies
    assert f.body_store.bodies == before


@pytest.mark.parametrize("poison", ("closure", "missing", "extra", "foreign_package"))
def test_original_publication_refuses_wrong_inputs_before_any_write(published_dependency, poison):
    f = published_dependency
    _, bodies = _invocation("a")
    request = _request(f.request, expected_head_revision=1,
        execution_input_closure_digest=ContentDigest(
            derive_workspace_materialize_execution_input_closure_digest(bodies)))
    invocation = f.invocation
    if poison == "closure":
        request = _request(request, execution_input_closure_digest=ContentDigest.of_bytes(b"other"))
    elif poison == "missing":
        bodies = ()
    elif poison == "extra":
        bodies = (*bodies, bodies[0])
    else:
        request = _request(request, package=replace(request.package, package_ref="package:foreign"))
    before = dict(f.body_store.bodies)
    with pytest.raises((WorkspaceSemanticMaterializationPublicationError, WorkspaceMaterializeOperationError)):
        f.publisher._publish_graph_v2(request=request, snapshot=f.snapshot,
            invocation=invocation, input_bodies=bodies)
    assert f.body_store.bodies == before


@pytest.mark.parametrize("poison", ("input_missing", "input_changed", "invocation_missing", "result_changed"))
def test_retained_input_reader_refuses_body_substitution(published_dependency, poison):
    f = published_dependency
    bodies, evidence = _retain(f)
    key = _body_ref({
        "input_missing": bodies[0].coordinate.digest.value,
        "input_changed": bodies[0].coordinate.digest.value,
        "invocation_missing": f.invocation.digest.value,
        "result_changed": f.snapshot.result_digest.value,
    }[poison])
    if poison.endswith("missing"):
        f.body_store.bodies.pop(key)
    else:
        f.body_store.bodies[key] = b"{}"
    before = dict(f.body_store.bodies)
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        f.publisher._read_graph_input_bodies(evidence.head)
    assert f.body_store.bodies == before


def test_issuer_delivers_inputs_under_exact_direct_pins(published_dependency):
    f = published_dependency
    bodies, _ = _retain(f)
    handle = issue(f)
    original = read(f, handle)
    rows = f.fulfillment.read_inputs(handle, f.resolution, f.expected)
    assert len(rows) == 2  # Two original demands, not flattened leaf demands.
    assert all(inputs == bodies for _, _, inputs in rows)
    assert all(parent.package == f.request.package for _, parent, _ in rows)
    assert read(f, handle) == original
    assert f.fulfillment.read_inputs(handle, f.resolution, f.expected) == rows


def test_input_refusal_terminally_retires_original_fulfillment(published_dependency):
    f = published_dependency
    bodies, _ = _retain(f)
    handle = issue(f)
    key = _body_ref(bodies[0].coordinate.digest.value)
    original = f.body_store.bodies.pop(key)
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        f.fulfillment.read_inputs(handle, f.resolution, f.expected)
    f.body_store.bodies[key] = original
    with pytest.raises(SourceObservationUnavailable, match="terminal"):
        f.fulfillment.read_inputs(handle, f.resolution, f.expected)


def test_input_reader_descriptor_substitution_refuses_without_foreign_call(published_dependency, monkeypatch):
    f = published_dependency
    _retain(f)
    handle = issue(f)
    calls = []

    def foreign(*args, **kwargs):
        calls.append(1)
        raise AssertionError("foreign reader called")

    monkeypatch.setattr(f.publisher, "_read_graph_v2_invocation", foreign)
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        f.fulfillment.read_inputs(handle, f.resolution, f.expected)
    assert not calls


def test_unretained_historical_input_does_not_gain_body_authority(published_dependency):
    f = published_dependency
    handle = issue(f)
    # Existing direct product reads still work; absent input retention is not
    # repaired from caller bytes and does not become an empty input closure.
    assert read(f, handle)
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        f.fulfillment.read_inputs(handle, f.resolution, f.expected)


def test_parent_head_movement_during_carriage_is_terminal(published_dependency):
    f = published_dependency
    _retain(f)
    handle = issue(f)
    calls = []

    def advance_during_inputs():
        calls.append(1)
        if len(calls) == 1:
            # Move during the original retained read chain, not before entry.
            f.body_store.after_read = advance_during_inputs
            return
        request = _request(f.request, expected_head_revision=2,
            source_identity_digest=ContentDigest.of_bytes(b"advanced-source"))
        f.publisher._publish_graph_v2(request=request,
            snapshot=f.snapshot, invocation=f.invocation)

    f.body_store.after_read = advance_during_inputs
    with pytest.raises(SourceObservationUnavailable, match="parent_head_changed"):
        f.fulfillment.read_inputs(handle, f.resolution, f.expected)
    assert len(calls) == 2
    assert f.fulfillment.records[handle].terminal


def test_v4_uses_the_same_original_input_retention_and_reader():
    from aware_local_service_runtime import InMemoryLocalOperationalStateStore
    from test_semantic_materialization_publication import (
        OPERATION_DIGEST,
        _existing_v4_successor_fixture,
        _occurrence,
    )

    (runtime, first_request, first_head, body_store, prior_state,
     request, invocation, snapshot, _) = _existing_v4_successor_fixture()
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        first_request.package.package_ref, expected_revision=0, value=first_head.to_wire())
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=body_store)
    _, bodies = _invocation("b")
    request = _request(request, execution_input_closure_digest=ContentDigest(
        derive_workspace_materialize_execution_input_closure_digest(bodies)))
    _, evidence = publisher._publish_graph_v4_existing_successor(
        request=request, snapshot=snapshot, invocation=invocation,
        package_occurrence=_occurrence(), expected_prior_head_digest=first_head.head_digest,
        prior_output_state=prior_state, operation_ref="materialize:sdk-2",
        operation_digest=OPERATION_DIGEST, output_role="output", input_bodies=bodies)
    assert publisher._read_graph_input_bodies(evidence.head.base_head) == bodies


def test_original_code_input_keeps_grandchild_beneath_its_parent_pin(published_dependency):
    """Real Code fixture execution, not native Meta or installed construction."""
    f = published_dependency
    _retain(f)
    handle = issue(f)
    value = decode_dependency_product_input(read(f, handle).canonical_body)
    codec = SemanticDependencyProductInputCodec()
    role = "z_dependencies"
    base = _profile()
    declaration = replace(base.providers[0], package_kinds=("fixture",), consumed_roles=(
        *base.providers[0].consumed_roles, ConsumedRoleDeclaration(role, (codec.contract,)),
    ))
    profile = replace(base, package_kinds=("fixture",), providers=(declaration,),
        inputs=(*base.inputs, ProfileInputDeclaration(role, codec.contract)),
        steps=(replace(base.steps[0], bindings=(
            *base.steps[0].bindings, RoleBinding(role, role),
        )),))

    class Provider(_Provider):
        @property
        def declaration(self):
            return declaration

    old = value.demand_set
    demand_set = SemanticDependencyDemandSet.create(
        package=value.package, intent=value.intent,
        profile_ref=profile.profile_ref, profile_digest=profile.digest,
        contract_profile_binding_digest=old.contract_profile_binding_digest,
        planner_implementation_ref=old.planner_implementation_ref,
        planner_implementation_digest=old.planner_implementation_digest,
        planner_configuration=SemanticConfigurationCoordinate(
            old.planner_configuration_ref, old.planner_configuration_digest),
        demands=old.demands,
    )
    value = replace(value, demand_set=demand_set)
    nested = dependency_product_input_body(value, role=role)
    invocation, source = _invocation("b")
    bodies = tuple(sorted((*source, nested),
        key=lambda item: canonical_json_bytes(item.coordinate.to_wire())))
    invocation = replace(invocation, target_package=value.package,
        profile_digest=profile.digest,
        inputs=tuple(body.coordinate for body in sorted(bodies, key=lambda item: item.coordinate.role)),
        dependencies=tuple(sorted({p.coordinate for p in value.products},
            key=lambda item: canonical_json_bytes(item.to_wire()))),
        body_codec_bindings=tuple(sorted((*invocation.body_codec_bindings,
            SemanticBodyCodecBinding(codec.contract, codec.implementation)),
            key=lambda item: canonical_json_bytes(item.contract.to_wire()))))
    runtime = SemanticContractRuntime(profile, {"test-provider": Provider()},
        {**{contract: _JsonCodec(contract) for contract in (SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT)},
         codec.contract: codec})
    completion = asyncio.run(runtime.execute(invocation, bodies))
    snapshot = runtime.snapshot_completion(completion)
    request = _request(f.request, package=value.package, expected_head_revision=0,
        result_coordinate=snapshot.result.transition.result,
        operation_result_digest=snapshot.result_digest,
        execution_input_closure_digest=ContentDigest(
            derive_workspace_materialize_execution_input_closure_digest(bodies)))
    _, evidence = f.publisher._publish_graph_v2(request=request,
        snapshot=snapshot, invocation=invocation, input_bodies=bodies)
    delivered = f.publisher._read_graph_input_bodies(evidence.head)
    retained = next(body for body in delivered if body.coordinate.contract == codec.contract)
    recovered = decode_dependency_product_input(retained.canonical_body)
    assert recovered == value
    assert tuple(p.body for p in recovered.products) == tuple(p.body for p in value.products)
    assert recovered.package == value.package
    assert all(p.coordinate.package == f.request.package for p in recovered.products)
    # The direct parent result is not rewritten to carry its own dependency
    # bodies, and the parent's inputs do not become the root's direct demands.
    assert snapshot.body_for(request.result_coordinate).canonical_body == b'{"sdk":"b"}'
