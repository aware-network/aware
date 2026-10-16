"""Profile/source correspondence; the catalog-parent/input fixtures are explicit.

The real catalog resolver and codecs execute. Portable grouped source inputs
and the catalog parent are not production Workspace/Policy admission.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace

import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as owner,
)
from aware_code_module_manifest_contract_runtime.grammar_factory import (
    construct_grammar_profile_selection_product,
    construct_grammar_syntax_binding_product,
)
from aware_code_module_manifest_contract_runtime.grammar_profile_source import (
    GrammarProfileSourceError,
)
from aware_code_semantic_contract_runtime.catalog_host_leg import (
    prepare_code_catalog_leg,
    published_code_catalog_leg,
    revoke_code_catalog_leg,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarSourceRoleSelectionV1,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarProfileSelectionCodec,
    grammar_profile_selection_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    CodeGrammarDeclarationSourceV1,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
)
from aware_code_semantic_contract_runtime.source_origin import decode_source_origin
from test_catalog_host_leg import Owner as CatalogParentFixture
from test_grammar_declaration_context import input_value, portable_group
from test_grammar_profile_source import PROFILE
from test_materialization_catalog import _binding, _catalog, _execution_closure
from test_retained_declaration_scope import body
from test_retained_declaration_scope import fixture as declaration_fixture
from test_syntax_declaration import source


def supplied_input(
    *, authored=None, stage="profile_selection", module_body=None, package_kind=None
):
    closure = declaration_fixture()
    provider_module = module_body or source().replace(
        b'kind = "code"', b'kind = "sdk"'
    ).replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    scopes = []
    for scope in closure.scopes:
        module = replace(
            scope.projection.modules[0],
            manifest=body(
                scope.projection.modules[0].manifest.relative_path, provider_module
            ),
        )
        package = replace(
            scope.projection.packages[0],
            package_id="provider",
            **({"package_kind": package_kind} if package_kind else {}),
        )
        scopes.append(
            replace(
                scope,
                projection=replace(
                    scope.projection, modules=(module,), packages=(package,)
                ),
            )
        )
    raw = (
        authored
        or PROFILE.split(b"[[providers]]")[0].replace(
            b'key = "grammar.example"', b'key = "default"'
        )
        + b'[[providers]]\nmodule_id="sdk"\nprovider_key="demo"\n'
    )
    publication = closure.local_profiles[0]
    manifest = body(publication.manifest.relative_path, raw)
    closure = replace(
        closure,
        scopes=tuple(scopes),
        local_profiles=(replace(publication, manifest=manifest),),
        profile_associations=(
            replace(closure.profile_associations[0], manifest=manifest),
        ),
    )
    group = portable_group(closure)
    ordinary = input_value(group, closure)
    expected = SemanticInputProductionExpectation.create(
        use_ref=ordinary.use_ref,
        operation_ref=ordinary.operation_ref,
        stage=stage,
        package_identity=ordinary.package_identity,
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in ordinary.sources),
        context_bodies=ordinary.context_bodies,
    )
    value = SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        ordinary.sources,
        expected.input_digest,
        expected.context_bodies,
    )
    selected = CodeGrammarSourceRoleSelectionV1(
        value.operation_ref,
        stage,
        value.input_digest,
        group.root_occurrence_ref,
        publication.profile_key,
        CodeGrammarDeclarationSourceV1(
            closure.repository_binding_ref,
            publication.owning_scope_key,
            "profile",
            manifest.relative_path,
            manifest.body_ref,
            manifest.content_digest,
            len(raw),
        ),
    )
    occurrence = next(
        row.occurrence_ref
        for row in group.members
        if decode_source_origin(bytes.fromhex(row.origin_body_hex)).occurrence.scope_key
        == publication.owning_scope_key
    )
    return value, selected, (occurrence,), group


def v2_supplied_input(
    profile, *, stage="profile_selection", nomination=None, syntax_table=None
):
    from test_grammar_profile_source import v2_authored

    module, raw = v2_authored(
        profile if nomination is None else nomination, syntax_table=syntax_table
    )
    module = module.replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    return supplied_input(
        authored=raw, stage=stage, module_body=module, package_kind="code"
    )


@pytest.fixture
def admitted_catalog():
    binding = _binding(provider_key="demo")
    # Runtime identity deliberately differs from the authored selector. Neither
    # ref nor version is inferred from TOML's format or profile key.
    profile = replace(
        binding.profile_declaration, profile_ref="original.runtime.profile", version="9"
    )
    binding = CodeSemanticMaterializationProfileBinding.create(
        **{
            field.name: profile
            if field.name == "profile_declaration"
            else getattr(binding, field.name)
            for field in fields(binding)
            if field.name != "binding_digest"
        }
    )
    catalog = _catalog(binding)
    executables, planners = _execution_closure(catalog)
    parent = CatalogParentFixture()
    leg = prepare_code_catalog_leg(
        joint_host=parent,
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
    )
    parent.published = True  # Explicit fixture; never claimed as host authority.
    _, resolver = published_code_catalog_leg(leg)
    try:
        yield parent, resolver, profile, binding
    finally:
        revoke_code_catalog_leg(leg)


def arguments(admitted_catalog, **changes):
    value, selected, occurrences, _ = supplied_input()
    _, catalog, profile, _ = admitted_catalog
    return dict(
        input=value,
        selection=selected,
        profile=profile,
        catalog=catalog,
        provider_occurrences=occurrences,
        **changes,
    )


def test_complete_original_profile_and_exact_owner_body(admitted_catalog):
    args = arguments(admitted_catalog)
    result = owner.produce_grammar_profile_selection(**args)
    assert result == grammar_profile_selection_body(args["profile"])
    assert (
        CodeGrammarProfileSelectionCodec().decode(result.canonical_body)
        == args["profile"]
    )
    assert args["profile"].profile_ref == "original.runtime.profile"
    assert args["profile"].version == "9"
    assert owner.validate_grammar_profile_selection_result(result, **args) is None
    # Data copies are not source/result retention admissions.
    assert (
        owner.produce_grammar_profile_selection(
            **copy.deepcopy({k: v for k, v in args.items() if k != "catalog"}),
            catalog=args["catalog"],
        )
        == result
    )


def test_v2_direct_entrance_rechecks_full_authored_nomination(admitted_catalog):
    _, catalog, profile, _ = admitted_catalog
    value, selection, occurrences, _ = v2_supplied_input(profile)
    args = dict(
        input=value,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=occurrences,
    )
    result = owner.produce_grammar_profile_selection(**args)
    assert result == grammar_profile_selection_body(profile)
    assert owner.validate_grammar_profile_selection_result(result, **args) is None


@pytest.mark.parametrize("field", ("profile_ref", "version", "operation_kinds"))
def test_v2_direct_supplied_profile_cannot_override_original_nomination(
    admitted_catalog, field
):
    _, catalog, profile, _ = admitted_catalog
    foreign = replace(
        profile, **{field: ("foreign",) if field == "operation_kinds" else "foreign"}
    )
    value, selection, occurrences, _ = v2_supplied_input(profile)
    with pytest.raises(ContractViolation, match="nomination differs"):
        owner.produce_grammar_profile_selection(
            value,
            selection=selection,
            profile=foreign,
            catalog=catalog,
            provider_occurrences=occurrences,
        )


@pytest.mark.parametrize("field", ("profile_ref", "version", "operation_kinds"))
def test_v2_direct_entrance_cannot_bypass_foreign_authored_nomination(
    admitted_catalog, field
):
    _, catalog, profile, _ = admitted_catalog
    foreign = replace(
        profile, **{field: ("foreign",) if field == "operation_kinds" else "foreign"}
    )
    value, selection, occurrences, _ = v2_supplied_input(profile, nomination=foreign)
    with pytest.raises(ContractViolation, match="nomination differs"):
        owner.produce_grammar_profile_selection(
            value,
            selection=selection,
            profile=profile,
            catalog=catalog,
            provider_occurrences=occurrences,
        )


@pytest.mark.parametrize(
    "field", ("input", "selection", "profile", "catalog", "provider_occurrences")
)
@pytest.mark.parametrize("invalid", (None, {}, []))
def test_exact_inputs_refuse_before_parser_or_catalog(
    monkeypatch, admitted_catalog, field, invalid
):
    args = arguments(admitted_catalog)
    args[field] = invalid

    def forbidden(*a, **kw):
        raise AssertionError("invalid shape reached original owner")

    monkeypatch.setattr(owner, "parse_registered_grammar_profile", forbidden)
    with pytest.raises(TypeError):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize(
    "field", ("operation_ref", "input_digest", "root_occurrence_ref", "profile_key")
)
def test_selection_forgery_refuses_before_interpretation(
    monkeypatch, admitted_catalog, field
):
    args = arguments(admitted_catalog)
    value = ContentDigest.of_bytes(b"foreign") if field == "input_digest" else "foreign"
    args["selection"] = replace(args["selection"], **{field: value})

    def forbidden(*a, **kw):
        raise AssertionError("foreign selection reached parser")

    monkeypatch.setattr(owner, "parse_registered_grammar_profile", forbidden)
    with pytest.raises(ContractViolation):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize(
    "occurrences", ((), ("absent",), ("same", "same"), (None,), ("x",) * 257)
)
def test_provider_occurrence_inventory_is_exact(admitted_catalog, occurrences):
    args = arguments(admitted_catalog)
    args["provider_occurrences"] = occurrences
    with pytest.raises((TypeError, ContractViolation)):
        owner.produce_grammar_profile_selection(**args)


def test_equal_labels_and_bytes_cannot_supply_foreign_scope(admitted_catalog):
    args = arguments(admitted_catalog)
    _, _, occurrences, group = supplied_input()
    foreign = next(
        row.occurrence_ref
        for row in group.members
        if row.occurrence_ref != occurrences[0]
    )
    assert group.members[0].sources == group.members[1].sources
    args["provider_occurrences"] = (foreign,)
    with pytest.raises(ContractViolation, match="scope/module"):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize(
    "change",
    ("mode", "provider", "module", "package_kind", "manifest", "missing_syntax"),
)
def test_authored_changes_do_not_fall_back_to_catalog(admitted_catalog, change):
    args = arguments(admitted_catalog)
    raw = PROFILE.split(b"[[providers]]")[0].replace(
        b'key = "grammar.example"', b'key = "default"'
    )
    raw += b'[[providers]]\nmodule_id="sdk"\nprovider_key="demo"\n'
    module = (
        source()
        .replace(b'kind = "code"', b'kind = "sdk"')
        .replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    )
    if change == "mode":
        raw = raw.replace(b"registered_contracts", b"dynamic_contract_module")
    elif change == "provider":
        raw = raw.replace(b'provider_key="demo"', b'provider_key="other"')
    elif change == "module":
        raw = raw.replace(b'module_id="sdk"', b'module_id="other"')
    elif change == "package_kind":
        module = module.replace(b'kind = "sdk"', b'kind = "code"')
    elif change == "manifest":
        module = module.replace(b"package/aware.sdk.toml", b"foreign/aware.sdk.toml")
    else:
        module = module.split(b"syntax =")[0]
    value, selected, occurrences, _ = supplied_input(authored=raw, module_body=module)
    args.update(input=value, selection=selected, provider_occurrences=occurrences)
    with pytest.raises((GrammarProfileSourceError, ContractViolation)):
        owner.produce_grammar_profile_selection(**args)


def test_syntax_stage_does_not_execute_profile_interpretation(admitted_catalog):
    args = arguments(admitted_catalog)
    value, selected, occurrences, _ = supplied_input(stage="syntax_binding")
    args.update(input=value, selection=selected, provider_occurrences=occurrences)
    with pytest.raises(ContractViolation, match="role/package"):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize(
    "field", ("role", "contract", "value_ref", "digest", "size_bytes", "body")
)
def test_result_refuses_every_coordinate_or_byte_substitution(admitted_catalog, field):
    args = arguments(admitted_catalog)
    result = owner.produce_grammar_profile_selection(**args)
    coordinate = result.coordinate
    forged = copy.copy(result)
    if field == "body":
        object.__setattr__(forged, "canonical_body", result.canonical_body + b" ")
    else:
        value = {
            "role": "foreign",
            "contract": replace(coordinate.contract, version="99"),
            "value_ref": "foreign",
            "digest": ContentDigest.of_bytes(b"foreign"),
            "size_bytes": coordinate.size_bytes + 1,
        }[field]
        object.__setattr__(forged, "coordinate", replace(coordinate, **{field: value}))
    with pytest.raises((ContractViolation, ValueError)):
        owner.validate_grammar_profile_selection_result(forged, **args)


def test_self_consistent_other_profile_body_is_not_selected_result(admitted_catalog):
    args = arguments(admitted_catalog)
    forged = grammar_profile_selection_body(replace(args["profile"], version="10"))
    with pytest.raises(ContractViolation, match="selected source/catalog"):
        owner.validate_grammar_profile_selection_result(forged, **args)


@pytest.mark.parametrize("phase", ("parse", "catalog", "encode"))
@pytest.mark.parametrize(
    "failure", (RuntimeError("original"), KeyboardInterrupt(), SystemExit(7))
)
def test_original_failure_and_interruption_identity_survive(
    monkeypatch, admitted_catalog, phase, failure
):
    args = arguments(admitted_catalog)

    def fail(*a, **kw):
        raise failure

    if phase == "parse":
        monkeypatch.setattr(owner, "parse_registered_grammar_profile", fail)
    elif phase == "catalog":
        monkeypatch.setattr(type(args["catalog"]), "read_profile_binding", fail)
    else:
        monkeypatch.setattr(owner, "grammar_profile_selection_body", fail)
    with pytest.raises(type(failure)) as caught:
        owner.produce_grammar_profile_selection(**args)
    assert caught.value is failure


def test_closed_original_catalog_cannot_be_reconstructed(admitted_catalog):
    args = arguments(admitted_catalog)
    parent, _, _, _ = admitted_catalog
    parent.live = False
    with pytest.raises((RuntimeError, ContractViolation)):
        owner.produce_grammar_profile_selection(**args)
    parent.live = True
    with pytest.raises(ContractViolation):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize(
    "factory",
    (
        construct_grammar_profile_selection_product,
        construct_grammar_syntax_binding_product,
    ),
)
def test_interpretation_does_not_activate_original_factories(factory):
    product = factory()
    for call in (
        product.provider.input_closure,
        lambda value: product.provider.execute(None, value),
    ):
        with pytest.raises(ContractViolation, match="source-role attachment"):
            call(object())


@pytest.mark.parametrize("restore", (False, True))
def test_catalog_closure_during_encoding_refuses_without_retry(
    monkeypatch, admitted_catalog, restore
):
    args = arguments(admitted_catalog)
    parent, _, _, _ = admitted_catalog
    original_encode = owner.grammar_profile_selection_body
    calls = []

    def encode(profile):
        calls.append(profile)
        value = original_encode(profile)
        parent.live = False
        return value

    monkeypatch.setattr(owner, "grammar_profile_selection_body", encode)
    with pytest.raises((ContractViolation, RuntimeError)):
        owner.produce_grammar_profile_selection(**args)
    assert calls == [args["profile"]]
    if restore:
        parent.live = True
        with pytest.raises(ContractViolation):
            owner.produce_grammar_profile_selection(**args)
        assert calls == [args["profile"]]


@pytest.mark.parametrize("invalid", (None, [], {}, b"raw", bytearray(b"raw")))
def test_result_shape_cannot_invoke_foreign_reconstruction(
    monkeypatch, admitted_catalog, invalid
):
    args = arguments(admitted_catalog)

    def forbidden(*a, **kw):
        raise AssertionError("invalid result reached reconstruction")

    monkeypatch.setattr(owner, "produce_grammar_profile_selection", forbidden)
    with pytest.raises(TypeError):
        owner.validate_grammar_profile_selection_result(invalid, **args)


def test_complete_catalog_profile_substitution_is_not_a_selector_fallback(
    admitted_catalog,
):
    args = arguments(admitted_catalog)
    args["profile"] = replace(args["profile"], version="10")
    with pytest.raises(ContractViolation, match="exact planning catalog"):
        owner.produce_grammar_profile_selection(**args)


@pytest.mark.parametrize("version", (1, 2, 3))
def test_original_module_versions_keep_the_same_interpretation_boundary(
    admitted_catalog, version
):
    args = arguments(admitted_catalog)
    module = (
        source(version=version)
        .replace(b'kind = "code"', b'kind = "sdk"')
        .replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    )
    value, selected, occurrences, _ = supplied_input(module_body=module)
    args.update(input=value, selection=selected, provider_occurrences=occurrences)
    assert owner.produce_grammar_profile_selection(
        **args
    ) == grammar_profile_selection_body(args["profile"])
