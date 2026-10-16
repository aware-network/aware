"""Original factory/product/catalog ports, not Workspace/Policy bootstrap."""

from __future__ import annotations

import ast
import asyncio
import copy
import inspect
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_module_manifest_contract_runtime import grammar_factory as f
from aware_code_semantic_contract_runtime import grammar_product_contracts as g
from aware_code_semantic_contract_runtime import product_contribution as p
from aware_code_semantic_contract_runtime import selected_provider as s
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractMatch,
    CodeSemanticPackagePlanningContext,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticMaterializationIntent,
)
from aware_code_semantic_contract_runtime.stage_contribution import (
    close_selected_provider_stage_contribution,
    compose_selected_provider_stage_catalog_input,
    issue_selected_provider_stage_contribution,
    produce_selected_provider_stage_catalog_contribution,
)
from test_stage_contribution import _catalog_product as root_catalog_fixture
from test_stage_contribution import factory_fixture as root_factory_fixture

MOD = Path(__file__).resolve().parents[1]
REPO = next(x for x in MOD.parents if (x / ".git").is_dir())
SEM = (
    REPO / "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python"
)
BASE = "506ba250d161bfac16ad8cd66fd821953a433898"
FACTORIES = (
    f.construct_grammar_profile_selection_product,
    f.construct_grammar_syntax_binding_product,
)


@pytest.fixture(scope="module")
def admissions():
    # Original functions and issuer, not a fixture factory or parent flag.
    return tuple(
        s._admit_selected_provider_factory(
            factory_ref=fn.__module__ + ":" + fn.__name__,
            provider_key=fn().binding.provider_key,
            selection_factory=fn,
        )
        for fn in FACTORIES
    )


@pytest.fixture(params=(0, 1), ids=("profile", "syntax"))
def original(request, admissions):
    value = p.issue_selected_provider_product_contribution(admissions[request.param])
    try:
        yield value
    finally:
        p.close_selected_provider_product_contribution(value)


@pytest.mark.parametrize("fn", FACTORIES)
def test_fresh_complete_products_and_original_bound_methods(fn):
    a, b = fn(), fn()
    assert type(a) is s._SelectedProviderFactoryProduct
    assert a.runtime is not b.runtime and a.provider is not b.provider
    assert a.runtime.profile == b.runtime.profile and a.binding == b.binding
    assert a.executable_entrance.__self__ is a.provider
    assert a.executable_entrance.__func__ is type(a.provider).execute
    assert a.input_closure_entrance.__self__ is a.provider
    assert a.input_closure_entrance.__func__ is type(a.provider).input_closure
    assert not inspect.signature(fn).parameters
    assert a.catalog_contribution_producer is f.produce_grammar_product_catalog
    stage = json.loads(a.configuration_body)["slot"]
    assert a.runtime.profile == g.grammar_operational_profile(stage)
    assert set(a.runtime._body_codecs) == set(g.grammar_operational_contracts(stage))
    assert len(a.runtime._body_codecs) == (7 if stage == "syntax_binding" else 6)
    assert all(
        a.runtime._body_codecs[ref] is not b.runtime._body_codecs[ref]
        for ref in a.runtime._body_codecs
    )


@pytest.mark.parametrize("fn", FACTORIES)
def test_frozen_implementation_configuration_and_binding(fn):
    product = fn()
    wire = json.loads(product.semantic_implementation_contract_body)
    assert set(wire) == {
        "contract",
        "slot",
        "profile",
        "provider",
        "body_codecs",
        "entrances",
        "validation_recipe",
    }
    assert canonical_json_bytes(wire) == product.semantic_implementation_contract_body
    assert wire["profile"] == product.runtime.profile.to_wire()
    assert wire["provider"] == product.provider.declaration.to_wire()
    assert wire["entrances"]["factory"] == fn.__module__ + ":" + fn.__name__
    refs = tuple(row["contract"] for row in wire["body_codecs"])
    assert refs == tuple(
        ref.to_wire() for ref in g.grammar_operational_contracts(wire["slot"])
    )
    assert product.binding.implementation.closure_digest == ContentDigest.of_bytes(
        product.semantic_implementation_contract_body
    )
    assert product.binding.configuration.digest == ContentDigest.of_bytes(
        product.configuration_body
    )
    assert json.loads(product.configuration_body) == {
        "contract": "aware.code.grammar-source-role-configuration.v1",
        "slot": wire["slot"],
        "options": {},
    }
    plan = json.loads(
        (
            REPO
            / "docs/reports/code-language-grammar-factory-source-installation-20261012.json"
        ).read_bytes()
    )
    row = next(x for x in plan["factory_products"] if x["slot"] == wire["slot"])
    assert (
        product.binding.implementation.implementation_ref == row["implementation_ref"]
    )
    assert product.binding.configuration.configuration_ref == row["configuration_ref"]
    assert wire["entrances"]["interpretation"] == row["interpretation"]
    for ref, binding in zip(
        g.grammar_operational_contracts(wire["slot"]), wire["body_codecs"], strict=True
    ):
        assert (
            binding["implementation"]
            == product.runtime._body_codecs[ref].implementation.to_wire()
        )


def test_actual_registration_catalog_single_use_and_identity(original):
    value = p.read_selected_provider_product_contribution(original)
    catalog = p.produce_selected_provider_product_catalog_contribution(original)
    repeated = p.read_selected_provider_product_catalog_contribution(original)
    assert repeated.entries is catalog.entries and repeated.planner is catalog.planner
    (entry,) = catalog.entries
    assert entry.profile_declaration == value.profile
    assert entry.provider_execution_bindings == (value.binding,)
    assert catalog.executables == (
        (value.binding.implementation, value.binding.configuration, value.executable),
    )
    assert entry.semantic_owner_key == "aware_code.grammar"
    assert entry.package_families == ("public",) and entry.package_roles == (
        "aware_code.grammar",
    )
    assert entry.manifest_contracts == (g.GRAMMAR_SOURCE_ROLE_SELECTION_REF,)
    assert tuple(x.role for x in entry.result_product_contracts) == tuple(
        sorted((value.profile.terminal_result_role, value.profile.terminal_effect_role))
    )
    assert entry.dependency_planner_contract == g.GRAMMAR_SOURCE_ROLE_PLANNER_REF
    assert (
        entry.dependency_planner_implementation.closure_digest
        == ContentDigest.of_bytes(g.GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR)
    )
    with pytest.raises(ContractViolation, match="already consumed"):
        p.produce_selected_provider_product_catalog_contribution(original)
    with pytest.raises(TypeError):
        copy.copy(original)


def test_two_products_compose_original_catalog_input(admissions):
    # Root pair is an explicit existing fixture. Grammar products, factory
    # registrations and all compose calls are original; no catalog is admitted.
    root_factory, _, _ = root_factory_fixture(catalog_producer=root_catalog_fixture)
    root = issue_selected_provider_stage_contribution(root_factory)
    produce_selected_provider_stage_catalog_contribution(root)
    originals = tuple(
        p.issue_selected_provider_product_contribution(x) for x in admissions
    )
    try:
        for original in originals:
            p.produce_selected_provider_product_catalog_contribution(original)
        with pytest.raises(ContractViolation, match="original stage contributions"):
            compose_selected_provider_stage_catalog_input(
                (),
                product_contributions=originals,
                catalog_ref="source-proof:no-root",
                catalog_generation=1,
            )
        catalog = compose_selected_provider_stage_catalog_input(
            (root,),
            product_contributions=originals,
            catalog_ref="source-proof:grammar-products",
            catalog_generation=1,
        )
        assert len(catalog.entries) == 4
        assert tuple(
            x.semantic_provider_key
            for x in catalog.entries
            if x.semantic_owner_key == "aware_code.grammar"
        ) == (
            "aware_code.grammar.profile_selection",
            "aware_code.grammar.syntax_binding",
        )
        with pytest.raises(ContractViolation):
            compose_selected_provider_stage_catalog_input(
                (root,),
                product_contributions=originals + (originals[0],),
                catalog_ref="source-proof:duplicate",
                catalog_generation=1,
            )
    finally:
        for original in reversed(originals):
            p.close_selected_provider_product_contribution(original)
        close_selected_provider_stage_contribution(root)


def test_detached_product_cannot_substitute_for_contribution():
    for value in (object(), FACTORIES[0](), FACTORIES[1]()):
        with pytest.raises((TypeError, ContractViolation)):
            f.produce_grammar_product_catalog(value)


@pytest.mark.parametrize(
    "name",
    (
        "profile",
        "provider",
        "binding",
        "executable",
        "producer",
        "input_closure",
        "runtime",
        "implementation_body",
        "configuration",
    ),
)
def test_original_registration_substitutions_refuse(original, name):
    product = p._CONTRIBUTIONS[original].product
    if name == "profile":
        owner, field, changed = (
            product.runtime,
            "_profile",
            replace(product.runtime.profile, profile_ref="foreign-profile"),
        )
    elif name == "provider":
        owner, field, changed = product, "provider", FACTORIES[0]().provider
    elif name == "binding":
        owner, field, changed = (
            product,
            "binding",
            replace(product.binding, provider_key="foreign-provider"),
        )
    elif name == "executable":
        owner, field, changed = product, "executable_entrance", lambda *_: None
    elif name == "producer":
        owner, field, changed = product, "catalog_contribution_producer", lambda _: None
    elif name == "input_closure":
        owner, field, changed = product, "input_closure_entrance", lambda _: None
    elif name == "runtime":
        owner, field, changed = (
            product,
            "runtime",
            (
                FACTORIES[1]
                if type(product.provider) is f.GrammarSyntaxBindingProvider
                else FACTORIES[0]
            )().runtime,
        )
    elif name == "implementation_body":
        owner, field, changed = product, "semantic_implementation_contract_body", b"{}"
    else:
        owner, field, changed = product, "configuration_body", b"{}"
    previous = getattr(owner, field)
    object.__setattr__(owner, field, changed)
    try:
        with pytest.raises((TypeError, ContractViolation)):
            p.produce_selected_provider_product_catalog_contribution(original)
    finally:
        object.__setattr__(owner, field, previous)


def planner_inputs(catalog):
    (entry,) = catalog.entries
    package = SemanticPackageCoordinate(
        "source-proof:customer", "code", ContentDigest.of_bytes(b"manifest")
    )
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="resolve_grammar_profile",
        requested_semantic_root_refs=("source-proof:unsupported-target",),
        requested_terminal_output_roles=tuple(
            row.role for row in entry.result_product_contracts
        ),
        semantic_configuration_coordinate=None,
    )
    context = CodeSemanticPackagePlanningContext.create(
        package=package,
        package_family="public",
        package_role="aware_code.grammar",
        manifest_contract=g.GRAMMAR_SOURCE_ROLE_SELECTION_REF,
        code_intent=intent,
        required_result_products=entry.result_product_contracts,
        required_semantic_provider_keys=(entry.semantic_provider_key,),
    )
    return {
        "package": package,
        "intent": intent,
        "selected_match": CodeSemanticContractMatch.create(
            context=context, selected_binding=entry
        ),
        "planning_input": SemanticDependencyPlanningInput(
            package, ContentDigest.of_bytes(b"source"), ()
        ),
    }


def test_valid_planner_refuses_instead_of_empty_demands(original):
    catalog = p.produce_selected_provider_product_catalog_contribution(original)
    with pytest.raises(ContractViolation, match="require original source-role join"):
        asyncio.run(catalog.planner.plan(**planner_inputs(catalog)))


@pytest.mark.parametrize(
    "field", ("package", "intent", "selected_match", "planning_input")
)
def test_planner_validates_inputs_before_unsupported_disposition(original, field):
    catalog = p.produce_selected_provider_product_catalog_contribution(original)
    values = planner_inputs(catalog)
    values[field] = object()
    with pytest.raises(TypeError, match="exact grammar planner input"):
        asyncio.run(catalog.planner.plan(**values))


def test_retirement_refuses_before_planner_payload_access(admissions):
    original = p.issue_selected_provider_product_contribution(admissions[0])
    catalog = p.produce_selected_provider_product_catalog_contribution(original)
    p.close_selected_provider_product_contribution(original)
    with pytest.raises(ContractViolation, match="unavailable"):
        asyncio.run(
            catalog.planner.plan(
                package=object(),
                intent=object(),
                selected_match=object(),
                planning_input=object(),
            )
        )


@pytest.mark.parametrize("fn", FACTORIES)
@pytest.mark.parametrize("port", ("input_closure", "execute", "derive"))
def test_construction_never_grants_source_execution(fn, port):
    provider = fn().provider
    with pytest.raises(
        ContractViolation, match="requires original source-role attachment"
    ):
        if port == "input_closure":
            provider.input_closure(object())
        elif port == "execute":
            provider.execute(object(), object())
        else:
            asyncio.run(provider.derive(object()))


@pytest.mark.parametrize(
    "name,ref",
    (
        ("planner", g.GRAMMAR_SOURCE_ROLE_PLANNER_REF),
        ("demand", g.GRAMMAR_SOURCE_ROLE_DEMAND_REF),
        ("target_intent", g.GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF),
    ),
)
def test_frozen_descriptor_references(name, ref):
    contract = json.loads(
        (
            REPO / "docs/reports/code-language-grammar-product-contract-20261012.json"
        ).read_bytes()
    )
    descriptor = contract["descriptors"][name]
    assert ref.schema_digest == ContentDigest.of_bytes(canonical_json_bytes(descriptor))
    if name == "planner":
        assert g.GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR == canonical_json_bytes(
            descriptor
        )


@pytest.mark.parametrize(
    "ref", (g.GRAMMAR_SOURCE_ROLE_DEMAND_REF, g.GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF)
)
@pytest.mark.parametrize("port", ("encode", "decode"))
@pytest.mark.parametrize("kind", ("empty", "json", "foreign"))
def test_graph_value_and_write_permission_are_not_admitted(ref, port, kind):
    class Foreign:
        def __getattribute__(self, name):
            raise AssertionError("refusal must not call foreign data")

    value = {"empty": b"", "json": b"{}", "foreign": Foreign()}[kind]
    with pytest.raises(ContractViolation, match="not admitted"):
        getattr(g.CodeGrammarUnadmittedGraphCodec(ref), port)(value)


def test_owner_asts_runtime_and_base_metadata_preserved():
    path = SEM / "aware_code_semantic_contract_runtime/grammar_product_contracts.py"
    previous = subprocess.check_output(
        ["git", "show", f"{BASE}:{path.relative_to(REPO)}"], cwd=REPO
    )
    old, new = ast.parse(previous), ast.parse(path.read_bytes())
    nodes = {
        n.name: ast.dump(n)
        for n in new.body
        if isinstance(n, (ast.ClassDef, ast.FunctionDef))
    }
    for node in old.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            assert nodes[node.name] == ast.dump(node)
    for path in (
        MOD / "pyproject.toml",
        SEM / "pyproject.toml",
        SEM / "aware_code_semantic_contract_runtime/runtime.py",
    ):
        assert path.read_bytes() == subprocess.check_output(
            ["git", "show", f"{BASE}:{path.relative_to(REPO)}"], cwd=REPO
        )


def test_site_free_import_construct_no_admission_or_higher_owners():
    env = {
        **os.environ,
        "PYTHONPATH": str(MOD) + ":" + str(SEM),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    code = """
import sys
from aware_code_semantic_contract_runtime import selected_provider as s
before = (len(s._FACTORIES),len(s._REGISTRATIONS),len(s._SELECTION_ROOTS))
from aware_code_module_manifest_contract_runtime.grammar_factory import construct_grammar_profile_selection_product,construct_grammar_syntax_binding_product
construct_grammar_profile_selection_product(); construct_grammar_syntax_binding_product()
assert before == (len(s._FACTORIES),len(s._REGISTRATIONS),len(s._SELECTION_ROOTS))
assert not any(k.startswith(('aware_workspace','aware_code_retained_registry_policy','aware_language','aware_meta','aware_ontology','aware_dev','aware_sdk','aware_service')) for k in sys.modules)
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-S", "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("index", (0, 1), ids=("profile", "syntax"))
def test_committed_predecessor_exhibits_provider_and_entrance_gap_in_isolated_process(
    index,
):
    # Run unchanged current factory construction over the committed old product
    # owner in a disposable process. No original registry in this pytest process
    # is replaced or shared with the child.
    program = r"""
import json, subprocess, sys
from dataclasses import replace
from aware_code_semantic_contract_runtime import product_contribution as p
from aware_code_semantic_contract_runtime import selected_provider as s
raw = subprocess.check_output(["git", "show", sys.argv[1] + ":" + sys.argv[2]], cwd=sys.argv[3])
exec(compile(raw, "<committed-product-owner>", "exec"), p.__dict__)
from aware_code_module_manifest_contract_runtime import grammar_factory as f
fn = (f.construct_grammar_profile_selection_product, f.construct_grammar_syntax_binding_product)[int(sys.argv[4])]
a = s._admit_selected_provider_factory(factory_ref=fn.__module__+":"+fn.__name__,
    provider_key=fn().binding.provider_key, selection_factory=fn)
original = p.issue_selected_provider_product_contribution(a)
product = p._CONTRIBUTIONS[original].product
old_provider = product.provider
replacement = fn().provider
object.__setattr__(product, "provider", replacement)
assert p.read_selected_provider_product_contribution(original).executable is replacement
object.__setattr__(product, "provider", old_provider)
old_execute = product.executable_entrance
object.__setattr__(product, "executable_entrance", lambda *_: None)
p.read_selected_provider_product_contribution(original)
object.__setattr__(product, "executable_entrance", old_execute)
p.close_selected_provider_product_contribution(original)
print(json.dumps({"provider_substitution_accepted": True, "executable_substitution_accepted": True}))
"""
    env = {
        **os.environ,
        "PYTHONPATH": str(MOD) + ":" + str(SEM),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    relative = (
        SEM / "aware_code_semantic_contract_runtime/product_contribution.py"
    ).relative_to(REPO)
    done = subprocess.run(
        [
            sys.executable,
            "-B",
            "-S",
            "-c",
            program,
            BASE,
            str(relative),
            str(REPO),
            str(index),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == {
        "provider_substitution_accepted": True,
        "executable_substitution_accepted": True,
    }
