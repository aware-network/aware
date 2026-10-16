"""Deterministic original Code data resolution, not source/admission authority."""

import copy
from dataclasses import fields, replace
from pathlib import PurePosixPath

import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as interpretation,
)
from aware_code_module_manifest_contract_runtime import grammar_source_operands as owner
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
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    GRAMMAR_PROFILE_RESULT_REF,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    grammar_profile_selection_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    CodeGrammarSourceGroupV1,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerDeclaration,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
    SemanticInputSourceContract,
    execute_registered_semantic_input,
    register_semantic_input_producer,
    release_registered_semantic_input_result,
    validate_registered_semantic_input_result,
)
from test_catalog_host_leg import Owner as ParentFixture
from test_grammar_declaration_context import input_value
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_profile_composition import supplied_input, v2_supplied_input
from test_grammar_profile_source import v2_authored
from test_materialization_catalog import _catalog, _execution_closure
from test_retained_declaration_scope import body


def args(fixture, **changes):
    value, selection, occurrences, _ = supplied_input()
    _, resolver, profile, _ = fixture
    result = dict(input=value, profile_key=selection.profile_key, catalog=resolver)
    result.update(changes)
    return result, selection, profile, occurrences


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_v2_exact_registration_selects_original_complete_catalog_product(
    admitted_catalog, stage
):
    _, catalog, profile, _ = admitted_catalog
    value, selected, occurrences, _ = v2_supplied_input(profile, stage=stage)
    result = owner.derive_grammar_source_operands(
        value, profile_key="default", catalog=catalog
    )
    assert result.selection == selected and result.profile == profile
    assert result.provider_occurrences == occurrences


@pytest.mark.parametrize("field", ("profile_ref", "version", "operation_kinds"))
def test_v2_catalog_key_cannot_override_authored_full_product_identity(
    admitted_catalog, field
):
    _, catalog, profile, _ = admitted_catalog
    foreign = replace(
        profile, **{field: ("foreign",) if field == "operation_kinds" else "foreign"}
    )
    value, _, _, _ = v2_supplied_input(profile, nomination=foreign)
    with pytest.raises(ContractViolation, match="absent or ambiguous"):
        owner.derive_grammar_source_operands(
            value, profile_key="default", catalog=catalog
        )


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_v2_missing_authored_package_preserves_frozen_diagnostic(
    admitted_catalog, stage
):
    _, catalog, profile, _ = admitted_catalog
    module, raw = v2_authored(profile)
    raw = raw.replace(b'package_id="provider"', b'package_id="foreign"')
    module = module.replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    value, _, _, _ = supplied_input(
        authored=raw, stage=stage, module_body=module, package_kind="code"
    )
    with pytest.raises(GrammarProfileSourceError) as caught:
        owner.derive_grammar_source_operands(
            value, profile_key="default", catalog=catalog
        )
    assert type(caught.value) is GrammarProfileSourceError
    assert caught.value.reason == "syntax_provider_declaration_mismatch"


def test_v1_missing_provider_package_preserves_original_generic_refusal(
    admitted_catalog,
):
    value, selection, _, _ = supplied_input()
    _, closure = read_grammar_declaration_context(value)
    raw = closure.local_profiles[0].manifest.body.replace(
        b'provider_key="demo"', b'provider_key="foreign"'
    )
    changed, _, _, _ = supplied_input(authored=raw)
    with pytest.raises(ContractViolation) as caught:
        owner.derive_grammar_source_operands(
            changed, profile_key=selection.profile_key, catalog=admitted_catalog[1]
        )
    assert type(caught.value) is ContractViolation
    assert (
        str(caught.value) == "authored grammar provider package is absent or ambiguous"
    )
    assert not hasattr(caught.value, "reason")


def operand_input(group, closure, *, stage="profile_selection"):
    value = input_value(group, closure)
    expected = SemanticInputProductionExpectation.create(
        use_ref=value.use_ref,
        operation_ref=value.operation_ref,
        stage=stage,
        package_identity=value.package_identity,
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in value.sources),
        context_bodies=value.context_bodies,
    )
    return SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        value.sources,
        expected.input_digest,
        expected.context_bodies,
    )


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_complete_profile_selection_and_occurrences_from_original_data(
    admitted_catalog, stage
):
    value, selection, occurrences, _ = supplied_input(stage=stage)
    _, resolver, profile, _ = admitted_catalog
    result = owner.derive_grammar_source_operands(
        value, profile_key="default", catalog=resolver
    )
    assert result.selection == selection
    assert result.profile == profile
    assert result.provider_occurrences == occurrences
    assert result.profile.profile_ref == "original.runtime.profile"
    assert result.profile.version == "9"
    if stage == "profile_selection":
        produced = interpretation.produce_grammar_profile_selection(
            value,
            selection=result.selection,
            profile=result.profile,
            catalog=resolver,
            provider_occurrences=result.provider_occurrences,
        )
        assert produced == grammar_profile_selection_body(profile)


@pytest.mark.parametrize("field", ("input", "catalog"))
@pytest.mark.parametrize("bad", (None, {}, (), object()))
def test_exact_shapes_refuse_before_parsers_and_catalog(
    admitted_catalog, monkeypatch, field, bad
):
    values, _, _, _ = args(admitted_catalog, **{field: bad})

    def forbidden(*a, **kw):
        raise AssertionError("foreign shape reached source interpretation")

    monkeypatch.setattr(owner, "read_grammar_declaration_context", forbidden)
    with pytest.raises(TypeError):
        owner.derive_grammar_source_operands(**values)


@pytest.mark.parametrize(
    "key", (None, "", "wrong", "separate.interpretation", "default alias", "x" * 513)
)
def test_explicit_key_has_no_alias_or_default_fallback(admitted_catalog, key):
    values, _, _, _ = args(admitted_catalog, profile_key=key)
    with pytest.raises((TypeError, ContractViolation, ValueError)):
        owner.derive_grammar_source_operands(**values)


def test_data_copy_does_not_create_original_admission(admitted_catalog):
    values, _, _, _ = args(admitted_catalog)
    before = owner.derive_grammar_source_operands(**values)
    after = owner.derive_grammar_source_operands(
        copy.deepcopy(values["input"]),
        profile_key=values["profile_key"],
        catalog=values["catalog"],
    )
    assert before == after
    assert not hasattr(before, "registration")
    assert not hasattr(before, "source_identity")


@pytest.mark.parametrize("mode", ("consumer_and_import", "unassociated"))
def test_equal_profile_labels_do_not_select_a_scope(admitted_catalog, mode):
    values, _, _, _ = args(admitted_catalog)
    group, closure = read_grammar_declaration_context(values["input"])
    original = closure.local_profiles[0]
    if mode == "consumer_and_import":
        root_scope = next(
            row for row in closure.scopes if row.scope_key == closure.consumer_scope_key
        )
        path = str(
            PurePosixPath(root_scope.projection.workspace_manifest.relative_path).parent
            / "semantic_contract/profiles/default/aware.semantic_contract_profile.toml"
        )
        extra = replace(
            original,
            owning_scope_key=closure.consumer_scope_key,
            manifest=body(path, original.manifest.body),
        )
        closure = replace(
            closure,
            local_profiles=tuple(
                sorted(
                    (*closure.local_profiles, extra),
                    key=lambda row: (
                        row.owning_scope_key.encode(),
                        row.profile_key.encode(),
                    ),
                )
            ),
        )
    else:
        # Remove entitlement by changing the selector publication rather than
        # flattening qualified source occurrences or fabricating an edge.
        values["profile_key"] = "missing.local.publication"
    values["input"] = operand_input(group, closure)
    with pytest.raises(ContractViolation, match="scope"):
        owner.derive_grammar_source_operands(**values)


def test_missing_qualified_provider_cannot_borrow_equal_bytes(admitted_catalog):
    values, _, _, _ = args(admitted_catalog)
    group, closure = read_grammar_declaration_context(values["input"])
    # Preserve the root but omit the imported provider. No equal-labelled root
    # or matching manifest body supplies the missing qualified occurrence.
    root = next(
        row for row in group.members if row.occurrence_ref == group.root_occurrence_ref
    )
    changed = CodeGrammarSourceGroupV1(group.root_occurrence_ref, (root,), ())
    values["input"] = operand_input(changed, closure)
    with pytest.raises(ContractViolation, match="occurrence"):
        owner.derive_grammar_source_operands(**values)


def test_two_equal_byte_qualified_provider_occurrences_refuse(admitted_catalog):
    values, _, _, _ = args(admitted_catalog)
    group, _ = read_grammar_declaration_context(values["input"])
    # The original closed group rejects a second member for the same complete
    # occurrence. It cannot become a second selectable provider by relabelling.
    with pytest.raises(ContractViolation):
        CodeGrammarSourceGroupV1(
            group.root_occurrence_ref, (group.members[0], group.members[0]), ()
        )


def test_multiple_full_catalog_profiles_refuse_without_priority_selection(
    admitted_catalog,
):
    values, _, _, _ = args(admitted_catalog)
    _, _, _, binding = admitted_catalog
    other = replace(binding.profile_declaration, profile_ref="another.complete.profile")
    changed = dict(
        (field.name, getattr(binding, field.name))
        for field in fields(binding)
        if field.name != "binding_digest"
    )
    changed["profile_declaration"] = other
    alternative = type(binding).create(**changed)
    catalog = _catalog(binding, alternative)
    executables, planners = _execution_closure(catalog)
    parent = ParentFixture()
    leg = prepare_code_catalog_leg(
        joint_host=parent,
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
    )
    parent.published = (
        True  # Explicit catalog-parent fixture, not production authority.
    )
    _, resolver = published_code_catalog_leg(leg)
    try:
        values["catalog"] = resolver
        with pytest.raises(ContractViolation, match="profile.*ambiguous"):
            owner.derive_grammar_source_operands(**values)
    finally:
        revoke_code_catalog_leg(leg)


@pytest.mark.parametrize(
    "mode", ("distinct_profile", "duplicate_product", "unselected_corruption")
)
def test_v2_exact_product_selection_keeps_full_original_catalog(admitted_catalog, mode):
    _, _, profile, binding = admitted_catalog
    changed = {
        field.name: getattr(binding, field.name)
        for field in fields(binding)
        if field.name != "binding_digest"
    }
    if mode == "duplicate_product":
        changed["semantic_owner_key"] = "foreign_owner"
    else:
        changed["profile_declaration"] = replace(
            profile, profile_ref="another.complete.profile"
        )
    alternative = type(binding).create(**changed)
    catalog = _catalog(binding, alternative)
    executables, planners = _execution_closure(catalog)
    parent = ParentFixture()
    leg = prepare_code_catalog_leg(
        joint_host=parent,
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
    )
    parent.published = True  # Explicit parent fixture, not genuine host authority.
    _, resolver = published_code_catalog_leg(leg)
    value, _, _, _ = v2_supplied_input(profile)
    retained_alternative = next(
        row
        for row in resolver._catalog.entries
        if row.profile_declaration == alternative.profile_declaration
        and row.semantic_owner_key == alternative.semantic_owner_key
    )
    original_digest = retained_alternative.binding_digest
    try:
        if mode == "distinct_profile":
            result = owner.derive_grammar_source_operands(
                value, profile_key="default", catalog=resolver
            )
            assert result.profile == profile and len(resolver.catalog.entries) == 2
        else:
            if mode == "unselected_corruption":
                # The original full resolver must detect corruption even outside the selected product.
                object.__setattr__(
                    retained_alternative,
                    "binding_digest",
                    ContentDigest.of_bytes(b"foreign"),
                )
            with pytest.raises(ContractViolation):
                owner.derive_grammar_source_operands(
                    value, profile_key="default", catalog=resolver
                )
    finally:
        object.__setattr__(retained_alternative, "binding_digest", original_digest)
        revoke_code_catalog_leg(leg)


@pytest.mark.parametrize("mode", ("missing", "duplicate", "unsupported"))
def test_authored_providers_are_not_filtered_to_create_a_match(admitted_catalog, mode):
    value, selected, _, _ = supplied_input()
    _, closure = read_grammar_declaration_context(value)
    raw = closure.local_profiles[0].manifest.body
    if mode == "missing":
        raw = raw.replace(b'provider_key="demo"', b'provider_key="missing"')
    elif mode == "duplicate":
        raw += b'[[providers]]\nmodule_id="sdk"\nprovider_key="demo"\n'
    else:
        raw = raw.replace(b'"registered_contracts"', b'"dynamic_contract_module"')
    value, _, _, _ = supplied_input(authored=raw)
    with pytest.raises((ContractViolation, ValueError)):
        owner.derive_grammar_source_operands(
            value, profile_key=selected.profile_key, catalog=admitted_catalog[1]
        )


def test_original_catalog_retirement_is_not_bypassed(admitted_catalog):
    values, _, _, _ = args(admitted_catalog)
    parent = admitted_catalog[0]
    parent.published = False
    with pytest.raises(ContractViolation):
        owner.derive_grammar_source_operands(**values)


@pytest.mark.parametrize(
    "error", (ValueError("parser failure"), KeyboardInterrupt(), SystemExit(5))
)
def test_original_parser_error_identity_is_not_reconstructed(
    admitted_catalog, monkeypatch, error
):
    values, _, _, _ = args(admitted_catalog)

    def fail(*a, **kw):
        raise error

    monkeypatch.setattr(owner, "parse_registered_grammar_profile", fail)
    with pytest.raises(type(error)) as caught:
        owner.derive_grammar_source_operands(**values)
    assert caught.value is error


@pytest.mark.parametrize(
    "stage", ("source_planning", "fixture:receiving", "authority_derivation")
)
def test_other_stages_refuse_before_catalog_use(admitted_catalog, stage, monkeypatch):
    value, _, _, _ = supplied_input()
    group, closure = read_grammar_declaration_context(value)
    value = operand_input(group, closure, stage=stage)

    def forbidden(*a, **kw):
        raise AssertionError("foreign stage reached original profile interpretation")

    monkeypatch.setattr(owner, "_produce_profile_selection", forbidden)
    with pytest.raises(ContractViolation, match="role/package"):
        owner.derive_grammar_source_operands(
            value, profile_key="default", catalog=admitted_catalog[1]
        )


@pytest.mark.parametrize("key", ("é" * 257, "\ud800", "default\n", "default\t"))
def test_utf8_and_whitespace_bounds_precede_source_calls(
    admitted_catalog, key, monkeypatch
):
    values, _, _, _ = args(admitted_catalog, profile_key=key)

    def forbidden(*a, **kw):
        raise AssertionError("invalid key reached original source parsing")

    monkeypatch.setattr(owner, "read_grammar_declaration_context", forbidden)
    with pytest.raises(ValueError):
        owner.derive_grammar_source_operands(**values)


def test_late_catalog_retirement_is_rechecked(admitted_catalog, monkeypatch):
    values, _, _, _ = args(admitted_catalog)
    original = owner.parse_grammar_provider_module

    def retire(*a, **kw):
        result = original(*a, **kw)
        admitted_catalog[0].published = False
        return result

    monkeypatch.setattr(owner, "parse_grammar_provider_module", retire)
    with pytest.raises(ContractViolation):
        owner.derive_grammar_source_operands(**values)


def test_operand_derivation_does_not_invoke_factories(admitted_catalog, monkeypatch):
    from aware_code_module_manifest_contract_runtime import grammar_factory

    def forbidden(*a, **kw):
        raise AssertionError("data resolution attempted product construction")

    monkeypatch.setattr(
        grammar_factory, "construct_grammar_profile_selection_product", forbidden
    )
    monkeypatch.setattr(
        grammar_factory, "construct_grammar_syntax_binding_product", forbidden
    )
    values, _, _, _ = args(admitted_catalog)
    assert owner.derive_grammar_source_operands(**values).profile == admitted_catalog[2]


@pytest.mark.asyncio
async def test_original_registered_executor_retains_exact_operand_result(
    admitted_catalog,
):
    """Real Code registration/retention, explicitly fixture source and producer.

    This does not admit the production Policy constructor or a factory-owned
    grammar producer. It proves this helper can feed the unchanged owner ports.
    """
    value, _, _, _ = supplied_input()

    class SourceFixture:
        expected = None

        def validate_semantic_input_source(self, admission, *, expected):
            if admission is not self or expected is not self.expected:
                raise ContractViolation("original fixture source differs")

        def validate_semantic_input_context(self, admission, *, expected):
            self.validate_semantic_input_source(admission, expected=expected)

        def read_semantic_input_sources(self, admission, *, expected):
            self.validate_semantic_input_source(admission, expected=expected)
            return value.sources

    source = SourceFixture()
    expected = SemanticInputProductionExpectation.create(
        use_ref=value.use_ref,
        operation_ref=value.operation_ref,
        stage=value.stage,
        package_identity=value.package_identity,
        operation_identity=object(),
        source_identity=source,
        source_coordinates=tuple(row.source for row in value.sources),
        context_bodies=value.context_bodies,
    )
    source.expected = expected

    async def produce(original_input):
        derived = owner.derive_grammar_source_operands(
            original_input,
            profile_key="default",
            catalog=admitted_catalog[1],
        )
        return grammar_profile_selection_body(derived.profile)

    digest = ContentDigest.of_bytes(b"explicit fixture reader, not production factory")
    declaration = SemanticInputProducerDeclaration(
        "fixture.grammar.operands",
        "fixture.grammar.operands.v1",
        SemanticImplementationCoordinate("fixture.grammar.operands", digest),
        SemanticConfigurationCoordinate("fixture.grammar.operands", digest),
        tuple(
            sorted(
                {
                    SemanticInputSourceContract(
                        row.source.coordinate.role, row.source.coordinate.contract
                    )
                    for row in value.sources
                },
                key=lambda row: row.role.encode(),
            )
        ),
        "code.profile_selection",
        GRAMMAR_PROFILE_RESULT_REF,
        context_contracts=tuple(
            SemanticInputContextContract(row.coordinate.role, row.coordinate.contract)
            for row in value.context_bodies
        ),
    )
    host = SemanticInputProducerHost()
    registration = register_semantic_input_producer(
        host,
        declaration=declaration,
        producer=produce,
        validator=source,
        validator_entrance=source.validate_semantic_input_source,
        context_validator_entrance=source.validate_semantic_input_context,
        reader=source,
        reader_entrance=source.read_semantic_input_sources,
        retain_result=True,
    )
    try:
        result = await execute_registered_semantic_input(
            host,
            registration,
            source_admission=source,
            expected=expected,
        )
        validate_registered_semantic_input_result(
            host,
            registration,
            source_admission=source,
            expected=expected,
            result=result,
        )
        with pytest.raises(ContractViolation):
            validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=source,
                expected=expected,
                result=copy.deepcopy(result),
            )
        release_registered_semantic_input_result(
            host,
            registration,
            source_admission=source,
            expected=expected,
            result=result,
        )
        with pytest.raises(ContractViolation):
            validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=source,
                expected=expected,
                result=result,
            )
    finally:
        host.close()
