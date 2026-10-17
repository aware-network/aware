"""Aggregated optimizations preserve the literal original codec contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
import types
from dataclasses import asdict, fields, replace
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
import test_repository_tree_projection_contract as cases
from aware_workspace_sdk import repository_tree_projection_codec as codec
from aware_workspace_sdk import repository_tree_projection_values as values


@pytest.fixture(scope="module")
def predecessor():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    path = "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py"
    body = subprocess.run(
        ["git", "show", "8be9c5aa6dcfa7dceb6b6aebb14f2fcbdae35bc7:" + path],
        cwd=root,
        capture_output=True,
        check=True,
    ).stdout
    assert (
        hashlib.sha256(body).hexdigest()
        == "8b63a112403720a07b9be561fab9cacdde10383181cd765abdb5fde19067a268"
    )
    module = types.ModuleType("aware_workspace_sdk._aggregate_predecessor")
    module.__package__ = "aware_workspace_sdk"
    exec(compile(body, "<literal-aggregate-predecessor>", "exec"), vars(module))  # noqa: S102
    return module


def outcome(module, value):
    try:
        return "ok", module.repository_tree_projection_value_to_json(value)
    except Exception as error:  # noqa: BLE001 -- literal predecessor outcome parity
        return type(error).__name__, str(error)


def resign(value):
    payload = asdict(value)
    del payload["binding_ref"]
    body = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return replace(
        value, binding_ref="sha256:" + hashlib.sha256(body.encode()).hexdigest()
    )


@pytest.mark.parametrize("value", cases.examples())
def test_complete_wire_digest_and_roundtrip_parity(predecessor, value):
    text = predecessor.repository_tree_projection_value_to_json(value)
    assert codec.repository_tree_projection_value_to_json(value) == text
    assert codec.repository_tree_projection_value_digest(
        value
    ) == predecessor.repository_tree_projection_value_digest(value)
    assert codec.repository_tree_projection_value_from_json(
        type(value), text
    ) == predecessor.repository_tree_projection_value_from_json(type(value), text)


@pytest.mark.parametrize(
    "text",
    [
        "ordinary",
        "é漢🙂",
        'x,"binding_ref":"bad","effect_paths":[]',
        "\\\n\t\u0000",
        '"' * 40,
    ],
)
def test_commitment_removes_only_the_exact_top_level_member(predecessor, text):
    value = resign(replace(cases.binding(), plan_ref=text, layout_ref=text))
    assert outcome(codec, value) == outcome(predecessor, value)
    wrong = replace(value, binding_ref=text)
    assert outcome(codec, wrong) == outcome(predecessor, wrong)


@pytest.mark.parametrize("kind", ["CREATE", "UPDATE", "DELETE"])
def test_one_fresh_sequence_wire_per_operand(monkeypatch, kind):
    value = cases.binding(kind=kind)
    calls = []
    original = codec._wire

    def measure(payload):
        calls.append(payload)
        return original(payload)

    monkeypatch.setattr(codec, "_wire", measure)
    codec.repository_tree_projection_value_validate_equal(value, expected_value=value)
    assert len(calls) == 2
    assert calls[0] is not calls[1]
    assert all(row["binding_ref"] == value.binding_ref for row in calls)


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_exact_requested_metadata_boundary_preserved(predecessor, delta):
    value = cases.binding()
    size = len(codec.repository_tree_projection_value_to_json(value).encode())
    # The limit digits can alter the commitment envelope; find its fixed point.
    maximum = size
    for _ in range(4):
        trial = resign(
            replace(value, limits=replace(value.limits, maximum_metadata_bytes=maximum))
        )
        maximum = len(predecessor._wire(asdict(trial)).encode())
    trial = resign(
        replace(
            value, limits=replace(value.limits, maximum_metadata_bytes=maximum + delta)
        )
    )
    assert outcome(codec, trial) == outcome(predecessor, trial)


@pytest.mark.parametrize(
    "field", [f.name for f in fields(values.WorkspaceTreeProjectionBinding)]
)
def test_every_binding_field_refusal_and_commitment_order(predecessor, field):
    original = cases.binding()
    for bad in (None, False, 0, "", (), object()):
        value = replace(original, **{field: bad})
        assert outcome(codec, value) == outcome(predecessor, value), (field, bad)


@pytest.mark.parametrize("example", cases.examples())
def test_compiled_enums_keep_type_depth_and_error_order(predecessor, example):
    for field, hint in get_type_hints(type(example)).items():
        if get_origin(hint) is not Literal:
            continue
        for item in (*get_args(hint), None, False, 7, "unknown", b"CREATE"):
            value = replace(example, **{field: item})
            assert outcome(codec, value) == outcome(predecessor, value), (
                type(example),
                field,
                item,
            )


def test_substituted_compiled_enum_converter_never_runs(monkeypatch):
    value = cases.binding().files[0]
    key = id(type(value))
    calls = []

    def foreign(*args):
        calls.append(args)
        return {}

    entry = codec._NATIVE_FIELDS_BY_ID[key]
    monkeypatch.setitem(
        codec._NATIVE_FIELDS_BY_ID,
        key,
        (entry[0], entry[1], (foreign, foreign.__code__)),
    )
    with pytest.raises(codec.WorkspaceTreeProjectionValueError):
        codec.repository_tree_projection_value_to_payload(value)
    assert not calls


@pytest.mark.parametrize("maximum", [1, 2, 3, 5, 12, 13, 14, 4096])
@pytest.mark.parametrize(
    "path", ["pkg/output.py", "pkg/é.py", "pkg/漢.py", "pkg/🙂.py"]
)
def test_fresh_child_path_and_narrower_sequence_limit(predecessor, maximum, path):
    value = cases.binding()
    row = replace(value.files[0], path=path)
    value = resign(
        replace(
            value,
            files=(row,),
            effect_paths=("pkg", path),
            limits=replace(value.limits, maximum_path_utf8_bytes=maximum),
        )
    )
    assert outcome(codec, value) == outcome(predecessor, value)


@pytest.mark.parametrize(
    "path", ["pkg/../bad", "pkg//bad", "pkg/\x00bad", "pkg/e\u0301.py"]
)
def test_direct_unverified_sequence_still_checks_canonical_paths(predecessor, path):
    payload = asdict(cases.binding())
    payload["files"][0]["path"] = path
    for module in (codec, predecessor):
        with pytest.raises(ValueError, match="noncanonical tree path"):
            module._sequence(payload)


def test_path_change_between_complete_operand_validations_still_refuses(monkeypatch):
    first, second = cases.binding(), cases.binding()
    original = codec.repository_tree_projection_value_to_payload
    count = 0

    def encode(value):
        nonlocal count
        result = original(value)
        count += 1
        if count == 1:
            object.__setattr__(second.files[0], "path", "pkg/../drift")
        return result

    monkeypatch.setattr(codec, "repository_tree_projection_value_to_payload", encode)
    with pytest.raises(codec.WorkspaceTreeProjectionValueError, match="noncanonical"):
        codec.repository_tree_projection_value_validate_equal(
            first, expected_value=second
        )
    assert count == 1


@pytest.mark.parametrize(
    "marker",
    [
        ',"binding_ref":"x"',
        ',"effect_paths":[]',
        ',"binding_ref":"x","effect_paths":[]',
    ],
)
def test_ancestor_strings_cannot_be_confused_with_top_level_members(
    predecessor, marker
):
    value = cases.binding()
    parent = "pkg" + marker
    child = parent + "/output.py"
    value = resign(
        replace(
            value,
            ancestors=(replace(value.ancestors[0], path=parent),),
            files=(replace(value.files[0], path=child),),
            effect_paths=(parent, child),
        )
    )
    assert outcome(codec, value) == outcome(predecessor, value)
    assert outcome(codec, value)[0] == "ok"


def test_current_aggregate_census_preserves_every_other_declaration():
    import ast

    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    rows = [
        (
            "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py",
            "8b63a112403720a07b9be561fab9cacdde10383181cd765abdb5fde19067a268",
            {"_compile_native_fields", "_convert", "_sequence", "_validate"},
        ),
        (
            "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py",
            "063d3330bbf45793163354b3e920335b8989c3d6af3b09f139d4e9fa683bf732",
            {"_encode", "_compile_receipt_fields"},
        ),
        (
            "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_contract.py",
            "fc8aa38eab16239fd20a372d73b050841bedade1687fb420027aef00087d08a3",
            {
                "test_fresh_wire_reuses_only_unchanged_sequence_measurement",
                "test_fresh_wire_preserves_frozen_functions_and_prior_test_declarations",
                "test_traversal_keeps_all_nonadmitted_declarations_and_previous_tests",
                "test_ascii_path_keeps_every_nonadmitted_declaration_and_prior_test",
            },
        ),
    ]
    for path, digest, allowed in rows:
        body = subprocess.run(
            ["git", "show", "8be9c5aa6dcfa7dceb6b6aebb14f2fcbdae35bc7:" + path],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        assert hashlib.sha256(body).hexdigest() == digest
        before, after = ast.parse(body), ast.parse((root / path).read_bytes())

        def declarations(tree):
            return {
                n.name: ast.dump(n, include_attributes=False)
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }

        old, new = declarations(before), declarations(after)
        assert old.keys() == new.keys()
        assert {name for name in old if old[name] != new[name]} == allowed

        def remaining(tree, allowed_names):
            return [
                ast.dump(n, include_attributes=False)
                for n in tree.body
                if not (
                    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and n.name in allowed_names
                )
            ]

        assert remaining(before, allowed) == remaining(after, allowed)
