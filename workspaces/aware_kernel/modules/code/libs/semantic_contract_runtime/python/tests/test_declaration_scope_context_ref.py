"""Original codec schema publication; values never grant Workspace admission."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    retained_declaration_scope_codec as codec,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    SemanticContractRef,
    canonical_json_bytes,
)
from test_retained_declaration_scope import fixture, nested_profile_fixture, selected

ROOT = Path(__file__).resolve().parents[8]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BASE = "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/"
CODEC_PATH = (
    BASE + "aware_code_semantic_contract_runtime/retained_declaration_scope_codec.py"
)
PREDECESSOR = "0ca8362ae636ad7d62f097e15b914013a0aa5cb7"
FREEZE = "72be86493315f3bc0840e123e3d301ce6435844f"
FREEZE_PATH = "docs/reports/code-grammar-original-declaration-intake-20261011.py"
EXPECTED = "sha256:34ca57cb747ded8a3d9a55127b6ba39257c5852dae297b7ba5a218a00222c0e9"
FUNCTIONS = (
    "declaration_closure_payload_bytes",
    "encode_retained_declaration_scope",
    "_preflight",
    "decode_retained_declaration_scope",
    "encode_selected_package_source_binding",
    "decode_selected_package_source_binding",
)


def committed(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def frozen_descriptor():
    tree = ast.parse(committed(FREEZE, FREEZE_PATH))
    values = {
        item.targets[0].id: item.value
        for item in tree.body
        if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name)
    }

    class OriginalKey(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id != "DECLARATION_CONTEXT_KEY":
                raise AssertionError("unexpected reference in authored descriptor")
            return ast.copy_location(
                ast.Constant(ast.literal_eval(values[node.id])), node
            )

    # Interpret only the committed literal descriptor, never execute the report.
    value = ast.literal_eval(
        OriginalKey().visit(values["DECLARATION_CONTEXT_DESCRIPTOR"])
    )
    return canonical_json_bytes(value)


def predecessor():
    namespace = {
        "__name__": "aware_code_semantic_contract_runtime._predecessor_codec",
        "__package__": "aware_code_semantic_contract_runtime",
    }
    exec(
        compile(
            committed(PREDECESSOR, CODEC_PATH), "<committed-original-codec>", "exec"
        ),
        namespace,
    )
    return namespace


def test_descriptor_matches_exact_committed_freeze_bytes():
    assert type(codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR) is bytes
    assert codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR == frozen_descriptor()
    assert len(codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR) == 2544
    assert (
        ContentDigest.of_bytes(codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR).value
        == EXPECTED
    )


def test_reference_is_exact_original_type_and_complete_frozen_identity():
    ref = codec.RETAINED_DECLARATION_SCOPE_V3_REF
    assert type(ref) is SemanticContractRef
    assert ref.to_wire() == {
        "key": "aware.code.retained-dependency-scope-closure.v3",
        "version": "3",
        "schema_digest": EXPECTED,
    }


def test_constants_are_immutable_values_not_a_mutable_schema_inventory():
    with pytest.raises(FrozenInstanceError):
        codec.RETAINED_DECLARATION_SCOPE_V3_REF.version = "foreign"
    with pytest.raises(TypeError):
        codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR[0] = 0
    assert not hasattr(codec, "DECLARATION_CONTEXT_DESCRIPTOR")


def test_exact_additive_submodule_exports_preserve_all_existing_exports():
    assert codec.__all__ == [
        "RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR",
        "RETAINED_DECLARATION_SCOPE_V3_REF",
        *predecessor()["__all__"],
    ]


@pytest.mark.parametrize("name", FUNCTIONS)
def test_original_codec_function_ast_is_unchanged(name):
    before = ast.parse(committed(PREDECESSOR, CODEC_PATH))
    after = ast.parse((ROOT / CODEC_PATH).read_bytes())

    def function(tree):
        return next(
            value
            for value in tree.body
            if isinstance(value, ast.FunctionDef) and value.name == name
        )

    assert ast.dump(function(before), include_attributes=False) == ast.dump(
        function(after), include_attributes=False
    )


@pytest.mark.parametrize("kind", ["closure", "nested-profile", "selected-source"])
def test_actual_predecessor_wire_and_decode_parity(kind):
    old = predecessor()
    if kind == "selected-source":
        value = selected(fixture())
        encode = "encode_selected_package_source_binding"
        decode = "decode_selected_package_source_binding"
    else:
        value = fixture() if kind == "closure" else nested_profile_fixture()
        encode = "encode_retained_declaration_scope"
        decode = "decode_retained_declaration_scope"
    original_bytes = old[encode](value)
    assert getattr(codec, encode)(value) == original_bytes
    assert (
        getattr(codec, decode)(original_bytes) == old[decode](original_bytes) == value
    )


def test_schema_closure_and_context_body_digests_remain_distinct():
    value = fixture()
    raw = codec.encode_retained_declaration_scope(value)
    assert (
        len(
            {
                codec.RETAINED_DECLARATION_SCOPE_V3_REF.schema_digest,
                value.closure_digest,
                ContentDigest.of_bytes(raw),
            }
        )
        == 3
    )
    assert json.loads(raw)["closure_digest"] == value.closure_digest.value


def test_descriptor_field_substitution_does_not_preserve_schema_identity():
    value = json.loads(codec.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR)
    value["fields"]["closure"].append("caller_validated")
    assert ContentDigest.of_bytes(canonical_json_bytes(value)).value != EXPECTED


def test_metadata_and_dependencies_remain_actual_predecessor_bytes():
    assert (PACKAGE_ROOT / "pyproject.toml").read_bytes() == committed(
        PREDECESSOR, BASE + "pyproject.toml"
    )


def test_fresh_isolated_import_does_not_pull_in_owners_or_documentation():
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    program = """
import json, sys
sys.path.insert(0, sys.argv[1])
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR, RETAINED_DECLARATION_SCOPE_V3_REF,
)
blocked = ("aware_workspace", "aware_language", "aware_meta", "aware_ontology",
           "aware_service", "aware_sdk", "aware_fs", "docs.")
assert not any(name.startswith(blocked) for name in sys.modules)
print(json.dumps({"bytes": len(RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR),
                  "ref": RETAINED_DECLARATION_SCOPE_V3_REF.to_wire()}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program, str(PACKAGE_ROOT)],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    record = json.loads(result.stdout)
    assert record["bytes"] == 2544
    assert record["ref"]["schema_digest"] == EXPECTED
