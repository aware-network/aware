"""Production .aware closure, neutral import boundary and strict evidence codecs."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tomllib
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_protocol_runtime import bootstrap as runtime
from aware_protocol_sdk import bootstrap as sdk

ROOT = next(
    parent for parent in Path(__file__).parents if (parent / "AGENTS.md").is_file()
)
HOME = ROOT / "workspaces/aware_kernel/modules/protocol"


def test_real_authored_closure_and_oracle(monkeypatch):
    from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
    from tree_sitter_aware.ontology_meaning_resolver import (
        OntologyMeaningPackageInput,
        resolve_ontology_meaning,
    )

    home = HOME / "sdks/protocol/aware"
    sources = {path.name: path.read_text() for path in sorted(home.glob("*.aware"))}
    documents = tuple(
        parse_neutral_aware_source(text, source_path=str(home / name))
        for name, text in sources.items()
    )
    meaning = resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name="protocol-sdk",
                fqn_prefix="aware_protocol_sdk",
                sources_root=str(home),
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple(
                    (str(home / name), "") for name in sources
                ),
            ),
        ),
        selected_package_names=frozenset({"protocol-sdk"}),
    )
    assert meaning
    fixture = (
        ROOT / "tools/cli/tests/fixtures/portable_initializer_protocol.aware"
    ).read_text()
    values = sources["bootstrap_values.aware"]
    assert (
        values.split("enum ", 1)[1].rstrip()
        == fixture.split("enum ", 1)[1].split("sdk protocol_sdk", 1)[0].rstrip()
    )
    for name in (
        "ProtocolBootstrapRequest",
        "ProtocolBootstrapFile",
        "ProtocolBootstrapInput",
        "ProtocolBootstrapEffect",
        "ProtocolBootstrapPlanObservation",
        "ProtocolBootstrapResult",
        "ProtocolBootstrapErrorEvidence",
    ):
        body = values.split("class " + name + " : inline_value {", 1)[1].split("}", 1)[
            0
        ]
        assert [item.name for item in fields(getattr(sdk, name))] == [
            line.strip().split()[0] for line in body.splitlines() if line.strip()
        ]
    monkeypatch.syspath_prepend(
        str(
            ROOT
            / "workspaces/aware_kernel/modules/sdk/libs/contract_runtime_source/python"
        )
    )
    from aware_sdk_contract_runtime_source import materialize_sdk_source_contract

    contract = materialize_sdk_source_contract(
        sdk_toml_text=(home / "aware.sdk.toml").read_text(),
        source_text_by_path=sources,
        selected_operation_refs=("protocol_sdk.initialize_profile",),
    )
    operation = contract.manifest.operations[0]
    assert operation.operation_ref == "protocol_sdk.initialize_profile"
    assert operation.provider_operation_ref == "protocol.profile.initialize"
    assert {
        ref for part in contract.manifest.schema_slices for ref in part.root_type_refs
    } == {
        "aware_protocol_sdk.ProtocolBootstrapRequest",
        "aware_protocol_sdk.ProtocolBootstrapResult",
        "aware_protocol_sdk.ProtocolBootstrapErrorEvidence",
    }


def _result():
    return sdk.ProtocolBootstrapResult(
        sdk.ProtocolBootstrapRequest("/customer"),
        "planned",
        ("owner diagnostic",),
        "codex-fixture",
        None,
        None,
        None,
        (),
        "completed",
        True,
        False,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract", "foreign"),
        ("operation_ref", "foreign"),
        ("ledger_complete", 1),
        ("diagnostics", (17,)),
        ("authorizes_retry", True),
        ("cleanup_state", "imagined"),
        ("manifest_source_sha256", "bare"),
        ("manifest_semantic_digest", "bare"),
    ],
)
def test_strict_codec_refuses_invalid_carriers(field, value):
    with pytest.raises(sdk.ProtocolBootstrapValueError):
        sdk.protocol_bootstrap_value_to_payload(replace(_result(), **{field: value}))


@pytest.mark.parametrize("diagnostics", [(), ("",), (" ", "\t")])
def test_refused_result_requires_owner_diagnostics(diagnostics):
    with pytest.raises(sdk.ProtocolBootstrapValueError, match="diagnostics"):
        sdk.protocol_bootstrap_value_to_payload(
            replace(_result(), outcome="refused", diagnostics=diagnostics)
        )


def test_codec_detaches_nested_values_and_preserves_diagnostics():
    result = _result()
    encoded = sdk.protocol_bootstrap_value_to_json(result)
    decoded = sdk.protocol_bootstrap_value_from_json(type(result), encoded)
    assert (
        decoded == result
        and decoded is not result
        and decoded.request is not result.request
    )
    assert decoded.diagnostics == ("owner diagnostic",)
    payload = sdk.protocol_bootstrap_value_to_payload(result)
    with pytest.raises(sdk.ProtocolBootstrapValueError):
        sdk.protocol_bootstrap_value_from_payload(
            type(result), {**payload, "unexpected": True}
        )
    with pytest.raises(sdk.ProtocolBootstrapValueError, match="duplicate"):
        sdk.protocol_bootstrap_value_from_json(type(result), '{"a":1,"a":2}')


@pytest.mark.parametrize(
    "version,admitted",
    [
        ("0.3.2", False),
        ("0.3.3", True),
        ("0.3.4", True),
        ("0.4.0", False),
        ("1.0.0", False),
    ],
)
def test_bootstrap_supplier_range_is_finite(version, admitted):
    from packaging.requirements import Requirement

    metadata = tomllib.loads(
        (HOME / "libs/fs_adapter/python/pyproject.toml").read_text()
    )
    requirement = Requirement(
        metadata["project"]["optional-dependencies"]["bootstrap"][0]
    )
    assert requirement.name == "aware-file-system"
    assert requirement.specifier.contains(version) is admitted


def test_successor_metadata_and_guidance_membership():
    fs_metadata = tomllib.loads(
        (HOME / "libs/fs_adapter/python/pyproject.toml").read_text()
    )
    sdk_metadata = tomllib.loads(
        (HOME / "sdks/protocol/python/pyproject.toml").read_text()
    )
    runtime_metadata = tomllib.loads(
        (HOME / "libs/runtime/python/pyproject.toml").read_text()
    )
    assert fs_metadata["project"]["version"] == "0.6.4"
    assert sdk_metadata["project"]["version"] == "0.3.1"
    assert runtime_metadata["project"]["version"] == "0.1.1"
    assert runtime_metadata["project"]["dependencies"] == []
    assert sdk_metadata["project"]["dependencies"] == [
        "aware-protocol-runtime>=0.1.1,<0.2.0"
    ]
    assert fs_metadata["project"]["dependencies"] == [
        "aware-protocol-runtime>=0.1.1,<0.2.0",
        "aware-protocol-sdk>=0.3.1,<0.4.0",
        "jsonschema>=4.23.0,<5.0.0",
    ]
    assert fs_metadata["project"]["optional-dependencies"]["draft"] == [
        "aware-file-system>=0.3.0,<0.4.0"
    ]
    assert (
        "aware_protocol_fs_adapter/templates/*.md"
        in fs_metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["include"]
    )
    from packaging.requirements import Requirement

    for metadata in (sdk_metadata, fs_metadata):
        requirement = Requirement(metadata["project"]["dependencies"][0])
        assert not requirement.specifier.contains("0.1.0")
        assert requirement.specifier.contains("0.1.1")
        assert not requirement.specifier.contains("0.2.0")


def test_runtime_has_no_physical_io_or_upward_imports():
    tree = ast.parse(
        (HOME / "libs/runtime/python/aware_protocol_runtime/bootstrap.py").read_text()
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(
                item.name.startswith(
                    (
                        "pathlib",
                        "subprocess",
                        "aware_protocol_sdk",
                        "aware_file_system",
                        "aware_workspace",
                        "aware_issue",
                    )
                )
                for item in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(
                (
                    "aware_protocol_sdk",
                    "aware_protocol_fs_adapter",
                    "aware_file_system",
                    "aware_workspace",
                    "aware_issue",
                )
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in (
                "stat",
                "lstat",
                "open",
                "mkdir",
                "unlink",
                "read_bytes",
                "write_bytes",
            )


def test_neutral_sdk_exports_do_not_load_optional_or_service_owners():
    roots = [
        str(HOME / path) for path in ("sdks/protocol/python", "libs/runtime/python")
    ]
    script = """
import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("aware_protocol_fs_adapter", "aware_file_system", "aware_workspace", "aware_issue", "aware_service", "aware_ontology")):
            raise AssertionError("optional import attempted: " + fullname)
sys.meta_path.insert(0, Block())
import aware_protocol_sdk as sdk
for name in sdk.__all__:
    getattr(sdk, name)
assert sdk.ProtocolBootstrapRequest("/customer").dry_run
try:
    sdk.ProtocolBootstrapClient.filesystem(repository_root="/customer", execution_id="codex-fixture")
except AssertionError as error:
    assert "aware_protocol_fs_adapter" in str(error)
else:
    raise AssertionError("unexpected fallback")
"""
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(roots),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_decoded_values_and_forged_equal_types_cannot_issue_authority():
    for kind in (
        sdk.ProtocolBootstrapPlan,
        sdk.ProtocolBootstrapAdmission,
        sdk.ProtocolBootstrapClient,
    ):
        with pytest.raises(TypeError):
            kind()

    class Equal(type):
        def __eq__(self, other):
            return True

    class Fake(metaclass=Equal):
        pass

    with pytest.raises(sdk.ProtocolBootstrapValueError):
        sdk.protocol_bootstrap_value_from_payload(Fake, {})
    cyclic = {}
    cyclic["self"] = cyclic
    assert (
        runtime.unvalidated_report(cyclic)["self"]["reason"] == "cycle_or_depth_bound"
    )
