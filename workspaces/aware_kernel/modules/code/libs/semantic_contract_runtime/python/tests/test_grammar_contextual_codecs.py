"""Original runtime registration with fixture providers, not host/source admission."""

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

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    PreparedSemanticEffectEnvelope,
    ProviderDerivation,
    ProviderExecutionBinding,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractResult,
    SemanticContractRuntime,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticTransitionEnvelope,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import grammar_product_contracts as g
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarProfileSelectionCodec,
    CodeGrammarSyntaxBindingCodec,
    grammar_profile_selection_body,
    grammar_syntax_binding_body,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    CodeGrammarSourceGroupCodec,
    grammar_source_group_body,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
    decode_retained_declaration_scope,
    encode_retained_declaration_scope,
)
from test_grammar_declaration_context import portable_group
from test_grammar_profile_contract import DIGEST, ROOT, declaration, syntax_fixture
from test_profile_runtime import profile as authored_profile
from test_retained_declaration_scope import fixture as declaration_fixture

FIXTURE_IMPLEMENTATION = SemanticImplementationCoordinate("fixture-provider", DIGEST)
FIXTURE_CONFIGURATION = SemanticConfigurationCoordinate("fixture-no-options", DIGEST)


class OwnerCodecFixture:
    """Delegate portable inputs to actual owner codecs; no source authority."""

    def __init__(self, contract, encode, decode):
        self.contract = contract
        self.implementation = SemanticImplementationCoordinate(
            "fixture-input-adapter", DIGEST
        )
        self.encode = encode
        self.decode = decode


class CapturedTransition(g.CodeGrammarReadTransitionCodec):
    def __init__(self):
        self.contexts = []

    def decode_contextual(self, body, context):
        self.contexts.append(context)
        return super().decode_contextual(body, context)


class CapturedEffect(g.CodeGrammarReadEffectCodec):
    def __init__(self):
        self.contexts = []

    def decode_contextual(self, body, context):
        self.contexts.append(context)
        return super().decode_contextual(body, context)


def body(role, contract, raw):
    return SemanticBody(
        SemanticValueCoordinate(
            role, contract, "fixture:" + role, ContentDigest.of_bytes(raw), len(raw)
        ),
        raw,
    )


class FixtureProvider:
    def __init__(self, profile, candidate, selection, mutate=None):
        self.declaration = profile.providers[0]
        self.candidate, self.selection, self.mutate = candidate, selection, mutate
        self.calls = 0

    async def derive(self, step):
        self.calls += 1
        candidate = self.candidate
        transition_value = g.CodeGrammarReadTransitionV1(
            self.selection.stage,
            step.input_closure_digest,
            self.selection.input_digest,
            candidate.coordinate,
        )
        effect_value = g.CodeGrammarReadEffectV1(
            self.selection.stage,
            step.input_closure_digest,
            self.selection.input_digest,
            candidate.coordinate,
        )
        raw = {
            "transition": canonical_json_bytes(transition_value.to_wire()),
            "effect": canonical_json_bytes(effect_value.to_wire()),
        }
        if self.mutate:
            self.mutate(raw)
        transition_body = body(
            "fixture.transition", g.GRAMMAR_READ_TRANSITION_REF, raw["transition"]
        )
        effect_body = body(
            self.declaration.effect_role.role, g.GRAMMAR_READ_EFFECT_REF, raw["effect"]
        )
        impacts = (
            SemanticImpactCoordinate(
                step.invocation.target_package.package_ref, "definition", "grammar-read"
            ),
        )
        transition = SemanticTransitionEnvelope(
            self.declaration.provider_key,
            self.declaration.result_role.contract,
            g.GRAMMAR_READ_TRANSITION_REF,
            step.invocation.predecessor,
            candidate.coordinate,
            transition_body.coordinate,
            impacts,
            step.input_closure_digest,
        )
        effect = PreparedSemanticEffectEnvelope(
            self.declaration.provider_key,
            g.GRAMMAR_READ_EFFECT_REF,
            transition.digest,
            step.invocation.predecessor,
            candidate.coordinate,
            effect_body.coordinate,
            (),
            impacts,
            (),
        )
        return ProviderDerivation(
            SemanticContractResult(
                TerminalStatus.DELTA,
                step.invocation.digest,
                transition=transition,
                effect=effect,
            ),
            tuple(
                sorted(
                    (candidate, transition_body, effect_body),
                    key=lambda b: canonical_json_bytes(b.coordinate.to_wire()),
                )
            ),
        )


def execution(stage="profile_selection", mutate=None, syntax=None):
    profile = g.grammar_operational_profile(stage)
    closure = declaration_fixture()
    group = portable_group(closure)
    selection = g.CodeGrammarSourceRoleSelectionV1(
        "fixture-operation",
        stage,
        DIGEST,
        group.root_occurrence_ref,
        "selected",
        declaration(),
    )
    inputs = [
        body(
            "declaration_scope",
            RETAINED_DECLARATION_SCOPE_V3_REF,
            encode_retained_declaration_scope(closure),
        ),
        body(
            "grammar_selection",
            g.GRAMMAR_SOURCE_ROLE_SELECTION_REF,
            g.encode_grammar_source_role_selection(selection),
        ),
        grammar_source_group_body(group),
    ]
    prior = grammar_profile_selection_body(authored_profile())
    if stage == "syntax_binding":
        inputs.append(prior)
        candidate = grammar_syntax_binding_body(syntax or syntax_fixture())
    else:
        candidate = prior
    provider = FixtureProvider(profile, candidate, selection, mutate)
    transition_codec, effect_codec = CapturedTransition(), CapturedEffect()
    codecs = {
        RETAINED_DECLARATION_SCOPE_V3_REF: OwnerCodecFixture(
            RETAINED_DECLARATION_SCOPE_V3_REF,
            encode_retained_declaration_scope,
            decode_retained_declaration_scope,
        ),
        g.GRAMMAR_SOURCE_ROLE_SELECTION_REF: OwnerCodecFixture(
            g.GRAMMAR_SOURCE_ROLE_SELECTION_REF,
            g.encode_grammar_source_role_selection,
            g.decode_grammar_source_role_selection,
        ),
        g.GRAMMAR_SOURCE_GROUP_REF: CodeGrammarSourceGroupCodec(),
        g.GRAMMAR_PROFILE_RESULT_REF: CodeGrammarProfileSelectionCodec(),
        g.GRAMMAR_READ_TRANSITION_REF: transition_codec,
        g.GRAMMAR_READ_EFFECT_REF: effect_codec,
    }
    if stage == "syntax_binding":
        codecs[g.GRAMMAR_SYNTAX_BINDING_V2_REF] = CodeGrammarSyntaxBindingCodec()
    bindings = tuple(
        SemanticBodyCodecBinding(ref, codecs[ref].implementation)
        for ref in sorted(codecs, key=lambda r: canonical_json_bytes(r.to_wire()))
    )
    provider_binding = ProviderExecutionBinding(
        provider.declaration.provider_key, FIXTURE_IMPLEMENTATION, FIXTURE_CONFIGURATION
    )
    from aware_code_semantic_contract_runtime.source_origin import decode_source_origin

    root = next(
        m for m in group.members if m.occurrence_ref == group.root_occurrence_ref
    )
    package = decode_source_origin(bytes.fromhex(root.origin_body_hex)).package
    call = SemanticContractInvocation(
        "fixture-invocation",
        "fixture-idem",
        profile.profile_ref,
        profile.digest,
        package,
        "resolve_grammar_profile",
        tuple(
            b.coordinate
            for b in sorted(inputs, key=lambda b: b.coordinate.role.encode())
        ),
        TypedEmptyCoordinate(provider.declaration.result_role.contract),
        (),
        bindings,
        (provider_binding,),
    )
    runtime = SemanticContractRuntime(
        profile, {provider.declaration.provider_key: provider}, codecs
    )
    return runtime, call, tuple(inputs), provider, transition_codec, effect_codec


def complete(stage="profile_selection"):
    runtime, call, inputs, provider, t, e = execution(stage)
    completion = asyncio.run(runtime.execute(call, inputs))
    return runtime, completion, provider, t, e


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_original_runtime_contextual_round_trip_and_completion(stage):
    runtime, completion, provider, transition, effect = complete(stage)
    assert provider.calls == 1 and runtime.owns_completion(completion)
    for codec in (transition, effect):
        ctx = codec.contexts[-1]
        assert ctx.has_validation_epoch
        raw = completion.body_for(ctx.coordinate).canonical_body
        value = codec.decode_contextual(raw, ctx)
        assert codec.encode_contextual(value, ctx) == raw
        assert value.stage == stage
        assert value.source_input_digest == DIGEST
        assert value.input_closure_digest == ctx.input_closure_digest != DIGEST
        assert value.result == ctx.candidate.coordinate
    assert (
        json.loads(completion.body_for(effect.contexts[-1].coordinate).canonical_body)[
            "physical_effect"
        ]
        == "none"
    )


@pytest.mark.parametrize(
    "codec", (g.CodeGrammarReadTransitionCodec(), g.CodeGrammarReadEffectCodec())
)
@pytest.mark.parametrize("value", (None, b"{}", {}, object()))
def test_every_context_free_encode_decode_refuses(codec, value):
    with pytest.raises(ContractViolation, match="contextual"):
        codec.encode(value)
    with pytest.raises(ContractViolation, match="contextual"):
        codec.decode(value)


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
@pytest.mark.parametrize("purpose", ("transition", "effect"))
@pytest.mark.parametrize(
    "mode",
    (
        "stage",
        "closure",
        "source",
        "result",
        "contract",
        "extra",
        "missing",
        "noncanonical",
        "duplicate",
        "null",
    ),
)
def test_actual_registered_runtime_refuses_wrong_body(stage, purpose, mode):
    def mutate(raw):
        value = json.loads(raw[purpose])
        if mode == "stage":
            value["stage"] = (
                "syntax_binding"
                if stage == "profile_selection"
                else "profile_selection"
            )
        elif mode == "closure":
            value["input_closure_digest"] = DIGEST.value
        elif mode == "source":
            value["source_input_digest"] = ContentDigest.of_bytes(b"foreign").value
        elif mode == "result":
            value["result"]["value_ref"] = "foreign-result"
        elif mode == "contract":
            value["contract"] = "foreign-contract"
        elif mode == "extra":
            value["authority"] = True
        elif mode == "missing":
            del value["result"]
        elif mode == "null":
            value["result"] = None
        raw[purpose] = canonical_json_bytes(value)
        if mode == "noncanonical":
            raw[purpose] += b" "
        elif mode == "duplicate":
            raw[purpose] = raw[purpose][:-1] + b',"stage":"profile_selection"}'

    runtime, call, inputs, provider, t, e = execution(stage, mutate)
    with pytest.raises((ContractViolation, TypeError)):
        asyncio.run(runtime.execute(call, inputs))
    assert provider.calls == 1
    assert (t if purpose == "transition" else e).contexts


def test_read_effect_cannot_claim_a_physical_write():
    def mutate(raw):
        value = json.loads(raw["effect"])
        value["physical_effect"] = "write"
        raw["effect"] = canonical_json_bytes(value)

    runtime, call, inputs, *_ = execution(mutate=mutate)
    with pytest.raises(ContractViolation, match="read-only"):
        asyncio.run(runtime.execute(call, inputs))


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
@pytest.mark.parametrize("purpose", ("transition", "effect"))
def test_equal_context_clone_and_unregistered_context_refuse(stage, purpose):
    _, completion, _, t, e = complete(stage)
    codec = t if purpose == "transition" else e
    ctx = codec.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    for cloned in (replace(ctx), copy.copy(ctx), replace(ctx, _validation_epoch=None)):
        with pytest.raises(ContractViolation):
            codec.decode_contextual(raw, cloned)
    assert codec.decode_contextual(raw, ctx)


@pytest.mark.parametrize(
    "field",
    (
        "provider_key",
        "input_closure_digest",
        "invocation_digest",
        "coordinate",
        "_profile_digest",
        "_registered_admission_token",
    ),
)
def test_original_context_restamp_cannot_preserve_registration(field):
    _, completion, _, t, _ = complete()
    ctx = t.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    value = {
        "provider_key": "foreign",
        "input_closure_digest": DIGEST,
        "invocation_digest": DIGEST,
        "coordinate": replace(ctx.coordinate, value_ref="foreign"),
        "_profile_digest": DIGEST,
        "_registered_admission_token": object(),
    }[field]
    object.__setattr__(ctx, field, value)
    with pytest.raises(ContractViolation):
        t.decode_contextual(raw, ctx)


@pytest.mark.parametrize(
    "field",
    (
        "interpretation_profile",
        "profile_key",
        "profile_ref",
        "profile_version",
        "code_profile_digest",
        "profile_source",
    ),
)
def test_syntax_output_must_correspond_to_consumed_full_profile(field):
    value = syntax_fixture()
    changes = {
        "interpretation_profile": replace(
            value.interpretation_profile, value_ref="foreign"
        ),
        "profile_key": "foreign",
        "profile_ref": "foreign",
        "profile_version": "foreign",
        "code_profile_digest": ContentDigest.of_bytes(b"foreign"),
        "profile_source": replace(value.profile_source, body_ref="foreign"),
    }
    runtime, call, inputs, *_ = execution(
        "syntax_binding", syntax=replace(value, **{field: changes[field]})
    )
    with pytest.raises(ContractViolation, match="retained profile"):
        asyncio.run(runtime.execute(call, inputs))


def test_codec_coordinates_bind_full_reference_and_frozen_recipe():
    account = json.loads(
        (
            ROOT / "docs/reports/code-language-grammar-product-contract-20261012.json"
        ).read_bytes()
    )
    for codec in (g.CodeGrammarReadTransitionCodec(), g.CodeGrammarReadEffectCodec()):
        assert codec.implementation.closure_digest == ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "contract": codec.contract.to_wire(),
                    "recipe": account["codec_recipe"]["transition_effect"],
                }
            )
        )


def test_foreign_context_refuses_before_attribute_access():
    class Foreign:
        def __getattribute__(self, key):
            raise AssertionError("foreign context callback")

    for codec in (g.CodeGrammarReadTransitionCodec(), g.CodeGrammarReadEffectCodec()):
        with pytest.raises(TypeError):
            codec.decode_contextual(b"{}", Foreign())


def test_four_additive_root_exports_are_the_original_ports():
    import aware_code_semantic_contract_runtime as root

    for name in (
        "CodeGrammarReadTransitionCodec",
        "CodeGrammarReadEffectCodec",
        "GRAMMAR_READ_TRANSITION_CODEC_IMPLEMENTATION",
        "GRAMMAR_READ_EFFECT_CODEC_IMPLEMENTATION",
    ):
        assert name in root.__all__ and getattr(root, name) is getattr(g, name)


@pytest.mark.parametrize("purpose", ("transition", "effect"))
@pytest.mark.parametrize(
    "primary", (RuntimeError("retained result failed"), KeyboardInterrupt())
)
def test_original_result_failure_or_interruption_survives_without_retry(
    monkeypatch, purpose, primary
):
    _, completion, _, t, e = complete()
    codec = t if purpose == "transition" else e
    ctx = codec.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    calls = []

    def fail(value):
        calls.append(value)
        raise primary

    monkeypatch.setattr(ctx.candidate._codec, "encode", fail)
    with pytest.raises(type(primary)) as caught:
        codec.decode_contextual(raw, ctx)
    assert caught.value is primary
    assert len(calls) == 1


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
@pytest.mark.parametrize("purpose", ("transition", "effect"))
def test_contextual_encoding_cannot_change_the_original_result(stage, purpose):
    _, completion, _, t, e = complete(stage)
    codec = t if purpose == "transition" else e
    ctx = codec.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    value = codec.decode_contextual(raw, ctx)
    for changed in (
        replace(value, source_input_digest=ContentDigest.of_bytes(b"foreign")),
        replace(value, input_closure_digest=DIGEST),
        replace(value, result=replace(value.result, value_ref="foreign")),
    ):
        with pytest.raises(ContractViolation):
            codec.encode_contextual(changed, ctx)


def test_registered_context_cannot_borrow_another_epoch_or_codec_identity():
    _, completion, _, t, _ = complete()
    _, _, _, other, _ = complete()
    ctx = t.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    object.__setattr__(ctx, "_validation_epoch", other.contexts[-1]._validation_epoch)
    with pytest.raises(ContractViolation):
        t.decode_contextual(raw, ctx)
    # An intact original context also rejects a different codec identity.
    _, completion, _, t, _ = complete()
    ctx = t.contexts[-1]
    raw = completion.body_for(ctx.coordinate).canonical_body
    t.implementation = SemanticImplementationCoordinate("foreign", DIGEST)
    with pytest.raises(ContractViolation):
        t.decode_contextual(raw, ctx)


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
@pytest.mark.parametrize("purpose", ("transition", "effect"))
@pytest.mark.parametrize("field", ("role", "contract", "digest", "size_bytes"))
def test_each_nested_result_coordinate_field_is_context_bound(stage, purpose, field):
    def mutate(raw):
        value = json.loads(raw[purpose])
        changed = {
            "role": "foreign",
            "contract": g.GRAMMAR_READ_EFFECT_REF.to_wire(),
            "digest": ContentDigest.of_bytes(b"foreign").to_wire(),
            "size_bytes": True,
        }
        value["result"][field] = changed[field]
        raw[purpose] = canonical_json_bytes(value)

    runtime, call, inputs, *_ = execution(stage, mutate)
    with pytest.raises((ContractViolation, TypeError)):
        asyncio.run(runtime.execute(call, inputs))


def test_previous_portable_and_profile_definitions_are_unchanged():
    relative = "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_product_contracts.py"
    original = subprocess.check_output(
        ["git", "show", "01f062b65041f9854dd509e2fd1851ee26188186:" + relative],
        cwd=ROOT,
        text=True,
    )
    current = ast.parse(Path(g.__file__).read_text())
    index = {
        node.name: ast.dump(node, include_attributes=False)
        for node in current.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    for node in ast.parse(original).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            assert index[node.name] == ast.dump(node, include_attributes=False)


def test_site_free_import_keeps_owners_and_services_out(tmp_path):
    script = (
        "import sys; import aware_code_semantic_contract_runtime as c; "
        "assert c.CodeGrammarReadTransitionCodec().contract == c.GRAMMAR_READ_TRANSITION_REF; "
        "assert c.CodeGrammarReadEffectCodec().contract == c.GRAMMAR_READ_EFFECT_REF; "
        "assert not any(n.startswith(('aware_workspace','aware_language','aware_ontology','aware_meta','aware_dev','aware_service')) for n in sys.modules)"
    )
    subprocess.run(
        [sys.executable, "-B", "-S", "-c", script],
        cwd=tmp_path,
        env={
            "PYTHONPATH": str(Path(g.__file__).resolve().parent.parent),
            "PATH": os.defpath,
        },
        check=True,
        capture_output=True,
        text=True,
    )
