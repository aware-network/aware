"""Issue-owned value parity with standard, uniquely named test collection."""

from __future__ import annotations

import dataclasses
import json
import tomllib
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
from aware_issue_sdk import repository_publication as values
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
AUTHORED = ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/aware"
RECORDS = (
    values.IssueRepositoryPublicationBinding,
    values.IssueRepositoryPublicationRequest,
    values.IssueRepositoryPublicationEnrollmentRequest,
)


def binding(head=None, paths=("a", "é.txt")):
    return values.IssueRepositoryPublicationBinding(
        "binding",
        "attempt",
        "repository",
        "refs/heads/main",
        head,
        paths,
        "sha256:" + "a" * 64,
        "sha256:" + "b" * 64,
        "generation",
        "provider",
        "execution",
    )


def sample(record, head=None):
    bound = binding(head)
    if record is values.IssueRepositoryPublicationBinding:
        return bound
    if record is values.IssueRepositoryPublicationRequest:
        return record("fb/2026-10-09/example", "sha256:" + "c" * 64, bound)
    return record(bound, "consumer", "repository_publication")


def lower():
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    path = "/sdk/issue/repository_publication_values.aware"
    document = parse_neutral_aware_source(
        (AUTHORED / "repository_publication_values.aware").read_text(), source_path=path
    )
    package = manifest["sdk"]
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=package["package_name"],
                fqn_prefix=package["fqn_prefix"],
                sources_root="/sdk/issue",
                dependencies=(),
                documents=(document,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({package["package_name"]}),
    )


@pytest.mark.parametrize("record", RECORDS)
@pytest.mark.parametrize("head", [None, "d" * 40])
def test_all_issue_values_round_trip_detached_with_exact_correlation(record, head):
    value = sample(record, head)
    payload = values.repository_publication_value_to_payload(value)
    saved = json.dumps(payload, ensure_ascii=False)
    decoded = values.repository_publication_value_from_payload(record, payload)
    assert decoded == value and type(decoded) is record
    assert (
        values.repository_publication_value_from_json(
            record, values.repository_publication_value_to_json(value)
        )
        == value
    )
    assert json.dumps(payload, ensure_ascii=False) == saved
    bound_payload = (
        payload
        if record is values.IssueRepositoryPublicationBinding
        else payload["binding"]
    )
    bound_payload["target_paths"].append("z")
    assert (
        decoded
        if record is values.IssueRepositoryPublicationBinding
        else decoded.binding
    ).target_paths == ("a", "é.txt")


@pytest.mark.parametrize("record", RECORDS)
def test_all_required_fields_and_unknown_fields_refuse(record):
    payload = values.repository_publication_value_to_payload(sample(record))
    missing = dict(payload)
    missing.pop(next(iter(missing)))
    for invalid in (missing, dict(payload, admitted=True)):
        saved = json.dumps(invalid, ensure_ascii=False)
        with pytest.raises(values.IssuePublicationValueError):
            values.repository_publication_value_from_payload(record, invalid)
        assert json.dumps(invalid, ensure_ascii=False) == saved


@pytest.mark.parametrize(
    "purpose", get_args(values.IssueRepositoryPublicationEnrollmentRequestPurpose)
)
def test_all_authored_purposes_preserve_exact_values(purpose):
    value = values.IssueRepositoryPublicationEnrollmentRequest(
        binding(), "consumer", purpose
    )
    assert (
        values.repository_publication_value_from_json(
            type(value), values.repository_publication_value_to_json(value)
        )
        == value
    )


@pytest.mark.parametrize("purpose", [True, None, "approved", "repository_publication "])
def test_purpose_cannot_be_coerced_or_widened(purpose):
    value = values.IssueRepositoryPublicationEnrollmentRequest(
        binding(), "consumer", purpose
    )
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_to_payload(value)


@pytest.mark.parametrize("record", RECORDS)
def test_production_source_real_lowering_preserves_owned_fields(record):
    meaning = lower()
    owner = "aware_issue_sdk." + record.__name__
    members = {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member" and entry.fqn.rsplit(".", 1)[0] == owner
    }
    ordered_members = tuple(sorted(members, key=lambda name: members[name]["position"]))
    assert ordered_members == tuple(field.name for field in dataclasses.fields(record))
    assert set(members) == set(get_type_hints(record))
    payload = values.repository_publication_value_to_payload(sample(record))
    assert tuple(payload) == ordered_members
    if record is values.IssueRepositoryPublicationBinding:
        assert members["expected_head"]["nullable"] is True
        assert members["target_paths"]["collection"] is True


def test_canonical_manifest_selects_source_and_fixture_body_is_preserved():
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    assert "*.aware" in manifest["build"]["include_paths"]
    assert manifest["sdk"]["fqn_prefix"] == "aware_issue_sdk"
    assert len(lower().entries) == 24
    fixture = (
        ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/fixtures/issue_publication_values.aware"
    )
    assert (AUTHORED / "repository_publication_values.aware").read_text().split(
        "\n", 2
    )[2] == fixture.read_text().split("\n", 2)[2]


@pytest.mark.parametrize(
    "path",
    ["", "/a", "a\\b", ".", "..", "a/../b", "a//b", "a/", "e\u0301/a", "a\ud800"]
    + [f"a{chr(number)}b" for number in (*range(32), *range(127, 160))],
)
def test_issue_binding_paths_refuse_noncanonical_spelling(path):
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_to_payload(binding(paths=(path,)))


@pytest.mark.parametrize("paths", [("b", "a"), ("a", "a")])
def test_issue_paths_refuse_unsorted_or_duplicate_collections(paths):
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_to_payload(binding(paths=paths))


@pytest.mark.parametrize(
    "source", ["NaN", "Infinity", "-Infinity", "1e999", "1.25", "{}", "[]", "null"]
)
def test_issue_json_refuses_malformed_or_nonfinite_input(source):
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_json(
            values.IssueRepositoryPublicationBinding, source
        )


def test_nested_duplicate_fields_and_shape_refuse():
    request = sample(values.IssueRepositoryPublicationRequest)
    source = values.repository_publication_value_to_json(request)
    duplicated = source.replace(
        '"expected_head":null', '"expected_head":null,"expected_head":null'
    )
    with pytest.raises(values.IssuePublicationValueError, match="duplicate"):
        values.repository_publication_value_from_json(type(request), duplicated)
    payload = values.repository_publication_value_to_payload(request)
    payload["binding"] = None
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(type(request), payload)


def test_known_type_names_and_caller_wrappers_do_not_restore_admission():
    class Forged(type):
        def __eq__(self, other):
            return True

    class Admission(metaclass=Forged):
        pass

    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(Admission, {})
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_to_payload(Admission())
    for handle in (
        values.IssueRepositoryPublicationAdmission,
        values.IssueRepositoryPublicationLease,
    ):
        with pytest.raises(TypeError):
            handle()
        with pytest.raises(values.IssuePublicationValueError):
            values.repository_publication_value_from_payload(handle, {})
    for name in (
        "admit_repository_publication",
        "consume_repository_publication",
    ):
        assert not hasattr(values, name)
    assert all(hasattr(values, name) for name in values.__all__)
