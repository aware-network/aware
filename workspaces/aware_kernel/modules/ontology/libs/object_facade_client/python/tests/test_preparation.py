"""Frozen original-host lower vectors and pure detached refusal conformance."""
import ast
import copy
import hashlib
import inspect
from typing import Any
import json
from pathlib import Path
import sys

import pytest
from aware_ontology_object_facade_client import codec, preparation as p, owner_values as v

# Captured from genuine pre-delegation host composition at 968bb082e51;
# no evaluator call. The three-case 45981-byte corpus SHA-256 is
# 0ee30c48ea792de23a6c633b7abf0259859578a1c38e8a8c18d8282b022492aa.
ACTIVATION = {'branch_ref': 'branch:notes', 'actor_ref': 'actor:luis', 'projection_ref': 'object_demo.NoteView.view', 'operation_ref': 'operation:p2', 'idempotency_key': 'idempotency:p2', 'object_abi_digest': 'sha256:6287972c044fc54fedf3753d805b9a6940bc52df705f90ea7c125eddb038ff0a', 'application_authority_body': {'application_ref': 'application:object-demo', 'authority_digest': 'sha256:93820c4197a36e90d416cfacbf566468c185a20712a44ba05c51cbd9b5dab2b0', 'implementation_digest': 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, 'expected_revision_ref': None}

CONTEXT: dict[str, Any] = {'branch_ref': 'branch:notes', 'retained_revision_ref': 'revision:0', 'provider_ref': 'memory', 'provider_generation': 'generation:1', 'topology_digest': 'sha256:0503eeff84f5963f8be34d7099349777de3918b126d25d8497d55efea9e0ff2a', 'schema_digest': 'sha256:678a4df82bb7023ea9c1ef22764678f4a0f889f591a1605ec6006ca51ca53127', 'schema_slice_digest': 'sha256:9843fbc040110ec592947720932b80eb60c0032d5bef86b8fbe68baf989c26f1', 'object_abi_digest': 'sha256:6287972c044fc54fedf3753d805b9a6940bc52df705f90ea7c125eddb038ff0a', 'application_authority_digest': 'sha256:93820c4197a36e90d416cfacbf566468c185a20712a44ba05c51cbd9b5dab2b0', 'selection_profile_digest': 'sha256:78970b1eb77840ccda5fd27d669e91b80f761a8943a5d85ad992921feb01c83c', 'base_operational_digest': 'sha256:7738e3298fa5192a9632073341c4d6e5c75c1d424246df22670d7022b5ec1c27'}

SELECTION_PROFILE = {'application_authority_digest': 'sha256:93820c4197a36e90d416cfacbf566468c185a20712a44ba05c51cbd9b5dab2b0', 'branch_ref': 'branch:notes', 'codec_version': 1, 'object_abi_digest': 'sha256:6287972c044fc54fedf3753d805b9a6940bc52df705f90ea7c125eddb038ff0a', 'profile_digest': 'sha256:78970b1eb77840ccda5fd27d669e91b80f761a8943a5d85ad992921feb01c83c', 'schema': 'aware.ontology.object-executable-selection-profile.v1', 'schema_digest': 'sha256:678a4df82bb7023ea9c1ef22764678f4a0f889f591a1605ec6006ca51ca53127', 'schema_slice_digest': 'sha256:9843fbc040110ec592947720932b80eb60c0032d5bef86b8fbe68baf989c26f1', 'selection_facts_body': {'actor_rule_body': {'codec_version': 1, 'kind': 'any_exact_text', 'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681', 'schema': 'aware.ontology.object-executable-selection-text-rule.v1', 'values': []}, 'authority_ref': 'executable-authority:object-demo:v1', 'capability_catalog_digest': 'sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 'codec_version': 1, 'executable_root_digest': 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'facts_digest': 'sha256:867ebfbf3a381d73671bb8310310806f1dd3428228a734e7c6a3517d6a6b6b4e', 'idempotency_rule_body': {'codec_version': 1, 'kind': 'any_exact_text', 'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681', 'schema': 'aware.ontology.object-executable-selection-text-rule.v1', 'values': []}, 'operation_rule_body': {'codec_version': 1, 'kind': 'any_exact_text', 'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681', 'schema': 'aware.ontology.object-executable-selection-text-rule.v1', 'values': []}, 'projection_rule_body': {'codec_version': 1, 'kind': 'any_exact_text', 'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681', 'schema': 'aware.ontology.object-executable-selection-text-rule.v1', 'values': []}, 'provider_generation': 'generation:1', 'provider_key': 'memory', 'schema': 'aware.ontology.object-executable-selection-facts.v1', 'vm_implementation_digest': 'sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc'}, 'selection_facts_digest': 'sha256:867ebfbf3a381d73671bb8310310806f1dd3428228a734e7c6a3517d6a6b6b4e', 'topology_digest': 'sha256:0503eeff84f5963f8be34d7099349777de3918b126d25d8497d55efea9e0ff2a'}

PRECONTACT_PROFILE = {'action_epoch_check_kind': 'provider_native_o1', 'attempt_head_namespace_digest': 'sha256:2222222222222222222222222222222222222222222222222222222222222222', 'attempt_ref_scheme': 'ontology-object-attempt-sha256-v1', 'codec_version': 1, 'epoch_check_support': 'provider_native_o1_with_durable_boundaries', 'executable_authority_digest': 'sha256:7c1613d6cd9fd33793f3768b9f72213f74d766125dbcfc444d71f5c645cb7b15', 'native_fencing_implementation_contract_digest': 'sha256:4444444444444444444444444444444444444444444444444444444444444444', 'owner_write_epoch_check_kind': 'durable_head_reread', 'profile_contract_digest': 'sha256:06f97fc6dad7b4141b9f2efe9f80e166ab10fb0d92a00eb1496f4e11d0fd0f30', 'profile_digest': 'sha256:74dbb7eea83b3df61a71ed251f79eee6a9c615c641e5f36ba0968776829bdc79', 'provider_distribution_digest': 'sha256:5f6768e3a3b6d3d6254634af996ae59f0fc4b67474d2286c215fcbb7dc14607c', 'provider_generation': 'generation:1', 'provider_key': 'memory', 'recovery_ref_scheme': 'ontology-object-recovery-sha256-v1', 'restart_recovery_kind': 'durable_provider_journal', 'schema': 'aware.ontology.object-precontact-recovery-profile.v1', 'seal_epoch_check_kind': 'durable_head_reread', 'supports_precontact_resolution': True, 'supports_preseal_resolution': True, 'supports_seal_intent_recovery': True, 'trace_namespace_digest': 'sha256:3333333333333333333333333333333333333333333333333333333333333333'}

EXPECTED = [{'selection': 'c11d048e3b013867341cb1beb94da658424dc3c9af58bc15ec9750826712975e', 'profile': 'ea4471d6205e41cb962a3073bf21968b3a5253bbb55274347014891a7ade7964', 'attempt': '436bb57a6916b8ae67c3908854be2e642cdc328bd3a0c1c8afb4cc41f2c521f9', 'admission': 'c67209e7876536b614f20d83d7c03b96fcfd5b7a62530bdb0f02759eb7c03a7c'}, {'selection': 'a0c41b9d98186968ac5085b6811d8c7fb12d66b16cd9d31207fb8e36b85b0159', 'profile': 'ea4471d6205e41cb962a3073bf21968b3a5253bbb55274347014891a7ade7964', 'attempt': 'de6f22169713a692fa39e04a2491a130ab70ccc81e134b5f4763e6f0703e1b83', 'admission': '5b258ad602f68ecc3ff175976bbcb9fac350dc9fd6cd99518d2b73f5934f5024'}]

def lower_inputs(revision=None):
    activation = copy.deepcopy(ACTIVATION)
    activation["expected_revision_ref"] = revision
    profile = v.OntologyObjectExecutableSelectionProfile.from_wire(copy.deepcopy(SELECTION_PROFILE))
    precontact = v.OntologyObjectPrecontactRecoveryProfile.from_wire(copy.deepcopy(PRECONTACT_PROFILE))
    return activation, copy.deepcopy(CONTEXT), profile, precontact


@pytest.mark.parametrize("revision,index", ((None, 0), ("revision:0", 1)))
def test_original_host_lower_vectors_remain_exact_detached_data(revision, index):
    activation, context, profile, recovery = lower_inputs(revision)
    authority, execution, selection = p._derive_selection_data(activation_preimage=activation,
        derivation_context=context, selection_profile=profile)
    attempt, admission = p._derive_attempt_data(activation_preimage=activation,
        derivation_context=context, selection_admission=selection, precontact_profile=recovery)
    for name, value in (("selection", selection), ("profile", recovery), ("attempt", attempt), ("admission", admission)):
        assert hashlib.sha256(value.canonical_bytes()).hexdigest() == EXPECTED[index][name]
    assert authority == selection.executable_authority_body
    assert v.attempt_digest_wire("aware.ontology.object-execution-admission-request.v1", execution) == selection.execution_admission_request_digest
    assert selection.retained_revision_ref == "revision:0"
    assert all(getattr(admission, "provider_" + name + "_count") == 0 for name in ("begin", "read", "action", "seal", "write", "recovery"))


def test_membership_preserves_historical_revision_policy_without_new_selection():
    activation, context, profile, _ = lower_inputs("revision:historical")
    assert p._validate_selection_membership(activation_preimage=activation,
        derivation_context=context, selection_profile=profile) is None
    with pytest.raises(p.PreparationError) as error:
        p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    assert error.value.code == "source_stale"
    assert error.value.reason == "selection_operational_base_stale"


@pytest.mark.parametrize("name", tuple(CONTEXT))
def test_every_lower_context_join_or_field_law_is_required(name):
    activation, context, profile, _ = lower_inputs()
    context[name] = "invalid" if name.endswith("digest") else None
    with pytest.raises(p.PreparationError):
        p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)


@pytest.mark.parametrize("slot", ("activation", "context", "profile", "recovery"))
@pytest.mark.parametrize("nested", (False, True))
def test_foreign_nested_operands_and_metaclass_equality_are_never_dispatched(slot, nested):
    calls = []
    class Meta(type):
        def __eq__(self, other):
            calls.append("equality")
            return False
    class Foreign(metaclass=Meta):
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign behavior")
    activation, context, profile, recovery = lower_inputs()
    value = {"nested": [Foreign()]} if nested else Foreign()
    if slot == "activation": activation = value
    if slot == "context": context = value
    if slot == "profile": profile = value
    if slot == "recovery": recovery = value
    with pytest.raises(p.PreparationError):
        if slot == "recovery":
            _, _, selection = p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
            p._derive_attempt_data(activation_preimage=activation, derivation_context=context, selection_admission=selection, precontact_profile=recovery)
        else:
            p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    assert calls == []


@pytest.mark.parametrize("target", ("_preparation_check", "_validate_context", "type", "_CONTEXT_KEYS"))
def test_genuine_guards_refuse_writable_binding_or_absent_builtin_substitution(monkeypatch, target):
    activation, context, profile, _ = lower_inputs()
    calls = []
    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign behavior")
    monkeypatch.setattr(p, target, foreign, raising=False)
    with pytest.raises(p.PreparationError):
        p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    assert calls == []


def test_actual_owning_return_boundary_rechecks_before_following_dispatch(monkeypatch):
    activation, context, profile, _ = lower_inputs()
    calls, injected = [], []
    original = p._validate_activation
    watched = inspect.unwrap(original).__code__
    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign behavior")
    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            monkeypatch.setattr(p, "_validate_context", foreign)
    sys.setprofile(observe)
    try:
        with pytest.raises(p.PreparationError):
            p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    finally:
        sys.setprofile(None)
    assert injected == [True]
    assert calls == []


def _facts_origin():
    root = Path(__file__).resolve().parents[8]
    vectors = json.loads((root / "docs/reports/ontology-facade-operation-wire-successor-vectors-20261004.json").read_text())
    request = json.loads(bytes.fromhex(next(r for r in vectors["requests"] if r["name"] == "operation.activate")["canonical_hex"]))
    bundle = json.loads(bytes.fromhex(request["payload"]["bundle"]["body_hex"]))
    return bundle["facts_body"], bundle["origin_body"]


def test_full_facts_topology_profile_refuses_without_partial_bundle_or_host_import():
    facts, origin = _facts_origin()
    with pytest.raises(p.PreparationError) as error:
        p.prepare_operation(facts_body=facts, origin_body=origin)
    assert error.value.code == "unsupported_profile"
    assert error.value.reason == "topology_decoder_unqualified"
    assert not any(name == "aware_ontology_runtime" or name.startswith("aware_ontology_runtime.") for name in sys.modules)
    with pytest.raises(p.PreparationError) as error:
        p._encode_bundle({})
    assert error.value.code == "unsupported_profile"


def test_origin_and_base_joins_refuse_even_under_recomputed_wrapper_hashes():
    facts, origin = _facts_origin()
    value = json.loads(bytes.fromhex(facts["body_hex"]))
    base = json.loads(bytes.fromhex(value["preparation_base_body"]["body_hex"]))
    base["provider_ref"] = "provider:different"
    base["base_digest"] = codec.domain_digest(base["contract"], {k:v for k,v in base.items() if k != "base_digest"})
    value["preparation_base_body"] = codec.make_body(base["contract"], codec.canonical_bytes(base))
    value["facts_digest"] = codec.domain_digest(value["contract"], {k:v for k,v in value.items() if k != "facts_digest"})
    with pytest.raises(p.PreparationError) as error:
        p.prepare_operation(facts_body=codec.make_body(value["contract"], codec.canonical_bytes(value)), origin_body=origin)
    assert error.value.reason == "base_operation_mismatch"


@pytest.mark.parametrize("kind", (str, int))
def test_scalar_subclasses_refuse_before_comparison_or_conversion(kind):
    calls = []
    class Foreign(kind):
        def __eq__(self, other):
            calls.append("eq")
            return True
        def strip(self, *args):
            calls.append("strip")
            return "actor:luis"
        def __str__(self):
            calls.append("str")
            return "actor:luis"
    activation, context, profile, _ = lower_inputs()
    activation["actor_ref"] = Foreign("actor:luis") if kind is str else Foreign(1)
    with pytest.raises(p.PreparationError):
        p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    assert calls == []


def test_class_name_metadata_substitution_refuses_before_foreign_hash():
    activation, context, profile, _ = lower_inputs()
    calls = []
    class ForeignName(str):
        def __hash__(self):
            calls.append("hash")
            return 1
        def __eq__(self, other):
            calls.append("eq")
            return True
    admitted_class = v.OntologyObjectExecutableSelectionAdmission
    original_name = type.__getattribute__(admitted_class, "__name__")
    type.__setattr__(admitted_class, "__name__", ForeignName("Foreign"))
    try:
        with pytest.raises(p.PreparationError):
            p._derive_selection_data(activation_preimage=activation, derivation_context=context, selection_profile=profile)
    finally:
        type.__setattr__(admitted_class, "__name__", original_name)
    assert calls == []


@pytest.mark.parametrize("entrance", ("framing", "preparation"))
@pytest.mark.parametrize("target", ("public_binding", "public_code", "compile_binding", "compile_code", "compiler_binding", "parser_binding", "view_binding", "module_class"))
def test_regex_dispatch_substitution_refuses_before_foreign_entry(monkeypatch, entrance, target):
    import re
    from types import ModuleType
    facts, origin = _facts_origin()
    vectors = json.loads((Path(__file__).resolve().parents[8] / "docs/reports/ontology-facade-operation-wire-successor-vectors-20261004.json").read_text())
    request = json.loads(bytes.fromhex(vectors["requests"][0]["canonical_hex"]))
    calls = []
    def foreign(*args, **kwargs):
        raise AssertionError("foreign regex behavior")
    class ForeignModule(ModuleType):
        def __getattribute__(self, name):
            calls.append("foreign_module")
            raise AssertionError("foreign regex module")
    if target == "public_binding": monkeypatch.setattr(re, "fullmatch", foreign)
    elif target == "public_code": monkeypatch.setattr(re.fullmatch, "__code__", foreign.__code__)
    elif target == "compile_binding": monkeypatch.setattr(re, "_compile", foreign)
    elif target == "compile_code": monkeypatch.setattr(vars(re)["_compile"], "__code__", foreign.__code__)
    elif target == "compiler_binding": monkeypatch.setattr(vars(re)["_compiler"], "compile", foreign)
    elif target == "parser_binding": monkeypatch.setattr(vars(re)["_parser"], "parse", foreign)
    elif target == "view_binding": monkeypatch.setattr(codec.re, "fullmatch", foreign)
    else: monkeypatch.setattr(re, "__class__", ForeignModule)
    previous, rejected = sys.getprofile(), False
    def observe(frame, event, arg):
        if event == "call" and frame.f_code is foreign.__code__: calls.append("foreign_entry")
    sys.setprofile(observe)
    try:
        try:
            if entrance == "framing": codec.encode_request(request)
            else: p.prepare_operation(facts_body=facts, origin_body=origin)
        except (codec.WireError, p.PreparationError):
            rejected = True
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()  # Restore stdlib before pytest formats any assertion.
    assert rejected and calls == []


@pytest.mark.parametrize("entrance", ("framing", "preparation"))
def test_regex_substitution_at_actual_codec_object_return_refuses_before_dispatch(monkeypatch, entrance):
    import re
    facts, origin = _facts_origin()
    vectors = json.loads((Path(__file__).resolve().parents[8] / "docs/reports/ontology-facade-operation-wire-successor-vectors-20261004.json").read_text())
    request = json.loads(bytes.fromhex(vectors["requests"][0]["canonical_hex"]))
    calls, injected, rejected = [], [], False
    watched = inspect.unwrap(codec._obj).__code__
    def foreign(*args, **kwargs):
        raise AssertionError("foreign regex behavior")
    def observe(frame, event, arg):
        if event == "call" and frame.f_code is foreign.__code__: calls.append("foreign_entry")
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            monkeypatch.setattr(re, "fullmatch", foreign)
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        try:
            if entrance == "framing": codec.encode_request(request)
            else: p.prepare_operation(facts_body=facts, origin_body=origin)
        except (codec.WireError, p.PreparationError):
            rejected = True
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert injected == [True] and rejected and calls == []


def test_regex_cache_changes_do_not_change_framing_or_supported_refusal():
    import re
    facts, origin = _facts_origin()
    before = codec.make_body("fixture.regex.v1", b"data")
    re.purge()
    re.compile(r"ordinary-unrelated-cache-use-[0-9]+")
    assert codec.make_body("fixture.regex.v1", b"data") == before
    with pytest.raises(p.PreparationError) as error:
        p.prepare_operation(facts_body=facts, origin_body=origin)
    assert error.value.code == "unsupported_profile"


def test_regex_closure_retains_genuine_bindings_and_native_fixed_matchers():
    import re
    verifier = inspect.getclosurevars(codec._digest).nonlocals["check"]
    retained = inspect.getclosurevars(verifier).nonlocals
    assert any(row[0] is re for row in retained["module_rows"])
    for method in (re.fullmatch, vars(re)["_compile"], vars(re)["_compiler"].compile, vars(re)["_parser"].parse):
        assert any(row[0] is method and row[1] is method.__code__ for row in retained["function_rows"])
    matching = inspect.getclosurevars(inspect.unwrap(codec.re.fullmatch)).nonlocals["compiled_matchers"]
    assert tuple(row[0] for row in matching) == (r"sha256:[0-9a-f]{64}", r"[0-9a-f]+", r"[0-9a-f]{64}")
    assert all(type(method.__self__) is re.Pattern for _, method in matching)


def test_t1_both_full_preparation_refusals_remain_literal():
    source = Path(p.__file__).read_text()
    tree = ast.parse(source)
    nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in ("prepare_operation", "_encode_bundle"):
        node = nodes[name]
        assert any(isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and
            len(n.exc.args) == 2 and all(isinstance(a, ast.Constant) for a in n.exc.args) and
            tuple(a.value for a in n.exc.args if isinstance(a, ast.Constant)) == ("unsupported_profile", "topology_decoder_unqualified")
            for n in ast.walk(node))


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("mutation", ("attributes_in_place", "attributes_replaced", "keyword_defaults", "annotations", "retained_set"))
def test_complete_fingerprint_mutations_refuse_without_foreign_behavior(monkeypatch, phase, mutation):
    calls, injected, set_restore = [], [], []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            raise AssertionError("foreign equality")

    class Foreign(metaclass=ForeignMeta):
        def __hash__(self):
            calls.append("hash")
            return 1

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality")

    foreign = Foreign()
    original = inspect.unwrap(codec._text)
    tree = inspect.unwrap(codec._tree)
    retained = inspect.getclosurevars(p._preparation_check).nonlocals
    # The value is caller controlled only in the injector, never a guard marker.
    def poison():
        if mutation == "attributes_in_place":
            monkeypatch.setitem(original.__dict__, "injected", foreign)
        elif mutation == "attributes_replaced":
            monkeypatch.setattr(original, "__dict__", {"injected": foreign})
        elif mutation == "keyword_defaults":
            monkeypatch.setitem(tree.__kwdefaults__, "opaque", foreign)
        elif mutation == "annotations":
            monkeypatch.setitem(original.__annotations__, "value", foreign)
        else:
            target = next(value for value, _ in retained["data_rows"] if type(value) is set)
            before = target.copy()
            target.add(foreign)
            set_restore.append((target, before))
        calls.clear()

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is original.__code__ and not injected:
            injected.append(True)
            poison()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            poison()
        else:
            sys.setprofile(observe)
        with pytest.raises((codec.WireError, p.PreparationError)):
            codec.canonical_bytes({"number": 1})
    finally:
        sys.setprofile(previous)
        for target, before in set_restore:
            target.clear()
            target.update(before)
        monkeypatch.undo()
    assert calls == []
    if phase == "owner_return":
        assert injected == [True]
    assert codec.canonical_bytes({"number": 1}) == b'{"number":1}'


@pytest.mark.parametrize("target", ("wire_module", "policy_descriptor"))
def test_native_leaf_return_keeps_complete_caller_continuation_checks(monkeypatch, target):
    calls, injected = [], []
    original = inspect.unwrap(codec._text)

    class ForeignModule(type(sys)):
        def __getattribute__(self, name):
            calls.append("module attribute")
            raise AssertionError("foreign caller continuation")

    def foreign(self):
        calls.append("descriptor")
        raise AssertionError("foreign descriptor")

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is original.__code__ and not injected:
            injected.append(True)
            if target == "wire_module":
                monkeypatch.setattr(codec.w, "__class__", ForeignModule)
            else:
                monkeypatch.setattr(codec._Policy, "message", property(foreign))

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises((codec.WireError, p.PreparationError)):
            codec.domain_digest("fixture.performance.v1", {})
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert injected == [True] and calls == []
    assert codec.domain_digest("fixture.performance.v1", {}) == "sha256:" + hashlib.sha256(b"fixture.performance.v1\0{}").hexdigest()


def test_retained_attribute_aliases_have_fresh_complete_data_checks():
    retained = inspect.getclosurevars(p._preparation_check).nonlocals
    dictionaries = {id(value): expected for value, expected in retained["data_rows"] if type(value) is dict}
    for target, _, _, _, (attributes, expected), _, _ in retained["function_rows"]:
        assert attributes is object.__getattribute__(target, "__dict__")
        assert dictionaries[id(attributes)] == expected
    assert p._preparation_check() is None


def test_equivalent_native_attribute_dictionary_replacement_preserves_behavior(monkeypatch):
    original = inspect.unwrap(codec._text)
    monkeypatch.setattr(original, "__dict__", dict(original.__dict__))
    assert codec.canonical_bytes({"number": 1}) == b'{"number":1}'


def test_complete_checks_reduce_fingerprint_construction_without_pruning_rows():
    retained = inspect.getclosurevars(p._preparation_check).nonlocals
    check_code, state_code = p._preparation_check.__code__, retained["state"].__code__
    counts = {"check": 0, "state": 0}

    def observe(frame, event, arg):
        if event == "call":
            if frame.f_code is check_code:
                counts["check"] += 1
            elif frame.f_code is state_code:
                counts["state"] += 1

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        p._preparation_check()
    finally:
        sys.setprofile(previous)
    assert counts == {"check": 1, "state": 0}
    assert len(retained["function_rows"]) > 500
    assert len(retained["data_rows"]) > 1_000


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("field", (
    "__code__", "__defaults__", "__kwdefaults__", "__dict__",
    "__name__", "__qualname__", "__module__", "__annotations__"))
def test_complete_native_function_scan_retains_every_field(monkeypatch, phase, field):
    original = inspect.unwrap(codec._text)
    original_code = original.__code__
    injected = []

    def replacement(value):
        return value

    changes = {"__code__": replacement.__code__, "__defaults__": (object(),),
               "__kwdefaults__": {"unexpected": object()},
               "__dict__": {"unexpected": object()},
               "__name__": "changed_name", "__qualname__": "changed_qualname",
               "__module__": "changed_module",
               "__annotations__": {"unexpected": object()}}

    def change():
        injected.append(True)
        monkeypatch.setattr(original, field, changes[field])

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("row_kind", ("function", "cell", "cell_type_binding"))
def test_complete_native_slot_scan_admits_kinds_before_access(
        monkeypatch, phase, row_kind):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    rows = control["function_rows"].cell_contents
    calls, injected = [], []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            reason = "foreign native slot access"
            raise AssertionError(reason)

    foreign = Foreign()
    original_code = inspect.unwrap(codec._text).__code__

    def change():
        injected.append(True)
        if row_kind == "cell_type_binding":
            monkeypatch.setattr(p, "CellType", Foreign)
            return
        altered = list(rows)
        index = (next(i for i, row in enumerate(rows) if row[6])
                 if row_kind == "cell" else 0)
        row = list(altered[index])
        if row_kind == "function":
            row[0] = foreign
        else:
            row[6] = ((foreign, row[6][0][1]), *row[6][1:])
        altered[index] = tuple(row)
        control["function_rows"].cell_contents = tuple(altered)

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["function_rows"].cell_contents = rows
        monkeypatch.undo()
    assert injected == [True] and calls == []
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("kind", (set, frozenset))
@pytest.mark.parametrize("mutation", ("length", "replacement"))
def test_complete_native_set_scan_retains_every_identity(phase, kind, mutation):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    rows = control["data_rows"].cell_contents
    index = next(i for i, (value, _) in enumerate(rows)
                 if type(value) is kind and value)
    value, expected = rows[index]
    before = value.copy()
    calls, injected = [], []

    class Foreign:
        def __hash__(self):
            calls.append("hash")
            return 1

        def __eq__(self, other):
            calls.append("equality")
            reason = "foreign data equality"
            raise AssertionError(reason)

    foreign = Foreign()
    original_code = inspect.unwrap(codec._text).__code__

    def change():
        injected.append(True)
        if kind is set:
            if mutation == "replacement":
                value.pop()
            value.add(foreign)
        else:
            elements = list(value)
            if mutation == "replacement":
                elements.pop()
            elements.append(foreign)
            altered = list(rows)
            altered[index] = (frozenset(elements), expected)
            control["data_rows"].cell_contents = tuple(altered)
        calls.clear()

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = rows
        if kind is set:
            value.clear()
            value.update(before)
    assert injected == [True] and calls == []
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


def test_complete_native_list_scan_refuses_length_change_after_admission():
    check = p._preparation_check
    retained = inspect.getclosurevars(check).nonlocals
    target, expected = next(
        (value, expected) for value, expected in retained["data_rows"]
        if type(value) is list and len(value) > 1)
    before, injected = target.copy(), []

    def observe(frame, event, primitive):
        if (event == "c_return" and primitive is len and frame.f_code is check.__code__
                and frame.f_locals.get("value") is target
                and frame.f_locals.get("identities") is expected[1] and not injected):
            injected.append(True)
            target.pop()

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.setprofile(previous)
        target[:] = before
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("binding", ("builtin", "module_shadow"))
def test_complete_native_function_metadata_lookup_has_fresh_binding_checks(
        phase, binding):
    import builtins

    original_lookup = builtins.getattr
    calls, injected = [], []
    original_code = inspect.unwrap(codec._text).__code__

    def foreign(*args):
        calls.append(True)
        reason = "foreign metadata lookup"
        raise AssertionError(reason)

    def change():
        injected.append(True)
        if binding == "builtin":
            builtins.__dict__["getattr"] = foreign
        else:
            p.__dict__["getattr"] = foreign

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous, refused = sys.getprofile(), False
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        try:
            codec.canonical_bytes({"fixture": 1})
        except (p.PreparationError, codec.WireError):
            refused = True
    finally:
        sys.setprofile(previous)
        builtins.__dict__["getattr"] = original_lookup
        if binding == "module_shadow":
            p.__dict__.pop("getattr", None)
    assert refused and injected == [True] and calls == []
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("binding", ("builtin", "module_shadow"))
@pytest.mark.parametrize("checkpoint", ("first_field", "later_field"))
def test_retained_metadata_accessor_survives_mid_scan_binding_change(
        binding, checkpoint):
    import builtins

    check = p._preparation_check
    source, start = inspect.getsourcelines(check)
    lookup_lines = {start + i for i, line in enumerate(source)
                    if ("if target.__" in line and "is not expected:" in line)
                    or "elif get(target, name) is not expected:" in line}
    original_lookup = builtins.getattr
    injected, observed = [], []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno in lookup_lines):
            observed.append(frame.f_locals["name"])
            if (not injected
                    and len(observed) == (1 if checkpoint == "first_field" else 5)):
                injected.append(True)
                # A benign noncallable binding tests continued native dispatch.
                # The next admission must refuse the changed binding.
                namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
                namespace["getattr"] = None
        return observe

    previous, refused = sys.gettrace(), False
    try:
        sys.settrace(observe)
        assert check() is None
        try:
            check()
        except p.PreparationError:
            refused = True
    finally:
        sys.settrace(previous)
        builtins.__dict__["getattr"] = original_lookup
        if binding == "module_shadow":
            p.__dict__.pop("getattr", None)
    assert injected == [True] and refused
    assert len(observed) == 4 * len(
        inspect.getclosurevars(check).nonlocals["function_rows"])
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
def test_complete_native_cell_scan_retains_contents(phase):
    closure = codec._text.__closure__
    assert closure is not None
    target = next(cell for name, cell in zip(
        codec._text.__code__.co_freevars, closure, strict=True) if name == "target")
    before = target.cell_contents
    injected = []
    original_code = before.__code__

    def change():
        injected.append(True)
        target.cell_contents = object()

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        target.cell_contents = before
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("kind", (list, set, frozenset))
def test_complete_native_data_scan_refuses_foreign_container_kinds(phase, kind):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    rows = control["data_rows"].cell_contents
    index = next(i for i, (value, _) in enumerate(rows) if type(value) is kind)
    value, expected = rows[index]
    calls, injected = [], []

    class Foreign(kind):
        def __iter__(self):
            calls.append("iteration")
            reason = "foreign container iteration"
            raise AssertionError(reason)

        def __len__(self):
            calls.append("length")
            reason = "foreign container length"
            raise AssertionError(reason)

    foreign = Foreign(value)
    original_code = inspect.unwrap(codec._text).__code__

    def change():
        injected.append(True)
        altered = list(rows)
        altered[index] = (foreign, expected)
        control["data_rows"].cell_contents = tuple(altered)

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = rows
    assert injected == [True] and calls == []
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("mutation", ("length", "replacement", "order"))
def test_complete_tuple_scan_retains_mutable_list_checks(phase, mutation):
    retained = inspect.getclosurevars(p._preparation_check).nonlocals
    target = next(value for value, _ in retained["data_rows"]
                  if type(value) is list and len(value) > 1
                  and len({id(item) for item in value}) > 1)
    before = target.copy()
    calls, injected = [], []

    class Foreign:
        def __eq__(self, other):
            calls.append("equality")
            reason = "foreign metadata equality"
            raise AssertionError(reason)

        def __hash__(self):
            calls.append("hash")
            reason = "foreign metadata hash"
            raise AssertionError(reason)

    foreign = Foreign()

    def poison():
        injected.append(True)
        if mutation == "length":
            target.append(foreign)
        elif mutation == "replacement":
            target[0] = foreign
        else:
            target.reverse()

    original = inspect.unwrap(codec._text).__code__

    def observe(frame, event, result):
        if not injected and event == "return" and frame.f_code is original:
            poison()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            poison()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        target[:] = before
    assert injected == [True] and calls == []
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("name", ("copyright", "str"))
def test_builtin_namespace_foreign_keys_refuse_before_equality(phase, name):
    retained = inspect.getclosurevars(p._preparation_check).nonlocals
    namespace = retained["primitive_namespace"]
    before = namespace.copy()
    clear, update, native_type = dict.clear, dict.update, type
    key_hash = hash(name)
    calls, injected = [], []
    original = inspect.unwrap(codec._text)

    class ForeignKey:
        def __hash__(self):
            return key_hash

        def __eq__(self, other):
            calls.append("foreign equality")
            raise AssertionError("foreign primitive key")

    foreign = ForeignKey()
    changed = {foreign if key == name else key: value for key, value in before.items()}

    def poison():
        clear(namespace)
        update(namespace, changed)

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is original.__code__ and not injected:
            injected.append(True)
            poison()

    previous, failure = sys.getprofile(), None
    try:
        if phase == "entry":
            poison()
        else:
            sys.setprofile(observe)
        try:
            codec.canonical_bytes({"number": 1})
        except BaseException as error:  # noqa: BLE001 - inspect after native namespace restoration
            failure = error
    finally:
        # Restore the process-wide native namespace before pytest inspection.
        clear(namespace)
        update(namespace, before)
        sys.setprofile(previous)
    assert native_type(failure) is codec.WireError or native_type(failure) is p.PreparationError
    assert calls == []
    if phase == "owner_return":
        assert injected == [True]
    assert codec.canonical_bytes({"number": 1}) == b'{"number":1}'


def _refusal_descriptor_proof(monkeypatch, error_kind, field, phase, attempt, watched):
    """Shared proof; genuine-host runners supply their original owner fixture."""
    calls, injected = [], []
    native_dictionary = BaseException.__dict__["__dict__"].__get__

    def foreign_get(self):
        calls.append("descriptor getter")
        raise RuntimeError("foreign refusal getter")

    def foreign_set(self, value):
        calls.append("descriptor setter")
        raise RuntimeError("foreign refusal setter")

    def poison(code=None, *args):
        if phase != "entry" and code is not watched:
            return
        if not injected:
            injected.append(True)
            monkeypatch.setattr(error_kind, field, property(foreign_get, foreign_set), raising=False)

    # Only the selected original code is observed. PY_UNWIND injects after the
    # original error exists, before the protected caller authenticates unwind.
    monitoring, tool_id = sys.monitoring, 5
    event = monitoring.events.PY_RETURN if phase == "owner_return" else monitoring.events.PY_UNWIND
    failure: BaseException | None = None
    if phase == "entry":
        poison()
    else:
        monitoring.use_tool_id(tool_id, "refusal-descriptor-proof")
        monitoring.register_callback(tool_id, event, poison)
        if phase == "unwind":
            monitoring.set_events(tool_id, event)
        else:
            monitoring.set_local_events(tool_id, watched, event)
    try:
        try:
            attempt()
        except BaseException as error:  # noqa: BLE001 - inspect only after descriptor restoration
            failure = error
    finally:
        if phase != "entry":
            monitoring.set_events(tool_id, 0)
            monitoring.set_local_events(tool_id, watched, 0)
            monitoring.register_callback(tool_id, event, None)
            monitoring.free_tool_id(tool_id)
        monkeypatch.undo()
    assert injected == [True] and calls == []
    assert failure is not None
    assert type(failure) is error_kind or type(failure) is p.PreparationError
    fields = native_dictionary(failure)
    assert fields == {"code": "malformed", "reason": "preparation_binding_mismatch"} or fields == {"code": "malformed"}
    assert failure.args == ("preparation_binding_mismatch",) or failure.args == ("malformed",)
    return failure


@pytest.mark.parametrize("phase", ("entry", "owner_return", "unwind"))
@pytest.mark.parametrize("entrance,field", (
    ("preparation", "code"), ("preparation", "reason"), ("framing", "code"),
))
def test_refusal_fields_bypass_replaced_error_descriptors(monkeypatch, entrance, field, phase):
    facts, origin = _facts_origin()
    if entrance == "preparation":
        error_kind = p.PreparationError
        watched = inspect.unwrap(p._native_inputs).__code__
        supplied_facts: Any = object() if phase == "unwind" else facts

        def preparation_attempt():
            return p.prepare_operation(facts_body=supplied_facts, origin_body=origin)

        attempt = preparation_attempt
    else:
        error_kind = codec.WireError
        watched = inspect.unwrap(codec._fail if phase == "unwind" else codec._tree).__code__

        def framing_attempt():
            return codec.canonical_bytes(object() if phase == "unwind" else {"number": 1})

        attempt = framing_attempt

    _refusal_descriptor_proof(monkeypatch, error_kind, field, phase, attempt, watched)
    assert codec.canonical_bytes({"number": 1}) == b'{"number":1}'
    with pytest.raises(p.PreparationError, match="topology_decoder_unqualified"):
        p.prepare_operation(facts_body=facts, origin_body=origin)


def _refusal_storage_proof(entrance, phase, binding, paired, attempt, watched, receiver=None):
    """Exercise the actual issuer cells and its check, not a replacement guard."""
    retained = inspect.getclosurevars(entrance).nonlocals
    refuse, check = retained["refuse"], retained["check"]
    cells = dict(zip(refuse.__code__.co_freevars, refuse.__closure__, strict=True))
    expected = {"allocate": "refusal_allocate", "initialize": "refusal_initialize",
                "exception_dictionary": "refusal_dictionary", "put_dictionary": "refusal_put"}
    names = (binding, expected[binding]) if paired else (binding,)
    before = [(cells[name], cells[name].cell_contents) for name in names]
    calls, injected = [], []
    checked: list[BaseException] = []
    failure: BaseException | None = None

    def foreign(*args, **kwargs):
        calls.append("rejected refusal helper")
        raise RuntimeError("foreign refusal helper")

    def poison(code=None, *args):
        if phase != "entry" and code is not watched:
            return
        if not injected:
            injected.append(True)
            for cell, _ in before:
                cell.cell_contents = foreign

    monitoring, tool_id = sys.monitoring, 5
    event = monitoring.events.PY_RETURN if phase == "owner_return" else monitoring.events.PY_UNWIND
    if phase != "entry":
        monitoring.use_tool_id(tool_id, "refusal-storage-proof")
        monitoring.register_callback(tool_id, event, poison)
        if phase == "unwind":
            monitoring.set_events(tool_id, event)
        else:
            monitoring.set_local_events(tool_id, watched, event)
    try:
        if phase == "entry":
            poison()
            try:
                check(receiver)
            except BaseException as error:  # noqa: BLE001 - inspect after restoring issuer cells
                checked.append(error)
            assert calls == []
        try:
            attempt()
        except BaseException as error:  # noqa: BLE001 - inspect after restoring issuer cells
            failure = error
        if not paired:
            # Direct private refusal construction must also reject before any
            # substituted primitive runs, independently of the complete check.
            assert refuse() is retained["binding_failure"]
    finally:
        if phase != "entry":
            monitoring.set_events(tool_id, 0)
            monitoring.set_local_events(tool_id, watched, 0)
            monitoring.register_callback(tool_id, event, None)
            monitoring.free_tool_id(tool_id)
        for cell, value in before:
            cell.cell_contents = value
    error_kind = inspect.getclosurevars(refuse).nonlocals["error_kind"]
    assert failure is not None
    assert type(failure) is error_kind or type(failure) is codec.WireError
    assert calls == [] and injected == [True]
    if phase == "entry":
        assert len(checked) == 1 and type(checked[0]) is error_kind
        assert failure is checked[0]
    fields = BaseException.__dict__["__dict__"].__get__(failure)
    assert fields == {"code": "malformed", "reason": "preparation_binding_mismatch"} or fields == {"code": "malformed"}
    return failure


@pytest.mark.parametrize("phase", ("entry", "owner_return", "unwind"))
@pytest.mark.parametrize("entrance", ("preparation", "framing"))
@pytest.mark.parametrize("binding,paired", (
    ("exception_dictionary", False), ("put_dictionary", False),
    ("allocate", False), ("initialize", False),
    ("exception_dictionary", True), ("put_dictionary", True),
))
def test_rejected_refusal_helpers_never_dispatch(entrance, phase, binding, paired):
    facts, origin = _facts_origin()
    if entrance == "preparation":
        target = p.prepare_operation
        watched = inspect.unwrap(p._native_inputs).__code__
        supplied_facts: Any = object() if phase == "unwind" else facts

        def preparation_attempt():
            return target(facts_body=supplied_facts, origin_body=origin)

        attempt = preparation_attempt
    else:
        target = codec.canonical_bytes
        watched = inspect.unwrap(codec._fail if phase == "unwind" else codec._tree).__code__

        def framing_attempt():
            return target(object() if phase == "unwind" else {"number": 1})

        attempt = framing_attempt
    _refusal_storage_proof(target, phase, binding, paired, attempt, watched)
    assert codec.canonical_bytes({"number": 1}) == b'{"number":1}'
    with pytest.raises(p.PreparationError, match="topology_decoder_unqualified"):
        p.prepare_operation(facts_body=facts, origin_body=origin)


def _text_owner_return_proof(monkeypatch, phase, target, attempt, accepted_errors):
    """Inject at the actual original/wrapper return, or its refusal unwind."""
    original_cast = inspect.unwrap(codec.cast)
    wrapper_code = codec.cast.__code__
    original_text = inspect.unwrap(codec._text)
    check_code = p._preparation_check.__code__
    calls, injected = [], []
    foreign_codes = []

    def foreign(*args, **kwargs):
        calls.append("foreign textual continuation")
        reason = "foreign textual continuation"
        raise RuntimeError(reason)

    def foreign_code(*args, **kwargs):
        reason = "foreign textual guard"
        raise RuntimeError(reason)

    def poison():
        if target == "constructor":
            monkeypatch.setattr(codec.WireError, "__init__", foreign)
        elif target == "allocation":
            monkeypatch.setattr(codec.WireError, "__new__", staticmethod(foreign))
        elif target == "error_descriptor":
            monkeypatch.setattr(
                codec.WireError, "code", property(foreign, foreign), raising=False,
            )
        elif target == "policy_descriptor":
            monkeypatch.setattr(codec._Policy, "message", property(foreign))
        elif target == "guard_binding":
            monkeypatch.setattr(codec, "_preparation_check", foreign)
        elif target == "guard_code":
            check = p._preparation_check
            changed = foreign_code.__code__.replace(
                co_freevars=check.__code__.co_freevars,
            )
            foreign_codes.append(changed)
            monkeypatch.setattr(check, "__code__", changed)
        elif target == "cast_binding":
            monkeypatch.setattr(codec, "cast", foreign)
        elif target == "cast_code":
            changed = foreign_code.__code__.replace(
                co_freevars=codec.cast.__code__.co_freevars,
            )
            foreign_codes.append(changed)
            monkeypatch.setattr(codec.cast, "__code__", changed)
        else:
            monkeypatch.setattr(codec, "len", foreign, raising=False)

    def observe(frame, event, arg):
        if event == "call" and any(frame.f_code is code for code in foreign_codes):
            calls.append("foreign guard entry")
        if injected or event != "return":
            return
        original_return = (
            phase == "original_return" and frame.f_code is original_cast.__code__
            and frame.f_back is not None
            and frame.f_back.f_code is wrapper_code
            and frame.f_back.f_back is not None
            and frame.f_back.f_back.f_code is original_text.__code__
        )
        wrapper_return = (phase == "wrapper_return" and frame.f_code is wrapper_code
                          and frame.f_locals.get("target") is original_cast
                          and frame.f_back is not None
                          and frame.f_back.f_code is original_text.__code__)
        check_return = (
            phase == "check_return" and frame.f_code is check_code
            and frame.f_back is not None
            and frame.f_back.f_code is original_text.__code__
        )
        if original_return or wrapper_return or check_return:
            injected.append(True)
            poison()

    monitoring, tool_id = sys.monitoring, 5

    def unwind(code, *args):
        if code is original_text.__code__ and not injected:
            injected.append(True)
            poison()

    def native_return(code, offset, called, first):
        if (code is original_text.__code__ and not injected
                and getattr(called, "__self__", None)
                is BaseException.__dict__["__dict__"]):
            injected.append(True)
            poison()

    previous = sys.getprofile()
    failure = None
    try:
        sys.setprofile(observe)
        if phase == "entry":
            injected.append(True)
            poison()
        elif phase == "unwind":
            monitoring.use_tool_id(tool_id, "text-refusal-unwind")
            monitoring.register_callback(tool_id, monitoring.events.PY_UNWIND, unwind)
            monitoring.set_events(tool_id, monitoring.events.PY_UNWIND)
        elif phase == "native_return":
            monitoring.use_tool_id(tool_id, "text-native-return")
            monitoring.register_callback(
                tool_id, monitoring.events.C_RETURN, native_return,
            )
            monitoring.set_local_events(
                tool_id, original_text.__code__, monitoring.events.CALL
                | monitoring.events.C_RETURN | monitoring.events.C_RAISE,
            )
        try:
            attempt()
        except accepted_errors as error:  # inspect only after restoration
            failure = error
    finally:
        sys.setprofile(previous)
        if phase == "unwind":
            monitoring.set_events(tool_id, 0)
            monitoring.register_callback(tool_id, monitoring.events.PY_UNWIND, None)
            monitoring.free_tool_id(tool_id)
        elif phase == "native_return":
            monitoring.set_local_events(tool_id, original_text.__code__, 0)
            monitoring.register_callback(tool_id, monitoring.events.C_RETURN, None)
            monitoring.free_tool_id(tool_id)
        monkeypatch.undo()
    assert injected == [True], (phase, target, type(failure), repr(failure))
    assert calls == [], (phase, target, calls)
    assert failure is not None and any(
        type(failure) is owner for owner in accepted_errors
    )
    return failure


@pytest.mark.parametrize("phase", (
    "entry", "native_return", "original_return", "wrapper_return",
    "check_return", "unwind",
))
@pytest.mark.parametrize("target", (
    "constructor", "allocation", "error_descriptor", "policy_descriptor",
    "guard_binding", "guard_code", "cast_binding", "cast_code", "absent_builtin",
))
def test_text_caller_returns_and_unwind_reject_before_behavior(
    monkeypatch, phase, target,
):
    failure = _text_owner_return_proof(
        monkeypatch, phase, target, lambda: codec._text(chr(0xD800)),
        (codec.WireError, p.PreparationError),
    )
    assert BaseException.__dict__["__dict__"].__get__(failure)["code"] == "malformed"
    assert codec._text("é") == "é"


@pytest.mark.parametrize("phase", ("original_return", "wrapper_return"))
@pytest.mark.parametrize("entrance", ("framing", "preparation"))
def test_text_owner_returns_are_admitted_through_public_entrances(
    monkeypatch, phase, entrance,
):
    if entrance == "framing":
        def framing_attempt():
            return codec.canonical_bytes({"text": chr(0xD800)})
        attempt = framing_attempt
    else:
        facts, origin = _facts_origin()
        def preparation_attempt():
            return p.prepare_operation(facts_body=facts, origin_body=origin)
        attempt = preparation_attempt
    _text_owner_return_proof(monkeypatch, phase, "constructor", attempt,
                            (codec.WireError, p.PreparationError))
    assert codec.canonical_bytes({"text": "é"}) == b'{"text":"\xc3\xa9"}'


@pytest.mark.parametrize("value,code", (
    (1, "malformed"), (chr(0xD800), "malformed"),
    ("x" * 65_537, "limit_exceeded"), ("é" * 32_769, "limit_exceeded"),
))
def test_text_refusal_preserves_exact_fields_and_args(value, code):
    with pytest.raises(codec.WireError) as refused:
        codec._text(value)
    assert type(refused.value) is codec.WireError
    assert refused.value.args == (code,)
    assert BaseException.__dict__["__dict__"].__get__(refused.value) == {"code": code}


@pytest.mark.parametrize("policy", (
    codec._V1_POLICY, codec._READ_REQUEST_POLICY, codec._READ_RESULT_POLICY,
))
def test_text_native_budget_slot_preserves_all_owning_policy_limits(policy):
    assert codec._text("x" * policy.message, policy) == "x" * policy.message
    with pytest.raises(codec.WireError, match="limit_exceeded"):
        codec._text("x" * (policy.message + 1), policy)
    assert (codec._text("é" * (policy.message // 2), policy)
            == "é" * (policy.message // 2))
    with pytest.raises(codec.WireError, match="limit_exceeded"):
        codec._text("é" * (policy.message // 2 + 1), policy)


def _tree_owner_return_proof(monkeypatch, phase, target):
    original_cast = inspect.unwrap(codec.cast)
    original_tree = inspect.unwrap(codec._tree)
    tree_code, cast_code = codec._tree.__code__, codec.cast.__code__
    check_code = p._preparation_check.__code__
    watched = {
        "text_return": codec._text.__code__,
        "recursive_return": tree_code,
        "body_return": codec._body.__code__,
        "parse_return": codec._parse.__code__,
    }.get(phase)
    calls, injected, foreign_codes = [], [], []

    def foreign(*args, **kwargs):
        calls.append("foreign tree continuation")
        reason = "foreign tree continuation"
        raise RuntimeError(reason)

    def foreign_code(*args, **kwargs):
        reason = "foreign tree code"
        raise RuntimeError(reason)

    def poison():
        if target in ("entries", "message", "depth", "aggregate_body"):
            monkeypatch.setattr(codec._Policy, target, property(foreign))
        elif target == "constructor":
            monkeypatch.setattr(codec.WireError, "__init__", foreign)
        elif target in ("guard_code", "cast_code"):
            function = p._preparation_check if target == "guard_code" else codec.cast
            changed = foreign_code.__code__.replace(
                co_freevars=function.__code__.co_freevars,
            )
            foreign_codes.append(changed)
            monkeypatch.setattr(function, "__code__", changed)
        else:
            binding = {"guard_binding": "_preparation_check", "visitor": "_tree",
                       "reader": "_text", "body": "_body", "parser": "_parse",
                       "failure": "_fail", "cast_binding": "cast"}.get(target, target)
            monkeypatch.setattr(codec, binding, foreign, raising=False)

    def observe(frame, event, arg):
        if event == "call" and any(frame.f_code is code for code in foreign_codes):
            calls.append("foreign code entry")
        if injected or event != "return" or frame.f_back is None:
            return
        owner = frame.f_back.f_code is original_tree.__code__
        original = (
            phase == "original_return" and frame.f_code is original_cast.__code__
            and frame.f_back.f_code is cast_code and frame.f_back.f_back is not None
            and frame.f_back.f_back.f_code is original_tree.__code__
        )
        wrapper = phase == "wrapper_return" and frame.f_code is cast_code and owner
        checked = phase == "check_return" and frame.f_code is check_code and owner
        nested = watched is not None and frame.f_code is watched and owner
        if original or wrapper or checked or nested:
            injected.append(True)
            poison()

    monitoring, tool_id = sys.monitoring, 5

    def unwind(code, *args):
        if code is original_tree.__code__ and not injected:
            injected.append(True)
            poison()

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        if phase == "entry":
            injected.append(True)
            poison()
        elif phase == "unwind":
            monitoring.use_tool_id(tool_id, "tree-refusal-unwind")
            monitoring.register_callback(tool_id, monitoring.events.PY_UNWIND, unwind)
            monitoring.set_events(tool_id, monitoring.events.PY_UNWIND)
        raw = b"[]"
        value = {"contract_ref": "contract:fixture", "body_hex": raw.hex(),
                 "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest()}
        supplied = (value if phase in ("body_return", "parse_return") else
                    {"key": [0]} if phase == "text_return" else
                    [[0]] if phase == "recursive_return" else
                    object() if phase == "unwind" else [])
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes(supplied)
    finally:
        sys.setprofile(previous)
        if phase == "unwind":
            monitoring.set_events(tool_id, 0)
            monitoring.register_callback(tool_id, monitoring.events.PY_UNWIND, None)
            monitoring.free_tool_id(tool_id)
        monkeypatch.undo()
    assert injected == [True], (phase, target)
    assert calls == [], (phase, target, calls)


@pytest.mark.parametrize("phase", (
    "entry", "original_return", "wrapper_return", "check_return", "unwind",
))
@pytest.mark.parametrize("target", (
    "len", "entries", "message", "depth", "aggregate_body", "constructor",
    "guard_binding", "guard_code", "cast_binding", "cast_code", "visitor", "set",
))
def test_tree_actual_cast_returns_reject_before_behavior(monkeypatch, phase, target):
    _tree_owner_return_proof(monkeypatch, phase, target)


@pytest.mark.parametrize("phase", (
    "text_return", "recursive_return", "body_return", "parse_return",
))
@pytest.mark.parametrize("target", (
    "len", "entries", "reader", "body", "parser", "failure",
))
def test_tree_nested_owner_returns_reject_before_behavior(monkeypatch, phase, target):
    _tree_owner_return_proof(monkeypatch, phase, target)


def test_shared_cast_audit_retains_only_authenticated_text_and_tree_callers():
    source = Path(codec.__file__).read_text()
    owners = {}
    for definition in ast.parse(source).body:
        if isinstance(definition, ast.FunctionDef):
            sites = [node for node in ast.walk(definition) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)
                     and node.func.id in ("cast", "casting")]
            if sites:
                owners[definition.name] = len(sites)
    assert owners == {"_text": 1, "_tree": 1}


@pytest.mark.parametrize("value,wire", (
    ([], b"[]"), ({}, b"{}"), ([0, True, None], b"[0,true,null]"),
    ({"b": [1], "a": "é"}, '{"a":"é","b":[1]}'.encode()),
))
def test_tree_shared_cast_success_preserves_canonical_bytes(value, wire):
    assert codec.canonical_bytes(value) == wire
    assert codec.decode_canonical(wire) == value


@pytest.mark.parametrize("raw,code", (
    (b"owner-local opaque bytes", None),
    (b"\xff", None),
    (b'{"unfinished":', None),
    (b'{"owner_number":1.5}', None),
    (b"[" * 33 + b"0" + b"]" * 33, "limit_exceeded"),
    (b"[" + b"0," * 4_096 + b"0]", "limit_exceeded"),
))
def test_tree_parser_refusal_preserves_opaque_bytes_and_resource_limits(raw, code):
    body = {
        "contract_ref": "contract:fixture", "body_hex": raw.hex(),
        "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }
    expected = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if code is None:
        assert codec.canonical_bytes(body) == expected
        assert codec.decode_canonical(expected) == body
    else:
        for attempt in (lambda: codec.canonical_bytes(body),
                        lambda: codec.decode_canonical(expected)):
            with pytest.raises(codec.WireError) as refused:
                attempt()
            assert type(refused.value) is codec.WireError
            assert refused.value.args == (code,)
            fields = BaseException.__dict__["__dict__"].__get__(refused.value)
            assert fields == {"code": code}


@pytest.mark.parametrize("entrance", ("encode", "decode"))
@pytest.mark.parametrize("field", (
    "code_descriptor", "attribute_fallback", "attribute_reader",
    "missing_code", "none_code", "integer_code", "string_subclass_code",
    "foreign_code", "foreign_key", "dictionary_subclass",
))
def test_tree_parser_exception_fields_refuse_before_foreign_behavior(
    monkeypatch, entrance, field,
):
    tree_code = inspect.unwrap(codec._tree).__code__
    check_code = codec._preparation_check.__code__
    dictionary_slot = BaseException.__dict__["__dict__"]
    calls, admitted = [], []

    def forbidden(*args, **kwargs):
        calls.append(field)
        reason = "exception field behavior must not run"
        raise AssertionError(reason)

    class ForeignString(str):
        __hash__ = str.__hash__
        __eq__ = forbidden

    class ForeignCode:
        __eq__ = forbidden

    class ForeignDictionary(dict):
        items = forbidden

    def observe(frame, event, result):
        if (admitted or event != "return" or frame.f_code is not check_code
                or frame.f_back is None or frame.f_back.f_code is not tree_code):
            return
        error = frame.f_back.f_locals.get("error")
        if type(error) is not codec.WireError:
            return
        admitted.append(True)
        fields = dictionary_slot.__get__(error)
        if field == "code_descriptor":
            monkeypatch.setattr(
                codec.WireError, "code", property(forbidden), raising=False,
            )
        elif field == "attribute_fallback":
            monkeypatch.setattr(
                codec.WireError, "__getattr__", forbidden, raising=False,
            )
        elif field == "attribute_reader":
            monkeypatch.setattr(codec.WireError, "__getattribute__", forbidden)
        elif field == "missing_code":
            fields.clear()
        elif field == "foreign_key":
            fields[ForeignString("other")] = "malformed"
        elif field == "dictionary_subclass":
            dictionary_slot.__set__(error, ForeignDictionary(code="malformed"))
        else:
            fields["code"] = {
                "none_code": None, "integer_code": 1,
                "string_subclass_code": ForeignString("malformed"),
                "foreign_code": ForeignCode(),
            }[field]

    raw = b"owner-local opaque bytes"
    body = {"contract_ref": "contract:fixture", "body_hex": raw.hex(),
            "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest()}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(p.PreparationError):
            if entrance == "encode":
                codec.canonical_bytes(body)
            else:
                codec.decode_canonical(encoded)
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert admitted == [True]
    assert calls == []
    assert codec.canonical_bytes([]) == b"[]"


@pytest.mark.parametrize("caller", (
    "_obj", "_uint", "_enum", "_field", "command_prefix_digest",
))
@pytest.mark.parametrize("target", ("len", "guard_binding", "dispatch_code"))
@pytest.mark.parametrize("phase", ("entry", "check_return"))
def test_former_cast_callers_keep_authenticated_dispatch(
    monkeypatch, caller, target, phase,
):
    function = getattr(codec, caller)
    caller_code = inspect.unwrap(function).__code__
    check_code = p._preparation_check.__code__
    calls, injected, changed_codes = [], [], []
    dispatch_name = {"_obj": "_text", "_uint": "_fail", "_enum": "_fail",
                     "_field": "_schema", "command_prefix_digest": "_schema"}[caller]

    def foreign(*args, **kwargs):
        calls.append("foreign former-cast dispatch")
        reason = "foreign former-cast dispatch"
        raise RuntimeError(reason)

    def poison():
        injected.append(True)
        if target == "dispatch_code":
            dispatch = getattr(codec, dispatch_name)
            changed = foreign.__code__.replace(
                co_freevars=dispatch.__code__.co_freevars,
            )
            changed_codes.append(changed)
            monkeypatch.setattr(dispatch, "__code__", changed)
        else:
            name = "_preparation_check" if target == "guard_binding" else target
            monkeypatch.setattr(codec, name, foreign, raising=False)

    def observe(frame, event, arg):
        if event == "call" and any(frame.f_code is code for code in changed_codes):
            calls.append("foreign former-cast code entry")
        if (phase == "check_return" and not injected and event == "return"
                and frame.f_code is check_code and frame.f_back is not None
                and frame.f_back.f_code is caller_code):
            poison()

    arguments = {"_obj": ({"key": 0},), "_uint": (0,), "_enum": ("x", ("x",)),
                 "_field": ([], "updates"), "command_prefix_digest": ([],)}[caller]
    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        if phase == "entry":
            poison()
        with pytest.raises(p.PreparationError):
            function(*arguments)
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert injected == [True], (caller, target, phase)
    assert calls == [], (caller, target, phase, calls)


@pytest.mark.parametrize("caller,dispatch", (
    ("_field", "_wrapper"), ("_result", "required_witness_roles"),
))
@pytest.mark.parametrize("phase", ("entry", "owner_return", "check_return"))
def test_former_argument_cast_callers_authenticate_retained_targets(
    monkeypatch, caller, dispatch, phase,
):
    import test_codec as framing

    function = getattr(codec, caller)
    original_code = inspect.unwrap(function).__code__
    object_code, check_code = codec._obj.__code__, p._preparation_check.__code__
    arguments = (
        (framing.bundle()["origin_body"], "body:aware.ontology.facade-origin.v1")
        if caller == "_field" else (framing.specimen_result("view.read", "refused"),)
    )
    calls, injected, changed_codes = [], [], []

    def foreign(*args, **kwargs):
        reason = "foreign argument-cast continuation"
        raise RuntimeError(reason)

    def poison():
        injected.append(True)
        target = getattr(codec, dispatch)
        changed = foreign.__code__.replace(co_freevars=target.__code__.co_freevars)
        changed_codes.append(changed)
        monkeypatch.setattr(target, "__code__", changed)

    def observe(frame, event, arg):
        if event == "call" and any(frame.f_code is code for code in changed_codes):
            calls.append("foreign argument-cast code entry")
        watched = object_code if phase == "owner_return" else check_code
        if (not injected and phase != "entry" and event == "return"
                and frame.f_code is watched and frame.f_back is not None
                and frame.f_back.f_code is original_code):
            poison()

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        if phase == "entry":
            poison()
        with pytest.raises(p.PreparationError):
            function(*arguments)
    finally:
        sys.setprofile(previous)
        monkeypatch.undo()
    assert injected == [True], (caller, phase)
    assert calls == [], (caller, phase, calls)


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("binding", ("builtin", "module_shadow", "retained_cell"))
def test_mapped_scan_admits_native_iterator_before_dispatch(phase, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_map = builtins.map
    retained_map = control["native_map"].cell_contents
    original_code = inspect.unwrap(codec._text).__code__
    injected = []

    def change():
        injected.append(True)
        if binding == "retained_cell":
            control["native_map"].cell_contents = None
        else:
            namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
            namespace["map"] = None

    def observe(frame, event, result):
        if event == "return" and frame.f_code is original_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        builtins.__dict__["map"] = original_map
        p.__dict__.pop("map", None)
        control["native_map"].cell_contents = retained_map
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("binding", ("builtin", "module_shadow", "retained_cell"))
@pytest.mark.parametrize("checkpoint", ("dictionary", "sequence"))
def test_mapped_scan_keeps_admitted_dispatch_during_binding_change(
        binding, checkpoint):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_map = builtins.map
    retained_map = control["native_map"].cell_contents
    source, start = inspect.getsourcelines(check)
    marker = ("for key_id, item_id, "
              if checkpoint == "dictionary" else
              "for item_id, expected_id in native_zip(")
    line = start + next(i for i, text in enumerate(source)
                        if marker in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line):
            assert frame.f_locals["mapping"] is original_map
            assert frame.f_locals["identity"] is id
            if not injected:
                injected.append(True)
                if binding == "retained_cell":
                    control["native_map"].cell_contents = None
                    # Trace callbacks synchronize their locals view back to
                    # closure cells; keep the benign mask in that view too.
                    frame.f_locals["native_map"] = None
                else:
                    namespace = (builtins.__dict__
                                 if binding == "builtin" else p.__dict__)
                    namespace["map"] = None
        return observe

    previous = sys.gettrace()
    try:
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["map"] = original_map
        p.__dict__.pop("map", None)
        control["native_map"].cell_contents = retained_map
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("exception_binding", (None, "ValueError", "RuntimeError"))
def test_mapped_dictionary_scan_refuses_change_during_view_creation(exception_binding):
    import builtins

    check = p._preparation_check
    retained = inspect.getclosurevars(check).nonlocals
    target = next(value for value, _ in retained["data_rows"]
                  if type(value) is dict and value)
    before, injected = target.copy(), []
    exception_kind = (builtins.__dict__[exception_binding]
                      if exception_binding else None)

    def observe(frame, event, primitive):
        if (frame.f_code is check.__code__ and event == "c_return"
                and getattr(primitive, "__self__", None) is target
                and getattr(primitive, "__name__", None) == "values"
                and not injected):
            injected.append(True)
            target.clear()
            if exception_binding:
                builtins.__dict__[exception_binding] = None

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.setprofile(previous)
        target.update(before)
        if exception_binding:
            builtins.__dict__[exception_binding] = exception_kind
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("binding", ("map", "id"))
def test_mapped_scan_alias_admission_uses_original_bank_values(binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    cell = control["native_map" if binding == "map" else "native_id"]
    original = cell.cell_contents
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "identity = native_id" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            builtins.__dict__[binding] = None
            if binding == "id":
                cell.cell_contents = None
                frame.f_locals["native_id"] = None
        return observe

    previous = sys.gettrace()
    try:
        if binding == "map":
            cell.cell_contents = None
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__[binding] = original
        cell.cell_contents = original
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("binding", ("builtin", "module_shadow"))
def test_mapped_dictionary_kind_admission_keeps_original_bank_value(binding):
    import builtins

    check = p._preparation_check
    original = builtins.dict
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "if kind_of(value) is not dictionary_kind:" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
            namespace["dict"] = None
        return observe

    previous = sys.gettrace()
    try:
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["dict"] = original
        p.__dict__.pop("dict", None)
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("field", (
    "__name__", "__qualname__", "__module__", "__annotations__"))
def test_fixed_native_metadata_scan_retains_every_field(field, phase):
    target = inspect.unwrap(codec._text)
    original = getattr(target, field)
    injected = []

    def change():
        injected.append(True)
        setattr(target, field, {} if field == "__annotations__" else "benign_mask")

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        setattr(target, field, original)
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("binding", ("builtin", "module_shadow"))
@pytest.mark.parametrize("field", (
    "__name__", "__qualname__", "__module__", "__annotations__"))
def test_fixed_native_metadata_scan_survives_binding_change(field, binding):
    import builtins

    check = p._preparation_check
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "if target." + field + " is not expected:" in text)
    original = builtins.getattr
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
            namespace["getattr"] = None
        return observe

    previous = sys.gettrace()
    try:
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["getattr"] = original
        p.__dict__.pop("getattr", None)
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("field", (
    "__name__", "__qualname__", "__module__", "__annotations__"))
def test_fixed_native_metadata_scan_keeps_retained_fallback(field):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["function_rows"].cell_contents
    row = original_rows[0]
    metadata = tuple((name.encode().decode() if name == field else name, expected)
                     for name, expected in row[5])
    assert next(name for name, _ in metadata if name == field) is not field
    changed = (*row[:5], metadata, row[6])
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "elif get(target, name) is not expected:" in text)
    original_lookup = builtins.getattr
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            assert frame.f_locals["name"] == field
            builtins.__dict__["getattr"] = None
        return observe

    previous = sys.gettrace()
    try:
        control["function_rows"].cell_contents = (changed, *original_rows[1:])
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["getattr"] = original_lookup
        control["function_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("size,index", ((1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2)))
def test_indexed_native_tuple_scan_retains_every_item(size, index, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed = (*value[:index], object(), *value[index + 1:])
        control["data_rows"].cell_contents = ((changed, expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("binding", ("builtin", "module_shadow"))
@pytest.mark.parametrize("size", (1, 2, 3))
def test_indexed_native_tuple_scan_keeps_admitted_identity(size, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "identity(value[0])" in text)
    original_identity = builtins.id
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
            namespace["id"] = None
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["id"] = original_identity
        p.__dict__.pop("id", None)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("kind", (list, set))
def test_indexed_native_tuple_scan_retains_mutable_cardinality_interval(kind):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = kind((object(), object(), object()))
    expected = (id(kind), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "for item_id, expected_id in native_zip" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            assert frame.f_locals["value"] is value
            if kind is list:
                value.append(object())
            else:
                value.add(object())
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("size", (0, 4))
def test_indexed_native_tuple_scan_retains_empty_and_large_cardinality(size, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        control["data_rows"].cell_contents = (
            ((*value, object()), expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("kind", (list, set))
def test_indexed_native_tuple_scan_keeps_literal_kind_during_cell_change(kind):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_tuple = control["native_tuple"].cell_contents
    value = kind((object(), object(), object()))
    expected = (id(kind), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    gate_line = start + next(i for i, text in enumerate(source)
                             if "if kind is tuple_kind and item_count <= 3:" in text)
    fallback_line = start + next(i for i, text in enumerate(source)
                                 if "for item_id, expected_id in native_zip" in text)
    injected, fallback = [], []

    def observe(frame, event, result):
        if frame.f_code is check.__code__ and event == "line":
            if frame.f_lineno == gate_line and not injected:
                injected.append(True)
                control["native_tuple"].cell_contents = kind
            elif frame.f_lineno == fallback_line and not fallback:
                fallback.append(True)
                assert frame.f_locals["value"] is value
                if kind is list:
                    value.append(object())
                else:
                    value.add(object())
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        control["native_tuple"].cell_contents = original_tuple
        control["data_rows"].cell_contents = original_rows
    assert injected == fallback == [True]
    assert check() is None


@pytest.mark.parametrize("kind", (list, set))
def test_indexed_native_tuple_scan_refuses_mutable_expectation_during_cell_change(kind):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_tuple = control["native_tuple"].cell_contents
    value = (object(), object())
    expected = (id(tuple), kind(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "if (native_id(kind) != expected[0]" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            control["native_tuple"].cell_contents = kind
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        control["native_tuple"].cell_contents = original_tuple
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("field", ("key", "value"))
@pytest.mark.parametrize("size,index", ((1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2)))
def test_fused_native_dictionary_scan_retains_every_identity(size, index, field, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    pairs = tuple((object(), object()) for _ in range(size))
    value = dict(pairs)
    expected = (id(dict), tuple((id(key), id(item)) for key, item in pairs))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed = list(pairs)
        key, item = changed[index]
        changed[index] = (object(), item) if field == "key" else (key, object())
        value.clear()
        value.update(changed)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("binding", ("builtin", "module_shadow", "cell"))
@pytest.mark.parametrize("size", (1, 3))
def test_fused_native_dictionary_scan_keeps_admitted_zip(size, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_zip = control["native_zip"].cell_contents
    value = {object(): object() for _ in range(size)}
    expected = (id(dict), tuple((id(key), id(item)) for key, item in value.items()))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "for key_id, item_id, "
                        "(expected_key, expected_item) in zipping(" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            if binding == "cell":
                control["native_zip"].cell_contents = None
            else:
                namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
                namespace["zip"] = None
        return observe

    previous = sys.gettrace()
    try:
        # This benign single-row fixture isolates the new dictionary dispatch.
        # Complete production observation counts are proved on the full rows.
        control["data_rows"].cell_contents = ((value, expected),)
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__["zip"] = original_zip
        p.__dict__.pop("zip", None)
        control["native_zip"].cell_contents = original_zip
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase,size", (("before_iterator", 1), ("before_iterator", 3),
                                       ("after_first_pair", 3)))
@pytest.mark.parametrize("mutation", ("append", "remove"))
def test_fused_native_dictionary_scan_retains_cardinality_intervals(
        phase, size, mutation):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = {object(): object() for _ in range(size)}
    expected = (id(dict), tuple((id(key), id(item)) for key, item in value.items()))
    source, start = inspect.getsourcelines(check)
    snippet = ("for key_id, item_id, "
               "(expected_key, expected_item) in zipping("
               if phase == "before_iterator" else
               "if key_id != expected_key or item_id != expected_item:")
    line = start + next(i for i, text in enumerate(source) if snippet in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            assert frame.f_locals["value"] is value
            if mutation == "append":
                value[object()] = object()
            else:
                value.pop(next(iter(value)))
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("size,index", tuple(
    (size, index) for size in (4, 8, 12) for index in range(size)))
def test_direct_native_tuple_scan_retains_every_identity(size, index, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed = (*value[:index], object(), *value[index + 1:])
        control["data_rows"].cell_contents = ((changed, expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("size", (4, 8, 12))
@pytest.mark.parametrize("primitive,binding", (
    ("id", "builtin"), ("id", "module_shadow"), ("zip", "builtin"),
    ("zip", "module_shadow"), ("zip", "cell")))
def test_direct_native_tuple_scan_keeps_admitted_dispatch(size, primitive, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_primitive = builtins.__dict__[primitive]
    original_zip = control["native_zip"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "for item, expected_id in zipping(" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            if binding == "cell":
                control["native_zip"].cell_contents = None
            else:
                namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
                namespace[primitive] = None
        return observe

    previous = sys.gettrace()
    try:
        # This isolated benign row checks the new dispatch interval. Full
        # production scans retain their separate complete observation proof.
        control["data_rows"].cell_contents = ((value, expected),)
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__[primitive] = original_primitive
        p.__dict__.pop(primitive, None)
        control["native_zip"].cell_contents = original_zip
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("size", (4, 8, 12))
@pytest.mark.parametrize("mutation", ("append", "remove"))
def test_direct_native_tuple_scan_retains_cardinality(size, mutation, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed = (*value, object()) if mutation == "append" else value[:-1]
        control["data_rows"].cell_contents = ((changed, expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("size", (4, 8, 12))
def test_direct_native_tuple_scan_observes_original_item_order(size):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    expected = (id(tuple), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "if identity(item) != expected_id:" in text)
    observed = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line):
            observed.append((frame.f_locals["item"], frame.f_locals["expected_id"]))
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected),)
        sys.settrace(observe)
        assert check() is None
    finally:
        sys.settrace(previous)
        control["data_rows"].cell_contents = original_rows
    assert len(observed) == size
    assert all(item is value[index] and expected_id == expected[1][index]
               for index, (item, expected_id) in enumerate(observed))
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("field", ("key", "value"))
@pytest.mark.parametrize("size,index", tuple(
    (size, index) for size in (1, 3, 8) for index in range(size)))
def test_direct_native_dictionary_scan_retains_every_identity(
        size, index, field, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = {object(): object() for _ in range(size)}
    expected = (id(dict), tuple((id(key), id(item)) for key, item in value.items()))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        pairs = list(value.items())
        key, item = pairs[index]
        pairs[index] = (object(), item) if field == "key" else (key, object())
        control["data_rows"].cell_contents = ((dict(pairs), expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("size", (1, 3))
@pytest.mark.parametrize("phase", ("before_iterator", "before_identity"))
@pytest.mark.parametrize("primitive,binding", (
    ("id", "builtin"), ("id", "module_shadow"), ("zip", "builtin"),
    ("zip", "module_shadow"), ("zip", "cell")))
def test_direct_native_dictionary_scan_keeps_admitted_dispatch(
        size, phase, primitive, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_primitive = builtins.__dict__[primitive]
    original_zip = control["native_zip"].cell_contents
    value = {object(): object() for _ in range(size)}
    expected = (id(dict), tuple((id(key), id(item)) for key, item in value.items()))
    source, start = inspect.getsourcelines(check)
    snippet = ("for key_id, item_id, (expected_key, expected_item) in zipping("
               if phase == "before_iterator" else "item_id = identity(item_id)")
    line = start + next(i for i, text in enumerate(source) if snippet in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            if binding == "cell":
                control["native_zip"].cell_contents = None
            else:
                namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
                namespace[primitive] = None
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected),)
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__[primitive] = original_primitive
        p.__dict__.pop(primitive, None)
        control["native_zip"].cell_contents = original_zip
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("size", (1, 3, 8))
@pytest.mark.parametrize("mismatch", (False, True))
def test_direct_native_dictionary_scan_reads_both_identities_before_comparison(
        size, mismatch):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = {object(): object() for _ in range(size)}
    pairs = tuple(value.items())
    expected_pairs = tuple((id(key), id(item)) for key, item in pairs)
    if mismatch:
        expected_pairs = ((0, expected_pairs[0][1]), *expected_pairs[1:])
    expected = (id(dict), expected_pairs)
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "item_id = identity(item_id)" in text)
    observed = []
    original_identity = id

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "c_call"
                and result is original_identity and frame.f_lineno == line):
            # The original native key map has already observed this key id.
            # The value id runs now, before either key/value comparison.
            observed.append((frame.f_locals["key_id"], frame.f_locals["item_id"]))

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected),)
        sys.setprofile(observe)
        if mismatch:
            with pytest.raises(p.PreparationError):
                check()
        else:
            assert check() is None
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    wanted = pairs[:1 if mismatch else size]
    assert len(observed) == len(wanted)
    assert all(key_id == id(key) and item is expected_item
               for (key_id, item), (key, expected_item)
               in zip(observed, wanted, strict=True))
    assert check() is None


@pytest.mark.parametrize("size", (1, 3))
@pytest.mark.parametrize("phase", ("before_first_identity", "after_first_pair"))
@pytest.mark.parametrize("mutation", ("append", "remove"))
def test_direct_native_dictionary_scan_retains_cardinality_intervals(
        size, phase, mutation):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = {object(): object() for _ in range(size)}
    expected = (id(dict), tuple((id(key), id(item)) for key, item in value.items()))
    source, start = inspect.getsourcelines(check)
    snippet = ("item_id = identity(item_id)" if phase == "before_first_identity"
               else "if key_id != expected_key or item_id != expected_item:")
    line = start + next(i for i, text in enumerate(source) if snippet in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            if mutation == "append":
                value[object()] = object()
            else:
                value.pop(next(iter(value)))
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        sys.settrace(observe)
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("phase", ("entry", "owner_return"))
@pytest.mark.parametrize("dispatch", ("native", "fallback"))
@pytest.mark.parametrize("field", (
    "__name__", "__qualname__", "__module__", "__annotations__"))
def test_direct_metadata_comparison_refuses_each_retained_reference(
        field, dispatch, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["function_rows"].cell_contents
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed_rows = []
        for row in original_rows:
            if row[0] is target:
                metadata = tuple(
                    (name.encode().decode() if dispatch == "fallback" else name,
                     object() if name == field else expected)
                    for name, expected in row[5])
                row = (*row[:5], metadata, row[6])
            changed_rows.append(row)
        control["function_rows"].cell_contents = tuple(changed_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["function_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("dispatch", ("native", "fallback"))
@pytest.mark.parametrize("mismatch", (
    None, "__name__", "__qualname__", "__module__", "__annotations__"))
def test_direct_metadata_comparison_preserves_read_and_refusal_order(
        dispatch, mismatch):
    import dis

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["function_rows"].cell_contents
    row = original_rows[0]
    metadata = tuple(
        (name.encode().decode() if dispatch == "fallback" else name,
         object() if name == mismatch else expected)
        for name, expected in row[5])
    changed = (*row[:5], metadata, row[6])
    fields = ("__name__", "__qualname__", "__module__", "__annotations__")
    source, start = inspect.getsourcelines(check)
    markers = {}
    for instruction in dis.get_instructions(check):
        if instruction.opname == "LOAD_ATTR" and instruction.argval in fields:
            markers[instruction.offset] = "read"
        positions = instruction.positions
        if positions is None or positions.lineno is None:
            continue
        text = source[positions.lineno - start]
        if "elif get(target, name) is not expected:" in text:
            if instruction.opname == "CALL":
                markers[instruction.offset] = "read"
            elif instruction.opname == "IS_OP":
                markers[instruction.offset] = "compare"
        elif ("if target.__" in text and "is not expected:" in text
              and instruction.opname == "IS_OP"):
            markers[instruction.offset] = "compare"
    observed = []

    def observe(code, offset):
        if offset in markers:
            frame = sys._getframe(1)
            observed.append((markers[offset], frame.f_locals["name"]))

    try:
        control["function_rows"].cell_contents = (changed,)
        sys.monitoring.use_tool_id(4, "native metadata read and comparison order")
        sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, observe)
        sys.monitoring.set_local_events(
            4, check.__code__, sys.monitoring.events.INSTRUCTION)
        try:
            if mismatch is None:
                assert check() is None
            else:
                with pytest.raises(p.PreparationError):
                    check()
        finally:
            sys.monitoring.set_local_events(4, check.__code__, 0)
            sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, None)
            sys.monitoring.free_tool_id(4)
    finally:
        control["function_rows"].cell_contents = original_rows
    observed_fields = (fields if mismatch is None
                       else fields[:fields.index(mismatch) + 1])
    assert observed == [(event, field) for field in observed_fields
                        for event in ("read", "compare")]
    assert check() is None


@pytest.mark.parametrize("primitive", ("type", "len"))
@pytest.mark.parametrize("binding", ("builtin", "module_shadow", "retained_cell"))
@pytest.mark.parametrize("phase", ("entry", "owner_return"))
def test_local_native_scan_primitives_refuse_before_owner_continuation(
        primitive, binding, phase):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    cell = control["native_type" if primitive == "type" else "length"]
    original = cell.cell_contents
    original_builtin = builtins.__dict__[primitive]
    namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
    original_present = primitive in namespace
    original_namespace_value = namespace.get(primitive)
    owner_code = inspect.unwrap(codec._text).__code__
    injected = []
    refusal = pytest.raises((p.PreparationError, codec.WireError))

    def change():
        injected.append(True)
        if binding == "retained_cell":
            cell.cell_contents = None
        else:
            namespace[primitive] = None

    def observe(frame, event, result):
        if event == "return" and frame.f_code is owner_code and not injected:
            change()

    previous = sys.getprofile()
    try:
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with refusal:
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        builtins.__dict__[primitive] = original_builtin
        cell.cell_contents = original
        if original_present:
            namespace[primitive] = original_namespace_value
        else:
            namespace.pop(primitive, None)
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("primitive", ("type", "len"))
@pytest.mark.parametrize("binding", ("builtin", "module_shadow", "retained_cell"))
@pytest.mark.parametrize("checkpoint", ("function", "data"))
def test_local_native_scan_primitives_keep_admitted_snapshot(
        primitive, binding, checkpoint):
    import builtins
    import dis

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    cell = control["native_type" if primitive == "type" else "length"]
    original = cell.cell_contents
    original_builtin = builtins.__dict__[primitive]
    namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
    original_present = primitive in namespace
    original_namespace_value = namespace.get(primitive)
    source, start = inspect.getsourcelines(check)
    snippet = ("if kind_of(target) is not function_kind:"
               if checkpoint == "function" else
               "if kind_of(value) is not dictionary_kind:")
    line = start + next(i for i, text in enumerate(source) if snippet in text)
    selected = [instruction.offset for instruction in dis.get_instructions(check)
                if instruction.opname == "LOAD_FAST"
                and instruction.argval == "kind_of"
                and instruction.positions is not None
                and instruction.positions.lineno == line]
    assert len(selected) == 1
    injected, snapshots = [], []
    first_refusal = pytest.raises(p.PreparationError)
    next_refusal = pytest.raises(p.PreparationError)

    def observe(code, offset):
        if offset == selected[0]:
            frame = sys._getframe(1)
            snapshots.append((frame.f_locals["kind_of"], frame.f_locals["size_of"]))
            if not injected:
                injected.append(True)
                if binding == "retained_cell":
                    cell.cell_contents = None
                else:
                    namespace[primitive] = None

    try:
        sys.monitoring.use_tool_id(4, "local native scan snapshot")
        sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, observe)
        sys.monitoring.set_local_events(
            4, check.__code__, sys.monitoring.events.INSTRUCTION)
        try:
            # The complete function table may observe the changed shared type
            # cell and refuse this scan; it must not call the benign None mask.
            if (primitive == "type" and binding == "retained_cell"
                    and checkpoint == "function"):
                with first_refusal:
                    check()
            else:
                assert check() is None
        finally:
            sys.monitoring.set_local_events(4, check.__code__, 0)
            sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, None)
            sys.monitoring.free_tool_id(4)
        with next_refusal:
            check()
    finally:
        builtins.__dict__[primitive] = original_builtin
        cell.cell_contents = original
        if original_present:
            namespace[primitive] = original_namespace_value
        else:
            namespace.pop(primitive, None)
    assert injected == [True]
    assert snapshots and all(kind is type and size is len for kind, size in snapshots)
    assert check() is None


@pytest.mark.parametrize("table", (
    "function_rows", "receiver_function_rows", "data_rows", "receiver_data_rows"))
@pytest.mark.parametrize("replacement", (None, [], frozenset()))
@pytest.mark.parametrize("phase", ("entry", "owner_return"))
def test_grouped_complete_scan_refuses_non_tuple_tables(table, replacement, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    cell = control[table]
    original = cell.cell_contents
    target = inspect.unwrap(codec._text)
    injected = []

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            injected.append(True)
            cell.cell_contents = replacement

    previous = sys.getprofile()
    try:
        if phase == "entry":
            injected.append(True)
            cell.cell_contents = replacement
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        cell.cell_contents = original
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("scan", ("function", "data"))
def test_grouped_complete_scan_preserves_snapshots_and_row_order(scan):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    names = ("function_rows", "receiver_function_rows",
             "data_rows", "receiver_data_rows")
    original = {name: control[name].cell_contents for name in names}
    if scan == "function":
        rows = original["function_rows"][:2]
        first, second = names[:2]
        snippet = "if kind_of(target) is not function_kind:"
        operand = "target"
    else:
        values = ((object(),), (object(),))
        rows = tuple((value, (id(tuple), tuple(id(item) for item in value)))
                     for value in values)
        first, second = names[2:]
        snippet = "if expected[0] == dictionary_kind_id:"
        operand = "value"
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source) if snippet in text)
    observed = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line):
            local = frame.f_locals
            observed.append(local[operand])
            if len(observed) == 1:
                # Keep the trace frame cache and native cell in agreement.
                local[second] = None
                control[second].cell_contents = None
        return observe

    previous = sys.gettrace()
    try:
        for name in names:
            control[name].cell_contents = ()
        control[first].cell_contents = rows[:1]
        control[second].cell_contents = rows[1:]
        sys.settrace(observe)
        assert check() is None
        sys.settrace(previous)
        assert len(observed) == 2
        assert all(value is row[0] for value, row in zip(observed, rows, strict=True))
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        for name in names:
            control[name].cell_contents = original[name]
    assert check() is None


@pytest.mark.parametrize(("size", "mismatch"), (
    (0, None), (1, None), (1, 0), (2, None), (2, 0), (2, 1),
    (3, None), (3, 0), (3, 1), (3, 2)))
def test_short_tuple_completion_preserves_identity_and_comparison_order(
        size, mismatch):
    import dis

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = tuple(object() for _ in range(size))
    identities = tuple(0 if index == mismatch else id(item)
                       for index, item in enumerate(value))
    source, start = inspect.getsourcelines(check)
    markers = {}
    for instruction in dis.get_instructions(check):
        positions = instruction.positions
        if positions is None:
            continue
        line = positions.lineno
        if line is None:
            continue
        text = source[line - start]
        for index in range(3):
            if f"identity(value[{index}])" in text:
                if instruction.opname == "CALL":
                    markers[instruction.offset] = ("read", index)
                elif instruction.opname == "COMPARE_OP":
                    markers[instruction.offset] = ("compare", index)
    observed = []

    def observe(code, offset):
        if offset in markers:
            observed.append(markers[offset])

    try:
        control["data_rows"].cell_contents = ((value, (id(tuple), identities)),)
        sys.monitoring.use_tool_id(4, "short tuple complete observation order")
        sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, observe)
        sys.monitoring.set_local_events(
            4, check.__code__, sys.monitoring.events.INSTRUCTION)
        try:
            if mismatch is None:
                assert check() is None
            else:
                with pytest.raises(p.PreparationError):
                    check()
        finally:
            sys.monitoring.set_local_events(4, check.__code__, 0)
            sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, None)
            sys.monitoring.free_tool_id(4)
    finally:
        control["data_rows"].cell_contents = original_rows
    count = size if mismatch is None else mismatch + 1
    assert observed == [(event, index) for index in range(count)
                        for event in ("read", "compare")]
    assert check() is None


@pytest.mark.parametrize(("size", "mismatch"), (
    (0, None), (1, None), (1, 0), (4, None), (4, 0), (4, 2), (4, 3),
    (8, None), (8, 0), (8, 3), (8, 7)))
def test_direct_frozenset_scan_preserves_read_and_first_refusal_order(size, mismatch):
    import dis

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = frozenset(object() for _ in range(size))
    items = tuple(value)
    identities = tuple(0 if index == mismatch else id(item)
                       for index, item in enumerate(items))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "if identity(item) != expected_id:" in text)
    markers = {}
    for instruction in dis.get_instructions(check):
        positions = instruction.positions
        if positions is not None and positions.lineno == line:
            if instruction.opname == "CALL":
                markers[instruction.offset] = "read"
            elif instruction.opname == "COMPARE_OP":
                markers[instruction.offset] = "compare"
    assert sorted(markers.values()) == ["compare", "read"]
    observed = []

    def observe(code, offset):
        if offset in markers:
            observed.append(markers[offset])

    try:
        control["data_rows"].cell_contents = ((value, (id(frozenset), identities)),)
        sys.monitoring.use_tool_id(4, "direct frozen set observation order")
        sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, observe)
        sys.monitoring.set_local_events(
            4, check.__code__, sys.monitoring.events.INSTRUCTION)
        try:
            if mismatch is None:
                assert check() is None
            else:
                with pytest.raises(p.PreparationError):
                    check()
        finally:
            sys.monitoring.set_local_events(4, check.__code__, 0)
            sys.monitoring.register_callback(4, sys.monitoring.events.INSTRUCTION, None)
            sys.monitoring.free_tool_id(4)
    finally:
        control["data_rows"].cell_contents = original_rows
    count = size if mismatch is None else mismatch + 1
    assert observed == [event for _ in range(count) for event in ("read", "compare")]
    assert check() is None


@pytest.mark.parametrize("size", (0, 4, 8))
@pytest.mark.parametrize("primitive,binding", (
    ("id", "builtin"), ("id", "module_shadow"), ("zip", "builtin"),
    ("zip", "module_shadow"), ("zip", "cell"),
    ("frozenset", "builtin"), ("frozenset", "module_shadow")))
def test_direct_frozenset_scan_keeps_admitted_dispatch(size, primitive, binding):
    import builtins

    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    original_primitive = builtins.__dict__[primitive]
    original_zip = control["native_zip"].cell_contents
    value = frozenset(object() for _ in range(size))
    expected = (id(frozenset), tuple(id(item) for item in value))
    source, start = inspect.getsourcelines(check)
    line = start + next(i for i, text in enumerate(source)
                        if "kind is tuple_kind or kind is immutable_set_kind" in text)
    injected = []

    def observe(frame, event, result):
        if (frame.f_code is check.__code__ and event == "line"
                and frame.f_lineno == line and not injected):
            injected.append(True)
            if binding == "cell":
                control["native_zip"].cell_contents = None
            else:
                namespace = builtins.__dict__ if binding == "builtin" else p.__dict__
                namespace[primitive] = None
        return observe

    previous = sys.gettrace()
    try:
        control["data_rows"].cell_contents = ((value, expected),)
        sys.settrace(observe)
        assert check() is None
        with pytest.raises(p.PreparationError):
            check()
    finally:
        sys.settrace(previous)
        builtins.__dict__[primitive] = original_primitive
        p.__dict__.pop(primitive, None)
        control["native_zip"].cell_contents = original_zip
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert check() is None


@pytest.mark.parametrize("size", (1, 4, 8))
@pytest.mark.parametrize("mutation", ("append", "remove"))
@pytest.mark.parametrize("phase", ("entry", "owner_return"))
def test_direct_frozenset_scan_retains_cardinality(size, mutation, phase):
    check = p._preparation_check
    control = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    original_rows = control["data_rows"].cell_contents
    value = frozenset(object() for _ in range(size))
    expected = (id(frozenset), tuple(id(item) for item in value))
    target = inspect.unwrap(codec._text)
    injected = []

    def change():
        injected.append(True)
        changed = (value | {object()} if mutation == "append"
                   else value - {next(iter(value))})
        control["data_rows"].cell_contents = ((changed, expected), *original_rows)

    def observe(frame, event, result):
        if frame.f_code is target.__code__ and event == "return" and not injected:
            change()

    previous = sys.getprofile()
    try:
        control["data_rows"].cell_contents = ((value, expected), *original_rows)
        assert check() is None
        if phase == "entry":
            change()
        else:
            sys.setprofile(observe)
        with pytest.raises((p.PreparationError, codec.WireError)):
            codec.canonical_bytes({"fixture": 1})
    finally:
        sys.setprofile(previous)
        control["data_rows"].cell_contents = original_rows
    assert injected == [True]
    assert codec.canonical_bytes({"fixture": 1}) == b'{"fixture":1}'


@pytest.mark.parametrize("helper_name", ("_positive_canonical_data", "_positive_decode_data"))
def test_positive_native_unavailable_refuses_before_mutable_dependencies(helper_name):
    if codec._positive_canonical_entry is not None:
        pytest.skip("requires the real absent optional native feature profile")
    # Exercise the exact original helper body: the first unavailable refusal
    # must be safe even before the surrounding prepared wrapper's admission.
    original = inspect.unwrap(getattr(codec, helper_name))
    namespace = vars(codec)
    effects = []

    class ForeignError(ValueError):
        def __new__(cls, *args, **kwargs):
            effects.append("exception_constructor")
            raise AssertionError("substituted exception constructor called")

    def foreign(*args, **kwargs):
        effects.append("dependency")
        raise AssertionError("substituted dependency called")

    for name, replacement in (
        ("_preparation_failure", ForeignError), ("ValueError", ForeignError),
        ("BaseException", ForeignError), ("type", foreign), ("tuple", foreign),
        ("_positive_native_unavailable_type", ForeignError),
        ("_positive_canonical_entry", foreign), ("_preparation_check", foreign),
        ("_parse", foreign), ("_body", foreign), ("_dump", foreign),
    ):
        present, saved = name in namespace, namespace.get(name)
        namespace[name] = replacement
        try:
            try:
                original(object(), object())
            except ValueError as error:
                assert type(error) is ValueError
                assert error.args == ("positive_native_data_unavailable",)
            else:
                raise AssertionError("unavailable native helper returned success")
            assert effects == [], name
        finally:
            if present:
                namespace[name] = saved
            else:
                del namespace[name]
    assert codec.canonical_bytes({"unchanged": True}) == b'{"unchanged":true}'


@pytest.mark.parametrize("helper_name", ("_positive_canonical_data", "_positive_decode_data"))
def test_positive_native_unavailable_releases_rejected_payload_and_policy(helper_name):
    import gc
    import weakref

    if codec._positive_canonical_entry is not None:
        pytest.skip("requires the real absent optional native feature profile")
    helper = getattr(codec, helper_name)
    held = []
    for _ in range(2):
        try:
            helper(None, None)
        except ValueError as error:
            assert type(error) is ValueError
            assert error.args == ("positive_native_data_unavailable",)
            held.append(error)
        else:
            raise AssertionError("unavailable native helper returned success")
    assert held[0] is not held[1]
    held.clear()
    gc.collect()

    class Payload:
        pass

    def refuse_once():
        payload, policy = Payload(), Payload()
        references = (weakref.ref(payload), weakref.ref(policy))
        try:
            helper(payload, policy)
        except ValueError as error:
            assert type(error) is ValueError
            assert error.args == ("positive_native_data_unavailable",)
        else:
            raise AssertionError("unavailable native helper returned success")
        return references

    references = [reference for _ in range(50) for reference in refuse_once()]
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("name_kind", ("foreign", "str_subclass"))
def test_positive_native_optional_loader_name_refuses_without_foreign_comparison(name_kind):
    import subprocess

    # A fresh ordinary import executes the real codec source against a native
    # ModuleNotFoundError, rather than substituting/reimplementing its handler.
    source = Path(codec.__file__).resolve()
    script = r'''
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import sys
from pathlib import Path
source = Path(sys.argv[1])
expected = sys.argv[2]
name_kind = sys.argv[3]
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
root = source.parent.parent
sys.path.insert(0, str(root))
package = 'aware_ontology_object_facade_client'
selected = importlib.machinery.PathFinder.find_spec(package, [str(root)])
assert selected is not None and Path(selected.origin).resolve() == source.parent / '__init__.py'
effects = []
class ForeignName:
    def __eq__(self, other):
        effects.append('equality')
        return False
    def __ne__(self, other):
        effects.append('inequality')
        return True
class ForeignString(str):
    __eq__ = ForeignName.__eq__
    __ne__ = ForeignName.__ne__
kernel = package + '._preparation_scan'
name = ForeignName() if name_kind == 'foreign' else ForeignString(kernel)
refusal = ModuleNotFoundError('malformed optional native loader name', name=name)
class RejectNative(importlib.abc.MetaPathFinder):
    calls = 0
    def find_spec(self, fullname, path=None, target=None):
        if fullname == kernel:
            self.calls += 1
            raise refusal
finder = RejectNative()
sys.meta_path.insert(0, finder)
try:
    try:
        importlib.import_module(package)
    except ModuleNotFoundError as error:
        assert error is refusal
    else:
        raise AssertionError('malformed loader name selected portable fallback')
finally:
    sys.meta_path.remove(finder)
assert finder.calls == 1
assert effects == []
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
print(json.dumps({'attempts': finder.calls, 'foreign_effects': effects}))
'''
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(source),
         hashlib.sha256(source.read_bytes()).hexdigest(), name_kind],
        check=True, text=True, capture_output=True, timeout=15,
    )
    assert json.loads(result.stdout) == {"attempts": 1, "foreign_effects": []}
