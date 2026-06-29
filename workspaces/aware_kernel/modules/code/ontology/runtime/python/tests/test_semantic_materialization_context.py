from __future__ import annotations

from typing import cast

from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SEMANTIC_FUNCTION_CALL_CONTEXT_KEY,
    SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION,
    SEMANTIC_SOURCE_SESSION_CONTEXT_KEY,
    SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS,
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY,
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY,
    SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION,
    SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
    SemanticMaterializationBaselineRef,
    SemanticMaterializationBaselineResolution,
    SemanticFunctionCallContext,
    SemanticSourceSessionCacheRef,
    SemanticSourceSessionContext,
    SemanticSourceSessionPackageContext,
    SemanticProviderDeltaDurableExecutionInputs,
    SemanticProviderDeltaLaneState,
    SemanticProviderDeltaRequest,
    SemanticProviderDeltaRequestBundle,
    SemanticProviderDeltaResult,
    SemanticProjectionPortalPolicy,
    build_semantic_provider_delta_head_move_plan,
    encode_semantic_function_call_context,
    encode_semantic_function_call_context_by_provider,
    encode_semantic_source_session_context,
)


def test_semantic_function_call_context_normalizes_payload() -> None:
    context = SemanticFunctionCallContext.from_payload(
        {
            "current_semantic_object_ids": {
                " api:demo ": " api-id ",
                "": "empty-key",
                "blank-value": "",
            },
            "resolved_argument_ref_object_ids": {
                " aware_demo.Request ": " request-id ",
            },
        }
    )

    assert context.current_semantic_object_ids == {"api:demo": "api-id"}
    assert context.resolved_argument_ref_object_ids == {
        "aware_demo.Request": "request-id",
    }


def test_semantic_function_call_context_merges_provider_overlay() -> None:
    context = SemanticFunctionCallContext.from_materialization_context(
        {
            SEMANTIC_FUNCTION_CALL_CONTEXT_KEY: {
                "current_semantic_object_ids": {
                    "api:demo": "generic-api-id",
                },
                "resolved_argument_ref_object_ids": {
                    "aware_demo.Request": "generic-request-id",
                },
            },
            SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: {
                "aware_api": {
                    "current_semantic_object_ids": {
                        "api:demo": "api-provider-id",
                        "api:demo/capability:read": "capability-id",
                    },
                },
            },
        },
        provider_key="aware_api",
    )

    assert context.current_semantic_object_ids == {
        "api:demo": "api-provider-id",
        "api:demo/capability:read": "capability-id",
    }
    assert context.resolved_argument_ref_object_ids == {
        "aware_demo.Request": "generic-request-id",
    }


def test_encode_semantic_function_call_contexts() -> None:
    context = SemanticFunctionCallContext(
        current_semantic_object_ids={"api:demo": "api-id"},
        resolved_argument_ref_object_ids={"aware_demo.Request": "request-id"},
    )

    assert encode_semantic_function_call_context(context) == {
        "current_semantic_object_ids": {"api:demo": "api-id"},
        "resolved_argument_ref_object_ids": {
            "aware_demo.Request": "request-id",
        },
    }
    assert encode_semantic_function_call_context_by_provider(
        {"aware_api": context, "": context}
    ) == {
        "aware_api": {
            "current_semantic_object_ids": {"api:demo": "api-id"},
            "resolved_argument_ref_object_ids": {
                "aware_demo.Request": "request-id",
            },
        },
    }


def test_semantic_source_session_context_normalizes_payload() -> None:
    context = SemanticSourceSessionContext.from_payload(
        {
            "source_session_id": " source-session ",
            "environment": " workspace ",
            "branch_key": " main ",
            "session_key": " local-cli ",
            "source_delta_fingerprint": " sha256:source ",
            "lifecycle_stages": ["semantic_status", "", "semantic_plan"],
            "packages": [
                {
                    "package_name": " home-ontology ",
                    "code_package_id": " home-code-package ",
                    "manifest_path": " ontologies/home/aware.ontology.toml ",
                    "semantic_provider_key": " aware_meta ",
                    "semantic_owner": " aware_meta.provider ",
                    "delta_fingerprint": " sha256:package ",
                    "source_files": [" aware/home.aware ", ""],
                    "cache_refs": [
                        {
                            "cache_kind": (
                                SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND
                            ),
                            "cache_key": " source-index-key ",
                            "signature": " sha256:package ",
                            "source": " workspace.session ",
                            "hit": False,
                            "evidence": {"source_code_package_id": "home-code"},
                        },
                    ],
                },
                {"package_name": ""},
            ],
            "cache_refs": [
                {
                    "cache_kind": "workspace_source_delta",
                    "cache_key": "source-delta-key",
                },
            ],
        }
    )

    assert context.contract_version == SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION
    assert context.source_session_id == "source-session"
    assert context.branch_key == "main"
    assert context.session_key == "local-cli"
    assert context.source_delta_fingerprint == "sha256:source"
    assert context.lifecycle_stages == ("semantic_status", "semantic_plan")
    assert len(context.packages) == 1
    package = context.packages[0]
    assert package.package_name == "home-ontology"
    assert package.code_package_id == "home-code-package"
    assert package.source_files == ("aware/home.aware",)
    assert package.cache_refs[0].cache_kind == (
        SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND
    )
    assert package.cache_refs[0].hit is False
    assert context.cache_refs[0].cache_key == "source-delta-key"


def test_semantic_source_session_context_materialization_key_roundtrips() -> None:
    context = SemanticSourceSessionContext(
        source_session_id="source-session",
        branch_key="main",
        session_key="local-cli",
        source_delta_fingerprint="sha256:source",
        lifecycle_stages=("semantic_status",),
        packages=(
            SemanticSourceSessionPackageContext(
                package_name="home-ontology",
                code_package_id="home-code-package",
                delta_fingerprint="sha256:package",
                source_files=("aware/home.aware",),
                cache_refs=(
                    SemanticSourceSessionCacheRef(
                        cache_kind=SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
                        cache_key="source-index-key",
                        signature="sha256:package",
                    ),
                ),
            ),
        ),
    )
    encoded = encode_semantic_source_session_context(context)
    rebuilt = SemanticSourceSessionContext.from_materialization_context(
        {
            SEMANTIC_SOURCE_SESSION_CONTEXT_KEY: encoded,
        }
    )

    assert encoded["context_kind"] == "semantic_source_session_context"
    assert rebuilt.source_session_id == "source-session"
    assert rebuilt.packages[0].package_name == "home-ontology"
    assert rebuilt.packages[0].cache_refs[0].cache_key == "source-index-key"


def test_provider_delta_execution_context_metadata_keys_are_code_owned() -> None:
    assert SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY == (
        "execution_context_resolvers"
    )
    assert SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY == (
        "operation_execution_projection_name"
    )
    assert SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY == (
        "provider_delta_durable_execution_inputs"
    )


def test_semantic_projection_portal_policy_roundtrips_static_contract() -> None:
    policy = SemanticProjectionPortalPolicy.model_validate(
        {
            "provider_key": " aware_meta ",
            "semantic_owner": " aware_meta.provider ",
            "operation_family": " ocg_genesis ",
            "primary_projection": " ObjectConfigGraphPackage ",
            "projections": [
                {
                    "projection_name": " ObjectConfigGraphPackage ",
                    "participation": "required",
                },
                {
                    "projection_name": " ObjectConfigGraph ",
                    "participation": "required",
                },
                {
                    "projection_name": " ObjectProjectionGraph ",
                    "participation": "created_in_plan",
                    "metadata": {"owned_by": "opg_genesis"},
                },
            ],
            "portals": [
                {
                    "policy_key": (" aware_meta.ocg_genesis.object_projection_graphs "),
                    "source_projection": " ObjectConfigGraph ",
                    "source_path": (" ObjectConfigGraph.object_projection_graphs "),
                    "target_projection": " ObjectProjectionGraph ",
                    "hydration": "created_in_plan",
                    "operation_scope": [" create_root ", " create_node ", ""],
                }
            ],
        }
    )

    dumped = policy.model_dump(mode="json")
    projections = cast(list[dict[str, object]], dumped["projections"])
    portals = cast(list[dict[str, object]], dumped["portals"])

    assert policy.contract_version == SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION
    assert policy.provider_key == "aware_meta"
    assert policy.projection_names == (
        "ObjectConfigGraphPackage",
        "ObjectConfigGraph",
        "ObjectProjectionGraph",
    )
    assert policy.portal_policy_keys == (
        "aware_meta.ocg_genesis.object_projection_graphs",
    )
    assert dumped["policy_kind"] == "semantic_projection_portal_policy"
    assert projections[2]["participation"] == "created_in_plan"
    assert portals[0]["hydration"] == "created_in_plan"
    assert portals[0]["operation_scope"] == ["create_root", "create_node"]

    rebuilt = SemanticProjectionPortalPolicy.model_validate(dumped)

    assert rebuilt == policy


def test_semantic_projection_portal_policy_rejects_runtime_provenance() -> None:
    cases = [
        {
            "provider_key": "aware_meta",
            "operation_family": "ocg_genesis",
            "primary_projection": "ObjectConfigGraphPackage",
            "branch_id": "branch-id",
        },
        {
            "provider_key": "aware_meta",
            "operation_family": "ocg_genesis",
            "primary_projection": "ObjectConfigGraphPackage",
            "projections": [
                {
                    "projection_name": "ObjectConfigGraph",
                    "projection_hash": "projection-hash",
                }
            ],
        },
        {
            "provider_key": "aware_meta",
            "operation_family": "ocg_genesis",
            "primary_projection": "ObjectConfigGraphPackage",
            "portals": [
                {
                    "policy_key": "aware_meta.ocg_genesis.opg",
                    "source_projection": "ObjectConfigGraph",
                    "source_path": "ObjectConfigGraph.object_projection_graphs",
                    "target_projection": "ObjectProjectionGraph",
                    "baseline_commit_id": "commit-id",
                }
            ],
        },
    ]

    for payload in cases:
        try:
            SemanticProjectionPortalPolicy.model_validate(payload)
        except ValueError as exc:
            assert "runtime provenance" in str(exc)
        else:  # pragma: no cover - assertion branch
            raise AssertionError("runtime provenance payload was accepted")


def test_semantic_projection_portal_policy_rejects_invalid_modes() -> None:
    for payload in (
        {
            "provider_key": "aware_meta",
            "operation_family": "ocg_genesis",
            "primary_projection": "ObjectConfigGraphPackage",
            "projections": [
                {
                    "projection_name": "ObjectConfigGraph",
                    "participation": "existing_head",
                }
            ],
        },
        {
            "provider_key": "aware_meta",
            "operation_family": "ocg_genesis",
            "primary_projection": "ObjectConfigGraphPackage",
            "portals": [
                {
                    "policy_key": "aware_meta.ocg_genesis.opg",
                    "source_projection": "ObjectConfigGraph",
                    "source_path": "ObjectConfigGraph.object_projection_graphs",
                    "target_projection": "ObjectProjectionGraph",
                    "hydration": "all",
                }
            ],
        },
    ):
        try:
            SemanticProjectionPortalPolicy.model_validate(payload)
        except ValueError as exc:
            assert "invalid" in str(exc)
        else:  # pragma: no cover - assertion branch
            raise AssertionError("invalid projection portal policy mode accepted")


def test_semantic_provider_delta_durable_execution_inputs_are_code_owned() -> None:
    payload = SemanticProviderDeltaDurableExecutionInputs.model_validate(
        {
            "provider_key": " aware_meta ",
            "semantic_owner": " aware_meta.provider ",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_hash": "projection-hash",
            "semantic_projection_name": "ObjectConfigGraphPackage",
            "author_id": "author-id",
            "source_object_instance_graph_commit_id": "source-oig-commit",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit",
            "semantic_root_object_instance_graph_commit_id": "root-oig-commit",
            "provider_inputs": {
                "baseline_oig_hydrator": lambda: None,
                "descriptor_tree_append_ready_applier": "applier-ref",
            },
        }
    )

    dumped = payload.model_dump(mode="json")
    python_dump = payload.model_dump(mode="python")
    evidence = payload.evidence_payload()

    assert payload.missing_common_fields() == ()
    assert dumped["contract_version"] == (
        SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION
    )
    assert dumped["common_inputs_available"] is True
    assert dumped["provider_key"] == "aware_meta"
    assert cast(dict[str, object], dumped["provider_inputs"])[
        "baseline_oig_hydrator"
    ] == {
        "value_kind": "callable",
        "callable_type": "function",
    }
    assert callable(
        cast(dict[str, object], python_dump["provider_inputs"])["baseline_oig_hydrator"]
    )
    assert evidence["provider_input_keys"] == (
        "baseline_oig_hydrator",
        "descriptor_tree_append_ready_applier",
    )


def test_semantic_provider_delta_durable_execution_inputs_report_missing_common_fields() -> (
    None
):
    payload = SemanticProviderDeltaDurableExecutionInputs(
        semantic_branch_id="semantic-branch-id",
    )

    assert SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS == (
        "semantic_branch_id",
        "semantic_projection_hash",
        "author_id",
    )
    assert payload.missing_common_fields() == (
        "semantic_projection_hash",
        "author_id",
    )
    assert payload.model_dump(mode="json")["common_inputs_available"] is False


def test_semantic_provider_delta_request_owns_baseline_key_contract() -> None:
    request = SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "demo-ontology",
                "workspace_manifest_kind": "aware_toml",
                "manifest_path": "modules/demo/structure/aware.toml",
                "source_code_package_id": "source-code-package-id",
            },
            "semantic_contract": {
                "module": "aware_meta.semantic_contract",
                "provider_key": "aware_meta",
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:current",
            "delta_cause_hints": {
                "changed_path_count": 1,
                "source_owned_path_count": 1,
                "top_changed_paths": [
                    {
                        "path": "aware/model.aware",
                        "change_kind": "update",
                        "classification": "source_owned",
                        "is_structural": True,
                    }
                ],
                "current_delta_fingerprint_available": True,
                "previous_delta_fingerprint_available": True,
            },
            "baseline_ref": _baseline_ref_payload(),
        }
    )

    payload = request.model_dump(mode="json")
    request_key = cast(str, payload["provider_delta_request_key"])
    baseline_ref = cast(dict[str, object], payload["baseline_ref"])
    assert (
        payload["contract_version"] == SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION
    )
    assert request_key.startswith("provider_delta_request:sha256:")
    assert payload["baseline_source_object_instance_graph_commit_id"] == (
        "source-oig-commit"
    )
    assert payload["baseline_semantic_object_instance_graph_commit_id"] == (
        "semantic-package-oig-commit"
    )
    assert payload["baseline_semantic_root_object_instance_graph_commit_id"] == (
        "semantic-root-oig-commit"
    )
    assert baseline_ref["semantic_branch_id"] == "semantic-branch-id"


def test_semantic_provider_delta_head_move_uses_code_request_contract() -> None:
    request = SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "demo-ontology",
                "manifest_path": "modules/demo/structure/aware.toml",
            },
            "semantic_contract": {
                "module": "aware_meta.semantic_contract",
                "provider_key": "aware_meta",
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:current",
            "baseline_ref": _baseline_ref_payload(),
        }
    )

    plan = build_semantic_provider_delta_head_move_plan(
        request=request,
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "baseline_index_compared",
            "current_delta_fingerprint": "sha256:current",
            "baseline_index_compare_available": True,
            "baseline_index_compare_status": "baseline_index_compared",
            "semantic_dirty_entries": [
                {
                    "entry_key": "ocg:demo/node:Room",
                    "semantic_key": "ocg:demo/node:Room",
                    "dirty_operation": "class_update",
                    "baseline_compare_operation": "class_update",
                    "baseline_object_matched": True,
                    "baseline_object_id": "baseline-room-id",
                    "baseline_object_kind": "class",
                }
            ],
        },
    ).model_dump(mode="json")

    assert plan["status"] == "head_move_plan_ready"
    assert plan["provider_delta_request_key"] == request.provider_delta_request_key
    plan_baseline_ref = cast(dict[str, object], plan["baseline_ref"])
    assert plan_baseline_ref["semantic_branch_id"] == "semantic-branch-id"
    assert plan["planned_operation_count"] == 1
    planned_operations = cast(list[dict[str, object]], plan["planned_operations"])
    assert planned_operations[0]["operation_family"] == "update"


def test_semantic_provider_delta_result_and_bundle_are_code_contracts() -> None:
    request = SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "demo-ontology",
                "manifest_path": "modules/demo/structure/aware.toml",
            },
            "semantic_contract": {
                "module": "aware_meta.semantic_contract",
                "provider_key": "aware_meta",
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:current",
        }
    )
    result = SemanticProviderDeltaResult.model_validate(
        {
            "status": "succeeded",
            "package": request.package,
            "semantic_contract": request.semantic_contract,
            "current_delta_fingerprint": request.current_delta_fingerprint,
            "applied_semantic_keys": ["ocg:demo/node:Room"],
        }
    )
    bundle = SemanticProviderDeltaRequestBundle.model_validate({"requests": [request]})

    assert result.contract_version == SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    assert result.applied_semantic_keys == ("ocg:demo/node:Room",)
    assert bundle.request_count == 1
    assert bundle.provider_delta_request_keys == (request.provider_delta_request_key,)


def test_semantic_materialization_baseline_ref_reports_missing_hydrator_fields() -> (
    None
):
    payload = _baseline_ref_payload()
    payload["semantic_branch_id"] = ""

    baseline_ref = SemanticMaterializationBaselineRef.model_validate(payload)

    assert baseline_ref.missing_required_fields() == ("semantic_branch_id",)


def test_semantic_materialization_baseline_resolution_wraps_code_ref() -> None:
    baseline_ref = SemanticMaterializationBaselineRef.model_validate(
        _baseline_ref_payload()
    )

    resolution = SemanticMaterializationBaselineResolution.model_validate(
        {
            "status": "resolved",
            "reason": "baseline_ref_resolved",
            "available": True,
            "evidence_complete": True,
            "candidate_count": 1,
            "package": {"package_name": "demo-ontology"},
            "semantic_contract": {"provider_key": "aware_meta"},
            "baseline_ref": baseline_ref,
        }
    )

    payload = resolution.model_dump(mode="json")
    assert resolution.baseline_ref == baseline_ref
    assert payload["baseline_ref"] == baseline_ref.model_dump(mode="json")
    assert payload["package"] == {"package_name": "demo-ontology"}


def test_semantic_provider_delta_lane_state_carries_existing_head_truth() -> None:
    baseline_ref = SemanticMaterializationBaselineRef.model_validate(
        _baseline_ref_payload()
    )

    lane_state = SemanticProviderDeltaLaneState.model_validate(
        {
            "status": "existing_head",
            "reason": "baseline_ref_resolved",
            "package": {"package_name": "demo-ontology"},
            "semantic_contract": {"provider_key": "aware_meta"},
            "baseline_ref": baseline_ref,
            "candidate_count": 1,
            "evidence_complete": True,
        }
    )

    payload = lane_state.model_dump(mode="json")
    assert lane_state.contract_version == (
        SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION
    )
    assert lane_state.semantic_branch_id == "semantic-branch-id"
    assert lane_state.semantic_projection_name == "ObjectConfigGraphPackage"
    assert lane_state.semantic_object_instance_graph_commit_id == (
        "semantic-package-oig-commit"
    )
    assert payload["baseline_ref"] == baseline_ref.model_dump(mode="json")


def test_semantic_provider_delta_request_accepts_lane_state_baseline_ref() -> None:
    baseline_ref = SemanticMaterializationBaselineRef.model_validate(
        _baseline_ref_payload()
    )
    lane_state = SemanticProviderDeltaLaneState.model_validate(
        {
            "status": "existing_head",
            "reason": "baseline_ref_resolved",
            "package": {"package_name": "demo-ontology"},
            "semantic_contract": {"provider_key": "aware_meta"},
            "baseline_ref": baseline_ref,
            "candidate_count": 1,
            "evidence_complete": True,
        }
    )

    request = SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "demo-ontology",
                "manifest_path": "modules/demo/structure/ontology/aware.toml",
                "source_code_package_id": "source-code-package-id",
            },
            "semantic_contract": {
                "module": "aware_meta.semantic_contract",
                "provider_key": "aware_meta",
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:current",
            "provider_delta_lane_state": lane_state,
        }
    )

    assert request.baseline_ref == baseline_ref
    assert request.provider_delta_lane_state == lane_state
    assert request.baseline_source_object_instance_graph_commit_id == (
        "source-oig-commit"
    )
    assert request.baseline_semantic_object_instance_graph_commit_id == (
        "semantic-package-oig-commit"
    )
    assert request.baseline_semantic_root_object_instance_graph_commit_id == (
        "semantic-root-oig-commit"
    )
    assert request.model_dump(mode="json")["provider_delta_lane_state"] == (
        lane_state.model_dump(mode="json")
    )


def _baseline_ref_payload() -> dict[str, object]:
    return {
        "workspace_revision_id": "workspace-revision-id",
        "workspace_materialization_id": "workspace-materialization-id",
        "workspace_materialization_index": 1,
        "revision_code_package_id": "revision-code-package-id",
        "source_code_package_id": "source-code-package-id",
        "source_object_instance_graph_commit_id": "source-oig-commit",
        "revision_code_package_object_instance_graph_commit_id": "source-oig-commit",
        "semantic_package_commit_id": "semantic-package-commit-id",
        "semantic_owner_module": "aware_meta",
        "semantic_package_kind": "object_config_graph_package",
        "semantic_package_id": "semantic-package-id",
        "semantic_package_name": "demo-ontology",
        "semantic_contract_module": "aware_meta.semantic_contract",
        "semantic_contract_name": "aware.semantic_provider",
        "semantic_contract_role": "aware_meta.provider",
        "semantic_contract_provider_key": "aware_meta",
        "semantic_provider_key": "aware_meta",
        "semantic_projection_name": "ObjectConfigGraphPackage",
        "semantic_branch_id": "semantic-branch-id",
        "semantic_object_instance_graph_commit_id": "semantic-package-oig-commit",
        "semantic_root_kind": "object_config_graph",
        "semantic_root_id": "semantic-root-id",
        "semantic_root_object_instance_graph_commit_id": "semantic-root-oig-commit",
        "manifest_path": "modules/demo/structure/aware.toml",
        "manifest_toml_path": "modules/demo/structure/aware.toml",
    }
