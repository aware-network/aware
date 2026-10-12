"""Authored requirements and legacy meaning parity, never source admission."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModulePackageSemanticContractSpec,
    AwareModulePackageSemanticContractSyntaxSpec,
    AwareModuleSyntaxDeclarationSpec,
    AwareModuleTomlError,
    ModuleManifestMeaningError,
    SyntaxDeclarationError,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
    syntax_declaration_digest,
)
from aware_code_module_manifest_contract_runtime import syntax_declaration as syntax

REPO = Path(__file__).resolve().parents[7]
BASE = "workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime"
PREDECESSOR = "a662f7cad712d479e990b092df537f44b13eb7e7"
HEADER = """aware = 1
[[plugins]]
kind = "code.module_plugin"
provider_key = "demo"
[[packages]]
id = "provider"
kind = "code"
manifest = "provider/pyproject.toml"
[packages.semantic_contract]
role = "demo.provider"
contract = "aware.semantic_provider"
provider_key = "demo"
module = "demo.provider"
owns_manifest_kinds = ["demo"]
capabilities = ["materialize"]
"""


def table():
    return {
        "version": 1,
        "contributions": ["syntax/z.syntax.json", "syntax/a.syntax.json"],
        "anchors": [
            {
                "consumer_contract": {
                    "key": "fixture.meaning.v1",
                    "version": "1",
                    "schema_digest": "sha256:" + "a" * 64,
                },
                "role": "meaning",
                "rule_name": "definition",
                "field_path": ["body"],
                "required": True,
                "top_level": True,
            }
        ],
    }


def toml_value(value):
    if type(value) is dict:
        return (
            "{"
            + ", ".join(f"{key}={toml_value(item)}" for key, item in value.items())
            + "}"
        )
    if type(value) is list:
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def source(value=None, version=1):
    payload = table() if value is None else value
    return (
        HEADER.replace("aware = 1", f"aware = {version}")
        + "syntax = "
        + toml_value(payload)
        + "\n"
    ).encode()


@pytest.mark.parametrize("version", [1, 2, 3])
def test_public_parser_and_full_meaning_roundtrip(version):
    value = parse_module_manifest(source(version=version))
    provider = value.packages[0].semantic_contract
    assert type(provider) is AwareModulePackageSemanticContractSyntaxSpec
    assert provider.syntax.contributions == tuple(table()["contributions"])
    encoded = encode_module_manifest_meaning(value)
    assert decode_module_manifest_meaning(encoded) == value
    assert (
        json.loads(encoded)["meaning"]["packages"][0]["semantic_contract"]["syntax"]
        == table()
    )
    assert not hasattr(provider.syntax, "source_identity")


@pytest.mark.parametrize("version", [1, 2, 3])
def test_absence_preserves_original_exact_model_and_shape(version):
    value = parse_module_manifest(
        HEADER.replace("aware = 1", f"aware = {version}").encode()
    )
    provider = value.packages[0].semantic_contract
    assert type(provider) is AwareModulePackageSemanticContractSpec
    assert "syntax" not in asdict(provider)
    assert b'"syntax":' not in encode_module_manifest_meaning(value)


def test_lowered_digest_is_domain_bound_not_manifest_hash():
    declared = parse_module_manifest(source()).packages[0].semantic_contract.syntax
    raw = json.dumps(
        {"contract": "aware.code.grammar-syntax-declaration.v1", "value": table()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert (
        syntax_declaration_digest(declared)
        == "sha256:" + hashlib.sha256(raw).hexdigest()
    )
    assert (
        syntax_declaration_digest(declared)
        != "sha256:" + hashlib.sha256(source()).hexdigest()
    )
    changed = replace(declared, contributions=declared.contributions[::-1])
    assert syntax_declaration_digest(changed) != syntax_declaration_digest(declared)
    assert (
        parse_module_manifest(source().replace(b"\n", b"\r\n"))
        .packages[0]
        .semantic_contract.syntax
        == declared
    )


@pytest.mark.parametrize("part", ["declaration", "anchor", "contract"])
@pytest.mark.parametrize("kind", ["missing", "extra"])
def test_exact_table_closure_through_public_source_parser(part, kind):
    value = table()
    row = {
        "declaration": value,
        "anchor": value["anchors"][0],
        "contract": value["anchors"][0]["consumer_contract"],
    }[part]
    if kind == "missing":
        del row[next(iter(row))]
    else:
        row["caller_validated"] = True
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(source(value))


@pytest.mark.parametrize(
    "path",
    [
        "/a.syntax.json",
        "./a.syntax.json",
        "../a.syntax.json",
        "a//b.syntax.json",
        "a/../b.syntax.json",
        "a\\b.syntax.json",
        "a.syntax.json/",
        "a.syntax",
        "a.json",
        "a\x00.syntax.json",
        "e\u0301.syntax.json",
        "a" * 244 + ".syntax.json",
        "a/" * 128 + "x.syntax.json",
        " /x.syntax.json",
    ],
)
def test_contribution_paths_refuse_without_normalizing(path):
    value = table()
    value["contributions"] = [path]
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(source(value))


@pytest.mark.parametrize(
    "path", ["é.syntax.json", "syntax/a file.syntax.json", "x" * 243 + ".syntax.json"]
)
def test_bounded_code_path_grammar_preserves_valid_spaces_and_nfc(path):
    value = table()
    value["contributions"] = [path]
    assert parse_module_manifest(source(value)).packages[
        0
    ].semantic_contract.syntax.contributions == (path,)


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", True),
        ("version", 2),
        ("version", "1"),
        ("contributions", []),
        ("contributions", ["same.syntax.json", "same.syntax.json"]),
        ("contributions", ["x.syntax.json"] * 129),
        ("anchors", []),
        ("anchors", table()["anchors"] * 8193),
        ("anchors", table()["anchors"] * 2),
    ],
)
def test_declaration_versions_counts_and_duplicates_refuse(key, value):
    raw = table()
    raw[key] = value
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(source(raw))


@pytest.mark.parametrize(
    "key,value",
    [
        ("required", 1),
        ("top_level", "true"),
        ("role", ""),
        ("role", "has space"),
        ("role", "x" * 513),
        ("rule_name", "rule.with.dot"),
        ("rule_name", "x" * 129),
        ("field_path", []),
        ("field_path", ["x"] * 65),
        ("field_path", ["not-a-field"]),
        ("field_path", [1]),
    ],
)
def test_anchor_types_and_language_name_limits_refuse(key, value):
    raw = table()
    raw["anchors"][0][key] = value
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(source(raw))


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_digest", "a" * 64),
        ("schema_digest", "sha256:" + "A" * 64),
        ("key", ""),
        ("version", ""),
        ("version", 1),
        ("key", "x" * 513),
    ],
)
def test_full_consumer_contract_ref_required(key, value):
    raw = table()
    raw["anchors"][0]["consumer_contract"][key] = value
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(source(raw))


def test_anchor_can_reference_generated_wrapper_without_declaring_a_rule():
    raw = table()
    raw["anchors"][0]["rule_name"] = "source_file"
    result = parse_module_manifest(source(raw))
    assert (
        result.packages[0].semantic_contract.syntax.anchors[0].rule_name
        == "source_file"
    )


def test_null_is_not_omitted_syntax():
    raw = json.loads(
        encode_module_manifest_meaning(parse_module_manifest(HEADER.encode()))
    )
    raw["meaning"]["packages"][0]["semantic_contract"]["syntax"] = None
    with pytest.raises(ModuleManifestMeaningError):
        decode_module_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )


def test_codec_refuses_bad_values_and_field_substitution():
    value = parse_module_manifest(source())
    raw = json.loads(encode_module_manifest_meaning(value))
    raw["meaning"]["packages"][0]["semantic_contract"]["syntax"]["version"] = True
    with pytest.raises(ModuleManifestMeaningError):
        decode_module_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )
    object.__setattr__(
        value.packages[0].semantic_contract.syntax,
        "contributions",
        ("../foreign.syntax.json",),
    )
    with pytest.raises(ModuleManifestMeaningError):
        encode_module_manifest_meaning(value)


class ForeignMeta(type):
    def __getattribute__(self, name):
        raise AssertionError("foreign metaclass called")


class Foreign(metaclass=ForeignMeta):
    def __getattribute__(self, name):
        raise AssertionError("foreign field called")

    def __iter__(self):
        raise AssertionError("foreign iteration called")

    def __eq__(self, other):
        raise AssertionError("foreign equality called")


@pytest.mark.parametrize(
    "target,field",
    [
        ("syntax", "version"),
        ("syntax", "contributions"),
        ("syntax", "anchors"),
        ("anchor", "consumer_contract"),
        ("anchor", "role"),
        ("anchor", "field_path"),
        ("anchor", "required"),
        ("anchor", "top_level"),
        ("contract", "schema_digest"),
    ],
)
def test_forged_syntax_graph_refuses_before_foreign_callbacks(target, field):
    root = parse_module_manifest(source()).packages[0].semantic_contract.syntax
    node = {
        "syntax": root,
        "anchor": root.anchors[0],
        "contract": root.anchors[0].consumer_contract,
    }[target]
    object.__setattr__(node, field, Foreign())
    with pytest.raises(SyntaxDeclarationError):
        syntax_declaration_digest(root)


def test_foreign_variant_and_uninitialized_root_refuse():
    value = parse_module_manifest(source())
    spec = value.packages[0].semantic_contract
    foreign = type(
        "ForeignSyntaxProvider", (AwareModulePackageSemanticContractSyntaxSpec,), {}
    )
    object.__setattr__(value.packages[0], "semantic_contract", object.__new__(foreign))
    with pytest.raises(ModuleManifestMeaningError):
        encode_module_manifest_meaning(value)
    with pytest.raises(SyntaxDeclarationError):
        syntax_declaration_digest(object.__new__(AwareModuleSyntaxDeclarationSpec))
    assert type(spec) is AwareModulePackageSemanticContractSyntaxSpec


def test_byte_bound_is_complete_not_just_array_counts(monkeypatch):
    declared = parse_module_manifest(source()).packages[0].semantic_contract.syntax
    wire = syntax.syntax_declaration_wire(declared)
    size = len(
        json.dumps(
            wire, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    )
    monkeypatch.setattr(syntax, "MAX_SYNTAX_DECLARATION_BYTES", size)
    assert syntax.syntax_declaration_wire(declared) == wire
    monkeypatch.setattr(syntax, "MAX_SYNTAX_DECLARATION_BYTES", size - 1)
    with pytest.raises(SyntaxDeclarationError):
        syntax.syntax_declaration_wire(declared)


def test_parser_reads_no_files_and_digest_changes_no_provider_membership(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("source parser opened a file")

    monkeypatch.setattr("builtins.open", forbidden)
    value = parse_module_manifest(source(), source_label="/not/an/authority")
    encode_module_manifest_meaning(value)
    syntax_declaration_digest(value.packages[0].semantic_contract.syntax)


@pytest.fixture(scope="module")
def predecessor_package(tmp_path_factory):
    root = tmp_path_factory.mktemp("committed-module-predecessor")
    archive = subprocess.check_output(["git", "archive", PREDECESSOR, BASE], cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as content:
        content.extractall(root, filter="data")
    return root / BASE


def test_actual_predecessor_models_and_bytes_preserved(predecessor_package):
    bodies = [
        HEADER.replace("aware = 1", f"aware = {version}").encode()
        for version in (1, 2, 3)
    ]
    bodies.extend(
        [
            b"aware=1\npackages=[]\n",
            b'aware=true\n[[packages]]\nid="x"\nkind="code"\nmanifest="./x//pyproject.toml"\n',
        ]
    )
    script = """import json, sys
from dataclasses import asdict
from aware_code_module_manifest_contract_runtime import parse_module_manifest, encode_module_manifest_meaning
out=[]
for encoded in json.load(sys.stdin):
    v=parse_module_manifest(bytes.fromhex(encoded))
    out.append({"model":asdict(v),"wire":encode_module_manifest_meaning(v).hex()})
json.dump(out,sys.stdout)
"""
    environment = {
        **os.environ,
        "PYTHONPATH": str(predecessor_package),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    original = subprocess.check_output(
        [sys.executable, "-B", "-c", script],
        input=json.dumps([body.hex() for body in bodies]).encode(),
        env=environment,
        cwd=predecessor_package,
    )
    actual = [
        {
            "model": json.loads(json.dumps(asdict(parse_module_manifest(body)))),
            "wire": encode_module_manifest_meaning(parse_module_manifest(body)).hex(),
        }
        for body in bodies
    ]
    assert json.loads(original) == actual


def test_neutral_import_and_metadata_unchanged():
    script = 'import sys, aware_code_module_manifest_contract_runtime; assert not any(n.startswith(("aware_workspace", "aware_language", "aware_meta", "aware_ontology", "aware_code_sdk", "aware_filesystem")) for n in sys.modules)'
    subprocess.run([sys.executable, "-B", "-c", script], check=True)
    committed = subprocess.check_output(
        ["git", "show", PREDECESSOR + ":" + BASE + "/pyproject.toml"], cwd=REPO
    )
    assert (REPO / BASE / "pyproject.toml").read_bytes() == committed
