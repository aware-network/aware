"""Original host/product/node lifecycle mechanics with an isolated owner."""

import os
from dataclasses import fields, replace

import pytest
import pytest_asyncio
from aware_code_retained_registry_policy_runtime import direct_host, product_execution
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from test_dependency_operation_validator import (
    case as dependency_case,  # noqa: F401 - pytest fixture import
)
from test_direct_epoch_tracking import Owner, clearance
from test_product_runtime_retention import _case


class NodeOwner(Owner):
    def __init__(self):
        super().__init__(None)
        self.node = object()
        self.node_live = True
        self.node_checks = 0

    def validate_selected_graph_node_use(self, source, *, closure=None):
        if self.guards:
            raise ContractViolation("source read under parent exclusion")
        if source is not self.node or not self.node_live:
            raise ContractViolation("original graph-node source unavailable")
        self.node_checks += 1

    def check_selected_graph_node_use_locked(self, source):
        if not self.guards or source is not self.node or not self.node_live:
            raise ContractViolation("original locked graph-node use unavailable")


def setup():
    base, _, _, live = _case()
    owner = NodeOwner()
    resources = tuple(
        replace(item, resource=(
            calculate_registry_policy if item.role == "policy_producer" else owner
        ))
        if item.role in {
            "composition_factory", "lifetime_runtime", "scope_adapter",
            "policy_producer",
        }
        else item
        for item in base.resources
    )
    expected = replace(base, resources=resources)
    owner.expected = expected
    bootstrap = direct_host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=expected
    )
    host = direct_host.register_direct_workspace_origin(bootstrap, owner.lifetime)
    invocation = DirectInvocationExpectation(
        expected.invocation_identity, expected.epoch_identity, os.getpid()
    )
    digest = ContentDigest.of_bytes(b"graph-product-node-membership")
    owner.epoch = CatalogPairEpochExpectation(
        invocation, object(), direct_host._HOSTS[host].catalog_digest, digest, digest
    )
    owner.successor = CatalogPublicationExpectation(
        object(), owner.epoch,
        replace(owner.epoch, publication_identity=object()), digest,
    )
    guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=invocation)
    try:
        tracker = epochs._assemble_code_epoch_participation(
            owner=owner, parent=owner.parent, invocation=invocation,
            epoch_owner=owner, guard=guard,
        )
        _bind_direct_policy_epoch(
            host, tracker, owner.current, expected=owner.epoch, guard=guard
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    registration = expected.product_runtime_bindings[0].registration
    return owner, host, registration, tracker, live


def test_product_node_use_blocks_successor_and_refuses_replay():
    owner, host, registration, tracker, _ = setup()
    origin = product_execution.bind_product_execution_origin(host, registration)
    stage = origin.adopt(owner.node)
    origin.validate(stage, None)
    assert owner.node_checks >= 2
    with pytest.raises(ContractViolation, match="runtime-owned"):
        origin.complete(stage, object())
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)
    with pytest.raises(ContractViolation, match="replay"):
        origin.adopt(owner.node)
    origin.fail(stage)
    with pytest.raises(ContractViolation, match="running"):
        origin.validate(stage, None)
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)
    direct_host.close_direct_validation_host(host)


def test_source_and_catalog_revocation_reject_before_selected_use():
    owner, host, registration, _tracker, live = setup()
    origin = product_execution.bind_product_execution_origin(host, registration)
    owner.node_live = False
    with pytest.raises(ContractViolation, match="source unavailable"):
        origin.adopt(owner.node)
    owner.node_live = True
    live[0] = False
    with pytest.raises(ContractViolation):
        origin.adopt(owner.node)
    direct_host.close_direct_validation_host(host)


def test_factory_substitution_and_foreign_registration_refuse():
    owner, host, registration, _tracker, _ = setup()
    with pytest.raises((ContractViolation, TypeError)):
        product_execution.bind_product_execution_origin(host, object())
    owner.check_selected_graph_node_use_locked = lambda source: None
    with pytest.raises(ContractViolation, match="entrance"):
        product_execution.bind_product_execution_origin(host, registration)
    direct_host.close_direct_validation_host(host)


def test_selected_admission_failure_retains_uncertain_node_use():
    owner, host, registration, tracker, _ = setup()
    product_execution.bind_product_execution_origin(host, registration)
    runtime = selected._registration_state(registration).runtime
    with pytest.raises(AssertionError, match="closure invocation"):
        selected.issue_selected_provider_execution(
            runtime, registration, object(), operation_context=owner.node
        )
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)
    direct_host.close_direct_validation_host(host)


class ReadNode:
    pass


class ReadOwner(NodeOwner):
    def __init__(self):
        super().__init__()
        self.node = ReadNode()
        self.assembly = None
        self.on_full = None
        self.read_calls = 0

    def validate_selected_input_node_use(self, source, *, assembly=None, closure=None):
        from aware_code_semantic_contract_runtime.semantic_input_producer import (
            validate_registered_semantic_input_result,
        )
        if self.guards or source is not self.node or not self.node_live:
            raise ContractViolation("original selected read source unavailable")
        if assembly is not self.assembly:
            raise ContractViolation("original prepared assembly differs")
        self.read_calls += 1
        for original in assembly.source_results:
            validate_registered_semantic_input_result(
                original.host, original.registration,
                source_admission=original.source_admission,
                expected=original.expected, result=original.result)
        if self.on_full is not None:
            self.on_full()

    def check_selected_input_node_use_locked(self, source):
        if not self.guards or source is not self.node or not self.node_live:
            raise ContractViolation("original locked selected read unavailable")


@pytest_asyncio.fixture
async def read_host(monkeypatch):
    import test_product_runtime_retention as retention_fixtures
    from aware_code_semantic_contract_runtime import (
        ProviderDerivation,
        SemanticBody,
        SemanticBodyCodecBinding,
        SemanticValueCoordinate,
        TypedEmptyCoordinate,
    )
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as delivery,
    )
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputProducerHost,
        execute_registered_semantic_input,
        register_semantic_input_producer,
    )
    from test_contracts import (
        EFFECT_BODY,
        OUTPUT_BODY,
        RESULT_BODY,
        SOURCE_BODY,
        TRANSITION_BODY,
        body_coordinate,
        delta_result,
        invocation,
    )
    from test_semantic_input_producer import (
        _DECLARATION,
        _expectation,
        _SourceValidator,
    )

    class Provider(retention_fixtures._SelectedProvider):
        def __init__(self):
            self.calls = 0
            self.uses = []
            self.on_execute = None

        def observe(self, event, use):
            if event == "associated":
                self.uses.append(use)

        def input_closure(self, value):
            return selected.SelectedProviderInvocationClosure(*value)

        def execute(self, step, value):
            self.calls += 1
            delivery.validate_selected_invocation_inputs(self.uses[-1], self)
            if self.on_execute is not None:
                self.on_execute()
            declared = self.declaration
            raw = delta_result(step.invocation, step.input_closure_digest)
            candidate = body_coordinate("result", declared.result_role.contract, "read-result", RESULT_BODY)
            transition = replace(raw.transition, provider_key=declared.provider_key,
                result_contract=declared.result_role.contract,
                transition_contract=declared.transition_contract, result=candidate,
                transition_body=body_coordinate("transition-body", declared.transition_contract,
                                               "read-transition", TRANSITION_BODY))
            effect = replace(raw.effect, provider_key=declared.provider_key,
                effect_contract=declared.effect_contract, transition_digest=transition.digest,
                candidate_state=candidate,
                effect_body=body_coordinate("effect", declared.effect_contract, "read-effect", EFFECT_BODY))
            output = replace(raw.outputs[0], provider_key=declared.provider_key,
                output=body_coordinate("python_sdk", declared.output_roles[0].contract,
                                       "read-output", OUTPUT_BODY), prepared_effect_digest=effect.digest)
            result = replace(raw, transition=transition, effect=effect, outputs=(output,))
            bodies = tuple(sorted((SemanticBody(candidate, RESULT_BODY),
                SemanticBody(transition.transition_body, TRANSITION_BODY),
                SemanticBody(effect.effect_body, EFFECT_BODY),
                SemanticBody(output.output, OUTPUT_BODY)), key=lambda body: body.coordinate.role))
            return ProviderDerivation(result, bodies)

    original_binding = retention_fixtures._binding

    def binding(**kwargs):
        entry = original_binding(**kwargs)
        profile = replace(entry.profile_declaration,
            providers=(replace(entry.profile_declaration.providers[0],
                               allows_typed_empty=True, counter_keys=("movements",)),))
        values = {field.name: getattr(entry, field.name)
                  for field in fields(entry) if field.name != "binding_digest"}
        values["profile_declaration"] = profile
        return type(entry).create(**values)

    monkeypatch.setattr(retention_fixtures, "_binding", binding)
    original_factory_issuer = selected._admit_selected_provider_factory

    def issue_factory(**kwargs):
        original = kwargs["selection_factory"]
        def factory():
            value = original()
            return replace(value, selected_invocation_observer=value.provider.observe)
        return original_factory_issuer(**{**kwargs, "selection_factory": factory})

    monkeypatch.setattr(retention_fixtures, "_SelectedProvider", Provider)
    monkeypatch.setattr(selected, "_admit_selected_provider_factory", issue_factory)
    monkeypatch.setattr(__import__(__name__), "NodeOwner", ReadOwner)
    owner, host, registration, tracker, _live = setup()
    state = selected._registration_state(registration)
    runtime, provider = state.runtime, state.provider
    body = SemanticBody(SemanticValueCoordinate("source", runtime.profile.inputs[0].contract,
                        "original-source", ContentDigest.of_bytes(SOURCE_BODY), len(SOURCE_BODY)), SOURCE_BODY)
    call = replace(invocation(), profile_ref=runtime.profile.profile_ref,
                   profile_digest=runtime.profile.digest, inputs=(body.coordinate,),
                   predecessor=TypedEmptyCoordinate(provider.declaration.result_role.contract),
                   provider_bindings=(direct_host._HOSTS[host].catalog_resolver.catalog.entries[0].provider_execution_bindings[0],), requested_output_roles=("python_sdk",),
                   body_codec_bindings=tuple(sorted((SemanticBodyCodecBinding(contract, codec.implementation)
                        for contract, codec in runtime._body_codecs.items()), key=lambda item: item.contract.key)))
    value = (call, (body,))
    source_host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    expected = _expectation(operation, source)
    declaration = replace(_DECLARATION, result_role="source", result_contract=body.coordinate.contract)
    async def produce(value):
        return body
    source_registration = register_semantic_input_producer(
        source_host, declaration=declaration, producer=produce, validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator, reader_entrance=validator.read_semantic_input_sources,
        retain_result=True)
    returned = await execute_registered_semantic_input(source_host, source_registration,
                                                       source_admission=source, expected=expected)
    source_result = delivery.SelectedInputSourceResult(source_host, source_registration,
                                                       source, expected, returned)
    assembly = delivery.SelectedInputVerificationAssembly(value, value[1], (source_result,),
                                                          source_input_roles=(("source", 0),))
    owner.assembly = assembly
    origin = product_execution.bind_selected_input_verification_origin(host, registration)
    try:
        yield owner, host, registration, origin, assembly, provider, validator, tracker
    finally:
        direct_host.close_direct_validation_host(host)
        for admission, execution in tuple(selected._EXECUTIONS.values()):
            if execution.registration is registration and execution.lifecycle == "active":
                selected._abort_selected_provider_execution(runtime, admission)
        if not state.closed:
            selected.close_selected_provider_registration(runtime, registration)
        source_host.close()


def prepare_read(case):
    owner, host, registration, _, assembly, _, _, _ = case
    product_execution.prepare_selected_input_verification(host, owner.node, registration, assembly=assembly)


def execute_read(case):
    owner, _, registration, _, assembly, provider, _, _ = case
    runtime = selected._registration_state(registration).runtime
    admission = selected.issue_selected_provider_execution(
        runtime, registration, assembly.semantic_input, operation_context=owner.node)
    completion = selected.execute_selected_provider(runtime, admission)
    return completion, provider.uses[-1]


@pytest.mark.asyncio
async def test_original_read_inputs_verify_after_real_selected_completion(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        release_selected_invocation_input_verification,
        validate_selected_invocation_inputs,
    )
    owner, _, _, _, assembly, provider, _, _ = read_host
    prepare_read(read_host)
    completion, use = execute_read(read_host)
    evidence = selected.require_selected_invocation(use, provider)
    assert evidence.terminal_success and evidence.completion is completion
    assert evidence.semantic_input is assembly.semantic_input
    calls = provider.calls
    before = owner.read_calls
    validate_selected_invocation_inputs(use, provider)
    assert owner.read_calls == before + 1 and provider.calls == calls == 1
    release_selected_invocation_input_verification(use, provider)
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)
    # The independent original source registration remains open.
    assert not assembly.source_results[0].host._closed


@pytest.mark.asyncio
async def test_original_read_source_mutation_terminally_refuses_after_return(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    owner, _, _, origin, _, provider, validator, _ = read_host
    prepare_read(read_host)
    _, use = execute_read(read_host)
    validator.live = False
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)
    validator.live = True
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)
    assert product_execution._read_origin(origin).uses[id(owner.node)].retained is None


@pytest.mark.asyncio
async def test_read_preparation_replay_and_equal_assembly_substitution_reject(read_host):
    owner, host, registration, _, assembly, _, _, _ = read_host
    with pytest.raises(ContractViolation, match="assembly differs"):
        product_execution.prepare_selected_input_verification(
            host, owner.node, registration, assembly=replace(assembly))
    with pytest.raises(ContractViolation, match="replay"):
        prepare_read(read_host)


@pytest.mark.asyncio
async def test_wrong_selected_input_rejects_before_provider_dispatch(read_host):
    owner, _, registration, origin, assembly, provider, _, _ = read_host
    prepare_read(read_host)
    runtime = selected._registration_state(registration).runtime
    with pytest.raises(ContractViolation, match="semantic input differs"):
        selected.issue_selected_provider_execution(runtime, registration,
            tuple(item for item in assembly.semantic_input), operation_context=owner.node)
    assert provider.calls == 0 and not provider.uses
    assert product_execution._read_origin(origin).uses[id(owner.node)].retained is None


@pytest.mark.asyncio
async def test_read_host_close_disposes_after_guard_and_refuses_later_use(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    owner, host, _, origin, _, provider, _, _ = read_host
    prepare_read(read_host)
    _, use = execute_read(read_host)
    stage = product_execution._read_origin(origin).uses[id(owner.node)]
    direct_host.close_direct_validation_host(host)
    assert not owner.guards and stage.retained is None
    assert origin not in product_execution._READ_ORIGINS
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)


@pytest.mark.asyncio
async def test_read_checkpoint_budget_and_no_reset(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    prepare_read(read_host)
    _, use = execute_read(read_host)
    provider = read_host[5]
    stage = product_execution._read_origin(read_host[3]).uses[id(read_host[0].node)]
    while stage.checkpoints < 32:
        validate_selected_invocation_inputs(use, provider)
    with pytest.raises(ContractViolation, match="checkpoint bound"):
        validate_selected_invocation_inputs(use, provider)
    assert stage.retained is None


@pytest.mark.asyncio
async def test_input_tuple_copy_rejects_before_original_factory_contact(read_host):
    owner, _, _, _, assembly, provider, _, _ = read_host
    prepare_read(read_host)
    before = owner.read_calls
    original = assembly.input_bodies
    object.__setattr__(assembly, "input_bodies", tuple(body for body in original))
    try:
        with pytest.raises(ContractViolation, match="assembly identity changed"):
            execute_read(read_host)
    finally:
        object.__setattr__(assembly, "input_bodies", original)
    assert owner.read_calls == before and provider.calls == 0


@pytest.mark.asyncio
async def test_read_factory_callable_substitution_rejects_without_invocation(read_host, monkeypatch):
    _owner, _, _, _, _, provider, _, _ = read_host
    prepare_read(read_host)
    called = []
    monkeypatch.setattr(ReadOwner, "validate_selected_input_node_use", lambda *args, **kwargs: called.append(True))
    with pytest.raises(ContractViolation, match="entrance"):
        execute_read(read_host)
    assert called == [] and provider.calls == 0


@pytest.mark.asyncio
async def test_read_dispatch_mutation_aborts_and_drops_input_retention(read_host):
    owner, _, _, origin, _, provider, validator, tracker = read_host
    prepare_read(read_host)
    provider.on_execute = lambda: setattr(validator, "live", False)
    with pytest.raises(ContractViolation):
        execute_read(read_host)
    stage = product_execution._read_origin(origin).uses[id(owner.node)]
    assert stage.status == "failed" and stage.retained is None
    assert provider.calls == 1
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)


@pytest.mark.asyncio
async def test_read_revocation_during_final_locked_check_rejects(read_host):
    owner, _, _, origin, _, provider, _, _ = read_host
    prepare_read(read_host)
    owner.on_full = lambda: setattr(owner, "node_live", False)
    with pytest.raises(ContractViolation):
        execute_read(read_host)
    assert product_execution._read_origin(origin).uses[id(owner.node)].retained is None
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_read_registration_close_retires_before_host_disposal(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    owner, host, registration, origin, _, provider, _, _ = read_host
    prepare_read(read_host)
    _, use = execute_read(read_host)
    stage = product_execution._read_origin(origin).uses[id(owner.node)]
    selected.close_selected_provider_registration(selected._registration_state(registration).runtime, registration)
    assert stage.status == "retired"
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)
    direct_host.close_direct_validation_host(host)
    assert stage.retained is None and origin not in product_execution._READ_ORIGINS


@pytest.mark.asyncio
async def test_read_wrong_thread_and_fork_refuse_without_original_calls(read_host, monkeypatch):
    from threading import Thread
    owner, host, registration, _, assembly, _, _, _ = read_host
    errors = []
    def foreign_thread():
        try:
            prepare_read(read_host)
        except ContractViolation as error:
            errors.append(error)
    thread = Thread(target=foreign_thread)
    before = owner.read_calls
    thread.start()
    thread.join()
    assert len(errors) == 1 and isinstance(errors[0], ContractViolation)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            product_execution.prepare_selected_input_verification(host, owner.node, registration, assembly=assembly)
    assert owner.read_calls == before


@pytest.mark.asyncio
async def test_read_epoch_retirement_drops_references_outside_exclusion(read_host):
    owner, host, _, origin, _, provider, _, _ = read_host
    prepare_read(read_host)
    _, use = execute_read(read_host)
    record = product_execution._read_origin(origin)
    stage = record.uses[id(owner.node)]
    with product_execution.hooks._guard(record.binding):
        product_execution._retire_selected_input_host(host, record.binding)
        assert stage.retained is not None and stage.status == "retired"
    product_execution._dispose_retired_selected_inputs(host)
    assert stage.retained is None and origin not in product_execution._READ_ORIGINS
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, provider)


@pytest.mark.asyncio
async def test_read_foreign_product_is_not_read_or_admitted(read_host):
    from aware_code_semantic_contract_runtime import SemanticBody
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as delivery,
    )
    owner, host, registration, _, assembly, _, _, _ = read_host
    class Foreign:
        def read_products(self):
            raise AssertionError("foreign reader executed")
    body = SemanticBody(replace(assembly.input_bodies[0].coordinate, role="products"),
                        assembly.input_bodies[0].canonical_body)
    mixed = delivery.SelectedInputVerificationAssembly(assembly.semantic_input,
        (*assembly.input_bodies, body), assembly.source_results,
        source_input_roles=assembly.source_input_roles,
        dependency_products=Foreign(), dependency_input_role="products")
    owner.assembly = mixed
    with pytest.raises(TypeError, match="exact admitted"):
        product_execution.prepare_selected_input_verification(host, owner.node, registration, assembly=mixed)


@pytest.mark.asyncio
async def test_read_products_from_another_command_host_reject_without_reread(read_host, dependency_case):  # noqa: F811 - pytest fixture argument
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as delivery,
    )
    _, operation, _, _, _, body, dependency_owner, consumer, planner = dependency_case
    admitted = consumer.admit_dependency_products(operation, dependency_owner.dep_resolution,
        dependency_owner.dep_fulfillment, body=body)
    dependency_owner.calls.clear()
    owner, host, registration, _, assembly, provider, _, _ = read_host
    mixed = delivery.SelectedInputVerificationAssembly(assembly.semantic_input,
        (*assembly.input_bodies, body), assembly.source_results,
        source_input_roles=assembly.source_input_roles,
        dependency_products=admitted, dependency_input_role=body.coordinate.role)
    owner.assembly = mixed
    with pytest.raises(ContractViolation, match="product host differs"):
        product_execution.prepare_selected_input_verification(host, owner.node, registration, assembly=mixed)
    assert dependency_owner.calls == [] and planner.calls == 1 and provider.calls == 0


@pytest.mark.asyncio
async def test_read_cancellation_retires_payload_and_preserves_uncertain_execution(read_host):
    class Cancelled(BaseException):
        pass
    owner, _, _, origin, _, provider, _, tracker = read_host
    prepare_read(read_host)
    def cancel():
        raise Cancelled()
    provider.on_execute = cancel
    with pytest.raises(Cancelled):
        execute_read(read_host)
    stage = product_execution._read_origin(origin).uses[id(owner.node)]
    assert stage.retained is None and stage.status == "failed"
    with pytest.raises(ContractViolation, match="active"):
        clearance(owner, tracker)


@pytest.mark.asyncio
async def test_original_read_method_code_replacement_refuses_before_contact(read_host):
    _, _, _, _, _, provider, _, _ = read_host
    prepare_read(read_host)
    original = ReadOwner.validate_selected_input_node_use.__code__
    def no_op(self, source, *, assembly=None, closure=None):
        raise AssertionError("replaced original method was called")
    ReadOwner.validate_selected_input_node_use.__code__ = no_op.__code__
    try:
        with pytest.raises(ContractViolation, match="method code changed"):
            execute_read(read_host)
    finally:
        ReadOwner.validate_selected_input_node_use.__code__ = original
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_failed_exclusion_close_revokes_then_defers_reference_disposal(read_host, monkeypatch):
    owner, host, _, origin, _, _, _, _ = read_host
    prepare_read(read_host)
    record = product_execution._read_origin(origin)
    stage = record.uses[id(owner.node)]
    original_release = record.binding.release.method
    def release_then_fail(guard):
        original_release(guard)
        raise ContractViolation("original exclusion release failed")
    with monkeypatch.context() as patch:
        patch.setattr(type(record.binding.release), "call", type(record.binding.release).call)
        object.__setattr__(record.binding.release, "method", release_then_fail)
        try:
            with pytest.raises(ContractViolation, match="release failed"):
                direct_host.close_direct_validation_host(host)
        finally:
            object.__setattr__(record.binding.release, "method", original_release)
    assert record.retired and stage.status == "retired"
    assert stage.retained is not None and not owner.guards
    # Fixed composition has confirmed release/terminal ownership here; it can
    # dispose independently without invoking a source verifier or closing it.
    product_execution._dispose_retired_selected_inputs(host)
    assert stage.retained is None and origin not in product_execution._READ_ORIGINS


@pytest.mark.asyncio
@pytest.mark.parametrize("checkpoint", ("prepare", "adopt", "complete", "verify", "fail"))
async def test_input_checkpoint_release_failure_defers_disposal(read_host, monkeypatch, checkpoint):
    owner, host, registration, origin, assembly, provider, _, tracker = read_host
    record = product_execution._read_origin(origin)
    runtime = selected._registration_state(registration).runtime
    if checkpoint != "prepare":
        prepare_read(read_host)
    if checkpoint == "fail":
        selected.issue_selected_provider_execution(
            runtime, registration, assembly.semantic_input, operation_context=owner.node)
    if checkpoint == "verify":
        _, observed_use = execute_read(read_host)
    release = record.binding.release
    original_release = release.method
    original_dispose = product_execution._release_input_data
    disposals = []
    finalized = []
    releases = 0

    class DisposalProbe:
        def __del__(self):
            finalized.append(len(owner.guards))

    def dispose(stage):
        disposals.append(len(owner.guards))
        original_dispose(stage)

    def fail_without_release(guard):
        nonlocal releases
        releases += 1
        # Completion must reach its own final guard, not fail an earlier check.
        if checkpoint == "complete" and record.uses[id(owner.node)].status != "completed":
            original_release(guard)
            return
        # Adoption's first full checkpoint succeeds; its own guard then fails.
        if checkpoint == "adopt" and releases == 1:
            original_release(guard)
            return
        raise ContractViolation("checkpoint exclusion remains held")

    with monkeypatch.context() as patch:
        patch.setattr(product_execution, "_release_input_data", dispose)
        object.__setattr__(release, "method", fail_without_release)
        try:
            with pytest.raises(ContractViolation, match="exclusion remains held"):
                if checkpoint == "prepare":
                    prepare_read(read_host)
                elif checkpoint == "adopt":
                    selected.issue_selected_provider_execution(
                        runtime, registration, assembly.semantic_input, operation_context=owner.node)
                elif checkpoint == "complete":
                    execute_read(read_host)
                elif checkpoint == "verify":
                    from aware_code_semantic_contract_runtime.selected_input_verification import (
                        validate_selected_invocation_inputs,
                    )
                    validate_selected_invocation_inputs(observed_use, provider)
                else:
                    origin.fail(record.uses[id(owner.node)])
            stage = record.uses[id(owner.node)]
            stage.product_reader = DisposalProbe()
            assert owner.guards and record.exclusion_pending
            assert stage.retained is not None and stage.source is owner.node
            assert disposals == []
            # Even explicit delivery release cannot dispose an uncertain guard.
            if checkpoint == "fail":
                origin.release_inputs(stage, selected.require_selected_invocation(provider.uses[-1], provider))
            with pytest.raises(ContractViolation):
                product_execution._read_full(record, stage)
            assert disposals == [] and finalized == [] and stage.retained is not None
            with pytest.raises(ContractViolation, match="release is unconfirmed"):
                direct_host.close_direct_validation_host(host)
            assert disposals == [] and finalized == []
        finally:
            object.__setattr__(release, "method", original_release)
            for guard in tuple(owner.guards):
                original_release(guard)
        if checkpoint == "fail":
            selected._abort_selected_provider_execution(
                runtime, selected.require_selected_invocation(provider.uses[-1], provider).admission)
        product_execution._retire_selected_input_host(host)
        product_execution._dispose_retired_selected_inputs(host)
        assert finalized == [0]
        assert disposals == [0] and stage.retained is None
        assert origin not in product_execution._READ_ORIGINS
    if checkpoint == "fail":
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, tracker)


async def _held_input_failure(monkeypatch, *, completed):
    import weakref

    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )

    fixture = read_host.__wrapped__(monkeypatch)
    case = await fixture.__anext__()
    owner, host, registration, _, assembly, provider, _, _ = case
    source_host = weakref.ref(assembly.source_results[0].host)
    held = None
    method = ReadOwner.validate_selected_input_node_use
    original_code = method.__code__

    def substituted(self, source, *, assembly=None, closure=None):
        raise AssertionError("substituted method must never run")

    def change_after_owner_return():
        method.__code__ = substituted.__code__

    try:
        if completed:
            prepare_read(case)
            _, use = execute_read(case)
        owner.on_full = change_after_owner_return
        try:
            if completed:
                validate_selected_invocation_inputs(use, provider)
            else:
                product_execution.prepare_selected_input_verification(
                    host, owner.node, registration, assembly=assembly)
        except ContractViolation as error:
            held = error
        assert held is not None
    finally:
        method.__code__ = original_code
        owner.assembly = None
        owner.on_full = None
        await fixture.aclose()
        # This test helper is a caller frame, not Code-owned rejection custody.
        case = owner = host = registration = assembly = provider = fixture = None
        use = None
    return held, source_host


@pytest.mark.asyncio
@pytest.mark.parametrize("completed", (False, True))
async def test_held_code_rejection_does_not_own_released_source(monkeypatch, completed):
    import gc

    error, source_host = await _held_input_failure(monkeypatch, completed=completed)
    gc.collect()
    assert error is not None and source_host() is None
    assert "method code changed" in str(error)


@pytest.mark.asyncio
async def test_code_custody_does_not_clear_foreign_owner_frames(read_host):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )

    prepare_read(read_host)
    _, use = execute_read(read_host)
    owner, _, _, _, assembly, provider, validator, _ = read_host
    validator.live = False
    try:
        validate_selected_invocation_inputs(use, provider)
    except ContractViolation as error:
        trace = error.__traceback__
        foreign = []
        while trace is not None:
            frame = trace.tb_frame
            if frame.f_code is ReadOwner.validate_selected_input_node_use.__code__:
                foreign.append(frame)
            trace = trace.tb_next
        assert len(foreign) == 1
        assert foreign[0].f_locals["self"] is owner
        assert foreign[0].f_locals["assembly"] is assembly
    else:
        pytest.fail("revoked original source accepted")


def _signature_failure(pin):
    try:
        product_execution._body_signature(pin)
    except AttributeError as error:
        pin = None  # Caller owns this test frame; runtime never clears it.
        # AttributeError.obj is foreign exception payload, not frame custody.
        error.obj = None
        return error
    raise AssertionError("invalid body accepted")


def test_code_rejection_custody_clears_cause_context_cycles():
    import gc
    import weakref

    class Pin:
        pass

    first_pin, second_pin = Pin(), Pin()
    references = weakref.ref(first_pin), weakref.ref(second_pin)
    first, second = _signature_failure(first_pin), _signature_failure(second_pin)
    first.__cause__ = second
    second.__context__ = first
    first_pin = second_pin = None
    assert all(reference() is not None for reference in references)
    selected._clear_input_rejection_frames(first, product_execution.__file__)
    gc.collect()
    assert all(reference() is None for reference in references)
    assert first.__cause__ is second and second.__context__ is first
