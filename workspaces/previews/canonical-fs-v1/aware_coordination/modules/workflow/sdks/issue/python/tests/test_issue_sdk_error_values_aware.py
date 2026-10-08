"""Real authored error-value projection; NOT complete Issue operation lowering."""

import hashlib
from pathlib import Path

import pytest
from aware_issue_sdk import (
    IssueCommitWorkspaceError,
    IssueMutationError,
    IssueProviderReport,
    IssueReadProjectionResolveError,
)
from aware_language_parsed_document_contract import NEUTRAL_SYNTAX_IR_SCHEMA
from aware_meta_type_schema import TypeSchemaBundle, validate_typed_value
from aware_meta_type_schema_aware_source import project_parsed_type_schema
from tree_sitter_aware.parsed_document import (
    TREE_SITTER_AWARE_PARSER_PROFILE,
    AwarePortableParseInput,
    AwareSemanticPackageProjectionRequest,
    parse_aware_document_batch,
)


@pytest.fixture(scope="module")
def bundle():
    root = Path(__file__).resolve().parents[2] / "aware"
    source = (root / "issue_operation_errors.aware").read_bytes()
    manifest = (root / "aware.sdk.toml").read_bytes()
    digest = lambda body: "sha256:" + hashlib.sha256(body).hexdigest()
    batch = parse_aware_document_batch(
        (
            AwarePortableParseInput(
                "package:issue-sdk@1",
                "issue-sdk",
                "sdk/sources/issue_operation_errors.aware",
                "cas://issue-errors/" + digest(source)[7:],
                digest(source),
                len(source),
                source.decode(),
            ),
        )
    ).batch
    projection_request = AwareSemanticPackageProjectionRequest.create(
        composition_authority_digest=digest(source),
        parent_operation_authority_digest=digest(source),
        package_ref="package:issue-sdk@1",
        package_name="issue-sdk",
        package_kind="sdk",
        fqn_prefix="aware_issue_sdk",
        semantic_version="1",
        package_root="sdk",
        sources_root="sdk/sources",
        manifest_path="sdk/aware.sdk.toml",
        manifest_ref="cas://manifest/" + digest(manifest)[7:],
        manifest_digest=digest(manifest),
        manifest_size_bytes=len(manifest),
        declared_source_paths=("sdk/sources/issue_operation_errors.aware",),
        direct_dependency_package_refs=(),
        dependency_package_refs=(),
        requested_root_refs=tuple(
            sorted(
                "aware_issue_sdk." + value.__name__
                for value in (
                    IssueReadProjectionResolveError,
                    IssueMutationError,
                    IssueCommitWorkspaceError,
                )
            )
        ),
        source_lifecycle="genesis",
        parser_contract=NEUTRAL_SYNTAX_IR_SCHEMA,
        parser_profile=TREE_SITTER_AWARE_PARSER_PROFILE,
        parsed_batch_ref=batch.batch_ref,
    )
    projection = project_parsed_type_schema(projection_request, batch)
    return TypeSchemaBundle.create(
        namespace="aware_issue_sdk",
        semantic_version="1",
        types=tuple(item.definition for item in projection.definitions),
    )


@pytest.mark.parametrize(
    "error_type",
    [IssueReadProjectionResolveError, IssueMutationError, IssueCommitWorkspaceError],
)
def test_authored_value_matches_public_failure_wire(bundle, error_type):
    value = error_type(
        "provider_result_invalid",
        "result",
        "issue_sdk.commit_workspace",
        "fb/2026-10-08/test",
        True,
        "unknown",
        IssueProviderReport('{"publication_receipt_ref":"git:reported"}'),
    ).to_wire()
    type_ref = "aware_issue_sdk." + error_type.__name__
    definition = next(item for item in bundle.types if item.type_ref == type_ref)
    assert {field.name for field in definition.fields} == set(value)
    assert validate_typed_value(bundle, type_ref, value).is_valid
    assert not validate_typed_value(
        bundle, type_ref, {**value, "provider_invoked": "true"}
    ).is_valid
    assert not validate_typed_value(
        bundle, type_ref, {**value, "capture_diagnostics": [17]}
    ).is_valid
    defaults = {
        field.name: field.default_value.to_wire()
        for field in definition.fields
        if field.default_value is not None
    }
    assert defaults["contract"] == error_type.contract
    assert defaults["provider_report_grade"] == "unvalidated_provider_report"
