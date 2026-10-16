"""Real Code/Language data correspondence; source/catalog parents are fixtures."""

from __future__ import annotations

import copy
from dataclasses import replace

import aware_language_syntax_assembly as language_owner
import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as entry,
)
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as owner,
)
from aware_code_module_manifest_contract_runtime import (
    grammar_syntax_composition as shim,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
    grammar_profile_selection_body,
    grammar_syntax_binding_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    CodeGrammarSourceBodyV1,
    CodeGrammarSourceGroupV1,
    CodeGrammarSourceMemberV1,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputJoinedProductionInput,
    SemanticInputPackageIdentity,
    SemanticInputPredecessorBody,
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
    SemanticInputSourceCoordinate,
)
from aware_code_semantic_contract_runtime.source_origin import (
    SOURCE_ORIGIN_REF,
    SemanticInputSourceOccurrence,
    SemanticInputSourceOrigin,
    decode_source_origin,
    encode_source_origin,
    source_occurrence_ref,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SemanticSelectedSource,
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
    SyntaxScannerV1,
    SyntaxSourceBindingV1,
    decode_syntax_assembly_value,
    encode_syntax_assembly_value,
)
from aware_language_syntax_assembly import reconstruct_syntax_contribution
from test_grammar_declaration_context import RAW, input_value
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_profile_composition import supplied_input, v2_supplied_input
from test_syntax_declaration import source, table


def member_sources(member, bodies):
    previous = decode_source_origin(bytes.fromhex(member.origin_body_hex))
    coordinates = tuple(
        SemanticInputSourceCoordinate(
            path,
            SemanticValueCoordinate(
                "selected_raw",
                RAW,
                "fixture:source:" + path,
                ContentDigest.of_bytes(raw),
                len(raw),
            ),
        )
        for path, raw in sorted(bodies.items())
    )
    selected = source_selection_body(
        SemanticSourceSelection(
            previous.package,
            previous.source_identity_digest,
            ContentDigest.of_bytes(b"portable selected inventory"),
            (),
            tuple(
                SemanticSelectedSource(
                    "selected_raw", RAW, row.relative_path, row.coordinate.digest
                )
                for row in coordinates
            ),
        ),
        role="selection",
    )
    origin = SemanticInputSourceOrigin(
        previous.package,
        previous.source_identity_digest,
        selected.coordinate,
        ContentDigest.of_bytes(b"portable selected inventory"),
        previous.occurrence,
        previous.outer_package_root,
        previous.outer_manifest,
        tuple(
            SemanticInputSourceOccurrence(
                row, source_occurrence_ref(previous.occurrence, row.relative_path)
            )
            for row in coordinates
        ),
    )
    raw_origin = encode_source_origin(origin)
    coordinate = SemanticValueCoordinate(
        "source_origin",
        SOURCE_ORIGIN_REF,
        "fixture:origin:" + origin.occurrence.occurrence_ref,
        ContentDigest.of_bytes(raw_origin),
        len(raw_origin),
    )
    return CodeGrammarSourceMemberV1(
        member.occurrence_ref,
        selected.coordinate,
        selected.canonical_body.hex(),
        coordinate,
        raw_origin.hex(),
        tuple(
            CodeGrammarSourceBodyV1(
                row.relative_path, row.coordinate, bodies[row.relative_path].hex()
            )
            for row in coordinates
        ),
    )


def syntax_inputs(
    admitted_catalog,
    *,
    count=1,
    missing_dependency=False,
    duplicate_label=False,
    scanner=False,
    anchor_mismatch=False,
    dependency=False,
    bad_dependency_digest=False,
    v2=False,
    nomination=None,
):
    _, catalog, profile, _ = admitted_catalog
    provider = profile.providers[0]
    consumer = provider.consumed_roles[0]
    expected = consumer.accepted_contracts[0]
    syntax = table()
    paths = tuple(f"syntax/{i}.syntax.json" for i in range(count))
    syntax["contributions"] = list(paths)
    syntax["anchors"] = [
        {
            "consumer_contract": {
                "key": expected.key,
                "version": expected.version,
                "schema_digest": expected.schema_digest.value,
            },
            "role": consumer.role,
            "rule_name": "sample",
            "field_path": ["value"],
            "required": True,
            "top_level": True,
        }
    ]
    if anchor_mismatch:
        syntax["anchors"][0]["consumer_contract"]["schema_digest"] = (
            ContentDigest.of_bytes(b"foreign").value
        )
    module = (
        source(syntax)
        .replace(b'kind = "code"', b'kind = "sdk"')
        .replace(b"provider/pyproject.toml", b"package/aware.sdk.toml")
    )
    if v2:
        old_input, selection, occurrences, group = v2_supplied_input(
            profile, stage="syntax_binding", nomination=nomination, syntax_table=syntax
        )
    else:
        old_input, selection, occurrences, group = supplied_input(
            stage="syntax_binding", module_body=module
        )
    _, closure = read_grammar_declaration_context(old_input)
    selected_member = next(
        row for row in group.members if row.occurrence_ref == occurrences[0]
    )
    origin = decode_source_origin(bytes.fromhex(selected_member.origin_body_hex))
    own = provider.provider_contract
    owner_ref = SyntaxContractRefV1(own.key, own.version, own.schema_digest.value)
    scanner_raw = b"fixture original scanner source"
    scanner_binding = SyntaxSourceBindingV1(
        occurrences[0],
        source_occurrence_ref(origin.occurrence, "scanner.c"),
        origin.package.package_ref,
        "scanner.c",
        len(scanner_raw),
        ContentDigest.of_bytes(scanner_raw).value,
    )
    payloads = {}
    dependency_target = None
    for ordinal in reversed(range(len(paths))):
        path = paths[ordinal]
        dependencies = (
            (
                SyntaxDependencyV1(
                    "absent", "1", ContentDigest.of_bytes(b"absent").value
                ),
            )
            if missing_dependency
            else ()
        )
        if dependency and ordinal == 0:
            assert dependency_target is not None
            dependencies = (
                SyntaxDependencyV1(
                    dependency_target.contribution_ref,
                    dependency_target.version,
                    ContentDigest.of_bytes(b"foreign dependency").value
                    if bad_dependency_digest
                    else dependency_target.digest,
                ),
            )
        payload = SyntaxContributionSourceV1(
            "sample" if duplicate_label else f"sample-{ordinal}",
            "1",
            owner_ref,
            dependencies,
            (SyntaxRuleV1("sample", SyntaxExpressionV1("STRING", value="sample")),),
            ("sample",),
            ("sample",),
            (),
            (),
            SyntaxScannerV1("none", scanner_binding, ()) if scanner else None,
        )
        payloads[path] = encode_syntax_assembly_value(payload)
        binding = SyntaxSourceBindingV1(
            occurrences[0],
            source_occurrence_ref(origin.occurrence, path),
            origin.package.package_ref,
            path,
            len(payloads[path]),
            ContentDigest.of_bytes(payloads[path]).value,
        )
        account = [(binding, payloads[path])]
        if scanner:
            account.append((scanner_binding, scanner_raw))
        dependency_target = reconstruct_syntax_contribution(
            authored_source=binding,
            owner_contract=owner_ref,
            source_bodies=tuple(
                sorted(account, key=lambda row: row[0].relative_path.encode())
            ),
        )
    if scanner:
        payloads["scanner.c"] = scanner_raw
    members = tuple(member_sources(row, payloads) for row in group.members)
    group = CodeGrammarSourceGroupV1(
        group.root_occurrence_ref, members, group.dependency_edges
    )
    value = input_value(group, closure)
    expected_input = SemanticInputProductionExpectation.create(
        use_ref=value.use_ref,
        operation_ref=value.operation_ref,
        stage="syntax_binding",
        package_identity=SemanticInputPackageIdentity(
            value.package_identity.package, value.package_identity.package_name
        ),
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in value.sources),
        context_bodies=value.context_bodies,
    )
    ordinary = SemanticInputProductionInput(
        expected_input.use_ref,
        expected_input.operation_ref,
        expected_input.stage,
        expected_input.package_identity,
        value.sources,
        expected_input.input_digest,
        value.context_bodies,
    )
    selection = replace(selection, input_digest=ordinary.input_digest)
    previous = grammar_profile_selection_body(profile)
    joined = SemanticInputJoinedProductionInput(
        ordinary,
        (
            SemanticInputPredecessorBody(
                "code.profile_selection", previous.coordinate, previous.canonical_body
            ),
        ),
        ContentDigest.of_bytes(b"fixture portable predecessor closure, not admission"),
        ordinary.operation_ref,
    )
    observed = []
    for path in paths:
        raw = payloads[path]
        row = SyntaxSourceBindingV1(
            occurrences[0],
            source_occurrence_ref(origin.occurrence, path),
            origin.package.package_ref,
            path,
            len(raw),
            ContentDigest.of_bytes(raw).value,
        )
        account = [(row, raw)]
        if scanner:
            account.append((scanner_binding, scanner_raw))
        rebuilt = reconstruct_syntax_contribution(
            authored_source=row,
            owner_contract=owner_ref,
            source_bodies=tuple(
                sorted(account, key=lambda row: row[0].relative_path.encode())
            ),
        )
        encoded = encode_syntax_assembly_value(rebuilt)
        # Outer coordinates are explicit fixture result data. No claim of an
        # original registered Language producer or production output contract.
        body = SemanticBody(
            SemanticValueCoordinate(
                "fixture_observed_syntax",
                RAW,
                "fixture:observed:" + path,
                ContentDigest.of_bytes(encoded),
                len(encoded),
            ),
            encoded,
        )
        observed.append((occurrences[0], path, body))
    return dict(
        input=joined,
        selection=selection,
        catalog=catalog,
        provider_occurrences=occurrences,
        observed_contributions=tuple(observed),
    )


@pytest.mark.parametrize("count", (1, 2, 4))
@pytest.mark.parametrize("scanner", (False, True))
def test_original_language_reconstruction_and_complete_code_wire(
    admitted_catalog, count, scanner
):
    args = syntax_inputs(admitted_catalog, count=count, scanner=scanner)
    result = entry.produce_grammar_source_binding(**args)
    value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    assert grammar_syntax_binding_body(value) == result
    assert (
        len(value.contribution_bindings) == len(value.contribution_coordinates) == count
    )
    assert value.interpretation_profile == args["input"].predecessors[0].coordinate
    assert (
        value.profile_ref == "original.runtime.profile" and value.profile_version == "9"
    )
    assert tuple(
        row.contribution_coordinate for row in value.contribution_bindings
    ) == tuple(row[2].coordinate for row in args["observed_contributions"])
    assert owner.validate_grammar_source_binding_result(result, **args) is None


def test_v2_syntax_direct_entrance_preserves_original_owner_wire(admitted_catalog):
    args = syntax_inputs(admitted_catalog, v2=True)
    result = entry.produce_grammar_source_binding(**args)
    value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    assert value.profile_ref == "original.runtime.profile"
    assert value.code_profile_digest == admitted_catalog[2].digest
    assert len(value.contribution_bindings) == 1
    assert owner.validate_grammar_source_binding_result(result, **args) is None


@pytest.mark.parametrize("field", ("profile_ref", "version", "operation_kinds"))
def test_v2_syntax_predecessor_cannot_bypass_authored_nomination(
    admitted_catalog, monkeypatch, field
):
    original = admitted_catalog[2]
    foreign = replace(
        original, **{field: ("foreign",) if field == "operation_kinds" else "foreign"}
    )
    args = syntax_inputs(admitted_catalog, v2=True, nomination=foreign)

    def forbidden(*a, **kw):
        raise AssertionError("foreign V2 product reached Language interpretation")

    monkeypatch.setattr(language_owner, "reconstruct_syntax_contribution", forbidden)
    with pytest.raises(ContractViolation, match="nomination differs"):
        entry.produce_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "field",
    ("input", "selection", "catalog", "provider_occurrences", "observed_contributions"),
)
@pytest.mark.parametrize("invalid", (None, {}, []))
def test_exact_receiving_shapes_refuse(admitted_catalog, field, invalid):
    args = syntax_inputs(admitted_catalog)
    args[field] = invalid
    with pytest.raises((TypeError, ContractViolation)):
        entry.produce_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "kind",
    ("missing", "extra", "duplicate", "foreign_occurrence", "foreign_path", "reverse"),
)
def test_observed_source_bijection_refuses_without_label_fallback(
    admitted_catalog, kind
):
    args = syntax_inputs(admitted_catalog, count=2)
    rows = args["observed_contributions"]
    if kind == "missing":
        rows = rows[:1]
    elif kind == "duplicate":
        rows = (rows[0], rows[0])
    elif kind == "reverse":
        rows = rows[::-1]
    elif kind == "foreign_occurrence":
        rows = (("foreign", rows[0][1], rows[0][2]), rows[1])
    elif kind == "foreign_path":
        rows = ((rows[0][0], "absent.syntax.json", rows[0][2]), rows[1])
    else:
        rows = rows + ((rows[-1][0], "syntax/z.syntax.json", rows[-1][2]),)
    args["observed_contributions"] = rows
    with pytest.raises((TypeError, ContractViolation, SyntaxAssemblyContractError)):
        owner.produce_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "kind", ("missing_dependency", "duplicate_label", "anchor_mismatch")
)
def test_namespace_dependency_and_full_consumer_contract_refusals(
    admitted_catalog, kind
):
    args = syntax_inputs(admitted_catalog, count=2, **{kind: True})
    with pytest.raises((ContractViolation, SyntaxAssemblyContractError)) as caught:
        owner.produce_grammar_source_binding(**args)
    if kind == "duplicate_label":
        assert caught.value.code == "syntax_contribution_occurrence_ambiguous"
    if kind == "missing_dependency":
        assert caught.value.code == "syntax_contribution_source_missing"


@pytest.mark.parametrize("kind", ("role", "version", "value_ref", "different_profile"))
def test_full_retained_profile_predecessor_refuses(admitted_catalog, kind):
    args = syntax_inputs(admitted_catalog)
    previous = args["input"].predecessors[0]
    coordinate = previous.coordinate
    if kind == "role":
        coordinate = replace(coordinate, role="foreign")
    elif kind == "version":
        coordinate = replace(
            coordinate, contract=replace(coordinate.contract, version="99")
        )
    elif kind == "value_ref":
        coordinate = replace(coordinate, value_ref="foreign")
    else:
        _, _, profile, _ = admitted_catalog
        changed = grammar_profile_selection_body(replace(profile, version="10"))
        previous = replace(
            previous,
            coordinate=changed.coordinate,
            canonical_body=changed.canonical_body,
        )
    if kind != "different_profile":
        previous = replace(previous, role=coordinate.role, coordinate=coordinate)
    args["input"] = replace(args["input"], predecessors=(previous,))
    with pytest.raises(ContractViolation):
        owner.produce_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "field", ("role", "contract", "value_ref", "digest", "size_bytes", "body")
)
def test_result_refuses_complete_coordinate_and_body_substitutions(
    admitted_catalog, field
):
    args = syntax_inputs(admitted_catalog)
    result = copy.copy(owner.produce_grammar_source_binding(**args))
    if field == "body":
        object.__setattr__(result, "canonical_body", result.canonical_body + b" ")
    else:
        coordinate = result.coordinate
        value = {
            "role": "foreign",
            "contract": replace(coordinate.contract, version="99"),
            "value_ref": "foreign",
            "digest": ContentDigest.of_bytes(b"foreign"),
            "size_bytes": coordinate.size_bytes + 1,
        }[field]
        object.__setattr__(result, "coordinate", replace(coordinate, **{field: value}))
    with pytest.raises(ContractViolation):
        owner.validate_grammar_source_binding_result(result, **args)


@pytest.mark.parametrize(
    "failure",
    (RuntimeError("original Language failure"), KeyboardInterrupt(), SystemExit(7)),
)
def test_language_failure_and_interrupt_identity_survive(
    monkeypatch, admitted_catalog, failure
):
    args = syntax_inputs(admitted_catalog)
    calls = []

    def fail(**kw):
        calls.append(kw)
        raise failure

    monkeypatch.setattr(language_owner, "reconstruct_syntax_contribution", fail)
    with pytest.raises(type(failure)) as caught:
        owner.produce_grammar_source_binding(**args)
    assert caught.value is failure and len(calls) == 1


def test_late_catalog_retirement_refuses_after_real_language_call(
    monkeypatch, admitted_catalog
):
    args = syntax_inputs(admitted_catalog)
    parent, _, _, _ = admitted_catalog
    original = language_owner.reconstruct_syntax_contribution
    calls = []

    def reconstruct(**kw):
        value = original(**kw)
        calls.append(value)
        parent.live = False
        return value

    monkeypatch.setattr(language_owner, "reconstruct_syntax_contribution", reconstruct)
    with pytest.raises((RuntimeError, ContractViolation)):
        owner.produce_grammar_source_binding(**args)
    assert len(calls) == 1
    parent.live = True
    with pytest.raises(ContractViolation):
        owner.produce_grammar_source_binding(**args)
    assert len(calls) == 1


@pytest.mark.parametrize("scanner", (False, True))
def test_complete_selected_dependency_matches_original_language_digest(
    admitted_catalog, scanner
):
    args = syntax_inputs(admitted_catalog, count=2, dependency=True, scanner=scanner)
    result = owner.produce_grammar_source_binding(**args)
    assert owner.validate_grammar_source_binding_result(result, **args) is None


def test_equal_dependency_label_wrong_complete_digest_refuses(admitted_catalog):
    args = syntax_inputs(
        admitted_catalog, count=2, dependency=True, bad_dependency_digest=True
    )
    with pytest.raises(SyntaxAssemblyContractError, match="version/digest"):
        owner.produce_grammar_source_binding(**args)


@pytest.mark.parametrize("target", ("observed", "predecessor"))
def test_changed_result_data_cannot_survive_final_correspondence(
    monkeypatch, admitted_catalog, target
):
    args = syntax_inputs(admitted_catalog)
    original = owner.grammar_syntax_binding_body

    def encode(value):
        result = original(value)
        body = (
            args["observed_contributions"][0][2]
            if target == "observed"
            else args["input"].predecessors[0]
        )
        object.__setattr__(
            body,
            "coordinate",
            replace(body.coordinate, value_ref="foreign:after-encoding"),
        )
        return result

    monkeypatch.setattr(owner, "grammar_syntax_binding_body", encode)
    with pytest.raises(ContractViolation):
        owner.produce_grammar_source_binding(**args)


def test_join_budget_refuses_before_language_interpretation(
    monkeypatch, admitted_catalog
):
    args = syntax_inputs(admitted_catalog)
    occurrence, path, observed = args["observed_contributions"][0]
    raw = b"x" * (8 * 1024 * 1024)
    body = SemanticBody(
        replace(
            observed.coordinate, digest=ContentDigest.of_bytes(raw), size_bytes=len(raw)
        ),
        raw,
    )
    args["observed_contributions"] = ((occurrence, path, body),)

    def forbidden(**kw):
        raise AssertionError("over-budget input reached Language")

    monkeypatch.setattr(language_owner, "reconstruct_syntax_contribution", forbidden)
    with pytest.raises(ContractViolation, match="aggregate byte budget"):
        owner.produce_grammar_source_binding(**args)


def reproject_input(args, bodies):
    group, closure = read_grammar_declaration_context(args["input"].ordinary)
    members = tuple(member_sources(row, bodies) for row in group.members)
    rebuilt = input_value(
        CodeGrammarSourceGroupV1(
            group.root_occurrence_ref, members, group.dependency_edges
        ),
        closure,
    )
    expected = SemanticInputProductionExpectation.create(
        use_ref=rebuilt.use_ref,
        operation_ref=rebuilt.operation_ref,
        stage="syntax_binding",
        package_identity=rebuilt.package_identity,
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in rebuilt.sources),
        context_bodies=rebuilt.context_bodies,
    )
    ordinary = SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        rebuilt.sources,
        expected.input_digest,
        expected.context_bodies,
    )
    args["input"] = replace(args["input"], ordinary=ordinary)
    args["selection"] = replace(args["selection"], input_digest=ordinary.input_digest)


@pytest.mark.parametrize("change", ("owner", "scanner_missing", "scanner_occurrence"))
def test_original_owner_and_scanner_account_refuse_before_result(
    admitted_catalog, change
):
    args = syntax_inputs(admitted_catalog, scanner=True)
    group, _ = read_grammar_declaration_context(args["input"].ordinary)
    member = next(
        row
        for row in group.members
        if row.occurrence_ref == args["provider_occurrences"][0]
    )
    bodies = {row.relative_path: bytes.fromhex(row.body_hex) for row in member.sources}
    path = "syntax/0.syntax.json"
    payload = decode_syntax_assembly_value(
        bodies[path], expected_type=SyntaxContributionSourceV1
    )
    if change == "owner":
        payload = replace(
            payload,
            owner_contract=replace(
                payload.owner_contract,
                schema_digest=ContentDigest.of_bytes(b"foreign owner").value,
            ),
        )
    elif change == "scanner_occurrence":
        foreign = next(
            row for row in group.members if row.occurrence_ref != member.occurrence_ref
        )
        origin = decode_source_origin(bytes.fromhex(foreign.origin_body_hex))
        binding = replace(
            payload.scanner.source_binding,
            occurrence_ref=foreign.occurrence_ref,
            source_occurrence_ref=source_occurrence_ref(origin.occurrence, "scanner.c"),
        )
        payload = replace(
            payload, scanner=replace(payload.scanner, source_binding=binding)
        )
    else:
        del bodies["scanner.c"]
    bodies[path] = encode_syntax_assembly_value(payload)
    reproject_input(args, bodies)
    with pytest.raises(SyntaxAssemblyContractError):
        owner.produce_grammar_source_binding(**args)


def test_detached_coordinate_copy_is_data_not_original_result_admission(
    admitted_catalog,
):
    args = syntax_inputs(admitted_catalog)
    occurrence, path, observed = args["observed_contributions"][0]
    supplied = replace(
        observed,
        coordinate=replace(observed.coordinate, value_ref="fixture:detached-copy"),
    )
    args["observed_contributions"] = ((occurrence, path, supplied),)
    result = owner.produce_grammar_source_binding(**args)
    value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    assert value.contribution_bindings[0].contribution_coordinate == supplied.coordinate
    # This data-only success is deliberately not a retained producer result.
    assert not hasattr(result, "registration") and not hasattr(
        result, "source_admission"
    )


def test_auxiliary_home_reexports_the_same_original_functions():
    assert shim.produce_grammar_source_binding is owner.produce_grammar_source_binding
    assert (
        shim.validate_grammar_source_binding_result
        is owner.validate_grammar_source_binding_result
    )
