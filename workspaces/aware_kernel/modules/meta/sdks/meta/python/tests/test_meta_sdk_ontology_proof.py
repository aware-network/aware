from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import pytest

from aware_meta_sdk import (
    FunctionCallProof,
    FunctionCoverageSkip,
    MetaSdkClient,
    OigCommitExpectation,
    ProjectionBehaviorProof,
    ProjectionProof,
    assert_oig_commit_matches,
    prove_ontology_package,
)
from aware_meta_sdk import ontology_proof
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionResponse,
)


@pytest.mark.asyncio
async def test_prove_ontology_package_uses_projection_proof_handles() -> None:
    api = _FakeGeneratedMetaApi()
    sdk = MetaSdkClient(api_client=api)

    proof = await prove_ontology_package(
        sdk,
        package_root=Path("/repo/workspaces/aware_kernel/modules/content/ontology/structure"),
        source_files=("aware/content/content.aware",),
        projection_proofs=(ProjectionProof("Content"), "ContentChain"),
    )

    proof.assert_complete()
    assert proof.report.status == "passed"
    assert proof.report.as_dict()["projection_names"] == [
        "Content",
        "ContentChain",
    ]
    assert proof.package_name == "content-ontology"
    assert proof.fqn_prefix == "aware_content"
    assert proof.projection_names == frozenset({"Content", "ContentChain"})
    request = api.meta.diagnostics.requests[0]
    assert request.include_object_config_graph is True
    assert request.source_files == ["aware/content/content.aware"]


@pytest.mark.asyncio
async def test_ontology_proof_reports_missing_projection_handles() -> None:
    api = _FakeGeneratedMetaApi()
    sdk = MetaSdkClient(api_client=api)

    proof = await prove_ontology_package(
        sdk,
        package_root="/repo/modules/content/ontology/structure",
        projection_proofs=(ProjectionProof("MissingProjection"),),
    )

    assert proof.missing_projection_names == ("MissingProjection",)
    with pytest.raises(AssertionError, match="Missing projection proofs"):
        proof.assert_succeeded()


@pytest.mark.asyncio
async def test_ontology_proof_requires_projected_function_coverage_or_skip() -> None:
    api = _FakeGeneratedMetaApi()
    sdk = MetaSdkClient(api_client=api)

    proof = await prove_ontology_package(
        sdk,
        package_root="/repo/modules/content/ontology/structure",
        projection_proofs=(ProjectionProof("Content"),),
        behavior_proofs=(
            ProjectionBehaviorProof(
                "Content",
                covered_functions=(
                    FunctionCallProof(
                        "Content.create",
                        OigCommitExpectation(label="Content.create"),
                    ),
                ),
                expected_skips=(
                    FunctionCoverageSkip(
                        "Content.rename",
                        "receipt-gated native behavior proof",
                    ),
                ),
            ),
        ),
    )

    proof.assert_complete()
    behavior_result = proof.behavior_results[0]
    assert behavior_result.required_function_keys == (
        "Content.create",
        "Content.rename",
    )
    assert [
        result.status for result in behavior_result.function_results
    ] == ["passed", "skipped"]
    assert proof.report.as_dict()["behavior_proofs"] == [
        {
            "projection_name": "Content",
            "status": "passed",
            "exists": True,
            "required_functions": ["Content.create", "Content.rename"],
            "passed_functions": ["Content.create"],
            "skipped_functions": ["Content.rename"],
            "missing_functions": [],
            "unknown_functions": [],
            "invalid_skip_functions": [],
        }
    ]
    behavior_result.covered_function_proofs[0].assert_matches(
        {
            "domain_commit_id": uuid4(),
            "object_instance_graph_commit_id": uuid4(),
            "graph_hash_post": "sha256:post",
            "root_object_id": uuid4(),
        }
    )


@pytest.mark.asyncio
async def test_ontology_proof_reports_uncovered_projected_functions() -> None:
    api = _FakeGeneratedMetaApi()
    sdk = MetaSdkClient(api_client=api)

    proof = await prove_ontology_package(
        sdk,
        package_root="/repo/modules/content/ontology/structure",
        behavior_proofs=(
            ProjectionBehaviorProof(
                "Content",
                covered_functions=("Content.create",),
            ),
        ),
    )

    with pytest.raises(AssertionError, match="missing function coverage"):
        proof.assert_succeeded()
    assert proof.report.status == "failed"
    assert proof.report.behavior_reports[0].missing_function_keys == (
        "Content.rename",
    )


def test_oig_commit_expectation_checks_shared_commit_receipt_fields() -> None:
    branch_id = uuid4()
    root_object_id = uuid4()
    response = MetaGraphInvokeFunctionResponse(
        status="succeeded",
        domain_branch_id=branch_id,
        domain_projection_hash="projection:content",
        root_object_id=root_object_id,
        graph_hash_post="sha256:post",
        domain_commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )

    assert_oig_commit_matches(
        response,
        OigCommitExpectation(
            label="Content create",
            expected_domain_branch_id=branch_id,
            expected_domain_projection_hash="projection:content",
            expected_root_object_id=root_object_id,
        ),
    )


def test_oig_commit_expectation_fails_when_commit_fields_are_missing() -> None:
    with pytest.raises(AssertionError, match="missing domain_commit_id"):
        assert_oig_commit_matches(
            MetaGraphInvokeFunctionResponse(status="succeeded")
        )


def test_ontology_proof_import_boundary_stays_outside_meta_runtime() -> None:
    source = inspect.getsource(ontology_proof)
    forbidden_tokens = (
        "aware_meta.runtime",
        "aware_runtime",
        "services.meta",
        "MetaGraphRuntime",
        "handler_modules",
        "bootstrap_modules",
    )
    for token in forbidden_tokens:
        assert token not in source


@dataclass(slots=True)
class _FakeDiagnosticsApi:
    requests: list[object] = field(default_factory=list)

    async def analyze_object_config_graph_completeness(
        self,
        request: object,
    ) -> MetaCompletenessAnalyzeResponse:
        self.requests.append(request)
        return MetaCompletenessAnalyzeResponse(
            status="succeeded",
            actor_id=getattr(request, "actor_id"),
            workspace_root=getattr(request, "workspace_root"),
            package_root=getattr(request, "package_root"),
            aware_toml_path=getattr(request, "aware_toml_path"),
            package_name="content-ontology",
            fqn_prefix="aware_content",
            diagnostics=[],
            object_config_graph={
                "object_projection_graph_declarations": [
                    {
                        "projection_name": "Content",
                        "object_projection_graph_bindings": [
                            {
                                "class_name": "Content",
                                "class_fqn": (
                                    "aware_content.default.content.Content"
                                ),
                            }
                        ],
                    },
                    {"projection_name": "ContentChain"},
                ],
                "object_config_graph_nodes": [
                    {
                        "class_config": {
                            "name": "Content",
                            "class_fqn": (
                                "aware_content.default.content.Content"
                            ),
                            "class_config_function_configs": [
                                {
                                    "is_constructor": True,
                                    "function_config": {
                                        "name": "create",
                                        "owner_key": (
                                            "aware_content.default.content."
                                            "Content"
                                        ),
                                    },
                                },
                                {
                                    "is_constructor": False,
                                    "function_config": {
                                        "name": "rename",
                                        "owner_key": (
                                            "aware_content.default.content."
                                            "Content"
                                        ),
                                    },
                                },
                            ],
                        }
                    }
                ],
            },
        )


@dataclass(slots=True)
class _FakeMetaApi:
    diagnostics: _FakeDiagnosticsApi = field(default_factory=_FakeDiagnosticsApi)


@dataclass(slots=True)
class _FakeGeneratedMetaApi:
    meta: _FakeMetaApi = field(default_factory=_FakeMetaApi)
