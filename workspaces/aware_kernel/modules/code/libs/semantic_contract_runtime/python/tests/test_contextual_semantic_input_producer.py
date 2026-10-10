"""Declared opaque context over the existing original-source execution rail."""

from dataclasses import replace
from types import MethodType

import pytest

from aware_code_semantic_contract_runtime import (
    ContentDigest, ContractViolation, SemanticContractRef, SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF,
)
from test_semantic_input_producer import (
    _DECLARATION, _SourceValidator, _body, _digest, _expectation,
)


_CONTEXT = SemanticContractRef("example.context.v1", "1", _digest("context-schema"))


def context(body=b"\xff\x00opaque-context", *, role="context", contract=_CONTEXT):
    return SemanticBody(
        SemanticValueCoordinate(role, contract, "context:" + _digest(body.hex()).value,
                                ContentDigest.of_bytes(body), len(body)), body,
    )


def expectation(operation, source, contexts, **changes):
    base = _expectation(operation, source)
    return inputs.SemanticInputProductionExpectation.create(
        use_ref=changes.get("use_ref", base.use_ref),
        operation_ref=base.operation_ref, stage=changes.get("stage", base.stage),
        package_identity=base.package_identity, operation_identity=operation,
        source_identity=source, source_coordinates=base.source_coordinates,
        context_bodies=contexts,
    )


class OriginalSource(_SourceValidator):
    def __init__(self, source, operation, contexts):
        super().__init__(source, operation)
        # Independent retained fixture evidence, not the caller's body objects.
        self.evidence = tuple((replace(body.coordinate), bytes(body.canonical_body))
                              for body in contexts)
        self.context_calls = 0
        self.return_value = None

    def validate_semantic_input_context(self, source_admission, *, expected):
        self.validate_semantic_input_source(source_admission, expected=expected)
        self.context_calls += 1
        if tuple((body.coordinate, body.canonical_body) for body in expected.context_bodies) != self.evidence:
            raise ContractViolation("context differs from original retained fixture evidence")
        return self.return_value


def register(host, owner, producer, *, declaration=None, entrance=True):
    return inputs.register_semantic_input_producer(
        host, declaration=declaration or replace(
            _DECLARATION,
            context_contracts=(inputs.SemanticInputContextContract("context", _CONTEXT),),
        ), producer=producer, validator=owner,
        validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources,
        context_validator_entrance=owner.validate_semantic_input_context if entrance else None,
    )


@pytest.mark.asyncio
async def test_original_context_is_detached_opaque_and_validated_around_owner():
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    bodies = (context(),)
    owner = OriginalSource(source, operation, bodies)
    expected = expectation(operation, source, bodies)
    seen = []

    async def produce(value):
        assert value.context_bodies is bodies
        assert value.input_digest == expected.input_digest
        assert value.context_bodies[0].canonical_body == b"\xff\x00opaque-context"
        seen.append(value)
        return _body()

    admitted = register(host, owner, produce)
    result = await inputs.execute_registered_semantic_input(
        host, admitted, source_admission=source, expected=expected,
    )
    assert result == _body() and len(seen) == 1 and owner.context_calls == 3
    with pytest.raises(ContractViolation, match="consumed"):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source, expected=expected,
        )
    host.close()


@pytest.mark.parametrize("bad", ["missing", "lambda", "reconstructed", "foreign_receiver"])
def test_registration_requires_original_context_method_on_original_source_owner(bad):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = OriginalSource(source, operation, (context(),))
    entrance = owner.validate_semantic_input_context
    if bad == "missing":
        entrance = None
    elif bad == "lambda":
        entrance = lambda *args, **kwargs: None
    elif bad == "reconstructed":
        entrance = MethodType(lambda self, *args, **kwargs: None, owner)
    else:
        entrance = OriginalSource(source, operation, (context(),)).validate_semantic_input_context
    with pytest.raises(ContractViolation, match="original context"):
        inputs.register_semantic_input_producer(
            host, declaration=replace(_DECLARATION, context_contracts=(
                inputs.SemanticInputContextContract("context", _CONTEXT),
            )), producer=lambda value: _body(), validator=owner,
            validator_entrance=owner.validate_semantic_input_source,
            reader=owner, reader_entrance=owner.read_semantic_input_sources,
            context_validator_entrance=entrance,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["missing", "extra", "wrong_role", "wrong_contract", "unobserved"])
async def test_complete_context_inventory_and_original_evidence_are_required(bad):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = OriginalSource(source, operation, (context(),))
    seen = []
    admitted = register(host, owner, lambda value: seen.append(value) or _body())
    bodies = (context(),)
    if bad == "missing":
        bodies = ()
    elif bad == "extra":
        bodies += (context(role="extra"),)
    elif bad == "wrong_role":
        bodies = (context(role="wrong"),)
    elif bad == "wrong_contract":
        bodies = (context(contract=replace(_CONTEXT, version="2")),)
    else:
        bodies = (context(b"not-the-retained-context"),)
    with pytest.raises(ContractViolation):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source,
            expected=expectation(operation, source, bodies),
        )
    assert not seen
    # Repair does not revive the attempted use or fall back to context-free v1.
    with pytest.raises(ContractViolation, match="consumed"):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source,
            expected=expectation(operation, source, (context(),)),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["tuple", "coordinate", "body", "epoch_evidence", "declaration", "entrance", "non_none", "producer_input"])
async def test_changes_during_awaited_owner_call_refuse_result_and_replay(bad, monkeypatch):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    bodies = (context(),)
    owner = OriginalSource(source, operation, bodies)
    expected = expectation(operation, source, bodies)
    declaration = replace(_DECLARATION, context_contracts=(
        inputs.SemanticInputContextContract("context", _CONTEXT),
    ))

    async def produce(value):
        if bad == "tuple":
            object.__setattr__(expected, "context_bodies", tuple(list(bodies)))
        elif bad == "coordinate":
            object.__setattr__(bodies[0], "coordinate", replace(bodies[0].coordinate))
        elif bad == "body":
            changed = context(b"changed")
            object.__setattr__(bodies[0], "canonical_body", changed.canonical_body)
            object.__setattr__(bodies[0], "coordinate", changed.coordinate)
            coherent = expectation(operation, source, bodies)
            object.__setattr__(expected, "input_digest", coherent.input_digest)
        elif bad == "epoch_evidence":
            owner.evidence = ((context(b"moved-epoch").coordinate, b"moved-epoch"),)
        elif bad == "declaration":
            object.__setattr__(declaration, "profile_ref", "changed-profile")
        elif bad == "entrance":
            monkeypatch.setattr(OriginalSource, "validate_semantic_input_context",
                                lambda *args, **kwargs: None)
        elif bad == "non_none":
            owner.return_value = ("fake-receipt",)
        else:
            object.__setattr__(value, "context_bodies", tuple(list(bodies)))
        return _body()

    admitted = register(host, owner, produce, declaration=declaration)
    with pytest.raises((ContractViolation, TypeError)):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source, expected=expected,
        )
    # Registration changes may also refuse before reaching the spent-use check.
    with pytest.raises((ContractViolation, TypeError)):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source, expected=expected,
        )
    assert not host._uses[(admitted, expected.use_ref)].running
    assert host._uses[(admitted, expected.use_ref)].consumed


def test_context_is_digest_bound_and_legacy_preimage_remains_unchanged():
    operation, source = object(), object()
    legacy = _expectation(operation, source)
    old_payload = {
        "operation_ref": legacy.operation_ref,
        "package_identity": legacy.package_identity.to_wire(),
        "source_coordinates": [value.to_wire() for value in legacy.source_coordinates],
        "stage": legacy.stage, "use_ref": legacy.use_ref,
    }
    assert legacy.input_digest == ContentDigest.of_bytes(canonical_json_bytes(old_payload))
    a = expectation(operation, source, (context(b"a"),))
    b = expectation(operation, source, (context(b"b"),))
    assert a.input_digest != b.input_digest and a.input_digest != legacy.input_digest
    with pytest.raises(ContractViolation, match="digest"):
        replace(a, input_digest=b.input_digest)
    assert replace(_DECLARATION, context_contracts=()).digest == _DECLARATION.digest


def test_dependency_products_cannot_be_relabelled_as_source_context():
    with pytest.raises(ContractViolation, match="dependency entrance"):
        inputs.SemanticInputContextContract("context", SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF)
    with pytest.raises(ContractViolation, match="dependency entrance"):
        expectation(object(), object(), (context(contract=SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF),))


@pytest.mark.parametrize("bad", ["duplicates", "reordered", "foreign", "count", "bytes", "role_collision"])
def test_context_boundaries_refuse_without_owner_invocation(bad, monkeypatch):
    operation, source = object(), object()
    bodies = (context(),)
    if bad == "duplicates":
        bodies += bodies
    elif bad == "reordered":
        bodies = (context(role="z"), context(role="a"))
    elif bad == "foreign":
        bodies = (object(),)
    elif bad == "count":
        monkeypatch.setattr(inputs, "MAX_CONTEXT_BODIES", 0)
    elif bad == "bytes":
        monkeypatch.setattr(inputs, "MAX_CONTEXT_BYTES", 1)
    else:
        with pytest.raises(ContractViolation, match="disjoint"):
            replace(_DECLARATION, context_contracts=(
                inputs.SemanticInputContextContract("source", _CONTEXT),
            ))
        return
    with pytest.raises((ContractViolation, TypeError)):
        expectation(operation, source, bodies)


def joined_fixture(mode, producer):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    bodies = (context(),)
    contracts = (inputs.SemanticInputContextContract("context", _CONTEXT),)
    prior_context = bodies if mode != "terminal_only" else ()
    terminal_context = bodies if mode != "predecessor_only" else ()
    prior_owner = OriginalSource(source, operation, prior_context)
    terminal_owner = OriginalSource(source, operation, terminal_context)
    prior_expected = expectation(operation, source, prior_context,
                                 use_ref="prior", stage="prepared")
    terminal_expected = expectation(operation, source, terminal_context,
                                    use_ref="terminal", stage="joined")
    prior_declaration = replace(_DECLARATION, producer_ref="example.prepare",
                                result_role="prepared",
                                context_contracts=contracts if prior_context else ())
    prior_result = SemanticBody(
        replace(_body().coordinate, role="prepared"), _body().canonical_body,
    )
    prior = register(host, prior_owner, lambda value: prior_result,
                     declaration=prior_declaration, entrance=bool(prior_context))
    ordinary = replace(_DECLARATION, producer_ref="example.joined", result_role="joined",
                       context_contracts=contracts if terminal_context else ())
    terminal = inputs.register_joined_semantic_input_producer(
        host, declaration=inputs.SemanticInputJoinedProducerDeclaration(
            ordinary, (inputs.SemanticInputSourceContract("prepared", prior_result.coordinate.contract),),
        ), producer=producer, validator=terminal_owner,
        validator_entrance=terminal_owner.validate_semantic_input_source,
        reader=terminal_owner, reader_entrance=terminal_owner.read_semantic_input_sources,
        context_validator_entrance=terminal_owner.validate_semantic_input_context if terminal_context else None,
    )
    join = inputs.open_semantic_input_role_join(
        host, joined_registration=terminal, joined_expected=terminal_expected,
        source_admission=source,
        predecessors=(inputs.SemanticInputRoleJoinPredecessor(prior, prior_expected),),
    )
    return host, source, prior, prior_expected, terminal, terminal_expected, join, prior_result


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["both", "predecessor_only", "terminal_only"])
async def test_contextual_join_preserves_declared_inputs_and_binds_v2_preimage(mode):
    seen = []

    def produce(value):
        seen.append(value)
        return SemanticBody(replace(_body().coordinate, role="joined"), _body().canonical_body)

    host, source, prior, prior_expected, terminal, expected, join, prior_result = joined_fixture(mode, produce)
    await inputs.execute_registered_semantic_input(
        host, prior, source_admission=source, expected=prior_expected,
    )
    await inputs.execute_registered_joined_semantic_input(
        host, terminal, source_admission=source, expected=expected, role_join=join,
    )
    assert seen[0].ordinary.context_bodies is expected.context_bodies
    assert seen[0].predecessors[0].canonical_body == prior_result.canonical_body
    fields = (
        expected.operation_ref.encode(),
        canonical_json_bytes(expected.package_identity.to_wire()),
        expected.input_digest.value.encode(),
        b"prepared", prior_expected.use_ref.encode(), prior_expected.input_digest.value.encode(),
        canonical_json_bytes([item.to_wire() for item in prior_expected.source_coordinates]),
        canonical_json_bytes(prior_result.coordinate.to_wire()), prior_result.canonical_body,
    )
    preimage = b"aware.code.semantic-input-predecessor-closure.v2\0"
    preimage += b"".join(len(field).to_bytes(8, "big") + field for field in fields)
    assert seen[0].predecessor_closure_digest == ContentDigest.of_bytes(preimage)
    with pytest.raises(ContractViolation):
        await inputs.execute_registered_joined_semantic_input(
            host, terminal, source_admission=source, expected=expected, role_join=join,
        )
    host.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("which", ["prior", "terminal"])
async def test_context_substitution_between_join_stages_terminally_consumes_join(which):
    called = []
    fixture = joined_fixture("both", lambda value: called.append(value))
    host, source, prior, prior_expected, terminal, expected, join, _ = fixture
    await inputs.execute_registered_semantic_input(
        host, prior, source_admission=source, expected=prior_expected,
    )
    changed = prior_expected if which == "prior" else expected
    original = changed.context_bodies
    object.__setattr__(changed, "context_bodies", tuple(list(original)))
    with pytest.raises(ContractViolation):
        await inputs.execute_registered_joined_semantic_input(
            host, terminal, source_admission=source, expected=expected, role_join=join,
        )
    object.__setattr__(changed, "context_bodies", original)
    with pytest.raises(ContractViolation, match="unavailable"):
        await inputs.execute_registered_joined_semantic_input(
            host, terminal, source_admission=source, expected=expected, role_join=join,
        )
    assert not called


@pytest.mark.asyncio
async def test_context_free_registration_cannot_silently_accept_context():
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = _SourceValidator(source, operation)
    called = []
    admitted = inputs.register_semantic_input_producer(
        host, declaration=_DECLARATION,
        producer=lambda value: called.append(value) or _body(), validator=owner,
        validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources,
    )
    with pytest.raises(ContractViolation, match="context inventory"):
        await inputs.execute_registered_semantic_input(
            host, admitted, source_admission=source,
            expected=expectation(operation, source, (context(),)),
        )
    assert not called and owner.calls == 0
