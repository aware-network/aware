"""Genuine supplier proof from committed source, not installed/public readiness.

Workspace's original planning comparison stays the declared upstream fixture.
The Code receiver runs in its real registered executor, with original Workspace
source/context/selection owners. No fixture replaces the receiving helper.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[8]
CODE = Path(__file__).resolve().parents[1]
SUPPLIER = "32fb6dcb32b3526bf3ddc2ea31fa88563186b18c"
WORKSPACE = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime"
SDK = "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public"
POLICY = "workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime"
MODULE = "workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime"
PIN = "17b81ea6f54f726bc0d06f221aae99ca342cef0512d923e62c18642c8cb131fa"


@pytest.fixture(scope="module")
def suppliers(tmp_path_factory):
    destination = tmp_path_factory.mktemp("committed-grammar-suppliers")
    archive = subprocess.check_output(
        ["git", "archive", SUPPLIER, WORKSPACE, SDK, POLICY, MODULE],
        cwd=ROOT,
    )
    with tarfile.open(fileobj=io.BytesIO(archive)) as retained:
        retained.extractall(destination, filter="data")
    return destination


@pytest.mark.parametrize("mode", ["success", "mutation-restoration"])
def test_original_registered_workspace_declaration_reaches_code_receiver(
    tmp_path,
    suppliers,
    mode,
):
    roots = [
        CODE,
        CODE / "tests",
        suppliers / WORKSPACE,
        suppliers / WORKSPACE / "tests",
        suppliers / SDK,
        suppliers / SDK / "tests",
        suppliers / POLICY,
        suppliers / MODULE,
    ]
    program = r"""
import asyncio, hashlib, json, sys
from pathlib import Path
for entry in reversed(json.loads(sys.argv[1])):
    sys.path.insert(0, entry)
from aware_code_semantic_contract_runtime.grammar_profile_join import read_grammar_declaration_context
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_workspace_runtime import SourceObservationUnavailable
import aware_workspace_runtime.declaration_scope_admission as supplier_module
from test_grouped_selected_source_input import dependency_group, scope, register, result, DECLARATION_CONTEXTS

assert hashlib.sha256(Path(supplier_module.__file__).read_bytes()).hexdigest() == sys.argv[4]
mode = sys.argv[3]

async def consume():
    calls = []
    try:
      async with dependency_group(Path(sys.argv[2])) as (original, root, participant, edge):
        changed = None
        try:
            with scope(original, root=root, participants=(participant,), dependency_edges=(edge,),
                       contexts=DECLARATION_CONTEXTS) as expected:
                async def produce(value):
                    nonlocal changed
                    group, closure = read_grammar_declaration_context(value)
                    assert len(group.members) == 2
                    assert closure.local_profiles and closure.profile_associations
                    assert not hasattr(value, "declaration_handle")
                    module = next(row for row in next(
                        row for row in closure.scopes
                        if row.scope_key == "workspaces/network/aware.workspace.toml"
                    ).projection.modules if row.module_id == "main")
                    target = original.root / module.manifest.relative_path
                    assert module.manifest.body == target.read_bytes()
                    calls.append(value.input_digest.value)
                    if mode == "mutation-restoration":
                        changed = (target, target.read_bytes())
                        target.write_bytes(changed[1] + b"\n# fixture changed after receiver\n")
                    return result()
                registration = register(original, expected, produce)
                try:
                    received = await inputs.execute_registered_semantic_input(
                        original.host, registration, source_admission=original.selected, expected=expected,
                    )
                    assert mode == "success" and received == result()
                finally:
                    inputs.close_semantic_input_producer_registration(original.host, registration)
            assert mode == "success"
        except SourceObservationUnavailable:
            assert mode == "mutation-restoration" and changed is not None
            changed[0].write_bytes(changed[1])
            try:
                original.issuer.validate_semantic_input_context(original.selected, expected=expected)
            except SourceObservationUnavailable:
                pass
            else:
                raise AssertionError("restored bytes revived original retired use")
            raise
        assert len(calls) == 1
        assert original.issuer._semantic_source_window is None
    except SourceObservationUnavailable:
        assert mode == "mutation-restoration" and changed is not None
    assert len(calls) == 1
    print(json.dumps({"mode": mode, "receiver_calls": len(calls), "original_supplier": True}))

asyncio.run(consume())
"""
    # -I ignores inherited source/env selection; the exact source roots are
    # explicitly inserted inside this isolated proof subprocess, not installed.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    received = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            program,
            json.dumps(list(map(str, roots))),
            str(tmp_path),
            mode,
            PIN,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert received.returncode == 0, received.stdout + received.stderr
    assert json.loads(received.stdout) == {
        "mode": mode,
        "receiver_calls": 1,
        "original_supplier": True,
    }
