"""Owner adapter/data joins; fixtures do not admit Workspace or role hosts."""

from __future__ import annotations

import ast
import asyncio
import copy
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import aware_code_semantic_contract_runtime as public
import pytest
from aware_code_semantic_contract_runtime import grammar_input_codecs as inputs
from aware_code_semantic_contract_runtime import grammar_product_contracts as products
from aware_code_semantic_contract_runtime import grammar_profile_join as receiver
from aware_code_semantic_contract_runtime import (
    retained_declaration_scope_codec as retained,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticBodyCodecBinding,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    CodeGrammarDeclarationSourceV1,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedLocalProfilePublication,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
)
from test_grammar_contextual_codecs import execution
from test_grammar_declaration_context import input_value, portable_group
from test_retained_declaration_scope import body
from test_retained_declaration_scope import fixture as declaration_fixture

BASE = Path(__file__).resolve().parents[1]
REPO = next(path for path in BASE.parents if (path / ".git").is_dir())
PREDECESSOR = "b8c70d01c92a120f703002c6bdb58e5a8407c806"


def selection_fixture(stage="profile_selection", local=False, closure=None):
    closure = closure or declaration_fixture()
    if local:
        consumer = next(
            scope
            for scope in closure.scopes
            if scope.scope_key == closure.consumer_scope_key
        )
        prefix = consumer.projection.workspace_manifest.relative_path.rpartition("/")[0]
        path = (prefix + "/" if prefix else "") + (
            "semantic_contract/profiles/local/aware.semantic_contract_profile.toml"
        )
        publication = CodeRetainedLocalProfilePublication(
            closure.consumer_scope_key, "local", body(path, b"local profile")
        )
        closure = replace(
            closure,
            local_profiles=tuple(
                sorted(
                    (*closure.local_profiles, publication),
                    key=lambda row: (
                        row.owning_scope_key.encode(),
                        row.profile_key.encode(),
                    ),
                )
            ),
        )
    else:
        publication = closure.local_profiles[0]
    group = portable_group(closure)
    portable = input_value(group, closure)
    expected = SemanticInputProductionExpectation.create(
        use_ref=portable.use_ref,
        operation_ref="fixture:resolve-grammar",
        stage=stage,
        package_identity=portable.package_identity,
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in portable.sources),
        context_bodies=portable.context_bodies,
    )
    owner_input = SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        portable.sources,
        expected.input_digest,
        expected.context_bodies,
    )
    manifest = publication.manifest
    source = CodeGrammarDeclarationSourceV1(
        closure.repository_binding_ref,
        publication.owning_scope_key,
        "profile",
        manifest.relative_path,
        manifest.body_ref,
        manifest.content_digest,
        len(manifest.body),
    )
    selection = products.CodeGrammarSourceRoleSelectionV1(
        owner_input.operation_ref,
        stage,
        owner_input.input_digest,
        group.root_occurrence_ref,
        publication.profile_key,
        source,
    )
    return selection, owner_input, group, closure


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
@pytest.mark.parametrize("local", (False, True))
def test_complete_local_and_imported_selection_correspondence(stage, local):
    selection, value, group, closure = selection_fixture(stage, local)
    assert inputs.validate_grammar_source_role_selection(selection, input=value) is None
    codec = inputs.CodeGrammarSourceRoleSelectionCodec()
    encoded = codec.encode(selection)
    assert encoded == products.encode_grammar_source_role_selection(selection)
    assert codec.decode(canonical_body=encoded) == selection
    declared = retained.CodeRetainedDeclarationScopeCodec()
    encoded = declared.encode(closure)
    assert encoded == retained.encode_retained_declaration_scope(closure)
    assert declared.decode(canonical_body=encoded) == closure
    table = inputs.grammar_input_body_codecs()
    assert (
        table[products.GRAMMAR_SOURCE_GROUP_REF].decode(
            table[products.GRAMMAR_SOURCE_GROUP_REF].encode(group)
        )
        == group
    )


def test_fresh_three_input_table_and_exact_public_exports():
    first, second = (
        inputs.grammar_input_body_codecs(),
        inputs.grammar_input_body_codecs(),
    )
    expected = {
        "declaration_scope": retained.CodeRetainedDeclarationScopeCodec,
        "grammar_selection": inputs.CodeGrammarSourceRoleSelectionCodec,
        "grammar_source_group": public.CodeGrammarSourceGroupCodec,
    }
    required = products.grammar_operational_profile("profile_selection").inputs
    assert set(first) == {row.contract for row in required}
    for row in required:
        assert type(first[row.contract]) is expected[row.role]
        assert first[row.contract] is not second[row.contract]
        assert first[row.contract].implementation == second[row.contract].implementation
    first.clear()
    assert len(second) == len(inputs.grammar_input_body_codecs()) == 3
    for module, names in (
        (inputs, inputs.__all__),
        (
            retained,
            [
                "CodeRetainedDeclarationScopeCodec",
                "RETAINED_DECLARATION_SCOPE_V3_CODEC_IMPLEMENTATION",
            ],
        ),
    ):
        for name in names:
            assert getattr(public, name) is getattr(module, name)


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_real_runtime_admits_actual_input_adapters_with_fixture_provider(stage):
    _, call, bodies, provider, transition, effect = execution(stage)
    codecs = inputs.grammar_input_body_codecs()
    codecs[products.GRAMMAR_PROFILE_RESULT_REF] = (
        public.CodeGrammarProfileSelectionCodec()
    )
    codecs[products.GRAMMAR_READ_TRANSITION_REF] = transition
    codecs[products.GRAMMAR_READ_EFFECT_REF] = effect
    if stage == "syntax_binding":
        codecs[products.GRAMMAR_SYNTAX_BINDING_V2_REF] = (
            public.CodeGrammarSyntaxBindingCodec()
        )
    bindings = tuple(
        SemanticBodyCodecBinding(ref, codecs[ref].implementation)
        for ref in sorted(codecs, key=lambda ref: canonical_json_bytes(ref.to_wire()))
    )
    call = replace(call, body_codec_bindings=bindings)
    assert set(codecs) == set(products.grammar_operational_contracts(stage))
    runtime = SemanticContractRuntime(
        products.grammar_operational_profile(stage),
        {provider.declaration.provider_key: provider},
        codecs,
    )
    result = asyncio.run(runtime.execute(call, bodies))
    assert runtime.owns_completion(result) and provider.calls == 1
    for codec in (transition, effect):
        context = codec.contexts[-1]
        raw = result.body_for(context.coordinate).canonical_body
        assert (
            codec.encode_contextual(codec.decode_contextual(raw, context), context)
            == raw
        )


@pytest.mark.parametrize(
    "field",
    (
        "operation_ref",
        "stage",
        "input_digest",
        "root_occurrence_ref",
        "profile_key",
    ),
)
def test_selection_substitution_refuses_complete_input(field):
    selection, value, _, _ = selection_fixture()
    change = {
        "operation_ref": "foreign:operation",
        "stage": "syntax_binding",
        "input_digest": ContentDigest.of_bytes(b"foreign input"),
        "root_occurrence_ref": "foreign:occurrence",
        "profile_key": "foreign",
    }[field]
    with pytest.raises(ContractViolation):
        inputs.validate_grammar_source_role_selection(
            replace(selection, **{field: change}),
            input=value,
        )


@pytest.mark.parametrize(
    "field",
    (
        "repository_binding_ref",
        "scope_key",
        "relative_path",
        "body_ref",
        "content_digest",
        "size_bytes",
    ),
)
def test_complete_profile_source_not_path_or_digest_matching(field):
    selection, value, _, _ = selection_fixture()
    change = {
        "repository_binding_ref": "foreign:repository",
        "scope_key": "foreign/workspace.toml",
        "relative_path": "foreign/profile.toml",
        "body_ref": "foreign:body",
        "content_digest": ContentDigest.of_bytes(b"foreign content"),
        "size_bytes": 999,
    }[field]
    changed = replace(selection.profile_source, **{field: change})
    with pytest.raises(ContractViolation):
        inputs.validate_grammar_source_role_selection(
            replace(selection, profile_source=changed),
            input=value,
        )


def test_imported_profile_membership_without_consumer_association_refuses():
    closure = replace(declaration_fixture(), edges=(), profile_associations=())
    selection, value, _, _ = selection_fixture(closure=closure)
    with pytest.raises(ContractViolation, match="lacks association"):
        inputs.validate_grammar_source_role_selection(selection, input=value)


def test_wrong_consumer_scope_even_with_fresh_original_input_digest_refuses():
    closure = declaration_fixture()
    closure = replace(closure, consumer_scope_key=closure.scopes[1].scope_key)
    selection, value, _, _ = selection_fixture(closure=closure)
    with pytest.raises(ContractViolation, match="consumer scope"):
        inputs.validate_grammar_source_role_selection(selection, input=value)


def test_equal_bytes_and_path_do_not_select_other_scope():
    selection, value, _, closure = selection_fixture()
    foreign = replace(selection.profile_source, scope_key=closure.consumer_scope_key)
    assert foreign.relative_path == selection.profile_source.relative_path
    assert foreign.content_digest == selection.profile_source.content_digest
    with pytest.raises(ContractViolation, match="publication unavailable"):
        inputs.validate_grammar_source_role_selection(
            replace(selection, profile_source=foreign),
            input=value,
        )


def test_no_validation_cache_before_or_after_changed_profile():
    selection, value, _, closure = selection_fixture()
    inputs.validate_grammar_source_role_selection(selection, input=value)
    manifest = body(
        closure.local_profiles[0].manifest.relative_path, b"changed profile"
    )
    changed = replace(
        closure,
        local_profiles=(replace(closure.local_profiles[0], manifest=manifest),),
        profile_associations=(
            replace(closure.profile_associations[0], manifest=manifest),
        ),
    )
    new_selection, new_value, _, _ = selection_fixture(closure=changed)
    for old in (selection, replace(selection, input_digest=new_value.input_digest)):
        with pytest.raises(ContractViolation):
            inputs.validate_grammar_source_role_selection(old, input=new_value)
    inputs.validate_grammar_source_role_selection(new_selection, input=new_value)
    # Detached restoration is only data; no retired owner-use revival is claimed.
    inputs.validate_grammar_source_role_selection(selection, input=value)


class Foreign:
    def __getattribute__(self, name):
        raise AssertionError("foreign callback must never run")


@pytest.mark.parametrize("location", ("selection", "source", "input"))
def test_exact_graph_refuses_before_foreign_callbacks(location):
    selection, value, _, _ = selection_fixture()
    if location == "selection":
        selection = Foreign()
    elif location == "source":
        selection = copy.copy(selection)
        object.__setattr__(selection, "profile_source", Foreign())
    else:
        value = Foreign()
    with pytest.raises((TypeError, ContractViolation)):
        inputs.validate_grammar_source_role_selection(selection, input=value)


@pytest.mark.parametrize(
    "codec",
    (
        inputs.CodeGrammarSourceRoleSelectionCodec,
        retained.CodeRetainedDeclarationScopeCodec,
    ),
)
@pytest.mark.parametrize("kind", ("null", "mapping", "foreign", "bytes"))
def test_encode_wrong_type_never_calls_foreign_value(codec, kind):
    value = {"null": None, "mapping": {}, "foreign": Foreign(), "bytes": b"bytes"}[kind]
    with pytest.raises((TypeError, ContractViolation)):
        codec().encode(value)


@pytest.mark.parametrize("owner", ("selection", "declaration"))
@pytest.mark.parametrize(
    "mutation",
    (
        "extra",
        "missing",
        "literal",
        "indent",
        "duplicate",
        "trailing",
        "invalid_utf8",
    ),
)
def test_owner_wire_refusals_are_preserved(owner, mutation):
    selection, _, _, closure = selection_fixture()
    codec, value = (
        (inputs.CodeGrammarSourceRoleSelectionCodec(), selection)
        if owner == "selection"
        else (retained.CodeRetainedDeclarationScopeCodec(), closure)
    )
    raw = codec.encode(value)
    wire = json.loads(raw)
    if mutation == "extra":
        wire["extra"] = None
    elif mutation == "missing":
        wire.pop("contract")
    elif mutation == "literal":
        wire["contract"] = "foreign"
    if mutation in ("extra", "missing", "literal"):
        raw = canonical_json_bytes(wire)
    elif mutation == "indent":
        raw = json.dumps(wire, indent=2).encode()
    elif mutation == "duplicate":
        raw = b'{"contract":"foreign",' + raw[1:]
    elif mutation == "trailing":
        raw += b" "
    elif mutation == "invalid_utf8":
        raw = b"\xff"
    with pytest.raises(ContractViolation):
        codec.decode(raw)


def test_original_budget_and_input_digest_still_checked():
    selection, value, _, _ = selection_fixture()
    object.__setattr__(value, "input_digest", ContentDigest.of_bytes(b"restamped"))
    with pytest.raises(ContractViolation):
        inputs.validate_grammar_source_role_selection(
            replace(selection, input_digest=value.input_digest),
            input=value,
        )


@pytest.mark.parametrize("bound", ("sources", "contexts"))
def test_selection_join_preserves_existing_shared_input_budget(monkeypatch, bound):
    selection, value, _, _ = selection_fixture()
    limit = (
        1
        if bound == "sources"
        else sum(len(row.canonical_body) for row in value.sources)
    )
    monkeypatch.setattr(receiver, "MAX_GROUP_BYTES", limit)
    with pytest.raises(ContractViolation, match="body bound exceeded"):
        inputs.validate_grammar_source_role_selection(selection, input=value)


@pytest.mark.parametrize("owner", ("selection", "declaration"))
@pytest.mark.parametrize("kind", ("bytearray", "memoryview", "text"))
def test_adapter_decode_requires_exact_owner_bytes(owner, kind):
    selection, _, _, closure = selection_fixture()
    codec, value = (
        (inputs.CodeGrammarSourceRoleSelectionCodec(), selection)
        if owner == "selection"
        else (retained.CodeRetainedDeclarationScopeCodec(), closure)
    )
    raw = codec.encode(value)
    foreign = {
        "bytearray": bytearray(raw),
        "memoryview": memoryview(raw),
        "text": raw.decode(),
    }[kind]
    with pytest.raises((TypeError, ContractViolation)):
        codec.decode(foreign)


@pytest.mark.parametrize("owner", ("selection", "declaration"))
@pytest.mark.parametrize("failure_type", (RuntimeError, KeyboardInterrupt))
def test_owner_failure_identity_propagates_without_retry(
    monkeypatch, owner, failure_type
):
    selection, _, _, closure = selection_fixture()
    failure = failure_type("original owner failure")
    calls = []

    def refuse(value):
        calls.append(value)
        raise failure

    codec, value, module, name = (
        (
            inputs.CodeGrammarSourceRoleSelectionCodec(),
            selection,
            inputs,
            "encode_grammar_source_role_selection",
        )
        if owner == "selection"
        else (
            retained.CodeRetainedDeclarationScopeCodec(),
            closure,
            retained,
            "encode_retained_declaration_scope",
        )
    )
    monkeypatch.setattr(module, name, refuse)
    with pytest.raises(failure_type) as caught:
        codec.encode(value)
    assert caught.value is failure and len(calls) == 1


@pytest.mark.parametrize("owner", ("selection", "declaration"))
def test_codec_recipe_identity_uses_full_reference_not_body_or_source_hash(owner):
    codec = (
        inputs.CodeGrammarSourceRoleSelectionCodec()
        if owner == "selection"
        else retained.CodeRetainedDeclarationScopeCodec()
    )
    recipe = (
        "closed descriptor expanded with original declaration-source fields/bounds; compare complete selection against original ordinary input and scope/group before and after"
        if owner == "selection"
        else "delegate exact V3 values and bytes to original retained-declaration encode/decode; preserve complete closure, canonical wires and owner bounds; no source, catalog or lifetime authority"
    )
    assert codec.implementation.closure_digest == ContentDigest.of_bytes(
        canonical_json_bytes({"contract": codec.contract.to_wire(), "recipe": recipe})
    )
    assert codec.implementation.closure_digest != codec.contract.schema_digest
    foreign_ref = replace(codec.contract, version="foreign")
    assert codec.implementation.closure_digest != ContentDigest.of_bytes(
        canonical_json_bytes({"contract": foreign_ref.to_wire(), "recipe": recipe})
    )


def test_owner_ast_functions_schema_and_metadata_unchanged():
    relative = BASE.relative_to(REPO)
    for name in (
        "retained_declaration_scope_codec.py",
        "grammar_product_contracts.py",
        "grammar_source_group.py",
        "grammar_profile_join.py",
        "runtime.py",
    ):
        path = relative / "aware_code_semantic_contract_runtime" / name
        old = subprocess.check_output(
            ["git", "show", f"{PREDECESSOR}:{path}"], cwd=REPO
        )
        new = (REPO / path).read_bytes()
        before, after = ast.parse(old), ast.parse(new)
        current = {
            node.name: ast.dump(node)
            for node in after.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        for node in before.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert current[node.name] == ast.dump(node)
    path = relative / "pyproject.toml"
    assert (
        subprocess.check_output(["git", "show", f"{PREDECESSOR}:{path}"], cwd=REPO)
        == (REPO / path).read_bytes()
    )
    wire = json.loads(retained.RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR)
    assert (
        retained.RETAINED_DECLARATION_SCOPE_V3_REF.schema_digest
        == ContentDigest.of_bytes(canonical_json_bytes(wire))
    )


def test_site_free_import_and_no_external_owner_dependency():
    env = {**os.environ, "PYTHONPATH": str(BASE), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-S",
            "-c",
            "import sys; import aware_code_semantic_contract_runtime as c; "
            "assert len(c.grammar_input_body_codecs()) == 3; "
            "assert not any(k.startswith(('aware_workspace', 'aware_language', 'aware_meta', "
            "'aware_ontology', 'aware_sdk', 'aware_service')) for k in sys.modules)",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
