"""Source-backed original bytes/refusals; no runtime, journal or evaluator."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from aware_ontology_object_facade_client import owner_values as owner
from aware_ontology_object_facade_client import topology_values as topology

OWNER_PATH = "workspaces/aware_kernel/modules/ontology/libs/object_facade_client/python/aware_ontology_object_facade_client/owner_values.py"


@pytest.fixture(scope="module")
def original():
    root = Path(__file__).resolve().parents[8]
    body = subprocess.check_output(
        ["git", "show", "e7f6d2a9efbe:" + OWNER_PATH], cwd=root
    )
    names = {
        "normalize_json",
        "canonical_json",
        "_attempt_normalize",
        "attempt_canonical_bytes",
        "decode_attempt_canonical_bytes",
        "_attempt_object_pairs",
        "_attempt_error",
    }
    nodes = [
        n
        for n in ast.parse(body).body
        if isinstance(n, ast.FunctionDef) and n.name in names
    ]
    assert len(nodes) == len(names)
    # The oracle is the complete original pure encoding bodies, not a backend
    # substitute. Original public exception classes and stock JSON are retained.
    namespace = {
        "json": json,
        "cast": cast,
        "Any": Any,
        "JsonScalar": owner.JsonScalar,
        "OntologyRuntimeEncodingError": owner.OntologyRuntimeEncodingError,
        "OntologyObjectOperationAttemptCodecError": owner.OntologyObjectOperationAttemptCodecError,
        "_attempt_call": lambda op, *a, **kw: op(*a, **kw),
    }
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0
            ),
            *nodes,
        ],
        type_ignores=[],
    )
    exec(  # noqa: S102 -- exact published pure function preimages only
        compile(ast.fix_missing_locations(module), "<original-pure-encoding>", "exec"),
        namespace,
    )
    return namespace


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"key": [False, 1, None, "é", "𐐀", "a\nb"]},
        {"key": (1, {"nested": "value"}), "long": "x" * 70000},
        {"key": '"\\\u0000\u2028'},
        {"key": "a\ud800b"},
        {"key": " padded"},
        {"key": 1.0},
        {1: "key"},
        {"": 1},
    ],
)
def test_original_canonical_bytes_and_refusals_match(original, value):
    try:
        expected = original["attempt_canonical_bytes"](value)
    except (TypeError, ValueError, UnicodeError) as failure:
        with pytest.raises(type(failure)):
            owner.attempt_canonical_bytes(value)
    else:
        assert owner.attempt_canonical_bytes(value) == expected
        assert owner.decode_attempt_canonical_bytes(expected) == original[
            "decode_attempt_canonical_bytes"
        ](expected)


@pytest.mark.parametrize(
    "body",
    [
        b'{"x":1,"x":2}',
        b'{ "x":1}',
        b'{"x":1.0}',
        b'{"x":NaN}',
        b'{"x":" padded"}',
        b"[]",
        b"\xff",
        b'{"x":"\\ud800"}',
    ],
)
def test_original_decode_refusals_match(original, body):
    with pytest.raises((TypeError, ValueError, UnicodeError)) as expected:
        original["decode_attempt_canonical_bytes"](body)
    with pytest.raises(type(expected.value)):
        owner.decode_attempt_canonical_bytes(body)


def test_every_unicode_codepoint_keeps_original_canonical_bytes(original):
    value = {
        "unicode": "x"
        + "".join(chr(i) for i in range(0x110000) if not 0xD800 <= i <= 0xDFFF)
        + "x"
    }
    assert owner.attempt_canonical_bytes(value) == original["attempt_canonical_bytes"](
        value
    )


def test_owned_normalization_snapshot_is_not_the_callers_mutable_graph():
    value = {"key": [1, 2, 3]}
    expected = b'{"key":[1,2,3]}'
    code = owner._attempt_normalize.__wrapped__.__code__
    observed = []

    def returned(frame, event, result):
        if (
            event == "return"
            and frame.f_code is code
            and frame.f_locals.get("value") is value
        ):
            observed.append(True)
            value["key"] = [object()]

    previous = sys.getprofile()
    try:
        sys.setprofile(returned)
        assert owner.attempt_canonical_bytes(value) == expected
    finally:
        sys.setprofile(previous)
    assert observed == [True]


def test_module_mutation_after_normalization_refuses_before_next_dispatch(monkeypatch):
    value = {"key": [1, 2, 3]}
    code = owner._attempt_normalize.__wrapped__.__code__
    observed, foreign_calls = [], []

    def foreign(*args, **kwargs):
        foreign_calls.append(True)
        raise AssertionError("foreign serializer ran")

    def returned(frame, event, result):
        if (
            event == "return"
            and frame.f_code is code
            and frame.f_locals.get("value") is value
            and not observed
        ):
            observed.append(True)
            monkeypatch.setattr(json, "dumps", foreign)

    previous = sys.getprofile()
    try:
        sys.setprofile(returned)
        with pytest.raises((TypeError, ValueError)):
            owner.attempt_canonical_bytes(value)
    finally:
        sys.setprofile(previous)
    assert observed == [True] and foreign_calls == []


def test_normalized_encoder_does_not_admit_a_serializer_or_callback_port():
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign JSON encoder")

    # The original dispatcher still refuses direct json.dumps selection; the
    # new retained helper has fixed options and cannot accept an encoder hook.
    with pytest.raises((TypeError, ValueError)):
        owner._attempt_call(json.dumps, {"key": 1})
    with pytest.raises((TypeError, ValueError)):
        owner._attempt_encode_normalized({"key": 1}, cls=foreign)
    assert calls == []


@pytest.mark.parametrize("decode", [False, True])
def test_one_strict_normalization_and_no_general_json_renormalization(decode):
    strict = owner._attempt_normalize.__wrapped__.__code__
    seen = {"strict": 0, "general": 0}

    def calls(frame, event, result):
        if event == "call":
            if frame.f_code is strict:
                seen["strict"] += 1
            if (
                frame.f_code.co_name == "normalize_json"
                and frame.f_code.co_filename == owner.__file__
            ):
                seen["general"] += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(calls)
        if decode:
            assert owner.decode_attempt_canonical_bytes(b'{"data":[1,2,3]}') == {
                "data": [1, 2, 3]
            }
        else:
            assert (
                owner.attempt_canonical_bytes({"data": [1, 2, 3]})
                == b'{"data":[1,2,3]}'
            )
    finally:
        sys.setprofile(previous)
    assert seen == {"strict": 5, "general": 0}


def graph_binding():
    return topology.GraphTypeBinding(
        type_ref="demo.Type",
        identity_mode=topology.GraphIdentityMode.SCHEMA_FIELDS,
        identity_field_refs=("demo.Type.id",),
        schema_relationship_field_refs=(),
        association_role_refs=(),
    )


def test_revalidation_reuses_one_live_class_view_not_record_or_admission():
    value = graph_binding()
    seen = []

    def returned(frame, event, result):
        if (
            event == "c_call"
            and result is vars
            and frame.f_code.co_filename == topology.__file__
        ):
            seen.append(True)

    previous = sys.getprofile()
    try:
        sys.setprofile(returned)
        copied = topology._revalidate(value)
    finally:
        sys.setprofile(previous)
    assert copied is not value and type(copied) is type(value)
    assert copied.to_wire() == value.to_wire()
    assert len(seen) == 1


def test_live_class_view_still_refuses_substitution_on_native_return(monkeypatch):
    value = graph_binding()
    seen = []

    def returned(frame, event, result):
        if (
            event == "c_return"
            and result is vars
            and frame.f_code.co_filename == topology.__file__
            and not seen
        ):
            seen.append(True)
            monkeypatch.setattr(
                topology.GraphTypeBinding, "__module__", "foreign.module"
            )

    previous = sys.getprofile()
    try:
        sys.setprofile(returned)
        with pytest.raises(TypeError):
            topology._revalidate(value)
    finally:
        sys.setprofile(previous)
    assert seen == [True]
