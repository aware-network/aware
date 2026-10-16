"""Grouped contribution data is not original Workspace source/edge authority."""

import copy
from dataclasses import fields, replace

import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as owner,
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
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    CodeGrammarSourceEdgeV1,
    CodeGrammarSourceGroupV1,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
)
from aware_code_semantic_contract_runtime.source_origin import (
    SemanticInputPackageOccurrence,
    SemanticInputSourceOrigin,
    decode_source_origin,
    encode_source_origin,
    source_occurrence_ref,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SemanticSourceSelection,
    source_selection_body,
)
from aware_language_parsed_document_contract import (
    SyntaxAssemblyContractError,
    SyntaxContractRefV1,
    SyntaxContributionSourceV1,
    SyntaxDependencyV1,
    SyntaxExpressionV1,
    SyntaxRuleV1,
    SyntaxSourceBindingV1,
    encode_syntax_assembly_value,
)
from aware_language_syntax_assembly import reconstruct_syntax_contribution
from test_catalog_host_leg import Owner as CatalogParentFixture
from test_grammar_declaration_context import input_value
from test_grammar_syntax_composition import member_sources, syntax_inputs
from test_materialization_catalog import _binding, _catalog, _execution_closure
from test_retained_declaration_scope import body
from test_syntax_declaration import source, table


@pytest.fixture
def group_catalog():
    first, second = (_binding(provider_key=key) for key in ("demo", "peer"))
    other = second.profile_declaration.providers[0]
    other = replace(
        other,
        result_role=replace(other.result_role, role="peer_result"),
        effect_role=replace(other.effect_role, role="peer_effect"),
        output_roles=tuple(
            replace(row, role="peer_" + row.role) for row in other.output_roles
        ),
    )
    profile = replace(
        first.profile_declaration,
        profile_ref="original.grouped.profile",
        version="9",
        providers=(first.profile_declaration.providers[0], other),
        steps=(
            first.profile_declaration.steps[0],
            replace(second.profile_declaration.steps[0], step_key="render_peer"),
        ),
    )
    bindings = tuple(
        CodeSemanticMaterializationProfileBinding.create(
            **{
                field.name: profile
                if field.name == "profile_declaration"
                else (
                    *first.provider_execution_bindings,
                    *second.provider_execution_bindings,
                )
                if field.name == "provider_execution_bindings"
                else getattr(original, field.name)
                for field in fields(original)
                if field.name != "binding_digest"
            }
        )
        for original in (first, second)
    )
    catalog = _catalog(*bindings)
    executables, planners = _execution_closure(catalog)
    parent = CatalogParentFixture()
    leg = prepare_code_catalog_leg(
        joint_host=parent,
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
    )
    parent.published = True  # Explicit fixture parent, never installed provenance.
    _, resolver = published_code_catalog_leg(leg)
    try:
        yield parent, resolver, profile, bindings
    finally:
        revoke_code_catalog_leg(leg)


def grouped_args(
    catalog,
    *,
    edge=True,
    reverse_edge=False,
    wrong_digest=False,
    wrong_version=False,
    duplicate_label=False,
    dependency=True,
):
    """Closed portable fixtures; the registered source owner admits their use."""
    args = syntax_inputs(catalog)
    _, resolver, profile, _ = catalog
    joined = args["input"]
    group, closure = read_grammar_declaration_context(joined.ordinary)
    first_ref = args["provider_occurrences"][0]
    member = next(row for row in group.members if row.occurrence_ref == first_ref)
    old = decode_source_origin(bytes.fromhex(member.origin_body_hex))
    scope = next(
        row for row in closure.scopes if row.scope_key == old.occurrence.scope_key
    )
    original_module = scope.projection.modules[0]
    declaration = table()
    declaration["contributions"] = ["syntax/peer.syntax.json"]
    consumer = profile.providers[1].consumed_roles[0]
    accepted = consumer.accepted_contracts[0]
    declaration["anchors"] = [
        {
            "consumer_contract": {
                "key": accepted.key,
                "version": accepted.version,
                "schema_digest": accepted.schema_digest.value,
            },
            "role": consumer.role,
            "rule_name": "peer",
            "field_path": ["value"],
            "required": True,
            "top_level": True,
        }
    ]
    peer_decl = source(declaration).replace(
        b'provider_key = "demo"', b'provider_key = "peer"'
    )
    peer_decl = (
        peer_decl.replace(b'id = "provider"', b'id = "peer"')
        .replace(b'kind = "code"', b'kind = "sdk"')
        .replace(b"provider/pyproject.toml", b"peer/aware.sdk.toml")
    )
    module = replace(
        original_module,
        manifest=replace(
            body(
                original_module.manifest.relative_path,
                original_module.manifest.body.replace(
                    b"[[packages]]",
                    b'[[plugins]]\nkind="code.module_plugin"\nprovider_key="peer"\n[[packages]]',
                    1,
                )
                + b"\n[[packages]]"
                + peer_decl.split(b"[[packages]]", 1)[1],
            ),
            body_ref="fixture:module:" + scope.scope_key,
        ),
    )
    first_package = scope.projection.packages[0]
    peer_package = replace(
        first_package,
        package_id="peer",
        package_root="mods/sdk/peer",
        manifest=body("mods/sdk/peer/aware.sdk.toml", b"peer manifest"),
    )
    scope = replace(
        scope,
        projection=replace(
            scope.projection,
            modules=(module,),
            packages=tuple(
                sorted(
                    (first_package, peer_package),
                    key=lambda row: (row.module_id.encode(), row.package_id.encode()),
                )
            ),
        ),
    )
    publication = closure.local_profiles[0]
    raw_profile = (
        publication.manifest.body
        + b'[[providers]]\nmodule_id="sdk"\nprovider_key="peer"\n'
    )
    manifest = body(publication.manifest.relative_path, raw_profile)
    closure = replace(
        closure,
        scopes=tuple(
            scope if row.scope_key == scope.scope_key else row for row in closure.scopes
        ),
        local_profiles=(replace(publication, manifest=manifest),),
        profile_associations=(
            replace(closure.profile_associations[0], manifest=manifest),
        ),
    )
    occurrence = SemanticInputPackageOccurrence(
        old.occurrence.repository_binding_ref,
        old.occurrence.scope_key,
        old.occurrence.module_id,
        "peer",
        peer_package.package_root,
        peer_package.manifest_relative_path,
    )
    outer = replace(
        old.outer_manifest,
        coordinate=replace(
            old.outer_manifest.coordinate,
            value_ref=peer_package.manifest.body_ref,
            digest=peer_package.manifest.content_digest,
            size_bytes=len(peer_package.manifest.body),
        ),
    )
    prototype = SemanticInputSourceOrigin(
        SemanticPackageCoordinate(
            old.package.package_ref, "sdk", peer_package.manifest.content_digest
        ),
        old.source_identity_digest,
        old.selection_coordinate,
        old.selection_input_digest,
        occurrence,
        old.outer_package_root + "-peer",
        outer,
        (),
    )
    empty_selection = source_selection_body(
        SemanticSourceSelection(
            prototype.package,
            prototype.source_identity_digest,
            prototype.selection_input_digest,
            (),
            (),
        ),
        role="selection",
    )
    prototype = replace(prototype, selection_coordinate=empty_selection.coordinate)
    origin_raw = encode_source_origin(prototype)
    prototype_member = replace(
        member,
        occurrence_ref=occurrence.occurrence_ref,
        selection_coordinate=empty_selection.coordinate,
        selection_body_hex=empty_selection.canonical_body.hex(),
        sources=(),
        origin_coordinate=replace(
            member.origin_coordinate,
            digest=ContentDigest.of_bytes(origin_raw),
            size_bytes=len(origin_raw),
        ),
        origin_body_hex=origin_raw.hex(),
    )
    ref = profile.providers[1].provider_contract
    owner_ref = SyntaxContractRefV1(ref.key, ref.version, ref.schema_digest.value)
    peer = SyntaxContributionSourceV1(
        "sample-0" if duplicate_label else "peer",
        "1",
        owner_ref,
        (),
        (SyntaxRuleV1("peer", SyntaxExpressionV1("STRING", value="peer")),),
        ("peer",),
        ("peer",),
        (),
        (),
        None,
    )
    peer_raw = encode_syntax_assembly_value(peer)
    peer_source = SyntaxSourceBindingV1(
        occurrence.occurrence_ref,
        source_occurrence_ref(occurrence, "syntax/peer.syntax.json"),
        prototype.package.package_ref,
        "syntax/peer.syntax.json",
        len(peer_raw),
        ContentDigest.of_bytes(peer_raw).value,
    )
    target = reconstruct_syntax_contribution(
        authored_source=peer_source,
        owner_contract=owner_ref,
        source_bodies=((peer_source, peer_raw),),
    )
    dependency_value = SyntaxDependencyV1(
        target.contribution_ref,
        "2" if wrong_version else target.version,
        ContentDigest.of_bytes(b"foreign").value if wrong_digest else target.digest,
    )
    ref = profile.providers[0].provider_contract
    first_payload = SyntaxContributionSourceV1(
        "sample-0",
        "1",
        SyntaxContractRefV1(ref.key, ref.version, ref.schema_digest.value),
        (dependency_value,) if dependency else (),
        (SyntaxRuleV1("sample", SyntaxExpressionV1("STRING", value="sample")),),
        ("sample",),
        ("sample",),
        (),
        (),
        None,
    )
    first_member = member_sources(
        member, {"syntax/0.syntax.json": encode_syntax_assembly_value(first_payload)}
    )
    peer_member = member_sources(
        prototype_member, {"syntax/peer.syntax.json": peer_raw}
    )
    edges = [
        *group.dependency_edges,
        CodeGrammarSourceEdgeV1(
            group.root_occurrence_ref, occurrence.occurrence_ref, "fixture", "peer-root"
        ),
    ]
    if edge:
        edges.append(
            CodeGrammarSourceEdgeV1(
                occurrence.occurrence_ref if reverse_edge else first_ref,
                first_ref if reverse_edge else occurrence.occurrence_ref,
                "fixture",
                "peer-target",
            )
        )
    group = CodeGrammarSourceGroupV1(
        group.root_occurrence_ref,
        tuple(
            sorted(
                (
                    *(
                        first_member if row.occurrence_ref == first_ref else row
                        for row in group.members
                    ),
                    peer_member,
                ),
                key=lambda row: row.occurrence_ref.encode(),
            )
        ),
        tuple(
            sorted(
                edges,
                key=lambda row: (
                    row.owner_occurrence_ref.encode(),
                    row.target_occurrence_ref.encode(),
                    row.dependency_kind.encode(),
                    row.dependency_ref.encode(),
                ),
            )
        ),
    )
    value = input_value(group, closure)
    expected = SemanticInputProductionExpectation.create(
        use_ref=value.use_ref,
        operation_ref=value.operation_ref,
        stage="syntax_binding",
        package_identity=value.package_identity,
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in value.sources),
        context_bodies=value.context_bodies,
    )
    ordinary = SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        value.sources,
        expected.input_digest,
        value.context_bodies,
    )
    joined = replace(joined, ordinary=ordinary, operation_ref=ordinary.operation_ref)
    return dict(
        input=joined,
        selection=replace(
            args["selection"],
            input_digest=ordinary.input_digest,
            profile_source=replace(
                args["selection"].profile_source,
                body_ref=manifest.body_ref,
                content_digest=manifest.content_digest,
                size_bytes=len(manifest.body),
            ),
        ),
        catalog=resolver,
        provider_occurrences=(first_ref, occurrence.occurrence_ref),
    )


def test_complete_selected_group_retains_two_occurrences(group_catalog):
    args = grouped_args(group_catalog)
    result = owner.reconstruct_grammar_group_dependency_binding(**args)
    value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    assert len(value.provider_bindings) == len(value.contribution_bindings) == 2
    assert {row.occurrence_ref for row in value.contribution_bindings} == set(
        args["provider_occurrences"]
    )
    assert value.interpretation_profile == args["input"].predecessors[0].coordinate


@pytest.mark.parametrize(
    "options",
    (
        {"edge": False},
        {"reverse_edge": True},
        {"wrong_digest": True},
        {"wrong_version": True},
        {"duplicate_label": True},
    ),
)
def test_incomplete_or_ambiguous_selected_group_refuses(group_catalog, options):
    args = grouped_args(group_catalog, **options)
    with pytest.raises((ContractViolation, SyntaxAssemblyContractError)):
        owner.reconstruct_grammar_group_dependency_binding(**args)


def test_local_and_dependency_free_entrances_keep_refusal(group_catalog):
    args = grouped_args(group_catalog)
    with pytest.raises(ContractViolation, match="target admission required"):
        owner.reconstruct_grammar_local_dependency_binding(**args)
    with pytest.raises(ContractViolation, match="dependency admission required"):
        owner.reconstruct_grammar_source_binding(**args)


def test_portable_copy_is_only_data_and_no_capability(group_catalog):
    args = grouped_args(group_catalog)
    detached = copy.deepcopy({k: v for k, v in args.items() if k != "catalog"})
    assert owner.reconstruct_grammar_group_dependency_binding(
        **args
    ) == owner.reconstruct_grammar_group_dependency_binding(
        **detached, catalog=args["catalog"]
    )


def test_dependency_free_group_preserves_original_bytes(group_catalog):
    args = grouped_args(group_catalog, dependency=False)
    assert owner.reconstruct_grammar_group_dependency_binding(
        **args
    ) == owner.reconstruct_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "field", ("input", "selection", "catalog", "provider_occurrences")
)
def test_exact_public_shapes_refuse_before_language(group_catalog, monkeypatch, field):
    import aware_language_syntax_assembly as language

    args = grouped_args(group_catalog)
    args[field] = None
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("invalid shape reached Language")

    monkeypatch.setattr(language, "reconstruct_syntax_contribution", forbidden)
    with pytest.raises(TypeError):
        owner.reconstruct_grammar_group_dependency_binding(**args)
    assert calls == []


def test_explicit_provider_occurrence_order_is_not_repaired(group_catalog):
    args = grouped_args(group_catalog)
    args["provider_occurrences"] = tuple(reversed(args["provider_occurrences"]))
    with pytest.raises(GrammarProfileSourceError, match="selected package differs"):
        owner.reconstruct_grammar_group_dependency_binding(**args)


def test_original_shared_budget_refuses_before_language(group_catalog, monkeypatch):
    args = grouped_args(group_catalog)
    monkeypatch.setattr(owner, "MAX_GRAMMAR_BODY_BYTES", 1)
    with pytest.raises(ContractViolation, match="aggregate byte budget"):
        owner.reconstruct_grammar_group_dependency_binding(**args)
