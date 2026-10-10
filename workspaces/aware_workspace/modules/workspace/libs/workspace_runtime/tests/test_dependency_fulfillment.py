"""Original publisher reads with explicit fixture resolution/source authority.

The Code runtime executes a neutral test provider and the real Workspace
publisher persists its result. Fixture resolution is not installed admission.
"""

import asyncio
import copy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticContractRuntime,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    decode_dependency_product_input,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyTarget,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
    _revoke_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    encode_code_semantic_contract_match_admission,
)
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from test_materialization_catalog import _binding, _catalog, _execution_closure
from test_semantic_materialization_publication import (
    EFFECT,
    OUTPUT,
    RESULT,
    SOURCE,
    TRANSITION,
    _BodyStore,
    _invocation,
    _JsonCodec,
    _profile,
    _Provider,
)

from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.dependency_fulfillment import (
    WorkspaceDependencyFulfillmentAdmission,
    _WorkspaceEmptyDependencyFulfillmentRuntime,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceSemanticMaterializationRequestV3,
    _body_ref,
)


@pytest.fixture
def published_dependency():
    profile = _profile()
    declaration = replace(profile.providers[0], package_kinds=("fixture",))
    profile = replace(
        profile,
        profile_ref="fixture.materialize",
        package_kinds=("fixture",),
        providers=(declaration,),
    )

    class Provider(_Provider):
        @property
        def declaration(self):
            return declaration

    runtime = SemanticContractRuntime(
        profile,
        {"test-provider": Provider()},
        {
            contract: _JsonCodec(contract)
            for contract in (SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT)
        },
    )
    invocation, source_bodies = _invocation("a")
    package = SemanticPackageCoordinate(
        "package:foundation", "fixture", ContentDigest.of_bytes(b"foundation-manifest")
    )
    invocation = replace(
        invocation,
        profile_ref=profile.profile_ref,
        profile_digest=profile.digest,
        target_package=package,
    )
    completion = asyncio.run(runtime.execute(invocation, source_bodies))
    assert runtime.owns_completion(completion)
    snapshot = runtime.snapshot_completion(completion)
    template = _binding()
    values = {
        field: getattr(template, field)
        for field in template.__dataclass_fields__
        if field != "binding_digest"
    }
    values.update(
        semantic_owner_key="fixture.owner",
        semantic_provider_key="test-provider",
        package_roles=("fixture",),
        manifest_contracts=(
            SemanticContractRef(
                "fixture.manifest", "1", ContentDigest.of_bytes(b"manifest-schema")
            ),
        ),
        profile_declaration=profile,
        provider_execution_bindings=invocation.provider_bindings,
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(role=role, contract=contract)
            for role, contract in (
                ("effect", EFFECT),
                ("output", OUTPUT),
                ("result", RESULT),
            )
        ),
    )
    binding = CodeSemanticMaterializationProfileBinding.create(**values)
    catalog = _catalog(binding)
    providers, planners = _execution_closure(catalog)
    admitted_catalog = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: True,
    )
    resolver = CodeSemanticContractCatalogResolver(admitted_catalog)
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("foundation.root",),
        requested_terminal_output_roles=("result",),
        semantic_configuration_coordinate=None,
    )
    context = CodeSemanticPackagePlanningContext.create(
        package=package,
        package_family="public",
        package_role="fixture",
        manifest_contract=binding.manifest_contracts[0],
        code_intent=intent,
        required_semantic_provider_keys=("test-provider",),
        required_result_products=(
            CodeSemanticRequiredResultProduct.create(role="result", contract=RESULT),
        ),
    )
    match, match_admission = resolver.resolve(context)
    wire = encode_code_semantic_contract_match_admission(
        match_admission, context=context, resolver=resolver
    )
    source_digest = ContentDigest.of_bytes(b"foundation-source")
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=package,
        result_coordinate=snapshot.result.transition.result,
        source_identity_digest=source_digest,
        code_intent_digest=intent.intent_digest,
        code_match_digest=match.match_digest,
        planning_input_digest=ContentDigest.of_bytes(b"planning"),
        execution_input_closure_digest=ContentDigest.of_bytes(b"closure"),
        operation_result_digest=snapshot.result_digest,
        expected_head_revision=0,
    )

    class BodyStore(_BodyStore):
        reads = 0
        after_read = None

        def read_body(self, body_ref):
            result = super().read_body(body_ref)
            self.reads += 1
            if self.after_read is not None:
                action, self.after_read = self.after_read, None
                action()
            return result

    class StateStore(InMemoryLocalOperationalStateStore):
        after_read = None

        def read(self, namespace, key):
            result = super().read(namespace, key)
            if self.after_read is not None:
                action, self.after_read = self.after_read, None
                action()
            return result

    store, body_store = StateStore(), BodyStore()
    publisher = WorkspaceSemanticMaterializationPublisher(
        state_store=store, body_store=body_store
    )
    publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    demands = tuple(
        SemanticDependencyDemand.create(
            consumer_semantic_role=role,
            authored_dependency_kind="module",
            authored_dependency_ref="foundation",
            target_constraints=(),
            required_result_role="result",
            result_product_contract=RESULT,
            target_intent=intent,
            cardinality="required",
        )
        for role in ("first", "second")
    )
    consumer = replace(package, package_ref="package:consumer")
    demand_set = SemanticDependencyDemandSet.create(
        package=consumer,
        intent=intent,
        profile_ref=profile.profile_ref,
        profile_digest=profile.digest,
        contract_profile_binding_digest=binding.binding_digest,
        planner_implementation_ref=binding.dependency_planner_implementation.implementation_ref,
        planner_implementation_digest=binding.dependency_planner_implementation.closure_digest,
        planner_configuration=binding.dependency_planner_configuration,
        demands=tuple(sorted(demands, key=lambda value: value.demand_digest.value)),
    )
    expected = SimpleNamespace(
        planning_input=SemanticDependencyPlanningInput(
            consumer,
            ContentDigest.of_bytes(b"consumer-source"),
            (
                SemanticAuthoredDependency(
                    "module",
                    "foundation",
                    (SemanticDependencyTarget(package, ("foundation.root",)),),
                ),
            ),
        ),
        demand_set=demand_set,
        planning_context=context,
    )
    resolution, target = object(), object()
    source = SimpleNamespace(
        membership=target,
        context=SimpleNamespace(package=package, source_identity_digest=source_digest),
    )

    class Resolutions:
        live = True

        def __init__(self):
            self.records = {
                resolution: SimpleNamespace(
                    operation=object(),
                    inventory=object(),
                    expected=expected,
                    targets=tuple(
                        (d.demand_digest, target, object(), context, wire)
                        for d in demand_set.demands
                    ),
                )
            }

        def validate(self, handle, value):
            if not self.live or handle is not resolution or value is not expected:
                raise SourceObservationUnavailable("fixture_resolution_unavailable")

        def _inventory(self, operation, inventory, value):
            self.validate(resolution, value)
            assert operation is self.records[resolution].operation
            assert inventory is self.records[resolution].inventory
            return SimpleNamespace(targets=(source,)), {}

        def close(self):
            self.live = False
            self.records.clear()

    resolutions = Resolutions()
    resolutions.resolver = resolver
    fulfillment = _WorkspaceEmptyDependencyFulfillmentRuntime(resolutions)
    yield SimpleNamespace(
        runtime=runtime,
        completion=completion,
        publisher=publisher,
        store=store,
        body_store=body_store,
        request=request,
        source=source,
        snapshot=snapshot,
        invocation=invocation,
        resolutions=resolutions,
        resolution=resolution,
        expected=expected,
        fulfillment=fulfillment,
    )
    fulfillment.close()
    _revoke_code_semantic_contract_catalog(admitted_catalog)


def issue(fixture):
    fixture.fulfillment.bind_publisher(fixture.publisher)
    return fixture.fulfillment.issue_products(fixture.resolution, fixture.expected)


def read(fixture, handle):
    return fixture.fulfillment.read(handle, fixture.resolution, fixture.expected)


def test_original_published_body_preserves_each_demand(published_dependency):
    f = published_dependency
    f.body_store.reads = 0
    handle = issue(f)
    assert f.body_store.reads == 1
    body = read(f, handle)
    assert f.body_store.reads == 2
    value = decode_dependency_product_input(body.canonical_body)
    assert tuple(p.demand_digest for p in value.products) == tuple(
        d.demand_digest for d in f.expected.demand_set.demands
    )
    assert len(value.products) == 2
    assert value.products[0].body == value.products[1].body
    assert value.products[0].body.coordinate == f.request.result_coordinate
    f.fulfillment.validate(
        handle,
        f.resolution,
        RetainedDependencyFulfillmentExpectation(f.expected, body.coordinate, value),
    )
    with pytest.raises(TypeError):
        copy.copy(handle)
    with pytest.raises(SourceObservationUnavailable, match="replay"):
        f.fulfillment.issue_products(f.resolution, f.expected)
    with pytest.raises(SourceObservationUnavailable, match="original_fulfillment"):
        _WorkspaceEmptyDependencyFulfillmentRuntime(f.resolutions).issue(
            f.resolution, f.expected
        )


@pytest.mark.parametrize(
    "fault", ["source", "role", "contract", "intent", "match", "package"]
)
def test_head_must_match_original_source_and_selected_context(
    published_dependency, fault
):
    f = published_dependency
    changes = {
        "source": {"source_identity_digest": ContentDigest.of_bytes(b"wrong-source")},
        "role": {
            "result_coordinate": replace(f.request.result_coordinate, role="wrong-role")
        },
        "contract": {
            "result_coordinate": replace(
                f.request.result_coordinate, contract=replace(RESULT, version="wrong")
            )
        },
        "intent": {"code_intent_digest": ContentDigest.of_bytes(b"wrong-intent")},
        "match": {"code_match_digest": ContentDigest.of_bytes(b"wrong-match")},
        "package": {
            "package": replace(
                f.request.package,
                manifest_digest=ContentDigest.of_bytes(b"wrong-manifest"),
            )
        },
    }[fault]
    from aware_workspace_runtime.semantic_materialization_publication import (
        WorkspaceSemanticMaterializationHeadV3,
    )

    changed = WorkspaceSemanticMaterializationRequestV3.create(
        **{
            name: changes.get(name, getattr(f.request, name))
            for name in f.request.__dataclass_fields__
            if name != "request_digest"
        }
    )
    head = WorkspaceSemanticMaterializationHeadV3.create(request=changed)
    record = f.store.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE, f.request.package.package_ref
    )
    f.store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        f.request.package.package_ref,
        expected_revision=record.revision,
        value=head.to_wire(),
    )
    with pytest.raises(SourceObservationUnavailable, match="correspondence"):
        issue(f)
    assert not f.fulfillment.records


@pytest.mark.parametrize(
    "fault", ["body", "source", "resolution", "resource", "reader", "head"]
)
def test_post_return_loss_retires_original_admission(published_dependency, fault):
    f = published_dependency
    handle = issue(f)
    original_body = f.body_store.bodies[
        _body_ref(f.request.result_coordinate.digest.value)
    ]
    old_resource = f.publisher._body_store
    old_read = f.publisher._read_graph_v2_body
    if fault == "body":
        f.body_store.bodies[_body_ref(f.request.result_coordinate.digest.value)] = (
            b"poison"
        )
    elif fault == "source":
        f.source.context.source_identity_digest = ContentDigest.of_bytes(b"changed")
    elif fault == "resolution":
        f.resolutions.live = False
    elif fault == "resource":
        f.publisher._body_store = _BodyStore()
    elif fault == "reader":
        f.publisher._read_graph_v2_body = lambda coordinate: None
    else:
        record = f.store.read(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
        )
        f.store.compare_and_set(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
            expected_revision=record.revision,
            value=record.value,
        )
    with pytest.raises((SourceObservationUnavailable, RuntimeError)):
        read(f, handle)
    retained = f.fulfillment.records[handle]
    assert retained.terminal and retained.body is None and retained.heads == ()
    f.body_store.bodies[_body_ref(f.request.result_coordinate.digest.value)] = (
        original_body
    )
    f.source.context.source_identity_digest = f.request.source_identity_digest
    f.resolutions.live = True
    f.publisher._body_store = old_resource
    if fault == "reader":
        del f.publisher._read_graph_v2_body
        assert f.publisher._read_graph_v2_body == old_read
    with pytest.raises(SourceObservationUnavailable, match="terminal"):
        read(f, handle)


def test_foreign_publisher_is_rejected_without_behavior(published_dependency):
    class Foreign:
        calls = 0

        def __getattribute__(self, name):
            type(self).calls += 1
            raise AssertionError(name)

    with pytest.raises(
        SourceObservationUnavailable, match="original_dependency_publisher"
    ):
        published_dependency.fulfillment.bind_publisher(Foreign())
    assert Foreign.calls == 0


def test_no_bound_publisher_and_terminal_close_refuse(published_dependency):
    f = published_dependency
    with pytest.raises(SourceObservationUnavailable, match="publisher_unavailable"):
        f.fulfillment.issue_products(f.resolution, f.expected)
    assert not f.fulfillment.records
    f.fulfillment.close()
    with pytest.raises(SourceObservationUnavailable, match="lifetime"):
        f.fulfillment.bind_publisher(f.publisher)
    # The fulfillment borrows these resources; closing it must not dispose them.
    assert f.publisher._read_graph_v2_body(f.request.result_coordinate).coordinate == (
        f.request.result_coordinate
    )


@pytest.mark.parametrize("fault", ["missing_head", "body_capacity", "target_capacity"])
def test_unavailable_or_over_bound_results_refuse_before_body_read(
    published_dependency, fault
):
    from aware_workspace_runtime.semantic_materialization_publication import (
        WorkspaceSemanticMaterializationHeadV3,
    )

    f = published_dependency
    if fault == "target_capacity":
        record = f.resolutions.records[f.resolution]
        record.targets = (record.targets[0],) * 129
    elif fault == "missing_head":
        f.publisher = WorkspaceSemanticMaterializationPublisher(
            state_store=InMemoryLocalOperationalStateStore(), body_store=f.body_store
        )
    else:
        coordinate = replace(
            f.request.result_coordinate, size_bytes=8 * 1024 * 1024 + 1
        )
        request = WorkspaceSemanticMaterializationRequestV3.create(
            **{
                name: coordinate
                if name == "result_coordinate"
                else getattr(f.request, name)
                for name in f.request.__dataclass_fields__
                if name != "request_digest"
            }
        )
        record = f.store.read(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
        )
        f.store.compare_and_set(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
            expected_revision=record.revision,
            value=WorkspaceSemanticMaterializationHeadV3.create(
                request=request
            ).to_wire(),
        )
    before = f.body_store.reads
    with pytest.raises(SourceObservationUnavailable):
        issue(f)
    assert f.body_store.reads == before
    assert not f.fulfillment.records
    with pytest.raises(SourceObservationUnavailable, match="replay"):
        f.fulfillment.issue_products(f.resolution, f.expected)


def test_foreign_handle_does_not_retire_original_family(published_dependency):
    f = published_dependency
    handle = issue(f)
    with pytest.raises(SourceObservationUnavailable, match="foreign"):
        read(f, object())
    assert not f.fulfillment.records[handle].terminal
    assert read(f, handle).coordinate.role == "semantic_dependencies"


def test_registered_handle_restamping_is_terminal_without_behavior(
    published_dependency,
):
    f = published_dependency
    handle = issue(f)

    class Restamped:
        __slots__ = ()
        calls = 0

        def __hash__(self):
            type(self).calls += 1
            raise AssertionError("foreign hash")

    object.__setattr__(handle, "__class__", Restamped)
    with pytest.raises(SourceObservationUnavailable, match="terminal"):
        read(f, handle)
    assert Restamped.calls == 0
    object.__setattr__(handle, "__class__", WorkspaceDependencyFulfillmentAdmission)
    with pytest.raises(SourceObservationUnavailable, match="terminal"):
        read(f, handle)


def test_fixed_composition_refuses_unknown_host_before_reader_calls(
    published_dependency,
):
    f = published_dependency
    with pytest.raises(RuntimeError, match="original fixed host"):
        composition._compose_direct_workspace_dependency_product_issuer(
            object(),
            object(),
            publisher=f.publisher,
        )


def test_head_movement_during_body_read_refuses_before_issuance(published_dependency):
    f = published_dependency

    def move():
        record = f.store.read(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
        )
        f.store.compare_and_set(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            f.request.package.package_ref,
            expected_revision=record.revision,
            value=record.value,
        )

    f.body_store.after_read = move
    with pytest.raises(SourceObservationUnavailable, match="head_changed"):
        issue(f)
    assert not f.fulfillment.records
    with pytest.raises(SourceObservationUnavailable, match="replay"):
        f.fulfillment.issue_products(f.resolution, f.expected)


def test_nested_reader_substitution_refuses_without_call(published_dependency):
    f = published_dependency
    handle = issue(f)
    calls = []
    f.publisher._read_graph_v2_head = lambda *args, **kwargs: calls.append("foreign")
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        read(f, handle)
    assert calls == []


@pytest.mark.parametrize("phase", ["issuance", "validation"])
@pytest.mark.parametrize("io_boundary", ["state", "body"])
@pytest.mark.parametrize("behavior", ["returning", "raising", "transient_restoration"])
@pytest.mark.parametrize(
    "binding",
    [
        "nested_head_reader",
        "state_reader",
        "both_readers",
        "body_reader",
        "v4_evidence",
        "v4_head",
        "v4_state",
        "dispatcher",
        "binding_guard",
        "lifetime_guard",
    ],
)
def test_nested_dispatch_poison_never_runs_and_cannot_resume(
    published_dependency, phase, io_boundary, behavior, binding
):
    f = published_dependency
    if phase == "validation":
        handle = issue(f)
        body = read(f, handle)
        expectation = RetainedDependencyFulfillmentExpectation(
            f.expected,
            body.coordinate,
            decode_dependency_product_input(body.canonical_body),
        )
    else:
        f.fulfillment.bind_publisher(f.publisher)
    entries = {
        "nested_head_reader": ((f.publisher, "_read_graph_v2_head"),),
        "state_reader": ((f.store, "read"),),
        "both_readers": ((f.publisher, "_read_graph_v2_head"), (f.store, "read")),
        "body_reader": ((f.body_store, "read_body"),),
        "v4_evidence": ((f.publisher, "_read_graph_v4_head_evidence"),),
        "v4_head": ((f.publisher, "_read_graph_v4_head"),),
        "v4_state": ((f.publisher, "_read_graph_v4_output_state"),),
        "dispatcher": ((f.fulfillment, "_call_publisher"),),
        "binding_guard": ((f.fulfillment, "_check_publisher"),),
        "lifetime_guard": ((f.fulfillment, "_check_live"),),
    }[binding]
    calls = []

    def install():
        for receiver, name in entries:
            original = getattr(receiver, name)

            def hostile(
                *args, receiver=receiver, name=name, original=original, **kwargs
            ):
                calls.append(name)
                if behavior == "raising":
                    raise AssertionError("hostile reader ran")
                if behavior == "transient_restoration":
                    delattr(receiver, name)
                return original(*args, **kwargs)

            setattr(receiver, name, hostile)

    # Replace nested dispatch during an original store read, after authentication.
    if io_boundary == "state":
        f.store.after_read = install
    else:
        f.body_store.after_read = install
    before_bodies = f.body_store.reads
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        if phase == "issuance":
            f.fulfillment.issue_products(f.resolution, f.expected)
        else:
            f.fulfillment.validate(handle, f.resolution, expectation)
    assert calls == []
    assert f.body_store.reads == before_bodies + (io_boundary == "body")
    for receiver, name in entries:
        delattr(receiver, name)
    if phase == "issuance":
        assert not f.fulfillment.records
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            f.fulfillment.issue_products(f.resolution, f.expected)
    else:
        record = f.fulfillment.records[handle]
        assert record.terminal and record.body is None and record.heads == ()
        with pytest.raises(SourceObservationUnavailable, match="terminal"):
            read(f, handle)


@pytest.mark.parametrize("phase", ["issuance", "reread", "validation"])
@pytest.mark.parametrize("behavior", ["returning", "raising", "transient_restoration"])
@pytest.mark.parametrize("guard", ["_check_live", "_check_publisher"])
def test_pre_entry_guard_substitution_never_runs_and_cannot_resume(
    published_dependency, phase, behavior, guard
):
    f = published_dependency
    if phase == "issuance":
        f.fulfillment.bind_publisher(f.publisher)
    else:
        handle = issue(f)
        body = read(f, handle)
        expected = RetainedDependencyFulfillmentExpectation(
            f.expected,
            body.coordinate,
            decode_dependency_product_input(body.canonical_body),
        )
    calls = []
    original = getattr(f.fulfillment, guard)

    def hostile():
        calls.append(guard)
        if behavior == "raising":
            raise AssertionError("hostile entry guard ran")
        if behavior == "transient_restoration":
            delattr(f.fulfillment, guard)
        return original()

    setattr(f.fulfillment, guard, hostile)
    before = f.body_store.reads
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        if phase == "issuance":
            f.fulfillment.issue_products(f.resolution, f.expected)
        elif phase == "reread":
            read(f, handle)
        else:
            f.fulfillment.validate(handle, f.resolution, expected)
    assert calls == []
    assert f.body_store.reads == before
    delattr(f.fulfillment, guard)
    if phase == "issuance":
        assert not f.fulfillment.records
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            f.fulfillment.issue_products(f.resolution, f.expected)
    else:
        record = f.fulfillment.records[handle]
        assert record.terminal and record.body is None and record.heads == ()
        with pytest.raises(SourceObservationUnavailable, match="terminal"):
            read(f, handle)
    assert f.body_store.reads == before


def test_foreign_resolution_entry_rejection_does_not_spend_original(
    published_dependency,
):
    f = published_dependency
    f.fulfillment.bind_publisher(f.publisher)
    calls = []
    f.fulfillment._check_live = lambda: calls.append("foreign")
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        f.fulfillment.issue_products(object(), f.expected)
    assert not f.fulfillment.issued and calls == []
    del f.fulfillment._check_live
    handle = f.fulfillment.issue_products(f.resolution, f.expected)
    assert read(f, handle).coordinate.role == "semantic_dependencies"


def _use_v4_read_fixture(f):
    """Codec/read fixture, not an installed output-state publication admission."""
    from test_semantic_materialization_publication import _state_bound_head_fixture

    from aware_workspace_runtime.semantic_materialization_publication import (
        WorkspaceSemanticMaterializationHeadV4,
    )

    _, _, prototype, bodies, _, _, _, _ = _state_bound_head_fixture()
    record = f.store.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE, f.request.package.package_ref
    )
    request = WorkspaceSemanticMaterializationRequestV3.create(
        **{
            name: record.revision
            if name == "expected_head_revision"
            else getattr(f.request, name)
            for name in f.request.__dataclass_fields__
            if name != "request_digest"
        }
    )
    old = f.publisher._read_graph_v2_head(
        f.request.package.package_ref, observation_role="dependency_h1"
    )
    head = WorkspaceSemanticMaterializationHeadV4.create(
        request=request,
        package_occurrence=prototype.package_occurrence,
        predecessor_head_digest=old.head.head_digest,
        operation_ref=prototype.operation_ref,
        operation_digest=prototype.operation_digest,
        output_state_bindings=prototype.output_state_bindings,
    )
    f.body_store.bodies.update(bodies.bodies)
    f.store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        f.request.package.package_ref,
        expected_revision=record.revision,
        value=head.to_wire(),
    )


def test_retained_v4_reader_chain_preserves_detached_products(published_dependency):
    f = published_dependency
    _use_v4_read_fixture(f)
    handle = issue(f)
    body = read(f, handle)
    value = decode_dependency_product_input(body.canonical_body)
    assert len(value.products) == 2
    assert all(p.body.coordinate == f.request.result_coordinate for p in value.products)


@pytest.mark.parametrize("phase", ["issuance", "validation"])
@pytest.mark.parametrize("behavior", ["returning", "raising", "transient_restoration"])
@pytest.mark.parametrize("step", ["after_prior", "after_state"])
def test_v4_nested_body_reader_poison_is_terminal(
    published_dependency, phase, behavior, step
):
    f = published_dependency
    _use_v4_read_fixture(f)
    if phase == "validation":
        handle = issue(f)
        body = read(f, handle)
        expectation = RetainedDependencyFulfillmentExpectation(
            f.expected,
            body.coordinate,
            decode_dependency_product_input(body.canonical_body),
        )
    else:
        f.fulfillment.bind_publisher(f.publisher)
    calls = []
    original = f.publisher._read_graph_v2_body
    before_bodies = f.body_store.reads
    target = before_bodies + (1 if step == "after_prior" else 2)

    def hostile(*args, **kwargs):
        calls.append("delta_reader")
        if behavior == "raising":
            raise AssertionError("hostile delta reader ran")
        if behavior == "transient_restoration":
            del f.publisher._read_graph_v2_body
        return original(*args, **kwargs)

    def after_body():
        if f.body_store.reads == target:
            f.publisher._read_graph_v2_body = hostile
        else:
            f.body_store.after_read = after_body

    f.body_store.after_read = after_body
    with pytest.raises(SourceObservationUnavailable, match="reader_substituted"):
        if phase == "issuance":
            f.fulfillment.issue_products(f.resolution, f.expected)
        else:
            f.fulfillment.validate(handle, f.resolution, expectation)
    assert calls == []
    assert f.body_store.reads == target
    del f.publisher._read_graph_v2_body
    if phase == "issuance":
        assert not f.fulfillment.records
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            f.fulfillment.issue_products(f.resolution, f.expected)
    else:
        assert f.fulfillment.records[handle].terminal
        assert f.fulfillment.records[handle].body is None
        with pytest.raises(SourceObservationUnavailable, match="terminal"):
            read(f, handle)


@pytest.mark.parametrize("boundary", ["thread", "process"])
def test_cross_boundary_refusal_releases_original_body(published_dependency, boundary):
    from concurrent.futures import ThreadPoolExecutor

    f = published_dependency
    handle = issue(f)
    before = f.body_store.reads
    if boundary == "thread":
        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            pytest.raises(SourceObservationUnavailable, match="lifetime"),
        ):
            pool.submit(read, f, handle).result()
    else:
        f.fulfillment._pid -= 1
        with pytest.raises(SourceObservationUnavailable, match="lifetime"):
            read(f, handle)
    assert f.body_store.reads == before
    assert f.fulfillment.records[handle].terminal


def test_changed_fulfillment_expectation_is_terminal(published_dependency):
    f = published_dependency
    handle = issue(f)
    body = read(f, handle)
    value = decode_dependency_product_input(body.canonical_body)
    expected = RetainedDependencyFulfillmentExpectation(
        f.expected, replace(body.coordinate, value_ref="wrong"), value
    )
    with pytest.raises(SourceObservationUnavailable, match="correspondence"):
        f.fulfillment.validate(handle, f.resolution, expected)
    with pytest.raises(SourceObservationUnavailable, match="terminal"):
        read(f, handle)


@pytest.mark.parametrize("mutate", [False, True])
@pytest.mark.asyncio
async def test_original_workspace_source_brackets_published_products(
    tmp_path,
    published_dependency,
    mutate,
):
    """Original source and publisher; Code demand validation stays fixture grade."""
    from test_declaration_scope_admission import fixture
    from test_materialization_declaration_selection import _selection
    from test_v3_dependency_issuer import _author_imported_target
    from test_v3_source_admission import _expected, _Validator

    from aware_workspace_runtime.declaration_scope_admission import (
        WorkspaceDeclarationInventoryAdmission,
    )

    f = published_dependency
    async with fixture(tmp_path) as (root, _, borrowed, _, _, _):
        _author_imported_target(root)
        module = root / "workspaces/kernel/modules/main/aware.module.toml"
        module.write_text(
            module.read_text().replace('kind="example"', 'kind="fixture"')
        )
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("package", "network-example")
            ) as selected_roots:
                selected = selected_roots[0][1]
                source_context = object()
                source_expectation = replace(
                    _expected(issuer, selected), stage="source_planning"
                )
                issuer._bind_original_code_validator(
                    _Validator(source_context, source_expectation)
                )
                _, inventory = issuer.issue_source_planning_pair(
                    selected, context=source_context, expected=source_expectation
                )
                original = issuer._semantic[inventory]
                target = original.targets[0]
                authored = original.inventory.entries[0]
                old_context = f.resolutions.records[f.resolution].targets[0][3]
                intent = CodeSemanticMaterializationIntent.create(
                    operation_kind="materialize",
                    requested_semantic_root_refs=authored.targets[0].semantic_root_refs,
                    requested_terminal_output_roles=("result",),
                    semantic_configuration_coordinate=None,
                )
                context = CodeSemanticPackagePlanningContext.create(
                    package=target.context.package,
                    package_family=old_context.package_family,
                    package_role=old_context.package_role,
                    manifest_contract=old_context.manifest_contract,
                    code_intent=intent,
                    required_result_products=old_context.required_result_products,
                    required_semantic_provider_keys=old_context.required_semantic_provider_keys,
                )
                match, match_admission = f.resolutions.resolver.resolve(context)
                wire = encode_code_semantic_contract_match_admission(
                    match_admission, context=context, resolver=f.resolutions.resolver
                )
                invocation = replace(
                    f.invocation,
                    invocation_ref="original-target",
                    idempotency_key="original-target",
                    target_package=context.package,
                )
                _, source_bodies = _invocation("a")
                # Existing runtime performs one additional genuine test-provider call.
                completion = await f.runtime.execute(invocation, source_bodies)
                snapshot = f.runtime.snapshot_completion(completion)
                request = WorkspaceSemanticMaterializationRequestV3.create(
                    package=context.package,
                    result_coordinate=snapshot.result.transition.result,
                    source_identity_digest=target.context.source_identity_digest,
                    code_intent_digest=context.code_intent.intent_digest,
                    code_match_digest=match.match_digest,
                    planning_input_digest=f.request.planning_input_digest,
                    execution_input_closure_digest=f.request.execution_input_closure_digest,
                    operation_result_digest=snapshot.result_digest,
                    expected_head_revision=0,
                )
                f.publisher._publish_graph_v2(
                    request=request, snapshot=snapshot, invocation=invocation
                )
                resolution_record = f.resolutions.records[f.resolution]
                old_demands = f.expected.demand_set
                demands = tuple(
                    SemanticDependencyDemand.create(
                        consumer_semantic_role=role,
                        authored_dependency_kind=authored.dependency_kind,
                        authored_dependency_ref=authored.dependency_ref,
                        target_constraints=authored.target_constraints,
                        required_result_role="result",
                        result_product_contract=RESULT,
                        target_intent=intent,
                        cardinality="required",
                    )
                    for role in ("first", "second")
                )
                f.expected.planning_input = SemanticDependencyPlanningInput(
                    original.context.package,
                    original.context.source_identity_digest,
                    (
                        SemanticAuthoredDependency(
                            authored.dependency_kind,
                            authored.dependency_ref,
                            authored.targets,
                            authored.target_constraints,
                        ),
                    ),
                )
                f.expected.demand_set = SemanticDependencyDemandSet.create(
                    package=original.context.package,
                    intent=intent,
                    profile_ref=old_demands.profile_ref,
                    profile_digest=old_demands.profile_digest,
                    contract_profile_binding_digest=old_demands.contract_profile_binding_digest,
                    planner_implementation_ref=old_demands.planner_implementation_ref,
                    planner_implementation_digest=old_demands.planner_implementation_digest,
                    planner_configuration=SemanticConfigurationCoordinate(
                        old_demands.planner_configuration_ref,
                        old_demands.planner_configuration_digest,
                    ),
                    demands=tuple(sorted(demands, key=lambda d: d.demand_digest.value)),
                )
                f.expected.planning_context = context
                resolution_record.targets = tuple(
                    (d.demand_digest, target.membership, object(), context, wire)
                    for d in f.expected.demand_set.demands
                )
                original_inventory = f.resolutions._inventory

                def validated_inventory(operation, admission, expected):
                    original_inventory(operation, admission, expected)
                    result = issuer._validate_semantic_admission(
                        inventory,
                        expected=source_expectation,
                        kind=WorkspaceDeclarationInventoryAdmission,
                    )
                    return result, {}

                f.resolutions._inventory = validated_inventory
                issuer._dependency_resolution = f.resolutions
                issuer._dependency_fulfillment = f.fulfillment
                issuer._bind_original_dependency_product_publisher(f.publisher)
                handle = issuer.issue_dependency_fulfillment(
                    f.resolution, expected=f.expected
                )
                body = issuer.read_dependency_products(
                    handle, resolution_admission=f.resolution, expected=f.expected
                )
                value = decode_dependency_product_input(body.canonical_body)
                assert all(
                    p.coordinate.package == target.context.package
                    for p in value.products
                )
                if mutate:
                    target_path = (
                        root / "workspaces/kernel/modules/main/package/body.bin"
                    )
                    before_reads = f.body_store.reads
                    target_path.write_bytes(b"changed after original fulfillment")
                    with pytest.raises(SourceObservationUnavailable):
                        issuer.read_dependency_products(
                            handle,
                            resolution_admission=f.resolution,
                            expected=f.expected,
                        )
                    assert f.body_store.reads == before_reads
                    assert f.fulfillment.records[handle].terminal
        assert f.fulfillment.publisher is None
        assert not f.fulfillment.records
