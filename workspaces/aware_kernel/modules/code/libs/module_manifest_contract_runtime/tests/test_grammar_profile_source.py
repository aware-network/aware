"""Authored grammar lowering, not original provider or source admission."""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path
from types import ModuleType

import pytest
from aware_code_module_manifest_contract_runtime import (
    GrammarProfileSourceError,
    encode_module_manifest_meaning,
    parse_grammar_provider_module,
    parse_module_manifest,
    parse_registered_grammar_profile,
    syntax_declaration_digest,
)
from aware_code_module_manifest_contract_runtime import grammar_profile_source as owner
from aware_code_module_manifest_contract_runtime.profile_codec import (
    encode_profile_manifest,
)
from aware_code_module_manifest_contract_runtime.profile_parser import (
    parse_profile_manifest,
)
from test_syntax_declaration import HEADER, source, table, toml_value

ROOT = Path(__file__).resolve().parents[7]
PACKAGE = Path(__file__).resolve().parents[1]
PREDECESSOR = "aa0945ae512a3ac1e04df663313ccde5a5408784"
BASE = "workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime"
PROFILE = b"""aware_semantic_contract_profile = 1
[profile]
key = "grammar.example"
package_key = "separate.interpretation"
runtime_import_mode = "registered_contracts"
runtime_import_required = true
status = "active"
[[providers]]
module_id = "z_module"
provider_key = "demo"
required = true
status = "active"
[[providers]]
module_id = "a_module"
provider_key = "other"
required = true
status = "active"
"""


def test_full_profile_meaning_and_authored_provider_order_preserved():
    observed = parse_registered_grammar_profile(PROFILE, profile_key="grammar.example")
    expected = parse_profile_manifest(PROFILE)
    assert observed == expected
    assert encode_profile_manifest(observed) == encode_profile_manifest(expected)
    assert observed.profile.package_key == "separate.interpretation"
    assert [row.module_id for row in observed.providers] == ["z_module", "a_module"]


def test_v2_product_exposure_is_explicit_without_changing_legacy_defaults():
    from test_profile_manifest_v2 import SOURCE as PRODUCT

    body = PRODUCT.replace(b'key = "custom.product"', b'key = "grammar.example"')
    assert parse_profile_manifest(body).aware_semantic_contract_profile == 2
    with pytest.raises(GrammarProfileSourceError, match="active required registered"):
        parse_registered_grammar_profile(body, profile_key="grammar.example")
    registered = body.replace(
        b"[profile]\n", b'[profile]\nruntime_import_mode="registered_contracts"\n'
    )
    original = parse_profile_manifest(registered)
    received = parse_registered_grammar_profile(
        registered, profile_key="grammar.example"
    )
    assert type(received) is type(original)
    assert encode_profile_manifest(received) == encode_profile_manifest(original)


def v2_authored(profile=None, *, syntax_table=None):
    """Original portable owner fixtures; these bytes establish no admission."""
    from test_v3_declarations import product_source

    module = product_source().replace(
        "[[packages.semantic_contract.registrations]]",
        "syntax="
        + toml_value(table() if syntax_table is None else syntax_table)
        + "\n[[packages.semantic_contract.registrations]]",
        1,
    )
    if profile is not None:
        module = (
            module.replace(
                'profile_ref="demo.product"',
                "profile_ref=" + toml_value(profile.profile_ref),
            )
            .replace(
                'profile_version="1"', "profile_version=" + toml_value(profile.version)
            )
            .replace(
                'profile_digest="sha256:' + "a" * 64 + '"',
                "profile_digest=" + toml_value(profile.digest.value),
            )
        )
    raw = b"""aware_semantic_contract_profile=2
[profile]
key="default"
package_key="separate.interpretation"
runtime_import_mode="registered_contracts"
[[providers]]
module_id="sdk"
package_id="provider"
registration_key="demo"
provider_key="demo"
exposure="graph_product"
"""
    return module.encode(), raw


def test_v2_nomination_reads_original_complete_registration_without_authority():
    module, raw = v2_authored()
    parsed = parse_module_manifest(module)
    row = parse_registered_grammar_profile(raw, profile_key="default").providers[0]
    assert owner._read_grammar_v2_product_nomination(parsed, declared=row) == (
        "demo.product",
        "1",
        "sha256:" + "a" * 64,
    )
    assert encode_module_manifest_meaning(parsed) == encode_module_manifest_meaning(
        parse_module_manifest(module)
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("package_id", "home"),
        ("package_id", "missing"),
        ("registration_key", "missing"),
        ("provider_key", "foreign"),
        ("exposure", "stage_pair"),
    ),
)
def test_v2_nomination_rejects_substituted_owner_coordinates(field, value):
    module, raw = v2_authored()
    row = parse_registered_grammar_profile(raw, profile_key="default").providers[0]
    with pytest.raises(GrammarProfileSourceError) as caught:
        owner._read_grammar_v2_product_nomination(
            parse_module_manifest(module), declared=replace(row, **{field: value})
        )
    assert caught.value.reason == "syntax_provider_declaration_mismatch"


@pytest.mark.parametrize("version", (1, 2))
def test_v2_nomination_requires_exact_original_v3_module(version):
    _, raw = v2_authored()
    row = parse_registered_grammar_profile(raw, profile_key="default").providers[0]
    with pytest.raises(GrammarProfileSourceError) as caught:
        owner._read_grammar_v2_product_nomination(
            parse_module_manifest(source(version=version)), declared=row
        )
    assert caught.value.reason == "syntax_provider_declaration_mismatch"


def test_v2_nomination_does_not_reinterpret_an_original_stage_pair():
    from test_v3_declarations import full_source

    _, raw = v2_authored()
    row = parse_registered_grammar_profile(raw, profile_key="default").providers[0]
    module = full_source().replace(
        "[[packages.semantic_contract.registrations]]",
        "syntax="
        + toml_value(table())
        + "\n[[packages.semantic_contract.registrations]]",
        1,
    )
    with pytest.raises(GrammarProfileSourceError) as caught:
        owner._read_grammar_v2_product_nomination(
            parse_module_manifest(module.encode()), declared=row
        )
    assert caught.value.reason == "syntax_provider_declaration_mismatch"


@pytest.mark.parametrize(
    "old,new",
    [
        (b'"registered_contracts"', b'"dynamic_contract_module"'),
        (b'"registered_contracts"', b'"anything_else"'),
        (b"runtime_import_required = true", b"runtime_import_required = false"),
        (b'status = "active"', b'status = "inactive"'),
        (b"required = true", b"required = false"),
        (
            b'provider_key = "other"\nrequired = true\nstatus = "active"',
            b'provider_key = "other"\nrequired = true\nstatus = "inactive"',
        ),
        (
            b"aware_semantic_contract_profile = 1",
            b"aware_semantic_contract_profile = true",
        ),
    ],
)
def test_unsupported_modes_refuse_without_changing_legacy_parser(old, new):
    candidate = PROFILE.replace(old, new)
    original = parse_profile_manifest(candidate)
    assert original
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_registered_grammar_profile(candidate, profile_key="grammar.example")
    assert caught.value.reason == "unsupported_profile_mode"
    assert parse_profile_manifest(candidate) == original


def test_legacy_implicit_dynamic_default_refuses_only_new_grammar_path():
    body = PROFILE.replace(b'runtime_import_mode = "registered_contracts"\n', b"")
    assert (
        parse_profile_manifest(body).profile.runtime_import_mode
        == "dynamic_contract_module"
    )
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_registered_grammar_profile(body, profile_key="grammar.example")
    assert caught.value.reason == "unsupported_profile_mode"


def test_no_alias_or_package_key_selector_fallback():
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_registered_grammar_profile(PROFILE, profile_key="separate.interpretation")
    assert caught.value.reason == "profile_selection_mismatch"


@pytest.mark.parametrize("version", [1, 2, 3])
def test_complete_provider_module_and_original_syntax_preserved(version):
    body = source(version=version)
    module, package = parse_grammar_provider_module(
        body, package_id="provider", provider_key="demo"
    )
    assert module == parse_module_manifest(body)
    assert package is module.packages[0]
    assert encode_module_manifest_meaning(module) == encode_module_manifest_meaning(
        parse_module_manifest(body)
    )
    declaration = package.semantic_contract
    assert declaration.capabilities == ("materialize",)
    assert declaration.owns_manifest_kinds == ("demo",)
    assert declaration.module == "demo.provider"
    assert declaration.syntax.contributions == tuple(table()["contributions"])
    assert (
        syntax_declaration_digest(declaration.syntax)
        != "sha256:" + hashlib.sha256(body).hexdigest()
    )


@pytest.mark.parametrize(
    "package,provider", [("absent", "demo"), ("provider", "foreign")]
)
def test_explicit_package_and_provider_are_not_substitutable(package, provider):
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_grammar_provider_module(
            source(), package_id=package, provider_key=provider
        )
    assert caught.value.reason == (
        "syntax_provider_declaration_missing"
        if package == "absent"
        else "syntax_provider_declaration_mismatch"
    )


def test_absent_syntax_remains_valid_legacy_module_but_refuses_grammar():
    body = HEADER.encode()
    assert parse_module_manifest(body)
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_grammar_provider_module(body, package_id="provider", provider_key="demo")
    assert caught.value.reason == "syntax_provider_declaration_missing"


def test_other_package_same_provider_does_not_override_explicit_package():
    body = (
        source()
        + b'\n[[packages]]\nid="other"\nkind="code"\nmanifest="other/pyproject.toml"\n'
    )
    module, package = parse_grammar_provider_module(
        body, package_id="provider", provider_key="demo"
    )
    assert len(module.packages) == 2 and package.id == "provider"
    with pytest.raises(GrammarProfileSourceError):
        parse_grammar_provider_module(body, package_id="other", provider_key="demo")


@pytest.mark.parametrize("entry", ["profile", "module"])
@pytest.mark.parametrize(
    "body", [None, {}, bytearray(b"x"), b"", b"x" * (8 * 1024 * 1024 + 1)]
)
def test_invalid_body_refuses_before_any_parser(monkeypatch, entry, body):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid body reached original parser")

    monkeypatch.setattr(owner, "parse_module_manifest", forbidden)
    monkeypatch.setattr(owner, "parse_profile_manifest", forbidden)
    with pytest.raises(GrammarProfileSourceError):
        if entry == "profile":
            parse_registered_grammar_profile(body, profile_key="grammar.example")
        else:
            parse_grammar_provider_module(
                body, package_id="provider", provider_key="demo"
            )


@pytest.mark.parametrize("entry", ["profile", "package", "provider"])
@pytest.mark.parametrize("selector", [None, [], "", " padded ", "x" * 513, "\ud800"])
def test_invalid_selector_refuses_before_parsing(monkeypatch, entry, selector):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid selector reached parser")

    monkeypatch.setattr(owner, "parse_module_manifest", forbidden)
    monkeypatch.setattr(owner, "parse_profile_manifest", forbidden)
    with pytest.raises(GrammarProfileSourceError) as caught:
        if entry == "profile":
            parse_registered_grammar_profile(PROFILE, profile_key=selector)
        else:
            parse_grammar_provider_module(
                source(),
                package_id=selector if entry == "package" else "provider",
                provider_key=selector if entry == "provider" else "demo",
            )
    assert caught.value.reason == "authored_selector_invalid"


@pytest.mark.parametrize("entry", ["profile", "module"])
def test_original_parser_failure_survives_without_reconstruction(monkeypatch, entry):
    original = RuntimeError("original owner diagnostic")

    def fail(*args, **kwargs):
        raise original

    monkeypatch.setattr(
        owner,
        "parse_profile_manifest" if entry == "profile" else "parse_module_manifest",
        fail,
    )
    with pytest.raises(RuntimeError) as caught:
        if entry == "profile":
            parse_registered_grammar_profile(PROFILE, profile_key="grammar.example")
        else:
            parse_grammar_provider_module(
                source(), package_id="provider", provider_key="demo"
            )
    assert caught.value is original


def test_profile_provider_bound_preserves_complete_legacy_value(monkeypatch):
    body = PROFILE.split(b"[[providers]]")[0] + b"".join(
        f'[[providers]]\nmodule_id="main"\nprovider_key="p_{i}"\n'.encode()
        for i in range(257)
    )
    assert len(parse_profile_manifest(body).providers) == 257

    def forbidden(*args, **kwargs):
        raise AssertionError("oversized profile reached complete-value encoding")

    monkeypatch.setattr(owner, "encode_profile_manifest", forbidden)
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_registered_grammar_profile(body, profile_key="grammar.example")
    assert caught.value.reason == "authored_source_bound"


def test_provider_limit_is_inclusive_without_silent_truncation():
    body = PROFILE.split(b"[[providers]]")[0] + b"".join(
        f'[[providers]]\nmodule_id="main"\nprovider_key="p_{i}"\n'.encode()
        for i in range(256)
    )
    observed = parse_registered_grammar_profile(body, profile_key="grammar.example")
    assert len(observed.providers) == 256
    assert observed == parse_profile_manifest(body)


def test_module_legacy_bool_format_does_not_become_grammar_admission():
    body = source().replace(b"aware = 1", b"aware = true", 1)
    assert parse_module_manifest(body).aware is True
    with pytest.raises(GrammarProfileSourceError) as caught:
        parse_grammar_provider_module(body, package_id="provider", provider_key="demo")
    assert caught.value.reason == "authored_source_invalid"


def test_self_consistent_replacement_is_data_not_source_authority():
    first = parse_grammar_provider_module(
        source(), package_id="provider", provider_key="demo"
    )
    replacement = source().replace(b"syntax/z.syntax.json", b"syntax/new.syntax.json")
    second = parse_grammar_provider_module(
        replacement, package_id="provider", provider_key="demo"
    )
    assert first != second
    assert not hasattr(second[1], "source_admission")


@pytest.mark.parametrize(
    "filename",
    [
        "codec.py",
        "syntax_declaration.py",
    ],
)
def test_original_parser_and_codec_asts_and_bytes_unchanged(filename):
    path = f"{BASE}/aware_code_module_manifest_contract_runtime/{filename}"
    prior = subprocess.check_output(["git", "show", f"{PREDECESSOR}:{path}"], cwd=ROOT)
    current = (ROOT / path).read_bytes()
    assert current == prior
    assert ast.dump(ast.parse(current)) == ast.dump(ast.parse(prior))


def _predecessor_module(filename):
    path = f"{BASE}/aware_code_module_manifest_contract_runtime/{filename}"
    prior = subprocess.check_output(["git", "show", f"{PREDECESSOR}:{path}"], cwd=ROOT)
    module = ModuleType(
        "aware_code_module_manifest_contract_runtime._predecessor_" + filename[:-3]
    )
    module.__package__ = "aware_code_module_manifest_contract_runtime"
    exec(compile(prior, f"{PREDECESSOR}:{path}", "exec"), module.__dict__)  # noqa: S102 - exact pinned repository source in a separate test namespace
    return module


def test_legacy_module_meaning_parity_with_original_parser_after_v3_extension():
    # Whole-file pins do not prohibit a separately governed v3 extension.
    # Exercise the exact predecessor parser with the original shared models.
    prior = _predecessor_module("parser.py")
    bodies = [HEADER, source()]
    for body in bodies:
        raw = body.encode() if type(body) is str else body
        assert asdict(parse_module_manifest(raw)) == asdict(
            prior.parse_module_manifest(raw)
        )


@pytest.mark.parametrize(
    "change", ["original", "boolean", "newline", "wrong_bool", "duplicate", "missing"]
)
def test_profile_v1_meaning_and_wire_parity_with_exact_predecessor(change):
    from test_profile_manifest import SOURCE as LEGACY

    body = LEGACY
    if change == "boolean":
        body = body.replace(b"= 1", b"= true", 1)
    elif change == "newline":
        body = body.replace(b"\n", b"\r\n")
    elif change == "wrong_bool":
        body = body.replace(b"required = false", b"required = 0")
    elif change == "duplicate":
        body = body.replace(b'"aware_api"', b'"aware_code"')
    elif change == "missing":
        body = body.replace(b'package_key = "different.package"\n', b"")
    parser = _predecessor_module("profile_parser.py")
    codec = _predecessor_module("profile_codec.py")
    try:
        old = parser.parse_profile_manifest(body)
    except ValueError as error:
        with pytest.raises(ValueError) as current:
            parse_profile_manifest(body)
        assert str(current.value) == str(error)
    else:
        value = parse_profile_manifest(body)
        assert value == old
        assert encode_profile_manifest(value) == codec.encode_profile_manifest(old)


def test_isolated_root_import_needs_no_semantic_language_workspace_or_objects():
    script = """
import sys
sys.path.insert(0, sys.argv[1])
import aware_code_module_manifest_contract_runtime as owner
assert owner.parse_registered_grammar_profile and owner.parse_grammar_provider_module
for name in sys.modules:
    assert not name.startswith(("aware_code_semantic_contract_runtime", "aware_language_", "aware_workspace", "aware_meta", "aware_ontology", "aware_service")), name
"""
    subprocess.run([sys.executable, "-I", "-B", "-c", script, str(PACKAGE)], check=True)


def test_metadata_matches_actual_committed_predecessor():
    previous = subprocess.check_output(
        ["git", "show", f"{PREDECESSOR}:{BASE}/pyproject.toml"], cwd=ROOT
    )
    assert (PACKAGE / "pyproject.toml").read_bytes() == previous
