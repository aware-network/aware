"""Portable receiving correspondence; only original owners supply admission."""

from __future__ import annotations

from dataclasses import replace

import aware_code_semantic_contract_runtime as public
import pytest
from aware_code_semantic_contract_runtime import grammar_profile_join as receiver
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    CodeGrammarSourceBodyV1,
    CodeGrammarSourceEdgeV1,
    CodeGrammarSourceGroupV1,
    CodeGrammarSourceMemberV1,
    grammar_source_group_body,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
    encode_retained_declaration_scope,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputPackageIdentity,
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
    SemanticInputSourceBody,
    SemanticInputSourceCoordinate,
)
from aware_code_semantic_contract_runtime.source_origin import (
    SOURCE_ORIGIN_REF,
    SemanticInputPackageOccurrence,
    SemanticInputSourceOccurrence,
    SemanticInputSourceOrigin,
    encode_source_origin,
    source_occurrence_ref,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SemanticSelectedSource,
    SemanticSourceSelection,
    source_selection_body,
)
from test_retained_declaration_scope import fixture as declaration_fixture

RAW = SemanticContractRef("fixture.raw", "1", ContentDigest.of_bytes(b"raw"))


def retained_body(role, ref, raw, value_ref=None):
    digest = ContentDigest.of_bytes(raw)
    return SemanticBody(
        SemanticValueCoordinate(
            role,
            ref,
            value_ref or "workspace-context:" + digest.value,
            digest,
            len(raw),
        ),
        raw,
    )


def portable_group(closure):
    members = []
    for scope in closure.scopes:
        package = scope.projection.packages[0]
        occurrence = SemanticInputPackageOccurrence(
            closure.repository_binding_ref,
            scope.scope_key,
            package.module_id,
            package.package_id,
            "" if package.package_root == "." else package.package_root,
            package.manifest_relative_path,
        )
        semantic_package = SemanticPackageCoordinate(
            "fixture:package", package.package_kind, package.manifest.content_digest
        )
        raw = b"fixture syntax bytes"
        coordinate = SemanticValueCoordinate(
            "selected_raw", RAW, "fixture:source", ContentDigest.of_bytes(raw), len(raw)
        )
        source = SemanticInputSourceCoordinate("part.syntax.json", coordinate)
        selection = SemanticSourceSelection(
            semantic_package,
            ContentDigest.of_bytes(b"source epoch"),
            ContentDigest.of_bytes(b"selected input"),
            (),
            (
                SemanticSelectedSource(
                    "selected_raw", RAW, source.relative_path, coordinate.digest
                ),
            ),
        )
        selected = source_selection_body(selection, role="selection")
        manifest = package.manifest
        outer = SemanticInputSourceCoordinate(
            package.manifest_relative_path,
            SemanticValueCoordinate(
                "outer_manifest",
                RAW,
                manifest.body_ref,
                manifest.content_digest,
                len(manifest.body),
            ),
        )
        origin = SemanticInputSourceOrigin(
            semantic_package,
            selection.source_identity_digest,
            selected.coordinate,
            selection.production_input_digest,
            occurrence,
            "/fixture/" + scope.workspace_handle,
            outer,
            (
                SemanticInputSourceOccurrence(
                    source, source_occurrence_ref(occurrence, source.relative_path)
                ),
            ),
        )
        origin_body = retained_body(
            "source_origin", SOURCE_ORIGIN_REF, encode_source_origin(origin)
        )
        members.append(
            CodeGrammarSourceMemberV1(
                occurrence.occurrence_ref,
                selected.coordinate,
                selected.canonical_body.hex(),
                origin_body.coordinate,
                origin_body.canonical_body.hex(),
                (CodeGrammarSourceBodyV1(source.relative_path, coordinate, raw.hex()),),
            )
        )
    root = members[0]
    edge = CodeGrammarSourceEdgeV1(
        root.occurrence_ref, members[1].occurrence_ref, "fixture", "fixture:participant"
    )
    return CodeGrammarSourceGroupV1(
        root.occurrence_ref,
        tuple(sorted(members, key=lambda row: row.occurrence_ref.encode())),
        (edge,),
    )


def input_value(group, closure, contexts=None):
    root = next(
        row for row in group.members if row.occurrence_ref == group.root_occurrence_ref
    )
    sources = tuple(
        SemanticInputSourceBody(
            SemanticInputSourceCoordinate(row.relative_path, row.coordinate),
            bytes.fromhex(row.body_hex),
        )
        for row in root.sources
    )
    bodies = (
        contexts
        if contexts is not None
        else (
            retained_body(
                "declaration_scope",
                RETAINED_DECLARATION_SCOPE_V3_REF,
                encode_retained_declaration_scope(closure),
            ),
            grammar_source_group_body(group),
        )
    )
    from aware_code_semantic_contract_runtime.source_origin import decode_source_origin

    origin = decode_source_origin(bytes.fromhex(root.origin_body_hex))
    expected = SemanticInputProductionExpectation.create(
        use_ref="fixture:receiving",
        operation_ref="fixture:operation",
        stage="fixture:receiving",
        package_identity=SemanticInputPackageIdentity(
            origin.package, "fixture-package"
        ),
        operation_identity=object(),
        source_identity=object(),
        source_coordinates=tuple(row.source for row in sources),
        context_bodies=bodies,
    )
    return SemanticInputProductionInput(
        expected.use_ref,
        expected.operation_ref,
        expected.stage,
        expected.package_identity,
        sources,
        expected.input_digest,
        expected.context_bodies,
    )


def test_both_contexts_decode_complete_portable_members_not_admission():
    closure = declaration_fixture()
    group = portable_group(closure)
    value = input_value(group, closure)
    assert (
        public.read_grammar_declaration_context
        is receiver.read_grammar_declaration_context
    )
    decoded = receiver.read_grammar_declaration_context(value)
    assert decoded == (group, closure)
    assert len(decoded[0].members) == 2
    assert decoded[0].members[0].sources == decoded[0].members[1].sources
    assert not hasattr(decoded[1], "declaration_handle")


@pytest.mark.parametrize("role", ["declaration_scope", "grammar_source_group"])
@pytest.mark.parametrize(
    "kind", ["missing", "role", "key", "version", "schema", "value_ref"]
)
def test_context_substitution_refuses_even_with_fresh_input_digest(role, kind):
    closure = declaration_fixture()
    group = portable_group(closure)
    value = input_value(group, closure)
    bodies = list(value.context_bodies)
    index = next(i for i, row in enumerate(bodies) if row.coordinate.role == role)
    original = bodies[index]
    if kind == "missing":
        bodies.pop(index)
    else:
        coordinate = original.coordinate
        if kind == "role":
            coordinate = replace(coordinate, role="foreign")
        elif kind == "value_ref":
            coordinate = replace(coordinate, value_ref="foreign:ref")
        else:
            ref = coordinate.contract
            changed = (
                ContentDigest.of_bytes(b"foreign schema")
                if kind == "schema"
                else "foreign"
            )
            ref = replace(
                ref, **{"schema_digest" if kind == "schema" else kind: changed}
            )
            coordinate = replace(coordinate, contract=ref)
        bodies[index] = replace(original, coordinate=coordinate)
    bodies.sort(key=lambda item: item.coordinate.role.encode())
    changed = input_value(group, closure, contexts=tuple(bodies))
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(changed)


@pytest.mark.parametrize(
    "field",
    [
        "package_kind",
        "package_root",
        "manifest_relative_path",
        "manifest_ref",
        "manifest_body",
        "package_id",
        "module_id",
    ],
)
def test_complete_member_manifest_not_matching_labels_or_bytes(field):
    closure = declaration_fixture()
    group = portable_group(closure)
    scope = closure.scopes[0]
    package = scope.projection.packages[0]
    if field == "manifest_ref":
        package = replace(
            package, manifest=replace(package.manifest, body_ref="foreign:body")
        )
    elif field == "manifest_body":
        body = b"foreign manifest"
        package = replace(
            package,
            manifest=replace(
                package.manifest,
                body=body,
                content_digest=ContentDigest.of_bytes(body),
                body_ref="foreign:manifest",
            ),
        )
    elif field in {"package_root", "manifest_relative_path"}:
        root = "other/root" if field == "package_root" else package.package_root
        local = (
            "other.toml"
            if field == "manifest_relative_path"
            else package.manifest_relative_path
        )
        package = replace(
            package,
            package_root=root,
            manifest_relative_path=local,
            manifest=replace(package.manifest, relative_path=root + "/" + local),
        )
    elif field == "module_id":
        module = replace(scope.projection.modules[0], module_id="foreign")
        package = replace(package, module_id="foreign")
        scope = replace(
            scope,
            projection=replace(
                scope.projection, modules=(module,), packages=(package,)
            ),
        )
    else:
        package = replace(package, **{field: "foreign"})
    scope = replace(scope, projection=replace(scope.projection, packages=(package,)))
    changed = replace(closure, scopes=(scope, *closure.scopes[1:]))
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(input_value(group, changed))


def test_retained_module_and_profile_bodies_are_not_interpreted_or_cropped():
    closure = declaration_fixture()
    group = portable_group(closure)
    scope = closure.scopes[0]
    module = scope.projection.modules[0]
    changed_body = b"different complete authored module bytes"
    module = replace(
        module,
        manifest=replace(
            module.manifest,
            body=changed_body,
            content_digest=ContentDigest.of_bytes(changed_body),
            body_ref="foreign:module",
        ),
    )
    scope = replace(scope, projection=replace(scope.projection, modules=(module,)))
    changed = replace(closure, scopes=(scope, *closure.scopes[1:]))
    decoded = receiver.read_grammar_declaration_context(input_value(group, changed))
    assert decoded[1] == changed
    assert decoded[1].local_profiles == closure.local_profiles
    # A coherent supplied change is data. Original Workspace currentness must
    # refuse source replacement before/after original registered production.


def test_invalid_input_digest_refuses_before_any_decoder(monkeypatch):
    closure = declaration_fixture()
    group = portable_group(closure)
    value = input_value(group, closure)
    object.__setattr__(value, "input_digest", ContentDigest.of_bytes(b"foreign input"))

    def forbidden(*args, **kwargs):
        raise AssertionError("decoder reached before input check")

    monkeypatch.setattr(receiver, "decode_grammar_source_group", forbidden)
    monkeypatch.setattr(receiver, "decode_retained_declaration_scope", forbidden)
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(value)


@pytest.mark.parametrize("raw", [b"{}", b"not JSON", b"null", b"[]"])
def test_original_declaration_codec_rejects_invalid_payload(raw):
    closure = declaration_fixture()
    group = portable_group(closure)
    contexts = (
        retained_body("declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF, raw),
        grammar_source_group_body(group),
    )
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(input_value(group, closure, contexts))


def test_foreign_repository_refuses_without_calling_a_source_owner():
    closure = declaration_fixture()
    group = portable_group(closure)
    scopes = tuple(
        replace(
            row, projection=replace(row.projection, repository_binding_ref="foreign")
        )
        for row in closure.scopes
    )
    changed = replace(closure, repository_binding_ref="foreign", scopes=scopes)
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(input_value(group, changed))


def test_other_original_contexts_are_preserved_and_still_charged():
    closure = declaration_fixture()
    group = portable_group(closure)
    value = input_value(group, closure)
    other = retained_body("z_other", RAW, b"another original input")
    value = input_value(group, closure, (*value.context_bodies, other))
    assert receiver.read_grammar_declaration_context(value) == (group, closure)
    assert value.context_bodies[-1] is other


@pytest.mark.parametrize("role", ["declaration_scope", "grammar_source_group"])
def test_same_contract_under_another_role_is_ambiguous(role):
    closure = declaration_fixture()
    group = portable_group(closure)
    value = input_value(group, closure)
    original = next(row for row in value.context_bodies if row.coordinate.role == role)
    extra = replace(original, coordinate=replace(original.coordinate, role="z_alias"))
    changed = input_value(group, closure, (*value.context_bodies, extra))
    with pytest.raises(ContractViolation):
        receiver.read_grammar_declaration_context(changed)


def test_exact_input_graph_rejects_foreign_objects_before_decoder(monkeypatch):
    class Foreign:
        def __getattribute__(self, name):
            raise AssertionError("foreign callback")

    def forbidden(*args, **kwargs):
        raise AssertionError("decoder reached")

    monkeypatch.setattr(receiver, "decode_grammar_source_group", forbidden)
    monkeypatch.setattr(receiver, "decode_retained_declaration_scope", forbidden)
    with pytest.raises(TypeError):
        receiver.read_grammar_declaration_context(Foreign())


def test_repository_root_package_dot_maps_to_original_empty_occurrence_root():
    closure = declaration_fixture()
    scopes = []
    for scope in closure.scopes:
        package = scope.projection.packages[0]
        package = replace(
            package,
            package_root=".",
            manifest=replace(
                package.manifest, relative_path=package.manifest_relative_path
            ),
        )
        scopes.append(
            replace(scope, projection=replace(scope.projection, packages=(package,)))
        )
    closure = replace(closure, scopes=tuple(scopes))
    group = portable_group(closure)
    assert receiver.read_grammar_declaration_context(input_value(group, closure)) == (
        group,
        closure,
    )
