from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest

import aware_api_runtime.workspace_provider as workspace_provider
from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
    ApiSemanticFunctionCallInvocation,
    ApiSemanticFunctionCallInvocationResult,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_ENDPOINT_UPDATE_FUNCTION_REF,
)
from aware_api_runtime.workspace_provider.deltas.baseline import (
    api_delta_baseline_semantic_object_index_from_root_and_source,
    api_delta_baseline_semantic_object_index_from_root_oig,
    api_delta_baseline_semantic_payload_index_from_source_code_package_oig,
    api_delta_root_baseline_hydration_ref_resolution,
    api_delta_source_baseline_hydration_ref_resolution,
)
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SemanticFunctionCallContext,
    SemanticMaterializationBaselineRef,
    SemanticProviderDeltaPreviousEvidenceResolverRequest,
    SemanticProviderDeltaRequest,
    encode_semantic_function_call_context_by_provider,
)
from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
)


class _RecordingApiExecutionBackend:
    def __init__(self) -> None:
        self.invocations: list[ApiSemanticFunctionCallInvocation] = []

    async def invoke(
        self,
        invocation: ApiSemanticFunctionCallInvocation,
    ) -> ApiSemanticFunctionCallInvocationResult:
        self.invocations.append(invocation)
        return ApiSemanticFunctionCallInvocationResult(
            object_id="unexpected-created-object-id",
        )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_simple_api_delta_fixture(workspace_root: Path) -> Path:
    api_toml_path = workspace_root / "aware.api.toml"
    _write(
        api_toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "demo-api"',
                'fqn_prefix = "aware_demo_api"',
                "version_number = 1",
                'title = "Demo API"',
                'description = "Demo API semantic package"',
                "",
                "[build]",
                'sources_dir = "apis"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                'compilation_mode = "api_ontology"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "apis" / "demo.aware",
        "\n".join(
            [
                "api demo {",
                "    capability read_demo {",
                "        endpoint read_demo aware_demo_api.ReadDemoRequest {",
                "            response aware_demo_api.DemoResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    return api_toml_path


def _api_provider_delta_request(
    *,
    api_toml_path: Path,
) -> SemanticProviderDeltaRequest:
    return SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "demo-api",
                "workspace_manifest_kind": "api",
                "manifest_path": api_toml_path.as_posix(),
                "source_code_package_id": "source-code-package-id",
            },
            "semantic_contract": {
                "module": "aware_api_runtime.semantic_contract",
                "provider_key": "aware_api",
                "role": "aware_api.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:current",
            "code_package_delta": CodePackageDelta(
                package_name="demo-api",
                package_root=".",
                sources_root="apis",
                manifest_relative_path=api_toml_path.name,
                authority_kind="workspace_provider_delta",
                source_revision_id="provider-delta-baseline-ref-test",
                paths=[
                    CodePackageDeltaPath(
                        relative_path="apis/demo.aware",
                        kind=CodePackageDeltaKind.update,
                        content_text=(
                            api_toml_path.parent / "apis" / "demo.aware"
                        ).read_text(encoding="utf-8"),
                        language=CodeLanguage.aware,
                        is_structural=True,
                    )
                ],
            ),
            "delta_cause_hints": {
                "changed_path_count": 1,
                "source_owned_path_count": 1,
                "generated_fallout_path_count": 0,
                "changed_path_classifications": {"source_owned": 1},
                "top_changed_path_limit": 8,
                "top_changed_paths": [
                    {
                        "path": "apis/demo.aware",
                        "change_kind": "update",
                        "classification": "source_owned",
                        "package_relative_path": "apis/demo.aware",
                        "language": "aware",
                        "is_structural": True,
                    }
                ],
                "current_delta_fingerprint_available": True,
                "previous_delta_fingerprint_available": True,
            },
            "previous_materialization_evidence": {
                "available": True,
                "previous_delta_fingerprint_available": True,
                "evidence_source": "workspace_semantic_baseline_resolution",
                "current_semantic_object_id_count": 0,
                "provider_delta_operation_execution_context_available": False,
            },
            "baseline_ref": _baseline_ref_payload(api_toml_path=api_toml_path),
        }
    )


def _baseline_ref_payload(*, api_toml_path: Path) -> dict[str, object]:
    return {
        "workspace_revision_id": "workspace-revision-id",
        "workspace_materialization_id": "workspace-materialization-id",
        "workspace_materialization_index": 3,
        "revision_code_package_id": "revision-code-package-id",
        "source_code_package_id": "source-code-package-id",
        "source_object_instance_graph_commit_id": "source-oig-commit",
        "revision_code_package_object_instance_graph_commit_id": "source-oig-commit",
        "semantic_package_commit_id": "semantic-package-commit-id",
        "semantic_owner_module": "aware_api",
        "semantic_package_kind": "api_package",
        "semantic_package_id": "semantic-package-id",
        "semantic_package_name": "demo-api",
        "semantic_contract_module": "aware_api_runtime.semantic_contract",
        "semantic_contract_name": "aware.semantic_provider",
        "semantic_contract_role": "aware_api.provider",
        "semantic_contract_provider_key": "aware_api",
        "semantic_projection_name": "ApiPackage",
        "semantic_branch_id": "semantic-branch-id",
        "semantic_object_instance_graph_commit_id": "semantic-package-oig-commit",
        "semantic_root_kind": "api",
        "semantic_root_id": "api-id",
        "semantic_root_object_instance_graph_commit_id": "api-root-oig-commit",
        "manifest_path": api_toml_path.as_posix(),
        "manifest_toml_path": api_toml_path.as_posix(),
    }


def _matching_baseline_semantic_object_index() -> dict[str, dict[str, object]]:
    return {
        "api:demo": {
            "object_id": "api-id",
            "object_kind": "api",
            "payload": {
                "name": "demo",
                "capability_count": 1,
                "graph_count": 0,
            },
        },
        "api:demo/capability:read_demo": {
            "object_id": "capability-id",
            "object_kind": "api_capability",
            "payload": {
                "api_name": "demo",
                "name": "read_demo",
                "description": None,
                "endpoint_count": 1,
            },
        },
        "api:demo/capability:read_demo/endpoint:read_demo": {
            "object_id": "endpoint-id",
            "object_kind": "api_capability_endpoint",
            "payload": {
                "api_name": "demo",
                "capability_name": "read_demo",
                "name": "read_demo",
                "description": None,
                "request_class_ref": "aware_demo_api.ReadDemoRequest",
            },
        },
    }


def _execution_request(
    base_request: SemanticProviderDeltaRequest,
    **overrides: object,
) -> SimpleNamespace:
    fields: dict[str, object] = {
        "package": base_request.package,
        "semantic_contract": base_request.semantic_contract,
        "current_delta_fingerprint": base_request.current_delta_fingerprint,
        "code_package_delta": base_request.code_package_delta,
        "delta_cause_hints": base_request.delta_cause_hints,
        "previous_materialization_evidence": (
            base_request.previous_materialization_evidence
        ),
        "baseline_ref": base_request.baseline_ref,
        "baseline_source_object_instance_graph_commit_id": (
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        "baseline_semantic_object_instance_graph_commit_id": (
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        "execute_provider_delta_materialization": True,
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _baseline_oig_class_instance(
    *,
    model_type: type[object],
    object_id: str,
    values: dict[str, object],
) -> SimpleNamespace:
    entity = model_type.get_class_config()  # type: ignore[attr-defined]
    field_id_by_name = {
        binding.field.name: binding.field.id
        for binding in entity.field_bindings
        if binding.field is not None
    }
    attributes = tuple(
        SimpleNamespace(
            attribute=SimpleNamespace(
                id=f"attribute:{object_id}:{field_name}",
                attribute_config_id=field_id_by_name[field_name],
                value_root=SimpleNamespace(primitive_value={"value": value}),
            )
        )
        for field_name, value in values.items()
        if value is not None
    )
    return SimpleNamespace(
        class_config_id=entity.id,
        source_object_id=object_id,
        class_instance_attributes=attributes,
        attributes=(),
    )


def _matching_baseline_api_root_oig() -> SimpleNamespace:
    return SimpleNamespace(
        class_instances=(
            _baseline_oig_class_instance(
                model_type=Api,
                object_id="api-id",
                values={"name": "demo", "description": None},
            ),
            _baseline_oig_class_instance(
                model_type=ApiCapability,
                object_id="capability-id",
                values={
                    "api_id": "api-id",
                    "name": "read_demo",
                    "description": None,
                },
            ),
            _baseline_oig_class_instance(
                model_type=ApiCapabilityEndpoint,
                object_id="endpoint-id",
                values={
                    "api_capability_id": "capability-id",
                    "name": "read_demo",
                    "description": None,
                },
            ),
            _baseline_oig_class_instance(
                model_type=ApiCapabilityEndpointRequestConfig,
                object_id="request-config-id",
                values={
                    "api_capability_endpoint_id": "endpoint-id",
                    "class_config_id": "request-class-config-id",
                    "description": None,
                },
            ),
        ),
    )


def _matching_baseline_source_code_package_oig(
    *,
    source_text: str,
) -> SimpleNamespace:
    relative_path = "apis/demo.aware"
    return SimpleNamespace(
        class_instances=(
            _baseline_oig_class_instance(
                model_type=CodePackage,
                object_id="source-code-package-id",
                values={
                    "manifest_relative_path": "aware.api.toml",
                    "package_name": "demo-api",
                    "package_root": ".",
                    "sources_root": "apis",
                    "language": "aware",
                },
            ),
            _baseline_oig_class_instance(
                model_type=CodePackageCode,
                object_id="code-package-code-id",
                values={
                    "code_package_id": "source-code-package-id",
                    "relative_path": relative_path,
                    "path_role": "authored_source",
                },
            ),
            _baseline_oig_class_instance(
                model_type=Code,
                object_id="code-id",
                values={
                    "code_package_code_id": "code-package-code-id",
                    "relative_path": relative_path,
                    "language": "aware",
                    "content_part_text_id": "content-part-text-id",
                },
            ),
            _baseline_oig_class_instance(
                model_type=ContentPartText,
                object_id="content-part-text-id",
                values={
                    "key": "default",
                    "inline_text": source_text,
                },
            ),
        ),
    )


def test_api_provider_delta_previous_evidence_resolver_uses_full_rebuild_details(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    api_id = "ac849708-1a41-55f0-b303-76210a7625e9"
    capability_id = stable_api_capability_id(
        api_id=UUID(api_id),
        name="read_demo",
    )
    endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name="read_demo",
    )

    result = (
        workspace_provider.resolve_api_provider_delta_previous_materialization_evidence(
            request=SemanticProviderDeltaPreviousEvidenceResolverRequest(
                provider_key="aware_api",
                semantic_owner="aware_api.provider",
                workspace_root=tmp_path,
                manifest_path=api_toml_path,
                request=base_request,
                previous_materialization_evidence={
                    **dict(base_request.previous_materialization_evidence),
                    "provider_materialization_details": {
                        "steps": (
                            {
                                "details": {
                                    "api_id": api_id,
                                    "api_name": "demo",
                                    "api_endpoint_catalog": {
                                        "demo": {"read_demo": ("read_demo",)}
                                    },
                                    "api_semantic_object_index": (
                                        _matching_baseline_semantic_object_index()
                                    ),
                                },
                            },
                        )
                    },
                },
            )
        )
    )

    assert result.status == "resolved"
    evidence = result.previous_materialization_evidence
    assert evidence["provider_delta_operation_execution_context_available"] is True
    assert evidence["current_semantic_object_ids"] == {
        "api:demo": api_id,
        "api:demo/capability:read_demo": str(capability_id),
        "api:demo/capability:read_demo/endpoint:read_demo": str(endpoint_id),
    }
    baseline_index = cast(
        dict[str, dict[str, object]],
        evidence["baseline_semantic_object_index"],
    )
    assert baseline_index == _matching_baseline_semantic_object_index()
    assert evidence["baseline_semantic_object_index_count"] == 3


@pytest.mark.asyncio
async def test_api_provider_delta_accepts_code_owned_request_contract(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    provider_delta_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    code_request = SemanticProviderDeltaRequest.model_validate(
        provider_delta_request.model_dump(mode="json")
    )

    result = await workspace_provider.materialize_delta(
        request=_execution_request(code_request),
    )

    details = cast(dict[str, object], result["details"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    assert result["status"] == "succeeded"
    assert head_move_plan["provider_delta_request_key"] == (
        code_request.provider_delta_request_key
    )
    baseline_ref = cast(dict[str, object], head_move_plan["baseline_ref"])
    assert baseline_ref["semantic_branch_id"] == ("semantic-branch-id")


@pytest.mark.asyncio
async def test_api_provider_delta_reports_baseline_ref_but_blocks_missing_current_head(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)

    result = await workspace_provider.materialize_delta(
        request=_execution_request(base_request),
    )

    details = cast(dict[str, object], result["details"])
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    dirty_diff = cast(dict[str, object], details["api_semantic_dirty_diff"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_execution_preflight = cast(
        dict[str, object],
        details["provider_delta_typed_operation_execution_preflight"],
    )
    preflight = cast(dict[str, object], details["baseline_hydration_preflight"])
    assert result["status"] == "succeeded"
    assert details["semantic_delta_count"] == 3
    assert operation_plan["operation_count"] == 3
    assert operation_plan["api_semantic_dirty_diff_status"] == (
        "semantic_dirty_diff_blocked"
    )
    assert operation_plan["api_baseline_index_compare_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert details["provider_delta_typed_operation_execution_status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert typed_execution_preflight["status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert typed_execution_preflight["typed_operation_count"] == 0
    assert typed_execution_preflight["blocked_plan_operation_count"] == 3
    assert typed_execution_preflight["payload_completeness_checked"] is False
    assert typed_execution_preflight["payload_complete"] is False
    assert operation_plan["provider_delta_typed_operation_execution_preflight"] == (
        typed_execution_preflight
    )
    assert operation_plan["provider_delta_typed_operation_execution_status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert operation_plan["provider_delta_typed_operation_execution_blocked"] is True
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["blocked_entry_count"] == 3
    assert dirty_diff["baseline_index_compare_available"] is False
    assert dirty_diff["baseline_index_compare_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert dirty_diff["dirty_entry_count"] == 3
    assert dirty_diff["baseline_compare_operation_counts"] == {"blocked": 3}
    assert head_move_plan["contract_version"] == (
        "aware.workspace.semantic-materialization.provider-delta-head-move.v1"
    )
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["blocked_status"] == "semantic_dirty_diff_blocked"
    assert head_move_plan["planned_operation_count"] == 0
    assert head_move_plan["baseline_hydration_status"] == (
        "current_head_context_missing"
    )
    assert operation_execution["operation_count"] == 3
    assert operation_execution["status"] == "typed_operation_execution_blocked"
    assert operation_execution["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert operation_execution["did_execute"] is False
    assert preflight["status"] == "current_head_context_missing"
    assert preflight["commit_backed_baseline_available"] is True
    assert preflight["baseline_ref_available"] is True
    assert preflight["baseline_ref_hydrator_ready"] is True
    assert preflight["current_head_context_available"] is False
    assert preflight["baseline_commit_refs"] == {
        "baseline_source_object_instance_graph_commit_id": "source-oig-commit",
        "baseline_semantic_object_instance_graph_commit_id": (
            "semantic-package-oig-commit"
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            "api-root-oig-commit"
        ),
    }
    assert operation_plan["baseline_hydration_preflight"] == preflight
    assert operation_plan["api_semantic_dirty_diff"] == dirty_diff
    assert operation_plan["provider_delta_head_move_plan"] == head_move_plan


@pytest.mark.asyncio
async def test_api_provider_delta_hydrates_current_head_from_durable_baseline_index(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    hydration_refs: list[dict[str, object]] = []

    async def _baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: object,
    ) -> tuple[object, dict[str, object]]:
        assert getattr(request, "require_full_baseline_oig") is True
        hydration_refs.append(cast(dict[str, object], baseline_ref))
        hydration_ref = cast(dict[str, object], baseline_ref)
        if hydration_ref["semantic_projection_name"] == "CodePackage":
            return (
                _matching_baseline_source_code_package_oig(
                    source_text=(
                        api_toml_path.parent / "apis" / "demo.aware"
                    ).read_text(encoding="utf-8"),
                ),
                {
                    "status": "baseline_hydrated",
                    "reason": "workspace_baseline_source_oig_hydrated_from_test",
                    "source": (
                        "workspace.semantic_materialization.baseline_oig_hydrator"
                    ),
                    "did_hydrate": True,
                },
            )
        return (
            _matching_baseline_api_root_oig(),
            {
                "status": "baseline_hydrated",
                "reason": "workspace_baseline_oig_hydrated_from_test",
                "source": "workspace.semantic_materialization.baseline_oig_hydrator",
                "did_hydrate": True,
            },
        )

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            context={
                SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                    "provider_key": "aware_api",
                    "semantic_owner": "aware_api.provider",
                    "semantic_branch_id": "semantic-branch-id",
                    "semantic_projection_hash": "sha256:api-package",
                    "semantic_projection_name": "ApiPackage",
                    "author_id": "author-id",
                    "provider_inputs": {
                        "baseline_oig_hydrator": _baseline_oig_hydrator,
                    },
                },
                SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                    encode_semantic_function_call_context_by_provider(
                        {
                            "aware_api": SemanticFunctionCallContext(
                                resolved_argument_ref_object_ids={
                                    "aware_demo_api.ReadDemoRequest": (
                                        "new-request-class-config-id"
                                    ),
                                },
                            ),
                        }
                    )
                ),
            },
            execute_provider_delta_materialization=False,
        ),
    )

    details = cast(dict[str, object], result["details"])
    hydration = cast(dict[str, object], details["baseline_context_hydration"])
    preflight = cast(dict[str, object], details["baseline_hydration_preflight"])
    dirty_diff = cast(dict[str, object], details["api_semantic_dirty_diff"])
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )

    assert result["status"] == "succeeded"
    assert hydration["status"] == "current_head_context_hydrated"
    assert hydration["current_semantic_object_id_count"] == 3
    assert len(hydration_refs) == 2
    hydration_ref, source_hydration_ref = hydration_refs
    assert hydration_ref["source"] == (
        "aware_api.provider_delta.baseline_root_hydration_ref"
    )
    assert hydration_ref["workspace_revision_id"] == "workspace-revision-id"
    assert hydration_ref["semantic_package_id"] == "semantic-package-id"
    assert hydration_ref["semantic_package_commit_id"] == ("semantic-package-commit-id")
    assert hydration_ref["semantic_projection_name"] == "Api"
    assert hydration_ref["semantic_projection_hash"] is None
    assert hydration_ref["semantic_object_instance_graph_commit_id"] == (
        "api-root-oig-commit"
    )
    assert hydration_ref["semantic_root_object_instance_graph_commit_id"] == (
        "api-root-oig-commit"
    )
    assert source_hydration_ref["source"] == (
        "aware_api.provider_delta.baseline_source_hydration_ref"
    )
    assert source_hydration_ref["semantic_projection_name"] == "CodePackage"
    assert source_hydration_ref["semantic_projection_hash"] is None
    assert source_hydration_ref["semantic_object_instance_graph_commit_id"] == (
        "source-oig-commit"
    )
    assert source_hydration_ref["semantic_root_kind"] == "code_package"
    assert source_hydration_ref["semantic_root_id"] == "source-code-package-id"
    root_ref_resolution = cast(
        dict[str, object],
        hydration["baseline_root_hydration_ref_resolution"],
    )
    assert root_ref_resolution["status"] == "ready"
    assert root_ref_resolution["source_projection_name"] == "ApiPackage"
    assert root_ref_resolution["source_object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert root_ref_resolution["hydration_projection_name"] == "Api"
    assert root_ref_resolution["hydration_object_instance_graph_commit_id"] == (
        "api-root-oig-commit"
    )
    assert hydration["baseline_semantic_object_index_source"] == (
        "aware_api.provider_delta.hydrated_source_code_package_and_api_root_oig"
    )
    root_oig_projection = cast(
        dict[str, object],
        hydration["api_baseline_root_oig_projection"],
    )
    assert root_oig_projection["status"] == "ready"
    assert root_oig_projection["baseline_semantic_object_index_count"] == 3
    source_oig_projection = cast(
        dict[str, object],
        hydration["api_baseline_source_oig_projection"],
    )
    assert source_oig_projection["status"] == "ready"
    assert source_oig_projection["source_path_count"] == 1
    assert source_oig_projection["baseline_semantic_payload_index_count"] == 3
    root_source_merge = cast(
        dict[str, object],
        hydration["api_baseline_root_source_merge"],
    )
    assert root_source_merge["status"] == "ready"
    assert root_source_merge["baseline_semantic_object_index_count"] == 3
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_sources"] == (
        "previous_materialization_evidence",
    )
    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "api_noop": 1,
        "api_capability_noop": 1,
        "api_capability_endpoint_noop": 1,
    }
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["operation_family_counts"] == {}
    assert typed_operation_plan["typed_operation_count"] == 0
    assert typed_operation_plan["noop_entry_count"] == 3
    assert operation_execution["status"] == "flag_required"


@pytest.mark.asyncio
async def test_api_provider_delta_blocks_non_api_root_before_hydrator(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    invalid_root_ref = {
        **_baseline_ref_payload(api_toml_path=api_toml_path),
        "semantic_root_kind": "api_package",
    }
    hydrator_calls: list[object] = []

    async def _baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: object,
    ) -> dict[str, object]:
        hydrator_calls.append((request, baseline_ref))
        return {}

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            baseline_ref=invalid_root_ref,
            execute_provider_delta_materialization=False,
            context={
                SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                    "provider_key": "aware_api",
                    "semantic_owner": "aware_api.provider",
                    "semantic_branch_id": "semantic-branch-id",
                    "semantic_projection_hash": "sha256:api-package",
                    "semantic_projection_name": "ApiPackage",
                    "author_id": "author-id",
                    "provider_inputs": {
                        "baseline_oig_hydrator": _baseline_oig_hydrator,
                    },
                },
            },
        ),
    )

    details = cast(dict[str, object], result["details"])
    hydration = cast(dict[str, object], details["baseline_context_hydration"])
    root_ref_resolution = cast(
        dict[str, object],
        hydration["baseline_root_hydration_ref_resolution"],
    )
    assert hydrator_calls == []
    assert hydration["status"] == "baseline_root_ref_blocked"
    assert hydration["reason"] == "api_provider_delta_baseline_root_kind_must_be_api"
    assert root_ref_resolution["status"] == "blocked"
    assert root_ref_resolution["blockers"] == (
        "api_provider_delta_baseline_root_kind_must_be_api",
    )


def test_api_provider_delta_source_oig_projection_blocks_missing_source_text(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    complete_oig = _matching_baseline_source_code_package_oig(
        source_text=(api_toml_path.parent / "apis" / "demo.aware").read_text(
            encoding="utf-8"
        ),
    )
    incomplete_oig = SimpleNamespace(
        class_instances=complete_oig.class_instances[:-1],
    )
    source_ref_payload = {
        **_baseline_ref_payload(api_toml_path=api_toml_path),
        "semantic_projection_name": "CodePackage",
        "semantic_object_instance_graph_commit_id": "source-oig-commit",
        "semantic_root_kind": "code_package",
        "semantic_root_id": "source-code-package-id",
        "semantic_root_object_instance_graph_commit_id": "source-oig-commit",
    }
    baseline_ref = SemanticMaterializationBaselineRef.model_validate(source_ref_payload)

    projection = api_delta_baseline_semantic_payload_index_from_source_code_package_oig(
        oig=incomplete_oig,
        baseline_ref=baseline_ref,
    )

    assert projection.status == "blocked"
    assert (
        projection.reason == "api_provider_delta_baseline_source_content_text_required"
    )
    assert projection.baseline_semantic_payload_index == {}


def test_api_provider_delta_root_source_merge_blocks_semantic_key_mismatch(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    baseline_ref_payload = _baseline_ref_payload(api_toml_path=api_toml_path)
    root_ref_resolution = api_delta_root_baseline_hydration_ref_resolution(
        baseline_ref=baseline_ref_payload,
    )
    source_ref_resolution = api_delta_source_baseline_hydration_ref_resolution(
        baseline_ref=baseline_ref_payload,
    )
    assert root_ref_resolution.hydration_ref is not None
    assert source_ref_resolution.hydration_ref is not None
    root_projection = api_delta_baseline_semantic_object_index_from_root_oig(
        oig=_matching_baseline_api_root_oig(),
        baseline_ref=root_ref_resolution.hydration_ref,
    )
    source_text = (api_toml_path.parent / "apis" / "demo.aware").read_text(
        encoding="utf-8"
    )
    source_projection = (
        api_delta_baseline_semantic_payload_index_from_source_code_package_oig(
            oig=_matching_baseline_source_code_package_oig(
                source_text=source_text.replace("api demo", "api other"),
            ),
            baseline_ref=source_ref_resolution.hydration_ref,
        )
    )

    merged = api_delta_baseline_semantic_object_index_from_root_and_source(
        root_projection=root_projection,
        source_projection=source_projection,
        root_ref=root_ref_resolution.hydration_ref,
        source_ref=source_ref_resolution.hydration_ref,
    )

    assert merged.status == "blocked"
    assert merged.reason == (
        "api_provider_delta_baseline_source_keys_missing_root_identity"
    )
    assert merged.baseline_semantic_object_index == {}
    assert len(merged.missing_root_identity_keys) == 3
    assert len(merged.missing_source_payload_keys) == 3


@pytest.mark.asyncio
async def test_api_provider_delta_executes_exact_endpoint_description_update(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    baseline_index = _matching_baseline_semantic_object_index()
    endpoint_key = "api:demo/capability:read_demo/endpoint:read_demo"
    cast(dict[str, object], baseline_index[endpoint_key]["payload"])[
        "description"
    ] = "Previous endpoint description."
    previous_evidence = {
        "available": True,
        "previous_delta_fingerprint_available": True,
        "evidence_source": "workspace_semantic_baseline_resolution",
        "current_semantic_object_id_count": 3,
        "provider_delta_operation_execution_context_available": True,
        "current_semantic_object_ids": {
            semantic_key: str(entry["object_id"])
            for semantic_key, entry in baseline_index.items()
        },
        "baseline_semantic_object_index": baseline_index,
    }
    backend = _RecordingApiExecutionBackend()

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            previous_materialization_evidence=previous_evidence,
            semantic_function_call_execution_context={
                SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                    encode_semantic_function_call_context_by_provider(
                        {
                            "aware_api": SemanticFunctionCallContext(
                                resolved_argument_ref_object_ids={
                                    "aware_demo_api.ReadDemoRequest": (
                                        "request-class-config-id"
                                    ),
                                },
                            ),
                        }
                    )
                ),
                SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {"enabled": True},
                API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
            },
        ),
    )

    details = cast(dict[str, object], result["details"])
    dirty_diff = cast(dict[str, object], details["api_semantic_dirty_diff"])
    typed_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "api_noop": 1,
        "api_capability_noop": 1,
        "api_capability_endpoint_update": 1,
    }
    assert dirty_diff["noop_entry_count"] == 2
    assert dirty_diff["actionable_entry_count"] == 1
    assert typed_plan["typed_operation_count"] == 1
    assert typed_plan["noop_entry_count"] == 2
    assert typed_plan["operation_family_counts"] == {"update": 1}
    (typed_operation,) = typed_plan["typed_operations"]
    assert typed_operation["semantic_key"] == endpoint_key
    assert typed_operation["baseline"]["changed_fields"] == ("description",)
    assert operation_execution["status"] == "executed"
    assert operation_execution["did_execute"] is True
    typed_execution = cast(
        dict[str, object],
        operation_execution["typed_operation_execution"],
    )
    assert typed_execution["step_count"] == 1
    endpoint_update_invocations = tuple(
        invocation
        for invocation in backend.invocations
        if invocation.function_ref == API_CAPABILITY_ENDPOINT_UPDATE_FUNCTION_REF
    )
    assert len(endpoint_update_invocations) == 1
    (invocation,) = endpoint_update_invocations
    assert invocation.function_ref == API_CAPABILITY_ENDPOINT_UPDATE_FUNCTION_REF
    assert invocation.receiver_object_id == "endpoint-id"
    assert invocation.arguments == {"description": None}


@pytest.mark.asyncio
async def test_api_provider_delta_blocks_id_only_previous_evidence(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    previous_evidence = {
        "available": True,
        "previous_delta_fingerprint_available": True,
        "evidence_source": "workspace_semantic_baseline_resolution",
        "current_semantic_object_id_count": 3,
        "provider_delta_operation_execution_context_available": True,
        "current_semantic_object_ids": {
            "api:demo": "api-id",
            "api:demo/capability:read_demo": "capability-id",
            ("api:demo/capability:read_demo/" "endpoint:read_demo"): "endpoint-id",
        },
    }

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            previous_materialization_evidence=previous_evidence,
            execute_provider_delta_materialization=False,
        ),
    )

    details = cast(dict[str, object], result["details"])
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    preflight = cast(dict[str, object], details["baseline_hydration_preflight"])
    dirty_diff = cast(dict[str, object], details["api_semantic_dirty_diff"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    typed_execution_preflight = cast(
        dict[str, object],
        details["provider_delta_typed_operation_execution_preflight"],
    )
    assert result["status"] == "succeeded"
    assert operation_execution["status"] == "flag_required"
    assert operation_execution["did_execute"] is False
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_available"] is True
    assert preflight["current_semantic_object_id_count"] == 3
    assert preflight["current_head_context_sources"] == (
        "previous_materialization_evidence",
    )
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["baseline_semantic_object_index_available"] is False
    assert dirty_diff["baseline_semantic_object_index_sources"] == ()
    assert dirty_diff["baseline_index_compare_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert dirty_diff["baseline_compare_operation_counts"] == {"blocked": 3}
    assert dirty_diff["blocked_entry_count"] == 3
    assert operation_plan["api_baseline_index_compare_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["planned_operation_count"] == 0
    assert typed_operation_plan["status"] == "typed_operation_plan_blocked"
    assert typed_operation_plan["typed_operation_count"] == 0
    assert typed_operation_plan["operation_family_counts"] == {}
    assert typed_execution_preflight["status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert typed_execution_preflight["typed_operation_count"] == 0
    assert typed_execution_preflight["payload_completeness_checked"] is False
    assert typed_execution_preflight["payload_complete"] is False
    assert typed_execution_preflight["execution_wired"] is False
    assert typed_execution_preflight["would_execute"] is False
    assert typed_execution_preflight["operation_family_counts"] == {}
    assert operation_plan["provider_delta_typed_operation_status"] == (
        "typed_operation_plan_blocked"
    )
    assert operation_plan["provider_delta_typed_operation_count"] == 0
    assert operation_plan["provider_delta_typed_operation_execution_status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert operation_plan["provider_delta_typed_operation_execution_reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert operation_plan["provider_delta_typed_operation_plan"] == (
        typed_operation_plan
    )
    assert operation_plan["provider_delta_typed_operation_execution_preflight"] == (
        typed_execution_preflight
    )
    assert typed_operation_plan["typed_operations"] == ()
    assert typed_execution_preflight["operation_execution_preflights"] == ()


@pytest.mark.asyncio
async def test_api_provider_delta_typed_operation_plan_classifies_create_update(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    previous_evidence = {
        "available": True,
        "previous_delta_fingerprint_available": True,
        "evidence_source": "workspace_semantic_baseline_resolution",
        "current_semantic_object_id_count": 1,
        "provider_delta_operation_execution_context_available": True,
        "current_semantic_object_ids": {
            "api:demo": "api-id",
        },
        "baseline_semantic_object_index": {
            "api:demo": _matching_baseline_semantic_object_index()["api:demo"],
        },
    }

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            previous_materialization_evidence=previous_evidence,
            execute_provider_delta_materialization=False,
        ),
    )

    details = cast(dict[str, object], result["details"])
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    typed_execution_preflight = cast(
        dict[str, object],
        details["provider_delta_typed_operation_execution_preflight"],
    )
    typed_operations = tuple(
        cast(
            tuple[dict[str, object], ...],
            typed_operation_plan["typed_operations"],
        )
    )
    typed_operation_by_key = {
        operation["semantic_key"]: operation for operation in typed_operations
    }
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["operation_family_counts"] == {
        "create": 2,
    }
    assert typed_operation_plan["operation_type_counts"] == {
        "aware_api.api_capability.create": 1,
        "aware_api.api_capability_endpoint.create": 1,
    }
    assert typed_execution_preflight["status"] == "typed_operation_execution_ready"
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_typed_operation_execution_ready"
    )
    assert typed_execution_preflight["payload_complete"] is True
    assert typed_execution_preflight["payload_missing_operation_count"] == 0
    assert typed_execution_preflight["create_operation_count"] == 2
    assert typed_execution_preflight["update_operation_count"] == 0
    assert typed_execution_preflight["operation_family_counts"] == {"create": 2}
    assert typed_operation_plan["noop_entry_count"] == 1
    assert "api:demo" not in typed_operation_by_key
    capability_operation = typed_operation_by_key["api:demo/capability:read_demo"]
    capability_api_operation = cast(
        dict[str, object],
        capability_operation["api_operation"],
    )
    assert capability_operation["operation_family"] == "create"
    assert capability_api_operation["operation"] == "ensure_api_capability"
    assert capability_api_operation["receiver_semantic_key"] == "api:demo"
    endpoint_operation = typed_operation_by_key[
        "api:demo/capability:read_demo/endpoint:read_demo"
    ]
    endpoint_api_operation = cast(
        dict[str, object],
        endpoint_operation["api_operation"],
    )
    endpoint_source_event = cast(
        dict[str, object],
        endpoint_operation["source_semantic_event"],
    )
    endpoint_function_call_plan = cast(
        dict[str, object],
        endpoint_operation["function_call_plan"],
    )
    assert endpoint_operation["operation_family"] == "create"
    assert endpoint_api_operation["operation"] == "ensure_api_capability_endpoint"
    assert endpoint_api_operation["receiver_semantic_key"] == (
        "api:demo/capability:read_demo"
    )
    assert endpoint_source_event["event_key"] == (
        "aware_api.api_capability_endpoint.upserted"
    )
    assert endpoint_function_call_plan["result_semantic_key"] == (
        "api:demo/capability:read_demo/endpoint:read_demo"
    )


@pytest.mark.asyncio
async def test_api_provider_delta_rejects_explicit_id_only_context_before_execute(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    backend = _RecordingApiExecutionBackend()
    execution_context = {
        SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
            encode_semantic_function_call_context_by_provider(
                {
                    "aware_api": SemanticFunctionCallContext(
                        current_semantic_object_ids={
                            "api:demo": "api-id",
                            "api:demo/capability:read_demo": "capability-id",
                            (
                                "api:demo/capability:read_demo/" "endpoint:read_demo"
                            ): "endpoint-id",
                        },
                        resolved_argument_ref_object_ids={
                            "aware_demo_api.ReadDemoRequest": (
                                "request-class-config-id"
                            ),
                        },
                    ),
                }
            )
        ),
        SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {"enabled": True},
        API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
    }

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            semantic_function_call_execution_context=execution_context,
        ),
    )

    details = cast(dict[str, object], result["details"])
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    package_source_execution = cast(
        dict[str, object],
        details["provider_delta_package_source_operation_execution"],
    )
    preflight = cast(dict[str, object], details["baseline_hydration_preflight"])
    dirty_diff = cast(dict[str, object], details["api_semantic_dirty_diff"])
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    typed_execution_preflight = cast(
        dict[str, object],
        details["provider_delta_typed_operation_execution_preflight"],
    )
    function_execution = cast(
        dict[str, object],
        operation_execution["semantic_function_call_execution"],
    )
    assert operation_execution["status"] == "typed_operation_execution_blocked"
    assert operation_execution["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert operation_execution["did_execute"] is False
    assert operation_execution["semantic_function_call_resolution_count"] == 0
    assert operation_execution["semantic_function_call_resolution_status_counts"] == {}
    assert "typed_operation_execution" not in operation_execution
    assert function_execution["status"] == "typed_operation_execution_blocked"
    assert function_execution["enabled"] is False
    assert package_source_execution["status"] == "operation_not_ready"
    assert package_source_execution["did_execute"] is False
    assert typed_execution_preflight["status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert typed_execution_preflight["typed_operation_count"] == 0
    assert len(backend.invocations) == 0
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_available"] is True
    assert preflight["current_semantic_object_id_count"] == 3
    assert preflight["baseline_semantic_object_index_available"] is False
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["baseline_semantic_object_index_available"] is False
    assert dirty_diff["baseline_index_compare_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert dirty_diff["baseline_compare_operation_counts"] == {"blocked": 3}
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert head_move_plan["blocked"] is True
    assert head_move_plan["planned_operation_count"] == 0


@pytest.mark.asyncio
async def test_api_provider_delta_blocks_mixed_create_update_before_legacy_execution(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    backend = _RecordingApiExecutionBackend()
    execution_context = {
        SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
            encode_semantic_function_call_context_by_provider(
                {
                    "aware_api": SemanticFunctionCallContext(
                        current_semantic_object_ids={
                            "api:demo": "api-id",
                        },
                        resolved_argument_ref_object_ids={
                            "aware_demo_api.ReadDemoRequest": (
                                "request-class-config-id"
                            ),
                        },
                    ),
                }
            )
        ),
        SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {"enabled": True},
        API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
    }

    result = await workspace_provider.materialize_delta(
        request=_execution_request(
            base_request,
            semantic_function_call_execution_context=execution_context,
        ),
    )

    details = cast(dict[str, object], result["details"])
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    package_source_execution = cast(
        dict[str, object],
        details["provider_delta_package_source_operation_execution"],
    )
    typed_operation_plan = cast(
        dict[str, object],
        details["provider_delta_typed_operation_plan"],
    )
    typed_execution_preflight = cast(
        dict[str, object],
        details["provider_delta_typed_operation_execution_preflight"],
    )
    assert result["status"] == "succeeded"
    assert typed_operation_plan["status"] == "typed_operation_plan_blocked"
    assert typed_operation_plan["operation_family_counts"] == {}
    assert typed_operation_plan["typed_operation_count"] == 0
    assert typed_execution_preflight["status"] == (
        "typed_operation_execution_preflight_blocked"
    )
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert operation_execution["status"] == "typed_operation_execution_blocked"
    assert operation_execution["reason"] == (
        "api_provider_delta_baseline_payload_comparison_blocked"
    )
    assert operation_execution["did_execute"] is False
    assert operation_execution["semantic_function_call_resolution_count"] == 0
    assert "typed_operation_execution" not in operation_execution
    assert package_source_execution["status"] == "operation_not_ready"
    assert package_source_execution["did_execute"] is False
    assert package_source_execution["step_count"] == 0
    assert len(backend.invocations) == 0
