from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import aware_api_runtime.workspace_provider as workspace_provider
from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
    ApiSemanticFunctionCallInvocation,
    ApiSemanticFunctionCallInvocationResult,
)
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SemanticFunctionCallContext,
    SemanticProviderDeltaRequest,
    encode_semantic_function_call_context_by_provider,
)
from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_workspace.features.semantic_materialization.delta_contract import (
    WorkspaceSemanticMaterializationProviderDeltaRequest,
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
) -> WorkspaceSemanticMaterializationProviderDeltaRequest:
    return WorkspaceSemanticMaterializationProviderDeltaRequest.model_validate(
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


def _execution_request(
    base_request: (
        WorkspaceSemanticMaterializationProviderDeltaRequest
        | SemanticProviderDeltaRequest
    ),
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


@pytest.mark.asyncio
async def test_api_provider_delta_accepts_code_owned_request_contract(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    workspace_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    code_request = SemanticProviderDeltaRequest.model_validate(
        workspace_request.model_dump(mode="json")
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
        "semantic_dirty_diff_ready"
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
        "api_provider_delta_baseline_current_head_index_required"
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
    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
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
    assert head_move_plan["blocked_status"] == (
        "baseline_semantic_object_index_unavailable"
    )
    assert head_move_plan["planned_operation_count"] == 0
    assert head_move_plan["baseline_hydration_status"] == (
        "current_head_context_missing"
    )
    assert operation_execution["operation_count"] == 3
    assert operation_execution["status"] == "baseline_current_head_missing"
    assert operation_execution["reason"] == (
        "api_provider_delta_operation_execution_requires_hydrated_baseline_current_head"
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
async def test_api_provider_delta_hydrates_baseline_index_from_previous_evidence(
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
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_available"] is True
    assert preflight["current_semantic_object_id_count"] == 3
    assert preflight["current_head_context_sources"] == (
        "previous_materialization_evidence",
    )
    assert dirty_diff["baseline_semantic_object_index_available"] is True
    assert dirty_diff["baseline_semantic_object_index_sources"] == (
        "previous_materialization_evidence",
    )
    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "api_capability_endpoint_update": 1,
        "api_capability_update": 1,
        "api_update": 1,
    }
    assert operation_plan["api_baseline_index_compare_status"] == (
        "baseline_index_compared"
    )
    assert operation_plan["provider_delta_head_move_status"] == ("head_move_plan_ready")
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert head_move_plan["planned_operation_count"] == 3
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["typed_operation_count"] == 3
    assert typed_operation_plan["operation_family_counts"] == {"update": 3}
    assert typed_operation_plan["operation_type_counts"] == {
        "aware_api.api.update": 1,
        "aware_api.api_capability.update": 1,
        "aware_api.api_capability_endpoint.update": 1,
    }
    assert typed_execution_preflight["status"] == "typed_operation_execution_ready"
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_typed_operation_execution_ready"
    )
    assert typed_execution_preflight["typed_operation_count"] == 3
    assert typed_execution_preflight["payload_completeness_checked"] is True
    assert typed_execution_preflight["payload_complete"] is True
    assert typed_execution_preflight["payload_missing_operation_count"] == 0
    assert typed_execution_preflight["create_operation_count"] == 0
    assert typed_execution_preflight["update_operation_count"] == 3
    assert typed_execution_preflight["update_upsert_executor_support_ready"] is True
    assert typed_execution_preflight["execution_wired"] is False
    assert typed_execution_preflight["would_execute"] is False
    assert typed_execution_preflight["operation_family_counts"] == {"update": 3}
    assert operation_plan["provider_delta_typed_operation_status"] == (
        "typed_operation_plan_ready"
    )
    assert operation_plan["provider_delta_typed_operation_count"] == 3
    assert operation_plan["provider_delta_typed_operation_execution_status"] == (
        "typed_operation_execution_ready"
    )
    assert operation_plan["provider_delta_typed_operation_execution_reason"] == (
        "api_provider_delta_typed_operation_execution_ready"
    )
    assert operation_plan["provider_delta_typed_operation_plan"] == (
        typed_operation_plan
    )
    assert operation_plan["provider_delta_typed_operation_execution_preflight"] == (
        typed_execution_preflight
    )
    planned_operations = cast(
        tuple[dict[str, object], ...],
        head_move_plan["planned_operations"],
    )
    assert {operation["operation_family"] for operation in planned_operations} == {
        "update",
    }
    typed_operations = tuple(
        cast(
            tuple[dict[str, object], ...],
            typed_operation_plan["typed_operations"],
        )
    )
    typed_operation_by_key = {
        operation["semantic_key"]: operation for operation in typed_operations
    }
    endpoint_operation = typed_operation_by_key[
        "api:demo/capability:read_demo/endpoint:read_demo"
    ]
    endpoint_api_operation = cast(
        dict[str, object],
        endpoint_operation["api_operation"],
    )
    endpoint_arguments = cast(
        dict[str, object],
        endpoint_api_operation["arguments"],
    )
    assert endpoint_operation["provider_operation_type"] == (
        "aware_api.api_capability_endpoint.update"
    )
    assert endpoint_api_operation["operation"] == "ensure_api_capability_endpoint"
    assert endpoint_api_operation["receiver_semantic_key"] == (
        "api:demo/capability:read_demo"
    )
    assert endpoint_arguments["request_class_ref"] == ("aware_demo_api.ReadDemoRequest")
    endpoint_event_projection = cast(
        dict[str, object],
        endpoint_operation["semantic_event_projection"],
    )
    assert endpoint_event_projection["event_key"] == (
        "aware_api.provider_delta.api_capability_endpoint.update"
    )
    assert endpoint_event_projection["event_dispatch_wired"] is False
    assert cast(dict[str, object], endpoint_operation["baseline"])["object_id"] == (
        "endpoint-id"
    )
    operation_preflights = cast(
        tuple[dict[str, object], ...],
        typed_execution_preflight["operation_execution_preflights"],
    )
    assert {preflight["payload_complete"] for preflight in operation_preflights} == {
        True,
    }
    assert {
        preflight["executor_support_ready"] for preflight in operation_preflights
    } == {True}


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
        "update": 1,
    }
    assert typed_operation_plan["operation_type_counts"] == {
        "aware_api.api.update": 1,
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
    assert typed_execution_preflight["update_operation_count"] == 1
    assert typed_execution_preflight["operation_family_counts"] == {
        "create": 2,
        "update": 1,
    }
    api_operation = typed_operation_by_key["api:demo"]
    assert api_operation["operation_family"] == "update"
    assert cast(dict[str, object], api_operation["baseline"])["object_id"] == ("api-id")
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
async def test_api_provider_delta_trusts_explicit_current_head_context_before_execute(
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
    typed_execution = cast(
        dict[str, object],
        operation_execution["typed_operation_execution"],
    )
    assert operation_execution["status"] == "executed"
    assert operation_execution["reason"] == (
        "api_provider_delta_typed_operation_execution_invoked"
    )
    assert operation_execution["did_execute"] is True
    assert operation_execution["semantic_function_call_resolution_count"] == 0
    assert operation_execution["semantic_function_call_resolution_status_counts"] == {}
    assert typed_execution["typed_operation_execution_preflight_status"] == (
        "typed_operation_execution_ready"
    )
    assert typed_execution["typed_operation_count"] == 3
    assert function_execution["status"] == "executed"
    assert function_execution["enabled"] is True
    assert function_execution["status_counts"] == {"invoked": 3}
    assert function_execution["step_count"] == 3
    assert package_source_execution["status"] == "operation_refs_missing"
    assert package_source_execution["did_execute"] is False
    assert typed_execution_preflight["status"] == "typed_operation_execution_ready"
    assert typed_execution_preflight["update_operation_count"] == 3
    assert len(backend.invocations) == 3
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_available"] is True
    assert preflight["current_semantic_object_id_count"] == 3
    assert dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert dirty_diff["baseline_semantic_object_index_available"] is True
    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["baseline_compare_operation_counts"] == {
        "api_capability_endpoint_update": 1,
        "api_capability_update": 1,
        "api_update": 1,
    }
    dirty_entries = cast(
        tuple[dict[str, object], ...],
        dirty_diff["semantic_dirty_entries"],
    )
    endpoint_entry = next(
        entry
        for entry in dirty_entries
        if entry["ontology_subject_kind"] == "api_capability_endpoint"
    )
    assert endpoint_entry["dirty_operation"] == "api_capability_endpoint_update"
    assert endpoint_entry["baseline_object_id"] == "endpoint-id"
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert head_move_plan["blocked"] is False
    assert head_move_plan["planned_operation_count"] == 3
    planned_operations = cast(
        tuple[dict[str, object], ...],
        head_move_plan["planned_operations"],
    )
    assert planned_operations[2]["operation_family"] == "update"


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
    typed_execution = cast(
        dict[str, object],
        operation_execution["typed_operation_execution"],
    )

    assert result["status"] == "succeeded"
    assert typed_operation_plan["status"] == "typed_operation_plan_ready"
    assert typed_operation_plan["operation_family_counts"] == {
        "create": 2,
        "update": 1,
    }
    assert typed_execution_preflight["status"] == "typed_operation_execution_ready"
    assert typed_execution_preflight["reason"] == (
        "api_provider_delta_typed_operation_execution_ready"
    )
    assert operation_execution["status"] == "executed"
    assert operation_execution["reason"] == (
        "api_provider_delta_typed_operation_execution_invoked"
    )
    assert operation_execution["did_execute"] is True
    assert operation_execution["semantic_function_call_resolution_count"] == 0
    assert typed_execution["typed_operation_count"] == 3
    assert typed_execution["typed_operation_execution_preflight_status"] == (
        typed_execution_preflight["status"]
    )
    assert package_source_execution["status"] == "operation_refs_missing"
    assert package_source_execution["did_execute"] is False
    assert package_source_execution["step_count"] == 0
    assert len(backend.invocations) == 3
