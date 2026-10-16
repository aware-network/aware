"""Original V3 integrity is complete, nonportable and behavior-free."""

import copy
from dataclasses import fields, is_dataclass

import pytest

# isort: split
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.retained_declaration_scope_validation import (
    capture_retained_declaration_scope,
    validate_detached_declaration_scope_coordinate,
    validate_retained_declaration_scope_coordinate,
)

# isort: split
from test_retained_declaration_scope import fixture


def test_complete_original_matches_canonical_commitment_without_reencoding(monkeypatch):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_codec as codec,
    )

    value = fixture()
    expected = value.closure_digest.value
    coordinate = capture_retained_declaration_scope(value)
    assert coordinate.digest == expected
    assert coordinate.original is value

    def forbidden(*args):
        pytest.fail("original validation reencoded V3")

    monkeypatch.setattr(codec, "declaration_closure_payload_bytes", forbidden)
    for _ in range(3):
        validate_retained_declaration_scope_coordinate(coordinate, value)


def test_coordinate_covers_every_original_dataclass_field():
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    seen = set()

    def verify(item):
        if type(item) is tuple:
            for child in item:
                verify(child)
        elif is_dataclass(item) and id(item) not in seen:
            seen.add(id(item))
            (record,) = [row for row in coordinate.records if row.original is item]
            assert tuple(name for name, _, _ in record.fields) == tuple(f.name for f in fields(item))
            for name, _, child in record.fields:
                assert getattr(item, name) is child
                verify(child)

    verify(value)
    assert len(seen) == len(coordinate.records)


@pytest.mark.parametrize("record_index,field_index", [
    (i, j)
    for i, record in enumerate(capture_retained_declaration_scope(fixture()).records)
    for j in range(len(record.fields))
])
@pytest.mark.parametrize("detached", [False, True])
def test_every_original_field_is_checked_without_hostile_dispatch(record_index, field_index, detached):
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    actual = copy.deepcopy(value) if detached else value
    actual_coordinate = capture_retained_declaration_scope(actual) if detached else coordinate
    record = actual_coordinate.records[record_index]
    validate = validate_detached_declaration_scope_coordinate if detached else validate_retained_declaration_scope_coordinate
    name, _, original = record.fields[field_index]
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign attribute")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality")

    object.__setattr__(record.original, name, Hostile())
    with pytest.raises(ContractViolation):
        validate(coordinate, actual)
    assert calls == []
    object.__setattr__(record.original, name, original)
    # Integrity alone is not an operation-lifetime or terminal-state issuer.
    validate(coordinate, actual)


def test_copy_and_equal_tuple_substitution_refuse():
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    with pytest.raises(ContractViolation, match="original declaration coordinate"):
        validate_retained_declaration_scope_coordinate(coordinate, copy.deepcopy(value))
    original = value.scopes
    substitute = tuple(item for item in original)
    assert substitute == original and substitute is not original
    object.__setattr__(value, "scopes", substitute)
    with pytest.raises(ContractViolation, match="field changed"):
        validate_retained_declaration_scope_coordinate(coordinate, value)


def test_foreign_metaclass_and_descriptor_refuse_without_behavior(monkeypatch):
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    calls = []

    class HostileMeta(type):
        def __eq__(cls, other):
            calls.append("meta equality")
            raise AssertionError

        def __hash__(cls):
            calls.append("meta hash")
            raise AssertionError

    class Foreign(metaclass=HostileMeta):
        pass

    object.__setattr__(value, "consumer_scope_key", Foreign())
    with pytest.raises(ContractViolation, match="foreign declaration field"):
        capture_retained_declaration_scope(value)
    assert calls == []
    original = coordinate.records[0].fields[0][2]
    object.__setattr__(value, "consumer_scope_key", original)

    class Descriptor:
        def __get__(self, instance, owner):
            calls.append("descriptor")
            raise AssertionError

    monkeypatch.setattr(type(value), "consumer_scope_key", Descriptor())
    for call in (lambda: capture_retained_declaration_scope(value),
                 lambda: validate_retained_declaration_scope_coordinate(coordinate, value)):
        with pytest.raises(ContractViolation, match="slot changed"):
            call()
    assert calls == []


def test_coordinate_is_immutable_and_invalid_semantics_still_refuse():
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    with pytest.raises(AttributeError):
        object.__setattr__(coordinate, "digest", "restamped")
    object.__setattr__(value, "consumer_scope_key", "missing")
    with pytest.raises(ContractViolation):
        capture_retained_declaration_scope(value)


def test_detached_exact_equal_values_keep_canonical_digest_and_reject_coherent_changes():
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    detached = copy.deepcopy(value)
    validate_detached_declaration_scope_coordinate(coordinate, detached)
    assert detached.closure_digest.value == coordinate.digest
    object.__setattr__(detached.scopes[0], "workspace_handle", "Other")
    changed_digest = detached.closure_digest.value
    assert changed_digest != coordinate.digest
    with pytest.raises(ContractViolation, match="field changed"):
        validate_detached_declaration_scope_coordinate(coordinate, detached)


def test_detached_foreign_tuple_and_equality_substitutes_have_zero_calls():
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    detached = copy.deepcopy(value)
    calls = []

    class HostileTuple(tuple):
        def __len__(self):
            calls.append("len")
            raise AssertionError

        def __iter__(self):
            calls.append("iter")
            raise AssertionError

    object.__setattr__(detached, "scopes", HostileTuple(detached.scopes))
    with pytest.raises(ContractViolation, match="tuple changed"):
        validate_detached_declaration_scope_coordinate(coordinate, detached)
    assert calls == []


@pytest.mark.parametrize("detached", [False, True])
def test_restamped_nested_class_is_rejected_before_attribute_behavior(detached):
    value = fixture()
    coordinate = capture_retained_declaration_scope(value)
    actual = copy.deepcopy(value) if detached else value
    body = actual.repository_manifest
    original_class = type(body)
    calls = []

    class Foreign:
        __slots__ = original_class.__slots__

        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute dispatch")

    object.__setattr__(body, "__class__", Foreign)
    validate = validate_detached_declaration_scope_coordinate if detached else validate_retained_declaration_scope_coordinate
    try:
        with pytest.raises(ContractViolation, match="class changed"):
            validate(coordinate, actual)
        assert calls == []
    finally:
        object.__setattr__(body, "__class__", original_class)
