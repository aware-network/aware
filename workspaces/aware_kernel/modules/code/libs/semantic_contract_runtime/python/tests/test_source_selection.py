from __future__ import annotations

import asyncio
import copy
from dataclasses import replace
from threading import Thread

import pytest
from test_semantic_input_producer import (
    _DECLARATION,
    _SOURCE_CONTRACT,
    _body,
    _expectation,
    _SourceValidator,
)

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSelectedSource,
    SemanticSourceSelection,
    decode_source_selection,
    encode_source_selection,
    source_selection_body,
)


def selection(expected, predecessors=(), *, rows=None):
    return SemanticSourceSelection(expected.package_identity.package,
        ContentDigest.of_bytes(b"original-source-inventory"), expected.input_digest,
        tuple(x.coordinate for x in predecessors), rows if rows is not None else (
            SemanticSelectedSource("input", _SOURCE_CONTRACT, "nested/manifest.toml", ContentDigest.of_bytes(b"inner")),
        ))


def register(host, owner, produce, *, declaration=None, retain=True):
    return inputs.register_semantic_input_producer(host,
        declaration=declaration or replace(_DECLARATION, result_role="selected_sources", result_contract=SOURCE_SELECTION_REF),
        producer=produce, validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources, retain_result=retain)


async def direct(*, produce=None, retain=True, owner_type=_SourceValidator):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = owner_type(source, operation)
    expected = _expectation(operation, source)
    def default(value):
        return source_selection_body(selection(expected), role="selected_sources")
    registration = register(host, owner, produce or default, retain=retain)
    result = await inputs.execute_registered_semantic_input(host, registration, source_admission=source, expected=expected)
    return host, registration, owner, source, expected, result


def read(fixture, **changes):
    host, registration, _, source, expected, result = fixture
    return inputs.read_registered_semantic_input_source_selection(changes.get("host", host),
        changes.get("registration", registration), source_admission=changes.get("source", source),
        expected=changes.get("expected", expected), result=changes.get("result", result))


def release(fixture):
    host, registration, _, source, expected, result = fixture
    inputs.release_registered_semantic_input_result(host, registration, source_admission=source, expected=expected, result=result)


@pytest.mark.asyncio
async def test_original_return_has_public_repeatable_currentness_reader_and_cleanup():
    f = await direct()
    first, second = read(f), read(f)
    assert first == second and first is not second
    assert first.sources[0].relative_path == "nested/manifest.toml"
    with pytest.raises(ContractViolation, match="consumed"):
        await inputs.execute_registered_semantic_input(f[0], f[1], source_admission=f[3], expected=f[4])
    release(f)
    with pytest.raises(ContractViolation, match="original returned"):
        read(f)
    assert not f[0]._results
    f[0].close()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["copy_result", "copy_expected", "foreign_source", "foreign_registration", "host", "coordinate", "tuple", "digest", "body", "declaration", "producer"])
async def test_original_result_substitution_refuses(change):
    f = await direct()
    host, registration, owner, source, expected, result = f
    if change == "copy_result":
        with pytest.raises(ContractViolation): read(f, result=copy.copy(result))
        assert read(f)  # A foreign body cannot originate an association.
        release(f)
        return
    if change == "copy_expected":
        action = lambda: read(f, expected=replace(expected))
    elif change == "foreign_source":
        action = lambda: read(f, source=object())
    elif change == "foreign_registration":
        other = register(host, owner, lambda value: result, declaration=replace(_DECLARATION, producer_ref="foreign"))
        action = lambda: read(f, registration=other)
    elif change == "host":
        foreign = inputs.SemanticInputProducerHost()
        with pytest.raises(ContractViolation): read(f, host=foreign)
        assert read(f)
        foreign.close()
        release(f)
        return
    elif change == "coordinate":
        object.__setattr__(result, "coordinate", replace(result.coordinate))
        action = lambda: read(f)
    elif change == "tuple":
        object.__setattr__(expected, "source_coordinates", tuple(list(expected.source_coordinates)))
        action = lambda: read(f)
    elif change == "digest":
        object.__setattr__(result.coordinate, "digest", replace(result.coordinate.digest))
        action = lambda: read(f)
    elif change == "body":
        altered = replace(selection(expected), source_identity_digest=ContentDigest.of_bytes(b"changed"))
        replacement = source_selection_body(altered, role="selected_sources")
        object.__setattr__(result, "canonical_body", replacement.canonical_body)
        object.__setattr__(result, "coordinate", replacement.coordinate)
        action = lambda: read(f)
    elif change == "declaration":
        host._registrations[registration].declaration = replace(host._registrations[registration].declaration)
        action = lambda: read(f)
    else:
        host._registrations[registration].producer = lambda value: result
        action = lambda: read(f)
    with pytest.raises(ContractViolation): action()
    assert not host._results
    host.close()


@pytest.mark.asyncio
async def test_source_loss_cannot_be_restored_into_result_reuse_and_close_clears_records():
    f = await direct()
    f[2].live = False
    with pytest.raises(ContractViolation, match="source unavailable"): read(f)
    f[2].live = True
    with pytest.raises(ContractViolation, match="original returned"): read(f)
    g = await direct()
    g[0].close()
    assert not g[0]._results
    with pytest.raises(ContractViolation, match="closed"): read(g)


@pytest.mark.asyncio
async def test_foreign_thread_and_fork_refuse_without_source_callback(monkeypatch):
    f = await direct()
    calls = f[2].calls
    errors = []
    def foreign():
        try: read(f)
        except ContractViolation as exc: errors.append(str(exc))
    thread = Thread(target=foreign); thread.start(); thread.join()
    assert errors and f[2].calls == calls
    g = await direct()
    with monkeypatch.context() as m:
        m.setattr(inputs.os, "getpid", lambda: g[0]._pid + 1)
        with pytest.raises(ContractViolation, match="another process"): read(g)
    release(g)


@pytest.mark.asyncio
async def test_no_retrospective_admission_for_unretained_or_failed_owner_return():
    f = await direct(retain=False)
    with pytest.raises(ContractViolation, match="original returned"): read(f)
    assert not f[0]._results
    async def fail(value):
        raise RuntimeError("owner failed")
    with pytest.raises(RuntimeError): await direct(produce=fail)


@pytest.mark.asyncio
async def test_retained_byte_and_count_bounds_refuse_terminally(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(inputs, "MAX_RETAINED_INPUT_RESULTS", 0)
        with pytest.raises(ContractViolation, match="retention budget"): await direct()
    with monkeypatch.context() as m:
        m.setattr(inputs, "MAX_RETAINED_INPUT_RESULT_BYTES", 1)
        with pytest.raises(ContractViolation, match="retention budget"): await direct()


@pytest.mark.asyncio
async def test_post_execution_owner_check_can_detect_mutation_and_cleanup_after_source_expiry():
    class Owner(_SourceValidator):
        action = None
        def validate_semantic_input_source(self, source_admission, *, expected):
            super().validate_semantic_input_source(source_admission, expected=expected)
            if self.action:
                action, self.action = self.action, None
                action()
    f = await direct(owner_type=Owner)
    f[2].action = lambda: object.__setattr__(f[5], "coordinate", replace(f[5].coordinate))
    with pytest.raises(ContractViolation): read(f)
    assert not f[0]._results
    g = await direct()
    g[2].live = False
    release(g)  # Cleanup does not need successful validation of expired evidence.
    assert not g[0]._results


@pytest.mark.asyncio
async def test_validator_substitution_during_read_does_not_dispatch_foreign_callback():
    class Owner(_SourceValidator):
        action = None
        def validate_semantic_input_source(self, source_admission, *, expected):
            super().validate_semantic_input_source(source_admission, expected=expected)
            if self.action:
                action, self.action = self.action, None
                action()
    f = await direct(owner_type=Owner)
    invoked = []
    f[2].action = lambda: setattr(f[0]._registrations[f[1]], "validator_entrance", lambda *a, **kw: invoked.append("foreign"))
    with pytest.raises(ContractViolation): read(f)
    assert not invoked and not f[0]._results


@pytest.mark.asyncio
async def test_original_parent_and_context_expiry_are_required_for_later_consumption():
    from test_contextual_semantic_input_producer import (
        OriginalSource,
        context,
        expectation,
    )
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    bodies = (context(),)
    owner = OriginalSource(source, operation, bodies)
    expected = expectation(operation, source, bodies)
    declaration = replace(_DECLARATION, result_role="selected_sources", result_contract=SOURCE_SELECTION_REF,
        context_contracts=(inputs.SemanticInputContextContract("context", bodies[0].coordinate.contract),))
    registration = inputs.register_semantic_input_producer(host, declaration=declaration,
        producer=lambda value: source_selection_body(selection(expected), role="selected_sources"),
        validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources,
        context_validator_entrance=owner.validate_semantic_input_context, retain_result=True)
    result = await inputs.execute_registered_semantic_input(host, registration, source_admission=source, expected=expected)
    f = host, registration, owner, source, expected, result
    assert read(f)
    original = owner.evidence
    owner.evidence = ()
    with pytest.raises(ContractViolation): read(f)
    owner.evidence = original
    with pytest.raises(ContractViolation, match="original returned"): read(f)


async def joined():
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = _SourceValidator(source, operation)
    before = _expectation(operation, source, use_ref="before")
    before = inputs.SemanticInputProductionExpectation.create(use_ref=before.use_ref,
        operation_ref=before.operation_ref, stage="owner_source_interpretation", package_identity=before.package_identity,
        operation_identity=operation, source_identity=source, source_coordinates=before.source_coordinates)
    final = _expectation(operation, source, use_ref="final")
    pred = register(host, owner, lambda value: _body(), declaration=_DECLARATION)
    declared = inputs.SemanticInputJoinedProducerDeclaration(
        replace(_DECLARATION, producer_ref="projection", result_role="selected_sources", result_contract=SOURCE_SELECTION_REF),
        (inputs.SemanticInputSourceContract(_DECLARATION.result_role, _DECLARATION.result_contract),),
        predecessor_stages=("owner_source_interpretation",))
    def project(value):
        # Only the semantic owner decodes its predecessor. Code sees opaque bytes.
        assert value.predecessors[0].canonical_body == b"result"
        return source_selection_body(selection(final, value.predecessors), role="selected_sources")
    terminal = inputs.register_joined_semantic_input_producer(host, declaration=declared,
        producer=project, validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources, retain_result=True)
    join = inputs.open_semantic_input_role_join(host, joined_registration=terminal, joined_expected=final,
        source_admission=source, predecessors=(inputs.SemanticInputRoleJoinPredecessor(pred, before),))
    original = await inputs.execute_registered_semantic_input(host, pred, source_admission=source, expected=before)
    result = await inputs.execute_registered_joined_semantic_input(host, terminal, role_join=join, source_admission=source, expected=final)
    return (host, terminal, owner, source, final, result), (host, pred, owner, source, before, original)


@pytest.mark.asyncio
async def test_existing_owner_predecessor_join_produces_neutral_selection_with_lifetime():
    final, previous = await joined()
    selected = read(final)
    assert selected.predecessor_coordinates == (previous[5].coordinate,)
    assert not final[0]._role_joins
    release(previous)
    assert not final[0]._results  # Cascading retirement of the projection.
    with pytest.raises(ContractViolation): read(final)


@pytest.mark.asyncio
async def test_joined_projection_refuses_mutated_original_predecessor():
    final, previous = await joined()
    object.__setattr__(previous[5], "coordinate", replace(previous[5].coordinate))
    with pytest.raises(ContractViolation): read(final)
    assert all(item.result is not final[5] for item in final[0]._results.values())


@pytest.mark.asyncio
async def test_registration_close_revokes_original_result_and_its_projection():
    final, previous = await joined()
    inputs.close_semantic_input_producer_registration(previous[0], previous[1])
    assert not final[0]._results
    with pytest.raises(ContractViolation): read(final)


@pytest.mark.asyncio
async def test_original_slot_descriptor_is_checked_without_invoking_replacement(monkeypatch):
    f = await direct()
    invoked = []
    def foreign(value):
        invoked.append(value)
        raise AssertionError("foreign descriptor invoked")
    with monkeypatch.context() as m:
        m.setattr(SemanticBody, "coordinate", property(foreign))
        with pytest.raises(ContractViolation, match="slot changed"): read(f)
    assert not invoked and not f[0]._results


@pytest.mark.asyncio
async def test_owner_method_descriptor_is_rejected_without_invocation(monkeypatch):
    f = await direct()
    invoked = []
    class ForeignDescriptor:
        def __get__(self, instance, owner):
            invoked.append("descriptor"); raise AssertionError("foreign method descriptor")
    with monkeypatch.context() as m:
        m.setattr(_SourceValidator, "validate_semantic_input_source", ForeignDescriptor())
        with pytest.raises(ContractViolation, match="entrance changed"): read(f)
    assert not invoked and not f[0]._results


@pytest.mark.asyncio
async def test_restamped_class_and_hostile_metaclass_refuse_without_behavior():
    f = await direct()
    invoked = []
    class Hostile(type):
        def __hash__(cls):
            invoked.append("hash"); raise AssertionError("foreign hash")
        def __eq__(cls, other):
            invoked.append("eq"); raise AssertionError("foreign equality")
    class Foreign(metaclass=Hostile):
        __slots__ = ("coordinate", "canonical_body")
    original = type(f[5])
    object.__setattr__(f[5], "__class__", Foreign)
    try:
        with pytest.raises(ContractViolation, match="node type changed"): read(f)
        assert not invoked and not f[0]._results
    finally:
        object.__setattr__(f[5], "__class__", original)


@pytest.mark.asyncio
async def test_restamped_nominal_registration_is_not_hashed_during_result_retirement():
    f = await direct()
    invoked = []
    class Foreign:
        __slots__ = ("_token",)
        def __hash__(self):
            invoked.append("hash"); raise AssertionError("foreign nominal hash")
    original = type(f[1])
    object.__setattr__(f[1], "__class__", Foreign)
    try:
        with pytest.raises((TypeError, ContractViolation)): read(f)
        assert not invoked and not f[0]._results
    finally:
        object.__setattr__(f[1], "__class__", original)


@pytest.mark.asyncio
async def test_cancelled_execution_never_retains_result_or_reopens_use():
    entered = asyncio.Event()
    async def produce(value):
        entered.set()
        await asyncio.Event().wait()
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = _SourceValidator(source, operation)
    expected = _expectation(operation, source)
    registration = register(host, owner, produce)
    task = asyncio.create_task(inputs.execute_registered_semantic_input(host, registration,
        source_admission=source, expected=expected))
    await entered.wait(); task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    assert not host._results
    with pytest.raises(ContractViolation, match="consumed"):
        await inputs.execute_registered_semantic_input(host, registration, source_admission=source, expected=expected)
    host.close()


def test_dependency_products_are_not_selected_source_contracts():
    with pytest.raises(ContractViolation, match="dependency products"):
        SemanticSelectedSource("input", SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF, "nested/input", ContentDigest.of_bytes(b"inner"))


def test_explicit_stages_are_complete_and_digest_bound():
    base = inputs.SemanticInputJoinedProducerDeclaration(_DECLARATION,
        (inputs.SemanticInputSourceContract("owner_input", _DECLARATION.result_contract),))
    staged = replace(base, predecessor_stages=("owner_source_interpretation",))
    assert staged.digest != base.digest
    assert staged.digest == ContentDigest.of_bytes(canonical_json_bytes({
        "contract": "aware.code.staged-semantic-input-joined-producer-declaration.v2",
        "ordinary_join_digest": base.digest.value,
        "predecessor_stages": ["owner_source_interpretation"],
    }))
    for bad in (("first", "extra"), ("bad stage",), ["stage"]):
        with pytest.raises((TypeError, ContractViolation)): replace(base, predecessor_stages=bad)


@pytest.mark.asyncio
async def test_staged_join_binds_actual_input_digests_in_existing_v2_closure():
    seen = []
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    owner = _SourceValidator(source, operation)
    before = _expectation(operation, source, use_ref="before")
    final = _expectation(operation, source, use_ref="final")
    previous = register(host, owner, lambda value: _body(), declaration=_DECLARATION)
    declaration = inputs.SemanticInputJoinedProducerDeclaration(
        replace(_DECLARATION, producer_ref="projection", result_role="selected_sources", result_contract=SOURCE_SELECTION_REF),
        (inputs.SemanticInputSourceContract("owner_input", _DECLARATION.result_contract),),
        predecessor_stages=(before.stage,))
    def project(value):
        seen.append(value.predecessor_closure_digest)
        return source_selection_body(selection(final, value.predecessors), role="selected_sources")
    registered = inputs.register_joined_semantic_input_producer(host, declaration=declaration, producer=project,
        validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources, retain_result=True)
    join = inputs.open_semantic_input_role_join(host, joined_registration=registered, joined_expected=final,
        source_admission=source, predecessors=(inputs.SemanticInputRoleJoinPredecessor(previous, before),))
    result = await inputs.execute_registered_semantic_input(host, previous, source_admission=source, expected=before)
    await inputs.execute_registered_joined_semantic_input(host, registered, role_join=join, source_admission=source, expected=final)
    fields = (final.operation_ref.encode(), canonical_json_bytes(final.package_identity.to_wire()),
        final.input_digest.value.encode(), b"owner_input", before.use_ref.encode(), before.input_digest.value.encode(),
        canonical_json_bytes([x.to_wire() for x in before.source_coordinates]),
        canonical_json_bytes(result.coordinate.to_wire()), result.canonical_body)
    wire = b"aware.code.semantic-input-predecessor-closure.v2\0" + b"".join(len(x).to_bytes(8, "big") + x for x in fields)
    assert seen == [ContentDigest.of_bytes(wire)]


def test_selection_count_and_byte_bounds(monkeypatch):
    import aware_code_semantic_contract_runtime.source_selection as module
    expected = _expectation(object(), object())
    with monkeypatch.context() as m:
        m.setattr(module, "MAX_CANDIDATES", 0)
        with pytest.raises(ContractViolation): selection(expected)
    with monkeypatch.context() as m:
        m.setattr(module, "MAX_SOURCE_SELECTION_BYTES", 1)
        with pytest.raises(ContractViolation): selection(expected)
        with pytest.raises(ContractViolation): decode_source_selection(b"{}")


@pytest.mark.parametrize("path", ["../x", "/x", "x//y", "x/./y", "x\\y", "x/ /y", "x/e\u0301"])
def test_shared_candidate_path_grammar_is_reused(path):
    with pytest.raises(ContractViolation):
        SemanticSelectedSource("input", _SOURCE_CONTRACT, path, ContentDigest.of_bytes(b"inner"))


def test_codec_is_strict_complete_and_preserves_distinct_paths_with_equal_digests():
    expected = _expectation(object(), object())
    first = selection(expected).sources[0]
    value = selection(expected, rows=(first, replace(first, relative_path="other/manifest.toml")))
    body = encode_source_selection(value)
    assert decode_source_selection(body) == value
    for damaged in (body + b"\n", body.replace(b'"contract":', b'"contract":null,"contract":', 1),
                    canonical_json_bytes({**value.to_wire(), "extra": 1})):
        with pytest.raises(ContractViolation): decode_source_selection(damaged)
    with pytest.raises(ContractViolation): selection(expected, rows=(first, first))
    with pytest.raises(ContractViolation): selection(expected, rows=tuple(reversed(value.sources)))
    with pytest.raises(ContractViolation): selection(expected, rows=(first, replace(first, role="other")))
    with pytest.raises(ContractViolation): selection(expected, rows=(first,
        replace(first, relative_path="other/manifest.toml", contract=_DECLARATION.result_contract)))


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["package", "input", "predecessors"])
async def test_generic_selection_must_match_its_actual_execution(field):
    def produce(value):
        expected = _expectation(object(), object())
        base = selection(expected)
        if field == "package": base = replace(base, package=replace(base.package, package_ref="foreign"))
        elif field == "input": base = replace(base, production_input_digest=ContentDigest.of_bytes(b"foreign"))
        else: base = replace(base, predecessor_coordinates=(_body().coordinate,))
        return source_selection_body(base, role="selected_sources")
    with pytest.raises(ContractViolation, match="production differs"): await direct(produce=produce)


def _independent_selection_wire(value):
    # Original public nested-wire formula, not the optimized private projector.
    return {"contract": "aware.code.semantic-source-selection.v1",
        "package": value.package.to_wire(),
        "source_identity_digest": value.source_identity_digest.to_wire(),
        "production_input_digest": value.production_input_digest.to_wire(),
        "predecessor_coordinates": [x.to_wire() for x in value.predecessor_coordinates],
        "sources": [{"role": x.role, "contract": x.contract.to_wire(),
            "relative_path": x.relative_path, "content_digest": x.content_digest.to_wire()}
            for x in value.sources]}


@pytest.mark.parametrize("count", [0, 1, 17, 3501])
def test_closed_projection_preserves_complete_original_wire(count):
    expected = _expectation(object(), object())
    rows = tuple(SemanticSelectedSource("input", _SOURCE_CONTRACT,
        f"nested/{i:05d}-\u00e9.aware", ContentDigest.of_bytes(b"same bytes"))
        for i in range(count))
    value = selection(expected, predecessors=(_body(),), rows=rows)
    independent = _independent_selection_wire(value)
    body = canonical_json_bytes(independent)
    assert value.to_wire() == independent
    assert encode_source_selection(value) == body
    assert encode_source_selection(decode_source_selection(body)) == body
    assert value.sources == rows  # Projection must not restamp borrowed values.


def test_encoder_admits_each_closed_row_once_without_nested_wire_dispatch(monkeypatch):
    expected = _expectation(object(), object())
    first = selection(expected).sources[0]
    value = selection(expected, rows=(first, replace(first, relative_path="other/manifest.toml")))
    original = SemanticSelectedSource.__post_init__
    calls = []

    def validate(row):
        calls.append(row)
        original(row)

    def forbidden_wire(row):
        raise AssertionError("fresh projection must not dispatch nested wire methods")

    with monkeypatch.context() as m:
        m.setattr(SemanticSelectedSource, "__post_init__", validate)
        m.setattr(SemanticSelectedSource, "to_wire", forbidden_wire)
        assert encode_source_selection(value)
        assert len(calls) == len(value.sources)
        assert all(a is b for a, b in zip(calls, value.sources, strict=True))
        calls.clear()
        assert value.to_wire()
        assert len(calls) == len(value.sources)


@pytest.mark.parametrize("field", ["package", "source_epoch", "production", "predecessor",
                                    "sources", "contract", "role", "path", "digest"])
@pytest.mark.parametrize("entrance", ["encode", "wire"])
def test_fresh_projection_rejects_nested_foreign_values_before_behavior(field, entrance):
    value = selection(_expectation(object(), object()))
    calls = []

    class HostileMeta(type):
        def __hash__(cls):
            calls.append("hash")
            raise AssertionError("foreign type hash")

        def __eq__(cls, other):
            calls.append("eq")
            raise AssertionError("foreign type equality")

    class Foreign(metaclass=HostileMeta):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign value behavior")

    rejected = Foreign()
    if field == "package":
        target, name = value, "package"
    elif field == "source_epoch":
        target, name = value, "source_identity_digest"
    elif field == "production":
        target, name = value, "production_input_digest"
    elif field == "predecessor":
        target, name = value, "predecessor_coordinates"
        rejected = (rejected,)
    elif field == "sources":
        target, name = value, "sources"
        rejected = (rejected,)
    else:
        target = value.sources[0]
        name = {"contract": "contract", "role": "role", "path": "relative_path",
                "digest": "content_digest"}[field]
    original = object.__getattribute__(target, name)
    object.__setattr__(target, name, rejected)
    try:
        with pytest.raises((TypeError, ContractViolation)):
            encode_source_selection(value) if entrance == "encode" else value.to_wire()
        assert calls == []
    finally:
        object.__setattr__(target, name, original)
    assert encode_source_selection(value) == canonical_json_bytes(_independent_selection_wire(value))


def test_exact_byte_ceiling_is_checked_after_validation_on_every_public_call(monkeypatch):
    import aware_code_semantic_contract_runtime.source_selection as module

    value = selection(_expectation(object(), object()))
    body = canonical_json_bytes(_independent_selection_wire(value))
    with monkeypatch.context() as m:
        m.setattr(module, "MAX_SOURCE_SELECTION_BYTES", len(body))
        assert encode_source_selection(value) == body
        assert value.to_wire() == _independent_selection_wire(value)
        assert decode_source_selection(body) == value
        m.setattr(module, "MAX_SOURCE_SELECTION_BYTES", len(body) - 1)
        for call in (lambda: encode_source_selection(value), value.to_wire,
                     lambda: decode_source_selection(body)):
            with pytest.raises(ContractViolation):
                call()


@pytest.mark.parametrize("contextual", [False, True])
def test_production_projection_keeps_the_original_complete_digest(contextual):
    expected = _expectation(object(), object())
    contexts = ()
    if contextual:
        from test_contextual_semantic_input_producer import context

        contexts = (context(),)
    expected = inputs.SemanticInputProductionExpectation.create(
        use_ref=expected.use_ref, operation_ref=expected.operation_ref, stage=expected.stage,
        package_identity=expected.package_identity, operation_identity=expected.operation_identity,
        source_identity=expected.source_identity, source_coordinates=expected.source_coordinates,
        context_bodies=contexts)
    independent = {"operation_ref": expected.operation_ref,
        "package_identity": expected.package_identity.to_wire(),
        "source_coordinates": [x.to_wire() for x in expected.source_coordinates],
        "stage": expected.stage, "use_ref": expected.use_ref}
    if contexts:
        independent["contract"] = "aware.code.contextual-semantic-input-production.v2"
        independent["context_bodies"] = [x.coordinate.to_wire() for x in contexts]
    assert expected.input_digest == ContentDigest.of_bytes(canonical_json_bytes(independent))
    owner = _SourceValidator(expected.source_identity, expected.operation_identity)
    sources = owner.read_semantic_input_sources(expected.source_identity, expected=expected)
    value = inputs.SemanticInputProductionInput(
        expected.use_ref, expected.operation_ref, expected.stage, expected.package_identity,
        sources, expected.input_digest, contexts)
    assert tuple(x.source for x in value.sources) == expected.source_coordinates
    assert value.input_digest == expected.input_digest
    with pytest.raises(ContractViolation):
        replace(value, sources=())


@pytest.mark.parametrize("container", ["expectation", "input"])
def test_production_projection_revalidates_restamped_sources_before_any_behavior(container):
    expected = _expectation(object(), object())
    owner = _SourceValidator(expected.source_identity, expected.operation_identity)
    sources = owner.read_semantic_input_sources(expected.source_identity, expected=expected)
    value = inputs.SemanticInputProductionInput(
        expected.use_ref, expected.operation_ref, expected.stage, expected.package_identity,
        sources, expected.input_digest, expected.context_bodies)
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign coordinate behavior")

    coordinate = expected.source_coordinates[0] if container == "expectation" else value.sources[0].source
    original = coordinate.coordinate
    object.__setattr__(coordinate, "coordinate", Foreign())
    try:
        with pytest.raises(TypeError):
            expected.__post_init__() if container == "expectation" else value.__post_init__()
        assert calls == []
    finally:
        object.__setattr__(coordinate, "coordinate", original)
    expected.__post_init__()
    value.__post_init__()


@pytest.mark.parametrize("path", ["nested/\u00e9.aware", "a b/source.aware", "source.aware"])
def test_source_coordinate_reuses_the_original_candidate_path_grammar(path):
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        CodeSemanticCandidate,
    )

    coordinate = _expectation(object(), object()).source_coordinates[0].coordinate
    CodeSemanticCandidate(path, coordinate.digest)
    value = inputs.SemanticInputSourceCoordinate(path, coordinate)
    value.__post_init__()
    assert value.to_wire()["relative_path"] == path


@pytest.mark.parametrize("path", ["", "/root.aware", "a//b", "a/../b", "a/./b",
                                 "a\\b", "a/\x00b", "a/e\u0301.aware", "a/ ",
                                 "a/" + "x" * 256, "/".join(["x"] * 129)])
def test_source_coordinate_preserves_candidate_path_refusals(path):
    from aware_code_semantic_contract_runtime.semantic_candidates import (
        CodeSemanticCandidate,
    )

    coordinate = _expectation(object(), object()).source_coordinates[0].coordinate
    with pytest.raises(ContractViolation):
        CodeSemanticCandidate(path, coordinate.digest)
    with pytest.raises(ContractViolation):
        inputs.SemanticInputSourceCoordinate(path, coordinate)


@pytest.mark.parametrize("field", ["path", "digest", "digest_value"])
def test_source_coordinate_fresh_admission_rejects_foreign_fields_without_calls(field):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign coordinate behavior")

    value = _expectation(object(), object()).source_coordinates[0]
    target, name = ((value, "relative_path") if field == "path" else
                    (value.coordinate, "digest") if field == "digest" else
                    (value.coordinate.digest, "value"))
    original = object.__getattribute__(target, name)
    object.__setattr__(target, name, Foreign())
    try:
        for call in (value.__post_init__, value.to_wire):
            with pytest.raises((TypeError, ContractViolation)):
                call()
        assert calls == []
    finally:
        object.__setattr__(target, name, original)
    value.__post_init__()


@pytest.mark.parametrize("count", [0, 1, 17, 3500])
@pytest.mark.parametrize("contextual", [False, True])
def test_closed_input_json_projection_matches_the_complete_original_formula(count, contextual):
    original = _expectation(object(), object())
    coordinates = tuple(replace(original.source_coordinates[0],
        relative_path=f"nested/m{i:05d}-\u00e9.aware") for i in range(count))
    contexts = ()
    if contextual:
        from test_contextual_semantic_input_producer import context

        contexts = (context(),)
    payload = {"operation_ref": original.operation_ref,
        "package_identity": original.package_identity.to_wire(),
        "source_coordinates": [x.to_wire() for x in coordinates],
        "stage": original.stage, "use_ref": original.use_ref}
    if contexts:
        payload["contract"] = "aware.code.contextual-semantic-input-production.v2"
        payload["context_bodies"] = [x.coordinate.to_wire() for x in contexts]
    expected_digest = ContentDigest.of_bytes(canonical_json_bytes(payload))
    expected = inputs.SemanticInputProductionExpectation.create(
        use_ref=original.use_ref, operation_ref=original.operation_ref, stage=original.stage,
        package_identity=original.package_identity, operation_identity=original.operation_identity,
        source_identity=original.source_identity, source_coordinates=coordinates, context_bodies=contexts)
    assert expected.input_digest == expected_digest
    expected.__post_init__()
    sources = tuple(inputs.SemanticInputSourceBody(x, b"source-body") for x in coordinates)
    value = inputs.SemanticInputProductionInput(
        expected.use_ref, expected.operation_ref, expected.stage, expected.package_identity,
        sources, expected.input_digest, contexts)
    value.__post_init__()
    assert value.input_digest == expected_digest
    assert inputs._validated_production_payload_bytes(payload) == canonical_json_bytes(payload)
