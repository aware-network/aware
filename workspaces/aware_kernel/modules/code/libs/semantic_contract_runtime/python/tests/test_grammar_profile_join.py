"""Portable input correspondence through the original registered Code executor.

Source owners and packages here are explicit synthetic fixtures, not Workspace
supplier admission or Language contribution-production qualification.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

import aware_code_semantic_contract_runtime as public
import pytest
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    validate_grammar_source_group_input,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
    MAX_GROUP_BYTES,
    CodeGrammarSourceEdgeV1,
    decode_grammar_source_group,
    grammar_source_group_body,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.source_origin import decode_source_origin
from test_grammar_source_group import Poison
from test_grammar_source_group import packet as packet
from test_semantic_input_producer import _body

ERRORS = (ContractViolation, TypeError)


def group_fixture(packet, index=0):
    return decode_grammar_source_group(
        bytes.fromhex(packet["vectors"][index]["body_hex"])
    )


def input_fixture(
    group, *, contexts=None, sources=None, identity=None, use_ref="fixture:group-input"
):
    root = next(
        member
        for member in group.members
        if member.occurrence_ref == group.root_occurrence_ref
    )
    origin = decode_source_origin(bytes.fromhex(root.origin_body_hex))
    sources = (
        sources
        if sources is not None
        else tuple(
            inputs.SemanticInputSourceBody(
                inputs.SemanticInputSourceCoordinate(
                    item.relative_path, item.coordinate
                ),
                bytes.fromhex(item.body_hex),
            )
            for item in root.sources
        )
    )
    expected = inputs.SemanticInputProductionExpectation.create(
        use_ref=use_ref,
        operation_ref="fixture:grammar-operation",
        stage="fixture:grammar-input",
        package_identity=identity
        or inputs.SemanticInputPackageIdentity(origin.package, "fixture:package"),
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(item.source for item in sources),
        context_bodies=(grammar_source_group_body(group),)
        if contexts is None
        else contexts,
    )
    value = inputs.SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        sources,
        expected.input_digest,
        expected.context_bodies,
    )
    return value, expected


@pytest.mark.parametrize("index", [0, 1])
def test_complete_input_golden_root_and_context_match(packet, index):
    group = group_fixture(packet, index)
    value, _ = input_fixture(group)
    assert validate_grammar_source_group_input(group, input=value) is None
    assert (
        public.validate_grammar_source_group_input
        is validate_grammar_source_group_input
    )
    assert not hasattr(value, "source_identity")


def test_other_contexts_are_preserved_and_package_name_is_original_owner_check(packet):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    original = value.context_bodies[0]
    extra = replace(
        original,
        coordinate=replace(
            original.coordinate,
            role="z_extra",
            contract=replace(GRAMMAR_SOURCE_GROUP_REF, key="fixture:extra"),
        ),
    )
    identity = replace(value.package_identity, package_name="fixture:different-name")
    value, _ = input_fixture(group, contexts=(original, extra), identity=identity)
    assert validate_grammar_source_group_input(group, input=value) is None
    assert value.context_bodies[1] is extra
    assert value.package_identity.package_name == "fixture:different-name"


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "wrong_role",
        "wrong_contract",
        "wrong_ref",
        "extra_same_contract",
        "different_bytes",
    ],
)
def test_context_substitution_refuses_even_with_valid_recomputed_input_digest(
    packet, kind
):
    group = group_fixture(packet)
    body = grammar_source_group_body(group)
    if kind == "missing":
        bodies = ()
    elif kind == "wrong_role":
        bodies = (
            replace(body, coordinate=replace(body.coordinate, role="not_the_group")),
        )
    elif kind == "wrong_contract":
        bodies = (
            replace(
                body,
                coordinate=replace(
                    body.coordinate,
                    contract=replace(GRAMMAR_SOURCE_GROUP_REF, version="2"),
                ),
            ),
        )
    elif kind == "wrong_ref":
        bodies = (
            replace(
                body,
                coordinate=replace(body.coordinate, value_ref="fixture:substitute"),
            ),
        )
    elif kind == "extra_same_contract":
        bodies = (
            body,
            replace(body, coordinate=replace(body.coordinate, role="z_group")),
        )
    else:
        ref = group.root_occurrence_ref
        other = replace(
            group,
            dependency_edges=(
                CodeGrammarSourceEdgeV1(ref, ref, "opaque", "fixture:extra"),
            ),
        )
        bodies = (grammar_source_group_body(other),)
    value, _ = input_fixture(group, contexts=bodies)
    with pytest.raises(ContractViolation):
        validate_grammar_source_group_input(group, input=value)


@pytest.mark.parametrize("field", ["package_ref", "package_kind", "manifest_digest"])
def test_complete_root_package_not_label_or_digest_only(packet, field):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    replacement = (
        ContentDigest.of_bytes(b"foreign manifest")
        if field == "manifest_digest"
        else "fixture:foreign"
    )
    identity = replace(
        value.package_identity,
        package=replace(value.package_identity.package, **{field: replacement}),
    )
    foreign, _ = input_fixture(group, identity=identity)
    with pytest.raises(ContractViolation):
        validate_grammar_source_group_input(group, input=foreign)


@pytest.mark.parametrize(
    "field", ["path", "role", "contract", "value_ref", "body", "missing", "extra"]
)
def test_complete_root_sources_not_just_equal_content(packet, field):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    body = value.sources[0]
    if field == "missing":
        sources = ()
    elif field == "extra":
        sources = (
            body,
            replace(
                body, source=replace(body.source, relative_path="z_extra.syntax.json")
            ),
        )
    else:
        source = body.source
        if field == "path":
            body = replace(
                body, source=replace(source, relative_path="foreign.syntax.json")
            )
        elif field == "body":
            raw = b"different original bytes"
            coordinate = replace(
                source.coordinate,
                digest=ContentDigest.of_bytes(raw),
                size_bytes=len(raw),
            )
            body = inputs.SemanticInputSourceBody(
                replace(source, coordinate=coordinate), raw
            )
        else:
            replacement = (
                replace(source.coordinate.contract, version="2")
                if field == "contract"
                else "fixture:foreign"
            )
            body = replace(
                body,
                source=replace(
                    source,
                    coordinate=replace(source.coordinate, **{field: replacement}),
                ),
            )
        sources = (body,)
    foreign, _ = input_fixture(group, sources=sources)
    with pytest.raises(ContractViolation):
        validate_grammar_source_group_input(group, input=foreign)


def test_recomputed_coherent_input_cannot_select_other_equal_byte_occurrence(packet):
    group = group_fixture(packet, 1)
    value, _ = input_fixture(group)
    other_root = next(
        member.occurrence_ref
        for member in group.members
        if member.occurrence_ref != group.root_occurrence_ref
    )
    edges = tuple(
        sorted(
            group.dependency_edges
            + (
                CodeGrammarSourceEdgeV1(
                    other_root, group.root_occurrence_ref, "opaque", "fixture:reverse"
                ),
            ),
            key=lambda edge: tuple(
                item.encode()
                for item in (
                    edge.owner_occurrence_ref,
                    edge.target_occurrence_ref,
                    edge.dependency_kind,
                    edge.dependency_ref,
                )
            ),
        )
    )
    other = replace(group, root_occurrence_ref=other_root, dependency_edges=edges)
    with pytest.raises(ContractViolation):
        validate_grammar_source_group_input(other, input=value)
    # A coherent *detached* pair remains portable data, not proof of original selection.
    detached, _ = input_fixture(other)
    validate_grammar_source_group_input(other, input=detached)


@pytest.mark.parametrize("field", ["use_ref", "operation_ref", "stage", "input_digest"])
def test_complete_input_digest_is_freshly_revalidated(packet, field):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    replacement = (
        ContentDigest.of_bytes(b"wrong digest")
        if field == "input_digest"
        else "fixture:changed"
    )
    object.__setattr__(value, field, replacement)
    with pytest.raises(ContractViolation):
        validate_grammar_source_group_input(group, input=value)


@pytest.mark.parametrize(
    "target,field",
    [
        ("input", "use_ref"),
        ("input", "operation_ref"),
        ("input", "stage"),
        ("input", "package_identity"),
        ("input", "sources"),
        ("input", "input_digest"),
        ("input", "context_bodies"),
        ("identity", "package"),
        ("identity", "package_name"),
        ("package", "package_ref"),
        ("package", "package_kind"),
        ("package", "manifest_digest"),
        ("source_body", "source"),
        ("source_body", "canonical_body"),
        ("source", "relative_path"),
        ("source", "coordinate"),
        ("context", "coordinate"),
        ("context", "canonical_body"),
    ],
)
def test_forged_input_graph_refuses_before_foreign_callbacks(packet, target, field):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    node = {
        "input": value,
        "identity": value.package_identity,
        "package": value.package_identity.package,
        "source_body": value.sources[0],
        "source": value.sources[0].source,
        "context": value.context_bodies[0],
    }[target]
    object.__setattr__(node, field, Poison())
    with pytest.raises(ERRORS):
        validate_grammar_source_group_input(group, input=value)


@pytest.mark.parametrize("kind", ["foreign", "subclass", "uninitialized"])
def test_input_exact_type_and_slot_presence_required(packet, kind):
    group = group_fixture(packet)
    cls = inputs.SemanticInputProductionInput
    if kind == "foreign":
        value = Poison()
    else:
        if kind == "subclass":
            cls = type("ForeignInput", (cls,), {"__post_init__": lambda self: None})
        value = object.__new__(cls)
    with pytest.raises(ERRORS):
        validate_grammar_source_group_input(group, input=value)


@pytest.mark.parametrize(
    "field", ["role", "value_ref", "contract", "digest", "size_bytes"]
)
def test_nested_source_coordinate_refuses_foreign_field_before_callback(packet, field):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    coordinate = replace(value.sources[0].source.coordinate)
    object.__setattr__(value.sources[0].source, "coordinate", coordinate)
    object.__setattr__(coordinate, field, Poison())
    with pytest.raises(ERRORS):
        validate_grammar_source_group_input(group, input=value)


@pytest.mark.parametrize(
    "kind", ["source_count", "context_count", "context_bytes", "source_bytes"]
)
def test_input_bounds_checked_before_original_validation(packet, kind):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    if kind == "source_count":
        object.__setattr__(value, "sources", value.sources * 16385)
    elif kind == "context_count":
        object.__setattr__(value, "context_bodies", value.context_bodies * 65)
    elif kind == "context_bytes":
        object.__setattr__(
            value.context_bodies[0], "canonical_body", b"x" * (MAX_GROUP_BYTES + 1)
        )
    else:
        object.__setattr__(
            value.sources[0], "canonical_body", b"x" * (MAX_GROUP_BYTES + 1)
        )
    with pytest.raises(ContractViolation, match="bound"):
        validate_grammar_source_group_input(group, input=value)


def test_root_source_aggregate_bound_precedes_original_hashing(packet, monkeypatch):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    first = replace(value.sources[0], source=replace(value.sources[0].source))
    raw = b"x" * (MAX_GROUP_BYTES // 2 + 1)
    object.__setattr__(first, "canonical_body", raw)
    object.__setattr__(value, "sources", (first, first))

    def unreachable(self):
        raise AssertionError(
            "original input validator entered after source bound exceeded"
        )

    monkeypatch.setattr(
        inputs.SemanticInputProductionInput, "__post_init__", unreachable
    )
    with pytest.raises(ContractViolation, match="bound"):
        validate_grammar_source_group_input(group, input=value)


def test_original_context_budget_is_shared_with_all_other_bodies(packet):
    group = group_fixture(packet)
    value, _ = input_fixture(group)
    first = value.context_bodies[0]
    raw = b"x" * (MAX_GROUP_BYTES - len(first.canonical_body))
    second = SemanticBody(
        replace(
            first.coordinate,
            role="z_extra",
            contract=replace(GRAMMAR_SOURCE_GROUP_REF, key="fixture:extra"),
            digest=ContentDigest.of_bytes(raw),
            size_bytes=len(raw),
        ),
        raw,
    )
    object.__setattr__(value, "context_bodies", (first, second))
    with pytest.raises(ContractViolation, match="budget"):
        validate_grammar_source_group_input(group, input=value)


class FixtureSourceOwner:
    """Synthetic original source owner; no Workspace receipt is fabricated."""

    def __init__(self, value, expected):
        self.source_identity = expected.source_identity
        self.operation_identity = expected.operation_identity
        self.identity = expected.package_identity
        self.sources = value.sources
        self.contexts = tuple(
            (body.coordinate, body.canonical_body) for body in value.context_bodies
        )
        self.live = True
        self.source_calls = 0
        self.context_calls = 0

    def validate_semantic_input_source(self, source_admission, *, expected):
        self.source_calls += 1
        if (
            not self.live
            or source_admission is not self.source_identity
            or expected.source_identity is not self.source_identity
            or expected.operation_identity is not self.operation_identity
            or expected.package_identity != self.identity
            or expected.source_coordinates
            != tuple(body.source for body in self.sources)
        ):
            raise ContractViolation("fixture original source unavailable")

    def read_semantic_input_sources(self, source_admission, *, expected):
        self.validate_semantic_input_source(source_admission, expected=expected)
        return self.sources

    def validate_semantic_input_context(self, source_admission, *, expected):
        self.validate_semantic_input_source(source_admission, expected=expected)
        self.context_calls += 1
        if (
            tuple(
                (body.coordinate, body.canonical_body)
                for body in expected.context_bodies
            )
            != self.contexts
        ):
            raise ContractViolation("fixture original context unavailable")


def original_registration(host, owner, produce):
    result = _body()
    roles = {
        body.source.coordinate.role: body.source.coordinate.contract
        for body in owner.sources
    }
    declaration = inputs.SemanticInputProducerDeclaration(
        "fixture:group-correspondence",
        "fixture:group-profile",
        SemanticImplementationCoordinate(
            "fixture:group-owner", ContentDigest.of_bytes(b"fixture implementation")
        ),
        SemanticConfigurationCoordinate(
            "fixture:group-configuration",
            ContentDigest.of_bytes(b"fixture configuration"),
        ),
        tuple(
            inputs.SemanticInputSourceContract(role, contract)
            for role, contract in sorted(roles.items())
        ),
        result.coordinate.role,
        result.coordinate.contract,
        context_contracts=(
            inputs.SemanticInputContextContract(
                "grammar_source_group", GRAMMAR_SOURCE_GROUP_REF
            ),
        ),
    )
    return inputs.register_semantic_input_producer(
        host,
        declaration=declaration,
        producer=produce,
        validator=owner,
        validator_entrance=owner.validate_semantic_input_source,
        reader=owner,
        reader_entrance=owner.read_semantic_input_sources,
        context_validator_entrance=owner.validate_semantic_input_context,
        retain_result=True,
    )


@pytest.mark.asyncio
async def test_real_registered_code_execution_retention_and_cleanup(packet):
    group = group_fixture(packet, 1)
    value, expected = input_fixture(group)
    owner = FixtureSourceOwner(value, expected)
    host = inputs.SemanticInputProducerHost()
    seen = []

    async def produce(value):
        validate_grammar_source_group_input(group, input=value)
        seen.append(value)
        return _body()

    registration = original_registration(host, owner, produce)
    try:
        result = await inputs.execute_registered_semantic_input(
            host,
            registration,
            source_admission=owner.source_identity,
            expected=expected,
        )
        assert len(seen) == 1 and owner.context_calls >= 3
        assert result == _body()
        inputs.validate_registered_semantic_input_result(
            host,
            registration,
            source_admission=owner.source_identity,
            expected=expected,
            result=result,
        )
        with pytest.raises(ContractViolation):
            inputs.validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=expected,
                result=replace(result),
            )
        inputs.release_registered_semantic_input_result(
            host,
            registration,
            source_admission=owner.source_identity,
            expected=expected,
            result=result,
        )
        with pytest.raises(ContractViolation):
            inputs.validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=expected,
                result=result,
            )
    finally:
        host.close()
    assert owner.live is True


@pytest.mark.asyncio
async def test_coherent_detached_context_does_not_grant_original_admission_or_retry(
    packet,
):
    group = group_fixture(packet)
    value, expected = input_fixture(group)
    owner = FixtureSourceOwner(value, expected)
    ref = group.root_occurrence_ref
    other = replace(
        group,
        dependency_edges=(
            CodeGrammarSourceEdgeV1(ref, ref, "opaque", "fixture:new-edge"),
        ),
    )
    coherent, detached = input_fixture(other)
    validate_grammar_source_group_input(other, input=coherent)
    foreign = replace(
        expected,
        context_bodies=detached.context_bodies,
        input_digest=detached.input_digest,
    )
    calls = []
    host = inputs.SemanticInputProducerHost()
    registration = original_registration(
        host, owner, lambda value: calls.append(value) or _body()
    )
    try:
        with pytest.raises(ContractViolation):
            await inputs.execute_registered_semantic_input(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=foreign,
            )
        assert calls == []
        with pytest.raises(ContractViolation, match="consumed"):
            await inputs.execute_registered_semantic_input(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=expected,
            )
    finally:
        host.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["source_lifetime", "context", "input_digest", "cancellation"]
)
async def test_changes_across_await_refuse_without_cached_success(packet, change):
    group = group_fixture(packet)
    value, expected = input_fixture(group)
    owner = FixtureSourceOwner(value, expected)
    host = inputs.SemanticInputProducerHost()

    async def produce(value):
        validate_grammar_source_group_input(group, input=value)
        await asyncio.sleep(0)
        if change == "source_lifetime":
            owner.live = False
        elif change == "context":
            owner.contexts = ()
        elif change == "input_digest":
            object.__setattr__(
                value, "input_digest", ContentDigest.of_bytes(b"changed")
            )
            validate_grammar_source_group_input(group, input=value)
        else:
            raise asyncio.CancelledError()
        return _body()

    registration = original_registration(host, owner, produce)
    try:
        with pytest.raises((ContractViolation, asyncio.CancelledError)):
            await inputs.execute_registered_semantic_input(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=expected,
            )
        owner.live = True
        owner.contexts = tuple(
            (body.coordinate, body.canonical_body) for body in expected.context_bodies
        )
        with pytest.raises(ContractViolation, match="consumed"):
            await inputs.execute_registered_semantic_input(
                host,
                registration,
                source_admission=owner.source_identity,
                expected=expected,
            )
    finally:
        host.close()
