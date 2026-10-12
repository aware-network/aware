from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from aware_meta_type_schema.composition import TypeOwnerBinding
from aware_meta_type_schema.definition_fragment import (
    SourceDefinitionBinding,
    TypeDefinitionFragment,
    TypeSchemaFragmentError,
    TypeSchemaSourceAttributionFragment,
)
from aware_meta_type_schema.model import (
    FieldDefinition,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    ValueShape,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "contracts/v2/workflow-content-storage/definition-movements.json"
)


def _issue_definition() -> TypeDefinition:
    return TypeDefinition(
        type_ref="workflow.Issue",
        name="Issue",
        kind=TypeKind.GRAPH_OBJECT,
        fields=(
            FieldDefinition(
                field_ref="workflow.Issue.description",
                name="description",
                shape=ValueShape.named("content.Text"),
            ),
        ),
    )


def test_definition_fragment_reuses_exact_type_definition_without_owner_fields() -> (
    None
):
    fragment = TypeDefinitionFragment.create(_issue_definition())

    assert fragment.type_ref == "workflow.Issue"
    assert fragment.referenced_type_refs == ("content.Text",)
    assert not {
        "package_ref",
        "source_path",
        "document_coordinate_ref",
    } & set(fragment.to_wire())
    assert fragment.to_body().coordinate.authority_ref == fragment.fragment_ref


def test_definition_fragment_rejects_recomputed_reference_closure() -> None:
    fragment = TypeDefinitionFragment.create(_issue_definition())
    with pytest.raises(TypeSchemaFragmentError, match="do not match"):
        _ = TypeDefinitionFragment(
            fragment.definition,
            (),
            fragment.fragment_ref,
        )
    with pytest.raises(TypeSchemaFragmentError, match="fragment_ref"):
        _ = replace(fragment, fragment_ref="sha256:" + "0" * 64)


def test_source_attribution_is_exact_sorted_and_content_addressed() -> None:
    fragment = TypeDefinitionFragment.create(_issue_definition())
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref="package:workflow@1.0.0",
        source_path="issue/issue.aware",
        document_coordinate_ref="sha256:" + "1" * 64,
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate),
        ),
    )

    assert attribution.bindings[0].definition == fragment.to_body().coordinate
    assert attribution.to_body().coordinate.authority_ref == attribution.attribution_ref


def test_source_attribution_rejects_duplicate_or_wrong_fragment_schema() -> None:
    fragment = TypeDefinitionFragment.create(_issue_definition())
    binding = SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate)
    with pytest.raises(TypeSchemaFragmentError, match="duplicate"):
        TypeSchemaSourceAttributionFragment.create(
            package_ref="package:workflow@1.0.0",
            source_path="issue/issue.aware",
            document_coordinate_ref="sha256:" + "1" * 64,
            bindings=(binding, binding),
        )
    wrong = (
        TypeOwnerBinding.create(
            type_ref=fragment.type_ref,
            package_ref="package:workflow@1.0.0",
        )
        .to_body()
        .coordinate
    )
    with pytest.raises(TypeSchemaFragmentError, match="definition fragment"):
        _ = SourceDefinitionBinding(fragment.type_ref, wrong)


def test_source_attribution_delete_evidence_contains_no_source_body() -> None:
    fragment = TypeDefinitionFragment.create(_issue_definition())
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref="package:workflow@1.0.0",
        source_path="issue/issue.aware",
        document_coordinate_ref="sha256:" + "1" * 64,
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate),
        ),
    )
    wire = attribution.to_wire()
    assert "source_text" not in wire
    assert "syntax" not in wire


def test_provider_neutral_definition_movement_fixture_is_exact() -> None:
    expected = json.loads(_FIXTURE.read_text())["movements"]
    actual = []
    for type_ref in ("content.Text", "storage.Blob", "workflow.Issue"):
        package = type_ref.split(".", 1)[0]
        fragment = TypeDefinitionFragment.create(
            TypeDefinition(
                type_ref=type_ref,
                name=type_ref.rsplit(".", 1)[-1],
                kind=TypeKind.SCALAR_ALIAS,
                scalar_target=ScalarKind.STRING,
            )
        )
        attribution = TypeSchemaSourceAttributionFragment.create(
            package_ref=f"package:{package}@1.0.0",
            source_path=f"{package}/{package}.aware",
            document_coordinate_ref=f"coordinate:{package}",
            bindings=(
                SourceDefinitionBinding(
                    fragment.type_ref,
                    fragment.to_body().coordinate,
                ),
            ),
        )
        actual.append(
            {
                "type_ref": type_ref,
                "fragment_ref": fragment.fragment_ref,
                "attribution_ref": attribution.attribution_ref,
                "definition_coordinate_ref": fragment.to_body().coordinate.coordinate_ref,
                "attribution_coordinate_ref": attribution.to_body().coordinate.coordinate_ref,
            }
        )
    assert actual == expected
